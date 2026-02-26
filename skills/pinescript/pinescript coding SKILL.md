---
name: pinescript
description: Comprehensive Pine Script v6 development skill for TradingView indicators and strategies. Use when creating indicators, strategies, alerts, or any TradingView Pine Script code. Triggers on terms like "pine script", "pinescript", "tradingview", "indicator", "strategy", "alert", "v6", "EMA", "VWAP", "stochastic", "divergence", "volume profile", "market profile", "webhook", "four pillars", "quad rotation", "ripster", "AVWAP", "BBWP". Covers complete v6 syntax, execution model, type system, UDTs, methods, arrays, matrices, maps, alert/webhook integration for n8n automation, and professional trading indicator patterns including Ripster EMA Clouds, Anchored VWAP (Brian Shannon methodology), Multi-Stochastic systems (Quad Rotation), and Volume/Market Profile concepts (Dalton).
---

# Pine Script v6 + Trading Technical Analysis Skill

## Quick Reference

### Script Declaration
```pinescript
//@version=6
indicator("Name", shorttitle="Short", overlay=true/false)
// OR
strategy("Name", overlay=true, margin_long=100, margin_short=100, 
         initial_capital=10000, default_qty_type=strategy.percent_of_equity, 
         default_qty_value=100, commission_type=strategy.commission.percent, 
         commission_value=0.1)
```

### v6 Critical Changes from v5
1. **No implicit bool casting**: `if bar_index` → `if bar_index != 0`
2. **Dynamic requests default ON**: `request.security()` works in local scopes
3. **`when` parameter removed**: Use `if` conditions instead
4. **Division returns float**: `5/2` = 2.5, use `int(5/2)` for integer
5. **Default margin 100%**: Explicitly set if different needed
6. **`na` not valid bool**: Use `false` or explicit checks

### Type System Qualifiers
| Qualifier | When Set | Can Change? |
|-----------|----------|-------------|
| const | Compile time | Never |
| input | Input time | Never (requires reload) |
| simple | Bar 0 | Never after bar 0 |
| series | Each bar | Yes, every bar |

### Core Built-in Variables
```pinescript
// Price data
open, high, low, close, volume, time, bar_index

// Bar states
barstate.ishistory, barstate.isrealtime, barstate.islast
barstate.isconfirmed, barstate.isnew

// Symbol info
syminfo.ticker, syminfo.tickerid, syminfo.currency
syminfo.mintick, syminfo.pointvalue

// Time
time_close, timenow, dayofweek, hour, minute
```

---

## Execution Model

Scripts execute sequentially on each bar. Key concepts:

1. **Historical bars**: Execute once per bar at close
2. **Realtime bars**: Execute on each tick (indicators) or bar close (strategies)
3. **History reference**: `close[1]` = previous bar's close
4. **Persistence**: Use `var` for values that persist across bars

```pinescript
// var persists value across bars
var float highestHigh = 0.0
highestHigh := math.max(highestHigh, high)

// Without var, resets each bar
float tempValue = 0.0  // Resets to 0 every bar
```

---

## Input Functions

```pinescript
// Basic inputs
i_length = input.int(14, "Length", minval=1, maxval=200)
i_source = input.source(close, "Source")
i_mult = input.float(2.0, "Multiplier", step=0.1)
i_show = input.bool(true, "Show Indicator")
i_color = input.color(color.blue, "Color")

// Dropdown
i_maType = input.string("EMA", "MA Type", options=["SMA", "EMA", "WMA", "VWMA"])

// Grouped inputs
i_fastLen = input.int(9, "Fast Length", group="Stochastic Settings")
i_slowLen = input.int(60, "Slow Length", group="Stochastic Settings")

// Timeframe input
i_tf = input.timeframe("D", "Higher Timeframe")

// With tooltip
i_lookback = input.int(5, "Lookback", minval=3, maxval=20, group="Settings",
    tooltip="Bars to look back for calculation")
```

---

## Common Calculations

### Moving Averages
```pinescript
ema_fast = ta.ema(close, 9)
ema_slow = ta.ema(close, 21)
sma_value = ta.sma(close, 20)
wma_value = ta.wma(close, 14)
vwma_value = ta.vwma(close, 20)

// Custom MA selector
getMA(src, len, maType) =>
    switch maType
        "SMA" => ta.sma(src, len)
        "EMA" => ta.ema(src, len)
        "WMA" => ta.wma(src, len)
        "VWMA" => ta.vwma(src, len)
        => ta.ema(src, len)
```

### Stochastic - CRITICAL: Fast vs Full

**John Kurisko Settings:**
| Name | K | Smooth | Type | Role |
|------|---|--------|------|------|
| 9-3 | 9 | 3 | Fast | Entry timing |
| 14-3 | 14 | 3 | Fast | Confirmation |
| 40-4 | 40 | 3 | Fast | Primary divergence |
| 60-10 | 60 | 10 | Full | Macro filter |

