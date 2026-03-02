# Plan: BingX Dashboard v1-2 Improvements

## Source of Feedback
User screenshots and notes from v1-1 live testing session (2026-02-28).

## Issues to Fix

### FIX-1: White input fields on Bot Controls tab
**Problem:** Input fields (dcc.Input, dcc.RadioItems) have white background — unreadable against dark theme.
**Root cause:** Dash default component styles override our dark CSS. The `assets/dashboard.css` only styles tabs, rows, and banner — not form controls.
**Fix:** Add CSS rules in `assets/dashboard.css` for:
- `input[type="number"]`, `input[type="text"]` — dark bg (`#161b22`), light text (`#c9d1d9`), border (`#30363d`)
- `.dash-radio` labels — inherit text color
- dcc.Dropdown internals — dark bg, dark menu, light text (`.Select-control`, `.Select-menu-outer`)
**Files:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\assets\dashboard.css`
**Lines:** ~30 new CSS rules

### FIX-2: Positions grid shows "No Rows To Show" on white background
**Problem:** Positions ag-grid has white background — jarring in dark theme.
**Root cause:** `ag-theme-alpine-dark` class may not be applied, or ag-grid's default styles override it.
**Fix:** Verify `className='ag-theme-alpine-dark'` on all `dag.AgGrid` components. Add CSS override for `.ag-root-wrapper`, `.ag-overlay-no-rows-wrapper` background colors.
**Files:** `assets/dashboard.css` + verify `bingx-live-dashboard-v1-1.py` grid definitions

### FIX-3: Analytics shows all-time (196 trades) vs History shows today only (23 trades)
**Problem:** Analytics and History show different trade counts with no way to control the date range.
**Fix:** Add a date range picker (dcc.DatePickerRange) to the Analytics tab. Default to "since bot started" (2026-02-27). Filter trades DataFrame before computing metrics and charts. History tab already has a "Today only" checkbox — add same date range picker there too.
**Files:** `bingx-live-dashboard-v1-1.py` — Analytics tab layout + CB-9 callback + `compute_metrics()` filtering
**New components:** `dcc.DatePickerRange(id='analytics-date-range')`, wired into CB-9
**Lines:** ~30 new

### FIX-4: Data loading too slow / tabs don't retain data
**Problem:** Switching tabs causes re-render. Coming back to Operational tab shows empty grid until next interval tick. Config values take time to appear despite being a local file read.
**Root cause:** CB-2 (`render_tab`) recreates the entire tab layout on each switch. The child callbacks (CB-3 for ops, CB-8 for history, CB-9 for analytics, CB-11 for config) only fire when their Input stores change — but the store data is already in memory, the problem is the tab content components are destroyed and recreated.
**Fix options:**
- **Option A (recommended):** Change tab rendering from `dcc.Tabs` with dynamic content to all tabs rendered in layout but hidden with `style={'display': 'none'}`. Only the active tab has `display: block`. This means all callbacks fire once on load and tab switching is instant (no re-render, no re-fetch).
- **Option B:** Add `dcc.Loading` wrappers around slow components and accept the delay.
- **Option C:** Cache tab content in dcc.Store — complex, not worth it.
**Decision:** Option A — render all tabs, toggle visibility. This eliminates the "empty on switch-back" problem entirely. Also add performance timing logs to identify actual bottlenecks.
**Files:** `bingx-live-dashboard-v1-1.py` — layout restructure + CB-2 replacement
**Impact:** Major callback restructure. CB-2 (render_tab) is removed. All tab layouts are in the initial layout. A single clientside callback toggles visibility.
**Lines:** ~80 changed

### FIX-5: Add timing diagnostics
**Problem:** User reports slow loading — need to measure where time is spent.
**Fix:** Add `time.time()` measurements in CB-1 (data loader) and log: file read time, mark price fetch time, total callback time. Log on every tick.
**Files:** `bingx-live-dashboard-v1-1.py` — CB-1 callback
**Lines:** ~10 new

## Analytics Overhaul

### ANALYTICS-1: Replace amateur metrics with professional trading metrics
**Current metrics (remove):** Total Trades, Win Rate, Profit Factor, Expectancy, Avg Win, Avg Loss, Max DD
**New metrics (add):**

| Metric | Definition | Source |
|--------|-----------|--------|
| Total Trades | Count of closed trades | trades.csv rows |
| Win Rate % | Wins / Total * 100 | trades.csv pnl_net > 0 |
| BE Hit Count | Trades where SL was at entry (breakeven) | Need: `be_raised` column in trades.csv |
| BE Hit % | BE Hit / Total * 100 | Derived |
| LSG % (Losers Saw Green) | % of losing trades that were profitable at some point | Need: `max_favorable_excursion` or `saw_green` column in trades.csv |
| Sharpe Ratio | mean(daily_returns) / std(daily_returns) * sqrt(365) | Computed from daily PnL |
| Profit Factor | gross_wins / gross_losses | Already exists |
| Max Drawdown $ | Deepest equity valley | Already exists |
| Max Drawdown % | Max DD / peak equity * 100 | New computation |
| Avg Win / Avg Loss ratio | avg_win / abs(avg_loss) | Already exists, reformat |
| Expectancy per trade | (WR * avg_win) + ((1-WR) * avg_loss) | Already exists |
| Net PnL | Total realized profit/loss | trades.csv sum |
| SL Hit % | % of exits via SL | trades.csv exit_reason |
| TP Hit % | % of exits via TP | trades.csv exit_reason |

**BLOCKER — LSG and BE data:**
- `be_raised` is in `state.json` per open position but NOT recorded in `trades.csv` when position closes
- LSG requires knowing if a losing trade was ever profitable — this needs `max_favorable_excursion` (MFE) data, which is NOT currently tracked by the bot
- **Prerequisite:** Modify `state_manager.py` to write `be_raised` to trades.csv on close. For LSG, position_monitor needs to track MFE per position and write it on close.
- **Dashboard v1-2 scope:** Add BE and LSG metric cards with "N/A — data not yet tracked" placeholder. Wire them up once bot writes the data. Sharpe, MaxDD%, and all others computable from existing trades.csv.

**Files:** `bingx-live-dashboard-v1-1.py` — `compute_metrics()` rewrite + analytics tab layout
**Lines:** ~60 changed

### ANALYTICS-2: Date range picker on Analytics tab
See FIX-3 above. Defaults to bot start date (earliest trade in trades.csv). End = now.

### ANALYTICS-3: Charts — add titles, axis labels, dark mode toolbar
**Problem:** Analytics charts show raw plotly toolbar (white icons on dark bg). No axis labels.
**Fix:** Add `config={'displayModeBar': False}` to all `dcc.Graph` components. Add proper titles and axis labels. Consider adding time-axis formatting for readability.
**Files:** `bingx-live-dashboard-v1-1.py` — chart builder functions
**Lines:** ~20 changed

## Summary of Changes

| ID | Severity | Area | Lines Changed |
|----|----------|------|---------------|
| FIX-1 | HIGH | CSS — dark form controls | ~30 (CSS) |
| FIX-2 | HIGH | CSS — ag-grid dark bg | ~10 (CSS) |
| FIX-3 | MEDIUM | Analytics — date range picker | ~30 |
| FIX-4 | HIGH | Layout — render all tabs, toggle visibility | ~80 |
| FIX-5 | LOW | Diagnostics — timing logs | ~10 |
| ANALYTICS-1 | HIGH | Metrics overhaul (Sharpe, LSG, BE, MaxDD%) | ~60 |
| ANALYTICS-2 | MEDIUM | Date range picker | (covered by FIX-3) |
| ANALYTICS-3 | LOW | Chart cleanup | ~20 |

**Total estimated delta:** ~240 lines changed/added

## Files Touched

1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-1.py` — FIX-3, FIX-4, FIX-5, ANALYTICS-1, ANALYTICS-3
2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\assets\dashboard.css` — FIX-1, FIX-2
3. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_dashboard.py` — update tests for new metrics

## Blockers / Dependencies

- **LSG %** requires MFE tracking in position_monitor.py (NOT in dashboard scope — bot change)
- **BE Hit Count** requires `be_raised` written to trades.csv on close (NOT in dashboard scope — bot change)
- Both will show "N/A" in v1-2 until bot changes are made

## Build Order

1. FIX-1 + FIX-2 (CSS only — immediate visual win)
2. FIX-4 (layout restructure — biggest impact on UX)
3. FIX-5 (timing diagnostics)
4. FIX-3 + ANALYTICS-2 (date range picker)
5. ANALYTICS-1 (metrics overhaul)
6. ANALYTICS-3 (chart cleanup)
7. Update test script
8. py_compile both files
