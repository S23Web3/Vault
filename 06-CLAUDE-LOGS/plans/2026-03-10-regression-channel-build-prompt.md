# Regression Channel Module — Agent Build Prompt

**Date:** 2026-03-10
**Target agent:** Claude (new session)
**Output:** signals/regression_channel.py + scripts/test_regression_channel.py via build script

---

## Prompt

```
# Regression Channel Module — Build + Audit + Test (v2)

## Project
Four Pillars Trading System backtester.
Root: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\

## Mandatory First Step
Load the Python skill: /python

---

## Design Spec

### Two separate uses of the channel (do not conflate them)

USE 1 — Pre-Stage-1 channel (orderly decline gate):
  Computed over the pre_lookback bars immediately BEFORE Stage 1 entry
  (before stoch_9 crosses below 25 for the first time).
  Purpose: was there an orderly downtrend that caused the oversold reading?
  High R² + negative slope = orderly decline. Low R² = V-bottom or chop → gate fails.
  This channel is computed ONCE at Stage 1 entry and stored in the state machine.

  Default pre_lookback = 20 bars. Sweep range: 10 to 40 in steps of 5.
  Rationale:
    - 20 bars = 100 minutes on 5m = a meaningful short-to-medium crypto decline
    - 2x the stoch_9 window (9 bars) — a natural multiple
    - If the actual decline was only 8-10 bars (V-bottom), looking back 20 bars
      includes prior structure that dilutes slope and R² → gate correctly rejects it
    - If decline was 30-40 bars, the last 20 bars still show clean slope → gate passes
    - This lookback naturally discriminates V-bottoms without needing an explicit check

USE 2 — Anchored channel Stage1-to-Stage2 (lower-half position check):
  Computed over ALL bars from Stage 1 entry bar to Stage 2 exit bar (inclusive).
  Purpose: at Stage 2 exit, is price still near the structural low, or has it already
  bounced too far up?
  Do NOT apply R² gate here — the two-dip-plus-bounce shape produces low R² by
  construction even for perfect divergence setups. Only use center_at_last.

The combined filter at Stage 2 exit:
  Step 1: pre_stage1_gate must have passed at Stage 1 entry (stored result)
  Step 2: compute anchored channel (Stage1 bar to Stage2 exit bar)
  Step 3: price_in_lower_half(current_price, anchored_channel.center_at_last)
           → True  = price still below declining midline → ACCEPT entry
           → False = price bounced above declining midline → REJECT (entering late)

This implements the trading rule:
"if price is in the lower half of the channel AND stochastic is exiting oversold → enter"

---

## File: signals/regression_channel.py

### ChannelResult (namedtuple)
Fields:
  slope           float  — slope in price units per bar (raw, signed)
  slope_pct       float  — slope / mean_price (normalized, negative = descending)
  r_squared       float  — fit quality 0.0-1.0
  band_width_pct  float  — 2 * std(residuals) / mean_price
  center_at_last  float  — regression line value at the LAST bar of the fit window
  std_residuals   float  — std of residuals in price units

Zero ChannelResult: all fields = 0.0. Return this on degenerate input.

---

### Function 1: fit_channel(prices) -> ChannelResult
  Fit a linear regression to the given price array (list or numpy array).
  Minimum length: 3. Returns zero ChannelResult if len < 3 or degenerate.
  Pure NumPy only. No scipy, no pandas.

  center_at_last = regression line value at index len(prices) - 1.
  slope is in price units per bar (not normalized).
  slope_pct = slope / mean(prices).
  band_width_pct = 2 * std(residuals) / mean(prices).
  r_squared = 1 - SS_res / SS_tot. If SS_tot == 0: r_squared = 0.0.

---

### Function 2: extrapolate_center(channel, bars_elapsed) -> float
  Extend the regression center forward by bars_elapsed bars past the fit window.
  formula: channel.center_at_last + channel.slope * bars_elapsed
  bars_elapsed must be >= 0. Returns channel.center_at_last if bars_elapsed == 0.

---

### Function 3: price_in_lower_half(price, center) -> bool
  Returns True if price < center (strictly below regression midline).
  Returns False if price >= center.
  Equal to center counts as upper half (not lower).

---

### Function 4: compute_channel_anchored(all_prices, start_idx, end_idx) -> ChannelResult
  Compute regression over all_prices[start_idx : end_idx + 1].
  start_idx: bar index where Stage 1 began.
  end_idx: bar index of Stage 2 exit (the signal bar).
  Window must have >= 3 bars. Returns zero ChannelResult if window < 3 or degenerate.
  center_at_last = regression value at end_idx bar (the signal bar).

---

### Function 5: pre_stage1_gate(channel, r2_min=0.45, slope_pct_max=-0.001) -> bool
  Returns True if both:
    channel.r_squared > r2_min           (orderly decline, not V-bottom)
    channel.slope_pct < slope_pct_max    (price was actually declining)
  slope_pct_max is NEGATIVE. slope_pct < -0.001 means price declined at least
  0.1% per bar on average over the lookback. At 20 bars this is a ~2% total decline minimum.
  Returns False otherwise.

---

## Integration Context (standalone module — state machine integration described in docstring only)

The state machine will use this module as follows. Document this in a module-level
comment in regression_channel.py but do NOT write any state_machine.py code.

  At Stage 1 entry (stoch_9 crosses below 25 for first time):
    self.stage1_bar = current_bar_index
    pre_window = prices[current_bar - pre_lookback : current_bar + 1]
    self.pre_ch = fit_channel(pre_window)
    self.ch_gate_passed = pre_stage1_gate(self.pre_ch)

  At Stage 2 exit (stoch_9 crosses above 25, divergence confirmed):
    if not self.ch_gate_passed:
        reject signal
    anchored = compute_channel_anchored(prices, self.stage1_bar, current_bar)
    if price_in_lower_half(current_price, anchored.center_at_last):
        fire entry signal
    else:
        reject signal

---

## File: scripts/build_regression_channel.py

Writes signals/regression_channel.py then scripts/test_regression_channel.py.
After writing each file: py_compile.compile(path, doraise=True) immediately.
Prints full absolute path + [PASS] or [FAIL] for each file.
Checks file existence before writing — aborts if file already exists.
Does NOT run the test script.

---

## File: scripts/test_regression_channel.py

Plain Python. No pytest. Each test prints name, values checked, and PASS or FAIL.

### Test 1: Orderly decline — pre-Stage-1 use case
  30 bars: linear decline from 100.0 to 94.0, plus numpy random noise with seed=42, scale=0.05.
  Call fit_channel(prices).
  Expected: r_squared > 0.85, slope_pct < -0.001, pre_stage1_gate returns True.
  Print r_squared, slope_pct, gate result.

### Test 2: V-bottom — should fail gate
  15 bars flat at 100.0, bars 15-16 drop to 90.0, bars 17-18 recover to 100.0.
  Total 19 bars. Call fit_channel(prices).
  Expected: r_squared < 0.25, pre_stage1_gate returns False.
  Print r_squared, gate result.

### Test 3: Sideways chop — should fail gate
  30 bars oscillating using sin wave with amplitude 0.5, centered at 100.0.
  Expected: abs(slope_pct) < 0.0005, r_squared < 0.2, pre_stage1_gate returns False.

### Test 4: Anchored channel — lower half ACCEPT
  Two-dip scenario, 20 bars total:
    bars 0-4:   100.0 declining to 96.0 (Stage 1 dip)
    bars 5-9:   96.0 bouncing to 99.0 (cooldown)
    bars 10-14: 99.0 declining to 93.0 (Stage 2 dip — lower low)
    bars 15-19: 93.0 recovering to 94.0 (Stage 2 exit — small bounce)
  Call compute_channel_anchored(prices, start_idx=0, end_idx=19).
  At Stage 2 exit: current_price = 94.0, center = anchored.center_at_last.
  Expected: price_in_lower_half(94.0, center) == True
  Print center_at_last, price, result.

### Test 5: Anchored channel — upper half REJECT
  Same bars 0-14 as Test 4.
    bars 15-19: 93.0 recovering to 98.0 (Stage 2 exit — large bounce)
  Call compute_channel_anchored(prices, start_idx=0, end_idx=19).
  At Stage 2 exit: current_price = 98.0, center = anchored.center_at_last.
  Expected: price_in_lower_half(98.0, center) == False
  Print center_at_last, price, result.

### Test 6: extrapolate_center
  Fit 20-bar declining series (100.0 to 95.0).
  Store channel. Extrapolate 5 bars forward.
  Assert: extrapolated < channel.center_at_last (trend continues down).
  Assert: abs(extrapolated - (channel.center_at_last + channel.slope * 5)) < 1e-9.
  Print both values.

### Test 7: price_in_lower_half boundary
  price_in_lower_half(99.9, 100.0) == True
  price_in_lower_half(100.0, 100.0) == False  (equal = not lower half)
  price_in_lower_half(100.1, 100.0) == False
  Print each result.

### Test 8: Edge cases — no exceptions allowed
  fit_channel([]) → zero result
  fit_channel([100.0]) → zero result
  fit_channel([100.0, 100.0]) → zero result
  fit_channel([100.0, 100.0, 100.0]) → r_squared=0.0, no exception
  compute_channel_anchored(list(range(100)), 5, 6) → 2-bar window → zero result
  Print each result's r_squared to confirm no exception.

### Test 9: pre_lookback sensitivity
  Same 30-bar orderly decline from Test 1.
  Call fit_channel with windows of 10, 20, 30 bars (last N bars of the series).
  Print r_squared and slope_pct for each. Verify all three pass pre_stage1_gate.
  This confirms the gate is stable across the 10-40 bar sweep range.

---

## Hard Rules
- NEVER use escaped quotes in f-strings inside build scripts. Use string concatenation.
- py_compile must pass before reporting PASS on any file.
- NEVER overwrite existing files. Check with os.path.exists() first. If exists, print
  warning and abort that file.
- Every function must have a one-line docstring.
- All printed paths must be full absolute Windows paths.
- No emojis anywhere in any file.
- Do NOT run Python scripts via Bash. Only py_compile one-liners are permitted via Bash.

## Output
Deliver: build script file path + full build script content only.
Run command:
  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_regression_channel.py"
```
