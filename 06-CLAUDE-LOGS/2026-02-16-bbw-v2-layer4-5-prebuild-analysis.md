# BBW V2 Layers 4 & 5 Pre-Build Analysis
**Date:** 2026-02-16
**Session:** Pre-Build Architecture Review
**Status:** Analysis Complete, Ready for Build

---

## Executive Summary

BBW V1 was fundamentally flawed - it simulated trades instead of analyzing backtester results. BBW V2 corrects this by analyzing **existing backtester_v385 results** grouped by BBW volatility state context to generate VINCE training features.

**Critical Corrections Applied:**
1. Trade source: Backtester results (NOT OHLC simulation)
2. Direction source: Four Pillars strategy (NOT BBW testing)
3. VINCE: Separate ML component (NOT Layer 6)
4. BBW purpose: Data generator for VINCE (NOT decision engine)

---

## Architecture Overview

### Data Flow (Corrected)

```
EXISTING SYSTEM (Unchanged):
┌─────────────────────────────────────────┐
│ Dashboard v3                            │
│ ├─ 400+ coins, year of data            │
│ ├─ 93% success rate                    │
│ └─ Executes backtester_v385            │
└────────────┬────────────────────────────┘
             │
             v
┌─────────────────────────────────────────┐
│ Backtester v385 (Four Pillars Strategy)│
│ ├─ Stochastics: Entry timing           │
│ ├─ Ripster: Trend confirmation         │
│ ├─ AVWAP: Trailing TP activation       │
│ ├─ BBW: Volatility context (future)    │
│ └─ Output: Trade results DataFrame     │
│    - timestamp, symbol, direction       │
│    - entry_price, exit_price, outcome   │
│    - pnl_gross, pnl_net, commission_rt  │
│    - leverage, size, grid               │
└────────────┬────────────────────────────┘
             │
             │ Trade results + BBW states
             v
┌─────────────────────────────────────────┐
│ BBW V2 ANALYSIS (This Build)           │
│                                         │
│ Layer 4: bbw_analyzer_v2.py            │
│ ├─ Enrich trades with BBW state        │
│ ├─ Group by (state, direction, LSG)    │
│ ├─ Calculate BE+fees rate per group    │
│ ├─ Find best LSG per (state, direction)│
│ └─ Detect directional bias             │
│                                         │
│ Layer 4b: bbw_monte_carlo_v2.py        │
│ ├─ Bootstrap PnL confidence intervals  │
│ ├─ Permutation DD/MCL robustness       │
│ ├─ Verdict assignment per state×dir    │
│ └─ Overfit detection                   │
│                                         │
│ Layer 5: bbw_report_v2.py              │
│ ├─ Aggregate directional bias          │
│ ├─ Generate VINCE feature CSVs         │
│ ├─ BE+fees success tables              │
│ └─ LSG sensitivity reports             │
└────────────┬────────────────────────────┘
             │
             │ VINCE training features
             v
┌─────────────────────────────────────────┐
│ VINCE ML (Future - Separate Component) │
│ ml/vince_model.py                       │
│ ├─ Learns optimal LSG from 4 pillars   │
│ ├─ BBW + Ripster + AVWAP + Stochastics │
│ └─ Real-time LSG optimization          │
└─────────────────────────────────────────┘
```

---

## Core Logic Analysis

### Layer 4: BBW Analyzer V2

**Purpose:** Analyze backtester results grouped by BBW state context.

**Input Contract:**
```python
def analyze_bbw_patterns_v2(
    backtester_results: pd.DataFrame,  # From backtester_v385
    bbw_states: pd.DataFrame,          # From Layer 2
    symbol: str = None,
    min_trades_per_group: int = 100
) -> BBWAnalysisResultV2
```

**Critical Logic Steps:**

