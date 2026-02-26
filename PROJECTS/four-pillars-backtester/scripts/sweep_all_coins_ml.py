r"""
Sweep all cached coins through the ML pipeline.

For each coin in data/cache/:
  1. Resample to target timeframe
  2. Compute Four Pillars signals
  3. Run backtest
  4. Extract features + label trades
  5. Train XGBoost meta-label model
  6. Compute SHAP importance
  7. Apply bet sizing (binary filter)
  8. Classify losers (Sweeney)
  9. Rank by expectancy, filtered expectancy, WFE

Saves results to:
  data/output/ml/sweep_results_{timeframe}.csv
  data/output/ml/{symbol}/  (per-coin artifacts if --save-all)

Run:  python scripts/sweep_all_coins_ml.py --timeframe 5m
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""

import sys
import argparse
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUTPUT_DIR = ROOT / "data" / "output" / "ml"

import numpy as np
import pandas as pd


def check_permissions():
    """Verify write access to output directory. Create if missing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    test_file = OUTPUT_DIR / "__write_test__"
    try:
        test_file.write_text("test")
        test_file.unlink()
    except PermissionError:
        print(f"ERROR: No write permission to {OUTPUT_DIR}")
        print("Fix permissions and re-run.")
        sys.exit(1)
    print(f"  Output dir: {OUTPUT_DIR} (writable)")


def resample(df_1m, tf_minutes):
    """Resample 1m data to target timeframe."""
    df = df_1m.copy()
    if "datetime" not in df.columns and df.index.name == "datetime":
        df = df.reset_index()
    df = df.set_index("datetime")
    ohlcv = df.resample(f"{tf_minutes}min").agg({
        "open": "first", "high": "max", "low": "min", "close": "last",
        "base_vol": "sum", "quote_vol": "sum", "timestamp": "first",
    }).dropna().reset_index()
    return ohlcv


def analyze_coin(symbol, df_5m, bt_params, xgb_params, threshold, save_all):
    """
    Run full ML pipeline on one coin. Returns result dict or None on failure.
    """
    from signals.four_pillars import compute_signals
    from engine.backtester import Backtester
    from engine.metrics import trades_to_dataframe
    from ml.features import extract_trade_features, get_feature_columns
    from ml.triple_barrier import label_trades, get_label_distribution
    from ml.loser_analysis import classify_losers, get_class_summary, compute_etd

    # Signals
    df = compute_signals(df_5m.copy())

    # Backtest
    bt = Backtester(bt_params)
    result = bt.run(df)
    trades_df = trades_to_dataframe(result["trades"])
    m = result["metrics"]

    if m["total_trades"] < 30:
        return None

    # Features
    feats = extract_trade_features(trades_df, df)
    feat_cols = get_feature_columns()
    available_cols = [c for c in feat_cols if c in feats.columns]
    X = feats[available_cols].copy()

    # Labels
    labels = label_trades(trades_df)
    dist = get_label_distribution(labels)
    binary_y = (labels == 1).astype(int)

    # Meta-label
    ml_acc = 0.0
    ml_skip_rate = 0.0
    filtered_net = 0.0
    filtered_exp = 0.0
    filtered_trades = 0
    top_feature = ""
    wfe_avg = 0.0
    wfe_rating = "N/A"

    try:
        from ml.meta_label import MetaLabelAnalyzer
        analyzer = MetaLabelAnalyzer(xgb_params)
        train_result = analyzer.train(X, binary_y, feature_names=available_cols)
        ml_acc = train_result["train_accuracy"]

        probs = analyzer.predict_proba(X)

        # Bet sizing
        from ml.bet_sizing import binary_sizing, get_sizing_summary
        sizes = binary_sizing(probs, threshold=threshold)
        sizing = get_sizing_summary(sizes)
        ml_skip_rate = sizing["skip_rate"]

        # Filtered results
        mask = sizes > 0
        if mask.sum() > 0:
            ft = trades_df.iloc[:len(mask)][mask]
            filtered_net = (ft["pnl"] - ft["commission"]).sum()
            filtered_exp = (ft["pnl"] - ft["commission"]).mean()
            filtered_trades = int(mask.sum())

        # Feature importance
        imp = analyzer.get_feature_importance()
        if len(imp) > 0:
            top_feature = imp.iloc[0]["feature"]

        # Walk-forward (quick: 3 windows)
        if len(X) >= 200:
            from ml.walk_forward import generate_windows, summarize_walk_forward
            windows = generate_windows(len(X), is_ratio=0.7, min_trades_per_window=50)
            wf_results = []
            for w in windows[:5]:
                try:
                    is_X = X.iloc[w["is_start"]:w["is_end"]]
                    is_y = binary_y[w["is_start"]:w["is_end"]]
                    oos_X = X.iloc[w["oos_start"]:w["oos_end"]]
                    oos_y = binary_y[w["oos_start"]:w["oos_end"]]
                    if len(is_X) < 20 or len(oos_X) < 5:
                        continue
                    wf_a = MetaLabelAnalyzer(xgb_params)
                    wf_a.train(is_X, is_y, feature_names=available_cols)
                    is_acc = np.mean(wf_a.model.predict(is_X.values) == is_y)
                    oos_acc = np.mean(wf_a.model.predict(oos_X.values) == oos_y)
                    wf_results.append({"is_metric": is_acc, "oos_metric": oos_acc})
                except Exception:
                    continue
            if wf_results:
                wf_summary = summarize_walk_forward(wf_results)
                wfe_avg = wf_summary["avg_wfe"]
                wfe_rating = wf_summary["rating"]

        # Save per-coin artifacts
        if save_all:
            coin_dir = OUTPUT_DIR / symbol
            coin_dir.mkdir(parents=True, exist_ok=True)
            feats.to_parquet(coin_dir / "features.parquet", index=False)
            np.save(str(coin_dir / "labels.npy"), labels)
            analyzer.model.save_model(str(coin_dir / "meta_model.json"))
            imp.to_csv(coin_dir / "feature_importance.csv", index=False)

    except ImportError:
        pass
    except Exception as e:
        print(f"    ML error: {e}")

    # Loser analysis
    classified = classify_losers(trades_df)
    class_summary = get_class_summary(classified)
    etd = compute_etd(trades_df)

    # Build result row
    c_counts = {}
    for _, row in class_summary.iterrows():
        c_counts[row["class"]] = int(row["count"])

    return {
        "Symbol": symbol,
        "Trades": m["total_trades"],
        "WR": m["win_rate"] * 100,
        "Net_PnL": m["net_pnl"],
        "Exp": m["expectancy"],
        "Sharpe": m["sharpe"],
        "PF": m["profit_factor"],
        "MaxDD_pct": m["max_drawdown_pct"],
        "LSG": m["pct_losers_saw_green"] * 100,
        "BE_n": m["be_raised_count"],
        "Avg_MFE": m["avg_mfe"],
        "Avg_MAE": m["avg_mae"],
        "Avg_ETD": etd["etd"].mean(),
        "ML_Acc": ml_acc,
        "ML_Skip": ml_skip_rate * 100,
        "Filt_Trades": filtered_trades,
        "Filt_Net": filtered_net,
        "Filt_Exp": filtered_exp,
        "WFE": wfe_avg,
        "WFE_Rating": wfe_rating,
        "Top_Feature": top_feature,
        "W": c_counts.get("W", 0),
        "A_losers": c_counts.get("A", 0),
        "B_losers": c_counts.get("B", 0),
        "C_losers": c_counts.get("C", 0),
        "D_losers": c_counts.get("D", 0),
    }


