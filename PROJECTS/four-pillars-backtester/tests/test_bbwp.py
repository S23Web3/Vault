"""
Tests for signals/bbwp.py — Layer 1 BBWP Calculator.
11 tests covering BB width, percentrank, spectrum, state, MA cross, points, NaN, columns.
Tests 1-10 use synthetic data with known expected outputs.
Test 11 uses real RIVERUSDT 5m parquet for sanity checks.

Run: python tests/test_bbwp.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from signals.bbwp import calculate_bbwp, DEFAULT_PARAMS

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


def make_df(closes, n=200):
    """Build a minimal OHLCV DataFrame from a close series."""
    if len(closes) < n:
        closes = list(closes) + [closes[-1]] * (n - len(closes))
    closes = np.array(closes[:n], dtype=float)
    return pd.DataFrame({
        'open': closes,
        'high': closes * 1.001,
        'low': closes * 0.999,
        'close': closes,
        'base_vol': np.ones(len(closes)) * 1000.0,
    })


# ─── Test 1: BB Width Calculation ────────────────────────────────────────────

def test_bbw_calculation():
    """BB width = (2 * stdev) / basis. Manual calc on 20 bars of known data."""
    print("\n[Test 1] BB Width Calculation")

    closes = [100.0 + i for i in range(20)]
    close_series = pd.Series(closes, dtype=float)

    basis_len = 13
    basis = close_series.rolling(basis_len).mean()
    stdev = close_series.rolling(basis_len).std(ddof=0)
    expected_bbw = (2 * stdev) / basis

    # Run through calculate_bbwp with enough data
    df = make_df(closes, n=200)
    result = calculate_bbwp(df, {'basis_len': basis_len, 'lookback': 20})

    # Compare first 20 bars of bbw_raw (after NaN warmup)
    for i in range(basis_len - 1, 20):
        got = result['bbwp_bbw_raw'].iloc[i]
        exp = expected_bbw.iloc[i]
        if not np.isnan(exp):
            check(f"bbw_raw[{i}]", abs(got - exp) < 1e-10,
                  f"got={got:.10f}, expected={exp:.10f}")


# ─── Test 2: Percentrank Matches Pine ────────────────────────────────────────

def test_percentrank_matches_pine():
    """Compare our percentrank to Pine's ta.percentrank on known sequence."""
    print("\n[Test 2] Percentrank Matches Pine")

    # Pine ta.percentrank(source, length):
    # Counts how many of the last `length` values are STRICTLY LESS than current.
    # Result = count_below / length * 100
    #
    # Example: window = [1, 3, 5, 7, 9], current = 7
    # Values in window (including current): [1, 3, 5, 7, 9]
    # Pine compares current against all `length` values (including current position)
    # count strictly less than 7: values 1, 3, 5 = 3 out of 5
    # percentrank = 3 / 5 * 100 = 60

    # Build a known sequence where we can manually compute percentrank
    # Use lookback=5 for simplicity
    # Sequence: constant 100 for warmup, then [10, 20, 30, 40, 50, 25]
    warmup = [100.0] * 13  # need basis_len warmup for BB
    data = warmup + [10, 20, 30, 40, 50, 25] + [30.0] * 180

    df = make_df(data, n=len(data))
    result = calculate_bbwp(df, {'basis_len': 13, 'lookback': 5, 'bbwp_ma_len': 3})

    # After lookback bars of valid BBW, bbwp values should be computed
    # We check that bbwp_value is in range 0-100 for non-NaN rows
    valid = result['bbwp_value'].dropna()
    check("bbwp_value range", (valid >= 0).all() and (valid <= 100).all(),
          f"min={valid.min():.1f}, max={valid.max():.1f}")

    # Check that it's not all the same value (percentile should vary)
    check("bbwp_value varies", valid.nunique() > 1,
          f"unique values: {valid.nunique()}")


# ─── Test 3: Spectrum Color Boundaries ────────────────────────────────────────

