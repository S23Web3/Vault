# Session Log Index
**Last Updated:** 2026-03-03
**Total:** 144 markdown files, 2 JSON manifests, 1 Python script

---

## By Date (newest first)

### 2026-03-03
| File | Summary |
| ---- | ------- |
| `2026-03-03-cuda-dashboard-v394-build.md` | CUDA dashboard v394 build session. Audited spec (4 issues found: engine version mismatch, column names, reentry cloud3 gate, v393 claim). Wrote build_cuda_engine.py (py_compile PASS). Discovered Python 3.13 CUDA blocker (Numba access violation). Wrote PowerShell Python 3.12 install script. Build script creates cuda_sweep.py + jit_backtest.py + dashboard_v394.py. |
| `2026-03-03-cuda-dashboard-v394-planning.md` | CUDA dashboard v394 spec planning. No code written. Identified 4 pre-audit errors in existing vault plan (column names, param_grid shape, tp sentinel, missing cloud3 arrays). Wrote corrected dashboard-focused handover spec: plans/2026-03-03-cuda-dashboard-v394-spec.md. Supersedes 2026-03-03-cuda-sweep-engine.md (which had errors). |
| `2026-03-03-bingx-dashboard-v1-4-patches.md` | BingX dashboard v1-4: diagnosed doubled Activity Log (patch7 ran twice on main.py), IndexError (CB-T3 initial_duplicate + CB-S1 conflict), Activity Log height cap. Wrote build_dashboard_v1_4_patch2.py (13 patches: dedup main.py, toggle button, OFFLINE header, 360px log height). Browser cache KeyError at session end — requires Ctrl+Shift+R after dashboard restart. |
| `2026-03-03-session-handoff.md` | Context switch session. No new builds. Verified B2 artefacts intact. Identified B1 spec conflict (build spec says v383_v2, plan mode plan says v386 — v386 is correct). Wrote next-steps roadmap: plans/2026-03-03-next-steps-roadmap.md. |
| `2026-03-03-ttp-integration-plan.md` | TTP engine integration planning session. Audited initial mark-price approach, found 5 critical gaps, revised to hybrid architecture (TTP evaluates in market_loop on real OHLC, closes execute in monitor_loop). Plan finalized with full pseudocode and file-by-file change lists. |
| `2026-03-03-ttp-integration-build.md` | TTP engine build session. Wrote build_ttp_integration.py (6 patches: ttp_engine.py, signal_engine.py, position_monitor.py, main.py, config.yaml, test_ttp_engine.py) and build_dashboard_v1_4_patch3.py (5 patches: TTP columns, build_positions_df, Controls layout, CB-11, CB-12). Both py_compile PASS. |

### 2026-03-03
| File | Summary |
| ---- | ------- |
| `2026-03-03-signal-rename-architecture-session.md` | Signal rename session: A→Quad, B→Rotation (TBC), C→ADD. ADD is engine classification not state machine signal. Pine C (2/4) logic identified as wrong by design. Full gap analysis: Pine vs Python backtester vs intended behaviour. Pending: Q2/Q3/Q4/Q5 unanswered. No code written. |

