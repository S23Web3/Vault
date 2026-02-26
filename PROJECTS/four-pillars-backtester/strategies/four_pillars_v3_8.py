"""
Four Pillars v3.8 strategy implementation.
Inherits from BaseStrategy, uses the existing signal pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from strategies.base_strategy import BaseStrategy
from signals.four_pillars import compute_signals
from strategies.cloud_filter import apply_cloud3_filter


class FourPillarsV38(BaseStrategy):
    """
    Four Pillars v3.8 strategy.

    Config:
        atr_period: ATR lookback (8, 13, 14, or 21). Default 14.
        sl_atr_mult: SL distance in ATR units. Default 1.0.
        tp_atr_mult: TP distance in ATR units. Default 1.5.
        allow_b_fresh: Whether B signals can open fresh positions. Default True.
        cooldown_bars: Min bars between entries. Default 3.
        commission_rate: Per-side commission rate. Default 0.0008.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.atr_period = self.config.get("atr_period", 14)
        self.sl_atr_mult = self.config.get("sl_atr_mult", 1.0)
        self.tp_atr_mult = self.config.get("tp_atr_mult", 1.5)
        self.allow_b_fresh = self.config.get("allow_b_fresh", True)
        self.cooldown_bars = self.config.get("cooldown_bars", 3)
        self.commission_rate = self.config.get("commission_rate", 0.0008)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators (stochs, clouds, ATR)."""
        params = {
            "atr_length": self.atr_period,
            "allow_b_trades": True,
            "allow_c_trades": True,
            "b_open_fresh": self.allow_b_fresh,
        }
        df = compute_signals(df, params)
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals with Cloud 3 filter applied."""
        if "long_a" not in df.columns:
            df = self.calculate_indicators(df)
        df = apply_cloud3_filter(df)
        return df

    def get_sl_tp(self, entry_price: float, atr_value: float) -> tuple[float, float]:
        """Return (stop_loss, take_profit) for a LONG position."""
        sl = entry_price - self.sl_atr_mult * atr_value
        tp = entry_price + self.tp_atr_mult * atr_value
        return sl, tp

    def get_name(self) -> str:
        return "FourPillarsV38"


if __name__ == "__main__":
    import numpy as np
    strategy = FourPillarsV38()
    assert strategy.get_name() == "FourPillarsV38"
    sl, tp = strategy.get_sl_tp(100.0, 2.0)
    assert sl == 98.0 and tp == 103.0, f"SL/TP mismatch: {sl}, {tp}"
    assert isinstance(strategy, BaseStrategy)
    print("PASS -- FourPillarsV38 instantiates, SL/TP correct, inherits BaseStrategy")
