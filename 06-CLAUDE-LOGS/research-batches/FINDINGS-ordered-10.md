# Research Batch 10 — Findings
**Files processed:** 10
**Batch date:** 2026-03-05 (research execution date)

---

## 2026-03-03-ttp-integration-plan.md
**Date:** 2026-03-03
**Type:** Planning session

### What happened
Planning and audit session for integrating TTP (Trailing Take Profit) engine into the BingX connector and dashboard. Read handoff context from previous session (dashboard v1.4 patch2 applied). Read TTP spec, build brief, and draft ttp_engine.py code. Confirmed NO TTP logic existed anywhere in the connector yet. Clarified with user that TTP = display-only on dashboard + toggle on/off + wired into live bot. Initial plan using mark price approach written, then full audit found 5 critical gaps. Plan revised to hybrid architecture. Verified 5 "pre-existing bugs" in executor.py and state_manager.py — all were agent transcription errors, actual code was correct.

### Decisions recorded
1. TTP evaluates on real 1m OHLC in market_loop thread (signal_engine.py), close orders execute in monitor_loop thread (position_monitor.py). `ttp_close_pending` flag in state.json bridges the two threads.
2. Five critical plan gaps identified and resolved: mark price H=L issue, activation price gap bug, race condition guard, need for `_place_market_close()`, need for `_cancel_all_orders_for_symbol()`.
3. 7 files to be touched in next session build.

### State changes
- Plan written to `C:\Users\User\.claude\plans\cuddly-dancing-perlis.md` and vault copy `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-dashboard-v1-4-patch3-ttp-display.md`
- No code written this session — plan only

### Open items recorded
- Build `scripts/build_ttp_integration.py`
- Build `scripts/build_dashboard_v1_4_patch3.py`
- Run both scripts and tests
- ttp_engine.py source code (user-provided draft) had 4 bugs to fix: self.state never CLOSED, CLOSED_PARTIAL state, iterrows(), band_width_pct guard
- ttp_engine.py not yet saved to a file — must be re-pasted or retrieved in next session

### Notes
None.

---

## 2026-03-04-bingx-v1-5-full-audit-upgrade.md
**Date:** 2026-03-04
**Type:** Build session (multi-phase)

### What happened
Major 4-phase build session triggered by live bot running 12+ hours with multiple observed issues. Issues included TTP close orders failing (error 109400 — infinite retry loops), Close Market button broken (signature error 100001), equity curve mixing all sessions, coin summary date filter disconnected, EXIT_UNKNOWN exits, no TTP activation tracking in trades.csv, bot OFFLINE paradox, and $5/10x underperforming.

Phase 1: Built 6 diagnostic scripts (error audit, variable web, TTP audit, ticker collector, demo order verify, trade analysis). All py_compile PASS.

Phase 2: Bot core fixes — removed `reduceOnly` from `_place_market_close()` (root cause of 109400), added SL tightening after TTP activation, added TTP columns to trades.csv, updated config.yaml and main.py.

Phase 3: Dashboard v1.5 built from v1.4 base — 17 patches including signing fix (100001), reduceOnly removal from 3 callbacks, session equity filter, coin summary date wiring, dual bot/exchange status, TTP stats panel, trade chart popup modal with klines/stochastic/BBW.

Phase 4: Beta bot built — config_beta.yaml (44 coins, $5/20x), main_beta.py with overlap guard checking live state.json at startup.

Phase 1 was run and produced real data: 15,399 total error lines, 7,650 TTP_CLOSE_FAIL, win rate 8.3% (230 trades), net PnL -$825.24, LSG% 75.8%, EXIT_UNKNOWN 43% of all exits.

An audit fixes build (`build_audit_fixes.py`) applied 5 additional patches: duplicate function removal, NameError fix in signal_engine.py, reconcile() phantom close fix, input() blocking call removal, session_start refresh.

### Decisions recorded
1. BUG-1 root cause confirmed: `"reduceOnly": "true"` is invalid in Hedge mode on BingX — this caused 7,650 failed TTP closes (50% of all log entries).
2. Grade A worse than Grade B (3.3% vs 10.1% WR) — signal quality investigation needed.
3. LSG 75.8% + Avg MFE 0.937% suggests TP at 0.5-0.7% would capture most winners.
4. Beta bot needs overlaps removed before starting: LYN, GIGGLE, BEAT, TRUTH, STBL, BREV, Q, SKR, MUS.
5. Three audit items deferred for design discussion: H1 (BE/TTP coupling), H2 (exit price from state not fill), M1 (CSV header race), M2 (API rate limit batching), M3 (SL cancel-before-place race).

