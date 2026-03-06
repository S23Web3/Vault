# Batch 14 Findings — Dated Plans (2026-02-28 to 2026-03-02)

---

## 2026-02-28-b2-api-types-research-audit.md
**Date:** 2026-02-28
**Type:** Planning / Research Audit

### What happened
Research audit of the B2 build block for Vince v2. B2 covers `vince/types.py` (all dataclasses) and `vince/api.py` (clean Python API functions, no Dash imports). The `vince/` directory did not yet exist at time of writing. The audit identified the existing files that B2 wraps (`strategies/base_v2.py`, `engine/position_v384.py`, `signals/four_pillars.py`, `engine/commission.py`, `data/db.py`) and precisely scoped B2 to 3 new files: `vince/__init__.py`, `vince/types.py`, `vince/api.py` (stubs only raising `NotImplementedError`). Seven API function signatures were drafted. Seven design bottlenecks were identified and documented as blockers requiring user decisions before coding could start.

### Decisions recorded
- B2 scope explicitly: `vince/__init__.py`, `vince/types.py`, `vince/api.py` — stubs only, no logic implementation
- B2 does NOT implement enricher, query, or optimizer logic
- Both Python skill and Dash skill are mandatory before writing any vince/ directory file
- `py_compile` required on all 3 files after creation
- api.py stubs must raise `NotImplementedError` (not silent `pass`)

### State changes
- No files created; this is a research/audit document only
- Identified 7 open design questions blocking build: (1) active plugin pattern (module-global vs per-call), (2) EnrichedTradeSet (dataclass list vs DataFrame), (3) ConstellationFilter (typed vs dict), (4) SessionRecord fields, (5) run_enricher corrected signature, (6) MFE bar definition, (7) what counts as a session

### Open items recorded
- All 7 design questions explicitly listed as blocking the build
- Corrected `run_enricher` signature proposed: `(trade_csv, symbols, start, end, plugin)` vs concept doc's incomplete `(symbols, params)`
- Bar index alignment noted as B1 problem but B2 must document requirement

### Notes
- This is a research-only document; the actual build plan for B2 came on 2026-03-02 after design verdicts were locked.

---

## 2026-02-28-b3-enricher-research-audit.md
**Date:** 2026-02-28
**Type:** Research Audit / Planning

### What happened
Full audit of the B3 Enricher build block for Vince v2. B3 takes a trade CSV from any `StrategyPlugin.run_backtest()` call, loads OHLCV + indicator data, looks up indicator state at three critical bars per trade (entry, MFE, exit), and attaches snapshot columns. `diskcache` is used for caching. The audit confirmed existing files (StrategyPlugin ABC, signal pipeline, Trade384, backtester, OHLCV parquet cache) and documented missing components (`vince/enricher.py`, `vince/cache_config.py`, `strategies/four_pillars_plugin.py`, `diskcache` package not installed). Six critical blockers were identified with detailed analysis.

### Decisions recorded
- B3 scope: modify `engine/position_v384.py` (add `mfe_bar`), create `strategies/four_pillars_plugin.py`, create `vince/__init__.py`, `vince/enricher.py`, `vince/cache_config.py`, plus tests
- `diskcache` must be installed before B3 can be built (`pip install diskcache`)
- Recommended cache: `FanoutCache` with 8 shards (for Optuna concurrency)
- Recommended OHLC storage: 4 separate columns (`entry_open`, `entry_high`, `entry_low`, `entry_close`) rather than tuples or JSON strings
- Column naming: rename in FourPillarsPlugin wrapper (option A — safest, no signal pipeline breakage)
- Cache directory: `data/vince_cache/` (separate from `data/cache/`)
- Cache key design: `f"{symbol}_{timeframe}_{params_hash}"`
- Enricher should be a context manager for clean Windows file handle management
- FanoutCache size limit: `size_limit=2 * 1024 ** 3` (2 GB cap)

### State changes
- No files created; research document only
- Six implementation improvements identified (Numba ATR sharing, raw stoch values in output, trade_schema mfe_bar/mae_atr fields, cache size cap, context manager pattern, compliance CLI)

### Open items recorded
- 8 open questions listed (Q1 through Q8)
- Q1 (mfe_bar tracking) explicitly called "the single most important decision before build starts"
- Q1 three options: (A) modify position_v384.py directly, (B) create position_v385.py, (C) Enricher second-pass over OHLCV
- Q7: which signal pipeline version (standard or Numba) — recommendation: standard first for correctness
- BLOCKER: `diskcache` not installed

### Notes
- The MFE bar question (Q1) is explicitly flagged as the critical dependency for Panel 4 (Exit State Analysis) and Panel 2 (PnL Reversal) functionality.

---

