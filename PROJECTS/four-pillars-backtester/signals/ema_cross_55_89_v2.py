"""
55/89 EMA Cross Scalp v2 -- Signal pipeline.

v2 redesign: 2-state stoch 9 D overzone entry, cascading alignment
(affects trade grade, not entry decision), EMA cross columns for BE trigger,
TDI uses RSI 14, regression channel gate (stub or real module).

Entry logic:
  State 1 (MONITORING): stoch 9 D drops below 20 (long) / above 80 (short)
  State 2 (ENTRY): stoch 9 D exits overzone + regression gate passes -> signal fires

Grade system at entry:
  A = stoch 40 AND 60 already TURNING+ at entry
  B = stoch 40 OR 60 TURNING+ (partial alignment)
  C = neither 40 nor 60 TURNING+ (no alignment yet)

Source of truth: 06-CLAUDE-LOGS/plans/2026-03-10-5589-v2-redesign-plan.md
"""

import numpy as np
import pandas as pd
from numba import njit

from .stochastics_v2 import compute_all_stochastics
from .clouds_v2 import ema

# Try real regression channel; fall back to stub
try:
    from .regression_channel import (
        fit_channel,
        pre_stage1_gate,
        compute_channel_anchored,
        price_in_lower_half,
    )
    _HAS_REGRESSION = True
except ImportError:
    _HAS_REGRESSION = False


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


# ---- TDI (RSI 14 for v2) ----

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


def compute_tdi(close, rsi_period=14, smooth_period=5, signal_period=10):
    """Compute TDI: RSI smoothed price line and signal line. v2 default RSI=14."""
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

    bbw_state = np.full(n, 0, dtype=np.int8)
    for i in range(n):
        if np.isnan(bbwp[i]) or np.isnan(spectrum_ma[i]):
            continue
        if bbwp[i] > 80:
            bbw_state[i] = 2   # EXTREME
        elif bbwp[i] > spectrum_ma[i]:
            bbw_state[i] = 1   # HEALTHY
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


# ---- Regression Channel Gate ----

def regression_gate_long(i, close_arr, pre_lookback=20, r2_min=0.45, slope_pct_max=-0.001):
    """Check if pre-entry channel shows orderly decline for LONG entry."""
    if not _HAS_REGRESSION:
        return True  # stub: always pass
    start = max(0, i - pre_lookback)
    if i - start < 3:
        return True  # not enough bars, pass by default
    prices = close_arr[start:i + 1]
    ch = fit_channel(prices)
    return pre_stage1_gate(ch, r2_min=r2_min, slope_pct_max=slope_pct_max)


def regression_gate_short(i, close_arr, pre_lookback=20, r2_min=0.45, slope_pct_min=0.001):
    """Check if pre-entry channel shows orderly rally for SHORT entry."""
    if not _HAS_REGRESSION:
        return True  # stub: always pass
    start = max(0, i - pre_lookback)
    if i - start < 3:
        return True
    prices = close_arr[start:i + 1]
    ch = fit_channel(prices)
    # For short: need positive slope (was rallying) and good R2
    return ch.r_squared > r2_min and ch.slope_pct > slope_pct_min


# ---- Main Signal Pipeline v2 ----

