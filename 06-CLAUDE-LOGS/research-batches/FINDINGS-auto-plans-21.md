# Batch 21 Findings — Auto-Plans Research

**Batch:** 21 of 22
**Files processed:** 5
**Date processed:** 2026-03-06

---

## witty-giggling-galaxy.md
**Date:** Referenced as around 2026-02-23 (log reference at end of file)
**Type:** Planning / Bug Fix Plan

### What happened
Detailed plan for fixing a session state cache bug in Dashboard v3.9.2 (Portfolio Analysis mode). The bug caused equity curves to display from a previous date range instead of the currently selected custom date range. Investigation identified the root cause as Streamlit session state not being cleared when settings change — the hash mismatch check at line 1963 only showed a warning but did not clear stale data or stop rendering. A critical audit revision was performed: the original plan included `st.stop()` which was found to create a blank-page UX, so the corrected approach uses `_pd = None` to allow existing `if _pd is not None:` guards to naturally skip all rendering.

### Decisions recorded
- Use Option 2 (hash mismatch → clear cache) NOT Option 1 (date-range-only check)
- Do NOT use `st.stop()` — use `_pd = None` instead, letting existing guards skip rendering
- Create `dashboard_v393.py` as new file (NEVER overwrite v392)
- Build via `build_dashboard_v393.py` script
- Base the build on reading v392 content and replacing the 2-line warning block

### State changes
- Plan created for dashboard v3.9.3 fix
- Build script path defined: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_dashboard_v393.py`
- Output path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v393.py`
- Exact old/new code blocks specified in plan

### Open items recorded
- Run verification: 4-step test scenario (fresh session, change date range, re-run, regression test)
- Syntax check with py_compile mandatory
- Update MEMORY.md after successful build
- Log session to `06-CLAUDE-LOGS/2026-02-23-dashboard-v393-bug-fix.md`

### Notes
- Plan contains an internal contradiction: the Summary section still says "Fix: Clear `st.session_state["portfolio_data"]` and call `st.stop()`" while the Implementation Plan section correctly removes `st.stop()`. The Implementation Plan section is the authoritative corrected version.
- CODE VERIFICATION: Glob check needed for dashboard_v393.py.

---

## witty-wiggling-forest.md
**Date:** Not explicitly dated in file content
**Type:** Planning / Pine Script Fix Plan

### What happened
Plan to fix commission blow-up in Pine Script strategy v3.7. With commission OFF, v3.7 shows 222 trades and +$4,480 (+44.81%). With commission ON (0.06%), the account blows up. Root cause identified as phantom trades from `strategy.close_all()` + `strategy.entry()` on the same bar creating double-commission events with $0 P&L, plus rapid flipping with no cooldown amplifying the damage. Six changes were specified.

### Decisions recorded
1. Switch to `cash_per_order` commission: $6/side — deterministic, not ambiguous with leverage
2. Remove all 4 `strategy.close_all()` calls from flip logic (lines 287, 300, 312, 324)
3. Cancel stale exit orders before flips using `strategy.cancel()`
4. Add cooldown input `i_cooldown` (default 3 bars) between entries
5. Add `cooldownOK` bool gate to all 8 entry conditions
6. Add commission tracker row to dashboard table (update table from 12 to 13 rows)

### State changes
- Plan created for Pine Script v3.7 commission fix
- File to modify: `c:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\four_pillars_v3_7_strategy.pine`
- Specific line numbers called out: 12-17 (commission), 287/300/312/324 (close_all), 45 (cooldown input), 269 (cooldown gate), 474 (dashboard row)

### Open items recorded
- Verification steps: Load on TradingView with 1000PEPEUSDT.P 5min, verify no phantom trades, verify single trades for flips, verify no entries within 3 bars, verify "Comm$" row in dashboard

### Notes
- Commission value in plan is $6/side (not $8 as in some other references). MEMORY.md states: "70% account = $4.80/RT net, 50% account = $8.00/RT net" and "$6 entry + $6 exit" — consistent with $6/side in this plan.
- This plan is for Pine Script (TradingView), not Python backtester.

