"""
Abstract base class for all strategy plugins.
Every strategy must implement these methods to integrate with
the Vince ML training pipeline.
"""

from abc import ABC, abstractmethod
import pandas as pd


class StrategyPlugin(ABC):
    """Base class for all strategy plugins."""

    name: str = "base"

    @abstractmethod
    def enrich_ohlcv(self, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
        """Compute indicator columns (ATR, stochastics, clouds, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def compute_signals(self, df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
        """Add signal columns (entries, reentries, adds)."""
        raise NotImplementedError

    @abstractmethod
    def get_backtester_params(self, overrides: dict = None) -> dict:
        """Return backtester config (sl_mult, tp_mult, commission, etc.)."""
        raise NotImplementedError

    @abstractmethod
    def extract_features(self, trades_df: pd.DataFrame,
                         ohlcv_df: pd.DataFrame) -> pd.DataFrame:
        """Extract per-trade features for ML training."""
        raise NotImplementedError

    @abstractmethod
    def get_feature_names(self) -> list:
        """Return ordered list of feature column names."""
        raise NotImplementedError

    @abstractmethod
    def label_trades(self, trades_df: pd.DataFrame,
                     mode: str = "exit") -> pd.Series:
        """Generate binary labels. Modes: exit (TP=1/SL=0) or pnl (win/loss)."""
        raise NotImplementedError
