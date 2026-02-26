# Vince Trading Platform - Code Generation Task

You are a senior Python developer generating production-ready code for a trading backtesting platform.

## CRITICAL INSTRUCTIONS

1. Generate COMPLETE, WORKING Python code for each file
2. Include ALL imports, type hints, docstrings, error handling
3. Do NOT include placeholder comments like "# [GENERATE CODE HERE]"
4. Do NOT just output completion markers - output the ACTUAL CODE
5. Each file must be fully functional and ready to run

## YOUR TASK

Generate the following 20 Python files in sequence. For each file, output the complete Python code within triple backticks with the language specified:

```python
[ACTUAL WORKING CODE GOES HERE]
```

After each code block, add a single line: `✓ filename.py COMPLETE` then immediately start the next file.

---

## File 1: strategies/base_strategy.py

Generate an abstract base class for trading strategies.

Requirements:
- Use Python's `abc` module for abstract methods
- Abstract methods: `calculate_indicators(df)`, `generate_signals(df)`, `get_sl_tp(entry_price, direction, atr)`
- Include comprehensive Google-style docstrings
- Type hints for all parameters and return values
- Example concrete implementation in `if __name__ == "__main__"` block

Generate the complete code now.

---

## File 2: engine/position_manager.py

Generate a Position class that tracks open trades with MFE/MAE.

Requirements:
- Track: entry_price, size, direction (LONG/SHORT), stop_loss, take_profit, entry_time
- MFE/MAE tracking: track max_price and min_price during trade
- Methods: `__init__()`, `update(current_price)`, `get_mfe_atr(atr)`, `get_mae_atr(atr)`, `check_exit(current_price)`, `close(exit_price)`
- Return trade dict with all data when closed
- Example usage in `if __name__ == "__main__"` block

Generate the complete code now.

---

## File 3: engine/exit_manager.py

Generate an ExitManager class that implements 4 risk management methods.

Requirements:
- Methods: be_only, be_plus_fees, be_plus_fees_trail_tp, be_trail_tp
- Parameters: mfe_trigger (ATR multiple to activate), sl_lock (ATR distance from entry), tp_trail_distance
- Method: `update_stops(position, current_price, current_atr)` returns (new_sl, new_tp)
- Never move stops backwards (always improve)
- Type hints and docstrings for all methods
- Example usage showing all 4 risk methods

Generate the complete code now.

---

## File 4: engine/metrics.py

Generate functions to calculate trading performance metrics.

Requirements:
- `calculate_sqn(returns)`: System Quality Number (sqrt(N) * mean / stdev)
- `calculate_sharpe(returns, risk_free_rate=0)`: Sharpe Ratio
- `calculate_sortino(returns, target_return=0)`: Sortino Ratio (downside deviation only)
- `calculate_max_drawdown(equity_curve)`: Returns (max_dd_pct, max_dd_duration_days)
- `calculate_lsg_percent(trades_df)`: Loser Saw Green % (losers that had MFE > 0)
- `calculate_win_rate(trades_df)`: Win rate %
- `calculate_profit_factor(trades_df)`: Gross profit / gross loss
- All functions with docstrings, type hints, error handling
- Example usage in `if __name__ == "__main__"`

Generate the complete code now.

---

## File 5: engine/backtester.py

Generate a Backtester class that runs event-based backtest simulation.

Requirements:
- Input: DataFrame with OHLCV + indicators, Strategy instance, ExitManager instance
- Simulate bar-by-bar execution
- Track: all trades (entry/exit/pnl/MFE/MAE), equity curve, drawdowns
- Methods: `run(df)` returns dict with trades_df, equity_curve, metrics
- Use PositionManager for tracking trades
- Calculate all metrics using engine.metrics functions
- Example usage showing full backtest workflow

Generate the complete code now.

---

## File 6: strategies/indicators.py

Generate functions to calculate Four Pillars trading indicators.

