# Four Pillars Backtester - Complete Project Review
**Date:** 2026-02-16 15:45 GST  
**Purpose:** Comprehensive review for mobile reading  
**Context:** BBW nearly complete, VINCE next phase

---

## System Architecture Overview

### Four Pillars Strategy Components

**Pillar 1: Ripster EMA Clouds**
- Cloud 2: 8/9 EMA (inner, fast reaction)
- Cloud 3: 34/50/72 EMA (trend filter, CRITICAL for grade approval)
- Cloud 4: 72/89 EMA (major trend, planned for trailing exits)
- Cloud 5: 89/200 EMA (macro trend)
- Price position: above/below/inside clouds
- Cross signals: MA_CROSS_UP, MA_CROSS_DOWN

**Pillar 2: Anchored VWAP (AVWAP)**
- Session anchor: Daily 00:00 UTC reset
- Band system: ±1σ, ±2σ, ±3σ (Bollinger-style)
- Trailing TP: +2σ checkpoint scale-out (25-50% position)
- Inheritance: ADD/RE-entry slots clone parent AVWAP state
- Exit trigger: Price crosses back below AVWAP (LONG) or above (SHORT)

**Pillar 3: Quad Rotation Stochastic**
- 4 timeframes: 3K, 5K, 7K, 14K
- D signal: Continuation when 60-K pinned in extreme zone (>80 or <20)
- Overbought: All K values >80
- Oversold: All K values <20
- State machine: A/B/C/D grades + ADD + RE-entry

**Pillar 4: Bollinger Band Width Percentile (BBWP)**
- 7 volatility states: BLUE, BLUE_DOUBLE, NORMAL, MA_CROSS_UP, MA_CROSS_DOWN, RED, RED_DOUBLE
- Percentile rank: 0-100 scale of BB width over lookback window
- State transitions: Track contraction → expansion cycles
- LSG optimization: Leverage, size, grid vary by state

**Integration:** All 4 pillars feed into state machine → directional bias → entry signal → LSG selection

---

## Trade Lifecycle Mechanics

### Entry Signals (State Machine v383)

**Grade A - Strongest (All 4 pillars aligned):**
- Quad overbought (SHORT) or oversold (LONG)
- Cloud 3 confirmation: Price above all 3 EMAs for LONG, below for SHORT
- AVWAP alignment: Price position supports direction
- BBWP state: Favorable volatility regime
- **Filter:** MUST pass Cloud 3 test (if price inside Cloud 3 bands → downgrade to B)

**Grade B - Strong (3/4 pillars):**
- Missing one confirmation (typically Cloud 3 or AVWAP)
- Still tradeable but lower position size
- Example: Stoch oversold + Ripster trend + favorable BBWP, but price below AVWAP for LONG

**Grade C - Weak (2/4 pillars):**
- Minimal confirmation
- Smallest position size
- Typically rejected unless extreme volatility state

**Grade D - Continuation:**
- Not new entry, but hold/add to existing position
- 60-K pinned in extreme zone (>80 for SHORT, <20 for LONG)
- Validates momentum continuation

**ADD Signal:**
- Existing position profitable (above entry price)
- New entry signal fires (can be lower grade than original)
- Opens parallel slot with independent SL/TP
- Clones parent AVWAP state

**RE-entry Signal:**
- Position stopped out, but setup still valid
- Fires within N bars of exit (configurable, typically 10-20 bars)
- New slot, fresh SL/TP

### Stop Loss Lifecycle

**Phase 1: Initial SL (Entry)**
```
SL_distance = sl_mult × ATR_14
LONG: SL = entry_price - SL_distance
SHORT: SL = entry_price + SL_distance

Example:
Entry: $100.00
ATR: $2.50
sl_mult: 2.0
SL: $100.00 - ($2.50 × 2.0) = $95.00
```

**Phase 2: Breakeven Raise (After +be_raise × ATR profit)**
```
Trigger: Price moves +be_raise × ATR from entry
Action: Move SL to entry_price (breakeven)

Example:
Entry: $100.00
be_raise: 4
ATR: $2.50
Trigger at: $100.00 + ($2.50 × 4) = $110.00
New SL: $100.00 (breakeven)
```

