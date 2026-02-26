# Current State — 2026-02-25
**Step 1 COMPLETE**: 67/67 tests passing. Bot running on BingX VST demo.
**Current task**: Fix leverage Hedge mode warning in main.py before first signal fires.

---

# Leverage Hedge Mode Fix — main.py

## Context
Bot is running. On startup, `set_leverage_and_margin()` sends `side=BOTH` for each coin.
BingX VST account is in Hedge mode — requires `side=LONG` and `side=SHORT` sent separately.
Current output: `WARNING Leverage fail RIVER-USDT: In the Hedge mode, the 'Side' field can only be set to LONG or SHORT`
Without this fix, leverage may be unset when first trade fires.

## File
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py`

## Change Required
In `set_leverage_and_margin()` (lines 52-85), replace the single `side=BOTH` request with two requests per symbol: one with `side=LONG`, one with `side=SHORT`.

### Current code (lines 54-70):
```python
for symbol in symbols:
    req = auth.build_signed_request("POST", LEVERAGE_PATH, {
        "symbol": symbol,
        "side": "BOTH",
        "leverage": str(leverage),
    })
    try:
        resp = requests.post(req["url"], headers=req["headers"], timeout=10)
        data = resp.json()
        if data.get("code", 0) == 0:
            logger.info("Leverage: %s -> %dx", symbol, leverage)
        else:
            logger.warning("Leverage fail %s: %s", symbol, data.get("msg"))
    except Exception as e:
        logger.error("Leverage error %s: %s", symbol, e)
```

### Replacement:
```python
for symbol in symbols:
    for side in ("LONG", "SHORT"):
        req = auth.build_signed_request("POST", LEVERAGE_PATH, {
            "symbol": symbol,
            "side": side,
            "leverage": str(leverage),
        })
        try:
            resp = requests.post(req["url"], headers=req["headers"], timeout=10)
            data = resp.json()
            if data.get("code", 0) == 0:
                logger.info("Leverage: %s %s -> %dx", symbol, side, leverage)
            else:
                logger.warning("Leverage fail %s %s: %s", symbol, side, data.get("msg"))
        except Exception as e:
            logger.error("Leverage error %s %s: %s", symbol, side, e)
```

## Verification
Restart bot. Startup log should show:
```
Leverage: RIVER-USDT LONG -> 10x
Leverage: RIVER-USDT SHORT -> 10x
Leverage: GUN-USDT LONG -> 10x
...
```
No leverage warnings.

## Other pending items (not code — user actions)
- Fill in `.env` with real `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
- Regenerate BingX secret key (was partially visible in screenshot shared in chat)

---

# Step 1 Build Plan — COMPLETE (archived)
**Derived from:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\COUNTDOWN-TO-LIVE.md`
**Scope:** Minimum fixes to get demo trades firing. No screener. No strategy changes.

---

## Fix 1 — executor.py `_round_down` test expectation
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py`
**Finding:** The function at line 123 already uses `math.floor(value / step) * step` — the fix is already in place.
**Actual bug:** The failing test in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` line 178 has an incorrect assertion — it expects `99.99` from float arithmetic that produces `99.99000000000001`. The function is correct; the test is wrong.
**Fix:** In `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_executor.py` at the `test_round_down` assertion, use `assertAlmostEqual(result, 99.99, places=8)` instead of `assertEqual`.
**Lines to change:** test_executor.py — the assertEqual at line 178 only.

## Fix 2 — test_integration.py missing price mock in `test_entry_then_close`
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py`
**Finding:** `test_entry_then_close` at line 92 mocks `mock_eg.side_effect` with 2 responses (price + step size) for the entry. But `executor.execute()` makes a price GET call before placing the order. The monitor's `check()` also calls GET for positions. The mock runs out of responses mid-test — executor fails silently, position never records, trades.csv never written, test fails at line 113.
**Fix:** Add a third entry to `mock_eg.side_effect` at line 94 — a positions response — so the monitor's GET has a response. Specifically, after the 2 executor GET mocks, the monitor needs `_resp({"code": 0, "data": []})` as a third side_effect entry for `mock_eg` OR confirm `mock_mg` is correctly patching `position_monitor.requests.get` (it patches a different namespace, which is correct — the real issue is the executor GET side_effect is exhausted before the order POST succeeds because `_safe_get` for step size fails when mock runs out).

## Fix 3 — config.yaml plugin switch
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`
**Current:** `strategy: plugin: "mock_strategy"`
**Change to:**
```yaml
strategy:
  plugin: "four_pillars_v384"

four_pillars:
  allow_a: true
  allow_b: true
  allow_c: false
  sl_atr_mult: 2.0
  tp_atr_mult: null
