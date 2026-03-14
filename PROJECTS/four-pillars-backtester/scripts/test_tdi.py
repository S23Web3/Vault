"""
Comprehensive test suite for signals/tdi.py and TDI core signal layer.

Outputs results to: logs/YYYY-MM-DD-tdi-tests.log
Prints audit summary to console on completion.

Run: python scripts/test_tdi.py
"""

import sys
import logging
import unittest
import time
from datetime import datetime, timezone
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

import numpy as np
import pandas as pd

# ---- Logging setup ----------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_path = LOG_DIR / (datetime.now(timezone.utc).strftime("%Y-%m-%d") + "-tdi-tests.log")

fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler = TimedRotatingFileHandler(str(log_path), when="midnight", backupCount=30, encoding="utf-8")
file_handler.setFormatter(fmt)
console_handler = logging.StreamHandler()
console_handler.setFormatter(fmt)

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
log = logging.getLogger(__name__)

sys.path.insert(0, str(ROOT))

from signals.tdi import (
    compute_tdi, compute_tdi_core, PRESETS, DEFAULT_PARAMS,
    _rsi_wilder, _cross, _classify_zones, _detect_divergences, _detect_pivots,
)

# ---- Expected column lists --------------------------------------------------

TDI_BASE_COLS = [
    "tdi_rsi", "tdi_fast_ma", "tdi_signal",
    "tdi_bb_upper", "tdi_bb_mid", "tdi_bb_lower",
    "tdi_zone", "tdi_color",
    "tdi_cloud_bull",
    "tdi_long", "tdi_short", "tdi_best_setup", "tdi_best_setup_short", "tdi_scalp",
    "tdi_bull_div", "tdi_bear_div", "tdi_hidden_bull_div", "tdi_hidden_bear_div",
    "tdi_rsi_cross_signal_up", "tdi_rsi_cross_signal_down",
    "tdi_rsi_cross_bb_upper", "tdi_rsi_cross_bb_lower",
    "tdi_rsi_cross_50_up", "tdi_rsi_cross_50_down",
]

TDI_CORE_COLS = [
    "tdi_core_long_a", "tdi_core_long_b", "tdi_core_long_c", "tdi_core_long_rev",
    "tdi_core_short_a", "tdi_core_short_b", "tdi_core_short_c", "tdi_core_short_rev",
]

BOOL_COLS = [
    "tdi_cloud_bull", "tdi_long", "tdi_short",
    "tdi_best_setup", "tdi_best_setup_short", "tdi_scalp",
    "tdi_bull_div", "tdi_bear_div", "tdi_hidden_bull_div", "tdi_hidden_bear_div",
    "tdi_rsi_cross_signal_up", "tdi_rsi_cross_signal_down",
    "tdi_rsi_cross_bb_upper", "tdi_rsi_cross_bb_lower",
    "tdi_rsi_cross_50_up", "tdi_rsi_cross_50_down",
]

# ---- Synthetic data helpers -------------------------------------------------

def make_ohlcv(n=300, price=1.0, seed=42):
    """Generate synthetic OHLCV DataFrame for testing."""
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, price * 0.01, n))
    close = np.clip(close, price * 0.3, price * 3.0)
    df = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n, freq="5min"),
        "open": close * rng.uniform(0.999, 1.001, n),
        "high": close * rng.uniform(1.000, 1.005, n),
        "low": close * rng.uniform(0.995, 1.000, n),
        "close": close,
        "base_vol": rng.integers(100000, 1000000, n).astype(float),
        "quote_vol": rng.integers(100000, 1000000, n).astype(float),
    })
    return df


def make_synthetic_bull_div(n=200):
    """Construct price series with a known bullish RSI divergence.

    Price makes lower low. RSI makes higher low (price drops less momentum).
    Uses a sine-wave price with damped second trough.
    """
    t = np.linspace(0, 4 * np.pi, n)
    # First trough deeper, second trough shallower in price
    price = 100.0 + 10.0 * np.sin(t) - 0.02 * t
    # Inject: price second trough is lower but RSI second trough higher
    # achieved by compressing the second half price range while keeping
    # the oscillation shape — RSI (momentum-based) sees less velocity
    price[n // 2:] = price[n // 2:] - 2.0  # price second half: push down
    price = np.clip(price, 50.0, 200.0)
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "timestamp": pd.date_range("2025-01-01", periods=n, freq="5min"),
        "open": price * rng.uniform(0.999, 1.001, n),
        "high": price * rng.uniform(1.000, 1.005, n),
        "low": price * rng.uniform(0.995, 1.000, n),
        "close": price,
        "base_vol": np.ones(n) * 500000.0,
        "quote_vol": np.ones(n) * 500000.0,
    })
    return df


