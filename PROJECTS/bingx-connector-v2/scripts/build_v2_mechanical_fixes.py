"""
Build script: v2 mechanical audit fixes (9 patches).
Backs up each file before patching. py_compile validates each.

Run: cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2" && python scripts/build_v2_mechanical_fixes.py
"""
import sys
import shutil
import py_compile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
APPLIED = []
SKIPPED = []
TS = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def backup(path):
    """Create timestamped .bak of a file."""
    bak = Path(str(path) + "." + TS + ".bak")
    shutil.copy2(path, bak)
    print("  BACKUP: " + str(bak))
    return bak


def verify(path):
    """Syntax-check a .py file; return True if clean."""
    try:
        py_compile.compile(str(path), doraise=True)
        print("  SYNTAX OK: " + str(path.name))
        return True
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        return False


def patch_file(path, anchor, replacement, label):
    """Replace anchor text in file. Returns True on success."""
    text = path.read_text(encoding="utf-8")
    if anchor not in text:
        print("  MISSING_ANCHOR: " + label)
        SKIPPED.append(label)
        return False
    if replacement in text:
        print("  ALREADY_APPLIED: " + label)
        SKIPPED.append(label + " (already applied)")
        return True
    new_text = text.replace(anchor, replacement, 1)
    path.write_text(new_text, encoding="utf-8")
    print("  PATCHED: " + label)
    APPLIED.append(label)
    return True


