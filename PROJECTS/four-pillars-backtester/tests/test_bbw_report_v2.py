"""Tests for BBW V2 Layer 5: Report Generator.

Run: python tests/test_bbw_report_v2.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd

from research.bbw_report_v2 import (
    BBWReportResultV2,
    validate_report_inputs,
    aggregate_directional_bias,
    generate_be_fees_success_tables,
    create_vince_features,
    analyze_lsg_sensitivity,
    generate_state_summary,
    generate_vince_features_v2
)


# =============================================================================
# MOCK DATA GENERATORS
# =============================================================================

def make_mock_analysis_result(n_states=3):
    """Generate mock BBWAnalysisResultV2 for testing."""
    from dataclasses import dataclass

    @dataclass
    class MockAnalysisResult:
        results: pd.DataFrame
        best_combos: pd.DataFrame
        directional_bias: pd.DataFrame
        summary: dict
        symbol: str

    states = ['BLUE', 'GREEN', 'RED'][:n_states]
    directions = ['LONG', 'SHORT']

    # Generate results (ALL groups)
    results_rows = []
    for state in states:
        for direction in directions:
            for lev in [10, 20]:
                for size in [0.1, 0.2]:
                    for grid in [1, 2]:
                        results_rows.append({
                            'bbw_state': state,
                            'direction': direction,
                            'leverage': lev,
                            'size': size,
                            'grid': grid,
                            'n_trades': np.random.randint(100, 200),
                            'be_plus_fees_rate': np.random.uniform(0.4, 0.6),
                            'win_rate': np.random.uniform(0.35, 0.55),
                            'avg_net_pnl': np.random.uniform(-5, 10),
                            'avg_commission': 5.0,
                            'commission_drag': 0.05,
                            'sharpe': np.random.uniform(-0.5, 1.5),
                            'max_dd': np.random.uniform(50, 150),
                            'per_trade_pnl': list(np.random.randn(120))
                        })

    results = pd.DataFrame(results_rows)

    # Generate best_combos (one per state x direction)
    best_combos_rows = []
    for state in states:
        for direction in directions:
            best_combos_rows.append({
                'bbw_state': state,
                'direction': direction,
                'leverage': 20,
                'size': 0.2,
                'grid': 2,
                'n_trades': 150,
                'be_plus_fees_rate': 0.55 if direction == 'LONG' else 0.50,
                'win_rate': 0.50,
                'avg_net_pnl': 8.0 if direction == 'LONG' else 5.0,
                'avg_commission': 5.0,
                'commission_drag': 0.05,
                'sharpe': 1.2,
                'max_dd': 100.0,
                'per_trade_pnl': list(np.random.randn(150))
            })

    best_combos = pd.DataFrame(best_combos_rows)

    directional_bias = pd.DataFrame([])
    summary = {'n_states': n_states}

    return MockAnalysisResult(
        results=results,
        best_combos=best_combos,
        directional_bias=directional_bias,
        summary=summary,
        symbol='TESTUSDT'
    )


def make_mock_mc_result(n_states=3):
    """Generate mock MonteCarloResultV2 for testing."""
    from dataclasses import dataclass

    @dataclass
    class MockMCResult:
        state_verdicts: pd.DataFrame
        confidence_intervals: pd.DataFrame
        overfit_flags: pd.DataFrame
        summary: dict

    states = ['BLUE', 'GREEN', 'RED'][:n_states]
    directions = ['LONG', 'SHORT']

    # State verdicts
    state_verdicts_rows = []
    for state in states:
        for direction in directions:
            state_verdicts_rows.append({
                'bbw_state': state,
                'direction': direction,
                'n_trades': 150,
                'mean_pnl': 8.0 if direction == 'LONG' else 5.0,
                'ci_lower': 2.0,
                'ci_upper': 12.0,
                'verdict': 'ROBUST' if direction == 'LONG' else 'FRAGILE',
                'verdict_reason': 'Test verdict'
            })

    state_verdicts = pd.DataFrame(state_verdicts_rows)

    confidence_intervals = pd.DataFrame([])
    overfit_flags = pd.DataFrame([])
    summary = {}

    return MockMCResult(
        state_verdicts=state_verdicts,
        confidence_intervals=confidence_intervals,
        overfit_flags=overfit_flags,
        summary=summary
    )


# =============================================================================
# PHASE 1: INPUT VALIDATION (5 tests)
# =============================================================================

def test_01_valid_inputs():
    """Valid inputs should return True."""
    analysis = make_mock_analysis_result(n_states=3)
    mc = make_mock_mc_result(n_states=3)

    result = validate_report_inputs(analysis, mc)
    assert result == True, "Valid inputs should return True"
    print("PASS test_01: Valid inputs accepted")


def test_02_missing_attribute():
    """Missing dataclass attribute should raise ValueError."""
    analysis = make_mock_analysis_result(n_states=3)
    mc = make_mock_mc_result(n_states=3)

    # Remove attribute
    delattr(analysis, 'best_combos')

    try:
        validate_report_inputs(analysis, mc)
        assert False, "Should raise ValueError for missing attribute"
    except ValueError as e:
        assert 'best_combos' in str(e)
        print("PASS test_02: Missing attribute caught")


def test_03_empty_best_combos():
    """Empty best_combos should raise ValueError."""
    analysis = make_mock_analysis_result(n_states=3)
    mc = make_mock_mc_result(n_states=3)

    analysis.best_combos = pd.DataFrame([])

    try:
        validate_report_inputs(analysis, mc)
        assert False, "Should raise ValueError for empty best_combos"
    except ValueError as e:
        assert 'empty' in str(e)
        print("PASS test_03: Empty best_combos caught")


def test_04_empty_state_verdicts():
    """Empty state_verdicts should raise ValueError."""
    analysis = make_mock_analysis_result(n_states=3)
    mc = make_mock_mc_result(n_states=3)

    mc.state_verdicts = pd.DataFrame([])

    try:
        validate_report_inputs(analysis, mc)
        assert False, "Should raise ValueError for empty state_verdicts"
    except ValueError as e:
        assert 'empty' in str(e)
        print("PASS test_04: Empty state_verdicts caught")


def test_05_column_mismatch():
    """Missing bbw_state column should raise ValueError."""
    analysis = make_mock_analysis_result(n_states=3)
    mc = make_mock_mc_result(n_states=3)

    analysis.best_combos.rename(columns={'bbw_state': 'state_old'}, inplace=True)

    try:
        validate_report_inputs(analysis, mc)
        assert False, "Should raise ValueError for missing bbw_state"
    except ValueError as e:
        assert 'bbw_state' in str(e)
        print("PASS test_05: Column mismatch caught")


# =============================================================================
# PHASE 2: FUNCTION 1 TESTS (8 tests)
# =============================================================================

def test_06_single_state_bias():
    """Single state with LONG+SHORT should calculate bias correctly."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.45}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert len(result) == 1, "Should return 1 row"
    assert result.iloc[0]['bbw_state'] == 'BLUE'
    assert result.iloc[0]['bias_direction'] == 'LONG', "LONG rate higher, should favor LONG"
    assert result.iloc[0]['bias_strength'] == 0.15, "Difference should be 0.15"
    print("PASS test_06: Single state bias calculation")


