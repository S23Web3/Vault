# Handoff Prompt — 55/89 EMA Cross Scalp: Master Build Script

**Date:** 2026-03-06
**Purpose:** Complete handoff for a new chat to build the 55/89 scalp strategy backtest as a MASTER SCRIPT. The script creates all files, validates each with py_compile, and wires into the existing dashboard.

---

## BASH PERMISSIONS NEEDED

Grant ALL of these upfront so the build runs uninterrupted:

```
Tool: Bash — "py_compile validation on generated .py files"
Tool: Bash — "python -c 'import py_compile; py_compile.compile(...)'"
Tool: Bash — "ls / dir commands to check file existence"
Tool: Bash — "head / cat to verify written file contents"
Tool: Bash — "git status / git diff (if user requests commit)"
Tool: Read — any file in C:\Users\User\Documents\Obsidian Vault\
Tool: Write — new files only (never overwrite existing without version bump)
Tool: Edit — append to session log, edit existing files
Tool: Glob — file pattern searches
Tool: Grep — code content searches
```

---

## MANDATORY FIRST READS

Read these files IN THIS ORDER before doing anything else:

1. `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` — project rules, hard constraints
2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md` — COMPLETE research methodology (8 sections: Markov chain, OU diffusion, slope/degree, TDI, stoch 9 trigger, BBW regime, MC simulation, Vince state output). SOURCE OF TRUTH for what the signal IS.
3. `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-06-55-89-scalp-research-plan.md` — research plan v2 (corrected after 12-discrepancy audit)
4. `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-06-uml-55-89-scalp-session.md` — session log showing what Claude previously INVENTED vs what user ACTUALLY SAID
5. `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md` — position management research (stoch settings, BBW rules, TDI rules)

---

## THE SIGNAL — EXACTLY AS STATED BY USER

Three confirmed elements. Nothing else.

1. All 4 stochastics align (9 / 14 / 40 / 60) — directional momentum building as a group
2. 55/89 EMA cross on 1m chart (BOTH are EMAs)
3. Move SL to breakeven after cross confirms

Key clarifications from the user (DO NOT contradict these):

- "Aligned" is NOT "all 4 crossed." It means fast stochs (9, 14) already moving; slow stochs (40, 60) showing improving degree of change. Could be in zone, at edge, or past it.
- Stoch 9 K/D cross is THE GATE. System is IDLE until it fires. Everything else is measured relative to stoch 9's cross as time-zero.
- K/D crossover on slow stochs is an observation, not a prerequisite.
- EMA delta compression is part of reading alignment, not a separate signal.
- TDI (RSI=9, Smooth=5, Signal=10) applies — CONFIRMING/OPPOSING states.
- BBW (BBWP SMA 7, length 100, Spectrum) applies — HEALTHY/EXTREME/QUIET states.
- Markov chain and OU diffusion models are LITERAL builds, not conceptual framing.

---

## CRITICAL ARCHITECTURE FINDINGS

The dashboard does NOT use BaseStrategy classes. It hardcodes the signal pipeline directly:

```python
# dashboard_v394.py line 57
from signals.four_pillars_v383_v2 import compute_signals_v383

# dashboard_v394.py line 71
from engine.backtester_v384 import Backtester384

# dashboard_v394.py line 284-287 (run_backtest function)
def run_backtest(df, sig_params, run_params, accumulator=None):
    df_sig = compute_signals_v383(df.copy(), sig_params)
    bt = Backtester384(run_params)
    results = bt.run(df_sig)
    return results, df_sig
```

The engine expects these signal columns in the DataFrame:

**Required:** `close`, `high`, `low`, `atr`, `long_a`, `long_b`, `short_a`, `short_b`, `reentry_long`, `reentry_short`, `cloud3_allows_long`, `cloud3_allows_short`

**Optional (with defaults):** `add_long_signal`, `add_short_signal`, `cloud2_cross_bull`, `cloud2_cross_bear`, `cloud3_cross_bull`, `cloud3_cross_bear`, `phase3_active_long`, `phase3_active_short`, `bbwp_state`, `bbwp_value`, `bbwp_spectrum`, `base_vol`

---

## WHAT THE MASTER SCRIPT MUST BUILD

The script (`scripts/build_55_89_scalp.py`) creates ALL of the following files, py_compile-validates each, and reports pass/fail:

### File 1: Signal Module
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\ema_cross_55_89.py`

