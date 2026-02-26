# BingX Execution Connector — Build Plan

## Context

The user designed a complete live trading execution connector for BingX exchange (UML spec v2.0 at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\BINGX-CONNECTOR-UML.md`). A separate bug audit found 8 connector bugs (at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\UML-BUG-FINDINGS-2026-02-20.md`). The user wants this built now to run on Jacky VPS over the weekend in demo mode with mock strategy.

**Decisions locked:**
- v3 endpoints for public market data (`/openApi/swap/v3/quote/klines`)
- v2 endpoints for trade/user operations (no confirmed v3 equivalents)
- Mock strategy only -- `FourPillarsV384` plugin is a separate build
- Write files directly to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\`
- One build script generates all files + py_compile each

## Bug Fixes Applied In Code

| Bug ID | Severity | Fix |
|--------|----------|-----|
| C03 | CRITICAL | halt_flag read by RiskGate check #1 (OR with daily_pnl check) |
| C04 | CRITICAL | halt_flag reset to False at 17:00 UTC daily reset |
| C05 | HIGH | allowed_grades comes from plugin.get_allowed_grades(), NOT connector config |
| C07 | HIGH | Public endpoints use unsigned requests (no HMAC, no timestamp) |
| C01 | MEDIUM | Signal uses LONG/SHORT/NONE vocabulary throughout |
| C02 | MEDIUM | Mark price fetched from /quote/price, not /quote/klines |

C06 (warmup_bars): Implemented -- MockStrategy returns 0, FourPillarsV384 will return 89.
C08 (sl_atr_mult): Out of scope for connector -- strategy plugin responsibility.

## Build Script

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\build_bingx_connector.py`

**Pattern:** Same as `build_dashboard_v391.py` and `build_yt_transcript_analyzer.py`:
- `write_and_verify(rel_path, content)` -- writes file, py_compile + ast.parse for .py files
- Each module in its own `build_*()` function
- Global ERRORS/CREATED lists
- Summary at end with pass/fail count

## Files Generated (18 total, dependency order)

| # | File | Purpose |
|---|------|---------|
| 1 | `requirements.txt` | requests, pyyaml, python-dotenv, pandas |
| 2 | `.env.example` | Template for credentials |
| 3 | `.gitignore` | Exclude .env, state.json, trades.csv, bot.log, __pycache__ |
| 4 | `config.yaml` | Connector config (demo_mode: true, 3 coins, risk params) |
| 5 | `bingx_auth.py` | HMAC-SHA256 signing, demo/live URL toggle, public URL builder |
| 6 | `notifier.py` | Telegram send(message), never raises, timestamps all messages |
| 7 | `state_manager.py` | state.json (atomic write), trades.csv (append), threading.Lock |
| 8 | `plugins/__init__.py` | Empty |
| 9 | `plugins/mock_strategy.py` | Signal dataclass + MockStrategy (random signals, inject_signal) |
| 10 | `data_fetcher.py` | Poll /v3/quote/klines, 200-bar buffer, new-bar detection, callback |
| 11 | `risk_gate.py` | 6 ordered checks, halt_flag fix (C03), returns (bool, reason) |
| 12 | `executor.py` | Mark price, qty calc, step size rounding, order+SL+TP, state record |
| 13 | `signal_engine.py` | Dynamic plugin load (importlib), on_new_bar orchestration |
| 14 | `position_monitor.py` | Poll /v2/user/positions, diff state, close detection, daily reset (C04) |
| 15 | `main.py` | Load config/.env, init all components, 2 threads, graceful shutdown |
| 16 | `tests/test_auth.py` | HMAC against known vector, public URL has no sig, demo URL toggle |
| 17 | `tests/test_risk_gate.py` | All 6 checks, halt_flag persistence, check ordering |
| 18 | `tests/test_executor.py` | Qty calc, LONG/SHORT payload, SL/TP JSON structure |
| 19 | `tests/test_plugin_contract.py` | MockStrategy interface, inject_signal, Signal fields |

## Module Design Highlights