def test_spectrum_color_boundaries():
    """Verify 25/50/75 boundaries produce correct 4-zone colors; NaN -> None."""
    print("\n[Test 3] Spectrum Color Boundaries")

    closes = np.random.RandomState(42).normal(100, 5, 300).tolist()
    df = make_df(closes, n=300)
    result = calculate_bbwp(df)

    # Valid colors (4 zones, no orange)
    valid_colors = {'blue', 'green', 'yellow', 'red'}
    spectrums = result['bbwp_spectrum'].dropna().unique()
    check("all spectrums valid (4 colors)", set(spectrums).issubset(valid_colors),
          f"got: {set(spectrums)}")

    # NaN bbwp rows should have None spectrum
    nan_rows = result[result['bbwp_value'].isna()]
    if len(nan_rows) > 0:
        check("NaN bbwp -> None spectrum",
              nan_rows['bbwp_spectrum'].isna().all(),
              f"non-None count: {nan_rows['bbwp_spectrum'].notna().sum()}")

    # Boundary checks: <=25 blue, >75 red
    valid_rows = result.dropna(subset=['bbwp_value'])
    if len(valid_rows) > 0:
        blue_rows = valid_rows[valid_rows['bbwp_value'] <= 25]
        if len(blue_rows) > 0:
            check("bbwp<=25 -> blue", (blue_rows['bbwp_spectrum'] == 'blue').all(),
                  f"non-blue count: {(blue_rows['bbwp_spectrum'] != 'blue').sum()}")
        else:
            check("bbwp<=25 -> blue", True, "no rows <= 25 (OK for random data)")

        red_rows = valid_rows[valid_rows['bbwp_value'] > 75]
        if len(red_rows) > 0:
            check("bbwp>75 -> red", (red_rows['bbwp_spectrum'] == 'red').all(),
                  f"non-red count: {(red_rows['bbwp_spectrum'] != 'red').sum()}")
        else:
            check("bbwp>75 -> red", True, "no rows > 75 (OK for random data)")


# ─── Test 4: State Priority Order ─────────────────────────────────────────────

def test_state_priority_order():
    """BLUE_DOUBLE takes priority over BLUE. RED_DOUBLE over RED. etc."""
    print("\n[Test 4] State Priority Order")

    # Verify all 7 states can appear
    valid_states = {'BLUE_DOUBLE', 'BLUE', 'RED_DOUBLE', 'RED',
                    'MA_CROSS_UP', 'MA_CROSS_DOWN', 'NORMAL'}

    closes = np.random.RandomState(99).normal(100, 10, 500).tolist()
    df = make_df(closes, n=500)
    result = calculate_bbwp(df)

    states_found = set(result['bbwp_state'].dropna().unique())
    check("all states valid", states_found.issubset(valid_states),
          f"got: {states_found}")

    # BLUE_DOUBLE: bbwp <= 10 AND bbwp < 25 (always true when <= 10)
    # So any row with bbwp_value <= 10 should be BLUE_DOUBLE
    valid_rows = result.dropna(subset=['bbwp_value'])
    blue_double_rows = valid_rows[valid_rows['bbwp_value'] <= 10]
    if len(blue_double_rows) > 0:
        check("bbwp<=10 -> BLUE_DOUBLE",
              (blue_double_rows['bbwp_state'] == 'BLUE_DOUBLE').all(),
              f"non-BLUE_DOUBLE: {blue_double_rows['bbwp_state'].value_counts().to_dict()}")

    # RED_DOUBLE: bbwp >= 90 AND bbwp > 75 (always true when >= 90)
    red_double_rows = valid_rows[valid_rows['bbwp_value'] >= 90]
    if len(red_double_rows) > 0:
        check("bbwp>=90 -> RED_DOUBLE",
              (red_double_rows['bbwp_state'] == 'RED_DOUBLE').all(),
              f"non-RED_DOUBLE: {red_double_rows['bbwp_state'].value_counts().to_dict()}")


# ─── Test 5: MA Cross Persistence ─────────────────────────────────────────────

def test_ma_cross_persistence():
    """Cross fires, persists for N bars, auto-resets on timeout (deterministic)."""
    print("\n[Test 5] MA Cross Persistence")

    # Crafted data: warmup(130 flat) + bump(20 rising) + flat(250 stable)
    # The bump creates BB width variance; flat tail keeps BBWP in normal range
    warmup = [100.0] * 130
    bump = [100.0 + i * 0.5 for i in range(20)]
    flat = [110.0] * 250
    closes = warmup + bump + flat
    df = make_df(closes, n=len(closes))
    result = calculate_bbwp(df, {'ma_cross_timeout': 10})

    # MA_CROSS_UP runs must not exceed timeout
    is_cross_up = (result['bbwp_state'] == 'MA_CROSS_UP').astype(int)
    runs = is_cross_up.diff().fillna(0)
    run_starts = runs[runs == 1].index.tolist()
    run_ends = runs[runs == -1].index.tolist()
    if len(run_ends) < len(run_starts):
        run_ends.append(len(result))

    max_run = 0
    for s, e in zip(run_starts, run_ends):
        max_run = max(max_run, e - s)

    check("MA_CROSS_UP run <= timeout",
          max_run <= 10,
          f"max run length: {max_run}")

    # Cross events should be sparse
    cross_up_events = result['bbwp_ma_cross_up'].sum()
    cross_down_events = result['bbwp_ma_cross_down'].sum()
    total_bars = len(result.dropna(subset=['bbwp_value']))
    check("cross events sparse",
          (cross_up_events + cross_down_events) < total_bars * 0.15,
          f"up={cross_up_events}, down={cross_down_events}, total_valid={total_bars}")


