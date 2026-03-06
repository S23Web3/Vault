# Batch 06 Research Findings
**Files:** 20 logs from 2026-02-16 and 2026-02-17
**Processed:** 2026-03-05

---

## 2026-02-16-bbw-v2-layer4-5-prebuild-analysis.md
**Date:** 2026-02-16
**Type:** Planning / Architecture spec

### What happened
Pre-build architecture review and analysis for BBW V2 Layers 4, 4b, and 5. Documented the corrected architecture after identifying that BBW V1 was fundamentally flawed (simulated trades instead of analyzing backtester results). Established data flow: Backtester v385 results → Layer 4 (BBW Analyzer V2) → Layer 4b (Monte Carlo V2) → Layer 5 (Report V2) → VINCE ML (separate component).

Defined the primary metric as BE+fees rate (% trades with pnl_net >= 0), contrasting with win rate (gross PnL > 0). Documented five math validations, syntax error prevention rules (Windows path safety, DataFrame merge alignment, groupby index handling, column name consistency), and a test strategy of 40+ unit tests per layer. Specified 5 CSV output files from Layer 5 and detailed input/output contracts for all three layers.

### Decisions recorded
- BBW V1 was wrong: it simulated trades; V2 analyzes real backtester results
- Direction source is Four Pillars strategy, NOT BBW testing
- VINCE is a separate ML component, NOT Layer 6
- BBW purpose is data generator for VINCE training
- BE+fees rate is the primary metric (pnl_net >= 0, not pnl_gross > 0)
- Bias threshold: 5% difference between LONG and SHORT rates
- min_trades_per_group default: 100

### State changes
- Document created as pre-build reference
- Architecture corrected from V1 misconceptions
- Data contracts specified for Layer 4 → 4b → 5 handoffs

### Open items recorded
- Layer 4 build execution (7-8 hours estimated)
- Layer 4b build (5-6 hours estimated)
- Layer 5 build (6-7 hours estimated)

### Notes
- This corrects errors from earlier sessions where BBW was described as having 6 layers; VINCE is confirmed separate. Also establishes that trade direction comes from Four Pillars strategy, not BBW states.

---

## 2026-02-16-bbw-v2-layer4-build-journal.md
**Date:** 2026-02-16
**Type:** Build session

### What happened
Complete build journal for `research/bbw_analyzer_v2.py` (Layer 4). Documented all 10 phases of construction using test-first development. The journal starts with a pre-build checklist (showing "BUILD NOT STARTED") but the final build summary confirms all 10 phases completed.

Key phases completed:
- Phase 1 (Input Validation): validate_backtester_data() and validate_bbw_states(), 10/10 assertions PASS
- Phase 2 (Data Enrichment): enrich_with_bbw_state() with left join to preserve all trades, 33/33 PASS
- Phase 3+4 (Grouping + Metrics): group_by_state_direction_lsg(), calculate_group_metrics(), 62/62 PASS
- Phase 5 (Best Combo): find_best_lsg_per_state_direction(), 91/91 PASS
- Phase 6 (Directional Bias): detect_directional_bias() with 5% threshold, 125/125 PASS
- Phase 7 (Main Pipeline): analyze_bbw_patterns_v2() orchestrator + BBWAnalysisResultV2 dataclass, 162/162 PASS
- Phase 8 (Debug Script): scripts/debug_bbw_analyzer_v2.py with 10 sections
- Phase 9 (Sanity Check): scripts/sanity_check_bbw_analyzer_v2.py — 2000 trades, 0.24s runtime, all validations PASS
- Phase 10 (Documentation): All functions have docstrings

Final results: 44 unit tests, 162 assertions, all PASS. Runtime 0.24s for 2000 trades (~8,333 trades/sec). 3 syntax errors encountered and fixed (unicode chars, invalid BBW state names, missing symbol column).

### Decisions recorded
- Left join used for enrichment (preserves all trades)
- Categorical dtypes for grouping performance
- Sort → GroupBy → First pattern for "best per group"
- Empty DataFrame handling propagates correctly through pipeline
- MISSING_DIRECTION is a valid bias state (some states may only work one direction)
- Tie-breaking: first in sort order (stable, deterministic)

### State changes
- research/bbw_analyzer_v2.py created (~640 lines)
- tests/test_bbw_analyzer_v2.py created (~1250 lines, 44 tests, 162 assertions)
- scripts/debug_bbw_analyzer_v2.py created (~505 lines)
- scripts/sanity_check_bbw_analyzer_v2.py created (~375 lines)
- Sanity check generated 4 CSV output files in results/bbw_analyzer_v2_sanity/

### Open items recorded
- Layer 4b (Monte Carlo V2) build next
- Layer 5 build after 4b complete

### Notes
- The journal template section (showing "NOT STARTED") is the pre-build placeholder; the actual build log entries confirm all 10 phases were completed within the same session.
- CODE VERIFICATION: File path referenced as `research/bbw_analyzer_v2.py` in project root.

---

## 2026-02-16-bbw-v2-layer4b-build-journal.md
**Date:** 2026-02-16
**Type:** Build session (journal header only — build not yet executed)

