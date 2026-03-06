# Batch 20 Findings — Auto-Named Plan Files
**Files processed:** 20
**Date generated:** 2026-03-06

---

## rustling-churning-swing.md
**Date:** 2026-02-18
**Type:** Planning

### What happened
Plan for building a Vince Parameter Optimizer using Optuna (Bayesian optimization). Context explains the previous session mislabeled a trade filter/meta-labeling tool as "Vince." This plan corrects the scope: Vince is a rebate farmer that finds optimal parameter combinations to maximize trades and rebate income — NOT reduce trade count. The plan covers sweeping 26 parameters (16 signal + 10 backtester) across coins using the existing `compute_signals_v383()` + `Backtester384.run()` pipeline. Objective functions: `net_pnl_after_rebate` (default), `sharpe`, `risk_adjusted`. Supports walk-forward validation (expanding window, WFE rating), parameter importance analysis (fANOVA + SHAP), and multiple CLI flags.

### Decisions recorded
- Vince = Optuna parameter optimizer, NOT a trade filter
- Trade filtering/meta-labeling/bet sizing explicitly excluded
- Pruning: trials with < 10 trades pruned
- No dashboard integration (future scope)
- `pip install optuna` required before running
- 26 swept parameters with constraints enforced at sampling time

### State changes
Plan written. Files scoped:
- `scripts/build_optimize_vince.py` (build script)
- `ml/parameter_optimizer.py` (~400 lines)
- `scripts/optimize_vince.py` (CLI)
- `tests/test_parameter_optimizer.py`

### Open items recorded
- Build not yet executed (plan only)
- Dashboard integration deferred to future scope
- `sweep_all_coins_v2.py` not mentioned here (different context)

### Notes
This is a corrective plan explicitly addressing a prior session error where trade filtering was built instead of parameter optimization.

---

## serene-puzzling-squirrel.md
**Date:** Not explicitly stated in file (context references 2026-02-12 sweep)
**Type:** Planning

### What happened
Plan to verify all 16 coins in config.yaml are actively tradeable on BingX perpetual futures before restarting the bot. The backtester sweep ran on historical CSVs — some meme coins (PIPPIN, GIGGLE, FOLKS, STBL, SKR, UB, Q, NAORIS, ELSA) may not be listed. Solution: build a standalone `scripts/verify_coins.py` script that hits the public BingX contracts endpoint and checks each configured coin.

### Decisions recorded
- Script does NOT auto-edit config.yaml — outputs a clean list for user to review and apply manually
- Uses live BingX API (`https://open-api.bingx.com`), NOT VST
- Follows pattern of `scripts/test_connection.py`
- No test file needed — it's a utility script

### State changes
Plan created. One new file scoped:
- `scripts/verify_coins.py` (~80 lines)

### Open items recorded
- Bot restart pending until coins verified
- After successful run: mark COUNTDOWN-TO-LIVE.md step 3 done
- First signal expected 201 bars × 1m = ~3.4 hour warmup after restart

### Notes
None.

---

## shimmying-spinning-wozniak.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to fix 10 usability problems discovered during the first real run of the YT Transcript Analyzer (211 videos, 201 transcripts, 50+ min summarize stage). Problems include: no cancel, invisible progress (detail_text overwrites itself), no output preview, no output folder control, channels mix together, slow summarize with no opt-out, no ETA, no resume awareness, no re-run without re-download, and no download button.

Solution: major rewrite of `gui.py` plus changes to `fetcher.py`, `summarizer.py`, and `config.py`. Changes include: per-channel output directories, settings panel in sidebar, skip-summarize toggle, subprocess handle exposure for cancel, extended summarizer callback with result dict + `already_done` count, scrollable activity log container, clickable video list, ETA display, resume awareness, re-run without re-download checkbox, download button for report.

### Decisions recorded
- Per-channel dirs implemented via dynamic config globals override (simpler than refactoring all modules)
- Cancel via `proc.terminate()` in Streamlit `on_click` callback
- Skip-summarize forces the "no Ollama" code path
- Settings not persisted to `.env` — session-level only

### State changes
Files scoped for modification:
- `gui.py` (major rewrite)
- `fetcher.py` (on_process_started callback)
- `summarizer.py` (extended callback + already_done)
- `config.py` (get_channel_paths helper)

