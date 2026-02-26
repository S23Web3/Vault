"""Debug script for BBW Analyzer V2 (Layer 4).

Comprehensive validation with hand-computed checks across 10 debug sections.
Validates math logic, data integrity, and contract compliance.

Run: python scripts/debug_bbw_analyzer_v2.py
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
    find_best_lsg_per_state_direction,
    detect_directional_bias,
    analyze_bbw_patterns_v2
)


# =============================================================================
# SECTION 1: INPUT DATA VALIDATION
# =============================================================================

def section_1_input_validation():
    """Verify backtester results and BBW states structure."""
    print("\n" + "=" * 70)
    print("SECTION 1: INPUT DATA VALIDATION")
    print("=" * 70)

    # Create test dataset (500 trades for sufficient grouping)
    n_trades = 500
    trades = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_trades, freq='1min'),
        'symbol': ['RIVERUSDT'] * n_trades,
        'direction': ['LONG'] * (n_trades//2) + ['SHORT'] * (n_trades//2),
        'entry_price': np.random.uniform(0.50, 0.60, n_trades),
        'exit_price': np.random.uniform(0.50, 0.60, n_trades),
        'leverage': np.random.choice([10, 15, 20], n_trades),
        'size': np.random.choice([1.0, 1.5, 2.0], n_trades),
        'grid': np.random.choice([1.5, 2.0, 2.5], n_trades),
        'outcome': np.random.choice(['TP', 'SL', 'TIMEOUT'], n_trades),
        'pnl_gross': np.random.uniform(-20, 30, n_trades),
        'pnl_net': np.random.uniform(-28, 22, n_trades),
        'commission_rt': [8.0] * n_trades,
        'bars_held': np.random.randint(1, 50, n_trades)
    })

    bbw_states = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_trades, freq='1min'),
        'symbol': ['RIVERUSDT'] * n_trades,
        'bbw_state': np.random.choice([
            'BLUE', 'BLUE_DOUBLE', 'GREEN', 'YELLOW',
            'RED', 'RED_DOUBLE', 'NORMAL', 'MA_CROSS_UP', 'MA_CROSS_DOWN'
        ], n_trades),
        'bbwp': np.random.uniform(0, 100, n_trades)
    })

    # Validate
    try:
        validate_backtester_data(trades)
        print("[PASS] Backtester data validation")
        print(f"  - Rows: {len(trades)}")
        print(f"  - Columns: {len(trades.columns)}")
        print(f"  - Date range: {trades['timestamp'].min()} to {trades['timestamp'].max()}")
    except Exception as e:
        print(f"[FAIL] Backtester validation: {e}")

    try:
        validate_bbw_states(bbw_states)
        print("[PASS] BBW states validation")
        print(f"  - Rows: {len(bbw_states)}")
        print(f"  - Unique states: {bbw_states['bbw_state'].nunique()}")
        print(f"  - BBWP range: [{bbw_states['bbwp'].min():.1f}, {bbw_states['bbwp'].max():.1f}]")
    except Exception as e:
        print(f"[FAIL] BBW states validation: {e}")

    return trades, bbw_states


# =============================================================================
# SECTION 2: ENRICHMENT VERIFICATION
# =============================================================================

def section_2_enrichment_verification(trades, bbw_states):
    """Hand-check BBW state assignment and verify no data loss."""
    print("\n" + "=" * 70)
    print("SECTION 2: ENRICHMENT VERIFICATION")
    print("=" * 70)

    enriched = enrich_with_bbw_state(trades, bbw_states)

    # Check row count preservation
    if len(enriched) == len(trades):
        print(f"[PASS] Row count preserved: {len(enriched)} trades")
    else:
        print(f"[FAIL] Row count changed: {len(trades)} -> {len(enriched)}")

    # Check no missing BBW states
    missing_count = enriched['bbw_state'].isna().sum()
    if missing_count == 0:
        print(f"[PASS] No missing BBW states (0 nulls)")
    else:
        print(f"[FAIL] Missing BBW states: {missing_count} nulls")

    # Check state distribution
    print("\nBBW State Distribution:")
    state_dist = enriched['bbw_state'].value_counts()
    for state, count in state_dist.items():
        pct = (count / len(enriched)) * 100
        print(f"  {state:15s}: {count:4d} ({pct:5.1f}%)")

    # Hand-check first 3 rows
    print("\nFirst 3 Trades (Hand-Check):")
    for idx in range(min(3, len(enriched))):
        ts = enriched.iloc[idx]['timestamp']
        state = enriched.iloc[idx]['bbw_state']
        # Find matching BBW state
        bbw_row = bbw_states[bbw_states['timestamp'] == ts]
        expected_state = bbw_row.iloc[0]['bbw_state'] if len(bbw_row) > 0 else 'MISSING'
        match = "PASS" if state == expected_state else "FAIL"
        print(f"  Trade {idx}: {ts} -> {state} (expected: {expected_state}) [{match}]")

    return enriched


# =============================================================================
# SECTION 3: GROUPING VALIDATION
# =============================================================================

def section_3_grouping_validation(enriched):
    """Count groups per state and verify LSG combinations."""
    print("\n" + "=" * 70)
    print("SECTION 3: GROUPING VALIDATION")
    print("=" * 70)

    grouped = group_by_state_direction_lsg(enriched, min_trades=5)

    print(f"Total groups: {len(grouped)}")
    print(f"Min trades threshold: 5")

    # Groups per state
    if not grouped.empty:
        state_groups = grouped.groupby('bbw_state').size()
        print("\nGroups per BBW State:")
        for state, count in state_groups.items():
            print(f"  {state:15s}: {count:3d} groups")

        # Groups per direction
        dir_groups = grouped.groupby('direction').size()
        print("\nGroups per Direction:")
        for direction, count in dir_groups.items():
            print(f"  {direction:5s}: {count:3d} groups")

        # Verify min_trades filtering
        min_n = grouped['n_trades'].min()
        max_n = grouped['n_trades'].max()
        print(f"\nTrades per group: min={min_n}, max={max_n}")
        if min_n >= 5:
            print("[PASS] All groups meet min_trades threshold")
        else:
            print(f"[FAIL] Some groups below threshold (min={min_n})")

    else:
        print("[WARN] No groups met min_trades threshold (empty result)")

    return grouped


# =============================================================================
# SECTION 4: BE+FEES VS WIN RATE COMPARISON
# =============================================================================

def section_4_be_fees_vs_win_rate(grouped):
    """Show examples where BE+fees diverges from win rate."""
    print("\n" + "=" * 70)
    print("SECTION 4: BE+FEES VS WIN RATE COMPARISON")
    print("=" * 70)

    if grouped.empty:
        print("[SKIP] No groups to analyze")
        return

    # Calculate divergence
    grouped['divergence'] = grouped['win_rate'] - grouped['be_plus_fees_rate']

    # Find top 5 divergences (commission impact)
    top_divergences = grouped.nlargest(5, 'divergence')

    print("Top 5 Commission Kill Examples (win_rate - BE+fees):\n")
    for idx, row in top_divergences.iterrows():
        print(f"State: {row['bbw_state']}, Direction: {row['direction']}, LSG: ({row['leverage']}, {row['size']}, {row['grid']})")
        print(f"  Win Rate:        {row['win_rate']:.3f} ({row['win_rate']*100:.1f}%)")
        print(f"  BE+fees Rate:    {row['be_plus_fees_rate']:.3f} ({row['be_plus_fees_rate']*100:.1f}%)")
        print(f"  Divergence:      {row['divergence']:.3f} ({row['divergence']*100:.1f}%)")
        print(f"  Commission Drag: ${row['commission_drag']:.2f}")
        print(f"  n_trades:        {row['n_trades']}")
        print()

    # Overall stats
    avg_divergence = grouped['divergence'].mean()
    print(f"Average divergence (all groups): {avg_divergence:.3f} ({avg_divergence*100:.1f}%)")
    if avg_divergence > 0:
        print("[PASS] BE+fees < win_rate on average (commission impact confirmed)")


# =============================================================================
# SECTION 5: BEST COMBO SELECTION
# =============================================================================

def section_5_best_combo_selection(grouped):
    """Show top 3 LSG per (state, direction) and verify highest BE+fees selected."""
    print("\n" + "=" * 70)
    print("SECTION 5: BEST COMBO SELECTION")
    print("=" * 70)

    best_combos = find_best_lsg_per_state_direction(grouped)

    print(f"Best combos found: {len(best_combos)}")
    print(f"Expected: 1 per (state, direction)\n")

    # Show top 3 for one state×direction
    if not grouped.empty and len(grouped) > 0:
        # Pick first state×direction combo
        first_state = grouped.iloc[0]['bbw_state']
        first_dir = grouped.iloc[0]['direction']

        subset = grouped[
            (grouped['bbw_state'] == first_state) &
            (grouped['direction'] == first_dir)
        ].sort_values('be_plus_fees_rate', ascending=False).head(3)

        print(f"Example: {first_state} {first_dir} - Top 3 LSG Combos:\n")
        for idx, row in subset.iterrows():
            rank = subset.index.get_loc(idx) + 1
            marker = "[BEST]" if rank == 1 else ""
            print(f"{rank}. LSG ({row['leverage']}, {row['size']:.1f}, {row['grid']:.1f}): BE+fees={row['be_plus_fees_rate']:.3f} {marker}")
            print(f"   n_trades={row['n_trades']}, avg_net_pnl=${row['avg_net_pnl']:.2f}")

        # Verify best combo matches
        best_for_example = best_combos[
            (best_combos['bbw_state'] == first_state) &
            (best_combos['direction'] == first_dir)
        ]

        if len(best_for_example) == 1:
            selected_rate = best_for_example.iloc[0]['be_plus_fees_rate']
            max_rate = subset.iloc[0]['be_plus_fees_rate']
            if abs(selected_rate - max_rate) < 0.001:
                print(f"\n[PASS] Highest BE+fees rate selected: {max_rate:.3f}")
            else:
                print(f"\n[FAIL] Mismatch: selected={selected_rate:.3f}, max={max_rate:.3f}")


    return best_combos


# =============================================================================
# SECTION 6: DIRECTIONAL BIAS DETECTION
# =============================================================================

def section_6_directional_bias(best_combos):
    """Show bias calculations step-by-step."""
    print("\n" + "=" * 70)
    print("SECTION 6: DIRECTIONAL BIAS DETECTION")
    print("=" * 70)

    bias_df = detect_directional_bias(best_combos, bias_threshold=0.05)

    print(f"States analyzed: {len(bias_df)}\n")

    for idx, row in bias_df.iterrows():
        state = row['bbw_state']
        long_rate = row['long_be_fees_rate']
        short_rate = row['short_be_fees_rate']
        diff = row['difference']
        bias = row['bias']
        strength = row['bias_strength']

        print(f"{state}:")
        print(f"  LONG:       {long_rate if long_rate is not None else 'N/A'}")
        print(f"  SHORT:      {short_rate if short_rate is not None else 'N/A'}")
        print(f"  Difference: {diff if diff is not None else 'N/A'} (LONG - SHORT)")
        print(f"  Bias:       {bias}")
        print(f"  Strength:   {strength if strength is not None else 'N/A'}")
        print()

    # Bias distribution
    bias_dist = bias_df['bias'].value_counts()
    print("Bias Distribution:")
    for bias_type, count in bias_dist.items():
        print(f"  {bias_type:18s}: {count}")


# =============================================================================
# SECTION 7: COMMISSION KILL EXAMPLES
# =============================================================================

def section_7_commission_kill(grouped):
    """Find groups with gross > 0, net <= 0 (commission killed edge)."""
    print("\n" + "=" * 70)
    print("SECTION 7: COMMISSION KILL EXAMPLES")
    print("=" * 70)

    if grouped.empty:
        print("[SKIP] No groups to analyze")
        return

    # Find commission-killed groups
    killed = grouped[
        (grouped['avg_gross_pnl'] > 0) &
        (grouped['avg_net_pnl'] <= 0)
    ]

    print(f"Commission-killed groups: {len(killed)} / {len(grouped)}")
    if len(killed) > 0:
        kill_pct = (len(killed) / len(grouped)) * 100
        print(f"Kill percentage: {kill_pct:.1f}%\n")

        # Show top 5 by gross PnL
        top_killed = killed.nlargest(5, 'avg_gross_pnl')
        for idx, row in top_killed.iterrows():
            print(f"{row['bbw_state']} {row['direction']} LSG({row['leverage']}, {row['size']}, {row['grid']}):")
            print(f"  Avg Gross PnL: +${row['avg_gross_pnl']:.2f}")
            print(f"  Avg Net PnL:   ${row['avg_net_pnl']:.2f}")
            print(f"  Commission:    ${row['avg_commission']:.2f}")
            print(f"  Kill Amount:   ${row['avg_gross_pnl'] - row['avg_net_pnl']:.2f}")
            print()


# =============================================================================
# SECTION 8: PER-TRADE PNL PRESERVATION
# =============================================================================

def section_8_per_trade_pnl(best_combos, enriched):
    """Verify per_trade_pnl arrays match original trades."""
    print("\n" + "=" * 70)
    print("SECTION 8: PER-TRADE PNL PRESERVATION")
    print("=" * 70)

    if best_combos.empty:
        print("[SKIP] No best combos to validate")
        return

    # Check first best combo
    first_combo = best_combos.iloc[0]
    per_trade_pnl = first_combo['per_trade_pnl']

    print(f"First best combo: {first_combo['bbw_state']} {first_combo['direction']}")
    print(f"  n_trades:       {first_combo['n_trades']}")
    print(f"  per_trade_pnl:  {len(per_trade_pnl)} elements")

    # Validate length matches n_trades
    if len(per_trade_pnl) == first_combo['n_trades']:
        print(f"  [PASS] Length matches n_trades")
    else:
        print(f"  [FAIL] Length mismatch: {len(per_trade_pnl)} != {first_combo['n_trades']}")

    # Validate sum consistency
    total_pnl = sum(per_trade_pnl)
    expected_total = first_combo['total_net_pnl']
    if abs(total_pnl - expected_total) < 0.01:
        print(f"  [PASS] Sum matches total_net_pnl: ${total_pnl:.2f}")
    else:
        print(f"  [FAIL] Sum mismatch: ${total_pnl:.2f} != ${expected_total:.2f}")

    # Show first 5 PnL values
    print(f"\n  First 5 PnL values: {[round(p, 2) for p in per_trade_pnl[:5]]}")


# =============================================================================
# SECTION 9: SUMMARY STATISTICS
# =============================================================================

def section_9_summary_stats(result, trades):
    """Cross-check summary against raw backtester data."""
    print("\n" + "=" * 70)
    print("SECTION 9: SUMMARY STATISTICS")
    print("=" * 70)

    summary = result.summary

    print("Summary Statistics:")
    for key, value in summary.items():
        print(f"  {key:25s}: {value}")

    # Cross-check against raw data
    print("\nCross-Checks:")
    if summary['n_trades_analyzed'] == len(trades):
        print(f"[PASS] n_trades_analyzed matches raw data: {len(trades)}")
    else:
        print(f"[FAIL] n_trades_analyzed mismatch: {summary['n_trades_analyzed']} != {len(trades)}")

    if summary['n_groups'] == len(result.results):
        print(f"[PASS] n_groups matches results DataFrame: {len(result.results)}")
    else:
        print(f"[FAIL] n_groups mismatch: {summary['n_groups']} != {len(result.results)}")

    if summary['n_best_combos'] == len(result.best_combos):
        print(f"[PASS] n_best_combos matches best_combos DataFrame: {len(result.best_combos)}")
    else:
        print(f"[FAIL] n_best_combos mismatch: {summary['n_best_combos']} != {len(result.best_combos)}")


# =============================================================================
# SECTION 10: FULL PIPELINE TEST
# =============================================================================

def section_10_full_pipeline(trades, bbw_states):
    """Run full pipeline and validate output contract."""
    print("\n" + "=" * 70)
    print("SECTION 10: FULL PIPELINE TEST")
    print("=" * 70)

    result = analyze_bbw_patterns_v2(
        backtester_results=trades,
        bbw_states=bbw_states,
        symbol="RIVERUSDT",
        min_trades_per_group=5
    )

    print(f"Pipeline completed in {result.runtime_seconds:.3f} seconds")
    print(f"\nOutput Structure:")
    print(f"  results:           {len(result.results)} rows, {len(result.results.columns)} columns")
    print(f"  best_combos:       {len(result.best_combos)} rows, {len(result.best_combos.columns)} columns")
    print(f"  directional_bias:  {len(result.directional_bias)} rows, {len(result.directional_bias.columns)} columns")
    print(f"  summary:           {len(result.summary)} keys")

    # Validate contract
    print("\nOutput Contract Validation:")
    required_result_cols = ['bbw_state', 'direction', 'leverage', 'size', 'grid',
                            'n_trades', 'be_plus_fees_rate', 'per_trade_pnl']
    missing = [col for col in required_result_cols if col not in result.results.columns]
    if not missing:
        print(f"  [PASS] results has all required columns")
    else:
        print(f"  [FAIL] results missing columns: {missing}")

    required_summary_keys = ['symbol', 'n_trades_analyzed', 'n_states', 'runtime_seconds']
    missing = [key for key in required_summary_keys if key not in result.summary]
    if not missing:
        print(f"  [PASS] summary has all required keys")
    else:
        print(f"  [FAIL] summary missing keys: {missing}")

    return result


# =============================================================================
# MAIN RUNNER
# =============================================================================

def main():
    """Run all 10 debug sections."""
    print("\n" + "=" * 70)
    print("BBW ANALYZER V2 - DEBUG SCRIPT")
    print("10 Validation Sections")
    print("=" * 70)

    # Section 1: Input validation
    trades, bbw_states = section_1_input_validation()

    # Section 2: Enrichment verification
    enriched = section_2_enrichment_verification(trades, bbw_states)

    # Section 3: Grouping validation
    grouped = section_3_grouping_validation(enriched)

    # Section 4: BE+fees vs win rate
    section_4_be_fees_vs_win_rate(grouped)

    # Section 5: Best combo selection
    best_combos = section_5_best_combo_selection(grouped)

    # Section 6: Directional bias
    section_6_directional_bias(best_combos)

    # Section 7: Commission kill examples
    section_7_commission_kill(grouped)

    # Section 8: Per-trade PnL preservation
    section_8_per_trade_pnl(best_combos, enriched)

    # Section 10: Full pipeline test (includes Section 9)
    result = section_10_full_pipeline(trades, bbw_states)

    # Section 9: Summary stats (using result from Section 10)
    section_9_summary_stats(result, trades)

    print("\n" + "=" * 70)
    print("DEBUG SCRIPT COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
