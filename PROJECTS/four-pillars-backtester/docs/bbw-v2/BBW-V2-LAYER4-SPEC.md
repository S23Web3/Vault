# BBW V2 Layer 4 Build Specification (CORRECTED)
**File:** `research/bbw_simulator_v2.py`  
**Build Date:** 2026-02-16  
**Status:** Specification (Not Built)

---

## Overview

Layer 4 analyzes **existing backtester results** from backtester_v385, grouping trades by BBW state context to discover LSG effectiveness patterns. This is NOT a trade simulator - it's a results analyzer that enriches backtester data with BBW state information.

**Critical Clarification:**
- V1 spec (WRONG): Simulate new trades
- V2 spec (CORRECT): Analyze backtester_v385 results

---

## Input Contract

### Primary Input: Backtester Results

```python
def analyze_bbw_patterns_v2(
    backtester_results: pd.DataFrame,  # From backtester_v385 run
    bbw_states: pd.DataFrame,          # From Layer 2 (bbw_sequence.py)
    symbol: str = None,                # Optional filter
    min_trades_per_group: int = 100    # Minimum sample size
) -> BBWAnalysisResultV2
```

### backtester_results DataFrame

**Expected columns from backtester_v385:**
```python
Required columns:
- timestamp (datetime64[ns]): Trade entry timestamp
- symbol (str): Trading pair (e.g., 'RIVERUSDT')
- direction (str): 'LONG' or 'SHORT' (from Four Pillars strategy)
- entry_price (float): Entry price
- exit_price (float): Exit price
- leverage (int): Leverage used (5-20)
- size (float): Size multiplier (0.25-2.0)
- grid (float): Grid multiplier (1.0-3.0)
- outcome (str): 'TP', 'SL', or 'TIMEOUT'
- pnl_gross (float): PnL before commission
- pnl_net (float): PnL after commission
- commission_rt (float): Round-trip commission paid
- bars_held (int): Duration in bars
- [other strategy metrics...]

Validation rules:
- No missing timestamps
- direction must be 'LONG' or 'SHORT'
- leverage in [5, 20]
- size in [0.25, 2.0]
- grid in [1.0, 3.0]
```

**Where this data comes from:**
```
User runs: scripts/dashboard_v3.py
Dashboard executes: engine/backtester_v385.py
Backtester outputs: results/sweep_results.csv (or DataFrame)
BBW V2 reads: These results + adds BBW state context
```

### bbw_states DataFrame

**From Layer 2 (signals/bbw_sequence.py):**
```python
Required columns:
- timestamp (datetime64[ns])
- symbol (str)
- bbw_state (str): BLUE, BLUE_DOUBLE, GREEN, YELLOW, 
                   NORMAL, RED, RED_DOUBLE, 
                   MA_CROSS_UP, MA_CROSS_DOWN
- bbwp (float): BBWP percentile value (0-100)

Validation rules:
- Timestamps must align with backtester results
- States must be valid enum values
```

---

## Core Logic

### Step 1: Enrich Backtester Results with BBW State

```python
def enrich_with_bbw_state(
    trades: pd.DataFrame,
    bbw_states: pd.DataFrame
) -> pd.DataFrame:
    """
    Add BBW state at entry time to each trade.
    
    Logic:
    1. For each trade's entry timestamp
    2. Lookup BBW state at that timestamp
    3. Add as new column: bbw_state_at_entry
    
    Returns: trades DataFrame with bbw_state_at_entry column
    """
    
    # Merge on timestamp (aligned index)
    enriched = trades.merge(
        bbw_states[['timestamp', 'bbw_state', 'bbwp']],
        left_on='timestamp',
        right_on='timestamp',
        how='left'
    )
    
    # Rename for clarity
    enriched.rename(columns={
        'bbw_state': 'bbw_state_at_entry',
        'bbwp': 'bbwp_at_entry'
    }, inplace=True)
    
    # Drop trades without BBW state (shouldn't happen if data aligned)
    enriched = enriched.dropna(subset=['bbw_state_at_entry'])
    
    return enriched
```

### Step 2: Group by (State, Direction, LSG)

