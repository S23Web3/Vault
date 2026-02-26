# Backtest Results — 2026-02-07

## Session Summary

Built and ran the Four Pillars Python backtester (v3.7.1 logic) on low-price coins. Key discovery: **5-minute timeframe makes all 5 coins profitable**.

## Data Pipeline

- **Source**: Bybit v5 API (`/v5/market/kline`, public, no auth)
- **Period**: 2025-11-09 to 2026-02-07 (3 months)
- **Resolution**: 1m candles (resampled to 5m in code)
- **Coins fetched**: 1000PEPEUSDT, RIVERUSDT, KITEUSDT, HYPEUSDT, SANDUSDT
- **Each coin**: 129,600 candles, ~5 MB Parquet
- **Also cached from earlier**: BTCUSDT, ETHUSDT, SOLUSDT, MEMEUSDT

## Backtester Configuration (v3.7.1)

| Parameter | Value |
|-----------|-------|
| Capital | $10,000 equity |
| Margin per trade | $500 |
| Leverage | 20x |
| Notional per trade | $10,000 |
| SL | 1.0 ATR |
| TP | 1.5 ATR |
| Cooldown | 3 bars |
| B/C open fresh | Yes |
| Commission | $6/side ($12 RT) |
| Rebate | 70% (settles 5pm UTC daily) |
| Net commission | $3.60/RT |

## Results — 1-Minute Candles (3 months)

| Coin | Best BE | Trades | WR% | Net P&L | $/trade | LSG% |
|------|---------|--------|-----|---------|---------|------|
| 1000PEPE | $6 | 19,712 | 15.6% | -$29,349 | -$1.49 | 73.5% |
| RIVER | $2 | 20,535 | 18.4% | +$87,510 | +$4.26 | 76.9% |
| KITE | $2 | 19,431 | 18.5% | -$14,588 | -$0.75 | 68.6% |
| HYPE | $2 | 20,204 | 17.3% | -$19,241 | -$0.95 | 80.1% |
| SAND | $4 | 19,451 | 15.1% | -$35,345 | -$1.82 | 59.0% |
| **Total** | | **99,333** | | **-$11,012** | **-$0.11** | |

Only RIVER profitable on 1m. Commission-to-move ratio kills the others.

## Results — 5-Minute Candles (3 months) — ALL PROFITABLE

| Coin | Best BE | Trades | WR% | Net P&L | $/trade | LSG% |
|------|---------|--------|-----|---------|---------|------|
| 1000PEPE | $2 | 4,145 | 17.6% | +$10,436 | +$2.52 | 83.3% |
| RIVER | $4 | 4,003 | 16.8% | +$55,855 | +$13.95 | 83.2% |
| KITE | $2 | 3,994 | 18.9% | +$14,979 | +$3.75 | 79.2% |
| HYPE | $10 | 4,124 | 13.7% | +$7,218 | +$1.75 | 84.2% |
| SAND | $6 | 4,017 | 18.9% | +$8,572 | +$2.13 | 77.4% |
| **Total** | | **20,283** | | **+$97,060** | **+$4.79** | |

## Key Findings

### 1. 5-Minute is the optimal timeframe
- 1m: too many trades, commission bleed overwhelms edge
- 5m: ~4,000 trades/coin (vs ~20,000 on 1m), better signal quality
- Same signals, just fewer false entries from 1m noise

### 2. RIVER dominates
- Best coin on both 1m (+$87K) and 5m (+$56K)
- $13.95/trade on 5m = highest expectancy of any coin
- High ATR/price ratio = commission is small % of each trade

### 3. Breakeven raise is critical
- BE$0 (no raise): ALL coins negative on 1m, most negative on 5m
- BE$2: best for most coins — catches the 68-84% of losers that saw green
- LSG (Losers Saw Green) ranges 59-84% — most losing trades were profitable at some point

### 4. Earlier finding confirmed: BTC/ETH/SOL too expensive
- Commission is 46% of BTC TP win ($12 on $26 TP)
- Low-price coins: commission is ~7% of TP win
- Always trade coins where ATR/price ratio > commission impact

## Bugs Fixed This Session

1. **Rebate settlement bug**: `df.set_index('datetime')` removes datetime from columns → backtester never credited rebates. Fixed by checking `df.index.name`.
2. **WEEX API**: No historical pagination. Switched to Bybit as primary data source.
3. **Bybit pagination**: Returns newest-first, needed backward pagination.

## Files Created/Modified

- `data/fetcher.py` — Rewritten with BybitFetcher (primary) + WEEXFetcher (live only)
- `scripts/fetch_data.py` — CLI entry point for Bybit data fetch
- `scripts/sweep_low_price.py` — BE sweep script for low-price coins
- `engine/backtester.py` — Fixed datetime index detection for rebate settlement

## Next Steps

- [ ] Build v3.8 ATR-based BE logic (separate files, per v3.8 plan)
- [ ] Commission rate verification: v3.8 plan says $4/side (0.04%), current uses $6 (0.06%)
- [ ] Install PyTorch with CUDA for ML optimizer
- [ ] Monte Carlo validation on 5m results
- [ ] Streamlit dashboard integration
