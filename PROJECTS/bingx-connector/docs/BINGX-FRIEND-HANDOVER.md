# BingX Futures Bot — Friend Handover Guide

**From:** A friend who already built one of these
**For:** You, starting fresh on BingX perpetual swap API
**How to use:** Give both this file and `BINGX-API-V3-COMPLETE-REFERENCE.md` to your AI. This doc is the knowledge layer (lessons, gotchas, patterns). The API reference is the lookup layer (endpoints, params, responses).

---

## What's In This Package

| File | Purpose |
|---|---|
| `BINGX-FRIEND-HANDOVER.md` | This file — lessons, gotchas, architecture, code patterns |
| `BINGX-API-V3-COMPLETE-REFERENCE.md` | Full 224-endpoint API scrape — use as reference during dev |

---

## Base URLs

```
Live API:  https://open-api.bingx.com
Demo/VST:  https://open-api-vst.bingx.com

Live WS:   wss://open-api-swap.bingx.com/swap-market
Demo WS:   wss://vst-open-api-ws.bingx.com/swap-market
```

> **VST WARNING:** `open-api-vst.bingx.com` resolves to Indonesian IPs and is NOT on CloudFront.
> Most datacenters (AWS, Azure, Hetzner, etc.) get blocked. Run demo bots from a home PC or an
> Indonesian VPS. Live API (`open-api.bingx.com`) is on CloudFront and works from anywhere.

---

## 1. Authentication — Get This Right First

BingX uses HMAC-SHA256 request signing. Every authenticated request needs `timestamp` and `recvWindow`.

### The Correct Implementation

```python
import hashlib
import hmac
import time

def sign_params(params: dict, secret_key: str) -> tuple[str, str]:
    """Sort params alphabetically, build raw query string, sign it."""
    sorted_params = sorted(params.items())

    # CRITICAL: raw string join — NOT urlencode()
    # urlencode() encodes special chars ({, ", :, ,) which breaks the signature
    # when any param contains JSON (stopLoss, takeProfit objects)
    query_string = "&".join(k + "=" + str(v) for k, v in sorted_params)

    signature = hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return query_string, signature

def build_signed_request(method: str, path: str, params: dict,
                          api_key: str, secret_key: str, base_url: str) -> dict:
    """Build a fully signed request ready to fire."""
    params = dict(params)  # don't mutate caller's dict
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"  # 10 seconds — prevents timestamp drift errors

    query_string, signature = sign_params(params, secret_key)
    url = base_url + path + "?" + query_string + "&signature=" + signature
    headers = {"X-BX-APIKEY": api_key}

    return {"url": url, "headers": headers, "method": method}
```

### Public Endpoints (no signature needed)

```python
from urllib.parse import urlencode

def build_public_url(path: str, params: dict, base_url: str) -> str:
    """Public endpoints: no timestamp, no signature, urlencode is fine here."""
    if params:
        query_string = urlencode(sorted(params.items()))
        return base_url + path + "?" + query_string
    return base_url + path
```

**Public endpoints** (no auth): `/quote/price`, `/quote/klines`, `/quote/contracts`, `/quote/depth`
**Signed endpoints** (everything else): account, orders, positions, WebSocket listen key

---

## 2. Critical Gotchas — In Order of Pain

### GOTCHA 1 — Signature: Raw String, NOT urlencode() [BLOCKER]

**What breaks:** Every order placement fails. Leverage and simple requests work by accident (no JSON params), masking the issue until you try to place an order with `stopLoss`/`takeProfit`.

**Why:** BingX signs the raw query string. When your params include JSON:
```
stopLoss={"type":"STOP_MARKET","stopPrice":0.95}
```
`urlencode()` turns `{` into `%7B`, `"` into `%22`, etc. Your signature doesn't match what BingX expects.

**Fix:** See auth implementation above. Use raw string join on sorted params.

---

### GOTCHA 2 — recvWindow: Always Set It [RANDOM FAILURES]

