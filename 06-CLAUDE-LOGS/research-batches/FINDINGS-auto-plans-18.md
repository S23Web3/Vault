# Research Batch 18 — Auto-Plan Files Findings

**Batch:** 18 of 22
**Files processed:** 20
**Date processed:** 2026-03-06

---

## elegant-weaving-sutherland.md
**Date:** 2026-03-05
**Type:** Planning

### What happened
Detailed plan to switch the BingX bot's trailing take-profit (TTP) from a custom code-managed engine to BingX's native `TRAILING_STOP_MARKET` exchange order. The switch is config-toggled via a new `ttp_mode` key: `"native"` uses exchange trailing at tick-level, `"engine"` keeps the existing custom 5m-candle TTP. The native mode reuses existing `ttp_act` (0.008 = 0.8%) and `ttp_dist` (0.003 = 0.3%) params. Context: the custom TTP engine had a ~6min worst-case delay before trailing exit fires, whereas native runs tick-level.

### Decisions recorded
- New config key `ttp_mode: native` added under position section
- `_place_trailing_order()` gains `price_rate` parameter to override trailing rate
- `signal_engine.py` early-returns when `ttp_mode == "native"` to skip engine evaluation
- `position_monitor.py` skips `check_ttp_closes` and `check_ttp_sl_tighten` in native mode
- Critical bug fix: `_cancel_open_sl_orders` must exclude `TRAILING_STOP_MARKET` from cancellation (currently `"STOP" in "TRAILING_STOP_MARKET"` = True, so BE raise would cancel the native trail)
- `_detect_exit` must detect when trailing_order_id missing from open orders = it fired
- `ws_listener.py` adds `TRAILING_STOP_MARKET` detection before generic STOP handling
- Build script: `scripts/build_native_trailing.py` writes all 6 modified files

### State changes
- 6 files planned for modification: config.yaml, executor.py, signal_engine.py, position_monitor.py, ws_listener.py, state_manager.py
- `ttp_engine.py` untouched; dashboard deferred
- Breakeven raise remains active in native mode as safety net

### Open items recorded
- Manual verification required: set `ttp_mode: native` + `demo_mode: true`, run bot, verify trailing order placed, BE raise does NOT cancel trailing, exit detected as `TRAILING_EXIT` in trades.csv
- Switchback test: set `ttp_mode: engine`, verify three-stage pipeline restored

### Notes
- Previous native trailing attempt failed because activation was ATR-based (too far) and callback was 2% (too wide). This plan uses percentage-based params matching the working TTP config.
- Three-stage interaction table provided: BE raise (+0.4%), TTP activation (+0.8%), trail (0.3% callback).

---

## eventual-plotting-pony.md
**Date:** Not stated (no date in filename or content)
**Type:** Guided instructions / Setup document

