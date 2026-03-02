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
                    "state.json load failed: %s — using defaults", e)
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
        """Return a copy of open positions dict."""
        with self.lock:
            return dict(self.state["open_positions"])

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
            logger.error("trades.csv append failed: %s", e)

    def reset_daily(self):
        """Reset daily_pnl, daily_trades, halt_flag (BUG-C04 fix)."""
        with self.lock:
            self.state["daily_pnl"] = 0.0
            self.state["daily_trades"] = 0
            self.state["halt_flag"] = False
            self._save_state()
            logger.info("Daily reset: pnl=0, trades=0, halt=False")

    def set_halt_flag(self, value):
        """Set the halt flag explicitly."""
        with self.lock:
            self.state["halt_flag"] = value
            self._save_state()
            logger.info("halt_flag set to %s", value)

    def reconcile(self, live_positions):
        """Remove phantom positions not present on exchange."""
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
                logger.warning("Reconcile: removing phantom %s", key)
                self.state["open_positions"].pop(key, None)
            if phantoms:
                self._save_state()
                logger.info("Reconcile: removed %d phantoms",
                            len(phantoms))
            else:
                logger.info(
                    "Reconcile: state matches exchange (%d positions)",
                    len(state_keys))

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