def manual_rsi(close, period=14):
    """Manual RSI calculation for known-value cross-check."""
    n = len(close)
    rsi = [float("nan")] * n
    gains, losses = [], []
    for i in range(1, n):
        d = close[i] - close[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    if len(gains) < period:
        return rsi
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    rsi[period] = 100.0 if avg_l == 0 else 100.0 - 100.0 / (1.0 + avg_g / avg_l)
    for i in range(period, len(gains)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
        rsi[i + 1] = 100.0 if avg_l == 0 else 100.0 - 100.0 / (1.0 + avg_g / avg_l)
    return rsi


# ============================================================================
# Test classes
# ============================================================================

class TestTDIColumns(unittest.TestCase):
    """Verify output column presence and types."""

    def setUp(self):
        """Compute TDI on standard 300-bar data."""
        self.df = make_ohlcv(300)
        self.result = compute_tdi(self.df)

    def test_all_base_columns_present(self):
        """All base TDI columns must exist."""
        for col in TDI_BASE_COLS:
            self.assertIn(col, self.result.columns, msg="missing: " + col)

    def test_exact_tdi_column_count(self):
        """Count of tdi_ columns must equal len(TDI_BASE_COLS)."""
        tdi_cols = [c for c in self.result.columns if c.startswith("tdi_")]
        self.assertEqual(len(tdi_cols), len(TDI_BASE_COLS),
                         msg="got " + str(len(tdi_cols)) + " tdi_ cols, expected " + str(len(TDI_BASE_COLS)))

    def test_bool_columns_dtype(self):
        """Boolean columns must have bool dtype."""
        for col in BOOL_COLS:
            self.assertEqual(self.result[col].dtype, bool, msg=col + " wrong dtype")

    def test_float_columns_dtype(self):
        """Float columns must have float64 dtype."""
        for col in ["tdi_rsi", "tdi_fast_ma", "tdi_signal",
                    "tdi_bb_upper", "tdi_bb_mid", "tdi_bb_lower"]:
            self.assertTrue(np.issubdtype(self.result[col].dtype, np.floating),
                            msg=col + " should be float")

    def test_row_count_preserved(self):
        """Row count must not change."""
        self.assertEqual(len(self.result), len(self.df))

    def test_original_columns_intact(self):
        """Original OHLCV columns must remain."""
        for col in ["open", "high", "low", "close", "base_vol"]:
            self.assertIn(col, self.result.columns, msg="lost: " + col)

    def test_core_columns_present(self):
        """compute_tdi_core must add 8 tdi_core_ columns."""
        result = compute_tdi_core(self.df)
        for col in TDI_CORE_COLS:
            self.assertIn(col, result.columns, msg="core missing: " + col)
        core_cols = [c for c in result.columns if c.startswith("tdi_core_")]
        self.assertEqual(len(core_cols), len(TDI_CORE_COLS),
                         msg="core col count wrong: " + str(len(core_cols)))


class TestTDIWarmup(unittest.TestCase):
    """Verify NaN warmup periods are correct."""

    def _warmup(self, preset, key_period, extra=0):
        """Return warmup end bar index for a given period sum."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": preset})
        return result, PRESETS[preset][key_period] + extra

    def test_rsi_nan_before_period(self):
        """RSI NaN for bars 0..rsi_period-1."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": "cw_trades"})
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        for i in range(rp):
            self.assertTrue(np.isnan(result["tdi_rsi"].iloc[i]),
                            msg="RSI not NaN at bar " + str(i))
        self.assertFalse(np.isnan(result["tdi_rsi"].iloc[rp]),
                         msg="RSI should be valid at bar " + str(rp))

    def test_fast_ma_warmup(self):
        """fast_ma valid after rsi_period + fast_len - 1."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": "cw_trades"})
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        fl = PRESETS["cw_trades"]["tdi_fast_ma_len"]
        warmup = rp + fl - 1
        self.assertTrue(np.isnan(result["tdi_fast_ma"].iloc[warmup - 1]),
                        msg="fast_ma not NaN at warmup-1")
        self.assertFalse(np.isnan(result["tdi_fast_ma"].iloc[warmup]),
                         msg="fast_ma should be valid at warmup")

    def test_signal_warmup(self):
        """signal valid after rsi_period + signal_len - 1."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": "cw_trades"})
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        sl = PRESETS["cw_trades"]["tdi_signal_ma_len"]
        warmup = rp + sl - 1
        self.assertTrue(np.isnan(result["tdi_signal"].iloc[warmup - 1]))
        self.assertFalse(np.isnan(result["tdi_signal"].iloc[warmup]))

    def test_bb_mid_warmup(self):
        """bb_mid valid after rsi_period + bb_period - 1."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": "cw_trades"})
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        bp = PRESETS["cw_trades"]["tdi_bb_period"]
        warmup = rp + bp - 1
        self.assertTrue(np.isnan(result["tdi_bb_mid"].iloc[warmup - 1]))
        self.assertFalse(np.isnan(result["tdi_bb_mid"].iloc[warmup]))

    def test_bool_cols_false_during_warmup(self):
        """Boolean signal columns should be False during warmup."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": "cw_trades"})
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        for col in BOOL_COLS:
            warmup_vals = result[col].iloc[:rp].values
            self.assertTrue(np.all(~warmup_vals),
                            msg=col + " has True during RSI warmup")


