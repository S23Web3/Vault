# Plan — WEEX Futures Screener v1

## Context

TradingView Premium's CEX screener filters by absolute ATR (dollar value), which makes
cross-coin comparison meaningless — a $63k BTC and a $0.01 RIVER coin can't share the
same ATR threshold. The Four Pillars strategy requires normalised ATR (ATR / price) to
assess commission viability, plus strategy-specific signal state (stoch_60 zone, cloud
direction, pullback position) that TradingView has no concept of.

This screener fills that gap: live WEEX futures data, Four Pillars signal pipeline,
strategy-derived thresholds instead of arbitrary dollar values.

---

## What It Does

1. Fetch full WEEX perpetual futures symbol list from the WEEX public API
2. For each symbol: fetch 300 bars of recent OHLCV (5m default)
3. Run `compute_signals_v383` on that data — same pipeline as the dashboard
4. Extract live signal state: ATR ratio, stoch values, cloud position, current grade
5. Display ranked table with strategy-relevant columns
6. Sidebar filters — all derived from strategy math, not arbitrary values
7. Optional: auto-refresh on timer

No backtest. No parquet files. Pure live signal state from WEEX.

---

## WEEX API (confirmed, public — no API keys needed)

| Purpose | Endpoint | Format |
|---------|----------|--------|
| All futures symbols | `GET https://api-contract.weex.com/capi/v2/market/contracts` | `cmt_btcusdt` |
| OHLCV (candles) | `GET https://api-spot.weex.com/api/v2/market/candles?symbol=BTCUSDT_SPBL&period=5m&limit=300` | `BTCUSDT_SPBL` |
| All tickers (24h data) | `GET https://api-spot.weex.com/api/v2/market/tickers` | price, 24h change%, vol |
| Single ticker | `GET https://api-spot.weex.com/api/v2/market/ticker?symbol=BTCUSDT_SPBL` | |

Rate limit: 500 req / 10s. Intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d.

**Symbol format note:** Contract list uses `cmt_btcusdt`, OHLCV uses `BTCUSDT_SPBL`.
Fetcher must handle both. `BTCUSDT` → `BTCUSDT_SPBL` for candles.

**Gap to verify at implementation:** Confirm whether futures OHLCV uses the spot
candles endpoint or a separate contract candles endpoint.

---

## ATR Ratio Threshold — Derived, Not Arbitrary

```
min_atr_ratio = (taker_rate * 2) / tp_mult * safety_factor

WEEX taker rate:  0.10% (0.001)  — verify user's actual tier
TP mult default:  2.0 ATR
Safety factor:    3x
Result:           (0.001 * 2) / 2.0 * 3 = 0.003
```

At this threshold, TP revenue = 3x round-trip commission. Below it, edge is eaten.
The sidebar shows the formula, not just the number.

---

## Screener Columns (what matters for the strategy)

| Column | Computation | What it means |
|--------|-------------|---------------|
| `atr_ratio` | `mean(atr) / mean(close)` last 200 bars | Commission viability — normalised, cross-coin comparable |
| `stoch_60` | Last bar value | Macro state — < 25 or > 75 = in setup zone |
| `stoch_9` | Last bar value | Entry trigger proximity |
| `cloud3_dir` | `cloud3_bull` last bar | Trend direction (bull/bear) |
| `price_pos` | -1 / 0 / +1 | Price below / inside / above cloud3 |
| `signal_now` | Last bar grade: A/B/C/D/R or None | Is a signal firing right now? |
| `24h_change_pct` | From ticker API | Has it pumped recently? |
| `24h_vol_usd` | From ticker API | Liquidity check |
| `vol_change_pct` | From ticker API | Unusual volume activity |

---

## Sidebar Filters

