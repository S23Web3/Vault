
"""Layer 4c: Coin Classifier -- KMeans volatility tier assignment.

Input: Parquet directory containing SYMBOL_TIMEFRAME.parquet files.
Output: DataFrame with [symbol, tier, avg_atr_pct, avg_bbw_raw,
        avg_daily_range, avg_base_vol, vol_of_vol] columns.

Tiers sorted by avg_atr_pct: 0=calmest, N-1=wildest.
Imported by: scripts/run_bbw_simulator.py
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

REQUIRED_COLS = ["open", "high", "low", "close"]
BB_PERIOD = 20
BB_STD = 2.0
ATR_PERIOD = 14
SILHOUETTE_K_RANGE = (3, 5)


def _compute_atr(df, period=ATR_PERIOD):
    """Wilder-smoothed ATR series."""
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def _compute_bb_width(df, period=BB_PERIOD, n_std=BB_STD):
    """Bollinger Band Width: (upper - lower) / middle."""
    close = df["close"].astype(float)
    mid = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    upper = mid + n_std * std
    lower = mid - n_std * std
    denom = mid.replace(0, np.nan)
    return (upper - lower) / denom


def _resample_ohlcv(df, timeframe):
    """Resample 1m OHLCV DataFrame to target timeframe string."""
    freq_map = {"5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}
    freq = freq_map.get(timeframe, timeframe)
    if "datetime" not in df.columns:
        if df.index.name == "datetime":
            df = df.reset_index()
    df = df.set_index("datetime")
    vol_col = "base_vol" if "base_vol" in df.columns else (
        "volume" if "volume" in df.columns else None
    )
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if vol_col:
        agg[vol_col] = "sum"
    resampled = df.resample(freq).agg(agg).dropna()
    return resampled.reset_index()


def compute_coin_features(df, symbol):
    """Compute 5 volatility features from OHLCV DataFrame for one coin.

    Returns dict: symbol, avg_atr_pct, avg_bbw_raw, avg_daily_range,
    avg_base_vol, vol_of_vol.
    """
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError("Missing column " + col + " for " + symbol)
    close = df["close"].astype(float)
    if close.empty or close.isna().all():
        raise ValueError("No valid close prices for " + symbol)
    atr = _compute_atr(df)
    avg_atr_pct = float((atr / close.replace(0, np.nan)).dropna().mean() * 100)
    bbw = _compute_bb_width(df)
    avg_bbw_raw = float(bbw.dropna().mean())
    high_f = df["high"].astype(float)
    low_f = df["low"].astype(float)
    daily_range = (high_f - low_f) / close.replace(0, np.nan)
    avg_daily_range = float(daily_range.dropna().mean() * 100)
    vol_of_vol = float(daily_range.dropna().std() * 100)
    vol_col = (
        "base_vol" if "base_vol" in df.columns
        else "volume" if "volume" in df.columns
        else None
    )
    avg_base_vol = float(df[vol_col].astype(float).dropna().mean()) if vol_col else 0.0
    return {
        "symbol": symbol,
        "avg_atr_pct": avg_atr_pct,
        "avg_bbw_raw": avg_bbw_raw,
        "avg_daily_range": avg_daily_range,
        "avg_base_vol": avg_base_vol,
        "vol_of_vol": vol_of_vol,
    }


def classify_coin_tiers(parquet_dir, timeframe="5m", n_clusters=4,
                        output_path=None, verbose=False):
    """Assign KMeans volatility tier to each coin in parquet_dir.

    Loads all *.parquet files, computes 5 features per coin, runs KMeans
    with silhouette-selected k in range 3-5. Tiers sorted by avg_atr_pct:
    0=calmest, N-1=wildest. Saves CSV if output_path given.
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        raise ImportError(
            "scikit-learn is required for coin_classifier. "
            "Install with: pip install scikit-learn"
        ) from e

    parquet_dir = Path(parquet_dir)
    # Always load 1m files and resample -- avoids processing the same symbol
    # twice when both _1m.parquet and _5m.parquet exist in the cache.
    parquet_files = sorted(parquet_dir.glob("*_1m.parquet"))
    if not parquet_files:
        # Fallback: any parquet (e.g. custom cache with different naming)
        parquet_files = sorted(parquet_dir.glob("*.parquet"))
    if not parquet_files:
        raise ValueError("No parquet files found in " + str(parquet_dir))

    feature_rows = []
    seen_symbols = set()
    for pfile in parquet_files:
        stem = pfile.stem
        parts = stem.rsplit("_", 1)
        symbol = parts[0] if len(parts) > 1 else stem
        if symbol in seen_symbols:
            log.debug("SKIP %s: already processed", symbol)
            continue
        seen_symbols.add(symbol)
        try:
            df = pd.read_parquet(pfile)
        except Exception as e:
            log.warning("SKIP %s: failed to load -- %s", pfile.name, e)
            continue
        if timeframe != "1m":
            try:
                df = _resample_ohlcv(df, timeframe)
            except Exception as e:
                log.warning("SKIP %s: resample failed -- %s", symbol, e)
                continue
        if len(df) < 50:
            log.warning("SKIP %s: too few bars (%d)", symbol, len(df))
            continue
        try:
            feat = compute_coin_features(df, symbol)
            feature_rows.append(feat)
            if verbose:
                log.info("OK %s: atr_pct=%.4f bbw=%.4f",
                         symbol, feat["avg_atr_pct"], feat["avg_bbw_raw"])
        except Exception as e:
            log.warning("SKIP %s: feature error -- %s", symbol, e)
            continue

    if len(feature_rows) < 4:
        raise ValueError(
            "Need at least 4 coins for tier classification, got "
            + str(len(feature_rows))
        )

    features_df = pd.DataFrame(feature_rows)
    feature_cols = [
        "avg_atr_pct", "avg_bbw_raw", "avg_daily_range",
        "avg_base_vol", "vol_of_vol",
    ]
    X = features_df[feature_cols].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k = n_clusters
    best_score = -1.0
    best_labels = None
    k_min, k_max = SILHOUETTE_K_RANGE
    for k in range(k_min, min(k_max + 1, len(feature_rows))):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        if len(np.unique(labels)) < 2:
            continue
        score = silhouette_score(X_scaled, labels)
        if verbose:
            log.info("  k=%d silhouette=%.4f", k, score)
        if score > best_score:
            best_score = score
            best_k = k
            best_labels = labels

    if best_labels is None:
        km = KMeans(
            n_clusters=min(n_clusters, len(feature_rows)),
            random_state=42, n_init=10,
        )
        best_labels = km.fit_predict(X_scaled)

    features_df["raw_cluster"] = best_labels
    cluster_means = features_df.groupby("raw_cluster")["avg_atr_pct"].mean()
    sorted_clusters = cluster_means.sort_values().index.tolist()
    cluster_to_tier = {c: i for i, c in enumerate(sorted_clusters)}
    features_df["tier"] = features_df["raw_cluster"].map(cluster_to_tier)

    result = (
        features_df[["symbol", "tier"] + feature_cols]
        .sort_values(["tier", "symbol"])
        .reset_index(drop=True)
    )

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(out, index=False)
        if verbose:
            log.info("Saved tier CSV: %s", out)

    return result
