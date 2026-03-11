"""
Build script: Mechanical Audit Fixes (2026-03-06)
7 fixes across 6 files. Creates .bak backups before patching.

Fixes:
  1. C1+C2: Always use actual fill price for PnL (position_monitor.py)
  2. C3: Capture MARKET order fills in WS listener (ws_listener.py)
  3. C2-supp: Store market close fill price for TTP (position_monitor.py)
  4. H2+H3: Fix BE buffer + commission fallback (position_monitor.py, main.py, config.yaml)
  5. M1: Add max_atr_ratio to risk gate (risk_gate.py, config.yaml)
  6. Data gap: Write atr_at_entry + sl_price to trades.csv (state_manager.py)
  7. M2+M3: Minor cleanup (position_monitor.py)
"""
import os
import sys
import shutil
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
APPLIED = []
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(filepath):
    """Create timestamped .bak copy."""
    src = Path(filepath)
    dst = src.with_suffix("." + TIMESTAMP + ".bak" + src.suffix)
    shutil.copy2(src, dst)
    print("  Backup: %s" % dst.name)


def patch(filepath, old, new, label):
    """Replace old with new in file. Reports APPLIED or MISSING."""
    p = Path(filepath)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        print("  MISSING_ANCHOR: %s" % label)
        ERRORS.append("MISSING_ANCHOR: %s in %s" % (label, p.name))
        return False
    if text.count(old) > 1:
        print("  AMBIGUOUS_ANCHOR: %s (found %d times)" % (label, text.count(old)))
        ERRORS.append("AMBIGUOUS: %s in %s" % (label, p.name))
        return False
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    print("  APPLIED: %s" % label)
    APPLIED.append(label)
    return True


def compile_check(filepath, label):
    """Run py_compile on file."""
    try:
        py_compile.compile(str(filepath), doraise=True)
        print("  py_compile PASS: %s" % Path(filepath).name)
        return True
    except py_compile.PyCompileError as e:
        print("  py_compile FAIL: %s -- %s" % (Path(filepath).name, e))
        ERRORS.append("py_compile FAIL: %s" % label)
        return False


# =========================================================================
# Fix 1: _detect_exit() -- always query allOrders for actual fill price first
# =========================================================================
print("\n=== Fix 1: Actual fill price in _detect_exit (C1+C2) ===")
PM = ROOT / "position_monitor.py"
backup(PM)

# Fix 1a: Rewrite _detect_exit to query filled orders FIRST
OLD_DETECT_EXIT = '''    def _detect_exit(self, symbol, pos_data):
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
                "Both SL and TP still open for %s \u2014 position may not be closed",
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
                    " \u2014 using SL price estimate", symbol)
        return exit_price, exit_reason'''

NEW_DETECT_EXIT = '''    def _detect_exit(self, symbol, pos_data):
        """Detect SL or TP hit. Always queries allOrders for actual fill price first.

        Priority: (1) stored TTP fill price, (2) allOrders avgPrice,
        (3) pending order inference for reason, (4) state price estimate.
        Returns (exit_price, exit_reason) or (None, None) on failure.
        """
        # TTP exit: use stored fill price if available, trail level as fallback
        if pos_data.get("ttp_exit_pending"):
            fill = pos_data.get("ttp_fill_price")
            if fill is not None:
                logger.info("TTP exit with fill price: %s %.8f", symbol, float(fill))
                return float(fill), "TTP_EXIT"
            trail = pos_data.get("ttp_trail_level")
            if trail is not None:
                logger.warning("TTP exit using trail_level estimate: %s %.8f", symbol, float(trail))
                return float(trail), "TTP_EXIT"
            return None, "TTP_EXIT"
        # Step 1: Query allOrders for ACTUAL fill price (most accurate)
        hist_price, hist_reason = self._fetch_filled_exit(symbol, pos_data)
        if hist_price is not None:
            # Clean up any orphaned pending orders
            self._cleanup_orphaned_orders(symbol, hist_reason)
            logger.info("Exit detected via allOrders: %s reason=%s price=%.8f",
                        symbol, hist_reason, hist_price)
            return hist_price, hist_reason
        # Step 2: Infer from pending orders (reason only, then try to get price)
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
            logger.info("Detected TP_HIT for %s (pending inference, price=estimate), cancelled %d SL orders",
                        symbol, len(sl_orders))
        elif tp_orders and not sl_orders:
            exit_reason = "SL_HIT"
            exit_price = pos_data.get("sl_price")
            for o in tp_orders:
                self._cancel_order(symbol, o.get("orderId"))
            logger.info("Detected SL_HIT for %s (pending inference, price=estimate), cancelled %d TP orders",
                        symbol, len(tp_orders))
        elif sl_orders and tp_orders:
            logger.warning(
                "Both SL and TP still open for %s \u2014 position may not be closed",
                symbol)
            return None, None
        else:
            exit_reason = "EXIT_UNKNOWN"
            exit_price = pos_data.get("sl_price")
            logger.warning(
                "No pending or filled SL/TP found for %s"
                " \u2014 using SL price estimate", symbol)
        return exit_price, exit_reason

    def _cleanup_orphaned_orders(self, symbol, exit_reason):
        """Cancel orphaned SL or TP orders after detecting exit via allOrders."""
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
            for o in orders:
                otype = o.get("type", "")
                if exit_reason == "SL_HIT" and "TAKE_PROFIT" in otype:
                    self._cancel_order(symbol, o.get("orderId"))
                elif exit_reason == "TP_HIT" and "STOP" in otype:
                    self._cancel_order(symbol, o.get("orderId"))
        except Exception as e:
            logger.warning("cleanup_orphaned_orders %s: %s", symbol, e)'''

