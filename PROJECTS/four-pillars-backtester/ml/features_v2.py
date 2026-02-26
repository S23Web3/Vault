"""
Strategy-agnostic feature extraction v2 — extends features.py with
12 new volume + market cap features (26 total).

New volume features (8):
  vol_ratio_5, vol_ratio_50, vol_ratio_200, vol_trend,
  vol_zscore, quote_vol_ratio, vol_price_corr, relative_spread

New market cap features (4):
  log_market_cap, log_daily_turnover, market_cap_rank, turnover_to_cap_ratio

Backward compatible: new params default to None, excluded by available_cols filter.
"""

import numpy as np
import pandas as pd
from typing import Optional


def extract_trade_features(trades_df: pd.DataFrame,
                           ohlcv_df: pd.DataFrame,
                           coin_metadata: Optional[dict] = None,
                           market_cap_history: Optional[pd.DataFrame] = None,
                           ) -> pd.DataFrame:
    """
    Build feature matrix for each trade using bar data at entry time.

    Args:
        trades_df: DataFrame from backtester (needs entry_bar, entry_price,
                   sl_price, tp_price, mfe, mae, pnl, commission, direction,
                   grade, exit_reason columns).
        ohlcv_df: OHLCV DataFrame with signal columns (stoch_9, stoch_14,
                  stoch_40, stoch_60, atr, close, base_vol, quote_vol,
                  cloud3_bull, price_pos, ema34, ema50, etc).
        coin_metadata: Optional dict with keys:
                       - market_cap: float (current market cap in USD)
                       - market_cap_rank: int (1-399 ordinal rank)
        market_cap_history: Optional DataFrame with columns [date, symbol, market_cap, total_volume].
                           Used for daily historical market cap at trade entry date.

    Returns:
        DataFrame with one row per trade, columns are features.
    """
    features = []

    # Pre-extract arrays for speed
    close = ohlcv_df["close"].values
    high = ohlcv_df["high"].values
    low = ohlcv_df["low"].values
    atr = ohlcv_df["atr"].values if "atr" in ohlcv_df.columns else None
    n_bars = len(ohlcv_df)

    # Optional columns
    stoch_9 = ohlcv_df["stoch_9"].values if "stoch_9" in ohlcv_df.columns else None
    stoch_14 = ohlcv_df["stoch_14"].values if "stoch_14" in ohlcv_df.columns else None
    stoch_40 = ohlcv_df["stoch_40"].values if "stoch_40" in ohlcv_df.columns else None
    stoch_60 = ohlcv_df["stoch_60"].values if "stoch_60" in ohlcv_df.columns else None
    volume = ohlcv_df["base_vol"].values if "base_vol" in ohlcv_df.columns else None
    quote_vol = ohlcv_df["quote_vol"].values if "quote_vol" in ohlcv_df.columns else None
    cloud3_bull = ohlcv_df["cloud3_bull"].values if "cloud3_bull" in ohlcv_df.columns else None
    price_pos = ohlcv_df["price_pos"].values if "price_pos" in ohlcv_df.columns else None
    ema34 = ohlcv_df["ema34"].values if "ema34" in ohlcv_df.columns else None
    ema50 = ohlcv_df["ema50"].values if "ema50" in ohlcv_df.columns else None

    # Datetime for temporal features
    has_datetime = False
    dt_series = None
    if "datetime" in ohlcv_df.columns:
        dt_series = pd.to_datetime(ohlcv_df["datetime"])
        has_datetime = True
    elif isinstance(ohlcv_df.index, pd.DatetimeIndex):
        dt_series = ohlcv_df.index
        has_datetime = True

    # ------------------------------------------------------------------
    # Pre-compute rolling volume arrays (vectorized, outside the loop)
    # ------------------------------------------------------------------
    vol_ma5 = vol_ma20 = vol_ma50 = vol_ma200 = None
    vol_std50 = vol_trend_arr = None
    if volume is not None:
        vol_series = pd.Series(volume)
        vol_ma5 = vol_series.rolling(5, min_periods=1).mean().values
        vol_ma20 = vol_series.rolling(20, min_periods=1).mean().values
        vol_ma50 = vol_series.rolling(50, min_periods=1).mean().values
        vol_ma200 = vol_series.rolling(200, min_periods=1).mean().values
        vol_std50 = vol_series.rolling(50, min_periods=1).std().values
        # Volume trend: slope approximation = (MA20 now - MA20 10 bars ago)
        vol_ma20_series = pd.Series(vol_ma20)
        vol_trend_arr = (vol_ma20_series - vol_ma20_series.shift(10)).values

    # Quote volume rolling (USDT turnover)
    qvol_ma20 = None
    if quote_vol is not None:
        qvol_series = pd.Series(quote_vol)
        qvol_ma20 = qvol_series.rolling(20, min_periods=1).mean().values

    # Volume-price correlation (rolling 20-bar)
    vol_price_corr_arr = None
    if volume is not None:
        price_change = pd.Series(close).pct_change().values
        vol_price_corr_arr = (
            pd.Series(volume).rolling(20, min_periods=5)
            .corr(pd.Series(price_change))
            .values
        )

    # Daily quote volume for turnover feature (resample to daily sum)
    daily_turnover_at_bar = None
    if quote_vol is not None and has_datetime:
        try:
            _tmp = pd.DataFrame({"datetime": dt_series, "quote_vol": quote_vol})
            _tmp = _tmp.set_index("datetime")
            daily_sum = _tmp["quote_vol"].resample("1D").sum()
            daily_sum = daily_sum.shift(1)  # Lag by 1 day to prevent look-ahead bias
            daily_ma20 = daily_sum.rolling(20, min_periods=1).mean()
            # Map back to each bar by date
            daily_turnover_at_bar = (
                _tmp.index.normalize().map(
                    lambda d: daily_ma20.get(d, np.nan) if d in daily_ma20.index else np.nan
                )
            )
            # Convert to numpy if possible
            if hasattr(daily_turnover_at_bar, 'values'):
                daily_turnover_at_bar = daily_turnover_at_bar.values
            else:
                daily_turnover_at_bar = np.array(list(daily_turnover_at_bar))
        except Exception:
            daily_turnover_at_bar = None

    # ------------------------------------------------------------------
    # Market cap history lookup
    # ------------------------------------------------------------------
    mcap_lookup = {}
    if market_cap_history is not None and len(market_cap_history) > 0:
        # Build dict: date_str -> {market_cap, total_volume}
        for _, row_mc in market_cap_history.iterrows():
            mcap_lookup[row_mc["date"]] = {
                "market_cap": row_mc.get("market_cap", 0),
                "total_volume": row_mc.get("total_volume", 0),
            }

    # ------------------------------------------------------------------
    # Per-trade feature extraction
    # ------------------------------------------------------------------
    for _, trade in trades_df.iterrows():
        i = int(trade["entry_bar"])
        if i < 0 or i >= n_bars:
            continue

        row = {}

        # --- Original features (14) ---

        row["direction_enc"] = 1 if trade["direction"] == "LONG" else -1
        row["grade_enc"] = {"A": 3, "B": 2, "C": 1, "R": 0}.get(trade["grade"], 0)

        if stoch_9 is not None:
            row["stoch_9"] = stoch_9[i] if not np.isnan(stoch_9[i]) else 50.0
        if stoch_14 is not None:
            row["stoch_14"] = stoch_14[i] if not np.isnan(stoch_14[i]) else 50.0
        if stoch_40 is not None:
            row["stoch_40"] = stoch_40[i] if not np.isnan(stoch_40[i]) else 50.0
        if stoch_60 is not None:
            row["stoch_60"] = stoch_60[i] if not np.isnan(stoch_60[i]) else 50.0

        if atr is not None and not np.isnan(atr[i]) and close[i] > 0:
            row["atr_pct"] = atr[i] / close[i]
        else:
            row["atr_pct"] = 0.0

        if volume is not None and vol_ma20 is not None and vol_ma20[i] > 0:
            row["vol_ratio"] = volume[i] / vol_ma20[i]
        else:
            row["vol_ratio"] = 1.0

        if cloud3_bull is not None:
            row["cloud3_bull"] = int(cloud3_bull[i]) if not np.isnan(cloud3_bull[i]) else 0
        if price_pos is not None:
            row["price_pos"] = int(price_pos[i]) if not np.isnan(price_pos[i]) else 0

        if ema34 is not None and ema50 is not None and close[i] > 0:
            if not np.isnan(ema34[i]) and not np.isnan(ema50[i]):
                row["cloud3_spread"] = (ema34[i] - ema50[i]) / close[i]
            else:
                row["cloud3_spread"] = 0.0

        sl_dist = abs(trade["entry_price"] - trade["sl_price"])
        if sl_dist > 0:
            row["mfe_r"] = trade["mfe"] / sl_dist
            row["mae_r"] = trade["mae"] / sl_dist
            net_pnl = trade["pnl"] - trade["commission"]
            row["pnl_r"] = net_pnl / sl_dist
        else:
            row["mfe_r"] = 0.0
            row["mae_r"] = 0.0
            row["pnl_r"] = 0.0

        if has_datetime and i < len(dt_series):
            dt = dt_series.iloc[i]
            row["hour"] = dt.hour
            row["day_of_week"] = dt.dayofweek
        else:
            row["hour"] = 0
            row["day_of_week"] = 0

        net_pnl = trade["pnl"] - trade["commission"]
        row["etd"] = trade["mfe"] - max(net_pnl, 0)
        row["duration_bars"] = int(trade["exit_bar"] - trade["entry_bar"])

        # --- NEW: Volume features (8) ---

        # vol_ratio_5: volume / 5-bar MA
        if volume is not None and vol_ma5 is not None and vol_ma5[i] > 0:
            row["vol_ratio_5"] = volume[i] / vol_ma5[i]
        else:
            row["vol_ratio_5"] = 1.0

        # vol_ratio_50: volume / 50-bar MA
        if volume is not None and vol_ma50 is not None and vol_ma50[i] > 0:
            row["vol_ratio_50"] = volume[i] / vol_ma50[i]
        else:
            row["vol_ratio_50"] = 1.0

        # vol_ratio_200: volume / 200-bar MA
        if volume is not None and vol_ma200 is not None and vol_ma200[i] > 0:
            row["vol_ratio_200"] = volume[i] / vol_ma200[i]
        else:
            row["vol_ratio_200"] = 1.0

        # vol_trend: slope of 20-bar volume MA (positive = increasing volume)
        if vol_trend_arr is not None and not np.isnan(vol_trend_arr[i]):
            # Normalize by current MA to make it relative
            if vol_ma20[i] > 0:
                row["vol_trend"] = vol_trend_arr[i] / vol_ma20[i]
            else:
                row["vol_trend"] = 0.0
        else:
            row["vol_trend"] = 0.0

        # vol_zscore: how unusual is current volume? (z-score vs 50-bar window)
        if (volume is not None and vol_std50 is not None and
                vol_ma50 is not None and vol_std50[i] > 0):
            row["vol_zscore"] = (volume[i] - vol_ma50[i]) / vol_std50[i]
        else:
            row["vol_zscore"] = 0.0

        # quote_vol_ratio: USDT turnover / 20-bar MA (captures dollar volume)
        if quote_vol is not None and qvol_ma20 is not None and qvol_ma20[i] > 0:
            row["quote_vol_ratio"] = quote_vol[i] / qvol_ma20[i]
        else:
            row["quote_vol_ratio"] = 1.0

        # vol_price_corr: rolling 20-bar correlation(volume, price change)
        if vol_price_corr_arr is not None and not np.isnan(vol_price_corr_arr[i]):
            row["vol_price_corr"] = vol_price_corr_arr[i]
        else:
            row["vol_price_corr"] = 0.0

        # relative_spread: (high - low) / close (intrabar volatility proxy)
        if close[i] > 0:
            row["relative_spread"] = (high[i] - low[i]) / close[i]
        else:
            row["relative_spread"] = 0.0

        # --- NEW: Market cap features (4) ---

        # log_market_cap: static log10 market cap from coin metadata
        if coin_metadata and coin_metadata.get("market_cap", 0) > 0:
            row["log_market_cap"] = np.log10(coin_metadata["market_cap"])
        else:
            row["log_market_cap"] = np.nan

        # log_daily_turnover: log10 of 20-day avg daily quote volume
        if daily_turnover_at_bar is not None and i < len(daily_turnover_at_bar):
            val = daily_turnover_at_bar[i]
            if not np.isnan(val) and val > 0:
                row["log_daily_turnover"] = np.log10(val)
            else:
                row["log_daily_turnover"] = np.nan
        else:
            row["log_daily_turnover"] = np.nan

        # market_cap_rank: ordinal rank (1-399) from coin metadata
        if coin_metadata and "market_cap_rank" in coin_metadata:
            row["market_cap_rank"] = coin_metadata["market_cap_rank"]
        else:
            row["market_cap_rank"] = np.nan

        # turnover_to_cap_ratio: daily turnover / market cap
        # Uses historical market cap if available, else static
        mcap_val = None
        if has_datetime and i < len(dt_series) and mcap_lookup:
            date_str = dt_series.iloc[i].strftime("%Y-%m-%d")
            if date_str in mcap_lookup:
                mcap_val = mcap_lookup[date_str].get("market_cap", 0)
        if mcap_val is None and coin_metadata:
            mcap_val = coin_metadata.get("market_cap", 0)

        if (mcap_val and mcap_val > 0 and
                daily_turnover_at_bar is not None and i < len(daily_turnover_at_bar)):
            turnover = daily_turnover_at_bar[i]
            if not np.isnan(turnover) and turnover > 0:
                row["turnover_to_cap_ratio"] = turnover / mcap_val
            else:
                row["turnover_to_cap_ratio"] = np.nan
        else:
            row["turnover_to_cap_ratio"] = np.nan

        features.append(row)

    return pd.DataFrame(features)


def get_feature_columns() -> list:
    """
    Return the list of feature column names used for ML training.
    Excludes target/label columns (mfe_r, mae_r, pnl_r, etd) which are
    derived from trade outcome and would leak future info.
    """
    return [
        # Original 14
        "direction_enc", "grade_enc",
        "stoch_9", "stoch_14", "stoch_40", "stoch_60",
        "atr_pct", "vol_ratio",
        "cloud3_bull", "price_pos", "cloud3_spread",
        "hour", "day_of_week",
        # Volume features (8)
        "vol_ratio_5", "vol_ratio_50", "vol_ratio_200",
        "vol_trend", "vol_zscore",
        "quote_vol_ratio", "vol_price_corr", "relative_spread",
        # Market cap features (4)
        "log_market_cap", "log_daily_turnover",
        "market_cap_rank", "turnover_to_cap_ratio",
    ]
