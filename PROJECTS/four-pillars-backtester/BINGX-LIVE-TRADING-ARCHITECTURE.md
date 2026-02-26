# BingX Live Trading — System Architecture
**Version:** 1.0  
**Date:** 2026-02-20  
**Status:** PRE-BUILD — Strategy review required before any code deployment  
**Capital:** $1,000 account | $50 position size per trade  
**Exchange:** BingX Perpetual Futures  

---

## PURPOSE OF THIS DOCUMENT

This is the architectural blueprint for deploying the Four Pillars v3.8.x strategy to live trading on BingX. No code is written until:

1. Strategy parameters are reviewed and locked via dashboard sweep
2. Coin list is validated (backtest results confirmed profitable)
3. Risk limits are defined and hardcoded
4. This document is approved

This document covers: architecture, data flow, API reference, risk management, deployment plan, and pre-launch checklist.

---

## SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│                    JACKY VPS (Jakarta)                  │
│                                                         │
│  ┌─────────────────┐    ┌──────────────────────────┐   │
│  │  DATA LAYER     │    │  SIGNAL ENGINE           │   │
│  │                 │    │                          │   │
│  │  BingX REST API │───▶│  Four Pillars v3.8.x     │   │
│  │  (OHLCV fetch)  │    │  (same logic as          │   │
│  │  5m candles     │    │   backtester)            │   │
│  │  every 30s poll │    │                          │   │
│  └─────────────────┘    └──────────┬───────────────┘   │
│                                    │                    │
│                          Signal fired? (A/B/C)          │
│                                    │                    │
│                         ┌──────────▼───────────┐       │
│                         │  RISK GATE           │       │
│                         │  - Max open positions│       │
│                         │  - Daily loss limit  │       │
│                         │  - Per-trade sizing  │       │
│                         └──────────┬───────────┘       │
│                                    │                    │
│                         ┌──────────▼───────────┐       │
│                         │  EXECUTION LAYER     │       │
│                         │  BingX swap/v2 API   │       │
│                         │  - Place order       │       │
│                         │  - Attach SL/TP      │       │
│                         │  - Track position    │       │
│                         └──────────┬───────────┘       │
│                                    │                    │
│                         ┌──────────▼───────────┐       │
│                         │  STATE STORE         │       │
│                         │  SQLite / JSON file  │       │
│                         │  - Open positions    │       │
│                         │  - Trade history     │       │
│                         │  - Daily P&L         │       │
│                         └──────────┬───────────┘       │
│                                    │                    │
│                         ┌──────────▼───────────┐       │
│                         │  NOTIFICATION        │       │
│                         │  Telegram bot        │       │
│                         │  - Entry/exit alerts │       │
│                         │  - Daily summary     │       │
│                         │  - Error alerts      │       │
│                         └──────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## PHASE 0: BEFORE WRITING CODE — MANDATORY CHECKLIST

These must be completed IN ORDER before any code is written.

### Step 1: Strategy Parameter Review (Dashboard)

Run the dashboard on target coins and lock these parameters:

| Parameter | Current Default | Action Required |
|-----------|----------------|-----------------|
| sl_atr_mult | 1.0 | Run sweep, confirm or adjust |
| tp_atr_mult | 1.5 | Run sweep per coin (TP sweep already done for RIVER) |
| be_raise_atr | 4 (RIVER only) | Confirm value per coin |
| allow_b_trades | True | Confirm — more trades but lower quality |
| allow_c_trades | True | May want to DISABLE for live (too noisy) |
| cross_level | 25 | Leave default unless sweep shows otherwise |
| zone_level | 30 | Leave default |
| atr_length | 14 | Leave default |

**Recommended first sweep:** Grade A only, MARKET orders, SL=1.5 ATR, TP=2.0 ATR on 5m. Compare expectancy vs the runner (no TP) variant.

**Gate:** If expectancy $/trade < $1.00 after commissions at $50 notional, do NOT proceed.

### Step 2: Coin Selection

**Criteria for a coin to qualify for live trading:**

| Metric | Minimum Threshold | Source |
|--------|-------------------|--------|
| Net P&L (30 days backtest) | Positive after rebate | Dashboard sweep |
| Expectancy $/trade | > $1.00 | Dashboard drill-down |
| Profit Factor | > 1.1 | Dashboard |
| Trade count (30 days, 5m) | > 150 | Enough sample |
| MaxDD | < 40% of notional | Dashboard |
| avg_atr_pct | 0.40 – 0.80 | coin_tiers.csv |
| avg_daily_range | > 0.35% | coin_tiers.csv |

