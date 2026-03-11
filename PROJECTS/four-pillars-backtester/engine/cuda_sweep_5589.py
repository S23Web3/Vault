"""
CUDA GPU sweep engine for 55/89 EMA cross scalp (Backtester5589).

Grid: sl_mult x avwap_sigma (2D sweep, fixed avwap_warmup/tp_atr_offset/ratchet_threshold).

SL lifecycle per trade (matches engine/backtester_55_89.py exactly):
  Phase 1 (bars 1 to avwap_warmup-1): SL = entry +/- sl_mult * entry_atr
  Phase 2 (bars_in_trade >= avwap_warmup): SL moves to frozen AVWAP band
    AVWAP = volume-weighted HLC3 from entry bar. Sigma floored at sigma_floor_atr * atr.
    LONG: SL = max(existing_sl, avwap_center - avwap_sigma * avwap_std)
    SHORT: SL = min(existing_sl, avwap_center + avwap_sigma * avwap_std)
  Phase 3 (overzone exit): SL ratchets to live AVWAP band; ratchet_count++
    Long overzone in: stoch_9_d < 20. Exit (ratchet fires): stoch_9_d >= 20.
    Short overzone in: stoch_9_d > 80. Exit (ratchet fires): stoch_9_d <= 80.
  Phase 4 (ratchet_count >= ratchet_threshold): TP activates and tracks each bar
    TP_long  = max(ema_72, ema_89) + tp_atr_offset * ATR
    TP_short = min(ema_72, ema_89) - tp_atr_offset * ATR

Commission: taker on both entry and exit (matches Backtester5589 default).
One position at a time (5589 strategy is always flat between entries).

Port source: engine/backtester_55_89.py
"""
import math

import numpy as np
import pandas as pd

try:
    import numba
    from numba import cuda, int32, float32
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False

SIGMA_FLOOR_ATR_DEFAULT = 0.5   # sigma floor fraction of ATR (matches AVWAPTracker default)


def get_cuda_info():
    """Return dict with GPU device info, or None if CUDA unavailable."""
    if not CUDA_AVAILABLE:
        return None
    try:
        device = cuda.get_current_device()
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


def build_param_grid_5589(
    sl_range=None,
    sigma_range=None,
    warmup_val=5,
    tp_offset_val=0.5,
    ratchet_val=2,
):
    """Build [N_combos, 5] float32 param grid for the 5589 GPU sweep.

    Grid axes: sl_mult x avwap_sigma. warmup, tp_offset, ratchet are fixed per call.
    Returns array shape [N_combos, 5]: [sl_mult, avwap_sigma, avwap_warmup, tp_atr_offset, ratchet_threshold].
    """
    if sl_range is None:
        sl_range = np.arange(0.5, 4.25, 0.5)
    if sigma_range is None:
        sigma_range = np.arange(1.0, 3.25, 0.5)
    combos = []
    for sl in sl_range:
        for sig in sigma_range:
            combos.append([float(sl), float(sig), float(warmup_val), float(tp_offset_val), float(ratchet_val)])
    return np.array(combos, dtype=np.float32)


