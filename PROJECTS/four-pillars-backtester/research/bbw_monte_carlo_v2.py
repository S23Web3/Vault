"""BBW V2 Layer 4b: Monte Carlo Validation - Statistical validation of backtester results.

Validates BBW Analyzer V2 results using bootstrap and permutation testing.
Classifies edges as ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT.

Critical Architecture:
- Input: BBWAnalysisResultV2 (real backtester results from Layer 4)
- Method: Bootstrap (CI) + Permutation (DD robustness)
- Output: Verdicts per (state, direction) with confidence metrics
- Purpose: Statistical validation before VINCE training

Run: Imported by scripts, not run directly
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class MonteCarloResultV2:
    """Output container for Monte Carlo validation of BBW Analyzer results.

    Attributes:
        state_verdicts: Verdict summary per (state, direction)
        confidence_intervals: Bootstrap CI for PnL metrics
        overfit_flags: Detailed overfit detection flags
        summary: Overall statistics dictionary
    """
    state_verdicts: pd.DataFrame
    confidence_intervals: pd.DataFrame
    overfit_flags: pd.DataFrame
    summary: dict


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_monte_carlo_input(analysis_result) -> bool:
    """Validate BBWAnalysisResultV2 has required structure for MC testing.

    Args:
        analysis_result: BBWAnalysisResultV2 from Layer 4

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails with specific reason
    """
    # Check it's a BBWAnalysisResultV2 object
    required_attrs = ['best_combos', 'results', 'summary', 'symbol']
    for attr in required_attrs:
        if not hasattr(analysis_result, attr):
            raise ValueError(f"analysis_result missing attribute: {attr}")

    # Check best_combos DataFrame
    if analysis_result.best_combos.empty:
        raise ValueError("best_combos DataFrame is empty - no edges to validate")

    required_cols = ['bbw_state', 'direction', 'n_trades',
                     'be_plus_fees_rate', 'per_trade_pnl']
    missing_cols = [col for col in required_cols
                    if col not in analysis_result.best_combos.columns]
    if missing_cols:
        raise ValueError(f"best_combos missing columns: {missing_cols}")

    # Check per_trade_pnl exists and is non-empty
    for idx, row in analysis_result.best_combos.iterrows():
        pnl_array = row['per_trade_pnl']
        if not isinstance(pnl_array, (list, np.ndarray)):
            raise ValueError(f"per_trade_pnl must be list/array, got {type(pnl_array)}")
        if len(pnl_array) == 0:
            raise ValueError(f"per_trade_pnl is empty for {row['bbw_state']} {row['direction']}")
        if len(pnl_array) != row['n_trades']:
            raise ValueError(f"per_trade_pnl length ({len(pnl_array)}) != n_trades ({row['n_trades']})")

    return True


# =============================================================================
# BOOTSTRAP TESTING (with replacement)
# =============================================================================

def run_bootstrap_pnl(
    per_trade_pnl: List[float],
    n_sims: int = 1000,
    confidence: float = 0.90,
    seed: Optional[int] = None
) -> Tuple[float, float, np.ndarray]:
    """Bootstrap resample PnL to get confidence intervals.

    Resamples trade PnL with replacement to estimate distribution of mean PnL.
    Used to determine if edge is consistent across different trade samples.

    Args:
        per_trade_pnl: List of per-trade PnL values
        n_sims: Number of bootstrap simulations (default 1000)
        confidence: Confidence level (default 0.90 for 90% CI)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (ci_lower, ci_upper, bootstrap_means)
    """
    if seed is not None:
        np.random.seed(seed)

    n_trades = len(per_trade_pnl)
    pnl_array = np.array(per_trade_pnl)
    bootstrap_means = []

    for _ in range(n_sims):
        # Resample with replacement
        sample = np.random.choice(pnl_array, size=n_trades, replace=True)
        bootstrap_means.append(sample.mean())

    bootstrap_means = np.array(bootstrap_means)

    # Calculate confidence interval
    alpha = 1.0 - confidence
    ci_lower = np.percentile(bootstrap_means, alpha/2 * 100)
    ci_upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)

    return ci_lower, ci_upper, bootstrap_means


# =============================================================================
# PERMUTATION TESTING (without replacement, path-dependent)
# =============================================================================

def run_permutation_dd(
    per_trade_pnl: List[float],
    n_sims: int = 1000,
    seed: Optional[int] = None
) -> Tuple[float, float, bool]:
    """Permutation test for drawdown robustness (path-dependent).

    Shuffles trade sequence to test if drawdown is path-dependent (fragile)
    or stable across permutations (robust). High drawdown relative to
    permutations indicates the result is sensitive to trade order.

    Args:
        per_trade_pnl: List of per-trade PnL values
        n_sims: Number of permutation simulations (default 1000)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (real_dd, p95_dd, is_fragile)
            real_dd: Actual max drawdown from original sequence
            p95_dd: 95th percentile of permuted drawdowns
            is_fragile: True if real_dd > p95_dd
    """
    if seed is not None:
        np.random.seed(seed)

    pnl_array = np.array(per_trade_pnl)

    # Calculate real drawdown
    real_equity = np.cumsum(pnl_array)
    real_peak = np.maximum.accumulate(real_equity)
    real_dd = np.max(real_peak - real_equity)

    # Permutation distribution
    permuted_dds = []
    for _ in range(n_sims):
        shuffled = np.random.permutation(pnl_array)
        equity = np.cumsum(shuffled)
        peak = np.maximum.accumulate(equity)
        dd = np.max(peak - equity)
        permuted_dds.append(dd)

    permuted_dds = np.array(permuted_dds)
    p95_dd = np.percentile(permuted_dds, 95)

    # Fragile if real DD significantly worse than permutations
    is_fragile = real_dd > p95_dd

    return real_dd, p95_dd, is_fragile


# =============================================================================
# VERDICT CLASSIFICATION
# =============================================================================

def classify_verdict(
    n_trades: int,
    mean_pnl: float,
    ci_lower: float,
    ci_upper: float,
    dd_fragile: bool,
    min_trades: int = 100,
    min_net_expectancy: float = 1.0
) -> Tuple[str, str]:
    """Classify edge robustness based on statistical metrics.

    Verdict categories:
    - INSUFFICIENT: Not enough trades for reliable statistics
    - COMMISSION_KILL: Even best-case scenario loses money
    - FRAGILE: Inconsistent edge or path-dependent drawdown
    - ROBUST: Consistent profitable edge with stable drawdown

    Args:
        n_trades: Total number of trades
        mean_pnl: Mean PnL per trade
        ci_lower: Lower bound of confidence interval
        ci_upper: Upper bound of confidence interval
        dd_fragile: True if drawdown is path-dependent (permutation test)
        min_trades: Minimum trades required (default 100)
        min_net_expectancy: Minimum acceptable CI lower bound (default $1)

    Returns:
        Tuple of (verdict, reason)
    """
    if n_trades < min_trades:
        return "INSUFFICIENT", f"Only {n_trades} trades (need {min_trades})"

    if ci_upper < 0:
        return "COMMISSION_KILL", f"Even 95th percentile loses: ${ci_upper:.2f}"

    if ci_lower < 0:
        return "FRAGILE", f"5th percentile negative: ${ci_lower:.2f}"

    if dd_fragile:
        return "FRAGILE", "Drawdown path-dependent (permutation fragile)"

    if ci_lower >= min_net_expectancy:
        return "ROBUST", f"Consistent edge: CI=[${ci_lower:.2f}, ${ci_upper:.2f}]"

    return "FRAGILE", f"Weak edge: CI=[${ci_lower:.2f}, ${ci_upper:.2f}]"


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_monte_carlo_v2(
    analysis_result,
    n_sims: int = 1000,
    confidence: float = 0.90,
    min_trades: int = 100,
    min_net_expectancy: float = 1.0,
    seed: Optional[int] = 42
) -> MonteCarloResultV2:
    """Run Monte Carlo validation on BBW Analyzer V2 results.

    Performs bootstrap and permutation testing on each (state, direction)
    combination to classify edge robustness.

    Args:
        analysis_result: BBWAnalysisResultV2 from Layer 4
        n_sims: Number of simulations for MC tests (default 1000)
        confidence: Confidence level for CIs (default 0.90)
        min_trades: Minimum trades for ROBUST verdict (default 100)
        min_net_expectancy: Minimum acceptable CI lower (default $1)
        seed: Random seed for reproducibility

    Returns:
        MonteCarloResultV2 with verdicts and confidence metrics

    Raises:
        ValueError: If input validation fails
    """
    import time
    t0 = time.time()

    # Validate input
    validate_monte_carlo_input(analysis_result)

    # Process each (state, direction) combination
    state_verdicts_list = []
    confidence_intervals_list = []
    overfit_flags_list = []

    for idx, row in analysis_result.best_combos.iterrows():
        state = row['bbw_state']
        direction = row['direction']
        n_trades = row['n_trades']
        per_trade_pnl = row['per_trade_pnl']
        mean_pnl = np.mean(per_trade_pnl)

        # Bootstrap test for PnL confidence interval
        ci_lower, ci_upper, bootstrap_means = run_bootstrap_pnl(
            per_trade_pnl, n_sims=n_sims, confidence=confidence, seed=seed
        )

        # Permutation test for drawdown robustness
        real_dd, p95_dd, dd_fragile = run_permutation_dd(
            per_trade_pnl, n_sims=n_sims, seed=seed
        )

        # Classify verdict
        verdict, reason = classify_verdict(
            n_trades=n_trades,
            mean_pnl=mean_pnl,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            dd_fragile=dd_fragile,
            min_trades=min_trades,
            min_net_expectancy=min_net_expectancy
        )

        # Store verdict
        state_verdicts_list.append({
            'bbw_state': state,
            'direction': direction,
            'n_trades': n_trades,
            'mean_pnl': mean_pnl,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'verdict': verdict,
            'verdict_reason': reason
        })

        # Store confidence intervals
        confidence_intervals_list.append({
            'bbw_state': state,
            'direction': direction,
            'metric': 'pnl',
            'real_value': mean_pnl,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'pctl_rank': (bootstrap_means <= mean_pnl).sum() / len(bootstrap_means) * 100
        })

        # Store overfit flags
        overfit_flags_list.append({
            'bbw_state': state,
            'direction': direction,
            'sample_size_flag': n_trades < min_trades,
            'commission_kill_flag': ci_upper < 0,
            'pnl_fragile_flag': ci_lower < 0,
            'dd_fragile_flag': dd_fragile,
            'verdict': verdict
        })

    # Convert to DataFrames
    state_verdicts = pd.DataFrame(state_verdicts_list)
    confidence_intervals = pd.DataFrame(confidence_intervals_list)
    overfit_flags = pd.DataFrame(overfit_flags_list)

    # Summary statistics
    runtime = time.time() - t0
    summary = {
        'symbol': analysis_result.symbol,
        'n_states_tested': len(state_verdicts),
        'n_robust': len(state_verdicts[state_verdicts['verdict'] == 'ROBUST']),
        'n_fragile': len(state_verdicts[state_verdicts['verdict'] == 'FRAGILE']),
        'n_commission_kill': len(state_verdicts[state_verdicts['verdict'] == 'COMMISSION_KILL']),
        'n_insufficient': len(state_verdicts[state_verdicts['verdict'] == 'INSUFFICIENT']),
        'n_sims': n_sims,
        'confidence': confidence,
        'runtime_seconds': runtime
    }

    return MonteCarloResultV2(
        state_verdicts=state_verdicts,
        confidence_intervals=confidence_intervals,
        overfit_flags=overfit_flags,
        summary=summary
    )
