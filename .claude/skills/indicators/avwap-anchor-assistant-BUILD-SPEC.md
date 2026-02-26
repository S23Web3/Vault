# AVWAP ANCHOR ASSISTANT - BUILD SPECIFICATION v1.2
**Version**: 1.2 (All Fixes Applied)  
**Date**: 2026-02-02  
**Target**: PineScript v6  
**Methodology**: Brian Shannon AVWAP + Wyckoff VSA

---

## CHANGELOG

### v1.2 (Current)
| Issue | Fix |
|-------|-----|
| VWAP backfill missing | Added for-loop backfill from anchor bar on pivot detection |
| Structure trend false positive | Added history check, show "BUILDING..." until enough data |
| Volume Flow MA hardcoded | Added i_volFlowPeriod input |
| Dashboard N/A color | Fixed to show neutral color for N/A values |
| Dashboard 9999 display | Shows "STALE" instead of raw bar count |

### v1.1
| Issue | Fix |
|-------|-----|
| POC not implemented | Removed all POC references |
| VWAP loop O(n²) | Replaced with cumulative calculation |
| VSA var bug | Removed `var` from per-bar variables |
| Label accumulation | Added array management with cleanup |
| Structure trend logic | Fixed to track swing sequence properly |
| Dashboard table creation | Moved outside if block |
| Export syntax | Removed invalid `export` keyword |
| volumeFlowBullish unused | Added to dashboard |
| Missing alerts | Added alert conditions |

---

## COMPLETE IMPLEMENTATION CODE

### Section 1: Indicator Declaration & Inputs

```pinescript
//@version=6
indicator("AVWAP Anchor Assistant", shorttitle="AVWAP-AA", overlay=true, 
          max_boxes_count=500, max_lines_count=500, max_labels_count=500)

// ═══════════════════════════════════════════════════════════════════════════
// INPUTS
// ═══════════════════════════════════════════════════════════════════════════

// Structure Settings
grpStructure = "═══ PILLAR A: STRUCTURE ═══"
i_pivotLen = input.int(5, "Pivot Lookback", minval=2, maxval=20, group=grpStructure, 
             tooltip="Bars to confirm swing high/low. Higher = fewer swings, more reliable.")
i_showSwings = input.bool(true, "Show Swing Levels", group=grpStructure)
i_extendSwings = input.bool(true, "Extend Swing Lines", group=grpStructure)
i_maxSwingAge = input.int(200, "Max Swing Age (bars)", minval=50, maxval=500, group=grpStructure,
                tooltip="Swings older than this are considered stale")

// Volume Settings
grpVolume = "═══ PILLAR B: VOLUME ═══"
i_volMaPeriod = input.int(20, "Volume MA Period", minval=5, maxval=50, group=grpVolume)
i_volFlowPeriod = input.int(14, "Volume Flow MA", minval=5, maxval=50, group=grpVolume,
                  tooltip="EMA period for bull/bear volume flow separation")
i_spikeThreshold = input.float(1.5, "Spike Threshold (x avg)", minval=1.1, maxval=3.0, step=0.1, group=grpVolume)
i_climaxThreshold = input.float(2.0, "Climax Threshold (x avg)", minval=1.5, maxval=4.0, step=0.1, group=grpVolume)
i_atrPeriod = input.int(14, "ATR Period", minval=5, maxval=30, group=grpVolume)
i_showVSA = input.bool(true, "Show VSA Labels", group=grpVolume)
i_maxVSALabels = input.int(30, "Max VSA Labels", minval=10, maxval=100, group=grpVolume)

// VWAP Settings
grpVWAP = "═══ PILLAR C: VWAP ═══"
i_showVWAPs = input.bool(true, "Show VWAP Lines", group=grpVWAP)
i_vwapFromHigh = input.bool(true, "VWAP from Structure High", group=grpVWAP)
i_vwapFromLow = input.bool(true, "VWAP from Structure Low", group=grpVWAP)
i_vwapFromEvent = input.bool(true, "VWAP from Volume Event", group=grpVWAP)

// Dashboard Settings
grpDash = "═══ DASHBOARD ═══"
i_showDashboard = input.bool(true, "Show Dashboard", group=grpDash)
i_dashPosition = input.string("Top Right", "Position", 
                 options=["Top Right", "Top Left", "Bottom Right", "Bottom Left"], group=grpDash)
i_dashSize = input.string("Normal", "Size", options=["Small", "Normal", "Large"], group=grpDash)

// Colors
grpColors = "═══ COLORS ═══"
i_bullColor = input.color(color.new(#26a69a, 0), "Bullish", group=grpColors)
i_bearColor = input.color(color.new(#ef5350, 0), "Bearish", group=grpColors)
i_neutralColor = input.color(color.new(#787b86, 0), "Neutral", group=grpColors)
i_highQualityColor = input.color(color.new(#00e676, 0), "High Quality", group=grpColors)
i_medQualityColor = input.color(color.new(#ffeb3b, 0), "Medium Quality", group=grpColors)
i_vwapHighColor = input.color(color.new(#ef5350, 30), "VWAP High Line", group=grpColors)
i_vwapLowColor = input.color(color.new(#26a69a, 30), "VWAP Low Line", group=grpColors)
i_vwapEventColor = input.color(color.new(#ff9800, 30), "VWAP Event Line", group=grpColors)
```

