# BingX Connector — Trade UML: All Scenarios
**Generated:** 2026-02-27
**Source files:** main.py, executor.py, position_monitor.py, signal_engine.py, risk_gate.py, state_manager.py

---

## 1. System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         main.py (orchestrator)                          │
│                                                                         │
│  Thread A: market_loop()              Thread B: monitor_loop()          │
│  ┌──────────────────────┐             ┌──────────────────────────────┐  │
│  │  MarketDataFeed       │             │  PositionMonitor             │  │
│  │  ._fetch_klines()     │             │  .check()                    │  │
│  │  ._is_new_bar()       │             │  ._detect_exit()             │  │
│  │  .tick(callback)      │             │  ._fetch_filled_exit()       │  │
│  └──────────┬───────────┘             │  ._handle_close()            │  │
│             │ on_new_bar              │  .check_daily_reset()        │  │
│             ▼                         │  .check_hourly_metrics()     │  │
│  ┌──────────────────────┐             └──────────────────────────────┘  │
│  │  StrategyAdapter     │                                               │
│  │  .on_new_bar()       │─────────────────────────┐                    │
│  │  FourPillarsV384     │                          │                    │
│  │  .get_signal()       │                          ▼                    │
│  └──────────┬───────────┘             ┌──────────────────────────────┐  │
│             │ signal                  │  StateManager (shared)       │  │
│             ▼                         │  .open_positions (dict)      │  │
│  ┌──────────────────────┐             │  .daily_pnl                  │  │
│  │  RiskGate            │             │  .daily_trades               │  │
│  │  .evaluate()         │             │  .halt_flag                  │  │
│  └──────────┬───────────┘             │  .record_open_position()     │  │
│             │ approved                │  .close_position()           │  │
│             ▼                         │  .reset_daily()              │  │
│  ┌──────────────────────┐             └──────────────────────────────┘  │
│  │  Executor            │                                               │
│  │  .execute()          │                                               │
│  └──────────────────────┘                                               │
│                                                                         │
│  Shared: BingXAuth, Notifier (Telegram), requests.Session              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Trade Lifecycle — State Machine

```
                    ┌──────────┐
                    │   IDLE   │  (no position for this symbol)
                    └────┬─────┘
                         │ new bar closes, signal fires
                         ▼
                    ┌──────────────────┐
                    │ RISK_GATE_CHECK  │
                    └────┬─────────────┘
          BLOCKED        │              APPROVED
     ┌───────────────────┤              │
     ▼                   │              ▼
┌──────────┐             │       ┌───────────────────┐
│ REJECTED │◄────────────┘       │  ENTRY_IN_PROGRESS│
│ (logged) │                     └────────┬──────────┘
└──────────┘                              │
     │ (symbol can fire again             │ order placed OK
     │  on next bar)                      ▼
     │                            ┌───────────────┐
     └───────────────────────────►│     OPEN      │
                                  │ (SL+TP live)  │
                                  └──────┬────────┘
                                         │
                  ┌──────────────────────┼─────────────────────┐
                  │                      │                      │
                  ▼                      ▼                      ▼
         ┌──────────────┐      ┌───────────────────┐   ┌──────────────────┐
         │  ENTRY_FAILED│      │  EXIT_DETECTED    │   │   HARD_STOP      │
         │ (returns to  │      │ (key gone from    │   │ (halt_flag=True, │
         │  IDLE)       │      │  exchange)        │   │  daily loss hit) │
         └──────────────┘      └─────────┬─────────┘   └──────────────────┘
                                         │
                      ┌──────────────────┼──────────────────┐
                      │                  │                  │
                      ▼                  ▼                  ▼
              ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐
              │   TP_HIT     │  │   SL_HIT     │  │  EXIT_UNKNOWN     │
              │TP order filled│  │SL order filled│  │(order history    │
              │SL cancelled  │  │TP cancelled  │  │ empty or purged) │
              └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘
                     │                 │                    │
                     └─────────────────┴────────────────────┘
                                       │
                                       ▼
                              ┌────────────────┐
                              │     CLOSED     │
                              │ (trades.csv,   │
                              │  state.json    │
                              │  updated)      │
                              └────────────────┘
```

---

## 3. Signal-to-Entry — Full Sequence

