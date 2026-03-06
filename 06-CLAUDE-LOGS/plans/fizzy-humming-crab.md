# Position Management Study Document
**Date:** 2026-03-04
**Status:** RESEARCH — rules documented from live chart examples, open questions flagged
**Trade Type:** Trend-hold trades (trades with a reason to hold longer)

---

## Source Material

Two live trade walkthroughs on TradingView Replay:
1. **PUMPUSDT LONG** — Wed 04 Mar '26, 5m chart, Bybit Spot
2. **PIPPINUSDT SHORT** — Tue 03 Mar '26, 5m chart, Bybit Perpetual

Both are the same trade TYPE: trend-hold trades where HTF determines direction and stoch 60 gate opens.

**Other trade types exist but are NOT covered here:**
- Quick rotations (stoch 60 gate never opens)
- 1-minute EMA cross scalps (55/89 EMA cross, all 4 stochs align)
- Counter-trend trades (prerequisite: 5m or 15m trending in trade direction + BBW spectrum blue or red)

---

## Indicators Used

| Indicator | Settings | Role |
|-----------|----------|------|
| Stoch 9 | 9, 1, 3 (Raw K) | Entry trigger — fires first |
| Stoch 14 | 14, 1, 3 (Raw K) | Entry confirmation — follows 9 |
| Stoch 40 | 40, 1, 4 (Raw K) | Divergence / trend filter |
| Stoch 60 | 60, 1, 10 (Raw K) | Gate — determines trade type |
| TDI (CW_Trades) | RSI=9, Smooth=5, Signal=10, BB=34 | Entry condition + 2-candle exit rule |
| BBWP | SMA 7 100 Spectrum | Entry confirmation + health monitor + trail tightening |
| ATR | 14 RMA | SL sizing (2x), volatility confirmation |
| Ripster EMA Clouds | 8/9, 5/12, 34/50, 72/89, 180/200 | Milestones, targets, cloud waypoints |
| Ripster MTF Clouds | 50/55 + 20/21, res=15m, src=hl2 | Layer 2: execution filter (HTF on 5m chart) |
| AVWAP | From structure / from trade start | Trailing SL mechanism |

---

## Phase 1: HTF Direction — Three-Layer System

**Purpose:** Determine LONG or SHORT bias. Non-negotiable — 5m does NOT decide direction.

### Layer 1: Session Bias (4h / 1h — start of day)
At the start of the trading day, 4h and 1h charts establish the SESSION DIRECTION. "Today is a long day" or "Today is a short day." Set once, applies to the entire session. Every trade must align with this perspective.

### Layer 2: Execution Filter (15m MTF Clouds on 5m)
Ripster MTF Clouds indicator (EMA 1: 50/55, EMA 2: 20/21, resolution=15m, source=hl2) overlaid on the 5m execution chart. Confirms the session bias is still active at the moment a trade is being considered. Pine Script source available — Python conversion agent-delegatable.

### Layer 3: Entry Timing (5m)
Stochastic alignment, BBW, TDI — all within the direction set by Layers 1 and 2.

**All three layers must agree.** If 4h/1h says bearish → only shorts. If 15m MTF clouds flip against session bias → no new entries until realigned.

**PUMP example:** 15m ascending support trendline from lows = LONG bias. Taken despite extremely bearish 5m conditions.

**PIPPIN example:** 4h rally exhausted. 1h Ripster Cloud 3 touching price as resistance in downtrend = SHORT bias.

**Confirmed:**
- Session bias set at start of day from 4h/1h analysis
- 15m MTF clouds confirm bias is still valid for each trade
- 5m is execution timing only — never decides direction
- You never trade against the perspective

**RESOLVED [HTF-1]:** Session bias determined by Ripster EMA cloud transitions on 4h and 1h:
- **4h:** Look for cloud stack flipping direction. Bearish = clouds above price, red/brown fills. Bullish = clouds below price, green/teal fills. A perspective reversal = price crossing through the cloud stack and clouds compressing/flipping.
- **1h:** Confirms the 4h read with more granularity. Clouds flip sequentially: Cloud 2 (5/12) first, then Cloud 3 (34/50), then Cloud 4 (72/89). When they converge at a compression point and price breaks through, the perspective is confirmed.
- **Structural confluence:** Key horizontal levels (AVWAP, S/R) align with the cloud compression zone.
- **PUMP example:** 4h clouds flipped around March 1st. 1h showed sequential cloud flips converging at ~0.001949, price broke above the full stack on March 4th = LONG perspective confirmed.

