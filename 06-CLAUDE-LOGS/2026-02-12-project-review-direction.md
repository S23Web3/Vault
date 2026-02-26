# Project Review & Direction — 2026-02-12

## v3.8.4 Current State

| Metric | RIVER | KITE | BERA | Combined |
|--------|-------|------|------|----------|
| Trades | 2,099 | 2,062 | 2,108 | 6,269 |
| WR | 43% | 40% | 39% | ~40% |
| Net+Reb | $7,911 | $3,551 | $2,410 | $13,872 |
| $/Trade | $3.77 | $1.72 | $1.14 | $2.21 |
| MaxDD | $5,224 | $1,697 | $1,588 | $6,138 |
| DD% | 36.0% | 13.5% | 13.7% | 35.3% |
| TP exits | 528 | 565 | 585 | 1,678 |
| SL exits | 1,527 | 1,432 | 1,447 | 4,406 |

Config: $10K account, $5K notional, 20x lev, SL=2.5 ATR, TP=2.0 ATR, 70% rebate.

---

## The Math Problem

**R:R ratio is inverted.** TP = 2.0 ATR, SL = 2.5 ATR → R:R = 0.8.

Breakeven win rate at 0.8 R:R = `1 / (1 + 0.8)` = **55.6%**.

Actual WR = 40%. **The raw trading edge is negative.**

Where the profit comes from:
- $60.87M volume × 0.08% commission × 70% rebate ≈ $34K in rebates
- Net P&L (before rebate) is likely **negative** — rebates carry the system

This isn't inherently bad. Volume generation with a non-destructive strategy is a valid model. But it means:

> **Improvement = making the raw edge positive (or less negative) while maintaining volume.**

---

## Critical Bug: BE Raise Completely Missing in v3.8.4

`position_v384.py` has **zero** breakeven raise logic. Both `close_at()` and `do_scale_out()` hardcode `be_raised=False`.

Compare with `position.py` (v3.7.x) which had full BE raise with `be_trigger_atr` and `be_lock_atr` params.

**This was the #1 optimization lever identified in v3.7.1 analysis** (68-84% of losers saw green). It was dropped during the v3.8.x refactor.

---

## Deep Analysis: What The System Actually Needs

Malik's constraint: **never take fewer trades**. The volume is the business model. Every valid signal enters.

This means the entire optimization space is on the **exit side**:

### 1. Asymmetric Exit Management (the core problem)

Current: fixed TP at 2.0 ATR, fixed SL at 2.5 ATR → reward < risk.

What an ML system should do here is NOT meta-label entries. It should **dynamically manage exits** based on regime and trade state.

**Concept: ML Exit Classifier**

At every bar while a position is open, evaluate:
- Should I tighten SL? (protect profit)
- Should I widen TP? (let it run)
- Should I close now? (optimal exit timing)

Features available per-bar (no lookahead):
- Bars held
- Current unrealized P&L / R-multiple
- AVWAP distance (price vs AVWAP center, sigma bands)
- Stochastic state (are stochs rolling over?)
- Volume profile (is volume confirming the move?)
- ATR expansion/contraction (is volatility changing?)
- Cloud state change (did cloud3 flip?)

Label: **Remaining Favorable Excursion (RFE)** — from this bar forward, how much more profit does this trade capture before it closes?

This is a regression problem, not classification. Train on historical trades using MFE/MAE data you already collect.

### 2. Restore + Optimize BE Raise (immediate win)

Step 1: Add BE raise back to `position_v384.py`.

The logic should be:
```
After N bars (or when price reaches X ATR from entry):
  → Move SL to entry + small buffer (cover commission)
  → be_raised = True
```

With 80% of losers seeing green, even a simple BE raise at 0.5 ATR profit, locking at 0.1 ATR, would convert ~40-50% of current losers into scratches/small wins.

**Impact estimate:**
- Current: 4,406 SL exits × avg loss ≈ ~$12.50 each = ~$55K in losses
- If BE raise converts 40% to scratches: save ~$22K
- Net improvement: $22K → total return jumps from 138% to ~360%

### 3. Multi-Tier Exit (scale-out rethink)

Current scale-out requires AVWAP+2sigma — too aggressive, rarely triggers.

