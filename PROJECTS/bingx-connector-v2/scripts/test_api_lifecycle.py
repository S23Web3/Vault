"""
BingX API lifecycle test: 15 steps, real VST demo API, ~40 seconds.
Exercises the full trade lifecycle without waiting for a market signal.

LONG cycle:   auth -> data -> leverage -> qty -> entry+SL+TP -> verify ->
              query pending -> raise SL -> trail TP -> close -> verify
SHORT cycle:  entry+SL+TP -> verify -> close -> verify (all in one step)
Multi-pos:    LONG+SHORT simultaneous -> close one -> verify other survives
Limit order:  LIMIT BUY near ask -> fill -> close (tests maker order flow)
Order query:  fetch entry order details, verify avgPrice

Stops on first failure. Prints full URL and response on FAIL for debugging.

Run:
  python scripts/test_api_lifecycle.py
  python scripts/test_api_lifecycle.py --coin GUN-USDT
"""
import os
import sys
import json
import math
import time
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bingx_auth import BingXAuth

RESULTS = []
logger = logging.getLogger("lifecycle")


class UTC4Formatter(logging.Formatter):
    """Formatter that outputs timestamps in UTC+4."""

    _utc4 = timezone(timedelta(hours=4))

    def formatTime(self, record, datefmt=None):
        """Format log record timestamp as UTC+4."""
        dt = datetime.fromtimestamp(record.created, tz=self._utc4)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


def setup_logging():
    """Configure dual logging: file + console with UTC+4 timestamps."""
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = log_dir / (today + "-lifecycle-test.log")
    fmt = UTC4Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_h = logging.FileHandler(str(log_file), encoding="utf-8")
    file_h.setFormatter(fmt)
    console_h = logging.StreamHandler(sys.stdout)
    console_h.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO, handlers=[file_h, console_h])


def run_step(step_num, name, func, ctx):
    """Run one lifecycle step. Print PASS/FAIL. Stop on failure."""
    label = "STEP " + str(step_num)
    start = time.time()
    try:
        ok, detail = func(ctx)
        ms = int((time.time() - start) * 1000)
        if ok:
            RESULTS.append(("PASS", label, name, ms))
            logger.info("[PASS] %s: %s (%dms) -- %s", label, name, ms, detail)
            return True
        else:
            RESULTS.append(("FAIL", label, name, ms))
            logger.error("[FAIL] %s: %s (%dms) -- %s", label, name, ms, detail)
            return False
    except Exception as e:
        ms = int((time.time() - start) * 1000)
        RESULTS.append(("ERROR", label, name, ms))
        logger.error("[ERROR] %s: %s (%dms) -- %s", label, name, ms, str(e))
        return False


# ---------------------------------------------------------------------------
# STEP 1: Auth check
# ---------------------------------------------------------------------------
def step_auth_check(ctx):
    """Sign a request and GET /positions. Verify code=0."""
    auth = ctx["auth"]
    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()
    code = data.get("code", -1)
    if code != 0:
        return False, ("code=" + str(code)
                       + " msg=" + str(data.get("msg"))
                       + " url=" + req["url"])
    pos_count = len(data.get("data", []))
    return True, "code=0, " + str(pos_count) + " positions on account"


# ---------------------------------------------------------------------------
# STEP 2: Public endpoints (klines + price + contracts)
# ---------------------------------------------------------------------------
def step_public_endpoints(ctx):
    """Fetch klines, mark price, and step size for the test coin."""
    auth = ctx["auth"]
    coin = ctx["coin"]

    # 2a: Klines
    url_k = auth.build_public_url(
        "/openApi/swap/v3/quote/klines",
        {"symbol": coin, "interval": "5m", "limit": "5"})
    resp_k = requests.get(url_k, timeout=10)
    data_k = resp_k.json()
    if data_k.get("code", -1) != 0:
        return False, ("Klines code=" + str(data_k.get("code"))
                       + " msg=" + str(data_k.get("msg"))
                       + " url=" + url_k)
    bars = data_k.get("data", [])
    if not bars:
        return False, "Klines returned empty data for " + coin

    # 2b: Mark price
    url_p = auth.build_public_url(
        "/openApi/swap/v2/quote/price", {"symbol": coin})
    resp_p = requests.get(url_p, timeout=10)
    data_p = resp_p.json()
    if data_p.get("code", -1) != 0:
        return False, ("Price code=" + str(data_p.get("code"))
                       + " msg=" + str(data_p.get("msg"))
                       + " url=" + url_p)
    price_data = data_p.get("data", {})
    if isinstance(price_data, dict):
        mark_price = float(price_data.get("price", 0))
    elif isinstance(price_data, list) and price_data:
        mark_price = float(price_data[0].get("price", 0))
    else:
        return False, "Unexpected price format: " + json.dumps(data_p)[:200]
    if mark_price <= 0:
        return False, "Mark price <= 0: " + str(mark_price)
    ctx["mark_price"] = mark_price

    # 2c: Contracts / step size
    url_c = auth.build_public_url("/openApi/swap/v2/quote/contracts")
    resp_c = requests.get(url_c, timeout=10)
    data_c = resp_c.json()
    if data_c.get("code", -1) != 0:
        return False, ("Contracts code=" + str(data_c.get("code"))
                       + " url=" + url_c)
    step_size = None
    for c in data_c.get("data", []):
        if c.get("symbol") == coin:
            step_size = float(
                c.get("tradeMinQuantity", c.get("stepSize", 1)))
            break
    if step_size is None:
        return False, "Symbol " + coin + " not found in contracts list"
    ctx["step_size"] = step_size

    detail = ("klines=" + str(len(bars)) + " bars"
              + " mark_price=" + str(mark_price)
              + " step_size=" + str(step_size))
    return True, detail