### What happened
Step-by-step instructions for connecting the BingX bot to Telegram by filling in `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the `.env` file. Covers: creating a bot via BotFather, getting Chat ID, editing `.env`, testing with a one-liner, and running the bot. Noted that code (`notifier.py`, `main.py`) is already fully built and only the placeholder values in `.env` are blocking alerts.

### Decisions recorded
- No quotes, no spaces around `=` in `.env`
- Test command provided: Python one-liner to POST to Telegram API and confirm 200/ok response before running bot

### State changes
- No code changes — purely a user instruction document
- Files involved: `.env` (user edits), `notifier.py` and `main.py` (read-only reference)

### Open items recorded
- User must complete all 5 steps and check off `Telegram alert received` in `STEP1-CHECKLIST.md`

### Notes
- None.

---

## eventual-tickling-stardust.md
**Date:** 2026-03-03
**Type:** Fix plan / Audit execution

### What happened
Plan to execute a full logic audit's findings on `cuda_sweep.py`, `dashboard_v394.py`, and BingX connector files via a single build script `build_audit_fixes.py`. The audit was completed in a previous session; this plan applies fixes in priority order.

**Critical fixes:**
1. Commission split in cuda_sweep.py: taker entry (0.0008) vs maker exit (0.0002) — previously both sides used 0.0008, overstating P&L by 0.06% per RT
2. pnl_sum missing entry commission — `pnl_sum += net_pnl - entry_comm` at both exit points
3. win_rate displayed as raw decimal in 3 table locations in dashboard_v394.py — format to `* 100` and rename to `win_rate%`
4. HIGH #4 (TTP state lost on restart): REASSESSED — already fixed (code at signal_engine.py lines 113-127 restores from persisted fields). No action.
5. WSListener dies permanently after 3 failures with no alert — increase MAX_RECONNECT to 10, add exponential backoff, write `logs/ws_dead_{timestamp}.flag`
6. `_place_market_close()` missing `reduceOnly` — add as defensive measure (no downside in hedge mode)
7. `saw_green` uses `>` instead of `>=` at cuda_sweep.py lines 163/171

### Decisions recorded
- CRITICAL #1 & #2 resolved with split commission accounting: `entry_comm = notional * taker_rate`, `exit_comm = notional * maker_rate`
- HIGH #4 confirmed already fixed — skipped
- HIGH #6 downgraded to LOW (hedge mode + positionSide sufficient), but add `reduceOnly: "true"` defensively anyway
- All 6 entry blocks in cuda kernel: change `comm_per_side` → `entry_comm`
- `maker_rate=0.0002` added to `run_gpu_sweep()` and `run_gpu_sweep_multi()` signatures

### State changes
- 4 files planned for patching: `engine/cuda_sweep.py`, `scripts/dashboard_v394.py`, `bingx-connector/ws_listener.py`, `bingx-connector/position_monitor.py`
- Build script: `scripts/build_audit_fixes.py` (string replacement, no full rewrite)
- All prior GPU sweep P&L numbers are overstated by 0.06% × notional per RT

### Open items recorded
- User must run GPU Sweep on one coin and verify `win_rate%` column shows values like `42.3` not `0.423`
- User must verify net_pnl figures are lower than previous runs (correct accounting)

### Notes
- Medium/low issues explicitly deferred: stale detection for sweep params, shared pool capital enforcement, TTP mid-bar timing, race condition TTP close vs exchange SL/TP, commission rate fallback mismatch, no slippage protection, C trades checkbox UI.

---

## expressive-painting-taco.md
**Date:** Not stated in content
**Type:** Planning — BingX bot enhancements

### What happened
Plan for two deliverables: (1) Windows Task Scheduler auto-start for the BingX bot with crash recovery via PowerShell wrapper, and (2) improved Telegram message formatting (HTML bold `<b>` tags + newlines instead of single-line dumps). One build script `build_autostart_and_tg.py` creates 3 new files and modifies 3 existing files.

**New files created:**
- `scripts/run_bot.ps1` — PowerShell crash-recovery loop (restarts on non-zero exit, waits 30s, clean exit code 0 = don't restart)
- `scripts/bingx-bot-task.xml` — Task Scheduler XML (AtStartup trigger, 60s delay, run hidden)
- `scripts/install_autostart.ps1` — admin script to register/verify/unregister task

**Files modified (with backups):**
- `executor.py`: 3 Telegram calls formatted with `<b>ORDER FAILED</b>`, `<b>ORDER ID UNKNOWN</b>`, `<b>ENTRY</b>`
- `position_monitor.py`: 4 Telegram calls formatted with `<b>EXIT</b>`, `<b>DAILY SUMMARY</b>`, `<b>HARD STOP</b>`, `<b>WARNING</b>`
- `main.py`: 3 Telegram calls formatted with `<b>BOT STARTED</b>`, `<b>BOT STOPPING</b>`, `<b>BOT STOPPED</b>`

### Decisions recorded
- VPS (Hostinger Jakarta) cannot reach BingX VST API — bot runs locally on Windows
- Demo mode first ("let it burn VST", 47 coins, 5m)
- Clean exit (code 0) = intentional stop, no restart; non-zero = crash, restart after 30s
- All 10 exact string replacements specified with old/new code blocks

### State changes
- 6 files total touched (3 new, 3 modified with backups)
- py_compile validates every .py file touched

### Open items recorded
- Verification: run build script, test bot manually via PS1, verify TG messages, install as admin, reboot test, test crash recovery

### Notes
- Context: Indonesian VPS IPs blocked from BingX VST API.

---

## fizzy-humming-crab.md
**Date:** 2026-03-04
**Type:** Research / Strategy specification

### What happened
Comprehensive position management study document built from two live TradingView Replay walkthroughs: PUMPUSDT LONG and PIPPINUSDT SHORT (both 5m chart, both trend-hold type). Documents the full trade lifecycle: HTF direction (three-layer system), entry detection (sequential stochastic confirmation + BBW + TDI), gate check (stoch 60 K vs D), trend hold management (TDI 2-candle rule, BBW health monitor, AVWAP trailing, Ripster cloud milestones), add-ons, and exit rules.

**Key confirmed rules:**
- Three-layer HTF system: Layer 1 = 4h/1h session bias, Layer 2 = 15m MTF clouds on 5m chart, Layer 3 = 5m entry timing
- All 4 stochastics (9, 14, 40, 60) must have K cross above/below D — sequential process, stoch 9 crosses first (alert), wait for others
- BBW spectrum must cross from below to above MA for entry confirmation
- TDI price line must be on correct side of MA at entry AND is a hard 2-candle exit rule
- SL = 2 × ATR(14) validated against structural level
- Stoch 60 K vs D crossing = gate opens = trend-hold mode
- AVWAP is the trailing SL anchor (plain from trade start for longs, +2sigma for shorts, tightened on BBW red)
- Ripster Cloud 4 value FROZEN at time of confirmation = TP target (doesn't move with cloud)
- Add-ons require stoch 9/14 to reach opposite zone while 40/60 hold trend direction

### Decisions recorded
- N=10 bars for recent-zone check (K must have been below 20 / above 80 within last 10 bars) — flagged for Vince optimization
- MTF clouds = hold duration modulator (not hard binary): price above MTF = stay in longer; below MTF = quick close
- ATR role: thermometer only (SL sizing + confirmation), NOT central to phase transitions (contradicts ATR-SL-MOVEMENT-BUILD-GUIDANCE.md)
- "This is not a patch on v386. It is a different strategy architecture."

### State changes
- Study document only — no code written
- State machine summary diagram provided (FLAT → MONITORING → IN TRADE → TREND HOLD with all transitions)
- Full comparison table: User's Actual Trading vs ATR-SL-MOVEMENT Spec vs AVWAP 3-Stage vs v386

### Open items recorded
- 6 open questions: SL-1 (what if 2 ATR doesn't align with structure?), SL-2 (what counts as structure?), GATE-1 (numeric threshold for K/D distance?), BE-1 (two BE methods interchangeable?), TRAIL-1 (AVWAP variant selection), CLOUD-1 (frozen Cloud 4 target longs-only?), TP-1 (cloud target vs % target?)
- Document explicitly states: "No code should be written until the user explicitly approves the rules"

### Notes
- BBW-1 (BBWP thresholds for red/blue/dark blue) was marked RESOLVED as "flagged for Vince research" — no numeric boundaries established yet.

---

## floating-jingling-valiant.md
**Date:** 2026-03-05 (from content)
**Type:** Audit / Quality review

### What happened
Thoroughness audit of the `2026-03-05-next-chat-prompt.md` continuation prompt, performed while the bot was RUNNING (collecting 48h live data, must not be restarted). Found 2 errors and 3 gaps in the prompt, verified 8 claims as correct.

**Errors found:**
1. Task 1 function mismatch: prompt says `compute_signals()` accepts `require_stage2`/`rot_level`, but dashboard_v394.py line 57 actually calls `compute_signals_v383()` from `four_pillars_v383_v2.py`, which does NOT accept those params
2. Task 2 already 80% done: dashboard v1.5 EXISTS (133K, built 2026-03-04), with BUG-4/BUG-1b/BUG-2/BUG-5 all fixed; only `be_act` save callback missing

**Gaps found:**
1. No bot restart constraint in prompt
2. Stale runtime data (PnL snapshot, RENDER positions)
3. Import switch not mentioned if Task 1 changes signal function

### Decisions recorded
- Create corrected v2 prompt, do NOT overwrite original
- Fix 1: Add "CONSTRAINT: Bot is RUNNING -- DO NOT RESTART" section
- Fix 2: Specify import switch (line 57 → `from signals.four_pillars import compute_signals`)
- Fix 3: Rewrite Task 2 scope to only `be_act` save callback
- Fix 4: Replace stale runtime data with instruction to check current logs

### State changes
- New file planned: `06-CLAUDE-LOGS/plans/2026-03-05-next-chat-prompt-v2.md`
- Original file preserved

### Open items recorded
- Read new v2 file back to confirm all 5 fixes present

### Notes
- Content of this file is IDENTICAL to fluffy-singing-mango.md — both files contain the same audit document. This is a duplicate plan file.

---

## fluffy-singing-mango.md
**Date:** 2026-02-27
**Type:** Planning — BingX bot improvement

### What happened
Comprehensive BingX bot improvement plan created after scraping the full BingX API v3 reference (224 endpoints, 849KB). Cross-referenced against current bot code. Three major discoveries affecting live trading accuracy:
1. Commission rate hardcoded wrong: bot uses 0.0012, real rate is 0.0016 RT — every recorded trade understated commission by 33%
2. Position history endpoint gives BingX-calculated PnL (netProfit) with actual commission + funding fees — ground truth not used
3. WebSocket ORDER_TRADE_UPDATE gives real-time fills — eliminates EXIT_UNKNOWN; entry price uses mark_price (wrong) not fill price (avgPrice)

**P0 fixes (live trading blockers):**
- FIX-1: Query `GET /openApi/swap/v2/user/commissionRate` at startup, use dynamic rate
- FIX-2: Use `data.avgPrice` from order POST response as entry_price
- FIX-3: Validate SL direction before order (LONG sl_price < mark_price, SHORT sl_price > mark_price)

**P1 improvements:**
- IMP-1: New `ws_listener.py` module with WebSocket ORDER_TRADE_UPDATE daemon thread
- IMP-2: `scripts/reconcile_pnl.py` standalone PnL audit vs BingX positionHistory

**P2 improvements:**
- IMP-3: Handle error 101209 (max position value exceeded) with halved quantity retry
- IMP-4: Cooldown filter (`cooldown_bars: 3`) to match backtester
- IMP-5: Startup commission fetch consolidation

Full Ollama-based build runbook provided for each step (steps 1-11), including exact prompts to send to Ollama, bash commands for py_compile and diff, file copy sequences.

### Decisions recorded
- Execution via Ollama (local LLM) to generate code modifications
- Two new files: `ws_listener.py`, `scripts/reconcile_pnl.py`
- 5 files to modify: `position_monitor.py`, `executor.py`, `main.py`, `state_manager.py`, `risk_gate.py`, `config.yaml`
- VPS cannot reach BingX VST API — local running only

### State changes
- Improvement catalog documented but not yet implemented (planning document)
- All prior trade PnL records in bot logs have understated commission by 33%

### Open items recorded
- 11-step build runbook for implementation
- P2/P3 deferred: batch cancel on shutdown, Cancel All After safety timer, trailing stop option

### Notes
- ws_listener.py was subsequently built in a later session (file exists in repo per git status). This plan appears to predate that implementation.

---

## fluttering-kindling-creek.md
**Date:** Not stated (no date in content)
**Type:** Planning — Dashboard build

### What happened
Build plan for `bingx-live-dashboard-v1-1.py` — a Plotly Dash web app replacing the Streamlit read-only dashboard. References a 1795-line build spec at `C:\Users\User\.claude\plans\goofy-dancing-summit.md`. Notes that previous session finalized the spec but hit context limit before writing code. This plan executes the spec without further design decisions.

**Deliverables:** 3 files:
1. `bingx-live-dashboard-v1-1.py` (~700 lines) — Dash 4.0 app, port 8051, 5 tabs (Operational, History, Analytics, Coin Summary, Bot Controls), 14 callbacks, ag-grid, dark theme, BingX API integration
2. `assets/dashboard.css` (~20 lines) — dark theme overrides
3. `scripts/test_dashboard.py` (~170 lines) — unit tests

**Key technical decisions confirmed:**
- `suppress_callback_exceptions=True`
- `prevent_initial_call=False` for CB-1 and CB-2 only
- CB-6/CB-7 both output to `pos-action-status` (allowed, different inputs)
- `fetch_all_mark_prices` uses `ThreadPoolExecutor(max_workers=8)`
- API signing replicated in dashboard (not imported from bot internals)
- Atomic writes via tmp + `os.replace()`
- Dual logging with `TimedRotatingFileHandler`

### Decisions recorded
- Load Dash skill (`/dash`) mandatory per MEMORY.md before any Dash code
- Existing v1 (Streamlit) must NOT be touched

### State changes
- No code written yet — plan to execute existing spec
- References spec file: `C:\Users\User\.claude\plans\goofy-dancing-summit.md`

### Open items recorded
- Build steps 1-7 listed; user verifies: py_compile, test_dashboard.py, actual launch at port 8051

### Notes
- This is a pre-execution plan referencing goofy-dancing-summit.md (the full build spec, batch 18 file #13).

---

## foamy-soaring-snowflake.md
**Date:** 2026-03-05
**Type:** Fix plan — Runtime error resolution

### What happened
Dashboard v1.5 passed `py_compile` but first launch revealed 3 errors. The v2 continuation prompt had only listed `be_act` bug — these runtime errors are new findings.

**Errors:**
1. `KeyError: "Callback function not found for output 'store-bot-status.data'."` at line 1141 — `dcc.Store(id='store-bot-status', data=[])` is the only store not using `storage_type='memory'`; the `data=[]` conflicts with callback registration
2. `IndexError: list index out of range` in `_prepare_grouping` — likely cascading from Error 1 (Dash internal misalignment)
3. `BingX error 100001: Signature verification failed` — API credential issue, not a code bug

**Fix:**
- Patch 1: Change `dcc.Store(id='store-bot-status', data=[])` → `dcc.Store(id='store-bot-status', storage_type='memory')` (line 1141)
- Patch 2: If IndexError persists, investigate CB-3, CB-9, CB-10 callbacks

### Decisions recorded
- Build script: `scripts/build_dashboard_v1_5_patch_runtime.py` patches base file in-place
- Error 100001 is user action (verify `.env` keys), not a code fix
- Patch 1 aligns store-bot-status with all other stores

### State changes
- Single-line change to `bingx-live-dashboard-v1-5.py` line 1141
- `be_act` save bug deferred (separate task from v2 prompt)
- dashboard_v395 backtester preset deferred

### Open items recorded
- User must re-run dashboard after patch, verify no KeyError/IndexError in first 30 seconds
- Signature errors will persist until `.env` keys updated

### Notes
- The v2 continuation prompt (`2026-03-05-next-chat-prompt-v2.md`) only listed `be_act` — this plan discovered additional runtime errors not previously known.

---

## functional-orbiting-rabbit.md
**Date:** 2026-02-18
**Type:** Handoff document / Comprehensive session summary

### What happened
Full handoff document for Vince ML v2, created when context limit hit. Contains: critical error log, Vince ML v2 scope (in progress), full code audit of dashboard and engine, and pending items.

**Critical error:** Claude inverted "under 60" to "past/over 60" when restating user direction — opposite signal meaning. Prevention rule documented: NEVER paraphrase directional statements.

**Vince ML v2 scope (IN PROGRESS):**
- Vince = trade research engine (NOT a trade filter/classifier)
- Reads trade CSV from any strategy's backtester, enriches with full indicator constellation at every bar
- Finds relationships between indicator states and trade outcomes using GPU (PyTorch)
- Evidence from 2 unoptimized 10-coin runs: 86% LSG (Lost Saw Green) is systemic — entries work, exits lose money
- Data flow: Stage 1 (Strategy → Trade CSV) → Stage 2 (Vince: Enricher → Relationship Engine → Cross-Validation → Dashboard)
- Previous v1 build was wrong (Vicky architecture: XGBoost classifier for TAKE/SKIP — reduces volume, wrong for rebate strategy)

**Full code audit (9 files):**
- Signal pipeline (stochastics, clouds, state_machine_v383, four_pillars_v383): CORRECT
- backtester_v384.py: CORRECT with ONE known bug — scale-out entry commission double-count in Trade CSV (equity curve unaffected)
- position_v384.py, avwap.py, commission.py: CORRECT
- dashboard_v391.py: CORRECT — direct pass-through from engine, no inflation
- Capital model v2: NOT audited in detail

**Audit verdict:** The 77K-90K trades and 85-86% LSG numbers are REAL.

### Decisions recorded
- Vince = relationship research engine. Vicky = trade classifier (wrong architecture for rebate strategy)
- NEVER reduce trade count — volume = $1.49B/year, critical for rebate
- Strategy-agnostic base (Andy = forex later)
- No prioritization of relationship questions — data shows what's there
- "Under 60" = "< 60", never to be paraphrased

### State changes
- Vince ML v2 scope IN PROGRESS, not finalized
- Code audit completed on all engine files
- Known bug documented: scale-out entry commission double-count in Trade CSV

### Open items recorded
1. Vince ML v2 scope not finalized — resume scoping
2. Scale-out commission bug — not fixed, low priority (equity unaffected)
3. RE-ENTRY logic — "currently totally wrongly programmed," deferred after scope
4. Dashboard v3.9.2 build script written but not run by user
5. Architecture breakdown — next step after scope finalized

### Notes
- This is a comprehensive handoff from early in the project (2026-02-18), covering the pivot from Vicky (classifier) to Vince (research engine) architecture.
- dashboard_v391.py referenced here (2338 lines); later versions up to v394 were built in subsequent sessions.

---

## generic-humming-kurzweil.md
**Date:** Not stated
**Type:** Planning — BingX bot utilities

### What happened
Plan for two tasks in the BingX connector:
1. Create `historical_fetcher.py` — standalone script to pull full historical OHLCV data from BingX public klines endpoint and save as parquet (idempotent, deduplicates by timestamp). CLI usage and importable `fetch_and_save()` function. Paginates using startTime/endTime, max 1440 bars per call.
2. Extract `set_leverage_and_margin()` from `main.py` (lines ~63-94) into new `exchange_setup.py` — separates exchange API logic from orchestration.

### Decisions recorded
- Uses `/openApi/swap/v3/quote/klines` (public, no auth needed)
- Parquet schema: time (int64), open/high/low/close/volume (float64)
- `data/historical/{symbol}_{timeframe}.parquet` save location
- `main.py` after extraction imports from `exchange_setup.py`; call site stays identical

### State changes
- 3 files planned: `historical_fetcher.py` (new), `exchange_setup.py` (new), `main.py` (edit)

### Open items recorded
- Verification: pull 5 days BTC-USDT, re-run same command (dedup test), run main.py in demo mode

### Notes
- Context: Telegram already connected. `data_fetcher.py` only maintains 200-bar in-memory buffers — no persistence before this plan.

---

## giggly-nibbling-sunset.md
**Date:** Not stated
**Type:** Planning — Dashboard promotion

### What happened
Plan to validate and promote Dashboard v3.9.3 to production. Investigation revealed the `PRODUCT-BACKLOG.md` P0.3 entry ("IndentationError at line 1972") was STALE — `py_compile` passes clean on the current v3.9.3 file. The indentation fix was completed at some point after the backlog entry was written.

**v3.9.3 changes vs v3.9.2:**
1. Stale cache fix: `_pd = None` when sidebar settings change, portfolio rendering guarded by `if _pd is not None`
2. Sweep symbol persistence across rerenders
3. Selectbox key fix (`sweep_drill_select`)
4. PDF download button (in-browser download after generation)

**Plan steps:**
1. Runtime validation (user runs `streamlit run dashboard_v393.py`, 7-item checklist)
2. Update docs: PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md
3. Add trailing newline to v3.9.3 (missing)
4. Clean up dead fix scripts (ask user first)

### Decisions recorded
- The v3.9.3 indentation bug was already fixed — backlog entry was stale
- Documentation updates deferred until runtime validation passes

### State changes
- v3.9.3 file: 2383 lines, py_compile PASS
- v3.9.2: 2371 lines, current production at time of writing

### Open items recorded
- 7-item runtime checklist must pass before doc updates
- Ask user about deleting 3 dead fix scripts

### Notes
- None.

---

## goofy-dancing-summit.md
**Date:** Not stated
**Type:** Build specification — large file (83.8KB)

### What happened
Comprehensive self-contained build specification for `bingx-live-dashboard-v1-1.py` — a Plotly Dash web app replacing the Streamlit read-only dashboard. Full spec for a 5-tab interactive dashboard with position management capabilities. This is the spec referenced by `fluttering-kindling-creek.md` (batch 18 file #8).

**Core architecture (from first 200 lines read):**
- Dash 4.0.0, dash-ag-grid, port 8051
- Single-file app, no multi-page routing
- Single data load point: `dcc.Interval` (60s) → reads state.json, trades.csv, config.yaml → writes to dcc.Store → all tab callbacks read from stores only
- 5 tabs: Operational, History, Analytics, Coin Summary, Bot Controls
- BingX API client replicated in dashboard (not imported from bot internals); live API only
- Color constants module-level (`COLORS` dict with bg/panel/text/muted/green/red/blue/orange/grid)
- `server = app.server` at module level for gunicorn
- VPS deployment: gunicorn on port 8051 with BasicAuth recommended before deployment

**Data sources:**
- `state.json`: open_positions dict with symbol, direction, grade, entry/sl/tp prices, quantity, notional, order_id, atr_at_entry, be_raised
- `trades.csv`: closed trade log with exit_reason values SL_HIT/TP_HIT/EXIT_UNKNOWN/SL_HIT_ASSUMED
- `config.yaml`: editable sections (connector, four_pillars, risk, position)

**Note:** Only first 200 lines of 83.8KB file read via persisted output. Full spec covers all 14 callbacks, tab layouts, position action logic, config editor, halt/resume.

### Decisions recorded
- Dash over Streamlit: Streamlit reruns on every click, wiping form state; Dash reactive callbacks preserve state
- Pattern-matching callbacks (MATCH selector) required for per-row Raise BE / Move SL buttons
- `suppress_callback_exceptions=True` because tab IDs don't exist at startup

### State changes
- Build spec only — no code written yet (code written in subsequent session)

### Open items recorded
- Full spec to be executed; referenced build plan in `fluttering-kindling-creek.md`

### Notes
- File is 83.8KB — the largest plan file in the batch. Full content not read (preview only due to size).

---

## groovy-seeking-yao.md
**Date:** 2026-02-28
**Type:** Research / Analysis

### What happened
Research document analyzing trailing take-profit (TTP) options for the live BingX bot. Context: live account ($110, $5 margin × 10x) had 47 trades with 0 TP_HIT exits (46 SL_HIT, 1 EXIT_UNKNOWN). Root cause: `tp_atr_mult: null` set in config with no trailing TP replacement built.

**6 TTP examples catalogued (E1-E6):**
- E1: Fixed ATR TP (already tried in demo, 4/47 = 8.5% TP rate)
- E2: ATR Trailing with HTF ATR activation (2026-02-02 build spec)
- E3: AVWAP 3-Stage Trailing (v3.8.2 Pine Script)
- E4: AVWAP 2σ + 10-Candle Counter (confirmed design)
- E5: BingX Native Trailing immediate
- E6: BingX Native Trailing with activation

**5 approaches compared:**
- A: Fixed TP — trivial (1 config line), deterministic, leaves money on table
- B: Trailing immediate — ~20 lines, premature exit risk on small caps
- C: Trailing + activation (2×ATR) — ~25 lines, exchange-managed after activation, recommended
- D: AVWAP 2σ + 10-candle + TRAILING_STOP_MARKET — ~150 lines, highest complexity, correct long-term
- E: Periodic SL ratchet — ~40 lines, 60s polling gap, good complement

### Decisions recorded
- Recommendation: phased — Approach C immediately, Approach D later
- Why not A: wrong exit model, misses runners
- Why not B: activates on noise, premature exits on small-cap coins
- Why not D now: highest risk for live bot, 150 lines + AVWAP recalculation per position per bar
- Why not E alone: 60s polling gap unreliable as primary exit

**Implementation plan (Approach C):**
- Modify `executor.py` — add trailing order after SL order placement
- Modify `config.yaml` — add `trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`
- Add test in `tests/test_executor.py`

### State changes
- Research document only — no code written yet
- Session log to create: `06-CLAUDE-LOGS/2026-02-28-bingx-ttp-research.md`
- INDEX.md update required

### Open items recorded
- Implementation of Approach C pending user decision
- Approach D deferred to future phase

### Notes
- This document predates the three-stage TTP engine that was eventually built (be_act → ttp_act → ttp_dist). The recommended "Approach C" appears to be the precursor to that design.

---

## happy-humming-mccarthy.md
**Date:** 2026-02-18 Session 3
**Type:** Corrective plan / Project restructuring

### What happened
Plan to separate Vince and Vicky projects after discovering that the "Vince ML Build" was actually Vicky's architecture (XGBoost classifier, trade filtering) mislabeled as Vince.

**Part 1: Create Vicky project folder (`PROJECTS/vicky/`):**
- 11 files to MOVE from four-pillars-backtester to vicky/ (renamed where needed: train_vince.py → train_vicky.py, vince_model.py → vicky_model.py, etc.)
- 16 files stay in four-pillars-backtester as shared infrastructure (backtester, signals, data, ML utilities)

**Part 2: Vince correct scope — Parameter Optimizer:**
- Vince = parameter sweep engine wrapping existing backtester as inner loop
- Optimizes: stochastics (k1-k4 lengths, d_smooth, cross_level, zone_level), clouds (all 3 EMAs), AVWAP, SL/TP/BE, entry types
- Objective: `net_pnl = gross_pnl - total_commission + total_rebate`
- Sweep modes: grid search, Bayesian (Optuna), per-coin, per-tier
- Output: `optimal_params.json` per coin with metrics (net_pnl, trade_count, win_rate, max_drawdown, rebate_earned, sharpe)
- Vince stays in `four-pillars-backtester/`: `scripts/optimize_vince.py` + `ml/parameter_optimizer.py`

**Part 3: MEMORY.md updates** — add persona definitions, correct "VINCE ML Build" to "VICKY ML Build (mislabeled)"

**Part 4: cloud3_allows_long/short** — pre-existing in engine, not introduced by this build; users entering below cloud 3 is potential backtester fix (separate scope)

### Decisions recorded
- Vicky = trade classifier/filter, separate project folder
- Vince = parameter optimizer, stays in four-pillars-backtester
- No Python execution — all file moves + edits
- Vicky scripts import from four-pillars-backtester via sys.path

### State changes
- `PROJECTS/vicky/` folder created with 11 files moved
- `models/four_pillars/` dir removed from backtester
- `train_vince.py` removed from backtester/scripts
- MEMORY.md updated with persona definitions

### Open items recorded
- Session log to append to `06-CLAUDE-LOGS/2026-02-18-vince-ml-build.md`
- cloud3_allows_long fix deferred to separate scope

### Notes
- This corrective plan (Session 3 of 2026-02-18) represents the architectural pivot from Vicky to properly separating the two personas. Vince's scope was reset from ML classifier to parameter optimizer.
- However, `functional-orbiting-rabbit.md` (also 2026-02-18) redefines Vince AGAIN as a "relationship research engine" — suggesting further scope evolution within the same day or later that day.

---

## harmonic-greeting-lemon.md
**Date:** Not stated
**Type:** Planning — Dashboard build

### What happened
Build plan for `bingx-live-dashboard-v1-2.py`. User tested v1-1 live on 2026-02-28 and filed 8 issues. Plan implements all 8 fixes via a build script that produces 3 files.

**8 issues and fixes:**
- FIX-1: White form inputs → dark CSS rules for all input types, radio, checklist, Select components, DateRangePicker
- FIX-2: White ag-grid backgrounds → dark CSS for `.ag-root-wrapper`, `.ag-overlay-no-rows-wrapper`, `.ag-header`
- FIX-3: No date range picker → replace `dcc.Checklist(today-filter)` with `dcc.DatePickerRange` on History + Analytics tabs; update CB-8 and CB-9 signatures
- FIX-4: Slow tab switching → render all 5 tabs at startup, toggle visibility via `app.clientside_callback()` (pure JS, zero server round-trip)
- FIX-5: No timing diagnostics → `time.time()` markers around each data loader in CB-1
- ANALYTICS-1: Professional metrics → expand from 7 to 13 cards, add sharpe/maxDD%/W-L ratio/SL%/TP%/BE hits/LSG%
- ANALYTICS-3: Chart cleanup → `config={'displayModeBar': False}` on all 4 graphs, add xaxis_title where missing

**Section-by-section delta provided** mapping v1-1 line ranges to action (verbatim/rewrite/delete).

### Decisions recorded
- `suppress_callback_exceptions=True` kept — CB-5 still creates dynamic IDs
- `hist-today-filter` component removed — only CB-8 references it
- Date pickers default to None = "no filter" = show all trades
- `gross_pnl` kept as alias for `net_pnl` in compute_metrics() — grade comparison uses this key
- Build script uses `.format()` not f-strings (escaped quote rule)
- `math.sqrt(365)` for Sharpe annualization — add `import math`

### State changes
- 3 output files: `assets/dashboard.css` (overwrite, 28→~95 lines), `bingx-live-dashboard-v1-2.py` (new, ~1750 lines), `scripts/test_dashboard.py` (overwrite with v1-2 references + new tests)
- CB-2 (`render_tab` server callback) → deleted and replaced with clientside callback

### Open items recorded
- Verification: run build, run tests, run dashboard, 4 visual checks listed

### Notes
- `be_raised` / `saw_green` columns noted as "not yet in bot" at the time — `BE Hits` and `LSG%` metrics return "N/A" until bot adds those columns.

---

## hidden-frolicking-bunny.md
**Date:** References 2026-02-25 in content; no explicit date stated
**Type:** Planning — Bot logging fixes

### What happened
Plan to fix two outstanding issues before bot restart: M2 (bot.log relative path writing to wrong locations) and UTC+4 logging preference. Context: bot is STOPPED, all 67/67 tests passing, all code fixes (E1/A1/M1/SB1/SB2) applied and verified.

**Problem M2:** `logging.FileHandler("bot.log")` uses cwd, so log appeared in `C:\Users\User\bot.log` AND a stale copy in the project dir. Run 2 log was unfindable.

**Fix:** New `setup_logging()` function in `main.py` with:
- Absolute path: `Path(__file__).resolve().parent / "logs"`
- Dated filename: `logs/YYYY-MM-DD-bot.log`
- `logs/` directory created at startup
- Custom `UTC4Formatter` class with `formatTime()` method outputting UTC+4 timestamps
- Dual handler (file + console StreamHandler)

**Fix 2:** Extend datetime import to include `timedelta, date` (needed for UTC+4 offset and dated filename).

### Decisions recorded
- Log file always in project dir regardless of cwd
- Timestamps in UTC+4 for user's timezone
- Follows MEMORY.md LOGGING STANDARD: dated file, `logs/` dir, dual handler

### State changes
- `main.py` lines 14 (import) and 32-42 (logging setup) modified
- Log path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\2026-02-25-bot.log`

