"""
Strategy-agnostic feature extraction from trade data + OHLCV bars.

Computes per-trade features at entry time:
  - Stochastic values (9/14/40/60 K lines)
  - ATR normalized by price
  - Cloud distances (EMA spread as % of price)
  - Volume ratio (current vs rolling average)
  - R-multiple normalization (MFE_R, MAE_R)
  - Temporal features (hour of day, day of week)

Input: trades DataFrame + OHLCV DataFrame with signal columns.
Output: feature matrix (DataFrame) aligned to trades.
"""

import numpy as np
import pandas as pd


def extract_trade_features(trades_df: pd.DataFrame,
                           ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix for each trade using bar data at entry time.

    Args:
        trades_df: DataFrame from backtester (needs entry_bar, entry_price,
                   sl_price, tp_price, mfe, mae, pnl, commission, direction,
                   grade, exit_reason columns).
        ohlcv_df: OHLCV DataFrame with signal columns (stoch_9_3_k,
                  stoch_14_3_k, stoch_40_3_k, stoch_60_10_k, atr, close,
                  base_vol, cloud3_bull, price_pos, ema34, ema50, etc).

    Returns:
        DataFrame with one row per trade, columns are features.
    """
    features = []

    # Pre-extract arrays for speed
    close = ohlcv_df["close"].values
    atr = ohlcv_df["atr"].values if "atr" in ohlcv_df.columns else None
    n_bars = len(ohlcv_df)

    # Optional columns -- extract if present, else None
    stoch_9 = ohlcv_df["stoch_9"].values if "stoch_9" in ohlcv_df.columns else None
    stoch_14 = ohlcv_df["stoch_14"].values if "stoch_14" in ohlcv_df.columns else None
    stoch_40 = ohlcv_df["stoch_40"].values if "stoch_40" in ohlcv_df.columns else None
    stoch_60 = ohlcv_df["stoch_60"].values if "stoch_60" in ohlcv_df.columns else None
    volume = ohlcv_df["base_vol"].values if "base_vol" in ohlcv_df.columns else None
    cloud3_bull = ohlcv_df["cloud3_bull"].values if "cloud3_bull" in ohlcv_df.columns else None
    price_pos = ohlcv_df["price_pos"].values if "price_pos" in ohlcv_df.columns else None
    ema34 = ohlcv_df["ema34"].values if "ema34" in ohlcv_df.columns else None
    ema50 = ohlcv_df["ema50"].values if "ema50" in ohlcv_df.columns else None

    # Datetime for temporal features
    has_datetime = False
    if "datetime" in ohlcv_df.columns:
        dt_series = pd.to_datetime(ohlcv_df["datetime"])
        has_datetime = True
    elif isinstance(ohlcv_df.index, pd.DatetimeIndex):
        dt_series = ohlcv_df.index
        has_datetime = True

    # Rolling volume average (20-bar)
    vol_ma20 = None
    if volume is not None:
        vol_series = pd.Series(volume)
        vol_ma20 = vol_series.rolling(20, min_periods=1).mean().values

    for _, trade in trades_df.iterrows():
        i = int(trade["entry_bar"])

        # Guard against out-of-bounds
        if i < 0 or i >= n_bars:
            continue

        row = {}

        # -- Direction and grade encoded --
        row["direction_enc"] = 1 if trade["direction"] == "LONG" else -1
        row["grade_enc"] = {"A": 3, "B": 2, "C": 1, "R": 0}.get(trade["grade"], 0)

        # -- Stochastic values at entry --
        if stoch_9 is not None:
            row["stoch_9"] = stoch_9[i] if not np.isnan(stoch_9[i]) else 50.0
        if stoch_14 is not None:
            row["stoch_14"] = stoch_14[i] if not np.isnan(stoch_14[i]) else 50.0
        if stoch_40 is not None:
            row["stoch_40"] = stoch_40[i] if not np.isnan(stoch_40[i]) else 50.0
        if stoch_60 is not None:
            row["stoch_60"] = stoch_60[i] if not np.isnan(stoch_60[i]) else 50.0

        # -- ATR normalized by price (volatility proxy) --
        if atr is not None and not np.isnan(atr[i]) and close[i] > 0:
            row["atr_pct"] = atr[i] / close[i]
        else:
            row["atr_pct"] = 0.0

        # -- Volume ratio: current bar vs 20-bar average --
        if volume is not None and vol_ma20 is not None and vol_ma20[i] > 0:
            row["vol_ratio"] = volume[i] / vol_ma20[i]
        else:
            row["vol_ratio"] = 1.0

        # -- Cloud 3 state at entry --
        if cloud3_bull is not None:
            row["cloud3_bull"] = int(cloud3_bull[i]) if not np.isnan(cloud3_bull[i]) else 0
        if price_pos is not None:
            row["price_pos"] = int(price_pos[i]) if not np.isnan(price_pos[i]) else 0

        # -- Cloud 3 distance: (ema34 - ema50) / price --
        if ema34 is not None and ema50 is not None and close[i] > 0:
            if not np.isnan(ema34[i]) and not np.isnan(ema50[i]):
                row["cloud3_spread"] = (ema34[i] - ema50[i]) / close[i]
            else:
                row["cloud3_spread"] = 0.0

        # -- R-multiple normalization --
        # R = SL distance from entry
        sl_dist = abs(trade["entry_price"] - trade["sl_price"])
        if sl_dist > 0:
            row["mfe_r"] = trade["mfe"] / sl_dist if sl_dist > 0 else 0.0
            row["mae_r"] = trade["mae"] / sl_dist if sl_dist > 0 else 0.0
            net_pnl = trade["pnl"] - trade["commission"]
            row["pnl_r"] = net_pnl / sl_dist
        else:
            row["mfe_r"] = 0.0
            row["mae_r"] = 0.0
            row["pnl_r"] = 0.0

        # -- Temporal features --
        if has_datetime and i < len(dt_series):
            dt = dt_series.iloc[i]
            row["hour"] = dt.hour
            row["day_of_week"] = dt.dayofweek
        else:
            row["hour"] = 0
            row["day_of_week"] = 0

        # -- ETD: end trade drawdown = MFE - actual profit --
        net_pnl = trade["pnl"] - trade["commission"]
        row["etd"] = trade["mfe"] - max(net_pnl, 0)

        # -- Trade duration in bars --
        row["duration_bars"] = int(trade["exit_bar"] - trade["entry_bar"])

        features.append(row)

    return pd.DataFrame(features)


def get_feature_columns() -> list:
    """
    Return the list of feature column names used for ML training.
    Excludes target/label columns (mfe_r, mae_r, pnl_r, etd) which are
    derived from trade outcome and would leak future info.
    """
    return [
        "direction_enc", "grade_enc",
        "stoch_9", "stoch_14", "stoch_40", "stoch_60",
        "atr_pct", "vol_ratio",
        "cloud3_bull", "price_pos", "cloud3_spread",
        "hour", "day_of_week",
    ]
