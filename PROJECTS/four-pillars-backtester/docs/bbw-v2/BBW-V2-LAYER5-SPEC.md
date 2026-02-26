# BBW V2 Layer 5 Build Specification
**File:** `research/bbw_report_v2.py`  
**Build Date:** 2026-02-16  
**Status:** Specification (Not Built)

---

## Overview

Layer 5 aggregates Layer 4 and 4b results to generate **VINCE training features** and analysis reports. This is a pure data transformation layer - no ML, no trading decisions, just feature engineering and aggregation.

**Critical:** Layer 5 does NOT contain VINCE ML logic. VINCE is a separate component.

---

## Input Contract

### Primary Inputs

```python
def generate_vince_features_v2(
    analysis_results: BBWAnalysisResultV2,    # From Layer 4
    mc_results: MonteCarloResultV2,           # From Layer 4b
    output_dir: str = 'results/bbw_v2/'
) -> BBWReportResultV2
```

### analysis_results (from Layer 4)

**BBWAnalysisResultV2 attributes:**
```python
- results: pd.DataFrame
  - All (state, direction, LSG) combinations
  - BE+fees rates, PnL metrics, risk metrics
  
- best_combos: pd.DataFrame
  - Top LSG per (state, direction)
  - Highest BE+fees rate selections
  
- directional_bias: pd.DataFrame
  - LONG vs SHORT comparison per state
  - Bias strength and direction
  
- summary: dict
  - Overall statistics
```

### mc_results (from Layer 4b)

**MonteCarloResultV2 attributes:**
```python
- state_verdicts: pd.DataFrame
  - Verdict per (state, direction)
  - ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT
  
- confidence_intervals: pd.DataFrame
  - Bootstrap PnL CIs
  - Permutation DD/MCL percentiles
  
- overfit_flags: pd.DataFrame
  - Overfit detection flags
  - Reasons for flags
```

---

## Core Logic

### Step 1: Aggregate Directional Bias

```python
def aggregate_directional_bias(
    best_combos: pd.DataFrame,
    mc_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """
    Aggregate directional effectiveness per BBW state.
    
    Output columns:
    - bbw_state
    - long_be_fees_rate
    - short_be_fees_rate
    - long_verdict (ROBUST/FRAGILE/etc.)
    - short_verdict
    - bias_direction (LONG/SHORT/NEUTRAL)
    - bias_strength (abs difference)
    - confidence (based on sample sizes + verdicts)
    """
    
    bias_data = []
    
    for state in best_combos['bbw_state_at_entry'].unique():
        state_data = best_combos[
            best_combos['bbw_state_at_entry'] == state
        ]
        
        # Get LONG metrics
        long_data = state_data[state_data['direction'] == 'LONG']
        short_data = state_data[state_data['direction'] == 'SHORT']
        
        if len(long_data) == 0 or len(short_data) == 0:
            continue
        
        long_rate = long_data['be_plus_fees_rate'].iloc[0]
        short_rate = short_data['be_plus_fees_rate'].iloc[0]
        
        # Get verdicts
        long_verdict = mc_verdicts[
            (mc_verdicts['state'] == state) & 
            (mc_verdicts['direction'] == 'LONG')
        ]['verdict'].iloc[0]
        
        short_verdict = mc_verdicts[
            (mc_verdicts['state'] == state) & 
            (mc_verdicts['direction'] == 'SHORT')
        ]['verdict'].iloc[0]
        
        # Calculate bias
        difference = short_rate - long_rate
        
        if abs(difference) < 0.05:  # 5% threshold
            bias = 'NEUTRAL'
        elif difference > 0:
            bias = 'SHORT'
        else:
            bias = 'LONG'
        
        # Confidence: Both ROBUST = high, one FRAGILE = medium, both FRAGILE = low
        if long_verdict == 'ROBUST' and short_verdict == 'ROBUST':
            confidence = 'HIGH'
        elif long_verdict == 'FRAGILE' and short_verdict == 'FRAGILE':
            confidence = 'LOW'
        else:
            confidence = 'MEDIUM'
        
        bias_data.append({
            'bbw_state': state,
            'long_be_fees_rate': long_rate,
            'short_be_fees_rate': short_rate,
            'long_verdict': long_verdict,
            'short_verdict': short_verdict,
            'bias_direction': bias,
            'bias_strength': abs(difference),
            'confidence': confidence
        })
    
    return pd.DataFrame(bias_data)
```

