# Technical Analysis Framework Reference

## Four Pillars Trading System

### Pillar 1: Price Structure (Multi-EMA / Ripster Clouds)

**Ripster EMA Cloud Configuration:**
- Cloud 1: 8/9 EMA (Not used in Four Pillars)
- Cloud 2: 5/12 EMA (Short-term momentum)
- Cloud 3: 34/50 EMA (Medium-term trend, BC filter)
- Cloud 4: 72/89 EMA (Long-term trend)
- Cloud 5: 180/200 EMA (Macro trend, not used)

**Implementation:**
```pinescript
// Ripster EMA Clouds
ema5 = ta.ema(close, 5)
ema12 = ta.ema(close, 12)
ema34 = ta.ema(close, 34)
ema50 = ta.ema(close, 50)
ema8 = ta.ema(close, 8)
ema9 = ta.ema(close, 9)

// Cloud states
cloud1_bullish = ema8 > ema9      // Cloud 1: 8/9 (unused)
cloud2_bullish = ema5 > ema12     // Cloud 2: 5/12
cloud3_bullish = ema34 > ema50    // Cloud 3: 34/50

// Full bullish alignment (Clouds 2-4)
fullBullish = cloud2_bullish and cloud3_bullish and cloud4_bullish
fullBearish = not cloud2_bullish and not cloud3_bullish and not cloud4_bullish
```

**Trading Rules:**
- All clouds green = Strong uptrend, look for longs only
- All clouds red = Strong downtrend, look for shorts only
- Mixed colors = Consolidation/transition, reduce size or wait

---

### Pillar 2: Directional Bias (VWAP / Anchored VWAP)

**Session VWAP:**
```pinescript
vwap_daily = ta.vwap(hlc3)

// Price relationship to VWAP
aboveVwap = close > vwap_daily
belowVwap = close < vwap_daily
```

**Anchored VWAP (Brian Shannon Method):**

Key anchor points (psychologically meaningful, not mechanical):
1. **Significant swing highs/lows** - Major turning points
2. **Earnings/news events** - Fundamental catalysts
3. **Gap opens** - Sentiment shifts
4. **Volume spikes** - Institutional activity
5. **Consolidation breakouts** - New trend initiations

```pinescript
// Manual AVWAP calculation from anchor bar
var float sumPV = 0.0
var float sumV = 0.0
var int anchorBar = 0

// Reset on new anchor (user input or detected)
if newAnchorCondition
    sumPV := 0.0
    sumV := 0.0
    anchorBar := bar_index

// Accumulate from anchor
sumPV += hlc3 * volume
sumV += volume
avwap = sumPV / sumV
```

**WARNING — AVWAP stdev=0 on bar 1:** Immediately after anchor reset, standard deviation is 0 (only 1 data point). This creates a near-zero SL distance if using AVWAP ± stdev as stop loss. Always floor with ATR:
```pinescript
float avwap_stdev = ta.stdev(hlc3, bar_index - anchorBar + 1)
float sl_distance = math.max(avwap_stdev, ta.atr(14))  // Floor with ATR
```

---

### Pillar 3: Momentum (Quad Rotation Stochastic)

**The 4 Stochastics (John Kurisko Settings):**
| Name | K | Smooth | Type | Role |
|------|---|--------|------|------|
| 9-3 | 9 | 3 | Fast | Entry timing |
| 14-3 | 14 | 3 | Fast | Confirmation |
| 40-4 | 40 | 3 | Fast | Primary divergence |
| 60-10 | 60 | 10 | Full | Macro filter |

**CRITICAL: Fast vs Full Stochastic**
- Fast = single smoothing: `ta.sma(rawK, smooth)`
- Full = double smoothing: `ta.sma(ta.sma(rawK, smooth), smooth)`

**Alignment Scoring:**
- 4/4 aligned = Maximum conviction
- 3/4 aligned = Strong signal
- 2/4 + Macro aligned = Continuation setup
- <2/4 = No trade or reduced size

**Divergence Detection (40-4 PRIMARY):**

Bullish Divergence:
1. 40-4 stochastic drops <20, bounces >20
2. Price makes lower low
3. 40-4 stochastic makes higher low
4. Stochastic turning up (stoch > stoch[1])

---

### Pillar 4: Volatility Filter (BBWP)

**Bollinger Band Width Percentile:**
```pinescript
[middle, upper, lower] = ta.bb(close, 20, 2.0)
bbw = (upper - lower) / middle

bbwp_lookback = 252
bbwp = ta.percentrank(bbw, bbwp_lookback)

lowVolatility = bbwp < 20      // Squeeze, breakout likely
highVolatility = bbwp > 80     // Extended, mean reversion likely
```

---

## Market Profile / Volume Profile

### Core Concepts

| Element | Definition | Trading Use |
|---------|------------|-------------|
| POC | Point of Control - highest volume price | Magnet, support/resistance |
| VAH | Value Area High - upper 70% boundary | Resistance, breakout level |
| VAL | Value Area Low - lower 70% boundary | Support, breakdown level |
| HVN | High Volume Node | Price "sticks" here |
| LVN | Low Volume Node | Price moves fast through |

### Balance-Imbalance-Excess Framework

**1. BALANCE (70-80% of time):**
- Symmetrical bell-curve profile
- Trade: Fade extremes, buy VAL, sell VAH

**2. IMBALANCE:**
- One side dominates, value area migrating
- Trade: Go with direction, don't fade

**3. EXCESS:**
- Sharp spike on LOW volume, immediate reversal
- Trade: Mark as reversal point

---

## Trailing SL vs Symmetric SL Tradeoffs

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Symmetric SL/TP** (fixed at entry) | Predictable R:R, fast exits, low commission waste | Misses runners, no adaptation | Rebate farming, high-frequency |
| **Cloud Trail** (follows EMA cloud) | Catches trends, adapts to momentum | Activation delay, bleeds in chop, slow to protect gains | Trending markets only |
| **AVWAP Trail** (follows AVWAP ± stdev) | Statistically meaningful levels | stdev=0 early, barely trails in first bars | Swing trades with anchor |
| **Breakeven + $X Raise** | Converts 86% of "saw green" losers to small wins | Ultra-tight, may get stopped out on noise | Add-on to any SL strategy |

**Key finding (v3.5→v3.7.1):** 86% of losing trades saw unrealized profit before dying. Signal quality is fine — exit timing is the bottleneck. Trailing stops bleed in choppy markets. Tight symmetric SL/TP + breakeven raise is the current best approach for rebate farming.

---

## Risk Management

**Position Sizing:**
```pinescript
accountRisk = 0.02  // 2% risk per trade
stopDistance = math.abs(close - stopLoss)
positionSize = (accountSize * accountRisk) / stopDistance

// For crypto with leverage
leverage = 20
positionValue = 250  // USD per position
```

**Entry Checklist:**
1. ✅ Price Structure aligned (Ripster Clouds)
2. ✅ Directional Bias confirmed (VWAP position)
3. ✅ Momentum aligned (Stochastic 3/4 or 4/4)
4. ✅ Volatility acceptable (BBWP not extreme)
5. ✅ Profile context (not trading into HVN resistance)
