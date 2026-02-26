# Plan — BingX Connector Full Audit + Session Log

**Date:** 2026-02-25
**Scope:** Full audit of bot against all known bug lists. Session log append.

---

## Context

User ran the bot (`main.py`) and confirmed it is working. They want a full audit to verify everything is behaving correctly against the fault report (5 bugs) and the UML bug findings (16 bugs = C01-C08, S01-S08). Total unique issues across all documents: ~17 code-relevant bugs (doc-only bugs excluded from count). Two additional bugs were fixed this session (leverage mode, buffer off-by-one). Session log at `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-25-bingx-connector-session.md` already exists — user wants audit findings appended.

---

## Audit Findings

### A. Fault Report Bugs (5 items)

| # | Bug | File | Status |
|---|-----|------|--------|
| F1 | Float precision in test (`assertEqual` → `assertAlmostEqual`) | `tests/test_executor.py` line 178 | FIXED |
| F2 | Integration test shared-module mock conflict | `tests/test_integration.py` | FIXED |
| F3 | Plugin imports `four_pillars.py` — wrong module? | `plugins/four_pillars_v384.py` line 21 | CLEARED — `four_pillars.py` confirmed produces `long_a/b/c`, `short_a/b/c` at lines 64-73 |
| F4 | warmup_bars returns 200 vs UML spec 89 | `plugins/four_pillars_v384.py` | INFORMATIONAL — safe, just slower to first signal |
| F5 | config.yaml missing `four_pillars` block | `config.yaml` | FIXED — block added with `sl_mult: 2.0`, `tp_mult: null` |

### B. UML Bug Findings (C01-C08, S01-S08)

#### Connector Bugs

| ID | Severity | Bug | Status in Code |
|----|----------|-----|---------------|
| C01 | MEDIUM | Signal vocab BUY/SELL/HOLD in Section 1 | DOC ONLY — code uses LONG/SHORT/NONE correctly |
| C02 | MEDIUM | Mark price fetch uses wrong participant (BINGX_K) | FIXED — `executor.py` calls `/openApi/swap/v2/quote/price` |
| C03 | CRITICAL | `halt_flag` missing from RiskGate D1 check | FIXED — `risk_gate.py` Check 1: `halt_flag OR daily_pnl <= -limit` |
| C04 | CRITICAL | `halt_flag` never reset — permanent silent trade block | FIXED — `position_monitor.py` `check_daily_reset()` resets at 17:00 UTC |
| C05 | HIGH | `allowed_grades` in connector config violates plugin boundary | FIXED — grades from `plugin.get_allowed_grades()`, not connector config |
| C06 | HIGH | `warmup_bars()` declared in interface, not in code | FIXED — `FourPillarsV384.warmup_bars()` returns 200 |
| C07 | HIGH | Klines endpoint marked Signed, should be Public | FIXED — `data_fetcher.py` uses v3 public endpoint, no auth |
| C08 | CRITICAL | `sl_atr_mult: 1.0` in config vs backtester default 2.0 | FIXED — `config.yaml` `sl_mult: 2.0` |

#### Strategy Bugs

| ID | Severity | Bug | Status in Code |
|----|----------|-----|---------------|
| S01 | HIGH | "Crosses below 25" — code is `< 25`, no crossover check. Cold-start risk. | OPEN — behavior unchanged. Cold-start: bot may enter Stage 1 immediately if stoch_9 < 25 at restart |
| S02 | HIGH | "Crosses back above 25" — code is `>= 25`. Same issue. | OPEN — same cold-start window as S01. Only 1-bar false signal risk. |
| S03 | CRITICAL | Grade C doc says `price_pos != 0`, code requires `== +1` (LONG) or `== -1` (SHORT) | DOC ONLY — code is correct |
| S04 | HIGH | Re-entry shown inside grading flow — it is a separate pipeline | DOC ONLY — code has independent re-entry logic |
| S05 | HIGH | ExitManager shown as initial SL/TP calc — it is bar-by-bar dynamic updater only | DOC ONLY — plugin computes SL/TP via ATR math only, ExitManager not used |
| S06 | LOW | `process_bar()` signature missing 3 params in class diagram | DOC ONLY |
| S07 | MEDIUM | `FourPillarsPlugin` class did not exist — marked as current | FIXED — `plugins/four_pillars_v384.py` exists and works |
| S08 | CRITICAL | Backtester multi-slot vs live single-slot — P&L not comparable | OPEN RISK — not blocking demo, blocks Step 3 (go live) |

