# Layer 3 Test Results -- 2026-02-14 14:33 UTC


## Layer 3 Tests
```
======================================================================
Forward Returns Layer 3 Tests -- 2026-02-14 14:33 UTC
======================================================================

[Test 1] Output Columns
  PASS  fwd_atr exists
  PASS  column fwd_10_max_up_pct
  PASS  column fwd_10_max_down_pct
  PASS  column fwd_10_max_up_atr
  PASS  column fwd_10_max_down_atr
  PASS  column fwd_10_close_pct
  PASS  column fwd_10_direction
  PASS  column fwd_10_max_range_atr
  PASS  column fwd_10_proper_move
  PASS  column fwd_20_max_up_pct
  PASS  column fwd_20_max_down_pct
  PASS  column fwd_20_max_up_atr
  PASS  column fwd_20_max_down_atr
  PASS  column fwd_20_close_pct
  PASS  column fwd_20_direction
  PASS  column fwd_20_max_range_atr
  PASS  column fwd_20_proper_move
  PASS  original open preserved
  PASS  original high preserved
  PASS  original low preserved
  PASS  original close preserved
  PASS  original base_vol preserved
  PASS  new column count

[Test 2] Missing OHLCV
  PASS  ValueError mentions column
  PASS  ValueError raised

[Test 3] ATR Calculation
  PASS  atr[0] is NaN
  PASS  atr[1] is NaN
  PASS  atr[2] is NaN
  PASS  atr[3] is not NaN
  PASS  atr[3] approx 4.0

[Test 4] Sign Conventions
  PASS  fwd_10_max_up_pct >= 0
  PASS  fwd_10_max_down_pct <= 0
  PASS  fwd_10_max_up_atr >= 0
  PASS  fwd_10_max_down_atr >= 0
  PASS  fwd_20_max_up_pct >= 0
  PASS  fwd_20_max_down_pct <= 0
  PASS  fwd_20_max_up_atr >= 0
  PASS  fwd_20_max_down_atr >= 0

[Test 5] Last W Bars NaN
  PASS  last 10 bars of fwd_10 are NaN
  PASS  bar n-11 of fwd_10 is valid
  PASS  last 20 bars of fwd_20 are NaN
  PASS  bar n-21 of fwd_20 is valid

[Test 6] Known Forward Returns
  PASS  bar15 ATR=4.0
  PASS  bar15 max_up_pct=7.0
  PASS  bar15 max_down_pct=-7.0
  PASS  bar15 max_up_atr=1.75
  PASS  bar15 max_down_atr=1.75
  PASS  bar15 close_pct=-6.0
  PASS  bar15 direction=down
  PASS  bar15 max_range_atr=3.5
  PASS  bar15 proper_move=True

[Test 7] ATR Normalization
  PASS  ATR norm bar 34
  PASS  ATR norm bar 35
  PASS  ATR norm bar 36
  PASS  ATR norm bar 37
  PASS  ATR norm bar 38
  PASS  ATR norm bar 39
  PASS  ATR norm bar 40
  PASS  ATR norm bar 41
  PASS  ATR norm bar 42
  PASS  ATR norm bar 43

[Test 8] Direction Label
  PASS  positive close_pct -> up
  PASS  negative close_pct -> down
  PASS  zero close_pct -> flat

[Test 9] Proper Move
  PASS  ATR[19] approx 2.0
  PASS  bar19 range_atr >= 3.0
  PASS  bar19 proper_move=True

[Test 10] ATR Zero Handling
  PASS  ATR near 0 for flat data
  PASS  no inf in open
  PASS  no inf in high
  PASS  no inf in low
  PASS  no inf in close
  PASS  no inf in fwd_atr
  PASS  no inf in fwd_5_max_up_pct
  PASS  no inf in fwd_5_max_down_pct
  PASS  no inf in fwd_5_max_up_atr
  PASS  no inf in fwd_5_max_down_atr
  PASS  no inf in fwd_5_close_pct
  PASS  no inf in fwd_5_max_range_atr

[Test 11] Custom Windows
  PASS  column fwd_5_max_up_pct
  PASS  column fwd_5_max_down_pct
  PASS  column fwd_5_max_up_atr
  PASS  column fwd_5_max_down_atr
  PASS  column fwd_5_close_pct
  PASS  column fwd_5_direction
  PASS  column fwd_5_max_range_atr
  PASS  column fwd_5_proper_move
  PASS  column fwd_30_max_up_pct
  PASS  column fwd_30_max_down_pct
  PASS  column fwd_30_max_up_atr
  PASS  column fwd_30_max_down_atr
  PASS  column fwd_30_close_pct
  PASS  column fwd_30_direction
  PASS  column fwd_30_max_range_atr
  PASS  column fwd_30_proper_move
  PASS  no fwd_10 columns
  PASS  no fwd_20 columns

[Test 12] Real Parquet (RIVERUSDT 5m)
  Loaded 32,762 5m bars
  PASS  fwd_atr > 0
  PASS  max_down_pct mean < 0
  PASS  proper_move 5-80%
  PASS  direction ~40-60% up
  PASS  no inf in any numeric column

======================================================================
RESULTS: 102 PASS / 0 FAIL
======================================================================
```


