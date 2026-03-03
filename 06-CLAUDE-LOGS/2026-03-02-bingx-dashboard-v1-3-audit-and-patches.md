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

## Session Continuation (2026-03-02 afternoon)

### Patches Applied This Session
| Script | Status | What |
|--------|--------|------|
| build_dashboard_v1_3_patch2.py | PARTIAL | F4 reconciliation PASS; F1/F3 already applied from earlier build |
| build_dashboard_v1_3_patch3.py | PASS | Balance/Equity/Unrealized from API (GET /openApi/swap/v3/user/balance) |
| build_dashboard_v1_3_patch4.py | NOT RUN | Superseded by patch5 |
| build_dashboard_v1_3_patch5.py | PASS | Date filter, stale session, coin detail, CSS improvements |

### Working After Patches
- Status bar shows Balance $101.80 / Equity $101.80 / Unrealized $+0.00 from API
- Positions 0/8, phantoms removed by reconciliation
- Daily Trades 0/50 / Risk Used 0% -- stale session detection working
- 72 trades shown (filter >= 2026-02-27)
- Dropdowns dark, menus dark

### ROOT CAUSE: White Backgrounds (asked 7 times this session)
**Dash 2.x uses CSS custom properties (CSS variables) in dcc.css.**
Seen in DevTools on `:root`:
```
--Dash-Fill-Inverse-Strong: #fff   <- THE WHITE
--Dash-Text-Primary: rgba(0, 18, 77, 0.87)
--Dash-Fill-Interactive-Strong: #7f4bc4
```
Class-name CSS and !important do NOT override CSS variables. Must override at :root.

**PATCH 6 FIX -- append to dashboard.css:**
```css
:root {
    --Dash-Fill-Inverse-Strong: #21262d !important;
    --Dash-Fill-Inverse-Weak: rgba(33, 38, 45, 0.9) !important;
    --Dash-Fill-Interactive-Weak: rgba(33, 38, 45, 0.5) !important;
    --Dash-Fill-Primary-Hover: rgba(88, 166, 255, 0.1) !important;
    --Dash-Fill-Primary-Active: rgba(88, 166, 255, 0.2) !important;
    --Dash-Text-Primary: #c9d1d9 !important;
    --Dash-Text-Weak: #8b949e !important;
    --Dash-Stroke-Strong: #484f58 !important;
    --Dash-Stroke-Weak: rgba(72, 79, 88, 0.3) !important;
    --Dash-Fill-Interactive-Strong: #58a6ff !important;
    --Dash-Text-Disabled: #484f58 !important;
}
```

### Feature Request: Bot Status Feed
User wants live status messages in dashboard: "Connecting", "Connected", "Reading candles", "Warmup 50/100", "Loaded strategy parameters", "Connected 100%". Requires bot to write startup steps to a status file the dashboard polls, OR a status endpoint.

### Next Steps for New Chat
1. Apply patch6: override Dash CSS variables at :root in dashboard.css
2. Plan and build bot status feed feature
3. Version as v1-4 once all visual issues resolved

## Session Continuation (2026-03-02 evening)

### Patches Built This Session
| Script | Status | What |
|--------|--------|------|
| build_dashboard_v1_3_patch6.py | BUILT, NOT YET RUN | Appends :root CSS variables block to dashboard.css |
| build_dashboard_v1_3_patch7.py | BUILT, NOT YET RUN | Bot status feed (main.py + data_fetcher.py + dashboard + CSS) |

### Patch 6 Details
- Script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch6.py`
- Changes: `assets/dashboard.css` only (append :root block)
- Guard: checks for `--Dash-Fill-Inverse-Strong` before appending (idempotent)
- py_compile: N/A (CSS only)
- Run: `python scripts/build_dashboard_v1_3_patch6.py`

### Patch 7 Details
- Script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch7.py`
- Changes 4 files:
  - `main.py`: `write_bot_status()` helper + `STATUS_PATH` constant + 7 call sites + clear-on-start
  - `data_fetcher.py`: `progress_callback=None` param added to `warmup()`, fires every 5 symbols
  - `bingx-live-dashboard-v1-3.py`: `store-bot-status`, `status-interval` (5s), status panel in Ops tab, CB-S1 + CB-S2
  - `assets/dashboard.css`: `.status-feed-panel` + `.status-ts` styles
- `bot-status.json`: cleared on bot start, appended atomically (temp+os.replace)
- Dashboard polls every 5s, shows newest-first, max 20 messages, "Bot offline" if file missing
- py_compile: both main.py and dashboard checked
- Run: `python scripts/build_dashboard_v1_3_patch7.py`

### analyze_trades.py note
Not relevant to either patch. It reads trades.csv and generates performance reports -- no overlap with CSS or status feed.

