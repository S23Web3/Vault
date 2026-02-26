# Session Log — 2026-02-24 — WEEX Screener Scope

## What Was Built This Session

### Vince Screener v1 (built, but wrong approach)
- `utils/screener_engine.py` — runs full backtest per coin on last 30 days
- `scripts/screener_v1.py` — Streamlit app, incremental loop
- `tests/test_screener_engine.py` — 22/22 tests passed
- `bingx-connector/main.py` — patched to read active_coins.json

**Problem:** This screener runs the backtester on historical data to rank coins by
past PnL. It answers "which coins were profitable recently?" That is backwards-looking
and dominated by market regime noise. TradingView Premium already does live market
scanning better. The screener_v1.py added no real value over TradingView's CEX screener.

---

## What Is Actually Needed

**A WEEX live market screener** — like TradingView's CEX screener but with
Four Pillars-specific metrics that TradingView cannot provide:

1. **Normalised ATR ratio** (ATR / price) — cross-coin comparable. TradingView uses
   absolute dollar ATR which makes BTC ($2000 ATR) and RIVER ($0.07 ATR) incomparable.
2. **Four Pillars signal state** — current stoch values (9, 14, 40, 60), cloud3 direction,
   price position (above/inside/below cloud), current signal grade (A/B/C/D or none).
3. **Setup detection** — is this coin in pullback after a pump, with signals ready to fire?

**What it is NOT:**
- Not a backtester
- Not a trade executor
- No commission math, no taker/maker rates (it's a screener, not a trader)
- Not BingX (user is on WEEX for this tool)

---

## WEEX API Research (confirmed — no auth needed for market data)

| Purpose | Endpoint |
|---------|----------|
| All futures symbols | `GET https://api-contract.weex.com/capi/v2/market/contracts` |
| OHLCV (candles) | `GET https://api-spot.weex.com/api/v2/market/candles?symbol=BTCUSDT_SPBL&period=5m&limit=300` |
| All tickers (24h) | `GET https://api-spot.weex.com/api/v2/market/tickers` |

Rate limit: 500 req / 10s. Intervals: 1m, 5m, 15m, 30m, 1h, 4h, 1d.

Symbol format: contract list = `cmt_btcusdt`, OHLCV = `BTCUSDT_SPBL`.
Conversion: `BTCUSDT` → `BTCUSDT_SPBL` (append `_SPBL`).

**Open question:** Confirm whether the futures candles endpoint is different from
the spot candles endpoint. May need to test both at build time.

---

## Signal Code Confirmed (from explore agent)

- Import: `from signals.four_pillars_v383_v2 import compute_signals_v383`
- Minimum bars for full signal validity: **69** (60 for K4 + 9 for D smooth)
- Default fetch: 300 bars — safe margin above minimum
- Signal columns relevant to screener: `stoch_9`, `stoch_60`, `cloud3_bull`,
  `cloud3_allows_long`, `cloud3_allows_short`, `price_pos`, `long_a/b/c/d`,
  `short_a/b/c/d`, `atr`

---

## Next Session: Scope First, Then Build

### Scope for WEEX Screener v1

**Files (3 max):**
1. `utils/weex_fetcher.py` — public API client: symbol list, OHLCV, tickers
2. `utils/weex_screener_engine.py` — fetch + run signals + extract metrics per symbol
3. `scripts/weex_screener_v1.py` — Streamlit table with auto-refresh

**Columns to show:**
- symbol, price, 24h_change_pct, 24h_vol_usd, vol_change_pct
- atr_ratio (normalised), stoch_60, stoch_9, cloud3_dir, price_pos, signal_now

**Filters (sidebar):**
- Min ATR ratio (default 0.003)
- Min 24h volume USD (default $1M)
- Stoch 60 in zone (< 25 long / > 75 short)
- Cloud direction (any / bull / bear)
- Signal active (any / only coins with grade firing now)
- Timeframe (5m default)
- Auto-refresh interval

**Reuses:** `compute_signals_v383` and `DEFAULT_SIGNAL_PARAMS` from existing codebase.
No backtest. No commission math.

### Do NOT include:
- Taker/maker rates (not relevant for a screener)
- Backtest PnL
- Export to connector (separate concern)
- Any BingX references

### Start next session with:
"Read `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md`
then scope the WEEX screener build — no code until scope is approved."
