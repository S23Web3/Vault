"""
Stochastic calculations v2 — Raw K, no smoothing.
stoch_k() is Numba JIT-compiled; drop-in replacement for signals.stochastics.
"""
import numpy as np
import pandas as pd
from numba import njit


@njit(cache=True)
def stoch_k(close, high, low, k_len):
    """Raw K stochastic window loop; Numba JIT-compiled via @njit(cache=True)."""
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
    """Compute all 4 stochastic K values plus D smooth using JIT-compiled stoch_k."""
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
    df["stoch_60_d"] = df["stoch_60"].rolling(window=d_smooth, min_periods=1).mean()
    return df
