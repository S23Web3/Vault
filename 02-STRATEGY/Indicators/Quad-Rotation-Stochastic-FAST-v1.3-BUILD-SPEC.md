# QUAD ROTATION STOCHASTIC FAST v1.3 - BUILD SPECIFICATION
**Version:** 1.3  
**Date:** 2026-02-04  
**Status:** READY FOR CLAUDE CODE BUILD  
**Methodology:** John Kurisko HPS - Fast Variant  
**Role:** Momentum Rotation Detection (Pillar 4 of Four Pillars)  
**Pine Script:** v6

---

## CRITICAL DESIGN PRINCIPLE

**This indicator is ONE PILLAR - NOT a standalone trading system.**

| Pillar | Indicator | Role |
|--------|-----------|------|
| 1 | Ripster EMA Clouds | **Trend direction** |
| 2 | VWAP | **Value position** |
| 3 | BBWP | **Volatility state** |
| 4 | **Quad Rotation FAST** | **Momentum rotation** |

**FAST does NOT filter by trend.** It outputs rotation state. The integration layer (Four Pillars dashboard or n8n) decides whether to act based on ALL pillars.

---

## PHILOSOPHY CHANGES FROM v1.2

| Aspect | v1.2 | v1.3 |
|--------|------|------|
| Trend filter | Built-in (Auto/Manual) | **REMOVED** |
| Channel (60-10) | MANDATORY filter | **CONTEXT OUTPUT only** |
| Counter-trend exit | Tight exit logic | **REMOVED** |
| Signal hierarchy | 4 tiers (trend-dependent) | **3 tiers (rotation quality)** |
| Zone threshold | Strict only (20/80) | **+ near zone (30/70)** |
| 14-3 confirmation | 2-bar momentum | **1-bar direction** |
| Signal cooldown | None | **5-bar minimum** |

---

## WHAT THIS INDICATOR DOES

| Function | Output Type | Consumer |
|----------|-------------|----------|
| Detect 9-3 rotation from zone | Signal + Alert | n8n / Dashboard |
| Confirm with 14-3 direction | Signal tier | Position sizing |
| Track 40-4 and 60-10 state | Hidden plots (JSON) | Integration layer |
| Identify exit zones | Alert | Trade management |

## WHAT THIS INDICATOR DOES NOT DO

| Function | Handled By |
|----------|------------|
| Filter by trend direction | Ripster EMA Clouds |
| Confirm value position | VWAP indicator |
| Time entry by volatility | BBWP indicator |
| Track open positions | n8n workflow |
| Calculate stop loss | ATR indicator |

---

## STOCHASTIC SETTINGS

| Name | K | Smooth | Type | Role in FAST |
|------|---|--------|------|--------------|
| 9-3 | 9 | 3 | Fast | **PRIMARY TRIGGER** |
| 14-3 | 14 | 3 | Fast | **ROTATION CONFIRMATION** |
| 40-4 | 40 | 4 | Fast | Context output |
| 60-10 | 60 | 10 | Full (double) | Context output |

---

## INPUTS

```pinescript
//@version=6
indicator("Quad Rotation Stochastic FAST v1.3", shorttitle="QRS-FAST", overlay=false)

// === ZONE SETTINGS ===
i_9_3_oversold = input.int(20, "9-3 Oversold", minval=10, maxval=30, group="Zones",
    tooltip="Strict oversold zone")
i_9_3_overbought = input.int(80, "9-3 Overbought", minval=70, maxval=90, group="Zones",
    tooltip="Strict overbought zone")
i_9_3_near_oversold = input.int(30, "9-3 Near Oversold", minval=20, maxval=40, group="Zones",
    tooltip="Near zone for lower confidence signals")
i_9_3_near_overbought = input.int(70, "9-3 Near Overbought", minval=60, maxval=80, group="Zones",
    tooltip="Near zone for lower confidence signals")

// === TIMING SETTINGS ===
i_zone_memory = input.int(3, "Zone Memory Bars", minval=1, maxval=10, group="Timing",
    tooltip="Bars to remember recent zone visit")
i_signal_cooldown = input.int(5, "Signal Cooldown Bars", minval=0, maxval=20, group="Timing",
    tooltip="Minimum bars between signals (0 = off)")

// === EXIT ZONE SETTINGS ===
i_exit_warning = input.int(70, "Exit Warning Level", minval=60, maxval=80, group="Exit",
    tooltip="9-3 level to warn approaching exit zone")
i_exit_signal = input.int(80, "Exit Signal Level", minval=70, maxval=90, group="Exit",
    tooltip="9-3 level for take profit zone")

// === DISPLAY ===
i_show_9_3 = input.bool(true, "Show 9-3", group="Display")
i_show_14_3 = input.bool(false, "Show 14-3", group="Display")
i_show_40_4 = input.bool(false, "Show 40-4", group="Display")
i_show_60_10 = input.bool(false, "Show 60-10", group="Display")
```

