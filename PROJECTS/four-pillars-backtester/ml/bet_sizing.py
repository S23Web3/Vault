"""
Bet Sizing from Meta-Label Probabilities (De Prado Ch 10).

Converts model probability output to position size.
User sets the sizing curve parameters (threshold, max size, scaling).

Three methods:
  1. Binary: prob >= threshold -> full size, else skip
  2. Linear: size scales linearly from 0 at threshold to max at 1.0
  3. Kelly: f* = (p * b - q) / b  where p=prob, q=1-p, b=avg_win/avg_loss

Input: array of probabilities from meta-label model.
Output: array of position sizes (0.0 to 1.0 as fraction of max size).
"""

import numpy as np


def binary_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5) -> np.ndarray:
    """
    Binary bet sizing: above threshold = full size, below = skip.

    Args:
        probabilities: array of model probabilities (0 to 1).
        threshold: minimum probability to take the trade.

    Returns:
        array of sizes: 1.0 (take) or 0.0 (skip).
    """
    return (probabilities >= threshold).astype(float)


def linear_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5,
                  max_size: float = 1.0) -> np.ndarray:
    """
    Linear bet sizing: size scales from 0 at threshold to max_size at 1.0.

    Args:
        probabilities: array of model probabilities (0 to 1).
        threshold: minimum probability to take the trade.
        max_size: maximum position size (fraction of notional).

    Returns:
        array of sizes (0.0 to max_size).
    """
    sizes = np.zeros_like(probabilities)
    above = probabilities >= threshold
    if above.any():
        # Scale: threshold->0, 1.0->max_size
        scale_range = 1.0 - threshold
        if scale_range > 0:
            sizes[above] = ((probabilities[above] - threshold) / scale_range) * max_size
        else:
            sizes[above] = max_size
    return sizes


def kelly_sizing(probabilities: np.ndarray,
                 avg_win: float,
                 avg_loss: float,
                 max_size: float = 1.0,
                 fraction: float = 0.5) -> np.ndarray:
    """
    Kelly criterion bet sizing: optimal fraction based on edge.

    f* = (p * b - q) / b
    where p = win probability, q = 1-p, b = avg_win / |avg_loss|

    Uses fractional Kelly (default 0.5) for safety.

    Args:
        probabilities: array of win probabilities from model.
        avg_win: average winning trade P&L (positive number).
        avg_loss: average losing trade P&L (negative number, will be abs'd).
        max_size: cap on maximum position size.
        fraction: Kelly fraction (0.5 = half-Kelly, safer).

    Returns:
        array of sizes (0.0 to max_size). Negative Kelly = skip.
    """
    if avg_win <= 0 or avg_loss >= 0:
        return np.zeros_like(probabilities)

    b = avg_win / abs(avg_loss)  # odds ratio
    q = 1.0 - probabilities
    kelly_f = (probabilities * b - q) / b

    # Apply fractional Kelly
    kelly_f *= fraction

    # Clip to [0, max_size]
    sizes = np.clip(kelly_f, 0.0, max_size)

    return sizes


def get_sizing_summary(sizes: np.ndarray) -> dict:
    """
    Summarize sizing decisions.

    Args:
        sizes: array of position sizes (0.0 to 1.0).

    Returns:
        dict with skip count, take count, avg size, etc.
    """
    total = len(sizes)
    skipped = int(np.sum(sizes == 0))
    taken = total - skipped

    return {
        "total_signals": total,
        "taken": taken,
        "skipped": skipped,
        "skip_rate": skipped / total if total > 0 else 0,
        "avg_size": float(np.mean(sizes[sizes > 0])) if taken > 0 else 0,
        "min_size": float(np.min(sizes[sizes > 0])) if taken > 0 else 0,
        "max_size": float(np.max(sizes[sizes > 0])) if taken > 0 else 0,
    }
