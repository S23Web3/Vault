"""BBW V2 Layer 4: Analyzer - Analyze backtester results by BBW state.

This module analyzes EXISTING backtester results (not simulation) grouped by
BBW volatility state context to discover LSG effectiveness patterns.

Critical Architecture:
- Input: Backtester v385 results (trades already executed)
- Direction: From Four Pillars strategy (not BBW decision)
- Output: BE+fees success rates per (state, direction, LSG)
- Purpose: Generate VINCE training features (not trading decisions)

Run: python -c "from research.bbw_analyzer_v2 import *"
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Optional, Tuple

import numpy as np
import pandas as pd


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BBWAnalysisResultV2:
    """Analysis results from backtester data grouped by BBW state.

    Attributes:
        results: All (state, direction, LSG) combinations with metrics
        best_combos: Top LSG per (state, direction) by BE+fees rate
        directional_bias: LONG vs SHORT comparison per state
        summary: Overall statistics and metadata
        symbol: Trading pair analyzed
        n_trades_analyzed: Total trades processed
        n_states: Number of unique BBW states
        date_range: (start, end) datetime tuple
        runtime_seconds: Analysis execution time
    """
    results: pd.DataFrame
    best_combos: pd.DataFrame
    directional_bias: pd.DataFrame
    summary: dict
    symbol: str
    n_trades_analyzed: int
    n_states: int
    date_range: Tuple[datetime, datetime]
    runtime_seconds: float


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_backtester_data(df: pd.DataFrame) -> bool:
    """Validate backtester results DataFrame has required structure.

    Args:
        df: DataFrame from backtester_v385 execution

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails with specific reason
    """
    # Check DataFrame is not empty
    if df.empty:
        raise ValueError("Backtester results DataFrame is empty")

    # Required columns
    required = [
        'timestamp', 'symbol', 'direction', 'entry_price', 'exit_price',
        'leverage', 'size', 'grid', 'outcome', 'pnl_gross', 'pnl_net',
        'commission_rt', 'bars_held'
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Validate timestamp
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        raise ValueError("timestamp column must be datetime64 dtype")

    null_timestamps = df['timestamp'].isna().sum()
    if null_timestamps > 0:
        raise ValueError(f"Found {null_timestamps} null timestamps")

    # Validate direction
    valid_directions = {'LONG', 'SHORT'}
    invalid_directions = set(df['direction'].unique()) - valid_directions
    if invalid_directions:
        raise ValueError(
            f"Invalid directions found: {invalid_directions}. "
            f"Must be 'LONG' or 'SHORT'"
        )

    # Validate leverage range
    if not df['leverage'].between(5, 20).all():
        out_of_range = df[~df['leverage'].between(5, 20)]['leverage'].unique()
        raise ValueError(
            f"Leverage out of range [5, 20]: {out_of_range}"
        )

    # Validate size — must be positive (supports fixed-margin backtester output)
    if (df['size'] <= 0).any():
        raise ValueError("size must be > 0 for all trades")

    # Validate grid — must be non-negative
    if (df['grid'] < 0).any():
        raise ValueError("grid must be >= 0 for all trades")

    # Validate outcome values
    valid_outcomes = {'TP', 'SL', 'TIMEOUT'}
    invalid_outcomes = set(df['outcome'].unique()) - valid_outcomes
    if invalid_outcomes:
        raise ValueError(
            f"Invalid outcomes found: {invalid_outcomes}. "
            f"Must be 'TP', 'SL', or 'TIMEOUT'"
        )

    # Validate prices are positive
    if (df['entry_price'] <= 0).any():
        raise ValueError("entry_price must be > 0")

    if (df['exit_price'] <= 0).any():
        raise ValueError("exit_price must be > 0")

    # Validate commission is non-negative
    if (df['commission_rt'] < 0).any():
        raise ValueError("commission_rt must be >= 0")

    # Validate bars_held is positive
    if (df['bars_held'] <= 0).any():
        raise ValueError("bars_held must be > 0")

    return True


def validate_bbw_states(df: pd.DataFrame) -> bool:
    """Validate BBW states DataFrame has required structure.

    Args:
        df: DataFrame from Layer 2 (bbw_sequence.py)

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails with specific reason
    """
    # Check DataFrame is not empty
    if df.empty:
        raise ValueError("BBW states DataFrame is empty")

    # Required columns
    # Required columns — symbol optional (added by bridge script per coin)
    required = ['timestamp', 'bbwp_state', 'bbwp_value']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in bbw_states: {missing}")

    # Validate timestamp
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        raise ValueError("timestamp column must be datetime64 dtype")

    null_timestamps = df['timestamp'].isna().sum()
    if null_timestamps > 0:
        raise ValueError(f"Found {null_timestamps} null timestamps")

    # Validate BBW state values (uses bbwp_state — L1 column name)
    valid_states = {
        'BLUE', 'BLUE_DOUBLE', 'GREEN', 'YELLOW', 'NORMAL',
        'RED', 'RED_DOUBLE', 'MA_CROSS_UP', 'MA_CROSS_DOWN'
    }
    invalid_states = set(df['bbwp_state'].dropna().unique()) - valid_states
    if invalid_states:
        raise ValueError(
            "Invalid BBW states found: " + str(invalid_states) + ". "
            "Must be one of: " + str(valid_states)
        )

    # Validate BBWP percentile range (uses bbwp_value — L1 column name)
    if not df['bbwp_value'].between(0, 100).all():
        raise ValueError("bbwp_value values out of range [0, 100]")

    return True


# =============================================================================
# PLACEHOLDER FOR REMAINING FUNCTIONS
# =============================================================================

def enrich_with_bbw_state(
    trades: pd.DataFrame,
    bbw_states: pd.DataFrame
) -> pd.DataFrame:
    """Add BBW state at entry time to each trade.

    Merges backtester trade results with BBW state information based on
    timestamp alignment. Preserves all original trade columns and adds
    BBW state context.

    Args:
        trades: Validated backtester results DataFrame
        bbw_states: Validated BBW state sequence DataFrame

    Returns:
        DataFrame with original trade data plus:
            - bbw_state: BBW state at trade entry time
            - bbwp_at_entry: BBWP percentile at trade entry time

    Raises:
        ValueError: If timestamp merge results in missing BBW states
    """
    # Ensure timestamps are datetime64
    if not pd.api.types.is_datetime64_any_dtype(trades['timestamp']):
        trades = trades.copy()
        trades['timestamp'] = pd.to_datetime(trades['timestamp'])

    if not pd.api.types.is_datetime64_any_dtype(bbw_states['timestamp']):
        bbw_states = bbw_states.copy()
        bbw_states['timestamp'] = pd.to_datetime(bbw_states['timestamp'])

    # Build bbw_states slice — rename L1 columns to internal names
    bbw_cols = ['timestamp', 'bbwp_state', 'bbwp_value']
    if 'symbol' in bbw_states.columns:
        bbw_cols = ['symbol'] + bbw_cols
    bbw_slice = bbw_states[bbw_cols].rename(columns={
        'bbwp_state': 'bbw_state',
        'bbwp_value': 'bbwp_at_entry'
    })

    # Sort both DataFrames by timestamp (required for merge_asof)
    trades_sorted = trades.sort_values('timestamp').copy()
    bbw_sorted = bbw_slice.sort_values('timestamp')

    # Nearest-bar join: each trade gets BBW state of closest preceding bar
    # Use by='symbol' when symbol is present in both DataFrames
    use_by = ('symbol' in trades_sorted.columns and 'symbol' in bbw_sorted.columns)
    if use_by:
        enriched = pd.merge_asof(
            trades_sorted,
            bbw_sorted,
            on='timestamp',
            by='symbol',
            direction='backward'
        )
    else:
        enriched = pd.merge_asof(
            trades_sorted,
            bbw_sorted,
            on='timestamp',
            direction='backward'
        )

    # Check for missing BBW states after join
    missing_count = enriched['bbw_state'].isna().sum()
    if missing_count > 0:
        total_trades = len(enriched)
        pct_missing = (missing_count / total_trades) * 100
        if pct_missing > 10.0:
            raise ValueError(
                "BBW state join failed: " + str(missing_count) + " trades ("
                + str(round(pct_missing, 1)) + "%) missing BBW state. "
                "Check that OHLCV cache covers the same date range as trades."
            )
        # Warn but continue if < 10% missing
        enriched = enriched.dropna(subset=['bbw_state'])

    return enriched


def group_by_state_direction_lsg(
    enriched_trades: pd.DataFrame,
    min_trades: int = 100
) -> pd.DataFrame:
    """Group trades by BBW state, direction, and LSG parameters.

    Groups enriched trade data by all dimensions: state, direction, leverage,
    size, and grid. Calculates aggregated metrics for each group and filters
    out groups with insufficient sample size.

    Args:
        enriched_trades: Trades with BBW state added (from enrich_with_bbw_state)
        min_trades: Minimum trades required per group (default 100)

    Returns:
        DataFrame with one row per (state, direction, LSG) combination.
        Includes aggregated metrics for each group.

    Raises:
        ValueError: If enriched_trades missing required columns
    """
    # Validate required columns
    required = [
        'bbw_state', 'direction', 'leverage', 'size', 'grid',
        'pnl_net', 'pnl_gross', 'commission_rt', 'outcome'
    ]
    missing = [col for col in required if col not in enriched_trades.columns]
    if missing:
        raise ValueError(
            f"enriched_trades missing required columns: {missing}. "
            f"Did you call enrich_with_bbw_state() first?"
        )

    # Convert to categorical for faster grouping
    enriched = enriched_trades.copy()
    enriched['bbw_state'] = enriched['bbw_state'].astype('category')
    enriched['direction'] = enriched['direction'].astype('category')

    # Group by all dimensions
    grouped = enriched.groupby([
        'bbw_state',
        'direction',
        'leverage',
        'size',
        'grid'
    ], observed=True).apply(calculate_group_metrics, include_groups=False)

    # Reset index to convert MultiIndex to regular columns
    grouped = grouped.reset_index()

    # Filter: Remove groups with insufficient trades
    grouped_filtered = grouped[grouped['n_trades'] >= min_trades].copy()

    return grouped_filtered


def calculate_group_metrics(group: pd.DataFrame) -> pd.Series:
    """Calculate performance metrics for a group of trades.

    PRIMARY METRIC: BE+fees rate (% trades with pnl_net >= 0)

    Args:
        group: Trades in a single (state, direction, LSG) group

    Returns:
        Series with aggregated metrics:
            - n_trades: Sample size
            - be_plus_fees_rate: PRIMARY - % achieving BE+fees
            - be_plus_fees_count: Count achieving BE+fees
            - win_rate: For comparison (gross PnL > 0)
            - avg_gross_pnl: Before commission
            - avg_net_pnl: After commission
            - total_net_pnl: Sum of all net PnLs
            - avg_commission: Average RT commission
            - commission_drag: gross - net average
            - max_dd: Maximum drawdown
            - sharpe: Sharpe ratio
            - sortino: Sortino ratio
            - tp_count, sl_count, timeout_count: Outcome distribution
            - per_trade_pnl: List of individual net PnLs (for Layer 4b MC)
    """
    n_trades = len(group)

    # BE+fees calculation (PRIMARY METRIC)
    be_plus_fees_count = (group['pnl_net'] >= 0).sum()
    be_plus_fees_rate = be_plus_fees_count / n_trades if n_trades > 0 else 0.0

    # PnL metrics
    avg_gross_pnl = group['pnl_gross'].mean()
    avg_net_pnl = group['pnl_net'].mean()
    total_net_pnl = group['pnl_net'].sum()

    # Commission impact
    avg_commission = group['commission_rt'].mean()
    commission_drag = avg_gross_pnl - avg_net_pnl

    # Risk metrics
    pnl_array = group['pnl_net'].values
    max_dd = calculate_max_drawdown(pnl_array)
    sharpe = calculate_sharpe(pnl_array)
    sortino = calculate_sortino(pnl_array)

    # Outcome distribution
    tp_count = (group['outcome'] == 'TP').sum()
    sl_count = (group['outcome'] == 'SL').sum()
    timeout_count = (group['outcome'] == 'TIMEOUT').sum()

    # Win rate (for comparison with BE+fees rate)
    win_rate = (group['pnl_gross'] > 0).sum() / n_trades if n_trades > 0 else 0.0

    return pd.Series({
        'n_trades': n_trades,
        'be_plus_fees_rate': be_plus_fees_rate,  # PRIMARY METRIC
        'be_plus_fees_count': be_plus_fees_count,
        'win_rate': win_rate,  # For comparison
        'avg_gross_pnl': avg_gross_pnl,
        'avg_net_pnl': avg_net_pnl,
        'total_net_pnl': total_net_pnl,
        'avg_commission': avg_commission,
        'commission_drag': commission_drag,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'sortino': sortino,
        'tp_count': tp_count,
        'sl_count': sl_count,
        'timeout_count': timeout_count,
        'per_trade_pnl': pnl_array.tolist()  # For Layer 4b MC
    })


def find_best_lsg_per_state_direction(
    grouped_results: pd.DataFrame
) -> pd.DataFrame:
    """For each (state, direction), find LSG with highest BE+fees rate.

    Selects the optimal leverage, size, and grid parameters for each
    (state, direction) combination based on maximum BE+fees success rate.

    Args:
        grouped_results: All group combinations with metrics from grouping

    Returns:
        DataFrame with exactly 1 row per (state, direction) combination.
        Contains the best performing LSG parameters and all associated metrics.

    Raises:
        ValueError: If grouped_results missing required columns
    """
    # Validate required columns
    required = ['bbw_state', 'direction', 'be_plus_fees_rate']
    missing = [col for col in required if col not in grouped_results.columns]
    if missing:
        raise ValueError(f"grouped_results missing required columns: {missing}")

    if grouped_results.empty:
        # Return empty DataFrame with same structure
        return grouped_results.copy()

    # Sort by BE+fees rate (descending) to get highest first
    sorted_results = grouped_results.sort_values(
        by='be_plus_fees_rate',
        ascending=False
    )

    # Keep first (highest BE+fees) row per (state, direction)
    best_combos = sorted_results.groupby(
        ['bbw_state', 'direction'],
        as_index=False,
        observed=True
    ).first()

    return best_combos


def detect_directional_bias(
    best_combos: pd.DataFrame,
    bias_threshold: float = 0.05
) -> pd.DataFrame:
    """Determine if BBW states favor LONG or SHORT direction.

    Compares BE+fees rates for LONG vs SHORT trades in each BBW state.
    Identifies states with significant directional edge.

    Args:
        best_combos: Best LSG per (state, direction) from find_best_lsg_per_state_direction()
        bias_threshold: Minimum difference to declare bias (default 0.05 = 5%)

    Returns:
        DataFrame with columns:
            - bbw_state: State name
            - long_be_fees_rate: BE+fees rate for LONG (None if missing)
            - short_be_fees_rate: BE+fees rate for SHORT (None if missing)
            - difference: LONG - SHORT (positive favors LONG, negative favors SHORT)
            - bias: "LONG", "SHORT", "NEUTRAL", or "MISSING_DIRECTION"
            - bias_strength: abs(difference), None if missing direction
    """
    # Validate input
    required = ['bbw_state', 'direction', 'be_plus_fees_rate']
    missing = [col for col in required if col not in best_combos.columns]
    if missing:
        raise ValueError(f"best_combos missing required columns: {missing}")

    if best_combos.empty:
        return pd.DataFrame(columns=[
            'bbw_state', 'long_be_fees_rate', 'short_be_fees_rate',
            'difference', 'bias', 'bias_strength'
        ])

    # Get unique states
    unique_states = best_combos['bbw_state'].unique()

    bias_results = []
    for state in unique_states:
        state_data = best_combos[best_combos['bbw_state'] == state]

        # Extract LONG and SHORT rates
        long_data = state_data[state_data['direction'] == 'LONG']
        short_data = state_data[state_data['direction'] == 'SHORT']

        long_rate = long_data['be_plus_fees_rate'].iloc[0] if len(long_data) > 0 else None
        short_rate = short_data['be_plus_fees_rate'].iloc[0] if len(short_data) > 0 else None

        # Calculate difference (LONG - SHORT)
        if long_rate is not None and short_rate is not None:
            difference = long_rate - short_rate
        else:
            difference = None

        # Determine bias
        if difference is None:
            bias = "MISSING_DIRECTION"
            bias_strength = None
        elif abs(difference) < bias_threshold:
            bias = "NEUTRAL"
            bias_strength = abs(difference)
        elif difference > 0:
            bias = "LONG"
            bias_strength = abs(difference)
        else:
            bias = "SHORT"
            bias_strength = abs(difference)

        bias_results.append({
            'bbw_state': state,
            'long_be_fees_rate': long_rate,
            'short_be_fees_rate': short_rate,
            'difference': difference,
            'bias': bias,
            'bias_strength': bias_strength
        })

    return pd.DataFrame(bias_results)


def analyze_bbw_patterns_v2(
    backtester_results: pd.DataFrame,
    bbw_states: pd.DataFrame,
    symbol: Optional[str] = None,
    min_trades_per_group: int = 100
) -> BBWAnalysisResultV2:
    """Analyze backtester results grouped by BBW state context.

    Main entry point for Layer 4 BBW analysis. Orchestrates all phases:
    - Phase 1: Input validation
    - Phase 2: Data enrichment (BBW state alignment)
    - Phase 3+4: Grouping and metrics calculation
    - Phase 5: Best combo selection
    - Phase 6: Directional bias detection

    Args:
        backtester_results: Trade results from backtester_v385
        bbw_states: BBW state sequence from Layer 2
        symbol: Optional symbol override (auto-detected if not provided)
        min_trades_per_group: Minimum sample size per group (default 100)

    Returns:
        BBWAnalysisResultV2 with complete analysis including:
            - results: All (state, direction, LSG) groups
            - best_combos: Top LSG per (state, direction)
            - directional_bias: LONG vs SHORT comparison
            - summary: Metadata and statistics

    Raises:
        ValueError: If input data validation fails
    """
    t0 = time.time()

    # Phase 1: Input Validation
    validate_backtester_data(backtester_results)
    validate_bbw_states(bbw_states)

    # Phase 2: Data Enrichment (BBW state alignment)
    enriched_trades = enrich_with_bbw_state(backtester_results, bbw_states)

    # Phase 3+4: Grouping Logic + Metrics Calculation
    grouped_results = group_by_state_direction_lsg(enriched_trades, min_trades_per_group)

    # Phase 5: Best Combo Selection
    best_combos = find_best_lsg_per_state_direction(grouped_results)

    # Phase 6: Directional Bias Detection
    directional_bias = detect_directional_bias(best_combos)

    # Extract metadata
    if symbol is None:
        # Auto-detect from data
        if 'symbol' in backtester_results.columns:
            symbol = backtester_results['symbol'].iloc[0] if len(backtester_results) > 0 else "UNKNOWN"
        else:
            symbol = "UNKNOWN"

    n_trades_analyzed = len(enriched_trades)
    n_states = len(enriched_trades['bbw_state'].unique()) if not enriched_trades.empty else 0

    # Date range
    if 'timestamp' in enriched_trades.columns and not enriched_trades.empty:
        min_date = enriched_trades['timestamp'].min()
        max_date = enriched_trades['timestamp'].max()
        date_range = (min_date, max_date)
    else:
        date_range = (None, None)

    runtime_seconds = time.time() - t0

    # Summary dictionary
    summary = {
        'symbol': symbol,
        'n_trades_analyzed': n_trades_analyzed,
        'n_states': n_states,
        'n_groups': len(grouped_results),
        'n_best_combos': len(best_combos),
        'n_biased_states': len(directional_bias[directional_bias['bias'] != 'NEUTRAL']) if not directional_bias.empty else 0,
        'date_range_start': date_range[0],
        'date_range_end': date_range[1],
        'runtime_seconds': runtime_seconds,
        'min_trades_per_group': min_trades_per_group
    }

    # Assemble result object
    result = BBWAnalysisResultV2(
        results=grouped_results,
        best_combos=best_combos,
        directional_bias=directional_bias,
        summary=summary,
        symbol=symbol,
        n_trades_analyzed=n_trades_analyzed,
        n_states=n_states,
        date_range=date_range,
        runtime_seconds=runtime_seconds
    )

    return result


# =============================================================================
# HELPER FUNCTIONS (Stubs)
# =============================================================================

def calculate_max_drawdown(pnl_array: np.ndarray) -> float:
    """Calculate maximum drawdown from PnL array.

    Args:
        pnl_array: Array of per-trade PnLs

    Returns:
        Maximum drawdown as positive value (peak - trough)
    """
    if len(pnl_array) == 0:
        return 0.0

    # Calculate cumulative equity curve
    equity = np.cumsum(pnl_array)

    # Calculate running maximum (peak)
    peak = np.maximum.accumulate(equity)

    # Drawdown at each point
    drawdown = peak - equity

    # Maximum drawdown (stored as positive value)
    max_dd = np.max(drawdown)

    return float(max_dd)


def calculate_sharpe(pnl_array: np.ndarray) -> float:
    """Calculate Sharpe ratio from PnL array.

    Args:
        pnl_array: Array of per-trade PnLs

    Returns:
        Sharpe ratio (mean / std). Returns 0.0 for zero variance.
    """
    if len(pnl_array) == 0:
        return 0.0

    mean_pnl = np.mean(pnl_array)
    std_pnl = np.std(pnl_array, ddof=1)  # Sample std

    # Handle zero variance case
    if std_pnl == 0 or np.isnan(std_pnl):
        return 0.0

    return float(mean_pnl / std_pnl)


def calculate_sortino(pnl_array: np.ndarray) -> float:
    """Calculate Sortino ratio from PnL array.

    Only considers downside volatility (negative PnLs).

    Args:
        pnl_array: Array of per-trade PnLs

    Returns:
        Sortino ratio (mean / downside_std). Returns 0.0 for zero downside.
    """
    if len(pnl_array) == 0:
        return 0.0

    mean_pnl = np.mean(pnl_array)

    # Downside deviations only (negative PnLs)
    downside = pnl_array[pnl_array < 0]

    if len(downside) == 0:
        # No losses = infinite Sortino, return 0.0 by convention
        return 0.0

    downside_std = np.std(downside, ddof=1)

    # Handle zero variance case
    if downside_std == 0 or np.isnan(downside_std):
        return 0.0

    return float(mean_pnl / downside_std)


if __name__ == '__main__':
    print("BBW Analyzer V2 - Layer 4")
    print("Phase 1: Input Validation - COMPLETE")
    print("Remaining phases: TBD")