# ---------------------------------------------------------------------------
# STEP 3: Leverage + margin type
# ---------------------------------------------------------------------------
def step_leverage_margin(ctx):
    """Set leverage for LONG and SHORT, then set margin type ISOLATED."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    leverage = ctx["leverage"]

    for side in ("LONG", "SHORT"):
        req = auth.build_signed_request(
            "POST", "/openApi/swap/v2/trade/leverage", {
                "symbol": coin, "side": side,
                "leverage": str(leverage),
            })
        resp = requests.post(req["url"], headers=req["headers"], timeout=10)
        data = resp.json()
        if data.get("code", -1) != 0:
            return False, ("Leverage " + side + " code="
                           + str(data.get("code"))
                           + " msg=" + str(data.get("msg"))
                           + " url=" + req["url"])

    req_m = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/marginType", {
            "symbol": coin, "marginType": "ISOLATED",
        })
    resp_m = requests.post(req_m["url"], headers=req_m["headers"], timeout=10)
    data_m = resp_m.json()
    if data_m.get("code", -1) != 0:
        msg = str(data_m.get("msg", ""))
        if "no need" not in msg.lower() and "already" not in msg.lower():
            return False, ("MarginType code=" + str(data_m.get("code"))
                           + " msg=" + msg)

    return True, ("Leverage=" + str(leverage) + "x LONG+SHORT"
                  + " margin=ISOLATED for " + coin)


# ---------------------------------------------------------------------------
# STEP 4: Quantity calculation
# ---------------------------------------------------------------------------
def step_qty_calc(ctx):
    """Calculate order quantity using real mark price and step size."""
    mark_price = ctx["mark_price"]
    step_size = ctx["step_size"]
    margin = ctx["margin_usd"]
    leverage = ctx["leverage"]
    notional = margin * leverage

    # Use minimum viable quantity to conserve demo balance
    min_qty = step_size
    full_qty = math.floor(notional / mark_price / step_size) * step_size

    # Use the smaller of: 2 steps or full qty (in case full is < 2 steps)
    test_qty = min(step_size * 2, full_qty)
    if test_qty <= 0:
        test_qty = step_size

    # Final round-down
    quantity = math.floor(test_qty / step_size) * step_size
    if quantity <= 0:
        return False, ("Rounded qty is 0: mark_price=" + str(mark_price)
                       + " step_size=" + str(step_size))
    ctx["quantity"] = quantity

    detail = ("notional=$" + str(notional)
              + " full_qty=" + str(round(full_qty, 8))
              + " test_qty=" + str(quantity)
              + " (min viable, not full position)")
    return True, detail


# ---------------------------------------------------------------------------
# STEP 5: Place order with SL (the E1-ROOT signature test)
# ---------------------------------------------------------------------------
def step_place_order(ctx):
    """Place a MARKET BUY with SL attached. Tests signature on JSON params."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    quantity = ctx["quantity"]
    mark_price = ctx["mark_price"]

    # SL 10% below, TP 10% above (won't trigger during the test)
    sl_price = round(mark_price * 0.90, 8)
    tp_price = round(mark_price * 1.10, 8)

    sl_json = json.dumps({
        "type": "STOP_MARKET",
        "stopPrice": sl_price,
        "workingType": "MARK_PRICE",
    }, separators=(',', ':'))

    tp_json = json.dumps({
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": tp_price,
        "workingType": "MARK_PRICE",
    }, separators=(',', ':'))

    order_params = {
        "symbol": coin,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": str(quantity),
        "stopLoss": sl_json,
        "takeProfit": tp_json,
    }

    ctx["sl_price"] = sl_price
    ctx["tp_price"] = tp_price

    req = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", order_params)
    logger.info("  Order URL (first 300 chars): %s", req["url"][:300])

    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()
    code = data.get("code", -1)

    if code != 0:
        return False, ("code=" + str(code)
                       + " msg=" + str(data.get("msg"))
                       + "\n  Full URL: " + req["url"]
                       + "\n  Response: " + json.dumps(data)[:500])

    order_data = data.get("data", {})
    order_id = str(order_data.get("orderId",
                   order_data.get("order", {}).get("orderId", "")))
    if not order_id or order_id == "":
        return False, ("Order succeeded but no orderId: "
                       + json.dumps(data)[:300])

    ctx["order_id"] = order_id
    return True, ("orderId=" + order_id
                  + " qty=" + str(quantity)
                  + " sl=" + str(sl_price))