**What breaks:** You get `100400: Invalid timestamp` errors. They start rare, then get more frequent. After ~5 hours everything fails.

**Why:** Without `recvWindow`, BingX defaults to 5 seconds. Clocks drift. Your timestamps eventually fall outside the 5s window.

**Fix:** Always add `"recvWindow": "10000"` (10s) to every signed request. Already in the auth template above.

---

### GOTCHA 3 — Commission: Fetch It, Don't Hardcode [WRONG P&L]

**What breaks:** Your P&L calculations are off. Bot thinks it's profitable when it's not (or vice versa).

**BingX taker rate:** `0.0016` per side (but can vary per account/VIP level)

**Fix:**
```python
# Fetch at startup
GET /openApi/swap/v2/user/commissionRate

# Response path
rate = data["data"]["commission"]["takerCommissionRate"]  # e.g. 0.0008

# Every trade costs BOTH open and close commission
round_trip_commission_rate = rate * 2  # e.g. 0.0016

# Per-trade cost
commission_usd = notional * (rate * 2)
```

---

### GOTCHA 4 — Fill Price: Use avgPrice, Not Mark Price [WRONG SL DISTANCE]

**What breaks:** Your SL is placed relative to the wrong price. On fast-moving coins the mark price when your signal fires can differ 1-4% from the actual fill price.

**Why:** Signal fires on closed bar → you read mark price → you place order → 100-200ms pass → order fills at market → actual fill is `avgPrice` in the response.

**Fix:**
```python
result = requests.post(order_url, headers=headers, timeout=10)
order_data = result.json().get("data", {})

# Use this — the actual fill price
fill_price = float(order_data.get("avgPrice", 0) or 0)

# NOT this — the price you used to calculate quantity
entry_price = fill_price if fill_price > 0 else mark_price_at_signal
```

---

### GOTCHA 5 — Leverage API: Hedge Mode Needs LONG + SHORT Separate Calls [ACCOUNT SETUP]

**What breaks:** `POST /openApi/swap/v2/trade/leverage` with `side=BOTH` returns an error on demo accounts. Demo accounts (VST) are in Hedge Mode by default.

**Fix:**
```python
for side in ("LONG", "SHORT"):
    params = {
        "symbol": symbol,
        "side": side,          # Must be "LONG" or "SHORT", not "BOTH"
        "leverage": str(leverage),
    }
    # ... call the leverage endpoint
```

Live accounts may be in One-Way mode where `side=BOTH` works. Check account settings. In Hedge Mode, positions are tracked separately per direction, so you can simultaneously hold a LONG and SHORT on the same symbol.

---

### GOTCHA 6 — listenKey Endpoint: Docs Say GET, API Requires POST [WS SETUP]

**What breaks:** WebSocket connection never gets a valid `listenKey`. API returns `100400`.

**Official docs say:** `GET /openApi/user/auth/userDataStream`
**Reality:** Use `POST` — the GET method returns an error.

```python
# WRONG (what docs say)
resp = requests.get(url, headers=headers)

# CORRECT
resp = requests.post(url, headers=headers)
```

---

### GOTCHA 7 — listenKey Response Format: Two Different Structures [WS PARSING]

**What breaks:** Your code extracts `None` for the listen key and WS fails silently.

**BingX returns different formats in different contexts:**
```json
// Format A (most common)
{"code": 0, "data": {"listenKey": "abc123..."}}

// Format B (sometimes)
{"code": 0, "listenKey": "abc123..."}

// Format C (rare)
{"code": 0, "data": "abc123..."}
```

**Fix:**
```python
def parse_listen_key(response_data: dict) -> str:
    """Handle all listenKey response formats."""
    data = response_data.get("data", {})

    # Try nested dict first
    if isinstance(data, dict):
        key = data.get("listenKey", "")
        if key:
            return key

    # Try data as bare string
    if isinstance(data, str) and data:
        return data

    # Try top-level
    return response_data.get("listenKey", "")
```

