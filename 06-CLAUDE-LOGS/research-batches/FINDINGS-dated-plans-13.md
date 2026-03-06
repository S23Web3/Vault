# Batch 13 Findings — Dated Plans (2026-02-25 to 2026-02-27)

**Files processed:** 20
**Batch date:** 2026-03-06

---

## 2026-02-25-bingx-step1-verify-coins.md
**Date:** 2026-02-25
**Type:** Planning

### What happened
Plan to build a standalone coin verification script (`scripts/verify_coins.py`) before restarting the BingX bot. Context: `config.yaml` had 16 coins from the 2026-02-12 sweep, but coins were selected from historical CSV data rather than verified against live BingX perpetual futures listings. Some meme coins (PIPPIN, GIGGLE, FOLKS, STBL, SKR, UB, Q, NAORIS, ELSA, etc.) were flagged as potentially unlisted or delisted. The script reuses the existing `executor.py` contracts fetch pattern (`GET /openApi/swap/v2/quote/contracts`).

### Decisions recorded
- Script does NOT auto-edit config.yaml — outputs clean list to stdout for manual review
- Uses live BingX endpoint (not VST demo) as source of truth for contract availability
- Pattern mirrors `scripts/test_connection.py` (standalone, single responsibility)
- No new test file — diagnostic utility only

### State changes
- Plan to create: `PROJECTS/bingx-connector/scripts/verify_coins.py` (~80 lines)
- Config manually updated after running script (user action)
- After script passes: `COUNTDOWN-TO-LIVE.md` step 3 marked done

### Open items recorded
- Run `python scripts/verify_coins.py` and review output
- If fails: copy clean list from stdout, paste into config.yaml
- Restart bot and verify warmup logs
- Wait for first signal (201 bars × 1m = ~3.4h warmup)

### Notes
None.

---

## 2026-02-26-bingx-5m-production-readiness.md
**Date:** 2026-02-26
**Type:** Session log / Planning

### What happened
Post-24h demo review of BingX bot on 1m timeframe. Bot ran for ~20.5 hours with zero crashes or exceptions, 105 trades opened and closed, daily P&L of -$354.27. 428 signals blocked by ATR filter ("Too Quiet"). ~90% of exits were EXIT_UNKNOWN (position monitor fell back to SL price estimate because BingX VST demo cleaned up conditional orders before the 60-second monitor check).

Three phases of work identified: Phase 1 (config + P0 bug fixes before restart), Phase 2 (reliability fixes for production), Phase 3 (observability improvements), Phase 4 (config tuning after 5m demo).

### Decisions recorded
- Switch timeframe to 5m (config.yaml line 4: "1m" -> "5m")
- Fix commission rate: `position_monitor.py` line 186: 0.001 -> 0.0008
- Fix EXIT_UNKNOWN: query BingX trade history for actual fill price
- Add daily reset on startup (compare session_start date to today)
- Add reconnection retry with exponential backoff (3 attempts, 1s/2s/4s + jitter)
- Add post-execution order validation (verify order_id != "unknown")
- Add graceful shutdown with threading.Event
- Warmup stays at 200 bars for safety (not reduced to 89)

### State changes
- Files to modify: config.yaml, position_monitor.py, data_fetcher.py, executor.py, main.py
- Commission rate overstating losses by ~25% (0.10% vs 0.08% per side)

### Open items recorded
- Run `python -m pytest tests/ -v` (67 tests must pass)
- Start bot on 5m, monitor first 30 minutes for warmup + first signal
- After first trade closes: verify exit_reason is no longer EXIT_UNKNOWN
- Verify Telegram alerts arrive with correct data

### Notes
1m performance as expected bad — consistent with backtester findings. 5m is the correct timeframe for production. Bot infrastructure confirmed solid (zero crashes over 20+ hours).

---

## 2026-02-26-bingx-bot-local-autostart.md
**Date:** 2026-02-26
**Type:** Planning

### What happened
Plan for local Windows auto-start with reboot persistence for the BingX bot. Context: VPS (Hostinger Jakarta) cannot reach BingX VST demo API (`open-api-vst.bingx.com` blocked from datacenter IPs); live API works fine on VPS via CloudFront CDN. Since demo mode needs to run first, bot runs locally. Three deliverables: PowerShell wrapper script (`run_bot.ps1`) with infinite restart loop, Windows Task Scheduler XML (`bingx-bot-task.xml`) for startup trigger, and install helper (`install_autostart.ps1`).

### Decisions recorded
- Wrapper: crash recovery + 30-second wait before restart
- Wrapper logs to `logs/YYYY-MM-DD-wrapper.log`
- Task Scheduler: triggers at system startup, runs with highest privileges, no stop on idle
- No changes to main.py, config.yaml, or any bot modules

### State changes
- Files to create:
  - `PROJECTS/bingx-connector/scripts/run_bot.ps1`
  - `PROJECTS/bingx-connector/scripts/bingx-bot-task.xml`
  - `PROJECTS/bingx-connector/scripts/install_autostart.ps1`

