"""
Connection test for BingX API (requires .env).
Does NOT place orders. Read-only + one Telegram message.
Run: python scripts/test_connection.py
"""
import os
import sys
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bingx_auth import BingXAuth
from notifier import Notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)
RESULTS = []


def test_step(name, func):
    """Run a test step and record result."""
    start = time.time()
    try:
        ok = func()
        ms = round((time.time() - start) * 1000)
        status = "PASS" if ok else "FAIL"
        RESULTS.append((status, name, ms))
        log.info("%s: %s (%dms)", status, name, ms)
    except Exception as e:
        ms = round((time.time() - start) * 1000)
        RESULTS.append(("ERROR", name, ms))
        log.error("ERROR: %s (%dms): %s", name, ms, e)


def main():
    """Run all connection tests."""
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not api_key or not secret_key:
        log.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY")
        sys.exit(1)
    auth = BingXAuth(api_key, secret_key, demo_mode=True)

    def t_auth():
        """Test auth signing."""
        req = auth.build_signed_request(
            "GET", "/test", {"symbol": "BTC-USDT"})
        return ("signature=" in req["url"]
                and "timestamp=" in req["url"])
    test_step("Auth signing", t_auth)

    def t_klines():
        """Fetch klines."""
        url = auth.build_public_url(
            "/openApi/swap/v3/quote/klines",
            {"symbol": "BTC-USDT", "interval": "5m",
             "limit": "5"})
        resp = requests.get(url, timeout=10)
        d = resp.json()
        return d.get("code", -1) == 0 and len(d.get("data", [])) > 0
    test_step("Fetch klines (v3)", t_klines)

    def t_price():
        """Fetch mark price."""
        url = auth.build_public_url(
            "/openApi/swap/v2/quote/price",
            {"symbol": "BTC-USDT"})
        resp = requests.get(url, timeout=10)
        return resp.json().get("code", -1) == 0
    test_step("Fetch mark price", t_price)

    def t_contracts():
        """Fetch contracts."""
        url = auth.build_public_url(
            "/openApi/swap/v2/quote/contracts")
        resp = requests.get(url, timeout=10)
        d = resp.json()
        if d.get("code", -1) != 0:
            return False
        for c in d.get("data", []):
            if c.get("symbol") == "BTC-USDT":
                log.info("  BTC-USDT step: %s",
                         c.get("tradeMinQuantity"))
                return True
        return False
    test_step("Fetch contracts", t_contracts)

    def t_positions():
        """Check positions (signed)."""
        req = auth.build_signed_request(
            "GET", "/openApi/swap/v2/user/positions")
        resp = requests.get(
            req["url"], headers=req["headers"], timeout=10)
        return resp.json().get("code", -1) == 0
    test_step("Check positions", t_positions)

    def t_telegram():
        """Send test Telegram message."""
        if not tg_token:
            log.warning("No TELEGRAM_BOT_TOKEN — skip")
            return True
        n = Notifier(tg_token, tg_chat)
        return n.send("BingX connector test — connection OK")
    test_step("Telegram send", t_telegram)

    log.info("=" * 50)
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    log.info("Results: %d/%d passed", passed, len(RESULTS))
    for status, name, ms in RESULTS:
        log.info("  %s  %s  (%dms)", status, name, ms)
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
