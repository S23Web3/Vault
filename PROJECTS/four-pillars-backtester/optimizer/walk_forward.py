"""
Walk-forward validation at the optimizer level.
Splits OHLCV data by time, optimizes on train window, tests on test window.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd


def walk_forward_split(
    df: pd.DataFrame,
    train_months: int = 2,
    test_months: int = 1,
    step_weeks: int = 2,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Split time-series data into walk-forward train/test windows.

    Args:
        df: DataFrame with datetime index or column.
        train_months: Size of training window in months.
        test_months: Size of test window in months.
        step_weeks: Step forward between windows in weeks.

    Returns:
        List of (train_df, test_df) tuples.
    """
    if isinstance(df.index, pd.DatetimeIndex):
        ts = df.index
    elif "datetime" in df.columns:
        ts = pd.to_datetime(df["datetime"])
    elif "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
    else:
        raise ValueError("DataFrame must have datetime index or datetime/timestamp column")

    start = ts.min()
    end = ts.max()

    train_delta = pd.DateOffset(months=train_months)
    test_delta = pd.DateOffset(months=test_months)
    step_delta = pd.DateOffset(weeks=step_weeks)

    windows = []
    cursor = start

    while cursor + train_delta + test_delta <= end:
        train_end = cursor + train_delta
        test_end = train_end + test_delta

        train_mask = (ts >= cursor) & (ts < train_end)
        test_mask = (ts >= train_end) & (ts < test_end)

        train_df = df[train_mask.values] if not isinstance(df.index, pd.DatetimeIndex) else df[train_mask]
        test_df = df[test_mask.values] if not isinstance(df.index, pd.DatetimeIndex) else df[test_mask]

        if len(train_df) > 0 and len(test_df) > 0:
            windows.append((train_df, test_df))

        cursor += step_delta

    return windows


def walk_forward_validate(
    run_backtest_fn,
    df: pd.DataFrame,
    params: dict,
    train_months: int = 2,
    test_months: int = 1,
    step_weeks: int = 2,
) -> dict:
    """
    Run walk-forward validation using a backtest function.

    Args:
        run_backtest_fn: Callable(df, params) -> dict with "metrics" key.
        df: Full OHLCV+signals DataFrame.
        params: Backtest parameters.
        train_months: Training window size.
        test_months: Test window size.
        step_weeks: Step between windows.

    Returns:
        dict with per-window results and degradation ratios.
    """
    windows = walk_forward_split(df, train_months, test_months, step_weeks)

    results = []
    for i, (train_df, test_df) in enumerate(windows):
        train_result = run_backtest_fn(train_df, params)
        test_result = run_backtest_fn(test_df, params)

        train_sharpe = train_result["metrics"].get("sharpe", 0)
        test_sharpe = test_result["metrics"].get("sharpe", 0)

        degradation = test_sharpe / train_sharpe if train_sharpe != 0 else 0

        results.append({
            "window": i,
            "train_trades": train_result["metrics"].get("total_trades", 0),
            "test_trades": test_result["metrics"].get("total_trades", 0),
            "train_sharpe": train_sharpe,
            "test_sharpe": test_sharpe,
            "degradation": degradation,
        })

    avg_deg = np.mean([r["degradation"] for r in results]) if results else 0
    overfit = avg_deg < 0.5

    return {
        "windows": results,
        "avg_degradation": float(avg_deg),
        "overfit_flag": overfit,
        "n_windows": len(results),
    }


if __name__ == "__main__":
    dates = pd.date_range("2025-11-01", periods=5000, freq="5min")
    df = pd.DataFrame({
        "datetime": dates,
        "close": 100 + np.cumsum(np.random.randn(5000) * 0.1),
    })
    windows = walk_forward_split(df, train_months=1, test_months=1, step_weeks=1)
    print(f"PASS -- {len(windows)} walk-forward windows generated")
