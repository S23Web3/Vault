"""
SANITY CHECK: Validate all cached parquet files.
Categorizes each coin into: COMPLETE, PARTIAL (rate-limited, retryable), NEW_LISTING (no earlier data exists), QUALITY issues.
Writes retryable symbols to data/cache/_retry_symbols.txt for download script.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache"
HIST_DIR = ROOT / "data" / "historical"
TARGET_START = datetime(2025, 2, 11, tzinfo=timezone.utc)
# Coins listed after this date can't have data before it — not retryable
NEW_LISTING_THRESHOLD_DAYS = 200  # gap > 200 days = probably a new listing


def check_file(path):
    """Returns dict of stats or None on read error."""
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        return {"error": str(e)}

    if len(df) == 0:
        return {"error": "empty file", "bars": 0}

    ts_col = "timestamp"
    if ts_col not in df.columns:
        return {"error": f"no '{ts_col}' column, cols={list(df.columns)}"}

    df[ts_col] = pd.to_numeric(df[ts_col], errors="coerce")
    df = df.sort_values(ts_col).reset_index(drop=True)

    dt = pd.to_datetime(df[ts_col], unit="ms", utc=True)
    earliest = dt.min()
    latest = dt.max()
    bars = len(df)

    # Duplicates
    dupes = int(df.duplicated(subset=[ts_col]).sum())

    # Nulls in OHLC
    ohlc = ["open", "high", "low", "close"]
    ohlc_present = [c for c in ohlc if c in df.columns]
    nulls = int(df[ohlc_present].isnull().any(axis=1).sum()) if ohlc_present else 0

    # Expected bars (1m candles between earliest and latest)
    span_minutes = (latest - earliest).total_seconds() / 60
    expected = int(span_minutes) + 1
    completeness = bars / expected * 100 if expected > 0 else 0

    # Gap from target start
    gap_days = max(0, (earliest - TARGET_START).days) if earliest > TARGET_START else 0

    return {
        "bars": bars,
        "earliest": earliest,
        "latest": latest,
        "earliest_str": earliest.strftime("%Y-%m-%d"),
        "latest_str": latest.strftime("%Y-%m-%d"),
        "dupes": dupes,
        "nulls": nulls,
        "completeness": round(completeness, 1),
        "gap_days": gap_days,
    }


def main():
    files = sorted(CACHE_DIR.glob("*_1m.parquet"))
    hist_files = set(f.name for f in HIST_DIR.glob("*_1m.parquet")) if HIST_DIR.exists() else set()

    print("=" * 90)
    print(f"SANITY CHECK: {len(files)} parquet files in cache/")
    print(f"Target start: {TARGET_START.strftime('%Y-%m-%d')}")
    print("=" * 90)

    categories = {"complete": [], "partial": [], "new_listing": [], "error": [], "quality": []}
    total_bars = 0
    has_hist = 0

    for f in files:
        symbol = f.stem.replace("_1m", "")
        result = check_file(f)

        if "error" in result:
            categories["error"].append((symbol, result.get("error", "")))
            continue

        total_bars += result["bars"]
        if f.name in hist_files:
            has_hist += 1

        if result["dupes"] > 0 or result["nulls"] > 0:
            categories["quality"].append((symbol, result["dupes"], result["nulls"]))

        if result["gap_days"] == 0:
            categories["complete"].append(symbol)
        elif result["gap_days"] >= NEW_LISTING_THRESHOLD_DAYS:
            # Large gap = coin probably didn't exist, Bybit returned no data
            categories["new_listing"].append((symbol, result["gap_days"], result["earliest_str"]))
        else:
            # Smaller gap = likely rate-limited mid-download, retryable
            categories["partial"].append((symbol, result["gap_days"], result["earliest_str"], result["bars"]))

    # Summary
    print(f"\n{'SUMMARY':=^90}")
    print(f"  Total files:       {len(files)}")
    print(f"  COMPLETE:          {len(categories['complete'])}  (data starts at or before {TARGET_START.strftime('%Y-%m-%d')})")
    print(f"  PARTIAL (retry):   {len(categories['partial'])}  (gap < {NEW_LISTING_THRESHOLD_DAYS}d, likely rate-limited)")
    print(f"  NEW LISTING:       {len(categories['new_listing'])}  (gap >= {NEW_LISTING_THRESHOLD_DAYS}d, coin didn't exist yet)")
    print(f"  READ ERRORS:       {len(categories['error'])}")
    print(f"  QUALITY ISSUES:    {len(categories['quality'])}  (dupes or null OHLC)")
    print(f"  In historical/:    {has_hist}")
    print(f"  Total bars:        {total_bars:,}")

    # Partial — retryable
    if categories["partial"]:
        print(f"\n{'PARTIAL - RETRYABLE (' + str(len(categories['partial'])) + ')':=^90}")
        for sym, gap, earliest, bars in sorted(categories["partial"]):
            print(f"  {sym:<30s} gap={gap:>3d}d  starts={earliest}  bars={bars:>10,}")

    # New listings — not retryable
    if categories["new_listing"]:
        print(f"\n{'NEW LISTINGS - NOT RETRYABLE (' + str(len(categories['new_listing'])) + ')':=^90}")
        for sym, gap, earliest in sorted(categories["new_listing"])[:20]:
            print(f"  {sym:<30s} gap={gap:>3d}d  starts={earliest}")
        if len(categories["new_listing"]) > 20:
            print(f"  ... and {len(categories['new_listing']) - 20} more")

    # Quality
    if categories["quality"]:
        print(f"\n{'QUALITY ISSUES (' + str(len(categories['quality'])) + ')':=^90}")
        for sym, dupes, nulls in sorted(categories["quality"]):
            print(f"  {sym:<30s} dupes={dupes}  null_ohlc={nulls}")

    # Errors
    if categories["error"]:
        print(f"\n{'READ ERRORS (' + str(len(categories['error'])) + ')':=^90}")
        for sym, err in sorted(categories["error"]):
            print(f"  {sym}: {err}")

    # Write retryable symbols to file for download script
    retry_file = CACHE_DIR / "_retry_symbols.txt"
    retry_symbols = [sym for sym, _, _, _ in categories["partial"]]
    retry_file.write_text("\n".join(sorted(retry_symbols)))
    print(f"\n{'=' * 90}")
    print(f"Wrote {len(retry_symbols)} retryable symbols to {retry_file}")
    print(f"Run: python scripts\\download_1year_gap_FIXED.py --retry")
    print("=" * 90)


if __name__ == "__main__":
    main()
