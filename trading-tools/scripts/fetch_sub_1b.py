"""
Standalone script: Fetch 3-month 1m candle data for all Bybit USDT perpetual coins
with market cap < $1 billion, sorted by market cap descending.

Usage:
    python scripts/fetch_sub_1b.py                    # Full run: discover + fetch
    python scripts/fetch_sub_1b.py --list-only         # Just show the coin list, don't fetch
    python scripts/fetch_sub_1b.py --skip-discovery    # Skip CoinGecko, use saved coin list
    python scripts/fetch_sub_1b.py --max-coins 50      # Limit to first N coins
    python scripts/fetch_sub_1b.py --months 1          # Fetch 1 month instead of 3

Saves Parquet files to: PROJECTS/four-pillars-backtester/data/cache/
Restartable: skips coins that already have complete cached data.
"""

import sys
import time
import json
import requests
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CACHE_DIR = PROJECT_ROOT / "data" / "cache"
COIN_LIST_FILE = PROJECT_ROOT / "data" / "sub_1b_coins.json"
LOG_FILE = PROJECT_ROOT / "data" / "fetch_log.txt"

# ─── Configuration ───────────────────────────────────────────────────────────

BYBIT_BASE = "https://api.bybit.com"
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
MARKET_CAP_LIMIT = 1_000_000_000  # $1 billion
BYBIT_RATE_LIMIT = 0.12           # seconds between Bybit requests (safe for 10 req/s)
COINGECKO_RATE_LIMIT = 7.0        # seconds between CoinGecko requests (free tier: ~10/min safe)
BYBIT_MAX_CANDLES = 1000          # API limit per request
REQUEST_TIMEOUT = 30              # seconds
MAX_RETRIES = 3                   # retries per failed request
RETRY_DELAY = 5                   # seconds between retries


# ─── Logging ─────────────────────────────────────────────────────────────────

def log(msg: str):
    """Print and log to file. Handles Unicode safely on Windows."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"))
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ─── HTTP helpers with retry ─────────────────────────────────────────────────

def safe_get(url: str, params: dict = None, timeout: int = REQUEST_TIMEOUT,
             retries: int = MAX_RETRIES) -> dict | list | None:
    """GET request with retry, timeout, and error handling. Returns parsed JSON or None."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout)

            if resp.status_code == 429:
                wait = min(120, 15 * attempt)
                log(f"  Rate limited (429). Waiting {wait}s before retry {attempt}/{retries}...")
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                log(f"  Forbidden (403) from {url}. CoinGecko may require API key.")
                return None

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            log(f"  Timeout on attempt {attempt}/{retries}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError as e:
            log(f"  Connection error on attempt {attempt}/{retries}: {e}")
            time.sleep(RETRY_DELAY * attempt)
        except requests.exceptions.HTTPError as e:
            log(f"  HTTP error: {e}")
            if attempt < retries:
                time.sleep(RETRY_DELAY)
            else:
                return None
        except json.JSONDecodeError:
            log(f"  Invalid JSON response from {url}")
            return None
        except Exception as e:
            log(f"  Unexpected error: {type(e).__name__}: {e}")
            if attempt < retries:
                time.sleep(RETRY_DELAY)
            else:
                return None

    log(f"  Failed after {retries} retries: {url}")
    return None


# ─── Step 1: Get all Bybit USDT perpetual symbols ───────────────────────────

def get_bybit_symbols() -> list[str]:
    """Fetch all active USDT linear perpetual symbols from Bybit."""
    log("Fetching Bybit instrument list...")
    data = safe_get(f"{BYBIT_BASE}/v5/market/instruments-info",
                    params={"category": "linear", "limit": "1000"})
    if data is None or data.get("retCode") != 0:
        log("ERROR: Failed to fetch Bybit instruments")
        return []

    instruments = data["result"]["list"]
    symbols = [i["symbol"] for i in instruments
               if i["symbol"].endswith("USDT") and i["status"] == "Trading"]
    log(f"  Found {len(symbols)} active USDT perpetual pairs")
    return sorted(symbols)


# ─── Step 2: Get market caps from CoinGecko ─────────────────────────────────

def strip_bybit_prefix(symbol: str) -> str:
    """
    Strip USDT suffix and numeric prefixes from Bybit symbol.
    1000PEPEUSDT -> PEPE, 10000SATSUSDT -> SATS, BTCUSDT -> BTC
    """
    base = symbol.replace("USDT", "")
    # Strip leading digits (1000, 10000, 1000000, etc.)
    i = 0
    while i < len(base) and base[i].isdigit():
        i += 1
    stripped = base[i:] if i > 0 and i < len(base) else base
    return stripped.lower()


def get_coingecko_market_caps() -> dict:
    """
    Fetch market cap data from CoinGecko for top ~2000 coins.
    Returns dict: symbol_lower -> {market_cap, name, id, ...}
    """
    log("Fetching market cap data from CoinGecko...")
    all_coins = {}
    pages_to_fetch = 8  # 250 per page × 8 = 2000 coins

    for page in range(1, pages_to_fetch + 1):
        log(f"  CoinGecko page {page}/{pages_to_fetch}...")
        data = safe_get(f"{COINGECKO_BASE}/coins/markets", params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": "250",
            "page": str(page),
            "sparkline": "false",
        })

        if data is None:
            log(f"  WARNING: Failed to fetch page {page}, continuing with what we have")
            break

        if not isinstance(data, list) or len(data) == 0:
            log(f"  No more data at page {page}")
            break

        for coin in data:
            sym = coin.get("symbol", "").lower()
            mcap = coin.get("market_cap") or 0
            if sym and mcap > 0:
                # If duplicate symbol, keep the one with higher market cap
                if sym not in all_coins or mcap > all_coins[sym]["market_cap"]:
                    all_coins[sym] = {
                        "id": coin.get("id", ""),
                        "name": coin.get("name", ""),
                        "symbol": sym,
                        "market_cap": mcap,
                        "current_price": coin.get("current_price", 0),
                    }

        log(f"    Got {len(data)} coins (total unique: {len(all_coins)})")
        time.sleep(COINGECKO_RATE_LIMIT)

    log(f"  Total unique coins with market cap: {len(all_coins)}")
    return all_coins


