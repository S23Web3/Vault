# Batch 16 Findings: Dated Plans (2026-03-05 group)

Processed: 9 files
Date range: 2026-03-05

---

## 2026-03-05-cards-on-the-table.md
**Date:** 2026-03-05
**Type:** Strategy spec / Analysis

### What happened
A structured "cards on the table" document was created to lay out the exact gap between what the live BingX bot knows vs what the user's actual trading system requires. Written in 10 cards, each covering a specific facet of the mismatch. Purpose: no interpretation, just facts, to inform decisions about what to build next.

Key cards:
- **Card 1**: B trade = stoch 9 cross + 2 of 3 slower stochs (14/40/60) below zone + price above Cloud 3. Missing: 3rd stoch never confirmed.
- **Card 2**: A trade = all 3 stochs confirmed + Stage 2 rotation (stoch 40+60 rotated through 20, price at Cloud 3 within last 5 bars).
- **Card 3**: Bot has zero concept of HTF session bias (4h/1h cloud transitions), 15m MTF execution filter, sequential K/D crosses, BBW spectrum vs MA, TDI price vs MA, structure validation for SL placement.
- **Card 4**: PIPPIN LONG (2026-02-28 09:05:35, LONG-B, entry=0.673800, sl=0.654449) legitimately passed bot's rules. Bot saw: stoch 9 trigger, 2/3 slower stochs confirmed, price above Cloud 3, allow_b=true. Bot did NOT see: HTF perspective, 15m MTF clouds, sequential K/D alignment, BBW, TDI, or "nowhere's land" price context.
- **Card 5**: Bot runs v3.8.4 plugin (config.yaml `plugin: four_pillars_v384`). v3.8.4 Stage 2 defaults to False; config has `require_stage2: true` but possible loading bug means it may not propagate. v3.8.6 has Stage 2 ON by default.
- **Card 6**: User's "perspective" is a 3-layer system: Layer 1 = 4h/1h HTF session bias from sequential cloud flips (binary: long day or short day). Layer 2 = 15m MTF clouds modulating hold duration. Layer 3 = 5m entry timing. Bot has no Layer 1 or 2.
- **Card 7**: Cloud 3 gate (`price_pos >= 0`, i.e., price above EMA 34/50) is too crude to distinguish strong directional move from sideways drift — "nowhere's land."
- **Card 8**: Two coexisting trading modes — volume generation (B-trades, higher frequency, rebate income) and top-tier waiting (A-grade trend-hold trades, full perspective alignment).
- **Card 9**: 6 open questions still block trend-hold implementation: SL-1 (2 ATR vs structure), SL-2 (what counts as structure), GATE-1 (stoch 60 K-D threshold), BE-1 (BE method), TRAIL-1 (AVWAP variant), CLOUD-1/TP-1 (frozen Cloud 4 vs % target).
- **Card 10**: Entry-side improvements that do NOT require answering those 6 questions: (1) perspective layer (HTF direction check), (2) B-trade tightening (fix Stage 2 config bug, or upgrade to v386, or add BBW/TDI gates), (3) coin monitor pre-filter, (4) sequential K/D check.

### Decisions recorded
- The 6 open questions from the position management study block trend-hold builds.
- Entry-side improvements (perspective layer, B-trade tightening, coin monitor, sequential K/D) can proceed without resolving those 6 questions.
- PIPPIN LONG is acknowledged as a legitimate bot-rule pass, not a bug — bot's rules are incomplete.

### State changes
- Document created as a factual reference/diagnostic. No code changes.

### Open items recorded
- 6 open questions listed (SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1/TP-1)
- 4 entry-side improvements identified as buildable without resolving those questions

### Notes
- References `fizzy-humming-crab.md` as source for position management study content.
- References `PROJECTS\bingx-connector\logs\2026-02-27-bot.log` line 10667 as source of PIPPIN LONG log entry.
- The claim "v384 Stage 2 defaults to False, possible config loading bug" is stated but not verified by reading the plugin code.

---

## 2026-03-05-native-trailing-switch.md
**Date:** 2026-03-05
**Type:** Planning / Build spec

### What happened
A detailed build plan for switching the TTP (trailing take-profit) engine to use BingX's native `TRAILING_STOP_MARKET` order type instead of the custom 5m-candle-evaluated engine. The plan was triggered by the custom engine's ~6-minute worst-case delay vs exchange tick-level reaction.

Key design decisions:
- New config key `ttp_mode: native` vs `ttp_mode: engine` (default).
- Reuses existing `ttp_act=0.008` and `ttp_dist=0.003` parameters for both modes.
- 6 files modified: `config.yaml`, `executor.py`, `signal_engine.py`, `position_monitor.py`, `ws_listener.py`, `state_manager.py`.
- ~65 lines changed total.