### What happened
Build journal template created for `research/bbw_monte_carlo_v2.py` (Layer 4b). Status marked "BUILD STARTED" but no build log entries are present — the file contains only the journal header with architecture overview, build plan, input/output contracts, core logic definitions (bootstrap PnL function, permutation DD function, verdict classification function), math validation trackers (all PENDING), and a files-to-create list.

Key design documented:
- Bootstrap: Resample with replacement 1000 sims, extract 5th/95th percentile CI
- Permutation DD: Shuffle sequence, compare real DD to permuted p95
- Verdict logic: INSUFFICIENT → COMMISSION_KILL → FRAGILE → ROBUST

Layer 4b V2 vs V1 difference: V1 validated simulated trades; V2 validates real backtester results.

### Decisions recorded
- Bootstrap uses 1000 simulations by default
- 90% CI (5th and 95th percentiles)
- Verdict priority order: INSUFFICIENT → COMMISSION_KILL → FRAGILE → ROBUST
- COMMISSION_KILL: ci_upper < 0 (even best-case scenario loses money)
- FRAGILE: ci_lower < 0 OR dd_fragile
- ROBUST: ci_lower >= min_net_expectancy (default $1.00)

### State changes
- Build journal file created as template
- No code files created yet in this journal

### Open items recorded
- All 7 build phases pending execution
- 30+ unit tests to write
- Bootstrap CI coverage validation
- Permutation DD detection validation
- Verdict logic validation

### Notes
- The 2026-02-17 bbw-project-completion-status.md log confirms Layer 4b was eventually completed (45/45 tests PASS, 56/56 debug PASS), so the actual build happened in a subsequent session not captured in this journal.

---

## 2026-02-16-bbw-v2-layer5-logic-analysis.md
**Date:** 2026-02-16
**Type:** Architecture spec / pre-build analysis

### What happened
Pre-build logic verification for Layer 5 (`research/bbw_report_v2.py`). Documented function-by-function logic for all 6 functions: aggregate_directional_bias(), generate_be_fees_success_tables(), create_vince_features(), analyze_lsg_sensitivity(), generate_state_summary(), and generate_vince_features_v2() orchestrator.

Three critical logic issues identified:
1. Column name mismatch: Layer 4 uses `bbw_state_at_entry`, Layer 4b uses `bbw_state` — Layer 5 must standardize
2. Verdict encoding includes "MARGINAL" which doesn't exist in Layer 4b output (fix: remove MARGINAL)
3. Missing edge case handling for states with only one direction and NaN correlations

VINCE feature output includes: state ordinal encoding, direction binary, bias alignment, bias strength, LSG parameters, verdict ordinal, sample weight (ROBUST=1.0, others=0.5). Target variables: be_plus_fees_rate, avg_net_pnl, sharpe, verdict.

4 questions documented for user approval before build.

### Decisions recorded
- Layer 5 should accept both `bbw_state_at_entry` and `bbw_state` column names
- NEUTRAL bias: feature_bias_aligned = 0 (no alignment bonus)
- Missing verdict: use "UNKNOWN" (not raise error)
- State quality: categorical HIGH_QUALITY/MIXED/DEAD
- MARGINAL verdict removed from encoding dict
- Recommended build order: fix column name issue first, then Functions 1-5, then orchestrator

### State changes
- Analysis document created
- No code written yet
- 4 logic issues identified and resolved in spec

### Open items recorded
- User must approve 4 logic questions before build
- 48 unit tests to write (~120 assertions)
- 7-section debug script needed

### Notes
- This log establishes the spec for Layer 5 which was built on 2026-02-17.

---

## 2026-02-16-full-project-review.md
**Date:** 2026-02-16 15:45 GST
**Type:** Session log / project review

### What happened
Comprehensive project review intended for mobile reading. Covers: Four Pillars strategy components (all 4 pillars: Ripster EMAs, AVWAP, Quad Rotation Stochastics, BBWP), trade lifecycle mechanics (SL phases, TP logic, multi-slot position management), commission and rebate model, full BBW Pipeline status (Layers 1-4b COMPLETE, Layer 5 IN PROGRESS), VINCE ML architecture (9 modules), training data strategy (hybrid split 280/40/79), and critical path timeline.

Key findings reported:
- BBW Monte Carlo RIVERUSDT results: 6/7 states COMMISSION_KILL, 1 state FRAGILE (RED_DOUBLE, net_exp=$10.90)
- Commission drag: avg gross exp $5.22/trade, avg net exp -$1.92/trade, commission drag $7.14/trade
- $8 RT commission kills edge on 6/7 BBW states
- Fix required: BE raise restoration reduces loser count → improves net_exp

Known bug documented: AVWAP trail not ratcheting properly in v3.9, location: `engine/exit_manager.py` lines ~200-250.

### Decisions recorded
- VINCE training data split: 280 train (53%), 40 val (10%), 79 test (20%, FROZEN), remaining future reserve
- splits.json created ONCE before any training, never modified
- Test set: 79 coins, NEVER loaded during development
- 5-fold cross-validation on training set
- Monte Carlo verdicts filter training data: COMMISSION_KILL states excluded entirely
- Data augmentation: bootstrap within-state trades + BBWP noise injection (±2%) for training only

