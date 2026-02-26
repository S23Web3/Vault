"""
Stochastic calculations — Raw K (no smoothing).
Matches v3.7.1 stoch_k() exactly.
"""

import numpy as np
import pandas as pd


def stoch_k(close: np.ndarray, high: np.ndarray, low: np.ndarray, k_len: int) -> np.ndarray:
    """
    Raw K stochastic — NO SMA smoothing.
    Returns array of same length as input. First (k_len-1) values are NaN.

    Matches Pine Script:
        stoch_k(int k_len) =>
            float lowest = ta.lowest(low, k_len)
            float highest = ta.highest(high, k_len)
            highest - lowest == 0 ? 50.0 : 100.0 * (close - lowest) / (highest - lowest)
    """
    n = len(close)
    result = np.full(n, np.nan)

    for i in range(k_len - 1, n):
        window_low = low[i - k_len + 1: i + 1]
        window_high = high[i - k_len + 1: i + 1]
        lowest = np.min(window_low)
        highest = np.max(window_high)
        if highest - lowest == 0:
            result[i] = 50.0
        else:
            result[i] = 100.0 * (close[i] - lowest) / (highest - lowest)

    return result


def compute_all_stochastics(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Compute all 4 stochastics + D line for a DataFrame with OHLCV columns.
    Adds columns: stoch_9, stoch_14, stoch_40, stoch_60, stoch_60_d
    All K lengths and D smoothing configurable via params.
    """
    p = params or {}
    k1 = p.get("stoch_k1", 9)
    k2 = p.get("stoch_k2", 14)
    k3 = p.get("stoch_k3", 40)
    k4 = p.get("stoch_k4", 60)
    d_smooth = p.get("stoch_d_smooth", 10)

    close = df["close"].values
    high = df["high"].values
    low = df["low"].values

    df = df.copy()
    df["stoch_9"] = stoch_k(close, high, low, k1)
    df["stoch_14"] = stoch_k(close, high, low, k2)
    df["stoch_40"] = stoch_k(close, high, low, k3)
    df["stoch_60"] = stoch_k(close, high, low, k4)

    # D line = SMA(stoch_60, d_smooth)
    df["stoch_60_d"] = df["stoch_60"].rolling(window=d_smooth, min_periods=1).mean()

    return df
