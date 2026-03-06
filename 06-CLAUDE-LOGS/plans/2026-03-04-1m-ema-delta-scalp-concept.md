# 1-Minute EMA-Delta Scalp — Concept Note
**Date:** 2026-03-04
**Status:** CONCEPT — not yet validated with chart examples
**Trade Type:** 1-minute EMA cross scalps (one of 4 trade types identified)

---

## Origin

User proposed measuring the delta (distance) between two EMAs as a leading indicator for crossover prediction. Combined with stochastic zone entry and TDI MA cross, this forms a multi-condition entry for 1m scalps that could run all day with no discretion.

## Core Idea

The distance between two EMAs narrows before a crossover. By measuring this delta and setting a threshold, the strategy gets a "crossover approaching" signal BEFORE the actual cross happens. This pre-alert, combined with stoch zone confirmation and TDI MA cross, creates a high-confidence entry.

### The Three Conditions

1. **EMA Delta Threshold (leading indicator)**
   - Delta = abs(EMA_short - EMA_long) — e.g., abs(EMA55 - EMA89) on 1m chart
   - When delta narrows below threshold → pre-alert: crossover is approaching
   - This is mathematically equivalent to a custom MACD approaching zero

2. **Stochastic Zone Entry (energy confirmation)**
   - All 4 stochastics (9/14/40/60) enter oversold (below 20) or overbought (above 80)
   - Confirms the directional energy is present, not just a flat squeeze

3. **TDI MA Cross (trigger)**
   - TDI price line crosses its moving average (RSI=9, Smooth=5, Signal=10, BB=34)
   - Within a "threshold" of the MA — exact threshold TBD
   - This is the final confirmation that fires the trade

**Entry = all three conditions true simultaneously.**

## What Was Already Known (from trend-hold study)

The user previously described the 1m trade type:
- 55/89 EMA cross
- All 4 stochs align
- Move to BE after cross

The EMA-delta concept ENHANCES this by:
- Replacing "wait for EMA cross" with "detect approaching cross via delta threshold"
- Adding TDI MA cross as a timing trigger
- Making the whole thing quantifiable and backtestable

## Management (Speculative)

The delta could also modulate position management:
- Delta EXPANDING after entry = trend strengthening → hold
- Delta COMPRESSING back = trend weakening → tighten trail / exit
- Similar concept to how BBW spectrum works for the trend-hold type

## Parameters for Vince to Optimize

| Parameter | Description | Starting Range |
|-----------|-------------|---------------|
| EMA pair | Which two EMAs to measure delta between | 55/89 (default), also test 34/50, 72/89 |
| Delta threshold | How narrow the delta must be to trigger pre-alert | Needs research — try absolute, ATR-normalized, and %-of-price |
| Stoch zone depth | How deep into OS/OB the stochs must go | 20/80 (strict), 25/75 (loose) |
| TDI MA threshold | How close to the MA counts as "within threshold" | Exact cross vs within N points |
| N stochs required | Must all 4 be in zone, or just fast ones (9/14)? | All 4 vs 9+14 only |
| Timeframe | 1m primary, but could test 5m too | 1m |

## Normalization Question

The raw delta (EMA55 - EMA89) will be different in absolute terms for a $0.001 coin vs a $50 coin. Options:
1. **ATR-normalized delta** — delta / ATR(14). Scale-invariant.
2. **Percentage delta** — delta / price * 100. Also scale-invariant.
3. **Sigma-based** — delta / std_dev of recent closes. Statistical approach.

ATR normalization is likely best since ATR is already in the system and adapts to volatility.

## Differences from Trend-Hold Type

| Aspect | Trend-Hold (5m) | 1m Delta Scalp |
|--------|-----------------|----------------|
| HTF filter | 4h/1h session bias + 15m MTF clouds | TBD — may not need HTF for scalps |
| Entry trigger | All 4 stoch K/D cross + BBW + TDI | EMA delta threshold + stoch zone + TDI MA cross |
| Hold duration | Minutes to hours (gate-dependent) | Seconds to minutes |
| TP | Ripster Cloud 4 frozen / % target | Quick — stoch 9 reaching opposite zone? |
| Trail | AVWAP from trade start / +sigma | Move to BE after EMA cross confirms |
| Management | BBW health + TDI 2-candle rule | Delta expanding/compressing? TBD |
| Automation | Partially discretionary (HTF) | Fully automatable — no discretion |

## What This Concept Needs Before Build

1. **Chart walkthrough** — user walks through 1m scalp examples like PUMP/PIPPIN for trend-hold
2. **Delta threshold research** — what numeric values make sense? Needs backtesting data
3. **Management rules** — does the delta-based management work, or is it something else?
4. **Interaction with HTF** — does this scalp type need HTF filter, or is it time-of-day based?
5. **Stoch zone rules** — same "recent zone check" (N=10 bars) as trend-hold, or different for 1m?

## What This Document Is NOT

- This is NOT a build spec
- This is NOT validated — no chart examples reviewed yet
- The parameters are placeholders for Vince to research
- No code should be written until concept is validated with real trade examples
