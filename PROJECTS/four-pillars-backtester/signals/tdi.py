"""
TDI (Traders Dynamic Index) — Standalone indicator module.

RSI + Bollinger Bands on RSI + two MA lines + multi-color zones +
pivot-based divergence (regular + hidden) + buy/sell signals + cross signals
+ graded core signal layer.

Two presets: 'cw_trades' (RSI 13) and 'classic' (RSI 14, Dean Malone).
All parameters overridable via params dict.

Signal architecture (from ZyadaCharts/LazyBear Pine source):
  - tdi_fast_ma   : SMA(RSI, fast_len=2)    -- reactive trade line
  - tdi_signal    : SMA(RSI, slow_len=7/8)  -- slower signal line
  - tdi_bb_mid    : SMA(RSI, bb_period)     -- BB midline (distinct from signal)
  - tdi_cloud_bull: fast_ma > signal        -- cloud fill direction
  - tdi_long      : crossover(fast, signal) AND signal > bb_mid AND signal > 50
  - tdi_short     : crossunder(fast, signal) AND signal < bb_mid AND signal < 50
  - tdi_best_setup: crossover(fast, bb_mid)
  - tdi_scalp     : fast_ma > bb_mid (bool, background trend bias)

Zone color: RSI vs signal delta. BB breach overrides (yellow/red).
Divergence: RSI-pivot-only approach matching Pine source. Regular + hidden.

Public API:
  compute_tdi(df, params)        -> DataFrame + 24 tdi_ columns
  compute_tdi_core(df, params)   -> DataFrame + 24 tdi_ + 8 tdi_core_ columns

Run: from signals.tdi import compute_tdi, compute_tdi_core
"""

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ---- Presets ----------------------------------------------------------------

PRESETS = {
    "cw_trades": {
        "tdi_rsi_period": 13,
        "tdi_fast_ma_len": 2,
        "tdi_signal_ma_len": 8,
        "tdi_bb_period": 34,
        "tdi_bb_std": 1.6185,
    },
    "classic": {
        # Dean Malone original TDI settings
        "tdi_rsi_period": 14,
        "tdi_fast_ma_len": 2,
        "tdi_signal_ma_len": 7,
        "tdi_bb_period": 20,
        "tdi_bb_std": 2.0,
    },
}

DEFAULT_PARAMS = {
    "tdi_preset": "cw_trades",
    "tdi_rsi_period": None,
    "tdi_fast_ma_len": None,
    "tdi_signal_ma_len": None,
    "tdi_bb_period": None,
    "tdi_bb_std": None,
    # Divergence pivot settings (match Pine source defaults)
    "tdi_pivot_lookback": 5,
    "tdi_div_range_lower": 5,    # min bars between RSI pivots for divergence
    "tdi_div_range_upper": 60,   # max bars between RSI pivots for divergence
    # Zone delta thresholds: RSI - signal distance
    "tdi_delta_neutral": 2.0,    # abs(delta) <= this -> NEUTRAL
    "tdi_delta_weak": 5.0,       # abs(delta) <= this -> WEAK bull/bear
    "tdi_delta_strong": 10.0,    # abs(delta) > this -> STRONG bull/bear
}

# ---- Zone colors ------------------------------------------------------------
BB_UPPER_BREACH = ("BB_UPPER_BREACH", "#FFFF00")
BB_LOWER_BREACH = ("BB_LOWER_BREACH", "#FF0000")

BULL_ZONES = {"STRONG_BULL", "BULL", "WEAK_BULL", "BB_UPPER_BREACH"}
BEAR_ZONES = {"STRONG_BEAR", "BEAR", "WEAK_BEAR", "BB_LOWER_BREACH"}
STRONG_BULL_ZONES = {"STRONG_BULL", "BB_UPPER_BREACH"}
STRONG_BEAR_ZONES = {"STRONG_BEAR", "BB_LOWER_BREACH"}


# ---- Private helpers --------------------------------------------------------

def _resolve_params(params):
    """Merge preset defaults with user overrides."""
    merged = dict(DEFAULT_PARAMS)
    if params:
        merged.update(params)
    preset_name = merged["tdi_preset"]
    preset = PRESETS.get(preset_name, PRESETS["cw_trades"])
    for key, val in preset.items():
        if merged.get(key) is None:
            merged[key] = val
    return merged