1. **Enrich Backtester Results** (Step 1)
   - Merge trades with BBW states on timestamp
   - Add `bbw_state_at_entry` column to each trade
   - Validation: No data loss during merge

   **Math Validation:**
   ```python
   n_trades_input = len(backtester_results)
   n_trades_enriched = len(enriched_df)

   # MUST BE TRUE:
   assert n_trades_enriched == n_trades_input, \
       "Data loss during enrichment"

   # MUST NOT HAVE NULLS:
   assert enriched_df['bbw_state_at_entry'].isna().sum() == 0, \
       "Missing BBW states after enrichment"
   ```

2. **Group by (State, Direction, LSG)** (Step 2)
   - Group dimensions: [state, direction, leverage, size, grid]
   - Filter: n_trades >= min_trades_per_group

   **Logic Validation:**
   ```python
   # Example grouping:
   # state='BLUE', direction='LONG', lev=10, size=1.0, grid=1.5
   #   -> n_trades=4575, be_fees_rate=0.68

   # state='BLUE', direction='SHORT', lev=10, size=1.0, grid=1.5
   #   -> n_trades=4575, be_fees_rate=0.72

   # Direction from strategy, not from BBW state logic
   ```

3. **Calculate BE+fees Rate** (Step 3 - PRIMARY METRIC)
   - Definition: % of trades where `pnl_net >= 0`
   - Critical: Commission already deducted in `pnl_net`

   **Math Validation:**
   ```python
   # Example trade:
   pnl_gross = +$7.50
   commission_rt = $8.00  # 0.0008 * 2 sides * notional
   pnl_net = pnl_gross - commission_rt = -$0.50

   # V1 (WRONG): Win if pnl_gross > 0 → Counts as WIN
   # V2 (CORRECT): Win if pnl_net >= 0 → Counts as LOSS

   be_fees_rate = (pnl_net >= 0).sum() / n_trades
   win_rate = (pnl_gross > 0).sum() / n_trades  # For comparison

   # BE+fees rate MUST BE <= win_rate
   assert be_fees_rate <= win_rate, \
       "BE+fees rate cannot exceed win rate"
   ```

4. **Find Best LSG per (State, Direction)** (Step 4)
   - For each (state, direction) combo
   - Select LSG with highest `be_plus_fees_rate`
   - Preserve `per_trade_pnl` array for Layer 4b

   **Logic Validation:**
   ```python
   # For state='BLUE', direction='LONG':
   # Test LSG combos: (10,1.0,1.5), (15,1.5,2.0), (20,2.0,2.5)
   #   Rates:         0.68,          0.71,          0.65
   # Best: (15,1.5,2.0) with 0.71

   best_combos = grouped.sort_values(
       'be_plus_fees_rate', ascending=False
   ).groupby(['state', 'direction']).first()

   # MUST HAVE: 1 row per (state, direction)
   n_unique_states = n_states * 2  # * 2 for LONG/SHORT
   assert len(best_combos) == n_unique_states, \
       "Missing state×direction combinations"
   ```

5. **Detect Directional Bias** (Step 5)
   - Compare LONG vs SHORT `be_plus_fees_rate` per state
   - Bias threshold: 5% difference
   - Bias types: LONG, SHORT, NEUTRAL

   **Math Validation:**
   ```python
   # Example: BLUE state
   long_rate = 0.68
   short_rate = 0.72
   difference = short_rate - long_rate = +0.04

   # Threshold = 0.05
   if abs(difference) < 0.05:
       bias = 'NEUTRAL'
   elif difference > 0:
       bias = 'SHORT'  # SHORT performs better
   else:
       bias = 'LONG'   # LONG performs better

   # For BLUE: difference=+0.04 < 0.05 → NEUTRAL
   # For RED: if difference=+0.12 > 0.05 → SHORT bias
   ```

**Output Contract (Layer 4 → Layer 4b):**
```python
BBWAnalysisResultV2:
    results: pd.DataFrame           # All groups
    best_combos: pd.DataFrame       # Top per state×direction
    directional_bias: pd.DataFrame  # Bias analysis
    summary: dict                   # Statistics
```

---

### Layer 4b: Monte Carlo V2

