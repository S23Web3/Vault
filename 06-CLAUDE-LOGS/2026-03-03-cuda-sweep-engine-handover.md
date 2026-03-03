# CUDA Sweep Engine — Session Handover
**Date**: 2026-03-03
**Status**: PLAN COMPLETE, AUDITED — ready for implementation in new chat
**Context used at handover**: ~80% — new chat required before building

---

## What This Session Did

Planned CUDA/GPU acceleration for the Four Pillars parameter sweep engine and dashboard. No code was written. The plan was fully designed, then audited against the actual engine source (`backtester_v390.py`, `state_machine_v390.py`), and 18 gaps were found and resolved. The plan is now correct and ready to implement.

---

## Plan Files (read these first in new chat)

- **Primary plan**: `C:\Users\User\.claude\plans\majestic-conjuring-meerkat.md`
- **Vault copy**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-sweep-engine.md`

Both are identical and contain the full audited architecture. The vault copy is the one to keep long-term.

---

## Problem Being Solved

Sweeps and portfolio runs are fully sequential and CPU-bound:
- Single coin sweep: 500+ param combos × 10K bars = 50–100 seconds
- 400-coin full sweep: 6–60 hours
- Portfolio mode (dashboard): sequential loop through coins, no parallelism

Hardware available: RTX 3060 (3584 CUDA cores, 12GB VRAM). Currently idle for this workload.

---

## Solution Summary

**Why Numba CUDA, not PyTorch**: The backtest is a stateful bar-by-bar state machine. PyTorch cannot express this cleanly — it's designed for differentiable tensor math, not imperative branching loops. Numba `@cuda.jit` maps directly: one GPU thread = one parameter combo, each thread holds private position state in registers, all threads share read-only signal arrays. 1,980 combos → 1,980 simultaneous GPU threads.

**Expected speedup**: ~400 coins × ~2s GPU per coin = ~13 minutes total (vs 6–60 hours current).

---

## Files to Create (4 new files, no overwrites)

All via `scripts/build_cuda_engine.py` (build script written first, then user runs it):

| File | Purpose |
|------|---------|
| `engine/cuda_sweep.py` | Numba CUDA kernel + Python wrapper |
| `engine/jit_backtest.py` | Numba @njit CPU-compiled core (single run + portfolio) |
| `scripts/sweep_all_coins_v2.py` | GPU-powered multi-coin sweep orchestrator |
| `scripts/dashboard_v394.py` | Dashboard with GPU Sweep tab + faster portfolio |

The build script (`scripts/build_cuda_engine.py`) is the first thing to write. It creates all 4 files and runs `py_compile` on each.

---

## Source Files to Read Before Building

These were read in this session. Read them again in the new chat before building:

| File | Why |
|------|-----|
| `engine/backtester_v390.py` | Port position logic, entry priority, exit logic to kernel. 630 lines. |
| `signals/state_machine_v390.py` | Signal column names, grade A/B/RE logic. Confirms: `reentry_long/reentry_short` (not re_long/re_short). |
| `signals/four_pillars_v390.py` | Signal computation — confirms `cloud3_allows_long/cloud3_allows_short` column names |
| `engine/position_v384.py` | Position slot state (already simplified in kernel — just know what's being dropped) |
| `scripts/dashboard_v392.py` | Base for v394 copy. Read the portfolio mode section (lines ~1764-2100) and sweep section (lines ~1320-1599). |

All paths: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`

---

## Critical Architecture Details (verified against actual code)

### Kernel Inputs — 12 signal arrays (not 10)
```
# Price (float32)
close[N], high[N], low[N], atr[N]

# Entry signals (int8)
long_a[N], long_b[N], short_a[N], short_b[N]
reentry_long[N], reentry_short[N]    # confirmed column names from engine line 113-114

# Cloud3 gates (int8) — CRITICAL for grade B gating
cloud3_ok_long[N], cloud3_ok_short[N]   # from engine lines 106-107, 259-260
```

