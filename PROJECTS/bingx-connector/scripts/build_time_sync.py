"""
Build script: BingX server time synchronization (fixes error 109400).

Creates time_sync.py and patches bingx_auth.py + main.py + dashboard + executor + position_monitor
to use server-synced timestamps instead of raw time.time().

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts\\build_time_sync.py
"""
import os
import sys
import shutil
import py_compile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
CREATED = []
BACKED_UP = []
MODIFIED = []


def backup(filepath):
    """Create timestamped backup of a file."""
    p = Path(filepath)
    if not p.exists():
        print(f"  SKIP backup (not found): {p}")
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(f".{ts}.bak.py")
    shutil.copy2(p, bak)
    BACKED_UP.append(str(bak))
    print(f"  BACKUP: {bak}")


def write_file(filepath, content, label=""):
    """Write file, py_compile, track result."""
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  WROTE: {p}")
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"  py_compile OK: {p.name}")
    except py_compile.PyCompileError as e:
        ERRORS.append(f"{label or p.name}: {e}")
        print(f"  py_compile FAILED: {p.name} -- {e}")
    return p


def build_time_sync():
    """Create time_sync.py -- server time synchronization module."""
    target = ROOT / "time_sync.py"
    if target.exists():
        ERRORS.append("time_sync.py already exists -- not overwriting")
        print(f"  ERROR: {target} exists, skipping")
        return
    content = '''\
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
'''
    write_file(target, content, "time_sync.py")
    CREATED.append(str(target))


def patch_bingx_auth():
    """Patch bingx_auth.py to use synced timestamps."""
    target = ROOT / "bingx_auth.py"
    backup(target)
    content = '''\
"""
BingX authentication and request signing.
HMAC-SHA256 with alphabetical param sorting.
"""
import hashlib
import hmac
import logging
from urllib.parse import urlencode
from time_sync import synced_timestamp_ms

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
        query_string = "&".join(k + "=" + str(v) for k, v in sorted_params)
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
        params["timestamp"] = str(synced_timestamp_ms())
        params["recvWindow"] = "10000"
        query_string, signature = self.sign_params(params)
        url = (self.base_url + path + "?" + query_string
               + "&signature=" + signature)
        headers = {"X-BX-APIKEY": self.api_key}
        return {"url": url, "headers": headers, "method": method}

    def build_public_url(self, path, params=None):
        """Build public URL -- no timestamp, no signature (BUG-C07 fix)."""
        if params is None:
            params = {}
        if params:
            query_string = urlencode(sorted(params.items()))
            return self.base_url + path + "?" + query_string
        return self.base_url + path
'''
    write_file(target, content, "bingx_auth.py")
    MODIFIED.append(str(target))


def patch_main():
    """Patch main.py to initialize TimeSync at startup."""
    target = ROOT / "main.py"
    backup(target)
    src = target.read_text(encoding="utf-8")

    # 1. Add import after 'from ws_listener import WSListener'
    old_import = "from ws_listener import WSListener"
    new_import = old_import + "\nfrom time_sync import get_time_sync"
    if "from time_sync import" not in src:
        src = src.replace(old_import, new_import)

    # 2. Add sync init after 'auth = BingXAuth(api_key, secret_key, demo_mode=demo_mode)'
    old_auth = '    auth = BingXAuth(api_key, secret_key, demo_mode=demo_mode)'
    new_auth = old_auth + """
    # --- Time sync (prevents 109400 "timestamp is invalid") ---
    _ts = get_time_sync(base_url=auth.base_url, sync_interval=30)
    _ts_ok = _ts.sync()
    if not _ts_ok:
        logger.warning("Initial time sync FAILED -- using local clock")
    else:
        logger.info("Time sync OK: offset=%+dms", _ts.get_offset_ms())
    _ts.start_periodic()
    write_bot_status("Time sync: offset=" + str(_ts.get_offset_ms()) + "ms")"""
    if "get_time_sync(" not in src:
        src = src.replace(old_auth, new_auth)

    # 3. Add cleanup before ws_thread.stop()
    old_shutdown = "    ws_thread.stop()"
    new_shutdown = "    _ts.stop_periodic()\n" + old_shutdown
    if "_ts.stop_periodic()" not in src:
        src = src.replace(old_shutdown, new_shutdown, 1)

    write_file(target, src, "main.py")
    MODIFIED.append(str(target))


def patch_executor():
    """Patch executor.py to retry on 109400 timestamp error."""
    target = ROOT / "executor.py"
    backup(target)
    src = target.read_text(encoding="utf-8")

    # Add 109400 retry block after the 101209 block
    # Find the else block that handles generic errors (the catch-all after 101209)
    old_else = """\
            else:
                logger.error("API error %s: %s",
                             error_code, result.get("msg"))
                self.notifier.send(
                    "<b>ORDER FAILED</b>\\n" + side + " " + symbol)
                return None"""

    new_else = """\
            elif error_code == 109400:
                # Timestamp invalid -- force re-sync and retry once
                from time_sync import get_time_sync
                _ts = get_time_sync()
                _ts.force_resync()
                req_retry = self.auth.build_signed_request(
                    "POST", ORDER_PATH, dict(order_params))
                result = self._safe_post(
                    req_retry["url"], headers=req_retry["headers"])
                if result and result.get("code", 0) == 0:
                    logger.info("109400 retry OK: %s", symbol)
                    error_code = 0
                else:
                    logger.error("109400 retry FAILED: %s", symbol)
                    self.notifier.send(
                        "<b>ORDER FAILED</b>\\n" + side + " " + symbol
                        + "\\n109400 timestamp error after retry")
                    return None
            else:
                logger.error("API error %s: %s",
                             error_code, result.get("msg"))
                self.notifier.send(
                    "<b>ORDER FAILED</b>\\n" + side + " " + symbol)
                return None"""

    if "109400" not in src:
        src = src.replace(old_else, new_else)

    write_file(target, src, "executor.py")
    MODIFIED.append(str(target))