**RESOLVED [HTF-2]:** 15m MTF clouds are NOT a hard binary filter. A trade CAN fire with price below the MTF clouds, but:
- Price BELOW MTF clouds = cautious, quick to close (reduced hold time)
- Price PASSES ABOVE MTF clouds (for long) = reason to stay in longer (trend-hold)
This directly modulates trade type: below MTF = more like a quick rotation. Above MTF = trend-hold with trailing.

---

## Phase 2: Entry Detection (5m)

### Stochastic Alignment

**Confirmed rule:** All 4 stochastics must have K cross above D (LONG) or K cross below D (SHORT).

**Sequence observed (PIPPIN long bounce example, 04:30 → 04:55):**
- At 04:30: All 4 stochs rising from oversold, but ALL had K below D still
  - Stoch 9: K=49.33, D=53.53 (K < D)
  - Stoch 14: K=49.33, D=53.53 (K < D)
  - Stoch 40: K=33.73, D=41.44 (K < D)
  - Stoch 60: K=33.73, D=40.98 (K < D)
- By 04:55: All 4 had K above D — crossovers completed
  - Stoch 9: K=49.32, D=37.95 (K > D)
  - Stoch 14: K=59.35, D=41.29 (K > D)
  - Stoch 40: K=40.58, D=29.85 (K > D)
  - Stoch 60: K=40.58, D=38.15 (K > D)

**Key nuance:** Stoch 9 is the alert — it moves first. But you do NOT enter until the other stochastics follow with their own K/D crossovers.

**RESOLVED [ENTRY-1]:** Sequential confirmation. Stoch 9 crosses K/D first (alert). Then wait for 14, 40, 60 to follow with their own K/D crosses. Enter when the LAST stochastic completes its K/D cross. This is NOT a snapshot check — it's a sequential process where each stoch must individually cross over.

**RESOLVED [ENTRY-2]:** Stochastics must have come FROM the zone. Specifically: K must have been below 20 (for long) or above 80 (for short) within the last N bars when the K/D cross fires. **N = 10 bars (50 minutes) as starting value. Flag for Vince to optimize via backtesting.** This handles the "stoch 60 speed problem" where K crashes through the zone fast and the K/D cross happens mid-range — the recent-zone check ensures the energy came from the zone even if the cross is slightly above/below it.

### BBW Spectrum vs MA — Entry Confirmation

**Confirmed rule:** BBW spectrum line must cross from below the MA to above the MA. This signals "the perspective" — the volatility regime is confirming the directional move.

**Observed (PIPPIN at 04:30):** BBWP at 63%/55.8%, spectrum just crossed above MA. This coincided with the stochastic alignment window.

**Without this cross, the stochastic movement could be noise.** The BBW spectrum above MA validates that the move is real.

### TDI vs Moving Average — Entry Condition

**Confirmed:** The TDI price line must be on the correct side of its moving average at entry.
- LONG: TDI above MA
- SHORT: TDI below MA

This is both an entry condition AND an ongoing exit rule (see Phase 4).

### SL Placement

**Confirmed baseline:** SL = 2 x ATR(14) from entry price.

**Critical nuance (from PIPPIN):** The 2 ATR calculation must land near a structural level. PIPPIN example: 0.00357 * 2 = 0.00714. Entry ~0.5676 + 0.00714 = 0.57475, near the 0.57687 AVWAP/resistance level. The alignment gave confidence to take the trade.

**The ATR provides the math. Structure provides the validation.**

**OPEN QUESTION [SL-1]:** If 2 ATR doesn't align with any structural level, what happens? Adjust SL to the structure? Skip the trade? Use a different multiplier?

**OPEN QUESTION [SL-2]:** What counts as "structure" for validation? AVWAP levels, recent swing high/low, Ripster cloud levels, horizontal S/R — all of them?

---

## Phase 3: Gate Check — Stoch 60 K vs D

**This is THE pivotal condition.** It determines what kind of trade you're in.

**For LONG:** Stoch 60 K crosses above D → gate opens → trend trade
**For SHORT:** Stoch 60 K crosses below D with distance → gate opens → trend trade

**If gate opens:**
- Remove fixed TP (or set at Ripster Cloud 4 frozen value / % target)
- Begin trailing
- Add-ons become possible

**If gate never opens:**
- Quick rotation trade (separate type, NOT documented here)
- TP on stoch 9 reaching opposite zone

**PUMP example:** Gate opened at ~08:35 when stoch 60 K crossed above D.
**PIPPIN example:** Stoch 60 K was already below D at entry with growing distance, confirming bearish trend.

**OPEN QUESTION [GATE-1]:** What is "distance" numerically? Is there a minimum K-D spread (e.g., K-D > 10 points) that confirms the gate?

---

## Phase 4: Trend Hold Management (Gate Open)

