# WEEX Connector v1.0 — Full UML Architecture
# Date: 2026-03-13
# Status: Phase 3 COMPLETE

---

## 1. System Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SYSTEMS                         │
│                                                                 │
│  ┌──────────────────────────┐   ┌──────────────────────────┐   │
│  │   WEEX Exchange API       │   │   Telegram API           │   │
│  │  REST: api-contract.weex  │   │  alerts + error reports  │   │
│  │  WS:   ws-contract.weex   │   └──────────────┬───────────┘   │
│  └──────────┬───────────────┘                  │               │
│             │ REST + WebSocket                  │ HTTPS         │
└─────────────┼──────────────────────────────────┼───────────────┘
              │                                  │
┌─────────────▼──────────────────────────────────▼───────────────┐
│                    WEEX CONNECTOR BOT                           │
│                                                                 │
│   ┌────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│   │  main.py   │  │  config.yaml │  │  .env               │   │
│   │ (orchestr) │  │ (runtime cfg)│  │ (API keys)          │   │
│   └─────┬──────┘  └──────────────┘  └─────────────────────┘   │
│         │                                                       │
│   ┌─────▼──────────────────────────────────────────────────┐   │
│   │                   THREAD LAYER                          │   │
│   │  MarketLoop │ MonitorLoop │ WSListener                  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   STATE LAYER                           │   │
│   │  state.json (positions)  │  trades.csv (history)       │   │
│   └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Actors:**
| Actor | Role |
|-------|------|
| WEEX Exchange API | Provides market data, accepts orders, pushes fill events |
| Telegram API | Receives alert messages (entry, exit, errors, daily summary) |
| Connector Bot | Core process: signals, execution, monitoring, state |
| Config (YAML + .env) | Runtime parameters + secret credentials |
| State Files | Persistence layer: open positions + trade history |

---