def _rsi_wilder(close, period):
    """Compute RSI using Wilder smoothing (RMA). Matches Pine ta.rsi()."""
    n = len(close)
    rsi = np.full(n, np.nan)
    if n < period + 1:
        return rsi
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))
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


def _sma(series, window):
    """Simple moving average. NaN for first (window-1) bars."""
    return pd.Series(series).rolling(window=window, min_periods=window).mean().values


def _bb_on_rsi(rsi, period, std_dev):
    """Bollinger Bands on RSI. Returns (upper, mid, lower). ddof=0 matches Pine stdev."""
    s = pd.Series(rsi)
    mid = s.rolling(window=period, min_periods=period).mean().values
    std = s.rolling(window=period, min_periods=period).std(ddof=0).values
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    return upper, mid, lower


def _classify_zones(rsi, signal, bb_upper, bb_lower, delta_neutral, delta_weak, delta_strong):
    """Zone classification: BB breach overrides, then RSI-vs-signal delta zones."""
    n = len(rsi)
    zones = np.full(n, "", dtype=object)
    colors = np.full(n, "", dtype=object)
    for i in range(n):
        r = rsi[i]
        if np.isnan(r):
            continue
        bbu = bb_upper[i] if not np.isnan(bb_upper[i]) else np.inf
        bbl = bb_lower[i] if not np.isnan(bb_lower[i]) else -np.inf
        if r > bbu:
            zones[i] = BB_UPPER_BREACH[0]
            colors[i] = BB_UPPER_BREACH[1]
            continue
        if r < bbl:
            zones[i] = BB_LOWER_BREACH[0]
            colors[i] = BB_LOWER_BREACH[1]
            continue
        sig = signal[i]
        if np.isnan(sig):
            zones[i] = "NEUTRAL"
            colors[i] = "#808080"
            continue
        delta = r - sig
        if abs(delta) <= delta_neutral:
            zones[i] = "NEUTRAL"
            colors[i] = "#808080"
        elif delta > delta_strong:
            zones[i] = "STRONG_BULL"
            colors[i] = "#00FF00"
        elif delta > delta_weak:
            zones[i] = "BULL"
            colors[i] = "#008000"
        elif delta > delta_neutral:
            zones[i] = "WEAK_BULL"
            colors[i] = "#006400"
        elif delta < -delta_strong:
            zones[i] = "STRONG_BEAR"
            colors[i] = "#FF00FF"
        elif delta < -delta_weak:
            zones[i] = "BEAR"
            colors[i] = "#800080"
        else:
            zones[i] = "WEAK_BEAR"
            colors[i] = "#4B0082"
    return zones, colors


def _cross(a, b):
    """Crossover detection. Returns (cross_up, cross_down) bool arrays."""
    n = len(a)
    cross_up = np.zeros(n, dtype=bool)
    cross_down = np.zeros(n, dtype=bool)
    for i in range(1, n):
        if np.isnan(a[i]) or np.isnan(b[i]) or np.isnan(a[i - 1]) or np.isnan(b[i - 1]):
            continue
        if a[i] > b[i] and a[i - 1] <= b[i - 1]:
            cross_up[i] = True
        if a[i] < b[i] and a[i - 1] >= b[i - 1]:
            cross_down[i] = True
    return cross_up, cross_down


def _detect_pivots(series, lookback):
    """Detect confirmed swing highs/lows using symmetric window. Returns (is_high, is_low)."""
    n = len(series)
    is_high = np.zeros(n, dtype=bool)
    is_low = np.zeros(n, dtype=bool)
    for i in range(lookback, n - lookback):
        if np.isnan(series[i]):
            continue
        window = series[i - lookback: i + lookback + 1]
        if np.any(np.isnan(window)):
            continue
        if series[i] == np.max(window):
            is_high[i] = True
        if series[i] == np.min(window):
            is_low[i] = True
    return is_high, is_low


