# Session Log: Lifecycle Test Build + stopPrice Bug (2026-02-25)

## What Was Built
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py` — 15-step API lifecycle test
- Exercises FULL trade lifecycle against BingX VST in ~40 seconds, no signal wait needed
- Steps: auth -> public endpoints -> leverage/margin -> qty calc -> LONG entry+SL+TP -> verify -> query pending orders -> raise SL -> trail TP -> close -> verify -> SHORT cycle -> multi-position -> limit order -> order query

## Bug Found: stopPrice String vs Float (E2-STOPPRICE)
- **File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` lines 157, 164
- **Error**: `109400: Mismatch type float64 with value string` on step 5
- **Root cause**: `str(signal.sl_price)` wraps price in quotes inside `json.dumps()`, producing `"stopPrice":"8.4546"`. BingX expects raw float: `"stopPrice":8.4546`
- **Fix applied**: Removed `str()` wrapper — `"stopPrice": signal.sl_price` (raw float, json.dumps handles it)
- **Fixed in**: executor.py (lines 157, 164) + test_api_lifecycle.py (all json.dumps SL/TP calls)
- **py_compile**: PASS on both files
- **This bug would have hit on the NEXT live signal** — lifecycle test caught it in 3.6 seconds

## Lifecycle Test Results (after stopPrice fix)
- Steps 1-4: ALL PASS (auth, public endpoints, leverage, qty calc)
- Step 5: FAILED before fix (stopPrice string), needs re-run after fix
- Steps 6-15: NOT YET RUN (stopped on step 5 failure)

## PICKUP POINT FOR NEXT SESSION
1. Run the lifecycle test: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py"`
2. If step 5 passes, continue through all 15 steps — fix any failures as they appear
3. Once 15/15 pass, the bot's entire trade lifecycle is validated
4. Then restart the bot: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"`
5. API docs cross-reference NOT YET DONE — BingX docs at https://bingx-api.github.io/docs-v3/#/en/info are JS-rendered, couldn't scrape. User wants every function cross-referenced against official docs. Do this in next session.
6. User also wants 37 more coins added (has a list)

## Open Questions for Next Session
- Cross-reference ALL bot API calls against official BingX v3 docs (https://bingx-api.github.io/docs-v3/#/en/info)
- Endpoints to verify: trade/order (POST), user/positions (GET), trade/openOrders (GET), trade/allOpenOrders (DELETE), trade/order (DELETE cancel), trade/order (GET query), trade/leverage (POST), trade/marginType (POST), quote/klines (GET v3), quote/price (GET), quote/contracts (GET)
- Confirm: does BingX support simultaneous SL+TP on a single order? (conflicting info online)
- build_bingx_connector.py lines 954/961 still have the old str(stopPrice) bug — not critical (build script) but should be fixed

## All Bugs Found This Session (Cumulative)
| ID | File | Bug | Status |
|----|------|-----|--------|
| E1-ROOT | bingx_auth.py:31 | urlencode() before signing breaks signature on JSON params | FIXED |
| E2-STOPPRICE | executor.py:157,164 | str() around stopPrice in json.dumps produces string, BingX wants float | FIXED |
| A1 | bingx_auth.py:44 | Missing recvWindow parameter | FIXED (prior session) |
| M1 | main.py:202 | No API error check on reconcile | FIXED (prior session) |
| M2 | main.py:36-37 | Relative log path | FIXED (prior session) |
| TZ1 | main.py+notifier.py | UTC vs UTC+4 timestamps | FIXED (prior session) |
| SB1 | main.py:74 | Wrong leverage side enum | FIXED (prior session) |
| SB2 | config.yaml | Buffer 200 vs 201 off-by-one | FIXED (prior session) |

## Session 2 — Continued (2026-02-25 afternoon)

### Lifecycle Test: 15/15 PASS
- Fixed hedge mode detection in test steps 11/12/13 (`positionSide` instead of `positionAmt > 0`)
- Added step 0 cleanup (close stale positions before test)
- Changed runner to continue on failure (no break)
- Final result: **15/15 PASS in 22.3 seconds**

### Bot Deployed: 47 coins on BingX VST demo
- Merged 14 high-Exp + 34 low-DD coins from v384 sweep = 53 initial
- Removed 6 not on BingX perps: 1000TOSHI, XCN, MON, DODO, ES, 1000000MOG
- Final: **47 coins** in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
- Set `tp_atr_mult: 4.0` (was null = no TP on any trade)
- Set `poll_interval_sec: 45`, `max_positions: 25`, `max_daily_trades: 200`
- Added startup throttle (200ms between leverage/margin API calls)
- Changed log level to INFO, silenced urllib3
- Added connection pooling (`requests.Session()`) to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\data_fetcher.py`

### 3 Critical Bug Fixes Applied
| Bug | File | Before | After | Impact |
|-----|------|--------|-------|--------|
| Hedge mode | `position_monitor.py:151` + `state_manager.py:156` | `amt > 0` for direction | `positionSide` field (fallback to amt) | BingX hedge mode always returns positive positionAmt for both LONG and SHORT |
| Exit detection | `position_monitor.py:60-138` | Queried entry order ID (always got SL_HIT_ASSUMED) | Queries open orders: SL pending = TP hit, TP pending = SL hit. Cancels orphaned order. | Correct exit reason + orphan cleanup |
| Commission | `position_monitor.py:186` | `notional * 0.0008 * 2` (0.16%) | `notional * 0.001` (0.10%) | 0.08% taker entry + 0.02% maker exit = 0.10% blended |

### Test Fix
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_data_fetcher.py`: Changed mock from `data_fetcher.requests.get` to `data_fetcher.requests.Session.get` (connection pooling broke old mock target)
- **67/67 tests passing**

### Bot Status at End of Session
- Running on BingX VST demo with 47 coins
- Warmup in progress (~3.3 hours for 201 bars at 1m)
- All SL + TP enforced on every trade
- 102k VST balance, $50 margin per trade, 10x leverage

### Remaining Performance Items (not yet done)
1. Cache contract step sizes in executor (avoids re-downloading all contracts per trade)
2. Connection pooling for executor + position_monitor (only data_fetcher has it)
3. Poll cycle drift compensation (timer should account for fetch duration)
4. Skip leverage/margin setup on restart if already set

## Key Files Modified This Session
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_api_lifecycle.py` — NEW + hedge mode fixes
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` — stopPrice fix (lines 157, 164)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` — hedge mode, exit detection, commission, orphan cancel
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py` — hedge mode in reconcile()
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\data_fetcher.py` — connection pooling
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` — log level, throttle, urllib3 silence
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` — 47 coins, tp_atr_mult=4.0, poll=45s
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_data_fetcher.py` — Session.get mock fix
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\build_bingx_connector.py` — stopPrice str() removed
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\docs\BINGX-API-V3-REFERENCE.md` — NEW (API reference)
