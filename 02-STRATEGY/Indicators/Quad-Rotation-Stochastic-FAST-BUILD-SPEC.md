# QUAD ROTATION STOCHASTIC FAST - BUILD SPECIFICATION
**Version:** 1.1  
**Date:** 2026-02-03  
**Status:** READY FOR CLAUDE CODE BUILD  
**Methodology:** John Kurisko HPS - Fast Variant  
**Based On:** Quad Rotation Stochastic v4.1  
**Pine Script:** v6

---

## PERFORMANCE METRICS

| Metric | Value |
|--------|-------|
| Win Rate | TBD (requires testing) |
| Signal Frequency | Higher than v4 |
| Entry Timing | Earlier than v4 |
| Stop Out Risk | Higher (faster entry) |

---

## TRADING PHILOSOPHY

**QUAD FAST vs QUAD v4:**
- v4: 40-4 divergence leads → waits for alignment → conservative
- FAST: 9-3 + 14-3 lead → slow stochs provide context → aggressive

**Use Case:** Pullback/continuation entries in established trends

**External Dependencies (same as v4):**
- VWAP exit conditions → Ripster/VWAP indicator
- Trend confirmation → Ripster EMA Clouds
- Stop management → ATR-based (separate indicator)

---

## WHAT THIS INDICATOR DOES

| Component | Detection Method | Priority |
|-----------|------------------|----------|
| FAST Signal | 9-3 + 14-3 zone turn | **PRIMARY** |
| FAST Super | FAST + slow context | **A-CLASS** |
| 40-4 Divergence | Stage-based state machine | SECONDARY |
| Quad Rotation Angle | All 4 stochs | CONTEXT |
| Alignment | Count >60 / <40 | CONTEXT |

---

## STOCHASTIC SETTINGS (Same as v4)

| Name | K | D | Smooth | Role |
|------|---|---|--------|------|
| Fast | 9 | 3 | 3 | **PRIMARY TRIGGER** |
| Fast | 14 | 3 | 3 | **CONFIRMATION** |
| Fast | 40 | 4 | 3 | Divergence, context |
| Full | 60 | 10 | 10 | Macro context |

---

## INPUTS

```pinescript
// === FAST SIGNAL SETTINGS ===
i_fast_lookback = input.int(3, "Fast Lookback", minval=3, maxval=20, group="Fast Signal",
    tooltip="Bars to compare for turn detection. 3=responsive, higher=smoother")
i_9_3_oversold = input.int(20, "9-3 Oversold Zone", minval=10, maxval=30, group="Fast Signal")
i_9_3_overbought = input.int(80, "9-3 Overbought Zone", minval=70, maxval=90, group="Fast Signal")
i_14_3_lower = input.int(40, "14-3 Lower Zone", minval=30, maxval=50, group="Fast Signal")
i_14_3_upper = input.int(60, "14-3 Upper Zone", minval=50, maxval=70, group="Fast Signal")

// === SLOW CONTEXT SETTINGS ===
i_slow_context_level = input.int(50, "Slow Context Level", minval=40, maxval=60, group="Slow Context",
    tooltip="40-4 or 60-10 above this = bullish context, below = bearish context")

// === DIVERGENCE SETTINGS (same as v4) ===
i_price_threshold = input.float(0.1, "Price Threshold %", minval=0.0, maxval=1.0, step=0.05, 
    group="Divergence", tooltip="Tolerance for equal high/low. 0.1 = 0.1%")
i_div_lookback = input.int(20, "Divergence Lookback", minval=10, maxval=50, 
    group="Divergence", tooltip="Max bars between Stage 1 and confirmation")

// === ANGLE SETTINGS (same as v4) ===
i_angle_lookback = input.int(5, "Angle Lookback Bars", minval=3, maxval=10, group="Angle")
i_signal_threshold = input.float(3.0, "Signal Threshold °", minval=1.0, maxval=10.0, group="Angle")
i_agreement_factor = input.float(0.7, "Agreement Factor", minval=0.3, maxval=0.9, step=0.1, group="Angle")

// === ALIGNMENT SETTINGS (same as v4) ===
i_align_bull = input.int(60, "Bullish Threshold", minval=50, maxval=70, group="Alignment")
i_align_bear = input.int(40, "Bearish Threshold", minval=30, maxval=50, group="Alignment")

// === VISUAL ===
i_show_9_3 = input.bool(true, "Show 9-3 Stochastic", group="Display")
i_show_14_3 = input.bool(false, "Show 14-3 Stochastic", group="Display")
i_show_40_4 = input.bool(false, "Show 40-4 Stochastic", group="Display")
```

---

