# CUDA Dashboard v394 — Session Handover
**Date**: 2026-03-03
**For**: New chat — ready to build, no further planning needed
**Status**: PLAN AUDITED AND COMPLETE — build `scripts/build_cuda_engine.py` first

---

## What This Session Must Build

Add CUDA GPU sweep capability and Numba JIT portfolio speedup to the Four Pillars dashboard.
Output: `scripts/dashboard_v394.py` + engine files, all created via one build script.

**NOTE**: The earlier vault plan (`06-CLAUDE-LOGS/plans/2026-03-03-cuda-sweep-engine.md`) contains
4 pre-audit errors. This document has the CORRECTED architecture. Use this doc, not the vault plan.

---

## Problem Being Solved

Sweeps and portfolio runs are sequential and CPU-bound:
- Single-coin sweep: 2,112 param combos × 10K bars = 5–10 minutes
- 400-coin full sweep: 6–60 hours
- Portfolio (dashboard): sequential loop, no parallelism

RTX 3060 (3584 CUDA cores, 12GB VRAM) is idle for this workload. Each param combo reads the same
signal arrays independently — embarrassingly parallel across combos.

**Why Numba CUDA, not PyTorch**: The backtest is a stateful bar-by-bar state machine with
imperative branching. PyTorch cannot express this without a full rewrite. Numba `@cuda.jit` maps
directly: one GPU thread = one param combo, private position state in registers, shared read-only
signal arrays. PyTorch stays for ML only.

---

## Source Files — READ THESE FIRST in New Chat

All under: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`

| File | Why | Lines |
|------|-----|-------|
| `engine/backtester_v390.py` | Port position logic, entry priority, exit logic to kernel | Full (630 lines) |
| `signals/state_machine_v390.py` | Confirms column names: `reentry_long/reentry_short`, grade A/B logic | Full |
| `signals/four_pillars_v390.py` | Confirms: `cloud3_allows_long/cloud3_allows_short` column names | First 100 lines |
| `scripts/dashboard_v392.py` | Base for v394 copy. Read mode structure (lines 700-730), sweep mode (lines 1372-1615), portfolio mode (lines 1764-2100) | Targeted sections |

**Confirmed facts about v392 (do not re-verify):**
- Mode system: `if mode == "settings"` / `elif mode == "single"` / `elif mode == "sweep"` / `elif mode == "sweep_detail"` / `elif mode == "portfolio"` — new `gpu_sweep` mode appended after `portfolio`
- Existing sweep uses CPU `Backtester390` in a per-rerun loop with CSV progress file
- Existing portfolio uses sequential `run_backtest()` calls with no parallelism
- v393 has an IndentationError — base from v392, NOT v393

---

## Files to Create

All created by `scripts/build_cuda_engine.py`. No file is overwritten — build script checks
existence and exits with error if any target already exists.

| File | Purpose |
|------|---------|
| `scripts/build_cuda_engine.py` | Build script: writes all 4 files + py_compile each |
| `engine/cuda_sweep.py` | Numba CUDA kernel + Python wrapper + get_cuda_info() |
| `engine/jit_backtest.py` | Numba @njit CPU-compiled core (single run + portfolio) |
| `scripts/dashboard_v394.py` | v392 copy + GPU Sweep mode + portfolio JIT path + sidebar GPU panel |

**Not included in this build**: `scripts/sweep_all_coins_v2.py` — defer to next session.

---

## Engine Architecture (CORRECTED — audit-verified)

### CUDA Kernel (`engine/cuda_sweep.py`)

**GPU thread model**: one thread per parameter combo.

**Kernel inputs — 12 signal arrays (NOT 10):**
```python
# Price (float32, read-only)
close[N], high[N], low[N], atr[N]

# Entry signals (int8, read-only)
long_a[N], long_b[N], short_a[N], short_b[N]
reentry_long[N], reentry_short[N]    # CORRECT names (NOT re_long/re_short)

