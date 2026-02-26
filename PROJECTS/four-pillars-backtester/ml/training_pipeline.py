"""
VINCE Training Pipeline -- Pool split, data loading, training, validation.

Implements the blind training protocol:
  Pool A (60%): Training -- VINCE sees characteristics + results
  Pool B (20%): Validation -- VINCE predicts, then checks
  Pool C (20%): Holdout -- never touched until final evaluation

Pool assignment stored in data/coin_pools.json.
"""

import os
import json
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple, Optional

# Project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def assign_pools(symbols: List[str], seed: int = 42,
                 pool_file: str = None) -> Dict[str, str]:
    """
    Assign coins to pools A/B/C (60/20/20).
    If pool_file exists, load it. Else generate and save.
    """
    if pool_file is None:
        pool_file = os.path.join(_ROOT, "data", "coin_pools.json")

    if os.path.exists(pool_file) and os.path.getsize(pool_file) > 0:
        with open(pool_file, "r") as f:
            pools = json.load(f)
        # Validate all symbols present
        missing = [s for s in symbols if s not in pools]
        if missing:
            # New coins go to Pool C (holdout)
            for s in missing:
                pools[s] = "C"
            with open(pool_file, "w") as f:
                json.dump(pools, f, indent=2)
        return pools

    rng = random.Random(seed)
    shuffled = list(symbols)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_a = int(n * 0.6)
    n_b = int(n * 0.2)

    pools = {}
    for i, sym in enumerate(shuffled):
        if i < n_a:
            pools[sym] = "A"
        elif i < n_a + n_b:
            pools[sym] = "B"
        else:
            pools[sym] = "C"

    os.makedirs(os.path.dirname(pool_file), exist_ok=True)
    with open(pool_file, "w") as f:
        json.dump(pools, f, indent=2)

    return pools


class TradeDataset(Dataset):
    """Dataset for per-trade features."""

    def __init__(self, features_df: pd.DataFrame, labels: np.ndarray):
        self.features = torch.FloatTensor(features_df.values)
        self.labels = torch.FloatTensor(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def load_trade_parquets(symbols: List[str], timeframe: str = "5m",
                        results_dir: str = None) -> pd.DataFrame:
    """Load and concatenate per-trade parquet files for given symbols."""
    if results_dir is None:
        results_dir = os.path.join(_ROOT, "results")

    frames = []
    for sym in symbols:
        path = os.path.join(results_dir, f"trades_{sym}_{timeframe}.parquet")
        if os.path.exists(path):
            df = pd.read_parquet(path)
            df["symbol"] = sym
            frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def prepare_labels(trades_df: pd.DataFrame) -> np.ndarray:
    """Binary label: 1 if trade is a net winner, 0 otherwise."""
    if "pnl" in trades_df.columns and "commission" in trades_df.columns:
        net = trades_df["pnl"] - trades_df["commission"]
    elif "net_pnl" in trades_df.columns:
        net = trades_df["net_pnl"]
    else:
        net = trades_df.get("pnl", pd.Series(np.zeros(len(trades_df))))
    return (net > 0).astype(float).values


def train_phase1(model, train_loader, val_loader,
                 epochs: int = 50, lr: float = 1e-3,
                 device: str = "cuda" if torch.cuda.is_available() else "cpu"):
    """
    Phase 1 training: tabular + context only.
    Returns training history dict.
    """
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        n_batch = 0
        for features, labels in train_loader:
            features = features.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            # For Phase 1, we use predict_tabular_only
            # Features layout: [numeric (22) | grade_idx (1) | dir_idx (1) |
            #                   path_idx (1) | coin_features (10)]
            numeric = features[:, :22]
            grade = features[:, 22].long()
            dir_idx = features[:, 23].long()
            path_idx = features[:, 24].long()
            coin_ctx = features[:, 25:35]

            out = model.predict_tabular_only(numeric, grade, dir_idx, path_idx, coin_ctx)
            loss = criterion(out["win_prob"], labels)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batch += 1

        history["train_loss"].append(epoch_loss / max(n_batch, 1))

        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for features, labels in val_loader:
                features = features.to(device)
                labels = labels.to(device)
                numeric = features[:, :22]
                grade = features[:, 22].long()
                dir_idx = features[:, 23].long()
                path_idx = features[:, 24].long()
                coin_ctx = features[:, 25:35]
                out = model.predict_tabular_only(numeric, grade, dir_idx, path_idx, coin_ctx)
                val_loss += criterion(out["win_prob"], labels).item()
                preds = (out["win_prob"] > 0.5).float()
                correct += (preds == labels).sum().item()
                total += len(labels)

        history["val_loss"].append(val_loss / max(len(val_loader), 1))
        history["val_acc"].append(correct / max(total, 1))

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{epochs} -- "
                  f"train_loss={history['train_loss'][-1]:.4f} "
                  f"val_acc={history['val_acc'][-1]:.4f}")

    return history