class TestRSIKnownValues(unittest.TestCase):
    """Cross-check RSI against independent manual implementation."""

    def test_rsi_matches_manual(self):
        """_rsi_wilder must match manual Wilder RSI to 6 decimal places."""
        df = make_ohlcv(100, seed=99)
        close = df["close"].values
        auto = _rsi_wilder(close, 14)
        manual = manual_rsi(close, 14)
        for i in range(14, 100):
            self.assertAlmostEqual(
                auto[i], manual[i], places=6,
                msg="RSI mismatch at bar " + str(i) + ": auto=" + str(auto[i]) + " manual=" + str(manual[i])
            )

    def test_rsi_constant_up_near_100(self):
        """Constant increasing prices -> RSI near 100."""
        close = np.arange(1.0, 101.0)
        rsi = _rsi_wilder(close, 14)
        self.assertAlmostEqual(rsi[-1], 100.0, places=1)

    def test_rsi_constant_down_near_0(self):
        """Constant decreasing prices -> RSI near 0."""
        close = np.arange(100.0, 0.0, -1.0)
        rsi = _rsi_wilder(close, 14)
        self.assertAlmostEqual(rsi[-1], 0.0, places=1)

    def test_rsi_always_0_to_100(self):
        """RSI must stay in [0, 100] for any input."""
        for seed in [1, 42, 99, 777]:
            df = make_ohlcv(500, seed=seed)
            rsi = _rsi_wilder(df["close"].values, 13)
            valid = rsi[~np.isnan(rsi)]
            self.assertTrue(np.all(valid >= 0.0), msg="RSI < 0 with seed=" + str(seed))
            self.assertTrue(np.all(valid <= 100.0), msg="RSI > 100 with seed=" + str(seed))

    def test_rsi_period_14_classic(self):
        """Classic preset uses RSI 14; verify period is applied."""
        df = make_ohlcv(300)
        result = compute_tdi(df, {"tdi_preset": "classic"})
        # First valid bar should be at index 14
        self.assertTrue(np.isnan(result["tdi_rsi"].iloc[13]))
        self.assertFalse(np.isnan(result["tdi_rsi"].iloc[14]))


class TestPresetsAndParams(unittest.TestCase):
    """Verify preset selection and parameter override."""

    def test_cw_trades_vs_classic_rsi_differ(self):
        """RSI 13 and RSI 14 must produce different values."""
        df = make_ohlcv(300)
        cw = compute_tdi(df, {"tdi_preset": "cw_trades"})
        cl = compute_tdi(df, {"tdi_preset": "classic"})
        rsi_cw = cw["tdi_rsi"].dropna().values
        rsi_cl = cl["tdi_rsi"].dropna().values
        n = min(len(rsi_cw), len(rsi_cl))
        self.assertFalse(np.allclose(rsi_cw[:n], rsi_cl[:n]),
                         msg="RSI 13 and 14 should differ")

    def test_classic_preset_bb_settings(self):
        """Classic preset must use bb_period=20 and bb_std=2.0."""
        df = make_ohlcv(300)
        cw = compute_tdi(df, {"tdi_preset": "cw_trades"})
        cl = compute_tdi(df, {"tdi_preset": "classic"})
        # BB width differs because bb_period and bb_std differ
        cw_width = (cw["tdi_bb_upper"] - cw["tdi_bb_lower"]).dropna().mean()
        cl_width = (cl["tdi_bb_upper"] - cl["tdi_bb_lower"]).dropna().mean()
        self.assertNotAlmostEqual(cw_width, cl_width, places=2,
                                  msg="CW and Classic BB widths should differ")

    def test_param_override_rsi_period(self):
        """Overriding rsi_period=14 on cw_trades preset matches classic RSI."""
        df = make_ohlcv(300)
        custom = compute_tdi(df, {"tdi_preset": "cw_trades", "tdi_rsi_period": 14})
        classic = compute_tdi(df, {"tdi_preset": "classic"})
        rsi_c = custom["tdi_rsi"].dropna().values
        rsi_cl = classic["tdi_rsi"].dropna().values
        n = min(len(rsi_c), len(rsi_cl))
        self.assertTrue(np.allclose(rsi_c[:n], rsi_cl[:n], atol=1e-10),
                        msg="Override rsi_period=14 should match classic")

    def test_unknown_preset_falls_back_to_cw(self):
        """Unknown preset name falls back to cw_trades."""
        df = make_ohlcv(100)
        result = compute_tdi(df, {"tdi_preset": "nonexistent"})
        self.assertFalse(result["tdi_rsi"].dropna().empty)