Critical bugs identified and planned for fix:
1. `_cancel_open_sl_orders` in `position_monitor.py`: `"STOP" in "TRAILING_STOP_MARKET"` evaluates True, so breakeven raise would cancel native trailing order. Fix: add exclusion for `otype != "TRAILING_STOP_MARKET"`.
2. `_detect_exit`: When trailing fires, SL+TP remain pending, trailing gone from open orders — returns `(None, None)`. Fix: detect `trailing_order_id` missing from open orders = trailing fired.
3. `_fetch_filled_exit`: Add explicit `TRAILING_STOP_MARKET` check before generic `"STOP" in otype` check.
4. `ws_listener.py _parse_fill_event`: Add `TRAILING_STOP_MARKET` detection before `"STOP" in order_type`.

Three-stage interaction table documented: BE raise still active in native mode (safety net between +0.4% and +0.8%), TTP engine evaluation skipped (exchange handles it), SL tighten post-TTP skipped.

Edge cases covered: BE cancelling trailing (fixed), exit detection when trailing fires (fixed), native trailing rejected by exchange (logged, SL safety net remains), bot restart (trailing lives on exchange, state.json holds trailing_order_id), switchback to engine mode (zero regressions).

Delivery: build script at `PROJECTS\bingx-connector\scripts\build_native_trailing.py`, writes all 6 modified files, py_compile each.

### Decisions recorded
- Native trailing is config-toggled, not a replacement — `ttp_mode: engine` fully reverts to current behavior.
- `ttp_engine.py` is untouched; not invoked in native mode.
- `check_breakeven()` remains active in native mode as a safety net.
- Dashboard deferred.

### State changes
- Plan document created. Build script (`build_native_trailing.py`) planned.

### Open items recorded
- Verification steps: py_compile all 6 files, `test_three_stage_logic.py` passes unchanged, manual demo test with `ttp_mode: native` + `demo_mode: true`, switchback test.

### Notes
- CODE VERIFICATION: `build_native_trailing.py` EXISTS on disk at `PROJECTS\bingx-connector\scripts\build_native_trailing.py` — plan was executed.
- Previous native trailing attempt failed (activation was ATR-based/too far, callback was 2%/too wide). This plan fixes those by using percentage-based params matching working TTP config.

---

## 2026-03-05-next-chat-prompt-audit.md
**Date:** 2026-03-05
**Type:** Audit

### What happened
An audit of `2026-03-05-next-chat-prompt.md` (the original v1 prompt) before using it in a new session. Two errors and three gaps were identified.

**ERROR 1 (will cause build failure):** Prompt says `compute_signals()` in `signals/four_pillars.py` already accepts `require_stage2` and `rot_level` and directs wiring into the `sig_params` dict. Reality: `dashboard_v394.py` calls `compute_signals_v383()` from `signals/four_pillars_v383_v2.py` (line 57), which does NOT accept those params. Fix options: (A) switch dashboard import to non-versioned function, or (B) add params to v383 versions. Option B (safer, no import change).

**ERROR 2 (already done):** Task 2 in prompt listed 5 bugs still pending for v1.5 dashboard. Reality: `bingx-live-dashboard-v1-5.py` EXISTS (133K, built 2026-03-04) with patches P3-A through P3-H already applied. BUG-4 (recvWindow), BUG-1b (reduceOnly), BUG-2 (analytics period), BUG-5 (coin summary date sync) all fixed. Only truly unfixed: `be_act` not in dashboard settings save callback.

**GAP 1:** Prompt did not warn that bot is collecting 48h live data and must NOT be restarted.

**GAP 2:** Lines 59-60 (daily PnL snapshot, RENDER positions) are stale point-in-time data, not live.

**GAP 3:** If Task 1 switches imports, the GPU sweep and portfolio sweep paths must also be considered.

Verified correct: Three-stage TTP params (be_act=0.004, ttp_act=0.008, ttp_dist=0.003), orderId extraction fix in 3 places, unrealized PnL in Telegram, max_positions=25, 25/25 test pass, key file paths.

### Decisions recorded
- Fix 2 errors and 3 gaps before using the prompt in a next session.
- Task 1 fix: Add `require_stage2` and `rot_level` to the v383 pipeline (Option B), not switch imports.
- Task 2 fix: State v1.5 already built, only `be_act` save callback remaining.

### State changes
- Audit document created. No code changes.

### Open items recorded
- ~10 minutes of prompt edits needed to fix 2 errors + 3 gaps.

