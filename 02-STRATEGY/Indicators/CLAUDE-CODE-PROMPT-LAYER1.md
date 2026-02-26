# CLAUDE CODE PROMPT — Layer 1: signals/bbwp.py

## CONTEXT — READ FIRST, BUILD SECOND

You are building Layer 1 of a 7-layer BBW Simulator pipeline. This is a Python backtesting/research engine for cryptocurrency scalping on perpetual futures (5m timeframe, 399 coins cached as parquet in data/cache/).

**Project root:** C:\Users\User\four-pillars-backtester\

### What the full system does
The BBW Simulator answers: "Given the BBW volatility state at any bar, what Leverage, Size, and Grid/Target (LSG) parameters maximize risk-adjusted returns?"

### Full pipeline (you are building Layer 1 only)
```
Layer 1: signals/bbwp.py          ← THIS BUILD
Layer 2: signals/bbw_sequence.py  — color transitions, skip detection
Layer 3: research/bbw_forward_returns.py — tag bars with future returns
Layer 4: research/bbw_simulator.py — 10,752-combo LSG grid search
Layer 4b: research/bbw_monte_carlo.py — 1000x shuffle validation
Layer 5: research/bbw_report.py — aggregate CSVs
Layer 6: research/bbw_ollama_review.py — local LLM analysis via Ollama
```

Layer 1 is the FOUNDATION. Every downstream layer depends on its output columns being correct. It gets reused in both the simulator (research, run once) and the live pipeline (signals/four_pillars.py, runs every bar).

---

## MANDATORY: READ THESE SKILL FILES FIRST

Before writing ANY code:
1. Read `C:\Users\User\Documents\Obsidian Vault\skills\python\python-trading-development.md`
2. Read the Pine Script source: `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\bbwp_v2.pine`
3. Read the architecture: `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md` (Layer 1 section)
4. Read the research doc: `C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\BBW-STATISTICS-RESEARCH.md` (VINCE features section)

---

## WHAT TO BUILD

**File:** `signals/bbwp.py`

### Function signature
```python
def calculate_bbwp(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Port of bbwp_v2.pine to Python.
    
    Input: DataFrame with columns: open, high, low, close, base_vol
    Output: Same DataFrame with 10 new bbwp_ columns added
    
    This is a PURE FUNCTION — no side effects, no file I/O.
    """
```

### Parameters (with defaults matching Pine v2)
```python
DEFAULT_PARAMS = {
    'basis_len': 13,
    'basis_type': 'SMA',
    'lookback': 100,
    'bbwp_ma_len': 5,
    'bbwp_ma_type': 'SMA',
    'extreme_low': 10,
    'extreme_high': 90,
    'spectrum_low': 25,
    'spectrum_high': 75,
    'ma_cross_timeout': 10,
}
```

### Output columns (10 total, all prefixed bbwp_)
```
bbwp_value         : float (0-100)   — percentile rank of BB width
bbwp_ma            : float           — MA of BBWP
bbwp_bbw_raw       : float           — raw BB width (debug)
bbwp_spectrum      : str             — 'blue'|'green'|'yellow'|'orange'|'red'
bbwp_state         : str             — 'BLUE_DOUBLE'|'BLUE'|'MA_CROSS_UP'|'MA_CROSS_DOWN'|'NORMAL'|'RED'|'RED_DOUBLE'
bbwp_points        : int (0-2)       — Four Pillars grade points
bbwp_is_blue_bar   : bool            — BBWP <= extreme_low
bbwp_is_red_bar    : bool            — BBWP >= extreme_high
bbwp_ma_cross_up   : bool            — crossover EVENT (single bar True)
bbwp_ma_cross_down : bool            — crossunder EVENT (single bar True)
```

### Calculation steps (must match Pine v2 EXACTLY)

**Step 1: BB Width**
```python
basis = SMA(close, basis_len)  # or EMA/WMA/RMA/HMA/VWMA per basis_type
stdev = rolling_std(close, basis_len)
bbw = (2 * stdev) / basis  # raw BB width
```

**Step 2: BBWP (percentile rank)**
```python
# Pine: ta.percentrank(bbw, lookback)
# Python equivalent: for each bar, count how many of the last `lookback` BBW values
# are LESS THAN the current BBW value, divide by lookback, multiply by 100
bbwp = bbw.rolling(lookback).apply(lambda x: percentileofscore(x[:-1], x[-1], kind='strict'))
# NOTE: percentileofscore from scipy.stats — verify it matches Pine's ta.percentrank
```

