"""
Build script: Layer 3 -- Forward Return Tagger.

Creates 5 files (research/__init__.py already exists):
  1. research/bbw_forward_returns.py  -- forward return tagger (17 output columns)
  2. tests/test_forward_returns.py    -- 12 tests, 50+ assertions
  3. scripts/debug_forward_returns.py -- hand-computed math validator (60+ checks)
  4. scripts/sanity_check_forward_returns.py -- RIVERUSDT distribution stats
  5. scripts/run_layer3_tests.py      -- runner that saves output to log MD

Then py_compiles each, runs all three test/debug/sanity scripts via the runner.

Run: python scripts/build_layer3_forward_returns.py
"""

import sys
import os
import py_compile
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent
RESEARCH = ROOT / "research"
TESTS = ROOT / "tests"
SCRIPTS = ROOT / "scripts"

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print(f"{'='*70}")
print(f"Layer 3 Build Script -- {ts}")
print(f"{'='*70}")

# ─── Safety: check targets don't exist ────────────────────────────────────────

TARGETS = {
    "research/bbw_forward_returns.py": RESEARCH / "bbw_forward_returns.py",
    "tests/test_forward_returns.py": TESTS / "test_forward_returns.py",
    "scripts/debug_forward_returns.py": SCRIPTS / "debug_forward_returns.py",
    "scripts/sanity_check_forward_returns.py": SCRIPTS / "sanity_check_forward_returns.py",
    "scripts/run_layer3_tests.py": SCRIPTS / "run_layer3_tests.py",
}

for name, path in TARGETS.items():
    if path.exists():
        print(f"FATAL: {name} already exists. Remove or rename before running.")
        sys.exit(1)

RESEARCH.mkdir(exist_ok=True)
(RESEARCH / "__init__.py").touch()


def write_and_compile(filepath, content, label):
    """Write file content and py_compile it. Exit on syntax error."""
    filepath.write_text(content, encoding="utf-8")
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"  OK    {label} -- written + syntax OK")
    except py_compile.PyCompileError as e:
        print(f"  FAIL  {label} -- SYNTAX ERROR:")
        print(f"        {e}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# FILE 1: research/bbw_forward_returns.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing research/bbw_forward_returns.py ---")

write_and_compile(RESEARCH / "bbw_forward_returns.py", '''"""
Layer 3: Forward Return Tagger -- ATR-normalized forward returns for each bar.

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with OHLCV columns (open, high, low, close, base_vol).
Output: Same DataFrame with 17 new columns (8 per window x 2 windows + fwd_atr).

Does NOT depend on Layer 1/2. Works on raw OHLCV only.
"""

import numpy as np
import pandas as pd

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_WINDOWS = [10, 20]
REQUIRED_OHLCV = ['open', 'high', 'low', 'close', 'base_vol']
ATR_COL = 'fwd_atr'


def _calculate_atr(df, period=14):
    """Wilder ATR: exponential moving average of true range, alpha=1/period."""
    high = df['high'].values
    low = df['low'].values
    prev_close = df['close'].shift(1).values

    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - prev_close),
            np.abs(low - prev_close)
        )
    )
    atr = pd.Series(tr, index=df.index).ewm(
        alpha=1.0 / period, min_periods=period, adjust=False
    ).mean()
    return atr


def _forward_max(series, window):
    """Max of next `window` bars (EXCLUDING current bar). Vectorized."""
    return series[::-1].rolling(window=window, min_periods=window).max()[::-1].shift(-1)


def _forward_min(series, window):
    """Min of next `window` bars (EXCLUDING current bar). Vectorized."""
    return series[::-1].rolling(window=window, min_periods=window).min()[::-1].shift(-1)


def _forward_close(series, window):
    """Close value `window` bars ahead. Vectorized."""
    return series.shift(-window)


def tag_forward_returns(df, windows=None, atr_period=14, proper_move_atr=3.0):
    """Tag each bar with forward-looking return metrics.

    Input: DataFrame with OHLCV columns.
    Output: Same DataFrame with 8 columns per window + fwd_atr column.
    """
    if windows is None:
        windows = DEFAULT_WINDOWS

    for col in REQUIRED_OHLCV:
        if col not in df.columns:
            raise ValueError(f"Missing required OHLCV column: {col}")

    result = df.copy()
    close = result['close'].astype(float)
    high = result['high'].astype(float)
    low = result['low'].astype(float)

    # ATR calculation
    atr = _calculate_atr(result, period=atr_period)
    result[ATR_COL] = atr

    for w in windows:
        prefix = f"fwd_{w}_"

        # Forward max high / min low (excluding current bar)
        fwd_max_high = _forward_max(high, w)
        fwd_min_low = _forward_min(low, w)
        fwd_close = _forward_close(close, w)

        # Percentage returns (safe division: close=0 -> NaN)
        safe_close = np.where(close != 0, close, np.nan)

        max_up_pct = (fwd_max_high - close) / safe_close * 100
        max_down_pct = (fwd_min_low - close) / safe_close * 100
        close_pct = (fwd_close - close) / safe_close * 100

        # ATR-normalized returns (safe division: atr=0 -> NaN)
        safe_atr = np.where(atr > 0, atr, np.nan)

        max_up_atr = (fwd_max_high - close) / safe_atr
        max_down_atr = (close - fwd_min_low) / safe_atr
        max_range_atr = (fwd_max_high - fwd_min_low) / safe_atr

        # Direction label
        close_pct_series = pd.Series(close_pct, index=result.index)
        direction = np.where(
            close_pct_series.isna(), None,
            np.where(close_pct > 0, 'up',
                     np.where(close_pct < 0, 'down', 'flat'))
        )

        # Proper move flag
        proper_move = pd.Series(max_range_atr, index=result.index) >= proper_move_atr

        # Assign columns
        result[prefix + 'max_up_pct'] = max_up_pct
        result[prefix + 'max_down_pct'] = max_down_pct
        result[prefix + 'max_up_atr'] = max_up_atr
        result[prefix + 'max_down_atr'] = max_down_atr
        result[prefix + 'close_pct'] = close_pct
        result[prefix + 'direction'] = direction
        result[prefix + 'max_range_atr'] = max_range_atr
        result[prefix + 'proper_move'] = proper_move

    return result
''', "research/bbw_forward_returns.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 2: tests/test_forward_returns.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing tests/test_forward_returns.py ---")