### Notes
- This document is the audit that led to the creation of `2026-03-05-next-chat-prompt-v2.md`.

---

## 2026-03-05-next-chat-prompt-position-study.md
**Date:** 2026-03-05
**Type:** Planning / Continuation prompt

### What happened
A continuation prompt for resuming the position management study across a new session. The study ran across 3 sessions (2026-03-04 to 2026-03-05). 7 of 13 open questions were resolved; 6 remain. Two new concept documents were also created (1m delta scalp, probability framework).

Key state captured:
- The authoritative study document is `C:\Users\User\.claude\plans\fizzy-humming-crab.md`.
- 6 remaining questions: SL-1, SL-2, GATE-1, BE-1, TRAIL-1, CLOUD-1/TP-1.
- User indicated GATE-1 on PUMP should be next.
- 7 already-confirmed items listed (HTF-1, HTF-2, ENTRY-1, ENTRY-2, BBW-1, TDI-1, and others) to prevent re-asking.
- v391 strategy files exist on disk but have WRONG trading logic — must not be tested or deployed.

Violation note included: A previous session deleted `2026-03-04-markov-trade-state-research.md` without asking, violating the NEVER OVERWRITE/DELETE FILES rule. Content was preserved in a replacement file. Logged in session log and TOPIC-critical-lessons.md.

### Decisions recorded
- This is a RESEARCH session — no code to be written.
- Update `fizzy-humming-crab.md` as questions are resolved, keep vault copy synced at `06-CLAUDE-LOGS\plans\2026-03-04-position-management-study.md`.
- When all 6 resolved, the study document becomes complete spec for trend-hold trade type.

### State changes
- Prompt document created. No code changes.

### Open items recorded
- 6 remaining position management questions to resolve (starting with GATE-1 on PUMP chart).

### Notes
- Explicitly flags prior file-deletion violation as a trust-breaking event.

---

## 2026-03-05-next-chat-prompt-v2.md
**Date:** 2026-03-05
**Type:** Planning / Continuation prompt (audited version)

### What happened
The audited v2 version of the next-chat continuation prompt, fixing the 2 errors and 3 gaps identified in `2026-03-05-next-chat-prompt-audit.md`.

Key fixes applied vs v1:
1. Added explicit bot-running constraint at top: "DO NOT modify or restart bot core files: main.py, position_monitor.py, signal_engine.py, state_manager.py, ws_listener.py, config.yaml."
2. Task 1 (dashboard v395) corrected: Explicitly states to add `require_stage2` and `rot_level` to the v383 pipeline (state_machine_v383.py and four_pillars_v383_v2.py), NOT switch imports. References where to mirror from (signals/four_pillars.py lines 60-61, signals/state_machine.py).
3. Task 2 (live dashboard v1.5) corrected: States v1.5 BUILT with patches P3-A through P3-H already applied. Only remaining issue: `be_act` not in settings save callback. Scope narrowed to one missing input field + save wire.
4. Stale snapshot data (daily PnL, RENDER positions) replaced with instruction to check current state in logs/.

Prompt references session log `2026-03-05-bingx-bot-session.md` and plan `sparkling-doodling-hare.md`.

Tasks in v2:
- **Task 1**: `dashboard_v395.py` — add `require_stage2` checkbox + `rot_level` slider + "Load v384 Live Preset" button. Patch v383 pipeline to accept these params. Build script: `build_dashboard_v395.py`.
- **Task 2**: Live dashboard v1.5 patch — add `be_act` numeric input to Strategy Parameters tab + wire into settings save callback. Build script: `build_dashboard_v1_5_patch1.py`.

### Decisions recorded
- Keep `compute_signals_v383()` import in dashboard; patch the v383 files to accept new params.
- Bot hands-off: 6 core files explicitly off-limits.
- v1.5 patch scope: be_act only, nothing else.

### State changes
- Prompt document created. No code changes yet.

### Open items recorded
- Task 1: `dashboard_v395.py` build.
- Task 2: `bingx-live-dashboard-v1-5.py` be_act patch.

### Notes
- This is the cleaned-up version of the original prompt. The v2-prompt-audit.md (separate file) confirmed this version is ready to use.

---

## 2026-03-05-next-chat-prompt.md
**Date:** 2026-03-05
**Type:** Planning / Continuation prompt (v1 — pre-audit)

### What happened
The original (v1) next-chat continuation prompt, written before the audit identified 2 errors and 3 gaps. Documents the completed work from the prior session and the next tasks.

