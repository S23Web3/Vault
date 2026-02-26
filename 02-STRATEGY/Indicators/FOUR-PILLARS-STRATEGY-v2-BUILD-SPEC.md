# Four Pillars Strategy - Build Specification v2.0

**Version:** 2.0
**Date:** 2026-02-04
**Status:** CORRECTED - Aligned with built indicators
**Purpose:** Combined dashboard with entry/exit logic and position management

---

## CRITICAL CORRECTIONS FROM v1.0

| Issue | v1.0 (WRONG) | v2.0 (CORRECT) |
|-------|--------------|----------------|
| Primary trigger | "Stoch 55 K/D cross" | **40-4 divergence/rotation** |
| Stochastic settings | Stoch 55 (55, 1, 12) | **9-3, 14-3, 40-4, 60-10 (Kurisko HPS)** |
| Trigger priority | Stoch 55 mandatory | **40-4 divergence = SUPERSIGNAL** |
| TDI reference | "TDI CW_Trades" | **REMOVED** (not built) |
| Exit signal | "Stoch 55 momentum" | **9-3 reaches opposite zone** |

**Source of correction:** John Kurisko HPS methodology (PDF reviewed 2026-02-03), built QRS indicators

---

## PHILOSOPHY

The Four Pillars framework combines multiple confirmation layers to grade trade setups. Higher confluence = higher grade = larger target.

**Core Principle:** No guessing. When conditions align, action is taken.

**What This Does:**
- Combines signals from all 4 pillar indicators
- Grades setups (A / B / C / No Trade)
- Shows direction (LONG / SHORT / FLAT)
- Manages position (stop loss, breakeven, trailing)
- Outputs dashboard with all conditions visible

---

## THE FOUR PILLARS

| Pillar | Indicator | What It Measures | Role |
|--------|-----------|------------------|------|
| 1. Structure | Ripster EMA Clouds | Trend via EMA alignment | **Bias filter** |
| 2. Directional Bias | AVWAP Anchor Assistant | Price vs volume-weighted levels | **Confirmation** |
| 3. Momentum | Quad Rotation Stochastic | 40-4 divergence + rotation | **Entry trigger** |
| 4. Volatility | BBWP v2 | Band width state | **Filter + grade boost** |

---

## PILLAR 1: PRICE STRUCTURE (Ripster EMA Clouds)

**Source:** `ripster_ema_clouds_v6.pine`

**Cloud Configuration (Ripster Standard):**
- Cloud 1: 8/9 EMA (Entry timing)
- Cloud 2: 5/12 EMA (Short-term momentum)
- Cloud 3: 34/50 EMA (Medium-term trend) ← **PRIMARY**

**Conditions for LONG:**
| Condition | Check | Points |
|-----------|-------|--------|
| Price above 34/50 cloud | `close > mashort3 AND close > malong3` | +1 |
| 34/50 cloud is green (bullish) | `mashort3 > malong3` | +1 |
| 5/12 cloud is green | `mashort2 > malong2` | +1 |

**Conditions for SHORT:** (Inverse)

**Max Points:** 3

**Integration Variables Needed:**
```
cloud_34_50_bullish (bool)   // mashort3 > malong3
cloud_5_12_bullish (bool)    // mashort2 > malong2
price_above_34_50 (bool)     // close > both 34 and 50 EMAs
price_below_34_50 (bool)     // close < both 34 and 50 EMAs
```

**MANDATORY CONDITION:**
- Price MUST be on correct side of 34/50 cloud for ANY trade
- Above cloud = LONG only | Below cloud = SHORT only | In cloud = NO TRADE

---

## PILLAR 2: DIRECTIONAL BIAS (AVWAP Anchor Assistant)

**Source:** `avwap_anchor_assistant_v1.pine`

**Brian Shannon AVWAP Philosophy:**
- Anchor from structure HIGH = Resistance VWAP (sellers in control below)
- Anchor from structure LOW = Support VWAP (buyers in control above)

**Conditions for LONG:**
| Condition | Check | Points |
|-----------|-------|--------|
| Price above VWAP from Low | `close > vwapFromLow` | +1 |
| Volume flow bullish | `bullVolMA > bearVolMA` | +1 |
| Anchor quality HIGH | `anchor_quality_score >= 70` | +1 |
| Anchor quality MEDIUM | `anchor_quality_score >= 40` | +0.5 |

**Max Points:** 3

