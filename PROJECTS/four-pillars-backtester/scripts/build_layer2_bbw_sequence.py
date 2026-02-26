"""
Build script: Layer 2 — BBW Sequence Tracker.

Creates 4 files:
  1. signals/bbw_sequence.py        — sequence tracking module
  2. tests/test_bbw_sequence.py     — 10 tests, 40+ assertions
  3. scripts/sanity_check_bbw_sequence.py — RIVERUSDT distribution stats
  4. scripts/debug_bbw_sequence.py  — math/logic validation with crafted data

Then runs: tests -> sanity check -> debug validator.
Logs results to 06-CLAUDE-LOGS/2026-02-14-bbw-layer2-build.md

Run: python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\build_layer2_bbw_sequence.py"
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent
SIGNALS = ROOT / "signals"
TESTS = ROOT / "tests"
SCRIPTS = ROOT / "scripts"

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print(f"{'='*70}")
print(f"Layer 2 Build Script -- {ts}")
print(f"{'='*70}")

# ─── Safety: check targets don't exist ────────────────────────────────────────

TARGETS = {
    "signals/bbw_sequence.py": SIGNALS / "bbw_sequence.py",
    "tests/test_bbw_sequence.py": TESTS / "test_bbw_sequence.py",
    "scripts/sanity_check_bbw_sequence.py": SCRIPTS / "sanity_check_bbw_sequence.py",
    "scripts/debug_bbw_sequence.py": SCRIPTS / "debug_bbw_sequence.py",
}

for name, path in TARGETS.items():
    if path.exists():
        print(f"FATAL: {name} already exists. Remove or rename before running.")
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 1: signals/bbw_sequence.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing signals/bbw_sequence.py ---")

(SIGNALS / "bbw_sequence.py").write_text(r'''"""
Layer 2: BBW Sequence Tracker — color transitions, direction, skip detection, pattern IDs.

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with Layer 1 columns: bbwp_spectrum, bbwp_state, bbwp_value.
Output: Same DataFrame with 9 new bbw_seq_ columns added.

