# Qwen Task 2: Four Pillars Strategy Components

**Priority**: 🔴 CRITICAL (needed for first backtest)
**Files**: 4 Python files (~1,050 lines)
**Estimated Time**: 6-8 hours

---

## Task Overview

Generate the Four Pillars v3.8 trading strategy implementation in 4 separate Python files.

---

## File 1: Indicator Calculations (indicators.py)

**Lines**: ~300

```python
"""
vince/strategies/indicators.py

Calculate all Four Pillars technical indicators using ta-lib and pandas.

Requirements:
- 4 Stochastic oscillators with Raw K (K smooth=1)
- 5 Ripster EMA clouds
- ATR with configurable period
- Cloud 3 directional bias
- Volume analysis

All calculations must be vectorized (pandas/numpy, no loops).
Include comprehensive error handling.
"""

#!/usr/bin/env python3
from typing import Optional
import pandas as pd
import numpy as np
import talib as ta

def calculate_stochastics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 4 stochastic oscillators (John Kurisko settings).

    Stoch 9-3: K=9, smooth=1 (Raw K), D=3
    Stoch 14-3: K=14, smooth=1 (Raw K), D=3
    Stoch 40-3: K=40, smooth=1 (Raw K), D=3
    Stoch 60-10: K=60, smooth=1 (Raw K), D=10

    Args:
        df: DataFrame with columns [high, low, close]

    Returns:
        df with added columns: stoch_9_k, stoch_14_k, stoch_40_k, stoch_60_k, stoch_60_d

    Example:
        >>> df = calculate_stochastics(df)
        >>> print(df[['stoch_9_k', 'stoch_14_k']].head())
    """
    try:
        # Validate inputs
        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Stoch 9-3 (K=9, smooth=1, D=3)
        stoch_9_k, stoch_9_d = ta.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=9,
            slowk_period=1,  # Raw K (no smoothing)
            slowk_matype=0,  # SMA
            slowd_period=3,
            slowd_matype=0
        )
        df['stoch_9_k'] = stoch_9_k
        df['stoch_9_d'] = stoch_9_d

        # Stoch 14-3 (K=14, smooth=1, D=3)
        stoch_14_k, stoch_14_d = ta.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=14,
            slowk_period=1,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0
        )
        df['stoch_14_k'] = stoch_14_k
        df['stoch_14_d'] = stoch_14_d

        # Stoch 40-3 (K=40, smooth=1, D=3)
        stoch_40_k, stoch_40_d = ta.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=40,
            slowk_period=1,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0
        )
        df['stoch_40_k'] = stoch_40_k
        df['stoch_40_d'] = stoch_40_d

        # Stoch 60-10 (K=60, smooth=1, D=10)
        stoch_60_k, stoch_60_d = ta.STOCH(
            df['high'], df['low'], df['close'],
            fastk_period=60,
            slowk_period=1,
            slowk_matype=0,
            slowd_period=10,
            slowd_matype=0
        )
        df['stoch_60_k'] = stoch_60_k
        df['stoch_60_d'] = stoch_60_d

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to calculate stochastics: {e}")


def calculate_ripster_clouds(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Ripster EMA clouds (Cloud 2-5, skip Cloud 1).

    Cloud 2: EMA 5/12
    Cloud 3: EMA 34/50
    Cloud 4: EMA 72/89
    Cloud 5: EMA 180/200

    Args:
        df: DataFrame with column [close]

    Returns:
        df with added columns: ema5, ema12, ema34, ema50, ema72, ema89, ema180, ema200,
                               cloud2_top, cloud2_bot, cloud3_top, cloud3_bot,
                               cloud4_top, cloud4_bot, cloud5_top, cloud5_bot
    """
    try:
        if 'close' not in df.columns:
            raise ValueError("Missing required column: close")

        # Calculate all EMAs
        df['ema5'] = ta.EMA(df['close'], timeperiod=5)
        df['ema12'] = ta.EMA(df['close'], timeperiod=12)
        df['ema34'] = ta.EMA(df['close'], timeperiod=34)
        df['ema50'] = ta.EMA(df['close'], timeperiod=50)
        df['ema72'] = ta.EMA(df['close'], timeperiod=72)
        df['ema89'] = ta.EMA(df['close'], timeperiod=89)
        df['ema180'] = ta.EMA(df['close'], timeperiod=180)
        df['ema200'] = ta.EMA(df['close'], timeperiod=200)

        # Cloud 2 (5/12)
        df['cloud2_top'] = df[['ema5', 'ema12']].max(axis=1)
        df['cloud2_bot'] = df[['ema5', 'ema12']].min(axis=1)

        # Cloud 3 (34/50)
        df['cloud3_top'] = df[['ema34', 'ema50']].max(axis=1)
        df['cloud3_bot'] = df[['ema34', 'ema50']].min(axis=1)

        # Cloud 4 (72/89)
        df['cloud4_top'] = df[['ema72', 'ema89']].max(axis=1)
        df['cloud4_bot'] = df[['ema72', 'ema89']].min(axis=1)

        # Cloud 5 (180/200)
        df['cloud5_top'] = df[['ema180', 'ema200']].max(axis=1)
        df['cloud5_bot'] = df[['ema180', 'ema200']].min(axis=1)

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to calculate Ripster clouds: {e}")


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate ATR (Average True Range) with configurable period.

    Args:
        df: DataFrame with columns [high, low, close]
        period: ATR period (8, 13, 14, or 21)

    Returns:
        df with added column: atr
    """
    try:
        if period not in [8, 13, 14, 21]:
            raise ValueError(f"ATR period must be 8, 13, 14, or 21, got {period}")

        required_cols = ['high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        df['atr'] = ta.ATR(df['high'], df['low'], df['close'], timeperiod=period)

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to calculate ATR: {e}")


def calculate_cloud3_bias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cloud 3 directional bias.

    price_pos = -1 if price below cloud (bearish)
    price_pos = 0 if price inside cloud (neutral)
    price_pos = 1 if price above cloud (bullish)

    Args:
        df: DataFrame with columns [close, cloud3_top, cloud3_bot]

    Returns:
        df with added columns: price_pos, cloud3_allows_long, cloud3_allows_short
    """
    try:
        required_cols = ['close', 'cloud3_top', 'cloud3_bot']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Initialize price_pos
        df['price_pos'] = 0

        # Above cloud = bullish (1)
        df.loc[df['close'] > df['cloud3_top'], 'price_pos'] = 1

        # Below cloud = bearish (-1)
        df.loc[df['close'] < df['cloud3_bot'], 'price_pos'] = -1

        # Inside cloud stays 0

        # Directional filters
        df['cloud3_allows_long'] = (df['price_pos'] >= 0)
        df['cloud3_allows_short'] = (df['price_pos'] <= 0)

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to calculate Cloud 3 bias: {e}")


def calculate_volume_analysis(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Calculate volume ratios vs moving average.

    Args:
        df: DataFrame with columns [base_vol, quote_vol]
        period: SMA period for volume average

    Returns:
        df with added columns: volume_ratio, volume_surge
    """
    try:
        if 'base_vol' not in df.columns:
            raise ValueError("Missing required column: base_vol")

        # Volume ratio vs SMA
        volume_sma = df['base_vol'].rolling(window=period).mean()
        df['volume_ratio'] = df['base_vol'] / volume_sma

        # Volume surge (>2x average)
        df['volume_surge'] = (df['volume_ratio'] > 2.0).astype(int)

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to calculate volume analysis: {e}")


def calculate_all_indicators(df: pd.DataFrame, atr_period: int = 14) -> pd.DataFrame:
    """
    Calculate all Four Pillars indicators in one pass.

    Args:
        df: DataFrame with OHLCV columns [timestamp, open, high, low, close, base_vol, quote_vol]
        atr_period: ATR period (8, 13, 14, or 21)

    Returns:
        df with all indicator columns added

    Example:
        >>> df = pd.read_parquet("data/cache/BTCUSDT_5m.parquet")
        >>> df = calculate_all_indicators(df, atr_period=14)
        >>> print(df.columns)
    """
    try:
        # Calculate in order (dependencies)
        df = calculate_stochastics(df)
        df = calculate_ripster_clouds(df)
        df = calculate_atr(df, period=atr_period)
        df = calculate_cloud3_bias(df)
        df = calculate_volume_analysis(df)

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to calculate all indicators: {e}")


if __name__ == "__main__":
    # Test with dummy data
    try:
        print("Testing indicator calculations...")

        # Create sample OHLCV data
        dates = pd.date_range('2024-01-01', periods=200, freq='5min')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(100, 110, 200),
            'high': np.random.uniform(110, 115, 200),
            'low': np.random.uniform(95, 100, 200),
            'close': np.random.uniform(100, 110, 200),
            'base_vol': np.random.uniform(1000, 5000, 200),
            'quote_vol': np.random.uniform(100000, 500000, 200),
        })

        # Calculate all indicators
        df = calculate_all_indicators(df, atr_period=14)

        # Verify columns exist
        expected_cols = ['stoch_9_k', 'stoch_14_k', 'stoch_40_k', 'stoch_60_k',
                        'ema34', 'ema50', 'cloud3_top', 'cloud3_bot',
                        'atr', 'price_pos', 'cloud3_allows_long', 'volume_ratio']

        for col in expected_cols:
            assert col in df.columns, f"Missing column: {col}"

        print(f"✓ All indicators calculated successfully")
        print(f"✓ Output shape: {df.shape}")
        print(f"✓ Sample row:\n{df[expected_cols].iloc[-1]}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

# Generate this complete file with all imports, type hints, error handling, and tests.
```

