"""
VINCE Unified Model -- PyTorch model with tabular + sequence + context branches.

Architecture:
  Tabular branch:  entry-state (11) + lifecycle (14) -> 64-dim
  Sequence branch: per-bar indicators [bars x 15] -> LSTM -> 64-dim
  Context branch:  coin characteristics (10) -> 32-dim
  Fusion:          [64 + 64 + 32] = 160-dim -> dense -> outputs

Outputs:
  Primary:   win probability (0-1)
  Secondary: P&L path class (4 types)
  Tertiary:  optimal exit bar estimate
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Dict, Tuple


class TabularBranch(nn.Module):
    """Processes entry-state + lifecycle summary features."""

    def __init__(self, n_numeric: int = 22, n_cat_embed: int = 3,
                 embed_dims: int = 8, hidden: int = 128, out_dim: int = 64):
        super().__init__()
        # Categorical embeddings: grade (5 vals), stoch9_direction (3 vals), pnl_path (4 vals)
        self.grade_embed = nn.Embedding(5, embed_dims)
        self.dir_embed = nn.Embedding(3, embed_dims)
        self.path_embed = nn.Embedding(4, embed_dims)

        input_dim = n_numeric + n_cat_embed * embed_dims
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, out_dim),
            nn.ReLU(),
        )

    def forward(self, numeric, grade_idx, dir_idx, path_idx):
        g = self.grade_embed(grade_idx)
        d = self.dir_embed(dir_idx)
        p = self.path_embed(path_idx)
        x = torch.cat([numeric, g, d, p], dim=-1)
        return self.net(x)


class SequenceBranch(nn.Module):
    """Processes per-bar indicator evolution via LSTM."""

    def __init__(self, input_dim: int = 15, hidden: int = 64,
                 n_layers: int = 2, out_dim: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim, hidden, n_layers,
            batch_first=True, dropout=0.2,
        )
        self.fc = nn.Linear(hidden, out_dim)

    def forward(self, seq, lengths=None):
        if lengths is not None:
            packed = nn.utils.rnn.pack_padded_sequence(
                seq, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            _, (h, _) = self.lstm(packed)
        else:
            _, (h, _) = self.lstm(seq)
        return self.fc(h[-1])


class ContextBranch(nn.Module):
    """Processes coin characteristics."""

    def __init__(self, input_dim: int = 10, hidden: int = 32, out_dim: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, out_dim),
            nn.ReLU(),
        )

    def forward(self, x):
        return self.net(x)


class VinceModel(nn.Module):
    """Unified VINCE model combining all three branches."""

    def __init__(self, tabular_numeric: int = 22, seq_features: int = 15,
                 coin_features: int = 10, fusion_dim: int = 160):
        super().__init__()
        self.tabular = TabularBranch(n_numeric=tabular_numeric)
        self.sequence = SequenceBranch(input_dim=seq_features)
        self.context = ContextBranch(input_dim=coin_features)

        self.fusion = nn.Sequential(
            nn.Linear(fusion_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
        )

        # Output heads
        self.win_head = nn.Sequential(nn.Linear(64, 1), nn.Sigmoid())
        self.path_head = nn.Linear(64, 4)  # 4 P&L path classes
        self.exit_head = nn.Sequential(nn.Linear(64, 1), nn.ReLU())

    def forward(self, numeric, grade_idx, dir_idx, path_idx,
                seq, seq_lengths, coin_ctx):
        tab_out = self.tabular(numeric, grade_idx, dir_idx, path_idx)
        seq_out = self.sequence(seq, seq_lengths)
        ctx_out = self.context(coin_ctx)

        fused = torch.cat([tab_out, seq_out, ctx_out], dim=-1)
        h = self.fusion(fused)

        win_prob = self.win_head(h).squeeze(-1)
        path_logits = self.path_head(h)
        exit_bars = self.exit_head(h).squeeze(-1)

        return {"win_prob": win_prob, "path_logits": path_logits, "exit_bars": exit_bars}

    def predict_tabular_only(self, numeric, grade_idx, dir_idx, path_idx,
                             coin_ctx):
        """Phase 1: tabular + context only, no sequence branch."""
        tab_out = self.tabular(numeric, grade_idx, dir_idx, path_idx)
        seq_out = torch.zeros(tab_out.shape[0], 64, device=tab_out.device)
        ctx_out = self.context(coin_ctx)

        fused = torch.cat([tab_out, seq_out, ctx_out], dim=-1)
        h = self.fusion(fused)

        win_prob = self.win_head(h).squeeze(-1)
        path_logits = self.path_head(h)
        exit_bars = self.exit_head(h).squeeze(-1)

        return {"win_prob": win_prob, "path_logits": path_logits, "exit_bars": exit_bars}


# Encoding helpers
GRADE_MAP = {"A": 3, "B": 2, "C": 1, "R": 0, "D": 4, "": 0}
DIR_MAP = {"rising": 0, "falling": 1, "flat": 2}
PATH_MAP = {"direct": 0, "green_then_red": 1, "red_then_green": 2, "choppy": 3}