---

### Section 2: Pillar A - Structure Detection (v1.2 FIXED)

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// PILLAR A: STRUCTURE DETECTION
// ═══════════════════════════════════════════════════════════════════════════

// Swing Detection using built-in pivot functions
pivotHigh = ta.pivothigh(high, i_pivotLen, i_pivotLen)
pivotLow = ta.pivotlow(low, i_pivotLen, i_pivotLen)

// Persistent tracking of swings
var float lastSwingHigh = na
var float lastSwingLow = na
var int lastSwingHighBar = na
var int lastSwingLowBar = na
var float prevSwingHigh = na
var float prevSwingLow = na

// Track swing sequence for trend - use na for "unknown" state (v1.2 FIX)
var bool lastHighWasHH = na
var bool lastLowWasHL = na

// Track if we have comparison history (v1.2 FIX)
var bool hasSwingHighHistory = false
var bool hasSwingLowHistory = false

// Update swing high
if not na(pivotHigh)
    // Check if we have previous swing to compare (v1.2 FIX)
    hasSwingHighHistory := not na(lastSwingHigh)
    prevSwingHigh := lastSwingHigh
    lastSwingHigh := pivotHigh
    lastSwingHighBar := bar_index - i_pivotLen
    // Only set HH/LH if we have comparison data (v1.2 FIX)
    if hasSwingHighHistory
        lastHighWasHH := pivotHigh > prevSwingHigh

// Update swing low
if not na(pivotLow)
    hasSwingLowHistory := not na(lastSwingLow)
    prevSwingLow := lastSwingLow
    lastSwingLow := pivotLow
    lastSwingLowBar := bar_index - i_pivotLen
    if hasSwingLowHistory
        lastLowWasHL := pivotLow > prevSwingLow

// Calculate bars since swings (with safety)
barsFromSwingHigh = na(lastSwingHighBar) ? 9999 : bar_index - lastSwingHighBar
barsFromSwingLow = na(lastSwingLowBar) ? 9999 : bar_index - lastSwingLowBar

// Check if swings are stale
swingHighStale = barsFromSwingHigh > i_maxSwingAge
swingLowStale = barsFromSwingLow > i_maxSwingAge

// Can we determine trend? Need both HH/LH and HL/LL data (v1.2 FIX)
bool canDetermineTrend = not na(lastHighWasHH) and not na(lastLowWasHL)

// Market Structure Classification
// Bullish: HH AND HL | Bearish: LH AND LL | Neutral: Mixed
structureTrend = not canDetermineTrend ? 0 :
                 lastHighWasHH and lastLowWasHL ? 1 :
                 (not lastHighWasHH) and (not lastLowWasHL) ? -1 : 0

structureTrendStr = not canDetermineTrend ? "BUILDING..." :
                    structureTrend == 1 ? "BULLISH (HH/HL)" :
                    structureTrend == -1 ? "BEARISH (LH/LL)" :
                    "NEUTRAL (MIXED)"
