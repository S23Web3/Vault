# CUDA Dashboard v3.9.4 — Spec Audit Report

**Date**: 2026-03-03
**Purpose**: Audit the handover spec (`06-CLAUDE-LOGS/plans/2026-03-03-cuda-dashboard-v394-spec.md`) against actual source code before building.

---

## AUDIT VERDICT: 3 Issues Found (2 Critical, 1 Minor)

### ISSUE 1 — CRITICAL: Backtester Version Mismatch

**Spec claims**: Dashboard sweep uses `Backtester390` in a per-rerun loop.
**Actual code**: Dashboard v3.9.2 uses `Backtester384` (line 278) and signal pipeline `compute_signals_v383` — NOT the v3.9.0 engine/signals.

The v3.9.0 files exist (`engine/backtester_v390.py`, `signals/state_machine_v390.py`, `signals/four_pillars_v390.py`) but the **active dashboard does not use them**. The dashboard imports:
```python
from signals.four_pillars_v383_v2 import compute_signals_v383
from engine.backtester_v384 import Backtester384
```

**Impact on CUDA build**: The CUDA kernel must match whichever engine the dashboard actually calls. Two options:
- **Option A**: Build CUDA kernel matching v3.8.4 logic (what the dashboard currently uses) — guaranteed parity with existing sweep/portfolio results
- **Option B**: Build CUDA kernel matching v3.9.0 logic (what the spec describes) — the kernel results will NOT match the dashboard's CPU sweep results, because the dashboard runs v3.8.4

**Recommendation**: Option A (match v3.8.4) for result parity. Or upgrade the dashboard to v3.9.0 pipeline first, then build CUDA — but that's scope creep.

### ISSUE 2 — CRITICAL: Column Name Inconsistency in Spec

**Spec kernel section** uses variable names `cloud3_ok_long` / `cloud3_ok_short` for the GPU arrays.
**Actual DataFrame columns** are `cloud3_allows_long` / `cloud3_allows_short` (confirmed in `signals/four_pillars_v390.py` line 81-82 and `engine/backtester_v390.py` lines 106-107).

The spec's `run_gpu_sweep()` wrapper must extract columns using `df["cloud3_allows_long"]`, not `df["cloud3_ok_long"]`. The local variable names inside the kernel can be anything, but the DataFrame column lookup must use `allows_`.

**Fix**: Ensure the Python wrapper uses `cloud3_allows_long` / `cloud3_allows_short` when extracting from the DataFrame. The kernel parameter names (`cloud3_ok_long`, etc.) are fine as internal names.

### ISSUE 3 — MINOR: v393 IndentationError Claim

**Spec claims**: v393 has an IndentationError — base from v392, NOT v393.
**Actual**: v393 exists (127KB) and passes py_compile with no IndentationError.

**Impact**: Low. The spec already says to base v394 on v392, which is correct since v392 is the known-good active version. Whether v393 has errors or not doesn't change the build plan.

---

## VERIFIED FACTS (All Correct in Spec)

| Item | Spec Claim | Verified |
|------|-----------|----------|
| Mode chain | settings → single → sweep → sweep_detail → portfolio | YES — lines 705, 710, 1378, 1616, 1764 |
| Reentry columns | `reentry_long`, `reentry_short` | YES — state_machine_v390.py + engine |
| Position slots | 4 max | YES — engine line 132 |
| Direction conflict gate | has_longs blocks shorts, vice versa | YES — engine lines 252-260 |
| Entry priority | A → B → RE ordering | YES — engine lines 265-345 |
| Portfolio is sequential | for-loop, no parallelism | YES — lines 1905-1933 |
| compute_params_hash() exists | Lines 287-291, MD5-based | YES |
| Equity cache bug | Single mode has no hash validation | YES — line 721 checks None only |
| Sidebar buttons | Run Backtest / Sweep ALL / Portfolio Analysis | YES — lines 474-476 |
| Target files don't exist | cuda_sweep.py, jit_backtest.py, dashboard_v394.py, build_cuda_engine.py | YES — all clear |
| Existing Numba usage | CPU @njit only, no @cuda.jit in project | YES — 11 files with @njit, zero CUDA |
| engine/__init__.py | Exists (empty stub) | YES |

---

## DECISION NEEDED BEFORE BUILD

The critical question: **Which engine version should the CUDA kernel replicate?**

- **v3.8.4** (`Backtester384`) — what the dashboard actually runs today. Results will match CPU sweep exactly.
- **v3.9.0** (`Backtester390`) — what the spec describes. Results will differ from the dashboard's CPU sweep because the dashboard doesn't use v3.9.0.

This determines which source file I read to port the position/exit logic into the CUDA kernel.