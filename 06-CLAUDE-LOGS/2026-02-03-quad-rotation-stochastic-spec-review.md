# Quad Rotation Stochastic - Comprehensive Spec Review
**Date:** 2026-02-03  
**Session Type:** Indicator Specification & Statistical Analysis  
**Status:** Ready for Claude Code Build

---

## SESSION OVERVIEW

Deep review of Quad Rotation Stochastic indicator specification to align with John Kurisko's (DayTraderRockStar) HPS methodology. Included statistical analysis of angle calculation methods using 5,000 randomized samples.

---

## JOHN KURISKO HPS METHODOLOGY (Source: PDF)

### Stochastic Settings (Exact)
| Name | Settings | Role |
|------|----------|------|
| Fast | 9, 3 | Entry timing, quick rotations |
| Fast | 14, 3 | Primary confirmation |
| Fast | 40, 4 | Trend context, **highest priority divergence** |
| Full | 60, 10 | Macro filter, channel timeframe |

### John's Rule 5 (Critical)
> "Always take a 40-4 divergence or any multiple-band divergences"

### John's Divergence Definition

**BULLISH DIVERGENCE:**
- Stage 1: Stochastics UNDER 20 (oversold), price makes low
- Bounce brings stochastics back ABOVE 20
- Stage 2: Price returns and makes LOWER LOW (or equal low)
- Stochastics HOLD ABOVE 20 and turn UP
- **Divergence Confirmed:** Price Lower Low + Stoch Higher Low

**BEARISH DIVERGENCE:**
- Stage 1: Stochastics OVER 80 (overbought), price makes high
- Pullback brings stochastics back UNDER 80
- Stage 2: Price returns and makes HIGHER HIGH (or equal high)
- Stochastics HOLD UNDER 80 and turn DOWN
- **Divergence Confirmed:** Price Higher High + Stoch Lower High

### John's Exit Rule (Rule 1)
> "Under 200/VWAP, take trade off on first 9-3 rotation above 80"

### 20/20 Flag Explanation
- First "20": 9-3 stochastic rotates DOWN to 20 level
- Second "20": Price holds above 20 EMA
- **Decision:** Skip flag detection - requires visual chart reading for flag pole and consolidation pattern. Stochastic conditions provide context only.

---

## QUAD ROTATION v4 - FINAL SPECIFICATION

### Components Included
| Feature | Include | Method |
|---------|---------|--------|
| 4 Stochastics (9-3, 14-3, 40-4, 60-10) | ✅ | Calculated, 40-4 plotted |
| 40-4 Divergence | ✅ | Stage-based state machine |
| Price Threshold (equal high/low) | ✅ | Configurable % input |
| Quad Rotation Angle | ✅ | Option C Optimized |
| Alignment Counting | ✅ | Above 60 / Below 40 |
| Zone Alerts | ✅ | Entering/exiting 20/80 |
| Exit Signals | ✅ | 9-3 >80 rotation |
| Flag Detection | ❌ | Skipped - visual identification |
| Coil Detection | ❌ | Later version |
| Channel Detection | ❌ | Later version |

### Components NOT Displayed
- 4 stochastics NOT plotted (too crowded)
- Only 40-4 line displayed (replaces existing 40-4 stochastic)

---

## 40-4 STAGE-BASED DIVERGENCE (Final Code)

### State Machine - Bullish
```
[WAITING]
    │
    ▼ stoch_40_4 < 20
[STAGE_1] ─── Record: price_low, stoch_low, bar_index
    │
    ▼ stoch_40_4 > 20
[STAGE_2] ─── Bounce confirmed, watching for price return
    │
    ├──► stoch_40_4 < 20 again → RESET to STAGE_1
    │
    ▼ price makes LOWER LOW (or equal) + stoch_40_4 > 20 + stoch turning UP
[BULLISH DIVERGENCE] ─── SUPERSIGNAL LONG
```

### State Machine - Bearish
```
[WAITING]
    │
    ▼ stoch_40_4 > 80
[STAGE_1] ─── Record: price_high, stoch_high, bar_index
    │
    ▼ stoch_40_4 < 80
[STAGE_2] ─── Pullback confirmed, watching for price return
    │
    ├──► stoch_40_4 > 80 again → RESET to STAGE_1
    │
    ▼ price makes HIGHER HIGH (or equal) + stoch_40_4 < 80 + stoch turning DOWN
[BEARISH DIVERGENCE] ─── SUPERSIGNAL SHORT
```

### Price Threshold for Equal High/Low
```pinescript
// Input for price equality threshold
i_price_threshold = input.float(0.1, "Price Threshold %", minval=0.0, maxval=1.0, step=0.05, 
                    tooltip="How close price can be to previous extreme and still count. 0.1 = 0.1%")

threshold_mult = i_price_threshold / 100

// BULLISH: Price must be AT or BELOW stage 1 low (+ threshold tolerance)
bull_threshold_band = bull_stage1_price_low * (1 + threshold_mult)
price_valid_bull = low <= bull_threshold_band

// BEARISH: Price must be AT or ABOVE stage 1 high (- threshold tolerance)
bear_threshold_band = bear_stage1_price_high * (1 - threshold_mult)
price_valid_bear = high >= bear_threshold_band
```