# Cloud3 gates (int8, read-only) — required for grade B gating
cloud3_ok_long[N], cloud3_ok_short[N]   # from engine lines 106-107, 259-260
```

**Kernel scalar args** (NOT in param_grid):
```python
notional: float32        # scalar — same for all combos
commission_rate: float32 # scalar — 0.0008
```

**Param grid shape — [N_combos, 4] (NOT 5):**
```python
param_grid[c] = [sl_mult, tp_mult, be_trigger_atr, cooldown]
# notional is scalar kernel arg, NOT per-combo
```

**tp_mult sentinel — 999.0 (NOT 0.0):**
- 0.0 = TP at entry price = instant exit. NEVER use.
- 999.0 = no TP, hold until SL or end of data. Safe in float32.

**Per-thread position state** (Numba requires `cuda.local.array`, NOT Python lists):
```python
pos_active    = cuda.local.array(4, numba.int8)    # 0=empty, 1=open
pos_dir       = cuda.local.array(4, numba.int8)    # 1=LONG, -1=SHORT
pos_entry     = cuda.local.array(4, numba.float32)
pos_sl        = cuda.local.array(4, numba.float32)
pos_tp        = cuda.local.array(4, numba.float32) # 999.0 = no TP
pos_be_raised = cuda.local.array(4, numba.int8)    # 0 or 1
```

Scalar state in registers:
```
equity, peak_equity, max_dd, last_entry_bar, trade_count, win_count,
pnl_sum, lsg_count, wf_n, wf_mean, wf_M2
```

**Sharpe — Welford's online variance** (no per-trade list in GPU kernel):
```python
# On each trade close:
wf_n += 1
delta = trade_net_pnl - wf_mean
wf_mean += delta / wf_n
wf_M2 += delta * (trade_net_pnl - wf_mean)
# At end: variance = wf_M2 / wf_n; sharpe = wf_mean / sqrt(variance) if variance > 0 else 0.0
```

**Direction conflict gate** (matches engine exactly):
```python
has_longs  = any pos_dir[s]==1  for active slots
has_shorts = any pos_dir[s]==-1 for active slots
# Grade A long:  not has_shorts and can_enter
# Grade A short: not has_longs  and can_enter
# Grade B long:  not has_shorts and can_enter and cloud3_ok_long[i]
# Grade B short: not has_longs  and can_enter and cloud3_ok_short[i]
# RE long:       not has_shorts and can_enter (no cloud3 gate)
# RE short:      not has_longs  and can_enter
```

**Kernel output** — `results[N_combos, 8]`:
```
[total_trades, win_rate, net_pnl, expectancy, max_dd_pct, profit_factor, lsg_pct, sharpe]
```

**Kernel launch config**:
```python
threads_per_block = 256
blocks = math.ceil(N_combos / threads_per_block)
backtest_kernel[blocks, threads_per_block](
    d_close, d_high, d_low, d_atr,
    d_long_a, d_long_b, d_short_a, d_short_b,
    d_reentry_long, d_reentry_short,
    d_cloud3_ok_long, d_cloud3_ok_short,
    d_param_grid, N, N_combos,
    notional, commission_rate,
    d_results
)
numba.cuda.synchronize()
```

**Known kernel simplifications** (intentional, documented in docstring):
- Fixed ATR SL only — no AVWAP dynamic SL ratcheting
- No scale-outs (AVWAP checkpoint partial exits omitted)
- No ADD entries (AVWAP pyramid limit orders omitted)
- Reentry = immediate market entry (uses signal column, not AVWAP limit order)
- Grade C labeling omitted (A/B fires while in-position enters as A/B, not C)
- Fixed constants: `allow_c_trades=True`, `b_open_fresh=True`, `be_lock_atr=0.0`

**Python wrapper** `run_gpu_sweep(df_signals, param_grid_np, notional, comm_rate)`:
1. Extract signal/price columns from DataFrame as float32 numpy arrays
2. `cuda.to_device()` all arrays
3. Launch kernel, synchronize
4. Copy results back, build pandas DataFrame with column names
5. Return sorted by net_pnl descending

**`build_param_grid(sl_range, tp_range, cooldown_vals, be_vals)`**:
```python
sl_vals       = np.arange(0.5, 3.25, 0.25)          # 11 values
tp_vals       = [999.0] + list(np.arange(0.5, 4.25, 0.25))  # 16 values
cooldown_vals = [0, 3, 5, 10]                         # 4 values
be_vals       = [0.0, 0.5, 1.0]                       # 3 values
# Total: 11 × 16 × 4 × 3 = 2,112 combos
```

**`get_cuda_info()`**: returns dict `{'device': str, 'vram_total_gb': float, 'vram_free_gb': float, 'cuda_version': str, 'numba_version': str}` for sidebar display.

---

### CPU Compiled Core (`engine/jit_backtest.py`)

**`@njit backtest_loop(...)`**:
- Same logic as CUDA kernel but Numba CPU-compiled
- Signature: `(close, high, low, atr, long_a, long_b, short_a, short_b, reentry_long, reentry_short, cloud3_ok_long, cloud3_ok_short, sl_mult, tp_mult, be_trigger, cooldown, notional, commission_rate)`
- Returns: `(trade_count, win_count, net_pnl, max_dd_pct, lsg_pct, equity_curve_array)`
- Used by: dashboard portfolio per-coin call via ThreadPoolExecutor

**`ensure_warmup()`** — call at module import with 10-bar dummy arrays.
Prevents 1–5 second JIT compilation freeze on first real portfolio run.

**Fallback**: `try: from numba import njit` / `except ImportError: njit = lambda f: f`
Dashboard falls back to CPU path without crash if Numba unavailable.

---

## Dashboard v394 Spec

**Base**: copy of `scripts/dashboard_v392.py`. Apply these additions:

### 1. New Mode: `gpu_sweep`

Append after the `elif mode == "portfolio":` block (around line 2100+):

```python
# ── GPU SWEEP MODE ─────────────────────────────────────────────────────────
elif mode == "gpu_sweep":
```

**Sidebar trigger**: add `"GPU Sweep"` button alongside existing mode buttons in settings sidebar.
When clicked: `st.session_state["mode"] = "gpu_sweep"` + `st.rerun()`.

**GPU Sweep mode layout**:

```
[Back to Settings]

