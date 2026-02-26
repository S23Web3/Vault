# CLAUDE CODE PROMPT — Layer 2 Build via Python Script

## CONTEXT

Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
Layer 1 bugfixes MUST be applied first (see `BUILDS\PROMPT-LAYER1-BUGFIX.md`).
Verify: `python tests\test_bbwp.py` must show 0 FAIL before proceeding.

## STRATEGY — TOKEN CONSERVATION

Do NOT write files interactively line-by-line. Instead:
1. Read `signals\bbwp.py` to confirm Layer 1 output columns
2. Read skill file: `C:\Users\User\Documents\Obsidian Vault\skills\python\python-trading-development-skill.md`
3. Write THREE Python files in one shot each (no iterating):
   - `signals\bbw_sequence.py`
   - `tests\test_bbw_sequence.py`
   - `scripts\sanity_check_bbw_sequence.py`
4. Run tests
5. Run sanity check
6. Write log

Total Claude Code output: ~6 tool calls (read skill, write 3 files, run tests, run sanity).

---

## SPEC: `signals\bbw_sequence.py`

### Function: `track_bbw_sequence(df: pd.DataFrame) -> pd.DataFrame`

Pure function. No side effects, no file I/O.
Requires Layer 1 columns: `bbwp_spectrum`, `bbwp_state`, `bbwp_value`.
Raises `ValueError` if missing.

### 9 output columns:
```
bbw_seq_prev_color     : str|None  — previous bar's spectrum color
bbw_seq_color_changed  : bool      — color transition this bar
bbw_seq_bars_in_color  : int       — consecutive bars at current spectrum color
bbw_seq_bars_in_state  : int       — consecutive bars in current bbwp_state
bbw_seq_direction      : str|None  — 'expanding'|'contracting'|'flat'|None
bbw_seq_skip_detected  : bool      — color skipped a step
bbw_seq_pattern_id     : str       — last 3 color transitions (e.g., 'BGY')
bbw_seq_from_blue_bars : int|NaN   — bars since last blue spectrum
bbw_seq_from_red_bars  : int|NaN   — bars since last red spectrum
```

### Constants (4 colors matching Pine v2):
```python
COLOR_ORDER = {'blue': 0, 'green': 1, 'yellow': 2, 'red': 3}
COLOR_LETTERS = {'blue': 'B', 'green': 'G', 'yellow': 'Y', 'red': 'R'}
VALID_COLORS = set(COLOR_ORDER.keys())
```

### NaN/None handling:
- After Layer 1 bugfix, NaN bbwp bars have `bbwp_spectrum = None`
- Skip None spectrum bars entirely (don't count, don't track)
- Begin tracking from FIRST bar where `bbwp_spectrum is not None`
- All bbw_seq_ columns default to NaN/None/False/0 for None-spectrum bars

### Helpers:
```python
def _sequence_direction(prev_color, curr_color):
    if prev_color == curr_color: return 'flat'
    return 'expanding' if COLOR_ORDER[curr_color] > COLOR_ORDER[prev_color] else 'contracting'

def _is_skip(prev_color, curr_color):
    return abs(COLOR_ORDER[curr_color] - COLOR_ORDER[prev_color]) > 1
```

### Main loop logic:
- Iterate bar-by-bar (stateful tracking)
- Track: last_color, last_state, current_color_count, current_state_count, last_blue_bar, last_red_bar, recent_transitions (max 3)
- On color change: set direction, check skip, reset color count, append to transitions
- On same color: direction='flat', increment count
- Pattern ID = ''.join(recent_transitions[-3:])
- from_blue_bars = current_index - last_blue_bar (NaN if never seen blue)
- from_red_bars = current_index - last_red_bar (NaN if never seen red)

### Edge cases:
1. All bars same color → pattern = single letter, direction always 'flat'
2. blue→yellow = skip (missed green)
3. from_blue_bars on a blue bar = 0
4. from_blue_bars if never seen blue = NaN
5. None spectrum bars pause counters, resume on next valid bar

---

## SPEC: `tests\test_bbw_sequence.py`

10 tests, 40+ assertions. Use synthetic data via helper:

```python
def make_sequence_df(spectrums, states=None):
    n = len(spectrums)
    if states is None: states = ['NORMAL'] * n
    value_map = {'blue': 15, 'green': 37, 'yellow': 62, 'red': 87, None: np.nan}
    values = [value_map.get(s, np.nan) for s in spectrums]
    return pd.DataFrame({'bbwp_spectrum': spectrums, 'bbwp_state': states, 'bbwp_value': values})
```

### Tests:
1. Output columns — 9 bbw_seq_ columns present, correct dtypes
2. Missing Layer 1 columns — raises ValueError
3. NaN spectrum skipped — warmup bars get defaults, first valid bar starts tracking
4. Color transitions — `[None]*5 + ['blue','blue','green','green','green','yellow','red']`
5. Bars in color — monotonic within same color, resets on change
6. Direction — expanding/contracting/flat on known transitions
7. Skip detection — blue→yellow=True, blue→green=False, blue→red=True, red→blue=True
8. Pattern ID — `['blue','green','yellow','red']` → B, BG, BGY, GYR
9. From blue/red bars — correct distances, 0 on blue bar, NaN if never seen
10. Real parquet — RIVERUSDT 5m via Layer 1 + Layer 2, distribution checks

### Test 10 checks:
- bars_in_color mean > 1
- color_changed pct < 50%
- skip_detected pct < 20%
- pattern_id has multiple unique values
- from_blue_bars min = 0
- from_red_bars min = 0

---

## SPEC: `scripts\sanity_check_bbw_sequence.py`

Load RIVERUSDT 5m → Layer 1 → Layer 2 → print summary stats.
If output too large, write to `results\bbw_sequence_sanity.csv`.

Print:
- Color transition frequency
- Top 10 pattern_id by count
- Skip detection rate
- Direction distribution (expanding/contracting/flat)
- bars_in_color: mean, median, max per color
- bars_in_state: mean, median, max per state
- from_blue_bars: mean, P50, P90
- from_red_bars: mean, P50, P90
- Performance: bars/sec

---

## EXECUTION ORDER

1. Read skill file + `signals\bbwp.py`
2. Verify: `python tests\test_bbwp.py` → 0 FAIL
3. Write `signals\bbw_sequence.py` in one shot
4. Write `tests\test_bbw_sequence.py` in one shot
5. Run: `python tests\test_bbw_sequence.py` → all must pass
6. Write `scripts\sanity_check_bbw_sequence.py` in one shot
7. Run: `python scripts\sanity_check_bbw_sequence.py`
8. Write log

## LOG LOCATION

`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-bbw-layer2-build.md`

## DO NOT

- Do not rewrite `signals\bbwp.py`
- Do not print full DataFrames
- Do not run on all 399 coins
- Do not exceed 32K output tokens
- Do not apply edits interactively — write complete files in one shot each
- All paths must use backslashes and be inside the Obsidian Vault
