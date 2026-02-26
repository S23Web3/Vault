"""
Download 1m OHLCV data for all cached coins, split by year period.
File: PROJECTS/four-pillars-backtester/scripts/download_periods_v2.py

v2 changes from v1:
  - --all flag: chains 2023-2024 then 2024-2025 in one run
  - CoinGecko smart filtering: reads coin_market_history.parquet to skip coins
    that didn't exist in a given period (zero wasted API calls)
  - --yes flag: skip confirmation prompt (useful with --all)
  - Logs skipped coin counts per period

Usage:
  python scripts/download_periods_v2.py --all                          # Both periods, smart filter
  python scripts/download_periods_v2.py --all --yes                    # No confirmation prompt
  python scripts/download_periods_v2.py --period 2023-2024             # Single period
  python scripts/download_periods_v2.py --period 2024-2025 --yes       # Single, no prompt
  python scripts/download_periods_v2.py --period 2023-2024 --max-coins 5 --dry-run
  python scripts/download_periods_v2.py --period 2023-2024 --symbols BTCUSDT ETHUSDT
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
COINGECKO_DIR = ROOT / "data" / "coingecko"
CG_COIN_HISTORY = COINGECKO_DIR / "coin_market_history.parquet"

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

ALL_PERIODS = ["2023-2024", "2024-2025"]

RATE_LIMIT = 0.1        # seconds between API pages (default)
SYMBOL_PAUSE = 1.0      # seconds between symbols
MAX_RETRIES = 5
BASE_WAIT = 10           # exponential backoff base (seconds)

LISTING_DATES_FILE = PERIODS_DIR / "_coin_listing_dates.json"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str):
    """Print timestamped log message to stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode("ascii"))


# ---------------------------------------------------------------------------
# CoinGecko listing date lookup
# ---------------------------------------------------------------------------

def load_coingecko_listing_dates() -> dict:
    """
    Read coin_market_history.parquet and find the earliest date per symbol.
    Returns dict: {symbol: "YYYY-MM-DD"} or empty dict if file not found.
    """
    if not CG_COIN_HISTORY.exists():
        log("  WARNING: CoinGecko coin_market_history.parquet not found.")
        log("  Run: python scripts/fetch_coingecko_v2.py --reset")
        log("  Proceeding without smart filtering (all coins will be attempted).")
        return {}

    try:
        df = pd.read_parquet(CG_COIN_HISTORY, columns=["date", "symbol"])
        earliest = df.groupby("symbol")["date"].min().to_dict()
        log(f"  Loaded CoinGecko listing dates for {len(earliest)} coins")
        return earliest
    except Exception as e:
        log(f"  WARNING: Could not read CoinGecko data: {e}")
        return {}


def filter_coins_for_period(symbols: list, period: str,
                            cg_dates: dict) -> tuple:
    """
    Filter symbol list to only coins that existed before the period's end date.
    Returns (eligible_symbols, skipped_count).

    Logic:
      - If CoinGecko has a date for this symbol and it's AFTER the period ends,
        the coin didn't exist yet -> skip it.
      - If CoinGecko has no data for this symbol, keep it (let Bybit decide).
      - If CoinGecko data is empty (file not found), keep all coins.
    """
    if not cg_dates:
        return symbols, 0

    period_end = PERIODS[period]["end"].strftime("%Y-%m-%d")

    eligible = []
    skipped = 0
    for sym in symbols:
        earliest = cg_dates.get(sym)
        if earliest and earliest >= period_end:
            skipped += 1
        else:
            eligible.append(sym)

    return eligible, skipped


# ---------------------------------------------------------------------------
# Progress tracking (per period)
# ---------------------------------------------------------------------------

def state_file(period: str) -> Path:
    """Return path to JSON state file for a given period."""
    return PERIODS_DIR / f"_state_{period}.json"


def load_state(period: str) -> dict:
    """Load progress state from JSON file. Returns default dict if not found."""
    sf = state_file(period)
    if not sf.exists():
        return {"period": period, "completed": [], "no_data": [], "failed": []}
    try:
        return json.loads(sf.read_text())
    except Exception:
        return {"period": period, "completed": [], "no_data": [], "failed": []}


def save_state(st: dict):
    """Persist progress state to JSON file with UTC timestamp."""
    sf = state_file(st["period"])
    st["updated"] = datetime.now(timezone.utc).isoformat()
    sf.write_text(json.dumps(st, indent=2))


def load_listing_dates() -> dict:
    """Load coin listing dates from JSON. Used for cross-period skip logic."""
    if LISTING_DATES_FILE.exists():
        try:
            return json.loads(LISTING_DATES_FILE.read_text())
        except Exception:
            pass
    return {}