```
MarketLoop    MarketFeed     StrategyAdapter    RiskGate      Executor    Exchange     State
    │              │                │               │              │          │           │
    │──tick()─────►│                │               │              │          │           │
    │              │─_fetch_klines()►               │              │          │           │
    │              │◄──────────────df               │              │          │           │
    │              │                │               │              │          │           │
    │              │─_is_new_bar()  │               │              │          │           │
    │              │  [last bar ts  │               │              │          │           │
    │              │   unchanged]   │               │              │          │           │
    │              │──SKIP──────────►               │              │          │           │
    │              │                │               │              │          │           │
    │              │  [new bar ts]  │               │              │          │           │
    │              │──callback(sym,df)──────────────►              │          │           │
    │              │                │               │              │          │           │
    │              │                │─warmup check  │              │          │           │
    │              │                │  [< 200 bars] │              │          │           │
    │              │                │──SKIP─────────►              │          │           │
    │              │                │               │              │          │           │
    │              │                │  [>= 200 bars]│              │          │           │
    │              │                │─plugin.get_signal(df)        │          │           │
    │              │                │               │              │          │           │
    │              │                │  [no signal]  │              │          │           │
    │              │                │──return None──►              │          │           │
    │              │                │               │              │          │           │
    │              │                │  [signal A/B] │              │          │           │
    │              │                │─evaluate(sig,state)──────────►          │           │
    │              │                │               │              │          │           │
    │              │                │  [any check fails]           │          │           │
    │              │                │◄──BLOCKED(reason)────────────│          │           │
    │              │                │                              │          │           │
    │              │                │  [all 6 checks pass]         │          │           │
    │              │                │◄──APPROVED───────────────────│          │           │
    │              │                │─execute(signal, symbol)──────────────────►          │
    │              │                │               │              │          │           │
    │              │                │               │  fetch_mark_price()─────►           │
    │              │                │               │              │◄─────mark_price──────│
    │              │                │               │  [price fail]│          │           │
    │              │                │               │              │──return None          │
    │              │                │               │              │          │           │
    │              │                │               │  fetch_step_size()──────►           │
    │              │                │               │              │◄────step_size─────── │
    │              │                │               │              │          │           │
    │              │                │               │  calc_qty = floor(notional / mark_price / step) * step
    │              │                │               │              │          │           │
    │              │                │               │  [qty == 0]  │          │           │
    │              │                │               │              │──return None          │
    │              │                │               │              │          │           │
    │              │                │               │  place_order(LONG/SHORT, qty, SL, TP)──────►
    │              │                │               │              │◄─────order_id─────── │
    │              │                │               │              │          │           │
    │              │                │               │  [order fail]│          │           │
    │              │                │               │              │──return None (notifier alert)
    │              │                │               │              │          │           │
    │              │                │               │              │─record_open_position()────────►
    │              │                │               │              │          │           │◄──OK──│
    │              │                │               │              │──notifier.send(ENTRY)         │
```

---

## 4. Risk Gate — 6-Check Decision Tree

```
signal arrives
      │
      ▼
 ┌─────────────────────────────────────┐
 │ Check 1: HARD STOP                  │
 │  halt_flag == True ?                │
 │  OR daily_pnl <= -loss_limit ?      │
 └──────┬─────────────────────────────┘
        │ YES → BLOCKED("hard stop / loss limit")
        │ NO
        ▼
 ┌─────────────────────────────────────┐
 │ Check 2: MAX POSITIONS              │
 │  len(open_positions) >= max_pos ?   │
 └──────┬─────────────────────────────┘
        │ YES → BLOCKED("max positions")
        │ NO
        ▼
 ┌─────────────────────────────────────┐
 │ Check 3: DUPLICATE                  │
 │  position_key in open_positions ?   │
 │  key = symbol + direction           │
 └──────┬─────────────────────────────┘
        │ YES → BLOCKED("duplicate position")
        │ NO
        ▼
 ┌─────────────────────────────────────┐
 │ Check 4: GRADE FILTER               │
 │  signal.grade in allowed_grades ?   │
 │  (from plugin: A, B — C disabled)   │
 └──────┬─────────────────────────────┘
        │ NO → BLOCKED("grade not allowed")
        │ YES
        ▼
 ┌─────────────────────────────────────┐
 │ Check 5: ATR THRESHOLD              │
 │  atr / entry_price < min_atr_ratio? │
 │  (min_atr_ratio = 0.003 in config)  │
 └──────┬─────────────────────────────┘
        │ YES → BLOCKED("atr too quiet")
        │ NO
        ▼
 ┌─────────────────────────────────────┐
 │ Check 6: DAILY TRADE LIMIT          │
 │  daily_trades >= max_daily_trades ? │
 │  (max = 200 in config)              │
 └──────┬─────────────────────────────┘
        │ YES → BLOCKED("daily trade limit")
        │ NO
        ▼
   APPROVED → Executor.execute()
```

