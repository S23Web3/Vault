# Portfolio Bugfix — 2026-02-16
**Session:** Fix 2 bugs from user screenshot (AFK session)
**Status:** BUILD READY, NOT EXECUTED

---

## Bugs Fixed

### BUG A: Run Portfolio Backtest re-randomizes coin list
**Root cause:** `random.sample()` called on every Streamlit rerun (line 1764). Clicking the Run button triggers a rerun BEFORE the backtest code runs, so the coin list changes.
**Fix:** Store `port_symbols` in `st.session_state["port_symbols_locked"]` when Run is clicked. On subsequent reruns, reuse locked list instead of recomputing. Added "Reset Selection" button to clear the lock.

### BUG B: Best Equity / Worst DD metrics confusing
**Root cause:** "Best Equity: $108k" is the raw summed equity (10 coins x $10k = $100k baseline). So $108k = +$8k net profit at peak. But "Net P&L: -$12k" is the FINAL value. Different timepoints, displayed without context.
**Fix:** Changed labels:
- "Best Equity" -> "Peak Net Profit" showing `+$X` from baseline
- "Worst DD" -> "Worst Drawdown" showing both `% and ($X net)`
- Added help tooltips explaining baseline calculation

---

## Patches Applied (5 total)

| Patch | Target | Description |
|-------|--------|-------------|
| P1 | Session state init (line ~103) | Add `port_symbols_locked` key |
| P2 | Back button (line ~1727) | Clear locked symbols on back |
| P3 | Coin selection (lines 1751-1772) | Lock-on-run logic, Reset button |
| P4 | Run button (line ~1774) | Save port_symbols to session state |
| P5 | Best/Worst display (lines 1827-1839) | Net profit labels, dollar DD |

---

## Files

| File | Action |
|------|--------|
| `scripts/build_portfolio_bugfix.py` | CREATED -- applies 5 patches to dashboard.py |
| `scripts/dashboard_pre_bugfix.py.backup` | CREATED on first run -- backup of dashboard.py |
| `scripts/dashboard.py` | MODIFIED by build script |

---

## Run Command
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_portfolio_bugfix.py"
```

Then test:
```
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py"
```

---

## Validation Checklist
- [ ] Random N: click Run, verify same coins stay on rerun
- [ ] Top N: click Run, verify same coins stay on rerun
- [ ] Reset Selection: verify coins re-randomize after reset
- [ ] Peak Net Profit: shows +$X or -$X (not raw summed equity)
- [ ] Worst Drawdown: shows both % and dollar amount
- [ ] Back to Settings: verify locked symbols clear
- [ ] Custom mode: verify multiselect default works

---

## Session 2: Capital Mode Consistency Fix

**Timestamp:** 2026-02-16
**Status:** BUILD READY, NOT EXECUTED

### Problem
7 data consistency bugs in Shared Pool mode. When capital constraints reject trades, the dashboard still displayed unconstrained data in multiple locations:

| Bug | Location | Issue |
|-----|----------|-------|
| 1 | Per-coin metrics table | Trades, WR%, Volume, Rebate, Sharpe, PF etc from ALL trades |
| 2 | Drill-down trades tab | Shows rejected trades as if they were taken |
| 3 | Trading Volume section | Sums unconstrained volume/commission/rebate |
| 4 | Daily volume stats | Counts rejected trades in daily volume |
| 5 | Net P&L after rebate | Uses unconstrained metrics + DOUBLE baseline subtraction |
| 6 | Total Trades metric | Manual subtraction hack instead of accurate count |
| 7 | Per-coin monthly P&L, grade/exit, loser detail | From unfiltered trades_df |

### Root Cause
`capital_model.py` rebuilt equity curves and position counts but left `trades_df` and `metrics` dict untouched in adjusted coin results. All downstream dashboard code that read `cr["metrics"]` or `cr["trades_df"]` got unconstrained data.

### Fix
**capital_model.py** (4 patches):
- CM1: Added `_rebuild_metrics_from_df()` helper -- rebuilds key metrics from filtered trades_df
- CM2: Added `notional` parameter to `apply_capital_constraints()`
- CM3: Filters `trades_df` to accepted-only, rebuilds `metrics` for adjusted coin results
- CM4: Added `reject_by_coin` to return dict

**dashboard_v39.py** (6 patches):
- D1: Passes `notional` to `apply_capital_constraints()`
- D2: Total Trades metric uses metrics directly (no manual subtraction hack)
- D3: Net P&L after rebate -- removed double baseline subtraction bug
- D4: Stores params hash + margin + notional with portfolio results
- D5: Warns user when sidebar settings changed since last run
- D6: Display uses stored margin/notional from run (not live sidebar)

### Files

| File | Action |
|------|--------|
| `scripts/build_capital_mode_fix.py` | CREATED -- applies 10 patches |
| `utils/capital_model_pre_capfix.py.backup` | CREATED on first run |
| `scripts/dashboard_v39_pre_capfix.py.backup` | CREATED on first run |
| `utils/capital_model.py` | MODIFIED |
| `scripts/dashboard_v39.py` | MODIFIED |

### Run Command
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_capital_mode_fix.py"
```

### Validation Checklist (Shared Pool mode)
- [ ] Per-coin table: Trades column = accepted only (not all engine trades)
- [ ] Per-coin table: Volume$ = accepted trades volume only
- [ ] Per-coin table: Rebate$ = proportionally scaled
- [ ] Drill-down Trades tab: only shows accepted trades
- [ ] Drill-down Grade/Exit tab: grade/exit from accepted trades only
- [ ] Total Trades metric: shows accepted count + rejected subtitle
- [ ] Trading Volume section: Total Volume = accepted only
- [ ] Trading Volume section: Total Rebate = accepted only
- [ ] Trading Volume section: Net P&L after rebate = correct (no double subtraction)
- [ ] Daily volume stats: reflect accepted trades only
- [ ] Per-Coin Independent mode: unchanged, all trades shown
- [ ] Change sidebar margin after run: warning appears
- [ ] Change sidebar SL/TP after run: warning appears
- [ ] Display uses stored margin/notional (not live sidebar after change)
- [ ] Click Run again after warning: results update, warning clears
