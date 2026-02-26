"""
Purged K-Fold Cross-Validation (De Prado Ch 7).

Standard K-Fold leaks information because trades near fold boundaries
overlap in time. Purged CV removes trades from the training set that
overlap with test set trades, preventing look-ahead bias.

Embargo: additional gap (in bars) between train and test to prevent
autocorrelation leakage.

Input: trades DataFrame with entry_bar and exit_bar columns.
Output: list of (train_indices, test_indices) tuples.
"""

import numpy as np
import pandas as pd


def purged_kfold_split(trades_df: pd.DataFrame,
                       n_splits: int = 5,
                       embargo_bars: int = 10) -> list:
    """
    Generate purged K-fold splits based on trade entry_bar ordering.

    Trades are sorted by entry_bar. Each fold is a contiguous block.
    Training set excludes trades whose [entry_bar, exit_bar] overlaps
    with the test fold window, plus an embargo buffer.

    Args:
        trades_df: DataFrame with entry_bar and exit_bar columns.
        n_splits: Number of folds.
        embargo_bars: Extra bars of gap between train and test.

    Returns:
        List of (train_indices, test_indices) tuples.
        Indices refer to positions in the sorted trades_df.
    """
    n = len(trades_df)
    if n < n_splits:
        raise ValueError(f"Need at least {n_splits} trades for {n_splits}-fold CV, got {n}")

    # Sort by entry time
    sorted_df = trades_df.sort_values("entry_bar").reset_index(drop=True)
    entry_bars = sorted_df["entry_bar"].values
    exit_bars = sorted_df["exit_bar"].values

    # Split into n_splits contiguous blocks by index
    fold_size = n // n_splits
    folds = []
    for k in range(n_splits):
        start = k * fold_size
        end = start + fold_size if k < n_splits - 1 else n
        folds.append((start, end))

    splits = []
    for test_start, test_end in folds:
        # Test set boundaries in bar space
        test_bar_start = entry_bars[test_start]
        test_bar_end = exit_bars[test_end - 1]

        # Purge zone: test window expanded by embargo
        purge_start = test_bar_start - embargo_bars
        purge_end = test_bar_end + embargo_bars

        test_idx = list(range(test_start, test_end))
        train_idx = []

        for i in range(n):
            if i in range(test_start, test_end):
                continue
            # Check overlap: trade [entry, exit] vs purge zone [purge_start, purge_end]
            trade_entry = entry_bars[i]
            trade_exit = exit_bars[i]
            overlaps = trade_entry <= purge_end and trade_exit >= purge_start
            if not overlaps:
                train_idx.append(i)

        splits.append((train_idx, test_idx))

    return splits


def get_split_summary(splits: list, total_trades: int) -> list:
    """
    Summarize each split: train size, test size, purged count.

    Args:
        splits: list of (train_indices, test_indices) from purged_kfold_split.
        total_trades: total number of trades.

    Returns:
        list of dicts with fold stats.
    """
    summaries = []
    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        purged = total_trades - len(train_idx) - len(test_idx)
        summaries.append({
            "fold": fold_idx + 1,
            "train": len(train_idx),
            "test": len(test_idx),
            "purged": purged,
            "train_pct": len(train_idx) / total_trades * 100,
        })
    return summaries