```pinescript
// ============================================================================
// FAST STOCHASTIC - Single smoothing
// Used for: 9-3, 14-3, 40-4
// ============================================================================
stoch_fast(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k = ta.sma(k_raw, smooth_k)  // SINGLE smooth
    k

// ============================================================================
// FULL STOCHASTIC - Double smoothing
// Used for: 60-10
// ============================================================================
stoch_full(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k_smooth1 = ta.sma(k_raw, smooth_k)
    float k_full = ta.sma(k_smooth1, smooth_k)  // DOUBLE smooth
    k_full

// Calculate all 4
float stoch_9_3  = stoch_fast(9, 3)
float stoch_14_3 = stoch_fast(14, 3)
float stoch_40_4 = stoch_fast(40, 3)
float stoch_60_10 = stoch_full(60, 10)
```

### RSI
```pinescript
rsi_value = ta.rsi(close, 14)
```

### VWAP
```pinescript
vwap_value = ta.vwap(hlc3)

// Anchored VWAP - see references/technical-analysis.md
```

### Bollinger Bands
```pinescript
[middle, upper, lower] = ta.bb(close, 20, 2.0)
bbw = (upper - lower) / middle  // Band width
```

### ATR
```pinescript
atr_value = ta.atr(14)
```

---

## State Machine Pattern (Divergence Detection)

**CRITICAL: Use if/else if chains to prevent multiple blocks executing on same bar.**

```pinescript
// ============================================================================
// STATE MACHINE FOR DIVERGENCE DETECTION
// States: 0=waiting, 1=in_zone, 2=exited_zone
// ============================================================================
var int bull_state = 0
var float bull_stage1_price = na
var float bull_stage1_stoch = na  // Store stoch AT the price, not min/max
var int bull_stage1_bar = na

bool bullish_divergence = false

// CRITICAL: if/else if chain prevents multiple execution
if bull_state == 0 and stoch_40_4 < 20
    // State 0 → 1: Enter oversold
    bull_state := 1
    bull_stage1_price := low
    bull_stage1_stoch := stoch_40_4  // Stoch AT this low
    bull_stage1_bar := bar_index

else if bull_state == 1 and stoch_40_4 < 20
    // State 1: Track lowest price while in oversold
    if low < bull_stage1_price
        bull_stage1_price := low
        bull_stage1_stoch := stoch_40_4  // Stoch AT new low

else if bull_state == 1 and stoch_40_4 >= 20
    // State 1 → 2: Exit oversold (bounce)
    bull_state := 2

else if bull_state == 2
    if stoch_40_4 < 20
        // Reset: re-entered oversold
        bull_state := 1
        bull_stage1_price := low
        bull_stage1_stoch := stoch_40_4
        bull_stage1_bar := bar_index
    else if bar_index - bull_stage1_bar > 20  // Lookback exceeded
        bull_state := 0
    else
        // Check divergence: price lower/equal, stoch higher
        bool price_lower = low <= bull_stage1_price * 1.001  // 0.1% threshold
        bool stoch_higher = stoch_40_4 > bull_stage1_stoch
        bool turning_up = stoch_40_4 > stoch_40_4[1]
        
        if price_lower and stoch_higher and turning_up
            bullish_divergence := true
            bull_state := 0
```

---

## Edge Detection for Alerts - CRITICAL

**All alerts must fire ONCE when condition becomes true, not every bar while true.**

```pinescript
// ============================================================================
// EDGE DETECTION - Simple [1] method (preferred)
// ============================================================================
bool signal_trigger = signal_condition and not signal_condition[1]

// Example with alignment
bool full_bull = bull_count == 4
bool full_bull_trigger = full_bull and not full_bull[1]  // Fires ONCE

alertcondition(full_bull_trigger, "Full Bullish", "All 4 stochastics above 60")
```

**For signals that persist (supersignals):**
```pinescript
// Track bars since divergence for timing alignment
var int bars_since_div = 100

if bullish_divergence
    bars_since_div := 0
else
    bars_since_div := bars_since_div + 1

// Divergence active within N bars
bool div_active = bars_since_div <= 5

// Supersignal = recent divergence + current alignment
bool supersignal = div_active and bull_count >= 3
bool supersignal_trigger = supersignal and not supersignal[1]
```

---

## Turn Detection (Fast Indicators)

**CRITICAL: Must combine lookback AND current bar momentum.**

