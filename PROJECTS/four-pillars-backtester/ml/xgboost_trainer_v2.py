"""
XGBoost binary classifier v2 -- GPU mandatory, bug fixes applied.

Fixes from v1:
  - Removed deprecated use_label_encoder param
  - GPU: device=cuda, tree_method=hist (mandatory, no CPU fallback)
  - Safe mask indexing: np.asarray(y) prevents Series misalignment
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
)

log = logging.getLogger(__name__)


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list = None,
    test_size: float = 0.3,
    params: dict = None,
) -> dict:
    """Train XGBoost binary classifier with GPU acceleration."""
    if not HAS_XGB:
        raise ImportError("xgboost not installed. pip install xgboost")

    # Clean NaN -- safe indexing
    if isinstance(X, pd.DataFrame):
        mask = ~X.isna().any(axis=1)
        X = X[mask].values
        y = np.asarray(y)[mask.values]
    else:
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = np.asarray(y)[mask]

    if len(X) < 20:
        raise ValueError("Need >= 20 samples, got " + str(len(X)))

    default_params = {
        "objective": "binary:logistic",
        "device": "cuda",
        "tree_method": "hist",
        "max_depth": 4,
        "learning_rate": 0.05,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "logloss",
        "verbosity": 0,
    }
    if params:
        default_params.update(params)

    n_unique = len(np.unique(y))
    stratify = y if n_unique > 1 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )

    model = XGBClassifier(**default_params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    importances = model.feature_importances_
    if feature_names and len(feature_names) == X.shape[1]:
        names = feature_names
    else:
        names = ["f" + str(i) for i in range(len(importances))]

    imp_df = pd.DataFrame({
        "feature": names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)

    # AUC (handle single-class edge case)
    try:
        auc = float(roc_auc_score(y_test, y_proba))
    except ValueError:
        auc = 0.0
        log.warning("AUC undefined (single class in test set)")

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "auc": auc,
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
    """Predict 0 (SKIP) or 1 (TAKE) for each sample."""
    proba = model.predict_proba(X)[:, 1]
    return (proba >= threshold).astype(int)
