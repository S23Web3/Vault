# Research Findings — Batch 05
**Files processed:** 20
**Date range covered:** 2026-02-14 to 2026-02-16
**Topic:** BBW Simulator Layers 1-5, Operational Audit, Dashboard v3.1, Vault Sweep Review

---

## 2026-02-14-bbw-full-session.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
Combined session log covering 5 areas of BBW simulator work: (1) UML diagram fixes for BBW-UML-DIAGRAMS.md (replaced tiny stateDiagram-v2 with readable flowchart LR, added color-coded zones, VINCE feature legend with 17 total features across 4 categories, MonteCarloValidator class); (2) Monte Carlo validation added as Layer 4b (bbw_monte_carlo.py, 1000 shuffles per BBW state, 95% CI on PnL/maxDD/Sharpe, overfit detection, 4 output CSVs, ~23 min runtime); (3) Ollama integration defined as Layer 6 with 6 integration points using 3 models (qwen3:8b fast, qwen2.5-coder:32b code review, qwen3-coder:30b deep); (4) Full architecture doc written (BBW-SIMULATOR-ARCHITECTURE.md, 6-layer pipeline, ~35 min total runtime); (5) Claude Code prompt written for Layer 1 (CLAUDE-CODE-PROMPT-LAYER1.md, 12KB, 5 tricky parts flagged); (6) Investopedia article reviewed and dismissed (no value above existing architecture); (7) Layer 1 (signals/bbwp.py) confirmed COMPLETE. Session also noted a context compaction violation — triggered without warning causing wasteful token-burning search outside vault.

### Decisions recorded
- Ollama integrated in simulator: Yes (Layer 6, post-computation reasoning)
- Models assigned: qwen3:8b (fast), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep)
- Monte Carlo: Yes (Layer 4b, 1000 sims, 95% CI)
- Total pipeline runtime: ~35 min for 399 coins
- Investopedia article: No value — already exceeded by existing architecture
- Layer 1 status: COMPLETE

### State changes
- BBW-UML-DIAGRAMS.md rewritten with 6 diagrams + legends
- BBW-STATISTICS-RESEARCH.md updated (Monte Carlo section + build sequence)
- BBW-SIMULATOR-ARCHITECTURE.md created (new, full 6-layer + Ollama)
- CLAUDE-CODE-PROMPT-LAYER1.md created (new, Claude Code build prompt)
- signals/bbwp.py confirmed built and tested

### Open items recorded
1. New chat needed — write CLAUDE-CODE-PROMPT-LAYER2.md for bbw_sequence.py
2. Layer 2 through Layer 6b not yet built (all NOT STARTED)
3. Context compaction rule violation — needs rule reinforcement

### Notes
- First log to confirm Layer 1 (signals/bbwp.py) as COMPLETE with 61/61 tests PASS
- VERIFICATION: signals/bbwp.py confirmed present on disk

---

## 2026-02-14-bbw-layer1-build.md
**Date:** 2026-02-14 (post-build timestamp 11:16 UTC)
**Type:** Build session

### What happened
Build log for Layer 1 of the BBW simulator: Python port of bbwp_v2.pine (264-line Pine v6 script) to signals/bbwp.py. Pre-build section documents scope (3 files to create), Pine Script references, and 7 known tricky parts (MA cross persistence stateful, percentrank manual implementation, operator precision differences, spectrum vs state boundaries, cross event vs persisted state, state string format, NaN handling). Post-build: 4 files created (tests/__init__.py, tests/test_bbwp.py with 11 tests, signals/bbwp.py, scripts/sanity_check_bbwp.py). 61/61 tests PASS. 2 bugs found and fixed: (1) _percentrank_pine() included current bar in window — corrected to use only previous length values; (2) Test thresholds too tight for NORMAL state distribution. Sanity check on RIVERUSDT 5m (32,762 bars): BBWP mean=48.8 (correct for uniform percentile), performance 101K bars/sec. Pine Script fidelity checklist fully verified.

### Decisions recorded
- percentrank: manual implementation matching Pine's "previous length values strictly less" semantics (not scipy)
- State strings: uppercase with underscores (BLUE_DOUBLE, MA_CROSS_UP)
- Spectrum strings: lowercase (blue, green, yellow, orange, red)
- 10 output columns with bbwp_ prefix

### State changes
- Created: tests/__init__.py (empty)
- Created: tests/test_bbwp.py (11 tests, ~300 lines)
- Created: signals/bbwp.py (~210 lines) — Layer 1 COMPLETE
- Created: scripts/sanity_check_bbwp.py

### Open items recorded
- Layer 2 (signals/bbw_sequence.py) — next build

### Notes
- Layer 1 state distribution on RIVERUSDT: NORMAL=17.9%, BLUE_DOUBLE=14.5%, MA_CROSS_UP=14.3%, BLUE=14.0%, MA_CROSS_DOWN=13.8%, RED_DOUBLE=13.2%, RED=12.4%
- VERIFICATION: signals/bbwp.py confirmed present on disk

---

## 2026-02-14-bbw-layer2-build.md
**Date:** 2026-02-14 (start 13:16 UTC, tests pass 13:22 UTC)
**Type:** Build session

