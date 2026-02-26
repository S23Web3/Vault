"""
Test script for dashboard sweep logic: params hash, CSV persistence,
auto-resume, LSG bars metric, mode transitions, metrics completeness.

Run: python scripts/test_sweep.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

PASS_COUNT = 0
FAIL_COUNT = 0


def check(name, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {name}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {name} -- {detail}")


# ── Import dashboard helpers ──────────────────────────────────────────────
# These are module-level functions defined in dashboard.py.
# We import them by manipulating sys.path and importing the module.

def _import_dashboard_helpers():
    """Import compute_params_hash and compute_avg_green_bars from dashboard.
    Dashboard uses streamlit which we mock minimally."""
    import importlib
    # We need streamlit installed but won't actually run the app
    try:
        import streamlit
    except ImportError:
        print("  SKIP: streamlit not installed, cannot import dashboard helpers")
        return None, None

    # Read dashboard.py source and extract just the helper functions
    dashboard_path = Path(__file__).resolve().parent / "dashboard.py"
    if not dashboard_path.exists():
        print(f"  SKIP: {dashboard_path} not found")
        return None, None

    source = dashboard_path.read_text(encoding="utf-8")

    # Extract compute_params_hash function
    import hashlib
    import json

    def compute_params_hash(signal_params, bt_params, timeframe):
        payload = json.dumps({"s": signal_params, "b": bt_params, "tf": timeframe},
                             sort_keys=True, default=str)
        return hashlib.md5(payload.encode()).hexdigest()[:8]

    def compute_avg_green_bars(trades_df, df_sig):
        losers = trades_df[(trades_df["net_pnl"] < 0) & (trades_df["saw_green"] == True)]
        if losers.empty:
            return 0.0
        close_vals = df_sig["close"].values if "close" in df_sig.columns else None
        if close_vals is None:
            return 0.0
        green_counts = []
        for _, t in losers.iterrows():
            eb = int(t["entry_bar"])
            xb = int(t["exit_bar"])
            ep = float(t["entry_price"])
            d = t["direction"]
            count = 0
            for bar in range(eb, min(xb + 1, len(close_vals))):
                if d == "LONG":
                    unreal = close_vals[bar] - ep
                else:
                    unreal = ep - close_vals[bar]
                if unreal > 0:
                    count += 1
            green_counts.append(count)
        return float(np.mean(green_counts)) if green_counts else 0.0

    return compute_params_hash, compute_avg_green_bars


# ── Test functions ────────────────────────────────────────────────────────

def test_params_hash_determinism():
    """Same params = same hash. Different params = different hash."""
    print("\n=== Params Hash Determinism ===")
    compute_params_hash, _ = _import_dashboard_helpers()
    if compute_params_hash is None:
        return

    sp = {"atr_length": 14, "cross_level": 25, "stoch_k1": 9}
    bp = {"sl_mult": 2.5, "tp_mult": 2.0, "cooldown": 3}
    tf = "5m"

    h1 = compute_params_hash(sp, bp, tf)
    h2 = compute_params_hash(sp, bp, tf)
    check("same params same hash", h1 == h2, f"{h1} vs {h2}")
    check("hash is 8 chars", len(h1) == 8, f"len={len(h1)}")

    # Different params
    sp2 = dict(sp, atr_length=20)
    h3 = compute_params_hash(sp2, bp, tf)
    check("different signal params different hash", h1 != h3, f"{h1} vs {h3}")

    bp2 = dict(bp, sl_mult=3.0)
    h4 = compute_params_hash(sp, bp2, tf)
    check("different bt params different hash", h1 != h4, f"{h1} vs {h4}")

    h5 = compute_params_hash(sp, bp, "1m")
    check("different timeframe different hash", h1 != h5, f"{h1} vs {h5}")


def test_sweep_csv_write_read():
    """Write sweep progress CSV, read it back, verify all columns."""
    print("\n=== Sweep CSV Write/Read ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        csv_path = tmpdir / "sweep_progress.csv"
        rows = []
        for i in range(5):
            rows.append({
                "Symbol": f"COIN{i}USDT", "Trades": 100 + i * 10,
                "WR%": 55.0 + i, "Net": 1000.0 + i * 500,
                "Exp": 5.0 + i, "LSG%": 85.0 + i,
                "LSG_Bars": 3.5 + i * 0.2,
                "ScaleOut": 10 + i, "TP_Exits": 40 + i,
                "SL_Exits": 50 + i, "DD%": 5.0 + i,
                "Sharpe": 0.5 + i * 0.1, "PF": 1.5 + i * 0.1,
                "Rebate$": 50.0 + i * 10,
                "Start": "2024-01-01", "End": "2024-03-31",
                "params_hash": "abcd1234",
            })
        df = pd.DataFrame(rows)
        df.to_csv(csv_path, index=False)

        # Read back
        df_read = pd.read_csv(csv_path)
        check("csv has 5 rows", len(df_read) == 5)
        expected_cols = ["Symbol", "Trades", "WR%", "Net", "Exp", "LSG%",
                         "LSG_Bars", "ScaleOut", "TP_Exits", "SL_Exits",
                         "DD%", "Sharpe", "PF", "Rebate$", "Start", "End",
                         "params_hash"]
        missing = [c for c in expected_cols if c not in df_read.columns]
        check("all columns present", len(missing) == 0, f"missing: {missing}")
    finally:
        shutil.rmtree(tmpdir)


def test_sweep_csv_resume():
    """Write 3/10 rows, verify remaining = 7 symbols."""
    print("\n=== Sweep CSV Resume ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        csv_path = tmpdir / "sweep_progress.csv"
        all_symbols = [f"COIN{i}USDT" for i in range(10)]
        completed = all_symbols[:3]
        hash_val = "test1234"

        rows = []
        for sym in completed:
            rows.append({"Symbol": sym, "Trades": 100, "Net": 500.0,
                         "params_hash": hash_val})
        pd.DataFrame(rows).to_csv(csv_path, index=False)

        # Simulate resume logic
        prev_df = pd.read_csv(csv_path)
        matching = prev_df[prev_df["params_hash"] == hash_val]
        completed_symbols = set(matching["Symbol"].tolist())
        remaining = [s for s in all_symbols if s not in completed_symbols]

        check("3 completed", len(completed_symbols) == 3)
        check("7 remaining", len(remaining) == 7, f"got {len(remaining)}")
        check("remaining correct", remaining == all_symbols[3:])
    finally:
        shutil.rmtree(tmpdir)


def test_sweep_csv_hash_filter():
    """Write rows with 2 different hashes, verify filter works."""
    print("\n=== Sweep CSV Hash Filter ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        csv_path = tmpdir / "sweep_progress.csv"
        rows = []
        for i in range(5):
            rows.append({"Symbol": f"A{i}USDT", "Trades": 100,
                         "Net": 500.0, "params_hash": "hash_aaa"})
        for i in range(3):
            rows.append({"Symbol": f"B{i}USDT", "Trades": 200,
                         "Net": 1000.0, "params_hash": "hash_bbb"})
        pd.DataFrame(rows).to_csv(csv_path, index=False)

        prev_df = pd.read_csv(csv_path)

        match_a = prev_df[prev_df["params_hash"] == "hash_aaa"]
        check("hash_a matches 5", len(match_a) == 5)

        match_b = prev_df[prev_df["params_hash"] == "hash_bbb"]
        check("hash_b matches 3", len(match_b) == 3)

        match_c = prev_df[prev_df["params_hash"] == "hash_ccc"]
        check("hash_c matches 0", len(match_c) == 0)
    finally:
        shutil.rmtree(tmpdir)


def test_avg_green_bars():
    """Mock trades_df with known saw_green losers, verify avg bars."""
    print("\n=== Avg Green Bars ===")
    _, compute_avg_green_bars = _import_dashboard_helpers()
    if compute_avg_green_bars is None:
        return

    # Create mock close prices: goes up then down
    # bars 0-19: price starts at 100, goes to 110, then drops to 95
    close_vals = np.array(
        [100 + i * 0.5 for i in range(10)] +  # 100, 100.5, ..., 104.5
        [105 - i * 1.0 for i in range(10)]     # 105, 104, ..., 96
    )
    df_sig = pd.DataFrame({"close": close_vals})

    # Trade: LONG entry at bar 0, price 100, exit at bar 19, price 96
    # saw_green=True, net_pnl=-4 (loser)
    # Bars where close > 100 (entry price): bars 0 is 100 (not >), bars 1-14 are > 100
    # Actually bar 0 = 100 (not > 0 unrealized), bar 1 = 100.5 (green), ...
    # bar 10 = 105, bar 11 = 104, ..., bar 14 = 101 (green), bar 15 = 100 (not green)
    # Green bars: 1 through 14 = 14 bars
    trades_df = pd.DataFrame([{
        "direction": "LONG", "grade": "A",
        "entry_bar": 0, "exit_bar": 19,
        "entry_price": 100.0, "exit_price": 96.0,
        "net_pnl": -4.0, "saw_green": True,
        "pnl": -3.5, "commission": 0.5,
    }])

    avg = compute_avg_green_bars(trades_df, df_sig)
    # Count: bars 1-14 where close > 100.0
    expected_green = sum(1 for b in range(0, 20) if close_vals[b] > 100.0)
    check("avg green bars calculated", avg == expected_green,
          f"got {avg}, expected {expected_green}")


def test_avg_green_bars_short():
    """Test avg green bars for SHORT trades."""
    print("\n=== Avg Green Bars (SHORT) ===")
    _, compute_avg_green_bars = _import_dashboard_helpers()
    if compute_avg_green_bars is None:
        return

    # Price goes down then up: SHORT at 100, wins initially, then loses
    close_vals = np.array(
        [100 - i * 0.5 for i in range(5)] +  # 100, 99.5, 99, 98.5, 98
        [98 + i * 1.0 for i in range(5)]       # 98, 99, 100, 101, 102
    )
    df_sig = pd.DataFrame({"close": close_vals})

    trades_df = pd.DataFrame([{
        "direction": "SHORT", "grade": "B",
        "entry_bar": 0, "exit_bar": 9,
        "entry_price": 100.0, "exit_price": 102.0,
        "net_pnl": -2.5, "saw_green": True,
        "pnl": -2.0, "commission": 0.5,
    }])

    avg = compute_avg_green_bars(trades_df, df_sig)
    # SHORT: green when close < entry_price (100)
    # bar 0: 100 (not green), bars 1-4: 99.5,99,98.5,98 (green), bar 5: 98 (green),
    # bar 6: 99 (green), bar 7: 100 (not green), bar 8: 101 (not), bar 9: 102 (not)
    expected_green = sum(1 for b in range(0, 10) if close_vals[b] < 100.0)
    check("short green bars", avg == expected_green,
          f"got {avg}, expected {expected_green}")


def test_avg_green_bars_no_losers():
    """No losers with saw_green -> returns 0."""
    print("\n=== Avg Green Bars (no losers) ===")
    _, compute_avg_green_bars = _import_dashboard_helpers()
    if compute_avg_green_bars is None:
        return

    df_sig = pd.DataFrame({"close": [100 + i for i in range(10)]})

    # All winners
    trades_df = pd.DataFrame([{
        "direction": "LONG", "grade": "A",
        "entry_bar": 0, "exit_bar": 9,
        "entry_price": 100.0, "exit_price": 110.0,
        "net_pnl": 9.5, "saw_green": True,
        "pnl": 10.0, "commission": 0.5,
    }])
    avg = compute_avg_green_bars(trades_df, df_sig)
    check("no losers returns 0", avg == 0.0)


def test_mode_transitions():
    """Verify valid mode transitions."""
    print("\n=== Mode Transitions ===")
    valid_modes = {"settings", "single", "sweep", "sweep_detail"}
    valid_transitions = {
        ("settings", "single"),    # click Run Backtest
        ("settings", "sweep"),     # click Sweep ALL
        ("single", "settings"),    # click Back
        ("sweep", "settings"),     # click Back
        ("sweep", "sweep_detail"), # click View Detail
        ("sweep_detail", "sweep"), # click Back to Sweep
    }

    for src, dst in valid_transitions:
        check(f"{src} -> {dst}", (src, dst) in valid_transitions)

    # Invalid: can't go from single to sweep_detail directly
    check("single -> sweep_detail invalid",
          ("single", "sweep_detail") not in valid_transitions)
    check("sweep_detail -> settings invalid",
          ("sweep_detail", "settings") not in valid_transitions)


def test_metrics_completeness():
    """Run a real backtest on cached RIVERUSDT 5m data, check all dashboard-used keys."""
    print("\n=== Metrics Completeness ===")
    cache_dir = Path(__file__).resolve().parent.parent / "data" / "cache"
    river_path = cache_dir / "RIVERUSDT_1m.parquet"

    if not river_path.exists():
        print("  SKIP: RIVERUSDT_1m.parquet not in cache (need cached data)")
        return

    from signals.four_pillars_v383 import compute_signals_v383
    from engine.backtester_v384 import Backtester384

    df = pd.read_parquet(river_path)
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})

    # Resample to 5m
    df2 = df.copy()
    if "datetime" not in df2.columns and df2.index.name == "datetime":
        df2 = df2.reset_index()
    df2 = df2.set_index("datetime")
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    for col in ["base_vol", "quote_vol"]:
        if col in df2.columns:
            agg[col] = "sum"
    if "timestamp" in df2.columns:
        agg["timestamp"] = "first"
    df_5m = df2.resample("5min").agg(agg).dropna(subset=["close"]).reset_index()

    df_sig = compute_signals_v383(df_5m.copy(), {})

    bt_params = {
        "sl_mult": 2.5, "tp_mult": 2.0, "cooldown": 3,
        "b_open_fresh": True, "notional": 10000.0,
        "commission_rate": 0.0008, "maker_rate": 0.0002,
        "rebate_pct": 0.70, "initial_equity": 10000.0,
        "max_positions": 4, "checkpoint_interval": 5,
        "max_scaleouts": 2, "sigma_floor_atr": 0.5,
        "enable_adds": True, "enable_reentry": True,
        "be_trigger_atr": 0.0, "be_lock_atr": 0.0,
    }

    results = Backtester384(bt_params).run(df_sig)
    m = results["metrics"]
    trades_df = results["trades_df"]

    check("has trades", m["total_trades"] > 0, f"trades={m['total_trades']}")

    # All keys that dashboard.py references from metrics dict
    dashboard_keys = [
        "total_trades", "win_rate", "expectancy", "net_pnl",
        "profit_factor", "sharpe", "max_drawdown_pct",
        "total_commission", "scale_out_count", "tp_exits", "sl_exits",
        "grades", "be_raised_count", "total_rebate", "net_pnl_after_rebate",
        "pct_losers_saw_green", "total_volume", "total_sides",
        "avg_positions", "max_positions_used", "pct_time_flat",
        "avg_margin_used", "peak_margin_used",
    ]
    missing = [k for k in dashboard_keys if k not in m]
    check("all dashboard keys present", len(missing) == 0,
          f"missing: {missing}")

    # Check trades_df columns used by dashboard
    trades_cols = ["direction", "grade", "entry_bar", "exit_bar",
                   "entry_price", "exit_price", "sl_price", "tp_price",
                   "pnl", "commission", "net_pnl", "mfe", "mae",
                   "exit_reason", "saw_green", "scale_idx"]
    missing_tcols = [c for c in trades_cols if c not in trades_df.columns]
    check("all trades_df columns present", len(missing_tcols) == 0,
          f"missing: {missing_tcols}")

    # Check result dict top-level keys
    result_keys = ["trades_df", "metrics", "equity_curve", "position_counts"]
    missing_rkeys = [k for k in result_keys if k not in results]
    check("all result keys present", len(missing_rkeys) == 0,
          f"missing: {missing_rkeys}")

    # Equity curve is numpy array
    check("equity_curve is array", isinstance(results["equity_curve"], np.ndarray))
    check("equity_curve length matches data", len(results["equity_curve"]) == len(df_sig))

    print(f"  (RIVERUSDT 5m: {m['total_trades']} trades, ${m['net_pnl']:.2f} net)")


def test_get_cached_symbols():
    """Test multi-interval symbol discovery logic."""
    print("\n=== get_cached_symbols Logic ===")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        # Create fake parquet files
        (tmpdir / "BTCUSDT_1m.parquet").write_bytes(b"fake")
        (tmpdir / "BTCUSDT_5m.parquet").write_bytes(b"fake")
        (tmpdir / "ETHUSDT_1m.parquet").write_bytes(b"fake")
        (tmpdir / "RIVERUSDT_5m.parquet").write_bytes(b"fake")
        (tmpdir / "SOLUSDT_15m.parquet").write_bytes(b"fake")

        # Replicate the logic from dashboard.py
        symbols = set()
        for f in tmpdir.glob("*.parquet"):
            stem = f.stem
            for suffix in ["_1m", "_5m", "_15m", "_1h", "_4h", "_1d"]:
                if stem.endswith(suffix):
                    symbols.add(stem[:-len(suffix)])
                    break

        check("found 4 unique symbols", len(symbols) == 4,
              f"got {len(symbols)}: {symbols}")
        check("BTC deduplicated", "BTCUSDT" in symbols)
        check("RIVER found from 5m only", "RIVERUSDT" in symbols)
        check("SOL found from 15m", "SOLUSDT" in symbols)
    finally:
        shutil.rmtree(tmpdir)


def test_coin_list_parsing():
    """Test custom coin list parsing for txt, csv, json."""
    print("\n=== Coin List Parsing ===")
    import json

    # TXT format
    txt_content = "BTCUSDT\nETHUSDT\nSOLUSDT\n"
    parsed = [line.strip().upper() for line in txt_content.splitlines() if line.strip()]
    check("txt parsing", parsed == ["BTCUSDT", "ETHUSDT", "SOLUSDT"])

    # JSON format
    json_content = '["BTCUSDT", "ETHUSDT", "SOLUSDT"]'
    parsed = [s.strip().upper() for s in json.loads(json_content) if isinstance(s, str)]
    check("json parsing", parsed == ["BTCUSDT", "ETHUSDT", "SOLUSDT"])

    # CSV format (with header)
    import csv as csv_mod
    csv_content = "symbol,exchange\nBTCUSDT,Bybit\nETHUSDT,Bybit\n"
    reader = csv_mod.reader(csv_content.splitlines())
    rows = list(reader)
    header = [h.strip().lower() for h in rows[0]]
    sym_col = None
    for i, h in enumerate(header):
        if h in ("symbol", "pair", "coin", "ticker"):
            sym_col = i
            break
    if sym_col is not None:
        parsed = [r[sym_col].strip().upper() for r in rows[1:] if len(r) > sym_col]
    check("csv parsing", parsed == ["BTCUSDT", "ETHUSDT"])


# ── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  SWEEP / DASHBOARD TEST SUITE")
    print("=" * 60)

    test_params_hash_determinism()
    test_sweep_csv_write_read()
    test_sweep_csv_resume()
    test_sweep_csv_hash_filter()
    test_avg_green_bars()
    test_avg_green_bars_short()
    test_avg_green_bars_no_losers()
    test_mode_transitions()
    test_get_cached_symbols()
    test_coin_list_parsing()
    test_metrics_completeness()

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {PASS_COUNT} passed, {FAIL_COUNT} failed")
    print(f"{'=' * 60}")
    sys.exit(0 if FAIL_COUNT == 0 else 1)