## COMPONENT 1: STOCHASTIC CALCULATIONS (Same as v4)

```pinescript
//@version=6
indicator("Quad Rotation Stochastic FAST", shorttitle="QRS-FAST", overlay=false)

// ============================================================================
// FAST STOCHASTIC (9-3, 14-3, 40-4)
// ============================================================================
stoch_fast(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k = ta.sma(k_raw, smooth_k)
    k

// ============================================================================
// FULL STOCHASTIC (60-10) - DOUBLE SMOOTHING
// ============================================================================
stoch_full(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k_smooth1 = ta.sma(k_raw, smooth_k)
    float k_full = ta.sma(k_smooth1, smooth_k)
    k_full

// ============================================================================
// CALCULATE ALL 4 STOCHASTICS
// ============================================================================
float stoch_9_3  = stoch_fast(9, 3)
float stoch_14_3 = stoch_fast(14, 3)
float stoch_40_4 = stoch_fast(40, 3)
float stoch_60_10 = stoch_full(60, 10)
```

---

## COMPONENT 2: FAST SIGNAL DETECTION (NEW)

```pinescript
// ============================================================================
// FAST SIGNAL DETECTION
// Primary: 9-3 in zone + turning
// Confirmation: 14-3 in zone + moving same direction
// ============================================================================

// 9-3 conditions
bool stoch_9_3_in_oversold = stoch_9_3 < i_9_3_oversold
bool stoch_9_3_in_overbought = stoch_9_3 > i_9_3_overbought
// Must be higher than lookback AND currently rising (not just higher than old value)
bool stoch_9_3_turning_up = stoch_9_3 > nz(stoch_9_3[i_fast_lookback], 50) and stoch_9_3 > stoch_9_3[1]
bool stoch_9_3_turning_down = stoch_9_3 < nz(stoch_9_3[i_fast_lookback], 50) and stoch_9_3 < stoch_9_3[1]

// 14-3 conditions
bool stoch_14_3_in_lower = stoch_14_3 < i_14_3_lower
bool stoch_14_3_in_upper = stoch_14_3 > i_14_3_upper
// Must be higher than lookback AND currently rising
bool stoch_14_3_rising = stoch_14_3 > nz(stoch_14_3[i_fast_lookback], 50) and stoch_14_3 > stoch_14_3[1]
bool stoch_14_3_falling = stoch_14_3 < nz(stoch_14_3[i_fast_lookback], 50) and stoch_14_3 < stoch_14_3[1]

// Slow context (40-4 or 60-10 showing trend)
bool slow_context_bullish = stoch_40_4 > i_slow_context_level or stoch_60_10 > i_slow_context_level
bool slow_context_bearish = stoch_40_4 < i_slow_context_level or stoch_60_10 < i_slow_context_level

// ============================================================================
// FAST SIGNALS
// ============================================================================
bool fast_long = stoch_9_3_in_oversold and stoch_9_3_turning_up and 
                 stoch_14_3_in_lower and stoch_14_3_rising

bool fast_short = stoch_9_3_in_overbought and stoch_9_3_turning_down and 
                  stoch_14_3_in_upper and stoch_14_3_falling

// ============================================================================
// FAST SUPERSIGNALS (Fast + Slow Context)
// ============================================================================
bool fast_super_long = fast_long and slow_context_bullish
bool fast_super_short = fast_short and slow_context_bearish

// Edge detection (fires ONCE when condition first becomes true)
bool fast_long_trigger = fast_long and not fast_long[1]
bool fast_short_trigger = fast_short and not fast_short[1]
bool fast_super_long_trigger = fast_super_long and not fast_super_long[1]
bool fast_super_short_trigger = fast_super_short and not fast_super_short[1]
```

---

## COMPONENT 3: 40-4 DIVERGENCE (Same as v4)

