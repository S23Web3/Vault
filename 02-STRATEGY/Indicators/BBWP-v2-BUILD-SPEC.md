# BBWP v2 - Build Specification

**Version:** 2.0
**Date:** 2026-02-04
**Role:** Pillar 4 - Volatility Filter
**Base:** The_Caretaker's BBWP

---

## WHAT BBWP DOES

Measures the width of Bollinger Bands compared to history. That's it.

- Low BBWP = Bands tight (compressed)
- High BBWP = Bands wide (expanded)

**BBWP is NOT:**
- Entry signal
- Exit signal
- Exhaustion indicator
- Direction indicator

**BBWP IS:**
- A volatility state indicator
- Combined with other pillars for grade calculation

---

## OUTPUT STATES (6 TOTAL)

| State | Condition | Dashboard Output |
|-------|-----------|------------------|
| BLUE DOUBLE | BBWP extremely low (bar + spectrum) | `BLUE DOUBLE` |
| BLUE | BBWP low (spectrum only) | `BLUE` |
| MA CROSS UP | Normal range + BBWP crosses above MA | `MA CROSS UP` |
| MA CROSS DOWN | Normal range + BBWP crosses below MA | `MA CROSS DOWN` |
| NORMAL | Normal range, no MA cross | `NORMAL` |
| RED | BBWP high (spectrum only) | `RED` |
| RED DOUBLE | BBWP extremely high (bar + spectrum) | `RED DOUBLE` |

---

## GRADE POINTS (FOR FOUR PILLARS)

| State | Points |
|-------|--------|
| BLUE DOUBLE | +2 |
| BLUE | +1 |
| MA CROSS UP | +1 |
| MA CROSS DOWN | 0 |
| NORMAL | 0 |
| RED | +1 |
| RED DOUBLE | +1 |

**Note:** Red states are NOT negative. Valid trades can happen at red when momentum aligns.

---

## PARAMETERS

| Parameter | Default | Description |
|-----------|---------|-------------|
| Price Source | close | Source for BB calculation |
| Basis Length | 13 | BB period (scalping optimized) |
| Basis Type | SMA | MA type for BB basis |
| Lookback | 100 | BBWP percentile lookback |
| BBWP MA Length | 5 | MA of BBWP for crossover |
| BBWP MA Type | SMA | MA type |
| Extreme Low | 10 | Blue bar threshold |
| Extreme High | 90 | Red bar threshold |

---

## SPECTRUM COLOR LOGIC

From The_Caretaker's code:

```
BBWP 0-25%    → Blue shades (low volatility)
BBWP 25-50%   → Green shades
BBWP 50-75%   → Yellow shades  
BBWP 75-100%  → Red shades (high volatility)
```

---

## STATE DETECTION LOGIC

```pinescript
// Thresholds
extremeLow = 10
extremeHigh = 90
spectrumLowThresh = 25
spectrumHighThresh = 75

// Bar conditions (background alerts)
bluBar = bbwp <= extremeLow
redBar = bbwp >= extremeHigh

// Spectrum conditions
bluSpectrum = bbwp < spectrumLowThresh
redSpectrum = bbwp > spectrumHighThresh

// MA cross conditions
maCrossUp = ta.crossover(bbwp, bbwpMA)
maCrossDown = ta.crossunder(bbwp, bbwpMA)

// State determination (priority order)
string state = "NORMAL"

if bluBar and bluSpectrum
    state := "BLUE DOUBLE"
else if bluSpectrum
    state := "BLUE"
else if redBar and redSpectrum
    state := "RED DOUBLE"
else if redSpectrum
    state := "RED"
else if maCrossUp
    state := "MA CROSS UP"
else if maCrossDown
    state := "MA CROSS DOWN"
```

---

## INTEGRATION EXPORTS

```pinescript
// For Four Pillars dashboard
integration_bbwp_value = bbwp
integration_bbwp_state = state
integration_bbwp_points = state == "BLUE DOUBLE" ? 2 :
                          state == "BLUE" ? 1 :
                          state == "MA CROSS UP" ? 1 :
                          state == "RED" ? 1 :
                          state == "RED DOUBLE" ? 1 : 0

// Hidden plots for external access
plot(integration_bbwp_value, "bbwp_value", display=display.none)
plot(integration_bbwp_points, "bbwp_points", display=display.none)
```

---

## VISUAL OUTPUT

1. **BBWP Line** - Spectrum colored (blue→green→yellow→red)
2. **BBWP MA Line** - White
3. **Background** - Blue/Red at extremes
4. **Hlines** - 0, extremeLow, 50, extremeHigh, 100

---

## ALERTS

| Alert | Condition |
|-------|-----------|
| Blue Double | State changes to BLUE DOUBLE |
| Red Double | State changes to RED DOUBLE |
| MA Cross Up | State changes to MA CROSS UP |
| MA Cross Down | State changes to MA CROSS DOWN |

---

## FILE OUTPUT

```
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\bbwp_v2.pine
```
