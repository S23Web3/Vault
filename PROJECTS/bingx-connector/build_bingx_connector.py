"""
Build script for BingX Execution Connector.
Generates all project files, validates syntax, runs import smoke tests.
Run: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector/build_bingx_connector.py"
"""
import os
import sys
import ast
import py_compile
import importlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
ERRORS = []
CREATED = []
TOTAL = 25
STEP = [0]


def next_step(name):
    """Print step counter."""
    STEP[0] += 1
    print("[" + str(STEP[0]) + "/" + str(TOTAL) + "] " + name)


def write_and_verify(rel_path, content):
    """Write file and verify .py files with py_compile + ast.parse."""
    full_path = ROOT / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    CREATED.append(str(rel_path))
    print("  [WRITE] " + str(rel_path))
    if str(rel_path).endswith(".py"):
        try:
            py_compile.compile(str(full_path), doraise=True)
            print("  [COMPILE OK] " + str(rel_path))
        except py_compile.PyCompileError as e:
            print("  [COMPILE FAIL] " + str(rel_path) + ": " + str(e))
            ERRORS.append("compile:" + str(rel_path))
            return False
        try:
            ast.parse(content, filename=str(rel_path))
            print("  [AST OK] " + str(rel_path))
        except SyntaxError as e:
            print("  [AST FAIL] " + str(rel_path) + " line " + str(e.lineno) + ": " + str(e.msg))
            ERRORS.append("ast:" + str(rel_path))
            return False
    return True


# ---------------------------------------------------------------------------
# 1. requirements.txt
# ---------------------------------------------------------------------------
def build_requirements():
    """Generate requirements.txt."""
    next_step("requirements.txt")
    content = """\
requests>=2.28.0
pyyaml>=6.0
python-dotenv>=1.0.0
pandas>=2.0.0
numpy>=1.24.0
"""
    write_and_verify("requirements.txt", content)


# ---------------------------------------------------------------------------
# 2. .env.example
# ---------------------------------------------------------------------------
def build_env_example():
    """Generate .env.example template."""
    next_step(".env.example")
    content = """\
BINGX_API_KEY=your_api_key_here
BINGX_SECRET_KEY=your_secret_key_here
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
"""
    write_and_verify(".env.example", content)


# ---------------------------------------------------------------------------
# 3. .gitignore
# ---------------------------------------------------------------------------
def build_gitignore():
    """Generate .gitignore."""
    next_step(".gitignore")
    content = """\
.env
state.json
state.json.tmp
trades.csv
bot.log
__pycache__/
*.pyc
.pytest_cache/
"""
    write_and_verify(".gitignore", content)


# ---------------------------------------------------------------------------
# 4. config.yaml
# ---------------------------------------------------------------------------
def build_config_yaml():
    """Generate config.yaml with demo defaults."""
    next_step("config.yaml")
    content = """\
connector:
  poll_interval_sec: 30
  position_check_sec: 60
  timeframe: "5m"
  ohlcv_buffer_bars: 200
  demo_mode: true

coins:
  - "RIVER-USDT"
  - "GUN-USDT"
  - "AXS-USDT"

strategy:
  plugin: "mock_strategy"

risk:
  max_positions: 3
  max_daily_trades: 20
  daily_loss_limit_usd: 75.0
  min_atr_ratio: 0.003

position:
  margin_usd: 50.0
  leverage: 10
  margin_mode: "ISOLATED"
  sl_working_type: "MARK_PRICE"
  tp_working_type: "MARK_PRICE"

notification:
  daily_summary_utc_hour: 17
"""
    write_and_verify("config.yaml", content)


# ---------------------------------------------------------------------------
# 5. bingx_auth.py
# ---------------------------------------------------------------------------
def build_bingx_auth():
    """Generate BingX authentication module."""
    next_step("bingx_auth.py")
    content = '''\
"""
BingX authentication and request signing.
HMAC-SHA256 with alphabetical param sorting.
"""
import hashlib
import hmac
import time
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

LIVE_BASE = "https://open-api.bingx.com"
DEMO_BASE = "https://open-api-vst.bingx.com"


class BingXAuth:
    """HMAC-SHA256 signing for BingX perpetual swap API."""

    def __init__(self, api_key, secret_key, demo_mode=True):
        """Initialize with API credentials and mode toggle."""
        self.api_key = api_key
        self.secret_key = secret_key
        self.demo_mode = demo_mode
        self.base_url = DEMO_BASE if demo_mode else LIVE_BASE
        logger.info("BingXAuth: base=%s demo=%s", self.base_url, demo_mode)

    def sign_params(self, params):
        """Sort params alphabetically, compute HMAC-SHA256 hex digest."""
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return query_string, signature

    def build_signed_request(self, method, path, params=None):
        """Build a fully signed request with URL, headers, and method."""
        if params is None:
            params = {}
        params["timestamp"] = str(int(time.time() * 1000))
        query_string, signature = self.sign_params(params)
        url = (self.base_url + path + "?" + query_string
               + "&signature=" + signature)
        headers = {"X-BX-APIKEY": self.api_key}
        return {"url": url, "headers": headers, "method": method}

    def build_public_url(self, path, params=None):
        """Build public URL — no timestamp, no signature (BUG-C07 fix)."""
        if params is None:
            params = {}
        if params:
            query_string = urlencode(sorted(params.items()))
            return self.base_url + path + "?" + query_string
        return self.base_url + path
'''
    write_and_verify("bingx_auth.py", content)


# ---------------------------------------------------------------------------
# 6. notifier.py
# ---------------------------------------------------------------------------
def build_notifier():
    """Generate Telegram notifier module."""
    next_step("notifier.py")
    content = '''\
"""
Telegram notification sender. Never raises exceptions.
"""
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class Notifier:
    """Send timestamped messages to Telegram."""

    def __init__(self, bot_token, chat_id, enabled=True):
        """Initialize with Telegram bot credentials."""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled

    def send(self, message):
        """Send a message with UTC timestamp prefix. Returns True on success."""
        if not self.enabled:
            logger.debug("Notifier disabled, skip: %s", message[:80])
            return False
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        full_msg = "[" + ts + "] " + message
        url = ("https://api.telegram.org/bot" + self.bot_token
               + "/sendMessage")
        try:
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": full_msg,
                "parse_mode": "HTML",
            }, timeout=10)
            if resp.status_code == 200:
                logger.debug("Telegram sent: %s", message[:80])
                return True
            logger.warning("Telegram HTTP %d: %s",
                           resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            logger.warning("Telegram failed: %s", e)
            return False
'''
    write_and_verify("notifier.py", content)


# ---------------------------------------------------------------------------
# 7. state_manager.py
# ---------------------------------------------------------------------------
def build_state_manager():
    """Generate state persistence module."""
    next_step("state_manager.py")
    content = '''\
"""
State persistence: state.json (atomic write) + trades.csv (append).
Thread-safe with threading.Lock.
"""
import os
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
        state = dict(DEFAULT_STATE)
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

    def close_position(self, key, exit_price, exit_reason, pnl_net):
        """Close position, update daily_pnl, append to trades.csv."""
        with self.lock:
            pos = self.state["open_positions"].pop(key, None)
            if pos is None:
                logger.warning("close_position: key %s not found", key)
                return None
            self.state["daily_pnl"] += pnl_net
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
'''
    write_and_verify("state_manager.py", content)


# ---------------------------------------------------------------------------
# 8. plugins/__init__.py
# ---------------------------------------------------------------------------
def build_plugins_init():
    """Generate empty plugins package init."""
    next_step("plugins/__init__.py")
    write_and_verify("plugins/__init__.py", "")


# ---------------------------------------------------------------------------
# 9. plugins/mock_strategy.py
# ---------------------------------------------------------------------------
def build_mock_strategy():
    """Generate mock strategy plugin."""
    next_step("plugins/mock_strategy.py")
    content = '''\
"""
Mock strategy plugin for testing. Random signals with inject override.
"""
import random
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Strategy signal output."""
    direction: str
    grade: str
    entry_price: float
    sl_price: float
    tp_price: Optional[float]
    atr: float
    bar_ts: int


class MockStrategy:
    """Mock strategy that fires random signals at ~5% probability."""

    def __init__(self, config=None):
        """Initialize with optional config dict."""
        self.config = config or {}
        self.signal_probability = self.config.get(
            "signal_probability", 0.05)
        self._injected_signal = None
        logger.info("MockStrategy: prob=%.2f", self.signal_probability)

    def get_signal(self, ohlcv_df):
        """Return a Signal or None based on random probability."""
        if self._injected_signal is not None:
            sig = self._injected_signal
            self._injected_signal = None
            logger.info("MockStrategy: injected %s", sig.direction)
            return sig
        if random.random() > self.signal_probability:
            return None
        last = ohlcv_df.iloc[-1]
        close = float(last["close"])
        atr = close * 0.01
        direction = random.choice(["LONG", "SHORT"])
        if direction == "LONG":
            sl_price = close - (atr * 2.0)
            tp_price = close + (atr * 3.0)
        else:
            sl_price = close + (atr * 2.0)
            tp_price = close - (atr * 3.0)
        if "time" in ohlcv_df.columns:
            bar_ts = int(last["time"])
        else:
            bar_ts = 0
        signal = Signal(
            direction=direction,
            grade="MOCK",
            entry_price=close,
            sl_price=sl_price,
            tp_price=tp_price,
            atr=atr,
            bar_ts=bar_ts,
        )
        logger.info("MockStrategy: %s at %.6f", direction, close)
        return signal

    def inject_signal(self, signal):
        """Force the next get_signal() to return this signal."""
        self._injected_signal = signal

    def get_name(self):
        """Return strategy name."""
        return "MockStrategy"

    def get_version(self):
        """Return strategy version."""
        return "1.0.0"

    def warmup_bars(self):
        """Return warmup bars needed. Mock needs 0."""
        return 0

    def get_allowed_grades(self):
        """Return list of grades this strategy produces."""
        return ["MOCK"]
'''
    write_and_verify("plugins/mock_strategy.py", content)