def match_bybit_to_marketcap(bybit_symbols: list[str],
                              cg_data: dict) -> list[dict]:
    """
    Match Bybit symbols to CoinGecko market cap data.
    Returns list of matched coins, sorted by market cap descending.
    """
    matched = []
    unmatched = []

    for sym in bybit_symbols:
        base_lower = strip_bybit_prefix(sym)

        if base_lower in cg_data:
            info = cg_data[base_lower]
            matched.append({
                "bybit_symbol": sym,
                "name": info["name"],
                "market_cap": info["market_cap"],
                "price": info["current_price"],
                "cg_id": info["id"],
            })
        else:
            unmatched.append(sym)

    # Sort by market cap descending
    matched.sort(key=lambda x: x["market_cap"], reverse=True)

    log(f"  Matched: {len(matched)} | Unmatched: {len(unmatched)}")
    if unmatched and len(unmatched) <= 20:
        log(f"  Unmatched symbols: {', '.join(unmatched)}")
    elif unmatched:
        log(f"  Unmatched symbols (first 20): {', '.join(unmatched[:20])}...")

    return matched


# ─── Step 3: Filter and build coin list ──────────────────────────────────────

def build_coin_list(max_coins: int = None) -> list[dict]:
    """Full discovery pipeline: Bybit symbols -> CoinGecko market caps -> filtered list."""
    bybit_symbols = get_bybit_symbols()
    if not bybit_symbols:
        return []

    cg_data = get_coingecko_market_caps()
    if not cg_data:
        log("ERROR: No market cap data retrieved")
        return []

    matched = match_bybit_to_marketcap(bybit_symbols, cg_data)

    # Filter: market cap < $1B
    sub_1b = [c for c in matched if c["market_cap"] < MARKET_CAP_LIMIT]
    log(f"\nCoins with market cap < ${MARKET_CAP_LIMIT/1e9:.0f}B: {len(sub_1b)}")

    if max_coins:
        sub_1b = sub_1b[:max_coins]
        log(f"Limited to first {max_coins} coins")

    # Save to file for restartability
    COIN_LIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COIN_LIST_FILE, "w") as f:
        json.dump(sub_1b, f, indent=2)
    log(f"Coin list saved to {COIN_LIST_FILE}")

    return sub_1b


