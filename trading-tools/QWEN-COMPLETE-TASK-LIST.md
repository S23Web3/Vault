# Complete Qwen Task List — All Code Generation for Vince

**Total Tasks**: 62 code files (beyond the 5 from overnight)
**Total Lines**: ~8,500 lines of Python code
**Estimated Time**: 60-80 hours with qwen3-coder:30b

---

## Phase 1: Core Components (Overnight - IN PROGRESS)

✅ **Completed Tonight**:
1. base_strategy.py (~100 lines)
2. position_manager.py (~150 lines)
3. exit_manager.py (~120 lines)
4. metrics.py (~200 lines)
5. backtester.py (~150 lines)

---

## Phase 2: Four Pillars Strategy (Day 2 - Priority)

### 2.1 Indicator Calculations (indicators.py)
**Lines**: ~300
**Complexity**: Medium

```python
"""
Calculate all Four Pillars indicators:
- 4 Stochastic oscillators (9-3, 14-3, 40-3, 60-10) using ta-lib
- 5 Ripster EMA clouds (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89, Cloud 5: 180/200)
- ATR with configurable period (8, 13, 14, 21)
- Cloud 3 directional bias (price_pos: -1/0/1)
- Volume analysis (relative volume vs SMA)

Return DataFrame with all indicator columns.
Use vectorized operations (pandas/numpy).
Include input validation and error handling.
"""
```

### 2.2 Signal Generation (signals.py)
**Lines**: ~250
**Complexity**: High

```python
"""
Implement Four Pillars A/B/C signal state machine:

A Signal (Strongest):
- 4/4 stochastics aligned (all oversold for long, overbought for short)
- Cloud 3 directional filter (must allow direction)
- Can open new position or flip direction

B Signal (Strong):
- 3/4 stochastics aligned
- Cloud 3 filter
- Can add to position or open fresh (if bOpenFresh=true)

C Signal (Confirmation):
- 2/4 stochastics aligned
- Cloud 3 filter + inside Cloud 3
- Can add to position only

Return DataFrame with columns: signal_type (A/B/C), direction (LONG/SHORT), action (OPEN/ADD/FLIP)
"""
```

### 2.3 Cloud 3 Filter (cloud_filter.py)
**Lines**: ~100
**Complexity**: Low

```python
"""
Calculate Cloud 3 (EMA 34/50) directional bias:

price_pos = -1 if price below cloud (bearish)
price_pos = 0 if price inside cloud (neutral)
price_pos = 1 if price above cloud (bullish)

cloud3_allows_long = (price_pos >= 0)
cloud3_allows_short = (price_pos <= 0)

Return DataFrame with columns: cloud3_top, cloud3_bot, price_pos, allows_long, allows_short
"""
```

### 2.4 Four Pillars Strategy Class (four_pillars_v3_8.py)
**Lines**: ~400
**Complexity**: High

```python
"""
Complete Four Pillars v3.8 strategy implementation.

Inherits from BaseStrategy (from overnight task).

Methods:
- calculate_indicators(): Use indicators.py functions
- generate_signals(): Use signals.py + cloud_filter.py
- get_sl_tp(): ATR-based (1.0 ATR SL, 1.5 ATR TP)
- get_entry_size(): Risk-based position sizing

Config parameters:
- atr_period: int (8, 13, 14, or 21)
- sl_atr_mult: float (default 1.0)
- tp_atr_mult: float (default 1.5)
- allow_b_fresh: bool (default False)
- cooldown_bars: int (default 3)

Commission: $8/side via exit_manager
"""
```

---

## Phase 3: Parameter Optimization (Day 3-4)

### 3.1 Grid Search (optimizer/grid_search.py)
**Lines**: ~200
**Complexity**: Medium

```python
"""
Exhaustive parameter sweep across:
- atr_period: [8, 13, 14, 21]
- mfe_trigger: [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
- sl_lock: [0, 0.2, 0.3, 0.5, 0.7]
- tp_trail_distance: [0.3, 0.5, 0.7, 1.0]
- risk_method: ['be_only', 'be_plus_fees', 'be_plus_fees_trail_tp', 'be_trail_tp']

Run backtest for each combination.
Return sorted results by SQN × Total Profit.
Support parallel execution (multiprocessing).
"""
```

### 3.2 Bayesian Optimization (optimizer/bayesian_opt.py)
**Lines**: ~250
**Complexity**: High