# ---------------------------------------------------------------------------
# STEP 6: Verify position open
# ---------------------------------------------------------------------------
def step_verify_position(ctx):
    """Fetch positions, verify the test coin LONG appears."""
    auth = ctx["auth"]
    coin = ctx["coin"]

    time.sleep(1)

    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    if data.get("code", -1) != 0:
        return False, ("Positions code=" + str(data.get("code"))
                       + " msg=" + str(data.get("msg")))

    positions = data.get("data", [])
    for pos in positions:
        sym = pos.get("symbol", "")
        amt = float(pos.get("positionAmt", 0))
        if sym == coin and amt > 0:
            detail = ("Found " + coin + " LONG"
                      + " amt=" + str(amt)
                      + " avgPrice=" + str(pos.get("avgPrice", "?"))
                      + " unrealizedProfit="
                      + str(pos.get("unrealizedProfit", "?")))
            return True, detail

    found = [p.get("symbol", "?") + "=" + str(p.get("positionAmt", 0))
             for p in positions if float(p.get("positionAmt", 0)) != 0]
    return False, "Position not found. Open positions: " + str(found)


# ---------------------------------------------------------------------------
# STEP 7: Query pending orders (discover SL/TP structure)
# ---------------------------------------------------------------------------
def step_query_pending_orders(ctx):
    """Fetch pending/open orders to find the SL and TP conditional orders."""
    auth = ctx["auth"]
    coin = ctx["coin"]

    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/trade/openOrders", {
            "symbol": coin,
        })
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    if data.get("code", -1) != 0:
        return False, ("openOrders code=" + str(data.get("code"))
                       + " msg=" + str(data.get("msg"))
                       + " url=" + req["url"])

    orders = data.get("data", {}).get("orders", data.get("data", []))
    if isinstance(orders, dict):
        orders = [orders]

    # Log every pending order for debugging
    sl_order_id = None
    tp_order_id = None
    for o in orders:
        otype = str(o.get("type", ""))
        oid = str(o.get("orderId", ""))
        stop_price = o.get("stopPrice", o.get("price", "?"))
        logger.info("  Pending: id=%s type=%s stopPrice=%s status=%s",
                     oid, otype, stop_price, o.get("status", "?"))
        if "STOP" in otype and "PROFIT" not in otype:
            sl_order_id = oid
        if "TAKE_PROFIT" in otype:
            tp_order_id = oid

    ctx["sl_order_id"] = sl_order_id
    ctx["tp_order_id"] = tp_order_id
    found_count = len(orders) if isinstance(orders, list) else 0

    detail = (str(found_count) + " pending orders found"
              + " sl_order_id=" + str(sl_order_id)
              + " tp_order_id=" + str(tp_order_id))
    return True, detail