def main():
    parser = argparse.ArgumentParser(description="Sweep all coins through ML pipeline")
    parser.add_argument("--timeframe", type=str, default="5m", help="Timeframe (1m, 5m, 15m)")
    parser.add_argument("--sl", type=float, default=1.0, help="SL ATR multiplier")
    parser.add_argument("--tp", type=float, default=1.5, help="TP ATR multiplier")
    parser.add_argument("--cooldown", type=int, default=3, help="Min bars between entries")
    parser.add_argument("--be-raise", type=float, default=2.0, help="Fixed BE raise ($)")
    parser.add_argument("--threshold", type=float, default=0.5, help="ML filter threshold")
    parser.add_argument("--top", type=int, default=20, help="Show top N coins")
    parser.add_argument("--save-all", action="store_true", help="Save per-coin ML artifacts")
    parser.add_argument("--symbols", type=str, default=None,
                        help="Comma-separated symbols (default: all cached)")
    args = parser.parse_args()

    tf_map = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60}
    tf_min = tf_map.get(args.timeframe)
    if tf_min is None:
        print(f"ERROR: Unknown timeframe. Use: {list(tf_map.keys())}")
        sys.exit(1)

    print("=" * 100)
    print(f"  VINCE ML SWEEP -- All Coins {args.timeframe}")
    print("=" * 100)

    check_permissions()

    # Load coin list
    from data.fetcher import BybitFetcher
    fetcher = BybitFetcher(cache_dir=str(ROOT / "data" / "cache"))

    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    else:
        symbols = sorted(fetcher.list_cached())

    print(f"  {len(symbols)} coins to process")

    bt_params = {
        "sl_mult": args.sl, "tp_mult": args.tp, "cooldown": args.cooldown,
        "b_open_fresh": True, "notional": 10000.0,
        "commission_rate": 0.0008, "rebate_pct": 0.70,
        "be_raise_amount": args.be_raise,
    }
    xgb_params = {
        "n_estimators": 200, "max_depth": 4,
        "learning_rate": 0.05, "subsample": 0.8,
        "colsample_bytree": 0.8, "verbosity": 0,
    }

    t0 = time.time()
    results = []
    errors = []

    for i, sym in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] {sym}...", end="", flush=True)

        df_1m = fetcher.load_cached(sym)
        if df_1m is None:
            print(" SKIP (no data)")
            continue

        try:
            if tf_min > 1:
                df_tf = resample(df_1m, tf_min)
            else:
                df_tf = df_1m.copy()

            row = analyze_coin(sym, df_tf, bt_params, xgb_params,
                             args.threshold, args.save_all)
            if row is None:
                print(f" SKIP (<30 trades)")
                continue

            results.append(row)
            print(f" {row['Trades']} trades, Net ${row['Net_PnL']:>10,.2f}, "
                  f"Exp ${row['Exp']:>7.2f}, ML_Acc {row['ML_Acc']:.3f}")

        except Exception as e:
            errors.append({"symbol": sym, "error": str(e)})
            print(f" ERROR: {e}")

    # Build results DataFrame
    if not results:
        print("\nNo results. Check data and parameters.")
        sys.exit(1)

    rdf = pd.DataFrame(results)

    # ========== RANKINGS ==========
    print("\n" + "=" * 100)
    print(f"  TOP {args.top} BY EXPECTANCY ({args.timeframe})")
    print("=" * 100)
    top_exp = rdf.sort_values("Exp", ascending=False).head(args.top)
    print(f"{'Symbol':>18} {'Trades':>7} {'WR%':>6} {'Net P&L':>12} "
          f"{'Exp$/tr':>9} {'Sharpe':>7} {'LSG%':>6} {'ML_Acc':>7} "
          f"{'ML_Skip%':>8} {'WFE':>6} {'Rating':>8}")
    for _, r in top_exp.iterrows():
        print(f"{r['Symbol']:>18} {r['Trades']:>7} {r['WR']:>6.1f} "
              f"{r['Net_PnL']:>12,.2f} {r['Exp']:>9.2f} {r['Sharpe']:>7.3f} "
              f"{r['LSG']:>6.1f} {r['ML_Acc']:>7.3f} {r['ML_Skip']:>8.1f} "
              f"{r['WFE']:>6.3f} {r['WFE_Rating']:>8}")

    # Filtered rankings
    filtered = rdf[rdf["Filt_Trades"] > 0].copy()
    if len(filtered) > 0:
        print("\n" + "=" * 100)
        print(f"  TOP {args.top} BY FILTERED EXPECTANCY (ML threshold={args.threshold})")
        print("=" * 100)
        top_filt = filtered.sort_values("Filt_Exp", ascending=False).head(args.top)
        print(f"{'Symbol':>18} {'Orig_Tr':>8} {'Filt_Tr':>8} {'Orig_Exp':>9} "
              f"{'Filt_Exp':>9} {'Filt_Net':>12} {'ML_Skip%':>8}")
        for _, r in top_filt.iterrows():
            print(f"{r['Symbol']:>18} {r['Trades']:>8} {r['Filt_Trades']:>8} "
                  f"{r['Exp']:>9.2f} {r['Filt_Exp']:>9.2f} "
                  f"{r['Filt_Net']:>12,.2f} {r['ML_Skip']:>8.1f}")

    # Loser class summary
    print("\n" + "=" * 100)
    print("  LOSER CLASS DISTRIBUTION (all coins)")
    print("=" * 100)
    print(f"{'Symbol':>18} {'W':>5} {'A':>5} {'B':>5} {'C':>5} {'D':>5} "
          f"{'C+D%':>6} {'Avg_ETD':>8}")
    for _, r in rdf.sort_values("Exp", ascending=False).head(args.top).iterrows():
        total_losers = r["A_losers"] + r["B_losers"] + r["C_losers"] + r["D_losers"]
        cd_pct = (r["C_losers"] + r["D_losers"]) / total_losers * 100 if total_losers > 0 else 0
        print(f"{r['Symbol']:>18} {r['W']:>5} {r['A_losers']:>5} {r['B_losers']:>5} "
              f"{r['C_losers']:>5} {r['D_losers']:>5} {cd_pct:>6.1f} {r['Avg_ETD']:>8.2f}")

    # Grand totals
    print("\n" + "=" * 100)
    print("  GRAND TOTALS")
    print("=" * 100)
    total_net = rdf["Net_PnL"].sum()
    total_trades = rdf["Trades"].sum()
    total_filt_net = rdf["Filt_Net"].sum()
    total_filt_trades = rdf["Filt_Trades"].sum()
    print(f"  Coins:          {len(rdf)}")
    print(f"  Total trades:   {total_trades:,}")
    print(f"  Total net:      ${total_net:,.2f}")
    print(f"  Avg exp/trade:  ${total_net / total_trades:.2f}" if total_trades > 0 else "")
    if total_filt_trades > 0:
        print(f"  Filtered trades: {total_filt_trades:,}")
        print(f"  Filtered net:    ${total_filt_net:,.2f}")
        print(f"  Filtered exp:    ${total_filt_net / total_filt_trades:.2f}")

    # Save CSV
    csv_path = OUTPUT_DIR / f"sweep_ml_{args.timeframe}.csv"
    rdf.to_csv(csv_path, index=False)
    print(f"\n  Results saved to {csv_path}")

    if errors:
        print(f"\n  {len(errors)} errors:")
        for e in errors:
            print(f"    {e['symbol']}: {e['error']}")

    elapsed = time.time() - t0
    print(f"\n  Done in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
