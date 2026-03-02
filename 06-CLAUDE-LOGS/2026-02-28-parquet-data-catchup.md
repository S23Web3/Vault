# Parquet Data Catch-Up Session — 2026-02-28

## Task
Update 1m candle parquet files in backtester cache. Last fetch was 2026-02-13 (15 days stale).

## Findings
- **Data source**: Bybit v5 API (confirmed)
- **Cache location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\`
- **Cache contents**: 399 coins, 798 files (1m + 5m), 6.7 GB
- **Time span**: 2025-02-11 to 2026-02-13
- **Fetch script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_data.py`
- **Fetcher class**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\fetcher.py` (BybitFetcher)
- **5m candles**: existing fetcher only pulls 1m (hardcoded `interval: "1"`). 5m parquets were from a prior process. User decided 1m only for now.

## Bug Found
- `config.yaml` only lists 5 default coins (BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, MEMEUSDT)
- `--coins N` flag slices from config list, so `--coins 399` still yields 5
- No `--all` flag existed to discover symbols from cached parquets

## Fix Applied
- Added `--all` flag to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_data.py`
- When `--all` is passed, discovers all symbols from existing `*_1m.parquet` files in cache dir
- Errors out if no cached parquets found
- Moved `cache_dir` resolution above symbol determination so `--all` can glob the cache
- py_compile: PASS

## Run Command
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/fetch_data.py --months 1 --all
```

## Status
- Script updated, py_compile OK
- Awaiting user to run from terminal
