# BBW V2 Layer 5 Logic Analysis & Build Plan
**Date:** 2026-02-16
**Purpose:** Pre-build logic verification before implementation
**Status:** ANALYSIS (No code yet)

---

## Executive Summary

**What Layer 5 Does:**
- Takes Layer 4 (analyzer) + Layer 4b (Monte Carlo) results
- Aggregates them into VINCE training features
- Generates comprehensive reports (CSV exports)
- NO ML/trading logic - pure data transformation

**Input:** 2 dataclasses (BBWAnalysisResultV2, MonteCarloResultV2)
**Output:** 1 dataclass (BBWReportResultV2) + CSV files
**Core Operations:** 5 aggregation functions + 1 orchestrator

---

## Input Contract Verification

### BBWAnalysisResultV2 (from Layer 4)

**Attributes:**
```
- results: DataFrame (all state×direction×LSG groups)
- best_combos: DataFrame (1 row per state×direction)
- directional_bias: DataFrame (bias per state)
- summary: dict
- symbol: str
- n_trades_analyzed: int
- n_states: int
- date_range: Tuple[datetime, datetime]
- runtime_seconds: float
```

**best_combos columns (verified from Layer 4):**
```
- bbw_state_at_entry
- direction
- leverage, size, grid
- n_trades
- be_plus_fees_rate
- win_rate
- avg_gross_pnl, avg_net_pnl
- commission_drag, avg_commission
- sharpe, sortino, max_dd
- per_trade_pnl (list of floats)
```

### MonteCarloResultV2 (from Layer 4b)

**Attributes:**
```
- state_verdicts: DataFrame
- confidence_intervals: DataFrame
- overfit_flags: DataFrame
- summary: dict
```

**state_verdicts columns (verified from Layer 4b):**
```
- bbw_state
- direction
- n_trades
- mean_pnl
- ci_lower, ci_upper
- verdict (ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT)
- verdict_reason
```

---

## Logic Verification - Function by Function

### Function 1: aggregate_directional_bias()

**Purpose:** Combine Layer 4 bias with Layer 4b verdicts

**Input:**
- best_combos (from Layer 4)
- state_verdicts (from Layer 4b)

**Logic (VERIFIED CLEAR):**
```
For each unique BBW state:
  1. Get LONG row from best_combos
  2. Get SHORT row from best_combos
  3. Get LONG verdict from state_verdicts
  4. Get SHORT verdict from state_verdicts
  5. Calculate: difference = short_rate - long_rate
  6. Classify bias:
     - If |difference| < 0.05 → NEUTRAL
     - If difference > 0 → SHORT favored
     - If difference < 0 → LONG favored
  7. Calculate confidence:
     - Both ROBUST → HIGH
     - Both FRAGILE → LOW
     - Mixed → MEDIUM
  8. Append row to output
```

**Output columns:**
```
- bbw_state
- long_be_fees_rate
- short_be_fees_rate
- long_verdict
- short_verdict
- bias_direction (LONG/SHORT/NEUTRAL)
- bias_strength (abs(difference))
- confidence (HIGH/MEDIUM/LOW)
```

**FUZZY LOGIC CHECK:** ❌ ISSUE FOUND
- **Problem:** Column name mismatch
  - Layer 4 best_combos uses: `bbw_state_at_entry`
  - Layer 4b state_verdicts uses: `bbw_state`
- **Fix:** Function must handle both column names OR standardize

**Edge Cases:**
- State has only LONG (no SHORT) → Skip
- State has only SHORT (no LONG) → Skip
- Verdict not found → Error or skip?

---

### Function 2: generate_be_fees_success_tables()

**Purpose:** Create comprehensive success rate table

**Input:**
- best_combos (from Layer 4)
- state_verdicts (from Layer 4b)

**Logic (VERIFIED CLEAR):**
```
For each row in best_combos:
  1. Extract state and direction
  2. Lookup verdict from state_verdicts (match on state+direction)
  3. Calculate rate_divergence = be_plus_fees_rate - win_rate
  4. Assemble row with all metrics
  5. Append to output
```

**Output columns:**
```
- state, direction
- leverage, size, grid
- n_trades
- be_plus_fees_rate, win_rate, rate_divergence
- avg_net_pnl, avg_commission, commission_drag
- verdict
- sharpe, max_dd
```

**FUZZY LOGIC CHECK:** ✅ CLEAR
- All columns exist in inputs
- Straightforward 1:1 merge

**Edge Cases:**
- Verdict not found for (state, direction) → Use "UNKNOWN"?