**Integration Variables (from hidden plots):**
```
vwap_from_low (float)
vwap_from_high (float)
vol_flow_numeric (int: 1=bull, -1=bear)
anchor_quality (float: 0-100)
bias_numeric (int: -2 to +2)
structure_trend (int: -1, 0, +1)
```

---

## PILLAR 3: MOMENTUM (Quad Rotation Stochastic) ← THE TRIGGER

**Source:** `Quad-Rotation-Stochastic-v4-CORRECTED.pine` or `Quad-Rotation-Stochastic-FAST.pine`

### THE 4 STOCHASTICS (John Kurisko HPS Settings)

| Name | K | Smooth | Type | Role |
|------|---|--------|------|------|
| 9-3 | 9 | 3 | Fast | Entry timing, EXIT signals |
| 14-3 | 14 | 3 | Fast | Confirmation |
| 40-4 | 40 | 3 | Fast | **PRIMARY - Divergence trigger** |
| 60-10 | 60 | 10 | Full (double smooth) | Macro filter / Channel |

### CRITICAL: 40-4 IS THE PRIMARY TRIGGER

**John Kurisko Rule 5:** "Always take a 40-4 divergence or any multiple-band divergences"

**Entry Signals (Priority Order):**

| Signal | Condition | Points |
|--------|-----------|--------|
| **SUPERSIGNAL** | 40-4 Divergence + 3/4 Alignment | +4 (HIGHEST) |
| **DIVERGENCE** | 40-4 Stage-based divergence fires | +3 |
| **FULL ROTATION** | All 4 stochs rotating from zone | +3 |
| **CONFIRMED ROTATION** | 9-3 + 14-3 rotating from zone | +2 |
| **ALIGNMENT FLIP** | Regime changes bull↔bear | +1 |

### 40-4 DIVERGENCE DETECTION (Stage Machine)

**Bullish Divergence:**
1. Stage 1: 40-4 drops below 20, record price low + stoch low
2. Stage 2: 40-4 bounces above 20 (watching for return)
3. Confirmation: Price makes LOWER LOW (or equal) + 40-4 HOLDS above 20 + turning UP
4. Signal fires: BULLISH DIVERGENCE

**Bearish Divergence:** (Inverse at 80 level)

### EXIT SIGNALS (9-3 Based)

| Condition | Action |
|-----------|--------|
| 9-3 crosses above 80 (in long) | Move to breakeven |
| 9-3 crosses below 20 (in short) | Move to breakeven |
| 40-4 momentum declines after entry | Tighten stop |

**Max Points:** 4

**Integration Variables (from hidden plots):**
```
stoch_9_3 (float)
stoch_14_3 (float)
stoch_40_4 (float)
stoch_60_10 (float)
bull_count (int: 0-4)
bear_count (int: 0-4)
bull_state (int: 0, 1, 2)  // divergence state machine
bear_state (int: 0, 1, 2)
div_active (int: -1, 0, 1)
channel_numeric (int: -3 to +3)  // 60-10 state
```

---

## PILLAR 4: VOLATILITY (BBWP v2)

**Source:** `bbwp_v2.pine`

**BBWP is a FILTER, not a signal.**

| State | Points | Meaning |
|-------|--------|---------|
| BLUE DOUBLE | +2 | Extreme compression, breakout imminent |
| BLUE | +1 | Low volatility, good for entry |
| MA CROSS UP | +1 | Volatility starting to expand |
| MA CROSS DOWN | 0 | Volatility contracting |
| NORMAL | 0 | Neutral |
| RED | +1 | High volatility (valid if momentum aligns) |
| RED DOUBLE | +1 | Extreme expansion (valid if momentum aligns) |

**Max Points:** 2

**Integration Variables (from hidden plots):**
```
bbwp_value (float: 0-100)
bbwp_points (int: 0-2)
is_blue_bar (bool)
is_red_bar (bool)
is_blue_spectrum (bool)
is_red_spectrum (bool)
ma_cross_up_state (bool)
ma_cross_down_state (bool)
```

---

## GRADE CALCULATION

**Total Possible Points:** 12 (3+3+4+2)

| Grade | Points | Conditions | Target |
|-------|--------|------------|--------|
| A | 9+ | 40-4 trigger + high confluence | 6 ATR |
| B | 6-8 | 40-4 trigger + moderate confluence | 4 ATR |
| C | 4-5 | Rotation + low confluence | 2-3 ATR |
| No Trade | <4 OR missing mandatory | Too weak | - |

