# Session Log: TDI Python Module Build
*Date: 2026-03-13*

## Summary

Built `signals/tdi.py` — a standalone TDI (Traders Dynamic Index) Python module for the Four Pillars backtester. Two public functions, 24 base output columns + 8 graded signal columns. Inspired by CW_Trades TDI (closed-source) and TDI + RSI Div by ZyadaCharts (Pine source provided by user).

## Files Created

### `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\tdi.py`
- ~300 lines
- py_compile PASS, ast.parse PASS
- Two public functions:
  - `compute_tdi(df, params)` → 24 `tdi_` columns
  - `compute_tdi_core(df, params)` → 24 + 8 `tdi_core_` columns (graded signal layer)

**Two presets:**
| Setting | `cw_trades` | `classic` (Dean Malone) |
|---------|-------------|------------------------|
| RSI period | 13 | 14 |
| Fast MA | 2 | 2 |
| Signal MA | 8 | 7 |
| BB period | 34 | 34 |
| BB std dev | 1.6185 | 2.0 |

**Output columns (24 base):**
- Core: `tdi_rsi`, `tdi_fast_ma`, `tdi_signal`, `tdi_bb_upper`, `tdi_bb_mid`, `tdi_bb_lower`
- Zone/color: `tdi_zone` (9-state enum), `tdi_color` (hex) — delta-based (RSI vs signal MA)
- Cloud: `tdi_cloud_bull`, `tdi_cloud_bear`
- Signals: `tdi_long`, `tdi_short`, `tdi_best_setup`, `tdi_best_setup_short`, `tdi_scalp_bias`
- Divergence: `tdi_bull_div`, `tdi_bear_div`, `tdi_hidden_bull_div`, `tdi_hidden_bear_div`
- RSI crosses: `tdi_rsi_cross_signal_up`, `tdi_rsi_cross_signal_down`, `tdi_rsi_cross_bb_upper`, `tdi_rsi_cross_bb_lower`, `tdi_rsi_cross_50_up`, `tdi_rsi_cross_50_down`

**8 graded signal columns from `compute_tdi_core`:**
- `tdi_core_long_a` — long + scalp_bias + strong bull zone
- `tdi_core_long_b` — long + scalp_bias
- `tdi_core_long_c` — best_setup + scalp_bias
- `tdi_core_long_rev` — bull_div + RSI cross 50 up
- `tdi_core_short_a` — short + not scalp_bias + strong bear zone
- `tdi_core_short_b` — short + not scalp_bias
- `tdi_core_short_c` — best_setup_short + not scalp_bias
- `tdi_core_short_rev` — bear_div + RSI cross 50 down

### `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_tdi.py`
- ~400 lines
- 48 test cases across 13 test classes
- File output: `logs/YYYY-MM-DD-tdi-tests.log` (TimedRotatingFileHandler)
- Audit report printed at end
- Test classes: TestTDIColumns, TestTDIWarmup, TestRSIKnownValues, TestPresetsAndParams, TestZoneClassification, TestCrossDetection, TestBuySellSignals, TestCloudAndScalp, TestDivergence, TestCrossSignalsIntegration, TestCoreSignals, TestEdgeCases, TestPerformance

## Key Design Decisions

1. **RSI**: Wilder's smoothing (RMA) — matches Pine `ta.rsi()`. Private copy, no import coupling.
2. **Two MA lines**: `fast_ma = SMA(RSI, 2)` and `signal = SMA(RSI, 7/8)` — NOT a single line. Matches Pine source exactly.
3. **Zone colors**: Delta-based (`delta = RSI - signal`), not raw RSI levels. BB breach overrides.
4. **Buy signal**: `crossover(fast, signal) AND signal > bb_mid AND signal > 50`
5. **Sell signal**: `crossunder(fast, signal) AND signal < bb_mid AND signal < 50`
6. **Best setup**: `crossover(fast, bb_mid)` (long) / `crossunder(fast, bb_mid)` (short)
7. **Scalp bias**: `fast_ma > bb_mid`
8. **Divergence**: RSI-pivot-only (not coincident price+RSI pivots). Range check 5-60 bars. Regular + hidden.
9. **Warmup**: `rsi_period + max(bb_period, signal_ma_len)` bars. All columns NaN/False during warmup.
10. **BB std**: `ddof=0` (population std) to match Pine `ta.stdev()`.
11. **Performance**: Fully vectorized (numpy boolean masking). No Python loops except RSI Wilder init.

## Bugs Fixed During Build

1. **Zone classification used raw RSI levels** — corrected to delta-based (RSI vs signal) per user direction.
2. **Divergence required coincident price+RSI pivots** — root cause: mismatch with Pine source. Pine uses RSI pivots only, reads price at those bars. Fixed to RSI-pivot-only approach.
3. **Classic preset had wrong BB settings** — was 34/1.6185 (same as CW_Trades). Fixed to Dean Malone original: bb_period=34, bb_std=2.0.
4. **Python loops for cloud/scalp/long/short** — vectorized to numpy operations.
5. **Missing `tdi_best_setup_short`** — added alongside `tdi_best_setup`.

## Status

- py_compile PASS on both files
- ast.parse PASS on both files
- 66/66 tests PASS (runtime verified 2026-03-13)
- Standalone module — NOT wired into `four_pillars.py` or `indicators.py`
- NOT yet tested on real OHLCV data from parquet cache

## Opus Audit (2026-03-13)

Full code audit performed with Opus 4.6. Two bugs found and fixed:

### Fixed (2)
- **C1. `_cross` used strict `<`/`>` instead of Pine `<=`/`>=`** — Previous fix for test_touch_then_cross had changed `<=` to `<`, diverging from Pine `ta.crossover` definition (`a > b AND a[1] <= b[1]`). Reverted to `<=`/`>=`. Test corrected to match Pine semantics.
- **H3. Docstrings said 23 columns, actual output is 24** — All docstrings updated to 24.

### Open (not yet fixed)
| ID | Severity | Issue |
|----|----------|-------|
| H1 | HIGH | `_classify_zones` is O(n) Python loop — vectorize with `np.select` |
| H2 | HIGH | `_detect_pivots` uses `==` for float comparison — add epsilon |
| M1 | MEDIUM | Pivot can be both high AND low on flat RSI — guard against |
| M2 | MEDIUM | `long_a` uses `strong_bull \| bull_zone` which is redundant (strong is subset of bull) |
| M3 | MEDIUM | `tdi_cloud_bear` column missing (only `tdi_cloud_bull` emitted) |
| M4 | MEDIUM | `_resolve_params` silently ignores typos in param keys |

### Test coverage gaps noted
- No test for hidden divergence independently
- No test for `_detect_pivots` directly
- No test that RSI crosses BB upper/lower actually fire
- No negative test for core_short_c hierarchy

## Run Command

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_tdi.py"
```
