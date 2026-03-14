"""
Market data feed: polls BingX klines, detects new bars, fires callbacks.
Uses v3 endpoint for public market data (BUG-C07 fix: no auth).
"""
import logging
import time
import random
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
        self._session = requests.Session()  # reuse TCP connections
        self._consecutive_fails = 0
        self._max_retries = 3
        self._fail_alert_threshold = 10
        # W08: Track consecutive low-bar fetches per symbol
        self._low_bar_count = {}
        logger.info("MarketDataFeed: %d symbols, tf=%s, buffer=%d",
                     len(symbols), timeframe, buffer_bars)

    def _fetch_klines(self, symbol):
        """Fetch klines from BingX v3 with retry + exponential backoff."""
        params = {
            "symbol": symbol,
            "interval": self.timeframe,
            "limit": str(self.buffer_bars),
        }
        query_parts = []
        for k, v in sorted(params.items()):
            query_parts.append(k + "=" + v)
        url = self.base_url + KLINES_PATH + "?" + "&".join(query_parts)
        last_error = None
        for attempt in range(self._max_retries):
            try:
                resp = self._session.get(url, timeout=10)
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
                        df[col] = pd.to_numeric(
                            df[col], errors="coerce")
                if "time" in df.columns:
                    df["time"] = pd.to_numeric(
                        df["time"], errors="coerce").astype("int64")
                    df = df.sort_values("time").reset_index(drop=True)
                if len(df) > self.buffer_bars:
                    df = df.tail(
                        self.buffer_bars).reset_index(drop=True)
                self._consecutive_fails = 0
                # W08: Track low-bar fetches
                if len(df) < 2:
                    count = self._low_bar_count.get(symbol, 0) + 1
                    self._low_bar_count[symbol] = count
                    if count >= 3:
                        logger.warning(
                            "Low bar count for %s: %d consecutive fetches with < 2 bars",
                            symbol, count)
                else:
                    self._low_bar_count[symbol] = 0
                return df
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        "Klines %s attempt %d/%d failed (%s),"
                        " retry in %.1fs",
                        symbol, attempt + 1, self._max_retries,
                        type(e).__name__, delay)
                    time.sleep(delay)
                    continue
            except requests.exceptions.HTTPError as e:
                logger.error("Klines HTTP %s: %s",
                             e.response.status_code, symbol)
                return None
            except (ValueError, KeyError) as e:
                logger.error("Klines parse error %s: %s", symbol, e)
                return None
        self._consecutive_fails += 1
        if self._consecutive_fails >= self._fail_alert_threshold:
            logger.critical(
                "ALERT: %d consecutive kline fetch failures"
                " -- possible API outage", self._consecutive_fails)
        logger.error("Klines failed after %d retries: %s (%s)",
                     self._max_retries, symbol, last_error)
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

    def warmup(self, progress_callback=None):
        """Initial fetch for all symbols at startup. W13: throttled with 0.1s sleep."""
        total = len(self.symbols)
        for i, symbol in enumerate(self.symbols):
            df = self._fetch_klines(symbol)
            if df is not None:
                self.buffers[symbol] = df
                if len(df) >= 2:
                    self.last_bar_ts[symbol] = int(df.iloc[-2]["time"])
                logger.info("Warmup %s: %d bars", symbol, len(df))
            else:
                logger.warning("Warmup failed for %s", symbol)
            if progress_callback and (i + 1) % 5 == 0:
                progress_callback(i + 1, total)
            # W13: Throttle warmup to avoid rate limits
            time.sleep(0.1)

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