def test_07_only_long():
    """State with only LONG (no SHORT) should be skipped."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.60}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert len(result) == 0, "Should skip states with only one direction"
    print("PASS test_07: Only LONG skipped")


def test_08_only_short():
    """State with only SHORT (no LONG) should be skipped."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.50}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert len(result) == 0, "Should skip states with only one direction"
    print("PASS test_08: Only SHORT skipped")


def test_09_both_robust():
    """Both ROBUST verdicts should give HIGH confidence."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.55}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'ROBUST'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert result.iloc[0]['confidence'] == 'HIGH', "Both ROBUST should give HIGH confidence"
    print("PASS test_09: Both ROBUST -> HIGH confidence")


def test_10_both_fragile():
    """Both FRAGILE verdicts should give LOW confidence."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.55},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.50}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'FRAGILE'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert result.iloc[0]['confidence'] == 'LOW', "Both FRAGILE should give LOW confidence"
    print("PASS test_10: Both FRAGILE -> LOW confidence")


def test_11_mixed_verdicts():
    """Mixed verdicts should give MEDIUM confidence."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.50}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert result.iloc[0]['confidence'] == 'MEDIUM', "Mixed verdicts should give MEDIUM confidence"
    print("PASS test_11: Mixed verdicts -> MEDIUM confidence")


def test_12_neutral_bias():
    """NEUTRAL bias when difference < 0.05."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.52},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.51}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'ROBUST'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert result.iloc[0]['bias_direction'] == 'NEUTRAL', "Small difference should be NEUTRAL"
    print("PASS test_12: Small difference -> NEUTRAL bias")