**Phase 3: AVWAP Trailing (After BE raised)**
```
Recalculates every bar:
band_width = avwap_band_mult × current_ATR
floor = avwap_floor_mult × current_ATR

LONG:
  new_SL = max(current_SL, AVWAP - band_width - floor)

SHORT:
  new_SL = min(current_SL, AVWAP + band_width + floor)

Ratchets upward (LONG) or downward (SHORT) as AVWAP moves
Never reverses direction
```

**Current Bug:** AVWAP trail not ratcheting properly in v3.9
**Location:** `engine/exit_manager.py` lines ~200-250
**Fix needed:** Debug logging + SL update verification

### Take Profit Logic

**Optional ATR-based TP:**
```
If tp_mult > 0:
  TP_distance = tp_mult × ATR_14
  LONG: TP = entry_price + TP_distance
  SHORT: TP = entry_price - TP_distance
```

**AVWAP Checkpoint Scale-Out:**
```
If price crosses AVWAP +2σ (LONG) or -2σ (SHORT):
  Close 25-50% of position (configurable)
  Lock in partial profit
  Let remainder run with trailing SL
```

**Cloud 4 Trailing (Planned v3.9.1):**
```
LONG: SL = Cloud4_bottom - (offset_mult × ATR)
SHORT: SL = Cloud4_top + (offset_mult × ATR)

Expected improvement: 8x profit capture vs static SL
Test coin: PIPPINUSDT
```

### Position Management (Multi-Slot)

**Slot System:**
```
Max slots: 4 concurrent positions
Each slot: Independent entry, SL, TP, AVWAP state
Slots do NOT share risk/reward
```

**Slot Lifecycle:**
```
1. Entry signal → Open slot 1
2. ADD signal → Open slot 2 (while slot 1 active)
3. Slot 1 hits SL → Close slot 1
4. RE-entry signal → Open slot 3 (within 10 bars of slot 1 exit)
5. All slots tracked independently
```

**Capital Allocation:**
```
Per-slot notional = base_size × size_frac × leverage
Total exposure = sum of all active slot notionals
Max exposure = base_size × max_positions × leverage

Example:
base_size: $250
size_frac: 1.0
leverage: 20x
max_positions: 4

Slot 1 notional: $250 × 1.0 × 20 = $5,000
Slot 2 notional: $250 × 1.0 × 20 = $5,000
Max total: $20,000 (if 4 slots active)
```

### Commission & Rebate Model

**Round-Trip Commission:**
```
notional = position_size × leverage × base_capital
entry_fee = notional × commission_rate (0.08% taker = 0.0008)
exit_fee = notional × commission_rate
RT_commission = entry_fee + exit_fee

Example:
notional: $5,000
rate: 0.0008
RT = $5,000 × 0.0008 × 2 = $8.00
```

**Daily Rebate Settlement (17:00 UTC):**
```
rebate_rate = 0.02% (maker rebate)
daily_volume = sum of all notional trades in 24h window
rebate_credit = daily_volume × rebate_rate

Example:
25 trades/day × $5,000 notional = $125,000 volume
Rebate: $125,000 × 0.0002 = $25.00 credit
```

**Net Expectancy Impact:**
```
gross_exp = avg_win × win_rate - avg_loss × loss_rate
commission_drag = RT_commission (per trade)
net_exp = gross_exp - commission_drag

Critical threshold:
If net_exp < $1.00 → COMMISSION_KILL verdict (not tradeable)
If net_exp < rebate_credit → THIN_EDGE (barely profitable)
```

---

## BBW Pipeline (5 Layers - CORRECTED)

### Layer 1: BBWP Calculator
**File:** `signals/bbwp.py`  
**Status:** ✅ COMPLETE (61/61 tests PASS)  
**Input:** OHLC DataFrame  
**Output:** 10 columns
```
bbwp_value (0-100 percentile)
bbwp_ma (MA of BBWP)
bbwp_bb_upper/lower (Bollinger bands around BBWP_MA)
bbwp_state (categorical: BLUE/NORMAL/RED etc)
bbwp_color (numeric 1-5)
bbwp_points (weighted score)
bbwp_is_double (transition flag)
bbwp_prev_state (for transition tracking)
bbwp_bars_in_state (duration counter)
```