Depends on: signals/bbwp.py (Layer 1) output.
"""

import numpy as np
import pandas as pd

# ─── Constants (4 colors matching Pine v2 gradient inflection at 25/50/75) ───

COLOR_ORDER = {'blue': 0, 'green': 1, 'yellow': 2, 'red': 3}
COLOR_LETTERS = {'blue': 'B', 'green': 'G', 'yellow': 'Y', 'red': 'R'}
VALID_COLORS = set(COLOR_ORDER.keys())

REQUIRED_COLS = ['bbwp_spectrum', 'bbwp_state', 'bbwp_value']

OUTPUT_COLS = [
    'bbw_seq_prev_color', 'bbw_seq_color_changed', 'bbw_seq_bars_in_color',
    'bbw_seq_bars_in_state', 'bbw_seq_direction', 'bbw_seq_skip_detected',
    'bbw_seq_pattern_id', 'bbw_seq_from_blue_bars', 'bbw_seq_from_red_bars',
]


def _sequence_direction(prev_color, curr_color):
    """Return 'expanding', 'contracting', or 'flat' based on color order transition."""
    if prev_color is None or curr_color is None:
        return None
    if prev_color == curr_color:
        return 'flat'
    return 'expanding' if COLOR_ORDER[curr_color] > COLOR_ORDER[prev_color] else 'contracting'


def _is_skip(prev_color, curr_color):
    """Return True if the transition skipped a color step (abs diff > 1)."""
    if prev_color is None or curr_color is None:
        return False
    return abs(COLOR_ORDER[curr_color] - COLOR_ORDER[prev_color]) > 1


def track_bbw_sequence(df: pd.DataFrame) -> pd.DataFrame:
    """Track BBWP color sequences, transitions, patterns, and distances.

    Input: DataFrame with Layer 1 columns: bbwp_spectrum, bbwp_state, bbwp_value.
    Output: Same DataFrame with 9 new bbw_seq_ columns added.
    """
    # Validate required columns
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing required Layer 1 column: {col}")

    result = df.copy()
    n = len(result)

    # Pre-allocate output arrays
    prev_color_arr = np.empty(n, dtype=object)
    color_changed_arr = np.zeros(n, dtype=bool)
    bars_in_color_arr = np.zeros(n, dtype=np.int64)
    bars_in_state_arr = np.zeros(n, dtype=np.int64)
    direction_arr = np.empty(n, dtype=object)
    skip_detected_arr = np.zeros(n, dtype=bool)
    pattern_id_arr = np.empty(n, dtype=object)
    from_blue_arr = np.full(n, np.nan)
    from_red_arr = np.full(n, np.nan)

    # Initialize defaults for NaN/None rows
    for i in range(n):
        prev_color_arr[i] = None
        direction_arr[i] = None
        pattern_id_arr[i] = ''

    # Stateful tracking variables
    last_color = None
    last_state = None
    current_color_count = 0
    current_state_count = 0
    last_blue_idx = -1  # -1 means never seen
    last_red_idx = -1
    recent_transitions = []  # max 3 color letters

    spectrums = result['bbwp_spectrum'].values
    states = result['bbwp_state'].values

    for i in range(n):
        spectrum = spectrums[i]
        state = states[i]

        # Skip None/NaN spectrum bars entirely
        if spectrum is None or (isinstance(spectrum, float) and np.isnan(spectrum)):
            prev_color_arr[i] = None
            color_changed_arr[i] = False
            bars_in_color_arr[i] = 0
            bars_in_state_arr[i] = 0
            direction_arr[i] = None
            skip_detected_arr[i] = False
            pattern_id_arr[i] = ''
            from_blue_arr[i] = np.nan
            from_red_arr[i] = np.nan
            continue

        # Valid spectrum bar — track it
        prev_color_arr[i] = last_color

        # Color tracking
        if last_color is None:
            # First valid bar
            color_changed_arr[i] = False
            current_color_count = 1
            direction_arr[i] = None
            skip_detected_arr[i] = False
            recent_transitions.append(COLOR_LETTERS.get(spectrum, '?'))
        elif spectrum != last_color:
            # Color changed
            color_changed_arr[i] = True
            current_color_count = 1
            direction_arr[i] = _sequence_direction(last_color, spectrum)
            skip_detected_arr[i] = _is_skip(last_color, spectrum)
            recent_transitions.append(COLOR_LETTERS.get(spectrum, '?'))
            if len(recent_transitions) > 3:
                recent_transitions = recent_transitions[-3:]
        else:
            # Same color
            color_changed_arr[i] = False
            current_color_count += 1
            direction_arr[i] = 'flat'
            skip_detected_arr[i] = False

        bars_in_color_arr[i] = current_color_count

        # State tracking
        if last_state is None or state != last_state:
            current_state_count = 1
        else:
            current_state_count += 1
        bars_in_state_arr[i] = current_state_count

        # Pattern ID = last 3 transitions
        pattern_id_arr[i] = ''.join(recent_transitions[-3:])

        # Blue/red distance tracking
        if spectrum == 'blue':
            last_blue_idx = i
        if spectrum == 'red':
            last_red_idx = i

        from_blue_arr[i] = (i - last_blue_idx) if last_blue_idx >= 0 else np.nan
        from_red_arr[i] = (i - last_red_idx) if last_red_idx >= 0 else np.nan

        # Update state for next iteration
        last_color = spectrum
        last_state = state

    # Assign columns
    result['bbw_seq_prev_color'] = prev_color_arr
    result['bbw_seq_color_changed'] = color_changed_arr
    result['bbw_seq_bars_in_color'] = bars_in_color_arr
    result['bbw_seq_bars_in_state'] = bars_in_state_arr
    result['bbw_seq_direction'] = direction_arr
    result['bbw_seq_skip_detected'] = skip_detected_arr
    result['bbw_seq_pattern_id'] = pattern_id_arr
    result['bbw_seq_from_blue_bars'] = from_blue_arr
    result['bbw_seq_from_red_bars'] = from_red_arr

    return result
''', encoding='utf-8')
print("  OK    signals/bbw_sequence.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 2: tests/test_bbw_sequence.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing tests/test_bbw_sequence.py ---")

(TESTS / "test_bbw_sequence.py").write_text(r'''"""
Tests for signals/bbw_sequence.py — Layer 2 BBW Sequence Tracker.
10 tests, 40+ assertions. Synthetic data with known expected outputs.

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_bbw_sequence.py"
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
''', encoding='utf-8')
print("  OK    tests/test_bbw_sequence.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 3: scripts/sanity_check_bbw_sequence.py
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing scripts/sanity_check_bbw_sequence.py ---")

(SCRIPTS / "sanity_check_bbw_sequence.py").write_text(r'''"""
Sanity check: Run Layer 1 + Layer 2 on RIVERUSDT 5m, print distribution stats.

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\sanity_check_bbw_sequence.py"
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from signals.bbwp import calculate_bbwp
from signals.bbw_sequence import track_bbw_sequence


def main():
    """Run BBW Sequence sanity check on RIVERUSDT 5m data."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBW Sequence Layer 2 Sanity Check -- {ts}")
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

    print(f"\n  Input: {len(df):,} bars (5m)")

    # Layer 1
    t0 = time.time()
    df_l1 = calculate_bbwp(df)
    t1 = time.time()

    # Layer 2
    result = track_bbw_sequence(df_l1)
    t2 = time.time()

    l1_time = t1 - t0
    l2_time = t2 - t1
    total = t2 - t0
    print(f"  Layer 1: {l1_time:.2f}s ({len(df)/l1_time:,.0f} bars/sec)")
    print(f"  Layer 2: {l2_time:.2f}s ({len(df)/l2_time:,.0f} bars/sec)")
    print(f"  Total:   {total:.2f}s ({len(df)/total:,.0f} bars/sec)")

    valid = result[result['bbwp_spectrum'].notna()]
    nan_count = result['bbwp_spectrum'].isna().sum()
    print(f"  Valid bars: {len(valid):,}")
    print(f"  NaN warmup: {nan_count:,}")

    # Color Transition Frequency
    print(f"\n--- Color Transitions ---")
    cc_count = valid['bbw_seq_color_changed'].sum()
    cc_pct = cc_count / len(valid) * 100
    print(f"  Transitions: {int(cc_count):,} ({cc_pct:.1f}%)")

    # Direction Distribution
    print(f"\n--- Direction Distribution ---")
    dir_dist = valid['bbw_seq_direction'].value_counts()
    for d in ['flat', 'expanding', 'contracting']:
        count = dir_dist.get(d, 0)
        pct = count / len(valid) * 100
        print(f"  {d:15s} {count:6,} ({pct:5.1f}%)")
    none_dirs = valid['bbw_seq_direction'].isna().sum()
    print(f"  {'None':15s} {none_dirs:6,} ({none_dirs/len(valid)*100:5.1f}%)")

    # Skip Detection Rate
    print(f"\n--- Skip Detection ---")
    skip_count = valid['bbw_seq_skip_detected'].sum()
    skip_pct = skip_count / len(valid) * 100
    print(f"  Skips: {int(skip_count):,} ({skip_pct:.1f}%)")
    # Skip breakdown: which transitions caused skips
    skip_rows = valid[valid['bbw_seq_skip_detected'] == True]
    if len(skip_rows) > 0:
        skip_trans = []
        for _, row in skip_rows.iterrows():
            prev = row['bbw_seq_prev_color']
            curr = row['bbwp_spectrum']
            if prev and curr:
                skip_trans.append(f"{prev}->{curr}")
        if skip_trans:
            from collections import Counter
            top_skips = Counter(skip_trans).most_common(5)
            for trans, cnt in top_skips:
                print(f"    {trans}: {cnt:,}")

    # Top 10 Pattern IDs
    print(f"\n--- Top 10 Pattern IDs ---")
    pid_dist = valid['bbw_seq_pattern_id'].value_counts().head(10)
    for pid, count in pid_dist.items():
        pct = count / len(valid) * 100
        print(f"  {pid:6s} {count:6,} ({pct:5.1f}%)")

    # Bars in Color per color
    print(f"\n--- Bars in Color (per spectrum) ---")
    for color in ['blue', 'green', 'yellow', 'red']:
        rows = valid[valid['bbwp_spectrum'] == color]
        if len(rows) > 0:
            bic = rows['bbw_seq_bars_in_color']
            print(f"  {color:8s}  mean={bic.mean():5.1f}  median={bic.median():5.0f}  max={bic.max():5.0f}")

    # Bars in State per state
    print(f"\n--- Bars in State (per state) ---")
    for state in ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL',
                  'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE']:
        rows = valid[valid['bbwp_state'] == state]
        if len(rows) > 0:
            bis = rows['bbw_seq_bars_in_state']
            print(f"  {state:20s}  mean={bis.mean():5.1f}  median={bis.median():5.0f}  max={bis.max():5.0f}")

    # From Blue/Red Bars
    print(f"\n--- Distance from Blue/Red ---")
    fb = valid['bbw_seq_from_blue_bars'].dropna()
    fr = valid['bbw_seq_from_red_bars'].dropna()
    if len(fb) > 0:
        print(f"  from_blue: mean={fb.mean():.1f}  P50={fb.quantile(0.5):.0f}  P90={fb.quantile(0.9):.0f}")
    if len(fr) > 0:
        print(f"  from_red:  mean={fr.mean():.1f}  P50={fr.quantile(0.5):.0f}  P90={fr.quantile(0.9):.0f}")

    # NaN Check
    print(f"\n--- NaN Check (valid bars only) ---")
    for col in ['bbw_seq_bars_in_color', 'bbw_seq_bars_in_state',
                'bbw_seq_color_changed', 'bbw_seq_skip_detected']:
        nan_ct = valid[col].isna().sum()
        status = "OK" if nan_ct == 0 else f"WARN: {nan_ct} NaN"
        print(f"  {col:30s} {status}")

    print(f"\n{'='*70}")
    print(f"SANITY CHECK COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
''', encoding='utf-8')
print("  OK    scripts/sanity_check_bbw_sequence.py")

# ═══════════════════════════════════════════════════════════════════════════════
# FILE 4: scripts/debug_bbw_sequence.py — Math/Logic Validator
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n--- Writing scripts/debug_bbw_sequence.py ---")

(SCRIPTS / "debug_bbw_sequence.py").write_text(r'''"""
Debug & Math Validator for Layer 2 BBW Sequence Tracker.

Crafted test vectors with hand-computed expected values.
Every assertion has a comment explaining the math.
Catches off-by-one, wrong direction, broken counters, NaN leaks.

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\debug_bbw_sequence.py"
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from signals.bbw_sequence import (
    track_bbw_sequence, _sequence_direction, _is_skip,
    COLOR_ORDER, COLOR_LETTERS, VALID_COLORS
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


def make_df(spectrums, states=None):
    """Build minimal Layer 2 input DataFrame."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Helper function unit tests
# ═══════════════════════════════════════════════════════════════════════════════

def debug_helper_functions():
    """Validate _sequence_direction and _is_skip against all color pairs."""
    print("\n[Debug 1] Helper Functions — All Color Pairs")

    # _sequence_direction truth table:
    # blue(0)->green(1)  = expanding  (1>0)
    # blue(0)->yellow(2) = expanding  (2>0)
    # blue(0)->red(3)    = expanding  (3>0)
    # green(1)->blue(0)  = contracting (0<1)
    # green(1)->yellow(2)= expanding  (2>1)
    # green(1)->red(3)   = expanding  (3>1)
    # yellow(2)->blue(0) = contracting (0<2)
    # yellow(2)->green(1)= contracting (1<2)
    # yellow(2)->red(3)  = expanding  (3>2)
    # red(3)->blue(0)    = contracting (0<3)
    # red(3)->green(1)   = contracting (1<3)
    # red(3)->yellow(2)  = contracting (2<3)
    # same->same         = flat

    direction_cases = [
        ('blue', 'green', 'expanding'),
        ('blue', 'yellow', 'expanding'),
        ('blue', 'red', 'expanding'),
        ('green', 'blue', 'contracting'),
        ('green', 'yellow', 'expanding'),
        ('green', 'red', 'expanding'),
        ('yellow', 'blue', 'contracting'),
        ('yellow', 'green', 'contracting'),
        ('yellow', 'red', 'expanding'),
        ('red', 'blue', 'contracting'),
        ('red', 'green', 'contracting'),
        ('red', 'yellow', 'contracting'),
    ]

    for prev, curr, expected in direction_cases:
        got = _sequence_direction(prev, curr)
        check(f"dir {prev}->{curr}={expected}", got == expected, f"got={got}")

    # Same color = flat
    for color in VALID_COLORS:
        got = _sequence_direction(color, color)
        check(f"dir {color}->{color}=flat", got == 'flat', f"got={got}")

    # None inputs
    check("dir None->blue=None", _sequence_direction(None, 'blue') is None)
    check("dir blue->None=None", _sequence_direction('blue', None) is None)

    # _is_skip truth table:
    # Skip if abs(ORDER[curr] - ORDER[prev]) > 1
    # blue(0)->green(1):  |1-0|=1 -> False
    # blue(0)->yellow(2): |2-0|=2 -> True
    # blue(0)->red(3):    |3-0|=3 -> True
    # green(1)->yellow(2):|2-1|=1 -> False
    # green(1)->red(3):   |3-1|=2 -> True
    # yellow(2)->red(3):  |3-2|=1 -> False
    # And all reverses

    skip_cases = [
        ('blue', 'green', False),    # |1-0|=1
        ('blue', 'yellow', True),    # |2-0|=2
        ('blue', 'red', True),       # |3-0|=3
        ('green', 'blue', False),    # |0-1|=1
        ('green', 'yellow', False),  # |2-1|=1
        ('green', 'red', True),      # |3-1|=2
        ('yellow', 'blue', True),    # |0-2|=2
        ('yellow', 'green', False),  # |1-2|=1
        ('yellow', 'red', False),    # |3-2|=1
        ('red', 'blue', True),       # |0-3|=3
        ('red', 'green', True),      # |1-3|=2
        ('red', 'yellow', False),    # |2-3|=1
    ]

    for prev, curr, expected in skip_cases:
        got = _is_skip(prev, curr)
        check(f"skip {prev}->{curr}={expected}", got == expected, f"got={got}")

    # Same color never skip
    for color in VALID_COLORS:
        check(f"skip {color}->{color}=False", _is_skip(color, color) == False)

    # None inputs
    check("skip None->blue=False", _is_skip(None, 'blue') == False)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Full pipeline — hand-computed expected values
# ═══════════════════════════════════════════════════════════════════════════════

def debug_full_pipeline_vector():
    """Hand-computed 12-bar vector, verify every cell."""
    print("\n[Debug 2] Full Pipeline — 12-Bar Hand-Computed Vector")

    # Sequence: None, None, blue, blue, green, green, yellow, red, red, blue, green, green
    # Index:    0     1     2     3     4      5      6       7    8    9     10     11
    spectrums = [None, None, 'blue', 'blue', 'green', 'green', 'yellow', 'red', 'red', 'blue', 'green', 'green']
    states =    ['NORMAL']*2 + ['BLUE_DOUBLE', 'BLUE', 'NORMAL', 'NORMAL', 'NORMAL', 'RED', 'RED_DOUBLE', 'BLUE', 'NORMAL', 'NORMAL']

    df = make_df(spectrums, states)
    r = track_bbw_sequence(df)

    # ── Bar 0: None -> defaults ──
    check("b0 prev=None", r['bbw_seq_prev_color'].iloc[0] is None)
    check("b0 changed=False", r['bbw_seq_color_changed'].iloc[0] == False)
    check("b0 bic=0", r['bbw_seq_bars_in_color'].iloc[0] == 0)
    check("b0 bis=0", r['bbw_seq_bars_in_state'].iloc[0] == 0)
    check("b0 dir=None", r['bbw_seq_direction'].iloc[0] is None)
    check("b0 skip=False", r['bbw_seq_skip_detected'].iloc[0] == False)
    check("b0 pid=''", r['bbw_seq_pattern_id'].iloc[0] == '')
    check("b0 fb=NaN", np.isnan(r['bbw_seq_from_blue_bars'].iloc[0]))
    check("b0 fr=NaN", np.isnan(r['bbw_seq_from_red_bars'].iloc[0]))

    # ── Bar 2: first valid (blue). prev=None, bic=1, transitions=['B'] ──
    check("b2 prev=None", r['bbw_seq_prev_color'].iloc[2] is None)
    check("b2 changed=False", r['bbw_seq_color_changed'].iloc[2] == False)
    check("b2 bic=1", r['bbw_seq_bars_in_color'].iloc[2] == 1)
    check("b2 bis=1", r['bbw_seq_bars_in_state'].iloc[2] == 1)  # BLUE_DOUBLE, first
    check("b2 dir=None", r['bbw_seq_direction'].iloc[2] is None)
    check("b2 skip=False", r['bbw_seq_skip_detected'].iloc[2] == False)
    check("b2 pid='B'", r['bbw_seq_pattern_id'].iloc[2] == 'B')
    check("b2 fb=0", r['bbw_seq_from_blue_bars'].iloc[2] == 0)  # on blue bar
    check("b2 fr=NaN", np.isnan(r['bbw_seq_from_red_bars'].iloc[2]))  # never seen red

    # ── Bar 3: blue again. prev=blue, bic=2, flat ──
    check("b3 prev=blue", r['bbw_seq_prev_color'].iloc[3] == 'blue')
    check("b3 changed=False", r['bbw_seq_color_changed'].iloc[3] == False)
    check("b3 bic=2", r['bbw_seq_bars_in_color'].iloc[3] == 2)
    check("b3 bis=1", r['bbw_seq_bars_in_state'].iloc[3] == 1)  # BLUE != BLUE_DOUBLE, resets
    check("b3 dir=flat", r['bbw_seq_direction'].iloc[3] == 'flat')
    check("b3 pid='B'", r['bbw_seq_pattern_id'].iloc[3] == 'B')  # still just B
    check("b3 fb=0", r['bbw_seq_from_blue_bars'].iloc[3] == 0)

    # ── Bar 4: green. prev=blue, changed, expanding, bic=1 ──
    # transitions = ['B','G'], ORDER[green]=1 > ORDER[blue]=0 -> expanding
    # |1-0|=1 -> no skip
    check("b4 prev=blue", r['bbw_seq_prev_color'].iloc[4] == 'blue')
    check("b4 changed=True", r['bbw_seq_color_changed'].iloc[4] == True)
    check("b4 bic=1", r['bbw_seq_bars_in_color'].iloc[4] == 1)
    check("b4 dir=expanding", r['bbw_seq_direction'].iloc[4] == 'expanding')
    check("b4 skip=False", r['bbw_seq_skip_detected'].iloc[4] == False)
    check("b4 pid='BG'", r['bbw_seq_pattern_id'].iloc[4] == 'BG')
    check("b4 fb=1", r['bbw_seq_from_blue_bars'].iloc[4] == 1)  # idx4 - idx3 = 1

    # ── Bar 6: yellow. prev=green, expanding ──
    # transitions = ['B','G','Y'], ORDER[yellow]=2 > ORDER[green]=1 -> expanding
    # |2-1|=1 -> no skip
    check("b6 prev=green", r['bbw_seq_prev_color'].iloc[6] == 'green')
    check("b6 changed=True", r['bbw_seq_color_changed'].iloc[6] == True)
    check("b6 bic=1", r['bbw_seq_bars_in_color'].iloc[6] == 1)
    check("b6 dir=expanding", r['bbw_seq_direction'].iloc[6] == 'expanding')
    check("b6 skip=False", r['bbw_seq_skip_detected'].iloc[6] == False)
    check("b6 pid='BGY'", r['bbw_seq_pattern_id'].iloc[6] == 'BGY')
    check("b6 fb=3", r['bbw_seq_from_blue_bars'].iloc[6] == 3)  # idx6 - idx3 = 3

    # ── Bar 7: red. prev=yellow, expanding ──
    # transitions = ['B','G','Y','R'][-3:] = ['G','Y','R'] -> 'GYR'
    # ORDER[red]=3 > ORDER[yellow]=2 -> expanding
    # |3-2|=1 -> no skip
    check("b7 prev=yellow", r['bbw_seq_prev_color'].iloc[7] == 'yellow')
    check("b7 changed=True", r['bbw_seq_color_changed'].iloc[7] == True)
    check("b7 dir=expanding", r['bbw_seq_direction'].iloc[7] == 'expanding')
    check("b7 skip=False", r['bbw_seq_skip_detected'].iloc[7] == False)
    check("b7 pid='GYR'", r['bbw_seq_pattern_id'].iloc[7] == 'GYR')
    check("b7 fb=4", r['bbw_seq_from_blue_bars'].iloc[7] == 4)  # idx7 - idx3
    check("b7 fr=0", r['bbw_seq_from_red_bars'].iloc[7] == 0)   # on red bar

    # ── Bar 8: red again. bic=2, flat ──
    check("b8 bic=2", r['bbw_seq_bars_in_color'].iloc[8] == 2)
    check("b8 dir=flat", r['bbw_seq_direction'].iloc[8] == 'flat')
    check("b8 fr=0", r['bbw_seq_from_red_bars'].iloc[8] == 0)  # still on red

    # ── Bar 9: blue. prev=red, contracting, SKIP ──
    # ORDER[blue]=0 < ORDER[red]=3 -> contracting
    # |0-3|=3 -> SKIP!
    # transitions = ['G','Y','R','B'][-3:] = ['Y','R','B'] -> 'YRB'
    check("b9 prev=red", r['bbw_seq_prev_color'].iloc[9] == 'red')
    check("b9 changed=True", r['bbw_seq_color_changed'].iloc[9] == True)
    check("b9 dir=contracting", r['bbw_seq_direction'].iloc[9] == 'contracting')
    check("b9 SKIP=True", r['bbw_seq_skip_detected'].iloc[9] == True)
    check("b9 pid='YRB'", r['bbw_seq_pattern_id'].iloc[9] == 'YRB')
    check("b9 fb=0", r['bbw_seq_from_blue_bars'].iloc[9] == 0)
    check("b9 fr=1", r['bbw_seq_from_red_bars'].iloc[9] == 1)  # idx9 - idx8

    # ── Bar 10: green. prev=blue, expanding, no skip ──
    # |1-0|=1 -> no skip
    # transitions = ['Y','R','B','G'][-3:] = ['R','B','G'] -> 'RBG'
    check("b10 prev=blue", r['bbw_seq_prev_color'].iloc[10] == 'blue')
    check("b10 dir=expanding", r['bbw_seq_direction'].iloc[10] == 'expanding')
    check("b10 skip=False", r['bbw_seq_skip_detected'].iloc[10] == False)
    check("b10 pid='RBG'", r['bbw_seq_pattern_id'].iloc[10] == 'RBG')
    check("b10 fb=1", r['bbw_seq_from_blue_bars'].iloc[10] == 1)  # idx10 - idx9
    check("b10 fr=2", r['bbw_seq_from_red_bars'].iloc[10] == 2)   # idx10 - idx8

    # ── Bar 11: green again. bic=2, flat ──
    check("b11 bic=2", r['bbw_seq_bars_in_color'].iloc[11] == 2)
    check("b11 dir=flat", r['bbw_seq_direction'].iloc[11] == 'flat')
    check("b11 fb=2", r['bbw_seq_from_blue_bars'].iloc[11] == 2)  # idx11 - idx9
    check("b11 fr=3", r['bbw_seq_from_red_bars'].iloc[11] == 3)   # idx11 - idx8


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: State counter independence from color counter
# ═══════════════════════════════════════════════════════════════════════════════

def debug_state_counter_independence():
    """State changes independently of color — verify separate counters."""
    print("\n[Debug 3] State Counter Independence")

    # Same color (blue) but alternating states
    spectrums = ['blue', 'blue', 'blue', 'blue']
    states =    ['BLUE_DOUBLE', 'BLUE', 'BLUE', 'BLUE_DOUBLE']
    df = make_df(spectrums, states)
    r = track_bbw_sequence(df)

    # Color counter: 1, 2, 3, 4 (never resets, same color)
    bic = r['bbw_seq_bars_in_color'].tolist()
    check("color 1,2,3,4", bic == [1, 2, 3, 4])

    # State counter: resets on state change
    # bar0: BLUE_DOUBLE (first) -> 1
    # bar1: BLUE (changed) -> 1
    # bar2: BLUE (same) -> 2
    # bar3: BLUE_DOUBLE (changed) -> 1
    bis = r['bbw_seq_bars_in_state'].tolist()
    check("state 1,1,2,1", bis == [1, 1, 2, 1])


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: All-same-color edge case
# ═══════════════════════════════════════════════════════════════════════════════

def debug_all_same_color():
    """Every bar same color — direction always flat, pattern = single letter."""
    print("\n[Debug 4] All Same Color Edge Case")

    spectrums = ['green'] * 10
    df = make_df(spectrums)
    r = track_bbw_sequence(df)

    # All flat after first bar (first bar = None direction)
    dirs = r['bbw_seq_direction'].tolist()
    check("bar0 dir=None", dirs[0] is None)
    check("bars1-9 all flat", all(d == 'flat' for d in dirs[1:]))

    # Color changed always False
    check("never changed", r['bbw_seq_color_changed'].sum() == 0)

    # bars_in_color monotonic 1..10
    bic = r['bbw_seq_bars_in_color'].tolist()
    check("bic = 1..10", bic == list(range(1, 11)))

    # Pattern always 'G'
    pids = r['bbw_seq_pattern_id'].tolist()
    check("pattern always 'G'", all(p == 'G' for p in pids))

    # No skips
    check("no skips", r['bbw_seq_skip_detected'].sum() == 0)

    # from_blue always NaN (never saw blue)
    check("from_blue all NaN", r['bbw_seq_from_blue_bars'].isna().all())


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: None gaps mid-stream — counters pause and resume
# ═══════════════════════════════════════════════════════════════════════════════

def debug_none_gaps_midstream():
    """None bars in the middle should pause tracking, resume correctly."""
    print("\n[Debug 5] None Gaps Mid-Stream")

    # blue, blue, None, None, blue, green
    spectrums = ['blue', 'blue', None, None, 'blue', 'green']
    df = make_df(spectrums)
    r = track_bbw_sequence(df)

    # Bar 0-1: blue, bic=1,2
    check("b0 bic=1", r['bbw_seq_bars_in_color'].iloc[0] == 1)
    check("b1 bic=2", r['bbw_seq_bars_in_color'].iloc[1] == 2)

    # Bar 2-3: None, defaults
    check("b2 bic=0", r['bbw_seq_bars_in_color'].iloc[2] == 0)
    check("b3 bic=0", r['bbw_seq_bars_in_color'].iloc[3] == 0)
    check("b2 dir=None", r['bbw_seq_direction'].iloc[2] is None)

    # Bar 4: blue again. Last tracked color was blue, so same color -> no change
    # bic should continue? No — the counter was reset by the None gap.
    # Actually: last_color is still 'blue' from bar 1. Bar 4 = blue.
    # Same color -> bic increments from current_color_count.
    # current_color_count was 2 at bar 1. None bars don't reset it.
    # So bar 4: same color -> current_color_count = 3
    check("b4 prev=blue", r['bbw_seq_prev_color'].iloc[4] == 'blue')
    check("b4 changed=False", r['bbw_seq_color_changed'].iloc[4] == False)
    check("b4 bic=3", r['bbw_seq_bars_in_color'].iloc[4] == 3)
    check("b4 dir=flat", r['bbw_seq_direction'].iloc[4] == 'flat')

    # Bar 5: green. prev=blue, changed, expanding
    check("b5 prev=blue", r['bbw_seq_prev_color'].iloc[5] == 'blue')
    check("b5 changed=True", r['bbw_seq_color_changed'].iloc[5] == True)
    check("b5 bic=1", r['bbw_seq_bars_in_color'].iloc[5] == 1)
    check("b5 dir=expanding", r['bbw_seq_direction'].iloc[5] == 'expanding')

    # from_blue distances account for index, not just valid bars
    # last_blue_idx was set to 4 (bar 4 is blue)
    check("b4 fb=0", r['bbw_seq_from_blue_bars'].iloc[4] == 0)
    check("b5 fb=1", r['bbw_seq_from_blue_bars'].iloc[5] == 1)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Cross-validate Layer 1 + Layer 2 on real data
# ═══════════════════════════════════════════════════════════════════════════════

def debug_cross_validate_real():
    """Run real data, verify Layer 2 outputs are consistent with Layer 1."""
    print("\n[Debug 6] Cross-Validate Real Data")

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

    df_l1 = calculate_bbwp(df_5m)
    result = track_bbw_sequence(df_l1)

    valid = result[result['bbwp_spectrum'].notna()]

    # 1. Every color_changed=True bar must have prev_color != current color
    changed = valid[valid['bbw_seq_color_changed'] == True]
    if len(changed) > 0:
        mismatch = changed[changed['bbw_seq_prev_color'] == changed['bbwp_spectrum']]
        check("changed bars have different prev/curr color",
              len(mismatch) == 0, f"{len(mismatch)} mismatches")

    # 2. Every color_changed=False bar (except first valid) must have prev == curr
    not_changed = valid[valid['bbw_seq_color_changed'] == False]
    # Exclude bars where prev is None (first valid bar)
    not_changed_with_prev = not_changed[not_changed['bbw_seq_prev_color'].notna()]
    if len(not_changed_with_prev) > 0:
        mismatch2 = not_changed_with_prev[
            not_changed_with_prev['bbw_seq_prev_color'] != not_changed_with_prev['bbwp_spectrum']
        ]
        check("unchanged bars have same prev/curr color",
              len(mismatch2) == 0, f"{len(mismatch2)} mismatches")

    # 3. bars_in_color resets to 1 on every color change
    changed_bic = changed['bbw_seq_bars_in_color']
    if len(changed_bic) > 0:
        check("bic=1 on every color change",
              (changed_bic == 1).all(), f"non-1 count: {(changed_bic != 1).sum()}")

    # 4. from_blue_bars = 0 on every blue bar
    blue_bars = valid[valid['bbwp_spectrum'] == 'blue']
    if len(blue_bars) > 0:
        check("from_blue=0 on blue bars",
              (blue_bars['bbw_seq_from_blue_bars'] == 0).all())

    # 5. from_red_bars = 0 on every red bar
    red_bars = valid[valid['bbwp_spectrum'] == 'red']
    if len(red_bars) > 0:
        check("from_red=0 on red bars",
              (red_bars['bbw_seq_from_red_bars'] == 0).all())

    # 6. direction on flat bars must be 'flat'
    flat_bars = valid[(valid['bbw_seq_color_changed'] == False) & (valid['bbw_seq_prev_color'].notna())]
    if len(flat_bars) > 0:
        check("unchanged bars direction=flat",
              (flat_bars['bbw_seq_direction'] == 'flat').all(),
              f"non-flat: {flat_bars['bbw_seq_direction'].value_counts().to_dict()}")

    # 7. skip detected only on changed bars
    skip_on_unchanged = valid[
        (valid['bbw_seq_skip_detected'] == True) & (valid['bbw_seq_color_changed'] == False)
    ]
    check("skip only on changed bars", len(skip_on_unchanged) == 0,
          f"found {len(skip_on_unchanged)} skip-on-unchanged")

    # 8. pattern_id length always 1-3 for valid bars
    pid_lens = valid['bbw_seq_pattern_id'].str.len()
    check("pattern_id len 1-3", (pid_lens >= 1).all() and (pid_lens <= 3).all(),
          f"min={pid_lens.min()}, max={pid_lens.max()}")

    # 9. pattern_id only contains valid letters
    valid_letters = set('BGYR')
    all_letters = set(''.join(valid['bbw_seq_pattern_id'].values))
    check("pattern_id only BGYR", all_letters.issubset(valid_letters),
          f"found: {all_letters}")

    # 10. from_blue/red monotonically increase between same-color bars
    # (They should increment by 1 on consecutive non-blue bars)
    # Just check they never decrease except when reset to 0
    fb = valid['bbw_seq_from_blue_bars'].values
    for i in range(1, len(fb)):
        if not np.isnan(fb[i]) and not np.isnan(fb[i-1]):
            if fb[i] != 0:  # not a reset
                if fb[i] < fb[i-1]:
                    check(f"from_blue monotonic at {i}", False,
                          f"prev={fb[i-1]}, curr={fb[i]}")
                    break
    else:
        check("from_blue monotonic (no decrease except reset)", True)

    print(f"\n  Validated {len(valid):,} bars")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: Constants integrity
# ═══════════════════════════════════════════════════════════════════════════════

def debug_constants():
    """Verify COLOR_ORDER, COLOR_LETTERS, VALID_COLORS consistency."""
    print("\n[Debug 7] Constants Integrity")

    check("4 colors in ORDER", len(COLOR_ORDER) == 4)
    check("4 letters in LETTERS", len(COLOR_LETTERS) == 4)
    check("VALID_COLORS matches ORDER keys", VALID_COLORS == set(COLOR_ORDER.keys()))
    check("ORDER monotonic", list(COLOR_ORDER.values()) == [0, 1, 2, 3])
    check("blue=0", COLOR_ORDER['blue'] == 0)
    check("green=1", COLOR_ORDER['green'] == 1)
    check("yellow=2", COLOR_ORDER['yellow'] == 2)
    check("red=3", COLOR_ORDER['red'] == 3)
    check("B for blue", COLOR_LETTERS['blue'] == 'B')
    check("G for green", COLOR_LETTERS['green'] == 'G')
    check("Y for yellow", COLOR_LETTERS['yellow'] == 'Y')
    check("R for red", COLOR_LETTERS['red'] == 'R')
    check("no orange in VALID_COLORS", 'orange' not in VALID_COLORS)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run all debug sections."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{'='*70}")
    print(f"BBW Sequence Layer 2 Debug & Math Validator -- {ts}")
    print(f"{'='*70}")

    debug_helper_functions()
    debug_full_pipeline_vector()
    debug_state_counter_independence()
    debug_all_same_color()
    debug_none_gaps_midstream()
    debug_cross_validate_real()
    debug_constants()

    print(f"\n{'='*70}")
    print(f"DEBUG RESULTS: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL")
    if ERRORS:
        print(f"FAILURES: {', '.join(ERRORS)}")
    print(f"{'='*70}")

    return FAIL_COUNT


