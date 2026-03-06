"""
WebSocket listener for BingX order fill events.
Daemon thread that connects to user data stream and pushes fill events to a queue.
"""
import gzip
import json
import time
import queue
import logging
import asyncio
import threading
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

LISTEN_KEY_PATH = "/openApi/user/auth/userDataStream"
WS_LIVE_URL = "wss://open-api-swap.bingx.com/swap-market"
WS_DEMO_URL = "wss://vst-open-api-ws.bingx.com/swap-market"
REFRESH_INTERVAL = 55 * 60  # 55 minutes
MAX_RECONNECT = 10
RECONNECT_DELAY = 5  # base; actual = RECONNECT_DELAY * 2**min(reconnect_count, 5)


class WSListener(threading.Thread):
    """Daemon thread that listens for BingX WebSocket order fill events."""

    def __init__(self, auth, fill_queue, ws_logger=None):
        """Initialize with auth, fill queue, and optional logger."""
        super().__init__(daemon=True, name="WSListener")
        self.auth = auth
        self.fill_queue = fill_queue
        self.log = ws_logger or logger
        self._stop_event = threading.Event()
        self._listen_key = None
        self._ws_base = WS_DEMO_URL if auth.demo_mode else WS_LIVE_URL

    def _obtain_listen_key(self):
        """POST to BingX to get a new listenKey. Returns str or None."""
        req = self.auth.build_signed_request("POST", LISTEN_KEY_PATH)
        try:
            resp = requests.post(
                req["url"], headers=req["headers"], timeout=10)
            data = resp.json()
            if data.get("code", 0) != 0:
                self.log.error("listenKey API error %s: %s",
                               data.get("code"), data.get("msg"))
                return None
            key = data.get("data", {}).get("listenKey", "")
            if not key and isinstance(data.get("data"), str):
                key = data["data"]
            if not key:
                key = data.get("listenKey", "")  # unwrapped response format
            if key:
                self.log.info("listenKey obtained: %s...%s", key[:8], key[-4:])
            else:
                self.log.error("listenKey empty — full response: %s", data)
            return key or None
        except Exception as e:
            self.log.error("listenKey fetch failed: %s", e)
            return None

    def _refresh_listen_key(self):
        """Extend listenKey validity by another 60 minutes."""
        req = self.auth.build_signed_request(
            "PUT", LISTEN_KEY_PATH,
            {"listenKey": self._listen_key})
        try:
            resp = requests.put(
                req["url"], headers=req["headers"], timeout=10)
            data = resp.json()
            if data.get("code", 0) == 0:
                self.log.info("listenKey refreshed")
            else:
                self.log.warning("listenKey refresh failed: %s", data.get("msg"))
        except Exception as e:
            self.log.warning("listenKey refresh error: %s", e)

    def _delete_listen_key(self):
        """Delete listenKey on shutdown."""
        if not self._listen_key:
            return
        req = self.auth.build_signed_request(
            "DELETE", LISTEN_KEY_PATH,
            {"listenKey": self._listen_key})
        try:
            resp = requests.delete(
                req["url"], headers=req["headers"], timeout=10)
            self.log.info("listenKey deleted")
        except Exception as e:
            self.log.warning("listenKey delete error: %s", e)

    def _parse_fill_event(self, msg_data):
        """Parse ORDER_TRADE_UPDATE message. Returns dict or None."""
        event_type = msg_data.get("e", "")
        if event_type != "ORDER_TRADE_UPDATE":
            return None
        order = msg_data.get("o", {})
        status = order.get("X", "")
        if status != "FILLED":
            return None
        symbol = order.get("s", "")
        avg_price = float(order.get("ap", 0) or 0)
        order_type = order.get("o", "")
        if "TAKE_PROFIT" in order_type:
            reason = "TP_HIT"
        elif "STOP" in order_type:
            reason = "SL_HIT"
        else:
            return None
        if avg_price <= 0 or not symbol:
            return None
        return {
            "symbol": symbol,
            "avg_price": avg_price,
            "reason": reason,
            "position_side": order.get("ps", ""),
            "realized_pnl": float(order.get("rp", 0) or 0),
            "fee": float(order.get("n", 0) or 0),
        }

    async def _ws_loop(self):
        """Main WebSocket event loop with reconnection logic."""
        try:
            import websockets
        except ImportError:
            self.log.error("websockets library not installed")
            return
        reconnect_count = 0
        while not self._stop_event.is_set() and reconnect_count < MAX_RECONNECT:
            self._listen_key = self._obtain_listen_key()
            if not self._listen_key:
                backoff = RECONNECT_DELAY * (2 ** min(reconnect_count, 5))
                self.log.error("Cannot obtain listenKey, retry in %ds (attempt %d/%d)",
                               backoff, reconnect_count + 1, MAX_RECONNECT)
                reconnect_count += 1
                await asyncio.sleep(backoff)
                continue
            ws_url = self._ws_base + "?listenKey=" + self._listen_key
            self.log.info("Connecting to WS: %s...%s",
                          ws_url[:50], ws_url[-20:])
            try:
                async with websockets.connect(ws_url, ping_interval=20,
                                              ping_timeout=10) as ws:
                    reconnect_count = 0
                    last_refresh = time.time()
                    self.log.info("WebSocket connected")
                    while not self._stop_event.is_set():
                        try:
                            msg = await asyncio.wait_for(
                                ws.recv(), timeout=5.0)
                        except asyncio.TimeoutError:
                            if time.time() - last_refresh > REFRESH_INTERVAL:
                                self._refresh_listen_key()
                                last_refresh = time.time()
                            continue
                        try:
                            if isinstance(msg, bytes):
                                msg = gzip.decompress(msg).decode("utf-8")
                            if msg == "Ping":
                                await ws.send("Pong")
                                continue
                            data = json.loads(msg)
                        except (json.JSONDecodeError, OSError):
                            self.log.warning("WS non-JSON message: %s", str(msg)[:100])
                            continue
                        event = self._parse_fill_event(data)
                        if event:
                            self.log.info(
                                "WS FILL: %s %s price=%.6f reason=%s",
                                event["symbol"], event["position_side"],
                                event["avg_price"], event["reason"])
                            self.fill_queue.put(event)
                        if time.time() - last_refresh > REFRESH_INTERVAL:
                            self._refresh_listen_key()
                            last_refresh = time.time()
            except Exception as e:
                self.log.error("WebSocket error: %s", e)
                reconnect_count += 1
                if reconnect_count < MAX_RECONNECT:
                    backoff = RECONNECT_DELAY * (2 ** min(reconnect_count, 5))
                    self.log.info("Reconnecting in %ds (attempt %d/%d)",
                                  backoff, reconnect_count, MAX_RECONNECT)
                    await asyncio.sleep(backoff)
        if reconnect_count >= MAX_RECONNECT:
            self.log.critical("WS LISTENER DEAD after %d reconnect attempts", MAX_RECONNECT)
            import datetime as _dt
            _ts = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            _flag_dir = Path("logs")
            _flag_dir.mkdir(exist_ok=True)
            _flag = _flag_dir / ("ws_dead_" + _ts + ".flag")
            _flag.write_text(
                "WS listener died at " + _ts + " after " + str(MAX_RECONNECT) + " reconnect attempts",
                encoding="utf-8",
            )
            self.log.critical("Dead flag written: %s", _flag)

    def run(self):
        """Run asyncio event loop in this thread."""
        self.log.info("WSListener thread started")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._ws_loop())
        except Exception as e:
            self.log.error("WSListener loop error: %s", e)
        finally:
            self._delete_listen_key()
            loop.close()
            self.log.info("WSListener thread stopped")

    def stop(self):
        """Signal the listener to stop."""
        self.log.info("WSListener stop requested")
        self._stop_event.set()