class TestZoneClassification(unittest.TestCase):
    """Verify zone logic with known delta values."""

    def _call(self, rsi_val, sig_val, bbu=80.0, bbl=20.0):
        """Classify a single bar using default thresholds."""
        p = DEFAULT_PARAMS
        zones, colors = _classify_zones(
            np.array([rsi_val]), np.array([sig_val]),
            np.array([bbu]), np.array([bbl]),
            p["tdi_delta_neutral"], p["tdi_delta_weak"], p["tdi_delta_strong"]
        )
        return zones[0], colors[0]

    def test_neutral_at_threshold_boundary(self):
        """delta exactly at delta_neutral should be NEUTRAL."""
        zone, _ = self._call(52.0, 50.0)  # delta=2.0 == threshold
        self.assertEqual(zone, "NEUTRAL")

    def test_weak_bull_just_above_neutral(self):
        """delta=2.1 (> neutral=2.0) should be WEAK_BULL."""
        zone, _ = self._call(52.1, 50.0)
        self.assertEqual(zone, "WEAK_BULL")

    def test_bull_range(self):
        """delta in (5, 10] should be BULL."""
        for delta in [5.1, 7.0, 9.9]:
            zone, _ = self._call(50.0 + delta, 50.0)
            self.assertEqual(zone, "BULL", msg="delta=" + str(delta) + " should be BULL")

    def test_strong_bull_above_threshold(self):
        """delta > 10 should be STRONG_BULL."""
        zone, color = self._call(65.0, 50.0)  # delta=15
        self.assertEqual(zone, "STRONG_BULL")
        self.assertEqual(color, "#00FF00")

    def test_bear_range(self):
        """delta in (-10, -5] should be BEAR."""
        for delta in [-5.1, -7.0, -9.9]:
            zone, _ = self._call(50.0 + delta, 50.0)
            self.assertEqual(zone, "BEAR", msg="delta=" + str(delta) + " should be BEAR")

    def test_strong_bear(self):
        """delta < -10 should be STRONG_BEAR."""
        zone, color = self._call(35.0, 50.0)  # delta=-15
        self.assertEqual(zone, "STRONG_BEAR")
        self.assertEqual(color, "#FF00FF")

    def test_bb_upper_breach_priority(self):
        """BB upper breach overrides delta even when bullish."""
        zone, color = self._call(82.0, 60.0, bbu=80.0)
        self.assertEqual(zone, "BB_UPPER_BREACH")
        self.assertEqual(color, "#FFFF00")

    def test_bb_lower_breach_priority(self):
        """BB lower breach overrides delta even when bearish."""
        zone, color = self._call(18.0, 35.0, bbl=20.0)
        self.assertEqual(zone, "BB_LOWER_BREACH")
        self.assertEqual(color, "#FF0000")

    def test_nan_rsi_empty(self):
        """NaN RSI produces empty zone string."""
        p = DEFAULT_PARAMS
        zones, _ = _classify_zones(
            np.array([np.nan]), np.array([50.0]),
            np.array([80.0]), np.array([20.0]),
            p["tdi_delta_neutral"], p["tdi_delta_weak"], p["tdi_delta_strong"]
        )
        self.assertEqual(zones[0], "")

    def test_nan_signal_neutral_fallback(self):
        """NaN signal inside BB falls back to NEUTRAL."""
        p = DEFAULT_PARAMS
        zones, colors = _classify_zones(
            np.array([60.0]), np.array([np.nan]),
            np.array([80.0]), np.array([20.0]),
            p["tdi_delta_neutral"], p["tdi_delta_weak"], p["tdi_delta_strong"]
        )
        self.assertEqual(zones[0], "NEUTRAL")
        self.assertEqual(colors[0], "#808080")

    def test_all_zones_reachable(self):
        """All 9 zone strings must be reachable with valid inputs."""
        expected = {
            "NEUTRAL", "WEAK_BULL", "BULL", "STRONG_BULL",
            "WEAK_BEAR", "BEAR", "STRONG_BEAR",
            "BB_UPPER_BREACH", "BB_LOWER_BREACH"
        }
        seen = set()
        test_cases = [
            (50.0, 50.0, 80.0, 20.0),   # NEUTRAL
            (52.5, 50.0, 80.0, 20.0),   # WEAK_BULL
            (57.0, 50.0, 80.0, 20.0),   # BULL
            (65.0, 50.0, 80.0, 20.0),   # STRONG_BULL
            (47.5, 50.0, 80.0, 20.0),   # WEAK_BEAR
            (43.0, 50.0, 80.0, 20.0),   # BEAR
            (35.0, 50.0, 80.0, 20.0),   # STRONG_BEAR
            (82.0, 50.0, 80.0, 20.0),   # BB_UPPER_BREACH
            (18.0, 50.0, 80.0, 20.0),   # BB_LOWER_BREACH
        ]
        for rsi_v, sig_v, bbu, bbl in test_cases:
            z, _ = self._call(rsi_v, sig_v, bbu, bbl)
            seen.add(z)
        self.assertEqual(seen, expected, msg="Unreachable zones: " + str(expected - seen))


