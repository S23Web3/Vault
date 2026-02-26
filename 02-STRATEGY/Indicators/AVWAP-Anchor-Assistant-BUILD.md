# AVWAP Anchor Assistant - Claude Code Build

**Version:** 1.2
**Date:** 2026-02-04
**Methodology:** Brian Shannon AVWAP + Wyckoff VSA
**Full Spec:** `C:\Users\User\Documents\Obsidian Vault\skills\indicators\avwap-anchor-assistant-BUILD-SPEC.md`

---

## PHILOSOPHY

### What is AVWAP?
Anchored Volume Weighted Average Price - VWAP calculated from a **specific point** rather than session start.

### Brian Shannon's Core Principle
> "The greater the volume of trading at a particular price level, the larger the number of participants with an emotional connection to that price level."

**Translation:** Where big volume traded = where traders are emotionally invested = where price reacts.

### Why This Matters for Trading
- Fixed VWAP (daily) is arbitrary - starts at midnight
- AVWAP from meaningful events captures **actual institutional commitment**
- Price remembers these levels because trapped traders defend them

### Shannon's Framework: Multiple AVWAPs
He does NOT pick "the best" AVWAP. He uses **three simultaneously**:

| AVWAP | Anchored To | Question It Answers |
|-------|-------------|---------------------|
| **Structure High** | Swing high | Where are sellers defending? (Resistance) |
| **Structure Low** | Swing low | Where are buyers defending? (Support) |
| **Volume Event** | Highest volume bar / VSA event | Where did institutions commit? |

These are **complementary views**, not competing signals.

---

## WHAT THIS INDICATOR DOES

**Problem it solves:** "Where should I anchor my AVWAP?"

**Answer:** It identifies high-quality anchor points automatically using:
1. **Structure** - Swing highs/lows (trapped traders)
2. **Volume** - VSA patterns (stopping volume, climax, spring, upthrust)
3. **Recency** - Fresh anchors > stale anchors
4. **Trend alignment** - Anchors that match structure trend

**Output:** Silent dashboard showing facts. Trader decides action.

---

## THREE PILLARS

### PILLAR A: STRUCTURE
Identifies swing highs/lows where traders are trapped.

```pinescript
// Core functions needed:
ta.pivothigh(high, pivotLen, pivotLen)  // Swing high detection
ta.pivotlow(low, pivotLen, pivotLen)    // Swing low detection

// Track:
- lastSwingHigh / lastSwingLow (prices)
- lastSwingHighBar / lastSwingLowBar (bar indices)
- prevSwingHigh / prevSwingLow (for HH/HL/LH/LL detection)
- structureTrend: HH+HL = bullish, LH+LL = bearish
```

### PILLAR B: VOLUME COMMITMENT
Identifies VSA patterns where institutions acted.

```pinescript
// Core calculations:
avgVol = ta.sma(volume, 20)
volRatio = volume / avgVol
spread = high - low
atr = ta.atr(14)
spreadRatio = spread / atr
closePosition = (close - low) / spread  // 0=low, 1=high

// VSA Patterns to detect:
- Stopping Volume: Down bar + volume spike + close off low
- Selling Climax: Down bar + wide spread + climax volume + close recovering
- Buying Climax: Up bar + wide spread + climax volume + close off high
- Spring: New low + close high + volume (false breakdown)
- Upthrust: New high + close low + volume (false breakout)
- No Supply: Down bar + narrow spread + low volume (bullish)
- No Demand: Up bar + narrow spread + low volume (bearish)
```

### PILLAR C: VWAP CALCULATION
Three VWAPs from three different anchors.

```pinescript
// Cumulative calculation (efficient):
var float cumPV = 0.0  // cumulative price × volume
var float cumV = 0.0   // cumulative volume

// On new anchor: reset and BACKFILL from anchor bar
if newAnchorDetected
    cumPV := 0.0
    cumV := 0.0
    for i = 1 to pivotLen  // backfill
        cumPV += hlc3[i] * volume[i]
        cumV += volume[i]

// Every bar: accumulate
cumPV += hlc3 * volume
cumV += volume

// VWAP = cumPV / cumV
vwap = cumV > 0 ? cumPV / cumV : na
```

**Critical:** Pivot detected at bar N, but actual swing was at bar N - pivotLen. Must backfill.

---

## ANCHOR QUALITY SCORING

| Weight | Factor | Logic |
|--------|--------|-------|
| 40% | VSA Event | Climax=100%, Stopping/Spring=85%, No Supply/Demand=60% |
| 25% | Volume at anchor | >1.5x avg = full, >1.2x = 60% |
| 20% | Recency | <20 bars = full, <50 = 50%, <100 = 25% |
| 15% | Trend alignment | High anchor + bearish trend = full, etc. |

**Quality levels:**
- HIGH: Score ≥ 70
- MEDIUM: Score 40-69
- LOW: Score < 40

---

## DASHBOARD OUTPUT