## 2. Module / Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WEEX CONNECTOR                                 │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  main.py                                                         │   │
│  │  • Loads config.yaml + .env                                      │   │
│  │  • Validates all required fields                                 │   │
│  │  • Starts 3 daemon threads                                       │   │
│  │  • Registers SIGTERM/SIGINT graceful shutdown                    │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │ spawns                                │
│          ┌──────────────────────┼──────────────────────┐               │
│          ▼                      ▼                      ▼               │
│  ┌───────────────┐   ┌─────────────────┐   ┌─────────────────────┐    │
│  │ MarketLoop    │   │  MonitorLoop    │   │   WSListener        │    │
│  │ (Thread)      │   │  (Thread)       │   │   (Thread)          │    │
│  │ 45s poll      │   │  30s check      │   │   async fills       │    │
│  └──────┬────────┘   └────────┬────────┘   └──────────┬──────────┘    │
│         │                     │                        │               │
│         ▼                     ▼                        ▼               │
│  ┌────────────┐  ┌──────────────────┐    ┌─────────────────────┐      │
│  │data_fetcher│  │position_monitor  │    │   ws_listener       │      │
│  │            │  │                  │    │                     │      │
│  │• klines    │  │• query positions │    │• WS connect/auth    │      │
│  │• 201-bar   │  │• BE raise        │    │• pong on srv ping   │      │
│  │  buffer    │  │• TTP tighten     │    │• fill event parse   │      │
│  │• new-bar   │  │• orphan cleanup  │    │• fill_queue.put()   │      │
│  │  detection │  │• fill_queue.get  │    └─────────────────────┘      │
│  └──────┬─────┘  └──────────────────┘                                 │
│         │                                                               │
│         ▼                                                               │
│  ┌────────────────┐                                                     │
│  │ signal_engine  │                                                     │
│  │                │                                                     │
│  │• call plugin   │                                                     │
│  │• A/B/C grading │                                                     │
│  │• risk_gate     │                                                     │
│  │• dispatch      │                                                     │
│  └───────┬────────┘                                                     │
│          │ signal                                                       │
│          ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      EXECUTION LAYER                             │  │
│  │                                                                  │  │
│  │  ┌─────────────┐   ┌──────────────┐   ┌─────────────────────┐  │  │
│  │  │ executor.py │   │  ttp_engine  │   │   risk_gate         │  │  │
│  │  │             │   │              │   │                     │  │  │
│  │  │• market ord │   │• candle-lvl  │   │• ATR ratio check    │  │  │
│  │  │• SL algo ord│   │  TTP eval    │   │• max positions      │  │  │
│  │  │• cancel ord │   │• trail price │   │• daily trades       │  │  │
│  │  │• close pos  │   │  update      │   │• daily loss         │  │  │
│  │  └──────┬──────┘   └──────────────┘   │• cooldown timer     │  │  │
│  │         │                             │• symbol cooldown    │  │  │
│  │         ▼                             │• position exists    │  │  │
│  │  ┌──────────────────────────────────┐ │• SL distance valid  │  │  │
│  │  │         weex_auth.py             │ └─────────────────────┘  │  │
│  │  │  • sign(secret,ts,method,path,b) │                          │  │
│  │  │  • ws_sign(secret,ts)            │                          │  │
│  │  │  • build_headers()               │                          │  │
│  │  └──────────────────────────────────┘                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      SHARED SERVICES                             │  │
│  │                                                                  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │  │
│  │  │ state_manager  │  │  api_utils     │  │  notifier        │  │  │
│  │  │                │  │                │  │                  │  │  │
│  │  │• state.json RW │  │• mark price    │  │• entry alert     │  │  │
│  │  │• state_lock    │  │• rate limiter  │  │• exit alert      │  │  │
│  │  │• deep copy pat │  │• http helpers  │  │• BE raise alert  │  │  │
│  │  │• trades.csv    │  │• contractid_to │  │• TTP alert       │  │  │
│  │  │  append        │  │  _symbol()     │  │• error alert     │  │  │
│  │  └────────────────┘  └────────────────┘  └──────────────────┘  │  │
│  │                                                                  │  │
│  │  ┌────────────────┐                                             │  │
│  │  │  time_sync     │                                             │  │
│  │  │• server time   │                                             │  │
│  │  │• offset_ms     │                                             │  │
│  │  │• synced_ts()   │                                             │  │
│  │  └────────────────┘                                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      PLUGIN LAYER                                │  │
│  │                                                                  │  │
│  │  ┌──────────────────────────────────┐                           │  │
│  │  │  plugins/four_pillars.py         │                           │  │
│  │  │  (implements StrategyPlugin ABC) │                           │  │
│  │  │  • compute_signal(bars) -> Signal│                           │  │
│  │  │  • A/B/C grade logic             │                           │  │
│  │  │  • stochastic evaluation         │                           │  │
│  │  └──────────────────────────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

| Module | Responsibility | Key Inputs | Key Outputs |
|--------|---------------|------------|-------------|
| `main.py` | Startup, config validation, thread orchestration, shutdown | `config.yaml`, `.env` | 3 running threads |
| `weex_auth.py` | HMAC signing, header building | API key/secret/passphrase | Auth headers dict |
| `time_sync.py` | Fetch server time, maintain offset, provide synced timestamps | WEEX `/market/time` | `offset_ms`, synced unix_ms |
| `data_fetcher.py` | OHLCV polling, 201-bar rolling buffer, new-bar detection | kline endpoint | `bars` list, `new_bar` bool |
| `executor.py` | Place market orders, SL algoOrders, cancel orders, close positions | signal dict | order IDs |
| `position_monitor.py` | Query open positions, BE raise, TTP tighten, orphan cleanup | positions endpoint, fill_queue | state mutations |
| `state_manager.py` | Atomic state.json read/write, deep copy, trades.csv append | lock, state dict | persisted state |
| `risk_gate.py` | 8 pre-trade checks, returns pass/fail + reason | config, state | bool, str reason |
| `signal_engine.py` | Call strategy plugin, handle plugin errors, dispatch to executor | bars, plugin | Signal or None |
| `notifier.py` | Send Telegram HTML messages for all alert types | bot token, chat_id, message dict | HTTP response |
| `ttp_engine.py` | Candle-level trailing profit evaluation (no exchange native TTP) | bars, position state | new trail price or None |
| `ws_listener.py` | WebSocket connect, auth, heartbeat, fill event parsing, fill_queue | WS URL, auth | fill_queue items |
| `api_utils.py` | Mark price fetch, token-bucket rate limiter, HTTP request helper, symbol conversion | endpoints | prices, responses |
| `plugins/four_pillars.py` | Four Pillars strategy: stochastic grading, A/B/C signals | bars (201 candles) | Signal(direction, grade, sl_price, size) |

