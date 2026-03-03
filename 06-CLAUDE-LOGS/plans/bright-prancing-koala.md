# CUDA Dashboard v3.9.4 — Spec Audit + Corrected Build Plan

**Date**: 2026-03-03
**Purpose**: Audit the handover spec, then provide corrected build plan.
**User decision**: Build CUDA kernel from v3.9.0 (`Backtester390`) logic.

---

## AUDIT FINDINGS — 4 Issues (2 Critical, 1 Moderate, 1 Minor)

### ISSUE 1 — CRITICAL: Backtester Version Mismatch

**Spec claims**: Dashboard sweep uses `Backtester390`.
**Actual**: Dashboard v3.9.2 imports `Backtester384` + `compute_signals_v383`.

**Resolution**: User chose v3.9.0 for CUDA kernel. The GPU Sweep mode will call `compute_signals()` from `signals/four_pillars_v390.py` and run the v3.9.0-based kernel. This means GPU sweep results will NOT match the existing CPU sweep (which runs v3.8.4). The GPU Sweep mode must use its own signal pipeline call, not the dashboard's existing one.

### ISSUE 2 — CRITICAL: Column Name Inconsistency

**Spec kernel section** uses `cloud3_ok_long/short` as kernel parameter names.
**Actual DataFrame columns** are `cloud3_allows_long/short`.

**Fix**: Python wrapper `run_gpu_sweep()` must extract via `df["cloud3_allows_long"]`. Internal kernel variable names are fine as-is.

### ISSUE 3 — MODERATE: Reentry Cloud3 Gate Error in Spec

**Spec claims** (line 139-140): "RE long: not has_shorts and can_enter (no cloud3 gate)"
**Actual v3.9.0 code** (line 328): `if reentry_long[i] and can_long_b` — where `can_long_b = not has_shorts and can_enter and cloud3_ok_long[i]`.

**v3.9.0 reentry IS cloud3-gated.** The spec incorrectly says it isn't. The CUDA kernel must gate reentry through cloud3, matching the actual engine.

### ISSUE 4 — MINOR: v393 IndentationError Claim

**Spec claims**: v393 has an IndentationError.
**Actual**: v393 passes py_compile. No impact — we base on v392 regardless.

---

## CORRECTED BUILD PLAN

### Context

The Four Pillars dashboard runs parameter sweeps and portfolio backtests on CPU, taking 5-10 min per coin (2,112 combos). The RTX 3060 (3584 CUDA cores, 12GB VRAM) is unused. This build adds:
1. A Numba CUDA kernel that runs 2,112+ param combos in parallel on GPU (~2 seconds)
2. A Numba @njit CPU-compiled path for portfolio mode (ThreadPoolExecutor, ~10x faster)
3. A new "GPU Sweep" mode in the dashboard with heatmap visualization

### Files to Create

All created by `scripts/build_cuda_engine.py`:

| File | Purpose |
|------|---------|
| `C:\...\four-pillars-backtester\scripts\build_cuda_engine.py` | Build script (writes 3 files + py_compile each) |
| `C:\...\four-pillars-backtester\engine\cuda_sweep.py` | Numba CUDA kernel + wrapper + get_cuda_info() |
| `C:\...\four-pillars-backtester\engine\jit_backtest.py` | Numba @njit CPU core (portfolio + single) |
| `C:\...\four-pillars-backtester\scripts\dashboard_v394.py` | v392 copy + GPU Sweep mode + JIT portfolio + GPU sidebar |

### Critical Corrections to Apply (vs original spec)

1. **Reentry gate**: Use `can_long_b`/`can_short_b` (cloud3-gated) for reentry — NOT ungated `can_enter`
2. **Column extraction**: `df["cloud3_allows_long"]` / `df["cloud3_allows_short"]` in Python wrapper
3. **Signal pipeline in GPU Sweep mode**: Must call `compute_signals()` from `four_pillars_v390` (NOT reuse dashboard's v3.8.3 signals) — otherwise the kernel gets columns from the wrong pipeline
4. **No long_d/short_d**: v3.9.0 removed these grades. CUDA kernel has 6 entry signal arrays (long_a, long_b, short_a, short_b, reentry_long, reentry_short) — NOT 8

### Kernel Signal Arrays — 12 Total (Spec Confirmed Correct)

```text
Price:   close[N], high[N], low[N], atr[N]              # 4 float32
Entry:   long_a[N], long_b[N], short_a[N], short_b[N]   # 4 int8
Reentry: reentry_long[N], reentry_short[N]               # 2 int8
Cloud3:  cloud3_ok_long[N], cloud3_ok_short[N]           # 2 int8
```

v3.9.0 drops long_d/short_d (v384 had these). long_c/short_c exist but are always zero (engine assigns C internally) — omitted from kernel. The 12-array count in the original spec is correct.

### Corrected Entry Logic for CUDA Kernel

```
# Grade A long:  long_a[i] and not has_shorts and can_enter
# Grade A short: short_a[i] and not has_longs and can_enter
# Grade B long:  long_b[i] and not has_shorts and can_enter and cloud3_ok_long[i]
# Grade B short: short_b[i] and not has_longs and can_enter and cloud3_ok_short[i]
# RE long:       reentry_long[i] and not has_shorts and can_enter and cloud3_ok_long[i]  <-- CORRECTED
# RE short:      reentry_short[i] and not has_longs and can_enter and cloud3_ok_short[i] <-- CORRECTED
```

### GPU Sweep Mode — Signal Pipeline

The GPU Sweep mode block must import and call v3.9.0 signals directly:
```python
from signals.four_pillars_v390 import compute_signals
```
This is separate from the dashboard's existing `compute_signals_v383` import. The existing modes (single, sweep, portfolio) continue using v3.8.3/v3.8.4 pipeline unchanged.

### Build Order

1. Read source: `engine/backtester_v390.py` (full), `signals/state_machine_v390.py` (full), `signals/four_pillars_v390.py` (first 150 lines), `scripts/dashboard_v392.py` (mode structure + sidebar buttons + portfolio block)
2. Write `scripts/build_cuda_engine.py` — single build script creating all 3 target files
3. py_compile the build script
4. Give user run command — STOP, user runs it
5. User reports results — fix any issues

### Verification

1. py_compile all files (build script does this automatically)
2. `python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"` — verify GPU detected
3. Launch dashboard, check GPU sidebar panel
4. GPU Sweep mode: select a coin, run sweep, verify heatmap appears
5. Portfolio mode: enable "compiled core" checkbox, run, verify faster execution
6. Fallback: `NUMBA_DISABLE_JIT=1` — dashboard loads, GPU Sweep shows error, portfolio falls back

### Everything Else from Original Spec

The following items from the original spec are verified correct and carry forward unchanged:
- Param grid: [N_combos, 4] — sl_mult, tp_mult, be_trigger_atr, cooldown
- tp_mult sentinel: 999.0 (not 0.0)
- Per-thread state: cuda.local.array(4, ...) for position slots
- Welford's online variance for Sharpe
- Kernel output: results[N_combos, 8]
- Kernel launch: 256 threads/block
- Known simplifications (no AVWAP, no scale-outs, no ADDs, fixed constants)
- Heatmap: go.Heatmap(colorscale="RdYlGn", zmid=0), SL vs TP pivot
- JIT warmup: ensure_warmup() at import
- Numba fallback: try/except ImportError → njit = lambda f: f
- Equity curve bug fix: tie to compute_params_hash()
