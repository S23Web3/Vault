# ATR Stop Loss & Trailing Take Profit - Build Specification

**Version:** 1.0  
**Date:** 2026-02-02  
**Status:** Ready for Claude Code  
**Purpose:** Comprehensive build instructions for Pine Script indicator and n8n workflow

---

## 1. SYSTEM OVERVIEW

### 1.1 Purpose

Automated position management system that:
- Calculates dynamic stop loss from 1-minute ATR
- Calculates trailing stop activation and distance from 5-minute ATR
- Validates momentum before order execution
- Places orders with trailing stop on exchange
- Set and forget - exchange manages trailing after placement

### 1.2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   TRADINGVIEW (Pine Script)                 │
│                                                             │
│  1. Detect entry signal (from Four Pillars or manual)       │
│  2. Calculate 1m ATR (for stop loss)                        │
│  3. Calculate 5m ATR (for trailing activation + distance)   │
│  4. Compute all price levels                                │
│  5. Draw horizontal ray on chart                            │
│  6. Send alert with full payload                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    JSON Alert Payload
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         N8N                                 │
│                                                             │
│  1. Receive webhook                                         │
│  2. Fetch last 3 candles (5m) from exchange API             │
│  3. Calculate average ATR of 3 candles                      │
│  4. VALIDATE: TV ATR >= 75% of average ATR                  │
│  5. If valid → Place order with SL + trailing on exchange   │
│  6. If invalid → Log rejection, no order                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       EXCHANGE                              │
│                                                             │
│  • Order placed with:                                       │
│    - Entry price                                            │
│    - Stop loss price                                        │
│    - Trailing stop activation price                         │
│    - Trailing stop callback amount                          │
│  • Exchange manages trailing automatically                  │
│  • No further action needed from automation                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. PINE SCRIPT INDICATOR SPECIFICATION

### 2.1 Indicator Declaration

```pinescript
//@version=6
indicator("ATR Position Manager", 
    shorttitle="ATR-PM", 
    overlay=true,
    max_lines_count=500,
    max_labels_count=500)
```

### 2.2 Input Parameters

```
GROUP: "ATR Settings"
├── atr_length        : int    : default 14    : "ATR Length"
├── atr_smoothing     : string : default "RMA" : options ["RMA", "SMA", "EMA", "WMA"]
├── sl_multiplier     : float  : default 2.0   : "Stop Loss ATR Multiplier"
├── trail_multiplier  : float  : default 2.0   : "Trailing ATR Multiplier"

GROUP: "Timeframes"
├── tf_trail          : string : default "5"   : "Trailing ATR Timeframe (HTF)"

NOTE: Stop Loss ATR always uses CHART timeframe. Trailing ATR uses next HTF.
      Chart 1m  → SL = 1m ATR,  Trail = 5m ATR
      Chart 5m  → SL = 5m ATR,  Trail = 15m ATR
      Chart 15m → SL = 15m ATR, Trail = 1H ATR

GROUP: "Visuals"
├── show_sl_line      : bool   : default true  : "Show Stop Loss Line"
├── sl_line_color     : color  : default red   : "Stop Loss Line Color"
├── sl_line_style     : string : default "dotted" : options ["solid", "dotted", "dashed"]

GROUP: "Alerts"
├── webhook_secret    : string : default ""    : "Webhook Secret"
├── position_size_usd : float  : default 250   : "Position Size (USD)"
├── leverage          : int    : default 20    : "Leverage"
```

### 2.3 Core Calculations

#### 2.3.1 Multi-Timeframe ATR Function

```
FUNCTION: get_mtf_atr(timeframe, length, smoothing)

INPUT:
  - timeframe: string (e.g., "1", "5", "15")
  - length: int (ATR period)
  - smoothing: string (RMA/SMA/EMA/WMA)

PROCESS:
  1. Use request.security() to fetch HTF data
  2. Calculate True Range: max(high-low, abs(high-close[1]), abs(low-close[1]))
  3. Apply smoothing based on type
  4. Return ATR value

OUTPUT:
  - atr_value: float

IMPORTANT:
  - Use barmerge.gaps_off to prevent gaps
  - Use lookahead_off to prevent repainting
```