**Purpose:** Validate Layer 4 results via bootstrap/permutation per state×direction.

**Key Difference from V1:**
- V1: MC per state only (ignored direction)
- V2: MC per (state, direction) combination

**Logic:**
```python
# For each (state, direction):
#   Bootstrap: PnL CI per direction
#   Permutation: DD/MCL per direction
#   Verdict: ROBUST/FRAGILE per direction
```

**Verdict Logic (Updated for BE+fees):**
```python
def assign_verdict(state, direction, metrics):
    be_fees_rate = metrics['be_plus_fees_rate']
    pnl_ci_lo = metrics['bootstrap_pnl_ci_lo']
    pnl_ci_hi = metrics['bootstrap_pnl_ci_hi']
    dd_real = metrics['perm_dd_real']
    dd_p95 = metrics['perm_dd_p95']
    n_trades = metrics['n_trades']

    # Priority 1: Sample size
    if n_trades < 100:
        return 'INSUFFICIENT_DATA'

    # Priority 2: Commission kill
    if metrics['avg_net_pnl'] <= 0 and metrics['avg_gross_pnl'] > 0:
        return 'COMMISSION_KILL'

    # Priority 3: Robustness checks
    if be_fees_rate > 0.50 and pnl_ci_lo > 0 and dd_real <= dd_p95:
        return 'ROBUST'
    else:
        return 'FRAGILE'
```

---

### Layer 5: Reporting V2

**Purpose:** Generate VINCE training features + analysis reports.

**Output CSVs (5 files):**

1. **bbw_directional_bias.csv**
   - Columns: state, long_rate, short_rate, bias, strength, confidence
   - Shows which directions work per state

2. **bbw_be_fees_success.csv**
   - Columns: state, direction, lev, size, grid, be_fees_rate, verdict
   - Success rates per state×direction

3. **bbw_vince_features.csv**
   - Columns: state, direction, feature_*, target_*
   - ML training features for VINCE

4. **bbw_lsg_sensitivity.csv**
   - Columns: state, direction, lev_range, size_range, grid_range
   - LSG parameter sensitivity per direction

5. **bbw_state_summary.csv**
   - Columns: state, n_trades, avg_be_fees, best_direction
   - Overall state performance

---

## Critical Math Validations

### 1. BE+fees Rate vs Win Rate Divergence

**Expected Behavior:**
```python
# Commission kills small edges:
trades = [
    {'pnl_gross': +7.50, 'commission': 8.00, 'pnl_net': -0.50},  # WIN→LOSS
    {'pnl_gross': +15.00, 'commission': 8.00, 'pnl_net': +7.00}, # WIN→WIN
    {'pnl_gross': -10.00, 'commission': 8.00, 'pnl_net': -18.00}, # LOSS→LOSS
]

win_rate = 2/3 = 0.667  # 2 gross wins
be_fees_rate = 1/3 = 0.333  # 1 net win

# CRITICAL: be_fees_rate < win_rate due to commission
# If be_fees_rate == win_rate, commission logic is broken
```

### 2. Grouping Count Validation

**Expected Behavior:**
```python
# Input: 100K trades across 7 states, 2 directions, 10 LSG combos
n_trades = 100_000
n_states = 7
n_directions = 2
n_lsg_combos = 10

max_groups = n_states * n_directions * n_lsg_combos = 140

# After min_trades filter (100):
n_groups_filtered = len(grouped_results)

# MUST BE TRUE:
assert n_groups_filtered <= max_groups, \
    "More groups than possible combinations"

# Typical result: 80-120 groups (some combos filtered out)
```

### 3. Best Combo Selection Validation