```pinescript
// ============================================================================
// TURN DETECTION - Prevents false signals
// ============================================================================
int i_lookback = 3  // Configurable 3-20

// WRONG: Only checks if higher than lookback
// bool turning_up = stoch > stoch[i_lookback]  // Can be true while still falling!

// CORRECT: Higher than lookback AND currently rising
bool turning_up = stoch > nz(stoch[i_lookback], 50) and stoch > stoch[1]
bool turning_down = stoch < nz(stoch[i_lookback], 50) and stoch < stoch[1]
```

---

## Plotting

```pinescript
// Basic plot
plot(ema_fast, "Fast EMA", color.blue, 2)

// Conditional color
plot(close, color = close > open ? color.green : color.red)

// Fill between plots
p1 = plot(upper, "Upper")
p2 = plot(lower, "Lower")
fill(p1, p2, color.new(color.blue, 90))

// Shapes - edge triggered
plotshape(buySignal and not buySignal[1], "Buy", shape.triangleup, location.belowbar, 
    color.green, size=size.small, text="BUY")

// Background
bgcolor(bullish ? color.new(color.green, 90) : na)

// Horizontal lines
hline(80, "Overbought", color.red, hline.style_dashed)
hline(50, "Mid", color.gray, hline.style_dotted)
hline(20, "Oversold", color.green, hline.style_dashed)

// ============================================================================
// HIDDEN PLOTS FOR JSON ALERTS
// ============================================================================
plot(stoch_9_3, "stoch_9_3", display=display.none)
plot(stoch_14_3, "stoch_14_3", display=display.none)
plot(stoch_40_4, "stoch_40_4", display=display.none)
plot(stoch_60_10, "stoch_60_10", display=display.none)
plot(quad_angle, "quad_angle", display=display.none)
```

---

## Alert System

### alertcondition() - For Indicators
```pinescript
// CRITICAL: All alerts must be edge-triggered
alertcondition(signal and not signal[1], "Signal Name", "Description")

// Management alerts (raise stop, not close)
alertcondition(ta.crossover(stoch_9_3, 80), "Mgmt Long", "9-3 >80 - RAISE STOP")
```

### alert() Function
```pinescript
if buyCondition and not buyCondition[1]
    alert("BUY Signal: " + syminfo.ticker, alert.freq_once_per_bar_close)
```

### JSON Payload for n8n Webhooks
```json
{
  "ticker": "{{ticker}}",
  "timeframe": "{{interval}}",
  "timestamp": "{{time}}",
  "close": {{close}},
  "stochastics": {
    "9_3": {{plot("stoch_9_3")}},
    "14_3": {{plot("stoch_14_3")}},
    "40_4": {{plot("stoch_40_4")}},
    "60_10": {{plot("stoch_60_10")}}
  }
}
```

**NOTE:** `{{strategy.order.action}}` only works in STRATEGIES, not indicators!

---

## Strategy Functions

```pinescript
// Entry
strategy.entry("Long", strategy.long, qty=1, limit=limitPrice, stop=stopPrice)
strategy.entry("Short", strategy.short)

// Exit
strategy.close("Long")
strategy.close_all()

// Exit with TP/SL
strategy.exit("Exit Long", "Long", 
    profit=100,      // Ticks
    loss=50,         // Ticks  
    trail_points=20, 
    trail_offset=10)

// Or percentage-based
strategy.exit("Exit Long", "Long",
    limit=strategy.position_avg_price * 1.02,  // 2% TP
    stop=strategy.position_avg_price * 0.98)   // 2% SL

// Position info
strategy.position_size      // Current position (+ long, - short, 0 flat)
strategy.position_avg_price // Average entry price
strategy.opentrades         // Number of open trades
```

---

## Multi-Timeframe Data

```pinescript
// Request higher timeframe data
htf_close = request.security(syminfo.tickerid, "D", close)
htf_ema = request.security(syminfo.tickerid, "4H", ta.ema(close, 20))

// Prevent repainting
htf_close_safe = request.security(syminfo.tickerid, "D", close[1], barmerge.gaps_off, barmerge.lookahead_on)

// Dynamic requests (v6 default)
tf = i_higherTF
htf_data = request.security(syminfo.tickerid, tf, close)
```

---

## User-Defined Types (UDT)

```pinescript
type TradeSetup
    string direction
    float entryPrice
    float stopLoss
    float takeProfit
    int signalBar

// Create instance
setup = TradeSetup.new("long", close, close - atr, close + 2*atr, bar_index)

// Access fields
if setup.direction == "long"
    strategy.entry("Long", strategy.long)
```

---

## Arrays

```pinescript
// Create
var float[] prices = array.new_float()

// Add elements
array.push(prices, close)

// Maintain size
if array.size(prices) > 100
    array.shift(prices)

// Access
lastPrice = array.get(prices, array.size(prices) - 1)

// Statistics
avgPrice = array.avg(prices)
maxPrice = array.max(prices)
```