#### 2.3.2 Calculate Position Levels

```
FUNCTION: calculate_position_levels(direction, entry_price, atr_1m, atr_5m)

INPUT:
  - direction: string ("LONG" or "SHORT")
  - entry_price: float (current close)
  - atr_1m: float (1-minute ATR value)
  - atr_5m: float (5-minute ATR value)

PROCESS:
  IF direction == "LONG":
    sl_price = entry_price - (atr_1m * sl_multiplier)
    trail_activation = entry_price + (atr_5m * trail_multiplier)
    trail_callback = atr_5m * trail_multiplier
    
  IF direction == "SHORT":
    sl_price = entry_price + (atr_1m * sl_multiplier)
    trail_activation = entry_price - (atr_5m * trail_multiplier)
    trail_callback = atr_5m * trail_multiplier

OUTPUT:
  - sl_price: float
  - trail_activation: float
  - trail_callback: float (always positive, represents distance)
```

### 2.4 Entry Signal Detection

```
OPTION A: Manual Signal (via input)
  - Add input.bool for manual long/short trigger
  - Useful for testing

OPTION B: Integration Point
  - Export function that other indicators can call
  - OR receive signal from external indicator via plot

OPTION C: Built-in Conditions (placeholder)
  - Simple EMA cross for testing purposes
  - Replace with Four Pillars integration later

FOR THIS BUILD: Use Option A + C
  - Manual trigger input for testing
  - Simple EMA cross (9/21) as default signal
  - Easy to replace signal source later
```

### 2.5 Horizontal Ray Drawing

```
WHEN: Entry signal fires

CREATE LINE:
  - Start point: bar_index, sl_price
  - End point: bar_index + 500, sl_price (extends right)
  - Color: sl_line_color (input)
  - Style: line.style_dotted (or from input)
  - Width: 1

CREATE LABEL:
  - Position: bar_index + 5, sl_price
  - Text: "Stop Loss"
  - Style: label.style_none
  - Text color: sl_line_color
  - Text size: size.small

STORAGE:
  - Use var to store line ID
  - Use var to store label ID
  - Delete previous line/label when new signal fires

NO TRAILING VISUAL UPDATE:
  - Line stays at initial SL price
  - Exchange manages actual trailing
  - Keeps indicator simple and performant
```

### 2.6 Alert Payload Structure

```json
{
  "secret": "{{webhook_secret}}",
  "timestamp": "{{timenow}}",
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "direction": "LONG",
  "entry_price": {{close}},
  "atr_1m": {{atr_1m_value}},
  "atr_5m": {{atr_5m_value}},
  "sl_price": {{calculated_sl}},
  "sl_distance": {{atr_1m * multiplier}},
  "trail_activation_price": {{calculated_activation}},
  "trail_callback": {{atr_5m * multiplier}},
  "position_size_usd": {{position_size}},
  "leverage": {{leverage}},
  "timeframe": "{{interval}}"
}
```

### 2.7 Alert Trigger

```
WHEN: Entry signal condition is TRUE

ACTION:
  1. Calculate all levels
  2. Draw/update line and label
  3. Build JSON payload string
  4. Fire alert with alert() function
  5. Use alert.freq_once_per_bar_close to prevent spam
```

---

## 3. N8N WORKFLOW SPECIFICATION

### 3.1 Workflow Structure

```
[Webhook Trigger]
       │
       ▼
[Validate Secret]
       │
       ▼
[Fetch 3 Candles from Exchange]
       │
       ▼
[Calculate 3-Candle Average ATR]
       │
       ▼
[Momentum Validation]
       │
       ├── PASS ──▶ [Place Order on Exchange]
       │                    │
       │                    ▼
       │            [Log Success]
       │                    │
       │                    ▼
       │            [Respond 200 OK]
       │
       └── FAIL ──▶ [Log Rejection]
                           │
                           ▼
                    [Respond 200 OK with rejection reason]
```