### Step 2: Generate BE+fees Success Tables

```python
def generate_be_fees_success_tables(
    best_combos: pd.DataFrame,
    mc_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """
    Create comprehensive BE+fees success rate tables.
    
    One row per (state, direction) with:
    - BE+fees rate
    - Sample size
    - Verdict
    - LSG parameters
    - Commission impact
    """
    
    success_data = []
    
    for _, row in best_combos.iterrows():
        state = row['bbw_state_at_entry']
        direction = row['direction']
        
        # Get verdict
        verdict = mc_verdicts[
            (mc_verdicts['state'] == state) & 
            (mc_verdicts['direction'] == direction)
        ]['verdict'].iloc[0]
        
        success_data.append({
            'state': state,
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
    
    return pd.DataFrame(success_data)
```

### Step 3: Create VINCE Feature Candidates

```python
def create_vince_features(
    best_combos: pd.DataFrame,
    directional_bias: pd.DataFrame,
    mc_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate feature vectors for VINCE ML training.
    
    One row per (state, direction) representing a training example.
    
    Features:
    - State encoding (one-hot or ordinal)
    - Direction encoding (binary)
    - Historical LSG parameters
    - Success metrics
    - Confidence indicators
    
    Targets:
    - BE+fees rate (primary)
    - Net PnL
    - Verdict (classification)
    """
    
    features = []
    
    for _, row in best_combos.iterrows():
        state = row['bbw_state_at_entry']
        direction = row['direction']
        
        # Get bias info
        bias_row = directional_bias[
            directional_bias['bbw_state'] == state
        ]
        
        if len(bias_row) == 0:
            continue
        
        bias = bias_row.iloc[0]
        
        # Get verdict
        verdict = mc_verdicts[
            (mc_verdicts['state'] == state) & 
            (mc_verdicts['direction'] == direction)
        ]['verdict'].iloc[0]
        
        # State encoding (ordinal based on volatility)
        state_ordinal = {
            'BLUE': 1, 'BLUE_DOUBLE': 2,
            'GREEN': 3, 'YELLOW': 4, 'NORMAL': 5,
            'RED': 6, 'RED_DOUBLE': 7,
            'MA_CROSS_UP': 8, 'MA_CROSS_DOWN': 9
        }.get(state, 0)
        
        # Direction encoding
        direction_binary = 1 if direction == 'LONG' else 0
        
        # Verdict encoding
        verdict_ordinal = {
            'ROBUST': 3,
            'MARGINAL': 2,
            'FRAGILE': 1,
            'COMMISSION_KILL': 0,
            'INSUFFICIENT_DATA': -1
        }.get(verdict, -1)
        
        features.append({
            # Identifiers
            'state': state,
            'direction': direction,
            
            # Feature: State encoding
            'feature_state_ordinal': state_ordinal,
            'feature_state_blue': 1 if 'BLUE' in state else 0,
            'feature_state_red': 1 if 'RED' in state else 0,
            'feature_state_double': 1 if 'DOUBLE' in state else 0,
            
            # Feature: Direction
            'feature_direction_long': direction_binary,
            
            # Feature: Bias context
            'feature_bias_aligned': 1 if (
                (direction == 'LONG' and bias['bias_direction'] == 'LONG') or
                (direction == 'SHORT' and bias['bias_direction'] == 'SHORT')
            ) else 0,
            'feature_bias_strength': bias['bias_strength'],
            
            # Feature: Historical LSG
            'feature_leverage': row['leverage'],
            'feature_size': row['size'],
            'feature_grid': row['grid'],
            
            # Feature: Sample quality
            'feature_n_trades': row['n_trades'],
            'feature_verdict_ordinal': verdict_ordinal,
            
            # Target: Primary
            'target_be_plus_fees_rate': row['be_plus_fees_rate'],
            
            # Target: Secondary
            'target_avg_net_pnl': row['avg_net_pnl'],
            'target_sharpe': row['sharpe'],
            'target_verdict': verdict,
            
            # Weight: For ML training
            'sample_weight': 1.0 if verdict == 'ROBUST' else 0.5
        })
    
    return pd.DataFrame(features)
```

