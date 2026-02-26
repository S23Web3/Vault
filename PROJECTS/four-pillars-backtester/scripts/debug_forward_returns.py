"""
Debug and Math Validator for Layer 3 Forward Return Tagger.

Hand-computed vectors with exact expected values from audit pass 3.
6 sections, 60+ checks.

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


# =============================================================================
# SECTION 1: ATR calculation validation (atr_period=3)
# =============================================================================

def debug_atr_calculation():
    """Verify ATR against manual TR + Wilder EWM, atr_period=3, 10-bar dataset."""
    print("\n[Debug 1] ATR Calculation -- Manual Verification")

    df = pd.DataFrame({
        'open':     [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
        'high':     [102, 104, 105, 106, 107, 108, 109, 110, 111, 112],
        'low':      [ 98,  99, 100, 101, 102, 103, 104, 105, 106, 107],
        'close':    [101, 103, 104, 105, 106, 107, 108, 109, 110, 111],
        'base_vol': [1000]*10,
    })

    atr = _calculate_atr(df, period=3)

    check("TR[0]=NaN (no prev_close)", np.isnan(atr.iloc[0]))

    check("ATR[1]=NaN", np.isnan(atr.iloc[1]))
    check("ATR[2]=NaN", np.isnan(atr.iloc[2]))

    check("ATR[3] not NaN", not np.isnan(atr.iloc[3]))
    check("ATR[3] approx 5.0", abs(atr.iloc[3] - 5.0) < 0.1,
          f"got {atr.iloc[3]:.6f}")

    for i in range(4, 10):
        check(f"ATR[{i}] approx 5.0", abs(atr.iloc[i] - 5.0) < 0.1,
              f"got {atr.iloc[i]:.6f}")


# =============================================================================
# SECTION 2: Forward return exact values (audit-verified)
# =============================================================================

def debug_forward_return_exact():
    """20-bar dataset with hand-computed values from audit pass 2+3."""
    print("\n[Debug 2] Forward Return Exact Values -- Audit-Verified")

    opens =  [100]*16 + [101, 103, 104, 96]
    highs =  [102]*16 + [105, 107, 106, 98]
    lows =   [ 98]*16 + [ 99, 101,  95, 93]
    closes = [100]*16 + [103, 104,  96, 94]

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': [1000]*20
    })

    # -- Bar 15, window=4, atr_period=2 --
    result = tag_forward_returns(df, windows=[4], atr_period=2)

    atr_15 = result[ATR_COL].iloc[15]
    check("bar15 ATR=4.0", abs(atr_15 - 4.0) < 0.001, f"got {atr_15:.6f}")

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

    # -- Bar 16, window=3, atr_period=2 (second call) --
    result2 = tag_forward_returns(df, windows=[3], atr_period=2)

    atr_16 = result2[ATR_COL].iloc[16]
    check("bar16 ATR=5.0", abs(atr_16 - 5.0) < 0.001, f"got {atr_16:.6f}")

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


# =============================================================================
# SECTION 3: Sign convention validation
# =============================================================================

def debug_sign_conventions():
    """Verify sign invariants across all bars of random data."""
    print("\n[Debug 3] Sign Conventions -- Global Invariants")

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

    for col in result.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(result[col].dropna()).sum()
        check(f"no inf in {col}", inf_ct == 0)


# =============================================================================
# SECTION 4: Edge cases
# =============================================================================

def debug_edge_cases():
    """Flat prices, single bar window, oversized window, NaN boundary."""
    print("\n[Debug 4] Edge Cases")

    # -- Flat prices: ATR=0 -> NaN, not inf --
    n = 50
    df_flat = pd.DataFrame({
        'open': [100.0]*n, 'high': [100.0]*n, 'low': [100.0]*n,
        'close': [100.0]*n, 'base_vol': [1000]*n
    })
    r_flat = tag_forward_returns(df_flat, windows=[5], atr_period=3)
    for col in r_flat.select_dtypes(include=[np.number]).columns:
        inf_ct = np.isinf(r_flat[col].dropna()).sum()
        check(f"flat: no inf in {col}", inf_ct == 0)

    # -- Single bar window (window=1) --
    df = pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [102, 103, 104, 105, 106],
        'low':  [ 98,  99, 100, 101, 102],
        'close':[101, 102, 103, 104, 105],
        'base_vol': [1000]*5,
    })
    r1 = tag_forward_returns(df, windows=[1], atr_period=2)
    up_0 = r1['fwd_1_max_up_pct'].iloc[0]
    if not np.isnan(up_0):
        expected = (103 - 101) / 101 * 100
        check("window=1 bar0 max_up_pct", abs(up_0 - expected) < 0.001,
              f"got {up_0:.6f}, expected {expected:.6f}")
    check("window=1 last bar NaN", np.isnan(r1['fwd_1_max_up_pct'].iloc[-1]))

    # -- Very large window (window > len) -> all NaN --
    r_big = tag_forward_returns(df, windows=[100], atr_period=2)
    check("window>len: all NaN",
          r_big['fwd_100_max_up_pct'].isna().all())

    # -- NaN boundary for window=10 on 100-bar df --
    df100 = pd.DataFrame({
        'open': np.random.RandomState(42).normal(100, 1, 100),
        'high': np.random.RandomState(42).normal(101, 1, 100),
        'low': np.random.RandomState(42).normal(99, 1, 100),
        'close': np.random.RandomState(42).normal(100, 1, 100),
        'base_vol': [1000]*100,
    })
    df100['high'] = df100[['open','high','close']].max(axis=1) + 0.1
    df100['low'] = df100[['open','low','close']].min(axis=1) - 0.1

    r100 = tag_forward_returns(df100, windows=[10], atr_period=14)
    last_10 = r100['fwd_10_max_up_pct'].iloc[-10:]
    check("last 10 bars NaN", last_10.isna().all(),
          f"non-NaN: {last_10.notna().sum()}")
    if not np.isnan(r100[ATR_COL].iloc[89]):
        check("bar 89 valid", not np.isnan(r100['fwd_10_max_up_pct'].iloc[89]))


# =============================================================================
# SECTION 5: Cross-validate with Layer 1+2 on real data
# =============================================================================

def debug_cross_validate_real():
    """L1 -> L2 -> L3 on RIVERUSDT 5m. Group by state, verify BLUE_DOUBLE > NORMAL."""
    print("\n[Debug 5] Cross-Validate Real Data (L1+L2+L3)")

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

    df_l1 = calculate_bbwp(df_5m)
    df_l2 = track_bbw_sequence(df_l1)
    result = tag_forward_returns(df_l2, windows=[10])

    valid = result.dropna(subset=['fwd_10_max_range_atr', 'bbwp_state'])

    grouped = valid.groupby('bbwp_state').agg({
        'fwd_10_max_range_atr': 'mean',
        'fwd_10_max_up_atr': 'mean',
        'fwd_10_max_down_atr': 'mean',
        'fwd_10_proper_move': 'mean',
    }).round(3)

    print(f"\n  State x Forward Return Summary:")
    hdr = f"  {'State':20s} {'range_atr':>10s} {'up_atr':>10s} {'down_atr':>10s} {'proper%':>10s}"
    print(hdr)
    for state in ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL',
                  'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE']:
        if state in grouped.index:
            r = grouped.loc[state]
            print(f"  {state:20s} {r['fwd_10_max_range_atr']:10.3f} "
                  f"{r['fwd_10_max_up_atr']:10.3f} {r['fwd_10_max_down_atr']:10.3f} "
                  f"{r['fwd_10_proper_move']*100:9.1f}%")

    if 'BLUE_DOUBLE' in grouped.index and 'NORMAL' in grouped.index:
        bd_range = grouped.loc['BLUE_DOUBLE', 'fwd_10_max_range_atr']
        nm_range = grouped.loc['NORMAL', 'fwd_10_max_range_atr']
        # Soft check: hypothesis may not hold on all coins/timeframes
        if bd_range > nm_range:
            check("BLUE_DOUBLE range > NORMAL range", True,
                  f"BD={bd_range:.3f} > NORMAL={nm_range:.3f}")
        else:
            print(f"  INFO  BLUE_DOUBLE range <= NORMAL range -- "
                  f"BD={bd_range:.3f}, NORMAL={nm_range:.3f} (hypothesis not confirmed)")

    print(f"\n  Validated {len(valid):,} bars across L1+L2+L3")


# --- _forward_max vectorized trace --------------------------------------------

def debug_forward_max_trace():
    """Verify _forward_max on a 5-element series."""
    print("\n[Debug 6] _forward_max Vectorized Trace")

    s = pd.Series([10, 20, 30, 40, 50])

    result = _forward_max(s, 2)
    check("fwd_max[0]=30", result.iloc[0] == 30, f"got {result.iloc[0]}")
    check("fwd_max[1]=40", result.iloc[1] == 40, f"got {result.iloc[1]}")
    check("fwd_max[2]=50", result.iloc[2] == 50, f"got {result.iloc[2]}")
    check("fwd_max[3]=NaN", np.isnan(result.iloc[3]))
    check("fwd_max[4]=NaN", np.isnan(result.iloc[4]))

    result_min = _forward_min(s, 2)
    check("fwd_min[0]=20", result_min.iloc[0] == 20, f"got {result_min.iloc[0]}")
    check("fwd_min[1]=30", result_min.iloc[1] == 30, f"got {result_min.iloc[1]}")
    check("fwd_min[2]=40", result_min.iloc[2] == 40, f"got {result_min.iloc[2]}")


# --- Main ---------------------------------------------------------------------

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

    print(f"\n{'='*70}")
    print(f"DEBUG RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print("FAILURES: " + ", ".join(ERRORS))
    print(f"{'='*70}")

    return FAIL_COUNT


if __name__ == "__main__":
    sys.exit(main())