**Expected Behavior:**
```python
# For BLUE state:
grouped_blue = grouped_results[
    grouped_results['state'] == 'BLUE'
]

# Should have 20 rows (2 directions * 10 LSG combos)
assert len(grouped_blue) <= 20, \
    "Too many combinations for single state"

# After best selection:
best_blue = best_combos[best_combos['state'] == 'BLUE']

# Should have exactly 2 rows (1 per direction)
assert len(best_blue) == 2, \
    "Must have 1 best combo per direction"

# Validate highest BE+fees selected:
long_best = best_blue[best_blue['direction'] == 'LONG'].iloc[0]
all_long = grouped_blue[grouped_blue['direction'] == 'LONG']

assert long_best['be_plus_fees_rate'] == all_long['be_plus_fees_rate'].max(), \
    "Best combo must have highest BE+fees rate"
```

### 4. Directional Bias Detection Validation

**Expected Behavior:**
```python
# RED state (high volatility):
long_rate = 0.58
short_rate = 0.72
difference = 0.72 - 0.58 = +0.14

# Threshold = 0.05
assert abs(difference) > 0.05, "Significant difference"
assert difference > 0, "SHORT outperforms LONG"

bias = 'SHORT'  # CORRECT
bias_strength = 0.14

# Interpretation: In RED (high volatility), SHORT direction
# achieves 14% higher BE+fees rate than LONG
```

### 5. Commission Drag Validation

**Expected Behavior:**
```python
# Group metrics:
avg_gross_pnl = +$12.50
avg_net_pnl = +$4.50
avg_commission = $8.00

commission_drag = avg_gross_pnl - avg_net_pnl
# = 12.50 - 4.50 = $8.00

# MUST BE TRUE:
assert abs(commission_drag - avg_commission) < 0.01, \
    "Commission drag must equal average commission"

# If this fails, either:
# - pnl_net calculation is wrong
# - commission_rt is not per-trade
# - Grouping logic is broken
```

---

## Syntax Error Prevention Checklist

### 1. Windows Path Safety (CRITICAL)

**NEVER use backslash paths in:**
- Docstrings
- String literals
- f-strings

```python
# ❌ FATAL - Causes SyntaxError
"""
Run: python C:\Users\User\Documents\script.py
"""

# ✅ CORRECT
"""
Run: python C:/Users/User/Documents/script.py
"""

# ❌ FATAL
path = "C:\Users\User\Documents\file.csv"

# ✅ CORRECT
from pathlib import Path
path = Path("C:/Users/User/Documents/file.csv")
```

### 2. DataFrame Merge Alignment

```python
# CRITICAL: Timestamp alignment
trades['timestamp'] = pd.to_datetime(trades['timestamp'])
bbw_states['timestamp'] = pd.to_datetime(bbw_states['timestamp'])

# Use left join to preserve all trades
enriched = trades.merge(
    bbw_states[['timestamp', 'bbw_state']],
    on='timestamp',
    how='left'
)

# Validate: No nulls allowed
assert enriched['bbw_state'].isna().sum() == 0, \
    "Timestamp mismatch between trades and BBW states"
```

### 3. Groupby Index Handling

```python
# GroupBy resets index by default
grouped = df.groupby(['state', 'direction']).apply(func)

# CRITICAL: Reset index before further operations
grouped = grouped.reset_index()

# Otherwise: MultiIndex breaks downstream operations
```

### 4. Column Name Consistency

```python
# Layer 4 output: 'bbw_state_at_entry'
# Layer 4b expects: 'state'
# Layer 5 expects: 'bbw_state'

# SOLUTION: Standardize column names at boundaries
best_combos.rename(columns={
    'bbw_state_at_entry': 'state'
}, inplace=True)
```

---

## Test Strategy

### Unit Test Categories (40+ tests per layer)

**Layer 4 Tests:**
1. Data enrichment (8 tests)
2. Grouping logic (10 tests)
3. Metrics calculation (12 tests)
4. Best combo selection (8 tests)
5. Directional bias (8 tests)
6. Integration (5 tests)

**Layer 4b Tests:**
1. Bootstrap per direction (8 tests)
2. Permutation per direction (8 tests)
3. Verdict logic (10 tests)
4. Overfit detection (8 tests)
5. Integration (5 tests)

