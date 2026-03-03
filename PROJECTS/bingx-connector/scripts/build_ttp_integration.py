r"""
Build script: TTP Engine Integration into BingX Connector
Creates ttp_engine.py, patches signal_engine.py, position_monitor.py, main.py,
config.yaml, and writes tests/test_ttp_engine.py.

Run:
    cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
    python scripts/build_ttp_integration.py
"""
import os
import sys
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
PASS = []


def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def check_compile(path):
    """Compile a Python file and report result."""
    try:
        py_compile.compile(str(path), doraise=True)
        log(f"  py_compile PASS: {path.name}")
        PASS.append(path.name)
    except py_compile.PyCompileError as e:
        log(f"  py_compile FAIL: {path.name} -- {e}")
        ERRORS.append(f"{path.name}: {e}")


def patch_file(path, old, new, label):
    """Replace old string with new in file. Reports success/failure."""
    content = path.read_text(encoding="utf-8")
    if old not in content:
        log(f"  PATCH SKIP ({label}): anchor not found in {path.name}")
        ERRORS.append(f"PATCH {label}: anchor not found in {path.name}")
        return False
    if content.count(old) > 1:
        log(f"  PATCH WARN ({label}): multiple matches in {path.name}, replacing first")
    content = content.replace(old, new, 1)
    path.write_text(content, encoding="utf-8")
    log(f"  PATCH OK: {label}")
    return True


# =========================================================================
# P1: Write ttp_engine.py (all 4 bugs fixed)
# =========================================================================