### bingx_auth.py
- `BingXAuth(api_key, secret_key, demo_mode=True)` -- toggles base URL
- `sign_params(params)` -- sort alphabetically, HMAC-SHA256, hex digest
- `build_signed_request(method, path, params)` -- returns {url, headers, method}
- `build_public_url(path, params)` -- no timestamp, no signature (BUG-C07 fix)

### data_fetcher.py
- `MarketDataFeed(base_url, symbols, timeframe="5m", buffer_bars=200, poll_interval=30)`
- `_fetch_klines(symbol)` -- GET v3/quote/klines (PUBLIC, no auth)
- `_is_new_bar(symbol, df)` -- compare last CLOSED bar timestamp (not current bar)
- `tick(callback)` -- one cycle: fetch all symbols, fire callback(symbol, df) on new bars
- `warmup()` -- initial fetch for all symbols at startup

### risk_gate.py (BUG-C03/C04 applied)
- Check 1: `halt_flag == True OR daily_pnl <= -loss_limit` (reads halt_flag from state)
- Check 2-6: max positions, duplicate, grade filter (from plugin), ATR threshold, daily limit
- `evaluate(signal, symbol, state, allowed_grades)` -> (bool, str)

### state_manager.py
- Atomic write: state.json.tmp -> os.replace -> state.json
- `threading.Lock` for concurrent access from market + monitor threads
- `reset_daily()` -- sets daily_pnl=0, daily_trades=0, halt_flag=False (BUG-C04)
- `reconcile(live_positions)` -- sync state with exchange on startup

### executor.py
- Uses v2 endpoints for all signed operations (trade/order, quote/price, quote/contracts)
- SL/TP attached as JSON params on the order (single POST, not separate orders)
- positionSide mapping: LONG signal -> side=BUY, positionSide=LONG
- Quantity rounded DOWN to step size (never up)

### position_monitor.py
- Polls /v2/user/positions every 60s
- State position missing from exchange -> closed (SL/TP hit server-side)
- Exit price estimation: defaults to SL price (pessimistic) -- noted as future v2 improvement
- Daily reset at 17:00 UTC: calls state_manager.reset_daily()

### main.py
- Two daemon threads: market_loop (30s), monitor_loop (60s)
- `threading.Event` for clean shutdown on Ctrl+C
- Startup: load .env + config.yaml, init all components, set leverage/margin per coin, reconcile, warmup, notify

### plugins/mock_strategy.py
- `Signal` dataclass: direction, grade, entry_price, sl_price, tp_price, atr, bar_ts
- `MockStrategy(config)`: 5% signal probability per bar, random LONG/SHORT
- `inject_signal(signal)` -- deterministic test override
- `get_allowed_grades()` -> ["MOCK"]
- `warmup_bars()` -> 0

## Threading Model

```
Main Thread: startup -> join threads -> KeyboardInterrupt handler

Thread 1 (MarketDataLoop, daemon):
    while not shutdown.is_set():
        feed.tick(callback=adapter.on_new_bar)
        shutdown.wait(poll_interval)

Thread 2 (MonitorLoop, daemon):
    while not shutdown.is_set():
        monitor.check()
        monitor.check_daily_reset()
        shutdown.wait(position_check_sec)
```