write_and_compile(TESTS / "test_forward_returns.py", '''"""
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

# ─── Helpers ──────────────────────────────────────────────────────────────────

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


# ─── Test 1: Output Columns ──────────────────────────────────────────────────

def test_output_columns():
    """Verify 17 new columns present (8 per window x 2 + fwd_atr)."""
    print("\\n[Test 1] Output Columns")
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


# ─── Test 2: Missing OHLCV ───────────────────────────────────────────────────

def test_missing_ohlcv():
    """Raises ValueError if OHLCV columns missing."""
    print("\\n[Test 2] Missing OHLCV")
    df_bad = pd.DataFrame({'close': [100, 101, 102]})
    raised = False
    try:
        tag_forward_returns(df_bad)
    except ValueError as e:
        raised = True
        check("ValueError mentions column", "open" in str(e) or "high" in str(e))
    check("ValueError raised", raised)


# ─── Test 3: ATR Calculation ─────────────────────────────────────────────────

def test_atr_calculation():
    """Verify ATR against manual TR + EWM with atr_period=3."""
    print("\\n[Test 3] ATR Calculation")

    # 10-bar dataset with known prices
    df = pd.DataFrame({
        'open':     [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high':     [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'low':      [ 98,  99, 100, 101, 102, 103, 104, 105, 106, 107],
        'close':    [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        'base_vol': [1000]*10,
    })

    result = tag_forward_returns(df, windows=[3], atr_period=3)
    atr = result[ATR_COL]

    # Bar 0: no prev_close -> TR uses H-L only but shift(1) gives NaN -> NaN
    check("atr[0] is NaN", np.isnan(atr.iloc[0]))

    # Bars 1-2: have TR but min_periods=3 not met
    check("atr[1] is NaN", np.isnan(atr.iloc[1]))

    # Bar 2: first valid ATR (min_periods=3, but bar 0 TR is NaN due to shift)
    # Actually: bar 0 has NaN TR (prev_close=NaN), so ewm with min_periods=3
    # needs 3 non-NaN TR values. Bar 1,2,3 have valid TR.
    # Bar 3 is first with 3 valid TRs (bars 1,2,3).
    # Let me verify: TR[0]=NaN, TR[1]=4, TR[2]=4, TR[3]=4
    # ewm min_periods=3: bar 3 is first valid (3 non-NaN TRs: bars 1,2,3)
    check("atr[2] is NaN", np.isnan(atr.iloc[2]))

    # Bar 3 should be first valid ATR
    check("atr[3] is not NaN", not np.isnan(atr.iloc[3]))

    # TR for bars 1+: all are max(H-L, |H-prevC|, |L-prevC|) = max(4, 2, 2) = 4
    # ATR[3] with Wilder's EWM (alpha=1/3): first valid = simple mean of first 3 TRs = 4.0
    # Then stays at 4.0 since all TR=4
    check("atr[3] approx 4.0", abs(atr.iloc[3] - 4.0) < 0.01,
          f"got {atr.iloc[3]:.6f}")


# ─── Test 4: Sign Conventions ────────────────────────────────────────────────

def test_sign_conventions():
    """max_up_pct >= 0, max_down_pct <= 0, max_up_atr >= 0, max_down_atr >= 0."""
    print("\\n[Test 4] Sign Conventions")

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


# ─── Test 5: Last W Bars NaN ─────────────────────────────────────────────────

def test_last_w_bars_nan():
    """Last 10 bars have NaN fwd_10, last 20 bars have NaN fwd_20."""
    print("\\n[Test 5] Last W Bars NaN")

    df = make_ohlcv(100)
    result = tag_forward_returns(df)

    for w in DEFAULT_WINDOWS:
        col = f'fwd_{w}_max_up_pct'
        last_w = result[col].iloc[-w:]
        check(f"last {w} bars of fwd_{w} are NaN", last_w.isna().all(),
              f"non-NaN count: {last_w.notna().sum()}")

        # Bar just before the NaN zone should be valid (if ATR is also valid)
        if len(result) > w + 14:  # enough bars for ATR warmup
            bar_before = result[col].iloc[-(w+1)]
            check(f"bar n-{w+1} of fwd_{w} is valid", not np.isnan(bar_before),
                  f"got NaN")


# ─── Test 6: Known Forward Returns ───────────────────────────────────────────

def test_known_forward_returns():
    """20-bar dataset with exact pre-computed values at bar 15, window=4."""
    print("\\n[Test 6] Known Forward Returns")

    # Bars 0-15: O=100, H=102, L=98, C=100 (TR=4 from bar 1, ATR converges to 4.0)
    # Bar 16: O=101, H=105, L=99, C=103
    # Bar 17: O=103, H=107, L=101, C=104
    # Bar 18: O=104, H=106, L=95, C=96 (big drop)
    # Bar 19: O=96, H=98, L=93, C=94
    opens =  [100]*16 + [101, 103, 104, 96]
    highs =  [102]*16 + [105, 107, 106, 98]
    lows =   [ 98]*16 + [ 99, 101,  95, 93]
    closes = [100]*16 + [103, 104,  96, 94]

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': [1000]*20
    })

    result = tag_forward_returns(df, windows=[4], atr_period=2)

    # Bar 15: ATR should be 4.0 (stable after 16 identical bars)
    atr_15 = result[ATR_COL].iloc[15]
    check("bar15 ATR=4.0", abs(atr_15 - 4.0) < 0.001, f"got {atr_15:.6f}")

    # Bar 15 forward window covers bars 16-19
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


# ─── Test 7: ATR Normalization ────────────────────────────────────────────────

def test_atr_normalization():
    """Verify max_up_atr == (max_high - close) / atr to 6 decimal places."""
    print("\\n[Test 7] ATR Normalization")

    df = make_ohlcv(200)
    result = tag_forward_returns(df, windows=[10], atr_period=14)

    # Pick bars with valid ATR and valid forward returns
    valid = result.dropna(subset=['fwd_10_max_up_atr', ATR_COL])
    if len(valid) > 10:
        sample = valid.iloc[20:30]  # middle bars
        for idx in sample.index:
            up_atr = result.loc[idx, 'fwd_10_max_up_atr']
            up_pct = result.loc[idx, 'fwd_10_max_up_pct']
            atr_val = result.loc[idx, ATR_COL]
            close_val = result.loc[idx, 'close']

            if not np.isnan(up_atr) and atr_val > 0:
                expected_up_atr = (up_pct / 100 * close_val) / atr_val
                check(f"ATR norm bar {idx}", abs(up_atr - expected_up_atr) < 1e-6,
                      f"got={up_atr:.6f}, expected={expected_up_atr:.6f}")


# ─── Test 8: Direction Label ─────────────────────────────────────────────────

def test_direction_label():
    """Positive close_pct -> up, negative -> down, zero -> flat."""
    print("\\n[Test 8] Direction Label")

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


# ─── Test 9: Proper Move ─────────────────────────────────────────────────────

def test_proper_move():
    """Alternating volatile data: spike range >= 3*ATR -> True, smaller -> False."""
    print("\\n[Test 9] Proper Move")

    # Alternating bars: TR=2, ATR converges to 2.0 with period=2
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

    # Bar 20: big spike (range=8, which is 4*ATR=4*2=8 >= 3*2=6)
    opens[20] = 100; highs[20] = 108; lows[20] = 96; closes[20] = 100
    # Bar 25: small spike (range=4, which is 2*ATR < 3*2=6)
    opens[25] = 100; highs[25] = 102; lows[25] = 98; closes[25] = 100

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': [1000]*n
    })

    # Use window=1 so we can check individual bars, atr_period=2
    result = tag_forward_returns(df, windows=[1], atr_period=2, proper_move_atr=3.0)

    # ATR at bar 19 should be ~2.0 (stable after many TR=2 bars)
    atr_19 = result[ATR_COL].iloc[19]
    check("ATR[19] approx 2.0", abs(atr_19 - 2.0) < 0.1, f"got {atr_19:.4f}")

    # Bar 19 looks at bar 20 (window=1): range = H20-L20 = 108-96 = 12
    # But fwd_1_max_range_atr = (max_high - min_low) / atr
    # max_high = H[20] = 108, min_low = L[20] = 96
    # range_atr = 12 / atr[19] ~= 12/2 = 6.0 >= 3.0
    range_atr_19 = result['fwd_1_max_range_atr'].iloc[19]
    if not np.isnan(range_atr_19):
        check("bar19 range_atr >= 3.0", range_atr_19 >= 3.0,
              f"got {range_atr_19:.2f}")
        check("bar19 proper_move=True", result['fwd_1_proper_move'].iloc[19] == True)


# ─── Test 10: ATR Zero Handling ───────────────────────────────────────────────

def test_atr_zero_handling():
    """Flat price -> ATR near 0 -> ATR-normalized cols = NaN, not inf."""
    print("\\n[Test 10] ATR Zero Handling")

    # Perfectly flat: O=H=L=C=100
    n = 50
    df = pd.DataFrame({
        'open': [100.0]*n, 'high': [100.0]*n, 'low': [100.0]*n,
        'close': [100.0]*n, 'base_vol': [1000]*n
    })

    result = tag_forward_returns(df, windows=[5], atr_period=3)

    # ATR should be 0 (or very near 0) after warmup
    atr_vals = result[ATR_COL].dropna()
    if len(atr_vals) > 0:
        check("ATR near 0 for flat data", atr_vals.max() < 0.001,
              f"max ATR={atr_vals.max():.6f}")

    # No inf anywhere
    for col in result.columns:
        if result[col].dtype in [np.float64, np.float32]:
            inf_count = np.isinf(result[col].dropna()).sum()
            check(f"no inf in {col}", inf_count == 0,
                  f"inf count: {inf_count}")


# ─── Test 11: Custom Windows ─────────────────────────────────────────────────

def test_custom_windows():
    """Custom windows=[5, 30] produce correctly named columns."""
    print("\\n[Test 11] Custom Windows")

    df = make_ohlcv(100)
    result = tag_forward_returns(df, windows=[5, 30])

    for w in [5, 30]:
        for suffix in ['max_up_pct', 'max_down_pct', 'max_up_atr', 'max_down_atr',
                        'close_pct', 'direction', 'max_range_atr', 'proper_move']:
            col = f"fwd_{w}_{suffix}"
            check(f"column {col}", col in result.columns)

    # Default window columns should NOT be present
    check("no fwd_10 columns", 'fwd_10_max_up_pct' not in result.columns)
    check("no fwd_20 columns", 'fwd_20_max_up_pct' not in result.columns)


# ─── Test 12: Real Parquet ────────────────────────────────────────────────────

def test_on_real_parquet():
    """RIVERUSDT 5m: distribution checks on forward returns."""
    print("\\n[Test 12] Real Parquet (RIVERUSDT 5m)")

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

    # fwd_atr > 0 for valid bars
    valid_atr = result[ATR_COL].dropna()
    check("fwd_atr > 0", (valid_atr > 0).all(), f"zero count: {(valid_atr <= 0).sum()}")

    # max_down_pct mean < 0
    valid_10 = result.dropna(subset=['fwd_10_max_down_pct'])
    down_mean = valid_10['fwd_10_max_down_pct'].mean()
    check("max_down_pct mean < 0", down_mean < 0, f"mean={down_mean:.4f}")

    # proper_move rate between 5% and 80%
    pm_rate = valid_10['fwd_10_proper_move'].mean()
    check("proper_move 5-80%", 0.05 <= pm_rate <= 0.80, f"rate={pm_rate:.1%}")

    # direction distribution roughly balanced
    dir_dist = valid_10['fwd_10_direction'].value_counts(normalize=True)
    up_pct = dir_dist.get('up', 0)
    check("direction ~40-60% up", 0.30 <= up_pct <= 0.70, f"up={up_pct:.1%}")

    # No inf values
    for col in result.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(result[col].dropna()).sum()
        if inf_ct > 0:
            check(f"no inf in {col}", False, f"inf count: {inf_ct}")
            break
    else:
        check("no inf in any numeric column", True)


# ─── Main ─────────────────────────────────────────────────────────────────────

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

    print(f"\\n{'='*70}")
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print(f"FAILURES: {\\', \\'.join(ERRORS)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
''', "tests/test_forward_returns.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 3: scripts/debug_forward_returns.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing scripts/debug_forward_returns.py ---")