---

### GOTCHA 8 — WebSocket Messages: Gzip-Compressed [PARSE ERROR]

**What breaks:** `json.loads()` fails with `'utf-8' codec can't decode byte 0x8b`.

**Why:** BingX sends binary frames compressed with gzip. Magic bytes `\x1f\x8b` identify gzip.

**Fix:**
```python
import gzip

async def handle_message(msg):
    if isinstance(msg, bytes):
        msg = gzip.decompress(msg).decode("utf-8")

    data = json.loads(msg)
    # ... process
```

---

### GOTCHA 9 — WebSocket Heartbeat: Application-Level Ping/Pong [CONNECTION DROPS]

**What breaks:** WebSocket connection drops after ~25 seconds with `no close frame received`.

**Why:** BingX sends text string `"Ping"` every 5 seconds. You must echo `"Pong"` within 5 pings (25 seconds) or the server closes the connection. This is NOT the standard WebSocket protocol-level ping.

**Fix:**
```python
if isinstance(msg, bytes):
    msg = gzip.decompress(msg).decode("utf-8")

if msg == "Ping":
    await ws.send("Pong")
    continue  # Don't try to parse as JSON

data = json.loads(msg)
```

---

### GOTCHA 10 — Order History Purges Within Seconds [EXIT DETECTION]

**What breaks:** You poll `GET /openApi/swap/v2/trade/allOrders` right after a position closes. API returns nothing. You can't determine if it was a TP or SL hit.

**Why:** BingX purges recent filled orders from the history endpoint very quickly (seconds, not minutes).

**Fix:** Use the WebSocket `ORDER_TRADE_UPDATE` event for exit detection. Parse fills in real-time instead of querying history. See Section 7 for the full pattern.

---

### GOTCHA 11 — Per-Coin Position Limits (Error 101209) [LIVE TRADING]

**What breaks:** Order rejected with `101209: max position value for this leverage is X USDT`.

**Why:** BingX has per-coin position limits that aren't documented in the API reference. They vary by coin and leverage level.

**Fix pattern:**
```python
if error_code == 101209:
    # Try halved quantity once
    halved_qty = round_down(original_qty / 2, step_size)
    if halved_qty > 0:
        retry_order(halved_qty)
    else:
        # Mark symbol as blocked for this session
        session_blocked.add(symbol)
```

---

## 3. Key Endpoints — What a Futures Bot Actually Needs

From the 224 endpoints in the reference, these are the ones you'll actually use:

### Base URLs
```
All REST calls: https://open-api.bingx.com (live) / https://open-api-vst.bingx.com (demo)
```

### Account Setup (run at startup)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/openApi/swap/v2/trade/leverage` | POST | Signed | Set leverage per symbol per side |
| `/openApi/swap/v2/trade/marginType` | POST | Signed | Set ISOLATED or CROSS margin |
| `/openApi/swap/v2/user/commissionRate` | GET | Signed | Fetch taker commission rate |

**Leverage params:** `symbol`, `side` (LONG/SHORT), `leverage`
**Margin params:** `symbol`, `marginType` (ISOLATED/CROSSED)

---

### Market Data (public, no auth)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/openApi/swap/v2/quote/price` | GET | None | Mark price for a symbol |
| `/openApi/swap/v2/quote/klines` | GET | None | OHLCV candles |
| `/openApi/swap/v2/quote/contracts` | GET | None | Contract specs incl. min step size |

**Price params:** `symbol`
**Price response:** `data.price` (dict) or `data[0].price` (list — handle both)

**Klines params:** `symbol`, `interval` (1m/5m/15m/1h/4h/1d), `limit`
**Klines response:** `data` array of `[timestamp, open, high, low, close, volume]`

**Contracts response:** Array of objects. Per symbol, get `tradeMinQuantity` for min order size (also `stepSize` as fallback).

