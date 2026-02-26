"""Layer 4 Sanity Check: RIVERUSDT full pipeline with reduced grid.

Runs L1 -> L2 -> L3 -> L4 on real data, prints summary stats.
Saves lsg_top to results/bbw_simulator_sanity.csv.
Run: python scripts/sanity_check_bbw_simulator.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signals.bbwp import calculate_bbwp
from signals.bbw_sequence import track_bbw_sequence
from research.bbw_forward_returns import tag_forward_returns
from research.bbw_simulator import SimulatorConfig, run_simulator


def main():
    """Run sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Simulator Layer 4 Sanity Check -- {ts}")
    print("=" * 70)

    parquet = ROOT / "data" / "cache" / "RIVERUSDT_5m.parquet"
    if not parquet.exists():
        print(f"  SKIP  {parquet} not found")
        return

    t0 = time.time()
    df_raw = pd.read_parquet(parquet)
    print(f"  Input: {len(df_raw)} bars (5m)")

    t1 = time.time()
    df1 = calculate_bbwp(df_raw)
    t2 = time.time()
    df2 = track_bbw_sequence(df1)
    t3 = time.time()
    df3 = tag_forward_returns(df2, windows=[10])
    t4 = time.time()

    sanity_config = SimulatorConfig(
        leverage_grid=[10, 20],
        size_grid=[0.5, 1.0],
        target_atr_grid=[2, 4],
        sl_atr_grid=[1.5, 2.0],
        windows=[10],
        directions=['long'],
        min_sample_size=30,
    )

    result = run_simulator(df3, sanity_config)
    t5 = time.time()

    print()
    print("--- Runtime Breakdown ---")
    print(f"  L1 (BBWP):     {t2-t1:.2f}s")
    print(f"  L2 (Sequence):  {t3-t2:.2f}s")
    print(f"  L3 (Forward):   {t4-t3:.2f}s")
    print(f"  L4 (Simulator): {result.summary['runtime_sec']:.2f}s")
    print(f"  Total:          {t5-t0:.2f}s")

    print()
    print("--- Summary ---")
    for k, v in result.summary.items():
        print(f"  {k}: {v}")

    print()
    print("--- Group Stats Overview ---")
    for gname, gdf in result.group_stats.items():
        n_cats = len(gdf)
        if not gdf.empty and 'edge_score' in gdf.columns:
            best = gdf.loc[gdf['edge_score'].idxmax()] if gdf['edge_score'].notna().any() else None
            if best is not None:
                print(f"  {gname}: {n_cats} categories, "
                      f"best={best['group_value']} "
                      f"(edge={best['edge_score']:.3f})")
            else:
                print(f"  {gname}: {n_cats} categories, no valid edge")
        else:
            print(f"  {gname}: {n_cats} categories")

    print()
    print("--- LSG Top Combos ---")
    if not result.lsg_top.empty:
        for _, row in result.lsg_top.head(10).iterrows():
            print(f"  {row['bbwp_state']:15s} lev={row['leverage']:2.0f} "
                  f"sz={row['size_frac']:.2f} tgt={row['target_atr']:.0f} "
                  f"sl={row['sl_atr']:.1f} "
                  f"exp=${row['expectancy_usd']:8.2f} "
                  f"wr={row['win_rate']:.1%} "
                  f"pf={row['profit_factor']:.2f}")
    else:
        print("  No combos passed min_sample_size filter")

    print()
    print("--- Scaling Verdicts ---")
    if not result.scaling_results.empty:
        for _, row in result.scaling_results.iterrows():
            print(f"  {row['entry_state']:15s} -> {row['add_trigger_state']:12s} "
                  f"wait={row['max_bars_to_wait']:2.0f} "
                  f"trig={row['triggered_pct']:.1%} "
                  f"verdict={row['verdict']}")
    else:
        print("  No scaling results")

    # Save lsg_top CSV
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "bbw_simulator_sanity.csv"
    if not result.lsg_top.empty:
        result.lsg_top.to_csv(out_file, index=False)
        print(f"\n  Saved: {out_file}")
    else:
        print("\n  No CSV to save (empty lsg_top)")

    print()
    print("=" * 70)
    print("SANITY CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
