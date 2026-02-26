# BingX Connector — Full Audit + Health + Dashboard Labeling
**Session:** 2026-02-25 | **Status:** Demo mode, 67/67 tests passing, not yet started

---

## SCOPE

Four deliverables:
1. **Full audit** — new issues beyond the 2026-02-24 fault report
2. **ccxt/bingx-python tips applied** — practical patterns only
3. **Bot health/status visibility** — status.json + heartbeat
4. **Dashboard labeling** — structured events.jsonl + enriched trades.csv + Telegram prefix

---

## AREA 1: FULL AUDIT — New Issues

The 2026-02-24 fault report covered: leverage hedge mode, buffer size, float precision in test, mock conflicts, deepcopy bug. These are NOT repeated below.

### CRITICAL

| # | File | Issue | Fix |
|---|------|-------|-----|
| C1 | `signal_engine.py` | **Plugin config never passed to constructor.** `instance = attr()` — the entire `four_pillars:` block in config.yaml is silently ignored at runtime. `allow_a`, `allow_b`, `sl_atr_mult`, `tp_atr_mult` always use hardcoded defaults. | Pass full config dict to `attr(config=full_config)`. Requires passing `full_config` into `StrategyAdapter.__init__()` from main.py. |
| C2 | `position_monitor.py` | **PnL direction wrong for SHORT positions.** `_handle_close()` computes `pnl = (sl_price - entry_price) * qty` for all closes. For LONG SL this is negative (correct). For SHORT SL this gives wrong sign. Daily loss limiter reads corrupted PnL. | `if direction == "LONG": pnl = (exit - entry) * qty` else `pnl = (entry - exit) * qty` |
| C3 | `position_monitor.py` | **All closes assumed to be SL exits.** Actual exit price is `sl_price` regardless of whether TP was hit. trades.csv shows wrong prices and wrong reasons. | Call `GET /openApi/swap/v2/trade/order` with `orderId` to get actual fill price and order type. Fall back to assumed sl_price only on API failure (label `SL_HIT_ASSUMED`). |
| C4 | `main.py` | **Daemon threads die silently.** If MarketLoop or MonitorLoop crashes, the process stays alive but no polling occurs. SIGTERM still responds normally — bot looks alive, all positions are undefended. | Wrap thread bodies in `try/except Exception`. On uncaught exception: log CRITICAL, send Telegram alert, write `status.json` with `"status": "THREAD_DEAD"`. MonitorLoop should attempt one restart after 5s sleep before giving up. |

### HIGH

| # | File | Issue | Fix |
|---|------|-------|-----|
| H1 | `executor.py` | **`fetch_step_size()` fetches all contracts on every order.** Full contracts list (~200 symbols) fetched on every `execute()` call. Adds 100–500ms latency per order, consumes rate limit budget. | Cache step sizes at startup in a class-level dict. Refresh once per hour or on unknown symbol. |
| H2 | `executor.py` | **No SL confirmation check.** If BingX rejects the SL parameter silently (order still placed), position runs live with no stop loss. | After order response, validate that stop loss was confirmed. On failure: log CRITICAL, attempt separate stop-order placement, if that fails close position at market. |
| H3 | `data_fetcher.py` | **No stale data detection.** If API fails repeatedly, old buffer used silently. Bot may fire signals on hours-old data. No visibility into this. | After each fetch cycle, compare `iloc[-2]` timestamp against `utcnow()`. If older than `poll_interval_sec * 4`, set `stale=True` flag on the symbol. Propagate to status.json. |
| H4 | `state_manager.py` | **`reconcile()` removes phantoms without writing trades.csv row.** Trade is permanently lost from history. PnL from phantom is uncounted. | In `reconcile()`, call `_append_trade()` with `exit_reason="RECONCILE_REMOVED"`, `exit_price=0.0`, `pnl_net=0.0` for each phantom removed. |
| H5 | `main.py` | **No graceful order cancellation on shutdown.** On SIGTERM, SL/TP conditional orders on BingX remain live as orphans after the bot exits. | In shutdown handler, iterate `state_manager.get_open_positions()` and call `DELETE /openApi/swap/v2/trade/allOpenOrders` for each symbol before exit. |

### MEDIUM

