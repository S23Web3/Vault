# CLAUDE CODE PROMPT — Layer 3: Forward Return Tagger

## CONTEXT

Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
Layer 1 (`signals\bbwp.py`) — 61/61 PASS
Layer 2 (`signals\bbw_sequence.py`) — 68/68 PASS, 148/148 debug PASS

Layer 3 is the FIRST file in `research\`. Create `research\__init__.py` (empty) before building.

## MANDATORY — READ FIRST

1. Read skill file: `skills\python\SKILL.md`
2. Read `signals\bbwp.py` (Layer 1 output columns)
3. Read `signals\bbw_sequence.py` (Layer 2 output columns)

## STRATEGY — TOKEN CONSERVATION

Do NOT write files interactively. Write complete files in one shot each.

Execution order:
1. Read skill file + both signal files (3 reads)
2. Create `research\` directory AND `research\__init__.py` (empty). Use: `from pathlib import Path; Path('research').mkdir(exist_ok=True); Path('research/__init__.py').touch()`
3. Write `research\bbw_forward_returns.py` in one shot
4. `python -m py_compile research\bbw_forward_returns.py` — MUST pass before proceeding
5. Write `tests\test_forward_returns.py` in one shot
6. `python -m py_compile tests\test_forward_returns.py` — MUST pass
7. Run: `python tests\test_forward_returns.py`
8. Write `scripts\debug_forward_returns.py` in one shot
9. `python -m py_compile scripts\debug_forward_returns.py` — MUST pass
10. Run: `python scripts\debug_forward_returns.py`
11. Write `scripts\sanity_check_forward_returns.py` in one shot
12. `python -m py_compile scripts\sanity_check_forward_returns.py` — MUST pass
13. Run: `python scripts\sanity_check_forward_returns.py`
14. Write `scripts\run_layer3_tests.py` (runner that saves all output to log)
15. Run: `python scripts\run_layer3_tests.py`

Total: ~17-20 tool calls (3 reads, 1 init, 5 writes, 5 py_compile checks, 3-4 runs)

## CRITICAL — STRING SAFETY

All docstrings use forward slashes for paths: `research/bbw_forward_returns.py`
All code paths use `pathlib.Path` with forward slashes or relative joins.
NEVER put Windows backslash paths in docstrings, strings, or f-strings.
After writing each .py file: `python -m py_compile <file>` — if SyntaxError, fix before proceeding.

---

## SPEC: `research\bbw_forward_returns.py`

### Function: `tag_forward_returns(df, windows=None, atr_period=14, proper_move_atr=3.0)`

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with OHLCV columns (`open`, `high`, `low`, `close`, `base_vol`).
Layer 1/2 columns NOT required — this function works on raw OHLCV.
Output: Same DataFrame with forward return columns added.

### Parameters:
```python
DEFAULT_WINDOWS = [10, 20]  # 10 bars = 50min on 5m, 20 bars = 1h40 on 5m
```

### Internal ATR calculation:
```python
def _calculate_atr(df, period=14):
    """
    Wilder's ATR (exponential moving average of true range).
    Returns Series of ATR values. First `period` bars are NaN.
    """
    high = df['high'].values
    low = df['low'].values
    prev_close = df['close'].shift(1).values

    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - prev_close),
            np.abs(low - prev_close)
        )
    )
    # Wilder's EMA: alpha = 1/period
    atr = pd.Series(tr, index=df.index).ewm(alpha=1.0/period, min_periods=period, adjust=False).mean()
    return atr