### Open items recorded
- Build not executed (plan only)
- 7 verification tests listed

### Notes
None.

---

## sleepy-plotting-bengio.md
**Date:** 2026-03-02
**Type:** Planning

### What happened
Plan for BingX Dashboard v1-3 Patches 6 and 7. Context: Patch 5 applied class-based dark CSS but Dash 2.x injects CSS variables into `:root` that override class rules — specifically `--Dash-Fill-Inverse-Strong: #fff` causes white backgrounds on date pickers and dropdowns. Class-level `!important` cannot override CSS variables; must override at `:root`.

Patch 6: CSS-only fix appending `:root` variable overrides to `assets/dashboard.css` with guard check and timestamped backup.
Patch 7: Bot status feed in Operational tab — adds `write_bot_status()` helper to `main.py` (atomic JSON write), `progress_callback` param to `data_fetcher.py` warmup, and 2 new callbacks + UI panel to `bingx-live-dashboard-v1-3.py`. Bot status polled every 5s from `bot-status.json`.

### Decisions recorded
- Atomic write: `tmp = status_path.with_suffix(".tmp")` → `os.replace(tmp, status_path)`
- Progress callback fires every 5 symbols (not every symbol)
- Status feed shows last 20 messages, newest first
- `dcc.Store(id='store-bot-status')` + `dcc.Interval(interval=5000)` pattern

### State changes
Two build scripts scoped:
- `scripts/build_dashboard_v1_3_patch6.py`
- `scripts/build_dashboard_v1_3_patch7.py`
Files modified: `assets/dashboard.css`, `bingx-live-dashboard-v1-3.py`, `main.py`, `data_fetcher.py`

### Open items recorded
- Build not executed (plan only)

### Notes
References session log `2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md`.

---

## snuggly-mixing-moon.md
**Date:** ~2026-03-02 (references "previous session built four_pillars_v386.py")
**Type:** Planning

### What happened
B1 plan: wrap Four Pillars backtester behind the Vince v2 `StrategyPlugin` ABC. The existing `strategies/four_pillars.py` is a v1 class that inherits from the wrong base and is missing 4 of 5 required methods. Plan: archive current v1, write new `FourPillarsPlugin(StrategyPlugin)` class. Build script creates archive, writes new class, runs 4 inline smoke tests. Key design: import alias `_compute_signals_fn` to avoid shadowing the class method. Param routing: pass ALL params to both signal pipeline and Backtester385 via `.get()` with defaults. Data path from `config.yaml → data.cache_dir`.

### Decisions recorded
- Strategy document property returns `Path` to `docs/FOUR-PILLARS-STRATEGY-v386.md`
- `run_backtest()` writes trades to `results/trades_b1_{timestamp}.csv`
- No Dash, PostgreSQL, Optuna, Enricher, RL/LLM, or pytest — all out of scope
- 4 smoke tests: syntax, interface, compute_signals, strategy_document

### State changes
Files scoped:
- `strategies/four_pillars.py` (archive → rewrite)
- `strategies/four_pillars_v1_archive.py` (new)
- `scripts/build_b1_plugin.py` (new)

### Open items recorded
- Post-build memory updates listed: session log, INDEX.md, PRODUCT-BACKLOG.md (B1 DONE, B2 READY), TOPIC-vince-v2.md

### Notes
Part of Vince v2 build series (B1-B6). B1 is prerequisite for Enricher, Optimizer, Dash shell.

---

## sparkling-doodling-hare.md
**Date:** 2026-03-05
**Type:** Planning (dual content: current plan + superseded earlier plan)

### What happened
Plan has two distinct sections:

**Current (top):** Add a "Load v384 Live Preset" button to `dashboard_v394.py` so it can be pre-configured to exactly match the live bot's signal logic. Two params missing from dashboard UI: `require_stage2` and `rot_level`. Plan: add new checkbox + slider, add preset button that sets all session_state keys. Build via `scripts/build_dashboard_v395.py` (reads v394, patches via safe_replace, writes v395). Also: scan yesterday's 11,466-line bot log for errors, create today's session log.