```python
"""
Smart parameter search using optuna library.

Search space:
- atr_period: Categorical([8, 13, 14, 21])
- mfe_trigger: Float(0.3, 2.0)
- sl_lock: Float(0.0, 1.0)
- tp_trail_distance: Float(0.3, 1.0)
- risk_method: Categorical(['be_only', 'be_plus_fees', ...])

Objective: Maximize SQN × Total Profit

Run 200 trials per coin (vs 5,760 for grid search).
Use TPE sampler (Tree-structured Parzen Estimator).
Support pruning (early stopping for bad trials).
"""
```

### 3.3 Walk-Forward Validation (optimizer/walk_forward.py)
**Lines**: ~150
**Complexity**: Medium

```python
"""
Split data into train/test windows:
- Train: 2 months
- Test: 1 month
- Walk forward: 2-week steps

For each window:
1. Optimize on train data
2. Test on unseen test data
3. Record OOS (out-of-sample) performance

Return DataFrame with columns:
- window_start, window_end
- train_sqn, test_sqn
- train_profit, test_profit
- is_overfitted (test_profit < 0.5 × train_profit)

This prevents overfitting to historical data.
"""
```

### 3.4 Multi-Coin Aggregator (optimizer/aggregator.py)
**Lines**: ~180
**Complexity**: Medium

```python
"""
Aggregate optimization results across multiple coins.

Input: List of (coin, best_params, metrics) tuples

Find "universal best practice" parameters:
- Most common atr_period across all coins
- Median mfe_trigger
- Median sl_lock
- Most common risk_method
- Highest average SQN

Return:
- universal_params: dict
- per_coin_results: DataFrame
- performance_comparison: grid vs bayesian vs walk-forward
"""
```

---

## Phase 4: ML Components (Day 5-7)

### 4.1 Triple Barrier Labeling (ml/triple_barrier.py)
**Lines**: ~200
**Complexity**: Medium

```python
"""
De Prado's Triple Barrier Method for labeling trades:

For each signal:
1. Upper barrier: TP at entry + (tp_atr_mult × ATR)
2. Lower barrier: SL at entry - (sl_atr_mult × ATR)
3. Vertical barrier: Time exit at +100 bars (5m) or +20 bars (1h)

Return label:
- 1 if TP hit first (TAKE)
- 0 if SL hit first (SKIP)
- 0.5 if time exit (UNCERTAIN)

Return DataFrame with columns:
- label (0/0.5/1)
- hit_time (bars to exit)
- exit_reason ('TP', 'SL', 'TIME')
- mfe_atr, mae_atr

This creates labels for XGBoost meta-labeling.
"""
```

### 4.2 Feature Engineering (ml/features.py)
**Lines**: ~300
**Complexity**: Medium

```python
"""
Generate 21 features for XGBoost:

Price Features (5):
- pct_from_cloud3_top: (close - cloud3_top) / cloud3_top
- pct_from_cloud3_bot: (close - cloud3_bot) / cloud3_bot
- price_pos: -1/0/1
- atr_pct: ATR / close
- close_vs_ema50: (close - ema50) / ema50

Stoch Features (8):
- stoch_9_k, stoch_14_k, stoch_40_k, stoch_60_k
- stoch_9_oversold (1 if < 20 else 0)
- stoch_14_oversold, stoch_40_oversold, stoch_60_oversold

Volume Features (3):
- volume_ratio: volume / sma(volume, 20)
- volume_surge: 1 if volume_ratio > 2 else 0
- quote_vol_ratio: quote_vol / sma(quote_vol, 20)

Momentum Features (3):
- rsi_14: RSI(14)
- macd: MACD histogram
- roc_10: Rate of change (10 bars)

Cloud Features (2):
- cloud3_width: (cloud3_top - cloud3_bot) / cloud3_bot
- inside_cloud3: 1 if price_pos == 0 else 0

Return DataFrame with all feature columns.
"""
```

### 4.3 XGBoost Trainer (ml/xgboost_trainer.py)
**Lines**: ~250
**Complexity**: High

```python
"""
Train XGBoost binary classifier:

Target: labels from triple_barrier.py (0 = SKIP, 1 = TAKE)
Features: 21 features from features.py

Model config:
- objective='binary:logistic'
- eval_metric='logloss'
- max_depth=6
- learning_rate=0.1
- n_estimators=100
- tree_method='gpu_hist' (use GPU)

Split:
- Train: 70%
- Test: 30%

Use Purged K-Fold CV (5 folds, 1% embargo).

Return:
- trained_model: XGBoost classifier
- feature_importances: DataFrame sorted by importance
- test_accuracy, test_precision, test_recall
- confusion_matrix
"""
```

