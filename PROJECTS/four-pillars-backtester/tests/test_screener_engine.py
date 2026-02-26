"""
Integration tests for utils/screener_engine.py.
Uses real RIVER + KITE parquet data from data/cache/.
Run: python tests/test_screener_engine.py
From: C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester
"""
import sys
import math
import unittest
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from utils.screener_engine import (
    screen_coin,
    run_screener,
    to_bingx_symbol,
    DEFAULT_SIGNAL_PARAMS,
    DEFAULT_BT_PARAMS,
    DEFAULT_THRESHOLDS,
)

CACHE_DIR = ROOT / "data" / "cache"
LOOKBACK = 30

EXPECTED_KEYS = {
    "symbol", "atr_ratio", "net_pnl_30d", "avg_daily_vol_usd",
    "trade_count", "pass_atr", "pass_pnl", "pass_vol", "pass_trades",
    "score", "eligible", "error",
}


class TestToBingxSymbol(unittest.TestCase):
    """Symbol format conversion."""

    def test_river_conversion(self):
        """RIVERUSDT converts to RIVER-USDT."""
        self.assertEqual(
            to_bingx_symbol("RIVERUSDT"), "RIVER-USDT",
            msg="RIVERUSDT should become RIVER-USDT",
        )

    def test_kite_conversion(self):
        """KITEUSDT converts to KITE-USDT."""
        self.assertEqual(
            to_bingx_symbol("KITEUSDT"), "KITE-USDT",
            msg="KITEUSDT should become KITE-USDT",
        )

    def test_non_usdt_passthrough(self):
        """Non-USDT symbol passes through unchanged."""
        self.assertEqual(
            to_bingx_symbol("BTCUSD"), "BTCUSD",
            msg="Non-USDT symbol should pass through unchanged",
        )

    def test_btc_conversion(self):
        """BTCUSDT converts to BTC-USDT."""
        self.assertEqual(
            to_bingx_symbol("BTCUSDT"), "BTC-USDT",
            msg="BTCUSDT should become BTC-USDT",
        )


class TestScreenCoinRiver(unittest.TestCase):
    """screen_coin on RIVERUSDT -- real data integration test."""

    @classmethod
    def setUpClass(cls):
        """Run screen_coin once; all tests in class share the result."""
        parquet = CACHE_DIR / "RIVERUSDT_1m.parquet"
        if not parquet.exists():
            raise unittest.SkipTest("RIVERUSDT_1m.parquet not found -- skipping")
        cls.result = screen_coin(
            "RIVERUSDT", CACHE_DIR, LOOKBACK,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, DEFAULT_THRESHOLDS,
        )

    def test_returns_all_expected_keys(self):
        """Result dict must contain all expected keys."""
        missing = EXPECTED_KEYS - set(self.result.keys())
        self.assertEqual(missing, set(), msg="Missing keys: " + str(missing))

    def test_no_exception(self):
        """error field should be None when screening succeeds."""
        self.assertIsNone(
            self.result["error"],
            msg="Unexpected error: " + str(self.result.get("error")),
        )

    def test_atr_ratio_is_finite_positive(self):
        """atr_ratio must be a finite float > 0 for low-price coin RIVER."""
        v = self.result["atr_ratio"]
        self.assertFalse(math.isnan(v), msg="atr_ratio is NaN")
        self.assertFalse(math.isinf(v), msg="atr_ratio is inf")
        self.assertGreater(v, 0.0, msg="atr_ratio should be > 0 for RIVER")

    def test_volume_is_finite(self):
        """avg_daily_vol_usd must be a finite float."""
        v = self.result["avg_daily_vol_usd"]
        self.assertFalse(math.isnan(v), msg="avg_daily_vol_usd is NaN")
        self.assertFalse(math.isinf(v), msg="avg_daily_vol_usd is inf")
        self.assertGreater(v, 0.0, msg="avg_daily_vol_usd should be > 0")

    def test_net_pnl_is_finite(self):
        """net_pnl_30d must be a finite float."""
        v = self.result["net_pnl_30d"]
        self.assertFalse(math.isnan(v), msg="net_pnl_30d is NaN")
        self.assertFalse(math.isinf(v), msg="net_pnl_30d is inf")

    def test_trade_count_is_nonneg_int(self):
        """trade_count must be a non-negative int."""
        tc = self.result["trade_count"]
        self.assertIsInstance(tc, int, msg="trade_count should be int, got " + type(tc).__name__)
        self.assertGreaterEqual(tc, 0, msg="trade_count should be >= 0")

    def test_eligible_is_bool(self):
        """eligible field must be a Python bool."""
        self.assertIsInstance(
            self.result["eligible"], bool,
            msg="eligible should be bool, got " + type(self.result["eligible"]).__name__,
        )

    def test_score_range(self):
        """score must be a float in [0.0, 5.0]."""
        s = self.result["score"]
        self.assertIsInstance(s, float, msg="score should be float")
        self.assertGreaterEqual(s, 0.0, msg="score should be >= 0")
        self.assertLessEqual(s, 5.0, msg="score should be <= 5")

    def test_pass_fields_are_bool(self):
        """All pass_* fields must be Python bools."""
        for field in ("pass_atr", "pass_pnl", "pass_vol", "pass_trades"):
            self.assertIsInstance(
                self.result[field], bool,
                msg=field + " should be bool, got " + type(self.result[field]).__name__,
            )

    def test_eligible_consistent_with_pass_fields(self):
        """eligible must equal AND of all four pass fields."""
        expected = all([
            self.result["pass_atr"],
            self.result["pass_pnl"],
            self.result["pass_vol"],
            self.result["pass_trades"],
        ])
        self.assertEqual(
            self.result["eligible"], expected,
            msg="eligible inconsistent with pass fields",
        )


