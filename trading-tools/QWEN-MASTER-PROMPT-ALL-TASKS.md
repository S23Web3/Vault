# QWEN MASTER PROMPT — Generate ALL Vince Components (Sequential Chain)

**Total Output**: 20+ Python files (~3,500 lines)
**Goal**: Complete as many files as possible without stopping

---

## INSTRUCTIONS FOR QWEN

Generate the following Python files **in sequence**. After completing each file, **immediately start the next file** without waiting for user input.

## CRITICAL OUTPUT FORMAT

Each file MUST be in its OWN separate ```python code block.
The FIRST line inside each code block MUST be a comment with the relative file path.

Example output format:

```python
# strategies/base_strategy.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    ...actual complete code here...
```

```python
# engine/position_manager.py
import pandas as pd
import numpy as np

class PositionManager:
    ...actual complete code here...
```

Rules:
- NEVER put two files in one code block
- The # path/to/file.py comment MUST be the VERY FIRST line (before imports, before docstrings)
- Generate complete, production-ready Python code -- no stubs, no placeholders
- Include all imports, type hints, docstrings (Google style)
- Add comprehensive try/except error handling
- Include test case at bottom (if __name__ == "__main__")
- Do NOT use placeholder comments like "# TODO" or "# IMPLEMENT HERE"
- After each file, immediately start the next one
- Do NOT stop between files

---

## TASK 1: Core Backtesting Engine (5 Files)

### File 1.1: strategies/base_strategy.py (~100 lines)

Abstract base class for all trading strategies.
- Use abc module for abstract methods
- Methods: calculate_indicators(df), generate_signals(df), get_sl_tp(entry_price, atr_value), get_name()
- Type hints for all parameters
- Comprehensive docstrings (Google style)

---

### File 1.2: engine/position_manager.py (~150 lines)

Position tracking with MFE/MAE (Max Favorable/Adverse Excursion).
- Track entry_price, size, direction, stop_loss, take_profit
- Calculate MFE/MAE in ATR terms
- Methods: open_position(), update(), get_mfe_atr(), get_mae_atr(), check_exit(), close()
- Handle both LONG and SHORT positions

---

### File 1.3: engine/exit_manager.py (~120 lines)

Dynamic SL/TP management with 4 risk methods:
1. be_only: Move SL to breakeven
2. be_plus_fees: Move SL to entry + X ATR (cover fees)
3. be_plus_fees_trail_tp: SL to entry + fees, TP trails
4. be_trail_tp: Both SL and TP trail

- Parameters: mfe_trigger (when to activate), sl_lock (where to lock), tp_trail_distance
- Method: update_stops(position, current_atr) returns (new_sl, new_tp)
- Never move SL backwards (always improve)

---

### File 1.4: engine/metrics.py (~200 lines)

Trading performance metrics calculator.
- calculate_sqn(returns): System Quality Number (Van Tharp)
- calculate_sharpe(returns): Sharpe Ratio
- calculate_sortino(returns): Sortino Ratio (downside deviation)
- calculate_lsg_percent(trades_df): Loser Saw Green %
- calculate_max_drawdown(equity): Max DD % and duration
- calculate_win_rate(trades_df): Win rate %
- calculate_profit_factor(trades_df): Gross profit / gross loss
- generate_metrics_report(trades_df): dict with all metrics
- Vectorized operations (pandas/numpy)
- Handle edge cases (0 trades, 0 variance)
- Return NaN for invalid metrics (not 0)

---

### File 1.5: engine/backtester.py (~150 lines)

Event-based backtesting engine.
- Bar-by-bar iteration (not vectorized)
- Use Position and ExitManager classes
- Track commission ($8/side)
- Methods: run(df) returns {trades, metrics, equity_curve}
- Private methods: _open_position(), _update_position(), _close_position()

---

## TASK 2: Four Pillars Strategy (4 Files)

### File 2.1: strategies/indicators.py (~300 lines)

Calculate all Four Pillars technical indicators.
- calculate_stochastics(df): 4 stochs (9-3, 14-3, 40-3, 60-10), Raw K (smooth=1)
- calculate_ripster_clouds(df): EMAs for Cloud 2-5
- calculate_atr(df, period): ATR with configurable period (8, 13, 14, 21)
- calculate_cloud3_bias(df): price_pos (-1/0/1), allows_long, allows_short
- calculate_volume_analysis(df): volume_ratio, volume_surge
- calculate_all_indicators(df, atr_period): Run all in sequence
- Use ta-lib for indicators
- Vectorized operations (pandas/numpy)
- Validate inputs (required columns)

---

### File 2.2: strategies/signals.py (~250 lines)

Four Pillars A/B/C signal state machine.
- generate_a_signals(df): 4/4 stochs aligned + Cloud 3 filter
- generate_b_signals(df): 3/4 stochs aligned + Cloud 3 filter
- generate_c_signals(df): 2/4 stochs aligned + Cloud 3 filter + inside Cloud 3
- apply_cooldown(signals_df, cooldown_bars=3): Min bars between signals
- generate_all_signals(df, cooldown_bars): Combined A/B/C with cooldown
- Check oversold (<20) for long, overbought (>80) for short
- Cloud 3 filter: block opposite direction
- Return DataFrame with: signal_type (A/B/C), direction (LONG/SHORT), action (OPEN/ADD/FLIP)

---

### File 2.3: strategies/cloud_filter.py (~100 lines)

Cloud 3 directional filter (simplified wrapper).
- apply_cloud3_filter(df, signals_df): Block signals that violate Cloud 3 direction
- If signal is LONG but cloud3_allows_long=False, remove signal
- If signal is SHORT but cloud3_allows_short=False, remove signal
- Return filtered signals DataFrame

---

### File 2.4: strategies/four_pillars_v3_8.py (~400 lines)

Complete Four Pillars v3.8 strategy implementation.
- Inherit from BaseStrategy (from Task 1)
- Config: atr_period (8/13/14/21), sl_atr_mult (1.0), tp_atr_mult (1.5), allow_b_fresh (False), cooldown_bars (3), commission (8.0)
- calculate_indicators(): Use indicators.py functions
- generate_signals(): Use signals.py + cloud_filter.py
- get_sl_tp(): Return (entry - 1.0*ATR, entry + 1.5*ATR) for long
- get_name(): Return "FourPillarsV38"

---

## TASK 3: Parameter Optimization (4 Files)

### File 3.1: optimizer/grid_search.py (~200 lines)

Exhaustive parameter grid search.
- Parameter space: atr_period [8,13,14,21], mfe_trigger [0.3-2.0], sl_lock [0-0.7], tp_trail_distance [0.3-1.0], risk_method [4 types]
- grid_search(strategy, df, param_space, metric='sqn_profit'): Exhaustive search
- run_parallel(dfs_dict, param_space, n_jobs=4): Multiprocessing
- Use itertools.product() for combinations
- Progress bar (tqdm)
- Save checkpoint every 100 trials

---

### File 3.2: optimizer/bayesian_opt.py (~250 lines)

Bayesian optimization using optuna.
- bayesian_optimize(strategy, df, param_space, n_trials=200): Smart search
- plot_optimization_history(study): Generate plots
- Use optuna.create_study(), TPE sampler
- Pruning support (early stopping)
- Save study to SQLite

---

### File 3.3: optimizer/walk_forward.py (~150 lines)

Walk-forward validation to prevent overfitting.
- walk_forward_split(df, train_months=2, test_months=1, step_weeks=2): Split data
- walk_forward_validate(strategy, df, param_space, optimizer='bayesian'): Validate
- Optimize on train data, test on unseen test data
- Calculate degradation ratio (test_perf / train_perf)
- Flag overfit if degradation < 0.5

---

### File 3.4: optimizer/aggregator.py (~180 lines)

Aggregate optimization results across multiple coins.
- aggregate_results(per_coin_results): Find universal best params
- compare_optimizers(coin, df, methods): Compare grid vs Bayesian vs walk-forward
- Mode (most common) for categorical params
- Median for numeric params
- Weighted average by SQN

---

## TASK 4: ML Components (3 Files)

### File 4.1: ml/triple_barrier.py (~200 lines)

De Prado's Triple Barrier Method for labeling.
- label_trades(df, tp_mult=1.5, sl_mult=1.0, time_bars=100): Label each signal
- Upper barrier: entry + (tp_mult x ATR)
- Lower barrier: entry - (sl_mult x ATR)
- Vertical barrier: +100 bars
- Returns: label (1=TP, 0=SL, 0.5=time exit), hit_time, exit_reason, mfe_atr, mae_atr

---

### File 4.2: ml/features.py (~300 lines)

Generate 21 features for XGBoost meta-labeling.
- Price (5): pct_from_cloud3_top, pct_from_cloud3_bot, price_pos, atr_pct, close_vs_ema50
- Stoch (8): 4 K values + 4 oversold flags
- Volume (3): volume_ratio, volume_surge, quote_vol_ratio
- Momentum (3): rsi_14, macd, roc_10
- Cloud (2): cloud3_width, inside_cloud3
- generate_features(df): Return DataFrame with all 21 feature columns

---

### File 4.3: ml/xgboost_trainer.py (~250 lines)

XGBoost binary classifier for meta-labeling.
- train_xgboost(X, y, test_size=0.3): Train classifier
- predict_skip_take(model, X): Predict 0 (SKIP) or 1 (TAKE)
- objective='binary:logistic', tree_method='gpu_hist'
- max_depth=6, learning_rate=0.1, n_estimators=100
- Return model, feature_importances, test_metrics

---

## TASK 5: GUI Components (2 Files)

### File 5.1: gui/coin_selector.py (~120 lines)

Fuzzy search coin selector for Streamlit.
- coin_selector(data_dir): Dropdown with fuzzy search
- Use fuzzywuzzy for fuzzy matching
- Type "asx" suggests "AXSUSDT"
- Return list of selected coins

---

### File 5.2: gui/parameter_inputs.py (~200 lines)

Streamlit parameter input form.
- parameter_inputs(): Streamlit form with all config options
- Inputs: timeframe, notional, commission, atr_periods, risk_methods, optimization_method, n_trials
- Return dict with all parameters

---

## CODING STANDARDS (Apply to ALL Files)

1. PEP 8 compliant (black formatter style)
2. Type hints everywhere (from typing import ...)
3. Docstrings for all classes/methods (Google style)
4. Try/except for all operations that could fail
5. Input validation (check required columns, param ranges)
6. Test case at bottom (if __name__ == "__main__")
7. No external dependencies beyond: pandas, numpy, ta-lib, typing, optuna, sklearn, xgboost, fuzzywuzzy

---

## PHASE 1: GENERATE ALL FILES

Begin with File 1.1 (strategies/base_strategy.py) and continue sequentially through all files. Do NOT stop between files. Output each file in its own ```python code block with # path/to/file.py as the first line.