```python
def group_by_state_direction_lsg(
    enriched_trades: pd.DataFrame,
    min_trades: int = 100
) -> pd.DataFrame:
    """
    Group trades by BBW state, direction, and LSG parameters.
    
    Groups:
    - state: BBW state at entry
    - direction: LONG or SHORT
    - leverage: Leverage used
    - size: Size multiplier
    - grid: Grid multiplier
    
    Returns: Grouped metrics per combination
    """
    
    # Group by all dimensions
    grouped = enriched_trades.groupby([
        'bbw_state_at_entry',
        'direction',
        'leverage',
        'size',
        'grid'
    ]).apply(calculate_group_metrics)
    
    # Filter: Remove groups with insufficient trades
    grouped = grouped[grouped['n_trades'] >= min_trades]
    
    return grouped.reset_index()
```

### Step 3: Calculate Metrics per Group

```python
def calculate_group_metrics(group: pd.DataFrame) -> pd.Series:
    """
    Calculate performance metrics for a group of trades.
    
    Primary Metric: BE+fees rate (% trades with net_pnl >= 0)
    
    Returns: Series with aggregated metrics
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
```

### Step 4: Find Best LSG per (State, Direction)

```python
def find_best_lsg_per_state_direction(
    grouped_results: pd.DataFrame
) -> pd.DataFrame:
    """
    For each (state, direction) combo, find LSG with highest BE+fees rate.
    
    Returns: DataFrame with 1 row per (state, direction)
    """
    
    # Sort by BE+fees rate (descending)
    sorted_results = grouped_results.sort_values(
        by='be_plus_fees_rate',
        ascending=False
    )
    
    # Keep top combo per (state, direction)
    best_combos = sorted_results.groupby([
        'bbw_state_at_entry',
        'direction'
    ]).first().reset_index()
    
    return best_combos
```

### Step 5: Detect Directional Bias

```python
def detect_directional_bias(
    best_combos: pd.DataFrame,
    bias_threshold: float = 0.05  # 5% difference
) -> pd.DataFrame:
    """
    For each BBW state, determine if there's a directional bias.
    
    Bias types:
    - LONG: LONG BE+fees rate significantly > SHORT
    - SHORT: SHORT BE+fees rate significantly > LONG
    - NEUTRAL: Difference < threshold
    
    Returns: DataFrame with bias information per state
    """
    
    bias_results = []
    
    for state in best_combos['bbw_state_at_entry'].unique():
        state_data = best_combos[
            best_combos['bbw_state_at_entry'] == state
        ]
        
        # Get LONG and SHORT rates
        long_data = state_data[state_data['direction'] == 'LONG']
        short_data = state_data[state_data['direction'] == 'SHORT']
        
        if len(long_data) == 0 or len(short_data) == 0:
            # Missing direction data
            continue
        
        long_rate = long_data['be_plus_fees_rate'].iloc[0]
        short_rate = short_data['be_plus_fees_rate'].iloc[0]
        
        difference = short_rate - long_rate
        
        if abs(difference) < bias_threshold:
            bias = 'NEUTRAL'
        elif difference > 0:
            bias = 'SHORT'
        else:
            bias = 'LONG'
        
        bias_results.append({
            'bbw_state': state,
            'long_be_fees_rate': long_rate,
            'short_be_fees_rate': short_rate,
            'difference': difference,
            'bias': bias,
            'bias_strength': abs(difference)
        })
    
    return pd.DataFrame(bias_results)
```

---

## Output Contract

### BBWAnalysisResultV2 Class

```python
@dataclass
class BBWAnalysisResultV2:
    """
    Analysis results from backtester data grouped by BBW state.
    """
    
    # Full results: All (state, direction, LSG) combinations
    results: pd.DataFrame
    
    # Best LSG per (state, direction)
    best_combos: pd.DataFrame
    
    # Directional bias analysis
    directional_bias: pd.DataFrame
    
    # Summary statistics
    summary: dict
    
    # Metadata
    symbol: str
    n_trades_analyzed: int
    n_states: int
    date_range: tuple  # (start, end)
    runtime_seconds: float
```

### results DataFrame Columns