Requirements:
- `calculate_stochastics(df, periods=[9,14,40,60], k_smooth=1, d_smooth=10)`: Raw K stochastics
- `calculate_ema_clouds(df)`: Ripster clouds (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89)
- `calculate_atr(df, period=14)`: Average True Range
- `calculate_cloud3_position(df)`: Returns price_pos (-1/0/1)
- `calculate_all_indicators(df)`: Calls all above functions, returns df with all indicators
- Use TA-Lib for technical indicators
- Vectorized pandas operations
- Comprehensive error handling

Generate the complete code now.

---

## File 7: strategies/signals.py

Generate signal generation logic for Four Pillars A/B/C signals.

Requirements:
- Class `SignalGenerator` with method `generate_signals(df)`
- A signal: 4/4 stochastics oversold/overbought + Cloud 3 allows direction
- B signal: 3/4 stochastics + Cloud 3 allows + can open fresh
- C signal: 2/4 stochastics + price inside Cloud 3
- State machine for stage tracking (oversold entry → exit oversold)
- Output columns: signal_type (A/B/C), direction (LONG/SHORT), action (OPEN/ADD/FLIP)
- Configurable parameters (allow_b_fresh, allow_c_fresh, use_cloud3_filter)
- Example usage in `if __name__ == "__main__"`

Generate the complete code now.

---

## File 8: strategies/four_pillars_v3_8.py

Generate the complete Four Pillars v3.8 strategy class.

Requirements:
- Inherits from BaseStrategy
- Implements: calculate_indicators(), generate_signals(), get_sl_tp()
- Uses indicators.py for calculations
- Uses signals.py for A/B/C signal generation
- ATR-based SL/TP: sl_atr=1.0, tp_atr=1.5
- Commission: $8/side (0.08%)
- Cooldown: 3 bars between entries
- Cloud 3 directional filter (always on)
- Returns complete signals DataFrame ready for backtester
- Example usage showing full backtest on sample data

Generate the complete code now.

---

## File 9: optimizer/grid_search.py

Generate grid search optimizer for strategy parameters.

Requirements:
- Function `grid_search(strategy_class, df, param_grid, metric='sqn')`
- Iterate through all parameter combinations
- Run backtest for each combination
- Sort results by specified metric
- Return DataFrame with all results (params + metrics)
- Show progress bar (tqdm)
- Example: optimize be_trigger, be_lock, sl_atr, tp_atr on sample data

Generate the complete code now.

---

## File 10: optimizer/bayesian_opt.py

Generate Bayesian optimization for strategy parameters.

Requirements:
- Use `optuna` library for Bayesian optimization
- Function `bayesian_optimize(strategy_class, df, param_ranges, n_trials=100, metric='sqn')`
- Define objective function that runs backtest and returns metric
- Log all trials to SQLite database
- Return best parameters + study object
- Example: find optimal be_trigger (0.3-1.0), be_lock (0.1-0.5), sl_atr (0.5-2.0), tp_atr (1.0-3.0)

Generate the complete code now.

---

## File 11: optimizer/walk_forward.py

Generate walk-forward validation system.

Requirements:
- Function `walk_forward(strategy_class, df, param_grid, train_days=60, test_days=14, step_days=7)`
- Split data into overlapping train/test windows
- Optimize on train window, test on test window
- Track performance across all windows
- Return: per-window results, aggregate metrics, parameter stability analysis
- Visualize results (optional matplotlib chart)
- Example showing 3-month data split into 6 windows

Generate the complete code now.

---

## File 12: optimizer/aggregator.py

Generate results aggregator for multi-coin optimization.

Requirements:
- Function `aggregate_results(per_coin_results)`: Takes list of optimization results DataFrames
- Calculate: best params per coin, universal best params (average across coins), coin-specific vs universal performance delta
- Methods: `rank_parameters_by_consistency()`, `find_universal_params()`, `analyze_param_stability()`
- Output: summary DataFrame with recommendations
- Example: aggregate results from 5 coins (RIVER, KITE, PEPE, HYPE, SAND)

Generate the complete code now.

---

## File 13: ml/triple_barrier.py

Generate Triple Barrier Method labeling (from De Prado).