```
**Note:** This is a config edit, not a code change. No test rewrite needed for this.

## Verification
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python -m pytest tests/ -v
```
All 67 must pass before proceeding.

Then:
```
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py"
```
Bot starts, connects BingX VST demo, logs warmup progress. No signal expected for ~16h (200 bars × 5m).

---

# Full Pipeline Scope — Four Pillars Live Trading
**Date:** 2026-02-24
**Goal:** End-to-end scope from coin discovery to live trades on BingX

---

## Context

The BingX connector infrastructure is built and 64/67 tests pass. The strategy plugin
(FourPillarsV384) is built but not wired to a live coin source. The missing piece is a
screener that automatically discovers and ranks coins, then feeds them to the connector.
This document scopes everything needed to go from current state to live trades.

---

## Current State Audit

### What exists and works
| File | Path | Status | Does it do what it should? |
|------|------|--------|---------------------------|
| `bingx_auth.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx_auth.py` | COMPLETE | YES — HMAC-SHA256, param sorting, header injection |
| `data_fetcher.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\data_fetcher.py` | COMPLETE | YES — 200-bar rolling OHLCV buffer, new-bar detection |
| `signal_engine.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\signal_engine.py` | COMPLETE | YES — dynamic plugin load, warmup check, grade filtering |
| `risk_gate.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\risk_gate.py` | COMPLETE | YES — 6 ordered checks, halt_flag, duplicate detection |
| `executor.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` | COMPLETE | YES — qty calc, SL+TP attached, MARK_PRICE mode |
| `position_monitor.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` | COMPLETE | YES — 60s poll, close detection, daily reset at 17:00 UTC |
| `state_manager.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py` | COMPLETE | YES — state.json + trades.csv, crash recovery |
| `notifier.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\notifier.py` | COMPLETE | YES — Telegram send, no business logic |
| `plugins/four_pillars_v384.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\four_pillars_v384.py` | COMPLETE | YES — wraps compute_signals, A/B/C grades, ATR SL/TP |
| `plugins/mock_strategy.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\plugins\mock_strategy.py` | COMPLETE | YES — random/injectable signals for testing |
| `main.py` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` | COMPLETE | PARTIAL — loads coins from config.yaml only, no dynamic reload |

### Known bugs (non-blocking for demo, must fix before live)
| Bug | File | Line | Severity | Fix |
|-----|------|------|----------|-----|
| Float precision `99.99 != 99.99` | `executor.py` | 178 | LOW | Use `math.floor(value/step) * step` |
| Integration test mock incomplete | `tests/test_integration.py` | 113 | LOW | Fix mock for `_safe_get()` price response |

### Configuration gaps (must fix before switching from mock to live)
| Gap | File | What is missing |
|-----|------|----------------|
| Plugin still set to `mock_strategy` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | Change to `four_pillars_v384` |
| No `four_pillars` config block | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | Add `allow_a`, `allow_b`, `allow_c`, `sl_atr_mult`, `tp_atr_mult` |
| Coins are 3 hardcoded test coins | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml` | Will be replaced by screener → `active_coins.json` |
| `active_coins.json` does not exist | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\active_coins.json` | Screener must create and maintain this file |
| `main.py` does not read `active_coins.json` | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` | Must add startup read of `active_coins.json` if it exists |

---

## What Needs to Be Built

### Build 1 — BingX Screener
Scans all BingX perpetual futures coins. Filters to pre-breakout setups. Writes shortlist to `active_coins.json`.

**Files:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\utils\bingx_screener_fetcher.py`
  - `get_symbols()` → list of all BingX perpetual futures symbols
  - `get_ohlcv(symbol, period, limit)` → DataFrame (reuses BingX public klines endpoint)
  - `get_tickers()` → dict of 24h vol + price change per symbol
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\utils\screener_engine.py`
  - `scan_symbol(symbol)` → dict of signal metrics (stoch_60, stoch_9, cloud3_dir, price_pos, atr_ratio, signal_now)
  - `scan_all(symbols)` → DataFrame of all results
  - Reuses: `compute_signals_v383` from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\utils\coin_ranker.py`
  - `apply_filters(df, params)` → filtered DataFrame
  - `rank_coins(df)` → sorted by setup quality score
  - `write_active_coins(df, path)` → writes `active_coins.json` with symbol + metadata
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\live_screener_v1.py`
  - Streamlit table: symbol, price, 24h_change_pct, vol, atr_ratio, stoch_60, stoch_9, cloud3_dir, price_pos, signal_now
  - Sidebar filters: min ATR ratio, min vol USD, stoch_60 zone, cloud direction, signal active
  - Hybrid sweep: startup = all coins, delta loop = only changed coins
  - Writes `active_coins.json` on every sweep cycle
  - Ollama scorer (optional, qwen3:8b): scores delta coins only with `SYMBOL:GRADE:URGENCY` format

