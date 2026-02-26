"""
Order executor: mark price, qty calc, order placement with SL/TP.
Uses v2 endpoints for all signed operations.
BUG-C02 fix: mark price from /quote/price, not /quote/klines.
"""
import json
import math
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PRICE_PATH = "/openApi/swap/v2/quote/price"
CONTRACTS_PATH = "/openApi/swap/v2/quote/contracts"
ORDER_PATH = "/openApi/swap/v2/trade/order"


class Executor:
    """Execute trades on BingX with SL/TP attached."""

    def __init__(self, auth, state_manager, notifier, position_config):
        """Initialize with auth, state, notifier, position settings."""
        self.auth = auth
        self.state = state_manager
        self.notifier = notifier
        self.margin_usd = position_config.get("margin_usd", 50.0)
        self.leverage = position_config.get("leverage", 10)
        self.sl_working_type = position_config.get(
            "sl_working_type", "MARK_PRICE")
        self.tp_working_type = position_config.get(
            "tp_working_type", "MARK_PRICE")
        logger.info("Executor: margin=%.0f leverage=%d",
                     self.margin_usd, self.leverage)

    def _safe_get(self, url, headers=None):
        """Execute GET with error handling. Returns dict or None."""
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error("API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data
        except requests.exceptions.Timeout:
            logger.error("Timeout: GET %s", url[:100])
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Connection failed: GET %s", url[:100])
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP %s: GET %s",
                         e.response.status_code, url[:100])
            return None
        except ValueError:
            logger.error("Invalid JSON: GET %s", url[:100])
            return None

    def _safe_post(self, url, headers=None):
        """Execute POST with error handling. Returns dict or None."""
        try:
            resp = requests.post(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error("API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data
        except requests.exceptions.Timeout:
            logger.error("Timeout: POST %s", url[:100])
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Connection failed: POST %s", url[:100])
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP %s: POST %s",
                         e.response.status_code, url[:100])
            return None
        except ValueError:
            logger.error("Invalid JSON: POST %s", url[:100])
            return None

    def fetch_mark_price(self, symbol):
        """Fetch current mark price. Returns float or None."""
        url = self.auth.build_public_url(
            PRICE_PATH, {"symbol": symbol})
        data = self._safe_get(url)
        if data is None:
            return None
        try:
            price_data = data.get("data", {})
            if isinstance(price_data, dict):
                return float(price_data.get("price", 0))
            if isinstance(price_data, list) and price_data:
                return float(price_data[0].get("price", 0))
            logger.error("Unexpected price format: %s", symbol)
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error("Price parse error %s: %s", symbol, e)
            return None

    def fetch_step_size(self, symbol):
        """Fetch step size for a symbol. Returns float or None."""
        url = self.auth.build_public_url(CONTRACTS_PATH)
        data = self._safe_get(url)
        if data is None:
            return None
        try:
            contracts = data.get("data", [])
            for c in contracts:
                if c.get("symbol") == symbol:
                    return float(c.get("tradeMinQuantity",
                                       c.get("stepSize", 1)))
            logger.error("Symbol %s not found in contracts", symbol)
            return None
        except (ValueError, TypeError) as e:
            logger.error("Step size parse error %s: %s", symbol, e)
            return None

    def _round_down(self, value, step):
        """Round value DOWN to the nearest step increment."""
        if step <= 0:
            return value
        return math.floor(value / step) * step

    def execute(self, signal, symbol):
        """Execute trade: price, qty, order+SL+TP. Returns dict or None."""
        mark_price = self.fetch_mark_price(symbol)
        if mark_price is None or mark_price <= 0:
            logger.error("Cannot execute %s: no mark price", symbol)
            return None
        step_size = self.fetch_step_size(symbol)
        if step_size is None:
            logger.error("Cannot execute %s: no step size", symbol)
            return None
        notional = self.margin_usd * self.leverage
        raw_qty = notional / mark_price
        quantity = self._round_down(raw_qty, step_size)
        if quantity <= 0:
            logger.error("Qty zero: %s raw=%.8f step=%.8f",
                         symbol, raw_qty, step_size)
            return None
        side = "BUY" if signal.direction == "LONG" else "SELL"
        position_side = signal.direction
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": "MARKET",
            "quantity": str(quantity),
        }
        sl_order = {
            "type": "STOP_MARKET",
            "stopPrice": signal.sl_price,
            "workingType": self.sl_working_type,
        }
        order_params["stopLoss"] = json.dumps(sl_order, separators=(',', ':'))
        if signal.tp_price is not None:
            tp_order = {
                "type": "TAKE_PROFIT_MARKET",
                "stopPrice": signal.tp_price,
                "workingType": self.tp_working_type,
            }
            order_params["takeProfit"] = json.dumps(
                tp_order, separators=(',', ':'))
        req = self.auth.build_signed_request(
            "POST", ORDER_PATH, order_params)
        logger.info(
            "Order: %s %s qty=%.6f mark=%.6f notional=%.2f",
            side, symbol, quantity, mark_price, notional)
        result = self._safe_post(req["url"], headers=req["headers"])
        if result is None:
            logger.error("Order failed: %s", symbol)
            self.notifier.send("ORDER FAILED: " + side + " " + symbol)
            return None
        order_data = result.get("data", {})
        order_id = str(order_data.get("orderId",
                       order_data.get("order", {}).get(
                           "orderId", "unknown")))
        if order_id == "unknown":
            logger.error(
                "Order returned unknown ID for %s — not recording"
                " position", symbol)
            self.notifier.send(
                "ORDER ID UNKNOWN: " + side + " " + symbol
                + " — position NOT tracked")
            return None
        position_record = {
            "symbol": symbol,
            "direction": signal.direction,
            "grade": signal.grade,
            "entry_price": mark_price,
            "sl_price": signal.sl_price,
            "tp_price": signal.tp_price,
            "quantity": quantity,
            "notional_usd": notional,
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "order_id": order_id,
            "atr_at_entry": signal.atr,
        }
        key = symbol + "_" + signal.direction
        self.state.record_open_position(key, position_record)
        entry_msg = ("ENTRY: " + side + " " + symbol
                     + " qty=" + str(round(quantity, 6))
                     + " price=" + str(round(mark_price, 6))
                     + " SL=" + str(round(signal.sl_price, 6))
                     + " grade=" + signal.grade)
        if signal.tp_price is not None:
            entry_msg += " TP=" + str(round(signal.tp_price, 6))
        self.notifier.send(entry_msg)
        logger.info("Order placed: %s id=%s", key, order_id)
        return result
