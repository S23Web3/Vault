"""
Position monitor: polls exchange, detects closes, daily reset.
BUG-C04 fix: halt_flag reset at 17:00 UTC.
"""
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

POSITIONS_PATH = "/openApi/swap/v2/user/positions"
ORDER_PATH = "/openApi/swap/v2/trade/order"
OPEN_ORDERS_PATH = "/openApi/swap/v2/trade/openOrders"
ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"


class PositionMonitor:
    """Monitor open positions and detect SL/TP exits."""

    def __init__(self, auth, state_manager, notifier, config):
        """Initialize with auth, state, notifier, and config."""
        self.auth = auth
        self.state = state_manager
        self.notifier = notifier
        self.daily_loss_limit = config.get(
            "daily_loss_limit_usd", 75.0)
        self.daily_summary_hour = config.get(
            "daily_summary_utc_hour", 17)
        self._last_reset_date = None
        self._last_metrics_hour = -1
        self._check_startup_reset()
        logger.info("PositionMonitor: loss=%.1f reset_h=%d",
                     self.daily_loss_limit, self.daily_summary_hour)

    def _check_startup_reset(self):
        """Reset daily metrics if bot restarted on a new calendar day."""
        current = self.state.get_state()
        session_start = current.get("session_start", "")
        if not session_start:
            return
        try:
            from datetime import datetime as dt
            start_date = dt.fromisoformat(
                session_start.replace("Z", "+00:00")).date()
            today = datetime.now(timezone.utc).date()
            if start_date < today:
                logger.info(
                    "Startup reset: session_start=%s is before today=%s",
                    start_date, today)
                self.state.reset_daily()
                self._last_reset_date = today
        except (ValueError, TypeError) as e:
            logger.warning("Startup reset date parse error: %s", e)

    def _fetch_positions(self):
        """Fetch open positions from BingX. Returns list or None."""
        req = self.auth.build_signed_request(
            "GET", POSITIONS_PATH)
        try:
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error("Positions API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data.get("data", [])
        except requests.exceptions.Timeout:
            logger.error("Positions timeout")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Positions connection failed")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("Positions HTTP %s",
                         e.response.status_code)
            return None
        except ValueError:
            logger.error("Positions invalid JSON")
            return None

    def _detect_exit(self, symbol, pos_data):
        """Detect SL or TP hit by checking which conditional orders remain.

        Queries open orders for the symbol. If SL is still pending, TP
        was hit (and vice versa). Cancels the orphaned remaining order.
        Returns (exit_price, exit_reason) or (None, None) on failure.
        """
        try:
            req = self.auth.build_signed_request(
                "GET", OPEN_ORDERS_PATH, {"symbol": symbol})
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("open orders API error %s: %s",
                               data.get("code"), data.get("msg"))
                return None, None
            orders = data.get("data", {}).get("orders", [])
            if isinstance(data.get("data"), list):
                orders = data["data"]
        except Exception as e:
            logger.warning("open orders fetch failed %s: %s", symbol, e)
            return None, None
        sl_orders = []
        tp_orders = []
        for o in orders:
            otype = o.get("type", "")
            if "TAKE_PROFIT" in otype:
                tp_orders.append(o)
            elif "STOP" in otype:
                sl_orders.append(o)
        if sl_orders and not tp_orders:
            exit_reason = "TP_HIT"
            exit_price = pos_data.get("tp_price")
            for o in sl_orders:
                self._cancel_order(symbol, o.get("orderId"))
            logger.info("Detected TP_HIT for %s, cancelled %d SL orders",
                        symbol, len(sl_orders))
        elif tp_orders and not sl_orders:
            exit_reason = "SL_HIT"
            exit_price = pos_data.get("sl_price")
            for o in tp_orders:
                self._cancel_order(symbol, o.get("orderId"))
            logger.info("Detected SL_HIT for %s, cancelled %d TP orders",
                        symbol, len(tp_orders))
        elif sl_orders and tp_orders:
            logger.warning(
                "Both SL and TP still open for %s — position may not be closed",
                symbol)
            return None, None
        else:
            hist_price, hist_reason = self._fetch_filled_exit(
                symbol, pos_data)
            if hist_price is not None:
                exit_price = hist_price
                exit_reason = hist_reason
            else:
                exit_reason = "EXIT_UNKNOWN"
                exit_price = pos_data.get("sl_price")
                logger.warning(
                    "No pending or filled SL/TP found for %s"
                    " — using SL price estimate", symbol)
        return exit_price, exit_reason

    def _fetch_filled_exit(self, symbol, pos_data):
        """Query order history to find actual exit fill price.

        When pending SL/TP orders are already cleaned up by BingX,
        check allOrders for a recently filled STOP or TP order.
        Returns (exit_price, exit_reason) or (None, None).
        """
        try:
            entry_time = pos_data.get("entry_time", "")
            params = {"symbol": symbol, "limit": "20"}
            if entry_time:
                from datetime import datetime as dt
                try:
                    t = dt.fromisoformat(entry_time.replace("Z", "+00:00"))
                    params["startTime"] = str(int(t.timestamp() * 1000))
                except (ValueError, TypeError):
                    pass
            req = self.auth.build_signed_request(
                "GET", ALL_ORDERS_PATH, params)
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("allOrders API error %s: %s",
                               data.get("code"), data.get("msg"))
                return None, None
            orders = data.get("data", {}).get("orders", [])
            if isinstance(data.get("data"), list):
                orders = data["data"]
            for o in orders:
                status = o.get("status", "")
                otype = o.get("type", "")
                if status != "FILLED":
                    continue
                avg_price = float(o.get("avgPrice", 0))
                if avg_price <= 0:
                    continue
                if "TAKE_PROFIT" in otype:
                    logger.info(
                        "Found filled TP order for %s avgPrice=%.6f",
                        symbol, avg_price)
                    return avg_price, "TP_HIT"
                if "STOP" in otype:
                    logger.info(
                        "Found filled SL order for %s avgPrice=%.6f",
                        symbol, avg_price)
                    return avg_price, "SL_HIT"
            return None, None
        except Exception as e:
            logger.warning("allOrders fetch failed %s: %s", symbol, e)
            return None, None

    def _cancel_order(self, symbol, order_id):
        """Cancel a single order by ID."""
        if not order_id:
            return
        try:
            req = self.auth.build_signed_request(
                "DELETE", ORDER_PATH,
                {"symbol": symbol, "orderId": str(order_id)})
            resp = requests.delete(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("Cancel order %s failed: %s",
                               order_id, data.get("msg"))
            else:
                logger.info("Cancelled orphaned order %s for %s",
                            order_id, symbol)
        except Exception as e:
            logger.warning("Cancel order %s error: %s", order_id, e)

    def check(self):
        """Poll positions and detect closes."""
        live_raw = self._fetch_positions()
        if live_raw is None:
            return
        live_keys = set()
        for pos in live_raw:
            symbol = pos.get("symbol", "")
            amt = float(pos.get("positionAmt", 0))
            if amt == 0:
                continue
            side = pos.get("positionSide", "")
            if side in ("LONG", "SHORT"):
                direction = side
            else:
                direction = "LONG" if amt > 0 else "SHORT"
            key = symbol + "_" + direction
            live_keys.add(key)
        state_positions = self.state.get_open_positions()
        for key, pos_data in state_positions.items():
            if key not in live_keys:
                self._handle_close(key, pos_data)

    def _handle_close(self, key, pos_data):
        """Handle a position closed on exchange (SL/TP hit)."""
        entry_price = pos_data.get("entry_price", 0)
        sl_price = pos_data.get("sl_price", 0)
        direction = pos_data.get("direction", "LONG")
        quantity = pos_data.get("quantity", 0)
        notional = pos_data.get("notional_usd", 0)
        symbol = key.rsplit("_", 1)[0]
        detected_price, detected_reason = self._detect_exit(
            symbol, pos_data)
        if detected_price is not None:
            exit_price = detected_price
            exit_reason = detected_reason
        else:
            exit_price = sl_price
            exit_reason = "SL_HIT_ASSUMED"
            logger.warning(
                "Exit detection failed for %s — using SL price as estimate",
                key)
        if direction == "LONG":
            pnl_gross = (exit_price - entry_price) * quantity
        else:
            pnl_gross = (entry_price - exit_price) * quantity
        commission = notional * 0.0012  # 0.06% taker x 2 sides
        pnl_net = pnl_gross - commission
        self.state.close_position(key, exit_price, exit_reason,
                                  pnl_net)
        current = self.state.get_state()
        if current.get("daily_pnl", 0) <= -self.daily_loss_limit:
            self.state.set_halt_flag(True)
            self.notifier.send(
                "HARD STOP: daily loss limit ($"
                + str(round(abs(current["daily_pnl"]), 2)) + ")")
        msg = ("EXIT: " + key
               + " reason=" + exit_reason
               + " pnl=" + str(round(pnl_net, 2))
               + " daily=" + str(round(
                   current.get("daily_pnl", 0), 2)))
        self.notifier.send(msg)
        logger.info("Closed: %s pnl=%.2f", key, pnl_net)

    def check_daily_reset(self):
        """Check if 17:00 UTC has passed and trigger reset."""
        now = datetime.now(timezone.utc)
        today = now.date()
        if (now.hour >= self.daily_summary_hour
                and self._last_reset_date != today):
            self._last_reset_date = today
            current = self.state.get_state()
            daily_pnl = current.get("daily_pnl", 0)
            daily_trades = current.get("daily_trades", 0)
            open_count = len(current.get("open_positions", {}))
            self.state.reset_daily()
            summary = ("DAILY SUMMARY: pnl="
                       + str(round(daily_pnl, 2))
                       + " trades=" + str(daily_trades)
                       + " open=" + str(open_count))
            self.notifier.send(summary)
            logger.info("Daily reset: %s", summary)

    def check_hourly_metrics(self):
        """Log hourly metrics snapshot. Alert if daily loss exceeds 50%."""
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        if current_hour == self._last_metrics_hour:
            return
        self._last_metrics_hour = current_hour
        current = self.state.get_state()
        daily_pnl = current.get("daily_pnl", 0)
        daily_trades = current.get("daily_trades", 0)
        open_count = len(current.get("open_positions", {}))
        pct_of_limit = (abs(daily_pnl) / self.daily_loss_limit
                        * 100) if self.daily_loss_limit > 0 else 0
        logger.info(
            "HOURLY: pnl=%.2f trades=%d open=%d loss_pct=%.1f%%",
            daily_pnl, daily_trades, open_count, pct_of_limit)
        if daily_pnl < 0 and pct_of_limit >= 50:
            self.notifier.send(
                "WARNING: daily loss at "
                + str(round(pct_of_limit, 1))
                + "% of limit ($"
                + str(round(abs(daily_pnl), 2))
                + " / $" + str(round(self.daily_loss_limit, 2))
                + ")")
