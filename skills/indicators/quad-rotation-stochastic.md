# QUAD ROTATION STOCHASTIC INDICATOR - FRAMEWORK
**Purpose:** Calculate 4-Stochastic alignment for Quad Rotation strategy setups  
**Strategy Components:** Divergence, Coil, Trend Line, Vwap  
**Integration:** Replaces Multi-RSI as Pillar 3 in Four Pillars framework  
**Output:** Alignment data for trader decision (not standalone entry signals)  
**Location:** Internal to main strategy indicator (not separately visible)

---

## QUAD ROTATION STOCHASTIC - STRATEGY SUMMARY

### **Core Philosophy**
The Quad Rotation strategy combines 4 elements: **Divergence**, **Coil**, **Trend Line**, and **Vwap**. This indicator focuses on the 4 Stochastics which provide the momentum layer for these setups.

### **The 4 Stochastics:**
- **Fast (9-3):** Entry timing - **DIVERGENCE DETECTION ONLY USES THIS ONE**
- **Standard (14-3):** Primary confirmation
- **Medium (40-4):** Trend context  
- **Slow (60-10):** Macro filter

### **Four Core Setups (from Trading Playbook):**
1. **Quad Divergence** - Uses Fast (9-3) stochastic
2. **Quad Channel Line** - Channel breakout with stochastic rotation
3. **Plain Divergence** - Basic divergence
4. **20/20 Bull or Bear Flag** - Flag patterns
5. **Dealer's Choice** - Combinations

### **Super Signal:**
Merger of Quad Rotation + HPS Playbook trade setup = ONLY trade the Super Signal

### **Purpose:**
- Calculate alignment strength (4/4, 3/4, 2/4)
- Detect divergence on Fast (9-3) stochastic **ONLY**
- Provide momentum context for all Quad Rotation setups
- Output data to dashboard
- **NOT** a standalone entry signal - part of "Super Signal"

### **Divergence Detection Logic (Fast 9-3 Stochastic ONLY):**

