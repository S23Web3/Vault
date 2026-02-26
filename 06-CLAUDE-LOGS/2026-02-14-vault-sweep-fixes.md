# Vault Code Review Fixes -- 2026-02-14

## Source
Qwen 14B swept 234 files (`06-CLAUDE-LOGS/2026-02-13-vault-sweep-review.md`).
This log records Claude's verification of each claimed bug and fixes applied.

## Summary
- **Files reviewed**: 13 (from ~15 Qwen flagged as potentially actionable)
- **Files fixed**: 1
- **False positives**: 12 (Qwen misread the code or guards already existed)

---

## FIXED

### File 1: `indicators/supporting/atr_position_manager_v1.pine` -- SECURITY FIX
- **Claim**: `i_secret` webhook secret exposed in alert message body (line 212)
- **Verified**: YES. `i_secret` was the first param in the `str.format()` alert JSON, appearing as `"secret":"<value>"` in TradingView's alert log panel.
- **Fix**: Removed `i_secret` from the alert JSON payload. Added comment recommending webhook URL auth or IP allowlist instead.
- **Before**: `'\{"secret":"{0}","ticker":"{1}",...'` with `i_secret` as param 0
- **After**: `'\{"ticker":"{0}","direction":"{1}",...'` -- secret removed, params renumbered
- **Risk**: If user's webhook endpoint validates via the JSON `secret` field, they need to switch to URL-based auth. Comment explains alternatives.

---

## REVIEWED -- NO FIX NEEDED

### File 2: `engine/exit_manager.py` -- FALSE POSITIVE
- **Claim**: `_be_sl` for LONG returns `entry + offset` instead of `entry - offset` (line 113)
- **Verified**: NO. `entry + offset` is CORRECT for LONG.
  - `be_only` (offset=0): SL moves to entry price (breakeven). Correct.
  - `be_plus_fees` (offset=0.3 ATR): SL moves to entry + fees. This means the position must at least cover fees before SL triggers. Correct -- locks in fee coverage.
  - `entry - offset` would put the SL BELOW entry for longs, which is the initial SL direction, NOT a breakeven raise.
- **Conclusion**: Qwen confused SL direction with BE direction. Code is correct.

### File 3: `engine/position_v383.py` -- FALSE POSITIVE
- **Claim**: Checkpoint condition `(bars_held % interval) != 0` should be `== 0` (line 164)
- **Verified**: NO. The `!= 0` is an EARLY RETURN guard: `if not_at_checkpoint: return False`.
  - Line 164: `if (bars_held % self.checkpoint_interval) != 0: return False`
  - Meaning: "if we're NOT at a checkpoint, skip (don't scale out)."
  - The code CONTINUES past this guard only when `bars_held % interval == 0` (at checkpoint).
- **Conclusion**: Qwen misread the control flow. Early-return pattern is correct.

### File 4: `engine/position_v384.py` -- FALSE POSITIVE
- **Claim**: Same checkpoint bug as v383 (line 214)
- **Verified**: NO. Identical correct pattern to v383. Same early-return guard.

### File 5: `02-STRATEGY/Indicators/four_pillars_v3.pine` -- FALSE POSITIVE
- **Claim**: Division by zero in `stoch_k_line` when highest == lowest
- **Verified**: NO. Zero guard already exists on line 45:
  `highest - lowest == 0 ? 50.0 : 100.0 * (close - lowest) / (highest - lowest)`
- **Conclusion**: Qwen didn't read the ternary operator.

### File 6: `02-STRATEGY/Indicators/four_pillars_v3_8_2.pine` -- FALSE POSITIVE
- **Claim**: Division by zero, na checks for hlc3/volume
- **Verified**: NO.
  - `stoch_k()` has same zero guard on line 61: `highest - lowest == 0 ? 50.0 : ...`
  - `hlc3` and `volume` are Pine built-in series, never `na` on normal bars.
  - AVWAP math guards with `cumV > 0` check on line 240.
- **Conclusion**: Guards already exist throughout.

### File 7: `indicators/experimental/liquidity-farming-detector.pine` -- FALSE POSITIVE
- **Claim**: `atr_pct = (atr / close) * 100` division by zero when close=0 (line 52)
- **Verified**: NO. In cryptocurrency markets, `close` can NEVER be 0 on a live chart. If price reaches 0, the asset is delisted and no bars exist. This is a theoretical impossibility.
- **Conclusion**: Not actionable. No real-world scenario produces close=0.

### File 8: `indicators/supporting/Dashboard-Framework-v3.pine` -- FALSE POSITIVE
- **Claim**: Off-by-one in cross detection loop (line 75): `for i = 0 to i_crossWindow - 1` should be `to i_crossWindow`
- **Verified**: NO. `for i = 0 to i_crossWindow - 1` with default `i_crossWindow=3` loops over i=0,1,2 = 3 iterations = 3 bars of lookback. This matches the input label "Cross Detection Bars".
  - Qwen's suggestion (`to i_crossWindow`) would check 4 bars when user sets 3.
- **Conclusion**: Current code correctly checks N bars. Qwen miscounted.

