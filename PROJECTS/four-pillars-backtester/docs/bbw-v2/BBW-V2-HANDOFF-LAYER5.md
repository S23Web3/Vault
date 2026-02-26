# BBW V2 Architecture Corrections - Handoff Document for Layer 5 Build
**Date:** 2026-02-16  
**Purpose:** Context document for new chat session to build Layer 5  
**Session Log:** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-16-bbw-v2-fundamental-corrections.md

---

## Executive Summary

BBW V2 is a **complete rebuild** that corrects fundamental architectural misunderstandings. The original design attempted to simulate trades, which was wrong. BBW V2 **analyzes existing backtester results** from backtester_v385 (400+ coins, year of data, 93% success rate) to generate training data for VINCE machine learning optimization.

**Critical Finding:** BBW is a data analyzer, not a trade simulator. No Layer 6 exists - VINCE is a separate ML component.

---

## Critical Architecture Corrections

### 1. Trade Source (MOST IMPORTANT)

**WRONG (Original V1/V2 Design):**
- BBW simulates new trades
- BBW generates synthetic LONG and SHORT trades
- Input: BBW states + raw OHLC data only

**CORRECT:**
- BBW analyzes **REAL backtester_v385 trade results**
- Input: Backtester results (trades already executed) + BBW states (for enrichment)
- 400+ coins, year of data, 93% success rate
- These are REAL trades from dashboard sweeps, not simulations

**User Reality Check Quote:**
> "There is a set ran on the dashboard, and we swept through a whole year with 93% with 80+% LSG and you ask me this question? Over 400 coins, for real, unless you say that what you coded is a fantasy, do the dashboard results actually make sense, now I start to doubt."

### 2. Direction Source

**WRONG:**
- BBW tests both LONG and SHORT to discover directional bias
- Direction determined by AVWAP alone
- BBW makes directional decisions

**CORRECT:**
- Direction comes from **Four Pillars strategy** (Stochastics + Ripster + AVWAP combined)
- Stochastics: Entry timing + initial direction
- Ripster: Trend confirmation (higher timeframe context)
- AVWAP: Trailing TP activation
- BBW receives trades with direction already decided
- BBW analyzes effectiveness per (state, direction) combination

**User Example:**
```
Trade Setup:
├─ Stochastics: Overbought → SHORT signal
├─ Ripster: Trending down → SHORT confirmation
├─ AVWAP: Price above → LONG bias (conflict)
└─ Strategy Decision: SHORT (2 vs 1, weighted by signal strength)

BBW's Job: Given SHORT in BLUE state, what LSG works best?
```

### 3. Layer 6 Does NOT Exist

**WRONG:**
- BBW Layer 6: bbw_vince_insights.py
- ML built into BBW pipeline
- BBW generates VINCE training insights directly

**CORRECT:**
- **No Layer 6 in BBW architecture**
- VINCE is a **separate ML component** at ml/vince_model.py (future build)
- BBW outputs training data (one of four pillar inputs to VINCE)
- BBW has only 5 layers: L1-L3 (data), L4-L5 (analysis)

### 4. BBW Purpose

**BBW V2 Simple Purpose:**
Generate training data for VINCE. That's it.

```
Input: Backtester trade results (already executed by Four Pillars)
Process: Enrich with BBW state, group by (state, direction, LSG), calculate BE+fees rates
Output: Training dataset for VINCE

Example:
"State=BLUE, Direction=LONG, LSG(10,1,1.5) → 68% BE+fees rate"
"State=BLUE, Direction=SHORT, LSG(10,1,1.5) → 72% BE+fees rate"
"State=RED, Direction=LONG, LSG(15,1.5,2.5) → 65% BE+fees rate"
"State=RED, Direction=SHORT, LSG(15,1.5,2.5) → 70% BE+fees rate"
```

**BBW does NOT:**
- Determine trade direction
- Make entry/exit decisions
- Simulate trades
- Contain ML logic

**BBW DOES:**
- Analyze backtester results
- Group by volatility state
- Calculate BE+fees success rates
- Generate VINCE training features

---

## BBW V2 Architecture Overview

### Complete Layer Structure

