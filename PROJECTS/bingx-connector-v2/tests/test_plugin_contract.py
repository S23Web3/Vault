"""
Tests for mock_strategy.py — interface compliance.
Run: python -m pytest tests/test_plugin_contract.py -v
"""
import sys
import unittest
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugins.mock_strategy import MockStrategy, Signal


class TestPluginContract(unittest.TestCase):
    """Test MockStrategy interface compliance."""

    def setUp(self):
        """Set up mock strategy."""
        self.strategy = MockStrategy(
            {"signal_probability": 0.05})

    def _make_ohlcv(self, n=100, price=0.01, seed=42):
        """Generate synthetic OHLCV for testing."""
        rng = np.random.default_rng(seed)
        close = price + np.cumsum(rng.normal(0, price * 0.01, n))
        close = np.clip(close, price * 0.5, price * 2)
        return pd.DataFrame({
            "open": close * rng.uniform(0.999, 1.001, n),
            "high": close * rng.uniform(1.000, 1.005, n),
            "low": close * rng.uniform(0.995, 1.000, n),
            "close": close,
            "volume": rng.integers(1e6, 1e7, n).astype(float),
            "time": range(1700000000000,
                          1700000000000 + n * 60000, 60000),
        })

    def test_has_required_methods(self):
        """MockStrategy has all 5 required methods."""
        for m in ["get_signal", "get_name", "get_version",
                   "warmup_bars", "get_allowed_grades"]:
            self.assertTrue(hasattr(self.strategy, m),
                            msg="Missing: " + m)
            self.assertTrue(callable(getattr(self.strategy, m)),
                            msg="Not callable: " + m)

    def test_get_signal_returns_signal_or_none(self):
        """get_signal returns Signal or None."""
        df = self._make_ohlcv()
        for _ in range(100):
            r = self.strategy.get_signal(df)
            self.assertTrue(
                r is None or isinstance(r, Signal),
                msg="Expected Signal/None: " + str(type(r)))

    def test_inject_signal(self):
        """inject_signal forces next output."""
        df = self._make_ohlcv()
        forced = Signal(
            direction="LONG", grade="MOCK",
            entry_price=100.0, sl_price=98.0,
            tp_price=103.0, atr=1.0, bar_ts=1700000000000)
        self.strategy.inject_signal(forced)
        result = self.strategy.get_signal(df)
        self.assertIs(result, forced, msg="Should be injected")

    def test_inject_clears_after_use(self):
        """Injected signal consumed after one call."""
        df = self._make_ohlcv()
        forced = Signal(
            direction="SHORT", grade="MOCK",
            entry_price=50.0, sl_price=52.0,
            tp_price=47.0, atr=0.5, bar_ts=0)
        self.strategy.inject_signal(forced)
        self.strategy.get_signal(df)
        results = [self.strategy.get_signal(df) for _ in range(20)]
        nones = sum(1 for r in results if r is None)
        self.assertGreater(nones, 0,
                           msg="Should be consumed after 1 use")

    def test_signal_fields(self):
        """Signal has all 7 fields with correct types."""
        sig = Signal(
            direction="LONG", grade="A",
            entry_price=100.0, sl_price=98.0,
            tp_price=103.0, atr=1.0, bar_ts=170000)
        self.assertIsInstance(sig.direction, str)
        self.assertIsInstance(sig.grade, str)
        self.assertIsInstance(sig.entry_price, float)
        self.assertIsInstance(sig.sl_price, float)
        self.assertIsInstance(sig.tp_price, float)
        self.assertIsInstance(sig.atr, float)
        self.assertIsInstance(sig.bar_ts, int)

    def test_signal_tp_none(self):
        """Signal tp_price can be None (runner mode)."""
        sig = Signal(
            direction="LONG", grade="A",
            entry_price=100.0, sl_price=98.0,
            tp_price=None, atr=1.0, bar_ts=0)
        self.assertIsNone(sig.tp_price)

    def test_allowed_grades_nonempty(self):
        """get_allowed_grades returns non-empty list of strings."""
        grades = self.strategy.get_allowed_grades()
        self.assertIsInstance(grades, list)
        self.assertGreater(len(grades), 0, msg="Empty grades")
        for g in grades:
            self.assertIsInstance(g, str)

    def test_warmup_bars_int(self):
        """warmup_bars returns int, MockStrategy returns 0."""
        wb = self.strategy.warmup_bars()
        self.assertIsInstance(wb, int)
        self.assertEqual(wb, 0)

    def test_name_and_version(self):
        """get_name and get_version return non-empty strings."""
        self.assertGreater(
            len(self.strategy.get_name()), 0)
        self.assertGreater(
            len(self.strategy.get_version()), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
