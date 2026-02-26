# QUAD ROTATION STOCHASTIC FAST v1.2 - BUILD SPECIFICATION
**Version:** 1.2  
**Date:** 2026-02-04  
**Status:** READY FOR CLAUDE CODE BUILD  
**Methodology:** John Kurisko HPS - Fast Variant (Philosophy Corrected)  
**Based On:** Quad Rotation Stochastic v4.2 CORRECTED  
**Pine Script:** v6

---

## PHILOSOPHY CHANGES FROM v1.1

| # | Change | v1.1 | v1.2 |
|---|--------|------|------|
| 1 | Channel Respect | Optional `OR` context | **MANDATORY 60-10 filter** |
| 2 | Signal Type | Zone + turn | **Rotation FROM recent zone** |
| 3 | Trend Filter | None | **Required via 60-10 or external** |
| 4 | Exit Strategy | Same as v4 | **Earlier exits + Rule 2** |
| 5 | Super Definition | FAST + loose context | **FAST + channel + mid + zone** |
| 6 | 14-3 Role | Zone-based (40/60) | **Direction confirmation only** |
| 7 | Signal Hierarchy | Independent | **Context-dependent priority** |

---

## TRADING PHILOSOPHY (CORRECTED)

### John Kurisko HPS Rule Alignment

**Rule 2 Applied:**
> "The larger channel is represented by the 60-minute chart; the small moves inside the larger channel are represented by the 9-3 Stochastics. In a downtrending market, always sell your profits quicker."

- **60-10 = The Channel** → NEVER trade against it
- **9-3 = Small moves inside channel** → Entry timing only
- **Counter-trend = faster exit** → Tighter profit targets

### FAST vs v4 Philosophy

| Aspect | v4 (Conservative) | FAST (Aggressive) |
|--------|-------------------|-------------------|
| Primary Trigger | 40-4 divergence | 9-3 + 14-3 rotation |
| Entry Timing | Late (wait for alignment) | Early (rotation start) |
| Use Case | Reversals, exhaustion | Pullbacks, continuation |
| Channel Role | Context | **MANDATORY FILTER** |
| Exit Strategy | Management (raise stop) | **Take profit earlier** |

### When to Use FAST

| Market Condition | Use FAST? | Why |
|------------------|-----------|-----|
| Strong trend, price pulling back | ✅ YES | Core use case |
| 60-10 rising, 9-3 dipped to oversold | ✅ YES | Continuation setup |
| 60-10 falling, 9-3 bounced from oversold | ❌ NO | Counter-channel |
| After fresh divergence on 40-4 | ✅ YES | Entry timing for reversal |
| Chop (60-10 flat near 50) | ❌ NO | No clear channel |
| News spike / volatility | ❌ NO | False signals likely |

---

## SIGNAL HIERARCHY

| Signal Type | Requirements | Confidence | Position Size |
|-------------|--------------|------------|---------------|
| **FAST SUPER** | Rotation + Channel + Mid + Zone | HIGH | Full size |
| **FAST + DIV** | Rotation + Recent divergence | HIGH | Full size |
| **FAST Standard** | Rotation + Channel aligned | MEDIUM | 70% size |
| **FAST Raw** | Rotation only (no filters) | LOW | Scalp only |

---

## STOCHASTIC SETTINGS (Same as v4)

| Name | K | Smooth | Type | Role in FAST |
|------|---|--------|------|--------------|
| 9-3 | 9 | 3 | Fast | **PRIMARY TRIGGER** |
| 14-3 | 14 | 3 | Fast | **ROTATION CONFIRMATION** |
| 40-4 | 40 | 4 | Fast | Mid-context, divergence |
| 60-10 | 60 | 10 | Full (double) | **CHANNEL DIRECTION** |

---

## INPUTS

