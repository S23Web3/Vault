# Four Pillars Strategy - ACTUAL Implementation (v3.8.4)
**Date:** 2026-02-16  
**Purpose:** Accurate documentation of current live system  
**Source:** signals/state_machine.py, signals/four_pillars.py

---

## Signal Pipeline Architecture

```
OHLCV Data
  ↓
compute_all_stochastics(df, params)
  ↓ (adds: stoch_9, stoch_14, stoch_40, stoch_60, stoch_60_d)
compute_clouds(df, params)
  ↓ (adds: ema5/12/34/50/72/89, cloud positions, price_pos)
compute_atr(df, params)
  ↓ (adds: atr column via Wilder's RMA)
FourPillarsStateMachine.process_bar()
  ↓ (outputs: long_a/b/c, short_a/b/c, reentry signals)
Signal DataFrame
```

---

## Component 1: Stochastics (Entry Timing)

### Four Raw K Values (No Smoothing)

**stoch_9 (Entry Trigger):**
- Purpose: Initiates setup when crosses below 25 (LONG) or above 75 (SHORT)
- Calculation: Raw K over 9 bars
- Formula: `100 * (close - lowest_9) / (highest_9 - lowest_9)`

**stoch_14 (Primary Confirmation):**
- Purpose: First confirmation signal
- Threshold: Must go below 30 (LONG) or above 70 (SHORT) during setup
- Weight: Required for Grade C, contributes to Grade A/B

**stoch_40 (Divergence Detection):**
- Purpose: Secondary confirmation
- Threshold: Must go below 30 (LONG) or above 70 (SHORT) during setup
- Weight: Contributes to Grade A/B

**stoch_60 (Macro Filter):**
- Purpose: Tertiary confirmation
- Threshold: Must go below 25 (LONG) or above 75 (SHORT) during setup
- Weight: Contributes to Grade A/B

**stoch_60_d (D Line Filter - Optional):**
- Purpose: Additional filter to prevent counter-trend entries
- Calculation: 10-period SMA of stoch_60
- Filter: LONG requires D > 20, SHORT requires D < 80
- Default: DISABLED (use_60d = False)

### Critical Note
All stochastics are RAW K values with NO SMA smoothing. This differs from standard indicator implementations that apply smoothing.

---

## Component 2: Ripster EMA Clouds (Trend Context)

### Cloud 2 (5/12 EMA) - Re-Entry System
**Purpose:** Fast-reaction cloud for re-entry signals
**Calculation:**
- ema5 = EMA(close, 5)
- ema12 = EMA(close, 12)
- cloud2_bull = ema5 > ema12
- cloud2_top = max(ema5, ema12)
- cloud2_bottom = min(ema5, ema12)

**Re-Entry Logic:**
- price_cross_above_cloud2: Price crosses above cloud2_top
- price_cross_below_cloud2: Price crosses below cloud2_bottom
- Triggers within 10 bars of last entry signal

### Cloud 3 (34/50 EMA) - DIRECTIONAL FILTER (ALWAYS ON)
**Purpose:** Primary trend filter - PREVENTS counter-trend trades
**Calculation:**
- ema34 = EMA(close, 34)
- ema50 = EMA(close, 50)
- cloud3_bull = ema34 > ema50
- cloud3_top = max(ema34, ema50)
- cloud3_bottom = min(ema34, ema50)

**Price Position (price_pos):**
```
+1 = Price ABOVE cloud3_top (bullish zone)
 0 = Price INSIDE cloud (neutral zone)
-1 = Price BELOW cloud3_bottom (bearish zone)
```

**CRITICAL FILTER RULES:**
- LONG trades: price_pos MUST be >= 0 (above or inside Cloud 3)
- SHORT trades: price_pos MUST be <= 0 (below or inside Cloud 3)
- This is NON-NEGOTIABLE and ALWAYS ENFORCED

### Cloud 4 (72/89 EMA) - Major Trend
**Purpose:** Planned for trailing exits (not yet implemented in v3.8.4)
**Calculation:**
- ema72 = EMA(close, 72)
- ema89 = EMA(close, 89)
- cloud4_bull = ema72 > ema89

**Planned Usage:**
- Trailing SL = cloud4_bottom - (atr × offset) for LONG
- Expected 8x profit improvement vs static SL

---

## Component 3: ATR (Volatility Measurement)

**Calculation Method:** Wilder's RMA (Exponential smoothing)
```
TR = max(H-L, |H-prevC|, |L-prevC|)
ATR[0] = average(TR[0:14])
ATR[i] = (ATR[i-1] × 13 + TR[i]) / 14
```

**Usage:**
- Initial SL distance: entry ± (sl_mult × ATR)
- TP distance: entry ± (tp_mult × ATR) if enabled
- BE raise trigger: price moves (be_trigger_atr × ATR)
- AVWAP band width: avwap_band_mult × ATR

