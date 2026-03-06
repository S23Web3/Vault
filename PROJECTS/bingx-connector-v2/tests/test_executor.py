"""
Tests for executor.py — order construction with mocked HTTP.
Run: python -m pytest tests/test_executor.py -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from executor import Executor
from bingx_auth import BingXAuth


class MockSignal:
    """Mock signal for executor testing."""

    def __init__(self, direction="LONG", grade="A",
                 entry_price=100.0, sl_price=98.0,
                 tp_price=103.0, atr=1.0, bar_ts=0):
        """Initialize mock signal."""
        self.direction = direction
        self.grade = grade
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.atr = atr
        self.bar_ts = bar_ts


def _mock_resp(json_data):
    """Create a mock HTTP response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


class TestExecutor(unittest.TestCase):
    """Test order construction and quantity calculation."""

    def setUp(self):
        """Set up executor with mocked deps."""
        self.auth = BingXAuth("k", "s", demo_mode=True)
        self.state = MagicMock()
        self.notifier = MagicMock()
        self.executor = Executor(
            self.auth, self.state, self.notifier,
            {"margin_usd": 50.0, "leverage": 10})

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_quantity_calculation(self, mock_get, mock_post):
        """Qty = notional / mark_price, rounded down to step."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "0.005"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "TEST-USDT",
                 "tradeMinQuantity": "1"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "123"}})
        result = self.executor.execute(
            MockSignal(sl_price=0.003), "TEST-USDT")
        self.assertIsNotNone(result, msg="Should succeed")
        self.state.record_open_position.assert_called_once()
        pos = self.state.record_open_position.call_args[0][1]
        self.assertEqual(pos["quantity"], 100000.0,
                         msg="qty: " + str(pos["quantity"]))

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_long_payload(self, mock_get, mock_post):
        """LONG -> side=BUY, positionSide=LONG."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        self.executor.execute(
            MockSignal(direction="LONG"), "BTC-USDT")
        url = mock_post.call_args[0][0]
        self.assertIn("side=BUY", url,
                       msg="LONG->BUY: " + url[:200])
        self.assertIn("positionSide=LONG", url,
                       msg="LONG pos: " + url[:200])

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_short_payload(self, mock_get, mock_post):
        """SHORT -> side=SELL, positionSide=SHORT."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        self.executor.execute(
            MockSignal(direction="SHORT", sl_price=102.0), "BTC-USDT")
        url = mock_post.call_args[0][0]
        self.assertIn("side=SELL", url, msg="SHORT->SELL")
        self.assertIn("positionSide=SHORT", url,
                       msg="SHORT pos")

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_sl_tp_in_payload(self, mock_get, mock_post):
        """SL and TP present as JSON strings in URL."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        self.executor.execute(
            MockSignal(sl_price=98.0, tp_price=103.0),
            "BTC-USDT")
        url = mock_post.call_args[0][0]
        self.assertIn("stopLoss=", url, msg="Missing SL")
        self.assertIn("takeProfit=", url, msg="Missing TP")

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_api_failure_returns_none(self, mock_get, mock_post):
        """API error -> None, no position recorded."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": -1, "msg": "error"})
        result = self.executor.execute(
            MockSignal(), "BTC-USDT")
        self.assertIsNone(result, msg="Failed should be None")
        self.state.record_open_position.assert_not_called()

    @patch("executor.requests.get")
    def test_mark_price_failure(self, mock_get):
        """Mark price failure -> None, no order."""
        mock_get.return_value = _mock_resp(
            {"code": -1, "msg": "error"})
        result = self.executor.execute(
            MockSignal(), "BTC-USDT")
        self.assertIsNone(result, msg="No price -> None")

    @patch("executor.requests.get")
    def test_step_size_failure(self, mock_get):
        """Step size failure -> None, no order."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": -1, "msg": "error"}),
        ]
        result = self.executor.execute(
            MockSignal(), "BTC-USDT")
        self.assertIsNone(result, msg="No step -> None")

    def test_round_down(self):
        """Round DOWN to step size."""
        rd = self.executor._round_down
        self.assertEqual(rd(10.7, 1.0), 10.0)
        self.assertEqual(rd(0.00567, 0.001), 0.005)
        self.assertAlmostEqual(rd(99.99, 0.01), 99.99, places=8)
        self.assertEqual(rd(1.0, 0.1), 1.0)

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_trailing_order_placed_on_entry(self, mock_get, mock_post):
        """When trailing config present, a TRAILING_STOP_MARKET is placed after main order."""
        executor = Executor(
            self.auth, self.state, self.notifier,
            {"margin_usd": 50.0, "leverage": 10,
             "trailing_rate": 0.02, "trailing_activation_atr_mult": 2.0})
        mock_get.side_effect = [
            _mock_resp({"code": 0, "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT", "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "999"}})
        result = executor.execute(
            MockSignal(direction="LONG", sl_price=98.0,
                       tp_price=None, atr=1.0),
            "BTC-USDT")
        self.assertIsNotNone(result, msg="Execute should succeed")
        self.assertEqual(mock_post.call_count, 2,
                         msg="Should have 2 POST calls: main + trailing")
        trailing_url = mock_post.call_args_list[1][0][0]
        self.assertIn("TRAILING_STOP_MARKET", trailing_url,
                      msg="Trailing order type missing: " + trailing_url[:300])
        self.assertIn("priceRate=0.02", trailing_url,
                      msg="priceRate missing: " + trailing_url[:300])
        self.assertIn("activationPrice=102.0", trailing_url,
                      msg="activationPrice wrong (expected 102.0): " + trailing_url[:300])
        self.assertIn("side=SELL", trailing_url,
                      msg="Close side should be SELL for LONG: " + trailing_url[:300])

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_trailing_short_activation_price(self, mock_get, mock_post):
        """SHORT trailing activation = entry - atr * mult."""
        executor = Executor(
            self.auth, self.state, self.notifier,
            {"margin_usd": 50.0, "leverage": 10,
             "trailing_rate": 0.02, "trailing_activation_atr_mult": 2.0})
        mock_get.side_effect = [
            _mock_resp({"code": 0, "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT", "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "888"}})
        executor.execute(
            MockSignal(direction="SHORT", sl_price=102.0,
                       tp_price=None, atr=1.0),
            "BTC-USDT")
        trailing_url = mock_post.call_args_list[1][0][0]
        self.assertIn("activationPrice=98.0", trailing_url,
                      msg="SHORT: activation=100-1*2=98: " + trailing_url[:300])
        self.assertIn("side=BUY", trailing_url,
                      msg="Close side should be BUY for SHORT: " + trailing_url[:300])

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_no_trailing_without_config(self, mock_get, mock_post):
        """When trailing config absent, only one POST (main order)."""
        mock_get.side_effect = [
            _mock_resp({"code": 0, "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT", "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "111"}})
        self.executor.execute(MockSignal(sl_price=98.0), "BTC-USDT")
        self.assertEqual(mock_post.call_count, 1,
                         msg="No trailing config -> only 1 POST")


if __name__ == "__main__":
    unittest.main(verbosity=2)
