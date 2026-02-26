"""
Unified indicator calculation for the Four Pillars strategy.
Wraps signals.stochastics, signals.clouds, and ATR into a single call.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from signals.stochastics import compute_all_stochastics
from signals.clouds import compute_clouds


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ATR using Wilder's RMA (matches Pine Script ta.atr).

    Args:
        df: DataFrame with high, low, close columns.
        period: ATR lookback period.

    Returns:
        Series with ATR values.
    """
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values

    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - np.roll(close, 1)),
            np.abs(low - np.roll(close, 1)),
        ),
    )
    tr[0] = high[0] - low[0]

    atr = np.full(len(tr), np.nan)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, len(tr)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return pd.Series(atr, index=df.index, name="atr")


def calculate_stochastics(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute all 4 stochastics (9-3, 14-3, 40-3, 60-10)."""
    return compute_all_stochastics(df, params)


def calculate_ripster_clouds(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute Ripster EMA Clouds 2-5."""
    return compute_clouds(df, params)


def calculate_cloud3_bias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Cloud 3 directional bias.

    Adds columns:
        price_pos: -1 (below), 0 (inside), 1 (above) Cloud 3
        cloud3_allows_long: True if price_pos >= 0
        cloud3_allows_short: True if price_pos <= 0
    """
    df = df.copy()
    close = df["close"].values

    if "cloud3_top" not in df.columns:
        df = calculate_ripster_clouds(df)

    top = df["cloud3_top"].values
    bot = df["cloud3_bottom"].values

    df["price_pos"] = np.where(close > top, 1, np.where(close < bot, -1, 0))
    df["cloud3_allows_long"] = df["price_pos"] >= 0
    df["cloud3_allows_short"] = df["price_pos"] <= 0

    return df


def calculate_volume_analysis(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Compute volume analysis metrics.

    Adds columns:
        volume_ratio: current volume / rolling average
        volume_surge: True if volume_ratio > 2.0
    """
    df = df.copy()
    vol_col = "base_vol" if "base_vol" in df.columns else "volume"
    if vol_col not in df.columns:
        df["volume_ratio"] = 1.0
        df["volume_surge"] = False
        return df

    vol = df[vol_col]
    avg = vol.rolling(lookback, min_periods=1).mean()
    df["volume_ratio"] = np.where(avg > 0, vol / avg, 1.0)
    df["volume_surge"] = df["volume_ratio"] > 2.0
    return df


def calculate_all_indicators(df: pd.DataFrame, atr_period: int = 14, params: dict = None) -> pd.DataFrame:
    """
    Run all indicator calculations in sequence.

    Args:
        df: DataFrame with OHLCV columns.
        atr_period: ATR lookback period.
        params: Optional dict for stochastic/cloud overrides.

    Returns:
        DataFrame with all indicator columns added.
    """
    df = calculate_stochastics(df, params)
    df = calculate_ripster_clouds(df, params)
    df["atr"] = calculate_atr(df, atr_period)
    df = calculate_cloud3_bias(df)
    df = calculate_volume_analysis(df)
    return df


if __name__ == "__main__":
    n = 200
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame({
        "open": close - 0.1,
        "high": close + np.abs(np.random.randn(n)) * 0.5,
        "low": close - np.abs(np.random.randn(n)) * 0.5,
        "close": close,
        "base_vol": np.random.randint(1000, 5000, n).astype(float),
    })
    result = calculate_all_indicators(df)
    expected = ["stoch_9", "stoch_14", "stoch_40", "stoch_60", "atr", "cloud3_top",
                "price_pos", "cloud3_allows_long", "volume_ratio"]
    missing = [c for c in expected if c not in result.columns]
    if missing:
        print(f"FAIL -- missing columns: {missing}")
    else:
        print(f"PASS -- {len(result.columns)} columns, {len(result)} rows")