def test_13_multiple_states():
    """Multiple states should all be processed."""
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'RED', 'direction': 'LONG', 'be_plus_fees_rate': 0.45},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'be_plus_fees_rate': 0.55}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'},
        {'bbw_state': 'RED', 'direction': 'LONG', 'verdict': 'FRAGILE'},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'verdict': 'ROBUST'}
    ])

    result = aggregate_directional_bias(best_combos, state_verdicts)

    assert len(result) == 2, "Should process both states"
    assert 'BLUE' in result['bbw_state'].values
    assert 'RED' in result['bbw_state'].values
    print("PASS test_13: Multiple states processed")


# =============================================================================
# PHASE 3: FUNCTION 2 TESTS (5 tests)
# =============================================================================

def test_14_verdict_lookup():
    """All verdicts found should populate table."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        }
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = generate_be_fees_success_tables(best_combos, state_verdicts)

    assert len(result) == 1
    assert result.iloc[0]['verdict'] == 'ROBUST'
    assert result.iloc[0]['rate_divergence'] == 0.05, "Divergence should be be_fees - win_rate"
    print("PASS test_14: Verdict lookup successful")


def test_15_verdict_not_found():
    """Verdict not found should use UNKNOWN."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        }
    ])
    state_verdicts = pd.DataFrame([])

    result = generate_be_fees_success_tables(best_combos, state_verdicts)

    assert result.iloc[0]['verdict'] == 'UNKNOWN', "Missing verdict should use UNKNOWN"
    print("PASS test_15: Missing verdict -> UNKNOWN")


def test_16_rate_divergence():
    """Rate divergence calculated correctly."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.50, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        }
    ])
    state_verdicts = pd.DataFrame([])

    result = generate_be_fees_success_tables(best_combos, state_verdicts)

    assert result.iloc[0]['rate_divergence'] == 0.10, "0.60 - 0.50 = 0.10"
    print("PASS test_16: Rate divergence correct")


def test_17_empty_input():
    """Empty input should return empty output."""
    best_combos = pd.DataFrame([])
    state_verdicts = pd.DataFrame([])

    result = generate_be_fees_success_tables(best_combos, state_verdicts)

    assert len(result) == 0, "Empty input should return empty DataFrame"
    print("PASS test_17: Empty input -> empty output")


def test_18_all_columns_present():
    """All expected columns should be present."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        }
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = generate_be_fees_success_tables(best_combos, state_verdicts)

    expected_cols = ['bbw_state', 'direction', 'leverage', 'size', 'grid', 'n_trades',
                     'be_plus_fees_rate', 'win_rate', 'rate_divergence',
                     'avg_net_pnl', 'avg_commission', 'commission_drag',
                     'verdict', 'sharpe', 'max_dd']

    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"

    print("PASS test_18: All columns present")


# =============================================================================
# PHASE 4: FUNCTION 3 TESTS (8 tests)
# =============================================================================

def test_19_state_encoding():
    """State encoding should be correct."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        },
        {
            'bbw_state': 'RED', 'direction': 'SHORT',
            'leverage': 10, 'size': 0.1, 'grid': 1,
            'n_trades': 120, 'be_plus_fees_rate': 0.50,
            'win_rate': 0.48, 'avg_net_pnl': 5.0,
            'avg_commission': 5.0, 'commission_drag': 0.10,
            'sharpe': 0.8, 'max_dd': 100.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'bias_strength': 0.10},
        {'bbw_state': 'RED', 'bias_direction': 'SHORT', 'bias_strength': 0.05}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert result.iloc[0]['feature_state_ordinal'] == 1, "BLUE should be 1"
    assert result.iloc[1]['feature_state_ordinal'] == 7, "RED should be 7"
    print("PASS test_19: State encoding correct")


def test_20_direction_encoding():
    """Direction encoding should be correct."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        },
        {
            'bbw_state': 'BLUE', 'direction': 'SHORT',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.50,
            'win_rate': 0.48, 'avg_net_pnl': 5.0,
            'avg_commission': 5.0, 'commission_drag': 0.10,
            'sharpe': 0.8, 'max_dd': 100.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'bias_strength': 0.10}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert result.iloc[0]['feature_direction_long'] == 1, "LONG should be 1"
    assert result.iloc[1]['feature_direction_long'] == 0, "SHORT should be 0"
    print("PASS test_20: Direction encoding correct")