**BUY SIDE (Bullish Divergence):**
1. **Stage 1:** Fast stochastic drops <20 → Price makes low → Bounces → Fast stochastic back >20
2. **Stage 2:** Price makes lower low (or double bottom) + Fast stochastic makes higher low (can be >20, doesn't need to stay exactly at 20)
3. **Optional:** 5min/60min stochastics rising from oversold + Reversal candle + Lower channel line

**SELL SIDE (Bearish Divergence):**
1. **Stage 1:** Fast stochastic rises >80 → Price makes high → Pulls back → Fast stochastic back <80
2. **Stage 2:** Price makes higher high (or double top) + Fast stochastic makes lower high (can be <80, doesn't need to stay exactly at 80)
3. **Optional:** 5min/60min stochastics falling from overbought + Reversal candle + Upper channel line

### **Alignment Conditions:**
- **Strongest (4/4):** All 4 stochastics above/below 50
- **Strong (3/4):** 3 out of 4 aligned
- **Continuation (2/4):** 2 out of 4 aligned + Macro (slow 60-10) climbing/descending

### **Output to Dashboard:**
- Alignment count (4/4, 3/4, 2/4, 1/4, 0/4)
- Direction (bullish/bearish/neutral)
- Each stochastic's current value
- Divergence status (detected/not detected) - **ONLY from Fast 9-3**
- **Trader decides:** Yes/No based on alignment + other pillars

---

## PINE SCRIPT v6 FRAMEWORK

### INDICATOR HEADER
```pinescript
//@version=6
indicator("Quad Rotation Stochastic", shorttitle="QRS", overlay=false)
```

---

## INPUT PARAMETERS

### Stochastic Settings
```pinescript
// Fast Stochastic (9-3) - USED FOR DIVERGENCE DETECTION
fast_k = input.int(9, "Fast K Length", minval=1, group="Fast Stochastic (9-3)")
fast_d = input.int(3, "Fast D Smoothing", minval=1, group="Fast Stochastic (9-3)")

// Standard Stochastic (14-3)
std_k = input.int(14, "Standard K Length", minval=1, group="Standard Stochastic (14-3)")
std_d = input.int(3, "Standard D Smoothing", minval=1, group="Standard Stochastic (14-3)")

// Medium Stochastic (40-4)
med_k = input.int(40, "Medium K Length", minval=1, group="Medium Stochastic (40-4)")
med_d = input.int(4, "Medium D Smoothing", minval=1, group="Medium Stochastic (40-4)")

// Slow Stochastic (60-10) - MACRO FILTER
slow_k = input.int(60, "Slow K Length", minval=1, group="Slow Stochastic (60-10)")
slow_d = input.int(10, "Slow D Smoothing", minval=1, group="Slow Stochastic (60-10)")

// Smoothing method (SMA is standard)
smooth_k = input.int(3, "K Smoothing", minval=1, group="General")
```

### Alignment Thresholds
```pinescript
// Overbought/Oversold levels
ob_level = input.int(80, "Overbought Level", minval=50, maxval=100, group="Levels")
os_level = input.int(20, "Oversold Level", minval=0, maxval=50, group="Levels")

// Alignment threshold (50 = neutral line)
align_threshold = input.int(50, "Alignment Threshold", minval=0, maxval=100, group="Levels")
```

### Divergence Detection Settings (Fast 9-3 Only)
```pinescript
// Lookback period for divergence detection
divergence_lookback = input.int(10, "Divergence Lookback", minval=5, maxval=50, group="Divergence")

// Minimum bars between pivots
min_pivot_bars = input.int(3, "Min Bars Between Pivots", minval=1, group="Divergence")
```

---

## STOCHASTIC CALCULATIONS

### Function: Calculate Stochastic
```pinescript
// Custom stochastic function
stoch(k_length, d_length, smooth) =>
    // Calculate %K
    lowest_low = ta.lowest(low, k_length)
    highest_high = ta.highest(high, k_length)
    k_raw = 100 * (close - lowest_low) / (highest_high - lowest_low)
    
    // Smooth %K
    k = ta.sma(k_raw, smooth)
    
    // Calculate %D (SMA of %K)
    d = ta.sma(k, d_length)
    
    [k, d]
```

### Calculate All 4 Stochastics
```pinescript
// Fast Stochastic (9-3) - PRIMARY FOR DIVERGENCE
[fast_k_val, fast_d_val] = stoch(fast_k, fast_d, smooth_k)

// Standard Stochastic (14-3)
[std_k_val, std_d_val] = stoch(std_k, std_d, smooth_k)

// Medium Stochastic (40-4)
[med_k_val, med_d_val] = stoch(med_k, med_d, smooth_k)

// Slow Stochastic (60-10) - MACRO FILTER
[slow_k_val, slow_d_val] = stoch(slow_k, slow_d, smooth_k)
```

---

## ALIGNMENT DETECTION

### Bullish/Bearish Alignment
```pinescript
// Check if stochastic is bullish (above threshold)
fast_bullish = fast_k_val > align_threshold
std_bullish = std_k_val > align_threshold
med_bullish = med_k_val > align_threshold
slow_bullish = slow_k_val > align_threshold

// Check if stochastic is bearish (below threshold)
fast_bearish = fast_k_val < align_threshold
std_bearish = std_k_val < align_threshold
med_bearish = med_k_val < align_threshold
slow_bearish = slow_k_val < align_threshold
```

### Count Aligned Stochastics
```pinescript
// Count bullish alignment
bullish_count = 0
bullish_count := bullish_count + (fast_bullish ? 1 : 0)
bullish_count := bullish_count + (std_bullish ? 1 : 0)
bullish_count := bullish_count + (med_bullish ? 1 : 0)
bullish_count := bullish_count + (slow_bullish ? 1 : 0)

// Count bearish alignment
bearish_count = 0
bearish_count := bearish_count + (fast_bearish ? 1 : 0)
bearish_count := bearish_count + (std_bearish ? 1 : 0)
bearish_count := bearish_count + (med_bearish ? 1 : 0)
bearish_count := bearish_count + (slow_bearish ? 1 : 0)
```

### Alignment Strength
```pinescript
// Determine overall alignment
alignment_strength = bullish_count > bearish_count ? bullish_count : -bearish_count
alignment_direction = bullish_count > bearish_count ? "BULLISH" : bearish_count > bullish_count ? "BEARISH" : "NEUTRAL"

// Alignment quality
is_full_alignment = bullish_count == 4 or bearish_count == 4  // 4/4
is_strong_alignment = bullish_count >= 3 or bearish_count >= 3  // 3/4
is_continuation_setup = (bullish_count >= 2 and slow_bullish) or (bearish_count >= 2 and slow_bearish)  // 2/4 + macro
```

---

## DIVERGENCE DETECTION (FAST 9-3 STOCHASTIC ONLY)

### Pivot Detection
```pinescript
// Find pivot highs and lows in price
pivot_high_price = ta.pivothigh(high, min_pivot_bars, min_pivot_bars)
pivot_low_price = ta.pivotlow(low, min_pivot_bars, min_pivot_bars)

// Find pivot highs and lows in FAST stochastic ONLY (not all 4)
pivot_high_stoch = ta.pivothigh(fast_k_val, min_pivot_bars, min_pivot_bars)
pivot_low_stoch = ta.pivotlow(fast_k_val, min_pivot_bars, min_pivot_bars)
```

### Bullish Divergence Detection (Buy Setup)
```pinescript
// Stage 1: Fast stochastic went <20, bounced >20
var float prev_low_stoch = na
var float prev_low_price = na
var int prev_low_bar = na

if not na(pivot_low_stoch) and not na(pivot_low_price)
    prev_low_stoch := fast_k_val[min_pivot_bars]
    prev_low_price := low[min_pivot_bars]
    prev_low_bar := bar_index - min_pivot_bars

// Stage 2: Price makes lower low, fast stochastic makes higher low
// NOTE: Higher low can be >20 (doesn't need to stay exactly at 20)
bullish_divergence = false
if not na(pivot_low_stoch) and not na(pivot_low_price) and not na(prev_low_stoch)
    current_low_price = low[min_pivot_bars]
    current_low_stoch = fast_k_val[min_pivot_bars]
    
    // Check conditions:
    // 1. Current price low < previous price low (lower low in price)
    // 2. Current stoch low > previous stoch low (higher low in stochastic)
    // 3. Previous stoch was <20 (oversold in Stage 1)
    // 4. Stochastic bounced back >20 at some point
    if current_low_price < prev_low_price and current_low_stoch > prev_low_stoch
        if prev_low_stoch < os_level
            bullish_divergence := true
```

### Bearish Divergence Detection (Sell Setup)
```pinescript
// Stage 1: Fast stochastic went >80, pulled back <80
var float prev_high_stoch = na
var float prev_high_price = na
var int prev_high_bar = na

if not na(pivot_high_stoch) and not na(pivot_high_price)
    prev_high_stoch := fast_k_val[min_pivot_bars]
    prev_high_price := high[min_pivot_bars]
    prev_high_bar := bar_index - min_pivot_bars

// Stage 2: Price makes higher high, fast stochastic makes lower high
// NOTE: Lower high can be <80 (doesn't need to stay exactly at 80)
bearish_divergence = false
if not na(pivot_high_stoch) and not na(pivot_high_price) and not na(prev_high_stoch)
    current_high_price = high[min_pivot_bars]
    current_high_stoch = fast_k_val[min_pivot_bars]
    
    // Check conditions:
    // 1. Current price high > previous price high (higher high in price)
    // 2. Current stoch high < previous stoch high (lower high in stochastic)
    // 3. Previous stoch was >80 (overbought in Stage 1)
    // 4. Stochastic pulled back <80 at some point
    if current_high_price > prev_high_price and current_high_stoch < prev_high_stoch
        if prev_high_stoch > ob_level
            bearish_divergence := true
```

---

## MOMENTUM DIRECTION (Macro Trend)

### Slow Stochastic Trend
```pinescript
// Check if slow (macro) stochastic is climbing or descending
slow_climbing = slow_k_val > slow_k_val[1] and slow_k_val[1] > slow_k_val[2]  // Rising for 2 bars
slow_descending = slow_k_val < slow_k_val[1] and slow_k_val[1] < slow_k_val[2]  // Falling for 2 bars

// Macro trend state
macro_trend = slow_climbing ? "CLIMBING" : slow_descending ? "DESCENDING" : "FLAT"
```

---

## OVERSOLD/OVERBOUGHT CONDITIONS

### Current State
```pinescript
// Check if any stochastic is in oversold/overbought territory
fast_oversold = fast_k_val < os_level
std_oversold = std_k_val < os_level
med_oversold = med_k_val < os_level
slow_oversold = slow_k_val < os_level

fast_overbought = fast_k_val > ob_level
std_overbought = std_k_val > ob_level
med_overbought = med_k_val > ob_level
slow_overbought = slow_k_val > ob_level

// Any in extreme zones
any_oversold = fast_oversold or std_oversold or med_oversold or slow_oversold
any_overbought = fast_overbought or std_overbought or med_overbought or slow_overbought
```

---

## OUTPUT VARIABLES FOR ALERT/DASHBOARD

### Structured Output
```pinescript
// These variables will be used in TradingView alerts and passed to n8n
var string output_alignment_direction = na
var int output_alignment_count = na
var string output_macro_trend = na
var bool output_bullish_divergence = na
var bool output_bearish_divergence = na

// Update output variables
output_alignment_direction := alignment_direction
output_alignment_count := bullish_count > bearish_count ? bullish_count : bearish_count
output_macro_trend := macro_trend
output_bullish_divergence := bullish_divergence
output_bearish_divergence := bearish_divergence

// Individual stochastic values (for dashboard)
var float output_fast_k = na
var float output_std_k = na
var float output_med_k = na
var float output_slow_k = na

output_fast_k := fast_k_val
output_std_k := std_k_val
output_med_k := med_k_val
output_slow_k := slow_k_val
```

---

## PLOTTING (Optional - for standalone testing)

### Visual Display
```pinescript
// Plot all 4 stochastics
plot(fast_k_val, "Fast (9-3)", color=color.blue, linewidth=1)
plot(std_k_val, "Standard (14-3)", color=color.green, linewidth=1)
plot(med_k_val, "Medium (40-4)", color=color.orange, linewidth=1)
plot(slow_k_val, "Slow (60-10)", color=color.red, linewidth=2)  // Thicker for macro

// Plot reference lines
hline(ob_level, "Overbought", color=color.red, linestyle=hline.style_dashed)
hline(align_threshold, "Neutral", color=color.gray, linestyle=hline.style_dotted)
hline(os_level, "Oversold", color=color.green, linestyle=hline.style_dashed)

// Plot alignment background
bgcolor(is_full_alignment and bullish_count == 4 ? color.new(color.green, 90) : na)
bgcolor(is_full_alignment and bearish_count == 4 ? color.new(color.red, 90) : na)

// Plot divergence signals (from Fast 9-3 ONLY)
plotshape(bullish_divergence, "Bullish Div", style=shape.triangleup, location=location.bottom, color=color.green, size=size.small)
plotshape(bearish_divergence, "Bearish Div", style=shape.triangledown, location=location.top, color=color.red, size=size.small)
```

---

## ALERT CONDITIONS

### Alert Triggers
```pinescript
// Alert when full alignment occurs (4/4)
alertcondition(is_full_alignment and bullish_count == 4, "Full Bullish Alignment", "All 4 stochastics aligned BULLISH")
alertcondition(is_full_alignment and bearish_count == 4, "Full Bearish Alignment", "All 4 stochastics aligned BEARISH")

// Alert when divergence is detected (Fast 9-3 ONLY)
alertcondition(bullish_divergence, "Bullish Divergence", "Bullish divergence detected on Fast (9-3)")
alertcondition(bearish_divergence, "Bearish Divergence", "Bearish divergence detected on Fast (9-3)")

// Alert when continuation setup (2/4 + macro trend)
alertcondition(is_continuation_setup and slow_climbing, "Bullish Continuation", "2+ stochastics aligned + macro climbing")
alertcondition(is_continuation_setup and slow_descending, "Bearish Continuation", "2+ stochastics aligned + macro descending")
```

---

## JSON PAYLOAD FOR TRADINGVIEW ALERTS

### Alert Message Template
```json
{
  "stochastic_data": {
    "alignment": {
      "direction": "{{output_alignment_direction}}",
      "count": "{{output_alignment_count}}",
      "strength": "{{is_full_alignment ? 'FULL' : is_strong_alignment ? 'STRONG' : is_continuation_setup ? 'CONTINUATION' : 'WEAK'}}"
    },
    "values": {
      "fast_9_3": "{{output_fast_k}}",
      "std_14_3": "{{output_std_k}}",
      "med_40_4": "{{output_med_k}}",
      "slow_60_10": "{{output_slow_k}}"
    },
    "divergence": {
      "bullish": "{{output_bullish_divergence}}",
      "bearish": "{{output_bearish_divergence}}",
      "note": "Divergence detected using Fast (9-3) stochastic only"
    },
    "macro_trend": "{{output_macro_trend}}",
    "conditions": {
      "oversold": "{{any_oversold}}",
      "overbought": "{{any_overbought}}"
    }
  }
}
```

---

## INTEGRATION WITH FOUR PILLARS STRATEGY

### When Used in Main Indicator
```pinescript
// Import this as Pillar 3: Stochastic Momentum
// Replace Multi-RSI calculations with:

// Call stochastic alignment function
[align_direction, align_count, macro_trend, bull_div, bear_div] = quad_rotation_stochastic()

// Use in strategy conditions
pillar3_bullish = align_direction == "BULLISH" and align_count >= 3
pillar3_bearish = align_direction == "BEARISH" and align_count >= 3

// Optional: Require divergence for highest-probability setups
pillar3_with_divergence = (pillar3_bullish and bull_div) or (pillar3_bearish and bear_div)
```

---

## USAGE NOTES FOR CLAUDE CODE

### What to Build
1. **Complete Pine Script indicator** with all functions above
2. **Internal calculations** - not visible on chart (if embedded in main strategy)
3. **Output variables** for alert JSON payload
4. **Divergence detection** logic using **FAST (9-3) STOCHASTIC ONLY**
5. **Alignment counting** and strength classification

### Critical Requirements
- ✅ Divergence detection uses **ONLY Fast (9-3)** stochastic
- ✅ Stage 2 bullish: Higher low **can be >20** (not required to stay at 20)
- ✅ Stage 2 bearish: Lower high **can be <80** (not required to stay at 80)
- ✅ All 4 stochastics calculated for alignment
- ✅ Slow (60-10) used as macro trend filter

### What NOT to Include
- ❌ Entry/exit signals directly
- ❌ Strategy.entry() or strategy.close() calls
- ❌ Automatic trade execution
- ❌ Position sizing logic
- ❌ Divergence detection on all 4 stochastics (ONLY Fast 9-3)

### Testing Checklist
- [ ] All 4 stochastics calculate correctly
- [ ] Alignment count matches visual inspection (4/4, 3/4, 2/4)
- [ ] Divergence detection triggers on valid setups **using Fast 9-3 only**
- [ ] Macro trend (slow stochastic) direction correct
- [ ] Alert JSON payload contains all required fields
- [ ] Works on 30min timeframe (primary trading timeframe)
- [ ] Can be embedded in main strategy indicator

### Refinement Areas
1. **Divergence detection** - May need adjustment for double top/bottom detection
2. **Pivot lookback** - May need to vary by timeframe (5min vs 60min)
3. **Alignment threshold** - Currently 50, may need dynamic adjustment
4. **Macro trend** - Currently 2-bar confirmation, may need longer

---

## DEPLOYMENT INSTRUCTIONS

### Standalone Indicator (for testing)
1. Give this framework to Claude Code
2. Claude Code builds full Pine Script v6 indicator
3. Save as "Quad Rotation Stochastic.pine"
4. Apply to chart in TradingView
5. Test on BYBIT:RIVERUSDT.P 30min timeframe
6. Verify alignment count and divergence signals (Fast 9-3 only)

### Integrated into Main Strategy
1. Copy functions and calculations from built indicator
2. Paste into main Four Pillars strategy indicator
3. Remove plotting code
4. Keep only output variables and alert conditions
5. Use output variables in strategy logic

---

## FILE LOCATION
**Framework saved to:** `C:\Users\User\Documents\Obsidian Vault\skills\indicators\quad-rotation-stochastic.md`

**Related Files:**
- Main Strategy: `indicators\four-pillars-strategy.pine` (to be created)
- Alert Template: `02-STRATEGY\alert-templates\quad-rotation-alert.json`
- Usage Guide: `02-STRATEGY\Quad-Rotation-Rules.md`

---

## QUAD ROTATION STRATEGY COMPONENTS

**Remember:** This indicator is just ONE part of the Quad Rotation system, which has 4 elements:
1. **Divergence** - Detected using Fast (9-3) stochastic
2. **Coil** - Tight consolidation before breakout
3. **Trend Line** - Channel lines for support/resistance
4. **Vwap** - Price relationship to volume-weighted average

**Super Signal = Quad Rotation + HPS Playbook setup**

---

**Status:** Framework complete - Ready for Claude Code implementation  
**Next Step:** Give this framework to Claude Code to build full Pine Script v6 indicator  
**Testing:** BYBIT:RIVERUSDT.P 30min timeframe with live market data  
**Important:** Divergence uses ONLY Fast (9-3) stochastic, not all 4
