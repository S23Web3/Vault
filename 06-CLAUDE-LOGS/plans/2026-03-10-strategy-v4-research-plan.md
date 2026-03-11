# Strategy v4 — Research Confirmation + Critical Review

## Context

The user wants two things:
1. Confirmation that research has been done (scenario PNGs exist, builds verified)
2. A critical (non-yes-man) review of the strategy v4 concept — why is progression stalled

This is a RESEARCH AND REVIEW session. No code. No builds. Output is analysis.

---

## What Has Been Built (Confirmed by Filesystem)

### SL Lifecycle Visualizer (55/89 scalp)
All 12 scenario PNGs confirmed present:
`PROJECTS/four-pillars-backtester/results/sl_lifecycle/scenario_01.png` through `scenario_12.png`

This means the user RAN `visualize_sl_lifecycle_v2.py`. The 55/89 engine is built and tested (7/7 tests pass per session log 2026-03-07).

### Strategy Catalogue (S1-S11)
- `visualize_strategy_perspectives.py` — written, py_compile PASS. Status: written, py_compile PASS — user should have run it to produce S1-S5 PNGs in `results/strategy_perspectives/`
- `visualize_strategy_perspectives_v2.py` — S6-S11, same status
- The session log says "awaiting user run" — unclear if actually run

### Strategy v4 Design
`C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\STRATEGY-V4-DESIGN.md` — WRITTEN, contains design but backtest results table is BLANK.

---

## Why Progression Is Stalled — Critical Analysis

### Problem 1: The Design Doc Contradicts Session 4

**STRATEGY-V4-DESIGN.md** (Session 3, 2026-03-07) specifies the hybrid model:

```
Stage 1 trigger: stoch_9 < 40 AND stoch_40 > 50 AND stoch_60 > 50
```

**Session 4** (2026-03-10, today) rejected this. The cascade model says:
- Stoch 40 crosses OUT OF oversold (e.g., crosses back above 30)
- SMI 60 catches up AFTER (not a gate)

These are fundamentally different. The design doc has NOT been updated. So we have two models: one in the document, one in the latest session. We cannot build from a contradicted spec.

### Problem 2: The Cascade Model Has Unscoped Components

The cascade model requires things not in the current indicator stack:

| Component | In current code? | Complexity to add |
|-----------|-----------------|-------------------|
| Stoch 40 crosses out of oversold | Yes (crossover logic exists) | Low |
| Stoch 9 divergence detection | NO | HIGH — requires swing detection, multi-bar comparison |
| Price descending channel detection | NO | VERY HIGH — swing highs/lows, trendline logic |
| SMI 60 catches up after | Yes (threshold check) | Low |

If the cascade model requires divergence detection and channel detection — those are 2-3 separate engineering projects before a single signal fires.

**This is scope creep.** The design doc's validation criterion says "signal count must be >=50% of v3.8.4." We have no estimate of signal count with these filters.

### Problem 3: The Real Signal Per Core-Trading-Strategy.md Is Stoch 55 — Not In Either Model

Core-Trading-Strategy.md (v2, 2026-01-29) is explicit:
- Entry trigger: **Stoch 55 crosses UP**
- Stoch 9 < 20 = staging condition
- Stoch 55 cross = the actual entry

The current bot (v3.8.4) uses Stoch 9 crossover as the trigger. Stoch 55 is NOT in the bot at all.
The v4 hybrid model uses Stoch 9 crossover (same as v3.8.4, just with different threshold values).
The v4 cascade model uses Stoch 40 crossover as the trigger.

Neither v4 variant implements the core strategy as written. This is the deepest mismatch in the whole project and has not been stated plainly in any session.

### Problem 4: No Baseline Backtest Exists

STRATEGY-V4-DESIGN.md has a validation criteria table and a blank results table. We are building v4 to fix R:R = 0.28, but we have NEVER confirmed that v3.8.4 on historical data also produces R:R ~= 0.28.

If the backtester produces R:R > 1.0 on historical data but live shows 0.28, the problem is execution (slippage, timestamp, SL placement) — NOT the signal model. The fix would be in the bot, not in a new strategy.

This baseline run takes minutes on existing infrastructure and would either confirm or eliminate the signal hypothesis entirely.