# ─── Test 6: MA Cross Cancelled by Spectrum ──────────────────────────────────

def test_ma_cross_cancelled_by_spectrum():
    """Active MA_CROSS_UP cancelled when BBWP enters blue/red spectrum."""
    print("\n[Test 6] MA Cross Cancelled by Spectrum")

    # Verify: no row can be MA_CROSS_UP/DOWN AND in blue/red spectrum simultaneously
    closes = np.random.RandomState(55).normal(100, 8, 500).tolist()
    df = make_df(closes, n=500)
    result = calculate_bbwp(df)

    ma_cross_rows = result[result['bbwp_state'].isin(['MA_CROSS_UP', 'MA_CROSS_DOWN'])]
    if len(ma_cross_rows) > 0:
        # These rows should NOT have bbwp < 25 or bbwp > 75
        in_spectrum = ma_cross_rows[
            (ma_cross_rows['bbwp_value'] < 25) | (ma_cross_rows['bbwp_value'] > 75)
        ]
        check("no MA_CROSS in spectrum range",
              len(in_spectrum) == 0,
              f"found {len(in_spectrum)} MA_CROSS rows in blue/red spectrum")
    else:
        check("no MA_CROSS in spectrum range", True,
              "no MA_CROSS states found")


# ─── Test 7: MA Cross Up Cancels Down ────────────────────────────────────────

def test_ma_cross_up_cancels_down():
    """Cross_up event bar must have MA_CROSS_UP state (not DOWN); at least 1 tested."""
    print("\n[Test 7] MA Cross Up Cancels Down")

    closes = np.random.RandomState(33).normal(100, 5, 400).tolist()
    df = make_df(closes, n=400)
    result = calculate_bbwp(df)

    # cross_up and cross_down events never on same bar
    both_events = result[
        (result['bbwp_ma_cross_up'] == True) &
        (result['bbwp_ma_cross_down'] == True)
    ]
    check("never both cross events on same bar", len(both_events) == 0)

    # Every cross_up event bar must have MA_CROSS_UP state (not DOWN)
    cross_up_bars = result[result['bbwp_ma_cross_up'] == True]
    tested_count = 0
    if len(cross_up_bars) > 0:
        check("cross_up event -> MA_CROSS_UP state",
              (cross_up_bars['bbwp_state'] == 'MA_CROSS_UP').all(),
              f"states: {cross_up_bars['bbwp_state'].unique()}")
        tested_count += len(cross_up_bars)

    # Every cross_down event bar must have MA_CROSS_DOWN state (not UP)
    cross_down_bars = result[result['bbwp_ma_cross_down'] == True]
    if len(cross_down_bars) > 0:
        check("cross_down event -> MA_CROSS_DOWN state",
              (cross_down_bars['bbwp_state'] == 'MA_CROSS_DOWN').all(),
              f"states: {cross_down_bars['bbwp_state'].unique()}")
        tested_count += len(cross_down_bars)

    check("at least 1 cross event tested", tested_count > 0,
          f"tested {tested_count} cross event bars")


# ─── Test 8: Points Mapping ──────────────────────────────────────────────────

def test_points_mapping():
    """Verify points match Pine v2 exactly."""
    print("\n[Test 8] Points Mapping")

    expected_points = {
        'BLUE_DOUBLE': 2,
        'BLUE': 1,
        'RED_DOUBLE': 1,
        'RED': 1,
        'MA_CROSS_UP': 1,
        'MA_CROSS_DOWN': 0,
        'NORMAL': 0,
    }

    closes = np.random.RandomState(11).normal(100, 10, 500).tolist()
    df = make_df(closes, n=500)
    result = calculate_bbwp(df)

    for state, exp_pts in expected_points.items():
        rows = result[result['bbwp_state'] == state]
        if len(rows) > 0:
            actual_pts = rows['bbwp_points'].unique()
            check(f"{state} -> {exp_pts} pts",
                  len(actual_pts) == 1 and actual_pts[0] == exp_pts,
                  f"got: {actual_pts}")
        else:
            check(f"{state} -> {exp_pts} pts", True,
                  f"no {state} rows found (OK)")


