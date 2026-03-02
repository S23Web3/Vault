"""
PnL reconciliation: compare bot trades.csv against BingX positionHistory.
Queries past 24h of closed positions from BingX, compares netProfit to recorded pnl_net.
Logs discrepancies to logs/YYYY-MM-DD-reconcile.log.

Run: python scripts/reconcile_pnl.py
"""
import os
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta, date

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bingx_auth import BingXAuth

POSITION_HISTORY_PATH = "/openApi/swap/v1/trade/positionHistory"


def setup_logging():
    """Configure dual logging: file + console."""
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    today = date.today().strftime("%Y-%m-%d")
    log_file = log_dir / (today + "-reconcile.log")
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(fmt)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logging.basicConfig(level=logging.INFO,
                        handlers=[file_handler, console_handler])
    return logging.getLogger(__name__)


def load_bot_trades(trades_path, since_utc):
    """Load trades from CSV that occurred after since_utc. Returns list of dicts."""
    trades = []
    if not trades_path.exists():
        return trades
    with open(trades_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp", "")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            if ts >= since_utc:
                trades.append(row)
    return trades


def fetch_position_history(auth, since_ms):
    """Fetch closed positions from BingX for the last 24h. Returns list."""
    params = {
        "startTime": str(since_ms),
        "endTime": str(int(datetime.now(timezone.utc).timestamp() * 1000)),
        "pageSize": "100",
        "pageId": "1",
    }
    req = auth.build_signed_request("GET", POSITION_HISTORY_PATH, params)
    try:
        resp = requests.get(req["url"], headers=req["headers"], timeout=15)
        data = resp.json()
        if data.get("code", 0) != 0:
            logging.error("positionHistory API error %s: %s",
                          data.get("code"), data.get("msg"))
            return []
        positions = data.get("data", [])
        if isinstance(positions, dict):
            positions = positions.get("data", [])
        return positions if isinstance(positions, list) else []
    except Exception as e:
        logging.error("positionHistory fetch failed: %s", e)
        return []


def reconcile(bot_trades, bingx_positions, log):
    """Compare bot trades against BingX positions. Log discrepancies."""
    log.info("Bot trades (24h): %d", len(bot_trades))
    log.info("BingX positions (24h): %d", len(bingx_positions))
    bingx_by_symbol = {}
    for pos in bingx_positions:
        symbol = pos.get("symbol", "")
        if symbol not in bingx_by_symbol:
            bingx_by_symbol[symbol] = []
        bingx_by_symbol[symbol].append(pos)
    discrepancies = 0
    matched = 0
    for trade in bot_trades:
        symbol = trade.get("symbol", "")
        bot_pnl = float(trade.get("pnl_net", 0))
        direction = trade.get("direction", "")
        bingx_list = bingx_by_symbol.get(symbol, [])
        if not bingx_list:
            log.warning("UNMATCHED (no BingX record): %s %s pnl=%.4f",
                        symbol, direction, bot_pnl)
            discrepancies += 1
            continue
        best_match = bingx_list[0]
        bingx_pnl = float(best_match.get("netProfit", 0))
        bingx_comm = float(best_match.get("positionCommission", 0))
        diff = abs(bot_pnl - bingx_pnl)
        if diff > 0.50:
            log.warning(
                "DISCREPANCY: %s %s bot=%.4f bingx=%.4f diff=%.4f comm=%.4f",
                symbol, direction, bot_pnl, bingx_pnl, diff, bingx_comm)
            discrepancies += 1
        else:
            log.info("MATCH: %s %s bot=%.4f bingx=%.4f diff=%.4f",
                     symbol, direction, bot_pnl, bingx_pnl, diff)
            matched += 1
        if bingx_list:
            bingx_list.pop(0)
    log.info("=== Summary: matched=%d discrepancies=%d unmatched_bingx=%d ===",
             matched, discrepancies,
             sum(len(v) for v in bingx_by_symbol.values()))


def main():
    """Entry point for PnL reconciliation."""
    log = setup_logging()
    log.info("=== PnL Reconciliation ===")
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("BINGX_API_KEY", "")
    secret_key = os.getenv("BINGX_SECRET_KEY", "")
    if not api_key or not secret_key:
        log.error("Missing BINGX_API_KEY or BINGX_SECRET_KEY in .env")
        sys.exit(1)
    demo_mode = True
    auth = BingXAuth(api_key, secret_key, demo_mode=demo_mode)
    since_utc = datetime.now(timezone.utc) - timedelta(hours=24)
    since_ms = int(since_utc.timestamp() * 1000)
    trades_path = ROOT / "trades.csv"
    bot_trades = load_bot_trades(trades_path, since_utc)
    bingx_positions = fetch_position_history(auth, since_ms)
    reconcile(bot_trades, bingx_positions, log)
    log.info("=== Done ===")


if __name__ == "__main__":
    main()