### 4.4 Purged K-Fold CV (ml/purged_cv.py)
**Lines**: ~150
**Complexity**: High

```python
"""
De Prado's Purged K-Fold Cross-Validation.

Problem: Standard K-fold leaks information (train/test overlap).

Solution:
1. Split data into K folds
2. For each fold:
   a. Remove training samples that overlap with test period
   b. Add embargo period (1% of data) after test set
   c. Train on purged training set
   d. Test on clean test set

Return:
- cv_scores: list of (fold, train_score, test_score)
- avg_train_score, avg_test_score
- is_overfit: (test_score < 0.7 × train_score)

This prevents overfitting to temporal patterns.
"""
```

### 4.5 SHAP Values (ml/shap_analyzer.py)
**Lines**: ~180
**Complexity**: Medium

```python
"""
Calculate SHAP (SHapley Additive exPlanations) values for XGBoost.

For each trade prediction:
- Which features contributed to SKIP decision?
- Which features contributed to TAKE decision?

Example output:
Trade #123 (SKIP prediction):
- stoch_9_k = 75 (overbought) → +0.3 toward SKIP
- price_pos = -1 (below cloud) → +0.2 toward SKIP
- rsi_14 = 68 → +0.1 toward SKIP
- volume_ratio = 0.8 → -0.1 toward TAKE

Return DataFrame with:
- trade_id
- prediction (0 = SKIP, 1 = TAKE)
- shap_values (dict of feature: contribution)
- top_3_features (most influential)

Use shap.TreeExplainer for XGBoost models.
"""
```

### 4.6 Meta-Labeling Pipeline (ml/meta_labeling.py)
**Lines**: ~200
**Complexity**: Medium

```python
"""
Complete meta-labeling workflow:

1. Four Pillars generates signals (primary model)
2. XGBoost predicts TAKE/SKIP for each signal (secondary model)
3. Only act on signals where XGBoost says TAKE

Process:
- Load historical data
- Run Four Pillars strategy → get signals
- Generate 21 features for each signal
- Train XGBoost on labeled data (triple_barrier)
- Predict on new signals
- Filter: only take signals with XGBoost confidence > 0.6

Return:
- signals_before_filter: all Four Pillars signals
- signals_after_filter: XGBoost-approved signals
- improvement: (filtered_sqn / unfiltered_sqn - 1) × 100%
"""
```

---

## Phase 5: Streamlit GUI (Day 8-10)

### 5.1 Coin Selector (gui/coin_selector.py)
**Lines**: ~120
**Complexity**: Low

```python
"""
Fuzzy search coin selector using fuzzywuzzy library.

Features:
- Dropdown with all available coins (from data/cache/*.parquet)
- Type-ahead search: "asx" → suggests "AXSUSDT"
- Select random 5 coins button
- Multi-select (checkboxes)

Return: list of selected coin symbols

Example:
>>> coins = coin_selector(data_dir="data/cache")
>>> print(coins)
['BTCUSDT', 'ETHUSDT', 'RIVERUSDT']
"""
```

### 5.2 Parameter Input Form (gui/parameter_inputs.py)
**Lines**: ~200
**Complexity**: Low

```python
"""
Streamlit form for parameter configuration:

Inputs:
- Timeframe: selectbox (1m, 5m, 15m, 1h)
- Notional value: number_input ($500, $1000, $5000)
- Commission: number_input ($8/side default)
- ATR periods: multiselect ([8, 13, 14, 21])
- Risk methods: checkboxes (be_only, be_plus_fees, ...)
- Optimization method: radio (Bayesian, Grid Search, Walk-Forward)
- Number of trials: slider (100-500)

Return: dict with all parameters

Use st.form() to batch inputs.
Add validation (e.g., notional > 0).
"""
```

### 5.3 Results Dashboard (gui/report_viewer.py)
**Lines**: ~400
**Complexity**: High

