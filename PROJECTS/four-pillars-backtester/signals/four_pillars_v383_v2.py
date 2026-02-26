"""
Signal pipeline for v3.8.3 — v2: uses Numba-compiled stochastics/clouds/ATR.
Imports stochastics_v2 and clouds_v2; extracts _rma_kernel via @njit.
"""
import numpy as np
import pandas as pd
from numba import njit

from .stochastics_v2 import compute_all_stochastics
from .clouds_v2 import compute_clouds
from .state_machine_v383 import FourPillarsStateMachine383


@njit(cache=True)
def _rma_kernel(tr, atr_len):
    """Wilder RMA loop for ATR calculation; Numba JIT-compiled via @njit(cache=True)."""
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    return atr


def compute_signals_v383(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Run the full Four Pillars v3.8.3 signal pipeline with Numba-accelerated kernels."""
    if params is None:
        params = {}

    df = compute_all_stochastics(df, params)
    df = compute_clouds(df, params)

    # ATR (RMA / Wilder's smoothing) — inner loop JIT-compiled via _rma_kernel
    atr_len = params.get("atr_length", 14)
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    prev_c = np.roll(c, 1)
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    tr[0] = h[0] - l[0]

    atr = _rma_kernel(tr, atr_len)
    df["atr"] = atr

    # v3.8.3 state machine
    sm = FourPillarsStateMachine383(
        cross_level=params.get("cross_level", 25),
        zone_level=params.get("zone_level", 30),
        stage_lookback=params.get("stage_lookback", 10),
        allow_b=params.get("allow_b_trades", True),
        allow_c=params.get("allow_c_trades", True),
        b_open_fresh=params.get("b_open_fresh", True),
        cloud2_reentry=params.get("cloud2_reentry", True),
        reentry_lookback=params.get("reentry_lookback", 10),
        use_60d=params.get("use_60d", False),
    )

    n = len(df)
    signals = {
        "long_a": np.zeros(n, dtype=bool),
        "long_b": np.zeros(n, dtype=bool),
        "long_c": np.zeros(n, dtype=bool),
        "long_d": np.zeros(n, dtype=bool),
        "short_a": np.zeros(n, dtype=bool),
        "short_b": np.zeros(n, dtype=bool),
        "short_c": np.zeros(n, dtype=bool),
        "short_d": np.zeros(n, dtype=bool),
        "reentry_long": np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
        "add_long": np.zeros(n, dtype=bool),
        "add_short": np.zeros(n, dtype=bool),
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
        signals["long_d"][i] = result.long_d
        signals["short_a"][i] = result.short_a
        signals["short_b"][i] = result.short_b
        signals["short_c"][i] = result.short_c
        signals["short_d"][i] = result.short_d
        signals["reentry_long"][i] = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short
        signals["add_long"][i] = result.add_long
        signals["add_short"][i] = result.add_short

    for col, arr in signals.items():
        df[col] = arr

    return df