```

---

### Section 3: Pillar B - Volume Commitment (v1.2 FIXED)

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// PILLAR B: VOLUME COMMITMENT
// ═══════════════════════════════════════════════════════════════════════════

// Core calculations
avgVol = ta.sma(volume, i_volMaPeriod)
volRatio = avgVol > 0 ? volume / avgVol : 1.0
atr = ta.atr(i_atrPeriod)

// Volume Classification
isVolumeSpike = volRatio > i_spikeThreshold
isVolumeClimax = volRatio > i_climaxThreshold
isLowVolume = volRatio < 0.8

// Spread Classification
spread = high - low
spreadRatio = atr > 0 ? spread / atr : 1.0
isWideSpread = spreadRatio > 1.5
isNarrowSpread = spreadRatio < 0.7

// Close Position (0 = low, 1 = high)
closePosition = spread > 0 ? (close - low) / spread : 0.5
isCloseHigh = closePosition > 0.7
isCloseLow = closePosition < 0.3
isCloseOffLow = closePosition > 0.4
isCloseOffHigh = closePosition < 0.6

// Bar Direction
isUpBar = close > open
isDownBar = close < open

// ─────────────────────────────────────────────────────────────────────────
// VOLUME FLOW (Bull vs Bear) - v1.2 FIX: Use input for MA period
// ─────────────────────────────────────────────────────────────────────────
bullVol = isUpBar ? volume : 0.0
bearVol = isDownBar ? volume : 0.0
bullVolMA = ta.ema(bullVol, i_volFlowPeriod)
bearVolMA = ta.ema(bearVol, i_volFlowPeriod)
volumeFlowBullish = bullVolMA > bearVolMA
volumeFlowStr = volumeFlowBullish ? "BULL FLOW" : "BEAR FLOW"

// ─────────────────────────────────────────────────────────────────────────
// VSA PATTERN DETECTION
// ─────────────────────────────────────────────────────────────────────────

// STOPPING VOLUME (Bullish)
stoppingVolume = isDownBar and 
                 volRatio > i_spikeThreshold and
                 isCloseOffLow

// SELLING CLIMAX (Bullish - end of downtrend)
sellingClimax = isDownBar and
                isWideSpread and
                volRatio > i_climaxThreshold and
                closePosition > 0.3

// BUYING CLIMAX (Bearish - end of uptrend)
buyingClimax = isUpBar and
               isWideSpread and
               volRatio > i_climaxThreshold and
               isCloseOffHigh

// NO SUPPLY (Bullish)
noSupply = isDownBar and
           isNarrowSpread and
           isLowVolume

// NO DEMAND (Bearish)
noDemand = isUpBar and
           isNarrowSpread and
           isLowVolume

// UPTHRUST (Bearish)
upthrust = isDownBar and
           high > ta.highest(high[1], 10) and
           closePosition < 0.4 and
           volRatio > 1.0

// SPRING (Bullish)
spring = isUpBar and
         low < ta.lowest(low[1], 10) and
         closePosition > 0.6 and
         volRatio > 1.0

// ─────────────────────────────────────────────────────────────────────────
// VSA SIGNAL AGGREGATION (no var - recalculates each bar)
// ─────────────────────────────────────────────────────────────────────────

string currentVSA = "NONE"
bool isBullishVSA = false
bool isBearishVSA = false

if sellingClimax
    currentVSA := "SELL CLIMAX"
    isBullishVSA := true
else if buyingClimax
    currentVSA := "BUY CLIMAX"
    isBearishVSA := true
else if stoppingVolume
    currentVSA := "STOPPING"
    isBullishVSA := true
else if spring
    currentVSA := "SPRING"
    isBullishVSA := true
else if upthrust
    currentVSA := "UPTHRUST"
    isBearishVSA := true
else if noSupply
    currentVSA := "NO SUPPLY"
    isBullishVSA := true
else if noDemand
    currentVSA := "NO DEMAND"
    isBearishVSA := true

// Track most recent significant event (persistent)
var float lastEventPrice = na
var float lastEventHigh = na
var float lastEventLow = na
var int lastEventBar = na
var string lastEventType = "NONE"
var bool lastEventBullish = false

if currentVSA != "NONE"
    lastEventPrice := close
    lastEventHigh := high
    lastEventLow := low
    lastEventBar := bar_index
    lastEventType := currentVSA
    lastEventBullish := isBullishVSA

barsFromEvent = na(lastEventBar) ? 9999 : bar_index - lastEventBar
```

---

### Section 4: Pillar C - VWAP Calculation (v1.2 FIXED: Backfill)

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// PILLAR C: VWAP CALCULATION (v1.2 FIX: Proper backfill from anchor bar)
// ═══════════════════════════════════════════════════════════════════════════

// Cumulative sums for each VWAP anchor
var float cumPV_high = 0.0
var float cumV_high = 0.0
var float cumPV_low = 0.0
var float cumV_low = 0.0
var float cumPV_event = 0.0
var float cumV_event = 0.0

// ─────────────────────────────────────────────────────────────────────────
// RESET AND BACKFILL when new anchor detected (v1.2 FIX)
// Pivot is detected at current bar but actual swing was i_pivotLen bars ago
// We need to include data from anchor bar through current bar
// ─────────────────────────────────────────────────────────────────────────

if not na(pivotHigh)
    // Reset cumulative sums
    cumPV_high := 0.0
    cumV_high := 0.0
    // Backfill from anchor bar (i_pivotLen ago) to bar BEFORE current (i=1)
    // Current bar will be added by normal accumulation below
    for i = 1 to i_pivotLen
        cumPV_high += hlc3[i] * volume[i]
        cumV_high += volume[i]

