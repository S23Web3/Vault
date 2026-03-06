# Plan: Daily Bybit Data Updater Script

## Context

The backtester's data cache (399 coins, `data/cache/`) is stale -- last updated 2026-02-13 (1m files to ~Feb 28). The user wants a **daily-run script** that:

1. Discovers all active USDT linear perpetuals from Bybit API
2. Incrementally fetches only NEW candles since last cached timestamp for each coin
3. Resamples updated 1m data to 5m
4. Can be run daily from terminal (or scheduled via Task Scheduler)

## Approach: New Standalone Script (not patching fetch_data.py)

A daily updater is a different use case than the batch fetcher. Rather than patching `fetch_data.py` (which is designed for initial bulk downloads), build a new standalone script purpose-built for daily incremental updates. This follows the existing pattern -- `fetch_sub_1b.py` is also standalone, not a patch of `fetch_data.py`.

## Build Script

**File**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_updater.py`

Creates: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_update.py`

## What daily_update.py Does

### Step 1: Discover symbols from Bybit
- Hit `GET /v5/market/instruments-info?category=linear&limit=1000`
- Filter: `status == "Trading"` and `symbol.endswith("USDT")`
- Compare against existing cache (`data/cache/*_1m.parquet`)
- Report: X total active, Y already cached, Z new

### Step 2: Incremental fetch for each symbol
For each symbol (existing + new):
- **If cached**: read `.meta` file to get `cached_end_ms`. Fetch only from `cached_end_ms` to now. Append new candles to existing parquet. Update `.meta`.
- **If new (no cache)**: full fetch from `--months` back (default 12). Save new parquet + `.meta`.
- Rate limiting: 0.12s between requests (matches `fetch_sub_1b.py` pattern)
- Retry logic: 3 retries with exponential backoff on rate limit / timeout

### Step 3: Resample to 5m
- Import `TimeframeResampler` from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\resample_timeframes.py`
- Call `resample_file(symbol, "5m", overwrite=True)` for each updated symbol
- Only resample symbols that were actually fetched (skip unchanged)

### Step 4: Summary + log
- Print totals: updated / new / skipped / failed
- Log to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\logs\YYYY-MM-DD-daily-update.log`
- Dual handler: file + console (per MEMORY.md logging standard)

## CLI Interface

```
python scripts/daily_update.py                    # Default: update all, 12-month lookback for new coins
python scripts/daily_update.py --months 6         # 6-month lookback for new coins
python scripts/daily_update.py --skip-new         # Only update existing cached coins, skip new discoveries
python scripts/daily_update.py --skip-resample    # Skip 5m resampling step
python scripts/daily_update.py --max-new 50       # Cap how many new coins to add per run
python scripts/daily_update.py --dry-run          # Show what would be fetched without fetching
```

## Key Design Decisions

1. **Standalone script, not a patch** -- Cleaner than bolting `--discover --incremental --resample` onto `fetch_data.py`. The daily updater has a different lifecycle (run unattended daily vs. manual bulk fetch).

2. **Reuses existing modules** -- Imports `BybitFetcher` from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\fetcher.py` for the core fetch logic (pagination, parquet save). Imports `TimeframeResampler` from `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\resample_timeframes.py` for 5m resampling. No code duplication.

3. **Incremental append is new logic** -- The existing `BybitFetcher.fetch_symbol()` does full re-fetch if range doesn't match. The daily updater adds an `incremental_fetch()` function that reads the existing parquet, fetches only the gap, concatenates, deduplicates, and saves. This logic lives in `daily_update.py` itself (not patched into `fetcher.py`) to keep the existing fetcher stable.

4. **Symbol discovery reuses proven pattern** -- `fetch_sub_1b.py` line 113-126 already has `get_bybit_symbols()` calling the same API. We replicate this pattern (not import it, since that script has CoinGecko coupling we don't want).

## Files Modified / Created

| File | Action |
|------|--------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_updater.py` | NEW -- build script |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_update.py` | NEW -- daily updater (created by build) |

No existing files are modified.

## Verification

1. Build script runs `py_compile.compile(path, doraise=True)` + `ast.parse()` on generated file
2. User runs: `python scripts/daily_update.py --dry-run` to verify discovery + incremental plan without fetching
3. User runs: `python scripts/daily_update.py --max-new 5` to test with a small batch first
4. Full run: `python scripts/daily_update.py` (takes ~5-10 min for existing coins gap fill, longer for new coins)

## Run Command

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/build_daily_updater.py
python scripts/daily_update.py --dry-run
```
