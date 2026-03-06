"""
Build Phase 2: Bot core fixes.

Patches applied:
  P2-A: position_monitor.py -- remove reduceOnly from _place_market_close()
  P2-B: state_manager.py    -- add TTP + BE columns to _append_trade()
  P2-C: position_monitor.py -- add _tighten_sl_after_ttp() + wire into check_ttp_closes()
  P2-D: config.yaml         -- add sl_trail_pct_post_ttp key

STOP THE BOT before running this script.
Run: python scripts/build_phase2_bot_fixes.py
"""
import py_compile
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []


def verify(path: Path, label: str) -> bool:
    """Syntax-check and AST-parse; print result."""
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        print("  OK: " + label)
        return True
    except (py_compile.PyCompileError, SyntaxError) as e:
        print("  FAIL: " + label + " -- " + str(e))
        ERRORS.append(label)
        return False


def safe_replace(source: str, old: str, new: str, label: str) -> str:
    """Replace old with new; abort if old not found exactly once."""
    count = source.count(old)
    if count == 0:
        print("  PATCH MISSING ANCHOR: " + label)
        ERRORS.append("ANCHOR:" + label)
        return source
    if count > 1:
        print("  PATCH AMBIGUOUS (" + str(count) + " matches): " + label)
        ERRORS.append("AMBIGUOUS:" + label)
        return source
    print("  PATCH OK: " + label)
    return source.replace(old, new, 1)


# ---------------------------------------------------------------------------
# P2-A + P2-C: position_monitor.py
# ---------------------------------------------------------------------------
pm_path = ROOT / "position_monitor.py"
pm_src = pm_path.read_text(encoding="utf-8")

# P2-A: Remove reduceOnly from _place_market_close()
pm_src = safe_replace(
    pm_src,
    '''    def _place_market_close(self, symbol, direction, quantity):
        """Place MARKET reduceOnly close order. Returns True on success."""
        side = "SELL" if direction == "LONG" else "BUY"
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": direction,
            "type": "MARKET",
            "quantity": str(quantity),
            "reduceOnly": "true",
        }''',
    '''    def _place_market_close(self, symbol, direction, quantity):
        """Place MARKET close order using positionSide (Hedge mode — no reduceOnly). Returns True on success."""
        side = "SELL" if direction == "LONG" else "BUY"
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": direction,
            "type": "MARKET",
            "quantity": str(quantity),
        }''',
    "P2-A: remove reduceOnly from _place_market_close",
)

# P2-C: Add _tighten_sl_after_ttp() method and wire into check_ttp_closes()
# Insert the new method just before check_ttp_closes
TTP_TIGHTEN_METHOD = '''
    def _tighten_sl_after_ttp(self, key, pos_data, mark_price):
        """Progressive SL tightening once TTP is ACTIVATED.

        Trails SL toward current_extreme * (1 - sl_trail_pct) for LONG
        or current_extreme * (1 + sl_trail_pct) for SHORT.
        Only moves SL in the favourable direction. Rate-limited: only
        fires when new level is >=0.1% better than current SL.
        sl_trail_pct_post_ttp in config (default 0.003 = 0.3%). Set to
        null to disable.
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

        # Cancel existing SL orders then place tightened SL
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
                order_id = str(data.get("data", {}).get("orderId", "?"))
                self.state.update_position(key, {"sl_price": new_sl})
                logger.info("SL tightened: %s new_sl=%.8f orderId=%s", key, new_sl, order_id)
            else:
                logger.warning("SL tighten failed %s: code=%s msg=%s",
                               key, data.get("code"), data.get("msg"))
        except Exception as e:
            logger.warning("SL tighten error %s: %s", key, e)

'''

pm_src = safe_replace(
    pm_src,
    "    def check_ttp_closes(self):",
    TTP_TIGHTEN_METHOD + "    def check_ttp_closes(self):",
    "P2-C: insert _tighten_sl_after_ttp method",
)

# Wire tightening into check_ttp_closes after the ttp_close_pending skip block
# After the loop iterates through positions, we need an additional loop that runs
# _tighten_sl_after_ttp for positions where ttp_state==ACTIVATED but no close pending.
# Insert after the closing brace of check_ttp_closes.
# Find the method that follows check_ttp_closes to use as anchor.
pm_src = safe_replace(
    pm_src,
    "    def _cancel_all_orders_for_symbol(self, symbol, direction):",
    '''    def check_ttp_sl_tighten(self):
        """Tighten SL progressively for all ACTIVATED TTP positions."""
        positions = self.state.get_open_positions()
        for key, pos in positions.items():
            if pos.get("ttp_state") != "ACTIVATED":
                continue
            if pos.get("ttp_close_pending"):
                continue  # TTP close already queued — don't move SL
            symbol    = pos.get("symbol", key.rsplit("_", 1)[0])
            direction = pos.get("direction", "LONG")
            mark = self._fetch_mark_price_pm(symbol)
            if mark and mark > 0:
                self._tighten_sl_after_ttp(key, pos, mark)

    def _cancel_all_orders_for_symbol(self, symbol, direction):''',
    "P2-C: add check_ttp_sl_tighten public method",
)

pm_path.write_text(pm_src, encoding="utf-8")
verify(pm_path, "position_monitor.py")


