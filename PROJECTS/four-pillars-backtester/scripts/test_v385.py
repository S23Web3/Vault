"""
Test script for backtester_v385.py.
Validates: 12 new metrics, entry-state, lifecycle, LSG, P&L path, parquet.
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
    print("TEST: backtester_v385.py")
    print("=" * 60)

    # 1. Import
    try:
        from engine.backtester_v385 import Backtester385
        check("Import Backtester385", True)
    except Exception as e:
        check(f"Import Backtester385: {e}", False)
        print(f"\n{PASS} passed, {FAIL} failed")
        return

    # 2. Load test data
    from signals.four_pillars_v383 import compute_signals_v383
    cache = os.path.join(ROOT, "data", "cache")
    test_file = None
    for f in os.listdir(cache):
        if "RIVER" in f and "5m" in f and f.endswith(".parquet"):
            test_file = os.path.join(cache, f)
            break
    if not test_file:
        for f in os.listdir(cache):
            if f.endswith(".parquet"):
                test_file = os.path.join(cache, f)
                break

    if not test_file:
        print("No cached data found for testing.")
        return

    df = pd.read_parquet(test_file)
    df = compute_signals_v383(df, {})
    check("Load test data", len(df) > 100)

    # 3. Run v385 backtest
    params = {"sl_mult": 2.5, "tp_mult": 2.0, "cooldown": 3,
              "margin": 500, "leverage": 20, "commission_rate": 0.0008,
              "save_parquet": True, "symbol": "TEST", "timeframe": "5m"}
    bt = Backtester385(params=params)
    results = bt.run(df)
    trades = results["trades"]
    metrics = results["metrics"]
    tdf = results["trades_df"]

    check("Backtest completes", results is not None)
    check("Has trades", len(trades) > 0)

    # 4. New metrics present
    new_keys = ["max_single_win", "max_single_loss", "avg_winner", "avg_loser",
                "wl_ratio", "max_win_streak", "max_loss_streak", "sortino",
                "calmar", "be_exits", "lsg_cat_a_pct", "lsg_cat_b_pct"]
    for k in new_keys:
        check(f"Metric '{k}' present", k in metrics)

    # 5. Entry-state fields
    entry_cols = ["entry_stoch9_value", "entry_stoch9_direction",
                  "entry_stoch14_value", "entry_ripster_expanding",
                  "entry_avwap_distance", "entry_vol_ratio"]
    for c in entry_cols:
        check(f"Entry field '{c}' in DataFrame", c in tdf.columns)

    # 6. Lifecycle fields
    life_cols = ["life_bars", "life_stoch9_min", "life_stoch9_max",
                 "life_ripster_flip", "life_avwap_max_dist", "life_mfe_bar"]
    for c in life_cols:
        check(f"Lifecycle field '{c}' in DataFrame", c in tdf.columns)

    # 7. P&L path values
    valid_paths = {"direct", "green_then_red", "red_then_green", "choppy"}
    if "life_pnl_path" in tdf.columns:
        paths = set(tdf["life_pnl_path"].unique())
        check("P&L path values valid", paths.issubset(valid_paths))
    else:
        check("P&L path column exists", False)

    # 8. LSG categories
    if "lsg_category" in tdf.columns:
        cats = set(tdf["lsg_category"].unique()) - {""}
        valid_cats = {"A", "B", "C", "D"}
        check("LSG categories valid", cats.issubset(valid_cats))
    else:
        check("LSG category column exists", False)

    # 9. Parquet output
    parquet_path = os.path.join(ROOT, "results", "trades_TEST_5m.parquet")
    check("Parquet file written", os.path.exists(parquet_path))
    if os.path.exists(parquet_path):
        pq = pd.read_parquet(parquet_path)
        check("Parquet readable", len(pq) > 0)
        check("Parquet cols >= 30", len(pq.columns) >= 30)
        os.remove(parquet_path)  # cleanup

    # 10. Metric sanity
    check("Calmar is numeric", isinstance(metrics.get("calmar", 0), (int, float)))
    check("WL ratio >= 0", metrics.get("wl_ratio", 0) >= 0)
    check("Win streak >= 0", metrics.get("max_win_streak", 0) >= 0)

    # 11. Compare with v384 net PnL (should be identical)
    try:
        from engine.backtester_v384 import Backtester384
        bt4 = Backtester384(params=params)
        r4 = bt4.run(df)
        pnl_384 = r4["metrics"].get("net_pnl", 0)
        pnl_385 = metrics.get("net_pnl", 0)
        diff = abs(pnl_385 - pnl_384)
        check(f"v385 net PnL matches v384 (diff={diff:.4f})", diff < abs(pnl_384) * 0.01 + 0.01)
    except Exception as e:
        check(f"v384 comparison: {e}", False)

    print(f"\n{'='*60}")
    print(f"RESULTS: {PASS} passed, {FAIL} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