**MANDATORY CONDITIONS (Required for ANY trade):**
1. Price on correct side of 34/50 cloud
2. At least ONE momentum trigger (divergence, rotation, or flip)

Without BOTH = No Trade regardless of points.

---

## ENTRY LOGIC

### LONG ENTRY
```
MANDATORY:
  ✓ Price ABOVE 34/50 cloud
  ✓ At least ONE of:
    - 40-4 Bullish Divergence
    - 40-4 Rotation from oversold
    - Alignment Flip to Bullish

GRADED (adds to score):
  + 34/50 cloud green (rising)
  + 5/12 cloud green
  + Price above VWAP from Low
  + Volume flow bullish
  + Anchor quality HIGH
  + 3/4 or 4/4 stoch alignment
  + BBWP blue state

ENTRY EXECUTION:
  IF mandatory conditions met AND points >= 4:
    - Calculate grade (A/B/C)
    - Set stop loss = Entry - (2 × ATR)
    - Set target = Entry + (grade_ATR × ATR)
    - Fire alert with JSON payload
```

### SHORT ENTRY (Inverse)

---

## EXIT LOGIC

### PROTECTIVE EXITS (Exit or Tighten Immediately)

| Condition | Action |
|-----------|--------|
| 40-4 momentum DECLINES after entry | Tighten stop to 1 ATR |
| Price closes against 5/12 cloud | Exit |
| Price breaks VWAP (loses control) | Exit |
| Stop loss hit | Exit |

### PROFIT MANAGEMENT EXITS

| Condition | Action |
|-----------|--------|
| 9-3 reaches opposite zone (>80 long, <20 short) | Move to breakeven |
| Trail activation reached (+2 ATR profit) | Activate trailing stop |
| Target reached | Exit |
| BBWP maxes out (RED DOUBLE after BLUE entry) | Consider partial exit |

---

## POSITION MANAGEMENT

**Source:** `atr_position_manager_v1.pine`

### Stop Loss
```
Chart TF ATR for initial stop

LONG:  Stop = Entry - (2 × ATR)
SHORT: Stop = Entry + (2 × ATR)
```

### Move to Breakeven
```
Condition: 9-3 reaches opposite zone (>80 for long, <20 for short)
Action: Move stop to entry price

RATIONALE: John Kurisko Rule 1 - "Under 200/VWAP, take trade off on first
           9-3 rotation above 80" - This is about PROTECTING profits.
```

### Trailing Stop
```
Activation: Price moves 2 ATR in profit direction
Trail Distance: 2 × HTF ATR
Callback: 2 × HTF ATR

Timeframe Mapping:
| Chart TF | Trail ATR TF |
|----------|--------------|
| 1m       | 5m           |
| 5m       | 15m          |
| 15m      | 1H           |
| 1H       | 4H           |
```

### Target Based on Grade
| Grade | Target | Example (ATR=0.001) |
|-------|--------|---------------------|
| A | 6 × ATR | 0.006 |
| B | 4 × ATR | 0.004 |
| C | 2-3 × ATR | 0.002-0.003 |

---

## DASHBOARD LAYOUT

```
┌─────────────────────────────────────────────────────────────────┐
│ FOUR PILLARS v2.0                    GRADE: A    LONG           │
├─────────────────────────────────────────────────────────────────┤
│ PILLAR          │ STATUS      │ PTS │ DETAIL                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. STRUCTURE    │ ✓ BULLISH   │ 3/3 │ Above 34/50, clouds green │
│ 2. BIAS         │ ✓ BUYERS    │ 2/3 │ Above VWAP, bull flow     │
│ 3. MOMENTUM     │ ✓ DIVERGENCE│ 4/4 │ 40-4 bull div, 4/4 align  │
│ 4. VOLATILITY   │ ✓ BLUE      │ 2/2 │ BLUE DOUBLE (squeeze)     │
├─────────────────────────────────────────────────────────────────┤
│ TOTAL           │             │11/12│                           │
├─────────────────────────────────────────────────────────────────┤
│ TRIGGER         │ 40-4 BULLISH DIVERGENCE                       │
├─────────────────────────────────────────────────────────────────┤
│ POSITION MANAGEMENT                                             │
├─────────────────────────────────────────────────────────────────┤
│ Entry           │ 0.10766                                       │
│ Stop Loss       │ 0.10652 (2 ATR)                               │
│ Breakeven       │ NOT ACTIVE (9-3 at 47, need >80)              │
│ Trailing        │ NOT ACTIVE (need +2 ATR = 0.10880)            │
│ Target          │ 0.11108 (6 ATR, Grade A)                      │
└─────────────────────────────────────────────────────────────────┘
```

