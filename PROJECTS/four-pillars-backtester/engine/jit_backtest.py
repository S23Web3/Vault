"""
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
