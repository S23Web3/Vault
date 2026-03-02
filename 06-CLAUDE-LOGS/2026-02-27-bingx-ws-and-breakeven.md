# BingX Connector — WS + Breakeven Session
**Date**: 2026-02-27
**Status**: COMPLETE — bot live and stable

---

## Context
Bot went live on $110 real account. 4 SHORT positions open (BEAT, ELSA, VIRTUAL, PENDLE). WS listener was broken. Breakeven raise not yet built.

---

## What Was Built / Fixed

### 1. Stage 2 Filter Bug (four_pillars_v384.py)
`require_stage2` and `rot_level` were missing from `self._params` dict. Stage 2 was silently disabled despite `config.yaml` having `require_stage2: true`. Added both keys to `_params`.

### 2. Breakeven Raise (position_monitor.py + state_manager.py + main.py)
**Trigger**: LONG mark >= entry×1.0016 | SHORT mark <= entry×0.9984 (0.16% = 2× commission RT)
**Sequence**: Cancel open SL → Place STOP_MARKET at entry_price → Update state (`sl_price + be_raised=True`)
**Persistence**: `be_raised` stored in state.json — survives restart
**Alert**: Telegram `<b>BREAKEVEN RAISED</b>` with entry and mark
**New methods**: `_fetch_mark_price_pm`, `_cancel_open_sl_orders`, `_place_be_sl`, `check_breakeven`
**New method**: `update_position(key, updates)` in StateManager
**Wired**: `monitor.check_breakeven()` added to monitor_loop in main.py

### 3. listenKey — Wrong Response Parsing (ws_listener.py)
BingX returns `{"listenKey": "..."}` at top level — no `code/msg/data` wrapper.
Our code was looking at `data["data"]["listenKey"]` which found nothing.
**Fix**: Added `key = data.get("listenKey", "")` as fallback.

### 4. listenKey — Method (ws_listener.py)
API docs say GET, but actual BingX API returns 100400 "use POST" with GET.
Changed `_obtain_listen_key` to use POST. (Previous session.)

### 5. Gzip Decompression (ws_listener.py)
BingX sends binary WebSocket frames compressed with gzip (`0x1f 0x8b` magic bytes).
`json.loads()` was failing with `'utf-8' codec can't decode byte 0x8b`.
**Fix**: Added `import gzip` + `if isinstance(msg, bytes): msg = gzip.decompress(msg).decode("utf-8")` before JSON parsing.

### 6. Ping/Pong Heartbeat (ws_listener.py)
BingX sends application-level text `"Ping"` every 5 seconds expecting `"Pong"` response.
After 5 unanswered Pings, BingX closes connection (`no close frame received or sent`).
**Fix**: Added `if msg == "Ping": await ws.send("Pong"); continue` before JSON parsing.

---

## Live Confirmation

- ELSA-USDT_SHORT: BE triggered at 19:17:08 (mark=0.08418 <= entry×0.9984)
- VIRTUAL-USDT_SHORT: BE triggered at 19:17:10 (mark=0.6871 <= entry×0.9984)
- One position subsequently closed at breakeven SL
- Final state: open=2, WS stable, no errors

---

## API Audit Findings (main.py vs docs)

| Endpoint | Method | Status |
|---|---|---|
| POST /swap/v2/trade/leverage | POST | ✓ |
| POST /swap/v2/trade/marginType | POST | ✓ |
| GET /swap/v2/user/commissionRate | GET | ✓ |
| GET /swap/v2/user/positions | GET | ✓ |
| GET /user/auth/userDataStream | POST (docs=GET, actual=POST) | Fixed |

commissionRate path confirmed: `data["data"]["commission"]["takerCommissionRate"]` ✓
positions fields confirmed: `positionAmt`, `positionSide`, `symbol` ✓

---

## Files Changed This Session

| File | Change |
|---|---|
| `plugins/four_pillars_v384.py` | Added `require_stage2` + `rot_level` to `_params` |
| `state_manager.py` | Added `update_position(key, updates)` |
| `position_monitor.py` | Added BE constants + 4 BE methods + `check_breakeven()` |
| `main.py` | Added `monitor.check_breakeven()` to monitor_loop |
| `ws_listener.py` | listenKey parsing, gzip, Ping/Pong |

All files: py_compile ✓

---

## Next Session: Vince ML
Strategy validation and Vince ML build.
