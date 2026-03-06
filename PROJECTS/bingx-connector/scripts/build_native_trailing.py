"""
Build script: bingx-connector-v2 with native trailing stop support.
Copies bingx-connector to bingx-connector-v2, applies 6 file patches + config.
Run: python scripts/build_native_trailing.py
"""
import os
import sys
import shutil
import py_compile
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent  # bingx-connector/
DST = PROJ.parent / "bingx-connector-v2"
ERRORS = []


def safe_replace(filepath, old, new, description):
    """Replace old with new in filepath. Asserts old exists exactly once."""
    content = filepath.read_text(encoding="utf-8")
    count = content.count(old)
    if count == 0:
        ERRORS.append("PATCH FAILED (not found): " + description + " in " + filepath.name)
        print("  FAILED (not found): " + description)
        return False
    if count > 1:
        ERRORS.append("PATCH FAILED (found " + str(count) + "x): " + description + " in " + filepath.name)
        print("  FAILED (found " + str(count) + "x): " + description)
        return False
    content = content.replace(old, new, 1)
    filepath.write_text(content, encoding="utf-8")
    print("  PATCHED: " + description)
    return True


def compile_check(filepath):
    """Run py_compile on a file. Appends to ERRORS on failure."""
    try:
        py_compile.compile(str(filepath), doraise=True)
        print("  COMPILE OK: " + filepath.name)
        return True
    except py_compile.PyCompileError as e:
        ERRORS.append("COMPILE FAILED: " + filepath.name + " -- " + str(e))
        print("  COMPILE FAILED: " + filepath.name)
        return False


