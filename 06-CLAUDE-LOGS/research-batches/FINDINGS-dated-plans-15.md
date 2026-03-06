# Research Findings — Batch 15: Dated Plans (2026-03-02 to 2026-03-05)

Generated: 2026-03-06
Files processed: 20

---

## 2026-03-02-git-push-vault-update.md
**Date:** 2026-03-02 (inferred from filename)
**Type:** Planning

### What happened
Plan to push all new and updated vault files to GitHub (`git@github.com:S23Web3/Vault.git`, branch `main`). The vault had ~170 items in `git status` (27 modified, ~143 untracked) since the initial commit `1e1c49b`. Plan identified four items needing user decision before proceeding: `*.bak.*` files (9 files, not caught by existing `*.bak` rule), `.playwright-mcp/` directory (local MCP config), `.claude/settings.local.json` (local Claude Code permissions), and `PROJECTS/yt-transcript-analyzer/output/` (608 generated files).

Recommended additions to `.gitignore`: `.playwright-mcp/`, `.claude/settings.local.json`, `*.bak.*`, `PROJECTS/yt-transcript-analyzer/output/`. Then `git add .`, commit, push.

### Decisions recorded
- Add `.playwright-mcp/` to `.gitignore` (machine-specific)
- Add `.claude/settings.local.json` to `.gitignore` (machine-specific)
- Add `*.bak.*` to `.gitignore` (backup files, not deliverables)
- Add `PROJECTS/yt-transcript-analyzer/output/` to `.gitignore` (generated output)

### State changes
Plan document only — no files modified in this plan itself. Proposed commit message: `"Vault update: bingx connector live + dashboards, vince build specs, yt analyzer v2, session logs"`.

### Open items recorded
None stated — plan is ready for execution pending user approval on flagged items.

### Notes
The actual commit with message `"Vault update: bingx connector live + dashboards, vince build specs B1-B6, yt analyzer v2, session logs"` appears in git history as `0b12d60`. A later commit `914a1b2` also references vault updates. The plan's staging categories match what went into subsequent commits.

---

## 2026-03-03-audit-fix-cuda-bingx.md
**Date:** 2026-03-03
**Type:** Build session / Audit

### What happened
Full plan for executing audit bug fixes across four files: `engine/cuda_sweep.py`, `scripts/dashboard_v394.py`, `bingx-connector/ws_listener.py`, and `bingx-connector/position_monitor.py`. Defines a single build script `build_audit_fixes.py` that patches all four files using string replacement, then runs `py_compile` + `ast.parse` on each.

Seven findings were documented from a prior audit session:

**CRITICAL #1**: Commission split error in CUDA kernel — same rate used for both taker entry (0.0008) and maker exit (0.0002). Fix: add `maker_rate=0.0002` parameter to `run_gpu_sweep()`, split into `entry_comm` and `exit_comm`.

**CRITICAL #2**: `pnl_sum` missing entry commission — only exit cost subtracted at close, making `pnl_sum` not equal to `equity - 10000`. Fix: `pnl_sum += net_pnl - entry_comm` at both exit points.

**HIGH #3**: `win_rate` displayed as raw decimal in three dashboard table locations (GPU Sweep top-20, portfolio per-coin top-5, uniform top-10). Fix: multiply by 100, rename column to `win_rate%`.

**HIGH #4**: TTP state lost on restart — REASSESSED as already fixed in `signal_engine.py` lines 113-127. No action needed.

**HIGH #5**: `WSListener` dies permanently after 3 reconnect failures with no alert. Fix: increase `MAX_RECONNECT` to 10, add exponential backoff, write `logs/ws_dead_{timestamp}.flag` after exit.

**HIGH #6**: `_place_market_close()` missing `reduceOnly` — REASSESSED as low risk in hedge mode since `positionSide` already scopes the close. Decision: add `"reduceOnly": "true"` defensively.

**HIGH #7**: `saw_green` uses `>` instead of `>=` at CUDA kernel lines 163/171. Fix: change to `>=` / `<=`.

### Decisions recorded
- CRITICAL #1 and #2: Fix commission split and pnl_sum
- HIGH #3: Format win_rate as % in three table locations
- HIGH #5: MAX_RECONNECT=10, exponential backoff, dead flag file
- HIGH #6: Add `reduceOnly` defensively
- HIGH #7: Fix saw_green comparison operators
- HIGH #4: No action (already fixed)

