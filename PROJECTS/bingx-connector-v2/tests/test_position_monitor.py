"""
Tests for position_monitor.py -- breakeven price calculation.
Run: python -m pytest tests/test_position_monitor.py -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from position_monitor import PositionMonitor

COMMISSION_RATE = 0.001  # 0.1% RT (0.05% per side), as used on live account


def _mock_resp(json_data):
    """Return a mock HTTP response with the given JSON body."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


def _make_monitor(commission_rate=COMMISSION_RATE):
    """Construct a PositionMonitor with fully mocked dependencies."""
    auth = MagicMock()
    auth.build_signed_request.return_value = {
        "url": "https://example.com/order",
        "headers": {},
    }
    state = MagicMock()
    state.get_state.return_value = {}
    state.get_open_positions.return_value = {}
    notifier = MagicMock()
    monitor = PositionMonitor(
        auth, state, notifier,
        config={},
        commission_rate=commission_rate,
    )
    return monitor, auth, state, notifier


class TestBEPriceFormula(unittest.TestCase):
    """Verify _place_be_sl() computes correct BE stop price."""

    @patch("position_monitor.requests.post")
    def test_long_be_price_above_entry(self, mock_post):
        """LONG: be_price == entry * (1 + commission_rate)."""
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        monitor, auth, _, _ = _make_monitor()
        entry = 1.000
        pos_data = {"direction": "LONG", "entry_price": entry,
                    "quantity": 50.0}
        be_price = monitor._place_be_sl("TEST-USDT", pos_data)
        self.assertIsNotNone(be_price, msg="Success -> float returned")
        expected = entry * (1 + COMMISSION_RATE)
        self.assertAlmostEqual(be_price, expected, places=8,
                               msg="LONG be_price: entry*(1+cr)")
        self.assertGreater(be_price, entry,
                           msg="LONG BE stop must be above entry")

    @patch("position_monitor.requests.post")
    def test_short_be_price_below_entry(self, mock_post):
        """SHORT: be_price == entry * (1 - commission_rate)."""
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "2"}})
        monitor, auth, _, _ = _make_monitor()
        entry = 0.084630  # ELSA from live log
        pos_data = {"direction": "SHORT", "entry_price": entry,
                    "quantity": 574.02}
        be_price = monitor._place_be_sl("ELSA-USDT", pos_data)
        self.assertIsNotNone(be_price)
        expected = entry * (1 - COMMISSION_RATE)
        self.assertAlmostEqual(be_price, expected, places=8,
                               msg="SHORT be_price: entry*(1-cr)")
        self.assertLess(be_price, entry,
                        msg="SHORT BE stop must be below entry")

    @patch("position_monitor.requests.post")
    def test_stop_price_in_api_params(self, mock_post):
        """stopPrice in the API request params must equal be_price."""
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "3"}})
        monitor, auth, _, _ = _make_monitor()
        entry = 1.873  # ATOM from live log
        pos_data = {"direction": "SHORT", "entry_price": entry,
                    "quantity": 25.92}
        be_price = monitor._place_be_sl("ATOM-USDT", pos_data)
        self.assertIsNotNone(be_price)
        # Verify params passed to build_signed_request
        call_params = auth.build_signed_request.call_args[0][2]
        stop_in_call = float(call_params["stopPrice"])
        self.assertAlmostEqual(stop_in_call, be_price, places=7,
                               msg="stopPrice in API call must match be_price")

    @patch("position_monitor.requests.post")
    def test_api_failure_returns_none(self, mock_post):
        """API error -> _place_be_sl returns None (not False)."""
        mock_post.return_value = _mock_resp(
            {"code": -1, "msg": "insufficient balance"})
        monitor, _, _, _ = _make_monitor()
        pos_data = {"direction": "LONG", "entry_price": 100.0,
                    "quantity": 0.5}
        result = monitor._place_be_sl("BTC-USDT", pos_data)
        self.assertIsNone(result, msg="API failure -> None")

    @patch("position_monitor.requests.post")
    def test_net_pnl_zero_at_be_price(self, mock_post):
        """If STOP_MARKET fills exactly at be_price, net pnl >= 0."""
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "4"}})
        notional = 50.0
        cr = COMMISSION_RATE
        for direction, entry in [("LONG", 100.0), ("SHORT", 0.08463),
                                  ("SHORT", 1.873), ("LONG", 0.007403)]:
            monitor, _, _, _ = _make_monitor(commission_rate=cr)
            qty = notional / entry
            pos_data = {"direction": direction, "entry_price": entry,
                        "quantity": qty}
            be_price = monitor._place_be_sl("X-USDT", pos_data)
            self.assertIsNotNone(be_price)
            if direction == "LONG":
                gross = (be_price - entry) * qty
            else:
                gross = (entry - be_price) * qty
            commission = notional * cr
            net = gross - commission
            self.assertGreaterEqual(
                net, -1e-6,
                msg=("net pnl at be_price must be >= 0 for "
                     + direction + " entry=" + str(entry)
                     + " got " + str(net)))

    @patch("position_monitor.requests.post")
    def test_missing_data_returns_none(self, mock_post):
        """Missing direction/entry/qty -> None without API call."""
        monitor, _, _, _ = _make_monitor()
        result = monitor._place_be_sl("X-USDT", {"direction": "", "entry_price": 0,
                                                  "quantity": 0})
        self.assertIsNone(result, msg="Missing data -> None")
        mock_post.assert_not_called()

    @patch("position_monitor.requests.post")
    def test_commission_rate_used_not_hardcoded(self, mock_post):
        """BE price must use self.commission_rate, not a hardcoded constant."""
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "5"}})
        cr_custom = 0.0016  # 0.16% RT (0.08% per side)
        monitor, _, _, _ = _make_monitor(commission_rate=cr_custom)
        entry = 1.000
        pos_data = {"direction": "LONG", "entry_price": entry, "quantity": 1.0}
        be_price = monitor._place_be_sl("TEST-USDT", pos_data)
        self.assertIsNotNone(be_price)
        expected = entry * (1 + cr_custom)
        self.assertAlmostEqual(be_price, expected, places=8,
                               msg="commission_rate must come from self, not hardcoded")


if __name__ == "__main__":
    unittest.main(verbosity=2)
