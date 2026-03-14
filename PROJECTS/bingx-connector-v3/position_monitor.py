"""
Position monitor: polls exchange, detects closes, daily reset.
BUG-C04 fix: halt_flag reset at 17:00 UTC.
"""
import queue
import logging
import requests
from datetime import datetime, timezone

from api_utils import fetch_mark_price as _shared_fetch_mark_price

logger = logging.getLogger(__name__)

POSITIONS_PATH = "/openApi/swap/v2/user/positions"
ORDER_PATH = "/openApi/swap/v2/trade/order"
OPEN_ORDERS_PATH = "/openApi/swap/v2/trade/openOrders"
ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"
PRICE_PATH = "/openApi/swap/v2/quote/price"

class PositionMonitor:
    """Monitor open positions and detect SL/TP exits."""

    def __init__(self, auth, state_manager, notifier, config,
                 commission_rate_rt=0.0016, fill_queue=None):
        """Initialize with auth, state, notifier, config, round-trip commission rate, fill queue.

        commission_rate_rt: Round-trip (entry + exit) taker fee.
        """
        self.auth = auth
        self.state = state_manager
        self.notifier = notifier
        # W07: Renamed to commission_rate_rt -- Round-trip (entry + exit) taker fee
        self.commission_rate_rt = commission_rate_rt
        self.fill_queue = fill_queue or queue.Queue()
        self.config = config
        self.daily_loss_limit = config.get(
            "daily_loss_limit_usd", 75.0)
        self.daily_summary_hour = config.get(
            "daily_summary_utc_hour", 17)
        self._last_reset_date = None
        self._last_metrics_hour = -1
        self._check_startup_reset()
        self.ttp_mode = config.get("position", {}).get("ttp_mode", "engine")
        logger.info("PositionMonitor: loss=%.1f reset_h=%d commission_rate_rt=%.6f ttp_mode=%s",
                     self.daily_loss_limit, self.daily_summary_hour,
                     self.commission_rate_rt, self.ttp_mode)

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
                if data.get("code") == 109400:
                    from time_sync import get_time_sync
                    _ts = get_time_sync()
                    _ts.force_resync()
                    req = self.auth.build_signed_request(
                        "GET", POSITIONS_PATH)
                    resp = requests.get(
                        req["url"], headers=req["headers"], timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("code", 0) == 0:
                        logger.info("109400 retry succeeded for positions")
                        return data.get("data", [])
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
        """Detect exit by querying allOrders FIRST for real fill price.

        Priority: (1) allOrders avgPrice, (2) pending-order inference for
        reason only, (3) state estimates as last resort.
        Returns (exit_price, exit_reason) or (None, None) on failure.
        """
        # TTP exit: if ttp_exit_pending flag is set, try allOrders for fill price
        if pos_data.get("ttp_exit_pending"):
            ttp_fill = pos_data.get("ttp_fill_price")
            if ttp_fill:
                return float(ttp_fill), "TTP_EXIT"
            hist_price, _ = self._fetch_filled_exit(symbol, pos_data)
            if hist_price:
                return hist_price, "TTP_EXIT"
            trail = pos_data.get("ttp_trail_level")
            if trail is not None:
                logger.warning("TTP exit %s: using trail_level as fallback (no fill price)", symbol)
                return float(trail), "TTP_EXIT"
            return None, "TTP_EXIT"
        # Step 1: Query allOrders for REAL fill price (most accurate)
        hist_price, hist_reason = self._fetch_filled_exit(symbol, pos_data)
        if hist_price is not None:
            # Real fill found -- cancel any orphaned orders
            self._cleanup_orphaned_orders(symbol, pos_data)
            return hist_price, hist_reason
        # Step 2: Check pending orders to infer exit reason
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
        trailing_orders = []
        for o in orders:
            otype = o.get("type", "")
            if "TAKE_PROFIT" in otype:
                tp_orders.append(o)
            elif otype == "TRAILING_STOP_MARKET":
                trailing_orders.append(o)
            elif "STOP" in otype:
                sl_orders.append(o)
        # Native trailing detection: trailing fired if not in open orders
        if self.ttp_mode == "native" and pos_data.get("trailing_order_id"):
            if not trailing_orders:
                for o in sl_orders + tp_orders:
                    self._cancel_order(symbol, o.get("orderId"))
                logger.info("Detected TRAILING_EXIT for %s, cancelled %d orphaned orders",
                            symbol, len(sl_orders) + len(tp_orders))
                return None, "TRAILING_EXIT"
        # Infer reason from which orders remain, but use state price as LAST RESORT
        if sl_orders and not tp_orders:
            exit_reason = "TP_HIT"
            exit_price = pos_data.get("tp_price")
            for o in sl_orders:
                self._cancel_order(symbol, o.get("orderId"))
            logger.warning("TP_HIT %s: allOrders miss, using state tp_price=%.8f as fallback",
                           symbol, float(exit_price or 0))
        elif tp_orders and not sl_orders:
            exit_reason = "SL_HIT"
            exit_price = pos_data.get("sl_price")
            for o in tp_orders:
                self._cancel_order(symbol, o.get("orderId"))
            logger.warning("SL_HIT %s: allOrders miss, using state sl_price=%.8f as fallback",
                           symbol, float(exit_price or 0))
        elif sl_orders and tp_orders:
            logger.warning(
                "Both SL and TP still open for %s -- position may not be closed",
                symbol)
            return None, None
        else:
            exit_reason = "EXIT_UNKNOWN"
            exit_price = pos_data.get("sl_price")
            logger.warning(
                "No pending or filled SL/TP found for %s"
                " -- using SL price estimate", symbol)
        return exit_price, exit_reason

    def _cleanup_orphaned_orders(self, symbol, pos_data):
        """Cancel any orphaned SL/TP/trailing orders after a fill is confirmed."""
        direction = pos_data.get("direction", "")
        try:
            req = self.auth.build_signed_request(
                "GET", OPEN_ORDERS_PATH, {"symbol": symbol})
            resp = requests.get(
                req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
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
                logger.info("Cleanup: cancelled %d orphaned orders for %s %s",
                            cancelled, symbol, direction)
        except Exception as e:
            logger.warning("Orphaned order cleanup failed %s: %s", symbol, e)

    def _fetch_filled_exit(self, symbol, pos_data):
        """Query order history to find actual exit fill price.

        W05: Filters by positionSide to avoid cross-position matches.
        Returns (exit_price, exit_reason) or (None, None).
        """
        try:
            entry_time = pos_data.get("entry_time", "")
            params = {"symbol": symbol, "limit": "50"}
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
                # W05: Filter by positionSide to match the position direction
                if o.get("positionSide", "") != pos_data.get("direction", ""):
                    continue
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
                if otype == "TRAILING_STOP_MARKET":
                    logger.info(
                        "Found filled TRAILING order for %s avgPrice=%.6f",
                        symbol, avg_price)
                    return avg_price, "TRAILING_EXIT"
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
        """Poll positions and detect closes. W01: Read state once, track WS-processed keys."""
        # W01: Read state_positions ONCE at the top
        state_positions = self.state.get_open_positions()
        # W01: Track keys processed by WS drain
        processed_keys = set()
        # Drain WebSocket fill events first (instant detection path)
        while not self.fill_queue.empty():
            try:
                event = self.fill_queue.get_nowait()
                symbol = event.get("symbol", "")
                key_long = symbol + "_LONG"
                key_short = symbol + "_SHORT"
                for key in (key_long, key_short):
                    pos = state_positions.get(key)
                    if pos:
                        logger.info("WS fill event: %s reason=%s price=%.6f",
                                    key, event["reason"], event["avg_price"])
                        self._handle_close_with_price(
                            key, pos, event["avg_price"], event["reason"])
                        processed_keys.add(key)
            except queue.Empty:
                break
        if not state_positions:
            return
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
        # W01: Use the single state_positions snapshot, skip WS-processed keys
        for key, pos_data in state_positions.items():
            if key in processed_keys:
                continue
            if key not in live_keys:
                self._handle_close(key, pos_data)

    def _handle_close(self, key, pos_data):
        """Handle a position closed on exchange (SL/TP hit). W02: TTP fallback to mark price."""
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
        elif detected_reason is not None and "TTP" in detected_reason:
            # W02: TTP exit returned (None, "TTP_EXIT") -- fetch mark price as fallback
            mark = self._fetch_mark_price_pm(symbol)
            if mark is not None and mark > 0:
                exit_price = mark
                exit_reason = detected_reason
                logger.warning(
                    "TTP exit %s: using mark price %.8f as fallback (no fill price)",
                    key, mark)
            else:
                exit_price = sl_price
                exit_reason = detected_reason
                logger.warning(
                    "TTP exit %s: mark price unavailable, using SL price as last resort",
                    key)
        else:
            exit_price = sl_price
            exit_reason = "SL_HIT_ASSUMED"
            logger.warning(
                "Exit detection failed for %s -- using SL price as estimate",
                key)
        if direction == "LONG":
            pnl_gross = (exit_price - entry_price) * quantity
        else:
            pnl_gross = (entry_price - exit_price) * quantity
        # W07: Use commission_rate_rt -- Round-trip (entry + exit) taker fee
        commission = notional * self.commission_rate_rt
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
        # W07: Use commission_rate_rt -- Round-trip (entry + exit) taker fee
        commission = notional * self.commission_rate_rt
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
        """Fetch current mark price for a symbol. W17: Delegates to shared api_utils helper."""
        return _shared_fetch_mark_price(self.auth.base_url, symbol)

    def _cancel_sl_orders(self, symbol, direction, keep_latest=False):
        """Cancel SL orders for symbol+direction. W18: Merged cancel functions.

        If keep_latest=True, keeps the most recent SL order (by updateTime/createTime).
        If keep_latest=False, cancels ALL SL orders.
        """
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
            sl_orders = []
            for o in orders:
                otype = o.get("type", "")
                pos_side = o.get("positionSide", "")
                if ("STOP" in otype and "TAKE_PROFIT" not in otype
                        and otype != "TRAILING_STOP_MARKET"
                        and pos_side == direction):
                    sl_orders.append(o)
            if not sl_orders:
                return
            if keep_latest:
                if len(sl_orders) <= 1:
                    return  # only the new SL exists, nothing to cancel
                # W10: Sort by updateTime/createTime instead of orderId
                sl_orders.sort(key=lambda o: int(
                    o.get("updateTime", o.get("createTime", o.get("orderId", 0)))))
                to_cancel = sl_orders[:-1]
            else:
                to_cancel = sl_orders
            for o in to_cancel:
                self._cancel_order(symbol, o.get("orderId"))
                logger.info("Cancelled SL order %s for %s %s (keep_latest=%s)",
                            o.get("orderId"), symbol, direction, keep_latest)
        except Exception as e:
            logger.warning("cancel_sl_orders failed %s: %s", symbol, e)

    def _place_be_sl(self, symbol, pos_data):
        """Place standalone STOP_MARKET at true breakeven price.

        BE price = entry * (1 + commission_rate_rt) for LONG,
                   entry * (1 - commission_rate_rt) for SHORT.
        Returns be_price (float) on success, None on failure.
        """
        direction = pos_data.get("direction", "")
        entry_price = pos_data.get("entry_price", 0)
        quantity = pos_data.get("quantity", 0)
        notional = pos_data.get("notional_usd", 0)
        if not direction or not entry_price or not quantity:
            logger.error("BE SL: missing data for %s", symbol)
            return None
        # Slippage buffer on top of commission to prevent negative fills
        be_buffer = self.config.get("position", {}).get("be_buffer", 0.002)
        if direction == "LONG":
            be_price = entry_price * (1 + self.commission_rate_rt + be_buffer)
        else:
            be_price = entry_price * (1 - self.commission_rate_rt - be_buffer)
        commission_usd = round(notional * self.commission_rate_rt, 4)
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
                _d = data.get("data", {})
                order_id = str(_d.get("orderId") or _d.get("order", {}).get("orderId", "?"))
                logger.info(
                    "BE+fees SL placed: %s side=%s entry=%.8f be_price=%.8f"
                    " rate=%.4f%% covers=$%.4f commission orderId=%s",
                    symbol, side, entry_price, be_price,
                    self.commission_rate_rt * 100, commission_usd, order_id)
                return be_price
            logger.error("BE SL order failed %s: code=%s msg=%s",
                         symbol, data.get("code"), data.get("msg"))
            return None
        except Exception as e:
            logger.error("BE SL place error %s: %s", symbol, e)
            return None

    def check_breakeven(self):
        """Auto-raise SL to breakeven when live mark price crosses be_act threshold.

        Runs once per position (be_raised persists in state.json).
        No-op if be_auto is False.
        """
        be_auto = self.config.get("position", {}).get("be_auto", True)
        if not be_auto:
            return
        be_activation = self.config.get("position", {}).get("be_act", 0.004)
        positions = self.state.get_open_positions()
        for key, pos_data in positions.items():
            if pos_data.get("be_raised"):
                continue
            entry_price = float(pos_data.get("entry_price", 0) or 0)
            direction = pos_data.get("direction", "")
            symbol = pos_data.get("symbol", key.rsplit("_", 1)[0])
            if not entry_price or direction not in ("LONG", "SHORT") or not symbol:
                continue
            mark = self._fetch_mark_price_pm(symbol)
            if mark is None or mark <= 0:
                logger.debug("BE check: no mark price for %s", symbol)
                continue
            if direction == "LONG":
                activation_price = entry_price * (1.0 + be_activation)
                triggered = mark >= activation_price
            else:
                activation_price = entry_price * (1.0 - be_activation)
                triggered = mark <= activation_price
            if not triggered:
                continue
            logger.info(
                "BE trigger (live mark): %s entry=%.6f mark=%.6f act=%.6f direction=%s",
                key, entry_price, mark, activation_price, direction)
            # SAFE: place new SL first, cancel old ONLY after success
            be_price = self._place_be_sl(symbol, pos_data)
            if be_price is not None:
                # W18: New BE SL confirmed -- now safe to cancel old SL (keep latest)
                self._cancel_sl_orders(symbol, direction, keep_latest=True)
                self.state.update_position(key, {
                    "sl_price": be_price,
                    "be_raised": True,
                })
                notional = pos_data.get("notional_usd", 0)
                commission_usd = round(notional * self.commission_rate_rt, 4)
                msg = ("<b>BE+FEES RAISED</b>  " + key
                       + "\nEntry:  " + str(round(entry_price, 8))
                       + "\nMark:   " + str(round(mark, 8))
                       + "\nSL -> " + str(round(be_price, 8))
                       + "  (+" + str(round(self.commission_rate_rt * 100, 3))
                       + "% covers $" + str(commission_usd) + " RT commission)")
                self.notifier.send(msg)
                logger.info(
                    "BE+fees raised: %s entry=%.8f mark=%.8f be_price=%.8f"
                    " (+%.4f%%) covers=$%.4f RT commission",
                    key, entry_price, mark, be_price,
                    self.commission_rate_rt * 100, commission_usd)
            else:
                # Placement failed -- old SL still intact (safe)
                logger.error(
                    "BE SL place FAILED for %s -- old SL preserved (safe)", key)
                self.notifier.send(
                    "<b>BE RAISE FAILED</b>  " + key
                    + "\nNew SL rejected -- old SL still active")



    def _tighten_sl_after_ttp(self, key, pos_data, mark_price):
        """Progressive SL tightening once TTP is ACTIVATED.

        Trails SL toward current_extreme * (1 - sl_trail_pct) for LONG.
        Only moves SL in the favourable direction. Rate-limited.
        """
        sl_trail_pct = (
            self.config.get("four_pillars", {}).get("sl_trail_pct_post_ttp")
            or self.config.get("position", {}).get("sl_trail_pct_post_ttp")
        )
        if not sl_trail_pct:
            return  # disabled

        direction   = pos_data.get("direction", "")
        entry_price = float(pos_data.get("entry_price") or 0)
        cur_sl      = float(pos_data.get("sl_price") or 0)
        ttp_extreme = pos_data.get("ttp_extreme")
        symbol      = pos_data.get("symbol", key.rsplit("_", 1)[0])
        quantity    = pos_data.get("quantity", 0)

        if not direction or not entry_price or not ttp_extreme or not quantity:
            return
        if direction not in ("LONG", "SHORT"):
            return

        extreme = float(ttp_extreme)
        sl_trail_pct = float(sl_trail_pct)

        if direction == "LONG":
            new_sl = extreme * (1.0 - sl_trail_pct)
            # Only move SL up
            if cur_sl and new_sl <= cur_sl:
                return
            # Must be above entry (never worse than entry)
            if new_sl <= entry_price:
                return
            # Rate limit: at least 0.1% improvement
            if cur_sl and (new_sl - cur_sl) / cur_sl < 0.001:
                return
        else:
            new_sl = extreme * (1.0 + sl_trail_pct)
            # Only move SL down
            if cur_sl and new_sl >= cur_sl:
                return
            if new_sl >= entry_price:
                return
            if cur_sl and (cur_sl - new_sl) / cur_sl < 0.001:
                return

        new_sl = round(new_sl, 8)
        logger.info("SL tighten post-TTP: %s cur_sl=%.8f new_sl=%.8f extreme=%.8f",
                    key, cur_sl, new_sl, extreme)

        # SAFE: place new SL first, cancel old ONLY after success
        side = "SELL" if direction == "LONG" else "BUY"
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": direction,
            "type": "STOP_MARKET",
            "quantity": str(quantity),
            "stopPrice": str(new_sl),
            "workingType": "MARK_PRICE",
        }
        req = self.auth.build_signed_request("POST", ORDER_PATH, order_params)
        try:
            resp = requests.post(req["url"], headers=req["headers"], timeout=10)
            data = resp.json()
            if data.get("code", 0) == 0:
                _d = data.get("data", {})
                order_id = str(_d.get("orderId") or _d.get("order", {}).get("orderId", "?"))
                # W18: New SL confirmed -- now safe to cancel old SL orders (keep latest)
                self._cancel_sl_orders(symbol, direction, keep_latest=True)
                self.state.update_position(key, {"sl_price": new_sl})
                logger.info("SL tightened: %s new_sl=%.8f orderId=%s", key, new_sl, order_id)
            else:
                # Placement failed -- old SL still intact (safe)
                logger.warning("SL tighten REJECTED %s: code=%s msg=%s -- old SL preserved",
                               key, data.get("code"), data.get("msg"))
        except Exception as e:
            logger.warning("SL tighten error %s: %s -- old SL preserved", key, e)


    def check_ttp_closes(self):
        """Process TTP close flags set by signal_engine. Executes market close on exchange."""
        if self.ttp_mode == "native":
            return
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

    def check_ttp_sl_tighten(self):
        """Tighten SL progressively for all ACTIVATED TTP positions."""
        if self.ttp_mode == "native":
            return
        positions = self.state.get_open_positions()
        for key, pos in positions.items():
            if pos.get("ttp_state") != "ACTIVATED":
                continue
            if pos.get("ttp_close_pending"):
                continue  # TTP close already queued -- don't move SL
            symbol    = pos.get("symbol", key.rsplit("_", 1)[0])
            direction = pos.get("direction", "LONG")
            mark = self._fetch_mark_price_pm(symbol)
            if mark and mark > 0:
                self._tighten_sl_after_ttp(key, pos, mark)

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
        """Place MARKET close order using positionSide (Hedge mode). Returns True on success."""
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
                _d = data.get("data", {})
                order_id = str(_d.get("orderId") or _d.get("order", {}).get("orderId", "?"))
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

    def _calc_unrealized_pnl(self, positions):
        """Fetch mark prices and sum unrealized PnL across all open positions."""
        total_unrealized = 0.0
        for key, pos in positions.items():
            symbol = pos.get("symbol", key.rsplit("_", 1)[0])
            entry = float(pos.get("entry_price") or 0)
            qty = float(pos.get("quantity") or 0)
            direction = pos.get("direction", "LONG")
            if not entry or not qty:
                continue
            mark = self._fetch_mark_price_pm(symbol)
            if not mark:
                continue
            if direction == "LONG":
                total_unrealized += (mark - entry) * qty
            else:
                total_unrealized += (entry - mark) * qty
        return round(total_unrealized, 2)

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
            open_positions = current.get("open_positions", {})
            open_count = len(open_positions)
            unrealized = self._calc_unrealized_pnl(open_positions)
            equity = round(daily_pnl + unrealized, 2)
            self.state.reset_daily()
            summary = ("<b>DAILY SUMMARY</b>"
                       + "\nRealized PnL: $" + str(round(daily_pnl, 2))
                       + "\nUnrealized:   $" + str(unrealized)
                       + "\nEquity:       $" + str(equity)
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
        open_positions = current.get("open_positions", {})
        open_count = len(open_positions)
        unrealized = self._calc_unrealized_pnl(open_positions)
        equity = round(daily_pnl + unrealized, 2)
        pct_of_limit = (abs(daily_pnl) / self.daily_loss_limit
                        * 100) if self.daily_loss_limit > 0 else 0
        logger.info(
            "HOURLY: realized=%.2f unrealized=%.2f equity=%.2f trades=%d open=%d loss_pct=%.1f%%",
            daily_pnl, unrealized, equity, daily_trades, open_count, pct_of_limit)
        if daily_pnl < 0 and pct_of_limit >= 50:
            self.notifier.send(
                "<b>WARNING</b>\nDaily loss at "
                + str(round(pct_of_limit, 1))
                + "% of limit\nRealized: $"
                + str(round(abs(daily_pnl), 2))
                + " / $" + str(round(self.daily_loss_limit, 2))
                + "\nUnrealized: $" + str(unrealized)
                + "\nEquity: $" + str(equity))