patch(PM, OLD_DETECT_EXIT, NEW_DETECT_EXIT, "Fix1-detect_exit")


# =========================================================================
# Fix 3: _place_market_close returns fill price + check_ttp_closes stores it
# =========================================================================
print("\n=== Fix 3: Store TTP fill price (C2 supplement) ===")

OLD_PLACE_MARKET = '''    def _place_market_close(self, symbol, direction, quantity):
        """Place MARKET close order using positionSide (Hedge mode \u2014 no reduceOnly). Returns True on success."""
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
            return False'''

NEW_PLACE_MARKET = '''    def _place_market_close(self, symbol, direction, quantity):
        """Place MARKET close order using positionSide (Hedge mode). Returns dict with avgPrice on success, None on failure."""
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
                avg_price = float(_d.get("avgPrice", 0) or 0)
                logger.info("TTP market close placed: %s %s orderId=%s avgPrice=%.8f",
                            symbol, side, order_id, avg_price)
                return {"orderId": order_id, "avgPrice": avg_price}
            logger.error("TTP market close failed %s: code=%s msg=%s",
                         symbol, data.get("code"), data.get("msg"))
            return None
        except Exception as e:
            logger.error("TTP market close error %s: %s", symbol, e)
            return None'''

patch(PM, OLD_PLACE_MARKET, NEW_PLACE_MARKET, "Fix3-place_market_close")

# Fix check_ttp_closes to store fill price
OLD_TTP_CLOSES = '''            ok = self._place_market_close(symbol, direction, quantity)
            if ok:
                self.state.update_position(key, {
                    "ttp_close_pending": False,
                    "ttp_exit_pending": True,
                })
                logger.info("TTP close executed: %s", key)
            else:
                # Failed to place market close -- leave flag for retry
                logger.error("TTP close FAILED: %s -- will retry next loop", key)'''

NEW_TTP_CLOSES = '''            result = self._place_market_close(symbol, direction, quantity)
            if result is not None:
                fill_price = result.get("avgPrice", 0)
                updates = {
                    "ttp_close_pending": False,
                    "ttp_exit_pending": True,
                }
                if fill_price and fill_price > 0:
                    updates["ttp_fill_price"] = fill_price
                    logger.info("TTP close executed: %s fill=%.8f", key, fill_price)
                else:
                    logger.info("TTP close executed: %s (no fill price in response)", key)
                self.state.update_position(key, updates)
            else:
                # Failed to place market close -- leave flag for retry
                logger.error("TTP close FAILED: %s -- will retry next loop", key)'''

patch(PM, OLD_TTP_CLOSES, NEW_TTP_CLOSES, "Fix3-ttp_closes_store_fill")


# =========================================================================
# Fix 4: BE buffer configurable + commission fallback
# =========================================================================
print("\n=== Fix 4: BE buffer + commission fallback (H2+H3) ===")

OLD_BE_BUFFER = '''        # 0.1% slippage buffer on top of commission to prevent negative fills
        be_buffer = 0.001'''

NEW_BE_BUFFER = '''        # Slippage buffer on top of commission to prevent negative fills (configurable)
        be_buffer = self.config.get("position", {}).get("be_buffer", 0.002)'''

patch(PM, OLD_BE_BUFFER, NEW_BE_BUFFER, "Fix4-be_buffer_configurable")

# Commission fallback in main.py
MAIN = ROOT / "main.py"
backup(MAIN)

OLD_COMMISSION_FALLBACK = '''    return 0.001  # fallback: 0.05% x 2 sides (BingX taker rate)'''
NEW_COMMISSION_FALLBACK = '''    return 0.0016  # fallback: 0.08% taker x 2 sides (BingX standard rate)'''

patch(MAIN, OLD_COMMISSION_FALLBACK, NEW_COMMISSION_FALLBACK, "Fix4-commission_fallback")


