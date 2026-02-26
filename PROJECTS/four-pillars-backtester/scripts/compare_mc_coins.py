"""Multi-coin Monte Carlo comparison script.

Runs Layer 4b MC on multiple coins with same config, compares results.
Run: python scripts/compare_mc_coins.py
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
from research.bbw_monte_carlo import MonteCarloConfig, run_monte_carlo


COINS = ['RIVERUSDT', 'AXSUSDT', 'KITEUSDT']


def process_coin(symbol):
    """Run full L1->L4->L4b pipeline for one coin."""
    parquet = ROOT / "data" / "cache" / f"{symbol}_5m.parquet"
    if not parquet.exists():
        return None, f"SKIP: {symbol} not found"

    t0 = time.time()
    df_raw = pd.read_parquet(parquet)

    # L1-L3
    df1 = calculate_bbwp(df_raw)
    df2 = track_bbw_sequence(df1)
    df3 = tag_forward_returns(df2, windows=[10])

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

    if sim_result.lsg_top.empty:
        return None, f"SKIP: {symbol} no L4 combos passed filter"

    # L4b
    mc_config = MonteCarloConfig(
        n_sims=100,
        min_trades=20,
        seed=42,
        commission_rate=0.0008,
        base_size=250.0,
        min_net_expectancy=1.00,
        max_mcl_threshold=15,
    )

    df3['symbol'] = symbol
    mc_result = run_monte_carlo(df3, sim_result.lsg_top, sim_config, mc_config)
    runtime = time.time() - t0

    return {
        'symbol': symbol,
        'n_bars': len(df_raw),
        'n_states': len(mc_result.state_verdicts),
        'runtime_sec': runtime,
        'mc_result': mc_result,
    }, None


def main():
    """Compare MC results across multiple coins."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 80)
    print(f"Multi-Coin Monte Carlo Comparison -- {ts}")
    print("=" * 80)
    print()

    results = []
    for symbol in COINS:
        print(f"[{symbol}] Processing...")
        result, error = process_coin(symbol)
        if error:
            print(f"  {error}")
        else:
            results.append(result)
            print(f"  DONE: {result['n_bars']} bars, {result['n_states']} states, "
                  + f"{result['runtime_sec']:.2f}s")
        print()

    if not results:
        print("No coins processed successfully")
        return

    # --- Summary Table ---
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print()

    header = f"{'Coin':<12} {'Bars':<8} {'States':<8} {'ROBUST':<8} {'FRAGILE':<8} " \
             + f"{'COMM_KILL':<10} {'Avg Gross':<12} {'Avg Net':<12} {'Drag':<10}"
    print(header)
    print("-" * 80)

    for r in results:
        sv = r['mc_result'].state_verdicts
        n_robust = int((sv['verdict'] == 'ROBUST').sum())
        n_fragile = int((sv['verdict'] == 'FRAGILE').sum())
        n_ck = int((sv['verdict'] == 'COMMISSION_KILL').sum())
        avg_gross = sv['gross_expectancy'].mean()
        avg_net = sv['net_expectancy'].mean()
        drag = avg_gross - avg_net

        print(f"{r['symbol']:<12} {r['n_bars']:<8} {r['n_states']:<8} "
              + f"{n_robust:<8} {n_fragile:<8} {n_ck:<10} "
              + f"${avg_gross:<11.2f} ${avg_net:<11.2f} ${drag:<9.2f}")

    # --- Per-Coin Details ---
    print()
    print("=" * 80)
    print("PER-COIN DETAILS")
    print("=" * 80)

    for r in results:
        print()
        print(f"--- {r['symbol']} ---")
        sv = r['mc_result'].state_verdicts
        print(f"  Total states: {len(sv)}")

        if not sv.empty:
            print()
            print(f"  {'State':<15} {'N':<6} {'Gross':<10} {'Net':<10} "
                  + f"{'RT':<6} {'Verdict':<20}")
            print("  " + "-" * 70)
            for _, row in sv.iterrows():
                state = row.get('bbwp_state', '?')[:15]
                n = row.get('n_trades', 0)
                gross = row.get('gross_expectancy', 0)
                net = row.get('net_expectancy', 0)
                rt = row.get('rt_commission', 0)
                verdict = row.get('verdict', '?')
                print(f"  {state:<15} {n:<6} ${gross:<9.2f} ${net:<9.2f} "
                      + f"${rt:<5.2f} {verdict:<20}")

    # --- Save CSVs ---
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)

    all_verdicts = []
    all_flags = []
    for r in results:
        all_verdicts.append(r['mc_result'].state_verdicts)
        all_flags.append(r['mc_result'].overfit_flags)

    combined_verdicts = pd.concat(all_verdicts, ignore_index=True)
    combined_flags = pd.concat(all_flags, ignore_index=True)

    out_verdicts = out_dir / "mc_comparison_verdicts.csv"
    out_flags = out_dir / "mc_comparison_flags.csv"

    combined_verdicts.to_csv(out_verdicts, index=False)
    combined_flags.to_csv(out_flags, index=False)

    print()
    print("=" * 80)
    print(f"Saved: {out_verdicts}")
    print(f"Saved: {out_flags}")
    print("=" * 80)


if __name__ == "__main__":
    main()
