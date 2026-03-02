"""
BingX live signal screener -- headless loop.
Fetches klines for all configured coins via public BingX API,
runs FourPillarsV384 signal detection, sends Telegram alert on fresh A/B signals.
Run: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/bingx-connector/screener/bingx_screener.py"
"""
import sys
import os
import logging
import time
import datetime
import random
import traceback
from pathlib import Path
from typing import Optional

import requests
import pandas as pd
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# sys.path setup — mirrors four_pillars_v384.py lines 14-20 exactly
# screener/ -> bingx-connector/ -> vault root -> four-pillars-backtester
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent.parent          # bingx-connector/
_BACKTESTER = _ROOT.parent / "four-pillars-backtester"  # four-pillars-backtester/

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_BACKTESTER) not in sys.path:
    sys.path.insert(0, str(_BACKTESTER))

from plugins.four_pillars_v384 import FourPillarsV384  # noqa: E402
from notifier import Notifier                           # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
KLINES_PATH = "/openApi/swap/v3/quote/klines"
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def setup_logging(log_dir: Path) -> logging.Logger:
    """Create dated log file + stream handler; return named logger."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / (str(datetime.date.today()) + "-screener.log")

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)

    logger = logging.getLogger("bingx_screener")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def load_config(config_path: Path) -> dict:
    """Read config.yaml with yaml.safe_load; return full config dict."""
    with open(config_path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    coins = cfg.get("coins", [])
    logging.getLogger("bingx_screener").info(
        "Config loaded: %d coins from %s", len(coins), str(config_path)
    )
    return cfg


def fetch_klines(
    session: requests.Session,
    base_url: str,
    symbol: str,
    timeframe: str = "5m",
    limit: int = 201,
) -> Optional[pd.DataFrame]:
    """Fetch klines from BingX v3 with 3 retries and exponential backoff."""
    params = {
        "symbol": symbol,
        "interval": timeframe,
        "limit": str(limit),
    }
    query_parts = []
    for k, v in sorted(params.items()):
        query_parts.append(k + "=" + v)
    url = base_url + KLINES_PATH + "?" + "&".join(query_parts)

    logger = logging.getLogger("bingx_screener")
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error(
                    "Klines API error %s: %s",
                    data.get("code"), data.get("msg")
                )
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
                    if lc in ("open", "high", "low", "close", "volume", "time"):
                        col_map[col] = lc
                df = df.rename(columns=col_map)
            elif isinstance(raw[0], list):
                ncols = len(raw[0])
                base_cols = ["time", "open", "close", "high", "low", "volume"]
                extra = ["extra_" + str(i) for i in range(max(0, ncols - 6))]
                df = pd.DataFrame(raw, columns=base_cols + extra)
            else:
                logger.error("Unknown kline format for %s", symbol)
                return None

            for col in ("open", "high", "low", "close", "volume"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            if "time" in df.columns:
                df["time"] = pd.to_numeric(
                    df["time"], errors="coerce"
                ).astype("int64")
                df = df.sort_values("time").reset_index(drop=True)
            if len(df) > limit:
                df = df.tail(limit).reset_index(drop=True)
            return df

        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                delay = (2 ** attempt) + random.uniform(0, 0.5)
                logger.warning(
                    "Klines %s attempt %d/%d failed (%s), retry in %.1fs",
                    symbol, attempt + 1, MAX_RETRIES,
                    type(exc).__name__, delay,
                )
                time.sleep(delay)
                continue
        except requests.exceptions.HTTPError as exc:
            logger.error(
                "Klines HTTP %s: %s", exc.response.status_code, symbol
            )
            return None
        except (ValueError, KeyError) as exc:
            logger.error("Klines parse error %s: %s", symbol, exc)
            return None

    logger.error(
        "Klines failed after %d retries: %s (%s)",
        MAX_RETRIES, symbol, last_error
    )
    return None


def rename_for_plugin(df: pd.DataFrame) -> pd.DataFrame:
    """Rename time->timestamp and volume->base_vol; add quote_vol=0.0 if absent."""
    df = df.rename(columns={"time": "timestamp", "volume": "base_vol"})
    if "quote_vol" not in df.columns:
        df["quote_vol"] = 0.0
    return df


def send_alert(
    notifier: Notifier,
    symbol: str,
    sig,
    atr_ratio: float,
) -> None:
    """Format and send a Telegram HTML signal alert via notifier."""
    lines = []
    lines.append("<b>BINGX SIGNAL</b>")
    lines.append("<b>Symbol:</b> " + symbol)
    lines.append(
        "<b>Grade:</b> " + str(sig.grade)
        + " | <b>Direction:</b> " + str(sig.direction)
    )
    lines.append("<b>ATR ratio:</b> " + "{:.4f}".format(atr_ratio))
    entry_sl = (
        "<b>Entry:</b> " + "{:.6f}".format(sig.entry_price)
        + " | <b>SL:</b> " + "{:.6f}".format(sig.sl_price)
    )
    if sig.tp_price is not None:
        entry_sl = entry_sl + " | <b>TP:</b> " + "{:.6f}".format(sig.tp_price)
    lines.append(entry_sl)
    message = "\n".join(lines)
    notifier.send(message)


def run_screener_loop(
    symbols: list,
    plugin: FourPillarsV384,
    notifier: Notifier,
    session: requests.Session,
    base_url: str,
    timeframe: str,
    loop_interval: int,
    logger: logging.Logger,
) -> None:
    """Infinite screener loop: fetch, detect signals, alert, deduplicate."""
    last_alerted: dict = {}

    while True:
        cycle_signals = 0
        for symbol in symbols:
            try:
                df = fetch_klines(session, base_url, symbol, timeframe, 201)
                if df is None:
                    continue

                df = rename_for_plugin(df)

                sig = plugin.get_signal(df)
                if sig is None:
                    logger.debug("No signal: %s", symbol)
                    continue

                atr_ratio = (
                    sig.atr / sig.entry_price if sig.entry_price > 0 else 0.0
                )

                if last_alerted.get(symbol) != sig.bar_ts:
                    last_alerted[symbol] = sig.bar_ts
                    send_alert(notifier, symbol, sig, atr_ratio)
                    logger.info(
                        "ALERT sent: %s grade=%s dir=%s",
                        symbol, sig.grade, sig.direction,
                    )
                    cycle_signals += 1
                else:
                    logger.debug(
                        "Dedup skip: %s bar_ts=%d", symbol, sig.bar_ts
                    )

            except Exception as exc:
                logger.error(
                    "Screener error on %s: %s", symbol, exc
                )
                logger.debug(traceback.format_exc())
                continue

        logger.info(
            "Cycle complete: %d coins scanned, %d signals",
            len(symbols), cycle_signals,
        )
        time.sleep(loop_interval)


def main() -> None:
    """Entry point: load config, init plugin and notifier, start loop."""
    load_dotenv(_ROOT / ".env")

    logger = setup_logging(_ROOT / "logs")
    config = load_config(_ROOT / "config.yaml")

    symbols = config.get("coins", [])
    strategy_cfg = config.get("strategy", {})

    # Always use live BingX API for public klines -- never from config
    base_url = "https://open-api.bingx.com"
    timeframe = strategy_cfg.get("timeframe", "5m")
    loop_interval = 60

    bot_token = os.getenv("BINGX_TELEGRAM_TOKEN", "")
    chat_id = os.getenv("BINGX_TELEGRAM_CHAT_ID", "")
    notifier = Notifier(bot_token, chat_id, enabled=bool(bot_token and chat_id))

    # FourPillarsV384 expects the full config (reads "four_pillars" sub-block)
    plugin = FourPillarsV384(config)

    session = requests.Session()

    logger.info(
        "Screener started: %d coins, tf=%s, interval=%ds",
        len(symbols), timeframe, loop_interval,
    )

    run_screener_loop(
        symbols, plugin, notifier, session,
        base_url, timeframe, loop_interval, logger,
    )


if __name__ == "__main__":
    main()