Completed last session:
- Three-stage position management: be_act=0.004, ttp_act=0.008, ttp_dist=0.003
- orderId extraction fix in 3 places in position_monitor.py
- Unrealized PnL added to Telegram daily summary and hourly warning
- 25/25 test pass on three-stage logic
- max_positions raised to 25

Tasks (v1 — known to have errors per audit):
- **Task 1**: `dashboard_v395.py` — add `require_stage2`, `rot_level`, "Load v384 Live Preset" button; wire into `sig_params` passed to `compute_signals()`. ERROR: dashboard actually calls `compute_signals_v383()`, not `compute_signals()`.
- **Task 2**: `dashboard_v1-5.py` — listed 5 bugs to fix. ERROR: v1.5 already exists with P3-A through P3-H applied; 4 of 5 bugs already fixed.

Bot status snapshot included: Log at `2026-03-04-bot.log`, daily PnL as of 14:52 = -$1.12, RENDER-USDT LONG+SHORT still open with ttp_state=CLOSED needing manual close.

### Decisions recorded
- None explicitly. This was a prompt draft.

### State changes
- Prompt document created. Superseded by v2.

### Open items recorded
- Same as v2, but with inaccurate scope.

### Notes
- This is the ORIGINAL version. The audit file (`next-chat-prompt-audit.md`) and v2 file (`next-chat-prompt-v2.md`) supersede it.
- Bot status data (PnL -$1.12, RENDER positions) is a point-in-time snapshot from ~14:52 on 2026-03-05.

---

## 2026-03-05-research-execution-plan.md
**Date:** 2026-03-05
**Type:** Planning / Build spec

### What happened
A plan to build an automated research orchestrator script (`run_log_research.py`) to systematically read all vault logs and produce structured findings. The vault at time of writing contained ~201 session logs + ~149 plan files (~87,000 total lines) spanning Jan 2025 to March 2026.

Architecture:
- One Python script discovers all .md files in `06-CLAUDE-LOGS/` and `06-CLAUDE-LOGS/plans/`.
- Splits into sized batches (~25 files per batch for normal files; mega-files >5000 lines get dedicated batches).
- For each batch, constructs a prompt and runs `claude -p` via subprocess with flags: `--allowedTools "Read,Edit,Write,Glob,Grep"`, `--max-turns 200`, `--model sonnet`.
- Waits for completion, logs result, moves to next batch.
- Final batch (synthesis) uses Opus model.

File ordering:
1. Ordered files from RESEARCH-TASK-PROMPT.md (162 files) in exact order
2. Unlisted files found on disk
3. Dated plan files
4. Auto-generated plan files
5. Synthesis as final batch

Output files:
- `scripts/run_log_research.py` (orchestrator)
- `06-CLAUDE-LOGS/research-batches/FINDINGS-*.md` (per-batch, at runtime)
- `06-CLAUDE-LOGS/research-batches/SYNTHESIS.md` (at runtime)
- `06-CLAUDE-LOGS/RESEARCH-PROGRESS.md` (checkbox tracker)
- `06-CLAUDE-LOGS/RESEARCH-FINDINGS.md` (final merged output)
- `06-CLAUDE-LOGS/logs/YYYY-MM-DD-research-orchestrator.log` (runtime log)

Overnight execution design:
- Zero prompts via `--allowedTools` pre-approval.
- Auto-retry: 1 retry per failed batch (30-second pause).
- Resilient: each batch writes its own file; failures don't stop other batches.
- Resumable: re-run skips completed batches.
- 2-hour timeout per batch.

Estimated runtime: 4-7.5 hours for ~16 file batches + 20-40 min synthesis = ~5-8 hours unattended.

### Decisions recorded
- Sonnet model for file batches, Opus for synthesis only.
- ~25 files per batch target.
- All 162 ordered files from RESEARCH-TASK-PROMPT.md processed first in exact order.

### State changes
- Plan document created.
- Build script `run_log_research.py` planned.

### Open items recorded
- Verification steps: all checkboxes in RESEARCH-PROGRESS.md marked [x], RESEARCH-FINDINGS.md has one section per file + synthesis, synthesis answers all 8 questions from research prompt, orchestrator log shows exit code 0 for all batches.

### Notes
- CODE VERIFICATION: `run_log_research.py` EXISTS on disk at `PROJECTS\four-pillars-backtester\scripts\run_log_research.py` — plan was executed.
- This plan is what created the current research task (the batch system being used to process this very file).

---

## 2026-03-05-trade-analyzer-v2.md
**Date:** 2026-03-05
**Type:** Planning / Build spec