if not na(pivotLow)
    cumPV_low := 0.0
    cumV_low := 0.0
    for i = 1 to i_pivotLen
        cumPV_low += hlc3[i] * volume[i]
        cumV_low += volume[i]

if currentVSA != "NONE"
    // VSA event IS at current bar - no backfill needed
    cumPV_event := 0.0
    cumV_event := 0.0

// ─────────────────────────────────────────────────────────────────────────
// ACCUMULATE on every bar (only if anchor exists and not stale)
// ─────────────────────────────────────────────────────────────────────────

if not na(lastSwingHighBar) and not swingHighStale
    cumPV_high += hlc3 * volume
    cumV_high += volume

if not na(lastSwingLowBar) and not swingLowStale
    cumPV_low += hlc3 * volume
    cumV_low += volume

if not na(lastEventBar) and barsFromEvent < i_maxSwingAge
    cumPV_event += hlc3 * volume
    cumV_event += volume

// Calculate VWAPs
vwapFromHigh = i_vwapFromHigh and cumV_high > 0 ? cumPV_high / cumV_high : na
vwapFromLow = i_vwapFromLow and cumV_low > 0 ? cumPV_low / cumV_low : na
vwapFromEvent = i_vwapFromEvent and cumV_event > 0 ? cumPV_event / cumV_event : na

// ─────────────────────────────────────────────────────────────────────────
// PRICE POSITION ANALYSIS
// ─────────────────────────────────────────────────────────────────────────

priceVsHighVWAP = na(vwapFromHigh) ? "N/A" : close > vwapFromHigh ? "ABOVE" : "BELOW"
priceVsLowVWAP = na(vwapFromLow) ? "N/A" : close > vwapFromLow ? "ABOVE" : "BELOW"
priceVsEventVWAP = na(vwapFromEvent) ? "N/A" : close > vwapFromEvent ? "ABOVE" : "BELOW"

distFromHighVWAP = not na(vwapFromHigh) ? ((close - vwapFromHigh) / vwapFromHigh) * 100 : na
distFromLowVWAP = not na(vwapFromLow) ? ((close - vwapFromLow) / vwapFromLow) * 100 : na
distFromEventVWAP = not na(vwapFromEvent) ? ((close - vwapFromEvent) / vwapFromEvent) * 100 : na

// Overall Bias Determination
string overallBias = "NEUTRAL"
string biasControl = "CONTESTED"

if not na(vwapFromHigh) and not na(vwapFromLow)
    if close > vwapFromHigh and close > vwapFromLow
        overallBias := "STRONG BULL"
        biasControl := "BUYERS"
    else if close < vwapFromHigh and close < vwapFromLow
        overallBias := "STRONG BEAR"
        biasControl := "SELLERS"
    else if close > vwapFromLow and close < vwapFromHigh
        overallBias := "NEUTRAL"
        biasControl := "RANGE"
    else
        overallBias := "CONTESTED"
        biasControl := "MIXED"
else if not na(vwapFromLow)
    overallBias := close > vwapFromLow ? "BULLISH" : "BEARISH"
    biasControl := close > vwapFromLow ? "BUYERS" : "SELLERS"
else if not na(vwapFromHigh)
    overallBias := close > vwapFromHigh ? "BULLISH" : "BEARISH"
    biasControl := close > vwapFromHigh ? "BUYERS" : "SELLERS"

biasValue = overallBias == "STRONG BULL" ? 2 :
            overallBias == "BULLISH" ? 1 :
            overallBias == "STRONG BEAR" ? -2 :
            overallBias == "BEARISH" ? -1 : 0