### What happened
Build log for Layer 2 of the BBW simulator: signals/bbw_sequence.py (sequence tracker, 9 output columns). 4 files created in 6 minutes. One hotfix applied during build: SyntaxError in 3 generated files caused by Windows \Users path in docstrings triggering unicode escape error — fixed by replacing full Windows paths with relative paths in docstrings. Test results: 68/68 PASS. Debug validator: 148/148 PASS. Layer 2 speed: 961K bars/sec vs Layer 1's 97K bars/sec (sequence computation is vectorized). Color transitions on RIVERUSDT: 19.3% of bars. Skip detection: 0.9% (mostly blue<->yellow). Top pattern: YGB (17.1%) — contracting from yellow through green to blue. Blue runs longest (mean 8.9 bars), green shortest (mean 3.5).

### Decisions recorded
- None stated (implementation followed spec)

### State changes
- Created: signals/bbw_sequence.py (9 output columns)
- Created: tests/test_bbw_sequence.py (10 tests, 68 assertions)
- Created: scripts/sanity_check_bbw_sequence.py
- Created: scripts/debug_bbw_sequence.py (7 sections, 148 checks)

### Open items recorded
- Layer 3 (research/bbw_forward_returns.py) — next build (prompt needs 3 audit passes)

### Notes
- Hotfix documented: Windows paths in docstrings cause unicode escape SyntaxError in generated files — use relative paths only
- VERIFICATION: signals/bbw_sequence.py confirmed present on disk

---

## 2026-02-14-bbw-layer3-audit-pass3.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Third audit pass on BUILDS\PROMPT-LAYER3-BUILD.md before executing in Claude Code. Previous sessions ran pass 1 (7 bugs) and pass 2 (3 bugs). This pass found 6 additional issues: (1) HIGH — Test 9 proper_move used flat data (ATR=0, test meaningless) — changed to alternating volatile bars; (2) HIGH — Debug Section 2 bar 16 was in NaN zone for window=4 — fixed with explicit second call using windows=[3]; (3) MEDIUM — bar 16 expected values not pre-computed — fully pre-computed all 10 values; (4) LOW — missing explicit research/ directory creation — added pathlib mkdir; (5) INFO — columns dropped (intentional, documented); (6) INFO — NaN tolerance strict (intentional, documented). All HIGH/CRITICAL bugs fixed. Cumulative 16 bugs across 3 passes: 4 CRITICAL, 4 HIGH, 4 MEDIUM, 2 LOW, 2 INFO. Math for bar 15 (window=4) and bar 16 (window=3) fully hand-verified. Prompt declared ready for Claude Code.

### Decisions recorded
- Layer 3 NaN tolerance: strict (100% valid bars required) — intentional, relaxable later
- Columns fwd_N_valid_bars, fwd_N_bbw_valid: deferred to pipeline orchestrator (not in Layer 3)
- research/ directory: must be explicitly created before research/__init__.py write

### State changes
- BUILDS\PROMPT-LAYER3-BUILD.md: 4 edits (Test 9, Debug bar 16, mkdir step, design decisions section)
- No Layer 3 code built yet

### Open items recorded
- Execute Layer 3 build in Claude Code using the audited prompt

### Notes
- Cumulative audit count across 3 passes: 16 total issues for Layer 3 prompt
- Math verification for bar 16 (window=3): ATR=5.0, max_range_atr=2.8, proper_move=False confirmed

---

## 2026-02-14-bbw-layer3-journal.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
Session journal for the same Layer 3 audit pass 3 session documented in bbw-layer3-audit-pass3.md. Contains the same content but organized as a journal with context loading section. Confirms: research/ directory does NOT exist yet before the build, Layer 1 (61/61 PASS) and Layer 2 (68/68 PASS, 148/148 debug PASS). Provides copy-paste ready Claude Code instruction to read 4 files in order and build Layer 3. Next steps: paste instruction into VS Code, Claude Code builds all Layer 3 files, all tests must pass before proceeding to Layer 4, resume instructions if max token hit.

### Decisions recorded
- Same decisions as bbw-layer3-audit-pass3.md

### State changes
- Same as bbw-layer3-audit-pass3.md (companion file, same session)

### Open items recorded
- Same as bbw-layer3-audit-pass3.md

### Notes
- Duplicate/companion file to bbw-layer3-audit-pass3.md — both created in same session. Content largely identical with different organizational structure.

---

## 2026-02-14-bbw-layer3-results.md
**Date:** 2026-02-14 (14:33 UTC)
**Type:** Build session

### What happened
Test results log for Layer 3 build (research/bbw_forward_returns.py). 12 tests, 102/102 PASS. 6 debug sections, 72/72 PASS. Sanity check on RIVERUSDT 5m: 0.02s runtime (2.15M bars/sec), ATR mean=0.2623 (1.58% of close). Cross-validation of L1+L2+L3 real data shows RED_DOUBLE state has highest range_atr (3.795) and highest proper_move rate (60.0%), while BLUE_DOUBLE has lowest range_atr (3.342) — noted as hypothesis not confirmed (BD range <= NORMAL range). NaN zones confirmed correct: last N bars per window contain NaN (10 NaN for window=10, 20 NaN for window=20). All pre-computed bar 15 and bar 16 values from audit passes verified with PASS.