if CUDA_AVAILABLE:
    @cuda.jit
    def backtest_kernel_5589(
        close, high, low, atr, volume,
        stoch_9_d, ema_72, ema_89,
        long_a, short_a,
        param_grid, N, N_combos,
        notional, commission_rate, sigma_floor_atr,
        results,
    ):
        """One thread per param combo. 4-phase 5589 SL lifecycle; single position at a time.

        Matches backtester_55_89.py _update_position logic.
        """
        c = cuda.grid(1)
        if c >= N_combos:
            return

        sl_mult = param_grid[c, 0]
        avwap_sigma = param_grid[c, 1]
        avwap_warmup = int32(param_grid[c, 2])
        tp_atr_offset = param_grid[c, 3]
        ratchet_threshold = int32(param_grid[c, 4])

        # Commission: taker on both sides (matches Backtester5589)
        entry_comm = notional * commission_rate
        exit_comm = notional * commission_rate

        # Running equity and stats
        equity = float32(10000.0)
        peak_equity = float32(10000.0)
        max_dd = float32(0.0)
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

        # Single position state
        pos_active = int32(0)           # 0 = flat, 1 = in trade
        pos_dir = int32(0)              # 1 = LONG, -1 = SHORT
        pos_entry = float32(0.0)
        pos_sl = float32(0.0)
        pos_tp = float32(999999.0)
        pos_phase = int32(1)            # 1, 2, 3, 4
        pos_bars = int32(0)             # bars in trade; entry bar = 1
        pos_cum_pv = float32(0.0)       # sum(hlc3 * volume) for AVWAP
        pos_cum_v = float32(0.0)        # sum(volume) for AVWAP
        pos_cum_pv2 = float32(0.0)      # sum(hlc3^2 * volume) for AVWAP variance
        pos_ratchet = int32(0)          # overzone exit count
        pos_in_overzone = int32(0)      # currently in overzone: 0/1
        pos_saw_green = int32(0)        # position moved favorably at any bar: 0/1

        for i in range(N):
            if atr[i] != atr[i]:           # isnan
                continue

            vol_i = volume[i]
            if vol_i <= float32(0.0):
                vol_i = float32(1e-10)

            hlc3 = (high[i] + low[i] + close[i]) / float32(3.0)

            # ── Manage open position ─────────────────────────────────────────
            if pos_active == 1:

                # 1. Accumulate AVWAP (every bar while active, before phase checks)
                pos_cum_pv += hlc3 * vol_i
                pos_cum_v += vol_i
                pos_cum_pv2 += hlc3 * hlc3 * vol_i
                pos_bars += 1

                # Compute AVWAP center and sigma
                avwap_center = pos_cum_pv / pos_cum_v
                avwap_var = pos_cum_pv2 / pos_cum_v - avwap_center * avwap_center
                if avwap_var < float32(0.0):
                    avwap_var = float32(0.0)
                avwap_std = math.sqrt(avwap_var)
                sigma_floor = sigma_floor_atr * atr[i]
                if avwap_std < sigma_floor:
                    avwap_std = sigma_floor

                # 2. Phase 2 transition: freeze AVWAP when bars_in_trade >= avwap_warmup
                if pos_phase == 1 and pos_bars >= avwap_warmup:
                    if pos_dir == 1:    # LONG: SL moves to AVWAP lower band
                        new_sl = avwap_center - avwap_sigma * avwap_std
                        if new_sl > pos_sl:
                            pos_sl = new_sl
                    else:               # SHORT: SL moves to AVWAP upper band
                        new_sl = avwap_center + avwap_sigma * avwap_std
                        if new_sl < pos_sl:
                            pos_sl = new_sl
                    pos_phase = int32(2)

                # 3. Overzone ratchet detection (Phase 2+)
                d = stoch_9_d[i]
                if pos_phase >= 2:
                    if pos_dir == 1:
                        currently_in_overzone = int32(1) if d < float32(20.0) else int32(0)
                    else:
                        currently_in_overzone = int32(1) if d > float32(80.0) else int32(0)

                    if pos_in_overzone == 1 and currently_in_overzone == 0:
                        # Overzone exit: ratchet SL to live AVWAP band
                        if pos_dir == 1:
                            sl_candidate = avwap_center - avwap_sigma * avwap_std
                            if sl_candidate > pos_sl:
                                pos_sl = sl_candidate
                        else:
                            sl_candidate = avwap_center + avwap_sigma * avwap_std
                            if sl_candidate < pos_sl:
                                pos_sl = sl_candidate
                        pos_ratchet += 1
                        pos_phase = int32(3)

                    pos_in_overzone = currently_in_overzone

                # 4. Phase 4 TP activation: track Cloud4 edge every bar
                if pos_ratchet >= ratchet_threshold:
                    pos_phase = int32(4)
                    e72 = ema_72[i]
                    e89 = ema_89[i]
                    if e72 == e72 and e89 == e89:   # neither is NaN
                        if pos_dir == 1:
                            cloud4_edge = e72 if e72 > e89 else e89
                            pos_tp = cloud4_edge + tp_atr_offset * atr[i]
                        else:
                            cloud4_edge = e72 if e72 < e89 else e89
                            pos_tp = cloud4_edge - tp_atr_offset * atr[i]

                # 5. Mark saw_green using high/low
                if pos_dir == 1 and high[i] >= pos_entry:
                    pos_saw_green = int32(1)
                elif pos_dir == -1 and low[i] <= pos_entry:
                    pos_saw_green = int32(1)

                # 6. Exit checks (SL first = pessimistic)
                exited = int32(0)
                exit_price = float32(0.0)
                if pos_dir == 1:    # LONG
                    if low[i] <= pos_sl:
                        exit_price = pos_sl
                        exited = int32(1)
                    elif pos_phase == 4 and high[i] >= pos_tp:
                        exit_price = pos_tp
                        exited = int32(1)
                else:               # SHORT
                    if high[i] >= pos_sl:
                        exit_price = pos_sl
                        exited = int32(1)
                    elif pos_phase == 4 and low[i] <= pos_tp:
                        exit_price = pos_tp
                        exited = int32(1)

                if exited == 1:
                    if pos_dir == 1:
                        raw_pnl = (exit_price - pos_entry) / pos_entry * notional
                    else:
                        raw_pnl = (pos_entry - exit_price) / pos_entry * notional
                    # Both entry and exit are taker (matches Backtester5589)
                    net_pnl_trade = raw_pnl - exit_comm - entry_comm
                    equity += raw_pnl - exit_comm   # entry_comm already deducted at entry

                    trade_count += 1
                    pnl_sum += net_pnl_trade
                    if net_pnl_trade > float32(0.0):
                        win_count += 1
                        gross_profit += net_pnl_trade
                    else:
                        gross_loss += (-net_pnl_trade)
                        total_losers += 1
                        if pos_saw_green == 1:
                            lsg_count += 1

                    # Welford update for Sharpe
                    wf_n += 1
                    delta = net_pnl_trade - wf_mean
                    wf_mean += delta / float32(wf_n)
                    wf_M2 += delta * (net_pnl_trade - wf_mean)

                    pos_active = int32(0)

            # ── Entry (only when flat) ────────────────────────────────────────
            if pos_active == 0:
                direction = int32(0)
                if long_a[i] != 0:
                    direction = int32(1)
                elif short_a[i] != 0:
                    direction = int32(-1)

                if direction != 0:
                    equity -= entry_comm
                    pos_active = int32(1)
                    pos_dir = direction
                    pos_entry = close[i]
                    pos_phase = int32(1)
                    pos_bars = int32(1)     # entry bar counts as bar 1
                    if direction == 1:
                        pos_sl = close[i] - sl_mult * atr[i]
                        pos_tp = float32(999999.0)   # sentinel: no TP until Phase 4
                    else:
                        pos_sl = close[i] + sl_mult * atr[i]
                        pos_tp = float32(-999999.0)  # sentinel: no TP until Phase 4
                    pos_ratchet = int32(0)
                    pos_in_overzone = int32(0)
                    pos_saw_green = int32(0)
                    # Initialise AVWAP with entry bar data
                    pos_cum_pv = hlc3 * vol_i
                    pos_cum_v = vol_i
                    pos_cum_pv2 = hlc3 * hlc3 * vol_i

            # ── Peak equity / drawdown ────────────────────────────────────────
            if equity > peak_equity:
                peak_equity = equity
            dd = peak_equity - equity
            if dd > max_dd:
                max_dd = dd

        # ── Close any remaining position at end of data ───────────────────────
        if pos_active == 1:
            last_close = close[N - 1]
            if pos_dir == 1:
                raw_pnl = (last_close - pos_entry) / pos_entry * notional
            else:
                raw_pnl = (pos_entry - last_close) / pos_entry * notional
            net_pnl_trade = raw_pnl - exit_comm - entry_comm
            equity += raw_pnl - exit_comm
            trade_count += 1
            pnl_sum += net_pnl_trade
            if net_pnl_trade > float32(0.0):
                win_count += 1
                gross_profit += net_pnl_trade
            else:
                gross_loss += (-net_pnl_trade)
            wf_n += 1
            delta = net_pnl_trade - wf_mean
            wf_mean += delta / float32(wf_n)
            wf_M2 += delta * (net_pnl_trade - wf_mean)

        # ── Write results ─────────────────────────────────────────────────────
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
        results[c, 2] = pnl_sum
        results[c, 3] = expectancy
        results[c, 4] = max_dd_pct
        results[c, 5] = profit_factor
        results[c, 6] = lsg_pct
        results[c, 7] = sharpe


