"""
55/89 EMA Cross Scalp — Signal pipeline.

Signal: stoch 9 K/D cross gates the pipeline. When alignment is active
(stoch 14 MOVING/EXTENDED, stoch 40/60 TURNING+, no contradiction,
delta compressing, TDI confirming, BBW not QUIET) AND 55/89 EMA delta
crosses zero, a trade signal fires.

Maps output to Backtester384-compatible columns (long_a, short_a, etc.).

Source of truth: PROJECTS/four-pillars-backtester/research/55-89-scalp-methodology.md
"""

import numpy as np
import pandas as pd
from numba import njit

from .stochastics_v2 import compute_all_stochastics
from .clouds_v2 import ema


# ---- ATR (Wilder RMA) ----

@njit(cache=True)
def _rma_kernel(tr, atr_len):
    """Wilder RMA loop for ATR; Numba JIT-compiled."""
    atr = np.full(len(tr), np.nan)
    if len(tr) < atr_len:
        return atr
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    return atr


def compute_atr(df, atr_len=14):
    """Compute ATR using Wilder RMA."""
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    prev_c = np.roll(c, 1)
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = h[0] - l[0]
    return _rma_kernel(tr, atr_len)


# ---- D lines (SMA of K) ----

def compute_d_line(k_series, smooth):
    """Compute D line as SMA(K, smooth)."""
    return pd.Series(k_series).rolling(window=smooth, min_periods=1).mean().values


# ---- TDI ----

