# CUDA Acceleration — Four Pillars Sweep Engine & Dashboard v3.9.4

**Date**: 2026-03-03
**Scope**: Full — engine layer + scripts + dashboard_v394
**Audit**: Complete (2026-03-03) — all critical/medium gaps resolved below

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
- `scripts/build_cuda_engine.py` — build script: creates all files, runs py_compile on each

### New (dashboard):
- `scripts/dashboard_v394.py` — new version (never overwrite v392/v393)

### New (sweep orchestrator):
- `scripts/sweep_all_coins_v2.py` — replaces sequential coin loop with GPU sweep per coin

---

## Architecture

### 1. CUDA Kernel (`engine/cuda_sweep.py`)

**GPU thread model**: one thread per parameter combo.

**Input arrays (on GPU device, float32, read-only — 12 arrays total):**
```
# Price
close[N], high[N], low[N], atr[N]

# Entry signals (int8 boolean)
long_a[N], long_b[N], short_a[N], short_b[N]
reentry_long[N], reentry_short[N]          # CORRECT names (engine lines 113-114)

# Cloud3 gates (int8 boolean) — REQUIRED to gate grade B entries correctly
cloud3_ok_long[N], cloud3_ok_short[N]      # engine lines 106-107, 259-260
```

**Param grid (float32, shape [N_combos, 4]):**
```
param_grid[c] = [sl_mult, tp_mult, be_trigger_atr, cooldown]
```
Note: `notional` and `commission_rate` are scalar kernel args, NOT per-combo — they are constant across all parameter combinations.

**tp_mult sentinel: 999.0** = no TP (hold until SL or end of data). Never use 0.0 — that sets TP at entry price, causing immediate exit. Confirmed: engine uses `tp_mult=None`; 999.0 maps cleanly to float32 and will never be hit.

**Output (float32, shape [N_combos, 9]):**
```
results[c] = [total_trades, win_rate, net_pnl, expectancy,
              max_dd_pct, profit_factor, lsg_pct, sharpe, be_raise_count]
```

**Per-thread private state (Numba CUDA local arrays — `cuda.local.array(4, numba.float32)` syntax required):**
```python
# Position slots (4 max)
pos_active   = cuda.local.array(4, numba.int8)    # 0=empty, 1=open
pos_dir      = cuda.local.array(4, numba.int8)    # 1=LONG, -1=SHORT
pos_entry    = cuda.local.array(4, numba.float32) # entry price
pos_sl       = cuda.local.array(4, numba.float32) # stop loss price
pos_tp       = cuda.local.array(4, numba.float32) # take profit price (999.0=none)
pos_be_raised= cuda.local.array(4, numba.int8)    # 1 if BE raise already applied

# Per-thread scalars (in registers)
equity         # running realized PnL
peak_equity    # for drawdown tracking
max_dd         # max drawdown dollar
last_entry_bar # cooldown tracking (global across all slots, matches engine)
trade_count, win_count
pnl_sum        # for expectancy
lsg_count      # losers that saw green

# Welford online variance (for Sharpe — no per-trade list in kernel)
wf_n, wf_mean, wf_M2   # incremental mean/variance of per-trade net PnL
```

**Kernel entry logic (matches engine exactly):**
```
Per bar i:
  1. Check exits: for each active slot, if high[i]>=pos_tp or low[i]<=pos_sl
     → close, record trade, update Welford state, track LSG
  2. Update BE raise: for each active slot, if unrealized_pnl > be_trigger_atr * atr[i]
     and not pos_be_raised → move pos_sl to entry, set pos_be_raised=1
  3. Cooldown check: cooldown_ok = (i - last_entry_bar) >= cooldown param
  4. Active count + direction conflict gate:
       has_longs  = any(pos_dir[s]==1  for active s)
       has_shorts = any(pos_dir[s]==-1 for active s)
       can_enter  = active_count < 4 and cooldown_ok
  5. Entry priority (matches engine):
       long_a[i]  and not has_shorts and can_enter          → open LONG
       short_a[i] and not has_longs  and can_enter          → open SHORT
       long_b[i]  and not has_shorts and can_enter and cloud3_ok_long[i]  → open LONG
       short_b[i] and not has_longs  and can_enter and cloud3_ok_short[i] → open SHORT
       reentry_long[i]  and not has_shorts and can_enter and cloud3_ok_long[i]  → open LONG
       reentry_short[i] and not has_longs  and can_enter and cloud3_ok_short[i] → open SHORT
  6. Update equity curve (unrealized)
End of data: close all open slots at close[-1]
Compute: sharpe = wf_mean / sqrt(wf_M2 / wf_n)  (Welford's formula)
Write results[thread_id]
```

