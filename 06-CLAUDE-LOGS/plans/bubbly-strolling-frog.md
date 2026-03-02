# Parquet Data Catch-Up — 2026-02-28

## Context
User needs to update 1m candle parquet files. Last fetch was 2026-02-13 (15 days stale). Data source is Bybit v5 API. No code changes required — existing fetch_data.py handles incremental updates.

## Status: No Build Needed

The existing infrastructure handles this:
- **Script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_data.py`
- **Fetcher**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\fetcher.py` (BybitFetcher class)
- **Cache**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\` (399 coins, 1m only)

## Run Command

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/fetch_data.py --months 1
```

- Restartable (skips complete symbols via .meta files)
- Rate limited at 0.1s between requests
- Only fetches missing candles since 2026-02-13
- 5m candles: skipped per user decision (1m only)

## Verification
- After run completes, check summary output for `Symbols fetched: 399/399`
- Spot-check a .meta file to confirm end date is 2026-02-28