def p1_write_ttp_engine():
    """Create ttp_engine.py with all 4 bugs fixed from the BUILD-TTP-ENGINE spec."""
    log("P1: Writing ttp_engine.py ...")
    dest = ROOT / "ttp_engine.py"
    if dest.exists():
        log(f"  WARNING: {dest.name} already exists -- overwriting")

    source = '''\
"""
Trailing Take Profit (TTP) exit engine.

Two-phase state machine: MONITORING -> ACTIVATED -> CLOSED.
Runs dual pessimistic/optimistic scenarios per candle.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TTPResult:
    """Result of evaluating one candle through the TTP engine."""

    closed_pessimistic: bool = False
    closed_optimistic: bool = False
    exit_pct_pessimistic: Optional[float] = None
    exit_pct_optimistic: Optional[float] = None
    trail_level_pct: Optional[float] = None
    extreme_pct: Optional[float] = None
    state: str = "MONITORING"


class TTPExit:
    """Trailing Take Profit exit engine -- evaluates one candle at a time."""

    def __init__(self, direction, entry_price, activation_pct=0.005,
                 trail_distance_pct=0.002):
        """Initialize TTP engine with direction, entry, activation, and trail distance."""
        self.direction = direction.upper()
        self.entry = float(entry_price)
        self.act = float(activation_pct)
        self.dist = float(trail_distance_pct)

        # State
        self.state = "MONITORING"
        self.extreme = None
        self.trail_level = None

        # Activation price (computed once)
        if self.direction == "LONG":
            self.activation_price = self.entry * (1.0 + self.act)
        else:
            self.activation_price = self.entry * (1.0 - self.act)

    def evaluate(self, candle_high, candle_low):
        """Evaluate one candle. Returns TTPResult."""
        h = float(candle_high)
        l = float(candle_low)

        # BUG 1 FIX: If already closed, return immediately with no mutation
        if self.state == "CLOSED":
            return TTPResult(state="CLOSED")

        if self.state == "MONITORING":
            activated = self._try_activate(h, l)
            if not activated:
                return TTPResult(state="MONITORING")
            # BUG 2 FIX: After activation, fall through to evaluate
            # the activation candle's full range below

        # --- ACTIVATED: run dual scenario ---
        if self.direction == "LONG":
            result = self._evaluate_long(h, l)
        else:
            result = self._evaluate_short(h, l)

        return result

    def _try_activate(self, h, l):
        """Check if activation threshold is reached. Sets extreme and trail on activation."""
        if self.direction == "LONG":
            if h >= self.activation_price:
                self.state = "ACTIVATED"
                self.extreme = self.activation_price
                self.trail_level = self.extreme * (1.0 - self.dist)
                return True
        else:
            if l <= self.activation_price:
                self.state = "ACTIVATED"
                self.extreme = self.activation_price
                self.trail_level = self.extreme * (1.0 + self.dist)
                return True
        return False

    def _evaluate_long(self, h, l):
        """Evaluate long position: high extends, low reverses."""
        # Snapshot current state for pessimistic check
        pess_extreme = self.extreme
        pess_trail = self.trail_level

        # PESSIMISTIC: check reversal BEFORE updating extreme
        closed_pess = False
        exit_pct_pess = None
        if l <= pess_trail:
            closed_pess = True
            exit_pct_pess = (pess_trail - self.entry) / self.entry
        else:
            # Update extreme only if not closed
            if h > pess_extreme:
                pess_extreme = h
                pess_trail = pess_extreme * (1.0 - self.dist)

        # OPTIMISTIC: update extreme BEFORE checking reversal
        opt_extreme = self.extreme
        opt_trail = self.trail_level
        if h > opt_extreme:
            opt_extreme = h
            opt_trail = opt_extreme * (1.0 - self.dist)
        closed_opt = False
        exit_pct_opt = None
        if l <= opt_trail:
            closed_opt = True
            exit_pct_opt = (opt_trail - self.entry) / self.entry

        # Commit pessimistic state as conservative baseline
        if not closed_pess:
            self.extreme = pess_extreme
            self.trail_level = pess_trail
        else:
            # Keep state at pre-close values (no further updates)
            pass

        # BUG 1 FIX: Set state to CLOSED when either scenario closes
        if closed_pess or closed_opt:
            self.state = "CLOSED"

        return TTPResult(
            closed_pessimistic=closed_pess,
            closed_optimistic=closed_opt,
            exit_pct_pessimistic=exit_pct_pess,
            exit_pct_optimistic=exit_pct_opt,
            trail_level_pct=(self.trail_level - self.entry) / self.entry if self.trail_level else None,
            extreme_pct=(self.extreme - self.entry) / self.entry if self.extreme else None,
            state=self.state,
        )

    def _evaluate_short(self, h, l):
        """Evaluate short position: low extends, high reverses."""
        # Snapshot current state for pessimistic check
        pess_extreme = self.extreme
        pess_trail = self.trail_level

        # PESSIMISTIC: check reversal BEFORE updating extreme
        closed_pess = False
        exit_pct_pess = None
        if h >= pess_trail:
            closed_pess = True
            exit_pct_pess = (self.entry - pess_trail) / self.entry
        else:
            if l < pess_extreme:
                pess_extreme = l
                pess_trail = pess_extreme * (1.0 + self.dist)

        # OPTIMISTIC: update extreme BEFORE checking reversal
        opt_extreme = self.extreme
        opt_trail = self.trail_level
        if l < opt_extreme:
            opt_extreme = l
            opt_trail = opt_extreme * (1.0 + self.dist)
        closed_opt = False
        exit_pct_opt = None
        if h >= opt_trail:
            closed_opt = True
            exit_pct_opt = (self.entry - opt_trail) / self.entry

        # Commit pessimistic state as conservative baseline
        if not closed_pess:
            self.extreme = pess_extreme
            self.trail_level = pess_trail

        # BUG 1 FIX: Set state to CLOSED when either scenario closes
        if closed_pess or closed_opt:
            self.state = "CLOSED"

        return TTPResult(
            closed_pessimistic=closed_pess,
            closed_optimistic=closed_opt,
            exit_pct_pessimistic=exit_pct_pess,
            exit_pct_optimistic=exit_pct_opt,
            trail_level_pct=(self.entry - self.trail_level) / self.entry if self.trail_level else None,
            extreme_pct=(self.entry - self.extreme) / self.entry if self.extreme else None,
            state=self.state,
        )


def run_ttp_on_trade(candles_df, entry_price, direction,
                     activation_pct=0.005, trail_distance_pct=0.002):
    """Run TTP engine over a DataFrame of candles for one trade.

    Returns dict with exit_candle_idx, exit_pct_pess, exit_pct_opt,
    band_width_pct, and candle_results list.
    """
    engine = TTPExit(direction, entry_price, activation_pct, trail_distance_pct)
    results = []
    exit_idx = None

    # BUG 4 FIX: use enumerate + itertuples for positional index and speed
    for i, row in enumerate(candles_df[["high", "low"]].itertuples(index=False)):
        result = engine.evaluate(candle_high=row.high, candle_low=row.low)
        results.append(result)
        if exit_idx is None and (result.closed_pessimistic or result.closed_optimistic):
            exit_idx = i

    # Collect exit percentages
    exit_pct_pess = None
    exit_pct_opt = None
    if results:
        for r in results:
            if r.closed_pessimistic and exit_pct_pess is None:
                exit_pct_pess = r.exit_pct_pessimistic
            if r.closed_optimistic and exit_pct_opt is None:
                exit_pct_opt = r.exit_pct_optimistic

    # BUG 5 FIX: Only compute band_width when both scenarios have closed
    band_width_pct = None
    if exit_pct_pess is not None and exit_pct_opt is not None:
        band_width_pct = abs(exit_pct_opt - exit_pct_pess)

    return {
        "exit_candle_idx": exit_idx,
        "exit_pct_pessimistic": exit_pct_pess,
        "exit_pct_optimistic": exit_pct_opt,
        "band_width_pct": band_width_pct,
        "candle_results": results,
    }
'''

    dest.write_text(source, encoding="utf-8")
    log(f"  Written: {dest}")
    check_compile(dest)


