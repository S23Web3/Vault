# Plan: Accelerate Dashboard — Timing Debug + Safe Numba (Audited)

## Context

User asked if sweep/portfolio loading can run on GPU. Answer: No — sequential state machine.
Real solution: measure first (timing instrumentation), then apply Numba only to the 3 kernels
confirmed pure-numpy by source audit.

Numba 0.61.2 already installed. Python 3.13 + llvmlite 0.44.0 + numpy 2.2.6 — confirmed compatible.
dashboard_v391.py is STABLE and will NOT be touched. Zero files modified — new files only.

---

## Audit Findings (Confirmed from Source)

Dashboard v391 import chain (confirmed from lines 1-100 of dashboard_v391.py):
```
dashboard_v391.py
  -> signals.four_pillars_v383.compute_signals_v383
       -> signals.stochastics.compute_all_stochastics  [calls stoch_k() x4]
       -> signals.clouds.compute_clouds                 [calls ema() x6]
       -> signals.state_machine_v383.FourPillarsStateMachine383
  -> engine.backtester_v384.Backtester384
  -> utils.capital_model_v2.apply_capital_constraints
  -> utils.portfolio_manager.*
  -> utils.coin_analysis.*
  -> utils.pdf_exporter_v2.*
```

**timing.py**: does NOT exist in utils/ — can be created fresh.

---

## Numba JIT — Exact Compatibility (Verified Line-by-Line)

### SAFE: stoch_k() in signals/stochastics.py
Signature: `stoch_k(close: np.ndarray, high: np.ndarray, low: np.ndarray, k_len: int) -> np.ndarray`

```python
# All operations: np.full, array slicing, np.min, np.max, float arithmetic
# Zero pandas. Zero dicts. Zero class instances.
# VERDICT: @njit(cache=True) applies directly, no changes to logic.
```

### SAFE: ema() in signals/clouds.py
Signature: `ema(series: np.ndarray, length: int) -> np.ndarray`

```python
# All operations: np.full, len(), np.mean, float arithmetic
# Seed step: result[length - 1] = np.mean(series[:length])  <- Numba supports this
# VERDICT: @njit(cache=True) applies directly, no changes to logic.
```

### SAFE (with extraction): ATR RMA loop in signals/four_pillars_v383.py
The RMA loop (lines ~38-43 of four_pillars_v383.py):
```python
atr = np.full(len(tr), np.nan)
atr[atr_len - 1] = np.mean(tr[:atr_len])
for i in range(atr_len, len(tr)):
    atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
```
The `tr` array is already a pure numpy array at this point (pandas `.values` extracted above it).
Requires: extract 4 lines into `_rma_kernel(tr, atr_len)` function, decorate, call it.

### NOT SAFE (do not attempt):
- `compute_all_stochastics()` — takes pandas DataFrame + dict
- `compute_clouds()` — takes pandas DataFrame + dict, uses `df.iloc[]`
- `compute_signals_v383()` — pandas DataFrame + dict + class instantiation
- `FourPillarsStateMachine383.process_bar()` — Python class method
- `Backtester384.run()` — Python class with pandas state, Optional types, complex branching

---

## Two-Phase Plan

### Phase 1: Timing Instrumentation (Proper Debugging — Measure First)

**New file**: `utils/timing.py`

A simple context manager + accumulator. Wraps each phase in `dashboard_v392.py`
so the user sees per-phase, per-coin milliseconds in a collapsible debug panel.

Timing points in portfolio mode:
1. `load_data()` per coin
2. `compute_signals_v383()` per coin (before and after Numba: proves the win)
3. `Backtester384.run()` per coin
4. `align_portfolio_equity()` total
5. `apply_capital_constraints()` total

UI: a "Performance Debug" checkbox in the sidebar. When checked, shows a table at page bottom.

### Phase 2: Numba-Accelerated Signal Files

**New files** (existing files untouched):
- `signals/stochastics_v2.py` — stochastics.py + `@njit(cache=True)` on `stoch_k()`
- `signals/clouds_v2.py` — clouds.py + `@njit(cache=True)` on `ema()`
- `signals/four_pillars_v383_v2.py` — four_pillars_v383.py with extracted `_rma_kernel()` + `@njit`

**dashboard_v392.py** imports from `signals.four_pillars_v383_v2` instead of `signals.four_pillars_v383`.
Everything else identical to v391.

---

## Files Created (Zero Files Modified)