Title: "GPU Sweep — {timeframe}"

Symbol:       [selectbox — single coin from cached list]
Date range:   [same date_range widget as other modes]

--- Param Ranges ---
SL:       min [0.5] max [3.0] step [0.25]
TP:       min [0.5] max [4.0] step [0.25]  + [x] Include "No TP" (999.0)
Cooldown: [multiselect: 0, 3, 5, 10]
BE trigger: [multiselect: 0.0, 0.5, 1.0]
Notional: [number_input — default from sidebar notional setting]

Combo count: {N} combos | Est. VRAM: ~{N * 0.0001:.1f} MB

[Run GPU Sweep]

--- Results (shown after run) ---
[Heatmap: SL vs TP, colored by net_pnl, go.Heatmap]
[Top-20 table: st.dataframe — all 8 metrics, sorted by expectancy]
[Export CSV button]
```

**CUDA availability check** at top of mode block:
```python
try:
    from engine.cuda_sweep import run_gpu_sweep, build_param_grid, get_cuda_info
    cuda_ok = True
except ImportError:
    cuda_ok = False
if not cuda_ok:
    st.error("engine/cuda_sweep.py not found. Run build_cuda_engine.py first.")
    st.stop()
```

**Heatmap construction** (after sweep completes):
- Pivot results df on `sl_mult` (y-axis) vs `tp_mult` (x-axis), values = `net_pnl`
- Replace 999.0 in axis labels with "No TP"
- `go.Heatmap(colorscale="RdYlGn", zmid=0)` — red=loss, green=profit
- Add best combo annotation at peak cell

**Session state key**: `st.session_state["gpu_sweep_results"]` — persist across reruns.
Cache invalidation: clear when symbol or date range changes.

---

### 2. Portfolio Mode Modifications (in existing `elif mode == "portfolio":` block)

Add JIT execution path alongside existing path:

```python
use_jit = st.checkbox("Use compiled core (10x faster)", value=True, key="port_use_jit")
```

When `use_jit=True` and Numba available:
```python
from engine.jit_backtest import backtest_loop as jit_loop, ensure_warmup
ensure_warmup()  # no-op if already warm