---

### Order Management

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/openApi/swap/v2/trade/order` | POST | Signed | Place order (entry + optional SL/TP) |
| `/openApi/swap/v2/trade/order` | DELETE | Signed | Cancel an open order |
| `/openApi/swap/v2/trade/openOrders` | GET | Signed | List all pending orders for symbol |
| `/openApi/swap/v2/trade/allOrders` | GET | Signed | Order history (purges fast — see Gotcha 10) |

---

### Position Management

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/openApi/swap/v2/user/positions` | GET | Signed | All open positions |

**Positions response:** Array with `symbol`, `positionSide` (LONG/SHORT), `positionAmt`, `entryPrice`, `unrealizedProfit`, `leverage`

---

### WebSocket Stream

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/openApi/user/auth/userDataStream` | POST | Signed | Obtain listenKey |
| `/openApi/user/auth/userDataStream` | PUT | Signed | Refresh listenKey validity (+60 min) |
| `/openApi/user/auth/userDataStream` | DELETE | Signed | Delete listenKey on shutdown |

> **Note:** All three use the same path. Refresh every 55 minutes to stay ahead of the 60-minute expiry.

---

## 4. Order Placement — The Full Pattern

BingX allows attaching `stopLoss` and `takeProfit` to the entry order in a single call. The SL/TP must be serialized as JSON **strings** in the params (not nested objects).

```python
import json

def place_entry_with_sl_tp(auth, symbol, direction, quantity, sl_price, tp_price=None):
    """Place a market entry order with SL (and optional TP) attached."""
    side = "BUY" if direction == "LONG" else "SELL"
    position_side = direction  # "LONG" or "SHORT"

    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": position_side,
        "type": "MARKET",
        "quantity": str(quantity),
    }

    # SL as JSON string — MARK_PRICE avoids wick-triggered exits
    sl_obj = {
        "type": "STOP_MARKET",
        "stopPrice": sl_price,
        "workingType": "MARK_PRICE",  # or "CONTRACT_PRICE"
    }
    params["stopLoss"] = json.dumps(sl_obj, separators=(',', ':'))

    # TP (optional) as JSON string
    if tp_price is not None:
        tp_obj = {
            "type": "TAKE_PROFIT_MARKET",
            "stopPrice": tp_price,
            "workingType": "MARK_PRICE",
        }
        params["takeProfit"] = json.dumps(tp_obj, separators=(',', ':'))

    req = build_signed_request("POST", "/openApi/swap/v2/trade/order", params, ...)
    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    return resp.json()
```

### SL Direction Validation (do this before sending)

```python
if direction == "LONG" and sl_price >= mark_price:
    raise ValueError(f"LONG SL must be BELOW entry. sl={sl_price} mark={mark_price}")
if direction == "SHORT" and sl_price <= mark_price:
    raise ValueError(f"SHORT SL must be ABOVE entry. sl={sl_price} mark={mark_price}")
```

### Quantity Calculation

```python
import math

def calculate_quantity(notional_usd: float, mark_price: float, step_size: float) -> float:
    """Calculate order quantity rounded DOWN to step_size."""
    raw_qty = notional_usd / mark_price
    if step_size <= 0:
        return raw_qty
    return math.floor(raw_qty / step_size) * step_size
```

`step_size` comes from `tradeMinQuantity` in `/openApi/swap/v2/quote/contracts`. Always round DOWN — rounding up can exceed your notional by a step.

### Order Response

```python
result = resp.json()
if result.get("code", 0) != 0:
    print(f"Order failed: {result['code']} {result.get('msg')}")
    return

order_data = result.get("data", {})
order_id = order_data.get("orderId") or order_data.get("order", {}).get("orderId")
fill_price = float(order_data.get("avgPrice", 0) or 0)  # actual fill (see Gotcha 4)
```

---

## 5. WebSocket User Data Stream — Full Setup Pattern

```python
import asyncio
import gzip
import json
import time
import threading
import websockets
import requests

