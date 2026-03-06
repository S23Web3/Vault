# Batch 17 Findings — Auto-Generated Plans (Part 1)

**Files processed:** 20
**Date processed:** 2026-03-06

---

## async-watching-balloon.md

**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to finalize the Vince v2 concept and build Vince as a unified Dash application. Establishes architectural philosophy: Vince is the app, dashboard serves Vince (not vice versa). Existing Streamlit dashboard (scripts/dashboard_v392.py, 2500 lines, 5 tabs) to be replaced. Documents coherence fixes already applied to the concept doc on 2026-02-27. Lists what still needs to be added (GUI section + architecture skeleton) before the concept doc can be locked as APPROVED FOR BUILD.

Specifies 8-panel layout for the Dash app (Coin Scorecard, PnL Reversal Analysis, Constellation Query, Exit State Analysis, Trade Browser, Settings Optimizer, Validation, Session History). Build order B1–B10 defined. Full file structure with vince/ directory detailed. Existing code reuse table provided (backtester_v384, signals/four_pillars_v383_v2, etc.).

### Decisions recorded
- Framework: Plotly Dash
- Architecture: Vince is the app, dashboard serves Vince
- Agent (RL/LLM): future iteration — API skeleton built now
- Scope: core analysis engine + Dash GUI first, RL/LLM/agent = later phases
- Panel 2 (PnL Reversal Analysis) designated highest build priority
- B1 through B10 build order locked

### State changes
- Concept doc coherence fixes applied (filename, symbol in trade_schema, RL state vector, list type annotations)
- Two sections still needed before doc can be approved: GUI section + architecture skeleton
- No Python built yet — plan only

### Open items recorded
- Add GUI section to VINCE-V2-CONCEPT-v2.md
- Add architecture skeleton to VINCE-V2-CONCEPT-v2.md
- Change concept doc status to APPROVED FOR BUILD after above

### Notes
None.

---

## atomic-crunching-sundae.md

**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to update the Vince v2 concept doc with 7 ML findings from 202 YT transcript analysis session (output: `06-CLAUDE-LOGS/plans/2026-02-27-yt-channel-ml-findings-for-vince.md`). Also begins P1.7: formal plugin interface spec (first concrete Vince build artifact).

10 specific edits planned to VINCE-V2-CONCEPT-v2.md covering: elevating Panel 2 as highest priority, adding RL Exit Policy Optimizer as new component, expanding Mode 2 with XGBoost feature importance + unsupervised clustering + bootstrap validation, adding walk-forward methodology to Mode 3, random dataset sampling strategy, expanded RL action space (4 actions: HOLD/EXIT/RAISE_SL/SET_BE), intra-candle context, survivorship bias note, reflexivity caution, new open question on RL training.

Two deliverables for P1.7:
1. `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` (prose spec for StrategyPlugin ABC)
2. `strategies/base_v2.py` (Python ABC stub)

Explicit instruction: do NOT overwrite `strategies/base.py` (from rejected v1 architecture).

