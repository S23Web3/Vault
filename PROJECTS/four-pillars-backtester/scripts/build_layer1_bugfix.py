"""
Build script: Layer 1 BBWP Bugfix (6 bugs + 4 test changes).

Applies targeted edits to:
  - signals/bbwp.py (6 bug fixes)
  - tests/test_bbwp.py (3 test rewrites + 1 new test)
  - scripts/sanity_check_bbwp.py (spectrum list 5->4)
  - 06-CLAUDE-LOGS/2026-02-14-layer1-bugfix.md (new log)

Then runs tests/test_bbwp.py and scripts/sanity_check_bbwp.py.

Run: python scripts/build_layer1_bugfix.py
"""

import sys
import os
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT.parent.parent  # Obsidian Vault root

ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print(f"{'='*70}")
print(f"Layer 1 Bugfix Build Script -- {ts}")
print(f"{'='*70}")

# ─── Safety: backup originals ────────────────────────────────────────────────

TARGETS = [
    ROOT / "signals" / "bbwp.py",
    ROOT / "tests" / "test_bbwp.py",
    ROOT / "scripts" / "sanity_check_bbwp.py",
]

for f in TARGETS:
    if not f.exists():
        print(f"FATAL: {f} not found")
        sys.exit(1)
    bak = f.with_suffix(f.suffix + ".pre_bugfix_bak")
    if not bak.exists():
        shutil.copy2(f, bak)
        print(f"  Backed up: {f.name} -> {bak.name}")
    else:
        print(f"  Backup exists: {bak.name} (skipping)")


def apply_edit(filepath, old_text, new_text, label=""):
    """Apply a single text replacement to a file. Fails if old_text not found."""
    content = filepath.read_text(encoding="utf-8")
    if old_text not in content:
        print(f"  FAIL  [{label}] old_text not found in {filepath.name}")
        print(f"         First 80 chars of old_text: {old_text[:80]!r}")
        return False
    count = content.count(old_text)
    if count > 1:
        print(f"  WARN  [{label}] old_text found {count} times in {filepath.name}, replacing first only")
    content = content.replace(old_text, new_text, 1)
    filepath.write_text(content, encoding="utf-8")
    print(f"  OK    [{label}] {filepath.name}")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1: signals/bbwp.py — 6 bug fixes
# ═══════════════════════════════════════════════════════════════════════════════

BBWP = ROOT / "signals" / "bbwp.py"
print(f"\n--- Patching {BBWP.name} ---")

# ── FIX 1+6: _spectrum_color rewrite (NaN->None, 4 colors at 25/50/75) ──────

apply_edit(BBWP,
    old_text='''def _spectrum_color(bbwp_val: float) -> str:
    """Map BBWP value to 5-tier spectrum color.

    Boundaries: <=20 blue, <=40 green, <=60 yellow, <=80 orange, >80 red.
    These are display boundaries, NOT the state detection thresholds (25/75).
    """
    if np.isnan(bbwp_val):
        return 'yellow'
    if bbwp_val <= 20:
        return 'blue'
    elif bbwp_val <= 40:
        return 'green'
    elif bbwp_val <= 60:
        return 'yellow'
    elif bbwp_val <= 80:
        return 'orange'
    else:
        return 'red\'''',
    new_text='''def _spectrum_color(bbwp_val: float):
    """Map BBWP value to 4-zone spectrum color (Pine gradient inflection at 25/50/75)."""
    if np.isnan(bbwp_val):
        return None
    if bbwp_val <= 25:
        return 'blue'
    elif bbwp_val <= 50:
        return 'green'
    elif bbwp_val <= 75:
        return 'yellow'
    else:
        return 'red\'''',
    label="BUG 1+6: _spectrum_color rewrite")

# ── FIX 7: _detect_states warmup gap — split NaN check ──────────────────────