```

---

### Section 5: Anchor Quality Scoring

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// ANCHOR QUALITY SCORING
// ═══════════════════════════════════════════════════════════════════════════

float WEIGHT_VSA = 40.0
float WEIGHT_VOLUME = 25.0
float WEIGHT_RECENCY = 20.0
float WEIGHT_TREND = 15.0

// Helper function for safe historical volume ratio access
safeVolRatio(int barsBack) =>
    if barsBack <= 0 or barsBack >= bar_index or barsBack > 500
        1.0
    else
        vol = volume[barsBack]
        avg = ta.sma(volume, i_volMaPeriod)[barsBack]
        avg > 0 ? vol / avg : 1.0

// Structure High Anchor Score
calcHighAnchorScore() =>
    float score = 0.0
    if na(lastSwingHighBar) or swingHighStale
        score
    else
        volAtSwing = safeVolRatio(barsFromSwingHigh)
        if volAtSwing > 1.5
            score += WEIGHT_VOLUME
        else if volAtSwing > 1.2
            score += WEIGHT_VOLUME * 0.6
        
        if barsFromSwingHigh < 20
            score += WEIGHT_RECENCY
        else if barsFromSwingHigh < 50
            score += WEIGHT_RECENCY * 0.5
        else if barsFromSwingHigh < 100
            score += WEIGHT_RECENCY * 0.25
        
        if structureTrend == -1
            score += WEIGHT_TREND
        else if structureTrend == 0
            score += WEIGHT_TREND * 0.5
        
        score

// Structure Low Anchor Score
calcLowAnchorScore() =>
    float score = 0.0
    if na(lastSwingLowBar) or swingLowStale
        score
    else
        volAtSwing = safeVolRatio(barsFromSwingLow)
        if volAtSwing > 1.5
            score += WEIGHT_VOLUME
        else if volAtSwing > 1.2
            score += WEIGHT_VOLUME * 0.6
        
        if barsFromSwingLow < 20
            score += WEIGHT_RECENCY
        else if barsFromSwingLow < 50
            score += WEIGHT_RECENCY * 0.5
        else if barsFromSwingLow < 100
            score += WEIGHT_RECENCY * 0.25
        
        if structureTrend == 1
            score += WEIGHT_TREND
        else if structureTrend == 0
            score += WEIGHT_TREND * 0.5
        
        score

// Event Anchor Score
calcEventAnchorScore() =>
    float score = 0.0
    if na(lastEventBar) or barsFromEvent > i_maxSwingAge
        score
    else
        if lastEventType == "SELL CLIMAX" or lastEventType == "BUY CLIMAX"
            score += WEIGHT_VSA
        else if lastEventType == "STOPPING" or lastEventType == "SPRING" or lastEventType == "UPTHRUST"
            score += WEIGHT_VSA * 0.85
        else if lastEventType != "NONE"
            score += WEIGHT_VSA * 0.6
        
        if barsFromEvent < 20
            score += WEIGHT_RECENCY
        else if barsFromEvent < 50
            score += WEIGHT_RECENCY * 0.5
        
        score += WEIGHT_VOLUME * 0.5
        score

highAnchorScore = calcHighAnchorScore()
lowAnchorScore = calcLowAnchorScore()
eventAnchorScore = calcEventAnchorScore()

getQualityStr(float score) =>
    score >= 70 ? "HIGH" : score >= 40 ? "MEDIUM" : score > 0 ? "LOW" : "NONE"

getQualityColor(float score) =>
    score >= 70 ? i_highQualityColor : score >= 40 ? i_medQualityColor : i_neutralColor

highAnchorQuality = getQualityStr(highAnchorScore)
lowAnchorQuality = getQualityStr(lowAnchorScore)
eventAnchorQuality = getQualityStr(eventAnchorScore)
```

---

### Section 6: Visual Outputs

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// VISUAL OUTPUTS
// ═══════════════════════════════════════════════════════════════════════════

// Swing Level Lines
var line swingHighLine = na
var line swingLowLine = na

if i_showSwings and not na(lastSwingHigh) and not swingHighStale
    if na(swingHighLine)
        swingHighLine := line.new(lastSwingHighBar, lastSwingHigh, bar_index, lastSwingHigh,
                                  color=i_bearColor, style=line.style_dashed, width=1,
                                  extend=i_extendSwings ? extend.right : extend.none)
    else
        line.set_xy1(swingHighLine, lastSwingHighBar, lastSwingHigh)
        line.set_xy2(swingHighLine, bar_index, lastSwingHigh)

if i_showSwings and not na(lastSwingLow) and not swingLowStale
    if na(swingLowLine)
        swingLowLine := line.new(lastSwingLowBar, lastSwingLow, bar_index, lastSwingLow,
                                 color=i_bullColor, style=line.style_dashed, width=1,
                                 extend=i_extendSwings ? extend.right : extend.none)
    else
        line.set_xy1(swingLowLine, lastSwingLowBar, lastSwingLow)
        line.set_xy2(swingLowLine, bar_index, lastSwingLow)

// VWAP Lines
plot(i_showVWAPs ? vwapFromHigh : na, "VWAP from High",
     color=i_vwapHighColor, linewidth=2, style=plot.style_line)

plot(i_showVWAPs ? vwapFromLow : na, "VWAP from Low",
     color=i_vwapLowColor, linewidth=2, style=plot.style_line)

plot(i_showVWAPs ? vwapFromEvent : na, "VWAP from Event",
     color=i_vwapEventColor, linewidth=2, style=plot.style_line)