LISTEN_KEY_PATH = "/openApi/user/auth/userDataStream"
REFRESH_INTERVAL = 55 * 60  # 55 minutes

def obtain_listen_key(auth) -> str:
    """POST to get a new listenKey."""
    req = build_signed_request("POST", LISTEN_KEY_PATH, {}, ...)
    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()
    if data.get("code", 0) != 0:
        raise RuntimeError(f"listenKey error: {data}")
    return parse_listen_key(data)  # use the multi-format parser from Gotcha 7

def refresh_listen_key(auth, key: str):
    """PUT to extend listenKey by another 60 min."""
    req = build_signed_request("PUT", LISTEN_KEY_PATH, {"listenKey": key}, ...)
    requests.put(req["url"], headers=req["headers"], timeout=10)

async def ws_loop(base_ws_url, auth, fill_queue):
    """Main WebSocket event loop."""
    listen_key = obtain_listen_key(auth)
    ws_url = base_ws_url + "?listenKey=" + listen_key

    async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
        last_refresh = time.time()
        async for msg in ws:
            # Decompress
            if isinstance(msg, bytes):
                msg = gzip.decompress(msg).decode("utf-8")

            # Application-level heartbeat (Gotcha 9)
            if msg == "Ping":
                await ws.send("Pong")
                continue

            # Refresh key before it expires (Gotcha — do this)
            if time.time() - last_refresh > REFRESH_INTERVAL:
                refresh_listen_key(auth, listen_key)
                last_refresh = time.time()

            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue

            # Parse fill events (see Section 6)
            event = parse_order_fill(data)
            if event:
                fill_queue.put(event)
```

### ORDER_TRADE_UPDATE Event Structure

```python
def parse_order_fill(msg_data: dict) -> dict | None:
    """Extract fill info from ORDER_TRADE_UPDATE event."""
    if msg_data.get("e") != "ORDER_TRADE_UPDATE":
        return None

    order = msg_data.get("o", {})

    if order.get("X") != "FILLED":  # X = order status
        return None

    order_type = order.get("o", "")  # o = order type
    if "TAKE_PROFIT" in order_type:
        reason = "TP_HIT"
    elif "STOP" in order_type:
        reason = "SL_HIT"
    else:
        return None  # Not a exit order

    return {
        "symbol": order.get("s"),           # s = symbol
        "position_side": order.get("ps"),    # ps = LONG or SHORT
        "avg_price": float(order.get("ap", 0) or 0),  # ap = avg price
        "realized_pnl": float(order.get("rp", 0) or 0),  # rp = realized PnL
        "fee": float(order.get("n", 0) or 0),  # n = fee amount
        "reason": reason,
    }
```

---

## 6. Bot Architecture — The Pattern That Works

### Dual-Thread Design

```
Thread A — MarketLoop (daemon):
  while running:
    fetch OHLCV for all coins (klines endpoint)
    detect new bar close
    feed to strategy plugin → get signal
    pass signal through risk gate
    if approved → execute order
    sleep(poll_interval)

Thread B — MonitorLoop (daemon):
  while running:
    drain WebSocket fill queue (instant exit detection)
    poll open positions from exchange
    detect closed positions vs local state
    if closed → record exit, update P&L
    check breakeven trigger on each open position
    check daily reset (at fixed UTC hour)
    sleep(check_interval)

Thread C — WSListener (daemon):
  asyncio loop:
    obtain listenKey
    connect to WebSocket
    listen for ORDER_TRADE_UPDATE events
    push fills to queue (thread-safe)
    refresh listenKey every 55 min
    reconnect on error
```

### Shared State — Thread-Safe Pattern

```python
import json
import os
import threading
from pathlib import Path