```pinescript
//@version=6
indicator("Quad Rotation Stochastic FAST v1.2", shorttitle="QRS-FAST", overlay=false)

// === CHANNEL SETTINGS (60-10) ===
i_channel_lookback = input.int(5, "Channel Lookback", minval=3, maxval=20, group="Channel",
    tooltip="Bars to determine 60-10 direction")
i_channel_bull_min = input.int(40, "Channel Bullish Min", minval=30, maxval=50, group="Channel",
    tooltip="60-10 must be above this for bullish channel")
i_channel_bear_max = input.int(60, "Channel Bearish Max", minval=50, maxval=70, group="Channel",
    tooltip="60-10 must be below this for bearish channel")

// === FAST SIGNAL SETTINGS ===
i_zone_memory = input.int(3, "Zone Memory Bars", minval=1, maxval=10, group="Fast Signal",
    tooltip="How many bars to remember recent zone visit")
i_9_3_oversold = input.int(20, "9-3 Oversold", minval=10, maxval=30, group="Fast Signal")
i_9_3_overbought = input.int(80, "9-3 Overbought", minval=70, maxval=90, group="Fast Signal")

// === MID-CONTEXT SETTINGS (40-4) ===
i_mid_level = input.int(50, "Mid-Context Level", minval=40, maxval=60, group="Mid-Context",
    tooltip="40-4 above/below this for context")

// === TREND FILTER ===
i_trend_filter = input.string("Auto", "Trend Filter Mode", 
    options=["Auto", "Bullish Only", "Bearish Only", "Off"], group="Trend",
    tooltip="Auto uses 60-10 direction. Manual overrides for known trend.")

// === EXIT SETTINGS (Rule 2) ===
i_exit_warning_long = input.int(70, "Long Exit Warning", minval=60, maxval=80, group="Exit",
    tooltip="9-3 level to warn approaching overbought")
i_exit_signal_long = input.int(80, "Long Exit Signal", minval=70, maxval=90, group="Exit",
    tooltip="9-3 level for take profit zone")
i_exit_warning_short = input.int(30, "Short Exit Warning", minval=20, maxval=40, group="Exit")
i_exit_signal_short = input.int(20, "Short Exit Signal", minval=10, maxval=30, group="Exit")
i_counter_trend_exit_long = input.int(60, "Counter-Trend Exit Long", minval=50, maxval=70, group="Exit",
    tooltip="Tighter exit when trading against channel (Rule 2)")
i_counter_trend_exit_short = input.int(40, "Counter-Trend Exit Short", minval=30, maxval=50, group="Exit")

// === DIVERGENCE CONTEXT (from v4) ===
i_div_context_bars = input.int(10, "Divergence Context Bars", minval=5, maxval=20, group="Divergence",
    tooltip="Bars after divergence to consider for FAST+DIV signal")

// === DISPLAY ===
i_show_9_3 = input.bool(true, "Show 9-3", group="Display")
i_show_14_3 = input.bool(false, "Show 14-3", group="Display")
i_show_40_4 = input.bool(false, "Show 40-4", group="Display")
i_show_60_10 = input.bool(false, "Show 60-10", group="Display")
i_show_channel_bg = input.bool(true, "Show Channel Background", group="Display")
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

// Warmup check (60-10 needs ~80 bars)
int WARMUP_BARS = 80
bool is_warmed_up = bar_index >= WARMUP_BARS
```

---

## COMPONENT 2: CHANNEL DETECTION (60-10 DIRECTION)

```pinescript
// ============================================================================
// CHANNEL DETECTION - 60-10 defines the larger move (Rule 2)
// NEVER trade against channel direction
// ============================================================================

// 60-10 direction over lookback period
float stoch_60_10_prev = nz(stoch_60_10[i_channel_lookback], 50)
bool stoch_60_10_rising = stoch_60_10 > stoch_60_10_prev
bool stoch_60_10_falling = stoch_60_10 < stoch_60_10_prev

// Channel state with level requirements
bool channel_bullish = stoch_60_10_rising and stoch_60_10 > i_channel_bull_min
bool channel_bearish = stoch_60_10_falling and stoch_60_10 < i_channel_bear_max
bool channel_neutral = not channel_bullish and not channel_bearish

// Track channel state for counter-trend detection
var bool was_channel_bullish = false
var bool was_channel_bearish = false

if channel_bullish
    was_channel_bullish := true
    was_channel_bearish := false
else if channel_bearish
    was_channel_bearish := true
    was_channel_bullish := false
```

---

## COMPONENT 3: FAST ROTATION DETECTION (REVISED)