---

## 5. Exit Detection — Classification Tree

```
MonitorLoop calls monitor.check() every 60s
      │
      ▼
fetch_positions() from exchange
      │
for each key in state.open_positions:
      │
      ├── key still on exchange? ──YES──► continue (still open)
      │
      └── key GONE from exchange
                │
                ▼
        _detect_exit(position_data)
                │
      query allOrders for SL order ID + TP order ID
                │
          ┌─────┴─────────────────────────────────┐
          │                                       │
     BOTH PENDING                        at least one FILLED/CANCELLED
          │                                       │
          ▼                                       │
   false alarm                    ┌───────────────┼───────────────┐
   (VST race condition)           │               │               │
   skip                           │               │               │
                                  ▼               ▼               ▼
                           SL FILLED         TP FILLED        BOTH GONE
                           TP CANCELLED      SL CANCELLED     (VST purge)
                                  │               │               │
                                  ▼               ▼               │
                               SL_HIT          TP_HIT             │
                                  │               │               │
                                  └───────────────┘               │
                                        │                         │
                                        │           _fetch_filled_exit()
                                        │              query allOrders history
                                        │                         │
                                        │              ┌──────────┴──────────┐
                                        │              │                     │
                                        │         found filled          not found
                                        │         order record          (purged)
                                        │              │                     │
                                        │         use actual           use estimated
                                        │         fill price           price + EXIT_UNKNOWN
                                        │              │                     │
                                        └──────────────┴─────────────────────┘
                                                       │
                                                       ▼
                                              _handle_close(exit_price, exit_reason)
```

---

## 6. PnL Calculation

```
LONG trade:
  gross_pnl = (exit_price - entry_price) * quantity
  commission = notional_usd * 0.0012        (0.06% taker x 2 sides)
  pnl_net = gross_pnl - commission

SHORT trade:
  gross_pnl = (entry_price - exit_price) * quantity
  commission = notional_usd * 0.0012
  pnl_net = gross_pnl - commission

notional_usd = margin_usd * leverage        ($75 * 20 = $1500)
quantity = floor(notional / mark_price / step_size) * step_size
```

---

## 7. Daily Limit & Hard Stop Flow

```
After every _handle_close():
      │
      ▼
state.daily_pnl += pnl_net
      │
      ▼
 daily_pnl <= -loss_limit?
  (loss_limit = $2000 in config)
      │
  YES │                   NO
      ▼                    │
halt_flag = True           │ continue normal
notifier.send(HARD STOP)   │
      │                    │
      ▼                    │
ALL new signals BLOCKED ◄──┘
(Check 1 in RiskGate)

Daily Reset at 17:00 UTC:
      │
      ▼
daily_pnl = 0
daily_trades = 0
halt_flag = False          ← clears HARD STOP
notifier.send(daily summary)
```

---

## 8. Startup Reconciliation

```
main() startup sequence:
      │
      ▼
load state.json (open_positions from previous session)
      │
      ▼
fetch live positions from exchange
      │
      ▼
reconcile(live_positions):
  for key in state.open_positions:
      │
      ├── key on exchange? ──YES──► keep (real position)
      │
      └── key NOT on exchange ──► remove from state (phantom)
                                   log WARNING
                                   (NO PnL calculated — position
                                    exit was not captured)
      │
      ▼
warmup(): fetch klines for all 47 symbols
      │
      ▼
spawn MarketLoop thread (daemon)
spawn MonitorLoop thread (daemon)
      │
      ▼
wait for SIGINT/SIGTERM
      │
      ▼
graceful shutdown (15s timeout for threads)
notifier.send(BOT STOPPED)
```