class TestCrossDetection(unittest.TestCase):
    """Verify _cross on synthetic sequences."""

    def test_cross_up_exact_bar(self):
        """Cross up fires at bar 2 only."""
        a = np.array([1.0, 2.0, 4.0, 5.0])
        b = np.array([3.0, 3.0, 3.0, 3.0])
        up, down = _cross(a, b)
        self.assertFalse(up[0])
        self.assertFalse(up[1])
        self.assertTrue(up[2])
        self.assertFalse(up[3])
        self.assertFalse(np.any(down))

    def test_cross_down_exact_bar(self):
        """Cross down fires at bar 2 only."""
        a = np.array([5.0, 4.0, 2.0, 1.0])
        b = np.array([3.0, 3.0, 3.0, 3.0])
        _, down = _cross(a, b)
        self.assertTrue(down[2])
        self.assertFalse(down[0])
        self.assertFalse(down[3])

    def test_nan_suppresses_cross(self):
        """NaN at bar n-1 prevents cross at bar n."""
        a = np.array([1.0, np.nan, 4.0, 5.0])
        b = np.array([3.0, 3.0, 3.0, 3.0])
        up, _ = _cross(a, b)
        self.assertFalse(up[2], msg="cross after NaN should not fire")

    def test_touch_then_cross(self):
        """Equal-then-above fires cross_up (Pine ta.crossover uses <= on prev bar)."""
        a = np.array([1.0, 3.0, 4.0])  # equal at 1, above at 2
        b = np.array([3.0, 3.0, 3.0])
        up, _ = _cross(a, b)
        self.assertFalse(up[1], msg="equal is not above, no cross at bar 1")
        self.assertTrue(up[2], msg="bar 2: a>b and prev a<=b, Pine crossover fires")

    def test_no_false_signals_flat(self):
        """Flat series (both equal) should produce no crosses."""
        a = np.array([5.0, 5.0, 5.0, 5.0])
        b = np.array([5.0, 5.0, 5.0, 5.0])
        up, down = _cross(a, b)
        self.assertFalse(np.any(up))
        self.assertFalse(np.any(down))