| # | File | Issue | Fix |
|---|------|-------|-----|
| M1 | `signal_engine.py` | **Plugin reflection fragile.** Picks first class with `get_signal` — if base class or mixin also defines it, wrong class loaded. | Add `IS_SIGNAL_PLUGIN = True` class attribute to each plugin. Engine checks `getattr(attr, "IS_SIGNAL_PLUGIN", False)` instead of `hasattr(attr, "get_signal")`. |
| M2 | `notifier.py` | **No rate limiting or retry.** Telegram allows ~1 msg/sec per chat. Three simultaneous close events will get rate-limited. Failures propagate exceptions. | Add token-bucket rate limiter (1 msg/sec). Add retry loop (3 attempts, 1s/2s/4s backoff). Catch all exceptions as WARNING — notification failure must never crash the bot. |
| M3 | `state_manager.py` | **Daily counters never reset at midnight UTC.** `daily_trades` and `daily_pnl` carry over across midnight if the bot runs continuously. Risk gate blocks all trading on the new day. | Store `last_reset_date_utc` in state. At start of each MarketLoop tick, check date and reset `daily_pnl=0.0`, `daily_trades=0`, `halt_flag=False` if date has changed. |
| M4 | `main.py` | **No startup symbol validation.** If a configured symbol is invalid on BingX, signals fire but orders fail silently. | At startup, call `fetch_step_size()` for each configured symbol. Log CRITICAL and `sys.exit(1)` if any symbol is not found in the contracts list. |
| M5 | `bingx_auth.py` | **No HTTP timeouts set.** If BingX API hangs, MarketLoop or MonitorLoop blocks indefinitely. Thread is technically alive but makes no progress. | Add `timeout=(5, 15)` (connect/read) to all `requests.get()` and `requests.post()` calls. Handle `requests.exceptions.Timeout` as WARNING. |

### LOW

| # | File | Issue | Fix |
|---|------|-------|-----|
| L1 | `data_fetcher.py` | No response shape validation. Malformed bars produce NaN values that propagate into signals. | After constructing DataFrame, validate: OHLC non-null, High >= Low, timestamps monotonically increasing, at least `buffer_bars / 2` rows. Skip tick on failure. |
| L2 | `plugins/four_pillars_v384.py` | `tp_atr_mult: null` in config — verify None guard. If arithmetic with None reaches signal generation, silent crash. | Confirm `tp_price = entry + atr * mult if mult is not None else None`. Already present in current code — mark verified. |

---

## AREA 2: ccxt/bingx-python Tips Applied

Only patterns directly applicable without architectural refactor:

### TIP-01: `fetch_order()` for actual exit price (fixes C3)
```
GET /openApi/swap/v2/trade/order?symbol={sym}&orderId={id}&timestamp=...&signature=...
```
Returns `data.order.avgPrice` (actual fill price) and `data.order.type` (`TAKE_PROFIT_MARKET` vs `STOP_MARKET`). Add `_fetch_actual_exit(order_id, symbol)` method to `position_monitor.py`.

### TIP-02: Rate limiting — token bucket (fixes M2, prevents API bans)
New file `rate_limiter.py` — shared singleton `bingx_limiter = TokenBucket(rate=8, capacity=10)`.
All `requests` calls in `bingx_auth.py` acquire one token before sending.

### TIP-03: `cancel_all_orders()` on shutdown (fixes H5)
```
DELETE /openApi/swap/v2/trade/allOpenOrders?symbol={sym}&timestamp=...&signature=...
```
Called per-symbol in shutdown handler before `sys.exit(0)`.

### TIP-04: WebSocket streaming — DEFERRED
`watch_ohlcv()` / `watch_positions()` would require async refactor of daemon threads.
Not needed at 30s polling on 5m candles. Revisit only if missed signals are observed.

---

## AREA 3: Bot Health / Status Visibility

### New File: `status_writer.py`
Thread-safe, atomic-write JSON status file. Written at end of every MarketLoop and MonitorLoop tick.