---

## 3. Thread Model Diagram

```
main.py startup
     │
     ├─── time_sync.sync_once()   ← blocking, must pass before threads start
     ├─── leverage + margin mode  ← set for each symbol in config
     ├─── fetch commission rate   ← cached at startup
     │
     ├─── Thread: MarketLoop (daemon=True)
     │       │  loop interval: 45s
     │       │
     │       ├── data_fetcher.poll()          → 201-bar kline buffer
     │       ├── data_fetcher.is_new_bar()    → bool
     │       │    └── [if new bar]
     │       │         ├── signal_engine.evaluate(bars)
     │       │         │    ├── risk_gate.check_all()   → pass/fail
     │       │         │    ├── plugin.compute_signal() → Signal | None
     │       │         │    └── [if signal]
     │       │         │         └── executor.open_position()
     │       │         └── ttp_engine.evaluate()  → update trail SL if active
     │       │
     │       └── [exception] → log + sleep 10s + continue
     │
     ├─── Thread: MonitorLoop (daemon=True)
     │       │  loop interval: 30s
     │       │
     │       ├── fill_queue.get_nowait()  → process pending fills (non-blocking)
     │       │    └── [fill event]
     │       │         ├── state_manager.on_fill()   → update position state
     │       │         └── notifier.send_exit_alert()
     │       │
     │       ├── position_monitor.query_positions()  → live position list
     │       ├── position_monitor.check_be_raise()   → [if trigger] cancel+replace SL
     │       ├── position_monitor.check_ttp()        → [if TTP active] tighten SL
     │       └── position_monitor.cleanup_orphans()  → close untracked positions
     │
     └─── Thread: WSListener (daemon=True)
             │  persistent connection
             │
             ├── ws_listener.connect()     → wss://ws-contract.weex.com/v2/ws/private
             ├── ws_listener.auth()        → send login frame
             ├── ws_listener.subscribe()   → {"event":"subscribe","channel":"fill"}
             └── ws_listener.on_message()
                  ├── [event: "ping" received from server]
                  │    └── send {"event":"pong","time": server_time}
                  │         (5 missed pongs = server disconnects)
                  └── [fill event received]
                       └── fill_queue.put(fill_dict)


SHARED STATE (protected by state_manager.state_lock — threading.Lock):
┌────────────────────────────────────────────────────┐
│  state.json in-memory mirror:                      │
│  {                                                 │
│    "positions": {                                  │
│      "BTCUSDT_LONG": {                             │
│        "symbol": str,                              │
│        "side": str,                                │
│        "entry_price": float,                       │
│        "size": float,                              │
│        "sl_order_id": str,       ← algo order ID  │
│        "sl_price": float,                          │
│        "be_raised": bool,                          │
│        "ttp_active": bool,                         │
│        "ttp_trail_price": float,                   │
│        "atr_at_entry": float,    ← for BE/TTP calc  │
│        "entry_time": int,        ← unix ms         │
│        "client_order_id": str,                     │
│      }                                             │
│    },                                              │
│    "daily": {                                      │
│      "date": str,                ← YYYY-MM-DD UTC  │
│      "trade_count": int,                           │
│      "loss_usdt": float,                           │
│      "last_trade_time": int,                       │
│    }                                               │
│  }                                                 │
└────────────────────────────────────────────────────┘

FILL QUEUE (thread-safe queue.Queue — unbounded):
  WSListener → put(fill_dict) → MonitorLoop → get_nowait()
```

---

## 4. Sequence Diagram: Full Trade Lifecycle

