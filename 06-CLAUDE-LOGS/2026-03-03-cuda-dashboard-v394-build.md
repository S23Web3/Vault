# CUDA Dashboard v3.9.4 — Build Session

**Date**: 2026-03-03
**Status**: LIVE — GPU sweep confirmed working on RTX 3060, Python 3.12, CUDA 12.4, Numba 0.64.

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

## Files Created (all confirmed working)

| File | Status |
|------|--------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` | LIVE — GPU detected, kernel compiles |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\jit_backtest.py` | Created |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py` | LIVE — GPU Sweep ran on 0GUSDT |

---

### 5. CUDA Toolkit Setup (Session 2)

Python 3.12 venv created at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312`. CUDA setup required multiple fixes:

| Issue | Fix |
|-------|-----|
| `cuda.is_available()` returns False but context works | `get_cuda_info()` crashed on `cuda.runtime.get_version()` — patched to try/except |
| `nvvm.dll` not found | `pip install nvidia-cuda-nvcc-cu12` + set `CUDA_HOME` env var |
| NVCC 12.9 too new for Numba 0.64 `CTK_SUPPORTED` map | Downgraded to `nvidia-cuda-nvcc-cu12==12.4.131` |
| `cudart.dll` not found by Numba | Copied `cudart64_12.dll` from `nvidia\cuda_runtime\bin\` into `nvidia\cuda_nvcc\bin\` |
| Numba `get_supported_ccs()` returns empty tuple | Fixed by making `cudart` loadable (above copy) — returns `(12, 4)` |

### 6. GPU Sweep Confirmed

Ran GPU Sweep on 0GUSDT — CSV exported to `C:\Users\User\Downloads\gpu_sweep_0GUSDT.csv`. Top combo: SL=0.5, TP=999 (disabled), BE=0.5, CD=5, 119 trades, $28,595 net PnL, PF 5.55.

---

## Launch Commands (future sessions)

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
$env:CUDA_HOME = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312\Lib\site-packages\nvidia\cuda_nvcc"
$env:PATH = "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312\Lib\site-packages\nvidia\cuda_runtime\bin;$env:PATH"
& "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\.venv312\Scripts\Activate.ps1"
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py"
```

---

## Key Decisions

- **Engine version**: User chose v3.9.0 (`Backtester390`) for CUDA kernel, knowing GPU sweep results will differ from existing CPU sweep (which runs v3.8.4)
- **Python version**: Python 3.12.8 in `.venv312`, side-by-side with system 3.13
- **CUDA toolkit**: pip packages (not conda) — `nvidia-cuda-nvcc-cu12==12.4.131`, `nvidia-cuda-runtime-cu12==12.4.127`, `nvidia-cuda-nvrtc-cu12==12.4.127`
- **Build approach**: Single build script copies v392 + applies text patches rather than embedding 2371 lines of dashboard source
- **Commission fix**: `fix_audit_bugs.py` patched build script to separate taker (0.0008) entry / maker (0.0002) exit commission

---

### 7. GPU Portfolio Sweep Mode (Session 3)

Added multi-coin GPU sweep mode to dashboard v3.9.4.

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_gpu_portfolio_sweep.py`

**What it adds**:
- `run_gpu_sweep_multi()` in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` — loops coins on host, CUDA kernel per coin
- "GPU Portfolio Sweep" sidebar button + full mode block in dashboard
- Coin selection (Top N / Lowest N / Random N / Custom), Load/Save portfolio
- Capital model: Per-Coin Independent (N x $10k) or Shared Pool (user total + per-trade notional)
- Parameter ranges: SL/TP/BE/cooldown (same as single GPU Sweep)
- Progress bar per coin during sweep

**Results display** (two views):
1. **Uniform Params** (shown first) — each param combo applied identically to ALL coins. Honest portfolio answer. Best uniform combo, top-10 table, ROI using correct capital denominator.
2. **Per-Coin Optimized** (cherry-picked) — each coin uses its own best params. Labeled as "overfitted upper bound".
3. **Uniform Params Heatmap** — SL vs TP, sum across coins for each exact combo, then best (BE, CD) per cell.
4. **Per-Coin Heatmaps** — expandable, top-5 table per coin.
5. **CSV exports** — full results + best-per-coin.

**Bugs fixed after first run**:
- ROI math: was dividing by user's $10k capital when kernel runs $10k per coin (50 coins = $500k deployed). Fixed to use N_coins x $10k for Per-Coin Independent, user's total for Shared Pool.
- Cherry-picking bias: "best per coin" sums were labeled as portfolio P&L. Now clearly separated with uniform params shown first.
- Stale params detection: changing date range / signals / capital after a run now shows warning.
- Heatmap aggregation: was cherry-picking best per coin per cell. Now sums across coins for each exact combo first.

### 8. Full Logic Audit (Session 3, continued)

Ran 3 parallel audit agents: CUDA kernel vs v390 reference, dashboard GPU modes, BingX bot.

**CRITICAL findings:**
1. Commission fix never applied — `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` still uses taker (0.0008) for both entry and exit. `fix_audit_bugs.py` patched the build script but cuda_sweep.py was never regenerated. Should be taker 0.0008 entry, maker 0.0002 exit.
2. `pnl_sum` missing entry commissions — net_pnl overstated in ALL GPU sweep results.

