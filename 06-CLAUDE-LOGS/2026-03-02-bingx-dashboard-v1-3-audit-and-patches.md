# 2026-03-02 — BingX Dashboard v1-3 Audit + Patches

## Context
Continued from previous session (context limit). v1-3 build script had been written but user feedback showed remaining issues.

## Actions

### 1. Ran build_dashboard_v1_3_final.py
- User ran from correct directory, all patches applied
- Only FAIL was Max DD% cap (already applied from previous build_dashboard_v1_3.py) -- expected

### 2. Full Code Audit (1805 lines + 180 CSS)
Read entire `bingx-live-dashboard-v1-3.py` + `assets/dashboard.css`. Found 6 issues:

| # | Severity | Issue |
|---|----------|-------|
| B1 | LOW | Duplicate `import io` on line 27 |
| B2 | MEDIUM | `pos_df["Unreal PnL"].sum()` can choke on `None` values (needs `pd.to_numeric`) |
| B3 | LOW | Move SL validation blocks trailing above entry for BE-raised positions |
| B4 | MEDIUM | CB-10 uses `State('store-trades')` instead of `Input` -- Coin Summary blank until radio clicked |
| B5 | LOW | ISO week filter edge case at year boundary |
| B6 | LOW | `gross_pnl` = alias for `net_pnl` in compute_metrics (confusing key name) |

### 3. Patch 1 (build_dashboard_v1_3_patch.py) -- B1 + B2 + B4
- Removed duplicate import io
- Wrapped Unreal PnL sum in `pd.to_numeric(..., errors="coerce")`
- Changed CB-10 State -> Input for store-trades
- ALL PASSED, py_compile OK

### 4. User Tested Live -- 5 Remaining Visual Issues
From screenshots:
1. Status bar still says "Realized PnL" -- user wants equity (realized + unrealized combined)
2. History + Analytics date pickers still white
3. Equity curve doesn't include open positions (unrealized PnL)
4. Grade comparison table has white background rows
5. Coin Summary table has white background rows

### 5. Data Discrepancy Identified
User noted analytics numbers differ from `analyze_trades.py`. Root cause: `analyze_trades.py` filters to Phase 3 only ($50 notional live trades). Dashboard shows ALL 196 trades including Phase 1 ($500 demo) + Phase 2 ($1500 demo) which had unreliable exit tracking.

### 6. Patch 2 (build_dashboard_v1_3_patch2.py) -- WRITTEN, NOT YET RUN
Fixes:
- F1: CB-3 status bar -- adds "Equity" card (realized + unrealized), renames "Realized PnL" -> "Realized", "Unreal. PnL" -> "Unrealized"
- F2: CSS -- ID-based `#hist-date-range input` / `#analytics-date-range input` selectors (force dark). AG Grid CSS custom properties (`--ag-background-color`, `--ag-odd-row-background-color`, etc.) for dark rows on ALL grids.
- F3: CB-9 -- adds `Input('store-unrealized')`, extends equity curve with dashed blue line from last closed-trade equity to current equity+unrealized. Only shown in all-time view (no date filter).

## Files Written
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch.py` -- B1+B2+B4 fixes (RUN, ALL PASS)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch2.py` -- F1+F2+F3 fixes (NOT YET RUN)

### 7. Position Reconciliation Added (F4)
User reported dashboard shows 6 open positions but BingX has 0. Root cause: `state.json` has stale positions from Feb 27-28 that were closed on the exchange while bot wasn't running. Dashboard reads state.json blindly.

Fix added to patch2: `reconcile_positions()` function calls `GET /openApi/swap/v2/user/positions` (same endpoint bot's `state_manager.reconcile()` uses). Builds set of live position keys from exchange response. Removes any state.json positions not on exchange. Atomic `_write_state()` cleans the file.

Called in CB-4 on every refresh cycle (60s). Phantom positions auto-cleaned on first load.

## Next Steps
1. User runs: `python scripts/build_dashboard_v1_3_patch2.py`
2. User runs dashboard: `python bingx-live-dashboard-v1-3.py`
3. Visual verification: dark date pickers, dark grid rows, equity card, no phantom positions
4. Future: add Phase filter to dashboard (or default to Phase 3) to match analyze_trades.py numbers