---

## zany-foraging-blum.md
**Date:** Audit notes reference 2026-02-27
**Type:** Planning / Build Plan (Web Scraper)

### What happened
Detailed plan to scrape the BingX API documentation site (`https://bingx-api.github.io/docs-v3/#/en/info`) into a single indexed markdown reference document. The existing manual reference covers only 11 endpoints; the full site has approximately 215 leaf endpoint pages across 8 top-level sections. Plan uses Playwright (headless Chromium) to handle the JS-rendered SPA. Full architecture specified: `BingXDocsScraper` class and `MarkdownCompiler` class. CLI arguments defined (`--output`, `--section`, `--test`, `--debug`, `--timeout`). Audit notes added 2026-02-27 with 6 critical fixes.

### Decisions recorded
- Use Playwright async headless Chromium (not requests/BeautifulSoup — site is JS-rendered SPA)
- Script location: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\scrape_bingx_docs.py`
- Test suite: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_scraper.py`
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-COMPLETE-REFERENCE.md`
- Save intermediate results every 20 pages to `.scrape-progress.json` for crash recovery
- Audit fix 1: Non-endpoint pages (Intro, Change Logs) need fallback to `main.innerText`
- Audit fix 2: WebSocket pages need different extraction path
- Audit fix 3: Python tab click must happen OUTSIDE `page.evaluate()` via Playwright API
- Audit fix 4: Use text-based selectors not index-based (indices go stale after SPA navigation)
- Audit fix 5: Follow all mandatory project rules (docstrings, py_compile, timestamps, etc.)
- Audit fix 6: `--output` default must be absolute path via `pathlib.Path(__file__).resolve()`

### State changes
- Plan created for BingX API docs scraper
- Plan vault copy reference: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-bingx-api-docs-scraper.md`
- Two Python files to create (scraper + test suite)
- One output markdown document to generate (~215 endpoints)

### Open items recorded
- Run test mode first (3 pages), then single section (Swap ~69 endpoints), then full scrape (~215)
- Validate output: TOC present, 3 random endpoint spot checks, no empty sections in log
- py_compile both .py files (mandatory)
- Run test_scraper.py (4 tests: nav tree, single page, markdown compile, full section)

### Notes
- This plan references Playwright MCP tools as a prerequisite ("user now has Playwright MCP tools available") — script depends on Playwright being installed.
- CODE VERIFICATION: Glob check needed for `scrape_bingx_docs.py`.

---

## zazzy-bouncing-boot.md
**Date:** 2026-02-19 (explicitly stated)
**Type:** Planning / Architecture Scope Session

### What happened
Comprehensive build plan for Vince v2 — the ML strategy optimizer/analyst for the Four Pillars trading system. This document combined a session log from a scope-only session (2026-02-19) with a full architectural build plan. The scope session established that Vince RUNS THE BACKTESTER HIMSELF (not passive CSV reader), learns from statistical frequency (not ML model weights), logs all runs with timestamps, and operates in three modes: user query, auto-discovery, and settings optimizer. Fixed constants identified (stochastic periods, cloud EMAs). Six-module architecture defined with strict build order.

### Decisions recorded
- Vince has 3 operating modes: (1) User constellation query, (2) Auto-discovery sweep, (3) Settings optimizer
- Fixed constants Vince NEVER sweeps: K1=9, K2=14, K3=40, K4=60 (Kurisko); Cloud EMAs 5/12, 34/50, 72/89
- Vince can sweep: TP mult (0.5-5.0), SL mult (1.0-4.0), cross_level, zone_level, allow_b/c, cloud3 gate, BE trigger, checkpoint_interval, sigma_floor_atr
- Core principle: "Vince reads. User changes." — strategy rule changes made by user, not Vince
- No PyTorch/GPU in MVP — pandas + numpy sufficient for 90K trades (deferred to v2.1 for 400 coins)
- No price charts in output — user reads indicators only
- Rebate constraint non-negotiable: win rate improvement cannot come at cost of volume
- RE-ENTRY wrongly programmed — Vince will expose this, fix deferred
- B/C trade logic may need full rewrite — Vince shows data, user rewrites rules
- 5 panels: Coin Scorecard, LSG Anatomy, Constellation Query Builder, Exit State Analysis, Validation
- 6 modules in strict build order: schema.py → enricher.py → analyzer.py → sampling.py → report.py → dashboard_tab.py
- Deliverable 0 (first output before any code): `docs/vince/VINCE-PROJECT.md`
- Session was at 70-75% context — note to open new chat