A `compute_signals_55_89(df, params)` function that:
1. Computes all 4 stochs via existing `compute_all_stochastics()` from `signals/stochastics_v2.py`
2. Computes D lines for all 4 stochs (SMA smoothing: 9->3, 14->3, 40->4, 60->10)
3. Computes EMA(55) and EMA(89) via existing `ema()` from `signals/clouds_v2.py`
4. Computes delta = EMA55 - EMA89
5. Computes ATR (Wilder RMA, period 14) — engine requires `atr` column
6. Computes TDI: RSI(close, 9), price_line = SMA(RSI, 5), signal_line = SMA(RSI, 10)
7. Computes BBW state: Bollinger(20, 2.0), BBWP over 100 bars, Spectrum MA = SMA(BBWP, 7)
8. Computes slope/acceleration on stoch 40/60: slope_N = K[i] - K[i-N], accel = slope_N[i] - slope_N[i-M]
9. Classifies each bar per stoch into Markov states: ZONE/TURNING/MOVING/EXTENDED
10. Implements the pipeline:
    - IDLE until stoch 9 K/D cross (K_9 crosses above D_9 for long, below for short)
    - MONITORING: check alignment (stoch 14 MOVING/EXTENDED, stoch 40/60 TURNING+, no contradiction, delta compressing, TDI confirming, BBW not QUIET)
    - Signal fires when: alignment active AND delta crosses zero (EMA cross happens)
    - Back to IDLE if stoch 9 reverses
11. Maps to engine-expected columns:
    - `long_a` = True when long signal fires (alignment + bullish EMA cross)
    - `short_a` = True when short signal fires (alignment + bearish EMA cross)
    - `long_b`, `short_b` = False (no Grade B for this strategy)
    - `reentry_long`, `reentry_short` = False (no re-entry logic)
    - `cloud3_allows_long`, `cloud3_allows_short` = True (no cloud filter)
    - All cloud cross columns = False (not used)
    - `bbwp_state`, `bbwp_value` = from BBW computation
12. Returns enriched DataFrame compatible with `Backtester384.run()`

### File 2: Dashboard Patch Script
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\patch_dashboard_55_89.py`

A script that patches `dashboard_v394.py` to add:
1. Import of `compute_signals_55_89` at the top
2. Strategy selector dropdown in sidebar (after line ~450): `st.sidebar.selectbox("Strategy", ["Four Pillars v3.8.4", "55/89 EMA Cross Scalp"])`
3. Conditional signal compute in `run_backtest()`: if strategy == "55/89", use `compute_signals_55_89` instead of `compute_signals_v383`
4. Conditional sidebar params: hide Four Pillars-specific params when 55/89 is selected, show 55/89-specific params (slope window N, slope window M)

OR: create a NEW dashboard file `scripts/dashboard_v394_55_89.py` that copies v394 and adds the strategy selector. User decides.

### File 3: Standalone Runner
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest.py`

CLI script to run the 55/89 backtest standalone (outside dashboard):
```
python scripts/run_55_89_backtest.py --symbol BTCUSDT --months 3
```

Loads parquet, calls `compute_signals_55_89()`, runs through `Backtester384`, prints metrics.

### File 4: Test Script
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_55_89_signals.py`

Validates:
- Signal module imports without error
- compute_signals_55_89() runs on a sample parquet
- Output DataFrame has all required engine columns
- Signal counts are non-zero (sanity check)
- Markov state classification produces valid states
- D line smoothing matches expected values
- TDI computation produces valid output
- BBW state classification produces valid states

---

## MASTER SCRIPT STRUCTURE

```python
# scripts/build_55_89_scalp.py
#
# Master build script for 55/89 EMA Cross Scalp strategy.
# Creates all files, validates each with py_compile, reports results.
#
# Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py"

import py_compile
from pathlib import Path

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
ERRORS = []

def write_and_validate(filepath: Path, content: str):
    """Write file and py_compile. Track failures."""
    if filepath.exists():
        print(f"SKIP (exists): {filepath}")
        ERRORS.append(f"File already exists: {filepath}")
        return False
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"PASS: {filepath}")
        return True
    except py_compile.PyCompileError as e:
        print(f"FAIL: {filepath} -- {e}")
        ERRORS.append(str(e))
        return False

# --- File 1: Signal module ---
write_and_validate(ROOT / "signals" / "ema_cross_55_89.py", SIGNAL_MODULE_CODE)

# --- File 2: Dashboard patch ---
write_and_validate(ROOT / "scripts" / "patch_dashboard_55_89.py", PATCH_CODE)

# --- File 3: Standalone runner ---
write_and_validate(ROOT / "scripts" / "run_55_89_backtest.py", RUNNER_CODE)

# --- File 4: Test script ---
write_and_validate(ROOT / "scripts" / "test_55_89_signals.py", TEST_CODE)

# --- Report ---
if ERRORS:
    print("\nFAILURES: " + ", ".join(ERRORS))
else:
    print("\nALL FILES CREATED AND VALIDATED")