| Filter | Default | Derived from |
|--------|---------|--------------|
| Min ATR ratio | 0.003 | Commission math (shown as formula) |
| Min 24h volume USD | $1M | Liquidity minimum |
| Stoch 60 zone | < 25 long / > 75 short | Strategy zone definition |
| Cloud direction | Any / Bull only / Bear only | cloud3_bull |
| Signal firing | Any / Only active signals | long_a/b/c/d on last bar |
| Timeframe | 5m (default), 1m, 15m | OHLCV fetch interval |
| Auto-refresh | Off / 1m / 5m / 15m | Polling interval |

---

## Files to Build

### 1. NEW — `utils/weex_fetcher.py`
- `get_futures_symbols() -> list[str]` — fetch all WEEX perpetual futures
- `get_ohlcv(symbol, interval, limit) -> pd.DataFrame` — fetch candles, return standard OHLCV df (columns: open/high/low/close/base_vol/quote_vol/datetime)
- `get_all_tickers() -> dict[str, dict]` — fetch 24h price/vol/change for all symbols
- Handles symbol format conversion (`BTCUSDT` ↔ `BTCUSDT_SPBL` ↔ `cmt_btcusdt`)
- Rate limit: `time.sleep(0.02)` between calls (50 req/s, well under 500/10s limit)

### 2. NEW — `utils/weex_screener_engine.py`
- `screen_symbol(symbol, interval, limit, signal_params, thresholds) -> dict`
  - Calls weex_fetcher to get OHLCV
  - Runs `compute_signals_v383(df, signal_params)` — reuses existing pipeline
  - Extracts: atr_ratio, stoch_60, stoch_9, cloud3_bull, price_pos, signal_now
  - Merges with ticker data (24h change, vol, vol change)
  - Returns metric dict — no backtest
- `run_weex_screener(symbols, interval, limit, signal_params, thresholds) -> pd.DataFrame`

### 3. NEW — `scripts/weex_screener_v1.py`
- Streamlit app
- Startup: fetch symbol list + all tickers (two API calls)
- Incremental loop: one symbol per `st.rerun()` (same pattern as screener_v1.py)
- Table: sortable, colour-coded by signal_now and stoch_60 zone
- Auto-refresh: `time.sleep` + `st.rerun()` timer
- No export needed (this is a watch tool, not a connector feed)

### 4. NEW — `tests/test_weex_fetcher.py`
- `get_futures_symbols()` returns list, len > 0
- `get_ohlcv("BTCUSDT", "5m", 100)` returns DataFrame with 100 rows, correct columns
- `get_all_tickers()` returns dict, BTCUSDT present
- Rate limit: confirm 50 calls complete without 429

---

## Reused Code (no new indicator logic)

```python
# Same import as dashboard_v392.py line 57
from signals.four_pillars_v383_v2 import compute_signals_v383

# Same default params as dashboard_v392.py lines 653-692
from utils.screener_engine import DEFAULT_SIGNAL_PARAMS
```

Minimum bars for full signal validity: **69** (60 for K4 + 9 for D smooth).
Default fetch: 300 bars — well above minimum, gives stable EMA clouds too.

---

## Key Differences from Current screener_v1.py

| | screener_v1.py (built) | weex_screener_v1.py (this plan) |
|---|---|---|
| Data source | Local Bybit parquets | Live WEEX API |
| Exchange | Bybit (399 cached coins) | WEEX (all futures, live) |
| Metric | 30d backtest PnL | Live signal state |
| Refresh | Manual re-run | Auto-refresh option |
| Purpose | Backtest-based eligibility | Live setup detection |

---

## Verification

1. `py_compile` all new .py files
2. `python tests/test_weex_fetcher.py` — API connectivity, correct columns, no 429
3. `streamlit run scripts/weex_screener_v1.py` — loads symbol list, runs 5 coins manually
4. Verify WHITEWHALE and RIVER appear (confirmed eligible from screener_v1.py results)
5. Verify ATR ratio column is normalised (RIVER ~0.009, BTC ~0.0003 — not same dollar value)

---

## Open Question Before Build

WEEX taker rate for user's account tier — defaults to 0.10% (0.001) but affects
the derived ATR ratio threshold formula shown in sidebar. Verify at build time.