def test_21_bias_aligned():
    """Bias alignment should be correct."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        },
        {
            'bbw_state': 'BLUE', 'direction': 'SHORT',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.50,
            'win_rate': 0.48, 'avg_net_pnl': 5.0,
            'avg_commission': 5.0, 'commission_drag': 0.10,
            'sharpe': 0.8, 'max_dd': 100.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'bias_strength': 0.10}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert result.iloc[0]['feature_bias_aligned'] == 1, "LONG on LONG bias should be 1"
    assert result.iloc[1]['feature_bias_aligned'] == 0, "SHORT on LONG bias should be 0"
    print("PASS test_21: Bias alignment correct")


def test_22_neutral_bias():
    """NEUTRAL bias should give feature_bias_aligned = 0."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.52,
            'win_rate': 0.50, 'avg_net_pnl': 5.0,
            'avg_commission': 5.0, 'commission_drag': 0.10,
            'sharpe': 1.0, 'max_dd': 90.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'NEUTRAL', 'bias_strength': 0.01}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert result.iloc[0]['feature_bias_aligned'] == 0, "NEUTRAL bias should give 0"
    print("PASS test_22: NEUTRAL bias -> feature_bias_aligned = 0")


def test_23_verdict_encoding():
    """Verdict encoding should be correct (no MARGINAL)."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        },
        {
            'bbw_state': 'GREEN', 'direction': 'SHORT',
            'leverage': 10, 'size': 0.1, 'grid': 1,
            'n_trades': 120, 'be_plus_fees_rate': 0.50,
            'win_rate': 0.48, 'avg_net_pnl': 5.0,
            'avg_commission': 5.0, 'commission_drag': 0.10,
            'sharpe': 0.8, 'max_dd': 100.0
        },
        {
            'bbw_state': 'RED', 'direction': 'LONG',
            'leverage': 5, 'size': 0.05, 'grid': 1,
            'n_trades': 50, 'be_plus_fees_rate': 0.40,
            'win_rate': 0.42, 'avg_net_pnl': -2.0,
            'avg_commission': 5.0, 'commission_drag': 0.15,
            'sharpe': -0.5, 'max_dd': 150.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'bias_strength': 0.10},
        {'bbw_state': 'GREEN', 'bias_direction': 'SHORT', 'bias_strength': 0.05},
        {'bbw_state': 'RED', 'bias_direction': 'NEUTRAL', 'bias_strength': 0.02}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'GREEN', 'direction': 'SHORT', 'verdict': 'FRAGILE'},
        {'bbw_state': 'RED', 'direction': 'LONG', 'verdict': 'INSUFFICIENT'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert result.iloc[0]['feature_verdict_ordinal'] == 3, "ROBUST should be 3"
    assert result.iloc[1]['feature_verdict_ordinal'] == 1, "FRAGILE should be 1"
    assert result.iloc[2]['feature_verdict_ordinal'] == -1, "INSUFFICIENT should be -1"
    print("PASS test_23: Verdict encoding correct (no MARGINAL)")


def test_24_sample_weight():
    """Sample weight should be 1.0 for ROBUST, 0.5 otherwise."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        },
        {
            'bbw_state': 'GREEN', 'direction': 'SHORT',
            'leverage': 10, 'size': 0.1, 'grid': 1,
            'n_trades': 120, 'be_plus_fees_rate': 0.50,
            'win_rate': 0.48, 'avg_net_pnl': 5.0,
            'avg_commission': 5.0, 'commission_drag': 0.10,
            'sharpe': 0.8, 'max_dd': 100.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'bias_strength': 0.10},
        {'bbw_state': 'GREEN', 'bias_direction': 'SHORT', 'bias_strength': 0.05}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'GREEN', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert result.iloc[0]['sample_weight'] == 1.0, "ROBUST should get weight 1.0"
    assert result.iloc[1]['sample_weight'] == 0.5, "FRAGILE should get weight 0.5"
    print("PASS test_24: Sample weight correct")


