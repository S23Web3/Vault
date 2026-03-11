# Plan: Strategy Catalogue Handoff — S6–S11 Market-Reading Perspectives

**Date:** 2026-03-07
**Session:** Continuation of 2026-03-07-strategy-catalogue-visual-plan.md
**Mode:** Research + scoping. No code until user says "build it."

---

## Context

Previous session (floating-hugging-kite.md) completed S1–S5 perspectives and wrote
`visualize_strategy_perspectives.py`. This session adds S6–S11 from the 6 remaining
source files — to complete the full strategy inventory for Vince ML pipeline design.

The goal is NOT entry/exit mechanics. It is: what does each strategy read, what state
must the market be in, and what does "aligned" mean?

---

## Source Files Read This Session

| Strategy | Source File |
|----------|-------------|
| S6 – Ripster EMA Cloud System | `02-STRATEGY\Indicators\Ripster-EMA-Clouds-Strategy.md` |
| S7 – Quad Rotation Stochastic | `02-STRATEGY\Indicators\Quad-Rotation-Stochastic.md` |
| S8 – Core Three Pillars Framework | `02-STRATEGY\Core-Trading-Strategy.md` |
| S9 – BBWP Volatility Filter | `02-STRATEGY\Indicators\BBWP-v2-BUILD-SPEC.md` |
| S10 – ATR SL Movement (3-phase) | `02-STRATEGY\Indicators\ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` |
| S11 – AVWAP Confirmation | `02-STRATEGY\Indicators\AVWAP-Anchor-Assistant-BUILD.md` |

---

## Market-Reading Perspectives (S6–S11)

### S6 — Ripster EMA Cloud System (Tenet/Cloud Manifesto)

**Indicators sensed:**
- Cloud 3 (34/50 EMA): primary trend direction and SL level
- Cloud 2 (5/12 EMA): entry confirmation and exit trigger
- Cloud 1 (8/9 EMA): optional pullback add ribbon
- Volume: 20%+ of average in first 30 mins = trend day
- ATR vs DTR: volatility context

**Required market state:**
- Price must be clearly above OR below Cloud 3 (34/50) — no ambiguity
- Cloud 2 must cross in trade direction (5 crosses above 12 for long)
- Higher highs / higher lows (long) OR lower lows / lower highs (short) forming

**What "aligned" means:**
- Price above Cloud 3 AND Cloud 2 just crossed bullish = LONG setup
- Price below Cloud 3 AND Cloud 2 just crossed bearish = SHORT setup
- 10-min candles riding the 5/12 cloud = trend active
- Cloud 3 = the SL anchor (stop below/above it)

**Exit read:**
- 10-min candle closes AGAINST 5/12 cloud = exit immediately
- Price crosses Cloud 3 = trend flip, reverse bias

**Visualizer plan (S6):**
- Price panel: Cloud 3 fill + Cloud 2 lines + entry arrows
- Cloud 2 panel: 5/12 delta showing cross + riding
- Volume panel: relative volume bar showing 20% threshold
- Annotate: "ABOVE CLOUD 3 = LONG ONLY zone"

---

### S7 — Quad Rotation Stochastic (4-Stoch Alignment)

**Indicators sensed:**
- Stoch 9,3 (Fast): entry timing + divergence detection ONLY this one
- Stoch 14,3 (Standard/TDI): primary confirmation
- Stoch 40,4 (Medium): trend context
- Stoch 60,10 (Slow/Macro): macro filter
- Divergence: price lower low + stoch higher low (from <20 zone) — bullish
- Divergence: price higher high + stoch lower high (from >80 zone) — bearish

**Required market state:**
- Alignment 4/4 (all above or below 50) = strongest setup
- Alignment 3/4 = strong
- 2/4 + macro climbing/descending = continuation setup
- Divergence on fast stoch from extreme zone (<20 or >80) = signal qualifier

**What "aligned" means:**
- All 4 stochs on same side of 50 = full consensus
- Macro (60-10) trend direction confirmed by 3-bar climbing/descending check
- Divergence adds probability weight but is NOT required for all setups

**Visualizer plan (S7):**
- All 4 stochs in one panel, colour-coded by speed
- Alignment count overlay (0/4 to 4/4 shown as background shade)
- Divergence markers on fast stoch
- Annotate: "4/4 ALIGNED = full consensus | DIVERGENCE from extreme = signal"

---

### S8 — Core Three Pillars Framework (Manual/Conceptual)