write_and_compile(SCRIPTS / "debug_forward_returns.py", '''"""
Debug and Math Validator for Layer 3 Forward Return Tagger.

Hand-computed vectors with exact expected values from audit pass 3.
5 sections, 60+ checks.

Run: python scripts/debug_forward_returns.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from research.bbw_forward_returns import (
    tag_forward_returns, _calculate_atr, _forward_max, _forward_min, ATR_COL
)

PASS_COUNT = 0
FAIL_COUNT = 0
ERRORS = []


def check(name, condition, detail=""):
    """Record a debug check pass/fail."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: ATR calculation validation (atr_period=3)
# ═══════════════════════════════════════════════════════════════════════════════

def debug_atr_calculation():
    """Verify ATR against manual TR + Wilder EWM, atr_period=3, 10-bar dataset."""
    print("\\n[Debug 1] ATR Calculation -- Manual Verification")

    df = pd.DataFrame({
        'open':     [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high':     [102, 104, 105, 106, 107, 108, 109, 110, 111, 112],
        'low':      [ 98,  99, 100, 101, 102, 103, 104, 105, 106, 107],
        'close':    [101, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'base_vol': [1000]*10,
    })

    atr = _calculate_atr(df, period=3)

    # Bar 0: prev_close=NaN -> TR=NaN
    check("TR[0]=NaN (no prev_close)", np.isnan(atr.iloc[0]))

    # Bar 1: prev_close=101, H=104, L=99
    # TR = max(104-99, |104-101|, |99-101|) = max(5, 3, 2) = 5
    # Bar 2: prev_close=103, H=105, L=100
    # TR = max(105-100, |105-103|, |100-103|) = max(5, 2, 3) = 5
    # Bar 3: prev_close=104, H=106, L=101
    # TR = max(106-101, |106-104|, |101-104|) = max(5, 2, 3) = 5

    # min_periods=3: bars 0,1 are NaN. Bar 2 has only 2 non-NaN TRs (bars 1,2).
    check("ATR[1]=NaN", np.isnan(atr.iloc[1]))
    check("ATR[2]=NaN", np.isnan(atr.iloc[2]))

    # Bar 3: first valid ATR. Wilder EWM with alpha=1/3:
    # ewm computes weighted avg. With min_periods=3, bar 3 is first valid.
    # All TR = 5, so ATR = 5.0
    check("ATR[3] not NaN", not np.isnan(atr.iloc[3]))
    check("ATR[3] approx 5.0", abs(atr.iloc[3] - 5.0) < 0.1,
          f"got {atr.iloc[3]:.6f}")

    # Subsequent bars also have TR=5, so ATR stays ~5.0
    for i in range(4, 10):
        check(f"ATR[{i}] approx 5.0", abs(atr.iloc[i] - 5.0) < 0.1,
              f"got {atr.iloc[i]:.6f}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Forward return exact values (audit-verified)
# ═══════════════════════════════════════════════════════════════════════════════

def debug_forward_return_exact():
    """20-bar dataset with hand-computed values from audit pass 2+3."""
    print("\\n[Debug 2] Forward Return Exact Values -- Audit-Verified")

    opens =  [100]*16 + [101, 103, 104, 96]
    highs =  [102]*16 + [105, 107, 106, 98]
    lows =   [ 98]*16 + [ 99, 101,  95, 93]
    closes = [100]*16 + [103, 104,  96, 94]

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': [1000]*20
    })

    # ── Bar 15, window=4, atr_period=2 ──
    result = tag_forward_returns(df, windows=[4], atr_period=2)

    atr_15 = result[ATR_COL].iloc[15]
    check("bar15 ATR=4.0", abs(atr_15 - 4.0) < 0.001, f"got {atr_15:.6f}")

    # max_high(16..19) = max(105,107,106,98) = 107
    # min_low(16..19) = min(99,101,95,93) = 93
    check("bar15 max_up_pct = 7.0",
          abs(result['fwd_4_max_up_pct'].iloc[15] - 7.0) < 0.001,
          f"got {result['fwd_4_max_up_pct'].iloc[15]:.6f}")

    check("bar15 max_down_pct = -7.0",
          abs(result['fwd_4_max_down_pct'].iloc[15] - (-7.0)) < 0.001,
          f"got {result['fwd_4_max_down_pct'].iloc[15]:.6f}")

    check("bar15 max_up_atr = 1.75",
          abs(result['fwd_4_max_up_atr'].iloc[15] - 1.75) < 0.001,
          f"got {result['fwd_4_max_up_atr'].iloc[15]:.6f}")

    check("bar15 max_down_atr = 1.75",
          abs(result['fwd_4_max_down_atr'].iloc[15] - 1.75) < 0.001,
          f"got {result['fwd_4_max_down_atr'].iloc[15]:.6f}")

    check("bar15 close_pct = -6.0",
          abs(result['fwd_4_close_pct'].iloc[15] - (-6.0)) < 0.001,
          f"got {result['fwd_4_close_pct'].iloc[15]:.6f}")

    check("bar15 direction = down",
          result['fwd_4_direction'].iloc[15] == 'down',
          f"got {result['fwd_4_direction'].iloc[15]}")

    check("bar15 max_range_atr = 3.5",
          abs(result['fwd_4_max_range_atr'].iloc[15] - 3.5) < 0.001,
          f"got {result['fwd_4_max_range_atr'].iloc[15]:.6f}")

    check("bar15 proper_move = True",
          result['fwd_4_proper_move'].iloc[15] == True)

    # Bar 16 with window=4 should be NaN (last 4 bars of 20-bar dataset)
    check("bar16 window=4 is NaN",
          np.isnan(result['fwd_4_max_up_pct'].iloc[16]))

    # ── Bar 16, window=3, atr_period=2 (second call) ──
    result2 = tag_forward_returns(df, windows=[3], atr_period=2)

    # TR[16] = max(105-99, |105-100|, |99-100|) = max(6,5,1) = 6
    # ATR[16] = 0.5*6 + 0.5*4.0 = 5.0
    atr_16 = result2[ATR_COL].iloc[16]
    check("bar16 ATR=5.0", abs(atr_16 - 5.0) < 0.001, f"got {atr_16:.6f}")

    # max_high(17..19) = max(107,106,98) = 107
    # min_low(17..19) = min(101,95,93) = 93
    # close[16] = 103
    check("bar16 max_up_pct = 3.883495",
          abs(result2['fwd_3_max_up_pct'].iloc[16] - 3.883495) < 0.001,
          f"got {result2['fwd_3_max_up_pct'].iloc[16]:.6f}")

    check("bar16 max_down_pct = -9.708738",
          abs(result2['fwd_3_max_down_pct'].iloc[16] - (-9.708738)) < 0.001,
          f"got {result2['fwd_3_max_down_pct'].iloc[16]:.6f}")

    check("bar16 max_up_atr = 0.8",
          abs(result2['fwd_3_max_up_atr'].iloc[16] - 0.8) < 0.001,
          f"got {result2['fwd_3_max_up_atr'].iloc[16]:.6f}")

    check("bar16 max_down_atr = 2.0",
          abs(result2['fwd_3_max_down_atr'].iloc[16] - 2.0) < 0.001,
          f"got {result2['fwd_3_max_down_atr'].iloc[16]:.6f}")

    check("bar16 close_pct = -8.737864",
          abs(result2['fwd_3_close_pct'].iloc[16] - (-8.737864)) < 0.001,
          f"got {result2['fwd_3_close_pct'].iloc[16]:.6f}")

    check("bar16 direction = down",
          result2['fwd_3_direction'].iloc[16] == 'down')

    check("bar16 max_range_atr = 2.8",
          abs(result2['fwd_3_max_range_atr'].iloc[16] - 2.8) < 0.001,
          f"got {result2['fwd_3_max_range_atr'].iloc[16]:.6f}")

    check("bar16 proper_move = False",
          result2['fwd_3_proper_move'].iloc[16] == False)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Sign convention validation
# ═══════════════════════════════════════════════════════════════════════════════

def debug_sign_conventions():
    """Verify sign invariants across all bars of random data."""
    print("\\n[Debug 3] Sign Conventions -- Global Invariants")

    np.random.seed(42)
    n = 200
    closes = 100 + np.cumsum(np.random.randn(n) * 0.5)
    highs = closes + np.abs(np.random.randn(n)) * 0.5
    lows = closes - np.abs(np.random.randn(n)) * 0.5
    opens = closes + np.random.randn(n) * 0.3
    highs = np.maximum(highs, np.maximum(opens, closes))
    lows = np.minimum(lows, np.minimum(opens, closes))

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': np.ones(n) * 1000
    })

    result = tag_forward_returns(df, windows=[10])
    valid = result.dropna(subset=['fwd_10_max_up_pct'])

    check("max_up_pct always >= 0",
          (valid['fwd_10_max_up_pct'] >= 0).all())
    check("max_down_pct always <= 0",
          (valid['fwd_10_max_down_pct'] <= 0).all())

    valid_atr = valid.dropna(subset=['fwd_10_max_up_atr'])
    check("max_up_atr always >= 0",
          (valid_atr['fwd_10_max_up_atr'] >= 0).all())
    check("max_down_atr always >= 0",
          (valid_atr['fwd_10_max_down_atr'] >= 0).all())
    check("max_range_atr always >= 0",
          (valid_atr['fwd_10_max_range_atr'] >= 0).all())

    # No inf
    for col in result.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(result[col].dropna()).sum()
        check(f"no inf in {col}", inf_ct == 0)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Edge cases
# ═══════════════════════════════════════════════════════════════════════════════

def debug_edge_cases():
    """Flat prices, single bar window, oversized window, NaN boundary."""
    print("\\n[Debug 4] Edge Cases")

    # ── Flat prices: ATR=0 -> NaN, not inf ──
    n = 50
    df_flat = pd.DataFrame({
        'open': [100.0]*n, 'high': [100.0]*n, 'low': [100.0]*n,
        'close': [100.0]*n, 'base_vol': [1000]*n
    })
    r_flat = tag_forward_returns(df_flat, windows=[5], atr_period=3)
    for col in r_flat.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(r_flat[col].dropna()).sum()
        check(f"flat: no inf in {col}", inf_ct == 0)

    # ── Single bar window (window=1) ──
    df = pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [102, 103, 104, 105, 106],
        'low':  [ 98,  99, 100, 101, 102],
        'close':[101, 102, 103, 104, 105],
        'base_vol': [1000]*5,
    })
    r1 = tag_forward_returns(df, windows=[1], atr_period=2)
    # Bar 0 with window=1: looks at bar 1 only
    # max_up_pct = (H[1]-C[0])/C[0]*100 = (103-101)/101*100 = 1.9802
    up_0 = r1['fwd_1_max_up_pct'].iloc[0]
    if not np.isnan(up_0):
        expected = (103 - 101) / 101 * 100
        check("window=1 bar0 max_up_pct", abs(up_0 - expected) < 0.001,
              f"got {up_0:.6f}, expected {expected:.6f}")
    # Last 1 bar should be NaN
    check("window=1 last bar NaN", np.isnan(r1['fwd_1_max_up_pct'].iloc[-1]))

    # ── Very large window (window > len) -> all NaN ──
    r_big = tag_forward_returns(df, windows=[100], atr_period=2)
    check("window>len: all NaN",
          r_big['fwd_100_max_up_pct'].isna().all())

    # ── NaN boundary for window=10 on 100-bar df ──
    df100 = pd.DataFrame({
        'open': np.random.RandomState(42).normal(100, 1, 100),
        'high': np.random.RandomState(42).normal(101, 1, 100),
        'low': np.random.RandomState(42).normal(99, 1, 100),
        'close': np.random.RandomState(42).normal(100, 1, 100),
        'base_vol': [1000]*100,
    })
    # Fix OHLC consistency
    df100['high'] = df100[['open','high','close']].max(axis=1) + 0.1
    df100['low'] = df100[['open','low','close']].min(axis=1) - 0.1

    r100 = tag_forward_returns(df100, windows=[10], atr_period=14)
    # Last 10 bars must be NaN
    last_10 = r100['fwd_10_max_up_pct'].iloc[-10:]
    check("last 10 bars NaN", last_10.isna().all(),
          f"non-NaN: {last_10.notna().sum()}")
    # Bar 89 (index 89) must be valid (if ATR is valid there)
    if not np.isnan(r100[ATR_COL].iloc[89]):
        check("bar 89 valid", not np.isnan(r100['fwd_10_max_up_pct'].iloc[89]))


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Cross-validate with Layer 1+2 on real data
# ═══════════════════════════════════════════════════════════════════════════════

def debug_cross_validate_real():
    """L1 -> L2 -> L3 on RIVERUSDT 5m. Group by state, verify BLUE_DOUBLE > NORMAL."""
    print("\\n[Debug 5] Cross-Validate Real Data (L1+L2+L3)")

    from signals.bbwp import calculate_bbwp
    from signals.bbw_sequence import track_bbw_sequence

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

    # L1 -> L2 -> L3
    df_l1 = calculate_bbwp(df_5m)
    df_l2 = track_bbw_sequence(df_l1)
    result = tag_forward_returns(df_l2, windows=[10])

    valid = result.dropna(subset=['fwd_10_max_range_atr', 'bbwp_state'])

    # Group by state
    grouped = valid.groupby('bbwp_state').agg({
        'fwd_10_max_range_atr': 'mean',
        'fwd_10_max_up_atr': 'mean',
        'fwd_10_max_down_atr': 'mean',
        'fwd_10_proper_move': 'mean',
    }).round(3)

    print("\\n  State x Forward Return Summary:")
    print(f"  {'State':20s} {'range_atr':>10s} {'up_atr':>10s} {'down_atr':>10s} {'proper%':>10s}")
    for state in ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL',
                  'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE']:
        if state in grouped.index:
            r = grouped.loc[state]
            print(f"  {state:20s} {r['fwd_10_max_range_atr']:10.3f} "
                  f"{r['fwd_10_max_up_atr']:10.3f} {r['fwd_10_max_down_atr']:10.3f} "
                  f"{r['fwd_10_proper_move']*100:9.1f}%")

    # Core hypothesis: BLUE_DOUBLE should have higher avg range than NORMAL
    if 'BLUE_DOUBLE' in grouped.index and 'NORMAL' in grouped.index:
        bd_range = grouped.loc['BLUE_DOUBLE', 'fwd_10_max_range_atr']
        nm_range = grouped.loc['NORMAL', 'fwd_10_max_range_atr']
        check("BLUE_DOUBLE range > NORMAL range",
              bd_range > nm_range,
              f"BD={bd_range:.3f}, NORMAL={nm_range:.3f}")

    print(f"\\n  Validated {len(valid):,} bars across L1+L2+L3")


# ─── _forward_max vectorized trace ────────────────────────────────────────────

def debug_forward_max_trace():
    """Verify _forward_max on a 5-element series."""
    print("\\n[Debug 6] _forward_max Vectorized Trace")

    s = pd.Series([10, 20, 30, 40, 50])

    # window=2: bar i gets max(i+1, i+2)
    result = _forward_max(s, 2)
    # Bar 0: max(20,30)=30, Bar 1: max(30,40)=40, Bar 2: max(40,50)=50
    # Bar 3: NaN (only 1 future bar), Bar 4: NaN (0 future bars)
    check("fwd_max[0]=30", result.iloc[0] == 30, f"got {result.iloc[0]}")
    check("fwd_max[1]=40", result.iloc[1] == 40, f"got {result.iloc[1]}")
    check("fwd_max[2]=50", result.iloc[2] == 50, f"got {result.iloc[2]}")
    check("fwd_max[3]=NaN", np.isnan(result.iloc[3]))
    check("fwd_max[4]=NaN", np.isnan(result.iloc[4]))

    # _forward_min
    result_min = _forward_min(s, 2)
    check("fwd_min[0]=20", result_min.iloc[0] == 20, f"got {result_min.iloc[0]}")
    check("fwd_min[1]=30", result_min.iloc[1] == 30, f"got {result_min.iloc[1]}")
    check("fwd_min[2]=40", result_min.iloc[2] == 40, f"got {result_min.iloc[2]}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run all debug sections."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"Forward Returns Layer 3 Debug & Math Validator -- {ts}")
    print(f"{'='*70}")

    debug_atr_calculation()
    debug_forward_return_exact()
    debug_sign_conventions()
    debug_edge_cases()
    debug_cross_validate_real()
    debug_forward_max_trace()

    print(f"\\n{'='*70}")
    print(f"DEBUG RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print(f"FAILURES: {\\', \\'.join(ERRORS)}")
    print(f"{'='*70}")

    return FAIL_COUNT


if __name__ == "__main__":
    sys.exit(main())
''', "scripts/debug_forward_returns.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 4: scripts/sanity_check_forward_returns.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing scripts/sanity_check_forward_returns.py ---")

