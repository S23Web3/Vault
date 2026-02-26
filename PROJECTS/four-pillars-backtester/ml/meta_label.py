"""
Meta-Labeling with XGBoost (De Prado Ch 3.6).

Meta-labeling is a secondary model that sits on top of a primary
strategy (e.g. Four Pillars). The primary strategy generates signals.
The meta-label model analyzes features at signal time and outputs:
  - Probability that this signal leads to a profitable trade
  - User reviews probabilities, sets threshold, trains model

This module provides the analysis engine. User controls training.

Input: feature matrix (from features.py) + labels (from triple_barrier.py).
Output: trained XGBoost model + probability predictions.
"""

import numpy as np
import pandas as pd

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False


class MetaLabelAnalyzer:
    """
    XGBoost-based meta-label analyzer.
    Trains a classifier on trade features to predict signal quality.
    User sets parameters and triggers training.
    """

    def __init__(self, params: dict = None):
        """
        Initialize with XGBoost hyperparameters.

        Args:
            params: dict of XGBoost params. Defaults to sensible values.
                    User can override any param.
        """
        if not HAS_XGB:
            raise ImportError("xgboost not installed. Run: pip install xgboost")

        default_params = {
            "n_estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "eval_metric": "logloss",
            "verbosity": 0,
        }
        if params:
            default_params.update(params)

        self.params = default_params
        self.model = None
        self.feature_names = None

    def train(self, X: pd.DataFrame, y: np.ndarray,
              feature_names: list = None) -> dict:
        """
        Train the meta-label classifier.

        Args:
            X: feature matrix (n_trades x n_features).
            y: binary labels (1=profitable, 0=not). Use triple_barrier labels
               mapped to binary: +1 -> 1, else -> 0.
            feature_names: optional list of feature column names.

        Returns:
            dict with training metrics (accuracy on train set).
        """
        self.feature_names = feature_names or list(X.columns) if hasattr(X, "columns") else None

        # Drop rows with NaN
        if isinstance(X, pd.DataFrame):
            mask = ~X.isna().any(axis=1)
            X_clean = X[mask].values
            y_clean = y[mask.values] if hasattr(mask, "values") else y[mask]
        else:
            mask = ~np.isnan(X).any(axis=1)
            X_clean = X[mask]
            y_clean = y[mask]

        if len(X_clean) < 20:
            raise ValueError(f"Need at least 20 clean samples, got {len(X_clean)}")

        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X_clean, y_clean)

        # Training accuracy
        preds = self.model.predict(X_clean)
        accuracy = np.mean(preds == y_clean)

        return {
            "train_samples": len(X_clean),
            "dropped_nan": int(np.sum(~mask)),
            "train_accuracy": float(accuracy),
            "positive_rate": float(np.mean(y_clean)),
        }

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probability of profitable trade for each row.

        Args:
            X: feature matrix (same columns as training).

        Returns:
            array of probabilities (0.0 to 1.0) for positive class.
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        if isinstance(X, pd.DataFrame):
            X_vals = X.values
        else:
            X_vals = X

        # Handle NaN rows: predict 0.5 (no opinion)
        mask = ~np.isnan(X_vals).any(axis=1)
        probs = np.full(len(X_vals), 0.5)
        if mask.any():
            probs[mask] = self.model.predict_proba(X_vals[mask])[:, 1]

        return probs

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Return feature importance from trained model.

        Returns:
            DataFrame with feature name and importance score, sorted descending.
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        importance = self.model.feature_importances_
        names = self.feature_names or [f"f{i}" for i in range(len(importance))]

        df = pd.DataFrame({
            "feature": names[:len(importance)],
            "importance": importance,
        }).sort_values("importance", ascending=False).reset_index(drop=True)

        return df