with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {
        ex.submit(jit_loop, *arrays_for(sym), sl_mult, tp_mult, ...): sym
        for sym in port_symbols
    }
    port_results = {futures[f]: f.result() for f in as_completed(futures)}
# All st.* calls AFTER this block — workers must NOT call st.*
```

When `use_jit=False` or Numba unavailable: existing sequential path unchanged.

---

### 3. Sidebar GPU Status Panel

Below existing sidebar controls, add:

```python
# GPU status (cached 60s)
@st.cache_data(ttl=60)
def _get_gpu_info():
    try:
        from engine.cuda_sweep import get_cuda_info
        return get_cuda_info()
    except Exception:
        return None

gpu_info = _get_gpu_info()
if gpu_info:
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"GPU: {gpu_info['device']}\n"
        f"VRAM: {gpu_info['vram_free_gb']:.1f}GB free / {gpu_info['vram_total_gb']:.1f}GB\n"
        f"CUDA {gpu_info['cuda_version']} | Numba {gpu_info['numba_version']}"
    )
```

---

### 4. Equity Curve Bug Fix (from v393 attempt)

Tie equity curve cache invalidation to `compute_params_hash()` (already exists in v392).
This is the fix that v393 attempted but introduced an IndentationError. Apply it cleanly in v394.
Locate the equity curve cache key in v392, replace the ad-hoc key with `compute_params_hash()` output.

---

## Build Script Spec (`scripts/build_cuda_engine.py`)

```
1. Check existence of all 4 targets — exit with error if any exists
2. Write engine/cuda_sweep.py     → py_compile → print [OK] cuda_sweep.py
3. Write engine/jit_backtest.py   → py_compile → print [OK] jit_backtest.py
4. Write scripts/dashboard_v394.py → py_compile → print [OK] dashboard_v394.py
5. Print: "All 3 files compiled clean. Run command: streamlit run ..."
```

**Note**: `sweep_all_coins_v2.py` deferred — build only 3 files in this session.

F-string safety rule: NEVER use escaped quotes in join() calls inside triple-quoted build strings.
Use string concatenation instead: `"ERRORS: " + ", ".join(errors)`.

---

## Build Order for New Chat

1. Load Python skill: `/python`
2. Read source files listed above (engine + state_machine + dashboard_v392 sections)
3. Verify no changes: confirm `reentry_long/reentry_short` and `cloud3_allows_long/short` column names
4. Write `scripts/build_cuda_engine.py` (full source, all 3 target files embedded)
5. py_compile validate the build script itself
6. Give user run command — STOP, wait for user to run it
7. User runs: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_cuda_engine.py"`
8. User reports results — fix any py_compile errors then repeat

---

## Run Commands

```bash
# Run the build script
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_cuda_engine.py"

# Verify CUDA (run from backtester root)
python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"

# Launch dashboard
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py"
```

---

## Verification Steps

1. **Syntax**: build script runs py_compile on all files, reports pass/fail per file
2. **CUDA check**: `python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"` — expected: `{'device': 'NVIDIA GeForce RTX 3060', ...}`
3. **GPU sidebar**: launch dashboard, confirm GPU panel shows in sidebar
4. **GPU Sweep tab**: navigate to GPU Sweep mode → select RIVERUSDT → click Run → heatmap appears within ~2 seconds
5. **Portfolio JIT**: portfolio mode → enable "Use compiled core" checkbox → run 5-coin portfolio → confirm faster than before
6. **Fallback test**: `NUMBA_DISABLE_JIT=1 streamlit run ...` → confirm dashboard loads, GPU Sweep shows error message, portfolio falls back to sequential — no crash

---

## Permissions Pre-Approved

User approved full scope. No new approvals needed for:
- Write new files: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`, `scripts/build_cuda_engine.py`
- Bash: py_compile one-liners ONLY — `python -c "import py_compile; py_compile.compile(path, doraise=True)"`
- Read: any source file in the backtester project
- No git, no network, no other script execution

---

## Memory Files to Update After Build

- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-backtester.md` — add cuda_sweep.py and jit_backtest.py to engine file inventory
- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-dashboard.md` — add dashboard_v394 status
- `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md` — update dashboard version when v394 promoted to production
- `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md` — mark CUDA sweep task as COMPLETE
