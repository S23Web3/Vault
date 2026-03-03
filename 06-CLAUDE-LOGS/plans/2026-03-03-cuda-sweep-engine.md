# CUDA Acceleration — Four Pillars Sweep Engine & Dashboard v3.9.4

**Date**: 2026-03-03
**Scope**: Full — engine layer + scripts + dashboard_v394

---

## Context

Parameter sweeps and portfolio runs are fully sequential and CPU-bound. A typical single-coin sweep (500+ param combos × 10K bars) takes 50–100 seconds. A full 400-coin sweep takes 6–60 hours. The backtest loop is stateful (position state per bar) so parallelism across bars is not possible, but parallelism **across parameter combos** is embarrassingly parallel — each combo reads the same signal arrays independently. RTX 3060 (3584 CUDA cores, 12GB VRAM) allows 2,640+ combos to run simultaneously.

**Why Numba CUDA, not PyTorch:**
The bar-by-bar state machine (`if pos_open: check SL/TP, update equity`) cannot be expressed as PyTorch tensor operations without a full rewrite that obscures logic and risks introducing bugs. Numba `@cuda.jit` maps directly: one GPU thread = one param combo, each thread holds private position state in registers, all threads share the same read-only signal/price arrays. PyTorch stays for ML only.

---

## Intended Outcome

1. **Single-coin GPU sweep**: 2,640 combos run in ~1–2 seconds instead of 5–10 minutes
2. **Dashboard "GPU Sweep" tab**: select symbol → click Run → full heatmap of SL×TP performance
3. **Faster portfolio**: multi-coin runs use Numba @njit CPU kernel (10x faster per backtest) + ThreadPoolExecutor (parallel coins); GPU launch overhead not worth it for <20 coins
4. **Offline sweep pipeline**: sweep_all_coins_v2.py uses GPU for per-coin param optimization

---

## Critical Files

### New (create via build script):
- `engine/cuda_sweep.py` — Numba CUDA kernel + Python wrapper
- `engine/jit_backtest.py` — Numba @njit compiled CPU core (single backtest, fallback)
- `scripts/build_cuda_engine.py` — build script: creates both files, runs py_compile on each

### New (dashboard):
- `scripts/dashboard_v394.py` — new version (never overwrite v392/v393)

### Updated (new versioned file):
- `scripts/sweep_all_coins_v2.py` — replaces sequential coin loop with GPU sweep per coin

---

## Architecture

### 1. CUDA Kernel (`engine/cuda_sweep.py`)

**GPU thread model**: one thread per parameter combo
**Input arrays** (on GPU device, float32, read-only):
```
close[N], high[N], low[N], atr[N]         # price arrays
long_a[N], long_b[N], short_a[N], short_b[N]  # signal booleans (int8)
re_long[N], re_short[N]                   # reentry signals
param_grid[N_combos, 5]                   # [sl_mult, tp_mult, be_trigger, cooldown, notional]
```

**Output** (on GPU device, float32):
```
results[N_combos, 8]  = [total_trades, win_rate, net_pnl, expectancy, max_dd_pct, profit_factor, lsg_pct, sharpe]
```

**Per-thread private state** (in registers — no shared memory needed):
- `pos_active[4], pos_dir[4], pos_entry[4], pos_sl[4], pos_tp[4]` — 4 position slots
- `equity, peak_equity, max_dd, trade_count, win_count, pnl_sum, cooldown_bars`
- `lsg_count` (losers that saw green — tracked with `pos_peak_pnl[4]`)

**Commission**: applied per trade as `notional * 0.0008 * 2` (entry + exit), subtracted from pnl. No rebate in kernel (post-processing in Python).

**tp_mult sentinel**: 0.0 = no TP (hold until SL hit or end of data). Avoids NULL in float array.

**Kernel launch**:
```python
threads_per_block = 256  # typical for non-memory-intensive kernels
blocks = ceil(N_combos / threads_per_block)
backtest_kernel[blocks, threads_per_block](...)
```

**Python wrapper** `run_gpu_sweep(df_signals, param_grid_np, notional, comm_rate)`:
1. Extract numpy arrays from DataFrame
2. Convert to float32, move to GPU via `cuda.to_device()`
3. Launch kernel, synchronize
4. Copy results back, build pandas DataFrame with column names
5. Return sorted by net_pnl descending

**`build_param_grid(sl_range, tp_range, cooldown_vals, be_vals)`**:
- Returns numpy array of all itertools.product combinations
- Default: sl=[0.5–3.0 step 0.25], tp=[0.0, 0.5–4.0 step 0.25], cooldown=[0,3,5,10], be=[0.0,0.5,1.0] → ~2,640 combos

