# 2026-03-03 — Daily Bybit Data Updater

## Session Summary

Built a daily-run script for updating the backtester's Bybit candle data cache. The cache (399 coins, `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\`) was stale since 2026-02-13.

## What Was Built

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_updater.py`
**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_update.py`

### daily_update.py Features

1. **Bybit symbol discovery** -- queries `/v5/market/instruments-info` for all active USDT linear perps (~548 symbols). Compares against existing cache, reports new/existing/delisted counts.
2. **Incremental fetch** -- reads `.meta` end timestamp per coin, fetches only the gap to now. No full re-fetch for existing coins. New coins get full `--months` lookback (default 12).
3. **5m resampling** -- imports `TimeframeResampler` from `resample_timeframes.py`, resamples only updated symbols.
4. **Dual logging** -- file (`logs/YYYY-MM-DD-daily-update.log`) + console, with timestamps.

### CLI Flags

- `--dry-run` -- preview without fetching
- `--skip-new` -- only update existing cached coins
- `--skip-resample` -- skip 5m resampling
- `--max-new N` -- cap new coin additions per run
- `--months N` -- lookback for new coins (default 12)

## Design Decisions

- **Standalone script**, not a patch of `fetch_data.py` -- different lifecycle (daily unattended vs manual bulk)
- **Reuses existing modules** -- `BybitFetcher` pattern for pagination, `TimeframeResampler` for 5m
- **Incremental append logic** lives in `daily_update.py` (not patched into `fetcher.py`) to keep existing fetcher stable
- **Symbol discovery** replicates `fetch_sub_1b.py` line 113-126 pattern (proven) without CoinGecko coupling

## Validation

- `py_compile` PASS on build script
- `ast.parse` PASS on embedded source
- Not yet executed by user

## Run Commands

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/build_daily_updater.py
python scripts/daily_update.py --dry-run
python scripts/daily_update.py
```

## Files Created

| File | Action |
|------|--------|
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_daily_updater.py` | NEW |
| `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\daily_update.py` | Created by build script (not yet executed) |

## Vault Updates (this session)

- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-backtester.md` -- added Daily Bybit Data Updater section
- `C:\Users\User\Documents\Obsidian Vault\LIVE-SYSTEM-STATUS.md` -- added daily updater, promoted dashboard v3.9.4, updated BingX detail to 2026-03-03
- `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md` -- added C.29 (Daily Bybit Data Updater)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-FILES.md` -- promoted v3.9.4 to production, v3.9.3 to prior stable
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-03-daily-bybit-updater.md` -- plan file