def _detect_divergences(close, rsi, pivot_lookback, range_lower, range_upper):
    """RSI-pivot-based divergence matching Pine source. Returns 4 bool arrays.

    Uses RSI pivots only (not price pivots). Reads price at RSI pivot bars.
    This matches Pine: plFound = pivotlow(osc, lbL, lbR) with price read at same bar.

    Regular bull  : RSI higher low  + price lower low  (classic bull div)
    Hidden bull   : RSI lower low   + price higher low (continuation bull)
    Regular bear  : RSI lower high  + price higher high (classic bear div)
    Hidden bear   : RSI higher high + price lower high (continuation bear)
    Range check   : gap between consecutive RSI pivots must be range_lower..range_upper.
    """
    n = len(close)
    reg_bull = np.zeros(n, dtype=bool)
    reg_bear = np.zeros(n, dtype=bool)
    hid_bull = np.zeros(n, dtype=bool)
    hid_bear = np.zeros(n, dtype=bool)

    rsi_is_high, rsi_is_low = _detect_pivots(rsi, pivot_lookback)

    # ---- RSI pivot lows -> bull divergences ----
    prev_idx = -1
    for i in range(n):
        if rsi_is_low[i]:
            if prev_idx >= 0:
                gap = i - prev_idx
                if range_lower <= gap <= range_upper:
                    confirm = min(i + pivot_lookback, n - 1)
                    # Regular bull: RSI HL + price LL
                    if rsi[i] > rsi[prev_idx] and close[i] < close[prev_idx]:
                        reg_bull[confirm] = True
                    # Hidden bull: RSI LL + price HL
                    if rsi[i] < rsi[prev_idx] and close[i] > close[prev_idx]:
                        hid_bull[confirm] = True
            prev_idx = i

    # ---- RSI pivot highs -> bear divergences ----
    prev_idx = -1
    for i in range(n):
        if rsi_is_high[i]:
            if prev_idx >= 0:
                gap = i - prev_idx
                if range_lower <= gap <= range_upper:
                    confirm = min(i + pivot_lookback, n - 1)
                    # Regular bear: RSI LH + price HH
                    if rsi[i] < rsi[prev_idx] and close[i] > close[prev_idx]:
                        reg_bear[confirm] = True
                    # Hidden bear: RSI HH + price LH
                    if rsi[i] > rsi[prev_idx] and close[i] < close[prev_idx]:
                        hid_bear[confirm] = True
            prev_idx = i

    return reg_bull, reg_bear, hid_bull, hid_bear


# ---- Public API: compute_tdi ------------------------------------------------

def compute_tdi(df, params=None):
    """Compute TDI indicator columns. Returns DataFrame with 24 new tdi_ columns.

    Standalone — not wired into the signal pipeline.
    """
    p = _resolve_params(params)
    rsi_period = p["tdi_rsi_period"]
    fast_ma_len = p["tdi_fast_ma_len"]
    signal_ma_len = p["tdi_signal_ma_len"]
    bb_period = p["tdi_bb_period"]
    bb_std = p["tdi_bb_std"]
    pivot_lookback = p["tdi_pivot_lookback"]
    div_range_lower = p["tdi_div_range_lower"]
    div_range_upper = p["tdi_div_range_upper"]
    delta_neutral = p["tdi_delta_neutral"]
    delta_weak = p["tdi_delta_weak"]
    delta_strong = p["tdi_delta_strong"]

    result = df.copy()
    close = result["close"].values.astype(float)

    # ---- Core lines ----
    rsi = _rsi_wilder(close, rsi_period)
    fast_ma = _sma(rsi, fast_ma_len)
    signal = _sma(rsi, signal_ma_len)
    bb_upper, bb_mid, bb_lower = _bb_on_rsi(rsi, bb_period, bb_std)

    result["tdi_rsi"] = rsi
    result["tdi_fast_ma"] = fast_ma
    result["tdi_signal"] = signal
    result["tdi_bb_upper"] = bb_upper
    result["tdi_bb_mid"] = bb_mid
    result["tdi_bb_lower"] = bb_lower

    # ---- Zone colors ----
    zones, colors = _classify_zones(rsi, signal, bb_upper, bb_lower,
                                    delta_neutral, delta_weak, delta_strong)
    result["tdi_zone"] = zones
    result["tdi_color"] = colors

    # ---- Cloud fill direction (vectorized) ----
    valid = ~np.isnan(fast_ma) & ~np.isnan(signal)
    result["tdi_cloud_bull"] = valid & (fast_ma > signal)

    # ---- Buy / Sell signals (vectorized) ----
    fast_cross_up, fast_cross_down = _cross(fast_ma, signal)
    valid_sig = ~np.isnan(signal) & ~np.isnan(bb_mid)
    result["tdi_long"] = fast_cross_up & valid_sig & (signal > bb_mid) & (signal > 50.0)
    result["tdi_short"] = fast_cross_down & valid_sig & (signal < bb_mid) & (signal < 50.0)

    # ---- Best setup: fast MA crosses above BB midline ----
    best_up, best_down = _cross(fast_ma, bb_mid)
    result["tdi_best_setup"] = best_up
    result["tdi_best_setup_short"] = best_down

    # ---- Scalp bias: fast MA above BB midline (vectorized) ----
    valid_bb = ~np.isnan(fast_ma) & ~np.isnan(bb_mid)
    result["tdi_scalp"] = valid_bb & (fast_ma > bb_mid)

    # ---- Divergence ----
    reg_bull, reg_bear, hid_bull, hid_bear = _detect_divergences(
        close, rsi, pivot_lookback, div_range_lower, div_range_upper
    )
    result["tdi_bull_div"] = reg_bull
    result["tdi_bear_div"] = reg_bear
    result["tdi_hidden_bull_div"] = hid_bull
    result["tdi_hidden_bear_div"] = hid_bear

    # ---- RSI cross signals ----
    fifty = np.full(len(close), 50.0)
    up_sig, down_sig = _cross(rsi, signal)
    result["tdi_rsi_cross_signal_up"] = up_sig
    result["tdi_rsi_cross_signal_down"] = down_sig

    up_bb, _ = _cross(rsi, bb_upper)
    result["tdi_rsi_cross_bb_upper"] = up_bb

    _, down_bb = _cross(rsi, bb_lower)
    result["tdi_rsi_cross_bb_lower"] = down_bb

    up_50, down_50 = _cross(rsi, fifty)
    result["tdi_rsi_cross_50_up"] = up_50
    result["tdi_rsi_cross_50_down"] = down_50

    log.debug("TDI: preset=%s rsi=%d fast=%d signal=%d bb=%d/%g",
              p["tdi_preset"], rsi_period, fast_ma_len, signal_ma_len, bb_period, bb_std)

    return result


