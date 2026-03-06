# Research Findings — Batch ordered-07

**Generated:** 2026-03-05
**Files processed:** 20
**Date range:** 2026-02-18 to 2026-02-25

---

## File 1: 2026-02-18-dashboard-audit.md

**Date:** 2026-02-18
**Type:** Code audit / verification

**What happened:**
Full read-through of 9 source files (~4,315 lines total) to verify backtest results are legitimate. User asked "is this really through, all those trades taken would they really result in that?" Audit covered signals, backtester engine, position management, commission, AVWAP, and dashboard display.

**Decisions recorded:**
- Engine declared MECHANICALLY CORRECT for all components except one known bug
- Scale-out commission double-count in CSV confirmed (low severity): SCALE_1 remainder shows commission=9.0 when it should be 5.0. Equity curve UNAFFECTED — entry commission deducted once at entry time only.
- Dashboard display: no inflation anywhere. Metrics direct from backtester dict.

**State changes:**
- Signals (stochastics, clouds, state_machine_v383): CORRECT
- Backtester (backtester_v384): CORRECT with 1 known CSV bug
- Position (position_v384): CORRECT
- AVWAP: CORRECT
- Commission: CORRECT
- Equity curve: CORRECT
- "77K-90K trades and 85-86% LSG numbers are REAL."

**Open items recorded:**
- Scale-out commission CSV bug: low priority, equity unaffected

**Notes:**
K4 stage machine: K4 enters extreme < 25 for longs, fires A/B/C based on K1/K2/K3 flags. A bypass: all 4 flagged, cloud3 not needed. B: K1+K2, requires cloud3_ok. C: K1 only, requires price_pos == +1. Exit uses SL/TP exact prices (not close). Commission: 0.08% taker entry, 0.02% maker exit.

---

## File 2: 2026-02-18-dashboard-v392-build.md

**Date:** 2026-02-18
**Type:** Build log / completed build

**What happened:**
Dashboard v3.9.2 built with Numba acceleration. 5 new files created via build script. 10 patches applied to dashboard_v391.py to create dashboard_v392.py. Three signal functions wrapped with @njit(cache=True): stoch_k, ema, _rma_kernel.

**Decisions recorded:**
- Numba selected for acceleration (not GPU)
- Zero modifications to existing files — all new files only
- Rollback: delete 6 new files to restore v3.9.1 instantly
- Build ran: 10/10 patches, 5/5 files clean. Dashboard v392 confirmed working by user.

**State changes:**
New files: utils/timing.py, signals/stochastics_v2.py, signals/clouds_v2.py, signals/four_pillars_v383_v2.py, scripts/build_dashboard_v392.py, scripts/dashboard_v392.py. Numba compiled on first launch.

**Open items recorded:**
- Numerical parity verification needed: RIVERUSDT 5m run v391 vs v392 — 4 numbers must match exactly

**Notes:**
Performance Debug checkbox added to sidebar. Timing panel shows signals_ms vs engine_ms per coin in portfolio run. Numba kernels: pure numpy, type inference instant, docstrings inside @njit ignored.

---

## File 3: 2026-02-18-vince-ml-build.md

**Date:** 2026-02-18
**Type:** Build log + critical correction

**What happened:**
Session 1: Built 3 build scripts implementing the Vince ML pipeline. Session 2 correction: ENTIRE BUILD WAS MISLABELED. What was built (XGBoost trade classifier, meta-labeling, SHAP, bet sizing) is VICKY's toolset. Vince's actual tool (parameter optimizer) was not built. Additionally, cloud3_allows_long/short filter was added to strategy plugin without user approval.

**Decisions recorded:**
- All files created this session: considered VICKY's pipeline, not Vince's
- Vince ML v1 (XGBoost classifier) = REJECTED, wrong architecture
- 15 discrepancies corrected in what was built vs spec

**State changes:**
Files created (but belong to Vicky): strategies/__init__.py, strategies/base.py, strategies/four_pillars.py, ml/xgboost_trainer_v2.py, ml/features_v3.py, ml/shap_analyzer_v2.py, ml/bet_sizing_v2.py, scripts/train_vince.py, scripts/build_docs_v1.py, scripts/build_data_infra_v1.py, scripts/build_train_vince_v1.py