### Decisions recorded
- None new (implementation followed audited prompt)

### State changes
- research/bbw_forward_returns.py confirmed built and passing
- Layer 3: COMPLETE (102/102 tests, 72/72 debug)

### Open items recorded
- Layer 4 (research/bbw_simulator.py) — next build (prompt needs audit)

### Notes
- Key finding from real data: RED_DOUBLE proper_move=60%, all others 45-51%. Hypothesis that BLUE_DOUBLE has lower range than NORMAL not confirmed (3.342 vs 3.377).
- VERIFICATION: research/bbw_forward_returns.py confirmed present on disk

---

## 2026-02-14-bbw-layer4-audit-and-sync.md
**Date:** 2026-02-14
**Type:** Audit / Planning

### What happened
Combined Layer 4 audit summary and project sync document. Confirms full project status: Layer 1-3 complete, Layer 4 build prompt audited and ready (22 bugs found/fixed in 2 rounds), Layer 4b/5/6 not yet built. Full layer output column reference documented (Layer 1: 10 cols, Layer 2: 9 cols, Layer 3: 17 cols, Layer 4: SimulatorResult dataclass with group_stats/lsg_results/lsg_top/scaling_results/summary). 10 Layer 4 design decisions locked (TP/SL ambiguity resolved to close_pct, no per-bar PnL storage, no transaction costs yet, states from L1 only, etc.). Layer 5 scope defined (bbw_report.py, 11 CSV output files in reports/bbw/ directory tree). Build order documented. Key fixes in audit: PnL formula with per-bar ATR/close enforcement, valid_mask made dynamic across all windows, scaling circular dependency resolved, architecture doc corrected (L3 input is OHLCV only, spectrum is 4 colors not 5).

### Decisions recorded
- PnL formula: close_pct based (not TP/SL ATR targets) for conservative approach
- No per-bar PnL storage (inline cumsum for drawdown only)
- No transaction costs in Layer 4 (raw edge first, config.fee_pct later)
- States from Layer 1 only (7 bbwp_state values)
- Bins start at -1 (defensive for bars_in_state)
- Group G uses pandas mask (not np.char.add) to avoid None->'None'
- profit_factor: NaN if both sum(wins) and sum(losses) are 0
- edge_pct guard: NaN if abs(mean_base_pnl) < 1e-10
- Layer 5 depends on BOTH Layer 4 AND Layer 4b (Monte Carlo must be built first)

### State changes
- BUILDS\PROMPT-LAYER4-BUILD.md: all 22 bugs fixed
- BBW-SIMULATOR-ARCHITECTURE.md: corrected (L3 input, spectrum 4 colors)
- Layer 4 build prompt: AUDITED, ready for Claude Code

### Open items recorded
- Layer 4: execute BUILDS\PROMPT-LAYER4-BUILD.md in Claude Code
- Layer 4b (Monte Carlo): needs build prompt
- Layer 5: needs build prompt
- Layer 6: needs build prompt
- PRE-STEP (coin_classifier.py): not built, blocks full Layer 5 output

### Notes
- Documents existing test/script files as of this point (7 test/script files confirmed)
- Architecture doc L3 input corrected: L3 only needs OHLCV (not OHLCV + BBWP + Sequence)

---

## 2026-02-14-bbw-layer4-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Detailed bug audit report for BUILDS\PROMPT-LAYER4-BUILD.md. Round 1: 14 bugs found and fixed (4 CRITICAL: PnL formula ATR source, ambiguous PnL undefined, valid_mask only checked fwd_10, expectancy_per_bar meaningless; 5 MODERATE: _lsg_grid_search signature mismatch, scaling circular dependency, bins edge at 0, Group G np.char.add None issue, calmar_approx needs max_drawdown; 5 MINOR: directional_bias string mapping, sanity combo math, L3 pre-check missing, _add_derived_columns not defined, _extract_top_combos closure). Round 2: 8 new issues (3 MODERATE: architecture doc L3 input, architecture doc 5 vs 4 spectrum colors, max_drawdown 2D vectorization; 5 MINOR: close_pct scoping, directional_bias excludes flat, profit_factor 0/0 edge, test dimension label, edge_pct divide by zero). Verdict: No critical bugs remain.

### Decisions recorded
- max_drawdown: added with inline cumsum pattern (np.maximum.accumulate on 2D)
- Architecture doc: L3 input corrected to OHLCV only, spectrum corrected to 4 colors

### State changes
- BUILDS\PROMPT-LAYER4-BUILD.md: all bugs fixed
- BBW-SIMULATOR-ARCHITECTURE.md: N1 (L3 input) and N2 (4 colors) corrected

### Open items recorded
- Build Layer 3 to completion first, then execute Layer 4 prompt

### Notes
- 22 total bugs across 2 rounds for Layer 4 prompt, all resolved before Claude Code execution
- Companion document to bbw-layer4-audit-and-sync.md (same audit, different format)

