# Four Pillars Combined - Build Specification

> **⚠️ DEPRECATED - See FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md**
>
> This spec contains errors:
> - "Stoch 55" does not exist in built indicators
> - TDI not built
> - Conflicts with John Kurisko HPS methodology
>
> **Use v2.0 instead:** [[FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC]]

**Version:** 1.0 (DEPRECATED)
**Date:** 2026-02-04
**Purpose:** Single dashboard that grades trade setups and manages position

---

## PHILOSOPHY

The market does predictable things. When conditions align, action is taken. No guessing, no hoping.

**Core Principle:** Confluence of 4 pillars determines trade validity. Each pillar contributes points. More points = higher grade = larger target.

**What This Indicator Does:**
- Combines signals from all built indicators
- Grades setups (A / B / C / No Trade)
- Shows direction (LONG / SHORT / FLAT)
- Manages position (breakeven, trailing stop)
- Outputs dashboard with all conditions visible

**What This Indicator Does NOT Do:**
- Auto-execute trades (that's n8n's job)
- Replace judgment (it's a tool, not a system)

---

## THE FOUR PILLARS

| Pillar | Indicator | What It Measures | Role |
|--------|-----------|------------------|------|
| 1. Price Structure | Ripster EMA Clouds | Trend direction via EMA alignment | Bias filter |
| 2. Directional Bias | AVWAP Anchor Assistant | Price vs volume-weighted levels | Confirmation |
| 3. Momentum | Quad Rotation Stochastic | Stoch 55 K/D cross + zone | Entry trigger |
| 4. Volatility | BBWP v2 | Band width state | Filter + grade boost |

---

## PILLAR 1: PRICE STRUCTURE (Ripster EMA Clouds)

**Source:** `ripster_ema_clouds_v6.pine`

**Conditions Checked:**

| Condition | LONG | SHORT |
|-----------|------|-------|
| Price vs 34/50 Cloud | Above green cloud | Below red cloud |
| Cloud Direction | Rising | Falling |
| 5/12 Cloud | Price crossed above | Price crossed below |

**Points:**
- Price correct side of 34/50 cloud: +1
- Cloud rising/falling in trade direction: +1
- 5/12 crossover confirmed: +1

**Max Points:** 3

**Integration Variables Needed:**
```
- price_above_cloud_34_50 (bool)
- price_below_cloud_34_50 (bool)
- cloud_rising (bool)
- cloud_falling (bool)
- cross_above_5_12 (bool)
- cross_below_5_12 (bool)
```

---

## PILLAR 2: DIRECTIONAL BIAS (AVWAP Anchor Assistant)

**Source:** `avwap_anchor_assistant_v1.pine`

**Conditions Checked:**

| Condition | LONG | SHORT |
|-----------|------|-------|
| Price vs Structure VWAP | Above VWAP from low | Below VWAP from high |
| Volume Flow | Bull flow | Bear flow |
| Anchor Quality | HIGH or MEDIUM | HIGH or MEDIUM |

**Points:**
- Price correct side of VWAP: +1
- Volume flow aligned: +1
- Anchor quality HIGH: +1 (MEDIUM: +0.5)

**Max Points:** 3

**Integration Variables Needed:**
```
- price_above_vwap (bool)
- price_below_vwap (bool)
- vol_flow_bullish (bool)
- vol_flow_bearish (bool)
- anchor_quality (string: HIGH/MEDIUM/LOW)
- anchor_quality_score (int: 0-100)
```

---

## PILLAR 3: MOMENTUM (Quad Rotation Stochastic)

**Source:** `Quad-Rotation-Stochastic-v4-CORRECTED.pine`

**This is the ENTRY TRIGGER pillar.**

**Stoch 55 is the key.** Other stochastics confirm.

**Entry Conditions:**

| Condition | LONG | SHORT |
|-----------|------|-------|
| Stoch 55 Zone | Was in oversold (<20), now exiting | Was in overbought (>80), now exiting |
| Stoch 55 K/D Cross | K crosses above D | K crosses below D |
| Stoch 9 Continuation | Rising (not diverging) | Falling (not diverging) |
| TDI Alignment | RSI > Signal, bullish | RSI < Signal, bearish |

**Points:**
- Stoch 55 in correct zone: +1
- Stoch 55 K/D cross: +2 (THIS IS THE TRIGGER)
- Stoch 9 continuation: +1
- TDI aligned: +1
- Divergence present: +1 (bonus)

**Max Points:** 6

**Critical Rule:** No Stoch 55 K/D cross = No trade, regardless of other pillars.

**Integration Variables Needed:**
```
- stoch_55_k (float)
- stoch_55_d (float)
- stoch_55_cross_up (bool)
- stoch_55_cross_down (bool)
- stoch_55_in_oversold (bool)
- stoch_55_in_overbought (bool)
- stoch_55_exiting_oversold (bool)
- stoch_55_exiting_overbought (bool)
- stoch_9_rising (bool)
- stoch_9_falling (bool)
- tdi_bullish (bool)
- tdi_bearish (bool)
- divergence_bull (bool)
- divergence_bear (bool)
```

---

## PILLAR 4: VOLATILITY (BBWP v2)

**Source:** `bbwp_v2.pine`

**This is a FILTER + GRADE BOOST pillar.**

**Conditions Checked:**

| State | Points | Meaning |
|-------|--------|---------|
| BLUE DOUBLE | +2 | Extreme compression, big move ready |
| BLUE | +1 | Low volatility, good for entry |
| MA CROSS UP | +1 | Volatility starting to expand |
| MA CROSS DOWN | 0 | Volatility contracting |
| NORMAL | 0 | Neutral |
| RED | +1 | High volatility, valid if momentum aligns |
| RED DOUBLE | +1 | Extreme expansion, valid if momentum aligns |

**Max Points:** 2

**Integration Variables Needed:**
```
- bbwp_value (float: 0-100)
- bbwp_state (string)
- bbwp_points (int: 0-2)
- is_blue_double (bool)
- is_red_double (bool)
```

---

## GRADE CALCULATION

**Total Possible Points:** 14 (3+3+6+2)

| Grade | Points | Conditions | Target |
|-------|--------|------------|--------|
| A | 10+ | Stoch 55 cross + high confluence | 6 ATR |
| B | 7-9 | Stoch 55 cross + moderate confluence | 4 ATR |
| C | 4-6 | Stoch 55 cross + low confluence | 2-3 ATR |
| No Trade | <4 OR no Stoch 55 cross | Missing trigger or too weak | - |

**Mandatory for ANY trade:**
- Stoch 55 K/D cross MUST happen
- Price MUST be correct side of 34/50 cloud

Without these two = No Trade regardless of points.

---

## ENTRY LOGIC

```
LONG ENTRY CONDITIONS:
1. [MANDATORY] Stoch 55 K crosses above D
2. [MANDATORY] Price above 34/50 green cloud
3. [GRADED] Stoch 55 was in or near oversold (<20)
4. [GRADED] Stoch 9 rising (continuation)
5. [GRADED] TDI bullish
6. [GRADED] Price above VWAP
7. [GRADED] Volume flow bullish
8. [GRADED] Cloud rising
9. [GRADED] BBWP state (any blue = bonus)

SHORT ENTRY CONDITIONS:
1. [MANDATORY] Stoch 55 K crosses below D
2. [MANDATORY] Price below 34/50 red cloud
3. [GRADED] Stoch 55 was in or near overbought (>80)
4. [GRADED] Stoch 9 falling (continuation)
5. [GRADED] TDI bearish
6. [GRADED] Price below VWAP
7. [GRADED] Volume flow bearish
8. [GRADED] Cloud falling
9. [GRADED] BBWP state (any blue = bonus)
```

---

## EXIT LOGIC

**Protective Exits (Exit Immediately):**

| Condition | Action |
|-----------|--------|
| Stoch 55 momentum declines after entry | Exit with small profit |
| Price closes against 5/12 cloud | Exit |
| Price breaks VWAP | Control lost, exit |
| Stop loss hit (2 ATR) | Exit |

**Profit Exits:**

| Condition | Action |
|-----------|--------|
| Target reached (based on grade) | Exit |
| Trailing stop triggered | Exit |
| Stoch 9 reaches opposite extreme | Tighten stop / partial exit |
| BBWP maxes out (RED DOUBLE after being BLUE) | Consider exit |

---

## POSITION MANAGEMENT

**Source:** `atr_position_manager_v1.pine`

### Stop Loss

```
Initial Stop Loss = Entry Price ± (2 × ATR of chart timeframe)

LONG: Stop = Entry - (2 × ATR)
SHORT: Stop = Entry + (2 × ATR)
```

### Move to Breakeven

```
Condition: Stoch 9 reaches opposite zone (>80 for long, <20 for short)
Action: Move stop to entry price (breakeven)
```

### Trailing Stop

```
Activation: Price moves 2 ATR in profit direction
Trail Distance: 2 × ATR (higher timeframe)
Callback: 2 × ATR

LONG Example:
- Entry: 100
- ATR: 2
- Trail activates at: 104 (entry + 2×ATR)
- Trail stop: Current price - (2 × HTF ATR)

Timeframe Mapping:
| Chart TF | Trail ATR TF |
|----------|--------------|
| 1m | 5m |
| 5m | 15m |
| 15m | 1H |
| 1H | 4H |
```

### Target Based on Grade

| Grade | Target |
|-------|--------|
| A | 6 × ATR |
| B | 4 × ATR |
| C | 2-3 × ATR |

---

## DASHBOARD LAYOUT

```
┌─────────────────────────────────────────────────────────────────┐
│ FOUR PILLARS                          GRADE: A    LONG          │
├─────────────────────────────────────────────────────────────────┤
│ PILLAR          │ STATUS      │ PTS │ DETAIL                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. STRUCTURE    │ ✓ BULLISH   │ 3/3 │ Above cloud, rising       │
│ 2. BIAS         │ ✓ ABOVE     │ 2/3 │ VWAP + Bull flow          │
│ 3. MOMENTUM     │ ✓ TRIGGER   │ 5/6 │ 55 cross, 9 cont, TDI     │
│ 4. VOLATILITY   │ ✓ BLUE      │ 2/2 │ BLUE DOUBLE               │
├─────────────────────────────────────────────────────────────────┤
│ TOTAL           │             │12/14│                           │
├─────────────────────────────────────────────────────────────────┤
│ TARGET: 6 ATR   │ STOP: 2 ATR │ R:R │ 3:1                       │
├─────────────────────────────────────────────────────────────────┤
│ POSITION MGMT   │ STATUS                                        │
├─────────────────────────────────────────────────────────────────┤
│ Entry           │ 0.10766                                       │
│ Stop Loss       │ 0.10652 (2 ATR)                               │
│ Breakeven       │ NOT ACTIVE (Stoch 9 at 47)                    │
│ Trailing        │ NOT ACTIVE (need +2 ATR)                      │
│ Target          │ 0.11108 (6 ATR)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Compact Mode (Alternative)

```
┌──────────────────────────┐
│ A LONG   12/14   6 ATR   │
├──────────────────────────┤
│ STRUCT  ✓  BIAS   ✓      │
│ MOMENT  ✓  VOLAT  ✓      │
├──────────────────────────┤
│ SL: 0.10652  TP: 0.11108 │
│ BE: —        TRAIL: —    │
└──────────────────────────┘
```

---

## ALERTS

| Alert | Condition |
|-------|-----------|
| Grade A Long | Grade = A AND Direction = LONG |
| Grade A Short | Grade = A AND Direction = SHORT |
| Grade B Long | Grade = B AND Direction = LONG |
| Grade B Short | Grade = B AND Direction = SHORT |
| Grade C Long | Grade = C AND Direction = LONG |
| Grade C Short | Grade = C AND Direction = SHORT |
| Move to Breakeven | Breakeven condition triggered |
| Trailing Active | Trailing stop activated |
| Exit Signal | Any exit condition triggered |

### Webhook JSON (for n8n)

```json
{
  "indicator": "four_pillars",
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "time": "{{timenow}}",
  "grade": "A",
  "direction": "LONG",
  "points": 12,
  "entry": {{close}},
  "stop_loss": {{close}} - 2 * {{atr}},
  "target": {{close}} + 6 * {{atr}},
  "structure_pts": 3,
  "bias_pts": 2,
  "momentum_pts": 5,
  "volatility_pts": 2,
  "bbwp_state": "BLUE DOUBLE",
  "stoch_55_k": 45.5,
  "stoch_55_d": 42.3
}
```

---

## INPUT STRUCTURE

```
GROUP: ═══ PILLAR 1: STRUCTURE ═══
- Use external Ripster (bool, default: true)
- EMA lengths if internal (5, 12, 34, 50)

GROUP: ═══ PILLAR 2: BIAS ═══
- Use external AVWAP (bool, default: true)
- VWAP source if internal

GROUP: ═══ PILLAR 3: MOMENTUM ═══
- Use external Quad Stoch (bool, default: true)
- Stoch 55 length (default: 55)
- Stoch 9 length (default: 9)
- Oversold level (default: 20)
- Overbought level (default: 80)

GROUP: ═══ PILLAR 4: VOLATILITY ═══
- Use external BBWP (bool, default: true)
- BBWP thresholds if internal

GROUP: ═══ POSITION MANAGEMENT ═══
- ATR Length (default: 14)
- Stop Loss ATR Multiplier (default: 2)
- Trail Activation ATR (default: 2)
- Trail Distance ATR (default: 2)
- HTF for Trail (default: auto based on chart TF)

GROUP: ═══ GRADE THRESHOLDS ═══
- Grade A minimum (default: 10)
- Grade B minimum (default: 7)
- Grade C minimum (default: 4)

GROUP: ═══ TARGETS ═══
- Grade A target ATR (default: 6)
- Grade B target ATR (default: 4)
- Grade C target ATR (default: 2)

GROUP: ═══ DASHBOARD ═══
- Show dashboard (bool)
- Dashboard position
- Compact mode (bool)
- Show position management (bool)

GROUP: ═══ ALERTS ═══
- Enable alerts (bool)
- Webhook format (bool)
```

---

## INTEGRATION METHOD

**Option A: External Indicators (Recommended)**

Use `request.security()` or plot references to pull data from other indicators already on chart.

```pinescript
// Example: Reading from external indicator plots
ext_bbwp = request.security(syminfo.tickerid, timeframe.period, 
           ta.valuewhen(barstate.isconfirmed, bbwp_value, 0))
```

**Option B: Internal Calculation**

Rebuild all calculations inside this indicator. Larger code but self-contained.

**Recommendation:** Start with Option B (self-contained) for reliability. Add Option A later for modularity.

---

## STATE TRACKING

```pinescript
// Position state
var bool inPosition = false
var string positionDirection = "FLAT"  // LONG, SHORT, FLAT
var float entryPrice = na
var float stopLoss = na
var float target = na
var string currentGrade = "—"
var bool breakevenActive = false
var bool trailingActive = false
var float trailingStop = na

// Update on entry signal
if entrySignal and not inPosition
    inPosition := true
    positionDirection := direction
    entryPrice := close
    stopLoss := direction == "LONG" ? close - (2 * atr) : close + (2 * atr)
    target := direction == "LONG" ? close + (targetATR * atr) : close - (targetATR * atr)
    currentGrade := grade

// Update breakeven
if inPosition and breakevenCondition and not breakevenActive
    stopLoss := entryPrice
    breakevenActive := true

// Update trailing
if inPosition and trailingCondition
    trailingActive := true
    trailingStop := direction == "LONG" ? 
                    close - (2 * htfATR) : 
                    close + (2 * htfATR)
    stopLoss := direction == "LONG" ? 
                math.max(stopLoss, trailingStop) : 
                math.min(stopLoss, trailingStop)

// Exit conditions
if inPosition and exitCondition
    inPosition := false
    positionDirection := "FLAT"
    entryPrice := na
    // ... reset all
```

---

## VALIDATION CHECKLIST

```
[ ] All pillar calculations working
[ ] Points calculated correctly
[ ] Grade assigned correctly
[ ] Mandatory conditions enforced (no trade without Stoch 55 cross + cloud)
[ ] Entry signals fire at correct moment
[ ] Stop loss calculated from ATR
[ ] Breakeven triggers when Stoch 9 reaches opposite zone
[ ] Trailing activates at +2 ATR profit
[ ] Trailing updates correctly
[ ] Exit signals fire on all exit conditions
[ ] Dashboard displays all information
[ ] Dashboard colors reflect state
[ ] Alerts fire on grade signals
[ ] Webhook JSON formatted correctly
```

---

## FILE OUTPUT

```
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\four_pillars_combined_v1.pine
```