```

### Output columns per window (e.g. window=10):
```
fwd_10_max_up_pct    : float  — max upside % = (max_high_in_window - close) / close * 100
fwd_10_max_down_pct  : float  — max downside % = (min_low_in_window - close) / close * 100  [NEGATIVE]
fwd_10_max_up_atr    : float  — max upside in ATR multiples = (max_high - close) / atr
fwd_10_max_down_atr  : float  — max downside in ATR multiples = (close - min_low) / atr  [POSITIVE]
fwd_10_close_pct     : float  — close-to-close % = (close[i+w] - close[i]) / close[i] * 100
fwd_10_direction     : str    — 'up' if close_pct > 0, 'down' if < 0, 'flat' if == 0
fwd_10_max_range_atr : float  — full range in ATR = (max_high - min_low) / atr
fwd_10_proper_move   : bool   — True if max_range_atr >= proper_move_atr (default 3.0)
```

Total: 8 columns x 2 windows = 16 new columns + fwd_atr = 17 columns.

### SIGN CONVENTIONS (CRITICAL — get this right):
- `max_up_pct`: always >= 0 (how much price went UP from entry)
- `max_down_pct`: always <= 0 (how much price went DOWN from entry — NEGATIVE value)
- `max_up_atr`: always >= 0 (upside in ATR multiples)
- `max_down_atr`: always >= 0 (downside in ATR multiples — POSITIVE, direction stripped)
- `close_pct`: positive or negative (signed)
- `max_range_atr`: always >= 0 (total range)

Layer 4 assigns MFE/MAE based on trade direction:
- LONG: MFE = max_up_atr, MAE = max_down_atr
- SHORT: MFE = max_down_atr, MAE = max_up_atr
Layer 3 does NOT assign MFE/MAE — just raw directional components.

### Vectorized forward-looking calculation:
```python
def _forward_max(series, window):
    """Max of next `window` bars (EXCLUDING current bar).
    
    How it works:
    1. Reverse the series
    2. Rolling max with min_periods=window (backward-looking on reversed = forward-looking on original)
    3. Reverse back — now bar i has max(i, i+1, ..., i+w-1) INCLUDING current bar
    4. shift(-1) — now bar i has max(i+1, i+2, ..., i+w) EXCLUDING current bar
    
    NaN boundary: last `window` bars are NaN.
    Reason: bar i needs bars i+1 through i+w to exist. Bar n-w needs bars n-w+1 through n,
    but bar n doesn't exist (0-indexed df of length n has indices 0 to n-1).
    So bars n-w through n-1 (last w bars) are NaN.
    """
    return series[::-1].rolling(window=window, min_periods=window).max()[::-1].shift(-1)

def _forward_min(series, window):
    """Min of next `window` bars (EXCLUDING current bar). Same logic as _forward_max."""
    return series[::-1].rolling(window=window, min_periods=window).min()[::-1].shift(-1)
```

**VALIDATION:** For a 100-bar df with window=10:
- Bars 0-89: valid (each looks at 10 future bars)
- Bars 90-99: NaN (last 10 bars, can't look far enough ahead)
- Bar 89 is the LAST valid bar (looks at bars 90-99 = exactly 10 bars)

Do NOT use Python loops over bars. Entire calculation must be vectorized.

### DataFrame mutation:
Same pattern as Layer 1 and Layer 2 — `df = df.copy()` at the start, add columns to the copy, return it. Never mutate the input.

### Edge cases:
1. **Last w bars** — last `window` bars have NaN fwd columns (can't look forward enough)
2. **ATR = 0** (perfectly flat price) — ATR-normalized columns = NaN (not inf). Use `np.where(atr > 0, value / atr, np.nan)` or equivalent to prevent div-by-zero.
3. **NaN in OHLCV** — propagates to output (don't fill)
4. **ATR warmup** — bar 0 always has NaN TR (no prev_close). First valid ATR at bar `atr_period`. Bars 0 through `atr_period - 1` have NaN ATR — ATR-normalized columns NaN for those bars.
5. **close = 0** — pct columns = NaN (not inf). Use `np.where(close != 0, ..., np.nan)`.
6. **max_up = 0** (price never went above entry) — max_up_pct = 0.0, max_up_atr = 0.0 (not NaN)
7. **Overlap of ATR warmup + forward NaN** — some bars near the start have NaN ATR, some near the end have NaN forward returns. Middle bars should have all valid values. Tests must verify the valid range explicitly.

### Input validation:
```python
REQUIRED_OHLCV = ['open', 'high', 'low', 'close', 'base_vol']
# Raise ValueError if any missing
```

### Also export:
```python
ATR_COL = 'fwd_atr'  # expose the ATR series as a column for downstream use
```

Add `fwd_atr` column (the raw ATR values) to output. Layer 4 needs it.

---

## SPEC: `tests\test_forward_returns.py`

12 tests, 50+ assertions. Use synthetic OHLCV data.

### Helper:
```python
def make_ohlcv(n=100, base_price=100.0, volatility=0.01):
    """Generate synthetic OHLCV with controlled properties."""
    np.random.seed(42)
    closes = base_price + np.cumsum(np.random.randn(n) * base_price * volatility)
    highs = closes + np.abs(np.random.randn(n)) * base_price * volatility
    lows = closes - np.abs(np.random.randn(n)) * base_price * volatility
    opens = closes + np.random.randn(n) * base_price * volatility * 0.5
    # Ensure OHLC consistency
    highs = np.maximum(highs, np.maximum(opens, closes))
    lows = np.minimum(lows, np.minimum(opens, closes))
    return pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows,
        'close': closes, 'base_vol': np.random.rand(n) * 10000
    })