```python
"""
6-tab Streamlit dashboard:

Tab 1: Summary
- Best parameters per coin (table)
- Universal best practice (highlighted)
- Performance comparison (grid vs bayesian)

Tab 2: Trade List
- DataFrame with all trades
- Columns: entry_time, exit_time, direction, pnl, mfe_atr, mae_atr, exit_reason
- LSG flag (1 if loser saw green)
- Export CSV button

Tab 3: Equity Curve
- Plotly line chart (cumulative P&L)
- Per coin (multi-line)
- Aggregate (bold line)
- Drawdown shaded area

Tab 4: LSG Analysis
- Histogram of MFE for losing trades
- Scatter: MFE vs MAE for losers
- % losers that hit BE, 0.5 ATR, 1.0 ATR profit

Tab 5: SHAP Values (if XGBoost used)
- Bar chart: feature importance
- Waterfall plot: per-trade explanation
- Force plot: prediction breakdown

Tab 6: Parameter Heatmap
- Heatmap: SQN vs mfe_trigger vs sl_lock
- 3D surface plot (if grid search)
- Optimization history (if Bayesian)

Use Plotly for all charts (interactive).
"""
```

### 5.4 Export Manager (gui/export_manager.py)
**Lines**: ~150
**Complexity**: Low

```python
"""
Export functionality for each dashboard tab:

Formats:
- CSV: trade list, parameter results
- PNG: all charts (via plotly.write_image)
- PDF: full report (via matplotlib backend)
- HTML: interactive dashboard (via plotly.to_html)

Functions:
- export_trades_csv(trades_df, filename)
- export_chart_png(fig, filename)
- export_full_report_pdf(all_tabs, filename)
- export_interactive_html(dashboard, filename)

Add Streamlit download buttons for each format.
"""
```

### 5.5 Main App (app.py)
**Lines**: ~300
**Complexity**: Medium

```python
"""
Main Streamlit app entry point.

Layout:
- Sidebar: parameter_inputs.py
- Main area: report_viewer.py (6 tabs)
- Footer: export buttons

Flow:
1. User selects coins, parameters
2. User clicks "Run Analysis"
3. App runs optimization (with progress bar)
4. Results displayed in tabs
5. User exports desired formats

Use st.cache_data for loaded data (parquet files).
Use st.cache_resource for trained models (XGBoost).
Add error handling (try/except with st.error).
"""
```

---

## Phase 6: Exchange Integration (Day 11-13)

### 6.1 BingX Data Fetcher (data/bingx_fetcher.py)
**Lines**: ~250
**Complexity**: Medium

```python
"""
Fetch historical OHLCV from BingX API.

API: https://bingx-api.github.io/docs/swap/market-api.html

Endpoints:
- GET /openApi/swap/v2/quote/klines (historical candles)
- Params: symbol, interval, startTime, endTime, limit

Features:
- Pagination (1000 candles per request)
- Rate limiting (10 req/sec)
- Retry on error (exponential backoff)
- Cache to Parquet (data/cache/{symbol}_{timeframe}.parquet)

Return DataFrame with columns:
- timestamp, open, high, low, close, base_vol, quote_vol

Handle errors: API down, rate limit, invalid symbol.
"""
```

### 6.2 WEEX Data Fetcher (data/weex_fetcher.py)
**Lines**: ~250
**Complexity**: Medium

```python
"""
Fetch historical OHLCV from WEEX API.

API: https://doc-cloud.weexstatic.com/ (if available)

Note: WEEX API has no pagination (from previous testing).
Workaround: Fetch in 1-day chunks, merge locally.

Features:
- Chunked fetching (1 day at a time)
- Rate limiting
- Retry on error
- Cache to Parquet

Return same DataFrame format as BingX fetcher.

If WEEX API unavailable, fallback to manual CSV import.
"""
```

### 6.3 WebSocket Handler (data/websocket_handler.py)
**Lines**: ~200
**Complexity**: High

```python
"""
Real-time data stream from BingX/WEEX WebSocket.

BingX WS: wss://open-api-ws.bingx.com/market

Subscribe to:
- ticker updates (price, volume)
- kline updates (1m candles)

Features:
- Auto-reconnect on disconnect
- Heartbeat/ping-pong
- Message queue (threading.Queue)
- Append to parquet cache

Use websocket-client library.
Run in background thread.
Callback function for new candles.
"""
```

### 6.4 Order Execution (trading/order_executor.py)
**Lines**: ~300
**Complexity**: Very High