# ---------------------------------------------------------------------------
# 10. data_fetcher.py
# ---------------------------------------------------------------------------
def build_data_fetcher():
    """Generate market data feed module."""
    next_step("data_fetcher.py")
    content = '''\
"""
Market data feed: polls BingX klines, detects new bars, fires callbacks.
Uses v3 endpoint for public market data (BUG-C07 fix: no auth).
"""
import logging
import requests
import pandas as pd

logger = logging.getLogger(__name__)

KLINES_PATH = "/openApi/swap/v3/quote/klines"


class MarketDataFeed:
    """Polls BingX klines and detects new closed bars."""

    def __init__(self, base_url, symbols, timeframe="5m",
                 buffer_bars=200, poll_interval=30):
        """Initialize with exchange URL and symbol list."""
        self.base_url = base_url
        self.symbols = symbols
        self.timeframe = timeframe
        self.buffer_bars = buffer_bars
        self.poll_interval = poll_interval
        self.buffers = {}
        self.last_bar_ts = {}
        logger.info("MarketDataFeed: %d symbols, tf=%s, buffer=%d",
                     len(symbols), timeframe, buffer_bars)

    def _fetch_klines(self, symbol):
        """Fetch klines from BingX v3 public endpoint. Returns df or None."""
        params = {
            "symbol": symbol,
            "interval": self.timeframe,
            "limit": str(self.buffer_bars),
        }
        query_parts = []
        for k, v in sorted(params.items()):
            query_parts.append(k + "=" + v)
        url = self.base_url + KLINES_PATH + "?" + "&".join(query_parts)
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error("Klines API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            raw = data.get("data", [])
            if not raw:
                logger.warning("Klines empty for %s", symbol)
                return None
            if isinstance(raw[0], dict):
                df = pd.DataFrame(raw)
                col_map = {}
                for col in df.columns:
                    lc = col.lower()
                    if lc in ("open", "high", "low", "close",
                              "volume", "time"):
                        col_map[col] = lc
                df = df.rename(columns=col_map)
            elif isinstance(raw[0], list):
                ncols = len(raw[0])
                base_cols = ["time", "open", "close", "high",
                             "low", "volume"]
                extra = ["extra_" + str(i)
                         for i in range(max(0, ncols - 6))]
                df = pd.DataFrame(raw, columns=base_cols + extra)
            else:
                logger.error("Unknown kline format for %s", symbol)
                return None
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            if "time" in df.columns:
                df["time"] = pd.to_numeric(
                    df["time"], errors="coerce").astype("int64")
                df = df.sort_values("time").reset_index(drop=True)
            if len(df) > self.buffer_bars:
                df = df.tail(self.buffer_bars).reset_index(drop=True)
            return df
        except requests.exceptions.Timeout:
            logger.error("Klines timeout: %s", symbol)
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Klines connection failed: %s", symbol)
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("Klines HTTP %s: %s",
                         e.response.status_code, symbol)
            return None
        except (ValueError, KeyError) as e:
            logger.error("Klines parse error %s: %s", symbol, e)
            return None

    def _is_new_bar(self, symbol, df):
        """Check if the last CLOSED bar is newer than previously seen."""
        if df is None or len(df) < 2:
            return False
        closed_ts = int(df.iloc[-2]["time"])
        prev_ts = self.last_bar_ts.get(symbol, 0)
        if closed_ts > prev_ts:
            self.last_bar_ts[symbol] = closed_ts
            return True
        return False

    def warmup(self):
        """Initial fetch for all symbols at startup."""
        for symbol in self.symbols:
            df = self._fetch_klines(symbol)
            if df is not None:
                self.buffers[symbol] = df
                if len(df) >= 2:
                    self.last_bar_ts[symbol] = int(df.iloc[-2]["time"])
                logger.info("Warmup %s: %d bars", symbol, len(df))
            else:
                logger.warning("Warmup failed for %s", symbol)

    def tick(self, callback):
        """One polling cycle: fetch all symbols, fire on new bars."""
        for symbol in self.symbols:
            df = self._fetch_klines(symbol)
            if df is None:
                continue
            self.buffers[symbol] = df
            if self._is_new_bar(symbol, df):
                logger.info("New bar: %s ts=%d",
                            symbol, self.last_bar_ts[symbol])
                try:
                    callback(symbol, df)
                except Exception as e:
                    logger.error("Callback error %s: %s", symbol, e)
'''
    write_and_verify("data_fetcher.py", content)


# ---------------------------------------------------------------------------
# 11. risk_gate.py
# ---------------------------------------------------------------------------
def build_risk_gate():
    """Generate risk gate module."""
    next_step("risk_gate.py")
    content = '''\
"""
Risk gate: 6 ordered pre-trade checks. Returns (approved, reason).
BUG-C03 fix: check 1 reads halt_flag from state.
BUG-C05 fix: allowed_grades comes from plugin, not connector config.
"""
import logging

logger = logging.getLogger(__name__)


class RiskGate:
    """Evaluate signals against risk rules before execution."""

    def __init__(self, config):
        """Initialize with risk config dict."""
        self.max_positions = config.get("max_positions", 3)
        self.max_daily_trades = config.get("max_daily_trades", 20)
        self.daily_loss_limit = config.get("daily_loss_limit_usd", 75.0)
        self.min_atr_ratio = config.get("min_atr_ratio", 0.003)
        logger.info(
            "RiskGate: max_pos=%d max_trades=%d loss=%.1f atr=%.4f",
            self.max_positions, self.max_daily_trades,
            self.daily_loss_limit, self.min_atr_ratio)

    def evaluate(self, signal, symbol, state, allowed_grades):
        """Run 6 ordered checks. Returns (bool, str)."""
        # Check 1: Hard stop (BUG-C03: halt_flag OR daily_pnl)
        halt = state.get("halt_flag", False)
        pnl = state.get("daily_pnl", 0)
        if halt or pnl <= -self.daily_loss_limit:
            reason = ("BLOCKED: Hard Stop (halt="
                      + str(halt) + " pnl="
                      + str(round(pnl, 2)) + ")")
            logger.warning("Check 1 FAIL: %s", reason)
            return False, reason

        # Check 2: Max positions
        open_count = len(state.get("open_positions", {}))
        if open_count >= self.max_positions:
            reason = ("BLOCKED: Max Positions ("
                      + str(open_count) + "/"
                      + str(self.max_positions) + ")")
            logger.info("Check 2 FAIL: %s", reason)
            return False, reason

        # Check 3: Duplicate position
        key = symbol + "_" + signal.direction
        if key in state.get("open_positions", {}):
            reason = "BLOCKED: Duplicate (" + key + ")"
            logger.info("Check 3 FAIL: %s", reason)
            return False, reason

        # Check 4: Grade filter (BUG-C05: from plugin)
        if signal.grade not in allowed_grades:
            reason = ("BLOCKED: Grade " + signal.grade
                      + " not in " + str(allowed_grades))
            logger.info("Check 4 FAIL: %s", reason)
            return False, reason

        # Check 5: ATR threshold
        if signal.entry_price > 0:
            atr_ratio = signal.atr / signal.entry_price
        else:
            atr_ratio = 0
        if atr_ratio < self.min_atr_ratio:
            reason = ("BLOCKED: Too Quiet (atr_ratio="
                      + str(round(atr_ratio, 6)) + ")")
            logger.info("Check 5 FAIL: %s", reason)
            return False, reason

        # Check 6: Daily trade limit
        daily_trades = state.get("daily_trades", 0)
        if daily_trades >= self.max_daily_trades:
            reason = ("BLOCKED: Trade Limit ("
                      + str(daily_trades) + "/"
                      + str(self.max_daily_trades) + ")")
            logger.info("Check 6 FAIL: %s", reason)
            return False, reason

        logger.info(
            "RiskGate APPROVED: %s %s grade=%s atr=%.4f",
            signal.direction, symbol, signal.grade, atr_ratio)
        return True, "APPROVED"
'''
    write_and_verify("risk_gate.py", content)