## 2026-02-28-bingx-be-fix-handover.md
**Date:** 2026-02-28
**Type:** Handover Prompt (for next session)

### What happened
A structured handover prompt designed to be pasted as the opening message of the next chat session. Focuses on the breakeven (BE) stop fix for the BingX live bot ($5 margin, 10x = $50 notional). Previous session had confirmed TTP (Approach C) was implemented. This session was scoped to BE fix only. The document provided the problem statement (stop placed at wrong price — raw entry_price instead of entry + commission RT), math verification (`True BE for LONG = entry × 1.0024`), the dollar impact ($0.08-$0.13 per trade on $50 notional), investigation steps (read position_monitor.py, check current BE stop price formula, review live logs, review trades.csv), and four approaches to fix (A: fix stop price only; B: add slippage buffer; C: change to STOP_LIMIT; D: replace with TAKE_PROFIT_MARKET).

### Decisions recorded
- Scope strictly limited to: `_place_be_sl()`, `check_breakeven()`, `BE_TRIGGER` constant
- Out of scope: SL logic, trailing TP, new entries, risk gate
- Fix must be proportionate to trade size ($0.08-$0.13 error on $50 notional)
- User was to be AFK — thorough autonomous investigation required
- py_compile must pass on all changed files
- Session log target: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-be-fix.md`

### State changes
- No code written; this is a session handover prompt document only

### Open items recorded
- Investigation steps 1-8 listed (read position_monitor.py, verify math, check BE_TRIGGER, check order type, read trades.csv, read live logs, read TOPIC file, read TTP session log)
- Deliverable format specified: implementation table, true BE math, approaches list, comparison table, recommended approach with implementation

### Notes
- The document correctly calculates true BE exit for LONG: `entry × (1 + 0.0016) / (1 - 0.0008) ≈ entry × 1.0024`, not simply `entry_price`.

---

## 2026-02-28-bingx-dashboard-design.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Design plan for the BingX live trading dashboard. Marked as a correction from a previous session that "built read-only twice" despite the user saying "position management." This plan explicitly states the dashboard is interactive (not read-only). Data sources: `state.json`, `trades.csv`, `config.yaml`, and optional BingX mark price API. Layout designed as a single Dash page with 5 sections: Bot Status Banner, Summary Cards (4 cards), Open Positions AG Grid (with management actions: Raise BE, Move SL), Today's Performance stats row, Closed Trades table. Technical decisions: Plotly Dash, port 8051, 60s refresh, direct JSON read, optional mark price API, `dash_ag_grid`. Single output file: `bingx-connector/dashboard.py`.

### Decisions recorded
- Dashboard IS interactive — "position management" means interactive controls (Raise BE, Move SL)
- Port 8051 (8050 reserved for Vince)
- Refresh interval: 60s (matches bot's position_check_sec)
- Dashboard reads files directly (not through StateManager) — read-only on data access but interactive on API calls
- Mark prices: optional BingX REST call via bingx_auth.py, graceful skip if no .env keys
- Future interactive features (manual close, SL adjust) deferred as separate build

### State changes
- No files created; design document only
- This supersedes/corrects the previous read-only dashboard design approach

### Open items recorded
- Mark price fetch toggle desired
- Note: "position management without interactivity = read-only" explicitly rejected by this plan

### Notes
- This plan references a rule violation from the prior session (MEMORY.md entry: user said "position management" — built read-only twice). This plan re-scopes correctly.

---

## 2026-02-28-bingx-dashboard-v1-1-build-spec.md
**Date:** 2026-02-28
**Type:** Build Spec (very large — 83.8KB)

### What happened
Complete, self-contained build specification for BingX Live Dashboard v1-1. A full Plotly Dash 4.0 app replacing the prior Streamlit-based `bingx-live-dashboard-v1.py`. Specification covers: output files (`bingx-live-dashboard-v1-1.py`, `assets/dashboard.css`), dependencies (dash, dash-ag-grid 33.3.3, plotly, pandas, pyyaml, requests, python-dotenv), run commands (local + gunicorn VPS), data sources (state.json, trades.csv, config.yaml, .env), architecture (single-file, 5 tabs, `dcc.Tabs`, `dcc.Store` pattern, `dcc.Interval` 60s), color constants, BingX API client (signed requests, `_sign()`, `_bingx_request()`), and a complete inventory of all functions and callbacks (Groups A-D: data loaders, data builders, chart builders, layout helpers; CB-1 through CB-14+). Key interactive features: CB-6 (Raise to Breakeven — cancel SL + place new STOP_MARKET at entry_price), CB-7 (Move SL — user-specified price), CB-12 (Save Config — atomic YAML write with diff report), CB-13/CB-14 (Halt/Resume bot via halt_flag in state.json). The spec also covers AG-Grid column definitions for positions, history, and coins views.

### Decisions recorded
- `suppress_callback_exceptions=True` — tab IDs don't exist at startup (dynamic content from CB-5)
- `prevent_initial_call=False` for CB-1 (data loader) and CB-2 (tab renderer)
- `prevent_initial_call=True` for all other callbacks
- CB-6 and CB-7 can both output to `pos-action-status` because they have different Inputs
- `server = app.server` required at module level for gunicorn
- `fetch_all_mark_prices` uses `ThreadPoolExecutor(max_workers=8)`
- API signing: replicated `_sign()` pattern (not imported from bot internals)
- Every callback wrapped in try/except; PreventUpdate re-raised before outer except
- Every def has one-line docstring
- Atomic writes via tmp + `os.replace()`
- Dual logging: file + StreamHandler, `TimedRotatingFileHandler`
- config.yaml validation rules defined (sl_atr_mult 0-10, leverage 1-125, etc.)

### State changes
- Specification document only; no files created from this spec yet at plan-writing time
- This spec was consumed by the build session that produced `bingx-live-dashboard-v1-1.py`

### Open items recorded
- VPS deployment: need `dash_auth.BasicAuth` before production (controls real money)
- Mark price API rate limit consideration noted

### Notes
- Code verification: `bingx-live-dashboard-v1-1.py` EXISTS on disk at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-1.py` — confirms the build was executed.

