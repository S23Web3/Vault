"""
Test BingX TRAILING_STOP_MARKET with tight priceRate (0.3%).
Opens position on DOGE-USDT (not in bot watchlist), places trailing,
checks acceptance, cancels, closes. Total cost: ~$0.08 commission.
"""
import sys
import os
import time
import json
import requests
import logging

# --- Setup path so we can import bot modules ---
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJ)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJ, ".env"))

from bingx_auth import BingXAuth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# --- Config ---
SYMBOL = "DOGE-USDT"
MARGIN_USD = 5.0
LEVERAGE = 10
DIRECTION = "LONG"

# These are the values we want to test
TEST_RATES = [0.003, 0.005, 0.01, 0.02]

ORDER_PATH = "/openApi/swap/v2/trade/order"
OPEN_ORDERS_PATH = "/openApi/swap/v2/trade/openOrders"
POSITIONS_PATH = "/openApi/swap/v2/user/positions"
LEVERAGE_PATH = "/openApi/swap/v2/trade/leverage"
MARGIN_PATH = "/openApi/swap/v2/trade/marginType"
PRICE_PATH = "/openApi/swap/v2/quote/price"

# -------------------------------------------------------------------

def get_auth():
    """Build BingXAuth from env vars."""
    api_key = os.getenv("BINGX_API_KEY")
    secret = os.getenv("BINGX_SECRET_KEY")
    demo = os.getenv("BINGX_DEMO_MODE", "false").lower() == "true"
    if not api_key or not secret:
        log.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY in .env")
        sys.exit(1)
    return BingXAuth(api_key, secret, demo_mode=demo)


def api_get(auth, path, params=None):
    """Signed GET request."""
    req = auth.build_signed_request("GET", path, params or {})
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    return resp.json()


def api_post(auth, path, params):
    """Signed POST request."""
    req = auth.build_signed_request("POST", path, params)
    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    return resp.json()


def api_delete(auth, path, params):
    """Signed DELETE request."""
    req = auth.build_signed_request("DELETE", path, params)
    resp = requests.delete(req["url"], headers=req["headers"], timeout=10)
    return resp.json()


def get_mark_price(auth, symbol):
    """Fetch current mark price."""
    url = auth.base_url + PRICE_PATH + "?symbol=" + symbol
    resp = requests.get(url, timeout=10)
    data = resp.json()
    pd = data.get("data", {})
    if isinstance(pd, dict):
        return float(pd.get("price", 0))
    if isinstance(pd, list) and pd:
        return float(pd[0].get("price", 0))
    return 0.0


def set_leverage(auth, symbol):
    """Set leverage for both sides."""
    for side in ("LONG", "SHORT"):
        data = api_post(auth, LEVERAGE_PATH, {
            "symbol": symbol, "side": side, "leverage": str(LEVERAGE)
        })
        log.info("Leverage %s %s: code=%s", symbol, side, data.get("code"))


def set_margin_mode(auth, symbol):
    """Set margin mode to ISOLATED."""
    data = api_post(auth, MARGIN_PATH, {
        "symbol": symbol, "marginType": "ISOLATED"
    })
    log.info("Margin %s: code=%s msg=%s", symbol, data.get("code"), data.get("msg"))


def open_position(auth, symbol, direction, quantity):
    """Open a market position. Returns order data or None."""
    side = "BUY" if direction == "LONG" else "SELL"
    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": direction,
        "type": "MARKET",
        "quantity": str(quantity),
    }
    data = api_post(auth, ORDER_PATH, params)
    if data.get("code", 0) == 0:
        log.info("Position opened: %s %s qty=%s", symbol, direction, quantity)
        return data.get("data", {})
    log.error("Open position failed: code=%s msg=%s", data.get("code"), data.get("msg"))
    return None


