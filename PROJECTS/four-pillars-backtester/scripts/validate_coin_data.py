"""
Validate all coin data across all period directories + cache.
Reports: coverage, gaps, data quality, OHLC sanity, duplicate bars.

Run: python scripts/validate_coin_data.py
Optional: python scripts/validate_coin_data.py --interval 5m
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PERIOD_DIRS = [
    ("2023-2024", ROOT / "data" / "periods" / "2023-2024"),
    ("2024-2025", ROOT / "data" / "periods" / "2024-2025"),
    ("cache",     ROOT / "data" / "cache"),
]

TWO_DAYS_MS = 2 * 24 * 60 * 60 * 1000


def get_symbols(directory, suffix):
    """Return set of symbol names from parquet files in directory."""
    if not directory.exists():
        return set()
    return {f.name.replace(suffix, "") for f in directory.glob(f"*{suffix}")}


def check_single_file(filepath):
    """Validate a single parquet file and return stats dict."""
    try:
        df = pd.read_parquet(filepath)
    except Exception as e:
        return {"error": str(e), "bars": 0}

    n = len(df)
    if n == 0:
        return {"error": "empty file", "bars": 0}

    ts = pd.to_numeric(df["timestamp"], errors="coerce").values
    start_dt = pd.to_datetime(ts.min(), unit="ms", utc=True)
    end_dt = pd.to_datetime(ts.max(), unit="ms", utc=True)

    # Duplicates
    dupes = int(pd.Series(ts).duplicated().sum())

    # OHLC sanity
    ohlc_bad = 0
    if all(c in df.columns for c in ["open", "high", "low", "close"]):
        h = df["high"].values
        l = df["low"].values
        o = df["open"].values
        c = df["close"].values
        ohlc_bad = int(((h < l) | (h < o) | (h < c) | (l > o) | (l > c)).sum())

    # Zero volume bars
    zero_vol = 0
    if "base_vol" in df.columns:
        zero_vol = int((df["base_vol"] == 0).sum())

    return {
        "bars": n,
        "start": start_dt.strftime("%Y-%m-%d"),
        "end": end_dt.strftime("%Y-%m-%d"),
        "dupes": dupes,
        "ohlc_bad": ohlc_bad,
        "zero_vol": zero_vol,
        "start_ts": int(ts.min()),
        "end_ts": int(ts.max()),
    }


def check_combined_gaps(symbol, interval, expected_gap_ms):
    """Load all periods for one symbol, check for gaps > 2 days."""
    suffix = f"_{interval}.parquet"
    parts = []

    for name, d in PERIOD_DIRS:
        fp = d / f"{symbol}{suffix}"
        if fp.exists():
            try:
                df = pd.read_parquet(fp, columns=["timestamp"])
                if len(df) > 0:
                    parts.append(df)
            except Exception:
                pass

    if not parts:
        return None, []

    combined = pd.concat(parts, ignore_index=True)
    combined["timestamp"] = pd.to_numeric(combined["timestamp"], errors="coerce")
    combined = combined.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    ts = combined["timestamp"].values

    if len(ts) < 2:
        return len(ts), []

    diffs = ts[1:] - ts[:-1]
    big_gaps = []
    for i in range(len(diffs)):
        if diffs[i] > TWO_DAYS_MS:
            gap_start = pd.to_datetime(ts[i], unit="ms", utc=True)
            gap_end = pd.to_datetime(ts[i + 1], unit="ms", utc=True)
            gap_hours = diffs[i] / 3_600_000
            big_gaps.append({
                "from": gap_start.strftime("%Y-%m-%d %H:%M"),
                "to": gap_end.strftime("%Y-%m-%d %H:%M"),
                "hours": round(gap_hours, 1),
                "days": round(gap_hours / 24, 1),
            })

    return len(ts), big_gaps


def main():
    """Run full coin data validation."""
    interval = "1m"
    if len(sys.argv) > 1 and sys.argv[1] == "--interval":
        interval = sys.argv[2] if len(sys.argv) > 2 else "5m"

    suffix = f"_{interval}.parquet"
    expected_gap_ms = 60_000 if interval == "1m" else 300_000

    print("=" * 80)
    print(f"COIN DATA VALIDATION -- {interval} interval")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 80)

    # Gather all symbols
    all_symbols = set()
    source_symbols = {}
    for name, d in PERIOD_DIRS:
        syms = get_symbols(d, suffix)
        source_symbols[name] = syms
        all_symbols |= syms
        print(f"\n  {name}: {len(syms)} coins  ({d})")

    print(f"\n  Total unique symbols: {len(all_symbols)}")

    # Overlap analysis
    s1 = source_symbols.get("2023-2024", set())
    s2 = source_symbols.get("2024-2025", set())
    sc = source_symbols.get("cache", set())

    in_all_3 = s1 & s2 & sc
    in_p2_cache = (s2 & sc) - s1
    in_p1_cache = (s1 & sc) - s2
    cache_only = sc - s1 - s2
    p2_only = s2 - sc - s1
    p1_only = s1 - sc - s2

    print(f"\n{'='*80}")
    print("COVERAGE OVERLAP")
    print(f"{'='*80}")
    print(f"  In all 3 sources:        {len(in_all_3)}")
    print(f"  2024-2025 + cache only:  {len(in_p2_cache)}")
    print(f"  2023-2024 + cache only:  {len(in_p1_cache)}")
    print(f"  Cache only:              {len(cache_only)}")
    print(f"  2024-2025 only:          {len(p2_only)}")
    print(f"  2023-2024 only:          {len(p1_only)}")

    # Per-file validation
    print(f"\n{'='*80}")
    print("PER-FILE VALIDATION")
    print(f"{'='*80}")

    file_issues = []
    total_files = 0
    total_bars = 0
    total_dupes = 0
    total_ohlc_bad = 0
    total_zero_vol = 0

    for name, d in PERIOD_DIRS:
        if not d.exists():
            continue
        files = sorted(d.glob(f"*{suffix}"))
        issues_in_source = 0
        for fp in files:
            total_files += 1
            sym = fp.name.replace(suffix, "")
            stats = check_single_file(fp)
            total_bars += stats.get("bars", 0)
            total_dupes += stats.get("dupes", 0)
            total_ohlc_bad += stats.get("ohlc_bad", 0)
            total_zero_vol += stats.get("zero_vol", 0)

            if stats.get("error"):
                file_issues.append(f"  {name}/{sym}: ERROR -- {stats['error']}")
                issues_in_source += 1
            elif stats["dupes"] > 0 or stats["ohlc_bad"] > 0:
                file_issues.append(
                    f"  {name}/{sym}: {stats['bars']:,} bars, "
                    f"{stats['dupes']} dupes, {stats['ohlc_bad']} OHLC bad"
                )
                issues_in_source += 1

        print(f"  {name}: {len(files)} files checked, {issues_in_source} with issues")

    if file_issues:
        print(f"\n  Files with issues ({len(file_issues)}):")
        for issue in file_issues[:20]:
            print(issue)
        if len(file_issues) > 20:
            print(f"  ... and {len(file_issues) - 20} more")
    else:
        print("\n  All files clean (no dupes, no OHLC errors)")

    print(f"\n  Totals: {total_files} files, {total_bars:,} bars, "
          f"{total_dupes} dupes, {total_ohlc_bad} OHLC bad, {total_zero_vol} zero-vol bars")

    # Gap analysis (combined across sources)
    print(f"\n{'='*80}")
    print("GAP ANALYSIS (combined across all sources, gaps > 2 days)")
    print(f"{'='*80}")

    coins_with_gaps = []
    coins_clean = 0
    coins_single_source = 0

    for sym in sorted(all_symbols):
        sources = sum(1 for n, d in PERIOD_DIRS if (d / f"{sym}{suffix}").exists())
        if sources < 2:
            coins_single_source += 1
            continue

        total, gaps = check_combined_gaps(sym, interval, expected_gap_ms)
        if gaps:
            coins_with_gaps.append((sym, gaps))
        else:
            coins_clean += 1

    print(f"  Coins with multi-source data: {coins_clean + len(coins_with_gaps)}")
    print(f"  Clean (no gaps > 2 days):     {coins_clean}")
    print(f"  With gaps > 2 days:           {len(coins_with_gaps)}")
    print(f"  Single-source only:           {coins_single_source}")

    if coins_with_gaps:
        # Summarize gap patterns
        all_gaps = []
        for sym, gaps in coins_with_gaps:
            for g in gaps:
                all_gaps.append(g)

        gap_days = [g["days"] for g in all_gaps]
        print(f"\n  Total gaps found: {len(all_gaps)}")
        print(f"  Gap range: {min(gap_days):.0f}d to {max(gap_days):.0f}d")

        # Group by similar gap
        from collections import Counter
        rounded = [round(d) for d in gap_days]
        counts = Counter(rounded)
        print(f"\n  Gap distribution:")
        for days, cnt in sorted(counts.items()):
            print(f"    ~{days}d: {cnt} coins")

        # Show first 10 examples
        print(f"\n  First 10 examples:")
        for sym, gaps in coins_with_gaps[:10]:
            for g in gaps:
                print(f"    {sym}: {g['from']} -> {g['to']} ({g['days']}d)")

    # Final verdict
    print(f"\n{'='*80}")
    print("VERDICT")
    print(f"{'='*80}")

    issues = []
    if coins_with_gaps:
        issues.append(f"{len(coins_with_gaps)} coins have gaps > 2 days")
    if total_dupes > 0:
        issues.append(f"{total_dupes} duplicate timestamps across all files")
    if total_ohlc_bad > 0:
        issues.append(f"{total_ohlc_bad} bars with invalid OHLC")

    if not issues:
        print("  CLEAN -- All coin data is continuous, deduplicated, and OHLC-valid.")
    else:
        print("  ISSUES FOUND:")
        for issue in issues:
            print(f"    - {issue}")

    print(f"\n{'='*80}")


if __name__ == "__main__":
    main()