**Confirmed candidate:** RIVERUSDT (5m, BE=4, Net +$55K on $5K notional — scale down)
**Other candidates to sweep:** BERAUSDT, KITEUSDT, GUNUSDT, AXSUSDT

**Maximum coins for $1,000 account:** 3 coins maximum (see Risk section)

### Step 3: Position Sizing Calculation

With $1,000 account, $50 positions:

```
Account balance:      $1,000 USDT
Position notional:    $50 margin × leverage
Recommended leverage: 10x (max, NOT 20x for live test)
Notional value:       $50 × 10 = $500 per trade
Max simultaneous:     3 positions = $150 margin = 15% of account
SL per trade:         1.5 ATR distance
Max loss per trade:   ~$20–25 (ATR-based, coin dependent)
Daily loss limit:     $75 (7.5% of account — HARD STOP)
```

**Why NOT 20x for $1,000 test:** At 20x, one trade with 1.5 ATR stop on a volatile coin can wipe 7-10% in a single trade. 10x is the correct starting leverage at this capital level. Review after 30 days.

---

## COMPONENT SPECIFICATIONS

### Component 1: Data Layer (OHLCV Fetcher)

**Purpose:** Fetch live 5m candles from BingX and maintain a rolling OHLCV buffer per coin.

**BingX Kline endpoint:**
```
GET https://open-api.bingx.com/openApi/swap/v2/quote/klines
Parameters:
  symbol:    BTC-USDT        (dash format — NOT BTCUSDT)
  interval:  5m              
  limit:     200             (need 200 bars for cloud EMAs to warm up)
  timestamp: unix_ms         (required, signed)

Auth: X-BX-APIKEY header + HMAC-SHA256 signature in query string
```

**Polling logic:**
- Poll every 30 seconds (not every second — rate limits apply)
- Fetch last 200 bars to ensure indicators have warm-up period
- Compare last close timestamp to previous — skip if no new bar
- Buffer: rolling 500 bars per coin (parquet or dict in memory)
- Rate limit: 2,000 req/10s account-wide (as of 2025-10-16) — 30s interval is safe

### Component 2: Signal Engine

**Purpose:** Run the identical Four Pillars signal pipeline used in the backtester. Not a reimplementation — import directly from the backtester codebase.

**Import path:**
```python
# Direct imports from backtester (no duplication)
from signals.four_pillars import compute_signals
from strategies.cloud_filter import apply_cloud3_filter
```

**Signal check trigger:**
- On each new confirmed 5m bar (bar close, not mid-bar)
- Run compute_signals() on the rolling buffer
- Check last bar for long_a, long_b, long_c, short_a, short_b, short_c
- Apply Grade filter (configurable: A only / A+B / A+B+C)

**CRITICAL:** Do NOT fire on mid-bar. Wait for bar close confirmation (timestamp of new bar appears in API response).

### Component 3: Risk Gate

**Purpose:** Filter all signals through risk checks before any order is sent. This is non-negotiable.

**Checks (in order):**

```
1. DAILY_LOSS_LIMIT
   current_daily_loss >= max_daily_loss ($75)?
   → BLOCK all new entries, log warning, send Telegram alert

2. MAX_POSITIONS
   open_positions >= max_concurrent (3)?
   → BLOCK, log "max positions reached"

3. SAME_COIN_DUPLICATE
   coin already has open position in same direction?
   → BLOCK, log "duplicate position blocked"

4. GRADE_FILTER
   signal grade in allowed_grades?
   (configurable: ['A'] for conservative, ['A','B'] for normal)
   → PASS or BLOCK

5. MIN_ATR_THRESHOLD
   current ATR / close price < 0.003 (0.3%)?
   → BLOCK — coin not moving enough to cover commission
```

Only if ALL checks pass does execution proceed.

### Component 4: Execution Layer

**Purpose:** Place order on BingX with attached SL/TP as a package.

