"""
Tests for 55/89 EMA Cross Scalp v2 signal pipeline.
Run: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/test_55_89_signals_v2.py"
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS = []


def report(name, passed, detail=""):
    """Report a test result."""
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if passed else "FAIL"
    if passed:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    msg = "  [" + status + "] " + name
    if detail:
        msg += " -- " + detail
    print(msg)
    RESULTS.append((name, status, detail))


def make_ohlcv(n=500, price=10.0, seed=42):
    """Generate synthetic OHLCV DataFrame for testing."""
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, price * 0.003, n))
    close = np.clip(close, price * 0.5, price * 2)
    high = close * (1 + rng.uniform(0.0, 0.003, n))
    low = close * (1 - rng.uniform(0.0, 0.003, n))
    opn = close * (1 + rng.uniform(-0.001, 0.001, n))
    vol = rng.integers(100000, 1000000, n).astype(float)
    df = pd.DataFrame({
        "open": opn, "high": high, "low": low,
        "close": close, "volume": vol,
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="5min")
    df.index.name = "datetime"
    return df


def make_overzone_scenario(n=200, seed=99):
    """Build synthetic data where stoch 9 D dips below 20 then exits back above 20."""
    rng = np.random.default_rng(seed)
    # Create a price series that drops then recovers (forces stoch 9 into overzone)
    prices = np.ones(n) * 100.0
    # Bars 0-50: stable
    # Bars 51-100: decline (pushes stoch 9 below 20)
    # Bars 101-150: recovery (stoch 9 exits overzone)
    # Bars 151+: stable
    for i in range(51, 101):
        prices[i] = prices[i - 1] - 0.3 + rng.normal(0, 0.05)
    for i in range(101, 151):
        prices[i] = prices[i - 1] + 0.3 + rng.normal(0, 0.05)
    for i in range(151, n):
        prices[i] = prices[i - 1] + rng.normal(0, 0.05)

    high = prices * (1 + np.abs(rng.normal(0, 0.001, n)))
    low = prices * (1 - np.abs(rng.normal(0, 0.001, n)))
    df = pd.DataFrame({
        "open": prices, "high": high, "low": low,
        "close": prices, "volume": rng.integers(100000, 1000000, n).astype(float),
    })
    df.index = pd.date_range("2025-06-01", periods=n, freq="5min")
    df.index.name = "datetime"
    return df


def main():
    """Run all v2 signal tests."""
    from signals.ema_cross_55_89_v2 import compute_signals_55_89

    print("=" * 60)
    print("55/89 Signal Pipeline v2 -- Test Suite")
    print("=" * 60)

    # ---- Test 1: Overzone entry fires signal ----
    print("\nTest 1: Overzone entry -- stoch 9 D dips below 20 and exits")
    df_oz = make_overzone_scenario(n=300, seed=99)
    result = compute_signals_55_89(df_oz, {"min_signal_gap": 1})
    longs = int(result["long_a"].sum())
    shorts = int(result["short_a"].sum())
    total = longs + shorts
    report("T1_overzone_entry",
           total > 0,
           "signals: " + str(longs) + "L / " + str(shorts) + "S")

    # ---- Test 2: No signal while still in overzone ----
    print("\nTest 2: No signal while stoch 9 D is still below 20")
    # Use the same scenario but check no signal fires while d9 < 20
    d9 = result["stoch_9_d"].values
    long_bars = np.where(result["long_a"].values)[0]
    if len(long_bars) > 0:
        first_signal = long_bars[0]
        # At signal bar, d9 should be >= 20 (just exited overzone)
        d9_at_signal = d9[first_signal]
        report("T2_no_signal_in_overzone",
               d9_at_signal >= 20.0,
               "d9 at signal bar: " + "{:.2f}".format(d9_at_signal))
    else:
        report("T2_no_signal_in_overzone", False, "No long signals found to check")

    # ---- Test 3: Cooldown suppresses rapid signals ----
    print("\nTest 3: Cooldown -- min_signal_gap suppression")
    df_big = make_ohlcv(n=2000, price=5.0, seed=123)
    result_no_gap = compute_signals_55_89(df_big, {"min_signal_gap": 1})
    result_gap50 = compute_signals_55_89(df_big, {"min_signal_gap": 50})
    result_gap200 = compute_signals_55_89(df_big, {"min_signal_gap": 200})
    count_no_gap = int(result_no_gap["long_a"].sum() + result_no_gap["short_a"].sum())
    count_gap50 = int(result_gap50["long_a"].sum() + result_gap50["short_a"].sum())
    count_gap200 = int(result_gap200["long_a"].sum() + result_gap200["short_a"].sum())
    report("T3_cooldown",
           count_gap50 <= count_no_gap and count_gap200 <= count_gap50,
           "gap=1: " + str(count_no_gap) + ", gap=50: " + str(count_gap50) + ", gap=200: " + str(count_gap200))

    # ---- Test 4: Grade A -- stoch 40/60 already turning at entry ----
    print("\nTest 4: Grade A -- stoch 40/60 turning at entry")
    result_graded = compute_signals_55_89(df_big, {"min_signal_gap": 1})
    signal_bars = np.where(result_graded["long_a"].values | result_graded["short_a"].values)[0]
    grades_at_signals = result_graded["trade_grade"].values[signal_bars]
    grade_counts = {}
    for g in grades_at_signals:
        if g:
            grade_counts[g] = grade_counts.get(g, 0) + 1
    has_grades = len(grade_counts) > 0
    report("T4_grade_A",
           has_grades and "A" in grade_counts,
           "grade distribution: " + str(grade_counts))

    # ---- Test 5: Grade C -- stoch 40/60 not turning ----
    print("\nTest 5: Grade C -- stoch 40/60 not turning at entry")
    report("T5_grade_C",
           has_grades and "C" in grade_counts,
           "grade distribution: " + str(grade_counts))

    # ---- Test 6: TDI uses RSI 14 ----
    print("\nTest 6: TDI uses RSI 14 (verify columns exist and are not NaN)")
    has_tdi_price = "tdi_price" in result_graded.columns
    has_tdi_signal = "tdi_signal" in result_graded.columns
    tdi_valid = False
    if has_tdi_price and has_tdi_signal:
        # With RSI 14, first valid TDI should be around bar 14+
        first_valid = np.where(~np.isnan(result_graded["tdi_price"].values))[0]
        if len(first_valid) > 0:
            tdi_valid = first_valid[0] >= 14  # RSI 14 needs 15 bars minimum
    report("T6_tdi_rsi14",
           has_tdi_price and has_tdi_signal and tdi_valid,
           "first valid TDI bar: " + (str(first_valid[0]) if len(first_valid) > 0 else "none"))

    # ---- Test 7: EMA cross columns ----
    print("\nTest 7: EMA cross columns computed correctly")
    has_bull = "ema_cross_bull" in result_graded.columns
    has_bear = "ema_cross_bear" in result_graded.columns
    bull_count = int(result_graded["ema_cross_bull"].sum()) if has_bull else 0
    bear_count = int(result_graded["ema_cross_bear"].sum()) if has_bear else 0
    report("T7_ema_cross_columns",
           has_bull and has_bear and (bull_count + bear_count) > 0,
           "bull crosses: " + str(bull_count) + ", bear crosses: " + str(bear_count))

    # ---- Summary ----
    print("\n" + "=" * 60)
    print("RESULTS: " + str(PASS_COUNT) + " PASS, " + str(FAIL_COUNT) + " FAIL out of " + str(PASS_COUNT + FAIL_COUNT))
    if FAIL_COUNT > 0:
        print("FAILURES:")
        for name, status, detail in RESULTS:
            if status == "FAIL":
                print("  - " + name + ": " + detail)
    print("=" * 60)
    return FAIL_COUNT == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