---

## 9. VST-Specific Known Failures (documented 2026-02-27)

```
Scenario                    Frequency    Outcome in code
──────────────────────────────────────────────────────────
Filled orders vanish        HIGH         → EXIT_UNKNOWN + estimated price
STOP fills wrong direction  MEDIUM       → SL_HIT with positive PnL (mislabeled)
Both SL+TP auto-cleaned     HIGH         → _fetch_filled_exit() fallback
Per-coin position limit     LOW          → order fail, entry returns None, notifier alert
Mark price drift from signal MEDIUM      → larger SL distance than expected
1m: EXIT_UNKNOWN ~100%      CONFIRMED    → switched to 5m (6% rate)
5m: EXIT_UNKNOWN ~6%        CONFIRMED    → acceptable, monitoring
```

---

## 10. Key Position Record Schema

```python
position_data = {
    "symbol":       "RIVER-USDT",
    "direction":    "LONG",           # or "SHORT"
    "grade":        "A",              # A, B, or C
    "entry_price":  0.0421,
    "quantity":     35642.0,          # contract units
    "notional_usd": 1500.0,           # margin * leverage
    "sl_price":     0.0412,
    "tp_price":     0.0463,
    "sl_order_id":  "2026...",
    "tp_order_id":  "2026...",
    "atr":          0.00019,
    "entry_time":   "2026-02-27T10:00:00+00:00",
    "bar_ts":       1740650400000     # ms timestamp of signal bar
}
```

---

## 11. BingX Order Status States

```
Order lifecycle on BingX (all three order types used by bot):

Order Type          Used for          Working Type
──────────────────────────────────────────────────
MARKET              Entry             n/a (fills immediately)
STOP_MARKET         SL                MARK_PRICE
TAKE_PROFIT_MARKET  TP                MARK_PRICE

BingX status values:
─────────────────────────────────────────────────────────────────
Status              Meaning                    Where visible
─────────────────────────────────────────────────────────────────
NEW                 Order placed, not triggered openOrders + allOrders
PENDING_NEW         Processing (transient)      openOrders (briefly)
PARTIALLY_FILLED    Partial fill (rare, market) openOrders + allOrders
FILLED              Fully executed              allOrders only
CANCELED            Cancelled by bot or BingX   allOrders only
EXPIRED             Expired by exchange         allOrders only
─────────────────────────────────────────────────────────────────

How status maps to exit detection:

  openOrders (active)    allOrders (history)    Code path
  ─────────────────────────────────────────────────────────
  SL=NEW, TP=NEW        (both still pending)    → both_open → skip (race condition)
  SL=NEW, TP=absent     TP in allOrders=FILLED  → TP_HIT
  TP=NEW, SL=absent     SL in allOrders=FILLED  → SL_HIT
  neither               TP in allOrders=FILLED  → TP_HIT  (_fetch_filled_exit)
  neither               SL in allOrders=FILLED  → SL_HIT  (_fetch_filled_exit)
  neither               nothing found           → EXIT_UNKNOWN (use sl_price estimate)

Auto-cancel pattern (BingX VST + Live):
  When TP fills → BingX auto-cancels SL  → SL status = CANCELED in allOrders
  When SL fills → BingX auto-cancels TP  → TP status = CANCELED in allOrders
  (VST also purges FILLED orders from history — hence EXIT_UNKNOWN at ~6% on 5m)
```

---

## 12. Full Data Flow Map