### State changes
- `scripts/build_phase1_diagnostics.py` — CREATED, py_compile PASS
- 6 diagnostic scripts created by phase 1 build
- `scripts/build_phase2_bot_fixes.py` — CREATED, BUILD OK
- `position_monitor.py` — PATCHED (reduceOnly removed + SL tighten added)
- `state_manager.py` — PATCHED (TTP columns added)
- `config.yaml` — PATCHED (sl_trail_pct_post_ttp: 0.003 added)
- `main.py` — PATCHED (check_ttp_sl_tighten wired in)
- `scripts/build_dashboard_v1_5.py` — CREATED, BUILD OK
- `bingx-live-dashboard-v1-5.py` — CREATED, py_compile + ast.parse PASS
- `scripts/build_phase4_beta_bot.py` — CREATED, BUILD OK
- `config_beta.yaml` — CREATED (44 coins, 20x leverage, $5 margin)
- `main_beta.py` — CREATED
- `beta/` and `beta/logs/` directories — CREATED
- `scripts/build_audit_fixes.py` — CREATED, BUILD OK, all 5 patches applied
- Phase 2 patches found to be ALREADY APPLIED from prior session (MISSING ANCHOR for P2-A and P2-B)

### Open items recorded
- Restart bot after patches
- Launch dashboard v1.5 and test Close Market + session equity curve
- Remove confirmed overlaps from config_beta.yaml then start main_beta.py
- Backtester TP sweep at 0.5-1.0x ATR range (LSG data supports tight TP hypothesis)

### Notes
- Phase 2 build script showed MISSING ANCHOR for P2-A and P2-B — both patches were already applied in a prior session (confirmed by reading actual files). This is a recurring pattern where prior sessions applied fixes not captured in earlier logs.
- The 109400 error is multi-cause: reduceOnly (fixed) AND timestamp drift (discovered 2026-03-05).

---

## 2026-03-04-position-management-study.md
**Date:** 2026-03-04
**Type:** Research/strategy session

### What happened
Research session documenting user's actual position management rules from live chart walkthroughs. Continuation of a previous session analyzing PUMPUSDT LONG and PIPPINUSDT SHORT trades. Focus was on trend-hold trades only (not quick rotations, 1min scalps, counter-trend). 5 of 13 open questions resolved this session. Charts reviewed: PUMPUSDT 4h (Bybit Spot) and PUMPUSDT 1h (Bybit Spot).

Two new trade type concepts documented: 1m EMA-Delta Scalp Concept (EMA delta threshold + stoch zone entry + TDI MA cross, fully automatable) and Probability-Based Trade Framework (Markov + Black-Scholes — replace hard thresholds with learned transition probabilities, 75 combined states, BBWP-to-BS bridge).

### Decisions recorded
1. HTF-1 resolved: 4h session bias determined by Ripster EMA cloud stack transitions; 1h confirmed by sequential cloud flips (Cloud 2 first, then 3, then 4) converging at structural level.
2. HTF-2 resolved: 15m MTF clouds NOT a hard binary filter — modulates hold duration, not entry permission.
3. ENTRY-1 resolved: All 4 stochastics confirm sequentially — enter when LAST stoch completes K/D cross.
4. BBW-1 resolved: Exact BBWP thresholds unknown — flagged for Vince to research via backtesting.
5. TDI-1 resolved: RSI period=9, RSI price smoothing=5, Signal line=10, Bollinger band period=34.
6. No code to be written until all questions resolved and user approves rules.

### State changes
- Study plan file updated: `C:\Users\User\.claude\plans\fizzy-humming-crab.md`
- Two concept plan files created: `2026-03-04-1m-ema-delta-scalp-concept.md` and `2026-03-04-probability-trade-framework.md`
- RULE VIOLATION recorded: `2026-03-04-markov-trade-state-research.md` was deleted without asking user. Content preserved in `2026-03-04-probability-trade-framework.md` but deletion was unauthorized.

### Open items recorded
- 7 questions still open: SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1, TP-1
- Next: resolve GATE-1 on PUMP first (user indicated this priority)