---

### Function 3: create_vince_features()

**Purpose:** Generate ML feature vectors

**Input:**
- best_combos (from Layer 4)
- directional_bias (from Function 1)
- state_verdicts (from Layer 4b)

**Logic (NEEDS CLARIFICATION):**
```
For each row in best_combos:
  1. Extract state and direction
  2. Lookup bias info from directional_bias (match on state)
  3. Lookup verdict from state_verdicts (match on state+direction)
  4. Encode state as ordinal (BLUE=1, RED=6, etc.)
  5. Encode direction as binary (LONG=1, SHORT=0)
  6. Calculate feature_bias_aligned:
     - If direction matches bias_direction → 1
     - Else → 0
  7. Assemble feature row
```

**Output columns:**
```
# Identifiers
- state, direction

# Features (inputs for VINCE)
- feature_state_ordinal (1-9)
- feature_state_blue (0/1)
- feature_state_red (0/1)
- feature_state_double (0/1)
- feature_direction_long (0/1)
- feature_bias_aligned (0/1)
- feature_bias_strength (float)
- feature_leverage, feature_size, feature_grid
- feature_n_trades
- feature_verdict_ordinal (0-3)

# Targets (outputs VINCE predicts)
- target_be_plus_fees_rate
- target_avg_net_pnl
- target_sharpe
- target_verdict

# Training weight
- sample_weight (1.0 for ROBUST, 0.5 otherwise)
```

**FUZZY LOGIC CHECK:** ⚠️ POTENTIAL ISSUE
- **Question:** What if bias_direction is NEUTRAL?
  - Current logic: feature_bias_aligned = 0
  - Is this correct? Should it be 0.5 for NEUTRAL?
- **Question:** Verdict encoding includes "MARGINAL" but Layer 4b only returns ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT
  - **Fix:** Remove MARGINAL from encoding dict

**Edge Cases:**
- State not in directional_bias → Skip row
- State has NEUTRAL bias → feature_bias_aligned = 0
- Verdict is INSUFFICIENT → verdict_ordinal = -1 (correct)

---

### Function 4: analyze_lsg_sensitivity()

**Purpose:** Analyze LSG parameter sensitivity

**Input:**
- results (ALL groups from Layer 4, not just best_combos)
- best_combos (for reference)

**Logic (VERIFIED CLEAR):**
```
For each (state, direction) combination:
  1. Filter results to only that state×direction
  2. If < 3 rows → Skip (not enough for correlation)
  3. Calculate correlations:
     - corr(leverage, be_plus_fees_rate)
     - corr(size, be_plus_fees_rate)
     - corr(grid, be_plus_fees_rate)
  4. Identify dominant parameter (highest |corr|)
  5. Get best combo for reference
  6. Assemble row
```

**Output columns:**
```
- state, direction
- best_leverage, best_size, best_grid
- leverage_sensitivity (correlation)
- size_sensitivity (correlation)
- grid_sensitivity (correlation)
- dominant_parameter ('leverage'/'size'/'grid')
```

**FUZZY LOGIC CHECK:** ✅ CLEAR
- Correlation calculation is standard
- Dominant parameter selection is clear

**Edge Cases:**
- < 3 groups for state×direction → Skip
- All correlations are NaN → dominant_parameter = None?
- Tied correlations → First in list wins (leverage > size > grid)

---

### Function 5: generate_state_summary()

**Purpose:** High-level summary per BBW state

**Input:**
- directional_bias (from Function 1)
- be_fees_success (from Function 2)
- state_verdicts (from Layer 4b)

**Logic (NEEDS SPECIFICATION):**
```
For each unique BBW state:
  1. Get bias info from directional_bias
  2. Get all (state, *) rows from be_fees_success
  3. Calculate aggregates:
     - n_directions (1 or 2)
     - avg_be_fees_rate (mean across both directions)
     - best_direction (LONG or SHORT with higher rate)
     - total_sample_size (sum of n_trades)
  4. Get verdict counts:
     - n_robust (count of ROBUST verdicts)
     - n_fragile
     - n_commission_kill
  5. Classify state quality:
     - If all ROBUST → "HIGH_QUALITY"
     - If all COMMISSION_KILL → "DEAD"
     - Else → "MIXED"
  6. Assemble row
```

**Output columns:**
```
- bbw_state
- bias_direction
- bias_confidence
- n_directions (1 or 2)
- avg_be_fees_rate
- best_direction
- total_sample_size
- n_robust, n_fragile, n_commission_kill
- state_quality (HIGH_QUALITY/MIXED/DEAD)
```