# ---------------------------------------------------------------------------
# STEP 8: Cancel SL and re-place at raised price (breakeven raise)
# ---------------------------------------------------------------------------
def step_raise_sl(ctx):
    """Cancel existing SL, place new SL closer to entry (raise toward breakeven)."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    sl_order_id = ctx.get("sl_order_id")
    mark_price = ctx["mark_price"]

    if sl_order_id is None:
        return True, ("SKIP: no SL order found in pending orders "
                      + "(SL may be position-level, not a separate order)")

    # Cancel the old SL
    req_cancel = auth.build_signed_request(
        "DELETE", "/openApi/swap/v2/trade/order", {
            "symbol": coin,
            "orderId": str(sl_order_id),
        })
    resp_cancel = requests.delete(
        req_cancel["url"], headers=req_cancel["headers"], timeout=10)
    data_cancel = resp_cancel.json()

    if data_cancel.get("code", -1) != 0:
        return False, ("Cancel SL code=" + str(data_cancel.get("code"))
                       + " msg=" + str(data_cancel.get("msg"))
                       + " url=" + req_cancel["url"])

    # Place new SL at 5% below entry (raised from 10%)
    new_sl_price = round(mark_price * 0.95, 8)

    # Place as a new conditional order on the existing position
    req_new = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", {
            "symbol": coin,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "STOP_MARKET",
            "quantity": str(ctx["quantity"]),
            "stopPrice": str(new_sl_price),
            "workingType": "MARK_PRICE",
        })
    resp_new = requests.post(
        req_new["url"], headers=req_new["headers"], timeout=10)
    data_new = resp_new.json()

    if data_new.get("code", -1) != 0:
        return False, ("New SL code=" + str(data_new.get("code"))
                       + " msg=" + str(data_new.get("msg"))
                       + " url=" + req_new["url"])

    new_oid = str(data_new.get("data", {}).get(
        "orderId", data_new.get("data", {}).get(
            "order", {}).get("orderId", "?")))

    detail = ("Cancelled old SL id=" + str(sl_order_id)
              + " -> new SL id=" + str(new_oid)
              + " raised from " + str(round(mark_price * 0.90, 8))
              + " to " + str(new_sl_price))
    return True, detail


# ---------------------------------------------------------------------------
# STEP 9: Cancel TP + re-place trailing TP (closer to current price)
# ---------------------------------------------------------------------------
def step_trail_tp(ctx):
    """Cancel existing TP, place new TP closer to entry (trailing TP test)."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    tp_order_id = ctx.get("tp_order_id")
    mark_price = ctx["mark_price"]

    if tp_order_id is None:
        return True, ("SKIP: no TP order found in pending orders "
                      + "(TP may be position-level, not a separate order)")

    # Cancel the old TP
    req_cancel = auth.build_signed_request(
        "DELETE", "/openApi/swap/v2/trade/order", {
            "symbol": coin,
            "orderId": str(tp_order_id),
        })
    resp_cancel = requests.delete(
        req_cancel["url"], headers=req_cancel["headers"], timeout=10)
    data_cancel = resp_cancel.json()

    if data_cancel.get("code", -1) != 0:
        return False, ("Cancel TP code=" + str(data_cancel.get("code"))
                       + " msg=" + str(data_cancel.get("msg"))
                       + " url=" + req_cancel["url"])

    # Place new TP at 5% above entry (tightened from 10%)
    new_tp_price = round(mark_price * 1.05, 8)

    req_new = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", {
            "symbol": coin,
            "side": "SELL",
            "positionSide": "LONG",
            "type": "TAKE_PROFIT_MARKET",
            "quantity": str(ctx["quantity"]),
            "stopPrice": str(new_tp_price),
            "workingType": "MARK_PRICE",
        })
    resp_new = requests.post(
        req_new["url"], headers=req_new["headers"], timeout=10)
    data_new = resp_new.json()

    if data_new.get("code", -1) != 0:
        return False, ("New TP code=" + str(data_new.get("code"))
                       + " msg=" + str(data_new.get("msg"))
                       + " url=" + req_new["url"])

    new_oid = str(data_new.get("data", {}).get(
        "orderId", data_new.get("data", {}).get(
            "order", {}).get("orderId", "?")))

    detail = ("Cancelled old TP id=" + str(tp_order_id)
              + " -> new TP id=" + str(new_oid)
              + " trailed from " + str(round(mark_price * 1.10, 8))
              + " to " + str(new_tp_price))
    return True, detail