### Stochastic Mini Panel (Optional)
```
┌─────────────────────────────┐
│ STOCHASTICS                 │
├─────────────────────────────┤
│  9-3: 47 ▲  14-3: 52 ▲      │
│ 40-4: 38 ▲  60-10: 45 ▲     │
│ ALIGN: 4/4 BULL | DIV: YES  │
└─────────────────────────────┘
```

---

## ALERTS

### Entry Alerts (Edge-Triggered)
| Alert | Condition |
|-------|-----------|
| Grade A Long | Grade=A AND dir=LONG AND new_entry |
| Grade A Short | Grade=A AND dir=SHORT AND new_entry |
| Grade B Long | Grade=B AND dir=LONG AND new_entry |
| Grade B Short | Grade=B AND dir=SHORT AND new_entry |
| Grade C Long | Grade=C AND dir=LONG AND new_entry |
| Grade C Short | Grade=C AND dir=SHORT AND new_entry |

### Position Management Alerts
| Alert | Condition |
|-------|-----------|
| Move to Breakeven | 9-3 reaches opposite zone |
| Trailing Active | Price reaches +2 ATR |
| Exit - Momentum Fail | 40-4 momentum declines post-entry |
| Exit - VWAP Break | Price loses VWAP |
| Exit - Stop Hit | Price hits stop loss |
| Exit - Target Hit | Price hits target |

---

## WEBHOOK JSON (for n8n)

```json
{
  "indicator": "four_pillars_v2",
  "version": "2.0",
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "time": "{{timenow}}",
  "grade": "A",
  "direction": "LONG",
  "points": 11,
  "trigger": "40-4 BULLISH DIVERGENCE",
  "entry": {{close}},
  "stop_loss": {{stop_loss}},
  "target": {{target}},
  "structure_pts": 3,
  "bias_pts": 2,
  "momentum_pts": 4,
  "volatility_pts": 2,
  "stoch_9_3": {{plot("stoch_9_3")}},
  "stoch_14_3": {{plot("stoch_14_3")}},
  "stoch_40_4": {{plot("stoch_40_4")}},
  "stoch_60_10": {{plot("stoch_60_10")}},
  "alignment": {{plot("bull_count")}},
  "div_active": {{plot("div_active")}},
  "bbwp_state": "BLUE DOUBLE",
  "bbwp_value": {{plot("bbwp_value")}},
  "vol_flow": {{plot("vol_flow_numeric")}},
  "secret": "YOUR_SECRET"
}
```

---

## INTEGRATION METHOD

**Option A: External Indicators (RECOMMENDED)**

Read from indicators already on chart using their hidden plots.

```pinescript
// Each indicator exposes hidden plots
// Four Pillars reads them and combines

// Example reading from QRS
qrs_bull_count = request.security(syminfo.tickerid, timeframe.period,
    ta.valuewhen(barstate.isconfirmed, bull_count, 0))
```

**Option B: Self-Contained**

Rebuild all calculations internally. Larger code but no dependencies.

**Recommendation:** Option A for modularity. User adds 4 indicators + Four Pillars = everything works.

---

## INPUT STRUCTURE

```
GROUP: ═══ PILLAR 1: STRUCTURE ═══
- Use external Ripster (bool)
- EMA lengths if internal

GROUP: ═══ PILLAR 2: BIAS ═══
- Use external AVWAP (bool)

GROUP: ═══ PILLAR 3: MOMENTUM ═══
- Use external QRS (bool)
- Oversold level (default: 20)
- Overbought level (default: 80)

GROUP: ═══ PILLAR 4: VOLATILITY ═══
- Use external BBWP (bool)

GROUP: ═══ POSITION MANAGEMENT ═══
- ATR Length (default: 14)
- Stop Loss ATR Mult (default: 2)
- Trail Activation ATR (default: 2)
- Trail Distance ATR (default: 2)

GROUP: ═══ GRADE THRESHOLDS ═══
- Grade A minimum (default: 9)
- Grade B minimum (default: 6)
- Grade C minimum (default: 4)

GROUP: ═══ TARGETS ═══
- Grade A target ATR (default: 6)
- Grade B target ATR (default: 4)
- Grade C target ATR (default: 2)

GROUP: ═══ DASHBOARD ═══
- Show dashboard (bool)
- Position (top right/left/bottom)
- Show stoch panel (bool)
- Show position mgmt (bool)
```