### 3.2 Node Specifications

#### Node 1: Webhook Trigger

```
Type: Webhook
Path: tradingview-atr-signal
Method: POST
Response: Using 'Respond to Webhook' Node
Authentication: None (secret validated in next node)
```

#### Node 2: Validate Secret

```
Type: IF
Condition: $json.secret == "YOUR_CONFIGURED_SECRET"

TRUE branch → Continue to fetch
FALSE branch → Respond with error, log attempt
```

#### Node 3: Fetch 3 Candles from Exchange

```
Type: HTTP Request
Method: GET

FOR WEEX (PRIMARY):
URL: https://api.weex.com/api/v1/market/candles
Query Parameters:
  - symbol: {{$json.ticker}}
  - period: 5min
  - limit: 3

FOR BYBIT (SECONDARY):
URL: https://api.bybit.com/v5/market/kline
Query Parameters:
  - category: linear
  - symbol: {{$json.ticker}} (remove .P suffix if present)
  - interval: 5
  - limit: 3

Output: Array of 3 candles with OHLCV data
```

#### Node 4: Calculate 3-Candle Average ATR

```
Type: Code (JavaScript)

INPUT: Array of 3 candles from previous node

LOGIC:
// Calculate True Range for each candle
function calcTR(candle, prevClose) {
  const high = parseFloat(candle.high);
  const low = parseFloat(candle.low);
  const close = parseFloat(candle.close);
  
  if (prevClose === null) {
    return high - low;
  }
  
  return Math.max(
    high - low,
    Math.abs(high - prevClose),
    Math.abs(low - prevClose)
  );
}

// Get candles (newest first from API, reverse for calculation)
const candles = $input.all().reverse();
let trValues = [];
let prevClose = null;

for (const candle of candles) {
  trValues.push(calcTR(candle, prevClose));
  prevClose = parseFloat(candle.close);
}

// Average TR (simple average for 3 candles)
const avgATR = trValues.reduce((a, b) => a + b, 0) / trValues.length;

return {
  avg_atr_5m: avgATR,
  candle_count: candles.length,
  tr_values: trValues
};
```

#### Node 5: Momentum Validation

```
Type: IF

INPUTS:
  - tv_atr: from webhook payload ($json.atr_5m)
  - exchange_avg_atr: from calculation node

CONDITION:
  tv_atr >= (exchange_avg_atr * 0.75)

MEANING:
  - TradingView ATR must be at least 75% of exchange 3-candle average
  - Below 75% = momentum fading, reject trade
  - 75%+ = momentum confirmed, proceed

TRUE branch → Place Order
FALSE branch → Log Rejection
```

#### Node 6: Place Order on Exchange

```
Type: HTTP Request
Method: POST

FOR WEEX (PRIMARY):
URL: https://api.weex.com/api/v1/trade/order
Headers:
  - X-API-KEY: {{$env.WEEX_API_KEY}}
  - X-TIMESTAMP: {{timestamp}}
  - X-SIGN: {{calculated_signature}}

Body:
{
  "symbol": "{{ticker}}",
  "side": "{{direction == 'LONG' ? 'buy' : 'sell'}}",
  "type": "market",
  "quantity": "{{calculate_qty(position_size_usd, leverage, entry_price)}}",
  "stopLoss": "{{sl_price}}",
  "trailingStop": {
    "callbackRate": "{{trail_callback}}",
    "activationPrice": "{{trail_activation_price}}"
  }
}

NOTE: Verify exact WEEX API endpoint and parameters before implementation.
      WEEX API documentation should be consulted for accurate field names.

FOR BYBIT (SECONDARY):
URL: https://api.bybit.com/v5/order/create
Headers:
  - X-BAPI-API-KEY: {{$env.BYBIT_API_KEY}}
  - X-BAPI-TIMESTAMP: {{timestamp}}
  - X-BAPI-SIGN: {{calculated_signature}}

Body:
{
  "category": "linear",
  "symbol": "{{ticker}}",
  "side": "{{direction == 'LONG' ? 'Buy' : 'Sell'}}",
  "orderType": "Market",
  "qty": "{{calculate_qty(position_size_usd, leverage, entry_price)}}",
  "stopLoss": "{{sl_price}}",
  "tpslMode": "Full",
  "slTriggerBy": "LastPrice"
}

THEN: Set Trailing Stop (separate call for Bybit)
URL: https://api.bybit.com/v5/position/trading-stop
Body:
{
  "category": "linear",
  "symbol": "{{ticker}}",
  "trailingStop": "{{trail_callback}}",
  "activePrice": "{{trail_activation_price}}"
}
```

