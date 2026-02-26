---
name: n8n-workflow-automation
description: n8n workflow automation for trading systems. Webhooks, API integrations, TradingView alerts, exchange connections.
---

# n8n Workflow Automation Skill

## Webhook Setup

### Basic Configuration
- HTTP Method: POST
- Path: Custom (e.g., `tradingview-alert`)
- Respond: "When Last Node Finishes"

### URL Types
- Production: `http://YOUR_IP:5678/webhook/YOUR_PATH` (always active)
- Test: `http://YOUR_IP:5678/webhook-test/YOUR_PATH` (only when listening)

### Security
```javascript
// Header Auth
Authentication: "Header Auth"
Header Name: "X-API-Key"
Header Value: "your_secret"
```

## TradingView Integration

### Alert JSON Format
```json
{
  "ticker": "{{ticker}}",
  "action": "BUY",
  "price": {{close}},
  "timeframe": "{{interval}}",
  "time": "{{timenow}}",
  "position_size": 250,
  "leverage": 20,
  "secret": "YOUR_SECRET"
}
```

### Common Variables
- `{{ticker}}` - Symbol
- `{{exchange}}` - Exchange name
- `{{close}}` - Current price
- `{{interval}}` - Timeframe
- `{{timenow}}` - Timestamp

**NOTE:** `{{strategy.order.action}}` only works in STRATEGIES, not indicators!

## Workflow Patterns

### Pattern 1: Validate → Execute → Notify
```
Webhook → IF (validate) → HTTP Request (exchange) → Telegram
```

### Pattern 2: Error Handling
```
Webhook → Try → HTTP Request → Success
            └─→ Error Handler → Alert
```

## HTTP Request Node

### WEEX API Example
```
Method: POST
URL: https://api.weex.com/v1/order
Headers:
  X-API-KEY: {{$env.WEEX_API_KEY}}
Body:
{
  "symbol": "{{$json.symbol}}",
  "side": "{{$json.action}}",
  "type": "market",
  "quantity": 250
}
```

## Data Transform (Set Node)
```javascript
{
  "symbol": "{{$json.ticker}}",
  "side": "{{$json.action === 'buy' ? 'BUY' : 'SELL'}}",
  "type": "MARKET",
  "quantity": "{{$json.position_size}}"
}
```

## Useful Expressions
```javascript
{{$now}}                    // Current timestamp
{{$json.fieldName}}         // JSON field
{{$env.API_KEY}}            // Environment variable
{{$json.price > 50000 ? 'high' : 'low'}}  // Conditional
```

## Production Checklist
- [ ] Webhook authentication enabled
- [ ] API credentials in environment variables
- [ ] Error handlers on critical nodes
- [ ] Telegram notifications configured
- [ ] Rate limiting (Wait node between API calls)
- [ ] Test with small positions first
