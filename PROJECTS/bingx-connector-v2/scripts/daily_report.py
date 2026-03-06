"""
Daily P&L report for BingX connector.
Reads trades.csv, computes today's stats, sends Telegram summary.
Run: python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\scripts\\daily_report.py"
Schedule: schtasks /create /tn "BingXDailyReport" /tr "python \\"C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\scripts\\daily_report.py\\"" /sc daily /st 21:00 /f
"""

import datetime
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent  # scripts/ -> bingx-connector/
sys.path.insert(0, str(_ROOT))
from notifier import Notifier


def setup_logging(log_dir: Path) -> logging.Logger:
    """Create log_dir if missing, wire file+stream handlers, return named logger."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / (str(datetime.date.today()) + "-daily-report.log")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(fmt)

    logger = logging.getLogger("daily_report")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def load_trades(trades_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load trades.csv from trades_path, parse timestamps, return DataFrame."""
    if not trades_path.exists():
        logger.warning("trades.csv not found at %s", trades_path)
        return pd.DataFrame()

    df = pd.read_csv(trades_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    before = len(df)
    df = df.dropna(subset=["timestamp"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with unparseable timestamps", dropped)
    return df


def filter_today(df: pd.DataFrame) -> pd.DataFrame:
    """Return only rows where timestamp date equals today (UTC)."""
    if df.empty:
        return df
    today = datetime.datetime.now(datetime.timezone.utc).date()
    return df[df["timestamp"].dt.date == today].copy()


def compute_stats(df: pd.DataFrame) -> dict:
    """Compute trade count, P&L, win rate, best and worst trade from df."""
    if df.empty:
        return {"empty": True}

    n_trades = len(df)
    total_pnl = float(df["pnl_net"].sum())
    n_wins = int((df["pnl_net"] > 0).sum())
    n_losses = int((df["pnl_net"] <= 0).sum())
    win_rate = (n_wins / n_trades * 100) if n_trades > 0 else 0.0

    best_idx = df["pnl_net"].idxmax()
    worst_idx = df["pnl_net"].idxmin()

    best = {
        "symbol": df.loc[best_idx, "symbol"],
        "direction": df.loc[best_idx, "direction"],
        "pnl": float(df.loc[best_idx, "pnl_net"]),
    }
    worst = {
        "symbol": df.loc[worst_idx, "symbol"],
        "direction": df.loc[worst_idx, "direction"],
        "pnl": float(df.loc[worst_idx, "pnl_net"]),
    }

    return {
        "empty": False,
        "n_trades": n_trades,
        "total_pnl": total_pnl,
        "n_wins": n_wins,
        "n_losses": n_losses,
        "win_rate": win_rate,
        "best": best,
        "worst": worst,
    }


def format_message(stats: dict, report_date: datetime.date) -> str:
    """Build an HTML Telegram message from computed stats and the report date."""
    utc4_now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=4)
    time_str = utc4_now.strftime("%H:%M")
    date_str = str(report_date)

    if stats.get("empty"):
        return (
            "[" + time_str + " UTC+4] "
            + "<b>DAILY REPORT -- " + date_str + "</b>\n"
            + "No closed trades today."
        )

    total_pnl = stats["total_pnl"]
    pnl_sign = "+" if total_pnl >= 0 else ""
    pnl_str = pnl_sign + "$" + "{:.2f}".format(total_pnl)

    win_rate_str = "{:.0f}".format(stats["win_rate"]) + "%"

    best = stats["best"]
    best_sign = "+" if best["pnl"] >= 0 else ""
    best_str = (
        best["symbol"].replace("-USDT", "")
        + " " + best["direction"]
        + " " + best_sign + "$" + "{:.2f}".format(best["pnl"])
    )

    worst = stats["worst"]
    worst_sign = "+" if worst["pnl"] >= 0 else ""
    worst_str = (
        worst["symbol"].replace("-USDT", "")
        + " " + worst["direction"]
        + " " + worst_sign + "$" + "{:.2f}".format(worst["pnl"])
    )

    header = "[" + time_str + " UTC+4] <b>DAILY REPORT -- " + date_str + "</b>"
    line_trades = "<b>Trades:</b> " + str(stats["n_trades"]) + " | <b>Win rate:</b> " + win_rate_str
    line_pnl = "<b>P&L:</b> " + pnl_str
    line_best = "<b>Best:</b> " + best_str
    line_worst = "<b>Worst:</b> " + worst_str

    return "\n".join([header, line_trades, line_pnl, line_best, line_worst])


def main() -> None:
    """Entry point: load env, read trades, compute stats, send Telegram report."""
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")

    logger = setup_logging(root / "logs")

    trades_path = root / "trades.csv"
    bot_token = os.getenv("BINGX_TELEGRAM_TOKEN", "")
    chat_id = os.getenv("BINGX_TELEGRAM_CHAT_ID", "")
    notifier = Notifier(bot_token, chat_id, enabled=bool(bot_token and chat_id))

    df = load_trades(trades_path, logger)
    today_df = filter_today(df)
    logger.info("Today trades: %d", len(today_df))

    stats = compute_stats(today_df)
    today = datetime.datetime.now(datetime.timezone.utc).date()
    message = format_message(stats, today)

    logger.info("Sending report: %d trades", stats.get("n_trades", 0))
    notifier.send(message)
    logger.info("Report sent")


if __name__ == "__main__":
    main()