```python
"""
Execute orders on BingX/WEEX.

API endpoints:
- POST /openApi/swap/v2/trade/order (create order)
- GET /openApi/swap/v2/trade/order (query order)
- DELETE /openApi/swap/v2/trade/order (cancel order)

Order types:
- MARKET (immediate execution)
- LIMIT (at specified price)
- STOP_MARKET (SL order)
- TAKE_PROFIT_MARKET (TP order)

Features:
- API key/secret management (from .env)
- Request signing (HMAC-SHA256)
- Error handling (insufficient balance, invalid price)
- Position sync (compare local state vs exchange)
- Commission tracking

CRITICAL: Test on paper trading first!
Never execute real orders without user confirmation.
"""
```

### 6.5 Position Sync (trading/position_sync.py)
**Lines**: ~150
**Complexity**: Medium

```python
"""
Sync local position state with exchange.

Problem: Local backtester state != exchange reality
- Orders may fail
- Partial fills
- Manual interventions

Solution:
1. Query exchange positions (GET /openApi/swap/v2/user/positions)
2. Compare with local Position objects
3. Reconcile differences:
   - Local says LONG, exchange says FLAT → close local position
   - Local says FLAT, exchange says LONG → create local position from exchange data
   - Position size mismatch → update local size

Run every 10 seconds.
Log all discrepancies for debugging.
"""
```

---

## Phase 7: Testing & Validation (Day 14-15)

### 7.1 Unit Tests (tests/test_position_manager.py)
**Lines**: ~200
**Complexity**: Low

```python
"""
Pytest unit tests for PositionManager:

Test cases:
- test_open_position_long()
- test_open_position_short()
- test_update_mfe_long()
- test_update_mae_short()
- test_check_exit_sl_hit()
- test_check_exit_tp_hit()
- test_close_position_profit()
- test_close_position_loss()

Use fixtures for sample data.
Assert all outputs match expected values.
"""
```

### 7.2 Integration Tests (tests/test_backtester.py)
**Lines**: ~250
**Complexity**: Medium

```python
"""
Pytest integration tests for full backtester:

Test cases:
- test_backtest_riverusdt_5m() → expect ~$55.9K profit
- test_four_pillars_strategy()
- test_exit_manager_be_raise()
- test_commission_calculation()
- test_equity_curve_generation()

Load cached data (RIVERUSDT 5m, 3 months).
Run backtest with known good parameters.
Assert results within ±5% of expected.
"""
```

### 7.3 Pine vs Python Validator (tests/validate_pine_python.py)
**Lines**: ~200
**Complexity**: High

```python
"""
Verify Pine Script v3.8 == Python v3.8 results.

Process:
1. Export TradingView trade list (CSV)
2. Run Python backtester on same coin/dates
3. Compare:
   - Total trades (±1% tolerance)
   - Total P&L (±5% tolerance)
   - Win rate (±2% tolerance)
   - Entry/exit prices (sample 10 trades, ±0.1% tolerance)

If mismatch > tolerance:
- Print diff report
- Highlight divergence point (first trade that differs)

This ensures Pine → Python conversion is accurate.
"""
```

---

## Phase 8: Utilities & Helpers (Day 16-17)

### 8.1 Logger (utils/logger.py)
**Lines**: ~100
**Complexity**: Low

```python
"""
Centralized logging for all modules.

Use loguru library:
- Logs to file: logs/vince_{date}.log
- Console output (colored)
- Rotation (10 MB per file)
- Retention (30 days)

Usage:
>>> from utils.logger import logger
>>> logger.info("Backtest started")
>>> logger.error("API call failed", exc_info=True)

Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
"""
```

### 8.2 Profiler (utils/profiler.py)
**Lines**: ~120
**Complexity**: Low

```python
"""
Performance profiling for bottlenecks.

Features:
- Decorator: @profile (logs execution time)
- Context manager: with profile("backtest"):
- Memory profiler (memory_profiler library)

Example:
>>> @profile
... def slow_function():
...     # ... code
>>> slow_function()
[PROFILE] slow_function took 2.35s

Output top 10 slowest functions after run.
"""
```

### 8.3 Kelly Criterion (utils/kelly.py)
**Lines**: ~80
**Complexity**: Low

```python
"""
Calculate optimal bet size using Kelly Criterion.

Formula:
f* = (p × b - q) / b

Where:
- p = win probability
- q = loss probability (1 - p)
- b = win/loss ratio (avg_win / avg_loss)

Input: DataFrame with trade P&L
Output: optimal_f (fraction of capital to risk)

Example:
>>> kelly_f = calculate_kelly(trades_df)
>>> print(f"Risk {kelly_f*100:.1f}% per trade")
Risk 2.3% per trade
"""
```