def compute_rsi(close, period):
    """Compute RSI using Wilder smoothing."""
    n = len(close)
    rsi = np.full(n, np.nan)
    if n < period + 1:
        return rsi
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rsi[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi[i + 1] = 100.0
        else:
            rsi[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return rsi


def sma(series, window):
    """Simple moving average with min_periods=1."""
    return pd.Series(series).rolling(window=window, min_periods=1).mean().values


def compute_tdi(close, rsi_period=9, smooth_period=5, signal_period=10):
    """Compute TDI: RSI smoothed price line and signal line."""
    rsi = compute_rsi(close, rsi_period)
    price_line = sma(rsi, smooth_period)
    signal_line = sma(rsi, signal_period)
    return price_line, signal_line


# ---- BBW / BBWP ----

def compute_bbwp(close, bb_len=20, bb_mult=2.0, bbwp_len=100, spectrum_ma_len=7):
    """Compute BBWP and Spectrum MA. Returns (bbwp, spectrum_ma, bbw_state)."""
    n = len(close)
    s = pd.Series(close)
    sma_bb = s.rolling(window=bb_len, min_periods=bb_len).mean().values
    std_bb = s.rolling(window=bb_len, min_periods=bb_len).std(ddof=0).values
    upper = sma_bb + bb_mult * std_bb
    lower = sma_bb - bb_mult * std_bb
    bbw = np.full(n, np.nan)
    valid = sma_bb != 0
    bbw[valid] = (upper[valid] - lower[valid]) / sma_bb[valid]

    bbwp = np.full(n, np.nan)
    for i in range(bbwp_len + bb_len - 1, n):
        window = bbw[i - bbwp_len + 1: i + 1]
        valid_w = window[~np.isnan(window)]
        if len(valid_w) > 0:
            bbwp[i] = np.sum(valid_w < bbw[i]) / len(valid_w) * 100.0

    spectrum_ma = sma(bbwp, spectrum_ma_len)

    bbw_state = np.full(n, 0, dtype=np.int8)  # 0=unknown
    for i in range(n):
        if np.isnan(bbwp[i]) or np.isnan(spectrum_ma[i]):
            continue
        if bbwp[i] > 80:
            bbw_state[i] = 2  # EXTREME
        elif bbwp[i] > spectrum_ma[i]:
            bbw_state[i] = 1  # HEALTHY
        else:
            bbw_state[i] = -1  # QUIET

    return bbwp, spectrum_ma, bbw_state


# ---- Markov State Classification ----

STATE_ZONE = 0
STATE_TURNING = 1
STATE_MOVING = 2
STATE_EXTENDED = 3

STATE_NAMES = {0: "ZONE", 1: "TURNING", 2: "MOVING", 3: "EXTENDED"}


def classify_markov_state_long(k_val, slope, accel):
    """Classify a single stoch bar into Markov state for LONG."""
    if k_val < 20:
        return STATE_ZONE
    if k_val > 50 and slope > 0:
        return STATE_EXTENDED
    if slope > 0 and accel > 0:
        return STATE_MOVING
    if slope > 0:
        return STATE_TURNING
    return STATE_ZONE


def classify_markov_state_short(k_val, slope, accel):
    """Classify a single stoch bar into Markov state for SHORT."""
    if k_val > 80:
        return STATE_ZONE
    if k_val < 50 and slope < 0:
        return STATE_EXTENDED
    if slope < 0 and accel < 0:
        return STATE_MOVING
    if slope < 0:
        return STATE_TURNING
    return STATE_ZONE


# ---- Main Signal Pipeline ----

def compute_signals_55_89(df, params=None):
    """Compute 55/89 EMA cross scalp signals mapped to Backtester384 columns.

    Pipeline:
    1. Compute stochs + D lines
    2. Compute EMA(55), EMA(89), delta
    3. Compute TDI, BBW
    4. Classify Markov states per stoch
    5. Run gated pipeline: IDLE -> MONITORING -> signal fires on alignment + delta cross
    6. Map to engine columns (long_a, short_a, etc.)
    """
    p = params or {}
    slope_n = p.get("slope_n", 5)
    slope_m = p.get("slope_m", 3)
    ema_fast = p.get("ema_fast", 55)
    ema_slow = p.get("ema_slow", 89)
    rsi_period = p.get("rsi_period", 9)
    rsi_smooth = p.get("rsi_smooth", 5)
    rsi_signal = p.get("rsi_signal", 10)
    bb_len = p.get("bb_len", 20)
    bb_mult = p.get("bb_mult", 2.0)
    bbwp_len = p.get("bbwp_len", 100)
    spectrum_ma_len = p.get("spectrum_ma_len", 7)
    atr_len = p.get("atr_length", 14)

    df = df.copy()
    n = len(df)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values

    # Step 1: Stochastics (all 4 K values)
    df = compute_all_stochastics(df, params)
    k9 = df["stoch_9"].values
    k14 = df["stoch_14"].values
    k40 = df["stoch_40"].values
    k60 = df["stoch_60"].values

    # D lines with correct smoothing per position management study
    d9 = compute_d_line(k9, 3)
    d14 = compute_d_line(k14, 3)
    d40 = compute_d_line(k40, 4)
    d60 = compute_d_line(k60, 10)
    df["stoch_9_d"] = d9
    df["stoch_14_d"] = d14
    df["stoch_40_d"] = d40
    df["stoch_60_d"] = d60

    # Step 2: EMAs and delta
    ema55 = ema(close, ema_fast)
    ema89 = ema(close, ema_slow)
    delta = ema55 - ema89
    df["ema_55"] = ema55
    df["ema_89"] = ema89
    df["ema_delta"] = delta

    # Step 3: ATR
    atr_vals = compute_atr(df, atr_len)
    df["atr"] = atr_vals

    # Step 4: TDI
    tdi_price, tdi_signal = compute_tdi(close, rsi_period, rsi_smooth, rsi_signal)
    df["tdi_price"] = tdi_price
    df["tdi_signal"] = tdi_signal

    # Step 5: BBW
    bbwp, spectrum_ma, bbw_state = compute_bbwp(close, bb_len, bb_mult, bbwp_len, spectrum_ma_len)
    df["bbwp_value"] = bbwp
    df["bbwp_spectrum"] = spectrum_ma
    bbw_state_str = np.where(bbw_state == 1, "HEALTHY",
                    np.where(bbw_state == 2, "EXTREME",
                    np.where(bbw_state == -1, "QUIET", "UNKNOWN")))
    df["bbwp_state"] = bbw_state_str

    # Step 6: Slopes and acceleration for stoch 40/60
    slope_40 = np.full(n, 0.0)
    slope_60 = np.full(n, 0.0)
    accel_40 = np.full(n, 0.0)
    accel_60 = np.full(n, 0.0)
    for i in range(slope_n, n):
        slope_40[i] = k40[i] - k40[i - slope_n]
        slope_60[i] = k60[i] - k60[i - slope_n]
    for i in range(slope_n + slope_m, n):
        accel_40[i] = slope_40[i] - slope_40[i - slope_m]
        accel_60[i] = slope_60[i] - slope_60[i - slope_m]

    # Also compute slopes for stoch 9 and 14 (for contradiction check)
    slope_9 = np.full(n, 0.0)
    slope_14 = np.full(n, 0.0)
    accel_9 = np.full(n, 0.0)
    accel_14 = np.full(n, 0.0)
    for i in range(slope_n, n):
        slope_9[i] = k9[i] - k9[i - slope_n]
        slope_14[i] = k14[i] - k14[i - slope_n]
    for i in range(slope_n + slope_m, n):
        accel_9[i] = slope_9[i] - slope_9[i - slope_m]
        accel_14[i] = slope_14[i] - slope_14[i - slope_m]

    # Step 7: Gated pipeline — bar by bar
    long_a = np.zeros(n, dtype=bool)
    short_a = np.zeros(n, dtype=bool)

    # State tracking
    # 0 = IDLE, 1 = MONITORING_LONG, 2 = MONITORING_SHORT
    system_state = 0
    prev_k9_above_d9 = False

    for i in range(1, n):
        if np.isnan(k9[i]) or np.isnan(d9[i]) or np.isnan(atr_vals[i]):
            continue

        k9_above_d9 = k9[i] > d9[i]
        k9_below_d9 = k9[i] < d9[i]

        # Detect stoch 9 K/D cross
        k9_cross_bull = k9_above_d9 and not prev_k9_above_d9
        k9_cross_bear = k9_below_d9 and prev_k9_above_d9

        prev_k9_above_d9 = k9_above_d9

        # State transitions
        if system_state == 0:
            # IDLE: waiting for stoch 9 K/D cross
            if k9_cross_bull:
                system_state = 1  # MONITORING_LONG
            elif k9_cross_bear:
                system_state = 2  # MONITORING_SHORT
            continue

        # MONITORING: check if stoch 9 reversed
        if system_state == 1 and k9_below_d9:
            system_state = 0
            if k9_cross_bear:
                system_state = 2
            continue
        if system_state == 2 and k9_above_d9:
            system_state = 0
            if k9_cross_bull:
                system_state = 1
            continue

        # --- Alignment check ---
        if system_state == 1:
            # LONG alignment
            st14 = classify_markov_state_long(k14[i], slope_14[i], accel_14[i])
            st40 = classify_markov_state_long(k40[i], slope_40[i], accel_40[i])
            st60 = classify_markov_state_long(k60[i], slope_60[i], accel_60[i])

            # Stoch 14: MOVING or EXTENDED
            s14_ok = st14 in (STATE_MOVING, STATE_EXTENDED)
            # Stoch 40, 60: TURNING, MOVING, or EXTENDED
            s40_ok = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            s60_ok = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            # No contradiction: no negative slope on any stoch
            no_contra = slope_9[i] >= 0 and slope_14[i] >= 0 and slope_40[i] >= 0 and slope_60[i] >= 0
            # Delta compressing: delta < 0 and approaching zero (velocity positive)
            # or delta already crossed zero on this bar
            delta_prev = delta[i - 1] if not np.isnan(delta[i - 1]) else delta[i]
            delta_velocity = delta[i] - delta_prev
            delta_compressing = (delta[i] < 0 and delta_velocity > 0) or delta[i] >= 0
            # TDI confirming: price line above signal line
            tdi_ok = (not np.isnan(tdi_price[i]) and not np.isnan(tdi_signal[i])
                      and tdi_price[i] > tdi_signal[i])
            # BBW not QUIET
            bbw_ok = bbw_state[i] != -1

            alignment = s14_ok and s40_ok and s60_ok and no_contra and delta_compressing and tdi_ok and bbw_ok

            # Signal fires when alignment + delta crosses zero (EMA cross)
            if alignment:
                # Delta cross: was negative, now >= 0
                if delta_prev < 0 and delta[i] >= 0:
                    long_a[i] = True

        elif system_state == 2:
            # SHORT alignment
            st14 = classify_markov_state_short(k14[i], slope_14[i], accel_14[i])
            st40 = classify_markov_state_short(k40[i], slope_40[i], accel_40[i])
            st60 = classify_markov_state_short(k60[i], slope_60[i], accel_60[i])

            s14_ok = st14 in (STATE_MOVING, STATE_EXTENDED)
            s40_ok = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            s60_ok = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            no_contra = slope_9[i] <= 0 and slope_14[i] <= 0 and slope_40[i] <= 0 and slope_60[i] <= 0
            delta_prev = delta[i - 1] if not np.isnan(delta[i - 1]) else delta[i]
            delta_velocity = delta[i] - delta_prev
            delta_compressing = (delta[i] > 0 and delta_velocity < 0) or delta[i] <= 0
            tdi_ok = (not np.isnan(tdi_price[i]) and not np.isnan(tdi_signal[i])
                      and tdi_price[i] < tdi_signal[i])
            bbw_ok = bbw_state[i] != -1

            alignment = s14_ok and s40_ok and s60_ok and no_contra and delta_compressing and tdi_ok and bbw_ok

            if alignment:
                # Delta cross: was positive, now <= 0
                if delta_prev > 0 and delta[i] <= 0:
                    short_a[i] = True

    # Step 8: Map to engine columns
    df["long_a"] = long_a
    df["short_a"] = short_a
    df["long_b"] = np.zeros(n, dtype=bool)
    df["long_c"] = np.zeros(n, dtype=bool)
    df["short_b"] = np.zeros(n, dtype=bool)
    df["short_c"] = np.zeros(n, dtype=bool)
    df["reentry_long"] = np.zeros(n, dtype=bool)
    df["reentry_short"] = np.zeros(n, dtype=bool)
    df["cloud3_allows_long"] = np.ones(n, dtype=bool)
    df["cloud3_allows_short"] = np.ones(n, dtype=bool)
    df["cloud2_cross_bull"] = np.zeros(n, dtype=bool)
    df["cloud2_cross_bear"] = np.zeros(n, dtype=bool)
    df["cloud3_cross_bull"] = np.zeros(n, dtype=bool)
    df["cloud3_cross_bear"] = np.zeros(n, dtype=bool)
    df["phase3_active_long"] = np.zeros(n, dtype=bool)
    df["phase3_active_short"] = np.zeros(n, dtype=bool)

    return df
