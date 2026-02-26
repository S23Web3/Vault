# BingX Bot: 24h Demo Review + Switch to 5m + Production Readiness

## Context

The BingX connector bot has been running on VST demo for ~20.5 hours (started 2026-02-25 15:12:44) on the **1-minute timeframe** with 47 coins, $50 margin, 10x leverage, Four Pillars v3.8.4 strategy. As expected on 1m, the strategy is not viable for production. User wants to:
1. Review the 24h demo results (trades, errors)
2. Switch to 5m timeframe
3. Identify all work needed to make it a proper production bot

---

## 24-Hour Demo Results Summary

| Metric | Value |
|--------|-------|
| Uptime | ~20.5 hours, still running |
| Trades opened | 105 |
| Trades closed | 105 |
| Errors / crashes | **0** |
| Exceptions | **0** |
| Daily P&L | -$354.27 |
| Blocked signals | 428 (all "Too Quiet" ATR filter) |
| Exit reasons | ~15 SL_HIT_ASSUMED, ~90 EXIT_UNKNOWN |

**Bot stability: SOLID.** Zero crashes, zero errors over 20+ hours. The infrastructure works.

**Trading performance: Expected bad on 1m.** The -$354 loss is consistent with backtester findings (1m destroys value on most coins).

---

## Critical Finding: EXIT_UNKNOWN (90% of exits)

The position monitor detects exits by checking which conditional orders (SL/TP) remain pending. When NEITHER is found, it falls back to `EXIT_UNKNOWN` with an SL price estimate. This is happening on ~90% of closes.

**Root cause hypothesis:** BingX VST demo may clean up conditional orders (attached SL/TP) immediately when the position closes, before the monitor's 60-second check interval can query them. Or the attached SL/TP JSON format isn't creating separate trackable orders on BingX's side.

**Impact:** P&L calculations use the SL price as an estimate when exit_reason is EXIT_UNKNOWN, which means the reported -$354 may not be accurate. The actual P&L could be better or worse.

**Fix required:** Query trade history (`/openApi/swap/v2/trade/allOrders` or `/user/historyOrders`) to get the actual fill price instead of guessing. This is a P0 fix.

---

## Plan: Work Items (Priority Order)

### Phase 1: Config Switch + Bug Fixes (before restarting bot)

**1.1 Switch timeframe to 5m**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
- Line 4: `timeframe: "1m"` -> `timeframe: "5m"`
- No code changes needed. System is fully timeframe-agnostic. Default in `main.py:161` is already "5m".
- Warmup: 201 bars x 5m = 16.7 hours of history fetched at startup (takes seconds via API). Signals won't fire until warmup complete (first poll cycle).

**1.2 Fix commission rate**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
- Line 186: `commission = notional * 0.001` -> `commission = notional * 0.0008`
- Currently 0.10% per side. Should be 0.08% per side per spec. Overstates losses by ~25%.

**1.3 Fix EXIT_UNKNOWN: use trade history for actual fill price**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
- In `_handle_close()`: before falling back to SL price estimate, query BingX trade history endpoint to get the actual exit fill price and reason.
- BingX API: `GET /openApi/swap/v2/trade/allOrders` with `symbol` param, filter by `orderId` or recent timestamp.
- This fixes both the exit_reason accuracy AND the P&L accuracy.

### Phase 2: Reliability Fixes (for production readiness)

**2.1 Daily reset on startup**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
- Currently resets only at 17:00 UTC. If bot restarts after midnight but before 17:00, yesterday's daily_pnl carries over.
- Fix: In `__init__()` or on first `check_daily_reset()` call, compare `state.session_start` date to today. If different, trigger reset.

**2.2 Reconnection logic with exponential backoff**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\data_fetcher.py`
- Currently: on API failure, logs warning and returns None (single attempt).
- Fix: Add retry loop (3 attempts) with exponential backoff (1s, 2s, 4s) + jitter in `_fetch_klines()`.
- Also add consecutive failure counter: if 10+ consecutive fails across all symbols, send Telegram alert.

**2.3 Post-execution order validation**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py`
- After `_safe_post()` returns, verify `order_id != "unknown"`. If unknown, don't record position in state.
- Optional: query `/openApi/swap/v2/trade/openOrders` to confirm order exists on exchange.

**2.4 Graceful shutdown**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py`
- Currently catches SIGINT but doesn't wait for in-flight operations.
- Fix: Add a `shutdown_event` (threading.Event). On SIGINT, set event, wait up to 15s for market_loop and monitor_loop to finish current cycle before exiting.

### Phase 3: Observability (recommended before live)

**3.1 Hourly metrics summary**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` (or new `metrics.py`)
- Log hourly: open position count, daily P&L so far, daily trade count, % of daily loss limit used.
- Send Telegram if daily loss exceeds 50% of limit (early warning).

**3.2 Reduce warmup to 89 bars (optional)**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py`
- Currently returns 200 for warmup. Backtester spec says 89 is minimum (Cloud 5 = 200 EMA, but signal columns are populated by bar 89).
- Keeps warmup at 200 bars for safety. Only change if 16.7h warmup window is a problem.

### Phase 4: Config Tuning (after 5m demo runs 24h+)

**4.1 Review coin list against 5m backtest data**
- The 47 coins were selected from 5m backtester sweep results, so they should perform properly on 5m.
- After 24h+ of 5m demo data, compare actual signal frequency + P&L against backtester expectations.

**4.2 Review risk parameters**
- `min_atr_ratio: 0.003` blocked 428 signals on 1m. On 5m, ATR ratios will be higher (more volatility per bar), so fewer blocks expected. Monitor and adjust if needed.
- `max_positions: 25` and `max_daily_trades: 200` — may need tuning after seeing 5m signal frequency.

---

## Files to Modify

| File | Changes |
|------|---------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | Line 4: timeframe "1m" -> "5m" |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` | Line 186: commission 0.001 -> 0.0008; add trade history query for exit price; daily reset on startup |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\data_fetcher.py` | Add retry with backoff in _fetch_klines() |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` | Validate order_id != "unknown" before recording position |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` | Graceful shutdown with threading.Event |

## Existing Code to Reuse
- `bingx_auth.py:build_signed_request()` — for new trade history API call
- `executor.py:_safe_get()` pattern — for retry logic
- `state_manager.py:get_state()` — for startup date check

## Verification

1. `python -m pytest tests/ -v` — all 67 tests must still pass after changes
2. `python -c "import py_compile; py_compile.compile('position_monitor.py', doraise=True)"` — for each modified file
3. Start bot with `python main.py` — verify logs show `timeframe: 5m`
4. Monitor first 30 minutes: confirm warmup completes, first signal fires, SL/TP attached correctly
5. After first trade closes: verify exit_reason is no longer EXIT_UNKNOWN (should be SL_HIT or TP_HIT with actual fill price)
6. Check Telegram alerts arrive with correct data