**HIGH findings:**
3. win_rate displayed as fraction (0.42) not percentage (42.0%) in 3 dashboard locations.
4. TTP state lost on restart — `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` doesn't reconstruct from bot-status.json.
5. WSListener dies permanently after 3 reconnect failures — no alert.
6. `_place_market_close()` missing `reduceOnly=true` in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py`.
7. `saw_green` check: kernel uses `>`, v390 uses `>=`.

**MEDIUM findings:**
8-9. Stale detection missing for single-coin GPU Sweep + doesn't cover sweep param ranges.
10. Shared Pool capital model not enforced in kernel.
11. TTP evaluates on incomplete bar.
12. Race condition TTP close vs exchange SL/TP fill.
13. Commission rate fallback mismatch.
14. No slippage protection on market orders.
15. Close-remaining missing `total_losers`/`lsg_count` update.

**LOW:** C trades checkbox misleading, capital label, lock gaps, logging gaps.

**Status**: All findings documented. No fixes applied yet — user to prioritize in next session.

### 9. Audit Fixes Applied (Session 4)

Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_audit_fixes.py`

**Reassessments:**
- HIGH #4 (TTP state lost on restart): Code already restored TTP state via `signal_engine.py` lines 113-127. No fix needed.
- HIGH #6 (reduceOnly missing): Function was in `position_monitor.py` not `executor.py`. BingX hedge mode doesn't strictly require `reduceOnly` but added as defensive measure.

**Fixes applied (all 4 files py_compile + ast.parse PASS):**

| Fix | File | Change |
|-----|------|--------|
| CRITICAL #1 | `engine\cuda_sweep.py` | Split `comm_per_side` into `entry_comm` (0.0008 taker) and `exit_comm` (0.0002 maker). New `maker_rate` param on kernel + both wrapper functions. |
| CRITICAL #2 | `engine\cuda_sweep.py` | `pnl_sum` now accumulates `net_pnl - entry_comm` (full round-trip cost). Win/loss, Welford Sharpe all use round-trip figure. |
| HIGH #3 | `scripts\dashboard_v394.py` | win_rate formatted as percentage (x100, 1dp) in 3 locations: GPU Sweep top-20, Uniform top-10, Per-coin top-5. |
| HIGH #5 | `ws_listener.py` | MAX_RECONNECT 3->10, exponential backoff (5s base, max ~160s), CRITICAL log + `logs/ws_dead_*.flag` sentinel file on death. |
| HIGH #6 | `position_monitor.py` | Added `"reduceOnly": "true"` to `_place_market_close()` order params. |
| HIGH #7 | `engine\cuda_sweep.py` | `saw_green` LONG: `>` -> `>=`, SHORT: `<` -> `<=` (matches v390 reference). |

**Remaining (MEDIUM/LOW, deferred):** Stale detection gaps, Shared Pool capital model, TTP mid-bar timing, race condition TTP vs exchange SL/TP, commission fallback mismatch, no slippage protection, close-remaining missing total_losers/lsg_count, UI tweaks, BingX lock/logging gaps.

### 10. Dashboard UX Improvements (Session 5)

**GPU Portfolio Sweep enhancements:**

| Change | Details |
|--------|---------|
| Coin selection reset | Tracks `_gp_prev_source` + `_gp_prev_n` in session state. Switching Top N / Lowest N / Random N or changing N clears locked coins + results. |
| Stop Sweep button | Sets `gp_stop_flag` checked by progress callback. `run_gpu_sweep_multi` returns early if callback returns True. |
| Reset Parameters button | Clears all `gp_*` session state keys and reruns. |
| Date range display | Shows active date range at top of GPU Portfolio Sweep page. |
| Random Week/Month (sidebar) | Added "Rand Week" / "Rand Month" to sidebar Period radio. Global date window override, works across all modes. Re-roll button. |
| Random Week/Month (GPU Portfolio) | Separate "Date Window" radio on GPU Portfolio page: Sidebar Date Range / Random Week / Random Month. Independent of coin selection. |
| Trading Volume & Rebates | Added to GPU Portfolio Sweep results (derived from best uniform combo). Total volume, gross/net commission, rebate (70%), True Net P&L. |
| Est. Trade Duration | Avg bars/trade, est. duration in minutes/hours/days, trades/coin avg. Computed from total bars stored during sweep run. |
| matplotlib crash fix | `background_gradient()` on correlation table wrapped in try/except. Falls back to plain dataframe if matplotlib missing in .venv312. |

**Bugs fixed:**
- Parquet index is int64 range (0,1,2...), not DatetimeIndex. Random window generation used `df.index` instead of `df["datetime"]` column. Caused TypeError and "0 days" span. Fixed in both sidebar and GPU Portfolio blocks.
- Bar count check `_gp_rand_days * 288` assumed 5m timeframe. Changed to `> 200` (same as signal computation minimum).
- `_gp_window_label` variable used before definition in else branch. Moved above the if/else block.

**Tomorrow's focus:** Strategy finetuning (4P stochastics, open trade scenarios), BingX bot monitoring (live).