**Layer 5 Tests:**
1. Directional bias aggregation (6 tests)
2. BE+fees tables (6 tests)
3. VINCE features (10 tests)
4. LSG sensitivity (6 tests)
5. Output validation (8 tests)

### Debug Script Structure (10 sections each)

**Layer 4 Debug:**
1. Input data validation
2. Enrichment verification
3. Grouping validation
4. BE+fees vs win rate comparison
5. Best combo selection
6. Directional bias detection
7. Commission kill examples
8. Per-trade PnL preservation
9. Summary statistics
10. Multi-coin consistency

**Layer 5 Debug:**
1. Input contract validation
2. Directional bias aggregation
3. BE+fees success tables
4. VINCE features generation
5. LSG sensitivity analysis
6. Cross-layer validation
7. CSV output verification
8. Feature encoding checks
9. Target variable distribution
10. Multi-coin consistency

---

## Data Contracts

### Contract 1: Backtester → Layer 4

**backtester_results DataFrame:**
```python
Required columns (validated):
- timestamp: datetime64[ns], NOT NULL
- symbol: str, NOT NULL
- direction: str, IN ['LONG', 'SHORT']
- entry_price: float, > 0
- exit_price: float, > 0
- leverage: int, IN [5, 20]
- size: float, IN [0.25, 2.0]
- grid: float, IN [1.0, 3.0]
- outcome: str, IN ['TP', 'SL', 'TIMEOUT']
- pnl_gross: float
- pnl_net: float
- commission_rt: float, >= 0
- bars_held: int, > 0
```

**Validation code:**
```python
def validate_backtester_data(df: pd.DataFrame) -> bool:
    assert 'timestamp' in df.columns, "Missing timestamp"
    assert df['timestamp'].dtype == 'datetime64[ns]', "Wrong timestamp dtype"
    assert df['timestamp'].isna().sum() == 0, "Null timestamps"

    assert 'direction' in df.columns, "Missing direction"
    assert df['direction'].isin(['LONG', 'SHORT']).all(), "Invalid direction"

    assert 'leverage' in df.columns, "Missing leverage"
    assert df['leverage'].between(5, 20).all(), "Leverage out of range"

    # ... (validate all required columns)

    return True
```

### Contract 2: Layer 4 → Layer 4b

**best_combos DataFrame:**
```python
Required columns:
- state: str (renamed from bbw_state_at_entry)
- direction: str
- leverage: int
- size: float
- grid: float
- n_trades: int
- be_plus_fees_rate: float
- avg_net_pnl: float
- avg_gross_pnl: float
- avg_commission: float
- max_dd: float
- sharpe: float
- sortino: float
- per_trade_pnl: list[float]  # CRITICAL for MC
```

**Validation code:**
```python
def validate_layer4_output(best_combos: pd.DataFrame) -> bool:
    assert 'per_trade_pnl' in best_combos.columns, \
        "Missing per_trade_pnl for MC"

    for _, row in best_combos.iterrows():
        pnl_array = row['per_trade_pnl']
        assert isinstance(pnl_array, list), "per_trade_pnl not a list"
        assert len(pnl_array) == row['n_trades'], \
            "PnL array length mismatch"

    return True
```

### Contract 3: Layer 4b → Layer 5

**mc_verdicts DataFrame:**
```python
Required columns:
- state: str
- direction: str
- verdict: str, IN ['ROBUST', 'FRAGILE', 'COMMISSION_KILL', 'INSUFFICIENT_DATA']
- be_plus_fees_rate: float
- pnl_ci_lo: float
- pnl_ci_hi: float
- dd_p95: float
- mcl_p95: float
```

---

## Build Execution Plan

### Phase 1: Layer 4 Build (7-8 hours)

**Step 1:** Input validation (30 min)
- `validate_backtester_data()`
- `validate_bbw_states()`
- Unit tests: 5/5 PASS

**Step 2:** Data enrichment (45 min)
- `enrich_with_bbw_state()`
- Timestamp alignment logic
- Unit tests: 8/8 PASS

