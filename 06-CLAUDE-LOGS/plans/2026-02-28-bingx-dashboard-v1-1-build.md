# Plan: BingX Live Dashboard v1-1 Build

## Context

The complete build spec exists at `C:\Users\User\.claude\plans\goofy-dancing-summit.md` (1795 lines). Previous session finalized the spec but hit context limit before writing any code. This plan executes that spec — no design decisions remain.

## What Gets Built

3 new files in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\`:

1. **`bingx-live-dashboard-v1-1.py`** (~700 lines) — Single-file Dash 4.0 app, port 8051, 5 tabs (Operational, History, Analytics, Coin Summary, Bot Controls), 14 callbacks, ag-grid, dark theme, BingX API integration for position management (Raise BE, Move SL), config editor, halt/resume
2. **`assets/dashboard.css`** (~20 lines) — Dark theme overrides for Dash tabs, row coloring, warning banner
3. **`scripts/test_dashboard.py`** (~170 lines) — Unit tests for all data loaders, builders, validators, chart builders (no Dash server needed)

## Build Steps

1. Load Dash skill (`/dash`) — mandatory per MEMORY.md before any Dash code
2. Write `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-1.py` — full file per spec
3. Write `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\assets\dashboard.css` — content verbatim from spec
4. Write `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_dashboard.py` — full file per spec
5. Run `py_compile` on `bingx-live-dashboard-v1-1.py` (mandatory per MEMORY.md)
6. Run `py_compile` on `scripts/test_dashboard.py` (mandatory per MEMORY.md)
7. Give user the run command (user runs it themselves per MEMORY.md rules)

## Key Technical Decisions (from spec)

- `suppress_callback_exceptions=True` — tab IDs don't exist at startup
- `prevent_initial_call=False` for CB-1 (data loader) and CB-2 (tab renderer) — must fire on load
- `prevent_initial_call=True` for all other callbacks
- CB-6 and CB-7 both output to `pos-action-status` — allowed because different Input triggers
- CB-13 and CB-14 both output to `halt-status` — same reason
- `server = app.server` at module level for gunicorn
- `fetch_all_mark_prices` uses `ThreadPoolExecutor(max_workers=8)` for parallel price fetches
- API signing: replicated `_sign()` pattern (not imported from bot internals)
- Every callback wrapped in try/except, PreventUpdate re-raised before outer except
- Every def has a one-line docstring
- Atomic writes via tmp + `os.replace()`
- Dual logging (file + console) with `TimedRotatingFileHandler`

## Critical Files Referenced

- **Build spec**: `C:\Users\User\.claude\plans\goofy-dancing-summit.md`
- **Existing v1 (Streamlit, DO NOT TOUCH)**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1.py`
- **Bot state**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state.json`
- **Trade log**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\trades.csv`
- **Bot config**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
- **API keys**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\.env`

## Verification

1. `py_compile` passes on both `.py` files
2. User runs `python scripts/test_dashboard.py` — expects "All tests passed"
3. User runs `python bingx-live-dashboard-v1-1.py` — expects `Dash is running on http://127.0.0.1:8051/`
4. `logs/YYYY-MM-DD-dashboard.log` created on startup
5. All 14 callbacks have correct `prevent_initial_call` settings
6. No `st.` or `import streamlit` references anywhere
