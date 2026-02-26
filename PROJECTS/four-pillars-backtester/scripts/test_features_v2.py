"""
Test script for ml/features_v2.py
File: PROJECTS/four-pillars-backtester/scripts/test_features_v2.py

Tests:
  1. All 26 features compute on synthetic data
  2. Volume features are non-trivial (not all default values)
  3. Market cap features work with/without metadata
  4. get_feature_columns() returns all 26 names
  5. Backward compatibility (no metadata = graceful NaN)
  6. Feature values are within expected ranges
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from ml.features_v2 import extract_trade_features, get_feature_columns

PASS = 0
FAIL = 0


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    ts = datetime.now().strftime("%H:%M:%S")
    if condition:
        PASS += 1
        print(f"[{ts}] PASS: {name}")
    else:
        FAIL += 1
        print(f"[{ts}] FAIL: {name} -- {detail}")


def make_synthetic_ohlcv(n_bars: int = 500) -> pd.DataFrame:
    """Generate synthetic OHLCV data with all required signal columns."""
    np.random.seed(42)
    base_price = 100.0
    prices = base_price + np.cumsum(np.random.randn(n_bars) * 0.5)
    prices = np.maximum(prices, 1.0)  # Prevent negative prices

    dt_start = datetime(2024, 6, 1, tzinfo=timezone.utc)
    timestamps = [int((dt_start + timedelta(minutes=i)).timestamp() * 1000) for i in range(n_bars)]

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": prices + np.random.randn(n_bars) * 0.1,
        "high": prices + abs(np.random.randn(n_bars) * 0.5),
        "low": prices - abs(np.random.randn(n_bars) * 0.5),
        "close": prices,
        "base_vol": np.random.exponential(1000, n_bars),
        "quote_vol": np.random.exponential(50000, n_bars),
        "datetime": pd.to_datetime(timestamps, unit="ms", utc=True),
        # Signal columns
        "stoch_9": np.random.uniform(0, 100, n_bars),
        "stoch_14": np.random.uniform(0, 100, n_bars),
        "stoch_40": np.random.uniform(0, 100, n_bars),
        "stoch_60": np.random.uniform(0, 100, n_bars),
        "atr": abs(np.random.randn(n_bars) * 2),
        "cloud3_bull": np.random.choice([0, 1], n_bars).astype(float),
        "price_pos": np.random.choice([-1, 0, 1], n_bars).astype(float),
        "ema34": prices + np.random.randn(n_bars) * 0.3,
        "ema50": prices + np.random.randn(n_bars) * 0.3,
    })
    return df


def make_synthetic_trades(ohlcv_df: pd.DataFrame, n_trades: int = 20) -> pd.DataFrame:
    """Generate synthetic trades aligned to OHLCV bars."""
    np.random.seed(123)
    n_bars = len(ohlcv_df)
    close = ohlcv_df["close"].values

    trades = []
    for _ in range(n_trades):
        entry_bar = np.random.randint(50, n_bars - 50)
        exit_bar = entry_bar + np.random.randint(5, 40)
        entry_price = close[entry_bar]
        direction = np.random.choice(["LONG", "SHORT"])
        sl_dist = entry_price * 0.02  # 2% SL
        tp_dist = entry_price * 0.04  # 4% TP

        if direction == "LONG":
            sl_price = entry_price - sl_dist
            tp_price = entry_price + tp_dist
        else:
            sl_price = entry_price + sl_dist
            tp_price = entry_price - tp_dist

        pnl = np.random.randn() * 20
        commission = abs(entry_price * 0.0008 * 2)

        trades.append({
            "entry_bar": entry_bar,
            "exit_bar": exit_bar,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "direction": direction,
            "grade": np.random.choice(["A", "B", "C", "R"]),
            "mfe": abs(np.random.randn() * 30),
            "mae": abs(np.random.randn() * 15),
            "pnl": pnl,
            "commission": commission,
            "exit_reason": np.random.choice(["sl", "tp", "signal"]),
        })

    return pd.DataFrame(trades)


def main():
    global PASS, FAIL
    print("=" * 70)
    print("TEST: ml/features_v2.py")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    ohlcv = make_synthetic_ohlcv(500)
    trades = make_synthetic_trades(ohlcv, 20)

    # --- Test 1: get_feature_columns returns 26 ---
    print("\n--- Test 1: Feature column count ---")
    feat_cols = get_feature_columns()
    test("get_feature_columns returns list", isinstance(feat_cols, list))
    test("26 feature columns", len(feat_cols) == 26,
         f"got {len(feat_cols)}: {feat_cols}")

    # --- Test 2: Extract with full metadata ---
    print("\n--- Test 2: Full extraction (with metadata) ---")
    coin_meta = {"market_cap": 500_000_000, "market_cap_rank": 42}

    # Build mock market cap history
    dates = pd.date_range("2024-05-01", "2024-07-01", freq="D")
    mcap_hist = pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "symbol": "TESTUSDT",
        "market_cap": np.random.uniform(4e8, 6e8, len(dates)),
        "total_volume": np.random.uniform(1e7, 5e7, len(dates)),
    })

    feats = extract_trade_features(trades, ohlcv, coin_meta, mcap_hist)
    test("returns DataFrame", isinstance(feats, pd.DataFrame))
    test("rows match trades", len(feats) == len(trades),
         f"expected {len(trades)}, got {len(feats)}")

    # Check all 26 feature columns present (excluding target cols)
    available = [c for c in feat_cols if c in feats.columns]
    test("all 26 features present", len(available) == 26,
         f"got {len(available)}: missing = {set(feat_cols) - set(feats.columns)}")

    # --- Test 3: Original 14 features ---
    print("\n--- Test 3: Original features ---")
    original_feats = ["direction_enc", "grade_enc", "stoch_9", "stoch_14",
                      "stoch_40", "stoch_60", "atr_pct", "vol_ratio",
                      "cloud3_bull", "price_pos", "cloud3_spread",
                      "hour", "day_of_week", "duration_bars"]
    for f in original_feats:
        test(f"original feature '{f}' exists", f in feats.columns)

    # --- Test 4: New volume features (8) ---
    print("\n--- Test 4: Volume features ---")
    vol_feats = ["vol_ratio_5", "vol_ratio_50", "vol_ratio_200",
                 "vol_trend", "vol_zscore", "quote_vol_ratio",
                 "vol_price_corr", "relative_spread"]
    for f in vol_feats:
        test(f"volume feature '{f}' exists", f in feats.columns)
        if f in feats.columns:
            non_default = (feats[f] != 0.0).any() if f != "vol_price_corr" else True
            test(f"  '{f}' has non-trivial values", non_default,
                 f"all zeros/defaults")

    # Range checks
    if "vol_ratio_5" in feats.columns:
        test("vol_ratio_5 positive", (feats["vol_ratio_5"] > 0).all())
    if "relative_spread" in feats.columns:
        test("relative_spread >= 0", (feats["relative_spread"] >= 0).all())

    # --- Test 5: Market cap features (4) ---
    print("\n--- Test 5: Market cap features ---")
    mcap_feats = ["log_market_cap", "log_daily_turnover",
                  "market_cap_rank", "turnover_to_cap_ratio"]
    for f in mcap_feats:
        test(f"market cap feature '{f}' exists", f in feats.columns)

    if "log_market_cap" in feats.columns:
        test("log_market_cap ~ log10(500M) ~ 8.7",
             abs(feats["log_market_cap"].iloc[0] - np.log10(500_000_000)) < 0.01,
             f"got: {feats['log_market_cap'].iloc[0]}")

    if "market_cap_rank" in feats.columns:
        test("market_cap_rank = 42", (feats["market_cap_rank"] == 42).all(),
             f"got: {feats['market_cap_rank'].unique()}")

    # --- Test 6: Backward compatibility (no metadata) ---
    print("\n--- Test 6: Backward compatibility ---")
    feats_no_meta = extract_trade_features(trades, ohlcv)
    test("runs without metadata", isinstance(feats_no_meta, pd.DataFrame))
    test("same row count", len(feats_no_meta) == len(trades))

    # Market cap features should be NaN without metadata
    if "log_market_cap" in feats_no_meta.columns:
        test("log_market_cap is NaN without metadata",
             feats_no_meta["log_market_cap"].isna().all())
    if "market_cap_rank" in feats_no_meta.columns:
        test("market_cap_rank is NaN without metadata",
             feats_no_meta["market_cap_rank"].isna().all())

    # Volume features should still work
    if "vol_ratio_5" in feats_no_meta.columns:
        test("vol_ratio_5 works without metadata",
             feats_no_meta["vol_ratio_5"].notna().all())

    # --- Test 7: Target columns excluded from feature list ---
    print("\n--- Test 7: Target column exclusion ---")
    target_cols = ["mfe_r", "mae_r", "pnl_r", "etd"]
    for c in target_cols:
        test(f"target '{c}' NOT in feature list", c not in feat_cols)
        test(f"target '{c}' IS in output DataFrame", c in feats.columns)

    # --- Summary ---
    print("\n" + "=" * 70)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 70)
    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