# =========================================================================
# P2: Patch signal_engine.py
# =========================================================================

def p2_patch_signal_engine():
    """Patch signal_engine.py: add TTP imports, __init__ params, restructure on_new_bar."""
    log("P2: Patching signal_engine.py ...")
    path = ROOT / "signal_engine.py"
    content = path.read_text(encoding="utf-8")

    # --- P2a: Add import ---
    old_import = 'import logging'
    new_import = 'import logging\nfrom ttp_engine import TTPExit'
    if "from ttp_engine import TTPExit" not in content:
        patch_file(path, old_import, new_import, "P2a-import")
        content = path.read_text(encoding="utf-8")

    # --- P2b: Add ttp_config to __init__ ---
    old_init = (
        '    def __init__(self, plugin_name, risk_gate, executor,\n'
        '                 state_manager, notifier, plugin_config=None):\n'
        '        """Initialize with plugin name and downstream components."""\n'
        '        self.plugin = self._load_plugin(plugin_name, plugin_config)\n'
        '        self.risk_gate = risk_gate\n'
        '        self.executor = executor\n'
        '        self.state_manager = state_manager\n'
        '        self.notifier = notifier\n'
        '        self.warmup_needed = self.plugin.warmup_bars()\n'
        '        self.allowed_grades = self.plugin.get_allowed_grades()'
    )
    new_init = (
        '    def __init__(self, plugin_name, risk_gate, executor,\n'
        '                 state_manager, notifier, plugin_config=None,\n'
        '                 ttp_config=None):\n'
        '        """Initialize with plugin name and downstream components."""\n'
        '        self.plugin = self._load_plugin(plugin_name, plugin_config)\n'
        '        self.risk_gate = risk_gate\n'
        '        self.executor = executor\n'
        '        self.state_manager = state_manager\n'
        '        self.notifier = notifier\n'
        '        self.warmup_needed = self.plugin.warmup_bars()\n'
        '        self.allowed_grades = self.plugin.get_allowed_grades()\n'
        '        # TTP configuration\n'
        '        _ttp = ttp_config or {}\n'
        '        self.ttp_enabled = _ttp.get("ttp_enabled", False)\n'
        '        self.ttp_act = _ttp.get("ttp_act", 0.005)\n'
        '        self.ttp_dist = _ttp.get("ttp_dist", 0.002)\n'
        '        self.ttp_engines = {}  # keyed by position key e.g. "BTCUSDT_LONG"'
    )
    patch_file(path, old_init, new_init, "P2b-init")
    content = path.read_text(encoding="utf-8")

    # --- P2c: Restructure on_new_bar + add _evaluate_ttp_for_symbol ---
    old_on_new_bar = (
        '    def on_new_bar(self, symbol, ohlcv_df):\n'
        '        """Process a new confirmed bar through the signal pipeline."""\n'
        '        if len(ohlcv_df) < self.warmup_needed + 1:\n'
        '            logger.debug("Warmup: %s has %d/%d bars",\n'
        '                         symbol, len(ohlcv_df), self.warmup_needed + 1)\n'
        '            return\n'
        '        try:\n'
        '            signal = self.plugin.get_signal(ohlcv_df)\n'
        '        except Exception as e:\n'
        '            logger.error("Plugin error %s: %s", symbol, e)\n'
        '            return\n'
        '        if signal is None or signal.direction == "NONE":\n'
        '            logger.debug("No signal: %s", symbol)\n'
        '            return\n'
        '        logger.info("Signal: %s %s grade=%s price=%.6f",\n'
        '                     signal.direction, symbol,\n'
        '                     signal.grade, signal.entry_price)\n'
        '        state_dict = self.state_manager.get_state()\n'
        '        approved, reason = self.risk_gate.evaluate(\n'
        '            signal, symbol, state_dict, self.allowed_grades,\n'
        '            state_manager=self.state_manager)\n'
        '        if not approved:\n'
        '            logger.info("Blocked: %s %s — %s",\n'
        '                         signal.direction, symbol, reason)\n'
        '            return\n'
        '        result = self.executor.execute(signal, symbol)\n'
        '        if result is None:\n'
        '            logger.error("Execution failed: %s %s",\n'
        '                          signal.direction, symbol)'
    )
    new_on_new_bar = (
        '    def on_new_bar(self, symbol, ohlcv_df):\n'
        '        """Process a new confirmed bar through the signal pipeline."""\n'
        '        if len(ohlcv_df) < self.warmup_needed + 1:\n'
        '            logger.debug("Warmup: %s has %d/%d bars",\n'
        '                         symbol, len(ohlcv_df), self.warmup_needed + 1)\n'
        '            return\n'
        '        # --- Signal processing ---\n'
        '        try:\n'
        '            signal = self.plugin.get_signal(ohlcv_df)\n'
        '        except Exception as e:\n'
        '            logger.error("Plugin error %s: %s", symbol, e)\n'
        '            signal = None\n'
        '        if signal is not None and signal.direction != "NONE":\n'
        '            logger.info("Signal: %s %s grade=%s price=%.6f",\n'
        '                         signal.direction, symbol,\n'
        '                         signal.grade, signal.entry_price)\n'
        '            state_dict = self.state_manager.get_state()\n'
        '            approved, reason = self.risk_gate.evaluate(\n'
        '                signal, symbol, state_dict, self.allowed_grades,\n'
        '                state_manager=self.state_manager)\n'
        '            if not approved:\n'
        '                logger.info("Blocked: %s %s — %s",\n'
        '                             signal.direction, symbol, reason)\n'
        '            else:\n'
        '                result = self.executor.execute(signal, symbol)\n'
        '                if result is None:\n'
        '                    logger.error("Execution failed: %s %s",\n'
        '                                  signal.direction, symbol)\n'
        '        # --- TTP evaluation (always runs after warmup, even without signal) ---\n'
        '        self._evaluate_ttp_for_symbol(symbol, ohlcv_df)\n'
        '\n'
        '    def _evaluate_ttp_for_symbol(self, symbol, ohlcv_df):\n'
        '        """Evaluate TTP trailing exit for any open position matching this symbol."""\n'
        '        if not self.ttp_enabled:\n'
        '            return\n'
        '        try:\n'
        '            latest = ohlcv_df.iloc[-1]\n'
        '            h = float(latest["high"])\n'
        '            l = float(latest["low"])\n'
        '        except (IndexError, KeyError, TypeError):\n'
        '            return\n'
        '        positions = self.state_manager.get_state().get("open_positions", {})\n'
        '        # Prune engines for closed positions\n'
        '        stale = [k for k in self.ttp_engines if k not in positions]\n'
        '        for k in stale:\n'
        '            del self.ttp_engines[k]\n'
        '        for key, pos in positions.items():\n'
        '            if pos.get("symbol") != symbol:\n'
        '                continue\n'
        '            engine = self.ttp_engines.get(key)\n'
        '            if engine is None:\n'
        '                engine = TTPExit(\n'
        '                    pos.get("direction", "LONG"),\n'
        '                    pos.get("entry_price", 0),\n'
        '                    self.ttp_act,\n'
        '                    self.ttp_dist,\n'
        '                )\n'
        '                self.ttp_engines[key] = engine\n'
        '            if engine.state == "CLOSED":\n'
        '                continue\n'
        '            result = engine.evaluate(candle_high=h, candle_low=l)\n'
        '            self.state_manager.update_position(key, {\n'
        '                "ttp_state": engine.state,\n'
        '                "ttp_trail_level": engine.trail_level,\n'
        '                "ttp_extreme": engine.extreme,\n'
        '            })\n'
        '            if result.closed_pessimistic:\n'
        '                self.state_manager.update_position(key, {\n'
        '                    "ttp_close_pending": True,\n'
        '                    "ttp_exit_pct_pess": result.exit_pct_pessimistic,\n'
        '                    "ttp_exit_pct_opt": result.exit_pct_optimistic,\n'
        '                })\n'
        '                logger.info("TTP close pending: %s pess=%.4f%%",\n'
        '                            key, (result.exit_pct_pessimistic or 0) * 100)'
    )
    patch_file(path, old_on_new_bar, new_on_new_bar, "P2c-on_new_bar")
    check_compile(path)