### Notes
- Rule violation logged in the file itself — unauthorized file deletion. This is the only session log reviewed so far that documents a rule violation in the session log (most violations are noted in MEMORY.md).

---

## 2026-03-05-bingx-bot-session.md
**Date:** 2026-03-05
**Type:** Build session + live bot monitoring

### What happened
Continuation from 2026-03-04 audit + patch session. Bot restarted with all fixes applied. Multiple significant events and builds:

1. Three-stage position management implemented: `be_act: 0.004` (BE raises at +0.4%), `ttp_act: 0.008` (TTP at +0.8%), `ttp_dist: 0.003` (trail 0.3%). Test script: 25/25 PASS.

2. orderId extraction bug fixed in 3 locations in position_monitor.py — was missing nested `order` key.

3. Unrealized PnL added to Telegram daily summary and hourly warnings.

4. max_positions increased from 15 to 25 via config.yaml.

5. Log review of 2026-03-04-bot.log (11,466 lines, 953KB) showed DNS outage at 13:15 (30+ CRITICAL alerts, self-recovered), several trades opened and closed.

6. Time Sync Fix (evening): Discovered bot and dashboard used raw `time.time() * 1000` without server sync. BingX rejects timestamps drifting >5 seconds (error 109400). User lost 17% due to this. Immediate fix: `w32tm /resync /force`. Permanent fix: `build_time_sync.py` creates `time_sync.py` module + patches 5 files (bingx_auth.py, main.py, executor.py, position_monitor.py, bingx-live-dashboard-v1-4.py).

7. Trade Analyzer v2 built (11 analysis sections, 3 output formats). Initial build had bugs fixed directly (CSV schema mismatch, ModuleNotFoundError dotenv, date filter). Build script SOURCE is now out of sync with output file.

8. ATR Investigation built and run — found 4 HIGH_VOL+ trades (atr_ratio > 1%) caused 66% of non-BE losses. Risk gate has no upper bound. Three recommended fixes: max_atr_ratio cap at 0.015, ATR-scaled position sizing, sl_atr_mult reduction from 2.0 to 1.5.

9. Trade Analyzer v2 results (57 trades, 2026-03-04 to 2026-03-05): 57.9% WR, net PnL -$0.694, post-rebate +$2.50. BE raised backbone (71.1% WR), TTP exits profit engine (+$9.59). Without BE+TTP, bot deeply negative.

10. Scaling analysis for $500 margin / 20x / $10k portfolio: 200x scale factor. Net +$500/57 trades post-rebate. Critical risk: Q-USDT (5.15% SL) would be liquidated before SL hits at 20x.

11. Dashboard v1.5 full debug chain (evening): Fixed store-bot-status KeyError, full line-by-line audit found 4 bugs (BUG-A through BUG-D), signing fix (100001 root cause: requests library re-encoding params), trades CSV loading fix (18-column bot vs 12-column header mismatch), Max DD % fix written (not yet run).