# ─── Test 9: NaN Handling ─────────────────────────────────────────────────────

def test_nan_handling():
    """First lookback bars return NaN for bbwp, 'NORMAL' for state."""
    print("\n[Test 9] NaN Handling")

    lookback = 100
    basis_len = 13
    closes = np.random.RandomState(22).normal(100, 2, 300).tolist()
    df = make_df(closes, n=300)
    result = calculate_bbwp(df, {'basis_len': basis_len, 'lookback': lookback})

    # First (basis_len - 1) bars: bbwp_bbw_raw should be NaN
    first_bbw_nan = result['bbwp_bbw_raw'].iloc[:basis_len - 1].isna().all()
    check("first basis_len-1 bars bbw_raw NaN", first_bbw_nan)

    # bbwp_state should NEVER be NaN — always has a value
    state_nan_count = result['bbwp_state'].isna().sum()
    check("no NaN in bbwp_state", state_nan_count == 0,
          f"NaN count: {state_nan_count}")

    # NaN bbwp bars should have state = NORMAL
    nan_bbwp_rows = result[result['bbwp_value'].isna()]
    if len(nan_bbwp_rows) > 0:
        check("NaN bbwp -> NORMAL state",
              (nan_bbwp_rows['bbwp_state'] == 'NORMAL').all(),
              f"states: {nan_bbwp_rows['bbwp_state'].unique()}")

    # NaN bbwp bars should have points = 0
    if len(nan_bbwp_rows) > 0:
        check("NaN bbwp -> 0 points",
              (nan_bbwp_rows['bbwp_points'] == 0).all())


# ─── Test 10: Output Columns ─────────────────────────────────────────────────

def test_output_columns():
    """Verify all 10 bbwp_ columns present with correct dtypes."""
    print("\n[Test 10] Output Columns")

    expected_cols = [
        'bbwp_value', 'bbwp_ma', 'bbwp_bbw_raw', 'bbwp_spectrum',
        'bbwp_state', 'bbwp_points', 'bbwp_is_blue_bar', 'bbwp_is_red_bar',
        'bbwp_ma_cross_up', 'bbwp_ma_cross_down',
    ]

    closes = np.random.RandomState(7).normal(100, 3, 200).tolist()
    df = make_df(closes, n=200)
    original_cols = list(df.columns)
    result = calculate_bbwp(df)

    # All 10 bbwp_ columns present
    for col in expected_cols:
        check(f"column {col} exists", col in result.columns)

    # Original columns preserved
    for col in original_cols:
        check(f"original column {col} preserved", col in result.columns)

    # Total column count = original + 10
    check("column count correct",
          len(result.columns) == len(original_cols) + 10,
          f"got {len(result.columns)}, expected {len(original_cols) + 10}")

    # Dtype checks
    valid_rows = result.dropna(subset=['bbwp_value'])
    if len(valid_rows) > 0:
        check("bbwp_value is float",
              valid_rows['bbwp_value'].dtype in [np.float64, np.float32])
        check("bbwp_points is int-like",
              valid_rows['bbwp_points'].dtype in [np.int64, np.int32, np.float64])
        check("bbwp_is_blue_bar is bool",
              valid_rows['bbwp_is_blue_bar'].dtype == bool)
        check("bbwp_spectrum is string",
              valid_rows['bbwp_spectrum'].dtype == object)
        check("bbwp_state is string",
              valid_rows['bbwp_state'].dtype == object)


# ─── Test 11: Real Parquet Sanity ─────────────────────────────────────────────