---

## 2026-02-14-bbw-layer4-results.md
**Date:** 2026-02-14 (16:24 UTC)
**Type:** Build session

### What happened
Test results log for Layer 4 build (research/bbw_simulator.py). 15 tests, 55/55 PASS. 7 debug sections, 44/44 PASS. Sanity check on RIVERUSDT 5m: L4 runs in 2.06s, total pipeline (L1+L2+L3+L4) in 2.47s. 7 states present, 112 LSG combos, 6 scaling scenarios. Group stats best categories: A_state=RED_DOUBLE (edge=0.070), B_spectrum=green (edge=0.062), C_direction=expanding (edge=0.051), D_pattern=GRB (edge=3.255), E_skip=True (edge=0.099), F_duration=21-50 bars (edge=0.388), G_ma_spectrum=cross_down_green (edge=0.142). Top LSG combo: RED_DOUBLE lev=20 tgt=4 sl=1.5 exp=$18.90 wr=44.4% pf=1.29. Scaling results: 5 of 6 scenarios verdict=USE. Results CSV saved.

### Decisions recorded
- None new (implementation followed audited prompt)

### State changes
- research/bbw_simulator.py confirmed built and passing
- Layer 4: COMPLETE (55/55 tests, 44/44 debug)
- results/bbw_simulator_sanity.csv saved to disk

### Open items recorded
- Layer 4b (Monte Carlo) — next build
- Layer 5 (bbw_report.py) — blocked by Layer 4b

### Notes
- Key finding: RED_DOUBLE state has best edge at $18.90 expectancy (vs $1.77-$4.27 for other states)
- Most states show RED at only $-0.21 — only state with negative gross expectancy
- VERIFICATION: research/bbw_simulator.py confirmed present on disk

---

## 2026-02-14-bbw-layer5-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Bug audit of BUILDS\PROMPT-LAYER5-BUILD.md (Layer 5 report generator). 15 issues found: 3 HIGH (H1: architecture diagram function signatures missing config parameter — 8 functions affected; H2: _summarize_group crashes on all-NaN expectancy_usd via idxmax(); H3: mock n_triggered can exceed n_entry_bars — independent random calls); 7 MEDIUM (M1: dead variable mc_status; M2: report manifest doesn't list itself; M3: manifest subdir detection fragile with prefix-matching; M4: groupby.apply() FutureWarning in pandas >= 2.1; M5: ReportConfig.top_n_per_state unused; M6: test count mismatch in header says 12 but has 20; M7: _validate_sim_result doesn't check summary is dict); 5 LOW (L1: bool→string conversion in mock; L2: no __all__; L3: asymmetric exception handling not documented; L4: ascending list construction brittle; L5: missing bbwp_ma from validation list — intentional). Cross-reference validation against Layer 4 output columns: all checks PASSED.

### Decisions recorded
- H1 fix: update architecture diagram to match all function signatures
- H2 fix: add isna().all() guard before idxmax()
- H3 fix: n_entry must be single random draw, n_triggered derived from it
- M2: manifest cannot list itself — document this limitation for Layer 6

### State changes
- BUILDS\PROMPT-LAYER5-BUILD.md: fixes documented (actual edits not confirmed in this log)

### Open items recorded
- Apply all 15 fixes to PROMPT-LAYER5-BUILD.md before Claude Code execution

### Notes
- Cross-reference between L4 and L5 column names: all 7 group keys, all DataFrame attributes, scaling columns — all matched

---

## 2026-02-14-bbw-layer5-v2-build-session.md
**Date:** 2026-02-14
**Type:** Build session

### What happened
Build session for Layer 5 V2: research/bbw_report_v2.py (VINCE feature generator, NOT the CSV report writer). Built as continuation of V2 pipeline work where Layers 1-4b V2 were already complete. Files created: bbw_report_v2.py, tests/test_bbw_report_v2.py (48 tests, NOT yet run), scripts/debug_bbw_integration.py, scripts/test_bbw_integration_random.py. Files modified: bbw_monte_carlo_v2.py, test_bbw_monte_carlo_v2.py, 2 debug scripts. 7 bugs found and fixed: (1) CRITICAL — bbw_state_at_entry → bbw_state column name mismatch across Layer 4b and debug scripts; (2) HIGH — 3 of 5 Layer 5 functions used 'state' instead of 'bbw_state'; (3) REAL BUG — state_encoding had 3 phantom states (GREEN_DOUBLE, YELLOW_DOUBLE, GRAY) and missed NORMAL/MA_CROSS_UP/MA_CROSS_DOWN; (4) BUG — import reference used non-existent function name; (5) BUG — integration test used wrong outcome values WIN/LOSS instead of TP/SL/TIMEOUT; (6) ARCHITECTURE — LSG should be fixed for entire run not random per-trade; (7) DATA — n_trades too low for group filter. Architecture note: two parallel Layer 5 implementations exist (bbw_report_v2.py for VINCE features, planned bbw_report.py for CSV reports).