---

## Entry Signal State Machine

### Two-Stage Process (Per Direction)

**STAGE 0: Idle / Waiting**
```
Condition: Monitoring stoch_9
Trigger to Stage 1:
  LONG:  stoch_9 < cross_level (25)
  SHORT: stoch_9 > (100 - cross_level) = 75
Action: Record bar_index, reset confirmation flags
```

**STAGE 1: Setup Window (Max 10 Bars)**
```
Active Monitoring:
  LONG:
    - Track if stoch_14 < zone_level (30) → long_14_seen
    - Track if stoch_40 < zone_level (30) → long_40_seen
    - Track if stoch_60 < cross_level (25) → long_60_seen
  
  SHORT:
    - Track if stoch_14 > zone_high (70) → short_14_seen
    - Track if stoch_40 > zone_high (70) → short_40_seen
    - Track if stoch_60 > cross_high (75) → short_60_seen

Timeout: After 10 bars → return to Stage 0 (no signal)

Exit Trigger:
  LONG:  stoch_9 crosses BACK ABOVE cross_level (25)
  SHORT: stoch_9 crosses BACK BELOW cross_high (75)
```

**STAGE 1 Exit → Signal Classification:**
```
confirmations = count of (14_seen, 40_seen, 60_seen) = 0-3

Grade A (Best):
  confirmations == 3
  AND cloud3_ok (price_pos filter passed)
  AND d_ok (D-line filter passed, if enabled)

Grade B (Good):
  confirmations >= 2
  AND allow_b_trades = True
  AND cloud3_ok
  AND d_ok

Grade C (Marginal):
  14_seen = True (at least stoch_14 confirmed)
  AND allow_c_trades = True
  AND price_pos == +1 (LONG) or -1 (SHORT)
  (Price must be OUTSIDE Cloud 3, not just above/below)
```

### Filter Details

**cloud3_ok (Directional Filter):**
```
LONG:  price_pos >= 0  (NOT below Cloud 3)
SHORT: price_pos <= 0  (NOT above Cloud 3)
```

**d_ok (D-Line Filter - Optional):**
```
LONG:  stoch_60_d > 20
SHORT: stoch_60_d < 80
Default: DISABLED (use_60d = False)
```

---

## Grade Classification System

### Grade A - Strongest Entry (All 4 Pillars Aligned)

**Requirements:**
1. stoch_9 crossed trigger level AND crossed back (setup complete)
2. stoch_14 entered extreme zone during setup
3. stoch_40 entered extreme zone during setup
4. stoch_60 entered extreme zone during setup
5. Cloud 3 directional filter passed
6. D-line filter passed (if enabled)

**Interpretation:**
- All momentum timeframes confirmed
- Trend filter aligned
- Highest probability setup
- Largest position size recommended

### Grade B - Strong Entry (3 of 4 Confirmed)

**Requirements:**
1. At least 2 of (stoch_14, stoch_40, stoch_60) confirmed
2. allow_b_trades = True (user setting)
3. Cloud 3 filter passed
4. D-line filter passed (if enabled)

**Interpretation:**
- Majority momentum confirmation
- Still trend-aligned
- Medium position size

**Typical Patterns:**
- 14 + 40 confirmed (fast momentum)
- 40 + 60 confirmed (slow momentum)
- 14 + 60 confirmed (mixed momentum)

### Grade C - Weak Entry (Minimal Confirmation)

**Requirements:**
1. Only stoch_14 confirmed (9 triggered, 14 entered zone)
2. allow_c_trades = True (user setting)
3. Price OUTSIDE Cloud 3 (price_pos = +1 or -1, NOT 0)
4. NO Cloud 3 bull/bear requirement
5. NO D-line requirement

**Interpretation:**
- Minimal confirmation
- Price must be in strong trend (outside cloud)
- Smallest position size
- Higher risk of false signals

**Key Difference:**
- Grade C bypasses Cloud 3 directional filter
- Only requires price be outside the cloud (strong trend)
- More aggressive than A/B

---

## Re-Entry System

### Cloud 2 Re-Entry (Default: ENABLED)

**Trigger Conditions:**
```
LONG Re-Entry:
  - Previous entry signal fired within last 10 bars
  - Price crosses ABOVE Cloud 2 top (5/12 EMA)
  - No new primary entry signal this bar

SHORT Re-Entry:
  - Previous entry signal fired within last 10 bars
  - Price crosses BELOW Cloud 2 bottom (5/12 EMA)
  - No new primary entry signal this bar
```

**Purpose:**
- Catches continuation after brief pullback
- Uses fast Cloud 2 as support/resistance
- Maintains exposure in strong trends

**Window:**
- reentry_lookback = 10 bars (default)
- Countdown starts from last A/B/C signal
- Window expires after 10 bars

