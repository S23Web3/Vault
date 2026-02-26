# Dashboard v3.9.2 Build Log
Date: 2026-02-18

## Files Generated

| File | Purpose |
|------|---------|
| `utils/timing.py` | TimingAccumulator class + records_to_df() |
| `signals/stochastics_v2.py` | stoch_k @njit(cache=True) |
| `signals/clouds_v2.py` | ema @njit(cache=True) |
| `signals/four_pillars_v383_v2.py` | _rma_kernel @njit + imports v2 signals |
| `scripts/build_dashboard_v392.py` | Build script (generates dashboard_v392.py) |

## Build Script Design

- `build_dashboard_v392.py` reads `dashboard_v391.py` and applies 10 targeted string patches
- Writes `dashboard_v392.py` then runs py_compile + ast.parse on all 5 output files
- Zero files modified — all new files only

## Patches Applied to dashboard_v391.py -> dashboard_v392.py

| Patch | Description |
|-------|-------------|
| P1 | Docstring: v3.9.1 -> v3.9.2 |
| P2 | Import: four_pillars_v383 -> four_pillars_v383_v2 |
| P3 | Add: from utils.timing import TimingAccumulator, records_to_df |
| P4 | Add session state: timing_records = [] |
| P5 | Add sidebar: perf_debug = st.sidebar.checkbox("Performance Debug") |
| P6a | run_backtest signature: add accumulator=None |
| P6b | run_backtest body: time.perf_counter() around signals + engine |
| P7 | Portfolio spinner: _timing_acc = TimingAccumulator() before loop |
| P8 | Portfolio loop: wrap load_data + run_backtest with timing |
| P9 | After loop: save timing_records to session_state |
| P10 | Append timing panel at end of portfolio section |

## Numba Kernels

| Function | File | @njit | Notes |
|----------|------|-------|-------|
| stoch_k | stochastics_v2.py | cache=True | 4 calls per coin per backtest |
| ema | clouds_v2.py | cache=True | 6 calls per coin per backtest |
| _rma_kernel | four_pillars_v383_v2.py | cache=True | 1 call per coin per backtest |

## Audit: Numba Compatibility

- stoch_k: pure numpy (np.full, slice, np.min, np.max, float arithmetic) — SAFE
- ema: pure numpy (np.full, len, np.mean, float arithmetic) — SAFE
- _rma_kernel: pure numpy (np.full, np.mean, float arithmetic) — SAFE
- All inputs: float64 numpy arrays. Type inference: instant, no fights.
- Docstrings inside @njit functions: Numba ignores them (LOAD_CONST + POP_TOP)

## Verification Protocol

1. Record v391 baseline: RIVERUSDT 5m single mode -> 4 numbers (PnL, Trades, WR, Sharpe)
2. Run build script: `python scripts/build_dashboard_v392.py`
3. First launch compiles 3 Numba kernels (~2-5s one-time)
4. Run v392 same params -> compare 4 numbers (must be EXACTLY equal)
5. Enable Performance Debug -> run Portfolio (RIVER+KITE+BERA)
6. Verify timing table shows signals_ms < engine_ms (signals now ~3ms vs ~50ms)
7. Re-run v391 -> same baseline numbers (proves v391 untouched)

## Build Script Checks

- build_dashboard_v392.py: py_compile PASS, ast.parse PASS (verified 2026-02-18)
- Generated files: py_compile + ast.parse run inside build script after each write

## Result (2026-02-18)
- Build ran: 10/10 patches applied, 5/5 files clean
- Dashboard v392 confirmed working — user verified
- Numba compiled on first launch, no errors

## Rollback

Delete these files to immediately restore v391 (which was never touched):
- utils/timing.py
- signals/stochastics_v2.py
- signals/clouds_v2.py
- signals/four_pillars_v383_v2.py
- scripts/dashboard_v392.py
- scripts/build_dashboard_v392.py
