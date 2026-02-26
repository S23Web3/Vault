"""BBW V2 Integration Debug Script.

Runs single scenario with detailed output for debugging L4->L4b->L5 pipeline.

Run: python scripts/debug_bbw_integration.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd

from research.bbw_analyzer_v2 import analyze_bbw_patterns_v2
from research.bbw_monte_carlo_v2 import run_monte_carlo_v2
from research.bbw_report_v2 import generate_vince_features_v2


def generate_debug_backtester_results(n_trades=1000, seed=42):
    """Generate mock backtester results for Layer 4 testing.

    Returns:
        Tuple of (backtester_results, bbw_states) DataFrames
    """
    np.random.seed(seed)

    # Generate BBW states timeline (8000 bars, enough for 5000 trades with spread)
    n_bars = 8000
    start_time = datetime(2024, 1, 1)
    # Valid states from Layer 4 validator (no GRAY, no GREEN_DOUBLE)
    states = ['BLUE', 'GREEN', 'RED']

    bbw_rows = []
    current_state = 'BLUE'

    for i in range(n_bars):
        # 80% chance to stay, 20% to switch
        if np.random.random() > 0.2 and i > 0:
            pass
        else:
            current_state = np.random.choice(states)

        # BBWP consistent with state
        if current_state == 'BLUE':
            bbwp = np.random.uniform(0, 30)
        elif current_state == 'GREEN':
            bbwp = np.random.uniform(30, 60)
        else:  # RED
            bbwp = np.random.uniform(60, 100)

        bbw_rows.append({
            'timestamp': pd.Timestamp(start_time + timedelta(minutes=i)),
            'symbol': 'DEBUGUSDT',
            'bbw_state': current_state,
            'bbwp': bbwp
        })

    bbw_states = pd.DataFrame(bbw_rows)

    # LSG grid: simulate one backtester run per (leverage, size, grid) combo.
    # Each run uses a FIXED LSG for ALL its trades — this matches how the real
    # backtester works. n_trades is split evenly across all LSG combos.
    lsg_combos = [
        (10, 0.5, 2.0),
        (10, 1.0, 2.0),
        (20, 0.5, 2.0),
        (20, 1.0, 2.0),
    ]
    trades_per_combo = n_trades // len(lsg_combos)

    trade_rows = []

    for (leverage, size, grid) in lsg_combos:
        for i in range(trades_per_combo):
            # Random entry time from BBW timeline
            entry_idx = np.random.randint(0, n_bars - 100)
            entry_time = bbw_rows[entry_idx]['timestamp']
            entry_state = bbw_rows[entry_idx]['bbw_state']

            direction = np.random.choice(['LONG', 'SHORT'])
            entry_price = np.random.uniform(0.5, 2.0)
            bars_held = np.random.randint(5, 50)

            # PnL depends on state and leverage (higher leverage = larger swings)
            scale = leverage / 10.0
            if entry_state == 'BLUE':
                pnl_pct = np.random.normal(0.02, 0.04) * scale if direction == 'LONG' \
                    else np.random.normal(-0.01, 0.04) * scale
            elif entry_state == 'GREEN':
                pnl_pct = np.random.normal(0.01, 0.035) * scale
            else:  # RED
                pnl_pct = np.random.normal(-0.01, 0.05) * scale

            exit_price = entry_price * (1 + pnl_pct) if direction == 'LONG' \
                else entry_price * (1 - pnl_pct)

            margin = 100
            notional = margin * leverage
            price_change_pct = (exit_price - entry_price) / entry_price
            if direction == 'SHORT':
                price_change_pct = -price_change_pct

            gross_pnl = notional * price_change_pct
            commission_rt = notional * 0.0008 * 2
            net_pnl = gross_pnl - commission_rt

            if net_pnl > 3:
                outcome = 'TP'
            elif net_pnl < -3:
                outcome = 'SL'
            else:
                outcome = 'TIMEOUT'

            trade_rows.append({
                'timestamp': pd.Timestamp(entry_time),
                'symbol': 'DEBUGUSDT',
                'direction': direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'leverage': leverage,
                'size': size,
                'grid': grid,
                'outcome': outcome,
                'pnl_gross': gross_pnl,
                'pnl_net': net_pnl,
                'commission_rt': commission_rt,
                'bars_held': bars_held
            })

    backtester_results = pd.DataFrame(trade_rows)

    return backtester_results, bbw_states


def print_separator(title):
    """Print section separator."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def main():
    """Run debug scenario."""
    print_separator("BBW V2 Integration Debug")

    # Generate data
    print("\n[1] Generating test data...")
    backtester_results, bbw_states = generate_debug_backtester_results(n_trades=5000, seed=42)
    print(f"    Generated {len(backtester_results)} trades")
    print(f"    BBW timeline: {len(bbw_states)} bars")
    print(f"    Date range: {bbw_states['timestamp'].min()} to {bbw_states['timestamp'].max()}")
    print(f"    States: {bbw_states['bbw_state'].value_counts().to_dict()}")
    print(f"    Directions: {backtester_results['direction'].value_counts().to_dict()}")

    # Layer 4: Analyzer
    print_separator("Layer 4: BBW Analyzer V2")
    print("\n[2] Running analyzer...")

    import time
    t0 = time.time()

    l4_result = analyze_bbw_patterns_v2(
        backtester_results=backtester_results,
        bbw_states=bbw_states,
        symbol='DEBUGUSDT',
        min_trades_per_group=50
    )

    l4_time = time.time() - t0

    print(f"    Runtime: {l4_time:.2f}s")
    print(f"\n    Results DataFrame: {len(l4_result.results)} rows")
    print(f"    Best combos: {len(l4_result.best_combos)} rows")
    print(f"    States analyzed: {l4_result.n_states}")
    print(f"    Trades analyzed: {l4_result.n_trades_analyzed}")

    print("\n    Best combos preview:")
    if not l4_result.best_combos.empty:
        for idx, row in l4_result.best_combos.head(3).iterrows():
            print(f"      {row['bbw_state']} {row['direction']}: "
                  f"BE+fees={row['be_plus_fees_rate']:.3f}, "
                  f"n={row['n_trades']}, "
                  f"sharpe={row['sharpe']:.2f}")

    # Check for per_trade_pnl
    print("\n    Checking per_trade_pnl...")
    if 'per_trade_pnl' in l4_result.best_combos.columns:
        first_pnl = l4_result.best_combos.iloc[0]['per_trade_pnl']
        print(f"      Type: {type(first_pnl)}")
        print(f"      Length: {len(first_pnl)}")
        print(f"      Sample: {first_pnl[:3]}")
    else:
        print("      ERROR: per_trade_pnl column missing!")

    # Layer 4b: Monte Carlo
    print_separator("Layer 4b: Monte Carlo Validation")
    print("\n[3] Running Monte Carlo...")

    t0 = time.time()

    l4b_result = run_monte_carlo_v2(
        l4_result,
        n_sims=100,
        confidence=0.90,
        min_trades=50,
        seed=42
    )

    l4b_time = time.time() - t0

    print(f"    Runtime: {l4b_time:.2f}s")
    print(f"\n    State verdicts: {len(l4b_result.state_verdicts)} rows")
    print(f"    Robust: {l4b_result.summary['n_robust']}")
    print(f"    Fragile: {l4b_result.summary['n_fragile']}")
    print(f"    Commission kill: {l4b_result.summary['n_commission_kill']}")
    print(f"    Insufficient: {l4b_result.summary['n_insufficient']}")

    print("\n    Verdict preview:")
    for idx, row in l4b_result.state_verdicts.head(5).iterrows():
        print(f"      {row['bbw_state']} {row['direction']}: "
              f"{row['verdict']} (CI=[{row['ci_lower']:.2f}, {row['ci_upper']:.2f}])")

    # Layer 5: Report
    print_separator("Layer 5: Report Generator")
    print("\n[4] Generating reports...")

    t0 = time.time()

    l5_result = generate_vince_features_v2(l4_result, l4b_result)

    l5_time = time.time() - t0

    print(f"    Runtime: {l5_time:.2f}s")
    print(f"\n    Directional bias: {len(l5_result.directional_bias)} rows")
    print(f"    BE+fees success: {len(l5_result.be_fees_success)} rows")
    print(f"    VINCE features: {len(l5_result.vince_features)} rows")
    print(f"    LSG sensitivity: {len(l5_result.lsg_sensitivity)} rows")
    print(f"    State summary: {len(l5_result.state_summary)} rows")

    print("\n    Directional bias preview:")
    for idx, row in l5_result.directional_bias.head(3).iterrows():
        print(f"      {row['bbw_state']}: {row['bias_direction']} "
              f"(strength={row['bias_strength']:.3f}, confidence={row['confidence']})")

    print("\n    State summary preview:")
    for idx, row in l5_result.state_summary.head(3).iterrows():
        print(f"      {row['bbw_state']}: {row['state_quality']} "
              f"(avg_rate={row['avg_be_fees_rate']:.3f}, "
              f"n_robust={row['n_robust']}, n_fragile={row['n_fragile']})")

    print("\n    VINCE features columns:")
    if not l5_result.vince_features.empty:
        feature_cols = [col for col in l5_result.vince_features.columns if col.startswith('feature_')]
        target_cols = [col for col in l5_result.vince_features.columns if col.startswith('target_')]
        print(f"      Features ({len(feature_cols)}): {', '.join(feature_cols[:5])}...")
        print(f"      Targets ({len(target_cols)}): {', '.join(target_cols)}")
        print(f"      Sample weights: {l5_result.vince_features['sample_weight'].unique()}")

    # Summary
    print_separator("Summary")
    print(f"\n  Total runtime: {l4_time + l4b_time + l5_time:.2f}s")
    print(f"    Layer 4:  {l4_time:.2f}s ({l4_time/(l4_time+l4b_time+l5_time)*100:.1f}%)")
    print(f"    Layer 4b: {l4b_time:.2f}s ({l4b_time/(l4_time+l4b_time+l5_time)*100:.1f}%)")
    print(f"    Layer 5:  {l5_time:.2f}s ({l5_time/(l4_time+l4b_time+l5_time)*100:.1f}%)")

    print(f"\n  Data flow:")
    print(f"    Input trades:     {len(backtester_results)}")
    print(f"    BBW timeline:     {len(bbw_states)}")
    print(f"    L4 results:       {len(l4_result.results)}")
    print(f"    L4 best combos:   {len(l4_result.best_combos)}")
    print(f"    L4b verdicts:     {len(l4b_result.state_verdicts)}")
    print(f"    L5 features:      {len(l5_result.vince_features)}")

    print("\n  SUCCESS - All layers completed without errors!")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
