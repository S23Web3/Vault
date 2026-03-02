# Plan: Dashboard v3.9.3 — Validate and Promote

## Context

Product backlog (P0.3) says Dashboard v3.9.3 is BLOCKED with "IndentationError at line 1972". Investigation reveals this is **stale** — `py_compile` passes clean on the current file. The v3.9.3 file has correct syntax and the indentation fix was completed at some point after the backlog entry was written.

**The actual remaining work is: runtime validation + doc updates.**

## What v3.9.3 Changes (vs v3.9.2)

1. **Stale cache fix** (the original bug): When sidebar settings change, `_pd` is set to `None` and the entire portfolio rendering block is guarded by `if _pd is not None:`. Previously, stale equity curves would display from a previous date range.
2. **Sweep symbol persistence**: Uploaded custom symbol lists now survive across Streamlit rerenders.
3. **Selectbox key fix**: `sweep_drill_select` key prevents widget ID collisions.
4. **PDF download button**: Added in-browser download after PDF generation (not just file save).

## Files

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py` (2383 lines, py_compile PASS)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v392.py` (2371 lines, current production)

## Steps

### 1. Runtime validation (user runs manually)

Run:
```
streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py"
```

Test checklist:
- [ ] Dashboard loads without error
- [ ] Single-coin backtest runs and displays chart
- [ ] Portfolio backtest runs and displays equity curve
- [ ] Change date range in sidebar -> old equity curve clears, info message shown
- [ ] Re-run portfolio after settings change -> new results display correctly
- [ ] Sweep tab: upload custom symbol list -> symbols persist after rerender
- [ ] PDF export generates file and shows download button

### 2. Update docs (if runtime passes)

Files to update:
- `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md` — Move P0.3 to Completed table
- `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md` — Change Dashboard version from v3.9.2 to v3.9.3 PRODUCTION
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-FILES.md` — Update version status
- `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md` — Update dashboard version in status table, remove from Active Blockers

### 3. Add trailing newline

v3.9.3 is missing a trailing newline at end of file (diff shows `\ No newline at end of file`). Add one.

### 4. Clean up dead fix scripts

These scripts are no longer needed (the fix is already applied):
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v393.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v393_fix.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fix_v393_indentation.py`

**Ask user** before deleting — they may want to keep for reference.

## Verification

The only real verification is Step 1: run the dashboard with `streamlit run` and go through the test checklist. py_compile already passes. If runtime tests pass, the fix is confirmed and we update docs.