### What happened
A detailed build plan for `run_trade_analysis_v2.py`, an enhanced trade analyzer for the BingX bot. Context: bot had been running ~1 day (2026-03-04 17:52 to 2026-03-05 13:24+), 49 trades at $50 notional. Existing `run_trade_analysis.py` had several limitations (no column padding, sparse output, missing analysis dimensions, hardcoded date filter).

One build script: `build_trade_analyzer_v2.py` creates `run_trade_analysis_v2.py`.

CLI flags: `--from YYYY-MM-DD`, `--to YYYY-MM-DD`, `--days N`, `--no-api`.

Output formats: terminal (fixed-width padded), markdown (`logs/trade_analysis_v2_YYYY-MM-DD.md`), CSV (`logs/trade_analysis_v2_YYYY-MM-DD.csv`).

10 analysis sections:
1. Summary Stats (trades, wins, losses, WR%, net PnL, profit factor, LSG count)
2. Equity Curve (ASCII mini-chart terminal; data table markdown)
3. Symbol Leaderboard (sorted by net PnL)
4. Direction Breakdown (LONG vs SHORT: WR%, net PnL, avg MFE/MAE)
5. Grade Breakdown (A/B/C: WR%, net PnL, avg MFE, LSG%)
6. Exit Reason Breakdown (SL_HIT, TTP_EXIT, etc.)
7. Hold Time Analysis (avg, shortest, longest; winners vs losers)
8. TTP Performance (if TTP trades exist)
9. BE Raise Effectiveness (BE vs non-BE trades)
10. Per-Trade Detail Table (padded columns)

Critical hazards documented:
- **CRITICAL**: CSV schema mismatch — header has 12 columns, rows 232+ have 18 values (6 extra TTP/BE fields added without header update). Fix: use `pd.read_csv` with all 18 column names defined, letting older rows have NaN for last 6.
- **HIGH**: F-string escape trap (build script rule — never use escaped quotes in f-strings inside build scripts).
- **HIGH**: Division by zero guards for all ratio computations.
- **MEDIUM**: API failure handling (empty list for delisted symbols, 15s timeout, 0.3s rate limit).
- **MEDIUM**: Float/string parsing edge cases.
- **MEDIUM**: Hold time edge cases (`entry_time` missing on old trades).
- **LOW**: Timestamp format (ISO 8601 with Z replacement).

6 tests planned: py_compile, dry run `--no-api`, small API run `--days 1`, full run (49 trades ~2 min), empty date range, output validation checklist.

Debugging aids built into script: `--verbose` flag, error counter, progress indicator, timestamped logging, API response logging.

### Decisions recorded
- Reuse `sign_and_build()`, `fetch_klines()`, `compute_mfe_mae()`, `to_ms()` from existing `run_trade_analysis.py`.
- Commission rate: 0.0008 (0.08% taker per side).
- No files modified; only new files created.

### State changes
- Plan document created.

### Open items recorded
- Build script to be run; then 5 tests to execute.

### Notes
- CODE VERIFICATION: `build_trade_analyzer_v2.py` EXISTS at `PROJECTS\bingx-connector\scripts\build_trade_analyzer_v2.py` — plan was executed.
- CODE VERIFICATION: `run_trade_analysis_v2.py` EXISTS at `PROJECTS\bingx-connector\scripts\run_trade_analysis_v2.py` — output file also confirmed on disk.

---

## 2026-03-05-v2-prompt-audit.md
**Date:** 2026-03-05
**Type:** Audit

### What happened
A brief audit of `2026-03-05-next-chat-prompt-v2.md` (the corrected prompt) after the errors were fixed. Verdict: clean scope, ready to use.

Audit findings:
- Task 1 (dashboard v395): Two new sidebar controls + preset button + v383 pipeline patch. Mirror job from existing v386 code. Blast radius limited to backtester dashboard; bot unaffected.
- Task 2 (live dashboard v1.5 patch): One missing `be_act` input field + save callback wire. Trivial scope.
- Constraint (bot hands-off): Six files explicitly off-limits. Correct — bot uses separate v384 plugin, not the v383 pipeline being patched.
- Explicitly notes: prompt does NOT address Cards 3/6/7/10 from "cards on the table" analysis. Those are future work.

No changes requested.

### Decisions recorded
- v2 prompt is ready for next session without further changes.
- Cards 3/6/7/10 (HTF perspective, "nowhere's land", volume generation modes, entry improvements) are future work, not in scope for next session.

### State changes
- Audit document created. No code changes.

### Open items recorded
- None. Prompt is ready.

### Notes
- This is a companion to `2026-03-05-next-chat-prompt-audit.md` (which audited v1). This document audits v2 and gives the green light.
