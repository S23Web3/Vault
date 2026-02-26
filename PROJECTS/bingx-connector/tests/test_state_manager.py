"""
Tests for state_manager.py — persistence, atomicity, threads.
Run: python -m pytest tests/test_state_manager.py -v
"""
import sys
import json
import unittest
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from state_manager import StateManager


class TestStateManager(unittest.TestCase):
    """Test state persistence and thread safety."""

    def setUp(self):
        """Set up temp directory for state files."""
        self.tmpdir = tempfile.mkdtemp()
        self.sp = Path(self.tmpdir) / "state.json"
        self.tp = Path(self.tmpdir) / "trades.csv"
        self.mgr = StateManager(self.sp, self.tp)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_open_position(self):
        """Position appears in state, daily_trades incremented."""
        self.mgr.record_open_position("BTC_LONG", {
            "symbol": "BTC-USDT", "direction": "LONG",
            "entry_price": 42000.0})
        s = self.mgr.get_state()
        self.assertIn("BTC_LONG", s["open_positions"])
        self.assertEqual(s["daily_trades"], 1)

    def test_close_position(self):
        """Close: removed from state, pnl updated, csv appended."""
        self.mgr.record_open_position("ETH_SHORT", {
            "symbol": "ETH-USDT", "direction": "SHORT",
            "grade": "A", "entry_price": 3000.0,
            "quantity": 1.0, "notional_usd": 500.0,
            "entry_time": "2026-01-01T00:00:00",
            "order_id": "123"})
        result = self.mgr.close_position(
            "ETH_SHORT", 2950.0, "TP", 50.0)
        self.assertIsNotNone(result)
        s = self.mgr.get_state()
        self.assertNotIn("ETH_SHORT", s["open_positions"])
        self.assertEqual(s["daily_pnl"], 50.0)
        self.assertTrue(self.tp.exists())

    def test_close_missing(self):
        """Closing non-existent position returns None."""
        result = self.mgr.close_position("FAKE", 0, "SL", -10)
        self.assertIsNone(result)

    def test_reset_daily(self):
        """reset_daily zeroes pnl, trades, halt (C04)."""
        self.mgr.record_open_position("A_L", {"symbol": "A"})
        self.mgr.close_position("A_L", 0, "SL", -50.0)
        self.mgr.set_halt_flag(True)
        self.mgr.reset_daily()
        s = self.mgr.get_state()
        self.assertEqual(s["daily_pnl"], 0.0)
        self.assertEqual(s["daily_trades"], 0)
        self.assertFalse(s["halt_flag"], msg="halt not reset")

    def test_atomic_persistence(self):
        """State persists on disk and can be reloaded."""
        self.mgr.record_open_position("X_L", {"symbol": "X"})
        mgr2 = StateManager(self.sp, self.tp)
        s = mgr2.get_state()
        self.assertIn("X_L", s["open_positions"])

    def test_load_empty(self):
        """Missing state.json returns defaults."""
        p = Path(self.tmpdir) / "no.json"
        mgr = StateManager(p, self.tp)
        s = mgr.get_state()
        self.assertEqual(len(s["open_positions"]), 0)
        self.assertEqual(s["daily_pnl"], 0.0)
        self.assertFalse(s["halt_flag"])

    def test_load_corrupt(self):
        """Corrupt state.json returns defaults."""
        self.sp.write_text("not json{{{", encoding="utf-8")
        mgr = StateManager(self.sp, self.tp)
        s = mgr.get_state()
        self.assertEqual(s["daily_pnl"], 0.0)

    def test_reconcile_removes_phantom(self):
        """Reconcile removes positions not on exchange."""
        self.mgr.record_open_position(
            "PHANTOM_LONG", {"symbol": "PHANTOM"})
        self.mgr.reconcile([])
        s = self.mgr.get_state()
        self.assertNotIn("PHANTOM_LONG", s["open_positions"])

    def test_reconcile_keeps_real(self):
        """Reconcile keeps positions on exchange."""
        self.mgr.record_open_position(
            "BTC-USDT_LONG", {"symbol": "BTC-USDT"})
        self.mgr.reconcile([
            {"symbol": "BTC-USDT", "positionAmt": "0.001"}])
        s = self.mgr.get_state()
        self.assertIn("BTC-USDT_LONG", s["open_positions"])

    def test_thread_safety(self):
        """Concurrent ops don't corrupt state."""
        errors = []

        def worker_record(n):
            """Record positions."""
            try:
                tid = threading.current_thread().ident
                for i in range(n):
                    key = "T" + str(tid) + "_" + str(i) + "_L"
                    self.mgr.record_open_position(
                        key, {"symbol": "T"})
            except Exception as e:
                errors.append(str(e))

        def worker_close():
            """Close positions."""
            try:
                for k in list(
                        self.mgr.get_open_positions().keys()):
                    self.mgr.close_position(k, 0, "T", 0)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(3):
            t = threading.Thread(target=worker_record, args=(10,))
            threads.append(t)
            t.start()
        for _ in range(2):
            t = threading.Thread(target=worker_close)
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(errors), 0,
                         msg="Errors: " + ", ".join(errors))
        raw = self.sp.read_text(encoding="utf-8")
        state = json.loads(raw)
        self.assertIn("open_positions", state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