# Part A: Replace the NaN guard block (lines 156-160)
apply_edit(BBWP,
    old_text='''        # Handle NaN bars — default to NORMAL, 0 points
        if np.isnan(bbwp) or np.isnan(bbwp_ma):
            states[i] = 'NORMAL'
            points[i] = 0
            continue''',
    new_text='''        # Handle NaN bbwp — default to NORMAL, 0 points
        if np.isnan(bbwp):
            states[i] = 'NORMAL'
            points[i] = 0
            continue

        # MA may still be NaN during warmup gap (bars with valid bbwp but NaN MA)
        ma_is_nan = np.isnan(bbwp_ma)''',
    label="BUG 7a: split NaN check")

# Part B: Guard crossover detection with ma_is_nan check (line 176)
apply_edit(BBWP,
    old_text='''        if i > 0 and in_normal_range:''',
    new_text='''        if i > 0 and in_normal_range and not ma_is_nan:''',
    label="BUG 7b: crossover guard")

# ── FIX 8: _percentrank_pine NaN fragility ───────────────────────────────────

apply_edit(BBWP,
    old_text='''def _percentrank_pine(bbw: pd.Series, lookback: int) -> pd.Series:
    """Match Pine's ta.percentrank(source, length) exactly.

    Pine ta.percentrank counts how many of the PREVIOUS `length` values
    (NOT including current bar) are strictly less than current value,
    divides by `length`, multiplies by 100.
    """
    values = bbw.values
    n = len(values)
    result = np.full(n, np.nan)

    for i in range(lookback, n):
        if np.isnan(values[i]):
            continue
        # Previous lookback values (NOT including current bar)
        prev_window = values[i - lookback:i]
        if np.any(np.isnan(prev_window)):
            continue
        current = values[i]
        count_below = np.sum(prev_window < current)
        result[i] = (count_below / lookback) * 100

    return pd.Series(result, index=bbw.index)''',
    new_text='''def _percentrank_pine(bbw: pd.Series, lookback: int) -> pd.Series:
    """Match Pine's ta.percentrank with NaN-tolerant window (min lookback//2 valid)."""
    values = bbw.values
    n = len(values)
    result = np.full(n, np.nan)
    min_valid = max(lookback // 2, 1)

    for i in range(lookback, n):
        if np.isnan(values[i]):
            continue
        # Previous lookback values (NOT including current bar)
        prev_window = values[i - lookback:i]
        valid_mask = ~np.isnan(prev_window)
        valid_count = valid_mask.sum()
        if valid_count < min_valid:
            continue
        current = values[i]
        count_below = np.sum(prev_window[valid_mask] < current)
        result[i] = (count_below / valid_count) * 100

    return pd.Series(result, index=bbw.index)''',
    label="BUG 8: _percentrank_pine NaN tolerance")

# ── FIX 5: VWMA silent fallback — add warning ────────────────────────────────

apply_edit(BBWP,
    old_text="import numpy as np\nimport pandas as pd",
    new_text="import warnings\n\nimport numpy as np\nimport pandas as pd",
    label="BUG 5a: add warnings import")

apply_edit(BBWP,
    old_text='''    elif ma_type == 'VWMA':
        # Fallback to SMA if no volume context available
        return series.rolling(length).mean()''',
    new_text='''    elif ma_type == 'VWMA':
        # Fallback to SMA if no volume context available
        warnings.warn("VWMA requested but no volume data available, falling back to SMA", stacklevel=2)
        return series.rolling(length).mean()''',
    label="BUG 5b: VWMA warning")

# ── FIX 2: Dead NaN override code — remove redundant lines ──────────────────

apply_edit(BBWP,
    old_text='''    # NaN comparisons produce False, which is correct behavior
    # But explicitly handle NaN: set to False
    result.loc[bbwp.isna(), 'bbwp_is_blue_bar'] = False
    result.loc[bbwp.isna(), 'bbwp_is_red_bar'] = False''',
    new_text='''    # NaN comparisons already produce False — no explicit override needed''',
    label="BUG 2: remove dead NaN override")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 2: tests/test_bbwp.py — 3 rewrites + 1 new test
