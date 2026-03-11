# Plan: Strategy v4 — Hybrid Stochastic Model

**Date:** 2026-03-07
**Vault copy:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-07-strategy-v4-build-plan.md`

---

## Context

The live bot (v2, `four_pillars_v384` plugin) has R:R = 0.28 (avg win $0.12, avg loss $0.44).
Root cause identified: the state machine fires when **all four stochs (9/14/40/60) dip to extreme low zones simultaneously and bounce** — a pure oversold reversal model.
The strategy catalogue (S1-S11, built 2026-03-07) describes a **hierarchical model**: macro stochs (40/60) provide directional bias and should stay elevated; only the fast stoch (9) pulls back to give the entry timing.

These are fundamentally different models. When everything is oversold together there is no macro trend support — producing small wins and large losses (R:R < 1.0).

Strategy v4 implements the **hybrid model** (user-selected): macro stochs above 50 for direction + stoch_9 pullback below 40 for timing.

Deployment order: backtester first → validate on historical data → bot plugin second.

---

## Gap Summary (Current v3.8.4 vs v4)

| Dimension | v3.8.4 (current) | v4 (new) |
|-----------|-----------------|----------|
| Stage 1 trigger | stoch_9 < 25 | stoch_9 < 40 (Grade B) / < 35 (Grade A) |
| stoch_14 role | must be < 30 (in zone) | must be < 45 (confirms pullback, not full reversal) |
| stoch_40 role | must be < 30 (in zone) | must be > 50 (trend bullish) |
| stoch_60 role | must be < 25 (in zone) | must be > 50 (macro bullish) |
| Signal fires when | all stochs bounce from low | macro/trend stochs up, fast stoch crosses back above trigger |

---

## Signal Logic — v4 Hybrid

### LONG entry

Stage 1 trigger (bar N): `stoch_9 < 40` AND `stoch_40 > 50` AND `stoch_60 > 50`

During Stage 1 (window = `stage_lookback` bars):
- Track: `stoch_14 < 45` seen (shallow pullback on the 14 = confirmation)
- Track: `stoch_40 > 55` seen (strong trend, not just barely above 50)
- Track: `stoch_60 > 60` seen (strong macro)

Signal fires when `stoch_9 >= 40` (crosses back up):
- **Grade A**: stoch_40 > 55 seen + stoch_60 > 60 seen + cloud3_ok
- **Grade B**: stoch_40 > 50 (entry bar) + stoch_60 > 50 (entry bar) + cloud3_ok
- Stage 2 filter removed (was nearly always trivially satisfied at rot_level=80; not meaningful in new model)

### SHORT entry (mirror)

Stage 1 trigger: `stoch_9 > 60` AND `stoch_40 < 50` AND `stoch_60 < 50`

Signal fires when `stoch_9 <= 60`:
- **Grade A**: stoch_40 < 45 seen + stoch_60 < 40 seen + cloud3_ok_short
- **Grade B**: stoch_40 < 50 (entry bar) + stoch_60 < 50 (entry bar) + cloud3_ok_short

### Cloud filter
Keep existing: `price_pos >= 0` for LONG (price at/above Cloud 3) — already proven

### ATR / SL / TP
No change: ATR 14, SL = 2.0x ATR, TP = null (TTP only). Same as v3.8.4.

---

## Files

### New (backtester)

| File | Purpose |
|------|---------|
| `PROJECTS/four-pillars-backtester/signals/state_machine_v4.py` | New state machine class `FourPillarsStateMachineV4` |
| `PROJECTS/four-pillars-backtester/signals/four_pillars_v4.py` | `compute_signals_v4()` — same orchestrator pattern as `four_pillars.py`, uses new state machine |
| `PROJECTS/four-pillars-backtester/scripts/run_v4_backtest.py` | Run v4 vs v3.8.4 comparison on N coins, print side-by-side stats |

### Modified (backtester)

| File | Change |
|------|--------|
| `PROJECTS/four-pillars-backtester/signals/__init__.py` | Import `compute_signals_v4` if it exists |

### Later (bot plugin — after validation)

| File | Purpose |
|------|---------|
| `PROJECTS/bingx-connector-v2/plugins/four_pillars_v4.py` | Drop-in plugin using `compute_signals_v4` |

---

## Critical Files (read-only reference)

| File | Role |
|------|------|
| `PROJECTS/four-pillars-backtester/signals/state_machine.py` | Current state machine — v4 replaces this logic |
| `PROJECTS/four-pillars-backtester/signals/stochastics.py` | Stoch calc — NOT changed (Raw K already correct) |
| `PROJECTS/four-pillars-backtester/signals/four_pillars.py` | Current orchestrator — v4 mirrors this pattern |
| `PROJECTS/four-pillars-backtester/signals/clouds.py` | Cloud calc — NOT changed |
| `PROJECTS/bingx-connector-v2/plugins/four_pillars_v384.py` | Current bot plugin — NOT changed yet |

---

## Default Parameters (v4)

```python
DEFAULTS_V4 = {
    "atr_length":      14,
    "stoch_k1":        9,
    "stoch_k2":        14,
    "stoch_k3":        40,
    "stoch_k4":        60,
    # v4 thresholds
    "v4_fast_trigger": 40,     # stoch_9 must be below this for Stage 1 (LONG)
    "v4_fast_grade_a": 35,     # stoch_9 < this = Grade A qualifier
    "v4_trend_min":    50,     # stoch_40 must be above this (LONG)
    "v4_trend_strong": 55,     # stoch_40 > this = Grade A qualifier
    "v4_macro_min":    50,     # stoch_60 must be above this (LONG)
    "v4_macro_strong": 60,     # stoch_60 > this = Grade A qualifier
    "v4_confirm_max":  45,     # stoch_14 < this = pullback confirmed (optional Grade A)
    "stage_lookback":  10,
    "allow_b":         True,
    "allow_c":         False,
}
```

---

## Build Method

**Write tool directly** (not build script) — same as visualizer builds.
Rationale: state machine is ~200 lines; build scripts with triple-quoted source strings cause escaped-newline bugs.

**After each file write**: `python -c "import py_compile; py_compile.compile('path', doraise=True)"` via Bash.

**All functions must have one-line docstrings** (hard rule).

---

## Comparison Script Logic (`run_v4_backtest.py`)

1. Load N coins from backtester data dir (default: 10)
2. Run `compute_signals()` (v3.8.4) + `compute_signals_v4()` on same data
3. Run backtester engine on each signal set (same ATR SL, same capital)
4. Print side-by-side per-coin:
   - Signal count, WR, Net P&L, Avg win, Avg loss, R:R
5. Print aggregate summary row

Key metric to watch: **R:R** — target > 1.0 for v4 to move toward breakeven.

---

## Verification

```bash
# 1 — syntax checks (run after each Write)
python -c "import py_compile; py_compile.compile(r'C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\state_machine_v4.py', doraise=True)"
python -c "import py_compile; py_compile.compile(r'C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v4.py', doraise=True)"
python -c "import py_compile; py_compile.compile(r'C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_v4_backtest.py', doraise=True)"

# 2 — run comparison
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/run_v4_backtest.py --limit 10

# 3 — expected output
# Table with v3.8.4 vs v4 stats per coin
# Key metric: v4 R:R > v3.8.4 R:R (target > 1.0)
```

---

## Out of Scope (this session)

- BBWP filter in signal engine (S9 integration — future enhancement)
- AVWAP confirmation (S11)
- 3-phase ATR SL progression (S10)
- Bot plugin `four_pillars_v4.py` (after backtest validation)
- Parameter sweep / optimization

---

## Session Log

Append to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-07-strategy-catalogue-visual-plan.md`
Use Edit tool only.