# =====================================================================
# PATCH 1: position_monitor.py — allOrders-first _detect_exit
# =====================================================================
def patch_position_monitor():
    """Apply 6 patches to position_monitor.py."""
    pm = ROOT / "position_monitor.py"
    print("\n=== position_monitor.py ===")
    backup(pm)

    # --- Fix 1: _detect_exit — query allOrders FIRST for real fill price ---
    # The current code uses state estimates (sl_price/tp_price) as exit prices.
    # We rewrite to query allOrders first, use pending orders only for reason.

    old_detect_exit = '''    def _detect_exit(self, symbol, pos_data):
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
                hist_price, _ = self._fetch_filled_exit(symbol, pos_data)
                if hist_price:
                    return hist_price, "TRAILING_EXIT"
                return None, "TRAILING_EXIT"
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
        return exit_price, exit_reason'''

    new_detect_exit = '''    def _detect_exit(self, symbol, pos_data):
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
            # Real fill found — cancel any orphaned orders
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
                "Both SL and TP still open for %s — position may not be closed",
                symbol)
            return None, None
        else:
            exit_reason = "EXIT_UNKNOWN"
            exit_price = pos_data.get("sl_price")
            logger.warning(
                "No pending or filled SL/TP found for %s"
                " — using SL price estimate", symbol)
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
            logger.warning("Orphaned order cleanup failed %s: %s", symbol, e)'''

    patch_file(pm, old_detect_exit, new_detect_exit,
               "Fix 1: allOrders-first _detect_exit")

    # --- Fix 2: check_breakeven — place-then-cancel (not cancel-then-place) ---
    old_be = '''            self._cancel_open_sl_orders(symbol, direction)
            be_price = self._place_be_sl(symbol, pos_data)
            if be_price is not None:
                self.state.update_position(key, {
                    "sl_price": be_price,
                    "be_raised": True,
                })
                notional = pos_data.get("notional_usd", 0)
                commission_usd = round(notional * self.commission_rate, 4)
                msg = ("<b>BE+FEES RAISED</b>  " + key
                       + "\\nEntry:  " + str(round(entry_price, 8))
                       + "\\nMark:   " + str(round(mark, 8))
                       + "\\nSL -> " + str(round(be_price, 8))
                       + "  (+" + str(round(self.commission_rate * 100, 3))
                       + "% covers $" + str(commission_usd) + " RT commission)")
                self.notifier.send(msg)
                logger.info(
                    "BE+fees raised: %s entry=%.8f mark=%.8f be_price=%.8f"
                    " (+%.4f%%) covers=$%.4f RT commission",
                    key, entry_price, mark, be_price,
                    self.commission_rate * 100, commission_usd)
            else:
                logger.error(
                    "BE SL place FAILED for %s -- old SL cancelled, check manually", key)
                self.notifier.send(
                    "<b>BE RAISE FAILED</b>  " + key
                    + "\\nOld SL cancelled but new SL FAILED -- check manually")'''

    new_be = '''            # SAFE: place new SL first, cancel old ONLY after success
            be_price = self._place_be_sl(symbol, pos_data)
            if be_price is not None:
                # New BE SL confirmed — now safe to cancel old SL
                self._cancel_open_sl_orders_except_latest(symbol, direction)
                self.state.update_position(key, {
                    "sl_price": be_price,
                    "be_raised": True,
                })
                notional = pos_data.get("notional_usd", 0)
                commission_usd = round(notional * self.commission_rate, 4)
                msg = ("<b>BE+FEES RAISED</b>  " + key
                       + "\\nEntry:  " + str(round(entry_price, 8))
                       + "\\nMark:   " + str(round(mark, 8))
                       + "\\nSL -> " + str(round(be_price, 8))
                       + "  (+" + str(round(self.commission_rate * 100, 3))
                       + "% covers $" + str(commission_usd) + " RT commission)")
                self.notifier.send(msg)
                logger.info(
                    "BE+fees raised: %s entry=%.8f mark=%.8f be_price=%.8f"
                    " (+%.4f%%) covers=$%.4f RT commission",
                    key, entry_price, mark, be_price,
                    self.commission_rate * 100, commission_usd)
            else:
                # Placement failed — old SL still intact (safe)
                logger.error(
                    "BE SL place FAILED for %s -- old SL preserved (safe)", key)
                self.notifier.send(
                    "<b>BE RAISE FAILED</b>  " + key
                    + "\\nNew SL rejected -- old SL still active")'''

    patch_file(pm, old_be, new_be,
               "Fix 2: check_breakeven place-then-cancel")

    # --- Fix 3: _tighten_sl_after_ttp — place-then-cancel ---
    old_tighten = '''        # Cancel existing SL orders then place tightened SL
        self._cancel_open_sl_orders(symbol, direction)
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
                self.state.update_position(key, {"sl_price": new_sl})
                logger.info("SL tightened: %s new_sl=%.8f orderId=%s", key, new_sl, order_id)
            else:
                logger.warning("SL tighten failed %s: code=%s msg=%s",
                               key, data.get("code"), data.get("msg"))
        except Exception as e:
            logger.warning("SL tighten error %s: %s", key, e)'''

    new_tighten = '''        # SAFE: place new SL first, cancel old ONLY after success
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
                # New SL confirmed — now safe to cancel old SL orders
                self._cancel_open_sl_orders_except_latest(symbol, direction)
                self.state.update_position(key, {"sl_price": new_sl})
                logger.info("SL tightened: %s new_sl=%.8f orderId=%s", key, new_sl, order_id)
            else:
                # Placement failed — old SL still intact (safe)
                logger.warning("SL tighten REJECTED %s: code=%s msg=%s -- old SL preserved",
                               key, data.get("code"), data.get("msg"))
        except Exception as e:
            logger.warning("SL tighten error %s: %s -- old SL preserved", key, e)'''

    patch_file(pm, old_tighten, new_tighten,
               "Fix 3: _tighten_sl_after_ttp place-then-cancel")

    # --- Fix 4: be_buffer from config instead of hardcoded 0.001 ---
    old_buffer = "        # 0.1% slippage buffer on top of commission to prevent negative fills\n        be_buffer = 0.001"
    new_buffer = "        # Slippage buffer on top of commission to prevent negative fills\n        be_buffer = self.config.get(\"position\", {}).get(\"be_buffer\", 0.002)"

    patch_file(pm, old_buffer, new_buffer,
               "Fix 4: configurable be_buffer (default 0.002)")

    # --- Fix 8: allOrders limit 20 -> 50 ---
    old_limit = '            params = {"symbol": symbol, "limit": "20"}'
    new_limit = '            params = {"symbol": symbol, "limit": "50"}'

    patch_file(pm, old_limit, new_limit,
               "Fix 8: allOrders limit 20 -> 50")

    # --- Fix 9: rename ttp_act variable to be_activation ---
    old_var = "        ttp_act = self.config.get(\"position\", {}).get(\"be_act\", 0.004)"
    new_var = "        be_activation = self.config.get(\"position\", {}).get(\"be_act\", 0.004)"

    patch_file(pm, old_var, new_var,
               "Fix 9a: rename ttp_act -> be_activation (declaration)")

    # Also rename the usages of ttp_act in check_breakeven
    text = pm.read_text(encoding="utf-8")
    # Replace ttp_act usages in the check_breakeven method body
    # There are two usages: activation_price calculations
    if "activation_price = entry_price * (1.0 + ttp_act)" in text:
        text = text.replace(
            "activation_price = entry_price * (1.0 + ttp_act)",
            "activation_price = entry_price * (1.0 + be_activation)")
        text = text.replace(
            "activation_price = entry_price * (1.0 - ttp_act)",
            "activation_price = entry_price * (1.0 - be_activation)")
        pm.write_text(text, encoding="utf-8")
        print("  PATCHED: Fix 9b: rename ttp_act usages -> be_activation")
        APPLIED.append("Fix 9b: rename ttp_act usages -> be_activation")
    else:
        print("  SKIP: Fix 9b (already renamed or not found)")

    # --- Add _cancel_open_sl_orders_except_latest helper method ---
    # This is needed by Fix 2 and Fix 3: cancels OLD SL orders but keeps the latest one
    helper_anchor = '''    def _cancel_open_sl_orders(self, symbol, direction):
        """Cancel any open STOP/STOP_MARKET orders for symbol+direction (not TP)."""'''

    helper_new = '''    def _cancel_open_sl_orders_except_latest(self, symbol, direction):
        """Cancel OLD SL orders for symbol+direction, keeping the most recent one."""
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
            if len(sl_orders) <= 1:
                return  # only the new SL exists, nothing to cancel
            # Sort by orderId (ascending) — cancel all except the last (newest)
            sl_orders.sort(key=lambda o: int(o.get("orderId", 0)))
            for o in sl_orders[:-1]:
                self._cancel_order(symbol, o.get("orderId"))
                logger.info("Cancelled old SL order %s for %s %s",
                            o.get("orderId"), symbol, direction)
        except Exception as e:
            logger.warning("cancel_old_sl_orders failed %s: %s", symbol, e)

    def _cancel_open_sl_orders(self, symbol, direction):
        """Cancel any open STOP/STOP_MARKET orders for symbol+direction (not TP)."""'''

    patch_file(pm, helper_anchor, helper_new,
               "Fix 2/3 helper: _cancel_open_sl_orders_except_latest")

    # Verify
    if not verify(pm):
        ERRORS.append("position_monitor.py")