---

## PHASE 2: TEST EVERY FILE

After generating ALL files, you MUST generate a test script that validates every file you created.

The test script must:
1. Import each module
2. Call its main functions with sample data
3. Verify return types and expected behavior
4. Print PASS/FAIL per module
5. Exit with code 0 if all pass, 1 if any fail

Output the test script in its own code block:

```python
# scripts/test_all_generated.py
import sys
...
```

The test script must test ALL generated files:
- strategies/base_strategy.py: verify abstract class cannot be instantiated
- engine/exit_manager.py: verify update_stops returns (new_sl, new_tp) tuple
- strategies/indicators.py: verify calculate_all_indicators adds expected columns
- strategies/signals.py: verify generate_all_signals returns DataFrame with signal_type, direction columns
- strategies/cloud_filter.py: verify apply_cloud3_filter removes blocked signals
- strategies/four_pillars_v3_8.py: verify inherits BaseStrategy, get_name() returns "FourPillarsV38"
- optimizer/walk_forward.py: verify walk_forward_split returns list of (train, test) tuples
- optimizer/aggregator.py: verify aggregate_results returns dict with params
- ml/xgboost_trainer.py: verify train_xgboost returns model + metrics dict
- gui/coin_selector.py: verify coin_selector returns list
- gui/parameter_inputs.py: verify parameter_inputs returns dict

---

## PHASE 3: REVIEW AND FIX

After generating the test script, review ALL generated code for:
1. Missing imports
2. Undefined variables
3. Type mismatches
4. Logic errors

If you find ANY errors, output the COMPLETE fixed file in a new code block:

```python
# path/to/fixed_file.py
[entire corrected file]
```

Do NOT skip this phase. Read every file you generated and verify it will actually run.