### Step 4: LSG Sensitivity Analysis

```python
def analyze_lsg_sensitivity(
    all_results: pd.DataFrame,
    best_combos: pd.DataFrame
) -> pd.DataFrame:
    """
    Analyze how BE+fees rate changes with LSG parameters.
    
    For each (state, direction):
    - How sensitive is BE+fees to leverage changes?
    - How sensitive to size changes?
    - How sensitive to grid changes?
    
    Output: Sensitivity coefficients per parameter.
    """
    
    sensitivity_data = []
    
    for state in all_results['bbw_state_at_entry'].unique():
        for direction in ['LONG', 'SHORT']:
            subset = all_results[
                (all_results['bbw_state_at_entry'] == state) &
                (all_results['direction'] == direction)
            ]
            
            if len(subset) < 3:
                continue
            
            # Calculate correlations
            lev_corr = subset[['leverage', 'be_plus_fees_rate']].corr().iloc[0, 1]
            size_corr = subset[['size', 'be_plus_fees_rate']].corr().iloc[0, 1]
            grid_corr = subset[['grid', 'be_plus_fees_rate']].corr().iloc[0, 1]
            
            # Get best combo for reference
            best = best_combos[
                (best_combos['bbw_state_at_entry'] == state) &
                (best_combos['direction'] == direction)
            ]
            
            if len(best) == 0:
                continue
            
            best = best.iloc[0]
            
            sensitivity_data.append({
                'state': state,
                'direction': direction,
                'best_leverage': best['leverage'],
                'best_size': best['size'],
                'best_grid': best['grid'],
                'leverage_sensitivity': lev_corr,
                'size_sensitivity': size_corr,
                'grid_sensitivity': grid_corr,
                'dominant_parameter': max(
                    [('leverage', abs(lev_corr)),
                     ('size', abs(size_corr)),
                     ('grid', abs(grid_corr))],
                    key=lambda x: x[1]
                )[0]
            })
    
    return pd.DataFrame(sensitivity_data)
```

### Step 5: State Summary Report

```python
def generate_state_summary(
    directional_bias: pd.DataFrame,
    be_fees_success: pd.DataFrame,
    mc_verdicts: pd.DataFrame
) -> pd.DataFrame:
    """
    High-level summary per BBW state.
    
    One row per state with:
    - Overall performance
    - Directional bias
    - Best direction
    - Sample quality
    """
    
    summary_data = []
    
    for state in directional_bias['bbw_state'].unique():
        bias_row = directional_bias[
            directional_bias['bbw_state'] == state
        ].iloc[0]
        
        success_subset = be_fees_success[
            be_fees_success['state'] == state
        ]
        
        # Overall metrics
        total_trades = success_subset['n_trades'].sum()
        avg_be_fees = success_subset['be_plus_fees_rate'].mean()
        
        # Verdict counts
        verdicts = success_subset['verdict'].value_counts().to_dict()
        
        summary_data.append({
            'state': state,
            'total_trades': total_trades,
            'avg_be_plus_fees_rate': avg_be_fees,
            'bias_direction': bias_row['bias_direction'],
            'bias_strength': bias_row['bias_strength'],
            'confidence': bias_row['confidence'],
            'n_robust': verdicts.get('ROBUST', 0),
            'n_fragile': verdicts.get('FRAGILE', 0),
            'n_commission_kill': verdicts.get('COMMISSION_KILL', 0),
            'best_direction': 'LONG' if bias_row['long_be_fees_rate'] > bias_row['short_be_fees_rate'] else 'SHORT'
        })
    
    return pd.DataFrame(summary_data)
```