### Open items recorded
- After applying fixes: restart bot, confirm log at correct path, confirm UTC+4 timestamps, confirm startup checks pass, wait for first trade to confirm E1 fix end-to-end
- Step 1 Checklist: M2 fix, UTC+4 logging, bot running continuously, first trade, Telegram alert, demo position visible — all pending at time of writing

### Notes
- Step 1 Checklist shows GUN-USDT LONG B signal fired in Run 1 but failed due to E1 (json.dumps spaces) — E1 now fixed.

---

## humble-sauteeing-pelican.md
**Date:** Not stated
**Type:** Planning — New feature build

### What happened
Plan for WEEX Futures Screener v1 — a live signal state screener for WEEX perpetual futures. Motivation: TradingView Premium CEX screener uses absolute ATR (not normalized), making cross-coin comparison meaningless. This screener uses normalized ATR (ATR/price) and strategy-derived thresholds.

**What it does:** Fetch WEEX symbol list + 300 bars OHLCV per symbol, run `compute_signals_v383`, extract live signal state, display ranked table with filters.

**WEEX API (public, no auth):**
- All futures symbols: `GET https://api-contract.weex.com/capi/v2/market/contracts`
- OHLCV: `GET https://api-spot.weex.com/api/v2/market/candles?symbol=BTCUSDT_SPBL&period=5m&limit=300`
- All tickers: `GET https://api-spot.weex.com/api/v2/market/tickers`
- Rate limit: 500 req/10s; use 50 req/s (0.02s sleep)