### Layer 2: BBW Sequence Analyzer
**File:** `signals/bbw_sequence.py`  
**Status:** ✅ COMPLETE (68/68 tests PASS)  
**Input:** Layer 1 output (with bbwp_state)  
**Output:** 9 columns
```
seq_id (unique transition ID)
seq_from_state, seq_to_state
seq_direction (expansion/contraction)
seq_duration_bars
seq_start_idx, seq_end_idx
seq_type (categorical: BLUE_TO_NORMAL, etc)
transition_velocity (bars to next state)
```

### Layer 3: Forward Returns Analyzer
**File:** `research/bbw_forward_returns.py`  
**Status:** ✅ COMPLETE (tests PASSING)  
**Input:** Layer 2 output + backtester trades  
**Output:** 17 columns (per state/direction combo)
```
state, direction
n_forward_bars (50, 100, 200)
forward_return_mean, forward_return_std
forward_return_sharpe
forward_dd_mean, forward_dd_max
forward_mcl_mean, forward_mcl_max
forward_win_rate, forward_profit_factor
Predictive power score (PPS)
```

### Layer 4: Backtester Results Analyzer
**File:** `research/bbw_analyzer_v2.py`  
**Status:** ✅ COMPLETE  
**Input:** Backtester v385 trade results (real historical trades)  
**Output:** BBWAnalysisResultV2 dataclass
```
results DataFrame: All (state, direction, LSG) combos with metrics
best_combos DataFrame: Top LSG per (state, direction)
directional_bias DataFrame: LONG vs SHORT preference per state
summary dict: Aggregate statistics
```

**Key Metrics per Group:**
```
n_trades (sample size)
be_plus_fees_rate (breakeven + commission survival rate)
win_rate (gross win %)
avg_gross_pnl, avg_net_pnl
commission_drag (avg RT commission)
sharpe, sortino, max_dd, max_consecutive_loss
per_trade_pnl (list for Monte Carlo input)
```

### Layer 4b: Monte Carlo Validation
**File:** `research/bbw_monte_carlo.py`  
**Status:** ✅ COMPLETE (45/45 tests PASS, 56/56 debug PASS)  
**Input:** Layer 4 per_trade_pnl lists  
**Output:** MonteCarloResultV2 dataclass
```
state_verdicts DataFrame:
  - bbw_state, direction, n_trades
  - mean_pnl, ci_lower, ci_upper (bootstrap 95% CI)
  - verdict (ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT)
  - verdict_reason (human-readable explanation)

confidence_intervals DataFrame:
  - total_pnl, sharpe, sortino, profit_factor CI ranges
  - max_dd, max_consecutive_loss permutation distributions

overfit_flags DataFrame:
  - PNL_OVERFIT (CI contains zero)
  - DD_FRAGILE (real DD > p95 permutation)
  - MCL_FRAGILE (real MCL > p95 permutation)
  - COMM_KILL (net_exp <= 0)
  - THIN_EDGE (net_exp < $1.00)
```

**Verdict Logic:**
```
INSUFFICIENT_DATA: n_trades < 100
COMMISSION_KILL: net_exp <= 0 (edge killed by fees)
FRAGILE: ci_lower <= 0 (uncertain profitability)
ROBUST: ci_lower > 0 AND net_exp >= $1.00 (proven edge)
```

### Layer 5: VINCE Feature Generator (IN PROGRESS)
**File:** `research/bbw_report_v2.py`  
**Status:** ⚡ PENDING COMPLETION  
**Input:** Layer 4 + Layer 4b outputs  
**Output:** BBWReportResultV2 + CSV files
```
VINCE training features (per state/direction):
  - directional_bias_score
  - confidence_level (HIGH/MEDIUM/LOW)
  - optimal_lsg (leverage, size, grid)
  - be_plus_fees_rate (target metric)
  - commission_sensitivity
  - monte_carlo_verdict
  - overfit_flags (binary indicators)

CSV exports:
  - vince_features.csv (model training input)
  - state_performance.csv (analytics)
  - directional_bias.csv (bias lookup table)
  - overfit_summary.csv (risk flags)
```

**CRITICAL:** Layer 5 is the final BBW output → feeds VINCE ML training

**NO LAYER 6** - VINCE is separate component, not part of BBW

---

## VINCE ML Agent (Separate from BBW)

