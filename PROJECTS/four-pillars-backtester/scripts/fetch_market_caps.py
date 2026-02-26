"""
Fetch daily historical market cap data from CoinGecko for all coins
in data/sub_1b_coins.json. Requires paid API key in .env.

Output: data/market_caps/daily_historical.parquet
  Columns: date, symbol, market_cap, total_volume

Usage:
  python scripts/fetch_market_caps.py
  python scripts/fetch_market_caps.py --max-coins 5
  python scripts/fetch_market_caps.py --days 365
  python scripts/fetch_market_caps.py --dry-run
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COIN_LIST_FILE = ROOT / "data" / "sub_1b_coins.json"
OUTPUT_DIR = ROOT / "data" / "market_caps"
OUTPUT_FILE = OUTPUT_DIR / "daily_historical.parquet"
STATE_FILE = OUTPUT_DIR / "_fetch_state.json"
ENV_FILE = ROOT / ".env"

# CoinGecko Pro API (paid key)
CG_PRO_BASE = "https://pro-api.coingecko.com/api/v3"
CG_FREE_BASE = "https://api.coingecko.com/api/v3"

DEFAULT_DAYS = 1095  # 3 years
RATE_LIMIT_PRO = 0.5    # seconds between requests (paid: 500/min safe at 2/sec)
RATE_LIMIT_FREE = 7.0   # seconds between requests (free: ~10/min)
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"))


def load_env_key() -> str | None:
    """Load COINGECKO_API_KEY from .env file or environment."""
    # Check environment first
    key = os.environ.get("COINGECKO_API_KEY")
    if key:
        return key

    # Check .env file
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("COINGECKO_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val and val != "your_coingecko_api_key_here":
                    return val
    return None


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"completed": [], "failed": []}


def save_state(st: dict):
    st["updated"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(st, indent=2))


# ---------------------------------------------------------------------------
# CoinGecko API
# ---------------------------------------------------------------------------

def fetch_market_chart(cg_id: str, days: int, api_key: str | None,
                       session: requests.Session) -> list[dict] | None:
    """
    Fetch daily market cap and volume for a coin from CoinGecko.
    Returns list of {date, market_cap, total_volume} dicts or None on failure.
    """
    if api_key:
        base_url = CG_PRO_BASE
        headers = {"x-cg-pro-api-key": api_key}
        rate = RATE_LIMIT_PRO
    else:
        base_url = CG_FREE_BASE
        headers = {}
        rate = RATE_LIMIT_FREE

    url = f"{base_url}/coins/{cg_id}/market_chart"
    params = {"vs_currency": "usd", "days": str(days), "interval": "daily"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = min(120, 15 * attempt)
                log(f"    Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                log(f"    Forbidden (403) for {cg_id}. API key may be invalid.")
                return None

            if resp.status_code == 404:
                log(f"    Not found (404) for {cg_id}. Coin may be delisted.")
                return None

            resp.raise_for_status()
            data = resp.json()

            # Extract market_caps and total_volumes arrays
            # Format: [[timestamp_ms, value], [timestamp_ms, value], ...]
            mcaps = data.get("market_caps", [])
            volumes = data.get("total_volumes", [])

            # Build lookup for volumes by date
            vol_by_date = {}
            for ts_ms, vol in volumes:
                date_str = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                vol_by_date[date_str] = vol

            results = []
            for ts_ms, mcap in mcaps:
                date_str = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                results.append({
                    "date": date_str,
                    "market_cap": mcap,
                    "total_volume": vol_by_date.get(date_str, 0),
                })

            return results

        except requests.exceptions.Timeout:
            log(f"    Timeout attempt {attempt}/{MAX_RETRIES}")
            time.sleep(5 * attempt)
        except requests.exceptions.ConnectionError as e:
            log(f"    Connection error attempt {attempt}/{MAX_RETRIES}: {e}")
            time.sleep(5 * attempt)
        except Exception as e:
            log(f"    Error: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(5)
            else:
                return None

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch historical market cap from CoinGecko")
    parser.add_argument("--max-coins", type=int, default=None,
                        help="Limit to first N coins (for testing)")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"Days of history (default: {DEFAULT_DAYS})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be fetched without API calls")
    args = parser.parse_args()

    # Load coin list
    if not COIN_LIST_FILE.exists():
        log(f"ERROR: {COIN_LIST_FILE} not found. Run fetch_sub_1b.py first.")
        return

    with open(COIN_LIST_FILE) as f:
        coins = json.load(f)
    log(f"Loaded {len(coins)} coins from {COIN_LIST_FILE.name}")

    if args.max_coins:
        coins = coins[:args.max_coins]

    # Check API key
    api_key = load_env_key()
    if api_key:
        log(f"CoinGecko API key found (Pro tier)")
        rate = RATE_LIMIT_PRO
    else:
        log("WARNING: No COINGECKO_API_KEY found. Using free tier (slower, 365-day limit).")
        log("Add COINGECKO_API_KEY=xxx to .env for full 3-year history.")
        rate = RATE_LIMIT_FREE
        if args.days > 365:
            log(f"WARNING: Free tier limited to ~365 days. Requested {args.days} may be truncated.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load progress
    st = load_state()
    done_set = set(st["completed"])
    remaining = [c for c in coins if c["bybit_symbol"] not in done_set]

    log("")
    log("=" * 80)
    log("FETCH HISTORICAL MARKET CAP")
    log(f"  Days:       {args.days}")
    log(f"  API tier:   {'Pro' if api_key else 'Free'}")
    log(f"  Rate:       {rate}s between requests")
    log(f"  Total:      {len(coins)} coins")
    log(f"  Already:    {len(done_set)}")
    log(f"  Remaining:  {len(remaining)}")
    log(f"  Output:     {OUTPUT_FILE}")
    log(f"  Dry run:    {args.dry_run}")
    log("=" * 80)

    if not remaining:
        log("All coins already fetched. Delete state file to redo.")
        return

    if args.dry_run:
        for c in remaining[:20]:
            log(f"  Would fetch: {c['bybit_symbol']} (cg_id={c['cg_id']})")
        if len(remaining) > 20:
            log(f"  ... and {len(remaining) - 20} more")
        return

    response = input("\nProceed? (yes/no): ")
    if response.strip().lower() != "yes":
        log("Cancelled.")
        return

    session = requests.Session()
    all_rows = []
    stats = {"ok": 0, "no_data": 0, "error": 0}

    # Load any existing partial data
    if OUTPUT_FILE.exists():
        existing_df = pd.read_parquet(OUTPUT_FILE)
        all_rows = existing_df.to_dict("records")
        log(f"Loaded {len(all_rows)} existing rows from {OUTPUT_FILE.name}")

    t0 = time.time()

    for i, coin in enumerate(remaining, 1):
        symbol = coin["bybit_symbol"]
        cg_id = coin["cg_id"]
        log(f"[{i}/{len(remaining)}] {symbol} (cg_id={cg_id})")

        data = fetch_market_chart(cg_id, args.days, api_key, session)

        if data is None or len(data) == 0:
            log(f"  NO DATA")
            stats["no_data"] += 1
            st["failed"].append(symbol)
        else:
            # Add symbol to each row
            for row in data:
                row["symbol"] = symbol
            all_rows.extend(data)
            stats["ok"] += 1
            log(f"  OK — {len(data)} daily rows")
            st["completed"].append(symbol)

        save_state(st)

        # Incremental save every 25 coins
        if stats["ok"] % 25 == 0 and stats["ok"] > 0:
            _save_parquet(all_rows)
            log(f"  [checkpoint] Saved {len(all_rows)} total rows")

        if i < len(remaining):
            time.sleep(rate)

    # Final save
    _save_parquet(all_rows)

    elapsed = time.time() - t0

    log("")
    log("=" * 80)
    log("SUMMARY")
    log("=" * 80)
    log(f"  OK:         {stats['ok']}")
    log(f"  No data:    {stats['no_data']}")
    log(f"  Total rows: {len(all_rows):,}")
    log(f"  Runtime:    {elapsed/60:.1f} min")
    log(f"  Output:     {OUTPUT_FILE.resolve()}")
    if OUTPUT_FILE.exists():
        size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
        log(f"  File size:  {size_mb:.1f} MB")
    log("=" * 80)


def _save_parquet(rows: list):
    """Save accumulated rows to parquet."""
    if not rows:
        return
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["date", "symbol"]).sort_values(["symbol", "date"])
    df.to_parquet(OUTPUT_FILE, engine="pyarrow", index=False)


if __name__ == "__main__":
    main()