---

## Output Contract

### BBWReportResultV2 Class

```python
@dataclass
class BBWReportResultV2:
    """
    Complete reporting output with VINCE features.
    """
    
    # VINCE training features (PRIMARY OUTPUT)
    vince_features: pd.DataFrame
    
    # Analysis reports
    directional_bias: pd.DataFrame
    be_fees_success: pd.DataFrame
    lsg_sensitivity: pd.DataFrame
    state_summary: pd.DataFrame
    
    # Metadata
    symbol: str
    n_states: int
    n_features_generated: int
    output_files: dict  # Mapping of report name to file path
    runtime_seconds: float
```

### Output CSV Files

**1. bbw_vince_features.csv** (PRIMARY - for VINCE training)
```python
Columns:
- state, direction (identifiers)
- feature_state_ordinal (1-9)
- feature_state_blue (0/1)
- feature_state_red (0/1)
- feature_state_double (0/1)
- feature_direction_long (0/1)
- feature_bias_aligned (0/1)
- feature_bias_strength (0.0-1.0)
- feature_leverage (5-20)
- feature_size (0.25-2.0)
- feature_grid (1.0-3.0)
- feature_n_trades (int)
- feature_verdict_ordinal (-1 to 3)
- target_be_plus_fees_rate (0.0-1.0)
- target_avg_net_pnl (float)
- target_sharpe (float)
- target_verdict (str)
- sample_weight (0.5 or 1.0)
```

**2. bbw_directional_bias.csv**
```python
Columns:
- bbw_state
- long_be_fees_rate
- short_be_fees_rate
- long_verdict
- short_verdict
- bias_direction (LONG/SHORT/NEUTRAL)
- bias_strength (0.0-1.0)
- confidence (HIGH/MEDIUM/LOW)
```

**3. bbw_be_fees_success.csv**
```python
Columns:
- state, direction
- leverage, size, grid (best LSG)
- n_trades
- be_plus_fees_rate
- win_rate
- rate_divergence (be_fees - win)
- avg_net_pnl
- avg_commission
- commission_drag
- verdict
- sharpe
- max_dd
```

**4. bbw_lsg_sensitivity.csv**
```python
Columns:
- state, direction
- best_leverage, best_size, best_grid
- leverage_sensitivity (correlation)
- size_sensitivity
- grid_sensitivity
- dominant_parameter (which LSG param matters most)
```

**5. bbw_state_summary.csv**
```python
Columns:
- state
- total_trades
- avg_be_plus_fees_rate
- bias_direction
- bias_strength
- confidence
- n_robust
- n_fragile
- n_commission_kill
- best_direction
```

---

## Test Requirements

### Unit Tests (30+ tests required)

**Category 1: Directional Bias Aggregation (8 tests)**
- test_bias_aggregation_neutral_state
- test_bias_aggregation_long_favored
- test_bias_aggregation_short_favored
- test_bias_confidence_both_robust
- test_bias_confidence_both_fragile
- test_bias_confidence_mixed
- test_bias_missing_direction_handling
- test_bias_threshold_edge_cases

**Category 2: BE+fees Success Tables (6 tests)**
- test_success_table_all_states
- test_success_table_rate_divergence
- test_success_table_commission_impact
- test_success_table_verdict_integration
- test_success_table_column_completeness
- test_success_table_sorting

**Category 3: VINCE Features (10 tests)**
- test_vince_features_state_encoding
- test_vince_features_direction_encoding
- test_vince_features_bias_alignment
- test_vince_features_lsg_inclusion
- test_vince_features_target_variables
- test_vince_features_sample_weights
- test_vince_features_robust_weighting
- test_vince_features_no_missing_values
- test_vince_features_ordinal_ranges
- test_vince_features_row_count_matches_combos

**Category 4: LSG Sensitivity (6 tests)**
- test_lsg_sensitivity_correlation_calculation
- test_lsg_sensitivity_dominant_parameter
- test_lsg_sensitivity_all_directions
- test_lsg_sensitivity_insufficient_data_skip
- test_lsg_sensitivity_best_combo_reference
- test_lsg_sensitivity_nan_handling