## Layer 3 Debug Validator
```
======================================================================
Forward Returns Layer 3 Debug & Math Validator -- 2026-02-14 14:33 UTC
======================================================================

[Debug 1] ATR Calculation -- Manual Verification
  PASS  TR[0]=NaN (no prev_close)
  PASS  ATR[1]=NaN
  PASS  ATR[2]=NaN
  PASS  ATR[3] not NaN
  PASS  ATR[3] approx 5.0
  PASS  ATR[4] approx 5.0
  PASS  ATR[5] approx 5.0
  PASS  ATR[6] approx 5.0
  PASS  ATR[7] approx 5.0
  PASS  ATR[8] approx 5.0
  PASS  ATR[9] approx 5.0

[Debug 2] Forward Return Exact Values -- Audit-Verified
  PASS  bar15 ATR=4.0
  PASS  bar15 max_up_pct = 7.0
  PASS  bar15 max_down_pct = -7.0
  PASS  bar15 max_up_atr = 1.75
  PASS  bar15 max_down_atr = 1.75
  PASS  bar15 close_pct = -6.0
  PASS  bar15 direction = down
  PASS  bar15 max_range_atr = 3.5
  PASS  bar15 proper_move = True
  PASS  bar16 window=4 is NaN
  PASS  bar16 ATR=5.0
  PASS  bar16 max_up_pct = 3.883495
  PASS  bar16 max_down_pct = -9.708738
  PASS  bar16 max_up_atr = 0.8
  PASS  bar16 max_down_atr = 2.0
  PASS  bar16 close_pct = -8.737864
  PASS  bar16 direction = down
  PASS  bar16 max_range_atr = 2.8
  PASS  bar16 proper_move = False

[Debug 3] Sign Conventions -- Global Invariants
  PASS  max_up_pct always >= 0
  PASS  max_down_pct always <= 0
  PASS  max_up_atr always >= 0
  PASS  max_down_atr always >= 0
  PASS  max_range_atr always >= 0
  PASS  no inf in open
  PASS  no inf in high
  PASS  no inf in low
  PASS  no inf in close
  PASS  no inf in base_vol
  PASS  no inf in fwd_atr
  PASS  no inf in fwd_10_max_up_pct
  PASS  no inf in fwd_10_max_down_pct
  PASS  no inf in fwd_10_max_up_atr
  PASS  no inf in fwd_10_max_down_atr
  PASS  no inf in fwd_10_close_pct
  PASS  no inf in fwd_10_max_range_atr

[Debug 4] Edge Cases
  PASS  flat: no inf in open
  PASS  flat: no inf in high
  PASS  flat: no inf in low
  PASS  flat: no inf in close
  PASS  flat: no inf in base_vol
  PASS  flat: no inf in fwd_atr
  PASS  flat: no inf in fwd_5_max_up_pct
  PASS  flat: no inf in fwd_5_max_down_pct
  PASS  flat: no inf in fwd_5_max_up_atr
  PASS  flat: no inf in fwd_5_max_down_atr
  PASS  flat: no inf in fwd_5_close_pct
  PASS  flat: no inf in fwd_5_max_range_atr
  PASS  window=1 bar0 max_up_pct
  PASS  window=1 last bar NaN
  PASS  window>len: all NaN
  PASS  last 10 bars NaN
  PASS  bar 89 valid

[Debug 5] Cross-Validate Real Data (L1+L2+L3)

  State x Forward Return Summary:
  State                 range_atr     up_atr   down_atr    proper%
  BLUE_DOUBLE               3.342      1.754      1.588      48.7%
  BLUE                      3.328      1.738      1.589      45.9%
  MA_CROSS_UP               3.507      1.823      1.684      49.7%
  NORMAL                    3.377      1.707      1.671      48.6%
  MA_CROSS_DOWN             3.345      1.733      1.612      46.1%
  RED                       3.474      1.737      1.737      51.0%
  RED_DOUBLE                3.795      2.060      1.735      60.0%
  INFO  BLUE_DOUBLE range <= NORMAL range -- BD=3.342, NORMAL=3.377 (hypothesis not confirmed)

  Validated 32,738 bars across L1+L2+L3

[Debug 6] _forward_max Vectorized Trace
  PASS  fwd_max[0]=30
  PASS  fwd_max[1]=40
  PASS  fwd_max[2]=50
  PASS  fwd_max[3]=NaN
  PASS  fwd_max[4]=NaN
  PASS  fwd_min[0]=20
  PASS  fwd_min[1]=30
  PASS  fwd_min[2]=40

======================================================================
DEBUG RESULTS: 72 PASS / 0 FAIL
======================================================================
```