```

### Tests:
1. **Output columns** — 16 fwd columns + fwd_atr = 17 new columns present
2. **Missing OHLCV** — raises ValueError
3. **ATR calculation** — verify against manual TR + EWM using `atr_period=3` on a 10-bar dataset (need enough bars for warmup)
4. **Sign conventions** — max_up_pct >= 0, max_down_pct <= 0, max_up_atr >= 0, max_down_atr >= 0
5. **Last w bars NaN** — last 10 bars have NaN fwd_10 columns, last 20 bars NaN fwd_20 columns
6. **Known forward returns** — construct 20-bar dataset (16 stable warmup + 4 active bars), use `atr_period=2, windows=[4]`. Verify exact pct values AND exact ATR-normalized values. Entry bar must have same range as warmup bars so ATR is stable there.
7. **ATR normalization** — using the same controlled dataset from test 6, verify `fwd_4_max_up_atr == (max_high - close) / atr` to 6 decimal places. The key is that ATR must be a known exact value at the test bar.
8. **Direction label** — positive close_pct -> 'up', negative -> 'down', zero -> 'flat'
9. **Proper move** — construct SLIGHTLY VOLATILE data (NOT flat — flat gives ATR=0 which makes everything NaN). Use alternating bars: even bars O=99,H=101,L=99,C=100 and odd bars O=100,H=101,L=99,C=100 so TR=2 and ATR converges to 2.0. Then spike bar with range >= 6.0 (3×ATR) triggers proper_move=True, and a smaller spike with range < 6.0 gives proper_move=False. Use `atr_period=2`, verify ATR is exactly 2.0 at the test bar. Do NOT use flat data (ATR=0 → NaN → test is meaningless).
10. **ATR zero handling** — flat price series -> ATR near 0 -> ATR-normalized cols = NaN, not inf
11. **Custom windows** — pass windows=[5, 30], verify columns named fwd_5_* and fwd_30_*
12. **Real parquet** — RIVERUSDT 5m, run tag_forward_returns, distribution checks:
    - fwd_atr > 0 for valid bars
    - max_down_pct mean < 0
    - proper_move rate between 5% and 80%
    - direction distribution roughly 40-60% up/down
    - No inf values anywhere

---

## SPEC: `scripts\debug_forward_returns.py`

Hand-computed vectors validating exact math. Same pattern as `debug_bbw_sequence.py`.

### Section 1: ATR calculation validation
- Use `atr_period=3` for manageable hand computation.
- 10-bar dataset with known OHLCV prices.
- Bar 0: TR is NaN (no prev_close) — verify ATR[0] = NaN.
- Bars 1+: compute TR manually, then Wilder's EWM: `ATR[i] = ATR[i-1] * (1 - 1/period) + TR[i] * (1/period)`
- First valid ATR at bar `atr_period` (0-indexed). Bars 0 to period-1 are NaN.
- Show: each bar's TR, cumulative ATR, verify numerically to 6 decimal places.

### Section 2: Forward return exact values
- Use `atr_period=2` and `windows=[4]` for this test.
- 20-bar dataset: 16 bars of stable data for ATR warmup, then 4 known bars.
- IMPORTANT: the "entry" bar must have the SAME range as the warmup bars so ATR is stable at that bar.
```
Bars 0-15:  O=100, H=102, L=98, C=100  (all identical, TR=4 from bar 1 onward, ATR converges to 4.0)
Bar 16: O=101, H=105, L=99,  C=103
Bar 17: O=103, H=107, L=101, C=104
Bar 18: O=104, H=106, L=95,  C=96   (big drop)
Bar 19: O=96,  H=98,  L=93,  C=94
```
- ATR trace:
  - Bar 0: TR=NaN (no prev_close). ATR=NaN.
  - Bar 1: prev_close=100, TR=max(102-98, |102-100|, |98-100|)=max(4,2,2)=4. ATR=NaN (min_periods=2).
  - Bar 2: TR=4. ATR = 0.5*4 + 0.5*4 = 4.0. First valid ATR.
  - Bars 3-15: TR=4, ATR stays 4.0 (stable).
  - Bar 15 is the ENTRY bar. ATR[15] = 4.0 exactly.

- For bar 15 with window=4 (looks at bars 16, 17, 18, 19):
  - max_high = max(H[16..19]) = max(105, 107, 106, 98) = 107
  - min_low = min(L[16..19]) = min(99, 101, 95, 93) = 93
  - max_up_pct = (107 - 100) / 100 * 100 = 7.0
  - max_down_pct = (93 - 100) / 100 * 100 = -7.0
  - max_up_atr = (107 - 100) / 4.0 = 1.75
  - max_down_atr = (100 - 93) / 4.0 = 1.75
  - close_pct = (C[19] - C[15]) / C[15] * 100 = (94 - 100) / 100 * 100 = -6.0
  - direction = 'down'
  - max_range_atr = (107 - 93) / 4.0 = 3.5
  - proper_move (threshold 3.0): 3.5 >= 3.0 = True

- IMPORTANT: bar 16 with window=4 is in the NaN zone (last 4 bars of 20-bar dataset). To verify bar 16, run a SECOND call: `tag_forward_returns(df, windows=[3], atr_period=2)`. With window=3, bar 16 looks at bars 17,18,19:
  - Bar 16: prev_close=C[15]=100, TR=max(105-99, |105-100|, |99-100|)=max(6,5,1)=6
  - ATR[16] = 0.5 * 6 + 0.5 * 4.0 = 5.0
  - max_high = max(H[17..19]) = max(107, 106, 98) = 107
  - min_low = min(L[17..19]) = min(101, 95, 93) = 93
  - max_up_pct = (107 - 103) / 103 * 100 = 3.883495  (note: divide by close[16]=103, NOT 100)
  - max_down_pct = (93 - 103) / 103 * 100 = -9.708738
  - max_up_atr = (107 - 103) / 5.0 = 0.8
  - max_down_atr = (103 - 93) / 5.0 = 2.0
  - close_pct = (C[19] - C[16]) / C[16] * 100 = (94 - 103) / 103 * 100 = -8.737864
  - direction = 'down'
  - max_range_atr = (107 - 93) / 5.0 = 14 / 5 = 2.8
  - proper_move (3.0): 2.8 < 3.0 = False
  - Also verify: bar 16 with window=4 (from the first call) IS NaN — confirms NaN boundary works

### Section 3: Sign convention validation
- Verify across all bars: max_up_pct >= 0, max_down_pct <= 0, max_up_atr >= 0, max_down_atr >= 0
- No inf values

### Section 4: Edge cases
- All flat prices (O=H=L=C=100 every bar) -> TR=0 from bar 1 onward (bar 0 TR=NaN) -> ATR converges to 0 -> ATR-normalized cols = NaN (not inf). Verify no inf anywhere.
- Single bar window (window=1) -> valid results (looks at bar i+1 only)
- Very large window (window > len(df)) -> all NaN
- NaN boundary: for window=10, verify exactly bars n-10 through n-1 have NaN fwd columns (last 10 bars). Bar n-11 must be valid (if ATR is also valid there).

### Section 5: Cross-validate with Layer 1+2 on real data (RIVERUSDT 5m)
- Run L1 -> L2 -> L3
- Group by bbwp_state, compute mean fwd_10_max_range_atr per state
- Verify: BLUE_DOUBLE has higher avg range than NORMAL (core hypothesis)
- Print table: bbwp_state x [mean_range_atr, mean_up_atr, mean_down_atr, proper_move_pct]
- This table is a preview of what Layer 4 will optimize

### Target: 60+ checks

---

## SPEC: `scripts\sanity_check_forward_returns.py`

Load RIVERUSDT 5m -> ATR + Forward Returns -> print summary.

Print:
- ATR: mean, P50, P90 (raw and as % of close)
- Per window (10, 20):
  - max_up_pct: mean, P50, P90
  - max_down_pct: mean, P50, P10
  - max_up_atr: mean, P50, P90
  - max_down_atr: mean, P50, P90
  - close_pct: mean, std
  - direction: % up vs % down
  - max_range_atr: mean, P50, P90
  - proper_move: % of bars flagged
- NaN count per fwd column
- Performance: bars/sec for tag_forward_returns only

---

## SPEC: `scripts\run_layer3_tests.py`

Same pattern as `scripts\run_layer2_tests.py`:
- Runs tests, debug, sanity scripts via subprocess
- Captures stdout/stderr per script
- Saves all output to log file
- Reports pass/fail summary at end

```python
SCRIPTS_TO_RUN = [
    ("Layer 3 Tests", ROOT / "tests" / "test_forward_returns.py"),
    ("Layer 3 Debug Validator", ROOT / "scripts" / "debug_forward_returns.py"),
    ("Layer 3 Sanity Check", ROOT / "scripts" / "sanity_check_forward_returns.py"),
]
```

Log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-bbw-layer3-results.md`