# =========================================================================
# P3: Patch position_monitor.py
# =========================================================================

def p3_patch_position_monitor():
    """Patch position_monitor.py: add TTP close execution methods."""
    log("P3: Patching position_monitor.py ...")
    path = ROOT / "position_monitor.py"
    content = path.read_text(encoding="utf-8")

    # --- P3a: Add _detect_exit TTP check ---
    # Insert TTP exit pending check at the top of _detect_exit
    old_detect = (
        '    def _detect_exit(self, symbol, pos_data):\n'
        '        """Detect SL or TP hit by checking which conditional orders remain.\n'
        '\n'
        '        Queries open orders for the symbol. If SL is still pending, TP\n'
        '        was hit (and vice versa). Cancels the orphaned remaining order.\n'
        '        Returns (exit_price, exit_reason) or (None, None) on failure.\n'
        '        """'
    )
    new_detect = (
        '    def _detect_exit(self, symbol, pos_data):\n'
        '        """Detect SL or TP hit by checking which conditional orders remain.\n'
        '\n'
        '        Queries open orders for the symbol. If SL is still pending, TP\n'
        '        was hit (and vice versa). Cancels the orphaned remaining order.\n'
        '        Returns (exit_price, exit_reason) or (None, None) on failure.\n'
        '        """\n'
        '        # TTP exit: if ttp_exit_pending flag is set, return trail level as exit price\n'
        '        if pos_data.get("ttp_exit_pending"):\n'
        '            trail = pos_data.get("ttp_trail_level")\n'
        '            if trail is not None:\n'
        '                return float(trail), "TTP_EXIT"\n'
        '            return None, "TTP_EXIT"'
    )
    patch_file(path, old_detect, new_detect, "P3a-detect_exit")
    content = path.read_text(encoding="utf-8")

    # --- P3b: Add new methods before check_daily_reset ---
    # We insert check_ttp_closes, _cancel_all_orders_for_symbol,
    # _place_market_close, _fetch_single_position
    ttp_methods = '''
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

'''

    anchor = '    def check_daily_reset(self):'
    if anchor in content:
        content = content.replace(anchor, ttp_methods + anchor, 1)
        path.write_text(content, encoding="utf-8")
        log("  PATCH OK: P3b-ttp_methods")
    else:
        log("  PATCH SKIP (P3b-ttp_methods): anchor not found")
        ERRORS.append("PATCH P3b: check_daily_reset anchor not found")

    check_compile(path)


