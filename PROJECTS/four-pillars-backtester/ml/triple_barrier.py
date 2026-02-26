"""
Triple Barrier Labeling (De Prado Ch 3).

Labels each trade based on which barrier was hit first:
  +1 = TP hit (upper barrier)
  -1 = SL hit (lower barrier)
   0 = time barrier (expired / flipped / ended)

This replaces simple win/loss classification with a 3-class label
that captures HOW the trade ended, not just whether it made money.

Input: trades DataFrame from backtester.
Output: array of labels {-1, 0, +1} aligned to trades.
"""

import numpy as np
import pandas as pd


def label_trades(trades_df: pd.DataFrame) -> np.ndarray:
    """
    Assign triple barrier labels to each trade.

    Args:
        trades_df: DataFrame with exit_reason column.
                   exit_reason values: "TP", "SL", "FLIP", "END", "SIGNAL".

    Returns:
        numpy array of labels: +1 (TP), -1 (SL), 0 (other).
    """
    labels = np.zeros(len(trades_df), dtype=int)

    for idx, reason in enumerate(trades_df["exit_reason"].values):
        if reason == "TP":
            labels[idx] = 1
        elif reason == "SL":
            labels[idx] = -1
        else:
            # FLIP, END, SIGNAL = time/event barrier
            labels[idx] = 0

    return labels


def label_trades_by_pnl(trades_df: pd.DataFrame,
                        draw_zone: float = 0.0) -> np.ndarray:
    """
    Alternative labeling: by net P&L with optional draw zone.

    Args:
        trades_df: DataFrame with pnl and commission columns.
        draw_zone: Trades with |net_pnl| <= draw_zone are labeled 0 (draw).

    Returns:
        numpy array of labels: +1 (win), -1 (loss), 0 (draw).
    """
    net_pnl = (trades_df["pnl"] - trades_df["commission"]).values
    labels = np.zeros(len(net_pnl), dtype=int)

    for idx, pnl in enumerate(net_pnl):
        if pnl > draw_zone:
            labels[idx] = 1
        elif pnl < -draw_zone:
            labels[idx] = -1
        # else stays 0

    return labels


def get_label_distribution(labels: np.ndarray) -> dict:
    """
    Return counts and percentages for each label class.

    Args:
        labels: array of {-1, 0, +1} labels.

    Returns:
        dict with counts and percentages per class.
    """
    total = len(labels)
    if total == 0:
        return {"total": 0}

    return {
        "total": total,
        "tp_count": int(np.sum(labels == 1)),
        "sl_count": int(np.sum(labels == -1)),
        "other_count": int(np.sum(labels == 0)),
        "tp_pct": float(np.mean(labels == 1)),
        "sl_pct": float(np.mean(labels == -1)),
        "other_pct": float(np.mean(labels == 0)),
    }