### TDI 2-Candle Rule (HARD EXIT)

**Confirmed rule:** If the TDI price line stays on the WRONG side of its moving average for 2 consecutive candles → EXIT.

- Wrong side for LONG = TDI below MA for 2 candles
- Wrong side for SHORT = TDI above MA for 2 candles

This is a hard, binary rule. Not discretionary.

**Observed (PIPPIN screenshot at ~06:35):** "As soon as 2 candles the TDI is staying on the wrong side of the moving average I am out."

### BBW Health Monitor (Trail + Exit)

**Confirmed states and actions:**

| BBW State | Condition | Action |
|-----------|-----------|--------|
| Healthy | Spectrum ABOVE MA | Hold, wider trail (e.g., AVWAP +2sigma) |
| Extreme | BBW turns RED | Tighten trail (e.g., +2sigma → +1sigma) |
| Exit | Spectrum BELOW MA or turns dark blue | EXIT trade |

**PUMP example:** BBW spectrum staying above MA = hold. BBW crossing MA at 10:00 = move SL to BE.
**PIPPIN example:** BBW turning red (stochs at floor, max volatility) = tighten from AVWAP +2sigma to +1sigma (green line).

**OPEN QUESTION [BBW-1]:** What BBWP percentile thresholds define "red" vs "blue" vs "dark blue"? Need numeric boundaries for programming.

### Breakeven Trigger

**Two methods observed:**
1. **PUMP:** BBW crossing its MA + price still trending + profit accumulated (~0.62%)
2. **PIPPIN:** Stoch 60 K/D distance confirming trend after a pullback

Both are "the trend is confirmed" signals.

**OPEN QUESTION [BE-1]:** Are these interchangeable? Does the situation determine which to use? Or is one preferred?

### Trail Mechanism

**Confirmed:** AVWAP is the trailing SL anchor. Two variants observed:
1. **AVWAP from trade start** (PUMP long) — plain AVWAP anchored at entry bar
2. **AVWAP +2sigma** (PIPPIN short) — upper band of AVWAP, tightened to +1sigma on BBW red

**OPEN QUESTION [TRAIL-1]:** What determines which AVWAP variant to use? Is it: use +sigma for shorts (SL above price) and plain for longs (SL below price)? Or is it setup-dependent?

### Ripster Cloud Milestones

**Confirmed:** Cloud crossings are waypoints, NOT SL triggers. They tell you how far the trade has progressed.

**PUMP specific:**
- Cloud 2 crossed → on track
- Cloud 3 crossed → strong
- Cloud 4 value at time of confirmation = FROZEN TP target (does not move with the cloud)
- All clouds crossed → raise SL, full trend mode

**OPEN QUESTION [CLOUD-1]:** Is the frozen Cloud 4 target specific to longs? For shorts, is the target a cloud level below, or always a % target?

### TP Framework

**Two methods observed:**
1. **PUMP:** Frozen Ripster Cloud 4 value at the time of confirmation
2. **PIPPIN:** 2% minimum = 0.55

**OPEN QUESTION [TP-1]:** When is Ripster cloud target used vs % target? Does it depend on whether clouds are nearby (use them) vs far away (use %)?

---

## Phase 5: Add-Ons

**Confirmed rule:** Stoch 9 or 14 must reach the OPPOSITE zone:
- For long add-on: stoch 9/14 must pull back to oversold (below 20)
- For short add-on: stoch 9/14 must bounce to overbought (above 80)

**While:** Stoch 40 and 60 maintain trend direction (K above/below D).

**Critical:** If the fast stoch doesn't reach the opposite zone, NO add-on. A half-hearted bounce to midrange does NOT qualify. The market decides.

**PUMP:** Two add-on opportunities visible (white lines in regression channel). Stoch 9 pulled back while 40/60 held bullish K > D.
**PIPPIN:** No add-ons. Stoch 9 only bounced to ~34 — never reached 80. Market didn't give it.

---

## Phase 6: Exit

**Confirmed exit triggers:**
1. TDI wrong side of MA for 2 candles (HARD — any phase)
2. BBW spectrum below MA or turns dark blue
3. Trailing SL hit (AVWAP-based)
4. Partial exit at Ripster Cloud 4 frozen value or % target
5. Larger timeframe breakdown

**Partial exit observed (PUMP):** Close half at ~2.32%, keep rest trailing on AVWAP from trade start.

---

## ATR Role — Clarification

**ATR does NOT drive trade decisions.** It serves two purposes only:
1. SL sizing: 2 x ATR as baseline (validated against structure)
2. Volatility confirmation: ATR rising = candle size increased (the breakout is real). ATR flat = questionable.

