# Plan: BingX API Lifecycle Test Script

## Context

The bot has had 8+ bugs discovered during live testing. Each bug requires: fix, restart bot, wait 30+ minutes for a real market signal, discover next bug. 4+ hours wasted on what should be 30-second validations. The root cause: **there is no way to test the full trade lifecycle without waiting for a live signal**.

The existing `test_connection.py` only tests read-only endpoints (klines, price, positions). It never places an order. Every order-related bug (E1-ROOT signature encoding, SL/TP JSON format, quantity precision) is invisible until a real signal fires.

**Solution**: A single script that exercises the ENTIRE trade lifecycle against the real BingX VST (demo) API in ~15 seconds: auth, data, config, order placement with SL, position verification, close, and order query.

## What Gets Built

**One file**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py`

No other files created or modified.

## Design

### Architecture
- Sequential 9-step test, stop on first failure
- Imports `BingXAuth` from `bingx_auth.py` (reuses production signing)
- Does NOT import `Executor` (avoids `StateManager`/`Notifier` coupling) -- calls `BingXAuth` directly with `requests`
- Follows the pattern established by `scripts/test_connection.py` (same `test_step()` harness, same logging, same ROOT/sys.path setup)
- Uses minimum viable quantity (1-2 step sizes, ~$0.02 notional) to conserve demo balance
- Logs to `logs/YYYY-MM-DD-lifecycle-test.log` with UTC+4 timestamps

### The 9 Steps

| Step | Name | What It Tests | API Call | Known Bugs It Would Catch |
|------|------|---------------|----------|--------------------------|
| 1 | Auth check | Credentials, signing, timestamp, recvWindow | `GET /v2/user/positions` (signed) | A1 (missing recvWindow) |
| 2 | Public endpoints | Symbol format, endpoint paths, response parsing | `GET /v3/quote/klines`, `GET /v2/quote/price`, `GET /v2/quote/contracts` | C07 (public signed wrongly), C02 (wrong price endpoint) |
| 3 | Leverage + margin | Parameter enums, POST signing | `POST /v2/trade/leverage` x2, `POST /v2/trade/marginType` | SB1 (wrong side enum) |
| 4 | Quantity calc | Rounding, step size precision | Pure math (no API) | Float precision bugs |
| 5 | Place order with SL | **THE critical test.** Signature on params containing JSON special chars (`{`, `"`, `:`) | `POST /v2/trade/order` with `stopLoss` JSON | E1-ROOT (URL encoding before sign) |
| 6 | Verify position | Position response parsing, direction detection | `GET /v2/user/positions` (signed) | Position matching bugs |
| 7 | Close position | Close-side logic (SELL + positionSide=LONG) | `POST /v2/trade/order` (no SL/TP) | Close direction bugs |
| 8 | Verify closed | Position removal detection | `GET /v2/user/positions` (signed) | State detection bugs |
| 9 | Fetch order details | Order query response format, avgPrice extraction | `GET /v2/trade/order` with orderId | Order query parsing |

### Step 5 Detail (the E1-ROOT reproducer)

This is the most important step. It builds the order params exactly as `executor.py` lines 148-170 do:
```
stopLoss = json.dumps({"type":"STOP_MARKET","stopPrice":"...","workingType":"MARK_PRICE"}, separators=(',',':'))
```
Then passes through `auth.build_signed_request()` which signs the raw query string. If the signing or transport URL-encodes the JSON before signing, BingX returns `100001: Signature verification failed`. This step catches that in 1 second instead of 30+ minutes.

### On Failure: Full Debug Output

Each failed step prints:
- The full request URL (so you can see the exact query string and signature)
- The full response body (so you can see the BingX error code and message)
- Context values (mark price, quantity, step size) relevant to the failure

### CLI Interface
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py" --coin GUN-USDT
```

Default coin: `RIVER-USDT`. Override with `--coin`.

## Key Files Referenced

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx_auth.py` -- imported for `BingXAuth` class (signing)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` -- reference for order param format (lines 148-170)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` -- reference for position parsing (lines 96-113) and order query (lines 59-94)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_connection.py` -- pattern to follow (test_step harness, ROOT setup)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` -- reference for leverage/margin setup (lines 70-104) and UTC+4 logging (lines 32-60)

## Verification

After build:
1. `py_compile` passes (mandatory)
2. Run the script on BingX VST: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py"`
3. All 9 steps PASS = the full trade lifecycle works end-to-end
4. Any FAIL = fix the reported issue, re-run (30 seconds, not 30 minutes)
5. Check log at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\YYYY-MM-DD-lifecycle-test.log`
