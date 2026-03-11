# Research Batch 18 Findings — Auto-Plans (e through i)

**Generated:** 2026-03-06
**Files processed:** 20
**Source directory:** C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\

---

## elegant-weaving-sutherland.md
**Date:** 2026-03-05
**Type:** Planning

### What happened
Plan for a config-toggled native trailing stop switch for the BingX connector. Context: the custom TTP engine evaluates on confirmed 5m candles creating up to ~6min worst-case delay before trailing exit fires. BingX native `TRAILING_STOP_MARKET` runs tick-level on exchange. A previous native trailing attempt had failed because activation was ATR-based (too far) and callback was 2% (too wide). This plan uses percentage-based params matching the working TTP config.

New config key `ttp_mode` with values `"native"` (exchange-managed, tick-level) or `"engine"` (existing custom 5m-candle TTP, default). Reuses existing `ttp_act=0.008` and `ttp_dist=0.003` for both modes.

6 files to modify: config.yaml, executor.py, signal_engine.py, position_monitor.py, ws_listener.py, state_manager.py (~65 lines changed total).

Critical bug fix designed: `"STOP" in "TRAILING_STOP_MARKET"` evaluates True in Python, so BE raise would cancel native trailing orders in `_cancel_open_sl_orders`. Fix: exclude `TRAILING_STOP_MARKET` from cancellation check. Also: `_detect_exit` must detect when trailing_order_id disappears from open orders (= it fired), and `_fetch_filled_exit` and `ws_listener._parse_fill_event` must classify `TRAILING_STOP_MARKET` as `TRAILING_EXIT`.

Delivery: build script `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_native_trailing.py`.

### Decisions recorded
- `ttp_mode: native` added to config.yaml under position section
- `_place_trailing_order()` gains `price_rate` override parameter
- `signal_engine.py` early-returns when `ttp_mode == "native"` (skip engine evaluation)
- `position_monitor.py` skips `check_ttp_closes` and `check_ttp_sl_tighten` in native mode
- BE raise still active in native mode (safety net between +0.4% and +0.8%)
- If native trailing rejected by exchange: log error, SL remains, no fallback to engine
- `ttp_engine.py`, `main.py`, and dashboard deferred/out of scope

### State changes
- Plan created for 6-file modification
- Critical BE/native trail interaction bug identified and fix designed
- `TRAILING_EXIT` reason added to trades.csv classification design
- Build script `build_native_trailing.py` planned

### Open items recorded
- Build script to be written and executed
- Manual verification: `ttp_mode: native` + `demo_mode: true`, verify trailing placed, BE doesn't cancel it, exit classified as `TRAILING_EXIT`
- Switchback test: `ttp_mode: engine`, verify three-stage pipeline fully restored

### Notes
Three-stage interaction table provided: BE raise (+0.4%), TTP activation (+0.8%), trail (0.3% callback). Previous failed attempt used ATR-based activation and 2% callback.

---

## enumerated-dazzling-squirrel.md
**Date:** 2026-03-05 (inferred from content — references work through 2026-03-05)
**Type:** Planning

### What happened
Plan for staging all vault repo changes and pushing to GitHub (S23Web3/ni9htw4lker). Covers all work from 2026-03-03 through 2026-03-05: BingX connector v1.5 patches (timestamp sync fix, TTP engine, config tuning), backtester v391 modules, session logs, build scripts, documentation updates. VPS was already configured with .env and environment; bot to be pulled and run on VPS after push.

5-step plan:
1. `git add -A` in vault root
2. Verify 12 critical bot files staged (including new `time_sync.py`, `main_beta.py`, `config_beta.yaml`, `bingx-live-dashboard-v1-5.py`)
3. Commit with specified message
4. `git push origin main`
5. Post-push verification + VPS instructions

Scope: 20 modified tracked files, 70+ new untracked files, 0 files with secrets (config.yaml has no API keys, bingx_auth.py reads from env vars).

### Decisions recorded
- Commit message: `"Vault update: BingX v1.5 (time sync, TTP, config tuning), backtester v391, session logs 2026-03-03 to 2026-03-05"`
- All files verified clean of secrets before push
- VPS next step: `git pull origin main` then `python main.py`

### State changes
- This plan documents the git push that produced commit `e85b370` (confirmed in current git log)

### Open items recorded
- VPS: `git pull origin main` + verify `time_sync.py` exists

### Notes
Commit `e85b370` in current git log confirms this plan was executed successfully.

---

## eventual-plotting-pony.md
**Date:** Not explicitly stated (BingX connector early setup phase)
**Type:** Guided instructions / Setup document