**BingX Order Endpoint:**
```
POST https://open-api.bingx.com/openApi/swap/v2/trade/order

Headers:
  X-BX-APIKEY: {api_key}

Query params (all signed):
  symbol:       BTC-USDT
  side:         BUY  (entry direction)
  positionSide: LONG (required — BingX uses hedge mode)
  type:         MARKET
  quantity:     {qty_in_base_currency}  (calculated from notional / mark_price)
  takeProfit:   {"type":"TAKE_PROFIT_MARKET","stopPrice":{tp_price},"workingType":"MARK_PRICE"}
  stopLoss:     {"type":"STOP_MARKET","stopPrice":{sl_price},"workingType":"MARK_PRICE"}
  timestamp:    {unix_ms}
  signature:    {hmac_sha256}

Auth method: HMAC-SHA256
  message = all_params_sorted_alphabetically_as_querystring
  signature = hmac(secret_key, message, sha256).hexdigest()
  append &signature={sig} to query string
```

**Position side mapping:**
```
Signal    | side | positionSide
----------|------|-------------
long_a/b/c | BUY  | LONG
short_a/b/c | SELL | SHORT
Close LONG  | SELL | LONG
Close SHORT | BUY  | SHORT
```

**Quantity calculation:**
```python
mark_price = fetch_mark_price(symbol)  # GET /openApi/swap/v2/quote/price
notional_usd = 500  # margin × leverage
qty = notional_usd / mark_price
qty = round_to_step_size(qty, symbol_info)  # fetch /openApi/swap/v2/quote/contracts
```

**SL/TP price calculation:**
```python
# From backtester logic — same formula
atr = compute_atr(df)[-1]
sl_price = entry_price - (sl_atr_mult × atr)  # for LONG
tp_price = entry_price + (tp_atr_mult × atr)  # for LONG
# Reverse for SHORT
```

**Demo mode:** BingX VST (demo) available at `https://open-api-vst.bingx.com` — same endpoints, same auth. Use this for integration testing before live.

### Component 5: State Store

**Purpose:** Track open positions, closed trades, and daily P&L. Lightweight — no PostgreSQL needed for this scale.

**Implementation:** Single JSON file per session + append-only trade log CSV.

```
/home/bingx-bot/
├── state.json          ← current open positions, daily P&L counter
├── trades.csv          ← append-only trade history
└── errors.log          ← all API errors with timestamp
```

**state.json structure:**
```json
{
  "open_positions": {
    "RIVER-USDT_LONG": {
      "symbol": "RIVER-USDT",
      "direction": "LONG",
      "entry_price": 0.0445,
      "sl_price": 0.0432,
      "tp_price": 0.0468,
      "quantity": 11236,
      "notional_usd": 500,
      "entry_time": "2026-02-20T14:30:00Z",
      "order_id": "1719727329359429732",
      "grade": "A"
    }
  },
  "daily_pnl": -12.50,
  "daily_trades": 4,
  "session_start": "2026-02-20T00:00:00Z"
}
```

**trades.csv columns:**
`timestamp, symbol, direction, grade, entry_price, exit_price, sl_price, tp_price, quantity, notional, pnl_gross, commission, pnl_net, exit_reason, duration_bars`

### Component 6: Position Monitor

**Purpose:** Detect when SL/TP has been hit (BingX handles this server-side — monitor only for state sync).

**Approach:** Poll open positions every 60 seconds via:
```
GET https://open-api.bingx.com/openApi/swap/v2/user/positions
```

If a position in state.json no longer appears in the API response → it was closed (SL or TP hit). Calculate P&L, update state.json, write to trades.csv, send Telegram notification.

**Alternative approach (cleaner):** BingX WebSocket user data stream. Subscribe to order fill events. Removes polling latency. Implement in V2 of the bot after basic version is stable.

### Component 7: Notification Layer

**Purpose:** Telegram bot for real-time trade alerts and daily summary.

**Events that trigger notifications:**
- Trade opened (symbol, direction, grade, entry, SL, TP, notional)
- Trade closed (exit reason, P&L, running daily total)
- Daily loss limit hit (HARD STOP engaged)
- API error (with error code and endpoint)
- Daily summary at 17:05 UTC (after rebate settlement)

**Telegram implementation:** Single function wrapping `requests.post` to `https://api.telegram.org/bot{TOKEN}/sendMessage`.

---

## AUTHENTICATION — BINGX HMAC-SHA256

**Confirmed working pattern from official examples:**

