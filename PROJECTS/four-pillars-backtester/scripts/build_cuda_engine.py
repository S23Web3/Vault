"""
Build script: CUDA sweep engine + JIT backtest core + dashboard v3.9.4.

Creates 3 files:
  1. engine/cuda_sweep.py     -- Numba CUDA kernel + Python wrapper + get_cuda_info()
  2. engine/jit_backtest.py   -- Numba @njit CPU-compiled core for portfolio
  3. scripts/dashboard_v394.py -- v392 copy + GPU Sweep mode + JIT portfolio + GPU sidebar

Run from backtester root:
  python scripts/build_cuda_engine.py

All files are py_compile validated after writing. No file is overwritten.
"""

import os
import sys
import shutil
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"
SCRIPTS = ROOT / "scripts"

TARGETS = {
    "cuda_sweep":    ENGINE / "cuda_sweep.py",
    "jit_backtest":  ENGINE / "jit_backtest.py",
    "dashboard":     SCRIPTS / "dashboard_v394.py",
}

ERRORS = []


def check_targets():
    """Exit if any target file already exists."""
    for name, path in TARGETS.items():
        if path.exists():
            print("ERROR: " + str(path) + " already exists. Remove it first.")
            sys.exit(1)


def validate(path):
    """py_compile a file. Append to ERRORS on failure."""
    try:
        py_compile.compile(str(path), doraise=True)
        print("[OK] " + path.name)
    except py_compile.PyCompileError as e:
        print("[FAIL] " + path.name + ": " + str(e))
        ERRORS.append(path.name)