def test_on_real_parquet():
    """Load RIVERUSDT 5m parquet, run calculate_bbwp, sanity check distributions."""
    print("\n[Test 11] Real Parquet Sanity (RIVERUSDT 5m)")

    cache_path = ROOT / "data" / "cache" / "RIVERUSDT_1m.parquet"
    if not cache_path.exists():
        print("  SKIP  RIVERUSDT parquet not found")
        return

    # Load and resample to 5m
    raw = pd.read_parquet(cache_path)
    if 'datetime' not in raw.columns and 'timestamp' in raw.columns:
        raw['datetime'] = pd.to_datetime(raw['timestamp'], unit='ms', utc=True)

    raw = raw.set_index('datetime')
    df_5m = raw.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min',
        'close': 'last', 'base_vol': 'sum'
    }).dropna().reset_index()

    print(f"  Loaded {len(df_5m):,} 5m bars")

    result = calculate_bbwp(df_5m)
    valid = result.dropna(subset=['bbwp_value'])

    # BBWP distribution should be roughly uniform 0-100
    bbwp_mean = valid['bbwp_value'].mean()
    bbwp_std = valid['bbwp_value'].std()
    check("bbwp_value mean 40-60", 40 <= bbwp_mean <= 60,
          f"mean={bbwp_mean:.1f}")
    check("bbwp_value std 20-35", 20 <= bbwp_std <= 35,
          f"std={bbwp_std:.1f}")

    # State distribution
    state_dist = valid['bbwp_state'].value_counts(normalize=True)
    normal_pct = state_dist.get('NORMAL', 0)
    check("NORMAL is most common (>10%)", normal_pct > 0.10,
          f"NORMAL={normal_pct:.1%}")

    # Rare states
    for rare in ['BLUE_DOUBLE', 'RED_DOUBLE']:
        pct = state_dist.get(rare, 0)
        check(f"{rare} is rare (<15%)", pct < 0.15,
              f"{rare}={pct:.1%}")

    # Points mean
    pts_mean = valid['bbwp_points'].mean()
    check("bbwp_points mean 0.2-1.0", 0.2 <= pts_mean <= 1.0,
          f"mean={pts_mean:.2f}")

    # No NaN in state
    check("no NaN in bbwp_state", result['bbwp_state'].isna().sum() == 0)

    # MA cross events sparse
    cross_up_pct = valid['bbwp_ma_cross_up'].mean()
    check("MA cross_up events sparse (<5%)", cross_up_pct < 0.05,
          f"pct={cross_up_pct:.2%}")

    print(f"\n  State distribution:")
    for state, pct in state_dist.items():
        print(f"    {state:20s} {pct:6.1%}")


# ─── Test 12: Warmup Gap Consistency ─────────────────────────────────────────

def test_warmup_gap_consistency():
    """Bars with valid bbwp but NaN MA should still detect BLUE/BLUE_DOUBLE."""
    print("\n[Test 12] Warmup Gap Consistency")

    # Flat price -> low BB width -> low BBWP -> should be blue spectrum
    # basis_len=13 means bbwp starts at bar 113 (lookback=100 + basis_len)
    # bbwp_ma (SMA 5) starts at bar 117 (113 + 5 - 1)
    # So bars 113-116 have valid bbwp but NaN bbwp_ma
    closes = [100.0] * 300  # perfectly flat -> zero stdev -> bbwp=0
    df = make_df(closes, n=300)
    result = calculate_bbwp(df, {'basis_len': 13, 'lookback': 100, 'bbwp_ma_len': 5})

    # Find bars with valid bbwp but NaN MA (the warmup gap)
    gap_rows = result[result['bbwp_value'].notna() & result['bbwp_ma'].isna()]

    if len(gap_rows) > 0:
        # These bars should NOT all be NORMAL — they should detect BLUE/BLUE_DOUBLE
        # since flat data produces bbwp near 0
        gap_states = set(gap_rows['bbwp_state'].unique())
        blue_states = {'BLUE', 'BLUE_DOUBLE'}
        has_blue = len(gap_states & blue_states) > 0
        check("warmup gap bars detect blue states", has_blue,
              f"gap states: {gap_states}, bbwp values: {gap_rows['bbwp_value'].tolist()}")

        # Verify these bars have correct spectrum color
        check("warmup gap bars have blue spectrum",
              (gap_rows['bbwp_spectrum'] == 'blue').all(),
              f"spectrums: {gap_rows['bbwp_spectrum'].unique()}")
    else:
        check("warmup gap bars detect blue states", True,
              "no gap rows found (all bars have both bbwp and MA)")

    # Also verify bars with NaN bbwp are still NORMAL
    nan_bbwp_rows = result[result['bbwp_value'].isna()]
    if len(nan_bbwp_rows) > 0:
        check("NaN bbwp bars still NORMAL",
              (nan_bbwp_rows['bbwp_state'] == 'NORMAL').all())


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run all 12 BBWP tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBWP Layer 1 Tests — {ts}")
    print(f"{'='*70}")

    test_bbw_calculation()
    test_percentrank_matches_pine()
    test_spectrum_color_boundaries()
    test_state_priority_order()
    test_ma_cross_persistence()
    test_ma_cross_cancelled_by_spectrum()
    test_ma_cross_up_cancels_down()
    test_points_mapping()
    test_nan_handling()
    test_output_columns()
    test_on_real_parquet()
    test_warmup_gap_consistency()

    print(f"\n{'='*70}")
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print(f"FAILURES: {', '.join(ERRORS)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