if __name__ == "__main__":
    sys.exit(main())
''', encoding='utf-8')
print("  OK    scripts/debug_bbw_sequence.py")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: Run all three
# ═══════════════════════════════════════════════════════════════════════════════

def run_script(label, script_path):
    """Run a Python script, print output, return stdout."""
    print(f"\n{'='*70}")
    print(f"Running {label} ...")
    print(f"{'='*70}\n")
    r = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=120
    )
    print(r.stdout)
    if r.stderr:
        print(f"STDERR:\n{r.stderr}")
    return r.stdout

test_out = run_script("tests/test_bbw_sequence.py", TESTS / "test_bbw_sequence.py")
sanity_out = run_script("scripts/sanity_check_bbw_sequence.py", SCRIPTS / "sanity_check_bbw_sequence.py")
debug_out = run_script("scripts/debug_bbw_sequence.py", SCRIPTS / "debug_bbw_sequence.py")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 6: Write log
# ═══════════════════════════════════════════════════════════════════════════════

LOG_DIR = VAULT / "06-CLAUDE-LOGS"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "2026-02-14-bbw-layer2-build.md"

log_content = f"""# Layer 2 Build Log — BBW Sequence Tracker

## Build started: {ts}

### Files Created
1. `signals/bbw_sequence.py` — sequence tracking module (9 output columns)
2. `tests/test_bbw_sequence.py` — 10 tests, 40+ assertions
3. `scripts/sanity_check_bbw_sequence.py` — RIVERUSDT distribution stats
4. `scripts/debug_bbw_sequence.py` — math/logic validator (7 sections, 100+ checks)

---

### Test output ({ts})
```
{test_out}
```

### Sanity check output ({ts})
```
{sanity_out}
```

### Debug validator output ({ts})
```
{debug_out}
```
"""

if LOG_FILE.exists():
    print(f"\n  WARN  Log file already exists, appending")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n## Re-run: {ts}\n{log_content}")
else:
    LOG_FILE.write_text(log_content, encoding="utf-8")
    print(f"\n  OK    Created {LOG_FILE.name}")

print(f"\n{'='*70}")
print(f"LAYER 2 BUILD COMPLETE -- {ts}")
print(f"{'='*70}")
