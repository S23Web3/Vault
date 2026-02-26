"""BBW V2 Integration Test - Random Scenarios.

Tests Layer 4 (Analyzer) -> Layer 4b (Monte Carlo) -> Layer 5 (Report) pipeline
with randomly generated data to catch edge cases and bugs.

Run: python scripts/test_bbw_integration_random.py [--scenarios N]
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd

from research.bbw_analyzer_v2 import analyze_bbw_patterns_v2
from research.bbw_monte_carlo_v2 import run_monte_carlo_v2
from research.bbw_report_v2 import generate_vince_features_v2


# =============================================================================
# RANDOM DATA GENERATORS
# =============================================================================

def generate_random_backtester_results(n_trades=1000, n_bars=3000, n_states=5, seed=None):
    """Generate random backtester results for Layer 4 testing.

    Args:
        n_trades: Number of trades to generate
        n_bars: Number of bars in BBW timeline
        n_states: Number of unique BBW states
        seed: Random seed

    Returns:
        Tuple of (backtester_results, bbw_states) DataFrames
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate BBW states timeline
    start_time = datetime(2024, 1, 1)
    # Valid states from Layer 4 validator
    valid_states = ['BLUE', 'BLUE_DOUBLE', 'GREEN', 'YELLOW', 'NORMAL',
                    'RED', 'RED_DOUBLE', 'MA_CROSS_UP', 'MA_CROSS_DOWN'][:n_states]

    bbw_rows = []
    current_state = np.random.choice(valid_states)

    for i in range(n_bars):
        # 70% chance to stay, 30% to switch
        if np.random.random() > 0.3 and i > 0:
            pass
        else:
            current_state = np.random.choice(valid_states)

        # BBWP consistent with state
        if 'BLUE' in current_state:
            bbwp = np.random.uniform(0, 30)
        elif 'GREEN' in current_state or current_state == 'NORMAL':
            bbwp = np.random.uniform(20, 50)
        elif 'YELLOW' in current_state:
            bbwp = np.random.uniform(40, 70)
        elif 'RED' in current_state:
            bbwp = np.random.uniform(60, 100)
        else:  # MA_CROSS
            bbwp = np.random.uniform(0, 100)

        bbw_rows.append({
            'timestamp': pd.Timestamp(start_time + timedelta(minutes=i)),
            'symbol': 'TEST',
            'bbw_state': current_state,
            'bbwp': bbwp
        })

    bbw_states = pd.DataFrame(bbw_rows)

    # Generate mock backtest trades.
    # LSG (Leverage, Size, Grid) are backtester parameters fixed for an entire
    # simulation run — not random per trade. We generate one batch of trades
    # per LSG combo, then concatenate, matching how the real backtester works.
    leverage_choices = [5, 10, 15, 20]
    size_choices = [0.5, 1.0, 1.5, 2.0]
    grid_choices = [1.0, 1.5, 2.0, 2.5, 3.0]

    # Pick 4 random discrete LSG combos for this scenario
    n_combos = 4
    lsg_combos = [
        (
            np.random.choice(leverage_choices),
            np.random.choice(size_choices),
            np.random.choice(grid_choices),
        )
        for _ in range(n_combos)
    ]
    trades_per_combo = max(1, n_trades // n_combos)

    trade_rows = []

    for (leverage, size, grid) in lsg_combos:
        for i in range(trades_per_combo):
            # Random entry time from BBW timeline
            entry_idx = np.random.randint(0, max(1, n_bars - 100))
            entry_time = bbw_rows[entry_idx]['timestamp']
            entry_state = bbw_rows[entry_idx]['bbw_state']

            direction = np.random.choice(['LONG', 'SHORT'])
            entry_price = np.random.uniform(0.5, 2.0)
            bars_held = np.random.randint(5, 50)

            # PnL depends on BBW state (state-dependent edge)
            if 'BLUE' in entry_state:
                pnl_pct = np.random.normal(0.02, 0.05) if direction == 'LONG' \
                    else np.random.normal(-0.01, 0.05)
            elif 'GREEN' in entry_state:
                pnl_pct = np.random.normal(0.01, 0.04)
            elif 'YELLOW' in entry_state:
                pnl_pct = np.random.normal(0, 0.05)
            elif 'RED' in entry_state:
                pnl_pct = np.random.normal(-0.01, 0.06)
            else:  # NORMAL, MA_CROSS_*
                pnl_pct = np.random.normal(0, 0.07)

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
                'symbol': 'TEST',
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




# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_layer4_output(result, scenario_name):
    """Validate Layer 4 (Analyzer) output structure and values.

    Args:
        result: BBWAnalysisResultV2 from Layer 4
        scenario_name: Name of scenario for error reporting

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check attributes exist
    required_attrs = ['results', 'best_combos', 'directional_bias', 'summary', 'symbol']
    for attr in required_attrs:
        if not hasattr(result, attr):
            errors.append(f"[L4 {scenario_name}] Missing attribute: {attr}")

    if errors:
        return errors

    # Check DataFrames non-empty
    if result.results.empty:
        errors.append(f"[L4 {scenario_name}] results DataFrame is empty")

    if result.best_combos.empty:
        errors.append(f"[L4 {scenario_name}] best_combos DataFrame is empty")

    # Check critical columns
    if 'bbw_state' not in result.best_combos.columns:
        errors.append(f"[L4 {scenario_name}] best_combos missing 'bbw_state' column")

    if 'direction' not in result.best_combos.columns:
        errors.append(f"[L4 {scenario_name}] best_combos missing 'direction' column")

    if 'per_trade_pnl' not in result.best_combos.columns:
        errors.append(f"[L4 {scenario_name}] best_combos missing 'per_trade_pnl' column")

    # Check per_trade_pnl is list
    if not result.best_combos.empty:
        first_pnl = result.best_combos.iloc[0]['per_trade_pnl']
        if not isinstance(first_pnl, (list, np.ndarray)):
            errors.append(f"[L4 {scenario_name}] per_trade_pnl is not list/array: {type(first_pnl)}")

    # Check numeric ranges
    if not result.best_combos.empty:
        be_fees = result.best_combos['be_plus_fees_rate']
        if (be_fees < 0).any() or (be_fees > 1).any():
            errors.append(f"[L4 {scenario_name}] be_plus_fees_rate out of range [0,1]")

    return errors


def validate_layer4b_output(result, scenario_name):
    """Validate Layer 4b (Monte Carlo) output structure and values.

    Args:
        result: MonteCarloResultV2 from Layer 4b
        scenario_name: Name of scenario for error reporting

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check attributes exist
    required_attrs = ['state_verdicts', 'confidence_intervals', 'overfit_flags', 'summary']
    for attr in required_attrs:
        if not hasattr(result, attr):
            errors.append(f"[L4b {scenario_name}] Missing attribute: {attr}")

    if errors:
        return errors

    # Check state_verdicts non-empty
    if result.state_verdicts.empty:
        errors.append(f"[L4b {scenario_name}] state_verdicts DataFrame is empty")
        return errors

    # Check critical columns
    if 'bbw_state' not in result.state_verdicts.columns:
        errors.append(f"[L4b {scenario_name}] state_verdicts missing 'bbw_state' column")

    if 'verdict' not in result.state_verdicts.columns:
        errors.append(f"[L4b {scenario_name}] state_verdicts missing 'verdict' column")

    # Check verdicts are valid
    valid_verdicts = {'ROBUST', 'FRAGILE', 'COMMISSION_KILL', 'INSUFFICIENT'}
    actual_verdicts = set(result.state_verdicts['verdict'].unique())
    invalid = actual_verdicts - valid_verdicts
    if invalid:
        errors.append(f"[L4b {scenario_name}] Invalid verdicts: {invalid}")

    # Check confidence intervals exist
    if 'ci_lower' not in result.state_verdicts.columns:
        errors.append(f"[L4b {scenario_name}] state_verdicts missing 'ci_lower' column")

    if 'ci_upper' not in result.state_verdicts.columns:
        errors.append(f"[L4b {scenario_name}] state_verdicts missing 'ci_upper' column")

    # Check CI ordering
    if not result.state_verdicts.empty:
        invalid_ci = result.state_verdicts[
            result.state_verdicts['ci_lower'] > result.state_verdicts['ci_upper']
        ]
        if len(invalid_ci) > 0:
            errors.append(f"[L4b {scenario_name}] {len(invalid_ci)} rows with ci_lower > ci_upper")

    return errors


def validate_layer5_output(result, scenario_name):
    """Validate Layer 5 (Report) output structure and values.

    Args:
        result: BBWReportResultV2 from Layer 5
        scenario_name: Name of scenario for error reporting

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check attributes exist
    required_attrs = ['directional_bias', 'be_fees_success', 'vince_features',
                      'lsg_sensitivity', 'state_summary', 'summary']
    for attr in required_attrs:
        if not hasattr(result, attr):
            errors.append(f"[L5 {scenario_name}] Missing attribute: {attr}")

    if errors:
        return errors

    # Check DataFrames are DataFrames
    for attr in required_attrs[:-1]:
        df = getattr(result, attr)
        if not isinstance(df, pd.DataFrame):
            errors.append(f"[L5 {scenario_name}] {attr} is not a DataFrame: {type(df)}")

    # Check critical columns in vince_features
    if not result.vince_features.empty:
        required_features = ['feature_state_ordinal', 'feature_direction_long',
                            'feature_bias_aligned', 'target_be_plus_fees_rate',
                            'sample_weight']
        for col in required_features:
            if col not in result.vince_features.columns:
                errors.append(f"[L5 {scenario_name}] vince_features missing '{col}' column")

    # Check sample_weight values
    if not result.vince_features.empty and 'sample_weight' in result.vince_features.columns:
        weights = result.vince_features['sample_weight'].unique()
        valid_weights = {0.5, 1.0}
        invalid = set(weights) - valid_weights
        if invalid:
            errors.append(f"[L5 {scenario_name}] Invalid sample weights: {invalid}")

    # Check state_summary has required columns
    if not result.state_summary.empty:
        required_cols = ['bbw_state', 'bias_direction', 'state_quality']
        for col in required_cols:
            if col not in result.state_summary.columns:
                errors.append(f"[L5 {scenario_name}] state_summary missing '{col}' column")

    # Check state_quality values
    if not result.state_summary.empty and 'state_quality' in result.state_summary.columns:
        qualities = result.state_summary['state_quality'].unique()
        valid_qualities = {'HIGH_QUALITY', 'MIXED', 'DEAD'}
        invalid = set(qualities) - valid_qualities
        if invalid:
            errors.append(f"[L5 {scenario_name}] Invalid state_quality values: {invalid}")

    return errors


# =============================================================================
# SCENARIO GENERATORS
# =============================================================================

def scenario_normal(seed):
    """Normal scenario: medium data, medium states.

    Groups = 4 combos * 2 directions * 5 states = 40.
    Trades per group = 1600 / 40 = 40 >= min_trades_per_group=10.
    """
    return {
        'name': f'normal_{seed}',
        'n_trades': 1600,
        'n_bars': 5000,
        'n_states': 5,
        'seed': seed
    }


def scenario_small_sample(seed):
    """Small sample scenario: few states, minimum viable data.

    Groups = 4 combos * 2 directions * 2 states = 16.
    Trades per group = 400 / 16 = 25 >= min_trades_per_group=10.
    """
    return {
        'name': f'small_{seed}',
        'n_trades': 400,
        'n_bars': 1500,
        'n_states': 2,
        'seed': seed
    }


def scenario_high_volatility(seed):
    """High volatility scenario: lots of trades, many states.

    Groups = 4 combos * 2 directions * 7 states = 56.
    Trades per group = 1600 / 56 = 28 >= min_trades_per_group=10.
    """
    return {
        'name': f'highvol_{seed}',
        'n_trades': 1600,
        'n_bars': 4000,
        'n_states': 7,
        'seed': seed
    }


def scenario_many_states(seed):
    """Many states scenario: all 9 BBW states.

    Groups = 4 combos * 2 directions * 9 states = 72.
    Trades per group = 2000 / 72 = 27 >= min_trades_per_group=10.
    """
    return {
        'name': f'manystates_{seed}',
        'n_trades': 2000,
        'n_bars': 6000,
        'n_states': 9,
        'seed': seed
    }


def scenario_random(seed):
    """Fully random scenario: all parameters random.

    Uses conservative n_trades floor to ensure enough data per group.
    Worst case: 9 states * 4 combos * 2 directions = 72 groups.
    Floor of 2000 trades gives 2000/72 = 27 >= min_trades_per_group=10.
    """
    np.random.seed(seed)
    n_states = np.random.randint(3, 10)
    return {
        'name': f'random_{seed}',
        'n_trades': np.random.randint(2000, 4000),
        'n_bars': np.random.randint(4000, 8000),
        'n_states': n_states,
        'seed': seed
    }


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_scenario(scenario):
    """Run full L4->L4b->L5 pipeline on one scenario.

    Args:
        scenario: Dict with scenario parameters

    Returns:
        Tuple of (success: bool, errors: list, timings: dict)
    """
    import time

    errors = []
    timings = {}

    try:
        # Generate data
        t0 = time.time()
        backtester_results, bbw_states = generate_random_backtester_results(
            n_trades=scenario['n_trades'],
            n_bars=scenario['n_bars'],
            n_states=scenario['n_states'],
            seed=scenario['seed']
        )
        timings['data_gen'] = time.time() - t0

        # Layer 4: Analyzer
        t0 = time.time()
        l4_result = analyze_bbw_patterns_v2(
            backtester_results=backtester_results,
            bbw_states=bbw_states,
            symbol='TEST',
            min_trades_per_group=10
        )
        timings['layer4'] = time.time() - t0

        # Validate Layer 4
        l4_errors = validate_layer4_output(l4_result, scenario['name'])
        errors.extend(l4_errors)
        if l4_errors:
            return False, errors, timings

        # Layer 4b: Monte Carlo
        t0 = time.time()
        l4b_result = run_monte_carlo_v2(
            l4_result,
            n_sims=100,  # Small for speed
            confidence=0.90,
            min_trades=50,  # Lower for random data
            seed=scenario['seed']
        )
        timings['layer4b'] = time.time() - t0

        # Validate Layer 4b
        l4b_errors = validate_layer4b_output(l4b_result, scenario['name'])
        errors.extend(l4b_errors)
        if l4b_errors:
            return False, errors, timings

        # Layer 5: Report
        t0 = time.time()
        l5_result = generate_vince_features_v2(l4_result, l4b_result)
        timings['layer5'] = time.time() - t0

        # Validate Layer 5
        l5_errors = validate_layer5_output(l5_result, scenario['name'])
        errors.extend(l5_errors)
        if l5_errors:
            return False, errors, timings

        return True, errors, timings

    except Exception as e:
        errors.append(f"[EXCEPTION {scenario['name']}] {type(e).__name__}: {e}")
        return False, errors, timings


def main():
    """Run random scenario tests."""
    parser = argparse.ArgumentParser(description='BBW V2 Integration Test - Random Scenarios')
    parser.add_argument('--scenarios', type=int, default=10, help='Number of scenarios to test')
    parser.add_argument('--seed', type=int, default=42, help='Base random seed')
    args = parser.parse_args()

    print("="*70)
    print("BBW V2 Integration Test - Random Scenarios")
    print("="*70)
    print(f"Testing {args.scenarios} scenarios with base seed {args.seed}")
    print()

    # Generate scenarios
    scenario_types = [scenario_normal, scenario_small_sample, scenario_high_volatility,
                     scenario_many_states, scenario_random]

    scenarios = []
    for i in range(args.scenarios):
        seed = args.seed + i
        scenario_type = scenario_types[i % len(scenario_types)]
        scenarios.append(scenario_type(seed))

    # Run scenarios
    results = []
    total_errors = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{args.scenarios}] Running {scenario['name']}... ", end='', flush=True)

        success, errors, timings = run_scenario(scenario)
        results.append(success)

        if success:
            total_time = sum(timings.values())
            print(f"PASS ({total_time:.2f}s)")
        else:
            print(f"FAIL")
            total_errors.extend(errors)
            for error in errors:
                print(f"    {error}")

    # Summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Scenarios run: {len(scenarios)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    print(f"Total errors: {len(total_errors)}")
    print()

    if total_errors:
        print("ERRORS:")
        for error in total_errors:
            print(f"  - {error}")
        print()
        return 1
    else:
        print("ALL SCENARIOS PASSED!")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
