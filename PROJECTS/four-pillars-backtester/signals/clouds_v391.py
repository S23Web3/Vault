"""
Ripster EMA Cloud calculations v391.

Extends clouds.py with EMA cross-detection columns required by the
3-phase SL movement system and Cloud 2 hard-close exit logic.

New columns vs clouds.py:
  cloud2_cross_bull  - True on the bar EMA5 crosses above EMA12 (one bar only)
  cloud2_cross_bear  - True on the bar EMA5 crosses below EMA12
  cloud3_cross_bull  - True on the bar EMA34 crosses above EMA50
  cloud3_cross_bear  - True on the bar EMA34 crosses below EMA50
  cloud4_bull        - EMA72 > EMA89 (already in clouds.py, kept for clarity)
  phase3_active_long - cloud3_bull AND cloud4_bull (Phase 3 trail trigger for longs)
  phase3_active_short- cloud3_bear AND cloud4_bear (Phase 3 trail trigger for shorts)
"""

import numpy as np
import pandas as pd


def ema(series: np.ndarray, length: int) -> np.ndarray:
    """Exponential Moving Average matching Pine Script ta.ema()."""
    result = np.full(len(series), np.nan)
    if len(series) < length:
        return result
    result[length - 1] = np.mean(series[:length])
    mult = 2.0 / (length + 1)
    for i in range(length, len(series)):
        result[i] = series[i] * mult + result[i - 1] * (1 - mult)
    return result


def compute_clouds_v391(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Compute Ripster EMA Clouds with full cross-detection for v391.

    Returns df with all original cloud columns plus:
      cloud2_cross_bull, cloud2_cross_bear,
      cloud3_cross_bull, cloud3_cross_bear,
      phase3_active_long, phase3_active_short
    """
    p = params or {}
    c2_fast = p.get("cloud2_fast", 5)
    c2_slow = p.get("cloud2_slow", 12)
    c3_fast = p.get("cloud3_fast", 34)
    c3_slow = p.get("cloud3_slow", 50)
    c4_fast = p.get("cloud4_fast", 72)
    c4_slow = p.get("cloud4_slow", 89)

    close = df["close"].values
    df = df.copy()

    # Cloud 2 (EMA 5/12)
    ema5  = ema(close, c2_fast)
    ema12 = ema(close, c2_slow)
    df["ema5"]         = ema5
    df["ema12"]        = ema12
    df["cloud2_bull"]  = ema5 > ema12
    df["cloud2_bear"]  = ema5 < ema12
    df["cloud2_top"]   = np.maximum(ema5, ema12)
    df["cloud2_bottom"]= np.minimum(ema5, ema12)

    # Cloud 3 (EMA 34/50)
    ema34 = ema(close, c3_fast)
    ema50 = ema(close, c3_slow)
    df["ema34"]        = ema34
    df["ema50"]        = ema50
    df["cloud3_bull"]  = ema34 > ema50
    df["cloud3_bear"]  = ema34 < ema50
    df["cloud3_top"]   = np.maximum(ema34, ema50)
    df["cloud3_bottom"]= np.minimum(ema34, ema50)

    # Cloud 4 (EMA 72/89)
    ema72 = ema(close, c4_fast)
    ema89 = ema(close, c4_slow)
    df["ema72"]        = ema72
    df["ema89"]        = ema89
    df["cloud4_bull"]  = ema72 > ema89
    df["cloud4_bear"]  = ema72 < ema89

    # Price position relative to Cloud 3
    df["price_pos"] = np.where(
        close > df["cloud3_top"].values,  1,
        np.where(close < df["cloud3_bottom"].values, -1, 0)
    )
    df["cloud3_allows_long"]  = df["price_pos"] >= 0
    df["cloud3_allows_short"] = df["price_pos"] <= 0

    # Price cross over Cloud 2 (for re-entry signals — unchanged from v390)
    df["price_cross_above_cloud2"] = (close > df["cloud2_top"].values) & (
        np.roll(close, 1) <= np.roll(df["cloud2_top"].values, 1)
    )
    df["price_cross_below_cloud2"] = (close < df["cloud2_bottom"].values) & (
        np.roll(close, 1) >= np.roll(df["cloud2_bottom"].values, 1)
    )
    df.iloc[0, df.columns.get_loc("price_cross_above_cloud2")] = False
    df.iloc[0, df.columns.get_loc("price_cross_below_cloud2")] = False

    # EMA cross-detection: True only on the bar the cross occurs
    c2_bull = df["cloud2_bull"].values.astype(bool)
    c3_bull = df["cloud3_bull"].values.astype(bool)
    c4_bull = df["cloud4_bull"].values.astype(bool)

    c2_bull_prev = np.roll(c2_bull, 1)
    c3_bull_prev = np.roll(c3_bull, 1)

    # cloud2_cross_bull: EMA5 crosses above EMA12
    cloud2_cross_bull  = c2_bull & ~c2_bull_prev
    cloud2_cross_bear  = ~c2_bull & c2_bull_prev
    # cloud3_cross_bull: EMA34 crosses above EMA50
    cloud3_cross_bull  = c3_bull & ~c3_bull_prev
    cloud3_cross_bear  = ~c3_bull & c3_bull_prev

    # Fix bar 0 (roll wraps last bar onto first)
    cloud2_cross_bull[0] = False
    cloud2_cross_bear[0] = False
    cloud3_cross_bull[0] = False
    cloud3_cross_bear[0] = False

    df["cloud2_cross_bull"]   = cloud2_cross_bull
    df["cloud2_cross_bear"]   = cloud2_cross_bear
    df["cloud3_cross_bull"]   = cloud3_cross_bull
    df["cloud3_cross_bear"]   = cloud3_cross_bear

    # Phase 3 activation: Cloud 3 AND Cloud 4 both aligned
    df["phase3_active_long"]  = c3_bull & c4_bull
    df["phase3_active_short"] = ~c3_bull & ~c4_bull

    return df
