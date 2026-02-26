"""
Debug script for BingX connector troubleshooting.
Run: python scripts/debug_connector.py --test-auth
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


def cmd_test_auth():
    """Test auth signing."""
    from bingx_auth import BingXAuth
    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", "demo_key"),
        os.getenv("BINGX_SECRET_KEY", "demo_secret"),
        demo_mode=True)
    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions",
        {"symbol": "BTC-USDT"})
    log.info("URL: %s", req["url"])
    log.info("Headers: %s", req["headers"])
    pub = auth.build_public_url(
        "/openApi/swap/v3/quote/klines",
        {"symbol": "BTC-USDT", "interval": "5m"})
    log.info("Public URL: %s", pub)


def cmd_test_klines(symbol):
    """Fetch klines for one symbol."""
    import requests
    from bingx_auth import BingXAuth
    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", "demo_key"),
        os.getenv("BINGX_SECRET_KEY", "demo_secret"),
        demo_mode=True)
    url = auth.build_public_url(
        "/openApi/swap/v3/quote/klines",
        {"symbol": symbol, "interval": "5m", "limit": "5"})
    log.info("GET %s", url)
    resp = requests.get(url, timeout=10)
    d = resp.json()
    log.info("Code: %s", d.get("code"))
    log.info("Count: %d", len(d.get("data", [])))
    for row in d.get("data", [])[:3]:
        log.info("  %s", json.dumps(row, indent=2)[:200])


def cmd_test_price(symbol):
    """Fetch mark price for one symbol."""
    import requests
    from bingx_auth import BingXAuth
    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", "demo_key"),
        os.getenv("BINGX_SECRET_KEY", "demo_secret"),
        demo_mode=True)
    url = auth.build_public_url(
        "/openApi/swap/v2/quote/price", {"symbol": symbol})
    log.info("GET %s", url)
    resp = requests.get(url, timeout=10)
    log.info("Response: %s",
             json.dumps(resp.json(), indent=2)[:500])


def cmd_test_state():
    """Load and print state.json."""
    sp = ROOT / "state.json"
    if sp.exists():
        d = json.loads(sp.read_text(encoding="utf-8"))
        log.info("State:\n%s", json.dumps(d, indent=2))
    else:
        log.info("No state.json found")


def cmd_test_signal():
    """Run mock strategy with synthetic data."""
    import pandas as pd
    import numpy as np
    from plugins.mock_strategy import MockStrategy
    rng = np.random.default_rng(42)
    n = 100
    close = 0.01 + np.cumsum(rng.normal(0, 0.0001, n))
    close = np.clip(close, 0.005, 0.02)
    df = pd.DataFrame({
        "open": close * rng.uniform(0.999, 1.001, n),
        "high": close * rng.uniform(1.000, 1.005, n),
        "low": close * rng.uniform(0.995, 1.000, n),
        "close": close,
        "volume": rng.integers(1e6, 1e7, n).astype(float),
        "time": range(17e11, 17e11 + n * 300000, 300000),
    })
    strat = MockStrategy({"signal_probability": 1.0})
    sig = strat.get_signal(df)
    if sig:
        log.info("Signal: %s grade=%s price=%.6f sl=%.6f",
                 sig.direction, sig.grade,
                 sig.entry_price, sig.sl_price)
    else:
        log.info("No signal")


def cmd_test_risk():
    """Run risk gate with synthetic state."""
    from risk_gate import RiskGate
    from plugins.mock_strategy import Signal
    gate = RiskGate({
        "max_positions": 3, "max_daily_trades": 20,
        "daily_loss_limit_usd": 75.0, "min_atr_ratio": 0.003})
    state = {"open_positions": {}, "daily_pnl": 0.0,
             "daily_trades": 0, "halt_flag": False}
    sig = Signal(
        direction="LONG", grade="MOCK", entry_price=0.01,
        sl_price=0.009, tp_price=0.013, atr=0.0001, bar_ts=0)
    ok, reason = gate.evaluate(sig, "TEST-USDT", state, ["MOCK"])
    log.info("Result: approved=%s reason=%s", ok, reason)


def cmd_test_telegram():
    """Send test Telegram message."""
    from notifier import Notifier
    load_dotenv(ROOT / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token:
        log.error("No TELEGRAM_BOT_TOKEN in .env")
        return
    n = Notifier(token, chat)
    result = n.send("Debug test from BingX connector")
    log.info("Result: %s", result)


def main():
    """Parse args and run debug command."""
    parser = argparse.ArgumentParser(
        description="BingX connector debugger")
    parser.add_argument("--test-auth", action="store_true")
    parser.add_argument("--test-klines", type=str, metavar="SYM")
    parser.add_argument("--test-price", type=str, metavar="SYM")
    parser.add_argument("--test-state", action="store_true")
    parser.add_argument("--test-signal", action="store_true")
    parser.add_argument("--test-risk", action="store_true")
    parser.add_argument("--test-telegram", action="store_true")
    args = parser.parse_args()
    if args.test_auth:
        cmd_test_auth()
    elif args.test_klines:
        cmd_test_klines(args.test_klines)
    elif args.test_price:
        cmd_test_price(args.test_price)
    elif args.test_state:
        cmd_test_state()
    elif args.test_signal:
        cmd_test_signal()
    elif args.test_risk:
        cmd_test_risk()
    elif args.test_telegram:
        cmd_test_telegram()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
