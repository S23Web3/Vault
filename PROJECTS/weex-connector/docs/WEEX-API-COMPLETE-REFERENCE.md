# WEEX Futures API — Complete Reference (V3)
*Scraped 2026-03-12/13 via Playwright from https://www.weex.com/api-doc/contract/*
*Version: V3 (current). Path prefix: /capi/v3/*

---

## Quick Facts

| Item | Value |
|------|-------|
| REST base URL | `https://api-contract.weex.com` |
| WS public | `wss://ws-contract.weex.com/v2/ws/public` |
| WS private | `wss://ws-contract.weex.com/v2/ws/private` |
| Symbol format (REST V3) | `BTCUSDT` (no prefix, uppercase) |
| Symbol format (WS push data) | `cmt_btcusdt` (V2 format — contractId field) |
| Timestamp | Unix milliseconds |
| Auth | Header-based (see Auth section) |
| Passphrase | **YES — required** (like Bitget) |
| Testnet | Unknown — not documented |
| Position modes | COMBINED (one-way) / SEPARATED (hedge) |
| Trailing stop order | **NOT SUPPORTED** — use candle-level TTP engine |

---

## Authentication (REST)

All authenticated endpoints require these HTTP headers:

| Header | Value |
|--------|-------|
| `ACCESS-KEY` | Your API key |
| `ACCESS-SIGN` | HMAC-SHA256 signature (Base64-encoded) |
| `ACCESS-PASSPHRASE` | Your API key passphrase |
| `ACCESS-TIMESTAMP` | Current Unix timestamp in milliseconds |
| `Content-Type` | `application/json` |

### REST Signature Algorithm

Based on Bitget white-label pattern (confirm at runtime):
```
preHashString = ACCESS-TIMESTAMP + HTTP_METHOD.upper() + requestPath + requestBody
signature = base64(hmac_sha256(API_SECRET, preHashString))
```

- `HTTP_METHOD`: `GET`, `POST`, `DELETE` (uppercase)
- `requestPath`: includes query string for GET (e.g. `/capi/v3/account/balance`)
- `requestBody`: JSON string for POST/DELETE with body; empty string `""` for GET
- Timestamp tolerance: expires after 30 seconds

**NOTE**: REST signature algorithm not explicitly documented on scraped pages. Verify empirically: try `timestamp + method + path + body` first (Bitget standard).

---

## Authentication (WebSocket Private)

Private WS connection requires the same headers:

| Header | Value |
|--------|-------|
| `ACCESS-KEY` | Your API key |
| `ACCESS-SIGN` | `base64(hmac_sha256(SECRET, timestamp + "/v2/ws/private"))` |
| `ACCESS-PASSPHRASE` | Your API key passphrase |
| `ACCESS-TIMESTAMP` | Unix milliseconds |

**WS Signature** (explicitly documented):
```
message = str(timestamp_ms) + "/v2/ws/private"
signature = base64.b64encode(hmac.new(secret.encode(), message.encode(), sha256).digest())
```

---

## WebSocket Protocol

### Endpoints
- Public: `wss://ws-contract.weex.com/v2/ws/public`
- Private: `wss://ws-contract.weex.com/v2/ws/private`

### Limits
- 300 connection requests / IP / 5 minutes
- Max 100 concurrent connections per IP
- 240 subscribe operations / hour / connection
- Max 100 channels per connection

### Ping/Pong Heartbeat
Server sends: `{"event": "ping", "time": "1693208170000"}`
Client must respond: `{"event": "pong", "time": "1693208170000"}`
5 missed pongs = server disconnects.

### Subscribe / Unsubscribe
```json
{"event": "subscribe", "channel": "fill"}
{"event": "unsubscribe", "channel": "fill"}
```

---

## Enum Definitions

| Enum | Values |
|------|--------|
| `marginType` | `CROSSED`, `ISOLATED` |
| `separatedType` / `separatedMode` | `COMBINED` (one-way), `SEPARATED` (hedge) |
| `side` | `BUY`, `SELL` |
| `positionSide` | `LONG`, `SHORT` |
| `type` (order) | `LIMIT`, `MARKET` |
| `type` (conditional) | `STOP`, `TAKE_PROFIT`, `STOP_MARKET`, `TAKE_PROFIT_MARKET` |
| `timeInForce` | `GTC`, `IOC`, `FOK`, `POST_ONLY` |
| `status` | `NEW`, `PENDING`, `UNTRIGGERED`, `FILLED`, `CANCELED`, `CANCELING` |
| `workingType` | `CONTRACT_PRICE`, `MARK_PRICE` |

---

## Market API (Public — No Auth)

### GET Server Time
```
GET /capi/v3/market/time
```
Response: `{"serverTime": 1764505776347}`

---

### GET Exchange Information (Contracts List)
```
GET /capi/v3/market/exchangeInfo
GET /capi/v3/market/exchangeInfo?symbol=BTCUSDT
```
Response:
```json
{
  "assets": [{"asset": "USDT", "marginAvailable": true}],
  "symbols": [
    {
      "symbol": "BTCUSDT",
      "baseAsset": "BTC",
      "quoteAsset": "USDT",
      "marginAsset": "USDT",
      "pricePrecision": 1,
      "quantityPrecision": 6,
      "baseAssetPrecision": 3,
      "quotePrecision": 8,
      "contractVal": 0.000001,
      "forwardContractFlag": true,
      "minLeverage": 1,
      "maxLeverage": 408,
      "makerFeeRate": 0,
      "takerFeeRate": 0.001,
      "minOrderSize": 0.0001,
      "maxOrderSize": 10000,
      "maxPositionSize": 20000000,
      "marketOpenLimitSize": 12000
    }
  ]
}
```
Key field for step size: `quantityPrecision` (decimal places for quantity).

---

### GET Kline Data
```
GET /capi/v3/market/klines?symbol=BTCUSDT&interval=5m&limit=1000
```
Parameters:
| Param | Required | Notes |
|-------|----------|-------|
| symbol | Yes | e.g. BTCUSDT |
| interval | Yes | 1m, 5m, 15m, 30m, 1h, 4h, 12h, 1d, 1w |
| limit | No | 1-1000, default 100 |

Response: Array of arrays (oldest first):
```
[
  [open_time_ms, "open", "high", "low", "close", "volume", close_time_ms, "quote_vol", trades, "taker_buy_vol", "taker_buy_quote_vol"],
  ...
]
```
Index mapping:
- `[0]` = open_time (Long, ms)
- `[1]` = open (String)
- `[2]` = high (String)
- `[3]` = low (String)
- `[4]` = close (String)
- `[5]` = volume base asset (String)
- `[6]` = close_time (Long, ms)
- `[7]` = quote_volume (String)
- `[8]` = trade_count (Long)
- `[9]` = taker_buy_base_vol (String)
- `[10]` = taker_buy_quote_vol (String)

---

### GET Symbol Price (Mark / Index)
```
GET /capi/v3/market/symbolPrice?symbol=BTCUSDT&priceType=MARK
```
`priceType`: `INDEX` (default) or `MARK`

Response: `{"symbol": "BTCUSDT", "price": "69348.5", "time": 1764505776890}`

---

### GET Best Bid/Ask
```
GET /capi/v3/market/ticker/bookTicker?symbol=BTCUSDT
```
Response: `[{"symbol", "bidPrice", "bidQty", "askPrice", "askQty", "time"}]`

---

### GET 24hr Ticker Statistics
```
GET /capi/v3/market/ticker/24h?symbol=BTCUSDT
```

---

## Account API (Requires Auth)

### GET Account Balance
```
GET /capi/v3/account/balance
```
Response: Array of asset objects:
```json
[{"asset": "USDT", "balance": "5696.49", "availableBalance": "5413.07", "frozen": "81.28", "unrealizePnl": "-34.55"}]
```

---

### GET Commission Rate
```
GET /capi/v3/account/commissionRate?symbol=BTCUSDT
```
Response: `{"symbol": "BTCUSDT", "makerCommissionRate": "0.0002", "takerCommissionRate": "0.0004"}`

Note: These are per-side rates. RT (round-trip) = rate * 2.

---

### GET All Positions
```
GET /capi/v3/account/position/allPosition
```
Response: Array of position objects:
```json
[{
  "id": 689987235755328154,
  "asset": "USDT",
  "symbol": "BTCUSDT",
  "side": "LONG",
  "marginType": "ISOLATED",
  "separatedMode": "COMBINED",
  "leverage": "20",
  "size": "0.020000",
  "openValue": "1801.07",
  "openFee": "0.707",
  "fundingFee": "1.226",
  "marginSize": "17.15",
  "isolatedMargin": "0",
  "unrealizePnl": "-85.57",
  "liquidatePrice": "0",
  "createdTime": 1764505776347,
  "updatedTime": 1764588886461
}]
```
Key fields: `symbol`, `side` (LONG/SHORT), `size`, `openValue`, `marginSize`, `unrealizePnl`, `leverage`, `marginType`, `separatedMode`.

---

### GET Single Position
```
GET /capi/v3/account/position/singlePosition?symbol=BTCUSDT&positionSide=LONG
```

---

### POST Change Margin Mode
```
POST /capi/v3/account/marginType
Body: {"symbol": "BTCUSDT", "marginType": "ISOLATED", "separatedType": "COMBINED"}
```
Response: `{"code": "200", "msg": "success", "requestTime": 1764505776347}`

---

### POST Update Leverage
```
POST /capi/v3/account/leverage
Body: {"symbol": "BTCUSDT", "marginType": "ISOLATED", "isolatedLongLeverage": "20", "isolatedShortLeverage": "20"}
```
Response: `{"symbol", "marginType", "crossLeverage", "isolatedLongLeverage", "isolatedShortLeverage"}`

Note: Must set both `isolatedLongLeverage` AND `isolatedShortLeverage` for isolated mode. At least one leverage field required.

---

## Trade API (Requires Auth)

### POST Place Order
```
POST /capi/v3/order
```
Body parameters:
| Param | Required | Notes |
|-------|----------|-------|
| symbol | Yes | e.g. BTCUSDT |
| side | Yes | BUY or SELL |
| positionSide | Yes | LONG or SHORT |
| type | Yes | LIMIT or MARKET |
| quantity | Yes | Base asset quantity |
| newClientOrderId | Yes | 1-36 chars, pattern `^[\.A-Z\:/a-z0-9_-]{1,36}$` |
| price | Conditional | Required when type=LIMIT |
| timeInForce | Conditional | Required when type=LIMIT. GTC/IOC/FOK |
| tpTriggerPrice | No | Inline take-profit trigger |
| slTriggerPrice | No | Inline stop-loss trigger |
| TpWorkingType | No | CONTRACT_PRICE or MARK_PRICE (default CONTRACT_PRICE) |
| SlWorkingType | No | CONTRACT_PRICE or MARK_PRICE (default CONTRACT_PRICE) |

Response:
```json
{"orderId": "702345678901234567", "clientOrderId": "my-order-0001", "success": true, "errorCode": "", "errorMessage": ""}
```

---

### DELETE Cancel Order
```
DELETE /capi/v3/order?orderId=702345678901234567
DELETE /capi/v3/order?origClientOrderId=my-order-0001
```
One of `orderId` or `origClientOrderId` required.

Response: `{"orderId", "origClientOrderId", "success", "errorCode", "errorMessage"}`

---

### POST Cancel All Open Orders
```
POST /capi/v3/order/cancelAllOrders
Body: {"symbol": "BTCUSDT"}
```

---

### POST Close Positions
```
POST /capi/v3/closePositions
Body: {"symbol": "BTCUSDT"}   // omit symbol to close ALL positions
```
Response: `[{"positionId", "success", "successOrderId", "errorMessage"}]`

---

### GET Get Order Info
```
GET /capi/v3/order?orderId=702345678901234567
```
Response fields: `orderId`, `clientOrderId`, `symbol`, `side`, `positionSide`, `type`, `status`, `origQty`, `executedQty`, `avgPrice`, `price`, `stopPrice`, `time`, `updateTime`, `timeInForce`, `reduceOnly`, `workingType`.

---

### GET Get Current Open Orders
```
GET /capi/v3/openOrders
GET /capi/v3/openOrders?symbol=BTCUSDT&limit=100&page=0
```
Parameters: `symbol` (optional), `orderId`, `startTime`, `endTime`, `limit` (1-100, default 100), `page` (0-based).
Response: Array of order objects (same schema as Get Order Info).

---

### GET Get Order History
```
GET /capi/v3/order/history
GET /capi/v3/order/history?symbol=BTCUSDT&limit=500&page=0
```
Parameters: `symbol`, `limit` (1-1000, default 500), `startTime`, `endTime` (within 90 days), `page`.
Response: Array of order objects including filled orders with `avgPrice`.

---

### GET Get Trade Details (Fill History)
```
GET /capi/v3/trade
GET /capi/v3/trade?symbol=BTCUSDT&limit=500
```

---

## Conditional Orders API (Requires Auth)

Used for STOP_MARKET SL and TAKE_PROFIT_MARKET TP orders.

### POST Place Conditional Order
```
POST /capi/v3/algoOrder
```
Body parameters:
| Param | Required | Notes |
|-------|----------|-------|
| symbol | Yes | e.g. BTCUSDT |
| side | Yes | BUY or SELL |
| positionSide | Yes | LONG or SHORT |
| type | Yes | STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET |
| quantity | Yes | Base asset quantity |
| triggerPrice | Yes | Trigger price |
| clientAlgoId | Yes | 1-36 chars |
| price | Conditional | Required when type=STOP or TAKE_PROFIT |
| TpWorkingType | No | CONTRACT_PRICE or MARK_PRICE |
| SlWorkingType | No | CONTRACT_PRICE or MARK_PRICE |

Response: Same schema as Place Order.

---

### DELETE Cancel Conditional Order
```
DELETE /capi/v3/algoOrder?orderId=712345678901234567
```
Response: Same schema as Cancel Order.

---

### POST Cancel All Conditional Orders
```
POST /capi/v3/algoOrder/cancelAllOrders
Body: {"symbol": "BTCUSDT"}
```

---

### GET Get Current Conditional Orders
```
GET /capi/v3/algoOpenOrders?symbol=BTCUSDT
```

---

### GET Get Conditional Order History
```
GET /capi/v3/algoOrder/history?symbol=BTCUSDT&limit=100
```

---

### POST Place TP/SL Conditional Orders (Position-level)
```
POST /capi/v3/placeTpSlOrder
```
Body parameters:
| Param | Required | Notes |
|-------|----------|-------|
| symbol | Yes | e.g. BTCUSDT |
| clientAlgoId | Yes | 1-36 chars |
| planType | Yes | TAKE_PROFIT or STOP_LOSS |
| triggerPrice | Yes | Trigger price |
| executePrice | Conditional | Set to "0" for market execution |
| quantity | Yes | Base asset quantity |
| positionSide | Yes | LONG or SHORT |
| triggerPriceType | No | CONTRACT_PRICE or MARK_PRICE (default CONTRACT_PRICE) |

Response: `[{"success", "orderId", "errorCode", "errorMessage"}]`

---

## WebSocket Channels

### Public Channels (`wss://ws-contract.weex.com/v2/ws/public`)

**Market / Ticker Channel**
```json
{"event": "subscribe", "channel": "ticker", "instId": "BTCUSDT"}
```

**Candlestick Channel**
```json
{"event": "subscribe", "channel": "candle5m", "instId": "BTCUSDT"}
```

**Depth Channel**
```json
{"event": "subscribe", "channel": "depth", "instId": "BTCUSDT"}
```

---

### Private Channels (`wss://ws-contract.weex.com/v2/ws/private`)

**Fill Channel (Trade Executions)**
```json
{"event": "subscribe", "channel": "fill"}
```

Subscription confirmation: `{"event": "subscribed", "channel": "fill"}`

Push payload structure:
```json
{
  "type": "trade-event",
  "channel": "fill",
  "event": "payload",
  "msg": {
    "msgEvent": "OrderUpdate",
    "version": 46655,
    "data": {
      "orderFillTransaction": [{
        "id": "617414920887075482",
        "coinId": "USDT",
        "contractId": "cmt_btcusdt",
        "orderId": "617414920861909658",
        "marginMode": "SHARED",
        "separatedMode": "COMBINED",
        "positionSide": "LONG",
        "orderSide": "BUY",
        "fillSize": "0.10000",
        "fillValue": "10381.270000",
        "fillFee": "6.228762",
        "liquidateFee": "0",
        "realizePnl": "0",
        "direction": "TAKER",
        "createdTime": "1747203188154",
        "updatedTime": "1747203188154"
      }]
    },
    "time": 1747203188154
  }
}
```

**CRITICAL**: `contractId` uses V2 `cmt_btcusdt` format, NOT V3 `BTCUSDT`. Must map back to REST symbol when matching fills to positions.

Key fields:
- `orderId` — matches REST orderId
- `positionSide` — LONG or SHORT (UNKNOWN for COMBINED/one-way positions)
- `orderSide` — BUY or SELL
- `fillSize` — quantity filled
- `fillValue` — notional value filled
- `fillFee` — fee paid (positive = paid, negative = rebate)
- `realizePnl` — realized PnL (only present on closing trades; "0" on opening)

**Account Channel**
```json
{"event": "subscribe", "channel": "account"}
```

**Position Channel**
```json
{"event": "subscribe", "channel": "position"}
```

**Order Channel**
```json
{"event": "subscribe", "channel": "order"}
```

---

## Key Architectural Notes

### No Trailing Stop Order
WEEX V3 does NOT have TRAILING_STOP_MARKET. Use candle-level TTP engine (same as BingX v1 approach).

### Symbol Format Mismatch (CRITICAL)
- REST V3 endpoints: `BTCUSDT`
- WS push data (`contractId` field): `cmt_btcusdt`
- Conversion: `cmt_btcusdt` -> strip `cmt_` -> uppercase -> `BTCUSDT`

### Position Mode
Default is COMBINED (one-way). Connector should use SEPARATED (hedge mode) for independent LONG/SHORT positions, same pattern as BingX. Set via `separatedType: "SEPARATED"` in Change Margin Mode.

### Leverage (Isolated Mode)
Must set both `isolatedLongLeverage` AND `isolatedShortLeverage` independently in SEPARATED mode. Pass same value for both if symmetric.

### Order Type for SL
Use `POST /capi/v3/algoOrder` with `type: "STOP_MARKET"` (NOT inline `slTriggerPrice` on the entry order, to allow independent management).

### Response Wrapper Inconsistency
- GET endpoints (market data, positions, balance): raw array or object, NO wrapper
- POST success/action endpoints (margin mode): `{"code": "200", "msg": "success", "requestTime": ...}`
- POST order endpoints: `{"orderId", "success", "errorCode", "errorMessage"}`
- Always check `success: true` on order/algo responses

### Rate Limits
- Public REST: 500 req / 10s
- Authenticated REST: weight-based (see per-endpoint Weight(UID) values)
- WS: 300 connections/IP/5min, 240 ops/hour/connection

---

## Signature Verification Checklist (Phase 4)

At Phase 4 runtime, verify these unknowns:
- [ ] REST signing algorithm: `timestamp + METHOD + path + body` vs other pattern
- [ ] GET requests: include query string in signature path or not
- [ ] SEPARATED mode is available and works as expected for hedge positions
- [ ] Leverage endpoint: can set LONG/SHORT independently in SEPARATED mode
- [ ] contractId format in WS fill events (confirmed `cmt_btcusdt` from docs)
- [ ] Error codes for rate limiting, invalid params, insufficient margin
- [ ] Commission rate for 70% rebate account (expect takerCommissionRate = 0.0008 * 0.3 effective)
