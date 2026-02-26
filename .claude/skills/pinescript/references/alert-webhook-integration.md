# Alert & Webhook Integration for n8n

## TradingView Alert Variables

### Indicator Placeholders
```
{{ticker}}              - Symbol (e.g., BTCUSDT)
{{exchange}}            - Exchange name
{{close}}               - Current close price
{{time}}                - Bar time (Unix timestamp)
{{timenow}}             - Current time (Unix timestamp)
{{interval}}            - Timeframe
```

### Strategy-Only Placeholders
```
{{strategy.order.action}}          - "buy" or "sell"
{{strategy.position_size}}         - Current position size
{{strategy.market_position}}       - "long", "flat", or "short"
```

**CRITICAL:** `{{strategy.order.action}}` only works in STRATEGIES, not indicators!

---

## JSON Alert Templates

### Indicator Alert
```json
{
  "source": "indicator",
  "ticker": "{{ticker}}",
  "timeframe": "{{interval}}",
  "signal": "BUY",
  "price": {{close}},
  "time": "{{timenow}}",
  "stochastics": {
    "9_3": {{plot("stoch_9_3")}},
    "14_3": {{plot("stoch_14_3")}},
    "40_4": {{plot("stoch_40_4")}},
    "60_10": {{plot("stoch_60_10")}}
  },
  "secret": "YOUR_SECRET"
}
```

### Strategy Alert
```json
{
  "source": "strategy",
  "action": "{{strategy.order.action}}",
  "ticker": "{{ticker}}",
  "price": {{close}},
  "position_size": 250,
  "leverage": 20,
  "secret": "YOUR_SECRET"
}
```

---

## Pine Script Alert Implementation

### Using alert() Function
```pinescript
// Build JSON message
buyMessage = '{' +
    '"action": "buy",' +
    '"ticker": "' + syminfo.ticker + '",' +
    '"price": ' + str.tostring(close) +
    '}'

// CRITICAL: Edge-trigger the alert
if buyCondition and not buyCondition[1]
    alert(buyMessage, alert.freq_once_per_bar_close)
```

### Using alertcondition() (Indicators)
```pinescript
// CRITICAL: All alerts must be edge-triggered
alertcondition(signal and not signal[1], "Signal Name", "Description")
```

### Hidden Plots for JSON Values
```pinescript
// Always plot for JSON access, regardless of visibility setting
plot(stoch_9_3, "stoch_9_3", display=display.none)
plot(stoch_14_3, "stoch_14_3", display=display.none)
```

---

## n8n Webhook Configuration

### Webhook Node
```
HTTP Method: POST
Path: /tradingview-alert
Authentication: Header Auth (X-API-Key)
Respond: When Last Node Finishes
```

### Validation IF Node
```javascript
{{$json.secret}} === "YOUR_SECRET" && {{$json.ticker}} && {{$json.action}}
```

### Transform Set Node
```javascript
{
  "symbol": "{{$json.ticker}}",
  "side": "{{$json.action === 'buy' ? 'BUY' : 'SELL'}}",
  "type": "MARKET",
  "quantity": {{$json.position_size}}
}
```

---

## Telegram Notification Format

```
🚀 Trade Executed
━━━━━━━━━━━━━━━
Symbol: {{$json.ticker}}
Action: {{$json.action}}
Price: {{$json.price}}
━━━━━━━━━━━━━━━
Time: {{$now}}
```

---

## Testing Checklist

- [ ] Webhook receives JSON correctly
- [ ] Secret validation works
- [ ] Field transformation correct
- [ ] Exchange API responds successfully
- [ ] Telegram notification sent
- [ ] Error handling catches failures