---

## 2026-02-28-bingx-dashboard-v1-1-build.md
**Date:** 2026-02-28
**Type:** Build Plan

### What happened
Execution plan for building the v1-1 dashboard based on the spec in `C:\Users\User\.claude\plans\goofy-dancing-summit.md` (1795 lines). Previous session hit context limit before writing code. This plan specifies building 3 files: `bingx-live-dashboard-v1-1.py` (~700 lines), `assets/dashboard.css` (~20 lines), `scripts/test_dashboard.py` (~170 lines). Build steps listed: load Dash skill, write main dashboard, write CSS, write test script, py_compile on both .py files, give run command.

### Decisions recorded
- Dash skill must be loaded before any code is written
- `suppress_callback_exceptions=True` confirmed
- `prevent_initial_call=False` for CB-1 and CB-2 only
- Every callback wrapped in try/except
- Dual logging with `TimedRotatingFileHandler`
- Existing v1 (Streamlit): `bingx-live-dashboard-v1.py` — DO NOT TOUCH
- User runs everything; never execute on their behalf

### State changes
- Build execution plan only; confirms 3 files are to be created
- References spec stored in system plan path: `C:\Users\User\.claude\plans\goofy-dancing-summit.md`

### Open items recorded
- py_compile must pass before delivery
- User run commands specified for test and launch

### Notes
- Code verification: `bingx-live-dashboard-v1-1.py` EXISTS on disk — confirms build was executed successfully.

---

## 2026-02-28-bingx-dashboard-v1-2-build.md
**Date:** 2026-02-28
**Type:** Build Plan

### What happened
Build plan for dashboard v1-2, addressing 8 issues found during live testing of v1-1. Issues: white form inputs, white ag-grid background, no date range picker, slow tab switching, no timing diagnostics, amateur analytics metrics, missing plotly toolbar cleanup. Plan specifies one build script (`scripts/build_dashboard_v1_2.py`) producing 3 files: overwritten `assets/dashboard.css` (28 → ~95 lines), new `bingx-live-dashboard-v1-2.py` (~1750 lines), overwritten `scripts/test_dashboard.py`. Delta table maps each section of v1-1 to v1-2 changes. Key changes: FIX-4 replaces dynamic tab rendering with all-tabs-in-layout + clientside visibility toggle (eliminates tab switch re-render); FIX-3 adds date range pickers; ANALYTICS-1 expands from 7 to 13 metric cards. Gotchas documented: `suppress_callback_exceptions` must stay `True`, `gross_pnl` alias kept for grade comparison, string formatting uses `.format()` not f-strings in build script to avoid escaped quote rule.

### Decisions recorded
- FIX-4: all tabs rendered in layout, visibility toggled via clientside callback (Option A chosen over B and C)
- FIX-3: `dcc.DatePickerRange` replaces "Today only" checkbox in History; added to Analytics
- ANALYTICS-1: 13 metric cards including Sharpe, MaxDD%, BE Hit, LSG% (last two = "N/A" until bot tracks data)
- `hist-today-filter` Checklist component REMOVED — only CB-8 references it
- `math.sqrt(365)` for Sharpe annualization requires `import math`
- LSG% and BE Hit Count deferred — require `be_raised` and MFE written to trades.csv (bot change, not dashboard scope)
- Build script uses `.format()` not f-strings to avoid escaped quote MEMORY rule