def load_coin_list() -> list[dict]:
    """Load previously saved coin list."""
    if not COIN_LIST_FILE.exists():
        log(f"ERROR: No saved coin list at {COIN_LIST_FILE}")
        log("Run without --skip-discovery first")
        return []
    with open(COIN_LIST_FILE) as f:
        coins = json.load(f)
    log(f"Loaded {len(coins)} coins from {COIN_LIST_FILE}")
    return coins


# ─── Step 4: Fetch candle data from Bybit ───────────────────────────────────

def fetch_page(session: requests.Session, symbol: str,
               start_ms: int, end_ms: int) -> list:
    """Fetch one page of 1m candles from Bybit."""
    data = safe_get(
        f"{BYBIT_BASE}/v5/market/kline",
        params={
            "category": "linear",
            "symbol": symbol,
            "interval": "1",
            "start": str(start_ms),
            "end": str(end_ms),
            "limit": str(BYBIT_MAX_CANDLES),
        },
    )
    if data is None or data.get("retCode") != 0:
        if data:
            log(f"    API error: {data.get('retMsg', 'unknown')}")
        return []
    return data.get("result", {}).get("list", []) or []


CACHE_TOLERANCE_MS = 48 * 60 * 60 * 1000  # 48 hours in milliseconds


def is_cached(symbol: str, start_ms: int, end_ms: int) -> bool:
    """Check if symbol already has cached data covering the requested range (within 48h tolerance)."""
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    meta_file = CACHE_DIR / f"{symbol}_1m.meta"
    if cache_file.exists() and meta_file.exists():
        try:
            meta = meta_file.read_text().strip().split(",")
            if len(meta) == 2:
                cached_start, cached_end = int(meta[0]), int(meta[1])
                if (cached_start <= start_ms + CACHE_TOLERANCE_MS and
                        cached_end >= end_ms - CACHE_TOLERANCE_MS):
                    return True
        except Exception:
            pass
    return False