```
MarketLoop          signal_engine       risk_gate          executor
    │                    │                  │                  │
    │  new bar detected  │                  │                  │
    │───────────────────>│                  │                  │
    │                    │  check_all()     │                  │
    │                    │─────────────────>│                  │
    │                    │  PASS            │                  │
    │                    │<─────────────────│                  │
    │                    │  compute_signal()│                  │
    │                    │  (plugin)        │                  │
    │                    │  Signal(LONG,A)  │                  │
    │                    │───────────────────────────────────> │
    │                    │                  │  place_order()   │
    │                    │                  │  MARKET BUY LONG │
    │                    │                  │  POST /capi/v3/order
    │                    │                  │                  │
    │                    │                  │  orderId returned│
    │                    │                  │  (immediate)     │
    │                    │                  │                  │
    │                    │                  │  [wait WS fill]  │

WSListener          fill_queue          MonitorLoop        state_manager
    │                    │                  │                  │
    │  fill event recv   │                  │                  │
    │  (cmt_btcusdt BUY) │                  │                  │
    │  contractid_to_sym │                  │                  │
    │  → BTCUSDT         │                  │                  │
    │  put(fill_dict)    │                  │                  │
    │───────────────────>│                  │                  │
    │                    │  get_nowait()    │                  │
    │                    │─────────────────>│                  │
    │                    │  on_fill(entry)  │                  │
    │                    │                  │─────────────────>│
    │                    │                  │  acquire lock    │
    │                    │                  │  deep copy state │
    │                    │                  │  write position  │
    │                    │                  │  release lock    │
    │                    │                  │  write state.json│
    │                    │                  │<─────────────────│

executor            weex_auth           WEEX API           state_manager
    │                    │                  │                  │
    │  place_sl_order()  │                  │                  │
    │  algoOrder POST    │                  │                  │
    │  STOP_MARKET SELL  │                  │                  │
    │  clientAlgoId=...  │                  │                  │
    │  build_headers()   │                  │                  │
    │───────────────────>│                  │                  │
    │  signed headers    │                  │                  │
    │<───────────────────│                  │                  │
    │  POST /capi/v3/algoOrder              │                  │
    │──────────────────────────────────────>│                  │
    │  {orderId, success:true}              │                  │
    │<──────────────────────────────────────│                  │
    │  store sl_order_id │                  │                  │
    │───────────────────────────────────────────────────────> │
    │                    │                  │  update state    │
    │                    │                  │  sl_order_id set │


    ~~~ TIME PASSES — price moves in direction ~~~


MonitorLoop         position_monitor    executor            state_manager
    │                    │                  │                  │
    │  30s check         │                  │                  │
    │  query_positions() │                  │                  │
    │───────────────────>│                  │                  │
    │  BE trigger check  │                  │                  │
    │  entry+ATR reached │                  │                  │
    │  place_sl_order()  │                  │                  │
    │  new SL at BE      │                  │                  │
    │  ──────────────────────────────────> │                  │
    │                    │  confirm success │                  │
    │  cancel_sl_order() │                  │                  │
    │  old sl_order_id   │                  │                  │
    │  ──────────────────────────────────> │                  │
    │                    │                  │                  │
    │  update state      │                  │                  │
    │  be_raised=True    │                  │                  │
    │  sl_order_id=new   │                  │                  │
    │  ──────────────────────────────────────────────────────>│
    │                    │  notifier.send_be_alert()           │


    ~~~ TTP ACTIVATION ~~~


MarketLoop          ttp_engine          state_manager
    │                    │                  │
    │  new bar (profit   │                  │
    │  threshold hit)    │                  │
    │  evaluate_ttp()    │                  │
    │───────────────────>│                  │
    │  ttp_active=True   │                  │
    │  trail_price = H-N │                  │
    │                    │─────────────────>│
    │                    │  update state    │
    │                    │  ttp_active=True │


    ~~~ EXIT: WS fill event (SL hit) ~~~


WSListener          fill_queue          MonitorLoop        state_manager
    │                    │                  │                  │
    │  fill event recv   │                  │                  │
    │  SELL LONG fill    │                  │                  │
    │  realizePnl != 0   │                  │                  │
    │  put(fill_dict)    │                  │                  │
    │───────────────────>│                  │                  │
    │                    │  get_nowait()    │                  │
    │                    │─────────────────>│                  │
    │                    │  on_fill(exit)   │                  │
    │                    │  detect_close()  │                  │
    │                    │  compute_pnl()   │                  │
    │                    │                  │─────────────────>│
    │                    │                  │  acquire lock    │
    │                    │                  │  remove position │
    │                    │                  │  release lock    │
    │                    │                  │  append trades.csv│
    │                    │                  │  update daily.*  │
    │                    │  notifier.send_exit_alert()         │


ERROR PATHS:
─ order fails (success:false)  → log error, notifier.send_error(), do NOT write state
─ WS disconnects               → ws_listener reconnects with backoff (5s, 10s, 30s max)
─ SL cancel fails              → log critical, notifier.send_error(), keep old SL in state
─ plugin exception             → log error, skip signal this bar, do NOT abort thread
─ state.json write fails       → log critical, raise (crash is safer than silent corruption)
```