```pinescript
// ============================================================================
// DIVERGENCE STATE VARIABLES
// ============================================================================
var int bull_state = 0
var float bull_stage1_price = na
var float bull_stage1_stoch = na
var int bull_stage1_bar = na

var int bear_state = 0
var float bear_stage1_price = na
var float bear_stage1_stoch = na
var int bear_stage1_bar = na

// ============================================================================
// BULLISH DIVERGENCE STATE MACHINE
// ============================================================================
bool bullish_divergence = false

if bull_state == 0 and stoch_40_4 < 20
    bull_state := 1
    bull_stage1_price := low
    bull_stage1_stoch := stoch_40_4
    bull_stage1_bar := bar_index

else if bull_state == 1 and stoch_40_4 < 20
    if low < bull_stage1_price
        bull_stage1_price := low
        bull_stage1_stoch := stoch_40_4

else if bull_state == 1 and stoch_40_4 >= 20
    bull_state := 2

else if bull_state == 2
    if stoch_40_4 < 20
        bull_state := 1
        bull_stage1_price := low
        bull_stage1_stoch := stoch_40_4
        bull_stage1_bar := bar_index
    else if bar_index - bull_stage1_bar > i_div_lookback
        bull_state := 0
    else
        float price_threshold_band = bull_stage1_price * (1 + i_price_threshold / 100)
        bool price_lower_or_equal = low <= price_threshold_band
        bool stoch_higher_low = stoch_40_4 > bull_stage1_stoch
        bool stoch_turning_up = stoch_40_4 > stoch_40_4[1]
        
        if price_lower_or_equal and stoch_higher_low and stoch_turning_up
            bullish_divergence := true
            bull_state := 0

// ============================================================================
// BEARISH DIVERGENCE STATE MACHINE
// ============================================================================
bool bearish_divergence = false

if bear_state == 0 and stoch_40_4 > 80
    bear_state := 1
    bear_stage1_price := high
    bear_stage1_stoch := stoch_40_4
    bear_stage1_bar := bar_index

else if bear_state == 1 and stoch_40_4 > 80
    if high > bear_stage1_price
        bear_stage1_price := high
        bear_stage1_stoch := stoch_40_4

else if bear_state == 1 and stoch_40_4 <= 80
    bear_state := 2

else if bear_state == 2
    if stoch_40_4 > 80
        bear_state := 1
        bear_stage1_price := high
        bear_stage1_stoch := stoch_40_4
        bear_stage1_bar := bar_index
    else if bar_index - bear_stage1_bar > i_div_lookback
        bear_state := 0
    else
        float price_threshold_band = bear_stage1_price * (1 - i_price_threshold / 100)
        bool price_higher_or_equal = high >= price_threshold_band
        bool stoch_lower_high = stoch_40_4 < bear_stage1_stoch
        bool stoch_turning_down = stoch_40_4 < stoch_40_4[1]
        
        if price_higher_or_equal and stoch_lower_high and stoch_turning_down
            bearish_divergence := true
            bear_state := 0
```

---

## COMPONENT 4: QUAD ROTATION ANGLE (Same as v4)

```pinescript
// ============================================================================
// QUAD ROTATION ANGLE CALCULATION
// ============================================================================
float stoch_prev = nz(stoch_40_4[i_angle_lookback], 50)
float stoch_change = (stoch_40_4 - stoch_prev) / 100.0
float base_angle = math.atan(stoch_change * 10) * (180.0 / math.pi)

bool base_rising = stoch_40_4 > stoch_prev

int agreement_count = 0
if (stoch_9_3 > nz(stoch_9_3[i_angle_lookback], 50)) == base_rising
    agreement_count += 1
if (stoch_14_3 > nz(stoch_14_3[i_angle_lookback], 50)) == base_rising
    agreement_count += 1
if (stoch_40_4 > stoch_prev) == base_rising
    agreement_count += 1
if (stoch_60_10 > nz(stoch_60_10[i_angle_lookback], 50)) == base_rising
    agreement_count += 1

float agreement = agreement_count / 4.0
float quad_angle = base_angle * (i_agreement_factor + (1.0 - i_agreement_factor) * agreement)

bool rotation_bullish = quad_angle > i_signal_threshold
bool rotation_bearish = quad_angle < -i_signal_threshold
bool rotation_neutral = math.abs(quad_angle) <= i_signal_threshold
```

---

## COMPONENT 5: ALIGNMENT COUNTING (Same as v4)

```pinescript
// ============================================================================
// ALIGNMENT COUNTING
// ============================================================================
int bull_count = 0
int bear_count = 0

if stoch_9_3 > i_align_bull
    bull_count += 1
if stoch_14_3 > i_align_bull
    bull_count += 1
if stoch_40_4 > i_align_bull
    bull_count += 1
if stoch_60_10 > i_align_bull
    bull_count += 1

if stoch_9_3 < i_align_bear
    bear_count += 1
if stoch_14_3 < i_align_bear
    bear_count += 1
if stoch_40_4 < i_align_bear
    bear_count += 1
if stoch_60_10 < i_align_bear
    bear_count += 1

bool full_bull = bull_count == 4
bool strong_bull = bull_count >= 3
bool full_bear = bear_count == 4
bool strong_bear = bear_count >= 3

var int prev_bull = 0
var int prev_bear = 0
bool flip_bullish = bull_count >= 3 and prev_bear >= 3
bool flip_bearish = bear_count >= 3 and prev_bull >= 3
prev_bull := bull_count
prev_bear := bear_count
```