class TestBuySellSignals(unittest.TestCase):
    """Verify tdi_long/tdi_short conditions are logically correct."""

    def setUp(self):
        """Compute on 500 bars for signal diversity."""
        self.result = compute_tdi(make_ohlcv(500))

    def test_long_signal_conditions(self):
        """Every tdi_long bar must satisfy signal > bb_mid AND signal > 50."""
        longs = self.result[self.result["tdi_long"]]
        if len(longs) == 0:
            self.skipTest("no tdi_long signals on this dataset")
        for _, row in longs.iterrows():
            self.assertGreater(row["tdi_signal"], row["tdi_bb_mid"],
                               msg="tdi_long: signal <= bb_mid")
            self.assertGreater(row["tdi_signal"], 50.0,
                               msg="tdi_long: signal <= 50")

    def test_short_signal_conditions(self):
        """Every tdi_short bar must satisfy signal < bb_mid AND signal < 50."""
        shorts = self.result[self.result["tdi_short"]]
        if len(shorts) == 0:
            self.skipTest("no tdi_short signals on this dataset")
        for _, row in shorts.iterrows():
            self.assertLess(row["tdi_signal"], row["tdi_bb_mid"],
                            msg="tdi_short: signal >= bb_mid")
            self.assertLess(row["tdi_signal"], 50.0,
                            msg="tdi_short: signal >= 50")

    def test_long_short_mutually_exclusive(self):
        """tdi_long and tdi_short never fire on the same bar."""
        both = self.result["tdi_long"] & self.result["tdi_short"]
        self.assertEqual(both.sum(), 0)

    def test_long_requires_cross(self):
        """tdi_long can only fire on a fast-crosses-signal-up bar."""
        result = self.result
        longs = result[result["tdi_long"]]
        if len(longs) == 0:
            self.skipTest("no tdi_long signals")
        # Reconstruct fast_cross_up independently
        from signals.tdi import _cross as tdi_cross
        fast_cross_up, _ = tdi_cross(result["tdi_fast_ma"].values, result["tdi_signal"].values)
        for idx in longs.index:
            pos = result.index.get_loc(idx)
            self.assertTrue(fast_cross_up[pos],
                            msg="tdi_long at bar " + str(pos) + " has no fast_cross_up")

    def test_no_signals_in_warmup(self):
        """No tdi_long or tdi_short during warmup."""
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        for col in ["tdi_long", "tdi_short"]:
            warmup_vals = self.result[col].iloc[:rp].values
            self.assertFalse(np.any(warmup_vals),
                             msg=col + " fires in warmup")


class TestCloudAndScalp(unittest.TestCase):
    """Verify cloud and scalp column correctness."""

    def test_cloud_bull_vectorized(self):
        """tdi_cloud_bull is True iff fast_ma > signal (ignoring NaN)."""
        result = compute_tdi(make_ohlcv(300))
        fast = result["tdi_fast_ma"].values
        sig = result["tdi_signal"].values
        cloud = result["tdi_cloud_bull"].values
        for i in range(len(fast)):
            if np.isnan(fast[i]) or np.isnan(sig[i]):
                self.assertFalse(cloud[i], msg="cloud True during NaN at bar " + str(i))
            else:
                expected = fast[i] > sig[i]
                self.assertEqual(cloud[i], expected,
                                 msg="cloud_bull wrong at bar " + str(i))

    def test_scalp_vectorized(self):
        """tdi_scalp is True iff fast_ma > bb_mid (ignoring NaN)."""
        result = compute_tdi(make_ohlcv(300))
        fast = result["tdi_fast_ma"].values
        bm = result["tdi_bb_mid"].values
        scalp = result["tdi_scalp"].values
        for i in range(len(fast)):
            if np.isnan(fast[i]) or np.isnan(bm[i]):
                self.assertFalse(scalp[i], msg="scalp True during NaN at bar " + str(i))
            else:
                expected = fast[i] > bm[i]
                self.assertEqual(scalp[i], expected,
                                 msg="scalp wrong at bar " + str(i))


