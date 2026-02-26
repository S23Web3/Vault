"""
Test all 5 dashboard tab data flows without Streamlit.
Validates ML integration works end-to-end with real cached data.

Run: python staging/test_dashboard_ml.py
"""

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

import numpy as np
import pandas as pd
import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)

from data.fetcher import BybitFetcher
from signals.four_pillars import compute_signals
from engine.backtester import Backtester


def resample_5m(df_1m):
    df = df_1m.copy()
    if 'datetime' not in df.columns:
        if df.index.name == 'datetime':
            df = df.reset_index()
    df = df.set_index('datetime')
    ohlcv = df.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
        'base_vol': 'sum', 'quote_vol': 'sum', 'timestamp': 'first'
    }).dropna()
    return ohlcv.reset_index()


def main():
    print("=" * 60)
    print("  DASHBOARD ML TAB TEST (no Streamlit)")
    print("=" * 60)
    print()

    # Load data
    cache_dir = str(PROJECT / "data" / "cache")
    df_1m = BybitFetcher(cache_dir=cache_dir).load_cached("RIVERUSDT")
    if df_1m is None:
        print("  [SKIP] No RIVERUSDT cache")
        sys.exit(0)

    df = resample_5m(df_1m)
    print(f"  Loaded {len(df)} 5m bars")

    # Compute signals + backtest
    df_sig = compute_signals(df.copy())
    bt = Backtester({"sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3,
                     "b_open_fresh": True, "notional": 10000.0,
                     "commission_rate": 0.0008, "rebate_pct": 0.70,
                     "be_raise_amount": 2.0})
    results = bt.run(df_sig)
    trades_df = results["trades_df"]
    m = results["metrics"]
    print(f"  Backtest: {m['total_trades']} trades, net=${m['net_pnl']:.2f}")
    print()

    tests = []

    # Tab 1: Overview (just metrics)
    try:
        assert m["total_trades"] > 0
        assert "win_rate" in m and "sharpe" in m
        tests.append(("Tab 1: Overview", True, f"{m['total_trades']} trades"))
    except Exception as e:
        tests.append(("Tab 1: Overview", False, str(e)))

    # Tab 2: Trade Analysis
    try:
        assert "net_pnl" in trades_df.columns
        assert "grade" in trades_df.columns
        assert "direction" in trades_df.columns
        grade_stats = trades_df.groupby("grade").agg(Count=("net_pnl", "count")).reset_index()
        assert len(grade_stats) > 0
        tests.append(("Tab 2: Trade Analysis", True, f"{len(grade_stats)} grades"))
    except Exception as e:
        tests.append(("Tab 2: Trade Analysis", False, str(e)))

    # Tab 3: MFE/MAE & Losers
    try:
        from ml.loser_analysis import classify_losers, get_class_summary, optimize_be_trigger, compute_etd
        classified = classify_losers(trades_df)
        assert "loser_class" in classified.columns
        summary = get_class_summary(classified)
        assert len(summary) > 0
        be_opt = optimize_be_trigger(trades_df)
        assert len(be_opt) > 0
        etd = compute_etd(trades_df)
        assert "etd" in etd.columns
        tests.append(("Tab 3: MFE/MAE & Losers", True,
                      f"{len(summary)} classes, {len(be_opt)} BE levels"))
    except Exception as e:
        tests.append(("Tab 3: MFE/MAE & Losers", False, str(e)))

    # Tab 4: ML Meta-Label
    try:
        from ml.features import extract_trade_features, get_feature_columns
        from ml.triple_barrier import label_trades, get_label_distribution
        from ml.meta_label import MetaLabelAnalyzer
        from ml.bet_sizing import binary_sizing, get_sizing_summary

        feat_df = extract_trade_features(trades_df, df_sig)
        feature_cols = get_feature_columns()
        avail_cols = [c for c in feature_cols if c in feat_df.columns]
        assert len(avail_cols) > 0, "No feature columns"

        labels = label_trades(trades_df)
        dist = get_label_distribution(labels)
        assert dist["total"] == len(trades_df)

        y_binary = (labels == 1).astype(int)
        X = feat_df[avail_cols]
        analyzer = MetaLabelAnalyzer(params={"n_estimators": 50, "max_depth": 3})
        train_result = analyzer.train(X.values, y_binary, feature_names=avail_cols)
        assert train_result["train_samples"] > 0

        importance = analyzer.get_feature_importance()
        assert len(importance) > 0

        proba = analyzer.predict_proba(X.values)
        sizes = binary_sizing(proba, threshold=0.5)
        sizing_summary = get_sizing_summary(sizes)
        assert sizing_summary["total_signals"] == len(trades_df)

        tests.append(("Tab 4: ML Meta-Label", True,
                      f"acc={train_result['train_accuracy']:.3f}, "
                      f"taken={sizing_summary['taken']}"))
    except Exception as e:
        tests.append(("Tab 4: ML Meta-Label", False, str(e)))

    # Tab 5: Validation
    try:
        from ml.purged_cv import purged_kfold_split, get_split_summary
        from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward

        splits = purged_kfold_split(trades_df, n_splits=5, embargo_bars=10)
        split_summary = get_split_summary(splits, len(trades_df))
        assert len(split_summary) == 5

        windows = generate_windows(len(trades_df))
        assert len(windows) > 0
        rating = get_wfe_rating(0.7)
        assert rating == "ROBUST"

        tests.append(("Tab 5: Validation", True,
                      f"{len(splits)} folds, {len(windows)} WF windows"))
    except Exception as e:
        tests.append(("Tab 5: Validation", False, str(e)))

    # Results
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print()
    passed = 0
    for name, ok, msg in tests:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"  [{status}] {name}: {msg}")

    print()
    print(f"  {passed}/{len(tests)} passed")
    print("=" * 60)
    sys.exit(0 if passed == len(tests) else 1)


if __name__ == "__main__":
    main()