**Known simplifications vs full engine (documented in kernel docstring):**
- **Fixed ATR SL only** — no AVWAP dynamic SL ratcheting. SL set once at entry: `entry ± sl_mult * atr`. Results will differ from v392 by ~10-20% on PnL for coins where AVWAP trail exits early.
- **No scale-outs** — partial exits at AVWAP checkpoints not implemented. Trade count and PnL will differ.
- **No ADD entries** — AVWAP-based pyramid limit orders require AVWAPTracker state, not feasible in kernel.
- **Reentry as immediate market entry** — `reentry_long/reentry_short` signals used as direct entries, not AVWAP limit orders as in engine.
- **Grade labeling simplified** — all entries labeled by signal type (A/B/RE); grade C pyramid labeling omitted (cosmetic only, doesn't affect metrics).
- **`allow_c_trades=True`, `b_open_fresh=True`** — fixed constants in kernel, not swept.
- **`be_lock_atr=0.0`** — fixed constant (SL raises exactly to entry price); not swept.
- **No rebate** — commission applied as `notional * commission_rate * 2` per trade (entry + exit). Daily rebate post-processed in Python wrapper from trade count.

**Kernel launch:**
```python
threads_per_block = 256
blocks = math.ceil(N_combos / threads_per_block)
backtest_kernel[blocks, threads_per_block](
    close_d, high_d, low_d, atr_d,
    long_a_d, long_b_d, short_a_d, short_b_d,
    reentry_long_d, reentry_short_d,
    cloud3_ok_long_d, cloud3_ok_short_d,
    param_grid_d,
    notional,        # scalar
    commission_rate, # scalar
    results_d,
)
cuda.synchronize()
```

**Python wrapper `run_gpu_sweep(df_signals, param_grid_np, notional, commission_rate)`:**
1. Validate required columns exist (including `cloud3_allows_long/cloud3_allows_short`)
2. Extract numpy arrays, cast to float32/int8, move to GPU via `cuda.to_device()`
3. Launch kernel, synchronize
4. Copy results back, build DataFrame with column names
5. Add `rebate` column: `trade_count * notional * commission_rate * 0.70` (approx daily rebate)
6. Return sorted by `net_pnl` descending

**`build_param_grid(sl_range, tp_range, cooldown_vals, be_vals)`:**
- Default: sl=[0.5..3.0 step 0.25], tp=[999.0, 0.5..4.0 step 0.25], cooldown=[0,3,5,10], be=[0.0,0.5,1.0]
- 11 × 15 × 4 × 3 = 1,980 combos (fits easily, RTX 3060 has headroom for 10K+)

**`get_cuda_info()`**: device name, VRAM total/free, CUDA version. Used by dashboard sidebar.

---

### 2. CPU Compiled Core (`engine/jit_backtest.py`)

**`@njit backtest_loop(close, high, low, atr, long_a, long_b, short_a, short_b, reentry_long, reentry_short, cloud3_ok_long, cloud3_ok_short, sl_mult, tp_mult, be_trigger_atr, cooldown, notional, commission_rate)`**

- Same logic and column names as kernel
- Returns `(trade_count, win_count, net_pnl, max_dd_pct, lsg_pct, sharpe, equity_curve_array)`
- `equity_curve_array` needed for portfolio alignment in dashboard
- Falls back to pure Python if `numba` not available (ImportError catch at module level)

**Warm-up call at module import:**
```python
# Trigger JIT compilation at import time with dummy 10-bar arrays
# Prevents 1-5 second freeze on first real call from dashboard
_warmup_done = False
def ensure_warmup():
    global _warmup_done
    if not _warmup_done:
        _dummy = np.zeros(10, dtype=np.float32)
        _dummy_b = np.zeros(10, dtype=np.int8)
        backtest_loop(_dummy, _dummy, _dummy, _dummy+0.01,
                      _dummy_b, _dummy_b, _dummy_b, _dummy_b,
                      _dummy_b, _dummy_b, _dummy_b, _dummy_b,
                      1.0, 999.0, 1.0, 3, 5000.0, 0.0008)
        _warmup_done = True
```

---

### 3. Updated sweep script (`scripts/sweep_all_coins_v2.py`)

```
For each coin in coin_list:
  1. load_cached(symbol) → DataFrame
  2. compute_signals(df, signal_params)  [CPU, vectorized — unchanged]
  3. Validate: cloud3_allows_long/short columns present
  4. run_gpu_sweep(df_signals, param_grid)  [GPU, all combos at once]
  5. Save top-N results to PostgreSQL + CSV
  6. Log timing per coin

Total: ~400 coins × ~2s GPU = ~13 minutes (vs 6–60 hours current)
```

**CLI**: `--symbols all|top100|<csv>`, `--top-n 10`, `--sl-range 0.5 3.0 0.25`, `--tp-range 0.5 4.0 0.25`, `--output-dir`

---

### 4. Dashboard v394 (`scripts/dashboard_v394.py`)

**Base**: copy of v392 with targeted additions. Existing modes preserved.

**Equity curve date filter bug**: v392 has this known bug (was being fixed in v393). Fix it in v394 during copy:
- Clear `st.session_state["equity_cache"]` when date range or params change
- Tie cache invalidation to `params_hash` (already computed in v392 as `compute_params_hash()`)

**New "GPU Sweep" tab:**
- Symbol selector + date range
- Param range controls: SL min/max/step, TP min/max/step, cooldown multi-select, BE trigger multi-select
- Combo count preview: `st.metric("Combos", len(build_param_grid(...)))`
- "Run GPU Sweep" button → spinner during kernel execution
- Results:
  - Heatmap (`go.Heatmap`): SL vs TP grid, color = net_pnl or expectancy (user toggle)
  - Top-20 table (`st.dataframe`): all 9 metrics, sorted by expectancy
  - Export CSV button

**Portfolio mode (compiled core checkbox):**
```python
use_compiled = st.checkbox("Use compiled core (faster)", value=True)
```
When checked: replace `run_backtest()` calls with `jit_backtest.backtest_loop()` in a `ThreadPoolExecutor`.

**ThreadPoolExecutor pattern — workers must NOT call `st.*`:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

futures = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    for sym, df in coin_data.items():
        futures[ex.submit(jit_backtest.backtest_loop, *arrays_from(df), *params)] = sym

coin_results = []
for fut in as_completed(futures):
    sym = futures[fut]
    result = fut.result()   # returns plain tuple, no st.* calls
    coin_results.append((sym, result))
# All st.* updates happen HERE in main thread
```

**Sidebar GPU status panel:**
```
GPU: NVIDIA GeForce RTX 3060
VRAM: 11.8 GB free / 12.0 GB total
CUDA 12.x | Numba 0.60.x
```
Uses `get_cuda_info()` with `@st.cache_data(ttl=60)`. Graceful: shows "No CUDA device" if unavailable.

---

## Build Script (`scripts/build_cuda_engine.py`)

Creates files in this order (each followed immediately by py_compile):
1. `engine/cuda_sweep.py`
2. `engine/jit_backtest.py`
3. `scripts/sweep_all_coins_v2.py`
4. `scripts/dashboard_v394.py` (copy of v392 + additions + equity curve fix)

Checks existence before writing each file — exits with error if any target already exists.
Final line: `print("[OK] All 4 files compiled clean.")` — only reached if all py_compile pass.

---

## Dependencies

Already installed: `numba`, `numpy`, `pandas`, `streamlit`, `plotly`
No new pip installs required.
CUDA toolkit verified via `numba.cuda.is_available()` at runtime.

---

## Verification

1. **Syntax**: build script py_compile passes for all 4 files
2. **CUDA check**:
   ```
   python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"
   ```
   Expected: `{'device': 'NVIDIA GeForce RTX 3060', 'vram_free_gb': ..., ...}`
3. **Single-coin GPU sweep**:
   ```
   python engine/cuda_sweep.py --symbol RIVERUSDT
   ```
   Expected: sorted results table printed, elapsed ~1–2 seconds
4. **Dashboard**:
   ```
   streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py"
   ```
   Navigate to GPU Sweep tab → select symbol → Run → heatmap renders
5. **CUDA fallback**: set `NUMBA_DISABLE_JIT=1` → dashboard loads, GPU Sweep shows "CUDA unavailable" message, portfolio uses Python path without crash

---

## Audit Log (2026-03-03)

Issues found and resolved in this plan revision:

| # | Severity | Issue | Resolution |
|---|----------|-------|------------|
| 1 | Critical | Column names `re_long/re_short` wrong | Fixed to `reentry_long/reentry_short` throughout |
| 2 | Critical | Missing `cloud3_allows_long/short` arrays | Added as 2 additional kernel inputs (12 total) |
| 3 | Critical | `tp_mult=0.0` sentinel causes instant exit | Changed to `999.0` sentinel |
| 4 | Critical | Notional per-combo in param_grid | Moved to scalar kernel arg, param_grid now [N,4] |
| 5 | Medium | AVWAP dynamic SL omitted silently | Documented in kernel docstring as known simplification |
| 6 | Medium | Scale-out omitted silently | Documented as excluded (ADD, scale-out, RE limit orders all excluded) |
| 7 | Medium | `pos_be_raised[4]` missing | Added to per-thread state |
| 8 | Medium | Grade C labeling not designed | Documented as cosmetic simplification (C label omitted, trade still taken) |
| 9 | Medium | Direction conflict gate missing | Added to kernel entry logic (`not has_shorts` / `not has_longs`) |
| 10 | Medium | Sharpe unspecified in kernel | Welford's online variance added to per-thread state |
| 11 | Low | `be_lock_atr` not addressed | Documented as fixed constant `0.0` in kernel |
| 12 | Low | `allow_c_trades` / `b_open_fresh` silent | Documented as fixed `True` constants |
| 13 | Low | Reentry simplified | Documented as immediate market entry, not AVWAP limit |
| 14 | Low | ADD mechanism absent | Documented as excluded |
| 15 | Low | Numba local array syntax | Specified `cuda.local.array(4, numba.float32)` |
| 16 | Low | v394 inherits v392 equity curve bug | Fixed: cache invalidation tied to `params_hash` |
| 17 | Low | ThreadPoolExecutor + st.* crash | Workers return plain tuples; all st.* in main thread |
| 18 | Low | @njit warm-up freeze | `ensure_warmup()` call at module import |

---

## Vault Log Copy
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-sweep-engine.md`