**FUZZY LOGIC CHECK:** ✅ MOSTLY CLEAR
- State quality classification is subjective but acceptable
- Alternative: Use % ROBUST instead of categorical

---

### Function 6: generate_vince_features_v2() - Main Orchestrator

**Purpose:** Run all 5 functions and export results

**Input:**
- analysis_results: BBWAnalysisResultV2
- mc_results: MonteCarloResultV2
- output_dir: str

**Logic:**
```
1. Validate inputs (check dataclasses)
2. Run Function 1: directional_bias = aggregate_directional_bias()
3. Run Function 2: be_fees_success = generate_be_fees_success_tables()
4. Run Function 3: vince_features = create_vince_features()
5. Run Function 4: lsg_sensitivity = analyze_lsg_sensitivity()
6. Run Function 5: state_summary = generate_state_summary()
7. Export all 5 DataFrames to CSV:
   - output_dir/directional_bias.csv
   - output_dir/be_fees_success.csv
   - output_dir/vince_features.csv
   - output_dir/lsg_sensitivity.csv
   - output_dir/state_summary.csv
8. Create summary dict
9. Return BBWReportResultV2
```

**Output dataclass:**
```python
@dataclass
class BBWReportResultV2:
    directional_bias: pd.DataFrame
    be_fees_success: pd.DataFrame
    vince_features: pd.DataFrame
    lsg_sensitivity: pd.DataFrame
    state_summary: pd.DataFrame
    summary: dict  # Keys: n_states, n_features, runtime_seconds
    output_dir: str
```

**FUZZY LOGIC CHECK:** ✅ CLEAR
- Straightforward orchestration
- CSV export with pathlib

---

## Critical Logic Issues Found

### Issue 1: Column Name Mismatch ⚠️
**Problem:** Inconsistent column naming between layers
- Layer 4 best_combos: `bbw_state_at_entry`
- Layer 4b state_verdicts: `bbw_state`

**Fix Options:**
1. **Option A (RECOMMENDED):** Standardize on `bbw_state` everywhere
   - Rename in Layer 4 output before passing to Layer 5
   - OR handle both names in Layer 5 merge logic
2. **Option B:** Add explicit column rename in Layer 5

**Decision:** Layer 5 should accept both and standardize internally

### Issue 2: Verdict Encoding Dictionary ⚠️
**Problem:** Spec includes "MARGINAL" verdict, but Layer 4b only generates:
- ROBUST
- FRAGILE
- COMMISSION_KILL
- INSUFFICIENT

**Fix:** Remove MARGINAL from encoding

### Issue 3: Missing Edge Case Handling ⚠️
**Problem:** Functions don't specify what to do when:
- State has only LONG (no SHORT)
- Verdict lookup fails
- Correlation calculation fails (NaN)

**Fix:** Add explicit edge case logic

---

## Test Requirements

### Phase 1: Input Validation (5 tests)
1. Valid inputs → Returns True
2. Missing dataclass attribute → ValueError
3. Empty best_combos → ValueError
4. Empty state_verdicts → ValueError
5. Column mismatch → Handled gracefully

### Phase 2: Function 1 Tests (8 tests)
1. Single state with LONG+SHORT → Correct bias calculation
2. State with only LONG → Skipped
3. State with only SHORT → Skipped
4. Both ROBUST verdicts → confidence=HIGH
5. Both FRAGILE verdicts → confidence=LOW
6. Mixed verdicts → confidence=MEDIUM
7. NEUTRAL bias (difference < 0.05) → bias_direction=NEUTRAL
8. Multiple states → All processed

### Phase 3: Function 2 Tests (5 tests)
1. All verdicts found → Complete table
2. Verdict not found → Uses UNKNOWN
3. rate_divergence calculated correctly
4. Column name mismatch handled
5. Empty input → Empty output

### Phase 4: Function 3 Tests (8 tests)
1. State encoding correct (BLUE=1, RED=6)
2. Direction encoding correct (LONG=1, SHORT=0)
3. feature_bias_aligned correct (LONG on LONG bias = 1)
4. feature_bias_aligned on NEUTRAL bias = 0
5. Verdict encoding correct (ROBUST=3, INSUFFICIENT=-1)
6. sample_weight correct (ROBUST=1.0, FRAGILE=0.5)
7. Missing bias → Row skipped
8. All features present

