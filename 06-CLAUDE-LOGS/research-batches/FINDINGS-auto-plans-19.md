# Batch 19 Findings — Auto-Plans Research
**Files processed:** 20
**Batch:** 19 of 22

---

## joyful-booping-cloud.md
**Date:** Not dated in filename; references "2026-02-13" in backup path
**Type:** Planning

### What happened
Plan for `download_all_available.py` — a script to fill backward and forward OHLCV data gaps for all 399 cached Bybit coins. The existing `download_1year_gap_FIXED.py` skipped coins listed after 2025-02-11. Goal: all 399 coins have all available data from 2025-11-02 (or listing date if later) in both Parquet and CSV format.

### Decisions recorded
- Backup entire cache before any writes: `data/cache_backup_YYYYMMDD_HHMMSS/`
- Six-step sanity gate per symbol before overwriting (row count, no nulls, no duplicates, sorted, extends both ends)
- Fetch both backward and forward gaps in one pass using `_fetch_page()` directly (not `fetch_symbol()` to avoid cache-overwrite side effects)
- Progress tracked in `data/cache/_download_progress.json` for restartability
- Rate limit: 0.05s/page, 1s between symbols, exponential backoff (10-160s)
- CLI flags: `--force`, `--symbols`, `--rate`

### State changes
Plan document created. Script `scripts/download_all_available.py` planned but not yet built (this is a pre-build plan).

### Open items recorded
- Build `scripts/download_all_available.py`
- Verification via `scripts/sanity_check_cache.py` after run

### Notes
None.

---

## kind-discovering-shore.md
**Date:** 2026-03-05
**Type:** Strategy/Analysis document

### What happened
Document titled "Cards on the Table" — a factual breakdown of what the BingX connector bot knows vs what the user knows when trading. Ten cards covering: B trade definition in code (2-of-3 stochs + Cloud 3 gate), A trade definition (all 3 + Stage 2), what the bot has NO concept of (HTF session bias, MTF clouds, sequential K/D, BBW, TDI, structure), why PIPPIN LONG happened on 2026-02-28, version discrepancy (bot runs v3.8.4 not v3.8.6), definition of "perspective" (3-layer HTF system), "nowhere's land", volume generation vs top-tier waiting modes, 6 open questions blocking trend-hold, and what CAN be done without those 6 answers.

### Decisions recorded
- Bot's Cloud 3 gate (`price_pos >= 0`) identified as too crude — cannot distinguish trending vs drifting
- v3.8.4 bot has Stage 2 potentially inactive (config says `require_stage2: true` but v384 defaults to `False` — potential loading bug)
- Entry-side improvements don't require answering the 6 open position management questions

### State changes
Analysis document created. No code changes. PIPPIN LONG root cause documented: bot passed its own weak rules legitimately; rules are incomplete relative to full manual trading system.

### Open items recorded
Six blocking questions (SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1/TP-1) still unanswered.
Four entry-side improvements identified that don't need those answers: perspective layer, B-trade tightening, coin monitoring, sequential K/D check.

### Notes
References `fizzy-humming-crab.md` as source for "perspective" definition. References log line 10667 from `PROJECTS/bingx-connector/logs/2026-02-27-bot.log` for PIPPIN trade details.

---

## kind-yawning-reef.md
**Date:** 2026-02-28
**Type:** Build spec / Research audit

### What happened
Plan for Vince B1 — the FourPillarsPlugin build. B1 is the foundation of Vince v2, making the Four Pillars backtester accessible to all Vince components. Plan includes: full audit of existing `strategies/four_pillars.py` (found to be v1, non-compliant with v2 ABC), identification of 5 issues before the build, and formal specification of all 5 ABC methods to implement.