# ---------------------------------------------------------------------------
# 12. executor.py
# ---------------------------------------------------------------------------
def build_executor():
    """Generate order executor module."""
    next_step("executor.py")
    content = '''\
"""
Order executor: mark price, qty calc, order placement with SL/TP.
Uses v2 endpoints for all signed operations.
BUG-C02 fix: mark price from /quote/price, not /quote/klines.
"""
import json
import math
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

PRICE_PATH = "/openApi/swap/v2/quote/price"
CONTRACTS_PATH = "/openApi/swap/v2/quote/contracts"
ORDER_PATH = "/openApi/swap/v2/trade/order"


class Executor:
    """Execute trades on BingX with SL/TP attached."""

    def __init__(self, auth, state_manager, notifier, position_config):
        """Initialize with auth, state, notifier, position settings."""
        self.auth = auth
        self.state = state_manager
        self.notifier = notifier
        self.margin_usd = position_config.get("margin_usd", 50.0)
        self.leverage = position_config.get("leverage", 10)
        self.sl_working_type = position_config.get(
            "sl_working_type", "MARK_PRICE")
        self.tp_working_type = position_config.get(
            "tp_working_type", "MARK_PRICE")
        logger.info("Executor: margin=%.0f leverage=%d",
                     self.margin_usd, self.leverage)

    def _safe_get(self, url, headers=None):
        """Execute GET with error handling. Returns dict or None."""
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error("API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data
        except requests.exceptions.Timeout:
            logger.error("Timeout: GET %s", url[:100])
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Connection failed: GET %s", url[:100])
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP %s: GET %s",
                         e.response.status_code, url[:100])
            return None
        except ValueError:
            logger.error("Invalid JSON: GET %s", url[:100])
            return None

    def _safe_post(self, url, headers=None):
        """Execute POST with error handling. Returns dict or None."""
        try:
            resp = requests.post(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error("API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data
        except requests.exceptions.Timeout:
            logger.error("Timeout: POST %s", url[:100])
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Connection failed: POST %s", url[:100])
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP %s: POST %s",
                         e.response.status_code, url[:100])
            return None
        except ValueError:
            logger.error("Invalid JSON: POST %s", url[:100])
            return None

    def fetch_mark_price(self, symbol):
        """Fetch current mark price. Returns float or None."""
        url = self.auth.build_public_url(
            PRICE_PATH, {"symbol": symbol})
        data = self._safe_get(url)
        if data is None:
            return None
        try:
            price_data = data.get("data", {})
            if isinstance(price_data, dict):
                return float(price_data.get("price", 0))
            if isinstance(price_data, list) and price_data:
                return float(price_data[0].get("price", 0))
            logger.error("Unexpected price format: %s", symbol)
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error("Price parse error %s: %s", symbol, e)
            return None

    def fetch_step_size(self, symbol):
        """Fetch step size for a symbol. Returns float or None."""
        url = self.auth.build_public_url(CONTRACTS_PATH)
        data = self._safe_get(url)
        if data is None:
            return None
        try:
            contracts = data.get("data", [])
            for c in contracts:
                if c.get("symbol") == symbol:
                    return float(c.get("tradeMinQuantity",
                                       c.get("stepSize", 1)))
            logger.error("Symbol %s not found in contracts", symbol)
            return None
        except (ValueError, TypeError) as e:
            logger.error("Step size parse error %s: %s", symbol, e)
            return None

    def _round_down(self, value, step):
        """Round value DOWN to the nearest step increment."""
        if step <= 0:
            return value
        return math.floor(value / step) * step

    def execute(self, signal, symbol):
        """Execute trade: price, qty, order+SL+TP. Returns dict or None."""
        mark_price = self.fetch_mark_price(symbol)
        if mark_price is None or mark_price <= 0:
            logger.error("Cannot execute %s: no mark price", symbol)
            return None
        step_size = self.fetch_step_size(symbol)
        if step_size is None:
            logger.error("Cannot execute %s: no step size", symbol)
            return None
        notional = self.margin_usd * self.leverage
        raw_qty = notional / mark_price
        quantity = self._round_down(raw_qty, step_size)
        if quantity <= 0:
            logger.error("Qty zero: %s raw=%.8f step=%.8f",
                         symbol, raw_qty, step_size)
            return None
        side = "BUY" if signal.direction == "LONG" else "SELL"
        position_side = signal.direction
        order_params = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": "MARKET",
            "quantity": str(quantity),
        }
        sl_order = {
            "type": "STOP_MARKET",
            "stopPrice": signal.sl_price,
            "workingType": self.sl_working_type,
        }
        order_params["stopLoss"] = json.dumps(sl_order, separators=(',', ':'))
        if signal.tp_price is not None:
            tp_order = {
                "type": "TAKE_PROFIT_MARKET",
                "stopPrice": signal.tp_price,
                "workingType": self.tp_working_type,
            }
            order_params["takeProfit"] = json.dumps(tp_order, separators=(',', ':'))
        req = self.auth.build_signed_request(
            "POST", ORDER_PATH, order_params)
        logger.info(
            "Order: %s %s qty=%.6f mark=%.6f notional=%.2f",
            side, symbol, quantity, mark_price, notional)
        result = self._safe_post(req["url"], headers=req["headers"])
        if result is None:
            logger.error("Order failed: %s", symbol)
            self.notifier.send("ORDER FAILED: " + side + " " + symbol)
            return None
        order_data = result.get("data", {})
        order_id = str(order_data.get("orderId",
                       order_data.get("order", {}).get(
                           "orderId", "unknown")))
        position_record = {
            "symbol": symbol,
            "direction": signal.direction,
            "grade": signal.grade,
            "entry_price": mark_price,
            "sl_price": signal.sl_price,
            "tp_price": signal.tp_price,
            "quantity": quantity,
            "notional_usd": notional,
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "order_id": order_id,
            "atr_at_entry": signal.atr,
        }
        key = symbol + "_" + signal.direction
        self.state.record_open_position(key, position_record)
        entry_msg = ("ENTRY: " + side + " " + symbol
                     + " qty=" + str(round(quantity, 6))
                     + " price=" + str(round(mark_price, 6))
                     + " SL=" + str(round(signal.sl_price, 6))
                     + " grade=" + signal.grade)
        if signal.tp_price is not None:
            entry_msg += " TP=" + str(round(signal.tp_price, 6))
        self.notifier.send(entry_msg)
        logger.info("Order placed: %s id=%s", key, order_id)
        return result
'''
    write_and_verify("executor.py", content)


# ---------------------------------------------------------------------------
# 13. signal_engine.py
# ---------------------------------------------------------------------------
def build_signal_engine():
    """Generate strategy adapter module."""
    next_step("signal_engine.py")
    content = '''\
"""
Strategy adapter: loads plugin, orchestrates signal flow on new bars.
"""
import importlib
import logging

logger = logging.getLogger(__name__)


class StrategyAdapter:
    """Load strategy plugin and drive signal-to-execution pipeline."""

    def __init__(self, plugin_name, risk_gate, executor,
                 state_manager, notifier):
        """Initialize with plugin name and downstream components."""
        self.plugin = self._load_plugin(plugin_name)
        self.risk_gate = risk_gate
        self.executor = executor
        self.state_manager = state_manager
        self.notifier = notifier
        self.warmup_needed = self.plugin.warmup_bars()
        self.allowed_grades = self.plugin.get_allowed_grades()
        logger.info(
            "StrategyAdapter: plugin=%s v%s warmup=%d grades=%s",
            self.plugin.get_name(), self.plugin.get_version(),
            self.warmup_needed, str(self.allowed_grades))

    def _load_plugin(self, plugin_name):
        """Dynamically load a strategy plugin from plugins package."""
        try:
            module = importlib.import_module("plugins." + plugin_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                        and hasattr(attr, "get_signal")
                        and attr_name != "Signal"):
                    instance = attr()
                    logger.info("Loaded plugin: %s", attr_name)
                    return instance
            raise ImportError(
                "No strategy class in plugins." + plugin_name)
        except ImportError as e:
            logger.error("Plugin load failed: %s", e)
            raise

    def on_new_bar(self, symbol, ohlcv_df):
        """Process a new confirmed bar through the signal pipeline."""
        if len(ohlcv_df) < self.warmup_needed + 1:
            logger.debug("Warmup: %s has %d/%d bars",
                         symbol, len(ohlcv_df), self.warmup_needed + 1)
            return
        try:
            signal = self.plugin.get_signal(ohlcv_df)
        except Exception as e:
            logger.error("Plugin error %s: %s", symbol, e)
            return
        if signal is None or signal.direction == "NONE":
            logger.debug("No signal: %s", symbol)
            return
        logger.info("Signal: %s %s grade=%s price=%.6f",
                     signal.direction, symbol,
                     signal.grade, signal.entry_price)
        state_dict = self.state_manager.get_state()
        approved, reason = self.risk_gate.evaluate(
            signal, symbol, state_dict, self.allowed_grades)
        if not approved:
            logger.info("Blocked: %s %s — %s",
                         signal.direction, symbol, reason)
            return
        result = self.executor.execute(signal, symbol)
        if result is None:
            logger.error("Execution failed: %s %s",
                          signal.direction, symbol)
'''
    write_and_verify("signal_engine.py", content)


# ---------------------------------------------------------------------------
# 14. position_monitor.py
# ---------------------------------------------------------------------------
def build_position_monitor():
    """Generate position monitor module."""
    next_step("position_monitor.py")
    content = '''\
"""
Position monitor: polls exchange, detects closes, daily reset.
BUG-C04 fix: halt_flag reset at 17:00 UTC.
"""
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

POSITIONS_PATH = "/openApi/swap/v2/user/positions"


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
        logger.info("PositionMonitor: loss=%.1f reset_h=%d",
                     self.daily_loss_limit, self.daily_summary_hour)

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
        exit_price = sl_price
        exit_reason = "SL"
        if direction == "LONG":
            pnl_gross = (exit_price - entry_price) * quantity
        else:
            pnl_gross = (entry_price - exit_price) * quantity
        commission = notional * 0.0008 * 2
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
'''
    write_and_verify("position_monitor.py", content)