### Problem 5: LSG Analysis Points to EXIT, Not Entry

From MEMORY.md (confirmed fact): "85-92% of losers were profitable at some point — TP or ML filter is key lever."

If 85-92% of losing trades were at some point profitable, the entry is getting direction RIGHT most of the time. The problem is not entry quality — it's that the exit doesn't capture profits when they exist. The v4 redesign is entirely focused on entry. This may be fixing the wrong variable.

The design doc does note this ("if entry quality improves, TTP may already work better") but doesn't fully confront the implication: maybe fix the exit first.

---

## The Actual Path to "Next Level"

The "next level" = running backtester numbers that either confirm or reject the signal hypothesis.

**Fastest unblock (2 steps, no new code needed):**

Step 1 — Run v3.8.4 backtester on 3 months of 5-6 coins.

```
python scripts/run_backtest.py --symbol SUIUSDT --save-db
```

Record R:R, WR, avg win, avg loss. If this matches live stats (R:R ~= 0.28), the signal hypothesis is supported and v4 build is justified. If baseline R:R > 1.0, the problem is bot execution — and the fix is in the bot, not the signal.

Step 2 — If hypothesis confirmed: build the SIMPLEST v4 variant first.
The simplest change = modify the state machine thresholds only. No divergence detection, no channel detection. Just change:

- Stage 1 trigger: stoch_9 < 40 AND stoch_40 > 50 AND stoch_60 > 50
- Signal fire: stoch_9 crosses back above 40 (not above 25)

This is ~20 lines of code change to signals/state_machine.py. Run side-by-side with v3.8.4. Get numbers. Then decide if more complexity is needed.

---

## Cascade Overlap Problem — Deep Analysis

The user flagged: "sometimes it could be overlapping — up to 4 stochastics might go in the same candle."

This is a real mathematical problem with the cascade model, rooted in how Raw K stochastics work.

### Raw K Mechanics (from stochastics.py)

```python
stoch_k = 100 * (close - lowest(k_len)) / (highest(k_len) - lowest(k_len))
```

Key properties:
- **No smoothing** — Raw K reacts to the current bar's close immediately, every bar
- **Denominator scales with window**: Stoch 9 uses 9-bar range, Stoch 60 uses 60-bar range
- **Same close change -> Stoch 9 moves MORE than Stoch 60** (smaller denominator)

### What Happens on a Strong Reversal Candle

Given the 4 stochastics (9, 14, 40, 60 bars):
- All 4 are computed from the SAME current bar's close
- On a strong bullish reversal candle (large body), the close snaps up sharply

Example: Price drops for 50 bars, then a single reversal candle closes 3% up.
- Stoch 9: 9-bar range is entirely within the recent decline -> close is near the new 9-bar high -> Stoch 9 snaps from <20 to >70+ in ONE bar
- Stoch 40: 40-bar range is larger, close is lower relative to 40-bar range -> Stoch 40 also jumps, but to a lower value
- Stoch 60: 60-bar range even larger -> Stoch 60 jumps least per the same close move

**Critical result:** On a sharp V-bottom, ALL 4 stochastics can cross their thresholds on the SAME BAR. The cascade (Stoch 40 crosses first, SMI 60 catches up over subsequent bars) only exists when the recovery is GRADUAL.

### The Two Reversal Types and Their Cascade Behavior

| Reversal Type | Stoch 40 | Stoch 60 | Cascade visible? |
|--------------|----------|----------|-----------------|
| Gradual (multiple bars recovering) | Crosses out of oversold on bar N | Crosses out of oversold on bar N+3 to N+8 | YES — true cascade |
| Sharp V-bottom (1-2 bar spike) | Crosses out of oversold on bar N | Also crosses out of oversold on bar N (or N+1) | NO — simultaneous |

### What This Means for the Cascade Model

The cascade model works as described by Malik ONLY on gradual recoveries. On sharp V-bottoms:
- All 4 stochastics snap simultaneously
- The cascade collapses into the same pattern as v3.8.4 (simultaneous pile-in)
- ATR is highest on V-bottoms -> worst entries

**This is not a flaw in the theory — it is a filter that's hidden in the observation.**

