"""
SHAP Explainability v2 -- bug fixes applied.

Fixes from v1:
  - Empty array guard before shap_values()
  - Binary SHAP list-vs-array normalization (old vs new shap library)
"""

import logging
import numpy as np
import pandas as pd

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

log = logging.getLogger(__name__)


class ShapAnalyzer:
    """Generates SHAP explanations for a trained XGBoost model."""

    def __init__(self, model, feature_names: list = None):
        """Initialize with a trained XGBoost model."""
        if not HAS_SHAP:
            raise ImportError("shap not installed. Run: pip install shap")
        self.model = model
        self.feature_names = feature_names
        self.shap_values = None
        self.explainer = None

    def compute(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values for all trades in feature matrix."""
        if isinstance(X, pd.DataFrame):
            X_vals = X.values
        else:
            X_vals = X

        # FIX: guard against empty feature matrix
        if len(X_vals) == 0:
            log.warning("Empty feature matrix passed to ShapAnalyzer.compute()")
            self.shap_values = np.empty((0, X_vals.shape[1] if X_vals.ndim == 2 else 0))
            return self.shap_values

        self.explainer = shap.TreeExplainer(self.model)
        self.shap_values = self.explainer.shap_values(X_vals)

        # FIX: handle binary XGBoost SHAP shape (old shap returns list)
        if isinstance(self.shap_values, list):
            log.info("SHAP returned list of %d arrays, using class 1 (TAKE)", len(self.shap_values))
            self.shap_values = self.shap_values[1]

        return self.shap_values

    def get_top_features(self, trade_idx: int, top_n: int = 5) -> list:
        """Get top N features driving prediction for a specific trade."""
        if self.shap_values is None:
            raise ValueError("Call compute() first.")
        if len(self.shap_values) == 0:
            return []

        vals = self.shap_values[trade_idx]
        names = self.feature_names or ["f" + str(i) for i in range(len(vals))]
        indices = np.argsort(np.abs(vals))[::-1][:top_n]

        result = []
        for idx in indices:
            result.append({
                "feature": names[idx] if idx < len(names) else "f" + str(idx),
                "shap_value": float(vals[idx]),
                "direction": "TAKE" if vals[idx] > 0 else "SKIP",
            })
        return result

    def get_global_importance(self) -> pd.DataFrame:
        """Mean absolute SHAP value per feature (global importance)."""
        if self.shap_values is None:
            raise ValueError("Call compute() first.")
        if len(self.shap_values) == 0:
            return pd.DataFrame(columns=["feature", "mean_abs_shap"])

        mean_abs = np.mean(np.abs(self.shap_values), axis=0)
        names = self.feature_names or ["f" + str(i) for i in range(len(mean_abs))]

        df = pd.DataFrame({
            "feature": names[:len(mean_abs)],
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

        return df