**Superseded (below "SUPERSEDED" marker):** Earlier plan for BingX Dashboard v1.4/v1.5 scope. Lists confirmed bugs (BUG-1 through BUG-9) with root causes. Contains 4 phases: Phase 1 (diagnostic scripts), Phase 2 (bot core fixes), Phase 3 (dashboard v1.5), Phase 4 (beta bot). This is a large plan covering TTP close fix, trade chart popup, beta bot at $5 20x, etc. Phase 1 scripts: run_error_audit.py, run_variable_web.py, run_ttp_audit.py, run_ticker_collector.py, run_demo_order_verify.py, run_trade_analysis.py.

### Decisions recorded
- `require_stage2` default=False (preserve existing behaviour), `rot_level` range 50-100 default 80
- v394 untouched, v395 is new file
- Beta bot: MUBARAK-USDT and SAHARA-USDT overlap with live bot — remove from beta
- 11 safe user beta coins confirmed

### State changes
Files scoped:
- `scripts/build_dashboard_v395.py` (CREATE)
- `scripts/dashboard_v395.py` (CREATE from build)
- Session logs to append/create

### Open items recorded
- Bot log scan pending
- Dashboard v395 build pending

### Notes
File contains superseded content from an earlier session merged into the same plan file. The superseded content represents the comprehensive v1.4/v1.5 + beta bot planning that was done in a prior session.

---

## sprightly-chasing-meteor.md
**Date:** 2026-02-25
**Type:** Planning / Audit

### What happened
Full audit of BingX connector beyond the 2026-02-24 fault report. Four areas:
1. New bugs (CRITICAL: C1-C4, HIGH: H1-H5, MEDIUM: M1-M5, LOW: L1-L2)
2. ccxt/bingx-python tips applied
3. Bot health/status visibility (status_writer.py + status.json schema)
4. Dashboard labeling (events.jsonl + enriched trades.csv + Telegram structured prefix)

Critical bugs: C1 — plugin config never passed to constructor (all config silently ignored); C2 — PnL direction wrong for SHORT; C3 — all closes assumed SL exits (exit price always sl_price); C4 — daemon threads die silently. New files: `status_writer.py`, `event_logger.py`, `rate_limiter.py`. Complete status.json schema documented (16 fields including threads, coins per-symbol, risk gates, positions). Structured Telegram prefix format `[MODE|STRATEGY|GRADE|EVENT_TYPE]`. New events.jsonl with 7 event types.

### Decisions recorded
- Implementation order: C1 first (highest value), then C2+C3 together, then H1, then Area 3, Area 4, Area 2, C4, H2-H5+M1-M5
- 67/67 tests must remain passing throughout all changes
- TIP-04 (WebSocket streaming) deferred

### State changes
3 new files + 8 modified files scoped. Plan document only — no build executed.

### Open items recorded
- All bugs remain open at time of plan creation
- Verification: tests must stay 67/67 throughout

### Notes
This is the comprehensive audit plan for the BingX connector post-demo-mode discovery phase.

---

## starry-hugging-elephant.md
**Date:** 2026-03-05
**Type:** Planning

### What happened
Plan for BingX Trade Analyzer v2. Context: bot has been running ~1 day (2026-03-04 17:52 to 2026-03-05 13:24+), 49 trades at $50 notional. The existing `run_trade_analysis.py` works but has issues: no column padding, terminal output too sparse, missing analysis dimensions, date filter hardcoded.

Build: one build script (`build_trade_analyzer_v2.py`) creates `run_trade_analysis_v2.py`. Analyzer v2 adds: CLI flags (--from/--to/--days/--no-api), 3 output formats (terminal, markdown, CSV), 10 analysis sections (summary stats, ASCII equity curve, symbol leaderboard, direction split, grade split, exit reason split, hold time, TTP performance, BE effectiveness, per-trade detail table). Fixed-width padded tables.

Critical build hazards documented: CSV schema mismatch (12-col header vs 18-col newer rows), f-string escape trap, division-by-zero guards, API failure handling.

### Decisions recorded
- `pd.read_csv(..., names=FULL_COLUMNS, header=0, on_bad_lines='warn')` for schema mismatch
- `--no-api` uses ttp_extreme_pct from CSV as MFE proxy
- 0.3s sleep between API calls
- Commission rate 0.0008 hardcoded in analyzer