When Malik says "Stoch 40 crosses first," he is implicitly observing setups where the recovery was gradual enough to create the cascade. He's NOT observing V-bottoms because those don't have the cascade structure.

### What This Means for the Build

The cascade model requires a GUARD condition: "was the recovery gradual enough to have temporal separation between Stoch 40 and Stoch 60 crossing?"

One approach — minimum bar gap guard:

```
Stage 1 starts when: stoch_9 enters extreme (<25)
Accumulate:
  - stoch_40_cross_bar: bar number when stoch_40 first crosses above 30
  - stoch_60_cross_bar: bar number when stoch_60 first crosses above 25
Signal valid only if: stoch_60_cross_bar - stoch_40_cross_bar >= min_cascade_gap (e.g., 2-5 bars)
```

If both cross on the same bar -> reject signal (V-bottom, not a genuine cascade).

This is a new parameter (`min_cascade_gap`) that does NOT exist in the current state machine. It would need to be added.

### Alternative Interpretation — ATR as the Proxy

Instead of measuring bar gaps (complex), use ATR at the moment stoch_40 crosses:
- Low ATR at cross = gradual, orderly recovery = valid cascade
- High ATR at cross = sharp V-bottom = cascade collapsed = reject

This is simpler and may already be partially captured by the 2x ATR SL width. But it's implicit, not explicit.

---

## Critical Questions That Must Be Answered Before Building Anything

1. **Which model?** Hybrid (stoch 40/60 above 50 as gate) or cascade (stoch 40 crosses out of oversold)? These are different. The design doc says hybrid. Session 4 says cascade. Pick one and close it.

2. **Is Stoch 55 the trigger?** The Core Strategy says yes. v4 proposals say no. If Stoch 55 is supposed to be the trigger — build that. If not, explain why Core-Trading-Strategy.md v2 is wrong.

3. **Run the baseline first?** Yes or no. If yes, it unblocks everything. If no, explain what other evidence justifies building v4 before seeing v3.8.4 baseline numbers.

4. **Divergence detection: in scope or out of scope for v4.0?** If yes, the build is 3-4x more complex than what's in the design doc. If no, the cascade model description needs to be updated to remove the divergence requirement.

---

## Files Critical to This Review

| File | Role |
|------|------|
| `02-STRATEGY/STRATEGY-V4-DESIGN.md` | Living design doc — contradicted by Session 4, needs update |
| `02-STRATEGY/Core-Trading-Strategy.md` | Source of truth — says Stoch 55 is the entry trigger |
| `06-CLAUDE-LOGS/2026-03-07-strategy-catalogue-visual-plan.md` | Session log with cascade model correction (Session 4) |
| `PROJECTS/four-pillars-backtester/results/sl_lifecycle/` | 12 PNGs confirmed — 55/89 SL lifecycle DONE |
| `PROJECTS/bingx-connector-v2/` | Live bot — baseline backtest comparison target |
| `PROJECTS/four-pillars-backtester/engine/` | Existing backtester infrastructure |

---

## Verification

No code in this plan. Verification = user reads the analysis and decides:
1. Which model to build (close the hybrid vs cascade decision)
2. Whether to run v3.8.4 baseline first
3. Whether Stoch 55 belongs in v4

After those 3 decisions are closed, a build plan can be written.

---

## S1-S11 Thorough Strategy Analysis vs Core Perspective

### Core Perspective Definition (user's exact words)

> "out of stochastics overzone -> other stochastics move with or soon after as base + there was a divergence or at least a regression channel before it"

Three required elements:

- **A — Overzone exit**: stoch_9 exits extreme (< 20 for longs, > 80 for shorts)
- **B — Others follow**: after stoch_9 exits, longer stochastics (40, 60) move in same direction within N bars (cascade)
- **C — Pre-condition**: before the signal, there was EITHER a stoch divergence (price LL + stoch HL) OR an orderly regression channel (price declining in controlled channel, not V-bottom)