```
Data Layers (Unchanged):
├─ Layer 1: BBWP Calculator
│  File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py
│  Status: INTACT (no changes needed)
│
├─ Layer 2: BBW Sequence
│  File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbw_sequence.py
│  Status: INTACT (no changes needed)
│
└─ Layer 3: Forward Returns
   File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_forward_returns.py
   Status: INTACT (no changes needed)

Analysis Layers (V2 Rebuild):
├─ Layer 4: BBW Analyzer V2 (TO BE BUILT FIRST)
│  File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_analyzer_v2.py
│  Purpose: Analyze backtester results grouped by BBW state
│  Input: Backtester results + BBW states
│  Output: Best LSG per (state, direction) + directional bias
│  Spec: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-LAYER4-SPEC.md
│
├─ Layer 4b: Monte Carlo V2 (TO BE BUILT SECOND)
│  File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_monte_carlo_v2.py
│  Purpose: Validate Layer 4 via bootstrap/permutation
│  Input: Layer 4 results
│  Output: Verdicts (ROBUST/FRAGILE/COMMISSION_KILL) + confidence intervals
│
└─ Layer 5: Reporting V2 (TO BE BUILT THIRD - THIS HANDOFF)
   File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_report_v2.py
   Purpose: Generate VINCE training features + analysis reports
   Input: Layer 4 + 4b results
   Output: 5 CSV files including vince_features.csv
   Spec: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-LAYER5-SPEC.md

VINCE (Separate Component - Future):
└─ VINCE Engine
   File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\ml\vince_model.py (future)
   Purpose: Learn optimal LSG from BBW + Ripster + AVWAP + Stochastics
   Input: BBW features (from Layer 5) + other 3 pillars
   Output: Real-time LSG recommendations
```

---

## Layer 4 Overview (Must Be Built Before Layer 5)

**File:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_analyzer_v2.py

### What Layer 4 Does

```python
# Input: Backtester results (from dashboard/backtester_v385)
backtester_results = pd.DataFrame({
    'timestamp': [...],
    'symbol': ['RIVERUSDT', ...],
    'direction': ['LONG', 'SHORT', ...],  # From Four Pillars strategy
    'entry_price': [...],
    'exit_price': [...],
    'leverage': [10, 15, ...],
    'size': [1.0, 1.5, ...],
    'grid': [1.5, 2.0, ...],
    'outcome': ['TP', 'SL', ...],
    'pnl_gross': [...],
    'pnl_net': [...],
    'commission_rt': [...]
})

# Input: BBW states (from Layer 2)
bbw_states = pd.DataFrame({
    'timestamp': [...],
    'symbol': ['RIVERUSDT', ...],
    'bbw_state': ['BLUE', 'RED', ...],
    'bbwp': [25.5, 78.3, ...]
})

# Process:
# 1. Enrich trades with BBW state at entry time
# 2. Group by (state, direction, LSG)
# 3. Calculate BE+fees rate per group
# 4. Find best LSG per (state, direction)
# 5. Detect directional bias

# Output: BBWAnalysisResultV2
results = {
    'state': ['BLUE', 'BLUE', 'RED', 'RED', ...],
    'direction': ['LONG', 'SHORT', 'LONG', 'SHORT', ...],
    'leverage': [10, 10, 15, 15, ...],
    'size': [1.0, 1.0, 1.5, 1.5, ...],
    'grid': [1.5, 1.5, 2.5, 2.5, ...],
    'n_trades': [4575, 4575, 4052, 4052, ...],
    'be_plus_fees_rate': [0.68, 0.72, 0.65, 0.70, ...],  # PRIMARY METRIC
    'avg_net_pnl': [12.50, 15.30, 18.20, 22.10, ...],
    'per_trade_pnl': [[...], [...], [...], [...]]  # For Layer 4b MC
}
```

### Layer 4 Output Contract

**BBWAnalysisResultV2 dataclass:**
```python
@dataclass
class BBWAnalysisResultV2:
    results: pd.DataFrame           # All (state, direction, LSG) combinations
    best_combos: pd.DataFrame       # Top LSG per (state, direction)
    directional_bias: pd.DataFrame  # LONG vs SHORT comparison per state
    summary: dict                   # Overall statistics
```

