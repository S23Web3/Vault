"""
Open a manual test trade on BingX VST demo.
Usage: python scripts/open_test_trade.py --side LONG --margin 10
       python scripts/open_test_trade.py --side SHORT --margin 10
       python scripts/open_test_trade.py --close LONG
       python scripts/open_test_trade.py --close SHORT
"""
import os
import sys
import json
import math
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bingx_auth import BingXAuth

COIN = "RIVER-USDT"
LEVERAGE = 10
SL_PCT = 0.10    # 10% from entry
TP_PCT = 0.10    # 10% from entry


def main():
    """Open or close a test trade on BingX VST demo."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=["LONG", "SHORT"], default="LONG")
    parser.add_argument("--margin", type=float, default=10.0)
    parser.add_argument("--coin", default=COIN)
    parser.add_argument("--close", choices=["LONG", "SHORT"],
                        help="Close existing position instead of opening")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", ""),
        os.getenv("BINGX_SECRET_KEY", ""),
        demo_mode=True)

    coin = args.coin

    # Fetch mark price
    url_p = auth.build_public_url("/openApi/swap/v2/quote/price",
                                  {"symbol": coin})
    resp_p = requests.get(url_p, timeout=10).json()
    mark = float(resp_p["data"]["price"])
    print("Mark price: " + str(mark))

    # Fetch step size
    url_c = auth.build_public_url("/openApi/swap/v2/quote/contracts")
    resp_c = requests.get(url_c, timeout=10).json()
    step = 1.0
    for c in resp_c.get("data", []):
        if c.get("symbol") == coin:
            step = float(c.get("tradeMinQuantity", c.get("stepSize", 1)))
            break
    print("Step size: " + str(step))

    if args.close:
        # Close position
        side_close = "SELL" if args.close == "LONG" else "BUY"
        # Find current position qty
        req_pos = auth.build_signed_request(
            "GET", "/openApi/swap/v2/user/positions")
        resp_pos = requests.get(
            req_pos["url"], headers=req_pos["headers"], timeout=10).json()
        qty = 0.0
        for pos in resp_pos.get("data", []):
            if (pos.get("symbol") == coin
                    and pos.get("positionSide") == args.close
                    and float(pos.get("positionAmt", 0)) != 0):
                qty = abs(float(pos["positionAmt"]))
                break
        if qty == 0:
            print("No " + args.close + " position found for " + coin)
            return
        # Cancel pending orders
        req_cancel = auth.build_signed_request(
            "DELETE", "/openApi/swap/v2/trade/allOpenOrders",
            {"symbol": coin})
        requests.delete(
            req_cancel["url"], headers=req_cancel["headers"], timeout=10)
        # Close
        close_params = {
            "symbol": coin, "side": side_close,
            "positionSide": args.close, "type": "MARKET",
            "quantity": str(qty)}
        req_cl = auth.build_signed_request(
            "POST", "/openApi/swap/v2/trade/order", close_params)
        resp_cl = requests.post(
            req_cl["url"], headers=req_cl["headers"], timeout=10).json()
        print("Close " + args.close + ": code=" + str(resp_cl.get("code"))
              + " msg=" + str(resp_cl.get("msg")))
        return

    # Open position
    notional = args.margin * LEVERAGE
    raw_qty = notional / mark
    quantity = math.floor(raw_qty / step) * step
    if quantity <= 0:
        print("Qty too small: raw=" + str(raw_qty) + " step=" + str(step))
        return

    side = "BUY" if args.side == "LONG" else "SELL"
    sl_price = round(mark * (1 - SL_PCT), 8) if args.side == "LONG" else round(mark * (1 + SL_PCT), 8)
    tp_price = round(mark * (1 + TP_PCT), 8) if args.side == "LONG" else round(mark * (1 - TP_PCT), 8)

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
    resp = requests.post(req["url"], headers=req["headers"], timeout=10).json()

    code = resp.get("code", -1)
    if code != 0:
        print("FAILED: code=" + str(code) + " msg=" + str(resp.get("msg")))
        return

    oid = resp.get("data", {}).get("order", {}).get("orderId", "?")
    print("OPENED " + args.side + " " + coin)
    print("  orderId: " + str(oid))
    print("  qty: " + str(quantity))
    print("  mark: " + str(mark))
    print("  notional: $" + str(notional))
    print("  margin: $" + str(args.margin))
    print("  leverage: " + str(LEVERAGE) + "x")
    print("  SL: " + str(sl_price))
    print("  TP: " + str(tp_price))


if __name__ == "__main__":
    main()