class TestDivergence(unittest.TestCase):
    """Verify divergence detection logic."""

    def test_divs_are_bool(self):
        """All divergence columns must be bool dtype."""
        result = compute_tdi(make_ohlcv(300))
        for col in ["tdi_bull_div", "tdi_bear_div",
                    "tdi_hidden_bull_div", "tdi_hidden_bear_div"]:
            self.assertEqual(result[col].dtype, bool, msg=col + " not bool")

    def test_no_divs_on_30_bars(self):
        """30 bars = too few pivots, no divergence expected."""
        result = compute_tdi(make_ohlcv(30))
        for col in ["tdi_bull_div", "tdi_bear_div",
                    "tdi_hidden_bull_div", "tdi_hidden_bear_div"]:
            self.assertEqual(result[col].sum(), 0, msg=col + " fired on 30 bars")

    def test_rsi_pivot_only_approach(self):
        """_detect_divergences should only use RSI pivots (not price pivots)."""
        df = make_ohlcv(300)
        close = df["close"].values
        rsi = _rsi_wilder(close, 14)
        # Use tight range to force some divergences
        reg_bull, reg_bear, hid_bull, hid_bear = _detect_divergences(
            close, rsi, pivot_lookback=5, range_lower=5, range_upper=60
        )
        rsi_is_high, rsi_is_low = _detect_pivots(rsi, 5)
        # Divergences can only fire at confirmed+lookback positions
        # They must correspond to RSI pivot locations (not arbitrary)
        total_rsi_pivots = rsi_is_low.sum() + rsi_is_high.sum()
        total_divs = reg_bull.sum() + reg_bear.sum() + hid_bull.sum() + hid_bear.sum()
        # Total divergences can't exceed total RSI pivots (one per pivot max)
        self.assertLessEqual(total_divs, total_rsi_pivots,
                             msg="More divergences than RSI pivots — logic error")

    def test_range_check_reduces_signals(self):
        """Tighter range_upper must produce <= divergences than wider range."""
        df = make_ohlcv(500)
        tight = compute_tdi(df, {"tdi_div_range_upper": 15})
        wide = compute_tdi(df, {"tdi_div_range_upper": 60})
        for col in ["tdi_bull_div", "tdi_bear_div"]:
            self.assertGreaterEqual(wide[col].sum(), tight[col].sum(),
                                    msg="wider range should have >= signals: " + col)

    def test_divergence_fires_on_large_dataset(self):
        """1000 bars of random data should produce at least some divergences."""
        result = compute_tdi(make_ohlcv(1000, seed=123))
        total = (result["tdi_bull_div"].sum() + result["tdi_bear_div"].sum() +
                 result["tdi_hidden_bull_div"].sum() + result["tdi_hidden_bear_div"].sum())
        self.assertGreater(total, 0, msg="zero divergences on 1000 bars")

    def test_divergence_not_in_warmup(self):
        """No divergence during RSI warmup period."""
        df = make_ohlcv(500)
        result = compute_tdi(df)
        rp = PRESETS["cw_trades"]["tdi_rsi_period"]
        for col in ["tdi_bull_div", "tdi_bear_div"]:
            self.assertEqual(result[col].iloc[:rp].sum(), 0,
                             msg=col + " fires in warmup")


class TestCrossSignalsIntegration(unittest.TestCase):
    """Integration tests for RSI cross signal columns."""

    def test_cross_50_fires_on_300_bars(self):
        """At least one RSI cross 50 must fire on 300 bars."""
        result = compute_tdi(make_ohlcv(300))
        total = result["tdi_rsi_cross_50_up"].sum() + result["tdi_rsi_cross_50_down"].sum()
        self.assertGreater(total, 0)

    def test_signal_cross_fires_on_300_bars(self):
        """At least one RSI/signal cross must fire on 300 bars."""
        result = compute_tdi(make_ohlcv(300))
        total = (result["tdi_rsi_cross_signal_up"].sum() +
                 result["tdi_rsi_cross_signal_down"].sum())
        self.assertGreater(total, 0)

    def test_cross_50_up_and_down_mutually_exclusive(self):
        """RSI cross 50 up and down cannot fire on the same bar."""
        result = compute_tdi(make_ohlcv(300))
        both = result["tdi_rsi_cross_50_up"] & result["tdi_rsi_cross_50_down"]
        self.assertEqual(both.sum(), 0)

    def test_best_setup_is_fast_cross_bb_mid(self):
        """tdi_best_setup must equal crossover(fast_ma, bb_mid) independently."""
        result = compute_tdi(make_ohlcv(300))
        from signals.tdi import _cross as tdi_cross
        cross_up, _ = tdi_cross(result["tdi_fast_ma"].values, result["tdi_bb_mid"].values)
        np.testing.assert_array_equal(
            result["tdi_best_setup"].values, cross_up,
            err_msg="tdi_best_setup does not match crossover(fast, bb_mid)"
        )