### State changes
2 new files scoped:
- `scripts/build_trade_analyzer_v2.py`
- `scripts/run_trade_analysis_v2.py`

### Open items recorded
- 5 test scenarios listed
- Build not executed (plan only)

### Notes
None.

---

## synchronous-conjuring-shell.md
**Date:** Not explicitly stated (context: bot has had 8+ bugs, references E1-ROOT signature bug)
**Type:** Planning

### What happened
Plan for a BingX API Lifecycle Test Script — a 9-step sequential test that exercises the entire trade lifecycle against BingX VST in ~15 seconds. Motivation: each bug requires fix + restart + 30+ min wait for a real signal. The existing `test_connection.py` only tests read-only endpoints. Step 5 (place order with SL) is identified as the critical test that catches the E1-ROOT signature encoding bug where JSON special chars in stopLoss param are URL-encoded before signing.

9 steps: auth check, public endpoints, leverage+margin, quantity calc, place order with SL, verify position, close position, verify closed, fetch order details.

### Decisions recorded
- Imports `BingXAuth` directly, NOT `Executor` (avoids StateManager/Notifier coupling)
- Minimum viable quantity (~$0.02 notional) to conserve demo balance
- Logs to `logs/YYYY-MM-DD-lifecycle-test.log`
- On failure: prints full request URL + full response body
- Default coin: RIVER-USDT, override with `--coin`

### State changes
One new file scoped:
- `scripts/test_api_lifecycle.py`

### Open items recorded
- Build not executed (plan only)

### Notes
This plan explains the context for the lifecycle test that appears in subsequent session logs.

---

## synthetic-mapping-ember.md
**Date:** 2026-03-03
**Type:** Planning (session handover)

### What happened
CUDA Dashboard v394 session handover document. Notes that an earlier vault plan (`2026-03-03-cuda-sweep-engine.md`) had 4 pre-audit errors — this document contains the CORRECTED architecture. Key corrections: 12 signal arrays (not 10), param grid shape [N_combos, 4] (not 5), tp_mult sentinel is 999.0 (not 0.0), notional is a scalar kernel arg (not per-combo). The kernel uses Welford's online variance for Sharpe computation (no per-trade list in GPU memory), `cuda.local.array` for position state. v393 had IndentationError — base from v392 not v393. `sweep_all_coins_v2.py` deferred.

Engine architecture documented: CUDA kernel (one thread per param combo), CPU-compiled `jit_backtest.py` with Numba @njit, dashboard v394 with GPU Sweep mode + JIT portfolio path + sidebar GPU panel.

### Decisions recorded
- 12 signal arrays in kernel: close/high/low/atr, long_a/b/short_a/b, reentry_long/short, cloud3_ok_long/short
- Param grid: [sl_mult, tp_mult_or_999, be_trigger_atr, cooldown] — 2,112 combos default
- GPU thread model: one thread = one param combo
- Known kernel simplifications: fixed ATR SL only, no AVWAP, no scale-outs, no ADD entries
- Build only 3 files this session (not sweep_all_coins_v2.py)

### State changes
Files to be created by `scripts/build_cuda_engine.py`:
- `engine/cuda_sweep.py`
- `engine/jit_backtest.py`
- `scripts/dashboard_v394.py`

### Open items recorded
- Build script to be executed in new chat
- Post-build: update TOPIC-backtester.md, TOPIC-dashboard.md, LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md

### Notes
This document explicitly supersedes the earlier vault plan `2026-03-03-cuda-sweep-engine.md`.

---

## temporal-brewing-sky.md
**Date:** 2026-02-25
**Type:** Planning (multi-section: current + archived step plan + full pipeline scope)

### What happened
Three distinct sections in one file:

**Section 1 (Current):** Fix leverage Hedge mode bug in `main.py`. Bot running on BingX VST. `set_leverage_and_margin()` sends `side=BOTH` — BingX Hedge mode requires `side=LONG` and `side=SHORT` separately. Fix: replace single request with loop over ("LONG", "SHORT") per symbol.