**Open items recorded:**
- Vince ML v2 scope: needs new architecture (trade research engine, NOT classifier)
- cloud3_allows_long/short filter decision: pending user approval

**Notes:**
Three ML personas confirmed: Vince = rebate farming/parameter optimization. Vicky = copy trading/trade filtering (XGBoost TAKE/SKIP). Andy = FTMO forex. This is the first clear separation of these three personas in the logs.

---

## File 4: 2026-02-18-vince-ml-build-plan.md

**Date:** 2026-02-18
**Type:** Architecture spec / build plan

**What happened:**
Revised Master Build Plan created correcting 15 discrepancies between Sonnet-generated build and three authoritative sources (SPEC-C, BUILD-VINCE-ML, book analyses). Full ML pipeline documented with Section 0 (strategy plugin architecture), A (docs), B (data infra), C (ML bug fixes), D (XGBoost training pipeline), E (Phase 2 book-prescribed enhancements — future only).

**Decisions recorded:**
- Pool split: 60/20/20 (NOT 70/10/20) — Pool A: 240 coins training, Pool B: 80 validation, Pool C: 79 holdout NEVER touched
- XGBoost role: per-coin AUDITOR only (not production). PyTorch = production (Phase 2)
- Per-coin models (one XGBoost per coin)
- Two labeling modes: exit (TP=1/SL=0) and pnl (net>0)
- Grade filtering D+R with threshold sweep 0.3-0.7
- Walk-forward WFE with ROBUST/MARGINAL/OVERFIT rating
- GPU mandatory: device=cuda, tree_method=hist, fail fast (no CPU fallback)
- Strategy plugin architecture approved: models/four_pillars/, models/vicky/, models/andy/ isolated directories

**State changes:**
Build plan approved and ready to execute. Existing 12 ML modules listed as "DO NOT REWRITE."

**Open items recorded:**
- Section E (Phase 2 enhancements): Triple-barrier labeling, Meta-labeling, Sample weights, Feature importance pre-screening, Deflated Sharpe, R-multiples + SQN — all documented but NOT built

**Notes:**
Full 12-step training pipeline defined. StrategyPlugin ABC interface defined with enrich_ohlcv, compute_signals, get_backtester_params, extract_features, get_feature_names, label_trades methods. RTX 3060 full sweep time estimate: 2-4 hours.

---

## File 5: 2026-02-18-vince-scope-session.md

**Date:** 2026-02-18
**Type:** Session log / scope work

**What happened:**
Multi-phase session: (1) identified Vince ML v1 failure — built critic (TAKE/SKIP) when needed assistant (parameter optimizer); (2) launched 3 explore agents; (3) mapped 83 relationship questions; (4) introduced "constellation" concept; (5) user provided two 10-coin portfolio CSVs (77,995 trades 86.0% LSG; 89,633 trades 85.6% LSG); (6) CRITICAL ERROR: I inverted "under 60" to "past 60" — user caught immediately.

**Decisions recorded:**
- Vince ML v2 = trade research engine (PyTorch, GPU), NOT classifier
- Never reduce trade count. Volume preserved.
- RE-ENTRY logic fix deferred until after Vince scope
- Dashboard v3.9.2 build script ready, not yet run by user

**State changes:**
Prevention rules added: (1) NEVER paraphrase directional statements, (2) SCOPE before plan before build, (3) Stochastics = UNIT (never analyze independently), (4) Complete numerical state only

**Open items recorded:**
- Continue Vince ML v2 scoping
- Architecture breakdown
- New UML diagrams for research engine (not classifier)
- Fix scale-out commission bug (user decides priority)

**Notes:**
"Under 60 for long" = K1 < 60 (not yet reached 60, still rising from oversold). User's exact correction documented: "wtf, i said under 60 for long and you make is past 60?" — this triggered the NEVER PARAPHRASE DIRECTIONS hard rule now in MEMORY.md.

---

## File 6: 2026-02-19-engine-audit.md

**Date:** 2026-02-19
**Type:** Engine audit + architecture session

