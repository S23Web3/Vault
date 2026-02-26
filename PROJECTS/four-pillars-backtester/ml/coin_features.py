"""
Coin characteristics -- 10 OHLCV-derived features per coin.

Computed ONCE from raw data before any backtest.
These are inputs to VINCE, never labels. No backtest result leakage.

volume_mcap_ratio deferred (needs external API for market cap).
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def compute_coin_features(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute 10 OHLCV-derived features for a single coin.

    Args:
        df: OHLCV DataFrame with columns: open, high, low, close, base_vol/volume.
            Must have datetime index or column.

    Returns:
        Dict of 10 feature name -> value pairs.
    """
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    n = len(close)

    vol_col = "base_vol" if "base_vol" in df.columns else "volume"
    vol = df[vol_col].values.astype(float) if vol_col in df.columns else np.zeros(n)

    quote_col = "quote_vol" if "quote_vol" in df.columns else "turnover"
    quote_vol = df[quote_col].values.astype(float) if quote_col in df.columns else vol * close

    # 1. avg_daily_volume: mean daily quote volume
    if hasattr(df.index, "date") or "datetime" in df.columns:
        try:
            if "datetime" in df.columns:
                dates = pd.to_datetime(df["datetime"])
            else:
                dates = df.index
            daily_vol = pd.Series(quote_vol, index=dates).resample("1D").sum()
            avg_daily_volume = float(daily_vol.mean())
        except Exception:
            avg_daily_volume = float(np.mean(quote_vol)) * 288  # approx 5m bars/day
    else:
        avg_daily_volume = float(np.mean(quote_vol)) * 288

    # 2. volume_stability: CV of daily volume
    try:
        daily_std = float(daily_vol.std())
        daily_mean = float(daily_vol.mean())
        volume_stability = daily_std / daily_mean if daily_mean > 0 else 0.0
    except Exception:
        volume_stability = 0.0

    # 3. avg_spread_proxy: mean (high-low)/close per bar
    spreads = (high - low) / np.where(close > 0, close, 1.0)
    avg_spread_proxy = float(np.nanmean(spreads))

    # 4. volatility_regime: annualized std of returns
    returns = np.diff(np.log(np.where(close > 0, close, 1.0)))
    volatility_regime = float(np.std(returns) * np.sqrt(365 * 288)) if len(returns) > 1 else 0.0

    # 5. drift_noise_ratio: net drift vs noise
    if n > 1 and np.std(close) > 0:
        drift_noise_ratio = abs(close[-1] - close[0]) / np.std(close)
    else:
        drift_noise_ratio = 0.0

    # 6. mean_reversion_score: lag-1 autocorrelation of returns
    if len(returns) > 2:
        mean_reversion_score = float(np.corrcoef(returns[:-1], returns[1:])[0, 1])
        if np.isnan(mean_reversion_score):
            mean_reversion_score = 0.0
    else:
        mean_reversion_score = 0.0

    # 7. volume_mcap_ratio: DEFERRED (needs market cap API)
    volume_mcap_ratio = 0.0

    # 8. bar_count: total bars
    bar_count = n

    # 9. gap_pct: bars with zero volume
    gap_pct = float(np.sum(vol == 0)) / n if n > 0 else 0.0

    # 10. price_range: (max - min) / min
    min_p = float(np.min(close[close > 0])) if np.any(close > 0) else 1.0
    max_p = float(np.max(close))
    price_range = (max_p - min_p) / min_p if min_p > 0 else 0.0

    return {
        "avg_daily_volume": avg_daily_volume,
        "volume_stability": volume_stability,
        "avg_spread_proxy": avg_spread_proxy,
        "volatility_regime": volatility_regime,
        "drift_noise_ratio": float(drift_noise_ratio),
        "mean_reversion_score": mean_reversion_score,
        "volume_mcap_ratio": volume_mcap_ratio,
        "bar_count": bar_count,
        "gap_pct": gap_pct,
        "price_range": price_range,
    }


def get_feature_names() -> list:
    """Return ordered list of coin feature names."""
    return [
        "avg_daily_volume", "volume_stability", "avg_spread_proxy",
        "volatility_regime", "drift_noise_ratio", "mean_reversion_score",
        "volume_mcap_ratio", "bar_count", "gap_pct", "price_range",
    ]
