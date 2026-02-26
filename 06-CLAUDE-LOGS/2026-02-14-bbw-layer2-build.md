# Layer 2 Build Log -- BBW Sequence Tracker

## Build started: 2026-02-14 13:16 UTC
## Tests passed: 2026-02-14 13:22 UTC

### Files Created
1. `signals/bbw_sequence.py` -- sequence tracking module (9 output columns)
2. `tests/test_bbw_sequence.py` -- 10 tests, 68 assertions
3. `scripts/sanity_check_bbw_sequence.py` -- RIVERUSDT distribution stats
4. `scripts/debug_bbw_sequence.py` -- math/logic validator (7 sections, 148 checks)

### Hotfix Applied
- SyntaxError in 3 generated files: Windows `\Users` path in docstrings triggered unicode escape error
- Fixed by replacing full Windows paths with relative paths in docstrings

---

### Test output (2026-02-14 13:22 UTC)
```
======================================================================
BBW Sequence Layer 2 Tests -- 2026-02-14 13:22 UTC
======================================================================

[Test 1] Output Columns — 13 PASS
[Test 2] Missing Layer 1 Columns — 2 PASS
[Test 3] NaN Spectrum Skipped — 7 PASS
[Test 4] Color Transitions — 10 PASS
[Test 5] Bars in Color — 3 PASS
[Test 6] Direction — 6 PASS
[Test 7] Skip Detection — 6 PASS
[Test 8] Pattern ID — 5 PASS
[Test 9] From Blue/Red Bars — 10 PASS
[Test 10] Real Parquet (RIVERUSDT 5m) — 6 PASS (32,662 valid bars)

======================================================================
RESULTS: 68 PASS / 0 FAIL
======================================================================
```

### Sanity check output (2026-02-14 13:22 UTC)
```
======================================================================
BBW Sequence Layer 2 Sanity Check -- 2026-02-14 13:22 UTC
======================================================================

  Input: 32,762 bars (5m)
  Layer 1: 0.34s (97,330 bars/sec)
  Layer 2: 0.03s (961,702 bars/sec)
  Total:   0.37s (88,385 bars/sec)
  Valid bars: 32,662
  NaN warmup: 100

--- Color Transitions ---
  Transitions: 6,320 (19.3%)

--- Direction Distribution ---
  flat            26,341 ( 80.6%)
  expanding        3,112 (  9.5%)
  contracting      3,208 (  9.8%)
  None                 1 (  0.0%)

--- Skip Detection ---
  Skips: 284 (0.9%)
    blue->yellow: 93
    yellow->blue: 70
    green->red: 66
    red->green: 29
    blue->red: 22

--- Top 10 Pattern IDs ---
  YGB     5,596 ( 17.1%)
  GYR     4,377 ( 13.4%)
  GBG     3,527 ( 10.8%)
  BGB     3,309 ( 10.1%)
  YRY     2,803 (  8.6%)
  BGY     2,327 (  7.1%)
  RYR     1,975 (  6.0%)
  RYG     1,950 (  6.0%)
  GYG     1,720 (  5.3%)
  YGY     1,422 (  4.4%)

--- Bars in Color (per spectrum) ---
  blue      mean=  8.9  median=    6  max=   62
  green     mean=  3.5  median=    2  max=   34
  yellow    mean=  3.7  median=    3  max=   31
  red       mean=  8.3  median=    6  max=   57

--- Bars in State (per state) ---
  BLUE_DOUBLE           mean=  5.2  median=    4  max=   33
  BLUE                  mean=  2.8  median=    2  max=   18
  MA_CROSS_UP           mean=  2.9  median=    2  max=   10
  NORMAL                mean=  3.3  median=    3  max=   16
  MA_CROSS_DOWN         mean=  3.0  median=    2  max=   13
  RED                   mean=  3.0  median=    2  max=   19
  RED_DOUBLE            mean=  5.7  median=    5  max=   28

--- Distance from Blue/Red ---
  from_blue: mean=15.2  P50=7  P90=44
  from_red:  mean=22.6  P50=12  P90=63

--- NaN Check (valid bars only) ---
  bbw_seq_bars_in_color          OK
  bbw_seq_bars_in_state          OK
  bbw_seq_color_changed          OK
  bbw_seq_skip_detected          OK

======================================================================
SANITY CHECK COMPLETE
======================================================================
```

### Debug validator output (2026-02-14 13:22 UTC)
```
======================================================================
BBW Sequence Layer 2 Debug & Math Validator -- 2026-02-14 13:22 UTC
======================================================================

[Debug 1] Helper Functions — All Color Pairs: 35 PASS
[Debug 2] Full Pipeline — 12-Bar Hand-Computed Vector: 66 PASS
[Debug 3] State Counter Independence: 2 PASS
[Debug 4] All Same Color Edge Case: 7 PASS
[Debug 5] None Gaps Mid-Stream: 15 PASS
[Debug 6] Cross-Validate Real Data: 10 PASS (32,662 bars)
[Debug 7] Constants Integrity: 13 PASS

======================================================================
DEBUG RESULTS: 148 PASS / 0 FAIL
======================================================================
```

### Summary
- Tests: **68/68 PASS**
- Debug: **148/148 PASS**
- Layer 2 speed: **961K bars/sec** (Layer 1: 97K, combined: 88K)
- Color transitions: 19.3% of bars (81% flat)
- Skips rare: 0.9% (mostly blue<->yellow)
- Top pattern: YGB (17.1%) -- contracting from yellow through green to blue
- Blue runs longest (mean 8.9 bars), green shortest (mean 3.5)
