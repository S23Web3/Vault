# BingX Connector v1.4 — Trade Lifecycle Use Case

Generated: 2026-03-03
Config: ttp_enabled=true, ttp_act=0.5%, ttp_dist=0.2%, be_auto=true, margin=$5, leverage=10x

---

## Actors

- **MarketLoop** — thread, polls OHLCV every 45s
- **MonitorLoop** — thread, polls exchange every 60s
- **WSListener** — thread, receives fill events instantly
- **BingX Exchange** — external system
- **Telegram** — notification sink

---

## Use Case: Full Trade Lifecycle (TTP + Auto-BE path)

```
MarketLoop          StrategyAdapter       RiskGate           Executor           Exchange
    |                     |                   |                  |                  |
    |--tick()--->          |                   |                  |                  |
    |            on_new_bar(symbol, ohlcv)     |                  |                  |
    |                     |                   |                  |                  |
    |            [warmup < 201 bars?]          |                  |                  |
    |            skip                         |                  |                  |
    |                     |                   |                  |                  |
    |            plugin.get_signal()          |                  |                  |
    |            signal: LONG/SHORT/NONE      |                  |                  |
    |                     |                   |                  |                  |
    |            [signal == NONE]             |                  |                  |
    |            goto TTP_EVAL               |                  |                  |
    |                     |                   |                  |                  |
    |            evaluate(signal, state)----->|                  |                  |
    |                     |         [PASS: 8 checks]             |                  |
    |                     |         - halt_flag == False         |                  |
    |                     |         - positions < 8             |                  |
    |                     |         - no duplicate key          |                  |
    |                     |         - grade in allowed (A/B)    |                  |
    |                     |         - atr_ratio >= 0.003        |                  |
    |                     |         - daily_trades < 50         |                  |
    |                     |         - cooldown elapsed (15min)  |                  |
    |                     |         - not session_blocked       |                  |
    |                     |<--APPROVED---------|                  |                  |
    |                     |                   |                  |                  |
    |                     |--execute(signal)------------------>  |                  |
    |                     |                   |    fetch mark price--------------->|
    |                     |                   |                  |<--mark_price-----|
    |                     |                   |    fetch step_size---------------->|
    |                     |                   |                  |<--step_size------|
    |                     |                   |    POST MARKET + SL + TP---------->|
    |                     |                   |    notional = $5 * 10 = $50        |
    |                     |                   |    qty = $50 / mark_price          |
    |                     |                   |                  |<--order_id-------|
    |                     |                   |    record_open_position()          |
    |                     |<--result(ok)------|                  |                  |
    |                     |                   |                  |                  |
    |            [TTP_EVAL — runs every bar for all open positions]
    |                     |                   |                  |                  |
    |            _evaluate_ttp_for_symbol()   |                  |                  |
    |            TTPExit.evaluate(high, low)  |                  |                  |
    |            write ttp_state to position  |                  |                  |
    |                     |                   |                  |                  |
```

---

## Use Case: TTP State Machine (per bar, per open position)

```
Bar N:   ttp_state = MONITORING
         high/low does NOT reach entry * 1.005 (LONG) or entry * 0.995 (SHORT)
         --> return MONITORING, no state change

Bar N+k: high/low REACHES activation price
         --> _try_activate(): state = ACTIVATED, extreme = activation_price
         --> _update_extreme_on_activation(): extend extreme if bar overshoots
         --> return ACTIVATED (no trail check on activation candle)

Bar N+k+1 onwards:
         PESSIMISTIC path:
           - Check LOW <= trail (LONG) or HIGH >= trail (SHORT) FIRST
           - If hit: closed_pessimistic = True, state = CLOSED
           - If not: update extreme if new high/low, update trail
         OPTIMISTIC path (informational only — does NOT drive state):
           - Update extreme FIRST, then check reversal
           - closed_optimistic = True if hit (stored, not acted on)
         --> write ttp_state, ttp_trail_level, ttp_extreme to position
         --> if closed_pessimistic: set ttp_close_pending = True
```

---

## Use Case: Auto-BE Raise (MonitorLoop, every 60s)

```
MonitorLoop         PositionMonitor        Exchange           State
    |                     |                   |                 |
    |--check_breakeven()-->|                   |                 |
    |                     |                   |                 |
    |            [be_auto == False] --> return |                 |
    |                     |                   |                 |
    |            for each open position:      |                 |
    |            [be_raised == True] --> skip |                 |
    |            [ttp_state != ACTIVATED] --> skip              |
    |                     |                   |                 |
    |            LONG:  be_price = entry * (1 + commission_rate)
    |            SHORT: be_price = entry * (1 - commission_rate)
    |            e.g. entry=$50, rate=0.0016 -> be_price=$50.08
    |                     |                   |                 |
    |            _cancel_open_sl_orders()---->|                 |
    |                     |<--cancelled--------|                 |
    |            POST STOP_MARKET at be_price->|                |
    |                     |<--order_id---------|                |
    |            update_position(be_raised=True, sl_price=be_price)
    |                     |                   |                 |
    |            Telegram: "BE+FEES RAISED (TTP)"              |
```

---

## Use Case: TTP Close Execution (MonitorLoop, every 60s)

