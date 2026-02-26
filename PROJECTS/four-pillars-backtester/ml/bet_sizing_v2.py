"""
Bet Sizing v2 -- bug fixes applied.

Fixes from v1:
  - Kelly avg_loss=0 guard now logs warning instead of silent zero-return
  - Negative edge logged as warning
"""

import logging
import numpy as np

log = logging.getLogger(__name__)


def binary_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5) -> np.ndarray:
    """Binary bet sizing: above threshold = full size, below = skip."""
    return (probabilities >= threshold).astype(float)


def linear_sizing(probabilities: np.ndarray,
                  threshold: float = 0.5,
                  max_size: float = 1.0) -> np.ndarray:
    """Linear bet sizing: size scales from 0 at threshold to max_size at 1.0."""
    sizes = np.zeros_like(probabilities)
    above = probabilities >= threshold
    if above.any():
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
    """Kelly criterion bet sizing with fractional Kelly for safety."""
    # FIX: log warning instead of silent zero-return
    if avg_win <= 0:
        log.warning("kelly_sizing: avg_win <= 0 (%.4f), returning zeros", avg_win)
        return np.zeros_like(probabilities)
    if avg_loss >= 0:
        log.warning("kelly_sizing: avg_loss >= 0 (%.4f), expected negative. Returning zeros", avg_loss)
        return np.zeros_like(probabilities)

    b = avg_win / abs(avg_loss)
    q = 1.0 - probabilities
    kelly_f = (probabilities * b - q) / b

    # Log negative edge trades
    n_negative = int(np.sum(kelly_f < 0))
    if n_negative > 0:
        log.info("kelly_sizing: %d/%d trades have negative edge (will be clipped to 0)",
                 n_negative, len(kelly_f))

    kelly_f *= fraction
    sizes = np.clip(kelly_f, 0.0, max_size)
    return sizes


def get_sizing_summary(sizes: np.ndarray) -> dict:
    """Summarize sizing decisions."""
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