```pinescript
// ============================================================================
// ZONE MEMORY - Was recently in extreme zone
// Signal comes from ROTATION OUT OF zone, not being IN zone
// ============================================================================

// Recent zone visits (within zone_memory bars)
bool was_oversold_recently = ta.lowest(stoch_9_3, i_zone_memory) < i_9_3_oversold
bool was_overbought_recently = ta.highest(stoch_9_3, i_zone_memory) > i_9_3_overbought

// ============================================================================
// ROTATION DETECTION - Current momentum direction
// Requires 2-bar confirmation (current AND previous bar moving same way)
// ============================================================================

// 9-3 rotation (primary)
bool stoch_9_3_rotating_up = stoch_9_3 > stoch_9_3[1] and stoch_9_3[1] > stoch_9_3[2]
bool stoch_9_3_rotating_down = stoch_9_3 < stoch_9_3[1] and stoch_9_3[1] < stoch_9_3[2]

// 14-3 confirmation (must be moving same direction)
bool stoch_14_3_confirming_up = stoch_14_3 > stoch_14_3[1] and stoch_14_3[1] > stoch_14_3[2]
bool stoch_14_3_confirming_down = stoch_14_3 < stoch_14_3[1] and stoch_14_3[1] < stoch_14_3[2]

// ============================================================================
// FAST ROTATION SIGNAL = Zone memory + Both stochs rotating
// ============================================================================

bool fast_rotation_long = was_oversold_recently and 
                          stoch_9_3_rotating_up and 
                          stoch_14_3_confirming_up

bool fast_rotation_short = was_overbought_recently and 
                           stoch_9_3_rotating_down and 
                           stoch_14_3_confirming_down
```

---

## COMPONENT 4: TREND FILTER (NEW)

```pinescript
// ============================================================================
// TREND FILTER - Respects channel direction
// Auto mode uses 60-10, Manual allows override
// ============================================================================

// Auto trend from 60-10
bool auto_trend_bullish = channel_bullish
bool auto_trend_bearish = channel_bearish

// Apply filter based on mode
bool trend_allows_long = switch i_trend_filter
    "Auto" => auto_trend_bullish or channel_neutral
    "Bullish Only" => true
    "Bearish Only" => false
    "Off" => true
    => true

bool trend_allows_short = switch i_trend_filter
    "Auto" => auto_trend_bearish or channel_neutral
    "Bullish Only" => false
    "Bearish Only" => true
    "Off" => true
    => true

// Counter-trend detection (for Rule 2 exit adjustment)
bool is_counter_trend_long = fast_rotation_long and not channel_bullish
bool is_counter_trend_short = fast_rotation_short and not channel_bearish
```

---

## COMPONENT 5: MID-CONTEXT (40-4)

```pinescript
// ============================================================================
// MID-CONTEXT - 40-4 provides intermediate momentum context
// ============================================================================

bool mid_context_bullish = stoch_40_4 > i_mid_level
bool mid_context_bearish = stoch_40_4 < i_mid_level

// 40-4 rotation (for additional confirmation)
bool stoch_40_4_rising = stoch_40_4 > stoch_40_4[3]
bool stoch_40_4_falling = stoch_40_4 < stoch_40_4[3]
```

---

## COMPONENT 6: EXIT STRATEGY (FAST-SPECIFIC, RULE 2)

```pinescript
// ============================================================================
// EXIT STRATEGY - Earlier exits for FAST entries
// Rule 2: "In a downtrending market, always sell your profits quicker"
// ============================================================================

// Standard exits (9-3 approaching/hitting opposite zone)
bool exit_warning_long = stoch_9_3 > i_exit_warning_long
bool exit_signal_long = stoch_9_3 > i_exit_signal_long
bool exit_warning_short = stoch_9_3 < i_exit_warning_short
bool exit_signal_short = stoch_9_3 < i_exit_signal_short

// Counter-trend tighter exits (Rule 2)
bool tight_exit_long = is_counter_trend_long and stoch_9_3 > i_counter_trend_exit_long
bool tight_exit_short = is_counter_trend_short and stoch_9_3 < i_counter_trend_exit_short

// Combined exit signals
bool fast_exit_long = exit_signal_long or tight_exit_long
bool fast_exit_short = exit_signal_short or tight_exit_short
```

---

## COMPONENT 7: DIVERGENCE CONTEXT (FROM v4)

