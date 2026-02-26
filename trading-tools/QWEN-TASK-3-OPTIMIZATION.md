# Qwen Task 3: Parameter Optimization Engine

**Priority**: 🔴 CRITICAL (needed to find optimal parameters)
**Files**: 4 Python files (~780 lines)
**Estimated Time**: 5-7 hours

---

## Overview

Generate parameter optimization modules for finding optimal exit parameters across multiple coins.

---

## File 1: Grid Search (optimizer/grid_search.py)

**Lines**: ~200

Generate complete grid search optimizer.

**Parameter Space**:
```python
PARAM_SPACE = {
    'atr_period': [8, 13, 14, 21],
    'mfe_trigger': [0.3, 0.5, 0.7, 1.0, 1.5, 2.0],
    'sl_lock': [0, 0.2, 0.3, 0.5, 0.7],
    'tp_trail_distance': [0.3, 0.5, 0.7, 1.0],
    'risk_method': ['be_only', 'be_plus_fees', 'be_plus_fees_trail_tp', 'be_trail_tp'],
}
```

**Functions**:
```python
def grid_search(strategy, df, param_space, metric='sqn_profit'):
    """
    Exhaustive parameter sweep.

    Args:
        strategy: Strategy class to optimize
        df: OHLCV DataFrame with indicators
        param_space: dict of parameter ranges
        metric: 'sqn_profit' (SQN × Total Profit)

    Returns:
        results_df: DataFrame with all combinations sorted by metric
    """

def run_parallel_grid_search(strategy, dfs_dict, param_space, n_jobs=4):
    """
    Run grid search on multiple coins in parallel using multiprocessing.

    Args:
        dfs_dict: {coin: df} dictionary
        n_jobs: number of parallel processes

    Returns:
        per_coin_results: dict of {coin: best_params}
    """
```

**Requirements**:
- Use itertools.product() for all combinations
- Multiprocessing support (ProcessPoolExecutor)
- Progress bar (tqdm)
- Comprehensive error handling
- Save checkpoint every 100 trials (resume if crashed)

---

## File 2: Bayesian Optimization (optimizer/bayesian_opt.py)

**Lines**: ~250

Generate Bayesian optimizer using optuna library.

**Functions**:
```python
def bayesian_optimize(strategy, df, param_space, n_trials=200, metric='sqn_profit'):
    """
    Smart parameter search using Bayesian optimization.

    Uses optuna TPE sampler (Tree-structured Parzen Estimator).

    Args:
        strategy: Strategy class
        df: OHLCV DataFrame
        param_space: dict of parameter ranges
        n_trials: number of trials (default 200)
        metric: optimization objective

    Returns:
        study: optuna.Study object with best params and history
    """

def plot_optimization_history(study):
    """Generate optimization history plots using plotly."""
```

**Requirements**:
- Use optuna.create_study()
- Support pruning (early stopping for bad trials)
- Categorical, Float, Int parameter types
- Save study to SQLite database (for resume)
- Generate 3 plots: history, parallel coordinate, importance

---

## File 3: Walk-Forward Validation (optimizer/walk_forward.py)

**Lines**: ~150

Generate walk-forward validator to prevent overfitting.

**Functions**:
```python
def walk_forward_split(df, train_months=2, test_months=1, step_weeks=2):
    """
    Split data into overlapping train/test windows.

    Example:
        Train: Jan-Feb, Test: Mar
        Train: Jan 15-Mar 15, Test: Mar 15-Apr 15
        Train: Feb-Mar, Test: Apr

    Returns:
        windows: list of (train_df, test_df, window_id) tuples
    """

def walk_forward_validate(strategy, df, param_space, optimizer='bayesian'):
    """
    For each window:
        1. Optimize on train data
        2. Test on unseen test data
        3. Record OOS performance

    Returns:
        oos_results: DataFrame with train/test performance per window
        is_overfit: bool (test profit < 0.5 × train profit)
    """
```

**Requirements**:
- Use pandas date_range for window splitting
- Support both grid and Bayesian optimizers
- Calculate degradation ratio (test_performance / train_performance)
- Flag overfit if degradation > 50%

---

## File 4: Multi-Coin Aggregator (optimizer/aggregator.py)

**Lines**: ~180

Generate aggregator to find universal best practices.

**Functions**:
```python
def aggregate_results(per_coin_results):
    """
    Find "universal best practice" parameters across all coins.

    Args:
        per_coin_results: {coin: {'params': {...}, 'metrics': {...}}}

    Returns:
        universal_params: dict (most common or median values)
        performance_table: DataFrame with all coins + universal
    """

def compare_optimizers(coin, df, methods=['grid', 'bayesian', 'walk_forward']):
    """
    Compare 3 optimization methods on same data.

    Returns:
        comparison_df: DataFrame with time, trials, best_sqn, best_profit
    """
```

**Requirements**:
- Calculate mode (most common) for categorical params
- Calculate median for numeric params
- Weighted average by SQN (better coins have more influence)
- Generate comparison table (CSV export)

---

## Output Format

For each file:
1. Complete Python file with imports
2. Type hints for all functions
3. Docstrings (Google style)
4. Try/except error handling
5. Test case at bottom

## Dependencies

- optuna>=3.0.0
- scikit-learn>=1.3.0
- tqdm>=4.65.0
- plotly>=5.17.0
- joblib>=1.3.0 (for multiprocessing)

---

**Paste this to Qwen after Strategy components complete (Task 2).**