class StateManager:
    def __init__(self, state_path):
        self._path = Path(state_path)
        self._lock = threading.Lock()
        self._state = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            with open(self._path) as f:
                return json.load(f)
        return {"open_positions": {}, "daily_pnl": 0.0,
                "daily_trades": 0, "halt_flag": False}

    def _save(self):
        """Atomic write: write to tmp then replace."""
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2)
        os.replace(tmp, self._path)  # atomic on same filesystem

    def get_snapshot(self) -> dict:
        with self._lock:
            return dict(self._state)  # return copy

    def record_position(self, key, position):
        with self._lock:
            self._state["open_positions"][key] = position
            self._state["daily_trades"] += 1
            self._save()

    def close_position(self, key, exit_price, reason):
        with self._lock:
            pos = self._state["open_positions"].pop(key, None)
            if pos:
                # ... calculate PnL, update daily_pnl
                self._save()
```

**Why atomic writes:** If the bot crashes mid-write, `state.json` won't be corrupted. The OS `replace()` call is atomic on the same filesystem.

### Plugin Pattern (Strategy Isolation)

Keep your strategy logic completely separate from exchange code:

```python
# plugins/my_strategy.py
class MyStrategy:
    def __init__(self, config):
        self.config = config

    def get_signal(self, symbol, ohlcv_df) -> Signal | None:
        """Return a Signal or None. Never call exchange APIs here."""
        # ... your logic
        return Signal(direction="LONG", grade="A", sl_price=..., tp_price=..., atr=...)

# signal_engine.py
import importlib
plugin_module = importlib.import_module(f"plugins.{plugin_name}")
plugin_class = getattr(plugin_module, "Strategy")  # or look up by convention
self.plugin = plugin_class(config)
```

---

## 7. Exit Detection — Why WebSocket, Not Polling

### The Polling Approach (Fails)

```
60s poll cycle:
  GET /openApi/swap/v2/user/positions → check if BTC-USDT LONG still there
  If gone → check allOrders → find the filled STOP/TP
  Problem: allOrders may already be empty (Gotcha 10)
  Result: EXIT_UNKNOWN — you know position closed but not why
```

### The WS Approach (Works)

```
Real-time:
  ORDER_TRADE_UPDATE event → FILLED + STOP_MARKET → SL_HIT, price=X
  ORDER_TRADE_UPDATE event → FILLED + TAKE_PROFIT_MARKET → TP_HIT, price=X

60s poll cycle:
  GET /openApi/swap/v2/user/positions → drain WS queue first
  WS queue catch: many exits detected already
  Polling catches: positions that missed WS (e.g. WS reconnecting)
```

**Queue-based integration:**
```python
fill_queue = queue.Queue()     # Thread-safe

# WSListener thread:
fill_queue.put(fill_event)

# MonitorLoop thread:
while not fill_queue.empty():
    event = fill_queue.get_nowait()
    handle_exit(event["symbol"], event["position_side"],
                 event["avg_price"], event["reason"])
```

---

## 8. Risk Gate — 8 Pre-Trade Checks

Run these in order before every order. Short-circuit on first fail.

```python
def should_trade(signal, symbol, state, config) -> tuple[bool, str]:
    """Returns (approved, reason)."""

    # 1. Hard stop: check state, not just config
    if state["halt_flag"] or state["daily_pnl"] <= -config["daily_loss_limit"]:
        return False, "HARD_STOP"

    # 2. Max concurrent positions
    if len(state["open_positions"]) >= config["max_positions"]:
        return False, "MAX_POSITIONS"

    # 3. No duplicate on same symbol + direction
    key = f"{symbol}_{signal.direction}"
    if key in state["open_positions"]:
        return False, "DUPLICATE"

    # 4. Grade filter — from strategy config, not risk config
    if signal.grade not in strategy_config["allowed_grades"]:
        return False, f"GRADE_FILTERED ({signal.grade})"

    # 5. Minimum volatility gate
    atr_ratio = signal.atr / signal.entry_price
    if atr_ratio < config["min_atr_ratio"]:
        return False, f"TOO_QUIET (atr_ratio={atr_ratio:.5f})"

    # 6. Daily trade limit
    if state["daily_trades"] >= config["max_daily_trades"]:
        return False, "TRADE_LIMIT"

    # 7. Cooldown since last exit on this symbol+direction
    last_exit = get_last_exit_time(key)
    if last_exit:
        elapsed = (datetime.utcnow() - last_exit).total_seconds()
        cooldown_sec = config["cooldown_bars"] * config["bar_duration_sec"]
        if elapsed < cooldown_sec:
            return False, f"COOLDOWN ({elapsed:.0f}s / {cooldown_sec}s)"

    # 8. Session-blocked (symbol hit error 101209 this session)
    if symbol in session_blocked:
        return False, "SESSION_BLOCKED"

    return True, "APPROVED"
