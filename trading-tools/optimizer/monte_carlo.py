"""
Monte Carlo validation — final gate for v4.
Three tests: trade reshuffling, parameter perturbation, trade skip.
"""

import numpy as np
import pandas as pd
from typing import Optional


def trade_reshuffle(trade_pnls: np.ndarray, n_iterations: int = 10000,
                    initial_equity: float = 10000.0) -> dict:
    """
    Test 1: Resample trades with replacement.
    Builds N equity curves from reshuffled trade order.
    Returns 5th/50th/95th percentile for final equity, max drawdown, Sharpe.
    """
    n_trades = len(trade_pnls)
    final_equities = []
    max_drawdowns = []
    sharpes = []

    for _ in range(n_iterations):
        sample = np.random.choice(trade_pnls, size=n_trades, replace=True)
        equity_curve = initial_equity + np.cumsum(sample)
        peak = np.maximum.accumulate(equity_curve)
        drawdown = peak - equity_curve

        final_equities.append(equity_curve[-1])
        max_drawdowns.append(np.max(drawdown))
        if np.std(sample) > 0:
            sharpes.append(np.mean(sample) / np.std(sample))
        else:
            sharpes.append(0)

    return {
        "final_equity_5th": np.percentile(final_equities, 5),
        "final_equity_50th": np.percentile(final_equities, 50),
        "final_equity_95th": np.percentile(final_equities, 95),
        "max_dd_5th": np.percentile(max_drawdowns, 5),
        "max_dd_50th": np.percentile(max_drawdowns, 50),
        "max_dd_95th": np.percentile(max_drawdowns, 95),
        "sharpe_5th": np.percentile(sharpes, 5),
        "sharpe_50th": np.percentile(sharpes, 50),
        "sharpe_95th": np.percentile(sharpes, 95),
        "pct_profitable": np.mean(np.array(final_equities) > initial_equity) * 100,
    }


def param_perturbation(run_backtest_fn, base_params: dict,
                       perturbation_pct: float = 0.10,
                       n_iterations: int = 100) -> dict:
    """
    Test 2: Add ±perturbation_pct noise to numeric params.
    If Sharpe drops >50%, params are fragile.

    Args:
        run_backtest_fn: Callable(params) -> dict with "metrics" key
        base_params: Base parameter dict
        perturbation_pct: Max perturbation (0.10 = ±10%)
        n_iterations: Number of perturbation runs
    """
    # Get base Sharpe
    base_result = run_backtest_fn(base_params)
    base_sharpe = base_result["metrics"]["sharpe"]

    sharpes = []
    numeric_keys = [k for k, v in base_params.items() if isinstance(v, (int, float)) and k != "settlement_hour_utc"]

    for _ in range(n_iterations):
        perturbed = dict(base_params)
        for k in numeric_keys:
            noise = 1.0 + np.random.uniform(-perturbation_pct, perturbation_pct)
            val = base_params[k] * noise
            if isinstance(base_params[k], int):
                val = max(0, int(round(val)))
            else:
                val = max(0.0, val)
            perturbed[k] = val

        result = run_backtest_fn(perturbed)
        sharpes.append(result["metrics"]["sharpe"])

    sharpes = np.array(sharpes)
    sharpe_drop = (base_sharpe - np.mean(sharpes)) / base_sharpe * 100 if base_sharpe != 0 else 0

    return {
        "base_sharpe": base_sharpe,
        "mean_perturbed_sharpe": np.mean(sharpes),
        "std_perturbed_sharpe": np.std(sharpes),
        "sharpe_drop_pct": sharpe_drop,
        "fragile": sharpe_drop > 50,
        "pct_still_positive": np.mean(sharpes > 0) * 100,
    }


def trade_skip(trade_pnls: np.ndarray, skip_pct: float = 0.10,
               n_iterations: int = 10000, initial_equity: float = 10000.0) -> dict:
    """
    Test 3: Randomly skip skip_pct of trades.
    If still profitable = survives real execution (missed fills, slippage).
    """
    n_trades = len(trade_pnls)
    n_skip = max(1, int(n_trades * skip_pct))

    final_equities = []

    for _ in range(n_iterations):
        skip_indices = np.random.choice(n_trades, size=n_skip, replace=False)
        mask = np.ones(n_trades, dtype=bool)
        mask[skip_indices] = False
        remaining = trade_pnls[mask]

        final_eq = initial_equity + np.sum(remaining)
        final_equities.append(final_eq)

    final_equities = np.array(final_equities)

    return {
        "trades_skipped": n_skip,
        "skip_pct": skip_pct,
        "final_equity_5th": np.percentile(final_equities, 5),
        "final_equity_50th": np.percentile(final_equities, 50),
        "final_equity_95th": np.percentile(final_equities, 95),
        "pct_profitable": np.mean(final_equities > initial_equity) * 100,
    }


def run_all_tests(trade_pnls: np.ndarray, run_backtest_fn=None,
                  base_params: dict = None, n_iterations: int = 10000) -> dict:
    """Run all 3 Monte Carlo tests and return combined results."""
    results = {}

    print("Running Test 1: Trade Reshuffling...")
    results["reshuffle"] = trade_reshuffle(trade_pnls, n_iterations)

    print("Running Test 3: Trade Skip (10%)...")
    results["skip"] = trade_skip(trade_pnls, 0.10, n_iterations)

    if run_backtest_fn is not None and base_params is not None:
        print("Running Test 2: Parameter Perturbation (±10%)...")
        results["perturbation"] = param_perturbation(run_backtest_fn, base_params, 0.10, min(100, n_iterations))

    # Summary
    results["pass_reshuffle"] = results["reshuffle"]["pct_profitable"] >= 95
    results["pass_skip"] = results["skip"]["pct_profitable"] >= 95
    if "perturbation" in results:
        results["pass_perturbation"] = not results["perturbation"]["fragile"]
    results["all_pass"] = all(results.get(f"pass_{t}", True) for t in ["reshuffle", "skip", "perturbation"])

    return results
