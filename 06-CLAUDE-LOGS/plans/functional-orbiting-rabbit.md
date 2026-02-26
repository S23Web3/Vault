# Vince ML v2 — HANDOFF DOCUMENT (Chat Continuation)

**Date:** 2026-02-18
**Purpose:** Complete handoff for next chat session. Contains: Vince ML v2 scope (APPROVED), dashboard code audit (COMPLETED), error log, and all pending items.

---

# PART 1: CRITICAL ERROR LOG

## Error: "Under 60" Inverted to "Over/Past 60"

**What happened:** User described a late entry constellation pattern for longs:
- User said: "9,3 is UNDER 60 for long and above 40 for short"
- Meaning: K1 (9,3 stochastic) has NOT yet reached 60. It's somewhere in the 25-58 range. The entry fired when K1 left oversold but K1 hasn't climbed far yet. That's what makes it "late" — the signal already fired, K1 has moved up from oversold, but it's still under 60.
- I restated it as "K1 past 60" which is the OPPOSITE direction. Under 60 = hasn't reached 60 yet. Past 60 = already exceeded 60.
- This is inverting the signal direction — changing a dimension entirely.

**Root cause:** Careless paraphrasing without verifying the exact words. "Under" was changed to "past/over" without realizing this flips the meaning.

**Prevention rule for future chats:**
- NEVER paraphrase directional statements (under/over, above/below, before/after). Quote the user's EXACT words.
- If restating, use the identical inequality operator: "under 60" = "< 60", never approximate.
- When in doubt about direction, STOP and verify with the user before proceeding.

---

# PART 2: VINCE ML v2 SCOPE (Status: IN PROGRESS, NOT FINALIZED)

## What Vince IS

A **trade research engine** that:
1. Reads trade CSV output from ANY strategy's backtester
2. Enriches each trade with full indicator constellation at every bar during the trade's lifetime
3. Finds relationships between indicator states and trade outcomes using GPU-accelerated matrix operations (PyTorch)
4. From those relationships, optimal strategy parameters EMERGE from the data
5. Validates parameters across random coin batches and multiple time periods

## What Vince is NOT

- NOT a trade filter/classifier (no TAKE/SKIP decisions)
- NOT reducing trade count (volume = $1.49B/year, critical for exchange rebate)
- NOT hardcoded to Four Pillars (strategy-agnostic base, plugins for each strategy)
- NOT hardcoded to crypto (Andy = forex later, separate build on same base)

## Why the Previous Build (v1) Failed

The v1 build was Vicky's architecture (copy trading, trade filtering) mislabeled as Vince:
- XGBoost binary classifier: predicts TAKE/SKIP per trade
- Bet sizing: reduces position or skips trades entirely
- Meta-labeling: decides if signal is "good enough"
- Net effect: FEWER trades = less volume = less rebate = wrong persona

## The Evidence (unoptimized, two random 10-coin runs)

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| Trades | 77,995 | 89,633 |
| TP exits | 21,733 (27.9%) | 25,188 (28.1%) |
| SL exits | 52,739 (67.6%) | 60,250 (67.2%) |
| **Saw green (LSG)** | **67,100 (86.0%)** | **76,717 (85.6%)** |

86% LSG is systemic across ANY random coin set. The entries work. The exits lose money.

## Data Flow

```
Stage 1: STRATEGY (already exists)
  OHLCV parquet -> Strategy plugin -> Backtester384 -> Trade CSV

Stage 2: VINCE (to be built)
  Trade CSV -> Trade Enricher -> Enriched Trade Tensor
  Enriched Trade Tensor -> Relationship Engine (PyTorch/GPU) -> Relationship Results
  Relationship Results -> Cross-Validation (coin batches + time periods) -> Robust Parameters
  Robust Parameters -> Dashboard Tab -> User reviews findings
```

The strategy is the DATA GENERATOR. Vince is the ANALYST that reads the strategy's output.

