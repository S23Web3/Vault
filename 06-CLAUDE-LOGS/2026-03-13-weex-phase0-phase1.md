# Session Log — 2026-03-13 — WEEX Connector Phase 0 + Phase 1

## What Was Done This Session

### Phase 0 (COMPLETE)
- Created WEEX skill scaffold: `C:\Users\User\.claude\skills\weex\SKILL.md`
- Created `.gitignore`: `PROJECTS\weex-connector\.gitignore`
- Created `api_utils.py` scaffold (empty module, py_compile PASS): `PROJECTS\weex-connector\api_utils.py`
- Added WEEX SKILL MANDATORY trigger rule to `CLAUDE.md`

### Phase 1 (COMPLETE)
Scraped WEEX V3 API docs via Playwright MCP. All endpoints documented.

**Output files:**
- `PROJECTS\weex-connector\docs\WEEX-API-COMPLETE-REFERENCE.md` — full reference doc
- `C:\Users\User\.claude\skills\weex\SKILL.md` — updated with all endpoint details

---

## Critical Findings from Phase 1 Docs Scrape

### 1. API Version is V3 (not V2)
- Probe script used V2: `/capi/v2/market/candles` with `cmt_btcusdt` symbols
- Docs confirm V3 is current: `/capi/v3/market/klines` with `BTCUSDT` symbols
- **Both still work but use different symbol formats — use V3 for all new code**

### 2. Symbol Format Mismatch (CRITICAL)
- REST V3 endpoints: `BTCUSDT`
- WS push data (`contractId` field): `cmt_btcusdt`
- Must convert on fill event receipt: strip `cmt_` prefix, uppercase

### 3. Auth: Passphrase IS Required
Headers: `ACCESS-KEY`, `ACCESS-SIGN`, `ACCESS-PASSPHRASE`, `ACCESS-TIMESTAMP`
REST signing algorithm (Bitget standard — verify at Phase 4):
```
signature = base64(hmac_sha256(secret, timestamp + METHOD + path + body))
```
WS signing (explicitly documented):
```
signature = base64(hmac_sha256(secret, timestamp + "/v2/ws/private"))
```

### 4. No TRAILING_STOP_MARKET
Order types: LIMIT, MARKET, STOP, TAKE_PROFIT, STOP_MARKET, TAKE_PROFIT_MARKET only.
TTP must be candle-level engine (same as BingX v1 approach). This is confirmed.

### 5. SL Order Placement
Use `POST /capi/v3/algoOrder` with `type: STOP_MARKET` and `triggerPrice`.
- Field `clientAlgoId` is required (not `newClientOrderId`)
- Separate from the entry order (not inline `slTriggerPrice`)

### 6. Position Mode
- COMBINED = one-way (default) — not suitable for connector
- SEPARATED = hedge mode (LONG/SHORT independent) — what we need
- Set at margin mode change: `separatedType: "SEPARATED"`

### 7. Leverage in Isolated SEPARATED Mode
Must set `isolatedLongLeverage` AND `isolatedShortLeverage` independently.
Both must be passed in the leverage update request.

### 8. Exchange Info Response
Contains `quantityPrecision` (decimal places for quantity) per symbol — use this for step size calculation. No need for separate step size fetch.

### 9. Response Format Inconsistency
- GET endpoints: raw array/object, NO `{code, msg, data}` wrapper
- POST order endpoints: `{orderId, success, errorCode, errorMessage}`
- POST config endpoints: `{code, msg, requestTime}`
- Always check `success: true` field on order responses

### 10. Cancel Conditional Orders
`DELETE /capi/v3/algoOrder?orderId=...` — uses `orderId` (NOT `clientAlgoId`)
Store `orderId` from `algoOrder` response, not just the client ID.

### 11. Close Positions Endpoint
`POST /capi/v3/closePositions` — dedicated endpoint, cleaner than MARKET order with reduceOnly.
Returns `{positionId, success, successOrderId, errorMessage}` per position.

### 12. Commission Rate Endpoint
`GET /capi/v3/account/commissionRate?symbol=BTCUSDT`
Returns `{makerCommissionRate, takerCommissionRate}` as decimals (e.g. `"0.0004"` = 0.04%).
70% rebate account will show effective rate after rebate settled. Fetch at startup.

---

## WebSocket Fill Channel Detail

Subscribe: `{"event": "subscribe", "channel": "fill"}`

Push structure:
```
msg.data.orderFillTransaction[] -> [{orderId, contractId(cmt_ format), positionSide, orderSide, fillSize, fillFee, realizePnl, createdTime}]
```
`realizePnl` is non-zero only on closing trades.

---

## What Was NOT Scraped (Lower Priority)

- Individual Account Channel and Order Channel WS schemas
- Get Account Configuration (symbol-level config)
- Get Account Income (billing history)
- Error codes list
- Historical klines endpoint details
- Public WS channel message schemas

All of these are in the full reference doc (endpoint paths documented, response schemas not scraped).

---

## Phase Status After This Session

| Phase | Status |
|-------|--------|
| Phase 0 | COMPLETE |
| Phase 1 | COMPLETE |
| Phase 2 | NOT STARTED (coin inventory — can do any time) |
| Phase 3 | NOT STARTED (UML — requires Phase 1 complete, now unblocked) |
| Phase 4 | BLOCKED — needs WEEX API keys from user |
| Phase 5-8 | NOT STARTED |

---

## Next Session Start Command

```
/weex
/python
```

Then read:
1. `C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\docs\WEEX-API-COMPLETE-REFERENCE.md`
2. `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-12-weex-connector-build-prompt.md`

**Next step: Phase 2 (coin inventory) OR Phase 3 (UML) — both unblocked.**
Phase 2 script: fetch WEEX contract list, cross-ref with BingX and Bybit data dirs, output CSV.
Phase 3: design WEEX connector UML in `docs/WEEX-CONNECTOR-UML.md`.

Phase 4 (test scripts with real API calls) needs API keys first. Ask user when ready.
