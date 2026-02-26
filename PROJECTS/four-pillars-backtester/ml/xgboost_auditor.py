"""
XGBoost Validation Auditor -- SHAP comparison with PyTorch model.

Role: Validation/auditor model. Trains on same data, same features.
NOT a production model -- it never makes live decisions.

Agreement metric: % of top-10 features shared between PyTorch (Captum)
and XGBoost (SHAP). If < 70%, flag for manual review.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from typing import Dict, List, Tuple, Optional


class XGBoostAuditor:
    """XGBoost validation auditor with SHAP interpretability."""

    def __init__(self, params: Optional[Dict] = None):
        self.params = params or {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 6,
            "learning_rate": 0.1,
            "n_estimators": 200,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
        }
        self.model = None
        self.feature_names = None
        self.shap_values = None
        self.explainer = None

    def train(self, X_train: pd.DataFrame, y_train: np.ndarray,
              X_val: pd.DataFrame = None, y_val: np.ndarray = None) -> Dict:
        """Train XGBoost on same data as PyTorch model."""
        self.feature_names = list(X_train.columns)

        n_est = self.params.pop("n_estimators", 200)
        self.model = xgb.XGBClassifier(n_estimators=n_est, **self.params)

        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))

        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False,
        )

        # Restore n_estimators for potential re-use
        self.params["n_estimators"] = n_est

        metrics = {
            "train_acc": float(self.model.score(X_train, y_train)),
        }
        if X_val is not None:
            metrics["val_acc"] = float(self.model.score(X_val, y_val))
            y_pred_proba = self.model.predict_proba(X_val)[:, 1]
            metrics["val_predictions"] = y_pred_proba

        return metrics

    def compute_shap(self, X: pd.DataFrame) -> np.ndarray:
        """Compute SHAP values for feature importance."""
        self.explainer = shap.TreeExplainer(self.model)
        self.shap_values = self.explainer.shap_values(X)
        return self.shap_values

    def get_top_features(self, n: int = 10) -> List[str]:
        """Return top-N features by mean absolute SHAP value."""
        if self.shap_values is None:
            raise ValueError("Call compute_shap() first")
        mean_abs = np.mean(np.abs(self.shap_values), axis=0)
        idx = np.argsort(mean_abs)[::-1][:n]
        return [self.feature_names[i] for i in idx]

    def compare_with_pytorch(self, pytorch_top_features: List[str],
                             n: int = 10) -> Dict:
        """
        Compare top-N features between XGBoost (SHAP) and PyTorch (Captum).
        Returns agreement metric and details.
        """
        xgb_top = set(self.get_top_features(n))
        pt_top = set(pytorch_top_features[:n])
        overlap = xgb_top & pt_top
        agreement = len(overlap) / n * 100

        return {
            "agreement_pct": agreement,
            "n_overlap": len(overlap),
            "shared_features": sorted(overlap),
            "xgb_only": sorted(xgb_top - pt_top),
            "pytorch_only": sorted(pt_top - xgb_top),
            "flag_review": agreement < 70,
        }

    def get_feature_importance_df(self) -> pd.DataFrame:
        """Return DataFrame of feature importances."""
        if self.shap_values is None:
            raise ValueError("Call compute_shap() first")
        mean_abs = np.mean(np.abs(self.shap_values), axis=0)
        df = pd.DataFrame({
            "feature": self.feature_names,
            "mean_abs_shap": mean_abs,
        })
        return df.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