def compute_signals_55_89(df, params=None):
    """Compute 55/89 v2 signals: 2-state overzone entry, cascading grade, EMA cross BE columns.

    Pipeline:
    1. Compute stochs + D lines
    2. Compute EMA(55), EMA(89), delta, EMA cross columns
    3. Compute TDI (RSI 14), BBW
    4. Classify Markov states per stoch (for grading)
    5. Run 2-state overzone pipeline: IDLE -> MONITORING -> ENTRY
    6. Grade each signal: A/B/C based on stoch 40/60 alignment at entry
    7. Map to engine columns (long_a, short_a, trade_grade, ema_cross_bull, ema_cross_bear)
    """
    p = params or {}
    slope_n = p.get("slope_n", 5)
    slope_m = p.get("slope_m", 3)
    ema_fast = p.get("ema_fast", 55)
    ema_slow = p.get("ema_slow", 89)
    rsi_period = p.get("rsi_period", 14)
    rsi_smooth = p.get("rsi_smooth", 5)
    rsi_signal = p.get("rsi_signal", 10)
    bb_len = p.get("bb_len", 20)
    bb_mult = p.get("bb_mult", 2.0)
    bbwp_len = p.get("bbwp_len", 100)
    spectrum_ma_len = p.get("spectrum_ma_len", 7)
    atr_len = p.get("atr_length", 14)
    overzone_long = p.get("overzone_long_threshold", 20.0)
    overzone_short = p.get("overzone_short_threshold", 80.0)
    min_signal_gap = p.get("min_signal_gap", 50)
    pre_lookback = p.get("pre_lookback", 20)
    r2_min = p.get("r2_min", 0.45)

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

    # EMA cross columns (for engine BE trigger)
    ema_cross_bull = np.zeros(n, dtype=bool)
    ema_cross_bear = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if np.isnan(delta[i]) or np.isnan(delta[i - 1]):
            continue
        if delta[i - 1] < 0 and delta[i] >= 0:
            ema_cross_bull[i] = True
        elif delta[i - 1] > 0 and delta[i] <= 0:
            ema_cross_bear[i] = True
    df["ema_cross_bull"] = ema_cross_bull
    df["ema_cross_bear"] = ema_cross_bear

    # Step 3: ATR
    atr_vals = compute_atr(df, atr_len)
    df["atr"] = atr_vals

    # Step 4: TDI (RSI 14 for v2)
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

    # Step 6: Slopes and acceleration for grading
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

    # Step 7: 2-state overzone pipeline -- bar by bar
    long_a = np.zeros(n, dtype=bool)
    short_a = np.zeros(n, dtype=bool)
    trade_grade = np.full(n, "", dtype=object)

    # State tracking for 2-state machine
    # 0 = IDLE, 1 = MONITORING_LONG, 2 = MONITORING_SHORT
    system_state = 0
    last_signal_bar = -9999

    for i in range(1, n):
        if np.isnan(d9[i]) or np.isnan(atr_vals[i]):
            continue

        d9_val = d9[i]
        d9_prev = d9[i - 1] if not np.isnan(d9[i - 1]) else d9_val

        # ---- State transitions ----

        if system_state == 0:
            # IDLE: detect overzone entry
            if d9_val < overzone_long and d9_prev >= overzone_long:
                # Stoch 9 D just dropped below 20 -> start monitoring long
                system_state = 1
            elif d9_val > overzone_short and d9_prev <= overzone_short:
                # Stoch 9 D just rose above 80 -> start monitoring short
                system_state = 2
            continue

        elif system_state == 1:
            # MONITORING_LONG: waiting for stoch 9 D to exit overzone (rise back above 20)
            if d9_val >= overzone_long and d9_prev < overzone_long:
                # Overzone exit detected -- check gates
                if i - last_signal_bar < min_signal_gap:
                    system_state = 0  # cooldown, back to idle
                    continue

                # Regression channel gate
                if not regression_gate_long(i, close, pre_lookback, r2_min):
                    system_state = 0  # gate failed
                    continue

                # ENTRY: fire long signal
                long_a[i] = True
                last_signal_bar = i

                # Grade: check stoch 40/60 alignment at entry
                st40 = classify_markov_state_long(k40[i], slope_40[i], accel_40[i])
                st60 = classify_markov_state_long(k60[i], slope_60[i], accel_60[i])
                s40_turning = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
                s60_turning = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)

                if s40_turning and s60_turning:
                    trade_grade[i] = "A"
                elif s40_turning or s60_turning:
                    trade_grade[i] = "B"
                else:
                    trade_grade[i] = "C"

                system_state = 0  # back to idle after signal
                continue

            # If stoch 9 D rises above overzone_short while monitoring long,
            # that is contradictory -- go idle
            if d9_val > overzone_short:
                system_state = 0
                continue

        elif system_state == 2:
            # MONITORING_SHORT: waiting for stoch 9 D to exit overzone (drop back below 80)
            if d9_val <= overzone_short and d9_prev > overzone_short:
                # Overzone exit detected -- check gates
                if i - last_signal_bar < min_signal_gap:
                    system_state = 0
                    continue

                # Regression channel gate (for short: need prior rally)
                if not regression_gate_short(i, close, pre_lookback, r2_min):
                    system_state = 0
                    continue

                # ENTRY: fire short signal
                short_a[i] = True
                last_signal_bar = i

                # Grade: check stoch 40/60 alignment at entry
                st40 = classify_markov_state_short(k40[i], slope_40[i], accel_40[i])
                st60 = classify_markov_state_short(k60[i], slope_60[i], accel_60[i])
                s40_turning = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
                s60_turning = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)

                if s40_turning and s60_turning:
                    trade_grade[i] = "A"
                elif s40_turning or s60_turning:
                    trade_grade[i] = "B"
                else:
                    trade_grade[i] = "C"

                system_state = 0
                continue

            # If stoch 9 D drops below overzone_long while monitoring short,
            # contradictory -- go idle
            if d9_val < overzone_long:
                system_state = 0
                continue

    # Step 8: Map to engine columns
    df["long_a"] = long_a
    df["short_a"] = short_a
    df["trade_grade"] = trade_grade
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