```
DATA SOURCES
────────────────────────────────────────────────────────────────

External (BingX API):
  Public (no auth):
    /openApi/swap/v3/quote/klines
        → MarketDataFeed._fetch_klines(symbol, limit=201)
        → DataFrame [time, open, high, low, close, volume]
        → FourPillarsV384.get_signal(df) → Signal

    /openApi/swap/v2/quote/price
        → Executor.fetch_mark_price(symbol)
        → float: current mark price for qty calc

    /openApi/swap/v2/quote/contracts
        → Executor.fetch_step_size(symbol)
        → float: tradeMinQuantity (step size for rounding)

  Private (HMAC-SHA256 signed):
    GET /openApi/swap/v2/user/positions
        → PositionMonitor._fetch_positions()
        → live position list → detect which keys are gone

    GET /openApi/swap/v2/trade/openOrders?symbol=X
        → PositionMonitor._detect_exit(symbol, pos_data)
        → pending SL/TP orders → classify TP_HIT vs SL_HIT

    GET /openApi/swap/v2/trade/allOrders?symbol=X&startTime=T
        → PositionMonitor._fetch_filled_exit(symbol, pos_data)
        → filled order history → actual avgPrice fill

Local files (read at startup):
  config.yaml       → symbols (47), strategy params, risk limits,
                       daily_loss_limit, sl/tp multipliers, margin, leverage
  state.json        → open_positions {}, daily_pnl, daily_trades,
                       halt_flag, session_start
  .env              → BINGX_API_KEY, BINGX_SECRET_KEY,
                       BINGX_TELEGRAM_TOKEN, BINGX_TELEGRAM_CHAT_ID

────────────────────────────────────────────────────────────────
COMPUTE PATH
────────────────────────────────────────────────────────────────

  Klines DataFrame
       │
       ▼
  compute_signals(df, params)          ← shared with backtester
       │
       ▼
  FourPillarsV384.get_signal(df)       ← reads iloc[-2] (last closed bar)
       │ Signal(direction, grade, entry_price, sl_price, tp_price, atr, bar_ts)
       ▼
  RiskGate.evaluate(signal, state)     ← 6 checks
       │ APPROVED
       ▼
  Executor.execute(signal, symbol)
       │  fetch mark_price + step_size
       │  calc qty = floor(notional / price / step) * step
       │  POST MARKET order + SL + TP
       │ position_record{}
       ▼
  StateManager.record_open_position()  ← state.json written

  (every 60s, MonitorLoop):
  PositionMonitor.check()
       │  GET positions → compare to state
       │  key gone from exchange?
       ▼
  _detect_exit() → _fetch_filled_exit()
       │ (exit_price, exit_reason)
       ▼
  _handle_close() → PnL calc
       │
       ▼
  StateManager.close_position()        ← state.json + trades.csv written

────────────────────────────────────────────────────────────────
DATA SINKS
────────────────────────────────────────────────────────────────

  BingX API (write):
    POST /openApi/swap/v2/trade/order  → entry + SL + TP attached
    DELETE /openApi/swap/v2/trade/order → cancel orphaned SL or TP

  Local files (write):
    state.json     → updated on every open / close event
    trades.csv     → row appended on every close:
                     [timestamp, symbol, direction, grade,
                      entry_price, exit_price, exit_reason,
                      pnl_net, quantity, notional_usd,
                      entry_time, order_id]
    logs/YYYY-MM-DD-bot.log → all INFO/WARNING/ERROR (TimedRotating, 30d)

  Telegram (Notifier.send, HTML, UTC+4):
    Event                   Trigger
    ─────────────────────────────────────────────────
    ENTRY alert             Executor.execute() success
    EXIT alert              _handle_close() always
    HARD STOP alert         daily_pnl <= -loss_limit
    WARNING (50% limit)     check_hourly_metrics()
    DAILY SUMMARY           check_daily_reset() at 17:00 UTC
    ORDER FAILED            Executor._safe_post() returns None
    ORDER ID UNKNOWN        order_id == "unknown" guard
```

---

## 13. Trade Management — Extended Scenarios (PLANNED, NOT YET BUILT)