### Decisions recorded
- LSG architecture: fixed for entire backtester run (not random per-trade)
- Two Layer 5 files: bbw_report_v2.py (VINCE ML features) and bbw_report.py (CSV reports, not yet built)
- state_encoding: must use all 9 Layer 4 valid states (not phantom states)

### State changes
- research/bbw_report_v2.py: CREATED (logic complete, tests built not run)
- tests/test_bbw_report_v2.py: CREATED (48 tests, not run)
- debug_bbw_integration.py, test_bbw_integration_random.py: CREATED
- bbw_monte_carlo_v2.py and related: MODIFIED (column rename fix)

### Open items recorded
1. Run scripts/debug_bbw_integration.py — confirm end-to-end pass
2. Run scripts/test_bbw_integration_random.py — confirm 10/10 pass
3. Run tests/test_bbw_report_v2.py — confirm 48/48 pass
4. Run tests/test_bbw_monte_carlo_v2.py — confirm Layer 4b still passes
5. Build research/bbw_report.py (full pipeline CSV writer, 11 files — separate from V2)

### Notes
- Layer 5 tests NOT run at session end — completeness status shows "BUILT, NOT RUN"
- VERIFICATION: research/bbw_report_v2.py confirmed present on disk

---

## 2026-02-14-bbw-layer6-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Bug audit of BUILDS\PROMPT-LAYER6-BUILD.md (Ollama review layer). 8 issues found: 1 HIGH (H1: architecture diagram function signatures all mismatched — 5 functions affected, same pattern as Layer 5 H1); 4 MEDIUM (M1: _discover_reports constructs wrong path for files with subdir='root' → base/'root'/filename doesn't exist; M2: _validate_ollama_connection fallback assigns non-existent model; M3: test count mismatch says 15 but has 20; M4: _ollama_call catches ValueError but doesn't retry on empty response); 3 LOW (L1: _analyze_features reads CSV as DataFrame — slight design break but documented; L2: max_csv_chars used for spec truncation — naming inconsistency; L3: no __all__ in test spec). Cross-reference validation of L5 → L6 file paths and column names: all checks PASSED with M1 fix.

### Decisions recorded
- H1 fix: update architecture diagram to match actual function signatures
- M1 fix: handle subdir == 'root' case explicitly (base/filename not base/root/filename)
- M4: either add ValueError to retry exceptions OR document as intentional

### State changes
- BUILDS\PROMPT-LAYER6-BUILD.md: fixes documented (actual edits not confirmed in this log)

### Open items recorded
- Apply all 8 fixes before Claude Code execution of Layer 6

### Notes
- Cross-reference between L5 output and L6 input: all filenames matched, directory structure matched (with M1 fix)

---

## 2026-02-14-bbw-uml-research.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
Combined log of 2 sessions covering BBW simulator architecture and UML work. Session 1 (morning): Reviewed existing vault files (bbwp_v2.pine, BBWP-v2-BUILD-SPEC.md, bbwp_caretaker_v6.pine). Core concept established: BBW does NOT limit trades — BBW TUNES the LSG parameters. Full architecture document produced (5-layer pipeline). BBWP percentile rank implementation options researched (Option A: pd.Series.rolling(100).rank(pct=True) recommended for production). Key design decisions locked: SL test values (1, 1.5, 2, 3 ATR), forward windows (10+20 bars on 5m), proper move threshold (3 ATR), coin grouping (KMeans clustering). Session 2 (afternoon): Ripster/AVWAP scope question answered — NO (rabbitholing), belongs at VINCE not BBW layer. 17 BBW features for VINCE identified. 6 UML diagrams produced in Mermaid format. Build sequence defined (10 steps, ~5 hours Claude Code). Ollama Layer 6 added to architecture post-revision.

### Decisions recorded
- BBW purpose: TUNES LSG (Leverage, Size, Grid/Target), does NOT limit trades
- Ripster/AVWAP: out of scope for BBW, belongs at VINCE (ML layer)
- SL values: 1, 1.5, 2, 3 ATR
- Forward windows: 10 bars + 20 bars on 5m
- Proper move threshold: 3 ATR
- Coin grouping: data-driven KMeans clustering
- TDI: out of scope
- Ollama: NOT needed for BBW math, relevant for VINCE NL reasoning

### State changes
- BBW-UML-DIAGRAMS.md: created (6 Mermaid diagrams with legends)
- BBW-STATISTICS-RESEARCH.md: created (scope, features, Monte Carlo, build sequence)
- BBW-SIMULATOR-ARCHITECTURE.md: created (full architecture + Ollama Layer 6)

### Open items recorded
- Review all 4 docs in Obsidian (diagrams render natively)
- Approve architecture → start build in Claude Code
- Build sequence: Layer 1 first

### Notes
- This is the original architecture session log that preceded all the layer build logs
- Notes contradiction with 2026-02-16-bbw-v2-fundamental-corrections.md: The original architecture treated Ollama reasoning as Layer 6 of BBW pipeline. The Feb 16 corrections document removes Layer 6 entirely and clarifies VINCE is separate.

---

## 2026-02-14-dashboard-v31-build.md
**Date:** 2026-02-14 (15:06 UTC)
**Type:** Build session