**results DataFrame columns:**
- state, direction, leverage, size, grid
- n_trades
- be_plus_fees_rate (PRIMARY METRIC)
- win_rate (for comparison)
- avg_gross_pnl, avg_net_pnl, total_net_pnl
- avg_commission, commission_drag
- max_dd, sharpe, sortino
- tp_count, sl_count, timeout_count
- per_trade_pnl (list, for Layer 4b)

**best_combos DataFrame:**
Same columns as results, but only 1 row per (state, direction) - the LSG with highest be_plus_fees_rate.

**directional_bias DataFrame:**
- bbw_state
- long_be_fees_rate, short_be_fees_rate
- difference (short - long)
- bias ('LONG', 'SHORT', 'NEUTRAL')
- bias_strength (abs difference)

---

## Layer 4b Overview (Must Be Built Before Layer 5)

**File:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_monte_carlo_v2.py

### What Layer 4b Does

Takes Layer 4 best_combos and validates via Monte Carlo:

```python
# Input: Layer 4 best_combos (per_trade_pnl lists)

# Process:
# 1. Bootstrap PnL confidence intervals per (state, direction)
# 2. Permutation DD/MCL robustness per (state, direction)
# 3. Assign verdicts: ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT

# Output: MonteCarloResultV2
verdicts = {
    'state': ['BLUE', 'BLUE', ...],
    'direction': ['LONG', 'SHORT', ...],
    'verdict': ['ROBUST', 'FRAGILE', ...],
    'be_plus_fees_rate': [0.68, 0.72, ...],
    'pnl_ci_lo': [25000, 28000, ...],
    'pnl_ci_hi': [42000, 48000, ...],
    'dd_p95': [32000, 30000, ...],
    'mcl_p95': [12, 11, ...],
    'overfit_flags': [['PNL_OVERFIT'], [], ...]
}
```

### Layer 4b Output Contract

**MonteCarloResultV2 dataclass:**
```python
@dataclass
class MonteCarloResultV2:
    state_verdicts: pd.DataFrame      # Verdict per (state, direction)
    confidence_intervals: pd.DataFrame # Bootstrap CIs
    overfit_flags: pd.DataFrame       # Overfit detection
    summary: dict                     # MC statistics
```

**Verdicts:**
- ROBUST: BE+fees > 50% AND PnL CI lo > 0 AND DD real <= p95
- FRAGILE: BE+fees < 50% OR PnL CI lo <= 0 OR DD real > p95
- COMMISSION_KILL: Gross edge positive but net <= 0
- INSUFFICIENT_DATA: n_trades < 100

---

## Layer 5 Build Requirements (THIS HANDOFF)

**File:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_report_v2.py

**Full Specification:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-LAYER5-SPEC.md

### Layer 5 Purpose

Generate **VINCE training features** and analysis reports from Layer 4 + 4b results.

### Layer 5 Inputs

```python
def generate_vince_features_v2(
    analysis_results: BBWAnalysisResultV2,  # From Layer 4
    mc_results: MonteCarloResultV2,         # From Layer 4b
    output_dir: str = 'results/bbw_v2/'
) -> BBWReportResultV2
```

### Layer 5 Core Functions (5 main functions)

1. **aggregate_directional_bias()** - Combine LONG/SHORT performance per state
2. **generate_be_fees_success_tables()** - Comprehensive success metrics
3. **create_vince_features()** - PRIMARY - Generate ML training features
4. **analyze_lsg_sensitivity()** - LSG parameter importance analysis
5. **generate_state_summary()** - High-level state performance

### Layer 5 Outputs (5 CSV files)

**1. bbw_vince_features.csv** (PRIMARY - for VINCE training)
```
Columns:
- state, direction (identifiers)
- feature_state_ordinal (1-9 encoding)
- feature_state_blue, feature_state_red, feature_state_double (0/1 flags)
- feature_direction_long (0/1)
- feature_bias_aligned (0/1)
- feature_bias_strength (0.0-1.0)
- feature_leverage, feature_size, feature_grid (LSG params)
- feature_n_trades, feature_verdict_ordinal (quality indicators)
- target_be_plus_fees_rate (PRIMARY TARGET)
- target_avg_net_pnl, target_sharpe, target_verdict (secondary targets)
- sample_weight (1.0 for ROBUST, 0.5 for others)
```

