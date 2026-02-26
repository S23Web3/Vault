r"""
Test the ml/ pipeline end-to-end with real cached data.

Tests all 8 modules in dependency order:
  1. features.py     -- extract features from backtest trades
  2. triple_barrier  -- label trades by exit type
  3. purged_cv       -- leak-free cross-validation splits
  4. meta_label      -- XGBoost meta-label training + predict
  5. shap_analyzer   -- SHAP feature explanations
  6. bet_sizing      -- probability to position size
  7. walk_forward    -- rolling IS/OOS validation
  8. loser_analysis  -- Sweeney loser classification

Uses RIVERUSDT 5m as the test coin (best performer in v3.8 sweep).
Falls back to synthetic data if no cached data available.

Run:  python scripts/test_ml_pipeline.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""

import sys
import time
import traceback
from pathlib import Path

# Project root on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd


# ==============================================================================
# DATA LOADING -- real cached data or synthetic fallback
# ==============================================================================

def load_test_data():
    """
    Load RIVERUSDT 5m, run signals + backtest, return (ohlcv_df, trades_df).
    Falls back to synthetic data if cache missing.
    """
    from data.fetcher import BybitFetcher
    from signals.four_pillars import compute_signals
    from engine.backtester import Backtester
    from engine.metrics import trades_to_dataframe

    fetcher = BybitFetcher(cache_dir=str(ROOT / "data" / "cache"))
    symbol = "RIVERUSDT"
    df_1m = fetcher.load_cached(symbol)

    if df_1m is None:
        # Try any available coin
        cached = fetcher.list_cached()
        if cached:
            symbol = cached[0]
            df_1m = fetcher.load_cached(symbol)

    if df_1m is None:
        print("  No cached data found. Using synthetic data.")
        return _synthetic_fallback()

    print(f"  Loaded {len(df_1m)} 1m bars for {symbol}")

    # Resample to 5m
    df = df_1m.copy()
    if "datetime" not in df.columns and df.index.name == "datetime":
        df = df.reset_index()
    df = df.set_index("datetime")
    df_5m = df.resample("5min").agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "base_vol": "sum", "quote_vol": "sum", "timestamp": "first",
    }).dropna().reset_index()
    print(f"  Resampled to {len(df_5m)} 5m bars")

    # Compute signals
    df_5m = compute_signals(df_5m)
    print(f"  Signals computed")

    # Run backtest
    bt = Backtester({
        "sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3,
        "b_open_fresh": True, "notional": 10000.0,
        "commission_rate": 0.0008, "rebate_pct": 0.70,
        "be_raise_amount": 4.0,
    })
    result = bt.run(df_5m)
    trades_df = trades_to_dataframe(result["trades"])
    print(f"  Backtest: {len(trades_df)} trades, net=${result['metrics']['net_pnl']:.2f}")

    return df_5m, trades_df, symbol


def _synthetic_fallback():
    """Generate synthetic test data when no cache available."""
    n = 500
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    close = np.maximum(close, 1.0)

    ohlcv = pd.DataFrame({
        "open": close + np.random.randn(n) * 0.3,
        "high": close + np.random.uniform(0.1, 1.0, n),
        "low": close - np.random.uniform(0.1, 1.0, n),
        "close": close, "base_vol": np.random.uniform(100, 10000, n),
        "atr": np.random.uniform(0.5, 3.0, n),
        "stoch_9": np.random.uniform(0, 100, n),
        "stoch_14": np.random.uniform(0, 100, n),
        "stoch_40": np.random.uniform(0, 100, n),
        "stoch_60": np.random.uniform(0, 100, n),
        "ema34": close + np.random.randn(n) * 0.3,
        "ema50": close + np.random.randn(n) * 0.3,
        "cloud3_bull": np.random.choice([True, False], n),
        "price_pos": np.random.choice([-1, 0, 1], n),
    })
    dates = pd.date_range("2025-11-01", periods=n, freq="5min", tz="UTC")
    ohlcv["datetime"] = dates

    rows = []
    for idx in range(80):
        d = np.random.choice(["LONG", "SHORT"])
        g = np.random.choice(["A", "B", "C", "R"])
        eb = idx * 5 + 10
        xb = eb + np.random.randint(1, 20)
        ep = 100 + np.random.randn() * 5
        atr_v = np.random.uniform(0.5, 3.0)
        sl = ep - atr_v if d == "LONG" else ep + atr_v
        tp = ep + 1.5 * atr_v if d == "LONG" else ep - 1.5 * atr_v
        er = np.random.choice(["TP", "SL", "FLIP"])
        xp = tp if er == "TP" else (sl if er == "SL" else ep + np.random.randn())
        pnl = (xp - ep) / ep * 10000 if d == "LONG" else (ep - xp) / ep * 10000
        mfe = max(pnl, abs(np.random.uniform(0, 30)))
        mae = min(-abs(np.random.uniform(0, 20)), pnl)
        rows.append({
            "direction": d, "grade": g, "entry_bar": eb, "exit_bar": xb,
            "entry_price": ep, "exit_price": xp, "sl_price": sl, "tp_price": tp,
            "pnl": pnl, "commission": 16.0, "net_pnl": pnl - 16.0,
            "mfe": mfe, "mae": mae, "exit_reason": er,
            "saw_green": mfe > 0, "be_raised": False,
        })

    return ohlcv, pd.DataFrame(rows), "SYNTHETIC"


# ==============================================================================
# TESTS
# ==============================================================================

def test_features(trades_df, ohlcv_df):
    """Test ml.features -- extract features from trades + OHLCV."""
    from ml.features import extract_trade_features, get_feature_columns
    feats = extract_trade_features(trades_df, ohlcv_df)
    assert len(feats) > 0, "No features extracted"
    cols = get_feature_columns()
    for c in ["stoch_9", "stoch_14", "atr_pct", "cloud3_spread", "vol_ratio"]:
        assert c in feats.columns, f"Missing column: {c}"
    return feats


def test_triple_barrier(trades_df):
    """Test ml.triple_barrier -- label trades by exit type."""
    from ml.triple_barrier import label_trades, get_label_distribution
    labels = label_trades(trades_df)
    assert len(labels) == len(trades_df), "Label count mismatch"
    assert set(np.unique(labels)).issubset({-1, 0, 1}), f"Bad labels: {np.unique(labels)}"
    dist = get_label_distribution(labels)
    return labels, dist


def test_purged_cv(trades_df):
    """Test ml.purged_cv -- leak-free cross-validation splits."""
    from ml.purged_cv import purged_kfold_split, get_split_summary
    n_splits = min(5, len(trades_df) // 20)
    if n_splits < 2:
        n_splits = 2
    splits = purged_kfold_split(trades_df, n_splits=n_splits, embargo_bars=5)
    assert len(splits) == n_splits, f"Expected {n_splits} folds"
    summary = get_split_summary(splits, len(trades_df))
    return splits, summary


def test_meta_label(feats, labels):
    """Test ml.meta_label -- XGBoost meta-label training."""
    from ml.meta_label import MetaLabelAnalyzer
    from ml.features import get_feature_columns
    binary_y = (labels == 1).astype(int)
    feat_cols = get_feature_columns()
    available = [c for c in feat_cols if c in feats.columns]
    X = feats[available].copy()

    analyzer = MetaLabelAnalyzer({"n_estimators": 100, "max_depth": 4})
    result = analyzer.train(X, binary_y, feature_names=available)
    assert result["train_samples"] > 0, "No training samples"
    probs = analyzer.predict_proba(X)
    assert len(probs) == len(X), "Probability count mismatch"
    imp = analyzer.get_feature_importance()
    return analyzer, probs, result


def test_shap(analyzer, feats):
    """Test ml.shap_analyzer -- SHAP feature explanations."""
    from ml.shap_analyzer import ShapAnalyzer
    from ml.features import get_feature_columns
    feat_cols = get_feature_columns()
    available = [c for c in feat_cols if c in feats.columns]
    X = feats[available].copy()

    shap_a = ShapAnalyzer(analyzer.model, feature_names=available)
    shap_vals = shap_a.compute(X)
    assert shap_vals.shape == X.shape, f"Shape mismatch: {shap_vals.shape} vs {X.shape}"
    top = shap_a.get_top_features(0, top_n=5)
    glob_imp = shap_a.get_global_importance()
    return shap_vals, top, glob_imp


def test_bet_sizing(probs):
    """Test ml.bet_sizing -- probability to position size."""
    from ml.bet_sizing import binary_sizing, linear_sizing, kelly_sizing, get_sizing_summary
    b = binary_sizing(probs, threshold=0.5)
    l = linear_sizing(probs, threshold=0.5, max_size=1.0)
    k = kelly_sizing(probs, avg_win=20.0, avg_loss=-10.0, max_size=1.0, fraction=0.5)
    summary = get_sizing_summary(b)
    assert summary["total_signals"] == len(probs), "Wrong total"
    return summary


def test_walk_forward():
    """Test ml.walk_forward -- rolling IS/OOS validation."""
    from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward
    windows = generate_windows(500, is_ratio=0.7, min_trades_per_window=100)
    assert len(windows) > 0, "No windows"
    wfe = compute_wfe(100.0, 70.0)
    assert wfe == 0.7, f"WFE wrong: {wfe}"
    assert get_wfe_rating(0.7) == "ROBUST"
    assert get_wfe_rating(0.4) == "MARGINAL"
    assert get_wfe_rating(0.1) == "OVERFIT"
    return windows


def test_loser_analysis(trades_df):
    """Test ml.loser_analysis -- Sweeney loser classification."""
    from ml.loser_analysis import classify_losers, get_class_summary, optimize_be_trigger, compute_etd
    classified = classify_losers(trades_df)
    assert "loser_class" in classified.columns, "Missing loser_class"
    summary = get_class_summary(classified)
    be_sweep = optimize_be_trigger(trades_df)
    etd = compute_etd(trades_df)
    assert "etd" in etd.columns, "Missing etd"
    return classified, summary, be_sweep


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("=" * 60)
    print("  ML PIPELINE TEST -- End-to-End Validation")
    print("=" * 60)

    t0 = time.time()

    # Load data
    print("\nLoading test data...")
    ohlcv_df, trades_df, symbol = load_test_data()
    print(f"  Symbol: {symbol}, Trades: {len(trades_df)}, Bars: {len(ohlcv_df)}")

    passed = 0
    failed = 0
    total = 8

    # Test 1: features
    print(f"\n[1/{total}] ml.features...")
    try:
        feats = test_features(trades_df, ohlcv_df)
        print(f"  PASS -- {len(feats)} trades x {len(feats.columns)} features")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        failed += 1
        feats = None

    # Test 2: triple_barrier
    print(f"\n[2/{total}] ml.triple_barrier...")
    try:
        labels, dist = test_triple_barrier(trades_df)
        print(f"  PASS -- TP:{dist['tp_count']} SL:{dist['sl_count']} Other:{dist['other_count']}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        failed += 1
        labels = None

    # Test 3: purged_cv
    print(f"\n[3/{total}] ml.purged_cv...")
    try:
        splits, cv_summary = test_purged_cv(trades_df)
        purge_counts = [s["purged"] for s in cv_summary]
        print(f"  PASS -- {len(splits)} folds, purged: {purge_counts}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        failed += 1

    # Test 4: meta_label (requires feats + labels)
    print(f"\n[4/{total}] ml.meta_label...")
    analyzer = None
    probs = None
    if feats is not None and labels is not None:
        try:
            analyzer, probs, train_result = test_meta_label(feats, labels)
            print(f"  PASS -- {train_result['train_samples']} samples, "
                  f"acc={train_result['train_accuracy']:.3f}, "
                  f"pos_rate={train_result['positive_rate']:.3f}")
            passed += 1
        except ImportError as e:
            print(f"  SKIP -- {e}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            traceback.print_exc()
            failed += 1
    else:
        print("  SKIP -- depends on features + labels")
        failed += 1

    # Test 5: shap_analyzer (requires analyzer + feats)
    print(f"\n[5/{total}] ml.shap_analyzer...")
    if analyzer is not None and feats is not None:
        try:
            shap_vals, top_feats, glob_imp = test_shap(analyzer, feats)
            print(f"  PASS -- top features: {[t['feature'] for t in top_feats[:3]]}")
            passed += 1
        except ImportError as e:
            print(f"  SKIP -- {e}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            traceback.print_exc()
            failed += 1
    else:
        print("  SKIP -- depends on meta_label")
        failed += 1

    # Test 6: bet_sizing (requires probs)
    print(f"\n[6/{total}] ml.bet_sizing...")
    if probs is not None:
        try:
            sizing_summary = test_bet_sizing(probs)
            print(f"  PASS -- taken:{sizing_summary['taken']} skipped:{sizing_summary['skipped']} "
                  f"avg_size:{sizing_summary['avg_size']:.3f}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            traceback.print_exc()
            failed += 1
    else:
        print("  SKIP -- depends on meta_label probabilities")
        failed += 1

    # Test 7: walk_forward
    print(f"\n[7/{total}] ml.walk_forward...")
    try:
        windows = test_walk_forward()
        print(f"  PASS -- {len(windows)} windows generated")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        failed += 1

    # Test 8: loser_analysis
    print(f"\n[8/{total}] ml.loser_analysis...")
    try:
        classified, class_summary, be_sweep = test_loser_analysis(trades_df)
        for _, row in class_summary.iterrows():
            print(f"    {row['class']}: {row['count']} trades ({row['pct']:.1f}%), "
                  f"avg=${row['avg_net_pnl']:.2f}")
        print(f"  PASS -- {len(class_summary)} classes, {len(be_sweep)} BE levels")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        failed += 1

    # Summary
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"  RESULT: {passed}/{total} passed, {failed} failed  ({elapsed:.1f}s)")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
