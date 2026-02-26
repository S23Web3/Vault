# CLAUDE CODE PROMPT — Layer 1 Bugfix via Python Script

## CONTEXT

Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
Fixing 6 bugs in Layer 1 before building Layer 2.

## STRATEGY — TOKEN CONSERVATION

Do NOT apply edits interactively. Instead:
1. Read the 3 source files
2. Write ONE Python script: `scripts\apply_layer1_bugfix.py`
3. That script patches `signals\bbwp.py` and `tests\test_bbwp.py` using string replacement
4. Execute the script
5. Run tests
6. Run sanity check
7. Write log

Total Claude Code output: ~3 tool calls (write script, run script, run tests).

## MANDATORY: READ FIRST

1. `signals\bbwp.py`
2. `tests\test_bbwp.py`
3. `indicators\supporting\bbwp_v2.pine`

---

## SCRIPT: `scripts\apply_layer1_bugfix.py`

Write this script. It must:

### 1. Patch `signals\bbwp.py` using file read → string replace → file write

**Patch A — BUG 1+6 combined: `_spectrum_color` rewrite**

Find and replace the entire `_spectrum_color` function. Old:
```python
def _spectrum_color(bbwp_val: float) -> str:
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
        return 'red'
```

New:
```python
def _spectrum_color(bbwp_val: float) -> str:
    """Map BBWP value to 4-tier spectrum color matching Pine v2 gradient zones.

    Pine gradient inflection points: 25, 50, 75.
    Zone 1: 0-25   -> blue   (compressed)
    Zone 2: 25-50  -> green  (low-normal)
    Zone 3: 50-75  -> yellow (high-normal)
    Zone 4: 75-100 -> red    (expanded)
    Returns None for NaN input (warmup bars).
    """
    if np.isnan(bbwp_val):
        return None
    if bbwp_val <= 25:
        return 'blue'
    elif bbwp_val <= 50:
        return 'green'
    elif bbwp_val <= 75:
        return 'yellow'
    else:
        return 'red'
```

**Patch B — BUG 7: `_detect_states` NaN MA handling**

Find:
```python
        # Handle NaN bars — default to NORMAL, 0 points
        if np.isnan(bbwp) or np.isnan(bbwp_ma):
            states[i] = 'NORMAL'
            points[i] = 0
            continue
```

Replace with:
```python
        # Handle NaN bbwp — default to NORMAL, 0 points
        if np.isnan(bbwp):
            states[i] = 'NORMAL'
            points[i] = 0
            continue

        # If only MA is NaN, still detect bar/spectrum states but skip MA cross
        ma_is_nan = np.isnan(bbwp_ma)
```

Also find:
```python
        if i > 0 and in_normal_range:
```

Replace with:
```python
        if i > 0 and in_normal_range and not ma_is_nan:
```

**Patch C — BUG 8: `_percentrank_pine` NaN tolerance**

Find the entire `_percentrank_pine` function and replace with NaN-tolerant version:
```python
def _percentrank_pine(bbw: pd.Series, lookback: int) -> pd.Series:
    """Match Pine's ta.percentrank(source, length) with NaN tolerance.

    Pine ta.percentrank counts how many of the PREVIOUS `length` values
    (NOT including current bar) are strictly less than current value,
    divides by `length`, multiplies by 100.

    NaN tolerance: skip NaN values in window, use valid count as denominator.
    If fewer than lookback/2 valid values, return NaN (insufficient data).
    """
    values = bbw.values
    n = len(values)
    result = np.full(n, np.nan)
    min_valid = lookback // 2

    for i in range(lookback, n):
        if np.isnan(values[i]):
            continue
        prev_window = values[i - lookback:i]
        valid_mask = ~np.isnan(prev_window)
        valid_count = valid_mask.sum()
        if valid_count < min_valid:
            continue
        current = values[i]
        count_below = np.sum(prev_window[valid_mask] < current)
        result[i] = (count_below / valid_count) * 100

    return pd.Series(result, index=bbw.index)
```

**Patch D — BUG 5: VWMA warning**

Find:
```python
    elif ma_type == 'VWMA':
        # Fallback to SMA if no volume context available
        return series.rolling(length).mean()
```

Replace with:
```python
    elif ma_type == 'VWMA':
        import warnings
        warnings.warn("VWMA requested but no volume column available — falling back to SMA", stacklevel=2)
        return series.rolling(length).mean()
```

**Patch E — BUG 2: Remove dead code**

Find:
```python
    # NaN comparisons produce False, which is correct behavior
    # But explicitly handle NaN: set to False
    result.loc[bbwp.isna(), 'bbwp_is_blue_bar'] = False
    result.loc[bbwp.isna(), 'bbwp_is_red_bar'] = False
```

Replace with:
```python
    # NaN <= extreme_low evaluates to False in pandas — correct behavior, no override needed
```

### 2. Patch `tests\test_bbwp.py`

**Patch F — Test 3: spectrum boundaries**

Replace the entire `test_spectrum_color_boundaries` function with updated version using 25/50/75 boundaries, 4 valid colors (no orange), and NaN→None check.

**Patch G — Test 5: deterministic timeout**

Replace the entire `test_ma_cross_persistence` function with the deterministic version using crafted warmup+bump+flat data.

**Patch H — Test 7: sequential mutual exclusion**

Replace the entire `test_ma_cross_up_cancels_down` function with the version that checks sequential state transitions on cross_up events.

**Patch I — Test 12: warmup gap consistency**

Append `test_warmup_gap_consistency` function before `def main()`.
Add `test_warmup_gap_consistency()` call in `main()` after `test_on_real_parquet()`.

### 3. Script self-verification

After all patches, the script should:
- Print each patch applied with line count diff
- Verify both files still parse (`compile(source, filename, 'exec')`)
- Print "ALL PATCHES APPLIED" or error out

### 4. Script does NOT run tests — that's a separate step

---

## EXECUTION ORDER

1. Read 3 source files
2. Write `scripts\apply_layer1_bugfix.py` with all patches above
3. Run: `python scripts\apply_layer1_bugfix.py`
4. Run: `python tests\test_bbwp.py` — all must pass
5. Run: `python scripts\sanity_check_bbwp.py` — verify blue is now ≤25
6. Write log to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-layer1-bugfix.md`

## LOG LOCATION

`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-layer1-bugfix.md`

## DO NOT

- Do not apply edits interactively one by one
- Do not print full file contents to terminal
- Do not exceed 32K output tokens
- All paths must use backslashes and be inside the Obsidian Vault