### State changes
- Document created as reference/review
- No code changes in this session

### Open items recorded
- BBW Layer 5 completion (this week)
- Dashboard 5m validation + AVWAP trail bug fix
- Restore BE raise in backtester
- Generate splits.json
- VINCE Module 3 build (next week)
- Cloud 4 trailing exit (week 3)

### Notes
- Confirms: "NO LAYER 6" — VINCE is separate component, not part of BBW

---

## 2026-02-16-portfolio-bugfix.md
**Date:** 2026-02-16
**Type:** Build session (two sessions)

### What happened
Two AFK build sessions fixing dashboard portfolio bugs.

**Session 1:** Two bugs fixed via `scripts/build_portfolio_bugfix.py` (5 patches):
- BUG A: Run Portfolio Backtest re-randomizes coin list — fix: store port_symbols in session_state["port_symbols_locked"] when Run clicked; added Reset Selection button
- BUG B: "Best Equity" / "Worst DD" metrics confusing — fix: renamed to "Peak Net Profit" (+$X from baseline) and "Worst Drawdown" (% and $ amount), added help tooltips

**Session 2:** Capital Model Consistency Fix via `scripts/build_capital_mode_fix.py` (10 patches):
- 7 data consistency bugs found in Shared Pool mode: per-coin metrics table, drill-down trades, trading volume section, daily volume stats, Net P&L after rebate, Total Trades metric, and per-coin monthly P&L all used unconstrained (unfiltered) data even after capital constraints rejected trades
- Root cause: capital_model.py rebuilt equity curves but left trades_df and metrics dict untouched
- Fix: Added `_rebuild_metrics_from_df()` helper, filtered trades_df to accepted-only, rebuilt metrics for adjusted coin results

### Decisions recorded
- Lock coin selection on Run button click, clear lock on Back button
- Metrics display must use accepted-only data in Shared Pool mode

### State changes
- scripts/build_portfolio_bugfix.py created
- scripts/build_capital_mode_fix.py created
- Both build scripts: BUILD READY, NOT EXECUTED (user runs)

### Open items recorded
- User must run both build scripts
- Validation checklists provided for both

### Notes
- Status at session end: BUILD READY, NOT EXECUTED for both.

---

## 2026-02-16-portfolio-v3-audit.md
**Date:** 2026-02-16
**Type:** Audit session (multiple sub-sessions)

### What happened
Multi-session audit and rebuild of dashboard portfolio enhancement utilities. Started with user reporting "something feels off" about the v2 build script.

**Audit Phase:** Read build_dashboard_portfolio_v2.py and cross-referenced against actual engine output (backtester_v384.py, position_v384.py, dashboard.py). Found 9 bugs:
- BUG 1 (CRITICAL): Capital model was decorative — returned original pf_data unchanged, rejection logic had zero effect
- BUG 2 (CRITICAL): Bar indices are per-coin local, not master_dt coordinates — caused incorrect overlap detection
- BUG 3 (CRITICAL): MFE used in signal strength = look-ahead bias (MFE only known after exit)
- BUG 4 (MEDIUM): rebate column doesn't exist in trades_df
- BUG 5 (MEDIUM): entry_dt column doesn't exist in trades_df (only entry_bar integer)
- BUG 6 (MEDIUM): Sortino annualized by trade count not bar count
- BUG 7 (MEDIUM): Capital efficiency used unconstrained values
- BUG 8 (LOW): be_raised not in trades_df
- BUG 9 (LOW): Test suite used fabricated data columns (entry_dt, rebate) masking integration failures

**V3 Build:** Created `scripts/build_dashboard_portfolio_v3.py` (~1500 lines) fixing all 9 bugs. Key fixes:
- Capital model: rebuild equity curves by subtracting rejected trade P&L
- Bar mapping: `_map_bar_to_master()` maps per-coin bar indices to master_dt via datetime_index searchsorted
- Signal strength: grade-only priority (no MFE)
- Test suite: realistic data structures matching actual _trades_to_df() output

**Session 2 continuation:** Tests confirmed 81/81 PASSED, debug ALL PASSED. Build script synced.

**Session 2b:** Created `scripts/build_dashboard_integration.py` with 6 patches to wire utilities into dashboard_v2.py.