## The Four Pillars (indicator components)

| Pillar | Sub-components | Role |
|--------|---------------|------|
| Stochastics | K1(9-3), K2(14-3), K3(40-3), K4(60-10) | Entry timing, confirmation, divergence, macro |
| EMA Clouds | C2(5/12), C3(34/50), C4(72/89), C5(180/200) | Momentum, direction, trend confirmation |
| ATR / SL / TP | ATR(14), sl_mult, tp_mult, BE raise, phases | Volatility, exit management |
| AVWAP | Entry-anchored center, sigma bands, slope | Trailing SL, adds, re-entries, scale-outs |

## Per-Indicator Properties (not just levels)

Each indicator at any moment has STATIC and DYNAMIC properties:

| Pillar | Static (snapshot) | Dynamic (behavior) |
|--------|------------------|-------------------|
| Stochastics | K1=25, K2=35, K3=55, K4=20 | Rising/falling, speed, zone entry/exit timing, approaching midline |
| Clouds | C3=bull, C2=bull, spread=X | Spread widening/narrowing, bars since last cross, about to flip |
| AVWAP | Center, sigma, price distance | Slope (building/flat), recently crossed, anchor age |
| ATR | ATR value | Expanding/contracting, rate of change, relative to recent range |

The stochastics are a UNIT. The question is never "what was K1" alone. It's the K1/K2/K3/K4 constellation and their inter-relationships (divergence, convergence, pullback, channel, pinned).

## Key Moments to Snapshot (per trade)

| Moment | Why |
|--------|-----|
| Entry bar | What was the constellation when we entered? |
| MFE bar | What did everything look like at the best possible exit? |
| MAE bar | What did everything look like at worst drawdown? |
| Breakeven bar | When did profit evaporate? What warned us? |
| Exit bar | What was the state at actual exit? |
| SL phase transition bar | When SL moved from ATR to AVWAP center — what was the constellation? |
| ADD/RE signal bars | What constellation triggered adds or re-entries? |
| Scale-out bars | What was the state when scale-out fired? |
| Stoch midline cross bars | K2/K3 crossing 50 — state snapshots |
| Cloud cross bars | C2/C3 flip events during trade lifetime |

## Relationship Questions (what the engine must answer)

### Stochastic Constellation Patterns
- At entry: K1 exits zone. Where are K2/K3/K4? Which constellations produce LSG vs runners?
- K2 + K3 both crossing 50 — does double midline confirmation predict outcome?
- Divergence (K1 vs K3 direction) at entry or during trade — LSG predictor?
- Pullback (K1 into zone, K3/K4 hold) — ADD quality by constellation?
- K4 pinned duration — D-signal effectiveness by how long K4 stays extreme?
- All 4 aligned vs partial alignment — runner prediction?
- Speed of K1 movement through zone — trade urgency indicator?

### Cloud Relationships
- Cloud 3 spread at entry — tight spread = reversal risk?
- Cloud 2 flip timing during trade — how many bars warning before reversal?
- Cloud 3+4 sync duration — runner predictor?
- Cloud 2 about to flip + stoch state — combined exit signal?

### AVWAP Mechanism Effectiveness
- SL phase transition (ATR -> AVWAP center at checkpoint_interval): does the constellation at that moment predict success?
- Is checkpoint_interval=5 the right timing, or should constellation determine when?
- ADD trades: win rate vs fresh entries? Constellation at ADD bar?
- RE-ENTRY trades: recovery rate? Same bad setup or genuine second chance?
- Scale-out at +2sigma: too early/too late? MFE remaining after scale-out?
- AVWAP sigma vs cloud spread — correlated?
- AVWAP slope vs K4 direction — agree at good exits?

### ATR / Exit Management
- Optimal SL mult per coin — where is the win rate peak?
- Optimal TP mult per coin — where is net PnL peak?
- ATR at entry vs ATR at MFE — vol expansion during trade matters?
- BE raise: rescues trades or causes premature exits?
- How many SL hits had MAE just barely beyond SL? (SL too tight)
- How many TP hits had MFE far beyond TP? (TP too tight, runners lost)

