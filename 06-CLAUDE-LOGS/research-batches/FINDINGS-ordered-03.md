# Research Batch 03 — Findings

**Batch:** 03 of 22
**Files processed:** 9
**Date range covered:** 2026-02-11 to 2026-02-13

---

## 2026-02-11-vince-ml-Session Log.md
**Date:** 2026-02-11
**Type:** Session log

### What happened
Six-hour session focused on two main activities: (1) root cause analysis of the v3.8 catastrophic strategy failure (-97% loss, $10K → $300), and (2) design of the v3.8.2 AVWAP 3-stage trailing stop replacement strategy. Additionally diagnosed and attempted to fix dashboard.py Streamlit deprecation bugs.

v3.8 root cause identified as an execution order bug in both Pine Script and Python: exit checks ran before breakeven raise logic, causing SL hits on volatile bars where price touched both the BE trigger and SL within the same bar. Python code returned "SL" immediately on line 120 before BE raise code on lines 150-158 could execute. 621 trades: 0 BE raise activations, 617 SL hits, 223 losing trades had profitable excursion.

v3.8.2 strategy designed with: AVWAP anchor at signal bar open (never moves), limit entry at ±1σ when price hits ±2σ, 3-bar limit timeout, Stage 1 SL at ±2σ, Stage 2 AVWAP±ATR trailing for 5 bars (triggered when opposite 2σ hit), Stage 3 Cloud 3 (34/50 EMA)±ATR trailing until stopped. No take profit — runner strategy. Pyramiding same direction only, each position tracks independently.

Filesystem tools (create_file, bash_tool) failed silently after session compaction — all 6 attempted file writes produced success messages but created no files on disk. Content preserved only in chat conversation.

### Decisions recorded
1. Limit timeout: 3 bars from order placement
2. AVWAP anchor: signal bar open, never moves per position
3. Stage 2 duration: exactly 5 bars
4. Stage 3 trigger: 6th bar after Stage 2 start
5. Cloud reference: Cloud 3 (34/50 EMA), not Cloud 2 (5/12)
6. Pyramiding: same direction only, independent tracking
7. No take profit — runner strategy
8. Entry at ±1σ when ±2σ is hit (not at ±2σ trigger)
9. Critical fix: update stops BEFORE checking exits

### State changes
- v3.8 root cause identified (execution order bug, both Pine Script and Python)
- v3.8.2 strategy design completed (in-chat, not saved to disk)
- dashboard_FIXED.py content generated but not saved to disk
- BUILD-v3.8.2.md spec generated but not saved to disk
- 0 files created on disk due to filesystem tool bug

### Open items recorded
- Save BUILD-v3.8.2.md manually from chat content
- Apply dashboard fixes to dashboard.py manually
- Fix position.py execution order
- Execute BUILD in Claude Code to create 4 Pine Script/doc files
- Monitor GitHub Issue #4462 for filesystem bug