**ATR ratio threshold derived from commission math:** `min_atr_ratio = (0.001 * 2) / 2.0 * 3 = 0.003`

**Screener columns:** atr_ratio, stoch_60, stoch_9, cloud3_dir, price_pos, signal_now, 24h_change_pct, 24h_vol_usd, vol_change_pct

**4 files to build:**
1. `utils/weex_fetcher.py` — API client with symbol format conversion (cmt_btcusdt ↔ BTCUSDT_SPBL)
2. `utils/weex_screener_engine.py` — `screen_symbol()` + `run_weex_screener()`
3. `scripts/weex_screener_v1.py` — Streamlit app with incremental per-symbol processing
4. `tests/test_weex_fetcher.py`

### Decisions recorded
- Reuse `compute_signals_v383` and `DEFAULT_SIGNAL_PARAMS` from existing screener_v1.py
- Minimum 69 bars for signal validity; default fetch 300 bars
- Autorefresh option (off/1m/5m/15m)
- No export needed (watch tool, not connector feed)

### State changes
- 4 new files planned (no existing files modified)
- Open question: WEEX taker rate for user's account tier (defaults to 0.10%)

### Open items recorded
- Verify futures OHLCV endpoint (spot candles vs separate contract candles)
- Verify WEEX taker rate at build time
- Verify WHITEWHALE and RIVER appear in results