**Step 3: BBWP MA**
```python
bbwp_ma = SMA(bbwp, bbwp_ma_len)  # or EMA/WMA per bbwp_ma_type
```

**Step 4: Spectrum color**
```python
# 5-tier discrete (NOT gradient like Pine visual)
def _spectrum_color(val):
    if val <= 20:   return 'blue'
    elif val <= 40: return 'green'
    elif val <= 60: return 'yellow'
    elif val <= 80: return 'orange'
    else:           return 'red'
```

**Step 5: State detection (CRITICAL — must match Pine priority order)**
```python
# Pine v2 priority chain:
# 1. bluBar AND bluSpectrum → BLUE_DOUBLE (2 pts)
# 2. bluSpectrum (not bluBar) → BLUE (1 pt)
# 3. redBar AND redSpectrum → RED_DOUBLE (1 pt) ← NOTE: 1 point, not 0
# 4. redSpectrum (not redBar) → RED (1 pt)
# 5. showMaCrossUp (persisted) → MA_CROSS_UP (1 pt)
# 6. showMaCrossDown (persisted) → MA_CROSS_DOWN (0 pts)
# 7. else → NORMAL (0 pts)

# MA CROSS STATE PERSISTENCE:
# - maCrossUp fires when: inNormalRange AND bbwp crosses ABOVE bbwp_ma
# - showMaCrossUp stays True until: bluSpectrum OR redSpectrum OR timeout
# - inNormalRange = NOT bluSpectrum AND NOT redSpectrum
# - timeout = bars since cross >= ma_cross_timeout (10)
# - New cross resets the counter
# - Cross UP cancels any active Cross DOWN (and vice versa)
```

### TRICKY PARTS — PAY ATTENTION

1. **MA cross persistence is STATEFUL.** Pine uses `var` variables that persist across bars. In pandas you need to iterate or use a stateful apply. This is the one part where vectorized pandas won't work cleanly — use a loop or numba.

2. **percentrank matching.** Pine's `ta.percentrank(source, length)` counts values strictly less than current. Verify `scipy.stats.percentileofscore(a, score, kind='strict')` produces identical results. If not, implement manually:
   ```python
   count_below = (window[:-1] < window[-1]).sum()
   prank = count_below / (len(window) - 1) * 100
   ```

3. **NaN handling.** First `lookback` bars will have NaN for BBWP. First `lookback + bbwp_ma_len` bars will have NaN for BBWP MA. State detection should return 'NORMAL' for NaN bars.

