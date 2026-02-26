# Indicator Patterns Reference

## Ripster EMA Clouds

**Cloud numbering:** Cloud 1: 8/9 (unused), Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89, Cloud 5: 180/200

```pinescript
//@version=6
indicator("Ripster EMA Clouds", overlay=true)

// Cloud 1 (unused): 8/9
ema8 = ta.ema(close, 8)
ema9 = ta.ema(close, 9)

// Cloud 2: 5/12 — short-term momentum
ema5 = ta.ema(close, 5)
ema12 = ta.ema(close, 12)

// Cloud 3: 34/50 — medium-term trend (BC filter)
ema34 = ta.ema(close, 34)
ema50 = ta.ema(close, 50)

// Cloud 4: 72/89 — long-term trend
ema72 = ta.ema(close, 72)
ema89 = ta.ema(close, 89)

p5 = plot(ema5, "EMA 5", color.new(color.blue, 100))
p12 = plot(ema12, "EMA 12", color.new(color.blue, 100))
fill(p5, p12, color = ema5 > ema12 ? color.new(color.green, 70) : color.new(color.red, 70))

cloud2_bull = ema5 > ema12
cloud3_bull = ema34 > ema50
cloud4_bull = ema72 > ema89
allBullish = cloud2_bull and cloud3_bull and cloud4_bull
allBearish = not cloud2_bull and not cloud3_bull and not cloud4_bull
```

---

## Quad Rotation Stochastic

### Raw K Stochastic (Four Pillars v3.7+)

```pinescript
// Raw K — NO SMA smoothing. Used for all 4 stochastics in Four Pillars.
stoch_k(int k_len) =>
    float lowest = ta.lowest(low, k_len)
    float highest = ta.highest(high, k_len)
    highest - lowest == 0 ? 50.0 : 100.0 * (close - lowest) / (highest - lowest)
```

### Fast vs Full Stochastic Functions

```pinescript
// FAST STOCHASTIC - Single smoothing (9-3, 14-3, 40-4)
stoch_fast(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k = ta.sma(k_raw, smooth_k)
    k

// FULL STOCHASTIC - Double smoothing (60-10)
stoch_full(int k_len, int smooth_k) =>
    float lowest_low = ta.lowest(low, k_len)
    float highest_high = ta.highest(high, k_len)
    float range_val = highest_high - lowest_low
    float k_raw = range_val == 0 ? 50.0 : 100.0 * (close - lowest_low) / range_val
    float k_smooth1 = ta.sma(k_raw, smooth_k)
    float k_full = ta.sma(k_smooth1, smooth_k)
    k_full
```

### Alignment Counting

```pinescript
threshold = 50
bull_count = (stoch_9_3 > threshold ? 1 : 0) +
             (stoch_14_3 > threshold ? 1 : 0) +
             (stoch_40_4 > threshold ? 1 : 0) +
             (stoch_60_10 > threshold ? 1 : 0)
```

---

## State Machine Pattern (Divergence)

```pinescript
var int bull_state = 0
var float bull_stage1_price = na
var float bull_stage1_stoch = na
var int bull_stage1_bar = na
bool bullish_divergence = false

// CRITICAL: if/else if chain prevents multiple execution
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
    else if bar_index - bull_stage1_bar > 20
        bull_state := 0
    else
        bool price_lower = low <= bull_stage1_price * 1.001
        bool stoch_higher = stoch_40_4 > bull_stage1_stoch
        bool turning_up = stoch_40_4 > stoch_40_4[1]
        if price_lower and stoch_higher and turning_up
            bullish_divergence := true
            bull_state := 0
```

---

## Turn Detection

```pinescript
// CRITICAL: Must check BOTH lookback AND current momentum
int i_lookback = 3

// WRONG - can be true while still falling
// bool turning_up = stoch > stoch[i_lookback]

// CORRECT
bool turning_up = stoch > nz(stoch[i_lookback], 50) and stoch > stoch[1]
bool turning_down = stoch < nz(stoch[i_lookback], 50) and stoch < stoch[1]
```

---

## BBWP (Bollinger Band Width Percentile)

```pinescript
[middle, upper, lower] = ta.bb(close, 20, 2.0)
bbw = (upper - lower) / middle * 100
bbwp = ta.percentrank(bbw, 252)

bgcolor(bbwp < 20 ? color.new(color.green, 90) : bbwp > 80 ? color.new(color.red, 90) : na)
```

---

## ATR-Based Stops

```pinescript
atr = ta.atr(14)
longStop = close - atr * 2.0
shortStop = close + atr * 2.0

plot(longStop, "Long Stop", color.green, 1, plot.style_stepline)
plot(shortStop, "Short Stop", color.red, 1, plot.style_stepline)
```

---

## Session Detection

```pinescript
inAsia = not na(time(timeframe.period, "0000-0900", "UTC"))
inLondon = not na(time(timeframe.period, "0700-1600", "UTC"))
inNewYork = not na(time(timeframe.period, "1300-2200", "UTC"))
```

---

## Edge-Triggered Shapes

```pinescript
// CRITICAL: Edge-trigger all visual signals
plotshape(buySignal and not buySignal[1], "Buy", shape.triangleup,
    location.belowbar, color.green, size=size.small)
```

---

## Hidden Plots for JSON

```pinescript
// Always plot regardless of visibility for JSON access
plot(stoch_9_3, "stoch_9_3", display=display.none)
plot(stoch_14_3, "stoch_14_3", display=display.none)
plot(stoch_40_4, "stoch_40_4", display=display.none)
plot(stoch_60_10, "stoch_60_10", display=display.none)
```