# ---------------------------------------------------------------------------
# P2-B: state_manager.py — add TTP + BE columns to _append_trade()
# ---------------------------------------------------------------------------
sm_path = ROOT / "state_manager.py"
sm_src = sm_path.read_text(encoding="utf-8")

sm_src = safe_replace(
    sm_src,
    '''    def _append_trade(self, pos, exit_price, exit_reason, pnl_net):
        """Append one trade row to trades.csv."""
        file_exists = self.trades_path.exists()
        try:
            with open(self.trades_path, "a", newline="",
                       encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        "timestamp", "symbol", "direction", "grade",
                        "entry_price", "exit_price", "exit_reason",
                        "pnl_net", "quantity", "notional_usd",
                        "entry_time", "order_id",
                    ])
                writer.writerow([
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
                ])
        except OSError as e:
            logger.error("trades.csv append failed: %s", e)''',
    '''    def _append_trade(self, pos, exit_price, exit_reason, pnl_net):
        """Append one trade row to trades.csv (includes TTP + BE columns)."""
        file_exists = self.trades_path.exists()
        try:
            with open(self.trades_path, "a", newline="",
                       encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow([
                        "timestamp", "symbol", "direction", "grade",
                        "entry_price", "exit_price", "exit_reason",
                        "pnl_net", "quantity", "notional_usd",
                        "entry_time", "order_id",
                        "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct",
                        "ttp_exit_reason", "be_raised", "saw_green",
                    ])
                # Compute TTP stats from position data at close time
                ttp_state    = pos.get("ttp_state", "")
                ttp_activated = ttp_state in ("ACTIVATED", "CLOSED")
                entry_p      = float(pos.get("entry_price") or 0)
                direction_p  = pos.get("direction", "LONG")
                ttp_extreme  = pos.get("ttp_extreme")
                ttp_trail    = pos.get("ttp_trail_level")
                ttp_extreme_pct = ""
                ttp_trail_pct   = ""
                if ttp_extreme and entry_p > 0:
                    raw_ext = float(ttp_extreme)
                    if direction_p == "LONG":
                        ttp_extreme_pct = round((raw_ext - entry_p) / entry_p * 100, 4)
                    else:
                        ttp_extreme_pct = round((entry_p - raw_ext) / entry_p * 100, 4)
                if ttp_trail and entry_p > 0:
                    raw_trail = float(ttp_trail)
                    if direction_p == "LONG":
                        ttp_trail_pct = round((raw_trail - entry_p) / entry_p * 100, 4)
                    else:
                        ttp_trail_pct = round((entry_p - raw_trail) / entry_p * 100, 4)
                ttp_exit_reason_col = "TTP_CLOSE" if exit_reason == "TTP_EXIT" else ""
                writer.writerow([
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
                ])
        except OSError as e:
            logger.error("trades.csv append failed: %s", e)''',
    "P2-B: add TTP + BE columns to _append_trade",
)

sm_path.write_text(sm_src, encoding="utf-8")
verify(sm_path, "state_manager.py")


# ---------------------------------------------------------------------------
# P2-D: config.yaml — add sl_trail_pct_post_ttp key
# ---------------------------------------------------------------------------
cfg_path = ROOT / "config.yaml"
cfg_src = cfg_path.read_text(encoding="utf-8")

if "sl_trail_pct_post_ttp" in cfg_src:
    print("  SKIP P2-D: sl_trail_pct_post_ttp already in config.yaml")
else:
    cfg_src = safe_replace(
        cfg_src,
        "  ttp_enabled: true",
        "  ttp_enabled: true\n  sl_trail_pct_post_ttp: 0.003   # 0.3% trail after TTP activates (null = disabled)",
        "P2-D: add sl_trail_pct_post_ttp to config.yaml",
    )
    cfg_path.write_text(cfg_src, encoding="utf-8")
    print("  OK: config.yaml (sl_trail_pct_post_ttp added)")


# ---------------------------------------------------------------------------
# Wire check_ttp_sl_tighten into monitor_loop in main.py
# ---------------------------------------------------------------------------
main_path = ROOT / "main.py"
main_src = main_path.read_text(encoding="utf-8")

if "check_ttp_sl_tighten" in main_src:
    print("  SKIP main.py: check_ttp_sl_tighten already wired")
else:
    main_src = safe_replace(
        main_src,
        "            monitor.check_ttp_closes()",
        "            monitor.check_ttp_closes()\n            monitor.check_ttp_sl_tighten()",
        "P2-C wire: add check_ttp_sl_tighten to monitor_loop",
    )
    main_path.write_text(main_src, encoding="utf-8")
    verify(main_path, "main.py")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("")
if ERRORS:
    print("BUILD FAILED: " + ", ".join(ERRORS))
    sys.exit(1)
else:
    print("BUILD OK — Phase 2 patches applied")
    print("")
    print("Changes made:")
    print("  position_monitor.py: reduceOnly removed from _place_market_close()")
    print("  position_monitor.py: _tighten_sl_after_ttp() added")
    print("  position_monitor.py: check_ttp_sl_tighten() added (public, called from monitor_loop)")
    print("  state_manager.py:    TTP + BE columns added to _append_trade()")
    print("  config.yaml:         sl_trail_pct_post_ttp: 0.003 added")
    print("  main.py:             check_ttp_sl_tighten() wired into monitor_loop")
    print("")
    print("Next: restart bot and watch logs for 109400 errors (should be gone)")