```
Note: Breakeven raise, trailing TP, and raised SL are NOT currently wired.
BingX API supports all three via cancel + re-place order pattern.
These are design specs for future implementation.

─────────────────────────────────────────────────────────────────────
Scenario A: BREAKEVEN RAISE
─────────────────────────────────────────────────────────────────────

Trigger: price moves >= be_atr_mult * ATR in profitable direction
         (e.g., be_atr_mult = 1.0 in config)

LONG:  mark_price >= entry + be_atr_mult * atr
SHORT: mark_price <= entry - be_atr_mult * atr

Action:
  1. DELETE /trade/order (cancel current SL order by sl_order_id)
  2. POST /trade/order:
       type=STOP_MARKET
       stopPrice = entry_price   ← SL now AT entry (break even)
       workingType = MARK_PRICE
  3. Update state: sl_price = entry_price
                   sl_order_id = new_order_id
  4. Log + Telegram: "BE RAISED: {symbol} SL moved to entry"

State after: BREAKEVEN_ARMED
  (position still open, but SL now at entry — worst case = 0 gross, net = -commission)

Outcome if SL then triggers at entry:
  exit_reason = SL_HIT
  pnl_gross   = 0.0
  pnl_net     = 0.0 - commission (small net loss)
  label this: BE_HIT in exit reason (optional extension)

─────────────────────────────────────────────────────────────────────
Scenario B: RAISED SL (lock-in profit)
─────────────────────────────────────────────────────────────────────

Trigger: price moves >= lock_atr_mult * ATR in profitable direction
         (e.g., lock_atr_mult = 2.0 — deeper than BE trigger)

LONG:  mark_price >= entry + lock_atr_mult * atr
SHORT: mark_price <= entry - lock_atr_mult * atr

Action:
  1. DELETE /trade/order (cancel current SL)
  2. POST /trade/order:
       type=STOP_MARKET
       stopPrice = entry + 1.0 * atr   ← SL now IN profit
       workingType = MARK_PRICE
  3. Update state: sl_price = new_sl, sl_order_id = new_id
  4. Log + Telegram: "SL RAISED: {symbol} SL locked at +1 ATR"

Outcome if SL then triggers:
  exit_reason = SL_HIT
  pnl_net     = positive (locked in ~+1 ATR minus commission)

─────────────────────────────────────────────────────────────────────
Scenario C: TRAILING TP
─────────────────────────────────────────────────────────────────────

Trigger: price moves >= trail_atr_mult * ATR beyond current TP
         (i.e., position is running further into profit)

LONG:  mark_price >= tp_price + trail_step_atr * atr
SHORT: mark_price <= tp_price - trail_step_atr * atr

Action:
  1. DELETE /trade/order (cancel current TP order by tp_order_id)
  2. POST /trade/order:
       type=TAKE_PROFIT_MARKET
       stopPrice = mark_price + 1.0 * atr   (LONG)
                   mark_price - 1.0 * atr   (SHORT)
       workingType = MARK_PRICE
  3. Update state: tp_price = new_tp, tp_order_id = new_id
  4. Log + Telegram: "TP TRAILED: {symbol} TP → new_tp"

Risk window: between DELETE and new POST, there is a brief window
             where no TP order exists — position can only exit via SL.
             Alternative: use BingX native TRAILING_STOP_MARKET order type.

─────────────────────────────────────────────────────────────────────
Full Extended State Machine (with planned features)
─────────────────────────────────────────────────────────────────────

                         OPEN (SL + TP live)
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                     │
         ▼                    ▼                     ▼
  price hits BE         price hits lock       price hits trail
  trigger (1x ATR)      trigger (2x ATR)      trigger beyond TP
         │                    │                     │
         ▼                    ▼                     ▼
  BREAKEVEN_ARMED      SL_LOCKED (profit)     TP_TRAILING
  (SL → entry)         (SL → entry+1xATR)     (TP → market+1xATR)
         │                    │                     │
         └────────────────────┴─────────────────────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
            TP_HIT          SL_HIT        EXIT_UNKNOWN
         (profit win)   (could be BE,   (fallback logic)
                         lock, or loss)
               │              │              │
               └──────────────┴──────────────┘
                              │
                           CLOSED
                       (trades.csv + state.json)
```

---

## 14. Order Cancel + Replace — API Pattern

```
Used by: BE raise, SL lock, trailing TP (all planned features)

Step 1: Cancel existing order
  DELETE /openApi/swap/v2/trade/order
  Params: symbol, orderId (from state: sl_order_id or tp_order_id)
  Response: code=0 means success

Step 2: Place replacement order
  POST /openApi/swap/v2/trade/order
  Params: symbol, side (opposite of entry), positionSide, type, stopPrice, workingType
  Response: new orderId

Step 3: Update state (critical — if not saved, bot will use stale price on exit)
  state.sl_price = new_stop_price
  state.sl_order_id = new_order_id
  state.json written to disk

Guards needed:
  - If DELETE fails → do NOT place replacement (old SL still active)
  - If POST fails after DELETE → NO stop order on position (DANGEROUS)
    → Notifier alert immediately, option to halt further trading
  - Bot restart after crash: state.json has updated sl_order_id — reconcile on startup
```