def patch_position_monitor():
    """Patch position_monitor.py to retry _fetch_positions on 109400."""
    target = ROOT / "position_monitor.py"
    backup(target)
    src = target.read_text(encoding="utf-8")

    # Replace _fetch_positions error handling to add 109400 retry
    old_block = """\
            if data.get("code", 0) != 0:
                logger.error("Positions API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data.get("data", [])"""

    new_block = """\
            if data.get("code", 0) != 0:
                if data.get("code") == 109400:
                    from time_sync import get_time_sync
                    _ts = get_time_sync()
                    _ts.force_resync()
                    req = self.auth.build_signed_request(
                        "GET", POSITIONS_PATH)
                    resp = requests.get(
                        req["url"], headers=req["headers"], timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("code", 0) == 0:
                        logger.info("109400 retry succeeded for positions")
                        return data.get("data", [])
                logger.error("Positions API error %s: %s",
                             data.get("code"), data.get("msg"))
                return None
            return data.get("data", [])"""

    if "force_resync" not in src:
        src = src.replace(old_block, new_block)

    write_file(target, src, "position_monitor.py")
    MODIFIED.append(str(target))


def patch_dashboard():
    """Patch bingx-live-dashboard-v1-4.py to use synced timestamps."""
    target = ROOT / "bingx-live-dashboard-v1-4.py"
    backup(target)
    src = target.read_text(encoding="utf-8")

    # 1. Add import after 'from dotenv import load_dotenv'
    old_import = "from dotenv import load_dotenv"
    new_import = old_import + "\nfrom time_sync import synced_timestamp_ms, get_time_sync"
    if "from time_sync import" not in src:
        src = src.replace(old_import, new_import)

    # 2. Add sync init after LOG = setup_logging() line
    old_log = 'LOG = setup_logging()\nLOG.info("Dashboard starting on port 8051")'
    new_log = old_log + """

# --- Time sync (prevents 109400 "timestamp is invalid") ---
_ts_sync = get_time_sync(base_url='https://open-api.bingx.com', sync_interval=30)
_ts_sync.sync()
_ts_sync.start_periodic()
LOG.info("TimeSync initialized: offset=%+dms", _ts_sync.get_offset_ms())"""
    if "_ts_sync" not in src:
        src = src.replace(old_log, new_log)

    # 3. Replace raw timestamp in _sign()
    old_ts = "params['timestamp'] = int(time.time() * 1000)"
    new_ts = "params['timestamp'] = synced_timestamp_ms()"
    if old_ts in src:
        src = src.replace(old_ts, new_ts)

    # 4. Add 109400 retry in _bingx_request
    old_err = """\
        if data.get('code', 0) != 0:
            return {'error': f"BingX error {data.get('code')}: {data.get('msg')}"}
        return data.get('data', {})"""

    new_err = """\
        if data.get('code', 0) != 0:
            if data.get('code') == 109400:
                from time_sync import get_time_sync as _gts
                _ts_retry = _gts()
                _ts_retry.force_resync()
                signed2 = _sign(dict(params))
                if method == 'GET':
                    resp = requests.get(url, params=signed2, headers=headers, timeout=8)
                elif method == 'DELETE':
                    resp = requests.delete(url, params=signed2, headers=headers, timeout=8)
                elif method == 'POST':
                    resp = requests.post(url, params=signed2, headers=headers, timeout=8)
                data2 = resp.json()
                if data2.get('code', 0) == 0:
                    LOG.info("109400 retry succeeded for %s", path)
                    return data2.get('data', {})
            return {'error': f"BingX error {data.get('code')}: {data.get('msg')}"}
        return data.get('data', {})"""

    if "force_resync" not in src:
        src = src.replace(old_err, new_err)

    write_file(target, src, "bingx-live-dashboard-v1-4.py")
    MODIFIED.append(str(target))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("BUILD: BingX Time Sync (fixes error 109400)")
    print("=" * 60)
    print()

    print("[1/6] Creating time_sync.py...")
    build_time_sync()
    print()

    print("[2/6] Patching bingx_auth.py...")
    patch_bingx_auth()
    print()

    print("[3/6] Patching main.py...")
    patch_main()
    print()

    print("[4/6] Patching executor.py...")
    patch_executor()
    print()

    print("[5/6] Patching position_monitor.py...")
    patch_position_monitor()
    print()

    print("[6/6] Patching bingx-live-dashboard-v1-4.py...")
    patch_dashboard()
    print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Created:  {len(CREATED)}")
    for f in CREATED:
        print(f"    + {f}")
    print(f"  Backed up: {len(BACKED_UP)}")
    for f in BACKED_UP:
        print(f"    ~ {f}")
    print(f"  Modified: {len(MODIFIED)}")
    for f in MODIFIED:
        print(f"    * {f}")
    if ERRORS:
        print(f"\n  FAILURES: {len(ERRORS)}")
        for e in ERRORS:
            print(f"    ! {e}")
        sys.exit(1)
    else:
        print("\n  All files passed py_compile.")
        print("\n  Next steps:")
        print('    1. Restart bot:       python main.py')
        print('    2. Restart dashboard: python bingx-live-dashboard-v1-4.py')
        print('    3. Watch logs for "TimeSync: offset=+Xms"')
        print("    4. 109400 errors should stop within 30 seconds")
    print()
