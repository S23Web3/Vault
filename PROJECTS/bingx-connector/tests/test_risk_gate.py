"""
Tests for risk_gate.py — all 6 checks in isolation.
Run: python -m pytest tests/test_risk_gate.py -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from risk_gate import RiskGate


class MockSignal:
    """Mock signal for risk gate testing."""

    def __init__(self, direction="LONG", grade="A",
                 entry_price=100.0, atr=0.5,
                 sl_price=99.0, tp_price=101.0, bar_ts=0):
        """Initialize mock signal fields."""
        self.direction = direction
        self.grade = grade
        self.entry_price = entry_price
        self.atr = atr
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.bar_ts = bar_ts


class TestRiskGate(unittest.TestCase):
    """Test all 6 risk gate checks."""

    def setUp(self):
        """Set up risk gate with default config."""
        self.gate = RiskGate({
            "max_positions": 3,
            "max_daily_trades": 20,
            "daily_loss_limit_usd": 75.0,
            "min_atr_ratio": 0.003,
        })

    def _clean_state(self):
        """Return a clean state dict."""
        return {
            "open_positions": {},
            "daily_pnl": 0.0,
            "daily_trades": 0,
            "halt_flag": False,
        }

    def test_check1_halt_flag_blocks(self):
        """Check 1: halt_flag=True blocks."""
        state = self._clean_state()
        state["halt_flag"] = True
        ok, reason = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="halt_flag should block")
        self.assertIn("Hard Stop", reason)

    def test_check1_daily_pnl_at_limit(self):
        """Check 1: daily_pnl exactly at -75.0 blocks."""
        state = self._clean_state()
        state["daily_pnl"] = -75.0
        ok, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="-75.0 should block (<=)")

    def test_check1_daily_pnl_below_limit(self):
        """Check 1: daily_pnl below limit blocks."""
        state = self._clean_state()
        state["daily_pnl"] = -80.0
        ok, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="-80 should block")

    def test_check1_c03_halt_or_pnl(self):
        """BUG-C03: halt_flag alone blocks even if pnl ok."""
        state = self._clean_state()
        state["halt_flag"] = True
        state["daily_pnl"] = 0.0
        ok, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="halt alone should block (C03)")

    def test_check2_max_positions(self):
        """Check 2: max positions blocks."""
        state = self._clean_state()
        state["open_positions"] = {
            "A_L": {}, "B_L": {}, "C_L": {}}
        ok, reason = self.gate.evaluate(
            MockSignal(), "D-USDT", state, ["A"])
        self.assertFalse(ok, msg="3/3 should block")
        self.assertIn("Max Positions", reason)

    def test_check3_duplicate(self):
        """Check 3: duplicate symbol+direction blocks."""
        state = self._clean_state()
        state["open_positions"] = {"BTC-USDT_LONG": {}}
        ok, reason = self.gate.evaluate(
            MockSignal(direction="LONG"),
            "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="Duplicate should block")
        self.assertIn("Duplicate", reason)

    def test_check3_opposite_ok(self):
        """Check 3: opposite direction passes."""
        state = self._clean_state()
        state["open_positions"] = {"BTC-USDT_LONG": {}}
        ok, _ = self.gate.evaluate(
            MockSignal(direction="SHORT"),
            "BTC-USDT", state, ["A"])
        self.assertTrue(ok, msg="Opposite should pass")

    def test_check4_grade_filter(self):
        """Check 4: grade not in allowed list blocks."""
        state = self._clean_state()
        ok, reason = self.gate.evaluate(
            MockSignal(grade="C"),
            "BTC-USDT", state, ["A", "B"])
        self.assertFalse(ok, msg="Grade C not in [A,B]")
        self.assertIn("Grade", reason)

    def test_check4_c05_plugin_grades(self):
        """BUG-C05: allowed_grades from plugin."""
        state = self._clean_state()
        ok, _ = self.gate.evaluate(
            MockSignal(grade="MOCK"),
            "BTC-USDT", state, ["MOCK"])
        self.assertTrue(ok, msg="MOCK grade should pass")

    def test_check5_atr_threshold(self):
        """Check 5: low ATR ratio blocks."""
        state = self._clean_state()
        ok, reason = self.gate.evaluate(
            MockSignal(entry_price=100.0, atr=0.1),
            "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="ATR 0.001 should block")
        self.assertIn("Too Quiet", reason)

    def test_check6_daily_trade_limit(self):
        """Check 6: daily trade limit blocks."""
        state = self._clean_state()
        state["daily_trades"] = 20
        ok, reason = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="20/20 should block")
        self.assertIn("Trade Limit", reason)

    def test_check_order_halt_before_max(self):
        """Halt blocks before max_positions is checked."""
        state = self._clean_state()
        state["halt_flag"] = True
        state["open_positions"] = {
            "A_L": {}, "B_L": {}, "C_L": {}}
        ok, reason = self.gate.evaluate(
            MockSignal(), "D-USDT", state, ["A"])
        self.assertFalse(ok)
        self.assertIn("Hard Stop", reason,
                       msg="Should be Hard Stop: " + reason)

    def test_halt_persists(self):
        """halt_flag survives across evaluate() calls."""
        state = self._clean_state()
        state["halt_flag"] = True
        ok1, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        ok2, _ = self.gate.evaluate(
            MockSignal(), "ETH-USDT", state, ["A"])
        self.assertFalse(ok1, msg="First call blocked")
        self.assertFalse(ok2, msg="Second call blocked")

    def test_approved_path(self):
        """Clean state + valid signal -> APPROVED."""
        state = self._clean_state()
        ok, reason = self.gate.evaluate(
            MockSignal(grade="A", atr=0.5, entry_price=100.0),
            "BTC-USDT", state, ["A"])
        self.assertTrue(ok, msg="Should approve: " + reason)
        self.assertEqual(reason, "APPROVED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
