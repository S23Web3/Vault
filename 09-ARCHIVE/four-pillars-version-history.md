# Four Pillars Version History
# Extracted from MEMORY.md on 2026-02-13 to reduce main memory under 200 lines.
# This file is reference-only. Current version: v3.8.4.

---

## v3.5.1
- Cloud 3 trail — bled out

## v3.6
- AVWAP SL — bled out
- Indicator: `02-STRATEGY/Indicators/four_pillars_v3_6.pine`

## v3.7 Architecture (Rebate Farming)
- Goal: ~3000 trades/month, flat equity, commission rebates = profit
- Tight SL/TP: 1.0 ATR SL, 1.5 ATR TP (no trailing)
- B/C open fresh: B (3/4 stochs) and C (2/4 + Cloud 3) can open new positions, not just add
- B/C can flip: When bOpenFresh is on, B/C signals flip direction too
- Free flips: No volume filter, instant direction change on any signal
- Cloud 2 re-entry: Broadened — tracks bars since ANY signal (A/B/C), not just A
- Single order ID: Back to v3.5 simplicity (strategy.position_size sync)
- pyramiding=1: One position at a time, fast turnover

## v3.7.1 Fixes (Commission Blow-Up)
- cash_per_order=8: Replaces commission.percent — deterministic $8/side, no leverage ambiguity
- No strategy.close_all(): Removed from all flips. strategy.entry() auto-reverses = 1 order not 2
- strategy.cancel() before flips: Clears stale exit orders that collide with new entries
- Cooldown (3 bars): Min bars between entries. Prevents 5 flips in 5 minutes
- cooldownOK gate: Applied to ALL entry conditions (A, BC, flip, re-entry)
- Dashboard Comm$ row: Shows running commission total
- Pine Strategy: `02-STRATEGY/Indicators/four_pillars_v3_7_1_strategy.pine`

## Phantom Trade Bug (v3.7 discovery)
- strategy.close_all() + strategy.entry() on SAME BAR = two trades: close ($0 P&L + commission) + new entry (commission)
- Fix: NEVER use strategy.close_all() for flips. strategy.entry() in opposite direction auto-reverses.
- Also: strategy.cancel() stale exit orders before flipping direction

## v3.8 (2026-02-10)
- Pine Strategy: `02-STRATEGY/Indicators/four_pillars_v3_8_strategy.pine`
- Pine Indicator: `02-STRATEGY/Indicators/four_pillars_v3_8.pine`
- Changes: Cloud 3 directional filter (ALWAYS ON), ATR-based BE raise, rate-based commission, MFE/MAE tracking
- Merged into production: `PROJECTS/four-pillars-backtester/signals/state_machine.py` + `clouds.py` updated
- RIVERUSDT 5m with Cloud 3 filter: 1,278 trades, +$18,952 net

## v3.8.3 (2026-02-11) — COMPLETE
- Entry logic overhaul: Zone trigger changed from 9-K to 60-K. A/B/C grading corrected. D signal added.
- D signal: Continuation while 60-K stays pinned in extreme. 9-K cycles -> D fires. No Cloud 3 needed. Can loop.
- SL overhaul: A/B/C/D = ATR * sl_mult (default 2.0, sweepable). ADD/RE = AVWAP 2sigma. Both switch to AVWAP center after 5 bars.
- Scale-out: Every 5 bars, if close at +2sigma -> close 50%. SL -> AVWAP center. Max 2 scale-outs. Replaces BE raise.
- AVWAP inheritance: ADD/RE slots clone parent's AVWAP accumulator state (not fresh).
- Best SL: 2.5 ATR (9/10 coins profitable). RIVER: +$6,261 ($3.29/tr), 1,901 trades.
- D+R grades drag P&L: D -$3.59/tr, R -$3.00/tr. Together drag -$3,323.
- LSG: 85-92% across all coins. Scale-out not enough — need TP or ML filter.
- Files: state_machine_v383.py, four_pillars_v383.py, position_v383.py, backtester_v383.py, run_backtest_v383.py, sweep_sl_mult_v383.py

