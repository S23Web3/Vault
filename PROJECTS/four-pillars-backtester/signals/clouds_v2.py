"""
Ripster EMA Cloud calculations v2 — ema() Numba JIT-compiled.
Drop-in replacement for signals.clouds.
"""
import numpy as np
import pandas as pd
from numba import njit


@njit(cache=True)
def ema(series, length):
    """EMA matching Pine Script ta.ema(); Numba JIT-compiled via @njit(cache=True)."""
    result = np.full(len(series), np.nan)
    if len(series) < length:
        return result
    result[length - 1] = np.mean(series[:length])
    mult = 2.0 / (length + 1)
    for i in range(length, len(series)):
        result[i] = series[i] * mult + result[i - 1] * (1 - mult)
    return result


def compute_clouds(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute Ripster EMA Clouds using JIT-compiled ema(); identical logic to v1."""
    p = params or {}
    c2_fast = p.get("cloud2_fast", 5)
    c2_slow = p.get("cloud2_slow", 12)
    c3_fast = p.get("cloud3_fast", 34)
    c3_slow = p.get("cloud3_slow", 50)
    c4_fast = p.get("cloud4_fast", 72)
    c4_slow = p.get("cloud4_slow", 89)
    close = df["close"].values
    df = df.copy()
    # Cloud 2
    df["ema5"] = ema(close, c2_fast)
    df["ema12"] = ema(close, c2_slow)
    df["cloud2_bull"] = df["ema5"] > df["ema12"]
    df["cloud2_top"] = np.maximum(df["ema5"], df["ema12"])
    df["cloud2_bottom"] = np.minimum(df["ema5"], df["ema12"])
    # Cloud 3
    df["ema34"] = ema(close, c3_fast)
    df["ema50"] = ema(close, c3_slow)
    df["cloud3_bull"] = df["ema34"] > df["ema50"]
    df["cloud3_top"] = np.maximum(df["ema34"], df["ema50"])
    df["cloud3_bottom"] = np.minimum(df["ema34"], df["ema50"])
    # Cloud 4
    df["ema72"] = ema(close, c4_fast)
    df["ema89"] = ema(close, c4_slow)
    df["cloud4_bull"] = df["ema72"] > df["ema89"]
    # Price position relative to Cloud 3
    df["price_pos"] = np.where(
        close > df["cloud3_top"].values, 1,
        np.where(close < df["cloud3_bottom"].values, -1, 0)
    )
    # Cloud 3 directional filter (v3.8: ALWAYS ON)
    df["cloud3_allows_long"] = df["price_pos"] >= 0
    df["cloud3_allows_short"] = df["price_pos"] <= 0
    # Cloud 2 crossovers (for re-entry)
    df["price_cross_above_cloud2"] = (close > df["cloud2_top"].values) & (
        np.roll(close, 1) <= np.roll(df["cloud2_top"].values, 1)
    )
    df["price_cross_below_cloud2"] = (close < df["cloud2_bottom"].values) & (
        np.roll(close, 1) >= np.roll(df["cloud2_bottom"].values, 1)
    )
    # Fix first bar
    df.iloc[0, df.columns.get_loc("price_cross_above_cloud2")] = False
    df.iloc[0, df.columns.get_loc("price_cross_below_cloud2")] = False
    return df