### 8.4 Chart Plotter (utils/plotter.py)
**Lines**: ~250
**Complexity**: Medium

```python
"""
Pre-built chart templates using Plotly.

Functions:
- plot_equity_curve(equity: pd.Series)
- plot_drawdown(equity: pd.Series)
- plot_trade_scatter(trades: pd.DataFrame)
- plot_mfe_mae_scatter(trades: pd.DataFrame)
- plot_parameter_heatmap(results: pd.DataFrame)
- plot_feature_importance(importances: pd.DataFrame)

Return Plotly figures (ready for Streamlit or export).
"""
```

---

## Phase 9: Documentation (Day 18)

### 9.1 README.md
**Lines**: ~400
**Complexity**: Low

```markdown
# Vince ML Platform — Four Pillars Backtesting & Optimization

## Overview
[Project description]

## Installation
pip install -r requirements.txt

## Quick Start
[5-minute tutorial]

## Features
[List of features]

## Architecture
[Diagram + explanation]

## Usage Examples
[Code snippets]

## API Reference
[Link to docs/]

## Contributing
[Guidelines]

## License
MIT
```

### 9.2 API Documentation (docs/api.md)
**Lines**: ~500
**Complexity**: Low

```markdown
# API Reference

## strategies.base_strategy
[Docstring-generated docs for BaseStrategy]

## engine.backtester
[Docstring-generated docs for Backtester]

## optimizer.grid_search
[...]

Use Sphinx or MkDocs to auto-generate from docstrings.
```

### 9.3 Strategy Guide (docs/strategy_guide.md)
**Lines**: ~600
**Complexity**: Low

```markdown
# Four Pillars Strategy Guide

## Entry Signals
[A/B/C signal explanation with charts]

## Exit Management
[4 risk methods explained]

## Parameter Optimization
[How to use grid search vs Bayesian]

## ML Meta-Labeling
[XGBoost integration guide]

## Best Practices
[Lessons learned from backtesting]
```

---

## Summary Table

| Phase | Tasks | Lines | Complexity | Priority | Qwen Time |
|-------|-------|-------|------------|----------|-----------|
| 1. Core (Overnight) | 5 | 720 | Medium | ✅ DONE | 4-8 hrs |
| 2. Strategy | 4 | 1050 | High | 🔴 Critical | 6-8 hrs |
| 3. Optimization | 4 | 780 | Medium-High | 🔴 Critical | 5-7 hrs |
| 4. ML | 6 | 1280 | High | 🟡 Important | 8-10 hrs |
| 5. GUI | 5 | 1170 | Medium | 🟡 Important | 6-8 hrs |
| 6. Exchange | 5 | 1150 | High | 🟢 Later | 8-10 hrs |
| 7. Testing | 3 | 650 | Medium | 🟡 Important | 4-6 hrs |
| 8. Utils | 4 | 550 | Low | 🟢 Later | 3-4 hrs |
| 9. Docs | 3 | 1500 | Low | 🟢 Later | 4-6 hrs |
| **TOTAL** | **39** | **8,850** | **-** | **-** | **52-75 hrs** |

---

## Recommended Qwen Workflow (Next 2 Weeks)

### Week 1: Core Functionality
- **Day 1** (Tomorrow): Phase 2 (Strategy components) - 6-8 hrs
- **Day 2**: Phase 3 (Optimization) - 5-7 hrs
- **Day 3**: Phase 7 (Testing) + Phase 2/3 fixes - 6-8 hrs
- **Day 4-5**: Phase 4 (ML) - 8-10 hrs each day

### Week 2: GUI & Integration
- **Day 6-7**: Phase 5 (GUI) - 6-8 hrs each day
- **Day 8-10**: Phase 6 (Exchange integration) - 8-10 hrs per day
- **Day 11**: Phase 8 (Utils) - 4 hrs
- **Day 12**: Phase 9 (Docs) - 6 hrs

**Total**: 60-80 hours of Qwen code generation over 12 days.

---

## How to Use This List

**Tonight**: Qwen generates Phase 1 (5 files)

**Tomorrow**: You paste Phase 1 output to Claude → Claude integrates/tests

**While Claude works**: You paste next Qwen task (Phase 2.1: indicators.py)

**Repeat**: Parallel workflow until all 44 files generated!

---

**Next Step**: After overnight task completes, check this list and pick the next priority task to give Qwen.
