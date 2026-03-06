"""
BingX server time synchronization.
Maintains offset between local clock and BingX server to prevent 109400 errors.
Thread-safe singleton -- one instance per process.
"""
import time
import threading
import logging
import requests

logger = logging.getLogger(__name__)

LIVE_SERVER_TIME_URL = "https://open-api.bingx.com/openApi/swap/v2/server/time"
DEMO_SERVER_TIME_URL = "https://open-api-vst.bingx.com/openApi/swap/v2/server/time"

_instance = None
_lock = threading.Lock()


class TimeSync:
    """Fetch BingX server time and maintain local-to-server offset."""

    def __init__(self, base_url=None, sync_interval=30):
        """Initialize with optional base URL and sync interval in seconds."""
        self._offset_ms = 0
        self._lock = threading.Lock()
        self._sync_interval = sync_interval
        self._last_sync = 0.0
        self._sync_count = 0
        self._server_time_url = self._resolve_url(base_url)
        self._timer = None
        self._running = False

    def _resolve_url(self, base_url):
        """Determine server time URL from base_url."""
        if base_url and "vst" in base_url:
            return DEMO_SERVER_TIME_URL
        return LIVE_SERVER_TIME_URL

    def sync(self):
        """Fetch server time and update offset. Returns True on success."""
        try:
            t_before = time.time()
            resp = requests.get(self._server_time_url, timeout=5)
            t_after = time.time()
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.warning("TimeSync API error: %s", data.get("msg"))
                return False
            server_time_ms = int(data["data"]["serverTime"])
            rtt = t_after - t_before
            local_time_ms = int(((t_before + t_after) / 2) * 1000)
            with self._lock:
                self._offset_ms = server_time_ms - local_time_ms
                self._last_sync = t_after
                self._sync_count += 1
            logger.info(
                "TimeSync: offset=%+dms rtt=%.0fms sync_count=%d",
                self._offset_ms, rtt * 1000, self._sync_count
            )
            return True
        except Exception as e:
            logger.error("TimeSync fetch failed: %s", e)
            return False

    def now_ms(self):
        """Return current timestamp in milliseconds, adjusted by server offset."""
        with self._lock:
            offset = self._offset_ms
        return int(time.time() * 1000) + offset

    def get_offset_ms(self):
        """Return current offset in milliseconds."""
        with self._lock:
            return self._offset_ms

    def start_periodic(self):
        """Start periodic background sync. Idempotent."""
        if self._running:
            return
        self._running = True
        self._schedule_next()

    def _schedule_next(self):
        """Schedule the next sync cycle."""
        if not self._running:
            return
        self._timer = threading.Timer(self._sync_interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self):
        """Periodic sync callback."""
        self.sync()
        self._schedule_next()

    def stop_periodic(self):
        """Stop periodic sync."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def force_resync(self):
        """Force immediate re-sync (call after 109400 error)."""
        logger.warning("TimeSync: forced re-sync triggered")
        return self.sync()


def get_time_sync(base_url=None, sync_interval=30):
    """Get or create the module-level TimeSync singleton."""
    global _instance
    with _lock:
        if _instance is None:
            _instance = TimeSync(base_url=base_url, sync_interval=sync_interval)
        return _instance


def synced_timestamp_ms():
    """Convenience: return server-adjusted timestamp. Falls back to local time if no sync."""
    global _instance
    if _instance is None:
        return int(time.time() * 1000)
    return _instance.now_ms()