### Phase 5: Function 4 Tests (6 tests)
1. Correlation calculation correct
2. Dominant parameter identified correctly
3. < 3 groups → Skipped
4. NaN correlations → Handled
5. Tied correlations → Deterministic selection
6. Multiple state×direction pairs → All processed

### Phase 6: Function 5 Tests (6 tests)
1. State summary aggregates correct
2. best_direction identified correctly
3. Verdict counts correct
4. state_quality classification correct
5. Single direction state → n_directions=1
6. Multiple states → All summarized

### Phase 7: Integration Tests (5 tests)
1. Full pipeline with 1 state → All 5 outputs
2. Full pipeline with 3 states → All 5 outputs
3. CSV export works → Files exist
4. BBWReportResultV2 structure correct
5. Runtime tracking works

**Total: 48 tests, ~120 assertions**

---

## Debugging Strategy

### Debug Script Sections

**Section 1: Input Inspection**
- Print best_combos shape and columns
- Print state_verdicts shape and columns
- Verify column name consistency
- Check for missing states

**Section 2: Function 1 Debug**
- Print bias calculation for each state
- Show LONG vs SHORT rates
- Show verdict assignments
- Show confidence logic

**Section 3: Function 2 Debug**
- Show verdict lookup process
- Print rate divergence calculations
- Verify all rows have verdicts

**Section 4: Function 3 Debug**
- Print feature encoding for first 3 rows
- Verify bias alignment logic
- Check verdict encoding
- Verify sample weights

**Section 5: Function 4 Debug**
- Print correlation calculations
- Show dominant parameter selection
- Display sensitivity table

**Section 6: Function 5 Debug**
- Print state aggregations
- Show verdict counts
- Display state quality classifications

**Section 7: Output Verification**
- Check all 5 DataFrames non-empty
- Verify CSV files created
- Print summary stats

---

## Build Checklist

**Pre-Build:**
- [ ] Review this analysis document
- [ ] User approves logic
- [ ] Confirm column name handling strategy
- [ ] Confirm edge case behavior

**Phase 1: Core Module**
- [ ] Create BBWReportResultV2 dataclass
- [ ] Implement Function 1 (aggregate_directional_bias)
- [ ] Implement Function 2 (generate_be_fees_success_tables)
- [ ] Implement Function 3 (create_vince_features)
- [ ] Implement Function 4 (analyze_lsg_sensitivity)
- [ ] Implement Function 5 (generate_state_summary)
- [ ] Implement Function 6 (generate_vince_features_v2)
- [ ] Add column name standardization logic
- [ ] Add edge case handling

**Phase 2: Tests**
- [ ] Create test helpers (mock data generators)
- [ ] Write Phase 1 tests (input validation)
- [ ] Write Phase 2 tests (Function 1)
- [ ] Write Phase 3 tests (Function 2)
- [ ] Write Phase 4 tests (Function 3)
- [ ] Write Phase 5 tests (Function 4)
- [ ] Write Phase 6 tests (Function 5)
- [ ] Write Phase 7 tests (integration)
- [ ] Run all tests → 100% PASS

**Phase 3: Debug Script**
- [ ] Create debug script with 7 sections
- [ ] Run on Layer 4 + 4b output
- [ ] Verify all sections work

**Phase 4: Integration**
- [ ] Run full L4→L4b→L5 pipeline
- [ ] Verify CSV exports
- [ ] Check output contract

**Completion Criteria:**
- [ ] All 48 tests PASS
- [ ] Debug script validates all functions
- [ ] No syntax errors (py_compile clean)
- [ ] CSV files generated correctly
- [ ] Ready for VINCE ML component

---

## Recommended Build Order

1. **Fix column name issue FIRST** (critical dependency)
2. Build Functions 1-5 in order (each depends on previous)
3. Build orchestrator (Function 6) last
4. Write tests alongside each function (test-first)
5. Create debug script after all functions work
6. Run integration test with real Layer 4 + 4b output

---

## Questions for User Approval

1. **Column names:** Should Layer 5 accept both `bbw_state_at_entry` and `bbw_state`? (RECOMMENDED: Yes)
2. **NEUTRAL bias:** When bias_direction=NEUTRAL, should feature_bias_aligned = 0 or 0.5? (RECOMMENDED: 0)
3. **Missing verdicts:** If verdict lookup fails, use "UNKNOWN" or raise error? (RECOMMENDED: "UNKNOWN")
4. **State quality:** Use categorical (HIGH_QUALITY/MIXED/DEAD) or percentage? (RECOMMENDED: Categorical)

---

**END OF ANALYSIS - READY FOR USER REVIEW**
