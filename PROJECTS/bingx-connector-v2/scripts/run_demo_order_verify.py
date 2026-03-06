"""
Demo order verification: test which order types BingX VST actually fills.
Places test orders on VST (paper money) and checks fill status.
Run: python scripts/run_demo_order_verify.py
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import date

import requests
import yaml
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "logs" / ("demo_order_verify_" + date.today().strftime("%Y-%m-%d") + ".md")

VST_BASE = "https://open-api-vst.bingx.com"
TEST_SYMBOL = "BTC-USDT"    # High-liquidity coin for reliable fills
TEST_QTY    = "0.001"       # Minimum size

# Paths
ORDER_PATH      = "/openApi/swap/v2/trade/order"
QUERY_PATH      = "/openApi/swap/v2/trade/order"
POSITIONS_PATH  = "/openApi/swap/v2/user/positions"
ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"

import hashlib
import hmac as hmac_lib


def sign(params: dict, secret: str) -> str:
    """HMAC-SHA256 sign params alphabetically."""
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    return hmac_lib.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()


def build_url(path: str, params: dict, api_key: str, secret: str) -> tuple[str, dict]:
    """Build signed URL and headers."""
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"
    sig = sign(params, secret)
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    url = VST_BASE + path + "?" + qs + "&signature=" + sig
    headers = {"X-BX-APIKEY": api_key}
    return url, headers


def post_order(params: dict, api_key: str, secret: str) -> dict:
    """Place an order on VST."""
    url, headers = build_url(ORDER_PATH, params, api_key, secret)
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {"code": -1, "msg": str(e)}


def get_mark_price(symbol: str) -> float:
    """Fetch mark price from VST (public endpoint)."""
    try:
        url = VST_BASE + "/openApi/swap/v2/quote/price?symbol=" + symbol
        resp = requests.get(url, timeout=10)
        data = resp.json()
        items = data.get("data", {})
        if isinstance(items, list):
            for item in items:
                if item.get("symbol") == symbol:
                    return float(item.get("price", 0))
        elif isinstance(items, dict):
            return float(items.get("price", 0))
    except Exception as e:
        log.error("Mark price fetch failed: %s", e)
    return 0.0


def close_all_positions(symbol: str, api_key: str, secret: str) -> None:
    """Close any open VST positions for the test symbol."""
    url, headers = build_url(POSITIONS_PATH, {"symbol": symbol}, api_key, secret)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        positions = data.get("data", [])
        for pos in positions:
            qty = pos.get("positionAmt", "0")
            side = pos.get("positionSide", "LONG")
            if float(qty) == 0:
                continue
            close_side = "SELL" if side == "LONG" else "BUY"
            close_params = {
                "symbol": symbol,
                "side": close_side,
                "positionSide": side,
                "type": "MARKET",
                "quantity": str(abs(float(qty))),
            }
            result = post_order(close_params, api_key, secret)
            log.info("Cleanup close %s %s: code=%s", symbol, side, result.get("code"))
    except Exception as e:
        log.error("Cleanup failed: %s", e)


def main() -> None:
    """Run order type verification tests."""
    load_dotenv(ROOT / ".env")
    api_key    = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    if not api_key or not secret_key:
        log.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY in .env")
        sys.exit(1)

    log.info("Using VST (demo) base: %s", VST_BASE)
    log.info("Test symbol: %s", TEST_SYMBOL)

    mark = get_mark_price(TEST_SYMBOL)
    if mark == 0.0:
        log.error("Cannot fetch mark price — check API connectivity")
        sys.exit(1)
    log.info("Mark price: %.2f", mark)

    # Clean up any previous test positions
    close_all_positions(TEST_SYMBOL, api_key, secret_key)
    time.sleep(2)

    results = []

    def run_test(test_name: str, params: dict) -> dict:
        """Place an order, wait, check status, return result dict."""
        log.info("TEST: %s", test_name)
        resp = post_order(params.copy(), api_key, secret_key)
        code = resp.get("code", -1)
        msg  = resp.get("msg", "")
        order_data = resp.get("data", {}) or {}
        order_id = str(order_data.get("orderId") or order_data.get("order", {}).get("orderId", ""))
        result = {
            "test": test_name,
            "code": code,
            "msg": msg,
            "order_id": order_id,
            "accepted": code == 0,
            "filled": False,
            "status": "",
        }
        log.info("  Placed: code=%s msg=%s order_id=%s", code, msg, order_id)
        if code == 0 and order_id:
            time.sleep(5)
            q_params = {"symbol": params.get("symbol", TEST_SYMBOL), "orderId": order_id}
            q_url, q_headers = build_url(QUERY_PATH, q_params, api_key, secret_key)
            try:
                q_resp = requests.get(q_url, headers=q_headers, timeout=10)
                q_data = q_resp.json()
                order_info = q_data.get("data", {}) or {}
                status = order_info.get("status", "UNKNOWN")
                result["status"] = status
                result["filled"] = status in ("FILLED", "PARTIALLY_FILLED")
                log.info("  Status after 5s: %s", status)
            except Exception as e:
                log.error("  Query failed: %s", e)
        results.append(result)
        time.sleep(2)
        return result

    sl_mark  = round(mark * 0.98, 2)   # 2% below mark (SL for LONG)
    tp_mark  = round(mark * 1.02, 2)   # 2% above mark (TP for LONG)

    # Test 1: MARKET entry LONG
    r = run_test("MARKET_LONG_ENTRY", {
        "symbol": TEST_SYMBOL,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": TEST_QTY,
    })

    if r["accepted"]:
        time.sleep(3)

        # Test 2: STOP_MARKET with MARK_PRICE
        run_test("STOP_MARKET_MARK_PRICE_SL", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "STOP_MARKET",
            "quantity": TEST_QTY,
            "stopPrice": str(sl_mark),
            "workingType": "MARK_PRICE",
        })

        # Test 3: STOP_MARKET with CONTRACT_PRICE
        run_test("STOP_MARKET_CONTRACT_PRICE_SL", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "STOP_MARKET",
            "quantity": TEST_QTY,
            "stopPrice": str(sl_mark),
            "workingType": "CONTRACT_PRICE",
        })

        # Test 4: TAKE_PROFIT_MARKET
        run_test("TAKE_PROFIT_MARKET", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "TAKE_PROFIT_MARKET",
            "quantity": TEST_QTY,
            "stopPrice": str(tp_mark),
            "workingType": "MARK_PRICE",
        })

        # Test 5: Market close (no reduceOnly)
        run_test("MARKET_CLOSE_NO_REDUCE_ONLY", {
            "symbol": TEST_SYMBOL,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "MARKET",
            "quantity": TEST_QTY,
        })

    # Write report
    lines = [
        "# Demo Order Verification — " + date.today().strftime("%Y-%m-%d"),
        "",
        "VST Base: " + VST_BASE,
        "Test Symbol: " + TEST_SYMBOL,
        "Mark Price at Test Time: " + str(mark),
        "",
        "| Test | Accepted | Status | Code | Notes |",
        "|------|----------|--------|------|-------|",
    ]
    for r in results:
        acc  = "YES" if r["accepted"] else "NO"
        fill = r["status"] if r["status"] else ("FILLED" if r["filled"] else "—")
        lines.append("| " + r["test"] + " | " + acc + " | " + fill +
                     " | " + str(r["code"]) + " | " + r["msg"][:80] + " |")

    lines += [
        "",
        "## Interpretation",
        "",
        "- STOP_MARKET_MARK_PRICE_SL accepted+filled = SL working correctly in VST",
        "- STOP_MARKET_MARK_PRICE_SL rejected = VST requires CONTRACT_PRICE workingType",
        "- MARKET_CLOSE_NO_REDUCE_ONLY filled = BUG-1 fix is correct (no reduceOnly needed)",
        "- Any code 109400 = reduceOnly still present somewhere",
    ]

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written: " + str(OUT_FILE))

    print("\n=== DEMO VERIFICATION RESULTS ===")
    for r in results:
        status = "PASS" if r["accepted"] else "FAIL"
        print(status + "  " + r["test"] + "  code=" + str(r["code"]) +
              "  status=" + r.get("status", "—"))


if __name__ == "__main__":
    main()