# ---------------------------------------------------------------------------
# 15. main.py
# ---------------------------------------------------------------------------
def build_main():
    """Generate main entry point."""
    next_step("main.py")
    content = '''\
"""
BingX Connector main entry point.
Two daemon threads: market polling + position monitoring.
Run: python main.py
"""
import os
import sys
import yaml
import logging
import threading
import signal as signal_mod
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

from bingx_auth import BingXAuth
from notifier import Notifier
from state_manager import StateManager
from data_fetcher import MarketDataFeed
from risk_gate import RiskGate
from executor import Executor
from signal_engine import StrategyAdapter
from position_monitor import PositionMonitor

logger = logging.getLogger(__name__)

LEVERAGE_PATH = "/openApi/swap/v2/trade/leverage"
MARGIN_TYPE_PATH = "/openApi/swap/v2/trade/marginType"


def setup_logging():
    """Configure dual logging: file + console with timestamps."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config():
    """Load config.yaml from the script directory."""
    config_path = Path(__file__).resolve().parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_leverage_and_margin(auth, symbols, leverage, margin_mode):
    """Set leverage and margin mode for each symbol at startup."""
    for symbol in symbols:
        req = auth.build_signed_request("POST", LEVERAGE_PATH, {
            "symbol": symbol,
            "side": "BOTH",
            "leverage": str(leverage),
        })
        try:
            resp = requests.post(
                req["url"], headers=req["headers"], timeout=10)
            data = resp.json()
            if data.get("code", 0) == 0:
                logger.info("Leverage: %s -> %dx", symbol, leverage)
            else:
                logger.warning("Leverage fail %s: %s",
                               symbol, data.get("msg"))
        except Exception as e:
            logger.error("Leverage error %s: %s", symbol, e)
        req = auth.build_signed_request("POST", MARGIN_TYPE_PATH, {
            "symbol": symbol,
            "marginType": margin_mode,
        })
        try:
            resp = requests.post(
                req["url"], headers=req["headers"], timeout=10)
            data = resp.json()
            if data.get("code", 0) == 0:
                logger.info("Margin: %s -> %s", symbol, margin_mode)
            else:
                logger.debug("Margin %s: %s",
                             symbol, data.get("msg"))
        except Exception as e:
            logger.error("Margin error %s: %s", symbol, e)


def market_loop(feed, adapter, shutdown_event, poll_interval):
    """Market data polling loop (daemon thread)."""
    logger.info("Market loop started: %ds", poll_interval)
    while not shutdown_event.is_set():
        try:
            feed.tick(callback=adapter.on_new_bar)
        except Exception as e:
            logger.error("Market loop error: %s", e, exc_info=True)
        shutdown_event.wait(poll_interval)
    logger.info("Market loop stopped")


def monitor_loop(monitor, shutdown_event, check_interval):
    """Position monitor polling loop (daemon thread)."""
    logger.info("Monitor loop started: %ds", check_interval)
    while not shutdown_event.is_set():
        try:
            monitor.check()
            monitor.check_daily_reset()
        except Exception as e:
            logger.error("Monitor loop error: %s", e, exc_info=True)
        shutdown_event.wait(check_interval)
    logger.info("Monitor loop stopped")


def main():
    """Load config, init components, run loops."""
    setup_logging()
    logger.info("=== BingX Connector Starting ===")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info("Startup: %s", ts)
    load_dotenv()
    api_key = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not api_key or not secret_key:
        logger.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY")
        sys.exit(1)
    config = load_config()
    conn = config.get("connector", {})
    risk_cfg = config.get("risk", {})
    pos_cfg = config.get("position", {})
    strat_cfg = config.get("strategy", {})
    notif_cfg = config.get("notification", {})
    symbols = config.get("coins", [])
    demo_mode = conn.get("demo_mode", True)
    poll_interval = conn.get("poll_interval_sec", 30)
    check_interval = conn.get("position_check_sec", 60)
    timeframe = conn.get("timeframe", "5m")
    buffer_bars = conn.get("ohlcv_buffer_bars", 200)
    logger.info("Config: demo=%s coins=%s tf=%s poll=%ds",
                demo_mode, str(symbols), timeframe, poll_interval)
    auth = BingXAuth(api_key, secret_key, demo_mode=demo_mode)
    notifier = Notifier(tg_token, tg_chat, enabled=bool(tg_token))
    root_dir = Path(__file__).resolve().parent
    state_mgr = StateManager(
        state_path=root_dir / "state.json",
        trades_path=root_dir / "trades.csv",
    )
    feed = MarketDataFeed(
        base_url=auth.base_url,
        symbols=symbols,
        timeframe=timeframe,
        buffer_bars=buffer_bars,
        poll_interval=poll_interval,
    )
    risk_gate = RiskGate(risk_cfg)
    executor_inst = Executor(auth, state_mgr, notifier, pos_cfg)
    adapter = StrategyAdapter(
        plugin_name=strat_cfg.get("plugin", "mock_strategy"),
        risk_gate=risk_gate,
        executor=executor_inst,
        state_manager=state_mgr,
        notifier=notifier,
    )
    monitor_cfg = dict(risk_cfg)
    monitor_cfg["daily_summary_utc_hour"] = notif_cfg.get(
        "daily_summary_utc_hour", 17)
    monitor = PositionMonitor(
        auth, state_mgr, notifier, monitor_cfg)
    logger.info("Setting leverage and margin mode...")
    set_leverage_and_margin(
        auth, symbols,
        pos_cfg.get("leverage", 10),
        pos_cfg.get("margin_mode", "ISOLATED"))
    logger.info("Reconciling state with exchange...")
    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    try:
        resp = requests.get(
            req["url"], headers=req["headers"], timeout=10)
        live_pos = resp.json().get("data", [])
        state_mgr.reconcile(live_pos)
    except Exception as e:
        logger.error("Reconcile failed: %s — using local state", e)
    logger.info("Warming up market data...")
    feed.warmup()
    open_count = len(state_mgr.get_open_positions())
    start_msg = ("Bot started: "
                 + str(len(symbols)) + " coins, "
                 + str(open_count) + " open, "
                 + ("DEMO" if demo_mode else "LIVE"))
    notifier.send(start_msg)
    logger.info(start_msg)
    shutdown_event = threading.Event()

    def on_signal(signum, frame):
        """Handle shutdown signal."""
        logger.info("Shutdown signal received")
        shutdown_event.set()

    signal_mod.signal(signal_mod.SIGINT, on_signal)
    signal_mod.signal(signal_mod.SIGTERM, on_signal)
    t1 = threading.Thread(
        target=market_loop,
        args=(feed, adapter, shutdown_event, poll_interval),
        daemon=True, name="MarketLoop")
    t2 = threading.Thread(
        target=monitor_loop,
        args=(monitor, shutdown_event, check_interval),
        daemon=True, name="MonitorLoop")
    t1.start()
    t2.start()
    logger.info("Threads started: MarketLoop + MonitorLoop")
    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(1.0)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — shutting down")
        shutdown_event.set()
    t1.join(timeout=5)
    t2.join(timeout=5)
    notifier.send("Bot stopped")
    logger.info("=== BingX Connector Stopped ===")


if __name__ == "__main__":
    main()
'''
    write_and_verify("main.py", content)


# ---------------------------------------------------------------------------
# 16. tests/__init__.py
# ---------------------------------------------------------------------------
def build_tests_init():
    """Generate empty tests package init."""
    next_step("tests/__init__.py")
    write_and_verify("tests/__init__.py", "")


# ---------------------------------------------------------------------------
# 17. tests/test_auth.py
# ---------------------------------------------------------------------------
def build_test_auth():
    """Generate auth unit tests."""
    next_step("tests/test_auth.py")
    content = '''\
"""
Tests for bingx_auth.py — HMAC signature correctness.
Run: python -m pytest tests/test_auth.py -v
"""
import sys
import hashlib
import hmac
import unittest
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bingx_auth import BingXAuth


class TestBingXAuth(unittest.TestCase):
    """Test HMAC signing, public URLs, demo toggle."""

    def setUp(self):
        """Set up test auth instance."""
        self.auth = BingXAuth(
            "test_api_key", "test_secret", demo_mode=True)

    def test_sign_params_known_vector(self):
        """Known input produces correct HMAC-SHA256 hex digest."""
        params = {
            "symbol": "BTC-USDT",
            "side": "BUY",
            "timestamp": "1700000000000",
        }
        qs, sig = self.auth.sign_params(params)
        expected_qs = urlencode(sorted(params.items()))
        self.assertEqual(qs, expected_qs,
                         msg="Query string not sorted: " + qs)
        expected_sig = hmac.new(
            b"test_secret",
            expected_qs.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(sig, expected_sig,
                         msg="Signature mismatch: " + sig)

    def test_public_url_no_signature(self):
        """Public URL has no signature or timestamp."""
        url = self.auth.build_public_url(
            "/test/path", {"symbol": "BTC-USDT"})
        self.assertNotIn("signature", url,
                         msg="Public URL has sig: " + url)
        self.assertNotIn("timestamp", url,
                         msg="Public URL has ts: " + url)

    def test_public_url_no_params(self):
        """Public URL with no params is base + path."""
        url = self.auth.build_public_url("/test/path")
        self.assertTrue(url.endswith("/test/path"),
                        msg="URL wrong: " + url)

    def test_demo_url_toggle(self):
        """demo_mode=True uses VST, False uses live."""
        demo = BingXAuth("k", "s", demo_mode=True)
        self.assertIn("open-api-vst.bingx.com", demo.base_url,
                       msg="Demo URL: " + demo.base_url)
        live = BingXAuth("k", "s", demo_mode=False)
        self.assertIn("open-api.bingx.com", live.base_url,
                       msg="Live URL: " + live.base_url)
        self.assertNotIn("vst", live.base_url,
                          msg="Live has vst: " + live.base_url)

    def test_signed_request_structure(self):
        """Signed request has timestamp, signature, API key header."""
        req = self.auth.build_signed_request(
            "GET", "/test", {"symbol": "ETH-USDT"})
        self.assertIn("timestamp=", req["url"],
                       msg="No ts: " + req["url"])
        self.assertIn("signature=", req["url"],
                       msg="No sig: " + req["url"])
        self.assertEqual(
            req["headers"]["X-BX-APIKEY"], "test_api_key",
            msg="API key header wrong")
        self.assertEqual(req["method"], "GET")

    def test_params_sorted_alphabetically(self):
        """Signed params are sorted alphabetically."""
        params = {"zebra": "1", "alpha": "2", "middle": "3"}
        req = self.auth.build_signed_request("POST", "/t", params)
        url = req["url"]
        qs_start = url.index("?") + 1
        sig_start = url.index("&signature=")
        qs = url[qs_start:sig_start]
        parts = qs.split("&")
        keys = [p.split("=")[0] for p in parts]
        self.assertEqual(keys, sorted(keys),
                         msg="Not sorted: " + str(keys))


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_auth.py", content)


# ---------------------------------------------------------------------------
# 18. tests/test_risk_gate.py
# ---------------------------------------------------------------------------
def build_test_risk_gate():
    """Generate risk gate unit tests."""
    next_step("tests/test_risk_gate.py")
    content = '''\