# ============================================================================
# FILE 1: engine/cuda_sweep.py
# ============================================================================
CUDA_SWEEP_SRC = r'''"""
CUDA GPU sweep engine for Four Pillars v3.9.0 parameter optimization.

One GPU thread per parameter combo. Reads shared signal arrays (read-only),
maintains private position state in registers/local arrays.

Known simplifications (intentional):
  - Fixed ATR SL only -- no AVWAP dynamic SL ratcheting
  - No scale-outs (AVWAP checkpoint partial exits omitted)
  - No ADD entries (AVWAP pyramid limit orders omitted)
  - Reentry = immediate market entry (uses signal column, not AVWAP limit order)
  - Grade C = A/B signal while in same-direction position (allow_c_trades=True)
  - Fixed constants: b_open_fresh=True, be_lock_atr=0.0
  - Commission: taker rate only (no maker/taker split, no rebate settlement)

Port source: engine/backtester_v390.py (position logic, entry priority, exit logic)
"""

import math
import numpy as np
import pandas as pd

try:
    import numba
    from numba import cuda, int8, int32, float32
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False


def get_cuda_info():
    """Return dict with GPU device info for sidebar display."""
    if not CUDA_AVAILABLE:
        return None
    try:
        device = cuda.get_current_device()
        ctx = device.get_primary_context()
        free, total = cuda.current_context().get_memory_info()
        return {
            "device": device.name.decode() if isinstance(device.name, bytes) else str(device.name),
            "vram_total_gb": round(total / (1024 ** 3), 1),
            "vram_free_gb": round(free / (1024 ** 3), 1),
            "cuda_version": ".".join(str(x) for x in cuda.runtime.get_version()),
            "numba_version": numba.__version__,
        }
    except Exception:
        return None


def build_param_grid(
    sl_range=None,
    tp_range=None,
    cooldown_vals=None,
    be_vals=None,
    include_no_tp=True,
):
    """Build [N_combos, 4] float32 param grid: [sl_mult, tp_mult, be_trigger_atr, cooldown].

    tp_mult sentinel: 999.0 = no TP (hold until SL or end of data).
    NEVER use 0.0 -- that means TP at entry price = instant exit.
    """
    if sl_range is None:
        sl_range = np.arange(0.5, 3.25, 0.25)
    if tp_range is None:
        tp_range = np.arange(0.5, 4.25, 0.25)
    if cooldown_vals is None:
        cooldown_vals = [0, 3, 5, 10]
    if be_vals is None:
        be_vals = [0.0, 0.5, 1.0]

    tp_list = list(tp_range)
    if include_no_tp:
        tp_list = [999.0] + tp_list

    combos = []
    for sl in sl_range:
        for tp in tp_list:
            for cd in cooldown_vals:
                for be in be_vals:
                    combos.append([float(sl), float(tp), float(be), float(cd)])
    return np.array(combos, dtype=np.float32)


if CUDA_AVAILABLE:
    @cuda.jit
    def backtest_kernel(
        close, high, low, atr,
        long_a, long_b, short_a, short_b,
        reentry_long, reentry_short,
        cloud3_ok_long, cloud3_ok_short,
        param_grid, N, N_combos,
        notional, commission_rate,
        results,
    ):
        """One thread per param combo. Bar-by-bar backtest matching v3.9.0 logic.

        Entry priority: A long > A short > B long > B short > RE long > RE short.
        Grade C: A/B signal while same-direction position open (allow_c_trades=True).
        Reentry: cloud3-gated (matches backtester_v390 line 328).
        BE raise: be_trigger_atr checked every bar, locks SL at entry (be_lock_atr=0.0).
        """
        c = cuda.grid(1)
        if c >= N_combos:
            return

        sl_mult         = param_grid[c, 0]
        tp_mult         = param_grid[c, 1]
        be_trigger_atr  = param_grid[c, 2]
        cooldown_bars   = int32(param_grid[c, 3])

        # Per-thread position state (4 slots)
        pos_active    = cuda.local.array(4, int8)
        pos_dir       = cuda.local.array(4, int8)     # 1=LONG, -1=SHORT
        pos_entry     = cuda.local.array(4, float32)
        pos_sl        = cuda.local.array(4, float32)
        pos_tp        = cuda.local.array(4, float32)   # 999.0 = no TP
        pos_be_raised = cuda.local.array(4, int8)
        pos_be_trigger = cuda.local.array(4, float32)
        pos_atr       = cuda.local.array(4, float32)

        for s in range(4):
            pos_active[s] = 0

        # Scalar state
        equity = float32(10000.0)
        peak_equity = float32(10000.0)
        max_dd = float32(0.0)
        last_entry_bar = int32(-999)
        trade_count = int32(0)
        win_count = int32(0)
        pnl_sum = float32(0.0)
        gross_profit = float32(0.0)
        gross_loss = float32(0.0)
        lsg_count = int32(0)
        total_losers = int32(0)

        # Welford online variance for Sharpe
        wf_n = int32(0)
        wf_mean = float32(0.0)
        wf_M2 = float32(0.0)

        comm_per_side = notional * commission_rate

        for i in range(N):
            if atr[i] != atr[i]:  # isnan check
                continue

            # ── Step 1: Check exits (SL first = pessimistic) ──────────────
            for s in range(4):
                if pos_active[s] == 0:
                    continue

                exit_price = float32(0.0)
                exited = int8(0)
                saw_green = int8(0)

                if pos_dir[s] == 1:  # LONG
                    # Check if trade went green at any point (using high)
                    if high[i] > pos_entry[s]:
                        saw_green = 1
                    if low[i] <= pos_sl[s]:
                        exit_price = pos_sl[s]
                        exited = 1
                    elif tp_mult < float32(998.0) and high[i] >= pos_tp[s]:
                        exit_price = pos_tp[s]
                        exited = 1
                else:  # SHORT
                    if low[i] < pos_entry[s]:
                        saw_green = 1
                    if high[i] >= pos_sl[s]:
                        exit_price = pos_sl[s]
                        exited = 1
                    elif tp_mult < float32(998.0) and low[i] <= pos_tp[s]:
                        exit_price = pos_tp[s]
                        exited = 1

                if exited == 1:
                    if pos_dir[s] == 1:
                        raw_pnl = (exit_price - pos_entry[s]) / pos_entry[s] * notional
                    else:
                        raw_pnl = (pos_entry[s] - exit_price) / pos_entry[s] * notional
                    net_pnl = raw_pnl - comm_per_side  # exit commission

                    trade_count += 1
                    pnl_sum += net_pnl
                    if net_pnl > 0:
                        win_count += 1
                        gross_profit += net_pnl
                    else:
                        gross_loss += (-net_pnl)
                        total_losers += 1
                        if saw_green == 1:
                            lsg_count += 1

                    # Welford update
                    wf_n += 1
                    delta = net_pnl - wf_mean
                    wf_mean += delta / float32(wf_n)
                    wf_M2 += delta * (net_pnl - wf_mean)

                    equity += net_pnl
                    pos_active[s] = 0

            # ── Step 2: BE raise check ────────────────────────────────────
            for s in range(4):
                if pos_active[s] == 0 or pos_be_raised[s] == 1:
                    continue
                if be_trigger_atr <= float32(0.0):
                    continue
                if pos_dir[s] == 1:  # LONG
                    if high[i] >= pos_be_trigger[s]:
                        pos_be_raised[s] = 1
                        # be_lock_atr=0.0 -> lock at entry price
                        if pos_entry[s] > pos_sl[s]:
                            pos_sl[s] = pos_entry[s]
                else:  # SHORT
                    if low[i] <= pos_be_trigger[s]:
                        pos_be_raised[s] = 1
                        if pos_entry[s] < pos_sl[s]:
                            pos_sl[s] = pos_entry[s]

            # ── Step 3: Entries ────────────────────────────────────────────
            active_count = int32(0)
            has_longs = int8(0)
            has_shorts = int8(0)
            for s in range(4):
                if pos_active[s] == 1:
                    active_count += 1
                    if pos_dir[s] == 1:
                        has_longs = 1
                    else:
                        has_shorts = 1

            cooldown_ok = int8(0)
            if (i - last_entry_bar) >= cooldown_bars:
                cooldown_ok = 1

            can_enter = int8(0)
            if active_count < 4 and cooldown_ok == 1:
                can_enter = 1

            did_enter = int8(0)

            # Grade A long: no cloud3 gate
            if long_a[i] != 0 and has_shorts == 0 and can_enter == 1 and did_enter == 0:
                slot = int8(-1)
                for s in range(4):
                    if pos_active[s] == 0:
                        slot = int8(s)
                        break
                if slot >= 0:
                    # C relabel: if already has longs, this is continuation (allow_c_trades=True)
                    pos_active[slot] = 1
                    pos_dir[slot] = 1
                    pos_entry[slot] = close[i]
                    pos_sl[slot] = close[i] - atr[i] * sl_mult
                    pos_atr[slot] = atr[i]
                    if tp_mult < float32(998.0):
                        pos_tp[slot] = close[i] + atr[i] * tp_mult
                    else:
                        pos_tp[slot] = float32(999999.0)
                    pos_be_raised[slot] = 0
                    if be_trigger_atr > float32(0.0):
                        pos_be_trigger[slot] = close[i] + atr[i] * be_trigger_atr
                    else:
                        pos_be_trigger[slot] = float32(999999.0)
                    equity -= comm_per_side  # entry commission
                    last_entry_bar = i
                    did_enter = 1

            # Grade A short: no cloud3 gate
            if short_a[i] != 0 and has_longs == 0 and can_enter == 1 and did_enter == 0:
                slot = int8(-1)
                for s in range(4):
                    if pos_active[s] == 0:
                        slot = int8(s)
                        break
                if slot >= 0:
                    pos_active[slot] = 1
                    pos_dir[slot] = -1
                    pos_entry[slot] = close[i]
                    pos_sl[slot] = close[i] + atr[i] * sl_mult
                    pos_atr[slot] = atr[i]
                    if tp_mult < float32(998.0):
                        pos_tp[slot] = close[i] - atr[i] * tp_mult
                    else:
                        pos_tp[slot] = float32(0.000001)
                    pos_be_raised[slot] = 0
                    if be_trigger_atr > float32(0.0):
                        pos_be_trigger[slot] = close[i] - atr[i] * be_trigger_atr
                    else:
                        pos_be_trigger[slot] = float32(0.000001)
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1

            # Grade B long: cloud3 gated
            if long_b[i] != 0 and has_shorts == 0 and can_enter == 1 and cloud3_ok_long[i] != 0 and did_enter == 0:
                slot = int8(-1)
                for s in range(4):
                    if pos_active[s] == 0:
                        slot = int8(s)
                        break
                if slot >= 0:
                    pos_active[slot] = 1
                    pos_dir[slot] = 1
                    pos_entry[slot] = close[i]
                    pos_sl[slot] = close[i] - atr[i] * sl_mult
                    pos_atr[slot] = atr[i]
                    if tp_mult < float32(998.0):
                        pos_tp[slot] = close[i] + atr[i] * tp_mult
                    else:
                        pos_tp[slot] = float32(999999.0)
                    pos_be_raised[slot] = 0
                    if be_trigger_atr > float32(0.0):
                        pos_be_trigger[slot] = close[i] + atr[i] * be_trigger_atr
                    else:
                        pos_be_trigger[slot] = float32(999999.0)
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1

            # Grade B short: cloud3 gated
            if short_b[i] != 0 and has_longs == 0 and can_enter == 1 and cloud3_ok_short[i] != 0 and did_enter == 0:
                slot = int8(-1)
                for s in range(4):
                    if pos_active[s] == 0:
                        slot = int8(s)
                        break
                if slot >= 0:
                    pos_active[slot] = 1
                    pos_dir[slot] = -1
                    pos_entry[slot] = close[i]
                    pos_sl[slot] = close[i] + atr[i] * sl_mult
                    pos_atr[slot] = atr[i]
                    if tp_mult < float32(998.0):
                        pos_tp[slot] = close[i] - atr[i] * tp_mult
                    else:
                        pos_tp[slot] = float32(0.000001)
                    pos_be_raised[slot] = 0
                    if be_trigger_atr > float32(0.0):
                        pos_be_trigger[slot] = close[i] - atr[i] * be_trigger_atr
                    else:
                        pos_be_trigger[slot] = float32(0.000001)
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1

            # RE long: cloud3 gated (matches v390 line 328: can_long_b)
            if reentry_long[i] != 0 and has_shorts == 0 and can_enter == 1 and cloud3_ok_long[i] != 0 and did_enter == 0:
                slot = int8(-1)
                for s in range(4):
                    if pos_active[s] == 0:
                        slot = int8(s)
                        break
                if slot >= 0:
                    pos_active[slot] = 1
                    pos_dir[slot] = 1
                    pos_entry[slot] = close[i]
                    pos_sl[slot] = close[i] - atr[i] * sl_mult
                    pos_atr[slot] = atr[i]
                    if tp_mult < float32(998.0):
                        pos_tp[slot] = close[i] + atr[i] * tp_mult
                    else:
                        pos_tp[slot] = float32(999999.0)
                    pos_be_raised[slot] = 0
                    if be_trigger_atr > float32(0.0):
                        pos_be_trigger[slot] = close[i] + atr[i] * be_trigger_atr
                    else:
                        pos_be_trigger[slot] = float32(999999.0)
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1

            # RE short: cloud3 gated (matches v390 line 338: can_short_b)
            if reentry_short[i] != 0 and has_longs == 0 and can_enter == 1 and cloud3_ok_short[i] != 0 and did_enter == 0:
                slot = int8(-1)
                for s in range(4):
                    if pos_active[s] == 0:
                        slot = int8(s)
                        break
                if slot >= 0:
                    pos_active[slot] = 1
                    pos_dir[slot] = -1
                    pos_entry[slot] = close[i]
                    pos_sl[slot] = close[i] + atr[i] * sl_mult
                    pos_atr[slot] = atr[i]
                    if tp_mult < float32(998.0):
                        pos_tp[slot] = close[i] - atr[i] * tp_mult
                    else:
                        pos_tp[slot] = float32(0.000001)
                    pos_be_raised[slot] = 0
                    if be_trigger_atr > float32(0.0):
                        pos_be_trigger[slot] = close[i] - atr[i] * be_trigger_atr
                    else:
                        pos_be_trigger[slot] = float32(0.000001)
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1

            # ── Track peak equity / drawdown ──────────────────────────────
            if equity > peak_equity:
                peak_equity = equity
            dd = peak_equity - equity
            if dd > max_dd:
                max_dd = dd

        # ── Close remaining positions at last bar ─────────────────────────
        for s in range(4):
            if pos_active[s] == 1:
                last_close = close[N - 1]
                if pos_dir[s] == 1:
                    raw_pnl = (last_close - pos_entry[s]) / pos_entry[s] * notional
                else:
                    raw_pnl = (pos_entry[s] - last_close) / pos_entry[s] * notional
                net_pnl = raw_pnl - comm_per_side
                trade_count += 1
                pnl_sum += net_pnl
                if net_pnl > 0:
                    win_count += 1
                    gross_profit += net_pnl
                else:
                    gross_loss += (-net_pnl)
                wf_n += 1
                delta = net_pnl - wf_mean
                wf_mean += delta / float32(wf_n)
                wf_M2 += delta * (net_pnl - wf_mean)
                equity += net_pnl

        # ── Write results ─────────────────────────────────────────────────
        win_rate = float32(0.0)
        if trade_count > 0:
            win_rate = float32(win_count) / float32(trade_count)

        expectancy = float32(0.0)
        if trade_count > 0:
            expectancy = pnl_sum / float32(trade_count)

        max_dd_pct = float32(0.0)
        if peak_equity > float32(0.0):
            max_dd_pct = max_dd / peak_equity * float32(100.0)

        profit_factor = float32(0.0)
        if gross_loss > float32(0.0):
            profit_factor = gross_profit / gross_loss

        lsg_pct = float32(0.0)
        if total_losers > 0:
            lsg_pct = float32(lsg_count) / float32(total_losers) * float32(100.0)

        sharpe = float32(0.0)
        if wf_n > 1 and wf_M2 > float32(0.0):
            variance = wf_M2 / float32(wf_n)
            std = math.sqrt(variance)
            if std > float32(0.0):
                sharpe = wf_mean / float32(std)

        results[c, 0] = float32(trade_count)
        results[c, 1] = win_rate
        results[c, 2] = pnl_sum       # net_pnl
        results[c, 3] = expectancy
        results[c, 4] = max_dd_pct
        results[c, 5] = profit_factor
        results[c, 6] = lsg_pct
        results[c, 7] = sharpe


def run_gpu_sweep(df_signals, param_grid_np, notional_val=5000.0, comm_rate=0.0008):
    """Run GPU sweep. Returns DataFrame with results sorted by net_pnl descending.

    Args:
        df_signals: DataFrame with signal columns from compute_signals() v3.9.0.
            Required columns: close, high, low, atr,
            long_a, long_b, short_a, short_b, reentry_long, reentry_short,
            cloud3_allows_long, cloud3_allows_short
        param_grid_np: [N_combos, 4] float32 array from build_param_grid()
        notional_val: position notional (same for all combos)
        comm_rate: taker commission rate per side (default 0.0008 = 0.08%)

    Returns:
        DataFrame with columns: sl_mult, tp_mult, be_trigger_atr, cooldown,
        total_trades, win_rate, net_pnl, expectancy, max_dd_pct,
        profit_factor, lsg_pct, sharpe
    """
    if not CUDA_AVAILABLE:
        raise RuntimeError("Numba CUDA not available. Install numba with CUDA support.")

    N = len(df_signals)
    N_combos = len(param_grid_np)

    # Extract signal arrays as float32/int8 numpy arrays
    d_close = cuda.to_device(df_signals["close"].values.astype(np.float32))
    d_high  = cuda.to_device(df_signals["high"].values.astype(np.float32))
    d_low   = cuda.to_device(df_signals["low"].values.astype(np.float32))
    d_atr   = cuda.to_device(df_signals["atr"].values.astype(np.float32))

    d_long_a  = cuda.to_device(df_signals["long_a"].values.astype(np.int8))
    d_long_b  = cuda.to_device(df_signals["long_b"].values.astype(np.int8))
    d_short_a = cuda.to_device(df_signals["short_a"].values.astype(np.int8))
    d_short_b = cuda.to_device(df_signals["short_b"].values.astype(np.int8))
    d_re_long  = cuda.to_device(df_signals["reentry_long"].values.astype(np.int8))
    d_re_short = cuda.to_device(df_signals["reentry_short"].values.astype(np.int8))

    # Column names in DataFrame are cloud3_allows_long/short (not cloud3_ok_long/short)
    d_c3_long  = cuda.to_device(df_signals["cloud3_allows_long"].values.astype(np.int8))
    d_c3_short = cuda.to_device(df_signals["cloud3_allows_short"].values.astype(np.int8))

    d_param_grid = cuda.to_device(param_grid_np.astype(np.float32))
    d_results = cuda.device_array((N_combos, 8), dtype=np.float32)

    threads_per_block = 256
    blocks = math.ceil(N_combos / threads_per_block)

    backtest_kernel[blocks, threads_per_block](
        d_close, d_high, d_low, d_atr,
        d_long_a, d_long_b, d_short_a, d_short_b,
        d_re_long, d_re_short,
        d_c3_long, d_c3_short,
        d_param_grid, N, N_combos,
        np.float32(notional_val), np.float32(comm_rate),
        d_results,
    )
    cuda.synchronize()

    results_np = d_results.copy_to_host()

    result_cols = [
        "total_trades", "win_rate", "net_pnl", "expectancy",
        "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",
    ]
    df_results = pd.DataFrame(results_np, columns=result_cols)

    # Attach param values
    df_results["sl_mult"]        = param_grid_np[:, 0]
    df_results["tp_mult"]        = param_grid_np[:, 1]
    df_results["be_trigger_atr"] = param_grid_np[:, 2]
    df_results["cooldown"]       = param_grid_np[:, 3].astype(int)

    # Reorder columns: params first, then metrics
    param_cols = ["sl_mult", "tp_mult", "be_trigger_atr", "cooldown"]
    df_results = df_results[param_cols + result_cols]

    return df_results.sort_values("net_pnl", ascending=False).reset_index(drop=True)
'''


