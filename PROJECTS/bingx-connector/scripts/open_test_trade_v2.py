"""
Open a manual test trade on BingX VST demo.
Usage: python scripts/open_test_trade_v2.py --side LONG --margin 10
       python scripts/open_test_trade_v2.py --side SHORT --margin 10
       python scripts/open_test_trade_v2.py --close LONG
       python scripts/open_test_trade_v2.py --close SHORT
"""
import os
import sys
import json
import math
import time
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bingx_auth import BingXAuth

COIN = "RIVER-USDT"
LEVERAGE = 10
SL_PCT = 0.10
TP_PCT = 0.10


def log(msg):
    """Print timestamped log line."""
    ts = time.strftime("%H:%M:%S")
    print("[" + ts + "] " + msg)


def main():
    """Open or close a test trade on BingX VST demo."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=["LONG", "SHORT"], default="LONG")
    parser.add_argument("--margin", type=float, default=10.0)
    parser.add_argument("--coin", default=COIN)
    parser.add_argument("--close", choices=["LONG", "SHORT"],
                        help="Close existing position instead of opening")
    args = parser.parse_args()

    log("=" * 50)
    if args.close:
        log("MODE: CLOSE " + args.close + " position")
    else:
        log("MODE: OPEN " + args.side + " | margin=$"
            + str(args.margin) + " | " + str(LEVERAGE) + "x leverage")
    log("Coin: " + args.coin)
    log("=" * 50)

    # --- Load .env ---
    log("Loading .env from " + str(ROOT / ".env"))
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    if not api_key or not secret_key:
        log("FATAL: Missing BINGX_API_KEY or BINGX_SECRET_KEY in .env")
        sys.exit(1)
    log("API key loaded: " + api_key[:8] + "..." + api_key[-4:])

    # --- Auth ---
    auth = BingXAuth(api_key, secret_key, demo_mode=True)
    log("Connected to: " + auth.base_url + " (demo=True)")

    # --- Auth test ---
    log("Testing auth (signed GET /positions)...")
    req_test = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_test = requests.get(
        req_test["url"], headers=req_test["headers"], timeout=10).json()
    if resp_test.get("code", -1) != 0:
        log("FATAL: Auth failed. code=" + str(resp_test.get("code"))
            + " msg=" + str(resp_test.get("msg")))
        sys.exit(1)
    positions = [p for p in resp_test.get("data", [])
                 if float(p.get("positionAmt", 0)) != 0]
    log("Auth OK. " + str(len(positions)) + " open positions on account.")

    coin = args.coin

    # --- Fetch mark price ---
    log("Fetching mark price for " + coin + "...")
    url_p = auth.build_public_url("/openApi/swap/v2/quote/price",
                                  {"symbol": coin})
    resp_p = requests.get(url_p, timeout=10).json()
    if resp_p.get("code", -1) != 0:
        log("FATAL: Price fetch failed. code=" + str(resp_p.get("code")))
        sys.exit(1)
    mark = float(resp_p["data"]["price"])
    log("Mark price: $" + str(mark))

    # --- Fetch step size ---
    log("Fetching contract specs...")
    url_c = auth.build_public_url("/openApi/swap/v2/quote/contracts")
    resp_c = requests.get(url_c, timeout=10).json()
    step = 1.0
    for c in resp_c.get("data", []):
        if c.get("symbol") == coin:
            step = float(c.get("tradeMinQuantity", c.get("stepSize", 1)))
            break
    log("Step size: " + str(step))

    # ===================== CLOSE MODE =====================
    if args.close:
        log("-" * 40)
        log("Finding " + args.close + " position for " + coin + "...")
        qty = 0.0
        entry_price = 0.0
        pnl = 0.0
        for pos in resp_test.get("data", []):
            if (pos.get("symbol") == coin
                    and pos.get("positionSide") == args.close
                    and float(pos.get("positionAmt", 0)) != 0):
                qty = abs(float(pos["positionAmt"]))
                entry_price = float(pos.get("avgPrice", 0))
                pnl = float(pos.get("unrealizedProfit", 0))
                break
        if qty == 0:
            log("No " + args.close + " position found for " + coin)
            return
        log("Found: qty=" + str(qty) + " entry=$" + str(entry_price)
            + " unrealizedPnL=$" + str(pnl))

        log("Cancelling pending orders (SL/TP)...")
        req_cancel = auth.build_signed_request(
            "DELETE", "/openApi/swap/v2/trade/allOpenOrders",
            {"symbol": coin})
        resp_cancel = requests.delete(
            req_cancel["url"], headers=req_cancel["headers"],
            timeout=10).json()
        log("Cancel orders: code=" + str(resp_cancel.get("code")))

        side_close = "SELL" if args.close == "LONG" else "BUY"
        log("Closing " + args.close + ": " + side_close + " MARKET qty="
            + str(qty) + "...")
        close_params = {
            "symbol": coin, "side": side_close,
            "positionSide": args.close, "type": "MARKET",
            "quantity": str(qty)}
        req_cl = auth.build_signed_request(
            "POST", "/openApi/swap/v2/trade/order", close_params)
        resp_cl = requests.post(
            req_cl["url"], headers=req_cl["headers"], timeout=10).json()
        code = resp_cl.get("code", -1)
        if code != 0:
            log("FAILED: code=" + str(code) + " msg="
                + str(resp_cl.get("msg")))
            return
        log("CLOSED " + args.close + " " + coin + " (code=0)")
        log("  entry: $" + str(entry_price) + " | exit: ~$" + str(mark))
        log("  unrealizedPnL at close: $" + str(pnl))
        return

    # ===================== OPEN MODE =====================
    log("-" * 40)
    notional = args.margin * LEVERAGE
    raw_qty = notional / mark
    quantity = math.floor(raw_qty / step) * step
    if quantity <= 0:
        log("FATAL: Qty too small. raw=" + str(raw_qty) + " step="
            + str(step) + " notional=$" + str(notional))
        return

    side = "BUY" if args.side == "LONG" else "SELL"
    if args.side == "LONG":
        sl_price = round(mark * (1 - SL_PCT), 8)
        tp_price = round(mark * (1 + TP_PCT), 8)
    else:
        sl_price = round(mark * (1 + SL_PCT), 8)
        tp_price = round(mark * (1 - TP_PCT), 8)

    log("Order plan:")
    log("  " + side + " " + args.side + " " + coin)
    log("  qty=" + str(quantity) + " @ market ($" + str(mark) + ")")
    log("  notional=$" + str(notional) + " (margin=$" + str(args.margin)
        + " x " + str(LEVERAGE) + ")")
    log("  SL=$" + str(sl_price) + " (" + str(int(SL_PCT * 100)) + "% from entry)")
    log("  TP=$" + str(tp_price) + " (" + str(int(TP_PCT * 100)) + "% from entry)")

    log("Placing order...")
    order_params = {
        "symbol": coin,
        "side": side,
        "positionSide": args.side,
        "type": "MARKET",
        "quantity": str(quantity),
        "stopLoss": json.dumps({
            "type": "STOP_MARKET",
            "stopPrice": sl_price,
            "workingType": "MARK_PRICE",
        }, separators=(',', ':')),
        "takeProfit": json.dumps({
            "type": "TAKE_PROFIT_MARKET",
            "stopPrice": tp_price,
            "workingType": "MARK_PRICE",
        }, separators=(',', ':')),
    }

    req = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", order_params)
    resp = requests.post(
        req["url"], headers=req["headers"], timeout=10).json()

    code = resp.get("code", -1)
    if code != 0:
        log("FAILED: code=" + str(code) + " msg=" + str(resp.get("msg")))
        log("  Full response: " + json.dumps(resp))
        return

    oid = resp.get("data", {}).get("order", {}).get("orderId", "?")
    log("ORDER FILLED")
    log("  orderId: " + str(oid))

    # --- Verify position appeared ---
    log("Verifying position...")
    time.sleep(1)
    req_v = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_v = requests.get(
        req_v["url"], headers=req_v["headers"], timeout=10).json()
    for pos in resp_v.get("data", []):
        if (pos.get("symbol") == coin
                and pos.get("positionSide") == args.side
                and float(pos.get("positionAmt", 0)) != 0):
            log("Position confirmed:")
            log("  qty=" + str(pos.get("positionAmt"))
                + " avgPrice=$" + str(pos.get("avgPrice"))
                + " liq=$" + str(pos.get("liquidationPrice")))
            log("  unrealizedPnL=$" + str(pos.get("unrealizedProfit")))
            break
    else:
        log("WARNING: Position not found in query (may need more time)")

    # --- Verify SL/TP orders ---
    log("Checking SL/TP orders...")
    req_o = auth.build_signed_request(
        "GET", "/openApi/swap/v2/trade/openOrders", {"symbol": coin})
    resp_o = requests.get(
        req_o["url"], headers=req_o["headers"], timeout=10).json()
    orders = resp_o.get("data", {}).get("orders", [])
    for o in orders:
        log("  " + o.get("type", "?") + " stopPrice=$"
            + str(o.get("stopPrice", "?")) + " status="
            + o.get("status", "?") + " id=" + str(o.get("orderId", "?")))

    log("=" * 50)
    log("DONE. Trade is live on VST demo.")
    log("Close with: python scripts/open_test_trade_v2.py --close "
        + args.side)


if __name__ == "__main__":
    main()