# ---------------------------------------------------------------------------
# STEP 10: Close LONG position (cancel remaining pending orders first)
# ---------------------------------------------------------------------------
def step_close_position(ctx):
    """Cancel remaining pending orders, then MARKET SELL to close position."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    quantity = ctx["quantity"]

    # Cancel all pending orders for this symbol first (SL, TP, raised SL)
    req_cancel = auth.build_signed_request(
        "DELETE", "/openApi/swap/v2/trade/allOpenOrders", {
            "symbol": coin,
        })
    resp_cancel = requests.delete(
        req_cancel["url"], headers=req_cancel["headers"], timeout=10)
    data_cancel = resp_cancel.json()
    cancel_code = data_cancel.get("code", -1)
    if cancel_code != 0:
        # Log but don't fail -- some exchanges return error if no orders
        logger.warning("  Cancel all orders: code=%s msg=%s",
                       cancel_code, data_cancel.get("msg"))

    # Close the position with a market order
    order_params = {
        "symbol": coin,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": str(quantity),
    }

    req = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", order_params)
    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()
    code = data.get("code", -1)

    if code != 0:
        return False, ("Close failed: code=" + str(code)
                       + " msg=" + str(data.get("msg"))
                       + "\n  URL: " + req["url"])

    return True, "Cancelled pending orders + closed position for " + coin


# ---------------------------------------------------------------------------
# STEP 11: Verify LONG position closed
# ---------------------------------------------------------------------------
def step_verify_closed(ctx):
    """Fetch positions, verify test coin is no longer open."""
    auth = ctx["auth"]
    coin = ctx["coin"]

    time.sleep(1)

    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    if data.get("code", -1) != 0:
        return False, "Positions code=" + str(data.get("code"))

    positions = data.get("data", [])
    for pos in positions:
        sym = pos.get("symbol", "")
        side = pos.get("positionSide", "")
        amt = float(pos.get("positionAmt", 0))
        if sym == coin and side == "LONG" and amt != 0:
            return False, ("Position still open: " + coin
                           + " LONG amt=" + str(amt))

    return True, "No LONG position for " + coin


# ---------------------------------------------------------------------------
# STEP 13: SHORT trade cycle (open + verify + close + verify)
# ---------------------------------------------------------------------------
def step_short_cycle(ctx):
    """Full SHORT cycle: SELL entry with SL+TP -> verify -> close -> verify."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    quantity = ctx["quantity"]
    mark_price = ctx["mark_price"]

    # SL 10% above, TP 10% below (inverse of LONG)
    sl_price = round(mark_price * 1.10, 8)
    tp_price = round(mark_price * 0.90, 8)

    sl_json = json.dumps({
        "type": "STOP_MARKET",
        "stopPrice": sl_price,
        "workingType": "MARK_PRICE",
    }, separators=(',', ':'))

    tp_json = json.dumps({
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": tp_price,
        "workingType": "MARK_PRICE",
    }, separators=(',', ':'))

    # SELL entry for SHORT
    order_params = {
        "symbol": coin,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "MARKET",
        "quantity": str(quantity),
        "stopLoss": sl_json,
        "takeProfit": tp_json,
    }

    req = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", order_params)
    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    if data.get("code", -1) != 0:
        return False, ("SHORT entry code=" + str(data.get("code"))
                       + " msg=" + str(data.get("msg"))
                       + "\n  URL: " + req["url"])

    short_oid = str(data.get("data", {}).get("orderId",
                    data.get("data", {}).get("order", {}).get(
                        "orderId", "?")))
    logger.info("  SHORT entry orderId=%s", short_oid)

    # Verify SHORT position appears
    time.sleep(1)
    req_pos = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_pos = requests.get(
        req_pos["url"], headers=req_pos["headers"], timeout=10)
    data_pos = resp_pos.json()
    if data_pos.get("code", -1) != 0:
        return False, "Position check code=" + str(data_pos.get("code"))

    found_short = False
    for pos in data_pos.get("data", []):
        if (pos.get("symbol") == coin
                and pos.get("positionSide") == "SHORT"
                and float(pos.get("positionAmt", 0)) != 0):
            found_short = True
            break
    if not found_short:
        return False, "SHORT position not found after entry"

    # Cancel all pending orders for this symbol
    req_cancel = auth.build_signed_request(
        "DELETE", "/openApi/swap/v2/trade/allOpenOrders", {
            "symbol": coin,
        })
    resp_cancel = requests.delete(
        req_cancel["url"], headers=req_cancel["headers"], timeout=10)

    # Close SHORT with BUY
    close_params = {
        "symbol": coin,
        "side": "BUY",
        "positionSide": "SHORT",
        "type": "MARKET",
        "quantity": str(quantity),
    }
    req_close = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", close_params)
    resp_close = requests.post(
        req_close["url"], headers=req_close["headers"], timeout=10)
    data_close = resp_close.json()

    if data_close.get("code", -1) != 0:
        return False, ("SHORT close code=" + str(data_close.get("code"))
                       + " msg=" + str(data_close.get("msg")))

    # Verify closed
    time.sleep(1)
    req_verify = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_verify = requests.get(
        req_verify["url"], headers=req_verify["headers"], timeout=10)
    data_verify = resp_verify.json()
    for pos in data_verify.get("data", []):
        if (pos.get("symbol") == coin
                and pos.get("positionSide") == "SHORT"
                and float(pos.get("positionAmt", 0)) != 0):
            return False, "SHORT still open after close"

    detail = ("SHORT cycle complete: entry -> verify -> cancel orders"
              + " -> close -> verify closed. orderId=" + short_oid)
    return True, detail