```
MonitorLoop         PositionMonitor        Exchange           State
    |                     |                   |                 |
    |--check_ttp_closes()->|                   |                 |
    |                     |                   |                 |
    |            [ttp_close_pending == False] --> skip          |
    |                     |                   |                 |
    |            _fetch_single_position() --->|                 |
    |                     |<--live_pos---------|                 |
    |            [position gone] --> clear flag, skip          |
    |                     |                   |                 |
    |            _cancel_all_orders() ------->|                 |
    |            (cancels SL + TP + trailing) |                 |
    |            _place_market_close() ------>|                 |
    |                     |<--ok--------------|                 |
    |            update(ttp_close_pending=False, ttp_exit_pending=True)
```

---

## Use Case: Position Close Detection (MonitorLoop, every 60s)

```
MonitorLoop         PositionMonitor        Exchange           State / CSV
    |                     |                   |                 |
    |--check()------------>|                   |                 |
    |                     |                   |                 |
    |            [drain WSListener fill queue first — instant path]
    |                     |                   |                 |
    |            GET /positions ------------->|                 |
    |                     |<--live_positions---|                 |
    |                     |                   |                 |
    |            diff: state_positions vs live_positions        |
    |            any key in state but NOT on exchange = closed  |
    |                     |                   |                 |
    |            _detect_exit(symbol, pos_data):               |
    |            [ttp_exit_pending] -> reason = TTP_EXIT        |
    |            [SL open, TP gone] -> reason = TP_HIT          |
    |            [TP open, SL gone] -> reason = SL_HIT          |
    |            [both gone]        -> query allOrders history  |
    |                     |                   |                 |
    |            calc PnL:                    |                 |
    |            LONG:  pnl_gross = (exit - entry) * qty       |
    |            SHORT: pnl_gross = (entry - exit) * qty       |
    |            commission = notional * 0.0016                 |
    |            pnl_net = pnl_gross - commission               |
    |                     |                   |                 |
    |            close_position(key, exit_price, reason, pnl)  |
    |            remove from open_positions   |                 |
    |            update daily_pnl             |                 |
    |            append trades.csv            |                 |
    |            [daily_pnl <= -$15] -> halt_flag = True        |
    |            Telegram: "POSITION CLOSED reason pnl"        |
```

---

## Use Case: Daily Reset (MonitorLoop, 17:00 UTC)

```
MonitorLoop         PositionMonitor        State              Telegram
    |                     |                   |                 |
    |--check_daily_reset()->|                  |                 |
    |            [hour != 17 OR same date] --> skip            |
    |                     |                   |                 |
    |            read: daily_pnl, daily_trades, open_count     |
    |            reset_daily():               |                 |
    |            daily_pnl = 0.0              |                 |
    |            daily_trades = 0             |                 |
    |            halt_flag = False            |                 |
    |            open_positions unchanged     |                 |
    |                     |                   |                 |
    |            "DAILY SUMMARY\nPnL: $X\nTrades: N\nOpen: M"->|
```

---

## Order Types Summary

| Order | Placed at | Side (LONG) | Stop Price | Working Type |
|-------|-----------|-------------|------------|--------------|
| MARKET (entry) | Entry | BUY | — | — |
| STOP_MARKET (initial SL) | Entry | SELL | signal.sl_price (entry - 2xATR) | MARK_PRICE |
| TAKE_PROFIT_MARKET | Entry | SELL | signal.tp_price (or null) | MARK_PRICE |
| STOP_MARKET (BE raise) | TTP ACTIVATED | SELL | entry * 1.0016 | MARK_PRICE |
| MARKET (TTP close) | closed_pessimistic | SELL | — | — |

---

## State Field Lifecycle

| Field | Written | By | Cleared |
|-------|---------|----|---------|
| entry_price | entry | executor | close_position |
| sl_price | entry | executor | close_position |
| sl_price | TTP activated | check_breakeven (BE raise) | close_position |
| tp_price | entry | executor | close_position |
| quantity / notional_usd | entry | executor | close_position |
| ttp_state | every bar | _evaluate_ttp_for_symbol | close_position |
| ttp_trail_level | every bar | _evaluate_ttp_for_symbol | close_position |
| ttp_extreme | every bar | _evaluate_ttp_for_symbol | close_position |
| ttp_close_pending | closed_pessimistic bar | _evaluate_ttp_for_symbol | check_ttp_closes |
| ttp_exit_pending | TTP market close placed | check_ttp_closes | close_position |
| be_raised | TTP ACTIVATED | check_breakeven | close_position |
| daily_pnl | close | close_position | reset_daily (17:00 UTC) |
| daily_trades | entry | record_open_position | reset_daily (17:00 UTC) |
| halt_flag | daily_pnl <= -$15 | position_monitor | reset_daily (17:00 UTC) |

---

## Current Config Values (active)

| Parameter | Value | Effect |
|-----------|-------|--------|
| margin_usd | $5 | Notional = $50 per trade |
| leverage | 10x | Notional = $50 per trade |
| ttp_enabled | true | TTP engine active on all positions |
| ttp_act | 0.5% | Activation at entry +/- 0.5% |
| ttp_dist | 0.2% | Trail stop 0.2% behind extreme |
| be_auto | true | SL raised to BE+fees on TTP activation |
| max_positions | 8 | Max $40 margin deployed simultaneously |
| daily_loss_limit | $15 | Hard stop if daily loss exceeds $15 |
| cooldown_bars | 3 | 15min (3 x 5m) between entries per symbol+direction |
| sl_atr_mult | 2.0 | SL placed at entry +/- 2x ATR |
| tp_atr_mult | null | No fixed TP — rely on TTP or manual |
| require_stage2 | true | Stoch40+60 must rotate before Grade A fires |
| allow_a | true | A-grade entries allowed |
| allow_b | true | B-grade entries allowed |
| allow_c | false | C-grade entries blocked |
