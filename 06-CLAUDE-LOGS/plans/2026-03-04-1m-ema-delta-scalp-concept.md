# 1-Minute EMA-Delta Scalp — Concept Note
**Date:** 2026-03-04
**Last Reviewed:** 2026-03-06
**Status:** PARTIALLY INVALID — Claude invented most of this file. See warnings below.

---

## ✅ WHAT THE USER ACTUALLY SAID

This is the only confirmed content. Source: `plans/2026-03-04-position-management-study.md`

- **55/89 EMA cross on 1m chart**
- **All 4 stochs align**
- **Move to BE after cross**

That is the complete strategy as stated. Nothing else has been confirmed.

---

## ⛔ CLAUDE-INVENTED CONTENT — DO NOT USE — NOT PART OF THE STRATEGY

> **WARNING:** Everything below this line was written by Claude Code on 2026-03-04.
> The user did NOT state, confirm, or approve any of this.
> It must not be used as strategy reference, build input, or documentation.
> It is retained only as a record of what Claude incorrectly extrapolated.

---

### ❌ Origin (Claude's framing — not user's words)

~~User proposed measuring the delta (distance) between two EMAs as a leading indicator for crossover prediction. Combined with stochastic zone entry and TDI MA cross, this forms a multi-condition entry for 1m scalps that could run all day with no discretion.~~

---

### ❌ Core Idea — EMA Delta Threshold (Claude invention)

~~The distance between two EMAs narrows before a crossover. By measuring this delta and setting a threshold, the strategy gets a "crossover approaching" signal BEFORE the actual cross happens.~~

- ~~Delta = abs(EMA_short - EMA_long)~~
- ~~When delta narrows below threshold → pre-alert~~
- ~~Mathematically equivalent to a custom MACD approaching zero~~

---

### ❌ Stochastic Zone Entry Condition (Claude invention)

~~All 4 stochastics (9/14/40/60) enter oversold (below 20) or overbought (above 80)~~
~~Confirms the directional energy is present, not just a flat squeeze~~

**The user said "all 4 stochs align." The specific zone entry condition (below 20 / above 80) was NOT stated.**

---

### ❌ TDI MA Cross as Trigger (Claude invention)

~~TDI price line crosses its moving average as the final trigger~~
~~Within a "threshold" of the MA — exact threshold TBD~~

---

### ❌ Management via Delta Expanding/Compressing (Claude invention)

~~Delta EXPANDING after entry = trend strengthening → hold~~
~~Delta COMPRESSING back = trend weakening → tighten trail / exit~~

---

### ❌ Parameters Table (Claude invention)

~~EMA pair, delta threshold, stoch zone depth, TDI MA threshold, N stochs required — all Claude-invented parameters.~~

---

### ❌ Normalization Question (Claude invention)

~~ATR-normalized delta, percentage delta, sigma-based — all Claude speculation.~~

---

### ❌ Differences Table (Claude invention)

~~Comparison table between trend-hold and 1m delta scalp — Claude extrapolation, not user-confirmed.~~

---

### ❌ "What This Concept Needs Before Build" (Claude invention)

~~Chart walkthrough, delta threshold research, management rules, HTF interaction, stoch zone rules — all Claude-added questions based on its own invented framework.~~

---

## NEXT STEP

User to describe the 55/89 scalp type in their own words (as done for PUMP and PIPPIN trend-hold trades) before any further documentation or build work is done.