### What happened
Dashboard v3.1 build session. 15 surgical patches applied to scripts/dashboard.py (1520 → 1893 lines) via scripts/build_dashboard_v31.py (626 lines). Pre-work: 7 critical logic fixes applied first (C-1 through C-7 from operational logic audit). 3 new features added: (1) Date Range Filter — sidebar widget with All/7d/30d/90d/1y/Custom modes, integrated into params_hash; (2) Stress Test — expander showing worst 1-5 non-overlapping drawdown windows, re-backtests on each; (3) Portfolio Mode — new sidebar mode, coin selection (Top N/Lowest N/Random N/Custom), runs per-coin, aligned equity curves, portfolio summary metrics, correlation matrix. Test results: 21/21 PASS (test_dashboard_v31.py). Build script: 15/15 anchors found, 0 missing, APPLIED, py_compile PASS. 6 bugs found and fixed during audit: P10b (date filter position), test assertion fixes, escaped quotes in f-strings (10 instances refactored to temp variables), missing py_compile, missing docstrings.

### Decisions recorded
- Date range filter integrated into params_hash so different date ranges get different sweep progress
- Portfolio mode: per-coin equity curves aligned using union DatetimeIndex + forward-fill
- f-string escaped quotes: refactored to temp variables (aligns with MEMORY hard rule)

### State changes
- scripts/dashboard.py: edited (1520 → 1893 lines)
- scripts/build_dashboard_v31.py: created (626 lines)
- scripts/test_dashboard_v31.py: created (~430 lines)

### Open items recorded
- None stated

### Notes
- Dashboard v3.1 is a build on top of dashboard.py (pre-existing file). The 7 operational fixes (C-1 through C-7) from the audit were applied before the v3.1 features.
- Run command: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py"`

---

## 2026-02-14-operational-logic-audit.md
**Date:** 2026-02-14
**Type:** Audit

### What happened
Full operational logic audit of Four Pillars backtester covering 9 engine files, 4 data pipeline files, and 6 ML pipeline files. Focus was trading logic correctness, look-ahead bias, commission math, data integrity (NOT bugs, style, or refactoring). 7 CRITICAL findings: (C-1) Equity curve ignores unrealized P&L — max DD understated; (C-2) Scale-out entry commission not prorated — SCALE_1 artificially profitable; (C-3) CommissionModel cost_per_side backdoor — future landmine; (C-4) duration_bars is look-ahead feature in ML training — inflates model accuracy; (C-5) daily_turnover uses intraday future volume (shift(1) needed); (C-6) Meta-labeler trains and evaluates on SAME data — purged CV exists but never wired; (C-7) Triple barrier labels ignore commission — TP hit but net negative. 15 WARNING findings covering backtester engine (W-1 through W-8), data pipeline (W-9 through W-15), ML pipeline (W-16 through W-20). 17 OK findings confirming correct implementation of commission math, entry timing, SL/TP priority, signal grading, ATR, etc.

### Decisions recorded
- Fix priority order: C-6 (purged CV) → C-4 (duration_bars) → C-1 (unrealized P&L) → C-7 (label_trades_by_pnl) → C-2 (scale-out commission) → C-5 (daily_sum.shift) → C-3 (remove cost_per_side)

### State changes
- Audit document created (findings only, no code changed in this session)
- C-1 through C-7 fixes applied separately in dashboard-v31-build.md session (same day)

### Open items recorded
- All 7 CRITICAL fixes (C-1 through C-7) — in priority order
- All 15 WARNING findings (lower priority)

### Notes
- This audit preceded and motivated the 7 pre-work fixes in the dashboard v3.1 build session
- C-6 (purged CV not wired) identified as highest priority fix — ML accuracy results are all in-sample and meaningless for live trading

---

## 2026-02-14-project-flow-update.md
**Date:** 2026-02-14
**Type:** Planning

### What happened
Two-chat session log covering project flow updates and Core Build 2 prompt. Key correction: data download status was wrong in the review doc (claimed 14% and 1%) — actual status is 100% complete for both periods. 2023-2024: 166 completed + 43 no_data = 209/209 eligible. 2024-2025: 257 completed + 19 no_data = 276/276 eligible. Explanation: CoinGecko listing date filter excluded coins that didn't exist in those periods (reducing eligible count). 399 coins total, 6.2 GB cache. Claude Code build_all_specs.py: ALL 9 FILES EXIST on disk. Core Build 2 defined with 7 steps (run test_v385.py, test_dashboard_v3.py, test_vince_ml.py, fix failures, smoke test dashboard, single coin parquet export, period_loader test). Key insight documented: role-prompting adds nothing — concrete specs + explicit pass/fail criteria do the heavy lifting. PROJECT-FLOW-CHRONOLOGICAL.md fully rewritten with accurate statuses.

### Decisions recorded
- BBWP Python port deferred to afternoon
- CoinGecko features join deferred until after Core Build 2
- Core Build 2 constraints: minimal patches, no rewrites

### State changes
- PROJECT-FLOW-CHRONOLOGICAL.md: full rewrite with accurate statuses + Core Build 2 phase

