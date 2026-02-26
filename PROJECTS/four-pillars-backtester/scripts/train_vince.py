"""
Vince ML Training Pipeline -- per-coin XGBoost auditor.
12-step pipeline using strategy plugin system.

Run single coin:
  python scripts/train_vince.py --symbol RIVERUSDT
Run with walk-forward:
  python scripts/train_vince.py --symbol RIVERUSDT --walk-forward
Run all coins:
  python scripts/train_vince.py --symbol ALL --top 20
"""

import sys
import json
import time
import logging
import argparse
import traceback
import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CACHE_DIR = ROOT / "data" / "cache"
MODELS_DIR = ROOT / "models"
POOL_FILE = ROOT / "data" / "coin_pools.json"


def gpu_preflight():
    """Verify CUDA is available for XGBoost. Fail fast if not."""
    try:
        from xgboost import XGBClassifier
        test_model = XGBClassifier(device="cuda", tree_method="hist",
                                   n_estimators=1, verbosity=0)
        test_model.fit([[0, 1], [1, 0]], [0, 1])
        log.info("GPU pre-flight: CUDA verified for XGBoost")
    except Exception as e:
        log.error("GPU pre-flight FAILED: %s", e)
        log.error("CUDA is MANDATORY. Install xgboost with GPU support.")
        sys.exit(1)


