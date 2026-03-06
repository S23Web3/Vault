"""
Four Pillars v3.9.1 signal pipeline.

Changes from four_pillars_v390.py:
- Uses compute_clouds_v391() which adds EMA cross-detection columns:
    cloud2_cross_bull, cloud2_cross_bear
    cloud3_cross_bull, cloud3_cross_bear
    phase3_active_long, phase3_active_short
  These columns are consumed by backtester_v391 for the 3-phase SL
  movement system and Cloud 2 hard-close exit logic.
- State machine unchanged (state_machine_v390 reused as-is).
- Stochastic ADD signal arrays computed here for backtester_v391:
    add_long_signal, add_short_signal
  True on the bar stoch9 exits overbought/oversold while 40/60 confirm.
"""

import numpy as np
import pandas as pd

from .stochastics import compute_all_stochastics
from .clouds_v391 import compute_clouds_v391
from .bbwp import calculate_bbwp
from .state_machine_v390 import FourPillarsStateMachine390


def compute_signals_v391(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Run the full Four Pillars v3.9.1 signal pipeline on OHLCV data.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol]
        params: Strategy parameters. See defaults below.

    Returns:
        DataFrame with all indicator and signal columns added.
        Key new columns vs v390:
          cloud2_cross_bull, cloud2_cross_bear  - EMA 5/12 cross bars
          cloud3_cross_bull, cloud3_cross_bear  - EMA 34/50 cross bars
          phase3_active_long, phase3_active_short - Phase 3 activation
          add_long_signal, add_short_signal     - Stoch-based ADD triggers
    """
    if params is None:
        params = {}

    # Step 1: stochastic indicators
    df = compute_all_stochastics(df, params)

    # Step 2: Ripster EMA clouds v391 (includes Cloud 4 + cross-detection)
    df = compute_clouds_v391(df, params)

    # Step 3: BBW volatility context (non-fatal)
    try:
        df = calculate_bbwp(df, params)
    except Exception as e:
        import warnings
        warnings.warn("BBW calculation failed, skipping: " + str(e), stacklevel=2)

    # Step 4: ATR — Wilder RMA matching Pine ta.atr(14)
    atr_len = params.get("atr_length", 14)
    tr = np.maximum(
        df["high"].values - df["low"].values,
        np.maximum(
            np.abs(df["high"].values - np.roll(df["close"].values, 1)),
            np.abs(df["low"].values  - np.roll(df["close"].values, 1))
        )
    )
    tr[0] = df["high"].iloc[0] - df["low"].iloc[0]
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    df["atr"] = atr

    # Step 5: Bar-by-bar state machine — A and B signals (unchanged from v390)
    sm = FourPillarsStateMachine390(
        cross_level      = params.get("cross_level",      25),
        zone_level       = params.get("zone_level",       30),
        stage_lookback   = params.get("stage_lookback",   10),
        allow_b          = params.get("allow_b_trades",   True),
        b_open_fresh     = params.get("b_open_fresh",     True),
        cloud2_reentry   = params.get("cloud2_reentry",   True),
        reentry_lookback = params.get("reentry_lookback", 10),
        use_ripster      = params.get("use_ripster",      False),
        use_60d          = params.get("use_60d",          False),
    )

    n = len(df)
    signals = {
        "long_a":        np.zeros(n, dtype=bool),
        "long_b":        np.zeros(n, dtype=bool),
        "long_c":        np.zeros(n, dtype=bool),  # zero — engine labels C
        "short_a":       np.zeros(n, dtype=bool),
        "short_b":       np.zeros(n, dtype=bool),
        "short_c":       np.zeros(n, dtype=bool),  # zero
        "reentry_long":  np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
    }

    stoch_9    = df["stoch_9"].values
    stoch_14   = df["stoch_14"].values
    stoch_40   = df["stoch_40"].values
    stoch_60   = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    price_pos  = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue
        result = sm.process_bar(
            bar_index                = i,
            stoch_9                  = stoch_9[i],
            stoch_14                 = stoch_14[i],
            stoch_40                 = stoch_40[i],
            stoch_60                 = stoch_60[i],
            stoch_60_d               = stoch_60_d[i],
            price_pos                = int(price_pos[i]),
            price_cross_above_cloud2 = bool(cross_above[i]),
            price_cross_below_cloud2 = bool(cross_below[i]),
        )
        signals["long_a"][i]        = result.long_a
        signals["long_b"][i]        = result.long_b
        signals["short_a"][i]       = result.short_a
        signals["short_b"][i]       = result.short_b
        signals["reentry_long"][i]  = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short

    for col, arr in signals.items():
        df[col] = arr

    # Step 6: Stochastic ADD signal detection
    # LONG ADD: stoch9 was > add_ob (overbought) and now crosses back below it,
    #   while stoch40 >= add_bull_min AND stoch60 >= add_bull_min
    # SHORT ADD: stoch9 was < add_os (oversold) and now crosses back above it,
    #   while stoch40 <= add_bear_max AND stoch60 <= add_bear_max
    add_ob       = params.get("add_ob",       70)    # overbought level for stoch9
    add_os       = params.get("add_os",       30)    # oversold level for stoch9
    add_bull_min = params.get("add_bull_min", 48)    # stoch40/60 must be >= this for long add
    add_bear_max = params.get("add_bear_max", 52)    # stoch40/60 must be <= this for short add

    add_long  = np.zeros(n, dtype=bool)
    add_short = np.zeros(n, dtype=bool)

    for i in range(1, n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_40[i]) or np.isnan(stoch_60[i]):
            continue
        # Long ADD: stoch9 was above add_ob, now exits (crosses below add_ob)
        if stoch_9[i - 1] >= add_ob and stoch_9[i] < add_ob:
            if stoch_40[i] >= add_bull_min and stoch_60[i] >= add_bull_min:
                add_long[i] = True
        # Short ADD: stoch9 was below add_os, now exits (crosses above add_os)
        if stoch_9[i - 1] <= add_os and stoch_9[i] > add_os:
            if stoch_40[i] <= add_bear_max and stoch_60[i] <= add_bear_max:
                add_short[i] = True

    df["add_long_signal"]  = add_long
    df["add_short_signal"] = add_short

    return df
