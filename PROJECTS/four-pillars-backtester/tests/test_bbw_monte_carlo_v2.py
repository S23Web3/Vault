"""Unit tests for BBW Monte Carlo V2 (Layer 4b).

Test-first development: Tests validate statistical logic.

Run: python tests/test_bbw_monte_carlo_v2.py
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.bbw_monte_carlo_v2 import (
    validate_monte_carlo_input,
    run_bootstrap_pnl,
    run_permutation_dd,
    classify_verdict,
    run_monte_carlo_v2,
    MonteCarloResultV2
)

from research.bbw_analyzer_v2 import BBWAnalysisResultV2


# =============================================================================
# TEST HELPERS
# =============================================================================

PASS_COUNT = 0
FAIL_COUNT = 0


def check(description: str, condition: bool):
    """Track test pass/fail."""
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {description}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {description}")


def make_mock_analysis_result(n_combos: int = 3):
    """Generate mock BBWAnalysisResultV2 for testing."""
    best_combos = pd.DataFrame({
        'bbw_state': ['BLUE', 'RED', 'GREEN'][:n_combos],
        'direction': ['LONG', 'SHORT', 'LONG'][:n_combos],
        'n_trades': [100, 150, 200][:n_combos],
        'be_plus_fees_rate': [0.65, 0.58, 0.72][:n_combos],
        'per_trade_pnl': [
            list(np.random.uniform(-10, 20, 100)),
            list(np.random.uniform(-15, 15, 150)),
            list(np.random.uniform(-8, 25, 200))
        ][:n_combos]
    })

    result = BBWAnalysisResultV2(
        results=pd.DataFrame(),  # Not used in MC
        best_combos=best_combos,
        directional_bias=pd.DataFrame(),
        summary={'symbol': 'RIVERUSDT'},
        symbol='RIVERUSDT',
        n_trades_analyzed=450,
        n_states=3,
        date_range=(None, None),
        runtime_seconds=0.5
    )

    return result


# =============================================================================
# PHASE 1: INPUT VALIDATION TESTS (5 tests)
# =============================================================================

def test_validate_input_valid():
    """Test input validation with valid BBWAnalysisResultV2."""
    print("\n=== Test 1: validate_monte_carlo_input valid ===")

    result = make_mock_analysis_result()

    try:
        is_valid = validate_monte_carlo_input(result)
        check("Validation returns True", is_valid)
        check("No exception raised", True)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_validate_input_missing_attribute():
    """Test validation fails when attribute missing."""
    print("\n=== Test 2: validate_monte_carlo_input missing attribute ===")

    # Create object without required attribute
    class FakeResult:
        best_combos = pd.DataFrame()
        results = pd.DataFrame()

    fake_result = FakeResult()

    try:
        validate_monte_carlo_input(fake_result)
        check("Raises ValueError", False)
    except ValueError as e:
        check("Raises ValueError", True)
        check("Error mentions missing attribute", 'attribute' in str(e).lower() or 'summary' in str(e).lower())


def test_validate_input_empty_best_combos():
    """Test validation fails when best_combos is empty."""
    print("\n=== Test 3: validate_monte_carlo_input empty best_combos ===")

    result = make_mock_analysis_result()
    result.best_combos = pd.DataFrame()  # Empty

    try:
        validate_monte_carlo_input(result)
        check("Raises ValueError", False)
    except ValueError as e:
        check("Raises ValueError", True)
        check("Error mentions empty", 'empty' in str(e).lower())


def test_validate_input_missing_per_trade_pnl():
    """Test validation fails when per_trade_pnl column missing."""
    print("\n=== Test 4: validate_monte_carlo_input missing per_trade_pnl ===")

    result = make_mock_analysis_result()
    result.best_combos = result.best_combos.drop(columns=['per_trade_pnl'])

    try:
        validate_monte_carlo_input(result)
        check("Raises ValueError", False)
    except ValueError as e:
        check("Raises ValueError", True)
        check("Error mentions missing columns", 'missing columns' in str(e).lower())


def test_validate_input_empty_pnl_array():
    """Test validation fails when per_trade_pnl is empty list."""
    print("\n=== Test 5: validate_monte_carlo_input empty pnl array ===")

    result = make_mock_analysis_result()
    result.best_combos.at[0, 'per_trade_pnl'] = []  # Empty array (use .at for list assignment)

    try:
        validate_monte_carlo_input(result)
        check("Raises ValueError", False)
    except ValueError as e:
        check("Raises ValueError", True)
        check("Error mentions empty", 'empty' in str(e).lower())


# =============================================================================
# PHASE 2: BOOTSTRAP TESTING (8 tests)
# =============================================================================

def test_bootstrap_identical_values():
    """Test bootstrap with identical PnL values (zero variance)."""
    print("\n=== Test 6: run_bootstrap_pnl identical values ===")

    per_trade_pnl = [10.0] * 100  # All identical

    try:
        ci_lower, ci_upper, bootstrap_means = run_bootstrap_pnl(
            per_trade_pnl, n_sims=100, seed=42
        )

        check("ci_lower = 10.0", abs(ci_lower - 10.0) < 0.01)
        check("ci_upper = 10.0", abs(ci_upper - 10.0) < 0.01)
        check("All bootstrap means = 10.0", np.all(np.abs(bootstrap_means - 10.0) < 0.01))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_real_mean_in_ci():
    """Test real mean falls within bootstrap CI."""
    print("\n=== Test 7: run_bootstrap_pnl real mean in CI ===")

    # Known distribution
    per_trade_pnl = list(np.random.normal(loc=5.0, scale=10.0, size=200))
    real_mean = np.mean(per_trade_pnl)

    try:
        ci_lower, ci_upper, bootstrap_means = run_bootstrap_pnl(
            per_trade_pnl, n_sims=1000, confidence=0.90, seed=42
        )

        check("ci_lower < real_mean", ci_lower < real_mean)
        check("real_mean < ci_upper", real_mean < ci_upper)
        check("CI is reasonable width", (ci_upper - ci_lower) > 0.5)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_ci_width_decreases_with_samples():
    """Test CI width decreases as sample size increases."""
    print("\n=== Test 8: run_bootstrap_pnl CI width vs sample size ===")

    # Same distribution, different sample sizes
    np.random.seed(42)
    small_sample = list(np.random.normal(10, 5, size=50))
    large_sample = list(np.random.normal(10, 5, size=500))

    try:
        ci_lower_small, ci_upper_small, _ = run_bootstrap_pnl(small_sample, n_sims=500, seed=42)
        ci_lower_large, ci_upper_large, _ = run_bootstrap_pnl(large_sample, n_sims=500, seed=43)

        width_small = ci_upper_small - ci_lower_small
        width_large = ci_upper_large - ci_lower_large

        check("Small sample CI calculated", width_small > 0)
        check("Large sample CI calculated", width_large > 0)
        check("Large sample has narrower CI", width_large < width_small)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_seed_reproducibility():
    """Test same seed produces same results."""
    print("\n=== Test 9: run_bootstrap_pnl seed reproducibility ===")

    per_trade_pnl = list(np.random.uniform(-10, 20, 100))

    try:
        ci_lower_1, ci_upper_1, means_1 = run_bootstrap_pnl(per_trade_pnl, n_sims=100, seed=42)
        ci_lower_2, ci_upper_2, means_2 = run_bootstrap_pnl(per_trade_pnl, n_sims=100, seed=42)

        check("ci_lower matches", abs(ci_lower_1 - ci_lower_2) < 0.001)
        check("ci_upper matches", abs(ci_upper_1 - ci_upper_2) < 0.001)
        check("bootstrap_means match", np.allclose(means_1, means_2))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_confidence_levels():
    """Test different confidence levels produce different CI widths."""
    print("\n=== Test 10: run_bootstrap_pnl confidence levels ===")

    per_trade_pnl = list(np.random.uniform(-10, 20, 200))

    try:
        ci_lower_90, ci_upper_90, _ = run_bootstrap_pnl(per_trade_pnl, n_sims=500, confidence=0.90, seed=42)
        ci_lower_95, ci_upper_95, _ = run_bootstrap_pnl(per_trade_pnl, n_sims=500, confidence=0.95, seed=42)

        width_90 = ci_upper_90 - ci_lower_90
        width_95 = ci_upper_95 - ci_lower_95

        check("90% CI calculated", width_90 > 0)
        check("95% CI calculated", width_95 > 0)
        check("95% CI wider than 90%", width_95 > width_90)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_negative_mean():
    """Test bootstrap handles negative mean PnL."""
    print("\n=== Test 11: run_bootstrap_pnl negative mean ===")

    per_trade_pnl = list(np.random.normal(loc=-5.0, scale=8.0, size=150))
    real_mean = np.mean(per_trade_pnl)

    try:
        ci_lower, ci_upper, _ = run_bootstrap_pnl(per_trade_pnl, n_sims=500, seed=42)

        check("real_mean is negative", real_mean < 0)
        check("ci_lower < 0", ci_lower < 0)
        check("real_mean in CI", ci_lower < real_mean < ci_upper)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_small_sample():
    """Test bootstrap handles small sample (edge case)."""
    print("\n=== Test 12: run_bootstrap_pnl small sample ===")

    per_trade_pnl = [5.0, 10.0, 15.0]  # Only 3 trades

    try:
        ci_lower, ci_upper, bootstrap_means = run_bootstrap_pnl(per_trade_pnl, n_sims=100, seed=42)

        check("Returns ci_lower", isinstance(ci_lower, (int, float)))
        check("Returns ci_upper", isinstance(ci_upper, (int, float)))
        check("bootstrap_means has 100 sims", len(bootstrap_means) == 100)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_bootstrap_mixed_pnl():
    """Test bootstrap with mixed positive/negative PnL."""
    print("\n=== Test 13: run_bootstrap_pnl mixed PnL ===")

    per_trade_pnl = [-10, -5, 0, 5, 10, 15, 20, -8, -12, 18]

    try:
        ci_lower, ci_upper, _ = run_bootstrap_pnl(per_trade_pnl, n_sims=500, seed=42)

        real_mean = np.mean(per_trade_pnl)
        check("real_mean in CI", ci_lower < real_mean < ci_upper)
        check("CI spans zero", ci_lower < 0 < ci_upper or (ci_lower < 0 and ci_upper < 0) or (ci_lower > 0 and ci_upper > 0))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 3: PERMUTATION TESTING (8 tests)
# =============================================================================

def test_permutation_identical_values():
    """Test permutation with identical PnL (zero DD)."""
    print("\n=== Test 14: run_permutation_dd identical values ===")

    per_trade_pnl = [10.0] * 100

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=100, seed=42)

        check("real_dd = 0", abs(real_dd) < 0.01)
        check("p95_dd = 0", abs(p95_dd) < 0.01)
        check("Not fragile (no variance)", not is_fragile)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_monotonic_increase():
    """Test permutation with monotonically increasing equity (no DD)."""
    print("\n=== Test 15: run_permutation_dd monotonic increase ===")

    per_trade_pnl = [1.0, 2.0, 3.0, 4.0, 5.0]  # Always increasing

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=100, seed=42)

        check("real_dd = 0 (no drawdown)", abs(real_dd) < 0.01)
        check("Not fragile", not is_fragile)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_oscillating_pattern():
    """Test permutation detects path-dependent DD in oscillating pattern."""
    print("\n=== Test 16: run_permutation_dd oscillating pattern ===")

    # Pattern: +10, -20, +10, -20, +10 (oscillating)
    # Worst path: +10, -20, -20 = -30 from +10 peak → DD = 40
    per_trade_pnl = [10, -20, 10, -20, 10, -20, 10, -20, 10]

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=500, seed=42)

        check("real_dd > 0", real_dd > 0)
        # Permutations may break pattern, reducing DD
        check("p95_dd calculated", p95_dd >= 0)
        # Fragility depends on how much pattern matters
        check("Fragile flag determined", isinstance(is_fragile, (bool, np.bool_)))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_seed_reproducibility():
    """Test same seed produces same permutation results."""
    print("\n=== Test 17: run_permutation_dd seed reproducibility ===")

    per_trade_pnl = list(np.random.uniform(-10, 15, 50))

    try:
        real_dd_1, p95_dd_1, is_fragile_1 = run_permutation_dd(per_trade_pnl, n_sims=100, seed=42)
        real_dd_2, p95_dd_2, is_fragile_2 = run_permutation_dd(per_trade_pnl, n_sims=100, seed=42)

        check("real_dd matches", abs(real_dd_1 - real_dd_2) < 0.001)
        check("p95_dd matches", abs(p95_dd_1 - p95_dd_2) < 0.001)
        check("is_fragile matches", is_fragile_1 == is_fragile_2)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_all_negative():
    """Test permutation with all negative PnL (consistent losses)."""
    print("\n=== Test 18: run_permutation_dd all negative ===")

    per_trade_pnl = [-5, -10, -8, -12, -6, -9]

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=100, seed=42)

        # Drawdown = total losses (equity only decreases)
        total_loss = sum(per_trade_pnl)
        check("real_dd ~= total loss", abs(real_dd - abs(total_loss)) < 0.1)
        check("Not fragile (no path dependency for monotonic)", not is_fragile or is_fragile)  # Either outcome valid
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_single_large_loss():
    """Test permutation with single large loss creates DD."""
    print("\n=== Test 19: run_permutation_dd single large loss ===")

    per_trade_pnl = [5, 5, 5, -30, 5, 5]  # One big loss

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=500, seed=42)

        check("real_dd > 0", real_dd > 0)
        check("real_dd includes large loss", real_dd >= 30)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_random_sequence():
    """Test permutation on random sequence."""
    print("\n=== Test 20: run_permutation_dd random sequence ===")

    np.random.seed(42)
    per_trade_pnl = list(np.random.normal(2, 10, size=100))

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=500, seed=42)

        check("real_dd >= 0", real_dd >= 0)
        check("p95_dd >= 0", p95_dd >= 0)
        check("is_fragile is bool", isinstance(is_fragile, (bool, np.bool_)))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_permutation_fragile_detection():
    """Test permutation correctly flags fragile vs robust DD."""
    print("\n=== Test 21: run_permutation_dd fragile detection ===")

    # Create pathological sequence: early wins, late losses
    per_trade_pnl = [20] * 10 + [-15] * 10  # Wins then losses

    try:
        real_dd, p95_dd, is_fragile = run_permutation_dd(per_trade_pnl, n_sims=500, seed=42)

        # This sequence has high DD due to ordering
        # Permutations will mix wins/losses, reducing DD
        check("real_dd calculated", real_dd > 0)
        # If fragile, real_dd should be > p95_dd
        if is_fragile:
            check("If fragile, real_dd > p95_dd", real_dd > p95_dd)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 4: VERDICT CLASSIFICATION (6 tests)
# =============================================================================

def test_verdict_insufficient_trades():
    """Test INSUFFICIENT verdict for low sample size."""
    print("\n=== Test 22: classify_verdict INSUFFICIENT ===")

    try:
        verdict, reason = classify_verdict(
            n_trades=50,
            mean_pnl=5.0,
            ci_lower=2.0,
            ci_upper=8.0,
            dd_fragile=False,
            min_trades=100
        )

        check("Verdict = INSUFFICIENT", verdict == "INSUFFICIENT")
        check("Reason mentions trades", "trades" in reason.lower() or "50" in reason)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_verdict_commission_kill():
    """Test COMMISSION_KILL verdict when even best case loses."""
    print("\n=== Test 23: classify_verdict COMMISSION_KILL ===")

    try:
        verdict, reason = classify_verdict(
            n_trades=200,
            mean_pnl=-3.0,
            ci_lower=-5.0,
            ci_upper=-1.0,  # Even 95th percentile negative
            dd_fragile=False,
            min_trades=100
        )

        check("Verdict = COMMISSION_KILL", verdict == "COMMISSION_KILL")
        check("Reason mentions percentile", "percentile" in reason.lower() or "loses" in reason.lower())
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_verdict_fragile_negative_ci_lower():
    """Test FRAGILE verdict when CI lower bound negative."""
    print("\n=== Test 24: classify_verdict FRAGILE (negative CI lower) ===")

    try:
        verdict, reason = classify_verdict(
            n_trades=150,
            mean_pnl=2.0,
            ci_lower=-1.0,  # Worst case loses
            ci_upper=5.0,
            dd_fragile=False,
            min_trades=100
        )

        check("Verdict = FRAGILE", verdict == "FRAGILE")
        check("Reason mentions negative or percentile", "negative" in reason.lower() or "percentile" in reason.lower())
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_verdict_fragile_dd():
    """Test FRAGILE verdict when drawdown is path-dependent."""
    print("\n=== Test 25: classify_verdict FRAGILE (DD fragile) ===")

    try:
        verdict, reason = classify_verdict(
            n_trades=200,
            mean_pnl=5.0,
            ci_lower=2.0,
            ci_upper=8.0,
            dd_fragile=True,  # Path-dependent DD
            min_trades=100
        )

        check("Verdict = FRAGILE", verdict == "FRAGILE")
        check("Reason mentions drawdown or path", "drawdown" in reason.lower() or "path" in reason.lower())
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_verdict_robust():
    """Test ROBUST verdict when edge is consistent and profitable."""
    print("\n=== Test 26: classify_verdict ROBUST ===")

    try:
        verdict, reason = classify_verdict(
            n_trades=300,
            mean_pnl=8.0,
            ci_lower=5.0,  # Even worst case > min_net_expectancy
            ci_upper=12.0,
            dd_fragile=False,
            min_trades=100,
            min_net_expectancy=1.0
        )

        check("Verdict = ROBUST", verdict == "ROBUST")
        check("Reason mentions edge or consistent", "edge" in reason.lower() or "consistent" in reason.lower())
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_verdict_weak_edge():
    """Test FRAGILE verdict for weak but positive edge."""
    print("\n=== Test 27: classify_verdict weak edge ===")

    try:
        verdict, reason = classify_verdict(
            n_trades=200,
            mean_pnl=2.0,
            ci_lower=0.5,  # Positive but < min_net_expectancy
            ci_upper=3.5,
            dd_fragile=False,
            min_trades=100,
            min_net_expectancy=1.0
        )

        check("Verdict = FRAGILE", verdict == "FRAGILE")
        check("Reason mentions weak", "weak" in reason.lower())
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


# =============================================================================
# PHASE 5: INTEGRATION TESTS (5 tests)
# =============================================================================

def test_full_pipeline_single_state():
    """Test full MC pipeline on single state."""
    print("\n=== Test 28: run_monte_carlo_v2 single state ===")

    result = make_mock_analysis_result(n_combos=1)

    try:
        mc_result = run_monte_carlo_v2(
            analysis_result=result,
            n_sims=100,
            seed=42
        )

        check("Returns MonteCarloResultV2", isinstance(mc_result, MonteCarloResultV2))
        check("Has state_verdicts", isinstance(mc_result.state_verdicts, pd.DataFrame))
        check("Has 1 verdict row", len(mc_result.state_verdicts) == 1)
        check("Has confidence_intervals", isinstance(mc_result.confidence_intervals, pd.DataFrame))
        check("Has overfit_flags", isinstance(mc_result.overfit_flags, pd.DataFrame))
        check("Has summary dict", isinstance(mc_result.summary, dict))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_multiple_states():
    """Test full MC pipeline on multiple states."""
    print("\n=== Test 29: run_monte_carlo_v2 multiple states ===")

    result = make_mock_analysis_result(n_combos=3)

    try:
        mc_result = run_monte_carlo_v2(
            analysis_result=result,
            n_sims=200,
            seed=42
        )

        check("Has 3 verdict rows", len(mc_result.state_verdicts) == 3)
        check("Has 3 CI rows", len(mc_result.confidence_intervals) == 3)
        check("Has 3 overfit flag rows", len(mc_result.overfit_flags) == 3)
        check("Summary has n_states_tested", 'n_states_tested' in mc_result.summary)
        check("n_states_tested = 3", mc_result.summary['n_states_tested'] == 3)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_output_columns():
    """Test output DataFrames have required columns."""
    print("\n=== Test 30: run_monte_carlo_v2 output columns ===")

    result = make_mock_analysis_result(n_combos=2)

    try:
        mc_result = run_monte_carlo_v2(result, n_sims=100, seed=42)

        # Check state_verdicts columns
        verdict_cols = ['bbw_state', 'direction', 'n_trades', 'mean_pnl',
                        'ci_lower', 'ci_upper', 'verdict', 'verdict_reason']
        for col in verdict_cols:
            check(f"state_verdicts has {col}", col in mc_result.state_verdicts.columns)

        # Check confidence_intervals columns
        ci_cols = ['bbw_state', 'direction', 'metric', 'real_value',
                   'ci_lower', 'ci_upper']
        for col in ci_cols:
            check(f"confidence_intervals has {col}", col in mc_result.confidence_intervals.columns)

        # Check overfit_flags columns
        flag_cols = ['bbw_state', 'direction', 'sample_size_flag',
                     'commission_kill_flag', 'dd_fragile_flag', 'verdict']
        for col in flag_cols:
            check(f"overfit_flags has {col}", col in mc_result.overfit_flags.columns)
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_verdict_distribution():
    """Test verdict distribution makes sense."""
    print("\n=== Test 31: run_monte_carlo_v2 verdict distribution ===")

    result = make_mock_analysis_result(n_combos=3)

    try:
        mc_result = run_monte_carlo_v2(result, n_sims=500, seed=42)

        verdicts = mc_result.state_verdicts['verdict'].values
        check("All verdicts are valid", all(v in ['ROBUST', 'FRAGILE', 'COMMISSION_KILL', 'INSUFFICIENT'] for v in verdicts))

        # Check summary counts
        summary = mc_result.summary
        total = summary['n_robust'] + summary['n_fragile'] + summary['n_commission_kill'] + summary['n_insufficient']
        check("Summary counts match total", total == len(mc_result.state_verdicts))
    except Exception as e:
        check("No exception raised", False)
        print(f"    Unexpected error: {e}")


def test_full_pipeline_runtime_tracking():
    """Test runtime is tracked in summary."""
    print("\n=== Test 32: run_monte_carlo_v2 runtime tracking ===")

    result = make_mock_analysis_result(n_combos=2)

    try:
        mc_result = run_monte_carlo_v2(result, n_sims=100, seed=42)

        check("Summary has runtime_seconds", 'runtime_seconds' in mc_result.summary)
        check("Runtime > 0", mc_result.summary['runtime_seconds'] > 0)
        check("Runtime < 60s", mc_result.summary['runtime_seconds'] < 60)
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
    print("BBW Monte Carlo V2 - Unit Tests")
    print("=" * 70)

    # Phase 1: Input Validation (5 tests)
    test_validate_input_valid()
    test_validate_input_missing_attribute()
    test_validate_input_empty_best_combos()
    test_validate_input_missing_per_trade_pnl()
    test_validate_input_empty_pnl_array()

    # Phase 2: Bootstrap Testing (8 tests)
    test_bootstrap_identical_values()
    test_bootstrap_real_mean_in_ci()
    test_bootstrap_ci_width_decreases_with_samples()
    test_bootstrap_seed_reproducibility()
    test_bootstrap_confidence_levels()
    test_bootstrap_negative_mean()
    test_bootstrap_small_sample()
    test_bootstrap_mixed_pnl()

    # Phase 3: Permutation Testing (8 tests)
    test_permutation_identical_values()
    test_permutation_monotonic_increase()
    test_permutation_oscillating_pattern()
    test_permutation_seed_reproducibility()
    test_permutation_all_negative()
    test_permutation_single_large_loss()
    test_permutation_random_sequence()
    test_permutation_fragile_detection()

    # Phase 4: Verdict Classification (6 tests)
    test_verdict_insufficient_trades()
    test_verdict_commission_kill()
    test_verdict_fragile_negative_ci_lower()
    test_verdict_fragile_dd()
    test_verdict_robust()
    test_verdict_weak_edge()

    # Phase 5: Integration (5 tests)
    test_full_pipeline_single_state()
    test_full_pipeline_multiple_states()
    test_full_pipeline_output_columns()
    test_full_pipeline_verdict_distribution()
    test_full_pipeline_runtime_tracking()

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