Requirements:
- Function `label_trades(df, tp_mult=1.5, sl_mult=1.0, time_bars=100)`
- For each signal bar: set upper barrier (tp_mult × ATR), lower barrier (sl_mult × ATR), time barrier (time_bars ahead)
- Label = 1 if TP hit first, 0 if SL hit first, 0.5 if time barrier hit first
- Track which barrier was hit and when
- Return DataFrame with labels + barrier_hit + bars_held
- Example on sample Four Pillars signals

Generate the complete code now.

---

## File 14: ml/features.py

Generate feature engineering for ML meta-labeling.

Requirements:
- Function `generate_features(df)`: Generate 20+ features from OHLCV + indicators
- Features: Stoch K values (4), EMA distances from price (normalized), ATR% (ATR/price), volume ratio (vol / vol_sma), RSI, CCI, MFI, MACD, BBW (Bollinger Band Width), OBV, ADOSC
- Normalize features using rolling z-score (window=100)
- Return DataFrame with all features + original columns
- TA-Lib for technical indicators
- Example usage

Generate the complete code now.

---

## File 15: ml/xgboost_trainer.py

Generate XGBoost meta-labeling trainer.

Requirements:
- Function `train_xgboost(features_df, labels, test_size=0.2, n_estimators=100)`
- Purged K-Fold CV (5 folds with 1% embargo between folds)
- Train XGBoost classifier to predict skip/take on Four Pillars signals
- Calculate SHAP values for feature importance
- Return: trained model, feature_importances DataFrame, test metrics (accuracy, precision, recall), SHAP values
- Example: train on sample labeled data, show SHAP summary

Generate the complete code now.

---

## File 16: gui/coin_selector.py

Generate Streamlit coin selector component.

Requirements:
- Function `render_coin_selector()`: Streamlit multiselect for coins
- Load coin list from data/cache/*.parquet files
- Filter by: market cap, volume, price range
- Fuzzy search by coin name or symbol
- Return list of selected coin symbols
- Example Streamlit app

Generate the complete code now.

---

## File 17: gui/parameter_inputs.py

Generate Streamlit parameter input components.

Requirements:
- Function `render_parameter_inputs()`: Streamlit sidebar with parameter sliders/inputs
- Parameters: atr_period (8-21), sl_atr (0.5-2.0), tp_atr (1.0-3.0), be_trigger (0.3-1.0), be_lock (0.1-0.5), commission ($4-$12)
- Organize into sections: Indicators, Entry/Exit, Risk Management, Costs
- Return dict of parameter values
- Example Streamlit app

Generate the complete code now.

---

## File 18: utils/data_loader.py

Generate data loading utilities.

Requirements:
- Function `load_coin_data(symbol, timeframe='5m', cache_dir='data/cache')`: Load from parquet
- Function `fetch_bybit_data(symbol, start_date, end_date, timeframe='5m')`: Fetch from Bybit API
- Function `resample_timeframe(df, from_tf, to_tf)`: Resample OHLCV data
- Cache management: save/load parquet files
- Error handling for missing files or API errors
- Example usage

Generate the complete code now.

---

## File 19: utils/logger.py

Generate logging utilities.

Requirements:
- Function `setup_logger(name, log_file, level=logging.INFO)`: Configure logger
- Dual output: console (INFO+) and file (DEBUG+)
- Colored output for console (colorama)
- Rotating file handler (max 10MB, 5 backups)
- Example usage showing different log levels

Generate the complete code now.

---

## File 20: main.py

Generate main entry point for running backtests.

Requirements:
- CLI using `argparse`: --coin, --timeframe, --start-date, --end-date, --strategy, --optimize
- Load data using utils.data_loader
- Initialize strategy (Four Pillars v3.8)
- Run backtest or optimization
- Print results summary
- Save results to CSV/JSON
- Example: `python main.py --coin RIVERUSDT --timeframe 5m --optimize`

Generate the complete code now.

---

## REMINDER

For each file:
1. Output complete, working Python code in ```python ``` code blocks
2. No placeholders or "TODO" comments
3. Include all imports
4. Add type hints and docstrings
5. Add example usage in `if __name__ == "__main__"`
6. After the code block, add: `✓ filename.py COMPLETE`

START GENERATING NOW.
