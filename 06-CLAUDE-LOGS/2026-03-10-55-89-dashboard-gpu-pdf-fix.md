# 2026-03-10 — 55/89 Dashboard v3: PDF + GPU Sweep Fix

## What was done

### Task 1: PDF export params table fix
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` line ~374
- Replaced stale `["BE trigger", bt_params.get("be_trigger_atr", 0)]` (returned 0, printed "0x ATR")
- Now shows 4 correct Backtester5589 params: AVWAP sigma, AVWAP warmup, TP ATR offset, Ratchet threshold

### Task 2: GPU sweep ported to Backtester5589
**New file:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep_5589.py`
- `build_param_grid_5589()` — [N, 5] grid: sl_mult x avwap_sigma (warmup/tp_offset/ratchet fixed per call)
- `backtest_kernel_5589` — CUDA kernel implementing full 4-phase AVWAP SL lifecycle:
  - Phase 1: ATR initial SL
  - Phase 2: Frozen volume-weighted AVWAP (HLC3) with sigma floor
  - Phase 3: Overzone ratchet (stoch_9_d < 20 exit for longs, > 80 exit for shorts)
  - Phase 4: Cloud4 TP (max/min of ema_72, ema_89 + tp_atr_offset * ATR), updated every bar
- `run_gpu_sweep_5589()` — dispatches to kernel with correct signal columns
- Commission: taker on both entry and exit (matches CPU backtester)
- Single position at a time (correct for 5589 strategy)

**Dashboard changes (5 edits to dashboard_55_89_v3.py):**
1. Import: `cuda_sweep` -> `cuda_sweep_5589`, function names updated
2. `run_gpu_sweep_55_89()`: now computes ema_72 (for Cloud4 TP), uses new param grid functions
3. `render_gpu_results()`: all `be_trigger_atr` -> `avwap_sigma`, axis labels updated
4. Sidebar: slider renamed "AVWAP sigma range max" (1.0-4.0), caption updated
5. PDF params: see Task 1

### Audit findings
- SHORT TP sentinel was `0.000001` (would trigger immediately for any real price) -> fixed to `-999999.0`
- Phase 4 guard (`pos_phase == 4`) protects sentinel values before TP activates
- Kernel AVWAP accumulation order matches CPU backtester exactly (traced bar by bar)

## Validation
- py_compile + ast.parse PASS on both files
- CUDA path still unreachable (numba-cuda not installed system-wide, only in .venv312)

## Files modified
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep_5589.py` (NEW)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` (5 edits)

## Not done
- No runtime test of GPU sweep (CUDA unavailable outside venv)
- No dashboard run (user runs from terminal)
- cuda_sweep_5589.py not tested with actual CUDA — architecture verified against CPU backtester only