### State changes
- Plan document; build script and output files created in the session
- `bingx-live-dashboard-v1-2.py` created — confirmed exists on disk

### Open items recorded
- LSG% deferred: needs MFE tracking in position_monitor.py
- BE Hit Count deferred: needs `be_raised` written to trades.csv on close

### Notes
- Code verification: `bingx-live-dashboard-v1-2.py` EXISTS on disk — confirms execution.

---

## 2026-02-28-bingx-dashboard-v1-2-improvements.md
**Date:** 2026-02-28
**Type:** Audit / Issue Log

### What happened
Source document for the v1-2 build plan — captures the 8 user-reported issues from v1-1 live testing with root cause analysis, fix options, and severity ratings. Same content as v1-2-build.md but structured as a requirements/issue document rather than a build plan. FIX-3 root cause: tab content recreation on each switch destroys child callback outputs. FIX-4 root cause: CB-2 renders_tab recreates entire tab layout on each switch. Analytics blocker: `be_raised` in state.json per open position but NOT written to trades.csv on close; LSG needs MFE tracking not yet implemented.

### Decisions recorded
- FIX-4 Option A selected: render all tabs, toggle visibility (immediate, no reload flash)
- LSG and BE data explicitly marked as BLOCKER — requires bot changes before dashboard can show real values
- Analytics cards: expand from 7 to 13
- Charts: add `config={'displayModeBar': False}` to all `dcc.Graph` components

### State changes
- Requirements document only; execution done via v1-2-build.md plan

### Open items recorded
- LSG%: requires MFE tracking in position_monitor.py
- BE Hit Count: requires `be_raised` written to trades.csv on close
- Both blocked on bot changes, not dashboard changes

### Notes
- Duplicates some content from v1-2-build.md but provides more detailed root cause analysis.

---

## 2026-02-28-bingx-dashboard-vince-b1-b6.md
**Date:** 2026-02-28
**Type:** Session Build Plan (daily)

### What happened
Master daily build plan for 2026-02-28 covering two tracks: (1) BingX live trades dashboard and (2) Vince B1 through B6. Token conservation rules stated: build every file directly, no agents, process order (dashboard first then B1→B2→B3→B4→B5→B6), user verifies after each block. Ollama (qwen3:8b) designated for boilerplate-only files (vince/types.py, __init__.py files, CSS). The plan defined data schemas for state.json and trades.csv, panel layouts for the BingX dashboard (6 panels: summary cards, open positions, closed trades, exit breakdown, grade analysis, cumulative PnL), and scopes for each Vince block (B1=FourPillarsPlugin, B2=API types, B3=Enricher, B4=PnL Reversal, B5=Constellation Query, B6=Dash shell). Files explicitly marked as NOT to be modified: `strategies/base_v2.py`, `signals/four_pillars_v383_v2.py`, `engine/backtester_v384.py`, `PROJECTS/bingx-connector/main.py`.

### Decisions recorded
- Build order: dashboard first, then B1→B2→B3→B4→B5→B6
- Ollama to handle boilerplate files (zero Claude tokens)
- B2 `vince/types.py`: Ollama. `vince/api.py`: Claude
- B6 `vince/__init__.py`, `vince/pages/__init__.py`, `vince/assets/style.css`: Ollama. `vince/layout.py`, `vince/app.py`: Claude
- LSG% note: "Bot does not store MFE — LSG lives in Vince Panel 2, not here" (for BingX dashboard)
- NEVER TOUCH specified files list

### State changes
- Daily plan document; this session executed blocks across both tracks

### Open items recorded
- End state: BingX dashboard running at localhost + `python vince/app.py` launches with sidebar and all panel routes + Panel 2 (PnL Reversal/LSG) functional

### Notes
- This is the overarching session plan; individual block plans are in separate files. The Ollama delegation for boilerplate is a recurring token-saving strategy.

---

## 2026-02-28-bingx-friend-handover-package.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan for creating a BingX futures trading bot knowledge handover package for a friend. Output: `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md` (~400 lines) plus the existing `BINGX-API-V3-COMPLETE-REFERENCE.md` (224 endpoints). The handover document structure covers: authentication (HMAC-SHA256, THE #1 BUG = URL encoding before hashing), 11 critical gotchas (signature URL encoding, commission rate, fill price, recvWindow, leverage API hedge mode, listenKey POST vs GET, listenKey response format variants, WebSocket gzip compression, WebSocket heartbeat, VST geoblocking, order history purge), key endpoints curated from 224 (14 endpoints listed), order placement pattern, WebSocket user data stream setup, bot architecture patterns (dual-thread design), risk gate (8 pre-trade checks), exit detection strategy, state machine & recovery, deployment checklist.