# =========================================================================
# P4: Patch main.py
# =========================================================================

def p4_patch_main():
    """Patch main.py: pass ttp_config, add monitor.check_ttp_closes()."""
    log("P4: Patching main.py ...")
    path = ROOT / "main.py"

    # --- P4a: Add ttp_config to StrategyAdapter constructor ---
    old_adapter = (
        '    adapter = StrategyAdapter(\n'
        '        plugin_name=strat_cfg.get("plugin", "mock_strategy"),\n'
        '        risk_gate=risk_gate,\n'
        '        executor=executor_inst,\n'
        '        state_manager=state_mgr,\n'
        '        notifier=notifier,\n'
        '        plugin_config=config,\n'
        '    )'
    )
    new_adapter = (
        '    adapter = StrategyAdapter(\n'
        '        plugin_name=strat_cfg.get("plugin", "mock_strategy"),\n'
        '        risk_gate=risk_gate,\n'
        '        executor=executor_inst,\n'
        '        state_manager=state_mgr,\n'
        '        notifier=notifier,\n'
        '        plugin_config=config,\n'
        '        ttp_config=pos_cfg,\n'
        '    )'
    )
    patch_file(path, old_adapter, new_adapter, "P4a-adapter")

    # --- P4b: Add check_ttp_closes to monitor_loop ---
    old_monitor = (
        '            monitor.check()\n'
        '            monitor.check_breakeven()'
    )
    new_monitor = (
        '            monitor.check()\n'
        '            monitor.check_breakeven()\n'
        '            monitor.check_ttp_closes()'
    )
    patch_file(path, old_monitor, new_monitor, "P4b-monitor_loop")
    check_compile(path)


