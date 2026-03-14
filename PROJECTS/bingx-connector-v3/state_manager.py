"""
State persistence: state.json (atomic write) + trades.csv (append).
Thread-safe with threading.Lock.
"""
import os
import copy
import json
import csv
import logging
import threading
import requests
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DEFAULT_STATE = {
    "open_positions": {},
    "daily_pnl": 0.0,
    "daily_trades": 0,
    "halt_flag": False,
    "session_start": "",
}

ALL_ORDERS_PATH = "/openApi/swap/v2/trade/allOrders"


class StateManager:
    """Thread-safe state persistence with atomic writes."""

    def __init__(self, state_path, trades_path):
        """Initialize with file paths and threading lock."""
        self.state_path = Path(state_path)
        self.trades_path = Path(trades_path)
        self.lock = threading.Lock()
        self._last_exit_time = {}
        self._session_blocked = set()
        self.state = self._load_state()

    def _load_state(self):
        """Load state from JSON file or return clean defaults."""
        if self.state_path.exists():
            try:
                data = json.loads(
                    self.state_path.read_text(encoding="utf-8"))
                merged = dict(DEFAULT_STATE)
                merged.update(data)
                logger.info(
                    "State loaded: %d positions, daily_pnl=%.2f, halt=%s",
                    len(merged.get("open_positions", {})),
                    merged.get("daily_pnl", 0),
                    merged.get("halt_flag", False))
                return merged
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "state.json load failed: %s -- using defaults", e)
        state = copy.deepcopy(DEFAULT_STATE)
        state["session_start"] = datetime.now(timezone.utc).isoformat()
        logger.info("State initialized with defaults")
        return state

    def _save_state(self):
        """Atomic write: tmp file -> os.replace -> state.json."""
        tmp_path = str(self.state_path) + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, default=str)
            os.replace(tmp_path, str(self.state_path))
        except OSError as e:
            logger.error("State save failed: %s", e)

    def get_state(self):
        """Return a deep copy of the full state dict."""
        with self.lock:
            return json.loads(json.dumps(self.state))

    def get_open_positions(self):
        """Return a deep copy of open positions dict. W03: Uses json round-trip for true deep copy."""
        with self.lock:
            return json.loads(json.dumps(self.state["open_positions"]))

    def record_open_position(self, key, position_data):
        """Record a new open position and increment daily_trades."""
        with self.lock:
            self.state["open_positions"][key] = position_data
            self.state["daily_trades"] += 1
            self._save_state()
            logger.info("Position opened: %s", key)

    def update_position(self, key, updates):
        """Merge updates dict into an existing open position record."""
        with self.lock:
            pos = self.state["open_positions"].get(key)
            if pos is None:
                logger.warning("update_position: key %s not found", key)
                return False
            pos.update(updates)
            self._save_state()
            logger.info("Position updated: %s fields=%s", key, list(updates.keys()))
            return True

    def close_position(self, key, exit_price, exit_reason, pnl_net):
        """Close position, update daily_pnl, append to trades.csv."""
        with self.lock:
            pos = self.state["open_positions"].pop(key, None)
            if pos is None:
                logger.warning("close_position: key %s not found", key)
                return None
            self.state["daily_pnl"] += pnl_net
            self._last_exit_time[key] = datetime.now(timezone.utc)
            self._save_state()
            self._append_trade(pos, exit_price, exit_reason, pnl_net)
            logger.info(
                "Position closed: %s reason=%s pnl=%.2f daily=%.2f",
                key, exit_reason, pnl_net, self.state["daily_pnl"])
            return pos

    def _append_trade(self, pos, exit_price, exit_reason, pnl_net):
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
                        "atr_at_entry", "sl_price",
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
                if exit_reason == "TTP_EXIT":
                    ttp_exit_reason_col = "TTP_CLOSE"
                elif exit_reason == "TRAILING_EXIT":
                    ttp_exit_reason_col = "TRAILING_EXIT"
                else:
                    ttp_exit_reason_col = ""
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
                    pos.get("atr_at_entry", ""),
                    pos.get("sl_price", ""),
                ])
        except OSError as e:
            logger.error("trades.csv append failed: %s", e)

    def reset_daily(self):
        """Reset daily_pnl, daily_trades, halt_flag, and session_start (BUG-C04 fix)."""
        with self.lock:
            self.state["daily_pnl"] = 0.0
            self.state["daily_trades"] = 0
            self.state["halt_flag"] = False
            self.state["session_start"] = datetime.now(timezone.utc).isoformat()
            self._save_state()
            logger.info("Daily reset: pnl=0, trades=0, halt=False, session_start refreshed")

    def set_halt_flag(self, value):
        """Set the halt flag explicitly."""
        with self.lock:
            self.state["halt_flag"] = value
            self._save_state()
            logger.info("halt_flag set to %s", value)

    def reconcile(self, live_positions, notifier=None, auth=None):
        """Remove phantom positions not present on exchange.

        W12: Optional notifier sends PHANTOM REMOVED alert.
        W12: Optional auth tries allOrders fill price before falling back to entry_price.
        """
        with self.lock:
            live_keys = set()
            for pos in live_positions:
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
            state_keys = set(self.state["open_positions"].keys())
            phantoms = state_keys - live_keys
            for key in phantoms:
                pos = self.state["open_positions"].pop(key, None)
                if pos is None:
                    continue
                symbol = pos.get("symbol", key.rsplit("_", 1)[0])
                entry_price = pos.get("entry_price", 0)
                exit_price = entry_price  # default fallback
                exit_reason = "EXIT_UNKNOWN_RECONCILE"
                pnl_net = 0.0
                # W12: Try to get actual fill price from allOrders
                if auth is not None:
                    fill_price = self._try_fetch_reconcile_fill(auth, symbol, pos)
                    if fill_price is not None:
                        exit_price = fill_price
                        direction = pos.get("direction", "LONG")
                        quantity = pos.get("quantity", 0)
                        notional = pos.get("notional_usd", 0)
                        if direction == "LONG":
                            pnl_gross = (exit_price - entry_price) * quantity
                        else:
                            pnl_gross = (entry_price - exit_price) * quantity
                        pnl_net = pnl_gross  # no commission deduction in reconcile (already paid)
                        logger.info(
                            "Reconcile %s: found fill price %.8f, pnl=%.4f",
                            key, exit_price, pnl_net)
                    else:
                        logger.critical(
                            "Reconcile %s: no fill price found in allOrders, "
                            "using entry_price %.8f with $0 PnL", key, entry_price)
                else:
                    logger.error(
                        "Reconcile: phantom position %s removed "
                        "-- recording EXIT_UNKNOWN with $0 PnL (no auth for fill lookup)", key)
                self.state["daily_pnl"] += pnl_net
                self._last_exit_time[key] = datetime.now(timezone.utc)
                self._append_trade(pos, exit_price, exit_reason, pnl_net)
                # W12: Send Telegram alert for phantom removal
                if notifier is not None:
                    alert_msg = ("<b>PHANTOM REMOVED</b>  " + key
                                 + "\nExit price: " + str(round(exit_price, 8))
                                 + "\nPnL: $" + str(round(pnl_net, 4))
                                 + "\nReason: " + exit_reason)
                    notifier.send(alert_msg)
            if phantoms:
                self._save_state()
                logger.error("Reconcile: removed %d phantom(s) -- "
                             "check exchange for liquidations",
                             len(phantoms))
            else:
                logger.info(
                    "Reconcile: state matches exchange (%d positions)",
                    len(state_keys))

    def _try_fetch_reconcile_fill(self, auth, symbol, pos_data):
        """Try to fetch fill price from allOrders for reconciliation. Returns float or None."""
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
            req = auth.build_signed_request("GET", ALL_ORDERS_PATH, params)
            resp = requests.get(req["url"], headers=req["headers"], timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                return None
            orders = data.get("data", {}).get("orders", [])
            if isinstance(data.get("data"), list):
                orders = data["data"]
            direction = pos_data.get("direction", "")
            for o in orders:
                if o.get("positionSide", "") != direction:
                    continue
                if o.get("status", "") != "FILLED":
                    continue
                avg_price = float(o.get("avgPrice", 0))
                if avg_price > 0:
                    return avg_price
            return None
        except Exception as e:
            logger.warning("Reconcile allOrders fetch failed %s: %s", symbol, e)
            return None

    def get_last_exit_time(self, key):
        """Return last exit time for a key, or None if no exit recorded."""
        return self._last_exit_time.get(key)

    def add_session_blocked(self, symbol):
        """Add a symbol to the session-blocked set."""
        self._session_blocked.add(symbol)
        logger.info("Session-blocked: %s", symbol)

    def is_session_blocked(self, symbol):
        """Check if a symbol is blocked for this session."""
        return symbol in self._session_blocked