**`get_cuda_info()`**: returns dict with device name, VRAM total/free, CUDA version for sidebar display.

---

### 2. CPU Compiled Core (`engine/jit_backtest.py`)

**`@njit backtest_loop(close, high, low, atr, long_a, long_b, short_a, short_b, re_long, re_short, sl_mult, tp_mult, be_trigger, cooldown, notional, commission_rate)`**:
- Same logic as kernel but Numba CPU-compiled
- Returns `(trade_count, win_count, net_pnl, max_dd_pct, lsg_pct, equity_curve_array)`
- Used by: dashboard single-coin run, portfolio per-coin call
- Falls back to Python if Numba unavailable (ImportError catch)

**`@njit batch_backtest_single_params(close, high, low, atr, ...signals, sl_mult, tp_mult, ...)`**: wraps `backtest_loop` for ThreadPoolExecutor calls (no GIL due to @njit).

---

### 3. Updated sweep script (`scripts/sweep_all_coins_v2.py`)

```
For each coin in coin_list:
  1. load_cached(symbol) → DataFrame
  2. compute_signals(df, signal_params)  [CPU, vectorized]
  3. run_gpu_sweep(df_signals, param_grid)  [GPU, all combos at once]
  4. save best N results to PostgreSQL + CSV
  5. log timing

Total: ~400 coins × ~2s GPU per coin = ~13 minutes (vs 6–60 hours)
```

**CLI args**: `--symbols all|top100|custom_list.csv`, `--top-n 10` (save best N per coin), `--sl-range`, `--tp-range`, `--output-dir`

---

### 4. Dashboard v394 (`scripts/dashboard_v394.py`)

**Base**: copy of v392 with targeted additions. Existing modes (single backtest, coin sweep, portfolio) preserved.

**New: "GPU Sweep" tab** (added as a new tab in the existing tab structure):
- Symbol selector + date range
- Param range controls: SL min/max/step, TP min/max/step, cooldown multi-select, BE trigger multi-select
- "Run GPU Sweep" button
- Progress indicator (spinner + combo count + estimated VRAM usage)
- Results:
  - **Heatmap** (go.Heatmap): SL vs TP colored by net_pnl or expectancy
  - **Top-20 table** (st.dataframe): all metrics, sorted by expectancy
  - **Export CSV** button

**Portfolio mode improvements** (same tab, new execution path):
- `use_gpu_cpu = st.checkbox("Use compiled core (faster)", value=True)`
- When checked: replace `run_backtest()` calls with `jit_backtest.backtest_loop()` wrapped in ThreadPoolExecutor(max_workers=8)
- Falls back to existing path if Numba unavailable

**Sidebar GPU status panel** (below existing controls):
```
GPU: NVIDIA RTX 3060
VRAM: 11.8GB free / 12.0GB total
CUDA: 12.x | Numba: 0.60.x
```
Uses `get_cuda_info()` with `@st.cache_data(ttl=60)`.

---

## Build Script (`scripts/build_cuda_engine.py`)

Single script creates all new files:
1. Writes `engine/cuda_sweep.py` — full source
2. `py_compile.compile("engine/cuda_sweep.py", doraise=True)`
3. Writes `engine/jit_backtest.py` — full source
4. `py_compile.compile("engine/jit_backtest.py", doraise=True)`
5. Writes `scripts/sweep_all_coins_v2.py` — full source
6. `py_compile.compile("scripts/sweep_all_coins_v2.py", doraise=True)`
7. Writes `scripts/dashboard_v394.py` — full source (copy v392 + additions)
8. `py_compile.compile("scripts/dashboard_v394.py", doraise=True)`
9. Prints: `[OK] All 4 files compiled clean.`

NEVER overwrites existing files. Checks existence first, exits with error if any target already exists.

---

## Dependencies

Already installed: `numba`, `numpy`, `pandas`, `streamlit`, `plotly`
No new pip installs required (user confirmed numba is installed).
CUDA toolkit: verified via `numba.cuda.is_available()` at runtime.

---

## Verification

1. **Syntax**: build script runs py_compile on all 4 files before reporting success
2. **CUDA check**: `python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"`
   Expected: `{'device': 'NVIDIA GeForce RTX 3060', ...}`
3. **Single-coin sweep**:
   `python engine/cuda_sweep.py --symbol RIVERUSDT`
   Expected: prints sorted results table, ~1–2 seconds total
4. **Dashboard**: `streamlit run scripts/dashboard_v394.py` → navigate to GPU Sweep tab → run → heatmap appears
5. **Fallback**: temporarily set `NUMBA_DISABLE_JIT=1` in env → confirm dashboard falls back to CPU path without crash

---

## Vault Log Copy
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-sweep-engine.md`
