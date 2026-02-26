# Plan: download_all_available.py

## Context

Current `download_1year_gap_FIXED.py` skips coins listed after 2025-02-11 (Bybit returns empty, script says "No data"). These newer coins only have their original 3-month fetch. Need all 399 coins to have ALL available data since 2025-11-02 (or listing date if later), in both Parquet and CSV.

## What Gets Built

**Single file**: `scripts/download_all_available.py`

## Safety: Backup Before Anything

Before touching ANY existing parquet file, the script:

1. Creates `data/cache_backup_YYYYMMDD_HHMMSS/` directory
2. Copies ALL existing `*_1m.parquet` and `*_1m.meta` files into it
3. Prints backup location and file count
4. Only proceeds after backup is verified (file count matches)

This protects days of cached data. If anything goes wrong, user restores from backup.

## Safety: Sanity Check on Merged Data

Before overwriting any parquet file, the script validates the merged DataFrame:

- Row count: merged must have >= rows as original (we are ADDING data, never removing)
- No null OHLC values in merged data
- No duplicate timestamps
- Timestamps sorted ascending
- Earliest timestamp <= original earliest (we only extend backward, never truncate)
- Latest timestamp >= original latest (we only extend forward, never truncate)

If ANY check fails for a symbol, the merge is SKIPPED for that symbol, original file untouched, error logged.

## How It Works

For each of 399 cached symbols:

1. Load existing `{SYMBOL}_1m.parquet` from cache
2. Get `earliest_ms` and `latest_ms` from the data
3. Fetch **backward gap**: 2025-11-02 to `(earliest_ms - 1min)` -- uses `_fetch_page()` directly (no file side-effects from `fetch_symbol()`)
4. Fetch **forward gap**: `(latest_ms + 1min)` to now -- same approach
5. If backward fetch returns empty (coin listed after 2025-11-02), that is fine -- coin keeps existing data + forward extension
6. Merge: `concat(backward_df, existing_df, forward_df)`, deduplicate on timestamp, sort ascending
7. **Run sanity checks on merged data** (see above). If fail, skip symbol.
8. Save merged Parquet to `data/cache/{SYMBOL}_1m.parquet`
9. Update `{SYMBOL}_1m.meta` with actual data range (min/max timestamp from data)
10. Resample 1m to 5m, save `{SYMBOL}_5m.parquet` + meta
11. Export `data/csv/{SYMBOL}_1m.csv` to new `data/csv/` directory

## Key Design Decisions

- **Backup first** -- full copy of existing cache before any writes
- **Sanity gate per symbol** -- merged data must pass 6 checks or original file is preserved
- **Uses `_fetch_page()` directly** -- avoids `fetch_symbol()` cache-overwrite side-effect
- **Bidirectional** -- fills backward AND forward gaps in one pass
- **Restartable** -- progress tracked in `data/cache/_download_progress.json`, completed symbols skipped on rerun
- **Rate limit safe** -- 0.05s/page, 1s between symbols, exponential backoff (10-160s) on rate limit

## Critical Files

| File | Role |
|------|------|
| [data/fetcher.py](PROJECTS/four-pillars-backtester/data/fetcher.py) | `BybitFetcher._fetch_page()` (lines 41-66) -- core pagination |
| [scripts/download_1year_gap_FIXED.py](PROJECTS/four-pillars-backtester/scripts/download_1year_gap_FIXED.py) | Existing pattern reference (concat + dedup + save) |
| [data/cache/](PROJECTS/four-pillars-backtester/data/cache/) | 399 existing parquet + meta files (BACKED UP before any writes) |

## Output at End of Script

```
BACKUP:  C:\...\data\cache_backup_20260213_143000\  (399 files)
PARQUET: C:\...\data\cache\
CSV:     C:\...\data\csv\

Run command:
  cd PROJECTS\four-pillars-backtester
  python scripts\download_all_available.py
```

## Run Command

```
cd PROJECTS\four-pillars-backtester
python scripts\download_all_available.py
```

Flags: `--force` (ignore progress, redo all), `--symbols BTCUSDT ETHUSDT` (specific coins), `--rate 0.1` (slower)

## Verification

1. Run the script -- confirm backup created first, then processing starts
2. Run `python scripts\sanity_check_cache.py` -- all coins should show COMPLETE or have earliest at actual listing date
3. Spot-check `data/csv/RIVERUSDT_1m.csv` has data from 2025-11-02
4. Spot-check a previously NEW_LISTING coin now has data from listing date to present
5. Compare file counts: backup dir vs cache dir should have same symbol count