---

## 5. Data Flow Diagram: State Management

```
LOCK ACQUISITION PATTERN (state_manager.py)
─────────────────────────────────────────────
Every write to _state follows this exact pattern:

  with state_lock:                    ← acquire
      s = copy.deepcopy(_state)       ← W03: deep copy (not shallow)
      s["positions"][key] = {...}     ← mutate copy
      _state = s                      ← replace reference atomically
      _flush_state_to_disk()          ← write state.json inside lock


READS use a separate pattern (read-only, still locked):

  with state_lock:
      snapshot = copy.deepcopy(_state)    ← snapshot under lock
  # use snapshot outside lock — never hold lock across I/O


WHAT GETS WRITTEN AT EACH EVENT:
─────────────────────────────────

  EVENT: entry_fill (position opened)
  ────────────────────────────────────
  _state["positions"]["{symbol}_{side}"] = {
      symbol, side, entry_price, size,
      atr_at_entry: float,     ← for BE/TTP threshold calc
      sl_order_id: None,       ← set after SL placed
      sl_price: 0.0,
      be_raised: False,
      ttp_active: False,
      ttp_trail_price: 0.0,
      entry_time: unix_ms,
      client_order_id: str,
  }
  state.json: full overwrite (atomic via tmp file rename)
  trades.csv: NOT yet (trade not closed)

  EVENT: sl_placed (after algoOrder success)
  ────────────────────────────────────────────
  _state["positions"][key]["sl_order_id"] = orderId_str
  _state["positions"][key]["sl_price"] = trigger_price
  state.json: full overwrite

  EVENT: be_raised (breakeven trigger)
  ──────────────────────────────────────
  _state["positions"][key]["be_raised"] = True
  _state["positions"][key]["sl_order_id"] = new_orderId
  _state["positions"][key]["sl_price"] = entry_price
  state.json: full overwrite

  EVENT: ttp_activated
  ──────────────────────
  _state["positions"][key]["ttp_active"] = True
  _state["positions"][key]["ttp_trail_price"] = initial_trail
  state.json: full overwrite

  EVENT: ttp_tightened (per new bar)
  ────────────────────────────────────
  _state["positions"][key]["ttp_trail_price"] = new_trail
  _state["positions"][key]["sl_order_id"] = new_orderId   ← after cancel+replace
  state.json: full overwrite

  EVENT: exit_fill (position closed)
  ────────────────────────────────────
  del _state["positions"][key]
  _state["daily"]["trade_count"] += 1
  _state["daily"]["loss_usdt"] += max(0, -pnl)
  _state["daily"]["last_trade_time"] = unix_ms
  state.json: full overwrite
  trades.csv: APPEND one row


TRADES.CSV APPEND SEQUENCE:
─────────────────────────────
  acquire state_lock
  compute pnl from fill data
  mutate _state (remove position, update daily)
  flush state.json
  release state_lock
  ← CSV append is OUTSIDE lock (file I/O, not shared state)
  append row to trades.csv:
    date, symbol, side, entry_price, exit_price, size,
    gross_pnl, commission, net_pnl, duration_s,
    exit_reason, grade


STATE.JSON ATOMIC WRITE (prevents corruption on crash):
─────────────────────────────────────────────────────────
  tmp_path = state_path.with_suffix(".json.tmp")
  tmp_path.write_text(json.dumps(_state, indent=2), encoding="utf-8")
  tmp_path.replace(state_path)    ← atomic on same filesystem
```