# =========================================================================
# P5: Patch config.yaml
# =========================================================================

def p5_patch_config():
    """Add TTP fields to config.yaml under position: section if not present."""
    log("P5: Patching config.yaml ...")
    path = ROOT / "config.yaml"
    content = path.read_text(encoding="utf-8")

    if "ttp_enabled" in content:
        log("  SKIP: ttp_enabled already present in config.yaml")
        return

    # Insert after the trailing_rate line (last line in position: section)
    anchor = '  trailing_rate: 0.02                  # 2% callback from peak once activation hit'
    ttp_lines = (
        '  trailing_rate: 0.02                  # 2% callback from peak once activation hit\n'
        '  ttp_enabled: false                   # Trailing Take Profit on/off\n'
        '  ttp_act: 0.005                       # 0.5% activation threshold\n'
        '  ttp_dist: 0.002                      # 0.2% trail distance'
    )
    if anchor in content:
        content = content.replace(anchor, ttp_lines, 1)
        path.write_text(content, encoding="utf-8")
        log("  PATCH OK: P5-config-ttp")
    else:
        log("  PATCH SKIP (P5): trailing_rate anchor not found")
        ERRORS.append("PATCH P5: trailing_rate anchor not found in config.yaml")


# =========================================================================
# P6: Write tests/test_ttp_engine.py
# =========================================================================

