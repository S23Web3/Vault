# Strategy Scoping: Why v386 Is the Baseline and What Needs to Change

**Date:** 2026-03-04
**Type:** Scoping only — no code, no build
**Source:** Complete review of all session logs, version history, strategy docs, ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0

---

## Context

The user wants to understand the current state of the Four Pillars strategy before any further development. The v391 build failed because it was built without verifying trading rules with the user. This plan captures the full picture from all logs.

---

## The Journey: What Every Version Was Trying to Solve

### The core problem that has never been fully solved:
> "85-92% of trades see green at some point, but exit at a loss."

Every version from v3.5 onward is an attempt to solve this LSG (Loss-from-Green) problem differently.

| Version | What It Tried | Result |
|---------|--------------|--------|
| v3.5.1 | Cloud 3 trail — stay in winners | Bled out |
| v3.6 | AVWAP SL — dynamic levels | Bled out |
| v3.7 | Rebate farming — tight SL/TP, volume = profit | Commission math barely viable |
| v3.7.1 | Fixed phantom trade bug (strategy.close_all) | Commission fixed |
| v3.8 | Cloud 3 filter ON, ATR BE raise, rate-based commission | RIVER: +$18,952 (best result to date) |
| v3.8.3 | D-signal (continuation), scale-out, AVWAP inheritance | D+R grade drag (-$3,323), scale-out insufficient |
| v3.8.4 | Optional per-coin ATR TP | Coin-specific: RIVER needs TP=2.0, KITE/BERA better without |
| v3.8.6 | Stage 2 conviction filter, C disabled | ~40 trades/day (from 93). Higher conviction. **LIVE** |

---

## What v386 Is (The Good Baseline)

**Signal side — correct:**
- Entry trigger: Stoch9 drops below 25 (LONG) / rises above 75 (SHORT)
- Grade A: Stoch14 + Stoch40 + Stoch60 all in zone + Cloud3 ok + Stage 2 conviction
- Grade B: Any 2 of (14/40/60) in zone + Cloud3 ok
- Stage 2: Stoch40 AND Stoch60 both rotated through 20/80 + price at Cloud3 in last 5 bars
- C trades: Disabled

**What is correct in v386:**
- The entry signal grades (A/B/C structure)
- The stochastic periods (9/14/40/60 Raw K, smooth=1)
- Cloud periods (5/12, 34/50, 72/89, 180/200)
- ATR calc (14 Wilder RMA)
- Stage 2 filter logic

**What v386 does NOT have (missing position management):**
- 3-phase SL/TP movement system (spec exists, never built correctly)
- Cloud 2 hard close (spec exists, never implemented)
- Cloud 4 (72/89) computed and used (was never calculated)

---

## What the Spec Says Should Happen (ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0)

This spec was written 2026-02-05. It has never been correctly implemented in any version.

### Entry
- SL = entry ± 2×ATR
- TP = entry ± 4×ATR

### Phase 1: Cloud 2 (EMA 5/12) crosses IN trade direction
- LONG: SL → candle_low − 1×ATR (tightens). TP → current_TP + 1×ATR (expands)
- SHORT: SL → candle_high + 1×ATR (tightens). TP → current_TP − 1×ATR (expands)
- Guard: SL only moves in favorable direction

### Phase 2: Cloud 3 (EMA 34/50) FRESH cross in trade direction (after entry)
- SL shifts by +1×ATR (favorable direction)
- TP shifts by +1×ATR (favorable direction)
- "Fresh" = cross must happen AFTER entry bar (if already crossed, wait)

### Phase 3: Cloud 3 AND Cloud 4 (EMA 72/89) both in sync
- TP removed entirely
- SL becomes continuous ATR trail: highest_high − 1×ATR (LONG), lowest_low + 1×ATR (SHORT)
- Updates every bar a new extreme is made

### Hard Close (any phase)
- Cloud 2 flips AGAINST trade → exit immediately, highest priority, overrides all else

