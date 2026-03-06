"""
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
        try:
            cuda_ver = ".".join(str(x) for x in cuda.runtime.get_version())
        except Exception:
            cuda_ver = "driver-only"
        return {
            "device": device.name.decode() if isinstance(device.name, bytes) else str(device.name),
            "vram_total_gb": round(total / (1024 ** 3), 1),
            "vram_free_gb": round(free / (1024 ** 3), 1),
            "cuda_version": cuda_ver,
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
        notional, commission_rate, maker_rate,
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

        entry_comm = notional * commission_rate
        exit_comm = notional * maker_rate

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
                    if high[i] >= pos_entry[s]:
                        saw_green = 1
                    if low[i] <= pos_sl[s]:
                        exit_price = pos_sl[s]
                        exited = 1
                    elif tp_mult < float32(998.0) and high[i] >= pos_tp[s]:
                        exit_price = pos_tp[s]
                        exited = 1
                else:  # SHORT
                    if low[i] <= pos_entry[s]:
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
                    net_pnl = raw_pnl - exit_comm  # exit commission (maker)
                    pnl_sum_pnl = net_pnl - entry_comm  # full round-trip for pnl_sum

                    trade_count += 1
                    pnl_sum += pnl_sum_pnl
                    if pnl_sum_pnl > 0:
                        win_count += 1
                        gross_profit += pnl_sum_pnl
                    else:
                        gross_loss += (-pnl_sum_pnl)
                        total_losers += 1
                        if saw_green == 1:
                            lsg_count += 1

                    # Welford update
                    wf_n += 1
                    delta = pnl_sum_pnl - wf_mean
                    wf_mean += delta / float32(wf_n)
                    wf_M2 += delta * (pnl_sum_pnl - wf_mean)

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
                    equity -= entry_comm  # entry commission (taker)
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
                    equity -= entry_comm  # entry commission (taker)
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
                    equity -= entry_comm  # entry commission (taker)
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
                    equity -= entry_comm  # entry commission (taker)
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
                    equity -= entry_comm  # entry commission (taker)
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
                    equity -= entry_comm  # entry commission (taker)
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
                net_pnl = raw_pnl - exit_comm  # exit commission (maker)
                pnl_sum_pnl = net_pnl - entry_comm  # full round-trip for pnl_sum
                trade_count += 1
                pnl_sum += pnl_sum_pnl
                if pnl_sum_pnl > 0:
                    win_count += 1
                    gross_profit += pnl_sum_pnl
                else:
                    gross_loss += (-pnl_sum_pnl)
                wf_n += 1
                delta = pnl_sum_pnl - wf_mean
                wf_mean += delta / float32(wf_n)
                wf_M2 += delta * (pnl_sum_pnl - wf_mean)
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


def run_gpu_sweep(df_signals, param_grid_np, notional_val=5000.0, comm_rate=0.0008, maker_rate=0.0002):
    """Run GPU sweep. Returns DataFrame with results sorted by net_pnl descending.

    Args:
        df_signals: DataFrame with signal columns from compute_signals() v3.9.0.
            Required columns: close, high, low, atr,
            long_a, long_b, short_a, short_b, reentry_long, reentry_short,
            cloud3_allows_long, cloud3_allows_short
        param_grid_np: [N_combos, 4] float32 array from build_param_grid()
        notional_val: position notional (same for all combos)
        comm_rate: taker commission rate per side entry (default 0.0008 = 0.08%)
        maker_rate: maker commission rate per side exit (default 0.0002 = 0.02%)

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
        np.float32(notional_val), np.float32(comm_rate), np.float32(maker_rate),
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


def run_gpu_sweep_multi(
    coin_data_list,
    param_grid_np,
    notional_val=5000.0,
    comm_rate=0.0008,
    maker_rate=0.0002,
    progress_callback=None,
):
    """Run GPU sweep across multiple coins. Returns dict keyed by symbol.

    Args:
        coin_data_list: list of (symbol, df_signals) tuples.
            Each df_signals must have the 12 required columns.
        param_grid_np: [N_combos, 4] float32 array from build_param_grid()
        notional_val: position notional per trade
        comm_rate: taker commission rate per side entry
        maker_rate: maker commission rate per side exit
        progress_callback: optional callable(current_idx, total, symbol)

    Returns:
        dict: {symbol: DataFrame} where each DataFrame has the same columns
              as run_gpu_sweep() output (params + 8 metrics).
    """
    results = {}
    total = len(coin_data_list)
    for idx, (symbol, df_signals) in enumerate(coin_data_list):
        if progress_callback is not None:
            should_stop = progress_callback(idx, total, symbol)
            if should_stop:
                break
        try:
            df_result = run_gpu_sweep(df_signals, param_grid_np, notional_val, comm_rate, maker_rate)
            results[symbol] = df_result
        except Exception:
            pass
    if progress_callback is not None:
        progress_callback(total, total, "done")
    return results