# ---- Public API: compute_tdi_core -------------------------------------------

def compute_tdi_core(df, params=None):
    """Compute TDI + graded core signal layer. Returns DataFrame with 24+8 columns.

    Core signal logic (graded A/B/C matching Four Pillars convention):

    LONG A  : tdi_long + scalp bias + strong/bull zone  (highest confidence)
    LONG B  : tdi_long + scalp bias                     (standard entry)
    LONG C  : best_setup cross + scalp bias             (early/aggressive)
    LONG REV: regular bull divergence + RSI cross 50 up (reversal)

    SHORT A  : tdi_short + no scalp bias + strong/bear zone
    SHORT B  : tdi_short + no scalp bias
    SHORT C  : best_setup_short cross + no scalp bias
    SHORT REV: regular bear divergence + RSI cross 50 down
    """
    result = compute_tdi(df, params)

    zone = result["tdi_zone"].values
    scalp = result["tdi_scalp"].values

    bull_zone = np.array([z in BULL_ZONES for z in zone])
    bear_zone = np.array([z in BEAR_ZONES for z in zone])
    strong_bull = np.array([z in STRONG_BULL_ZONES for z in zone])
    strong_bear = np.array([z in STRONG_BEAR_ZONES for z in zone])

    # Long grades
    result["tdi_core_long_a"] = (
        result["tdi_long"].values & scalp & (strong_bull | bull_zone)
    )
    result["tdi_core_long_b"] = (
        result["tdi_long"].values & scalp
    )
    result["tdi_core_long_c"] = (
        result["tdi_best_setup"].values & scalp
    )
    result["tdi_core_long_rev"] = (
        result["tdi_bull_div"].values & result["tdi_rsi_cross_50_up"].values
    )

    # Short grades
    result["tdi_core_short_a"] = (
        result["tdi_short"].values & ~scalp & (strong_bear | bear_zone)
    )
    result["tdi_core_short_b"] = (
        result["tdi_short"].values & ~scalp
    )
    result["tdi_core_short_c"] = (
        result["tdi_best_setup_short"].values & ~scalp
    )
    result["tdi_core_short_rev"] = (
        result["tdi_bear_div"].values & result["tdi_rsi_cross_50_down"].values
    )

    log.debug("TDI core signals computed")
    return result
