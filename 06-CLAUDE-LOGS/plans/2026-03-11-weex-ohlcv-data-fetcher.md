# Plan: WEEX OHLCV Data Fetcher

## Context

You have historical 1m OHLCV data from **Bybit** (~399 coins, `data/cache/`) and **BingX** (~626 coins, `data/bingx/`). You need the same from **WEEX** for backtesting.

**Problem**: The existing `WEEXFetcher` in `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\fetcher.py` (line 206) only pulls latest ~1,000 candles — no pagination, no `startTime`/`endTime`. Useless for backtesting.

**Known WEEX endpoints** (from `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-weex-screener-scope.md`):

- Contracts: `GET https://api-contract.weex.com/capi/v2/market/contracts`
- Contract candles: `GET https://api-contract.weex.com/capi/v2/market/candles?symbol=cmt_btcusdt&granularity=1m&limit=1000`
- Spot candles: `GET https://api-spot.weex.com/api/v2/market/candles?symbol=BTCUSDT_SPBL&period=5m&limit=300`

**Critical unknown**: Whether WEEX supports `startTime`/`endTime` pagination on any candle endpoint.

---

## Phase 1: API Probe Script (build first)

**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\probe_weex_api.py`

Build script that tests all WEEX candle endpoints with various pagination params:

1. **Contract candles** (`api-contract.weex.com/capi/v2/market/candles`)
   - Test with: `startTime`, `endTime`, `start`, `end`, `after`, `before` (ms timestamps)
   - Symbol: `cmt_btcusdt`

2. **Spot candles** (`api-spot.weex.com/api/v2/market/candles`)
   - Test with: `startTime`, `endTime`, `after`, `before`, `start`, `end`
   - Symbol: `BTCUSDT_SPBL`

3. **Contract candles v1** (`api.weex.com/api/v1/market/candles` — from build spec docs)
   - Test same params

For each test:

- Print HTTP status, response keys, first/last timestamp in data, total candle count
- Flag which param combos return older data vs just latest

**Output**: Console report saying "Endpoint X with params Y returns historical data: YES/NO"

**Run command**: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\probe_weex_api.py"`

---

## Phase 2: Full Fetcher (after probe confirms pagination)

Based on probe results, build the fetcher modeled on `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_bingx_ohlcv.py`.

### Files to Create

| Action | File                                                                     |
|--------|--------------------------------------------------------------------------|
| CREATE | `scripts/build_fetch_weex.py` — build script (creates all files below)  |
| CREATE | `scripts/fetch_weex_ohlcv.py` — bulk historical fetcher                 |
| CREATE | `scripts/daily_weex_update.py` — incremental updater                    |
| MODIFY | `scripts/data_scheduler.py` — add `--weex-only` flag, add to rotation  |

### Fetcher spec (`fetch_weex_ohlcv.py`)

- **Discover coins**: Hit contracts endpoint, filter USDT perps
- **Pagination**: Forward from `startTime` to `endTime` (exact params TBD by probe)
- **Rate limit**: 0.25s default, exponential backoff on 429
- **Output dir**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\weex\`
- **Output format**: `{SYMBOL}_1m.parquet` + `{SYMBOL}_5m.parquet` (resample)
- **Schema**: Identical 8-column format — `timestamp, open, high, low, close, base_vol, quote_vol, datetime`
- **CLI flags**: `--dry-run`, `--symbol`, `--max-coins N`, `--months N`, `--skip-existing`, `--resume-from SYMBOL`
- **Logging**: `logs/YYYY-MM-DD-weex-fetch.log` + console (dual handler, timestamps)

### Daily updater spec (`daily_weex_update.py`)

- Read existing parquets, find last timestamp per coin
- Fetch only new candles since then
- Append + deduplicate + resample 5m
- CLI flags: `--dry-run`, `--skip-new`, `--skip-resample`, `--max-new N`

### Fallback (if probe shows NO pagination)

If WEEX has no historical pagination on any endpoint:

- **Option A**: Start collecting from today, accumulate over time
- **Option B**: Check if Bitget API works (same subdomain pattern, documented pagination)
- **Option C**: Use Bybit data as backtesting proxy, WEEX for live screening only
- User decides which path after seeing probe results

---

## Verification

1. Run probe script — confirms which endpoint + params support pagination
2. `python scripts/fetch_weex_ohlcv.py --symbol BTCUSDT --months 1` — fetch 1 month BTC
3. Verify parquet schema matches: `pd.read_parquet("data/weex/BTCUSDT_1m.parquet").dtypes`
4. `python scripts/fetch_weex_ohlcv.py --max-coins 5 --months 3` — batch test
5. `python scripts/daily_weex_update.py --dry-run` — confirm incremental logic

## Reuse

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_bingx_ohlcv.py` — template for fetcher structure, pagination loop, parquet save, resample logic
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_bingx_update.py` — template for daily updater
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\fetcher.py` line 206 `WEEXFetcher` — existing symbol format conversion (`to_api_symbol`)