def patch_executor(fp):
    """Patch executor.py for native trailing support."""
    print("\n--- Patching executor.py ---")

    # E1: Constructor — add ttp_mode, ttp_act, ttp_dist
    safe_replace(fp,
        '        self.trailing_activation_atr_mult = position_config.get(\n'
        '            "trailing_activation_atr_mult", None)\n'
        '        logger.info("Executor: margin=%.0f leverage=%d trail_rate=%s",\n'
        '                     self.margin_usd, self.leverage, self.trailing_rate)',

        '        self.trailing_activation_atr_mult = position_config.get(\n'
        '            "trailing_activation_atr_mult", None)\n'
        '        self.ttp_mode = position_config.get("ttp_mode", "engine")\n'
        '        self.ttp_act = position_config.get("ttp_act", 0.008)\n'
        '        self.ttp_dist = position_config.get("ttp_dist", 0.003)\n'
        '        logger.info("Executor: margin=%.0f leverage=%d trail_rate=%s ttp_mode=%s",\n'
        '                     self.margin_usd, self.leverage, self.trailing_rate, self.ttp_mode)',
        "E1: constructor add ttp_mode/act/dist")

    # E2: _place_trailing_order — add price_rate param
    safe_replace(fp,
        '    def _place_trailing_order(self, symbol, direction, quantity, activation_price):\n'
        '        """Place TRAILING_STOP_MARKET order. Returns order_id str or None."""\n'
        '        close_side = "SELL" if direction == "LONG" else "BUY"\n'
        '        params = {\n'
        '            "symbol": symbol,\n'
        '            "side": close_side,\n'
        '            "positionSide": direction,\n'
        '            "type": "TRAILING_STOP_MARKET",\n'
        '            "quantity": str(quantity),\n'
        '            "priceRate": str(self.trailing_rate),\n'
        '            "activationPrice": str(round(activation_price, 8)),\n'
        '            "workingType": self.sl_working_type,\n'
        '        }',

        '    def _place_trailing_order(self, symbol, direction, quantity, activation_price, price_rate=None):\n'
        '        """Place TRAILING_STOP_MARKET order. Returns order_id str or None."""\n'
        '        close_side = "SELL" if direction == "LONG" else "BUY"\n'
        '        rate = price_rate if price_rate is not None else self.trailing_rate\n'
        '        if rate is None:\n'
        '            logger.error("Trailing order: no priceRate for %s", symbol)\n'
        '            return None\n'
        '        params = {\n'
        '            "symbol": symbol,\n'
        '            "side": close_side,\n'
        '            "positionSide": direction,\n'
        '            "type": "TRAILING_STOP_MARKET",\n'
        '            "quantity": str(quantity),\n'
        '            "priceRate": str(rate),\n'
        '            "activationPrice": str(round(activation_price, 8)),\n'
        '            "workingType": self.sl_working_type,\n'
        '        }',
        "E2: _place_trailing_order add price_rate param")

    # E3: Trailing log line — use local 'rate' variable
    safe_replace(fp,
        '        logger.info("Trailing order placed: %s %s act=%.6f rate=%.4f id=%s",\n'
        '                    symbol, direction, activation_price,\n'
        '                    self.trailing_rate, order_id)',

        '        logger.info("Trailing order placed: %s %s act=%.6f rate=%.4f id=%s",\n'
        '                    symbol, direction, activation_price,\n'
        '                    rate, order_id)',
        "E3: trailing log use local rate variable")

    # E4: Entry trailing block — dual-path (native vs ATR)
    safe_replace(fp,
        '        act_price = None\n'
        '        if self.trailing_rate and self.trailing_activation_atr_mult and signal.atr:\n'
        '            effective_entry = fill_price if fill_price > 0 else mark_price\n'
        '            offset = signal.atr * self.trailing_activation_atr_mult\n'
        '            act_price = (effective_entry + offset if signal.direction == "LONG"\n'
        '                         else effective_entry - offset)\n'
        '            trail_id = self._place_trailing_order(\n'
        '                symbol, signal.direction, quantity, act_price)\n'
        '            if trail_id and trail_id != "unknown":\n'
        '                self.state.update_position(key, {\n'
        '                    "trailing_order_id": trail_id,\n'
        '                    "trailing_activation_price": act_price,\n'
        '                })',

        '        act_price = None\n'
        '        trail_id = None\n'
        '        effective_entry = fill_price if fill_price > 0 else mark_price\n'
        '        if self.ttp_mode == "native":\n'
        '            if signal.direction == "LONG":\n'
        '                act_price = effective_entry * (1.0 + self.ttp_act)\n'
        '            else:\n'
        '                act_price = effective_entry * (1.0 - self.ttp_act)\n'
        '            trail_id = self._place_trailing_order(\n'
        '                symbol, signal.direction, quantity, act_price,\n'
        '                price_rate=self.ttp_dist)\n'
        '            if trail_id and trail_id != "unknown":\n'
        '                self.state.update_position(key, {\n'
        '                    "trailing_order_id": trail_id,\n'
        '                    "trailing_activation_price": act_price,\n'
        '                    "ttp_mode": "native",\n'
        '                })\n'
        '                logger.info("Native trailing placed: %s act=%.6f dist=%.4f id=%s",\n'
        '                            key, act_price, self.ttp_dist, trail_id)\n'
        '            else:\n'
        '                logger.error("Native trailing FAILED for %s -- SL remains as safety net", key)\n'
        '        elif self.trailing_rate and self.trailing_activation_atr_mult and signal.atr:\n'
        '            offset = signal.atr * self.trailing_activation_atr_mult\n'
        '            act_price = (effective_entry + offset if signal.direction == "LONG"\n'
        '                         else effective_entry - offset)\n'
        '            trail_id = self._place_trailing_order(\n'
        '                symbol, signal.direction, quantity, act_price)\n'
        '            if trail_id and trail_id != "unknown":\n'
        '                self.state.update_position(key, {\n'
        '                    "trailing_order_id": trail_id,\n'
        '                    "trailing_activation_price": act_price,\n'
        '                })',
        "E4: entry trailing dual-path (native vs ATR)")

    # E5: Notification — show NativeTrail info
    safe_replace(fp,
        '        if act_price is not None:\n'
        '            entry_msg += ("  Trail: act=" + str(round(act_price, 6))\n'
        '                          + " @" + str(int(self.trailing_rate * 100)) + "%")',

        '        if act_price is not None and trail_id:\n'
        '            if self.ttp_mode == "native":\n'
        '                entry_msg += ("  NativeTrail: act=" + str(round(act_price, 6))\n'
        '                              + " cb=" + str(round(self.ttp_dist * 100, 2)) + "%")\n'
        '            elif self.trailing_rate:\n'
        '                entry_msg += ("  Trail: act=" + str(round(act_price, 6))\n'
        '                              + " @" + str(int(self.trailing_rate * 100)) + "%")',
        "E5: notification NativeTrail info")