**2. bbw_directional_bias.csv**
```
Columns:
- bbw_state
- long_be_fees_rate, short_be_fees_rate
- long_verdict, short_verdict
- bias_direction (LONG/SHORT/NEUTRAL)
- bias_strength (abs difference)
- confidence (HIGH/MEDIUM/LOW)
```

**3. bbw_be_fees_success.csv**
```
Columns:
- state, direction
- leverage, size, grid (best LSG)
- n_trades
- be_plus_fees_rate, win_rate
- rate_divergence (be_fees - win)
- avg_net_pnl, avg_commission, commission_drag
- verdict, sharpe, max_dd
```

**4. bbw_lsg_sensitivity.csv**
```
Columns:
- state, direction
- best_leverage, best_size, best_grid
- leverage_sensitivity (correlation)
- size_sensitivity, grid_sensitivity
- dominant_parameter (which LSG param matters most)
```

**5. bbw_state_summary.csv**
```
Columns:
- state
- total_trades, avg_be_plus_fees_rate
- bias_direction, bias_strength, confidence
- n_robust, n_fragile, n_commission_kill
- best_direction
```

### Layer 5 Key Implementation Details

**State Encoding (for VINCE features):**
```python
state_ordinal = {
    'BLUE': 1, 'BLUE_DOUBLE': 2,
    'GREEN': 3, 'YELLOW': 4, 'NORMAL': 5,
    'RED': 6, 'RED_DOUBLE': 7,
    'MA_CROSS_UP': 8, 'MA_CROSS_DOWN': 9
}
```

**Verdict Encoding:**
```python
verdict_ordinal = {
    'ROBUST': 3,
    'MARGINAL': 2,
    'FRAGILE': 1,
    'COMMISSION_KILL': 0,
    'INSUFFICIENT_DATA': -1
}
```

**Sample Weighting:**
```python
sample_weight = 1.0 if verdict == 'ROBUST' else 0.5
# ROBUST states get higher weight in VINCE training
```

**Bias Alignment Feature:**
```python
feature_bias_aligned = 1 if (
    (direction == 'LONG' and bias_direction == 'LONG') or
    (direction == 'SHORT' and bias_direction == 'SHORT')
) else 0
# Indicates if trade direction matches state's bias
```

### Layer 5 Test Requirements

**30+ unit tests required:**
- 8 tests: Directional bias aggregation
- 6 tests: BE+fees success tables
- 10 tests: VINCE features (encoding, targets, weights)
- 6 tests: LSG sensitivity
- 5 tests: State summary
- 5+ tests: Integration (full pipeline, CSV generation)

**Build Estimate:** 6-7 hours

---

## Key Design Principles

### 1. No BBW_LSG_MAP Logic

**CRITICAL:** Layer 5 does NOT generate BBW_LSG_MAP configuration files. This was V1 logic and is wrong.

BBW V2 generates **training features**, not strategy configurations.

### 2. Feature Engineering, Not ML

Layer 5 does feature engineering and aggregation. NO machine learning code.

VINCE (separate component) does the ML training later.

### 3. Commission Awareness

All metrics are post-commission. BE+fees rate is the primary metric because it accounts for round-trip commission impact.

### 4. VINCE-First Output Design

All outputs designed for ML consumption:
- Feature vectors properly encoded
- Target variables clearly defined
- Sample weights for quality indicators
- No missing values in features

---

## Success Criteria for Layer 5

**Code Complete When:**
- [✅] All 30+ unit tests PASS
- [✅] Sanity check RIVERUSDT CLEAN
- [✅] All 5 CSV files generated correctly
- [✅] vince_features.csv complete and valid (PRIMARY OUTPUT)
- [✅] No BBW_LSG_MAP logic present
- [✅] Directional bias calculated for all states
- [✅] Feature encoding validated (state, direction, verdict)
- [✅] Sample weights assigned correctly
- [✅] No missing values in feature columns
- [✅] Output contract matches VINCE expectations
- [✅] Code coverage > 90%