### What happened
Step-by-step instructions for connecting the BingX bot to Telegram by populating `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the `.env` file. Code was already fully built (`notifier.py` complete, `main.py` loads from `.env`). Only the placeholder values were blocking alerts.

5 steps: create bot via @BotFather, get Chat ID via `getUpdates` API URL, edit `.env`, test with a Python one-liner (sends "BingX bot Telegram test OK"), run bot and verify startup Telegram message. References `STEP1-CHECKLIST.md` item `**Telegram alert received**`.

### Decisions recorded
- No quotes or spaces around `=` in .env values
- Test one-liner provided before running bot

### State changes
- No code changes — purely a user instruction document

### Open items recorded
- User must complete all 5 steps and check off `Telegram alert received` in STEP1-CHECKLIST.md

### Notes
No date in file. Context places it in early BingX connector setup (before first signal fired). This is a user-facing guide, not a technical build plan.

---

## eventual-tickling-stardust.md
**Date:** 2026-03-03
**Type:** Fix plan / Audit execution

### What happened
Plan to apply findings from a full logic audit of `cuda_sweep.py`, `dashboard_v394.py`, and BingX connector files via a single build script. Previous session documented findings without applying fixes.

**CRITICAL #1** — Commission split in cuda_sweep.py: same rate (0.0008) used for both entry and exit. Fix: add `maker_rate=0.0002` param, split into `entry_comm` and `exit_comm`. Impact: all prior GPU sweep P&L numbers overstated by 0.06% × notional per RT.

**CRITICAL #2** — `pnl_sum` missing entry commission: Fix: `pnl_sum += net_pnl - entry_comm` at both exit points.

**HIGH #3** — win_rate displayed as raw decimal in 3 table locations in dashboard_v394.py. Fix: multiply × 100, rename to `win_rate%`.

**HIGH #4** — TTP state lost on restart: REASSESSED as already fixed (signal_engine.py lines 113-127 already restores from persisted fields). No action.

**HIGH #5** — WSListener dies permanently after 3 reconnect failures with no alert. Fix: MAX_RECONNECT=10, exponential backoff, write `logs/ws_dead_{timestamp}.flag`.

**HIGH #6** — `_place_market_close()` missing reduceOnly: LOW risk in hedge mode. Decision: add `"reduceOnly": "true"` as defensive measure.

**HIGH #7** — `saw_green` uses `>` instead of `>=` at cuda_sweep.py lines 163/171.

Build script `build_audit_fixes.py` patches 4 files: cuda_sweep.py, dashboard_v394.py, ws_listener.py, position_monitor.py.

### Decisions recorded
- HIGH #4 confirmed already fixed — skipped
- HIGH #6 downgraded to LOW but add reduceOnly defensively
- `maker_rate=0.0002` added to `run_gpu_sweep()` and `run_gpu_sweep_multi()` signatures
- Patch via exact string replacement (no full rewrite)
- MEDIUM/LOW issues deferred

### State changes
- 4 files planned for patching
- All prior GPU sweep P&L numbers confirmed overstated (0.06% × notional per RT)
- Build script `build_audit_fixes.py` planned

### Open items recorded
- User runs GPU Sweep post-fix, verifies `win_rate%` shows 42.3 not 0.423
- Verify net_pnl figures lower than previous runs

### Notes
Previously noted TTP state restoration fix (signal_engine.py lines 113-127) confirmed correct by this audit.

---

## expressive-painting-taco.md
**Date:** Not explicitly stated (post-VPS-block discovery; consistent with early March 2026)
**Type:** Planning

### What happened
Plan for two deliverables: (1) Windows Task Scheduler auto-start on reboot with crash recovery, and (2) improved Telegram message formatting. Context: VPS (Hostinger Jakarta) cannot reach BingX VST API (Indonesian IPs block datacenter connections) — bot runs locally on Windows in demo mode (47 coins, 5m).

One build script `build_autostart_and_tg.py` backs up 3 existing files, creates 3 new files (PowerShell wrapper `run_bot.ps1`, Task Scheduler XML `bingx-bot-task.xml`, installer `install_autostart.ps1`), and modifies 3 existing files (executor.py, position_monitor.py, main.py — Telegram HTML formatting).

PowerShell wrapper: crash recovery loop, restarts on non-zero exit code after 30s delay, does NOT restart on clean exit (code 0). Task Scheduler: AtStartup trigger, 60s network delay.

Telegram messages reformatted from single-line dumps to multi-line HTML with `<b>` bold headers. 10 exact string replacements specified: ENTRY, ORDER FAILED, ORDER ID UNKNOWN, EXIT, DAILY SUMMARY, HARD STOP, WARNING, BOT STARTED, BOT STOPPING, BOT STOPPED.

### Decisions recorded
- Clean exit (code 0) = intentional stop, no restart; non-zero = crash, restart after 30s
- Task Scheduler: AtStartup, 60s delay, run hidden
- HTML parse mode (`<b>` tags) for all Telegram messages
- Bot runs locally on Windows (not VPS) due to VST API block

### State changes
- Build script planned creating 3 new files + modifying 3 existing (with timestamped .bak backups)

### Open items recorded
- User must run `install_autostart.ps1` as admin to register task
- Reboot test + crash recovery test required

### Notes
Indonesian VPS IPs block datacenter connections to BingX VST API — this was the constraint forcing local Windows execution.

---

## fizzy-humming-crab.md
**Date:** 2026-03-04
**Type:** Research / Strategy specification

### What happened
Comprehensive position management study document based on two live TradingView Replay walkthroughs: PUMPUSDT LONG (Wed 04 Mar '26, 5m Bybit Spot) and PIPPINUSDT SHORT (Tue 03 Mar '26, 5m Bybit Perpetual). Both are trend-hold type (stoch 60 gate opens). Documents the full trade lifecycle across 6 phases.

**Three-layer HTF direction system:** Layer 1 = 4h/1h session bias (Ripster EMA cloud transitions); Layer 2 = 15m MTF Clouds on 5m chart (hold duration modulator, not hard binary); Layer 3 = 5m execution timing. All three must agree.

**Entry detection:** All 4 stochastics (9, 14, 40, 60 Raw K) must have K/D crossovers — sequential process, stoch 9 crosses first (alert), wait for others. Recent zone check: K must have been below 20 (long) or above 80 (short) within last N=10 bars. BBW spectrum must cross from below to above MA. TDI price line on correct side of MA.

**SL:** 2 × ATR(14) from entry, validated against structural level.

**Gate check:** Stoch 60 K vs D crossing = gate opens = trend-hold mode.

**Trend hold management:** TDI 2-candle rule (hard exit), BBW health monitor (healthy/extreme/exit states), AVWAP trailing (plain or +2sigma), Ripster Cloud 4 value FROZEN at confirmation = TP target.

**Add-ons:** Stoch 9/14 must reach opposite zone while 40/60 hold trend direction.

Conclusion: "This is not a patch on v386. It is a different strategy architecture." Contradicts ATR-SL-MOVEMENT-BUILD-GUIDANCE.md which makes ATR central to phase transitions (ATR role here = thermometer only).

### Decisions recorded
- N=10 bars for recent zone check (flagged for Vince optimization)
- MTF clouds = hold duration modulator (not hard binary filter)
- ATR: thermometer only (SL sizing + volatility confirmation, not phase driver)
- No code until user explicitly approves the rules

### State changes
- Study document only — no code written
- State machine diagram created
- Full comparison table: User's Actual Trading vs ATR-SL-MOVEMENT Spec vs AVWAP 3-Stage vs v386

### Open items recorded
- 7 open questions: SL-1 (2 ATR not aligned with structure?), SL-2 (what counts as structure?), GATE-1 (K/D distance threshold?), BE-1 (two BE methods interchangeable?), TRAIL-1 (AVWAP variant selection), CLOUD-1 (frozen Cloud 4 longs-only?), TP-1 (cloud vs % target?)
- BBW BBWP percentile thresholds marked as "flagged for Vince research" — no numeric boundaries

### Notes
Document explicitly states: "No code should be written until the user explicitly approves the rules." This is a research artifact, not a build plan.

---

## floating-jingling-valiant.md
**Date:** 2026-03-05
**Type:** Audit / Quality review

### What happened
Thoroughness audit of the `2026-03-05-next-chat-prompt.md` continuation prompt. Bot was RUNNING and must NOT be restarted (48h live data collection). Found 2 errors and 3 gaps; verified 8 claims as correct.

**ERROR 1 (Task 1 function mismatch):** Prompt says `compute_signals()` in `signals/four_pillars.py` accepts `require_stage2`/`rot_level`. Reality: dashboard_v394.py line 57 imports `compute_signals_v383()` from `signals/four_pillars_v383_v2.py` which does NOT accept those params. Fix options: (A) switch import line 57 to `compute_signals` from `signals.four_pillars`, or (B) add params to the v383 function.

**ERROR 2 (Task 2 already 80% done):** Prompt says 5 bugs still pending. Reality: `bingx-live-dashboard-v1-5.py` already EXISTS (133K, built 2026-03-04) with patches P3-A through P3-H applied. BUG-4/BUG-1b/BUG-2/BUG-5 all fixed. Only `be_act` save callback genuinely missing.

**GAPs:** (1) No bot restart constraint, (2) Stale runtime data, (3) Import switch not mentioned.

Verified correct: Three-stage TTP config values (be_act=0.004, ttp_act=0.008, ttp_dist=0.003), orderId extraction in 3 places, unrealized PnL in Telegram, max_positions=25, test pass count, key file paths.

Plan: Create corrected v2 prompt at `2026-03-05-next-chat-prompt-v2.md` (do NOT overwrite original). 4 specific fixes documented.

### Decisions recorded
- Option A for Task 1: change import (line 57) to `from signals.four_pillars import compute_signals`
- Task 2 scoped down to `be_act` settings save only
- Create v2 prompt file, preserve original

### State changes
- New file planned: `06-CLAUDE-LOGS/plans/2026-03-05-next-chat-prompt-v2.md`
- Audit findings documented

### Open items recorded
- Write v2 prompt with all 4 fixes; read back to verify

### Notes
Confirms `bingx-live-dashboard-v1-5.py` existed as of 2026-03-04 with most bugs already fixed.

---

## fluffy-singing-mango.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
BingX bot improvement plan after scraping the full BingX API v3 reference (224 endpoints, 849KB). Decision context: stop polishing VST demo, prepare infrastructure for live money.

**3 key API discoveries:**
1. Commission rate queryable — `GET /openApi/swap/v2/user/commissionRate` returns actual taker/maker rates. Bot hardcoded 0.0012; real rate is 0.0016 RT — every trade understated commission by 33%.
2. Position history gives BingX-calculated PnL (`netProfit` with actual commission + funding fees — ground truth).
3. WebSocket ORDER_TRADE_UPDATE gives real-time fills — eliminates EXIT_UNKNOWN. Entry price wrong: bot uses `mark_price`, actual fill is `data.avgPrice`.

**P0 bugs:** FIX-1 (commission hardcoded wrong), FIX-2 (entry price = fill price not mark), FIX-3 (SL direction validation).

**P1:** IMP-1 (new `ws_listener.py` WebSocket daemon thread), IMP-2 (`scripts/reconcile_pnl.py` standalone PnL audit).

**P2:** IMP-3 (error 101209 max position value), IMP-4 (cooldown filter), IMP-5 (startup commission fetch).

**P3:** IMP-6 (batch cancel on shutdown), IMP-7 (Cancel All After safety timer), IMP-8 (trailing stop option).

Full Ollama-based build runbook (Steps 1-11): paste file content, apply specific changes, py_compile each result.

### Decisions recorded
- Build via Ollama (local LLM) code generation
- New files: `ws_listener.py`, `scripts/reconcile_pnl.py`
- WSListener = threading.Thread, daemon=True; fill_queue drain before polling
- Commission rate RT = taker rate × 2 = 0.0016

### State changes
- Improvement catalog created (11 items, 4 priority levels)
- All prior trade PnL records confirmed to have understated commission by 33%

### Open items recorded
- 11-step build runbook
- P2/P3 improvements deferred

### Notes
`ws_listener.py` was subsequently built (confirmed in git status as `M PROJECTS/bingx-connector/ws_listener.py`). This plan predates that implementation.

---

## fluttering-kindling-creek.md
**Date:** Not explicitly stated (references v1-1 spec; context ~2026-02-28)
**Type:** Planning

### What happened
Execution plan for building BingX Live Dashboard v1-1 from the complete spec in `C:\Users\User\.claude\plans\goofy-dancing-summit.md` (1795 lines). Previous session finalized spec but hit context limit before writing code.

3 files to build:
1. `bingx-live-dashboard-v1-1.py` (~700 lines) — Dash 4.0, port 8051, 5 tabs, 14 callbacks, ag-grid, dark theme, BingX API integration for position management (Raise BE, Move SL), config editor, halt/resume
2. `assets/dashboard.css` (~20 lines)
3. `scripts/test_dashboard.py` (~170 lines)

7-step build plan: load Dash skill, write 3 files, py_compile both .py files, give run command.

Key technical decisions: `suppress_callback_exceptions=True`, `prevent_initial_call=False` for CB-1/CB-2, API signing replicated in dashboard (not imported from bot), `ThreadPoolExecutor(max_workers=8)` for price fetches, atomic writes via tmp + `os.replace()`, dual logging with `TimedRotatingFileHandler`.

### Decisions recorded
- Dash 4.0 not Streamlit (Streamlit reruns full script on every click, wiping mid-action form state)
- Pattern-matching callbacks (MATCH selector) required for per-row Raise BE / Move SL
- Load Dash skill mandatory per MEMORY.md
- Existing v1 (Streamlit, `bingx-live-dashboard-v1.py`) must NOT be touched

### State changes
- No code written yet — plan to execute goofy-dancing-summit.md spec

### Open items recorded
- Build steps 1-7 to be executed
- User verification: py_compile, test_dashboard.py, launch at port 8051

### Notes
References `goofy-dancing-summit.md` as source spec. That file is also in this batch (see below).

---

## foamy-soaring-snowflake.md
**Date:** 2026-03-05
**Type:** Fix plan — Runtime error resolution

### What happened
Dashboard v1.5 passed `py_compile` but had never been run until 2026-03-05. First launch revealed 2 code errors and 1 API error.

**Error 1:** `KeyError: "Callback function not found for output 'store-bot-status.data'."` — `dcc.Store(id='store-bot-status', data=[])` at line 1141 was the only store not using `storage_type='memory'`. All 4 other stores use `storage_type='memory'` and work fine. The `data=[]` conflicts with callback registration.

**Error 2:** `IndexError: list index out of range` in `_prepare_grouping` — likely cascading from Error 1. Re-test after fixing Error 1. If persists, investigate CB-3 (line 1252), CB-9 (line 1933), CB-10 (line 2089).

**Error 3:** `BingX error 100001: Signature verification failed` — API auth issue, not code bug. User must verify `.env` keys.

Fix: build script `build_dashboard_v1_5_patch_runtime.py` applies one-line patch: `dcc.Store(id='store-bot-status', storage_type='memory')`.

### Decisions recorded
- Single patch: align store-bot-status with all other stores
- Error 100001 is user action (verify .env keys), not code
- `be_act` save bug and dashboard_v395 preset deferred to separate tasks

### State changes
- Single-line change to `bingx-live-dashboard-v1-5.py` line 1141
- Build script `build_dashboard_v1_5_patch_runtime.py` planned

### Open items recorded
- User re-runs dashboard after patch, verifies no KeyError/IndexError in first 30 seconds
- Signature errors persist until .env keys updated

### Notes
The v2 continuation prompt had only listed `be_act` — these runtime errors were new findings discovered at first launch.

---

## functional-orbiting-rabbit.md
**Date:** 2026-02-18
**Type:** Handoff document / Comprehensive session summary

### What happened
Vince ML v2 full handoff document created when context limit hit. Contains: critical error log, Vince ML v2 scope (in progress), full code audit of dashboard and engine, pending items.

**Critical error logged:** Claude inverted "under 60" to "past/over 60" when restating user direction — opposite signal meaning. Prevention rule: NEVER paraphrase directional statements; "under 60" = "< 60".

**Vince ML v2 scope (IN PROGRESS, not finalized):**
- Vince = trade research engine that reads trade CSV, enriches with indicator constellations at every bar, finds relationships using GPU (PyTorch), extracts robust parameters
- NOT a trade filter/classifier (previous v1 build = Vicky's architecture: XGBoost classifier, TAKE/SKIP decisions, reduces volume — wrong for rebate strategy)
- Evidence: 86% LSG across 2 unoptimized 10-coin runs (77K-90K trades each) — entries work, exits lose money
- Data flow: Stage 1 (Strategy → Trade CSV) → Stage 2 (Vince: Enricher → Relationship Engine → Cross-Validation → Dashboard)
- Key moments to snapshot: entry bar, MFE bar, MAE bar, breakeven bar, exit bar, phase transition bars, cloud cross bars

**Full code audit (9 files):**
- stochastics.py, clouds.py, state_machine_v383.py, four_pillars_v383.py: CORRECT
- backtester_v384.py: CORRECT with 1 known bug — scale-out entry commission double-count in Trade CSV (equity curve unaffected, LOW severity)
- position_v384.py, avwap.py, commission.py: CORRECT
- dashboard_v391.py (2338 lines): CORRECT — direct pass-through, no inflation
- Audit verdict: "The 77K-90K trades and 85-86% LSG numbers are REAL."

### Decisions recorded
- Vince = relationship research engine, NOT Vicky (trade classifier)
- NEVER reduce trade count (volume = $1.49B/year, rebate critical)
- Strategy-agnostic base (Andy = forex later)
- No prioritization of relationship questions
- "Under 60" = "< 60" — never to be paraphrased

### State changes
- Vince ML v2 scope IN PROGRESS, not finalized
- Full code audit completed; all engine math verified correct
- Scale-out commission double-count bug documented (not fixed)

### Open items recorded
1. Vince ML v2 scope not finalized — resume scoping
2. Scale-out commission bug — not fixed (equity unaffected, low priority)
3. RE-ENTRY logic — "currently totally wrongly programmed," deferred
4. Dashboard v3.9.2 build script written but not run by user
5. Architecture breakdown — next step after scope finalized

### Notes
This is the 2026-02-18 handoff document. Covers the pivot from Vicky (classifier) to Vince (research engine) architecture. dashboard_v391.py referenced here (2338 lines); later versions up to v394 were built in subsequent sessions.

---

## generic-humming-kurzweil.md
**Date:** Not explicitly stated (BingX connector setup context)
**Type:** Planning

### What happened
Plan for two tasks in the BingX connector:

**Task 1 — `historical_fetcher.py`:** Standalone script/importable module to pull full historical OHLCV from BingX public klines endpoint (`/openApi/swap/v3/quote/klines`, no auth) and save as parquet. Paginates backward using `startTime`/`endTime` (max 1440 per call). Saves to `data/historical/{symbol}_{timeframe}.parquet`. Deduplicates by timestamp on re-run (idempotent). Parquet schema: time (int64), open/high/low/close/volume (float64). CLI: `--symbol`, `--timeframe`, `--days`. Also importable as `fetch_and_save()`.

**Task 2 — Extract `set_leverage_and_margin()` to `exchange_setup.py`:** Move function and constants from main.py (~32 lines). Reason: main.py should wire components, not make raw API calls. Call site stays identical.

### Decisions recorded
- Public endpoint (no auth) for historical data
- Idempotent design with timestamp deduplication
- main.py: remove function + add `from exchange_setup import set_leverage_and_margin`

### State changes
- 3 files planned: `historical_fetcher.py` (new), `exchange_setup.py` (new), `main.py` (edit)

### Open items recorded
- Verification: pull 5 days BTC-USDT, re-run for dedup test, run main.py in demo mode

### Notes
Context note: Telegram already connected and working. `data_fetcher.py` only maintained 200-bar in-memory buffers before this plan (no persistence).

---

## giggly-nibbling-sunset.md
**Date:** Not explicitly stated
**Type:** Planning

### What happened
Plan to validate and promote dashboard v3.9.3 to production. Investigation revealed the Product Backlog P0.3 entry ("IndentationError at line 1972") was STALE — `py_compile` passes clean on the current v3.9.3 file. The indentation fix was completed at some point after the backlog entry was written.

v3.9.3 changes vs v3.9.2: (1) stale cache fix (`_pd = None` when settings change), (2) sweep symbol persistence across rerenders, (3) selectbox key fix (`sweep_drill_select`), (4) PDF download button (in-browser download).

Steps: (1) runtime validation — user runs streamlit, 7-item test checklist, (2) update 4 doc files if runtime passes (PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md), (3) add trailing newline to v3.9.3 (missing), (4) ask user before deleting 3 dead fix scripts.

### Decisions recorded
- Backlog entry was stale — not actually blocked
- Do NOT auto-delete old fix scripts — ask user first
- Doc updates deferred until runtime validation passes

### State changes
- v3.9.3 file: 2383 lines, py_compile PASS
- v3.9.2: 2371 lines (current production at time of writing)

### Open items recorded
- User must run 7-item runtime checklist
- 4 doc files to update after runtime passes

### Notes
None.

---

## goofy-dancing-summit.md
**Date:** Not explicitly stated (large file, 83.8KB — could not be read in full)
**Type:** Build specification

### What happened
Complete self-contained build specification for `bingx-live-dashboard-v1-1.py` — a Plotly Dash web app replacing the Streamlit read-only dashboard. This is the spec referenced by `fluttering-kindling-creek.md`. File is 83.8KB and was too large to read in full; findings based on preview and cross-references.

**Core architecture (from preview):**
- Dash 4.0.0, dash-ag-grid 33.3.3, Plotly, port 8051, single-file app
- Single data load point: `dcc.Interval` (60s) → reads state.json, trades.csv, config.yaml → dcc.Store → tab callbacks read from stores only
- 5 tabs: Operational, History, Analytics, Coin Summary, Bot Controls
- BingX API client replicated in dashboard (not imported from bot)
- `COLORS` dict module-level for dark theme
- `server = app.server` at module level for gunicorn
- Data sources: state.json (open positions with symbol/direction/grade/entry/sl/tp/qty/notional/order_id/atr_at_entry/be_raised), trades.csv (closed trades with exit reasons), config.yaml (editable sections)
- VPS: gunicorn on port 8051

Full spec covers all 14 callbacks, tab layouts, position action logic (Raise BE, Move SL), config editor, halt/resume.

### Decisions recorded
- Dash over Streamlit: Streamlit reruns on every click, wipes form state; Dash reactive callbacks preserve state
- Pattern-matching callbacks (MATCH selector) for per-row actions
- `suppress_callback_exceptions=True`
- Self-contained API signing in dashboard

### State changes
- Build spec created (83.8KB, 1795 lines per fluttering-kindling-creek.md reference)

### Open items recorded
- Build execution (per fluttering-kindling-creek.md)

### Notes
File is 83.8KB — largest plan file in this batch. Could not be read fully (output truncated at 2KB preview). Full spec details inferred from cross-references.

---

## groovy-seeking-yao.md
**Date:** 2026-02-28
**Type:** Research / Analysis

### What happened
Research document comparing all TTP (Trailing Take Profit) approaches for the BingX bot. Context: live account ($110, $5 margin × 10x) had 47 trades with 0 TP_HIT exits (46 SL_HIT, 1 EXIT_UNKNOWN). Root cause: `tp_atr_mult: null` set with no trailing TP replacement built. BE raise working but is a floor, not a profit-locker.

**6 TTP examples catalogued (E1-E6):** Fixed ATR TP, ATR Trailing (HTF), AVWAP 3-Stage, AVWAP 2σ + 10-Candle Counter, BingX Native Immediate, BingX Native with Activation.

**5 implementation approaches compared (A-E):**
- A: Fixed TP — 1 config line, 4/47 demo TP rate, misses runners
- B: Native Immediate — ~20 lines, premature exit on noise
- C: Native + Activation at 2×ATR — ~25 lines, exchange-managed after trigger, recommended
- D: AVWAP 2σ + 10-Candle + trailing — ~150 lines, highest risk, correct long-term
- E: Periodic SL Ratchet — ~40 lines, 60s polling gap, good complement

Recommendation: Approach C immediately (activation at 2×ATR, 2% callback), Approach D as future phase.

### Decisions recorded
- Approach C chosen: `TRAILING_STOP_MARKET` with `activationPrice = entry ± atr × 2`, `priceRate = 0.02`
- Fixed TP (A) rejected: wrong exit model, misses trend continuation
- Immediate trailing (B) rejected: fires on noise for small-cap coins
- AVWAP 2σ (D) deferred: 150 lines + AVWAP recalculation = highest risk for live bot
- E (ratchet) as complement, not primary

### State changes
- Research document only — no code written
- Session log planned: `06-CLAUDE-LOGS/2026-02-28-bingx-ttp-research.md`
- INDEX.md update noted as required

### Open items recorded
- Implementation of Approach C pending user decision
- Approach D deferred to future phase

### Notes
This document precedes the three-stage TTP architecture (be_act → ttp_act → ttp_dist) that was eventually built. Approach C is the conceptual precursor to that design.

---

## happy-humming-mccarthy.md
**Date:** 2026-02-18 Session 3
**Type:** Corrective plan / Project restructuring

### What happened
Plan to separate Vince and Vicky projects after discovering the "Vince ML Build" was actually Vicky's architecture (XGBoost classifier, TAKE/SKIP filtering) mislabeled as Vince.

**Part 1 — Create Vicky project folder `PROJECTS/vicky/`:** Move 11 files from four-pillars-backtester (with renames: `train_vince.py` → `train_vicky.py`, `vince_model.py` → `vicky_model.py`). 16 shared infrastructure files stay in four-pillars-backtester.

**Part 2 — Vince correct scope — parameter optimizer:** Vince = parameter sweep engine wrapping existing backtester. Optimizes stochastics (k1-k4, d_smooth, cross/zone levels), EMA clouds (all 3 pairs), AVWAP, SL/TP/BE, entry types. Objective: `net_pnl = gross_pnl - total_commission + total_rebate`. Sweep modes: grid search, Bayesian (Optuna), per-coin, per-tier. Output: `optimal_params.json` per coin. Vince stays in four-pillars-backtester: `scripts/optimize_vince.py` + `ml/parameter_optimizer.py`.

**Part 3 — MEMORY.md updates:** Add persona definitions, correct mislabeled sections.

**Part 4 — cloud3_allows_long/short:** Pre-existing, not introduced by this build; users entering below Cloud 3 flagged as potential backtester fix.

### Decisions recorded
- Vicky = trade classifier/filter, separate PROJECTS/vicky/
- Vince = parameter optimizer, stays in four-pillars-backtester
- No Python execution — all file moves + edits
- Vicky scripts import from four-pillars-backtester via sys.path

### State changes
- `PROJECTS/vicky/` folder structure planned with 11 files moved
- `models/four_pillars/` dir to be removed from backtester
- MEMORY.md update with persona definitions

### Open items recorded
- Execute 7 execution steps (create folder, move files, update imports, rename references, update MEMORY.md, append session log, remove empty dir)

### Notes
This is the Session 3 architectural correction (2026-02-18). `functional-orbiting-rabbit.md` (also 2026-02-18) redefines Vince again as a "relationship research engine" — scope evolved further within the same day. The parameter optimizer definition here and the relationship engine definition there are distinct — likely Session 3 happened before the handoff that became functional-orbiting-rabbit.md.

---

## harmonic-greeting-lemon.md
**Date:** Not explicitly stated (after 2026-02-28 v1-1 user testing)
**Type:** Planning

### What happened
Plan to build BingX Live Dashboard v1-2, addressing 8 issues filed by user after testing v1-1.

**8 issues and fixes:**
- FIX-1: White form inputs → CSS rules for 12 input/select/datepicker element types with dark bg/text/border
- FIX-2: White ag-grid backgrounds → dark CSS for `.ag-root-wrapper`, `.ag-overlay-no-rows-wrapper`, `.ag-header`
- FIX-3: No date range picker → replace `dcc.Checklist(today-filter)` with `dcc.DatePickerRange` on History + Analytics; update CB-8 and CB-9
- FIX-4: Slow tab switching → render all 5 tabs at startup, toggle visibility via `app.clientside_callback()` (pure JS, zero server round-trip)
- FIX-5: No timing diagnostics → `time.time()` markers around each data loader call in CB-1
- ANALYTICS-1: Expand from 7 to 13 metric cards — add net_pnl, Sharpe, maxDD%, avg W/L ratio, SL%/TP%/BE hits/LSG%
- ANALYTICS-3: Remove plotly toolbar (`displayModeBar: False`) + add axis labels

One build script `build_dashboard_v1_2.py` creates 3 files: `assets/dashboard.css` (overwrite, ~95 lines), `bingx-live-dashboard-v1-2.py` (new, ~1750 lines), `scripts/test_dashboard.py` (overwrite). Section-by-section delta table maps v1-1 line ranges to actions.

### Decisions recorded
- FIX-4: clientside callback for tab toggling (pure JS, not server-side)
- `suppress_callback_exceptions=True` kept (CB-5 still creates dynamic IDs)
- Date pickers default to None = no filter = show all trades
- `gross_pnl` kept as alias in `compute_metrics()` for backward compatibility
- Build script uses `.format()` not f-strings (escaped quote rule)
- Sharpe annualized using `math.sqrt(365)`, add `import math`

### State changes
- 3 output files planned
- CB-2 `render_tab` server callback deleted, replaced with clientside callback

### Open items recorded
- Build execution + 4 visual verification checks

### Notes
BE and LSG metrics (ANALYTICS-1) return "N/A" until bot adds `be_raised`/`saw_green` columns to trades.csv — those columns not yet in bot at plan time.

---

## hidden-frolicking-bunny.md
**Date:** References 2026-02-25 in content (log path dated)
**Type:** Planning

### What happened
Plan to fix two outstanding issues before bot restart: M2 (bot.log writing to wrong relative path locations) and UTC+4 logging preference. Context: bot STOPPED, all 67/67 tests passing, all code bugs fixed (E1/A1/M1/SB1/SB2). One signal had fired (GUN-USDT LONG B) but order failed due to E1 (now fixed).

**Fix 1 — M2:** `logging.FileHandler("bot.log")` used cwd — log appeared in `C:\Users\User\bot.log` AND a stale copy in project dir; Run 2 log was unfindable. New `setup_logging()` function: log at `Path(__file__).resolve().parent / "logs" / f"{today}-bot.log"`, creates `logs/` directory at startup.

**Fix 2 — UTC+4:** Custom `UTC4Formatter` class with `formatTime()` outputting `datetime.fromtimestamp(record.created, tz=utc4)`. Extend datetime import with `timedelta, date`.

Both fixes in `main.py` lines 14 (import) and 32-42 (logging setup).

Step 1 Checklist state: E1/A1/M1/SB1/SB2/SB3 checked, 67/67 tests passing, Telegram working, signal pipeline proven. Still pending: M2 fix, UTC+4, bot running continuously, first trade, Telegram entry alert, demo position visible in BingX VST.

### Decisions recorded
- Log file: absolute path to project dir `logs/` subdirectory, dated filename
- Timestamps: UTC+4 via custom Formatter class
- Follows MEMORY.md LOGGING STANDARD: dated file, logs/ dir, dual handler

### State changes
- Plan for 2-line changes to main.py (import extension + setup_logging replacement)

### Open items recorded
- Apply fixes, restart bot, confirm log at correct path with UTC+4 timestamps
- Wait for first trade to complete with E1 fix active

### Notes
M2 was item #8 in the overall Step 1 checklist. GUN-USDT LONG B signal fired in Run 1 but failed due to E1 (json.dumps spaces in order data) — E1 fix was the root cause of order failure.

---

## humble-sauteeing-pelican.md
**Date:** Not explicitly stated
**Type:** Planning

### What happened
Plan for WEEX Futures Screener v1. Context: TradingView Premium CEX screener uses absolute ATR making cross-coin comparison meaningless (BTC at $63k vs RIVER at $0.01 can't share same ATR threshold). This screener uses live WEEX data with normalized ATR and strategy-derived thresholds.

Function: fetch all WEEX perpetual futures symbols, get 300 bars OHLCV per symbol, run `compute_signals_v383`, extract live signal state, display ranked table, sidebar filters, optional auto-refresh.

WEEX API (public, no auth): contracts endpoint, OHLCV candles (`BTCUSDT_SPBL` format), all tickers. Rate limit 500 req/10s; use 0.02s sleep. Symbol format: contract list uses `cmt_btcusdt`, OHLCV uses `BTCUSDT_SPBL`.

ATR ratio threshold from commission math: `(0.001 × 2) / 2.0 × 3 = 0.003` — shown as formula in sidebar.

Screener columns: atr_ratio (normalized, cross-coin comparable), stoch_60, stoch_9, cloud3_dir, price_pos, signal_now, 24h_change_pct, 24h_vol_usd, vol_change_pct.

4 files to build: `utils/weex_fetcher.py`, `utils/weex_screener_engine.py`, `scripts/weex_screener_v1.py` (Streamlit, incremental loop), `tests/test_weex_fetcher.py`.

Reuses `compute_signals_v383` and `DEFAULT_SIGNAL_PARAMS` from existing screener_v1.py. Minimum 69 bars for signal validity.

### Decisions recorded
- Streamlit (not Dash) for screener
- Live signal state only — no backtest
- ATR ratio threshold formula shown in sidebar (not arbitrary number)
- WEEX taker rate defaults to 0.10% — verify actual tier at build time

### State changes
- 4 new files planned (no existing files modified)

### Open items recorded
- Verify futures OHLCV endpoint (spot candles vs separate contract candles)
- Verify WEEX taker rate for user's account
- Verify WHITEWHALE and RIVER appear in results

### Notes
Different from existing `screener_v1.py` (uses local Bybit parquets for backtested eligibility). This screener uses live WEEX API for live signal state detection.

---

## imperative-tumbling-bentley.md
**Date:** Not explicitly stated (v3.8.2 context = ~2026-02-11)
**Type:** Planning

### What happened
Plan for a capital utilization analyzer for v3.8.2 multi-coin backtests. User ran v3.8.2 on BERA (746 trades, -$94 net) and RIVER (881 trades, -$3.48 net) at $250 notional. User wants to know: idle capital, how many coins could run in parallel on $10K, combined P&L with 50% rebate.

One file: `PROJECTS/four-pillars-backtester/scripts/capital_utilization.py`. Inputs: two CSV files from Downloads folder.

Per-coin: build 5-min timeline, count open positions (0-4) per bar, compute max/avg concurrent, % time at each level, margin per bar ($250 × open_positions), peak/avg/idle margin, avg hold time, gross P&L scaled to $5000 notional, commission ($16/RT), rebate (50%), net P&L.

Combined: overlay BERA + RIVER timelines, combined margin per bar, idle capital = $10,000 - peak_combined_margin, max coins = `floor(idle_capital / max_margin_per_coin)`. Output: formatted table with BERA / RIVER / COMBINED columns.

### Decisions recorded
- $5000 notional per position ($250 margin at 20x)
- Commission: $16/RT
- Rebate: 50%

### State changes
- 1 new script planned

### Open items recorded
- User runs: `python scripts/capital_utilization.py`

### Notes
$16/RT commission figure used here. MEMORY.md shows taker rate 0.0008; at $5000 notional: $5000 × 0.0016 = $8.00/RT gross. The $16/RT figure appears inconsistent with current MEMORY.md commission constants — may reflect an older or different commission estimate from early in the project.

---

## CODE VERIFICATION

### elegant-weaving-sutherland.md
Referenced `scripts/build_native_trailing.py` as key deliverable.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_native_trailing.py` — file exists (untracked = newly created, not yet committed)

### enumerated-dazzling-squirrel.md
Referenced commit `"Vault update: BingX v1.5 (time sync, TTP, config tuning), backtester v391, session logs 2026-03-03 to 2026-03-05"`.
- Commit `e85b370` in current git log matches this message exactly — plan was executed.

### fluffy-singing-mango.md
Referenced `ws_listener.py` as new file to build.
- Git status shows `M PROJECTS/bingx-connector/ws_listener.py` (modified) — file exists and was modified. Plan was implemented.

### foamy-soaring-snowflake.md
Referenced `scripts/build_dashboard_v1_5_patch_runtime.py` as new build script.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_dashboard_v1_5_patch_runtime.py` — exists.

### eventual-tickling-stardust.md
Referenced `scripts/build_audit_fixes.py` for backtester and bingx-connector.
- Git status shows `?? PROJECTS/four-pillars-backtester/scripts/build_audit_fixes.py` — exists.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_audit_fixes.py` — exists.
