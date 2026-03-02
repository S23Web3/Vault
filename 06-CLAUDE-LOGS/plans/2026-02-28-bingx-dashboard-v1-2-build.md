# Plan: BingX Dashboard v1-2 Build

## Context
User tested v1-1 live on 2026-02-28 and filed 8 issues (white form inputs, white ag-grid bg, no date range picker, slow tab switching, no timing diagnostics, amateur analytics metrics, missing plotly cleanup). This plan implements all 8 fixes as a build script that produces 3 files.

## Deliverables
One build script (`scripts/build_dashboard_v1_2.py`) that creates:

| # | File | Action |
|---|------|--------|
| 1 | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\assets\dashboard.css` | Overwrite (28 -> ~95 lines) |
| 2 | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-2.py` | New file (~1750 lines) |
| 3 | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_dashboard.py` | Overwrite with v1-2 references + new tests |

Each file gets `py_compile` validation (CSS skipped -- not Python).

## Changes by Fix ID

### FIX-1: Dark form inputs (CSS only)
Add CSS rules for `input[type="number"]`, `input[type="text"]`, `.dash-radio label`, `.dash-checklist label`, `.Select-control`, `.Select-menu-outer`, `.Select-option`, `.Select-value-label`, `.DateRangePickerInput`, `.DateInput_input`, `.CalendarDay__default`, `.CalendarDay__selected`. All use `#161b22` bg, `#c9d1d9` text, `#30363d` border.

### FIX-2: Dark ag-grid backgrounds (CSS only)
Add CSS rules for `.ag-root-wrapper`, `.ag-overlay-no-rows-wrapper`, `.ag-header` -- all `#0d1117` or `#161b22` backgrounds.

### FIX-3: Date range pickers on Analytics + History
- **History tab**: Remove `dcc.Checklist(id='hist-today-filter')`. Add `dcc.DatePickerRange(id='hist-date-range')`. Update CB-8 to accept `start_date`/`end_date` inputs instead of `today_filter`. Empty dates = all trades.
- **Analytics tab**: Add `dcc.DatePickerRange(id='analytics-date-range')` at top. Update CB-9 to accept `start_date`/`end_date` inputs. Filter trades DataFrame before `compute_metrics()`. Empty dates = all trades.

### FIX-4: Render all tabs at startup, toggle visibility
- **Layout**: Replace `html.Div(id='tab-content')` with 5 wrapper divs (`tab-content-ops` through `tab-content-controls`), each calling its `make_*_tab()` builder. Only `tab-content-ops` starts visible (`display: block`), others hidden (`display: none`).
- **CB-2**: Delete server-side `render_tab()`. Replace with `app.clientside_callback()` that toggles `style` on all 5 wrapper divs based on `main-tabs` value. Pure JS, zero server round-trip.
- **`suppress_callback_exceptions`**: Keep `True` -- CB-5 still creates `raise-be-btn`/`move-sl-btn`/`new-sl-input` dynamically.
- **Child callbacks**: All keep `prevent_initial_call=True` -- they fire when CB-1 populates stores, not on layout render.

### FIX-5: Timing diagnostics in CB-1
Add `time.time()` markers around `load_state()`, `load_trades()`, `load_config()`. Single `LOG.debug()` line with all 4 timings (state, trades, config, total).

### ANALYTICS-1: Professional metrics
Rewrite `compute_metrics()` to return expanded dict:
- **Keep**: total, win_rate, profit_factor, avg_win, avg_loss, expectancy, max_dd, gross_pnl
- **Add**: net_pnl, sharpe (annualized from daily PnL, sqrt(365)), max_dd_pct (dd/peak*100), avg_win_loss_ratio, sl_hit_pct, tp_hit_pct, be_hit_count, be_hit_pct, lsg_pct
- **BE and LSG**: Return `"N/A"` unless `be_raised` / `saw_green` columns exist in trades.csv (they don't yet -- bot change required separately)
- **Analytics cards**: Expand from 7 to 13 cards (Total, Net PnL, Win Rate, PF, Sharpe, MaxDD$, MaxDD%, Expectancy, W/L Ratio, SL%, TP%, BE Hits, LSG%)
- **Grade comparison**: Add Sharpe column

### ANALYTICS-3: Chart cleanup
- Add `config={'displayModeBar': False}` to all 4 `dcc.Graph` components in `make_analytics_tab()`
- Add `xaxis_title` to equity, drawdown, exit reason, daily PnL charts where missing

## Section-by-Section Delta (v1-1 -> v1-2)

| Section | v1-1 Lines | Action |
|---------|-----------|--------|
| Docstring | 1-19 | Edit version to v1-2 |
| Imports | 20-41 | Add `import math` |
| Path constants -> API signing | 44-156 | Verbatim |
| Data loaders | 158-258 | Verbatim |
| Data builders | 260-319 | Verbatim |
| `compute_metrics()` | 321-352 | **REWRITE** (ANALYTICS-1) |
| `build_coin_summary()` | 355-383 | Verbatim |
| Chart builders | 386-468 | Add axis labels (ANALYTICS-3) |
| Layout helpers + col defs | 471-551 | Verbatim |
| `make_operational_tab()` | 558-583 | Verbatim |
| `make_history_tab()` | 586-607 | **REPLACE** filter bar (FIX-3) |
| `make_analytics_tab()` | 610-626 | **REPLACE** date picker + displayModeBar (FIX-3, ANALYTICS-3) |
| `make_coin_summary_tab()` | 629-646 | Verbatim |
| `make_bot_controls_tab()` | 649-739 | Verbatim |
| Config validation + state write | 742-803 | Verbatim |
| Dash app init + layout | 805-839 | **REPLACE** (FIX-4: all tabs in layout) |
| CB-2 render_tab | 877-894 | **DELETE** -> clientside callback |
| CB-1 data loader | 850-871 | **REPLACE** body (FIX-5: timing) |
| CB-3 through CB-7 | 901-1220 | Verbatim |
| CB-8 history grid | 1227-1290 | **REPLACE** signature + filter (FIX-3) |
| CB-9 analytics | 1297-1377 | **REPLACE** signature + cards (FIX-3, ANALYTICS-1) |
| CB-10 through CB-14 | 1384-1635 | Verbatim |
| Entry point | 1638-1645 | Verbatim |

## Gotchas Identified
1. `suppress_callback_exceptions` must stay `True` -- CB-5 creates button IDs dynamically
2. `hist-today-filter` component removed -- only CB-8 references it, and CB-8 is updated
3. Date pickers default to `None` -- callbacks treat `None` as "no filter" (show all trades)
4. `gross_pnl` kept as alias for `net_pnl` in `compute_metrics()` -- grade comparison table uses this key
5. String formatting in build script uses `.format()` not f-strings to avoid escaped quote rule
6. `math.sqrt(365)` for Sharpe annualization -- `math` import required

## Build Order
1. Write CSS file (FIX-1 + FIX-2)
2. Write dashboard v1-2 file (all Python changes)
3. py_compile dashboard
4. Write test script
5. py_compile test script
6. Print summary

## Verification
1. Run build: `python scripts/build_dashboard_v1_2.py`
2. Run tests: `python scripts/test_dashboard.py`
3. Run dashboard: `python bingx-live-dashboard-v1-2.py`
4. Visual checks:
   - Bot Controls tab: all inputs have dark backgrounds
   - Positions grid "No Rows" overlay: dark background
   - Tab switching: instant, no reload flash
   - Analytics tab: 13 metric cards, date range picker, no plotly toolbar
   - History tab: date range picker instead of "Today only" checkbox
   - Console: timing diagnostics on each data load
