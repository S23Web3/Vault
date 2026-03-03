# CUDA Dashboard v3.9.4 — Build Session

**Date**: 2026-03-03
**Status**: Build script written + py_compile PASS. Blocked on Python 3.12 for CUDA runtime.

---

## What Was Done

### 1. Spec Audit (3 parallel Explore agents)

Audited the handover spec (`06-CLAUDE-LOGS/plans/2026-03-03-cuda-dashboard-v394-spec.md`) against actual source code. Found **4 issues**:

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | CRITICAL | Spec says dashboard uses `Backtester390`. Actual: `Backtester384` + `compute_signals_v383`. | User chose v3.9.0 for CUDA kernel. GPU Sweep mode imports v3.9.0 signals separately. |
| 2 | CRITICAL | Column name inconsistency: spec kernel uses `cloud3_ok_long/short`, DataFrame has `cloud3_allows_long/short`. | Python wrapper uses `df["cloud3_allows_long"]`. Internal kernel var names unchanged. |
| 3 | MODERATE | Spec says reentry has no cloud3 gate. Actual v390 code (line 328): `reentry_long[i] and can_long_b` — reentry IS cloud3-gated. | CUDA kernel gates reentry through cloud3, matching engine. |
| 4 | MINOR | Spec says v393 has IndentationError. Actual: v393 passes py_compile. | No impact — base from v392 regardless. |

Audit plan saved to:
- `C:\Users\User\.claude\plans\bright-prancing-koala.md`
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-v394-spec-audit.md`

### 2. Build Script Written

Created `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_cuda_engine.py` — py_compile PASS.

Creates 3 files:
- `engine/cuda_sweep.py` — Numba CUDA kernel (one thread per param combo, 12 signal arrays, 4 position slots, Welford Sharpe, direction conflict gates, cloud3-gated reentry)
- `engine/jit_backtest.py` — Numba `@njit` CPU core (same logic, for portfolio mode with `ThreadPoolExecutor`)
- `scripts/dashboard_v394.py` — copy of v392 with patches:
  - GPU Sweep mode (selectbox, param range inputs, heatmap, top-20 table, CSV export)
  - GPU sidebar status panel (device, VRAM, CUDA version)
  - GPU Sweep sidebar button
  - Equity curve cache fix (params_hash validation in single mode)

### 3. Python 3.13 CUDA Blocker Discovered

Tested CUDA on the system Python:
- `numba.cuda.detect()` — sees RTX 3060, reports SUPPORTED
- `numba.cuda.is_available()` — returns `False`
- `cuda.to_device()` — crashes with `OSError: access violation reading 0x0000000000000000`

**Root cause**: Numba 0.61.2 does not support Python 3.13 for CUDA operations. The driver bindings have an ABI incompatibility. `@njit` CPU compilation works fine on 3.13.

System has Python 3.13 and 3.14 only — no 3.11 or 3.12. No conda.

### 4. Python 3.12 Install Script Written

Created `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\INSTALL-PYTHON312-CUDA.md` — PowerShell script that:
1. Downloads Python 3.12.8 installer from python.org
2. Installs to `C:\Python312` (no PATH modification, side-by-side with 3.13)
3. Creates `.venv312` venv in project root
4. Installs all backtester deps + numba + PyTorch CUDA 13.0
5. Verifies `cuda.is_available()` and `get_cuda_info()`

---

## Files Created This Session

| File | Status |
|------|--------|
| `C:\...\scripts\build_cuda_engine.py` | py_compile PASS |
| `C:\...\INSTALL-PYTHON312-CUDA.md` | PowerShell install script |
| `C:\...\06-CLAUDE-LOGS\plans\2026-03-03-cuda-v394-spec-audit.md` | Audit results |

## Files NOT Yet Created (waiting for user to run build script)

| File | Blocked on |
|------|-----------|
| `engine/cuda_sweep.py` | Run `python scripts/build_cuda_engine.py` |
| `engine/jit_backtest.py` | Run `python scripts/build_cuda_engine.py` |
| `scripts/dashboard_v394.py` | Run `python scripts/build_cuda_engine.py` |

---

## Next Steps

1. Run the Python 3.12 install script: `.\install_py312_cuda.ps1`
2. Activate venv: `.venv312\Scripts\Activate.ps1`
3. Run build script: `python scripts/build_cuda_engine.py`
4. Verify CUDA: `python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"`
5. Launch dashboard: `streamlit run scripts/dashboard_v394.py`
6. Test GPU Sweep on RIVERUSDT — heatmap should appear in ~2 seconds

---

## Key Decisions

- **Engine version**: User chose v3.9.0 (`Backtester390`) for CUDA kernel, knowing GPU sweep results will differ from existing CPU sweep (which runs v3.8.4)
- **Python version**: Deferred CUDA to Python 3.12 install. JIT CPU core works on 3.13 in the meantime.
- **Build approach**: Single build script copies v392 + applies text patches rather than embedding 2371 lines of dashboard source