# ============================================================================
# FILE 2: engine/jit_backtest.py
# ============================================================================
JIT_BACKTEST_SRC = r'''"""
Numba @njit CPU-compiled backtest core for Four Pillars v3.9.0.

Same logic as cuda_sweep.py kernel but compiled for CPU via @njit.
Used by dashboard portfolio mode with ThreadPoolExecutor for per-coin parallelism.

Same known simplifications as CUDA kernel (no AVWAP, no scale-outs, etc.).
"""

import numpy as np

try:
    from numba import njit, int8, int32, float32
    NUMBA_AVAILABLE = True
except ImportError:
    def njit(*args, **kwargs):
        """Fallback: no-op decorator when Numba not installed."""
        if args and callable(args[0]):
            return args[0]
        def wrapper(f):
            """Identity wrapper."""
            return f
        return wrapper
    NUMBA_AVAILABLE = False


@njit(cache=True)
def backtest_loop(
    close, high, low, atr_arr,
    long_a, long_b, short_a, short_b,
    reentry_long, reentry_short,
    cloud3_ok_long, cloud3_ok_short,
    sl_mult, tp_mult, be_trigger_atr, cooldown_bars,
    notional, commission_rate,
):
    """Run single-coin backtest with compiled core.

    Args:
        close, high, low, atr_arr: float64 price arrays
        long_a..cloud3_ok_short: int8 signal arrays
        sl_mult, tp_mult: floats (tp_mult=999.0 means no TP)
        be_trigger_atr: float (0.0 = disabled)
        cooldown_bars: int
        notional, commission_rate: floats

    Returns:
        (trade_count, win_count, net_pnl, max_dd_pct, lsg_pct, equity_curve)
    """
    N = len(close)
    comm_per_side = notional * commission_rate

    # Position state arrays
    pos_active = np.zeros(4, dtype=np.int8)
    pos_dir = np.zeros(4, dtype=np.int8)
    pos_entry = np.zeros(4, dtype=np.float64)
    pos_sl = np.zeros(4, dtype=np.float64)
    pos_tp = np.zeros(4, dtype=np.float64)
    pos_be_raised = np.zeros(4, dtype=np.int8)
    pos_be_trigger = np.zeros(4, dtype=np.float64)

    equity = 10000.0
    peak_equity = 10000.0
    max_dd = 0.0
    last_entry_bar = -999
    trade_count = 0
    win_count = 0
    pnl_sum = 0.0
    lsg_count = 0
    total_losers = 0
    equity_curve = np.empty(N, dtype=np.float64)

    for i in range(N):
        if atr_arr[i] != atr_arr[i]:  # isnan
            equity_curve[i] = equity
            continue

        # ── Exits ─────────────────────────────────────────────────────────
        for s in range(4):
            if pos_active[s] == 0:
                continue

            exit_price = 0.0
            exited = 0
            saw_green = 0

            if pos_dir[s] == 1:
                if high[i] > pos_entry[s]:
                    saw_green = 1
                if low[i] <= pos_sl[s]:
                    exit_price = pos_sl[s]
                    exited = 1
                elif tp_mult < 998.0 and high[i] >= pos_tp[s]:
                    exit_price = pos_tp[s]
                    exited = 1
            else:
                if low[i] < pos_entry[s]:
                    saw_green = 1
                if high[i] >= pos_sl[s]:
                    exit_price = pos_sl[s]
                    exited = 1
                elif tp_mult < 998.0 and low[i] <= pos_tp[s]:
                    exit_price = pos_tp[s]
                    exited = 1

            if exited == 1:
                if pos_dir[s] == 1:
                    raw_pnl = (exit_price - pos_entry[s]) / pos_entry[s] * notional
                else:
                    raw_pnl = (pos_entry[s] - exit_price) / pos_entry[s] * notional
                net = raw_pnl - comm_per_side
                trade_count += 1
                pnl_sum += net
                if net > 0:
                    win_count += 1
                else:
                    total_losers += 1
                    if saw_green == 1:
                        lsg_count += 1
                equity += net
                pos_active[s] = 0

        # ── BE raise ──────────────────────────────────────────────────────
        for s in range(4):
            if pos_active[s] == 0 or pos_be_raised[s] == 1:
                continue
            if be_trigger_atr <= 0.0:
                continue
            if pos_dir[s] == 1:
                if high[i] >= pos_be_trigger[s]:
                    pos_be_raised[s] = 1
                    if pos_entry[s] > pos_sl[s]:
                        pos_sl[s] = pos_entry[s]
            else:
                if low[i] <= pos_be_trigger[s]:
                    pos_be_raised[s] = 1
                    if pos_entry[s] < pos_sl[s]:
                        pos_sl[s] = pos_entry[s]

        # ── Entries ───────────────────────────────────────────────────────
        active_count = 0
        has_longs = 0
        has_shorts = 0
        for s in range(4):
            if pos_active[s] == 1:
                active_count += 1
                if pos_dir[s] == 1:
                    has_longs = 1
                else:
                    has_shorts = 1

        cooldown_ok = 1 if (i - last_entry_bar) >= cooldown_bars else 0
        can_enter = 1 if active_count < 4 and cooldown_ok == 1 else 0
        did_enter = 0

        # A long
        if long_a[i] != 0 and has_shorts == 0 and can_enter == 1 and did_enter == 0:
            for s in range(4):
                if pos_active[s] == 0:
                    pos_active[s] = 1
                    pos_dir[s] = 1
                    pos_entry[s] = close[i]
                    pos_sl[s] = close[i] - atr_arr[i] * sl_mult
                    pos_tp[s] = close[i] + atr_arr[i] * tp_mult if tp_mult < 998.0 else 999999.0
                    pos_be_raised[s] = 0
                    pos_be_trigger[s] = close[i] + atr_arr[i] * be_trigger_atr if be_trigger_atr > 0.0 else 999999.0
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1
                    break

        # A short
        if short_a[i] != 0 and has_longs == 0 and can_enter == 1 and did_enter == 0:
            for s in range(4):
                if pos_active[s] == 0:
                    pos_active[s] = 1
                    pos_dir[s] = -1
                    pos_entry[s] = close[i]
                    pos_sl[s] = close[i] + atr_arr[i] * sl_mult
                    pos_tp[s] = close[i] - atr_arr[i] * tp_mult if tp_mult < 998.0 else 0.000001
                    pos_be_raised[s] = 0
                    pos_be_trigger[s] = close[i] - atr_arr[i] * be_trigger_atr if be_trigger_atr > 0.0 else 0.000001
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1
                    break

        # B long (cloud3 gated)
        if long_b[i] != 0 and has_shorts == 0 and can_enter == 1 and cloud3_ok_long[i] != 0 and did_enter == 0:
            for s in range(4):
                if pos_active[s] == 0:
                    pos_active[s] = 1
                    pos_dir[s] = 1
                    pos_entry[s] = close[i]
                    pos_sl[s] = close[i] - atr_arr[i] * sl_mult
                    pos_tp[s] = close[i] + atr_arr[i] * tp_mult if tp_mult < 998.0 else 999999.0
                    pos_be_raised[s] = 0
                    pos_be_trigger[s] = close[i] + atr_arr[i] * be_trigger_atr if be_trigger_atr > 0.0 else 999999.0
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1
                    break

        # B short (cloud3 gated)
        if short_b[i] != 0 and has_longs == 0 and can_enter == 1 and cloud3_ok_short[i] != 0 and did_enter == 0:
            for s in range(4):
                if pos_active[s] == 0:
                    pos_active[s] = 1
                    pos_dir[s] = -1
                    pos_entry[s] = close[i]
                    pos_sl[s] = close[i] + atr_arr[i] * sl_mult
                    pos_tp[s] = close[i] - atr_arr[i] * tp_mult if tp_mult < 998.0 else 0.000001
                    pos_be_raised[s] = 0
                    pos_be_trigger[s] = close[i] - atr_arr[i] * be_trigger_atr if be_trigger_atr > 0.0 else 0.000001
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1
                    break

        # RE long (cloud3 gated -- matches v390 line 328)
        if reentry_long[i] != 0 and has_shorts == 0 and can_enter == 1 and cloud3_ok_long[i] != 0 and did_enter == 0:
            for s in range(4):
                if pos_active[s] == 0:
                    pos_active[s] = 1
                    pos_dir[s] = 1
                    pos_entry[s] = close[i]
                    pos_sl[s] = close[i] - atr_arr[i] * sl_mult
                    pos_tp[s] = close[i] + atr_arr[i] * tp_mult if tp_mult < 998.0 else 999999.0
                    pos_be_raised[s] = 0
                    pos_be_trigger[s] = close[i] + atr_arr[i] * be_trigger_atr if be_trigger_atr > 0.0 else 999999.0
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1
                    break

        # RE short (cloud3 gated -- matches v390 line 338)
        if reentry_short[i] != 0 and has_longs == 0 and can_enter == 1 and cloud3_ok_short[i] != 0 and did_enter == 0:
            for s in range(4):
                if pos_active[s] == 0:
                    pos_active[s] = 1
                    pos_dir[s] = -1
                    pos_entry[s] = close[i]
                    pos_sl[s] = close[i] + atr_arr[i] * sl_mult
                    pos_tp[s] = close[i] - atr_arr[i] * tp_mult if tp_mult < 998.0 else 0.000001
                    pos_be_raised[s] = 0
                    pos_be_trigger[s] = close[i] - atr_arr[i] * be_trigger_atr if be_trigger_atr > 0.0 else 0.000001
                    equity -= comm_per_side
                    last_entry_bar = i
                    did_enter = 1
                    break

        # Track peak/drawdown
        if equity > peak_equity:
            peak_equity = equity
        dd = peak_equity - equity
        if dd > max_dd:
            max_dd = dd

        equity_curve[i] = equity

    # Close remaining
    for s in range(4):
        if pos_active[s] == 1:
            last_close = close[N - 1]
            if pos_dir[s] == 1:
                raw_pnl = (last_close - pos_entry[s]) / pos_entry[s] * notional
            else:
                raw_pnl = (pos_entry[s] - last_close) / pos_entry[s] * notional
            net = raw_pnl - comm_per_side
            trade_count += 1
            pnl_sum += net
            if net > 0:
                win_count += 1
            else:
                total_losers += 1
            equity += net

    equity_curve[N - 1] = equity
    max_dd_pct = max_dd / peak_equity * 100.0 if peak_equity > 0.0 else 0.0
    lsg_pct = lsg_count / total_losers * 100.0 if total_losers > 0 else 0.0

    return trade_count, win_count, pnl_sum, max_dd_pct, lsg_pct, equity_curve


def ensure_warmup():
    """JIT-compile with dummy data so first real call is instant."""
    if not NUMBA_AVAILABLE:
        return
    dummy = np.zeros(10, dtype=np.float64)
    dummy_i = np.zeros(10, dtype=np.int8)
    backtest_loop(
        dummy, dummy, dummy, dummy + 1.0,
        dummy_i, dummy_i, dummy_i, dummy_i,
        dummy_i, dummy_i, dummy_i, dummy_i,
        2.0, 999.0, 0.0, 3,
        5000.0, 0.0008,
    )


# Warmup on import
ensure_warmup()
'''