### Notes
- Filesystem write bug confirmed on both Windows and Mac (GitHub Issue #4462, open since July 2024; duplicate Issue #5505 closed). Triggered by session compaction in long conversations.
- Dashboard fix refers to `trading-tools/scripts/dashboard.py` (older path, not `PROJECTS/four-pillars-backtester/scripts/dashboard.py`).

---

## 2026-02-11-WEEK-2-MILESTONE.md
**Date:** 2026-02-11
**Type:** Planning / Milestone summary

### What happened
Week 2 milestone summary covering 2026-02-05 to 2026-02-11. Documents completed work across Pine Script, ML/VINCE pipeline, infrastructure, and documentation. Lists bugs discovered and remaining work scoped across immediate, short-term, and medium-term horizons.

Completed: v3.8 built and failure-analyzed, v3.8.2 designed and built (4 Pine Script files: indicator 16.8KB + strategy 43.6KB + logic doc + changelog), ML pipeline tests passing in 15 seconds, VINCE architecture documented, VPS "Jacky" operational in Jakarta timezone, n8n workflows running, 399 coins cached (1.74GB, 1m + 5m), grid bots profitable on RIVERUSDT/GUNUSDT/AXSUSDT generating >$1,000. Open builds: 11 builds remain in master build queue.

### Decisions recorded
None explicitly — milestone summary only.

### State changes
- 4 Pine Script files for v3.8.2 confirmed created (16.8KB indicator, 43.6KB strategy, complete logic doc, changelog)
- 399 coins cached in Parquet, 1.74GB
- Grid bots running on RIVERUSDT, GUNUSDT, AXSUSDT with >$1,000 profit
- PyTorch blocked on RTX 3060 (GPU training deferred)
- 5-tab ML dashboard in staging, not deployed

### Open items recorded
1. Test v3.8.2 on TradingView (UNIUSDT 2m)
2. Git push v3.8.2
3. Apply dashboard fixes (Streamlit + PyArrow)
4. Deploy 5-tab ML dashboard from staging to scripts
5. Run v3.8.2 backtest sweep on 399 coins
6. Fix PyTorch GPU installation on RTX 3060
7. Train VINCE XGBoost model on v3.8.2 backtest results
8. SHAP analysis
9-12. Longer-term: WEEX API integration, grid bot optimization, Cloud 4 trail research, daily VINCE training

### Notes
- Milestone confirms that v3.8.2 Pine Script files WERE successfully created (4 files, sizes documented), contradicting the session log's report that 0 files were created. The session log states the filesystem tool bug caused silent write failures; the milestone summary says "4 Pine Script files created." This contradiction is unresolved in the logs — either the milestone was written from a different context (new conversation, pre-compaction), or the files were created manually by the user.
- Gap in session logs noted: Feb 6-10 due to filesystem tool bug.

---

## 2026-02-12.md
**Date:** 2026-02-12
**Type:** Build session (multi-session)

### What happened
Four sessions on 2026-02-12:

**Session 1 (~1 hour):** Bybit fetcher rate limit fix (changed _fetch_page to return tuple with rate_limited flag, exponential backoff retry). Download speed increased 20x (rate limit changed from 1.0s to 0.05s per Bybit docs of 600 req/5s). Sanity check script created (categories: COMPLETE/PARTIAL/NEW_LISTING). Download retry mode added (--retry flag reads _retry_symbols.txt). Data collection declared COMPLETE: 399 coins, 124.8M bars, ~6.2GB, 0 quality issues. Git pushed to GitHub (initialized git in backtester dir, merged with remote, committed 148 Python + 28 Pine Script files). Memory files moved to Obsidian Vault. MEMORY.md updated (70% chat limit rule added, Data Collection Status, Git Setup, Pending Builds P1-P5).

**Session 2 (~2 sessions):** Major dashboard overhaul. 7 tasks:
- data/normalizer.py (NEW, ~370L): universal OHLCV CSV-to-parquet normalizer, 6 exchange formats, auto-detect delimiter/columns/timestamps/interval
- scripts/convert_csv.py (NEW, ~150L): CLI wrapper for normalizer
- scripts/dashboard.py (EDIT): mode navigation (settings|single|sweep|sweep_detail), sweep persistence (CSV with params_hash), non-blocking sweep (1 coin per rerun), drill-down view
- scripts/test_normalizer.py (NEW, ~450L, 17 tests)
- scripts/test_sweep.py (NEW, ~300L, 11 tests)

**Session 3 (~30 min):** Bug fixes in normalizer (ts_ms undefined, "1D" resample deprecation) and test expectation fix. All 84 tests passing (47+37).

**Session 4 (~15 min):** Scoped P1-P5 pending builds. P1 conflict detected: staging/dashboard.py is stale (pre-Session 2), deploying it would overwrite all Session 2 work. Recommendation: deploy only live_pipeline.py from staging, skip rest. Recommended build order: P2 > P3 > P4 > P1(live_pipeline only) > P5.

### Decisions recorded
1. Git repo initialized in PROJECTS/four-pillars-backtester/ (not Desktop/ni9htw4lker which was empty clone)
2. Git identity: S23Web3 / malik@shortcut23.com (repo-local config)
3. .gitignore excludes: data/cache/, data/historical/, .env, __pycache__, *.meta, nul
4. Sweep is non-blocking (1 coin per st.rerun() cycle)
5. Auto-resume from CSV (no manual Resume button)
6. Normalizer output must match fetcher.py schema (same parquet schema, same .meta format)
7. P1 staging deploy: only live_pipeline.py, skip stale dashboard
8. Build order: P2 > P3 > P4 > P1(live_pipeline) > P5
9. 70% chat limit rule added to MEMORY.md

### State changes
- data/fetcher.py: rate limit retry logic added
- scripts/download_1year_gap_FIXED.py: 0.05s rate, --retry mode
- scripts/sanity_check_cache.py: NEW
- data/normalizer.py: NEW (~370L)
- scripts/convert_csv.py: NEW (~150L)
- scripts/test_normalizer.py: NEW (~450L)
- scripts/test_sweep.py: NEW (~300L)
- scripts/dashboard.py: EDITED (~1450L, was 1129L)
- 84/84 tests passing
- Git repo pushed to GitHub (148 Python + 28 Pine Script files)

### Open items recorded
- User must run: python scripts/build_staging.py, python staging/test_dashboard_ml.py
- P1-P5 builds scoped but not executed

### Notes
- MEMORY.md 70% chat limit rule added this session — first appearance of this rule.
- data/normalizer.py verified on disk (Glob confirmed: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\normalizer.py exists).

---

## 2026-02-12-project-review-direction.md
**Date:** 2026-02-12
**Type:** Strategy spec / Analysis

### What happened
Deep analysis of v3.8.4 current state and strategic direction for ML architecture. Identifies a fundamental math problem: R:R ratio is inverted (TP=2.0 ATR, SL=2.5 ATR → R:R=0.8, breakeven WR=55.6%, actual WR=40%). System profit is driven by rebates masking a negative raw edge.

Critical bug identified: position_v384.py has zero breakeven raise logic — both close_at() and do_scale_out() hardcode be_raised=False. BE raise was present in position.py (v3.7.x) but dropped during v3.8.x refactor.

Key metrics for v3.8.4 on 3 coins (RIVER/KITE/BERA): 6,269 total trades, ~40% WR, $13,872 net+rebate, $2.21/trade, $6,138 MaxDD (35.3%), config $10K account/$5K notional/20x leverage/SL=2.5ATR/TP=2.0ATR/70% rebate.

ML architecture reframed: current 9 ML modules are entry filters (meta-labeling), but the correct approach is ML on exits, not entries. Three proposed modules: RFE Predictor (XGBoost regression on remaining favorable excursion), Regime Classifier (trending/ranging/volatile), optional Bet Sizing. Constraint: every valid signal must still enter (volume is the business model).

Priority execution order defined: Phase 1 (immediate) = add BE raise, fix R:R. Phase 2 (1 week) = multi-tier exits (25% at 1/2/3 ATR). Phase 3 (2 weeks) = ML exit optimization. Phase 4 (3 weeks) = regime awareness.

### Decisions recorded
1. BE raise must be added back to position_v384.py (trigger at 0.75 ATR profit, lock at 0.1 ATR above entry)
2. R:R fix: test TP=3.0 ATR with SL=2.5 ATR (R:R=1.2)
3. ML focus: exits not entries — RFE Predictor + Regime Classifier + optional Bet Sizing
4. "Never take fewer trades" constraint = volume is the business model
5. What NOT to build: entry filters (meta-labeling that skips trades), complex neural networks, overfitted per-coin parameters, Bayesian optimization on SL/TP alone

### State changes
- No code built in this session — analysis and direction document only
- v3.8.4 confirmed to have zero BE raise logic (critical finding)

### Open items recorded
- Add BE raise to position_v384.py
- Test TP=3.0 ATR vs current TP=2.0 ATR
- Run capital_analysis_v384 with BE raise + R:R fix
- Build tiered scale-out (Phase 2)
- Build RFE dataset from existing MFE data (Phase 3)
- Implement real-time RFE scoring in backtester loop

### Notes
- This document contradicts the previous ML direction (meta-labeling / entry filtering) and explicitly reframes the ML goal as exit optimization. This is a significant strategic pivot.
- Conflict with 2026-02-13-vince-ml-build-session.md: that session's BUILD-VINCE-ML.md still includes XGBoost meta-label for D/R grades (entry filtering), suggesting the pivot in this doc was not fully carried through in the next build spec.

---

## 2026-02-13.md
**Date:** 2026-02-13
**Type:** Build session (multi-session)

### What happened
Two sessions building a 3-year historical data infrastructure.

**Session 1 (~12:00):** 9 files created for the four-pillars-backtester project. Bybit historical OHLCV downloader (scripts/download_periods.py) for 2023-2024 and 2024-2025 periods. CoinGecko comprehensive fetcher (fetch_coingecko_v2.py, 5 actions). ML features expanded: features_v2.py with 26 features (14 original + 8 volume + 4 market cap). Data period loader (data/period_loader.py). Test suites: 111/111 tests pass across 4 test files.

Verified downloads: BTC/ETH/SOL from Bybit 2024-2025 = 1.58M bars, 62.3 MB, 7.1 min. CoinGecko 3-coin test: 10 API calls, 0 errors, 6 seconds.

CoinGecko API key added to .env (Analyst plan, 1000 req/min, expires 2026-03-03).

Data organization: data/cache/ untouched (existing 6.2GB), data/periods/2023-2024/ and 2024-2025/ (new), data/coingecko/ (new, 5 output files).

**Session 2 (~14:00):** CoinGecko full run completed (792 API calls, 0 errors, 10 min, 394/394 coins OK). download_periods_v2.py built with --all flag (chains both periods), --yes flag (skip confirm), CoinGecko smart filtering (skips coins not listed before period end). New MEMORY standard established: ALL FUNCTIONS MUST HAVE DOCSTRINGS.

### Decisions recorded
1. CoinGecko Analyst plan API key stored in .env
2. Period data stored in data/periods/ (not mixed with existing data/cache/)
3. v2 downloader uses CoinGecko smart filtering to skip coins not listed in period
4. ALL FUNCTIONS MUST HAVE DOCSTRINGS — new hard rule added to MEMORY

### State changes
- scripts/download_periods.py: NEW
- scripts/fetch_coingecko_v2.py: NEW
- scripts/fetch_market_caps.py: NEW (superseded by v2)
- ml/features_v2.py: NEW (26 features)
- data/period_loader.py: NEW
- scripts/test_download_periods.py: NEW (17/17 pass)
- scripts/test_fetch_market_caps.py: NEW (20/20 pass)
- scripts/test_features_v2.py: NEW (56/56 pass)
- scripts/test_period_loader.py: NEW (18/18 pass)
- scripts/download_periods_v2.py: NEW
- scripts/test_download_periods_v2.py: NEW
- CoinGecko full run complete: 5 output files (5.1MB history, 28.3KB global, 152.4KB categories, 638KB metadata, 23.1KB movers)

### Open items recorded
- Bybit 2023-2024 full download (~2.5 hours for ~399 coins)
- Bybit 2024-2025 full download (~4.5 hours for ~399 coins)
- features_v2.py market cap join to CoinGecko data not yet built
- period_loader.py not yet integrated with backtester for 3-year backtests

### Notes
- ml/features_v2.py verified on disk (Glob confirmed).
- scripts/download_periods_v2.py verified on disk (Glob confirmed).
- CoinGecko API key expires 2026-03-03 — this is relevant given the research date of 2026-03-05 (key may have expired).

---

## 2026-02-13-full-project-review.md
**Date:** 2026-02-13
**Type:** Planning / Project review

### What happened
Evening project review session covering 8 sections: Claude Code build status, VINCE-FLOW.md mermaid update status, data pipeline status, BBWP update, PyTorch build scope, Saturday schedule, and chat summary log for Feb 10-13.

At time of writing, Claude Code (Session 6 of the day) was running build_all_specs.py to generate 9 files from Specs A, B, C — including backtester_v385.py, dashboard_v3.py, and 4 ML modules.

Data pipeline status: CoinGecko complete, Bybit recent cache complete (399 coins, 6.2GB, updated with +8085 bars), Bybit 2023-2024 at 14% (55 of ~280 coins, stopped at DODO alphabetically), Bybit 2024-2025 at 1% (3 coins only).

BBWP Pine Script files exist (v2, 233 lines; Caretaker v6). Python BBWP port does not exist. Build spec for BBWP lost to filesystem bug. BBWP 6-state logic documented: BLUE DOUBLE (bbwp≤10%), BLUE (bbwp<25%), MA CROSS UP, MA CROSS DOWN, NORMAL (25-75%), RED (bbwp>75%), RED DOUBLE (bbwp≥90%).

PyTorch confirmed installed (2.10.0+cu130, RTX 3060 12GB available). Three-phase ML build: Phase 1 tabular (25 features, MLP, blocked on Spec B), Phase 2 LSTM sequences (blocked on Phase 1 + --save-bars flag), Phase 3 live integration (blocked on Phase 2 accuracy).

Saturday schedule planned in Jakarta timezone (UTC+7) for 09:00-17:30.

VINCE-FLOW.md flagged as outdated — shows 5-tab dashboard, missing CoinGecko pipeline, missing historical period downloads, missing 3-spec dependency chain.

### Decisions recorded
1. Saturday action plan defined (verify builds, start data downloads, test dashboard, build BBWP port, update mermaid)
2. BBWP Python port spec: signals/bbwp.py, ~150L, params: basis_len=13, lookback=100, bbwp_ma_len=5, etc.
3. Saturday data download commands established

### State changes
- VINCE-FLOW.md identified as outdated (no update yet)
- Claude Code running build_all_specs.py (generating 9 files) at time of writing
- Bybit 2023-2024 download interrupted at 14% (55 coins, A-D)

### Open items recorded
1. Verify Claude Code build_all_specs.py completion
2. Run test_v385.py + test_dashboard_v3.py + test_vince_ml.py
3. Start 2023-2024 period download (remaining ~225 coins)
4. Start 2024-2025 period download (396 coins remaining)
5. Build signals/bbwp.py Python port (~2 hours)
6. Update VINCE-FLOW.md to match 3-spec architecture
7. Run full 399-coin sweep on dashboard v3
8. BBWP: confirm build per Section 4 spec?
9. Join CoinGecko data → features (not yet built)
10. period_loader.py integration with backtester (not yet built)

### Notes
- Confirms PyTorch 2.10.0+cu130 is installed and RTX 3060 12GB operational — resolves earlier blocker status from Week 2 Milestone.
- Mentions 11 components not yet built in Layer 4-6 (ML and live execution).

---

## 2026-02-13-project-audit.md
**Date:** 2026-02-13
**Type:** Audit

### What happened
Comprehensive project audit documenting the state of all 7 layers of the system: Data (complete), Strategy/Python backtester (complete, v3.8.4), Dashboard (complete but not fully tested), ML XGBoost (built but not wired — no orchestration, no trained models), ML PyTorch (spec only, zero code), Live Execution (not built), Pine Script (built but not validated against Python).

System described as building toward three personas: Vince (rebate farming on BingX/WEEX/Bybit), Vicky (copy trading, 55%+ WR needed), Andy (FTMO prop trading, 10%/month).

End state goal: TradingView webhook → n8n → exchange API → Vince monitor → dashboard.

Current blockers identified: ML not wired, staging dashboard stale, PyTorch+CUDA not installed (contradicts full-project-review which says PyTorch installed), n8n webhook 404, tests not run, no trained models.

Pending build queue (9 items, P1-B4) with priority order, effort, dependencies, and impact documented.

Codebase stats: 9 engine files, 7 signals files, 10 ML modules, 46 scripts, 6 strategies, 9 results files, 4 staging files, 0 model files, 2 Pine Script files. 176 git-tracked files total.

### Decisions recorded
None beyond what was already established — audit only.

### State changes
- No code built — audit document only
- Confirmed: models/ directory does not exist
- Confirmed: ml/live_pipeline.py still in staging/, not deployed

### Open items recorded
- All items from pending build queue P1-B4
- Fix n8n webhook 404 on VPS Jacky
- Deploy live_pipeline.py to ml/ (P1)
- Build train_vince.py orchestrator (P2)
- Multi-coin portfolio optimization (P3)
- 400-coin ML sweep (P4)
- TradingView validation (P5)
- 24/7 executor framework (P6)
- Dashboard UI/UX research (P7)
- PyTorch TradeTrajectoryNetwork (B3)
- Dashboard v2 ML tab wiring (B4)

### Notes
- States "PyTorch + CUDA not installed" as a current blocker — contradicts 2026-02-13-full-project-review.md which says "PyTorch 2.10.0+cu130 installed" and RTX 3060 available. One of these two same-day documents has a stale status. The project-review section is more detailed and appears to have been written later in the day.

---

## 2026-02-13-data-pipeline-build.md
**Date:** 2026-02-13
**Type:** Build session

### What happened
Concise session log summarizing the data pipeline build work, largely duplicating content from 2026-02-13.md (Session 1 and Session 2). Covers the same 9 files created, same test results (111/111 pass), same CoinGecko API key details, same verified download numbers, and same run commands. Session 2 summary covers CoinGecko full run completion and download_periods_v2.py build.

Adds one specific detail not in the main journal: CoinGecko API key prefix shown as `CG-DewaU1...`.

### Decisions recorded
Same as 2026-02-13.md — ALL FUNCTIONS MUST HAVE DOCSTRINGS standard added.

### State changes
Same as 2026-02-13.md — 9 files created, 111/111 tests passing, CoinGecko full run complete.

### Open items recorded
Same as 2026-02-13.md — full period downloads pending.

### Notes
- This file is a duplicate/condensed version of 2026-02-13.md sessions 1 and 2. No new information beyond the API key prefix fragment `CG-DewaU1...`.

---

## 2026-02-13-vince-ml-build-session.md
**Date:** 2026-02-13
**Type:** Build session

### What happened
~45 minute session, hit 70% context limit. Primary purpose was to audit state of the VINCE ML build and write the BUILD-VINCE-ML.md specification document.

Steps: Identified pending build from previous chat (BUILD-NORMALIZER-3PHASE.md spec). Verified normalizer build was already complete (all files exist on disk, dashboard.py updated 19:50 Feb 12). Audited ml/ directory: 9 modules exist, 0 trained models, no models/ directory, no train_vince.py orchestrator, live_pipeline.py still in staging only.

Reviewed screenshot showing v3.8.4 sweep results: 399 coins, 95% profitable, $9.52M net, $4.19 avg expectancy, 2.81M trades (SL=3.0, TP=2.5, $10K per coin, MaxPos=4).

User decision on BE raise: BE raise affects AVWAP runners (tradeoff). Not a blind restore. BE raise v3.8.5 blocked on VINCE training — VINCE must evaluate the tradeoff first.

Wrote BUILD-VINCE-ML.md covering: P1 (deploy staging), P2+B2 (XGBoost training pipeline), P4 (400-coin sweep), B3 (PyTorch TTN), B4 (dashboard integration).

Filesystem MCP config note: user needs to add .claude to allowed directories in claude_desktop_config.json.

### Decisions recorded
1. BE raise (v3.8.5) is BLOCKED on VINCE training — VINCE evaluates the tradeoff
2. Normalizer / Session 2 builds already complete — BUILD-NORMALIZER-3PHASE.md is redundant
3. Permissions confirmed by user: write new files, read existing, versioned dashboard edit

### State changes
- BUILD-VINCE-ML.md: NEW (saved to PROJECTS/four-pillars-backtester/)
- BUILD-NORMALIZER-3PHASE.md: NEW (redundant, saved for reference)
- 2026-02-13-vince-ml-build-session.md: NEW (this log file)

### Open items recorded
1. Add .claude to filesystem MCP config
2. Run P1 deploy staging commands (terminal only)
3. Run pending tests: test_normalizer.py, test_sweep.py
4. Build from BUILD-VINCE-ML.md (P2+B2 first)
5. Cross-reference vault builds vs logs vs chats (ran out of context, not done)

### Notes
- BUILD-VINCE-ML.md verified on disk (Glob confirmed: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-ML.md exists).
- Screenshot data (95% profitable, $9.52M net on 399 coins, SL=3.0/TP=2.5) is notable — this is a significantly better result than the v3.8.4 3-coin result of $13,872 net. Different params (SL=3.0/TP=2.5 vs SL=2.5/TP=2.0) and broader coin set.
- The BE raise decision (blocked on VINCE training) partially contradicts 2026-02-12-project-review-direction.md which set BE raise as "Phase 1 immediate" — the user imposed a new constraint that BE raise evaluation requires ML first.