class TestScreenCoinMissing(unittest.TestCase):
    """Graceful handling of a symbol with no parquet."""

    def test_missing_symbol_no_crash(self):
        """Missing parquet returns row with eligible=False and no exception raised."""
        result = screen_coin(
            "FAKECOIN999USDT", CACHE_DIR, LOOKBACK,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, DEFAULT_THRESHOLDS,
        )
        self.assertFalse(result["eligible"], msg="Missing coin should not be eligible")
        self.assertIsNotNone(result["error"], msg="Missing coin should set error field")

    def test_missing_returns_all_expected_keys(self):
        """Missing parquet result still contains all expected keys."""
        result = screen_coin(
            "FAKECOIN999USDT", CACHE_DIR, LOOKBACK,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, DEFAULT_THRESHOLDS,
        )
        missing = EXPECTED_KEYS - set(result.keys())
        self.assertEqual(missing, set(), msg="Missing keys in error result: " + str(missing))


class TestRunScreenerTwoCoins(unittest.TestCase):
    """run_screener on RIVER + KITE."""

    @classmethod
    def setUpClass(cls):
        """Run screener on two real coins; skip if either parquet missing."""
        if not (CACHE_DIR / "RIVERUSDT_1m.parquet").exists():
            raise unittest.SkipTest("RIVERUSDT_1m.parquet not found -- skipping")
        if not (CACHE_DIR / "KITEUSDT_1m.parquet").exists():
            raise unittest.SkipTest("KITEUSDT_1m.parquet not found -- skipping")
        cls.df = run_screener(
            ["RIVERUSDT", "KITEUSDT"], CACHE_DIR, LOOKBACK,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, DEFAULT_THRESHOLDS,
        )

    def test_returns_two_rows(self):
        """run_screener on 2 symbols returns exactly 2 rows."""
        self.assertEqual(len(self.df), 2, msg="Expected 2 rows, got " + str(len(self.df)))

    def test_sorted_by_score_descending(self):
        """DataFrame must be sorted by score descending."""
        scores = self.df["score"].tolist()
        self.assertEqual(
            scores, sorted(scores, reverse=True),
            msg="Results should be sorted by score descending: " + str(scores),
        )

    def test_has_eligible_column(self):
        """DataFrame must contain eligible column."""
        self.assertIn("eligible", self.df.columns, msg="DataFrame missing 'eligible' column")

    def test_all_symbols_present(self):
        """Both symbols must appear in the results."""
        syms = self.df["symbol"].tolist()
        self.assertIn("RIVERUSDT", syms, msg="RIVERUSDT missing from results")
        self.assertIn("KITEUSDT", syms, msg="KITEUSDT missing from results")


class TestRunScreenerMixedInput(unittest.TestCase):
    """run_screener with one valid and one invalid symbol."""

    def test_invalid_symbol_no_crash(self):
        """Invalid symbol in list does not crash run_screener."""
        if not (CACHE_DIR / "RIVERUSDT_1m.parquet").exists():
            self.skipTest("RIVERUSDT_1m.parquet not found")
        df = run_screener(
            ["RIVERUSDT", "FAKECOIN999USDT"], CACHE_DIR, LOOKBACK,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, DEFAULT_THRESHOLDS,
        )
        self.assertEqual(len(df), 2, msg="Expected 2 rows (1 valid, 1 error)")

    def test_invalid_symbol_not_eligible(self):
        """Invalid symbol row must have eligible=False."""
        if not (CACHE_DIR / "RIVERUSDT_1m.parquet").exists():
            self.skipTest("RIVERUSDT_1m.parquet not found")
        df = run_screener(
            ["RIVERUSDT", "FAKECOIN999USDT"], CACHE_DIR, LOOKBACK,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, DEFAULT_THRESHOLDS,
        )
        fake_rows = df[df["symbol"] == "FAKECOIN999USDT"]
        self.assertEqual(len(fake_rows), 1, msg="FAKECOIN row should be present")
        self.assertFalse(
            fake_rows.iloc[0]["eligible"],
            msg="FAKECOIN999USDT should not be eligible",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