---

## COMPONENT 6: ZONE & MANAGEMENT ALERTS (Same as v4)

```pinescript
// ============================================================================
// ZONE CROSSINGS (40-4)
// ============================================================================
bool entering_oversold = ta.crossunder(stoch_40_4, 20)
bool exiting_oversold = ta.crossover(stoch_40_4, 20)
bool entering_overbought = ta.crossover(stoch_40_4, 80)
bool exiting_overbought = ta.crossunder(stoch_40_4, 80)

// ============================================================================
// EMBEDDED DETECTION
// ============================================================================
bool slow_embedded_high = stoch_60_10 > 80 and stoch_40_4 > 80
bool slow_embedded_low = stoch_60_10 < 20 and stoch_40_4 < 20

// ============================================================================
// MANAGEMENT SIGNALS
// ============================================================================
bool mgmt_long_signal = ta.crossover(stoch_9_3, 80)
bool mgmt_short_signal = ta.crossunder(stoch_9_3, 20)
```

---

## PLOTTING

```pinescript
// ============================================================================
// VISIBLE PLOTS
// ============================================================================
plot(i_show_9_3 ? stoch_9_3 : na, "9-3 Stochastic", color=color.orange, linewidth=2)
plot(i_show_14_3 ? stoch_14_3 : na, "14-3 Stochastic", color=color.yellow, linewidth=1)
plot(i_show_40_4 ? stoch_40_4 : na, "40-4 Stochastic", color=color.blue, linewidth=1)

// Reference lines
hline(80, "Overbought", color=color.red, linestyle=hline.style_dashed)
hline(60, "Upper Zone", color=color.gray, linestyle=hline.style_dotted)
hline(50, "Mid", color=color.gray, linestyle=hline.style_dotted)
hline(40, "Lower Zone", color=color.gray, linestyle=hline.style_dotted)
hline(20, "Oversold", color=color.green, linestyle=hline.style_dashed)

// ============================================================================
// HIDDEN PLOTS (for JSON alerts - always plot regardless of visibility)
// ============================================================================
plot(stoch_9_3, "stoch_9_3", display=display.none)
plot(stoch_14_3, "stoch_14_3", display=display.none)
plot(stoch_40_4, "stoch_40_4", display=display.none)
plot(stoch_60_10, "stoch_60_10", display=display.none)
plot(quad_angle, "quad_angle", display=display.none)
plot(bull_count, "bull_count", display=display.none)
plot(bear_count, "bear_count", display=display.none)

// ============================================================================
// SIGNAL MARKERS
// ============================================================================
// FAST signals (primary)
plotshape(fast_long_trigger, "FAST LONG", shape.triangleup, location.bottom, 
    color=color.lime, size=size.small, text="FAST")
plotshape(fast_short_trigger, "FAST SHORT", shape.triangledown, location.top, 
    color=color.red, size=size.small, text="FAST")

// FAST SUPER signals
plotshape(fast_super_long_trigger, "FAST SUPER LONG", shape.labelup, location.bottom, 
    color=color.lime, size=size.normal, text="SUPER")
plotshape(fast_super_short_trigger, "FAST SUPER SHORT", shape.labeldown, location.top, 
    color=color.fuchsia, size=size.normal, text="SUPER")

// Divergence markers (secondary)
plotshape(bullish_divergence, "Bull Div", shape.diamond, location.bottom, 
    color=color.green, size=size.tiny, text="D")
plotshape(bearish_divergence, "Bear Div", shape.diamond, location.top, 
    color=color.red, size=size.tiny, text="D")

// Background for alignment
bgcolor(full_bull ? color.new(color.green, 90) : na)
bgcolor(full_bear ? color.new(color.red, 90) : na)
```

---

## ALERTS

### FAST Signal Alerts (PRIMARY)
```pinescript
alertcondition(fast_long_trigger, "FAST LONG", "9-3 + 14-3 bullish turn from oversold")
alertcondition(fast_short_trigger, "FAST SHORT", "9-3 + 14-3 bearish turn from overbought")
alertcondition(fast_super_long_trigger, "FAST SUPER LONG", "FAST LONG + slow context bullish")
alertcondition(fast_super_short_trigger, "FAST SUPER SHORT", "FAST SHORT + slow context bearish")
```

### Divergence Alerts (SECONDARY)
```pinescript
alertcondition(bullish_divergence, "40-4 Bullish Divergence", "Bullish divergence on 40-4")
alertcondition(bearish_divergence, "40-4 Bearish Divergence", "Bearish divergence on 40-4")
```