**Indicators sensed:**
- Pillar 1 (Price/Structure): Ripster 34/50 cloud + Anchored VWAP from swing low/high
- Pillar 2 (Volume): AVWAP placement confirms volume in trade direction
- Pillar 3 (Momentum): Stoch 55 cross + MUST CONTINUE building post-cross
- BBWP: volatility filter (squeeze = coiled, BBWP < 10%)
- ATR: rising = expanding volatility (good), flat/maxed = bad
- TDI CW_Trades: momentum confirmation

**Required market state:**
- BBWP in squeeze (<10%) OR transitioning from squeeze
- Stoch 9 in extreme zone (oversold for long, overbought for short)
- Stoch 55 approaching cross
- Price on correct side of 34/50 cloud

**What "aligned" means:**
- Price above 34/50 cloud + AVWAP from swing low = Buyers in control (Pillar 1+2)
- Stoch 55 crosses AND keeps building = Momentum confirmed (Pillar 3)
- If momentum DECLINES after cross = exit with small profit immediately

**Critical rule (the defining read):**
- "Stoch 55 declines after cross = exit" — this is the system's primary risk control
- The read is: is Pillar 3 building or dying?

**Visualizer plan (S8):**
- Price panel: Cloud 3 fill + AVWAP line
- BBWP panel: squeeze state (blue vs red)
- Stoch 55 panel: showing cross + momentum continuation vs decline
- Two scenarios annotated: "CONTINUES = hold" and "DECLINES = exit small win"

---

### S9 — BBWP Volatility Filter (Pure Volatility State)

**Indicators sensed:**
- Bollinger Band Width as percentile vs 100-bar history
- BB basis: 13-period SMA (scalping-optimized)
- BBWP MA: 5-period SMA of BBWP itself

**Required market state (6 states):**
- BLUE DOUBLE (bbwp ≤ 10 AND spectrum < 25): extreme squeeze, max coil
- BLUE (spectrum < 25): low volatility, preparing for move
- MA CROSS UP (bbwp crosses above MA): volatility expanding
- MA CROSS DOWN (bbwp crosses below MA): volatility contracting
- RED (spectrum > 75): high volatility, trend expanding
- RED DOUBLE (bbwp ≥ 90 AND spectrum > 75): extreme expansion, possible exhaustion

**What "aligned" means:**
- BBWP is a FILTER only — it tells you WHEN to act, not WHICH direction
- BLUE DOUBLE / BLUE = entry window open (coiled, move imminent)
- MA CROSS UP = breakout beginning, add conviction
- RED / RED DOUBLE = trend still valid but watch for exhaustion

**Points system (for Four Pillars grade):**
- BLUE DOUBLE = +2 pts, BLUE = +1, MA CROSS UP = +1, RED = +1, RED DOUBLE = +1

**Visualizer plan (S9):**
- BBWP line with spectrum coloring (blue → green → yellow → red)
- MA line (white)
- Background shading at extremes
- State label annotations: BLUE DOUBLE, MA CROSS UP, etc.
- Annotate: "FILTER ONLY — state gates entry, does not set direction"

---

### S10 — ATR SL Movement (3-Phase Cloud Progression)

**Indicators sensed:**
- Cloud 2 (5/12 EMA): Phase 1 trigger + exit signal
- Cloud 3 (34/50 EMA): Phase 2 trigger
- Cloud 4 (72/89 EMA): Phase 3 trigger (sync with Cloud 3 = continuous trail)
- ATR(14): sizing for each phase adjustment
- Stoch 9,3 (Fast): ADD signal trigger (pullback within trend)
- Stoch 40,3 and 60,10: ADD gate (must stay on trend side of midline)

**Required market state:**
- Phase 1: Cloud 2 crosses in trade direction AFTER entry
- Phase 2: Cloud 3 crosses in trade direction AFTER entry (fresh cross)
- Phase 3: Cloud 3 AND Cloud 4 BOTH aligned and synced
- ADD: Fast stoch enters extreme zone then exits, while medium/macro hold trend side

**What "aligned" means for each phase:**
- Phase 1 (Cloud 2 cross): momentum confirmed through fast cloud — SL tightens, TP expands
- Phase 2 (Cloud 3 cross): medium trend confirmed — both SL and TP extend with trade
- Phase 3 (Cloud 3+4 sync): full trend — TP removed, continuous ATR trail active
- EXIT: Cloud 2 flips AGAINST trade = hard close at any phase

**Visualizer plan (S10):**
- Price panel: phases marked with vertical lines at each cloud cross
- SL line changing style: Red solid (P0) → dotted (P1) → dashed (P2) → yellow trail (P3)
- TP line: solid (P0) → dotted (P1) → dashed (P2) → removed (P3)
- Cloud 2 panel showing cross events
- Annotate: "Each cloud cross advances the phase — SL only moves in trade's favor"

---

### S11 — AVWAP Confirmation (Brian Shannon / Wyckoff VSA)

