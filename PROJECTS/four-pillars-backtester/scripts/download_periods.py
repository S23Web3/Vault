"""
Download 1m OHLCV data for all cached coins, split by year period.
Target periods: 2023-2024 and 2024-2025.
Writes to data/periods/{period}/ — NEVER touches data/cache/.

Resumable via progress JSON. Coins with no data for a period are recorded
in _coin_listing_dates.json for reference.

Usage:
  python scripts/download_periods.py --period 2023-2024
  python scripts/download_periods.py --period 2024-2025
  python scripts/download_periods.py --period 2023-2024 --max-coins 5 --dry-run
  python scripts/download_periods.py --period 2023-2024 --symbols BTCUSDT ETHUSDT
  python scripts/download_periods.py --period 2023-2024 --rate 0.05
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.fetcher import BybitFetcher

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_DIR = ROOT / "data" / "cache"
PERIODS_DIR = ROOT / "data" / "periods"

PERIODS = {
    "2023-2024": {
        "start": datetime(2023, 1, 1, tzinfo=timezone.utc),
        "end": datetime(2024, 1, 1, tzinfo=timezone.utc),
    },
    "2024-2025": {
        "start": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "end": datetime(2025, 1, 1, tzinfo=timezone.utc),
    },
}

RATE_LIMIT = 0.1        # seconds between API pages (default)
SYMBOL_PAUSE = 1.0      # seconds between symbols
MAX_RETRIES = 5
BASE_WAIT = 10           # exponential backoff base (seconds)

LISTING_DATES_FILE = PERIODS_DIR / "_coin_listing_dates.json"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"))


# ---------------------------------------------------------------------------
# Progress tracking (per period)
# ---------------------------------------------------------------------------

def state_file(period: str) -> Path:
    return PERIODS_DIR / f"_state_{period}.json"


def load_state(period: str) -> dict:
    sf = state_file(period)
    if not sf.exists():
        return {"period": period, "completed": [], "no_data": [], "failed": []}
    try:
        return json.loads(sf.read_text())
    except Exception:
        return {"period": period, "completed": [], "no_data": [], "failed": []}


def save_state(st: dict):
    sf = state_file(st["period"])
    st["updated"] = datetime.now(timezone.utc).isoformat()
    sf.write_text(json.dumps(st, indent=2))


def load_listing_dates() -> dict:
    if LISTING_DATES_FILE.exists():
        try:
            return json.loads(LISTING_DATES_FILE.read_text())
        except Exception:
            pass
    return {}


def save_listing_dates(ld: dict):
    LISTING_DATES_FILE.write_text(json.dumps(ld, indent=2))


# ---------------------------------------------------------------------------
# Low-level fetch (no file I/O) — reuses proven pattern from download_all_available.py
# ---------------------------------------------------------------------------

def fetch_range(fetcher: BybitFetcher, symbol: str,
                start_ms: int, end_ms: int, rate: float) -> list:
    """
    Fetch raw candles for a time range using _fetch_page() directly.
    Returns list of raw candle arrays. Empty list if no data.
    """
    if start_ms >= end_ms:
        return []

    cursor = end_ms
    all_candles = []
    page = 0

    while cursor > start_ms:
        page += 1

        candles = []
        for attempt in range(MAX_RETRIES):
            candles, rate_limited = fetcher._fetch_page(symbol, start_ms, cursor)
            if not rate_limited:
                break
            wait = BASE_WAIT * (2 ** attempt)
            log(f"    rate limited, waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
            time.sleep(wait)
        else:
            log(f"    rate limit not cleared after {MAX_RETRIES} retries, stopping")
            break

        if not candles:
            break

        all_candles.extend(candles)

        oldest_ts = min(int(c[0]) for c in candles)
        next_cursor = oldest_ts - 1
        if next_cursor >= cursor:
            break
        cursor = next_cursor

        if len(candles) < fetcher.MAX_CANDLES:
            break

        time.sleep(rate)

        if page % 50 == 0:
            pct = min(100, (end_ms - cursor) / max(1, end_ms - start_ms) * 100)
            log(f"    {len(all_candles):,} candles ({pct:.0f}%)...")

    return all_candles


def raw_to_df(candles: list) -> pd.DataFrame:
    """Convert raw Bybit candle arrays to DataFrame."""
    if not candles:
        return pd.DataFrame()

    cols = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
    df = pd.DataFrame(candles, columns=cols)
    df["timestamp"] = pd.to_numeric(df["timestamp"])
    for col in ["open", "high", "low", "close", "volume", "turnover"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.rename(columns={"volume": "base_vol", "turnover": "quote_vol"})
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

def sanity_check(df: pd.DataFrame, symbol: str) -> str | None:
    """Validate fetched data. Returns None if OK, error string if failed."""
    if len(df) == 0:
        return "empty dataframe"

    ohlc = ["open", "high", "low", "close"]
    null_count = int(df[ohlc].isnull().sum().sum())
    if null_count > 0:
        return f"null OHLC values: {null_count}"

    dupes = int(df.duplicated(subset=["timestamp"]).sum())
    if dupes > 0:
        return f"duplicate timestamps: {dupes}"

    ts = df["timestamp"].values
    if not (ts[:-1] <= ts[1:]).all():
        return "timestamps not sorted ascending"

    return None


# ---------------------------------------------------------------------------
# Process one symbol for one period
# ---------------------------------------------------------------------------

def process_symbol(fetcher: BybitFetcher, symbol: str,
                   start_ms: int, end_ms: int, output_dir: Path,
                   rate: float, dry_run: bool) -> dict:
    """
    Fetch and save one symbol for one period.
    Returns: {"status": "ok"|"no_data"|"error"|"skip", "bars": N, "size_mb": float, "detail": str}
    """
    parquet_path = output_dir / f"{symbol}_1m.parquet"
    meta_path = output_dir / f"{symbol}_1m.meta"

    # Never overwrite
    if parquet_path.exists():
        return {"status": "skip", "bars": 0, "size_mb": 0, "detail": "already exists"}

    if dry_run:
        return {"status": "dry_run", "bars": 0, "size_mb": 0, "detail": "would fetch"}

    # Fetch
    raw = fetch_range(fetcher, symbol, start_ms, end_ms, rate)

    if not raw:
        return {"status": "no_data", "bars": 0, "size_mb": 0, "detail": "no candles returned"}

    df = raw_to_df(raw)

    # Filter to exact period range
    df = df[(df["timestamp"] >= start_ms) & (df["timestamp"] <= end_ms)]

    if len(df) == 0:
        return {"status": "no_data", "bars": 0, "size_mb": 0, "detail": "empty after filter"}

    # Sanity
    err = sanity_check(df, symbol)
    if err:
        return {"status": "error", "bars": 0, "size_mb": 0, "detail": f"SANITY: {err}"}

    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    actual_start = int(df["timestamp"].min())
    actual_end = int(df["timestamp"].max())
    meta_path.write_text(f"{actual_start},{actual_end}")

    size_mb = parquet_path.stat().st_size / 1024 / 1024
    return {"status": "ok", "bars": len(df), "size_mb": size_mb, "detail": "saved"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download historical 1m data by period")
    parser.add_argument("--period", required=True, choices=list(PERIODS.keys()),
                        help="Period to download: 2023-2024 or 2024-2025")
    parser.add_argument("--rate", type=float, default=RATE_LIMIT,
                        help=f"Seconds between API pages (default: {RATE_LIMIT})")
    parser.add_argument("--max-coins", type=int, default=None,
                        help="Limit to first N coins (for testing)")
    parser.add_argument("--symbols", nargs="+", default=None,
                        help="Specific symbols to download")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be downloaded without fetching")
    args = parser.parse_args()

    period = args.period
    period_cfg = PERIODS[period]
    start_ms = int(period_cfg["start"].timestamp() * 1000)
    end_ms = int(period_cfg["end"].timestamp() * 1000)

    output_dir = PERIODS_DIR / period
    output_dir.mkdir(parents=True, exist_ok=True)
    PERIODS_DIR.mkdir(parents=True, exist_ok=True)

    # Build symbol list from existing cache
    if args.symbols:
        symbols = sorted(args.symbols)
    else:
        fetcher_tmp = BybitFetcher(cache_dir=str(CACHE_DIR))
        symbols = sorted(fetcher_tmp.list_cached())

    if not symbols:
        log("No symbols found in cache. Run fetch_sub_1b.py first.")
        return

    if args.max_coins:
        symbols = symbols[:args.max_coins]

    # Load progress
    st = load_state(period)
    done_set = set(st["completed"]) | set(st["no_data"])
    remaining = [s for s in symbols if s not in done_set]

    log("=" * 80)
    log(f"DOWNLOAD PERIOD: {period}")
    log(f"  Range:      {period_cfg['start'].strftime('%Y-%m-%d')} to {period_cfg['end'].strftime('%Y-%m-%d')}")
    log(f"  Output:     {output_dir}")
    log(f"  Total:      {len(symbols)} symbols")
    log(f"  Already:    {len(done_set)} (completed={len(st['completed'])}, no_data={len(st['no_data'])})")
    log(f"  Remaining:  {len(remaining)}")
    log(f"  Rate:       {args.rate}s/page, {SYMBOL_PAUSE}s between symbols")
    log(f"  Dry run:    {args.dry_run}")
    log("=" * 80)

    if not remaining:
        log("All symbols already processed. Delete state file to redo.")
        return

    if not args.dry_run:
        response = input("\nProceed? (yes/no): ")
        if response.strip().lower() != "yes":
            log("Cancelled.")
            return

    fetcher = BybitFetcher(cache_dir=str(output_dir), rate_limit=args.rate)
    listing_dates = load_listing_dates()

    t0 = time.time()
    stats = {"ok": 0, "no_data": 0, "error": 0, "skip": 0, "dry_run": 0,
             "total_bars": 0, "total_mb": 0.0}

    for i, symbol in enumerate(remaining, 1):
        log(f"[{i}/{len(remaining)}] {symbol}")

        result = process_symbol(fetcher, symbol, start_ms, end_ms,
                                output_dir, args.rate, args.dry_run)

        status = result["status"]
        stats[status] = stats.get(status, 0) + 1
        stats["total_bars"] += result["bars"]
        stats["total_mb"] += result["size_mb"]

        if status == "ok":
            log(f"  OK — {result['bars']:,} bars, {result['size_mb']:.1f} MB")
            st["completed"].append(symbol)
        elif status == "no_data":
            log(f"  NO DATA — coin likely not listed in this period")
            st["no_data"].append(symbol)
            listing_dates[symbol] = {"period": period, "status": "no_data"}
        elif status == "error":
            log(f"  ERROR — {result['detail']}")
            st["failed"].append(symbol)
        elif status == "skip":
            log(f"  SKIP — {result['detail']}")
            st["completed"].append(symbol)
        elif status == "dry_run":
            log(f"  DRY RUN — would fetch")

        # Save progress after each coin (not on dry run)
        if not args.dry_run:
            save_state(st)
            save_listing_dates(listing_dates)

        if i < len(remaining):
            time.sleep(SYMBOL_PAUSE)

    elapsed = time.time() - t0

    log("")
    log("=" * 80)
    log("SUMMARY")
    log("=" * 80)
    log(f"  OK:         {stats['ok']}")
    log(f"  No data:    {stats['no_data']}")
    log(f"  Errors:     {stats['error']}")
    log(f"  Skipped:    {stats['skip']}")
    log(f"  Total bars: {stats['total_bars']:,}")
    log(f"  Total size: {stats['total_mb']:.1f} MB")
    log(f"  Runtime:    {elapsed/60:.1f} min")
    log(f"  Output:     {output_dir.resolve()}")
    log("=" * 80)

    if stats["error"] > 0:
        log(f"\nFailed symbols: {', '.join(st['failed'])}")
        log("Re-run the same command to retry failed symbols.")


if __name__ == "__main__":
    main()