### Notes
- This screener is for WEEX exchange, separate from the BingX connector. The existing `screener_v1.py` uses local Bybit parquets for backtested eligibility; this uses live WEEX API for live signal state.

---

## imperative-tumbling-bentley.md
**Date:** Not stated
**Type:** Planning — Analysis script

### What happened
Plan for a capital utilization analyzer script for v3.8.2 multi-coin backtests. User ran v3.8.2 on BERA (746 trades) and RIVER (881 trades) separately. Plan computes how much capital sits idle, how many coins could run in parallel on $10K account, and combined P&L with 50% commission rebate.

**Script:** `PROJECTS/four-pillars-backtester/scripts/capital_utilization.py`
**Inputs:** Two specific CSV files from Downloads folder

**Per-coin computations:**
- Build 5-min bar timeline, count open positions (0-4) per bar
- Max/avg concurrent, % time flat, % time at each level
- Margin deployed per bar = open_positions × $250
- Peak margin, average margin, idle margin ($10,000 - in-use)
- Average hold time in hours
- Gross P&L scaled to $5000 notional
- Commission: trades × $16/RT; Rebate: 50% of commission
- Net P&L = gross - commission + rebate

**Combined (BERA + RIVER):**
- Overlay timelines, combined margin per bar
- How many more coins could fit: `floor(idle_capital / max_margin_per_coin)`