// VSA Labels with array cleanup
var label[] vsaLabels = array.new_label()

if i_showVSA and currentVSA != "NONE"
    labelColor = isBullishVSA ? i_bullColor : i_bearColor
    labelStyle = isBullishVSA ? label.style_label_up : label.style_label_down
    labelY = isBullishVSA ? low - atr * 0.5 : high + atr * 0.5
    
    newLabel = label.new(bar_index, labelY, currentVSA,
                         color=labelColor, textcolor=color.white,
                         style=labelStyle, size=size.tiny)
    array.push(vsaLabels, newLabel)
    
    while array.size(vsaLabels) > i_maxVSALabels
        oldLabel = array.shift(vsaLabels)
        label.delete(oldLabel)

// Volume Spike Markers
plotshape(isVolumeSpike and not isVolumeClimax and currentVSA == "NONE", 
          "Volume Spike", shape.circle, location.belowbar,
          color=color.new(#2196f3, 50), size=size.tiny)

plotshape(isVolumeClimax and currentVSA == "NONE",
          "Volume Climax", shape.diamond, location.belowbar,
          color=color.new(#9c27b0, 30), size=size.small)

// Swing point markers
plotshape(not na(pivotHigh), "Swing High", shape.triangledown,
          location.abovebar, color=i_bearColor, size=size.tiny, offset=-i_pivotLen)

plotshape(not na(pivotLow), "Swing Low", shape.triangleup,
          location.belowbar, color=i_bullColor, size=size.tiny, offset=-i_pivotLen)
```

---

### Section 7: Dashboard (v1.2 FIXED: Colors and Stale Display)

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD (v1.2 FIX: Proper colors for N/A and stale display)
// ═══════════════════════════════════════════════════════════════════════════

tablePos = switch i_dashPosition
    "Top Right" => position.top_right
    "Top Left" => position.top_left
    "Bottom Right" => position.bottom_right
    "Bottom Left" => position.bottom_left
    => position.top_right

tableSize = switch i_dashSize
    "Small" => size.small
    "Large" => size.large
    => size.normal

var table dashboard = table.new(tablePos, 4, 9, 
                                bgcolor=color.new(#1e222d, 10),
                                border_width=1, 
                                border_color=color.new(#363a45, 0))

if i_showDashboard and barstate.islast
    // Header
    table.cell(dashboard, 0, 0, "AVWAP ANCHOR ASSISTANT",
               text_color=color.white, text_size=tableSize,
               bgcolor=color.new(#363a45, 0), text_halign=text.align_left)
    
    biasColor = biasValue > 0 ? i_bullColor : biasValue < 0 ? i_bearColor : i_neutralColor
    table.cell(dashboard, 3, 0, overallBias,
               text_color=color.white, text_size=tableSize, bgcolor=biasColor)
    
    // Column Headers
    table.cell(dashboard, 0, 1, "ANCHOR", text_color=color.gray, text_size=tableSize)
    table.cell(dashboard, 1, 1, "PRICE", text_color=color.gray, text_size=tableSize)
    table.cell(dashboard, 2, 1, "QUALITY", text_color=color.gray, text_size=tableSize)
    table.cell(dashboard, 3, 1, "INFO", text_color=color.gray, text_size=tableSize)
    
    // Row 2: Structure High (v1.2 FIX: Show STALE instead of 9999)
    swingHighBarsStr = swingHighStale ? "STALE" : str.tostring(barsFromSwingHigh) + " bars"
    swingHighInfoColor = swingHighStale ? i_neutralColor : i_bearColor
    
    table.cell(dashboard, 0, 2, "Struct High", text_color=i_bearColor, text_size=tableSize)
    table.cell(dashboard, 1, 2, str.tostring(lastSwingHigh, format.mintick), 
               text_color=color.white, text_size=tableSize)
    table.cell(dashboard, 2, 2, highAnchorQuality + " " + str.tostring(math.round(highAnchorScore)),
               text_color=getQualityColor(highAnchorScore), text_size=tableSize)
    table.cell(dashboard, 3, 2, swingHighBarsStr + " | RESISTANCE",
               text_color=swingHighInfoColor, text_size=tableSize)
    
    // Row 3: Structure Low
    swingLowBarsStr = swingLowStale ? "STALE" : str.tostring(barsFromSwingLow) + " bars"
    swingLowInfoColor = swingLowStale ? i_neutralColor : i_bullColor
    
    table.cell(dashboard, 0, 3, "Struct Low", text_color=i_bullColor, text_size=tableSize)
    table.cell(dashboard, 1, 3, str.tostring(lastSwingLow, format.mintick),
               text_color=color.white, text_size=tableSize)
    table.cell(dashboard, 2, 3, lowAnchorQuality + " " + str.tostring(math.round(lowAnchorScore)),
               text_color=getQualityColor(lowAnchorScore), text_size=tableSize)
    table.cell(dashboard, 3, 3, swingLowBarsStr + " | SUPPORT",
               text_color=swingLowInfoColor, text_size=tableSize)
    
    // Row 4: Volume Event
    eventStale = barsFromEvent > i_maxSwingAge
    eventBarsStr = eventStale ? "STALE" : str.tostring(barsFromEvent) + " bars"
    eventDisplayColor = eventStale ? i_neutralColor : (lastEventBullish ? i_bullColor : i_bearColor)
    
    table.cell(dashboard, 0, 4, "Vol Event", text_color=eventDisplayColor, text_size=tableSize)
    table.cell(dashboard, 1, 4, str.tostring(lastEventPrice, format.mintick),
               text_color=color.white, text_size=tableSize)
    table.cell(dashboard, 2, 4, eventAnchorQuality + " " + str.tostring(math.round(eventAnchorScore)),
               text_color=getQualityColor(eventAnchorScore), text_size=tableSize)
    table.cell(dashboard, 3, 4, eventBarsStr + " | " + lastEventType,
               text_color=eventDisplayColor, text_size=tableSize)
    
    // Row 5: Divider
    table.cell(dashboard, 0, 5, "─────────────────────────────────────",
               text_color=color.gray, text_size=tableSize, text_halign=text.align_center)
    table.merge_cells(dashboard, 0, 5, 3, 5)
    
    // Row 6: Price Position (v1.2 FIX: Neutral color for N/A)
    highPosColor = priceVsHighVWAP == "ABOVE" ? i_bullColor : 
                   priceVsHighVWAP == "BELOW" ? i_bearColor : i_neutralColor
    lowPosColor = priceVsLowVWAP == "ABOVE" ? i_bullColor :
                  priceVsLowVWAP == "BELOW" ? i_bearColor : i_neutralColor
    
    table.cell(dashboard, 0, 6, "POSITION", text_color=color.gray, text_size=tableSize)
    table.cell(dashboard, 1, 6, "vs H: " + priceVsHighVWAP,
               text_color=highPosColor, text_size=tableSize)
    table.cell(dashboard, 2, 6, "vs L: " + priceVsLowVWAP,
               text_color=lowPosColor, text_size=tableSize)
    table.cell(dashboard, 3, 6, biasControl,
               text_color=biasColor, text_size=tableSize)
    
    // Row 7: Volume Flow & Structure
    flowColor = volumeFlowBullish ? i_bullColor : i_bearColor
    structColor = structureTrend == 1 ? i_bullColor : 
                  structureTrend == -1 ? i_bearColor : i_neutralColor
    
    table.cell(dashboard, 0, 7, "VOL FLOW", text_color=color.gray, text_size=tableSize)
    table.cell(dashboard, 1, 7, volumeFlowStr, text_color=flowColor, text_size=tableSize)
    table.cell(dashboard, 2, 7, "Structure", text_color=color.gray, text_size=tableSize)
    table.cell(dashboard, 3, 7, structureTrendStr, text_color=structColor, text_size=tableSize)
    
    // Row 8: Best Anchor Recommendation
    bestScore = math.max(highAnchorScore, lowAnchorScore, eventAnchorScore)
    bestAnchor = bestScore == highAnchorScore ? "STRUCT HIGH" :
                 bestScore == lowAnchorScore ? "STRUCT LOW" : "VOL EVENT"
    
    table.cell(dashboard, 0, 8, "BEST ANCHOR", text_color=color.yellow, text_size=tableSize)
    table.cell(dashboard, 1, 8, bestAnchor, text_color=color.white, text_size=tableSize)
    table.cell(dashboard, 2, 8, "Score: " + str.tostring(math.round(bestScore)),
               text_color=getQualityColor(bestScore), text_size=tableSize)
    table.cell(dashboard, 3, 8, getQualityStr(bestScore) + " QUALITY",
               text_color=getQualityColor(bestScore), text_size=tableSize)
```

---

### Section 8: Alert Conditions

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// ALERT CONDITIONS
// ═══════════════════════════════════════════════════════════════════════════

alertcondition(not na(pivotHigh), "New Swing High",
               "Swing High detected at {{close}} - Potential AVWAP anchor")

alertcondition(not na(pivotLow), "New Swing Low",
               "Swing Low detected at {{close}} - Potential AVWAP anchor")

highVolSwingHigh = not na(pivotHigh) and safeVolRatio(i_pivotLen) > i_spikeThreshold
highVolSwingLow = not na(pivotLow) and safeVolRatio(i_pivotLen) > i_spikeThreshold

alertcondition(highVolSwingHigh, "High Volume Swing High",
               "HIGH VOLUME Swing High - Strong resistance anchor")

alertcondition(highVolSwingLow, "High Volume Swing Low",
               "HIGH VOLUME Swing Low - Strong support anchor")

alertcondition(sellingClimax, "Selling Climax",
               "SELLING CLIMAX - Potential bottom, strong bullish anchor")

alertcondition(buyingClimax, "Buying Climax",
               "BUYING CLIMAX - Potential top, strong bearish anchor")

alertcondition(stoppingVolume, "Stopping Volume",
               "STOPPING VOLUME - Accumulation signal, bullish anchor")

alertcondition(spring, "Spring",
               "SPRING detected - False breakdown, bullish anchor")

alertcondition(upthrust, "Upthrust",
               "UPTHRUST detected - False breakout, bearish anchor")

alertcondition(ta.crossover(close, vwapFromLow), "Cross Above Low VWAP",
               "Price crossed ABOVE Low VWAP - Buyers taking control")

alertcondition(ta.crossunder(close, vwapFromLow), "Cross Below Low VWAP",
               "Price crossed BELOW Low VWAP - Sellers taking control")

alertcondition(ta.crossover(close, vwapFromHigh), "Cross Above High VWAP",
               "Price crossed ABOVE High VWAP - Strong bullish breakout")

alertcondition(ta.crossunder(close, vwapFromHigh), "Cross Below High VWAP",
               "Price crossed BELOW High VWAP - Resistance rejection")

highQualityAnchor = (highAnchorScore >= 70 and not na(pivotHigh)) or
                    (lowAnchorScore >= 70 and not na(pivotLow)) or
                    (eventAnchorScore >= 70 and currentVSA != "NONE")

alertcondition(highQualityAnchor, "High Quality Anchor",
               "HIGH QUALITY AVWAP anchor detected - Score 70+")
```

---

### Section 9: Integration Variables

```pinescript
// ═══════════════════════════════════════════════════════════════════════════
// INTEGRATION VARIABLES (For Four Pillars Pillar 2)
// ═══════════════════════════════════════════════════════════════════════════

integration_vwap_primary = not na(vwapFromLow) ? vwapFromLow :
                           not na(vwapFromEvent) ? vwapFromEvent :
                           not na(vwapFromHigh) ? vwapFromHigh : na

integration_bias = biasValue
integration_quality = math.max(highAnchorScore, lowAnchorScore, eventAnchorScore)
integration_has_vsa = barsFromEvent < 30 and lastEventType != "NONE"
integration_vol_flow = volumeFlowBullish ? 1 : -1
integration_structure = structureTrend
```

---

## BUILD CHECKLIST

### Phase 1: Foundation
- [ ] Create indicator file with all inputs (Section 1)
- [ ] Implement Structure Detection with history check (Section 2)
- [ ] Implement Volume classification and flow (Section 3)
- [ ] Test on RIVERUSDT 30min - verify swings detected

### Phase 2: VSA + VWAP
- [ ] Implement full VSA patterns (Section 3)
- [ ] Implement cumulative VWAP with backfill (Section 4)
- [ ] Implement quality scoring (Section 5)
- [ ] Test VSA detection and VWAP accuracy

### Phase 3: Dashboard + Polish
- [ ] Build dashboard with proper colors (Section 7)
- [ ] Add visual outputs (Section 6)
- [ ] Add alert conditions (Section 8)
- [ ] Final testing across multiple pairs

---

## TESTING CRITERIA

1. ✓ Swings detect within 2 bars of visual swing
2. ✓ VSA labels appear on correct patterns
3. ✓ VWAP lines calculate from anchor bar (not detection bar)
4. ✓ Dashboard shows "BUILDING..." until enough swing data
5. ✓ Dashboard shows "STALE" for old anchors
6. ✓ N/A values show neutral color (not red)
7. ✓ No label accumulation errors
8. ✓ Quality scores update dynamically

---

## SETTINGS REFERENCE

### 30min Crypto (Default)
| Parameter | Value |
|-----------|-------|
| Pivot Lookback | 5 |
| Volume MA | 20 |
| Volume Flow MA | 14 |
| Spike Threshold | 1.5 |
| Climax Threshold | 2.0 |
| Max Swing Age | 200 |

---

**Document Version**: 1.2  
**All Critical Fixes Applied**  
**Ready for Claude Code Execution**