### Open items recorded
- User runs `install_autostart.ps1` from admin PowerShell
- User verifies "BingXBot" task exists in Task Scheduler GUI
- User tests by running `run_bot.ps1` manually
- User reboots to verify auto-start
- Kill test: kill python.exe from Task Manager, confirm wrapper restarts within 30s

### Notes
VPS cannot reach VST demo endpoint — confirmed blocker. Live API works from VPS but demo validation must happen locally.

---

## 2026-02-26-vault-organization-build.md
**Date:** 2026-02-26
**Type:** Build session (documentation/organization)

### What happened
Vault organization session addressing 5 areas of organizational debt: MEMORY.md exceeded 200-line limit (215 lines, truncated each session), 140+ session logs had no index, DASHBOARD-FILES.md was 9 days stale, PRODUCT-BACKLOG.md missing BingX/WEEX/Vince items, no single doc showing deployed systems. All pure documentation work.

Five steps completed:
1. MEMORY.md split from 215 lines to 84-line index + 7 topic files
2. `06-CLAUDE-LOGS/INDEX.md` created (140 markdown files indexed)
3. DASHBOARD-FILES.md updated (production corrected from v3.8.4 to v3.9.2)
4. PRODUCT-BACKLOG.md reconciled (5 new active items, 4 new completed items)
5. `LIVE-SYSTEM-STATUS.md` created with active systems table and pending deployments

### Decisions recorded
- MEMORY.md is a concise index only (under 200 lines)
- Detailed info lives in topic files in memory/ directory
- Topic files: TOPIC-vince-v2.md, TOPIC-backtester.md, TOPIC-dashboard.md, TOPIC-engine-and-capital.md, TOPIC-bingx-connector.md, TOPIC-yt-analyzer.md, TOPIC-critical-lessons.md

### State changes
- 9 new files created (7 topic files + INDEX.md + LIVE-SYSTEM-STATUS.md)
- 3 files modified (MEMORY.md reduced 215->84 lines, DASHBOARD-FILES.md corrected, PRODUCT-BACKLOG.md expanded)
- Dashboard production status corrected: was saying v3.8.4, now v3.9.2
- Backlog: P0.2 (BingX demo RUNNING), P0.3 (Dashboard v3.9.3 BLOCKED), P1.5 (WEEX Screener SCOPED), P1.6 (Strategy Scoping BLOCKED), P1.7 (Vince v2 plugin spec WAITING)

### Open items recorded
None stated in plan — all work marked complete.

### Notes
DASHBOARD-FILES.md had wrong production version (v3.8.4 instead of v3.9.2) for 9 days — corrected here.

---

## 2026-02-26-vault-vps-migration.md
**Date:** 2026-02-26
**Type:** Planning (step-by-step migration guide)

### What happened
Detailed migration guide for moving bot from local Windows PC to VPS (Jacky — 76.13.20.191, Ubuntu 24.04, 190GB free). Covers three parts: Part A (git setup on PC), Part B (VPS setup), Part C (ongoing workflow). Decisions: one flat git repo for entire vault (backtester .git removed), no cron, push from PC when work done, pull on VPS only when deploying, private repo `S23Web3/obsidian-vault`.

VPS architecture: bot runs on VPS (systemd, 24/7, auto-restart), ML/data stays on PC (RTX 3060 + 33GB data). Deploy command: `ssh root@76.13.20.191 "cd /root/vault && git pull && systemctl restart bingx-bot"`.

### Decisions recorded
- One flat repo for entire vault
- backtester's separate .git to be removed
- Private GitHub repo: S23Web3/obsidian-vault
- systemd service for bot on VPS (RestartSec=10, Restart=always)
- .gitignore excludes: 33GB data, .env, __pycache__, logs/, venv/, .pkl/.h5/.onnx, state.json/trades.csv

### State changes
- Plan creates one file: `C:\Users\User\Documents\Obsidian Vault\.gitignore`
- All other steps are manual commands (git, ssh)

### Open items recorded
- Part A: remove backtester .git, init vault repo, stage + commit, push to GitHub
- Part B: SSH to VPS, generate SSH key, clone vault, install Python 3.12 + venv, create .env, create systemd service
- Part C: ongoing push/deploy workflow

### Notes
VPS IP explicitly referenced: 76.13.20.191.

---

## 2026-02-26-vince-ml-scope-audit.md
**Date:** 2026-02-26
**Type:** Audit / Planning

### What happened
Comprehensive audit of Vince ML project status. Three distinct things called "Vince" identified: v1 (XGBoost/PyTorch classifier, BUILT but CONCEPTUALLY REJECTED), v2 (Trade Research Engine, CONCEPT WRITTEN but NOT APPROVED FOR BUILD), and existing reusable infrastructure (production backtester v3.8.4, signal pipeline, BBW pipeline, etc.).

