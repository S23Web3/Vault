# 2026-02-28 — Dashboard v3.9.3 Validate & Promote

## Summary
Investigated P0.3 (dashboard v3.9.3 BLOCKED — IndentationError). Found the file already compiles clean (py_compile PASS). The backlog entry was stale. Additionally found and fixed a pre-existing silent date filter fallback bug where 7d showed the full year of data instead of warning the user.

## What was done
1. **Confirmed v3.9.3 syntax is valid** — py_compile passes. The IndentationError was already resolved in a prior session.
2. **Added trailing newline** to `dashboard_v393.py` (was missing EOF newline).
3. **Fixed silent date filter fallback** in `apply_date_filter()`:
   - **Root cause**: When `len(df_filtered) < 100`, the function silently returned the FULL unfiltered dataset. For 7d date range where parquet data doesn't extend to recent dates, this meant showing the entire year with no warning.
   - **Fix**: Removed the `< 100` silent fallback. Function now always returns filtered data.
   - Added explicit warnings at 3 call sites:
     - Single-coin backtest (line ~727): `st.warning` + `st.stop()` when < 200 bars after filter
     - Sweep detail (line ~1640): Same pattern
     - Sweep incremental (line ~1540): `raise ValueError` caught by existing `except` to skip coin
     - Portfolio loop: Warning when all coins skipped due to date range
4. **User runtime validated**: Dashboard loads, portfolio runs, 30d works correctly. 7d now shows proper warning instead of misleading full-year chart.

## Files modified
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py`

## Changes (4 edits)
1. `apply_date_filter()` (line 294): Removed `if len(df_filtered) < 100: return df`
2. Single-coin path (line ~727): Added `< 200` bars warning after `apply_date_filter`
3. Sweep detail path (line ~1640): Same warning
4. Sweep incremental (line ~1540): `raise ValueError("Insufficient bars after date filter")`
5. Portfolio (line ~1949): Warning when `not coin_results` and `date_range` is set

## Status
- v3.9.3: py_compile PASS, runtime validated, promoted to PRODUCTION
- v3.9.2: remains as stable fallback