def patch_signal_engine(fp):
    """Patch signal_engine.py for native trailing support."""
    print("\n--- Patching signal_engine.py ---")

    # S1: Constructor — add ttp_mode
    safe_replace(fp,
        '        self.ttp_dist = _ttp.get("ttp_dist", 0.003)\n'
        '        self.ttp_engines = {}  # keyed by position key e.g. "BTCUSDT_LONG"\n'
        '        logger.info(\n'
        '            "StrategyAdapter: plugin=%s v%s warmup=%d grades=%s",\n'
        '            self.plugin.get_name(), self.plugin.get_version(),\n'
        '            self.warmup_needed, str(self.allowed_grades))',

        '        self.ttp_dist = _ttp.get("ttp_dist", 0.003)\n'
        '        self.ttp_mode = _ttp.get("ttp_mode", "engine")\n'
        '        self.ttp_engines = {}  # keyed by position key e.g. "BTCUSDT_LONG"\n'
        '        logger.info(\n'
        '            "StrategyAdapter: plugin=%s v%s warmup=%d grades=%s ttp_mode=%s",\n'
        '            self.plugin.get_name(), self.plugin.get_version(),\n'
        '            self.warmup_needed, str(self.allowed_grades), self.ttp_mode)',
        "S1: constructor add ttp_mode")

    # S2: _evaluate_ttp_for_symbol — early return for native
    safe_replace(fp,
        '        if not self.ttp_enabled:\n'
        '            return\n'
        '        try:\n'
        '            latest = ohlcv_df.iloc[-1]',

        '        if not self.ttp_enabled:\n'
        '            return\n'
        '        if self.ttp_mode == "native":\n'
        '            return\n'
        '        try:\n'
        '            latest = ohlcv_df.iloc[-1]',
        "S2: skip TTP engine in native mode")


