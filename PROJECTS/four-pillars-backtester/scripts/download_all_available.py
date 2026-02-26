"""
Download ALL available data for 399 cached coins.
Target: 2025-11-02 to present. Coins listed after that date get all data from listing.

Safety:
  - Full backup of data/cache/ before any writes
  - Per-symbol sanity check: merged data must pass 6 checks or original is preserved
  - Restartable via progress file

Usage:
  python scripts/download_all_available.py
  python scripts/download_all_available.py --force
  python scripts/download_all_available.py --symbols BTCUSDT ETHUSDT
  python scripts/download_all_available.py --rate 0.1
"""

import sys
import json
import shutil
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.fetcher import BybitFetcher

CACHE_DIR = ROOT / "data" / "cache"
CSV_DIR = ROOT / "data" / "csv"
PROGRESS_FILE = CACHE_DIR / "_download_progress.json"

TARGET_START = datetime(2025, 11, 2, tzinfo=timezone.utc)
TARGET_START_MS = int(TARGET_START.timestamp() * 1000)

RATE_LIMIT = 0.05       # seconds between API pages
SYMBOL_PAUSE = 1.0      # seconds between symbols
MAX_RETRIES = 5
BASE_WAIT = 10           # exponential backoff base (seconds)


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def backup_cache(cache_dir: Path) -> Path:
    """Copy all *_1m.parquet and *_1m.meta files to a timestamped backup dir."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = cache_dir.parent / f"cache_backup_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    src_files = list(cache_dir.glob("*_1m.parquet")) + list(cache_dir.glob("*_1m.meta"))
    for f in src_files:
        shutil.copy2(f, backup_dir / f.name)

    # Verify
    backed_up = len(list(backup_dir.glob("*")))
    if backed_up != len(src_files):
        print(f"BACKUP VERIFICATION FAILED: expected {len(src_files)}, got {backed_up}")
        sys.exit(1)

    print(f"BACKUP: {backup_dir}")
    print(f"  {backed_up} files copied")
    return backup_dir


# ---------------------------------------------------------------------------
# Progress (restartability)
# ---------------------------------------------------------------------------

def load_progress() -> set:
    """Return set of completed symbols. Empty set if no progress or different target."""
    if not PROGRESS_FILE.exists():
        return set()
    try:
        data = json.loads(PROGRESS_FILE.read_text())
        if data.get("target_start") != TARGET_START.isoformat():
            return set()
        return set(data.get("completed", []))
    except Exception:
        return set()


def save_progress(completed: set):
    """Persist completed symbols to progress file."""
    data = {
        "target_start": TARGET_START.isoformat(),
        "completed": sorted(completed),
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    PROGRESS_FILE.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Low-level fetch (no file side-effects)
# ---------------------------------------------------------------------------

def fetch_range(fetcher: BybitFetcher, symbol: str, start_ms: int, end_ms: int) -> list:
    """
    Fetch raw candles for a time range using _fetch_page() directly.
    Returns list of raw candle arrays. Empty list if no data.
    No file I/O -- caller handles persistence.
    """
    if start_ms >= end_ms:
        return []

    cursor = end_ms
    all_candles = []
    page = 0

    while cursor > start_ms:
        page += 1

        # Retry loop for rate limits
        candles = []
        for attempt in range(MAX_RETRIES):
            candles, rate_limited = fetcher._fetch_page(symbol, start_ms, cursor)
            if not rate_limited:
                break
            wait = BASE_WAIT * (2 ** attempt)
            print(f"    rate limited, waiting {wait}s (attempt {attempt+1}/{MAX_RETRIES})...")
            time.sleep(wait)
        else:
            print(f"    rate limit not cleared after {MAX_RETRIES} retries, stopping range")
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

        time.sleep(RATE_LIMIT)

        if page % 50 == 0:
            pct = min(100, (end_ms - cursor) / max(1, end_ms - start_ms) * 100)
            print(f"    {len(all_candles)} candles ({pct:.0f}%)...")

    return all_candles


def raw_to_df(candles: list) -> pd.DataFrame:
    """Convert raw Bybit candle arrays to DataFrame. Returns empty DF if no candles."""
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
# Sanity check on merged data
# ---------------------------------------------------------------------------

def sanity_check(merged_df: pd.DataFrame, original_df: pd.DataFrame, symbol: str) -> Optional[str]:
    """
    Validate merged data against original. Returns None if OK, error string if failed.
    """
    # 1. Row count: merged >= original
    if len(merged_df) < len(original_df):
        return f"row count shrunk: {len(merged_df)} < {len(original_df)}"

    # 2. No null OHLC
    ohlc = ["open", "high", "low", "close"]
    null_count = int(merged_df[ohlc].isnull().sum().sum())
    if null_count > 0:
        return f"null OHLC values: {null_count}"

    # 3. No duplicate timestamps
    dupes = int(merged_df.duplicated(subset=["timestamp"]).sum())
    if dupes > 0:
        return f"duplicate timestamps: {dupes}"

    # 4. Sorted ascending
    ts = merged_df["timestamp"].values
    if not (ts[:-1] <= ts[1:]).all():
        return "timestamps not sorted ascending"

    # 5. Earliest <= original earliest
    merged_earliest = merged_df["timestamp"].min()
    orig_earliest = original_df["timestamp"].min()
    if merged_earliest > orig_earliest:
        return f"earliest truncated: {merged_earliest} > {orig_earliest}"

    # 6. Latest >= original latest
    merged_latest = merged_df["timestamp"].max()
    orig_latest = original_df["timestamp"].max()
    if merged_latest < orig_latest:
        return f"latest truncated: {merged_latest} < {orig_latest}"

    return None


# ---------------------------------------------------------------------------
# 5m resampling
# ---------------------------------------------------------------------------

def resample_5m(df_1m: pd.DataFrame) -> pd.DataFrame:
    """Resample 1m DataFrame to 5m."""
    df = df_1m.copy()
    df = df.set_index("datetime")
    df_5m = df.resample("5min").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "base_vol": "sum",
        "quote_vol": "sum",
        "timestamp": "first",
    }).dropna(subset=["close"]).reset_index()
    return df_5m


# ---------------------------------------------------------------------------
# Per-symbol processing
# ---------------------------------------------------------------------------

def process_symbol(fetcher: BybitFetcher, symbol: str, now_ms: int) -> dict:
    """
    Process one symbol: backward fill + forward fill + merge + sanity + save.
    Returns status dict.
    """
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    meta_file = CACHE_DIR / f"{symbol}_1m.meta"

    result = {"symbol": symbol, "status": "error", "bars_added": 0, "total_bars": 0, "detail": ""}

    # Load existing
    if not cache_file.exists():
        result["detail"] = "no cache file"
        return result

    try:
        original_df = pd.read_parquet(cache_file)
    except Exception as e:
        result["detail"] = f"read error: {e}"
        return result

    if len(original_df) == 0 or "timestamp" not in original_df.columns:
        result["detail"] = "empty or no timestamp column"
        return result

    original_df["timestamp"] = pd.to_numeric(original_df["timestamp"], errors="coerce")
    if "datetime" not in original_df.columns:
        original_df["datetime"] = pd.to_datetime(original_df["timestamp"], unit="ms", utc=True)

    earliest_ms = int(original_df["timestamp"].min())
    latest_ms = int(original_df["timestamp"].max())
    original_bars = len(original_df)

    # Backward gap
    backward_end_ms = earliest_ms - 60_000  # 1 min before earliest
    backward_candles = []
    if TARGET_START_MS < earliest_ms:
        backward_candles = fetch_range(fetcher, symbol, TARGET_START_MS, backward_end_ms)

    backward_df = raw_to_df(backward_candles)

    # Forward gap
    forward_start_ms = latest_ms + 60_000  # 1 min after latest
    forward_candles = []
    if forward_start_ms < now_ms:
        forward_candles = fetch_range(fetcher, symbol, forward_start_ms, now_ms)

    forward_df = raw_to_df(forward_candles)

    # Merge
    parts = []
    if len(backward_df) > 0:
        parts.append(backward_df)
    parts.append(original_df)
    if len(forward_df) > 0:
        parts.append(forward_df)

    if len(parts) == 1 and len(backward_candles) == 0 and len(forward_candles) == 0:
        # Nothing new fetched, still mark as done
        result["status"] = "unchanged"
        result["total_bars"] = original_bars
        result["detail"] = "already up to date"
        # Still export CSV
        _export_csv(original_df, symbol)
        return result

    merged_df = pd.concat(parts, ignore_index=True)
    merged_df = merged_df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    # Ensure datetime column is correct after merge
    merged_df["datetime"] = pd.to_datetime(merged_df["timestamp"], unit="ms", utc=True)

    # Sanity check
    err = sanity_check(merged_df, original_df, symbol)
    if err is not None:
        result["detail"] = f"SANITY FAIL: {err}"
        # Export CSV of original (safe) data only
        _export_csv(original_df, symbol)
        return result

    bars_added = len(merged_df) - original_bars

    # Save 1m parquet + meta
    merged_df.to_parquet(cache_file, engine="pyarrow", index=False)
    actual_start = int(merged_df["timestamp"].min())
    actual_end = int(merged_df["timestamp"].max())
    meta_file.write_text(f"{actual_start},{actual_end}")

    # Save 5m parquet + meta
    df_5m = resample_5m(merged_df)
    if len(df_5m) > 0:
        path_5m = CACHE_DIR / f"{symbol}_5m.parquet"
        meta_5m = CACHE_DIR / f"{symbol}_5m.meta"
        df_5m.to_parquet(path_5m, engine="pyarrow", index=False)
        start_5m = int(df_5m["timestamp"].min())
        end_5m = int(df_5m["timestamp"].max())
        meta_5m.write_text(f"{start_5m},{end_5m}")

    # Export CSV
    _export_csv(merged_df, symbol)

    result["status"] = "updated" if bars_added > 0 else "unchanged"
    result["bars_added"] = bars_added
    result["total_bars"] = len(merged_df)
    bw = len(backward_df) if len(backward_df) > 0 else 0
    fw = len(forward_df) if len(forward_df) > 0 else 0
    result["detail"] = f"+{bw} back, +{fw} fwd"
    return result


def _export_csv(df: pd.DataFrame, symbol: str):
    """Export DataFrame to CSV in data/csv/."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = CSV_DIR / f"{symbol}_1m.csv"
    df.to_csv(csv_path, index=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global RATE_LIMIT

    parser = argparse.ArgumentParser(description="Download all available data since 2025-11-02")
    parser.add_argument("--force", action="store_true", help="Ignore progress, redo all symbols")
    parser.add_argument("--symbols", nargs="+", help="Process specific symbols only")
    parser.add_argument("--rate", type=float, default=RATE_LIMIT, help="Seconds between API pages")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup (use if backup already exists)")
    args = parser.parse_args()

    RATE_LIMIT = args.rate

    fetcher = BybitFetcher(cache_dir=str(CACHE_DIR), rate_limit=args.rate)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Get symbol list
    if args.symbols:
        symbols = sorted(args.symbols)
    else:
        symbols = sorted(fetcher.list_cached())

    if not symbols:
        print("No cached symbols found.")
        return

    # Backup
    if not args.no_backup:
        print("=" * 80)
        print("STEP 1: BACKUP")
        print("=" * 80)
        backup_dir = backup_cache(CACHE_DIR)
        print()
    else:
        backup_dir = None
        print("Backup skipped (--no-backup flag)")

    # Load progress
    completed = set() if args.force else load_progress()
    remaining = [s for s in symbols if s not in completed]

    print("=" * 80)
    print(f"DOWNLOAD ALL AVAILABLE DATA")
    print(f"  Target start:  {TARGET_START.strftime('%Y-%m-%d')} (or listing date if later)")
    print(f"  Target end:    now")
    print(f"  Total symbols: {len(symbols)}")
    print(f"  Already done:  {len(completed)}")
    print(f"  Remaining:     {len(remaining)}")
    print(f"  Rate limit:    {RATE_LIMIT}s/page, {SYMBOL_PAUSE}s between symbols")
    if backup_dir:
        print(f"  Backup:        {backup_dir}")
    print("=" * 80)

    if not remaining:
        print("\nAll symbols already processed. Use --force to redo.")
        _print_output_paths(backup_dir)
        return

    response = input("\nProceed? (yes/no): ")
    if response.strip().lower() != "yes":
        print("Cancelled.")
        return

    t0 = time.time()
    stats = {"updated": 0, "unchanged": 0, "error": 0, "sanity_fail": 0, "total_bars_added": 0}

    for i, symbol in enumerate(remaining, 1):
        print(f"\n[{i}/{len(remaining)}] {symbol}", end=" ", flush=True)

        result = process_symbol(fetcher, symbol, now_ms)

        if result["status"] == "updated":
            stats["updated"] += 1
            stats["total_bars_added"] += result["bars_added"]
            print(f"OK +{result['bars_added']:,} bars ({result['detail']})")
        elif result["status"] == "unchanged":
            stats["unchanged"] += 1
            print(f"unchanged ({result['detail']})")
        else:
            if "SANITY FAIL" in result["detail"]:
                stats["sanity_fail"] += 1
                print(f"SANITY FAIL: {result['detail']}")
            else:
                stats["error"] += 1
                print(f"ERROR: {result['detail']}")

        # Save progress only for successful symbols (errors/sanity fails retry next run)
        if result["status"] in ("updated", "unchanged"):
            completed.add(symbol)
            save_progress(completed)

        if i < len(remaining):
            time.sleep(SYMBOL_PAUSE)

    elapsed = time.time() - t0

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Updated:       {stats['updated']}")
    print(f"  Unchanged:     {stats['unchanged']}")
    print(f"  Sanity fails:  {stats['sanity_fail']}  (originals preserved)")
    print(f"  Errors:        {stats['error']}")
    print(f"  Bars added:    {stats['total_bars_added']:,}")
    print(f"  Runtime:       {elapsed/60:.1f} min")

    _print_output_paths(backup_dir)


def _print_output_paths(backup_dir):
    """Print final output locations."""
    print("\n" + "=" * 80)
    print("OUTPUT LOCATIONS")
    print("=" * 80)
    if backup_dir:
        backup_count = len(list(backup_dir.glob("*_1m.parquet")))
        print(f"  BACKUP:  {backup_dir.resolve()}  ({backup_count} parquet files)")
    print(f"  PARQUET: {CACHE_DIR.resolve()}")
    print(f"  CSV:     {CSV_DIR.resolve()}")
    csv_count = len(list(CSV_DIR.glob("*_1m.csv"))) if CSV_DIR.exists() else 0
    print(f"  CSV files: {csv_count}")
    print("=" * 80)
    print(f"\nRun command:")
    print(f"  cd PROJECTS\\four-pillars-backtester")
    print(f"  python scripts\\download_all_available.py")


if __name__ == "__main__":
    main()