**What happened:**
Two-part session. Part 1: Thorough re-audit of engine with actual CSV verification. PnL math verified by calculation against 3 sample trades. Commission dollar values verified. Exit prices verified (exact SL/TP levels). Part 2: Vince v2 architecture breakdown — 7 modules designed, feature vector size calculated, 5 analysis types identified.

**Decisions recorded:**
- Engine verdict: MECHANICALLY CORRECT, trades are REAL
- Conservative 5-10% net PnL discount recommended for live (slippage + funding)
- vince/ directory chosen (separate from ml/ which is Vicky's v1 code)
- AVWAP/SL option B: enricher runs lightweight AVWAP/SL simulator
- Bar alignment: entry_datetime/exit_datetime (NOT bar indices)
- Scale-out handling: group by (symbol, entry_bar, direction) = one position
- 5 analysis types: parameter sweep, conditional grouping, feature correlation, temporal delta, multi-condition filter

**State changes:**
7 Vince modules designed: schema.py, enricher.py, tensor_store.py, engine.py, validation.py, sampling.py, dashboard_tab.py. Feature vector: 24 static + 44 dynamic = 68 features × 10 moments = 680 per trade. 90K × 680 = ~244 MB float32, fits RTX 3060 12GB.

**Open items recorded:**
- Unified abstraction vs separate functions for 5 analysis types: user didn't decide
- Output format not finalized
- Build order not confirmed
- strategy_document add to get_vince_schema() deferred to next session

**Notes:**
Commission model uses DOLLAR values, not percentages. Standard trade: taker entry $8.0 + maker exit $2.0 = $10.0 total. Scale-out: $8 entry + $1 exit + $1 exit = $10 correct. Context ran out mid-session; user was about to answer dashboard UX question.

---

## File 7: 2026-02-19-vince-scope.md

**Date:** 2026-02-19
**Type:** Session log / scope continuation

**What happened:**
Continued Vince v2 scoping. User's opening question: 10 out of 400 coins not working at all, wants win rate improvement while keeping ALL trades. Session covered: random batch validation math, Cloud 3 discussion ("maybe the hard cloud 3 code should not be there"), constellation query dimensions (full list documented), BBW addition as dimension, scope expansion (Vince runs backtester himself, not passive CSV reader), "shoe salesman" correction. Training log: Claude made 5 unproven claims stated as fact.

**Decisions recorded:**
- Vince runs the backtester himself — 3 operating modes: user query, auto-discovery, settings optimizer
- Learning mechanism: pure statistical frequency (NOT ML weights). Accumulated run history with timestamps IS the learning.
- BBW added as constellation dimension (signals/bbwp.py already built, reuse)
- Two CSV comparison: before/after strategy change, same query on both, delta column
- Fixed constants confirmed: K1/K2/K3/K4 periods and cloud EMAs are FIXED (not swept)
- Dashboard must be interactive (real-time response to filter changes)
- No price charts. Indicator numbers only.
- Master project file: docs/vince/VINCE-PROJECT.md

**State changes:**
Constellation query dimensions fully documented (static, dynamic, trade type, outcome, regime, BBW). 5 panels designed for dashboard. Open items for next session: (1) how does optimizer decide which settings to try, (2) interactive ML UX specifics, (3) module architecture not approved, (4) one-line perspective not confirmed.

**Open items recorded:**
- Grid search vs random vs Bayesian for optimizer: not decided
- Interactive ML UX exact design: not defined
- User confirmed stochastics, cloud EMAs are FIXED instruments

**Notes:**
Training log appended to same file: 5 false claims documented with source traced. User quote: "I am going to build this automation with or without you. It is time to properly train you first." Rule added: before stating anything as fact, cite source or say hypothesis/unknown.

---

## File 8: 2026-02-20-bingx-architecture-session.md

**Date:** 2026-02-20
**Type:** Architecture planning / UML creation

**What happened:**
Architecture session for BingX live deployment. Confirmed strategy v3.8.4. Confirmed BingX API endpoints, auth method, symbol format, rate limits. Created full architecture doc and two UML documents: connector UML and strategy UML.

**Decisions recorded:**
- No code written until: (1) dashboard sweep locks sl_atr_mult/tp_atr_mult/be_raise/grade filter, (2) coin list confirmed (positive expectancy > $1/trade at $500 notional), (3) TP vs runner decision, (4) architecture approved
- Strategy = black-box plugin. Connector calls plugin.get_signal(ohlcv_df) → Signal object.
- Silo testing: each strategy variant is a separate plugin file
- 4 strategy variants planned: v384 baseline, v384 grade-A-only, v385 Cloud4 trail, v386 Vince-filtered

**State changes:**
New docs: BINGX-LIVE-TRADING-ARCHITECTURE.md, docs/BINGX-CONNECTOR-UML.md, docs/FOUR-PILLARS-STRATEGY-UML.md. BingX API details confirmed: HMAC-SHA256, X-BX-APIKEY header, positionSide required (hedge mode), SL/TP as JSON strings, VST demo URL.

**Open items recorded:**
- Which coins pass the sweep?
- Fixed TP or runner (Cloud 4 trail)?
- Grade A only or A+B for live?
- n8n or standalone Python bot?

**Notes:**
Target: $1,000 account, $50 positions. BingX rate limit: 10 orders/second (upgraded Oct 2025). No passphrase needed (unlike WEEX).

---

## File 9: 2026-02-20-bingx-connector-build.md

**Date:** 2026-02-20
**Type:** Build log / completed build

**What happened:**
Full BingX Execution Connector built in one build script generating 25 files. Build script: build_bingx_connector.py. All 25 files generated. Test results progression: first run 3 failures → second run 56/56 → third run 67/67 (including 11 user-added FourPillarsPlugin tests). Screener v1: 22/22.

**Decisions recorded:**
- 6 bug fixes applied: C03 (halt_flag in RiskGate check 1), C04 (halt_flag daily reset), C05 (allowed_grades from plugin), C07 (public endpoints unsigned), C01 (LONG/SHORT/NONE vocab), C02 (mark price from /v2/quote/price)
- Build script re-run: 25/25 files, 0 errors

**State changes:**
25 files created including: bingx_auth.py, notifier.py, state_manager.py, data_fetcher.py, risk_gate.py, executor.py, signal_engine.py, position_monitor.py, main.py, 6 test files, 2 debug scripts, config.yaml, plugins/mock_strategy.py.

**Open items recorded:**
- Deploy to Jacky VPS: scp command ready

**Notes:**
Architecture: 2 daemon threads (MarketLoop, MonitorLoop). Graceful shutdown. Daily halt reset at 17:00 UTC. Config: 3 coins, mock_strategy plugin (demo). Tests: 56 original + 11 FourPillarsPlugin = 67 total.

---

## File 10: 2026-02-20-vince-scope.md

**Date:** 2026-02-20
**Type:** Session log / scope continuation + audit

**What happened:**
Two-part session. Part 1: Concept doc v1 audit — 14 issues identified and logged. Part 2: New architectural direction adding two-layer design with fine-tuned trading LLM. Session ended before concept v2 was written. Session update from 2026-02-23 appended: concept v2 written and all 14 corrections applied.

**Decisions recorded:**
- Plugin interface: strategy plugin provides computational (compute_signals, parameter_space, trade_schema, run_backtest) AND semantic (strategy_document path in markdown) components
- Two-layer architecture: Layer 1 (Quantitative) always available; Layer 2 (Interpretive) via Ollama trading LLM triggered after full sweep
- Trading LLM: fine-tuned domain expert, NOT general model with prompts. Runs locally via Ollama. Candidate: DeepSeek-R1 (reasoning chain visible) or Qwen2.5.
- FULL PATHS EVERYWHERE rule added to MEMORY.md this session
- Concept v2 rewrite prepared but NOT written (session ran out)

**State changes:**
14 concept doc issues documented. Concept v2 written 2026-02-23. Qwen3 response to trading LLM training question saved to docs/TRADING-LLM-QWEN3-RESPONSE.md.

**Open items recorded:**
- Trading LLM scoping: separate session needed (fine-tuning dataset, training, evaluation, Ollama deployment)
- Plugin interface formal spec: blocked by concept v2 approval
- Concept v2 approval: awaiting user review

**Notes:**
14 issues: strategy coupling, hardcoded constants, hardcoded parameter space, hardcoded constellation dimensions, K4 regime buckets hardcoded, win rate as dominant metric bias, autonomy contradiction, backtester coupling, no significance control, hardcoded coin counts, editorial comment, LSG terminology specificity, What Already Exists mixing, dashboard coupling.

---

## File 11: 2026-02-20-youtube-transcript-analyzer-build.md

**Date:** 2026-02-20
**Type:** Build log / completed build

**What happened:**
YouTube transcript analyzer system designed and built. Spec complete in first session. Claude Code build session produced build script generating all modules. Architecture changed during build: dropped DeepSeek, single model qwen3:8b only.

**Decisions recorded:**
- yt-dlp for extraction (no API quota, no cost)
- qwen3:8b single model (DeepSeek dropped — eliminates VRAM contention)
- Confidence: FOUND=yes (include), FOUND=no (discard)
- $0 cost — all inference local via Ollama
- Rate limiting: 4-10s jitter between videos, 60-min HTTP 429 backoff
- archive.txt checkpoint for full resume
- VTT timestamps preserved, YouTube deeplinks generated

**State changes:**
Build script created: PROJECTS/yt-transcript-analyzer/build_yt_transcript_analyzer.py. Generates: config.py, startup.py, fetcher.py, cleaner.py, chunker.py, analyzer.py, reporter.py, main.py, 4 test files. Spec v2 created with audit fixes. Status: BUILD DELIVERED — not yet run by user.

**Open items recorded:**
- User must run build script and pip install
- Audit fixes applied: C1-C5, H1-H6, M1-M6, L1-L4

**Notes:**
Target: 210 videos, structured Obsidian report with timestamped deeplinks. English only. visual reference detection (trigger keywords). Upgrade path noted: multi-language, multi-channel, Claude API fallback, Streamlit UI.

---

## File 12: 2026-02-23-dashboard-v393-bug-fix.md

**Date:** 2026-02-23
**Type:** Bug fix session (in progress, blocked)

**What happened:**
Bug reported: custom date range change in Portfolio Analysis mode shows stale equity curve from previous run. Root cause: session state cache not cleared on settings change — warning shown but old data used. Fix designed (5 changes). Build script created. But indentation script had logic error — dashboard_v393.py has SYNTAX ERROR at line 1972.

**Decisions recorded:**
- Root cause confirmed: line 1963-1964, old portfolio_data not cleared when hash mismatch detected
- Fix: clear session_state["portfolio_data"] on change, set _pd = None, show info not warning
- All rendering code under `if _pd is not None:` guard — must indent lines 1971-2371 by +4 spaces
- st.stop() REJECTED — creates blank page, not suitable
- Smart indentation needed: only indent lines at base indent level 8, skip lines already at 12+

**State changes:**
Files created: scripts/build_dashboard_v393.py (WORKING), scripts/dashboard_v393.py (SYNTAX ERROR), scripts/fix_v393_indentation.py (LOGIC ERROR). Version v3.9.3 not yet functional.

**Open items recorded:**
- Fix indentation script logic
- Full verification: fresh session test, date change test, re-run test, regression test
- Update MEMORY.md and DASHBOARD-FILES.md once working

**Notes:**
Options: (1) fix automated indentation script, (2) user manually indents in IDE, (3) continue using v3.9.2 with workaround. Bug is cosmetic (stale chart display only) — v3.9.2 still functional.

---

## File 13: 2026-02-23-four-pillars-strategy-scoping.md

**Date:** 2026-02-23
**Type:** Strategy scoping / specification work

**What happened:**
Strategy scoping session building FOUR-PILLARS-QUANT-SPEC-v1.md. Key strategy decisions documented, chart reading rules established (chart-reading-skill.md), two-track build plan created (Track A: Cloud 3 fix + BingX demo, Track B: VINCE). 19 spec unknowns remaining after session.

**Decisions recorded:**
- BBW/BBWP and Ripster EMA Clouds: NOT entry or exit triggers — lagging, context only
- No hard lines on stochastic zones — 20/80 are reference points, zones are flexible
- Cloud 3 = EMA 34/50 (confirmed from ripster_ema_clouds_v6.pine)
- K4 K/D cross = late entry/add-on confirmation, NOT primary entry
- Cloud 3 role: post-entry health indicator only, not an entry gate
- Rotation window = 5 candles (working value), Vince to optimize

**State changes:**
New files: PROJECT-BUILD-PLAN-v2.md, docs/FOUR-PILLARS-QUANT-SPEC-v1.md (19 unknowns), skills/chart-reading-skill.md. Signal types documented: (1) Quad Rotation, (2) Add-On/Late Runner, (3) Divergence.

**Open items recorded:**
19 spec unknowns: rotation window, K above D criteria, BBWP thresholds, add-on stop, divergence pivot lookback, divergence entry trigger, K above/below D on divergence, BE trigger, trail distance, Cloud 3 persistent bearish threshold, counter-trend SL, K1 re-enters extreme zone action, max concurrent positions, skip or queue, leverage, min 24h volume, max watchlist, AVWAP anchor rule, add-on sizing.

**Notes:**
Errors this session: (1) called all 4 stochastics oversold when only K1/K2 were, (2) BBWP red zone called from color not numbers (55-57% is mid range), (3) K4 K/D cross called primary entry, (4) imposed hard lines after correction, (5) wrote "short is mirror of long." Session ended without completing scoping.

---

## File 14: 2026-02-23-screener-scope.md

**Date:** 2026-02-23
**Type:** Scope log / product scoping

**What happened:**
Screener concept scoped as solution to BingX connector config.yaml coin selection problem. Outcome: screener v1 (historical backtest ranker) was confirmed as WRONG approach — TradingView already does live scanning better. WEEX live market screener identified as what's actually needed.

**Decisions recorded:**
- Frequency: live continuous filter — runs at bot startup + daily reset
- Criteria: ATR ratio (commission viability) + recent performance (last 30/60 days) + volume/liquidity
- Integration: Vince dashboard — new Screener tab
- Historical all-time PnL: NOT selected — recency matters more
- Platform: WEEX (not BingX) for this screener

**State changes:**
Screener v1 (wrong approach) already built: utils/screener_engine.py, scripts/screener_v1.py, tests/test_screener_engine.py (22/22 pass), bingx-connector/main.py patched. Status: exists but deemed wrong approach.

**Open items recorded:**
- Lookback period: 30 or 60 days TBD
- Connector integration: reads active_coins.json or manual config.yaml update?
- Dashboard version to target

**Notes:**
Short file — screener scope just getting started. WEEX screener v1 scope outlined: 3 files (weex_fetcher.py, weex_screener_engine.py, weex_screener_v1.py). Columns: symbol, price, 24h_change_pct, 24h_vol_usd, vol_change_pct, atr_ratio, stoch_60, stoch_9, cloud3_dir, price_pos, signal_now.

---

## File 15: 2026-02-24-countdown-to-live-session.md

**Date:** 2026-02-24
**Type:** Session log / go-live prep

**What happened:**
Countdown-to-live session. Audit of Step 1 files revealed 5 faults. All 4 fixable faults resolved this session (fault report generated). 67/67 tests passing confirmed. config.yaml updated by user. Bot ready to run.

**Decisions recorded:**
- config.yaml updated: plugin = four_pillars_v384, allow_a/b: true, allow_c: false, sl_atr_mult: 2.0, tp_atr_mult: null
- Test fixes: assertAlmostEqual for float precision, single requests.get patch with 3 sequential responses, deepcopy for DEFAULT_STATE
- Ollama model: qwen3:8b confirmed (already installed, full GPU inference 40-60 tok/s)
- Week plan: Tue=Step1 (demo), Wed-Thu=Step2 (strategy spec + dashboard comparison), Fri=Step3 (go live $1,000/$50)

**State changes:**
COUNTDOWN-TO-LIVE.md created, STEP1-CHECKLIST.md created, fault-report created. 67/67 tests passing. Bot ready: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"`.

**Open items recorded:**
- Run main.py
- Observe: startup log, BingX VST connection, warmup progress (~16h for 200 bars on 5m)
- First A/B signal, Telegram alert, position in BingX VST account

**Notes:**
Step 1 = demo bot running. Step 2 = strategy spec unknowns + Signal Type 2 + dashboard comparison. Step 3 = go live. S08 open risk: backtester multi-slot vs live single-slot P&L not comparable — must resolve before Step 3.

---

## File 16: 2026-02-24-fault-report-step1-build-review.md

**Date:** 2026-02-24
**Type:** Fault report / code review

**What happened:**
Plan-mode read-only audit of all Step 1 files. 5 faults found, priority ordered. Fix order documented with exact line numbers.

**Decisions recorded:**
- F1 (CRITICAL → CLEARED after investigation): four_pillars.py produces correct long_a/b/c, short_a/b/c at lines 64-73 — plugin import is FINE
- F2 (HIGH): config.yaml missing four_pillars block — add explicit block
- F3 (LOW): test_executor.py line 178 assertEqual → assertAlmostEqual
- F4 (LOW): test_integration.py line 106 — add assertIsNotNone before monitor.check()
- F5 (INFORMATIONAL): warmup_bars=200 vs UML spec 89 — conservative, not wrong

**State changes:**
Fault report written to two locations: 06-CLAUDE-LOGS/ and PROJECTS/bingx-connector/docs/FAULT-REPORT-2026-02-24-step1-build-review.md.

**Open items recorded:**
- All 4 fixable faults resolved in countdown-to-live session (same day)

**Notes:**
Critical initial finding: F3 appeared to be CRITICAL (wrong plugin import). Investigation revealed four_pillars.py DOES produce correct signal columns. The "critical" label was downgraded to CLEARED. This is the correct audit approach — investigate before labeling severity.

---

## File 17: 2026-02-24-vince-todo.md

**Date:** 2026-02-24
**Type:** Session handoff / to-do list

**What happened:**
Short handoff file created after PC reboot. Lists 4 Vince items in priority order with file paths.

**Decisions recorded:**
- Concept v2 review and approval is blocker for all downstream Vince work
- Trading LLM scoping is a separate session (parallel track, not blocking Vince)
- Formal plugin interface spec: blocked by concept v2 approval
- Four Pillars plugin spec: blocked by plugin interface spec

**State changes:**
N/A — handoff only, no changes made.

**Open items recorded:**
1. Review and approve VINCE-V2-CONCEPT-v2.md
2. Scope trading LLM (separate session): collect DeepSeek-R1 response, define fine-tuning dataset
3. Formal plugin interface spec
4. Four Pillars plugin spec

**Notes:**
Short file (35 lines). All items point to existing files at full paths.

---

## File 18: 2026-02-24-vince-v2-ml-spec-review.md

**Date:** 2026-02-24
**Type:** Spec review / architectural fixes

**What happened:**
Thorough review of VINCE-V2-CONCEPT.md (v1), VINCE-V2-CONCEPT-v2.md, SPEC-C-VINCE-ML.md, vince-ml skill, and full project tree. 6 recommendations evaluated, 3 confirmed as definitive fixes, 2 marked overstated (dropped), 1 as user decision. 4 concrete changes applied to documents.

**Decisions recorded:**
- Mode 2 permutation gate: ADDED — shuffle trade outcome labels, compute empirical null distribution, only surface patterns above 95th percentile. Prevents false discovery in large constellation search space.
- Mode 3 fitness function: DEFINED explicitly — Calmar ratio with rebate. Hard rejection if trade_count < 0.95 * baseline. No ambiguity at build time.
- K4 regime bucket derivation: ADDED — 5-step pre-build procedure using decision tree on K4 vs outcome to find empirical split points.
- Tab 3 relabeled: "Research findings panel — informational only. No trade rejected by Vince. Trade count never reduced. TAKE/SKIP is Vicky's domain."
- Items 4 (55% accuracy gate) and 5 (LSTM suboptimal): DROPPED — overstated concerns.

**State changes:**
Two files modified: docs/VINCE-V2-CONCEPT-v2.md (3 sections updated), SPEC-C-VINCE-ML.md (Tab 3 relabeled). Overall spec assessment: on the right track, no structural redesign needed.

**Open items recorded:**
- User decision: SPEC-C vs VINCE-V2 classifier conflict on Tab 3 — RESOLVED (informational only)

**Notes:**
8 items already confirmed correct (always show N, complement alongside, trade count floor, two-sided Monte Carlo, ETD tracking, strategy-agnostic plugin, XGBoost as adversarial auditor, 60/20/20 split with holdout). Assessment: gaps were missing permutation correction, missing explicit fitness function, architectural contradiction (resolved), and regime buckets without derivation method.

---

## File 19: 2026-02-24-weex-screener-scope.md

**Date:** 2026-02-24
**Type:** Scope log / screener pivot

**What happened:**
Session that built Screener v1 (historical backtest ranker, 22/22 tests) then determined it was the wrong approach. Scoped WEEX Live Market Screener as the correct tool: live indicator state for all WEEX futures, not a backtester.

**Decisions recorded:**
- Screener v1 (historical PnL ranker): WRONG — backwards-looking, dominated by regime noise, TradingView does this better
- WEEX Live Market Screener: correct approach — normalised ATR ratio, Four Pillars signal state, setup detection
- WEEX API confirmed: no auth for market data, 500 req/10s rate limit
- Symbol format: contracts = cmt_btcusdt, OHLCV = BTCUSDT_SPBL (append _SPBL)
- Import confirmed: compute_signals_v383 from signals.four_pillars_v383_v2, minimum bars = 69 (60 for K4 + 9 for D smooth)

**State changes:**
Screener v1 exists but wrong approach. WEEX screener v1 scoped: 3 files planned. Columns defined. Filters defined. Sidebar controls defined.

**Open items recorded:**
- Confirm futures candles endpoint vs spot candles endpoint at build time
- Next session: scope first, then build

**Notes:**
Three key WEEX screener metrics not available on TradingView: (1) Normalised ATR ratio (ATR/price) for cross-coin comparison, (2) Four Pillars signal state (all 4 stoch values + cloud state), (3) Setup detection (coin in pullback with signals ready).

---

## File 20: 2026-02-25-bingx-connector-session.md

**Date:** 2026-02-25
**Type:** Session log / live bot debugging

**What happened:**
Multi-session log (5 sessions). Bot launched, encountered blocking bugs, fixed progressively. Critical finding: E1-ROOT (urlencode in bingx_auth.py line 31) was the #1 blocker — ALL order attempts had been failing with signature verification error because urlencode encoded JSON special chars while BingX computes signature on raw string.

**Decisions recorded:**
- Fix SB1: leverage API loop over LONG/SHORT (not BOTH — BingX hedge mode)
- Fix SB2: ohlcv_buffer_bars 200→201 (off-by-one, signals could NEVER fire — 200 >= 201 always False)
- Fix A1: recvWindow added to auth (5s default → timestamp errors every ~5h)
- Fix E1: json.dumps separators=(',',':') in executor.py
- Fix E1-ROOT: bingx_auth.py line 31 — urlencode replaced with manual &-join (no encoding of JSON chars)
- Fix M1: reconcile API error check (no silent wipe on error)
- Fix M2: absolute log path to logs/YYYY-MM-DD-bot.log
- UTC+4 fix: custom UTC4Formatter, Telegram timestamps UTC+4
- Data integrity timestamps (entry_time, session/trade timestamps, daily reset check): KEPT in UTC

**State changes:**
Bot running on BingX VST demo in hedge mode. 67/67 tests passing. 3 open risks remain: S01/S02 (cold-start false signal guard), S08 (multi-slot vs single-slot PnL not comparable — must fix before Step 3 go-live), E2/F1/D1 (deferred low severity). Bot confirmed running: warmup 201 bars all 3 coins, Telegram startup alert sent, first bar evaluated (No signal).

**Open items recorded:**
- Next signal to confirm E1-ROOT fix end-to-end
- Add 37 more coins to config.yaml (wider signal net)
- Increase max_positions if needed
- Switch back to 5m once trade confirmed
- Step 1 complete once first A/B demo trade placed

**Notes:**
E1-ROOT explanation: simple params (leverage, margin, positions) have no special chars — urlencode doesn't change them, those calls always worked. Order call includes stopLoss JSON with special chars — urlencode encodes {, ", :, , — signatures never matched. This explains why startup worked but every order attempt failed.

---

*End of batch ordered-07. 20 files processed.*