### Open items recorded
- Core Build 2: 7-step sequential test-and-fix workflow (Claude Code running)
- BBWP Python port: deferred to afternoon session

### Notes
- Data download percentage discrepancy explained: CoinGecko listing date filter caused discrepancy, not actual incompleteness
- Critical path updated: Data COMPLETE → Core Build 2 (active) → Sweep → Trade Parquet → ML Phase 1 → Live

---

## 2026-02-14-vault-sweep-review.md
**Date:** 2026-02-14
**Type:** Other (automated code review output)

### What happened
Automated Ollama code review of 62 vault Python files using qwen2.5-coder:14b model. Runtime: 4,259 seconds (71 minutes). 42 issues flagged across 62 files. Review format per file: Critical Issues, Security, Error Handling, Logic, Improvements (with code snippets). Files reviewed span the entire vault codebase including localllm/, data/ (fetcher.py, normalizer.py), scripts/ (dashboard.py, dashboard_v2.py, dashboard_v3.py, download scripts), engine/, signals/, ml/, and root-level utility scripts (vault_sweep.py, vault_sweep_3.py, vault_sweep_4.py). Large files (>50,000 chars) skipped with note — this affected dashboard.py and dashboard_v2.py. Common issues flagged: broad exception handling, infinite loop risks, missing retry mechanisms, off-by-one errors in stage lookback (state_machine_v382.py), missing try/except for file operations. File is ~4,200 lines (largest in the batch at ~86KB).

### Decisions recorded
- None (review output only, no decisions made)

### State changes
- No code changed in this session (read-only review output)

### Open items recorded
- 42 issues identified across codebase — no action plan stated in this file

### Notes
- This file documents an automated batch review, not a human decision session. Many suggestions are generic (add retries, use specific exceptions) that may not apply to the codebase's actual requirements.
- dashboard.py and dashboard_v2.py were SKIPPED (too large at >50K chars) — no review output for these files.

---

## 2026-02-16-bbw-layer4b-plan.md
**Date:** 2026-02-16
**Type:** Planning / Build session