def p6_write_tests():
    """Write 6 unit tests for TTPExit per BUILD-TTP-ENGINE spec."""
    log("P6: Writing tests/test_ttp_engine.py ...")
    tests_dir = ROOT / "tests"
    tests_dir.mkdir(exist_ok=True)
    dest = tests_dir / "test_ttp_engine.py"

    source = '''\
"""
Unit tests for TTP engine (ttp_engine.py).
6 tests covering long/short, ambiguous candles, activation candle, and post-close.

Run:
    cd "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector"
    python -m pytest tests/test_ttp_engine.py -v
"""
import sys
from pathlib import Path

# Add parent dir to path so ttp_engine can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ttp_engine import TTPExit


def test_short_clean_sequential():
    """Short -- clean sequential from TTP spec walk-through."""
    # Entry at 100.0, ACT=0.5%, DIST=0.2%
    # Activation price = 100 * 0.995 = 99.5
    engine = TTPExit("SHORT", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Candle 1: H=100.1, L=99.8 -- below activation (99.8 > 99.5) -- still monitoring
    r = engine.evaluate(100.1, 99.8)
    assert r.state == "MONITORING"

    # Candle 2: H=100.0, L=99.7 -- still above 99.5
    r = engine.evaluate(100.0, 99.7)
    assert r.state == "MONITORING"

    # Candle 3: H=99.8, L=99.5 -- hits activation (L <= 99.5)
    r = engine.evaluate(99.8, 99.5)
    assert engine.state == "ACTIVATED"
    # extreme = activation_price = 99.5, trail = 99.5 * 1.002 = 99.699
    assert engine.extreme == 99.5

    # Candle 4: H=99.6, L=99.2 -- new low
    r = engine.evaluate(99.6, 99.2)
    assert engine.state == "ACTIVATED"
    # pess: H=99.6 < trail(99.699), no close. L=99.2 < 99.5 -> extreme=99.2, trail=99.2*1.002=99.3984
    assert abs(engine.extreme - 99.2) < 0.0001

    # Candle 5: H=99.3, L=98.9 -- new low
    r = engine.evaluate(99.3, 98.9)
    assert engine.state == "ACTIVATED"
    assert abs(engine.extreme - 98.9) < 0.0001
    # trail = 98.9 * 1.002 = 99.0978

    # Candle 6: H=99.1, L=99.0 -- reversal hits trail
    r = engine.evaluate(99.1, 99.0)
    # trail was 99.0978, H=99.1 >= 99.0978 -> pess closes
    assert r.closed_pessimistic is True
    assert engine.state == "CLOSED"
    assert r.exit_pct_pessimistic is not None


def test_short_ambiguous_candle():
    """Short -- ambiguous candle: new low AND reversal on same candle."""
    engine = TTPExit("SHORT", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Activate: L=99.5
    engine.evaluate(100.0, 99.5)
    assert engine.state == "ACTIVATED"

    # Push extreme lower: L=99.2
    engine.evaluate(99.3, 99.2)
    # trail = 99.2 * 1.002 = 99.3984

    # Push further: L=98.9
    engine.evaluate(99.0, 98.9)
    # pess trail = 98.9 * 1.002 = 99.0978

    # Ambiguous candle: L=98.8 (new low), H=99.05 (near trail 99.0978)
    # Pessimistic: check H first -> 99.05 < 99.0978 -> no close. Then update extreme to 98.8
    # Optimistic: update extreme to 98.8 first -> trail = 98.8*1.002 = 98.9976. Then H=99.05 >= 98.9976 -> CLOSE
    r = engine.evaluate(99.05, 98.8)

    assert r.closed_pessimistic is False
    assert r.closed_optimistic is True


def test_long_clean_sequential():
    """Long -- clean sequential mirror of short test."""
    engine = TTPExit("LONG", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Below activation
    r = engine.evaluate(100.3, 99.9)
    assert r.state == "MONITORING"

    # Hit activation: H >= 100.5
    r = engine.evaluate(100.5, 100.2)
    assert engine.state == "ACTIVATED"
    assert engine.extreme == 100.5  # activation_price = 100.5

    # New high
    r = engine.evaluate(100.8, 100.4)
    assert abs(engine.extreme - 100.8) < 0.0001
    # trail = 100.8 * 0.998 = 100.5984

    # Another new high
    r = engine.evaluate(101.1, 100.7)
    assert abs(engine.extreme - 101.1) < 0.0001
    # trail = 101.1 * 0.998 = 100.8978

    # Reversal: L <= trail (100.8978)
    r = engine.evaluate(101.0, 100.8)
    assert r.closed_pessimistic is True
    assert engine.state == "CLOSED"


def test_long_ambiguous_candle():
    """Long -- ambiguous candle: new high AND reversal on same candle."""
    engine = TTPExit("LONG", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Activate
    engine.evaluate(100.5, 100.2)
    assert engine.state == "ACTIVATED"

    # Push extreme higher
    engine.evaluate(100.8, 100.4)
    # trail = 100.8 * 0.998 = 100.5984

    engine.evaluate(101.1, 100.7)
    # trail = 101.1 * 0.998 = 100.8978

    # Ambiguous: H=101.2 (new high), L=100.95 (near trail)
    # Pess: check L first -> 100.95 > 100.8978 -> no close. Update extreme to 101.2
    # Opt: update extreme to 101.2 -> trail=101.2*0.998=100.9976. L=100.95 < 100.9976 -> CLOSE
    r = engine.evaluate(101.2, 100.95)

    assert r.closed_pessimistic is False
    assert r.closed_optimistic is True


def test_activation_candle_trail_update():
    """Activation candle should also update extreme beyond activation price."""
    # Short: entry=100, activation=99.5
    # Single candle that activates AND extends further
    engine = TTPExit("SHORT", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Candle: H=99.8, L=99.3 (L < activation 99.5, AND L extends past activation)
    r = engine.evaluate(99.8, 99.3)

    # After activation, extreme should be updated to 99.3 (not stuck at 99.5)
    # because the candle's full range is evaluated after activation
    assert engine.state == "ACTIVATED"
    assert engine.extreme < 99.5  # extreme moved past activation price
    assert abs(engine.extreme - 99.3) < 0.0001


def test_engine_stops_after_close():
    """After CLOSED state, evaluate() returns CLOSED with no mutation."""
    engine = TTPExit("LONG", 100.0, activation_pct=0.005, trail_distance_pct=0.002)

    # Activate
    engine.evaluate(100.5, 100.2)
    # Push high
    engine.evaluate(101.0, 100.5)
    # trail = 101.0 * 0.998 = 100.798

    # Close: L <= trail
    r = engine.evaluate(100.9, 100.7)
    assert engine.state == "CLOSED"
    saved_extreme = engine.extreme
    saved_trail = engine.trail_level

    # Call again after close -- should return CLOSED, no state change
    r2 = engine.evaluate(105.0, 95.0)
    assert r2.state == "CLOSED"
    assert r2.closed_pessimistic is False
    assert r2.closed_optimistic is False
    assert engine.extreme == saved_extreme
    assert engine.trail_level == saved_trail
'''

    dest.write_text(source, encoding="utf-8")
    log(f"  Written: {dest}")
    check_compile(dest)


# =========================================================================
# Main
# =========================================================================

def main():
    """Run all patches in sequence."""
    log("=" * 60)
    log("TTP Integration Build Script")
    log("=" * 60)

    p1_write_ttp_engine()
    p2_patch_signal_engine()
    p3_patch_position_monitor()
    p4_patch_main()
    p5_patch_config()
    p6_write_tests()

    log("")
    log("=" * 60)
    if ERRORS:
        log("FAILURES: " + ", ".join(ERRORS))
    else:
        log("ALL PATCHES PASSED")
    log("Passed: " + ", ".join(PASS))
    log("=" * 60)

    if ERRORS:
        sys.exit(1)


if __name__ == "__main__":
    main()