## v3.8.4 (2026-02-11) — COMPLETE (CURRENT)
- Adds optional ATR-based TP on v3.8.3. SL checked first (pessimistic). Only re-entry on SL, not TP.
- TP sweep result: TP is coin-specific, NOT universal.
  - RIVER: TP=2.0 beats no-TP (+$7,911 vs +$6,261)
  - KITE: No TP best (+$5,069). ALL TP levels worse.
  - BERA: No TP best (+$4,883). ALL TP levels worse.
- Optimal 3-coin net (per-coin TP): +$17,863
- Capital analysis (3 coins, uniform TP=2.0): Combined DD $6,138, peak margin $1,500, headroom $2,362 on $10K
- Files: position_v384.py, backtester_v384.py, run_backtest_v384.py, sweep_tp_v384.py, capital_analysis_v384.py
- Sanity checked: All 6 source files reviewed, no bugs found.

---

## Backtest Results Summary (5m, 3 months)
- RIVER +$55.9K ($13.95/tr), KITE +$15K, PEPE +$10.4K, SAND +$8.6K, HYPE +$7.2K
- Total 5m: +$97,060 across 20,283 trades ($4.79/trade avg)
- BE$2 optimal for most coins; RIVER uses BE$4, HYPE uses BE$10, SAND uses BE$6

## ATR x Leverage Formula (Hilpisch Ch 11)
- Formula: ATR_leverage = ATR x leverage
- Example: 2% ATR x 20x leverage = 40% SL level
- TSL: Based on (price - max_price) / entry_price NOT (price - entry_price) / entry_price
- MFE/MAE tracking: entry_price, min_price, max_price

## Position Sizing
- Risk per trade: 1-2% of account
- Formula: position_size = (account x risk%) / (stop_loss_distance x price)
- Critical metric: Consecutive downside maximum (10 SLs in a row = account death)
- Crypto: $500 margin x 1% = $5 risk/trade (but $8 commission = 160% of risk, only viable with rebates)

## Qwen/Ollama Integration (2026-02-10)
- Ollama path: C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe (not in PATH)
- Parser FIXED: auto_generate_files.py now supports 4 patterns
- Ollama API: Port 11434

## Execution Framework Requirements (2026-02-10)
- Goal: Run scalping systems 24/7 without human intervention
- Requirements: Auto-restart on crash, checkpoint/resume, health monitoring, remote status
- Framework location: trading-tools/executor/ (task_runner.py, watchdog.py, checkpoint.py, dashboard.py)
- Must survive power cuts, blue screens, reboots — zero manual intervention
- Status: NOT BUILT

## 3-Year Data Pipeline (2026-02-13) — BUILT & TESTED
- **Period downloader**: `scripts/download_periods.py` — Bybit 1m OHLCV for 2023-2024 and 2024-2025
- **CoinGecko v2**: `scripts/fetch_coingecko_v2.py` — 5 actions (market cap history, global history, categories, coin detail, movers)
- **Features v2**: `ml/features_v2.py` — 26 features (14 orig + 8 volume + 4 market cap)
- **Period loader**: `data/period_loader.py` — concat 3 period sources into single DataFrame
- **CoinGecko outputs**: `data/coingecko/` (coin_market_history, global_market_history, coin_categories, coin_metadata, top_movers)
- **CoinGecko API**: Analyst plan, key in `.env`, 1000 req/min, 500K credits, expires 2026-03-03
- **Tests**: 111/111 passed across 4 test scripts
- **Pending full runs**: CoinGecko --reset (~3 min), Bybit 2023-2024 (~2.5h), Bybit 2024-2025 (~4.5h)
- **New ML features**: vol_ratio_5/50/200, vol_trend, vol_zscore, quote_vol_ratio, vol_price_corr, relative_spread, log_market_cap, log_daily_turnover, market_cap_rank, turnover_to_cap_ratio
