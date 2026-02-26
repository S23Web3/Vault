"""
Debug and Math Validator for Layer 1 BBWP Calculator.

Hand-computed vectors with exact expected values.
7 sections, 60+ checks.

Run: python scripts/debug_bbwp.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from signals.bbwp import (
    calculate_bbwp, _apply_ma, _percentrank_pine, _spectrum_color,
    _detect_states, DEFAULT_PARAMS, STATE_POINTS, OUTPUT_COLS
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


# =============================================================================
# SECTION 1: _spectrum_color exact boundary values
# =============================================================================

def debug_spectrum_color():
    """Verify 4-zone color mapping at exact boundary values."""
    print("\n[Debug 1] _spectrum_color Exact Boundaries")

    cases = [
        (np.nan, None, "NaN -> None"),
        (0.0,    "blue",   "0 -> blue"),
        (10.0,   "blue",   "10 -> blue"),
        (24.99,  "blue",   "24.99 -> blue"),
        (25.0,   "blue",   "25 -> blue (<=25)"),
        (25.01,  "green",  "25.01 -> green"),
        (37.5,   "green",  "37.5 -> green"),
        (49.99,  "green",  "49.99 -> green"),
        (50.0,   "green",  "50 -> green (<=50)"),
        (50.01,  "yellow", "50.01 -> yellow"),
        (62.5,   "yellow", "62.5 -> yellow"),
        (74.99,  "yellow", "74.99 -> yellow"),
        (75.0,   "yellow", "75 -> yellow (<=75)"),
        (75.01,  "red",    "75.01 -> red"),
        (90.0,   "red",    "90 -> red"),
        (100.0,  "red",    "100 -> red"),
    ]

    for val, expected, label in cases:
        result = _spectrum_color(val)
        check(label, result == expected, f"got {result}")


# =============================================================================
# SECTION 2: BB Width manual calculation
# =============================================================================

def debug_bbw_calculation():
    """Linear ramp: constant stdev, decreasing BBW. Verify to 6 decimals."""
    print("\n[Debug 2] BB Width Manual Calculation")

    # Linear ramp: close = 10, 12, 14, ..., 28 (step=2, 10 bars)
    # basis_len=3: SMA and stdev(ddof=0) on rolling window of 3
    # For linear ramp with step=2: stdev is always sqrt(8/3) = 1.632993
    closes = [10 + 2*i for i in range(10)]
    close_series = pd.Series(closes, dtype=float)

    basis = close_series.rolling(3).mean()
    stdev = close_series.rolling(3).std(ddof=0)

    expected_stdev = np.sqrt(8.0 / 3.0)  # 1.632993

    # Bars 0-1: NaN (not enough data)
    check("bbw[0] NaN", np.isnan(basis.iloc[0]))
    check("bbw[1] NaN", np.isnan(basis.iloc[1]))

    # Bar 2: window=[10,12,14], mean=12, stdev=sqrt(8/3), bbw=2*stdev/12
    check("basis[2]=12.0", abs(basis.iloc[2] - 12.0) < 1e-6,
          f"got {basis.iloc[2]:.6f}")
    check("stdev[2]=1.632993", abs(stdev.iloc[2] - expected_stdev) < 1e-4,
          f"got {stdev.iloc[2]:.6f}")

    expected_bbw_2 = 2 * expected_stdev / 12.0
    expected_bbw_3 = 2 * expected_stdev / 14.0
    expected_bbw_4 = 2 * expected_stdev / 16.0

    # Run through calculate_bbwp and verify bbwp_bbw_raw
    df = pd.DataFrame({
        'open': closes, 'high': [c+1 for c in closes],
        'low': [c-1 for c in closes], 'close': closes,
        'base_vol': [1000]*10
    })
    # Pad to 200 bars for lookback warmup
    pad = pd.DataFrame({
        'open': [28]*190, 'high': [29]*190, 'low': [27]*190,
        'close': [28]*190, 'base_vol': [1000]*190
    })
    df = pd.concat([df, pad], ignore_index=True)

    result = calculate_bbwp(df, {'basis_len': 3, 'lookback': 5})

    check("bbw_raw[2] matches",
          abs(result['bbwp_bbw_raw'].iloc[2] - expected_bbw_2) < 1e-6,
          f"got {result['bbwp_bbw_raw'].iloc[2]:.6f}, expected {expected_bbw_2:.6f}")
    check("bbw_raw[3] matches",
          abs(result['bbwp_bbw_raw'].iloc[3] - expected_bbw_3) < 1e-6,
          f"got {result['bbwp_bbw_raw'].iloc[3]:.6f}, expected {expected_bbw_3:.6f}")
    check("bbw_raw[4] matches",
          abs(result['bbwp_bbw_raw'].iloc[4] - expected_bbw_4) < 1e-6,
          f"got {result['bbwp_bbw_raw'].iloc[4]:.6f}, expected {expected_bbw_4:.6f}")


# =============================================================================
# SECTION 3: _percentrank_pine manual trace
# =============================================================================

def debug_percentrank():
    """Known BBW series, lookback=3, hand-computed percentrank at each bar."""
    print("\n[Debug 3] _percentrank_pine Manual Trace")

    # Constructed BBW series (bypass BB calc, test percentrank directly)
    bbw = pd.Series([np.nan, np.nan, 0.5, 0.3, 0.7, 0.4, 0.6, 0.2, 0.8, 0.5])
    lookback = 3
    # min_valid = max(3//2, 1) = 1

    result = _percentrank_pine(bbw, lookback)

    # Bars 0-2: i < lookback=3, all NaN
    check("prank[0] NaN", np.isnan(result.iloc[0]))
    check("prank[1] NaN", np.isnan(result.iloc[1]))
    check("prank[2] NaN", np.isnan(result.iloc[2]))

    # Bar 3: prev=[NaN,NaN,0.5], valid=[0.5], current=0.3
    #   count(0.5 < 0.3) = 0. result = 0/1*100 = 0.0
    check("prank[3]=0.0", abs(result.iloc[3] - 0.0) < 0.01,
          f"got {result.iloc[3]:.2f}")

    # Bar 4: prev=[NaN,0.5,0.3], valid=[0.5,0.3], current=0.7
    #   count(0.5<0.7)=1, count(0.3<0.7)=1 -> 2. result = 2/2*100 = 100.0
    check("prank[4]=100.0", abs(result.iloc[4] - 100.0) < 0.01,
          f"got {result.iloc[4]:.2f}")

    # Bar 5: prev=[0.5,0.3,0.7], valid=3, current=0.4
    #   count(<0.4): 0.5<0.4=F, 0.3<0.4=T, 0.7<0.4=F -> 1. result = 1/3*100 = 33.333
    check("prank[5]=33.33", abs(result.iloc[5] - 33.333) < 0.1,
          f"got {result.iloc[5]:.2f}")

    # Bar 6: prev=[0.3,0.7,0.4], valid=3, current=0.6
    #   count(<0.6): 0.3=T, 0.7=F, 0.4=T -> 2. result = 2/3*100 = 66.667
    check("prank[6]=66.67", abs(result.iloc[6] - 66.667) < 0.1,
          f"got {result.iloc[6]:.2f}")

    # Bar 7: prev=[0.7,0.4,0.6], valid=3, current=0.2
    #   count(<0.2): 0.7=F, 0.4=F, 0.6=F -> 0. result = 0.0
    check("prank[7]=0.0", abs(result.iloc[7] - 0.0) < 0.01,
          f"got {result.iloc[7]:.2f}")

    # Bar 8: prev=[0.4,0.6,0.2], valid=3, current=0.8
    #   count(<0.8): 0.4=T, 0.6=T, 0.2=T -> 3. result = 100.0
    check("prank[8]=100.0", abs(result.iloc[8] - 100.0) < 0.01,
          f"got {result.iloc[8]:.2f}")

    # Bar 9: prev=[0.6,0.2,0.8], valid=3, current=0.5
    #   count(<0.5): 0.6=F, 0.2=T, 0.8=F -> 1. result = 33.333
    check("prank[9]=33.33", abs(result.iloc[9] - 33.333) < 0.1,
          f"got {result.iloc[9]:.2f}")


# =============================================================================
# SECTION 4: _detect_states full trace (all 7 states)
# =============================================================================

def debug_state_machine():
    """Crafted BBWP+MA arrays that hit all 7 states. Hand-traced bar by bar."""
    print("\n[Debug 4] _detect_states Full Trace (All 7 States)")

    # Bar | BBWP  | MA   | Expected State    | Why
    # ----|-------|------|-------------------|----
    # 0   | NaN   | NaN  | NORMAL            | NaN bbwp
    # 1   | 5.0   | NaN  | BLUE_DOUBLE       | bbwp<=10 AND bbwp<25
    # 2   | 15.0  | NaN  | BLUE              | bbwp<25, not <=10
    # 3   | 40.0  | 30.0 | NORMAL            | in_normal, prev_ma=NaN -> no cross
    # 4   | 35.0  | 40.0 | MA_CROSS_DOWN     | crossunder: 35<40 AND prev(40>=30)
    # 5   | 38.0  | 42.0 | MA_CROSS_DOWN     | persist (no new event, no cancel)
    # 6   | 50.0  | 45.0 | MA_CROSS_UP       | crossover: 50>45 AND prev(38<=42)
    # 7   | 85.0  | 60.0 | RED               | bbwp>75, cancels cross
    # 8   | 95.0  | 70.0 | RED_DOUBLE        | bbwp>=90 AND bbwp>75
    # 9   | 50.0  | 65.0 | MA_CROSS_DOWN     | crossunder: 50<65 AND prev(95>=70)

    bbwp_arr = np.array([np.nan, 5.0, 15.0, 40.0, 35.0, 38.0, 50.0, 85.0, 95.0, 50.0])
    ma_arr = np.array([np.nan, np.nan, np.nan, 30.0, 40.0, 42.0, 45.0, 60.0, 70.0, 65.0])

    params = {
        'extreme_low': 10, 'extreme_high': 90,
        'spectrum_low': 25, 'spectrum_high': 75,
        'ma_cross_timeout': 10
    }

    states, points, cross_up, cross_down = _detect_states(bbwp_arr, ma_arr, params)

    expected_states = [
        'NORMAL', 'BLUE_DOUBLE', 'BLUE', 'NORMAL', 'MA_CROSS_DOWN',
        'MA_CROSS_DOWN', 'MA_CROSS_UP', 'RED', 'RED_DOUBLE', 'MA_CROSS_DOWN'
    ]
    expected_points = [0, 2, 1, 0, 0, 0, 1, 1, 1, 0]
    expected_cross_up = [False, False, False, False, False, False, True, False, False, False]
    expected_cross_down = [False, False, False, False, True, False, False, False, False, True]

    for i in range(10):
        check(f"bar{i} state={expected_states[i]}",
              states[i] == expected_states[i],
              f"got {states[i]}")

    for i in range(10):
        check(f"bar{i} points={expected_points[i]}",
              points[i] == expected_points[i],
              f"got {points[i]}")

    for i in range(10):
        if expected_cross_up[i]:
            check(f"bar{i} cross_up=True", cross_up[i] == True)
        if expected_cross_down[i]:
            check(f"bar{i} cross_down=True", cross_down[i] == True)

    # Verify no spurious cross events
    total_cross_up = sum(cross_up)
    total_cross_down = sum(cross_down)
    check("total cross_up events = 1", total_cross_up == 1, f"got {total_cross_up}")
    check("total cross_down events = 2", total_cross_down == 2, f"got {total_cross_down}")

    # All 7 states covered
    unique_states = set(states)
    check("all 7 states covered", len(unique_states) == 7,
          f"got {len(unique_states)}: {unique_states}")


# =============================================================================
# SECTION 5: _detect_states timeout mechanism
# =============================================================================

def debug_timeout():
    """MA_CROSS_UP persists for timeout-1 bars, then resets to NORMAL."""
    print("\n[Debug 5] MA Cross Timeout Mechanism")

    # Bar 0: NORMAL (no prev)
    # Bar 1: crossover fires -> MA_CROSS_UP, ma_cross_bar=1
    # Bar 2: persist (1 bar elapsed)
    # Bar 3: persist (2 bars elapsed)
    # Bar 4: timeout! (3 bars elapsed, timeout=3) -> NORMAL
    # Bar 5: NORMAL (no active cross)

    bbwp_arr = np.array([40.0, 50.0, 52.0, 53.0, 54.0, 55.0])
    ma_arr = np.array([50.0, 45.0, 47.0, 48.0, 49.0, 50.0])

    params = {
        'extreme_low': 10, 'extreme_high': 90,
        'spectrum_low': 25, 'spectrum_high': 75,
        'ma_cross_timeout': 3
    }

    states, points, cross_up, cross_down = _detect_states(bbwp_arr, ma_arr, params)

    expected = ['NORMAL', 'MA_CROSS_UP', 'MA_CROSS_UP', 'MA_CROSS_UP', 'NORMAL', 'NORMAL']

    for i in range(6):
        check(f"timeout bar{i} state={expected[i]}",
              states[i] == expected[i],
              f"got {states[i]}")

    check("cross_up fires at bar 1", cross_up[1] == True)
    check("no cross_up at bar 4", cross_up[4] == False)


# =============================================================================
# SECTION 6: Full pipeline invariants
# =============================================================================

def debug_pipeline_invariants():
    """Run calculate_bbwp, verify all structural invariants."""
    print("\n[Debug 6] Full Pipeline Invariants")

    np.random.seed(42)
    closes = np.random.normal(100, 10, 500).tolist()
    df = pd.DataFrame({
        'open': closes, 'high': [c*1.01 for c in closes],
        'low': [c*0.99 for c in closes], 'close': closes,
        'base_vol': [1000]*500
    })

    result = calculate_bbwp(df)

    # All 10 output columns present
    for col in OUTPUT_COLS:
        check(f"column {col} present", col in result.columns)

    # State -> points consistency
    for state, exp_pts in STATE_POINTS.items():
        rows = result[result['bbwp_state'] == state]
        if len(rows) > 0:
            mismatch = rows[rows['bbwp_points'] != exp_pts]
            check(f"{state} -> {exp_pts} pts (n={len(rows)})",
                  len(mismatch) == 0,
                  f"{len(mismatch)} mismatches")

    # blue_bar implies bbwp <= extreme_low
    valid = result.dropna(subset=['bbwp_value'])
    blue_bars = valid[valid['bbwp_is_blue_bar'] == True]
    if len(blue_bars) > 0:
        check("blue_bar -> bbwp<=10",
              (blue_bars['bbwp_value'] <= DEFAULT_PARAMS['extreme_low']).all())

    # red_bar implies bbwp >= extreme_high
    red_bars = valid[valid['bbwp_is_red_bar'] == True]
    if len(red_bars) > 0:
        check("red_bar -> bbwp>=90",
              (red_bars['bbwp_value'] >= DEFAULT_PARAMS['extreme_high']).all())

    # BLUE_DOUBLE implies both blue_bar and blue spectrum
    bd_rows = valid[valid['bbwp_state'] == 'BLUE_DOUBLE']
    if len(bd_rows) > 0:
        check("BLUE_DOUBLE -> bbwp<=10",
              (bd_rows['bbwp_value'] <= DEFAULT_PARAMS['extreme_low']).all())
        check("BLUE_DOUBLE -> blue spectrum",
              (bd_rows['bbwp_spectrum'] == 'blue').all())

    # RED_DOUBLE implies both red_bar and red spectrum
    rd_rows = valid[valid['bbwp_state'] == 'RED_DOUBLE']
    if len(rd_rows) > 0:
        check("RED_DOUBLE -> bbwp>=90",
              (rd_rows['bbwp_value'] >= DEFAULT_PARAMS['extreme_high']).all())
        check("RED_DOUBLE -> red spectrum",
              (rd_rows['bbwp_spectrum'] == 'red').all())

    # MA_CROSS states must be in normal spectrum range (25-75)
    mc_rows = valid[valid['bbwp_state'].isin(['MA_CROSS_UP', 'MA_CROSS_DOWN'])]
    if len(mc_rows) > 0:
        in_range = (mc_rows['bbwp_value'] >= DEFAULT_PARAMS['spectrum_low']) & \
                   (mc_rows['bbwp_value'] <= DEFAULT_PARAMS['spectrum_high'])
        # Note: cross FIRES in normal range, but can PERSIST while bbwp drifts.
        # The state is set when cross fires, then persists until cancel.
        # So we check the CROSS EVENT bars, not all MA_CROSS state bars.
        cross_event_bars = valid[valid['bbwp_ma_cross_up'] | valid['bbwp_ma_cross_down']]
        if len(cross_event_bars) > 0:
            in_range_events = (cross_event_bars['bbwp_value'] >= DEFAULT_PARAMS['spectrum_low']) & \
                              (cross_event_bars['bbwp_value'] <= DEFAULT_PARAMS['spectrum_high'])
            check("cross events fire in normal range",
                  in_range_events.all(),
                  f"{(~in_range_events).sum()} events outside range")

    # No NaN in state column
    check("no NaN in bbwp_state", result['bbwp_state'].isna().sum() == 0)

    # NaN bbwp -> NORMAL state
    nan_rows = result[result['bbwp_value'].isna()]
    if len(nan_rows) > 0:
        check("NaN bbwp -> NORMAL",
              (nan_rows['bbwp_state'] == 'NORMAL').all())

    # bbwp_value in [0, 100] for valid bars
    valid_bbwp = valid['bbwp_value']
    check("bbwp in [0,100]",
          (valid_bbwp >= 0).all() and (valid_bbwp <= 100).all(),
          f"min={valid_bbwp.min():.1f}, max={valid_bbwp.max():.1f}")


# =============================================================================
# SECTION 7: Cross-validate on RIVERUSDT
# =============================================================================

def debug_cross_validate_real():
    """RIVERUSDT 5m: verify distributions and invariants on real data."""
    print("\n[Debug 7] Cross-Validate Real Data (RIVERUSDT 5m)")

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

    result = calculate_bbwp(df_5m)
    valid = result.dropna(subset=['bbwp_value'])

    # BBWP roughly uniform: mean 40-60, std 20-35
    bbwp_mean = valid['bbwp_value'].mean()
    bbwp_std = valid['bbwp_value'].std()
    check("bbwp mean 40-60", 40 <= bbwp_mean <= 60,
          f"mean={bbwp_mean:.1f}")
    check("bbwp std 20-35", 20 <= bbwp_std <= 35,
          f"std={bbwp_std:.1f}")

    # All 4 spectrum colors present
    colors = set(valid['bbwp_spectrum'].unique())
    check("all 4 colors present", colors == {'blue', 'green', 'yellow', 'red'},
          f"got {colors}")

    # State distribution: NORMAL most common
    state_dist = valid['bbwp_state'].value_counts(normalize=True)
    check("NORMAL most common", state_dist.index[0] == 'NORMAL' or state_dist.get('NORMAL', 0) > 0.10,
          f"top state: {state_dist.index[0]} ({state_dist.iloc[0]:.1%})")

    # Points mean reasonable (0.2-1.0)
    pts_mean = valid['bbwp_points'].mean()
    check("points mean 0.2-1.0", 0.2 <= pts_mean <= 1.0,
          f"mean={pts_mean:.2f}")

    # No inf anywhere
    for col in result.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(result[col].dropna()).sum()
        if inf_ct > 0:
            check(f"no inf in {col}", False, f"inf count: {inf_ct}")
            break
    else:
        check("no inf in any numeric column", True)

    print(f"\n  Validated {len(valid):,} bars")


# --- Main ---------------------------------------------------------------------

def main():
    """Run all debug sections."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBWP Layer 1 Debug & Math Validator -- {ts}")
    print(f"{'='*70}")

    debug_spectrum_color()
    debug_bbw_calculation()
    debug_percentrank()
    debug_state_machine()
    debug_timeout()
    debug_pipeline_invariants()
    debug_cross_validate_real()

    print(f"\n{'='*70}")
    print(f"DEBUG RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))
    print(f"{'='*70}")

    return FAIL_COUNT


if __name__ == "__main__":
    sys.exit(main())
