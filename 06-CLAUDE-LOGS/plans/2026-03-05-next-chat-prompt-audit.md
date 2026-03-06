# Audit: 2026-03-05-next-chat-prompt.md

## Context
User asked for a thoroughness review of the next-chat continuation prompt before using it in a new session. Bot is RUNNING and must NOT be restarted (48h live data collection).

---

## ERRORS FOUND

### ERROR 1: Task 1 function mismatch (will cause build failure)
**Prompt says** (line 39): "Wire require_stage2 and rot_level into sig_params dict that is passed to compute_signals()" and "compute_signals() in signals/four_pillars.py already accepts both params (lines 60-61)"

**Reality**: dashboard_v394.py imports and calls `compute_signals_v383()` from `signals/four_pillars_v383_v2.py` (line 57). That function does NOT accept `require_stage2` or `rot_level`. The non-versioned `compute_signals()` in `signals/four_pillars.py` does accept them (lines 60-61), but the dashboard doesn't use it.

**Fix**: The prompt must specify either:
- (A) Switch dashboard import from `four_pillars_v383_v2` to `four_pillars` and call `compute_signals()` instead of `compute_signals_v383()`, OR
- (B) Add `require_stage2` and `rot_level` to `compute_signals_v383()` and `FourPillarsStateMachine383`

Option A is simpler but may break the backtester/sweep pipeline if they rely on v383 behavior. Option B is safer but duplicates params across two files.

### ERROR 2: Task 2 is already 80% done
**Prompt says** (line 45): "Still pending from prior plan. Key fixes needed: [5 bugs]"

**Reality**: `bingx-live-dashboard-v1-5.py` EXISTS (133K, built 2026-03-04). Patches P3-A through P3-H already applied:
- BUG-4 (recvWindow): FIXED in v1-5 line 194
- BUG-1b (reduceOnly): FIXED by P3-B (3 callbacks patched)
- BUG-2 (analytics period): FIXED by P3-C (radio filter + equity curve)
- BUG-5 (coin summary date sync): FIXED by P3-D

**Only genuinely unfixed**: `be_act` not in dashboard settings save callback (neither v1-4 nor v1-5 has it). Task 2 should say "v1.5 BUILT — only be_act save callback missing."

---

## GAPS (missing from prompt)

### GAP 1: No bot restart constraint
The prompt doesn't warn that the bot is collecting 48h of live data and must NOT be restarted. A future chat might patch bot files and suggest restart.

**Fix**: Add explicit line: "DO NOT restart the bot or modify bot core files (main.py, position_monitor.py, signal_engine.py, state_manager.py, config.yaml). Bot needs 48h uninterrupted run for live data."

### GAP 2: Stale runtime data
Line 59 (daily PnL) and line 60 (RENDER positions) are snapshots from the writing time. Will be outdated. Should say "check current state in logs/" or be removed.

### GAP 3: Import switch not mentioned
If Task 1 switches from `compute_signals_v383()` to `compute_signals()`, the prompt needs to specify this. The GPU sweep and portfolio sweep also use `compute_signals_v390` (dashboard lines 2457, 2623) — those are unaffected, but the main backtest path (line 284) would change.

---

## VERIFIED CORRECT

| Claim | Status | Evidence |
|-------|--------|---------|
| Three-stage TTP: be_act=0.004, ttp_act=0.008, ttp_dist=0.003 | CORRECT | config.yaml lines 82-84 |
| orderId extraction fix in 3 places | CORRECT | position_monitor.py lines 431, 587, 686 |
| Unrealized PnL in Telegram summary | CORRECT | position_monitor.py lines 757-766 |
| max_positions=25 | CORRECT | config.yaml line 66 |
| 25/25 test pass on three-stage logic | CORRECT | test_three_stage_logic.py exists, 50 checks |
| compute_signals() accepts require_stage2/rot_level | CORRECT | four_pillars.py lines 60-61 |
| Key files list | CORRECT | All paths verified |
| Bot log path | CORRECT | logs/ dir under bingx-connector |

---

## RECOMMENDATION

Fix the 2 errors and 3 gaps in the prompt before using it. Estimated: 10 min of edits. The errors would cause a future chat to either build against the wrong function (Error 1) or redo already-completed work (Error 2).