# ============================================================================
# FILE 3: dashboard_v394.py (copy v392 + patches)
# ============================================================================

def build_dashboard():
    """Copy dashboard_v392.py to dashboard_v394.py, then apply patches."""
    src = SCRIPTS / "dashboard_v392.py"
    dst = TARGETS["dashboard"]

    if not src.exists():
        print("ERROR: " + str(src) + " not found.")
        sys.exit(1)

    with open(src, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines)

    # ── Patch 1: Update docstring version ─────────────────────────────────
    content = content.replace(
        "Four Pillars v3.9.2 Backtest Dashboard -- Numba JIT + timing panel.",
        "Four Pillars v3.9.4 Backtest Dashboard -- CUDA GPU sweep + JIT portfolio.",
    )

    # ── Patch 2: Add GPU Sweep session state init ─────────────────────────
    # Insert after: st.session_state["timing_records"] = []
    old_init = 'if "timing_records" not in st.session_state:\n    st.session_state["timing_records"] = []\n'
    new_init = old_init + (
        'if "gpu_sweep_results" not in st.session_state:\n'
        '    st.session_state["gpu_sweep_results"] = None\n'
        'if "gpu_sweep_symbol" not in st.session_state:\n'
        '    st.session_state["gpu_sweep_symbol"] = None\n'
    )
    content = content.replace(old_init, new_init, 1)

    # ── Patch 3: Add GPU Sweep sidebar button ─────────────────────────────
    # Insert after: run_portfolio = st.sidebar.button("Portfolio Analysis")
    old_buttons = 'run_portfolio = st.sidebar.button("Portfolio Analysis")\n'
    new_buttons = old_buttons + 'run_gpu_sweep = st.sidebar.button("GPU Sweep (CUDA)")\n'
    content = content.replace(old_buttons, new_buttons, 1)

    # Add mode transition for GPU Sweep button
    old_mode_port = (
        'if run_portfolio:\n'
        '    st.session_state["mode"] = "portfolio"\n'
        '    st.session_state["portfolio_data"] = None\n'
    )
    new_mode_port = old_mode_port + (
        'if run_gpu_sweep:\n'
        '    st.session_state["mode"] = "gpu_sweep"\n'
        '    st.session_state["gpu_sweep_results"] = None\n'
    )
    content = content.replace(old_mode_port, new_mode_port, 1)

    # ── Patch 4: Add GPU sidebar status panel ─────────────────────────────
    # Insert after: perf_debug = st.sidebar.checkbox("Performance Debug", value=False)
    old_perf = 'perf_debug = st.sidebar.checkbox("Performance Debug", value=False)\n'
    new_perf = old_perf + GPU_SIDEBAR_PANEL
    content = content.replace(old_perf, new_perf, 1)

    # ── Patch 5: Append GPU Sweep mode block at end of file ───────────────
    content = content.rstrip() + "\n\n" + GPU_SWEEP_MODE + "\n"

    # ── Patch 6: Equity curve cache fix (add params_hash to single_data) ──
    # Add params_hash to single_data cache dict
    old_single_cache = (
        '            "symbol": symbol, "df": df, "timeframe": timeframe, "elapsed": time.time() - t0,\n'
        '        }\n'
    )
    new_single_cache = (
        '            "symbol": symbol, "df": df, "timeframe": timeframe, "elapsed": time.time() - t0,\n'
        '            "params_hash": compute_params_hash(signal_params, bt_params, timeframe, date_range),\n'
        '        }\n'
    )
    content = content.replace(old_single_cache, new_single_cache, 1)

    # Add hash validation before loading from cache
    old_cache_check = '    if st.session_state["single_data"] is None:\n'
    new_cache_check = (
        '    _single_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)\n'
        '    if st.session_state["single_data"] is not None and st.session_state["single_data"].get("params_hash") != _single_hash:\n'
        '        st.session_state["single_data"] = None  # params changed, invalidate cache\n'
        '    if st.session_state["single_data"] is None:\n'
    )
    content = content.replace(old_cache_check, new_cache_check, 1)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


