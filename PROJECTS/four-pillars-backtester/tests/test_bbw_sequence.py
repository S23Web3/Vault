"""
Tests for signals/bbw_sequence.py — Layer 2 BBW Sequence Tracker.
10 tests, 40+ assertions. Synthetic data with known expected outputs.

Run: python tests/test_bbw_sequence.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from signals.bbw_sequence import (
    track_bbw_sequence, COLOR_ORDER, COLOR_LETTERS, VALID_COLORS, OUTPUT_COLS
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


def make_sequence_df(spectrums, states=None):
    """Build a minimal DataFrame for Layer 2 input from spectrum list."""
    n = len(spectrums)
    if states is None:
        states = ['NORMAL'] * n
    value_map = {'blue': 15, 'green': 37, 'yellow': 62, 'red': 87, None: np.nan}
    values = [value_map.get(s, np.nan) for s in spectrums]
    return pd.DataFrame({
        'bbwp_spectrum': spectrums,
        'bbwp_state': states,
        'bbwp_value': values,
    })


# ─── Test 1: Output Columns ──────────────────────────────────────────────────

def test_output_columns():
    """Verify all 9 bbw_seq_ columns present with correct dtypes."""
    print("\n[Test 1] Output Columns")

    df = make_sequence_df(['blue', 'green', 'yellow', 'red'] * 5)
    result = track_bbw_sequence(df)

    for col in OUTPUT_COLS:
        check(f"column {col} exists", col in result.columns)

    # Original columns preserved
    for col in ['bbwp_spectrum', 'bbwp_state', 'bbwp_value']:
        check(f"original {col} preserved", col in result.columns)

    check("total column count", len(result.columns) == 3 + 9,
          f"got {len(result.columns)}, expected 12")


# ─── Test 2: Missing Layer 1 Columns ─────────────────────────────────────────

def test_missing_columns():
    """Raises ValueError if Layer 1 columns missing."""
    print("\n[Test 2] Missing Layer 1 Columns")

    df_bad = pd.DataFrame({'close': [100, 101, 102]})
    raised = False
    try:
        track_bbw_sequence(df_bad)
    except ValueError as e:
        raised = True
        check("ValueError mentions column", "bbwp_spectrum" in str(e))
    check("ValueError raised", raised)


# ─── Test 3: NaN Spectrum Skipped ─────────────────────────────────────────────

def test_nan_spectrum_skipped():
    """Warmup bars (None spectrum) get defaults, tracking starts at first valid bar."""
    print("\n[Test 3] NaN Spectrum Skipped")

    spectrums = [None, None, None, 'blue', 'blue', 'green']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    # None rows get defaults
    check("None row 0 bars_in_color=0", result['bbw_seq_bars_in_color'].iloc[0] == 0)
    check("None row 0 direction=None", result['bbw_seq_direction'].iloc[0] is None)
    check("None row 0 pattern_id=''", result['bbw_seq_pattern_id'].iloc[0] == '')
    check("None row 0 from_blue=NaN", np.isnan(result['bbw_seq_from_blue_bars'].iloc[0]))

    # First valid bar (idx 3) starts tracking
    check("first valid bar prev_color=None", result['bbw_seq_prev_color'].iloc[3] is None)
    check("first valid bar bars_in_color=1", result['bbw_seq_bars_in_color'].iloc[3] == 1)
    check("first valid bar color_changed=False", result['bbw_seq_color_changed'].iloc[3] == False)


# ─── Test 4: Color Transitions ───────────────────────────────────────────────

def test_color_transitions():
    """Known transition sequence with None warmup."""
    print("\n[Test 4] Color Transitions")

    spectrums = [None]*5 + ['blue','blue','green','green','green','yellow','red']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    # Bar 5 (first blue): prev=None, no change
    check("bar5 prev=None", result['bbw_seq_prev_color'].iloc[5] is None)
    check("bar5 changed=False", result['bbw_seq_color_changed'].iloc[5] == False)

    # Bar 6 (second blue): prev=blue, no change
    check("bar6 prev=blue", result['bbw_seq_prev_color'].iloc[6] == 'blue')
    check("bar6 changed=False", result['bbw_seq_color_changed'].iloc[6] == False)

    # Bar 7 (first green): prev=blue, changed
    check("bar7 prev=blue", result['bbw_seq_prev_color'].iloc[7] == 'blue')
    check("bar7 changed=True", result['bbw_seq_color_changed'].iloc[7] == True)

    # Bar 10 (yellow): prev=green, changed
    check("bar10 prev=green", result['bbw_seq_prev_color'].iloc[10] == 'green')
    check("bar10 changed=True", result['bbw_seq_color_changed'].iloc[10] == True)

    # Bar 11 (red): prev=yellow, changed
    check("bar11 prev=yellow", result['bbw_seq_prev_color'].iloc[11] == 'yellow')
    check("bar11 changed=True", result['bbw_seq_color_changed'].iloc[11] == True)


# ─── Test 5: Bars in Color ───────────────────────────────────────────────────

def test_bars_in_color():
    """Bars in color monotonic within run, resets on change."""
    print("\n[Test 5] Bars in Color")

    spectrums = ['blue','blue','blue','green','green','yellow']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    bic = result['bbw_seq_bars_in_color'].tolist()
    check("blue run 1,2,3", bic[0:3] == [1, 2, 3])
    check("green resets 1,2", bic[3:5] == [1, 2])
    check("yellow resets 1", bic[5] == 1)


# ─── Test 6: Direction ───────────────────────────────────────────────────────

def test_direction():
    """Expanding, contracting, flat on known transitions."""
    print("\n[Test 6] Direction")

    spectrums = ['blue', 'blue', 'green', 'yellow', 'green', 'red']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    dirs = result['bbw_seq_direction'].tolist()
    check("bar0 first bar direction=None", dirs[0] is None)
    check("bar1 same=flat", dirs[1] == 'flat')
    check("bar2 blue->green=expanding", dirs[2] == 'expanding')
    check("bar3 green->yellow=expanding", dirs[3] == 'expanding')
    check("bar4 yellow->green=contracting", dirs[4] == 'contracting')
    check("bar5 green->red=expanding", dirs[5] == 'expanding')


# ─── Test 7: Skip Detection ──────────────────────────────────────────────────

def test_skip_detection():
    """blue->yellow=skip, blue->green=no skip, blue->red=skip, red->blue=skip."""
    print("\n[Test 7] Skip Detection")

    spectrums = ['blue', 'green', 'blue', 'yellow', 'blue', 'red', 'blue']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    skips = result['bbw_seq_skip_detected'].tolist()
    check("blue->green no skip", skips[1] == False)
    check("green->blue no skip", skips[2] == False)
    check("blue->yellow SKIP", skips[3] == True)
    check("yellow->blue SKIP", skips[4] == True)
    check("blue->red SKIP", skips[5] == True)
    check("red->blue SKIP", skips[6] == True)


# ─── Test 8: Pattern ID ──────────────────────────────────────────────────────

def test_pattern_id():
    """Pattern builds as transitions accumulate, max 3 letters."""
    print("\n[Test 8] Pattern ID")

    spectrums = ['blue', 'green', 'yellow', 'red', 'blue']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    pids = result['bbw_seq_pattern_id'].tolist()
    check("bar0 pattern='B'", pids[0] == 'B')
    check("bar1 pattern='BG'", pids[1] == 'BG')
    check("bar2 pattern='BGY'", pids[2] == 'BGY')
    check("bar3 pattern='GYR' (window slides)", pids[3] == 'GYR')
    check("bar4 pattern='YRB' (window slides)", pids[4] == 'YRB')


# ─── Test 9: From Blue/Red Bars ──────────────────────────────────────────────

def test_from_blue_red_bars():
    """Correct distances: 0 on blue bar, NaN if never seen."""
    print("\n[Test 9] From Blue/Red Bars")

    spectrums = ['green', 'green', 'blue', 'green', 'red', 'green']
    df = make_sequence_df(spectrums)
    result = track_bbw_sequence(df)

    fb = result['bbw_seq_from_blue_bars'].tolist()
    fr = result['bbw_seq_from_red_bars'].tolist()

    # Before seeing blue: NaN
    check("bar0 from_blue=NaN", np.isnan(fb[0]))
    check("bar1 from_blue=NaN", np.isnan(fb[1]))

    # On blue bar: 0
    check("bar2 from_blue=0", fb[2] == 0)

    # After blue: distance grows
    check("bar3 from_blue=1", fb[3] == 1)
    check("bar4 from_blue=2", fb[4] == 2)
    check("bar5 from_blue=3", fb[5] == 3)

    # Before seeing red: NaN
    check("bar0 from_red=NaN", np.isnan(fr[0]))
    check("bar3 from_red=NaN", np.isnan(fr[3]))

    # On red bar: 0
    check("bar4 from_red=0", fr[4] == 0)

    # After red: distance
    check("bar5 from_red=1", fr[5] == 1)


# ─── Test 10: Real Parquet ────────────────────────────────────────────────────

def test_on_real_parquet():
    """Load RIVERUSDT 5m, run Layer 1 + Layer 2, check distributions."""
    print("\n[Test 10] Real Parquet (RIVERUSDT 5m)")

    from signals.bbwp import calculate_bbwp

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

    # Layer 1
    df_l1 = calculate_bbwp(df_5m)
    # Layer 2
    result = track_bbw_sequence(df_l1)

    valid = result[result['bbwp_spectrum'].notna()]
    print(f"  Valid bars: {len(valid):,}")

    # bars_in_color mean > 1 (colors persist for multiple bars)
    bic_mean = valid['bbw_seq_bars_in_color'].mean()
    check("bars_in_color mean > 1", bic_mean > 1, f"mean={bic_mean:.1f}")

    # color_changed pct < 50%
    cc_pct = valid['bbw_seq_color_changed'].mean()
    check("color_changed < 50%", cc_pct < 0.50, f"pct={cc_pct:.1%}")

    # skip_detected pct < 20%
    sd_pct = valid['bbw_seq_skip_detected'].mean()
    check("skip_detected < 20%", sd_pct < 0.20, f"pct={sd_pct:.1%}")

    # pattern_id has multiple unique values
    n_patterns = valid['bbw_seq_pattern_id'].nunique()
    check("pattern_id diverse (>5)", n_patterns > 5, f"unique={n_patterns}")

    # from_blue_bars min = 0 (seen on blue bars themselves)
    fb_min = valid['bbw_seq_from_blue_bars'].min()
    check("from_blue_bars min=0", fb_min == 0, f"min={fb_min}")

    # from_red_bars min = 0
    fr_min = valid['bbw_seq_from_red_bars'].min()
    check("from_red_bars min=0", fr_min == 0, f"min={fr_min}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run all 10 Layer 2 tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBW Sequence Layer 2 Tests -- {ts}")
    print(f"{'='*70}")

    test_output_columns()
    test_missing_columns()
    test_nan_spectrum_skipped()
    test_color_transitions()
    test_bars_in_color()
    test_direction()
    test_skip_detection()
    test_pattern_id()
    test_from_blue_red_bars()
    test_on_real_parquet()

    print(f"\n{'='*70}")
    print(f"RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print(f"FAILURES: {', '.join(ERRORS)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
