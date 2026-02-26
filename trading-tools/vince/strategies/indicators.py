# vince/strategies/indicators.py
"""
Four Pillars indicator calculations.

Implements:
- Raw K Stochastics (9-3, 14-3, 40-3, 60-10)
- Ripster EMA Clouds (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89)
- ATR calculation
- Cloud 3 directional filter (price position vs Cloud 3)

All calculations match Pine Script v3.8 exactly.
"""

import pandas as pd
import numpy as np
from typing import Tuple

def stoch_k(df: pd.DataFrame, period: int, source_high: str = 'high',
            source_low: str = 'low', source_close: str = 'close') -> pd.Series:
    """
    Calculate Raw K Stochastic (K smoothing = 1, no D line).

    Args:
        df: DataFrame with OHLC data
        period: K period (e.g., 9, 14, 40, 60)
        source_high: Column name for high prices
        source_low: Column name for low prices
        source_close: Column name for close prices

    Returns:
        Series with stochastic K values (0-100)

    Example:
        >>> stoch_9_3 = stoch_k(df, period=9)
        >>> stoch_14_3 = stoch_k(df, period=14)
    """
    high = df[source_high]
    low = df[source_low]
    close = df[source_close]

    # Calculate the lowest low and highest high over the period
    lowest_low = low.rolling(window=period, min_periods=1).min()
    highest_high = high.rolling(window=period, min_periods=1).max()

    # Calculate the stochastic K
    stoch_k_values = 100 * (close - lowest_low) / (highest_high - lowest_low)

    # Handle division by zero - return 50.0 when denominator is 0
    stoch_k_values = stoch_k_values.fillna(50.0)

    return stoch_k_values


def calculate_ripster_clouds(df: pd.DataFrame,
                              ema5: int = 5, ema12: int = 12,
                              ema34: int = 34, ema50: int = 50,
                              ema72: int = 72, ema89: int = 89) -> pd.DataFrame:
    """
    Calculate Ripster EMA clouds and price position.

    Adds columns:
    - ema5, ema12, cloud2_bull, cloud2_top, cloud2_bottom
    - ema34, ema50, cloud3_bull, cloud3_top, cloud3_bottom
    - ema72, ema89, cloud4_bull
    - price_pos: -1 (below Cloud 3), 0 (inside), 1 (above)
    - cloud3_allows_long: True if price_pos >= 0
    - cloud3_allows_short: True if price_pos <= 0

    Args:
        df: DataFrame with 'close' column (modified in-place)
        ema5-ema89: EMA periods

    Returns:
        Modified DataFrame with new columns
    """
    # Calculate all EMAs
    df['ema5'] = df['close'].ewm(span=ema5, adjust=False).mean()
    df['ema12'] = df['close'].ewm(span=ema12, adjust=False).mean()
    df['ema34'] = df['close'].ewm(span=ema34, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=ema50, adjust=False).mean()
    df['ema72'] = df['close'].ewm(span=ema72, adjust=False).mean()
    df['ema89'] = df['close'].ewm(span=ema89, adjust=False).mean()

    # Calculate cloud tops and bottoms for Cloud 2 (5/12)
    df['cloud2_top'] = df[['ema5', 'ema12']].max(axis=1)
    df['cloud2_bottom'] = df[['ema5', 'ema12']].min(axis=1)
    df['cloud2_bull'] = df['ema5'] > df['ema12']

    # Calculate cloud tops and bottoms for Cloud 3 (34/50)
    df['cloud3_top'] = df[['ema34', 'ema50']].max(axis=1)
    df['cloud3_bottom'] = df[['ema34', 'ema50']].min(axis=1)
    df['cloud3_bull'] = df['ema34'] > df['ema50']

    # Calculate cloud tops and bottoms for Cloud 4 (72/89)
    df['cloud4_bull'] = df['ema72'] > df['ema89']

    # Calculate price position relative to Cloud 3
    # -1 = below Cloud 3, 0 = inside, 1 = above
    df['price_pos'] = np.where(df['close'] < df['cloud3_bottom'], -1,
                              np.where(df['close'] > df['cloud3_top'], 1, 0))

    # Directional filters
    df['cloud3_allows_long'] = df['price_pos'] >= 0
    df['cloud3_allows_short'] = df['price_pos'] <= 0

    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.

    Args:
        df: DataFrame with 'high', 'low', 'close'
        period: ATR period (default 14)

    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Calculate True Range components
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    # True Range is the maximum of the three
    tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)

    # Calculate ATR using EMA
    atr = tr.ewm(span=period, adjust=False).mean()

    return atr


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all Four Pillars indicators in one call.

    Adds columns for stochastics, EMAs, clouds, ATR, and directional filters.

    Args:
        df: DataFrame with OHLC data

    Returns:
        Modified DataFrame with all indicator columns

    Example:
        >>> df = pd.read_parquet('RIVERUSDT_5m.parquet')
        >>> df = calculate_all_indicators(df)
        >>> print(df.columns)  # Now has stoch_9_3, ema34, cloud3_bull, atr, etc.
    """
    # Calculate all 4 stochastics
    df['stoch_9_3'] = stoch_k(df, period=9)
    df['stoch_14_3'] = stoch_k(df, period=14)
    df['stoch_40_3'] = stoch_k(df, period=40)
    df['stoch_60_10'] = stoch_k(df, period=60)

    # Calculate Ripster clouds and directional filters
    df = calculate_ripster_clouds(df)

    # Calculate ATR
    df['atr'] = calculate_atr(df, period=14)

    return df