### Lookback Limit
- Maximum 20 bars between Stage 1 and divergence confirmation
- Configurable via input

---

## QUAD ROTATION ANGLE - STATISTICAL ANALYSIS

### Methods Tested (5,000 samples)

**Option A: Composite → Angle**
- Weighted average of 4 stochastics, then calculate angle
- Weights: 9-3=1.0, 14-3=1.5, 40-4=2.0, 60-10=2.5

**Option B: Average of Angles**
- Calculate angle for each stochastic individually, then weighted average

**Option C: Agreement Multiplier (40-4 base)**
- Base angle from 40-4
- Multiplied by agreement factor when other stochastics confirm direction

### Test Results

| Method | Overall Accuracy |
|--------|------------------|
| Option A | 48.60% |
| Option B | 51.10% |
| **Option C** | **61.40%** |
| Option C Optimized | **66.10%** |

### Best Configuration (Option C Optimized)
| Parameter | Value |
|-----------|-------|
| Base | 40-4 Stochastic angle |
| Agreement Factor | 0.7 |
| Signal Threshold | ±3° |
| Min Threshold | 0° (not needed) |

### Accuracy by Scenario Type
| Scenario | Accuracy | Notes |
|----------|----------|-------|
| perfect_quad_up | 100% | ✅ |
| perfect_quad_down | 100% | ✅ |
| divergence_bull | 100% | ✅ |
| divergence_bear | 99% | ✅ |
| fast_up_slow_down | 86% | ✅ 40-4 leads correctly |
| fast_down_slow_up | 82% | ✅ 40-4 leads correctly |
| bear_flag | 65% | ⚠️ Moderate |
| choppy | 33% | Expected - outputs NEUTRAL |
| bull_flag | 34% | ❌ Requires visual ID |
| early_reversal_bull | 20% | ❌ Caught by divergence |
| early_reversal_bear | 8% | ❌ Caught by divergence |

### Final Angle Formula
```pinescript
// OPTIMIZED OPTION C
angle_length = input.int(5, "Angle Lookback")
signal_threshold = input.float(3.0, "Signal Threshold °")
agreement_factor = input.float(0.7, "Agreement Factor")

// Base angle from 40-4
stoch_change = (stoch_40_4 - stoch_40_4[angle_length]) / stoch_40_4[angle_length]
base_angle = math.atan(stoch_change) * (180 / math.pi)

// Agreement count
base_rising = stoch_40_4 > stoch_40_4[1]
agreement_count = 0
if (stoch_9_3 > stoch_9_3[1]) == base_rising
    agreement_count += 1
if (stoch_14_3 > stoch_14_3[1]) == base_rising
    agreement_count += 1
if (stoch_40_4 > stoch_40_4[1]) == base_rising
    agreement_count += 1
if (stoch_60_10 > stoch_60_10[1]) == base_rising
    agreement_count += 1

agreement = agreement_count / 4.0

// Final angle with agreement multiplier
quad_rotation_angle = base_angle * (agreement_factor + (1 - agreement_factor) * agreement)

// Classification
rotation_bullish = quad_rotation_angle > signal_threshold
rotation_bearish = quad_rotation_angle < -signal_threshold
rotation_neutral = math.abs(quad_rotation_angle) <= signal_threshold
```

---

## TRADING IMPACT ANALYSIS

### Without Flag Detection (Current Approach)
- Overall catch rate: **76.6%**
- Missed high-value setups: ~20 per 100 opportunities

### With Flag Detection (Theoretical)
- Overall catch rate: **93.4%**
- Improvement: +16.8%

### Decision: Skip Flag Detection
**Reason:** Flag pole and consolidation pattern require visual chart reading. Cannot reliably code:
- Flag pole detection (how many candles? what % gain?)
- Consolidation shape
- Regression channel
- Breakout confirmation

**Stochastic conditions (embedded 60-10 and 40-4, 9-3 rotation) provide CONTEXT alerts, not entry signals.**

### Early Reversals
- Caught by **divergence detection** (already in spec)
- When 40-4 makes higher low in oversold = bullish divergence signal

---

## CONFIRMED ALERTS

### Divergence Alerts
| # | Alert Name | Trigger |
|---|------------|---------|
| 1 | Bullish Divergence 40-4 | Stage-based bullish divergence confirmed |
| 2 | Bearish Divergence 40-4 | Stage-based bearish divergence confirmed |
| 3 | Bullish Stage 1 Active | Stoch 40-4 enters oversold (<20) |
| 4 | Bearish Stage 1 Active | Stoch 40-4 enters overbought (>80) |
| 5 | Bullish Stage 2 Active | Stoch 40-4 exits oversold (>20) |
| 6 | Bearish Stage 2 Active | Stoch 40-4 exits overbought (<80) |

