# Next Chat Continuation Prompt (v2 — audited)
Date: 2026-03-05

## Paste this at the start of the next chat:

---

## CONSTRAINT: Bot is RUNNING -- DO NOT RESTART
Bot launched 2026-03-04, collecting live trading data. Needs minimum 48h uninterrupted.
DO NOT modify or restart bot core files: main.py, position_monitor.py, signal_engine.py,
state_manager.py, ws_listener.py, config.yaml. Dashboard-only work is safe.

---

We are continuing work on the BingX trading bot + backtester dashboard.
Read the session log at:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-05-bingx-bot-session.md`

And the plan at:
`C:\Users\User\.claude\plans\sparkling-doodling-hare.md`

## What was completed last session
- Three-stage position management: be_act=0.004, ttp_act=0.008, ttp_dist=0.003
- orderId extraction fix in 3 places in position_monitor.py
- Unrealized PnL added to Telegram daily summary and hourly warning
- 25/25 test pass on three-stage logic
- max_positions raised to 25

## What to build next

### Task 1: dashboard_v395.py (backtester dashboard with v384 live preset)

Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v395.py`
Base file: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py`
Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v395.py`

Changes needed (safe_replace patches):
1. Add `require_stage2` checkbox to sidebar signal logic section (currently missing)
2. Add `rot_level` slider (range 50-100, step 1, default 80) to sidebar
3. Add "Load v384 Live Preset" button that calls st.session_state to set:
   - cross_level=25, zone_level=30, atr_length=14
   - allow_b=True, allow_c=False
   - require_stage2=True, rot_level=80
   - sl_mult=2.0, tp_mult=0 (disabled)
4. **ADD PARAMS TO v383 PIPELINE** (do NOT switch imports -- keep compute_signals_v383):
   - Patch `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\state_machine_v383.py` -- add `require_stage2` (bool, default False) and `rot_level` (int, default 80) kwargs to `__init__` and wire into signal logic
   - Patch `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` -- pass `require_stage2` and `rot_level` from params dict through to FourPillarsStateMachine383 constructor
   - Reference implementation: `signals/four_pillars.py` lines 60-61 and `signals/state_machine.py` already have working require_stage2/rot_level logic -- mirror that into the v383 versions
   - Dashboard keeps calling `compute_signals_v383()` as before -- no import change needed
5. Wire require_stage2 and rot_level into sig_params dict (dashboard_v394.py ~line 716-728) that is passed to compute_signals_v383()

py_compile + ast.parse must pass before delivering.
Run command: streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v395.py"

### Task 2: Dashboard v1.5 -- be_act settings patch

v1.5 already EXISTS (`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py`, built 2026-03-04). Patches P3-A through P3-H already applied.
BUG-4 (recvWindow), BUG-1b (reduceOnly), BUG-2 (analytics period), BUG-5 (coin summary) are ALL FIXED.

**Only remaining issue**: `be_act` is not in the dashboard settings save callback. Dashboard writes `ttp_act` but not `be_act` to config. User can't change breakeven activation threshold from the UI.

Scope: Add `be_act` numeric input to Strategy Parameters tab + wire into the settings save callback alongside `ttp_act`.

Build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_5_patch1.py`
Base: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py`

## Bot is currently RUNNING
Log dir: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\`
State: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state.json`
Check current bot state by reading latest log entries and state.json before taking any action.

## Key files
- Bot config: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
- Bot plugin: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py`
- Signal code (shared): `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars.py`
- Dashboard base (backtester): `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py`
- Dashboard base (live): `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py`
- position_monitor.py: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