class TestCoreSignals(unittest.TestCase):
    """Verify compute_tdi_core graded signal logic."""

    def setUp(self):
        """Compute core signals on 500 bars."""
        self.result = compute_tdi_core(make_ohlcv(500))

    def test_long_a_subset_of_long_b(self):
        """tdi_core_long_a implies tdi_core_long_b (A is stricter)."""
        long_a = self.result["tdi_core_long_a"]
        long_b = self.result["tdi_core_long_b"]
        violations = long_a & ~long_b
        self.assertEqual(violations.sum(), 0, msg="long_a fires without long_b")

    def test_short_a_subset_of_short_b(self):
        """tdi_core_short_a implies tdi_core_short_b."""
        short_a = self.result["tdi_core_short_a"]
        short_b = self.result["tdi_core_short_b"]
        violations = short_a & ~short_b
        self.assertEqual(violations.sum(), 0, msg="short_a fires without short_b")

    def test_long_b_subset_of_tdi_long(self):
        """tdi_core_long_b implies tdi_long (it adds scalp filter)."""
        long_b = self.result["tdi_core_long_b"]
        tdi_long = self.result["tdi_long"]
        violations = long_b & ~tdi_long
        self.assertEqual(violations.sum(), 0, msg="core_long_b fires without tdi_long")

    def test_no_long_short_core_same_bar(self):
        """No core long and core short on the same bar."""
        any_long = (self.result["tdi_core_long_a"] | self.result["tdi_core_long_b"] |
                    self.result["tdi_core_long_c"])
        any_short = (self.result["tdi_core_short_a"] | self.result["tdi_core_short_b"] |
                     self.result["tdi_core_short_c"])
        both = any_long & any_short
        self.assertEqual(both.sum(), 0, msg="core long and short on same bar")

    def test_core_cols_are_bool(self):
        """All core signal columns must be bool dtype."""
        for col in TDI_CORE_COLS:
            self.assertEqual(self.result[col].dtype, bool, msg=col + " not bool")


class TestEdgeCases(unittest.TestCase):
    """Edge cases and robustness."""

    def test_5_bars_no_crash(self):
        """5-bar DataFrame must not crash."""
        result = compute_tdi(make_ohlcv(5))
        self.assertEqual(len(result), 5)
        self.assertTrue(result["tdi_rsi"].isna().all())

    def test_single_bar_no_crash(self):
        """Single row must not crash."""
        result = compute_tdi(make_ohlcv(1))
        self.assertEqual(len(result), 1)

    def test_flat_price_no_crash(self):
        """Constant price series (zero RSI variance) must not crash."""
        df = make_ohlcv(100)
        df["close"] = 1.0
        df["open"] = 1.0
        df["high"] = 1.0
        df["low"] = 1.0
        result = compute_tdi(df)
        self.assertEqual(len(result), 100)

    def test_deterministic_output(self):
        """Same input must produce identical output on two calls."""
        df = make_ohlcv(300)
        r1 = compute_tdi(df)
        r2 = compute_tdi(df)
        pd.testing.assert_frame_equal(r1, r2)

    def test_input_df_not_mutated(self):
        """compute_tdi must not mutate the input DataFrame."""
        df = make_ohlcv(300)
        original_cols = list(df.columns)
        compute_tdi(df)
        self.assertEqual(list(df.columns), original_cols, msg="input df was mutated")


class TestPerformance(unittest.TestCase):
    """Performance sanity checks."""

    def test_1000_bars_under_5s(self):
        """compute_tdi on 1000 bars should complete in under 5 seconds."""
        df = make_ohlcv(1000)
        start = time.time()
        compute_tdi(df)
        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, msg="1000 bars took " + str(round(elapsed, 2)) + "s (> 5s)")

    def test_5000_bars_under_30s(self):
        """compute_tdi on 5000 bars should complete in under 30 seconds."""
        df = make_ohlcv(5000)
        start = time.time()
        compute_tdi(df)
        elapsed = time.time() - start
        self.assertLess(elapsed, 30.0, msg="5000 bars took " + str(round(elapsed, 2)) + "s (> 30s)")


# ---- Audit report -----------------------------------------------------------

def print_audit_report(result):
    """Print audit summary table from unittest result."""
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - errors - skipped

    log.info("=" * 60)
    log.info("TDI MODULE AUDIT REPORT")
    log.info("=" * 60)
    log.info("Total tests : %d", total)
    log.info("Passed      : %d", passed)
    log.info("Failed      : %d", failures)
    log.info("Errors      : %d", errors)
    log.info("Skipped     : %d", skipped)
    log.info("-" * 60)

    if failures:
        log.warning("FAILURES:")
        for test, traceback in result.failures:
            log.warning("  FAIL: %s", str(test))
            for line in traceback.strip().split("\n")[-3:]:
                log.warning("    %s", line)

    if errors:
        log.error("ERRORS:")
        for test, traceback in result.errors:
            log.error("  ERROR: %s", str(test))
            for line in traceback.strip().split("\n")[-3:]:
                log.error("    %s", line)

    if not failures and not errors:
        log.info("STATUS: ALL TESTS PASSED")
    else:
        log.warning("STATUS: BUILD REQUIRES ATTENTION")

    log.info("Log file: %s", str(log_path))
    log.info("=" * 60)


if __name__ == "__main__":
    log.info("=== TDI Module Test Suite ===")
    log.info("signals/tdi.py audit + regression + core signal validation")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print_audit_report(result)
    sys.exit(0 if result.wasSuccessful() else 1)
