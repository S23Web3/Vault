# Plan: BingX Friend Handover Package

**Date:** 2026-02-28
**Goal:** Create a handover package for a friend building a BingX futures trading bot, combining the API v3 reference, hard-won lessons from VST interactions, and architectural patterns.

---

## Output Files

### File 1: `PROJECTS/bingx-connector/docs/BINGX-FRIEND-HANDOVER.md`
The primary handover document. This is the "knowledge layer" the friend gives to their AI — everything a developer needs to avoid the bugs we hit and understand the API quickly.

### File 2: (Already exists) `PROJECTS/bingx-connector/docs/BINGX-API-V3-COMPLETE-REFERENCE.md`
The complete 224-endpoint API scrape. Friend receives this as-is — their AI can use it as a reference.

---

## Handover Document Structure

### 1. Introduction — What You're Getting
- Two files: this guide + raw API reference
- How to use with their AI (paste this doc, reference API doc for endpoints)
- Overview of what to expect building on BingX

### 2. Authentication — Getting Signatures Right
- BingX uses HMAC-SHA256 signed requests
- Parameters: `timestamp` + `recvWindow` required on all signed requests
- **THE #1 BUG**: URL encoding before hashing — must use raw string concat, not `urlencode()`
- `recvWindow: 10000` (10s) on every request to avoid timestamp drift errors
- Code snippet: correct `build_query_string()` implementation

### 3. Critical Gotchas (11 Issues, Ordered by Severity)
Each issue: what it is → how it manifests → the fix

1. Signature URL encoding (CRITICAL — every order fails without this)
2. Commission rate: fetch from API, not hardcode; taker × 2 = round-trip
3. Fill price: use `avgPrice` from order response, not mark price at signal time
4. `recvWindow` missing → random 100400 errors
5. Leverage API: Hedge Mode requires separate LONG + SHORT calls
6. `listenKey`: docs say GET, API requires POST
7. `listenKey` response format: two different structures, need fallback parser
8. WebSocket messages are gzip-compressed (check magic bytes `0x1f8b`)
9. WebSocket heartbeat: text `"Ping"` → echo `"Pong"` (not TCP-level)
10. VST demo API: geoblocked on most datacenters (Indonesian IPs only)
11. Order history purged within seconds of fill (use WS for exit detection, not polling)

### 4. Key Endpoints for a Futures Bot
Curated list (not all 224) — only what a trading bot actually needs:

| Category | Endpoint | Method | Purpose |
|---|---|---|---|
| Setup | `/openApi/swap/v2/trade/leverage` | POST | Set leverage per symbol |
| Setup | `/openApi/swap/v2/trade/marginType` | POST | Set ISOLATED/CROSSED |
| Setup | `/openApi/swap/v2/user/commissionRate` | GET | Fetch taker rate |
| Market | `/openApi/swap/v2/quote/price` | GET | Mark price (for SL calc) |
| Market | `/openApi/swap/v2/quote/klines` | GET | OHLCV bars |
| Market | `/openApi/swap/v2/quote/contracts` | GET | Min step size |
| Orders | `/openApi/swap/v2/trade/order` | POST | Place order (entry + SL/TP) |
| Orders | `/openApi/swap/v2/trade/order` | DELETE | Cancel order |
| Orders | `/openApi/swap/v2/trade/openOrders` | GET | List pending SL/TP |
| Orders | `/openApi/swap/v2/trade/allOrders` | GET | Order history |
| Positions | `/openApi/swap/v2/user/positions` | GET | All open positions |
| WS | `/openApi/user/auth/userDataStream` | POST | Get listenKey |
| WS | `/openApi/user/auth/userDataStream` | PUT | Refresh listenKey (55 min) |
| WS | `/openApi/user/auth/userDataStream` | DELETE | Delete listenKey |

For each: base URL, params, response structure, error codes