---

## COMPONENT 1: STOCHASTIC CALCULATIONS

```pinescript
// ============================================================================
// FAST STOCHASTIC - Single smoothing
// ============================================================================
stoch_fast(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k = ta.sma(k_raw, smooth_k)
    k

// ============================================================================
// FULL STOCHASTIC - Double smoothing (60-10)
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
float stoch_9_3 = stoch_fast(9, 3)
float stoch_14_3 = stoch_fast(14, 3)
float stoch_40_4 = stoch_fast(40, 4)
float stoch_60_10 = stoch_full(60, 10)

// Warmup check
int WARMUP_BARS = 80
bool is_warmed_up = bar_index >= WARMUP_BARS
```

---

## COMPONENT 2: ZONE DETECTION

```pinescript
// ============================================================================
// ZONE MEMORY - Was recently in extreme zone
// ============================================================================

// Strict zones (high confidence)
bool was_oversold = ta.lowest(stoch_9_3, i_zone_memory) < i_9_3_oversold
bool was_overbought = ta.highest(stoch_9_3, i_zone_memory) > i_9_3_overbought

// Near zones (lower confidence, catches more setups)
bool was_near_oversold = ta.lowest(stoch_9_3, i_zone_memory) < i_9_3_near_oversold
bool was_near_overbought = ta.highest(stoch_9_3, i_zone_memory) > i_9_3_near_overbought

// Zone state for JSON output
string zone_state = was_oversold ? "oversold" : 
                    was_overbought ? "overbought" : 
                    was_near_oversold ? "near_oversold" :
                    was_near_overbought ? "near_overbought" : "neutral"
```

---

## COMPONENT 3: ROTATION DETECTION

```pinescript
// ============================================================================
// 9-3 ROTATION (Primary) - Requires 2-bar momentum
// ============================================================================
bool stoch_9_3_rotating_up = stoch_9_3 > stoch_9_3[1] and stoch_9_3[1] > stoch_9_3[2]
bool stoch_9_3_rotating_down = stoch_9_3 < stoch_9_3[1] and stoch_9_3[1] < stoch_9_3[2]

// ============================================================================
// 14-3 CONFIRMATION - Single bar direction (allows natural lag)
// ============================================================================
bool stoch_14_3_up = stoch_14_3 > stoch_14_3[1]
bool stoch_14_3_down = stoch_14_3 < stoch_14_3[1]

// ============================================================================
// 40-4 DIRECTION - Context output
// ============================================================================
bool stoch_40_4_up = stoch_40_4 > stoch_40_4[1]
bool stoch_40_4_down = stoch_40_4 < stoch_40_4[1]
bool stoch_40_4_bullish = stoch_40_4 > 50
bool stoch_40_4_bearish = stoch_40_4 < 50

// ============================================================================
// 60-10 DIRECTION - Context output (channel)
// ============================================================================
bool stoch_60_10_up = stoch_60_10 > stoch_60_10[1]
bool stoch_60_10_down = stoch_60_10 < stoch_60_10[1]
bool stoch_60_10_bullish = stoch_60_10 > 50
bool stoch_60_10_bearish = stoch_60_10 < 50

// ============================================================================
// FULL ROTATION - All 4 stochastics moving same direction
// ============================================================================
bool all_rotating_up = stoch_9_3_rotating_up and stoch_14_3_up and stoch_40_4_up and stoch_60_10_up
bool all_rotating_down = stoch_9_3_rotating_down and stoch_14_3_down and stoch_40_4_down and stoch_60_10_down

// Context state for JSON output
string channel_context = stoch_60_10_bullish and stoch_60_10_up ? "bullish_rising" :
                         stoch_60_10_bullish and stoch_60_10_down ? "bullish_falling" :
                         stoch_60_10_bearish and stoch_60_10_down ? "bearish_falling" :
                         stoch_60_10_bearish and stoch_60_10_up ? "bearish_rising" : "neutral"

string mid_context = stoch_40_4_bullish ? "bullish" : stoch_40_4_bearish ? "bearish" : "neutral"
```