---

## STATE TRACKING

```pinescript
// Position state
var bool inPosition = false
var string positionDir = "FLAT"
var float entryPrice = na
var float stopLoss = na
var float target = na
var string currentGrade = "—"
var bool beActive = false
var bool trailActive = false
var float trailStop = na
var int entryBar = na

// Entry
if entrySignal and not inPosition
    inPosition := true
    positionDir := direction
    entryPrice := close
    entryBar := bar_index
    stopLoss := direction == "LONG" ?
                close - (2 * atr) :
                close + (2 * atr)
    target := direction == "LONG" ?
              close + (gradeATR * atr) :
              close - (gradeATR * atr)
    currentGrade := grade

// Breakeven (9-3 opposite zone)
if inPosition and not beActive
    if positionDir == "LONG" and stoch_9_3 > 80
        stopLoss := entryPrice
        beActive := true
    if positionDir == "SHORT" and stoch_9_3 < 20
        stopLoss := entryPrice
        beActive := true

// Trailing
if inPosition and not trailActive
    float profitATR = positionDir == "LONG" ?
                      (close - entryPrice) / atr :
                      (entryPrice - close) / atr
    if profitATR >= 2
        trailActive := true

if trailActive
    float newTrail = positionDir == "LONG" ?
                     close - (2 * htfATR) :
                     close + (2 * htfATR)
    if positionDir == "LONG"
        trailStop := math.max(nz(trailStop, 0), newTrail)
        stopLoss := math.max(stopLoss, trailStop)
    else
        trailStop := trailStop == 0 ? newTrail : math.min(trailStop, newTrail)
        stopLoss := math.min(stopLoss, trailStop)

// Exit
if inPosition
    bool hitStop = positionDir == "LONG" ?
                   close <= stopLoss :
                   close >= stopLoss
    bool hitTarget = positionDir == "LONG" ?
                     close >= target :
                     close <= target

    if hitStop or hitTarget or exitSignal
        // Reset all
        inPosition := false
        positionDir := "FLAT"
        entryPrice := na
        // ... reset all vars
```

---

## VALIDATION CHECKLIST

```
[ ] All 4 pillar indicators added to chart
[ ] Integration reads all hidden plots correctly
[ ] Points calculated correctly for each pillar
[ ] Grade assigned based on point thresholds
[ ] Mandatory conditions enforced (cloud side + trigger)
[ ] 40-4 divergence detection triggers correctly
[ ] Stop loss calculated from chart ATR
[ ] Breakeven triggers when 9-3 reaches opposite zone
[ ] Trailing activates at +2 ATR profit
[ ] Trailing updates correctly (HTF ATR)
[ ] Dashboard displays all information
[ ] Dashboard colors reflect state
[ ] Alerts fire on grade signals (edge-triggered)
[ ] Webhook JSON formatted correctly
[ ] All hidden plots exported for external access
```

---

## INDICATORS REQUIRED

| Indicator | File | Status |
|-----------|------|--------|
| Ripster EMA Clouds | `ripster_ema_clouds_v6.pine` | ✅ Built (needs integration plots) |
| AVWAP Anchor Assistant | `avwap_anchor_assistant_v1.pine` | ✅ Built |
| Quad Rotation Stochastic | `Quad-Rotation-Stochastic-v4-CORRECTED.pine` | ✅ Built |
| QRS FAST | `Quad-Rotation-Stochastic-FAST.pine` | ✅ Built |
| BBWP v2 | `bbwp_v2.pine` | ✅ Built |
| ATR Position Manager | `atr_position_manager_v1.pine` | ⏳ Pending |
| **Four Pillars Combined** | `four_pillars_v2.pine` | ⏳ This Spec |

---

## FILE OUTPUT

```
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\four_pillars_v2.pine
```

---

## CHANGELOG

### v2.0 (2026-02-04)
- **CORRECTED** Stoch 55 → 40-4 (aligned with Kurisko HPS)
- **CORRECTED** Primary trigger is 40-4 divergence, not "Stoch 55 K/D cross"
- **REMOVED** TDI references (indicator not built)
- **ADDED** Stage-based divergence as SUPERSIGNAL
- **ADDED** 9-3 as exit/breakeven trigger
- **CLARIFIED** Role of each stochastic
- **ADDED** Detailed position management logic
- **ADDED** Integration variable specifications

### v1.0 (2026-02-04)
- Initial spec (contained errors)