### 2026-03-02
| File | Summary |
| ---- | ------- |
| `2026-03-02-b2-api-types-build.md` | B2 built: vince/ package created (\_\_init\_\_.py, types.py, api.py, audit.py). 8 dataclasses, 8 API stubs, 13-check codebase auditor. All py_compile PASS. Audit finds: bot runs v1 signal (not v386), BBW orphaned, ExitManager likely dead code, trailing stop divergence, BE raise missing from bot. Strategy analysis report also built (scripts/build_strategy_analysis.py). |
| `2026-03-02-bingx-dashboard-v1-3-audit-and-patches.md` | Dashboard v1-3 full audit. Patches 1-5 applied: balance from API, position reconciliation, date filter (>=Feb27), stale session detection, coin detail on click. Root cause found for white backgrounds: Dash 2.x CSS custom properties (--Dash-Fill-Inverse-Strong: #fff). Fix is :root variable overrides in dashboard.css. Patch 6 pending. |

### 2026-02-28
| File | Summary |
| ---- | ------- |
| `2026-02-28-v386-scoping.md` | v386 scoping: require_stage2=True + allow_c=False locked. Produced signals/four_pillars_v386.py (py_compile PASS) + FOUR-PILLARS-STRATEGY-v386.md. State machine unchanged. ~93/day -> ~40/day. B1 unblocked. |
| `2026-02-28-parquet-data-catchup.md` | Parquet data catch-up: cache stale since 2026-02-13 (15 days). Confirmed Bybit v5 source. Found config only listed 5 coins so `--coins 399` was useless. Added `--all` flag to fetch_data.py (discovers symbols from cached parquets). py_compile OK. |
| `2026-02-28-dashboard-v393-promote.md` | Dashboard v3.9.3 validated and promoted. Backlog P0.3 was stale (py_compile already passes). Found + fixed silent date filter fallback: 7d showed full year because apply_date_filter silently returned unfiltered data when <100 bars matched. Now warns user. 4 edits to dashboard_v393.py. |
| `2026-02-28-bingx-dashboard-v1-3-patch.md` | Dashboard v1-3 patch: 10 fixes from v1-2 live testing. White tabs/inputs/date pickers fixed (comprehensive dark CSS ~270 lines). Max DD% capped at -100%. pd.read_json deprecation fixed (io.StringIO). Input contrast improved (#21262d bg + #484f58 borders). Build script py_compile OK. NOT YET RUN. |
| `2026-02-28-bingx-dashboard-v1-2-build.md` | Dashboard v1-2 build script written. Surgical approach: reads v1-1, applies 8 fixes (dark CSS, date pickers, all-tabs-visible, timing diagnostics, professional analytics with Sharpe/MaxDD%/SL%/TP%). Clientside JS replaces CB-2 for instant tab switching. Build script py_compile OK. NOT YET RUN. |
| `2026-02-28-bingx-trade-analysis-be-session.md` | Trade analysis script completed (Phase 3 only, live prices + open orders). BE+fees clarification: SL-at-entry exits relabeled (not true BE). Bot fixes: main.py fallback rate 0.0016→0.001, position_monitor BE Telegram renamed BE+FEES RAISED with commission USD shown. |
| `2026-02-28-bingx-be-fix.md` | BE fix: stop price corrected from entry_price to entry*(1±commission_rate). Confirmed from logs: 8 BE raises fired but all exited at a loss. Fix = 3 lines in _place_be_sl(). Return sig changed to float/None. 7 tests in test_position_monitor.py. py_compile OK. |
| `2026-02-28-bingx-dashboard-v1-1-build.md` | Dashboard v1-1 built (3 files: Dash app, CSS, tests). Logic audit found 3 bugs (critical: wrong qty in API orders, medium: no mark validation in BE raise, medium: history tab not auto-refreshing). All fixed. TTP research reviewed — new trailing fields safely ignored by dashboard. |
| `2026-02-28-bingx-ttp-research.md` | TTP research: 6 trailing TP examples evaluated, 5 approaches compared. Approach C chosen (BingX Native Trailing with activation gate). Implemented in executor.py + config.yaml + tests. Future: Approach D (AVWAP 2s + 10-candle counter). |
| `2026-02-28-vince-b4-scope-audit.md` | B4 PnL Reversal panel: full research audit. Skills identified (four-pillars, four-pillars-project, dash for B6, Python). 8 bottlenecks surfaced (mfe/saw_green field verification, TP sweep simulation vs re-run, ATR bin granularity, RL overlay scope, enricher MFE normalization, API surface, unused timeframe arg). 6 improvements proposed (9-bin histogram, winners-left-on-table, per-grade TP sweep, gross+net dual curve, date filtering, BE-adjusted MFE). Hard blocker: entire vince/ directory missing — B1→B2→B3 must complete first. No code built. |
| `2026-02-28-vince-b1-scope-audit.md` | B1 FourPillarsPlugin: research, scope & audit. BUILD-VINCE-B1-PLUGIN.md created. 6 v1 file problems found (wrong base class, 4 missing methods, wrong signal version). Engine decision: v385 over v384 (entry-state pre-enrichment). Skills: four-pillars + four-pillars-project only. No code built. |
| `2026-02-28-b3-enricher-research-audit.md` | B3 Enricher full research audit. 6 critical blockers identified (mfe_bar missing from Trade384, signature mismatch, column naming, diskcache not installed, bar index offset bug, OHLC tuple format). 8 open questions. 6 improvements. No code written — awaiting user decisions. |
| `2026-02-28-b2-api-types-research.md` | B2 research audit: vince/types.py + vince/api.py. 7 bottlenecks found. 4 design decisions researched + verdicts: per-call plugin arg, DataFrame-centric EnrichedTradeSet, typed base + column_filters dict for ConstellationFilter, named research session for SessionRecord. Corrected run_enricher signature. No code built. |
| `2026-02-28-bingx-dashboard-vince-planning.md` | Session 1: Planning only — BingX dashboard + Vince B1-B6 plan locked. No code built. Session reset after I assumed dashboard layout without asking user. Session 2 (appended): User gave dashboard requirements (3 tabs, interactive position management — raise BE, move SL). I incorrectly assumed read-only twice. User proved from logs that read-only was never stated. Streamlit read-only file written but wrong — needs interactive Dash replacement next session. |
| `2026-02-28-dash-skill-v12-community-audit.md` | Dash skill v1.1 → v1.2. Community audit via WebSearch (WebFetch blocked by hook). 10 searches, 15+ community.plotly.com threads. Added Part 4: 7 sections of community-sourced traps — extendData candlestick format/ghost bug, dcc.Interval queue buildup, relayoutData infinite loop, ag-grid styleConditions side effects, WebSocket vs Interval guide, background callback failure modes, trading dashboard test checklist. Skill: 1447 → 1726 lines. |

### 2026-02-27
| File | Summary |
|------|---------|
| 2026-02-27-bingx-ws-and-breakeven.md | Live bot session: breakeven raise built + confirmed live. 4 WS fixes (listenKey method, response parsing, gzip, Ping/Pong). Stage 2 param bug fixed. API audit vs docs. Bot live on $110, open=2, WS stable. |
|------|---------|
| 2026-02-27-dash-skill-creation.md | Dash super-skill creation: 1,040-line 2-in-1 skill file for Vince v2 Dash dashboard. Covers multi-page app, pattern-matching callbacks (MATCH/ALL), dcc.Store, background callbacks, ag-grid, ML serving, PostgreSQL, production stability. CLAUDE.md + MEMORY.md hard rules added. Known bugs table (6 issues). Dual guarantee system. |
| 2026-02-27-bingx-api-docs-scraper-session.md | BingX API docs scraper build: Playwright-based async scraper for full ~215-endpoint SPA site. 2 files (scraper + test suite), 6 audit fixes, 3 run modes (test/section/full). Output: indexed markdown reference. |
| 2026-02-27-bingx-trade-analysis.md | 5m demo trade analysis: 31 trades, -$379 PnL. EXIT_UNKNOWN down to 6%. BingX VST API oddities (vanishing orders, wrong fills, mislabeled exits). Decision: stop optimizing demo, move to Vince. |
| 2026-02-27-yt-analyzer-v2-build.md | YT Analyzer v2: timestamp preservation, clickable YouTube links, LLM summaries+tags via qwen3:8b, TOC, download stats, absolute output path fix. 6 files modified, 30 test scenarios, 6 debug protocols. |
| 2026-02-27-bingx-automation-build.md | BingX automation build: live screener (screener/bingx_screener.py) + daily P&L report (scripts/daily_report.py). py_compile pass. Scraper completed (16KB API reference). |
| 2026-02-27-vince-concept-doc-update-and-plugin-spec.md | Vince concept doc: 10 edits from ML findings (RL exit policy, random sampling, walk-forward, intra-candle timing). Plugin spec (7 sections) + strategies/base_v2.py stub created. Coherence review: 5 fixes (wrong filename, non-existent file, missing symbol column, strategy-agnostic RL state vector, type hint). |
| 2026-02-27-vince-ml-yt-findings.md | Vince ML research: read all 202 YT channel summaries + FreeCodeCamp course. Key findings: RL exit policy optimizer (missing piece), k-means clustering for Mode 2, XGBoost feature importance, exits > entries. 7 items to update in Vince v2 concept doc. |
| plans/2026-02-27-project-overview-diagram.md | Plan: cross-project master overview diagram. Created PROJECT-OVERVIEW.md at vault root with Mermaid graph of all 4 projects, status legend, today's output, blockers, next actions. |
| 2026-02-27-project-overview-session.md | Session review + PROJECT-OVERVIEW.md creation. Cross-project map: 4 projects, inter-project flow diagram, status tables, blockers, next actions. All 2026-02-27 output summarised. |
| 2026-02-27-vince-concept-lock-final.md | Vince v2 concept locked (APPROVED FOR BUILD). GUI + Architecture sections added to VINCE-V2-CONCEPT-v2.md. Build plan B1-B10 created. Dash skill (1040 lines) created. 4 plan alignment issues resolved (pages/ convention, four_pillars.py filename, B4 data-only clarification, diskcache storage). Vault plan copy written. |
| plans/2026-02-27-vince-b1-b10-build-plan.md | Vault copy of build plan: B1 FourPillarsPlugin → B10 Panels 6/7/8. Dash 4.0, pages/ convention, diskcache for enriched trades. |

### 2026-02-26
| File | Summary |
|------|---------|
| 2026-02-26-yt-analyzer-gui-session.md | YT Analyzer GUI build: Streamlit GUI, drain mode (no query), real-time progress with Popen callback, sidebar tool checks (yt-dlp/ffmpeg/deno), ffmpeg+deno install lesson |
| 2026-02-26-vps-migration-part-a-violation.md | Part A completed (1017 files pushed to GitHub). RULE VIOLATION: executed git add/commit/push without user permission. User wanted to run it themselves. |
| 2026-02-26-vault-vps-migration-session.md | VPS migration scripts: migrate_pc.ps1, setup_vps.sh, deploy.ps1. Two audit rounds (code quality + lifeline). Ubuntu line ending fixes. |
| 2026-02-26-bingx-audit-session.md | Master audit script, 103 trades all EXIT_UNKNOWN (SL assumed), strategy comparison, cooldown gap found |
| 2026-02-26-vps-migration-gitignore.md | Vault .gitignore created, bingx .gitignore updated (logs/ + venv/), no code changes needed for VPS |

### 2026-02-25
| File | Summary |
|------|---------|
| 2026-02-25-bingx-connector-session.md | BingX demo live: leverage hedge mode fix, buffer off-by-one fix |
| 2026-02-25-lifecycle-test-session.md | API lifecycle test script, 15/15 PASS, stopPrice string-vs-float bug |
| 2026-02-25-telegram-connection-session.md | Telegram bot setup for BingX connector alerts |
| 2026-02-25-test-telegram-github-note.md | GitHub release note draft for test_telegram.py |

### 2026-02-24
| File | Summary |
|------|---------|
| 2026-02-24-countdown-to-live-session.md | Master go-live plan, 3-step checklist, week target |
| 2026-02-24-fault-report-step1-build-review.md | Code audit: 5 faults found, all 5 resolved |
| 2026-02-24-screener-scope.md | Screener v1 scoping (backtester-based, later superseded) |
| 2026-02-24-vince-todo.md | Vince v2 parked TODO items (4 items) |
| 2026-02-24-vince-v2-ml-spec-review.md | Vince v2 ML spec review and corrections |
| 2026-02-24-weex-screener-scope.md | WEEX screener scope: 3 files, public API, signal metrics |

### 2026-02-23
| File | Summary |
|------|---------|
| 2026-02-23-dashboard-v393-bug-fix.md | Dashboard v3.9.3 equity curve date filter bug fix |
| 2026-02-23-four-pillars-strategy-scoping.md | Strategy scoping: 19 open unknowns for Step 2 |
| 2026-02-23-screener-scope.md | Screener architecture discussion |

### 2026-02-20
| File | Summary |
|------|---------|
| 2026-02-20-bingx-architecture-session.md | BingX connector UML architecture design |
| 2026-02-20-bingx-connector-build.md | BingX connector build: 25 files, 67/67 tests |
| 2026-02-20-vince-scope.md | Vince v2 full scope session, all decisions, pick-up instructions |
| 2026-02-20-youtube-transcript-analyzer-build.md | YT transcript analyzer spec and build |

### 2026-02-19
| File | Summary |
|------|---------|
| 2026-02-19-engine-audit.md | Backtester engine audit + architecture review |
| 2026-02-19-vince-scope.md | Vince scope continuation, full state, pick up here |

### 2026-02-18
| File | Summary |
|------|---------|
| 2026-02-18-dashboard-audit.md | Dashboard v3.9.1 engine audit, all 9 source files verified |
| 2026-02-18-dashboard-v392-build.md | Dashboard v3.9.2 build session |
| 2026-02-18-vince-ml-build.md | Vince ML module build session |
| 2026-02-18-vince-ml-build-plan.md | Vince ML build plan |
| 2026-02-18-vince-scope-session.md | Initial Vince v2 scope session |

### 2026-02-17
| File | Summary |
|------|---------|
| 2026-02-17-bbw-project-completion-status.md | BBW pipeline completion status report |
| 2026-02-17-dashboard-v391-audit.md | Dashboard v3.9.1 audit |
| 2026-02-17-pdf-diagram-alignment.md | PDF export diagram alignment fixes |
| 2026-02-17-pdf-export-optimization.md | PDF exporter optimization |
| 2026-02-17-pdf-orientation-fix.md | PDF orientation/layout fix |
| 2026-02-17-project-clarity-and-vince-architecture.md | Project clarity session, Vince architecture decisions |
| 2026-02-17-python-skill-update.md | Python skill file updates |
| 2026-02-17-uml-diagrams-creation.md | UML diagram creation for backtester |
| 2026-02-17-uml-logic-debugging.md | UML logic debugging session |
| 2026-02-17-vince-ml-strategy-exposure-audit.md | ML strategy exposure audit |

### 2026-02-16
| File | Summary |
|------|---------|
| 2026-02-16-bbw-layer4b-plan.md | BBW Layer 4b Monte Carlo plan |
| 2026-02-16-bbw-layer4b-results.md | BBW Layer 4b results |
| 2026-02-16-bbw-v2-fundamental-corrections.md | BBW v2 fundamental corrections |
| 2026-02-16-bbw-v2-layer4-5-prebuild-analysis.md | BBW Layer 4-5 prebuild analysis |
| 2026-02-16-bbw-v2-layer4-build-journal.md | BBW Layer 4 build journal |
| 2026-02-16-bbw-v2-layer4b-build-journal.md | BBW Layer 4b build journal |
| 2026-02-16-bbw-v2-layer5-logic-analysis.md | BBW Layer 5 logic analysis |
| 2026-02-16-full-project-review.md | Full project review |
| 2026-02-16-portfolio-bugfix.md | Portfolio manager bug fix |
| 2026-02-16-portfolio-v3-audit.md | Portfolio v3 audit |
| 2026-02-16-project-status-data-strategy.md | Project status, data, strategy overview |
| 2026-02-16-strategy-actual-implementation.md | Strategy actual implementation review |
| 2026-02-16-trade-flow-uml.md | Trade flow UML diagrams |

### 2026-02-14
| File | Summary |
|------|---------|
| 2026-02-14-bbw-full-session.md | BBW full build session (Layers 1-3) |
| 2026-02-14-bbw-layer1-build.md | BBW Layer 1 build |
| 2026-02-14-bbw-layer1-prompt.md | BBW Layer 1 build prompt |
| 2026-02-14-bbw-layer2-build.md | BBW Layer 2 build |
| 2026-02-14-bbw-layer3-audit-pass3.md | BBW Layer 3 audit pass 3 |
| 2026-02-14-bbw-layer3-journal.md | BBW Layer 3 build journal |
| 2026-02-14-bbw-layer3-prompt-build.md | BBW Layer 3 build prompt |
| 2026-02-14-bbw-layer3-results.md | BBW Layer 3 results |
| 2026-02-14-bbw-layer4-audit-and-sync.md | BBW Layer 4 audit and sync |
| 2026-02-14-bbw-layer4-audit.md | BBW Layer 4 audit |
| 2026-02-14-bbw-layer4-results.md | BBW Layer 4 results |
| 2026-02-14-bbw-layer5-audit.md | BBW Layer 5 audit |
| 2026-02-14-bbw-layer5-build-prompt.md | BBW Layer 5 build prompt |
| 2026-02-14-bbw-layer5-v2-build-session.md | BBW Layer 5 v2 build |
| 2026-02-14-bbw-layer6-audit.md | BBW Layer 6 audit |
| 2026-02-14-bbw-layer6-build-prompt.md | BBW Layer 6 build prompt |
| 2026-02-14-bbw-uml-research.md | BBW UML research |
| 2026-02-14-core-build-2.md | Core build session 2 |
| 2026-02-14-dashboard-v31-build.md | Dashboard v3.1 build |
| 2026-02-14-layer1-bugfix.md | Layer 1 bug fix |
| 2026-02-14-operational-logic-audit.md | Operational logic audit |
| 2026-02-14-project-flow-update.md | Project flow update |
| 2026-02-14-vault-sweep-fixes.md | Vault sweep fixes applied |
| 2026-02-14-vault-sweep-manifest.json | Vault sweep manifest (JSON) |
| 2026-02-14-vault-sweep-manifest.md | Vault sweep manifest |
| 2026-02-14-vault-sweep-review.md | Vault sweep review |

### 2026-02-13
| File | Summary |
|------|---------|
| 2026-02-13.md | Daily session log |
| 2026-02-13-build-journal-cc.md | Build journal (Claude Code) |
| 2026-02-13-build-journal-desktop.md | Build journal (Desktop) |
| 2026-02-13-dashboard-v3-spec-build.md | Dashboard v3 spec and build |
| 2026-02-13-data-pipeline-build.md | Data pipeline build |
| 2026-02-13-full-project-review.md | Full project review |
| 2026-02-13-hello-world-test.md | Hello world test (initial setup) |
| 2026-02-13-journal-audit.md | Journal audit |
| 2026-02-13-project-audit.md | Project audit |
| 2026-02-13-vault-sweep-manifest.json | Vault sweep manifest (JSON) |
| 2026-02-13-vault-sweep-manifest.md | Vault sweep manifest |
| 2026-02-13-vault-sweep-review.md | Vault sweep review |
| 2026-02-13-vince-ml-build-session.md | Vince ML build session |

### 2026-02-12
| File | Summary |
|------|---------|
| 2026-02-12.md | Daily session log |
| 2026-02-12-build-journal.md | Build journal |
| 2026-02-12-memory-test.md | Memory system test |
| 2026-02-12-project-review-direction.md | Project review and direction |
| 2026-02-12-test-file.md | Test file |

### 2026-02-11
| File | Summary |
|------|---------|
| 2026-02-11.md | Daily session log |
| 2026-02-11-build-journal.md | Build journal |
| 2026-02-11-recent-chats-log.md | Recent chats log |
| 2026-02-11-v38-build-session.md | v3.8 build session |
| 2026-02-11-v382-avwap-trailing-build.md | v3.8.2 AVWAP trailing stop build |
| 2026-02-11-vince-ml-architecture.md | Vince ML architecture |
| 2026-02-11-vince-ml-Session Log.md | Vince ML session log |
| 2026-02-11-WEEK-2-MILESTONE.md | Week 2 milestone summary |

### 2026-02-10
| File | Summary |
|------|---------|
| 2026-02-10.md | Daily session log |
| 2026-02-10-build-journal.md | Build journal |
| 2026-02-10-session1.md | Session 1 |
| 2026-02-10-session2.md | Session 2 |

### 2026-02-09
| File | Summary |
|------|---------|
| 2026-02-09.md | Daily session log |
| 2026-02-09-build-journal.md | Build journal |
| 2026-02-09-session-handoff.md | Session handoff notes |

### 2026-02-08
| File | Summary |
|------|---------|
| 2026-02-08.md | Daily session log |
| 2026-02-08-build-journal.md | Build journal |

### 2026-02-07
| File | Summary |
|------|---------|
| 2026-02-07.md | Daily session log |
| 2026-02-07-backtest-results.md | Backtest results |
| 2026-02-07-build-journal.md | Build journal |
| 2026-02-07-progress-review.md | Progress review |

### 2026-02-06
| File | Summary |
|------|---------|
| 2026-02-06.md | Daily session log |
| 2026-02-06-build-journal.md | Build journal |

### 2026-02-05
| File | Summary |
|------|---------|
| 2026-02-05.md | Daily session log |
| 2026-02-05-build-journal.md | Build journal |
| 2026-02-05-strategy-analysis-session.md | Strategy analysis session |

### 2026-02-04
| File | Summary |
|------|---------|
| 2026-02-04.md | Daily session log |
| 2026-02-04-build-journal.md | Build journal |
| 2026-02-04-four-pillars-strategy-specification.md | Four Pillars strategy specification |
| 2026-02-04-indicator-review-session.md | Indicator review session |
| 2026-02-04-quad-rotation-fast-v1.3-build.md | Quad Rotation Fast v1.3 build |

### 2026-02-03
| File | Summary |
|------|---------|
| 2026-02-03.md | Daily session log |
| 2026-02-03-build-journal.md | Build journal |
| 2026-02-03-quad-rotation-stochastic-spec-review.md | Quad Rotation stochastic spec review |
| 2026-02-03-quad-rotation-v4-fast-build-session.md | Quad Rotation v4 Fast build session |

### 2026-02-02
| File | Summary |
|------|---------|
| 2026-02-02.md | Daily session log |
| 2026-02-02-atr-sl-trailing-tp-build-spec.md | ATR SL trailing TP build spec |
| 2026-02-02-atr-sl-trailing-tp-session.md | ATR SL trailing TP session |
| 2026-02-02-avwap-anchor-assistant-framework.md | AVWAP anchor assistant framework |
| 2026-02-02-dashboard-framework.md | Dashboard framework |
| 2026-02-02-ripster-volume-status-build.md | Ripster volume status build |

### 2026-01-31
| File | Summary |
|------|---------|
| 2026-01-31-quad-rotation-session.md | Quad Rotation session |
| 2026-01-31-session-summary.md | Session summary |

### 2026-01-29 - 2026-01-30
| File | Summary |
|------|---------|
| 2026-01-30-tradingview-indicator-development.md | TradingView indicator development |
| 2026-01-29-pine-script-review.md | Pine Script review |
| 2026-01-29-session-summary.md | Session summary |
| 2026-01-29-strategy-refinement-session.md | Strategy refinement session |

### 2026-01-24 - 2026-01-28
| File | Summary |
|------|---------|
| 2026-01-28-Jacky-VPS-Setup.md | Jacky VPS setup (n8n + nginx) |
| 2026-01-28-n8n-webhook-testing.md | n8n webhook testing |
| 2026-01-25-trading-dashboard.md | Trading dashboard |
| 2026-01-24.md | Daily session log |

### 2025-01-21
| File | Summary |
|------|---------|
| Session-2025-01-21.md | Earliest session log (2025) |

---

## Undated / Non-Standard Files

| File | Summary |
|------|---------|
| BUILD-JOURNAL-2026-02-13.md | Build journal (uppercase naming) |
| build_journal_2026-02-11.md | Build journal (underscore naming) |
| PENDING-TASKS-MASTER.md | Detailed 14-item task list snapshot (2026-02-24) |
| commission-rebate-analysis.md | Commission rebate analysis |
| telegram_connection_test.py | Telegram connection test script (Python, not markdown) |

---

## By Topic

### BingX Connector (11 files)
- 2026-02-28-bingx-ttp-research.md
- 2026-02-27-bingx-trade-analysis.md
- 2026-02-26-vps-setup-and-autostart.md
- 2026-02-26-bingx-audit-session.md
- 2026-02-25-bingx-connector-session.md
- 2026-02-25-lifecycle-test-session.md
- 2026-02-25-telegram-connection-session.md
- 2026-02-25-test-telegram-github-note.md
- 2026-02-24-countdown-to-live-session.md
- 2026-02-24-fault-report-step1-build-review.md
- 2026-02-20-bingx-architecture-session.md
- 2026-02-20-bingx-connector-build.md

### BBW Simulator Pipeline (20 files)
- 2026-02-17-bbw-project-completion-status.md
- 2026-02-16-bbw-layer4b-plan.md
- 2026-02-16-bbw-layer4b-results.md
- 2026-02-16-bbw-v2-fundamental-corrections.md
- 2026-02-16-bbw-v2-layer4-5-prebuild-analysis.md
- 2026-02-16-bbw-v2-layer4-build-journal.md
- 2026-02-16-bbw-v2-layer4b-build-journal.md
- 2026-02-16-bbw-v2-layer5-logic-analysis.md
- 2026-02-14-bbw-full-session.md
- 2026-02-14-bbw-layer1-build.md through bbw-layer6-build-prompt.md (14 files)
- 2026-02-14-bbw-uml-research.md

### Dashboard (6 files)
- 2026-02-23-dashboard-v393-bug-fix.md
- 2026-02-18-dashboard-audit.md
- 2026-02-18-dashboard-v392-build.md
- 2026-02-17-dashboard-v391-audit.md
- 2026-02-14-dashboard-v31-build.md
- 2026-02-02-dashboard-framework.md

### Vince / ML / Screener (16 files)
- 2026-02-28-vince-b1-scope-audit.md — B1 FourPillarsPlugin scope audit, BUILD-VINCE-B1-PLUGIN.md created
- 2026-02-28-b2-api-types-research.md — B2 API+types research, 7 bottlenecks, 4 verdicts locked
- 2026-02-28-vince-b4-scope-audit.md — B4 PnL Reversal research, 8 bottlenecks, 6 improvements
- 2026-02-28-bingx-dashboard-vince-planning.md — build order B0-B6 locked, BingX dashboard scope
- 2026-02-24-vince-todo.md
- 2026-02-24-vince-v2-ml-spec-review.md
- 2026-02-24-weex-screener-scope.md
- 2026-02-24-screener-scope.md
- 2026-02-20-vince-scope.md
- 2026-02-19-vince-scope.md
- 2026-02-19-engine-audit.md
- 2026-02-18-vince-scope-session.md
- 2026-02-18-vince-ml-build.md
- 2026-02-18-vince-ml-build-plan.md
- 2026-02-17-vince-ml-strategy-exposure-audit.md
- 2026-02-13-vince-ml-build-session.md
- 2026-02-11-vince-ml-architecture.md
- 2026-02-11-vince-ml-Session Log.md

### Pine Script / Indicators (8 files)
- 2026-02-04-quad-rotation-fast-v1.3-build.md
- 2026-02-03-quad-rotation-v4-fast-build-session.md
- 2026-02-03-quad-rotation-stochastic-spec-review.md
- 2026-02-02-ripster-volume-status-build.md
- 2026-02-02-avwap-anchor-assistant-framework.md
- 2026-02-02-atr-sl-trailing-tp-build-spec.md
- 2026-02-02-atr-sl-trailing-tp-session.md
- 2026-01-30-tradingview-indicator-development.md

### Strategy (5 files)
- 2026-02-23-four-pillars-strategy-scoping.md
- 2026-02-16-strategy-actual-implementation.md
- 2026-02-05-strategy-analysis-session.md
- 2026-02-04-four-pillars-strategy-specification.md
- 2026-01-29-strategy-refinement-session.md
- commission-rebate-analysis.md

### Infrastructure / VPS (4 files)
- 2026-02-26-vps-setup-and-autostart.md
- 2026-02-26-vps-migration-part-a-violation.md
- 2026-01-28-Jacky-VPS-Setup.md
- 2026-01-28-n8n-webhook-testing.md

### Data Pipeline (3 files)
- 2026-02-28-parquet-data-catchup.md — Bybit cache 15 days stale, added --all flag to fetch_data.py
- 2026-02-13-data-pipeline-build.md
- 2026-02-20-youtube-transcript-analyzer-build.md

### PDF Export (3 files)
- 2026-02-17-pdf-diagram-alignment.md
- 2026-02-17-pdf-export-optimization.md
- 2026-02-17-pdf-orientation-fix.md

### UML / Architecture (3 files)
- 2026-02-17-uml-diagrams-creation.md
- 2026-02-17-uml-logic-debugging.md
- 2026-02-16-trade-flow-uml.md

### Vault Maintenance (6 files)
- 2026-02-14-vault-sweep-fixes.md
- 2026-02-14-vault-sweep-manifest.json
- 2026-02-14-vault-sweep-manifest.md
- 2026-02-14-vault-sweep-review.md
- 2026-02-13-vault-sweep-manifest.json
- 2026-02-13-vault-sweep-manifest.md
- 2026-02-13-vault-sweep-review.md

### Project Reviews (7 files)
- 2026-02-17-project-clarity-and-vince-architecture.md
- 2026-02-16-full-project-review.md
- 2026-02-16-project-status-data-strategy.md
- 2026-02-14-project-flow-update.md
- 2026-02-14-operational-logic-audit.md
- 2026-02-13-full-project-review.md
- 2026-02-13-project-audit.md
- 2026-02-12-project-review-direction.md

---

## Subdirectories

| Directory | Contents |
|-----------|----------|
| `plans/` | Plan files from Claude Code plan mode |
| `plans/2026-02-28-b3-enricher-research-audit.md` | B3 enricher audit, 6 blockers, 8 open Q's |
| `plans/2026-02-28-vince-doc-sync.md` | Master build: Vince B2-B6 build docs + UML status + INDEX + TOPIC sync |