4. **Edge case: basis = 0.** If SMA of close is 0 (shouldn't happen with real data), bbw = 0. Handle with `if basis > 0` guard, same as Pine.

5. **Points mapping from Pine v2:**
   - BLUE_DOUBLE: 2
   - BLUE: 1
   - RED_DOUBLE: 1 (NOT 0 — check Pine source line ~154)
   - RED: 1
   - MA_CROSS_UP: 1
   - MA_CROSS_DOWN: 0
   - NORMAL: 0

---

## BUILD ORDER

### Step 1: Write test file FIRST
**File:** `tests/test_bbwp.py`

Tests to write:
```python
def test_bbw_calculation():
    """BB width = (2 * stdev) / basis. Manual calc on 20 bars of known data."""

def test_percentrank_matches_pine():
    """Compare our percentrank to Pine's ta.percentrank on known sequence."""

def test_spectrum_color_boundaries():
    """Verify 20/40/60/80 boundaries produce correct colors."""

def test_state_priority_order():
    """BLUE_DOUBLE takes priority over BLUE. RED_DOUBLE over RED. etc."""

def test_ma_cross_persistence():
    """Cross fires, persists for N bars, auto-resets on timeout."""

def test_ma_cross_cancelled_by_spectrum():
    """Active MA_CROSS_UP cancelled when BBWP enters blue/red spectrum."""

def test_ma_cross_up_cancels_down():
    """New cross up cancels active cross down state."""

def test_points_mapping():
    """Verify points match Pine v2 exactly."""

def test_nan_handling():
    """First lookback bars return NaN for bbwp, NORMAL for state."""

def test_output_columns():
    """Verify all 10 columns present with correct dtypes."""

def test_on_real_parquet():
    """Load RIVERUSDT 5m parquet, run calculate_bbwp, sanity check distributions."""
```

Use mock data with KNOWN expected outputs for the first 9 tests. Use real parquet for test 10.

### Step 2: Write signals/bbwp.py
Implement to pass all tests.

### Step 3: Sanity checks on real data
After tests pass, run on RIVERUSDT 5m and verify:
- bbwp_value distribution: should be roughly uniform 0-100 (it's a percentile)
- State distribution: NORMAL should be most common (50-70%), BLUE_DOUBLE/RED_DOUBLE should be rare (1-5%)
- bbwp_points: mean should be 0.3-0.8 range
- No NaN in bbwp_state (should always have a value)
- bbwp_ma_cross_up events should be sparse (not every bar)

### Step 4: Ollama code review
After tests pass, send bbwp.py to qwen2.5-coder:32b for review:
```python
import requests
code = open('signals/bbwp.py').read()
spec = open(r'C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md').read()
response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'qwen2.5-coder:32b',
    'prompt': f"Review this Python code against its spec. Flag: logic errors, off-by-one, Pine Script mismatches, missing edge cases.\n\nSPEC:\n{spec}\n\nCODE:\n{code}\n\nOutput: bullet list of issues or PASS.",
    'temperature': 0.2,
    'stream': False,
})
print(response.json()['response'])
```

### Step 5: Log to Obsidian
Write build log to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-XX-bbw-layer1-build.md`:
- What was built
- Test results (pass/fail counts)
- Ollama review findings
- Sanity check distributions
- Issues found and fixed
- Time taken

---

## REVIEW CHECKLIST — VERIFY BEFORE SUBMITTING

### Pine Script Fidelity
- [ ] BB width formula matches: (2 * stdev) / basis
- [ ] percentrank implementation matches ta.percentrank behavior
- [ ] State priority chain matches Pine v2 exactly (7 states, correct order)
- [ ] Points mapping matches Pine v2 exactly (especially RED_DOUBLE = 1)
- [ ] MA cross persistence logic: fires in normal range only, persists, timeout resets
- [ ] MA cross cancellation: blue/red spectrum kills active cross, new cross replaces old
- [ ] Spectrum boundaries: 20/40/60/80 (NOT 25/75 — those are spectrum_low/high for state detection)

### Code Quality (per python-trading-development-skill.md)
- [ ] Test-first: tests written and passing before production code finalized
- [ ] Paths use pathlib (not hardcoded strings)
- [ ] All columns validated (required input cols, expected output cols)
- [ ] NaN handling explicit
- [ ] Docstrings explain WHY, not just WHAT
- [ ] No hardcoded magic numbers — all from DEFAULT_PARAMS
- [ ] Pure function — no side effects, no print(), no file I/O
- [ ] Type hints on function signature

### Performance
- [ ] Vectorized where possible (BB width, spectrum, bars, points)
- [ ] Loop only where necessary (MA cross state persistence)
- [ ] Should process 100K bars in under 5 seconds
- [ ] No iterrows() anywhere

### Downstream Compatibility
- [ ] Output DataFrame has original columns + 10 new bbwp_ columns (no columns dropped)
- [ ] Column names match exactly what Layer 2 expects: bbwp_value, bbwp_spectrum, bbwp_state, bbwp_is_blue_bar, bbwp_is_red_bar
- [ ] State strings match exactly: 'BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'MA_CROSS_DOWN', 'NORMAL', 'RED', 'RED_DOUBLE' (underscores, uppercase)
- [ ] Spectrum strings match exactly: 'blue', 'green', 'yellow', 'orange', 'red' (lowercase)

---

## SANITY PERSPECTIVE — WHY THIS MATTERS

This file gets called 399 times during simulation and potentially thousands of times during live trading. A bug here propagates into every downstream layer:
- Wrong BBWP value → wrong state detection → wrong LSG mapping → wrong position sizing → real money lost
- Wrong percentrank → statistical analysis in Layer 4 is invalid → Monte Carlo validates garbage
- Wrong MA cross logic → phantom signals that don't exist on TradingView chart → trades that shouldn't fire

The Pine Script is the source of truth. If Python output differs from Pine output on the same data, Python is wrong.

**Validation approach:** Export 100 bars of BBWP data from TradingView (Data Window → export), run same bars through Python, diff the outputs. Every value should match within floating point tolerance (1e-6).

---

## DO NOT BUILD

- Layer 2+ (that's next prompt)
- VINCE features (those derive from Layer 1+2 output, built separately)
- Report generation
- CLI entry point
- Anything not in signals/bbwp.py and tests/test_bbwp.py