def run_gpu_sweep_5589(
    df_sig,
    param_grid_np,
    notional_val=5000.0,
    comm_rate=0.0008,
    sigma_floor=SIGMA_FLOOR_ATR_DEFAULT,
):
    """Run 5589 GPU sweep. Returns DataFrame sorted by net_pnl descending.

    Required columns in df_sig: close, high, low, atr, volume (optional),
    stoch_9_d, ema_72, ema_89, long_a, short_a.
    ema_72 must be pre-computed by caller (not in compute_signals_55_89 output).

    param_grid_np: [N_combos, 5] float32 array from build_param_grid_5589().
    """
    if not CUDA_AVAILABLE:
        raise RuntimeError("Numba CUDA not available. Install numba with CUDA support.")

    N = len(df_sig)
    N_combos = len(param_grid_np)

    d_close = cuda.to_device(df_sig["close"].values.astype(np.float32))
    d_high = cuda.to_device(df_sig["high"].values.astype(np.float32))
    d_low = cuda.to_device(df_sig["low"].values.astype(np.float32))
    d_atr = cuda.to_device(df_sig["atr"].values.astype(np.float32))

    if "volume" in df_sig.columns:
        vol_arr = df_sig["volume"].values.astype(np.float32)
    else:
        vol_arr = np.ones(N, dtype=np.float32)
    d_volume = cuda.to_device(vol_arr)

    d_stoch_9_d = cuda.to_device(df_sig["stoch_9_d"].values.astype(np.float32))
    d_ema_72 = cuda.to_device(df_sig["ema_72"].values.astype(np.float32))
    d_ema_89 = cuda.to_device(df_sig["ema_89"].values.astype(np.float32))
    d_long_a = cuda.to_device(df_sig["long_a"].values.astype(np.int8))
    d_short_a = cuda.to_device(df_sig["short_a"].values.astype(np.int8))

    d_param_grid = cuda.to_device(param_grid_np.astype(np.float32))
    d_results = cuda.device_array((N_combos, 8), dtype=np.float32)

    threads_per_block = 256
    blocks = math.ceil(N_combos / threads_per_block)

    backtest_kernel_5589[blocks, threads_per_block](
        d_close, d_high, d_low, d_atr, d_volume,
        d_stoch_9_d, d_ema_72, d_ema_89,
        d_long_a, d_short_a,
        d_param_grid, N, N_combos,
        np.float32(notional_val), np.float32(comm_rate), np.float32(sigma_floor),
        d_results,
    )
    cuda.synchronize()

    results_np = d_results.copy_to_host()

    result_cols = [
        "total_trades", "win_rate", "net_pnl", "expectancy",
        "max_dd_pct", "profit_factor", "lsg_pct", "sharpe",
    ]
    df_results = pd.DataFrame(results_np, columns=result_cols)

    df_results["sl_mult"] = param_grid_np[:, 0]
    df_results["avwap_sigma"] = param_grid_np[:, 1]
    df_results["avwap_warmup"] = param_grid_np[:, 2].astype(int)
    df_results["tp_atr_offset"] = param_grid_np[:, 3]
    df_results["ratchet_threshold"] = param_grid_np[:, 4].astype(int)

    param_cols = ["sl_mult", "avwap_sigma", "avwap_warmup", "tp_atr_offset", "ratchet_threshold"]
    df_results = df_results[param_cols + result_cols]

    return df_results.sort_values("net_pnl", ascending=False).reset_index(drop=True)
