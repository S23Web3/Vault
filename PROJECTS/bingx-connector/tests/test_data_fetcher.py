"""
Tests for data_fetcher.py — kline fetch and new-bar detection.
Run: python -m pytest tests/test_data_fetcher.py -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_fetcher import MarketDataFeed


def _kline_resp(n=10, start_ts=1700000000000,
                interval_ms=300000):
    """Create a mock klines API response."""
    data = []
    for i in range(n):
        ts = start_ts + i * interval_ms
        data.append({
            "time": str(ts), "open": "100.0",
            "high": "101.0", "low": "99.0",
            "close": "100.5", "volume": "1000"})
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"code": 0, "data": data}
    return resp


class TestDataFetcher(unittest.TestCase):
    """Test kline fetch and new-bar detection."""

    def setUp(self):
        """Set up feed."""
        self.feed = MarketDataFeed(
            base_url="https://test.bingx.com",
            symbols=["BTC-USDT"],
            timeframe="5m", buffer_bars=200,
            poll_interval=30)

    @patch("data_fetcher.requests.Session.get")
    def test_new_bar_same_ts(self, mock_get):
        """Same timestamp twice -> not new bar."""
        mock_get.return_value = _kline_resp(n=5)
        df = self.feed._fetch_klines("BTC-USDT")
        self.assertIsNotNone(df)
        self.feed.last_bar_ts["BTC-USDT"] = int(
            df.iloc[-2]["time"])
        result = self.feed._is_new_bar("BTC-USDT", df)
        self.assertFalse(result, msg="Same ts not new")

    @patch("data_fetcher.requests.Session.get")
    def test_new_bar_new_ts(self, mock_get):
        """New timestamp -> new bar."""
        r1 = _kline_resp(n=5, start_ts=1700000000000)
        r2 = _kline_resp(n=5, start_ts=1700000300000)
        mock_get.side_effect = [r1, r2]
        df1 = self.feed._fetch_klines("BTC-USDT")
        self.feed.last_bar_ts["BTC-USDT"] = int(
            df1.iloc[-2]["time"])
        df2 = self.feed._fetch_klines("BTC-USDT")
        result = self.feed._is_new_bar("BTC-USDT", df2)
        self.assertTrue(result, msg="New ts should be new")

    @patch("data_fetcher.requests.Session.get")
    def test_api_error(self, mock_get):
        """API error code returns None."""
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"code": -1, "msg": "err"}
        mock_get.return_value = resp
        result = self.feed._fetch_klines("BTC-USDT")
        self.assertIsNone(result)

    @patch("data_fetcher.requests.Session.get")
    def test_timeout(self, mock_get):
        """Timeout returns None."""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("timeout")
        result = self.feed._fetch_klines("BTC-USDT")
        self.assertIsNone(result)

    @patch("data_fetcher.requests.Session.get")
    def test_buffer_cap(self, mock_get):
        """Buffer caps at buffer_bars."""
        self.feed.buffer_bars = 10
        mock_get.return_value = _kline_resp(n=20)
        df = self.feed._fetch_klines("BTC-USDT")
        self.assertLessEqual(len(df), 10,
                             msg="Buffer: " + str(len(df)))

    @patch("data_fetcher.requests.Session.get")
    def test_warmup(self, mock_get):
        """warmup populates all symbol buffers."""
        self.feed.symbols = ["BTC-USDT", "ETH-USDT"]
        mock_get.return_value = _kline_resp(n=5)
        self.feed.warmup()
        self.assertIn("BTC-USDT", self.feed.buffers)
        self.assertIn("ETH-USDT", self.feed.buffers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
