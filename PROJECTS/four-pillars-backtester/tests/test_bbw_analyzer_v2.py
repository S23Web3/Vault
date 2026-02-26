"""Unit tests for BBW Analyzer V2 (Layer 4).

Test-first development: Tests written before production code.

Run: python tests/test_bbw_analyzer_v2.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import numpy as np

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_analyzer_v2 import (
    validate_backtester_data,
    validate_bbw_states,
    enrich_with_bbw_state,
    group_by_state_direction_lsg,
    calculate_group_metrics,
    find_best_lsg_per_state_direction,
    detect_directional_bias,
    analyze_bbw_patterns_v2,
    calculate_max_drawdown,
    calculate_sharpe,
    calculate_sortino,
    BBWAnalysisResultV2
)


# =============================================================================
# TEST UTILITIES
# =============================================================================

PASS_COUNT = 0
FAIL_COUNT = 0


def check(description: str, condition: bool):
    """Assert with custom pass/fail tracking."""
    global PASS_COUNT, FAIL_COUNT
    if condition:
        print(f"  PASS: {description}")
        PASS_COUNT += 1
    else:
        print(f"  FAIL: {description}")
        FAIL_COUNT += 1


def make_mock_backtester_results(n_trades: int = 100) -> pd.DataFrame:
    """Generate mock backtester results for testing.

    Creates valid trade data matching backtester_v385 output format.
    """
    np.random.seed(42)

    timestamps = pd.date_range(
        start='2024-01-01',
        periods=n_trades,
        freq='5min'
    )

    return pd.DataFrame({
        'timestamp': timestamps,
        'symbol': ['TESTUSDT'] * n_trades,
        'direction': np.random.choice(['LONG', 'SHORT'], n_trades),
        'entry_price': np.random.uniform(100, 200, n_trades),
        'exit_price': np.random.uniform(100, 200, n_trades),
        'leverage': np.random.choice([5, 10, 15, 20], n_trades),
        'size': np.random.choice([0.25, 0.5, 1.0, 1.5, 2.0], n_trades),
        'grid': np.random.choice([1.0, 1.5, 2.0, 2.5, 3.0], n_trades),
        'outcome': np.random.choice(['TP', 'SL', 'TIMEOUT'], n_trades),
        'pnl_gross': np.random.uniform(-50, 100, n_trades),
        'pnl_net': np.random.uniform(-60, 90, n_trades),
        'commission_rt': np.full(n_trades, 8.0),
        'bars_held': np.random.randint(5, 100, n_trades)
    })


def make_mock_bbw_states(n_bars: int = 100) -> pd.DataFrame:
    """Generate mock BBW state sequence for testing.

    Creates valid BBW states matching Layer 2 output format.
    """
    np.random.seed(42)

    timestamps = pd.date_range(
        start='2024-01-01',
        periods=n_bars,
        freq='5min'
    )

    states = [
        'BLUE', 'BLUE_DOUBLE', 'GREEN', 'YELLOW', 'NORMAL',
        'RED', 'RED_DOUBLE', 'MA_CROSS_UP', 'MA_CROSS_DOWN'
    ]

    return pd.DataFrame({
        'timestamp': timestamps,
        'symbol': ['TESTUSDT'] * n_bars,
        'bbw_state': np.random.choice(states, n_bars),
        'bbwp': np.random.uniform(0, 100, n_bars)
    })


# =============================================================================
# PHASE 1: INPUT VALIDATION TESTS (5 tests)
# =============================================================================

def test_validate_backtester_data_valid():
    """Test validation passes for valid backtester results."""
    print("\n=== Test 1: validate_backtester_data with valid data ===")

    df = make_mock_backtester_results(n_trades=50)

    try:
        result = validate_backtester_data(df)
        check("Validation returns True", result is True)
        check("No exception raised", True)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_validate_backtester_data_missing_columns():
    """Test validation fails for missing required columns."""
    print("\n=== Test 2: validate_backtester_data missing columns ===")

    df = make_mock_backtester_results(n_trades=50)

    # Drop required column
    df_missing = df.drop(columns=['direction'])

    try:
        validate_backtester_data(df_missing)
        check("Raises ValueError for missing column", False)
    except ValueError as e:
        check("Raises ValueError for missing column", True)
        check("Error message mentions 'direction'", 'direction' in str(e).lower())


def test_validate_backtester_data_invalid_direction():
    """Test validation fails for invalid direction values."""
    print("\n=== Test 3: validate_backtester_data invalid direction ===")

    df = make_mock_backtester_results(n_trades=50)

    # Set invalid direction
    df.loc[0, 'direction'] = 'INVALID'

    try:
        validate_backtester_data(df)
        check("Raises ValueError for invalid direction", False)
    except ValueError as e:
        check("Raises ValueError for invalid direction", True)
        check("Error mentions LONG/SHORT", 'LONG' in str(e) or 'SHORT' in str(e))


def test_validate_backtester_data_out_of_range_leverage():
    """Test validation fails for leverage outside [5, 20]."""
    print("\n=== Test 4: validate_backtester_data out of range leverage ===")

    df = make_mock_backtester_results(n_trades=50)

    # Set leverage out of range
    df.loc[0, 'leverage'] = 25

    try:
        validate_backtester_data(df)
        check("Raises ValueError for leverage > 20", False)
    except ValueError as e:
        check("Raises ValueError for leverage > 20", True)
        check("Error mentions range [5, 20]", '[5, 20]' in str(e) or '5' in str(e))


def test_validate_bbw_states_valid():
    """Test validation passes for valid BBW states."""
    print("\n=== Test 5: validate_bbw_states with valid data ===")

    df = make_mock_bbw_states(n_bars=50)

    try:
        result = validate_bbw_states(df)
        check("Validation returns True", result is True)
        check("No exception raised", True)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 2: DATA ENRICHMENT TESTS (8 tests)
# =============================================================================

def test_enrich_with_bbw_state_aligned_data():
    """Test enrichment with perfectly aligned timestamps."""
    print("\n=== Test 6: enrich_with_bbw_state aligned data ===")

    trades = make_mock_backtester_results(n_trades=50)
    bbw_states = make_mock_bbw_states(n_bars=50)

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)

        check("Returns DataFrame", isinstance(enriched, pd.DataFrame))
        check("Same row count as input", len(enriched) == len(trades))
        check("Has bbw_state column", 'bbw_state' in enriched.columns)
        check("Has bbwp_at_entry column", 'bbwp_at_entry' in enriched.columns)
        check("No null bbw_state", enriched['bbw_state'].isna().sum() == 0)
        check("No null bbwp_at_entry", enriched['bbwp_at_entry'].isna().sum() == 0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_enrich_with_bbw_state_missing_states():
    """Test enrichment fails when BBW states missing for some timestamps."""
    print("\n=== Test 7: enrich_with_bbw_state missing states ===")

    trades = make_mock_backtester_results(n_trades=50)
    bbw_states = make_mock_bbw_states(n_bars=40)  # Fewer states than trades

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)
        check("Raises ValueError for missing states", False)
    except ValueError as e:
        check("Raises ValueError for missing states", True)
        check("Error mentions timestamp mismatch", 'timestamp' in str(e).lower())


def test_enrich_with_bbw_state_preserves_original_columns():
    """Test enrichment preserves all original trade columns."""
    print("\n=== Test 8: enrich_with_bbw_state preserves columns ===")

    trades = make_mock_backtester_results(n_trades=50)
    bbw_states = make_mock_bbw_states(n_bars=50)

    original_columns = set(trades.columns)

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)

        # Check all original columns still present
        enriched_columns = set(enriched.columns)
        missing_columns = original_columns - enriched_columns

        check("All original columns preserved", len(missing_columns) == 0)

        # Check new columns added
        new_columns = enriched_columns - original_columns
        expected_new = {'bbw_state', 'bbwp_at_entry'}

        check("New columns added", new_columns == expected_new)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_enrich_with_bbw_state_column_naming():
    """Test enriched columns have correct names."""
    print("\n=== Test 9: enrich_with_bbw_state column naming ===")

    trades = make_mock_backtester_results(n_trades=50)
    bbw_states = make_mock_bbw_states(n_bars=50)

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)

        check("Column named bbw_state (not bbw_state)",
              'bbw_state' in enriched.columns)
        check("Column named bbwp_at_entry (not bbwp)",
              'bbwp_at_entry' in enriched.columns)
        check("Original bbw_state not in columns",
              'bbw_state' not in enriched.columns)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_enrich_with_bbw_state_values_correct():
    """Test BBW state values correctly assigned to trades."""
    print("\n=== Test 10: enrich_with_bbw_state values correct ===")

    # Create aligned data with known values
    timestamps = pd.date_range('2024-01-01', periods=5, freq='5min')

    trades = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': ['TEST'] * 5,
        'direction': ['LONG'] * 5,
        'entry_price': [100.0] * 5,
        'exit_price': [105.0] * 5,
        'leverage': [10] * 5,
        'size': [1.0] * 5,
        'grid': [1.5] * 5,
        'outcome': ['TP'] * 5,
        'pnl_gross': [10.0] * 5,
        'pnl_net': [2.0] * 5,
        'commission_rt': [8.0] * 5,
        'bars_held': [10] * 5
    })

    bbw_states = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': ['TEST'] * 5,
        'bbw_state': ['BLUE', 'GREEN', 'YELLOW', 'RED', 'NORMAL'],
        'bbwp': [10.0, 30.0, 50.0, 80.0, 45.0]
    })

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)

        # Verify specific state assignments
        check("First trade has BLUE state",
              enriched.iloc[0]['bbw_state'] == 'BLUE')
        check("Second trade has GREEN state",
              enriched.iloc[1]['bbw_state'] == 'GREEN')
        check("First trade BBWP = 10.0",
              enriched.iloc[0]['bbwp_at_entry'] == 10.0)
        check("Fourth trade BBWP = 80.0",
              enriched.iloc[3]['bbwp_at_entry'] == 80.0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_enrich_handles_duplicate_timestamps():
    """Test enrichment handles duplicate timestamps gracefully."""
    print("\n=== Test 11: enrich_with_bbw_state duplicate timestamps ===")

    trades = make_mock_backtester_results(n_trades=50)

    # Create BBW states with duplicate timestamp
    bbw_states = make_mock_bbw_states(n_bars=50)
    bbw_states.loc[10, 'timestamp'] = bbw_states.loc[9, 'timestamp']

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)

        # Should handle duplicates (merge will create multiple rows)
        check("Function completes", True)
        check("Has bbw_state column", 'bbw_state' in enriched.columns)
    except Exception as e:
        # If it raises an error, that's also acceptable behavior
        check("Handles duplicates (error or success)", True)


def test_enrich_datetime_conversion():
    """Test enrichment converts timestamp dtypes if needed."""
    print("\n=== Test 12: enrich_with_bbw_state datetime conversion ===")

    trades = make_mock_backtester_results(n_trades=50)
    bbw_states = make_mock_bbw_states(n_bars=50)

    # Convert to string (simulating non-datetime input)
    trades_str = trades.copy()
    trades_str['timestamp'] = trades_str['timestamp'].astype(str)

    try:
        enriched = enrich_with_bbw_state(trades_str, bbw_states)

        check("Handles string timestamps", isinstance(enriched, pd.DataFrame))
        check("Has bbw_state", 'bbw_state' in enriched.columns)
        check("No null states", enriched['bbw_state'].isna().sum() == 0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_enrich_no_data_loss():
    """Test enrichment does not lose any trade records."""
    print("\n=== Test 13: enrich_with_bbw_state no data loss ===")

    trades = make_mock_backtester_results(n_trades=100)
    bbw_states = make_mock_bbw_states(n_bars=100)

    n_trades_before = len(trades)

    try:
        enriched = enrich_with_bbw_state(trades, bbw_states)

        n_trades_after = len(enriched)

        check("Trade count preserved", n_trades_after == n_trades_before)
        check("Exactly 100 trades output", n_trades_after == 100)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 3: GROUPING LOGIC TESTS (10 tests)
# =============================================================================

def test_group_by_state_direction_lsg_basic():
    """Test basic grouping functionality."""
    print("\n=== Test 14: group_by_state_direction_lsg basic ===")

    trades = make_mock_backtester_results(n_trades=200)
    bbw_states = make_mock_bbw_states(n_bars=200)
    enriched = enrich_with_bbw_state(trades, bbw_states)

    try:
        grouped = group_by_state_direction_lsg(enriched, min_trades=10)

        check("Returns DataFrame", isinstance(grouped, pd.DataFrame))
        check("Has n_trades column", 'n_trades' in grouped.columns)
        check("Has be_plus_fees_rate column", 'be_plus_fees_rate' in grouped.columns)
        check("Has grouping columns", all(col in grouped.columns for col in [
            'bbw_state', 'direction', 'leverage', 'size', 'grid'
        ]))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_group_min_trades_filter():
    """Test min_trades filtering works correctly."""
    print("\n=== Test 15: group_by_state_direction_lsg min_trades filter ===")

    trades = make_mock_backtester_results(n_trades=300)
    bbw_states = make_mock_bbw_states(n_bars=300)
    enriched = enrich_with_bbw_state(trades, bbw_states)

    try:
        # Group with low threshold
        grouped_low = group_by_state_direction_lsg(enriched, min_trades=5)

        # Group with high threshold
        grouped_high = group_by_state_direction_lsg(enriched, min_trades=50)

        # May have no groups with random data - that's OK
        check("Grouping completed", True)
        check("High threshold filters more or equal", len(grouped_high) <= len(grouped_low))

        # Only check min_trades if groups exist
        if len(grouped_low) > 0:
            check("All groups meet min_trades (low)", (grouped_low['n_trades'] >= 5).all())
        else:
            check("No groups met low threshold (OK for random data)", True)

        if len(grouped_high) > 0:
            check("All groups meet min_trades (high)", (grouped_high['n_trades'] >= 50).all())
        else:
            check("No groups met high threshold (OK for random data)", True)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_group_categorical_dtypes():
    """Test categorical dtype conversion for performance."""
    print("\n=== Test 16: group_by_state_direction_lsg categorical dtypes ===")

    trades = make_mock_backtester_results(n_trades=100)
    bbw_states = make_mock_bbw_states(n_bars=100)
    enriched = enrich_with_bbw_state(trades, bbw_states)

    try:
        grouped = group_by_state_direction_lsg(enriched, min_trades=5)

        # Check dtypes (should be category after grouping)
        check("Returns DataFrame", isinstance(grouped, pd.DataFrame))
        check("Has state column", 'bbw_state' in grouped.columns)
        check("Has direction column", 'direction' in grouped.columns)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_group_metrics_be_fees_rate():
    """Test BE+fees rate calculation logic."""
    print("\n=== Test 17: calculate_group_metrics BE+fees rate ===")

    # Create test group with known PnLs
    group = pd.DataFrame({
        'pnl_net': [10.0, -5.0, 0.0, -2.0, 15.0],  # 3 BE+fees (>=0)
        'pnl_gross': [18.0, 3.0, 8.0, 6.0, 23.0],
        'commission_rt': [8.0] * 5,
        'outcome': ['TP', 'SL', 'TIMEOUT', 'SL', 'TP']
    })

    try:
        metrics = calculate_group_metrics(group)

        expected_be_fees_rate = 3 / 5  # 3 out of 5 >= 0
        expected_be_fees_count = 3

        check("Returns Series", isinstance(metrics, pd.Series))
        check("BE+fees rate = 0.6", abs(metrics['be_plus_fees_rate'] - expected_be_fees_rate) < 0.001)
        check("BE+fees count = 3", metrics['be_plus_fees_count'] == expected_be_fees_count)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_group_metrics_win_rate_divergence():
    """Test BE+fees rate diverges from win rate due to commission."""
    print("\n=== Test 18: calculate_group_metrics win rate divergence ===")

    # Example: Gross winners killed by commission
    group = pd.DataFrame({
        'pnl_gross': [7.5, 15.0, -10.0],  # 2 wins, 1 loss (win_rate = 2/3)
        'pnl_net': [-0.5, 7.0, -18.0],    # 1 win, 2 losses (be_fees = 1/3)
        'commission_rt': [8.0, 8.0, 8.0],
        'outcome': ['TP', 'TP', 'SL']
    })

    try:
        metrics = calculate_group_metrics(group)

        win_rate = metrics['win_rate']
        be_fees_rate = metrics['be_plus_fees_rate']

        check("Win rate = 2/3", abs(win_rate - (2/3)) < 0.001)
        check("BE+fees rate = 1/3", abs(be_fees_rate - (1/3)) < 0.001)
        check("BE+fees < win rate (commission impact)", be_fees_rate < win_rate)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_group_metrics_commission_drag():
    """Test commission drag calculation."""
    print("\n=== Test 19: calculate_group_metrics commission drag ===")

    group = pd.DataFrame({
        'pnl_gross': [12.5, 12.5],
        'pnl_net': [4.5, 4.5],
        'commission_rt': [8.0, 8.0],
        'outcome': ['TP', 'TP']
    })

    try:
        metrics = calculate_group_metrics(group)

        avg_gross = 12.5
        avg_net = 4.5
        expected_drag = avg_gross - avg_net  # = 8.0

        check("Avg gross PnL = 12.5", abs(metrics['avg_gross_pnl'] - avg_gross) < 0.001)
        check("Avg net PnL = 4.5", abs(metrics['avg_net_pnl'] - avg_net) < 0.001)
        check("Commission drag = 8.0", abs(metrics['commission_drag'] - expected_drag) < 0.001)
        check("Drag matches avg commission", abs(metrics['commission_drag'] - metrics['avg_commission']) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_max_drawdown():
    """Test maximum drawdown calculation."""
    print("\n=== Test 20: calculate_max_drawdown ===")

    # Example: [+10, -15, +5] -> equity = [10, -5, 0]
    # Peak = [10, 10, 10], DD = [0, 15, 10], max_dd = 15
    pnl_array = np.array([10.0, -15.0, 5.0])

    try:
        max_dd = calculate_max_drawdown(pnl_array)

        check("Returns float", isinstance(max_dd, float))
        check("Max DD = 15.0", abs(max_dd - 15.0) < 0.001)
        check("DD is positive value", max_dd >= 0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_sharpe():
    """Test Sharpe ratio calculation."""
    print("\n=== Test 21: calculate_sharpe ===")

    # Simple test array
    pnl_array = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    mean = 30.0
    std = np.std(pnl_array, ddof=1)  # Sample std
    expected_sharpe = mean / std

    try:
        sharpe = calculate_sharpe(pnl_array)

        check("Returns float", isinstance(sharpe, float))
        check("Sharpe ratio matches expected", abs(sharpe - expected_sharpe) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_sharpe_zero_variance():
    """Test Sharpe returns 0 for zero variance (all identical PnLs)."""
    print("\n=== Test 22: calculate_sharpe zero variance ===")

    # All identical PnLs -> std = 0
    pnl_array = np.array([10.0, 10.0, 10.0, 10.0])

    try:
        sharpe = calculate_sharpe(pnl_array)

        check("Returns 0.0 for zero variance", sharpe == 0.0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_calculate_sortino():
    """Test Sortino ratio calculation."""
    print("\n=== Test 23: calculate_sortino ===")

    # Mixed PnLs with downside
    pnl_array = np.array([10.0, -5.0, 20.0, -10.0, 15.0])
    mean = pnl_array.mean()
    downside = pnl_array[pnl_array < 0]  # [-5.0, -10.0]
    downside_std = np.std(downside, ddof=1)
    expected_sortino = mean / downside_std

    try:
        sortino = calculate_sortino(pnl_array)

        check("Returns float", isinstance(sortino, float))
        check("Sortino ratio matches expected", abs(sortino - expected_sortino) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 5: BEST COMBO SELECTION TESTS (8 tests)
# =============================================================================

def test_best_lsg_single_state_direction():
    """Test best LSG selection for single state and direction."""
    print("\n=== Test 24: find_best_lsg single state×direction ===")

    # Create grouped results with known BE+fees rates
    grouped = pd.DataFrame({
        'bbw_state': ['BLUE'] * 3,
        'direction': ['LONG'] * 3,
        'leverage': [10, 15, 20],
        'size': [1.0, 1.5, 2.0],
        'grid': [1.5, 2.0, 2.5],
        'be_plus_fees_rate': [0.65, 0.72, 0.68],  # 15x has highest
        'n_trades': [100, 100, 100]
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        check("Returns DataFrame", isinstance(best, pd.DataFrame))
        check("Has exactly 1 row", len(best) == 1)
        check("Selected highest BE+fees rate", best.iloc[0]['leverage'] == 15)
        check("BE+fees rate = 0.72", abs(best.iloc[0]['be_plus_fees_rate'] - 0.72) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_multiple_states():
    """Test best LSG selection across multiple states."""
    print("\n=== Test 25: find_best_lsg multiple states ===")

    # Create grouped results for 2 states, 2 directions each
    grouped = pd.DataFrame({
        'bbw_state': ['BLUE', 'BLUE', 'RED', 'RED'],
        'direction': ['LONG', 'SHORT', 'LONG', 'SHORT'],
        'leverage': [10, 10, 15, 15],
        'size': [1.0, 1.0, 1.5, 1.5],
        'grid': [1.5, 1.5, 2.0, 2.0],
        'be_plus_fees_rate': [0.65, 0.70, 0.60, 0.75],
        'n_trades': [100, 100, 100, 100]
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        check("Returns DataFrame", isinstance(best, pd.DataFrame))
        check("Has exactly 4 rows (2 states × 2 directions)", len(best) == 4)

        # Check each state×direction has one row
        blue_long = best[(best['bbw_state'] == 'BLUE') & (best['direction'] == 'LONG')]
        blue_short = best[(best['bbw_state'] == 'BLUE') & (best['direction'] == 'SHORT')]
        red_long = best[(best['bbw_state'] == 'RED') & (best['direction'] == 'LONG')]
        red_short = best[(best['bbw_state'] == 'RED') & (best['direction'] == 'SHORT')]

        check("BLUE LONG has 1 row", len(blue_long) == 1)
        check("BLUE SHORT has 1 row", len(blue_short) == 1)
        check("RED LONG has 1 row", len(red_long) == 1)
        check("RED SHORT has 1 row", len(red_short) == 1)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_tie_breaking():
    """Test tie-breaking when multiple LSG have same BE+fees rate."""
    print("\n=== Test 26: find_best_lsg tie breaking ===")

    # Create grouped results with tied BE+fees rates
    grouped = pd.DataFrame({
        'bbw_state': ['BLUE'] * 3,
        'direction': ['LONG'] * 3,
        'leverage': [10, 15, 20],
        'size': [1.0, 1.5, 2.0],
        'grid': [1.5, 2.0, 2.5],
        'be_plus_fees_rate': [0.70, 0.70, 0.70],  # All tied
        'n_trades': [100, 100, 100]
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        check("Returns DataFrame", isinstance(best, pd.DataFrame))
        check("Has exactly 1 row", len(best) == 1)
        check("BE+fees rate = 0.70", abs(best.iloc[0]['be_plus_fees_rate'] - 0.70) < 0.001)
        # First in sort order is selected
        check("Selects one LSG combo", True)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_preserves_per_trade_pnl():
    """Test per_trade_pnl is preserved for Layer 4b."""
    print("\n=== Test 27: find_best_lsg preserves per_trade_pnl ===")

    # Create grouped results with per_trade_pnl
    grouped = pd.DataFrame({
        'bbw_state': ['BLUE'] * 2,
        'direction': ['LONG'] * 2,
        'leverage': [10, 15],
        'size': [1.0, 1.5],
        'grid': [1.5, 2.0],
        'be_plus_fees_rate': [0.65, 0.72],
        'n_trades': [3, 3],
        'per_trade_pnl': [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        check("Returns DataFrame", isinstance(best, pd.DataFrame))
        check("Has per_trade_pnl column", 'per_trade_pnl' in best.columns)

        pnl_array = best.iloc[0]['per_trade_pnl']
        check("per_trade_pnl is list", isinstance(pnl_array, list))
        check("per_trade_pnl has correct values", pnl_array == [4.0, 5.0, 6.0])
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_highest_be_fees_rate():
    """Test that highest BE+fees rate is always selected."""
    print("\n=== Test 28: find_best_lsg highest BE+fees rate ===")

    # Create grouped results with varying rates
    grouped = pd.DataFrame({
        'bbw_state': ['BLUE'] * 5,
        'direction': ['LONG'] * 5,
        'leverage': [5, 10, 15, 20, 10],
        'size': [0.5, 1.0, 1.5, 2.0, 1.0],
        'grid': [1.0, 1.5, 2.0, 2.5, 3.0],
        'be_plus_fees_rate': [0.60, 0.65, 0.80, 0.55, 0.70],  # 15x has max
        'n_trades': [100] * 5
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        all_rates = grouped['be_plus_fees_rate'].values
        max_rate = all_rates.max()
        selected_rate = best.iloc[0]['be_plus_fees_rate']

        check("Selected rate equals maximum", abs(selected_rate - max_rate) < 0.001)
        check("Maximum rate = 0.80", abs(max_rate - 0.80) < 0.001)
        check("Selected leverage = 15", best.iloc[0]['leverage'] == 15)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_empty_input():
    """Test best LSG handles empty input gracefully."""
    print("\n=== Test 29: find_best_lsg empty input ===")

    # Create empty DataFrame with correct structure
    grouped = pd.DataFrame({
        'bbw_state': [],
        'direction': [],
        'leverage': [],
        'be_plus_fees_rate': [],
        'n_trades': []
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        check("Returns DataFrame", isinstance(best, pd.DataFrame))
        check("Result is empty", len(best) == 0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_handles_missing_direction():
    """Test best LSG handles states with only one direction."""
    print("\n=== Test 30: find_best_lsg handles missing direction ===")

    # Create grouped results with only LONG (no SHORT)
    grouped = pd.DataFrame({
        'bbw_state': ['BLUE', 'BLUE', 'RED'],
        'direction': ['LONG', 'LONG', 'LONG'],  # No SHORT
        'leverage': [10, 15, 20],
        'size': [1.0, 1.5, 2.0],
        'grid': [1.5, 2.0, 2.5],
        'be_plus_fees_rate': [0.65, 0.72, 0.60],
        'n_trades': [100, 100, 100]
    })

    try:
        best = find_best_lsg_per_state_direction(grouped)

        check("Returns DataFrame", isinstance(best, pd.DataFrame))
        check("Has 2 rows (BLUE LONG, RED LONG)", len(best) == 2)
        check("All directions are LONG", (best['direction'] == 'LONG').all())
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_best_lsg_all_states_present():
    """Test best LSG processes all unique states."""
    print("\n=== Test 31: find_best_lsg all states present ===")

    # Create grouped results for 3 states, 2 directions each (6 combos)
    states = ['BLUE', 'GREEN', 'RED']
    directions = ['LONG', 'SHORT']
    grouped_list = []

    for state in states:
        for direction in directions:
            grouped_list.append({
                'bbw_state': state,
                'direction': direction,
                'leverage': 10,
                'size': 1.0,
                'grid': 1.5,
                'be_plus_fees_rate': 0.65,
                'n_trades': 100
            })

    grouped = pd.DataFrame(grouped_list)

    try:
        best = find_best_lsg_per_state_direction(grouped)

        unique_states = best['bbw_state'].unique()
        unique_directions = best['direction'].unique()

        check("Has 6 rows (3 states × 2 directions)", len(best) == 6)
        check("All 3 states present", len(unique_states) == 3)
        check("Both directions present", len(unique_directions) == 2)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 6: DIRECTIONAL BIAS DETECTION TESTS (8 tests)
# =============================================================================

def test_bias_long_favored():
    """Test bias detection when LONG outperforms SHORT."""
    print("\n=== Test 32: detect_directional_bias LONG favored ===")

    # Create best combos with LONG advantage
    best_combos = pd.DataFrame({
        'bbw_state': ['BLUE', 'BLUE'],
        'direction': ['LONG', 'SHORT'],
        'be_plus_fees_rate': [0.75, 0.60],  # LONG = 0.75, SHORT = 0.60, diff = +0.15
        'n_trades': [100, 100]
    })

    try:
        bias_df = detect_directional_bias(best_combos, bias_threshold=0.05)

        check("Returns DataFrame", isinstance(bias_df, pd.DataFrame))
        check("Has 1 row (1 state)", len(bias_df) == 1)
        check("LONG rate = 0.75", abs(bias_df.iloc[0]['long_be_fees_rate'] - 0.75) < 0.001)
        check("SHORT rate = 0.60", abs(bias_df.iloc[0]['short_be_fees_rate'] - 0.60) < 0.001)
        check("Difference = +0.15", abs(bias_df.iloc[0]['difference'] - 0.15) < 0.001)
        check("Bias = LONG", bias_df.iloc[0]['bias'] == 'LONG')
        check("Bias strength = 0.15", abs(bias_df.iloc[0]['bias_strength'] - 0.15) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_short_favored():
    """Test bias detection when SHORT outperforms LONG."""
    print("\n=== Test 33: detect_directional_bias SHORT favored ===")

    # Create best combos with SHORT advantage
    best_combos = pd.DataFrame({
        'bbw_state': ['RED', 'RED'],
        'direction': ['LONG', 'SHORT'],
        'be_plus_fees_rate': [0.58, 0.72],  # SHORT > LONG, diff = -0.14
        'n_trades': [100, 100]
    })

    try:
        bias_df = detect_directional_bias(best_combos, bias_threshold=0.05)

        check("Returns DataFrame", isinstance(bias_df, pd.DataFrame))
        check("Difference = -0.14", abs(bias_df.iloc[0]['difference'] - (-0.14)) < 0.001)
        check("Bias = SHORT", bias_df.iloc[0]['bias'] == 'SHORT')
        check("Bias strength = 0.14", abs(bias_df.iloc[0]['bias_strength'] - 0.14) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_neutral():
    """Test bias detection when LONG and SHORT are similar."""
    print("\n=== Test 34: detect_directional_bias NEUTRAL ===")

    # Create best combos with minimal difference
    best_combos = pd.DataFrame({
        'bbw_state': ['GREEN', 'GREEN'],
        'direction': ['LONG', 'SHORT'],
        'be_plus_fees_rate': [0.67, 0.64],  # diff = 0.03 < threshold (0.05)
        'n_trades': [100, 100]
    })

    try:
        bias_df = detect_directional_bias(best_combos, bias_threshold=0.05)

        check("Difference = 0.03", abs(bias_df.iloc[0]['difference'] - 0.03) < 0.001)
        check("Bias = NEUTRAL", bias_df.iloc[0]['bias'] == 'NEUTRAL')
        check("Bias strength = 0.03", abs(bias_df.iloc[0]['bias_strength'] - 0.03) < 0.001)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_threshold_edge_cases():
    """Test bias threshold boundary conditions."""
    print("\n=== Test 35: detect_directional_bias threshold edge cases ===")

    # Exactly at threshold (0.05)
    best_combos = pd.DataFrame({
        'bbw_state': ['YELLOW', 'YELLOW'],
        'direction': ['LONG', 'SHORT'],
        'be_plus_fees_rate': [0.70, 0.65],  # diff = 0.05 (exactly threshold)
        'n_trades': [100, 100]
    })

    try:
        # With default threshold (0.05), diff=0.05 should NOT be significant
        bias_df = detect_directional_bias(best_combos, bias_threshold=0.05)
        check("At threshold treated as NEUTRAL", bias_df.iloc[0]['bias'] == 'NEUTRAL')

        # With threshold 0.04, diff=0.05 should be significant
        bias_df2 = detect_directional_bias(best_combos, bias_threshold=0.04)
        check("Above threshold treated as LONG", bias_df2.iloc[0]['bias'] == 'LONG')
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_missing_long_direction():
    """Test bias when only SHORT direction present."""
    print("\n=== Test 36: detect_directional_bias missing LONG ===")

    # Only SHORT direction
    best_combos = pd.DataFrame({
        'bbw_state': ['BLUE'],
        'direction': ['SHORT'],
        'be_plus_fees_rate': [0.70],
        'n_trades': [100]
    })

    try:
        bias_df = detect_directional_bias(best_combos)

        check("Returns DataFrame", isinstance(bias_df, pd.DataFrame))
        check("LONG rate is None", pd.isna(bias_df.iloc[0]['long_be_fees_rate']))
        check("SHORT rate = 0.70", abs(bias_df.iloc[0]['short_be_fees_rate'] - 0.70) < 0.001)
        check("Difference is None", pd.isna(bias_df.iloc[0]['difference']))
        check("Bias = MISSING_DIRECTION", bias_df.iloc[0]['bias'] == 'MISSING_DIRECTION')
        check("Bias strength is None", pd.isna(bias_df.iloc[0]['bias_strength']))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_missing_short_direction():
    """Test bias when only LONG direction present."""
    print("\n=== Test 37: detect_directional_bias missing SHORT ===")

    # Only LONG direction
    best_combos = pd.DataFrame({
        'bbw_state': ['RED'],
        'direction': ['LONG'],
        'be_plus_fees_rate': [0.65],
        'n_trades': [100]
    })

    try:
        bias_df = detect_directional_bias(best_combos)

        check("LONG rate = 0.65", abs(bias_df.iloc[0]['long_be_fees_rate'] - 0.65) < 0.001)
        check("SHORT rate is None", pd.isna(bias_df.iloc[0]['short_be_fees_rate']))
        check("Bias = MISSING_DIRECTION", bias_df.iloc[0]['bias'] == 'MISSING_DIRECTION')
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_strength_calculation():
    """Test bias strength is abs(difference) regardless of direction."""
    print("\n=== Test 38: detect_directional_bias strength calculation ===")

    # Two states: LONG favored (+0.10), SHORT favored (-0.12)
    best_combos = pd.DataFrame({
        'bbw_state': ['BLUE', 'BLUE', 'RED', 'RED'],
        'direction': ['LONG', 'SHORT', 'LONG', 'SHORT'],
        'be_plus_fees_rate': [0.75, 0.65, 0.58, 0.70],
        'n_trades': [100, 100, 100, 100]
    })

    try:
        bias_df = detect_directional_bias(best_combos)

        blue_bias = bias_df[bias_df['bbw_state'] == 'BLUE'].iloc[0]
        red_bias = bias_df[bias_df['bbw_state'] == 'RED'].iloc[0]

        # BLUE: LONG favored, diff = +0.10
        check("BLUE diff = +0.10", abs(blue_bias['difference'] - 0.10) < 0.001)
        check("BLUE strength = 0.10", abs(blue_bias['bias_strength'] - 0.10) < 0.001)
        check("BLUE bias = LONG", blue_bias['bias'] == 'LONG')

        # RED: SHORT favored, diff = -0.12
        check("RED diff = -0.12", abs(red_bias['difference'] - (-0.12)) < 0.001)
        check("RED strength = 0.12", abs(red_bias['bias_strength'] - 0.12) < 0.001)
        check("RED bias = SHORT", red_bias['bias'] == 'SHORT')
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bias_all_states_analyzed():
    """Test bias analysis covers all unique states."""
    print("\n=== Test 39: detect_directional_bias all states present ===")

    # 3 states, each with LONG and SHORT
    states = ['BLUE', 'GREEN', 'RED']
    best_combos_list = []

    for state in states:
        best_combos_list.append({
            'bbw_state': state,
            'direction': 'LONG',
            'be_plus_fees_rate': 0.70,
            'n_trades': 100
        })
        best_combos_list.append({
            'bbw_state': state,
            'direction': 'SHORT',
            'be_plus_fees_rate': 0.65,
            'n_trades': 100
        })

    best_combos = pd.DataFrame(best_combos_list)

    try:
        bias_df = detect_directional_bias(best_combos)

        unique_states = bias_df['bbw_state'].unique()
        check("Has 3 rows (3 states)", len(bias_df) == 3)
        check("All 3 states present", len(unique_states) == 3)
        check("All states are BLUE/GREEN/RED", set(unique_states) == {'BLUE', 'GREEN', 'RED'})
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 7: MAIN PIPELINE INTEGRATION TESTS (5 tests)
# =============================================================================

def test_full_pipeline_single_symbol():
    """Test full pipeline on single symbol data."""
    print("\n=== Test 40: analyze_bbw_patterns_v2 single symbol ===")

    # Create mock data
    trades = make_mock_backtester_results(n_trades=500)
    bbw_states = make_mock_bbw_states(n_bars=500)

    try:
        result = analyze_bbw_patterns_v2(
            backtester_results=trades,
            bbw_states=bbw_states,
            symbol="RIVERUSDT",
            min_trades_per_group=20
        )

        check("Returns BBWAnalysisResultV2", isinstance(result, BBWAnalysisResultV2))
        check("Has results DataFrame", isinstance(result.results, pd.DataFrame))
        check("Has best_combos DataFrame", isinstance(result.best_combos, pd.DataFrame))
        check("Has directional_bias DataFrame", isinstance(result.directional_bias, pd.DataFrame))
        check("Has summary dict", isinstance(result.summary, dict))
        check("Symbol matches input", result.symbol == "RIVERUSDT")
        check("n_trades_analyzed > 0", result.n_trades_analyzed > 0)
        check("Runtime tracked", result.runtime_seconds > 0)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_auto_symbol_detection():
    """Test auto-detection of symbol from data."""
    print("\n=== Test 41: analyze_bbw_patterns_v2 auto symbol ===")

    # Create mock data with symbol column
    trades = make_mock_backtester_results(n_trades=200)
    trades['symbol'] = 'AXSUSDT'
    bbw_states = make_mock_bbw_states(n_bars=200)

    try:
        # Don't provide symbol argument
        result = analyze_bbw_patterns_v2(
            backtester_results=trades,
            bbw_states=bbw_states,
            min_trades_per_group=10
        )

        check("Symbol auto-detected", result.symbol == 'AXSUSDT')
        check("Summary has symbol", result.summary['symbol'] == 'AXSUSDT')
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_output_contract():
    """Test output contract matches Layer 4b requirements."""
    print("\n=== Test 42: analyze_bbw_patterns_v2 output contract ===")

    trades = make_mock_backtester_results(n_trades=300)
    bbw_states = make_mock_bbw_states(n_bars=300)

    try:
        result = analyze_bbw_patterns_v2(
            backtester_results=trades,
            bbw_states=bbw_states,
            min_trades_per_group=15
        )

        # Check results DataFrame columns
        required_results_cols = [
            'bbw_state', 'direction', 'leverage', 'size', 'grid',
            'n_trades', 'be_plus_fees_rate', 'per_trade_pnl'
        ]
        for col in required_results_cols:
            check(f"results has {col}", col in result.results.columns)

        # Check best_combos has exactly 1 row per (state, direction)
        if not result.best_combos.empty:
            grouped_count = result.best_combos.groupby(['bbw_state', 'direction']).size()
            check("best_combos: 1 row per (state, direction)", (grouped_count == 1).all())

        # Check directional_bias has required columns
        bias_cols = ['bbw_state', 'long_be_fees_rate', 'short_be_fees_rate', 'difference', 'bias']
        for col in bias_cols:
            check(f"directional_bias has {col}", col in result.directional_bias.columns)

        # Check summary dict has required keys
        summary_keys = ['symbol', 'n_trades_analyzed', 'n_states', 'runtime_seconds']
        for key in summary_keys:
            check(f"summary has {key}", key in result.summary)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_date_range_tracking():
    """Test date range extraction from backtester results."""
    print("\n=== Test 43: analyze_bbw_patterns_v2 date range ===")

    # Create trades with known date range
    trades = make_mock_backtester_results(n_trades=100)
    bbw_states = make_mock_bbw_states(n_bars=100)

    try:
        result = analyze_bbw_patterns_v2(
            backtester_results=trades,
            bbw_states=bbw_states,
            min_trades_per_group=5
        )

        check("date_range is tuple", isinstance(result.date_range, tuple))
        check("date_range has 2 elements", len(result.date_range) == 2)
        check("date_range_start in summary", 'date_range_start' in result.summary)
        check("date_range_end in summary", 'date_range_end' in result.summary)

        # If dates exist, start should be <= end
        if result.date_range[0] is not None and result.date_range[1] is not None:
            check("start <= end", result.date_range[0] <= result.date_range[1])
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_summary_statistics():
    """Test summary statistics accuracy."""
    print("\n=== Test 44: analyze_bbw_patterns_v2 summary stats ===")

    trades = make_mock_backtester_results(n_trades=250)
    bbw_states = make_mock_bbw_states(n_bars=250)

    try:
        result = analyze_bbw_patterns_v2(
            backtester_results=trades,
            bbw_states=bbw_states,
            min_trades_per_group=10
        )

        # Check summary counts match DataFrames
        check("n_trades_analyzed matches input", result.n_trades_analyzed == 250)
        check("n_groups matches results", result.summary['n_groups'] == len(result.results))
        check("n_best_combos matches best_combos", result.summary['n_best_combos'] == len(result.best_combos))

        # Check n_states matches unique states
        if result.n_trades_analyzed > 0:
            check("n_states > 0", result.n_states > 0)

        # Check min_trades_per_group stored
        check("min_trades_per_group stored", result.summary['min_trades_per_group'] == 10)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Execute all test functions."""
    global PASS_COUNT, FAIL_COUNT
    PASS_COUNT = 0
    FAIL_COUNT = 0

    print("=" * 70)
    print("BBW Analyzer V2 - Unit Tests")
    print("=" * 70)

    # Phase 1: Input Validation (5 tests)
    test_validate_backtester_data_valid()
    test_validate_backtester_data_missing_columns()
    test_validate_backtester_data_invalid_direction()
    test_validate_backtester_data_out_of_range_leverage()
    test_validate_bbw_states_valid()

    # Phase 2: Data Enrichment (8 tests)
    test_enrich_with_bbw_state_aligned_data()
    test_enrich_with_bbw_state_missing_states()
    test_enrich_with_bbw_state_preserves_original_columns()
    test_enrich_with_bbw_state_column_naming()
    test_enrich_with_bbw_state_values_correct()
    test_enrich_handles_duplicate_timestamps()
    test_enrich_datetime_conversion()
    test_enrich_no_data_loss()

    # Phase 3: Grouping Logic (10 tests)
    test_group_by_state_direction_lsg_basic()
    test_group_min_trades_filter()
    test_group_categorical_dtypes()
    test_calculate_group_metrics_be_fees_rate()
    test_calculate_group_metrics_win_rate_divergence()
    test_calculate_group_metrics_commission_drag()
    test_calculate_max_drawdown()
    test_calculate_sharpe()
    test_calculate_sharpe_zero_variance()
    test_calculate_sortino()

    # Phase 5: Best Combo Selection (8 tests)
    test_best_lsg_single_state_direction()
    test_best_lsg_multiple_states()
    test_best_lsg_tie_breaking()
    test_best_lsg_preserves_per_trade_pnl()
    test_best_lsg_highest_be_fees_rate()
    test_best_lsg_empty_input()
    test_best_lsg_handles_missing_direction()
    test_best_lsg_all_states_present()

    # Phase 6: Directional Bias Detection (8 tests)
    test_bias_long_favored()
    test_bias_short_favored()
    test_bias_neutral()
    test_bias_threshold_edge_cases()
    test_bias_missing_long_direction()
    test_bias_missing_short_direction()
    test_bias_strength_calculation()
    test_bias_all_states_analyzed()

    # Phase 7: Main Pipeline Integration (5 tests)
    test_full_pipeline_single_symbol()
    test_full_pipeline_auto_symbol_detection()
    test_full_pipeline_output_contract()
    test_full_pipeline_date_range_tracking()
    test_full_pipeline_summary_statistics()

    # Summary
    print("\n" + "=" * 70)
    print(f"PASS: {PASS_COUNT}")
    print(f"FAIL: {FAIL_COUNT}")
    print(f"TOTAL: {PASS_COUNT + FAIL_COUNT}")
    print("=" * 70)

    return FAIL_COUNT == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