#### Node 7: Log Success/Rejection

```
Type: HTTP Request (to PostgreSQL logger) OR Code node

Log Entry:
{
  "timestamp": "{{$now}}",
  "ticker": "{{ticker}}",
  "direction": "{{direction}}",
  "status": "EXECUTED" or "REJECTED",
  "rejection_reason": "Momentum below threshold" (if rejected),
  "tv_atr": {{tv_atr}},
  "exchange_atr": {{exchange_avg_atr}},
  "atr_ratio": {{tv_atr / exchange_avg_atr}},
  "sl_price": {{sl_price}},
  "trail_activation": {{trail_activation}},
  "trail_callback": {{trail_callback}}
}
```

#### Node 8: Respond to Webhook

```
Type: Respond to Webhook
Response Code: 200
Response Body:
{
  "status": "{{executed or rejected}}",
  "message": "{{description}}",
  "order_id": "{{if executed}}"
}
```

---

## 4. CALCULATION EXAMPLES

### 4.1 LONG Position Example

```
SIGNAL: LONG on GUNUSDT
Entry Price: 0.0300

ATR VALUES (calculated at signal time):
  1m ATR: 0.0003
  5m ATR: 0.0010

CALCULATIONS:
  Stop Loss = 0.0300 - (0.0003 × 2)
            = 0.0300 - 0.0006
            = 0.0294

  Trail Activation = 0.0300 + (0.0010 × 2)
                   = 0.0300 + 0.0020
                   = 0.0320

  Trail Callback = 0.0010 × 2
                 = 0.0020

BEHAVIOR:
  - If price drops to 0.0294 → Stop loss hit, exit
  - If price rises to 0.0320 → Trailing activates
  - At price 0.0320, trailing stop at 0.0320 - 0.0020 = 0.0300 (breakeven)
  - At price 0.0350, trailing stop at 0.0350 - 0.0020 = 0.0330
  - Trail only moves UP (for longs), never down
```

### 4.2 SHORT Position Example

```
SIGNAL: SHORT on BTCUSDT
Entry Price: 45000

ATR VALUES (calculated at signal time):
  1m ATR: 50
  5m ATR: 150

CALCULATIONS:
  Stop Loss = 45000 + (50 × 2)
            = 45000 + 100
            = 45100

  Trail Activation = 45000 - (150 × 2)
                   = 45000 - 300
                   = 44700

  Trail Callback = 150 × 2
                 = 300

BEHAVIOR:
  - If price rises to 45100 → Stop loss hit, exit
  - If price drops to 44700 → Trailing activates
  - At price 44700, trailing stop at 44700 + 300 = 45000 (breakeven)
  - At price 44000, trailing stop at 44000 + 300 = 44300
  - Trail only moves DOWN (for shorts), never up
```

### 4.3 Momentum Validation Example - REJECTED

```
SIGNAL: LONG on ZETAUSDT
TradingView 5m ATR: 0.0025

N8N FETCHES 3 CANDLES (5m):
  Candle 1: H=0.450, L=0.445, C=0.448 → TR=0.005
  Candle 2: H=0.449, L=0.444, C=0.446 → TR=0.005
  Candle 3: H=0.447, L=0.443, C=0.445 → TR=0.004

  Average TR = (0.005 + 0.005 + 0.004) / 3 = 0.00467

VALIDATION:
  Threshold = 0.00467 × 0.75 = 0.0035
  
  TradingView ATR (0.0025) >= Threshold (0.0035)?
  0.0025 >= 0.0035 = FALSE
  
RESULT: REJECTED - Momentum below threshold (ATR declining)
```