### Cross-Pillar (the millions of matrices)
- AVWAP sigma level vs Ripster cloud spread — relationship?
- AVWAP slope direction vs K4 direction — combined exit signal?
- Cloud 2 flip timing vs AVWAP sigma contraction — which leads?
- K3 crossing 50 + AVWAP slope change — combined signal?
- ATR expansion + AVWAP sigma expansion — same event or independent?
- Stoch speed vs AVWAP age — trade urgency?
- Full constellation at MFE bar vs exit bar — what changed? Which pillar moved first?

### Winner Analysis (not just losers)
- Was TP the ideal exit? Indicator state after TP hit?
- Could a trail have captured more? What type — AVWAP sigma? Cloud 2 flip? Stoch recross?
- Indicator state at TP vs 10-20 bars later — was there more to capture?

## User's Primary Use Case

There are questionable trades being taken that the user can identify visually by reading ALL indicator parameters simultaneously, but cannot manually review thousands of trades. Vince is the user's eyes at scale — reading every number, every relationship, every stochastic constellation for 90K+ trades.

The user does NOT look at price action ("price action is for amateurs"). They read the INDICATORS: every K value, every cloud state, every AVWAP level. Complete numerical state, no abstractions or summaries.

## Example Constellation Pattern (from user)

"Late entry" for longs: K1 (9,3) is UNDER 60 (e.g., at 45-58 range). Entry signal already fired when K1 left oversold. K1 has moved up but hasn't reached 60 yet. Meanwhile K2/K3/K4 are just beginning to cross their respective zones — confirmation arriving late.

Also: K2 and K3 crossing 50 while RE-ENTRY signal fires. User noted RE-ENTRY logic is "currently totally wrongly programmed" — will fix AFTER Vince scope is done.

## Validation Framework

1. Run analysis on 10 random coins from cache (2025-2026)
2. Extract optimal parameters from relationships
3. Run same analysis on DIFFERENT 10 random coins — do parameters hold?
4. Run on 2024-2025 period data (257 coins available)
5. Run on 2023-2024 period data (166 coins available)
6. Parameters that survive ALL batches AND ALL periods = robust strategy optimum
7. Scale to full 399 coins in batches

## Technology Stack

- **PyTorch** (GPU): tensor operations for millions of relationship matrices. RTX 3060 12GB confirmed.
- **Pandas**: trade CSV I/O, enrichment, aggregation
- **Streamlit**: dashboard tab for interactive exploration
- **Strategy plugin interface**: strategies/base.py (already exists)

## Design Constraints

- NEVER reduce trade count. All trades taken. Volume preserved.
- NOTHING hardcoded. Indicators configurable via strategy plugin.
- Strategy-agnostic base. Four Pillars is first plugin, not the only one.
- No crypto assumptions in core. Andy (forex) must be able to plug in later.
- User sees relationships and makes decisions. Vince recommends, user decides.
- Situational analysis (market regime) — noted for future, not this build.
- No prioritization of relationship questions — data shows what's there, then those relationships get analyzed.

## Existing Code to Reuse

| Component | Path | Reuse |
|-----------|------|-------|
| Strategy plugin ABC | strategies/base.py | Interface for indicator definitions |
| Four Pillars plugin | strategies/four_pillars.py | First strategy implementation |
| Backtester384 | engine/backtester_v384.py | Trade CSV generator |
| AVWAPTracker | engine/avwap.py | AVWAP center/sigma/bands computation |
| Signal pipeline | signals/four_pillars_v383.py | Indicator computation (stoch, clouds, ATR) |
| Stochastics | signals/stochastics.py | Raw K computation |
| Clouds | signals/clouds.py | EMA cloud computation |
| Commission model | engine/commission.py | Rate-based commission |