**active_coins.json format:**
```json
[
  {
    "symbol": "RIVER-USDT",
    "atr_ratio": 0.0041,
    "stoch_60": 18.2,
    "stoch_9": 24.1,
    "cloud3_dir": "bull",
    "signal_now": "A",
    "urgency": 2,
    "updated_at": "2026-02-24T14:32:00Z"
  }
]
```

---

### Build 2 — main.py patch (active_coins.json reader)
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` must:
1. On startup: check if `active_coins.json` exists. If yes, load symbols from it. If no, fall back to `config.yaml` coins list.
2. Existing config.yaml coins list becomes the fallback only — not removed.
3. No dynamic reload during runtime (too complex, out of scope). Restart bot when screener updates the list.

---

### Build 3 — config.yaml update
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config.yaml`:
- Switch `strategy.plugin` from `mock_strategy` → `four_pillars_v384`
- Add `four_pillars` block: `allow_a: true`, `allow_b: true`, `allow_c: false`, `sl_atr_mult: 2.0`, `tp_atr_mult: null`

---

### Build 4 — Fix 2 failing tests (pre-live requirement)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` — fix `_round_down()` float precision
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\tests\test_integration.py` — fix mock price response

---

## Ollama Layer (optional, non-blocking)
- Model: qwen3:8b (already installed, RTX 3060 12GB, full GPU inference)
- Role: visual audit only — labels coins in screener UI, does NOT affect `active_coins.json` content
- Fires: on startup full sweep (one-time, ~50s for all coins) and on delta changes only (~3s per cycle)
- Output: `SYMBOL:GRADE:URGENCY` — one line per coin, parsed in Python
- If Ollama offline: screener and bot continue unaffected

---

## Reused Code
| Pattern | Source | Function |
|---------|--------|----------|
| Signal computation | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\signals\four_pillars_v383_v2.py` | `compute_signals_v383` |
| BingX public klines | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\data_fetcher.py` | klines endpoint pattern |
| Ollama call + retry | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\analyzer.py` lines 50-69 | `call_ollama()` |
| Ollama health check | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\startup.py` lines 38-53 | `check_ollama()` |
| thinking strip | `C:\Users\User\Documents\Obsidian Vault\PROJECTS\yt-transcript-analyzer\analyzer.py` lines 31-33 | `strip_thinking()` |

---

## Time to Live Trades — Honest Estimate

### What is already done (zero sessions needed)
- Connector infrastructure: COMPLETE
- FourPillarsV384 plugin: COMPLETE
- Tests: 64/67 passing

### What needs building (sessions estimate)
| Build | Complexity | Sessions |
|-------|-----------|----------|
| Build 3 — config.yaml update | Trivial | 0 (5 min manual edit) |
| Build 2 — main.py patch (active_coins.json reader) | Small | 0.5 (part of screener session) |
| Build 4 — fix 2 failing tests | Small | 0.5 |
| Build 1 — BingX Screener (no Ollama) | Medium | 1-2 |
| Ollama scorer layer | Small (optional) | 0.5 |

### Path to first demo trade (minimum viable)
1. Edit `config.yaml` → switch plugin to `four_pillars_v384`, add four_pillars block (5 min manual)
2. Fix 2 failing tests (1 session)
3. Run connector in demo mode with current 3 hardcoded coins → confirm real signals fire and demo orders place

**That is 1 session away.** No screener needed for demo trades.

### Path to live trades with dynamic coin selection
1. Steps above (1 session)
2. Build screener → writes `active_coins.json` (1-2 sessions)
3. Patch `main.py` to read `active_coins.json` (part of screener session)
4. Switch `demo_mode: false` in `config.yaml`
5. Deploy to Jacky VPS

**Total: 2-3 sessions from now.**

---

## Verification Plan
1. **Demo signal test**: Switch config to `four_pillars_v384`, run `python main.py`, confirm A/B signal fires on RIVER-USDT within first 200-bar warmup. Check Telegram alert received.
2. **active_coins.json test**: Run screener, confirm file created at `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\active_coins.json`, confirm bot picks up coins from it on restart.
3. **End-to-end demo**: Screener running → shortlist written → bot restarted → real signal fires → demo order placed on BingX VST → position appears in BingX demo account.
4. **Test gate**: All 67 tests must pass before switching `demo_mode: false`.

