# Research Batch 11 — Findings
**Files:** 2026-02-03 through 2026-02-14 build journals and session logs
**Generated:** 2026-03-06

---

## 2026-02-03-build-journal.md
**Date:** 2026-02-03
**Type:** Build session

### What happened
Eight sessions focused on Pine Script indicator development. Sessions 1-2 audited existing indicators and refined the Quad Rotation Stochastic (QRS) spec. Session 3 ran 5,000-scenario statistical testing on angle calculation approaches; selected the "agreement multiplier" method. Session 4 validated with 5,000-sample testing, yielding 92.4% win rate; created complete Pine Script v6 build spec. Session 5 found 9 major bugs in the spec; re-validation showed 92.1% win rate with 5-bar lookback. Session 6 conducted critical code review and found 11 major implementation bugs (stochastic calc, 60-10 double smoothing, state machine, divergence tracking, alert naming, missing alerts, rotation clarity, JSON payload issues). Session 7 fixed all 11 bugs and added edge detection to all alerts. Session 8 built the Quad Rotation FAST v1.1 spec (9-3 + 14-3 primary triggers, 40-4/60-10 slow context) and found/fixed 5 more bugs.

### Decisions recorded
- Selected agreement multiplier approach for angle calculation (over composite angle and average angles)
- 5-bar lookback for divergence detection
- 60-10 requires DOUBLE smoothing (SMA of SMA)
- State machine must use if/else if chains, not multiple if blocks
- Edge detection pattern: `signal and not signal[1]` fires once

