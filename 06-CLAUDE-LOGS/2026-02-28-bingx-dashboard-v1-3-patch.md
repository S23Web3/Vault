# 2026-02-28 — BingX Dashboard v1-3 Patch Build

## Context
User ran v1-2 build script, tested dashboard live, reported 11 visual/calculation issues via screenshots.

## Issues Triaged (from user feedback)
1. White selected tab — CSS selectors didn't match Dash's actual class names
2. History tab all white — DatePickerRange + Dropdown internal classes not covered
3. Analytics date picker white + full width — same CSS issue + no maxWidth
4. Input fields too dark (low contrast) — bg #161b22 indistinguishable from body #0d1117
5. Number input +/- spinners white — browser native stepper unstyled
6. Grade comparison white bg + left-aligned — no container styling
7. Max DD% = -233.87% — peak equity was small (~$5), DD was large, ratio blew up
8. pd.read_json deprecation warning — passing literal JSON string, needs StringIO wrapper
9. "Daily PnL" label ambiguous — user confused it with equity (realized+unrealized)
10. Bot Controls white buttons/spinners — same CSS coverage gap
11. LSG% and BE Hits N/A — EXPECTED: trades.csv missing `be_raised` and `saw_green` columns (bot-side fix, not dashboard)

## Build Script
- **File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3.py`
- **Approach**: Reads v1-2, applies 15 text replacements + 1 section replacement, writes v1-3
- **py_compile**: PASS

## Changes Applied (P1-P10)
- P1: Added `className='dash-tab'` + `selected_className='dash-tab--selected'` to all 5 `dcc.Tab` components. Added `className='dash-tabs'` to `dcc.Tabs`. CSS targets `.dash-tab`, `.tab`, `.custom-tab` and selected variants.
- P2: CSS expanded from ~95 to ~270 lines. Comprehensive coverage: AG Grid (header, row, cell, pagination, filter popup), DatePickerRange (all calendar internal classes), Dropdown (all React-Select classes), scrollbar.
- P3: Input bg changed from `#161b22` to `#21262d`. Border from `#30363d` to `#484f58`. Focus glow added (blue box-shadow).
- P4: `input[type="number"]::-webkit-inner-spin-button { filter: invert(0.8); }`
- P5: Analytics date picker div gets `maxWidth: 500px`.
- P6: Grade comparison container gets `maxWidth: 800px`.
- P7: `compute_metrics` max_dd_pct: added `peak_at_dd >= 1.0` guard (skip when peak too small), capped at -100.0%.
- P8: `pd.read_json(trades_json, ...)` → `pd.read_json(io.StringIO(trades_json), ...)` in CB-8, CB-9, CB-10. Added `import io`.
- P9: Status bar card renamed from "Daily PnL" to "Realized PnL".
- P10: Version bump v1-2 → v1-3 (docstring, title, run command, gunicorn).

## Output Files (created by build script)
1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-3.py`
2. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\assets\dashboard.css` (~270 lines)
3. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_dashboard.py` (updated refs + max_dd_pct test)

## Status
Build script written and py_compile OK. NOT YET RUN by user.

## Next Steps
1. User runs: `cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector" && python scripts/build_dashboard_v1_3.py`
2. User runs tests: `python scripts/test_dashboard.py`
3. User runs dashboard: `python bingx-live-dashboard-v1-3.py`
4. Visual verification of all 10 fixes
5. Future: bot-side fix to write `be_raised` + `saw_green` to trades.csv on trade close (enables BE Hits + LSG% metrics)