### State changes
Plan document only. Build script `build_audit_fixes.py` to be created at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_audit_fixes.py`.

### Open items recorded
Several items deferred as MEDIUM/LOW: stale detection for sweep param ranges, Shared Pool capital model enforcement, TTP mid-bar timing, race condition, commission rate fallback mismatch, no slippage protection, close-remaining missing counters, UI tweaks, lock gaps in BingX.

### Notes
The file `PROJECTS/four-pillars-backtester/scripts/build_audit_fixes.py` appears in git status as untracked (`??`), confirming the build script was created. The prior audit (HIGH #4 reassessment) overrides any earlier claim that TTP state restoration was broken.

---

## 2026-03-03-be-auto-ttp-trigger.md
**Date:** 2026-03-03 (inferred from context)
**Type:** Build plan

### What happened
Plan to replace the 0.16% distance-based breakeven trigger (`BE_TRIGGER = 1.0016`) with TTP activation as the sole auto-BE trigger. Three files to modify: `position_monitor.py`, `bingx-live-dashboard-v1-4.py`, `config.yaml`.

Key changes:
- Remove `BE_TRIGGER` constant and mark price API fetch from `check_breakeven()`
- New trigger: `pos_data.get("ttp_state") == "ACTIVATED"` — already in state, no extra API call
- New `be_auto` config key (default `true`) with dashboard toggle (dcc.Checklist)
- Full rewrite of `check_breakeven()` provided with exact Python code

Dashboard changes: add `ctrl-be-auto` checklist to Strategy Parameters tab, wire into CB-11 (load config) and CB-12 (save config).

### Decisions recorded
- Replace distance-based BE trigger with TTP activation trigger
- `be_auto` config key added under `position:` section
- Dashboard toggle added for user control
- Keep `_fetch_mark_price_pm()` method (may be used elsewhere)
- Keep `_place_be_sl()` and `_cancel_open_sl_orders()` unchanged

### State changes
Plan document only. Modifies `position_monitor.py`, `bingx-live-dashboard-v1-4.py`, `config.yaml`.

### Open items recorded
None stated.

### Notes
This plan changes the BE trigger logic. Earlier plan `2026-03-03-audit-fix-cuda-bingx.md` had assessed HIGH #4 (TTP state restoration) as already fixed. This plan builds on that by using ttp_state as the BE trigger.

---

## 2026-03-03-bingx-dashboard-v1-4-patch4-close-market.md
**Date:** 2026-03-03
**Type:** Build session

### What happened
Plan to run `build_dashboard_v1_4_patch4.py` which adds a "Close Market" button to the position action panel and a new CB-16 callback. Context confirms patches 1-3 were already applied to `bingx-live-dashboard-v1-4.py` (2293 lines at time of writing).

Two anchor points verified before running:
- P1: `html.Button("Move SL"` at line 1379 — verified present, unique
- P2: `# CB-8: History Grid` at line 1586 — verified present, unique

Patch 4 adds:
- P1: Red `html.Button("Close Market", id="close-market-btn")` after Move SL
- P2: CB-16 callback before CB-8 — cancels all open orders for symbol, places MARKET reduceOnly close, writes `close_pending=True` to state.json

CB-16 uses `prevent_initial_call=True` and `allow_duplicate=True` on `pos-action-status`.

### Decisions recorded
- Close Market placed as red button after Move SL
- CB-16 uses prevent_initial_call=True
- State: `close_pending=True` written on execution

### State changes
Plan for build script `build_dashboard_v1_4_patch4.py` at `PROJECTS/bingx-connector/scripts/`. Target: `bingx-live-dashboard-v1-4.py`.

### Open items recorded
Verification checklist: build output (2/2 PASS, py_compile PASS), button visible in Live Trades tab, click with no row selected fires PreventUpdate, click with row selected shows status, log shows market close lines, no new IndexError/KeyError.

### Notes
File `PROJECTS/bingx-connector/scripts/build_dashboard_v1_4_patch4.py` appears in git status as `??` (untracked), confirming it was created.

---

## 2026-03-03-cuda-dashboard-v394-spec.md
**Date:** 2026-03-03
**Type:** Build plan / Handover document

### What happened
Corrected handover spec for building CUDA GPU sweep capability and Numba JIT portfolio speedup for the Four Pillars dashboard. Explicitly marked as superseding the earlier `2026-03-03-cuda-sweep-engine.md` plan (which contained 4 pre-audit errors).

Key corrections vs earlier plan:
- Param grid shape is [N_combos, 4], NOT [N_combos, 5] (notional is scalar, not per-combo)
- TP sentinel is 999.0, NOT 0.0 (0.0 = instant exit at entry price)
- Signal arrays are 12, NOT 10 (reentry_long/short + cloud3_ok_long/short added)
- Per-thread position state uses `cuda.local.array()`, NOT Python lists
- Sharpe uses Welford's online variance (no per-trade list in GPU kernel)
- Column names: `reentry_long`/`reentry_short` confirmed (NOT `re_long`/`re_short`)
- Python wrapper must extract `cloud3_allows_long`/`cloud3_allows_short` from DataFrame (internal kernel names can differ)

Architecture: CUDA kernel for GPU sweep (2,112 combos), `jit_backtest.py` for CPU-compiled portfolio, `dashboard_v394.py` copy of v392 with GPU Sweep mode + portfolio JIT path + sidebar GPU panel.

Build script `scripts/build_cuda_engine.py` creates 3 files (NOT 4 — `sweep_all_coins_v2.py` deferred).

### Decisions recorded
- Base dashboard on v392 (not v393, even though v393 passes py_compile)
- Defer `sweep_all_coins_v2.py` to next session
- TP sentinel: 999.0 (not 0.0)
- Param grid: 4 columns [sl_mult, tp_mult, be_trigger_atr, cooldown]
- Kernel simplifications documented (no AVWAP ratcheting, no scale-outs, etc.)

### State changes
Plan document. Files to create: `engine/cuda_sweep.py`, `engine/jit_backtest.py`, `scripts/dashboard_v394.py`, `scripts/build_cuda_engine.py`.

### Open items recorded
Memory files to update after build: `TOPIC-backtester.md`, `TOPIC-dashboard.md`, `LIVE-SYSTEM-STATUS.md`, `PRODUCT-BACKLOG.md`.

### Notes
This document explicitly supersedes `2026-03-03-cuda-sweep-engine.md`. The v394 dashboard and cuda_sweep.py files appear in git status as modified (`M`), confirming this build was completed.

---

## 2026-03-03-cuda-sweep-engine.md
**Date:** 2026-03-03
**Type:** Planning (superseded)

### What happened
Original architecture plan for CUDA acceleration of the Four Pillars backtester sweep engine and dashboard v394. Documents GPU thread model (one thread per parameter combo), input arrays (10 arrays), param grid (5-column including notional), and intended build script creating 4 files.

Key specs in this version (later found to have errors):
- `re_long`/`re_short` as reentry column names (wrong — should be `reentry_long`/`reentry_short`)
- Param grid: [sl_mult, tp_mult, be_trigger, cooldown, notional] — 5 columns (wrong — notional is scalar)
- TP sentinel: 0.0 = no TP (wrong — 0.0 = instant exit at entry price)
- `cloud3_ok_long`/`cloud3_ok_short` as column names for DataFrame extraction (wrong — `cloud3_allows_long/short`)
- Dashboard "GPU Sweep" implemented as a tab (later spec changes to a mode)

Build script creates 4 files: `cuda_sweep.py`, `jit_backtest.py`, `sweep_all_coins_v2.py`, `dashboard_v394.py`.

### Decisions recorded
None — this plan was superseded by `2026-03-03-cuda-dashboard-v394-spec.md`.

### State changes
Plan document only. Superseded.

### Open items recorded
None — superseded.

### Notes
This plan is explicitly overridden by `2026-03-03-cuda-dashboard-v394-spec.md` which documents 4 errors found during audit. The corrected plan deferred `sweep_all_coins_v2.py` and fixed the column names, tp_mult sentinel, and param grid shape.

---

## 2026-03-03-cuda-v394-spec-audit.md
**Date:** 2026-03-03
**Type:** Audit

### What happened
Audit of the `2026-03-03-cuda-dashboard-v394-spec.md` handover document against actual source code. Found 3 issues (2 critical, 1 minor).

**ISSUE 1 — CRITICAL: Backtester Version Mismatch**
Spec claims dashboard uses `Backtester390`. Actual: `dashboard_v392.py` imports `Backtester384` (line 278) and `compute_signals_v383`. The v390 files exist but are not used by the active dashboard. Decision required: match v3.8.4 for result parity (Option A) vs match v3.9.0 as spec describes (Option B — results won't match CPU sweep).

**ISSUE 2 — CRITICAL: Column Name Inconsistency**
Spec uses `cloud3_ok_long/short` for kernel variable names but actual DataFrame columns are `cloud3_allows_long/short`. Python wrapper must use `cloud3_allows_long/short` when extracting from DataFrame.

**ISSUE 3 — MINOR: v393 IndentationError Claim**
Spec says v393 has an IndentationError. Actual: v393 (127KB) passes py_compile. Low impact since plan already uses v392 as base.

Verified facts: mode chain is correct, reentry columns are `reentry_long/reentry_short`, position slots are 4, direction conflict gate is correct, portfolio is sequential, `compute_params_hash()` exists (MD5-based), all target files don't exist yet.

### Decisions recorded
None explicitly in this document — it raises the critical question: which engine version should the CUDA kernel replicate (v3.8.4 for parity vs v3.9.0 as spec describes)?

### State changes
Audit document only. No code changed.

### Open items recorded
Decision needed: which engine version for CUDA kernel — v3.8.4 or v3.9.0?

### Notes
This audit was produced before the corrected spec (`2026-03-03-cuda-dashboard-v394-spec.md`). The corrected spec uses v390 as the reference. This implies the decision was to use v390 (Option B) and accept some divergence from the v392 CPU sweep results.

---

## 2026-03-03-daily-bybit-updater.md
**Date:** 2026-03-03
**Type:** Build plan

### What happened
Plan for a daily incremental Bybit data updater script. Context: backtester data cache (399 coins, `data/cache/`) is stale — last updated 2026-02-13. New standalone script (not patching `fetch_data.py`) that discovers symbols, fetches only new candles since last cached timestamp, resamples to 5m, and logs results.

Four CLI modes: default (update all), `--months N`, `--skip-new`, `--skip-resample`, `--max-new N`, `--dry-run`.

Design decisions:
- Standalone script (not a patch of existing fetcher)
- Reuses `BybitFetcher` from `data/fetcher.py` for fetch logic
- Reuses `TimeframeResampler` from `resample_timeframes.py` for 5m resampling
- Incremental append logic lives in `daily_update.py` itself (not patched into fetcher)
- Rate limiting: 0.12s between requests
- 3 retries with exponential backoff

### Decisions recorded
- New standalone script, not a patch of `fetch_data.py`
- Reuse existing modules (BybitFetcher, TimeframeResampler)
- Incremental logic in the new script only

### State changes
Plan document. Creates: `scripts/build_daily_updater.py` (build script), `scripts/daily_update.py` (created by build). Both appear as `??` in git status, confirming creation.

### Open items recorded
User runs `--dry-run` first, then `--max-new 5` for test batch, then full run.

### Notes
The file `PROJECTS/four-pillars-backtester/scripts/build_daily_updater.py` appears in git status as `??` (untracked), confirming creation. `daily_update.py` itself is not listed — may have been created by the build script or may be named differently.

---

## 2026-03-03-dashboard-v1-4-patch3-ttp-display.md
**Date:** 2026-03-03
**Type:** Build plan

### What happened
Comprehensive plan for TTP (Trailing Take Profit) engine integration with the BingX connector and dashboard. Covers two build scripts: `build_ttp_integration.py` (connector files) and `build_dashboard_v1_4_patch3.py` (dashboard only).

Context: `ttp_engine.py` drafted by Opus with 4 bugs; BingX connector has no TTP logic; fixed ATR-TP order placed at entry currently.

Architecture — hybrid (split evaluation and execution):
- **Thread 1 (signal_engine.py)**: TTP evaluation using real 1m OHLC candles per `on_new_bar()` call
- **Thread 2 (position_monitor.py)**: TTP close execution via `check_ttp_closes()` reading `ttp_close_pending` flag

4 ttp_engine.py bug fixes:
1. `self.state` never set to CLOSED — add in `_evaluate_long`/`_evaluate_short`
4. Replace `CLOSED_PARTIAL` state with `"CLOSED"` everywhere
5. Replace `iterrows()` with `itertuples()`
6. Guard `band_width_pct` with proper None check

Files modified/created: `ttp_engine.py` (CREATE), `signal_engine.py` (MODIFY), `position_monitor.py` (MODIFY), `main.py` (MODIFY), `config.yaml` (MODIFY), `bingx-live-dashboard-v1-4.py` (MODIFY), `tests/test_ttp_engine.py` (CREATE).

Dashboard changes (Patch 3): Add TTP + Trail Lvl columns to positions grid, add TTP section to Controls tab (toggle, activation %, trail distance %), wire into CB-11/CB-12.

### Decisions recorded
- TTP evaluation in signal_engine (market loop thread), execution in position_monitor
- `ttp_close_pending` flag bridges threads via state.json
- Race guard: verify position exists on exchange before placing MARKET close
- Existing fixed TP orders still placed at entry — TTP runs alongside
- Config under `position:` section: `ttp_enabled: false`, `ttp_act: 0.005`, `ttp_dist: 0.002`
- `TTP_EXIT` exit reason in trades.csv

### State changes
Plan document. Build scripts to create. Multiple source files to be modified.

### Open items recorded
Verification: 10-step checklist including race test (SL fires first, TTP close skipped cleanly).

### Notes
This plan is labeled `cuddly-dancing-perlis.md` in its header (`**Plan file:**`), suggesting it was created from plan mode under that internal name. Confirms pre-existing bugs in executor.py and state_manager.py were agent transcription errors, not real bugs.

---

## 2026-03-03-git-cleanup-gitignore-backlog-commit.md
**Date:** 2026-03-03
**Type:** Planning

### What happened
Plan to fix VSCode "too many active changes" warning caused by untracked `.venv312/` (thousands of files), 37 `.bak*` backup files, and runtime artifacts. Two-step plan: update `.gitignore`, then commit all legitimate backlog.

New `.gitignore` patterns to append:
- `.venv/`, `.venv312/`, `.venv*/`, `venv*/`, `env/`, `.env/` (venv variants)
- `PROJECTS/bingx-connector/bot.pid`, `PROJECTS/bingx-connector/bot-status.json` (runtime state)
- `*.bak.*`, `*.bak.py`, `*.bak.css`, `*.bak.js` (build backup files)

Note: root `.gitignore` already has `**/venv/` but NOT `.venv312/` (dot prefix = different pattern).

Explicit decision: `06-CLAUDE-LOGS/plans/` directory is TRACKED in git (include in commit).

Proposed commit message: `"Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03"`.

### Decisions recorded
- `.venv312/` added to `.gitignore`
- `bot.pid` and `bot-status.json` excluded from git
- `*.bak.*` patterns added
- Plans directory tracked (not excluded)
- Commit all remaining untracked/modified files as one backlog commit

### State changes
Plan document. Target: `C:\Users\User\Documents\Obsidian Vault\.gitignore` (append 8 new lines). Git commit `914a1b2` with this exact message appears in git history, confirming execution.

### Open items recorded
None.

### Notes
Git history shows `914a1b2 Backlog commit: bingx-connector v1.4, backtester engine updates, session logs 2026-02-28 to 2026-03-03` — exact match to planned commit message, confirming this plan was executed.

---

## 2026-03-03-next-steps-roadmap.md
**Date:** 2026-03-03
**Type:** Planning / Roadmap

### What happened
Comprehensive next-steps roadmap for Four Pillars / Vince v2. Documents 5 phases with prerequisites:

**Phase 0 (blocks everything):** Strategy alignment. Run `build_strategy_analysis.py` → paste report into Claude Web → answer 6 open questions (rot_level, BBW wiring, bot v386 upgrade, trailing stop divergence, BE params, ExitManager status) → apply decisions to code.

**Phase 1 (B1 FourPillarsPlugin):** After Phase 0. Single file `strategies/four_pillars.py` (rewrite). Spec conflict resolved: use v386 (not v383_v2 as BUILD-VINCE-B1-PLUGIN.md states — that spec is outdated). Build script `scripts/build_b1_plugin.py` with 3 smoke tests.

**Phase 2 (B3 Enricher):** After B1. `vince/enricher.py` — per-trade indicator snapshot at entry/MFE/exit bars, diskcache.

**Phase 3 (B4 PnL Reversal Panel):** After B3. Dash page `vince/pages/pnl_reversal.py` — LSG analysis, MFE histogram, TP sweep.

**Phase 4 (B5 Query Engine):** After B3. `vince/query_engine.py` — constellation filter + permutation test.

**Phase 5 (B6 Dash Shell):** After B1-B5. `vince/app.py` + `vince/layout.py` — Dash skill mandatory.

### Decisions recorded
- Phase 0 blocks all other phases
- Use v386 signal file in B1 (overrides B1-PLUGIN.md spec)
- Engine: Backtester385 in B1
- B2 already built (API layer)
- Dash skill mandatory before B6

### State changes
Roadmap document only. No code changed.

### Open items recorded
6 open questions for Claude Web discussion (rot_level, BBW, bot upgrade, trailing divergence, BE params, ExitManager).

### Notes
Documents that B2 (API layer) is already complete. Confirms B1 spec conflict — `BUILD-VINCE-B1-PLUGIN.md` references `compute_signals_v383` but the correct import is v386.

---

## 2026-03-03-ttp-engine-activation-fix.md
**Date:** 2026-03-03
**Type:** Bug fix plan

### What happened
Fix plan for a TTP engine bug: 5 of 6 unit tests fail because the engine jumps from MONITORING → CLOSED on the activation candle, skipping the ACTIVATED state entirely.

Root cause: `evaluate()` calls `_try_activate()` which sets trail level, then falls through to `_evaluate_long`/`_evaluate_short` which immediately checks H/L against the trail — the activation candle's range naturally violates the trail level just set.

Example trace (SHORT):
- Entry=100, ACT=0.5%, DIST=0.2%
- `activation_price = 99.5`, candle H=99.8, L=99.5
- Trail set at 99.5 × 1.002 = 99.699
- `_evaluate_short`: H=99.8 >= trail=99.699 → CLOSED (wrong)

Fix — three changes to `ttp_engine.py`:
1. Restructure `evaluate()`: after activation, do NOT fall through to `_evaluate_long/short`. Instead call `_update_extreme_on_activation()` and return ACTIVATED result immediately.
2. Add `_update_extreme_on_activation()` method: extends extreme/trail if candle overshoots activation price (without checking trail stop).
3. Add `_trail_pct()` and `_extreme_pct()` helper methods.

### Decisions recorded
- Activation candle establishes baseline — trail stop checking starts on NEXT candle
- Activation candle CAN extend extreme beyond activation_price if the candle range goes further

### State changes
Plan document. Single file modified: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\ttp_engine.py`.

### Open items recorded
Run: `python -m pytest tests/test_ttp_engine.py -v` — all 6 tests should pass after fix.

### Notes
None.

---

## 2026-03-04-1m-ema-delta-scalp-concept.md
**Date:** 2026-03-04
**Type:** Strategy spec / Concept

### What happened
Concept note for a 1-minute EMA-Delta Scalp trade type — one of 4 identified trade types. Not yet validated with chart examples.

Core idea: measure the delta (distance) between two EMAs (e.g., EMA55 - EMA89) as a leading indicator for crossover prediction. Delta narrows before a crossover → pre-alert signal before actual cross.

Three entry conditions:
1. EMA Delta Threshold: `abs(EMA_short - EMA_long)` narrows below threshold (leading)
2. Stochastic Zone Entry: all 4 stochastics (9/14/40/60) in oversold (<20) or overbought (>80)
3. TDI MA Cross: TDI price line crosses its moving average (RSI=9, Smooth=5, Signal=10, BB=34)

All three conditions must be true simultaneously.

Parameters for Vince to optimize: EMA pair (55/89 default, also 34/50, 72/89), delta threshold (absolute, ATR-normalized, or %-of-price), stoch zone depth (20/80 strict vs 25/75 loose), TDI MA threshold, N stochs required, timeframe.

Normalization recommendation: ATR-normalized delta (delta / ATR) — scale-invariant, adapts to volatility.

Management concept: delta expanding after entry = hold; delta compressing back = tighten trail/exit.

### Decisions recorded
None — concept only, not validated.

### State changes
Concept document only. No code.

### Open items recorded
Requires: chart walkthrough, delta threshold research, management rules confirmation, HTF interaction rules, stoch zone rules for 1m.

### Notes
Explicitly marked "NOT a build spec" and "NOT validated." No code to be written until concept validated with real trade examples.

---

## 2026-03-04-bingx-v1-5-full-audit-upgrade.md
**Date:** 2026-03-04
**Type:** Build plan

### What happened
Comprehensive 4-phase upgrade plan for BingX connector after 12+ hours of live operation revealed multiple bugs. Context: TTP close orders failing (error 109400), Close Market button broken (100001 signature error), equity curve showing all sessions mixed, coin summary date filter disconnected.

**Phase 1 — Diagnostic Scripts (read-only):**
Build script: `build_phase1_diagnostics.py`. Creates 4 scripts:
- `run_error_audit.py` — parse bot log, categorize errors, output markdown table
- `run_variable_web.py` — AST analysis, trace data flow, flag orphaned/dead variables
- `run_ttp_audit.py` — read trades.csv for ttp_state column (expected ABSENT), read state.json for TTP fields, correlate EXIT_UNKNOWN vs TTP fail count
- `run_ticker_collector.py` — public BingX API ticker data, rank 47 config coins by liquidity

**Phase 2 — Bot Core Fixes:**
Build script: `build_phase2_bot_fixes.py`. STOP BOT BEFORE RUNNING.
- P2-A: Remove `"reduceOnly": "true"` from `_place_market_close()` (BUG-1: 109400 error — `positionSide` already scopes in Hedge mode)
- P2-B: Add TTP + BE columns to `_append_trade()` in `state_manager.py` (BUG-9: 6 new CSV columns)
- P2-C: Dynamic SL tightening after TTP activation — new `_tighten_sl_after_ttp()` method; 0.3% sl_trail_pct_post_ttp default; rate-limited (only updates when ≥0.1% improvement)

**Phase 3 — Dashboard v1.5:**
Build script: `build_dashboard_v1_5.py`. Reads v1-4 as base, writes v1-5.
- P3-A: Fix BUG-4 — add `recvWindow='10000'` to `_sign()` (100001 signature error)
- P3-B: Fix BUG-1b — remove `reduceOnly` from CB-6, CB-7, CB-16
- P3-C: Fix BUG-2 — analytics period quick-filter (`session|today|7d|all`), session equity curve
- P3-D: Fix BUG-5 — coin summary date sync with analytics date range
- P3-E: Status bar — separate BOT: LIVE/OFFLINE and EXCHANGE: CONNECTED/ERROR indicators
- P3-F: TTP Stats panel (if TTP columns present in trades.csv)
- P3-G: Trade chart popup (HIGH PRIORITY) — history grid row click → modal with candlestick + stochastics + BBW; klines fetched live from BingX

**Phase 4 — Beta Bot ($5 margin, 20x leverage):**
Build script: `build_phase4_beta_bot.py`. Requires user to confirm beta coin list first.
- New `config_beta.yaml` (leverage=20, margin_usd=5, beta coin list)
- New `main_beta.py` (all data paths prefixed with `beta/`)
- 13 user-specified coins; additional coins from ticker collector research

### Decisions recorded
- `reduceOnly` removal is the correct fix for 109400 in Hedge mode
- Dynamic SL tightening after TTP activation included in Phase 2
- Trade chart popup is HIGH PRIORITY in v1.5
- Beta bot uses separate config and data paths (no overlap with live)
- Phase 4 risk: HIGH — 20x leverage, ~5% adverse move to liquidation

### State changes
Plan document. Multiple build scripts and files to be created across all 4 phases. All relevant build scripts (`build_phase1_diagnostics.py` through `build_phase4_beta_bot.py`) appear in git status as `??`, confirming creation.

### Open items recorded
- USER ACTION REQUIRED: confirm beta coin list before Phase 4 build
- LSG `saw_green` backfill deferred (separate script)
- BUG-8 BE verification deferred
- Trade chart for open positions deferred (history grid only)

### Notes
This plan supersedes and expands on the earlier `2026-03-03-audit-fix-cuda-bingx.md` fix for HIGH #6 (`reduceOnly`). BUG-1 (109400) here is the same as HIGH #6 there. The earlier plan added `reduceOnly` defensively; this plan removes it entirely as the correct fix for Hedge mode.

---

## 2026-03-04-position-management-study.md
**Date:** 2026-03-04
**Type:** Strategy spec / Research

### What happened
Position management study document based on two live trade walkthroughs: PUMPUSDT LONG (5m, Bybit Spot) and PIPPINUSDT SHORT (5m, Bybit Perpetual). Both are trend-hold trade type only.

Documents 6 phases of position management:
1. **HTF Direction**: Three-layer system (4h/1h session bias → 15m MTF Clouds on 5m → 5m entry timing)
2. **Entry Detection**: All 4 stochastics K/D cross (sequential: 9 first, then 14/40/60), BBW spectrum above MA, TDI correct side of MA, SL=2×ATR validated against structure
3. **Gate Check**: Stoch 60 K vs D — determines trade type (trend-hold vs quick rotation)
4. **Trend Hold Management**: TDI 2-candle rule (HARD EXIT), BBW health monitor (trail/tighten/exit), breakeven trigger, AVWAP trail mechanism, Ripster Cloud milestones, TP framework
5. **Add-Ons**: Stoch 9/14 must reach opposite zone while 40/60 hold trend direction
6. **Exit**: 5 confirmed exit triggers

Key resolved questions: HTF-1 (cloud stack transitions determine session bias), HTF-2 (15m MTF = hold duration modulator, not hard binary), ENTRY-1 (sequential confirmation), ENTRY-2 (recent zone check: K below 20/above 80 within last N=10 bars), BBW-1 (flagged for Vince research), TDI-1 (RSI=9, Smooth=5, Signal=10, BB=34).

ATR clarification: ATR does NOT drive trade decisions. It is a thermometer (SL sizing + volatility confirmation only). This contradicts ATR-SL-MOVEMENT-BUILD-GUIDANCE.md which makes ATR central to phase transitions.

### Decisions recorded
- Sequential stochastic confirmation (9 crosses first, enter on last stoch completing K/D cross)
- Recent zone check: K must have been below 20 (long) or above 80 (short) within last 10 bars (flag for Vince optimization)
- 15m MTF clouds = hold duration modulator, not hard binary filter
- TDI 2-candle rule: HARD EXIT, binary
- BBW spectrum above MA = hold; crossing MA = tighten; below MA / dark blue = exit
- AVWAP trail: plain AVWAP (PUMP long) or AVWAP +2sigma (PIPPIN short), tighten to +1sigma when BBW red
- Ripster Cloud milestones are waypoints, not SL triggers; Cloud 4 value at confirmation = FROZEN TP target
- This is a different strategy architecture from v386, not a patch

### State changes
Research/study document only. No code.

### Open items recorded
6 open questions: SL-1 (what if 2 ATR doesn't align with structure?), SL-2 (what counts as "structure"?), GATE-1 (numeric threshold for stoch 60 K/D distance?), BE-1 (are two BE methods interchangeable?), TRAIL-1 (which AVWAP variant to use?), CLOUD-1 (frozen Cloud 4 target longs-only?), TP-1 (cloud target vs % target?).

### Notes
Explicitly states: "This is not a patch on v386. It is a different strategy architecture." ATR role contradicts `ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0`. Document explicitly covers only trend-hold trades — 3 other trade types (quick rotations, 1m scalps, counter-trend) are separate.

---

## 2026-03-04-probability-trade-framework.md
**Date:** 2026-03-04
**Type:** Strategy spec / Concept

### What happened
Theoretical framework document for replacing hard-coded indicator thresholds with learned transition probabilities (Markov) combined with continuous probability estimates (Black-Scholes).

**Markov approaches**:
- Observable Markov Chain: 75 combined states (5 EMA delta × 5 stoch zone × 3 TDI position), 75×75 transition matrix learned from historical data
- Hidden Markov Model: latent regimes (TRENDING/CHOPPY/TRANSITIONING) inferred from observable states using hmmlearn + Baum-Welch/Viterbi

**Black-Scholes applications**:
- Application 1: P(crossover within N bars) from current EMA delta and sigma
- Application 2: P(hit TP before SL) using first-passage-time formula
- Application 3: Expected time to reach Ripster Cloud milestone levels
- Application 4: BBWP-to-BS bridge — BBWP percentile maps to sigma regime, feeding BS formulas

**Three-layer probability architecture**:
1. Hard thresholds (current system) — instant binary filter
2. Markov — "what state comes next?"
3. Black-Scholes — "what's the probability of reaching target?"

Libraries: `hmmlearn` (HMM), `scipy.stats` (BS), `numpy` (transition matrix). RTX 3060 not needed for these (CPU-bound).

### Decisions recorded
None — concept only. Not yet validated.

### State changes
Concept document only. No code.

### Open items recorded
Must benchmark probability framework against hard-threshold baseline before building. Per document: "Start with Layer 1 + Layer 2 only. Add Layer 3 (BS) only if Layer 2 alone doesn't beat baseline."

### Notes
Explicitly marked "NOT a build spec — no code to be written yet." Identifies BS assumptions violated by crypto (non-stationary, fat tails) and mitigations. BBWP-to-BS bridge is described as "the key insight."

---

## 2026-03-04-strategy-scope-why-v386-baseline.md
**Date:** 2026-03-04
**Type:** Strategy analysis / Scoping

### What happened
Complete scoping document reviewing why v386 is the correct baseline and what gaps remain. Source: review of all session logs, version history, strategy docs, and ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0.

Version journey (v3.5 through v3.8.6) — each tried to solve the core LSG problem differently:
- v3.5.1: Cloud 3 trail → bled out
- v3.6: AVWAP SL → bled out
- v3.7: Rebate farming → commission barely viable
- v3.7.1: Fixed phantom trade bug (strategy.close_all)
- v3.8: Cloud 3 filter ON + ATR BE raise → RIVER: +$18,952 (best result)
- v3.8.3: D-signal + scale-out → drag
- v3.8.4: Optional per-coin ATR TP
- v3.8.6: Stage 2 conviction filter, C disabled → ~40 trades/day → **LIVE**

What v386 has (correct): entry grades A/B/C structure, stochastic periods, cloud periods, ATR calc, Stage 2 filter.
What v386 is missing: 3-phase SL/TP system (spec exists, never built correctly), Cloud 2 hard close, Cloud 4 computed.

Why v391 failed: built from spec doc without user confirming rules match actual trading. Spec may be incomplete vs actual chart behavior.

### Decisions recorded
- v386 signal side is correct — keep as-is
- Position management has NEVER been correctly implemented in any version
- v391 build requires user rule confirmation on all phase details before next attempt
- Next build sequence: user confirms phase rules → confirm which v391 files to keep → confirm ADD signal logic → build against confirmed rules only

### State changes
Scoping document only. No code.

### Open items recorded
5 unverified spec details: Phase 1 SL anchor (candle_low/high correct?), Phase 2 amounts (SL+TP shift by 1×ATR?), Phase 3 exit (continuous trail at highest_high/lowest_low − 1×ATR?), hard close scope (any Cloud 2 flip, or only after Phase 1?), ADD midline (48/52 threshold?).

### Notes
First document to explicitly name that spec ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0 has "never been correctly implemented in any version." v391 code files exist (clouds_v391.py, four_pillars_v391.py, position_v391.py, backtester_v391.py, build_strategy_v391.py) but are labeled "rules unverified."

---

## 2026-03-04-strategy-v391-rebuild.md
**Date:** 2026-03-04
**Type:** Build plan

### What happened
Detailed build plan for v3.9.1 Four Pillars signal quality rebuild. Goal: faithful implementation of ATR-SL-MOVEMENT-BUILD-GUIDANCE.md v2.0.

Three compounding problems in v3.9.0:
1. 3-phase SL/TP movement system not implemented (position_v384 uses AVWAP center as SL trail)
2. Cloud 2 hard close missing entirely
3. Cloud 4 (EMA 72/89) not computed anywhere — Phase 3 cannot activate

**Part 1 — clouds_v391.py**: Add `ema_72`/`ema_89` (Cloud 4), cloud state booleans (`cloud2_bull/bear`, `cloud3_bull/bear`, `cloud4_bull/bear`), cross detection columns (True only on bar of cross), and `phase3_active_long/short` (Cloud 3 AND Cloud 4 in sync).

**Part 2 — four_pillars_v391.py**: Nearly identical to v390. Call `compute_clouds_v391()` instead. State machine stays at v390.

**Part 3 — position_v391.py (THE CRITICAL REBUILD)**: Replace AVWAP-trail-as-SL with 3-phase system:
- Phase 0: SL=entry±2×ATR, TP=entry±4×ATR
- Phase 1 (Cloud 2 cross in trade direction): SL anchored to candle_low/high − 1×ATR (favorable guard), TP + 1×ATR
- Phase 2 (Cloud 3 fresh cross after entry): SL + 1×ATR, TP + 1×ATR
- Phase 3 (Cloud 3 AND Cloud 4 sync): TP removed, continuous ATR trail from highest_high/lowest_low
- Hard close: Cloud 2 flips AGAINST trade — highest priority, overrides all

AVWAP correct role: ADD entry trigger + scale-out trigger only (NOT SL trail).

ADD signals: stochastic-based (stoch9 exits overbought/oversold zone while 40+60 hold trend).

**Part 4 — backtester_v391.py**: Import position_v391, pass cloud cross columns to position slot per bar, hard close checked before SL/TP, expanded `update_bar()` signature, `sl_phase` field in trade record.

Build script: `scripts/build_strategy_v391.py` — 4 files, py_compile after each.

### Decisions recorded
- State machine stays at v390 (A/B/reentry logic correct)
- AVWAP removed from SL trail role
- AVWAP kept for ADD trigger and scale-out
- Phase 1 SL: anchor to candle_low/high (not shift by ATR)
- Phase 2: both SL and TP shift by +1×ATR
- Phase 3: TP removed, continuous ATR trail

### State changes
Plan document. Files `engine/position_v391.py`, `engine/backtester_v391.py`, `signals/four_pillars_v391.py`, `signals/clouds_v391.py`, `scripts/build_strategy_v391.py` all appear in git status as `??`, confirming creation.

### Open items recorded
Verification: smoke test on one symbol, check sl_phase values > 0, check CLOUD2_CLOSE exits, check Phase 3 trail behavior, compare signal count v390 vs v391.

### Notes
The preceding scoping doc (`2026-03-04-strategy-scope-why-v386-baseline.md`) notes that user said the spec may be incomplete vs actual trading. This plan was built from the spec. The session log `2026-03-04-strategy-v391-failed-attempt.md` (listed as `??` in git status) suggests this attempt was also problematic.

---

## 2026-03-05-bingx-timestamp-sync-fix.md
**Date:** 2026-03-05
**Type:** Build plan

### What happened
Plan to fix BingX 109400 "timestamp is invalid" error. Root cause: zero server time synchronization in the codebase. Both bot (`bingx_auth.py` line 43) and dashboard (line 193) use raw `time.time() * 1000`. BingX requires timestamp within 5000ms of server clock. User reportedly lost 17% due to this — position reconciliation, SL moves, TTP closes, and balance queries all failed silently.

Solution: new `time_sync.py` module with `TimeSync` class:
- `sync()` — fetches server time, calculates offset with RTT midpoint compensation
- `now_ms()` — returns `int(time.time() * 1000) + offset`
- `start_periodic()` — daemon Timer thread, re-syncs every 30s
- `force_resync()` — immediate sync on 109400 error
- Module-level singleton factory `get_time_sync(base_url)`
- Supports live and demo base URLs

Changes to 3 files:
- `bingx_auth.py`: replace `int(time.time() * 1000)` with `synced_timestamp_ms()` — all bot API calls flow through `build_signed_request()`
- `main.py`: init singleton at startup
- `bingx-live-dashboard-v1-4.py`: init singleton at startup, replace line 193

109400 retry logic added to `position_monitor.py`, `executor.py`, and dashboard.

Build script: `scripts/build_time_sync.py` — creates `time_sync.py`, backs up 5 files, writes updated versions, py_compile each.

Failure mode: if server-time endpoint unreachable, `_offset_ms` stays 0 = same as current behavior, no regression.

### Decisions recorded
- New `time_sync.py` module (not patching existing files directly)
- Singleton pattern per base URL
- 30s periodic resync
- 109400 error → force_resync → retry once
- Backup all modified files before writing

### State changes
Plan document. `time_sync.py` and `scripts/build_time_sync.py` both appear in git status as `??`, confirming creation.

### Open items recorded
Verification: restart bot, check log for `TimeSync: offset=+Xms`, watch for 30s sync messages, confirm 109400 errors stop.

### Notes
None.

---

## 2026-03-05-bingx-v1-5-runtime-fix.md
**Date:** 2026-03-05
**Type:** Bug fix plan

### What happened
Plan to fix runtime errors found on first launch of dashboard v1.5 (built 2026-03-04). Dashboard passed `py_compile` but revealed two code errors and one API error on first run.

**Error 1**: `KeyError: "Callback function not found for output 'store-bot-status.data'."` — `dcc.Store(id='store-bot-status', data=[])` is the only store not using `storage_type='memory'`. The `data=[]` initial value conflicts with CB-S1 callback registration.

**Error 2**: `IndexError: list index out of range` in `_prepare_grouping` — likely cascading from Error 1 (Dash's flat_data array misalignment). Expected to resolve after fixing Error 1.

**Error 3**: `BingX error 100001: Signature verification failed` — Not a code bug. API credentials may be expired/wrong. User action required (verify `.env` keys).

Fix: single line change in `bingx-live-dashboard-v1-5.py` line 1141:
```
OLD: dcc.Store(id='store-bot-status', data=[]),
NEW: dcc.Store(id='store-bot-status', storage_type='memory'),
```

Build script: `scripts/build_dashboard_v1_5_patch_runtime.py` — patches in-place, py_compile validates.

### Decisions recorded
- Fix: align `store-bot-status` with all other stores (use `storage_type='memory'`, remove `data=[]`)
- Error 3 (100001) is user action — verify `.env` keys
- Separate from previously planned tasks (`be_act` settings save bug, dashboard_v395 preset)

### State changes
Plan document. Build script `scripts/build_dashboard_v1_5_patch_runtime.py` appears in git status as `??`, confirming creation.

### Open items recorded
If IndexError persists after Patch 1: inspect CB-3, CB-9, CB-10 for mismatched initial data.

### Notes
Plan notes that the v2 continuation prompt (`2026-03-05-next-chat-prompt-v2.md`) listed only the `be_act` settings save bug, but these runtime errors are new findings from first launch. Confirms py_compile passes but does not catch Dash-specific callback registration errors.