Detailed side-by-side comparison of v1 vs v2: v1 asks "will this trade win or lose?" and reduces trade count (rejected because trade volume = rebate income); v2 asks "what patterns exist in my trades?" and never reduces trade count (approved direction). v2 uses frequency counting + permutation statistics, no trained ML model. v1 has 19 files, 2,643 lines, 37/37 tests — never deployed. v2 = concept doc only, zero code.

6 of 19 v1 modules identified as reusable in v2 (features_v3, triple_barrier, purged_cv, walk_forward, loser_analysis, coin_features). 7 modules NOT reusable (vince_model, training_pipeline, meta_label, bet_sizing, xgboost_trainer, staging files).

Document conflicts identified: `TOPIC-vince-v2.md` line 5 incorrectly says "APPROVED 2026-02-23" (wrong — concept not yet approved); `SPEC-C-VINCE-ML.md` describes v1 architecture; `BUILD-VINCE-ML.md` is 984-line v1 build spec.

### Decisions recorded
- Vince is NOT a classifier (confirmed as firm decision from 2026-02-18)
- Never reduce trade count (volume = rebate, confirmed 2026-02-18)
- Strategy-agnostic plugin architecture (confirmed 2026-02-20)
- Two-layer architecture (quant + LLM, confirmed 2026-02-20)
- Three operating modes (confirmed 2026-02-19)
- Tab 3 informational only (confirmed 2026-02-24)
- P1.7 (plugin interface spec) stays WAITING until concept approval

### State changes
- Identified: TOPIC-vince-v2.md has incorrect "APPROVED" status — needs correction
- Identified: SPEC-C-VINCE-ML.md should be marked SUPERSEDED
- Identified: BUILD-VINCE-ML.md should be marked ARCHIVED
- Identified: P1.2 "Deploy staging files" should be re-evaluated (staging files are v1 code)

### Open items recorded
1. Fix TOPIC file contradiction (correct "APPROVED" to "NOT YET APPROVED FOR BUILD")
2. User reads and approves concept v2 — single biggest blocker
3. Mark SPEC-C and BUILD-VINCE-ML as superseded/archived
4. Re-evaluate P1.2 backlog item
5. Formal plugin interface spec (P1.7) — first real build artifact
6. Scope trading LLM separately
7. Begin v2 build in order: plugin interface -> Enricher -> Analyzer -> Dashboard -> Optimizer -> Validator -> LLM

### Notes
This document explicitly flags that TOPIC-vince-v2.md line 5 is wrong ("APPROVED" is incorrect). The concept doc status was "NOT YET APPROVED FOR BUILD" at this date.

---

## 2026-02-26-vps-gitignore-deploy.md
**Date:** 2026-02-26
**Type:** Planning (build spec)

### What happened
Plan to build the vault-level `.gitignore` file needed for VPS migration. Bot confirmed production-ready (67/67 tests, 20.5h stable run, all fixes applied). Config already switched to 5m. Only missing piece: `.gitignore` file.

Two files to build: vault-level `.gitignore` (excludes ~33GB data + secrets + runtime artifacts) and updated bingx-connector `.gitignore` (add `logs/` and `venv/`). No code changes needed — all bot paths already cross-platform (uses `Path(__file__).resolve()`).

Timeline after VPS deploy: 0-16.7h = warmup (201 bars on 5m); 16.7h+ = signals fire; after 24h trading = run audit script to check exit reasons.