### ADD signals (pullback within trend)
- Stoch9 enters overbought/oversold, then exits
- Stoch40 + Stoch60 stay on trend side of midline (48/52 threshold)
- No SL/TP change — inherits live trade's current phase

---

## What Currently Exists vs What Should Exist

| Component | Current State | Should Be |
|-----------|--------------|-----------|
| Entry signals (v386) | Correct | Keep as-is |
| Initial SL | 2.0×ATR | 2.0×ATR (same) |
| Initial TP | None (trailing only) | 4.0×ATR (spec) |
| Phase 1 (Cloud 2 cross) | NOT IMPLEMENTED | 3-phase system |
| Phase 2 (Cloud 3 cross) | NOT IMPLEMENTED | 3-phase system |
| Phase 3 (Cloud 3+4 sync) | NOT IMPLEMENTED | Continuous ATR trail |
| Cloud 2 hard close | NOT IMPLEMENTED | Immediate exit on flip |
| Cloud 4 computed | NOT computed | Must be added |
| ADD signals | AVWAP-based | Stoch9 pullback exit |
| AVWAP center | Used as SL trail | NOT the SL mechanism — separate concern |

---

## Why v391 Failed (Process Problem, Not Code Problem)

The v391 code was built from the spec doc without the user confirming:
1. That the spec accurately represents how they trade
2. That the chart examples they showed previously match the spec
3. That Phase 3 behavior (continuous trail) is what they actually want

The code itself (clouds_v391.py, four_pillars_v391.py, position_v391.py, backtester_v391.py) is syntactically clean. The logic is based entirely on ATR-SL-MOVEMENT-BUILD-GUIDANCE.md. But the user noted: "I gave you charts to read in the past and you skipped parts and were even wrong about it."

This means the spec itself may be incomplete or inaccurate relative to how the user actually manages positions on a chart.

---

## The Real Gap: What Has Never Been Verified

The fundamental open question is:
**Does ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 accurately and completely describe how the user manages positions?**

Specifically, these details from the spec have never been confirmed on a real trade example:
1. Phase 1: SL anchors to candle_low/high (not just shifts by ATR) — is the anchor correct?
2. Phase 2: Both SL and TP shift by +1×ATR — is the amount right?
3. Phase 3: TP removed, continuous trail at highest_high/lowest_low − 1×ATR — is this the exit?
4. Hard close: Any Cloud 2 flip = immediate exit — is this truly any flip, or only after Phase 1?
5. ADD midline: 48/52 threshold (not 50) — is this right?

---

## The Next Build (v391 Correct Approach)

When ready to build, the correct sequence is:
1. User confirms each phase rule (ideally with a chart example or verbal walkthrough)
2. Confirm which files from the existing v391 build can be kept vs rewritten
3. Confirm ADD signal logic (stoch9 pullback is the spec — user to confirm)
4. Build against confirmed rules only

**Files that would be needed:**
- `signals/clouds_v391.py` — Cloud 4 computation, cross detection (EXISTS, may be correct)
- `signals/four_pillars_v391.py` — v386 signals + cloud columns wired in (EXISTS, may be correct)
- `engine/position_v391.py` — 3-phase SL, Trade391 dataclass (EXISTS, rules unverified)
- `engine/backtester_v391.py` — Backtester391, hard close priority (EXISTS, rules unverified)
- `scripts/build_strategy_v391.py` — build script (EXISTS)

**Critical files NOT to change:**
- `signals/state_machine_v390.py` — stoch A/B/reentry logic is correct (reuse)
- `signals/four_pillars_v386.py` — entry signal grades correct (reuse or extend)

---

## Summary

The strategy has evolved through 8 versions trying to solve one problem: trades see green but exit at a loss. The signal side (v386) is the best and is live. The position management side has NEVER been correctly implemented — the spec (ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0) has existed since 2026-02-05 but was never built faithfully. v391 was the first serious attempt but was built without user rule confirmation. The next step is to verify the spec against user-confirmed behavior, then build v391 correctly.