### 4.4 Momentum Validation Example - PASSED

```
SIGNAL: LONG on GUNUSDT
TradingView 5m ATR: 0.0042

N8N FETCHES 3 CANDLES (5m):
  Candle 1: H=0.032, L=0.028, C=0.031 → TR=0.004
  Candle 2: H=0.031, L=0.027, C=0.029 → TR=0.004
  Candle 3: H=0.030, L=0.026, C=0.028 → TR=0.004

  Average TR = (0.004 + 0.004 + 0.004) / 3 = 0.004

VALIDATION:
  Threshold = 0.004 × 0.75 = 0.003
  
  TradingView ATR (0.0042) >= Threshold (0.003)?
  0.0042 >= 0.003 = TRUE
  
RESULT: PASSED - Momentum confirmed (ATR expanding)
```

---

## 5. FILE STRUCTURE

### 5.1 Pine Script File

```
Location: C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\
Filename: atr_position_manager_v1.pine
```

### 5.2 N8N Workflow Export

```
Location: [Jacky VPS or local backup]
Filename: atr-position-manager-workflow.json
```

---

## 6. TESTING CHECKLIST

### 6.1 Pine Script Testing

```
[ ] Indicator compiles without errors
[ ] 1m ATR calculation correct (compare to built-in ATR on 1m chart)
[ ] 5m ATR calculation correct (compare to built-in ATR on 5m chart)
[ ] Stop loss line draws at correct price
[ ] Stop loss line is dotted and red
[ ] Label shows "Stop Loss"
[ ] Alert fires on signal
[ ] Alert JSON is valid (test with JSON validator)
[ ] All dynamic values populated correctly in alert
```

### 6.2 N8N Testing

```
[ ] Webhook receives alert from TradingView
[ ] Secret validation works (reject bad secret)
[ ] Exchange API returns 3 candles
[ ] ATR calculation produces reasonable values
[ ] Momentum validation passes when it should
[ ] Momentum validation rejects when it should
[ ] Order placement succeeds (paper trade first)
[ ] Trailing stop configuration correct
[ ] Logging captures all relevant data
[ ] Response sent back to TradingView
```

### 6.3 End-to-End Testing

```
[ ] Create alert on TradingView chart
[ ] Trigger alert manually
[ ] Verify n8n receives and processes
[ ] Verify order appears in exchange (testnet)
[ ] Verify stop loss price correct
[ ] Verify trailing stop activates at correct price
[ ] Verify trailing follows price movement
```

---

## 7. SECURITY NOTES

```
PINE SCRIPT:
  - Webhook secret stored in input (user configurable)
  - Do not hardcode secrets in script

N8N:
  - Exchange API keys in environment variables
  - Webhook secret validated before processing
  - Rate limiting via Nginx (already configured)
  - IP whitelist for TradingView IPs (already configured)

EXCHANGE:
  - Use IP whitelist for API keys
  - Restrict API permissions to trading only (no withdrawal)
```

---

## 8. FUTURE ENHANCEMENTS (NOT IN SCOPE)

```
- Multiple take profit levels (TP1, TP2, TP3)
- Partial position closing
- Break-even move after TP1
- Integration with Four Pillars signals
- Telegram notifications
- Dashboard display
- Position tracking across multiple pairs
- Multi-position handling (add to existing position)
- Visual trailing stop line update on chart
```

---

## 9. DEPENDENCIES

```
PINE SCRIPT:
  - TradingView Pro+ (for webhook alerts)
  - Pine Script v6

N8N:
  - Running on Jacky VPS
  - Nginx reverse proxy (already configured)
  - Exchange API credentials

EXCHANGE:
  - WEEX account (primary)
  - Bybit account (secondary)
  - API key with trading permissions
  - Testnet for initial testing
```

---

**END OF SPECIFICATION**

Ready for Claude Code to build Pine Script indicator.