GPU_SIDEBAR_PANEL = r'''
# ── GPU Status Panel ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def _get_gpu_info():
    """Fetch GPU info, cached 60s."""
    try:
        from engine.cuda_sweep import get_cuda_info
        return get_cuda_info()
    except Exception:
        return None

_gpu_info = _get_gpu_info()
if _gpu_info:
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "GPU: " + str(_gpu_info["device"]) + "\n"
        + "VRAM: " + str(_gpu_info["vram_free_gb"]) + "GB free / " + str(_gpu_info["vram_total_gb"]) + "GB\n"
        + "CUDA " + str(_gpu_info["cuda_version"]) + " | Numba " + str(_gpu_info["numba_version"])
    )
'''


GPU_SWEEP_MODE = r'''
# ============================================================================
# GPU SWEEP MODE (v3.9.4) -- CUDA parallel parameter optimization
# ============================================================================
elif mode == "gpu_sweep":
    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.session_state["gpu_sweep_results"] = None
        st.rerun()

    # CUDA availability check
    try:
        from engine.cuda_sweep import run_gpu_sweep, build_param_grid, get_cuda_info
        # GPU sweep uses v3.9.0 signal pipeline (separate from dashboard's v3.8.3)
        from signals.four_pillars_v390 import compute_signals as compute_signals_v390
        _cuda_ok = True
    except ImportError as _imp_err:
        _cuda_ok = False
        _cuda_msg = str(_imp_err)

    if not _cuda_ok:
        st.error("CUDA engine not available: " + _cuda_msg)
        st.info("Run: python scripts/build_cuda_engine.py")
        st.stop()

    _gpu = get_cuda_info()
    if _gpu:
        st.caption("GPU: " + str(_gpu["device"]) + " | VRAM free: " + str(_gpu["vram_free_gb"]) + " GB")
    st.title("GPU Sweep -- " + timeframe)

    # Symbol selection
    _gpu_symbols = get_cached_symbols()
    _gpu_sym = st.selectbox("Symbol", _gpu_symbols, key="gpu_sweep_sym")

    # Date range (reuse sidebar date_range)
    if date_range:
        st.caption("Date filter: " + str(date_range[0]) + " to " + str(date_range[1]))

    st.markdown("---")
    st.subheader("Parameter Ranges")

    _gc1, _gc2 = st.columns(2)
    with _gc1:
        _sl_min = st.number_input("SL min", value=0.5, step=0.25, key="gpu_sl_min")
        _sl_max = st.number_input("SL max", value=3.0, step=0.25, key="gpu_sl_max")
        _sl_step = st.number_input("SL step", value=0.25, step=0.05, key="gpu_sl_step")
    with _gc2:
        _tp_min = st.number_input("TP min", value=0.5, step=0.25, key="gpu_tp_min")
        _tp_max = st.number_input("TP max", value=4.0, step=0.25, key="gpu_tp_max")
        _tp_step = st.number_input("TP step", value=0.25, step=0.05, key="gpu_tp_step")

    _include_no_tp = st.checkbox('Include "No TP" (999.0)', value=True, key="gpu_no_tp")
    _cooldowns = st.multiselect("Cooldown values", [0, 3, 5, 10], default=[0, 3, 5, 10], key="gpu_cd")
    _be_vals = st.multiselect("BE trigger ATR values", [0.0, 0.5, 1.0], default=[0.0, 0.5, 1.0], key="gpu_be")
    _gpu_notional = st.number_input("Notional ($)", value=float(notional), key="gpu_notional")

    # Build param grid and show combo count
    import numpy as _np
    _sl_range = _np.arange(_sl_min, _sl_max + _sl_step * 0.5, _sl_step)
    _tp_range = _np.arange(_tp_min, _tp_max + _tp_step * 0.5, _tp_step)
    _pg = build_param_grid(
        sl_range=_sl_range, tp_range=_tp_range,
        cooldown_vals=_cooldowns, be_vals=_be_vals,
        include_no_tp=_include_no_tp,
    )
    _n_combos = len(_pg)
    _est_vram_mb = _n_combos * 0.0001
    st.info("Combos: " + str(_n_combos) + " | Est. VRAM: ~" + str(round(_est_vram_mb, 1)) + " MB")

    # Run button
    if st.button("Run GPU Sweep", key="gpu_run"):
        with st.spinner("Loading data and computing v3.9.0 signals..."):
            _df_gpu = load_data(_gpu_sym, timeframe)
            if _df_gpu is None:
                st.error("No data for " + _gpu_sym)
                st.stop()
            _df_gpu = apply_date_filter(_df_gpu, date_range)
            if len(_df_gpu) < 200:
                st.error("Too few bars after date filter: " + str(len(_df_gpu)))
                st.stop()
            # Compute v3.9.0 signals (NOT v3.8.3)
            _df_sig_gpu = compute_signals_v390(_df_gpu.copy(), signal_params)

        with st.spinner("Running " + str(_n_combos) + " combos on GPU..."):
            _t_gpu_start = time.time()
            _gpu_results = run_gpu_sweep(_df_sig_gpu, _pg, _gpu_notional, 0.0008)
            _t_gpu_elapsed = time.time() - _t_gpu_start

        st.session_state["gpu_sweep_results"] = _gpu_results
        st.session_state["gpu_sweep_symbol"] = _gpu_sym
        st.success(
            "GPU sweep complete: " + str(_n_combos) + " combos in "
            + str(round(_t_gpu_elapsed, 2)) + "s ("
            + str(len(_df_sig_gpu)) + " bars)"
        )

    # Display results
    _gpu_res = st.session_state.get("gpu_sweep_results")
    if _gpu_res is not None:
        st.markdown("---")

        # Heatmap: SL vs TP colored by net_pnl
        st.subheader("Heatmap: SL vs TP (net P&L)")
        # Aggregate across cooldown/BE by taking best net_pnl for each SL/TP pair
        _hm_df = _gpu_res.groupby(["sl_mult", "tp_mult"])["net_pnl"].max().reset_index()
        _hm_pivot = _hm_df.pivot(index="sl_mult", columns="tp_mult", values="net_pnl")

        # Replace 999.0 column label with "No TP"
        _new_cols = []
        for _col in _hm_pivot.columns:
            if _col >= 998.0:
                _new_cols.append("No TP")
            else:
                _new_cols.append(str(round(_col, 2)))
        _hm_pivot.columns = _new_cols
        _hm_pivot.index = [str(round(x, 2)) for x in _hm_pivot.index]

        _hm_fig = go.Figure(data=go.Heatmap(
            z=_hm_pivot.values,
            x=_hm_pivot.columns.tolist(),
            y=_hm_pivot.index.tolist(),
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="Net P&L ($)"),
        ))
        _hm_fig.update_layout(
            xaxis_title="TP Mult",
            yaxis_title="SL Mult",
            height=500,
        )
        # Annotate best cell
        _best_idx = _gpu_res["net_pnl"].idxmax()
        _best = _gpu_res.iloc[_best_idx]
        _best_tp_label = "No TP" if _best["tp_mult"] >= 998.0 else str(round(_best["tp_mult"], 2))
        _hm_fig.add_annotation(
            x=_best_tp_label,
            y=str(round(_best["sl_mult"], 2)),
            text="BEST",
            showarrow=True,
            arrowhead=2,
            font=dict(color="white", size=12),
        )
        st.plotly_chart(_hm_fig, use_container_width=True)

        # Top-20 table sorted by expectancy
        st.subheader("Top 20 Combos (by expectancy)")
        _top20 = _gpu_res.sort_values("expectancy", ascending=False).head(20).copy()
        _top20["tp_mult"] = _top20["tp_mult"].apply(lambda x: "No TP" if x >= 998.0 else str(round(x, 2)))
        _display_cols = [
            "sl_mult", "tp_mult", "be_trigger_atr", "cooldown",
            "total_trades", "win_rate", "net_pnl", "expectancy",
            "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",
        ]
        st.dataframe(_top20[_display_cols], use_container_width=True)

        # Export CSV
        _csv_data = _gpu_res.to_csv(index=False)
        st.download_button(
            "Export Full Results CSV",
            data=_csv_data,
            file_name="gpu_sweep_" + str(st.session_state.get("gpu_sweep_symbol", "")) + ".csv",
            mime="text/csv",
        )
'''


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    print("CUDA Engine Build Script")
    print("=" * 60)

    check_targets()

    # File 1: engine/cuda_sweep.py
    print("\nWriting engine/cuda_sweep.py ...")
    with open(TARGETS["cuda_sweep"], "w", encoding="utf-8") as f:
        f.write(CUDA_SWEEP_SRC)
    validate(TARGETS["cuda_sweep"])

    # File 2: engine/jit_backtest.py
    print("Writing engine/jit_backtest.py ...")
    with open(TARGETS["jit_backtest"], "w", encoding="utf-8") as f:
        f.write(JIT_BACKTEST_SRC)
    validate(TARGETS["jit_backtest"])

    # File 3: scripts/dashboard_v394.py (copy + patch)
    print("Writing scripts/dashboard_v394.py (copy v392 + patches) ...")
    build_dashboard()
    validate(TARGETS["dashboard"])

    print("\n" + "=" * 60)
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("All 3 files compiled clean.")
        print("\nRun command:")
        print('  streamlit run "' + str(TARGETS["dashboard"]) + '"')