# ═══════════════════════════════════════════════════════════════════════════════

TESTS = ROOT / "tests" / "test_bbwp.py"
print(f"\n--- Patching {TESTS.name} ---")

# ── Test 3: Spectrum boundaries (4 colors, <=25 blue, >75 red, NaN->None) ───

apply_edit(TESTS,
    old_text='''def test_spectrum_color_boundaries():
    """Verify 20/40/60/80 boundaries produce correct colors."""
    print("\\n[Test 3] Spectrum Color Boundaries")

    # We test the spectrum assignment by crafting BBWP values at boundaries
    # Spectrum: <=20 blue, <=40 green, <=60 yellow, <=80 orange, >80 red
    test_cases = [
        (0, 'blue'), (10, 'blue'), (20, 'blue'),
        (21, 'green'), (30, 'green'), (40, 'green'),
        (41, 'yellow'), (50, 'yellow'), (60, 'yellow'),
        (61, 'orange'), (70, 'orange'), (80, 'orange'),
        (81, 'red'), (90, 'red'), (100, 'red'),
    ]

    # Build data that produces known BBWP values is hard, so instead
    # test the internal spectrum function indirectly by checking that
    # the spectrum column contains only valid values
    closes = np.random.RandomState(42).normal(100, 5, 300).tolist()
    df = make_df(closes, n=300)
    result = calculate_bbwp(df)

    valid_colors = {'blue', 'green', 'yellow', 'orange', 'red'}
    spectrums = result['bbwp_spectrum'].dropna().unique()
    check("all spectrums valid", set(spectrums).issubset(valid_colors),
          f"got: {set(spectrums)}")

    # Check boundary logic: rows with bbwp_value <= 20 should be 'blue'
    valid_rows = result.dropna(subset=['bbwp_value'])
    if len(valid_rows) > 0:
        blue_rows = valid_rows[valid_rows['bbwp_value'] <= 20]
        if len(blue_rows) > 0:
            check("bbwp<=20 -> blue", (blue_rows['bbwp_spectrum'] == 'blue').all(),
                  f"non-blue count: {(blue_rows['bbwp_spectrum'] != 'blue').sum()}")
        else:
            check("bbwp<=20 -> blue", True, "no rows <= 20 (OK for random data)")

        red_rows = valid_rows[valid_rows['bbwp_value'] > 80]
        if len(red_rows) > 0:
            check("bbwp>80 -> red", (red_rows['bbwp_spectrum'] == 'red').all(),
                  f"non-red count: {(red_rows['bbwp_spectrum'] != 'red').sum()}")
        else:
            check("bbwp>80 -> red", True, "no rows > 80 (OK for random data)")''',
    new_text='''def test_spectrum_color_boundaries():
    """Verify 25/50/75 boundaries produce correct 4-zone colors; NaN -> None."""
    print("\\n[Test 3] Spectrum Color Boundaries")

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
            check("bbwp>75 -> red", True, "no rows > 75 (OK for random data)")''',
    label="Test 3: spectrum 4-zone boundaries")

# ── Test 5: Deterministic MA cross persistence ──────────────────────────────

