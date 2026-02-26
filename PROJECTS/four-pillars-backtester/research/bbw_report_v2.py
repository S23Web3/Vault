"""BBW V2 Layer 5: Report Generator - VINCE feature aggregation.

Transforms Layer 4 (Analyzer) + Layer 4b (Monte Carlo) results into VINCE training features.
Pure data transformation - no new calculations, no signal processing.

Architecture:
- Input: BBWAnalysisResultV2 + MonteCarloResultV2
- Output: BBWReportResultV2 (5 DataFrames + summary dict)
- Purpose: Generate ML features for VINCE training

Run: Imported by scripts, not run directly
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import time

import numpy as np
import pandas as pd


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BBWReportResultV2:
    """Output container for BBW report generation.

    Attributes:
        directional_bias: Bias analysis per state (LONG/SHORT/NEUTRAL)
        be_fees_success: Success rate table with verdicts
        vince_features: ML feature vectors for training
        lsg_sensitivity: LSG parameter correlation analysis
        state_summary: High-level summary per BBW state
        summary: Overall statistics dictionary
        output_dir: Directory where CSVs were written
    """
    directional_bias: pd.DataFrame
    be_fees_success: pd.DataFrame
    vince_features: pd.DataFrame
    lsg_sensitivity: pd.DataFrame
    state_summary: pd.DataFrame
    summary: dict
    output_dir: Optional[str] = None


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_report_inputs(analysis_result, mc_result) -> bool:
    """Validate Layer 4 and Layer 4b results have required structure.

    Args:
        analysis_result: BBWAnalysisResultV2 from Layer 4
        mc_result: MonteCarloResultV2 from Layer 4b

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails with specific reason
    """
    # Check Layer 4 result
    required_attrs = ['results', 'best_combos', 'directional_bias', 'summary', 'symbol']
    for attr in required_attrs:
        if not hasattr(analysis_result, attr):
            raise ValueError(f"analysis_result missing attribute: {attr}")

    if analysis_result.best_combos.empty:
        raise ValueError("best_combos DataFrame is empty - no data to process")

    # Check Layer 4b result
    required_attrs = ['state_verdicts', 'confidence_intervals', 'overfit_flags', 'summary']
    for attr in required_attrs:
        if not hasattr(mc_result, attr):
            raise ValueError(f"mc_result missing attribute: {attr}")

    # Empty state_verdicts is allowed — MC may be skipped; downstream uses UNKNOWN verdict

    # Check critical columns exist
    if 'bbw_state' not in analysis_result.best_combos.columns:
        raise ValueError("best_combos missing 'bbw_state' column")

    if 'bbw_state' not in mc_result.state_verdicts.columns:
        raise ValueError("state_verdicts missing 'bbw_state' column")

    return True


# =============================================================================
# FUNCTION 1: DIRECTIONAL BIAS AGGREGATION
# =============================================================================

def aggregate_directional_bias(
    best_combos: pd.DataFrame,
    state_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """Combine Layer 4 bias with Layer 4b verdicts.

    Args:
        best_combos: From Layer 4 (one row per state x direction)
        state_verdicts: From Layer 4b (verdicts per state x direction)

    Returns:
        DataFrame with columns:
            - bbw_state
            - long_be_fees_rate, short_be_fees_rate
            - long_verdict, short_verdict
            - bias_direction (LONG/SHORT/NEUTRAL)
            - bias_strength (abs difference)
            - confidence (HIGH/MEDIUM/LOW)
    """
    rows = []

    for state in best_combos['bbw_state'].unique():
        # Get LONG and SHORT rows
        long_row = best_combos[
            (best_combos['bbw_state'] == state) & (best_combos['direction'] == 'LONG')
        ]
        short_row = best_combos[
            (best_combos['bbw_state'] == state) & (best_combos['direction'] == 'SHORT')
        ]

        # Skip if either direction missing
        if long_row.empty or short_row.empty:
            continue

        long_rate = long_row.iloc[0]['be_plus_fees_rate']
        short_rate = short_row.iloc[0]['be_plus_fees_rate']

        # Get verdicts
        long_verdict = state_verdicts[
            (state_verdicts['bbw_state'] == state) & (state_verdicts['direction'] == 'LONG')
        ]
        short_verdict = state_verdicts[
            (state_verdicts['bbw_state'] == state) & (state_verdicts['direction'] == 'SHORT')
        ]

        long_v = long_verdict.iloc[0]['verdict'] if not long_verdict.empty else 'UNKNOWN'
        short_v = short_verdict.iloc[0]['verdict'] if not short_verdict.empty else 'UNKNOWN'

        # Calculate bias
        difference = short_rate - long_rate
        if abs(difference) < 0.05:
            bias_direction = 'NEUTRAL'
        elif difference > 0:
            bias_direction = 'SHORT'
        else:
            bias_direction = 'LONG'

        # Calculate confidence
        if long_v == 'ROBUST' and short_v == 'ROBUST':
            confidence = 'HIGH'
        elif long_v == 'FRAGILE' or short_v == 'FRAGILE':
            confidence = 'LOW'
        else:
            confidence = 'MEDIUM'

        rows.append({
            'bbw_state': state,
            'long_be_fees_rate': long_rate,
            'short_be_fees_rate': short_rate,
            'long_verdict': long_v,
            'short_verdict': short_v,
            'bias_direction': bias_direction,
            'bias_strength': abs(difference),
            'confidence': confidence
        })

    return pd.DataFrame(rows)


# =============================================================================
# FUNCTION 2: BE+FEES SUCCESS TABLES
# =============================================================================

def generate_be_fees_success_tables(
    best_combos: pd.DataFrame,
    state_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """Create comprehensive success rate table with verdicts.

    Args:
        best_combos: From Layer 4
        state_verdicts: From Layer 4b

    Returns:
        DataFrame with all metrics + verdict per row
    """
    rows = []

    for idx, row in best_combos.iterrows():
        state = row['bbw_state']
        direction = row['direction']

        # Lookup verdict
        verdict_row = state_verdicts[
            (state_verdicts['bbw_state'] == state) & (state_verdicts['direction'] == direction)
        ]
        verdict = verdict_row.iloc[0]['verdict'] if not verdict_row.empty else 'UNKNOWN'

        rows.append({
            'bbw_state': state,
            'direction': direction,
            'leverage': row['leverage'],
            'size': row['size'],
            'grid': row['grid'],
            'n_trades': row['n_trades'],
            'be_plus_fees_rate': row['be_plus_fees_rate'],
            'win_rate': row['win_rate'],
            'rate_divergence': row['be_plus_fees_rate'] - row['win_rate'],
            'avg_net_pnl': row['avg_net_pnl'],
            'avg_commission': row['avg_commission'],
            'commission_drag': row['commission_drag'],
            'verdict': verdict,
            'sharpe': row['sharpe'],
            'max_dd': row['max_dd']
        })

    return pd.DataFrame(rows)


# =============================================================================
# FUNCTION 3: VINCE FEATURES
# =============================================================================

def create_vince_features(
    best_combos: pd.DataFrame,
    directional_bias: pd.DataFrame,
    state_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """Generate ML feature vectors for VINCE training.

    Args:
        best_combos: From Layer 4
        directional_bias: From Function 1
        state_verdicts: From Layer 4b

    Returns:
        DataFrame with feature columns + target columns + sample_weight
    """
    # State encoding (ordinal) — must match Layer 4 valid_states exactly
    state_encoding = {
        'BLUE': 1, 'BLUE_DOUBLE': 2,
        'GREEN': 3,
        'YELLOW': 4,
        'NORMAL': 5,
        'RED': 6, 'RED_DOUBLE': 7,
        'MA_CROSS_UP': 8, 'MA_CROSS_DOWN': 9
    }

    # Verdict encoding (ordinal, MARGINAL removed as approved)
    verdict_encoding = {
        'ROBUST': 3,
        'FRAGILE': 1,
        'COMMISSION_KILL': 0,
        'INSUFFICIENT': -1,
        'UNKNOWN': -2
    }

    rows = []

    for idx, row in best_combos.iterrows():
        state = row['bbw_state']
        direction = row['direction']

        # Lookup bias
        bias_row = directional_bias[directional_bias['bbw_state'] == state]
        if bias_row.empty:
            continue  # Skip if bias not found

        bias_direction = bias_row.iloc[0]['bias_direction']
        bias_strength = bias_row.iloc[0]['bias_strength']

        # Lookup verdict
        verdict_row = state_verdicts[
            (state_verdicts['bbw_state'] == state) & (state_verdicts['direction'] == direction)
        ]
        verdict = verdict_row.iloc[0]['verdict'] if not verdict_row.empty else 'UNKNOWN'

        # Feature encoding
        feature_state_ordinal = state_encoding.get(state, 0)
        feature_state_blue = 1 if 'BLUE' in state else 0
        feature_state_red = 1 if 'RED' in state else 0
        feature_state_double = 1 if 'DOUBLE' in state else 0
        feature_state_macross = 1 if 'MA_CROSS' in state else 0
        feature_state_normal = 1 if state == 'NORMAL' else 0
        feature_direction_long = 1 if direction == 'LONG' else 0

        # Bias alignment (NEUTRAL = 0 as approved)
        if bias_direction == 'NEUTRAL':
            feature_bias_aligned = 0
        elif bias_direction == direction:
            feature_bias_aligned = 1
        else:
            feature_bias_aligned = 0

        # Verdict encoding
        feature_verdict_ordinal = verdict_encoding.get(verdict, -2)

        # Sample weight (ROBUST = 1.0, others = 0.5)
        sample_weight = 1.0 if verdict == 'ROBUST' else 0.5

        rows.append({
            # Identifiers
            'bbw_state': state,
            'direction': direction,
            # Features
            'feature_state_ordinal': feature_state_ordinal,
            'feature_state_blue': feature_state_blue,
            'feature_state_red': feature_state_red,
            'feature_state_double': feature_state_double,
            'feature_state_macross': feature_state_macross,
            'feature_state_normal': feature_state_normal,
            'feature_direction_long': feature_direction_long,
            'feature_bias_aligned': feature_bias_aligned,
            'feature_bias_strength': bias_strength,
            'feature_leverage': row['leverage'],
            'feature_size': row['size'],
            'feature_grid': row['grid'],
            'feature_n_trades': row['n_trades'],
            'feature_verdict_ordinal': feature_verdict_ordinal,
            # Targets
            'target_be_plus_fees_rate': row['be_plus_fees_rate'],
            'target_avg_net_pnl': row['avg_net_pnl'],
            'target_sharpe': row['sharpe'],
            'target_verdict': verdict,
            # Weight
            'sample_weight': sample_weight
        })

    return pd.DataFrame(rows)


# =============================================================================
# FUNCTION 4: LSG SENSITIVITY ANALYSIS
# =============================================================================

def analyze_lsg_sensitivity(
    results: pd.DataFrame,
    best_combos: pd.DataFrame
) -> pd.DataFrame:
    """Analyze LSG parameter sensitivity per state x direction.

    Args:
        results: ALL groups from Layer 4 (not just best_combos)
        best_combos: For reference

    Returns:
        DataFrame with correlation analysis per state x direction
    """
    rows = []

    for state in results['bbw_state'].unique():
        for direction in results['direction'].unique():
            subset = results[
                (results['bbw_state'] == state) & (results['direction'] == direction)
            ]

            if len(subset) < 3:
                continue  # Not enough for correlation

            # Calculate correlations
            lev_corr = subset[['leverage', 'be_plus_fees_rate']].corr().iloc[0, 1]
            size_corr = subset[['size', 'be_plus_fees_rate']].corr().iloc[0, 1]
            grid_corr = subset[['grid', 'be_plus_fees_rate']].corr().iloc[0, 1]

            # Dominant parameter
            corrs = {'leverage': abs(lev_corr), 'size': abs(size_corr), 'grid': abs(grid_corr)}
            dominant = max(corrs, key=corrs.get) if not all(np.isnan(list(corrs.values()))) else None

            # Get best combo
            best = best_combos[
                (best_combos['bbw_state'] == state) & (best_combos['direction'] == direction)
            ]

            if best.empty:
                continue

            rows.append({
                'bbw_state': state,
                'direction': direction,
                'best_leverage': best.iloc[0]['leverage'],
                'best_size': best.iloc[0]['size'],
                'best_grid': best.iloc[0]['grid'],
                'leverage_sensitivity': lev_corr,
                'size_sensitivity': size_corr,
                'grid_sensitivity': grid_corr,
                'dominant_parameter': dominant
            })

    return pd.DataFrame(rows)


# =============================================================================
# FUNCTION 5: STATE SUMMARY
# =============================================================================

def generate_state_summary(
    directional_bias: pd.DataFrame,
    be_fees_success: pd.DataFrame,
    state_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """Generate high-level summary per BBW state.

    Args:
        directional_bias: From Function 1
        be_fees_success: From Function 2
        state_verdicts: From Layer 4b

    Returns:
        DataFrame with state-level aggregates
    """
    rows = []

    for state in directional_bias['bbw_state'].unique():
        bias_row = directional_bias[directional_bias['bbw_state'] == state].iloc[0]

        # Get all rows for this state
        state_rows = be_fees_success[be_fees_success['bbw_state'] == state]

        n_directions = len(state_rows)
        avg_be_fees_rate = state_rows['be_plus_fees_rate'].mean()
        best_direction = state_rows.loc[state_rows['be_plus_fees_rate'].idxmax(), 'direction'] if n_directions > 0 else None
        total_sample_size = state_rows['n_trades'].sum()

        # Verdict counts
        verdicts = state_verdicts[state_verdicts['bbw_state'] == state]
        n_robust = len(verdicts[verdicts['verdict'] == 'ROBUST'])
        n_fragile = len(verdicts[verdicts['verdict'] == 'FRAGILE'])
        n_commission_kill = len(verdicts[verdicts['verdict'] == 'COMMISSION_KILL'])

        # State quality (categorical as approved)
        if n_robust == len(verdicts) and len(verdicts) > 0:
            state_quality = 'HIGH_QUALITY'
        elif n_commission_kill == len(verdicts) and len(verdicts) > 0:
            state_quality = 'DEAD'
        else:
            state_quality = 'MIXED'

        rows.append({
            'bbw_state': state,
            'bias_direction': bias_row['bias_direction'],
            'bias_confidence': bias_row['confidence'],
            'n_directions': n_directions,
            'avg_be_fees_rate': avg_be_fees_rate,
            'best_direction': best_direction,
            'total_sample_size': total_sample_size,
            'n_robust': n_robust,
            'n_fragile': n_fragile,
            'n_commission_kill': n_commission_kill,
            'state_quality': state_quality
        })

    return pd.DataFrame(rows)


# =============================================================================
# FUNCTION 6: MAIN ORCHESTRATOR
# =============================================================================

def generate_vince_features_v2(
    analysis_result,
    mc_result,
    output_dir: Optional[str] = None
) -> BBWReportResultV2:
    """Generate VINCE training features from Layer 4 + Layer 4b results.

    Main orchestrator that runs all 5 aggregation functions and exports CSVs.

    Args:
        analysis_result: BBWAnalysisResultV2 from Layer 4
        mc_result: MonteCarloResultV2 from Layer 4b
        output_dir: Optional directory to write CSV files

    Returns:
        BBWReportResultV2 with all 5 DataFrames + summary

    Raises:
        ValueError: If input validation fails
    """
    t0 = time.time()

    # Guard: if mc_result is None, create an empty placeholder so pipeline runs
    if mc_result is None:
        @dataclass
        class _EmptyMC:
            state_verdicts: pd.DataFrame = None
            confidence_intervals: pd.DataFrame = None
            overfit_flags: pd.DataFrame = None
            summary: dict = None
        empty_verdicts = pd.DataFrame(columns=['bbw_state', 'direction', 'verdict'])
        mc_result = _EmptyMC(
            state_verdicts=empty_verdicts,
            confidence_intervals=pd.DataFrame(),
            overfit_flags=pd.DataFrame(),
            summary={}
        )

    # Validate inputs
    validate_report_inputs(analysis_result, mc_result)

    # Run all 5 functions
    directional_bias = aggregate_directional_bias(
        analysis_result.best_combos,
        mc_result.state_verdicts
    )

    be_fees_success = generate_be_fees_success_tables(
        analysis_result.best_combos,
        mc_result.state_verdicts
    )

    vince_features = create_vince_features(
        analysis_result.best_combos,
        directional_bias,
        mc_result.state_verdicts
    )

    lsg_sensitivity = analyze_lsg_sensitivity(
        analysis_result.results,
        analysis_result.best_combos
    )

    state_summary = generate_state_summary(
        directional_bias,
        be_fees_success,
        mc_result.state_verdicts
    )

    # Export CSVs if output_dir provided
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        directional_bias.to_csv(output_path / "directional_bias.csv", index=False)
        be_fees_success.to_csv(output_path / "be_fees_success.csv", index=False)
        vince_features.to_csv(output_path / "vince_features.csv", index=False)
        lsg_sensitivity.to_csv(output_path / "lsg_sensitivity.csv", index=False)
        state_summary.to_csv(output_path / "state_summary.csv", index=False)

    runtime = time.time() - t0

    summary = {
        'n_states': len(directional_bias),
        'n_features': len(vince_features),
        'n_sensitivity_analyzed': len(lsg_sensitivity),
        'runtime_seconds': round(runtime, 2)
    }

    return BBWReportResultV2(
        directional_bias=directional_bias,
        be_fees_success=be_fees_success,
        vince_features=vince_features,
        lsg_sensitivity=lsg_sensitivity,
        state_summary=state_summary,
        summary=summary,
        output_dir=str(output_dir) if output_dir else None
    )