```
┌─────────────────────────────────────────────────────────────┐
│ AVWAP ANCHOR ASSISTANT                      STRONG BULL     │
├─────────────────────────────────────────────────────────────┤
│ ANCHOR      │ PRICE    │ QUALITY     │ INFO                │
├─────────────────────────────────────────────────────────────┤
│ Struct High │ 0.0325   │ MEDIUM 45   │ 35 bars | RESISTANCE│
│ Struct Low  │ 0.0298   │ HIGH 78     │ 12 bars | SUPPORT   │
│ Vol Event   │ 0.0305   │ HIGH 82     │ 8 bars | STOPPING   │
├─────────────────────────────────────────────────────────────┤
│ POSITION    │ vs H: BELOW │ vs L: ABOVE │ BUYERS           │
│ VOL FLOW    │ BULL FLOW   │ Structure   │ BULLISH (HH/HL)  │
├─────────────────────────────────────────────────────────────┤
│ BEST ANCHOR │ VOL EVENT   │ Score: 82   │ HIGH QUALITY     │
└─────────────────────────────────────────────────────────────┘
```

**Silent dashboard:** Shows facts only. No buy/sell signals. Trader interprets.

---

## CORE V6 FUNCTIONS REQUIRED

```pinescript
// Structure
ta.pivothigh(source, leftbars, rightbars)
ta.pivotlow(source, leftbars, rightbars)

// Volume/ATR
ta.sma(source, length)
ta.ema(source, length)
ta.atr(length)
ta.highest(source, length)
ta.lowest(source, length)

// VWAP cross detection
ta.crossover(source1, source2)
ta.crossunder(source1, source2)

// Types
type AnchorData
    float price
    int bar
    float score
    string quality

// Tables
table.new(position, columns, rows, ...)
table.cell(table, column, row, text, ...)
table.merge_cells(table, start_col, start_row, end_col, end_row)

// Lines
line.new(x1, y1, x2, y2, ...)
line.set_xy1(line, x, y)
line.set_xy2(line, x, y)

// Labels with cleanup
var label[] labelArray = array.new_label()
array.push(labelArray, newLabel)
while array.size(labelArray) > maxLabels
    label.delete(array.shift(labelArray))

// Alert conditions
alertcondition(condition, title, message)
```

---

## INPUT GROUPS

```pinescript
// Structure
i_pivotLen = input.int(5, "Pivot Lookback", group="PILLAR A: STRUCTURE")
i_maxSwingAge = input.int(200, "Max Swing Age", group="PILLAR A: STRUCTURE")

// Volume
i_volMaPeriod = input.int(20, "Volume MA", group="PILLAR B: VOLUME")
i_volFlowPeriod = input.int(14, "Volume Flow MA", group="PILLAR B: VOLUME")
i_spikeThreshold = input.float(1.5, "Spike Threshold", group="PILLAR B: VOLUME")
i_climaxThreshold = input.float(2.0, "Climax Threshold", group="PILLAR B: VOLUME")

// VWAP
i_showVWAPs = input.bool(true, "Show VWAP Lines", group="PILLAR C: VWAP")
i_vwapFromHigh = input.bool(true, "VWAP from High", group="PILLAR C: VWAP")
i_vwapFromLow = input.bool(true, "VWAP from Low", group="PILLAR C: VWAP")
i_vwapFromEvent = input.bool(true, "VWAP from Event", group="PILLAR C: VWAP")

// Dashboard
i_showDashboard = input.bool(true, "Show Dashboard", group="DASHBOARD")
i_dashPosition = input.string("Top Right", "Position", options=[...], group="DASHBOARD")
```

---

## CRITICAL FIXES APPLIED IN V1.2

| Issue | Fix |
|-------|-----|
| VWAP missing first bars | Backfill loop from anchor bar on pivot detection |
| Structure trend false positive | Show "BUILDING..." until enough swing history |
| 9999 displayed for stale | Show "STALE" text instead |
| N/A values wrong color | Use neutral color, not red |
| Label accumulation | Array management with while loop cleanup |

---

## INTEGRATION WITH FOUR PILLARS

This indicator exports values for Pillar 2 (VWAP Bias):

```pinescript
// Export variables (at end of indicator)
integration_vwap_primary = vwapFromLow  // or best available
integration_bias = biasValue            // -2 to +2
integration_quality = bestScore         // 0-100
integration_vol_flow = volFlowBullish ? 1 : -1
integration_structure = structureTrend  // -1, 0, 1
```

---

## TEST CHECKLIST

```
[ ] Compiles without errors in TradingView
[ ] Swings detect correctly (triangles at pivots)
[ ] VWAP lines start from anchor bar, not detection bar
[ ] VSA labels appear on correct patterns
[ ] Dashboard shows "BUILDING..." initially
[ ] Dashboard shows "STALE" for old anchors (>200 bars)
[ ] Quality scores update dynamically
[ ] No label accumulation (check after 100+ bars)
[ ] Alerts fire correctly
```

---

## FILE LOCATIONS

| File | Purpose |
|------|---------|
| `skills/indicators/avwap-anchor-assistant-BUILD-SPEC.md` | Full spec with complete code |
| `02-STRATEGY/Indicators/AVWAP-Anchor-Assistant-BUILD.md` | This build guide |
| `02-STRATEGY/Indicators/avwap_anchor_assistant_v1.pine` | Output file (to create) |

---

## BUILD APPROACH

1. Read full spec at `skills/indicators/avwap-anchor-assistant-BUILD-SPEC.md`
2. Implement section by section (9 sections total)
3. Test after each major section
4. Save to `02-STRATEGY/Indicators/avwap_anchor_assistant_v1.pine`

**Full implementation code is in the spec file.** This document is the philosophy and pointers.