"""
Tests for risk_gate.py — all 6 checks in isolation.
Run: python -m pytest tests/test_risk_gate.py -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from risk_gate import RiskGate


class MockSignal:
    """Mock signal for risk gate testing."""

    def __init__(self, direction="LONG", grade="A",
                 entry_price=100.0, atr=0.5,
                 sl_price=99.0, tp_price=101.0, bar_ts=0):
        """Initialize mock signal fields."""
        self.direction = direction
        self.grade = grade
        self.entry_price = entry_price
        self.atr = atr
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.bar_ts = bar_ts


class TestRiskGate(unittest.TestCase):
    """Test all 6 risk gate checks."""

    def setUp(self):
        """Set up risk gate with default config."""
        self.gate = RiskGate({
            "max_positions": 3,
            "max_daily_trades": 20,
            "daily_loss_limit_usd": 75.0,
            "min_atr_ratio": 0.003,
        })

    def _clean_state(self):
        """Return a clean state dict."""
        return {
            "open_positions": {},
            "daily_pnl": 0.0,
            "daily_trades": 0,
            "halt_flag": False,
        }

    def test_check1_halt_flag_blocks(self):
        """Check 1: halt_flag=True blocks."""
        state = self._clean_state()
        state["halt_flag"] = True
        ok, reason = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="halt_flag should block")
        self.assertIn("Hard Stop", reason)

    def test_check1_daily_pnl_at_limit(self):
        """Check 1: daily_pnl exactly at -75.0 blocks."""
        state = self._clean_state()
        state["daily_pnl"] = -75.0
        ok, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="-75.0 should block (<=)")

    def test_check1_daily_pnl_below_limit(self):
        """Check 1: daily_pnl below limit blocks."""
        state = self._clean_state()
        state["daily_pnl"] = -80.0
        ok, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="-80 should block")

    def test_check1_c03_halt_or_pnl(self):
        """BUG-C03: halt_flag alone blocks even if pnl ok."""
        state = self._clean_state()
        state["halt_flag"] = True
        state["daily_pnl"] = 0.0
        ok, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="halt alone should block (C03)")

    def test_check2_max_positions(self):
        """Check 2: max positions blocks."""
        state = self._clean_state()
        state["open_positions"] = {
            "A_L": {}, "B_L": {}, "C_L": {}}
        ok, reason = self.gate.evaluate(
            MockSignal(), "D-USDT", state, ["A"])
        self.assertFalse(ok, msg="3/3 should block")
        self.assertIn("Max Positions", reason)

    def test_check3_duplicate(self):
        """Check 3: duplicate symbol+direction blocks."""
        state = self._clean_state()
        state["open_positions"] = {"BTC-USDT_LONG": {}}
        ok, reason = self.gate.evaluate(
            MockSignal(direction="LONG"),
            "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="Duplicate should block")
        self.assertIn("Duplicate", reason)

    def test_check3_opposite_ok(self):
        """Check 3: opposite direction passes."""
        state = self._clean_state()
        state["open_positions"] = {"BTC-USDT_LONG": {}}
        ok, _ = self.gate.evaluate(
            MockSignal(direction="SHORT"),
            "BTC-USDT", state, ["A"])
        self.assertTrue(ok, msg="Opposite should pass")

    def test_check4_grade_filter(self):
        """Check 4: grade not in allowed list blocks."""
        state = self._clean_state()
        ok, reason = self.gate.evaluate(
            MockSignal(grade="C"),
            "BTC-USDT", state, ["A", "B"])
        self.assertFalse(ok, msg="Grade C not in [A,B]")
        self.assertIn("Grade", reason)

    def test_check4_c05_plugin_grades(self):
        """BUG-C05: allowed_grades from plugin."""
        state = self._clean_state()
        ok, _ = self.gate.evaluate(
            MockSignal(grade="MOCK"),
            "BTC-USDT", state, ["MOCK"])
        self.assertTrue(ok, msg="MOCK grade should pass")

    def test_check5_atr_threshold(self):
        """Check 5: low ATR ratio blocks."""
        state = self._clean_state()
        ok, reason = self.gate.evaluate(
            MockSignal(entry_price=100.0, atr=0.1),
            "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="ATR 0.001 should block")
        self.assertIn("Too Quiet", reason)

    def test_check6_daily_trade_limit(self):
        """Check 6: daily trade limit blocks."""
        state = self._clean_state()
        state["daily_trades"] = 20
        ok, reason = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        self.assertFalse(ok, msg="20/20 should block")
        self.assertIn("Trade Limit", reason)

    def test_check_order_halt_before_max(self):
        """Halt blocks before max_positions is checked."""
        state = self._clean_state()
        state["halt_flag"] = True
        state["open_positions"] = {
            "A_L": {}, "B_L": {}, "C_L": {}}
        ok, reason = self.gate.evaluate(
            MockSignal(), "D-USDT", state, ["A"])
        self.assertFalse(ok)
        self.assertIn("Hard Stop", reason,
                       msg="Should be Hard Stop: " + reason)

    def test_halt_persists(self):
        """halt_flag survives across evaluate() calls."""
        state = self._clean_state()
        state["halt_flag"] = True
        ok1, _ = self.gate.evaluate(
            MockSignal(), "BTC-USDT", state, ["A"])
        ok2, _ = self.gate.evaluate(
            MockSignal(), "ETH-USDT", state, ["A"])
        self.assertFalse(ok1, msg="First call blocked")
        self.assertFalse(ok2, msg="Second call blocked")

    def test_approved_path(self):
        """Clean state + valid signal -> APPROVED."""
        state = self._clean_state()
        ok, reason = self.gate.evaluate(
            MockSignal(grade="A", atr=0.5, entry_price=100.0),
            "BTC-USDT", state, ["A"])
        self.assertTrue(ok, msg="Should approve: " + reason)
        self.assertEqual(reason, "APPROVED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_risk_gate.py", content)


# ---------------------------------------------------------------------------
# 19. tests/test_executor.py
# ---------------------------------------------------------------------------
def build_test_executor():
    """Generate executor unit tests."""
    next_step("tests/test_executor.py")
    content = '''\
"""
Tests for executor.py — order construction with mocked HTTP.
Run: python -m pytest tests/test_executor.py -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from executor import Executor
from bingx_auth import BingXAuth


class MockSignal:
    """Mock signal for executor testing."""

    def __init__(self, direction="LONG", grade="A",
                 entry_price=100.0, sl_price=98.0,
                 tp_price=103.0, atr=1.0, bar_ts=0):
        """Initialize mock signal."""
        self.direction = direction
        self.grade = grade
        self.entry_price = entry_price
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.atr = atr
        self.bar_ts = bar_ts


