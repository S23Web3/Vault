# Build Journal — 2026-02-12

## Session Summary

**Duration**: ~1 hour
**Model**: Claude Opus 4.6
**Outcome**: Data infrastructure complete, git pushed, memory organized

---

## What Was Done

### 1. Bybit Fetcher — Rate Limit Fix
- **Problem**: `_fetch_page()` returned empty list on rate limit, `fetch_symbol()` treated it as "no data" and stopped
- **Fix**: `_fetch_page()` now returns `(candles, rate_limited)` tuple. `fetch_symbol()` retries with exponential backoff (10s, 20s, 40s, 80s, 160s) up to 5 attempts
- **File**: `data/fetcher.py`

### 2. Download Speed — 20x Faster
- **Problem**: `RATE_LIMIT = 1.0` (1 req/s) was absurdly conservative. Bybit allows 600 req per 5s per IP = 120/s
- **Fix**: Changed to `0.05s` (20 req/s). Kept 1s pause between symbols
- **File**: `scripts/download_1year_gap_FIXED.py`
- **Source**: https://bybit-exchange.github.io/docs/v5/rate-limit

### 3. Sanity Check Script
- **Created**: `scripts/sanity_check_cache.py`
- **Categories**: COMPLETE (data starts at/before target), PARTIAL (gap < 200d, retryable), NEW_LISTING (gap >= 200d, coin didn't exist)
- **Outputs**: Summary stats + writes `data/cache/_retry_symbols.txt` for download retry mode

### 4. Download Retry Mode
- **Added**: `--retry` flag to `download_1year_gap_FIXED.py`
- **Reads**: `_retry_symbols.txt` instead of scanning all 399 symbols
- **Result**: 8 coins had real data to download (ARKM, AXL, DODO, EGLD, JST, MEME, MOVE, ORBS). 32 others were newer listings with no earlier data

### 5. Data Collection — COMPLETE
- **399 coins cached**, 124.8M total bars, ~6.2 GB
- **169 coins**: Full 1-year history (back to 2025-02-11)
- **230 coins**: Newer listings, have ALL available Bybit data
- **0 quality issues**: No dupes, no null OHLC, no read errors

### 6. Git Push to GitHub
- **Problem**: `PROJECTS/four-pillars-backtester/` was not a git repo. `Desktop/ni9htw4lker/` was an empty clone
- **Fix**: Initialized git in backtester dir, merged with remote history (Pine Script indicators v2-v3.7.1)
- **Committed**: 148 Python files + 28 Pine Script files
- **Repo**: https://github.com/S23Web3/ni9htw4lker on `main` branch
- **Identity**: S23Web3 / malik@shortcut23.com (repo-local config)
- **.gitignore**: data/cache/, data/historical/, .env, __pycache__, *.meta, nul
- **Note**: `nul` file (0-byte Windows artifact) excluded from git

### 7. Memory Files — Moved to Obsidian Vault
- Copied from `.claude/projects/.../memory/` to vault root:
  - `BUILD-JOURNAL-2026-02-10.md`
  - `build_journal_2026-02-11.md`
  - `SETTINGS-AND-COMPLIANCE-REPORT.md`
  - `book_analysis_log.md`
- Updated MEMORY.md to reference vault root as canonical location

### 8. MEMORY.md Updates
- Added 70% chat limit rule (compaction causes save errors)
- Added Data Collection Status section
- Added Git Setup section
- Added Pending Builds list (P1-P5) with scope and permissions for each
- Updated Logs & Journals section to point to vault root

---

## Files Modified
- `data/fetcher.py` — rate limit retry logic
- `scripts/download_1year_gap_FIXED.py` — 0.05s rate, --retry mode, 1s between symbols
- `.gitignore` — added data/historical/, *.meta, nul

## Files Created
- `scripts/sanity_check_cache.py` — cache validation and categorization

## Pending (User Runs From Terminal)
- `python scripts/build_staging.py` — Deploy 4 staging files (P1)
- `python staging/test_dashboard_ml.py` — Verify ML dashboard tabs

---

## Pending Builds (Carried Forward)

### P1: Deploy Staging Files
- Run: `python scripts/build_staging.py`
- Verify: `python staging/test_dashboard_ml.py`

### P2: ML Meta-Label on D+R Grades (HIGHEST IMPACT)
- D=-$3.59/tr, R=-$3.00/tr. Combined drag -$3,323
- XGBoost filter to skip bad D/R trades

### P3: Multi-Coin Portfolio Optimization
- Add PEPE, SAND, HYPE to capital analysis

### P4: 400-Coin ML Sweep
- XGBoost meta-label across all 399 coins on 5m
- 2-4 hours GPU

### P5: Live TradingView Validation
- Compare Pine v3.8 signals vs Python backtester

---

## Session 2: Dashboard Overhaul + Data Normalizer (2026-02-12, late)

**Duration**: ~2 sessions (spanned context limit, resumed)
**Model**: Claude Opus 4.6
**Outcome**: Dashboard rewritten with mode navigation, sweep persistence, data normalizer built

### Plan
Merged 6 tasks from BUILD-NORMALIZER-3PHASE.md spec + user conversation requests.
Plan file: `.claude/plans/elegant-enchanting-wilkinson.md`

### Task 1: Data Normalizer (`data/normalizer.py`) -- NEW FILE
- Universal OHLCV CSV-to-parquet normalizer (~370 lines)
- Auto-detect: delimiter (csv.Sniffer), columns (fuzzy match 6 exchange formats), timestamps (epoch ms/s/ISO/datetime strings), interval (median diff)
- Validation: no dupes, OHLC sanity, sorted ascending, gap detection
- Output: `{SYMBOL}_{interval}.parquet` + `.meta` file matching fetcher.py format
- If 1m input, also auto-saves 5m resampled version
- Handles BOM, trailing comma, mixed case, extra columns

### Task 2: CLI Conversion Utility (`scripts/convert_csv.py`) -- NEW FILE
- Wraps OHLCVNormalizer for command-line use (~150 lines)
- Flags: `--input`, `--symbol`, `--preview`, `--batch`, `--columns` (JSON override), `--interval`, `--resample`, `--cache-dir`
- Prints summary: format detected, rows, period, saved files + sizes

### Task 3: Dashboard Mode Navigation (`scripts/dashboard.py`) -- EDIT
- Replaced fragile `if run_test / elif not run_batch / else` with session_state mode machine
- Modes: `settings | single | sweep | sweep_detail`
- Back buttons on every non-settings view
- Dropped "Test Run" button, kept "Run Backtest" + "Sweep ALL coins"
- Results cached in session_state (navigating back doesn't re-run)

### Task 4: Sweep Persistence + Auto-Resume (`scripts/dashboard.py`) -- EDIT
- `SWEEP_PROGRESS` CSV in `data/output/` with params_hash column
- `compute_params_hash()`: 8-char MD5 of all signal+bt params+timeframe
- Incremental: process ONE coin per `st.rerun()` cycle (non-blocking)
- Auto-resume: load CSV on entering sweep mode, skip completed coins
- Param change = hash mismatch = fresh sweep
- Drill-down: selectbox from results -> "View Detail" -> sweep_detail mode with 5-tab view

### Task 5: Sweep Coin List + Data Upload (`scripts/dashboard.py`) -- EDIT
- Sweep source radio: `[All Cache] [Custom List] [Upload Data]`
- **All Cache**: scans data/cache/*.parquet (current behavior)
- **Custom List**: file uploader for .txt/.csv/.json. Parses symbols, validates against cache, shows found/missing
- **Upload Data**: file uploader for .csv, runs `detect_format()` preview (delimiter, interval, rows, timestamp format, column map), symbol name input, "Convert & Add to Sweep" button
- Updated `get_cached_symbols()`: now scans all intervals (`*_1m`, `*_5m`, `*_15m`, etc.), deduplicates
- Updated `load_data()`: tries native `{symbol}_{timeframe}.parquet` first, falls back to 1m + resample

### Task 6: LSG Bars Metric (`scripts/dashboard.py`) -- EDIT
- `compute_avg_green_bars(trades_df, df_sig)`: walks entry_bar->exit_bar for saw_green losers, counts bars with unrealized P&L > 0
- Displayed in Tab 1 metrics (both single and sweep_detail modes)
- Added to sweep results table as "LSG_Bars" column

### Task 7: Test Scripts
- `scripts/test_normalizer.py` (NEW, ~450 lines, 17 tests): delimiter detection, column mapping (6 exchanges), timestamp parsing, interval detection, normalize (Bybit/Binance/TradingView/epoch-s), 5m detection, BOM handling, missing volume error, missing quote_vol NaN, duplicate removal, OHLC validation warnings, batch normalize, column override, integration pipeline
- `scripts/test_sweep.py` (NEW, ~300 lines, 11 tests): params hash determinism, CSV write/read, CSV resume, hash filter, avg green bars (long/short/no-losers), mode transitions, get_cached_symbols multi-interval, coin list parsing (txt/csv/json), metrics completeness (real RIVERUSDT backtest)

### Files Summary

| File | Action | Size |
|------|--------|------|
| `data/normalizer.py` | NEW | ~370L |
| `scripts/convert_csv.py` | NEW | ~150L |
| `scripts/test_normalizer.py` | NEW | ~450L |
| `scripts/test_sweep.py` | NEW | ~300L |
| `scripts/dashboard.py` | EDITED | ~1450L (was 1129L) |

### Run Commands (user runs from terminal)
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/test_normalizer.py
python scripts/test_sweep.py
streamlit run scripts/dashboard.py
```

### Key Design Decisions
- Sweep is NON-BLOCKING: 1 coin per st.rerun() cycle. User can navigate away.
- Auto-resume from CSV: no manual "Resume" button. Just re-enter sweep mode.
- 5-tab detail is UNIVERSAL: same view for single coin and sweep drill-down.
- Normalizer output matches fetcher.py exactly: same parquet schema, same .meta format.
- `get_cached_symbols()` no longer depends on fetcher's `list_cached()` (which only finds `*_1m`). Dashboard scans all interval suffixes directly.

---

## Session 3: Code Review + Bug Fixes + Test Validation (2026-02-12, late)

**Duration**: ~30 min
**Model**: Claude Opus 4.6
**Outcome**: All builds verified bug-free, all tests passing

### Bugs Found and Fixed

#### Bug 1: `ts_ms` undefined in normalizer validate block (`data/normalizer.py`)
- **Problem**: In `detect_format()`, if timestamp parsing failed in the try/except, `ts_ms` was never assigned. The validate block referenced `ts_ms`, causing a NameError silently caught by the outer try/except.
- **Fix**: Added `ts_ms = None` initialization before the try block. Changed validate condition to `if not missing and ts_ms is not None:`.

#### Bug 2: `"1D"` resample rule deprecated (`data/normalizer.py`)
- **Problem**: `resample("1D")` generates FutureWarning on pandas 2.2+.
- **Fix**: Changed to `"1d"` (lowercase) in rule_map.

#### Bug 3: Test expectation mismatch (`scripts/test_normalizer.py`)
- **Problem**: Test expected `_detect_timestamp_format` to return `"%Y-%m-%d %H:%M:%S"` for space-separated timestamps, but pandas 2.x `format="ISO8601"` accepts them, so the function returns `"ISO8601"`.
- **Fix**: Changed test to accept either format: `fmt in ("ISO8601", "%Y-%m-%d %H:%M:%S")`.

### Test Results (Final)

| Suite | Tests | Passed | Failed |
|-------|-------|--------|--------|
| `test_normalizer.py` | 47 | 47 | 0 |
| `test_sweep.py` | 37 | 37 | 0 |
| **Total** | **84** | **84** | **0** |

### Files Modified
- `data/normalizer.py` -- 2 bug fixes (ts_ms init, 1d resample rule)
- `scripts/test_normalizer.py` -- 1 test fix (accept ISO8601 for datetime strings)

### Status: ALL BUILDS VERIFIED
- data/normalizer.py -- CLEAN
- scripts/convert_csv.py -- CLEAN
- scripts/dashboard.py -- CLEAN
- scripts/test_normalizer.py -- 47/47 PASS
- scripts/test_sweep.py -- 37/37 PASS

---

## Session 4: Scoping P1-P5 (2026-02-12, end of day)

**Duration**: ~15 min
**Model**: Claude Opus 4.6
**Outcome**: All 5 pending builds scoped with permissions. No code written.

### P1: Deploy Staging Files -- CONFLICT DETECTED
- `staging/dashboard.py` is STALE (41KB, pre-Session 2). Deploying would overwrite all Session 2 work.
- Only useful piece: `staging/ml/live_pipeline.py` -> `ml/live_pipeline.py`
- Recommendation: Deploy only live_pipeline.py, skip rest

### P2: ML Meta-Label on D+R Grades -- READY TO BUILD
- All 9 ML modules in `ml/` are built (features, meta_label, xgboost_trainer, shap, purged_cv, etc.)
- `trades_df` exposes `grade` column (A/B/C/D/ADD/RE/R) from backtester_v384.py
- `features.py` extracts 14 features at entry time
- Need: orchestration script `scripts/ml_meta_label_dr.py` + test
- Impact: Fix D=-$3.59/tr, R=-$3.00/tr drag (-$3,323 combined)

### P3: Multi-Coin Portfolio Optimization -- TRIVIAL
- `capital_analysis_v384.py` already accepts `--coins` arg dynamically
- All 3 new coins (1000PEPEUSDT, SANDUSDT, HYPEUSDT) have 5m data cached
- Only change: add per-coin TP config (currently uniform TP across all coins)
- Versioned file: `capital_analysis_v385.py`

### P4: 400-Coin ML Sweep -- LARGE BUILD
- Loop all 399 cached coins on 5m, run backtest + XGBoost meta-label
- Rank coins by ML-filtered net P&L
- Depends on P2 working first
- Estimated 2-4 hours GPU runtime (user runs from terminal)

### P5: Live TradingView Validation -- MANUAL DEPENDENCY
- Requires TV trade export (manual step)
- Script to parse TV CSV, align with Python backtest, diff signals
- Blocked until user provides TV export data

### Recommended Build Order
P2 > P3 > P4 > P1(live_pipeline only) > P5