```pinescript
// ============================================================================
// DIVERGENCE CONTEXT - Tracks recent divergence for FAST+DIV signal
// Divergence detection is in v4, here we just track timing
// ============================================================================

// External input or calculated (if combining with v4)
var int bars_since_bull_div = 999
var int bars_since_bear_div = 999

// For standalone FAST, use input or set to 999 (no div context)
// If integrated with v4, these would be calculated

// Divergence context active (recent divergence enhances FAST signal)
bool div_context_bullish = bars_since_bull_div <= i_div_context_bars
bool div_context_bearish = bars_since_bear_div <= i_div_context_bars
```

---

## COMPONENT 8: SIGNAL GENERATION

```pinescript
// ============================================================================
// FAST SIGNALS - Layered by confidence
// ============================================================================

// RAW = Rotation only (lowest confidence)
bool fast_raw_long = fast_rotation_long
bool fast_raw_short = fast_rotation_short

// STANDARD = Rotation + Trend filter (medium confidence)
bool fast_std_long = fast_rotation_long and trend_allows_long
bool fast_std_short = fast_rotation_short and trend_allows_short

// SUPER = Rotation + Channel + Mid-context + Zone (high confidence)
bool fast_super_long = fast_rotation_long and 
                       channel_bullish and 
                       mid_context_bullish and 
                       was_oversold_recently

bool fast_super_short = fast_rotation_short and 
                        channel_bearish and 
                        mid_context_bearish and 
                        was_overbought_recently

// WITH DIVERGENCE = FAST + Recent divergence context (highest confidence)
bool fast_div_long = fast_std_long and div_context_bullish
bool fast_div_short = fast_std_short and div_context_bearish

// ============================================================================
// EDGE DETECTION - Fire once per signal
// ============================================================================

bool fast_raw_long_trigger = fast_raw_long and not fast_raw_long[1]
bool fast_raw_short_trigger = fast_raw_short and not fast_raw_short[1]

bool fast_std_long_trigger = fast_std_long and not fast_std_long[1]
bool fast_std_short_trigger = fast_std_short and not fast_std_short[1]

bool fast_super_long_trigger = fast_super_long and not fast_super_long[1]
bool fast_super_short_trigger = fast_super_short and not fast_super_short[1]

bool fast_div_long_trigger = fast_div_long and not fast_div_long[1]
bool fast_div_short_trigger = fast_div_short and not fast_div_short[1]

// Exit triggers (edge)
bool exit_warning_long_trigger = exit_warning_long and not exit_warning_long[1]
bool exit_warning_short_trigger = exit_warning_short and not exit_warning_short[1]
bool fast_exit_long_trigger = fast_exit_long and not fast_exit_long[1]
bool fast_exit_short_trigger = fast_exit_short and not fast_exit_short[1]
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
hline(60, "Upper Mid", color=color.gray, linestyle=hline.style_dotted)
hline(50, "Midline", color=color.gray, linestyle=hline.style_solid)
hline(40, "Lower Mid", color=color.gray, linestyle=hline.style_dotted)
hline(20, "Oversold", color=color.green, linestyle=hline.style_dashed)

// ============================================================================
// CHANNEL BACKGROUND (shows 60-10 direction)
// ============================================================================

bgcolor(i_show_channel_bg and channel_bullish ? color.new(color.green, 95) : na)
bgcolor(i_show_channel_bg and channel_bearish ? color.new(color.red, 95) : na)

// Warmup indicator
bgcolor(not is_warmed_up ? color.new(color.gray, 95) : na)

// ============================================================================
// HIDDEN PLOTS (for JSON alerts)
// ============================================================================

plot(stoch_9_3, "stoch_9_3", display=display.none)
plot(stoch_14_3, "stoch_14_3", display=display.none)
plot(stoch_40_4, "stoch_40_4", display=display.none)
plot(stoch_60_10, "stoch_60_10", display=display.none)
plot(channel_bullish ? 1 : channel_bearish ? -1 : 0, "channel_state", display=display.none)
plot(is_counter_trend_long ? 1 : is_counter_trend_short ? -1 : 0, "counter_trend", display=display.none)

// ============================================================================
// SIGNAL MARKERS
// ============================================================================

// SUPER signals (highest priority display)
plotshape(fast_super_long_trigger, "SUPER LONG", shape.labelup, location.bottom,
    color=color.lime, size=size.normal, text="SUPER")
plotshape(fast_super_short_trigger, "SUPER SHORT", shape.labeldown, location.top,
    color=color.fuchsia, size=size.normal, text="SUPER")

// FAST+DIV signals
plotshape(fast_div_long_trigger and not fast_super_long_trigger, "FAST+DIV LONG", shape.labelup, location.bottom,
    color=color.teal, size=size.normal, text="F+D")
plotshape(fast_div_short_trigger and not fast_super_short_trigger, "FAST+DIV SHORT", shape.labeldown, location.top,
    color=color.maroon, size=size.normal, text="F+D")

// Standard FAST signals (when not super or div)
plotshape(fast_std_long_trigger and not fast_super_long_trigger and not fast_div_long_trigger, 
    "FAST LONG", shape.triangleup, location.bottom,
    color=color.green, size=size.small, text="FAST")
plotshape(fast_std_short_trigger and not fast_super_short_trigger and not fast_div_short_trigger, 
    "FAST SHORT", shape.triangledown, location.top,
    color=color.red, size=size.small, text="FAST")

// Exit markers
plotshape(exit_warning_long_trigger, "Exit Warn Long", shape.xcross, location.top,
    color=color.orange, size=size.tiny)
plotshape(exit_warning_short_trigger, "Exit Warn Short", shape.xcross, location.bottom,
    color=color.orange, size=size.tiny)
plotshape(fast_exit_long_trigger, "Exit Long", shape.square, location.top,
    color=color.red, size=size.small, text="EXIT")
plotshape(fast_exit_short_trigger, "Exit Short", shape.square, location.bottom,
    color=color.green, size=size.small, text="EXIT")

// Counter-trend warning (background flash)
bgcolor(is_counter_trend_long and fast_std_long ? color.new(color.orange, 90) : na)
bgcolor(is_counter_trend_short and fast_std_short ? color.new(color.orange, 90) : na)
```

