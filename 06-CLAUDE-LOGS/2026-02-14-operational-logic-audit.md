# Operational Logic Audit -- 2026-02-14

## Scope
Full operational logic review of Four Pillars backtester, data pipeline, and ML pipeline.
Focus: trading logic correctness, look-ahead bias, commission math, data integrity.
NOT: bugs, error handling, style, refactoring.

## Files Audited

### Backtester Engine
- `scripts/dashboard.py` (~1499 lines)
- `engine/backtester_v384.py` (572 lines)
- `engine/position_v384.py` (296 lines)
- `engine/commission.py` (113 lines)
- `engine/avwap.py` (53 lines)
- `signals/four_pillars_v383.py` (112 lines)
- `signals/state_machine_v383.py` (340 lines)
- `signals/stochastics.py` (64 lines)
- `signals/clouds.py` (86 lines)

### Data Pipeline
- `data/fetcher.py`
- `scripts/download_periods_v2.py`
- `data/period_loader.py`
- `scripts/fetch_coingecko_v2.py`

### ML Pipeline
- `ml/features.py`
- `ml/features_v2.py`
- `ml/triple_barrier.py`
- `ml/meta_label.py`
- `ml/purged_cv.py`
- `ml/walk_forward.py`

---

## CRITICAL FINDINGS (7)

### C-1: Equity curve ignores unrealized P&L
- **File**: backtester_v384.py line 393
- **Issue**: Equity only changes on entry (commission) and exit (realized P&L). Between entry/exit, curve is flat. Unrealized drawdowns invisible.
- **Impact**: Max DD% understated. On 20x leverage, a position that dips 3 ATR before recovering creates real margin drawdown that current curve does not show.
- **Fix**: On each bar, compute `curve_equity = equity + sum(unrealized_pnl for each active slot)`.

### C-2: Scale-out entry commission not prorated
- **File**: backtester_v384.py lines 169-176
- **Issue**: Non-final scale-out gets zero entry commission. Final scale-out burdened with full entry commission.
- **Impact**: Per-trade net_pnl distorted. SCALE_1 artificially profitable, SCALE_2 artificially bad. ML meta-labeler trains on biased data.
- **Fix**: `trade_comm = comm_exit + (entry_commission * scale_notional / original_notional)`

### C-3: CommissionModel cost_per_side override
- **File**: commission.py lines 30-32
- **Issue**: `cost_per_side` parameter bypasses rate-based calculation entirely. Sets both taker AND maker to same fixed dollar amount.
- **Impact**: Landmine. Not triggered today but violates "never hardcode dollar amounts" rule. Future callers could silently produce wrong results.
- **Fix**: Remove parameter or add deprecation warning.

### C-4: duration_bars is look-ahead feature in training
- **File**: features.py line 144, features_v2.py line 207
- **Issue**: `duration_bars = exit_bar - entry_bar` uses exit information unknown at entry time. Included in `get_feature_columns()`.
- **Impact**: Model learns hindsight patterns. Inflates accuracy. OOS predictions meaningless.
- **Fix**: Remove `"duration_bars"` from `get_feature_columns()`. One line per file.

### C-5: daily_turnover_at_bar uses intraday future volume
- **File**: features_v2.py lines 107-127
- **Issue**: `resample("1D").sum()` sums ALL bars in calendar day, including bars AFTER trade entry. High-volume days (where big moves happen) show inflated turnover.
- **Impact**: `log_daily_turnover` and `turnover_to_cap_ratio` contain look-ahead data. Rolling-20 mitigates severity (1/20 tainted) but bias is consistent.
- **Fix**: `daily_sum.shift(1)` before computing rolling mean, so only completed prior days are used.

### C-6: Meta-labeler trains and evaluates on SAME data
- **File**: meta_label.py line 90, dashboard.py line 924
- **Issue**: `train(X, y)` then `predict_proba(X)` on identical data. purged_cv module exists but is NEVER wired into any integration path.
- **Impact**: ALL reported accuracy is in-sample. Model memorizes training set. Bet sizing, filtered trade PnL -- all based on in-sample predictions. Meaningless for live trading.
- **Fix**: Wire purged CV into training pipeline. At minimum use holdout split.