**Category 5: State Summary (5 tests)**
- test_state_summary_all_states_present
- test_state_summary_verdict_counts
- test_state_summary_best_direction_selection
- test_state_summary_metrics_aggregation
- test_state_summary_confidence_propagation

**Category 6: Integration (5+ tests)**
- test_full_pipeline_csv_generation
- test_full_pipeline_all_files_created
- test_full_pipeline_row_counts_consistent
- test_full_pipeline_vince_features_complete
- test_layer5_to_vince_contract

---

## File Structure

```
research/
└── bbw_report_v2.py            (~400-500 lines)
    ├── Classes
    │   └── BBWReportResultV2 (dataclass)
    ├── Core Functions
    │   ├── generate_vince_features_v2()
    │   ├── aggregate_directional_bias()
    │   ├── generate_be_fees_success_tables()
    │   ├── create_vince_features()
    │   ├── analyze_lsg_sensitivity()
    │   └── generate_state_summary()
    ├── Helper Functions
    │   ├── validate_layer4_results()
    │   ├── validate_layer4b_results()
    │   ├── encode_state()
    │   ├── encode_direction()
    │   └── calculate_sample_weight()
    └── Main Execution
        └── if __name__ == '__main__': sanity test

tests/
└── test_bbw_report_v2.py       (~400-500 lines)
    ├── Directional Bias Tests (8)
    ├── BE+fees Success Tests (6)
    ├── VINCE Features Tests (10)
    ├── LSG Sensitivity Tests (6)
    ├── State Summary Tests (5)
    └── Integration Tests (5+)

scripts/
└── sanity_check_bbw_report_v2.py  (~150-200 lines)
    └── RIVERUSDT full pipeline validation
```

---

## Build Order

1. **Input Validation** (20 min)
   - validate_layer4_results()
   - validate_layer4b_results()
   - Unit tests

2. **Directional Bias** (45 min)
   - aggregate_directional_bias()
   - Confidence logic
   - Unit tests

3. **BE+fees Tables** (30 min)
   - generate_be_fees_success_tables()
   - Rate divergence calculation
   - Unit tests

4. **VINCE Features** (90 min)
   - create_vince_features()
   - State/direction encoding
   - Sample weighting
   - Unit tests

5. **LSG Sensitivity** (45 min)
   - analyze_lsg_sensitivity()
   - Correlation calculations
   - Unit tests

6. **State Summary** (30 min)
   - generate_state_summary()
   - Aggregations
   - Unit tests

7. **Main Pipeline** (45 min)
   - generate_vince_features_v2()
   - CSV export
   - Integration tests

8. **Sanity Script** (45 min)
   - RIVERUSDT full pipeline
   - CSV validation

9. **Documentation** (30 min)
   - Docstrings
   - Usage examples

**Total Estimate:** 6-7 hours

---

## Success Criteria

### Code Complete When:
- [✅] All 30+ unit tests PASS
- [✅] Sanity check RIVERUSDT CLEAN
- [✅] All 5 CSV files generated
- [✅] VINCE features complete and valid
- [✅] No BBW_LSG_MAP logic present
- [✅] Directional bias for all states
- [✅] Output contract matches VINCE expectations
- [✅] Code coverage > 90%

### Ready for VINCE When:
- [✅] vince_features.csv complete
- [✅] Feature encoding validated
- [✅] Sample weights assigned
- [✅] Target variables present
- [✅] No missing values in features

---

## Related Documents

- **BBW-V2-ARCHITECTURE.md** - Overall V2 design (updated)
- **BBW-V2-UML.mmd** - System flow diagram (updated)
- **BBW-V2-LAYER4-SPEC.md** - Layer 4 specification (corrected)
- **BBW-V2-LAYER4B-SPEC.md** - Layer 4b specification (future)
- **2026-02-16-bbw-v2-fundamental-corrections.md** - Session log