# =========================================================================
# Fix 5: max_atr_ratio in risk_gate
# =========================================================================
print("\n=== Fix 5: max_atr_ratio cap (M1) ===")
RG = ROOT / "risk_gate.py"
backup(RG)

OLD_RISKGATE_INIT = '''        self.min_atr_ratio = config.get("min_atr_ratio", 0.003)
        self.cooldown_bars = config.get("cooldown_bars", 3)
        self.bar_duration_sec = config.get("bar_duration_sec", 300)
        logger.info(
            "RiskGate: max_pos=%d max_trades=%d loss=%.1f atr=%.4f cooldown=%d",
            self.max_positions, self.max_daily_trades,
            self.daily_loss_limit, self.min_atr_ratio, self.cooldown_bars)'''

NEW_RISKGATE_INIT = '''        self.min_atr_ratio = config.get("min_atr_ratio", 0.003)
        self.max_atr_ratio = config.get("max_atr_ratio", 0.015)
        self.cooldown_bars = config.get("cooldown_bars", 3)
        self.bar_duration_sec = config.get("bar_duration_sec", 300)
        logger.info(
            "RiskGate: max_pos=%d max_trades=%d loss=%.1f atr=%.4f-%.4f cooldown=%d",
            self.max_positions, self.max_daily_trades,
            self.daily_loss_limit, self.min_atr_ratio, self.max_atr_ratio,
            self.cooldown_bars)'''

patch(RG, OLD_RISKGATE_INIT, NEW_RISKGATE_INIT, "Fix5-riskgate_init")

OLD_ATR_CHECK = '''        if atr_ratio < self.min_atr_ratio:
            reason = ("BLOCKED: Too Quiet (atr_ratio="
                      + str(round(atr_ratio, 6)) + ")")
            logger.info("Check 5 FAIL: %s", reason)
            return False, reason

        # Check 6: Daily trade limit'''

NEW_ATR_CHECK = '''        if atr_ratio < self.min_atr_ratio:
            reason = ("BLOCKED: Too Quiet (atr_ratio="
                      + str(round(atr_ratio, 6)) + ")")
            logger.info("Check 5 FAIL: %s", reason)
            return False, reason

        # Check 5b: ATR too high (ultra-volatile, huge SL)
        if self.max_atr_ratio and atr_ratio > self.max_atr_ratio:
            reason = ("BLOCKED: Too Volatile (atr_ratio="
                      + str(round(atr_ratio, 6))
                      + " > max " + str(self.max_atr_ratio) + ")")
            logger.info("Check 5b FAIL: %s", reason)
            return False, reason

        # Check 6: Daily trade limit'''

patch(RG, OLD_ATR_CHECK, NEW_ATR_CHECK, "Fix5-max_atr_check")


# =========================================================================
# Fix 6: Write atr_at_entry + sl_price to trades.csv
# =========================================================================
print("\n=== Fix 6: atr_at_entry + sl_price in trades.csv ===")
SM = ROOT / "state_manager.py"
backup(SM)

OLD_CSV_HEADER = '''                    writer.writerow([
                        "timestamp", "symbol", "direction", "grade",
                        "entry_price", "exit_price", "exit_reason",
                        "pnl_net", "quantity", "notional_usd",
                        "entry_time", "order_id",
                        "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct",
                        "ttp_exit_reason", "be_raised", "saw_green",
                    ])'''

NEW_CSV_HEADER = '''                    writer.writerow([
                        "timestamp", "symbol", "direction", "grade",
                        "entry_price", "exit_price", "exit_reason",
                        "pnl_net", "quantity", "notional_usd",
                        "entry_time", "order_id",
                        "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct",
                        "ttp_exit_reason", "be_raised", "saw_green",
                        "atr_at_entry", "sl_price",
                    ])'''

patch(SM, OLD_CSV_HEADER, NEW_CSV_HEADER, "Fix6-csv_header")

OLD_CSV_ROW = '''                writer.writerow([
                    datetime.now(timezone.utc).isoformat(),
                    pos.get("symbol", ""),
                    pos.get("direction", ""),
                    pos.get("grade", ""),
                    pos.get("entry_price", ""),
                    exit_price,
                    exit_reason,
                    round(pnl_net, 4),
                    pos.get("quantity", ""),
                    pos.get("notional_usd", ""),
                    pos.get("entry_time", ""),
                    pos.get("order_id", ""),
                    ttp_activated,
                    ttp_extreme_pct,
                    ttp_trail_pct,
                    ttp_exit_reason_col,
                    pos.get("be_raised", False),
                    "",  # saw_green: backfilled by run_trade_analysis.py
                ])'''