### C-7: Triple barrier labels ignore commission
- **File**: triple_barrier.py lines 20-42
- **Issue**: `label_trades()` maps TP=+1 regardless of net P&L. A trade hitting TP at 1.0 ATR on low ATR/price coin can be net negative after 0.16% RT commission.
- **Impact**: Model learns "will it hit TP?" not "will it make money?" These are different questions on coins where commission eats TP profit.
- **Fix**: Switch downstream consumers from `label_trades()` to `label_trades_by_pnl()` (already exists, unused).

---

## WARNING FINDINGS (15)

### Backtester Engine (8)
- W-1: Rebate settlement misses multi-day data gaps (total correct, timing shifted)
- W-2: Settlement day tracking edge case when no bars after 17:00
- W-3: Cloud 3 inside = both long and short allowed for B-grade (whipsaw in consolidation)
- W-4: A and D grades bypass Cloud 3 (D counter-trend may be systematic losers)
- W-5: Stoch 60-K D-line min_periods=1 warmup (dormant -- use_60d=False)
- W-6: Margin display hardcodes /20 divisor (wrong for non-20x leverage)
- W-7: Sweep CSV duplicate header edge case on crash (benign)
- W-8: TP comparison recomputes identical signals (performance only)

### Data Pipeline (7)
- W-9: Log timestamps local time vs state file UTC
- W-10: Parquet date column type stability for CoinGecko filter
- W-11: Failed symbol list grows with duplicates across re-runs
- W-12: Existing parquet assumed valid on resume (no integrity check)
- W-13: Meta file records requested vs actual range (fetcher.py vs periods)
- W-14: Silent data truncation on empty API response (no gap detection)
- W-15: vol_price_corr includes current bar close (minor if bar-close entry)

### ML Pipeline
- W-16: grade_enc may be look-ahead depending on grading logic (verify)
- W-17: Walk-forward has no purge/embargo gap between IS and OOS
- W-18: Purged CV uses last trade exit not max exit across fold (partial leakage)
- W-19: NaN imputed to constants (50/0/1) defeats XGBoost native NaN handling
- W-20: Static market cap applied to all historical trades (look-ahead on cap growth)

---

## OK FINDINGS (17)

- Commission math rate-based throughout (0.0008 per side on notional)
- Entry at close, no look-ahead bias in backtester
- SL/TP direction and priority correct (SL checked first, pessimistic)
- Notional-based position sizing correct
- No close_all() for flips (individual position close)
- Signal grading A/B/C/D/R matches Four Pillars spec
- ATR Wilder's RMA correct, no look-ahead
- Cloud 2 crossover detection bar-accurate
- Sweep creates fresh Backtester384 per coin (no state leakage)
- 5m resample OHLCV aggregation standard
- Bybit pagination backward from end_ms correct
- All data timestamps explicitly UTC
- Period loader deduplication correct (earlier period wins)
- CoinGecko conservative filtering correct (unknown coins kept)
- Parquet column naming consistent (base_vol/quote_vol)
- Resume skip logic correct (completed + no_data skipped, failed retried)
- Rate limiting well within Bybit and CoinGecko limits

---

## RECOMMENDED FIX PRIORITY

| Priority | ID | Fix | Effort |
|----------|-----|-----|--------|
| 1 | C-6 | Wire purged CV into meta-labeler training | Medium |
| 2 | C-4 | Remove duration_bars from get_feature_columns() | Trivial |
| 3 | C-1 | Add unrealized P&L to equity curve | Medium |
| 4 | C-7 | Switch to label_trades_by_pnl() | Low |
| 5 | C-2 | Prorate entry commission on scale-outs | Low |
| 6 | C-5 | daily_sum.shift(1) for daily turnover | Trivial |
| 7 | C-3 | Remove cost_per_side parameter | Trivial |