def place_trailing(auth, symbol, direction, quantity, activation_price, price_rate):
    """Place TRAILING_STOP_MARKET. Returns (success, order_id, error_msg)."""
    close_side = "SELL" if direction == "LONG" else "BUY"
    params = {
        "symbol": symbol,
        "side": close_side,
        "positionSide": direction,
        "type": "TRAILING_STOP_MARKET",
        "quantity": str(quantity),
        "priceRate": str(price_rate),
        "activationPrice": str(round(activation_price, 8)),
        "workingType": "MARK_PRICE",
    }
    data = api_post(auth, ORDER_PATH, params)
    code = data.get("code", -1)
    if code == 0:
        d = data.get("data", {})
        oid = str(d.get("orderId") or d.get("order", {}).get("orderId", "?"))
        return True, oid, None
    return False, None, "code=" + str(code) + " msg=" + str(data.get("msg"))


def cancel_order(auth, symbol, order_id):
    """Cancel an order by ID."""
    data = api_delete(auth, ORDER_PATH, {
        "symbol": symbol, "orderId": str(order_id)
    })
    return data.get("code", -1) == 0


def close_position(auth, symbol, direction, quantity):
    """Market close the test position."""
    close_side = "SELL" if direction == "LONG" else "BUY"
    params = {
        "symbol": symbol,
        "side": close_side,
        "positionSide": direction,
        "type": "MARKET",
        "quantity": str(quantity),
    }
    data = api_post(auth, ORDER_PATH, params)
    if data.get("code", 0) == 0:
        log.info("Position closed: %s %s", symbol, direction)
        return True
    log.error("Close failed: code=%s msg=%s", data.get("code"), data.get("msg"))
    return False


def main():
    """Run trailing stop acceptance test."""
    auth = get_auth()

    print("=" * 60)
    print("BingX TRAILING_STOP_MARKET priceRate Acceptance Test")
    print("Symbol:", SYMBOL, " Margin:", MARGIN_USD, " Leverage:", LEVERAGE)
    print("Rates to test:", TEST_RATES)
    print("=" * 60)

    # Step 1: Get mark price
    mark = get_mark_price(auth, SYMBOL)
    if mark <= 0:
        log.error("Cannot fetch mark price for %s", SYMBOL)
        return
    log.info("Mark price: %s = %.8f", SYMBOL, mark)

    # Step 2: Calculate quantity
    notional = MARGIN_USD * LEVERAGE
    quantity = round(notional / mark, 0)
    if quantity <= 0:
        quantity = 1.0
    log.info("Notional: $%.2f  Quantity: %.0f", notional, quantity)

    # Step 3: Setup leverage + margin
    set_leverage(auth, SYMBOL)
    set_margin_mode(auth, SYMBOL)
    time.sleep(1)

    # Step 4: Open position
    result = open_position(auth, SYMBOL, DIRECTION, quantity)
    if result is None:
        log.error("ABORT: could not open test position")
        return

    time.sleep(2)  # Wait for position to settle

    # Step 5: Get updated mark for activation price
    mark = get_mark_price(auth, SYMBOL)
    activation_price = mark * 1.008  # +0.8% from current (same as ttp_act)

    # Step 6: Test each priceRate
    results = {}
    for rate in TEST_RATES:
        log.info("--- Testing priceRate=%.4f (%.2f%%) ---", rate, rate * 100)
        ok, oid, err = place_trailing(
            auth, SYMBOL, DIRECTION, quantity, activation_price, rate
        )
        if ok:
            log.info("ACCEPTED: priceRate=%.4f orderId=%s", rate, oid)
            results[rate] = "ACCEPTED"
            # Cancel immediately
            cancelled = cancel_order(auth, SYMBOL, oid)
            log.info("Cancelled: %s", cancelled)
        else:
            log.warning("REJECTED: priceRate=%.4f error=%s", rate, err)
            results[rate] = "REJECTED: " + str(err)
        time.sleep(1)

    # Step 7: Close test position
    time.sleep(1)
    close_position(auth, SYMBOL, DIRECTION, quantity)

    # Step 8: Report
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    for rate, status in results.items():
        pct = rate * 100
        print("  priceRate=%.4f (%5.2f%%): %s" % (rate, pct, status))
    print("=" * 60)

    # Find minimum accepted
    accepted = [r for r, s in results.items() if s == "ACCEPTED"]
    if accepted:
        print("MINIMUM ACCEPTED: priceRate=%.4f (%.2f%%)" % (min(accepted), min(accepted) * 100))
    else:
        print("ALL REJECTED -- native trailing may not work at these rates")


if __name__ == "__main__":
    main()