**Exact schema for `status.json`:**
```json
{
  "schema_version": 1,
  "bot_version": "1.0.0",
  "strategy": "four_pillars_v384",
  "session_id": "<uuid4>",
  "demo_mode": true,
  "status": "running",
  "started_utc": "2026-02-25T09:29:53Z",
  "last_updated_utc": "2026-02-25T10:30:05Z",
  "uptime_seconds": 3612,
  "threads": {
    "market_loop": {
      "alive": true,
      "last_tick_utc": "2026-02-25T10:30:05Z",
      "last_tick_age_seconds": 0,
      "tick_count": 721,
      "consecutive_errors": 0
    },
    "monitor_loop": {
      "alive": true,
      "last_tick_utc": "2026-02-25T10:30:02Z",
      "last_tick_age_seconds": 3,
      "tick_count": 360,
      "consecutive_errors": 0
    }
  },
  "coins": {
    "RIVER-USDT": {
      "last_bar_close_price": 0.02341,
      "last_bar_utc": "2026-02-25T10:25:00Z",
      "bar_count": 201,
      "last_signal": "NO_SIGNAL",
      "last_signal_utc": "2026-02-25T10:25:00Z",
      "stale": false
    }
  },
  "risk": {
    "open_positions": 1,
    "max_positions": 3,
    "daily_trades_count": 5,
    "max_daily_trades": 20,
    "daily_pnl_usd": -12.50,
    "daily_loss_limit_usd": 75.0,
    "daily_loss_pct_used": 16.7,
    "halt_flag": false
  },
  "positions": [
    {
      "symbol": "AXS-USDT",
      "direction": "LONG",
      "grade": "A",
      "entry_price": 5.234,
      "sl_price": 5.100,
      "tp_price": null,
      "qty": 9.51,
      "notional_usd": 49.77,
      "entry_time_utc": "2026-02-25T09:15:00Z",
      "hold_duration_seconds": 4512,
      "order_id": "1827364509182736450"
    }
  ],
  "last_error": null,
  "last_error_utc": null,
  "error_count_session": 0
}
```

**`status` field values:** `"starting"` | `"running"` | `"degraded"` | `"thread_dead"` | `"stopped"`

**Write pattern (atomic):**
```python
def _write(self):
    tmp = self._path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(self._data, f, indent=2)
    os.replace(tmp, self._path)
```

**Changes per file:**
- `main.py`: instantiate `StatusWriter(config, session_id)`, pass to both loop functions
- `data_fetcher.py`: call `status_writer.update_market_tick(symbol, bar_ts, close, signal, bar_count, stale)` at end of each tick
- `position_monitor.py`: call `status_writer.update_monitor_tick(positions, risk_snapshot)` at end of each check

### Heartbeat Log Line (in `main.py`)
Third daemon thread, 60s interval:
```
HEARTBEAT | status=running | positions=1 | daily_pnl=-12.50 | market_age=5s | monitor_age=3s | errors=0
```
A growing `market_age` > 120s without a `status=thread_dead` in status.json is the first warning sign.

---

## AREA 4: Dashboard Labeling

### 4.1 `trades.csv` — New Columns (append to existing 12, backward compat)

Add 11 columns:
```
session_id, demo_mode, strategy_version, signal_bar_utc, exit_reason_actual,
exit_price_actual, pnl_gross, commission_entry_usd, commission_exit_usd,
sl_atr_mult, tp_atr_mult
```

Full 23-column header:
```
timestamp,symbol,direction,grade,entry_price,exit_price,exit_reason,pnl_net,
quantity,notional_usd,entry_time,order_id,session_id,demo_mode,strategy_version,
signal_bar_utc,exit_reason_actual,exit_price_actual,pnl_gross,commission_entry_usd,
commission_exit_usd,sl_atr_mult,tp_atr_mult
```

`exit_reason_actual` values: `SL_HIT` | `TP_HIT` | `MANUAL` | `LIQUIDATION` | `RECONCILE_REMOVED` | `SL_HIT_ASSUMED`

### 4.2 `notifier.py` — Structured Prefix

All messages get prefix `[{MODE}|{STRATEGY}|{GRADE}|{EVENT_TYPE}]`

Examples:
```
[DEMO|FP384|A|ENTRY] AXS-USDT LONG qty=9.51 price=5.2340 SL=5.1000
[DEMO|FP384|A|EXIT_TP] AXS-USDT LONG exit=5.312 pnl=+3.65 daily=-8.85
[DEMO|FP384|-|RISK_BLOCK] AXS-USDT A_LONG BLOCKED: MAX_POSITIONS (1/1)
[DEMO|FP384|-|ERROR] MarketLoop dead — ConnectionTimeout (3rd consecutive)
[DEMO|FP384|-|DAILY_SUMMARY] trades=8 wins=5 pnl_net=+17.52 USD
```

Add `send_event(mode, strategy_short, grade, event_type, body)` method to `Notifier`.

### 4.3 New File: `events.jsonl` (append-only JSONL event stream)

New file `event_logger.py`. Rotates daily to `events_YYYY-MM-DD.jsonl`.

