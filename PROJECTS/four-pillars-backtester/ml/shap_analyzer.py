"""
SHAP Explainability for Meta-Label Model (Jansen Ch 12).

SHAP (SHapley Additive exPlanations) provides per-trade feature
attribution: for each trade, which features pushed the model
toward "take" vs "skip"?

This gives the user concrete explanations:
  "Trade #42 was flagged SKIP because stoch_60=48 (mid-range)
   and vol_ratio=0.3 (low volume)."

Input: trained meta-label model + feature matrix.
Output: SHAP values per trade, summary plots data.
"""

import numpy as np
import pandas as pd

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class ShapAnalyzer:
    """
    Generates SHAP explanations for a trained XGBoost meta-label model.
    User reviews explanations to understand model reasoning.
    """

    def __init__(self, model, feature_names: list = None):
        """
        Initialize with a trained XGBoost model.

        Args:
            model: trained XGBoost model (from MetaLabelAnalyzer.model).
            feature_names: list of feature column names.
        """
        if not HAS_SHAP:
            raise ImportError("shap not installed. Run: pip install shap")

        self.model = model
        self.feature_names = feature_names
        self.shap_values = None
        self.explainer = None

    def compute(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute SHAP values for all trades in feature matrix.

        Args:
            X: feature matrix (n_trades x n_features).

        Returns:
            SHAP values array (n_trades x n_features).
        """
        if isinstance(X, pd.DataFrame):
            X_vals = X.values
        else:
            X_vals = X

        # TreeExplainer is fastest for XGBoost
        self.explainer = shap.TreeExplainer(self.model)
        self.shap_values = self.explainer.shap_values(X_vals)

        return self.shap_values

    def get_top_features(self, trade_idx: int, top_n: int = 5) -> list:
        """
        Get the top N features driving prediction for a specific trade.

        Args:
            trade_idx: index of the trade in the feature matrix.
            top_n: number of top features to return.

        Returns:
            list of dicts with feature name, shap value, and direction.
        """
        if self.shap_values is None:
            raise ValueError("Call compute() first.")

        vals = self.shap_values[trade_idx]
        names = self.feature_names or [f"f{i}" for i in range(len(vals))]

        # Sort by absolute SHAP value
        indices = np.argsort(np.abs(vals))[::-1][:top_n]

        result = []
        for idx in indices:
            result.append({
                "feature": names[idx] if idx < len(names) else f"f{idx}",
                "shap_value": float(vals[idx]),
                "direction": "TAKE" if vals[idx] > 0 else "SKIP",
            })

        return result

    def get_global_importance(self) -> pd.DataFrame:
        """
        Mean absolute SHAP value per feature (global importance).

        Returns:
            DataFrame with feature and mean_abs_shap, sorted descending.
        """
        if self.shap_values is None:
            raise ValueError("Call compute() first.")

        mean_abs = np.mean(np.abs(self.shap_values), axis=0)
        names = self.feature_names or [f"f{i}" for i in range(len(mean_abs))]

        df = pd.DataFrame({
            "feature": names[:len(mean_abs)],
            "mean_abs_shap": mean_abs,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

        return df