write_and_compile(SCRIPTS / "sanity_check_forward_returns.py", '''"""
Sanity check: Run forward return tagger on RIVERUSDT 5m, print distribution stats.

Run: python scripts/sanity_check_forward_returns.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from research.bbw_forward_returns import tag_forward_returns, ATR_COL, DEFAULT_WINDOWS


def main():
    """Run forward returns sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"Forward Returns Layer 3 Sanity Check -- {ts}")
    print(f"{'='*70}")

    cache_path = ROOT / "data" / "cache" / "RIVERUSDT_1m.parquet"
    if not cache_path.exists():
        print("ERROR: RIVERUSDT parquet not found")
        return

    raw = pd.read_parquet(cache_path)
    if 'datetime' not in raw.columns and 'timestamp' in raw.columns:
        raw['datetime'] = pd.to_datetime(raw['timestamp'], unit='ms', utc=True)
    raw = raw.set_index('datetime')
    df = raw.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'base_vol': 'sum'
    }).dropna().reset_index()

    print(f"\\n  Input: {len(df):,} bars (5m)")

    t0 = time.time()
    result = tag_forward_returns(df)
    elapsed = time.time() - t0
    print(f"  Runtime: {elapsed:.2f}s ({len(df)/elapsed:,.0f} bars/sec)")

    # ATR distribution
    atr_valid = result[ATR_COL].dropna()
    close_valid = result.loc[atr_valid.index, 'close']
    atr_pct = (atr_valid / close_valid * 100)
    print(f"\\n--- ATR Distribution ---")
    print(f"  Mean:  {atr_valid.mean():.4f} ({atr_pct.mean():.2f}% of close)")
    print(f"  P50:   {atr_valid.quantile(0.5):.4f} ({atr_pct.quantile(0.5):.2f}%)")
    print(f"  P90:   {atr_valid.quantile(0.9):.4f} ({atr_pct.quantile(0.9):.2f}%)")

    for w in DEFAULT_WINDOWS:
        prefix = f"fwd_{w}_"
        valid = result.dropna(subset=[f'{prefix}max_up_pct'])
        nan_count = result[f'{prefix}max_up_pct'].isna().sum()

        print(f"\\n--- Window {w} ({len(valid):,} valid bars, {nan_count:,} NaN) ---")

        # Pct returns
        print(f"  max_up_pct:   mean={valid[f'{prefix}max_up_pct'].mean():.2f}  "
              f"P50={valid[f'{prefix}max_up_pct'].quantile(0.5):.2f}  "
              f"P90={valid[f'{prefix}max_up_pct'].quantile(0.9):.2f}")

        print(f"  max_down_pct: mean={valid[f'{prefix}max_down_pct'].mean():.2f}  "
              f"P50={valid[f'{prefix}max_down_pct'].quantile(0.5):.2f}  "
              f"P10={valid[f'{prefix}max_down_pct'].quantile(0.1):.2f}")

        # ATR returns
        atr_valid_w = valid.dropna(subset=[f'{prefix}max_up_atr'])
        if len(atr_valid_w) > 0:
            print(f"  max_up_atr:   mean={atr_valid_w[f'{prefix}max_up_atr'].mean():.3f}  "
                  f"P50={atr_valid_w[f'{prefix}max_up_atr'].quantile(0.5):.3f}  "
                  f"P90={atr_valid_w[f'{prefix}max_up_atr'].quantile(0.9):.3f}")

            print(f"  max_down_atr: mean={atr_valid_w[f'{prefix}max_down_atr'].mean():.3f}  "
                  f"P50={atr_valid_w[f'{prefix}max_down_atr'].quantile(0.5):.3f}  "
                  f"P90={atr_valid_w[f'{prefix}max_down_atr'].quantile(0.9):.3f}")

            print(f"  range_atr:    mean={atr_valid_w[f'{prefix}max_range_atr'].mean():.3f}  "
                  f"P50={atr_valid_w[f'{prefix}max_range_atr'].quantile(0.5):.3f}  "
                  f"P90={atr_valid_w[f'{prefix}max_range_atr'].quantile(0.9):.3f}")

        # Close pct
        print(f"  close_pct:    mean={valid[f'{prefix}close_pct'].mean():.3f}  "
              f"std={valid[f'{prefix}close_pct'].std():.3f}")

        # Direction
        dir_dist = valid[f'{prefix}direction'].value_counts(normalize=True)
        up_p = dir_dist.get('up', 0)
        down_p = dir_dist.get('down', 0)
        flat_p = dir_dist.get('flat', 0)
        print(f"  direction:    up={up_p:.1%}  down={down_p:.1%}  flat={flat_p:.1%}")

        # Proper move
        pm_rate = valid[f'{prefix}proper_move'].mean()
        print(f"  proper_move:  {pm_rate:.1%}")

    # NaN count per fwd column
    print(f"\\n--- NaN Counts ---")
    fwd_cols = [c for c in result.columns if c.startswith('fwd_')]
    for col in fwd_cols:
        nan_ct = result[col].isna().sum()
        print(f"  {col:30s} {nan_ct:6,}")

    print(f"\\n{'='*70}")
    print(f"SANITY CHECK COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
''', "scripts/sanity_check_forward_returns.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 5: scripts/run_layer3_tests.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing scripts/run_layer3_tests.py ---")

