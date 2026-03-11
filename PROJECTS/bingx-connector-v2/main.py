"""
BingX Connector main entry point.
Two daemon threads: market polling + position monitoring.
Run: python main.py
"""
import os
import sys
import time
import yaml
import logging
import queue
import threading
import signal as signal_mod
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta, date
from dotenv import load_dotenv

from bingx_auth import BingXAuth
from notifier import Notifier
from state_manager import StateManager
from data_fetcher import MarketDataFeed
from risk_gate import RiskGate
from executor import Executor
from signal_engine import StrategyAdapter
from position_monitor import PositionMonitor
from ws_listener import WSListener
from time_sync import get_time_sync

logger = logging.getLogger(__name__)

LEVERAGE_PATH = "/openApi/swap/v2/trade/leverage"
MARGIN_TYPE_PATH = "/openApi/swap/v2/trade/marginType"
COMMISSION_RATE_PATH = "/openApi/swap/v2/user/commissionRate"


def setup_logging():
    """Configure dual logging: file + console with UTC+4 timestamps."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    today = date.today().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}-bot.log"

    utc4 = timezone(timedelta(hours=4))

    class UTC4Formatter(logging.Formatter):
        """Formatter that outputs timestamps in UTC+4."""
        converter = None
        def formatTime(self, record, datefmt=None):
            """Format log record timestamp as UTC+4."""
            dt = datetime.fromtimestamp(record.created, tz=utc4)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    fmt = UTC4Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)

    logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
    # Keep urllib3 quiet (was flooding DEBUG with every HTTP connection)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_config():
    """Load config.yaml from the script directory."""
    config_path = Path(__file__).resolve().parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_leverage_and_margin(auth, symbols, leverage, margin_mode):
    """Set leverage and margin mode for each symbol at startup."""
    for symbol in symbols:
        for side in ("LONG", "SHORT"):
            req = auth.build_signed_request("POST", LEVERAGE_PATH, {
                "symbol": symbol,
                "side": side,
                "leverage": str(leverage),
            })
            try:
                resp = requests.post(
                    req["url"], headers=req["headers"], timeout=10)
                data = resp.json()
                if data.get("code", 0) == 0:
                    logger.info("Leverage: %s %s -> %dx", symbol, side, leverage)
                else:
                    logger.warning("Leverage fail %s %s: %s",
                                   symbol, side, data.get("msg"))
            except Exception as e:
                logger.error("Leverage error %s %s: %s", symbol, side, e)
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
        time.sleep(0.2)  # throttle: 200ms between coins to avoid rate limits


def fetch_commission_rate(auth):
    """Fetch taker commission rate from BingX. Returns float or default 0.0016."""
    req = auth.build_signed_request("GET", COMMISSION_RATE_PATH)
    try:
        resp = requests.get(req["url"], headers=req["headers"], timeout=10)
        data = resp.json()
        if data.get("code", 0) == 0:
            rate = float(data["data"]["commission"]["takerCommissionRate"])
            logger.info("Commission rate from API: %.6f (%.4f%%)", rate, rate * 100)
            return rate * 2  # round-trip (open + close)
        logger.warning("Commission rate API error %s — using default", data.get("code"))
    except Exception as e:
        logger.warning("Commission rate fetch failed: %s — using default", e)
    return 0.0016  # fallback: 0.08% taker x 2 sides (BingX standard rate)


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
            monitor.check_breakeven()
            monitor.check_ttp_closes()
            monitor.check_ttp_sl_tighten()
            monitor.check_daily_reset()
            monitor.check_hourly_metrics()
        except Exception as e:
            logger.error("Monitor loop error: %s", e, exc_info=True)
        shutdown_event.wait(check_interval)
    logger.info("Monitor loop stopped")



# ---------------------------------------------------------------------------
# Bot status file writer (Patch 7)
# ---------------------------------------------------------------------------
BOT_ROOT = Path(__file__).resolve().parent
STATUS_PATH = BOT_ROOT / "bot-status.json"


def write_bot_status(msg):
    """Append a timestamped message to bot-status.json. Atomic write."""
    import json as _json
    now = datetime.now(timezone.utc).isoformat()
    data = {"bot_start": now, "messages": []}
    if STATUS_PATH.exists():
        try:
            data = _json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except (_json.JSONDecodeError, OSError):
            pass
    if "messages" not in data:
        data["messages"] = []
    data["messages"].append({"ts": now, "msg": msg})
    tmp = STATUS_PATH.with_suffix(".tmp")
    tmp.write_text(_json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, STATUS_PATH)


def main():
    """Load config, init components, run loops."""
    setup_logging()
    logger.info("=== BingX Connector Starting ===")
    # Clear status file from previous run
    import json as _json_init
    STATUS_PATH.write_text(
        _json_init.dumps({"bot_start": datetime.now(timezone.utc).isoformat(),
                          "messages": []}, indent=2),
        encoding="utf-8")
    utc4 = timezone(timedelta(hours=4))
    ts = datetime.now(utc4).strftime("%Y-%m-%d %H:%M:%S UTC+4")
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
    write_bot_status("Config loaded: " + str(len(symbols)) + " coins, " + timeframe)
    auth = BingXAuth(api_key, secret_key, demo_mode=demo_mode)
    # --- Time sync (prevents 109400 "timestamp is invalid") ---
    _ts = get_time_sync(base_url=auth.base_url, sync_interval=30)
    _ts_ok = _ts.sync()
    if not _ts_ok:
        logger.warning("Initial time sync FAILED -- using local clock")
    else:
        logger.info("Time sync OK: offset=%+dms", _ts.get_offset_ms())
    _ts.start_periodic()
    write_bot_status("Time sync: offset=" + str(_ts.get_offset_ms()) + "ms")
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
        plugin_config=config,
        ttp_config=pos_cfg,
    )
    write_bot_status("Strategy loaded: " + strat_cfg.get("plugin", "mock_strategy"))
    logger.info("Setting leverage and margin mode...")
    set_leverage_and_margin(
        auth, symbols,
        pos_cfg.get("leverage", 10),
        pos_cfg.get("margin_mode", "ISOLATED"))
    commission_rate = fetch_commission_rate(auth)
    write_bot_status("Connected to BingX API")
    fill_queue = queue.Queue()
    ws_thread = WSListener(auth=auth, fill_queue=fill_queue, ws_logger=logger)
    monitor_cfg = dict(config)  # full config — PositionMonitor needs position.be_auto etc.
    # Hoist flat keys that PositionMonitor.__init__ reads directly from config
    monitor_cfg["daily_loss_limit_usd"] = risk_cfg.get("daily_loss_limit_usd", 75.0)
    monitor_cfg["daily_summary_utc_hour"] = notif_cfg.get("daily_summary_utc_hour", 17)
    monitor = PositionMonitor(
        auth, state_mgr, notifier, monitor_cfg,
        commission_rate=commission_rate,
        fill_queue=fill_queue)
    logger.info("Reconciling state with exchange...")
    req = auth.build_signed_request(
        "GET", "/openApi/swap/v2/user/positions")
    try:
        resp = requests.get(
            req["url"], headers=req["headers"], timeout=10)
        data = resp.json()
        if data.get("code", 0) != 0:
            logger.error("Reconcile API error %s: %s — using local state",
                         data.get("code"), data.get("msg"))
        else:
            live_pos = data.get("data", [])
            state_mgr.reconcile(live_pos)
    except Exception as e:
        logger.error("Reconcile failed: %s — using local state", e)
    write_bot_status("Positions reconciled")
    logger.info("Warming up market data...")
    write_bot_status("Warming up " + str(len(symbols)) + " symbols...")
    feed.warmup(
        progress_callback=lambda i, n: write_bot_status(
            "Warmup " + str(i) + "/" + str(n)))
    write_bot_status("Warmup complete (" + str(len(symbols)) + " symbols)")
    open_count = len(state_mgr.get_open_positions())
    start_msg = ("<b>BOT STARTED</b>"
                 + "\nCoins: " + str(len(symbols))
                 + "\nOpen: " + str(open_count)
                 + "\nMode: " + ("DEMO" if demo_mode else "LIVE"))
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
    ws_thread.start()
    logger.info("Threads started: MarketLoop + MonitorLoop + WSListener")
    write_bot_status("Bot running")
    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(1.0)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt — shutting down")
        shutdown_event.set()
    _ts.stop_periodic()
    ws_thread.stop()
    notifier.send("<b>BOT STOPPING</b>\nWaiting for in-flight ops...")
    logger.info("Waiting for threads to finish (max 15s)...")
    t1.join(timeout=15)
    t2.join(timeout=15)
    if t1.is_alive() or t2.is_alive():
        logger.warning("Threads did not stop cleanly within 15s")
    notifier.send("<b>BOT STOPPED</b>")
    logger.info("=== BingX Connector Stopped ===")
    logger.info("Bot process exiting.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