---

## COMPONENT 4: SIGNAL GENERATION

```pinescript
// ============================================================================
// SIGNAL TIERS (by rotation quality, NOT trend filtered)
// ============================================================================

// TIER 1: FAST ROTATION - 9-3 turning from strict zone
bool fast_rotation_long = was_oversold and stoch_9_3_rotating_up
bool fast_rotation_short = was_overbought and stoch_9_3_rotating_down

// TIER 2: FAST CONFIRMED - 9-3 + 14-3 aligned
bool fast_confirmed_long = was_oversold and stoch_9_3_rotating_up and stoch_14_3_up
bool fast_confirmed_short = was_overbought and stoch_9_3_rotating_down and stoch_14_3_down

// TIER 3: FAST FULL - All 4 stochastics rotating
bool fast_full_long = was_oversold and all_rotating_up
bool fast_full_short = was_overbought and all_rotating_down

// NEAR ZONE VARIANTS (lower confidence, more signals)
bool fast_near_long = was_near_oversold and not was_oversold and stoch_9_3_rotating_up and stoch_14_3_up
bool fast_near_short = was_near_overbought and not was_overbought and stoch_9_3_rotating_down and stoch_14_3_down

// ============================================================================
// COOLDOWN LOGIC
// ============================================================================
var int bars_since_long_signal = 999
var int bars_since_short_signal = 999

// ============================================================================
// EDGE DETECTION WITH COOLDOWN
// ============================================================================
bool fast_rotation_long_raw = fast_rotation_long and not fast_rotation_long[1]
bool fast_rotation_short_raw = fast_rotation_short and not fast_rotation_short[1]

bool fast_confirmed_long_raw = fast_confirmed_long and not fast_confirmed_long[1]
bool fast_confirmed_short_raw = fast_confirmed_short and not fast_confirmed_short[1]

bool fast_full_long_raw = fast_full_long and not fast_full_long[1]
bool fast_full_short_raw = fast_full_short and not fast_full_short[1]

bool fast_near_long_raw = fast_near_long and not fast_near_long[1]
bool fast_near_short_raw = fast_near_short and not fast_near_short[1]

// Apply cooldown
bool cooldown_allows_long = i_signal_cooldown == 0 or bars_since_long_signal > i_signal_cooldown
bool cooldown_allows_short = i_signal_cooldown == 0 or bars_since_short_signal > i_signal_cooldown

// Final triggers
bool fast_rotation_long_trigger = fast_rotation_long_raw and cooldown_allows_long
bool fast_rotation_short_trigger = fast_rotation_short_raw and cooldown_allows_short

bool fast_confirmed_long_trigger = fast_confirmed_long_raw and cooldown_allows_long
bool fast_confirmed_short_trigger = fast_confirmed_short_raw and cooldown_allows_short

bool fast_full_long_trigger = fast_full_long_raw and cooldown_allows_long
bool fast_full_short_trigger = fast_full_short_raw and cooldown_allows_short

bool fast_near_long_trigger = fast_near_long_raw and cooldown_allows_long
bool fast_near_short_trigger = fast_near_short_raw and cooldown_allows_short

// Update cooldown counters
if fast_rotation_long_trigger or fast_confirmed_long_trigger or fast_full_long_trigger
    bars_since_long_signal := 0
else
    bars_since_long_signal := math.min(bars_since_long_signal + 1, 999)

if fast_rotation_short_trigger or fast_confirmed_short_trigger or fast_full_short_trigger
    bars_since_short_signal := 0
else
    bars_since_short_signal := math.min(bars_since_short_signal + 1, 999)
```