**Output:** Formatted table with BERA / RIVER / COMBINED columns.

### Decisions recorded
- $5000 notional per position ($250 margin at 20x)
- Commission: $16/RT (round-trip)
- Rebate: 50%
- 1 file to create, no permissions needed beyond that

### State changes
- 1 new script planned

### Open items recorded
- User runs: `python scripts/capital_utilization.py`

### Notes
- $16/RT commission figure used here. MEMORY.md shows actual taker rate 0.0008 (0.08%); at $5000 notional: $5000 × 0.0016 = $8.00/RT for a 70% rebate account, $8.00 for 50% account. The $16/RT figure in this plan appears to be 0.16% × $10,000 (per notional at 2x the margin notional) or may use an older commission estimate. This should be noted as potentially inconsistent with MEMORY.md commission constants.

---

## jazzy-whistling-boot.md
**Date:** Not stated (in 06-CLAUDE-LOGS/plans directory, references events around 2026-03-05)
**Type:** Planning — Bug fix

### What happened
Plan to fix BingX error 109400 ("timestamp is invalid"). The bot and dashboard use raw `time.time() * 1000` with zero server time synchronization. BingX rejects requests where timestamp drifts >5 seconds from their server clock. This caused the user to lose 17% — when timestamps go invalid, position reconciliation, SL moves, TTP closes, and balance queries all fail silently.

