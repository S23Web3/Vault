# BingX Perpetual Futures API v3 Reference

Compiled 2026-02-25 from: BingX GitHub repos, CCXT source, python-bingx, py-bingx, BingX.Net.
Official docs (JS-rendered): https://bingx-api.github.io/docs-v3/#/en/info

---

## Base URLs

| Environment | URL |
|---|---|
| Live | `https://open-api.bingx.com` |
| Demo (VST) | `https://open-api-vst.bingx.com` |

---

## Authentication / Signature

**Method:** HMAC-SHA256

1. Add `timestamp` parameter (Unix milliseconds)
2. Sort ALL parameters alphabetically by key
3. Build query string: `key1=value1&key2=value2&...`
4. HMAC-SHA256 hex digest of query string using `secretKey`
5. Append `&signature={hexdigest}` to URL

**Header:** `X-BX-APIKEY: {api_key}`

**Auto-added params:** `timestamp` (required), `recvWindow` (optional, default 5000, recommended 10000)

**Public endpoints** do NOT need timestamp, signature, or header.

---

## Enum Values

**OrderSide:** `BUY`, `SELL`

**PositionSide:** `LONG`, `SHORT`, `BOTH` (one-way mode)

**OrderType:** `MARKET`, `LIMIT`, `STOP_MARKET`, `STOP`, `TAKE_PROFIT_MARKET`, `TAKE_PROFIT`, `TRIGGER_LIMIT`, `TRIGGER_MARKET`, `TRAILING_STOP_MARKET`, `TRAILING_TP_SL`

**MarginType:** `ISOLATED`, `CROSSED`

**WorkingType:** `MARK_PRICE`, `CONTRACT_PRICE`, `INDEX_PRICE`

**TimeInForce:** `GTC`, `IOC`, `FOK`, `PostOnly`

**Kline intervals:** `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M`

---

## Response Format (all endpoints)

```json
{"code": 0, "msg": "", "data": { ... }}
```

`code` = 0 means success.

---

## Symbol Format

BingX uses dash-separated: `BTC-USDT`, `ETH-USDT` (NOT `BTCUSDT`).

---

## Endpoint 1: Place Order

**POST** `/openApi/swap/v2/trade/order` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | e.g. `BTC-USDT` |
| `side` | string | YES | `BUY` or `SELL` |
| `positionSide` | string | YES | `LONG`, `SHORT`, or `BOTH` |
| `type` | string | YES | Order type |
| `quantity` | string | YES | Order quantity |
| `price` | string | for LIMIT | Limit price |
| `stopPrice` | float | for STOP/TP | Trigger price |
| `workingType` | string | NO | Default `MARK_PRICE` |
| `timeInForce` | string | NO | Default `GTC` for LIMIT |
| `reduceOnly` | string | NO | `true`/`false` |
| `closePosition` | string | NO | `true`/`false` |
| `clientOrderId` | string | NO | Custom ID |
| `stopLoss` | string(JSON) | NO | SL config as JSON string |
| `takeProfit` | string(JSON) | NO | TP config as JSON string |

### stopLoss / takeProfit JSON format

Passed as **JSON-encoded strings**, not nested objects:

```
stopLoss={"type":"STOP_MARKET","stopPrice":48000,"workingType":"MARK_PRICE"}
takeProfit={"type":"TAKE_PROFIT_MARKET","stopPrice":52000,"workingType":"MARK_PRICE"}
```

**CRITICAL:** `stopPrice` inside the JSON must be a **numeric float**, NOT a string. Sending `"stopPrice":"48000"` causes error 109400 (Mismatch type float64 with value string).

Fields:
- `type` -- `STOP_MARKET` or `TAKE_PROFIT_MARKET` (market trigger) or `STOP`/`TAKE_PROFIT` (limit trigger)
- `stopPrice` -- trigger price (numeric)
- `price` -- limit price (only for limit trigger types)
- `workingType` -- `MARK_PRICE`, `CONTRACT_PRICE`, `INDEX_PRICE`

### Response

```json
{"code": 0, "data": {"order": {"orderId": 123, "symbol": "BTC-USDT", "side": "BUY", "positionSide": "LONG", "type": "MARKET", "quantity": 0.01, "status": "NEW"}}}
```

### Caveat (CCXT Issue #19773)

BingX may silently ignore attached stopLoss/takeProfit on MARKET orders. If response shows `stopLossPrice: None`, SL/TP must be placed as separate orders after fill. **Validated working on VST demo as of 2026-02-25.**

---

## Endpoint 2: Query Positions

