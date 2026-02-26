"""
Layer 1: BBWP Calculator — Port of bbwp_v2.pine to Python.

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with columns: open, high, low, close, base_vol
Output: Same DataFrame with 10 new bbwp_ columns added.

Pine Script source of truth: 02-STRATEGY/Indicators/bbwp_v2.pine (264 lines, Pine v6)
"""

import warnings

import numpy as np
import pandas as pd

# ─── Default Parameters (matching Pine v2 inputs) ────────────────────────────

DEFAULT_PARAMS = {
    'basis_len': 13,
    'basis_type': 'SMA',
    'lookback': 100,
    'bbwp_ma_len': 5,
    'bbwp_ma_type': 'SMA',
    'extreme_low': 10,
    'extreme_high': 90,
    'spectrum_low': 25,
    'spectrum_high': 75,
    'ma_cross_timeout': 10,
}

# ─── State-to-Points mapping (Pine v2 lines 149-169) ─────────────────────────

STATE_POINTS = {
    'BLUE_DOUBLE': 2,
    'BLUE': 1,
    'RED_DOUBLE': 1,
    'RED': 1,
    'MA_CROSS_UP': 1,
    'MA_CROSS_DOWN': 0,
    'NORMAL': 0,
}

# ─── Required input columns ──────────────────────────────────────────────────

REQUIRED_COLS = ['close']

# ─── Output columns (10 total) ───────────────────────────────────────────────

OUTPUT_COLS = [
    'bbwp_value', 'bbwp_ma', 'bbwp_bbw_raw', 'bbwp_spectrum',
    'bbwp_state', 'bbwp_points', 'bbwp_is_blue_bar', 'bbwp_is_red_bar',
    'bbwp_ma_cross_up', 'bbwp_ma_cross_down',
]


def _apply_ma(series: pd.Series, length: int, ma_type: str) -> pd.Series:
    """Apply moving average of specified type to a series."""
    if ma_type == 'EMA':
        return series.ewm(span=length, adjust=False).mean()
    elif ma_type == 'WMA':
        weights = np.arange(1, length + 1, dtype=float)
        return series.rolling(length).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    elif ma_type == 'RMA':
        return series.ewm(alpha=1.0 / length, adjust=False).mean()
    elif ma_type == 'HMA':
        half_len = max(int(length / 2), 1)
        sqrt_len = max(int(np.sqrt(length)), 1)
        wma_half = _apply_ma(series, half_len, 'WMA')
        wma_full = _apply_ma(series, length, 'WMA')
        diff = 2 * wma_half - wma_full
        return _apply_ma(diff, sqrt_len, 'WMA')
    elif ma_type == 'VWMA':
        # Fallback to SMA if no volume context available
        warnings.warn("VWMA requested but no volume data available, falling back to SMA", stacklevel=2)
        return series.rolling(length).mean()
    else:
        # SMA (default)
        return series.rolling(length).mean()