---

## DESIGN DECISIONS (intentional, do NOT change)

1. **Strict NaN tolerance** — using `min_periods=window` (100% valid bars required). One NaN in forward window → NaN result. This is intentional for clean data. A relaxed threshold (70%) can be added later for batch processing with gapped data.
2. **No fwd_N_valid_bars column** — deferred. Only needed with relaxed NaN tolerance.
3. **No fwd_N_bbw_valid column** — Layer 3 works on raw OHLCV only, doesn't depend on Layer 1/2. This flag belongs in the pipeline orchestrator that chains L1→L2→L3.
4. **8 columns per window, not 11** — the 3 dropped columns (valid_bars, bbw_valid, plus one overlap) are deferred per decisions 1-3.

## DO NOT

- Do not rewrite `signals\bbwp.py` or `signals\bbw_sequence.py`
- Do not use Python for-loops over DataFrame rows for forward return calculation — vectorize everything
- Do not print full DataFrames
- Do not run on all 399 coins (single coin only: RIVERUSDT)
- Do not exceed 32K output tokens
- Do not apply edits interactively — write complete files in one shot each
- Do not put Windows backslash paths in any string literal, docstring, or f-string
- ALL paths in code: use `Path(__file__).resolve().parent.parent` or `Path("forward/slash")`
- After writing EVERY .py file: `python -m py_compile <file>` MUST pass before running