```python
import hmac
from hashlib import sha256
import time
import urllib.parse

def sign(params: dict, secret: str) -> str:
    """Sign params dict. Returns hexdigest."""
    query = urllib.parse.urlencode(sorted(params.items()))
    return hmac.new(
        secret.encode("utf-8"),
        query.encode("utf-8"),
        digestmod=sha256
    ).hexdigest()

def build_request(path: str, params: dict, api_key: str, secret: str) -> dict:
    """Returns headers and full URL for BingX API request."""
    params["timestamp"] = int(time.time() * 1000)
    sig = sign(params, secret)
    query = urllib.parse.urlencode(sorted(params.items()))
    url = f"https://open-api.bingx.com{path}?{query}&signature={sig}"
    headers = {"X-BX-APIKEY": api_key}
    return {"url": url, "headers": headers}
```

**Key differences from WEEX:**
- Signature goes in query string as `&signature=...` (NOT in header)
- API key in header `X-BX-APIKEY` (NOT `ACCESS-KEY`)
- Symbol format: `BTC-USDT` with dash (NOT `BTCUSDT` or `cmt_btcusdt`)
- No passphrase required (BingX uses only key + secret)
- Sort params alphabetically before signing

---

## RISK MANAGEMENT — HARD RULES

These are code-enforced, not guidelines.

| Rule | Value | Enforcement |
|------|-------|-------------|
| Max position size | $50 margin | Hardcoded, not configurable at runtime |
| Max leverage | 10x | Set via API on startup, verified before first trade |
| Max simultaneous positions | 3 | Risk Gate check #2 |
| Daily loss limit | $75 (7.5%) | Risk Gate check #1, kills all new entries |
| Minimum signal grade | A (conservative start) | Risk Gate check #4 |
| Stop Loss | ALWAYS attached at entry | Execution Layer — no SL = no trade |
| Take Profit | ALWAYS attached at entry | Execution Layer — no TP = no trade |
| SL/TP working type | MARK_PRICE | Prevents wick manipulation |
| Max daily trades | 20 | Prevents runaway loop bugs |
| Duplicate position | Blocked | One position per coin per direction |

**Margin mode:** ISOLATED (not cross). This prevents one bad trade from affecting other positions.

**Set on startup via API:**
```
POST /openApi/swap/v2/trade/leverage  → set to 10x per coin
POST /openApi/swap/v2/trade/marginType → set to ISOLATED per coin
```

---

## DEPLOYMENT — JACKY VPS

**Location:** Ubuntu 24, Jakarta timezone  
**Python version:** 3.11+  
**Run location:** `/home/ubuntu/bingx-bot/`  

**Credentials:**
- Stored in `.env` file on Jacky (NEVER in Obsidian vault)
- Variables: `BINGX_API_KEY`, `BINGX_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

**Process management:**
- Run as `systemd` service or `screen` session
- Restart policy: restart on crash, max 5 restarts/hour
- Log all output to `/home/ubuntu/bingx-bot/bot.log`

**Codebase on Jacky:**
```
/home/ubuntu/bingx-bot/
├── main.py                  ← Entry point, main loop
├── data_fetcher.py          ← BingX OHLCV polling
├── signal_engine.py         ← Imports from backtester signals/
├── risk_gate.py             ← All risk checks
├── executor.py              ← BingX order placement
├── position_monitor.py      ← Open position tracking
├── state_manager.py         ← state.json + trades.csv
├── notifier.py              ← Telegram integration
├── bingx_auth.py            ← HMAC signing utility
├── config.yaml              ← Non-secret config (coins, params)
├── .env                     ← Secrets (never committed)
├── trades.csv               ← Trade log
├── state.json               ← Live state
└── bot.log                  ← Operational log
```

**Backtester dependency:**
The signal_engine.py imports from the backtester project. Options:
1. Clone the backtester repo to Jacky and add to PYTHONPATH
2. Extract signals/ folder as standalone package
3. Pip install the backtester as local package

**Recommended:** Option 1 for now — simpler to keep in sync.

**Main loop logic:**
```
startup:
  load config, connect API, verify credentials
  set leverage and margin mode for each coin
  load state.json (resume if crash recovery)

