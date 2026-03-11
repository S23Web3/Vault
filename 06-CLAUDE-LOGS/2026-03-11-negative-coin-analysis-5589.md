# Session Log: 55/89 Negative Coin Deep Analysis
**Date:** 2026-03-11
**Duration:** ~10 min
**Model:** Claude Opus 4

---

## Objective

Run the pre-written `analyze_negative_coins_5589.py` script against the full data range for 9 coins, identify negative-PnL coins, classify failure modes per trade, and produce FARTCOINUSDT deep dive.

## What Happened

1. Read the analysis prompt at `plans/2026-03-10-fartcoin-trade-analysis-prompt.md`
2. Verified source files: `engine/backtester_55_89.py` (trade record fields), existing script at `scripts/analyze_negative_coins_5589.py` (903 lines, comprehensive, includes Plotly charts)
3. Confirmed all 9 parquet files exist in `data/historical/`
4. Found `.venv312` (not `.venv`) as the Python environment
5. `py_compile` PASS
6. First run failed: `UnicodeEncodeError` on `\u2192` (arrow character) in Windows cp1252 terminal
7. Second run with `PYTHONIOENCODING=utf-8` -- full success

## Key Results

### Portfolio (P0-fixed params, full data range)

| Coin | Trades | WR | Net PnL |
|------|--------|-----|---------|
| FARTCOINUSDT | 2,193 | 28.1% | -$60,107 |
| ORDERUSDT | 1,084 | 30.1% | -$24,647 |
| BBUSDT | 1,037 | 28.8% | -$22,983 |
| TRUMPUSDT | 459 | 30.1% | -$13,959 |
| OGUSDT | 686 | 29.9% | -$12,723 |
| CVCUSDT | 453 | 30.9% | -$11,391 |
| CHZUSDT | 330 | 33.9% | -$2,224 |
| BIGTIMEUSDT | 581 | 34.4% | -$1,468 |
| FILUSDT | 396 | 35.9% | +$986 |

**8 of 9 coins negative. Only FILUSDT positive.**

### Failure Mode Distribution (all 8 negative coins, losers only)

| Mode | Count | % |
|------|-------|---|
| COUNTER_TREND | 3,705 | 77.4% |
| WEAK_ENTRY (Grade C) | 2,862 | 59.8% |
| PHASE2_GRAVEYARD | 2,363 | 49.4% |
| PHASE2_SAW_GREEN | 2,140 | 44.7% |
| PHASE1_INSTANT_DEATH | 1,251 | 26.1% |
| HIGH_ATR_ENTRY | 1,160 | 24.2% |
| RATCHET_INSUFFICIENT | 753 | 15.7% |
| MARGINAL_CROSS | 372 | 7.8% |

### FARTCOINUSDT Deep Dive

- 2,193 trades, 28.1% WR, -$60,107 net
- COUNTER_TREND: 73.7% of losers (entering against EMA 55/89 direction)
- 82.9% of losers saw green before losing (Phase 2 AVWAP freeze killing profitable trades)
- 58% Grade C entries (all with ~28% WR)
- ATR avg 0.534% (high volatility meme coin)
- Phase distribution: P2 SL 41%, TP 25.4%, P1 SL 15.5%, P3 SL 11.7%

### Critical Finding: COUNTER_TREND is Universal

The strategy enters against EMA 55/89 delta on 77% of all losing trades. This is not coin-specific -- it's consistent across all 8 negative coins. The overzone state machine does not check EMA alignment at entry.

### Top 3 Actionable Fixes (priority order)

1. **EMA ALIGNMENT GATE** -- Only enter LONG when `ema_delta > 0`, SHORT when `ema_delta < 0`. Addresses #1 failure mode.
2. **GRADE C FILTER** -- Block Grade C entries. WR is 28-30% across all coins. 55-64% of all trades are Grade C.
3. **PHASE 2 AVWAP CHECK** -- Before tightening SL at Phase 2 freeze, verify it won't be tighter than current Phase 1 SL.

### Grade C Performance (universal)

| Coin | Grade C % | Grade C WR |
|------|-----------|------------|
| CHZUSDT | 64% | 30% |
| ORDERUSDT | 63% | 30% |
| BIGTIMEUSDT | 62% | 32% |
| CVCUSDT | 62% | 30% |
| BBUSDT | 59% | 28% |
| FARTCOINUSDT | 58% | 28% |
| TRUMPUSDT | 57% | 29% |
| OGUSDT | 55% | 29% |

## Output Files

All in `PROJECTS/four-pillars-backtester/results/`:

| File | Content |
|------|---------|
| `negative_coins_analysis_5589_v20260311_175333.txt` | Full statistical report |
| `trade_contexts_negative_5589_v20260311_175333.csv` | Per-trade context CSV (6,823 trades) |
| `fartcoin_deep_dive_5589_v20260311_175333.txt` | FARTCOIN detail report |
| `trades_5589_<SYMBOL>_v20260311_175333.csv` | Per-coin trade CSVs (9 files) |
| `chart_failure_modes_20260311_175333.html` | Failure mode bar chart |
| `chart_fartcoin_ema_cross_20260311_175333.html` | FARTCOIN price + EMA + signals |
| `chart_atr_profile_20260311_175333.html` | ATR% box plots per coin |
| `chart_fartcoin_pnl_scatter_20260311_175333.html` | PnL scatter by failure mode |
| `chart_grade_winrate_20260311_175333.html` | WR by grade per coin |
| `chart_phase_exits_20260311_175333.html` | Phase exit stacked bar |

## Decisions / Next Steps

- FARTCOINUSDT: **EXCLUDE** from portfolio (high ATR, 28% WR, 58% Grade C)
- EMA alignment gate is the highest-leverage fix to implement next
- Grade C filter is second priority
- Phase 2 AVWAP tightening check is third

## Technical Notes

- Volume column missing from all parquet files (AVWAP tracker uses `np.ones` fallback)
- `.venv312` is the correct venv, not `.venv`
- Windows terminal requires `PYTHONIOENCODING=utf-8` for Unicode arrows in output
