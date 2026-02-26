# Build Journal — 2026-02-13

## Session: 3-Year Historical Data + CoinGecko Comprehensive Fetch

**Started**: 2026-02-13 ~12:00
**Goal**: Download 3 years of OHLCV data (2023-2026) for all 399 coins + CoinGecko market cap, volume, categories, metadata

---

### Deliverables Built

| # | File | Purpose | Status |
|---|------|---------|--------|
| 1 | `scripts/download_periods.py` | Bybit historical OHLCV downloader (2 periods) | TESTED, VERIFIED |
| 2 | `scripts/fetch_market_caps.py` | CoinGecko historical market cap (v1, superseded) | TESTED |
| 3 | `scripts/fetch_coingecko_v2.py` | Comprehensive CoinGecko fetcher (5 actions) | TESTED, VERIFIED |
| 4 | `ml/features_v2.py` | 26-feature extractor (14 orig + 8 volume + 4 market cap) | TESTED |
| 5 | `data/period_loader.py` | Multi-period data concat utility | TESTED |
| 6 | `scripts/test_download_periods.py` | Tests for downloader | 17/17 PASS |
| 7 | `scripts/test_fetch_market_caps.py` | Tests for market cap fetcher | 20/20 PASS |
| 8 | `scripts/test_features_v2.py` | Tests for features_v2 | 56/56 PASS |
| 9 | `scripts/test_period_loader.py` | Tests for period loader | 18/18 PASS |

**Total tests: 111/111 passed**

---

### Real Download Test (2024-2025 period, 3 coins)

```
[12:18:01] BTCUSDT: 527,041 bars, 22.6 MB
[12:20:26] ETHUSDT: 527,041 bars, 21.3 MB
[12:22:46] SOLUSDT: 527,041 bars, 18.4 MB
TOTAL: 1,581,123 bars, 62.3 MB, 7.1 min
```

---

### CoinGecko v2 Fetch Test (3 coins, 30 days)

```
ACTION 1: Per-coin market cap + volume    — 3 OK, 0 no data
ACTION 2: Global market history           — 31 daily rows
ACTION 3: Category master list            — 667 categories
ACTION 4: Coin detail (ATH, launch, etc)  — 3 coins, 36 fields each
ACTION 5: Top gainers/losers + trending   — 30+30+15
TOTAL: 10 API calls, 0 errors, 6 seconds
```

**CoinGecko API key**: Added to `.env` (Analyst plan, 1000 req/min, expires 2026-03-03)

---

### Data Quality Verification

| File | Rows | Columns | Nulls | Dupes |
|------|------|---------|-------|-------|
| `coin_market_history.parquet` | 81,530 | 4 | 0 | 0 |
| `global_market_history.parquet` | 31 | 3 | 0 | 0 |
| `coin_categories.json` | 667 cats | 6 fields | n/a | n/a |
| `coin_metadata.json` | 3 coins | 36 fields | n/a | n/a |
| `top_movers.json` | 75 entries | varies | n/a | n/a |

---

### File Organization

```
data/
  cache/                    — UNTOUCHED (existing 2025-2026, ~6.2 GB)
  periods/
    2023-2024/              — NEW (pending full download)
    2024-2025/              — 3 coins downloaded (BTC, ETH, SOL)
  coingecko/                — NEW
    coin_market_history.parquet
    global_market_history.parquet
    coin_categories.json
    coin_metadata.json
    top_movers.json
    _fetch_state_v2.json
    _fetch_log.txt
```

---

### New ML Features (features_v2.py)

**Volume (8 new)**: vol_ratio_5, vol_ratio_50, vol_ratio_200, vol_trend, vol_zscore, quote_vol_ratio, vol_price_corr, relative_spread

**Market Cap (4 new)**: log_market_cap, log_daily_turnover, market_cap_rank, turnover_to_cap_ratio

**Total**: 14 original + 12 new = 26 features

---

### Pending Full Runs

```
# CoinGecko full (all 394 coins, 3 years) — ~3 min, ~792 API calls
python scripts/fetch_coingecko_v2.py --reset

# Bybit 2023-2024 (all 399 coins) — ~2.5 hours
python scripts/download_periods.py --period 2023-2024

# Bybit 2024-2025 (all 399 coins) — ~4.5 hours
python scripts/download_periods.py --period 2024-2025
```

---

### API Budget

- CoinGecko: ~792 calls needed / 500,000 available (0.16%)
- Bybit: Free public API, no limit concerns at 0.1s rate

---

## Session 2: download_periods_v2.py + Docstring Standard

**Started**: 2026-02-13 ~14:00

### CoinGecko Full Run Complete

- 792 API calls, 0 errors, 10 min
- 394/394 coins OK across all 5 actions
- Output: 5.1 MB (coin history), 28.3 KB (global), 152.4 KB (categories), 638 KB (metadata), 23.1 KB (movers)

### download_periods_v2.py Built

| File | Purpose | Status |
|------|---------|--------|
| `scripts/download_periods_v2.py` | Bybit downloader with CG smart filter + --all flag | BUILT |
| `scripts/test_download_periods_v2.py` | Tests for v2 | BUILT |

**v2 changes from v1:**
- `--all` flag: chains 2023-2024 then 2024-2025 in one run
- `--yes` flag: skip confirmation prompt
- CoinGecko smart filtering: reads `coin_market_history.parquet` to find earliest date per coin, skips coins not listed before period end
- All functions have docstrings (new standard)

### New MEMORY Standard

- **ALL FUNCTIONS MUST HAVE DOCSTRINGS** -- added to BUILD WORKFLOW hard rules

### Run Commands

```
python scripts/test_download_periods_v2.py
python scripts/download_periods_v2.py --all --yes
```