### 5. Order Placement — The Full Pattern
How to place an entry + SL + TP in a single request:
- Build `stopLoss` and `takeProfit` as JSON strings in the params
- The JSON objects MUST be inline strings, not nested objects
- Mark price vs. contract price for `workingType`
- Quantity rounding: use `tradeMinQuantity` from contracts endpoint

### 6. WebSocket User Data Stream — Setup Pattern
- POST to get listenKey
- Connect: `wss://open-api-ws.bingx.com/market?listenKey=<key>`
- Listen for `ORDER_TRADE_UPDATE` events
- Refresh listenKey every 55 minutes (PUT endpoint)
- Handle gzip decompression
- Handle Ping → Pong
- Reconnect logic (max 3 attempts, 5s delay)

### 7. Bot Architecture Patterns
Proven dual-thread design that works:
- Thread A (market_loop): fetch OHLCV → signal plugin → risk gate → execute
- Thread B (monitor_loop): poll positions → detect exits → breakeven raise → daily reset
- Shared state: JSON file with threading.Lock + atomic writes (tmp → os.replace)
- Plugin pattern: strategy logic isolated from exchange logic

### 8. Risk Gate — 8 Pre-Trade Checks
The checks that protect your capital:
1. Hard stop flag / daily loss limit
2. Max concurrent positions
3. No duplicate (same symbol + direction)
4. Grade filter (A/B/C)
5. ATR volatility threshold
6. Daily trade count limit
7. Cooldown since last exit on this symbol
8. Session-blocked symbols (error 101209)

### 9. Exit Detection Strategy
Why polling fails and why WebSocket is required:
- Order history purged within seconds → don't rely on `allOrders`
- WS `ORDER_TRADE_UPDATE` with `isReduceOnly=true` + status `FILLED` = clean exit signal
- Extract actual fill price from WS event
- Queue-based: WS thread puts events, monitor thread drains

### 10. State Machine & Recovery
- State stored in `state.json`: positions, daily PnL, halt flag, cooldowns
- Startup reconciliation: compare state vs. exchange, remove phantoms
- Breakeven: raise SL to entry after 0.16% move (covers round-trip commission)
- Daily reset: clear PnL/trade count/halt at fixed UTC hour

### 11. Deployment Checklist
Pre-flight checks before live trading.

---

## Implementation Steps

1. Write `BINGX-FRIEND-HANDOVER.md` (the main file, ~400 lines)
   - Pull auth pattern from executor.py + main.py lessons
   - Pull all gotchas from audit-report.md + session logs
   - Write endpoint table from BINGX-API-V3-COMPLETE-REFERENCE.md (curated)
   - Write architecture section from TRADE-UML-ALL-SCENARIOS.md patterns
   - Write deployment checklist from session knowledge

2. Write vault log copy to `06-CLAUDE-LOGS/plans/2026-02-28-bingx-friend-handover-package.md`
   (identical to plan file, per CLAUDE.md instructions)

---

## Source Files Referenced

| Source File | What to Pull |
|---|---|
| `executor.py` | Auth pattern, fill price logic, SL/TP order structure |
| `ws_listener.py` | WebSocket setup, ping/pong, gzip, listenKey lifecycle |
| `position_monitor.py` | Exit detection, breakeven, daily reset |
| `state_manager.py` | State structure, atomic writes, reconciliation |
| `risk_gate.py` | 8-check pattern |
| `main.py` | Startup sequence, commission fetch, thread setup |
| `docs/BINGX-API-V3-COMPLETE-REFERENCE.md` | Endpoint params, response schemas |
| `docs/TRADE-UML-ALL-SCENARIOS.md` | Architecture diagrams |
| `audit-report.md` | Bug list |
| Session logs | VST gotchas, API quirks |

---

## Verification

After writing:
- Read the output file and verify all 11 gotchas are present
- Verify auth code snippet is correct (raw string concat, not urlencode)
- Verify endpoint table includes all 14 key endpoints
- Verify deployment checklist is present