### C. Session Bugs (fixed this session, 2026-02-25)

| # | Bug | Fix |
|---|-----|-----|
| SB1 | Leverage API: `side=BOTH` rejected by BingX VST Hedge mode | `main.py` — loop over `("LONG", "SHORT")` |
| SB2 | Buffer off-by-one: `ohlcv_buffer_bars: 200` → trim leaves 200 → `200 >= 201` always False → signals never fire | `config.yaml` line 5: `200` → `201` |
| SB3 | `DEFAULT_STATE` shallow copy — `open_positions` dict shared across instances, test pollution + production bug | `state_manager.py` — `copy.deepcopy(DEFAULT_STATE)` |

---

## Live Log Analysis (from user's paste)

The log from 2026-02-25 13:39 shows the bot running correctly post-fix:

| Check | Result |
|-------|--------|
| 67/67 tests passing | PASS |
| Leverage LONG + SHORT for all 3 coins | 6x HTTP 200 — PASS |
| Margin ISOLATED for all 3 coins | 3x HTTP 200 — PASS |
| Reconcile (0 positions) | PASS |
| Warmup RIVER-USDT: 201 bars | PASS (was 201, not 200 — buffer fix working) |
| Warmup GUN-USDT: 201 bars | PASS |
| Warmup AXS-USDT: 201 bars | PASS |
| Telegram startup alert | 200 OK — "Bot started: 3 coins, 0 open, DEMO" — PASS |
| MarketLoop + MonitorLoop threads | Running — PASS |
| First bar cycle (13:40:04) | `New bar: RIVER-USDT ts=1772012100000` + `No signal: RIVER-USDT` — PASS |
| Signal engine past warmup | `No signal` (not warmup block) confirms buffer fix working — PASS |

**Conclusion from log: Bot is functioning correctly at the demo level. All startup checks pass. Signal engine is active and evaluating bars (returning No signal — market conditions not met, which is expected).**

---

## Open Items Summary

### Blocking Step 1 completion (waiting, not a bug)
- First A/B signal fires on a coin
- Telegram entry alert received
- Demo position visible in BingX VST

### Not blocking demo — flag for Step 3 before go-live
1. **BUG-S08** (CRITICAL): Re-run backtest with `max_positions=1, enable_adds=False, enable_reentry=False` — live single-slot P&L will differ from reported multi-slot results. Required before real money.
2. **BUG-S01/S02** (HIGH): Cold-start false signal risk. If bot restarts mid-trend with stoch_9 already < 25, it enters Stage 1 immediately. Mitigation: add a `cold_start_bar_count` guard in plugin that discards Stage 1 entries from the first N bars after startup.

### Doc-only (no code change needed)
- C01, S03, S04, S05, S06 — all UML diagram corrections only, code is correct

---

## Plan Actions

1. **Append audit findings to session log** (`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-25-bingx-connector-session.md`) using Edit tool (append only — NEVER Write)
   - Add section: `## Full Audit Results — 2026-02-25 (Claude)`
   - Include: bug table (all 17 issues, status), live log analysis, open items for Step 3

That is the only code action required. No files need editing for correctness — the bot is working.

---

## Verification

No code change needed. Audit is a read-only review. Session log append is the only write action.
To confirm bot health: let it run and wait for `Signal: RIVER-USDT LONG A ...` or similar in the log.