---

## ALERTS

### FAST Entry Alerts (Tiered)
```pinescript
// SUPER (highest confidence)
alertcondition(fast_super_long_trigger, "FAST SUPER LONG", 
    "Rotation + Channel + Mid-context aligned - HIGH CONFIDENCE")
alertcondition(fast_super_short_trigger, "FAST SUPER SHORT", 
    "Rotation + Channel + Mid-context aligned - HIGH CONFIDENCE")

// FAST + Divergence context
alertcondition(fast_div_long_trigger, "FAST+DIV LONG", 
    "Rotation + Recent bullish divergence - HIGH CONFIDENCE")
alertcondition(fast_div_short_trigger, "FAST+DIV SHORT", 
    "Rotation + Recent bearish divergence - HIGH CONFIDENCE")

// Standard FAST
alertcondition(fast_std_long_trigger, "FAST LONG", 
    "9-3 + 14-3 rotation from oversold - MEDIUM CONFIDENCE")
alertcondition(fast_std_short_trigger, "FAST SHORT", 
    "9-3 + 14-3 rotation from overbought - MEDIUM CONFIDENCE")

// Raw FAST (scalp only)
alertcondition(fast_raw_long_trigger, "FAST RAW LONG", 
    "Rotation only, no filter - LOW CONFIDENCE / SCALP")
alertcondition(fast_raw_short_trigger, "FAST RAW SHORT", 
    "Rotation only, no filter - LOW CONFIDENCE / SCALP")
```

### Exit Alerts (Rule 2 aware)
```pinescript
// Warning (approaching zone)
alertcondition(exit_warning_long_trigger, "Exit Warning Long", 
    "9-3 approaching overbought - prepare to take profit")
alertcondition(exit_warning_short_trigger, "Exit Warning Short", 
    "9-3 approaching oversold - prepare to take profit")

// Exit signal
alertcondition(fast_exit_long_trigger, "FAST Exit Long", 
    "Take profit zone reached or counter-trend tight exit")
alertcondition(fast_exit_short_trigger, "FAST Exit Short", 
    "Take profit zone reached or counter-trend tight exit")
```

### Channel State Alerts
```pinescript
alertcondition(channel_bullish and not channel_bullish[1], "Channel Bullish", 
    "60-10 rising above threshold - LONGS favored")
alertcondition(channel_bearish and not channel_bearish[1], "Channel Bearish", 
    "60-10 falling below threshold - SHORTS favored")
alertcondition(channel_neutral and not channel_neutral[1], "Channel Neutral", 
    "60-10 direction unclear - CAUTION")
```

