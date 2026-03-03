"""
Position monitor: polls exchange, detects closes, daily reset.
BUG-C04 fix: halt_flag reset at 17:00 UTC.
"""
import queue
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

POSITIONS_PATH = "/openApi/swap/v2/user/positions"
ORDER_PATH = "/openApi/swap/v2/trade/order"
OPEN_ORDERS_PATH = "/openApi/swap/v2/trade/openOrders"
ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"
PRICE_PATH = "/openApi/swap/v2/quote/price"

class PositionMonitor:
    """Monitor open positions and detect SL/TP exits."""

    def __init__(self, auth, state_manager, notifier, config,
                 commission_rate=0.0016, fill_queue=None):
        """Initialize with auth, state, notifier, config, commission rate, fill queue."""
        self.auth = auth
        self.state = state_manager
        self.notifier = notifier
        self.commission_rate = commission_rate
        self.fill_queue = fill_queue or queue.Queue()
        self.config = config
        self.daily_loss_limit = config.get(
            "daily_loss_limit_usd", 75.0)
        self.daily_summary_hour = config.get(
            "daily_summary_utc_hour", 17)
        self._last_reset_date = None
        self._last_metrics_hour = -1
        self._check_startup_reset()
        logger.info("PositionMonitor: loss=%.1f reset_h=%d commission=%.6f",
                     self.daily_loss_limit, self.daily_summary_hour,
                     self.commission_rate)

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
        # TTP exit: if ttp_exit_pending flag is set, return trail level as exit price
        if pos_data.get("ttp_exit_pending"):
            trail = pos_data.get("ttp_trail_level")
            if trail is not None:
                return float(trail), "TTP_EXIT"
            return None, "TTP_EXIT"
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
        # Drain WebSocket fill events first (instant detection path)
        while not self.fill_queue.empty():
            try:
                event = self.fill_queue.get_nowait()
                symbol = event.get("symbol", "")
                key_long = symbol + "_LONG"
                key_short = symbol + "_SHORT"
                for key in (key_long, key_short):
                    pos = self.state.get_open_positions().get(key)
                    if pos:
                        logger.info("WS fill event: %s reason=%s price=%.6f",
                                    key, event["reason"], event["avg_price"])
                        self._handle_close_with_price(
                            key, pos, event["avg_price"], event["reason"])
            except queue.Empty:
                break
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
        commission = notional * self.commission_rate  # taker fee x 2 sides (from config)
        pnl_net = pnl_gross - commission
        self.state.close_position(key, exit_price, exit_reason,
                                  pnl_net)
        current = self.state.get_state()
        if current.get("daily_pnl", 0) <= -self.daily_loss_limit:
            self.state.set_halt_flag(True)
            self.notifier.send(
                "<b>HARD STOP</b>\nDaily loss limit: $"
                + str(round(abs(current["daily_pnl"]), 2)))
        msg = ("<b>EXIT</b>  " + key
               + "\nReason: " + exit_reason
               + "\nPnL: $" + str(round(pnl_net, 2))
               + "\nDaily: $" + str(round(
                   current.get("daily_pnl", 0), 2)))
        self.notifier.send(msg)
        logger.info("Closed: %s pnl=%.2f", key, pnl_net)

    def _handle_close_with_price(self, key, pos_data, exit_price, exit_reason):
        """Handle close with known exit price and reason (from WS fill event)."""
        entry_price = pos_data.get("entry_price", 0)
        direction = pos_data.get("direction", "LONG")
        quantity = pos_data.get("quantity", 0)
        notional = pos_data.get("notional_usd", 0)
        if direction == "LONG":
            pnl_gross = (exit_price - entry_price) * quantity
        else:
            pnl_gross = (entry_price - exit_price) * quantity
        commission = notional * self.commission_rate
        pnl_net = pnl_gross - commission
        self.state.close_position(key, exit_price, exit_reason, pnl_net)
        current = self.state.get_state()
        if current.get("daily_pnl", 0) <= -self.daily_loss_limit:
            self.state.set_halt_flag(True)
            self.notifier.send(
                "<b>HARD STOP</b>\nDaily loss limit: $"
                + str(round(abs(current["daily_pnl"]), 2)))
        msg = ("<b>EXIT (WS)</b>  " + key
               + "\nReason: " + exit_reason
               + "\nPnL: $" + str(round(pnl_net, 2))
               + "\nDaily: $" + str(round(
                   current.get("daily_pnl", 0), 2)))
        self.notifier.send(msg)
        logger.info("Closed (WS): %s pnl=%.2f reason=%s", key, pnl_net, exit_reason)

    def _fetch_mark_price_pm(self, symbol):
        """Fetch current mark price for a symbol. Returns float or None."""
        url = self.auth.build_public_url(PRICE_PATH, {"symbol": symbol})
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("Mark price error %s: %s",
                               data.get("code"), data.get("msg"))
                return None
            price_data = data.get("data", {})
            if isinstance(price_data, dict):
                return float(price_data.get("price", 0))
            if isinstance(price_data, list) and price_data:
                return float(price_data[0].get("price", 0))
            return None
        except Exception as e:
            logger.warning("Mark price fetch error %s: %s", symbol, e)
            return None

    def _cancel_open_sl_orders(self, symbol, direction):
        """Cancel any open STOP/STOP_MARKET orders for symbol+direction (not TP)."""
        try:
            req = self.auth.build_signed_request(
                "GET", OPEN_ORDERS_PATH, {"symbol": symbol})
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("open orders error %s: %s",
                               data.get("code"), data.get("msg"))
                return
            orders = data.get("data", {}).get("orders", [])
            if isinstance(data.get("data"), list):
                orders = data["data"]
            for o in orders:
                otype = o.get("type", "")
                pos_side = o.get("positionSide", "")
                if ("STOP" in otype and "TAKE_PROFIT" not in otype
                        and pos_side == direction):
                    self._cancel_order(symbol, o.get("orderId"))
        except Exception as e:
            logger.warning("cancel_open_sl_orders failed %s: %s", symbol, e)

    def _place_be_sl(self, symbol, pos_data):
        """Place standalone STOP_MARKET at true breakeven price.

        BE price = entry * (1 + commission_rate) for LONG,
                   entry * (1 - commission_rate) for SHORT.
        This ensures the stop, if filled at exactly be_price, yields
        gross pnl == commission (net pnl == 0).
        Returns be_price (float) on success, None on failure.
        """
        direction = pos_data.get("direction", "")
        entry_price = pos_data.get("entry_price", 0)
        quantity = pos_data.get("quantity", 0)
        notional = pos_data.get("notional_usd", 0)
        if not direction or not entry_price or not quantity:
            logger.error("BE SL: missing data for %s", symbol)
            return None
        if direction == "LONG":
            be_price = entry_price * (1 + self.commission_rate)
        else:
            be_price = entry_price * (1 - self.commission_rate)
        commission_usd = round(notional * self.commission_rate, 4)
        side = "SELL" if direction == "LONG" else "BUY"
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": direction,
            "type": "STOP_MARKET",
            "quantity": str(quantity),
            "stopPrice": str(round(be_price, 8)),
            "workingType": "MARK_PRICE",
        }
        req = self.auth.build_signed_request("POST", ORDER_PATH, order_params)
        try:
            resp = requests.post(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) == 0:
                order_id = str(
                    data.get("data", {}).get("orderId", "?"))
                logger.info(
                    "BE+fees SL placed: %s side=%s entry=%.8f be_price=%.8f"
                    " rate=%.4f%% covers=$%.4f commission orderId=%s",
                    symbol, side, entry_price, be_price,
                    self.commission_rate * 100, commission_usd, order_id)
                return be_price
            logger.error("BE SL order failed %s: code=%s msg=%s",
                         symbol, data.get("code"), data.get("msg"))
            return None
        except Exception as e:
            logger.error("BE SL place error %s: %s", symbol, e)
            return None

    def check_breakeven(self):
        """Auto-raise SL to breakeven when TTP activates, if be_auto is enabled in config.

        Trigger: ttp_state == "ACTIVATED" written to position state by signal_engine each bar.
        Runs once per position (be_raised persists in state.json).
        No-op if be_auto is False or TTP is disabled (state never reaches ACTIVATED).
        """
        be_auto = self.config.get("position", {}).get("be_auto", True)
        if not be_auto:
            return
        positions = self.state.get_open_positions()
        for key, pos_data in positions.items():
            if pos_data.get("be_raised"):
                continue
            if pos_data.get("ttp_state") != "ACTIVATED":
                continue
            entry_price = float(pos_data.get("entry_price", 0) or 0)
            direction = pos_data.get("direction", "")
            symbol = pos_data.get("symbol", key.rsplit("_", 1)[0])
            if not entry_price or direction not in ("LONG", "SHORT") or not symbol:
                continue
            logger.info(
                "BE trigger (TTP activated): %s entry=%.6f direction=%s",
                key, entry_price, direction)
            self._cancel_open_sl_orders(symbol, direction)
            be_price = self._place_be_sl(symbol, pos_data)
            if be_price is not None:
                self.state.update_position(key, {
                    "sl_price": be_price,
                    "be_raised": True,
                })
                notional = pos_data.get("notional_usd", 0)
                commission_usd = round(notional * self.commission_rate, 4)
                msg = ("<b>BE+FEES RAISED (TTP)</b>  " + key
                       + "\nEntry:  " + str(round(entry_price, 8))
                       + "\nSL -> " + str(round(be_price, 8))
                       + "  (+" + str(round(self.commission_rate * 100, 3))
                       + "% covers $" + str(commission_usd) + " RT commission)"
                       + "\nTTP activated at ~0.5% from entry")
                self.notifier.send(msg)
                logger.info(
                    "BE+fees raised (TTP): %s entry=%.8f be_price=%.8f"
                    " (+%.4f%%) covers=$%.4f RT commission",
                    key, entry_price, be_price,
                    self.commission_rate * 100, commission_usd)
            else:
                logger.error(
                    "BE SL place FAILED for %s -- old SL cancelled, check manually", key)
                self.notifier.send(
                    "<b>BE RAISE FAILED</b>  " + key
                    + "\nOld SL cancelled but new SL FAILED -- check manually")


    def check_ttp_closes(self):
        """Process TTP close flags set by signal_engine. Executes market close on exchange."""
        positions = self.state.get_open_positions()
        for key, pos in positions.items():
            if not pos.get("ttp_close_pending"):
                continue
            symbol = pos.get("symbol", key.rsplit("_", 1)[0])
            direction = pos.get("direction", "LONG")
            quantity = pos.get("quantity", 0)
            # Race guard: verify position still exists on exchange
            live = self._fetch_single_position(symbol, direction)
            if not live:
                # SL/TP already filled on exchange -- clear flag
                self.state.update_position(key, {"ttp_close_pending": False})
                logger.info("TTP close skipped (position gone): %s", key)
                continue
            # Cancel all pending orders (SL + TP) then market close
            self._cancel_all_orders_for_symbol(symbol, direction)
            ok = self._place_market_close(symbol, direction, quantity)
            if ok:
                self.state.update_position(key, {
                    "ttp_close_pending": False,
                    "ttp_exit_pending": True,
                })
                logger.info("TTP close executed: %s", key)
            else:
                # Failed to place market close -- leave flag for retry
                logger.error("TTP close FAILED: %s -- will retry next loop", key)

    def _cancel_all_orders_for_symbol(self, symbol, direction):
        """Cancel ALL pending orders for symbol+direction (SL, TP, any type)."""
        try:
            req = self.auth.build_signed_request(
                "GET", OPEN_ORDERS_PATH, {"symbol": symbol})
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("TTP cancel orders error %s: %s",
                               data.get("code"), data.get("msg"))
                return
            orders = data.get("data", {}).get("orders", [])
            if isinstance(data.get("data"), list):
                orders = data["data"]
            cancelled = 0
            for o in orders:
                pos_side = o.get("positionSide", "")
                if pos_side == direction:
                    self._cancel_order(symbol, o.get("orderId"))
                    cancelled += 1
            if cancelled:
                logger.info("TTP cancelled %d orders for %s %s",
                            cancelled, symbol, direction)
        except Exception as e:
            logger.warning("TTP cancel_all_orders failed %s: %s", symbol, e)

    def _place_market_close(self, symbol, direction, quantity):
        """Place MARKET reduceOnly close order. Returns True on success."""
        side = "SELL" if direction == "LONG" else "BUY"
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": direction,
            "type": "MARKET",
            "quantity": str(quantity),
        }
        req = self.auth.build_signed_request("POST", ORDER_PATH, order_params)
        try:
            resp = requests.post(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) == 0:
                order_id = str(data.get("data", {}).get("orderId", "?"))
                logger.info("TTP market close placed: %s %s orderId=%s",
                            symbol, side, order_id)
                return True
            logger.error("TTP market close failed %s: code=%s msg=%s",
                         symbol, data.get("code"), data.get("msg"))
            return False
        except Exception as e:
            logger.error("TTP market close error %s: %s", symbol, e)
            return False

    def _fetch_single_position(self, symbol, direction):
        """Fetch a single position from exchange. Returns position dict or None."""
        try:
            req = self.auth.build_signed_request(
                "GET", POSITIONS_PATH)
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                return None
            for pos in data.get("data", []):
                if pos.get("symbol") != symbol:
                    continue
                amt = float(pos.get("positionAmt", 0))
                if amt == 0:
                    continue
                side = pos.get("positionSide", "")
                if side == direction:
                    return pos
                if side not in ("LONG", "SHORT"):
                    inferred = "LONG" if amt > 0 else "SHORT"
                    if inferred == direction:
                        return pos
            return None
        except Exception as e:
            logger.warning("TTP fetch_single_position %s: %s", symbol, e)
            return None

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
            summary = ("<b>DAILY SUMMARY</b>"
                       + "\nPnL: $" + str(round(daily_pnl, 2))
                       + "\nTrades: " + str(daily_trades)
                       + "\nOpen: " + str(open_count))
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
                "<b>WARNING</b>\nDaily loss at "
                + str(round(pct_of_limit, 1))
                + "% of limit\n$"
                + str(round(abs(daily_pnl), 2))
                + " / $" + str(round(self.daily_loss_limit, 2)))