User override noted: engine version is v385 (overrides build plan's v384 reference). Existing v1 file must be archived as `strategies/four_pillars_v1_archive.py` before rewrite.

Five methods specified: `compute_signals()`, `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document` property.

### Decisions recorded
- Archive existing `strategies/four_pillars.py` as `strategies/four_pillars_v1_archive.py` first (NEVER OVERWRITE rule)
- Use v385 engine (not v384 as build plan specified)
- `compute_signals()` merges enrich + compute into one method, no `params` arg
- Sweepable params: `sl_mult`, `tp_mult`, `be_trigger_atr`, `be_lock_atr`, `cross_level`, `allow_b_trades`, `allow_c_trades`
- `symbol` field added by `run_backtest()` wrapper (not in Trade384)
- B1 scope: ONE file only (`strategies/four_pillars.py`)

### State changes
Build spec document created. Target file planned: `strategies/four_pillars.py` (rewrite). Five issues identified: file conflict, signal version mismatch, v385 exists alongside v384, no `symbol` field in Trade384, date filtering column name unknown.

### Open items recorded
- Confirm which signal version is current (v383_v2.py vs state_machine.py)
- Confirm v384 is still production engine (not v385)
- Confirm parquet timestamp column name for date filtering

### Notes
References skills required: four-pillars, four-pillars-project (Dash NOT needed for B1). Comprehensive verification suite provided (py_compile + 3 smoke tests).

---

## lexical-kindling-rose.md
**Date:** 2026-02-17
**Type:** Planning (log action)

### What happened
Short plan document. User asked whether the Vince ML build exposes the Four Pillars trading strategy and whether it is safe to share. Two explore agents ran a codebase audit. Plan: create a new log file at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-17-vince-ml-strategy-exposure-audit.md` with findings.

### Decisions recorded
- `signals/` directory (10 files): PROPRIETARY — not safe to share
- `ml/` directory (14 files): GENERIC — strategy-agnostic, safe to share
- `build_staging.py`: NOT SAFE — embeds all parameter values
- `dashboard_v391.py`: NOT SAFE — parameter UI reveals settings
- Verdict: Only `ml/` directory is safe for public sharing

### State changes
Plan to write one log file. No code changes.

### Open items recorded
Write the log file and verify contents.

### Notes
This is a very short planning document (action = write one log file with listed content).

---

## linear-wiggling-seal.md
**Date:** 2026-02-14 (references shelved item) / main plan undated
**Type:** Build plan

### What happened
Two-part document: (1) a shelved plan for a cache gap finder, and (2) the main build plan for Dashboard v3.2 — bugfixes and UX improvements from live user testing of v3.1 (1893 lines).

14 bugs/issues documented with root causes and fixes:
- Bug 1: Portfolio DD% shows -207.3% (impossible) — fix: clip at -100%
- Bug 2: Stress test Arrow serialization crash — fix: keep numeric, use Styler
- Bug 3: `use_container_width=True` deprecated (~30 instances) — partial fix
- Bug 4: Portfolio mode has no tabs — DEFERRED to v3.3
- Bug 5: SHIB not in coin list — not a bug, need to download `1000SHIBUSDT`
- Bug 6: Run Backtest button at bottom of sidebar — fix: move to top
- Bug 7: No loading indicator during portfolio backtest — fix: add spinner
- Bug 8: BTC equity curve zigzag — NOT a bug, commission drag expected
- Feature 9: Info tooltips on key metrics — add `help=` param
- Bug 10: ML Filtered vs Unfiltered table Arrow crash — same fix as Bug 2
- Bug 11/12: Grades and TP Impact tables Arrow risk — same pattern fix
- Bug 13: Sweep detail mode missing `"df"` key — add it
- Bug 14: Equity curve x-axis shows bar index not datetime — fix: add datetime x

12 patches (P1-P12) planned for `scripts/build_dashboard_v32.py`.

### Decisions recorded
- Build approach: patch script same pattern as v3.1
- Portfolio tabs (Bug 4) deferred to v3.3 feature
- SHIB: user action (download), not code fix
- BTC zigzag: expected behavior, no code fix
- Equity curve x-axis: use datetime if available, fall back to range index

### State changes
Build plan created for v3.2. Files planned: `scripts/build_dashboard_v32.py`, `scripts/test_dashboard_v32.py`. No files written yet (this is the plan).

### Open items recorded
- User runs `download_all_available.py` for SHIB
- v3.3: portfolio tabs with coin selector dropdown
- Git push after v3.2 patches verified

### Notes
References `joyful-booping-cloud.md` indirectly (download script). Cache gap finder shelved until dashboard v3.2 fully verified.

---

## lively-baking-pumpkin.md
**Date:** 2026-03-03
**Type:** Planning (git operations)

### What happened
Plan for git cleanup: fix `.gitignore` to exclude `.venv312/` and `.bak*` files, then commit the accumulated backlog (all files modified/created since last commit on 2026-02-28 through 2026-03-03). The VSCode Git panel showed "too many active changes" due to `.venv312/` (thousands of files) and 37 `.bak*` files.

### Decisions recorded
- Add to root `.gitignore`: `.venv312/`, `.venv*/`, `venv*/`, `env/`, `.env/`, `bot.pid`, `bot-status.json`, `*.bak.*`, `*.bak.py`, `*.bak.css`, `*.bak.js`
- Plans directory (`06-CLAUDE-LOGS/plans/`) — TRACK in git (commit it)
- Single backlog commit including all bingx-connector, backtester, session logs

### State changes
Plan document created. Execution steps: edit `.gitignore`, verify ignored files removed, `git add` remaining, `git commit`, `git status` verify clean. Commit message specified: "Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03". This matches the actual commit message visible in gitStatus (`914a1b2`).

### Open items recorded
None — straightforward execution plan.

### Notes
This plan corresponds to commit `914a1b2` visible in the gitStatus at the top of the conversation. Execution appears to have been completed.

---

## lively-moseying-nova.md
**Date:** 2026-02-26 (content implies this; no explicit date in doc)
**Type:** Planning (VPS migration guide)

### What happened
Step-by-step guide for migrating the Obsidian Vault to a private GitHub repo and deploying the BingX bot to VPS "Jacky" (76.13.20.191, Ubuntu 24.04, 190GB free, 16GB RAM). Three parts: A (PC git setup), B (VPS setup via SSH), C (ongoing workflow).

Part A: Remove backtester's `.git`, init vault as single repo, create `.gitignore`, stage and commit, push to `S23Web3/Vault`.
Part B: SSH, generate SSH key, clone vault, install Python 3.12 + venv, create `.env`, create systemd service `bingx-bot`, start.
Part C: push from PC, deploy with one SSH command.

### Decisions recorded
- One flat repo for entire vault (backtester `.git` removed)
- No cron — manual push from PC, manual pull + restart on VPS
- Private repo: `S23Web3/Vault`
- Systemd service: `bingx-bot.service`, `Restart=always`, `RestartSec=10`

### State changes
Guide/plan document created. Three helper scripts planned but not yet written: `scripts/migrate_pc.ps1`, `scripts/setup_vps.sh`, `scripts/deploy.ps1`.

### Open items recorded
- All three helper scripts to be created
- VPS `.env` file to be created manually with API keys

### Notes
This is a guide document, not a build spec. Actual migration execution is user-driven. VPS IP 76.13.20.191 mentioned. Architecture diagram shows PC runs ML/data, VPS runs bot 24/7.

---

## logical-coalescing-lark.md
**Date:** 2026-02-27
**Type:** Research / Analysis findings

### What happened
Full findings from analyzing 202 YouTube transcripts from an algo trading channel + FreeCodeCamp ML course, for application to Vince v2 architecture. 14 findings organized into 3 tiers.

TIER 1 (directly applicable now):
1. Unsupervised clustering for Mode 2 auto-discovery (K-means clusters trades by entry-state vectors)
2. Feature importance to prioritize Mode 2 sweep dimensions (XGBoost — stochastics rank highest)
3. RL for exit policy optimization — identified as key missing piece; trains agent on trade lifecycle (state = bars_since_entry + current_pnl_in_atr + k1-k4 + cloud_state + bbw; action = HOLD or EXIT)
4. Random entry + risk management = exits matter more than entries (160% returns with random entry + ATR stop + trailing)

TIER 2 (component-specific):
5. Walk-forward with recent data weighting for Mode 3
6. Survivorship bias caveat for 399-coin dataset
7. Reflexivity: discovered patterns get arbitraged away
8. Held-out partition for Mode 2 patterns (80/20 split)
9. GARCH volatility regime (future scope)
10. LSTM warning: use returns not levels
11. NLP sentiment (future Layer 2)
12-13. Bayesian NN, Transformer attention (future scope)
14. Validated facts: stochastics + RSI consistently top-ranked; ATR stops outperform fixed

Seven updates recommended for Vince v2 concept doc.

### Decisions recorded
- RL Exit Policy Optimizer = new Vince component between Enricher and Dashboard
- Clustering pass added to Mode 2 before permutation sweep
- Feature importance pre-step in Mode 2 (XGBoost on enriched trades)
- Panel 2 (PnL Reversal) build priority made explicit
- Survivorship bias caveat to be added to concept doc
- Vault copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-27-yt-channel-ml-findings-for-vince.md`

### State changes
Research findings document created. No code written. Vince v2 concept doc updates recommended (not yet applied as of this plan).

### Open items recorded
Apply 7 updates to VINCE-V2-CONCEPT-v2.md.

### Notes
Finding 3 (RL exit policy) is described as "THE MISSING PIECE" — previously not incorporated into Vince architecture. This plan is a companion to or precursor of the vault copy it references.

---

## luminous-churning-sedgewick.md
**Date:** 2026-02-28
**Type:** Research audit / Design decisions

### What happened
B2 research audit for Vince — the API Layer and dataclasses block. Audits what exists vs what needs to be built, identifies 7 bottlenecks (labeled B1-B7 within the doc), and makes 4 design decisions with full rationale.

Bottlenecks identified:
- B1: Plugin arg missing from `run_enricher()` signature
- B2: `EnrichedTrade` — dataclass vs DataFrame decision
- B3: `ConstellationFilter` — typed vs generic dict
- B4: Bar index alignment (entry_bar is relative to filtered slice, not full parquet) — CRITICAL
- B5: `run_enricher` signature incomplete
- B6: MFE bar definition ambiguity (first vs last occurrence of max high)
- B7: `SessionRecord` — what is a session?

Four design decisions resolved:
1. Active plugin: per-call argument (thread-safe, testable, agent-callable) — NOT module-level global
2. EnrichedTradeSet: DataFrame-centric (400k rows × 50 cols = sub-second queries)
3. ConstellationFilter: typed base (direction, outcome, min_mfe_atr, saw_green) + `column_filters: dict`
4. SessionRecord: named research session (uuid, name, timestamps, plugin_name, symbols, date_range, notes, last_filter)

### Decisions recorded
All four design decisions stated as Verdicts (explicitly resolved).

### State changes
Research audit document created. Files planned: `vince/__init__.py`, `vince/types.py`, `vince/api.py`. None yet written at time of plan creation.

### Open items recorded
5 questions listed as "block the build" — but the doc then provides verdicts for items 1-4, so only Q5 (run_enricher signature confirmation) and Q6 (MFE bar definition) appear still open.

### Notes
CRITICAL flag on B4 (bar index alignment): this is a build-blocking issue that affects B1 (FourPillarsPlugin) and B3 (Enricher). The spec file `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` Section 7 is explicitly cited.

---

## majestic-conjuring-meerkat.md
**Date:** 2026-03-03
**Type:** Build spec / Design spec

### What happened
Full CUDA acceleration plan for the Four Pillars sweep engine and Dashboard v394. Covers: Numba CUDA kernel (`engine/cuda_sweep.py`), Numba @njit CPU fallback (`engine/jit_backtest.py`), updated sweep orchestrator (`scripts/sweep_all_coins_v2.py`), and Dashboard v394 (`scripts/dashboard_v394.py`).

Full kernel design: one GPU thread per param combo, 12 read-only signal arrays, param_grid [N_combos, 4], output [N_combos, 9] metrics including Welford online variance for Sharpe. Position state stored in `cuda.local.array`. Entry priority matches engine exactly.

Known simplifications documented: fixed ATR SL only (no AVWAP dynamic), no scale-outs, no ADD entries, reentry as immediate market entry, no rebate in kernel.

Dashboard v394 adds: GPU Sweep tab (heatmap + top-20 table), compiled core checkbox for portfolio mode (ThreadPoolExecutor, workers return plain tuples, no st.* calls), sidebar GPU status panel.

Build script: `scripts/build_cuda_engine.py` creates all 4 files, py_compiles each.

### Decisions recorded
- Numba CUDA (not PyTorch) for kernel — bar-by-bar state machine maps cleanly to threads
- tp_mult sentinel: `999.0` (not `0.0`) for "no TP"
- `notional` and `commission_rate` as scalar kernel args (not per-combo)
- 4 max position slots per thread
- Welford's online variance for Sharpe (no per-trade list in kernel)
- `be_lock_atr=0.0` as fixed constant
- ThreadPoolExecutor: workers return plain tuples, all st.* calls in main thread
- Equity curve bug from v392 fixed in v394: cache invalidation tied to `params_hash`
- Vault log copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-cuda-sweep-engine.md`

### State changes
Build spec created. 18 audit issues documented and resolved in this plan revision. Files planned: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/sweep_all_coins_v2.py`, `scripts/dashboard_v394.py`, `scripts/build_cuda_engine.py`. Expected performance: ~400 coins × ~2s GPU = ~13 minutes (vs 6-60 hours current).

### Open items recorded
Verification steps: CUDA check, single-coin sweep, dashboard GPU tab, CUDA fallback test.

### Notes
This is a thorough and audited build spec. The 18 issues were identified and resolved within this plan document itself before handing off to build. This plan corresponds to the session log `2026-03-03-cuda-dashboard-v394-build.md` visible in gitStatus as modified.

---

## mellow-watching-lemon.md
**Date:** 2026-02-28
**Type:** Research audit / Build spec

### What happened
B3 Enricher research audit and scope plan for Vince v2. Full audit of what exists vs what needs to be built for the Enricher component. Eight critical blockers documented with resolutions:

BLOCKER 1: `mfe_bar` not in Trade384 — must add to track which bar MFE occurred (breaking change)
BLOCKER 2: `compute_signals()` signature mismatch (takes `df, params=None` vs `self, ohlcv_df`)
BLOCKER 3: Indicator column naming convention mismatch (`stoch_9` vs `k1_9`)
BLOCKER 4: `diskcache` not installed — pip install needed
BLOCKER 5: Bar index offset — run_backtest() must add slice start offset to all bar indices
BLOCKER 6: OHLC tuple storage format undefined

Six improvements identified: shared Numba ATR, expose raw stoch values, include mfe_bar/mae in trade_schema, FanoutCache size cap (2GB), Enricher as context manager, compliance CLI.

Eight open questions listed.

### Decisions recorded
- Recommendations made: FanoutCache (8 shards, 2GB cap), 4 separate OHLC columns
- Implementation order: position_v384.py → four_pillars_plugin.py → test_plugin → diskcache + cache_config → enricher.py → test_enricher
- `diskcache.FanoutCache` for concurrency (Optuna parallelism)
- Cache key: `{symbol}_{timeframe}_{params_hash}` (MD5 first 8 chars)
- `mfe_bar` is the single most important decision before build starts

### State changes
Research audit document created. Files planned: `strategies/four_pillars_plugin.py` (new — separate from four_pillars.py), `vince/__init__.py`, `vince/enricher.py`, `vince/cache_config.py`, `tests/test_enricher.py`, `tests/test_four_pillars_plugin.py`. Modification planned for `engine/position_v384.py` (add `mfe_bar`).

### Open items recorded
Q1-Q8 listed; some are recommendations, others require user decisions (especially Q1: modify position_v384.py directly vs create v385).

### Notes
This document is STATUS: RESEARCH/AUDIT — not yet scoped for build. Decisions on Q1 (mfe_bar tracking approach) and Q2 (column renaming location) are noted as blocking before build can start.

---

## misty-sniffing-quail.md
**Date:** Approximately 2026-02-09 (references Qwen model, "IMMEDIATE EXECUTION PLAN: Updated 2026-02-09")
**Type:** Build plan / Strategy spec (early-stage)

### What happened
Very large plan document covering: (1) Root cause analysis of Four Pillars v3.7.1 directional filter problem, (2) Solution design for v3.8 in both Pine Script and Python, (3) Vince ML Analysis Pipeline architecture (7-script pipeline), (4) Immediate execution plan using Qwen code generation (overnight run of 20-file generation).

Root cause: B signals bypass Cloud 3 check, Ripster filter OFF by default, two state machines run in parallel with no mutual exclusion.

v3.8 changes: Cloud 3 directional filter (always on), ATR-based BE raise (replaces fixed $2/$4/$6), MFE/MAE tracking, commission updated to 0.08%.

Vince ML pipeline: data_prep → label_generator (Triple Barrier) → xgboost_trainer → parameter_sweep → walk_forward → risk_methods → generate_report.

Immediate execution plan: run `START_GENERATION.bat` overnight to generate 20 Python files via Qwen qwen3-coder:30b model. Six phases over 6 days planned.

### Decisions recorded
- Cloud 3 filter always on (not optional via `i_useRipster`)
- ATR-based BE trigger: 0.5× ATR, lock: 0.3× ATR (as starting values)
- Commission: `strategy.commission.cash_per_order = 8` (Pine Script), `0.08%` (Python)
- Qwen generates boilerplate, Claude reviews/fixes
- GPU acceleration: XGBoost `tree_method='gpu_hist'`, PyTorch CUDA, CuPy arrays

### State changes
Plan document created. Infrastructure (auto_generate_files.py, startup_generation.ps1, START_GENERATION.bat, QWEN-MASTER-PROMPT) already exists per checklist. This is an early-phase plan from around 2026-02-09 — predates later v3.8.4 and Vince v2 architecture.

### Open items recorded
5 open questions for user: Cloud 3 chop zone behavior, B/C signal behavior in fresh open, ATR BE defaults, analysis scope (all coins vs top 20 vs low-price), GPU CUDA version.

### Notes
This plan predates the current Vince v2 architecture (which uses plugin abstraction, not this direct pipeline). The Qwen-generated code was likely the prototype/early version. The final architecture evolved significantly from this plan.

---

## modular-strolling-shamir.md
**Date:** 2026-02-28
**Type:** Session plan / Build schedule

### What happened
Session plan for 2026-02-28 covering two major work streams: BingX Live Trades Dashboard (Block 0) and Vince B1-B6 builds. Establishes token conservation rules: no agents, no speculative searches, Ollama handles boilerplate-only files.

Block 0: BingX dashboard (`PROJECTS/bingx-connector/dashboard.py`) — 6 panels (summary cards, open positions, closed trades, exit breakdown, grade analysis, cumulative PnL). Data sources: `state.json` + `trades.csv`. Auto-refresh 60s. Read-only.

Block 1-6: Vince FourPillarsPlugin → API+Types → Enricher → PnL Reversal data module → Constellation Query Engine → Dash App Shell.

Four files delegated to Ollama: `vince/types.py` (dataclasses), `vince/__init__.py`, `vince/pages/__init__.py`, `vince/assets/style.css`.

### Decisions recorded
- BingX dashboard is read-only (never touch `main.py` or `state_manager.py`)
- No LSG% in BingX dashboard (MFE not tracked by bot — lives in Vince Panel 2)
- Files that must NOT be modified: `strategies/base_v2.py`, `signals/four_pillars_v383_v2.py`, `engine/backtester_v384.py`, `PROJECTS/bingx-connector/main.py`
- `signals/four_pillars.py` and `signals/state_machine.py` modified 2026-02-27 (stage 2 filter) — plugin must wrap CURRENT signal interface

### State changes
Session plan document created. This plan established the agenda for the 2026-02-28 session. Multiple build specs (kind-yawning-reef, luminous-churning-sedgewick, mellow-watching-lemon) correspond to the research done during this session.

### Open items recorded
End state target: BingX dashboard running + Vince app with sidebar + Panel 2 functional.

### Notes
This is a session-level orchestration plan, not a detailed build spec for any single file. References to later plan files (B1=kind-yawning-reef, B2=luminous-churning-sedgewick, B3=mellow-watching-lemon) confirm these were all built in the same session.

---

## moonlit-snuggling-mochi.md
**Date:** 2026-02-28
**Type:** Planning (skill file update)

### What happened
Plan to add Part 4 "Community-Sourced Traps & Patterns" to the Dash skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`). The community audit via WebFetch was blocked by hook; WebSearch was used instead and retrieved 15+ forum threads.

Seven community-sourced findings: extendData + Candlestick traps (stacking ghost artifacts, format strictness, performance cliff at 2500+ bars), dcc.Interval blocking behavior (queue backlog when callback exceeds interval), relayoutData + Candlestick infinite loop risk (GitHub issues #355, #608), ag-grid styleConditions side effects (`Math` unavailable, overrides textAlign), WebSocket vs dcc.Interval (3x faster for <500ms), background callback overhead (only worthwhile >10s; APScheduler + Gunicorn without `--preload` = data corruption risk), candlestick + rangebreaks performance cliff (unusable with >2 years of bars).

### Decisions recorded
- Append Part 4 (~180 lines) to SKILL.md after line 1447
- Update version block to v1.2
- Write vault copy of this plan

### State changes
Plan document created. Skill file to be updated from v1.1 to v1.2 (~1447 → ~1630 lines).

### Open items recorded
Execute the edit to SKILL.md, verify line count growth and section headers.

### Notes
None.

---

## mossy-bubbling-waterfall.md
**Date:** 2026-02-26
**Type:** Planning (git operations)

### What happened
Plan for git push of 170 items (27 modified + ~143 untracked) since initial commit `1e1c49b`. Pre-flight check of what `.gitignore` already handles. Four items flagged for user decision: `*.bak.*` files (9 total, `.gitignore` has `*.bak` but not `*.bak.py`), `.playwright-mcp/`, `.claude/settings.local.json`, and `PROJECTS/yt-transcript-analyzer/output/` (608 generated files).

Commit planned: "Vault update: bingx connector live + dashboards, vince build specs, yt analyzer v2, session logs". This matches commit `0b12d60` in gitStatus.

### Decisions recorded
- Add to `.gitignore`: `.playwright-mcp/`, `.claude/settings.local.json`, `*.bak.*`, `PROJECTS/yt-transcript-analyzer/output/`
- Stage all remaining non-ignored files (`git add .`)
- All 4 categories pushed in single commit

### State changes
Plan document created. Corresponds to commit `0b12d60` visible in gitStatus.

### Open items recorded
Execute: update `.gitignore`, `git add .`, `git commit`, `git push origin main`.

### Notes
This is a straightforward git operations plan. The corresponding commit exists in gitStatus.

---

## peppy-swinging-dusk.md
**Date:** 2026-02-25
**Type:** Audit session / Session log action

### What happened
Full audit of BingX connector against two bug lists: 5-item fault report and 17-item UML bug findings (C01-C08, S01-S08). Plus 3 session bugs fixed during the session (leverage mode, buffer off-by-one, DEFAULT_STATE shallow copy). All findings compiled with status (FIXED / DOC ONLY / OPEN).

Fault Report: F1-F5 — all resolved (FIXED or CLEARED or INFORMATIONAL).
UML Connector Bugs (C01-C08): C01=DOC ONLY, C02-C08=FIXED.
UML Strategy Bugs (S01-S08): S03-S06=DOC ONLY, S07=FIXED, S01/S02/S08=OPEN.

Session bugs fixed: leverage API loop (SB1), buffer off-by-one 200→201 (SB2), DEFAULT_STATE deepcopy (SB3).

Live log analysis: 67/67 tests passing, warmup at 201 bars, no errors, signal engine active returning "No signal" (expected).

### Decisions recorded
- Audit is read-only review — only action is appending findings to existing session log
- Open items flagged for Step 3 (go-live): S08 (multi-slot vs live single-slot P&L mismatch) and S01/S02 (cold-start false signal risk)

### State changes
Audit findings compiled. Session log at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-25-bingx-connector-session.md` to be appended (not overwritten). No code changes needed.

### Open items recorded
- S08: Rerun backtest with `max_positions=1, enable_adds=False, enable_reentry=False` before go-live
- S01/S02: Add `cold_start_bar_count` guard in plugin
- First A/B signal to fire (waiting)

### Notes
Buffer fix (SB2): `ohlcv_buffer_bars: 200` → `201` corrects the trim-to-200 logic that prevented signals from firing. This was previously identified as the root cause of the stuck counter (per MEMORY.md critical lesson).

---

## piped-rolling-blanket.md
**Date:** 2026-02-26
**Type:** Planning / Review + Decision

### What happened
Review of 24-hour demo results on 1m timeframe + plan to switch to 5m + identify production readiness work.

Demo stats: 105 trades opened and closed, 0 errors, 0 crashes, -$354.27 daily P&L, 428 blocked signals ("Too Quiet" ATR filter), ~90% EXIT_UNKNOWN exits.

Critical finding: EXIT_UNKNOWN on ~90% of exits — BingX VST may clean up conditional orders before 60-second monitor check, so exit price uses SL estimate (inaccurate). Fix: query trade history for actual fill price.

Four phases of work planned:
- Phase 1: Config switch (5m), commission rate fix (0.001→0.0008), EXIT_UNKNOWN fix (trade history query)
- Phase 2: Reliability (daily reset on startup, retry with backoff, order validation, graceful shutdown)
- Phase 3: Observability (hourly metrics, Telegram at 50% loss limit)
- Phase 4: Config tuning (after 5m demo 24h+)

### Decisions recorded
- Switch timeframe to 5m (`config.yaml` line 4)
- Fix commission rate: `0.001` → `0.0008` in `position_monitor.py` line 186
- Fix EXIT_UNKNOWN: query `/openApi/swap/v2/trade/allOrders` for actual fill price (P0 fix)
- Warmup stays at 200 bars on 5m (16.7h history at startup)
- Bot stability confirmed SOLID — infrastructure works

### State changes
Plan document created. Five files to modify: `config.yaml` (timeframe), `position_monitor.py` (commission + exit fix + daily reset), `data_fetcher.py` (retry backoff), `executor.py` (order validation), `main.py` (graceful shutdown).

### Open items recorded
All Phase 2-4 work items. First 5m signal to fire after 16.7h warmup.

### Notes
1m was expected to be bad (backtester confirms 5m >> 1m for all low-price coins per MEMORY.md). The -$354 loss is consistent with backtester findings.

---

## purring-herding-manatee.md
**Date:** 2026-02-26
**Type:** Planning (git + VPS deploy)

### What happened
Plan to write the vault-level `.gitignore` (the missing piece from the VPS migration guide in `lively-moseying-nova.md`) and update the bingx-connector `.gitignore`. Bot code described as production-ready (67/67 tests, 20.5h stable run, all fixes applied). Config already switched to 5m.

`.gitignore` content specified: excludes 33GB of data, Books/, postgres/, `.obsidian/`, `.env`, `__pycache__`, `venv/`, `logs/`, ML binaries, parquet/meta files, bot runtime state. Keeps all `.md`, `.py`, `.yaml`, `.json` files.

Timeline after deploy: 0-16.7h warmup (no trades), 16.7h+ signals fire, 40h+ total: run `audit_bot.py`.

### Decisions recorded
- No code changes needed (all paths relative, cross-platform, `Path(__file__).resolve()`)
- Backtester `.git` already removed per migration guide
- Two `.gitignore` files to write: vault-level + bingx-connector level
- VPS deploy: clone → venv → `.env` → systemd `bingx-bot` → start

### State changes
Plan document created for creating two `.gitignore` files. References existing migration guide at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-26-vault-vps-migration.md`.

### Open items recorded
After user executes Parts A, B, C from migration guide: verify bot runs on VPS, after 24h trading run audit_bot.py.

### Notes
This plan is the final missing piece (`.gitignore`) before VPS deployment could proceed. The migration guide referred to is `lively-moseying-nova.md` in this batch.

---

## refactored-imagining-taco.md
**Date:** 2026-02-16
**Type:** Build plan / Feature spec

### What happened
Portfolio enhancement plan for the Four Pillars dashboard — 4 features: (1) reusable portfolio selections (JSON persistence, save/load/compare), (2) PDF export (multi-page reportlab report), (3) enhanced per-coin analysis (10 new metrics + drill-down expander with 5 tabs), (4) unified capital model (post-processing filter approach, two-mode toggle).

Architecture discovery: backtester is NOT a unified portfolio engine — single-coin bottoms-up aggregator; cross-coin capital sharing not implemented. Current capital model already tracks unified position count (not per-coin independent pools as thought). "Money sits idle" confirmed — max capital used can be much less than total allocated.

Feature 4 implementation: Approach 1 recommended (post-processing filter, dashboard-only logic, no engine changes).

### Decisions recorded
- Portfolio JSON storage: `portfolios/*.json` with name, created timestamp, coins, selection_method, params_hash
- PDF library: reportlab + matplotlib
- Unified capital: post-processing filter (not true portfolio engine)
- Auto-save Random N selections with date suffix
- Per-coin drill-down: 5 tabs (Trades, Equity Curve, Trade Distribution, MFE/MAE, Risk Metrics)
- Design document `DASHBOARD-DESIGN.md` to be built after enhancement implementation
- Recommended implementation order: 1→2→3→4

### State changes
Build plan created. Files planned: `utils/portfolio_manager.py`, `utils/pdf_exporter.py`, `portfolios/` directory, `scripts/dashboard.py` (~500 lines of changes). New dependency: `reportlab`.

### Open items recorded
5 open questions for user before Phase 4: capital mode default, entry priority in unified mode, PDF detail level, rejected trades visibility, portfolio comparison feature.

### Notes
This is a 2026-02-16 plan — predates the current v3.8.4/v3.9.x dashboard work. Status of these enhancements is unknown from this document alone.

---

## replicated-scribbling-quokka.md
**Date:** 2026-02-28
**Type:** Planning (skill file update)

### What happened
Plan to add Part 3 "Trading Dashboard Knowledge" to the Dash skill file. The skill had zero trading-specific content. 10 missing knowledge areas identified: candlestick/OHLCV, real-time patterns, panel taxonomy, equity/drawdown charts, multi-chart synchronization, conditional ag-grid coloring, timezone handling, order book, rolling metrics, alert/status indicators.

8 subsections planned for addition: (1) Candlestick charts, (2) Trading dashboard panel taxonomy, (3) Real-time data patterns, (4) Equity curve & drawdown, (5) Multi-chart sync via relayoutData, (6) Conditional formatting in ag-grid, (7) Timezone-aware data in Plotly, (8) Order book/depth chart.

Also: update frontmatter to include trading dashboard keywords, bump version to v1.1.

### Decisions recorded
- Append Part 3 after line ~1054 (before Version History)
- Knowledge-dense, concise format — no large code walls
- Vault copy: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-dash-skill-trading-dashboard-enrichment.md`
- Version bump to v1.1

### State changes
Plan document created. Skill file (`C:\Users\User\.claude\skills\dash\SKILL.md`) to be modified from 1,064 lines to ~1,254 lines. Note: `moonlit-snuggling-mochi.md` in this batch plans v1.2 (adding community-sourced traps) — these are sequential updates (1.1 then 1.2).

### Open items recorded
Execute edit to SKILL.md, verify 8 subsections present, verify version updated, confirm no existing sections modified.

### Notes
This plan (Part 3, v1.1) must precede `moonlit-snuggling-mochi.md` (Part 4, v1.2). Both were dated 2026-02-28.