## Existing Code to DISCARD (wrong architecture — Vicky, not Vince)

| Component | Path | Why |
|-----------|------|-----|
| XGBoost classifier | ml/xgboost_trainer_v2.py | TAKE/SKIP classifier, wrong approach |
| Bet sizing | ml/bet_sizing_v2.py | Position sizing for filtering, wrong approach |
| Meta-label | ml/meta_label.py | Trade rejection, wrong approach |
| Features v3 | ml/features_v3.py | Extracted for classification, not relationship analysis |
| Triple barrier | ml/triple_barrier.py | Labeling for classification |
| Training pipeline | scripts/train_vince.py | 12-step classifier training |
| UML diagrams | docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md | Wrong architecture diagrams |
| Coin pools | data/coin_pools.json | 60/20/20 split for ML training, not needed |

## NEXT STEPS for Vince ML v2 (not started)

1. **Architecture breakdown**: module structure, interfaces, data contracts
2. **New UML diagrams** reflecting the research engine architecture
3. **Build order**: which modules first, dependencies
4. **Test strategy**: synthetic data tests, then real data validation
5. **Dashboard tab design**: what the user sees and interacts with
6. **Sampling script**: random 10 from 400 coins, run backtester, produce trade CSV, repeat N times

**Scope is IN PROGRESS. User was still providing examples when context ran out. Architecture design comes AFTER scope is finalized. No code until structure is approved.**

---

# PART 3: DASHBOARD CODE AUDIT (Full Engine Verification)

**Question from user:** "I want a full audit on the code of the dashboard. Is this really through, all those trades taken would they really result in that?"

## Audit Summary: YES, the trades are real. The engine is mechanically correct with ONE known bug.

### Files Audited

| File | Lines | Status |
|------|-------|--------|
| signals/stochastics.py | 64 | CORRECT |
| signals/clouds.py | 86 | CORRECT |
| signals/state_machine_v383.py | 340 | CORRECT |
| signals/four_pillars_v383.py | 112 | CORRECT |
| engine/backtester_v384.py | 581 | 1 BUG (see below) |
| engine/position_v384.py | 296 | CORRECT |
| engine/avwap.py | 53 | CORRECT |
| engine/commission.py | 107 | CORRECT |
| scripts/dashboard_v391.py | 2338 | CORRECT |

### 1. Signal Pipeline — VERIFIED CORRECT

**stochastics.py (64 lines)**
- `stoch_k()`: Raw K formula matches Pine Script exactly: `100 * (close - lowest) / (highest - lowest)`. Division by zero guarded (returns 50.0).
- `compute_all_stochastics()`: K1(9), K2(14), K3(40), K4(60), D line = SMA of K4 with smooth=10. Window indexing correct: `[i - k_len + 1 : i + 1]`.
- No phantom signals possible. NaN for first (k_len-1) bars.

**clouds.py (86 lines)**
- `ema()`: Matches Pine Script `ta.ema()`. SMA seed of first `length` values, then exponential smoothing with `mult = 2/(length+1)`.
- Cloud 2 (5/12), Cloud 3 (34/50), Cloud 4 (72/89). Bull = fast > slow.
- `price_pos`: +1 above cloud3_top, -1 below cloud3_bottom, 0 in between.
- Cloud 2 crossover detection: uses `np.roll(close, 1)` with bar 0 fix.
- `cloud3_allows_long = price_pos >= 0` means longs allowed when price is in or above Cloud 3.

