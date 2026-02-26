"""
Sanity check: Run forward return tagger on RIVERUSDT 5m, print distribution stats.

Run: python scripts/sanity_check_forward_returns.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from research.bbw_forward_returns import tag_forward_returns, ATR_COL, DEFAULT_WINDOWS


def main():
    """Run forward returns sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"Forward Returns Layer 3 Sanity Check -- {ts}")
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

    t0 = time.time()
    result = tag_forward_returns(df)
    elapsed = time.time() - t0
    print(f"  Runtime: {elapsed:.2f}s ({len(df)/elapsed:,.0f} bars/sec)")

    # ATR distribution
    atr_valid = result[ATR_COL].dropna()
    close_valid = result.loc[atr_valid.index, 'close']
    atr_pct = (atr_valid / close_valid * 100)
    print(f"\n--- ATR Distribution ---")
    print(f"  Mean:  {atr_valid.mean():.4f} ({atr_pct.mean():.2f}% of close)")
    print(f"  P50:   {atr_valid.quantile(0.5):.4f} ({atr_pct.quantile(0.5):.2f}%)")
    print(f"  P90:   {atr_valid.quantile(0.9):.4f} ({atr_pct.quantile(0.9):.2f}%)")

    for w in DEFAULT_WINDOWS:
        prefix = f"fwd_{w}_"
        valid = result.dropna(subset=[f'{prefix}max_up_pct'])
        nan_count = result[f'{prefix}max_up_pct'].isna().sum()

        print(f"\n--- Window {w} ({len(valid):,} valid bars, {nan_count:,} NaN) ---")

        print(f"  max_up_pct:   mean={valid[f'{prefix}max_up_pct'].mean():.2f}  "
              f"P50={valid[f'{prefix}max_up_pct'].quantile(0.5):.2f}  "
              f"P90={valid[f'{prefix}max_up_pct'].quantile(0.9):.2f}")

        print(f"  max_down_pct: mean={valid[f'{prefix}max_down_pct'].mean():.2f}  "
              f"P50={valid[f'{prefix}max_down_pct'].quantile(0.5):.2f}  "
              f"P10={valid[f'{prefix}max_down_pct'].quantile(0.1):.2f}")

        atr_valid_w = valid.dropna(subset=[f'{prefix}max_up_atr'])
        if len(atr_valid_w) > 0:
            print(f"  max_up_atr:   mean={atr_valid_w[f'{prefix}max_up_atr'].mean():.3f}  "
                  f"P50={atr_valid_w[f'{prefix}max_up_atr'].quantile(0.5):.3f}  "
                  f"P90={atr_valid_w[f'{prefix}max_up_atr'].quantile(0.9):.3f}")

            print(f"  max_down_atr: mean={atr_valid_w[f'{prefix}max_down_atr'].mean():.3f}  "
                  f"P50={atr_valid_w[f'{prefix}max_down_atr'].quantile(0.5):.3f}  "
                  f"P90={atr_valid_w[f'{prefix}max_down_atr'].quantile(0.9):.3f}")

            print(f"  range_atr:    mean={atr_valid_w[f'{prefix}max_range_atr'].mean():.3f}  "
                  f"P50={atr_valid_w[f'{prefix}max_range_atr'].quantile(0.5):.3f}  "
                  f"P90={atr_valid_w[f'{prefix}max_range_atr'].quantile(0.9):.3f}")

        print(f"  close_pct:    mean={valid[f'{prefix}close_pct'].mean():.3f}  "
              f"std={valid[f'{prefix}close_pct'].std():.3f}")

        dir_dist = valid[f'{prefix}direction'].value_counts(normalize=True)
        up_p = dir_dist.get('up', 0)
        down_p = dir_dist.get('down', 0)
        flat_p = dir_dist.get('flat', 0)
        print(f"  direction:    up={up_p:.1%}  down={down_p:.1%}  flat={flat_p:.1%}")

        pm_rate = valid[f'{prefix}proper_move'].mean()
        print(f"  proper_move:  {pm_rate:.1%}")

    print(f"\n--- NaN Counts ---")
    fwd_cols = [c for c in result.columns if c.startswith('fwd_')]
    for col in fwd_cols:
        nan_ct = result[col].isna().sum()
        print(f"  {col:30s} {nan_ct:6,}")

    print(f"\n{'='*70}")
    print(f"SANITY CHECK COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
