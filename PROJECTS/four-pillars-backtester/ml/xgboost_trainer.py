"""
XGBoost binary classifier for meta-labeling.
Wraps ml.meta_label.MetaLabelAnalyzer with a simpler interface.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str] = None,
    test_size: float = 0.3,
    params: dict = None,
) -> dict:
    """
    Train XGBoost binary classifier.

    Args:
        X: Feature matrix (n_samples x n_features).
        y: Binary labels (0 or 1).
        feature_names: Optional list of feature names.
        test_size: Fraction for test split.
        params: XGBoost hyperparameters override.

    Returns:
        dict with model, feature_importances, test_metrics.
    """
    if not HAS_XGB:
        raise ImportError("xgboost not installed. pip install xgboost")

    # Clean NaN
    if isinstance(X, pd.DataFrame):
        mask = ~X.isna().any(axis=1)
        X = X[mask].values
        y = y[mask.values] if hasattr(mask, 'values') else y[mask]
    else:
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = y[mask]

    if len(X) < 20:
        raise ValueError(f"Need >= 20 samples, got {len(X)}")

    default_params = {
        "objective": "binary:logistic",
        "max_depth": 4,
        "learning_rate": 0.05,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "logloss",
        "use_label_encoder": False,
        "verbosity": 0,
    }
    if params:
        default_params.update(params)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    model = XGBClassifier(**default_params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred.astype(float)

    importances = model.feature_importances_
    if feature_names and len(feature_names) == X.shape[1]:
        imp_df = pd.DataFrame({
            "feature": feature_names,
            "importance": importances,
        }).sort_values("importance", ascending=False)
    else:
        imp_df = pd.DataFrame({
            "feature": [f"f{i}" for i in range(len(importances))],
            "importance": importances,
        }).sort_values("importance", ascending=False)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "positive_rate": float(np.mean(y)),
    }

    return {
        "model": model,
        "feature_importances": imp_df,
        "metrics": metrics,
    }


def predict_skip_take(model, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """
    Predict 0 (SKIP) or 1 (TAKE) for each sample.

    Args:
        model: Trained XGBClassifier.
        X: Feature matrix.
        threshold: Probability threshold.

    Returns:
        Array of 0s and 1s.
    """
    proba = model.predict_proba(X)[:, 1]
    return (proba >= threshold).astype(int)


if __name__ == "__main__":
    np.random.seed(42)
    X = np.random.randn(200, 10)
    y = (X[:, 0] + X[:, 1] * 0.5 > 0).astype(int)
    result = train_xgboost(X, y, feature_names=[f"feat_{i}" for i in range(10)])
    print(f"PASS -- accuracy: {result['metrics']['accuracy']:.3f}, "
          f"features: {len(result['feature_importances'])}")
