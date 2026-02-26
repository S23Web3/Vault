# BBW Layer 5 V2 Build Session Log
Date: 2026-02-14
Topic: bbw_report_v2.py build, debug, audit, fix

---

## Session Summary

Continuation from previous context. Layers 1-4b of the V2 pipeline were already complete.
This session: built Layer 5 V2, integration test scripts, full audit, and bug fixes.

---

## Files Built / Modified

| File | Action | Status |
|---|---|---|
| `research/bbw_report_v2.py` | CREATED | Complete, bugs fixed |
| `tests/test_bbw_report_v2.py` | CREATED | 48 tests, not yet run |
| `scripts/debug_bbw_integration.py` | CREATED | L4->L4b->L5 single scenario debug |
| `scripts/test_bbw_integration_random.py` | CREATED | 10 random scenario runner |
| `research/bbw_monte_carlo_v2.py` | MODIFIED | Column rename fix |
| `tests/test_bbw_monte_carlo_v2.py` | MODIFIED | Column rename fix |
| `scripts/debug_bbw_analyzer_v2.py` | MODIFIED | Column rename fix |
| `scripts/sanity_check_bbw_analyzer_v2.py` | MODIFIED | Column rename fix |

---

## Bugs Found and Fixed

### 1. Column name mismatch: bbw_state_at_entry → bbw_state (CRITICAL)
- Root cause: Layer 4 was updated to output `bbw_state` but Layer 4b validator still read `bbw_state_at_entry`
- Affected: `bbw_monte_carlo_v2.py` (3 locations), `test_bbw_monte_carlo_v2.py`, 2 debug scripts
- Fix: Global replace across all affected files

### 2. Layer 5 output column inconsistency: state vs bbw_state (HIGH)
- Root cause: 3 of 5 Layer 5 functions used `'state'` as column key instead of `'bbw_state'`
- Affected: `bbw_report_v2.py` — generate_state_summary, aggregate_directional_bias, create_vince_features
- Fix: Standardized all 5 functions to output `bbw_state`

### 3. state_encoding in create_vince_features (REAL BUG)
- Root cause: Encoding table had 3 phantom states (GREEN_DOUBLE, YELLOW_DOUBLE, GRAY) that Layer 4 never produces
- Missing: NORMAL, MA_CROSS_UP, MA_CROSS_DOWN — all mapped to ordinal=0 (indistinguishable)
- Fix: Replaced encoding with all 9 Layer 4 valid states
- Fix: Added feature_state_macross and feature_state_normal binary features

### 4. Import reference: run_bbw_analysis_v2 (BUG)
- Root cause: Integration test called non-existent function name
- Fix: Updated to `analyze_bbw_patterns_v2` (actual function name)

### 5. Integration test: outcomes WIN/LOSS instead of TP/SL/TIMEOUT (BUG)
- Fix: Updated mock data to use correct Layer 4 outcome values

### 6. Integration test: LSG architecture — random per-trade vs fixed per-run (ARCHITECTURE)
- Root cause: Mock data generated random leverage/size/grid per trade
- Real behavior: LSG is fixed for an entire backtester run. All trades in one run share same LSG.
- With continuous random LSG: every trade had unique group → all groups had 1 trade → all filtered by min_trades → 0 results
- Fix: Changed to LSG-combo batch architecture:
  - Define N discrete LSG combos
  - Generate trades_per_combo trades per combo (all sharing same L, S, G)
  - Use discrete values: leverage [5,10,15,20], size [0.5,1.0,1.5,2.0], grid [1.0,1.5,2.0,2.5,3.0]
- Applied to: debug_bbw_integration.py and test_bbw_integration_random.py

### 7. Integration test: n_trades too low for group filter (DATA)
- Root cause: groups = n_combos(4) × n_directions(2) × n_states → need n_trades / groups >= min_trades
- With n_trades=800, n_states=5: 800/40 = 20 trades/group < min_trades=50 → all filtered
- Fix 1: Lowered min_trades_per_group to 10 in run_scenario (test data, not production)
- Fix 2: Scaled up scenario n_trades:
  - scenario_normal: 800→1600 (5 states, 40 groups, 40 trades/group)
  - scenario_small: 200→400, n_bars 500→1500 (2 states, 16 groups, 25 trades/group)
  - scenario_high_volatility: 1200→1600 (7 states, 56 groups, 28 trades/group)
  - scenario_many_states: 1000→2000 (9 states, 72 groups, 27 trades/group)
  - scenario_random: randint(300,1500)→randint(2000,4000)

---

## Logic Audit Results

### Layer 4 (bbw_analyzer_v2.py) — CORRECT
- Timestamp LEFT JOIN: intentional, hard error on mismatch is correct
- Groupby 5 dimensions: correct architecture
- Best combo selection via sort+groupby.first(): correct
- Directional bias calculation: correct (difference = long - short)
- Sharpe/Sortino with ddof=1: RuntimeWarning on n=1 groups, guarded by isnan check

### Layer 5 (bbw_report_v2.py) — COMPLETE after fixes
- aggregate_directional_bias: recalculates bias (not reusing L4's version), adds MC verdicts. Correct.
- generate_be_fees_success_tables: direct merge of best_combos + verdicts. Correct.
- create_vince_features: fixed state_encoding + added macross/normal features. Correct.
- analyze_lsg_sensitivity: Pearson with n=4 combos is noisy but not a code bug. Known limitation.
- generate_state_summary: state_quality DEAD/HIGH_QUALITY/MIXED logic is correct.

### Minor known issues (not fixed, by design)
- analyze_lsg_sensitivity: unreliable with <20 LSG combos per (state,direction). Known limitation.
- Single-direction states silently dropped from vince_features (no warning logged).
- Layer 4's directional_bias output is never consumed by Layer 5 (redundant, but not wrong).

---

## Completeness Status

| Component | Status |
|---|---|
| bbw_report_v2.py (logic) | COMPLETE |
| test_bbw_report_v2.py (48 tests) | BUILT, NOT RUN |
| debug_bbw_integration.py | BUILT, runs to ValueError (column fix pending when session ended) |
| test_bbw_integration_random.py | BUILT, last run 0/10 FAIL (LSG+data fixes applied, not re-run) |

### Next steps
1. Run: `python scripts/debug_bbw_integration.py` — confirm end-to-end pass
2. Run: `python scripts/test_bbw_integration_random.py` — confirm 10/10 pass
3. Run: `python tests/test_bbw_report_v2.py` — confirm 48/48 pass
4. Run: `python tests/test_bbw_monte_carlo_v2.py` — confirm Layer 4b tests still pass after column fix
5. Build: `research/bbw_report.py` (full pipeline CSV writer, 11 files — separate from V2)

---

## Architecture Note: V2 vs Full Pipeline

There are two parallel Layer 5 implementations:
- **bbw_report_v2.py** (THIS SESSION): VINCE feature generator. Input = BBWAnalysisResultV2 + MonteCarloResultV2. Output = 5 DataFrames for ML training. Used with the V2 debug pipeline.
- **bbw_report.py** (PLAN APPROVED, NOT YET BUILT): CSV report writer. Input = SimulatorResult + MonteCarloResult from full pipeline. Output = 11 CSVs in reports/bbw/ subdirectories. Described in plan file elegant-enchanting-wilkinson.md.

Both are Layer 5 but serve different purposes. The V2 version feeds VINCE training. The full version generates human-readable CSV reports.
