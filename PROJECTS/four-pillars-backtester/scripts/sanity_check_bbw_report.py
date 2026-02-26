"""Layer 5 Sanity Check: RIVERUSDT full L1->L5 pipeline.

Runs complete pipeline on real data, writes reports, validates output.
Run: python scripts/sanity_check_bbw_report.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signals.bbwp import calculate_bbwp
from signals.bbw_sequence import track_bbw_sequence
from research.bbw_forward_returns import tag_forward_returns
from research.bbw_simulator import SimulatorConfig, run_simulator
from research.bbw_monte_carlo import MonteCarloConfig, run_monte_carlo
from research.bbw_report import run_report


def main():
    """Run L1->L5 sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"BBW Report Layer 5 Sanity Check -- {ts}")
    print("=" * 70)

    parquet = ROOT / "data" / "cache" / "RIVERUSDT_5m.parquet"
    if not parquet.exists():
        print(f"  SKIP  {parquet} not found")
        return

    t0 = time.time()
    df_raw = pd.read_parquet(parquet)
    print(f"  Input: {len(df_raw)} bars (5m)")

    # L1-L3
    t1 = time.time()
    df1 = calculate_bbwp(df_raw)
    t2 = time.time()
    df2 = track_bbw_sequence(df1)
    t3 = time.time()
    df3 = tag_forward_returns(df2, windows=[10])
    t4 = time.time()
    print(f"  L1 (BBWP):     {t2-t1:.2f}s")
    print(f"  L2 (Sequence):  {t3-t2:.2f}s")
    print(f"  L3 (Forward):   {t4-t3:.2f}s")

    # L4
    sim_config = SimulatorConfig(
        leverage_grid=[10, 20],
        size_grid=[0.5, 1.0],
        target_atr_grid=[2, 4],
        sl_atr_grid=[1.5, 2.0],
        windows=[10],
        directions=['long'],
        min_sample_size=30,
    )
    sim_result = run_simulator(df3, sim_config)
    t5 = time.time()
    print(f"  L4 (Simulator): {sim_result.summary['runtime_sec']:.2f}s")

    # L4b
    mc_config = MonteCarloConfig(
        n_sims=100, min_trades=20, seed=42,
        commission_rate=0.0008, base_size=250.0,
    )
    df3['symbol'] = 'RIVERUSDT'
    mc_result = run_monte_carlo(df3, sim_result.lsg_top, sim_config, mc_config)
    t6 = time.time()
    print(f"  L4b (MC):       {mc_result.summary['runtime_sec']:.2f}s")

    # L5
    output_dir = ROOT / "results" / "bbw_reports_sanity"
    report = run_report(
        sim_result, mc_result, str(output_dir), verbose=True,
    )
    t7 = time.time()
    print(f"  L5 (Report):    {report['summary']['runtime_sec']:.4f}s")
    print(f"  Total:          {t7-t0:.2f}s")

    # Validation
    print()
    print("--- File Inventory ---")
    total_bytes = 0
    for fpath_str in report['reports_written']:
        fpath = Path(fpath_str)
        sz = fpath.stat().st_size
        total_bytes += sz
        # Human-readable size
        if sz >= 1_000_000:
            sz_str = f"{sz / 1_000_000:.2f} MB"
        elif sz >= 1_000:
            sz_str = f"{sz / 1_000:.1f} KB"
        else:
            sz_str = f"{sz} B"

        # Read and count rows
        df = pd.read_csv(fpath)
        rel = fpath.relative_to(output_dir)
        print(f"  {str(rel):<50} {len(df):>6} rows  {sz_str:>10}")

    if total_bytes >= 1_000_000:
        total_str = f"{total_bytes / 1_000_000:.2f} MB"
    else:
        total_str = f"{total_bytes / 1_000:.1f} KB"
    print(f"\n  Total disk usage: {total_str}")
    print(f"  Files written:    {report['summary']['n_total']}")
    print(f"  Errors:           {report['summary']['n_errors']}")

    if report['errors']:
        print("\n--- Errors ---")
        for fname, msg in report['errors']:
            print(f"  {fname}: {msg}")

    # Column spot-checks
    print()
    print("--- Column Spot-Checks ---")

    agg_path = output_dir / "aggregate" / "bbw_state_stats.csv"
    if agg_path.exists():
        df = pd.read_csv(agg_path)
        expected = {'group_value', 'window', 'direction', 'n_bars',
                    'mean_mfe_atr', 'edge_score'}
        actual = set(df.columns)
        missing = expected - actual
        if missing:
            print(f"  WARN: bbw_state_stats.csv missing: {missing}")
        else:
            print(f"  OK: bbw_state_stats.csv has {len(df.columns)} cols "
                  + f"(expected subset present)")

    mc_path = output_dir / "monte_carlo" / "mc_summary_by_state.csv"
    if mc_path.exists():
        df = pd.read_csv(mc_path)
        expected = {'symbol', 'bbwp_state', 'verdict', 'net_expectancy'}
        actual = set(df.columns)
        missing = expected - actual
        if missing:
            print(f"  WARN: mc_summary_by_state.csv missing: {missing}")
        else:
            print(f"  OK: mc_summary_by_state.csv has {len(df.columns)} cols "
                  + f"(expected subset present)")

    of_path = output_dir / "monte_carlo" / "mc_overfit_flags.csv"
    if of_path.exists():
        df = pd.read_csv(of_path)
        expected = {'verdict', 'reason', 'commission_kill_flag'}
        actual = set(df.columns)
        missing = expected - actual
        if missing:
            print(f"  WARN: mc_overfit_flags.csv missing: {missing}")
        else:
            print(f"  OK: mc_overfit_flags.csv has {len(df.columns)} cols "
                  + f"(expected subset present)")

    print()
    print("=" * 70)
    print("SANITY CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