NEW_CSV_ROW = '''                writer.writerow([
                    datetime.now(timezone.utc).isoformat(),
                    pos.get("symbol", ""),
                    pos.get("direction", ""),
                    pos.get("grade", ""),
                    pos.get("entry_price", ""),
                    exit_price,
                    exit_reason,
                    round(pnl_net, 4),
                    pos.get("quantity", ""),
                    pos.get("notional_usd", ""),
                    pos.get("entry_time", ""),
                    pos.get("order_id", ""),
                    ttp_activated,
                    ttp_extreme_pct,
                    ttp_trail_pct,
                    ttp_exit_reason_col,
                    pos.get("be_raised", False),
                    "",  # saw_green: backfilled by run_trade_analysis.py
                    pos.get("atr_at_entry", ""),
                    pos.get("sl_price", ""),
                ])'''

patch(SM, OLD_CSV_ROW, NEW_CSV_ROW, "Fix6-csv_row")


# =========================================================================
# Fix 7: Minor cleanup (M2 variable name, M3 allOrders limit)
# =========================================================================
print("\n=== Fix 7: Minor cleanup (M2+M3) ===")

OLD_BE_VARNAME = '''        ttp_act = self.config.get("position", {}).get("be_act", 0.004)
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
                activation_price = entry_price * (1.0 + ttp_act)
                triggered = mark >= activation_price
            else:
                activation_price = entry_price * (1.0 - ttp_act)
                triggered = mark <= activation_price'''

NEW_BE_VARNAME = '''        be_activation = self.config.get("position", {}).get("be_act", 0.004)
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
                triggered = mark <= activation_price'''

patch(PM, OLD_BE_VARNAME, NEW_BE_VARNAME, "Fix7-be_varname")

OLD_LIMIT = '''            params = {"symbol": symbol, "limit": "20"}'''
NEW_LIMIT = '''            params = {"symbol": symbol, "limit": "50"}'''

patch(PM, OLD_LIMIT, NEW_LIMIT, "Fix7-allorders_limit")


# =========================================================================
# Fix 2: WS listener captures MARKET fills (C3)
# =========================================================================
print("\n=== Fix 2: WS MARKET fill capture (C3) ===")
WS = ROOT / "ws_listener.py"
backup(WS)

OLD_PARSE_FILL = '''        order_type = order.get("o", "")
        if "TAKE_PROFIT" in order_type:
            reason = "TP_HIT"
        elif "STOP" in order_type:
            reason = "SL_HIT"
        else:
            return None'''

NEW_PARSE_FILL = '''        order_type = order.get("o", "")
        side = order.get("S", "")
        pos_side = order.get("ps", "")
        if "TAKE_PROFIT" in order_type:
            reason = "TP_HIT"
        elif "STOP" in order_type and "TRAILING" not in order_type:
            reason = "SL_HIT"
        elif "TRAILING" in order_type:
            reason = "TRAILING_EXIT"
        elif order_type == "MARKET":
            # MARKET fill: could be entry or TTP close
            # If side is opposite to positionSide, it is a close
            is_close = ((pos_side == "LONG" and side == "SELL")
                        or (pos_side == "SHORT" and side == "BUY"))
            if is_close:
                reason = "TTP_EXIT"
            else:
                return None  # entry fill, not relevant
        else:
            return None'''

patch(WS, OLD_PARSE_FILL, NEW_PARSE_FILL, "Fix2-ws_market_fill")


# =========================================================================
# Config: add be_buffer and max_atr_ratio
# =========================================================================
print("\n=== Config patches ===")
CFG = ROOT / "config.yaml"
backup(CFG)

OLD_CFG_BE = '''  be_auto: true'''
NEW_CFG_BE = '''  be_auto: true
  be_buffer: 0.002'''

patch(CFG, OLD_CFG_BE, NEW_CFG_BE, "Config-be_buffer")

OLD_CFG_ATR = '''  min_atr_ratio: 0.003'''
NEW_CFG_ATR = '''  min_atr_ratio: 0.003
  max_atr_ratio: 0.015'''

patch(CFG, OLD_CFG_ATR, NEW_CFG_ATR, "Config-max_atr_ratio")


# =========================================================================
# py_compile all modified files
# =========================================================================
print("\n=== py_compile checks ===")
for f in [PM, MAIN, RG, SM, WS]:
    compile_check(f, f.name)


# =========================================================================
# Summary
# =========================================================================
print("\n" + "=" * 60)
print("BUILD SUMMARY")
print("=" * 60)
print("Applied: %d patches" % len(APPLIED))
for a in APPLIED:
    print("  [OK] %s" % a)
if ERRORS:
    print("\nErrors: %d" % len(ERRORS))
    for e in ERRORS:
        print("  [FAIL] %s" % e)
else:
    print("\nErrors: 0")
print("\nBot restart required to activate fixes.")
print('Run: cd "%s" && python main.py' % ROOT)