**Common envelope** (all event types):
```json
{
  "event_id": "uuid4",
  "ts_utc": "ISO-8601Z",
  "event_type": "ENUM",
  "session_id": "uuid4",
  "strategy": "four_pillars_v384",
  "demo_mode": true,
  "schema_version": 1
}
```

**Event types and key payload fields:**

| event_type | Key fields |
|---|---|
| `TRADE_ENTRY` | symbol, direction, grade, entry_price, sl_price, tp_price, qty, notional_usd, signal_bar_utc, order_id, sl_atr_mult, tp_atr_mult |
| `TRADE_EXIT` | symbol, direction, grade, entry_price, exit_price, exit_reason, pnl_gross, pnl_net, commission_entry_usd, commission_exit_usd, hold_duration_seconds, exit_price_source |
| `SIGNAL` | symbol, signal (e.g. `"B_LONG"`), bar_utc, close_price, atr, computed_sl_price, computed_tp_price, action (`EXECUTED`/`SKIPPED`/`WARMUP`), skip_reason |
| `HEARTBEAT` | status, uptime_seconds, open_positions, daily_pnl_usd, daily_trades_count, market_loop_age_seconds, monitor_loop_age_seconds, error_count_session |
| `ERROR` | error_type, severity, source_file, source_function, symbol (opt), message, consecutive_count |
| `RECONCILE` | symbol, action (`PHANTOM_REMOVED`), state_entry_price, state_sl_price, state_qty, exchange_position_found |
| `DAILY_SUMMARY` | date_utc, total_trades, winning_trades, losing_trades, win_rate_pct, pnl_gross_usd, pnl_net_usd, total_commission_usd, largest_win/loss, by_grade |

---

## NEW FILES

| File | Purpose |
|---|---|
| `status_writer.py` | Atomic status.json writer, thread-safe |
| `event_logger.py` | Append-only JSONL event stream, daily rotation |
| `rate_limiter.py` | Token bucket, shared singleton `bingx_limiter` |

---

## MODIFIED FILES

| File | Changes |
|---|---|
| `signal_engine.py` | Pass config to plugin; IS_SIGNAL_PLUGIN marker |
| `position_monitor.py` | fetch_order for actual exit; fix PnL sign; event_logger calls |
| `executor.py` | Step size cache; SL confirmation; cancel_all_orders on shutdown |
| `data_fetcher.py` | Stale data detection; response validation; status_writer calls |
| `state_manager.py` | trades.csv row on phantom removal; midnight daily counter reset |
| `notifier.py` | Rate limiter; retry; send_event() method |
| `main.py` | Thread watchdog; startup symbol validation; graceful shutdown; heartbeat loop; session_id |
| `bingx_auth.py` | timeout=(5,15) on all requests; rate_limiter.acquire() |

---

## IMPLEMENTATION ORDER

Execute in this sequence to avoid breaking the 67/67 test suite:

1. **C1 — signal_engine.py** (plugin config)
   Single highest-value fix. Currently silent, blocks correct strategy config.

2. **C2 + C3 — position_monitor.py** (PnL sign + actual exit price)
   Correctness fixes. Do together since both touch `_handle_close`.

3. **H1 — executor.py** (step size cache)
   Quick win, no logic change.

4. **Area 3 — status_writer.py + heartbeat** (health visibility)
   Add new module, wire into main.py, data_fetcher.py, position_monitor.py.

5. **Area 4 — event_logger.py + trades.csv labels**
   Add new module. Update state_manager._append_trade() for new columns.

6. **Area 2 — rate_limiter.py + notifier retry** (API safety)
   Add rate limiter module, update notifier and bingx_auth.

7. **C4 — main.py thread watchdog** (resilience)
   Thread death detection + Telegram alert on crash.

8. **H2–H5 + M1–M5 + Low** (remaining issues)
   Address in order of perceived risk for the demo run.

---

## VERIFICATION

After each group of changes, run:
```
python -m pytest "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\" -v
```
Must remain 67/67 throughout.

After all changes:
```
python scripts/test_connection.py
python main.py
```

Watch for in `bot.log`:
- `Leverage: RIVER-USDT LONG -> 10x` (leverage set)
- `Warmup RIVER-USDT: 201 bars` (warmup complete)
- `Signal: LONG AXS-USDT grade=A` (first signal)
- `HEARTBEAT | status=running` (health loop active)

Check `status.json` is being written and updated every tick.
Check `events.jsonl` entries appear for each HEARTBEAT and eventual TRADE_ENTRY.