**Ready for VINCE When:**
- [✅] vince_features.csv has all required columns
- [✅] Feature encoding ranges validated
- [✅] Target variables present and valid
- [✅] Sample weights properly calculated
- [✅] No data quality issues

---

## Important File Paths

### Architecture Documents
- **Main Architecture:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-ARCHITECTURE.md
- **UML Diagram:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML.mmd
- **Layer 4 Spec:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-LAYER4-SPEC.md
- **Layer 5 Spec:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-LAYER5-SPEC.md

### Code Files (V2)
- **Layer 4:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_analyzer_v2.py (to be built)
- **Layer 4b:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_monte_carlo_v2.py (to be built)
- **Layer 5:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_report_v2.py (to be built - THIS HANDOFF)

### Test Files (V2)
- **Layer 4 Tests:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_bbw_analyzer_v2.py
- **Layer 4b Tests:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_bbw_monte_carlo_v2.py
- **Layer 5 Tests:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_bbw_report_v2.py

### Existing Infrastructure (Unchanged)
- **Backtester:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v385.py
- **Dashboard:** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v3.py
- **Layer 1 (BBWP):** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbwp.py
- **Layer 2 (Sequence):** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\bbw_sequence.py
- **Layer 3 (Forward):** C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_forward_returns.py

### Session Logs
- **This Session:** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-16-bbw-v2-fundamental-corrections.md
- **Previous BBW Work:** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-16-bbw-layer4b-plan.md

---

## What NOT to Do (Critical Mistakes to Avoid)

### ❌ DO NOT Create Layer 6
There is no Layer 6. VINCE is a separate component at ml/vince_model.py (future build).

### ❌ DO NOT Generate BBW_LSG_MAP
This is V1 logic. V2 generates VINCE training features, not strategy configs.

### ❌ DO NOT Simulate Trades
Layer 5 analyzes results from Layers 4/4b. No trade simulation anywhere in BBW V2.

### ❌ DO NOT Make Directional Decisions
Direction comes from Four Pillars strategy. BBW analyzes, does not decide.

### ❌ DO NOT Include ML Training Logic
Layer 5 does feature engineering only. VINCE does the ML training (separate component).

### ❌ DO NOT Assume AVWAP Determines Direction Alone
Direction is from combined Four Pillars strategy (Stochastics + Ripster + AVWAP).

---

## User Preferences Reminder

**From user preferences:**
- Windows 11 desktop environment
- Use PowerShell commands, backslash paths (C:\Users\...)
- Direct, business-focused responses (no fluff, no "excellent")
- Full file paths always (as done throughout this document)
- ALWAYS read skills before building (check C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\skills\)
- Test-first workflow mandatory
- Log everything to C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\

---

## Handoff Instructions for New Chat

**When building Layer 5:**

1. **Read this entire document first** - Contains all critical corrections
2. **Read Layer 5 spec** - C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-LAYER5-SPEC.md
3. **Check if Layer 4 and 4b are built** - If not, they must be built first (Layer 5 depends on their output)
4. **Review output contracts** - Layer 4/4b output must match Layer 5 input expectations
5. **Build test suite first** (TDD approach recommended)
6. **Focus on vince_features.csv** - This is the PRIMARY output
7. **No BBW_LSG_MAP logic** - Critical to remember
8. **Log progress** to C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-16-bbw-layer5-build.md

**Expected Build Time:** 6-7 hours (per spec)

---

## Questions to Clarify Before Starting Layer 5 Build

**If Layer 4 and 4b are NOT yet built:**
- Should build Layer 4 first? (Cannot build Layer 5 without Layer 4/4b outputs)

**If Layer 4 and 4b ARE built:**
- Confirm output contract matches expectations
- Run sanity checks on Layer 4/4b before starting Layer 5
- Verify CSV locations and data quality

**For Layer 5 build itself:**
- Confirm all 5 CSV output files needed
- Verify feature encoding approach (state ordinal, verdict ordinal, etc.)
- Check sample weighting strategy (1.0 for ROBUST, 0.5 for others)

---

**Document Version:** 1.0  
**Created:** 2026-02-16  
**Status:** Ready for handoff to new chat session