### Decisions recorded
- Two-file package: handover guide + raw API reference
- 11 gotchas to include, ordered by severity
- 14 key endpoints curated (not all 224)
- Sources: executor.py, ws_listener.py, position_monitor.py, state_manager.py, risk_gate.py, main.py, API reference doc, TRADE-UML, audit-report.md, session logs

### State changes
- Plan document only; handover file to be created at `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md`

### Open items recorded
- Verification steps: all 11 gotchas present, correct auth code snippet, all 14 endpoints in table, deployment checklist present

### Notes
- The #1 bug (URL encoding before HMAC signing) is called out as critical — "every order fails without this."

---

## 2026-02-28-bingx-trade-analysis.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan for a trade analysis script covering 196 closed trades from trades.csv across 3 phases with different notionals ($500, $1500, $50). Existing `scripts/audit_bot.py` treats all trades flat — meaningless because notionals differ. Plan: new `scripts/analyze_trades.py` for phase-segmented analysis. Phase detection by notional_usd. Phase 1 (103 trades, $500 notional, 1m, Feb 25-26): flagged as UNRELIABLE — all EXIT_UNKNOWN/SL_HIT_ASSUMED. Phase 2 (47 trades, $1500, 5m, Feb 26-27): primary signal quality data. Phase 3 (46 trades, $50, 5m, Feb 27-28): live account data. Report sections: dataset overview, Phase 1 flagged unreliable, Phase 2 deep dive (grade/direction/exit breakdown/symbol leaderboard/hold time), Phase 3 deep dive (same + % of notional), combined signal quality (Phase 2+3), key findings (auto-generated). Stdlib only (csv, datetime, pathlib, collections — no pandas). Output: markdown file + console + dated log file.

### Decisions recorded
- New script `analyze_trades.py` (not modifying existing `audit_bot.py` — separate purposes)
- Stdlib only, no pandas dependency
- Phase 1 shown but explicitly marked UNRELIABLE
- Phase detection: notional_usd == 500/1500/50

### State changes
- Plan document; script to be created at `PROJECTS/bingx-connector/scripts/analyze_trades.py`

### Open items recorded
- Verification: py_compile pass + all 6 sections present + 103+47+46=196 trades + Phase 1 flagged

### Notes
- Code verification: `PROJECTS/bingx-connector/scripts/analyze_trades.py` EXISTS on disk — confirms execution.

---

## 2026-02-28-bingx-ttp-research-and-comparison.md
**Date:** 2026-02-28
**Type:** Research / Strategy Analysis

### What happened
Full trailing take profit (TTP) research for the BingX live bot. Context: 0 TP_HIT exits in 47 live trades (46 SL_HIT, 1 EXIT_UNKNOWN) because `tp_atr_mult: null` was set for live trading but no trailing TP replacement was built. BE raise is working but is only a floor, not a profit-locker. The document catalogued 6 TTP examples (E1 Fixed ATR, E2 ATR Trailing HTF, E3 AVWAP 3-stage, E4 AVWAP 2σ + 10-candle counter, E5 BingX Native Immediate, E6 BingX Native with Activation), documented current implementation state (Fixed TP removed, BE raise built, everything else not built), coded each approach with complexity/pros/cons, and produced a full comparison table across 5 approaches (A through E).

### Decisions recorded
- Phased recommendation: immediate = Approach C (TRAILING_STOP_MARKET with activation at 2×ATR profit, 2% callback), later = Approach D (AVWAP 2σ trigger)
- Approach A (fixed TP) rejected: only 8.5% TP hit rate in demo 5m
- Approach B (immediate trailing) rejected: activates on noise, 2% callback from tiny 0.5% peak
- Approach D deferred: 150 lines + AVWAP per bar = highest live risk for now
- Approach E (ratchet) noted as complementary to C, not primary
- Files to modify for Approach C: `executor.py`, `config.yaml` (add `trailing_activation_atr_mult: 2.0`, `trailing_rate: 0.02`), `tests/test_executor.py`

### State changes
- Research document; implementation planned for Approach C
- Session log to be created at: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-bingx-ttp-research.md`

### Open items recorded
- Verification: py_compile on executor.py, pytest test_executor.py, watch bot log for `TRAILING_STOP_MARKET placed`, confirm in BingX open orders UI, watch for fill in trades.csv

### Notes
- The 10-candle AVWAP design (E4) is confirmed as user's intended design from prior TOPIC file entry.

---

## 2026-02-28-dash-skill-trading-dashboard-enrichment.md
**Date:** 2026-02-28
**Type:** Planning (skill update)

### What happened
Plan to add trading-dashboard-specific knowledge to the Dash skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`). At time of plan creation, the skill was 1,064 lines covering architecture, callbacks, multi-page structure, Vince store hierarchy, components, ag-grid, ML serving, PostgreSQL, gunicorn, performance. Ten gaps identified (candlestick, real-time patterns, panel taxonomy, equity/drawdown, relayoutData sync, ag-grid conditional formatting, timezone handling, order book, rolling metrics, alert patterns). New section "PART 3 — TRADING DASHBOARD KNOWLEDGE" to be appended with 8 subsections (candlestick charts, panel taxonomy, real-time patterns, equity/drawdown, multi-chart sync, ag-grid conditional formatting, timezone-aware data, order book). Version bump to v1.1.