---

## File 2: Signal Generation (signals.py)

**Lines**: ~250

Generate a complete Python file that implements the Four Pillars A/B/C signal state machine.

**Requirements**:
- A signal: 4/4 stochs aligned + Cloud 3 filter
- B signal: 3/4 stochs aligned + Cloud 3 filter
- C signal: 2/4 stochs aligned + Cloud 3 filter + inside Cloud 3
- Cooldown: minimum 3 bars between signals
- Direction flip: cancel opposite signals when new signal fires
- Return DataFrame with columns: signal_type, direction, action, bars_since_last

**Use the same structure**: imports, type hints, docstrings, error handling, test case at bottom.

---

## File 3: Cloud Filter (cloud_filter.py)

**Lines**: ~100

Generate a simplified Cloud 3 directional filter module.

**Requirements**:
- Single function: `apply_cloud3_filter(df, signals_df)`
- Block opposite-direction signals when Cloud 3 doesn't allow
- Return filtered signals DataFrame

---

## File 4: Four Pillars Strategy Class (four_pillars_v3_8.py)

**Lines**: ~400

Generate complete strategy class inheriting from BaseStrategy (from overnight task).

**Requirements**:
- Implements calculate_indicators() using indicators.py
- Implements generate_signals() using signals.py + cloud_filter.py
- Implements get_sl_tp() returning (1.0 ATR SL, 1.5 ATR TP)
- Config parameters: atr_period, sl_atr_mult, tp_atr_mult, allow_b_fresh, cooldown_bars
- Commission: $8/side

---

## Output Format

For each file, generate:
1. Complete Python file with all imports
2. Type hints for all functions/methods
3. Comprehensive docstrings (Google style)
4. Try/except error handling for all operations
5. Test case at bottom (if __name__ == "__main__")

## CRITICAL Requirements

- Use only these dependencies: pandas, numpy, ta-lib, typing
- All calculations must be vectorized (no for loops over rows)
- Every function must validate inputs
- Every function must handle errors gracefully
- Code must run without errors on first try

---

**Paste this entire prompt to Qwen after overnight task completes.**