### Decisions recorded
- .gitignore excludes: data/ dirs (33GB), Books/, postgres/, .obsidian/, Tv.md, .env, __pycache__, venv/, logs/, *.pkl/*.h5/*.onnx, *.parquet, state.json/trades.csv, .DS_Store/Thumbs.db
- .gitignore keeps: all .md, .py, .yaml/.json, requirements.txt, existing sub-project .gitignore files
- No code changes to main.py or any bot module

### State changes
- Files to create/modify: vault `.gitignore` (new), bingx-connector `.gitignore` (update)

### Open items recorded
- User runs Part A (git setup), Part B (VPS setup), Part C (ongoing workflow)
- After 24h trading: run `python scripts/audit_bot.py` for real exit reasons

### Notes
Companion plan to 2026-02-26-vault-vps-migration.md — provides the specific .gitignore content that the migration guide referenced as "I will write this for you."

---

## 2026-02-27-automation-weex-screener-daily-report.md
**Date:** 2026-02-27
**Type:** Planning (build spec, 3 parallel agents)

### What happened
Plan for "proper automation" — closing the feedback loop. Three gaps identified: no live signal visibility across 100+ WEEX coins, no automated daily P&L Telegram report, vault stale after BingX docs scraper was built. Plan for 3 parallel build agents:

**Agent 1:** WEEX data layer (`weex_fetcher.py` + `weex_screener_engine.py`). Public WEEX API, no auth. Symbol format `BTC_USDT`. Endpoints: `/contract/klines`, `/contract/tickers`. Signal logic copied from backtester (NOT imported — no coupling to backtester path).

**Agent 2:** WEEX Screener UI (`weex_screener_v1.py`). Streamlit app with sidebar filters (min_atr_ratio, timeframe, signal filter, auto-refresh). Table with color-coded rows. Telegram alerts via existing `Notifier` class. Alert dedup by `alerted_this_session` set.

**Agent 3:** Daily P&L Report (`scripts/daily_report.py`). Reads trades.csv, filters to today, computes metrics, sends Telegram. Task Scheduler setup: daily at 17:00 UTC (21:00 local UTC+4).

### Decisions recorded
- Signal logic copied, not imported from backtester (no path coupling)
- All agents: docstrings mandatory, py_compile required, dual logging (file + console with timestamps)
- No escaped quotes in f-strings (use string concatenation for join())
- 3 agents run simultaneously — no cross-dependencies except Agent 2 using Agent 1's dict schema

### State changes
- Files to create: `screener/weex_fetcher.py`, `screener/weex_screener_engine.py`, `screener/weex_screener_v1.py`, `scripts/daily_report.py`
- Vault updates planned: LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, TOPIC-bingx-connector.md

### Open items recorded
- py_compile all 4 files
- Run `streamlit run weex_screener_v1.py` and verify table loads
- Manually trigger Telegram alert
- Run `python daily_report.py` and verify Telegram message

### Notes
This is the WEEX screener scoping session — prior backlog items listed it as P1.5 SCOPED.

---

## 2026-02-27-bingx-api-docs-scraper.md
**Date:** 2026-02-27
**Type:** Planning (build spec)

### What happened
Plan to scrape BingX API docs site (JS-rendered SPA using Element UI) into a single indexed markdown reference. The site has ~215 leaf endpoint pages across 8 sections. Playwright MCP tools available for browser automation. Existing manual reference covers only 11 endpoints. Output: `docs/BINGX-API-V3-COMPLETE-REFERENCE.md`.

Two files: `scripts/scrape_bingx_docs.py` (main scraper) and `scripts/test_scraper.py` (4 tests). Script architecture: `BingXDocsScraper` class (nav expansion, tree collection, per-page extraction) + `MarkdownCompiler` class (TOC generation, markdown formatting). Per-page extraction via `page.evaluate()` JavaScript. Resume capability via `.scrape-progress.json` every 20 pages.

### Decisions recorded
- Dependencies: playwright only (stdlib for everything else)
- CLI args: `--output`, `--section`, `--test` (3 pages), `--debug`, `--timeout`
- Intermediate save every 20 pages for crash recovery
- Log to `logs/YYYY-MM-DD-scraper.log` with dual handler

### State changes
- Plan to create: `scripts/scrape_bingx_docs.py`, `scripts/test_scraper.py`
- Output doc to create: `docs/BINGX-API-V3-COMPLETE-REFERENCE.md` (~215 endpoints)
- This replaces/supersedes `BINGX-API-V3-REFERENCE.md` (11 endpoints)

### Open items recorded
1. py_compile both .py files
2. Run tests
3. `python scripts/scrape_bingx_docs.py --test --debug` (3 pages first)
4. `--section Swap --debug` (single section ~69 endpoints)
5. Full scrape (all ~215 endpoints, 5-10 min)

### Notes
None.

---

## 2026-02-27-bingx-bot-live-improvements.md
**Date:** 2026-02-27
**Type:** Planning (execution plan / runbook)

### What happened
Execution plan for applying P0 correctness fixes and P1 WebSocket improvements to BingX connector before live money deployment. Three P0 bugs identified via BingX API scrape: FIX-1 (commission rate hardcoded at 0.0012, should be 0.0016 from API), FIX-2 (entry price using mark_price instead of avgPrice from order response), FIX-3 (no SL direction validation before order placement). One P1 improvement: WebSocket ORDER_TRADE_UPDATE listener (`ws_listener.py`) to eliminate EXIT_UNKNOWN.

Steps 0-11 defined. Uses Ollama (qwen2.5-coder) for code generation. Per file: read source -> build Ollama prompt -> generate to `*_new.py` -> strip fences -> py_compile -> diff -> backup + replace. Pytest runs at steps 4, 8, 11 (must show 67/67).

Source plan: `fluffy-singing-mango.md`.

### Decisions recorded
- py_compile mandatory after every generated file
- Backup before overwrite: `cp file.py file.py.bak`
- User's AFK delegation interpreted as full autonomy override for pytest execution
- Session log: `06-CLAUDE-LOGS/2026-02-27-bingx-bot-live-improvements.md`
- All actions logged with timestamps in format `[YYYY-MM-DD HH:MM:SS] STEP N — ACTION: description`

### State changes
- Files to modify: executor.py (FIX-2, FIX-3), position_monitor.py (FIX-1, WS queue), main.py (commission fetch, WS thread)
- Files to create: ws_listener.py (WebSocket listener), scripts/reconcile_pnl.py
- Files to modify: state_manager.py (cooldown + 101209 handler), risk_gate.py

### Open items recorded
- Steps 2-11 remain after steps 0-1 done
- All 67 tests must pass after each phase
- .bak files must exist for every modified file after completion

### Notes
Commission rate discrepancy: plan says FIX-1 is 0.0012 should be 0.0016 from API — this differs from the prior plan (2026-02-26) which said 0.001 should be 0.0008. The API scrape revealed the correct rate; the prior plan was based on spec doc, not API docs. Potential contradiction.

---

## 2026-02-27-bingx-runbook-step-scripts.md
**Date:** 2026-02-27
**Type:** Planning (build spec)

### What happened
Follow-on to the live improvements plan. Steps 0-1 already done (executor.py has FIX-2+FIX-3, backup exists). Plan to build one master script `scripts/run_steps.py` to execute steps 2-11 unattended. Script shows full permission summary upfront (all files to modify, create, backup), user types `y` once, then all steps run sequentially with Ollama streaming visible.

Phase 1: permission request. Phase 2: sequential execution (Ollama for code generation, pytest at steps 4/8/11). Phase 3: summary report.

### Decisions recorded
- Single master script approach (not separate step scripts)
- Script halts immediately on py_compile failure or pytest < 67 passing
- All actions logged to `06-CLAUDE-LOGS/2026-02-27-bingx-bot-live-improvements.md`

### State changes
- Files to modify (steps 2-11): position_monitor.py, main.py, state_manager.py, risk_gate.py, executor.py (101209 only)
- Files to create: ws_listener.py, scripts/reconcile_pnl.py
- Master script: `scripts/run_steps.py` (new)

### Open items recorded
- Run: `cd "C:\...\bingx-connector" && python scripts/run_steps.py`
- Verify all 67 tests pass at end
- Verify .bak files exist for all modified files

### Notes
Clarifies that steps 0-1 were already done before this plan was written.

---

## 2026-02-27-dash-vince-skill-creation.md
**Date:** 2026-02-27
**Type:** Planning (skill creation spec)

### What happened
Plan to create a comprehensive Plotly Dash skill file for Vince v2 dashboard development. Context: Vince v2 requires an 8-panel Dash application. The constellation query builder (Panel 3) needs pattern-matching callbacks (MATCH/ALL) — the most complex Dash pattern. Dash 4.0.0 (released 2026-02-03) and dash-ag-grid 33.3.3 confirmed as target versions.

Skill file: `C:\Users\User\.claude\skills\dash\SKILL.md`, ~900 lines, two parts: Part 1 (Architecture & Perspective — Dash vs Streamlit comparison, mental model, app structure decision, Vince Store Hierarchy) and Part 2 (Deep Technical Reference — app setup, component reference, callback fundamentals, pattern-matching callbacks, dcc.Store, background callbacks, Plotly figures, dash_ag_grid, ML model serving, PostgreSQL, network/production, performance, code review checklist).

### Decisions recorded
- Dash 4.0.0 as framework (not Streamlit)
- Mandatory Dash skill load rule to be added to CLAUDE.md
- Vince uses multi-page app (pages/ folder, register_page) — 8 panels = separate page files
- dcc.Store hierarchy: 5 stores defined (enriched-trades=session, active-filters=memory, date-range=memory, session-meta=session, optimizer-results=memory)
- Server-side storage for large datasets (diskcache, session_id in dcc.Store, not raw DataFrame)
- `@callback` from `dash` (Dash 4.0 pattern, not `app.callback`)
- DiskcacheLongCallbackManager for dev, CeleryLongCallbackManager for prod

### State changes
- Files to create: `C:\Users\User\.claude\skills\dash\SKILL.md` (new)
- Files to create: vault plan copy (this file)
- Files to modify: `CLAUDE.md` (append Dash skill mandatory rule)

### Open items recorded
- Open skill in editor, confirm ~900 lines
- Test skill load in new Claude session

### Notes
Documents known Dash 4.0.0 bugs: #3628 (InvalidCallbackReturnValue in background callbacks), #3594 (dcc.Loading stops spinner before background callback completes), #3616 (Dropdown performance regression).

---

## 2026-02-27-project-overview-diagram.md
**Date:** 2026-02-27
**Type:** Planning (documentation build spec)

### What happened
Plan to create a cross-project master overview diagram (`PROJECT-OVERVIEW.md`) showing all 4 active projects, their status, and inter-project connections. Context: vault has 27 UML/diagram files but all are intra-project — no cross-project view exists. This was a high-output day (2026-02-27) with 6 sessions across 3 projects.

Mermaid graph defined with 4 subgraphs: Infrastructure (PostgreSQL, Ollama, VPS Jacky), Four Pillars Backtester, Vince ML v2, BingX Connector v1.0, YT Transcript Analyzer v2. Inter-project arrows defined (e.g., YT ML findings -> Vince concept, Engine plugin -> Bot, Ollama -> YT GUI).

State of each project as of 2026-02-27: BingX screener and daily report built, API docs scraped, Vince concept locked and APPROVED FOR BUILD, YT Analyzer v2.1 built with UX overhaul, Dashboard v3.9.3 BLOCKED.

### Decisions recorded
- One new file: `PROJECT-OVERVIEW.md` in vault root
- No existing files modified

### State changes
- Files to create: `PROJECT-OVERVIEW.md`, vault plan copy
- `INDEX.md` to be appended

### Open items recorded
- Open in Obsidian and verify Mermaid renders
- Cross-check inter-project arrows against LIVE-SYSTEM-STATUS.md
- Cross-check blockers against PRODUCT-BACKLOG.md P0 section

### Notes
Vince concept status shown as "LOCKED 2026-02-27" and "APPROVED FOR BUILD" in the diagram — this contradicts the 2026-02-26-vince-ml-scope-audit.md which said concept was NOT YET APPROVED. The approval happened between the audit (2026-02-26) and this plan (2026-02-27). Confirms concept was approved on 2026-02-27.

---

## 2026-02-27-vault-update-and-next-step.md
**Date:** 2026-02-27
**Type:** Planning (vault maintenance + status summary)

### What happened
Vault update plan after BingX demo validation completion and YT Analyzer v2 build. BingX demo ran for 18h with 31 trades on 5m timeframe. VST API confirmed too corrupted for strategy comparison (vanishing order history, wrong-direction fills, mark price drift). Decision: stop optimizing demo, move to live phase. Five files to update: LIVE-SYSTEM-STATUS.md, PRODUCT-BACKLOG.md, TOPIC-bingx-connector.md, TOPIC-yt-analyzer.md, INDEX.md.

Project status summary: BingX Connector demo validated (awaiting live funds), API docs scraper built (needs one run), YT Analyzer v2 built, Dashboard v3.9.3 BLOCKED, Vince ML v2 concept approved (no build started), WEEX Screener scoped, BingX Live waiting on funds.

### Decisions recorded
- BingX demo analysis complete — VST API too unreliable for further optimization
- Move directly to live when funds transferred
- Next strategic step: Vince ML v2 plugin interface spec

### State changes
- LIVE-SYSTEM-STATUS.md: BingX Connector -> DEMO VALIDATED, add YT Analyzer row, add scraper row, remove stale week plan
- PRODUCT-BACKLOG.md: add YT Analyzer v2 and BingX demo analysis to Completed
- TOPIC-bingx-connector.md: add session summary (31 trades, -$379, 6 VST oddities)
- TOPIC-yt-analyzer.md: mark BUILT, add run command
- INDEX.md: append new log rows

### Open items recorded
- Run BingX API docs scraper (immediate)
- Vince ML v2 plugin interface spec (next session)

### Notes
Demo P&L stated as -$379 here vs -$354.27 in the 2026-02-26 plan — slight discrepancy, likely because the demo continued running between the two sessions.

---

## 2026-02-27-vince-b1-b10-build-plan.md
**Date:** 2026-02-27
**Type:** Planning (build roadmap)

### What happened
Formal build plan for Vince v2 as a unified Plotly Dash application, post-concept-approval. Vince is defined as the application itself — the dashboard serves Vince, not the other way around. The existing Streamlit dashboard (`scripts/dashboard_v392.py`, 2500 lines, 5 tabs) to be replaced by a Dash app.

8 panels defined with what each answers: Coin Scorecard (why does this coin keep losing?), PnL Reversal Analysis (PRIORITY — reversal anatomy), Constellation Query (when indicator X was in state Y, what happened?), Exit State Analysis (what moved before reversal?), Trade Browser (show individual trades), Settings Optimizer (what parameters work?), Validation (is the edge real?), Session History (what did I find last time?).

B1-B10 build order: FourPillarsPlugin -> API layer + types -> Enricher -> Panel 2 (PnL Reversal) -> Constellation Query Engine -> Dash app shell -> Panels 1/3/4/5 -> Mode 2 Auto-Discovery -> Mode 3 Settings Optimizer -> Panels 6/7/8.

Full file structure defined: `vince/` directory with `app.py`, `layout.py`, `api.py`, `types.py`, `enricher.py`, `query_engine.py`, `discovery.py`, `optimizer.py`, `pages/` (8 panel files), `assets/style.css`.

### Decisions recorded
- Framework: Plotly Dash (confirmed)
- Architecture: Vince IS the app — dashboard serves Vince
- Panel 2 (PnL Reversal) = highest priority build
- API layer (`vince/api.py`) = skeleton for both GUI and future agent
- Enricher storage: diskcache (session_id in dcc.Store, enriched trade set on disk — never raw DataFrame in browser)
- Future: RL Exit Policy overlay on Panel 2, LLM Interpretation (Panel 9), Agent

### State changes
- Concept status: APPROVED FOR BUILD (confirmed in this plan)
- Files to create: entire `vince/` directory structure

### Open items recorded
- B1 builds first: `strategies/four_pillars.py` (FourPillarsPlugin)
- Verification after B1-B6: `python vince/app.py` launches, Panel 2 shows MFE histogram

### Notes
Existing reusable code identified: base_v2.py (ABC), four_pillars_v383_v2.py (signals), backtester_v384.py, position_v384.py (Trade384 dataclass), commission.py, bbwp.py, ml/features.py, ml/walk_forward.py, research/bbw_monte_carlo.py.

---

## 2026-02-27-vince-concept-doc-update-and-plugin-spec.md
**Date:** 2026-02-27
**Type:** Planning (build spec — documentation + spec creation)

### What happened
Post-YT-analysis session plan. 202 videos analyzed (algo trading channel + FreeCodeCamp ML course) and 7 ML findings identified for Vince. This plan updates `VINCE-V2-CONCEPT-v2.md` with all 7 findings and begins P1.7 (formal plugin interface spec).

7 specific edits to concept doc defined: (1) add Panel 2 as highest-priority to "What Changed from v1", (2) expand Mode 2 Auto-Discovery with XGBoost feature importance pre-step + k-means clustering + held-out partition + reflexivity caution, (3) add new "RL Exit Policy Optimizer" section (full architecture), (4) update Mermaid flowchart with RL node, (5) label Panel 2 as "HIGHEST BUILD PRIORITY (v1)" in diagram, (6) add survivorship bias and reflexivity bullets to Constraints, (7) add RL optimizer as open question #7.

`VINCE-PLUGIN-INTERFACE-SPEC-v1.md` to be created: 7 sections covering purpose, ABC class definition, method contracts (compute_signals, parameter_space, trade_schema, run_backtest, strategy_document), OHLCV DataFrame contract, Enricher contract, Compliance Checklist, FourPillarsPlugin compliance mapping.

### Decisions recorded
- Concept doc status stays "NOT YET APPROVED FOR BUILD" (concept approval not part of this plan)
- P1.7 backlog status stays WAITING
- No Python code written in this session

### State changes
- Files to modify: `VINCE-V2-CONCEPT-v2.md` (7 edits)
- Files to create: `VINCE-PLUGIN-INTERFACE-SPEC-v1.md`, vault plan copy
- Files to modify: `memory/TOPIC-vince-v2.md` (update status + new files)

### Open items recorded
- After implementation: verify 7 additions present, status still says "NOT YET APPROVED"
- Verify plugin interface spec has all 7 sections

### Notes
This plan says concept doc status "NOT YET APPROVED" — but the build plan (2026-02-27-vince-b1-b10-build-plan.md) written the same day says "APPROVED FOR BUILD." This likely represents two sessions on the same day, with approval happening between them. The concept-doc-update plan may have been written before the concept was approved, and the lock-and-build-roadmap + b1-b10 plans were written after approval.

---

## 2026-02-27-vince-concept-lock-and-build-roadmap.md
**Date:** 2026-02-27
**Type:** Planning (pre-approval discussion)

### What happened
Pre-approval planning document for Vince v2. Concept doc has been in scoping since 2026-02-18. User requirements stated: proper GUI (advanced Dash/Streamlit, not throwaway), agent-ready skeleton (clean API layer), core focus (analysis engine + GUI first, agent + RL + LLM = later phases).

Two things needed to be added to concept doc before locking: GUI section (framework decision, layout, key UX) and architecture skeleton (API layer with clean Python functions for both GUI and future agent). Build order B1-B9 proposed: FourPillarsPlugin -> API layer -> Enricher -> Panel 2 -> Constellation Query -> Dash GUI (Panels 1-4) -> Mode 2 Auto-Discovery -> Mode 3 Optimizer -> Dash GUI (Panels 5-7).

Three decisions needed from user: Dash or Streamlit?, is concept correct?, is build order right?

### Decisions recorded
- Agent-ready API layer to be built now as skeleton
- Agent itself is future iteration
- Scope: core analysis engine + GUI first

### State changes
- This appears to be the planning session BEFORE concept approval
- GUI section and architecture skeleton to be added to concept doc
- Status to change from draft to "APPROVED FOR BUILD" after user confirmation

### Open items recorded
- User to confirm: Dash or Streamlit, concept correctness, build order
- After confirmation: add GUI + skeleton sections to concept doc, lock it, start B1

### Notes
This is likely the earliest plan in the 2026-02-27 Vince sequence. Build order here has B6 as "Dash GUI Panels 1-4" and B9 as "Dash GUI Panels 5-7" — slightly different numbering than the b1-b10 plan which has B6 as "Dash app shell" and B7 as "Panels 1/3/4/5." Minor restructuring between the two plans.

---

## 2026-02-27-yt-analyzer-v2-structured-output.md
**Date:** 2026-02-27
**Type:** Planning (build spec)

### What happened
Plan to transform YT Transcript Analyzer v1 output from raw text dump into structured, navigable output with clickable YouTube timestamp links, LLM-generated summaries, and auto-tags. Problems identified: timestamps discarded in cleaner.py, no clickable YouTube links, no LLM summaries, no tags, unstructured report, unpredictable output path (relative), unexplained 15/211 subtitle gap in GUI, no re-run without re-download capability.

6 files to modify: `config.py` (fix OUTPUT_PATH to absolute), `cleaner.py` (preserve timestamps as `[MM:SS]` markers, extract video_id, write metadata comment), `summarizer.py` (NEW — LLM summary + auto-tags via qwen3:8b), `reporter.py` (rewrite with TOC, summaries, tags, clickable YouTube timestamp links), `gui.py` (Summarize stage, download stats, output path display), `fetcher.py` (track subtitle success/skip counts).

YouTube timestamp URL format: `https://www.youtube.com/watch?v=VIDEO_ID&t=SECONDS`. Example format: `[05:23](https://www.youtube.com/watch?v=cTJ0Qbz0eAI&t=323)`.

Extensive test scenarios (T1-T6) and debug protocols (D1-D6) defined.

### Decisions recorded
- Timestamps as `[MM:SS]` text markers (human-readable AND machine-parseable, not separate metadata files)
- Summarizer is separate module (can be skipped in drain-fast mode)
- Video titles from existing `manifest_videos.json`
- YouTube links as standard markdown
- VTT filename regex: `^\d{8}-([a-zA-Z0-9_-]{11})-` (date + 11-char video ID)
- OUTPUT_PATH: `Path(__file__).parent / "output"` (project-relative, not CWD-relative)

### State changes
- Files to modify: config.py, cleaner.py, reporter.py, gui.py, fetcher.py
- Files to create: summarizer.py (new)

### Open items recorded
- py_compile all 6 modified files
- Run drain on small channel (5-10 videos) to verify timestamps, summaries, links
- Run query mode and verify timestamp links in findings
- Spot-check 3 random YouTube timestamp links for accuracy

### Notes
None.

---

## 2026-02-27-yt-analyzer-v21-ux-overhaul.md
**Date:** 2026-02-27
**Type:** Planning (build spec — UX overhaul)

### What happened
UX overhaul plan for YT Analyzer after first real run discovered 10 usability problems (211 videos, 201 transcripts, 50+ minute summarize stage). Problems: no cancel button, invisible progress (overwrites self), no output preview, no output folder control, channels mix into same output/, summarize too slow with no opt-out, no ETA, no resume awareness, no re-run without re-download, no download button.

Per-channel namespacing (problem 5) deferred — requires refactoring all `from config import X` to `import config; config.X`. All other 9 problems addressed in v2.1.

3 files to modify: `gui.py` (full rewrite), `fetcher.py` (add `on_process_started` callback), `summarizer.py` (extended callback + `_cached` tag).

### Decisions recorded
- Per-channel namespacing deferred (too much refactoring)
- All other 9 UX problems addressed in v2.1
- gui.py gets full rewrite (not incremental edit)

### State changes
- Files to modify: gui.py (full rewrite), fetcher.py, summarizer.py

### Open items recorded
None explicitly stated in this plan (it's a spec, implementation follows separately).

### Notes
This is a follow-on to the v2 structured output plan — written after the first real run of v2 revealed UX problems.

---

## 2026-02-27-yt-channel-ml-findings-for-vince.md
**Date:** 2026-02-27
**Type:** Research findings document

### What happened
Compiled ML findings from analyzing 202 YT transcripts (algo trading channel + FreeCodeCamp ML course). 14 numbered findings organized in 3 tiers. Tier 1 (directly applicable now, 4 findings): unsupervised clustering for Mode 2 auto-discovery, XGBoost feature importance to prioritize Mode 2 sweep, RL exit policy optimizer (main finding), random entry + ATR stops = exits matter more than entries. Tier 2 (applicable to specific components, 9 findings): walk-forward rolling windows, survivorship bias, reflexivity, held-out partition for Mode 2, GARCH volatility, LSTM stationarity warning, NLP sentiment, Bayesian NN, Transformer attention. Plus 6 general validated facts.

Key finding: RL for exit policy. Environment = trade lifecycle. Episode = one trade. State = [bars_since_entry, current_pnl_in_atr, k1-k4_now, cloud_state_now, bbw_now]. Action = HOLD or EXIT. Reward = pnl_at_exit minus commission. Train on enriched trade historical data, test on held-out period. RL exit learner does NOT change entry signals.

Stochastics + RSI consistently top-ranked across all ML feature importance studies — validates Four Pillars indicator choice.

### Decisions recorded
- RL Exit Policy Optimizer = new Vince component between Enricher and Dashboard
- Panel 2 (PnL Reversal Analysis) is highest build priority
- Mode 2 to include: clustering pre-step + XGBoost feature importance pre-step + held-out partition + reflexivity caution
- Survivorship bias caveat to be added to all pattern results

### State changes
- This is a findings document (read-only analysis output)
- 7 items to update in Vince v2 concept doc identified

### Open items recorded
- Update VINCE-V2-CONCEPT-v2.md with 7 findings (see companion plan 2026-02-27-vince-concept-doc-update-and-plugin-spec.md)

### Notes
RL finding: constraint satisfaction explicitly stated — RL does NOT reduce trade count (entries unchanged, only exits modified). Consistent with Vince's core non-negotiable. Video sources cited for each finding with YouTube video IDs.
