"""
Sanity check: Run calculate_bbwp on RIVERUSDT 5m, print detailed distributions.

Run: python scripts/sanity_check_bbwp.py
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


def main():
    """Run BBWP sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBWP Layer 1 Sanity Check -- {ts}")
    print(f"{'='*70}")

    cache_path = ROOT / "data" / "cache" / "RIVERUSDT_1m.parquet"
    if not cache_path.exists():
        print("ERROR: RIVERUSDT parquet not found")
        return

    # Load and resample to 5m
    raw = pd.read_parquet(cache_path)
    if 'datetime' not in raw.columns and 'timestamp' in raw.columns:
        raw['datetime'] = pd.to_datetime(raw['timestamp'], unit='ms', utc=True)
    raw = raw.set_index('datetime')
    df = raw.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'base_vol': 'sum'
    }).dropna().reset_index()

    print(f"\n  Input: {len(df):,} bars (5m)")

    # Run BBWP
    t0 = time.time()
    result = calculate_bbwp(df)
    elapsed = time.time() - t0
    print(f"  Runtime: {elapsed:.2f}s ({len(df)/elapsed:,.0f} bars/sec)")

    valid = result.dropna(subset=['bbwp_value'])
    nan_count = result['bbwp_value'].isna().sum()
    print(f"  Valid BBWP bars: {len(valid):,}")
    print(f"  NaN warmup bars: {nan_count:,}")

    # BBWP Distribution
    print(f"\n--- BBWP Value Distribution ---")
    print(f"  Mean:   {valid['bbwp_value'].mean():.1f}")
    print(f"  Std:    {valid['bbwp_value'].std():.1f}")
    print(f"  Min:    {valid['bbwp_value'].min():.1f}")
    print(f"  Max:    {valid['bbwp_value'].max():.1f}")
    print(f"  P10:    {valid['bbwp_value'].quantile(0.10):.1f}")
    print(f"  P25:    {valid['bbwp_value'].quantile(0.25):.1f}")
    print(f"  P50:    {valid['bbwp_value'].quantile(0.50):.1f}")
    print(f"  P75:    {valid['bbwp_value'].quantile(0.75):.1f}")
    print(f"  P90:    {valid['bbwp_value'].quantile(0.90):.1f}")

    # Spectrum Distribution
    print(f"\n--- Spectrum Distribution ---")
    spec_dist = valid['bbwp_spectrum'].value_counts()
    for color in ['blue', 'green', 'yellow', 'red']:
        count = spec_dist.get(color, 0)
        pct = count / len(valid) * 100
        print(f"  {color:8s} {count:6,} ({pct:5.1f}%)")

    # State Distribution
    print(f"\n--- State Distribution ---")
    state_dist = valid['bbwp_state'].value_counts()
    for state in ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL',
                  'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE']:
        count = state_dist.get(state, 0)
        pct = count / len(valid) * 100
        print(f"  {state:20s} {count:6,} ({pct:5.1f}%)")

    # Points Distribution
    print(f"\n--- Points Distribution ---")
    pts_dist = valid['bbwp_points'].value_counts().sort_index()
    for pts, count in pts_dist.items():
        pct = count / len(valid) * 100
        print(f"  {int(pts)} pts: {count:6,} ({pct:5.1f}%)")
    print(f"  Mean: {valid['bbwp_points'].mean():.3f}")

    # MA Cross Events
    print(f"\n--- MA Cross Events ---")
    cross_up = valid['bbwp_ma_cross_up'].sum()
    cross_down = valid['bbwp_ma_cross_down'].sum()
    print(f"  Cross Up events:   {int(cross_up):,}")
    print(f"  Cross Down events: {int(cross_down):,}")
    print(f"  Cross Up %:   {cross_up/len(valid)*100:.2f}%")
    print(f"  Cross Down %: {cross_down/len(valid)*100:.2f}%")

    # Bar Flags
    print(f"\n--- Extreme Bars ---")
    blue_bars = valid['bbwp_is_blue_bar'].sum()
    red_bars = valid['bbwp_is_red_bar'].sum()
    print(f"  Blue bars (bbwp<=10): {int(blue_bars):,} ({blue_bars/len(valid)*100:.1f}%)")
    print(f"  Red bars (bbwp>=90):  {int(red_bars):,} ({red_bars/len(valid)*100:.1f}%)")

    # NaN check
    print(f"\n--- NaN Check ---")
    for col in ['bbwp_state', 'bbwp_points', 'bbwp_is_blue_bar', 'bbwp_is_red_bar']:
        nan_ct = result[col].isna().sum()
        status = "OK" if nan_ct == 0 else f"WARN: {nan_ct} NaN"
        print(f"  {col:25s} {status}")

    print(f"\n{'='*70}")
    print(f"SANITY CHECK COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