### Param Grid Shape — [N_combos, 4] (NOT 5)
```python
param_grid[c] = [sl_mult, tp_mult, be_trigger_atr, cooldown]
# notional and commission_rate are SCALAR kernel args, not per-combo
```

### tp_mult Sentinel — 999.0 (NOT 0.0)
- `0.0` means TP at entry price = instant exit. Never use it.
- `999.0` means no TP (hold until SL or end of data). Safe.
- Engine uses `tp_mult=None` — 999.0 maps cleanly to float32.

### Per-Thread Position State (Numba CUDA local arrays)
Numba CUDA requires `cuda.local.array(4, numba.float32)` syntax — Python list `[0,0,0,0]` raises error inside `@cuda.jit`.
```python
pos_active    = cuda.local.array(4, numba.int8)    # 0=empty, 1=open
pos_dir       = cuda.local.array(4, numba.int8)    # 1=LONG, -1=SHORT
pos_entry     = cuda.local.array(4, numba.float32)
pos_sl        = cuda.local.array(4, numba.float32)
pos_tp        = cuda.local.array(4, numba.float32) # 999.0 = no TP
pos_be_raised = cuda.local.array(4, numba.int8)    # 0 or 1
```
Plus scalars in registers: `equity, peak_equity, max_dd, last_entry_bar, trade_count, win_count, pnl_sum, lsg_count, wf_n, wf_mean, wf_M2`.

### Sharpe in Kernel — Welford's Online Variance
No per-trade PnL list in a GPU kernel. Use Welford's:
```python
# On each trade close:
wf_n += 1
delta = trade_net_pnl - wf_mean
wf_mean += delta / wf_n
wf_M2 += delta * (trade_net_pnl - wf_mean)
# At end:
# variance = wf_M2 / wf_n
# sharpe = wf_mean / sqrt(variance) if variance > 0 else 0.0
```

### Direction Conflict Gate (matches engine exactly)
```python
has_longs  = any pos_dir[s]==1  for active s
has_shorts = any pos_dir[s]==-1 for active s
# Grade A long: not has_shorts and can_enter
# Grade A short: not has_longs and can_enter
# Grade B long: not has_shorts and can_enter and cloud3_ok_long[i]
# Grade B short: not has_longs and can_enter and cloud3_ok_short[i]
```

### Known Kernel Simplifications (documented, intentional)
These diverge from the full v392 engine — sweep results approximate, not exact:
- **Fixed ATR SL only** — no AVWAP dynamic SL ratcheting (ratchet needs running VWAP state, not feasible per-thread)
- **No scale-outs** — AVWAP checkpoint partial exits omitted
- **No ADD entries** — AVWAP-based pyramid limit orders omitted
- **Reentry = immediate market entry** — uses signal column, not AVWAP limit order
- **Grade C labeling omitted** — A/B fires while in-position still enters, just labeled A/B not C (cosmetic)
- **Fixed constants**: `allow_c_trades=True, b_open_fresh=True, be_lock_atr=0.0`

### Dashboard v394 Base — v392 with equity curve bug fix
- Copy v392 (stable baseline), NOT v393 (has IndentationError)
- Apply equity curve date filter fix: tie cache invalidation to `compute_params_hash()` (already in v392)
- This resolves the known bug that v393 was trying to fix

### ThreadPoolExecutor in Dashboard — workers must NOT call st.*
```python
with ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(jit_backtest.backtest_loop, *arrays, *params): sym
               for sym, arrays in coin_data.items()}
results = [(futures[f], f.result()) for f in as_completed(futures)]
# All st.* calls happen AFTER this block in main thread
```

### Numba @njit Warm-up
Add `ensure_warmup()` to `jit_backtest.py` — call at module import with 10-bar dummy arrays.
Prevents 1–5 second freeze on first real portfolio run in dashboard.

---

## Default Param Grid

