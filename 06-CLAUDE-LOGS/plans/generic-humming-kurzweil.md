# Plan: Historical Fetcher + main.py Cleanup

## Context

- **Telegram**: Already connected via `notifier.py` — working correctly.
- **Historical pull**: Not implemented in the live bot. `data_fetcher.py` only maintains 200-bar in-memory buffers. No persistence.
- **main.py**: 228 lines — the `set_leverage_and_margin()` function (~32 lines) is the main extraction candidate.

---

## Task 1: Create `historical_fetcher.py`

**File**: `PROJECTS/bingx-connector/historical_fetcher.py`

### Purpose
Standalone script (also importable) to pull full historical OHLCV data for any coin from BingX and save as parquet.

### Design
- Uses BingX v3 public endpoint: `/openApi/swap/v3/quote/klines` (same as `data_fetcher.py` — no auth needed)
- Paginates using `startTime` / `endTime` params (BingX max `limit` is 1440 per call)
- Fetches backward from now until configured start date (or N days)
- Saves to `data/historical/{symbol}_{timeframe}.parquet`
- Deduplicates by timestamp on re-run (idempotent)
- Creates `data/historical/` directory if missing

### Parquet schema
| column | dtype   |
|--------|---------|
| time   | int64   |
| open   | float64 |
| high   | float64 |
| low    | float64 |
| close  | float64 |
| volume | float64 |

### CLI usage
```
python historical_fetcher.py --symbol BTC-USDT --timeframe 5m --days 90
python historical_fetcher.py  # uses coins from config.yaml, default 90 days
```

### As a utility (importable)
```python
from historical_fetcher import fetch_and_save
fetch_and_save(symbol="BTC-USDT", timeframe="5m", days=90)
```

---

## Task 2: Extract `set_leverage_and_margin()` from `main.py`

**Move to**: `PROJECTS/bingx-connector/exchange_setup.py`

### What moves
- The `set_leverage_and_margin()` function (currently lines ~63-94 of main.py)
- Constants: `LEVERAGE_PATH`, `MARGIN_TYPE_PATH`

### Why
- It makes direct HTTP API calls — exchange API logic, not orchestration
- `main.py` should only wire components together, not make raw API calls itself
- After extraction, `main.py` imports and calls `set_leverage_and_margin(auth, symbols, leverage, margin_mode)`

### main.py change
- Remove the function and constants
- Add `from exchange_setup import set_leverage_and_margin`
- Call site in `main()` stays identical

---

## Files Modified / Created

| File | Action |
|------|--------|
| `historical_fetcher.py` | **Create new** |
| `exchange_setup.py` | **Create new** |
| `main.py` | **Edit** — remove `set_leverage_and_margin` + constants, add import |

---

## Verification

1. Run `python historical_fetcher.py --symbol BTC-USDT --timeframe 5m --days 5` — check `data/historical/BTC-USDT_5m.parquet` is created
2. Re-run same command — verify no duplicate rows (deduplication works)
3. Run `python main.py` in demo mode — verify leverage/margin setup still logs correctly
4. Check Telegram still receives startup message
