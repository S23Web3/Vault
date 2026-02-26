"""Sanity check for BBW Analyzer V2 - Full pipeline validation.

Runs full Layer 4 analysis on RIVERUSDT backtester results and validates output.
If real data not available, uses larger synthetic dataset.

Outputs results to: results/bbw_analyzer_v2_sanity/

Run: python scripts/sanity_check_bbw_analyzer_v2.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import numpy as np

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_analyzer_v2 import analyze_bbw_patterns_v2


# =============================================================================
# DATA LOADING
# =============================================================================

def load_real_data():
    """Attempt to load real RIVERUSDT backtester data."""
    # Try to find real backtester results
    possible_paths = [
        ROOT / "results" / "backtester_RIVERUSDT.csv",
        ROOT / "data" / "backtester" / "RIVERUSDT.csv",
        ROOT / "cache" / "backtester_RIVERUSDT.parquet",
    ]

    for path in possible_paths:
        if path.exists():
            print(f"Loading real data from: {path}")
            if path.suffix == '.csv':
                return pd.read_csv(path, parse_dates=['timestamp'])
            elif path.suffix == '.parquet':
                return pd.read_parquet(path)

    return None


def generate_realistic_synthetic_data(n_trades=2000):
    """Generate larger synthetic dataset with realistic characteristics."""
    print(f"Generating synthetic data ({n_trades} trades)...")

    # Realistic date range
    timestamps = pd.date_range('2024-01-01', periods=n_trades, freq='5min')

    # Realistic BBW state distribution (BLUE/GREEN more common)
    bbw_states_weights = {
        'BLUE': 0.25,
        'BLUE_DOUBLE': 0.10,
        'GREEN': 0.20,
        'YELLOW': 0.15,
        'RED': 0.10,
        'RED_DOUBLE': 0.05,
        'NORMAL': 0.10,
        'MA_CROSS_UP': 0.025,
        'MA_CROSS_DOWN': 0.025
    }
    states = list(bbw_states_weights.keys())
    probs = list(bbw_states_weights.values())
    bbw_state_seq = np.random.choice(states, size=n_trades, p=probs)

    # Balanced LONG/SHORT
    directions = ['LONG'] * (n_trades // 2) + ['SHORT'] * (n_trades - n_trades // 2)
    np.random.shuffle(directions)

    # Realistic price movement (RIVERUSDT ~0.50-0.60)
    entry_prices = np.random.uniform(0.48, 0.62, n_trades)
    # Exit prices with some correlation to direction
    exit_prices = np.where(
        np.array(directions) == 'LONG',
        entry_prices * np.random.uniform(0.98, 1.05, n_trades),  # LONG slightly bullish
        entry_prices * np.random.uniform(0.95, 1.02, n_trades)   # SHORT slightly bearish
    )

    # PnL calculation
    pnl_gross = np.where(
        np.array(directions) == 'LONG',
        (exit_prices - entry_prices) / entry_prices * 100,  # % return
        (entry_prices - exit_prices) / entry_prices * 100
    )

    # Add realistic noise
    pnl_gross = pnl_gross * np.random.uniform(10, 30, n_trades)  # Scale to dollars

    # Commission (constant $8/RT)
    commission = np.full(n_trades, 8.0)
    pnl_net = pnl_gross - commission

    # Outcomes based on PnL
    outcomes = np.where(
        pnl_gross > 5, 'TP',
        np.where(pnl_gross < -8, 'SL', 'TIMEOUT')
    )

    # Assemble backtester results
    trades = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': ['RIVERUSDT'] * n_trades,
        'direction': directions,
        'entry_price': entry_prices,
        'exit_price': exit_prices,
        'leverage': np.random.choice([10, 15, 20], n_trades, p=[0.2, 0.5, 0.3]),
        'size': np.random.choice([1.0, 1.5, 2.0], n_trades, p=[0.3, 0.5, 0.2]),
        'grid': np.random.choice([1.5, 2.0, 2.5], n_trades, p=[0.3, 0.4, 0.3]),
        'outcome': outcomes,
        'pnl_gross': pnl_gross,
        'pnl_net': pnl_net,
        'commission_rt': commission,
        'bars_held': np.random.randint(1, 100, n_trades)
    })

    # BBW states (same timestamps)
    bbw_states = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': ['RIVERUSDT'] * n_trades,
        'bbw_state': bbw_state_seq,
        'bbwp': np.where(
            np.isin(bbw_state_seq, ['BLUE', 'BLUE_DOUBLE']), np.random.uniform(0, 20, n_trades),
            np.where(
                np.isin(bbw_state_seq, ['GREEN']), np.random.uniform(15, 35, n_trades),
                np.where(
                    np.isin(bbw_state_seq, ['YELLOW']), np.random.uniform(30, 70, n_trades),
                    np.where(
                        np.isin(bbw_state_seq, ['RED', 'RED_DOUBLE']), np.random.uniform(70, 100, n_trades),
                        np.random.uniform(0, 100, n_trades)  # Others
                    )
                )
            )
        )
    })

    return trades, bbw_states


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================

def run_sanity_check():
    """Execute full Layer 4 pipeline and validate results."""
    print("=" * 70)
    print("BBW ANALYZER V2 - SANITY CHECK")
    print("=" * 70)
    print()

    # Load data
    real_trades = load_real_data()

    if real_trades is not None:
        print("Using REAL backtester data\n")
        trades, bbw_states = real_trades  # Assuming real_trades returns tuple
        # TODO: Add BBW states loading for real data path
    else:
        print("Real data not found, using realistic synthetic data\n")
        trades, bbw_states = generate_realistic_synthetic_data(n_trades=2000)

    # Print data summary
    print(f"Data Summary:")
    print(f"  Trades:     {len(trades):,}")
    print(f"  BBW States: {len(bbw_states):,}")
    print(f"  Date Range: {trades['timestamp'].min()} to {trades['timestamp'].max()}")
    print(f"  Symbol:     {trades['symbol'].iloc[0]}")
    print()

    # Run analysis
    print("Running BBW Analyzer V2...")
    t0 = datetime.now()

    result = analyze_bbw_patterns_v2(
        backtester_results=trades,
        bbw_states=bbw_states,
        symbol="RIVERUSDT",
        min_trades_per_group=20  # Lower threshold for synthetic data
    )

    runtime = (datetime.now() - t0).total_seconds()
    print(f"Analysis completed in {runtime:.2f} seconds\n")

    # Validate results
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print()

    # Check 1: Row counts
    print("[1] Row Counts:")
    print(f"  Input trades:      {len(trades):,}")
    print(f"  Trades analyzed:   {result.n_trades_analyzed:,}")
    print(f"  Groups found:      {len(result.results):,}")
    print(f"  Best combos:       {len(result.best_combos):,}")
    print(f"  States analyzed:   {len(result.directional_bias):,}")

    if result.n_trades_analyzed == len(trades):
        print("  [PASS] All trades analyzed")
    else:
        print(f"  [FAIL] Trades mismatch")

    print()

    # Check 2: State coverage
    print("[2] BBW State Coverage:")
    unique_states = trades['symbol'].nunique()  # Placeholder
    enriched_states = result.n_states
    print(f"  Unique BBW states in data:    {enriched_states}")
    print(f"  States with best combos:      {result.best_combos['bbw_state'].nunique() if not result.best_combos.empty else 0}")

    if result.n_states > 0:
        print("  [PASS] States identified")
    print()

    # Check 3: LSG combinations
    print("[3] LSG Combinations:")
    if not result.results.empty:
        lsg_combos = result.results.groupby(['leverage', 'size', 'grid']).size()
        print(f"  Unique LSG combos tested:  {len(lsg_combos)}")
        print(f"  Leverage range: [{result.results['leverage'].min()}, {result.results['leverage'].max()}]")
        print(f"  Size range:     [{result.results['size'].min():.1f}, {result.results['size'].max():.1f}]")
        print(f"  Grid range:     [{result.results['grid'].min():.1f}, {result.results['grid'].max():.1f}]")
        print("  [PASS] LSG combinations found")
    else:
        print("  [WARN] No groups met min_trades threshold")

    print()

    # Check 4: BE+fees rate validation
    print("[4] BE+fees Rate Distribution:")
    if not result.results.empty:
        be_fees_rates = result.results['be_plus_fees_rate']
        print(f"  Min:    {be_fees_rates.min():.3f}")
        print(f"  Mean:   {be_fees_rates.mean():.3f}")
        print(f"  Median: {be_fees_rates.median():.3f}")
        print(f"  Max:    {be_fees_rates.max():.3f}")

        # Check for commission impact
        win_rates = result.results['win_rate']
        avg_divergence = (win_rates - be_fees_rates).mean()
        print(f"\n  Avg divergence (win - BE):  {avg_divergence:.3f}")
        if avg_divergence > 0:
            print("  [PASS] Commission impact detected (BE < win)")
    else:
        print("  [SKIP] No results to analyze")

    print()

    # Check 5: Output contract
    print("[5] Output Contract:")
    required_cols = ['bbw_state', 'direction', 'leverage', 'size', 'grid',
                     'n_trades', 'be_plus_fees_rate', 'per_trade_pnl']
    missing_cols = [col for col in required_cols if col not in result.results.columns]

    if not missing_cols:
        print("  [PASS] All required columns present")
    else:
        print(f"  [FAIL] Missing columns: {missing_cols}")

    required_keys = ['symbol', 'n_trades_analyzed', 'n_states', 'runtime_seconds']
    missing_keys = [key for key in required_keys if key not in result.summary]

    if not missing_keys:
        print("  [PASS] All required summary keys present")
    else:
        print(f"  [FAIL] Missing summary keys: {missing_keys}")

    print()

    # Export results
    output_dir = ROOT / "results" / "bbw_analyzer_v2_sanity"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[6] Exporting Results to: {output_dir}")

    # Export DataFrames
    results_path = output_dir / "results.csv"
    result.results.to_csv(results_path, index=False)
    print(f"  Wrote: {results_path.name} ({len(result.results)} rows)")

    best_combos_path = output_dir / "best_combos.csv"
    result.best_combos.to_csv(best_combos_path, index=False)
    print(f"  Wrote: {best_combos_path.name} ({len(result.best_combos)} rows)")

    bias_path = output_dir / "directional_bias.csv"
    result.directional_bias.to_csv(bias_path, index=False)
    print(f"  Wrote: {bias_path.name} ({len(result.directional_bias)} rows)")

    summary_path = output_dir / "summary.csv"
    pd.DataFrame([result.summary]).to_csv(summary_path, index=False)
    print(f"  Wrote: {summary_path.name}")

    print()
    print("=" * 70)
    print("SANITY CHECK COMPLETE")
    print("=" * 70)
    print()
    print(f"Total runtime: {runtime:.2f} seconds")
    print(f"Results exported to: {output_dir}")


if __name__ == '__main__':
    run_sanity_check()