| Strategy | A | B | C | Score | Notes |
|----------|---|---|---|-------|-------|
| S1 (Bible / original Four Pillars) | Y | Y partial | Y partial | **75%** | Best alignment |
| S2 (Rebate volume farming) | N | N | N | **0%** | Different paradigm entirely |
| S3 (v3.8 simple crossover) | Y | N | N | **20%** | Has A only |
| S4 (v3.8.4 current — simultaneous) | Y | N VIOLATED | N | **10%** | Pile-in violates B; code contradicts its own description |
| S5 (55/89 EMA scalp) | Y | Y partial | N | **35%** | Macro gate partial B, no divergence |
| S6 (Ripster cloud structural) | N | N | N | **5%** | Cloud structure only, no stochastics |
| S7 (Quad Rotation Stochastic) | Y | Y | Y | **70%** | Highest divergence alignment |
| S8 (Three Pillars / Core-Strategy v2) | Y | Y | N | **45%** | Correct trigger (Stoch 55), no divergence |
| S9 (BBWP volatility filter) | N | N | N | **0%** | Filter only — correct role |
| S10 (ATR Phase exit) | N/A | N/A | N/A | N/A | Exit-side management, not entry |
| S11 (AVWAP structural) | N | N | N | **15%** | Volume context only |

---

### S1 — Bible / Original Four Pillars (75%)

**Source**: `visualize_strategy_perspectives.py` annotate_box, `Trading-Manifesto.md`

Description box reads: "LONG BIAS: Stoch 60 holds above 80 (macro bull) / WAIT FOR: Stoch 9 to dip to oversold (<20) / ENTER: Stoch 9 exits oversold + price on 55 EMA / HOLD: Stoch 40 makes higher lows (divergence)"

