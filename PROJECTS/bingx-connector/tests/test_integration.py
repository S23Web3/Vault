"""
Integration test: end-to-end signal-to-execution, all HTTP mocked.
Run: python -m pytest tests/test_integration.py -v
"""
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bingx_auth import BingXAuth
from notifier import Notifier
from state_manager import StateManager
from risk_gate import RiskGate
from executor import Executor
from position_monitor import PositionMonitor
from plugins.mock_strategy import Signal


def _resp(json_data):
    """Create mock HTTP response."""
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status = MagicMock()
    r.json.return_value = json_data
    return r


class TestIntegration(unittest.TestCase):
    """End-to-end integration with all HTTP mocked."""

    def setUp(self):
        """Set up all components with temp state."""
        self.tmpdir = tempfile.mkdtemp()
        sp = Path(self.tmpdir) / "state.json"
        tp = Path(self.tmpdir) / "trades.csv"
        self.auth = BingXAuth("k", "s", demo_mode=True)
        self.notifier = MagicMock(spec=Notifier)
        self.notifier.send = MagicMock(return_value=True)
        self.state_mgr = StateManager(sp, tp)
        self.trades_path = tp
        self.risk_gate = RiskGate({
            "max_positions": 3,
            "max_daily_trades": 20,
            "daily_loss_limit_usd": 75.0,
            "min_atr_ratio": 0.003,
        })
        self.executor = Executor(
            self.auth, self.state_mgr, self.notifier,
            {"margin_usd": 50.0, "leverage": 10})
        self.monitor = PositionMonitor(
            self.auth, self.state_mgr, self.notifier,
            {"daily_loss_limit_usd": 75.0,
             "daily_summary_utc_hour": 17})

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_full_entry(self, mock_get, mock_post):
        """Signal -> risk gate -> execute -> 1 position."""
        mock_get.side_effect = [
            _resp({"code": 0, "data": {"price": "0.005"}}),
            _resp({"code": 0, "data": [
                {"symbol": "RIVER-USDT",
                 "tradeMinQuantity": "1"}]}),
        ]
        mock_post.return_value = _resp(
            {"code": 0, "data": {"orderId": "99"}})
        sig = Signal(
            direction="LONG", grade="MOCK",
            entry_price=0.005, sl_price=0.004,
            tp_price=0.007, atr=0.0001, bar_ts=17e11)
        state_dict = self.state_mgr.get_state()
        ok, reason = self.risk_gate.evaluate(
            sig, "RIVER-USDT", state_dict, ["MOCK"])
        self.assertTrue(ok, msg="Approve: " + reason)
        result = self.executor.execute(sig, "RIVER-USDT")
        self.assertIsNotNone(result)
        s = self.state_mgr.get_state()
        self.assertEqual(len(s["open_positions"]), 1)
        self.assertIn("RIVER-USDT_LONG", s["open_positions"])
        self.notifier.send.assert_called()

    @patch("executor.requests.post")
    @patch("requests.get")
    def test_entry_then_close(self, mock_get, mock_post):
        """Entry then close -> 0 positions, csv exists."""
        _responses = iter([
            _resp({"code": 0, "data": {"price": "0.005"}}),
            _resp({"code": 0, "data": [
                {"symbol": "RIVER-USDT",
                 "tradeMinQuantity": "1"}]}),
            _resp({"code": 0, "data": []}),
        ])
        mock_get.side_effect = lambda *a, **kw: next(_responses)
        mock_post.return_value = _resp(
            {"code": 0, "data": {"orderId": "99"}})
        sig = Signal(
            direction="LONG", grade="MOCK",
            entry_price=0.005, sl_price=0.004,
            tp_price=0.007, atr=0.0001, bar_ts=17e11)
        result = self.executor.execute(sig, "RIVER-USDT")
        self.assertIsNotNone(result, msg="execute must succeed")
        self.monitor.check()
        s = self.state_mgr.get_state()
        self.assertEqual(len(s["open_positions"]), 0,
                         msg="Should be 0 after close")
        self.assertTrue(self.trades_path.exists())

    def test_daily_reset(self):
        """reset_daily clears pnl, trades, halt."""
        self.state_mgr.state["daily_pnl"] = -80.0
        self.state_mgr.state["daily_trades"] = 15
        self.state_mgr.state["halt_flag"] = True
        self.state_mgr.reset_daily()
        s = self.state_mgr.get_state()
        self.assertEqual(s["daily_pnl"], 0.0)
        self.assertEqual(s["daily_trades"], 0)
        self.assertFalse(s["halt_flag"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