### File 9: `ml/bet_sizing.py` -- FALSE POSITIVE
- **Claim**: Division by zero when `avg_loss == 0` in Kelly sizing (line 86)
- **Verified**: NO. Guard on line 83: `if avg_win <= 0 or avg_loss >= 0: return np.zeros_like(probabilities)`
  - When `avg_loss == 0`, `avg_loss >= 0` is True, so function returns zeros before reaching the division.
- **Conclusion**: Guard already handles this case.

### File 10: `ml/loser_analysis.py` -- WARNING ONLY, NOT A BUG
- **Claim**: Division by zero when `r_value == 0` (line 44)
- **Verified**: PARTIAL. Line 44 uses `np.where(df["r_value"] > 0, df["mfe"] / df["r_value"], 0)`.
  - `np.where` evaluates BOTH branches before masking, so `df["mfe"] / df["r_value"]` triggers a `RuntimeWarning: divide by zero` when r_value contains 0.
  - However, the OUTPUT is correct: np.where replaces those inf/nan results with 0.
  - This is a cosmetic warning, not a logic error. No incorrect results produced.
- **Conclusion**: Warning only. Not worth changing -- np.where output is correct.

### File 11: `ml/features.py` -- FALSE POSITIVE
- **Claim**: Division by zero: `atr[i] / close[i]` and `volume[i] / vol_ma20[i]`
- **Verified**: NO. Guards already exist:
  - Line 93: `if atr is not None and not np.isnan(atr[i]) and close[i] > 0:`
  - Line 99: `if volume is not None and vol_ma20 is not None and vol_ma20[i] > 0:`
- **Conclusion**: Both divisions are guarded. Qwen didn't read the conditions.

### File 12: `optimizer/aggregator.py` -- FALSE POSITIVE
- **Claim**: Off-by-one: `np.searchsorted` result may exceed array bounds (line 60)
- **Verified**: NO. Guard already exists on line 61: `min(idx, len(v_sorted) - 1)`.
- **Conclusion**: Bounds check already implemented. Qwen missed it.

### File 13: `data/db.py` -- LOW PRIORITY, NOT A BUG
- **Claim**: Hardcoded password "admin" as default (line 38)
- **Verified**: YES, "admin" is the default, BUT:
  - It's a fallback: `os.getenv("PG_PASSWORD", "admin")`. `.env` file overrides it.
  - It's a local development database (localhost only, port 5433).
  - No network exposure risk.
- **Conclusion**: By design for local dev convenience. No fix needed.

---

## Files Skipped (~225 files)
Per the review plan, the following categories were skipped:
- ~28 GREEN (no issues found by Qwen)
- ~55 description-only RED (Qwen described code, no bugs identified)
- ~6 empty `__init__.py` (not bugs)
- ~6 skipped >50K chars (dashboard.py, build scripts)
- ~80 generic error-handling suggestions (style, not bugs)

---

## SWEEP 2: 2026-02-14 (vault_sweep_4.py, 62 files, 42 RED)

### Summary
- **Files reviewed**: 62
- **RED flagged**: 42
- **Actionable bugs found**: 0
- **False positive rate**: 100% on specific bug claims

### Key False Positives (Sweep 2)

1. **position_v382.py line 79**: Qwen said LONG SL should be `c + 2*s` (above center). WRONG -- that would instant stop-out every long. `c - 2*s` (below center) is correct.

2. **four_pillars_v382.py line 32**: Qwen said `tr[0] = h[0] - l[0]` should be `tr[0] = np.nan`. WRONG -- if TR[0]=NaN, `np.mean(tr[:atr_len])` = NaN and ATR never initializes. The h-l initialization is necessary.

3. **state_machine_v382.py lines 141/179**: Qwen said `>` should be `>=` in lookback check. WRONG -- both v382 and v383 use `>` consistently (Qwen rated v383 GREEN with the same operator). Design choice.

4. **position_v384.py line 145**: Qwen said `<=` should be `<` for SL check. WRONG -- `<=` means "price touched or crossed SL", which is standard fill behavior.

5. **features_v2.py line 145**: Qwen said `i >= n_bars` should be `i >= n_bars - 1`. WRONG -- would skip the last valid bar.

6. **metrics.py line 65**: Qwen said `> 1` should be `>= 2`. WRONG -- these are mathematically identical for integers.

7. **training_pipeline.py lines 53-55**: Qwen said pool assignment has off-by-one. WRONG -- `else` clause handles remainder automatically.

### Categories Skipped
- 6 description-only REDs (Qwen just described the code)
- 3 skipped >50K chars
- 25 generic try/except advice

---

## Lessons Learned (Both Sweeps Combined)
- Qwen 14B has a ~96% false positive rate on specific bug claims across 2 sweeps (1 real fix out of ~20 specific claims)
- Most "division by zero" claims are wrong because guards already exist
- Qwen frequently confuses SL direction (above/below entry for long/short)
- The checkpoint `!= 0` pattern (early-return guard) is commonly misread as inverted
- `>` vs `>=` comparisons are almost always design choices, not bugs
- Qwen rates identical code GREEN in one version and RED in another (v382 vs v383 state machines)
- The only real finding across both sweeps was the webhook secret in the Pine Script alert payload
- Sweep 2 confirms: description-only and generic error-handling entries dominate (~80% of REDs)
- Lesson: LLM code review is useful for FINDING files to check, but the actual analysis must be verified by a human or stronger model