apply_edit(TESTS,
    old_text='''def test_ma_cross_persistence():
    """Cross fires, persists for N bars, auto-resets on timeout."""
    print("\\n[Test 5] MA Cross Persistence")

    # Create data where BBWP stays in normal range (25-75) and crosses above MA
    # then verify MA_CROSS_UP persists for up to timeout bars
    closes = np.random.RandomState(77).normal(100, 3, 400).tolist()
    df = make_df(closes, n=400)
    result = calculate_bbwp(df, {'ma_cross_timeout': 10})

    ma_cross_up_states = result[result['bbwp_state'] == 'MA_CROSS_UP']
    ma_cross_down_states = result[result['bbwp_state'] == 'MA_CROSS_DOWN']

    # If any MA_CROSS_UP states exist, check they appear in runs <= timeout
    if len(ma_cross_up_states) > 0:
        # Find consecutive runs of MA_CROSS_UP
        is_cross_up = (result['bbwp_state'] == 'MA_CROSS_UP').astype(int)
        runs = is_cross_up.diff().fillna(0)
        run_starts = runs[runs == 1].index.tolist()
        run_ends = runs[runs == -1].index.tolist()

        if len(run_ends) < len(run_starts):
            run_ends.append(len(result))

        max_run = 0
        for s, e in zip(run_starts, run_ends):
            run_len = e - s
            max_run = max(max_run, run_len)

        check("MA_CROSS_UP run <= timeout",
              max_run <= 10,
              f"max run length: {max_run}")
    else:
        check("MA_CROSS_UP run <= timeout", True,
              "no MA_CROSS_UP states found (OK for this data)")

    # Check that MA cross events (single bar) are sparse
    cross_up_events = result['bbwp_ma_cross_up'].sum()
    cross_down_events = result['bbwp_ma_cross_down'].sum()
    total_bars = len(result.dropna(subset=['bbwp_value']))
    check("cross events sparse",
          (cross_up_events + cross_down_events) < total_bars * 0.15,
          f"up={cross_up_events}, down={cross_down_events}, total_valid={total_bars}")''',
    new_text='''def test_ma_cross_persistence():
    """Cross fires, persists for N bars, auto-resets on timeout (deterministic)."""
    print("\\n[Test 5] MA Cross Persistence")

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
          f"up={cross_up_events}, down={cross_down_events}, total_valid={total_bars}")''',
    label="Test 5: deterministic persistence")

# ── Test 7: Sequential mutual exclusion (real checks, not tautology) ─────────

apply_edit(TESTS,
    old_text='''def test_ma_cross_up_cancels_down():
    """New cross up cancels active cross down state."""
    print("\\n[Test 7] MA Cross Up Cancels Down")

    # Structural check: showMaCrossUp and showMaCrossDown should never both be True
    # We can verify this by checking that MA_CROSS_UP and MA_CROSS_DOWN never appear
    # on the same bar (which is impossible by the priority chain anyway)
    closes = np.random.RandomState(33).normal(100, 5, 400).tolist()
    df = make_df(closes, n=400)
    result = calculate_bbwp(df)

    # A row is either MA_CROSS_UP or MA_CROSS_DOWN, never both
    both = result[
        (result['bbwp_state'] == 'MA_CROSS_UP') &
        (result['bbwp_state'] == 'MA_CROSS_DOWN')
    ]
    check("never both MA_CROSS_UP and MA_CROSS_DOWN", len(both) == 0)

    # Also verify: cross_up event and cross_down event never on same bar
    both_events = result[
        (result['bbwp_ma_cross_up'] == True) &
        (result['bbwp_ma_cross_down'] == True)
    ]
    check("never both cross events on same bar", len(both_events) == 0)''',
    new_text='''def test_ma_cross_up_cancels_down():
    """Cross_up event bar must have MA_CROSS_UP state (not DOWN); at least 1 tested."""
    print("\\n[Test 7] MA Cross Up Cancels Down")

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
          f"tested {tested_count} cross event bars")''',
    label="Test 7: real mutual exclusion checks")

# ── NEW Test 12: Warmup gap consistency ──────────────────────────────────────

# Insert after test_on_real_parquet (before main)
apply_edit(TESTS,
    old_text='''# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    """Run all 11 BBWP tests."""''',
    new_text='''# ─── Test 12: Warmup Gap Consistency ─────────────────────────────────────────

def test_warmup_gap_consistency():
    """Bars with valid bbwp but NaN MA should still detect BLUE/BLUE_DOUBLE."""
    print("\\n[Test 12] Warmup Gap Consistency")

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
    """Run all 12 BBWP tests."""''',
    label="Test 12: warmup gap consistency")

