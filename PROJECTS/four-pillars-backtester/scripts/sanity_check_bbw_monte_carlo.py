"""Layer 4b Sanity Check: RIVERUSDT full L1->L4->L4b pipeline.

Runs full pipeline on real RIVERUSDT 5m data with reduced MC (100 sims).
Prints per-state verdicts, commission impact, overfit flags.
Saves state_verdicts + overfit_flags to results/bbw_monte_carlo_sanity.csv.
Run: python scripts/sanity_check_bbw_monte_carlo.py
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


def main():
    """Run L1->L4->L4b sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 70)
    print(f"Monte Carlo Layer 4b Sanity Check -- {ts}")
    print("=" * 70)

    parquet = ROOT / "data" / "cache" / "RIVERUSDT_5m.parquet"
    if not parquet.exists():
        print(f"  SKIP  {parquet} not found")
        return

    t0 = time.time()
    df_raw = pd.read_parquet(parquet)
    print(f"  Input: {len(df_raw)} bars (5m)")

    # --- L1: BBWP ---
    t1 = time.time()
    df1 = calculate_bbwp(df_raw)
    t2 = time.time()
    print(f"  L1 (BBWP):     {t2-t1:.2f}s")

    # --- L2: Sequence ---
    df2 = track_bbw_sequence(df1)
    t3 = time.time()
    print(f"  L2 (Sequence):  {t3-t2:.2f}s")

    # --- L3: Forward returns ---
    df3 = tag_forward_returns(df2, windows=[10])
    t4 = time.time()
    print(f"  L3 (Forward):   {t4-t3:.2f}s")

    # --- L4: Simulator ---
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

    lsg_top = sim_result.lsg_top
    print(f"  L4 top combos:  {len(lsg_top)} rows")

    if lsg_top.empty:
        print("\n  No L4 combos passed filter -- cannot run MC")
        return

    # --- L4b: Monte Carlo ---
    mc_config = MonteCarloConfig(
        n_sims=100,
        min_trades=20,
        seed=42,
        commission_rate=0.0008,
        base_size=250.0,
        min_net_expectancy=1.00,
        max_mcl_threshold=15,
    )

    df3['symbol'] = 'RIVERUSDT'
    mc_result = run_monte_carlo(df3, lsg_top, sim_config, mc_config)
    t6 = time.time()
    print(f"  L4b (MC):       {mc_result.summary['runtime_sec']:.2f}s")
    print(f"  Total:          {t6-t0:.2f}s")

    # --- Summary ---
    print()
    print("--- MC Summary ---")
    for k, v in mc_result.summary.items():
        print(f"  {k}: {v}")

    # --- Per-state verdicts ---
    print()
    print("--- Per-State Verdicts ---")
    if not mc_result.state_verdicts.empty:
        for _, row in mc_result.state_verdicts.iterrows():
            state = row.get('bbwp_state', '?')
            window = row.get('window', '?')
            direction = row.get('direction', '?')
            verdict = row.get('verdict', '?')
            n_tr = row.get('n_trades', 0)
            gross = row.get('gross_expectancy', 0)
            net = row.get('net_expectancy', 0)
            rt = row.get('rt_commission', 0)
            conv = row.get('convergence_sims', '?')
            print(f"  {state:15s} w={window} d={direction:5s} "
                  + f"n={n_tr:4d} "
                  + f"gross=${gross:8.2f} net=${net:8.2f} "
                  + f"RT=${rt:.2f} "
                  + f"conv={conv} "
                  + f"-> {verdict}")
    else:
        print("  (empty)")

    # --- Commission impact ---
    print()
    print("--- Commission Impact ---")
    if not mc_result.state_verdicts.empty:
        sv = mc_result.state_verdicts
        n_ck = int((sv['verdict'] == 'COMMISSION_KILL').sum())
        n_te = int((sv['verdict'] == 'THIN_EDGE').sum())
        n_total = len(sv)
        print(f"  States total:          {n_total}")
        print(f"  COMMISSION_KILL:       {n_ck}")
        print(f"  THIN_EDGE:             {n_te}")
        print(f"  Survived commission:   {n_total - n_ck - n_te}")

        if 'gross_expectancy' in sv.columns and 'net_expectancy' in sv.columns:
            avg_gross = sv['gross_expectancy'].mean()
            avg_net = sv['net_expectancy'].mean()
            avg_drag = avg_gross - avg_net
            print(f"  Avg gross exp:         ${avg_gross:.2f}")
            print(f"  Avg net exp:           ${avg_net:.2f}")
            print(f"  Avg commission drag:   ${avg_drag:.2f}")

    # --- Overfit flags ---
    print()
    print("--- Overfit Flags ---")
    if not mc_result.overfit_flags.empty:
        of = mc_result.overfit_flags
        for _, row in of.iterrows():
            state = row.get('bbwp_state', '?')
            verdict = row.get('verdict', '?')
            reason = row.get('reason', '?')
            pnl_flag = row.get('pnl_overfit_flag', False)
            dd_flag = row.get('dd_fragile_flag', False)
            ck_flag = row.get('commission_kill_flag', False)
            flags = []
            if pnl_flag:
                flags.append("PNL_OVERFIT")
            if dd_flag:
                flags.append("DD_FRAGILE")
            if ck_flag:
                flags.append("COMM_KILL")
            flag_str = ", ".join(flags) if flags else "none"
            print(f"  {state:15s} {verdict:20s} flags=[{flag_str}]")
            print(f"    reason: {reason}")
    else:
        print("  (empty)")

    # --- Confidence Intervals sample ---
    print()
    print("--- CI Sample (first 3 states) ---")
    if not mc_result.confidence_intervals.empty:
        ci = mc_result.confidence_intervals
        states_seen = []
        for _, row in ci.iterrows():
            key = f"{row['bbwp_state']}_{row['window']}_{row['direction']}"
            if key not in states_seen:
                states_seen.append(key)
            if len(states_seen) > 3:
                break
            print(f"  {row['bbwp_state']:15s} {row['metric']:22s} "
                  + f"real={row['real']:10.2f} "
                  + f"CI=[{row['ci_lower']:10.2f}, {row['ci_upper']:10.2f}]")

    # --- Save CSV ---
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)

    out_verdicts = out_dir / "bbw_monte_carlo_sanity_verdicts.csv"
    out_flags = out_dir / "bbw_monte_carlo_sanity_flags.csv"

    if not mc_result.state_verdicts.empty:
        mc_result.state_verdicts.to_csv(out_verdicts, index=False)
        print(f"\n  Saved verdicts: {out_verdicts}")

    if not mc_result.overfit_flags.empty:
        mc_result.overfit_flags.to_csv(out_flags, index=False)
        print(f"  Saved flags:    {out_flags}")

    print()
    print("=" * 70)
    print("SANITY CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
