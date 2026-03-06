"""
Tests for bingx_auth.py — HMAC signature correctness.
Run: python -m pytest tests/test_auth.py -v
"""
import sys
import hashlib
import hmac
import unittest
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bingx_auth import BingXAuth


class TestBingXAuth(unittest.TestCase):
    """Test HMAC signing, public URLs, demo toggle."""

    def setUp(self):
        """Set up test auth instance."""
        self.auth = BingXAuth(
            "test_api_key", "test_secret", demo_mode=True)

    def test_sign_params_known_vector(self):
        """Known input produces correct HMAC-SHA256 hex digest."""
        params = {
            "symbol": "BTC-USDT",
            "side": "BUY",
            "timestamp": "1700000000000",
        }
        qs, sig = self.auth.sign_params(params)
        expected_qs = urlencode(sorted(params.items()))
        self.assertEqual(qs, expected_qs,
                         msg="Query string not sorted: " + qs)
        expected_sig = hmac.new(
            b"test_secret",
            expected_qs.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(sig, expected_sig,
                         msg="Signature mismatch: " + sig)

    def test_public_url_no_signature(self):
        """Public URL has no signature or timestamp."""
        url = self.auth.build_public_url(
            "/test/path", {"symbol": "BTC-USDT"})
        self.assertNotIn("signature", url,
                         msg="Public URL has sig: " + url)
        self.assertNotIn("timestamp", url,
                         msg="Public URL has ts: " + url)

    def test_public_url_no_params(self):
        """Public URL with no params is base + path."""
        url = self.auth.build_public_url("/test/path")
        self.assertTrue(url.endswith("/test/path"),
                        msg="URL wrong: " + url)

    def test_demo_url_toggle(self):
        """demo_mode=True uses VST, False uses live."""
        demo = BingXAuth("k", "s", demo_mode=True)
        self.assertIn("open-api-vst.bingx.com", demo.base_url,
                       msg="Demo URL: " + demo.base_url)
        live = BingXAuth("k", "s", demo_mode=False)
        self.assertIn("open-api.bingx.com", live.base_url,
                       msg="Live URL: " + live.base_url)
        self.assertNotIn("vst", live.base_url,
                          msg="Live has vst: " + live.base_url)

    def test_signed_request_structure(self):
        """Signed request has timestamp, signature, API key header."""
        req = self.auth.build_signed_request(
            "GET", "/test", {"symbol": "ETH-USDT"})
        self.assertIn("timestamp=", req["url"],
                       msg="No ts: " + req["url"])
        self.assertIn("signature=", req["url"],
                       msg="No sig: " + req["url"])
        self.assertEqual(
            req["headers"]["X-BX-APIKEY"], "test_api_key",
            msg="API key header wrong")
        self.assertEqual(req["method"], "GET")

    def test_params_sorted_alphabetically(self):
        """Signed params are sorted alphabetically."""
        params = {"zebra": "1", "alpha": "2", "middle": "3"}
        req = self.auth.build_signed_request("POST", "/t", params)
        url = req["url"]
        qs_start = url.index("?") + 1
        sig_start = url.index("&signature=")
        qs = url[qs_start:sig_start]
        parts = qs.split("&")
        keys = [p.split("=")[0] for p in parts]
        self.assertEqual(keys, sorted(keys),
                         msg="Not sorted: " + str(keys))


if __name__ == "__main__":
    unittest.main(verbosity=2)