```

> **Bug to avoid:** The `halt_flag` check (#1) must read from `state` (the live state dict), not from config. Config doesn't have halt_flag. Halt gets set at runtime when loss limit is breached.

> **Bug to avoid:** `allowed_grades` (#4) should come from your strategy/plugin config, not the risk config. The strategy knows what grades it generates; the risk gate just filters.

---

## 9. Breakeven Logic

Raise your SL to entry after the position moves far enough to cover round-trip commission.

```
Round-trip commission = taker_rate * 2 = 0.0016 (at 0.08% per side)
Breakeven trigger = entry * (1 + commission_rate)  = entry * 1.0016 for LONG
                                                     = entry * (2 - 1.0016) for SHORT
```

**Implementation:**
```python
BE_MULTIPLIER = 1.0016  # 0.16% = 2x commission at 0.08% taker

def check_breakeven(position, mark_price, auth, state):
    if position.get("be_raised"):
        return  # Already raised, skip

    entry = position["entry_price"]

    if position["direction"] == "LONG":
        triggered = mark_price >= entry * BE_MULTIPLIER
    else:  # SHORT
        triggered = mark_price <= entry * (2.0 - BE_MULTIPLIER)

    if triggered:
        # Cancel existing SL order
        cancel_order(position["sl_order_id"])

        # Place new SL at entry price
        new_sl = entry
        place_sl_order(position["symbol"], position["direction"], new_sl)

        # Mark as raised (persist to state.json)
        position["be_raised"] = True
        state.update_position(position)
```

---

## 10. Startup Sequence & State Reconciliation

When the bot restarts, it may have open positions from before the crash. Always reconcile.

```python
def reconcile_state(auth, state_manager):
    """Remove phantom positions from local state that no longer exist on exchange."""
    req = build_signed_request("GET", "/openApi/swap/v2/user/positions", {}, ...)
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    # CRITICAL: If API returns an error, don't wipe state
    if data.get("code", 0) != 0:
        logger.error("Reconcile failed — keeping local state")
        return

    live_positions = {
        f"{p['symbol']}_{p['positionSide']}": p
        for p in data.get("data", [])
        if float(p.get("positionAmt", 0)) != 0  # filter empty slots
    }

    local_positions = state_manager.get_open_positions()

    for key in list(local_positions.keys()):
        if key not in live_positions:
            logger.warning("Phantom position removed: %s", key)
            state_manager.remove_position(key)
```

**Startup order:**
1. Load config
2. Initialize auth (API keys from `.env`)
3. Initialize Telegram notifier
4. Load state from `state.json`
5. Set leverage and margin for all symbols (throttle 200ms between coins)
6. Fetch commission rate from API
7. Reconcile state vs. exchange
8. Warm up market data (fill OHLCV buffer)
9. Start WebSocket listener thread
10. Start market loop thread + monitor loop thread
11. Send "Bot Started" Telegram message

---

## 11. Configuration Reference

Here's the shape of a working config:

```yaml
connector:
  demo_mode: true              # true = VST demo, false = live
  timeframe: "5m"              # signal bar size
  ohlcv_buffer_bars: 201       # warmup bars (must be > strategy lookback)
  poll_interval_sec: 45        # how often to fetch new bars (for N coins, needs headroom)
  position_check_sec: 60       # how often to poll positions