def load_pools() -> dict:
    """Load coin pool assignments from JSON."""
    if not POOL_FILE.exists():
        log.error("coin_pools.json not found. Run build_data_infra_v1.py first.")
        sys.exit(1)
    with open(POOL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_symbols(args, pools: dict) -> list:
    """Resolve symbol list from CLI args and pool assignments."""
    assignments = pools.get("assignments", {})

    if args.symbol == "ALL":
        # Only train on Pool A coins
        symbols = [s for s, p in assignments.items() if p == "A"]
        log.info("ALL mode: %d Pool A coins", len(symbols))
    else:
        symbols = [args.symbol]

    # Filter by pool (never train on Pool C)
    filtered = []
    for sym in symbols:
        pool = assignments.get(sym, "C")
        if pool == "C":
            log.warning("SKIP %s: Pool C (holdout, never train)", sym)
            continue
        filtered.append(sym)

    if args.top and args.top < len(filtered):
        filtered = filtered[:args.top]
        log.info("Limited to top %d coins", args.top)

    return filtered


def find_parquet(symbol: str, timeframe: str) -> Path:
    """Locate OHLCV parquet file for a symbol."""
    path = CACHE_DIR / (symbol + "_" + timeframe + ".parquet")
    if path.exists():
        return path
    # Try without underscore
    path2 = CACHE_DIR / (symbol + timeframe + ".parquet")
    if path2.exists():
        return path2
    return path  # will fail at load time with clear error


def train_single_coin(symbol: str, timeframe: str, strategy, args) -> dict:
    """Train XGBoost auditor for one coin. Returns report dict."""
    ts_start = time.time()
    report = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy.name,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "label_mode": args.label_mode,
        "status": "FAILED",
    }

    # Step 1: Load OHLCV
    pq_path = find_parquet(symbol, timeframe)
    if not pq_path.exists():
        log.warning("SKIP %s: no parquet at %s", symbol, pq_path)
        report["error"] = "No parquet file"
        return report

    df = pd.read_parquet(pq_path)
    log.info("[%s] Loaded %d bars from %s", symbol, len(df), pq_path.name)

    # Validate required OHLCV columns
    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        log.warning("SKIP %s: missing columns: %s", symbol, ", ".join(missing))
        report["error"] = "Missing columns: " + ", ".join(missing)
        return report

    # Ensure volume column exists
    if "base_vol" not in df.columns and "volume" in df.columns:
        df["base_vol"] = df["volume"]

    # Ensure datetime is accessible
    if "datetime" not in df.columns and isinstance(df.index, pd.DatetimeIndex):
        pass  # dt_series in features_v3 handles DatetimeIndex via pd.Series wrap
    elif "datetime" not in df.columns and "timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

    # Step 2-3: Enrich OHLCV with indicators
    log.info("[%s] Enriching OHLCV (ATR, stochastics, clouds)...", symbol)
    df = strategy.enrich_ohlcv(df)

    # Step 4: Generate signals
    log.info("[%s] Computing signals (state machine)...", symbol)
    df = strategy.compute_signals(df)

    # Step 5: Run backtest
    log.info("[%s] Running backtest...", symbol)
    from engine.backtester_v384 import Backtester384

    bt_params = strategy.get_backtester_params()
    if args.tp_mult is not None:
        bt_params["tp_mult"] = args.tp_mult
    if args.sl_mult is not None:
        bt_params["sl_mult"] = args.sl_mult

    bt = Backtester384(bt_params)
    bt_result = bt.run(df)
    trades_df = bt_result["trades_df"]

    if len(trades_df) < 20:
        log.warning("SKIP %s: only %d trades (need >= 20)", symbol, len(trades_df))
        report["error"] = "Too few trades: " + str(len(trades_df))
        report["n_trades"] = len(trades_df)
        return report

    log.info("[%s] Backtest: %d trades", symbol, len(trades_df))

    # Step 6: Extract features
    log.info("[%s] Extracting features...", symbol)
    X = strategy.extract_features(trades_df, df)

    # Prepend coin-level features (10 cols)
    from ml.coin_features import compute_coin_features, get_feature_names as coin_feat_names
    coin_feats = compute_coin_features(df)
    for feat_name in coin_feat_names():
        X[feat_name] = coin_feats.get(feat_name, 0.0)

    # Step 7: Label trades
    label_mode = args.label_mode
    log.info("[%s] Labeling trades (mode=%s)...", symbol, label_mode)
    y = strategy.label_trades(trades_df, mode=label_mode)

    # Guard: single-class labels cannot train a binary classifier
    n_unique = len(y.unique()) if hasattr(y, 'unique') else len(set(y))
    if n_unique < 2:
        if label_mode == "exit":
            tp_count = int((trades_df["exit_reason"] == "TP").sum())
            log.warning("[%s] Exit mode produced single class (TP exits: %d/%d). "
                        "tp_mult=%s. Auto-fallback to pnl mode.",
                        symbol, tp_count, len(trades_df), bt_params.get("tp_mult"))
            label_mode = "pnl"
            y = strategy.label_trades(trades_df, mode="pnl")
            report["label_mode_fallback"] = "exit -> pnl (no TP exits)"
            n_unique = len(y.unique()) if hasattr(y, 'unique') else len(set(y))

        if n_unique < 2:
            log.warning("SKIP %s: single class after labeling (all %s)", symbol,
                        "winners" if y.iloc[0] == 1 else "losers")
            report["error"] = "Single class: cannot train binary classifier"
            return report

    # Step 8: Grade filtering (optional)
    if args.grade_filter:
        grades_to_filter = [g.strip().upper() for g in args.grade_filter.split(",")]
        log.info("[%s] Grade filtering: removing grades %s", symbol, grades_to_filter)
        grade_mask = ~trades_df["grade"].isin(grades_to_filter)
        X = X[grade_mask.values].reset_index(drop=True)
        y = y[grade_mask.values].reset_index(drop=True)
        log.info("[%s] After grade filter: %d trades remain", symbol, len(X))

        if len(X) < 20:
            log.warning("SKIP %s: only %d trades after grade filter", symbol, len(X))
            report["error"] = "Too few trades after grade filter"
            return report

    # Select feature columns only (no leakage)
    feature_cols = strategy.get_feature_names() + coin_feat_names()
    available_cols = [c for c in feature_cols if c in X.columns]
    X_clean = X[available_cols].copy()

    # Drop columns that are entirely NaN (e.g. market cap when no metadata)
    all_nan_cols = [c for c in X_clean.columns if X_clean[c].isna().all()]
    if all_nan_cols:
        log.info("[%s] Dropping %d all-NaN columns: %s", symbol, len(all_nan_cols),
                 ", ".join(all_nan_cols))
        X_clean = X_clean.drop(columns=all_nan_cols)
        available_cols = [c for c in available_cols if c not in all_nan_cols]

    # Fill remaining sporadic NaNs with 0 (safe for tree models)
    nan_count = int(X_clean.isna().sum().sum())
    if nan_count > 0:
        log.info("[%s] Filling %d sporadic NaN values with 0", symbol, nan_count)
        X_clean = X_clean.fillna(0.0)
    report["n_features"] = len(available_cols)
    report["n_trades"] = len(X_clean)
    report["label_distribution"] = {
        "positive": int(y.sum()),
        "negative": int(len(y) - y.sum()),
        "positive_rate": float(y.mean()),
    }

    # Step 9: Validation
    from ml.purged_cv import purged_kfold_split, get_split_summary

    if args.walk_forward:
        log.info("[%s] Walk-forward validation...", symbol)
        from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward
        from ml.xgboost_trainer_v2 import train_xgboost

        windows = generate_windows(len(X_clean))
        window_results = []
        for w_idx, window in enumerate(windows):
            is_X = X_clean.iloc[window["is_start"]:window["is_end"]]
            is_y = y.iloc[window["is_start"]:window["is_end"]]
            oos_X = X_clean.iloc[window["oos_start"]:window["oos_end"]]
            oos_y = y.iloc[window["oos_start"]:window["oos_end"]]

            if len(is_X) < 20 or len(oos_X) < 10:
                continue

            try:
                is_result = train_xgboost(is_X, is_y.values, feature_names=available_cols)
                oos_pred = is_result["model"].predict(oos_X.values)
                from sklearn.metrics import accuracy_score
                is_metric = is_result["metrics"]["accuracy"]
                oos_metric = float(accuracy_score(oos_y, oos_pred))
                window_results.append({"is_metric": is_metric, "oos_metric": oos_metric})
            except Exception as e:
                log.warning("[%s] Walk-forward window %d failed: %s", symbol, w_idx, e)
                continue

        wf_summary = summarize_walk_forward(window_results)
        report["wfe_metrics"] = wf_summary
        log.info("[%s] WFE: %.3f (%s)", symbol, wf_summary["avg_wfe"], wf_summary["rating"])
    else:
        log.info("[%s] Purged K-fold CV (5 folds)...", symbol)
        n_splits = min(5, len(X_clean) // 5)
        if n_splits < 2:
            n_splits = 2
        try:
            splits = purged_kfold_split(trades_df.iloc[:len(X_clean)], n_splits=n_splits)
            split_summary = get_split_summary(splits, len(X_clean))
            report["cv_splits"] = split_summary
        except Exception as e:
            log.warning("[%s] Purged CV failed: %s", symbol, e)

    # Step 10: Train XGBoost
    log.info("[%s] Training XGBoost (GPU)...", symbol)
    from ml.xgboost_trainer_v2 import train_xgboost

    try:
        result = train_xgboost(
            X_clean, y.values,
            feature_names=available_cols,
        )
    except Exception as e:
        log.error("[%s] XGBoost training failed: %s", symbol, e)
        log.debug(traceback.format_exc())
        report["error"] = "Training failed: " + str(e)
        return report

    report["test_metrics"] = result["metrics"]
    report["feature_importance"] = result["feature_importances"].to_dict(orient="records")
    log.info("[%s] Accuracy=%.3f, F1=%.3f, AUC=%.3f",
             symbol, result["metrics"]["accuracy"],
             result["metrics"]["f1"], result["metrics"]["auc"])

    # Step 11: SHAP analysis
    log.info("[%s] SHAP analysis...", symbol)
    try:
        from ml.shap_analyzer_v2 import ShapAnalyzer
        shap_analyzer = ShapAnalyzer(result["model"], feature_names=available_cols)
        shap_analyzer.compute(X_clean)
        global_imp = shap_analyzer.get_global_importance()
        report["shap_global"] = global_imp.head(10).to_dict(orient="records")
    except Exception as e:
        log.warning("[%s] SHAP analysis failed: %s", symbol, e)
        report["shap_error"] = str(e)

    # Step 12: Bet sizing simulation
    log.info("[%s] Bet sizing simulation...", symbol)
    try:
        from ml.bet_sizing_v2 import binary_sizing, linear_sizing, kelly_sizing, get_sizing_summary

        y_proba = result["model"].predict_proba(X_clean.values)[:, 1]
        y_actual = y.values

        # Compute avg_win and avg_loss from actual trades
        net_pnl = trades_df["pnl"].values[:len(y_actual)]
        if "commission" in trades_df.columns:
            net_pnl = net_pnl - trades_df["commission"].values[:len(y_actual)]
        wins = net_pnl[net_pnl > 0]
        losses = net_pnl[net_pnl < 0]
        avg_win = float(np.mean(wins)) if len(wins) > 0 else 0.0
        avg_loss = float(np.mean(losses)) if len(losses) > 0 else 0.0

        sizing_results = {}
        for threshold in [0.4, 0.5, 0.6]:
            sizing_results["binary_" + str(threshold)] = get_sizing_summary(
                binary_sizing(y_proba, threshold)
            )
            sizing_results["linear_" + str(threshold)] = get_sizing_summary(
                linear_sizing(y_proba, threshold)
            )
        if avg_win > 0 and avg_loss < 0:
            sizing_results["kelly_0.5"] = get_sizing_summary(
                kelly_sizing(y_proba, avg_win, avg_loss, fraction=0.5)
            )

        report["bet_sizing"] = sizing_results
    except Exception as e:
        log.warning("[%s] Bet sizing failed: %s", symbol, e)
        report["bet_sizing_error"] = str(e)

    # Step 13: Save model + report
    ts_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    strategy_dir = MODELS_DIR / strategy.name
    strategy_dir.mkdir(parents=True, exist_ok=True)

    model_path = strategy_dir / (symbol + "_xgb_" + ts_str + ".json")
    result["model"].save_model(str(model_path))
    log.info("[%s] Model saved: %s", symbol, model_path)

    report["model_path"] = str(model_path)
    report["status"] = "OK"
    report["duration_sec"] = round(time.time() - ts_start, 1)

    report_path = strategy_dir / (symbol + "_report_" + ts_str + ".json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    log.info("[%s] Report saved: %s", symbol, report_path)

    return report


def main():
    """Entry point for Vince ML training pipeline."""
    parser = argparse.ArgumentParser(description="Vince ML Training Pipeline")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g. RIVERUSDT) or ALL")
    parser.add_argument("--timeframe", default="5m", help="Timeframe (default: 5m)")
    parser.add_argument("--strategy", default="four_pillars", help="Strategy plugin name")
    parser.add_argument("--label-mode", default="exit", choices=["exit", "pnl"],
                        help="Label mode: exit (TP=1/SL=0) or pnl (net>0)")
    parser.add_argument("--grade-filter", default=None,
                        help="Comma-separated grades to exclude (e.g. D,R)")
    parser.add_argument("--walk-forward", action="store_true",
                        help="Use walk-forward validation instead of purged CV")
    parser.add_argument("--tp-mult", type=float, default=None,
                        help="Override TP multiplier (ATR)")
    parser.add_argument("--sl-mult", type=float, default=None,
                        help="Override SL multiplier (ATR)")
    parser.add_argument("--top", type=int, default=None,
                        help="Limit to top N coins (ALL mode)")
    args = parser.parse_args()

    log.info("=== Vince ML Training Pipeline ===")
    log.info("Symbol: %s | Timeframe: %s | Strategy: %s | Label: %s",
             args.symbol, args.timeframe, args.strategy, args.label_mode)

    # GPU pre-flight
    gpu_preflight()

    # Load strategy
    from strategies import load_strategy
    strategy = load_strategy(args.strategy)
    log.info("Strategy loaded: %s", strategy.name)

    # Load pools
    pools = load_pools()

    # Resolve symbols
    symbols = get_symbols(args, pools)
    if not symbols:
        log.error("No symbols to process. Check pool assignments.")
        sys.exit(1)
    log.info("Processing %d symbols", len(symbols))

    # Train each coin
    results = []
    errors = []
    for idx, symbol in enumerate(symbols, 1):
        log.info("--- [%d/%d] %s ---", idx, len(symbols), symbol)
        try:
            report = train_single_coin(symbol, args.timeframe, strategy, args)
            results.append(report)
            if report["status"] != "OK":
                errors.append(symbol + ": " + report.get("error", "unknown"))
        except Exception as e:
            log.error("[%s] FATAL: %s", symbol, e)
            log.debug(traceback.format_exc())
            errors.append(symbol + ": " + str(e))
            continue

    # Summary
    ok_count = sum(1 for r in results if r.get("status") == "OK")
    log.info("=== COMPLETE ===")
    log.info("Processed: %d | OK: %d | Failed: %d", len(symbols), ok_count, len(errors))
    if errors:
        log.warning("Failures:")
        for err in errors:
            log.warning("  - %s", err)

    # Save sweep summary if ALL mode
    if args.symbol == "ALL" and results:
        summary_path = MODELS_DIR / strategy.name / "sweep_summary.json"
        summary = {
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "strategy": strategy.name,
            "timeframe": args.timeframe,
            "label_mode": args.label_mode,
            "total": len(symbols),
            "ok": ok_count,
            "failed": len(errors),
            "results": [
                {
                    "symbol": r["symbol"],
                    "status": r.get("status"),
                    "n_trades": r.get("n_trades", 0),
                    "accuracy": r.get("test_metrics", {}).get("accuracy", 0),
                    "f1": r.get("test_metrics", {}).get("f1", 0),
                    "auc": r.get("test_metrics", {}).get("auc", 0),
                }
                for r in results
            ],
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
        log.info("Sweep summary: %s", summary_path)


if __name__ == "__main__":
    main()
