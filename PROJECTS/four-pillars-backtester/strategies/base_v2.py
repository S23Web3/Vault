"""
Vince v2 Strategy Plugin ABC.

This is the formal Vince v2 interface. It replaces the concept described in
strategies/base.py (which is the rejected v1 XGBoost classifier interface —
kept as archive, do not use for new builds).

Spec: docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md
Concept: docs/VINCE-V2-CONCEPT-v2.md
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class StrategyPlugin(ABC):
    """Abstract base for all Vince-compatible strategy plugins.

    A strategy plugin is the boundary between a specific trading strategy and
    Vince's analysis infrastructure. Vince never reads strategy internals — all
    access goes through this interface.

    Implementing this interface makes any strategy compatible with:
    - Vince Enricher        (compute_signals)
    - Vince Optimizer       (run_backtest, parameter_space)
    - Vince Validator       (run_backtest)
    - Vince Analyzer        (trade_schema)
    - Vince LLM Layer       (strategy_document)
    """

    @abstractmethod
    def compute_signals(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Attach all indicator signals to OHLCV data and return enriched DataFrame.

        Called by the Enricher for every symbol in the active coin set.
        All original columns must be preserved unchanged. Indicator columns are
        appended to the right. See VINCE-PLUGIN-INTERFACE-SPEC-v1.md Section 3a
        for column naming conventions and NaN policy.

        Args:
            ohlcv_df: OHLCV DataFrame with RangeIndex and columns
                      [open, high, low, close, volume] as float64.
                      Minimum rows = longest indicator lookback + 1.

        Returns:
            DataFrame with all original columns plus indicator columns.

        Raises:
            ValueError: if ohlcv_df is missing required OHLCV columns.
            ValueError: if ohlcv_df has fewer rows than the longest lookback.
        """
        raise NotImplementedError

    @abstractmethod
    def parameter_space(self) -> dict:
        """Return sweepable parameter names with bounds and types.

        Used by the Vince Optimizer (Mode 3) to define the Optuna search space.
        Keys are parameter names. Values are dicts with 'type' and optional bounds.

        Schema per entry:
            {"type": "float" | "int" | "bool",
             "low": number,   # required for float/int, low < high
             "high": number,  # required for float/int
             "log": bool}     # optional, default False (log-uniform sampling)

        Returns:
            dict mapping parameter name to parameter spec.
            Return empty dict (not None) if no parameters are sweepable.

        Example:
            {
                "tp_mult":     {"type": "float", "low": 0.5, "high": 5.0},
                "sl_mult":     {"type": "float", "low": 0.5, "high": 3.0},
                "cross_level": {"type": "int",   "low": 20,  "high": 80},
                "allow_b":     {"type": "bool"},
            }
        """
        raise NotImplementedError

    @abstractmethod
    def trade_schema(self) -> dict:
        """Return column definitions for the trade CSV this plugin produces.

        Used by the Enricher to validate trade CSV structure before enrichment.
        Defines backtester output columns only. Indicator snapshot columns
        (k1_at_entry, etc.) are NOT part of this schema — they are added by the
        Enricher via compute_signals().

        Required columns (every plugin must declare all six):
            "entry_bar":  "int   — positional bar index of entry (RangeIndex)"
            "exit_bar":   "int   — positional bar index of exit (RangeIndex)"
            "pnl":        "float — gross PnL in USD before commission"
            "commission": "float — total round-trip commission in USD"
            "direction":  "str   — LONG or SHORT (exact strings)"
            "symbol":     "str   — ticker symbol matching parquet file key"

        Returns:
            dict mapping column name (str) to description string.
        """
        raise NotImplementedError

    @abstractmethod
    def run_backtest(
        self,
        params: dict,
        start: str,
        end: str,
        symbols: list,
    ) -> Path:
        """Run backtest with given params and return path to the trade CSV.

        Called by the Vince Optimizer (Mode 3) for each Optuna trial. Must be
        deterministic — same inputs always produce the same trade CSV. Must be
        thread-safe (Optuna may run trials in parallel).

        Args:
            params:  dict of parameter values matching keys from parameter_space().
                     All keys will be present. No extra keys.
            start:   ISO 8601 date string "YYYY-MM-DD". Inclusive.
            end:     ISO 8601 date string "YYYY-MM-DD". Inclusive.
            symbols: list of ticker strings (e.g. ["BTCUSDT", "ETHUSDT"]).
                     Subset of coins with parquet data available locally.

        Returns:
            pathlib.Path to the trade CSV. File must exist and be readable.
            CSV must contain all columns declared in trade_schema().

        Raises:
            FileNotFoundError: if parquet data for any symbol is missing.
            ValueError: if start >= end or date format is invalid.
            RuntimeError: for any other internal backtest failure.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def strategy_document(self) -> Path:
        """Return path to the strategy markdown document.

        Used by the Vince LLM Interpretive Layer (Panel 8) to ground hypothesis
        generation in strategy-specific logic. The LLM reads this document
        alongside quantitative results.

        Returns:
            pathlib.Path to a .md file. File must exist and be readable.
            Format must be markdown. PDF/DOCX not accepted.

        Raises:
            FileNotFoundError: if the document file does not exist.
        """
        raise NotImplementedError