```python
results_columns = [
    # Grouping dimensions
    'bbw_state_at_entry',  # str: BBW state
    'direction',           # str: 'LONG' or 'SHORT'
    'leverage',            # int: 5-20
    'size',               # float: 0.25-2.0
    'grid',               # float: 1.0-3.0
    
    # Sample size
    'n_trades',           # int: Number of trades in group
    
    # Primary metrics
    'be_plus_fees_rate',  # float: PRIMARY - % achieving BE+fees
    'be_plus_fees_count', # int: Count achieving BE+fees
    'win_rate',           # float: For comparison (gross PnL > 0)
    
    # PnL metrics
    'avg_gross_pnl',      # float: Before commission
    'avg_net_pnl',        # float: After commission
    'total_net_pnl',      # float: Sum of all net PnLs
    
    # Commission
    'avg_commission',     # float: Average RT commission
    'commission_drag',    # float: gross - net average
    
    # Risk metrics
    'max_dd',             # float: Maximum drawdown
    'sharpe',             # float: Sharpe ratio
    'sortino',            # float: Sortino ratio
    
    # Outcome distribution
    'tp_count',           # int: TP hits
    'sl_count',           # int: SL hits
    'timeout_count',      # int: Timeouts
    
    # For Layer 4b
    'per_trade_pnl'       # list[float]: Individual net PnLs
]
```

### best_combos DataFrame

Same columns as `results`, but only 1 row per (state, direction) - the LSG combo with highest `be_plus_fees_rate`.

### directional_bias DataFrame

```python
directional_bias_columns = [
    'bbw_state',            # str: BBW state name
    'long_be_fees_rate',    # float: BE+fees rate for LONG
    'short_be_fees_rate',   # float: BE+fees rate for SHORT
    'difference',           # float: short - long
    'bias',                 # str: 'LONG', 'SHORT', 'NEUTRAL'
    'bias_strength'         # float: abs(difference)
]
```

### summary Dictionary

```python
summary_keys = {
    'symbol': str,
    'n_trades_analyzed': int,
    'n_unique_states': int,
    'n_state_direction_combos': int,
    'date_range_start': datetime,
    'date_range_end': datetime,
    'avg_be_plus_fees_rate': float,  # Across all groups
    'avg_win_rate': float,           # For comparison
    'states_with_long_bias': list,   # States favoring LONG
    'states_with_short_bias': list,  # States favoring SHORT
    'states_neutral': list,          # States with no bias
    'commission_kill_count': int,    # Groups where net <= 0
    'runtime_seconds': float
}
```

---

## Key Implementation Details

### 1. Data Alignment

**Critical:** BBW states and backtester results must be time-aligned.

```python
# Ensure both DataFrames use same datetime index
bbw_states = bbw_states.set_index('timestamp')
trades = trades.set_index('timestamp')

# Merge on index
enriched = trades.join(
    bbw_states[['bbw_state', 'bbwp']],
    how='left',
    rsuffix='_bbw'
)

# Verify no missing BBW states
missing_count = enriched['bbw_state'].isna().sum()
if missing_count > 0:
    logger.warning(f"{missing_count} trades missing BBW state data")
```

### 2. Performance Optimization

```python
# Use categorical dtypes for grouping
enriched['bbw_state_at_entry'] = enriched['bbw_state_at_entry'].astype('category')
enriched['direction'] = enriched['direction'].astype('category')

# Vectorize calculations where possible
def vectorized_be_fees_rate(group):
    """Faster than .apply() for simple calculations"""
    return (group['pnl_net'] >= 0).mean()

# Use numba for hot loops
from numba import jit

@jit(nopython=True)
def fast_drawdown(pnl_array):
    equity = np.cumsum(pnl_array)
    peak = np.maximum.accumulate(equity)
    dd = peak - equity
    return np.max(dd)
```

### 3. Memory Management

```python
# Don't duplicate per_trade_pnl for all groups
# Only store for best combos (needed by Layer 4b)

def calculate_group_metrics_light(group):
    """Lighter version without per_trade_pnl"""
    metrics = calculate_group_metrics(group)
    del metrics['per_trade_pnl']  # Save memory
    return metrics

# Full metrics only for best combos
best_combos_full = best_combos.groupby([
    'bbw_state_at_entry', 'direction'
]).apply(lambda g: g)  # Keep per_trade_pnl
```

### 4. Missing Data Handling

```python
# Handle states with only LONG or SHORT trades
def safe_bias_detection(state_data):
    """Gracefully handle missing directions"""
    
    long_data = state_data[state_data['direction'] == 'LONG']
    short_data = state_data[state_data['direction'] == 'SHORT']
    
    if len(long_data) == 0:
        logger.warning(f"State {state}: No LONG trades found")
        return {
            'bias': 'SHORT_ONLY',
            'long_be_fees_rate': None,
            'short_be_fees_rate': short_data['be_plus_fees_rate'].iloc[0]
        }
    
    if len(short_data) == 0:
        logger.warning(f"State {state}: No SHORT trades found")
        return {
            'bias': 'LONG_ONLY',
            'long_be_fees_rate': long_data['be_plus_fees_rate'].iloc[0],
            'short_be_fees_rate': None
        }
    
    # Both directions present
    return calculate_bias(long_data, short_data)
```

