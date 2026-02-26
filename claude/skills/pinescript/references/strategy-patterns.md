# Strategy Patterns Reference

## Basic Strategy Template

```pinescript
//@version=6
strategy("Strategy Template",
    overlay=true,
    margin_long=100,
    margin_short=100,
    initial_capital=10000,
    default_qty_type=strategy.percent_of_equity,
    default_qty_value=100,
    commission_type=strategy.commission.cash_per_order,
    commission_value=6,
    pyramiding=1
)

// === INPUTS ===
i_atrLen = input.int(14, "ATR Length")
i_atrMult = input.float(2.0, "ATR Multiplier")

// === CALCULATIONS ===
atr = ta.atr(i_atrLen)

// === CONDITIONS ===
longCondition = ta.crossover(ta.ema(close, 9), ta.ema(close, 21))
shortCondition = ta.crossunder(ta.ema(close, 9), ta.ema(close, 21))

// === ENTRIES ===
if longCondition
    strategy.entry("Long", strategy.long)

if shortCondition
    strategy.entry("Short", strategy.short)

// === EXITS ===
strategy.exit("Exit Long", "Long",
    stop=strategy.position_avg_price - atr * i_atrMult,
    limit=strategy.position_avg_price + atr * i_atrMult * 2)
```

---

## Strategy with Webhook Alerts

```pinescript
//@version=6
strategy("Webhook Strategy", overlay=true)

i_positionSize = input.float(250, "Position Size USD")
i_leverage = input.int(20, "Leverage")
i_secret = input.string("YOUR_SECRET", "Webhook Secret")

atr = ta.atr(14)

longCondition = ta.crossover(ta.ema(close, 9), ta.ema(close, 21))

longMsg = '{' +
    '"action": "buy",' +
    '"ticker": "' + syminfo.ticker + '",' +
    '"price": ' + str.tostring(close) + ',' +
    '"stop_loss": ' + str.tostring(close - atr * 2) + ',' +
    '"position_size": ' + str.tostring(i_positionSize) + ',' +
    '"leverage": ' + str.tostring(i_leverage) + ',' +
    '"secret": "' + i_secret + '"' +
    '}'

if longCondition
    strategy.entry("Long", strategy.long, alert_message=longMsg)
```

---

## Position Sizing

### Fixed USD Position (Crypto)
```pinescript
positionUSD = 250.0
leverage = 20
contracts = positionUSD * leverage / close

strategy.entry("Long", strategy.long, qty=contracts)
```

### Fixed Risk Percentage
```pinescript
riskPercent = 0.02  // 2% risk per trade
accountSize = strategy.equity
stopDistance = math.abs(close - stopLoss)
positionSize = (accountSize * riskPercent) / stopDistance

strategy.entry("Long", strategy.long, qty=positionSize)
```

---

## Exit Strategies

### ATR-Based Trailing Stop
```pinescript
var float trailStop = na

if strategy.position_size > 0
    newStop = close - atr * 2
    trailStop := na(trailStop) ? newStop : math.max(trailStop, newStop)
    if close < trailStop
        strategy.close("Long")
        trailStop := na
else
    trailStop := na
```

### Partial Profit Taking
```pinescript
if longCondition
    strategy.entry("Long", strategy.long, qty=1.0)
    // Take 50% at 1R
    strategy.exit("TP1", "Long", qty_percent=50, limit=close + atr * 2)
    // Take remaining at 2R
    strategy.exit("TP2", "Long", limit=close + atr * 4)
```

---

## Session-Based Trading

```pinescript
i_sessionStart = input.session("0930-1600", "Trading Session")
i_timezone = input.string("America/New_York", "Timezone")

inSession = not na(time(timeframe.period, i_sessionStart, i_timezone))

// Only trade in session
longCondition = ta.crossover(ema_fast, ema_slow) and inSession

// Close all at session end
if strategy.position_size != 0 and not inSession
    strategy.close_all(comment="Session End")
```

---

## Performance Dashboard

```pinescript
winRate = strategy.wintrades / (strategy.wintrades + strategy.losstrades) * 100
profitFactor = strategy.grossprofit / math.abs(strategy.grossloss)
maxDD = strategy.max_drawdown

var table perf = table.new(position.bottom_right, 2, 4, bgcolor=color.black)
if barstate.islast
    table.cell(perf, 0, 0, "Win Rate", text_color=color.white)
    table.cell(perf, 1, 0, str.tostring(winRate, "#.#") + "%", text_color=color.white)
    table.cell(perf, 0, 1, "Profit Factor", text_color=color.white)
    table.cell(perf, 1, 1, str.tostring(profitFactor, "#.##"), text_color=color.white)
    table.cell(perf, 0, 2, "Max DD", text_color=color.white)
    table.cell(perf, 1, 2, str.tostring(maxDD, "#.##"), text_color=color.red)
    table.cell(perf, 0, 3, "Net Profit", text_color=color.white)
    table.cell(perf, 1, 3, str.tostring(strategy.netprofit, "#.##"),
               text_color=strategy.netprofit > 0 ? color.green : color.red)
```

---

## Direction Flip Pattern

**Auto-reverse without phantom trades.** Cancel stale exits, then `strategy.entry()` in the opposite direction flips the position in one order.

```pinescript
// From v3.7.1 lines 388-394
bool didEnterThisBar = entryBar == bar_index
if didEnterThisBar and posDir == "LONG"
    strategy.cancel("Exit Short")      // Clear stale exit from old direction
    strategy.entry("Long", strategy.long)  // Auto-reverses short→long
if didEnterThisBar and posDir == "SHORT"
    strategy.cancel("Exit Long")
    strategy.entry("Short", strategy.short)
```

---

## B/C Open Fresh Pattern

Allow lower-grade signals to open new positions (not just add to existing). When `bOpenFresh` is on, B/C signals can also flip direction.

```pinescript
// From v3.7.1 lines 275-280
bool enter_long_bc = (long_signal_b or long_signal_c) and
    ((i_bOpenFresh and isFlat) or (not isFlat and posDir == "LONG")) and cooldownOK

// B/C can also flip when bOpenFresh is on
bool flip_long_bc = (long_signal_b or long_signal_c) and
    i_bOpenFresh and not isFlat and posDir == "SHORT" and cooldownOK
```

---

## SL/TP Strategy Comparison

| Strategy | SL Type | TP Type | Best For | Weakness |
|----------|---------|---------|----------|----------|
| Static ATR (v3.7.1) | Fixed N×ATR at entry | Fixed N×ATR at entry | Rebate farming, high frequency | No trailing, misses runners |
| Cloud 3 Trail (v3.5.1) | Cloud 3 ± 1 ATR, trails | None (trail only) | Trending markets | Activation delay, bleeds in chop |
| AVWAP Trail (v3.6) | AVWAP ± max(stdev, ATR) | None (trail only) | Swing trades | stdev=0 on bar 1, barely trails early |
| Phased (ATR-SL spec) | Cloud 2→3→4 progression | Phase-based targets | Adaptive to trend strength | Complex, not yet built |

---

## Strategy Position Info

```pinescript
strategy.position_size      // Current position (+ long, - short, 0 flat)
strategy.position_avg_price // Average entry price
strategy.opentrades         // Number of open trades
strategy.closedtrades       // Number of closed trades
strategy.wintrades          // Winning trades count
strategy.losstrades         // Losing trades count
strategy.equity             // Current equity
strategy.netprofit          // Net profit
strategy.grossprofit        // Gross profit
strategy.grossloss          // Gross loss (negative)
strategy.max_drawdown       // Maximum drawdown
```