### State changes
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-v4-BUILD-SPEC.md` created (v4.1)
- `02-STRATEGY/Indicators/Quad-Rotation-Stochastic-FAST-BUILD-SPEC.md` created (v1.1)
- `skills/pinescript/SKILL.md` updated to v2.0
- `skills/pinescript/references/technical-analysis.md` created
- `skills/n8n/SKILL.md` created

### Open items recorded
1. Build v4.1 Pine Script in Claude Code
2. Build FAST v1.1 Pine Script in Claude Code
3. Test both on TradingView
4. Set up n8n webhook integration

### Notes
None.

---

## 2026-02-04-build-journal.md
**Date:** 2026-02-04
**Type:** Build session

### What happened
Eight sessions of Pine Script work and strategy spec development. Session 1: FAST v1.3 build with philosophy correction; FAST v1.4 selected as production. Session 2: reviewed AVWAP Anchor Assistant (fixed VSA alert edge-triggering), QRS indicators (fixed 40-4 smoothing from 4 to 3 — Kurisko original), and BBWP v2 (added MA cross persistence timeout 10 bars, timestamp display, hidden plots). Session 3: CRITICAL — v1.0 spec referenced "Stoch 55" which doesn't exist in any built indicator. Created corrected `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` with 40-4 divergence as SUPERSIGNAL and 9-3 for exit management. Session 4: Added 15 hidden plots to `ripster_ema_clouds_v6.pine` for Four Pillars integration (cloud states, price position, cloud direction, crossovers, scores, raw EMAs). Session 5: Built `four_pillars_v2.pine` (~500 lines) implementing all 4 pillars, grade calculation (A/B/C/No Trade), position management, dashboard, stochastic mini panel, 11 alert conditions. Session 6-8: Built `four_pillars_v3.pine` (v3.1-v3.3) with clean Quad Rotation logic using 9-3 as trigger, 3-bar lookback, dynamic SL (1x or 2x ATR based on Ripster cloud), then updated filters through v3.2 (40-3 D line position) and v3.3 (60-10 D line, fixed 20/80 thresholds).

### Decisions recorded
- FOUR-PILLARS-STRATEGY-v1.0 deprecated — it was built before Kurisko methodology was researched
- 40-4 smoothing is 3 (not 4) — Kurisko original
- 40-4 divergence is SUPERSIGNAL (highest priority)
- 9-3 is TRIGGER (fastest stochastic), all others must be in zone
- 3-bar lookback for "in zone" check
- 60-10 D filter fixed at 20/80 (not tied to input)
- `FOUR-PILLARS-COMBINED-BUILD-SPEC.md` deprecated

### State changes
- `Quad-Rotation-Stochastic-FAST.pine` — 40-4 smoothing fixed
- `Quad-Rotation-Stochastic-v4-CORRECTED.pine` — 40-4 smoothing fixed, hidden plot added
- `avwap_anchor_assistant_v1.pine` — edge-triggered VSA alerts
- `bbwp_v2.pine` — MA cross timeout + timestamp + hidden plots
- `FOUR-PILLARS-STRATEGY-v2-BUILD-SPEC.md` — NEW
- `ripster_ema_clouds_v6.pine` — 15 integration hidden plots added
- `four_pillars_v2.pine` — NEW combined indicator
- `four_pillars_v3.pine` — v3.3 with 60-10 D filter

### Open items recorded
1. Create strategy version of v3 for backtesting
2. Add trailing stop logic
3. Test all indicators in TradingView
4. Set up n8n webhook integration

### Notes
Root cause of v1.0 spec error identified: strategy was conceptualized on 2026-01-29 before Kurisko methodology was researched. Spec v1.0 was never updated after QRS indicators were built correctly.

---

## 2026-02-05-build-journal.md
**Date:** 2026-02-05
**Type:** Build session

### What happened
Eleven sessions of Pine Script strategy development. Session 1: Reviewed v3.4.1 strategy, hit context limit. Session 2: Added `i_useTP` and `i_useRaisingSL` toggles to indicator (v3.4.2); changed Phase 3 trail from Cloud 3 to Cloud 4. Session 3: Major SL overhaul — removed entire phased P0-P3 system and replaced with continuous Cloud 3 (34/50) ± 1 ATR trail every candle; added Cloud 2 re-entry A trade; removed Cloud 2 flip hard close exit; file reduced 645 → ~495 lines. Session 3b: Added trail activation gate (Cloud 3/4 cross), entry position replacement logic, priority reorder (re-entry A above B/C), inverse SL bug fix. Session 4: Created `four_pillars_v3_5.pine` — stochastic smoothing fix (all 4 stochastics now use raw K, 60-10 double smoothed). Session 5: Built `four_pillars_v3_5_strategy.pine` from scratch — pyramiding=1, smoothed stochastics, trail activation gate, no Cloud 2 exit, A-only direction flips. Session 6: Fixed 3 bugs (dual exit conflict, position replacement invisible, state desync after exit). Session 7: Removed position replacement (was killing winners and creating margin-call fragments). Session 8: v3.5.1 — CRITICAL root cause: "Stoch 9 1 3" means K smoothing=1 (raw K, no SMA). v3.5's "smoothing fix" made values equivalent to D line. Reverted to raw K. Also fixed position sizing ($500 fixed vs 100% equity) and B/C defaults (OFF by default). Sessions 9-11: Built v3.6 with AVWAP trailing, separate A/BC order IDs, BC exits on Cloud 2 cross or 60-10 K/D cross, Cloud 3/4 parallel filter for BC, AVWAP recovery re-entry, volume flip filter, dashboard fix.

### Decisions recorded
- Phased SL system (P0-P3) removed — replaced with continuous Cloud 3 trail
- No position replacement (kills winners)
- Stochastic K uses raw K (smooth=1) — matches "Stoch 9 1 3" setting in TradingView
- B/C defaults OFF — user must opt in
- A trades can flip direction; B/C/RE can only enter flat
- Volume flip filter applies ONLY to A direction flips, not fresh flat entries
- `var table dash` must be at global scope (not inside conditional block)

### State changes
- `four_pillars_v3_4.pine` updated to v3.4.2
- `four_pillars_v3_5.pine` NEW — v3.5.1
- `four_pillars_v3_5_strategy.pine` NEW — v3.5.1
- `four_pillars_v3_6_strategy.pine` NEW — v3.6
- `four_pillars_v3_6.pine` NEW — v3.6 indicator

### Open items recorded
None explicitly listed.

### Notes
Critical lesson captured: stochastic smoothing regression in v3.5 was caused by misunderstanding "Stoch 9 1 3" — the middle "1" is K smoothing (raw K), not D smoothing. Applying SMA(K,3) made values equivalent to D line, causing strategy to see midrange values while real K was in extreme zones.

---

## 2026-02-06-build-journal.md
**Date:** 2026-02-06
**Type:** Build session

### What happened
Two main sessions. Session 1: Built `four_pillars_v3_7_strategy.pine` — "rebate farming" architecture with tight static SL (1.0 ATR) and TP (1.5 ATR), free flips on any A/B/C signal, tracking bars since last ANY signal (not just A), single order ID, 3-bar cooldown. Session 2: CRITICAL BUG — `commission.percent=0.06` applies to CASH qty ($500), not notional ($10K with 20x leverage). Reality: $6/side = $12 round trip, not $0.30/0.60. Combined with phantom trade bug (`strategy.close_all()` + `strategy.entry()` = 2 trades per flip = $24/flip). Emergency fix in `four_pillars_v3_7_1_strategy.pine`: changed to `cash_per_order=6`, flip via `strategy.entry()` only (auto-reverses), added `strategy.cancel()` before every flip, 3-bar cooldown on ALL entry paths, running commission total in dashboard. Also exported CSV for validation from TradingView backtest.

### Decisions recorded
- commission.percent on leveraged strategies is wrong — must use cash_per_order
- cash_per_order=6 for $10K notional at 0.06% taker rate
- strategy.close_all() + strategy.entry() creates 2 trades (phantom trade bug) — use strategy.entry() only (auto-reverses)
- Cooldown must apply to ALL entry paths (A, BC, flip, re-entry)
- entryBar does NOT reset on exit — persists between trades

### State changes
- `four_pillars_v3_7_strategy.pine` NEW — rebate farming
- `four_pillars_v3_7_1_strategy.pine` NEW — commission fix + cooldown
- `four_pillars_v3_7_1.pine` NEW — indicator version
- Exported backtest CSV: `07-TEMPLATES/4Pv3.4.1-S_BYBIT_MEMEUSDT.P_2026-02-06_fcc84.csv`

### Open items recorded
1. Build Python backtester to validate v3.7.1 with correct commission
2. Test breakeven+$X raise on historical data
3. Fetch historical data for multiple coins

### Notes
Commission bug was previously undetected. $0.30 vs $6 per side is a 20x error. All prior TradingView backtests were underestimating commission costs by 20x for leveraged strategies.

---

## 2026-02-07-build-journal.md
**Date:** 2026-02-07
**Type:** Build session

### What happened
Six sessions covering planning, skill updates, full Python backtester build, live data, and CUDA installation. Session 1: Created master execution plan (WS1-WS5) — five workstreams from data pipeline to Monte Carlo validation. Session 2: Completed WS1 (Pine Script skill update) and WS2 (two progress documents). Session 3: Built complete Python backtester from scratch in `PROJECTS/four-pillars-backtester/` — data pipeline (Bybit v5 API, backward pagination, WEEX had no historical pagination), signal engine (raw K stochastics, Ripster clouds, A/B/C state machine), backtest engine (bar-by-bar loop, MFE/MAE tracking, position class with breakeven raise, commission + rebate settlement, metrics). Session 4: Fetched 3-month 1m data for 5 low-price coins; ran BE sweeps. Results: 1m = mostly negative (only RIVER profitable at +$87K), 5m = ALL PROFITABLE (total +$97K across 5 coins, 20,283 trades, $4.79/trade). Session 5: Built `scripts/fetch_sub_1b.py` using CoinGecko for market cap filtering + Bybit for candle data; discovered 394 sub-$1B coins; kicked off overnight fetch at 19:53. Session 6: Installed NVIDIA CUDA 13.1 toolkit; confirmed RTX 3060 12GB VRAM, driver 591.74. PyTorch, Optuna, XGBoost NOT installed yet.

### Decisions recorded
- Bybit v5 API for historical data (WEEX has no pagination for historical)
- Raw K (smooth=1) for all 4 stochastics in Python
- 5m timeframe superior to 1m — all coins profitable vs mostly negative
- Sub-$1B market cap = coin universe for backtesting

### State changes
- `.claude/plans/warm-waddling-wren.md` NEW — Master plan WS1-WS5
- Pine Script skill files updated
- `07-BUILD-JOURNAL/2026-02-07-progress-review.md` NEW
- `07-BUILD-JOURNAL/commission-rebate-analysis.md` NEW
- `PROJECTS/four-pillars-backtester/` created (entire tree)
- `data/cache/*.parquet` — 5 coins' 3-month 1m data
- `data/sub_1b_coins.json` — 394 coin list
- `scripts/fetch_sub_1b.py` NEW

### Open items recorded
1. Wait for overnight fetch (ETA ~02:00)
2. Install PyTorch with CUDA (user task)
3. Run 299-coin backtest on 5m
4. Build v3.8 ATR-based BE module

### Notes
Key discovery logged: 5m timeframe makes ALL coins profitable. Commission bleed on 1m (~20K trades) overwhelms edge. Bug fixed during dev: `df.set_index('datetime')` removes datetime from columns → rebate settlement never triggered. Fixed by checking `df.index.name`.

---

## 2026-02-08-build-journal.md
**Date:** 2026-02-08
**Type:** Build session

### What happened
Overnight fetch completed (started 2026-02-07 19:53:55, completed 2026-02-08 02:18:49, ~6.5 hours). Results: 394 total coins discovered, 363 successfully fetched, 31 failed (rate limited), 299 full data (>3MB, 3 months), 70 partial/tiny, 38.5M total candles, 1.36 GB on disk. Data quality: zero gaps, zero NaN, zero dupes, zero bad prices across all 299 complete coins. Issues: RIVER + SAND data overwritten, 31 coins rate-limited (needs backoff improvement), 70 partial fetches. Created comprehensive handoff document `07-BUILD-JOURNAL/2026-02-09-session-handoff.md` for context continuity.

### Decisions recorded
None explicitly stated — this was primarily a results recording session.

### State changes
- `data/cache/*.parquet` — 369 Parquet files (1.36 GB)
- `data/fetch_log.txt` — 2,479 lines
- `data/refetch_list.json` — 101 entries (31 failed + 70 incomplete)
- `07-BUILD-JOURNAL/2026-02-09-session-handoff.md` NEW — handoff document

### Open items recorded
- Install PyTorch (user task)
- Refetch 101 coins (needs `--refetch` flag)
- RIVER + SAND re-fetch
- v3.8 ATR-based BE module
- 299-coin full backtest
- WS3D exit strategy comparison
- WS4 ML optimizer (blocked on PyTorch)
- WS5 v4 + Monte Carlo (blocked on WS4)

### Notes
RIVER and SAND data were overwritten during sub-$1B fetch run (data quality issue from 2026-02-07 session).

---

## 2026-02-09-build-journal.md
**Date:** 2026-02-09
**Type:** Build session

### What happened
Session focused on book analysis and VINCE upgrade planning. 9 books analyzed and rated: Maximum Adverse Excursion (Sweeney, 9/10), Advances in Financial ML (De Prado, 9/10), ML for Algorithmic Trading (Jansen, 8/10), Trade Your Way to Financial Freedom (Van Tharp, 7/10), AI in Finance (Hilpisch, 5/10), RL for Finance (Hilpisch, 4/10), Python for Algo Trading (Hilpisch, 3/10), Listed Volatility Derivatives (Hilpisch, 1/10), Derivatives Analytics (Hilpisch, 1/10). VINCE upgrade plan synthesized from all books: 6 priority upgrades identified (drawdown constraint in Optuna, pre-entry XGBoost features, ATR regime gate, Sortino objective, data augmentation, options flow filter). Items deemed NOT worth doing: RNN for price prediction, DQL trading agent, options pricing models. Andy project skill created for FTMO prop trading ($200K, cTrader). Installed pymupdf4llm. PyTorch CUDA installed: `torch-2.10.0+cu130` on RTX 3060 12GB. Data refetch complete: 99 coins re-fetched, 0 failures, cache now 399 files / 1.74 GB. RIVER + SAND restored.

### Decisions recorded
- Sortino ratio preferred over Sharpe (downside-only risk, non-normal returns)
- Drawdown constraint: if max_drawdown > 10%, return float('-inf') in Optuna objective
- Pre-entry features: 11 features including stoch values, cloud distance, ATR percentile, volume ratio
- Half-Kelly or fractional Kelly for position sizing (not full Kelly)
- RNN for price prediction deemed not worth doing
- Andy project separated from Four Pillars (own skill, own rules)

### State changes
- `.claude/skills/andy/andy.md` NEW
- All project skills updated (four-pillars-project, vince-ml, andy)
- Data cache: 399 files / 1.74 GB (RIVER + SAND restored)
- PyTorch CUDA 2.10.0+cu130 installed
- pymupdf4llm installed

### Open items recorded
- Full 399-coin backtest on 5m
- WS4 ML optimizer
- WS4B MFE/MAE depth analysis
- De Prado concepts: Meta-Labeling, Purged CV, Triple Barrier comparison

### Notes
LSG 86% figure mentioned in 2026-02-07 progress review is confirmed here via book synthesis context.

---

## 2026-02-10-build-journal.md
**Date:** 2026-02-10
**Type:** Build session

### What happened
v3.8 BE sweep complete: 60 backtests (5 coins x 12 BE configs), saved to PostgreSQL run_id 2-61. Fixed-$ BE wins on ALL coins vs ATR-based BE. ATR trigger distances too wide for low-price coins. Cloud 3 filter impact measured: blocks ~67% of trades, per-trade quality drops from $4.79 to $3.79 (filter too aggressive for rebate farming). Added ATR-based BE raise to `engine/position.py` (be_trigger_atr + be_lock_atr params). Built 399-coin sweep script `scripts/sweep_all_coins.py` with auto-discovery, 5m timeframe, PostgreSQL save, CSV/JSON/log output, dry-run/no-db/top-N CLI flags. Established MEMORY.md hard rules: OUTPUT = BUILDS ONLY, NO FILLER, NO BASH EXECUTION, NEVER use emojis.

### Decisions recorded
- Fixed-$ BE superior to ATR-based BE on all tested coins
- Cloud 3 filter too aggressive for rebate farming volume strategy
- Hard rules established for all future sessions

### State changes
- ATR-based BE raise added to `engine/position.py`
- `engine/backtester.py` — pass-through to Position constructor
- `scripts/sweep_all_coins.py` NEW — 399-coin sweep
- `MEMORY.md` — hard rules added
- PostgreSQL: run_id 2-61 (60 backtests)
- Ollama prompt: `trading-tools/prompts/SWEEP-ALL-COINS-PROMPT.md`

### Open items recorded
1. Run `python scripts/sweep_all_coins.py`
2. Optuna on top 10 coins
3. MFE/MAE depth analysis from PostgreSQL
4. ML pipeline (ml/ directory)

### Notes
None.

---

## 2026-02-11-build-journal.md
**Date:** 2026-02-11
**Type:** Build session

### What happened
Three-phase build to complete all missing infrastructure files. Phase 1: `scripts/build_missing_files.py` (1570 lines) created 10 of 11 missing files (1 skipped — already existed from Qwen build): exit_manager.py, indicators.py, signals.py, cloud_filter.py, four_pillars_v3_8.py, optimizer/walk_forward.py, optimizer/aggregator.py, ml/xgboost_trainer.py, gui/coin_selector.py, gui/parameter_inputs.py. 19/19 tests passed. Phase 2: Full codebase inventory — 52 executable Python files + 2 Pine Script files, ~8,600+ lines total. Gaps identified: dashboard missing ML tabs, test script missing, WEEXFetcher import bug in run_backtest.py, ml/live_pipeline.py not built. Phase 3: `scripts/build_staging.py` (1692 lines) written to create 4 staging files (dashboard.py 5-tab ML dashboard, test_dashboard_ml.py, run_backtest.py fix, staging/ml/live_pipeline.py). Build script written but NOT YET RUN. Added SCOPE OF WORK FIRST rule to MEMORY.md. Updated Vince ML Build Status: all 9 ML modules now BUILT. MEMORY.md trimmed to 184 lines.

### Decisions recorded
- SCOPE OF WORK FIRST rule added: (1) Define scope, (2) List permissions, (3) Get approval, (4) Build
- Dashboard 5-tab layout: Overview, Trade Analysis, MFE/MAE & Losers, ML Meta-Label, Validation
- Live pipeline: WebSocket bar → rolling buffer → indicators → state machine → XGBoost → bet sizing → FilteredSignal

### State changes
- 10 Python files created via build_missing_files.py
- `scripts/build_staging.py` NEW (written, not yet run)
- `MEMORY.md` updated (new rule, trimmed to 184 lines)

### Open items recorded
```
python scripts/build_staging.py
python staging/test_dashboard_ml.py
streamlit run staging/dashboard.py
```
Then deploy staging to production. Next priorities: ML meta-label analysis, multi-coin portfolio optimization, 400-coin ML sweep, live TradingView validation.

### Notes
Bug fixed in walk_forward.py test — used 5,000 bars (17 days) but needed 2+ months; fixed to 100,000 bars. Streamlit ScriptRunContext spam fixed by suppressing logging in tests.

---

## 2026-02-11-recent-chats-log.md
**Date:** 2026-02-11
**Type:** Session log (chat summary compilation)

### What happened
Comprehensive log of 38 chats from Jan 27 – Feb 11, 2026. Generated via chat review. Key entries: AVWAP/BE race condition bug identified (be_raised prevents BE from triggering when AVWAP already moved SL past BE level); v3.8.2 cooperative BE+AVWAP design spec created; filesystem tool bug confirmed (files report created successfully but don't actually write); v3.8 catastrophic results analyzed (-97% performance from 621 consecutive losing trades); master build script bug (Phase 1 silently failed with exit code 1 but script continued); Ollama + LM Studio setup, Qwen LLM integration; position sizing mismatch in v3.8.2 ($10K/trade vs $2,500/trade across 4 pyramid slots); full project 75% complete assessment; Week 2 milestone document created; AVWAP disables breakeven identified as root cause of v3.8 failure (position.py line 145).

### Decisions recorded
- Rename `be_raised` → `be_checked` to allow cooperative BE+AVWAP logic
- Switch from LM Studio (context errors with Qwen3-Coder-30B) to Ollama (qwen2.5-coder:14b)
- February stats noted: 4,187 trades, $41.87M volume, -$348 trading loss + $5,862 rebates = $5,514 net profit

### State changes
- This is a compiled summary log, not a direct build session record
- Referenced files: v3.8.2 BUILD spec, dashboard fixes, GitHub bug report (all failed to save due to tool bug)

### Open items recorded
- PyTorch installation (critical blocker at time of writing)
- Filesystem tool bug (all chat file writes failing)
- v3.8.2 leverage verification

### Notes
Filesystem tool bug confirmed on Feb 11 — multiple sessions where Claude reported files "created successfully" but nothing was actually written. This explains gaps in file coverage from that period.

---

## 2026-02-12-build-journal.md
**Date:** 2026-02-12
**Type:** Build session

### What happened
Four sessions. Session 1: Fixed Bybit fetcher rate limit handling (returns tuple `(candles, rate_limited)` with exponential backoff 10s-160s up to 5 attempts); improved download speed 20x (`RATE_LIMIT=0.05s` = 20 req/s, 1s between symbols); built `scripts/sanity_check_cache.py` (COMPLETE/PARTIAL/NEW_LISTING categories, writes `_retry_symbols.txt`); added `--retry` flag to downloader; data collection declared complete (399 coins, 124.8M bars, ~6.2 GB, zero quality issues); pushed 148 Python + 28 Pine Script files to GitHub (`S23Web3/ni9htw4lker`, main branch); moved memory files from `.claude/projects/` to vault root. Session 2: Dashboard overhaul — data normalizer (`data/normalizer.py`, ~370 lines, auto-detect delimiter/columns/timestamps/interval, 6 exchange formats, resample), CLI utility (`scripts/convert_csv.py`), dashboard mode navigation (session_state mode machine: settings|single|sweep|sweep_detail), sweep persistence (CSV with params_hash, auto-resume, 1 coin per st.rerun()), sweep coin list upload, LSG bars metric. Session 3: Bug fixes and test validation (84/84 tests pass). Session 4: Scoped P1-P5 — staging deploy has conflict (stale), P2 (ML D+R grades) ready, P3 (multi-coin portfolio) trivial, P4 (400-coin ML sweep) large, P5 (TV validation) blocked on manual data.

### Decisions recorded
- Bybit rate: 0.05s (20 req/s), 1s between symbols
- Sweep is non-blocking: 1 coin per st.rerun() cycle
- Auto-resume from CSV: no manual resume button
- 5-tab detail view is universal (same for single coin and sweep drill-down)
- Normalizer output matches fetcher.py exactly (same parquet schema + .meta format)
- Build order: P2 > P3 > P4 > P1(live_pipeline only) > P5

### State changes
- `data/fetcher.py` — rate limit retry logic
- `scripts/download_1year_gap_FIXED.py` — 0.05s rate, --retry mode
- `.gitignore` — added data/historical/, *.meta, nul
- `scripts/sanity_check_cache.py` NEW
- `data/normalizer.py` NEW (~370 lines, then 542 after bug fixes)
- `scripts/convert_csv.py` NEW (~150 lines)
- `scripts/test_normalizer.py` NEW — 47/47 pass
- `scripts/test_sweep.py` NEW — 37/37 pass
- `scripts/dashboard.py` EDITED — ~1450 lines (was 1129)
- MEMORY.md — 70% chat limit rule added, Git Setup section added, Pending Builds P1-P5 added
- GitHub: 148 Python + 28 Pine Script files committed

### Open items recorded
- Run build_staging.py and validate
- Deploy staging to production
- Run ML analysis on RIVERUSDT
- Run sweep_all_coins_ml.py across all coins

### Notes
Data collection milestone: 169 coins with full 1-year history, 230 newer listing coins with all available Bybit data. Git initialized in backtester dir (Desktop/ni9htw4lker was empty clone).

---

## 2026-02-12-memory-test.md
**Date:** 2026-02-12
**Type:** Other (test file)

### What happened
Claude created a test file to verify Obsidian vault write access. Records that 15 memory entries were written with no compaction applied.

### Decisions recorded
None.

### State changes
Test file created in 06-CLAUDE-LOGS.

### Open items recorded
None.

### Notes
Minimal content — only purpose was filesystem access verification.

---

## 2026-02-12-test-file.md
**Date:** 2026-02-12
**Type:** Other (test file)

### What happened
Filesystem access test — Claude created this file to verify it could write to the Obsidian vault.

### Decisions recorded
None.

### State changes
File created successfully, confirming vault write access.

### Open items recorded
None.

### Notes
Companion to 2026-02-12-memory-test.md. Both are infrastructure verification artifacts.

---

## 2026-02-13-build-journal-cc.md
**Date:** 2026-02-13
**Type:** Build session (Claude Code environment)

### What happened
Four sessions. Session 1: Built `scripts/download_periods.py` (Bybit historical downloader for 2 periods), `scripts/fetch_market_caps.py` (CoinGecko v1, superseded), `scripts/fetch_coingecko_v2.py` (5-action comprehensive CoinGecko fetcher), `ml/features_v2.py` (26 features: 14 original + 8 volume + 4 market cap), `data/period_loader.py` (multi-period concat utility), and 4 test scripts (111/111 tests passed). Real download test: 3 coins (BTC, ETH, SOL), 1.58M bars, 62.3 MB, 7.1 min. CoinGecko v2 test: 3 coins, 30 days, 10 API calls, 0 errors, 6 seconds. CoinGecko API key noted: Analyst plan, 1,000 req/min, expires 2026-03-03. Session 2: CoinGecko full run complete (792 API calls, 394/394 coins, 0 errors, 10 min); built `download_periods_v2.py` with `--all` flag and CoinGecko smart filtering; established ALL FUNCTIONS MUST HAVE DOCSTRINGS standard. Sessions 3-4 content not present in this file (separate file covers those).

### Decisions recorded
- ALL FUNCTIONS MUST HAVE DOCSTRINGS — added to BUILD WORKFLOW hard rules
- CoinGecko smart filtering: reads coin_market_history.parquet to find earliest date, skips coins not listed before period end
- 14 original + 8 volume + 4 market cap = 26 total features in features_v2.py

### State changes
- `scripts/download_periods.py` NEW (385 lines, tested)
- `scripts/fetch_market_caps.py` NEW (322 lines, tested)
- `scripts/fetch_coingecko_v2.py` NEW (811 lines, tested)
- `ml/features_v2.py` NEW (334 lines, tested)
- `data/period_loader.py` NEW (123 lines, tested)
- 4 test scripts NEW (111/111 pass)
- `scripts/download_periods_v2.py` NEW (553 lines)
- `scripts/test_download_periods_v2.py` NEW
- CoinGecko data stored in `data/coingecko/` (5 files)
- MEMORY.md — docstring standard added

### Open items recorded
```
python scripts/test_download_periods_v2.py
python scripts/download_periods_v2.py --all --yes
```
Then: Bybit 2023-2024 (~2.5 hours) and 2024-2025 (~4.5 hours) full downloads.

### Notes
CoinGecko API budget: ~792 calls needed vs 500,000 available (0.16%).

---

## 2026-02-13-build-journal-desktop.md
**Date:** 2026-02-13
**Type:** Build session (Desktop/Claude.ai environment)

### What happened
Four sessions. Session 1: Built `scripts/download_all_available.py` (399-coin data fill, backup-first safety, bidirectional fetch, restartable via progress JSON); fixed 2 bugs during build. Also built `dashboard_v2.py` via direct Edit (RULE VIOLATION — should have used build script). Dashboard fixes: 3 mixed-type DataFrame cast issues, `use_container_width=True` → `width="stretch"`, logging added (logs/dashboard.log, 5MB rotation), `safe_dataframe()` wrapper. Post-mortem written about rule violation. New rule added: DOUBLE CONFIRM SHORTCUTS. Session 2: Created `DASHBOARD-VERSIONS.md` registry; confirmed cooldown is already fully configurable (backtester, dashboard slider, grid_search). Session 3: Built `DASHBOARD-V3-BUILD-SPEC.md` (1009 lines) — 6-tab VINCE control panel architecture (Single Coin | Discovery | Optimizer | Validation | Capital & Risk | Deploy); integrated code debt fixes CD-1-5, new metrics, LSG categorization, coin characteristics, trade lifecycle logging, VINCE blind training protocol. Session 4: Spec review by Claude Code identified scope creep; split into 3 focused specs: SPEC-A (Dashboard v3, standalone), SPEC-B (Backtester v385, engine changes), SPEC-C (VINCE ML, ML architecture). Dependency chain: A → B → C.

### Decisions recorded
- Dashboard v3 ships standalone with v384 backtester (no ML dependency)
- 3-spec architecture: A (dashboard), B (backtester v385), C (VINCE ML)
- `download_all_available.py` kicks off immediately (was already running during session)
- Cooldown no change needed — already fully configurable

### State changes
- `scripts/download_all_available.py` NEW (485 lines, currently running)
- `scripts/dashboard_v2.py` EDITED (1534 lines, rule violation)
- `DASHBOARD-VERSIONS.md` NEW (vault root)
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC.md` NEW (1009 lines)
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-SUGGESTIONS.md` NEW
- `PROJECTS/four-pillars-backtester/DASHBOARD-V3-BUILD-SPEC-REVIEW.md` NEW (created by Claude Code)
- `PROJECTS/four-pillars-backtester/SPEC-A-DASHBOARD-V3.md` NEW
- `PROJECTS/four-pillars-backtester/SPEC-B-BACKTESTER-V385.md` NEW
- `PROJECTS/four-pillars-backtester/SPEC-C-VINCE-ML.md` NEW
- MEMORY.md — DOUBLE CONFIRM SHORTCUTS rule added

### Open items recorded
- Wait for Claude Code to finish SPEC-A build
- Test dashboard v3 on RIVERUSDT
- Test sweep resume behavior
- If passing: SPEC-B (backtester v385)

### Notes
Rule violation post-mortem explicitly recorded. User's analogy: "Do not cross a highway — human does it anyway, slim chance of surviving if they keep doing it." Rule now enforced with DOUBLE CONFIRM SHORTCUTS.

---

## 2026-02-13-dashboard-v3-spec-build.md
**Date:** 2026-02-13
**Type:** Session log

### What happened
Summary of the evening dashboard v3 spec build session (Session 4 in the desktop journal). Documents: 6 dashboard bugs identified from v2 live testing (buttons disappearing, freeze on nav, sweep dying on tab switch, no progress bar, sweep not backgrounding, lag on mode switch). Built DASHBOARD-V3-BUILD-SPEC.md with disk persistence pattern, state namespace isolation per tab. Integrated VINCE coin characteristics (10 OHLCV-derived features), LSG 4-category reduction strategy, trade lifecycle logging (15 fields), ML architecture decision (unified PyTorch, 3 branches). Spec review by Claude Code → split into 3 specs (A/B/C). Claude Code now building SPEC-A.

### Decisions recorded
1. Dashboard is VINCE's control panel, not a backtest viewer
2. Default sort by Calmar (risk-adjusted), not net PnL
3. One unified PyTorch model, XGBoost as auditor
4. Entry-state + lifecycle logging = VINCE's training data
5. Spec split A/B/C — dashboard ships independently
6. Training time irrelevant — overnight runs

### State changes
- Same as build-journal-desktop.md session 3-4 entries (this is a companion log)

### Open items recorded
1. Wait for Claude Code to finish SPEC-A build
2. Test dashboard v3 on RIVERUSDT
3. Test sweep resume
4. Move to SPEC-B if passing

### Notes
This log is a companion to 2026-02-13-build-journal-desktop.md — documents the same sessions from the desktop chat perspective.

---

## 2026-02-13-hello-world-test.md
**Date:** 2026-02-13
**Type:** Other (test file)

### What happened
Filesystem write test from new session. Confirms Claude Code had write access to the vault at the start of the 2026-02-13 session.

### Decisions recorded
None.

### State changes
Test file written to 06-CLAUDE-LOGS.

### Open items recorded
None.

### Notes
Infrastructure verification artifact only.

---

## 2026-02-13-journal-audit.md
**Date:** 2026-02-13
**Type:** Audit

### What happened
Comprehensive audit of all journal and log files across the project. Mapped all locations: `.claude/projects/Obsidian-Vault/memory/` (5 files), vault root (2 loose files), `07-BUILD-JOURNAL/` (15 files Feb 3-11), `06-CLAUDE-LOGS/` (30 files Jan 25-Feb 13). Gap analysis: BUILD-JOURNAL-2026-02-12.md not copied to `.claude/memory/`, entire 07-BUILD-JOURNAL folder unknown to Claude Code sessions, no Feb 13 build journal yet. Duplicates: Feb 10 journal in both `.claude/memory/` and vault root. Naming inconsistency across 3 locations. Claude Code sessions only see `.claude/memory/`; Desktop sessions write to vault root or 07-BUILD-JOURNAL. Scanned 27 session files in Obsidian-Vault project (some with 45+ subagents), 71 todo files. Recommendations: consolidate to single location, standardize naming, trim MEMORY.md (at 223 lines, exceeds 200-line truncation limit).

### Decisions recorded
None explicitly — this was a discovery/audit session. Recommendations made but not yet acted upon.

### State changes
- `06-CLAUDE-LOGS/2026-02-13-hello-world-test.md` confirmed written
- `06-CLAUDE-LOGS/2026-02-13-journal-audit.md` this file created

### Open items recorded
1. Consolidate build journals to `07-BUILD-JOURNAL/` only
2. Remove vault root duplicates (Feb 10 loose file)
3. Copy Feb 12 journal to `07-BUILD-JOURNAL/`
4. Standardize naming
5. Update MEMORY.md references
6. Trim MEMORY.md below 200 lines (at 223 at time of audit)
7. Create Feb 13 build journal

### Notes
Critical finding: MEMORY.md at 223 lines exceeds 200-line truncation limit — info past line 200 gets dropped. This means Claude Code sessions were missing critical info from the end of MEMORY.md.

---

## 2026-02-13-vault-sweep-manifest.md
**Date:** 2026-02-13
**Type:** Other (code manifest)

### What happened
Auto-generated manifest of all code files in the vault. 234 total files (232 active, 2 inactive). Covers all Pine Script indicators, Python backtester files, ML modules, scripts, optimizers, GUI files, exits, signals, and engine files. Each entry includes file path, last modification date, line count, functions list, imports, and which files import it. Effectively a static dependency graph and inventory of the codebase as of 2026-02-13.

### Decisions recorded
None — this is a generated reference document.

### State changes
This file IS the manifest — no other files changed by its creation.

### Open items recorded
None.

### Notes
File is very large (28,272 tokens). Key stats visible from manifest: backtester_v384.py at 571 lines (most recent engine version as of 2026-02-13), dashboard.py at 1,498 lines, dashboard_v2.py at 1,533 lines, fetch_coingecko_v2.py at 811 lines, build_staging.py at 1,692 lines, build_missing_files.py at 1,571 lines, master_build.py at 1,455 lines.

---

## 2026-02-14-bbw-layer1-prompt.md
**Date:** 2026-02-14
**Type:** Session log

### What happened
~2-hour session on BBW (Bollinger Band Width) Simulator architecture. Four deliverables: (1) UML diagram fixes — replaced state diagram with flowchart LR (full LSG params, color-coded zones), added VINCE feature legend (17 total: Direct 4, Derived 7, Sequence 5, Markov 1). (2) Monte Carlo added as Layer 4b: 1,000x trade order shuffle per BBW state, 95% confidence intervals on PnL/max DD/Sharpe, overfit detection (real PnL must beat 95th percentile of shuffled), ~23 min additional runtime, total pipeline ~35 min for 399 coins. (3) Ollama integration as Layer 6: 6 integration points using qwen3:8b, qwen2.5-coder:32b, qwen3-coder:30b for code review, state analysis, feature recommendations, anomaly investigation, executive summary, build log. (4) `CLAUDE-CODE-PROMPT-LAYER1.md` written — self-contained 12KB build prompt including context, mandatory reads, exact spec, 5 tricky parts, build order, review checklist. Build order: tests first → implementation → sanity on RIVERUSDT → Ollama review → log. Issues: context compaction triggered without warning, caused wasteful searching outside vault.

### Decisions recorded
- Ollama confirmed for Layer 6 (reasoning about results, not math)
- Models: qwen3:8b (fast), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep analysis)
- Monte Carlo: yes, Layer 4b, 1,000 sims, 95% CI
- Total runtime estimate: ~35 min (8 compute + 23 MC + 3 Ollama + 1 overhead)

### State changes
- `02-STRATEGY/Indicators/BBW-UML-DIAGRAMS.md` rewritten (larger state diagram, legends)
- `02-STRATEGY/Indicators/BBW-STATISTICS-RESEARCH.md` updated (Monte Carlo section, build sequence)
- `02-STRATEGY/Indicators/BBW-SIMULATOR-ARCHITECTURE.md` NEW (full architecture + Ollama Layer 6)
- `02-STRATEGY/Indicators/CLAUDE-CODE-PROMPT-LAYER1.md` NEW (Claude Code build prompt, 12KB)
- `06-CLAUDE-LOGS/2026-02-14-bbw-uml-research.md` updated (session revisions logged)
- `06-CLAUDE-LOGS/2026-02-14-bbw-layer1-prompt.md` this file

### Open items recorded
1. Open Claude Code in VS Code
2. Paste 5-file read prompt
3. Claude Code builds tests/test_bbwp.py first, then signals/bbwp.py
4. After Layer 1 passes: new prompt for Layer 2

### Notes
Context compaction rule violated — compaction triggered without warning, causing agent to search outside vault path (C:\Users\User\Documents instead of vault). Token waste from searching wrong location. This session confirms the 70% context limit rule exists to prevent exactly this problem.