Better architecture:
```
Tier 1: At 1.0 ATR profit → close 25%, move SL to BE
Tier 2: At 2.0 ATR profit → close 25%, trail SL at AVWAP center
Tier 3: At 3.0 ATR profit → close 25%, trail SL at AVWAP+1sigma
Tier 4: Remainder rides with tight trail until stopped out
```

This creates convex payoff: small frequent losses, occasional large winners. Exactly what you want.

### 4. Conditional SL Width (not fewer trades — smarter risk)

Every signal still enters. But the SL width varies based on entry quality:

| Entry Grade | Current SL | Proposed SL |
|-------------|-----------|-------------|
| A (full rotation) | 2.5 ATR | 2.5 ATR (keep) |
| B (partial) | 2.5 ATR | 2.0 ATR |
| C (continuation) | 2.5 ATR | 1.5 ATR |
| D (pinned 60K) | 2.5 ATR | 2.0 ATR |
| R (re-entry) | 2.5 ATR | 1.5 ATR |
| ADD (AVWAP add) | AVWAP 2σ | AVWAP 1.5σ |

Same number of trades. Lower average loss per trade. Volume unchanged.

### 5. ML Architecture Reframe

**Current ML stack (meta-labeling):** predicts "should I take this trade?" → WRONG for this system.

**Proposed ML stack (exit optimization):**

```
Module 1: RFE Predictor (XGBoost regression)
  Input: per-bar features while trade is open
  Output: predicted remaining favorable excursion in R-multiples
  Action: If RFE < 0.2R → tighten SL to lock current profit

Module 2: Regime Classifier (XGBoost classification)  
  Input: market-level features (ATR trend, volume trend, stoch alignment)
  Output: trending / ranging / volatile regime
  Action: 
    Trending → wider TP (3.0 ATR), standard SL
    Ranging → fixed TP (1.5 ATR), tight SL (1.5 ATR)
    Volatile → no TP, trail with AVWAP, wider SL (3.0 ATR)

Module 3: Bet Sizing (optional, advanced)
  Input: RFE prediction confidence + regime
  Output: position size multiplier (0.5x to 1.5x of base notional)
  Constraint: total notional across positions ≤ 4× base
```

This keeps every entry. ML only affects HOW you manage the trade once open.

---

## Priority Execution Order

### Phase 1: Immediate (fix what's broken)
1. **Add BE raise back to position_v384.py** — trigger at 0.75 ATR profit, lock at 0.1 ATR above entry. Test on RIVER/KITE/BERA.
2. **Fix R:R ratio** — test TP=3.0 ATR with SL=2.5 ATR (R:R=1.2). Even with lower WR, net expectancy should improve.
3. **Run capital_analysis_v384 with both changes** — compare against current baseline.

### Phase 2: Multi-tier exits (1 week)
4. Implement tiered scale-out (25% at 1/2/3 ATR milestones).
5. Backtest tiered vs fixed TP across all 3 coins.
6. Measure: does volume decrease? (It shouldn't — same entries.)

### Phase 3: ML exit optimization (2 weeks)  
7. Build RFE dataset from existing trades (MFE data already collected).
8. Train XGBoost regressor on per-bar features → RFE.
9. Implement real-time RFE scoring in backtester loop.
10. Backtest ML-managed exits vs static exits.

### Phase 4: Regime awareness (3 weeks)
11. Build regime classifier on market features.
12. Integrate regime → exit parameter selection.
13. Full portfolio backtest with regime-adaptive exits.

---

## What NOT To Build

- Entry filters (meta-labeling that skips trades) — kills volume
- Complex neural networks — XGBoost is sufficient, interpretable, fast
- Overfitted per-coin parameters — the system should generalize
- Bayesian optimization on SL/TP multipliers alone — the problem is structural (fixed exits), not parametric

---

## Summary

The system works. 138.7% return on 3 coins is solid. But it's fragile — profit depends heavily on rebates masking a negative raw edge.

Three changes transform this from "rebate farming with a non-destructive strategy" into "profitable strategy amplified by rebates":

1. **Restore BE raise** (immediate, biggest impact per line of code)
2. **Fix the R:R inversion** (TP should be ≥ SL, not smaller)
3. **ML on exits, not entries** (the actual alpha is in exit timing, not signal generation)

The Four Pillars signal generation is good enough. The entries work. The exits are where money is left on the table.