**Indicators sensed:**
- AVWAP from swing HIGH (where are sellers defending?)
- AVWAP from swing LOW (where are buyers defending?)
- AVWAP from highest VOLUME EVENT (where did institutions commit?)
- VSA patterns: Stopping Volume, Selling Climax, Spring, Upthrust, No Supply, No Demand
- Anchor quality score (0–100): VSA weight 40% + volume 25% + recency 20% + trend alignment 15%
- Structure trend: HH/HL = bullish, LH/LL = bearish
- Volume flow: bull/bear flow via SMA of volume ratio

**Required market state:**
- At least one HIGH QUALITY anchor (score ≥ 70) from recent event (<50 bars)
- Price position relative to all three AVWAPs (above/below each)
- Volume flow direction must match structure trend direction
- "BUYERS" or "SELLERS" state: price above AVWAP from low + below AVWAP from high

**What "aligned" means:**
- Price ABOVE AVWAP from swing low = buyers defending their level
- Price BELOW AVWAP from swing high = sellers still in control at resistance
- VSA event at anchor = institutional commitment at that price
- Highest quality anchor = best SL anchor for the trade

**Visualizer plan (S11):**
- Price panel: three AVWAP lines (from high, low, volume event) + quality scores as text
- VSA event markers (stopping volume, spring, upthrust)
- Volume panel: volume bars + VSA ratio threshold
- Anchor quality panel: scoring bars showing HIGH/MEDIUM/LOW zones
- Annotate: "3 simultaneous AVWAPs — complementary views, not competing signals"

---

## What Will Be Built (when user says "build it")

**Option A — Extend existing script (recommended):**
Add `build_s6()` through `build_s11()` functions to:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives.py`

BUT this file already has 607 lines. Adding 6 more functions (~80-100 lines each) would push
it to ~1200 lines. Still valid Python, but borderline manageable.

**Option B — New versioned file (safer per NEVER OVERWRITE rule):**
Write a NEW file:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives_v2.py`

This file contains ALL 11 strategies (S1–S5 ported from v1 + S6–S11 new). Cleaner, keeps v1
intact as reference, and avoids the "never overwrite" issue.

**Recommendation: Option B (v2 file).** Reasons:
- Keeps v1 untouched (5 strategies already verified by user)
- No risk of breaking existing functions
- Cleaner to review as one complete document
- v2 becomes the canonical full-catalogue visualizer

**Output files (v2):**
```
results/strategy_perspectives/
  S1_bible.png              (re-rendered, identical to v1)
  S2_rebate_farming.png     (re-rendered)
  S3_v38_directional.png    (re-rendered)
  S4_v384_current.png       (re-rendered)
  S5_5589_scalp.png         (re-rendered)
  S6_ripster_clouds.png     (NEW)
  S7_quad_rotation.png      (NEW)
  S8_three_pillars.png      (NEW)
  S9_bbwp_filter.png        (NEW)
  S10_atr_sl_phases.png     (NEW)
  S11_avwap_confirmation.png (NEW)
```

---

## Build Rules (when triggered)

1. Python skill mandatory: `/python` before any `.py` file
2. py_compile must pass on the output file
3. NEVER overwrite v1 — v2 is a new file
4. Write tool directly (NOT build script) — avoids `\n` in triple-quoted string trap
5. Full Windows paths in all output/run commands
6. Session log: append to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md`

---

## Critical Files

| File | Role |
|------|------|
| `PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives.py` | v1 (DO NOT TOUCH) |
| `PROJECTS\four-pillars-backtester\scripts\visualize_strategy_perspectives_v2.py` | v2 target (to create) |
| `02-STRATEGY\Indicators\Ripster-EMA-Clouds-Strategy.md` | S6 source |
| `02-STRATEGY\Indicators\Quad-Rotation-Stochastic.md` | S7 source |
| `02-STRATEGY\Core-Trading-Strategy.md` | S8 source |
| `02-STRATEGY\Indicators\BBWP-v2-BUILD-SPEC.md` | S9 source |
| `02-STRATEGY\Indicators\ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` | S10 source |
| `02-STRATEGY\Indicators\AVWAP-Anchor-Assistant-BUILD.md` | S11 source |

---

## Verification (when built)

1. `python -c "import py_compile; py_compile.compile('scripts/visualize_strategy_perspectives_v2.py', doraise=True)"` — must pass
2. `python scripts/visualize_strategy_perspectives_v2.py` — must produce 11 PNGs in `results/strategy_perspectives/`
3. User visually checks each PNG: do the indicator panels match the described market-reading logic?
4. S6–S11 panels reviewed against source file perspectives written above
