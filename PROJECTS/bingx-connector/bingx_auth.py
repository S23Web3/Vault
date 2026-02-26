"""
BingX authentication and request signing.
HMAC-SHA256 with alphabetical param sorting.
"""
import hashlib
import hmac
import time
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

LIVE_BASE = "https://open-api.bingx.com"
DEMO_BASE = "https://open-api-vst.bingx.com"


class BingXAuth:
    """HMAC-SHA256 signing for BingX perpetual swap API."""

    def __init__(self, api_key, secret_key, demo_mode=True):
        """Initialize with API credentials and mode toggle."""
        self.api_key = api_key
        self.secret_key = secret_key
        self.demo_mode = demo_mode
        self.base_url = DEMO_BASE if demo_mode else LIVE_BASE
        logger.info("BingXAuth: base=%s demo=%s", self.base_url, demo_mode)

    def sign_params(self, params):
        """Sort params alphabetically, compute HMAC-SHA256 hex digest."""
        sorted_params = sorted(params.items())
        query_string = "&".join(k + "=" + str(v) for k, v in sorted_params)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return query_string, signature

    def build_signed_request(self, method, path, params=None):
        """Build a fully signed request with URL, headers, and method."""
        if params is None:
            params = {}
        params["timestamp"] = str(int(time.time() * 1000))
        params["recvWindow"] = "10000"
        query_string, signature = self.sign_params(params)
        url = (self.base_url + path + "?" + query_string
               + "&signature=" + signature)
        headers = {"X-BX-APIKEY": self.api_key}
        return {"url": url, "headers": headers, "method": method}

    def build_public_url(self, path, params=None):
        """Build public URL — no timestamp, no signature (BUG-C07 fix)."""
        if params is None:
            params = {}
        if params:
            query_string = urlencode(sorted(params.items()))
            return self.base_url + path + "?" + query_string
        return self.base_url + path
