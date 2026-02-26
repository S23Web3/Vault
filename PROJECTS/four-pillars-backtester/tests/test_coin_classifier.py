
"""Tests for research/coin_classifier.py
Run: python tests/test_coin_classifier.py
"""

import sys
import unittest
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from research.coin_classifier import compute_coin_features, classify_coin_tiers


def make_ohlcv(n=300, price=0.01, vol_mult=0.01, seed=42):
    """Generate synthetic OHLCV DataFrame with specified volatility."""
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, price * vol_mult, n))
    close = np.clip(close, price * 0.1, price * 10)
    df = pd.DataFrame({
        "open":   close * rng.uniform(0.999, 1.001, n),
        "high":   close * rng.uniform(1.000, 1.005, n),
        "low":    close * rng.uniform(0.995, 1.000, n),
        "close":  close,
        "volume": rng.integers(1_000_000, 10_000_000, n).astype(float),
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="1min")
    df.index.name = "datetime"
    return df


def write_parquet_set(tmpdir, n_coins=8):
    """Write n_coins synthetic parquet files with varying volatility."""
    vol_mults = [0.002, 0.004, 0.006, 0.008, 0.010, 0.012, 0.015, 0.020]
    for i in range(n_coins):
        vm = vol_mults[i % len(vol_mults)]
        df = make_ohlcv(n=300, price=0.01, vol_mult=vm, seed=i)
        df.to_parquet(Path(tmpdir) / ("COIN" + str(i) + "_1m.parquet"))


class TestComputeCoinFeatures(unittest.TestCase):

    def setUp(self):
        """Build synthetic OHLCV for tests."""
        self.df = make_ohlcv(n=300, price=0.01, seed=42)

    def test_returns_dict(self):
        """compute_coin_features returns a dict."""
        result = compute_coin_features(self.df, "TEST")
        self.assertIsInstance(result, dict, msg="result should be dict, got " + type(result).__name__)

    def test_keys_present(self):
        """Result dict has all expected keys."""
        result = compute_coin_features(self.df, "TEST")
        for k in ["symbol", "avg_atr_pct", "avg_bbw_raw",
                  "avg_daily_range", "avg_base_vol", "vol_of_vol"]:
            self.assertIn(k, result, msg="Missing key: " + k)

    def test_values_finite(self):
        """All numeric values are finite."""
        result = compute_coin_features(self.df, "TEST")
        for k, v in result.items():
            if k == "symbol":
                continue
            self.assertTrue(np.isfinite(v), msg=k + " is not finite: " + str(v))

    def test_atr_pct_positive(self):
        """avg_atr_pct is positive."""
        result = compute_coin_features(self.df, "TEST")
        self.assertGreater(result["avg_atr_pct"], 0,
                           msg="avg_atr_pct should be > 0, got " + str(result["avg_atr_pct"]))

    def test_symbol_preserved(self):
        """Symbol name is unchanged in output."""
        result = compute_coin_features(self.df, "MYCOIN")
        self.assertEqual(result["symbol"], "MYCOIN",
                         msg="symbol mismatch: " + str(result["symbol"]))

    def test_atr_pct_reasonable_range(self):
        """avg_atr_pct is in 0-100% for realistic data."""
        result = compute_coin_features(self.df, "TEST")
        self.assertGreater(result["avg_atr_pct"], 0.0, msg="atr_pct should be > 0")
        self.assertLess(result["avg_atr_pct"], 100.0, msg="atr_pct should be < 100")


class TestClassifyCoinTiers(unittest.TestCase):

    def setUp(self):
        """Create temp dir with synthetic parquet files."""
        import tempfile
        self.tmpobj = tempfile.TemporaryDirectory()
        self.tmpdir = self.tmpobj.name
        write_parquet_set(self.tmpdir, n_coins=8)

    def tearDown(self):
        """Clean up temp dir."""
        self.tmpobj.cleanup()

    def test_returns_dataframe(self):
        """classify_coin_tiers returns a DataFrame."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        self.assertIsInstance(result, pd.DataFrame,
                              msg="should return DataFrame, got " + type(result).__name__)

    def test_output_columns(self):
        """Output has required columns."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        for col in ["symbol", "tier", "avg_atr_pct"]:
            self.assertIn(col, result.columns, msg="Missing column: " + col)

    def test_tier_range(self):
        """Tiers are non-negative integers covering at least 2 values."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        self.assertGreaterEqual(result["tier"].min(), 0,
                                msg="min tier should be >= 0")
        self.assertGreaterEqual(result["tier"].nunique(), 2,
                                msg="should have at least 2 tiers")

    def test_no_duplicate_symbols(self):
        """No duplicate symbols in output."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        self.assertEqual(len(result), result["symbol"].nunique(),
                         msg="duplicate symbols found: " + str(len(result)) + " rows vs " + str(result["symbol"].nunique()) + " unique")

    def test_sorted_by_volatility(self):
        """Tier 0 has lower avg_atr_pct than max tier."""
        result = classify_coin_tiers(self.tmpdir, timeframe="1m")
        tier0_atr = result[result["tier"] == 0]["avg_atr_pct"].mean()
        max_tier = result["tier"].max()
        tierN_atr = result[result["tier"] == max_tier]["avg_atr_pct"].mean()
        self.assertLessEqual(tier0_atr, tierN_atr,
                             msg="tier 0 should be calmest: " + str(tier0_atr) + " vs " + str(tierN_atr))

    def test_empty_dir_raises(self):
        """Empty parquet dir raises ValueError."""
        import tempfile
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(ValueError, msg="empty dir should raise ValueError"):
                classify_coin_tiers(empty_dir, timeframe="1m")

    def test_too_few_coins_raises(self):
        """Fewer than 4 coins raises ValueError."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(2):
                df = make_ohlcv(n=300, price=0.01, seed=i)
                df.to_parquet(Path(tmpdir) / ("COIN" + str(i) + "_1m.parquet"))
            with self.assertRaises(ValueError, msg="<4 coins should raise ValueError"):
                classify_coin_tiers(tmpdir, timeframe="1m")

    def test_output_path_writes_csv(self):
        """output_path writes CSV to disk."""
        import tempfile
        with tempfile.TemporaryDirectory() as outdir:
            out_csv = Path(outdir) / "tiers.csv"
            classify_coin_tiers(self.tmpdir, timeframe="1m",
                                output_path=str(out_csv))
            self.assertTrue(out_csv.exists(), msg="CSV file should exist at output_path")
            df = pd.read_csv(out_csv)
            self.assertGreater(len(df), 0, msg="CSV should not be empty")

    def test_skip_corrupt_parquet(self):
        """Corrupt parquet file is skipped; valid coins still processed."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            write_parquet_set(tmpdir, n_coins=8)
            (Path(tmpdir) / "CORRUPT_1m.parquet").write_text("not a parquet")
            result = classify_coin_tiers(tmpdir, timeframe="1m")
            self.assertIsInstance(result, pd.DataFrame)
            self.assertNotIn("CORRUPT", result["symbol"].values,
                             msg="Corrupt file should be skipped")


class TestCoinFeatureMath(unittest.TestCase):

    def test_higher_volatility_higher_atr_pct(self):
        """Coin with higher vol_mult has higher avg_atr_pct."""
        df_calm = make_ohlcv(n=300, price=0.01, vol_mult=0.002, seed=0)
        df_wild = make_ohlcv(n=300, price=0.01, vol_mult=0.020, seed=0)
        feat_calm = compute_coin_features(df_calm, "CALM")
        feat_wild = compute_coin_features(df_wild, "WILD")
        self.assertGreater(
            feat_wild["avg_atr_pct"], feat_calm["avg_atr_pct"],
            msg="wild coin should have higher atr_pct: "
            + str(feat_wild["avg_atr_pct"]) + " vs " + str(feat_calm["avg_atr_pct"]),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