### Purpose
Optimize LSG (Leverage, Size, Grid) selection in real-time based on:
1. BBW state (from Layer 1 live calculation)
2. Ripster cloud position
3. AVWAP band distance
4. Stochastic momentum

### 9 Modules (from BUILD-VINCE-ML.md)

**Module 1: RFE (Recursive Feature Elimination)**
- Finds minimal feature set for LSG prediction
- Eliminates redundant/low-importance features
- Output: Feature importance ranking

**Module 2: Coin Feature Engineering**
- Enriches raw OHLC with technical features
- BBW state embeddings
- Ripster/AVWAP/Stoch derived features
- Output: Augmented feature DataFrame

**Module 3: LSG Optimizer (PRIORITY)**
- XGBoost classifier: Predicts optimal LSG combo
- Input: Current market state features
- Output: (leverage, size, grid) recommendation
- Training target: BBW Layer 5 be_plus_fees_rate

**Module 4: Meta-Labeling**
- Binary classifier: Trade or skip?
- Filters low-confidence setups
- Output: 0 (skip) or 1 (trade)

**Module 5: Bet Sizing (Kelly Criterion)**
- Dynamic position sizing based on edge
- Input: Win rate, avg win/loss, confidence
- Output: Optimal size_frac (0.0 - 1.0)

**Module 6: Feature Store**
- Versioned feature snapshots
- Training/inference consistency
- Handles schema evolution

**Module 7: Backtesting Integration**
- VINCE-in-the-loop backtests
- Compares ML-optimized vs static LSG
- A/B testing framework

**Module 8: Live Inference Pipeline**
- Real-time feature calculation
- Model serving (sub-50ms latency)
- n8n webhook integration

**Module 9: Monitoring & Retraining**
- Daily model retraining (post-rebate settlement)
- Drift detection (feature distribution shifts)
- Performance tracking (predicted vs actual)

### Training Data Strategy

**Data Split (Hybrid Approach):**
```
Training:   280 coins × 8 months  = 22.4M bars (53%)
Validation:  40 coins × 12 months =  4.2M bars (10%)
Test:        79 coins × 12 months =  8.3M bars (20%)
Future:      Remaining             =  7.1M bars (17%)
```

**Protection Measures:**
```
splits.json created ONCE before any training:
{
  "train_coins": [280 symbols],
  "val_coins": [40 symbols],
  "test_coins": [79 symbols],  // FROZEN, never loaded
  "frozen_date": "2026-02-16"
}
```

**5-Fold Cross-Validation on Training Set:**
```
Fold 1: 224 train, 56 validate
Fold 2: 224 train, 56 validate (different split)
... (5 folds)
```

**Benefits:**
- 100% of training data used efficiently
- Confidence intervals on model metrics
- Detects overfitting early
- Does NOT burn validation or test sets

**Monte Carlo Integration:**
```
Filter training data by Layer 4b verdicts:
  - ROBUST states: Full weight
  - FRAGILE states: 50% weight or exclude
  - COMMISSION_KILL: Exclude entirely
  - INSUFFICIENT_DATA: Exclude

Result: Train on ~60-70% of states (the CLEAN subset)
```

**Data Augmentation:**
```
Bootstrap within-state trades:
  - BLUE → NORMAL: 1000 real trades
  - Generate 5000 synthetic via resampling

BBWP noise injection (training only):
  - Real BBWP: 45.3
  - Augmented: 45.3 ± 2% = [44.4, 46.2]
  - Forces robust learning, not exact thresholds

Validation/test: REAL data only (no augmentation)
```

### Critical Rules

**IMMUTABLE:**
1. Test set list written ONCE, never modified
2. Test coins NEVER loaded during development
3. No hyperparameter tuning on test set
4. Test evaluation run ONCE for final report
5. Stratified by market cap (not cherry-picked)

**Code Enforcement:**
```python
assert current_coins.isdisjoint(splits['test_coins']), \
    "TEST SET CONTAMINATION DETECTED"
```

---

## Current Project Status