- **A** Y — Stoch 9 < 20 explicitly required
- **B** Y partial — Stoch 60 > 80 is a macro condition (it's IN the uptrend, not cascading out of oversold). Stoch 40 divergence check is post-entry hold logic, not pre-entry cascade gate.
- **C** Y partial — "Stoch 40 makes higher lows" IS a divergence element. But it is framed as a hold condition, not a pre-entry filter. The divergence structure is implied, not required to fire the signal.

**Gaps**: Stoch 60 being > 80 is a trend continuation model (pullback in uptrend). The core perspective the user described is more about bottoming/reversal with divergence. These overlap but are slightly different use cases. The S1 model is most aligned for trend continuation pullback re-entries; the core perspective is better for fresh reversals from downtrends.

---

### S2 — Rebate Volume Farming (0%)

No stochastic overzone. No cascade. No divergence. Pure position frequency / rebate model. Not a signal strategy. Completely separate design.

---

### S3 — v3.8 Simple Crossover (20%)

- **A** Y — stoch_9 < 25 entry zone
- **B** N — signal fires on stoch_9 crossing alone, no cascade confirmation
- **C** N — no divergence, no channel

This is the minimum viable signal model. Has the overzone element but nothing else. Produces high signal count but poor quality.

---

### S4 — v3.8.4 Current Bot (10%) — CRITICAL FINDINGS

This is the live bot. The findings here directly explain the R:R = 0.28 problem.

**What the visualizer description says**: "MACRO CONDITION: Stoch 60 pinned above 80" (i.e., uptrend context like S1)

**What the actual code in `state_machine.py` does**:

```python
self.long_60_seen = stoch_60 < cross_low   # cross_low = 25
```

The code requires stoch_60 to go BELOW 25 during Stage 1. The description says stoch_60 should be ABOVE 80. This is a fundamental inversion — the code and the description are measuring opposite conditions.

The simultaneous pile-in requirement means: stoch_9, stoch_14, stoch_40, stoch_60 must ALL be in extreme (< 25-30) at the SAME TIME. This only happens when:

1. There is a sharp, extended decline — everyone is beaten down simultaneously
2. V-bottom or panic-selling scenario — the worst possible entry conditions (high ATR, choppy reversals)

This is the EXACT OPPOSITE of the core perspective. The core perspective requires gradual recovery (cascade). S4 requires simultaneous capitulation before firing. That's why losses are large: entries happen at maximum volatility/disorder.

- **B** N VIOLATED — simultaneous pile-in is the anti-pattern of cascade
- This single finding explains R:R = 0.28.

---

### S5 — 55/89 EMA Scalp (35%)

- **A** Y — Stoch 9 oversold trigger in overzone design
- **B** Y partial — stoch_40 > 50 AND stoch_60 > 50 as GATE condition. These are positioning gates (stochs already above midline = macro healthy), not cascade exits from extreme. This validates uptrend continuation context but doesn't detect the cascade itself.
- **C** N — AVWAP -2 sigma trail is exit-side. No divergence detection on entry.

Better than S4 (no pile-in), but macro gate is not cascade exit. The gate prevents entries in macro downtrends. Still misses the "other stochs move with or soon after" element.

---

### S6 — Ripster Cloud Structural (5%)

Cloud color + cloud alignment only. No stochastics at all. Structurally complementary (confirms trend direction) but implements none of the core elements. Properly used as a filter or exit trigger (candle closes against cloud = exit), not as a signal generator.

---

### S7 — Quad Rotation Stochastic (70%) — CLOSEST TO CORE

Source: `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\Quad-Rotation-Stochastic.md`

Has the most complete divergence implementation of all 11 strategies:

```pinescript
plFound = na(ta.pivotlow(fast_k_val, pivot_left, pivot_right)) ? false : true
oscHL = fast_k_val[pivot_right] > ta.valuewhen(plFound, fast_k_val[pivot_right], 1)
priceLL = low[pivot_right] < ta.valuewhen(plFound, low[pivot_right], 1)
prev_pivot_oversold = ta.valuewhen(plFound, fast_k_val[pivot_right], 1) < os_level
bullish_divergence = priceLL and oscHL and plFound and prev_pivot_oversold
```

This directly implements: "price makes lower low, stoch makes higher low, previous pivot was oversold." That IS the core perspective C element in code.

- **A** Y — oversold filter (< 20) on both current and previous pivot
- **B** Y — has stoch_40 and stoch_60 in the rotation concept (though pivot method focuses on stoch_9 divergence)
- **C** Y — explicit bullish divergence with oversold filter

**Gap**: The pivot method introduces `pivot_right` bars of lookahead delay (default 3 bars). At 5m, that is 15 minutes of delay on a confirmed signal. For high-frequency scalp use, that is costly. The natural state machine approach (described below) is faster and removes lookahead.

---

### S8 — Three Pillars / Core-Trading-Strategy.md v2 (45%)

Source: `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Core-Trading-Strategy.md` (v2, 2026-01-29)

This is the ONLY strategy that implements the correct trigger as documented by Malik: **Stoch 55 crosses UP**.

- **A** Y — Stoch 9 < 20 explicitly as staging condition
- **B** Y — Stoch 55 cross is the entry signal. ATR climbing + BBWP transitioning are continuation checks.
- **C** N — No explicit pre-entry divergence requirement. Momentum continuation check is post-entry ("if momentum declines, exit"). Pre-entry divergence is not in the spec.

Key quote: "Entry: When Stoch 55 crosses UP / Confirm: Momentum continues building after cross"

**The Stoch 55 problem across all strategies**: Every other strategy model (S3, S4, S5, S7, and the v4 proposals) uses Stoch 9 exit or Stoch 40 exit as the entry trigger. NONE implement Stoch 55 as the trigger. This is never stated plainly in any session log. Stoch 55 is not in stochastics.py (which has 9, 14, 40, 60). Adding Stoch 55 is a code change, not just config.

---

### S9 — BBWP Volatility Filter (0% — by design)

BBWP is a filter. It tells you WHEN to be in the market (squeeze = move coming), not WHICH direction or WHAT structure. Scoring it 0% against the core perspective is correct — it's not trying to implement the core perspective.

Correct use: AND-combine with signal. "Only enter if BBWP < 10% (squeeze active)" layered on top of A+B+C signal.

---

### S10 — ATR Phase Exit Management (N/A)

Exit management only. Cloud 2 cross = Phase 1, Cloud 3 cross = Phase 2, Cloud 3+4 sync = Phase 3. Contains ADD signal logic (Stoch 40/60 stay above 48 midline = trend intact for pullback re-entry). This is complementary — plug this into v4 as the exit layer, not the entry layer.

---

### S11 — AVWAP Structural (15%)

AVWAP (Anchored VWAP) shows WHERE volume happened. It validates trend direction (price above AVWAP from low = buyers in control). Does not implement overzone detection, cascade, or divergence. Correct role: structural filter and SL reference. Not a signal generator.

---

## Synthesis: What a Correct v4 Looks Like

Only S1 (75%), S7 (70%), and S8 (45%) have meaningful alignment with the core perspective. A correct v4 takes:

- **S7's divergence detection** (C element — two-cycle stoch_9 lower low / higher low)
- **S1's macro bias** (Stoch 60 > 50 at minimum, ideally > 70, for uptrend context)
- **S8's Stoch 55 trigger** (B element — if keeping Core-Trading-Strategy.md as the reference)
- **S10's exit management** (phase-based SL tightening)

The cascade (B element) in the core perspective can be interpreted two ways:

1. Stoch 55 cross (S8) — the momentum indicator that catches up after stoch_9 enters extreme
2. Stoch 40 exits extreme (cascade model, Session 4) — shorter window exits before longer window

These are not the same instrument. Decision required: which one is the "other stochastics move with or soon after"?

---

## Divergence Stage 1 -> Stage 2: Detection Approaches

### What Stage 1 / Stage 2 Means (from Trading-Manifesto.md)

- **Stage 1**: All stochastics go below 20. Price makes a low. Stochastics bounce back above 20. (Oversold visit — first dip)
- **Stage 2**: Price makes a LOWER LOW. Stochastics make a HIGHER LOW (they stay above 20 or come back less deep). Stochastics turn up -> SIGNAL
- This is a classic bullish divergence: price diverges down, momentum does NOT confirm new lows -> reversal signal

### Approach 1: Natural Two-Cycle State Machine

No lookahead. Detects divergence by tracking two consecutive oversold cycles.

```
States: IDLE -> CYCLE_1 -> COOLDOWN -> CYCLE_2 -> DIVERGENCE_DETECTED

IDLE -> CYCLE_1:
  Trigger: stoch_9 crosses below 25
  Record: price_low_c1 = min(low), stoch_9_low_c1 = min(stoch_9)
  Track minimums each bar while in CYCLE_1

CYCLE_1 -> COOLDOWN:
  Trigger: stoch_9 crosses above 25
  Snapshot: freeze price_low_c1, stoch_9_low_c1

COOLDOWN -> CYCLE_2:
  Trigger: stoch_9 crosses below 25 AGAIN
  Guard: at least 1 bar stoch_9 was above 40 between cycles (genuine bounce)
  Guard: gap between cycles <= max_gap_bars (default 20) — prevents stale cycle
  Record: price_low_c2 = min(low), stoch_9_low_c2 = min(stoch_9)

CYCLE_2 -> DIVERGENCE_DETECTED:
  Trigger: stoch_9 crosses above 25
  Conditions:
    price_low_c2 < price_low_c1    (price made lower low — divergence)
    stoch_9_low_c2 > stoch_9_low_c1  (stoch made higher low — divergence)
    stoch_40 >= 30                 (cascade gate: stoch_40 already exiting extreme)
  If all conditions met -> divergence_signal = True, trigger entry
```

New parameters:

- `div_max_gap_bars` (default 20): max bars between cycle 1 exit and cycle 2 entry
- `div_min_bounce` (default 1): min bars stoch_9 above 40 between cycles

**Advantages**: No lookahead delay, pure event-driven, maps directly to existing state machine pattern.

**Disadvantages**: Two full dips required — misses single-bottom setups. Resets if gap too large.

### Approach 2: Pivot Method (from S7/Quad Rotation)

Python translation of the PineScript pivot divergence detector:

```python
def find_pivot_lows(stoch_series, left=3, right=3):
    """Find indices where stoch_series is a local minimum (lower than left/right neighbors)."""
    pivots = []
    for i in range(left, len(stoch_series) - right):
        window = stoch_series[i - left:i + right + 1]
        if stoch_series[i] == min(window):
            pivots.append(i)
    return pivots

def detect_bullish_divergence(closes, stoch_9, left=3, right=3, os_level=20):
    """
    Bullish divergence: price makes lower low at current pivot,
    stoch_9 makes higher low. Previous pivot must have been oversold.
    Returns divergence_at_bar or None.
    """
    pivots = find_pivot_lows(stoch_9, left, right)
    if len(pivots) < 2:
        return None
    curr_piv = pivots[-1]
    prev_piv = pivots[-2]
    price_ll = closes[curr_piv] < closes[prev_piv]     # price lower low
    stoch_hl = stoch_9[curr_piv] > stoch_9[prev_piv]  # stoch higher low
    prev_oversold = stoch_9[prev_piv] < os_level       # prev pivot was oversold
    if price_ll and stoch_hl and prev_oversold:
        return curr_piv
    return None
```

**Advantages**: Can detect divergence at any bar, not just two-cycle structure. More flexible.

**Disadvantages**: Requires `right` bars of lookahead (signal confirmed 3 bars after the fact). In backtester this is fine; in live trading it means 15-minute delay at 5m.

### Recommended: Natural Two-Cycle for v4

The two-cycle state machine is the right choice for the Python backtester:

1. No lookahead — no look-forward bias in backtest results
2. Aligns directly with how Trading-Manifesto.md describes Stage 1 / Stage 2
3. Can be added to existing state_machine.py as a new state layer
4. Parameters are sweepable

---

## Regression Channel Detection

### Purpose

A regression channel (orderly descending price in a defined band) is the pre-condition that makes a genuine cascade possible. V-bottoms do NOT have a regression channel — price collapses and spikes without structure. The channel gate filters V-bottoms before they reach the signal layer.

### Implementation (Pure NumPy, no external deps)

```python
def compute_regression_channel(closes, lookback=20):
    """
    Linear regression channel over the last N bars.
    Returns: (slope_pct, r_squared, band_width_pct)
      slope_pct: slope normalized by mean price (negative = descending)
      r_squared: fit quality 0-1 (higher = more orderly channel)
      band_width_pct: 2*std of residuals as % of mean (tighter = narrower channel)
    """
    p = np.array(closes[-lookback:], dtype=float)
    if len(p) < 3:
        return 0.0, 0.0, 0.0
    x = np.arange(len(p), dtype=float)
    xm, ym = x.mean(), p.mean()
    cov = np.sum((x - xm) * (p - ym))
    var = np.sum((x - xm) ** 2)
    if var == 0 or ym == 0:
        return 0.0, 0.0, 0.0
    slope = cov / var
    slope_pct = slope / ym
    intercept = ym - slope * xm
    fitted = slope * x + intercept
    residuals = p - fitted
    std_res = np.std(residuals)
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((p - ym) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    band_width_pct = (2 * std_res) / ym
    return slope_pct, r_squared, band_width_pct
```

### Gate Conditions for LONG Setup (descending channel before reversal)

```python
slope_pct, r_sq, band_w = compute_regression_channel(closes, lookback=reg_lookback)
channel_valid = (
    slope_pct < -reg_slope_min and    # price declining (e.g., < -0.001 = -0.1%/bar)
    r_sq > reg_r2_min and             # channel is orderly (e.g., > 0.55)
    band_w < reg_band_max             # channel is tight (e.g., < 0.03 = 3%)
)
```

Sweep parameters:

- `reg_lookback` (default 20): bars for regression window
- `reg_slope_min` (default 0.001): minimum slope magnitude (0.1%/bar at 5m = 2%/hr)
- `reg_r2_min` (default 0.55): minimum R^2 for "orderly" channel
- `reg_band_max` (default 0.03): maximum channel width as % of price

### The Relationship Between Channel and Cascade

These are measuring the same thing from two angles:

- Orderly descending channel -> price recovers gradually -> each stochastic exits extreme over multiple bars -> TRUE cascade
- Sharp V-bottom -> no channel -> all stochastics snap simultaneously -> FAKE cascade (same as S4 pile-in)

The channel gate and the `min_cascade_gap` bar guard from the cascade analysis are **redundant but complementary**. If one is chosen, the other is optional. The channel gate is easier to tune visually. The bar gap guard is more direct but requires tracking timestamps.

---

## Revised Combined v4 Spec

This is what a v4 that fully implements the core perspective looks like:

### Entry Signal Pipeline (LONG)

**Layer 1 — Macro Gate** (filter — non-sweepable baseline):

- `stoch_60 >= 40` (macro not in deep oversold or macro bearish)
- Optional: `stoch_60 >= 50` (only enter in macro uptrend pullbacks)

**Layer 2 — Channel Gate** (pre-condition):

- `compute_regression_channel(closes, reg_lookback)` -> slope, r_sq, band_w
- `channel_valid = slope < -reg_slope_min AND r_sq > reg_r2_min AND band_w < reg_band_max`
- Channel gate must be TRUE when Stage 1 begins (can relax to: was active at any point in the last N bars)

**Layer 3 — Divergence Detection** (two-cycle state machine):

- Cycle 1: stoch_9 enters extreme (< 25), records price_low_c1 + stoch_9_low_c1
- Bounce: stoch_9 exits (>= 25) and reaches > 40 for at least 1 bar
- Cycle 2: stoch_9 enters extreme again (< 25), records price_low_c2 + stoch_9_low_c2
- Divergence confirmed when: price_low_c2 < price_low_c1 AND stoch_9_low_c2 > stoch_9_low_c1

**Layer 4 — Cascade Gate** (confirmation):

- At Cycle 2 exit (stoch_9 crosses above 25):
  - `stoch_40 >= 30` (Stoch 40 already exited extreme — "moved with or soon after")
  - Optional: bar gap between stoch_40 exit and stoch_60 exit >= min_cascade_gap (gradual recovery check)

**Signal fires** -> enter LONG at close of signal bar

**Exit**: S10 ATR Phase logic (Cloud 2 cross = Phase 1, Cloud 3 = Phase 2, Cloud 4 sync = Phase 3)

### What This Model Does NOT Include (scope boundary)

- Stoch 55 as trigger — this would require adding Stoch 55 to stochastics.py and deciding it replaces or supplements Layer 4
- Stoch 9 vs price pivot divergence (Approach 2) — out of scope for v4.0, available as v4.1 upgrade
- ML filters (B3-B10) — blocked on Vince B1 per MEMORY.md
- BBWP filter — add later as Layer 0, does not affect signal logic

### Parameter Count (sweepable)

| Parameter | Default | Min | Max | Step |
|-----------|---------|-----|-----|------|
| reg_lookback | 20 | 10 | 40 | 5 |
| reg_slope_min | 0.001 | 0.0005 | 0.003 | 0.0005 |
| reg_r2_min | 0.55 | 0.3 | 0.8 | 0.05 |
| reg_band_max | 0.03 | 0.01 | 0.06 | 0.01 |
| div_max_gap_bars | 20 | 10 | 40 | 5 |
| div_min_bounce | 1 | 1 | 5 | 1 |
| stoch_60_macro_min | 40 | 30 | 60 | 5 |
| min_cascade_gap | 0 | 0 | 5 | 1 |

Total: 8 sweep parameters. With the above ranges, ~2,000-5,000 combinations. Manageable with the existing backtester + vince grid.

---

## Updated Critical Questions (revised)

1. **Channel gate: in scope for v4.0?**
   The regression channel is the cleanest way to prevent V-bottom entries. But it adds 4 new parameters. If yes, build it. If no, use `min_cascade_gap` as the simpler proxy.

2. **Two-cycle divergence: in scope for v4.0?**
   This is the core of "divergence from Stage 1 to Stage 2." It is what the Trading Manifesto describes. It requires the state machine to track two complete oversold cycles. This is a meaningful build (not 20 lines). If yes, scope it. If no, v4.0 is just the threshold change (hybrid model, not cascade model).

3. **Stoch 55: add it?**
   Core-Trading-Strategy.md says it is the trigger. No current code has it. Adding it = new stochastics.py entry + new state layer. Either adopt it as the B-element (replacing Stoch 40 cascade) or explain why the document is superseded.

4. **Run v3.8.4 baseline first?**
   This remains the fastest unblock. If backtester R:R > 1.0 on historical data but live shows 0.28, the fix is in bot execution (slippage, SL distance, timestamp). The entire v4 signal redesign would be unnecessary.

---

## Updated Verification

No code in this plan. Decisions required:

1. Run v3.8.4 backtester baseline: YES / NO
2. Channel gate in v4.0: YES / NO
3. Two-cycle divergence in v4.0: YES / NO
4. Stoch 55 in v4.0: YES / NO
5. Keep cascade model (Session 4) OR revert to hybrid model (design doc): CASCADE / HYBRID

Once these 5 decisions are locked, a build plan can be written.