**Section 2 (Archived — COMPLETE):** Step 1 Build Plan. Fix 1: `_round_down` test used assertEqual, should be assertAlmostEqual. Fix 2: test_integration.py missing price mock. Fix 3: config.yaml plugin switch from `mock_strategy` to `four_pillars_v384`. All 67 tests must pass.

**Section 3 (Full Pipeline Scope):** Scopes everything from coin discovery to live trades: Build 1 (BingX Screener with bingx_screener_fetcher.py, screener_engine.py, coin_ranker.py, live_screener_v1.py), Build 2 (main.py active_coins.json reader), Build 3 (config.yaml update), Build 4 (fix 2 failing tests). Also: Ollama scorer (qwen3:8b) for visual audit. Path to first demo trade = 1 session. Path to live with dynamic coins = 2-3 sessions.

### Decisions recorded
- Leverage fix: two requests per symbol (LONG + SHORT)
- main.py: active_coins.json takes priority over config.yaml coins on startup, no dynamic reload during runtime
- Ollama scorer fires on startup sweep and delta changes only, does NOT affect active_coins.json content
- Path to first demo trade: just fix 2 tests + edit config (no screener needed)

### State changes
This is a multi-session plan file. Step 1 is marked COMPLETE. Full pipeline is the ongoing scope.

### Open items recorded
- Leverage fix pending at time of writing
- Screener builds pending
- 67/67 tests needed before switching demo_mode: false

### Notes
This plan spans from the initial Step 1 completion state through the full live trading pipeline scope.

---

## temporal-nibbling-mist.md
**Date:** Not explicitly stated
**Type:** Planning

### What happened
Plan to add ML Analysis Tabs to the existing dashboard (`scripts/dashboard.py`, 526 lines). All ml/ modules are built and tested (8/8 pass). Current dashboard has no tabs — single view with test/single/batch modes. Plan: add `st.tabs()` with 5 tabs. Tab 1 (Overview): existing KPIs, equity curve, grade/exit breakdowns. Tab 2 (Trade Analysis): full trade table, P&L histogram. Tab 3 (MFE/MAE & Losers): MFE/MAE scatter + loser_analysis module. Tab 4 (ML Meta-Label): XGBoost meta-labeling, SHAP importance, bet sizing comparison. Tab 5 (Validation): purged CV, walk-forward validation. Sidebar: ML params (estimators, depth, threshold).

### Decisions recorded
- Delivered as a single Write to `scripts/dashboard.py` (no separate build script — single file edit)
- Test script: `scripts/test_dashboard_ml.py` (no Streamlit required)
- ML threshold slider inline controls what gets filtered in Tab 4

### State changes
One file modified, one test file created (plan only).

### Open items recorded
- Build not executed

### Notes
References an early version of the dashboard (526 lines) before the v38x/v39x numbering era.

---

## temporal-swinging-grove.md
**Date:** Not explicitly stated (context: lifecycle test steps 1-4 pass, step 5 failed due to E2-STOPPRICE bug)
**Type:** Planning

### What happened
Plan to install Playwright MCP, crawl and document the BingX v3 API docs (JS-rendered, unreadable by WebFetch), cross-reference API calls against documented specs, and complete the lifecycle test. Steps: install Playwright MCP (`claude mcp add playwright npx @playwright/mcp@latest`), crawl docs, save to `PROJECTS/bingx-connector/docs/BINGX-API-V3-REFERENCE.md`, fix build script (remove `str()` wrapper on sl_price/tp_price at lines 954 and 961), re-run lifecycle test, restart bot once 15/15 pass.

### Decisions recorded
- Fix is in `build_bingx_connector.py` lines 954/961 — remove `str()` wrapper
- Post-fix: restart bot once all 15 steps pass

### State changes
Files to be created/modified:
- `docs/BINGX-API-V3-REFERENCE.md` (create)
- `build_bingx_connector.py` (patch lines 954/961)

### Open items recorded
- Playwright MCP not yet installed at time of plan
- Steps 6-15 of lifecycle test not yet verified
- Session log to append: `2026-02-25-lifecycle-test-session.md`

### Notes
Context: the E2-STOPPRICE bug was found and fixed in executor.py but not yet re-tested. This plan bridges the debug session to re-verification.

---