**GET** `/openApi/swap/v2/user/positions` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | NO | Filter by symbol |

### Response

```json
{"code": 0, "data": [{"symbol": "BTC-USDT", "positionSide": "LONG", "positionAmt": "0.01", "entryPrice": "50000.0", "markPrice": "50500.0", "unrealizedProfit": "5.0", "liquidationPrice": "45000.0", "leverage": 10, "isolated": true, "initialMargin": "50.0"}]}
```

**IMPORTANT (hedge mode):** `positionAmt` is **always positive** for both LONG and SHORT. Use `positionSide` field to distinguish direction, NOT the sign of `positionAmt`.

---

## Endpoint 3: Query Open Orders

**GET** `/openApi/swap/v2/trade/openOrders` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | NO | Filter by symbol |

### Response

```json
{"code": 0, "data": {"orders": [{"orderId": 123, "symbol": "BTC-USDT", "type": "STOP_MARKET", "stopPrice": "48000.0", "status": "NEW", "workingType": "MARK_PRICE"}]}}
```

---

## Endpoint 4: Cancel Order

**DELETE** `/openApi/swap/v2/trade/order` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | Trading pair |
| `orderId` | int64 | YES | Order ID |

---

## Endpoint 5: Cancel All Orders

**DELETE** `/openApi/swap/v2/trade/allOpenOrders` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | Trading pair |

---

## Endpoint 6: Set Leverage

**POST** `/openApi/swap/v2/trade/leverage` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | Trading pair |
| `side` | string | YES | `LONG` or `SHORT` |
| `leverage` | int | YES | Leverage value |

**GET variant:** Same path, returns `{"longLeverage": 10, "shortLeverage": 10}`

---

## Endpoint 7: Set Margin Type

**POST** `/openApi/swap/v2/trade/marginType` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | Trading pair |
| `marginType` | string | YES | `ISOLATED` or `CROSSED` |

---

## Endpoint 8: Get Mark Price

**GET** `/openApi/swap/v2/quote/price` (public)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | NO | Omit for all symbols |

Note: v1 path `/openApi/swap/v1/ticker/price` is deprecated.

---

## Endpoint 9: Get Klines

**GET** `/openApi/swap/v3/quote/klines` (public)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | Trading pair |
| `interval` | string | YES | Kline interval |
| `startTime` | int64 | NO | Start ms |
| `endTime` | int64 | NO | End ms |
| `limit` | int | NO | Default 500, max 1440 |

Response format may be objects or arrays: `[time, open, close, high, low, volume]`

---

## Endpoint 10: Get Contracts

**GET** `/openApi/swap/v2/quote/contracts` (public)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | NO | Filter to specific symbol |

Key fields: `symbol`, `tradeMinQuantity`, `stepSize`, `pricePrecision`, `quantityPrecision`, `maxLongLeverage`, `maxShortLeverage`

---

## Endpoint 11: Query Single Order

**GET** `/openApi/swap/v2/trade/order` (signed)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | YES | Trading pair |
| `orderId` | int64 | YES | Order ID |

Response includes: `orderId`, `avgPrice`, `executedQty`, `status`, `profit`, `commission`

---

## Additional Endpoints

| Endpoint | Method | Path |
|---|---|---|
| Close All Positions | POST | `/openApi/swap/v2/trade/closeAllPositions` |
| Batch Orders | POST | `/openApi/swap/v2/trade/batchOrders` |
| Batch Cancel | DELETE | `/openApi/swap/v2/trade/batchOrders` |
| Order History | GET | `/openApi/swap/v2/trade/allOrders` |
| Account Balance | GET | `/openApi/swap/v2/user/balance` |
| Funding Rate | GET | `/openApi/swap/v2/quote/premiumIndex` |
| Depth | GET | `/openApi/swap/v2/quote/depth` |
| 24h Ticker | GET | `/openApi/swap/v2/quote/ticker` |
| Position Mode | GET/POST | `/openApi/swap/v2/trade/positionSide/dual` |

---

## Sources

- [BingX-API/BingX-Standard-Contract-doc](https://github.com/BingX-API/BingX-Standard-Contract-doc)
- [CCXT bingx.py](https://github.com/ccxt/ccxt/blob/master/python/ccxt/bingx.py)
- [python-bingx](https://github.com/niewiemczego/python-bingx)
- [CCXT Issue #19773 - SL/TP attachment](https://github.com/ccxt/ccxt/issues/19773)
- [BingX.Net enums](https://github.com/JKorf/BingX.Net)