# =====================================================================
# PATCH 5: main.py — commission fallback 0.001 -> 0.0016
# =====================================================================
def patch_main():
    """Fix commission fallback in main.py."""
    mp = ROOT / "main.py"
    print("\n=== main.py ===")
    backup(mp)

    old_comm = '    return 0.001  # fallback: 0.05% x 2 sides (BingX taker rate)'
    new_comm = '    return 0.0016  # fallback: 0.08% taker x 2 sides (BingX standard rate)'

    patch_file(mp, old_comm, new_comm,
               "Fix 5: commission fallback 0.001 -> 0.0016")

    if not verify(mp):
        ERRORS.append("main.py")


# =====================================================================
# PATCH 6: risk_gate.py — add max_atr_ratio check
# =====================================================================
def patch_risk_gate():
    """Add max_atr_ratio check to risk_gate.py."""
    rg = ROOT / "risk_gate.py"
    print("\n=== risk_gate.py ===")
    backup(rg)

    # Add max_atr_ratio to __init__
    old_init = '''        self.min_atr_ratio = config.get("min_atr_ratio", 0.003)
        self.cooldown_bars = config.get("cooldown_bars", 3)'''

    new_init = '''        self.min_atr_ratio = config.get("min_atr_ratio", 0.003)
        self.max_atr_ratio = config.get("max_atr_ratio", 0.015)
        self.cooldown_bars = config.get("cooldown_bars", 3)'''

    patch_file(rg, old_init, new_init,
               "Fix 6a: max_atr_ratio in __init__")

    # Update logger line to include max_atr
    old_log = '''        logger.info(
            "RiskGate: max_pos=%d max_trades=%d loss=%.1f atr=%.4f cooldown=%d",
            self.max_positions, self.max_daily_trades,
            self.daily_loss_limit, self.min_atr_ratio, self.cooldown_bars)'''

    new_log = '''        logger.info(
            "RiskGate: max_pos=%d max_trades=%d loss=%.1f atr=%.4f/%.4f cooldown=%d",
            self.max_positions, self.max_daily_trades,
            self.daily_loss_limit, self.min_atr_ratio, self.max_atr_ratio,
            self.cooldown_bars)'''

    patch_file(rg, old_log, new_log,
               "Fix 6b: log max_atr_ratio")

    # Add check 5b after check 5
    old_check5_end = '''        if atr_ratio < self.min_atr_ratio:
            reason = ("BLOCKED: Too Quiet (atr_ratio="
                      + str(round(atr_ratio, 6)) + ")")
            logger.info("Check 5 FAIL: %s", reason)
            return False, reason

        # Check 6: Daily trade limit'''

    new_check5_end = '''        if atr_ratio < self.min_atr_ratio:
            reason = ("BLOCKED: Too Quiet (atr_ratio="
                      + str(round(atr_ratio, 6)) + ")")
            logger.info("Check 5 FAIL: %s", reason)
            return False, reason

        # Check 5b: Max ATR ratio (blocks ultra-volatile coins)
        if self.max_atr_ratio and atr_ratio > self.max_atr_ratio:
            reason = ("BLOCKED: Too Volatile (atr_ratio="
                      + str(round(atr_ratio, 6))
                      + " > max=" + str(self.max_atr_ratio) + ")")
            logger.info("Check 5b FAIL: %s", reason)
            return False, reason

        # Check 6: Daily trade limit'''

    patch_file(rg, old_check5_end, new_check5_end,
               "Fix 6c: max_atr_ratio check 5b")

    if not verify(rg):
        ERRORS.append("risk_gate.py")