---

## COMPONENT 5: EXIT ZONES

```pinescript
// ============================================================================
// EXIT ZONE DETECTION (zone-based, not position-based)
// ============================================================================

// Long exit zones (9-3 rising toward overbought)
bool exit_warning_long = stoch_9_3 > i_exit_warning and stoch_9_3 <= i_exit_signal
bool exit_zone_long = stoch_9_3 > i_exit_signal

// Short exit zones (9-3 falling toward oversold)
bool exit_warning_short = stoch_9_3 < (100 - i_exit_warning) and stoch_9_3 >= (100 - i_exit_signal)
bool exit_zone_short = stoch_9_3 < (100 - i_exit_signal)

// Edge detection
bool exit_warning_long_trigger = exit_warning_long and not exit_warning_long[1]
bool exit_zone_long_trigger = exit_zone_long and not exit_zone_long[1]
bool exit_warning_short_trigger = exit_warning_short and not exit_warning_short[1]
bool exit_zone_short_trigger = exit_zone_short and not exit_zone_short[1]
```

---

## PLOTTING

```pinescript
// ============================================================================
// VISIBLE PLOTS
// ============================================================================

plot(i_show_9_3 ? stoch_9_3 : na, "9-3", color=color.orange, linewidth=2)
plot(i_show_14_3 ? stoch_14_3 : na, "14-3", color=color.yellow, linewidth=1)
plot(i_show_40_4 ? stoch_40_4 : na, "40-4", color=color.blue, linewidth=1)
plot(i_show_60_10 ? stoch_60_10 : na, "60-10", color=color.purple, linewidth=1)

// Reference lines
hline(80, "Overbought", color=color.red, linestyle=hline.style_dashed)
hline(70, "Near OB", color=color.orange, linestyle=hline.style_dotted)
hline(50, "Midline", color=color.gray, linestyle=hline.style_solid)
hline(30, "Near OS", color=color.teal, linestyle=hline.style_dotted)
hline(20, "Oversold", color=color.green, linestyle=hline.style_dashed)

// Warmup indicator
bgcolor(not is_warmed_up ? color.new(color.gray, 95) : na)

// ============================================================================
// HIDDEN PLOTS (for JSON alerts / integration)
// ============================================================================

plot(stoch_9_3, "stoch_9_3", display=display.none)
plot(stoch_14_3, "stoch_14_3", display=display.none)
plot(stoch_40_4, "stoch_40_4", display=display.none)
plot(stoch_60_10, "stoch_60_10", display=display.none)

// Context as numeric for JSON
plot(stoch_60_10_bullish ? (stoch_60_10_up ? 2 : 1) : (stoch_60_10_down ? -2 : -1), "channel_numeric", display=display.none)
plot(stoch_40_4_bullish ? 1 : -1, "mid_numeric", display=display.none)
plot(was_oversold ? -2 : was_near_oversold ? -1 : was_overbought ? 2 : was_near_overbought ? 1 : 0, "zone_numeric", display=display.none)

// ============================================================================
// SIGNAL MARKERS
// ============================================================================

// FULL signals (highest quality)
plotshape(fast_full_long_trigger, "FULL LONG", shape.labelup, location.bottom,
    color=color.lime, size=size.normal, text="FULL")
plotshape(fast_full_short_trigger, "FULL SHORT", shape.labeldown, location.top,
    color=color.fuchsia, size=size.normal, text="FULL")

// CONFIRMED signals
plotshape(fast_confirmed_long_trigger and not fast_full_long_trigger, "CONF LONG", shape.triangleup, location.bottom,
    color=color.green, size=size.small, text="CONF")
plotshape(fast_confirmed_short_trigger and not fast_full_short_trigger, "CONF SHORT", shape.triangledown, location.top,
    color=color.red, size=size.small, text="CONF")

// ROTATION signals (lowest tier from strict zone)
plotshape(fast_rotation_long_trigger and not fast_confirmed_long_trigger, "ROT LONG", shape.circle, location.bottom,
    color=color.teal, size=size.tiny)
plotshape(fast_rotation_short_trigger and not fast_confirmed_short_trigger, "ROT SHORT", shape.circle, location.top,
    color=color.maroon, size=size.tiny)

// NEAR zone signals (lower confidence)
plotshape(fast_near_long_trigger, "NEAR LONG", shape.diamond, location.bottom,
    color=color.new(color.green, 50), size=size.tiny, text="N")
plotshape(fast_near_short_trigger, "NEAR SHORT", shape.diamond, location.top,
    color=color.new(color.red, 50), size=size.tiny, text="N")

// Exit markers
plotshape(exit_warning_long_trigger, "Exit Warn L", shape.xcross, location.top,
    color=color.orange, size=size.tiny)
plotshape(exit_zone_long_trigger, "Exit Zone L", shape.square, location.top,
    color=color.red, size=size.small, text="TP")
plotshape(exit_warning_short_trigger, "Exit Warn S", shape.xcross, location.bottom,
    color=color.orange, size=size.tiny)
plotshape(exit_zone_short_trigger, "Exit Zone S", shape.square, location.bottom,
    color=color.green, size=size.small, text="TP")
```

