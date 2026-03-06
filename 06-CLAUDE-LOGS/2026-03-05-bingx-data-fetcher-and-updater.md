# 2026-03-05 — BingX OHLCV Data Fetcher & Daily Updater

## Session Summary

Continued from 2026-03-04 session. Built BingX OHLCV bulk fetcher (fetch_bingx_ohlcv.py) and daily incremental updater (daily_bingx_update.py). Fixed progress bar issues. Built autorun scheduler.

## What Was Built

### 1. BingX OHLCV Bulk Fetcher (started 2026-03-04, progress bar fixes 2026-03-05)

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_fetch_bingx.py`
**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_bingx_ohlcv.py`

- Discovers all BingX USDT perpetual futures (~626 coins)
- Fetches 1m OHLCV data going back 12 months per coin
- Saves to `data/bingx/` as parquet + .meta (uniform format matching Bybit)
- Also resamples and saves 5m parquets
- Schema: timestamp(int64), open, high, low, close, base_vol, quote_vol(NaN), datetime(UTC)
- Progress bars: outer (coins, fractional advancement) + inner (per-coin %)
- Empty streak optimization: skips forward 10x through unlisted periods
- CLI: --dry-run, --symbol, --max-coins, --months, --skip-existing, --output-dir, --resume-from

**Bug fixes applied (from audit)**:
- BUG-1: Removed unused `import os`
- BUG-2: HTTP 5xx errors now retried (not just 429)
- BUG-3: Partial data logged with warning
- BUG-5: quote_vol NaN preserved in 5m resample
- BUG-6: dropna on "close" (not "open") matching normalizer convention

**Progress bar fix (2026-03-05)**:
- Outer bar was stuck at 0/626 while first coin downloaded
- Fixed: outer bar now advances fractionally via `_update_outer()` — each coin's inner progress drives the outer bar proportionally
- `fetch_symbol_full()` accepts `coin_bar` and `coin_base` params

### 2. BingX Daily Updater

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_bingx_updater.py`
**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_bingx_update.py`

- Imports all fetch functions from fetch_bingx_ohlcv.py (zero code duplication)
- Reads .meta files to find last cached timestamp per coin
- Fetches only the gap (cached_end -> now), merges with existing parquet
- Discovers new coins not yet cached, fetches full history for those
- Skips coins less than 2 hours behind (considered current)
- CLI: --dry-run, --skip-new, --skip-resample, --max-new N, --months N
- Logs to: `logs/YYYY-MM-DD-bingx-daily-update.log`

### 3. Autorun Scheduler

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_data_scheduler.py`
**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\data_scheduler.py`

- Runs both Bybit and BingX daily updaters on a timed schedule
- Default: every 6 hours (configurable via --interval)
- Runs immediately on start, then repeats
- CLI: --interval N, --bingx-only, --bybit-only, --once
- Logs to: `logs/YYYY-MM-DD-data-scheduler.log`
- Designed to run in background terminal

## Run Commands

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Build all scripts
python scripts/build_fetch_bingx.py
python scripts/build_daily_bingx_updater.py
python scripts/build_data_scheduler.py

# Bulk fetch (first time, ~52 hours)
python scripts/fetch_bingx_ohlcv.py --skip-existing

# Daily update (incremental)
python scripts/daily_bingx_update.py --dry-run
python scripts/daily_bingx_update.py

# Autorun scheduler
python scripts/data_scheduler.py
python scripts/data_scheduler.py --interval 12
python scripts/data_scheduler.py --bingx-only --once
```

## Files Created

| File | Action |
|------|--------|
| `scripts/build_fetch_bingx.py` | UPDATED (progress bar, bug fixes, tqdm import) |
| `scripts/fetch_bingx_ohlcv.py` | UPDATED (fractional outer bar, all bug fixes) |
| `scripts/build_daily_bingx_updater.py` | NEW |
| `scripts/daily_bingx_update.py` | Created by build script |
| `scripts/build_data_scheduler.py` | NEW |
| `scripts/data_scheduler.py` | Created by build script |

## Data Layout

- **Bybit**: `data/cache/` — 399 coins, stale since 2026-02-13
- **BingX**: `data/bingx/` — 626 coins (bulk fetch in progress), ~292 completed as of session start
- Both use identical parquet schema (8 columns) + .meta files (start_ms,end_ms)
- BingX quote_vol = NaN (API doesn't provide turnover)
