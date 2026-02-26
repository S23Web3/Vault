"""
Debug & Math Validator for Layer 2 BBW Sequence Tracker.

Crafted test vectors with hand-computed expected values.
Every assertion has a comment explaining the math.
Catches off-by-one, wrong direction, broken counters, NaN leaks.

Run: python scripts/debug_bbw_sequence.py
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