---

## Code Review Checklist

**Before finalizing any Pine Script, verify:**

### Syntax & Types
- [ ] All variables have explicit type declarations (`float`, `int`, `bool`)
- [ ] No typos in variable names (especially in state machines)
- [ ] `nz()` used for historical data access that might be `na`
- [ ] Boundary conditions handled (== 20, == 80, not just < or >)

### Logic Flow
- [ ] State machines use `if/else if` chains (not multiple `if` blocks)
- [ ] Edge detection on all alerts (`and not condition[1]`)
- [ ] Turn detection includes current bar momentum check
- [ ] No unused inputs or variables

### Alerts
- [ ] All alerts fire ONCE (edge-triggered)
- [ ] Hidden plots exist for all JSON payload values
- [ ] No `{{strategy.order.action}}` in indicators

### Edge Cases
- [ ] Flat market (range = 0) returns neutral value (50)
- [ ] First N bars handled with `nz()` fallbacks
- [ ] Gap opens handled correctly

---

## Common Patterns Quick Reference

### Crossover Detection
```pinescript
bullishCross = ta.crossover(ema_fast, ema_slow)
bearishCross = ta.crossunder(ema_fast, ema_slow)
```

### Session Filtering
```pinescript
inSession = not na(time(timeframe.period, "0930-1600", "America/New_York"))
```

### Trend Direction
```pinescript
uptrend = close > ta.ema(close, 200)
downtrend = close < ta.ema(close, 200)
```

### Angle Calculation (for rotation indicators)
```pinescript
// Use absolute change, not percentage (prevents extreme values)
float stoch_prev = nz(stoch[lookback], 50)
float stoch_change = (stoch - stoch_prev) / 100.0  // Normalize to 0-1
float angle = math.atan(stoch_change * 10) * (180.0 / math.pi)
```

---

## Debugging Tips

```pinescript
// Plot debug values
plot(debugValue, "Debug", display=display.data_window)

// Label for specific bar info
if barstate.islast
    label.new(bar_index, high, str.tostring(myValue))

// Pine Logs (v6)
log.info("Value: " + str.tostring(myValue))
log.warning("Warning message")
log.error("Error message")
```

---

## Performance Optimization

1. **Use `var` for persistent variables** - Avoid recalculating unchanged values
2. **Limit array sizes** - Use `array.shift()` to maintain max size
3. **Minimize request.security() calls** - Cache results when possible
4. **Use simple types when possible** - `const` and `input` are faster than `series`
5. **Profile with Pine Profiler** - Identify bottlenecks

---

## Integration with n8n Webhooks

Standard alert JSON format for n8n integration:
```json
{
  "exchange": "{{exchange}}",
  "ticker": "{{ticker}}",
  "action": "LONG",
  "price": {{close}},
  "time": "{{timenow}}",
  "position_size": 250,
  "leverage": 20,
  "secret": "your_webhook_secret"
}
```

See `references/alert-webhook-integration.md` for complete n8n workflow patterns.

---

## Reference Documents

For detailed patterns and frameworks, read these reference files:

### Core References
- `references/pine-v6-language.md` - Complete v6 syntax and features
- `references/technical-analysis.md` - Market/Volume Profile, AVWAP, EMA Clouds
- `references/alert-webhook-integration.md` - n8n webhook patterns and JSON templates
- `references/indicator-patterns.md` - Common indicator implementations
- `references/strategy-patterns.md` - Strategy templates and position management

### When to Read Each
- **Building indicators**: Read `indicator-patterns.md` + `technical-analysis.md`
- **Building strategies**: Read `strategy-patterns.md` + `alert-webhook-integration.md`
- **Webhook automation**: Read `alert-webhook-integration.md`
- **Advanced v6 features**: Read `pine-v6-language.md`

---

## Code Templates Location

Pre-built templates in `scripts/`:
- `indicator-template.pine` - Basic indicator scaffold
- `strategy-template.pine` - Strategy with webhook alerts
- `four-pillars-framework.pine` - Complete Four Pillars implementation
- `quad-stochastic.pine` - Quad Rotation Stochastic system

---

## Version History

**v2.0 (2026-02-03) - Major Update**
- Added: Fast vs Full stochastic functions (critical distinction)
- Added: State machine pattern with if/else if chains
- Added: Edge detection requirements for alerts
- Added: Turn detection with momentum confirmation
- Added: Supersignal timing with persistence window
- Added: Hidden plots for JSON alerts
- Added: Code review checklist
- Fixed: Removed `{{strategy.order.action}}` from indicator examples
- Fixed: Alert naming (Management, not Exit)

**v1.0 - Initial Release**
- Basic Pine Script v6 syntax
- Common calculations and patterns
- Alert system basics