def patch_position_monitor(fp):
    """Patch position_monitor.py for native trailing support."""
    print("\n--- Patching position_monitor.py ---")

    # P1: Constructor — add ttp_mode
    safe_replace(fp,
        '        logger.info("PositionMonitor: loss=%.1f reset_h=%d commission=%.6f",\n'
        '                     self.daily_loss_limit, self.daily_summary_hour,\n'
        '                     self.commission_rate)',

        '        self.ttp_mode = config.get("position", {}).get("ttp_mode", "engine")\n'
        '        logger.info("PositionMonitor: loss=%.1f reset_h=%d commission=%.6f ttp_mode=%s",\n'
        '                     self.daily_loss_limit, self.daily_summary_hour,\n'
        '                     self.commission_rate, self.ttp_mode)',
        "P1: constructor add ttp_mode")

    # P2: _detect_exit — trailing order classification + native detection
    safe_replace(fp,
        '        sl_orders = []\n'
        '        tp_orders = []\n'
        '        for o in orders:\n'
        '            otype = o.get("type", "")\n'
        '            if "TAKE_PROFIT" in otype:\n'
        '                tp_orders.append(o)\n'
        '            elif "STOP" in otype:\n'
        '                sl_orders.append(o)\n'
        '        if sl_orders and not tp_orders:',

        '        sl_orders = []\n'
        '        tp_orders = []\n'
        '        trailing_orders = []\n'
        '        for o in orders:\n'
        '            otype = o.get("type", "")\n'
        '            if "TAKE_PROFIT" in otype:\n'
        '                tp_orders.append(o)\n'
        '            elif otype == "TRAILING_STOP_MARKET":\n'
        '                trailing_orders.append(o)\n'
        '            elif "STOP" in otype:\n'
        '                sl_orders.append(o)\n'
        '        # Native trailing detection: trailing fired if not in open orders\n'
        '        if self.ttp_mode == "native" and pos_data.get("trailing_order_id"):\n'
        '            if not trailing_orders:\n'
        '                for o in sl_orders + tp_orders:\n'
        '                    self._cancel_order(symbol, o.get("orderId"))\n'
        '                logger.info("Detected TRAILING_EXIT for %s, cancelled %d orphaned orders",\n'
        '                            symbol, len(sl_orders) + len(tp_orders))\n'
        '                hist_price, _ = self._fetch_filled_exit(symbol, pos_data)\n'
        '                if hist_price:\n'
        '                    return hist_price, "TRAILING_EXIT"\n'
        '                return None, "TRAILING_EXIT"\n'
        '        if sl_orders and not tp_orders:',
        "P2: _detect_exit trailing order classification + native detection")

    # P3: _fetch_filled_exit — TRAILING_STOP_MARKET before generic STOP
    safe_replace(fp,
        '                if "STOP" in otype:\n'
        '                    logger.info(\n'
        '                        "Found filled SL order for %s avgPrice=%.6f",\n'
        '                        symbol, avg_price)\n'
        '                    return avg_price, "SL_HIT"',

        '                if otype == "TRAILING_STOP_MARKET":\n'
        '                    logger.info(\n'
        '                        "Found filled TRAILING order for %s avgPrice=%.6f",\n'
        '                        symbol, avg_price)\n'
        '                    return avg_price, "TRAILING_EXIT"\n'
        '                if "STOP" in otype:\n'
        '                    logger.info(\n'
        '                        "Found filled SL order for %s avgPrice=%.6f",\n'
        '                        symbol, avg_price)\n'
        '                    return avg_price, "SL_HIT"',
        "P3: _fetch_filled_exit TRAILING_STOP_MARKET detection")

    # P4: _cancel_open_sl_orders — exclude TRAILING_STOP_MARKET
    safe_replace(fp,
        '                if ("STOP" in otype and "TAKE_PROFIT" not in otype\n'
        '                        and pos_side == direction):\n'
        '                    self._cancel_order(symbol, o.get("orderId"))',

        '                if ("STOP" in otype and "TAKE_PROFIT" not in otype\n'
        '                        and otype != "TRAILING_STOP_MARKET"\n'
        '                        and pos_side == direction):\n'
        '                    self._cancel_order(symbol, o.get("orderId"))',
        "P4: _cancel_open_sl_orders exclude TRAILING_STOP_MARKET")

    # P5: check_ttp_closes — early return for native
    safe_replace(fp,
        '    def check_ttp_closes(self):\n'
        '        """Process TTP close flags set by signal_engine. Executes market close on exchange."""\n'
        '        positions = self.state.get_open_positions()',

        '    def check_ttp_closes(self):\n'
        '        """Process TTP close flags set by signal_engine. Executes market close on exchange."""\n'
        '        if self.ttp_mode == "native":\n'
        '            return\n'
        '        positions = self.state.get_open_positions()',
        "P5: check_ttp_closes early return for native")

    # P6: check_ttp_sl_tighten — early return for native
    safe_replace(fp,
        '    def check_ttp_sl_tighten(self):\n'
        '        """Tighten SL progressively for all ACTIVATED TTP positions."""\n'
        '        positions = self.state.get_open_positions()',

        '    def check_ttp_sl_tighten(self):\n'
        '        """Tighten SL progressively for all ACTIVATED TTP positions."""\n'
        '        if self.ttp_mode == "native":\n'
        '            return\n'
        '        positions = self.state.get_open_positions()',
        "P6: check_ttp_sl_tighten early return for native")


def patch_ws_listener(fp):
    """Patch ws_listener.py for TRAILING_STOP_MARKET detection."""
    print("\n--- Patching ws_listener.py ---")

    safe_replace(fp,
        '        if "TAKE_PROFIT" in order_type:\n'
        '            reason = "TP_HIT"\n'
        '        elif "STOP" in order_type:\n'
        '            reason = "SL_HIT"\n'
        '        else:\n'
        '            return None',

        '        if "TAKE_PROFIT" in order_type:\n'
        '            reason = "TP_HIT"\n'
        '        elif order_type == "TRAILING_STOP_MARKET":\n'
        '            reason = "TRAILING_EXIT"\n'
        '        elif "STOP" in order_type:\n'
        '            reason = "SL_HIT"\n'
        '        else:\n'
        '            return None',
        "W1: TRAILING_STOP_MARKET fill detection")