---

## ALERTS

### Entry Signals (Tiered)
```pinescript
// FULL (all 4 rotating)
alertcondition(fast_full_long_trigger, "FAST FULL LONG", 
    "All 4 stochastics rotating up from oversold - HIGHEST QUALITY")
alertcondition(fast_full_short_trigger, "FAST FULL SHORT", 
    "All 4 stochastics rotating down from overbought - HIGHEST QUALITY")

// CONFIRMED (9-3 + 14-3)
alertcondition(fast_confirmed_long_trigger, "FAST CONFIRMED LONG", 
    "9-3 + 14-3 rotating up from oversold")
alertcondition(fast_confirmed_short_trigger, "FAST CONFIRMED SHORT", 
    "9-3 + 14-3 rotating down from overbought")

// ROTATION (9-3 only)
alertcondition(fast_rotation_long_trigger, "FAST ROTATION LONG", 
    "9-3 rotating up from oversold")
alertcondition(fast_rotation_short_trigger, "FAST ROTATION SHORT", 
    "9-3 rotating down from overbought")

// NEAR zone (lower confidence)
alertcondition(fast_near_long_trigger, "FAST NEAR LONG", 
    "9-3 + 14-3 rotating from near-oversold - LOWER CONFIDENCE")
alertcondition(fast_near_short_trigger, "FAST NEAR SHORT", 
    "9-3 + 14-3 rotating from near-overbought - LOWER CONFIDENCE")
```

### Exit Alerts
```pinescript
alertcondition(exit_warning_long_trigger, "9-3 Exit Warning Long", 
    "9-3 approaching overbought - prepare to take profit")
alertcondition(exit_zone_long_trigger, "9-3 Exit Zone Long", 
    "9-3 in overbought zone - take profit area")
alertcondition(exit_warning_short_trigger, "9-3 Exit Warning Short", 
    "9-3 approaching oversold - prepare to take profit")
alertcondition(exit_zone_short_trigger, "9-3 Exit Zone Short", 
    "9-3 in oversold zone - take profit area")
```

---

## JSON ALERT PAYLOAD

```json
{
  "ticker": "{{ticker}}",
  "timeframe": "{{interval}}",
  "timestamp": "{{time}}",
  "close": {{close}},
  "signal": "FAST_CONFIRMED_LONG",
  "stochastics": {
    "9_3": {{plot("stoch_9_3")}},
    "14_3": {{plot("stoch_14_3")}},
    "40_4": {{plot("stoch_40_4")}},
    "60_10": {{plot("stoch_60_10")}}
  },
  "context": {
    "zone": {{plot("zone_numeric")}},
    "channel": {{plot("channel_numeric")}},
    "mid": {{plot("mid_numeric")}}
  }
}
```