### Decisions recorded
1. Timestamp sync is root cause of many 109400 errors — permanent fix via time_sync.py module.
2. Three-stage position management adopted (BE at 0.4%, TTP at 0.8%, trail 0.3%).
3. max_atr_ratio cap recommended at 0.015 to block extreme-volatility entries.
4. Dashboard v1.5 signing must use manual URL-build approach (match bot's bingx_auth.py pattern), not requests.get() with params dict.
5. BE SL direction bug for SHORT noted but needs verification.
6. Dashboard v1-4 settings save does not write `be_act` — do NOT save settings from v1-4 until v1.5 fixes this.

### State changes
- `config.yaml` patched: be_act, ttp_act, ttp_dist, max_positions
- `position_monitor.py` patched: orderId extraction (3 locations), unrealized PnL method, three-stage logic
- `signal_engine.py` patched: fallback defaults updated
- `time_sync.py` CREATED
- `bingx_auth.py`, `main.py`, `executor.py`, `position_monitor.py`, `bingx-live-dashboard-v1-4.py` all patched with .bak backups
- `scripts/build_time_sync.py` CREATED
- `scripts/test_three_stage_logic.py` CREATED (25/25 PASS)
- `scripts/build_trade_analyzer_v2.py` CREATED
- `scripts/run_trade_analysis_v2.py` CREATED
- `scripts/build_atr_investigation.py` CREATED
- `scripts/run_atr_investigation.py` CREATED
- `scripts/build_dashboard_v1_5_full_audit_fix.py` CREATED (8 patches)
- `scripts/build_dashboard_v1_5_signing_fix.py` CREATED
- `scripts/build_dashboard_v1_5_trades_refresh.py` CREATED
- `scripts/build_dashboard_v1_5_drawdown_fix.py` CREATED (not yet run)

### Open items recorded
- P1: dashboard_v395.py — add require_stage2 checkbox, rot_level slider, "Load v384 Live Preset" button
- P2: BE SL direction bug for SHORT needs verification
- Dashboard v1.5 Max DD % fix pending (script written, not run)
- Bot restart required to activate time_sync.py patches
- Beta bot still needs overlap removal before starting

### Notes
- 109400 error has TWO root causes: (1) reduceOnly in Hedge mode (fixed 2026-03-04), (2) timestamp drift (fixed 2026-03-05). Prior logs attributed all 109400 to reduceOnly — this is now corrected.
- Trade Analyzer v2 build script SOURCE is out of sync with output file (3 fixes applied directly to output).
- Dashboard v1.5 was built before time_sync was added — BUG-A in the full audit found this gap.

---

## 2026-03-05-bingx-data-fetcher-and-updater.md
**Date:** 2026-03-05
**Type:** Build session

### What happened
Continued from 2026-03-04 session. Built BingX OHLCV bulk fetcher, daily incremental updater, and autorun scheduler for the four-pillars-backtester project.

BingX OHLCV Bulk Fetcher (`fetch_bingx_ohlcv.py`): Discovers all BingX USDT perpetual futures (~626 coins), fetches 1m OHLCV going back 12 months per coin, saves to `data/bingx/` as parquet + .meta, also resamples to 5m. Schema matches Bybit data (8 columns). Progress bars: outer (coins, fractional) + inner (per-coin %). CLI flags: --dry-run, --symbol, --max-coins, --months, --skip-existing, --output-dir, --resume-from. 6 bugs fixed from audit. Progress bar fix: outer bar was stuck at 0/626 — fixed with fractional advancement via `_update_outer()`.

BingX Daily Updater (`daily_bingx_update.py`): Imports functions from fetch_bingx_ohlcv.py (zero code duplication), reads .meta files, fetches only the gap, discovers new coins, skips coins less than 2 hours behind. CLI: --dry-run, --skip-new, --skip-resample, --max-new, --months. Logs to dated log file.

Autorun Scheduler (`data_scheduler.py`): Runs Bybit and BingX daily updaters on timed schedule (default 6h). CLI: --interval, --bingx-only, --bybit-only, --once. Designed to run in background terminal.

### Decisions recorded
1. BingX data stored in `data/bingx/` — separate from Bybit's `data/cache/`.
2. Zero code duplication — daily updater imports fetch functions, doesn't duplicate them.
3. quote_vol = NaN for BingX (API doesn't provide turnover).

### State changes
- `scripts/build_fetch_bingx.py` — UPDATED (progress bar, bug fixes, tqdm import)
- `scripts/fetch_bingx_ohlcv.py` — UPDATED (fractional outer bar, all bug fixes)
- `scripts/build_daily_bingx_updater.py` — NEW
- `scripts/daily_bingx_update.py` — created by build script
- `scripts/build_data_scheduler.py` — NEW
- `scripts/data_scheduler.py` — created by build script
- Data status: Bybit 399 coins (stale since 2026-02-13), BingX ~292 of 626 completed as of session start

### Open items recorded
- Bulk fetch still in progress (~292 of 626 completed) — expected ~52 hours total
- Bybit data stale since 2026-02-13 — daily updater also applies to Bybit

### Notes
- BingX OHLCV fetcher was started in 2026-03-04 session; progress bar fixes were applied in this 2026-03-05 session.

---

## 2026-03-05-project-review-volume-uml.md
**Date:** 2026-03-05
**Type:** Session log (review/documentation)

### What happened
Project review session. Read INDEX.md, key log files, and UML files. Read full trades.csv (300+ rows) for volume analysis. Produced full project brief and volume/rebate analysis for $10k/$500/20x scenario. Updated UML file.

UML update to `uml/strategy-system-flow.md` (updated from 2026-02-16 to 2026-03-05): State machine updated (C signal removed, v386 2026-02-28), dashboard updated (v3.9.4, CUDA GPU Sweep), ExitManager annotated as likely dead code, new Page 1b (BingX live bot system diagram), ML training/validation chains updated with blockers, new Page 3 (Vince ML build chain B1-B6), new Page 4 (signal architecture post-rename).

Volume analysis: $50 margin, 10x leverage = $500 notional/trade. ~70 trades/day = ~$70k daily notional. At $10k account, $500 margin, 20x: $10,000 notional/trade, ~$1.4M daily notional.

### Decisions recorded
None explicitly made — this was a review session.

### State changes
- `uml/strategy-system-flow.md` — UPDATED (full rewrite, 2026-02-16 to 2026-03-05)

### Open items recorded
Phase 0 blockers still unresolved (Q1-Q6 listed).
Signal rename pending (final name for B/Rotation).
Beta bot overlaps still need removal.

### Notes
- Open questions listed are unchanged from 2026-03-03 roadmap — no progress on Phase 0 questions in this period.

---

## BUILD-JOURNAL-2026-02-13.md
**Date:** 2026-02-13
**Type:** Build session (multi-session journal)

### What happened
Multi-session build journal covering 6 sessions on 2026-02-13.

Session 1: Built `download_all_available.py` for 399-coin data fill (bidirectional, restartable, backup-first). Built `dashboard_v2.py` with 3 DataFrame fixes, Streamlit API fixes, logging. RULE VIOLATION documented: used Edit tool directly instead of build script.

Session 2: Created `DASHBOARD-VERSIONS.md`. Confirmed cooldown parameter already fully configurable. Scoped P1-P5 backlog items. Recommended execution order: P2 > P3 > P4 > P1(B) > P5.

Session 3: Created `DASHBOARD-V3-BUILD-SPEC.md` — 6-tab VINCE control panel full architecture spec with 6 tabs, LSG categorization, VINCE blind training protocol, ~45 column sweep CSV.

Session 4: Reviewed monolithic spec, found 6 problems (emojis, scope creep, etc.), split into 3 separate specs: SPEC-A-DASHBOARD-V3.md (UI only), SPEC-B-BACKTESTER-V385.md (engine changes), SPEC-C-VINCE-ML.md (ML architecture).

Session 5: Cross-checked all 3 specs against actual source files. Found and fixed 10 issues. Key finding: BBWP exists only in Pine Script — no Python implementation. 3 fields deferred until BBWP Python port.

Session 6: Built `scripts/build_all_specs.py` (2189 lines) to generate all 9 output files from specs A, B, C. All generators produce valid Python (ast.parse verified). Fixed 2 critical bugs during review: `super().run()` signature mismatch and `import logging.handlers` placement.

### Decisions recorded
1. HARD RULE VIOLATION rule added to MEMORY.md: "DOUBLE CONFIRM SHORTCUTS — When tempted to take a shortcut, STOP and ask the user first."
2. Staging folder approach chosen over direct overwrite for dashboard deployment.
3. 3-spec split architecture: Spec A standalone, Spec B adds engine metrics, Spec C adds ML.
4. BBWP Python port deferred — separate future spec needed.
5. Backtester v385 uses two-pass design: v384 logic unchanged, post-process enrichment added.
6. Recommended backlog execution order: P2 > P3 > P4 > P1(B) > P5.

### State changes
- `scripts/download_all_available.py` — CREATED
- `scripts/dashboard_v2.py` — CREATED (RULE VIOLATION: direct Edit instead of build script)
- `DASHBOARD-VERSIONS.md` — CREATED
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC.md` — CREATED (1009L)
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC-REVIEW.md` — CREATED
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-SUGGESTIONS.md` — CREATED
- `PROJECTS/four-pillars-backtester/SPEC-A-DASHBOARD-V3.md` — CREATED + corrected
- `PROJECTS/four-pillars-backtester/SPEC-B-BACKTESTER-V385.md` — CREATED + corrected
- `PROJECTS/four-pillars-backtester/SPEC-C-VINCE-ML.md` — CREATED + corrected
- `scripts/build_all_specs.py` — CREATED (2189L), all 9 generators ast.parse verified

### Open items recorded
- User still has not run `build_staging.py` from 2026-02-12 Phase 3.
- `build_all_specs.py` written but user must run it.

### Notes
- This is the earliest log in batch 10 (2026-02-13 vs other 2026-03-xx logs). Provides historical context.
- BBWP finding here (no Python port) was still unresolved in 2026-03-xx sessions (BBW-1 open question in position-management-study).

---

## build_journal_2026-02-11.md
**Date:** 2026-02-10 to 2026-02-11
**Type:** Build session (multi-phase journal)

### What happened
Earliest journal in this batch. Multi-phase build session for Four Pillars ML backtester pipeline.

Phase 1: Built 11 missing infrastructure files across strategies/, engine/, optimizer/, ml/, gui/. 10 written (1 skipped — already existed). 19/19 tests passed.

Phase 2: Comprehensive inventory of 62 Python files. Identified 4 remaining gaps: missing ML dashboard tabs, missing dashboard test script, WEEXFetcher import bug, ml/live_pipeline.py not built.

Phase 3: Built `build_staging.py` (1692L) to create: staging/dashboard.py (5-tab ML dashboard), staging/test_dashboard_ml.py, staging/run_backtest.py (WEEXFetcher bug fixed), staging/ml/live_pipeline.py. Status: written, NOT YET RUN.

Phase 4: Built complete v3.8.3 Python backtester — 4-stage state machine, A/B/C/D/ADD/RE/R signals, ATR SL, AVWAP trailing, scale-out mechanism. 8 source files + 3 results files. Key result: SL=2.5 ATR best (9/10 coins profitable), LSG 85-92%.

Phase 5: Built v3.8.4 — adds optional ATR-based take profit. TP sweep results: No TP baseline +$6,261, TP=2.0 ATR +$7,911 (only level beating baseline), TP=0.50 catastrophic (-$5,095). Multi-coin sweep confirmed TP=2.0 NOT universal: KITE and BERA both worse with TP=2.0.

Phase 6: Referenced BUILD-JOURNAL-2026-02-12.md for dashboard overhaul + data normalizer.

### Decisions recorded
1. Staging folder approach for safe deployment (user's choice).
2. v3.8.3 designed with 4-slot engine, execution order: exits -> update -> scale -> pending -> entries -> adds -> re-entry.
3. v3.8.4 TP is optional (--tp-mult, default None = no TP).
4. SL checked before TP (pessimistic) when both could trigger.
5. TP=2.0 ATR is coin-specific, not universal — per-coin optimization needed.
6. WEEXFetcher bug fixed in staging only, production run_backtest.py retains old import.

### State changes
- `strategies/base_strategy.py` — SKIPPED (existed)
- 10 new infrastructure files created (exit_manager, indicators, signals, cloud_filter, four_pillars_v3_8, walk_forward, aggregator, xgboost_trainer, coin_selector, parameter_inputs)
- `scripts/build_staging.py` — CREATED (not yet run)
- v3.8.3 files: state_machine_v383.py, four_pillars_v383.py, position_v383.py, backtester_v383.py, run_backtest_v383.py, sweep_sl_mult_v383.py, test_v383.py, mfe_analysis_v383.py, capital_analysis_v383.py, validation_v371_vs_v383.py
- v3.8.4 files: position_v384.py, backtester_v384.py, run_backtest_v384.py, sweep_tp_v384.py, capital_analysis_v384.py
- `engine/commission.py` — modified to add volume tracking
- Results: sweep_v383_sl_mult.md, mfe_analysis_v383.md, validation_v371_vs_v383_RIVERUSDT.md, sweep_v384_tp_RIVERUSDT.md, KITEUSDT.md, BERAUSDT.md

### Open items recorded
- Run TP sweep on KITE and BERA (done in Phase 5 but originally listed as remaining)
- Deploy staging files (`build_staging.py` not yet run)
- ML meta-label on D+R grades
- Live TradingView validation (Pine Script vs Python)
- Multi-coin sweep with more coins
- BE raise optimization (LSG 85-92% opportunity)

### Notes
- v3.8.4 LSG 85-92% finding here is the earliest documented mention of this figure. Later logs reference "LSG 75.8%" for the live bot trades — these are different datasets (backtester vs live trades).
- LSG = "Loser Saw Green" (losers that reached unrealized profit before closing).
- This log predates the BingX connector work by ~9 days.

---

## PENDING-TASKS-MASTER.md
**Date:** Generated 2026-02-24
**Type:** Planning / task registry

### What happened
Master summary of all pending tasks as of 2026-02-24, compiled from source logs. Not a session log — a curated reference document.

Contains 14 items across priority levels: IMMEDIATE (2), HIGH PRIORITY BLOCKED (3), MEDIUM PRIORITY (4), LOWER PRIORITY (5), STRATEGY FIXES (1 section), DEFERRED (4 items), PRODUCT BACKLOG (7), and COMPLETED BUILDS reference (18 entries).

Key items:
- IMMEDIATE #1: Vince v2 Concept approval + Trading LLM scope + Plugin Interface Spec + Four Pillars Plugin Spec
- IMMEDIATE #2: WEEX Live Market Screener Build (scope approved, not started)
- HIGH #3: Dashboard v3.9.3 equity curve date filter bug — BLOCKED (build script works, generated file has syntax error, fix script has logic error)
- HIGH #4: Four Pillars Strategy Scoping — 19 unknowns remaining
- HIGH #5: BingX Live Trading — connector done (67/67 tests), open decisions block live config
- STRATEGY FIXES: 5-phase plan — R:R ratio inverted (TP=2.0 ATR, SL=2.5 ATR → R:R=0.8), BE raise logic removed in v3.8.x refactor must be restored

### Decisions recorded
None (this is a reference document, not a session log).

### State changes
None (document records state, not changes).

### Open items recorded
All items listed in the document are open items as of 2026-02-24. Notable:
- Dashboard v3.9.3 blocked on indentation fix logic error
- WEEX screener approved but not built
- 19 strategy unknowns unresolved
- BingX config decisions pending
- build_staging.py still not run (referenced from 2026-02-11 journal)

### Notes
- This document is dated 2026-02-24 — approximately 9-10 days before the other logs in this batch. Many items listed as open here were addressed in the 2026-03-03 to 2026-03-05 logs.
- Dashboard v3.9.3 bug noted here — separate from BingX dashboard (bingx-live-dashboard). This refers to the backtester dashboard.
- WEEX screener scope approved here — later logs reference BingX screener, not WEEX. Context shift occurred.
- Completed builds list (C.1-C.18) provides useful reference for what was done before 2026-02-24.

---

## commission-rebate-analysis.md
**Date:** 2026-02-07
**Type:** Strategy spec / analysis document

### What happened
Commission and rebate analysis document for Four Pillars v3.7.1 on WEEX exchange. Establishes correct commission math, rebate impact, expectancy calculations, and breakeven raise scenarios.

Key finding: v3.7 Pine Script used `strategy.commission.percent=0.06` which applied to cash ($500), giving $0.30/side instead of correct $6.00/side on $10k notional. This caused the backtester to show profit while the real account lost money.

Correct Pine Script: `commission_type=strategy.commission.cash_per_order, commission_value=6`.

Rebate math: Account 1 (70% rebate) = $8.40 rebate/RT, net $3.60/RT. Account 2 (50% rebate) = $6.00 rebate/RT, net $6.00/RT. Rebates settle daily 5pm UTC.

Expectancy: v3.7.1 gross $12.62/trade, after 70% rebate $9.02/trade = $902/month at 100 trades.

Breakeven+$2 raise scenario: converts 86% of losers (those that saw green) to small winners. Gross jumps from $12.62 to $41.13/trade. With 70% rebate: $37.53/trade = $3,753/month at 100 trades.

Backtester must model daily rebate settlement (actual credit at 5pm UTC), not simplified percentage reduction, because timing difference affects drawdown calculations.

### Decisions recorded
1. Pine Script must use `cash_per_order` not `commission.percent` for leveraged strategies.
2. Commission rate: 0.06% per side on notional (WEEX).
3. BE raise threshold optimal value is unknown — optimizer must test $2/$5/$10/$20 variants.
4. Daily rebate settlement must be modeled explicitly in backtester (timing matters for drawdown).

### State changes
None — this is an analysis document, not a build session.

### Open items recorded
- Backtester must validate: exact LSG figure, $2 raise feasibility, noise stop-outs, regime sensitivity, daily rebate settlement modeling.

### Notes
- This is the oldest document in this batch (2026-02-07). It documents WEEX exchange specifics — later work shifted to BingX.
- The 86% LSG figure cited here is from TradingView backtester (v3.7.1). Later Python backtester logs cite 85-92% LSG — consistent range. Live bot trades show 75.8% LSG.
- Commission rates differ between documents: WEEX = 0.06% (this doc), BingX = 0.08% (later docs). Different exchanges.
- The "rebate farming" concept documented here is the foundational framework referenced throughout later sessions.