def _mock_resp(json_data):
    """Create a mock HTTP response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data
    return resp


class TestExecutor(unittest.TestCase):
    """Test order construction and quantity calculation."""

    def setUp(self):
        """Set up executor with mocked deps."""
        self.auth = BingXAuth("k", "s", demo_mode=True)
        self.state = MagicMock()
        self.notifier = MagicMock()
        self.executor = Executor(
            self.auth, self.state, self.notifier,
            {"margin_usd": 50.0, "leverage": 10})

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_quantity_calculation(self, mock_get, mock_post):
        """Qty = notional / mark_price, rounded down to step."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "0.005"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "TEST-USDT",
                 "tradeMinQuantity": "1"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "123"}})
        result = self.executor.execute(
            MockSignal(), "TEST-USDT")
        self.assertIsNotNone(result, msg="Should succeed")
        self.state.record_open_position.assert_called_once()
        pos = self.state.record_open_position.call_args[0][1]
        self.assertEqual(pos["quantity"], 100000.0,
                         msg="qty: " + str(pos["quantity"]))

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_long_payload(self, mock_get, mock_post):
        """LONG -> side=BUY, positionSide=LONG."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        self.executor.execute(
            MockSignal(direction="LONG"), "BTC-USDT")
        url = mock_post.call_args[0][0]
        self.assertIn("side=BUY", url,
                       msg="LONG->BUY: " + url[:200])
        self.assertIn("positionSide=LONG", url,
                       msg="LONG pos: " + url[:200])

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_short_payload(self, mock_get, mock_post):
        """SHORT -> side=SELL, positionSide=SHORT."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        self.executor.execute(
            MockSignal(direction="SHORT"), "BTC-USDT")
        url = mock_post.call_args[0][0]
        self.assertIn("side=SELL", url, msg="SHORT->SELL")
        self.assertIn("positionSide=SHORT", url,
                       msg="SHORT pos")

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_sl_tp_in_payload(self, mock_get, mock_post):
        """SL and TP present as JSON strings in URL."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": 0, "data": {"orderId": "1"}})
        self.executor.execute(
            MockSignal(sl_price=98.0, tp_price=103.0),
            "BTC-USDT")
        url = mock_post.call_args[0][0]
        self.assertIn("stopLoss=", url, msg="Missing SL")
        self.assertIn("takeProfit=", url, msg="Missing TP")

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_api_failure_returns_none(self, mock_get, mock_post):
        """API error -> None, no position recorded."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": 0, "data": [
                {"symbol": "BTC-USDT",
                 "tradeMinQuantity": "0.001"}]}),
        ]
        mock_post.return_value = _mock_resp(
            {"code": -1, "msg": "error"})
        result = self.executor.execute(
            MockSignal(), "BTC-USDT")
        self.assertIsNone(result, msg="Failed should be None")
        self.state.record_open_position.assert_not_called()

    @patch("executor.requests.get")
    def test_mark_price_failure(self, mock_get):
        """Mark price failure -> None, no order."""
        mock_get.return_value = _mock_resp(
            {"code": -1, "msg": "error"})
        result = self.executor.execute(
            MockSignal(), "BTC-USDT")
        self.assertIsNone(result, msg="No price -> None")

    @patch("executor.requests.get")
    def test_step_size_failure(self, mock_get):
        """Step size failure -> None, no order."""
        mock_get.side_effect = [
            _mock_resp({"code": 0,
                        "data": {"price": "100.0"}}),
            _mock_resp({"code": -1, "msg": "error"}),
        ]
        result = self.executor.execute(
            MockSignal(), "BTC-USDT")
        self.assertIsNone(result, msg="No step -> None")

    def test_round_down(self):
        """Round DOWN to step size."""
        rd = self.executor._round_down
        self.assertEqual(rd(10.7, 1.0), 10.0)
        self.assertEqual(rd(0.00567, 0.001), 0.005)
        self.assertEqual(rd(99.99, 0.01), 99.99)
        self.assertEqual(rd(1.0, 0.1), 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_executor.py", content)


# ---------------------------------------------------------------------------
# 20. tests/test_plugin_contract.py
# ---------------------------------------------------------------------------
def build_test_plugin_contract():
    """Generate plugin interface compliance tests."""
    next_step("tests/test_plugin_contract.py")
    content = '''\
"""
Tests for mock_strategy.py — interface compliance.
Run: python -m pytest tests/test_plugin_contract.py -v
"""
import sys
import unittest
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from plugins.mock_strategy import MockStrategy, Signal


class TestPluginContract(unittest.TestCase):
    """Test MockStrategy interface compliance."""

    def setUp(self):
        """Set up mock strategy."""
        self.strategy = MockStrategy(
            {"signal_probability": 0.05})

    def _make_ohlcv(self, n=100, price=0.01, seed=42):
        """Generate synthetic OHLCV for testing."""
        rng = np.random.default_rng(seed)
        close = price + np.cumsum(rng.normal(0, price * 0.01, n))
        close = np.clip(close, price * 0.5, price * 2)
        return pd.DataFrame({
            "open": close * rng.uniform(0.999, 1.001, n),
            "high": close * rng.uniform(1.000, 1.005, n),
            "low": close * rng.uniform(0.995, 1.000, n),
            "close": close,
            "volume": rng.integers(1e6, 1e7, n).astype(float),
            "time": range(1700000000000,
                          1700000000000 + n * 60000, 60000),
        })

    def test_has_required_methods(self):
        """MockStrategy has all 5 required methods."""
        for m in ["get_signal", "get_name", "get_version",
                   "warmup_bars", "get_allowed_grades"]:
            self.assertTrue(hasattr(self.strategy, m),
                            msg="Missing: " + m)
            self.assertTrue(callable(getattr(self.strategy, m)),
                            msg="Not callable: " + m)

    def test_get_signal_returns_signal_or_none(self):
        """get_signal returns Signal or None."""
        df = self._make_ohlcv()
        for _ in range(100):
            r = self.strategy.get_signal(df)
            self.assertTrue(
                r is None or isinstance(r, Signal),
                msg="Expected Signal/None: " + str(type(r)))

    def test_inject_signal(self):
        """inject_signal forces next output."""
        df = self._make_ohlcv()
        forced = Signal(
            direction="LONG", grade="MOCK",
            entry_price=100.0, sl_price=98.0,
            tp_price=103.0, atr=1.0, bar_ts=1700000000000)
        self.strategy.inject_signal(forced)
        result = self.strategy.get_signal(df)
        self.assertIs(result, forced, msg="Should be injected")

    def test_inject_clears_after_use(self):
        """Injected signal consumed after one call."""
        df = self._make_ohlcv()
        forced = Signal(
            direction="SHORT", grade="MOCK",
            entry_price=50.0, sl_price=52.0,
            tp_price=47.0, atr=0.5, bar_ts=0)
        self.strategy.inject_signal(forced)
        self.strategy.get_signal(df)
        results = [self.strategy.get_signal(df) for _ in range(20)]
        nones = sum(1 for r in results if r is None)
        self.assertGreater(nones, 0,
                           msg="Should be consumed after 1 use")

    def test_signal_fields(self):
        """Signal has all 7 fields with correct types."""
        sig = Signal(
            direction="LONG", grade="A",
            entry_price=100.0, sl_price=98.0,
            tp_price=103.0, atr=1.0, bar_ts=170000)
        self.assertIsInstance(sig.direction, str)
        self.assertIsInstance(sig.grade, str)
        self.assertIsInstance(sig.entry_price, float)
        self.assertIsInstance(sig.sl_price, float)
        self.assertIsInstance(sig.tp_price, float)
        self.assertIsInstance(sig.atr, float)
        self.assertIsInstance(sig.bar_ts, int)

    def test_signal_tp_none(self):
        """Signal tp_price can be None (runner mode)."""
        sig = Signal(
            direction="LONG", grade="A",
            entry_price=100.0, sl_price=98.0,
            tp_price=None, atr=1.0, bar_ts=0)
        self.assertIsNone(sig.tp_price)

    def test_allowed_grades_nonempty(self):
        """get_allowed_grades returns non-empty list of strings."""
        grades = self.strategy.get_allowed_grades()
        self.assertIsInstance(grades, list)
        self.assertGreater(len(grades), 0, msg="Empty grades")
        for g in grades:
            self.assertIsInstance(g, str)

    def test_warmup_bars_int(self):
        """warmup_bars returns int, MockStrategy returns 0."""
        wb = self.strategy.warmup_bars()
        self.assertIsInstance(wb, int)
        self.assertEqual(wb, 0)

    def test_name_and_version(self):
        """get_name and get_version return non-empty strings."""
        self.assertGreater(
            len(self.strategy.get_name()), 0)
        self.assertGreater(
            len(self.strategy.get_version()), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_plugin_contract.py", content)


# ---------------------------------------------------------------------------
# 21. tests/test_state_manager.py
# ---------------------------------------------------------------------------
def build_test_state_manager():
    """Generate state manager unit tests."""
    next_step("tests/test_state_manager.py")
    content = '''\
"""
Tests for state_manager.py — persistence, atomicity, threads.
Run: python -m pytest tests/test_state_manager.py -v
"""
import sys
import json
import unittest
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from state_manager import StateManager


class TestStateManager(unittest.TestCase):
    """Test state persistence and thread safety."""

    def setUp(self):
        """Set up temp directory for state files."""
        self.tmpdir = tempfile.mkdtemp()
        self.sp = Path(self.tmpdir) / "state.json"
        self.tp = Path(self.tmpdir) / "trades.csv"
        self.mgr = StateManager(self.sp, self.tp)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_open_position(self):
        """Position appears in state, daily_trades incremented."""
        self.mgr.record_open_position("BTC_LONG", {
            "symbol": "BTC-USDT", "direction": "LONG",
            "entry_price": 42000.0})
        s = self.mgr.get_state()
        self.assertIn("BTC_LONG", s["open_positions"])
        self.assertEqual(s["daily_trades"], 1)

    def test_close_position(self):
        """Close: removed from state, pnl updated, csv appended."""
        self.mgr.record_open_position("ETH_SHORT", {
            "symbol": "ETH-USDT", "direction": "SHORT",
            "grade": "A", "entry_price": 3000.0,
            "quantity": 1.0, "notional_usd": 500.0,
            "entry_time": "2026-01-01T00:00:00",
            "order_id": "123"})
        result = self.mgr.close_position(
            "ETH_SHORT", 2950.0, "TP", 50.0)
        self.assertIsNotNone(result)
        s = self.mgr.get_state()
        self.assertNotIn("ETH_SHORT", s["open_positions"])
        self.assertEqual(s["daily_pnl"], 50.0)
        self.assertTrue(self.tp.exists())

    def test_close_missing(self):
        """Closing non-existent position returns None."""
        result = self.mgr.close_position("FAKE", 0, "SL", -10)
        self.assertIsNone(result)

    def test_reset_daily(self):
        """reset_daily zeroes pnl, trades, halt (C04)."""
        self.mgr.record_open_position("A_L", {"symbol": "A"})
        self.mgr.close_position("A_L", 0, "SL", -50.0)
        self.mgr.set_halt_flag(True)
        self.mgr.reset_daily()
        s = self.mgr.get_state()
        self.assertEqual(s["daily_pnl"], 0.0)
        self.assertEqual(s["daily_trades"], 0)
        self.assertFalse(s["halt_flag"], msg="halt not reset")

    def test_atomic_persistence(self):
        """State persists on disk and can be reloaded."""
        self.mgr.record_open_position("X_L", {"symbol": "X"})
        mgr2 = StateManager(self.sp, self.tp)
        s = mgr2.get_state()
        self.assertIn("X_L", s["open_positions"])

    def test_load_empty(self):
        """Missing state.json returns defaults."""
        p = Path(self.tmpdir) / "no.json"
        mgr = StateManager(p, self.tp)
        s = mgr.get_state()
        self.assertEqual(len(s["open_positions"]), 0)
        self.assertEqual(s["daily_pnl"], 0.0)
        self.assertFalse(s["halt_flag"])

    def test_load_corrupt(self):
        """Corrupt state.json returns defaults."""
        self.sp.write_text("not json{{{", encoding="utf-8")
        mgr = StateManager(self.sp, self.tp)
        s = mgr.get_state()
        self.assertEqual(s["daily_pnl"], 0.0)

    def test_reconcile_removes_phantom(self):
        """Reconcile removes positions not on exchange."""
        self.mgr.record_open_position(
            "PHANTOM_LONG", {"symbol": "PHANTOM"})
        self.mgr.reconcile([])
        s = self.mgr.get_state()
        self.assertNotIn("PHANTOM_LONG", s["open_positions"])

    def test_reconcile_keeps_real(self):
        """Reconcile keeps positions on exchange."""
        self.mgr.record_open_position(
            "BTC-USDT_LONG", {"symbol": "BTC-USDT"})
        self.mgr.reconcile([
            {"symbol": "BTC-USDT", "positionAmt": "0.001"}])
        s = self.mgr.get_state()
        self.assertIn("BTC-USDT_LONG", s["open_positions"])

    def test_thread_safety(self):
        """Concurrent ops don't corrupt state."""
        errors = []

        def worker_record(n):
            """Record positions."""
            try:
                tid = threading.current_thread().ident
                for i in range(n):
                    key = "T" + str(tid) + "_" + str(i) + "_L"
                    self.mgr.record_open_position(
                        key, {"symbol": "T"})
            except Exception as e:
                errors.append(str(e))

        def worker_close():
            """Close positions."""
            try:
                for k in list(
                        self.mgr.get_open_positions().keys()):
                    self.mgr.close_position(k, 0, "T", 0)
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(3):
            t = threading.Thread(target=worker_record, args=(10,))
            threads.append(t)
            t.start()
        for _ in range(2):
            t = threading.Thread(target=worker_close)
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=5)
        self.assertEqual(len(errors), 0,
                         msg="Errors: " + ", ".join(errors))
        raw = self.sp.read_text(encoding="utf-8")
        state = json.loads(raw)
        self.assertIn("open_positions", state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_state_manager.py", content)


# ---------------------------------------------------------------------------
# 22. tests/test_data_fetcher.py
# ---------------------------------------------------------------------------
def build_test_data_fetcher():
    """Generate data fetcher unit tests."""
    next_step("tests/test_data_fetcher.py")
    content = '''\
"""
Tests for data_fetcher.py — kline fetch and new-bar detection.
Run: python -m pytest tests/test_data_fetcher.py -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_fetcher import MarketDataFeed


def _kline_resp(n=10, start_ts=1700000000000,
                interval_ms=300000):
    """Create a mock klines API response."""
    data = []
    for i in range(n):
        ts = start_ts + i * interval_ms
        data.append({
            "time": str(ts), "open": "100.0",
            "high": "101.0", "low": "99.0",
            "close": "100.5", "volume": "1000"})
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"code": 0, "data": data}
    return resp


class TestDataFetcher(unittest.TestCase):
    """Test kline fetch and new-bar detection."""

    def setUp(self):
        """Set up feed."""
        self.feed = MarketDataFeed(
            base_url="https://test.bingx.com",
            symbols=["BTC-USDT"],
            timeframe="5m", buffer_bars=200,
            poll_interval=30)

    @patch("data_fetcher.requests.get")
    def test_new_bar_same_ts(self, mock_get):
        """Same timestamp twice -> not new bar."""
        mock_get.return_value = _kline_resp(n=5)
        df = self.feed._fetch_klines("BTC-USDT")
        self.assertIsNotNone(df)
        self.feed.last_bar_ts["BTC-USDT"] = int(
            df.iloc[-2]["time"])
        result = self.feed._is_new_bar("BTC-USDT", df)
        self.assertFalse(result, msg="Same ts not new")

    @patch("data_fetcher.requests.get")
    def test_new_bar_new_ts(self, mock_get):
        """New timestamp -> new bar."""
        r1 = _kline_resp(n=5, start_ts=1700000000000)
        r2 = _kline_resp(n=5, start_ts=1700000300000)
        mock_get.side_effect = [r1, r2]
        df1 = self.feed._fetch_klines("BTC-USDT")
        self.feed.last_bar_ts["BTC-USDT"] = int(
            df1.iloc[-2]["time"])
        df2 = self.feed._fetch_klines("BTC-USDT")
        result = self.feed._is_new_bar("BTC-USDT", df2)
        self.assertTrue(result, msg="New ts should be new")

    @patch("data_fetcher.requests.get")
    def test_api_error(self, mock_get):
        """API error code returns None."""
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"code": -1, "msg": "err"}
        mock_get.return_value = resp
        result = self.feed._fetch_klines("BTC-USDT")
        self.assertIsNone(result)

    @patch("data_fetcher.requests.get")
    def test_timeout(self, mock_get):
        """Timeout returns None."""
        from requests.exceptions import Timeout
        mock_get.side_effect = Timeout("timeout")
        result = self.feed._fetch_klines("BTC-USDT")
        self.assertIsNone(result)

    @patch("data_fetcher.requests.get")
    def test_buffer_cap(self, mock_get):
        """Buffer caps at buffer_bars."""
        self.feed.buffer_bars = 10
        mock_get.return_value = _kline_resp(n=20)
        df = self.feed._fetch_klines("BTC-USDT")
        self.assertLessEqual(len(df), 10,
                             msg="Buffer: " + str(len(df)))

    @patch("data_fetcher.requests.get")
    def test_warmup(self, mock_get):
        """warmup populates all symbol buffers."""
        self.feed.symbols = ["BTC-USDT", "ETH-USDT"]
        mock_get.return_value = _kline_resp(n=5)
        self.feed.warmup()
        self.assertIn("BTC-USDT", self.feed.buffers)
        self.assertIn("ETH-USDT", self.feed.buffers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_data_fetcher.py", content)


# ---------------------------------------------------------------------------
# 23. tests/test_integration.py
# ---------------------------------------------------------------------------
def build_test_integration():
    """Generate integration test."""
    next_step("tests/test_integration.py")
    content = '''\
"""
Integration test: end-to-end signal-to-execution, all HTTP mocked.
Run: python -m pytest tests/test_integration.py -v
"""
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bingx_auth import BingXAuth
from notifier import Notifier
from state_manager import StateManager
from risk_gate import RiskGate
from executor import Executor
from position_monitor import PositionMonitor
from plugins.mock_strategy import Signal


def _resp(json_data):
    """Create mock HTTP response."""
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status = MagicMock()
    r.json.return_value = json_data
    return r


class TestIntegration(unittest.TestCase):
    """End-to-end integration with all HTTP mocked."""

    def setUp(self):
        """Set up all components with temp state."""
        self.tmpdir = tempfile.mkdtemp()
        sp = Path(self.tmpdir) / "state.json"
        tp = Path(self.tmpdir) / "trades.csv"
        self.auth = BingXAuth("k", "s", demo_mode=True)
        self.notifier = MagicMock(spec=Notifier)
        self.notifier.send = MagicMock(return_value=True)
        self.state_mgr = StateManager(sp, tp)
        self.trades_path = tp
        self.risk_gate = RiskGate({
            "max_positions": 3,
            "max_daily_trades": 20,
            "daily_loss_limit_usd": 75.0,
            "min_atr_ratio": 0.003,
        })
        self.executor = Executor(
            self.auth, self.state_mgr, self.notifier,
            {"margin_usd": 50.0, "leverage": 10})
        self.monitor = PositionMonitor(
            self.auth, self.state_mgr, self.notifier,
            {"daily_loss_limit_usd": 75.0,
             "daily_summary_utc_hour": 17})

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_full_entry(self, mock_get, mock_post):
        """Signal -> risk gate -> execute -> 1 position."""
        mock_get.side_effect = [
            _resp({"code": 0, "data": {"price": "0.005"}}),
            _resp({"code": 0, "data": [
                {"symbol": "RIVER-USDT",
                 "tradeMinQuantity": "1"}]}),
        ]
        mock_post.return_value = _resp(
            {"code": 0, "data": {"orderId": "99"}})
        sig = Signal(
            direction="LONG", grade="MOCK",
            entry_price=0.005, sl_price=0.004,
            tp_price=0.007, atr=0.0001, bar_ts=17e11)
        state_dict = self.state_mgr.get_state()
        ok, reason = self.risk_gate.evaluate(
            sig, "RIVER-USDT", state_dict, ["MOCK"])
        self.assertTrue(ok, msg="Approve: " + reason)
        result = self.executor.execute(sig, "RIVER-USDT")
        self.assertIsNotNone(result)
        s = self.state_mgr.get_state()
        self.assertEqual(len(s["open_positions"]), 1)
        self.assertIn("RIVER-USDT_LONG", s["open_positions"])
        self.notifier.send.assert_called()

    @patch("position_monitor.requests.get")
    @patch("executor.requests.post")
    @patch("executor.requests.get")
    def test_entry_then_close(self, mock_eg, mock_ep, mock_mg):
        """Entry then close -> 0 positions, csv exists."""
        mock_eg.side_effect = [
            _resp({"code": 0, "data": {"price": "0.005"}}),
            _resp({"code": 0, "data": [
                {"symbol": "RIVER-USDT",
                 "tradeMinQuantity": "1"}]}),
        ]
        mock_ep.return_value = _resp(
            {"code": 0, "data": {"orderId": "99"}})
        sig = Signal(
            direction="LONG", grade="MOCK",
            entry_price=0.005, sl_price=0.004,
            tp_price=0.007, atr=0.0001, bar_ts=17e11)
        self.executor.execute(sig, "RIVER-USDT")
        mock_mg.return_value = _resp(
            {"code": 0, "data": []})
        self.monitor.check()
        s = self.state_mgr.get_state()
        self.assertEqual(len(s["open_positions"]), 0,
                         msg="Should be 0 after close")
        self.assertTrue(self.trades_path.exists())

    def test_daily_reset(self):
        """reset_daily clears pnl, trades, halt."""
        self.state_mgr.state["daily_pnl"] = -80.0
        self.state_mgr.state["daily_trades"] = 15
        self.state_mgr.state["halt_flag"] = True
        self.state_mgr.reset_daily()
        s = self.state_mgr.get_state()
        self.assertEqual(s["daily_pnl"], 0.0)
        self.assertEqual(s["daily_trades"], 0)
        self.assertFalse(s["halt_flag"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''
    write_and_verify("tests/test_integration.py", content)


# ---------------------------------------------------------------------------
# 24. scripts/test_connection.py
# ---------------------------------------------------------------------------
def build_test_connection():
    """Generate live connection test script."""
    next_step("scripts/test_connection.py")
    content = '''\
"""
Connection test for BingX API (requires .env).
Does NOT place orders. Read-only + one Telegram message.
Run: python scripts/test_connection.py
"""
import os
import sys
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bingx_auth import BingXAuth
from notifier import Notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)
RESULTS = []


def test_step(name, func):
    """Run a test step and record result."""
    start = time.time()
    try:
        ok = func()
        ms = round((time.time() - start) * 1000)
        status = "PASS" if ok else "FAIL"
        RESULTS.append((status, name, ms))
        log.info("%s: %s (%dms)", status, name, ms)
    except Exception as e:
        ms = round((time.time() - start) * 1000)
        RESULTS.append(("ERROR", name, ms))
        log.error("ERROR: %s (%dms): %s", name, ms, e)


def main():
    """Run all connection tests."""
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    tg_chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not api_key or not secret_key:
        log.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY")
        sys.exit(1)
    auth = BingXAuth(api_key, secret_key, demo_mode=True)

    def t_auth():
        """Test auth signing."""
        req = auth.build_signed_request(
            "GET", "/test", {"symbol": "BTC-USDT"})
        return ("signature=" in req["url"]
                and "timestamp=" in req["url"])
    test_step("Auth signing", t_auth)

    def t_klines():
        """Fetch klines."""
        url = auth.build_public_url(
            "/openApi/swap/v3/quote/klines",
            {"symbol": "BTC-USDT", "interval": "5m",
             "limit": "5"})
        resp = requests.get(url, timeout=10)
        d = resp.json()
        return d.get("code", -1) == 0 and len(d.get("data", [])) > 0
    test_step("Fetch klines (v3)", t_klines)

    def t_price():
        """Fetch mark price."""
        url = auth.build_public_url(
            "/openApi/swap/v2/quote/price",
            {"symbol": "BTC-USDT"})
        resp = requests.get(url, timeout=10)
        return resp.json().get("code", -1) == 0
    test_step("Fetch mark price", t_price)

    def t_contracts():
        """Fetch contracts."""
        url = auth.build_public_url(
            "/openApi/swap/v2/quote/contracts")
        resp = requests.get(url, timeout=10)
        d = resp.json()
        if d.get("code", -1) != 0:
            return False
        for c in d.get("data", []):
            if c.get("symbol") == "BTC-USDT":
                log.info("  BTC-USDT step: %s",
                         c.get("tradeMinQuantity"))
                return True
        return False
    test_step("Fetch contracts", t_contracts)

    def t_positions():
        """Check positions (signed)."""
        req = auth.build_signed_request(
            "GET", "/openApi/swap/v2/user/positions")
        resp = requests.get(
            req["url"], headers=req["headers"], timeout=10)
        return resp.json().get("code", -1) == 0
    test_step("Check positions", t_positions)

    def t_telegram():
        """Send test Telegram message."""
        if not tg_token:
            log.warning("No TELEGRAM_BOT_TOKEN — skip")
            return True
        n = Notifier(tg_token, tg_chat)
        return n.send("BingX connector test — connection OK")
    test_step("Telegram send", t_telegram)

    log.info("=" * 50)
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    log.info("Results: %d/%d passed", passed, len(RESULTS))
    for status, name, ms in RESULTS:
        log.info("  %s  %s  (%dms)", status, name, ms)
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
'''
    write_and_verify("scripts/test_connection.py", content)


# ---------------------------------------------------------------------------
# 25. scripts/debug_connector.py
# ---------------------------------------------------------------------------
def build_debug_connector():
    """Generate debug/troubleshooting script."""
    next_step("scripts/debug_connector.py")
    content = '''\
"""
Debug script for BingX connector troubleshooting.
Run: python scripts/debug_connector.py --test-auth
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


def cmd_test_auth():
    """Test auth signing."""
    from bingx_auth import BingXAuth
    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", "demo_key"),
        os.getenv("BINGX_SECRET_KEY", "demo_secret"),
        demo_mode=True)
    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions",
        {"symbol": "BTC-USDT"})
    log.info("URL: %s", req["url"])
    log.info("Headers: %s", req["headers"])
    pub = auth.build_public_url(
        "/openApi/swap/v3/quote/klines",
        {"symbol": "BTC-USDT", "interval": "5m"})
    log.info("Public URL: %s", pub)


def cmd_test_klines(symbol):
    """Fetch klines for one symbol."""
    import requests
    from bingx_auth import BingXAuth
    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", "demo_key"),
        os.getenv("BINGX_SECRET_KEY", "demo_secret"),
        demo_mode=True)
    url = auth.build_public_url(
        "/openApi/swap/v3/quote/klines",
        {"symbol": symbol, "interval": "5m", "limit": "5"})
    log.info("GET %s", url)
    resp = requests.get(url, timeout=10)
    d = resp.json()
    log.info("Code: %s", d.get("code"))
    log.info("Count: %d", len(d.get("data", [])))
    for row in d.get("data", [])[:3]:
        log.info("  %s", json.dumps(row, indent=2)[:200])


def cmd_test_price(symbol):
    """Fetch mark price for one symbol."""
    import requests
    from bingx_auth import BingXAuth
    load_dotenv(ROOT / ".env")
    auth = BingXAuth(
        os.getenv("BINGX_API_KEY", "demo_key"),
        os.getenv("BINGX_SECRET_KEY", "demo_secret"),
        demo_mode=True)
    url = auth.build_public_url(
        "/openApi/swap/v2/quote/price", {"symbol": symbol})
    log.info("GET %s", url)
    resp = requests.get(url, timeout=10)
    log.info("Response: %s",
             json.dumps(resp.json(), indent=2)[:500])


def cmd_test_state():
    """Load and print state.json."""
    sp = ROOT / "state.json"
    if sp.exists():
        d = json.loads(sp.read_text(encoding="utf-8"))
        log.info("State:\\n%s", json.dumps(d, indent=2))
    else:
        log.info("No state.json found")


def cmd_test_signal():
    """Run mock strategy with synthetic data."""
    import pandas as pd
    import numpy as np
    from plugins.mock_strategy import MockStrategy
    rng = np.random.default_rng(42)
    n = 100
    close = 0.01 + np.cumsum(rng.normal(0, 0.0001, n))
    close = np.clip(close, 0.005, 0.02)
    df = pd.DataFrame({
        "open": close * rng.uniform(0.999, 1.001, n),
        "high": close * rng.uniform(1.000, 1.005, n),
        "low": close * rng.uniform(0.995, 1.000, n),
        "close": close,
        "volume": rng.integers(1e6, 1e7, n).astype(float),
        "time": range(17e11, 17e11 + n * 300000, 300000),
    })
    strat = MockStrategy({"signal_probability": 1.0})
    sig = strat.get_signal(df)
    if sig:
        log.info("Signal: %s grade=%s price=%.6f sl=%.6f",
                 sig.direction, sig.grade,
                 sig.entry_price, sig.sl_price)
    else:
        log.info("No signal")


def cmd_test_risk():
    """Run risk gate with synthetic state."""
    from risk_gate import RiskGate
    from plugins.mock_strategy import Signal
    gate = RiskGate({
        "max_positions": 3, "max_daily_trades": 20,
        "daily_loss_limit_usd": 75.0, "min_atr_ratio": 0.003})
    state = {"open_positions": {}, "daily_pnl": 0.0,
             "daily_trades": 0, "halt_flag": False}
    sig = Signal(
        direction="LONG", grade="MOCK", entry_price=0.01,
        sl_price=0.009, tp_price=0.013, atr=0.0001, bar_ts=0)
    ok, reason = gate.evaluate(sig, "TEST-USDT", state, ["MOCK"])
    log.info("Result: approved=%s reason=%s", ok, reason)


def cmd_test_telegram():
    """Send test Telegram message."""
    from notifier import Notifier
    load_dotenv(ROOT / ".env")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token:
        log.error("No TELEGRAM_BOT_TOKEN in .env")
        return
    n = Notifier(token, chat)
    result = n.send("Debug test from BingX connector")
    log.info("Result: %s", result)


def main():
    """Parse args and run debug command."""
    parser = argparse.ArgumentParser(
        description="BingX connector debugger")
    parser.add_argument("--test-auth", action="store_true")
    parser.add_argument("--test-klines", type=str, metavar="SYM")
    parser.add_argument("--test-price", type=str, metavar="SYM")
    parser.add_argument("--test-state", action="store_true")
    parser.add_argument("--test-signal", action="store_true")
    parser.add_argument("--test-risk", action="store_true")
    parser.add_argument("--test-telegram", action="store_true")
    args = parser.parse_args()
    if args.test_auth:
        cmd_test_auth()
    elif args.test_klines:
        cmd_test_klines(args.test_klines)
    elif args.test_price:
        cmd_test_price(args.test_price)
    elif args.test_state:
        cmd_test_state()
    elif args.test_signal:
        cmd_test_signal()
    elif args.test_risk:
        cmd_test_risk()
    elif args.test_telegram:
        cmd_test_telegram()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''
    write_and_verify("scripts/debug_connector.py", content)


# ---------------------------------------------------------------------------
# Import smoke test
# ---------------------------------------------------------------------------
def run_import_tests():
    """Try importing each module to catch circular/missing deps."""
    print()
    print("=== Import Smoke Test ===")
    print("  (requires: pip install -r requirements.txt)")
    IMPORT_ORDER = [
        "bingx_auth",
        "notifier",
        "state_manager",
        "plugins.mock_strategy",
        "data_fetcher",
        "risk_gate",
        "executor",
        "signal_engine",
        "position_monitor",
    ]
    sys.path.insert(0, str(ROOT))
    for mod in IMPORT_ORDER:
        try:
            importlib.import_module(mod)
            print("  [IMPORT OK] " + mod)
        except ImportError as e:
            msg = str(e)
            if any(pkg in msg for pkg in [
                    "yaml", "dotenv", "requests", "pandas",
                    "numpy"]):
                print("  [IMPORT SKIP] " + mod
                      + ": missing package (" + msg + ")")
            else:
                print("  [IMPORT FAIL] " + mod + ": " + msg)
                ERRORS.append("import:" + mod)
        except Exception as e:
            print("  [IMPORT FAIL] " + mod + ": " + str(e))
            ERRORS.append("import:" + mod)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Build all files and report."""
    ts = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC")
    print("=== BingX Connector Build ===")
    print("  " + ts)
    print()

    build_requirements()
    build_env_example()
    build_gitignore()
    build_config_yaml()
    build_bingx_auth()
    build_notifier()
    build_state_manager()
    build_plugins_init()
    build_mock_strategy()
    build_data_fetcher()
    build_risk_gate()
    build_executor()
    build_signal_engine()
    build_position_monitor()
    build_main()
    build_tests_init()
    build_test_auth()
    build_test_risk_gate()
    build_test_executor()
    build_test_plugin_contract()
    build_test_state_manager()
    build_test_data_fetcher()
    build_test_integration()
    build_test_connection()
    build_debug_connector()

    run_import_tests()

    print()
    print("=== BUILD SUMMARY ===")
    print("  Files created: " + str(len(CREATED)))
    print("  Errors: " + str(len(ERRORS)))
    if ERRORS:
        print("  FAILURES: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("  ALL PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