Shared state protection: threading.Lock inside StateManager (callers don't manage it).

## API Endpoints Used

| Endpoint | Version | Auth | Purpose |
|----------|---------|------|---------|
| /openApi/swap/v3/quote/klines | v3 | Public | OHLCV candles |
| /openApi/swap/v2/quote/price | v2 | Public | Mark price for qty calc |
| /openApi/swap/v2/quote/contracts | v2 | Public | Step size / min qty |
| /openApi/swap/v2/trade/order | v2 | Signed | Place order with SL/TP |
| /openApi/swap/v2/user/positions | v2 | Signed | Open positions |
| /openApi/swap/v2/trade/leverage | v2 | Signed | Set leverage (startup) |
| /openApi/swap/v2/trade/marginType | v2 | Signed | Set ISOLATED (startup) |

## Run Commands

```bash
# Build (generates all files):
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\build_bingx_connector.py"

# Run tests locally:
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python -m pytest tests/ -v

# Deploy to Jacky:
scp -r "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\*" ubuntu@jacky:/home/ubuntu/bingx-bot/

# On Jacky:
cd /home/ubuntu/bingx-bot
pip install -r requirements.txt
nano .env  # add credentials
python -m pytest tests/ -v
python main.py  # demo mode
```

## Build-Time Validation (in build script)

Every generated .py file goes through 3 checks BEFORE the build reports success:

1. **py_compile.compile(path, doraise=True)** -- catches syntax errors, bad f-strings, unicode escapes
2. **ast.parse(source)** -- catches structural issues py_compile misses (malformed expressions)
3. **Import smoke test** -- after ALL files are written, attempt `importlib.import_module()` on each module in dependency order. Catches circular imports, missing dependencies, bad relative imports. This runs in the build script itself.

```python
# In build script, after all files written:
IMPORT_ORDER = [
    "bingx_auth", "notifier", "state_manager",
    "plugins.mock_strategy", "data_fetcher",
    "risk_gate", "executor", "signal_engine",
    "position_monitor",
]
sys.path.insert(0, str(ROOT))
for mod in IMPORT_ORDER:
    try:
        importlib.import_module(mod)
        print("  [IMPORT OK] " + mod)
    except Exception as e:
        print("  [IMPORT FAIL] " + mod + ": " + str(e))
        ERRORS.append("import:" + mod)
```

Build fails (non-zero exit, prints FAILURES list) if ANY check fails.

## Testing Architecture -- 4 Layers

### Layer 1: Unit Tests (no network, no .env required)

All tests run **fully offline** using `unittest.mock`. Zero API calls, zero Telegram sends.

**tests/test_auth.py** -- HMAC signature correctness
- Known input: `{"symbol": "BTC-USDT", "side": "BUY", "timestamp": 1700000000000}`, secret=`"test_secret"`
- Assert exact hex digest matches hand-calculated value
- Assert `build_public_url()` has NO signature param and NO timestamp
- Assert `demo_mode=True` uses `open-api-vst.bingx.com`, `False` uses `open-api.bingx.com`
- Assert params are sorted alphabetically in the signed query string

**tests/test_risk_gate.py** -- all 6 checks in isolation
- Test each check individually with crafted state dicts
- Test check ORDER: halt_flag (check 1) blocks before max_positions (check 2) is ever reached
- Test halt_flag survives across evaluate() calls (persistence via state dict)
- Test edge cases: daily_pnl exactly at -75.0 (boundary), 0 open positions, empty allowed_grades list
- Test APPROVED path: clean state, valid signal -> returns (True, "APPROVED")

**tests/test_executor.py** -- order construction (mocked HTTP)
- `@unittest.mock.patch("requests.get")` for mark price + contracts
- `@unittest.mock.patch("requests.post")` for order placement
- Assert qty = notional / mark_price, rounded DOWN to step size
- Assert LONG signal -> side="BUY", positionSide="LONG"
- Assert SHORT signal -> side="SELL", positionSide="SHORT"
- Assert SL/TP JSON structure in payload
- Assert API failure (non-0 code) -> returns None, does NOT record position
- Assert mark_price fetch failure -> returns None, does NOT attempt order
- Assert step_size fetch failure -> returns None gracefully

**tests/test_plugin_contract.py** -- interface compliance
- MockStrategy has all 5 required methods: get_signal, get_name, get_version, warmup_bars, get_allowed_grades
- get_signal() returns Signal or None (never raises)
- inject_signal() forces next output
- Signal dataclass has all 7 fields with correct types
- get_allowed_grades() returns non-empty list of strings

**tests/test_state_manager.py** (adding this -- critical for crash recovery)
- record_open_position() -> position appears in state, daily_trades incremented
- close_position() -> position removed, daily_pnl updated, trades.csv appended
- reset_daily() -> daily_pnl=0, daily_trades=0, halt_flag=False
- Atomic write: corrupt mid-write -> previous state.json still valid
- Thread safety: concurrent record + close don't corrupt state
- Load from empty/missing state.json -> returns clean defaults
- reconcile(): state has phantom position not on exchange -> removed

**tests/test_data_fetcher.py** (adding this -- critical for new-bar detection)
- `@unittest.mock.patch("requests.get")` with mock kline response
- _is_new_bar: same timestamp twice -> False
- _is_new_bar: new timestamp -> True
- _fetch_klines: API error (timeout, 500, bad JSON) -> returns None, no crash
- Buffer management: exactly 200 bars retained, older bars dropped
- warmup: all symbols fetched, all buffers populated

### Layer 2: Integration Test Script (offline, tests module wiring)

**tests/test_integration.py** -- end-to-end signal-to-execution flow with all modules wired together, ALL HTTP mocked.

```
1. Create all components with mock HTTP
2. Inject a LONG signal via mock_strategy.inject_signal()
3. MarketDataFeed.tick() fires (with mock kline data)
4. StrategyAdapter calls get_signal() -> returns injected Signal
5. RiskGate evaluates -> APPROVED (clean state)
6. Executor builds order payload (mock mark_price, mock step_size)
7. Executor POSTs order (mock response: success)
8. StateManager records position
9. Assert: state has 1 open position with correct fields
10. Assert: notifier.send() was called with entry message
```

Then simulate position closure:
```
11. PositionMonitor.check() with mock positions = [] (empty = position closed)
12. StateManager.close_position() called
13. Assert: state has 0 open positions
14. Assert: trades.csv has 1 row
15. Assert: notifier.send() called with exit message
```

Then simulate daily reset:
```
16. Set daily_pnl = -80 (below limit), halt_flag = True
17. PositionMonitor.check_daily_reset() at 17:00 UTC
18. Assert: daily_pnl = 0, halt_flag = False, daily_trades = 0
```

### Layer 3: Connection Test Script (needs .env, tests real API)

**scripts/test_connection.py** -- run manually when .env is configured. NOT part of automated test suite.

```python
# Tests (each prints PASS/FAIL):
# 1. BingX auth: sign a test request, verify URL format
# 2. Fetch klines: GET /v3/quote/klines for BTC-USDT, check response has data
# 3. Fetch mark price: GET /v2/quote/price for BTC-USDT
# 4. Fetch contracts: GET /v2/quote/contracts, find step size for BTC-USDT
# 5. Check positions: GET /v2/user/positions (signed)
# 6. Telegram: send test message "BingX connector test - connection OK"
# 7. Print: all results + latency per call
```

This script does NOT place orders. Read-only + one Telegram message.

Run command:
```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/test_connection.py
```

### Layer 4: Live Demo Test (BingX VST, needs .env)

Run `python main.py` with `demo_mode: true` in config.yaml. This uses BingX's demo exchange. Mock strategy fires ~5% of bars. Bot places real orders on demo, monitors positions, sends Telegram alerts.

Watch for:
- Startup notification on Telegram
- Kline fetch logs every 30s
- "New bar detected" logs when 5m bar closes
- Signal + risk gate evaluation logs
- Order placement logs (may fail on demo -- some symbols not available)
- Position monitor logs every 60s

## Error Handling Patterns (Built Into Every Module)

### HTTP Request Wrapper

Every module that makes HTTP calls uses a shared pattern:

```python
def _safe_request(self, method, url, headers=None, timeout=10):
    """Execute HTTP request with error handling. Returns response dict or None."""
    try:
        resp = requests.request(method, url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code", 0) != 0:
            logger.error("API error %s: %s", data.get("code"), data.get("msg"))
            return None
        return data
    except requests.exceptions.Timeout:
        logger.error("Timeout: %s %s", method, url)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection failed: %s %s", method, url)
        return None
    except requests.exceptions.HTTPError as e:
        logger.error("HTTP %s: %s %s", e.response.status_code, method, url)
        return None
    except ValueError:
        logger.error("Invalid JSON response: %s %s", method, url)
        return None
```

**Rule: every HTTP caller returns None on failure. Callers check for None before proceeding. No exceptions bubble up from network calls.**

### Module-Level Error Boundaries

Each module catches its own errors and logs them. The main loop never crashes from a module failure:

```python
# In market_loop:
try:
    feed.tick(callback)
except Exception as e:
    logger.error("Market loop error: %s", e, exc_info=True)
    # Continue -- don't crash the bot

# In monitor_loop:
try:
    monitor.check()
    monitor.check_daily_reset()
except Exception as e:
    logger.error("Monitor loop error: %s", e, exc_info=True)
    # Continue -- don't crash the bot
```

### Graceful Degradation Table

| Failure | Behavior | Recovery |
|---------|----------|----------|
| BingX API unreachable | Log error, skip this tick, retry next cycle | Automatic on next tick |
| Telegram unreachable | Log warning, continue trading | notifier.send() returns False |
| state.json corrupt | Load defaults (empty state), log warning | Manual: restore from backup |
| state.json.tmp write fails | Old state.json preserved (atomic write) | Automatic |
| Plugin import fails | Log error, send Telegram alert, exit cleanly | Fix plugin, restart |
| Mark price fetch fails | Skip this signal, log warning | Automatic on next signal |
| Order placement fails | Log error, notify Telegram, do NOT record position | Automatic on next signal |
| Step size fetch fails | Skip this signal, log warning | Automatic on next signal |
| threading.Lock deadlock | Not possible -- single lock, no nested locking | N/A |
| KeyboardInterrupt | shutdown_event.set(), threads exit, state saved | Manual restart |

### Logging Configuration

```python
# main.py sets up dual logging: file + console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
```

Every module: `logger = logging.getLogger(__name__)` at module level.

| Level | What gets logged |
|-------|-----------------|
| DEBUG | Every kline fetch result, every risk check detail, raw API responses |
| INFO | New bar detected, signal fired, risk gate result, order placed, position closed, daily reset |
| WARNING | API returned no data, Telegram send failed, symbol not found on exchange |
| ERROR | HTTP errors, order rejected, state write failed, unexpected exceptions |

## Debug Script

**scripts/debug_connector.py** -- manual interactive debugger for troubleshooting

```python
# Modes:
# --test-auth        Sign a request, print URL + signature
# --test-klines SYM  Fetch klines for one symbol, print DataFrame
# --test-price SYM   Fetch mark price, print value
# --test-state       Load state.json, print contents
# --test-signal      Run mock_strategy.get_signal() with synthetic OHLCV
# --test-risk        Run risk_gate.evaluate() with synthetic signal + state
# --test-telegram    Send test message
```

Run:
```bash
python scripts/debug_connector.py --test-auth
python scripts/debug_connector.py --test-klines BTC-USDT
python scripts/debug_connector.py --test-risk
```

## Updated File Count (21 total)

Added to the build:
- `tests/test_state_manager.py` (#20)
- `tests/test_data_fetcher.py` (#21)
- `tests/test_integration.py` (#22)
- `scripts/test_connection.py` (#23)
- `scripts/debug_connector.py` (#24)
- `tests/__init__.py` (#25)

**Final count: 25 files** generated by one build script.

## Verification

1. Build script outputs `ALL PASS` -- zero ERRORS, zero IMPORT FAIL
2. `python -m pytest tests/ -v` -- all 7 test files pass (auth, risk_gate, executor, plugin, state_manager, data_fetcher, integration)
3. `python scripts/debug_connector.py --test-auth` -- prints signed URL correctly
4. `python scripts/test_connection.py` -- all 7 connection checks pass (needs .env)
5. `python main.py` starts, connects to BingX VST demo, mock strategy runs

## Session Log

Append to: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-20-bingx-connector-build.md`

## MEMORY.md Update

Add BingX Connector section with project root, file list, status, run commands.
