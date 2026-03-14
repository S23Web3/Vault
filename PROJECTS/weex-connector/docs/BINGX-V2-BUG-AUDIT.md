# BingX Connector v2 — Bug Audit Report
**Date**: 2026-03-12
**Auditor**: Claude Opus 4.6
**Source**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\`
**Purpose**: Identify all connector infrastructure bugs before porting to WEEX connector. Strategy/signal logic excluded.

---

## CRITICAL (money loss or missed exits)

### W01: Race condition — double PnL accounting from WS + poll
**File**: `position_monitor.py:300-340`
**Description**: `check()` drains the WS fill queue (lines 303-316), then fetches live positions, then reads `state_positions` a SECOND time (line 337). Between line 321 and 337, a WS fill event could have already closed the position via `_handle_close_with_price()`. The polling path then sees the same key missing from `live_keys` and calls `_handle_close()` again — double PnL entry, double Telegram alert, double trades.csv row.
**Fix**: Read `state_positions` ONCE at the top. Track which keys were already processed by WS drain in a `processed_keys` set. Skip those in the polling loop.

### W02: TTP exit returns None price — caller silently uses SL as fallback
**File**: `position_monitor.py:122, 352-357`
**Description**: When `_detect_exit()` handles a TTP exit but finds no fill price, no WS price, and no trail level, it returns `(None, "TTP_EXIT")`. The caller at line 352 sees `detected_price is None` and falls back to `sl_price` with reason `"SL_HIT_ASSUMED"`, overwriting the TTP reason entirely. PnL is computed at the SL price even though the actual exit was at the TTP trail. Corrupts `trades.csv` and `daily_pnl`.
**Fix**: When TTP exit is detected, never fall back to SL. Fetch current mark price as best-effort. If that also fails, log CRITICAL and use trail_level from state (the last known value). Never overwrite the exit reason.

### W03: Shallow copy of positions — latent thread unsafety
**File**: `state_manager.py:77`
**Description**: `get_open_positions()` returns `dict(self.state["open_positions"])` — copies the outer dict but NOT the inner position dicts. Any mutation of a returned position dict writes directly into shared state without the lock. Currently no code mutates returned dicts, but this is a time bomb.
**Fix**: Use `copy.deepcopy(self.state["open_positions"])` or `json.loads(json.dumps(...))` like `get_state()` already does.

### W04: Executor 101209 retry reuses dict with stale timestamp (works by accident)
**File**: `executor.py:234-236`
**Description**: On 101209 retry, `order_params["quantity"]` is updated, then `build_signed_request` is called with the same dict. The dict still contains the OLD `timestamp` from the first attempt. This works ONLY because `build_signed_request` mutates the passed-in dict at line 43 (`params["timestamp"] = str(synced_timestamp_ms())`), overwriting the stale value. If that mutation behavior ever changes, the retry sends an expired timestamp.
**Fix**: Pass `dict(order_params)` (a copy) to the retry, same pattern used for 109400 at line 263.

---

## HIGH (incorrect data or missed operations)

### W05: `_fetch_filled_exit` doesn't filter by positionSide
**File**: `position_monitor.py:251-273`
**Description**: Iterates all filled orders for a symbol, matching by order type only. If both LONG and SHORT positions exist for the same symbol, a filled STOP from the SHORT side could be attributed to the LONG side's exit.
**Fix**: Add `if o.get("positionSide", "") != pos_data.get("direction", ""): continue` in the filter loop.

### W06: `fetch_step_size` fetches ALL contracts per trade — no caching
**File**: `executor.py:107-123`
**Description**: Every trade execution fetches the entire contracts list to find one symbol's step size. With 47 coins, this is 47 full-list fetches per signal cycle. The contracts list changes maybe once a month.
**Fix**: Cache contracts dict at startup with 1h TTL. Shared `_contracts_cache` dict + `_cache_ts` timestamp.

### W07: Commission rate naming confusion (RT rate stored as "commission_rate")
**File**: `main.py:124, position_monitor.py:365`
**Description**: `fetch_commission_rate()` returns `rate * 2` (round-trip). The variable is named `commission_rate` throughout, but it's actually the round-trip rate (0.0016), not the per-side rate (0.0008). The BE calculation at line 511 of position_monitor.py uses the same value for the price offset, which is correct — but anyone reading the code or porting it will assume per-side and double it again.
**Fix**: Rename to `commission_rate_rt` everywhere. Add comment: "Round-trip (entry + exit) taker fee."

### W08: 1-bar symbols silently never trigger signals
**File**: `data_fetcher.py:122-130`
**Description**: `_is_new_bar` returns False when `len(df) < 2`. During warmup, if a symbol returns exactly 1 bar, it never fires the callback. No warning is logged — the symbol just silently does nothing forever.
**Fix**: Log WARNING when a symbol returns < 2 bars for more than 3 consecutive fetches.

### W09: TimeSync singleton ignores base_url on subsequent calls
**File**: `time_sync.py:110-116`
**Description**: `get_time_sync(base_url=X)` creates the singleton. Subsequent calls with different `base_url` are silently ignored. If the singleton is created before `main.py` sets the URL (e.g., by an import-time side effect), it uses the wrong URL.
**Fix**: Either validate that subsequent calls match, or pass the TimeSync instance explicitly instead of using a module-level singleton.

---

## MEDIUM (reliability / data quality)

### W10: SL order sort by orderId — not guaranteed sequential
**File**: `position_monitor.py:458`
**Description**: `_cancel_open_sl_orders_except_latest` sorts by `int(o.get("orderId", 0))` to keep the "newest" SL. BingX orderIds are not guaranteed to be numerically sequential — a lower ID could be newer.
**Fix**: Sort by `updateTime` or `createTime` field from the order response.

### W11: No log cleanup — unbounded growth
**File**: `main.py:41-42`
**Description**: Uses `FileHandler` with date-based naming. Creates a new file per day, but old files are never deleted. After months, the `logs/` directory grows unbounded.
**Fix**: Add startup cleanup: delete log files older than 30 days. Or switch to `TimedRotatingFileHandler(when='midnight', backupCount=30)`.

### W12: Phantom reconcile hides losses — records $0 PnL with no Telegram alert
**File**: `state_manager.py:220-233`
**Description**: Phantom positions (in state but not on exchange) are closed with `EXIT_UNKNOWN_RECONCILE` and `pnl=0.0`. The actual loss is hidden. No Telegram notification is sent — only a log message.
**Fix**: (1) Send Telegram alert on phantom removal. (2) Try to fetch fill from allOrders before defaulting to $0. (3) If no fill found, use mark price for best-effort PnL.

### W13: Warmup fires all requests with no throttle
**File**: `data_fetcher.py:132-146`
**Description**: 47 symbols fetched back-to-back with zero delay. Can trigger rate limiting.
**Fix**: Add `time.sleep(0.1)` between warmup fetches.

### W14: `datetime.utcnow()` deprecated in Python 3.12+
**File**: `ws_listener.py:189-191`
**Description**: `datetime.utcnow()` is deprecated. Will emit warnings on Python 3.12+.
**Fix**: Replace with `datetime.now(timezone.utc)`.

### W15: WS dead flag uses relative path
**File**: `ws_listener.py:192-198`
**Description**: `Path("logs")` is relative to CWD, not the script directory. If the bot is started from a different directory, the flag file goes to the wrong place.
**Fix**: Use `Path(__file__).resolve().parent / "logs"`.

### W16: `_safe_post` contract differs from `_safe_get`
**File**: `executor.py:67-86`
**Description**: `_safe_get` returns None on non-zero API code. `_safe_post` returns the full dict regardless of code. This is intentional (callers need error codes for retry), but the inconsistent contract is a trap.
**Fix**: Rename to `_raw_post` or add docstring clearly stating the difference.

---

## LOW (code quality / maintainability)

### W17: Duplicated mark price fetch
**Files**: `executor.py:88-105`, `position_monitor.py:410-429`
**Description**: Two identical mark price fetch functions.
**Fix**: Extract to shared `api_utils.py` or add `fetch_mark_price` to auth class.

### W18: Duplicated cancel SL functions
**File**: `position_monitor.py:431-490`
**Description**: `_cancel_open_sl_orders` and `_cancel_open_sl_orders_except_latest` share 90% of code. The "except latest" variant is a superset.
**Fix**: Merge into one function with `keep_latest=True/False` parameter.

### W19: Plugin exceptions swallowed silently
**File**: `signal_engine.py:66-68`
**Description**: `except Exception as e: signal = None` — a bug in the strategy plugin produces no traceback in the log. Only `"Plugin error %s: %s"` with the exception message, not the stack trace.
**Fix**: Add `exc_info=True` to the logger.error call.

---

## Prevention Rules for WEEX Connector

1. **Single state read per check cycle** — never read state twice in the same function
2. **Deep copy all position data** returned from state manager
3. **Never fall back to SL price** for non-SL exits — fetch mark price instead
4. **Always pass dict copies** to retry calls, never reuse the original params dict
5. **Filter orders by positionSide** when attributing fills to positions
6. **Cache exchange metadata** (contracts, step sizes) with TTL
7. **Name commission variables explicitly** — `_rt` suffix for round-trip, `_per_side` for single
8. **Log warnings for stuck symbols** that never produce signals
9. **Pass singletons explicitly** — no module-level global state
10. **Sort orders by timestamp**, not by ID
11. **Send Telegram on ALL state mutations** that affect PnL (including reconcile)
12. **Throttle warmup requests** — 100ms minimum between fetches
13. **Use `datetime.now(timezone.utc)`** everywhere — never `utcnow()`
14. **Use absolute paths** for all file operations — `Path(__file__).resolve().parent`
15. **Consistent API contracts** — helper methods either always or never check error codes
16. **No duplicate utility functions** — shared helpers in `api_utils.py`
17. **Always log tracebacks** — `exc_info=True` on all `logger.error` calls for exceptions