---

## Test Requirements

### Unit Tests (40+ tests required)

**Category 1: Data Enrichment (8 tests)**
- test_enrich_with_bbw_state_aligned_data
- test_enrich_with_bbw_state_missing_states
- test_enrich_with_bbw_state_misaligned_timestamps
- test_enrich_handles_duplicate_timestamps
- test_enrich_preserves_original_columns
- test_enrich_drops_trades_without_state
- test_enrich_state_column_naming
- test_enrich_bbwp_column_added

**Category 2: Grouping Logic (10 tests)**
- test_group_by_state_direction_lsg
- test_group_min_trades_filter
- test_group_unique_combinations
- test_group_empty_input
- test_group_single_state
- test_group_single_direction
- test_group_single_lsg
- test_group_preserves_all_lsg_combos
- test_group_categorical_dtypes
- test_group_index_reset

**Category 3: Metrics Calculation (12 tests)**
- test_be_plus_fees_rate_all_positive
- test_be_plus_fees_rate_all_negative
- test_be_plus_fees_rate_mixed
- test_be_plus_fees_rate_exactly_zero
- test_be_plus_fees_vs_win_rate_divergence
- test_commission_drag_calculation
- test_max_dd_calculation
- test_sharpe_calculation
- test_sortino_calculation
- test_outcome_distribution_counts
- test_per_trade_pnl_preservation
- test_empty_group_handling

**Category 4: Best Combo Selection (8 tests)**
- test_best_lsg_single_state_direction
- test_best_lsg_multiple_states
- test_best_lsg_tie_breaking
- test_best_lsg_one_row_per_state_direction
- test_best_lsg_preserves_per_trade_pnl
- test_best_lsg_highest_be_fees_rate
- test_best_lsg_handles_missing_direction
- test_best_lsg_all_states_present

**Category 5: Directional Bias (8 tests)**
- test_bias_long_favored
- test_bias_short_favored
- test_bias_neutral
- test_bias_threshold_edge_cases
- test_bias_missing_long_direction
- test_bias_missing_short_direction
- test_bias_strength_calculation
- test_bias_all_states_analyzed

**Category 6: Integration (5+ tests)**
- test_full_pipeline_single_symbol
- test_full_pipeline_multi_symbol
- test_full_pipeline_matches_backtester_count
- test_full_pipeline_output_contract
- test_layer4_to_layer4b_contract

---

## Debug/Sanity Checks

### Debug Script: scripts/debug_bbw_analyzer_v2.py

**Sections (10+):**

1. **Input Data Validation**
   - Verify backtester results structure
   - Check BBW states alignment
   - Validate timestamp overlap

2. **Enrichment Verification**
   - Hand-check BBW state assignment
   - Verify no data loss during merge
   - Confirm state distribution

3. **Grouping Validation**
   - Count groups per state
   - Verify LSG combinations present
   - Check min_trades filtering

4. **BE+fees vs Win Rate Comparison**
   - Show examples where they diverge
   - Demonstrate commission impact
   - Validate metric calculation

5. **Best Combo Selection**
   - Show top 3 LSG per (state, direction)
   - Verify highest BE+fees selected
   - Check tie-breaking logic

6. **Directional Bias Detection**
   - Show bias calculations step-by-step
   - Verify threshold logic
   - Display bias strength distribution

7. **Commission Kill Examples**
   - Find groups with gross > 0, net <= 0
   - Calculate commission drag
   - Show kill percentage

8. **Per-trade PnL Preservation**
   - Verify arrays match original trades
   - Check sum consistency
   - Validate for Layer 4b handoff

9. **Summary Statistics**
   - Cross-check against raw backtester data
   - Verify date range accuracy
   - Validate state counts

10. **Multi-coin Consistency**
    - Run on RIVER, AXS, KITE
    - Compare patterns across coins
    - Check for data quality issues

### Sanity Check Script: scripts/sanity_check_bbw_analyzer_v2.py

**Must validate:**

1. **RIVERUSDT Full Analysis**
   - Use actual backtester results from dashboard
   - Process all states, both directions
   - Verify output contract compliance