strategy:
  plugin: "my_strategy"        # filename in plugins/ (without .py)

risk:
  max_positions: 5             # max concurrent open trades
  max_daily_trades: 30         # hard stop if we open this many in a day
  daily_loss_limit_usd: 50.0   # halt trading if daily PnL crosses this (negative)
  min_atr_ratio: 0.003         # minimum ATR/price ratio (skip choppy coins)
  cooldown_bars: 3             # bars to wait after exit before re-entering same symbol
  bar_duration_sec: 300        # seconds per bar (5m = 300, 1h = 3600)

position:
  margin_usd: 10.0             # USD per trade (margin, not notional)
  leverage: 10                 # leverage multiplier
  margin_mode: "ISOLATED"      # ISOLATED (recommended) or CROSSED
  sl_working_type: "MARK_PRICE" # MARK_PRICE avoids wick-triggered SLs

notification:
  daily_summary_utc_hour: 17   # hour to send daily P&L summary

coins:
  - BTC-USDT
  - ETH-USDT
  # ... etc
```

---

## 12. Environment Variables

```bash
# .env (never commit this)
BINGX_API_KEY=your_api_key_here
BINGX_SECRET_KEY=your_secret_key_here
TELEGRAM_BOT_TOKEN=123456789:ABCdef...   # from @BotFather
TELEGRAM_CHAT_ID=987654321               # your personal chat ID
```

Get your Telegram chat ID: message your bot, then hit:
`https://api.telegram.org/bot{TOKEN}/getUpdates`

---

## 13. Deployment Checklist

### Before Running on Live Account

- [ ] Auth test: `GET /openApi/swap/v2/user/commissionRate` returns your rate (not an error)
- [ ] Signature test: Set leverage on one coin — `POST /openApi/swap/v2/trade/leverage` returns code 0
- [ ] Commission rate is fetched dynamically, not hardcoded
- [ ] Order placement: verify `avgPrice` is extracted from response (not mark price calc)
- [ ] WS heartbeat: run for 30 min, confirm no connection drops with Ping/Pong logged
- [ ] WS gzip: confirm your message handler doesn't crash on binary messages
- [ ] listenKey refresh scheduled at 55-minute interval
- [ ] State file loads cleanly on restart (no crash on missing keys)
- [ ] Reconciliation runs at startup (phantom positions handled, API errors don't wipe state)
- [ ] SL direction validation active (prevents placing SL on wrong side)
- [ ] Error 101209 handled (halve qty + session block)
- [ ] Daily reset logic tested (P&L and trade count reset at correct UTC hour)
- [ ] Telegram alerts working (entry, exit, error, daily summary)

### Run First On Demo/VST

1. Start with `demo_mode: true` and `max_positions: 1`
2. Let run for 1+ week — watch EXIT_UNKNOWN rate (should be < 5%)
3. Check that commission math produces realistic P&L
4. Verify SL/TP orders appear in account after entry
5. Confirm breakeven raises correctly after 0.16% move
6. Then switch to live with same settings

---

## 14. Common Error Codes

| Code | Meaning | Fix |
|---|---|---|
| `100400` | Timestamp out of range | Add `recvWindow: 10000` |
| `100412` | Signature mismatch | Fix auth (raw string join, not urlencode) |
| `100001` | Required parameter missing | Check all required params sent |
| `101209` | Position value limit exceeded | Halve quantity, retry once, then session-block |
| `80001` | Too many requests | Add rate-limiting / backoff |
| `101204` | Insufficient margin | Account needs more funds |
| `101400` | Order price invalid | SL/TP price outside valid range |

---

Good luck with the build. The hard part is the auth signature and the exit detection — once those two work cleanly, everything else is plumbing.