### Counter-Trend Warning
```pinescript
alertcondition(is_counter_trend_long and fast_std_long_trigger, "Counter-Trend Long Warning", 
    "FAST LONG against bearish channel - USE TIGHT EXIT (Rule 2)")
alertcondition(is_counter_trend_short and fast_std_short_trigger, "Counter-Trend Short Warning", 
    "FAST SHORT against bullish channel - USE TIGHT EXIT (Rule 2)")
```

---

## JSON ALERT PAYLOAD

```json
{
  "ticker": "{{ticker}}",
  "timeframe": "{{interval}}",
  "timestamp": "{{time}}",
  "close": {{close}},
  "signal": "FAST_SUPER_LONG",
  "confidence": "HIGH",
  "stochastics": {
    "9_3": {{plot("stoch_9_3")}},
    "14_3": {{plot("stoch_14_3")}},
    "40_4": {{plot("stoch_40_4")}},
    "60_10": {{plot("stoch_60_10")}}
  },
  "context": {
    "channel": {{plot("channel_state")}},
    "counter_trend": {{plot("counter_trend")}}
  }
}
```

---

## TESTING CHECKLIST

### Channel Detection
- [ ] 60-10 rising + above 40 = channel bullish
- [ ] 60-10 falling + below 60 = channel bearish
- [ ] Neither = channel neutral
- [ ] Background colors reflect channel state

### Rotation Detection
- [ ] Zone memory works (3-bar lookback)
- [ ] 9-3 rotation requires 2-bar momentum
- [ ] 14-3 confirmation requires same direction
- [ ] Signal fires on rotation START, not while in zone

### Trend Filter
- [ ] Auto mode respects channel
- [ ] Manual overrides work
- [ ] Counter-trend detection accurate

### Exit Strategy
- [ ] Warning fires at 70/30
- [ ] Exit fires at 80/20
- [ ] Counter-trend tight exit fires at 60/40
- [ ] Rule 2: faster exit when against channel

### Signal Hierarchy
- [ ] SUPER requires all conditions
- [ ] FAST+DIV requires divergence context
- [ ] Standard requires trend filter only
- [ ] Raw has no filters
- [ ] Edge detection prevents repeats

### Alerts
- [ ] All edge-triggered
- [ ] JSON payload populates
- [ ] Counter-trend warning fires

---

## DIFFERENCES FROM v4.2

| Aspect | v4.2 | FAST v1.2 |
|--------|------|-----------|
| Primary trigger | 40-4 divergence | 9-3 + 14-3 rotation |
| Channel role | Context only | **MANDATORY filter** |
| 14-3 role | Part of alignment count | **Rotation confirmation** |
| Exit strategy | Management (raise stop) | **Take profit + Rule 2** |
| Super definition | Div + 3/4 alignment | Rotation + Channel + Mid + Zone |
| Default display | 40-4 only | 9-3 + channel background |
| Counter-trend | Not tracked | **Warned + tight exit** |
| Signal tiers | 2 (standard, super) | **4 (raw, std, super, +div)** |

---

## EXTERNAL DEPENDENCIES

| Feature | Source | Integration |
|---------|--------|-------------|
| Ripster trend | Ripster EMA Clouds | Use `i_trend_filter` manual mode |
| Divergence context | v4.2 indicator | Share `bars_since_bull_div` var |
| VWAP position | AVWAP indicator | Not in this build |
| ATR stop | ATR indicator | Not in this build |

---

## VERSION HISTORY

**v1.2 (2026-02-04) - Philosophy Corrected**
- ✅ Channel as MANDATORY filter (Rule 2)
- ✅ Rotation from zone, not in zone
- ✅ Trend filter with auto/manual modes
- ✅ FAST-specific exit strategy (earlier)
- ✅ Rule 2: counter-trend tight exits
- ✅ 14-3 as rotation confirmation (not zone)
- ✅ 4-tier signal hierarchy
- ✅ Counter-trend detection and warning

**v1.1 (2026-02-03) - Initial Build**
- Basic 9-3 + 14-3 zone detection
- Loose context filter

---

**STATUS: READY FOR CLAUDE CODE BUILD (v1.2 - PHILOSOPHY CORRECTED)**
