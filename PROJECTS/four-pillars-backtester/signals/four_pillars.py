"""
Orchestrator: compute indicators → run state machine → output signal DataFrame.
"""

import numpy as np
import pandas as pd

from .stochastics import compute_all_stochastics
from .clouds import compute_clouds
from .state_machine import FourPillarsStateMachine, SignalResult


def compute_signals(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Run the full Four Pillars signal pipeline on OHLCV data.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol]
        params: Strategy parameters (defaults to v3.7.1 settings)

    Returns:
        DataFrame with all indicator and signal columns added.
    """
    if params is None:
        params = {}

    # Compute indicators (pass params through for adjustable K lengths / EMA lengths)
    df = compute_all_stochastics(df, params)
    df = compute_clouds(df, params)

    # ATR (manual, matching Pine Script ta.atr(14))
    atr_len = params.get("atr_length", 14)
    tr = np.maximum(
        df["high"].values - df["low"].values,
        np.maximum(
            np.abs(df["high"].values - np.roll(df["close"].values, 1)),
            np.abs(df["low"].values - np.roll(df["close"].values, 1))
        )
    )
    tr[0] = df["high"].iloc[0] - df["low"].iloc[0]  # First bar: just H-L
    # RMA (Wilder's smoothing) for ATR
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    df["atr"] = atr

    # Initialize state machine
    sm = FourPillarsStateMachine(
        cross_level=params.get("cross_level", 25),
        zone_level=params.get("zone_level", 30),
        stage_lookback=params.get("stage_lookback", 10),
        allow_b=params.get("allow_b_trades", True),
        allow_c=params.get("allow_c_trades", True),
        b_open_fresh=params.get("b_open_fresh", True),
        cloud2_reentry=params.get("cloud2_reentry", True),
        reentry_lookback=params.get("reentry_lookback", 10),
        use_ripster=params.get("use_ripster", False),
        use_60d=params.get("use_60d", False),
    )

    # Run bar-by-bar
    n = len(df)
    signals = {
        "long_a": np.zeros(n, dtype=bool),
        "long_b": np.zeros(n, dtype=bool),
        "long_c": np.zeros(n, dtype=bool),
        "short_a": np.zeros(n, dtype=bool),
        "short_b": np.zeros(n, dtype=bool),
        "short_c": np.zeros(n, dtype=bool),
        "reentry_long": np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
    }

    stoch_9 = df["stoch_9"].values
    stoch_14 = df["stoch_14"].values
    stoch_40 = df["stoch_40"].values
    stoch_60 = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    cloud3_bull = df["cloud3_bull"].values
    price_pos = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        # Skip bars where indicators aren't ready
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue

        result = sm.process_bar(
            bar_index=i,
            stoch_9=stoch_9[i],
            stoch_14=stoch_14[i],
            stoch_40=stoch_40[i],
            stoch_60=stoch_60[i],
            stoch_60_d=stoch_60_d[i],
            cloud3_bull=bool(cloud3_bull[i]),
            price_pos=int(price_pos[i]),
            price_cross_above_cloud2=bool(cross_above[i]),
            price_cross_below_cloud2=bool(cross_below[i]),
        )

        signals["long_a"][i] = result.long_a
        signals["long_b"][i] = result.long_b
        signals["long_c"][i] = result.long_c
        signals["short_a"][i] = result.short_a
        signals["short_b"][i] = result.short_b
        signals["short_c"][i] = result.short_c
        signals["reentry_long"][i] = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short

    for col, arr in signals.items():
        df[col] = arr

    return df