```

---

## EXISTING CODE TO REUSE (do not rewrite)

| What | Full Path | Function |
|------|-----------|----------|
| Raw K stochastic (all 4) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\stochastics_v2.py` | `compute_all_stochastics()` — returns stoch_9/14/40/60 columns. Numba JIT. |
| EMA (JIT, matches Pine) | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\clouds_v2.py` | `ema(series, length)` — Numba JIT. Use for EMA(55), EMA(89). |
| BBW state classification | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_analyzer_v2.py` | BBW state logic. Reuse classification approach. |
| MC validation pattern | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_monte_carlo_v2.py` | Bootstrap/permutation structure for MC validation. |
| 1m parquet data | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\historical\*.parquet` | 371 coins. |
| Signal pipeline pattern | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` | `compute_signals_v383(df, params)` — follow same function signature pattern. |
| Engine | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v384.py` | `Backtester384(params).run(df_sig)` — the engine the dashboard uses. |

### New code required (written by the master script)

| What | Why |
|------|-----|
| D lines for stochs 9, 14, 40 | `stochastics_v2.py` only computes `stoch_60_d`. Need D = SMA(K, smooth) for all 4. |
| TDI computation | RSI(close, 9), SMA(RSI, 5), SMA(RSI, 10). Not in existing codebase. |
| Markov state classifier | ZONE/TURNING/MOVING/EXTENDED per stoch per bar. New logic. |
| Slope/acceleration | First/second derivative on stoch K values. New logic. |
| Signal-to-engine column mapping | Map 55/89 signal output to engine-expected columns (long_a, short_a, etc.). |

---

## OPEN QUESTIONS — MUST ASK USER BEFORE BUILDING

These are functional gaps, not invented conditions:

1. **Initial SL**: what value? (e.g., 2x ATR? Fixed pips?) Needed to determine if a trade survives to reach BE.
2. **Exit rule**: once SL is at BE, what closes the trade? (opposite signal? time limit? trailing? opposite EMA cross?)
3. **"After cross confirms"**: which cross triggers the BE move — the 55/89 EMA cross?
4. **Dashboard approach**: patch existing v394 or create new dashboard file `dashboard_v394_55_89.py`?

Without answers to 1-3, the backtest cannot compute trade P&L. Ask BEFORE writing the master script.

---

## WHAT NOT TO DO

- Do NOT invent entry conditions, exit conditions, or parameters not stated above
- Do NOT modify `backtester_v384.py` or any existing strategy/signal file
- Do NOT modify `dashboard_v394.py` directly — patch it or create a copy
- Do NOT add HTF filters, BBW/TDI as separate entry gates (they are part of alignment read)
- Do NOT assume product-of-marginals for joint stoch probabilities (stochs are correlated)
- Do NOT treat Markov states as sequential gates (any state, any time)
- Do NOT treat stoch 9 as one of four equal stochs (it is THE gate)
- Do NOT assume OU mean-reversion holds (test it)
- Do NOT execute the master script — write it, validate syntax, hand to user

---

## BUILD RULES

- Read `CLAUDE.md` first — all hard rules apply
- SCRIPT IS THE BUILD — one script creates all files, py_compile-validates each, reports results
- NEVER overwrite existing files — check existence first
- NEVER use escaped quotes in f-strings inside build scripts
- ALL functions must have docstrings
- ALL log entries must have timestamps
- Full Windows paths everywhere
- Log session to `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\YYYY-MM-DD-55-89-scalp-backtest-build.md`

---

## RUN COMMAND

After the master script is built and syntax-validated:

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py"
```

Then test:

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\test_55_89_signals.py"
```

Then run standalone backtest:

```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_55_89_backtest.py" --symbol BTCUSDT
```

---

## REFERENCE FILES (full index)

| File | What it contains |
|------|-----------------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md` | Complete research methodology — Markov, OU, slope, TDI, stoch 9 gate, BBW, MC, Vince state output, UML |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-06-55-89-scalp-research-plan.md` | Research plan v2 (corrected after 12-discrepancy audit) |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md` | Position management research — source of stoch settings, BBW rules, TDI rules |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-1m-ema-delta-scalp-concept.md` | Original concept note — most content marked INVALID (Claude-invented). Only 3 user-stated elements valid. |
| `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-06-uml-55-89-scalp-session.md` | Session log documenting Claude's invention of conditions user never stated |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\base_strategy.py` | BaseStrategy ABC (exists but dashboard doesn't use it — dashboard uses signal functions directly) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\backtester_v384.py` | Backtester384 — the engine the dashboard actually uses (not v391) |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\stochastics_v2.py` | Raw K stoch (JIT). Only has stoch_60_d — needs D for all 4. |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\clouds_v2.py` | EMA function (JIT, matches Pine). Use ema(series, 55) and ema(series, 89). |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` | Current signal pipeline — follow same function signature pattern for compute_signals_55_89(). |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py` | Production dashboard (Streamlit, v3.9.4, ~52290 lines). Lines 57/71 = imports, 264-287 = run_backtest(), 450 = sidebar, 537 = mode selection. |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-FILES.md` | Dashboard version index and file map |