**Context Decoding:**
- zone: -2=oversold, -1=near_oversold, 0=neutral, 1=near_overbought, 2=overbought
- channel: -2=bearish_falling, -1=bearish_rising, 1=bullish_falling, 2=bullish_rising
- mid: -1=bearish, 1=bullish

---

## SIGNAL MATRIX

| Signal | Zone | 9-3 | 14-3 | 40-4 | 60-10 | Confidence |
|--------|------|-----|------|------|-------|------------|
| FAST FULL | strict | ✅ rotating | ✅ same dir | ✅ same dir | ✅ same dir | HIGHEST |
| FAST CONFIRMED | strict | ✅ rotating | ✅ same dir | - | - | HIGH |
| FAST ROTATION | strict | ✅ rotating | - | - | - | MEDIUM |
| FAST NEAR | near | ✅ rotating | ✅ same dir | - | - | LOW |

---

## INTEGRATION GUIDE

**n8n Workflow Logic:**
```
IF FAST signal received:
  CHECK Ripster cloud color
    IF bullish AND signal = LONG → PROCEED
    IF bearish AND signal = SHORT → PROCEED
    ELSE → REJECT (counter-trend)
  
  CHECK VWAP position
    IF price > VWAP AND signal = LONG → CONFIRM
    IF price < VWAP AND signal = SHORT → CONFIRM
    ELSE → REDUCE SIZE
  
  CHECK BBWP state
    IF squeeze → WAIT or SMALL SIZE
    IF expanding → FULL SIZE
  
  EXECUTE with position size based on signal tier
```

**Position Sizing by Signal:**
| Signal Tier | Base Size |
|-------------|-----------|
| FAST FULL | 100% |
| FAST CONFIRMED | 75% |
| FAST ROTATION | 50% |
| FAST NEAR | 25% (scalp) |

---

## TESTING CHECKLIST

### Zone Detection
- [ ] Strict oversold (<20) detected correctly
- [ ] Near oversold (<30 but >20) detected correctly
- [ ] Zone memory works over 3 bars
- [ ] Zone state output correct for JSON

### Rotation Detection
- [ ] 9-3 requires 2 consecutive bars same direction
- [ ] 14-3 requires 1 bar same direction
- [ ] Full rotation requires all 4 moving together
- [ ] Context outputs correct for 40-4 and 60-10

### Signal Generation
- [ ] Signals tier correctly (FULL > CONFIRMED > ROTATION > NEAR)
- [ ] Edge detection fires once per signal
- [ ] Cooldown prevents rapid re-entry
- [ ] Near zone signals only fire when NOT in strict zone

### Exit Zones
- [ ] Warning at 70 (long) / 30 (short)
- [ ] Exit zone at 80 (long) / 20 (short)
- [ ] Edge detection works

### Integration
- [ ] All hidden plots output correctly
- [ ] JSON payload populates
- [ ] Context values decode correctly

---

## VERSION HISTORY

**v1.3 (2026-02-04) - Integration Focused**
- ❌ REMOVED: Trend filter (external handles)
- ❌ REMOVED: Channel as filter (now output only)
- ❌ REMOVED: Counter-trend logic (external handles)
- ✅ ADDED: Near zone detection (30/70)
- ✅ ADDED: Signal cooldown (5 bars)
- ✅ CHANGED: 14-3 confirmation to single bar
- ✅ CHANGED: 3-tier hierarchy (rotation quality)
- ✅ ADDED: Context outputs for integration

**v1.2 (2026-02-04) - Philosophy Corrected**
- Channel as mandatory filter
- Trend filter built-in
- Counter-trend exits

**v1.1 (2026-02-03) - Initial Build**
- Basic zone + turn detection

---

**STATUS: READY FOR CLAUDE CODE BUILD (v1.3 - INTEGRATION FOCUSED)**