### Decisions recorded
- Capital model must be post-processing (can't modify engine behavior)
- All cross-coin comparisons must map through datetime_index to master_dt
- Tests must use data structures from actual engine, not synthetic equivalents
- Look-ahead bias: only use entry-time information (grade, ATR, price levels, signals) for prioritization
- Integration not done automatically; requires separate integration build script

### State changes
- scripts/build_dashboard_portfolio_v3.py created (1500 lines)
- 8 utility files created by v3 build (utils/portfolio_manager.py, coin_analysis.py, pdf_exporter.py, capital_model.py, tests/, debug scripts)
- 81/81 tests PASSED (confirmed by user)
- FILE-INDEX.md updated with v3 reference
- scripts/build_dashboard_integration.py created (6 patches)

### Open items recorded
- User must run build_dashboard_integration.py to wire utils into dashboard
- Dashboard integration not started
- PDF dependency: pip install reportlab
- 5 open questions for user (integration timing, capital mode default, rejected trade visibility, PDF missing features, BBW integration)

### Notes
- Critical insight: backtester is NOT a portfolio engine; it's single-coin with results merged post-hoc. Capital model is always post-processing.

---

## 2026-02-16-project-status-data-strategy.md
**Date:** 2026-02-16 15:30 GST
**Type:** Session log / strategy planning

### What happened
Eagle-eye project status check combined with VINCE data preservation strategy planning. Corrected earlier error where Claude had described BBW as having 6 layers (Layer 6 = LLM analysis). User confirmed BBW has 5 layers only, VINCE is separate.

Data preservation analysis prompted by user concern: "I don't want VINCE to burn through my limited data and then have data bias." Documented recommended hybrid split strategy and data inventory (~42M bars, 399 coins × ~1 year × 5m).

Key comparison table for split strategies:
- No split: EXTREME bias risk
- Simple 80/20: High risk
- Hybrid recommended (53% train): Low risk
- Overly conservative (40%): Low but wasteful

### Decisions recorded
- Hybrid split: 280 train (53%), 40 val (10%), 79 test (20%, FROZEN), remaining future reserve
- Time-based walk-forward split REJECTED (market regime shifts would invalidate test distribution)
- splits.json written ONCE before any training, never modified
- Test coins NEVER loaded during development
- 5-fold CV on training set (224 train, 56 validate per fold)
- COMMISSION_KILL states excluded from training entirely
- Data augmentation: bootstrap within-state + BBWP noise injection (±2%, training only)

### State changes
- Architecture correction logged: BBW = 5 layers, VINCE = separate
- Strategy document created
- No code changes

### Open items recorded
- Complete BBW Layer 5
- Generate splits.json (280/40/79 allocation)
- Restore BE raise in backtester
- Run 400-coin sweep
- Build VINCE Module 3 (next week)

### Notes
- This log contains the same split numbers (280/40/79) as the full-project-review.md from the same day, confirming the decision was made and documented consistently.

---

## 2026-02-16-strategy-actual-implementation.md
**Date:** 2026-02-16
**Type:** Reference documentation

### What happened
Accurate documentation of the Four Pillars strategy as actually implemented in v3.8.4, sourced from signals/state_machine.py and signals/four_pillars.py. Covers: signal pipeline architecture, four stochastic components (stoch_9 entry trigger, stoch_14 primary confirmation, stoch_40 divergence, stoch_60 macro), Ripster EMA clouds (Cloud 2: 5/12 for re-entry, Cloud 3: 34/50 mandatory directional filter, Cloud 4: 72/89 planned trailing), ATR calculation (Wilder's RMA), two-stage state machine (Stage 0: Idle, Stage 1: Setup window max 10 bars), grade classification (A/B/C), re-entry system (Cloud 2 within 10 bars), ADD signals (not used in backtester v384).

Key corrections to common misconceptions documented:
- AVWAP NOT used for entries (exits only)
- D signal is optional filter, not a signal
- BBW states do not affect entry signals (v4 integration planned)
- All stochastics are raw K, no smoothing

### Decisions recorded
- Cloud 3 filter is NON-NEGOTIABLE and ALWAYS ENFORCED for A/B grades
- Grade C bypasses Cloud 3 directional filter (only requires price outside cloud)
- 10-bar setup window max
- D-line filter disabled by default

### State changes
- Reference document created
- No code changes

### Open items recorded
- ADD signals: reserved for future pyramiding logic (signal generated but not acted upon in v384)
- Cloud 4 trailing: planned for v3.9.1

### Notes
- This is the definitive strategy reference for v3.8.4, intended to correct prior misconceptions.

---

## 2026-02-16-trade-flow-uml.md
**Date:** 2026-02-16 15:50 GST
**Type:** Reference documentation (Mermaid UML diagrams)

### What happened
10 Mermaid UML diagrams created for project architecture and workflow visualization, intended for mobile review and Obsidian rendering. Diagrams cover:
1. Trade Lifecycle State Machine (Idle → Signal → Grade → Entry → SL phases)
2. Entry Grade Decision Tree (Quad Stoch → Cloud 3 → AVWAP → BBW → Grade A/B/C)
3. Stop Loss Lifecycle Flow (Initial → BE Raise → AVWAP Trailing)
4. SL Movement Over Time (numbered example: entry $100, ATR $2.50, SL progression)
5. ADD Signal Flow (sequence diagram)
6. System Architecture Component Diagram (all layers from data to live trading)
7. Critical Path Timeline (Gantt chart Feb-Mar 2026)
8. Commission and Rebate Flow
9. Data Split Strategy (280/40/79 with 5-fold CV)
10. Multi-Slot Position Management (sequence diagram)

### Decisions recorded
- None (documentation only)

### State changes
- Document created with 10 Mermaid diagrams

### Open items recorded
- None recorded in this file

### Notes
- Diagram 2 (Entry Grade Decision Tree) shows AVWAP and BBW influencing grade classification, which conflicts with strategy-actual-implementation.md which states AVWAP is only for exits. This may reflect a planned future state vs current implementation.

---

## 2026-02-17-bbw-project-completion-status.md
**Date:** 2026-02-17
**Type:** Session log (multiple sessions)

### What happened
Multi-session log covering 3 sessions on 2026-02-17:

**Session 1 (Morning):** BBW remaining build completed. Build script `scripts/build_bbw_remaining.py` generated 9 files, 45/45 tests PASS:
- research/coin_classifier.py (KMeans k=3-5 with silhouette selection, tiers by avg_atr_pct)
- research/bbw_ollama_review.py (optional LLM review of Layer 5 CSVs, NOT a pipeline layer)
- scripts/run_bbw_simulator.py (CLI wiring L1-L5 end-to-end)
- Plus 6 test + debug scripts

Smoke test PASS: RIVERUSDT 32,762 bars, 21.2s, 11 files written, 0 errors.

Bug fix: coin_classifier duplicate processing — glob matched both _1m and _5m files. Fixed with `glob("*_1m.parquet")` + seen_symbols dedup guard.

Layer 6 clarification confirmed: Layer 6 = ML/Vince = SEPARATE PROJECT. bbw_ollama_review.py is optional utility, not a layer. MEMORY.md updated.

**Session 2 (Afternoon):** Summarized BBW project status, critical path timeline, and pending tasks. Dashboard v3.9.1 confirmed stable (0 rejections, commission math validated).

**Session 3 (~19:03 UTC):** BBW V2 pipeline bug fixes and run_bbw_v2_pipeline.py created.

Bugs fixed:
1. bbw_analyzer_v2.py: column names corrected (bbwp_state/bbwp_value not bbw_state/bbwp), validators relaxed, timestamp merge changed to pd.merge_asof
2. bbw_report_v2.py: mc_result=None guard, validate_report_inputs no longer raises on empty state_verdicts
3. scripts/run_bbw_v2_pipeline.py created as bridge script loading portfolio CSV, adapting columns, running L4v2→L4bv2→L5

Run 1 (without rebate): ROBUST=0, FRAGILE=3, COMMISSION_KILL=11 (false positive)
Run 2 (with rebate --rebate-rate 0.70): ROBUST=8, FRAGILE=6, COMMISSION_KILL=0 — 14 feature rows for VINCE

VINCE feature results: BLUE_DOUBLE and MA_CROSS_UP = HIGH_QUALITY (both directions ROBUST). SHORT bias dominant in RED/RED_DOUBLE/MA_CROSS_DOWN/NORMAL/MA_CROSS_UP.

Output files: vince_features.csv (14 rows), directional_bias.csv, be_fees_success.csv, lsg_sensitivity.csv (empty, single LSG), state_summary.csv written to results/bbw_v2/

### Decisions recorded
- BBW project declared COMPLETE — both pipeline tracks functional
- Daily rebate must be included in pnl_net calculation for correct COMMISSION_KILL verdicts
- Layer 6 = VINCE = SEPARATE project (hard rule added to MEMORY.md)
- bbw_ollama_review.py = optional utility, NOT a pipeline layer

### State changes
- research/coin_classifier.py created
- research/bbw_ollama_review.py created
- scripts/run_bbw_simulator.py created
- research/bbw_analyzer_v2.py patched (3 fixes)
- research/bbw_report_v2.py patched (2 fixes)
- scripts/run_bbw_v2_pipeline.py created (new bridge script)
- vince_features.csv generated: 14 rows
- BBW project status changed from IN PROGRESS → COMPLETE

### Open items recorded
- Update UML diagrams (mark all layers L1-L5 complete, add CLI entry point)
- Generate coin_tiers.csv
- Multi-coin BBW sweep (top 10)
- Deploy VINCE ML staging
- MC result caching before 400-coin sweep

### Notes
- COMMISSION_KILL=11 in Run 1 was a false positive caused by missing daily rebate in CSV pnl_net. After applying rebate correction, results shifted dramatically to ROBUST=8.

---

## 2026-02-17-dashboard-v391-audit.md
**Date:** 2026-02-17
**Type:** Build session (5 sessions)

### What happened
Multi-session audit and rebuild resulting in Dashboard v3.9.1. Root cause investigation: Pool P&L showed -$9,513 while per-coin sum showed +$4,656.

**Session 1 (Audit):** Found root causes of discrepancy:
- E1 (Engine): SL/TP/Scale-out exits charged taker instead of maker — ~$6 overcharge per trade × ~1145 trades = ~$6,870 overcharge. Fix: maker=True on 3 lines (144, 174, 407 of backtester_v384.py)
- C1 (Capital Model, ROOT CAUSE): Scale-out trades treated as separate pool positions — one $500 position with 2 scale-outs consumes $1,500 in pool margin instead of $500
- C2 (Capital Model): Double margin deduction in available calculation
- D1-D7: Display-level bugs (wrong baselines, hardcoded 10000.0, DD% against wrong baseline)

**Session 2:** Engine fix applied (maker=True). Build script rewritten: capital_model_v2.py with position grouping via `_group_trades_into_positions()`, exchange-model pool with separate balance and margin_used. Dashboard: 11 patches. 15/15 patch targets verified.

**Session 3 (Post-Build Audit, 3-coin test):** Pool P&L = +$5,975 but 195 trade rejections. New bugs:
- P1: Pool simulation doesn't include rebate (only adds net_pnl on close)
- P2: "Net P&L (after rebate)" label confusing → renamed to "True Net P&L"
- P3: Discrepancy between drill-down sum and True Net P&L (stale state)

**Session 4 (Daily Rebate Fix):** Critical fix for Bug C3 — daily rebate settlement in pool simulation. Without it, pool drains to $491 with 195 rejections (10.5%). With daily rebate settlement: 0 rejections, pool stays above $5,762, final pool $12,480. Implementation: check 5pm UTC boundary before each bar, credit daily_comm × rebate_pct to balance. Also: combined trades CSV export added (PATCH 14), PDF per-coin chart rebasing fixed.

Commission model validation across 3 portfolio sizes: blended rate stable at ~0.0503-0.0505%/side, rebate ~67.4-67.5% (shortfall = unsettled last-day commission, acceptable).

**Session 5:** Build script `scripts/build_uml_diagram.py` created for Mermaid UML diagrams (6 diagrams: Component, Class, Portfolio Sequence, ER, Commission Flow, Shared Pool State Machine).

### Decisions recorded
- Exchange model: track positions (not individual trade records) through pool
- Position = (coin, entry_bar) key, collapses all scale-outs
- Separate balance and margin_used tracking (no double deduction)
- Daily rebate must settle intra-simulation at 5pm UTC boundaries
- "True Net P&L" = net_pnl + rebate (renamed from confusing "Net P&L after rebate")
- DD% = cash-on-hand drawdown from realized balance only (documented as known limitation)

### State changes
- engine/backtester_v384.py modified: maker=True on lines 144, 174, 407
- utils/capital_model_v2.py generated (537 lines, 7 functions)
- utils/pdf_exporter_v2.py generated (330 lines)
- scripts/dashboard_v391.py generated (2338 lines, 14 patches)
- scripts/build_dashboard_v391.py rewritten (916 lines)
- scripts/debug_pool_balance_v2.py created (543 lines)
- scripts/build_uml_diagram.py created (789 lines)
- Dashboard version: v3.9 → v3.9.1 (STABLE)

### Open items recorded
- 3 known minor issues documented (Net P&L vs per-coin sum gap ~$321, BANKUSDT positive Net but negative Sharpe/PF, DD% is cash-on-hand only)
- User needs to verify P3 discrepancy after rebuild

### Notes
- C1 (scale-out grouping) was the ROOT CAUSE of the -$9,513/-+$4,656 discrepancy. This is the most critical bug found in this session batch.

---

## 2026-02-17-pdf-diagram-alignment.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
User reported UML diagrams in BBW-V2-UML-DIAGRAMS.md were "not aligned per page" when exported to PDF. Created PDF-optimized version `BBW-V2-UML-DIAGRAMS-PDF.md` with explicit page breaks between each diagram, simplified diagrams (max 10 nodes, short labels, removed verbose subgraphs), one diagram per page, and summary tables at end.

Layout defined: 10 pages total — pages 1-8 each have one diagram, pages 9-10 have summary tables. Size reduction: ~40% smaller Mermaid code. Content preserved via tables for details moved out of diagrams.

### Decisions recorded
- Each diagram on separate page (explicit page-break-after divs)
- Max 10 nodes per diagram for PDF compatibility
- Short node labels (≤3 words)
- Tables for detailed data instead of diagram annotations

### State changes
- docs/bbw-v2/BBW-V2-UML-DIAGRAMS-PDF.md created

### Open items recorded
- User must test PDF export and report remaining issues

### Notes
- None

---

## 2026-02-17-pdf-export-optimization.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
User reported BUILD-VINCE-ML.pdf was "crooked" and needed reformatting. Rewrote BUILD-VINCE-ML.md with PDF-optimized structure: Table of Contents, 8 numbered sections, 40+ page break hints, code blocks max 40 lines, 5 tables for CLI args, shorter paragraphs, visual hierarchy.

Also created BBW-V2-ARCHITECTURE.md as a new PDF-friendly version of the architecture document: simplified Mermaid diagram, prose descriptions, status tables, glossary.

### Decisions recorded
- PDF best practices applied: page breaks after major sections, tables max 5 columns, code blocks max 40 lines, clear heading hierarchy, simplified Mermaid diagrams, generous white space

### State changes
- BUILD-VINCE-ML.md rewritten (PDF-optimized)
- docs/bbw-v2/BBW-V2-ARCHITECTURE.md created (new)

### Open items recorded
- User must test PDF export of both files

### Notes
- None

---

## 2026-02-17-pdf-orientation-fix.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
Added landscape orientation for diagrams 2 (Data Flow Sequence) and 6 (VINCE Deployment) in BBW-V2-UML-DIAGRAMS-PDF.md, plus center alignment for all content. CSS block added with @page rules and .diagram-container class. Wrapped all content in centered divs.

Documented that @page CSS support varies by tool (wkhtmltopdf = good support; Chrome/Firefox print = limited). Provided 4 export methods and manual fallback instructions (rotate pages 2 and 6 in PDF viewer).

### Decisions recorded
- Pages 2 and 6 should be landscape orientation
- All diagrams centered horizontally
- wkhtmltopdf recommended for reliable @page support

### State changes
- docs/bbw-v2/BBW-V2-UML-DIAGRAMS-PDF.md modified: CSS added, content wrapped in divs, landscape markers added

### Open items recorded
- User must test CSS method and report if @page orientation works in Obsidian

### Notes
- None

---

## 2026-02-17-project-clarity-and-vince-architecture.md
**Date:** 2026-02-17 (Tuesday)
**Type:** Session log / architecture planning

### What happened
~45-minute session preparing for a funding meeting. User asked for clarity on 10 topics: 5-task breakdown, VINCE independence, trading engine architecture, Cloud 3 constraint flexibility, GUI concept, version chaos, BBW next steps, PyTorch/XGBoost build status, funding talking points, and "what if" capability.

Project state confirmed:
- State Machine v3.8.3: STABLE
- Backtester v3.8.4: STABLE (BE raise removed accidentally)
- Exit Manager v3.8.4: BUGGY (AVWAP trail not ratcheting)
- Dashboard v3.9: STABLE
- BBW Pipeline v2.0: Layers 1-4b COMPLETE, Layer 5 IN PROGRESS
- VINCE ML v0.0: SPEC ONLY, 0% built

VINCE independence analysis: VINCE is tightly coupled to Four Pillars (14 hardcoded indicator fields). Three options discussed:
- Option A (RECOMMENDED): Hybrid — VINCE-Core (strategy-agnostic) + VINCE-FourPillars (current)
- Option B: Full rebuild with abstract interfaces (rejected — 4-6 weeks, overengineering)
- Option C: Clone repository per strategy (accepted as short-term pragmatic)

5-task breakdown: (1) Update UML ~30min, (2) Generate coin_tiers.csv ~5min, (3) Multi-coin BBW sweep ~10min, (4) Deploy VINCE staging ~15min, (5) MC result caching ~1 session.

Cloud 3 flexibility: Currently hardcoded in state_machine_v383.py. Could be made configurable but would break grade logic — not recommended until strategy proven.

"What if" capability concept: VINCE could run counterfactual simulations (what if leverage=15 instead of 20?) by injecting different LSG and re-running MC simulation. Documented as future feature.

### Decisions recorded
- VINCE-FourPillars (tight coupling) accepted for now; VINCE-Core extraction deferred post-launch
- Cloud 3 constraint: keep hardcoded until strategy proven
- "What if" simulations: future feature after v1.0 deployed

### State changes
- Session log created
- No code changes

### Open items recorded
- Funding meeting tomorrow — talking points documented
- Tasks 1-5 ranked by priority (UML update highest for pitch)
- VINCE-Core extraction: 2-3 week project after live trading proven

### Notes
- Confirms VINCE is 0% built (spec only) as of 2026-02-17 morning.

---

## 2026-02-17-python-skill-update.md
**Date:** 2026-02-17
**Type:** Infrastructure / meta session

### What happened
Review and update of Python coding skill files across all locations. Added multiple new sections to both vault SKILL.md and user-level SKILL.md. Content added:

- Filename Etiquette: naming convention table, project directory structure, safe_write_path() versioning helper
- Debugging: logging over print, structured exception handling, debug script template, log level discipline table
- Testing (Enhanced): programmatic py_compile.compile() in build scripts with ERRORS list, unittest template, make_ohlcv() mock data helper, assert patterns with msg=
- Syntax Error Prevention: f-string join trap, triple-quoted string escaping rules, ast.parse() secondary validator
- Code Patterns: input validation, API rate limiting, OHLCV data validation, incremental processing, performance (parquet/vectorized)
- Trading System Specifics: commission calculation, UTC timestamps
- Code Review Checklist expanded from 11 to 28 items across 5 categories

Also added MEMORY.md hard rule: "PYTHON SKILL MANDATORY — Before writing ANY Python code, ALWAYS load the Python skill first."

### Decisions recorded
- Python skill is mandatory before any .py file work (rule added to MEMORY.md)
- Both skill locations synchronized with identical content

### State changes
- Vault/.claude/skills/python/SKILL.md: updated (sections added)
- C:/Users/User/.claude/skills/python/SKILL.md: created (new)
- MEMORY.md: hard rule appended
- Legacy python-trading-development.md left in place (to delete when ready)

### Open items recorded
- Delete legacy python-trading-development.md when ready

### Notes
- Only 2 Python skill locations found (user expected 3 — confirmed only 2 exist).

---

## 2026-02-17-uml-diagrams-creation.md
**Date:** 2026-02-17
**Type:** Build session (documentation)

### What happened
User requested proper UML diagrams for BBW V2 architecture. Previous document had too much prose. Created `docs/bbw-v2/BBW-V2-UML-DIAGRAMS.md` with 8 comprehensive Mermaid diagrams.

Layer 3 investigation: Read bbw_forward_returns.py and determined it's a pure function that adds 17 forward-looking metrics (fwd_10_max_up_pct, fwd_10_max_down_pct, fwd_10_close_pct, fwd_10_max_up_atr, fwd_10_max_down_atr, fwd_10_max_range_atr, fwd_10_direction, fwd_10_proper_move — same 8 for 20-bar window, plus fwd_atr). Integration decision: Layer 3 → Layer 5 (forward returns as VINCE features).

8 diagrams created:
1. Component Architecture
2. Data Flow Sequence
3. Layer 3 Output Schema
4. BBW State Transitions (7 states)
5. Class Diagram - Data Contracts
6. Deployment: VINCE Local → Cloud
7. Activity: 400-Coin Sweep
8. Component Interaction (file-level)

VINCE deployment strategy documented: Phase 1 local training on RTX 3060, Phase 2 cloud deployment (TBD: AWS/GCP/Azure/DigitalOcean), Phase 3 TradingView → n8n → VINCE cloud API → trade execution.

### Decisions recorded
- Layer 3 integration: Layer 3 → Layer 5 (forward metrics as VINCE training features)
- VINCE deployment: local first, then cloud

### State changes
- docs/bbw-v2/BBW-V2-UML-DIAGRAMS.md created (8 diagrams)

### Open items recorded
- User to review diagrams, validate Layer 3 → Layer 5 integration
- Decide on cloud platform for VINCE deployment
- Layer 5 build: include forward_metrics.csv export

### Notes
- Layer 3 was previously marked "COMPLETE" but had no downstream consumer (orphaned). This session resolved that by deciding Layer 3 feeds Layer 5.

---

## 2026-02-17-uml-logic-debugging.md
**Date:** 2026-02-17
**Type:** Build session (debugging)

### What happened
Debug session on BBW-V2-ARCHITECTURE.md diagrams. Found 4 logical flow issues:

1. Layer 3 Orphaned (CRITICAL): `L1 --> L2 --> L3 [DEAD END]` — no output connection
2. Missing Data Source: Layer 1 had no input shown (CACHE node added)
3. VINCE Feedback Loop Ambiguity: `VINCE --> BT` arrow unclear (training vs production)
4. Missing Data Flow Labels: arrows didn't specify what data passes between nodes

Created corrected version `BBW-V2-ARCHITECTURE-CORRECTED.md`:
- Added CACHE data source node
- Layer 3 marked as "Research - Not used by L4" (dotted line)
- VINCE split into training mode (solid arrow L5→VINCE) and production mode (dotted arrow VINCE-.->BT)
- All arrows labeled with data contracts

Documented component dependency matrix showing Layer 3 still has unclear downstream use.

### Decisions recorded
- Layer 3 status: requires user clarification (Options A/B/C/D presented)
- VINCE feedback loop: solid for training CSVs, dotted for future production use
- User decision required: Layer 3 integration choice

### State changes
- docs/bbw-v2/BBW-V2-ARCHITECTURE-CORRECTED.md created

### Open items recorded
- User to decide: Layer 3 integration option (A: Layer 3→L5, B: standalone, C: Layer 3→L4, D: remove)
- User to confirm: VINCE production mode (real-time service vs offline optimizer)

### Notes
- This file and uml-diagrams-creation.md from the same day give conflicting guidance on Layer 3 — the creation log decided Layer 3→Layer 5, but this debugging log still marks it as "requires clarification." Likely uml-logic-debugging.md was written before uml-diagrams-creation.md finalized the decision.

---

## 2026-02-17-vince-ml-strategy-exposure-audit.md
**Date:** 2026-02-17
**Type:** Audit session

### What happened
Security/IP audit of codebase to determine what is safe to share publicly. Triggered by user question about VINCE ML build exposing the Four Pillars strategy.

Two codebase agents scanned signals/ and ml/ directories plus build_staging.py.

Findings:
- signals/ (10 files): PROPRIETARY — NOT SAFE TO SHARE. Contains A/B/C/R grade entry logic, Kurisko Raw K stochastic settings (K1=9, K2=14, K3=40, K4=60), Ripster EMA cloud parameters (5/12, 34/50, 72/89), full signal pipeline. "Anyone with these files could fully replicate Four Pillars."
- ml/ (14 files): GENERIC — SAFE TO SHARE. Strategy-agnostic: features.py, meta_label.py, triple_barrier.py, purged_cv.py, bet_sizing.py, walk_forward.py, vince_model.py (PyTorch multi-task), xgboost_trainer.py, training_pipeline.py, etc. "Could plug into any strategy."
- scripts/build_staging.py: NOT SAFE (embeds exact stochastic settings and cloud parameters)
- scripts/dashboard*.py: NOT SAFE (parameter UI reveals all indicator settings)

### Decisions recorded
- ml/ directory safe to open-source as-is
- signals/ and all dashboard files: treat as confidential
- If open-sourcing backtester framework: replace signals/ with strategy interface/stub
- Strip all numeric defaults from dashboard before sharing

### State changes
- Audit document created
- No code changes

### Open items recorded
- No open items explicitly stated

### Notes
- Confirms ml/ directory contains 14 built files including vince_model.py (PyTorch multi-task model with tabular + LSTM + context branches). This is significant: as of 2026-02-17, ml/ files existed and were built, contradicting the project-clarity-and-vince-architecture.md file from the same day which says "VINCE ML v0.0: SPEC ONLY, 0% built." The audit found actual ML code in ml/ — likely build_staging.py deployed these files.