def fetch_symbol_data(symbol: str, start_ms: int, end_ms: int,
                      session: requests.Session) -> bool:
    """
    Fetch all 1m candles for a symbol. Returns True on success.
    Paginates backward from end_ms (Bybit returns newest first).
    """
    import pandas as pd

    cursor = end_ms
    all_candles = []
    page = 0

    while cursor > start_ms:
        page += 1
        candles = fetch_page(session, symbol, start_ms, cursor)

        if not candles:
            if page == 1:
                log(f"    No data returned for {symbol}")
                return False
            break

        all_candles.extend(candles)

        # Oldest timestamp in this batch
        oldest_ts = min(int(c[0]) for c in candles)
        next_cursor = oldest_ts - 1
        if next_cursor >= cursor:
            break  # No progress
        cursor = next_cursor

        if len(candles) < BYBIT_MAX_CANDLES:
            break  # Last page

        time.sleep(BYBIT_RATE_LIMIT)

        if page % 50 == 0:
            pct = min(100, (end_ms - cursor) / max(1, end_ms - start_ms) * 100)
            log(f"    {symbol}: {len(all_candles):,} candles ({pct:.0f}%)...")

    if not all_candles:
        return False

    # Build DataFrame
    columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
    df = pd.DataFrame(all_candles, columns=columns)
    df["timestamp"] = pd.to_numeric(df["timestamp"])
    for col in ["open", "high", "low", "close", "volume", "turnover"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.rename(columns={"volume": "base_vol", "turnover": "quote_vol"})

    # Filter and deduplicate
    df = df[(df["timestamp"] >= start_ms) & (df["timestamp"] <= end_ms)]
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    # Save
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    meta_file = CACHE_DIR / f"{symbol}_1m.meta"
    df.to_parquet(cache_file, engine="pyarrow", index=False)
    meta_file.write_text(f"{start_ms},{end_ms}")

    return True


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fetch 3-month 1m data for sub-$1B market cap coins on Bybit"
    )
    parser.add_argument("--list-only", action="store_true",
                        help="Only build and display the coin list, don't fetch data")
    parser.add_argument("--skip-discovery", action="store_true",
                        help="Skip CoinGecko discovery, use saved coin list")
    parser.add_argument("--max-coins", type=int, default=None,
                        help="Max number of coins to process")
    parser.add_argument("--months", type=int, default=3,
                        help="Months of history to fetch (default: 3)")
    parser.add_argument("--start-from", type=int, default=0,
                        help="Start from coin index N (0-based, for resuming)")
    args = parser.parse_args()

    # Initialize log
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log("=" * 70)
    log("Four Pillars — Sub-$1B Market Cap Data Fetcher")
    log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    # Step 1: Get coin list
    if args.skip_discovery:
        coins = load_coin_list()
    else:
        coins = build_coin_list(max_coins=args.max_coins)

    if not coins:
        log("No coins to process. Exiting.")
        return

    # Apply --max-coins regardless of discovery mode
    if args.max_coins:
        coins = coins[:args.max_coins]

    # Display list (compact: show first 10, skip middle, show last 5 if >20)
    print()
    log(f"{'#':>4} {'Symbol':<25} {'Name':<25} {'Market Cap':>15} {'Price':>12}")
    log("-" * 85)
    show_all = len(coins) <= 20
    for i, c in enumerate(coins):
        if show_all or i < 10 or i >= len(coins) - 5:
            log(f"{i+1:>4} {c['bybit_symbol']:<25} {c['name'][:24]:<25} "
                f"${c['market_cap']:>14,.0f} ${c['price']:>10.4f}")
        elif i == 10:
            log(f"  ... ({len(coins) - 15} more coins) ...")
    log(f"\nTotal: {len(coins)} coins")

    if args.list_only:
        log("\n--list-only mode. Exiting without fetching data.")
        return

    # Step 2: Fetch data
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=args.months * 30)
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    log(f"\nFetching {args.months}-month 1m candles")
    log(f"Range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')} UTC")
    log(f"Cache: {CACHE_DIR}")
    log("")

    session = requests.Session()
    success = 0
    skipped = 0
    failed = 0
    failed_symbols = []
    consecutive_fails = 0

    total = len(coins)
    start_idx = args.start_from

    for i in range(start_idx, total):
        coin = coins[i]
        sym = coin["bybit_symbol"]
        pct = (i + 1) / total * 100

        # Check cache
        if is_cached(sym, start_ms, end_ms):
            log(f"[{i+1}/{total}] ({pct:5.1f}%) {sym:<20} CACHED — skipping")
            skipped += 1
            continue

        log(f"[{i+1}/{total}] ({pct:5.1f}%) {sym:<20} fetching...")

        try:
            ok = fetch_symbol_data(sym, start_ms, end_ms, session)
            if ok:
                cache_file = CACHE_DIR / f"{sym}_1m.parquet"
                size_mb = cache_file.stat().st_size / 1024 / 1024
                log(f"    OK — {size_mb:.1f} MB")
                success += 1
                consecutive_fails = 0
            else:
                log(f"    FAILED — no data")
                failed += 1
                failed_symbols.append(sym)
                consecutive_fails += 1
        except Exception as e:
            log(f"    ERROR: {type(e).__name__}: {e}")
            log(f"    {traceback.format_exc().splitlines()[-1]}")
            failed += 1
            failed_symbols.append(sym)
            consecutive_fails += 1

        # Adaptive backoff: escalate delay on consecutive failures
        if consecutive_fails >= 3:
            backoff = min(300, 30 * (consecutive_fails - 2))
            log(f"    WARNING: {consecutive_fails} consecutive failures — backing off {backoff}s...")
            time.sleep(backoff)
        elif consecutive_fails > 0:
            time.sleep(5)
        else:
            time.sleep(1)

    # Summary
    log("")
    log("=" * 70)
    log("FETCH COMPLETE")
    log("=" * 70)
    log(f"Success:  {success}")
    log(f"Skipped:  {skipped} (already cached)")
    log(f"Failed:   {failed}")
    log(f"Total:    {success + skipped + failed}/{total}")
    if failed_symbols:
        log(f"Failed:   {', '.join(failed_symbols)}")

    # Disk usage
    try:
        parquets = list(CACHE_DIR.glob("*_1m.parquet"))
        total_size = sum(f.stat().st_size for f in parquets)
        log(f"\nCache: {len(parquets)} files, {total_size / 1024 / 1024:.1f} MB total")
    except Exception:
        pass

    log(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    try:
        import pandas as pd
        import pyarrow
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install pandas pyarrow requests")
        sys.exit(1)

    main()