### Decisions recorded
- Knowledge-dense, concise — no large code walls
- Part 3 appended after Part 2, before Version History
- Frontmatter description keywords added: candlestick, equity curve, drawdown, real-time, dcc.Interval, live data, order book
- Vault copy required at `06-CLAUDE-LOGS/plans/2026-02-28-dash-skill-trading-dashboard-enrichment.md` (this file)

### State changes
- Plan document; SKILL.md update to be applied

### Open items recorded
- Verification: read SKILL.md to confirm 8 subsections, v1.1 version history, frontmatter keywords, no existing sections modified

### Notes
- This file IS its own vault copy per CLAUDE.md requirement.

---

## 2026-02-28-dash-skill-v12-community-audit.md
**Date:** 2026-02-28
**Type:** Session log (completed work)

### What happened
Community audit of the Dash skill conducted via WebSearch (WebFetch to community.plotly.com was blocked by permission hook). 15+ real practitioner discussions from community.plotly.com and GitHub issues (#64121, #355, #608, #3628, #3594) were retrieved and analyzed. Seven categories of undocumented gotchas were found: (1) extendData + Candlestick strict format, ghost artifact bug, trace index requirement, performance cliff at 2500+ bars; (2) dcc.Interval blocking if callback exceeds interval; (3) relayoutData + Candlestick infinite loop bug; (4) ag-grid styleConditions silently overrides textAlign, Math not available in condition strings; (5) WebSocket vs dcc.Interval — for <500ms needs, WebSocket non-negotiable; (6) background callback overhead meaningful only for >10s tasks, APScheduler + gunicorn without `--preload` = silent duplication; (7) rangebreaks performance cliff with >2 years of bar data. Part 4 was added to SKILL.md.

### Decisions recorded
- WebSearch used instead of WebFetch (different tool, not subject to the blocked hook)
- Part 4 appended to SKILL.md: "Community-Sourced Traps & Patterns"
- Use `cellStyle` function (JS) instead of `styleConditions` for complex ag-grid logic
- `xaxis.autorange = False` workaround for relayoutData infinite loop

### State changes
- SKILL.md modified: was 1447 lines (v1.1), now 1726 lines (v1.2)
- 7 new sections added to Part 4

### Open items recorded
None stated.

### Notes
- This document records completed work, not just a plan. SKILL.md was actually updated.

---

## 2026-02-28-dashboard-v393-validate-promote.md
**Date:** 2026-02-28
**Type:** Planning

### What happened
Plan to validate and promote the backtester dashboard v3.9.3 to production. The product backlog (P0.3) marked v3.9.3 as BLOCKED with "IndentationError at line 1972" but this was found to be stale — `py_compile` was already passing on the file. The actual remaining work was runtime validation + doc updates. v3.9.3 changes vs v3.9.2: stale cache fix (sidebar settings clear equity curves), sweep symbol persistence, selectbox key fix, PDF download button added. Steps: (1) user runs `streamlit run` and checks 7-item checklist, (2) update docs (PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md), (3) add trailing newline to v3.9.3, (4) ask user before deleting 3 dead fix scripts.

### Decisions recorded
- Stale backlog entry identified and corrected — py_compile already passes
- Doc update files listed: PRODUCT-BACKLOG.md, LIVE-SYSTEM-STATUS.md, DASHBOARD-FILES.md, PROJECT-OVERVIEW.md
- Dead scripts to ask user about (not auto-delete): build_dashboard_v393.py, build_dashboard_v393_fix.py, fix_v393_indentation.py

### State changes
- Plan document; actual promotion depends on user running the runtime test

### Open items recorded
- User must run runtime validation before docs can be updated
- Trailing newline to be added
- Dead scripts pending user decision

### Notes
- The stale backlog entry is a pattern: IndentationError was fixed during a prior session but the backlog was not updated.

---

## 2026-02-28-parquet-data-catchup.md
**Date:** 2026-02-28
**Type:** Planning (data maintenance)

### What happened
Short plan for updating 1m candle parquet files stale by 15 days (last fetch: 2026-02-13). No build needed. Existing infrastructure (`scripts/fetch_data.py`, `data/fetcher.py` BybitFetcher class, `data/cache/` with 399 coins) handles it. Run command given: `python scripts/fetch_data.py --months 1`. Script is restartable, rate-limited at 0.1s between requests, 5m candles skipped per prior user decision.

### Decisions recorded
- No new code needed
- 5m candles: skipped (1m only — per prior user decision)

### State changes
- No files created; run command provided for user to execute

### Open items recorded
- Verification: check for `Symbols fetched: 399/399` in output, spot-check .meta file end date

### Notes
- Data source: Bybit v5 API. 399 coins in cache.

---

## 2026-02-28-vince-b1-plugin-scope-audit.md
**Date:** 2026-02-28
**Type:** Research Audit / Planning

### What happened
Full audit and scope document for B1 (FourPillarsPlugin) build. Referenced `BUILD-VINCE-B1-PLUGIN.md` which did not exist at time of writing (was generated by this research). Key discovery: `strategies/four_pillars.py` already existed as a v1 partial implementation — not v2-compliant. 6 specific issues documented: wrong base class (v1 ABC not v2), 4 missing required methods, wrong signal version (`state_machine_v383.py` instead of `four_pillars_v383_v2.py`), wrong `compute_signals` signature, split enrichment method, legacy v1 classifier methods. NEVER OVERWRITE rule requires archiving to `strategies/four_pillars_v1_archive.py` first. Scope: one target file (strategies/four_pillars.py rewrite). 5 methods fully specified with implementation details. Four pre-build questions identified (file conflict, signal version mismatch, backtester_v385.py vs v384, no `symbol` field in Trade384, date filter mechanism).

### Decisions recorded
- NEVER OVERWRITE: create `strategies/four_pillars_v1_archive.py` backup first
- B1 scope: 5 methods (compute_signals, parameter_space, trade_schema, run_backtest, strategy_document property)
- `strategy_document`: point to `docs/FOUR-PILLARS-STRATEGY-UML.md`
- `run_backtest` output: write to `results/vince_{timestamp}.csv`, return Path
- `parameter_space()` sweepable params: sl_mult, tp_mult, be_trigger_atr, be_lock_atr, cross_level, allow_b_trades, allow_c_trades
- Thread safety: Backtester384 instantiated fresh per call — thread-safe
- Bar index note: entry_bar/exit_bar are 0-based indices into DATE-FILTERED slice; Enricher must use same slice

### State changes
- Research document; actual build to follow

### Open items recorded
- 4 pre-build confirmation questions listed (signal version, engine version, file conflict, date filter column name)
- Verification suite provided: syntax check, interface smoke test, compute_signals smoke test, full backtest smoke test

### Notes
- `backtester_v385.py` found alongside v384 — build plan specifies v384, requires confirmation. This was a discovery finding, not a resolution.

---

## 2026-02-28-vince-doc-sync.md
**Date:** 2026-02-28
**Type:** Session log (completed work — documentation sync)

### What happened
Master documentation sync operation for Vince v2 project state after 5 research sessions on 2026-02-28. Ran as an agent-executable instruction set. Created 5 new build docs (BUILD-VINCE-B2-API.md through BUILD-VINCE-B6-DASH-SHELL.md), updated 6 existing files (VINCE-V2-CONCEPT-v2.md, VINCE-PLUGIN-INTERFACE-SPEC-v1.md, INDEX.md, PRODUCT-BACKLOG.md, TOPIC-vince-v2.md, plus this plan file). BUILD-VINCE-B1-PLUGIN.md was skipped as it already existed (469 lines). Design verdicts for B2 were locked and documented: (1) plugin passed per-call (not global), (2) EnrichedTradeSet as DataFrame, (3) ConstellationFilter = typed fields + column_filters dict, (4) SessionRecord = named research session. Corrected run_enricher signature documented. Complete type definitions for all 7 dataclasses documented.

### Decisions recorded
- All B2 design verdicts locked (4 listed above)
- B2 through B6 all marked BLOCKED in status: B2 READY TO BUILD (after B1), B3-B6 BLOCKED on B1→B2→B3
- PRODUCT-BACKLOG updated: P0.5 updated, P1.8 (B2), P1.9 (B3), P2.5 (B4), P2.6 (B5), P2.7 (B6) added

### State changes
- 5 BUILD docs created in backtester project directory
- VINCE-V2-CONCEPT-v2.md: Build Status table prepended
- VINCE-PLUGIN-INTERFACE-SPEC-v1.md: Implementation Status table prepended
- INDEX.md: 4 new 2026-02-28 rows added
- PRODUCT-BACKLOG.md: B2-B6 entries added
- TOPIC-vince-v2.md: B1-B4 Research Sessions section appended

### Open items recorded
- Verification checklist listed (6 checks) to confirm all updates landed

### Notes
- This document reports completed execution, not just a plan. It is an execution log masquerading as a plan file.

---

## 2026-03-02-b2-api-types-build.md
**Date:** 2026-03-02
**Type:** Session log (completed build)

### What happened
B2 was built ahead of B1 because it has zero strategy dependency. Strategy (v386, state machine, exit logic) needed review before B1 could wrap it. B2 delivered: `vince/__init__.py`, `vince/types.py` (8 dataclasses), `vince/api.py` (8 API stubs), `vince/audit.py` (13-check auditor), `tests/test_b2_api.py` (5 test groups), `scripts/build_b2_api.py` (validation runner). All py_compile passed. Design verdicts locked on 2026-02-28 were used directly. Additional deliverable this session: strategy analysis report for Claude Web review (`scripts/build_strategy_analysis.py` producing `docs/STRATEGY-ANALYSIS-REPORT.md` with full source dump + 6 discussion questions).

### Decisions recorded
- B2 built ahead of B1 (unusual order — justified by zero strategy dependency)
- Strategy v386 review required before B1 can proceed
- Audit file added (`vince/audit.py` with 13-check auditor) — not originally in B2 spec
- Strategy analysis report added as additional deliverable for external Claude Web alignment session

### State changes
- 6 files created in backtester project:
  - `vince/__init__.py`
  - `vince/types.py` (8 dataclasses)
  - `vince/api.py` (8 API stubs)
  - `vince/audit.py` (13-check auditor)
  - `tests/test_b2_api.py` (5 test groups)
  - `scripts/build_b2_api.py`
- `docs/STRATEGY-ANALYSIS-REPORT.md` created by build script

### Open items recorded
- B1 blocked on strategy review/correction before wrapping
- Expected output when running build_b2_api.py: py_compile PASS + smoke tests PASS + CRITICAL audit findings (expected — document strategy issues, not B2 bugs)

### Notes
- Code verification: `vince/types.py` EXISTS on disk, `vince/api.py` EXISTS on disk — confirms build was executed.
- Note: `vince/audit.py` was an addition not in the original B2 spec from 2026-02-28.

---

## 2026-03-02-bingx-dashboard-patch6-7-css-statusfeed.md
**Date:** 2026-03-02
**Type:** Build Plan

### What happened
Plan for two patches to BingX dashboard v1-3. Patch 6 (CSS variables override): Dash 2.x injects CSS custom properties via `:root` in `dcc.css` — specifically `--Dash-Fill-Inverse-Strong: #fff`. Class-level `!important` cannot override CSS variables; must override at `:root`. Patch appends a block of ~12 `:root` variable overrides to `assets/dashboard.css`. Guard check prevents double-application. Timestamped backup created before modification. Patch 7 (bot status feed): adds live startup lifecycle messages to the Operational tab. Creates `bot-status.json` schema (bot_start + messages array). Modifies 4 files: `main.py` (adds `write_bot_status()` helper + 7 call sites at startup milestones, `STATUS_PATH` constant, overwrites bot-status.json at process start), `data_fetcher.py` (adds `progress_callback=None` to `warmup()`, fires every 5 symbols), `bingx-live-dashboard-v1-3.py` (adds `dcc.Store`, `dcc.Interval` at 5s, status feed panel UI in Operational tab, 2 new callbacks CB-S1 and CB-S2), `assets/dashboard.css` (status feed panel styles). Each patch has its own build script.

### Decisions recorded
- Patch 6: CSS variable override at `:root` level (only way to beat Dash 2.x injected variables)
- Patch 7: `bot-status.json` written atomically (tmp + os.replace) to avoid partial reads
- Progress callback fires every 5 symbols (not every symbol — avoid flooding file)
- Dashboard polls bot-status.json every 5s (separate from main 60s interval)
- Status feed shows last 20 messages, newest first
- Bot-status.json overwritten fresh at every process start (clear stale messages from prior run)

### State changes
- Build scripts to be created:
  - `scripts/build_dashboard_v1_3_patch6.py`
  - `scripts/build_dashboard_v1_3_patch7.py`
- Files to be modified: `assets/dashboard.css`, `bingx-live-dashboard-v1-3.py`, `main.py`, `data_fetcher.py`

### Open items recorded
- Patch 6 verification: restart dashboard, open date picker/dropdown, confirm dark background
- Patch 7 verification: restart bot, bot-status.json created, restart dashboard, status feed shows messages

### Notes
- Code verification: `scripts/build_dashboard_v1_3_patch6.py` EXISTS on disk, `scripts/build_dashboard_v1_3_patch7.py` EXISTS on disk — confirms both patches were executed.
- Root cause of persistent white backgrounds correctly identified: Dash 2.x CSS variable injection, not class-level rules.
