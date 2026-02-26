"""
Grid search — coarse sweep over parameter space.
Parallel across CPU cores per coin.
"""

import itertools
import numpy as np
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signals.four_pillars import compute_signals
from engine.backtester import Backtester


def _run_single(df_path: str, signal_params: dict, bt_overrides: dict) -> dict:
    """Run one backtest combo. Designed for multiprocessing."""
    df = pd.read_parquet(df_path)
    df = compute_signals(df, signal_params)

    bt = Backtester(bt_overrides)
    results = bt.run(df)
    m = results["metrics"]

    return {
        **bt_overrides,
        "total_trades": m["total_trades"],
        "win_rate": m["win_rate"],
        "expectancy": m["expectancy"],
        "net_pnl": m["net_pnl"],
        "profit_factor": m["profit_factor"],
        "sharpe": m["sharpe"],
        "max_drawdown": m["max_drawdown"],
        "max_drawdown_pct": m["max_drawdown_pct"],
        "pct_losers_saw_green": m["pct_losers_saw_green"],
        "be_raised_count": m["be_raised_count"],
    }


def grid_search(
    symbol: str,
    cache_dir: str,
    signal_params: dict,
    param_grid: dict,
    base_params: dict = None,
    max_workers: int = 4,
) -> pd.DataFrame:
    """
    Run grid search over parameter combinations.

    Args:
        symbol: Symbol to test
        cache_dir: Path to Parquet cache
        signal_params: Signal computation parameters
        param_grid: Dict of param_name → list of values to test
            Example: {"sl_mult": [0.5, 1.0, 1.5], "tp_mult": [1.0, 1.5, 2.0]}
        base_params: Base backtest parameters (grid values override these)
        max_workers: Number of parallel workers

    Returns:
        DataFrame with one row per parameter combination + metrics
    """
    if base_params is None:
        base_params = {
            "cooldown": 3,
            "b_open_fresh": True,
            "commission_rate": 0.0008,
            "notional": 10000.0,
            "rebate_pct": 0.70,
            "settlement_hour_utc": 17,
        }

    # Build all combos
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combos = list(itertools.product(*values))
    print(f"Grid search: {len(combos)} combinations for {symbol}")

    df_path = str(Path(cache_dir) / f"{symbol}_1m.parquet")

    results = []
    # Pre-compute signals once (save to temp parquet)
    df = pd.read_parquet(df_path)
    df = compute_signals(df, signal_params)
    temp_path = str(Path(cache_dir) / f"_temp_{symbol}_signals.parquet")
    df.to_parquet(temp_path)

    for idx, combo in enumerate(combos):
        bt_params = dict(base_params)
        for k, v in zip(keys, combo):
            bt_params[k] = v

        bt = Backtester(bt_params)
        res = bt.run(df)
        m = res["metrics"]

        row = dict(zip(keys, combo))
        row.update({
            "total_trades": m["total_trades"],
            "win_rate": m["win_rate"],
            "expectancy": m["expectancy"],
            "net_pnl": m["net_pnl"],
            "profit_factor": m["profit_factor"],
            "sharpe": m["sharpe"],
            "max_drawdown": m["max_drawdown"],
            "pct_losers_saw_green": m["pct_losers_saw_green"],
        })
        results.append(row)

        if (idx + 1) % 50 == 0:
            print(f"  {idx + 1}/{len(combos)} done")

    # Cleanup temp
    Path(temp_path).unlink(missing_ok=True)

    results_df = pd.DataFrame(results)
    print(f"Grid search complete: {len(results_df)} results")
    return results_df


# Default grid for quick testing
DEFAULT_GRID = {
    "sl_mult": [0.5, 0.75, 1.0, 1.5, 2.0],
    "tp_mult": [0.5, 1.0, 1.5, 2.0, 3.0],
    "be_raise_amount": [0, 2, 5, 10, 20],
    "cooldown": [0, 3, 5, 10],
}