loop (every 30s):
  for each coin in config.coins:
    1. fetch latest candles
    2. if new bar detected:
       a. run signal engine
       b. if signal: run risk gate
       c. if passes risk gate: execute order
  
  check open positions (every 60s):
    1. poll BingX positions API
    2. compare to state.json
    3. if position closed: record trade, update P&L, notify

  daily reset (at 00:00 UTC Jakarta time = 19:00 UTC-1):
    reset daily_pnl counter
    send daily summary to Telegram
```

---

## TESTING PROTOCOL — MANDATORY BEFORE LIVE

### Phase 1: Paper Test (VST Demo) — 3 Days Minimum

- Same code, same parameters
- Base URL: `https://open-api-vst.bingx.com`
- Single toggle in config: `demo_mode: true`
- Verify: orders place correctly, SL/TP attach, position monitor works, state.json updates, Telegram fires
- Confirm signal counts match backtester expectations

### Phase 2: Live Micro Test — Week 1

- $1,000 account, $50 positions
- Grade A signals ONLY
- Max 2 coins
- Max 2 simultaneous positions
- Daily loss limit: $50
- Review after 50 trades minimum

### Phase 3: Normal Live — Week 3+

- Grade A + B if week 1-2 is profitable
- Max 3 coins
- Max 3 simultaneous positions
- Daily loss limit: $75
- Add 3rd coin after 100 trades with positive expectancy

---

## OPEN QUESTIONS — MUST RESOLVE BEFORE BUILD

1. **Coin list:** Which 3 coins pass the dashboard sweep? (Sweep RIVERUSDT, GUNUSDT, AXSUSDT first)
2. **TP vs runner:** Fixed ATR TP, or let winners run (no TP, trail with Cloud 4)? RIVER sweep shows runner outperforms fixed TP at 2.0 ATR level — decision needed.
3. **Grade filter:** A only or A+B for live? A only = fewer trades, higher quality. A+B = more frequency but more noise.
4. **Strategy version:** v3.8.4 or wait for v3.8.5 (Cloud 4 trail fix)? Cloud 4 trail is documented as 8x improvement. Deploy with what's tested.
5. **Breakeven logic:** BE raise = 4 ATR confirmed for RIVER. Other coins need their own BE values from sweep.
6. **n8n dependency:** Architecture above is standalone Python (no n8n). Confirm: is n8n needed here, or is it only for TradingView webhook path?

---

## FILES TO CREATE (WHEN BUILD IS APPROVED)

| File | Location | Purpose |
|------|----------|---------|
| `bingx-live-bot/main.py` | Jacky VPS | Entry point |
| `bingx-live-bot/bingx_auth.py` | Jacky VPS | HMAC auth utility |
| `bingx-live-bot/data_fetcher.py` | Jacky VPS | OHLCV polling |
| `bingx-live-bot/signal_engine.py` | Jacky VPS | Signal computation |
| `bingx-live-bot/risk_gate.py` | Jacky VPS | Risk enforcement |
| `bingx-live-bot/executor.py` | Jacky VPS | Order placement |
| `bingx-live-bot/position_monitor.py` | Jacky VPS | Position tracking |
| `bingx-live-bot/state_manager.py` | Jacky VPS | State + trade log |
| `bingx-live-bot/notifier.py` | Jacky VPS | Telegram alerts |
| `bingx-live-bot/config.yaml` | Jacky VPS | Bot config |
| `BINGX-API-REFERENCE.md` | Obsidian PROJECTS | Confirmed endpoints |

All code built in Claude Code / VS Code. NOT in this desktop chat.

---

## NEXT ACTIONS IN SEQUENCE

**1. Strategy review (THIS SESSION or next)**
   - Run dashboard sweep on RIVERUSDT, GUNUSDT, AXSUSDT (5m timeframe)
   - Compare runner vs TP=2.0 ATR variant
   - Lock: sl_atr_mult, tp_atr_mult, be_raise, allowed_grades
   - Decision: Grade A only or A+B

**2. Coin selection (after strategy review)**
   - Any coin with expectancy > $1.00/trade at $500 notional (will scale to $50)
   - Lock final coin list (2–3 max)

**3. Build approval (after coin selection)**
   - Review this document with locked parameters filled in
   - Confirm deployment approach
   - Give go-ahead for Claude Code build

**4. Build on Jacky (Claude Code)**
   - All files listed above
   - VST demo test first (3 days minimum)
   - Then live

---

*Tags: #architecture #bingx #live-trading #four-pillars #2026-02-20*