# =====================================================================
# PATCH 7: state_manager.py — add atr_at_entry + sl_price to trades.csv
# =====================================================================
def patch_state_manager():
    """Add atr_at_entry and sl_price columns to trades.csv."""
    sm = ROOT / "state_manager.py"
    print("\n=== state_manager.py ===")
    backup(sm)

    # Add columns to header
    old_header = '''                    writer.writerow([
                        "timestamp", "symbol", "direction", "grade",
                        "entry_price", "exit_price", "exit_reason",
                        "pnl_net", "quantity", "notional_usd",
                        "entry_time", "order_id",
                        "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct",
                        "ttp_exit_reason", "be_raised", "saw_green",
                    ])'''

    new_header = '''                    writer.writerow([
                        "timestamp", "symbol", "direction", "grade",
                        "entry_price", "exit_price", "exit_reason",
                        "pnl_net", "quantity", "notional_usd",
                        "entry_time", "order_id",
                        "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct",
                        "ttp_exit_reason", "be_raised", "saw_green",
                        "atr_at_entry", "sl_price",
                    ])'''

    patch_file(sm, old_header, new_header,
               "Fix 7a: atr_at_entry + sl_price CSV header")

    # Add columns to row data
    old_row_end = '''                    pos.get("be_raised", False),
                    "",  # saw_green: backfilled by run_trade_analysis.py
                ])'''

    new_row_end = '''                    pos.get("be_raised", False),
                    "",  # saw_green: backfilled by run_trade_analysis.py
                    pos.get("atr_at_entry", ""),
                    pos.get("sl_price", ""),
                ])'''

    patch_file(sm, old_row_end, new_row_end,
               "Fix 7b: atr_at_entry + sl_price CSV row")

    if not verify(sm):
        ERRORS.append("state_manager.py")


# =====================================================================
# PATCH: config.yaml — add be_buffer + max_atr_ratio
# =====================================================================
def patch_config():
    """Add be_buffer and max_atr_ratio to config.yaml."""
    cfg = ROOT / "config.yaml"
    print("\n=== config.yaml ===")
    backup(cfg)

    text = cfg.read_text(encoding="utf-8")

    # Add be_buffer under position section
    if "be_buffer:" not in text:
        old_be_auto = "  be_auto: true"
        new_be_auto = "  be_buffer: 0.002\n  be_auto: true"
        if old_be_auto in text:
            text = text.replace(old_be_auto, new_be_auto, 1)
            print("  PATCHED: config be_buffer: 0.002")
            APPLIED.append("Config: be_buffer: 0.002")
        else:
            print("  MISSING_ANCHOR: config be_buffer")
            SKIPPED.append("Config: be_buffer")
    else:
        print("  ALREADY_APPLIED: config be_buffer")

    # Add max_atr_ratio under risk section
    if "max_atr_ratio:" not in text:
        old_min_atr = "  min_atr_ratio: 0.003"
        new_min_atr = "  min_atr_ratio: 0.003\n  max_atr_ratio: 0.015"
        if old_min_atr in text:
            text = text.replace(old_min_atr, new_min_atr, 1)
            print("  PATCHED: config max_atr_ratio: 0.015")
            APPLIED.append("Config: max_atr_ratio: 0.015")
        else:
            print("  MISSING_ANCHOR: config max_atr_ratio")
            SKIPPED.append("Config: max_atr_ratio")
    else:
        print("  ALREADY_APPLIED: config max_atr_ratio")

    cfg.write_text(text, encoding="utf-8")


# =====================================================================
# MAIN
# =====================================================================
def main():
    """Run all patches."""
    print("=" * 60)
    print("v2 Mechanical Audit Fixes — Build Script")
    print("=" * 60)
    print("Root: " + str(ROOT))
    print("Timestamp: " + TS)

    patch_position_monitor()
    patch_main()
    patch_risk_gate()
    patch_state_manager()
    patch_config()

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print("Applied: " + str(len(APPLIED)))
    for a in APPLIED:
        print("  + " + a)
    if SKIPPED:
        print("Skipped: " + str(len(SKIPPED)))
        for s in SKIPPED:
            print("  ~ " + s)
    if ERRORS:
        print("ERRORS: " + str(len(ERRORS)))
        for e in ERRORS:
            print("  ! " + e)
        print("\nBUILD FAILED — syntax errors in: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("\nBUILD OK — all files compile clean")
        print("\nRun command:")
        print('  cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector-v2" && python main.py')


if __name__ == "__main__":
    main()