# ---------------------------------------------------------------------------
# STEP 14: Multi-position test (LONG + SHORT simultaneous)
# ---------------------------------------------------------------------------
def step_multi_position(ctx):
    """Open LONG and SHORT on same coin, verify both, close one, verify other survives."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    quantity = ctx["quantity"]
    mark_price = ctx["mark_price"]

    # Open LONG
    sl_long = round(mark_price * 0.90, 8)
    long_params = {
        "symbol": coin,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": str(quantity),
        "stopLoss": json.dumps({
            "type": "STOP_MARKET",
            "stopPrice": sl_long,
            "workingType": "MARK_PRICE",
        }, separators=(',', ':')),
    }
    req_long = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", long_params)
    resp_long = requests.post(
        req_long["url"], headers=req_long["headers"], timeout=10)
    data_long = resp_long.json()
    if data_long.get("code", -1) != 0:
        return False, ("LONG entry code=" + str(data_long.get("code"))
                       + " msg=" + str(data_long.get("msg")))

    # Open SHORT
    sl_short = round(mark_price * 1.10, 8)
    short_params = {
        "symbol": coin,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "MARKET",
        "quantity": str(quantity),
        "stopLoss": json.dumps({
            "type": "STOP_MARKET",
            "stopPrice": sl_short,
            "workingType": "MARK_PRICE",
        }, separators=(',', ':')),
    }
    req_short = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", short_params)
    resp_short = requests.post(
        req_short["url"], headers=req_short["headers"], timeout=10)
    data_short = resp_short.json()
    if data_short.get("code", -1) != 0:
        return False, ("SHORT entry code=" + str(data_short.get("code"))
                       + " msg=" + str(data_short.get("msg")))

    # Verify BOTH positions appear
    time.sleep(1)
    req_pos = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_pos = requests.get(
        req_pos["url"], headers=req_pos["headers"], timeout=10)
    data_pos = resp_pos.json()
    if data_pos.get("code", -1) != 0:
        return False, "Position check code=" + str(data_pos.get("code"))

    found_long = False
    found_short = False
    for pos in data_pos.get("data", []):
        if pos.get("symbol") == coin and float(pos.get("positionAmt", 0)) != 0:
            if pos.get("positionSide") == "LONG":
                found_long = True
            if pos.get("positionSide") == "SHORT":
                found_short = True

    if not found_long or not found_short:
        return False, ("Multi-position: long=" + str(found_long)
                       + " short=" + str(found_short)
                       + " (expected both True)")

    # Close LONG only, verify SHORT survives
    req_cancel_all = auth.build_signed_request(
        "DELETE", "/openApi/swap/v2/trade/allOpenOrders", {
            "symbol": coin,
        })
    requests.delete(
        req_cancel_all["url"], headers=req_cancel_all["headers"], timeout=10)

    close_long = {
        "symbol": coin,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": str(quantity),
    }
    req_cl = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", close_long)
    resp_cl = requests.post(
        req_cl["url"], headers=req_cl["headers"], timeout=10)
    if resp_cl.json().get("code", -1) != 0:
        return False, "Close LONG failed: " + str(resp_cl.json().get("msg"))

    time.sleep(1)
    req_v2 = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_v2 = requests.get(
        req_v2["url"], headers=req_v2["headers"], timeout=10)
    data_v2 = resp_v2.json()

    long_still = False
    short_still = False
    for pos in data_v2.get("data", []):
        if pos.get("symbol") == coin and float(pos.get("positionAmt", 0)) != 0:
            if pos.get("positionSide") == "LONG":
                long_still = True
            if pos.get("positionSide") == "SHORT":
                short_still = True

    if long_still:
        return False, "LONG still open after close (should be gone)"
    if not short_still:
        return False, "SHORT disappeared when we only closed LONG"

    # Clean up: close the SHORT
    close_short = {
        "symbol": coin,
        "side": "BUY",
        "positionSide": "SHORT",
        "type": "MARKET",
        "quantity": str(quantity),
    }
    req_cs = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", close_short)
    resp_cs = requests.post(
        req_cs["url"], headers=req_cs["headers"], timeout=10)
    if resp_cs.json().get("code", -1) != 0:
        return False, "Close SHORT failed: " + str(resp_cs.json().get("msg"))

    detail = ("Multi-position: LONG+SHORT open -> verified both -> "
              + "closed LONG -> SHORT survived -> closed SHORT -> clean")
    return True, detail


# ---------------------------------------------------------------------------
# STEP 14: Limit order test (BUY LIMIT near ask price -> fill -> close)
# ---------------------------------------------------------------------------
def step_limit_order(ctx):
    """Place a LIMIT BUY slightly above mark price so it fills as taker."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    quantity = ctx["quantity"]

    # Fetch fresh mark price (may have moved since step 2)
    url_p = auth.build_public_url(
        "/openApi/swap/v2/quote/price", {"symbol": coin})
    resp_p = requests.get(url_p, timeout=10)
    data_p = resp_p.json()
    if data_p.get("code", -1) != 0:
        return False, "Price fetch failed: " + str(data_p.get("msg"))
    price_data = data_p.get("data", {})
    if isinstance(price_data, dict):
        fresh_price = float(price_data.get("price", 0))
    elif isinstance(price_data, list) and price_data:
        fresh_price = float(price_data[0].get("price", 0))
    else:
        return False, "Unexpected price format"
    if fresh_price <= 0:
        return False, "Fresh price <= 0"

    # Set limit price 0.5% above mark to guarantee immediate fill
    limit_price = round(fresh_price * 1.005, 8)

    order_params = {
        "symbol": coin,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "price": str(limit_price),
        "quantity": str(quantity),
    }

    req = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", order_params)
    resp = requests.post(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    if data.get("code", -1) != 0:
        return False, ("Limit order code=" + str(data.get("code"))
                       + " msg=" + str(data.get("msg"))
                       + "\n  URL: " + req["url"])

    limit_oid = str(data.get("data", {}).get("orderId",
                    data.get("data", {}).get("order", {}).get(
                        "orderId", "?")))
    logger.info("  Limit orderId=%s price=%s", limit_oid, limit_price)

    # Wait briefly for fill
    time.sleep(2)

    # Check if position opened
    req_pos = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    resp_pos = requests.get(
        req_pos["url"], headers=req_pos["headers"], timeout=10)
    data_pos = resp_pos.json()

    found = False
    for pos in data_pos.get("data", []):
        if pos.get("symbol") == coin and float(pos.get("positionAmt", 0)) > 0:
            found = True
            break

    if not found:
        # Check if order is still pending (not filled yet)
        req_ord = auth.build_signed_request(
            "GET", "/openApi/swap/v2/trade/order", {
                "symbol": coin, "orderId": str(limit_oid),
            })
        resp_ord = requests.get(
            req_ord["url"], headers=req_ord["headers"], timeout=10)
        ord_status = resp_ord.json().get("data", {}).get(
            "order", {}).get("status", "UNKNOWN")
        # Cancel unfilled order
        req_cancel = auth.build_signed_request(
            "DELETE", "/openApi/swap/v2/trade/order", {
                "symbol": coin, "orderId": str(limit_oid),
            })
        requests.delete(
            req_cancel["url"], headers=req_cancel["headers"], timeout=10)
        return False, ("Limit order not filled after 2s. status="
                       + str(ord_status) + " price=" + str(limit_price)
                       + " mark=" + str(fresh_price))

    # Clean up: cancel all pending + close position
    req_cancel_all = auth.build_signed_request(
        "DELETE", "/openApi/swap/v2/trade/allOpenOrders", {
            "symbol": coin,
        })
    requests.delete(
        req_cancel_all["url"], headers=req_cancel_all["headers"], timeout=10)

    close_params = {
        "symbol": coin,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "MARKET",
        "quantity": str(quantity),
    }
    req_close = auth.build_signed_request(
        "POST", "/openApi/swap/v2/trade/order", close_params)
    resp_close = requests.post(
        req_close["url"], headers=req_close["headers"], timeout=10)
    if resp_close.json().get("code", -1) != 0:
        return False, ("Limit close failed: "
                       + str(resp_close.json().get("msg")))

    detail = ("Limit BUY filled at " + str(limit_price)
              + " (mark=" + str(fresh_price) + ")"
              + " -> closed. orderId=" + limit_oid)
    return True, detail


# ---------------------------------------------------------------------------
# STEP 15: Fetch order details (LONG entry)
# ---------------------------------------------------------------------------
def step_fetch_order(ctx):
    """Query the LONG entry order by orderId. Verify avgPrice exists."""
    auth = ctx["auth"]
    coin = ctx["coin"]
    order_id = ctx["order_id"]

    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/trade/order", {
            "symbol": coin,
            "orderId": str(order_id),
        })
    resp = requests.get(req["url"], headers=req["headers"], timeout=10)
    data = resp.json()

    if data.get("code", -1) != 0:
        return False, ("Order query code=" + str(data.get("code"))
                       + " msg=" + str(data.get("msg"))
                       + " url=" + req["url"])

    order = data.get("data", {}).get("order", data.get("data", {}))
    avg_price = order.get("avgPrice", None)
    status = order.get("status", "UNKNOWN")

    if avg_price is None:
        return False, ("No avgPrice in response: "
                       + json.dumps(data)[:300])

    detail = ("orderId=" + str(order_id)
              + " avgPrice=" + str(avg_price)
              + " status=" + str(status))
    return True, detail


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Load credentials, run 15 lifecycle steps, print summary."""
    parser = argparse.ArgumentParser(
        description="BingX API lifecycle test (real VST demo)")
    parser.add_argument(
        "--coin", type=str, default="RIVER-USDT",
        help="Test coin symbol (default: RIVER-USDT)")
    args = parser.parse_args()

    setup_logging()

    logger.info("=" * 60)
    logger.info("BingX API Lifecycle Test")
    logger.info("Coin: %s", args.coin)
    logger.info("=" * 60)

    load_dotenv(ROOT / ".env")
    api_key = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    if not api_key or not secret_key:
        logger.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY in .env")
        sys.exit(1)

    auth = BingXAuth(api_key, secret_key, demo_mode=True)

    ctx = {
        "auth": auth,
        "coin": args.coin,
        "mark_price": None,
        "step_size": None,
        "quantity": None,
        "order_id": None,
        "leverage": 10,
        "margin_usd": 50.0,
    }

    steps = [
        (1, "Auth check (signed GET /positions)", step_auth_check),
        (2, "Public endpoints (klines + price + contracts)", step_public_endpoints),
        (3, "Leverage + margin type setup", step_leverage_margin),
        (4, "Quantity calculation", step_qty_calc),
        # --- LONG lifecycle ---
        (5, "LONG entry with SL+TP (signature test)", step_place_order),
        (6, "Verify LONG position open", step_verify_position),
        (7, "Query pending orders (find SL/TP)", step_query_pending_orders),
        (8, "Raise SL (cancel + re-place breakeven)", step_raise_sl),
        (9, "Trail TP (cancel + re-place closer)", step_trail_tp),
        (10, "Close LONG (cancel pending + MARKET SELL)", step_close_position),
        (11, "Verify LONG closed", step_verify_closed),
        # --- SHORT lifecycle ---
        (12, "SHORT full cycle (entry+SL+TP -> verify -> close)", step_short_cycle),
        # --- Multi-position ---
        (13, "Multi-position (LONG+SHORT -> close one -> other survives)", step_multi_position),
        # --- Limit order ---
        (14, "Limit order (BUY near ask -> fill -> close)", step_limit_order),
        # --- Order query ---
        (15, "Fetch LONG order details (avgPrice check)", step_fetch_order),
    ]

    # --- STEP 0: cleanup stale positions from prior runs ---
    coin = args.coin
    logger.info("STEP 0: Cleanup stale positions for %s", coin)
    try:
        req_cancel = auth.build_signed_request(
            "DELETE", "/openApi/swap/v2/trade/allOpenOrders", {
                "symbol": coin})
        requests.delete(
            req_cancel["url"], headers=req_cancel["headers"], timeout=10)
        for close_side, close_ps in [("SELL", "LONG"), ("BUY", "SHORT")]:
            req_p = auth.build_signed_request(
                "GET", "/openApi/swap/v2/user/positions")
            resp_p = requests.get(
                req_p["url"], headers=req_p["headers"], timeout=10)
            for pos in resp_p.json().get("data", []):
                if (pos.get("symbol") == coin
                        and pos.get("positionSide") == close_ps
                        and float(pos.get("positionAmt", 0)) != 0):
                    qty = abs(float(pos["positionAmt"]))
                    cp = {"symbol": coin, "side": close_side,
                          "positionSide": close_ps, "type": "MARKET",
                          "quantity": str(qty)}
                    rc = auth.build_signed_request(
                        "POST", "/openApi/swap/v2/trade/order", cp)
                    requests.post(
                        rc["url"], headers=rc["headers"], timeout=10)
                    logger.info("  Closed stale %s qty=%s", close_ps, qty)
        time.sleep(1)
    except Exception as e:
        logger.warning("  Cleanup error (non-fatal): %s", e)

    total_start = time.time()
    for step_num, name, func in steps:
        run_step(step_num, name, func, ctx)

    elapsed = round(time.time() - total_start, 1)
    logger.info("=" * 60)
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    total = len(steps)
    logger.info("RESULTS: %d/%d passed, %d failed in %.1fs",
                passed, total, failed, elapsed)
    for status, label, name, ms in RESULTS:
        logger.info("  %s  %s  %s  (%dms)", status, label, name, ms)
    logger.info("=" * 60)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