def _percentrank_pine(bbw: pd.Series, lookback: int) -> pd.Series:
    """Match Pine's ta.percentrank with NaN-tolerant window (min lookback//2 valid)."""
    values = bbw.values
    n = len(values)
    result = np.full(n, np.nan)
    min_valid = max(lookback // 2, 1)

    for i in range(lookback, n):
        if np.isnan(values[i]):
            continue
        # Previous lookback values (NOT including current bar)
        prev_window = values[i - lookback:i]
        valid_mask = ~np.isnan(prev_window)
        valid_count = valid_mask.sum()
        if valid_count < min_valid:
            continue
        current = values[i]
        count_below = np.sum(prev_window[valid_mask] < current)
        result[i] = (count_below / valid_count) * 100

    return pd.Series(result, index=bbw.index)


def _spectrum_color(bbwp_val: float):
    """Map BBWP value to 4-zone spectrum color (Pine gradient inflection at 25/50/75)."""
    if np.isnan(bbwp_val):
        return None
    if bbwp_val <= 25:
        return 'blue'
    elif bbwp_val <= 50:
        return 'green'
    elif bbwp_val <= 75:
        return 'yellow'
    else:
        return 'red'


def _detect_states(bbwp_values: np.ndarray, bbwp_ma_values: np.ndarray,
                   params: dict) -> tuple:
    """Detect BBWP states using stateful MA cross persistence.

    Must iterate bar-by-bar because MA cross state persists across bars
    (Pine v2 uses `var` variables). Returns arrays for state, points,
    cross_up events, cross_down events.

    Pine v2 reference: lines 100-169.
    """
    n = len(bbwp_values)
    states = np.empty(n, dtype=object)
    points = np.zeros(n, dtype=np.int64)
    cross_up_events = np.zeros(n, dtype=bool)
    cross_down_events = np.zeros(n, dtype=bool)

    extreme_low = params['extreme_low']
    extreme_high = params['extreme_high']
    spectrum_low = params['spectrum_low']
    spectrum_high = params['spectrum_high']
    ma_cross_timeout = params['ma_cross_timeout']

    # Persistent state variables (Pine `var`)
    show_ma_cross_up = False
    show_ma_cross_down = False
    ma_cross_bar = -1  # -1 means na (no active cross)

    for i in range(n):
        bbwp = bbwp_values[i]
        bbwp_ma = bbwp_ma_values[i]

        # Handle NaN bbwp — default to NORMAL, 0 points
        if np.isnan(bbwp):
            states[i] = 'NORMAL'
            points[i] = 0
            continue

        # MA may still be NaN during warmup gap (bars with valid bbwp but NaN MA)
        ma_is_nan = np.isnan(bbwp_ma)

        # Bar conditions (Pine lines 104-105)
        blu_bar = bbwp <= extreme_low   # <=, not <
        red_bar = bbwp >= extreme_high  # >=, not >

        # Spectrum conditions (Pine lines 108-109)
        blu_spectrum = bbwp < spectrum_low   # <, strict
        red_spectrum = bbwp > spectrum_high  # >, strict

        # MA cross conditions — only fire in normal range (Pine lines 112-114)
        in_normal_range = (not blu_spectrum) and (not red_spectrum)

        # Crossover/crossunder detection (compare current vs previous bar)
        ma_cross_up_event = False
        ma_cross_down_event = False
        if i > 0 and in_normal_range and not ma_is_nan:
            prev_bbwp = bbwp_values[i - 1]
            prev_ma = bbwp_ma_values[i - 1]
            if not (np.isnan(prev_bbwp) or np.isnan(prev_ma)):
                # Pine ta.crossover: current > MA AND previous <= MA
                if bbwp > bbwp_ma and prev_bbwp <= prev_ma:
                    ma_cross_up_event = True
                # Pine ta.crossunder: current < MA AND previous >= MA
                if bbwp < bbwp_ma and prev_bbwp >= prev_ma:
                    ma_cross_down_event = True

        cross_up_events[i] = ma_cross_up_event
        cross_down_events[i] = ma_cross_down_event

        # Check timeout (Pine line 123)
        ma_cross_timed_out = False
        if ma_cross_bar >= 0:
            if (i - ma_cross_bar) >= ma_cross_timeout:
                ma_cross_timed_out = True

        # Update persistent state (Pine lines 125-140)
        if ma_cross_up_event:
            show_ma_cross_up = True
            show_ma_cross_down = False
            ma_cross_bar = i
        elif ma_cross_down_event:
            show_ma_cross_down = True
            show_ma_cross_up = False
            ma_cross_bar = i
        elif blu_spectrum or red_spectrum or ma_cross_timed_out:
            show_ma_cross_up = False
            show_ma_cross_down = False
            ma_cross_bar = -1

        # State determination — priority order (Pine lines 149-169)
        if blu_bar and blu_spectrum:
            states[i] = 'BLUE_DOUBLE'
            points[i] = 2
        elif blu_spectrum:
            states[i] = 'BLUE'
            points[i] = 1
        elif red_bar and red_spectrum:
            states[i] = 'RED_DOUBLE'
            points[i] = 1
        elif red_spectrum:
            states[i] = 'RED'
            points[i] = 1
        elif show_ma_cross_up:
            states[i] = 'MA_CROSS_UP'
            points[i] = 1
        elif show_ma_cross_down:
            states[i] = 'MA_CROSS_DOWN'
            points[i] = 0
        else:
            states[i] = 'NORMAL'
            points[i] = 0

    return states, points, cross_up_events, cross_down_events


def calculate_bbwp(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Port of bbwp_v2.pine to Python.

    Input: DataFrame with columns: open, high, low, close, base_vol
    Output: Same DataFrame with 10 new bbwp_ columns added.

    This is a PURE FUNCTION -- no side effects, no file I/O.
    """
    # Merge user params with defaults
    p = {**DEFAULT_PARAMS}
    if params:
        p.update(params)

    # Validate required columns
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Work on a copy to avoid mutating input
    result = df.copy()
    close = result['close'].astype(float)

    # ── Step 1: BB Width (Pine lines 89-91) ───────────────────────────────
    basis = _apply_ma(close, p['basis_len'], p['basis_type'])
    stdev = close.rolling(p['basis_len']).std(ddof=0)
    bbw = np.where(basis > 0, (2 * stdev) / basis, 0.0)
    bbw = pd.Series(bbw, index=close.index)
    # Propagate NaN from basis warmup
    bbw[basis.isna()] = np.nan

    result['bbwp_bbw_raw'] = bbw

    # ── Step 2: BBWP percentile rank (Pine line 94) ──────────────────────
    bbwp = _percentrank_pine(bbw, p['lookback'])
    result['bbwp_value'] = bbwp

    # ── Step 3: BBWP MA (Pine line 97) ───────────────────────────────────
    bbwp_ma = _apply_ma(bbwp, p['bbwp_ma_len'], p['bbwp_ma_type'])
    result['bbwp_ma'] = bbwp_ma

    # ── Step 4: Spectrum color (vectorized) ──────────────────────────────
    result['bbwp_spectrum'] = bbwp.apply(_spectrum_color)

    # ── Step 5: Bar conditions (vectorized, Pine lines 104-105) ──────────
    result['bbwp_is_blue_bar'] = bbwp <= p['extreme_low']
    result['bbwp_is_red_bar'] = bbwp >= p['extreme_high']
    # NaN comparisons already produce False — no explicit override needed

    # ── Step 6: State detection (loop — stateful) ────────────────────────
    bbwp_arr = bbwp.values.astype(float)
    bbwp_ma_arr = bbwp_ma.values.astype(float)

    states, pts, cross_up, cross_down = _detect_states(
        bbwp_arr, bbwp_ma_arr, p
    )

    result['bbwp_state'] = states
    result['bbwp_points'] = pts
    result['bbwp_ma_cross_up'] = cross_up
    result['bbwp_ma_cross_down'] = cross_down

    return result