## twinkly-popping-summit.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan to analyze all 196 closed trades from `trades.csv` in phase-segmented format before going live with a $110 account. Existing `audit_bot.py` treats all trades as a flat dataset — meaningless since 3 phases have very different notionals ($500/$1500/$50). Build new `scripts/analyze_trades.py` focused on phase-segmented trade performance analysis.

Phase detection: by notional_usd (500.0 = Phase 1, 1500.0 = Phase 2, 50.0 = Phase 3). Phase 1 (103 trades, 1m, broken exit tracking) flagged as UNRELIABLE. Phase 2 (47 trades, 5m, $1500) and Phase 3 (46 trades, 5m, $50) are the primary analysis targets. Report sections: dataset overview, Phase 1 flagged, Phase 2 deep dive, Phase 3 deep dive, combined signal quality, key findings (auto-generated plain English). Uses stdlib only (csv, datetime, pathlib, collections).

### Decisions recorded
- New script serves different purpose than `audit_bot.py` — both kept
- stdlib only, no pandas
- Phase detection by notional_usd value
- Phase 1 explicitly flagged UNRELIABLE in all outputs
- Report auto-generates "Is Grade A outperforming Grade B?" style findings

### State changes
One new file scoped:
- `scripts/analyze_trades.py`
Report output: `06-CLAUDE-LOGS/2026-02-28-bingx-trade-analysis.md`

### Open items recorded
- Build not executed (plan only)
- Verification: trade count must be 103+47+46=196

### Notes
None.

---

## twinkly-wibbling-puzzle.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to create a comprehensive Dash Super-Skill for Vince v2 dashboard development. Context: Vince v2 requires a Plotly Dash application (8-panel research dashboard replacing Streamlit). The constellation query builder (Panel 3) requires pattern-matching callbacks (MATCH/ALL) — the most complex Dash pattern.

Deliverables: new skill file `C:\Users\User\.claude\skills\dash\SKILL.md` (~900 lines), vault copy, CLAUDE.md update adding mandatory Dash skill load rule. Skill covers: multi-page app (register_page/pages folder), pattern-matching callbacks with full WRONG/CORRECT/TRAP callouts, dcc.Store hierarchy, background long-running callbacks (Enricher + Optimizer), dash_ag_grid, ML model serving, PostgreSQL connection pooling, production gunicorn config. Key traps documented: string/dict IDs cannot mix, dots in dict ID values cause parse errors, ALLSMALLER only valid when MATCH in Output, DataFrame cannot be stored directly in dcc.Store.

### Decisions recorded
- Dash version: 4.0.0 (released 2026-02-03)
- dash-ag-grid version: 33.3.3
- Vince MUST use multi-page (pages/ folder) — 8 panels = separate page files
- `@callback` decorator (not `app.callback`) in Dash 4.0
- `DiskcacheLongCallbackManager` for dev, `CeleryLongCallbackManager` for production
- Store pattern: store session_id in dcc.Store, look up enriched trades from diskcache by key

