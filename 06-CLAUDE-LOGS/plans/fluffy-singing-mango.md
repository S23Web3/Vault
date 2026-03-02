# BingX Bot Improvement Plan — Post API Scrape Review

**Date**: 2026-02-27
**Context**: Scraped full BingX API v3 reference (224 endpoints, 849KB). Cross-referenced
against current bot code. Decision context: stop polishing VST demo, prepare infrastructure
for live money. Every fix here is about correctness on the LIVE API, not demo quirks.

---

## What the Scrape Revealed

The bot currently uses 6 endpoints. BingX exposes 50+ Swap-relevant endpoints. Three
discoveries directly affect live trading accuracy:

1. **Commission rate can be queried** — `GET /openApi/swap/v2/user/commissionRate` returns
   `takerCommissionRate` and `makerCommissionRate` as actual floats. Bot hardcodes 0.0012
   (0.06% × 2) in `position_monitor.py:268`. Per MEMORY.md the real rate is 0.08% → 0.0016
   RT. This means every closed trade in the bot's logs has underestimated commission by 33%.

2. **Position history gives BingX-calculated PnL** — `GET /openApi/swap/v1/trade/positionHistory`
   returns `netProfit` (after commission + funding fees, BingX's own accounting) and
   `positionCommission`. This is the ground truth. The bot re-derives PnL from entry/exit
   price manually with a hardcoded rate — two sources of error.

3. **WebSocket gives real-time order fills** — `wss://open-api-swap.bingx.com/swap-market?listenKey=X`
   pushes `ORDER_TRADE_UPDATE` with status=FILLED, `ap` (avgPrice), `rp` (realised PnL),
   `n` (fee), and `ps` (position side) the instant a fill occurs. This permanently solves
   EXIT_UNKNOWN — no polling, no race condition with BingX's order history purge.

4. **Entry price is wrong** — Bot stores `mark_price` at execution time as `entry_price`.
   The actual fill price (`avgPrice`) is returned in the POST order response under
   `data.avgPrice`. For MARKET orders at current BingX spread this can be off by 0.1-0.5%.
   Small but cumulative error in PnL accounting.

---

## Improvements Catalog

### P0 — Correctness Bugs (live trading blockers)

#### FIX-1: Commission rate hardcoded wrong
- **File**: `position_monitor.py:268`
- **Current**: `commission = notional * 0.0012`
- **Fix**: At startup, call `GET /openApi/swap/v2/user/commissionRate`, store
  `takerCommissionRate`, pass it into PositionMonitor. Use `notional * rate * 2` for RT cost.
- **Impact**: Every trade's recorded PnL is wrong by 33%. On 100 trades at $75 margin 20x
  ($1500 notional) that's $0.60/trade × 100 = $60 understated commission total.
- **Files touched**: `main.py` (startup query), `executor.py` (pass rate in), `position_monitor.py` (use rate)

#### FIX-2: Entry price = mark price, not fill price
- **File**: `executor.py:195`
- **Current**: `"entry_price": mark_price` (fetched before order, could be stale)
- **Fix**: After successful order POST, read `data.avgPrice` from response. Use that as
  `entry_price` if present and > 0, otherwise fall back to mark_price.
- **Impact**: PnL calculation uses wrong reference point. Especially matters for volatile coins.
- **Files touched**: `executor.py`

#### FIX-3: SL direction not validated before order
- **File**: `executor.py` (no validation exists)
- **Current**: SL price passed straight from signal, no sanity check
- **Fix**: Before placing order, assert: LONG → sl_price < mark_price, SHORT → sl_price > mark_price.
  If violated, log error and return None (reject trade, send Telegram alert).
- **Impact**: Prevents impossible SL orders that BingX would reject silently or fill immediately.
- **Files touched**: `executor.py`

---

### P1 — High Value (significant operational improvement)

#### IMP-1: WebSocket for real-time fill detection (kills EXIT_UNKNOWN permanently)
- **Current**: polls `/trade/allOrders` every 60s. BingX purges filled order history within
  seconds on VST (and sometimes on live). EXIT_UNKNOWN = bot doesn't know fill price or reason.
- **Fix**: Add `ws_listener.py` module using `websockets` library. At startup, call
  `POST /openApi/swap/v1/listenKey` → get listenKey. Connect to
  `wss://open-api-swap.bingx.com/swap-market?listenKey=X`. Receive `ORDER_TRADE_UPDATE`
  events with `X=FILLED`, read `ap` (avgPrice), `rp` (realised PnL), `ps` (side).
  Refresh listenKey every 55 minutes (`POST /openApi/swap/v1/listenKey/extend`).
- **Architecture**: Third daemon thread `WSThread` alongside MarketLoop + MonitorLoop.
  On fill event: write to a thread-safe queue. PositionMonitor.check() drains queue first,
  then falls back to polling only if queue is empty.
- **Impact**: EXIT_UNKNOWN drops to 0%. Fill prices are exact (from exchange). Real-time
  instead of 60s lag.
- **New endpoints**: `/openApi/swap/v1/listenKey` (POST/POST extend/DELETE), WebSocket
- **New file**: `ws_listener.py`
- **Files touched**: `main.py` (spawn thread), `position_monitor.py` (drain queue)

#### IMP-2: Position History for post-session reconciliation
- **Current**: Bot calculates PnL from price delta + hardcoded commission. Funding fees
  ignored entirely.
- **Fix**: Add `scripts/reconcile_pnl.py` standalone script (not a live bot change). After
  each session, run it to query `GET /openApi/swap/v1/trade/positionHistory` for the past
  24h. Compare `netProfit` (BingX's number) against bot's recorded PnL. Log discrepancies.
- **Impact**: Audit tool for live trading. Catches systematic commission errors, funding
  fee impact, fill price drift.
- **New endpoint**: `/openApi/swap/v1/trade/positionHistory`
- **New file**: `scripts/reconcile_pnl.py`

---

### P2 — Medium Value (robustness improvements)

#### IMP-3: Handle error 101209 (max position value exceeded)
- **Current**: If BingX rejects with 101209 (max position value, e.g. AIXBT at 20x),
  `_safe_post` logs error, notifier sends "ORDER FAILED", trade skipped. Symbol stays in
  coin list and fails every signal.
- **Fix**: In `executor.py`, detect error code 101209 in response. Retry once with
  halved quantity (10x effective instead of 20x, while keeping leverage setting). If still
  fails, add symbol to `session_blocked` set in state and skip it for the session.
- **Impact**: AIXBT, VIRTUAL and similar coins stop generating noise alerts.
- **Files touched**: `executor.py`, `state_manager.py`

#### IMP-4: Cooldown filter (known gap vs backtester)
- **Current**: No cooldown between trades on same symbol. Backtester has this configurable.
  Bot can re-enter same symbol immediately after exit. Signal engine audit noted this as
  the only genuine strategy gap.
- **Fix**: In `state_manager.py`, when closing a position, record `last_exit_time[key]`.
  In `signal_engine.py` or `risk_gate.py`, before accepting a signal, check if
  `now - last_exit_time[key] < cooldown_bars * bar_duration`. Config param: `cooldown_bars: 3`.
- **Impact**: Aligns live bot with backtester assumptions. Prevents re-entering on same
  signal setup immediately after stop.
- **Files touched**: `state_manager.py`, `risk_gate.py`, `config.yaml`

#### IMP-5: Startup commission rate fetch + log
- **Current**: Commission rate hardcoded everywhere.
- **Fix**: In `main.py` startup sequence, after leverage/margin setup, call
  `GET /openApi/swap/v2/user/commissionRate`. Log result. Raise exception if API fails
  (can't trade with unknown commission). Store in config dict passed to all components.
- **Impact**: Single source of truth. Automatic adaptation if BingX changes rate tier.
- **Files touched**: `main.py`

---

### P3 — Low Priority / Future

#### IMP-6: Batch cancel on shutdown
- **Current**: Shutdown sends SIGTERM → 15s graceful window → threads stop. Open SL/TP
  orders remain on exchange (correct — let them execute). But if user wants a clean slate
  on restart, there's no bulk cancel.
- **Fix**: Add `POST /openApi/swap/v2/trade/cancelAllOpenOrders` call in shutdown hook,
  guarded by a config flag `cancel_orders_on_shutdown: false` (off by default).
- **Impact**: Optional clean restart capability.

#### IMP-7: Cancel All After safety timer
- **Current**: No kill switch if bot crashes mid-session.
- **Fix**: On bot start, activate `POST /openApi/swap/v2/trade/cancelAllAfter` with
  type=ACTIVATE, timeOut=120s. Renew every 90s from the market loop heartbeat. If bot
  crashes, orders auto-cancel after 2 minutes.
- **Note**: This cancels ALL open conditional orders — including valid SL/TP on open positions.
  Would need careful design to only activate this when no positions are open.

#### IMP-8: Trailing stop option
- **Current**: Fixed SL at 2.0x ATR. SL never moves.
- **Fix**: Add `sl_type: TRAILING` option in config. In executor, if trailing, use
  `type: TRAILING_STOP_MARKET` with `priceRate` (e.g. 0.02 = 2% trail) instead of
  `STOP_MARKET` with fixed `stopPrice`.
- **Note**: Trailing stops and fixed SL have different risk profiles. Backtester would
  need updating to test this before enabling in live.

---

## Execution Runbook

Bot root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector`
Ollama base: `http://localhost:11434`
Model: confirmed via `ollama list` — use first qwen2.5-coder tag found

**Ollama helper** (reused for every call):
```bash
curl -s --max-time 600 http://localhost:11434/api/generate \
  -d "{\"model\":\"MODEL\",\"prompt\":\"PROMPT\",\"stream\":false}" \
  | python -c "import sys,json; r=json.load(sys.stdin); open('OUTPUT','w').write(r['response'])"
```
Then strip markdown fences from OUTPUT if present:
```bash
python -c "
import re, sys
t = open('OUTPUT').read()
m = re.search(r'\`\`\`python\n(.*?)\`\`\`', t, re.DOTALL)
open('OUTPUT','w').write(m.group(1) if m else t)
"
```

---

### STEP 0 — Preflight

```bash
ollama list
# → confirm qwen2.5-coder:Xb present. Note exact tag.
# If missing: ollama pull qwen2.5-coder:7b
```

---

### STEP 1 — P0: executor.py (FIX-2 + FIX-3)

**Spec to send Ollama:**
> You are given executor.py (pasted in full below). Apply ONLY these two changes and output the complete modified Python file. No explanation, no markdown prose — code only.
>
> CHANGE 1 (FIX-2: use actual fill price):
> In the execute() method, after `order_data = result.get("data", {})` and before building position_record, add:
> `fill_price = float(order_data.get("avgPrice", 0) or 0)`
> Then in position_record, change `"entry_price": mark_price` to
> `"entry_price": fill_price if fill_price > 0 else mark_price`
>
> CHANGE 2 (FIX-3: SL direction validation):
> In execute(), after mark_price is confirmed > 0 and before calculating notional, add:
> ```
> if signal.direction == "LONG" and signal.sl_price >= mark_price:
>     logger.error("SL invalid LONG: sl=%.6f >= mark=%.6f %s", signal.sl_price, mark_price, symbol)
>     self.notifier.send("<b>SL REJECTED</b>\n" + symbol + " LONG sl above entry")
>     return None
> if signal.direction == "SHORT" and signal.sl_price <= mark_price:
>     logger.error("SL invalid SHORT: sl=%.6f <= mark=%.6f %s", signal.sl_price, mark_price, symbol)
>     self.notifier.send("<b>SL REJECTED</b>\n" + symbol + " SHORT sl below entry")
>     return None
> ```
> [PASTE executor.py CONTENT HERE]

**Commands:**
```bash
# 1. Send to Ollama → executor_new.py
# 2. py_compile
python -c "import py_compile; py_compile.compile('executor_new.py', doraise=True)" && echo PASS || echo FAIL
# 3. Diff
git diff --no-index executor.py executor_new.py
# 4. If PASS + diff looks correct:
cp executor.py executor.py.bak && cp executor_new.py executor.py
```

---

### STEP 2 — P0: position_monitor.py (FIX-1)

**Spec to send Ollama:**
> You are given position_monitor.py (pasted in full below). Apply ONLY these changes. Output complete Python file, no explanation.
>
> CHANGE 1: In __init__, add parameter `commission_rate=0.0016` after `config`. Store as `self.commission_rate = commission_rate`. Add to logger.info line: show commission_rate.
>
> CHANGE 2: In _handle_close(), find `commission = notional * 0.0012  # 0.06% taker x 2 sides`
> Replace with: `commission = notional * self.commission_rate`
> Update the comment to: `# taker fee x 2 sides (from config)`
>
> [PASTE position_monitor.py CONTENT HERE]

**Commands:**
```bash
python -c "import py_compile; py_compile.compile('position_monitor_new.py', doraise=True)" && echo PASS || echo FAIL
git diff --no-index position_monitor.py position_monitor_new.py
cp position_monitor.py position_monitor.py.bak && cp position_monitor_new.py position_monitor.py
```

---

### STEP 3 — P0: main.py (FIX-1 startup + pass commission rate)

**Spec to send Ollama:**
> You are given main.py (pasted in full below). Apply ONLY these changes. Output complete Python file, no explanation.
>
> CHANGE 1: Add new constant near top: `COMMISSION_RATE_PATH = "/openApi/swap/v2/user/commissionRate"`
>
> CHANGE 2: Add new function after set_leverage_and_margin():
> ```python
> def fetch_commission_rate(auth):
>     """Fetch taker commission rate from BingX. Returns float or default 0.0016."""
>     req = auth.build_signed_request("GET", COMMISSION_RATE_PATH)
>     try:
>         resp = requests.get(req["url"], headers=req["headers"], timeout=10)
>         data = resp.json()
>         if data.get("code", 0) == 0:
>             rate = float(data["data"]["commission"]["takerCommissionRate"])
>             logger.info("Commission rate from API: %.6f (%.4f%%)", rate, rate * 100)
>             return rate * 2  # round-trip (open + close)
>         logger.warning("Commission rate API error %s — using default", data.get("code"))
>     except Exception as e:
>         logger.warning("Commission rate fetch failed: %s — using default", e)
>     return 0.0016  # fallback: 0.08% x 2 sides
> ```
>
> CHANGE 3: In main(), after set_leverage_and_margin() call, add:
> `commission_rate = fetch_commission_rate(auth)`
>
> CHANGE 4: In PositionMonitor constructor call, add `commission_rate=commission_rate` as kwarg.
>
> [PASTE main.py CONTENT HERE]

**Commands:**
```bash
python -c "import py_compile; py_compile.compile('main_new.py', doraise=True)" && echo PASS || echo FAIL
git diff --no-index main.py main_new.py
cp main.py main.py.bak && cp main_new.py main.py
```

---

### STEP 4 — P0 Verification

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python -m pytest tests/ -v 2>&1 | tail -20
# Must still show 67/67 passing
```

---

### STEP 5 — P1: ws_listener.py (new file)

**Spec to send Ollama:**
> Write a complete Python file ws_listener.py for a BingX futures WebSocket order fill listener.
>
> Requirements:
> - Class WSListener(threading.Thread, daemon=True)
> - __init__(self, auth, fill_queue, logger): auth=BingXAuth instance, fill_queue=queue.Queue()
> - On start: call POST /openApi/swap/v1/listenKey (signed) → get listenKey
> - Connect to wss://open-api-swap.bingx.com/swap-market?listenKey=KEY using websockets library (async)
> - Parse incoming messages: if event type ORDER_TRADE_UPDATE and X==FILLED:
>   extract symbol=o.s, avg_price=float(o.ap), reason="TP_HIT" if o.o contains TAKE_PROFIT else "SL_HIT" if o.o contains STOP else None
>   if reason is not None: put {"symbol": symbol, "avg_price": avg_price, "reason": reason} into fill_queue
> - Refresh listenKey every 55 minutes: POST /openApi/swap/v1/listenKey/extend
> - On disconnect: reconnect after 5s, max 3 attempts, then log error and stop
> - run() method runs asyncio event loop in this thread
> - stop() method sets _stop_event to exit loop cleanly
> - All functions have docstrings. Dual logging (file handler inherited from root logger + logger param).
> - Imports: threading, asyncio, queue, json, logging, time, requests, websockets
> - PROD URL: wss://open-api-swap.bingx.com/swap-market
> - VST URL: wss://vst-open-api-ws.bingx.com/swap-market
> - Detect demo_mode from auth.demo_mode to choose URL
> - No escaped quotes in f-strings — use string concatenation

**Commands:**
```bash
pip install websockets  # if not already installed
python -c "import py_compile; py_compile.compile('ws_listener.py', doraise=True)" && echo PASS || echo FAIL
```

---

### STEP 6 — P1: main.py patch (WS thread + listenKey)

**Spec to send Ollama:**
> Given main.py (already modified in Step 3, pasted below), add WebSocket thread support.
> Apply ONLY these changes:
>
> CHANGE 1: Add import: `from ws_listener import WSListener` and `import queue`
>
> CHANGE 2: In main(), after commission_rate = fetch_commission_rate(auth), add:
> `fill_queue = queue.Queue()`
> `ws_thread = WSListener(auth=auth, fill_queue=fill_queue, logger=logger)`
>
> CHANGE 3: Pass fill_queue to PositionMonitor: add `fill_queue=fill_queue` kwarg
>
> CHANGE 4: After t1.start(), t2.start(), add:
> `ws_thread.start()`
> `logger.info("Threads started: MarketLoop + MonitorLoop + WSListener")`
>
> CHANGE 5: In shutdown, after shutdown_event.set(), add: `ws_thread.stop()`
>
> [PASTE modified main.py CONTENT HERE]

**Commands:**
```bash
python -c "import py_compile; py_compile.compile('main_new.py', doraise=True)" && echo PASS || echo FAIL
git diff --no-index main.py main_new.py
cp main.py main.py.bak2 && cp main_new.py main.py
```

---

### STEP 7 — P1: position_monitor.py patch (drain fill_queue first)

**Spec to send Ollama:**
> Given position_monitor.py (already modified in Step 2, pasted below), add fill_queue drain support.
> Apply ONLY these changes:
>
> CHANGE 1: Add `import queue` to imports (if not present)
>
> CHANGE 2: In __init__, add parameter `fill_queue=None`. Store as `self.fill_queue = fill_queue or queue.Queue()`
>
> CHANGE 3: In check(), BEFORE the live_raw = self._fetch_positions() call, add:
> ```python
> # Drain WebSocket fill events first (instant detection path)
> while not self.fill_queue.empty():
>     try:
>         event = self.fill_queue.get_nowait()
>         symbol = event.get("symbol", "")
>         key_long = symbol + "_LONG"
>         key_short = symbol + "_SHORT"
>         for key in (key_long, key_short):
>             pos = self.state.get_open_positions().get(key)
>             if pos:
>                 logger.info("WS fill event: %s reason=%s price=%.6f",
>                             key, event["reason"], event["avg_price"])
>                 self._handle_close_with_price(key, pos, event["avg_price"], event["reason"])
>     except queue.Empty:
>         break
> ```
>
> CHANGE 4: Add new method _handle_close_with_price(self, key, pos_data, exit_price, exit_reason):
> Same logic as _handle_close but takes exit_price and exit_reason directly (no _detect_exit call needed).
>
> [PASTE modified position_monitor.py CONTENT HERE]

**Commands:**
```bash
python -c "import py_compile; py_compile.compile('position_monitor_new.py', doraise=True)" && echo PASS || echo FAIL
cp position_monitor.py position_monitor.py.bak2 && cp position_monitor_new.py position_monitor.py
```

---

### STEP 8 — P1 + P2 Verification

```bash
python -m pytest tests/ -v 2>&1 | tail -20
# Must still show 67/67 passing
```

---

### STEP 9 — P2: risk_gate.py + state_manager.py (cooldown + 101209)

Ollama generates both files per specs in the Improvements Catalog above.
Spec details: cooldown_bars check in risk_gate using state.last_exit_time[key], 101209 handler in executor.py that halves qty on retry, session_blocked set in state_manager.

---

### STEP 10 — P2: scripts/reconcile_pnl.py (new file)

Ollama generates standalone script: reads trades.csv, calls /openApi/swap/v1/trade/positionHistory for past 24h, compares netProfit to recorded pnl_net, logs discrepancies to logs/YYYY-MM-DD-reconcile.log.

---

### STEP 11 — Final test suite

```bash
python -m pytest tests/ -v 2>&1 | tail -5
# 67/67 must pass. If new files added, any new test files must also pass.
```

**Build before first live deposit (P1):**
4. IMP-1: WebSocket fill detection (2-3h — new file + thread + queue integration)
5. IMP-2: Reconciliation script (1h — standalone, no bot changes)

**Build during first live week (P2):**
6. IMP-3: Error 101209 handling
7. IMP-4: Cooldown filter
8. IMP-5: Startup commission fetch (consolidates FIX-1 properly)

---

## Files to Modify

| File | Changes |
|------|---------|
| `PROJECTS/bingx-connector/position_monitor.py` | FIX-1 (commission rate param), IMP-4 (cooldown check) |
| `PROJECTS/bingx-connector/executor.py` | FIX-2 (fill price), FIX-3 (SL validation), IMP-3 (101209) |
| `PROJECTS/bingx-connector/main.py` | IMP-5 (startup commission query), IMP-1 (spawn WS thread) |
| `PROJECTS/bingx-connector/state_manager.py` | IMP-3 (session_blocked set), IMP-4 (last_exit_time) |
| `PROJECTS/bingx-connector/risk_gate.py` | IMP-4 (cooldown gate) |
| `PROJECTS/bingx-connector/config.yaml` | IMP-4 (cooldown_bars param) |

## New Files

| File | Purpose |
|------|---------|
| `PROJECTS/bingx-connector/ws_listener.py` | WebSocket daemon thread (IMP-1) |
| `PROJECTS/bingx-connector/scripts/reconcile_pnl.py` | PnL audit vs BingX history (IMP-2) |

---

## Verification

- P0 fixes: Run `python -m pytest tests/ -v` — all 67 tests must pass. Then run bot in
  VST demo for 1h and confirm Telegram EXIT messages show correct commission.
- IMP-1 (WebSocket): Use `--debug` mode to log all WS events. Force-close a test position
  on BingX UI and verify bot receives FILLED event within 5 seconds.
- IMP-2 (reconcile): Run after a session with known trades. Compare bot's CSV vs
  BingX positionHistory netProfit. Should match within rounding.