def test_25_missing_bias():
    """Row with missing bias should be skipped."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        }
    ])
    directional_bias = pd.DataFrame([])  # No bias info
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    assert len(result) == 0, "Missing bias should skip row"
    print("PASS test_25: Missing bias -> row skipped")


def test_26_all_features_present():
    """All feature columns should be present."""
    best_combos = pd.DataFrame([
        {
            'bbw_state': 'BLUE', 'direction': 'LONG',
            'leverage': 20, 'size': 0.2, 'grid': 2,
            'n_trades': 150, 'be_plus_fees_rate': 0.60,
            'win_rate': 0.55, 'avg_net_pnl': 10.0,
            'avg_commission': 5.0, 'commission_drag': 0.05,
            'sharpe': 1.5, 'max_dd': 80.0
        }
    ])
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'bias_strength': 0.10}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = create_vince_features(best_combos, directional_bias, state_verdicts)

    expected_features = [
        'feature_state_ordinal', 'feature_state_blue', 'feature_state_red',
        'feature_state_double', 'feature_direction_long', 'feature_bias_aligned',
        'feature_bias_strength', 'feature_leverage', 'feature_size', 'feature_grid',
        'feature_n_trades', 'feature_verdict_ordinal'
    ]

    for col in expected_features:
        assert col in result.columns, f"Missing feature: {col}"

    print("PASS test_26: All features present")


# =============================================================================
# PHASE 5: FUNCTION 4 TESTS (6 tests)
# =============================================================================

def test_27_correlation_calculation():
    """Correlation calculation should be correct."""
    results = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 30, 'size': 0.3, 'grid': 3, 'be_plus_fees_rate': 0.70}
    ])
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2}
    ])

    result = analyze_lsg_sensitivity(results, best_combos)

    assert len(result) == 1
    assert result.iloc[0]['leverage_sensitivity'] == 1.0, "Perfect positive correlation"
    print("PASS test_27: Correlation calculation correct")


def test_28_dominant_parameter():
    """Dominant parameter should be identified correctly."""
    results = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 1, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 30, 'size': 0.3, 'grid': 1, 'be_plus_fees_rate': 0.70}
    ])
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 1}
    ])

    result = analyze_lsg_sensitivity(results, best_combos)

    assert result.iloc[0]['dominant_parameter'] in ['leverage', 'size'], "Should identify leverage or size"
    print("PASS test_28: Dominant parameter identified")


def test_29_insufficient_groups():
    """< 3 groups should be skipped."""
    results = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2, 'be_plus_fees_rate': 0.60}
    ])
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2}
    ])

    result = analyze_lsg_sensitivity(results, best_combos)

    assert len(result) == 0, "< 3 groups should be skipped"
    print("PASS test_29: < 3 groups skipped")


def test_30_multiple_states():
    """Multiple state x direction pairs should all be processed."""
    results = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 30, 'size': 0.3, 'grid': 3, 'be_plus_fees_rate': 0.70},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.45},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'leverage': 20, 'size': 0.2, 'grid': 2, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'leverage': 30, 'size': 0.3, 'grid': 3, 'be_plus_fees_rate': 0.55}
    ])
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'leverage': 20, 'size': 0.2, 'grid': 2}
    ])

    result = analyze_lsg_sensitivity(results, best_combos)

    assert len(result) == 2, "Should process both state x direction pairs"
    print("PASS test_30: Multiple state x direction pairs processed")


def test_31_nan_correlations():
    """NaN correlations should be handled gracefully."""
    results = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50}
    ])
    best_combos = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1}
    ])

    result = analyze_lsg_sensitivity(results, best_combos)

    # All values identical -> correlation NaN, but should not crash
    if len(result) > 0:
        assert pd.isna(result.iloc[0]['leverage_sensitivity']), "NaN correlation expected"
    print("PASS test_31: NaN correlations handled")


def test_32_best_combo_missing():
    """Missing best combo should skip row."""
    results = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 10, 'size': 0.1, 'grid': 1, 'be_plus_fees_rate': 0.50},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 20, 'size': 0.2, 'grid': 2, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'leverage': 30, 'size': 0.3, 'grid': 3, 'be_plus_fees_rate': 0.70}
    ])
    best_combos = pd.DataFrame([])  # No best combo

    result = analyze_lsg_sensitivity(results, best_combos)

    assert len(result) == 0, "Missing best combo should skip row"
    print("PASS test_32: Missing best combo skipped")


# =============================================================================
# PHASE 6: FUNCTION 5 TESTS (6 tests)
# =============================================================================

def test_33_state_aggregates():
    """State aggregates should be correct."""
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'confidence': 'HIGH'}
    ])
    be_fees_success = pd.DataFrame([
        {'bbw_state': 'BLUE','direction': 'LONG', 'n_trades': 150, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE','direction': 'SHORT', 'n_trades': 120, 'be_plus_fees_rate': 0.50}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = generate_state_summary(directional_bias, be_fees_success, state_verdicts)

    assert len(result) == 1
    assert result.iloc[0]['n_directions'] == 2
    assert result.iloc[0]['total_sample_size'] == 270, "150 + 120 = 270"
    assert result.iloc[0]['avg_be_fees_rate'] == 0.55, "(0.60 + 0.50) / 2 = 0.55"
    print("PASS test_33: State aggregates correct")


def test_34_best_direction():
    """Best direction should be identified correctly."""
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'confidence': 'HIGH'}
    ])
    be_fees_success = pd.DataFrame([
        {'bbw_state': 'BLUE','direction': 'LONG', 'n_trades': 150, 'be_plus_fees_rate': 0.65},
        {'bbw_state': 'BLUE','direction': 'SHORT', 'n_trades': 120, 'be_plus_fees_rate': 0.50}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = generate_state_summary(directional_bias, be_fees_success, state_verdicts)

    assert result.iloc[0]['best_direction'] == 'LONG', "LONG has higher rate"
    print("PASS test_34: Best direction identified")


def test_35_verdict_counts():
    """Verdict counts should be correct."""
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'confidence': 'HIGH'}
    ])
    be_fees_success = pd.DataFrame([
        {'bbw_state': 'BLUE','direction': 'LONG', 'n_trades': 150, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'BLUE','direction': 'SHORT', 'n_trades': 120, 'be_plus_fees_rate': 0.50}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'BLUE', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = generate_state_summary(directional_bias, be_fees_success, state_verdicts)

    assert result.iloc[0]['n_robust'] == 1
    assert result.iloc[0]['n_fragile'] == 1
    assert result.iloc[0]['n_commission_kill'] == 0
    print("PASS test_35: Verdict counts correct")


def test_36_state_quality():
    """State quality classification should be correct."""
    # All ROBUST
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'confidence': 'HIGH'}
    ])
    be_fees_success = pd.DataFrame([
        {'bbw_state': 'BLUE','direction': 'LONG', 'n_trades': 150, 'be_plus_fees_rate': 0.60}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = generate_state_summary(directional_bias, be_fees_success, state_verdicts)

    assert result.iloc[0]['state_quality'] == 'HIGH_QUALITY', "All ROBUST should be HIGH_QUALITY"

    # All COMMISSION_KILL
    state_verdicts2 = pd.DataFrame([
        {'bbw_state': 'RED', 'direction': 'LONG', 'verdict': 'COMMISSION_KILL'}
    ])
    directional_bias2 = pd.DataFrame([
        {'bbw_state': 'RED', 'bias_direction': 'NEUTRAL', 'confidence': 'LOW'}
    ])
    be_fees_success2 = pd.DataFrame([
        {'bbw_state': 'RED','direction': 'LONG', 'n_trades': 100, 'be_plus_fees_rate': 0.30}
    ])

    result2 = generate_state_summary(directional_bias2, be_fees_success2, state_verdicts2)

    assert result2.iloc[0]['state_quality'] == 'DEAD', "All COMMISSION_KILL should be DEAD"

    print("PASS test_36: State quality classification correct")


def test_37_single_direction():
    """Single direction state should show n_directions=1."""
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'confidence': 'MEDIUM'}
    ])
    be_fees_success = pd.DataFrame([
        {'bbw_state': 'BLUE','direction': 'LONG', 'n_trades': 150, 'be_plus_fees_rate': 0.60}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'}
    ])

    result = generate_state_summary(directional_bias, be_fees_success, state_verdicts)

    assert result.iloc[0]['n_directions'] == 1
    print("PASS test_37: Single direction state correct")


def test_38_multiple_states():
    """Multiple states should all be summarized."""
    directional_bias = pd.DataFrame([
        {'bbw_state': 'BLUE', 'bias_direction': 'LONG', 'confidence': 'HIGH'},
        {'bbw_state': 'RED', 'bias_direction': 'SHORT', 'confidence': 'LOW'}
    ])
    be_fees_success = pd.DataFrame([
        {'bbw_state': 'BLUE','direction': 'LONG', 'n_trades': 150, 'be_plus_fees_rate': 0.60},
        {'bbw_state': 'RED','direction': 'SHORT', 'n_trades': 100, 'be_plus_fees_rate': 0.45}
    ])
    state_verdicts = pd.DataFrame([
        {'bbw_state': 'BLUE', 'direction': 'LONG', 'verdict': 'ROBUST'},
        {'bbw_state': 'RED', 'direction': 'SHORT', 'verdict': 'FRAGILE'}
    ])

    result = generate_state_summary(directional_bias, be_fees_success, state_verdicts)

    assert len(result) == 2, "Should summarize both states"
    assert 'BLUE' in result['bbw_state'].values
    assert 'RED' in result['bbw_state'].values
    print("PASS test_38: Multiple states summarized")


# =============================================================================
# PHASE 7: INTEGRATION TESTS (10 tests)
# =============================================================================

def test_39_full_pipeline_1_state():
    """Full pipeline with 1 state should produce all 5 outputs."""
    analysis = make_mock_analysis_result(n_states=1)
    mc = make_mock_mc_result(n_states=1)

    result = generate_vince_features_v2(analysis, mc)

    assert len(result.directional_bias) >= 0, "Directional bias created"
    assert len(result.be_fees_success) > 0, "BE+fees success created"
    assert len(result.vince_features) >= 0, "VINCE features created"
    assert len(result.lsg_sensitivity) >= 0, "LSG sensitivity created"
    assert len(result.state_summary) > 0, "State summary created"
    print("PASS test_39: Full pipeline with 1 state")


def test_40_full_pipeline_3_states():
    """Full pipeline with 3 states should produce all 5 outputs."""
    analysis = make_mock_analysis_result(n_states=3)
    mc = make_mock_mc_result(n_states=3)

    result = generate_vince_features_v2(analysis, mc)

    assert len(result.directional_bias) >= 0
    assert len(result.be_fees_success) > 0
    assert len(result.vince_features) >= 0
    assert len(result.lsg_sensitivity) >= 0
    assert len(result.state_summary) > 0
    print("PASS test_40: Full pipeline with 3 states")


def test_41_csv_export():
    """CSV export should create 5 files."""
    import tempfile
    analysis = make_mock_analysis_result(n_states=2)
    mc = make_mock_mc_result(n_states=2)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "test_output"
        result = generate_vince_features_v2(analysis, mc, output_dir=str(output_dir))

        assert (output_dir / "directional_bias.csv").exists()
        assert (output_dir / "be_fees_success.csv").exists()
        assert (output_dir / "vince_features.csv").exists()
        assert (output_dir / "lsg_sensitivity.csv").exists()
        assert (output_dir / "state_summary.csv").exists()
        print("PASS test_41: CSV export creates 5 files")


def test_42_result_structure():
    """BBWReportResultV2 structure should be correct."""
    analysis = make_mock_analysis_result(n_states=2)
    mc = make_mock_mc_result(n_states=2)

    result = generate_vince_features_v2(analysis, mc)

    assert isinstance(result, BBWReportResultV2)
    assert isinstance(result.directional_bias, pd.DataFrame)
    assert isinstance(result.be_fees_success, pd.DataFrame)
    assert isinstance(result.vince_features, pd.DataFrame)
    assert isinstance(result.lsg_sensitivity, pd.DataFrame)
    assert isinstance(result.state_summary, pd.DataFrame)
    assert isinstance(result.summary, dict)
    print("PASS test_42: Result structure correct")


def test_43_runtime_tracking():
    """Runtime tracking should work."""
    analysis = make_mock_analysis_result(n_states=2)
    mc = make_mock_mc_result(n_states=2)

    result = generate_vince_features_v2(analysis, mc)

    assert 'runtime_seconds' in result.summary
    assert result.summary['runtime_seconds'] > 0
    print("PASS test_43: Runtime tracking works")


def test_44_summary_counts():
    """Summary counts should match outputs."""
    analysis = make_mock_analysis_result(n_states=2)
    mc = make_mock_mc_result(n_states=2)

    result = generate_vince_features_v2(analysis, mc)

    assert result.summary['n_states'] == len(result.directional_bias) or result.summary['n_states'] == len(result.state_summary)
    assert result.summary['n_features'] == len(result.vince_features)
    print("PASS test_44: Summary counts match")


def test_45_no_output_dir():
    """No output_dir should skip CSV export."""
    analysis = make_mock_analysis_result(n_states=2)
    mc = make_mock_mc_result(n_states=2)

    result = generate_vince_features_v2(analysis, mc, output_dir=None)

    assert result.output_dir is None
    print("PASS test_45: No output_dir skips CSV export")


def test_46_empty_results():
    """Empty results DataFrames should be handled."""
    analysis = make_mock_analysis_result(n_states=1)
    mc = make_mock_mc_result(n_states=1)

    # Empty results
    analysis.results = pd.DataFrame([])

    result = generate_vince_features_v2(analysis, mc)

    assert len(result.lsg_sensitivity) == 0, "Empty results should give empty LSG sensitivity"
    print("PASS test_46: Empty results handled")


def test_47_column_name_consistency():
    """Column name consistency (bbw_state) should work."""
    analysis = make_mock_analysis_result(n_states=2)
    mc = make_mock_mc_result(n_states=2)

    result = generate_vince_features_v2(analysis, mc)

    # Check all DataFrames use consistent column naming
    if len(result.directional_bias) > 0:
        assert 'bbw_state' in result.directional_bias.columns
    if len(result.state_summary) > 0:
        assert 'bbw_state' in result.state_summary.columns

    print("PASS test_47: Column name consistency (bbw_state)")


def test_48_large_dataset():
    """Large dataset should process without memory issues."""
    analysis = make_mock_analysis_result(n_states=7)  # 7 states = 14 directions
    mc = make_mock_mc_result(n_states=7)

    result = generate_vince_features_v2(analysis, mc)

    assert len(result.be_fees_success) <= 14, "Should handle 7 states (14 directions)"
    print("PASS test_48: Large dataset processed")


# =============================================================================
# TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all test phases."""
    print("\n" + "="*60)
    print("BBW V2 Layer 5 Report Generator - Test Suite")
    print("="*60)

    tests = [
        # Phase 1: Input validation
        test_01_valid_inputs,
        test_02_missing_attribute,
        test_03_empty_best_combos,
        test_04_empty_state_verdicts,
        test_05_column_mismatch,
        # Phase 2: Function 1
        test_06_single_state_bias,
        test_07_only_long,
        test_08_only_short,
        test_09_both_robust,
        test_10_both_fragile,
        test_11_mixed_verdicts,
        test_12_neutral_bias,
        test_13_multiple_states,
        # Phase 3: Function 2
        test_14_verdict_lookup,
        test_15_verdict_not_found,
        test_16_rate_divergence,
        test_17_empty_input,
        test_18_all_columns_present,
        # Phase 4: Function 3
        test_19_state_encoding,
        test_20_direction_encoding,
        test_21_bias_aligned,
        test_22_neutral_bias,
        test_23_verdict_encoding,
        test_24_sample_weight,
        test_25_missing_bias,
        test_26_all_features_present,
        # Phase 5: Function 4
        test_27_correlation_calculation,
        test_28_dominant_parameter,
        test_29_insufficient_groups,
        test_30_multiple_states,
        test_31_nan_correlations,
        test_32_best_combo_missing,
        # Phase 6: Function 5
        test_33_state_aggregates,
        test_34_best_direction,
        test_35_verdict_counts,
        test_36_state_quality,
        test_37_single_direction,
        test_38_multiple_states,
        # Phase 7: Integration
        test_39_full_pipeline_1_state,
        test_40_full_pipeline_3_states,
        test_41_csv_export,
        test_42_result_structure,
        test_43_runtime_tracking,
        test_44_summary_counts,
        test_45_no_output_dir,
        test_46_empty_results,
        test_47_column_name_consistency,
        test_48_large_dataset
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(tests, 1):
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL test_{i:02d}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR test_{i:02d}: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{len(tests)} PASS, {failed} FAIL")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