### State changes
Files to be created/modified:
- `C:\Users\User\.claude\skills\dash\SKILL.md` (CREATE)
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-dash-vince-skill-creation.md` (vault copy)
- `C:\Users\User\Documents\Obsidian Vault\CLAUDE.md` (EDIT — append Dash skill mandatory rule)

### Open items recorded
- Skill file build not yet executed
- CLAUDE.md update pending

### Notes
This plan is for the skill itself; CLAUDE.md now has the DASH SKILL MANDATORY rule as a result of this work.

---

## typed-wandering-tome.md
**Date:** Not explicitly stated (references v3.9.1, v3.9.2 era)
**Type:** Planning

### What happened
Dashboard v3.9.1 plan addressing two portfolio mode calculation errors. Root causes: (1) SL/TP/scale-out exits charge taker (0.08%) instead of maker (0.02%) — 4x overcharge; (2) Scale-out trades treated as separate positions — one position with 2 scale-outs creates 3 Trade384 records, capital model treats each as needing $500 margin = $1500 per position; (3) Double margin deduction; (4) Inconsistent baselines (N*10k vs pool balance vs deposit).

7 bugs documented (E1, C1-C2, D1-D7). Solution: direct engine fix (3 lines in backtester_v384.py, maker=True at lines 144/174/407), build script creating `capital_model_v2.py` (position grouping by entry_bar + exchange-model pool balance tracking), `dashboard_v391.py` (12 patches), `pdf_exporter_v2.py`.

Pool balance tracking: separate `balance` (realized cash) from `margin_used` (locked capital). Available = balance - margin_used. No double deduction.

### Decisions recorded
- Engine fix: direct Edit tool (not in build script)
- Position grouping key: `(coin, entry_bar)` collapses scale-out records
- Rebased equity: `rebased_chart_eq = adjusted_portfolio_eq - engine_baseline + total_capital`
- `scale_idx=0` hardcoded for SL/TP/END closes — grouping by entry_bar handles all cases

### State changes
Files:
- `engine/backtester_v384.py` (direct edit — 3 lines)
- `utils/capital_model_v2.py` (create via build script)
- `scripts/dashboard_v391.py` (create via build script from v39 base)
- `utils/pdf_exporter_v2.py` (create via build script)

### Open items recorded
- Build not executed (plan only)
- 5 verification scenarios listed

### Notes
This corrects the broken portfolio Mode 2 (Shared Pool) that showed Pool P&L = -$9,513 while per-coin sum = +$4,656.

---

## vast-enchanting-petal.md
**Date:** 2026-03-04
**Type:** Scoping / Strategy analysis

### What happened
Scoping document reviewing all Four Pillars strategy versions to understand why v386 is the correct baseline and what needs to change. Written after v391 build failed (built from spec without user confirming rules). Documents the "LSG problem" (85-92% of trades see green but exit at a loss) that every version since v3.5 tries to solve.

Version history table: v3.5.1 (cloud trail — bled out), v3.6 (AVWAP SL — bled out), v3.7 (rebate farming — barely viable), v3.7.1 (phantom trade fix), v3.8 (cloud 3 filter + ATR BE raise — best result: RIVER +$18,952), v3.8.3 (D-signal drag), v3.8.4 (optional per-coin ATR TP), v3.8.6 (stage 2 conviction filter, C disabled — LIVE).

ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 spec documented in detail (3-phase system + hard close). What v386 has vs what should exist: entry signals correct, Phase 1/2/3 NOT implemented, Cloud 2 hard close NOT implemented, Cloud 4 NOT computed.

Why v391 failed: built from spec without user confirming whether spec accurately represents their position management on charts. Spec may be incomplete relative to actual user behavior.

### Decisions recorded
- v386 entry signals: correct, keep as-is
- Initial SL: 2.0×ATR, TP: 4.0×ATR (per spec)
- Next build: user must confirm each phase rule before coding
- Existing v391 files (clouds_v391.py, four_pillars_v391.py, position_v391.py, backtester_v391.py, build_strategy_v391.py) exist and are syntactically clean but rules unverified

### State changes
Scoping document only — no code changes.

### Open items recorded
- 5 unverified spec details listed (Phase 1 anchor, Phase 2 amount, Phase 3 exit, hard close trigger, ADD midline threshold)
- Fundamental question: Does ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 accurately describe user's position management?

### Notes
Explicitly notes v391 was built without user rule confirmation — process problem, not code problem. This is the "cards on the table" clarification document before next build attempt.

---

## vast-skipping-crown.md
**Date:** 2026-02-25
**Type:** Planning

### What happened
Vault organization plan to address 5 areas of organizational debt: MEMORY.md at 215 lines (exceeds 200 hard limit, content being truncated), 24+ session logs with no index, DASHBOARD-FILES.md 9 days stale (shows v3.8.4 production when v3.9.2 is live), PRODUCT-BACKLOG.md missing BingX/WEEX/Vince items, and no single system status doc.

5 build steps: (1) MEMORY.md refactoring — split into index + 7 topic files (TOPIC-backtester.md, TOPIC-commission-rules.md, TOPIC-bbw-pipeline.md, TOPIC-bingx-connector.md, TOPIC-vince-v2.md, TOPIC-dashboard.md, TOPIC-critical-lessons.md); (2) Create INDEX.md for session logs; (3) Update DASHBOARD-FILES.md (v3.9.2 as production, v3.9.3 BLOCKED); (4) Reconcile PRODUCT-BACKLOG.md; (5) Create LIVE-SYSTEM-STATUS.md (new file, system status table).

### Decisions recorded
- TOPIC-commission-rules.md was planned but later merged into TOPIC-engine-and-capital.md (not visible in this document)
- LIVE-SYSTEM-STATUS.md to be created as a new file

### State changes
Plan for pure documentation work — zero code, zero risk. All write/edit operations on markdown files.

### Open items recorded
- Execution awaiting user approval at time of plan creation

### Notes
This is the genesis plan for the memory/topic file architecture now in use. Plan appears to have been executed (MEMORY.md topic files, INDEX.md, LIVE-SYSTEM-STATUS.md all exist in the vault).

---

## warm-waddling-wren.md
**Date:** 2026-02-07
**Type:** Master plan

### What happened
Four Pillars Trading System master execution plan (earliest strategic document in the set). 5 workstreams + 9 checkpoints. Context: v3.7.1 is marginally profitable at $1.81/trade expectancy. 86% of losers saw green — signal quality is fine, exit timing is bottleneck. Commission rebate changes math significantly: 70% account = $10.21/trade expectancy net of rebates.

WS1: Pine Script skill optimization (fix commission from $4→$6/side, add phantom trade bug, cooldown gate pattern). WS2: Progress review documents. WS3A: WEEX data pipeline (standalone fetcher, restartable, 1m candles). WS3B: Signal engine port from Pine to Python. WS3C: Backtest engine. WS3D: Additional exit strategies (cloud_trail, avwap_trail, phased). WS3E: Streamlit GUI extension. WS4: ML Parameter Optimizer (grid search → Optuna → PyTorch/XGBoost regime model). WS5: Stable v4 strategy + Monte Carlo validation.

CUDA setup instructions. WEEX API documented. Data size table (1 coin 24h → 500 coins 3 months). Breakeven+$2 raise identified as key optimization target.

### Decisions recorded
- Commission: raw $6/side (0.06%), NOT $4 — MEMORY.md was wrong and must be reverted
- Rebate settles daily at 5pm UTC
- Serial fetch per coin (not parallel) due to rate limits
- Target: 500 coins, 3 months, ~$450MB parquet cache
- Monte Carlo: 3 validation tests (trade reshuffling, parameter perturbation, trade skip)

### State changes
Master plan document only. Defines the entire project trajectory from early February 2026. Many of the builds scoped here have since been completed.

### Open items recorded
- At time of writing: all WS1-WS5 pending
- Since this is a historical master plan, most items are now complete

### Notes
This is the foundational master plan document. Commission figure confirmed as $6/side (later corrected to 0.08% taker but this captures the original planning context). The plan prompt at bottom is for use in new chat sessions to execute the plan.

---

## wise-juggling-dragonfly.md
**Date:** 2026-02-27
**Type:** Planning

### What happened
Plan to build two BingX automation tools using existing code patterns. Context: BingX demo validated. Bot trades but no feedback loop — can't see live signal state across 47 coins, performance review requires manual CSV reads.

Tool 1: `screener/bingx_screener.py` — headless loop fetching klines for all 47 coins every 60s, runs `FourPillarsV384.get_signal(df)`, fires Telegram on fresh A/B signals. Dedup via `last_alerted = {symbol: bar_ts}` dict. Uses live BingX API (public klines, no auth). Imports from both bingx-connector and four-pillars-backtester via sys.path inserts.

Tool 2: `scripts/daily_report.py` — reads trades.csv, filters to today's UTC date, computes P&L/win rate/best/worst, sends via Notifier. Configurable as Task Scheduler job at 21:00 local (17:00 UTC = rebate settlement time).

### Decisions recorded
- Live API (not VST) for klines — klines are public, no auth
- 60s poll interval (sufficient for 5m bars)
- Column rename required before plugin: `time → timestamp`, `volume → base_vol`
- Task Scheduler command included

### State changes
Two new files scoped:
- `screener/bingx_screener.py`
- `scripts/daily_report.py`

### Open items recorded
- Build not executed (plan only)
- WEEX screener stays in backlog

### Notes
Both tools use 2-parallel-agent delivery model per the plan header. Critical rules section references MEMORY.md hard rules (no escaped quotes in f-strings, dual logging, full paths).