---

## 6. WEEX-Specific Differences from BingX

| Concern | BingX Connector v2 | WEEX Connector v1 |
|---------|-------------------|-------------------|
| Auth method | HMAC params in query string | Headers: `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-PASSPHRASE`, `ACCESS-TIMESTAMP` |
| Passphrase | Not required | Required (Bitget white-label) |
| REST symbol format | `BTC-USDT` (hyphenated) | `BTCUSDT` (no prefix, uppercase) |
| WS symbol format | Same as REST | `cmt_btcusdt` — must convert on receipt |
| Symbol conversion needed | No | Yes — `contractid_to_symbol()` in api_utils |
| SL order type | `TRAILING_STOP_MARKET` (native TTP) | `algoOrder STOP_MARKET` (separate endpoint) |
| SL field for client ID | `newClientOrderId` | `clientAlgoId` |
| Cancel SL endpoint | `/order?orderId=` | `/algoOrder?orderId=` — store orderId, NOT clientAlgoId |
| TTP mechanism | TRAILING_STOP_MARKET native | Candle-level engine only (`ttp_engine.py`) |
| Step size source | Separate contracts fetch | `quantityPrecision` in `/market/exchangeInfo` |
| Position side field | `positionSide` | `side` (same values: LONG/SHORT) |
| Position mode | One-way or hedge | SEPARATED (hedge) required — set explicitly |
| Leverage setting | Single leverage call | Must set `isolatedLongLeverage` + `isolatedShortLeverage` both |
| Response wrapper (GET) | `{code, data, msg}` always | Raw object/array — no wrapper on GET endpoints |
| Response wrapper (POST) | `{code, data, msg}` always | `{orderId, success, errorCode, errorMessage}` on orders |
| Check order success | `code == 0` | `success == true` |
| WS fill event path | `ORDER_TRADE_UPDATE.o` | `msg.data.orderFillTransaction[]` |
| WS fill symbol field | `symbol` | `contractId` (cmt_ format — must convert) |
| WS fill PnL field | `rp` (realized pnl) | `realizePnl` (non-zero only on close) |
| Close position endpoint | `POST /order` reduceOnly=true | `POST /closePositions` (dedicated endpoint) |
| Rate limit | Weight-based per endpoint | 500 req/10s public, weight-based authenticated |
| Signing string components | `timestamp + METHOD + path + body` | Same — Bitget standard |
| WS auth path string | `/openApi/swap/listen-key` flow | `/v2/ws/private` hardcoded in sign message |

---

## Module Dependency Graph

```
main.py
  ├── config.yaml + .env
  ├── time_sync.py
  ├── weex_auth.py
  ├── api_utils.py
  │     └── weex_auth.py
  │     └── time_sync.py
  ├── state_manager.py
  ├── notifier.py
  ├── risk_gate.py
  │     └── state_manager.py
  ├── data_fetcher.py
  │     └── api_utils.py
  ├── signal_engine.py
  │     ├── data_fetcher.py
  │     ├── risk_gate.py
  │     ├── executor.py
  │     └── plugins/four_pillars.py
  ├── executor.py
  │     ├── weex_auth.py
  │     ├── api_utils.py
  │     ├── time_sync.py
  │     └── state_manager.py
  ├── position_monitor.py
  │     ├── api_utils.py
  │     ├── executor.py
  │     ├── ttp_engine.py
  │     ├── state_manager.py
  │     └── notifier.py
  ├── ttp_engine.py
  │     └── state_manager.py (read-only)
  └── ws_listener.py
        ├── weex_auth.py
        ├── time_sync.py
        └── fill_queue (queue.Queue — passed in)

plugins/four_pillars.py
  └── (no internal imports — pure signal logic)
```