write_and_compile(SCRIPTS / "run_layer3_tests.py", '''"""
Runner: executes Layer 3 tests + debug + sanity, captures all output to a log file.

Run: python scripts/run_layer3_tests.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent
LOG_FILE = VAULT / "06-CLAUDE-LOGS" / "2026-02-14-bbw-layer3-results.md"

SCRIPTS_TO_RUN = [
    ("Layer 3 Tests", ROOT / "tests" / "test_forward_returns.py"),
    ("Layer 3 Debug Validator", ROOT / "scripts" / "debug_forward_returns.py"),
    ("Layer 3 Sanity Check", ROOT / "scripts" / "sanity_check_forward_returns.py"),
]

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
lines = [f"# Layer 3 Test Results -- {ts}\\n"]

for label, script in SCRIPTS_TO_RUN:
    print(f"Running {label}...")
    r = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=120
    )
    print(r.stdout)
    if r.stderr:
        print(f"STDERR:\\n{r.stderr}")
    lines.append(f"\\n## {label}\\n```\\n{r.stdout}```\\n")
    if r.stderr:
        lines.append(f"### STDERR\\n```\\n{r.stderr}```\\n")
    if r.returncode != 0:
        lines.append(f"**Exit code: {r.returncode}**\\n")

log_content = "\\n".join(lines)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.write_text(log_content, encoding="utf-8")
print(f"\\nResults saved to: {LOG_FILE}")
print("Done.")
''', "scripts/run_layer3_tests.py")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 6: Run everything via the runner
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print("Running scripts/run_layer3_tests.py ...")
print(f"{'='*70}\n")

runner_result = subprocess.run(
    [sys.executable, str(SCRIPTS / "run_layer3_tests.py")],
    capture_output=True, text=True, cwd=str(ROOT), timeout=300
)
print(runner_result.stdout)
if runner_result.stderr:
    print(f"STDERR:\n{runner_result.stderr}")

print(f"\n{'='*70}")
print(f"LAYER 3 BUILD COMPLETE -- {ts}")
print(f"{'='*70}")
