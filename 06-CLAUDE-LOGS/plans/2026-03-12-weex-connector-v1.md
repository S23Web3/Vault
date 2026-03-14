# Plan: WEEX Trading Connector v1.0

## Context

BingX connector is live and working ($110 account, 47 coins, v1.5). User wants the same
connector for WEEX — their primary target exchange (WEEX is primary per ATR-SL BUILD SPEC).
WEEX offers higher rebates: 70% rebate account = $4.80/RT net.

## Phase 0: WEEX API Research (BEFORE ANY CODE)

The build spec (`ATR-SL-Trailing-TP-BUILD-SPEC.md`) notes WEEX trade endpoint as:
`https://api.weex.com/api/v1/trade/order` but flags it as UNVERIFIED.
The probe confirmed `api.weex.com` is a dead host. The working host from probe is
`api-contract.weex.com`. Need correct authenticated endpoints before building.

**Action required**: Use Playwright MCP (or browser) to research WEEX API docs:

- WEEX official API docs URL (likely `docs.weex.com` or similar)
- Auth method: header-based (X-API-KEY / X-SIGN) or query-param HMAC like BingX?
- Order placement endpoint for perpetual futures
- Position query endpoint
- Open orders endpoint
- Cancel order endpoint
- Account balance endpoint
- Server time endpoint (for clock sync)
- Whether WEEX has a testnet/demo mode

This research is done in a SEPARATE step before writing any code.

---

## Architecture: WEEX Connector v1.0

Mirror the BingX connector architecture exactly. Same components, same thread model,
different exchange API calls. Strategy plugin is reused unchanged (BingX and WEEX share
the same Four Pillars signals — compute_signals_v383 is exchange-agnostic).

### Project Root

`C:\Users\User\Documents\Obsidian Vault\PROJECTS\weex-connector\`

### Thread Model (identical to BingX)

| Thread | File | Function |
|--------|------|----------|
| Main | `main.py` | Startup, config, signal handler, daily reset |
| MarketLoop | `data_fetcher.py` | 45s poll, OHLCV buffer, new-bar detection |
| MonitorLoop | `position_monitor.py` | 30s check, SL/BE/TTP management |
| WSListener | `ws_listener.py` | Fill detection via WebSocket (if WEEX supports it) |

### Core Files (write original, following v2 component structure)

| BingX file | WEEX equivalent | Changes |
|------------|-----------------|---------|
| `bingx_auth.py` | `weex_auth.py` | Different auth scheme (TBD from API research) |
| `data_fetcher.py` | `data_fetcher.py` | Different kline endpoint + symbol format |
| `executor.py` | `executor.py` | Different order endpoints + response parsing |
| `position_monitor.py` | `position_monitor.py` | Different position query endpoints |
| `signal_engine.py` | `signal_engine.py` | **No changes** — strategy-agnostic |
| `state_manager.py` | `state_manager.py` | Minimal changes (field names if needed) |
| `risk_gate.py` | `risk_gate.py` | **No changes** — exchange-agnostic |
| `notifier.py` | `notifier.py` | **No changes** |
| `ws_listener.py` | `ws_listener.py` | Different WS endpoint + message schema |
| `time_sync.py` | `time_sync.py` | Different server time endpoint |
| `ttp_engine.py` | `ttp_engine.py` | **No changes** — price-level logic |
| `plugins/four_pillars.py` | `plugins/four_pillars.py` | **Write original** — reimplement latest signal version from scratch (standalone, no backtester import) |
| `config.yaml` | `config.yaml` | Exchange-specific fields replaced |

### Key Differences from BingX (anticipated)

1. **Auth**: BingX uses HMAC-SHA256 query-param signing. WEEX build spec shows header-based: `X-API-KEY`, `X-TIMESTAMP`, `X-SIGN`. Exact scheme TBD.
2. **Symbol format**: BingX = `BTC-USDT`. WEEX contract API = `cmt_btcusdt` (probe confirmed). Order API format may differ.
3. **Position mode**: BingX requires explicit LONG/SHORT positionSide (hedge mode). WEEX equivalent needs verification.
4. **Kline endpoint**: BingX = `/openApi/swap/v3/quote/klines`. WEEX = `/capi/v2/market/candles`.
5. **Order types**: BingX has `TRAILING_STOP_MARKET`. WEEX equivalent TBD.
6. **Testnet**: BingX has VST demo mode. WEEX testnet availability unknown.

### Config Schema (`config.yaml`)

```yaml
connector:
  poll_interval_sec: 45
  position_check_sec: 30
  timeframe: 5m
  ohlcv_buffer_bars: 201
  demo_mode: false
coins:
  - BTCUSDT   # WEEX symbol format (TBD from research)
strategy:
  plugin: four_pillars_v384
four_pillars:
  allow_a: true
  allow_b: true
  allow_c: false
  sl_atr_mult: 2.0
  tp_atr_mult: null
  require_stage2: true
  rot_level: 80
