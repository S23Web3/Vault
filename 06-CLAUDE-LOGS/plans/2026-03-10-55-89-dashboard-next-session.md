# Session handoff — 55/89 dashboard runtime verification

Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\PROJECT-STATUS.md` and `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-55-89-scalp.md` before doing anything else.

## What was done last session (2026-03-10)

### Task 1: PDF export params table fixed
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py` line ~383
- Replaced stale `["BE trigger", bt_params.get("be_trigger_atr", 0)]` (always printed "0x ATR") with 4 correct Backtester5589 params: AVWAP sigma, AVWAP warmup, TP ATR offset, Ratchet threshold

### Task 2: GPU sweep ported from Backtester384 to Backtester5589
**New file:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep_5589.py`
- `build_param_grid_5589()` — [N, 5] grid: sl_mult x avwap_sigma
- `backtest_kernel_5589` — CUDA kernel: 4-phase AVWAP SL (volume-weighted HLC3, sigma floor, overzone ratchet via stoch_9_d, Cloud4 TP via ema_72/ema_89). Commission: taker both sides. Single position.
- `run_gpu_sweep_5589()` — dispatches to kernel

**Dashboard edits (5 changes):**
1. Import swapped: `cuda_sweep` -> `cuda_sweep_5589`
2. `run_gpu_sweep_55_89()`: computes ema_72, uses new param grid
3. `render_gpu_results()`: `be_trigger_atr` -> `avwap_sigma` everywhere
4. Sidebar: slider "AVWAP sigma range max" (1.0-4.0), caption updated
5. PDF params table: see Task 1

**Audit fix:** SHORT TP sentinel changed from `0.000001` (would trigger immediately) to `-999999.0` (safe, guarded by Phase 4 check)

Both files: py_compile + ast.parse PASS.

## What needs doing now

### Verify dashboard runs
The dashboard has NOT been run since edits. User needs to verify:
```
& "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312\Scripts\python.exe" -m streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py"
```

Checklist:
1. Dashboard loads without import errors
2. CPU mode: single coin backtest runs, equity curve renders
3. CPU mode: PDF export shows AVWAP sigma / AVWAP warmup / TP ATR offset / Ratchet threshold (NOT "BE trigger 0x ATR")
4. GPU mode: sidebar shows "AVWAP sigma range max" slider (CUDA still unavailable, so sweep won't actually run — just verify sidebar renders correctly)
5. Portfolio mode: runs, per-coin table has Volume/Rebate columns

### Optional: test cuda_sweep_5589.py import in .venv312
Since numba is installed in .venv312, verify the module imports cleanly:
```
& "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312\Scripts\python.exe" -c "from engine.cuda_sweep_5589 import CUDA_AVAILABLE, build_param_grid_5589; print('CUDA:', CUDA_AVAILABLE); g = build_param_grid_5589(); print('Grid shape:', g.shape, 'dtypes:', g.dtype)"
```
Run from backtester root. Expected: `CUDA: False` (numba installed but numba.cuda may not have GPU runtime), grid shape like `(56, 5)` dtype `float32`.

## Key files

```
PROJECTS/four-pillars-backtester/
  engine/
    cuda_sweep_5589.py       NEW — 5589 GPU sweep (this session)
    cuda_sweep.py            LEGACY — Backtester384 GPU sweep (do not modify)
    backtester_55_89.py      CPU reference engine
    backtester_5589_jit.py   JIT engine (@njit, 270x speedup)
    avwap.py                 AVWAPTracker (volume-weighted HLC3)
  scripts/
    dashboard_55_89_v3.py    MODIFIED — PDF + GPU fixes (this session)
  signals/
    ema_cross_55_89.py       Signal pipeline (outputs stoch_9_d, ema_55, ema_89)
```

## Rules
- Load /python skill before writing any .py file
- py_compile + ast.parse on every file written
- Read files before editing — do not guess line numbers
- No bash execution of Python — give commands, user runs