def patch_state_manager(fp):
    """Patch state_manager.py for TRAILING_EXIT in trades.csv."""
    print("\n--- Patching state_manager.py ---")

    safe_replace(fp,
        '                ttp_exit_reason_col = "TTP_CLOSE" if exit_reason == "TTP_EXIT" else ""',

        '                if exit_reason == "TTP_EXIT":\n'
        '                    ttp_exit_reason_col = "TTP_CLOSE"\n'
        '                elif exit_reason == "TRAILING_EXIT":\n'
        '                    ttp_exit_reason_col = "TRAILING_EXIT"\n'
        '                else:\n'
        '                    ttp_exit_reason_col = ""',
        "SM1: TRAILING_EXIT in trades.csv ttp_exit_reason")


def patch_config(fp):
    """Patch config.yaml — add ttp_mode: native."""
    print("\n--- Patching config.yaml ---")

    safe_replace(fp,
        '  ttp_enabled: true\n'
        '  sl_trail_pct_post_ttp:',

        '  ttp_enabled: true\n'
        '  ttp_mode: native\n'
        '  sl_trail_pct_post_ttp:',
        "C1: add ttp_mode: native")


def main():
    """Build bingx-connector-v2 with native trailing support."""
    print("=" * 60)
    print("BUILD: bingx-connector-v2 (native trailing stop)")
    print("=" * 60)

    # Step 1: Check source exists
    if not PROJ.exists():
        print("ERROR: Source not found: " + str(PROJ))
        sys.exit(1)

    # Step 2: Check DST doesn't exist
    if DST.exists():
        print("ERROR: " + str(DST) + " already exists.")
        print("Remove it first: rmdir /s /q \"" + str(DST) + "\"")
        sys.exit(1)

    # Step 3: Copy entire directory (exclude runtime files)
    print("\nCopying " + str(PROJ) + "\n    -> " + str(DST))

    def ignore_fn(directory, files):
        """Ignore runtime files and caches."""
        ignored = set()
        for f in files:
            if f in ("state.json", "state.json.tmp", "trades.csv",
                     "bot-status.json", "bot-status.tmp",
                     "__pycache__"):
                ignored.add(f)
            if f == "logs":
                ignored.add(f)
        return ignored

    shutil.copytree(str(PROJ), str(DST), ignore=ignore_fn)
    print("Copy complete.")

    # Step 4: Apply patches to copied files
    patch_executor(DST / "executor.py")
    patch_signal_engine(DST / "signal_engine.py")
    patch_position_monitor(DST / "position_monitor.py")
    patch_ws_listener(DST / "ws_listener.py")
    patch_state_manager(DST / "state_manager.py")
    patch_config(DST / "config.yaml")

    # Step 5: py_compile all patched .py files
    print("\n--- py_compile checks ---")
    patched_py = [
        "executor.py",
        "signal_engine.py",
        "position_monitor.py",
        "ws_listener.py",
        "state_manager.py",
        "main.py",
    ]
    for name in patched_py:
        compile_check(DST / name)

    # Step 6: Create logs directory
    (DST / "logs").mkdir(exist_ok=True)

    # Step 7: Report
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    if ERRORS:
        print("FAILURES: " + str(len(ERRORS)))
        for e in ERRORS:
            print("  " + e)
        sys.exit(1)
    else:
        print("ALL PATCHES APPLIED + COMPILED SUCCESSFULLY")
        print()
        print("v2 bot location: " + str(DST))
        print()
        print("To run (after stopping v1):")
        print('  cd "' + str(DST) + '"')
        print("  python main.py")
        print()
        print("Config diff from v1:")
        print("  + ttp_mode: native  (exchange-managed trailing)")
        print("  = ttp_act: 0.008    (activation at +0.8%)")
        print("  = ttp_dist: 0.003   (0.3% callback rate)")
        print("  = be_act: 0.004     (BE raise at +0.4% -- still active)")


if __name__ == "__main__":
    main()