| File | Action | Notes |
|------|--------|-------|
| `utils/timing.py` | NEW | Context manager + accumulator, stdlib only |
| `signals/stochastics_v2.py` | NEW | stochastics.py + @njit on stoch_k() |
| `signals/clouds_v2.py` | NEW | clouds.py + @njit on ema() |
| `signals/four_pillars_v383_v2.py` | NEW | four_pillars_v383.py + extracted @njit _rma_kernel |
| `scripts/build_dashboard_v392.py` | NEW | Build script (the build) |
| `scripts/dashboard_v392.py` | NEW (generated) | dashboard_v391.py with timing + v2 signals |

**NEVER TOUCHED**: `signals/stochastics.py`, `signals/clouds.py`, `signals/four_pillars_v383.py`,
`scripts/dashboard_v391.py`, any engine or utils file.

---

## Numba Stability Guarantees

1. `cache=True` — compiled native code saved to `__pycache__`. Zero overhead after first run.
2. First run after build: 2-5s one-time compilation of 3 small kernels.
3. If compilation fails: error raised at import time, immediately visible in terminal.
4. Rollback: delete `stochastics_v2.py`, `clouds_v2.py`, `four_pillars_v383_v2.py` → v391 unaffected.
5. Numerical parity: identical output (same arithmetic, different execution mode).
6. Type inference: all inputs are float64 numpy arrays — Numba resolves instantly, no type fights.

---

## Expected Speedup (Realistic)

Estimated timings for 5m data (~30K bars per coin):

| Phase | Current | With Numba | Reason |
|-------|---------|-----------|--------|
| stoch_k() × 4 calls | ~50ms | ~3ms | 15x — window loop compiled |
| ema() × 6 calls | ~15ms | ~1ms | 15x — EMA loop compiled |
| ATR RMA loop | ~3ms | ~0.3ms | 10x — extracted, compiled |
| State machine (bar loop) | ~20ms | unchanged | Python class, not JIT-able |
| Backtester384.run() | ~200ms | unchanged | Python class, not JIT-able |
| **Total per coin** | ~290ms | ~225ms | **~22% per-coin speedup** |

For 30-coin portfolio: saves ~2 seconds on signal computation.
The timing panel will confirm these estimates with real numbers.

**Note**: The backtester loop dominates and cannot be Numba-compiled without a full
rewrite to struct-of-arrays layout. That's a separate, larger effort.

**The bigger architectural win** (CPU parallelism via ProcessPoolExecutor — 8-16x on per-coin phase)
is a Phase 3 option, informed by what the timing panel shows.

---

## Build + Run Commands

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v392.py"
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v392.py"
```

---

## Verification Protocol — Exact Steps

### Step 1: Record the v391 baseline BEFORE building v392

Run v391 (single mode) on RIVERUSDT, 5m timeframe, all default params. Record these 4 numbers:
- Net P&L ($)
- Total Trades
- Win Rate (%)
- Sharpe Ratio

```
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v391.py"
```

Mode: Single | Coin: RIVERUSDT | Timeframe: 5m | All other params: default
Write down the 4 numbers above. These are the golden baseline.

### Step 2: Build v392

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v392.py"
```

First run compiles the 3 Numba kernels (~2-5s in terminal). After that: done.

### Step 3: Confirm Numba compiled cleanly

Check terminal output after build — should see no errors. Optionally:
```
python -c "from signals.stochastics_v2 import stoch_k; import numpy as np; stoch_k(np.ones(100), np.ones(100), np.ones(100), 9); print('Numba OK')"
```
(Run from backtester root)

### Step 4: Run v392 single mode — verify numerical parity

```
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v392.py"
```

Mode: Single | Coin: RIVERUSDT | Timeframe: 5m | ALL params identical to Step 1
Compare the 4 baseline numbers. They must be EXACTLY equal (Numba produces identical float results).
If any number differs: stop, do not use v392, report the discrepancy.

### Step 5: Measure the timing win

In v392: enable "Performance Debug" checkbox in sidebar.
Run Portfolio mode with: RIVERUSDT, KITEUSDT, BERUSDT (same 3 coins as v3.8.4 known-good set).
Check the timing table — confirm:
- compute_signals is faster than the baseline estimate (~50ms → ~3-4ms per coin)
- Backtester.run is unchanged (~200ms per coin)
- Total per-coin time reduced

### Step 6: Confirm v391 still works

Kill the v392 streamlit process. Re-run v391 with same RIVERUSDT / default settings.
Confirm same numbers as Step 1. This proves v391 was never touched.

---

## Rollback (If Anything Goes Wrong)

Delete these files — v391 is immediately back to normal, unchanged:
- `signals/stochastics_v2.py`
- `signals/clouds_v2.py`
- `signals/four_pillars_v383_v2.py`
- `scripts/dashboard_v392.py`
- `scripts/build_dashboard_v392.py`
- `utils/timing.py`
