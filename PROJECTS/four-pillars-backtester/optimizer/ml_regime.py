"""
ML regime model — learns optimal parameters per market regime.
Uses XGBoost for regime classification, maps regimes to best params.
PyTorch available for deeper models if needed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def compute_regime_features(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
    """
    Compute market regime features from OHLCV data.

    Features:
    - ATR normalized by price (volatility)
    - Cloud 3 bull/bear ratio over lookback
    - BBWP approximation
    - Price position relative to Cloud 3
    - Trend strength (slope of ema50)
    """
    feat = pd.DataFrame(index=df.index)

    close = df["close"].values
    atr = df["atr"].values

    # Normalized ATR (volatility)
    feat["norm_atr"] = atr / close

    # Cloud 3 bull ratio over lookback
    if "cloud3_bull" in df.columns:
        feat["cloud3_bull_ratio"] = df["cloud3_bull"].rolling(lookback, min_periods=1).mean()

    # Price position rolling average
    if "price_pos" in df.columns:
        feat["price_pos_avg"] = df["price_pos"].rolling(lookback, min_periods=1).mean()

    # Trend strength: slope of ema50 over lookback
    if "ema50" in df.columns:
        ema50 = df["ema50"].values
        slope = np.full(len(ema50), np.nan)
        for i in range(lookback, len(ema50)):
            if not np.isnan(ema50[i]) and not np.isnan(ema50[i - lookback]):
                slope[i] = (ema50[i] - ema50[i - lookback]) / ema50[i - lookback]
        feat["ema50_slope"] = slope

    # BBW percentile approximation
    bbw = df["high"].rolling(20).max() - df["low"].rolling(20).min()
    feat["bbw_pctrank"] = bbw.rank(pct=True)

    return feat


def classify_regimes(features: pd.DataFrame, n_regimes: int = 3) -> np.ndarray:
    """
    Simple regime classification based on feature thresholds.
    Returns array of regime labels (0=bull, 1=bear, 2=crash).
    """
    n = len(features)
    regimes = np.full(n, 0)  # Default: bull

    if "norm_atr" in features.columns and "cloud3_bull_ratio" in features.columns:
        norm_atr = features["norm_atr"].values
        bull_ratio = features["cloud3_bull_ratio"].values

        for i in range(n):
            if np.isnan(norm_atr[i]) or np.isnan(bull_ratio[i]):
                continue

            # Crash: high volatility
            if norm_atr[i] > np.nanpercentile(norm_atr[:i + 1], 80) if i > 60 else False:
                regimes[i] = 2
            # Bear: mostly bearish clouds
            elif bull_ratio[i] < 0.4:
                regimes[i] = 1
            # Bull: default
            else:
                regimes[i] = 0

    return regimes


class RegimeParamMapper:
    """
    Maps market regimes to optimal strategy parameters.
    Train on grid search / Optuna results labeled with regime.
    """

    def __init__(self):
        self.regime_params = {}
        self.model = None

    def fit_from_grid(self, grid_results: pd.DataFrame, regimes: np.ndarray,
                      target_col: str = "sharpe"):
        """
        For each regime, find the best parameter set from grid results.

        Args:
            grid_results: DataFrame from grid_search with param columns + metric columns
            regimes: Regime label for each grid result row
            target_col: Metric to maximize
        """
        grid_results = grid_results.copy()
        grid_results["regime"] = regimes[:len(grid_results)]

        param_cols = [c for c in grid_results.columns
                      if c not in ["total_trades", "win_rate", "expectancy", "net_pnl",
                                   "profit_factor", "sharpe", "max_drawdown",
                                   "max_drawdown_pct", "pct_losers_saw_green",
                                   "be_raised_count", "regime"]]

        for regime_id in grid_results["regime"].unique():
            subset = grid_results[grid_results["regime"] == regime_id]
            if len(subset) == 0:
                continue
            best_idx = subset[target_col].idxmax()
            best_row = subset.loc[best_idx]
            self.regime_params[int(regime_id)] = {col: best_row[col] for col in param_cols}

        return self

    def get_params(self, regime: int) -> dict:
        """Get optimal params for a regime. Falls back to regime 0 if not found."""
        return self.regime_params.get(regime, self.regime_params.get(0, {}))

    def fit_xgboost(self, features: pd.DataFrame, regimes: np.ndarray):
        """Train XGBoost regime classifier on market features."""
        if not HAS_XGB:
            raise ImportError("xgboost not installed. pip install xgboost")

        # Drop NaN rows
        mask = ~features.isna().any(axis=1)
        X = features[mask].values
        y = regimes[mask.values]

        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            use_label_encoder=False,
            eval_metric="mlogloss",
            tree_method="gpu_hist" if HAS_TORCH and torch.cuda.is_available() else "hist",
        )
        self.model.fit(X, y)
        return self

    def predict_regime(self, features: pd.DataFrame) -> np.ndarray:
        """Predict regime from market features using trained model."""
        if self.model is None:
            raise ValueError("Model not trained. Call fit_xgboost() first.")
        mask = ~features.isna().any(axis=1)
        result = np.full(len(features), 0)
        if mask.any():
            result[mask.values] = self.model.predict(features[mask].values)
        return result