### Alignment Alerts (edge-triggered)
```pinescript
alertcondition(full_bull and not full_bull[1], "Full Bullish (4/4)", "All 4 stochastics above 60")
alertcondition(full_bear and not full_bear[1], "Full Bearish (4/4)", "All 4 stochastics below 40")
alertcondition(strong_bull and not strong_bull[1], "Strong Bullish (3/4)", "3+ stochastics above 60")
alertcondition(strong_bear and not strong_bear[1], "Strong Bearish (3/4)", "3+ stochastics below 40")
alertcondition(flip_bullish, "Flip to Bullish", "Alignment flipped bullish")
alertcondition(flip_bearish, "Flip to Bearish", "Alignment flipped bearish")
```

### Zone Alerts
```pinescript
alertcondition(entering_oversold, "40-4 Entering Oversold", "40-4 crossed below 20")
alertcondition(exiting_oversold, "40-4 Exiting Oversold", "40-4 crossed above 20")
alertcondition(entering_overbought, "40-4 Entering Overbought", "40-4 crossed above 80")
alertcondition(exiting_overbought, "40-4 Exiting Overbought", "40-4 crossed below 80")
```

### Management Alerts
```pinescript
alertcondition(mgmt_long_signal, "Mgmt Long (9-3 >80)", "9-3 crossed above 80 - RAISE STOP")
alertcondition(mgmt_short_signal, "Mgmt Short (9-3 <20)", "9-3 crossed below 20 - RAISE STOP")
```

### Rotation Alerts (Context)
```pinescript
alertcondition(rotation_bullish and not rotation_bullish[1], "Rotation Bullish", "Angle crossed above threshold")
alertcondition(rotation_bearish and not rotation_bearish[1], "Rotation Bearish", "Angle crossed below threshold")
```

### Embedded Alerts (Flag Context)
```pinescript
alertcondition(slow_embedded_high and not slow_embedded_high[1], "Embedded High", "60-10 and 40-4 both >80")
alertcondition(slow_embedded_low and not slow_embedded_low[1], "Embedded Low", "60-10 and 40-4 both <20")
```

---

## JSON ALERT PAYLOAD

```json
{
  "ticker": "{{ticker}}",
  "timeframe": "{{interval}}",
  "timestamp": "{{time}}",
  "close": {{close}},
  "signal_type": "FAST_LONG",
  "stochastics": {
    "9_3": {{plot("stoch_9_3")}},
    "14_3": {{plot("stoch_14_3")}},
    "40_4": {{plot("stoch_40_4")}},
    "60_10": {{plot("stoch_60_10")}}
  },
  "rotation": {
    "angle": {{plot("quad_angle")}},
    "bull_count": {{plot("bull_count")}},
    "bear_count": {{plot("bear_count")}}
  }
}
```

---

## DIFFERENCES FROM V4

| Aspect | v4 | FAST |
|--------|-----|------|
| Primary trigger | 40-4 divergence | 9-3 + 14-3 turn |
| Entry timing | Later (wait for alignment) | Earlier |
| Signal frequency | Lower | Higher |
| False signals | Fewer | More |
| Default plot | 40-4 | 9-3 |
| Stop out risk | Lower | Higher |
| Best for | Reversals, exhaustion | Pullbacks, continuation |

---

## TESTING CHECKLIST

### Fast Signal Detection
- [ ] 9-3 zone detection correct (20/80)
- [ ] 14-3 zone detection correct (40/60)
- [ ] Lookback comparison works (3-20)
- [ ] Edge detection prevents repeat signals
- [ ] Slow context correctly identifies trend

### Stochastic Calculations
- [ ] All 4 calculate correctly
- [ ] Same values as v4

### Divergence (same as v4)
- [ ] State machine works
- [ ] Signals fire correctly

### Alerts
- [ ] All edge-triggered
- [ ] JSON populates

---

## VERSION HISTORY

**v1.1 (2026-02-03) - Critical Review Fixes**
- ✅ Fixed: `bear_state_bar` typo → `bear_stage1_bar`
- ✅ Fixed: Turn detection now requires current bar momentum (`stoch > stoch[1]`)
- ✅ Fixed: Simplified edge detection using `[1]` instead of `var` tracking
- ✅ Fixed: Hidden plots always available for JSON (separate from visible plots)
- ✅ Added: 50 midline reference

**v1.0 (2026-02-03) - Initial Build**
- 9-3 + 14-3 as primary trigger
- Configurable lookback (3-20)
- Slow context for SUPER signals
- All v4 components retained (divergence, angle, alignment)

---

**STATUS: READY FOR CLAUDE CODE BUILD (v1.1 - ALL ISSUES FIXED)**