### Run Order
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch6.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_3_patch7.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-3.py"
```

## Session Continuation (2026-03-02 v1-4 build)

### v1-4 Requirements (from user AFK messages)

1. Rename "Operational" tab -> "Live Trades"
2. Rename "Bot Controls" tab -> "Strategy Parameters"
3. New "Bot Terminal" tab with Start/Stop bot + lifecycle messages
4. Tab order: Live Trades -> Bot Terminal -> Strategy Parameters -> History -> Analytics -> Coin Summary
5. Bot launch spawns new cmd window (subprocess.CREATE_NEW_CONSOLE) + shows status in browser
6. Activity feed = curated English messages from bot-status.json (same CB-S1/CB-S2 feeds)
7. Output: new file `bingx-live-dashboard-v1-4.py` (v1-3 NOT overwritten)

### Audit Findings (executor.py + position_monitor.py)

- Full read of both files completed (313 lines + 533 lines)
- Bugs reported in previous session summary are NOT present in current files
- executor.py: sl_price/tp_price set correctly, act_price assigned, logic flow correct
- position_monitor.py: return None,None correctly scoped, _handle_close indented inside loop
- Conclusion: both files appear clean; no changes needed

### Build Script Written

- Script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4.py`
- 15 safe_replace patches (P1-P14 including P3b)
- Reads v1-3, writes v1-4 (does NOT overwrite v1-3)
- py_compile validation of build script: PASS
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py`

### What v1-4 Changes

| Patch | Change |
|-------|--------|
| P1-P3b | Docstring updated (title, tabs, run cmd, gunicorn) |
| P4 | `import subprocess` added |
| P5 | `BOT_PID_PATH = BASE_DIR / "bot.pid"` added |
| P6 | `_is_bot_running()`, `_start_bot_process()`, `_stop_bot_process()` helpers |
| P7 | `make_operational_tab` -> `make_live_trades_tab`, Bot Status section removed |
| P8 | `make_bot_terminal_tab()` added (Start/Stop buttons + status-feed div) |
| P9 | `make_bot_controls_tab` -> `make_strategy_params_tab` |
| P10 | App title updated |
| P11 | 6-tab dcc.Tabs list with new order and labels |
| P12 | 6-tab content divs, renamed function calls |
| P13 | CB-2 clientside JS updated for 6 tabs |
| P14 | CB-T1 (start), CB-T2 (stop), CB-T3 (poll) added |

### Bot Terminal Design

- `_is_bot_running()`: PID file check + `tasklist /FI PID eq {pid} /NH`
- `_start_bot_process()`: `subprocess.Popen(["python", "main.py"], creationflags=CREATE_NEW_CONSOLE)`
- PID written to `bot.pid`, read on stop/check
- All 3 CB-T callbacks use `allow_duplicate=True` on shared outputs
- CB-T3 fires on `status-interval.n_intervals` (5s) -- no `prevent_initial_call` so button state initializes on load
- CB-T1/CB-T2 have `prevent_initial_call=True`

### Run Command

```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py"
```

## Session Continuation (2026-03-03 — audit + patch1 + skill update)

### Build Script Audit — 15/15 PASS

Full anchor verification of `build_dashboard_v1_4.py` against `bingx-live-dashboard-v1-3.py`:

| Patch | v1-3 location | Result |
| ----- | ------------- | ------ |
| P1 | Line 2 — docstring title | PASS |
| P2 | Line 5 — tabs list | PASS |
| P3 | Line 11 — run command | PASS |
| P3b | Line 15 — gunicorn module | PASS |
| P4 | Line 23 — `import threading\n` | PASS |
| P5 | Line 54 — `LOG_DIR = BASE_DIR / "logs"` | PASS |
| P6 | Line 136 — `LOG.info("Dashboard starting...")` | PASS |
| P7 | Lines 708-740 — full `make_operational_tab()` | PASS |
| P8 | Line 743 — `def make_history_tab()` | PASS |
| P9 | Lines 828-829 — `make_bot_controls_tab` def | PASS |
| P10 | Line 991 — app title | PASS |
| P11 | Lines 1012-1021 — dcc.Tabs 5-tab block | PASS |
| P12 | Lines 1023-1033 — tab content divs | PASS |
| P13 | Lines 1080-1103 — clientside callback | PASS |
| P14 | Lines 2080-2082 — entry point comment | PASS |

Logic/dependency order verified correct. No anchor conflicts between patches.

### v1-4 Crash — CB-T3 allow_duplicate + prevent_initial_call

**Error**: `DuplicateCallback: allow_duplicate requires prevent_initial_call to be True`

**Root cause**: CB-T3 used `allow_duplicate=True` with no `prevent_initial_call`. Dash requires one of:

- `prevent_initial_call=True` — skip initial fire, allow duplicate registration
- `prevent_initial_call='initial_duplicate'` — fire on load AND allow duplicate

CB-T3 needs to fire on load to initialize button state. Fix: `prevent_initial_call='initial_duplicate'`.

**Fix applied**:

- `build_dashboard_v1_4.py` P14_NEW corrected (future reruns produce correct output)
- `build_dashboard_v1_4_patch1.py` written — patches the existing v1-4 file in place

```bash
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch1.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py"
```

### Dash Skill Updated — v1.3

`C:\Users\User\.claude\skills\dash\SKILL.md` PART 5 added (9 sections, ~300 lines):

- Dark theme: Dash 2.x CSS variable root override — root cause of all white backgrounds across v1–v1.3
- Dark theme: Component CSS selectors — dcc.Tab class names, AG Grid vars, DatePickerRange, number spinners
- All-tabs-rendered + clientside toggle — instant tab switching pattern, suppress_callback_exceptions
- allow_duplicate rules — confirmed crash v1-4, both valid prevent_initial_call options documented
- pd.read_json + StringIO — pandas 2.x deprecation fix
- Bot process management — CREATE_NEW_CONSOLE + PID tracking + 3-callback pattern
- Bot status feed — atomic JSON write, CB-S1/CB-S2 poll-and-render, CSS
- Hyphenated filename import — importlib for test scripts
- Metrics traps — max DD% guard for small peak equity, Sharpe formula