**Two timestamp generation points identified:**
1. Bot: `bingx_auth.py` line 43 — `params["timestamp"] = str(int(time.time() * 1000))`
2. Dashboard: `bingx-live-dashboard-v1-4.py` line 193 — `params['timestamp'] = int(time.time() * 1000)`

**Fix: New `time_sync.py` module:**
- `TimeSync` class: fetches server time (`GET /openApi/swap/v2/server/time`), calculates offset with RTT midpoint compensation, thread-safe
- `now_ms()` → `int(time.time() * 1000) + offset`
- `start_periodic()` → daemon Timer, re-syncs every 30s
- `force_resync()` → immediate sync on 109400 error
- `get_time_sync(base_url)` → module-level singleton factory
- Supports both live and demo base URLs
- Falls back to raw `time.time()` if server endpoint unreachable

**Changes to 5 files:**
- `bingx_auth.py`: 3-line change to use `synced_timestamp_ms()`
- `main.py`: startup init + periodic sync + stop on shutdown
- `bingx-live-dashboard-v1-4.py`: init singleton, replace timestamp generation
- `position_monitor.py`: 109400 retry logic in `_fetch_positions()`
- `executor.py`: 109400 retry logic in `execute()` (retry once with fresh timestamp)

**Build script:** `scripts/build_time_sync.py` — 13 steps with backup, write, py_compile, summary.