### What happened
Combined Layer 4b build plan AND results (same file, results appended during session). Pre-build: 4 spec bugs fixed (CRITICAL: shuffle is order-invariant for PnL — must use bootstrap not permutation for PnL/Sharpe; CRITICAL: DD sign convention → store as positive absolute values; MEDIUM: MCL missing from MC loop; LOW: Layer 4 doesn't expose per-trade PnL — reconstruct via _vectorized_pnl). Dual-method approach designed: Bootstrap (WITH replacement) for PnL/Sharpe/profit_factor CIs; Permutation (WITHOUT replacement) for max_dd/max_consecutive_loss. 6 verdicts defined: ROBUST, MARGINAL, FRAGILE, COMMISSION_KILL, INSUFFICIENT_DATA, THIN_EDGE. Build manifest: 5 files (~350-400 lines each). Architecture evaluation: all L1-L4 complete. Layer 4b results: py_compile 5/5 PASS, unit tests 45/45 PASS (2 fixes applied), debug 57/57 (1 known FAIL — Section 6.2 DD=1900 not 2000, documented as correct). RIVERUSDT sanity: 6/7 states COMMISSION_KILL (gross $1.77-$4.27 killed by $8.00 RT), 1/7 FRAGILE (RED_DOUBLE gross=$18.90, net=$10.90). Layer 5 (bbw_report.py) also built in same session: 58/58 tests PASS, 11/11 CSVs written. GitHub push to branch bbw-layers-1-5-complete: 64 files, 19,108 insertions, push successful.

### Decisions recorded
- Bootstrap for PnL/Sharpe CI (order-invariant metrics need bootstrap, not permutation)
- Permutation for DD/MCL (path-dependent metrics)
- Commission: 0.0008 RT deducted from all PnL calculations
- Store percentile bands only (5 floats per state), discard raw 1000-sim matrices (400 GB vs 2 GB)
- Coin classifier gap: Layer 4b coin-agnostic, classifier deferred to Layer 5
- Layer 4b → Layer 5 output contract: 4 DataFrames (state_verdicts, confidence_intervals, equity_bands, overfit_flags)
- numpy.random.Generator (not legacy numpy.random.seed) for thread safety
- Min net expectancy threshold: $1.00
- Max MCL practical threshold: 15

### State changes
- research/bbw_monte_carlo.py: CREATED (5/5 py_compile, 45/45 tests)
- research/bbw_report.py: CREATED (58/58 tests, 11/11 CSVs written)
- GitHub branch bbw-layers-1-5-complete pushed (64 files changed)
- results/bbw_monte_carlo_sanity_verdicts.csv and flags.csv saved

### Open items recorded
- Layer 6: Ollama review (now unblocked)
- Fill remaining coin gaps (P0.2)
- Coin classifier (P1.1)
- Deploy staging files (P1.5)

### Notes
- KEY FINDING: BBW-only edges are too weak ($5.22 avg gross vs $8.00 RT commission). Validates that stochastics/grading do the heavy lifting in Four Pillars strategy.
- Multi-coin validation (RIVER/AXS/KITE): 21/21 states COMMISSION_KILL
- Debug section 6.2 intentional FAIL documented: DD for [-100]*20 starting at -100 is 1900 not 2000 (cumsum starts at first value, not 0)
- VERIFICATION: research/bbw_monte_carlo.py and research/bbw_report.py confirmed present on disk

---

## 2026-02-16-bbw-layer4b-results.md
**Date:** 2026-02-16 (07:59:51 UTC)
**Type:** Build session

### What happened
Detailed test results log for Layer 4b (bbw_monte_carlo.py). py_compile: 5/5 PASS. Unit tests: 45/45 PASS. Debug checks: 56/57 PASS (1 known FAIL in Section 6.2 — DD=1900 expected 2000; documented as correct behavior: cumsum starts at -100 not 0 for first-loss sequence). Sanity check: COMPLETE, 7 states processed. RIVERUSDT results: 6/7 COMMISSION_KILL, 1/7 FRAGILE (RED_DOUBLE). Avg commission drag: $7.14/trade. RED state used lev=10 sz=0.5 (RT=$2.00) but still killed by negative gross. Confidence interval samples provided for first 3 states showing negative total_pnl, negative sharpe/sortino, profit_factor 0.88-0.93. Max consecutive loss very high (real=38 for BLUE, p95=18 — real exceeds p95, DD_FRAGILE flag). Results CSVs saved to results/ directory.

### Decisions recorded
- None new (results log only)

### State changes
- research/bbw_monte_carlo.py: confirmed passing
- results/bbw_monte_carlo_sanity_verdicts.csv: saved
- results/bbw_monte_carlo_sanity_flags.csv: saved

### Open items recorded
- None stated (results log)

### Notes
- Companion results file to bbw-layer4b-plan.md — plan file also contains the results summary
- Section 6.2 FAIL is documented as expected (mathematical correctness): cumsum([−100]×20) starts at -100, peak=-100, trough=-2000, max DD = 2000-100 = 1900

---

## 2026-02-16-bbw-v2-fundamental-corrections.md
**Date:** 2026-02-16
**Type:** Planning / Architecture

### What happened
Major architecture correction session for BBW V2 design. Three fundamental misunderstandings corrected: (1) Direction source: BBW does NOT test both directions arbitrarily — direction comes from complete Four Pillars strategy (Stochastics + Ripster + AVWAP combined). User example: "Stochastics: Overbought → SHORT, Ripster: Trending down → SHORT, AVWAP: Price above → LONG bias (conflict) → Strategy Decision: SHORT (2 vs 1)". BBW's job is: given SHORT in BLUE state, what LSG works best? (2) Layer 6 does not exist: VINCE is a separate ML component, NOT part of BBW pipeline. BBW outputs data (one of four pillar inputs to VINCE). (3) Trade source: BBW analyzes REAL backtester results (400+ coins, year of data, 93% success rate from dashboard sweep) — NOT synthetic simulated trades. User quote: "There is a set ran on the dashboard, and we swept through a whole year with 93% with 80+% LSG...". BBW V2 purpose clarified: pure data generator for VINCE training — group by (state, direction, LSG), calculate BE+fees rates, output results. V2 uses BE+fees metric instead of win rate. 4 documents updated.

### Decisions recorded
- BBW V2 is a data generator only — no directional decision-making
- Direction always comes from Four Pillars strategy (Stochastics + Ripster + AVWAP)
- Layer 6 removed from BBW architecture
- VINCE is separate ML component
- Trade source: real backtester_v385 results (not synthetic)
- V2 metric: BE+fees success rate (not win rate)
- BBW V2 architecture: Layers 1-2-3-4-4b-5 (no Layer 6)

### State changes
- BBW-V2-ARCHITECTURE.md: updated to v2.0 (removed Layer 6, fixed trade source, clarified direction)
- BBW-V2-UML.mmd: updated (Layer 6 removed, backtester nodes added, VINCE shown as separate)
- BBW-V2-LAYER4-SPEC.md: complete rewrite (from simulation to analysis of real backtester results)
- BBW-V2-LAYER5-SPEC.md: new document created (feature engineering, 5 CSV outputs, 30+ tests)

### Open items recorded
1. Build Layer 4: bbw_analyzer_v2.py (7-8 hours)
2. Build Layer 4b: bbw_monte_carlo_v2.py (depends on Layer 4)
3. Build Layer 5: bbw_report_v2.py (depends on Layer 4b)

### Notes
- IMPORTANT CONTRADICTION with earlier logs: The original BBW architecture (bbw-uml-research.md, bbw-full-session.md) included Ollama as Layer 6 of the BBW pipeline. The Feb 16 corrections document removes Layer 6 entirely, clarifying VINCE (which includes Ollama reasoning) is a separate component.
- The V1 pipeline (L1-L5 including bbw_simulator.py) was built using the OLD architecture (synthetic trades, both directions tested). The V2 rebuild uses REAL backtester results.
- User expressed frustration at being asked directional questions when the dashboard already showed 93% success with real data.
- VERIFICATION: research/bbw_analyzer_v2.py and research/bbw_report_v2.py confirmed present on disk (V2 files built)