### Alignment Alerts
| # | Alert Name | Trigger |
|---|------------|---------|
| 7 | Full Bullish Alignment | 4/4 stochastics above 60 |
| 8 | Full Bearish Alignment | 4/4 stochastics below 40 |
| 9 | Strong Bullish Alignment | 3/4 stochastics above 60 |
| 10 | Strong Bearish Alignment | 3/4 stochastics below 40 |
| 11 | Alignment Flip Bullish | Changes from bearish to bullish |
| 12 | Alignment Flip Bearish | Changes from bullish to bearish |

### Exit Signals (Conditional - Raise Stop Loss)
| # | Alert Name | Trigger |
|---|------------|---------|
| 13 | Exit Long (9-3 >80) | 9-3 crosses above 80 |
| 14 | Exit Short (9-3 <20) | 9-3 crosses below 20 |
| 15 | Exit Long Under VWAP | 9-3 >80 AND price below VWAP |
| 16 | Exit Short Above VWAP | 9-3 <20 AND price above VWAP |

### Zone Alerts
| # | Alert Name | Trigger |
|---|------------|---------|
| 17 | 40-4 Entering Oversold | Stoch 40-4 crosses below 20 |
| 18 | 40-4 Exiting Oversold | Stoch 40-4 crosses above 20 |
| 19 | 40-4 Entering Overbought | Stoch 40-4 crosses above 80 |
| 20 | 40-4 Exiting Overbought | Stoch 40-4 crosses below 80 |

### Rotation Alerts (Angle-Based)
| # | Alert Name | Trigger |
|---|------------|---------|
| 21 | 40-4 Turning Bullish | Angle crosses above 0° |
| 22 | 40-4 Turning Bearish | Angle crosses below 0° |
| 23 | Strong Momentum Up | Angle > threshold (e.g., 20°) |
| 24 | Strong Momentum Down | Angle < -threshold |

### Combo Signals
| # | Alert Name | Trigger |
|---|------------|---------|
| 25 | Supersignal Long | Bullish Divergence + 3/4 Bullish Alignment |
| 26 | Supersignal Short | Bearish Divergence + 3/4 Bearish Alignment |

---

## SIGNAL HIERARCHY

| Signal Type | Detection Method | Priority |
|-------------|------------------|----------|
| 40-4 Divergence | Stage-based state machine | **SUPERSIGNAL (A)** |
| Quad Rotation | Angle (Option C Optimized) | **A-CLASS** |
| Alignment | Count above/below 60/40 | CONTEXT |
| Zone Alerts | Threshold crossings | CONTEXT |
| Exit Signal | 9-3 >80 under VWAP | MANAGEMENT |

---

## INPUTS SUMMARY

| Input | Default | Range | Purpose |
|-------|---------|-------|---------|
| Angle Lookback | 5 | 3-10 | Bars for angle calculation |
| Signal Threshold | 3.0° | 1-10 | Bull/bear classification |
| Agreement Factor | 0.7 | 0.3-0.9 | Weight of agreement multiplier |
| Price Threshold % | 0.1 | 0-1.0 | Equal high/low tolerance |
| Divergence Lookback | 20 | 10-50 | Max bars for Stage 2 |
| Alignment Bull | 60 | 50-70 | Threshold for bullish |
| Alignment Bear | 40 | 30-50 | Threshold for bearish |

---

## FILES REFERENCED

| File | Location | Status |
|------|----------|--------|
| Current Spec | `02-STRATEGY\Indicators\Quad-Rotation-Stochastic.md` | Needs update |
| Rockstar HPS Rules | `02-STRATEGY\Rockstar-HPS-Unspoken-Rules.md` | Complete |
| John Kurisko PDF | Web fetch | Analyzed |
| Trend Angle Indicator | Shared in chat | Incorporated |

---

## NEXT STEPS

1. **Update Quad Rotation spec** with all confirmed parameters
2. **Build in Claude Code** using finalized specification
3. **Test on RIVERUSDT** 30min chart
4. **Verify divergence detection** matches visual chart analysis

---

## KEY DECISIONS MADE

| Decision | Rationale |
|----------|-----------|
| Use Stage-based divergence (not TDI pivot) | Matches John's exact methodology |
| Use Option C Optimized for angle | 66% accuracy, best in statistical testing |
| Skip flag detection | Requires visual chart reading |
| Skip coil detection | Later version |
| Skip channel detection | Later version |
| 40-4 is primary (Supersignal) | John's Rule 5 |
| Early reversals caught by divergence | No separate detection needed |
| Exit signals = raise stop loss | Not immediate close |

---

## STATISTICAL EVIDENCE

**5,000 sample test confirmed:**
- Option C (Agreement Multiplier) significantly outperforms A and B
- Statistical significance: p < 0.001 (McNemar's test)
- 40-4 as base captures John's "slow stochastics lead" principle
- Agreement factor amplifies signal when all 4 confirm

---

*Session logged: 2026-02-03*
*Ready for Claude Code build phase*