### Decisions recorded
- Failure mode: if server time endpoint unreachable, offset stays 0 = same as current behavior, no regression
- `ws_listener.py`, `signal_engine.py`, `state_manager.py`, `risk_gate.py`, `data_fetcher.py`: no modifications needed

### State changes
- 1 new file: `time_sync.py`
- 5 files modified with `.bak` backups

### Open items recorded
- After build: restart bot and dashboard, verify `TimeSync: offset=+Xms` in logs, verify 30s periodic sync, verify 109400 errors stop
- `time_sync.py` already exists in repo (confirmed in git status as untracked `?? PROJECTS/bingx-connector/time_sync.py`) — plan was implemented

### Notes
- The `time_sync.py` file exists as an untracked file in the current git status, suggesting this plan was executed. The user reportedly lost 17% due to this timestamp issue.

---

## CODE VERIFICATION

### jazzy-whistling-boot.md
Referenced `time_sync.py` as key deliverable.
- Git status shows `?? PROJECTS/bingx-connector/time_sync.py` — file exists as untracked
- Plan references `scripts/build_time_sync.py` — git status shows `?? PROJECTS/bingx-connector/scripts/build_time_sync.py` — build script also exists

### elegant-weaving-sutherland.md
Referenced `scripts/build_native_trailing.py` as key deliverable.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_native_trailing.py` — exists

### fluffy-singing-mango.md
Referenced `ws_listener.py` as new file to create.
- Git status shows `M PROJECTS/bingx-connector/ws_listener.py` (modified) — file exists and has been modified since last commit, confirming the plan was implemented.

### foamy-soaring-snowflake.md
Referenced `scripts/build_dashboard_v1_5_patch_runtime.py` as new build script.
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_dashboard_v1_5_patch_runtime.py` — exists.

### eventual-tickling-stardust.md
Referenced `scripts/build_audit_fixes.py` for both four-pillars-backtester and bingx-connector.
- Git status shows `?? PROJECTS/four-pillars-backtester/scripts/build_audit_fixes.py` — exists
- Git status shows `?? PROJECTS/bingx-connector/scripts/build_audit_fixes.py` — exists