```python
sl_vals      = np.arange(0.5, 3.25, 0.25)   # 11 values
tp_vals      = [999.0] + list(np.arange(0.5, 4.25, 0.25))  # 16 values (999.0 = no TP)
cooldown_vals = [0, 3, 5, 10]                 # 4 values
be_vals       = [0.0, 0.5, 1.0]              # 3 values
# Total: 11 × 16 × 4 × 3 = 2,112 combos
# RTX 3060 headroom: comfortable up to 10,000+ combos
```

---

## Audit Log (18 issues found and resolved)

| # | Sev | Issue | Fix |
|---|-----|-------|-----|
| 1 | CRIT | Column names `re_long/re_short` wrong | Fixed to `reentry_long/reentry_short` |
| 2 | CRIT | Missing `cloud3_allows_long/short` arrays | Added as 2 additional kernel inputs (12 total) |
| 3 | CRIT | `tp_mult=0.0` sentinel causes instant exit | Changed to `999.0` sentinel |
| 4 | CRIT | Notional per-combo in param_grid wastes memory | Moved to scalar kernel arg; param_grid now [N,4] |
| 5 | MED | AVWAP dynamic SL omitted silently | Documented as known simplification in kernel docstring |
| 6 | MED | Scale-out omitted silently | Documented as excluded |
| 7 | MED | `pos_be_raised[4]` missing from state | Added to per-thread local arrays |
| 8 | MED | Grade C labeling not designed | Documented as cosmetic omission |
| 9 | MED | Direction conflict gate missing | Added `not has_shorts`/`not has_longs` to entry logic |
| 10 | MED | Sharpe unspecified in kernel | Welford's online variance added to thread state |
| 11 | LOW | `be_lock_atr` not addressed | Documented as fixed `0.0` constant |
| 12 | LOW | `allow_c_trades`/`b_open_fresh` silent | Documented as fixed `True` constants |
| 13 | LOW | Reentry simplified | Documented as immediate market entry, not AVWAP limit |
| 14 | LOW | ADD mechanism absent | Documented as excluded |
| 15 | LOW | Numba local array syntax missing | Specified `cuda.local.array(4, numba.float32)` |
| 16 | LOW | v394 inherits v392 equity curve bug | Fixed: tie cache to `compute_params_hash()` |
| 17 | LOW | ThreadPoolExecutor + st.* crash risk | Workers return plain tuples; st.* in main thread only |
| 18 | LOW | @njit warm-up freeze | `ensure_warmup()` at module import |

---

## Permissions Pre-Approved in This Session

User approved full scope. No new approvals needed in next chat for:
- Write new files: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/sweep_all_coins_v2.py`, `scripts/dashboard_v394.py`, `scripts/build_cuda_engine.py`
- Bash: py_compile one-liners only (`python -c "import py_compile; ..."`)
- Read: any source file in the backtester project

No git, no network, no script execution except py_compile.

---

## Build Order in New Chat

1. Load Python skill (`/python`)
2. Read source files (list above) to confirm no changes since this session
3. Write `scripts/build_cuda_engine.py` → py_compile it
4. Tell user: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_cuda_engine.py"`
5. User runs build script → all 4 files created + py_compiled
6. Verify: `python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"`
7. Test sweep: `python engine/cuda_sweep.py --symbol RIVERUSDT`
8. Test dashboard: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py"`

---

## Run Commands (for new chat to give user)

```bash
# Run the build script
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_cuda_engine.py"

# Verify CUDA
python -c "from engine.cuda_sweep import get_cuda_info; print(get_cuda_info())"

# Test single-coin sweep
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py" --symbol RIVERUSDT

# Launch dashboard
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py"
```

---

## PRODUCT-BACKLOG.md Update Needed

Add to backlog in new chat after implementation:
- Task: CUDA sweep engine + dashboard v394
- Status: IN PROGRESS → COMPLETE after build
- Notes: engine/cuda_sweep.py + engine/jit_backtest.py + dashboard_v394.py

---

## Memory Files That May Need Updating After Build

- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-backtester.md` — add cuda_sweep.py and jit_backtest.py to engine inventory
- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-dashboard.md` — add dashboard_v394 status
- `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md` — update dashboard version when v394 promoted to production