## Layer 3 Sanity Check
```
======================================================================
Forward Returns Layer 3 Sanity Check -- 2026-02-14 14:33 UTC
======================================================================

  Input: 32,762 bars (5m)
  Runtime: 0.02s (2,151,865 bars/sec)

--- ATR Distribution ---
  Mean:  0.2623 (1.58% of close)
  P50:   0.0871 (1.37%)
  P90:   0.7008 (2.87%)

--- Window 10 (32,752 valid bars, 10 NaN) ---
  max_up_pct:   mean=2.70  P50=1.66  P90=6.34
  max_down_pct: mean=-2.51  P50=-1.57  P10=-5.89
  max_up_atr:   mean=1.788  P50=1.317  P90=3.840
  max_down_atr: mean=1.658  P50=1.280  P90=3.490
  range_atr:    mean=3.446  P50=2.994  P90=5.513
  close_pct:    mean=0.099  std=3.700
  direction:    up=48.9%  down=50.7%  flat=0.4%
  proper_move:  49.8%

--- Window 20 (32,742 valid bars, 20 NaN) ---
  max_up_pct:   mean=3.89  P50=2.37  P90=9.34
  max_down_pct: mean=-3.52  P50=-2.24  P10=-8.42
  max_up_atr:   mean=2.620  P50=1.885  P90=5.752
  max_down_atr: mean=2.363  P50=1.794  P90=4.982
  range_atr:    mean=4.983  P50=4.248  P90=8.191
  close_pct:    mean=0.198  std=5.289
  direction:    up=48.8%  down=50.9%  flat=0.3%
  proper_move:  79.8%

--- NaN Counts ---
  fwd_atr                            14
  fwd_10_max_up_pct                  10
  fwd_10_max_down_pct                10
  fwd_10_max_up_atr                  24
  fwd_10_max_down_atr                24
  fwd_10_close_pct                   10
  fwd_10_direction                   10
  fwd_10_max_range_atr               24
  fwd_10_proper_move                 24
  fwd_20_max_up_pct                  20
  fwd_20_max_down_pct                20
  fwd_20_max_up_atr                  34
  fwd_20_max_down_atr                34
  fwd_20_close_pct                   20
  fwd_20_direction                   20
  fwd_20_max_range_atr               34
  fwd_20_proper_move                 34

======================================================================
SANITY CHECK COMPLETE
======================================================================
```