2. **Data Integrity**
   - Input trade count = output trade count
   - No data loss during enrichment
   - All BBW states represented

3. **Metric Accuracy**
   - BE+fees rate manually verified (sample)
   - Commission calculations correct
   - Directional bias matches expectations

4. **Output Quality**
   - Best combo per (state, direction) present
   - Directional bias analysis complete
   - Summary statistics accurate

5. **Performance**
   - Runtime < 5 seconds for RIVERUSDT
   - Memory usage reasonable
   - CSV export successful

6. **Layer 4b Readiness**
   - Per-trade PnL available for best combos
   - Output DataFrame has required columns
   - Contract matches Layer 4b expectations

---

## File Structure

```
research/
└── bbw_analyzer_v2.py          (~400-500 lines)
    ├── Classes
    │   └── BBWAnalysisResultV2 (dataclass)
    ├── Core Functions
    │   ├── analyze_bbw_patterns_v2()
    │   ├── enrich_with_bbw_state()
    │   ├── group_by_state_direction_lsg()
    │   ├── calculate_group_metrics()
    │   ├── find_best_lsg_per_state_direction()
    │   └── detect_directional_bias()
    ├── Helper Functions
    │   ├── validate_backtester_data()
    │   ├── validate_bbw_states()
    │   ├── calculate_max_drawdown()
    │   ├── calculate_sharpe()
    │   └── calculate_sortino()
    └── Main Execution
        └── if __name__ == '__main__': sanity test

tests/
└── test_bbw_analyzer_v2.py     (~500-600 lines)
    ├── Data Enrichment Tests (8)
    ├── Grouping Tests (10)
    ├── Metrics Tests (12)
    ├── Best Combo Tests (8)
    ├── Directional Bias Tests (8)
    └── Integration Tests (5+)

scripts/
├── debug_bbw_analyzer_v2.py    (~400-500 lines)
│   └── 10 debug sections
└── sanity_check_bbw_analyzer_v2.py  (~200-250 lines)
    └── RIVERUSDT full pipeline validation
```

---

## Build Order

1. **Input Validation** (30 min)
   - validate_backtester_data()
   - validate_bbw_states()
   - Unit tests

2. **Data Enrichment** (45 min)
   - enrich_with_bbw_state()
   - Timestamp alignment logic
   - Unit tests

3. **Grouping** (45 min)
   - group_by_state_direction_lsg()
   - Min trades filtering
   - Unit tests

4. **Metrics Calculation** (60 min)
   - calculate_group_metrics()
   - BE+fees rate calculation
   - Risk metrics
   - Unit tests

5. **Best Combo Selection** (30 min)
   - find_best_lsg_per_state_direction()
   - Tie-breaking logic
   - Unit tests

6. **Directional Bias** (45 min)
   - detect_directional_bias()
   - Threshold logic
   - Unit tests

7. **Main Pipeline** (45 min)
   - analyze_bbw_patterns_v2()
   - Output assembly
   - Integration tests

8. **Debug Script** (90 min)
   - 10 debug sections
   - Hand-computed validations

9. **Sanity Script** (60 min)
   - RIVERUSDT full pipeline
   - Output validation

10. **Documentation** (30 min)
    - Docstrings
    - Code comments
    - Usage examples

**Total Estimate:** 7-8 hours

---

## Success Criteria

### Code Complete When:
- [✅] All 40+ unit tests PASS
- [✅] Debug script 10/10 sections PASS
- [✅] Sanity check RIVERUSDT CLEAN
- [✅] Enrichment preserves all backtester trades
- [✅] BE+fees rate != win rate demonstrated
- [✅] Directional bias detected for at least 3 states
- [✅] Commission kill scenarios identified
- [✅] Output contract matches Layer 4b expectations
- [✅] Runtime < 5 seconds for RIVERUSDT
- [✅] Code coverage > 90%

### Ready for Layer 4b When:
- [✅] Per-trade PnL available for best combos
- [✅] State × direction results complete
- [✅] BE+fees rate as primary metric
- [✅] Output DataFrame has required columns
- [✅] Multi-coin validation successful

---

## Related Documents

- **BBW-V2-ARCHITECTURE.md** - Overall V2 design (needs revision)
- **BBW-V2-UML.mmd** - System flow diagram (needs revision)
- **BBW-V2-LAYER4B-SPEC.md** - Layer 4b specification (next)
- **2026-02-16-bbw-v2-fundamental-corrections.md** - Session log