# Add test_warmup_gap_consistency to main() call list
apply_edit(TESTS,
    old_text="    test_on_real_parquet()\n\n    print",
    new_text="    test_on_real_parquet()\n    test_warmup_gap_consistency()\n\n    print",
    label="Add test 12 to main()")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 3: scripts/sanity_check_bbwp.py — spectrum 5->4
# ═══════════════════════════════════════════════════════════════════════════════

SANITY = ROOT / "scripts" / "sanity_check_bbwp.py"
print(f"\n--- Patching {SANITY.name} ---")

apply_edit(SANITY,
    old_text="    for color in ['blue', 'green', 'yellow', 'orange', 'red']:",
    new_text="    for color in ['blue', 'green', 'yellow', 'red']:",
    label="Sanity: spectrum 5->4 colors")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 4: Create build log
# ═══════════════════════════════════════════════════════════════════════════════

LOG_DIR = VAULT / "06-CLAUDE-LOGS"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "2026-02-14-layer1-bugfix.md"

log_content = f"""# Layer 1 Bugfix Log

## Build started: {ts}

### Bugs Fixed
1. BUG 1+6: `_spectrum_color` rewrite -- NaN->None, 4 colors at 25/50/75 (drop orange)
2. BUG 7: `_detect_states` warmup gap -- split NaN check, bars with valid bbwp but NaN MA now detect states
3. BUG 8: `_percentrank_pine` NaN tolerance -- count valid values, min lookback//2
4. BUG 5: VWMA silent fallback -- added warnings.warn()
5. BUG 2: Dead NaN override -- removed redundant .loc[] assignments

### Tests Updated
- Test 3: Spectrum boundaries -> 4 colors, <=25 blue, >75 red, NaN->None
- Test 5: Deterministic MA cross persistence (crafted data, not random)
- Test 7: Real mutual exclusion checks (not tautology)
- Test 12 (NEW): Warmup gap consistency

### Sanity Check
- `scripts/sanity_check_bbwp.py` spectrum list: 5->4 colors

---

## Post-build results
"""

if LOG_FILE.exists():
    print(f"  WARN  Log file already exists, appending")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n## Re-run: {ts}\n")
else:
    LOG_FILE.write_text(log_content, encoding="utf-8")
    print(f"  OK    Created {LOG_FILE.name}")

# ═══════════════════════════════════════════════════════════════════════════════
# PART 5: Run tests
# ═══════════════════════════════════════════════════════════════════════════════

print(f"\n{'='*70}")
print("Running tests/test_bbwp.py ...")
print(f"{'='*70}\n")

import subprocess

test_result = subprocess.run(
    [sys.executable, str(ROOT / "tests" / "test_bbwp.py")],
    capture_output=True, text=True, cwd=str(ROOT), timeout=120
)
print(test_result.stdout)
if test_result.stderr:
    print(f"STDERR:\n{test_result.stderr}")

print(f"\n{'='*70}")
print("Running scripts/sanity_check_bbwp.py ...")
print(f"{'='*70}\n")

sanity_result = subprocess.run(
    [sys.executable, str(ROOT / "scripts" / "sanity_check_bbwp.py")],
    capture_output=True, text=True, cwd=str(ROOT), timeout=120
)
print(sanity_result.stdout)
if sanity_result.stderr:
    print(f"STDERR:\n{sanity_result.stderr}")

# Append results to log
combined_output = (
    f"### Test output ({ts})\n```\n{test_result.stdout}\n```\n\n"
    f"### Sanity check output ({ts})\n```\n{sanity_result.stdout}\n```\n"
)
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(combined_output)

print(f"\n{'='*70}")
print(f"BUILD COMPLETE -- results logged to {LOG_FILE.name}")
print(f"{'='*70}")
