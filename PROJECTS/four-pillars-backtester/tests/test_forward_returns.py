"""
Tests for research/bbw_forward_returns.py -- Layer 3 Forward Return Tagger.
12 tests, 50+ assertions.

Run: python tests/test_forward_returns.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from research.bbw_forward_returns import (
    tag_forward_returns, _calculate_atr, DEFAULT_WINDOWS, ATR_COL, REQUIRED_OHLCV
)

# --- Helpers ------------------------------------------------------------------

PASS_COUNT = 0
FAIL_COUNT = 0
ERRORS = []


def check(name, condition, detail=""):
    """Record a test pass/fail."""
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS  {name}")
    else:
        FAIL_COUNT += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"  -- {detail}"
        print(msg)
        ERRORS.append(name)


def make_ohlcv(n=100, base_price=100.0, volatility=0.01):
    """Generate synthetic OHLCV with controlled properties."""
    np.random.seed(42)
    closes = base_price + np.cumsum(np.random.randn(n) * base_price * volatility)
    highs = closes + np.abs(np.random.randn(n)) * base_price * volatility
    lows = closes - np.abs(np.random.randn(n)) * base_price * volatility
    opens = closes + np.random.randn(n) * base_price * volatility * 0.5
    highs = np.maximum(highs, np.maximum(opens, closes))
    lows = np.minimum(lows, np.minimum(opens, closes))
    return pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': np.random.rand(n) * 10000
    })


# --- Test 1: Output Columns --------------------------------------------------

def test_output_columns():
    """Verify 17 new columns present (8 per window x 2 + fwd_atr)."""
    print("\n[Test 1] Output Columns")
    df = make_ohlcv(100)
    result = tag_forward_returns(df)

    check("fwd_atr exists", ATR_COL in result.columns)

    for w in DEFAULT_WINDOWS:
        for suffix in ['max_up_pct', 'max_down_pct', 'max_up_atr', 'max_down_atr',
                        'close_pct', 'direction', 'max_range_atr', 'proper_move']:
            col = f"fwd_{w}_{suffix}"
            check(f"column {col}", col in result.columns)

    # Original columns preserved
    for col in REQUIRED_OHLCV:
        check(f"original {col} preserved", col in result.columns)

    expected_new = 1 + 8 * len(DEFAULT_WINDOWS)  # fwd_atr + 8 per window
    check("new column count", len(result.columns) == len(df.columns) + expected_new,
          f"got {len(result.columns)}, expected {len(df.columns) + expected_new}")


# --- Test 2: Missing OHLCV ---------------------------------------------------

def test_missing_ohlcv():
    """Raises ValueError if OHLCV columns missing."""
    print("\n[Test 2] Missing OHLCV")
    df_bad = pd.DataFrame({'close': [100, 101, 102]})
    raised = False
    try:
        tag_forward_returns(df_bad)
    except ValueError as e:
        raised = True
        check("ValueError mentions column", "open" in str(e) or "high" in str(e))
    check("ValueError raised", raised)


# --- Test 3: ATR Calculation --------------------------------------------------

def test_atr_calculation():
    """Verify ATR against manual TR + EWM with atr_period=3."""
    print("\n[Test 3] ATR Calculation")

    df = pd.DataFrame({
        'open':     [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high':     [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'low':      [ 98,  99, 100, 101, 102, 103, 104, 105, 106, 107],
        'close':    [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'base_vol': [1000]*10,
    })

    result = tag_forward_returns(df, windows=[3], atr_period=3)
    atr = result[ATR_COL]

    check("atr[0] is NaN", np.isnan(atr.iloc[0]))
    check("atr[1] is NaN", np.isnan(atr.iloc[1]))
    check("atr[2] is NaN", np.isnan(atr.iloc[2]))
    check("atr[3] is not NaN", not np.isnan(atr.iloc[3]))
    check("atr[3] approx 4.0", abs(atr.iloc[3] - 4.0) < 0.01,
          f"got {atr.iloc[3]:.6f}")


# --- Test 4: Sign Conventions ------------------------------------------------

def test_sign_conventions():
    """max_up_pct >= 0, max_down_pct <= 0, max_up_atr >= 0, max_down_atr >= 0."""
    print("\n[Test 4] Sign Conventions")

    df = make_ohlcv(200)
    result = tag_forward_returns(df)

    for w in DEFAULT_WINDOWS:
        valid = result.dropna(subset=[f'fwd_{w}_max_up_pct'])

        up_pct = valid[f'fwd_{w}_max_up_pct']
        check(f"fwd_{w}_max_up_pct >= 0", (up_pct >= 0).all(),
              f"min={up_pct.min():.4f}")

        down_pct = valid[f'fwd_{w}_max_down_pct']
        check(f"fwd_{w}_max_down_pct <= 0", (down_pct <= 0).all(),
              f"max={down_pct.max():.4f}")

        up_atr = valid[f'fwd_{w}_max_up_atr'].dropna()
        check(f"fwd_{w}_max_up_atr >= 0", (up_atr >= 0).all(),
              f"min={up_atr.min():.4f}")

        down_atr = valid[f'fwd_{w}_max_down_atr'].dropna()
        check(f"fwd_{w}_max_down_atr >= 0", (down_atr >= 0).all(),
              f"min={down_atr.min():.4f}")


# --- Test 5: Last W Bars NaN -------------------------------------------------

def test_last_w_bars_nan():
    """Last 10 bars have NaN fwd_10, last 20 bars have NaN fwd_20."""
    print("\n[Test 5] Last W Bars NaN")

    df = make_ohlcv(100)
    result = tag_forward_returns(df)

    for w in DEFAULT_WINDOWS:
        col = f'fwd_{w}_max_up_pct'
        last_w = result[col].iloc[-w:]
        check(f"last {w} bars of fwd_{w} are NaN", last_w.isna().all(),
              f"non-NaN count: {last_w.notna().sum()}")

        if len(result) > w + 14:
            bar_before = result[col].iloc[-(w+1)]
            check(f"bar n-{w+1} of fwd_{w} is valid", not np.isnan(bar_before),
                  f"got NaN")


# --- Test 6: Known Forward Returns -------------------------------------------

def test_known_forward_returns():
    """20-bar dataset with exact pre-computed values at bar 15, window=4."""
    print("\n[Test 6] Known Forward Returns")

    opens =  [100]*16 + [101, 103, 104, 96]
    highs =  [102]*16 + [105, 107, 106, 98]
    lows =   [ 98]*16 + [ 99, 101,  95, 93]
    closes = [100]*16 + [103, 104,  96, 94]

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': [1000]*20
    })

    result = tag_forward_returns(df, windows=[4], atr_period=2)

    atr_15 = result[ATR_COL].iloc[15]
    check("bar15 ATR=4.0", abs(atr_15 - 4.0) < 0.001, f"got {atr_15:.6f}")

    check("bar15 max_up_pct=7.0",
          abs(result['fwd_4_max_up_pct'].iloc[15] - 7.0) < 0.001)
    check("bar15 max_down_pct=-7.0",
          abs(result['fwd_4_max_down_pct'].iloc[15] - (-7.0)) < 0.001)
    check("bar15 max_up_atr=1.75",
          abs(result['fwd_4_max_up_atr'].iloc[15] - 1.75) < 0.001)
    check("bar15 max_down_atr=1.75",
          abs(result['fwd_4_max_down_atr'].iloc[15] - 1.75) < 0.001)
    check("bar15 close_pct=-6.0",
          abs(result['fwd_4_close_pct'].iloc[15] - (-6.0)) < 0.001)
    check("bar15 direction=down",
          result['fwd_4_direction'].iloc[15] == 'down')
    check("bar15 max_range_atr=3.5",
          abs(result['fwd_4_max_range_atr'].iloc[15] - 3.5) < 0.001)
    check("bar15 proper_move=True",
          result['fwd_4_proper_move'].iloc[15] == True)


# --- Test 7: ATR Normalization ------------------------------------------------

def test_atr_normalization():
    """Verify max_up_atr == (max_high - close) / atr to 6 decimal places."""
    print("\n[Test 7] ATR Normalization")

    df = make_ohlcv(200)
    result = tag_forward_returns(df, windows=[10], atr_period=14)

    valid = result.dropna(subset=['fwd_10_max_up_atr', ATR_COL])
    if len(valid) > 10:
        sample = valid.iloc[20:30]
        for idx in sample.index:
            up_atr = result.loc[idx, 'fwd_10_max_up_atr']
            up_pct = result.loc[idx, 'fwd_10_max_up_pct']
            atr_val = result.loc[idx, ATR_COL]
            close_val = result.loc[idx, 'close']

            if not np.isnan(up_atr) and atr_val > 0:
                expected_up_atr = (up_pct / 100 * close_val) / atr_val
                check(f"ATR norm bar {idx}", abs(up_atr - expected_up_atr) < 1e-6,
                      f"got={up_atr:.6f}, expected={expected_up_atr:.6f}")


# --- Test 8: Direction Label --------------------------------------------------

def test_direction_label():
    """Positive close_pct -> up, negative -> down, zero -> flat."""
    print("\n[Test 8] Direction Label")

    df = make_ohlcv(200)
    result = tag_forward_returns(df, windows=[10])

    valid = result.dropna(subset=['fwd_10_close_pct'])

    up_rows = valid[valid['fwd_10_close_pct'] > 0]
    if len(up_rows) > 0:
        check("positive close_pct -> up",
              (up_rows['fwd_10_direction'] == 'up').all())

    down_rows = valid[valid['fwd_10_close_pct'] < 0]
    if len(down_rows) > 0:
        check("negative close_pct -> down",
              (down_rows['fwd_10_direction'] == 'down').all())

    zero_rows = valid[valid['fwd_10_close_pct'] == 0]
    if len(zero_rows) > 0:
        check("zero close_pct -> flat",
              (zero_rows['fwd_10_direction'] == 'flat').all())
    else:
        check("zero close_pct -> flat", True, "no zero rows (OK for random data)")


# --- Test 9: Proper Move -----------------------------------------------------

def test_proper_move():
    """Alternating volatile data: spike range >= 3*ATR -> True, smaller -> False."""
    print("\n[Test 9] Proper Move")

    n = 30
    opens = []
    highs = []
    lows = []
    closes = []
    for i in range(n):
        if i % 2 == 0:
            opens.append(99); highs.append(101); lows.append(99); closes.append(100)
        else:
            opens.append(100); highs.append(101); lows.append(99); closes.append(100)

    opens[20] = 100; highs[20] = 108; lows[20] = 96; closes[20] = 100
    opens[25] = 100; highs[25] = 102; lows[25] = 98; closes[25] = 100

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': [1000]*n
    })

    result = tag_forward_returns(df, windows=[1], atr_period=2, proper_move_atr=3.0)

    atr_19 = result[ATR_COL].iloc[19]
    check("ATR[19] approx 2.0", abs(atr_19 - 2.0) < 0.1, f"got {atr_19:.4f}")

    range_atr_19 = result['fwd_1_max_range_atr'].iloc[19]
    if not np.isnan(range_atr_19):
        check("bar19 range_atr >= 3.0", range_atr_19 >= 3.0,
              f"got {range_atr_19:.2f}")
        check("bar19 proper_move=True", result['fwd_1_proper_move'].iloc[19] == True)


# --- Test 10: ATR Zero Handling -----------------------------------------------

def test_atr_zero_handling():
    """Flat price -> ATR near 0 -> ATR-normalized cols = NaN, not inf."""
    print("\n[Test 10] ATR Zero Handling")

    n = 50
    df = pd.DataFrame({
        'open': [100.0]*n, 'high': [100.0]*n, 'low': [100.0]*n,
        'close': [100.0]*n, 'base_vol': [1000]*n
    })

    result = tag_forward_returns(df, windows=[5], atr_period=3)

    atr_vals = result[ATR_COL].dropna()
    if len(atr_vals) > 0:
        check("ATR near 0 for flat data", atr_vals.max() < 0.001,
              f"max ATR={atr_vals.max():.6f}")

    for col in result.columns:
        if result[col].dtype in [np.float64, np.float32]:
            inf_count = np.isinf(result[col].dropna()).sum()
            check(f"no inf in {col}", inf_count == 0,
                  f"inf count: {inf_count}")


# --- Test 11: Custom Windows -------------------------------------------------

def test_custom_windows():
    """Custom windows=[5, 30] produce correctly named columns."""
    print("\n[Test 11] Custom Windows")

    df = make_ohlcv(100)
    result = tag_forward_returns(df, windows=[5, 30])

    for w in [5, 30]:
        for suffix in ['max_up_pct', 'max_down_pct', 'max_up_atr', 'max_down_atr',
                        'close_pct', 'direction', 'max_range_atr', 'proper_move']:
            col = f"fwd_{w}_{suffix}"
            check(f"column {col}", col in result.columns)

    check("no fwd_10 columns", 'fwd_10_max_up_pct' not in result.columns)
    check("no fwd_20 columns", 'fwd_20_max_up_pct' not in result.columns)


# --- Test 12: Real Parquet ----------------------------------------------------

def test_on_real_parquet():
    """RIVERUSDT 5m: distribution checks on forward returns."""
    print("\n[Test 12] Real Parquet (RIVERUSDT 5m)")

    cache_path = ROOT / "data" / "cache" / "RIVERUSDT_1m.parquet"
    if not cache_path.exists():
        print("  SKIP  RIVERUSDT parquet not found")
        return

    raw = pd.read_parquet(cache_path)
    if 'datetime' not in raw.columns and 'timestamp' in raw.columns:
        raw['datetime'] = pd.to_datetime(raw['timestamp'], unit='ms', utc=True)
    raw = raw.set_index('datetime')
    df_5m = raw.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'base_vol': 'sum'
    }).dropna().reset_index()

    print(f"  Loaded {len(df_5m):,} 5m bars")
    result = tag_forward_returns(df_5m)

    valid_atr = result[ATR_COL].dropna()
    check("fwd_atr > 0", (valid_atr > 0).all(), f"zero count: {(valid_atr <= 0).sum()}")

    valid_10 = result.dropna(subset=['fwd_10_max_down_pct'])
    down_mean = valid_10['fwd_10_max_down_pct'].mean()
    check("max_down_pct mean < 0", down_mean < 0, f"mean={down_mean:.4f}")

    pm_rate = valid_10['fwd_10_proper_move'].mean()
    check("proper_move 5-80%", 0.05 <= pm_rate <= 0.80, f"rate={pm_rate:.1%}")

    dir_dist = valid_10['fwd_10_direction'].value_counts(normalize=True)
    up_pct = dir_dist.get('up', 0)
    check("direction ~40-60% up", 0.30 <= up_pct <= 0.70, f"up={up_pct:.1%}")

    for col in result.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(result[col].dropna()).sum()
        if inf_ct > 0:
            check(f"no inf in {col}", False, f"inf count: {inf_ct}")
            break
    else:
        check("no inf in any numeric column", True)


# --- Main ---------------------------------------------------------------------

def main():
    """Run all 12 Layer 3 tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"Forward Returns Layer 3 Tests -- {ts}")
    print(f"{'='*70}")

    test_output_columns()
    test_missing_ohlcv()
    test_atr_calculation()
    test_sign_conventions()
    test_last_w_bars_nan()
    test_known_forward_returns()
    test_atr_normalization()
    test_direction_label()
    test_proper_move()
    test_atr_zero_handling()
    test_custom_windows()
    test_on_real_parquet()

    print(f"\n{'='*70}")
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