### Decisions recorded
- Approval status of concept doc unchanged (user still researching)
- P1.7 backlog status stays WAITING until concept approved
- `strategies/base.py` kept as archive — new file is `strategies/base_v2.py`
- Enricher normalizes MFE to ATR units before handing to B4 (not B4's responsibility)

### State changes
- Concept doc targeted for 10 edits
- Plugin interface spec to be created new
- `strategies/base_v2.py` to be created new
- VINCE-PLUGIN-INTERFACE-SPEC-v1.md added to docs

### Open items recorded
- Concept doc still not APPROVED FOR BUILD (user researching)
- P1.7 waiting on concept doc approval
- RL Exit Policy Optimizer training methodology needs separate scoping session

### Notes
Edit 3 adds RL Exit Policy Optimizer section with full architecture. Edit 10 expands RL action space to 4 actions with intra-candle state. These are significant architectural additions to the concept doc.

---

## bright-prancing-koala.md

**Date:** 2026-03-03
**Type:** Planning / Audit

### What happened
Audit of handover spec for CUDA dashboard v3.9.4 build, followed by corrected build plan. Identified 4 issues in the original spec:

- ISSUE 1 (CRITICAL): Spec claims GPU sweep uses `Backtester390` but actual dashboard v3.9.2 imports `Backtester384` + `compute_signals_v383`. Resolution: GPU Sweep mode uses its own v3.9.0 signal pipeline call — not the existing one.
- ISSUE 2 (CRITICAL): Column name mismatch — spec uses `cloud3_ok_long/short`, actual DataFrame uses `cloud3_allows_long/short`.
- ISSUE 3 (MODERATE): Reentry cloud3 gate — spec incorrectly says reentry is ungated; actual v3.9.0 code shows reentry IS cloud3-gated.
- ISSUE 4 (MINOR): Spec claims v393 has IndentationError; actual: v393 passes py_compile.

Corrected build plan creates 3 target files via build script `scripts/build_cuda_engine.py`: `engine/cuda_sweep.py` (Numba CUDA kernel), `engine/jit_backtest.py` (Numba @njit CPU core), `scripts/dashboard_v394.py`. Documents correct kernel entry logic, 12 signal arrays, GPU Sweep mode signal pipeline import from `four_pillars_v390`.

### Decisions recorded
- Build CUDA kernel from v3.9.0 (`Backtester390`) logic
- GPU Sweep mode imports `compute_signals` from `signals.four_pillars_v390` (NOT v3.8.3)
- Reentry is cloud3-gated (corrected from spec)
- Column extraction uses `df["cloud3_allows_long"]`

### State changes
- Corrected build plan written; original spec identified as having 4 issues
- No code built in this plan — plan only

### Open items recorded
- User runs `scripts/build_cuda_engine.py` to generate 3 target files
- Verification steps: GPU detected, heatmap, portfolio JIT mode, fallback

### Notes
CODE VERIFICATION: `engine/cuda_sweep.py` found at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\engine\cuda_sweep.py` — build was executed. Also `scripts/build_strategy_v391.py` found (separate build).

---

## bubbly-conjuring-pony.md

**Date:** 2026-03-03
**Type:** Planning / Execution

### What happened
Execution plan for running `build_dashboard_v1_4_patch4.py` and verifying results. Patch4 adds a "Close Market" button to the position action panel in the BingX live dashboard v1.4, plus CB-16 callback that cancels all open orders for the selected position and places a MARKET reduceOnly close.

Documents current state (patches 1-3 already applied, dashboard at 2293 lines). Anchor verification for both P1 and P2 patches included with exact line text. Steps include running build script, restarting dashboard, browser hard refresh, and verification checklist.

### Decisions recorded
- CB-16 uses `prevent_initial_call=True` and `allow_duplicate=True` on `pos-action-status` output
- `close_pending=True` written to state.json on close market action

### State changes
- Patch4 not yet applied at time of plan creation
- Build script `scripts/build_dashboard_v1_4_patch4.py` exists

### Open items recorded
- User to run build script and verify checklist items

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_4_patch4.py` exists on disk — build script created.

---

## bubbly-sparking-flute.md

**Date:** (no explicit date — inferred from context, BingX connector work, ~2026-03-03/04)
**Type:** Planning / Build spec

### What happened
Plan to replace the 0.16% distance-based breakeven (BE) trigger with TTP (Trailing Take Profit) activation as the sole auto-BE trigger. Changes span 3 files: `position_monitor.py`, `bingx-live-dashboard-v1-4.py`, `config.yaml`.

Key change: removes `BE_TRIGGER = 1.0016` constant and mark price API fetch from `check_breakeven()`. New trigger: `pos_data.get("ttp_state") == "ACTIVATED"`. Guard added: `be_auto` read from config, defaults True. New `be_auto` toggle added to Strategy Parameters tab in dashboard. CB-11 and CB-12 callbacks updated to load/save the toggle.

Provides complete `check_breakeven()` implementation with proper logging and Telegram notification.

### Decisions recorded
- TTP activation is the sole BE trigger (replaces 0.16% distance trigger)
- `be_auto` config key added under `position:` section, defaults True
- `_fetch_mark_price_pm()` method kept (may be used elsewhere)
- `_place_be_sl()` unchanged

### State changes
- position_monitor.py: 3 edits (store config, remove constant, rewrite check_breakeven)
- bingx-live-dashboard-v1-4.py: 3 edits (add toggle, CB-11 output, CB-12 state+save)
- config.yaml: add `be_auto: true` under position section

### Open items recorded
- Manual test: set `ttp_state: ACTIVATED` in test position, verify BE SL placed
- py_compile verification on both files

### Notes
This is distinct from the TTP engine integration plan. This plan only changes the BE trigger logic, not the TTP engine itself.

---

## bubbly-strolling-frog.md

**Date:** 2026-02-28
**Type:** Planning (minimal)

### What happened
Short planning note for Parquet data catch-up. Last 1m candle fetch was 2026-02-13 (15 days stale). No build needed — existing `scripts/fetch_data.py` and `data/fetcher.py` (BybitFetcher class) handle incremental updates. Cache location: `data/cache/` (399 coins, 1m only). Run command documented. 5m candles explicitly skipped per user decision.

### Decisions recorded
- No new code needed — use existing `scripts/fetch_data.py --months 1`
- 5m candles skipped (user decision)

### State changes
- No code changes — documentation only

### Open items recorded
- User to run: `python scripts/fetch_data.py --months 1`
- Verify `Symbols fetched: 399/399` in summary output

### Notes
None.

---

## cached-rolling-brooks.md

**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan for BingX bot runbook Steps 2-11 (Steps 0-1 already done). Approach: single master script `scripts/run_steps.py` that requests user permission upfront (prints full list of files to modify, new files to create, backups to create, Ollama call count, pytest run count), then executes all steps sequentially unattended with Ollama streaming visible in terminal.

Files to be modified: `position_monitor.py`, `main.py`, `state_manager.py`, `risk_gate.py`, `executor.py`. New files to create: `ws_listener.py`, `scripts/reconcile_pnl.py`. 7 backup files created automatically.

Steps map: Step 2 = commission rate in position_monitor, Step 3 = commission fetch in main.py, Step 5 = WSListener new file, Step 6 = main.py WS thread, Step 7 = position_monitor fill_queue, Steps 9a/9b/9c = cooldown + session_blocked, Step 10 = reconcile_pnl.py. Pytest runs at Steps 4, 8, 11 (>=67 passing required).

### Decisions recorded
- Single master script approach (not separate step scripts)
- User approves once upfront, no more prompts
- Script halts immediately on any py_compile or pytest failure

### State changes
- No code written — plan only

### Open items recorded
- Steps 2-11 all pending execution
- `ws_listener.py` to be created (does not exist yet)
- `scripts/reconcile_pnl.py` to be created

### Notes
Referenced session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-27-bingx-bot-live-improvements.md`. Cross-references `fluffy-singing-mango.md` (spec) and `cozy-swimming-lake.md` (runbook).

---

## compressed-stirring-quail.md

**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan to create a BingX friend handover package — documentation for a friend building a BingX futures trading bot. Two files: `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md` (new) and the existing `BINGX-API-V3-COMPLETE-REFERENCE.md` (224 endpoints, shared as-is).

Handover document structure: 11 sections covering authentication (HMAC-SHA256, URL encoding gotcha), 11 critical gotchas ordered by severity (signature encoding, commission rate, fill price, recvWindow, leverage hedge mode, listenKey POST not GET, listenKey response format, gzip WebSocket, heartbeat Ping/Pong, VST geoblocked on most datacenters, order history purged quickly), curated endpoint table (14 endpoints), order placement pattern, WebSocket user data stream setup, bot architecture patterns (dual-thread), risk gate 8 checks, exit detection strategy, state machine and recovery, deployment checklist.

### Decisions recorded
- Primary file: `BINGX-FRIEND-HANDOVER.md` (~400 lines)
- Existing API reference shared as-is
- Vault log copy to `06-CLAUDE-LOGS/plans/2026-02-28-bingx-friend-handover-package.md`

### State changes
- No code written yet — plan only
- Document to be created

### Open items recorded
- Write `BINGX-FRIEND-HANDOVER.md`

### Notes
VST demo API geoblocked on most datacenters (Indonesian IPs only) — recorded as gotcha #10.

---

## concurrent-sniffing-brook.md

**Date:** 2026-02-28
**Type:** Research / Audit / Planning

### What happened
Research audit of Vince B4 scope (PnL Reversal Panel). Identifies skills required, what B4 builds (4 functions in `vince/pages/pnl_reversal.py`), hard build order dependencies (B1→B2→B3 must complete first — entire vince/ directory does not exist), and 8 API/data bottlenecks.

Key bottlenecks surfaced: whether backtester_v384 outputs mfe/mae/saw_green/entry_atr, how saw_green is defined/tracked, whether TP sweep requires re-run or MFE simulation, which ATR bins to use, whether RL overlay is in B4 scope, whether EnrichedTrade carries OHLCV tuples, the input API surface from Dash layer, and gross vs net metric type.

6 improvements proposed over current spec: finer ATR bins (9 bins vs 6), winners-left-on-table metric, per-grade TP sweep, gross+net curve on TP sweep, temporal split of MFE data, breakeven-adjusted MFE view.

File existence audit: entire vince/ directory does not exist. strategies/base_v2.py exists (stub). signals/four_pillars.py recently modified.

### Decisions recorded
- B4 is pure Python (no Dash imports)
- RL overlay = placeholder only in B4, separate future scope
- `api.py` owns orchestration (B6 calls api.get_panel2_data(), not B4 directly)
- TP sweep uses simulation from MFE (not re-run) — same as reference implementation
- Enricher normalizes MFE to ATR units (B3 responsibility, not B4)
- 9-bin ATR scheme recommended: [0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, ∞]

### State changes
- Audit document created — no code written
- BUILD-VINCE-B4-PNL-REVERSAL.md to be created after approval

### Open items recorded
- Verify `engine/position_v384.py` has mfe/mae/saw_green/entry_atr fields
- Complete B1 → B2 → B3 before building B4
- Create BUILD-VINCE-B4-PNL-REVERSAL.md spec doc

### Notes
Explicitly calls out that "B4" in the archived BUILD-VINCE-ML.md refers to something different (Dashboard Integration for ML classifiers) — dead spec. The active B4 is Panel 2 from the v2 concept doc.

---

## cozy-squishing-orbit.md

**Date:** 2026-02-20 (implied from session log reference)
**Type:** Build spec / Planning

### What happened
BingX Execution Connector full build plan. Documents decisions, bug fixes, 25 files to generate via build script `build_bingx_connector.py`.

Decisions locked: v3 endpoints for public market data, v2 for trade/user operations, mock strategy only (FourPillarsV384 plugin = separate build), write files to PROJECTS/bingx-connector/.

Bug fixes from audit: C03 (halt_flag read by RiskGate), C04 (halt_flag reset daily), C05 (allowed_grades from plugin), C07 (public endpoints unsigned), C01 (LONG/SHORT/NONE vocabulary), C02 (mark price from /quote/price).

18 core files + 7 additional = 25 files total. Detailed module design for all major components (bingx_auth.py, data_fetcher.py, risk_gate.py, state_manager.py, executor.py, position_monitor.py, main.py, plugins/mock_strategy.py). 4-layer testing architecture: unit tests (no network), integration test, connection test (needs .env), live demo test. Detailed error handling patterns with graceful degradation table. Debug script `scripts/debug_connector.py` with 7 modes.

### Decisions recorded
- v3 endpoints for public data, v2 for signed operations
- Mock strategy only for initial build
- 25 files generated by one build script
- 3 validation checks per file: py_compile + ast.parse + import smoke test
- Dual thread model: market_loop (30s) + monitor_loop (60s)
- Exit price estimation defaults to SL price (pessimistic) — noted as future improvement

### State changes
- Full connector architecture designed
- 25 target files specified
- Session log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-20-bingx-connector-build.md`

### Open items recorded
- Run build script
- Run tests on Jacky VPS
- Deploy in demo mode

### Notes
This is the original BingX connector build plan from ~2026-02-20. Subsequent sessions (cozy-swimming-lake, cached-rolling-brooks) show post-build improvements applied.

---

## cozy-swimming-lake.md

**Date:** 2026-02-27
**Type:** Planning / Execution

### What happened
Revised execution plan for BingX bot live improvements, specifically switching from Ollama non-streaming (`"stream":false` — 16 minutes silent per step) to streaming (`"stream":true` — tokens print in real-time). Documents current state (executor.py already patched FIX-2+FIX-3, all other files not yet patched).

Execution sequence for Steps 2-11: each step follows read→edit→py_compile→report→log pattern. Step 2 = position_monitor commission rate, Step 3 = main.py commission fetch, Step 4 = pytest, Step 5 = ws_listener.py new file, Step 6 = main.py WS thread, Step 7 = position_monitor fill_queue, Step 8 = pytest, Step 9 = state_manager/risk_gate/executor cooldown+session_blocked, Step 10 = reconcile_pnl.py, Step 11 = final pytest.

Rules: py_compile must pass before replacing any file, backup every file, log every action with timestamp, halt if any step fails.

### Decisions recorded
- Use streaming Ollama calls (stream:true)
- Backup pattern: `file.py.bak` via Bash
- Halt immediately if any step fails — wait for user

### State changes
- Plan revised from non-streaming to streaming approach
- No code written yet in this plan — execution plan only

### Open items recorded
- Steps 2-11 pending execution
- Session log: `06-CLAUDE-LOGS/2026-02-27-bingx-bot-live-improvements.md`

### Notes
Companion to `cached-rolling-brooks.md` (the master script approach) and to the original spec in `fluffy-singing-mango.md`. This plan uses direct Edit tool approach instead of a master script.

---

## crispy-petting-sloth.md

**Date:** 2026-02-28
**Type:** Build spec (agent-executable)

### What happened
Complete, executable instruction set for building the v386 strategy version. Context: `require_stage2: true` in `config.yaml` is the sole driver of trade frequency reduction from ~93/day to ~40/day on 47 coins. Documents what changed from v384 to v386 (require_stage2, allow_c, tp_atr_mult). Includes complete Python code for `signals/four_pillars_v386.py` (copy of signals/four_pillars.py with two defaults changed).

6-step execution plan: Glob check (no overwrite), write signals file + py_compile, write docs/FOUR-PILLARS-STRATEGY-v386.md (full strategy doc), update PRODUCT-BACKLOG.md (P0.5 DONE, P0.6 READY), append to TOPIC-vince-v2.md, create session log + update INDEX.md.

v386 strategy doc included in full: indicators, Stage 1/2 entry logic, signal grades, risk parameters, coin selection filter, differences from v384.

### Decisions recorded
- v386 = v384 with `require_stage2=True` and `allow_c=False`
- State machine (state_machine.py) unchanged — Stage 2 logic was already implemented
- No new files overwritten (HARD RULE enforced — Glob first)

### State changes
- `signals/four_pillars_v386.py` to be created
- `docs/FOUR-PILLARS-STRATEGY-v386.md` to be created
- PRODUCT-BACKLOG.md: P0.5 DONE, P0.6 READY
- TOPIC-vince-v2.md: v386 section appended

### Open items recorded
- All 6 execution steps pending (checkboxes all unchecked at end of plan)

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v386.py` EXISTS on disk — build was executed.

---

## crystalline-dreaming-sun.md

**Date:** 2026-03-05
**Type:** Planning / Architecture

### What happened
Plan to build a Python script that orchestrates sequential `claude -p` CLI calls to automate chronological log research across the entire vault. Context: ~201 session logs + ~149 plan files (~87,000 total lines) spanning Jan 2025 to March 2026.

Architecture: `scripts/run_log_research.py` discovers all .md files, splits into batches, runs `claude -p` per batch via subprocess, waits for completion, moves to next batch. 16 batches total (~350 files): Batches 1-15 use sonnet, Batch 16 (synthesis) uses opus.

Prompt template per batch specifies: read files in order, append findings to RESEARCH-FINDINGS.md using exact format, update RESEARCH-PROGRESS.md checkboxes, code verification for referenced scripts.

Estimated runtime: 5-8 hours unattended. Key flags: `--allowedTools "Read,Edit,Glob,Grep"`, `--max-turns 200`, `--verbose`.

Batch design table provided (16 batches, purposes of each).

### Decisions recorded
- Single orchestrator script approach
- Write tool excluded from allowed tools (prevents overwrites in subagent calls)
- Batches 1-15 use sonnet model, Batch 16 synthesis uses opus
- ~25 files per batch, mega-files get dedicated batches

### State changes
- Orchestrator script `scripts/run_log_research.py` to be created
- `RESEARCH-PROGRESS.md` created at runtime by script

### Open items recorded
- Write and run `run_log_research.py`
- All 16 batches pending

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\run_log_research.py` EXISTS on disk — build was executed. This is the orchestrator for the current research task.

---

## crystalline-stirring-glade.md

**Date:** 2026-03-04
**Type:** Planning / Build spec

### What happened
Plan for v3.9.1 Four Pillars signal quality rebuild. Context: v3.9.0 signals have 3 compounding problems — 3-phase SL movement system not implemented (position_v384 uses AVWAP center as SL trail), Cloud 2 hard close missing, Cloud 4 (EMA 72/89) not computed or used.

Goal: build v391 as faithful implementation per `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md` v2.0.

5 new files specified:
- `signals/clouds_v391.py` — adds Cloud 4 + cross detection columns
- `signals/four_pillars_v391.py` — calls compute_clouds_v391(), keeps state_machine_v390.py
- `engine/position_v391.py` — 3-phase SL system with phase state, phase 0 (initial), phase 1 (cloud2 cross), phase 2 (cloud3 cross), phase 3 (cloud3+4 sync trail), hard close, corrected AVWAP role
- `engine/backtester_v391.py` — imports position_v391, passes cloud cross columns to position slot, hard close check first, expanded update_bar signature, sl_phase field in trade record
- `scripts/build_strategy_v391.py` — single build script

State machine v390 kept unchanged — A/B/reentry logic correct.

### Decisions recorded
- State machine stays at v390 (signal detection structurally correct)
- AVWAP moved to correct role: ADD entry trigger + scale-out trigger only (NOT SL trail)
- ADD signals changed from AVWAP-price trigger to stochastic-based trigger
- Phase 3: TP removed when Cloud3+4 sync, trail_extreme tracks highs/lows
- Hard close (Cloud 2 flips against trade) is highest priority exit, checked before SL

### State changes
- Build script `scripts/build_strategy_v391.py` to be created
- 4 engine/signal files to be created (all new, no overwrites)

### Open items recorded
- Run build script
- Smoke test on one symbol
- Verify sl_phase > 0 in trades, CLOUD2_CLOSE exits, Phase 3 trail active

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_strategy_v391.py` EXISTS on disk — build was executed.

---

## cuddly-dancing-perlis.md

**Date:** 2026-03-03 (revised after audit)
**Type:** Planning / Build spec

### What happened
Plan for TTP (Trailing Take Profit) engine integration with BingX connector and dashboard. Context: ttp_engine.py drafted by Opus has 4 remaining bugs; existing bot uses fixed ATR-TP placed at entry; user wants TTP toggleable from dashboard, displayed per-position.

4 bugs in ttp_engine.py: Bug 1 = `self.state` never set to CLOSED, Bug 4 = CLOSED_PARTIAL state (replace with CLOSED everywhere), Bug 5 = iterrows() slow/fragile (replace with itertuples), Bug 6 = `band_width_pct` `or 0` fallback (guard with proper None check).

Architecture: hybrid split — Thread 1 (market loop via signal_engine.py) evaluates TTP using real 1m OHLC bars, Thread 2 (monitor loop via position_monitor.py) executes TTP closes. `ttp_close_pending` flag bridges threads via state.json. Race guard: monitor verifies position exists on exchange before placing MARKET close.

7 files touched: ttp_engine.py (create), signal_engine.py (modify), position_monitor.py (modify), main.py (modify), config.yaml (modify), bingx-live-dashboard-v1-4.py (Patch 3), tests/test_ttp_engine.py (create).

Two build scripts: `scripts/build_ttp_integration.py` (connector files), `scripts/build_dashboard_v1_4_patch3.py` (dashboard only).

Dashboard changes (Patch 3): add TTP + Trail Lvl columns to POSITION_COLUMNS, update build_positions_df, add TTP section to Controls tab (toggle + activation % + trail distance %), update CB-11 and CB-12.

### Decisions recorded
- TTP evaluation uses real 1m OHLC (not mark price) — preserves dual scenario band
- TTP engines live in signal_engine (market loop), keyed by position key
- Existing fixed TP orders still placed on entry — TTP runs alongside, whichever fires first wins
- Exit reason "TTP_EXIT" logged in trades.csv

### State changes
- ttp_engine.py to be created (with 4 bugs fixed)
- signal_engine.py, position_monitor.py, main.py, config.yaml all to be modified
- bingx-live-dashboard-v1-4.py Patch 3 applied
- tests/test_ttp_engine.py to be created (6 unit tests)

### Open items recorded
- Run both build scripts
- 10 verification steps including race test

### Notes
Explicitly states "Replace fixed TP with TTP" is out of scope for this session (separate session).

---

## dashboard-v1-2-improvements.md

**Date:** 2026-02-28 (implied from context)
**Type:** Planning

### What happened
Plan for BingX Dashboard v1.2 improvements based on v1.1 live testing screenshots/notes. 5 fixes + 3 analytics improvements:

- FIX-1: White input fields on Bot Controls tab (CSS fix for dcc.Input, dcc.RadioItems, dcc.Dropdown)
- FIX-2: Positions grid white background ("No Rows To Show" on white bg with dark theme)
- FIX-3: Analytics shows all-time trades vs History shows today only — add date range picker
- FIX-4: Tab re-render on switch (Option A selected: render all tabs in layout, toggle visibility with clientside callback — removes CB-2 render_tab, ~80 lines changed)
- FIX-5: Add timing diagnostics in CB-1

3 analytics improvements: professional metrics (Sharpe, LSG%, BE Hit, MaxDD%, SL Hit%, TP Hit%), date range picker, chart cleanup (no toolbar, proper labels).

Blocker identified: LSG% requires MFE tracking in position_monitor.py (not in dashboard scope); BE Hit Count requires be_raised written to trades.csv on close. Both show "N/A" until bot changes made.

### Decisions recorded
- FIX-4 Option A selected: render all tabs, toggle visibility (not dynamic tab content)
- CB-2 (render_tab) removed
- LSG% and BE Hit will show "N/A" placeholder until bot tracking added

### State changes
- No code written — plan only
- Files to touch: bingx-live-dashboard-v1-1.py, assets/dashboard.css, scripts/test_dashboard.py

### Open items recorded
- Implement all 8 items in build order
- Bot changes needed (separate scope): MFE tracking in position_monitor, be_raised in trades.csv

### Notes
This plan targets bingx-live-dashboard-v1-1.py (producing v1.2). Not the Dash-based v1.4 dashboard.

---

## distributed-exploring-lerdorf.md

**Date:** (no explicit date — implied ~2026-03-03/04)
**Type:** Planning / Build spec

### What happened
Plan for a daily Bybit data updater script. Context: backtester data cache (399 coins, data/cache/) stale since 2026-02-13. New standalone script purpose-built for daily incremental updates (not patching fetch_data.py).

Build script: `scripts/build_daily_updater.py` creates `scripts/daily_update.py`.

daily_update.py does: Step 1 = discover symbols from Bybit (v5/market/instruments-info), Step 2 = incremental fetch for each symbol (read .meta for cached_end_ms, fetch only gap, append+deduplicate, update .meta; full fetch for new symbols), Step 3 = resample to 5m via TimeframeResampler, Step 4 = summary + log.

CLI flags: `--months`, `--skip-new`, `--skip-resample`, `--max-new`, `--dry-run`.

Reuses `BybitFetcher` from `data/fetcher.py` and `TimeframeResampler` from `resample_timeframes.py`. Symbol discovery pattern from `fetch_sub_1b.py` lines 113-126.

### Decisions recorded
- Standalone script (not patching fetch_data.py)
- Incremental append logic lives in daily_update.py (not patched into fetcher.py)
- Rate limit: 0.12s between requests (matches fetch_sub_1b.py)
- Log to `logs/YYYY-MM-DD-daily-update.log` with dual handler

### State changes
- Two new files planned: build_daily_updater.py + daily_update.py

### Open items recorded
- User to run `python scripts/build_daily_updater.py` then `--dry-run`

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_updater.py` EXISTS on disk — build was executed.

---

## dynamic-bubbling-cray.md

**Date:** 2026-02-28
**Type:** Planning / Build spec

### What happened
Plan for the initial BingX live dashboard v1.0. Read-only monitoring with 3 tabs: Positions (open positions from state.json + mark price API), History (closed trades from trades.csv), Coin Summary (grouped stats from trades.csv).

Framework chosen: Streamlit (not Dash). Rationale: read-only monitoring with 3 tabs, file-based data, simple tables. Streamlit = ~150 lines vs Dash = ~300 lines. Uses `st.tabs()`, `st.dataframe()`, `time.sleep(60); st.rerun()`.

Tab 1 columns: Symbol, Direction, Grade, Entry Price, Stop Loss, Take Profit, BE Raised, Unrealized PnL, Duration. Row color: green=LONG, red=SHORT.
Tab 2 columns: Date/Time, Symbol, Direction, Grade, Entry/Exit Price, Exit Reason, Net PnL, Duration. Default: today's trades.
Tab 3: Symbol grouped stats including SL%/TP%/Unknown% exit breakdown (LSG% noted as requiring MFE data not available).

Data files: state.json, trades.csv, config.yaml, .env, BingX /quote/price API.

### Decisions recorded
- Streamlit chosen over Dash for monitoring dashboard
- File: `bingx-live-dashboard-v1.py` at PROJECTS/bingx-connector/
- Run: `streamlit run ...`
- No buttons, no order actions — read-only only

### State changes
- Dashboard file to be created
- No existing files modified

### Open items recorded
- Write and run dashboard

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1.py` EXISTS on disk. This is the initial Streamlit version — later superseded by Dash-based versions (v1.1, v1.2, v1.4).

---

## eager-snacking-pearl.md

**Date:** (no explicit date — implied ~2026-02-28/early March)
**Type:** Planning / Build spec

### What happened
Plan to accelerate the backtester dashboard using timing instrumentation and safe Numba JIT. Context: user asked if sweep/portfolio loading can run on GPU — answer: no (sequential state machine). Real solution: measure first, then apply Numba only to confirmed pure-numpy kernels.

Numba 0.61.2 already installed. Python 3.13 + llvmlite 0.44.0 + numpy 2.2.6 confirmed compatible. Dashboard v391 will NOT be touched — zero files modified, new files only.

Audit findings confirmed from source:
- SAFE for @njit: `stoch_k()` in stochastics.py, `ema()` in clouds.py, ATR RMA loop (requires extraction to function)
- NOT SAFE: compute_all_stochastics(), compute_clouds(), compute_signals_v383(), FourPillarsStateMachine383.process_bar(), Backtester384.run()

Two-phase plan:
- Phase 1: `utils/timing.py` — context manager + accumulator. Performance Debug checkbox in sidebar shows per-phase/per-coin milliseconds.
- Phase 2: Three new signal files with @njit(cache=True): stochastics_v2.py, clouds_v2.py, four_pillars_v383_v2.py. Dashboard v392 imports from v2 signals.

6 files created total (zero files modified). Expected speedup ~22% per-coin for signal computation (state machine and backtester unchanged). Verification protocol: baseline metrics recorded from v391, v392 must produce EXACTLY equal results, timing panel confirms improvement.

### Decisions recorded
- Numba applied only to confirmed safe kernels (3 functions)
- dashboard_v391.py STABLE — never touched
- cache=True on all @njit decorators
- Rollback: delete 6 new files — v391 immediately back to normal

### State changes
- 6 new files to be created by `scripts/build_dashboard_v392.py`
- Numba first-run compilation 2-5s (one-time)

### Open items recorded
- Record baseline from v391 before building v392
- Run build script
- Verify numerical parity on RIVERUSDT

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v392.py` EXISTS on disk — build was executed.

---

## elegant-enchanting-wilkinson.md

**Date:** (no explicit date — implied ~2026-02-16/17 based on BBW pipeline context)
**Type:** Planning / Build spec

### What happened
Plan for remaining 3 components of the BBW (Bollinger Band Width) pipeline. Layers 1-5 already complete and tested. Three remaining components to make the pipeline fully runnable end-to-end:

1. `research/coin_classifier.py` — KMeans volatility tier assignment (4 functions, 15 tests)
2. `research/bbw_ollama_review.py` — Layer 6 LLM analysis of Layer 5 CSV output (3 analysis functions + run_ollama_review, 15 tests)
3. `scripts/run_bbw_simulator.py` — CLI entry point wiring all layers (run_pipeline, 12 tests)

Delivery: one build script `scripts/build_bbw_remaining.py` using build_staging.py pattern (FILES dict → write → py_compile → run tests → report). 9 files total.

Data contracts documented from existing codebase. Ollama models confirmed: qwen3:8b, qwen2.5-coder:14b, qwen2.5-coder:32b, qwen3-coder:30b, gpt-oss:20b. Error handling for offline Ollama (writes OFFLINE message, never raises).

CLI flags for run_bbw_simulator.py: --symbol, --tier, --timeframe, --top, --no-monte-carlo, --mc-sims, --no-ollama, --ollama-model, --output-dir, --verbose, --dry-run.

### Decisions recorded
- Build script pattern follows build_staging.py
- 9 files generated by one build script
- Ollama offline: write OFFLINE message, continue — never raises exception
- Debug scripts included for all 3 components

### State changes
- `scripts/build_bbw_remaining.py` to be created
- 9 target files (3 main + 3 test + 3 debug) to be created by build

### Open items recorded
- Run build script (expected: 9/9 syntax pass, 42/42 tests pass)
- Run `scripts/debug_run_bbw_simulator.py` for full pipeline smoke test on RIVERUSDT

### Notes
CODE VERIFICATION: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_bbw_remaining.py` EXISTS on disk — build was executed.
