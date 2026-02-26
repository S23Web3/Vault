"""
Mock strategy plugin for testing. Random signals with inject override.
"""
import random
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Strategy signal output."""
    direction: str
    grade: str
    entry_price: float
    sl_price: float
    tp_price: Optional[float]
    atr: float
    bar_ts: int


class MockStrategy:
    """Mock strategy that fires random signals at ~5% probability."""

    def __init__(self, config=None):
        """Initialize with optional config dict."""
        self.config = config or {}
        self.signal_probability = self.config.get(
            "signal_probability", 0.05)
        self._injected_signal = None
        logger.info("MockStrategy: prob=%.2f", self.signal_probability)

    def get_signal(self, ohlcv_df):
        """Return a Signal or None based on random probability."""
        if self._injected_signal is not None:
            sig = self._injected_signal
            self._injected_signal = None
            logger.info("MockStrategy: injected %s", sig.direction)
            return sig
        if random.random() > self.signal_probability:
            return None
        last = ohlcv_df.iloc[-1]
        close = float(last["close"])
        atr = close * 0.01
        direction = random.choice(["LONG", "SHORT"])
        if direction == "LONG":
            sl_price = close - (atr * 2.0)
            tp_price = close + (atr * 3.0)
        else:
            sl_price = close + (atr * 2.0)
            tp_price = close - (atr * 3.0)
        if "time" in ohlcv_df.columns:
            bar_ts = int(last["time"])
        else:
            bar_ts = 0
        signal = Signal(
            direction=direction,
            grade="MOCK",
            entry_price=close,
            sl_price=sl_price,
            tp_price=tp_price,
            atr=atr,
            bar_ts=bar_ts,
        )
        logger.info("MockStrategy: %s at %.6f", direction, close)
        return signal

    def inject_signal(self, signal):
        """Force the next get_signal() to return this signal."""
        self._injected_signal = signal

    def get_name(self):
        """Return strategy name."""
        return "MockStrategy"

    def get_version(self):
        """Return strategy version."""
        return "1.0.0"

    def warmup_bars(self):
        """Return warmup bars needed. Mock needs 0."""
        return 0

    def get_allowed_grades(self):
        """Return list of grades this strategy produces."""
        return ["MOCK"]
