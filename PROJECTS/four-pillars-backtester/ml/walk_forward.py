"""
Walk-Forward Validation (Jansen Ch 7).

Divides data into rolling windows:
  - In-sample (IS): train the model
  - Out-of-sample (OOS): test on unseen data
  - Roll forward, repeat

Walk Forward Efficiency (WFE) = OOS return / IS return.
  WFE > 60%  = robust
  WFE 30-60% = marginal
  WFE < 30%  = overfit

Input: trades DataFrame, feature matrix, labels.
Output: per-window metrics, concatenated OOS equity curve.
"""

import numpy as np
import pandas as pd


def generate_windows(n_trades: int,
                     is_ratio: float = 0.7,
                     min_trades_per_window: int = 100,
                     step_ratio: float = 0.3) -> list:
    """
    Generate rolling IS/OOS windows.

    Args:
        n_trades: total number of trades in dataset.
        is_ratio: fraction of window for in-sample (0.7 = 70%).
        min_trades_per_window: minimum trades in IS window.
        step_ratio: how far to roll forward each step (as fraction of window).

    Returns:
        list of dicts with is_start, is_end, oos_start, oos_end indices.
    """
    window_size = int(min_trades_per_window / is_ratio)
    step = max(1, int(window_size * step_ratio))
    is_size = int(window_size * is_ratio)

    windows = []
    pos = 0

    while pos + window_size <= n_trades:
        is_start = pos
        is_end = pos + is_size
        oos_start = is_end
        oos_end = min(pos + window_size, n_trades)

        windows.append({
            "is_start": is_start,
            "is_end": is_end,
            "oos_start": oos_start,
            "oos_end": oos_end,
            "is_size": is_end - is_start,
            "oos_size": oos_end - oos_start,
        })

        pos += step

    return windows


def compute_wfe(is_metric: float, oos_metric: float) -> float:
    """
    Compute Walk Forward Efficiency.

    Args:
        is_metric: in-sample performance metric (e.g. Sharpe, net PnL).
        oos_metric: out-of-sample performance metric.

    Returns:
        WFE as ratio (0 to 1+). Above 0.6 = robust.
    """
    if is_metric == 0:
        return 0.0
    return oos_metric / is_metric


def get_wfe_rating(wfe: float) -> str:
    """
    Rate the WFE value.

    Args:
        wfe: Walk Forward Efficiency ratio.

    Returns:
        Rating string: "ROBUST", "MARGINAL", or "OVERFIT".
    """
    if wfe >= 0.6:
        return "ROBUST"
    elif wfe >= 0.3:
        return "MARGINAL"
    else:
        return "OVERFIT"


def summarize_walk_forward(window_results: list) -> dict:
    """
    Summarize walk-forward analysis across all windows.

    Args:
        window_results: list of dicts with is_metric, oos_metric per window.

    Returns:
        dict with avg WFE, per-window WFE, overall rating.
    """
    if not window_results:
        return {"n_windows": 0, "avg_wfe": 0, "rating": "NO_DATA"}

    wfes = []
    for w in window_results:
        wfe = compute_wfe(w.get("is_metric", 0), w.get("oos_metric", 0))
        wfes.append(wfe)

    avg_wfe = float(np.mean(wfes)) if wfes else 0

    return {
        "n_windows": len(window_results),
        "wfes": wfes,
        "avg_wfe": avg_wfe,
        "min_wfe": float(np.min(wfes)) if wfes else 0,
        "max_wfe": float(np.max(wfes)) if wfes else 0,
        "rating": get_wfe_rating(avg_wfe),
    }
