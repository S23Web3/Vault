"""
Ripster EMA Cloud calculations.
Matches v3.7.1 cloud logic exactly.
"""

import numpy as np
import pandas as pd


def ema(series: np.ndarray, length: int) -> np.ndarray:
    """
    Exponential Moving Average matching Pine Script ta.ema().
    Uses multiplier = 2 / (length + 1).
    """
    result = np.full(len(series), np.nan)
    if len(series) < length:
        return result

    # Seed with SMA of first `length` values
    result[length - 1] = np.mean(series[:length])
    mult = 2.0 / (length + 1)

    for i in range(length, len(series)):
        result[i] = series[i] * mult + result[i - 1] * (1 - mult)

    return result


def compute_clouds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Ripster EMA Clouds for a DataFrame.
    Adds columns: ema5, ema12, ema34, ema50, ema72, ema89,
                  cloud2_bull, cloud3_bull, cloud4_bull,
                  cloud2_top, cloud2_bottom, cloud3_top, cloud3_bottom,
                  price_pos (1=above cloud3, -1=below, 0=inside)
    """
    close = df["close"].values
    df = df.copy()

    # Cloud 2: 5/12
    df["ema5"] = ema(close, 5)
    df["ema12"] = ema(close, 12)
    df["cloud2_bull"] = df["ema5"] > df["ema12"]
    df["cloud2_top"] = np.maximum(df["ema5"], df["ema12"])
    df["cloud2_bottom"] = np.minimum(df["ema5"], df["ema12"])

    # Cloud 3: 34/50
    df["ema34"] = ema(close, 34)
    df["ema50"] = ema(close, 50)
    df["cloud3_bull"] = df["ema34"] > df["ema50"]
    df["cloud3_top"] = np.maximum(df["ema34"], df["ema50"])
    df["cloud3_bottom"] = np.minimum(df["ema34"], df["ema50"])

    # Cloud 4: 72/89
    df["ema72"] = ema(close, 72)
    df["ema89"] = ema(close, 89)
    df["cloud4_bull"] = df["ema72"] > df["ema89"]

    # Price position relative to Cloud 3
    df["price_pos"] = np.where(
        close > df["cloud3_top"].values, 1,
        np.where(close < df["cloud3_bottom"].values, -1, 0)
    )

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
