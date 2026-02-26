"""
Layer 3: Forward Return Tagger -- ATR-normalized forward returns for each bar.

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with OHLCV columns (open, high, low, close, base_vol).
Output: Same DataFrame with 17 new columns (8 per window x 2 windows + fwd_atr).

Does NOT depend on Layer 1/2. Works on raw OHLCV only.
"""

import numpy as np
import pandas as pd

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_WINDOWS = [10, 20]
REQUIRED_OHLCV = ['open', 'high', 'low', 'close', 'base_vol']
ATR_COL = 'fwd_atr'


def _calculate_atr(df, period=14):
    """Wilder ATR: exponential moving average of true range, alpha=1/period."""
    high = df['high'].values
    low = df['low'].values
    prev_close = df['close'].shift(1).values

    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - prev_close),
            np.abs(low - prev_close)
        )
    )
    atr = pd.Series(tr, index=df.index).ewm(
        alpha=1.0 / period, min_periods=period, adjust=False
    ).mean()
    return atr


def _forward_max(series, window):
    """Max of next `window` bars (EXCLUDING current bar). Vectorized."""
    return series[::-1].rolling(window=window, min_periods=window).max()[::-1].shift(-1)


def _forward_min(series, window):
    """Min of next `window` bars (EXCLUDING current bar). Vectorized."""
    return series[::-1].rolling(window=window, min_periods=window).min()[::-1].shift(-1)


def _forward_close(series, window):
    """Close value `window` bars ahead. Vectorized."""
    return series.shift(-window)


def tag_forward_returns(df, windows=None, atr_period=14, proper_move_atr=3.0):
    """Tag each bar with forward-looking return metrics.

    Input: DataFrame with OHLCV columns.
    Output: Same DataFrame with 8 columns per window + fwd_atr column.
    """
    if windows is None:
        windows = DEFAULT_WINDOWS

    for col in REQUIRED_OHLCV:
        if col not in df.columns:
            raise ValueError(f"Missing required OHLCV column: {col}")

    result = df.copy()
    close = result['close'].astype(float)
    high = result['high'].astype(float)
    low = result['low'].astype(float)

    # ATR calculation
    atr = _calculate_atr(result, period=atr_period)
    result[ATR_COL] = atr

    for w in windows:
        prefix = f"fwd_{w}_"

        # Forward max high / min low (excluding current bar)
        fwd_max_high = _forward_max(high, w)
        fwd_min_low = _forward_min(low, w)
        fwd_close = _forward_close(close, w)

        # Percentage returns (safe division: close=0 -> NaN)
        safe_close = np.where(close != 0, close, np.nan)

        max_up_pct = np.maximum(0, (fwd_max_high - close) / safe_close * 100)
        max_down_pct = np.minimum(0, (fwd_min_low - close) / safe_close * 100)
        close_pct = (fwd_close - close) / safe_close * 100

        # ATR-normalized returns (safe division: atr=0 -> NaN)
        safe_atr = np.where(atr > 0, atr, np.nan)

        max_up_atr = np.maximum(0, (fwd_max_high - close) / safe_atr)
        max_down_atr = np.maximum(0, (close - fwd_min_low) / safe_atr)
        max_range_atr = (fwd_max_high - fwd_min_low) / safe_atr

        # Direction label
        close_pct_series = pd.Series(close_pct, index=result.index)
        direction = np.where(
            close_pct_series.isna(), None,
            np.where(close_pct > 0, 'up',
                     np.where(close_pct < 0, 'down', 'flat'))
        )

        # Proper move flag (NaN where max_range_atr is NaN)
        range_series = pd.Series(max_range_atr, index=result.index)
        proper_move = np.where(range_series.isna(), None, range_series >= proper_move_atr)

        # Assign columns
        result[prefix + 'max_up_pct'] = max_up_pct
        result[prefix + 'max_down_pct'] = max_down_pct
        result[prefix + 'max_up_atr'] = max_up_atr
        result[prefix + 'max_down_atr'] = max_down_atr
        result[prefix + 'close_pct'] = close_pct
        result[prefix + 'direction'] = direction
        result[prefix + 'max_range_atr'] = max_range_atr
        result[prefix + 'proper_move'] = proper_move

    return result
