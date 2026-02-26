r"""
Run full ML analysis pipeline on a single coin.

End-to-end flow:
  1. Load cached 1m data, resample to target timeframe
  2. Compute Four Pillars signals (v3.8 with Cloud 3 filter)
  3. Run backtest with specified BE config
  4. Extract features at entry time (ml/features.py)
  5. Label trades by exit barrier (ml/triple_barrier.py)
  6. Train XGBoost meta-label model (ml/meta_label.py)
  7. Compute SHAP explanations (ml/shap_analyzer.py)
  8. Apply bet sizing (ml/bet_sizing.py)
  9. Classify losers (ml/loser_analysis.py)
  10. Walk-forward validation (ml/walk_forward.py)
  11. Save all artifacts to data/output/ml/

Vince = analysis engine. User sets parameters and trains the model.
This script surfaces the analysis. User decides what to do with it.

Run:  python scripts/run_ml_analysis.py --symbol RIVERUSDT --timeframe 5m
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""

import sys
import argparse
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd


def resample(df_1m, tf_minutes):
    """Resample 1m data to target timeframe."""
    df = df_1m.copy()
    if "datetime" not in df.columns and df.index.name == "datetime":
        df = df.reset_index()
    df = df.set_index("datetime")
    rule = f"{tf_minutes}min"
    ohlcv = df.resample(rule).agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "base_vol": "sum", "quote_vol": "sum", "timestamp": "first",
    }).dropna().reset_index()
    return ohlcv


def main():
    parser = argparse.ArgumentParser(description="Vince ML Analysis Pipeline")
    parser.add_argument("--symbol", type=str, required=True, help="Symbol (e.g. RIVERUSDT)")
    parser.add_argument("--timeframe", type=str, default="5m", help="Timeframe (1m, 5m, 15m)")
    parser.add_argument("--sl", type=float, default=1.0, help="SL ATR multiplier")
    parser.add_argument("--tp", type=float, default=1.5, help="TP ATR multiplier")
    parser.add_argument("--cooldown", type=int, default=3, help="Min bars between entries")
    parser.add_argument("--be-raise", type=float, default=0.0, help="Fixed BE raise ($)")
    parser.add_argument("--be-trigger-atr", type=float, default=0.0, help="ATR-based BE trigger")
    parser.add_argument("--be-lock-atr", type=float, default=0.0, help="ATR-based BE lock level")
    parser.add_argument("--xgb-estimators", type=int, default=200, help="XGBoost n_estimators")
    parser.add_argument("--xgb-depth", type=int, default=4, help="XGBoost max_depth")
    parser.add_argument("--threshold", type=float, default=0.5, help="Bet sizing threshold")
    parser.add_argument("--save", action="store_true", help="Save artifacts to data/output/ml/")
    parser.add_argument("--save-db", action="store_true", help="Save backtest to PostgreSQL")
    args = parser.parse_args()

    # Parse timeframe to minutes
    tf_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60}
    tf_min = tf_map.get(args.timeframe)
    if tf_min is None:
        print(f"ERROR: Unknown timeframe {args.timeframe}. Use: {list(tf_map.keys())}")
        sys.exit(1)

    tag = f"{args.symbol}_{args.timeframe}"
    t0 = time.time()

    print("=" * 70)
    print(f"  VINCE ML ANALYSIS -- {args.symbol} {args.timeframe}")
    print("=" * 70)

    # ========== STEP 1: Load data ==========
    print("\n[1] Loading cached data...")
    from data.fetcher import BybitFetcher
    fetcher = BybitFetcher(cache_dir=str(ROOT / "data" / "cache"))
    df_1m = fetcher.load_cached(args.symbol)
    if df_1m is None:
        print(f"  ERROR: No cached data for {args.symbol}. Run fetch_data.py first.")
        sys.exit(1)
    print(f"  {len(df_1m)} 1m bars loaded")

    # ========== STEP 2: Resample ==========
    if tf_min > 1:
        print(f"\n[2] Resampling to {args.timeframe}...")
        df = resample(df_1m, tf_min)
        print(f"  {len(df)} {args.timeframe} bars")
    else:
        df = df_1m.copy()
        print(f"\n[2] Using 1m data directly ({len(df)} bars)")

    # ========== STEP 3: Compute signals ==========
    print("\n[3] Computing Four Pillars v3.8 signals...")
    from signals.four_pillars import compute_signals
    df = compute_signals(df)
    print(f"  Signals computed on {len(df)} bars")

    # ========== STEP 4: Run backtest ==========
    print("\n[4] Running backtest...")
    from engine.backtester import Backtester
    from engine.metrics import trades_to_dataframe

    bt_params = {
        "sl_mult": args.sl, "tp_mult": args.tp, "cooldown": args.cooldown,
        "b_open_fresh": True, "notional": 10000.0,
        "commission_rate": 0.0008, "rebate_pct": 0.70,
        "be_raise_amount": args.be_raise,
        "be_trigger_atr": args.be_trigger_atr,
        "be_lock_atr": args.be_lock_atr,
    }
    bt = Backtester(bt_params)
    result = bt.run(df)
    trades_df = trades_to_dataframe(result["trades"])
    m = result["metrics"]

    if m["total_trades"] == 0:
        print("  No trades generated. Adjust parameters.")
        sys.exit(1)

    print(f"  {m['total_trades']} trades, WR {m['win_rate']:.1%}, "
          f"Net ${m['net_pnl']:.2f}, Exp ${m['expectancy']:.2f}/trade")

    # ========== STEP 5: Extract features ==========
    print("\n[5] Extracting trade features...")
    from ml.features import extract_trade_features, get_feature_columns
    feats = extract_trade_features(trades_df, df)
    feat_cols = get_feature_columns()
    available_cols = [c for c in feat_cols if c in feats.columns]
    X = feats[available_cols].copy()
    print(f"  {len(feats)} trades x {len(available_cols)} features")

    # ========== STEP 6: Label trades ==========
    print("\n[6] Labeling trades (triple barrier)...")
    from ml.triple_barrier import label_trades, get_label_distribution
    labels = label_trades(trades_df)
    dist = get_label_distribution(labels)
    print(f"  TP: {dist['tp_count']} ({dist['tp_pct']:.1%}) | "
          f"SL: {dist['sl_count']} ({dist['sl_pct']:.1%}) | "
          f"Other: {dist['other_count']} ({dist['other_pct']:.1%})")

    # Binary labels for meta-labeling: TP=1, else=0
    binary_y = (labels == 1).astype(int)

    # ========== STEP 7: Train meta-label model ==========
    print("\n[7] Training XGBoost meta-label model...")
    try:
        from ml.meta_label import MetaLabelAnalyzer
        analyzer = MetaLabelAnalyzer({
            "n_estimators": args.xgb_estimators,
            "max_depth": args.xgb_depth,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        })
        train_result = analyzer.train(X, binary_y, feature_names=available_cols)
        probs = analyzer.predict_proba(X)
        imp = analyzer.get_feature_importance()

        print(f"  Trained: {train_result['train_samples']} samples, "
              f"acc={train_result['train_accuracy']:.3f}")
        print(f"  Top features:")
        for _, row in imp.head(5).iterrows():
            print(f"    {row['feature']:>20s}  {row['importance']:.4f}")

    except ImportError:
        print("  SKIP -- xgboost not installed")
        analyzer = None
        probs = None

    # ========== STEP 8: SHAP explanations ==========
    if analyzer is not None:
        print("\n[8] Computing SHAP explanations...")
        try:
            from ml.shap_analyzer import ShapAnalyzer
            shap_a = ShapAnalyzer(analyzer.model, feature_names=available_cols)
            shap_vals = shap_a.compute(X)
            glob_imp = shap_a.get_global_importance()

            print(f"  Global SHAP importance:")
            for _, row in glob_imp.head(5).iterrows():
                print(f"    {row['feature']:>20s}  {row['mean_abs_shap']:.4f}")

        except ImportError:
            print("  SKIP -- shap not installed")
            shap_a = None
    else:
        print("\n[8] SKIP -- no model trained")
        shap_a = None

    # ========== STEP 9: Bet sizing ==========
    if probs is not None:
        print("\n[9] Applying bet sizing...")
        from ml.bet_sizing import binary_sizing, linear_sizing, kelly_sizing, get_sizing_summary

        binary_sizes = binary_sizing(probs, threshold=args.threshold)
        linear_sizes = linear_sizing(probs, threshold=args.threshold, max_size=1.0)

        b_summary = get_sizing_summary(binary_sizes)
        l_summary = get_sizing_summary(linear_sizes)

        print(f"  Binary (t={args.threshold}): "
              f"take {b_summary['taken']}, skip {b_summary['skipped']} "
              f"({b_summary['skip_rate']:.1%} filtered)")
        print(f"  Linear (t={args.threshold}): "
              f"avg_size {l_summary['avg_size']:.3f}")

        # What would filtered results look like?
        filtered_idx = binary_sizes > 0
        if filtered_idx.sum() > 0:
            filtered_trades = trades_df.iloc[:len(filtered_idx)][filtered_idx]
            filtered_net = (filtered_trades["pnl"] - filtered_trades["commission"]).sum()
            filtered_exp = (filtered_trades["pnl"] - filtered_trades["commission"]).mean()
            print(f"  Filtered portfolio: {filtered_idx.sum()} trades, "
                  f"Net ${filtered_net:.2f}, Exp ${filtered_exp:.2f}/trade")
    else:
        print("\n[9] SKIP -- no probabilities")

    # ========== STEP 10: Loser analysis ==========
    print("\n[10] Classifying losers (Sweeney)...")
    from ml.loser_analysis import classify_losers, get_class_summary, optimize_be_trigger, compute_etd

    classified = classify_losers(trades_df)
    class_summary = get_class_summary(classified)
    print(f"  Loser classes:")
    for _, row in class_summary.iterrows():
        print(f"    {row['class']}: {row['count']:>4} trades ({row['pct']:>5.1f}%), "
              f"avg=${row['avg_net_pnl']:>7.2f}, total=${row['total_pnl']:>10.2f}")

    be_sweep = optimize_be_trigger(trades_df)
    if len(be_sweep) > 0:
        best_be = be_sweep.loc[be_sweep["net_impact"].idxmax()]
        print(f"  Optimal BE trigger: ${best_be['trigger']:.2f} "
              f"(saves {best_be['losers_saved']} losers, "
              f"kills {best_be['winners_killed']} winners, "
              f"net ${best_be['net_impact']:.2f})")

    etd = compute_etd(trades_df)
    print(f"  Avg ETD: ${etd['etd'].mean():.2f} (profit given back per trade)")

    # ========== STEP 11: Walk-forward validation ==========
    if analyzer is not None:
        print("\n[11] Walk-forward validation...")
        from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward
        from ml.purged_cv import purged_kfold_split

        n_trades = len(X)
        if n_trades >= 200:
            windows = generate_windows(n_trades, is_ratio=0.7, min_trades_per_window=100)
            window_results = []

            for w_idx, w in enumerate(windows):
                is_X = X.iloc[w["is_start"]:w["is_end"]]
                is_y = binary_y[w["is_start"]:w["is_end"]]
                oos_X = X.iloc[w["oos_start"]:w["oos_end"]]
                oos_y = binary_y[w["oos_start"]:w["oos_end"]]

                if len(is_X) < 20 or len(oos_X) < 10:
                    continue

                try:
                    wf_analyzer = MetaLabelAnalyzer({
                        "n_estimators": args.xgb_estimators,
                        "max_depth": args.xgb_depth,
                    })
                    wf_result = wf_analyzer.train(is_X, is_y, feature_names=available_cols)

                    # IS metric: accuracy
                    is_preds = wf_analyzer.model.predict(is_X.values)
                    is_acc = np.mean(is_preds == is_y)

                    # OOS metric: accuracy
                    oos_preds = wf_analyzer.model.predict(oos_X.values)
                    oos_acc = np.mean(oos_preds == oos_y)

                    window_results.append({
                        "window": w_idx, "is_metric": is_acc, "oos_metric": oos_acc,
                    })
                except Exception:
                    continue

            if window_results:
                wf_summary = summarize_walk_forward(window_results)
                print(f"  {wf_summary['n_windows']} windows, "
                      f"avg WFE={wf_summary['avg_wfe']:.3f}, "
                      f"rating={wf_summary['rating']}")
                for wr in window_results:
                    wfe = compute_wfe(wr["is_metric"], wr["oos_metric"])
                    print(f"    Window {wr['window']}: IS={wr['is_metric']:.3f} "
                          f"OOS={wr['oos_metric']:.3f} WFE={wfe:.3f} "
                          f"({get_wfe_rating(wfe)})")
            else:
                print("  Not enough data for walk-forward windows")
        else:
            print(f"  SKIP -- need 200+ trades, have {n_trades}")
    else:
        print("\n[11] SKIP -- no model trained")

    # ========== SAVE ARTIFACTS ==========
    if args.save:
        print("\n[SAVE] Saving artifacts to data/output/ml/...")
        output_dir = ROOT / "data" / "output" / "ml"
        output_dir.mkdir(parents=True, exist_ok=True)

        feats.to_parquet(output_dir / f"features_{tag}.parquet", index=False)
        np.save(str(output_dir / f"labels_{tag}.npy"), labels)
        classified.to_parquet(output_dir / f"loser_classification_{tag}.parquet", index=False)
        trades_df.to_csv(output_dir / f"trades_{tag}.csv", index=False)

        if analyzer is not None:
            analyzer.model.save_model(str(output_dir / f"meta_model_{tag}.json"))
            imp.to_csv(output_dir / f"feature_importance_{tag}.csv", index=False)
        if shap_a is not None and shap_a.shap_values is not None:
            np.save(str(output_dir / f"shap_values_{tag}.npy"), shap_a.shap_values)
            glob_imp.to_csv(output_dir / f"shap_importance_{tag}.csv", index=False)

        print(f"  Saved to {output_dir}")

    # ========== SAVE TO DB ==========
    if args.save_db:
        print("\n[SAVE-DB] Saving backtest to PostgreSQL...")
        try:
            from data.db import save_backtest_run
            run_id = save_backtest_run(
                symbol=args.symbol, timeframe=args.timeframe,
                params=bt_params, metrics=m,
                trades=result["trades"],
                equity_curve=result.get("equity_curve"),
                notes=f"ML analysis run",
            )
            print(f"  Saved: run_id={run_id}")
        except Exception as e:
            print(f"  DB ERROR: {e}")

    # ========== SUMMARY ==========
    elapsed = time.time() - t0
    print("\n" + "=" * 70)
    print(f"  ANALYSIS COMPLETE -- {args.symbol} {args.timeframe}  ({elapsed:.1f}s)")
    print("=" * 70)
    print(f"  Trades:     {m['total_trades']}")
    print(f"  Win Rate:   {m['win_rate']:.1%}")
    print(f"  Net P&L:    ${m['net_pnl']:.2f}")
    print(f"  Expectancy: ${m['expectancy']:.2f}/trade")
    print(f"  Sharpe:     {m['sharpe']:.3f}")
    print(f"  LSG:        {m['pct_losers_saw_green']:.0%}")
    if analyzer is not None:
        print(f"  ML Acc:     {train_result['train_accuracy']:.3f}")
    if probs is not None:
        print(f"  ML Filter:  {b_summary['skip_rate']:.0%} trades filtered at t={args.threshold}")


if __name__ == "__main__":
    main()
