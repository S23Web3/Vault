"""
Sanity check: Run Layer 1 + Layer 2 on RIVERUSDT 5m, print distribution stats.

Run: python scripts/sanity_check_bbw_sequence.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from signals.bbwp import calculate_bbwp
from signals.bbw_sequence import track_bbw_sequence


def main():
    """Run BBW Sequence sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBW Sequence Layer 2 Sanity Check -- {ts}")
    print(f"{'='*70}")

    cache_path = ROOT / "data" / "cache" / "RIVERUSDT_1m.parquet"
    if not cache_path.exists():
        print("ERROR: RIVERUSDT parquet not found")
        return

    raw = pd.read_parquet(cache_path)
    if 'datetime' not in raw.columns and 'timestamp' in raw.columns:
        raw['datetime'] = pd.to_datetime(raw['timestamp'], unit='ms', utc=True)
    raw = raw.set_index('datetime')
    df = raw.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'base_vol': 'sum'
    }).dropna().reset_index()

    print(f"\n  Input: {len(df):,} bars (5m)")

    # Layer 1
    t0 = time.time()
    df_l1 = calculate_bbwp(df)
    t1 = time.time()

    # Layer 2
    result = track_bbw_sequence(df_l1)
    t2 = time.time()

    l1_time = t1 - t0
    l2_time = t2 - t1
    total = t2 - t0
    print(f"  Layer 1: {l1_time:.2f}s ({len(df)/l1_time:,.0f} bars/sec)")
    print(f"  Layer 2: {l2_time:.2f}s ({len(df)/l2_time:,.0f} bars/sec)")
    print(f"  Total:   {total:.2f}s ({len(df)/total:,.0f} bars/sec)")

    valid = result[result['bbwp_spectrum'].notna()]
    nan_count = result['bbwp_spectrum'].isna().sum()
    print(f"  Valid bars: {len(valid):,}")
    print(f"  NaN warmup: {nan_count:,}")

    # Color Transition Frequency
    print(f"\n--- Color Transitions ---")
    cc_count = valid['bbw_seq_color_changed'].sum()
    cc_pct = cc_count / len(valid) * 100
    print(f"  Transitions: {int(cc_count):,} ({cc_pct:.1f}%)")

    # Direction Distribution
    print(f"\n--- Direction Distribution ---")
    dir_dist = valid['bbw_seq_direction'].value_counts()
    for d in ['flat', 'expanding', 'contracting']:
        count = dir_dist.get(d, 0)
        pct = count / len(valid) * 100
        print(f"  {d:15s} {count:6,} ({pct:5.1f}%)")
    none_dirs = valid['bbw_seq_direction'].isna().sum()
    print(f"  {'None':15s} {none_dirs:6,} ({none_dirs/len(valid)*100:5.1f}%)")

    # Skip Detection Rate
    print(f"\n--- Skip Detection ---")
    skip_count = valid['bbw_seq_skip_detected'].sum()
    skip_pct = skip_count / len(valid) * 100
    print(f"  Skips: {int(skip_count):,} ({skip_pct:.1f}%)")
    # Skip breakdown: which transitions caused skips
    skip_rows = valid[valid['bbw_seq_skip_detected'] == True]
    if len(skip_rows) > 0:
        skip_trans = []
        for _, row in skip_rows.iterrows():
            prev = row['bbw_seq_prev_color']
            curr = row['bbwp_spectrum']
            if prev and curr:
                skip_trans.append(f"{prev}->{curr}")
        if skip_trans:
            from collections import Counter
            top_skips = Counter(skip_trans).most_common(5)
            for trans, cnt in top_skips:
                print(f"    {trans}: {cnt:,}")

    # Top 10 Pattern IDs
    print(f"\n--- Top 10 Pattern IDs ---")
    pid_dist = valid['bbw_seq_pattern_id'].value_counts().head(10)
    for pid, count in pid_dist.items():
        pct = count / len(valid) * 100
        print(f"  {pid:6s} {count:6,} ({pct:5.1f}%)")

    # Bars in Color per color
    print(f"\n--- Bars in Color (per spectrum) ---")
    for color in ['blue', 'green', 'yellow', 'red']:
        rows = valid[valid['bbwp_spectrum'] == color]
        if len(rows) > 0:
            bic = rows['bbw_seq_bars_in_color']
            print(f"  {color:8s}  mean={bic.mean():5.1f}  median={bic.median():5.0f}  max={bic.max():5.0f}")

    # Bars in State per state
    print(f"\n--- Bars in State (per state) ---")
    for state in ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL',
                  'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE']:
        rows = valid[valid['bbwp_state'] == state]
        if len(rows) > 0:
            bis = rows['bbw_seq_bars_in_state']
            print(f"  {state:20s}  mean={bis.mean():5.1f}  median={bis.median():5.0f}  max={bis.max():5.0f}")

    # From Blue/Red Bars
    print(f"\n--- Distance from Blue/Red ---")
    fb = valid['bbw_seq_from_blue_bars'].dropna()
    fr = valid['bbw_seq_from_red_bars'].dropna()
    if len(fb) > 0:
        print(f"  from_blue: mean={fb.mean():.1f}  P50={fb.quantile(0.5):.0f}  P90={fb.quantile(0.9):.0f}")
    if len(fr) > 0:
        print(f"  from_red:  mean={fr.mean():.1f}  P50={fr.quantile(0.5):.0f}  P90={fr.quantile(0.9):.0f}")

    # NaN Check
    print(f"\n--- NaN Check (valid bars only) ---")
    for col in ['bbw_seq_bars_in_color', 'bbw_seq_bars_in_state',
                'bbw_seq_color_changed', 'bbw_seq_skip_detected']:
        nan_ct = valid[col].isna().sum()
        status = "OK" if nan_ct == 0 else f"WARN: {nan_ct} NaN"
        print(f"  {col:30s} {status}")

    print(f"\n{'='*70}")
    print(f"SANITY CHECK COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
