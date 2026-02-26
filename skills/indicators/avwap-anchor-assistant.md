# AVWAP Anchor Assistant
**Purpose**: Identify high-quality AVWAP anchor points using Structure, Volume, and Price Position
**Integration**: Standalone indicator, exports values for Four Pillars (Pillar 2: VWAP Bias)
**Methodology**: Brian Shannon AVWAP + Wyckoff VSA

---

## Three Pillars

### Pillar A: STRUCTURE
Identifies where trapped traders exist

```pinescript
// Swing Detection
pivotLen = input.int(5, "Pivot Length")
swingHigh = ta.pivothigh(high, pivotLen, pivotLen)
swingLow = ta.pivotlow(low, pivotLen, pivotLen)

// Track latest swings
var float lastSwingHigh = na
var float lastSwingLow = na
var int lastSwingHighBar = na
var int lastSwingLowBar = na

if not na(swingHigh)
    lastSwingHigh := swingHigh
    lastSwingHighBar := bar_index - pivotLen

if not na(swingLow)
    lastSwingLow := swingLow
    lastSwingLowBar := bar_index - pivotLen
```

**Output**: Structure High (resistance), Structure Low (support)

---

### Pillar B: VOLUME COMMITMENT
Identifies where institutional commitment entered

```pinescript
// Volume Classification
volMaPeriod = input.int(20, "Volume MA")
avgVol = ta.sma(volume, volMaPeriod)
volRatio = volume / avgVol

// Thresholds
isSpike = volRatio > 1.5
isClimax = volRatio > 2.0

// Spread Analysis
atr = ta.atr(14)
spread = high - low
spreadRatio = spread / atr
isWideSpread = spreadRatio > 1.5

// Close Position
closePosition = spread > 0 ? (close - low) / spread : 0.5
isCloseOffLow = closePosition > 0.4

// VSA Patterns
isDownBar = close < open
isUpBar = close > open

// Stopping Volume: Down bar + high volume + close off lows
stoppingVolume = isDownBar and volRatio > 1.5 and isCloseOffLow

// Selling Climax: Wide down bar + extreme volume
sellingClimax = isDownBar and isWideSpread and volRatio > 2.0 and closePosition > 0.3

// Buying Climax: Wide up bar + extreme volume
buyingClimax = isUpBar and isWideSpread and volRatio > 2.0 and closePosition < 0.7
```

**Output**: Event type (Stopping/Climax), Event price, Volume ratio

---

### Pillar C: PRICE POSITION
Determines who controls current price

```pinescript
// VWAP Calculations (simplified - from anchor points)
calcVWAP(startBar) =>
    sumPV = 0.0
    sumV = 0.0
    for i = 0 to bar_index - startBar
        sumPV += hlc3[i] * volume[i]
        sumV += volume[i]
    sumV > 0 ? sumPV / sumV : na

// Position Analysis
priceAboveHighVWAP = close > vwapFromHigh
priceBelowHighVWAP = close < vwapFromHigh
priceAboveLowVWAP = close > vwapFromLow
priceBelowLowVWAP = close < vwapFromLow

// Bias Determination
bias = priceAboveLowVWAP and priceBelowHighVWAP ? 0 :  // Neutral (between)
       priceAboveLowVWAP and priceAboveHighVWAP ? 1 :  // Strong Bullish
       priceBelowLowVWAP ? -1 : 0                       // Bearish
```

**Output**: Price vs each VWAP, Overall bias (Buyers/Sellers/Neutral)

---

## Dashboard Layout

```
┌──────────────────────────────────────────┐
│ AVWAP ASSISTANT                          │
├──────────────────────────────────────────┤
│ Structure High │ [price] │ RESISTANCE    │
│ Structure Low  │ [price] │ SUPPORT       │
│ Volume Event   │ [price] │ [event type]  │
│ POC            │ [price] │ FAIR VALUE    │
│ BIAS           │ [position] │ [control]  │
└──────────────────────────────────────────┘
```

---

## Settings (30min Crypto)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Volume MA | 20 | ~10 hours lookback |
| Spike threshold | 1.5x | Shannon minimum |
| Climax threshold | 2.0x | Extreme events |
| Pivot length | 5 | 2.5 hours for swings |
| ATR period | 14 | Spread normalization |

---

## Integration Export

```pinescript
// For Four Pillars Pillar 2
var float export_vwap_low = na
var float export_vwap_high = na
var int export_bias = 0  // 1=bull, -1=bear, 0=neutral
var string export_quality = "NONE"
```

---

## Shannon Alignment

| Shannon Principle | Implementation |
|-------------------|----------------|
| "Anchor at significant events" | VSA Stopping/Climax detection |
| "Volume = emotional commitment" | >1.5x threshold validation |
| "Swings trap traders" | Structure High/Low tracking |
| "Don't anchor randomly" | Quality scoring |
| "Who controls trend" | Price vs VWAP position |

---

## Build Priority

1. **Must Have**: Swing detection, Volume spikes, Dashboard
2. **Should Have**: VSA Stopping/Climax, VWAP calculations
3. **Nice to Have**: Quality scoring, Alerts, Integration export