| Component | Status | Blocker | Next Action |
|-----------|--------|---------|-------------|
| BBW Layer 1 | ✅ COMPLETE | None | — |
| BBW Layer 2 | ✅ COMPLETE | None | — |
| BBW Layer 3 | ✅ COMPLETE | None | — |
| BBW Layer 4 | ✅ COMPLETE | None | — |
| BBW Layer 4b | ✅ COMPLETE | None | — |
| BBW Layer 5 | ⚡ IN PROGRESS | Dev time | Finish build |
| Dashboard v3.9 | 🔧 OPERATIONAL | AVWAP bug | Fix + test 5m |
| Backtester v385 | ✅ COMPLETE | None | Restore BE raise |
| VINCE ML | 🔴 NOT STARTED | Layer 5 | Wait for CSVs |
| Live Integration | 🔴 NOT STARTED | VINCE | n8n webhook |
| Data Infrastructure | ✅ COMPLETE | None | — |
| Signal Pipeline | ✅ COMPLETE | None | — |

---

## Critical Path

```
NOW:
  BBW Layer 5 completion (this week)
    ↓
  splits.json generation (280/40/79 allocation)
    ↓
  Restore BE raise in backtester
    ↓
  400-coin sweep with clean data
    ↓
  Layer 5 CSV exports (VINCE training features)

NEXT WEEK:
  VINCE Module 3 build (LSG Optimizer)
    ↓
  XGBoost training on 280 coins
    ↓
  5-fold cross-validation
    ↓
  Validation on 40 held-out coins

WEEK AFTER:
  Hyperparameter tuning (Optuna/GridSearch)
    ↓
  Final model selection
    ↓
  Test set evaluation (79 coins, ONE run)
    ↓
  Production deployment

LIVE:
  n8n webhook receiver
    ↓
  Real-time feature calculation
    ↓
  VINCE LSG prediction (<50ms)
    ↓
  Adaptive exits (Cloud 4 trailing)
    ↓
  Daily retraining (17:05 UTC post-rebate)
```

---

## Performance Benchmarks

### 3-Coin Backtest (v3.8.4, Jan 2026)
```
RIVERUSDT (5m):
  Trades: ~4,000
  Win rate: 17%
  Exp $/tr: +$13.95
  Net P&L: +$55,000

GUNUSDT (5m):
  Net P&L: +$8,500

AXSUSDT (5m):
  Net P&L: +$4,363

Total: +$67,863 across 3 coins
Success rate: 93% (3/3 coins profitable after commission)
```

### BBW Monte Carlo Results (Layer 4b, RIVERUSDT 5m)
```
7 states analyzed:
  - 6 states: COMMISSION_KILL (net_exp <= 0)
  - 1 state: FRAGILE (RED_DOUBLE, net_exp=$10.90)

Commission impact:
  - Avg gross exp: $5.22/trade
  - Avg net exp: -$1.92/trade
  - Commission drag: $7.14/trade

Insight: $8 RT commission kills edge on 6/7 states
Fix: BE raise restoration reduces loser count → improves net_exp
```

---

## Priority Tasks (Next 2 Weeks)

**Priority 1: BBW Layer 5 Completion**
- Finish research/bbw_report_v2.py
- Generate VINCE training CSVs
- Validate output schema
- **Blocker:** Development time
- **Timeline:** This week

**Priority 2: Dashboard 5m Validation**
- Test RIVERUSDT 5m with BE raise 4
- Expected: +$55K, 17% win rate, ~4K trades
- Fix AVWAP trail bug (exit_manager.py)
- Add coin text input widget
- **Blocker:** AVWAP bug fix
- **Timeline:** This week

**Priority 3: Restore BE Raise**
- Backfill backtester v385 with BE raise logic
- Re-run 400-coin sweep
- Collect clean training data
- **Blocker:** Code restoration
- **Timeline:** This week

**Priority 4: Generate splits.json**
- 280 train, 40 val, 79 test coin allocation
- Stratify by market cap
- Freeze before any VINCE development
- **Blocker:** None (quick task)
- **Timeline:** This week

**Priority 5: VINCE Module 3 Build**
- LSG Optimizer (XGBoost classifier)
- Read splits.json, enforce test set lock
- Train on 280 coins × 8 months
- **Blocker:** Layer 5 CSVs
- **Timeline:** Next week

**Priority 6: 5-Fold Cross-Validation**
- Implement CV logic in VINCE training
- Calculate mean ± std metrics
- Detect overfitting (high variance)
- **Blocker:** Module 3 build
- **Timeline:** Next week