### State changes
- Scope session completed 2026-02-19 — no code built yet
- Architecture fully locked in plan
- All file paths defined for 6 modules + tests + build script
- Constellation query dimensions fully specified (static, volatility, dynamic, trade filters, outcome filters)
- Data flow diagram documented

### Open items recorded
- All code to be built (this was scope-only session)
- Verification steps defined: build script run, enricher tests, analyzer tests, smoke test on RIVERUSDT, dashboard integration
- Dashboard integration: add Vince tab to dashboard_v392 via patch in build_dashboard_v392.py

### Notes
- Plan references `Backtester384` and `signals/four_pillars_v383.py` as existing — these are reused not recreated.
- Plan references `compute_signals_v383` but MEMORY.md shows current version is v3.8.4. Discrepancy: plan may predate v3.8.4.
- Dashboard integration targets dashboard_v392 — but dashboard_v393 build plan also exists (witty-giggling-galaxy.md). Version alignment may need checking at build time.

---

## zazzy-wibbling-pudding.md
**Date:** 2026-02-27 (explicitly stated in file)
**Type:** Planning / Documentation Build Plan

### What happened
Plan to create a single cross-project master overview file (`PROJECT-OVERVIEW.md`) in the vault root. The vault had 27 UML/diagram files but all were intra-project. This plan addresses the missing cross-project oversight view showing all 4 active projects, their status, inter-project connections, current blockers, and immediate next actions. The plan was created after a high-output day (6 sessions across 3 projects on 2026-02-27).

### Decisions recorded
- Create one new file: `C:\Users\User\Documents\Obsidian Vault\PROJECT-OVERVIEW.md`
- No existing files modified
- File contains: master Mermaid graph, status legend, today's output summary, active blockers table, next actions table
- Also save plan copy to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-project-overview-diagram.md`
- Append row to INDEX.md

### State changes
- Plan created for PROJECT-OVERVIEW.md
- Mermaid diagram design fully specified in plan (5 subgraphs: INFRA, BACKTESTER, VINCE, BINGX, YT)
- Status as of 2026-02-27 captured in diagram nodes:
  - Dashboard v3.9.2 PRODUCTION, v3.9.3 BLOCKED (IndentationError)
  - BBW Pipeline L1-L5 COMPLETE
  - BingX Bot DEMO VALIDATED (5m, 47 coins), go-live WAITING on funds transfer
  - BingX Live Screener and Daily P&L Report BUILT 2026-02-27
  - BingX API Docs (215 endpoints) SCRAPED 2026-02-27
  - Vince: Concept LOCKED, Plugin Interface Spec v1 DONE, base_v2.py stub DONE
  - YT Analyzer GUI v2.1 BUILT 2026-02-27, CodeTradingCafe run COMPLETE (201 videos, 50min)

### Open items recorded
- Verify mermaid renders in Obsidian
- Confirm inter-project arrows accurate against LIVE-SYSTEM-STATUS.md
- Confirm blockers table matches PRODUCT-BACKLOG.md P0 section

### Notes
- Dashboard v3.9.3 is noted as "BLOCKED - IndentationError" in the diagram — this matches context from other logs about the dashboard build having a syntax error.
- This plan's diagram shows BingX API Docs as "SCRAPED 2026-02-27" — the scraper plan (zany-foraging-blum.md) was also from 2026-02-27, suggesting they were from the same session day.
- CODE VERIFICATION: Not applicable — this plan produces a markdown file, not Python.
