# Dashboard v3.1 Build Log
**Date**: 2026-02-14 15:06 UTC
**Session**: Dashboard v3.1 -- Date Range + Stress Test + Portfolio Mode

## Summary
Patched `scripts/dashboard.py` (1520 -> 1893 lines) with 15 surgical patches via `scripts/build_dashboard_v31.py`. Added 3 features: date range filtering, stress test (worst drawdowns), and portfolio mode.

## Pre-work: 7 Critical Fixes (from prior session)
Applied 7 operational logic fixes before v3.1 build:
- C-1: Mark-to-market equity curve (unrealized P&L from open positions)
- C-2: Prorated entry commission on scale-outs
- C-3: Removed cost_per_side backdoor from CommissionModel
- C-4: Removed duration_bars look-ahead leak from ML feature columns
- C-5: Fixed daily_turnover look-ahead with shift(1)
- C-6: Wired purged k-fold CV into walk-forward ML training
- C-7: Switched ML training labels to commission-aware label_trades_by_pnl

## v3.1 Features Added

### 1. Date Range Filter
- Sidebar widget: All | 7d | 30d | 90d | 1y | Custom
- Custom mode: date_input start/end pickers
- Applied in single, sweep, and sweep_detail modes
- Integrated into params_hash so different date ranges get different sweep progress

### 2. Stress Test (Worst Drawdowns)
- Expander in Tab 1 after Capital Utilization
- Slider: 1-5 drawdown windows (default 3)
- Auto-detects worst non-overlapping drawdown windows
- Re-backtests on each window: Trades, WR, Net, PF, LSG%, Avg Capital
- Best vs Worst capital moments side-by-side

### 3. Portfolio Mode
- New mode: "Portfolio Analysis" button in sidebar
- Coin selection: Top N | Lowest N | Random N | Custom
- Runs backtest per coin with progress bar
- Aligned equity curves (union DatetimeIndex, forward-fill)
- Portfolio summary: Net P&L, Max DD%, Peak Capital, Total Trades
- Best vs Worst capital allocation moments
- LSG% per coin table
- Portfolio equity curve (bold) + per-coin overlays (thin)
- Capital utilization over time chart
- Equity change correlation matrix

## Files

| File | Action | Lines |
|------|--------|-------|
| scripts/dashboard.py | EDITED (15 patches) | 1520 -> 1893 |
| scripts/build_dashboard_v31.py | CREATED | 626 |
| scripts/test_dashboard_v31.py | CREATED | ~430 |

## Test Results
- test_dashboard_v31.py: 21/21 PASS
- build_dashboard_v31.py --dry-run: 15/15 anchors, 0 missing
- build_dashboard_v31.py: APPLIED, py_compile PASS

## Bugs Found & Fixed During Audit
1. P10b: Date filter inserted before null guard -> moved INSIDE existing if-block
2. Test T2: Expected ~2880 bars but inclusive range gives ~4320 -> fixed assertion
3. Test T4: Expected fallback but 1440 bars > 100 threshold -> redesigned test with smaller df
4. Escaped quotes in f-strings (10 instances) -> refactored to temp variables
5. Missing py_compile after file write -> added with PASS/FAIL reporting
6. Missing docstrings (4 functions) -> added

## Run Command
```
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py"
```
