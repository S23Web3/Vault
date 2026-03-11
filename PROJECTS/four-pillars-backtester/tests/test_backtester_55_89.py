"""
Unit tests for Backtester5589.
Run: python tests/test_backtester_55_89.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.backtester_55_89 import Backtester5589


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

def _base_df(n=120, price=100.0, seed=42) -> pd.DataFrame:
    """Return synthetic OHLCV + indicator DataFrame with n bars."""
    rng = np.random.default_rng(seed)
    close = np.full(n, price)  # flat price makes SL arithmetic exact
    high = close * 1.003
    low = close * 0.997
    vol = rng.integers(1_000_000, 5_000_000, n).astype(float)
    atr = close * 0.005  # fixed 0.5% ATR
    df = pd.DataFrame({
        "open": close,
        "high": high.copy(),
        "low": low.copy(),
        "close": close.copy(),
        "volume": vol,
        "atr": atr,
        "ema_55": close * 0.998,
        "ema_89": close * 0.996,
        "stoch_9_d": np.full(n, 50.0),
        "long_a": np.zeros(n, dtype=bool),
        "short_a": np.zeros(n, dtype=bool),
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="1min")
    df.index.name = "datetime"
    return df


def _sl_for(df, entry_i: int, direction: str, sl_mult: float) -> float:
    """Compute the phase-1 SL price that the engine will set at entry."""
    ep = float(df["close"].iloc[entry_i])
    atr = float(df["atr"].iloc[entry_i])
    if direction == "LONG":
        return ep - sl_mult * atr
    return ep + sl_mult * atr


def _safe_lows(df, from_bar: int, to_bar: int, sl: float, cushion_mult: float = 1.5):
    """Set lows above sl + cushion so phase-1 SL never triggers."""
    safe = sl + cushion_mult * float(df["atr"].iloc[from_bar])
    for j in range(from_bar, min(to_bar, len(df))):
        df.loc[df.index[j], "low"] = safe
        if df.loc[df.index[j], "close"] < safe:
            df.loc[df.index[j], "close"] = safe


def _params_fast(extra=None) -> dict:
    """Return params with avwap_warmup=3 so phase-2 fires quickly in tests."""
    p = {
        "sl_mult": 2.0,
        "avwap_warmup": 3,
        "avwap_sigma": 2.0,
        "tp_atr_offset": 0.5,
        "ratchet_threshold": 2,
        "notional": 1000.0,
        "initial_equity": 10000.0,
        "sigma_floor_atr": 0.5,
    }
    if extra:
        p.update(extra)
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBacktester5589(unittest.TestCase):
    """Tests for Backtester5589 4-phase engine."""

    # --- basic structure ---

    def test_no_positions_no_crash(self):
        """Empty signals produce total_trades=0 without error."""
        df = _base_df()
        bt = Backtester5589(_params_fast())
        results = bt.run(df)
        self.assertEqual(results["metrics"]["total_trades"], 0,
                         msg="expected 0 trades when no signals; got " + str(results["metrics"]["total_trades"]))

    def test_results_dict_structure(self):
        """Results dict contains all required top-level keys."""
        df = _base_df()
        df.loc[df.index[10], "long_a"] = True
        bt = Backtester5589(_params_fast())
        results = bt.run(df)
        for key in ("trades", "trades_df", "metrics", "equity_curve", "position_counts"):
            self.assertIn(key, results, msg="missing key: " + key)
        self.assertIsInstance(results["equity_curve"], np.ndarray,
                              msg="equity_curve should be ndarray")
        self.assertIsInstance(results["trades_df"], pd.DataFrame,
                              msg="trades_df should be DataFrame")

    def test_metrics_required_keys(self):
        """Metrics dict contains all dashboard-compatible keys."""
        df = _base_df()
        df.loc[df.index[10], "long_a"] = True
        bt = Backtester5589(_params_fast())
        m = bt.run(df)["metrics"]
        required = [
            "total_trades", "win_count", "loss_count", "win_rate",
            "avg_win", "avg_loss", "expectancy", "gross_profit", "gross_loss",
            "profit_factor", "net_pnl", "total_commission", "total_rebate",
            "net_pnl_after_rebate", "sharpe", "max_drawdown", "max_drawdown_pct",
            "pct_losers_saw_green", "final_equity", "equity_curve",
            "total_volume", "total_sides", "avg_positions", "max_positions_used",
            "pct_time_flat", "tp_exits", "sl_exits",
            "phase1_exits", "phase2_exits", "phase3_exits", "phase4_exits",
            "avg_ratchet_count", "ratchet_threshold_hit_pct",
        ]
        for k in required:
            self.assertIn(k, m, msg="metrics missing key: " + k)

    # --- phase 1 ---

    def test_phase1_sl_fires(self):
        """Price hits SL on bar 1 after entry -> exit_reason sl_phase1."""
        df = _base_df(n=60)
        entry_i = 5
        df.loc[df.index[entry_i], "long_a"] = True
        sl_mult = 2.0
        sl = _sl_for(df, entry_i, "LONG", sl_mult)

        # Crash low below SL on the very next bar (bar 6 = bars_in_trade=1, phase=1)
        df.loc[df.index[entry_i + 1], "low"] = sl - float(df["atr"].iloc[entry_i + 1])
        df.loc[df.index[entry_i + 1], "close"] = sl - float(df["atr"].iloc[entry_i + 1])

        bt = Backtester5589(_params_fast({"sl_mult": sl_mult}))
        results = bt.run(df)
        trades = results["trades"]
        self.assertGreater(len(trades), 0, msg="expected at least 1 trade")
        t = trades[0]
        self.assertEqual(t["exit_reason"], "sl_phase1",
                         msg="expected sl_phase1, got " + str(t["exit_reason"]))
        self.assertEqual(t["phase_at_exit"], 1,
                         msg="expected phase 1 at exit, got " + str(t["phase_at_exit"]))

    # --- phase 2 ---

    def test_phase2_transition_occurs(self):
        """Trade surviving past avwap_warmup bars has phase >= 2 at exit."""
        df = _base_df(n=80)
        entry_i = 5
        sl_mult = 2.0
        warmup = 3
        df.loc[df.index[entry_i], "long_a"] = True

        # Compute exact SL and keep all lows safely above it until crash bar
        sl = _sl_for(df, entry_i, "LONG", sl_mult)
        crash_bar = entry_i + warmup + 5

        # All bars from entry+1 to crash-1: lows safely above SL
        _safe_lows(df, entry_i + 1, crash_bar, sl)

        # Crash on crash_bar: low well below SL
        df.loc[df.index[crash_bar], "low"] = sl - float(df["atr"].iloc[crash_bar]) * 2.0
        df.loc[df.index[crash_bar], "close"] = sl - float(df["atr"].iloc[crash_bar]) * 2.0

        bt = Backtester5589(_params_fast({"sl_mult": sl_mult, "avwap_warmup": warmup}))
        results = bt.run(df)
        trades = results["trades"]
        self.assertGreater(len(trades), 0, msg="expected at least 1 trade")
        t = trades[0]
        self.assertGreaterEqual(t["phase_at_exit"], 2,
                                msg="expected phase >= 2, got " + str(t["phase_at_exit"]))

    # --- phase 3 ratchet ---

    def test_phase3_ratchet_increments(self):
        """Stoch-9-D dipping below 20 then recovering increments ratchet_count."""
        df = _base_df(n=100)
        entry_i = 5
        sl_mult = 2.0
        warmup = 3
        df.loc[df.index[entry_i], "long_a"] = True

        sl = _sl_for(df, entry_i, "LONG", sl_mult)

        # Keep lows safe for the entire run
        _safe_lows(df, entry_i + 1, len(df), sl)

        # Inject one overzone cycle after warmup: dip below 20, then recover
        dip_start = entry_i + warmup + 1
        df.loc[df.index[dip_start], "stoch_9_d"] = 15.0
        df.loc[df.index[dip_start + 1], "stoch_9_d"] = 22.0  # exit overzone -> ratchet fires

        bt = Backtester5589(_params_fast({"sl_mult": sl_mult, "avwap_warmup": warmup}))
        results = bt.run(df)
        trades = results["trades"]
        self.assertGreater(len(trades), 0, msg="expected at least 1 trade")
        t = trades[0]
        self.assertGreaterEqual(t["ratchet_count"], 1,
                                msg="expected ratchet_count >= 1, got " + str(t["ratchet_count"]))

    # --- phase 4 TP ---

    def test_phase4_tp_fires(self):
        """After ratchet_threshold overzone exits, TP on Cloud4 touch exits with tp_phase4."""
        n = 150
        df = _base_df(n=n, price=100.0)
        entry_i = 5
        sl_mult = 2.0
        warmup = 3
        ratchet_threshold = 2
        df.loc[df.index[entry_i], "long_a"] = True

        sl = _sl_for(df, entry_i, "LONG", sl_mult)
        _safe_lows(df, entry_i + 1, n, sl)

        params = _params_fast({
            "sl_mult": sl_mult,
            "avwap_warmup": warmup,
            "ratchet_threshold": ratchet_threshold,
            "tp_atr_offset": 0.0,  # TP = exactly Cloud4 edge
        })

        # Two overzone cycles after warmup
        c1_start = entry_i + warmup + 1
        df.loc[df.index[c1_start], "stoch_9_d"] = 15.0
        df.loc[df.index[c1_start + 1], "stoch_9_d"] = 25.0  # ratchet 1

        c2_start = c1_start + 3
        df.loc[df.index[c2_start], "stoch_9_d"] = 12.0
        df.loc[df.index[c2_start + 1], "stoch_9_d"] = 28.0  # ratchet 2 -> phase 4 activates

        # Price touches Cloud4 (ema_89) on the next bar after phase 4 activates
        tp_bar = c2_start + 2
        tp_level = float(df["ema_89"].iloc[tp_bar])
        df.loc[df.index[tp_bar], "high"] = tp_level * 1.01  # high reaches into TP zone
        df.loc[df.index[tp_bar], "close"] = tp_level

        bt = Backtester5589(params)
        results = bt.run(df)
        trades = results["trades"]
        tp_trades = [t for t in trades if t["exit_reason"] == "tp_phase4"]
        self.assertGreater(len(tp_trades), 0,
                           msg="expected tp_phase4 exit; got trades=" + str(
                               [(t["exit_reason"], t["ratchet_count"]) for t in trades]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
