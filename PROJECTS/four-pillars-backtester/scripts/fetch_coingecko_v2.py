"""
Comprehensive CoinGecko data fetcher — pulls everything useful in one run.
File: PROJECTS/four-pillars-backtester/scripts/fetch_coingecko_v2.py

Actions (run sequentially, each with its own progress bar):
  1. Per-coin historical market cap + volume (394 coins x 3 years daily)
  2. Global market data history (BTC dominance, total mcap, total vol)
  3. Coin categories/sectors (meme, L1, DeFi, gaming, etc.)
  4. Coin detail metadata (launch date, ATH, ATH date, ATH change %)
  5. Top gainers/losers snapshot (Analyst+ endpoint)

Outputs (all to data/coingecko/):
  coin_market_history.parquet   — daily market cap + volume per coin
  global_market_history.parquet — daily BTC dominance, total mcap, total vol
  coin_categories.json          — category/sector per coin
  coin_metadata.json            — launch date, ATH, ATH date, ATH change %
  top_movers.json               — current top gainers and losers

Progress: per-action status bar, ETA, API calls used, save locations, errors logged.
Resumable: state file tracks completed actions + per-coin progress.

Usage:
  python scripts/fetch_coingecko_v2.py                   # Full run (all 5 actions)
  python scripts/fetch_coingecko_v2.py --actions 1 2     # Only actions 1 and 2
  python scripts/fetch_coingecko_v2.py --max-coins 10    # Limit coins (testing)
  python scripts/fetch_coingecko_v2.py --reset            # Clear state, start fresh
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
OUTPUT_DIR = ROOT / "data" / "coingecko"
STATE_FILE = OUTPUT_DIR / "_fetch_state_v2.json"
LOG_FILE = OUTPUT_DIR / "_fetch_log.txt"
ENV_FILE = ROOT / ".env"

# Outputs
OUT_COIN_HISTORY = OUTPUT_DIR / "coin_market_history.parquet"
OUT_GLOBAL_HISTORY = OUTPUT_DIR / "global_market_history.parquet"
OUT_CATEGORIES = OUTPUT_DIR / "coin_categories.json"
OUT_METADATA = OUTPUT_DIR / "coin_metadata.json"
OUT_MOVERS = OUTPUT_DIR / "top_movers.json"

CG_PRO_BASE = "https://pro-api.coingecko.com/api/v3"
DEFAULT_DAYS = 1095  # 3 years
RATE_LIMIT = 0.12    # 0.12s = ~500 req/min (safe for 1000/min Analyst cap)
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_log_fh = None

def log(msg: str):
    global _log_fh
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"))
    if _log_fh:
        try:
            _log_fh.write(line + "\n")
            _log_fh.flush()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Progress bar
# ---------------------------------------------------------------------------

def progress_bar(current: int, total: int, width: int = 40,
                 prefix: str = "", suffix: str = "") -> str:
    """Render a text progress bar."""
    if total == 0:
        pct = 100.0
    else:
        pct = current / total * 100
    filled = int(width * current / max(total, 1))
    bar = "#" * filled + "-" * (width - filled)
    return f"{prefix}[{bar}] {current}/{total} ({pct:.1f}%) {suffix}"


def eta_str(elapsed_s: float, current: int, total: int) -> str:
    """Estimate time remaining."""
    if current == 0:
        return "ETA: calculating..."
    rate = elapsed_s / current
    remaining = rate * (total - current)
    if remaining < 60:
        return f"ETA: {remaining:.0f}s"
    elif remaining < 3600:
        return f"ETA: {remaining/60:.1f}m"
    else:
        return f"ETA: {remaining/3600:.1f}h"


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {
        "action1_completed": [],
        "action1_no_data": [],
        "action2_done": False,
        "action3_done": False,
        "action4_completed": [],
        "action4_no_data": [],
        "action5_done": False,
        "api_calls": 0,
        "errors": [],
    }


def save_state(st: dict):
    st["updated"] = datetime.now(timezone.utc).isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, indent=2))


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def load_env_key() -> str | None:
    key = os.environ.get("COINGECKO_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("COINGECKO_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val and val != "your_coingecko_api_key_here":
                    return val
    return None


def api_get(session: requests.Session, endpoint: str, params: dict,
            api_key: str, st: dict) -> dict | list | None:
    """
    Make a CoinGecko Pro API request with retries and error tracking.
    Returns parsed JSON or None on failure.
    """
    url = f"{CG_PRO_BASE}{endpoint}"
    headers = {"x-cg-pro-api-key": api_key}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            st["api_calls"] = st.get("api_calls", 0) + 1
            resp = session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = min(120, 15 * attempt)
                log(f"    RATE LIMITED (429). Waiting {wait}s... [attempt {attempt}/{MAX_RETRIES}]")
                st["errors"].append({"time": datetime.now().isoformat(), "type": "429",
                                     "endpoint": endpoint, "attempt": attempt})
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                log(f"    FORBIDDEN (403). Endpoint may require higher tier.")
                st["errors"].append({"time": datetime.now().isoformat(), "type": "403",
                                     "endpoint": endpoint})
                return None

            if resp.status_code == 404:
                return None  # Coin/resource not found — not an error

            resp.raise_for_status()
            return resp.json()

        except requests.exceptions.Timeout:
            log(f"    TIMEOUT attempt {attempt}/{MAX_RETRIES}")
            st["errors"].append({"time": datetime.now().isoformat(), "type": "timeout",
                                 "endpoint": endpoint, "attempt": attempt})
            time.sleep(5 * attempt)
        except requests.exceptions.ConnectionError as e:
            log(f"    CONNECTION ERROR attempt {attempt}/{MAX_RETRIES}: {e}")
            st["errors"].append({"time": datetime.now().isoformat(), "type": "connection",
                                 "endpoint": endpoint, "attempt": attempt})
            time.sleep(5 * attempt)
        except Exception as e:
            log(f"    ERROR: {type(e).__name__}: {e}")
            st["errors"].append({"time": datetime.now().isoformat(), "type": str(type(e).__name__),
                                 "endpoint": endpoint, "detail": str(e)})
            if attempt < MAX_RETRIES:
                time.sleep(5)
            else:
                return None

    return None


# ---------------------------------------------------------------------------
# ACTION 1: Per-coin historical market cap + volume
# ---------------------------------------------------------------------------

def action_1_coin_history(coins: list, api_key: str, session: requests.Session,
                          st: dict, days: int):
    """Fetch daily market cap + volume for each coin. ~394 API calls."""
    log("")
    log("=" * 80)
    log("ACTION 1/5: Per-Coin Historical Market Cap + Volume")
    log(f"  Coins: {len(coins)} | Days: {days} | Output: {OUT_COIN_HISTORY.name}")
    log("=" * 80)

    done_set = set(st["action1_completed"]) | set(st["action1_no_data"])
    remaining = [c for c in coins if c["bybit_symbol"] not in done_set]

    if not remaining:
        log("  All coins already fetched. Skipping.")
        return

    log(f"  Remaining: {len(remaining)} coins")

    # Load existing partial data
    all_rows = []
    if OUT_COIN_HISTORY.exists():
        existing_df = pd.read_parquet(OUT_COIN_HISTORY)
        all_rows = existing_df.to_dict("records")
        log(f"  Loaded {len(all_rows):,} existing rows")

    t0 = time.time()
    ok_count = 0
    no_data_count = 0

    for i, coin in enumerate(remaining, 1):
        symbol = coin["bybit_symbol"]
        cg_id = coin["cg_id"]
        elapsed = time.time() - t0

        # Progress bar
        bar = progress_bar(i, len(remaining), prefix="  ",
                           suffix=f"{symbol:<20} | API calls: {st['api_calls']} | {eta_str(elapsed, i-1, len(remaining))}")
        print(f"\r{bar}", end="", flush=True)

        data = api_get(session, f"/coins/{cg_id}/market_chart",
                       {"vs_currency": "usd", "days": str(days), "interval": "daily"},
                       api_key, st)

        if data is None:
            no_data_count += 1
            st["action1_no_data"].append(symbol)
            save_state(st)
            time.sleep(RATE_LIMIT)
            continue

        # Parse response
        mcaps = data.get("market_caps", [])
        volumes = data.get("total_volumes", [])

        if not mcaps:
            no_data_count += 1
            st["action1_no_data"].append(symbol)
            save_state(st)
            time.sleep(RATE_LIMIT)
            continue

        vol_by_date = {}
        for ts_ms, vol in volumes:
            date_str = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            vol_by_date[date_str] = vol

        for ts_ms, mcap in mcaps:
            date_str = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            all_rows.append({
                "date": date_str,
                "symbol": symbol,
                "market_cap": mcap,
                "total_volume": vol_by_date.get(date_str, 0),
            })

        ok_count += 1
        st["action1_completed"].append(symbol)
        save_state(st)

        # Checkpoint save every 50 coins
        if ok_count % 50 == 0:
            _save_coin_history(all_rows)
            print()  # newline after progress bar
            log(f"  [checkpoint] {ok_count} coins done, {len(all_rows):,} total rows saved")

        time.sleep(RATE_LIMIT)

    # Final save
    _save_coin_history(all_rows)
    elapsed = time.time() - t0

    print()  # newline after progress bar
    log(f"  DONE: {ok_count} OK, {no_data_count} no data, {elapsed:.0f}s elapsed")
    if OUT_COIN_HISTORY.exists():
        size_mb = OUT_COIN_HISTORY.stat().st_size / 1024 / 1024
        log(f"  Saved: {OUT_COIN_HISTORY.name} ({size_mb:.1f} MB, {len(all_rows):,} rows)")


def _save_coin_history(rows: list):
    if not rows:
        return
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["date", "symbol"]).sort_values(["symbol", "date"])
    df.to_parquet(OUT_COIN_HISTORY, engine="pyarrow", index=False)


# ---------------------------------------------------------------------------
# ACTION 2: Global market data history
# ---------------------------------------------------------------------------

def action_2_global_history(api_key: str, session: requests.Session,
                            st: dict, days: int):
    """Fetch historical BTC dominance, total market cap, total volume. 1 API call."""
    log("")
    log("=" * 80)
    log("ACTION 2/5: Global Market History (BTC Dominance, Total MCap, Total Vol)")
    log(f"  Days: {days} | Output: {OUT_GLOBAL_HISTORY.name}")
    log("=" * 80)

    if st.get("action2_done"):
        log("  Already fetched. Skipping.")
        return

    t0 = time.time()

    data = api_get(session, "/global/market_cap_chart",
                   {"days": str(days)}, api_key, st)

    if data is None:
        log("  FAILED: Could not fetch global market data")
        log("  NOTE: /global/market_cap_chart requires Analyst+ plan")
        return

    mcaps = data.get("market_cap_chart", {}).get("market_cap", [])
    volumes = data.get("market_cap_chart", {}).get("volume", [])

    if not mcaps:
        # Try alternate response format
        mcaps = data.get("market_caps", [])
        volumes = data.get("total_volumes", [])

    if not mcaps:
        log(f"  FAILED: Empty response. Keys: {list(data.keys())}")
        return

    vol_by_date = {}
    for ts_ms, vol in volumes:
        date_str = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        vol_by_date[date_str] = vol

    rows = []
    for ts_ms, mcap in mcaps:
        date_str = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append({
            "date": date_str,
            "total_market_cap": mcap,
            "total_volume": vol_by_date.get(date_str, 0),
        })

    if rows:
        df = pd.DataFrame(rows)
        df = df.drop_duplicates(subset=["date"]).sort_values("date")
        df.to_parquet(OUT_GLOBAL_HISTORY, engine="pyarrow", index=False)
        st["action2_done"] = True
        save_state(st)

        elapsed = time.time() - t0
        size_mb = OUT_GLOBAL_HISTORY.stat().st_size / 1024 / 1024
        log(f"  DONE: {len(df)} daily rows, {size_mb:.2f} MB, {elapsed:.1f}s")
        log(f"  Range: {df['date'].min()} to {df['date'].max()}")
    else:
        log("  FAILED: No rows parsed from response")


# ---------------------------------------------------------------------------
# ACTION 3: Category master list (sector-level market data)
# ---------------------------------------------------------------------------

def action_3_categories(api_key: str, session: requests.Session, st: dict):
    """Fetch category master list with aggregated market data. 1 API call."""
    log("")
    log("=" * 80)
    log("ACTION 3/5: Category Master List (sector-level market data)")
    log(f"  Output: {OUT_CATEGORIES.name}")
    log("=" * 80)

    if st.get("action3_done"):
        log("  Already fetched. Skipping.")
        return

    t0 = time.time()

    cat_data = api_get(session, "/coins/categories", {}, api_key, st)
    time.sleep(RATE_LIMIT)

    categories_list = []
    if cat_data and isinstance(cat_data, list):
        for cat in cat_data:
            categories_list.append({
                "id": cat.get("id", ""),
                "name": cat.get("name", ""),
                "market_cap": cat.get("market_cap", 0),
                "market_cap_change_24h": cat.get("market_cap_change_24h", 0),
                "volume_24h": cat.get("volume_24h", 0),
                "updated_at": cat.get("updated_at", ""),
            })
        log(f"  Found {len(categories_list)} categories")
    else:
        log("  WARNING: Could not fetch categories list")

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "categories": categories_list,
    }
    OUT_CATEGORIES.write_text(json.dumps(output, indent=2, default=str))
    st["action3_done"] = True
    save_state(st)

    elapsed = time.time() - t0
    log(f"  DONE: {len(categories_list)} categories, {elapsed:.1f}s")
    log(f"  Saved: {OUT_CATEGORIES.name}")


# ---------------------------------------------------------------------------
# ACTION 4: Coin detail — metadata + categories + ATH (single call per coin)
# ---------------------------------------------------------------------------

def action_4_coin_detail(coins: list, api_key: str, session: requests.Session,
                         st: dict):
    """
    Fetch per-coin detail via /coins/{id}. One call per coin extracts:
    categories, genesis_date, ATH/ATL, supply, market data snapshot.
    Saves both coin_metadata.json and populates category mappings.
    """
    log("")
    log("=" * 80)
    log("ACTION 4/5: Coin Detail (Categories + ATH + Launch + Supply)")
    log(f"  Coins: {len(coins)} | Output: {OUT_METADATA.name}")
    log("=" * 80)

    done_set = set(st.get("action4_completed", [])) | set(st.get("action4_no_data", []))
    remaining = [c for c in coins if c["bybit_symbol"] not in done_set]

    if not remaining:
        log("  All coins already fetched. Skipping.")
        return

    log(f"  Remaining: {len(remaining)} coins")

    # Load existing
    existing_meta = {}
    if OUT_METADATA.exists():
        try:
            raw = json.loads(OUT_METADATA.read_text())
            if "coins" in raw:
                existing_meta = raw["coins"]
        except Exception:
            existing_meta = {}

    t0 = time.time()
    ok_count = 0
    no_data_count = 0

    for i, coin in enumerate(remaining, 1):
        symbol = coin["bybit_symbol"]
        cg_id = coin["cg_id"]
        elapsed = time.time() - t0

        bar = progress_bar(i, len(remaining), prefix="  ",
                           suffix=f"{symbol:<20} | API: {st['api_calls']} | {eta_str(elapsed, i-1, len(remaining))}")
        print(f"\r{bar}", end="", flush=True)

        data = api_get(session, f"/coins/{cg_id}",
                       {"localization": "false", "tickers": "false",
                        "community_data": "false", "developer_data": "false",
                        "sparkline": "false"},
                       api_key, st)

        if data and isinstance(data, dict):
            md = data.get("market_data", {}) or {}
            existing_meta[symbol] = {
                "cg_id": cg_id,
                "name": data.get("name"),
                "symbol": data.get("symbol"),
                # Categories & classification
                "categories": [c for c in (data.get("categories") or []) if c],
                "hashing_algorithm": data.get("hashing_algorithm"),
                "genesis_date": data.get("genesis_date"),
                "country_origin": data.get("country_origin"),
                "description_length": len((data.get("description") or {}).get("en", "") or ""),
                "platforms": list((data.get("platforms") or {}).keys()),
                "asset_platform_id": data.get("asset_platform_id"),
                # All-time high / low
                "ath_usd": (md.get("ath") or {}).get("usd"),
                "ath_date_usd": (md.get("ath_date") or {}).get("usd"),
                "ath_change_pct_usd": (md.get("ath_change_percentage") or {}).get("usd"),
                "atl_usd": (md.get("atl") or {}).get("usd"),
                "atl_date_usd": (md.get("atl_date") or {}).get("usd"),
                "atl_change_pct_usd": (md.get("atl_change_percentage") or {}).get("usd"),
                # Current market data snapshot
                "current_price_usd": (md.get("current_price") or {}).get("usd"),
                "market_cap_usd": (md.get("market_cap") or {}).get("usd"),
                "market_cap_rank": md.get("market_cap_rank"),
                "fully_diluted_valuation": (md.get("fully_diluted_valuation") or {}).get("usd"),
                # Supply
                "total_supply": md.get("total_supply"),
                "max_supply": md.get("max_supply"),
                "circulating_supply": md.get("circulating_supply"),
                # Price changes (multiple windows)
                "price_change_24h_pct": md.get("price_change_percentage_24h"),
                "price_change_7d_pct": md.get("price_change_percentage_7d"),
                "price_change_14d_pct": md.get("price_change_percentage_14d"),
                "price_change_30d_pct": md.get("price_change_percentage_30d"),
                "price_change_60d_pct": md.get("price_change_percentage_60d"),
                "price_change_200d_pct": md.get("price_change_percentage_200d"),
                "price_change_1y_pct": md.get("price_change_percentage_1y"),
                # Volume
                "total_volume_usd": (md.get("total_volume") or {}).get("usd"),
                # High/Low
                "high_24h_usd": (md.get("high_24h") or {}).get("usd"),
                "low_24h_usd": (md.get("low_24h") or {}).get("usd"),
                # Sentiment (if available)
                "sentiment_votes_up_pct": data.get("sentiment_votes_up_percentage"),
                "sentiment_votes_down_pct": data.get("sentiment_votes_down_percentage"),
                "watchlist_portfolio_users": data.get("watchlist_portfolio_users"),
            }
            ok_count += 1
            st.setdefault("action4_completed", []).append(symbol)
        else:
            no_data_count += 1
            st.setdefault("action4_no_data", []).append(symbol)

        save_state(st)

        # Checkpoint every 50 coins
        if ok_count % 50 == 0 and ok_count > 0:
            _save_metadata(existing_meta)
            print()
            log(f"  [checkpoint] {ok_count} coins saved, {no_data_count} no data")

        time.sleep(RATE_LIMIT)

    # Final save
    _save_metadata(existing_meta)
    elapsed = time.time() - t0

    print()
    log(f"  DONE: {ok_count} OK, {no_data_count} no data, {elapsed:.0f}s elapsed")
    log(f"  Saved: {OUT_METADATA.name}")


def _save_metadata(meta: dict):
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "coin_count": len(meta),
        "coins": meta,
    }
    OUT_METADATA.write_text(json.dumps(output, indent=2, default=str))


# ---------------------------------------------------------------------------
# ACTION 5: Top gainers/losers snapshot
# ---------------------------------------------------------------------------

def action_5_movers(api_key: str, session: requests.Session, st: dict):
    """Fetch current top gainers and losers. 2 API calls."""
    log("")
    log("=" * 80)
    log("ACTION 5/5: Top Gainers & Losers Snapshot")
    log(f"  Output: {OUT_MOVERS.name}")
    log("=" * 80)

    if st.get("action5_done"):
        log("  Already fetched. Skipping.")
        return

    t0 = time.time()
    result = {"fetched_at": datetime.now(timezone.utc).isoformat()}

    # Top gainers
    log("  Fetching top gainers...")
    gainers = api_get(session, "/coins/top_gainers_losers",
                      {"vs_currency": "usd", "duration": "24h"}, api_key, st)
    time.sleep(RATE_LIMIT)

    if gainers and isinstance(gainers, dict):
        result["top_gainers"] = gainers.get("top_gainers", [])[:30]
        result["top_losers"] = gainers.get("top_losers", [])[:30]
        log(f"  Gainers: {len(result.get('top_gainers', []))}, Losers: {len(result.get('top_losers', []))}")
    elif gainers and isinstance(gainers, list):
        result["top_gainers"] = gainers[:30]
        result["top_losers"] = []
        log(f"  Got {len(gainers)} movers (list format)")
    else:
        log("  WARNING: Could not fetch gainers/losers (may require Analyst+ plan)")
        result["top_gainers"] = []
        result["top_losers"] = []

    # Trending coins
    log("  Fetching trending coins...")
    trending = api_get(session, "/search/trending", {}, api_key, st)
    time.sleep(RATE_LIMIT)

    if trending and isinstance(trending, dict):
        coins_trending = trending.get("coins", [])
        result["trending"] = [
            {
                "name": c.get("item", {}).get("name"),
                "symbol": c.get("item", {}).get("symbol"),
                "market_cap_rank": c.get("item", {}).get("market_cap_rank"),
                "price_btc": c.get("item", {}).get("price_btc"),
            }
            for c in coins_trending[:15]
        ]
        log(f"  Trending: {len(result['trending'])} coins")
    else:
        result["trending"] = []

    OUT_MOVERS.write_text(json.dumps(result, indent=2, default=str))
    st["action5_done"] = True
    save_state(st)

    elapsed = time.time() - t0
    log(f"  DONE: {elapsed:.1f}s elapsed")
    log(f"  Saved: {OUT_MOVERS.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global _log_fh

    parser = argparse.ArgumentParser(description="Comprehensive CoinGecko data fetcher")
    parser.add_argument("--actions", nargs="+", type=int, default=[1, 2, 3, 4, 5],
                        help="Which actions to run (1-5, default: all)")
    parser.add_argument("--max-coins", type=int, default=None,
                        help="Limit coins for testing")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"Days of history for actions 1,2 (default: {DEFAULT_DAYS})")
    parser.add_argument("--reset", action="store_true",
                        help="Clear state file and start fresh")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _log_fh = open(LOG_FILE, "a", encoding="utf-8")

    # Load API key
    api_key = load_env_key()
    if not api_key:
        log("ERROR: No COINGECKO_API_KEY found in .env")
        log("Add: COINGECKO_API_KEY=your_key_here")
        return

    # Load coin list
    if not COIN_LIST_FILE.exists():
        log(f"ERROR: {COIN_LIST_FILE} not found. Run fetch_sub_1b.py first.")
        return

    with open(COIN_LIST_FILE) as f:
        coins = json.load(f)

    if args.max_coins:
        coins = coins[:args.max_coins]

    # State
    if args.reset and STATE_FILE.exists():
        STATE_FILE.unlink()
        log("State file cleared.")
    st = load_state()

    # Estimate API calls
    calls_estimate = 0
    if 1 in args.actions:
        done_1 = len(set(st["action1_completed"]) | set(st["action1_no_data"]))
        calls_estimate += max(0, len(coins) - done_1)
    if 2 in args.actions and not st.get("action2_done"):
        calls_estimate += 1
    if 3 in args.actions and not st.get("action3_done"):
        calls_estimate += 1  # just the categories master list
    if 4 in args.actions:
        done_4 = len(set(st.get("action4_completed", [])) | set(st.get("action4_no_data", [])))
        calls_estimate += max(0, len(coins) - done_4)  # 1 call per coin (categories + metadata combined)
    if 5 in args.actions and not st.get("action5_done"):
        calls_estimate += 2

    time_estimate_s = calls_estimate * RATE_LIMIT
    time_estimate_m = time_estimate_s / 60

    log("")
    log("=" * 80)
    log("COINGECKO COMPREHENSIVE DATA FETCH")
    log("=" * 80)
    log(f"  API key:      {api_key[:12]}...")
    log(f"  Coins:        {len(coins)}")
    log(f"  Days:         {args.days}")
    log(f"  Actions:      {args.actions}")
    log(f"  Rate:         {RATE_LIMIT}s/request ({1/RATE_LIMIT:.0f} req/s)")
    log(f"  Est. calls:   ~{calls_estimate}")
    log(f"  Est. time:    ~{time_estimate_m:.1f} min")
    log(f"  Calls used:   {st.get('api_calls', 0)} (previous sessions)")
    log(f"  Output dir:   {OUTPUT_DIR}")
    log(f"  Log file:     {LOG_FILE.name}")
    log("")
    log("  Actions:")
    action_names = {
        1: "Per-coin historical market cap + volume (394 coins x 3yr daily)",
        2: "Global market history (total mcap + total vol, 3yr daily)",
        3: "Category master list (sector-level market data, 1 call)",
        4: "Coin detail: categories + ATH + launch + supply (394 coins)",
        5: "Top gainers/losers + trending snapshot (2 calls)",
    }
    for a in sorted(args.actions):
        status = "PENDING"
        if a == 1:
            done = len(set(st["action1_completed"]) | set(st["action1_no_data"]))
            status = f"{done}/{len(coins)} coins done" if done > 0 else "PENDING"
        elif a == 2 and st.get("action2_done"):
            status = "DONE"
        elif a == 3 and st.get("action3_done"):
            status = "DONE"
        elif a == 4:
            done = len(set(st.get("action4_completed", [])) | set(st.get("action4_no_data", [])))
            status = f"{done}/{len(coins)} coins done" if done > 0 else "PENDING"
        elif a == 5 and st.get("action5_done"):
            status = "DONE"
        log(f"    [{a}] {action_names[a]} [{status}]")
    log("=" * 80)

    response = input("\nProceed? (yes/no): ")
    if response.strip().lower() != "yes":
        log("Cancelled.")
        return

    session = requests.Session()
    t0_total = time.time()

    # Execute actions
    if 1 in args.actions:
        action_1_coin_history(coins, api_key, session, st, args.days)

    if 2 in args.actions:
        action_2_global_history(api_key, session, st, args.days)

    if 3 in args.actions:
        action_3_categories(api_key, session, st)

    if 4 in args.actions:
        action_4_coin_detail(coins, api_key, session, st)

    if 5 in args.actions:
        action_5_movers(api_key, session, st)

    # Final summary
    elapsed_total = time.time() - t0_total

    log("")
    log("=" * 80)
    log("FINAL SUMMARY")
    log("=" * 80)
    log(f"  Total API calls:  {st.get('api_calls', 0)}")
    log(f"  Total errors:     {len(st.get('errors', []))}")
    log(f"  Total runtime:    {elapsed_total/60:.1f} min")
    log("")
    log("  Output files:")
    for f in [OUT_COIN_HISTORY, OUT_GLOBAL_HISTORY, OUT_CATEGORIES, OUT_METADATA, OUT_MOVERS]:
        if f.exists():
            size = f.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            log(f"    {f.name:<40} {size_str:>10}")
        else:
            log(f"    {f.name:<40} {'NOT CREATED':>10}")
    log("")
    log(f"  State file:  {STATE_FILE.name}")
    log(f"  Log file:    {LOG_FILE.name}")
    log("=" * 80)

    if _log_fh:
        _log_fh.close()


if __name__ == "__main__":
    main()