risk:
  max_positions: 25
  max_daily_trades: 200
  daily_loss_limit_usd: 15.0
  min_atr_ratio: 0.003
  max_atr_ratio: 0.015
  cooldown_bars: 3
  bar_duration_sec: 300
position:
  margin_usd: 5.0
  leverage: 20   # WEEX target is 20x (rebate model)
  margin_mode: ISOLATED
  ttp_enabled: true
  ttp_act: 0.008
  ttp_dist: 0.003
  be_auto: true
  be_act: 0.004
  be_buffer: 0.002
  sl_trail_pct_post_ttp: 0.003
notification:
  daily_summary_utc_hour: 17
```

---

## Build Sequence

### Step 1 — API Research (one session, Playwright)

- Hit WEEX docs, extract all endpoints needed
- Confirm auth method
- Confirm symbol format for order API
- Confirm testnet availability
- Write `docs/WEEX-API-REFERENCE.md`

### Step 2 — Project scaffold + auth

- Create `weex-connector/` directory structure
- `build_weex_connector.py` — single build script, creates all files
- `weex_auth.py` — auth class with correct signing
- `time_sync.py` — server time sync
- `config.yaml`, `.env.example`, `requirements.txt`

### Step 3 — Market data

- `data_fetcher.py` — kline polling, buffer management (same logic, WEEX endpoint)
- Test: verify OHLCV buffer fills correctly for a handful of coins

### Step 4 — Core trading

- `executor.py` — order placement, SL, cancel
- `position_monitor.py` — position queries, BE raise, TTP tighten
- `state_manager.py` — write original (apply deep-copy + reconcile patterns from bug audit)
- `risk_gate.py` — write original, exchange-agnostic
- Test: lifecycle test (open + close + verify state)

### Step 5 — Signal + monitoring

- `signal_engine.py` — write original strategy adapter
- `ws_listener.py` — WEEX WS fills (if supported)
- `notifier.py` — write original Telegram notifier
- `ttp_engine.py` — write original TTP engine
- `plugins/` — write original (same Four Pillars strategy logic)

### Step 6 — main.py + tests

- `main.py` — startup, thread orchestration
- `tests/` — full test suite mirroring BingX 67 tests
- `scripts/test_connection.py`, `scripts/test_api_lifecycle.py`

### Step 7 — Demo run

- 24h demo run (if testnet available) or paper trade against live market
- Verify fills, exit detection, Telegram alerts, state persistence

---

## Files to Create

| File | Purpose |
|------|---------|
| `docs/WEEX-API-REFERENCE.md` | Exchange API reference (from research) |
| `build_weex_connector.py` | Master build script — creates all source files |
| `weex_auth.py` | Auth/signing |
| `time_sync.py` | Server time sync |
| `data_fetcher.py` | OHLCV polling |
| `executor.py` | Order placement |
| `position_monitor.py` | Position / SL / BE / TTP |
| `state_manager.py` | Atomic state (state.json + trades.csv) |
| `risk_gate.py` | Trade risk checks |
| `signal_engine.py` | Strategy adapter |
| `notifier.py` | Telegram alerts |
| `ttp_engine.py` | TTP candle-level evaluation |
| `ws_listener.py` | WebSocket fills |
| `main.py` | Entry point |
| `config.yaml` | Runtime config |
| `.env.example` | Key template |
| `requirements.txt` | Dependencies |
| `plugins/four_pillars.py` | Strategy plugin (standalone reimplementation of latest signal version) |
| `tests/` | Full test suite |
| `scripts/test_connection.py` | Quick API health check |
| `scripts/test_api_lifecycle.py` | Full trade lifecycle test |

---

## Critical Dependency

**Everything blocks on Step 1 (API research).** Cannot write `weex_auth.py`, `executor.py`,
`position_monitor.py`, or `data_fetcher.py` without confirmed endpoint + auth scheme.

## Relationship to BingX Connector

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector-v2\` — ARCHITECTURAL reference only (component structure, thread model). Do NOT copy code.
- `signal_engine.py`, `risk_gate.py`, `notifier.py`, `ttp_engine.py`, `plugins/` — write original, following same component structure as v2
- `state_manager.py` — write original, apply deep-copy and reconcile patterns from bug audit
- `main.py` — write original, WEEX-specific startup calls

## Verification

1. `python scripts/test_connection.py` — confirms API keys work, klines return data
2. `python scripts/test_api_lifecycle.py` — opens 1 test position, verifies state, closes it
3. 24h demo run — Telegram alerts flow, no crashes, exits correctly classified
4. `python -m pytest tests/ -v` — all tests pass

## Open-Source Requirement

This connector will be submitted to a public GitHub repository. All code must be original — no copy-paste from BingX connector v2, v3, or any other source. The bug audit prevention rules apply as engineering principles, not as code to copy.