def save_listing_dates(ld: dict):
    """Persist coin listing dates to JSON for cross-period reuse."""
    LISTING_DATES_FILE.write_text(json.dumps(ld, indent=2))


# ---------------------------------------------------------------------------
# Low-level fetch (no file I/O)
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
# Run one period
# ---------------------------------------------------------------------------

def run_period(period: str, symbols: list, rate: float,
               dry_run: bool, auto_yes: bool, cg_dates: dict) -> dict:
    """
    Download one period for the given symbols.
    Returns stats dict with ok/no_data/error/skip counts.
    """
    period_cfg = PERIODS[period]
    start_ms = int(period_cfg["start"].timestamp() * 1000)
    end_ms = int(period_cfg["end"].timestamp() * 1000)

    output_dir = PERIODS_DIR / period
    output_dir.mkdir(parents=True, exist_ok=True)

    # Smart filter: skip coins that didn't exist in this period
    eligible, skipped = filter_coins_for_period(symbols, period, cg_dates)

    # Load progress
    st = load_state(period)
    done_set = set(st["completed"]) | set(st["no_data"])
    remaining = [s for s in eligible if s not in done_set]

    log("")
    log("=" * 80)
    log(f"DOWNLOAD PERIOD: {period}")
    log(f"  Range:         {period_cfg['start'].strftime('%Y-%m-%d')} to {period_cfg['end'].strftime('%Y-%m-%d')}")
    log(f"  Output:        {output_dir}")
    log(f"  Total cached:  {len(symbols)} symbols")
    log(f"  CG eligible:   {len(eligible)} symbols")
    log(f"  CG skipped:    {skipped} symbols (not listed before {period_cfg['end'].strftime('%Y-%m-%d')})")
    log(f"  Already done:  {len(done_set)} (completed={len(st['completed'])}, no_data={len(st['no_data'])})")
    log(f"  Remaining:     {len(remaining)}")
    log(f"  Rate:          {rate}s/page, {SYMBOL_PAUSE}s between symbols")
    log(f"  Dry run:       {dry_run}")
    log("=" * 80)

    if not remaining:
        log("All eligible symbols already processed.")
        return {"ok": 0, "no_data": 0, "error": 0, "skip": 0, "dry_run": 0,
                "total_bars": 0, "total_mb": 0.0, "cg_skipped": skipped,
                "eligible": len(eligible)}

    if not dry_run and not auto_yes:
        response = input("\nProceed? (yes/no): ")
        if response.strip().lower() != "yes":
            log("Cancelled.")
            return {"ok": 0, "no_data": 0, "error": 0, "skip": 0, "dry_run": 0,
                    "total_bars": 0, "total_mb": 0.0, "cg_skipped": skipped,
                    "eligible": len(eligible), "cancelled": True}

    fetcher = BybitFetcher(cache_dir=str(output_dir), rate_limit=rate)
    listing_dates = load_listing_dates()

    t0 = time.time()
    stats = {"ok": 0, "no_data": 0, "error": 0, "skip": 0, "dry_run": 0,
             "total_bars": 0, "total_mb": 0.0, "cg_skipped": skipped,
             "eligible": len(eligible)}

    for i, symbol in enumerate(remaining, 1):
        elapsed = time.time() - t0
        if i > 1 and elapsed > 0:
            rate_per_sym = elapsed / (i - 1)
            eta_s = rate_per_sym * (len(remaining) - i + 1)
            eta_m = eta_s / 60
            eta_str = f"ETA: {eta_m:.0f}m"
        else:
            eta_str = "ETA: --"

        log(f"[{i}/{len(remaining)}] {symbol}  ({eta_str})")

        result = process_symbol(fetcher, symbol, start_ms, end_ms,
                                output_dir, rate, dry_run)

        status = result["status"]
        stats[status] = stats.get(status, 0) + 1
        stats["total_bars"] += result["bars"]
        stats["total_mb"] += result["size_mb"]

        if status == "ok":
            log(f"  OK -- {result['bars']:,} bars, {result['size_mb']:.1f} MB")
            st["completed"].append(symbol)
            # Record earliest data timestamp as listing date
            meta_path = output_dir / f"{symbol}_1m.meta"
            if meta_path.exists():
                try:
                    parts = meta_path.read_text().strip().split(",")
                    listing_dates[symbol] = {
                        "earliest_ms": int(parts[0]),
                        "earliest_date": datetime.fromtimestamp(
                            int(parts[0]) / 1000, tz=timezone.utc
                        ).strftime("%Y-%m-%d"),
                        "source": "bybit",
                    }
                except Exception:
                    pass
        elif status == "no_data":
            log(f"  NO DATA -- coin not listed on Bybit in this period")
            st["no_data"].append(symbol)
            listing_dates[symbol] = {
                "no_data_before": period_cfg["end"].isoformat(),
                "period": period,
                "source": "bybit_empty",
            }
        elif status == "error":
            log(f"  ERROR -- {result['detail']}")
            st["failed"].append(symbol)
        elif status == "skip":
            log(f"  SKIP -- {result['detail']}")
            st["completed"].append(symbol)
        elif status == "dry_run":
            log(f"  DRY RUN -- would fetch")

        # Save progress after each coin (not on dry run)
        if not dry_run:
            save_state(st)
            save_listing_dates(listing_dates)

        if i < len(remaining):
            time.sleep(SYMBOL_PAUSE)

    elapsed = time.time() - t0

    log("")
    log("=" * 80)
    log(f"PERIOD {period} SUMMARY")
    log("=" * 80)
    log(f"  OK:           {stats['ok']}")
    log(f"  No data:      {stats['no_data']}")
    log(f"  Errors:       {stats['error']}")
    log(f"  Skipped:      {stats['skip']} (already downloaded)")
    log(f"  CG filtered:  {skipped} (not listed in period)")
    log(f"  Total bars:   {stats['total_bars']:,}")
    log(f"  Total size:   {stats['total_mb']:.1f} MB")
    log(f"  Runtime:      {elapsed/60:.1f} min")
    log(f"  Output:       {output_dir.resolve()}")
    log("=" * 80)

    if stats["error"] > 0:
        log(f"\nFailed symbols: {', '.join(st['failed'])}")
        log("Re-run the same command to retry failed symbols.")

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """CLI entry point. Parses args and runs one or both download periods."""
    parser = argparse.ArgumentParser(
        description="Download historical 1m data by period (v2: CoinGecko smart filter)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--period", choices=list(PERIODS.keys()),
                       help="Period to download: 2023-2024 or 2024-2025")
    group.add_argument("--all", action="store_true",
                       help="Download both periods sequentially (2023-2024 then 2024-2025)")
    parser.add_argument("--rate", type=float, default=RATE_LIMIT,
                        help=f"Seconds between API pages (default: {RATE_LIMIT})")
    parser.add_argument("--max-coins", type=int, default=None,
                        help="Limit to first N coins (for testing)")
    parser.add_argument("--symbols", nargs="+", default=None,
                        help="Specific symbols to download")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be downloaded without fetching")
    parser.add_argument("--yes", action="store_true",
                        help="Skip confirmation prompt")
    args = parser.parse_args()

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

    # Load CoinGecko listing dates for smart filtering
    log("Loading CoinGecko listing dates...")
    cg_dates = load_coingecko_listing_dates()

    # Determine which periods to run
    periods_to_run = ALL_PERIODS if args.all else [args.period]

    grand_stats = {"ok": 0, "no_data": 0, "error": 0, "skip": 0,
                   "total_bars": 0, "total_mb": 0.0, "cg_skipped": 0}
    grand_t0 = time.time()

    for period in periods_to_run:
        stats = run_period(period, symbols, args.rate,
                           args.dry_run, args.yes, cg_dates)

        if stats.get("cancelled"):
            log("Cancelled by user. Stopping.")
            return

        for key in ["ok", "no_data", "error", "skip", "total_bars", "cg_skipped"]:
            grand_stats[key] += stats.get(key, 0)
        grand_stats["total_mb"] += stats.get("total_mb", 0.0)

    # Grand summary if running --all
    if args.all:
        grand_elapsed = time.time() - grand_t0
        log("")
        log("=" * 80)
        log("GRAND SUMMARY (ALL PERIODS)")
        log("=" * 80)
        log(f"  Periods:      {', '.join(periods_to_run)}")
        log(f"  OK:           {grand_stats['ok']}")
        log(f"  No data:      {grand_stats['no_data']}")
        log(f"  Errors:       {grand_stats['error']}")
        log(f"  Skipped:      {grand_stats['skip']} (already downloaded)")
        log(f"  CG filtered:  {grand_stats['cg_skipped']} (total across periods)")
        log(f"  Total bars:   {grand_stats['total_bars']:,}")
        log(f"  Total size:   {grand_stats['total_mb']:.1f} MB")
        log(f"  Total time:   {grand_elapsed/60:.1f} min")
        log("=" * 80)


if __name__ == "__main__":
    main()