**Step 3:** Grouping (45 min)
- `group_by_state_direction_lsg()`
- Min trades filtering
- Unit tests: 10/10 PASS

**Step 4:** Metrics calculation (60 min)
- `calculate_group_metrics()`
- BE+fees rate logic
- Risk metrics
- Unit tests: 12/12 PASS

**Step 5:** Best combo selection (30 min)
- `find_best_lsg_per_state_direction()`
- Tie-breaking
- Unit tests: 8/8 PASS

**Step 6:** Directional bias (45 min)
- `detect_directional_bias()`
- Threshold logic
- Unit tests: 8/8 PASS

**Step 7:** Main pipeline (45 min)
- `analyze_bbw_patterns_v2()`
- Output assembly
- Integration tests: 5/5 PASS

**Step 8:** Debug script (90 min)
- 10 debug sections
- Hand-computed validations

**Step 9:** Sanity script (60 min)
- RIVERUSDT full pipeline
- Output validation

**Step 10:** Documentation (30 min)
- Docstrings
- Usage examples

### Phase 2: Layer 4b Build (5-6 hours)

- Reuse V1 logic structure
- Update for per-direction analysis
- Update verdict logic for BE+fees

### Phase 3: Layer 5 Build (6-7 hours)

- Feature engineering
- CSV generation
- VINCE contract compliance

---

## Success Criteria

### Layer 4 Complete When:
- [✅] 40+ unit tests PASS
- [✅] 10/10 debug sections PASS
- [✅] RIVERUSDT sanity check CLEAN
- [✅] BE+fees rate != win rate demonstrated
- [✅] Directional bias detected for 3+ states
- [✅] Output contract matches Layer 4b expectations
- [✅] Runtime < 5 seconds for RIVERUSDT

### Layer 4b Complete When:
- [✅] MC per (state, direction) working
- [✅] Verdicts updated for BE+fees
- [✅] Output contract matches Layer 5 expectations
- [✅] 40+ unit tests PASS

### Layer 5 Complete When:
- [✅] 5 CSVs generated correctly
- [✅] VINCE features validate
- [✅] 30+ unit tests PASS
- [✅] Multi-coin sanity check PASS

---

## Risk Assessment

### HIGH RISK: Data Alignment Issues

**Problem:** Timestamp mismatch between backtester results and BBW states.

**Mitigation:**
- Validate timestamp overlap before enrichment
- Use left join to preserve all trades
- Assert no nulls after merge

### MEDIUM RISK: BE+fees vs Win Rate Not Diverging

**Problem:** If BE+fees == win_rate, commission logic is broken.

**Mitigation:**
- Debug script Section 4 validates divergence
- Hand-check commission calculations
- Test with known commission_rt values

### MEDIUM RISK: Missing Directions

**Problem:** Some states may only have LONG or SHORT trades.

**Mitigation:**
- Bias detection handles missing directions
- Flag states with single direction
- Document in summary

### LOW RISK: Performance

**Problem:** Grouping 100K+ trades could be slow.

**Mitigation:**
- Use categorical dtypes
- Vectorize calculations
- Profile if > 5 seconds

---

## Next Steps

1. **Review this document** - Confirm architecture understanding
2. **Build Layer 4** - Start with input validation
3. **Test incrementally** - Run tests after each step
4. **Debug thoroughly** - Validate all math by hand
5. **Document learnings** - Update this log with findings

---

## Document Control

**Version:** 1.0 (Pre-Build)
**Related Documents:**
- `BBW-V2-ARCHITECTURE.md` (v2.0)
- `BBW-V2-UML.mmd` (corrected flow)
- `BBW-V2-LAYER4-SPEC.md` (detailed spec)
- `BBW-V2-LAYER5-SPEC.md` (detailed spec)
- `2026-02-16-bbw-v2-fundamental-corrections.md` (session log)

**Status:** Ready for Layer 4 build execution.
