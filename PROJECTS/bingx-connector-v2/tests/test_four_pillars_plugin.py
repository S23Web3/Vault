"""
Tests for plugins/four_pillars_v384.py.
Run: python scripts/run_tests.py
"""
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugins.four_pillars_v384 import FourPillarsV384
from plugins.mock_strategy import Signal

_CFG = {
    "four_pillars": {
        "allow_a": True,
        "allow_b": True,
        "allow_c": False,
        "sl_atr_mult": 2.0,
        "tp_atr_mult": None,
        "atr_length": 14,
        "cross_level": 25,
        "zone_level": 30,
    }
}


def _make_ohlcv(n=250, price=0.005, seed=42):
    """Generate synthetic OHLCV DataFrame matching MarketDataFeed columns."""
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, price * 0.01, n))
    close = np.clip(close, price * 0.5, price * 2.0)
    high = np.maximum(close * rng.uniform(1.000, 1.005, n), close)
    low = np.minimum(close * rng.uniform(0.995, 1.000, n), close)
    return pd.DataFrame({
        "time":   np.arange(n, dtype=np.int64) * 300_000,
        "open":   close * rng.uniform(0.999, 1.001, n),
        "high":   high,
        "low":    low,
        "close":  close,
        "volume": rng.uniform(1e6, 1e7, n),
    })


class TestFourPillarsPlugin(unittest.TestCase):
    """Tests for FourPillarsV384 plugin contract."""

    def setUp(self):
        """Create plugin and a 250-bar synthetic DataFrame."""
        self.plugin = FourPillarsV384(config=_CFG)
        self.df = _make_ohlcv(n=250)

    def test_name_and_version(self):
        """get_name() and get_version() return expected values."""
        self.assertEqual(self.plugin.get_name(), "FourPillarsV384")
        self.assertEqual(self.plugin.get_version(), "3.8.4")

    def test_warmup_bars(self):
        """warmup_bars() returns 200."""
        self.assertEqual(self.plugin.warmup_bars(), 200)

    def test_allowed_grades_allow_ab(self):
        """allow_a=True allow_b=True allow_c=False -> grades=[A,B]."""
        grades = self.plugin.get_allowed_grades()
        self.assertIn("A", grades, msg="A should be in grades")
        self.assertIn("B", grades, msg="B should be in grades")
        self.assertNotIn("C", grades, msg="C should not be in grades")

    def test_no_exception_on_synthetic_data(self):
        """250 synthetic bars should not raise; returns Signal or None."""
        result = self.plugin.get_signal(self.df)
        self.assertIn(
            type(result).__name__, ["Signal", "NoneType"],
            msg="Expected Signal or None, got: " + str(type(result)),
        )

    def test_returns_none_on_none(self):
        """None input returns None."""
        self.assertIsNone(self.plugin.get_signal(None))

    def test_returns_none_on_empty_df(self):
        """Empty DataFrame returns None."""
        self.assertIsNone(self.plugin.get_signal(pd.DataFrame()))

    def test_returns_none_on_single_bar(self):
        """Single-row DataFrame returns None (need at least 2 rows)."""
        self.assertIsNone(self.plugin.get_signal(self.df.iloc[:1]))

    def test_sl_on_correct_side_when_signal_fires(self):
        """If Signal fires: LONG SL < entry, SHORT SL > entry."""
        for seed in range(30):
            df = _make_ohlcv(n=250, seed=seed)
            result = self.plugin.get_signal(df)
            if result is not None:
                if result.direction == "LONG":
                    self.assertLess(
                        result.sl_price, result.entry_price,
                        msg="LONG SL must be below entry",
                    )
                else:
                    self.assertGreater(
                        result.sl_price, result.entry_price,
                        msg="SHORT SL must be above entry",
                    )
                return
        # No signal in 30 seeds is acceptable for synthetic data

    def test_grade_in_allowed_set_when_signal_fires(self):
        """If Signal fires: grade must be in get_allowed_grades()."""
        allowed = set(self.plugin.get_allowed_grades())
        for seed in range(30):
            df = _make_ohlcv(n=250, seed=seed)
            result = self.plugin.get_signal(df)
            if result is not None:
                self.assertIn(
                    result.grade, allowed,
                    msg="Grade " + result.grade + " not in " + str(allowed),
                )
                return

    def test_tp_none_when_tp_mult_not_set(self):
        """tp_price is None when tp_atr_mult is None."""
        for seed in range(30):
            df = _make_ohlcv(n=250, seed=seed)
            result = self.plugin.get_signal(df)
            if result is not None:
                self.assertIsNone(
                    result.tp_price,
                    msg="tp_price should be None when tp_atr_mult not set",
                )
                return

    def test_tp_set_when_tp_mult_given(self):
        """tp_price is set when tp_atr_mult is provided."""
        cfg_with_tp = {
            "four_pillars": dict(
                _CFG["four_pillars"], tp_atr_mult=3.0
            )
        }
        plugin_tp = FourPillarsV384(config=cfg_with_tp)
        for seed in range(30):
            df = _make_ohlcv(n=250, seed=seed)
            result = plugin_tp.get_signal(df)
            if result is not None:
                self.assertIsNotNone(
                    result.tp_price,
                    msg="tp_price should be set when tp_atr_mult=3.0",
                )
                return


if __name__ == "__main__":
    unittest.main(verbosity=2)
