"""
Test script for VINCE ML pipeline.
Validates: coin_features, vince_model, training_pipeline, xgboost_auditor.
"""

import os
import sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PASS = 0
FAIL = 0

def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


def main():
    global PASS, FAIL
    print("=" * 60)
    print("TEST: VINCE ML Pipeline")
    print("=" * 60)

    # 1. Coin features
    print("\n--- coin_features.py ---")
    try:
        from ml.coin_features import compute_coin_features, get_feature_names
        check("Import coin_features", True)
    except Exception as e:
        check(f"Import coin_features: {e}", False)
        print(f"\n{PASS} passed, {FAIL} failed")
        return

    # Create sample OHLCV data
    n = 1000
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    sample_df = pd.DataFrame({
        "open": prices,
        "high": prices + np.random.rand(n) * 2,
        "low": prices - np.random.rand(n) * 2,
        "close": prices + np.random.randn(n) * 0.3,
        "base_vol": np.random.rand(n) * 1000 + 100,
        "datetime": pd.date_range("2025-01-01", periods=n, freq="5min"),
    })
    sample_df = sample_df.set_index("datetime")

    features = compute_coin_features(sample_df)
    check("Compute features returns dict", isinstance(features, dict))
    check("Has 10 features", len(features) == 10)

    names = get_feature_names()
    check("get_feature_names() returns 10", len(names) == 10)
    for name in names:
        check(f"Feature '{name}' computed", name in features)

    check("avg_daily_volume > 0", features["avg_daily_volume"] > 0)
    check("bar_count == 1000", features["bar_count"] == 1000)

    # 2. VINCE Model
    print("\n--- vince_model.py ---")
    try:
        import torch
        from ml.vince_model import VinceModel, GRADE_MAP, DIR_MAP, PATH_MAP
        check("Import VinceModel", True)
    except Exception as e:
        check(f"Import VinceModel: {e}", False)
        print(f"\n{PASS} passed, {FAIL} failed")
        return

    model = VinceModel()
    check("Model instantiates", model is not None)

    # Test forward pass
    batch = 4
    numeric = torch.randn(batch, 22)
    grade_idx = torch.tensor([0, 1, 2, 3])
    dir_idx = torch.tensor([0, 1, 2, 0])
    path_idx = torch.tensor([0, 1, 2, 3])
    seq = torch.randn(batch, 10, 15)
    seq_len = torch.tensor([10, 8, 6, 10])
    coin_ctx = torch.randn(batch, 10)

    out = model(numeric, grade_idx, dir_idx, path_idx, seq, seq_len, coin_ctx)
    check("Forward pass produces win_prob", "win_prob" in out)
    check("win_prob shape correct", out["win_prob"].shape == (batch,))
    check("win_prob in [0,1]", out["win_prob"].min() >= 0 and out["win_prob"].max() <= 1)
    check("path_logits shape correct", out["path_logits"].shape == (batch, 4))

    # Phase 1 (tabular only)
    out1 = model.predict_tabular_only(numeric, grade_idx, dir_idx, path_idx, coin_ctx)
    check("Phase 1 forward pass works", "win_prob" in out1)

    # 3. Training pipeline
    print("\n--- training_pipeline.py ---")
    try:
        from ml.training_pipeline import assign_pools, TradeDataset
        check("Import training_pipeline", True)
    except Exception as e:
        check(f"Import training_pipeline: {e}", False)
        print(f"\n{PASS} passed, {FAIL} failed")
        return

    test_symbols = [f"COIN{i}USDT" for i in range(100)]
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    try:
        pools = assign_pools(test_symbols, seed=42, pool_file=tmp_path)
        check("Pool assignment returns dict", isinstance(pools, dict))
        check("All symbols assigned", len(pools) == 100)
        a_count = sum(1 for v in pools.values() if v == "A")
        b_count = sum(1 for v in pools.values() if v == "B")
        c_count = sum(1 for v in pools.values() if v == "C")
        check(f"Pool A ~60% (got {a_count})", 55 <= a_count <= 65)
        check(f"Pool B ~20% (got {b_count})", 15 <= b_count <= 25)
        check(f"Pool C ~20% (got {c_count})", 15 <= c_count <= 25)

        # Deterministic
        pools2 = assign_pools(test_symbols, seed=42, pool_file=tmp_path)
        check("Pool assignment deterministic", pools == pools2)
    finally:
        os.remove(tmp_path)

    # 4. XGBoost Auditor
    print("\n--- xgboost_auditor.py ---")
    try:
        from ml.xgboost_auditor import XGBoostAuditor
        check("Import XGBoostAuditor", True)
    except Exception as e:
        check(f"Import XGBoostAuditor: {e}", False)
        print(f"\n{PASS} passed, {FAIL} failed")
        return

    auditor = XGBoostAuditor()
    check("Auditor instantiates", auditor is not None)

    # Small synthetic dataset
    X = pd.DataFrame(np.random.randn(200, 5), columns=["f1", "f2", "f3", "f4", "f5"])
    y = (X["f1"] + X["f2"] > 0).astype(int).values
    metrics = auditor.train(X[:160], y[:160], X[160:], y[160:])
    check("Auditor trains", "train_acc" in metrics)
    check("Train acc > 0.5", metrics["train_acc"] > 0.5)

    shap_vals = auditor.compute_shap(X[:160])
    check("SHAP values computed", shap_vals is not None)
    top = auditor.get_top_features(3)
    check("Top features returned", len(top) == 3)

    comparison = auditor.compare_with_pytorch(["f1", "f2", "f3", "f4", "f5"])
    check("Comparison returns agreement_pct", "agreement_pct" in comparison)

    print(f"\n{'='*60}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
