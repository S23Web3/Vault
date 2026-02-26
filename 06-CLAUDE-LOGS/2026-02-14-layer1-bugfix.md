# Layer 1 Bugfix Log

## Build started: 2026-02-14 13:07 UTC

### Bugs Fixed
1. BUG 1+6: `_spectrum_color` rewrite -- NaN->None, 4 colors at 25/50/75 (drop orange)
2. BUG 7: `_detect_states` warmup gap -- split NaN check, bars with valid bbwp but NaN MA now detect states
3. BUG 8: `_percentrank_pine` NaN tolerance -- count valid values, min lookback//2
4. BUG 5: VWMA silent fallback -- added warnings.warn()
5. BUG 2: Dead NaN override -- removed redundant .loc[] assignments

### Tests Updated
- Test 3: Spectrum boundaries -> 4 colors, <=25 blue, >75 red, NaN->None
- Test 5: Deterministic MA cross persistence (crafted data, not random)
- Test 7: Real mutual exclusion checks (not tautology)
- Test 12 (NEW): Warmup gap consistency

### Sanity Check
- `scripts/sanity_check_bbwp.py` spectrum list: 5->4 colors

---

## Post-build results
### Test output (2026-02-14 13:07 UTC)
```
======================================================================
BBWP Layer 1 Tests — 2026-02-14 13:07 UTC
======================================================================

[Test 1] BB Width Calculation
  PASS  bbw_raw[12]
  PASS  bbw_raw[13]
  PASS  bbw_raw[14]
  PASS  bbw_raw[15]
  PASS  bbw_raw[16]
  PASS  bbw_raw[17]
  PASS  bbw_raw[18]
  PASS  bbw_raw[19]

[Test 2] Percentrank Matches Pine
  PASS  bbwp_value range
  PASS  bbwp_value varies

[Test 3] Spectrum Color Boundaries
  PASS  all spectrums valid (4 colors)
  PASS  NaN bbwp -> None spectrum
  PASS  bbwp<=25 -> blue
  PASS  bbwp>75 -> red

[Test 4] State Priority Order
  PASS  all states valid
  PASS  bbwp<=10 -> BLUE_DOUBLE
  PASS  bbwp>=90 -> RED_DOUBLE

[Test 5] MA Cross Persistence
  PASS  MA_CROSS_UP run <= timeout
  PASS  cross events sparse

[Test 6] MA Cross Cancelled by Spectrum
  PASS  no MA_CROSS in spectrum range

[Test 7] MA Cross Up Cancels Down
  PASS  never both cross events on same bar
  PASS  cross_up event -> MA_CROSS_UP state
  PASS  cross_down event -> MA_CROSS_DOWN state
  PASS  at least 1 cross event tested

[Test 8] Points Mapping
  PASS  BLUE_DOUBLE -> 2 pts
  PASS  BLUE -> 1 pts
  PASS  RED_DOUBLE -> 1 pts
  PASS  RED -> 1 pts
  PASS  MA_CROSS_UP -> 1 pts
  PASS  MA_CROSS_DOWN -> 0 pts
  PASS  NORMAL -> 0 pts

[Test 9] NaN Handling
  PASS  first basis_len-1 bars bbw_raw NaN
  PASS  no NaN in bbwp_state
  PASS  NaN bbwp -> NORMAL state
  PASS  NaN bbwp -> 0 points

[Test 10] Output Columns
  PASS  column bbwp_value exists
  PASS  column bbwp_ma exists
  PASS  column bbwp_bbw_raw exists
  PASS  column bbwp_spectrum exists
  PASS  column bbwp_state exists
  PASS  column bbwp_points exists
  PASS  column bbwp_is_blue_bar exists
  PASS  column bbwp_is_red_bar exists
  PASS  column bbwp_ma_cross_up exists
  PASS  column bbwp_ma_cross_down exists
  PASS  original column open preserved
  PASS  original column high preserved
  PASS  original column low preserved
  PASS  original column close preserved
  PASS  original column base_vol preserved
  PASS  column count correct
  PASS  bbwp_value is float
  PASS  bbwp_points is int-like
  PASS  bbwp_is_blue_bar is bool
  PASS  bbwp_spectrum is string
  PASS  bbwp_state is string

[Test 11] Real Parquet Sanity (RIVERUSDT 5m)
  Loaded 32,762 5m bars
  PASS  bbwp_value mean 40-60
  PASS  bbwp_value std 20-35
  PASS  NORMAL is most common (>10%)
  PASS  BLUE_DOUBLE is rare (<15%)
  PASS  RED_DOUBLE is rare (<15%)
  PASS  bbwp_points mean 0.2-1.0
  PASS  no NaN in bbwp_state
  PASS  MA cross_up events sparse (<5%)

  State distribution:
    NORMAL                17.9%
    BLUE_DOUBLE           14.5%
    MA_CROSS_UP           14.3%
    BLUE                  14.0%
    MA_CROSS_DOWN         13.8%
    RED_DOUBLE            13.1%
    RED                   12.4%

[Test 12] Warmup Gap Consistency
  PASS  warmup gap bars detect blue states
  PASS  warmup gap bars have blue spectrum
  PASS  NaN bbwp bars still NORMAL

======================================================================
RESULTS: 67 PASS / 0 FAIL
======================================================================

```

### Sanity check output (2026-02-14 13:07 UTC)
```
======================================================================
BBWP Layer 1 Sanity Check -- 2026-02-14 13:07 UTC
======================================================================

  Input: 32,762 bars (5m)
  Runtime: 0.33s (99,621 bars/sec)
  Valid BBWP bars: 32,662
  NaN warmup bars: 100

--- BBWP Value Distribution ---
  Mean:   48.8
  Std:    31.1
  Min:    0.0
  Max:    100.0
  P10:    6.0
  P25:    21.0
  P50:    48.0
  P75:    76.0
  P90:    93.0

--- Spectrum Distribution ---
  blue      9,608 ( 29.4%)
  green     7,487 ( 22.9%)
  yellow    7,221 ( 22.1%)
  red       8,346 ( 25.6%)

--- State Distribution ---
  BLUE_DOUBLE           4,736 ( 14.5%)
  BLUE                  4,578 ( 14.0%)
  MA_CROSS_UP           4,669 ( 14.3%)
  NORMAL                5,831 ( 17.9%)
  MA_CROSS_DOWN         4,502 ( 13.8%)
  RED                   4,052 ( 12.4%)
  RED_DOUBLE            4,294 ( 13.1%)

--- Points Distribution ---
  0 pts: 10,333 ( 31.6%)
  1 pts: 17,593 ( 53.9%)
  2 pts:  4,736 ( 14.5%)
  Mean: 0.829

--- MA Cross Events ---
  Cross Up events:   1,376
  Cross Down events: 1,281
  Cross Up %:   4.21%
  Cross Down %: 3.92%

--- Extreme Bars ---
  Blue bars (bbwp<=10): 4,736 (14.5%)
  Red bars (bbwp>=90):  4,294 (13.1%)

--- NaN Check ---
  bbwp_state                OK
  bbwp_points               OK
  bbwp_is_blue_bar          OK
  bbwp_is_red_bar           OK

======================================================================
SANITY CHECK COMPLETE
======================================================================

```