**state_machine_v383.py (340 lines)**
- 4-stage state machine: 0=Idle, 1=A/B/C tracking, 2=D-ready, 3=D-tracking.
- Entry trigger: K4 (60-period) enters extreme zone (< 25 for longs, > 75 for shorts).
- Signal fires when K1 (9-period) crosses BACK out of the zone.
- A (4/4): K1 + K2 + K3 all flagged. Bypasses Cloud 3 filter.
- B (3/4): K1 + K2 flagged. Requires Cloud 3 direction.
- C (2/4): K1 only. Requires `price_pos == 1` (firmly above Cloud 3 for longs).
- D: K4 stays pinned, K1 cycles again. Loops back to stage 2 for more D's.
- Lookback timeout: `stage_lookback=10` bars max per stage. Prevents stale setups.
- Only ONE signal fires per bar (not both long and short simultaneously, because can_long checks `not has_shorts` and vice versa in backtester).
- RE-ENTRY: Cloud 2 crossover within `reentry_lookback=10` bars of last signal. Excluded if a fresh signal fires on same bar.
- ADD: K1 > 30 (long), K3 > 48, K4 > 48 — stochastic pullback conditions.

**four_pillars_v383.py (112 lines)**
- Orchestrator. Calls `compute_all_stochastics()`, `compute_clouds()`, computes ATR (Wilder's RMA), then runs state machine bar-by-bar.
- ATR formula: `atr[i] = (atr[i-1] * (len-1) + tr[i]) / len`. Correct Wilder's RMA. Seed = SMA of first `atr_len` bars.
- True Range: `max(H-L, |H-prevC|, |L-prevC|)`. Bar 0 fix: `tr[0] = h[0] - l[0]`.
- Skips bars where stoch_9, stoch_60, or ATR are NaN (warmup period).
- All 12 signal columns written from state machine output.

### 2. Backtester Engine — VERIFIED CORRECT (1 known bug)

**backtester_v384.py (581 lines)**

**Execution order per bar (lines 120-446):**
1. Commission settlement check (daily 5pm UTC rebate)
2. Check exits on all 4 slots (SL/TP from previous bar's levels)
3. Update AVWAP + ratchet SL for surviving slots
4. Check scale-outs at checkpoints
5. Process pending limit orders (ADD/RE fills)
6. Check stochastic entries (A > short_A > B/C > short_B/C > D > short_D > R > short_R)
7. Check AVWAP adds (limit orders with AVWAP inheritance)
8. Check AVWAP re-entry (limit orders from exited slot's AVWAP)

**Entry logic verification:**
- `can_enter`: requires `active_count < max_positions` AND cooldown OK.
- Direction lock: `has_longs` blocks shorts, `has_shorts` blocks longs. No mixed directions.
- `did_enter` flag: only ONE entry per bar. First match wins (priority: A > B/C > D > R).
- A-trades bypass Cloud 3 filter (`can_long_a`). B/C require it (`can_long`).
- Commission charged at entry: `self.comm.charge()` = taker (0.08%). Deducted from equity immediately.

**Exit logic verification:**
- `check_exit()` called on slot BEFORE `update_bar()`. SL checked first (pessimistic when both SL and TP could trigger).
- Exit price: SL at `slots[s].sl`, TP at `slots[s].tp`. Not close price — correct.
- Exit commission: `charge_custom(notional, maker=True)` = 0.02% of full notional. Correct.
- After exit: equity gets `trade.pnl - comm_exit`. PnL is gross (no commission inside).
- RE-ENTRY clone: on SL exit, AVWAP state cloned for potential re-entry.

**Scale-out verification:**
- Triggers at `checkpoint_interval` multiples when close hits +/-2sigma.
- First scale-out: closes half notional. Second (final): closes remaining.
- Commission: `charge_custom(scale_notional, maker=True)` on the portion closed. Correct.
- Entry commission share: `entry_commission * scale_notional / original_notional`. Proportional. Correct for the SCALE trade record.

**KNOWN BUG: Entry commission double-count on remaining position after scale-out**
- Line 147: When remaining position closes after a prior scale-out, it uses `comm_exit + slots[s].entry_commission` (FULL entry commission).
- Line 175: The scale-out trade already attributed a proportional share of entry commission.
- Result: the entry commission is counted ~1.5x in Trade CSV records (once proportional in SCALE trade, once full in final SL/TP trade).
- Impact on Trade CSV: overstates total commission by ~$4 per scale-out position in the combined trade records.
- Impact on equity curve: ZERO. Entry commission is deducted from equity once at entry (line 251/261/etc). The `trade.commission` field is for CSV reporting only.
- Impact on metrics: `total_commission` in metrics sums `trade.commission` values, so it overstates commission.
- Severity: LOW for equity/PnL accuracy. MEDIUM for trade-level commission reporting.

**Pending limit orders (ADD/RE):**
- ADD: triggers when price touches -2sigma (long) or +2sigma (short). Fill limit at -1sigma/+1sigma. Maker commission (0.02%).
- RE: inherits cloned AVWAP from exited slot. Same trigger/fill logic.
- Cancel after `cancel_bars=3` if not filled.
- AVWAP state inherited via `.clone()` — deep copy of cumulative stats. Correct.

**Equity curve:**
- Mark-to-market: `equity + unrealized` per bar (line 402). Unrealized = `(close - entry) / entry * notional` for each open slot.
- Final bar: all remaining positions closed with "END" reason. Equity updated.
- `equity_curve[-1] = equity` (line 414) overwrites the final bar with realized equity after forced close.

**PnL formula verification:**
- Long: `(exit_price - entry_price) / entry_price * notional`. Correct percentage-of-notional.
- Short: `(entry_price - exit_price) / entry_price * notional`. Correct.
- `Trade384.pnl` = gross PnL. `Trade384.commission` = entry + exit commission.
- `net_pnl = pnl - commission` (computed in `_trades_to_df` and in metrics).

### 3. Position Slot — VERIFIED CORRECT

**position_v384.py (296 lines)**

- SL initialization: A/B/C/D = `entry_price +/- ATR * sl_mult`. ADD/RE = AVWAP -2sigma/+2sigma.
- SL phase transition: at `checkpoint_interval` bars, SL moves to AVWAP center. Only if favorable (ratchet-only).
- BE raise: fires BEFORE AVWAP ratchet. Trigger = price reaches `entry + be_trigger_atr * ATR`. Lock SL at `entry + be_lock_atr * ATR`.
- MFE/MAE: updated every bar from high/low. `mfe = max(mfe, best_unrealized)`. `mae = min(mae, worst_unrealized)`. `saw_green` set when `ub > 0`.
- Scale-out `do_scale_out()`: reduces `self.notional` by half (or all if final). Ratchets SL to AVWAP center after scale.
- No position size going negative: `close_notional = self.notional / 2` or `self.notional` (for final).

### 4. AVWAP — VERIFIED CORRECT

**avwap.py (53 lines)**

- Cumulative VWAP: `center = sum(hlc3 * vol) / sum(vol)`. Standard.
- Variance: `E[X^2] - E[X]^2` with `max(..., 0.0)` floor. No negative variance possible.
- Sigma floor: `max(sigma_raw, sigma_floor_atr * ATR)`. Prevents zero sigma when price is flat.
- Volume guard: `if volume <= 0: volume = 1e-10`. No division by zero.
- Clone: copies all 5 cumulative fields. Deep copy confirmed (float values, not references).

### 5. Commission — VERIFIED CORRECT

**commission.py (107 lines)**

- Taker: `notional * 0.0008` = 0.08%. For market/stop orders (entries).
- Maker: `notional * 0.0002` = 0.02%. For limit orders (ADD/RE fills, all exits).
- `charge()`: standard notional. `charge_custom(notional)`: partial closes.
- Daily settlement: at first bar crossing 5pm UTC after previous settlement day. `rebate = daily_commission * rebate_pct`.
- Settlement boundary logic: requires `current_day > last_settlement_day AND hour >= 17`. Correct — doesn't double-settle.
- NOTE: Settlement on first bar sets `_last_settlement_day` only (no rebate on day 1). Correct.

### 6. Dashboard — VERIFIED CORRECT

**dashboard_v391.py (2338 lines)**

- `run_backtest()` (line 253): calls `compute_signals_v383(df.copy(), sig_params)` then `Backtester384(run_params).run(df_sig)`. Clean pipeline, no data manipulation between signal and backtest.
- Portfolio mode (line 1887-1938): iterates over selected coins, runs same `run_backtest()` per coin. Results stored directly. No inflation.
- `align_portfolio_equity()` (line 348): aligns equity curves to master datetime index using `ffill`. Portfolio equity = SUM of per-coin equity curves. Each starts at $10K. This means portfolio baseline = 10K * N coins.
- CSV export: writes directly from `trades_df` which comes from `_trades_to_df()` in backtester. No transformation.
- Trade count, win rate, PnL: computed from `metrics` dict returned by backtester. No dashboard-level modification.
- LSG%: `losers[losers.saw_green].count / total_losers`. Uses per-trade `saw_green` flag from engine. Correct.

### 7. Capital Model v2 — NOT AUDITED IN DETAIL

`utils/capital_model_v2.py` was mentioned in previous sessions as having all bugs fixed (E1, C1, C2, C3). Applied only in "Shared Pool" mode. Per-coin independent mode does NOT use it — each coin runs unconstrained.

---

## AUDIT VERDICT

| Component | Verdict | Notes |
|-----------|---------|-------|
| Signal generation | CORRECT | Stoch/Cloud/ATR math matches Pine Script. State machine logic verified. |
| Trade entries | CORRECT | Priority order enforced. Direction lock works. Cooldown works. |
| Trade exits | CORRECT | SL checked first (pessimistic). Exit prices are SL/TP levels, not close. |
| PnL calculation | CORRECT | Percentage-of-notional formula. Gross PnL in trade, net = gross - commission. |
| MFE/MAE | CORRECT | Updated from high/low every bar. saw_green when best unrealized > 0. |
| Commission | 1 BUG | Scale-out entry commission double-count in Trade CSV. Equity curve unaffected. |
| AVWAP | CORRECT | Cumulative VWAP + sigma with floor. Clone is deep copy. |
| Equity curve | CORRECT | Mark-to-market (realized + unrealized). Final bar forced close. |
| Dashboard display | CORRECT | Direct pass-through from engine results. No inflation. |
| CSV export | CORRECT | Direct from trades_df. What engine computed is what you see. |

**The 77K-90K trades and 85-86% LSG numbers are REAL. The engine is doing exactly what the code says.**

---

# PART 4: PENDING ITEMS

1. **Vince ML v2 scope** — NOT finalized. User was still providing constellation examples. Resume scoping in next chat.
2. **Scale-out commission bug** — found but not fixed. User hasn't decided priority. Low severity (equity curve unaffected).
3. **RE-ENTRY logic** — user said "currently totally wrongly programmed." Deferred until after Vince scope.
4. **Dashboard v3.9.2** — build script written (`scripts/build_dashboard_v392.py`), SYNTAX OK, not yet run by user. Next: run build, verify Numba compiles, check parity vs v391.
5. **Architecture breakdown** — next step after scope is finalized. Module structure, interfaces, data contracts, new UML diagrams.

---

# PART 5: RULES FOR NEXT CHAT

1. NEVER paraphrase directional statements. Quote exact words. "Under 60" = "< 60". Period.
2. SCOPE before build. Get user approval before any plan or code.
3. Stochastics are a UNIT. Never analyze K values independently.
4. Vince = research engine (find relationships). NOT Vicky (filter trades).
5. ALL parameters — complete numerical state. No summaries or abstractions.
6. User reads INDICATORS, not price charts.
7. ML reads TRADE CSV output from strategy, not raw OHLCV.
8. Strategy-agnostic base. Andy (forex) must plug in later.
9. No prioritization of relationship questions — data shows what relationships exist.
10. When in doubt, STOP and verify with user. Do not guess.