---

## ADD Signals (Currently Not Used)

**Purpose:** Planned for future pyramiding logic

**LONG ADD Trigger:**
```
stoch_9 > add_zone_long (30)
AND stoch_40 > add_mid_long (48)
AND stoch_60 > add_mid_long (48)
```

**SHORT ADD Trigger:**
```
stoch_9 < add_zone_short (70)
AND stoch_40 < add_mid_short (52)
AND stoch_60 < add_mid_short (52)
```

**Status:** Signal generated but NOT acted upon in backtester v384

---

## Parameter Reference

### Stochastic Settings
```
stoch_k1:         9   (entry trigger)
stoch_k2:        14   (primary confirmation)
stoch_k3:        40   (divergence)
stoch_k4:        60   (macro)
stoch_d_smooth:  10   (D-line smoothing)
```

### Signal Logic Settings
```
cross_level:     25   (entry trigger threshold)
zone_level:      30   (confirmation threshold)
stage_lookback:  10   (max bars in setup window)
reentry_lookback: 10  (re-entry window after signal)
```

### Cloud Settings
```
cloud2_fast:      5   (re-entry cloud)
cloud2_slow:     12
cloud3_fast:     34   (directional filter)
cloud3_slow:     50
cloud4_fast:     72   (planned trailing)
cloud4_slow:     89
```

### Trade Enablement
```
allow_b_trades:    True   (enable Grade B)
allow_c_trades:    True   (enable Grade C)
b_open_fresh:      True   (B/C can open fresh, not just add)
cloud2_reentry:    True   (enable re-entry signals)
use_60d:          False   (D-line filter disabled)
```

### ATR Settings
```
atr_length:       14    (Wilder's RMA period)
```

---

## Signal Output Columns

### Added by compute_signals()

**Stochastics:**
- stoch_9
- stoch_14
- stoch_40
- stoch_60
- stoch_60_d

**Clouds:**
- ema5, ema12, ema34, ema50, ema72, ema89
- cloud2_bull, cloud3_bull, cloud4_bull
- cloud2_top, cloud2_bottom
- cloud3_top, cloud3_bottom
- price_pos (-1, 0, +1)
- cloud3_allows_long, cloud3_allows_short
- price_cross_above_cloud2, price_cross_below_cloud2

**ATR:**
- atr

**Entry Signals:**
- long_a, long_b, long_c
- short_a, short_b, short_c
- reentry_long, reentry_short

**Note:** add_long and add_short signals exist in state machine but are NOT added to DataFrame (reserved for future use)

---

## Critical Rules Summary

**1. Cloud 3 Filter is NON-NEGOTIABLE**
- LONG impossible if price_pos < 0
- SHORT impossible if price_pos > 0
- This prevents ALL counter-trend setups for A/B grades

**2. Grade C Bypasses Cloud 3 Direction**
- Only requires price_pos != 0 (outside cloud)
- Allows counter-trend if price in strong trend zone
- Higher risk, smallest position size

**3. Confirmation Window is Limited**
- 10 bars max in Stage 1
- If stoch_9 doesn't cross back, setup expires
- Prevents stale signals

**4. Re-Entry Independent of Primary Signals**
- Uses Cloud 2 crossovers only
- 10-bar window after last primary signal
- Does NOT re-trigger if new A/B/C fires

**5. All Stochastics are Raw K (No Smoothing)**
- Faster reaction than smoothed versions
- More noise, but catches turns earlier
- D-line is the only smoothed component

---

## Differences from Common Implementations

**What This System Does DIFFERENTLY:**

1. **No AVWAP in Entry Logic**
   - AVWAP only used for exits and trailing
   - Entry is pure stochastic + cloud filter

2. **Two-Stage State Machine**
   - Stage 0: Wait for trigger
   - Stage 1: Collect confirmations during window
   - Not instant signal on cross

3. **Cloud 3 Always Enforced**
   - Cannot disable directional filter for A/B
   - Strong trend-following bias
   - Rejects chop/range-bound setups

4. **Raw K Stochastics**
   - No %K/%D smoothing pairs
   - Faster but noisier signals
   - D-line only for optional filter

5. **Grade-Based Position Sizing**
   - Not all entries equal
   - A > B > C in size and priority
   - Allows risk adjustment per signal quality

---

## Common Misconceptions Corrected

**WRONG:**
- "AVWAP provides directional bias for entries"
- "D signal is for continuation trades"
- "BBW states affect entry signals"
- "All stochastics use standard %K/%D smoothing"

**CORRECT:**
- AVWAP only for exits (scale-out, trailing)
- D-line is an optional filter, not a signal
- BBW is for analysis only (v4 integration planned)
- All stochastics are raw K, no smoothing

---

**END OF STRATEGY DOCUMENTATION**

This reflects the ACTUAL code in production as of v3.8.4.