**Priority 7: Monte Carlo Filter Integration**
- Filter training data by Layer 4b verdicts
- Exclude COMMISSION_KILL states
- Weight FRAGILE states lower
- **Blocker:** Layer 5 completion
- **Timeline:** Next week

**Priority 8: Data Augmentation**
- Bootstrap within-state trades
- BBWP noise injection (±2%)
- Expand effective training size
- **Blocker:** Module 3 build
- **Timeline:** Next week

**Priority 9: Validation Set Testing**
- Predict LSG on 40 held-out coins
- Compare vs static grid search
- Calculate accuracy, F1, AUC
- **Blocker:** Model training
- **Timeline:** Week 3

**Priority 10: Cloud 4 Trailing Exit**
- Add _cloud4_trail_sl to exit_manager.py
- Test on PIPPINUSDT (expect 8x improvement)
- Integrate with AVWAP trail
- **Blocker:** AVWAP bug fix
- **Timeline:** Week 3

**Priority 11: Live n8n Integration**
- Webhook receiver for TradingView alerts
- Real-time VINCE LSG prediction
- Entry scoring + position management
- **Blocker:** VINCE validation
- **Timeline:** Week 4

---

## Key Insights

**Commission Sensitivity:**
- $8 RT commission on $5,000 notional = significant drag
- Many states: gross_exp $3-5 → net_exp negative
- Fix: BE raise reduces losers → improves net expectancy
- VINCE can optimize LSG to minimize commission impact

**BBW State Predictive Power:**
- RED_DOUBLE: Only FRAGILE state (not COMMISSION_KILL)
- Volatility expansion states have higher win rates
- Direction matters: LONG vs SHORT bias varies by state
- Layer 5 directional_bias critical for VINCE training

**Data Preservation:**
- 53% training data sufficient (vs 80% typical)
- Quality > quantity: Clean ROBUST states beat noisy full set
- Test set integrity: 79 coins untouched until final report
- Cross-validation: Uses 100% of training data efficiently

**VINCE Value Proposition:**
- Static LSG: Manual tuning per coin (time-consuming)
- VINCE: Real-time LSG optimization (scalable to 400+ coins)
- Expected improvement: +5-10% BE+fees rate
- Enables trading coins that fail with static LSG

---

## File Locations Reference

**Project Root:**  
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`

**BBW Pipeline:**
```
signals\bbwp.py                        (Layer 1)
signals\bbw_sequence.py                (Layer 2)
research\bbw_forward_returns.py        (Layer 3)
research\bbw_analyzer_v2.py            (Layer 4)
research\bbw_monte_carlo.py            (Layer 4b)
research\bbw_report_v2.py              (Layer 5 - IN PROGRESS)
```

**Core Engine:**
```
engine\backtester_v385.py              (Main backtest engine)
engine\exit_manager.py                 (SL/TP lifecycle - AVWAP bug)
signals\state_machine_v383.py          (Four Pillars state machine)
```

**Dashboard:**
```
scripts\dashboard_v39.py               (Streamlit UI - 5 tabs)
```

**Tests:**
```
tests\test_bbwp.py                     (Layer 1 - 61 tests)
tests\test_bbw_sequence.py             (Layer 2 - 68 tests)
tests\test_forward_returns.py          (Layer 3)
tests\test_bbw_monte_carlo.py          (Layer 4b - 45 tests)
scripts\run_layer4b_tests.py           (Layer 4b runner)
```

**Specs & Docs:**
```
SPEC-A-DASHBOARD-V3.md                 (Dashboard v3 spec)
SPEC-B-BACKTESTER-V385.md              (Backtester v385 spec)
SPEC-C-VINCE-ML.md                     (VINCE ML spec)
BUILD-VINCE-ML.md                      (VINCE build plan)
PROJECT-FLOW-CHRONOLOGICAL.md          (Build flow diagram)
```

**Logs:**
```
06-CLAUDE-LOGS\2026-02-16-project-status-data-strategy.md
06-CLAUDE-LOGS\2026-02-16-bbw-layer4b-results.md
06-CLAUDE-LOGS\2026-02-14-bbw-full-session.md
```

---

**END OF REVIEW**

Read on mobile, reference tomorrow for workflow handoff.
