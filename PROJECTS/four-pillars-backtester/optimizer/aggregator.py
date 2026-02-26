"""
Aggregate optimization results across multiple coins.
Find universal best parameters via mode (categorical) and median (numeric).
"""

import numpy as np
import pandas as pd
from collections import Counter
from typing import Any


def aggregate_results(per_coin_results: dict[str, dict]) -> dict[str, Any]:
    """
    Find universal best parameters across all coins.

    Uses mode for categorical params, weighted median for numeric.
    Weight = SQN (or sharpe if SQN not available).

    Args:
        per_coin_results: {coin_name: {param_name: best_value, "sharpe": x, ...}}

    Returns:
        dict with aggregated best params and per-coin summary.
    """
    if not per_coin_results:
        return {"params": {}, "coins": 0, "summary": []}

    all_params = {}
    weights = {}

    for coin, result in per_coin_results.items():
        w = result.get("sqn", result.get("sharpe", 1.0))
        weights[coin] = max(w, 0.01)

        for key, val in result.items():
            if key in ("sharpe", "sqn", "net_pnl", "total_trades", "win_rate",
                       "max_drawdown", "profit_factor"):
                continue
            if key not in all_params:
                all_params[key] = []
            all_params[key].append((val, weights[coin]))

    aggregated = {}
    for param, values_weights in all_params.items():
        vals = [v for v, w in values_weights]

        # Categorical: use mode
        if isinstance(vals[0], str):
            counts = Counter(vals)
            aggregated[param] = counts.most_common(1)[0][0]
        else:
            # Numeric: weighted median
            w_arr = np.array([w for v, w in values_weights])
            v_arr = np.array([float(v) for v, w in values_weights])
            sorted_idx = np.argsort(v_arr)
            v_sorted = v_arr[sorted_idx]
            w_sorted = w_arr[sorted_idx]
            cum_w = np.cumsum(w_sorted)
            half = cum_w[-1] / 2.0
            idx = np.searchsorted(cum_w, half)
            aggregated[param] = float(v_sorted[min(idx, len(v_sorted) - 1)])

    summary = []
    for coin, result in per_coin_results.items():
        summary.append({
            "coin": coin,
            "weight": weights[coin],
            **{k: v for k, v in result.items()
               if k in ("sharpe", "net_pnl", "total_trades", "win_rate")},
        })

    return {
        "params": aggregated,
        "coins": len(per_coin_results),
        "summary": summary,
    }


def compare_optimizers(results_by_method: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Compare grid search vs Bayesian vs walk-forward results.

    Args:
        results_by_method: {"grid": df, "bayesian": df, "walk_forward": df}

    Returns:
        Summary DataFrame with best params and metrics per method.
    """
    rows = []
    for method, df in results_by_method.items():
        if len(df) == 0:
            continue
        best_idx = df["sharpe"].idxmax() if "sharpe" in df.columns else 0
        best = df.iloc[best_idx] if isinstance(best_idx, int) else df.loc[best_idx]
        rows.append({
            "method": method,
            "best_sharpe": best.get("sharpe", 0),
            "best_net_pnl": best.get("net_pnl", 0),
            "trials": len(df),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    results = {
        "RIVERUSDT": {"sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3, "risk_method": "be_only", "sharpe": 1.8},
        "KITEUSDT": {"sl_mult": 1.2, "tp_mult": 1.5, "cooldown": 5, "risk_method": "be_plus_fees", "sharpe": 1.2},
        "1000PEPEUSDT": {"sl_mult": 1.0, "tp_mult": 2.0, "cooldown": 3, "risk_method": "be_only", "sharpe": 0.9},
    }
    agg = aggregate_results(results)
    print(f"PASS -- aggregated {agg['coins']} coins, params: {agg['params']}")