This directly contradicts ATR-SL-MOVEMENT-BUILD-GUIDANCE.md which makes ATR central to phase transitions. In actual trading, ATR is a thermometer, not a thermostat.

---

## State Machine Summary

```
FLAT → [HTF direction set] → MONITORING
MONITORING → [All 4 stochs K/D cross + BBW spectrum > MA + TDI correct side] → IN TRADE
IN TRADE → [TDI wrong side 2 bars] → EXIT
IN TRADE → [Stoch 60 gate opens] → TREND HOLD
IN TRADE → [Stoch 60 gate never opens] → QUICK EXIT (separate type, not here)
TREND HOLD → [TDI wrong side 2 bars] → EXIT
TREND HOLD → [BBW spectrum < MA / dark blue] → EXIT
TREND HOLD → [Trail SL hit] → EXIT
TREND HOLD → [BBW red] → TIGHTEN TRAIL
TREND HOLD → [BBW confirms + profit] → MOVE TO BE
TREND HOLD → [Stoch 9/14 reaches opposite zone, 40/60 hold] → ADD-ON
TREND HOLD → [Ripster cloud target / % target] → PARTIAL EXIT
```

---

## Differences From ALL Existing Specs

| Aspect | ATR-SL-MOVEMENT Spec | AVWAP 3-Stage (v3.8.2) | v386 Current | User's Actual Trading |
|--------|---------------------|------------------------|-------------|----------------------|
| Entry | Stoch 9 zone cross | Stoch 9 zone cross | Stoch 9 < 25 / > 75 | All 4 stochs K/D cross + BBW + TDI |
| SL | 2x ATR (fixed) | AVWAP +/- 2sigma | 2.0x ATR | ~2 ATR validated against structure |
| Phase triggers | Cloud 2/3 crosses | Time/price stages | N/A (static) | Stoch 60 K vs D |
| TP | 4x ATR (fixed) | Dynamic AVWAP | Trailing 2% callback | Conditional: Ripster 4 frozen / % |
| Trail | Cloud 3+4 sync | Cloud 3 +/- ATR | BingX 2% native | AVWAP from trade start / +sigma |
| Hard close | Cloud 2 flip | N/A | N/A | TDI 2-candle rule + BBW spectrum |
| Health monitor | N/A | N/A | N/A | BBW spectrum vs MA + TDI MA slope |
| Add-ons | Stoch 9 pullback | AVWAP limit at 1sigma | N/A | Stoch 9/14 to opposite zone + 40/60 hold |
| ATR role | Central to phases | SL/TP sizing | SL/trail sizing | Thermometer only (SL sizing + confirmation) |

**This is not a patch on v386. It is a different strategy architecture.**

---

## Open Questions Index

### RESOLVED
| ID | Resolution | Detail |
|----|-----------|--------|
| ENTRY-2 | Recent zone check | K must have been below 20 (long) or above 80 (short) within last N=10 bars. N flagged for Vince optimization. |
| HTF-2 | MTF = hold duration modulator | Price below MTF clouds = cautious, quick close. Price passes MTF = stay in longer. Not a hard binary filter. |
| ENTRY-1 | Sequential confirmation | Stoch 9 crosses first (alert), wait for 14/40/60 to follow. Enter on last cross. |
| BBW-1 | Flagged for Vince research | Exact thresholds unknown. Use the 5-layer BBW module to find the relationship via backtesting. |
| TDI-1 | Settings confirmed | RSI period=9, RSI price smoothing=5, Signal line=10, Bollinger band period=34. |
| HTF-1 | Cloud stack transitions | 4h: cloud stack flipping direction. 1h: sequential cloud flips (Cloud 2 first, then 3, then 4) converging at structural level. |

### OPEN (6 remaining)
| ID | Question | Impact |
|----|----------|--------|
| SL-1 | What if 2 ATR doesn't align with structure? | Trade selection |
| SL-2 | What counts as "structure" for SL validation? | SL placement |
| GATE-1 | Numeric threshold for stoch 60 K/D "distance"? | Gate definition |
| BE-1 | Are the two BE methods interchangeable? | BE trigger |
| TRAIL-1 | What determines AVWAP variant (plain vs +sigma)? | Trail selection |
| CLOUD-1 | Is frozen Cloud 4 target longs-only? | TP framework |
| TP-1 | When cloud target vs % target? | TP framework |

---

## What This Document Is NOT

- This is NOT a build plan
- This is NOT comprehensive — it covers ONE trade type (trend-hold)
- The open questions MUST be answered before any build
- Quick rotations, 1min scalps, counter-trend trades are separate discussions
- No code should be written until the user explicitly approves the rules
