"""
build_dashboard_v1_3_patch7.py

Patch 7: Bot status feed in the Operational tab.

Adds a live message panel showing bot startup lifecycle:
  "Config loaded", "Strategy loaded", "Warming up 47 symbols...",
  "Warmup 10/47", "Warmup complete", "Bot running", etc.

Architecture:
  - Bot writes to bot-status.json at key startup milestones (main.py)
  - data_fetcher.py warmup() gains a progress_callback param
  - Dashboard polls bot-status.json every 5s (new dcc.Interval)
  - Status feed panel rendered in the Operational tab

Files changed:
  - main.py                        (write_bot_status helper + 7 calls)
  - data_fetcher.py                (progress_callback param in warmup)
  - bingx-live-dashboard-v1-3.py  (Interval, Store, UI, 2 callbacks)
  - assets/dashboard.css           (status feed panel styles)

Run: python scripts/build_dashboard_v1_3_patch7.py
"""
import shutil
import sys
import py_compile
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BOT_ROOT   = Path(__file__).resolve().parent.parent
MAIN_PY    = BOT_ROOT / "main.py"
FETCHER_PY = BOT_ROOT / "data_fetcher.py"
DASH_PY    = BOT_ROOT / "bingx-live-dashboard-v1-3.py"
CSS_PATH   = BOT_ROOT / "assets" / "dashboard.css"

ERRORS = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read(path):
    """Read file text."""
    return path.read_text(encoding="utf-8")


def write(path, text):
    """Write file text."""
    path.write_text(text, encoding="utf-8")


def backup(path):
    """Create timestamped backup of path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.parent / (path.stem + "." + ts + ".bak" + path.suffix)
    shutil.copy2(path, bak)
    return bak


def safe_replace(text, old, new, label):
    """Replace old with new in text. Record error if old not found."""
    if old not in text:
        ERRORS.append(label + ": anchor not found")
        print("  FAIL: " + label)
        return text
    print("  PASS: " + label)
    return text.replace(old, new, 1)


def compile_check(path, label):
    """Run py_compile on path. Record error on failure."""
    try:
        py_compile.compile(str(path), doraise=True)
        print("  PASS: py_compile " + label)
    except py_compile.PyCompileError as e:
        ERRORS.append("py_compile " + label + ": " + str(e))
        print("  FAIL: py_compile " + label + ": " + str(e))


# ---------------------------------------------------------------------------
# P1: main.py -- write_bot_status helper + STATUS_PATH + 7 call sites
# ---------------------------------------------------------------------------

MAIN_HELPER = '''
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


'''

# Anchor: inject helper just before main() definition
MAIN_HELPER_ANCHOR = 'def main():\n    """Load config, init components, run loops."""'
MAIN_HELPER_NEW = MAIN_HELPER + 'def main():\n    """Load config, init components, run loops."""'

# P1-A: clear status file at process start (after setup_logging)
MAIN_CLEAR_ANCHOR = '    logger.info("=== BingX Connector Starting ===")'
MAIN_CLEAR_NEW = (
    '    logger.info("=== BingX Connector Starting ===")\n'
    '    # Clear status file from previous run\n'
    '    import json as _json_init\n'
    '    STATUS_PATH.write_text(\n'
    '        _json_init.dumps({"bot_start": datetime.now(timezone.utc).isoformat(),\n'
    '                          "messages": []}, indent=2),\n'
    '        encoding="utf-8")'
)

# P1-B: after config loaded (line ~185)
MAIN_CFG_ANCHOR = (
    '    logger.info("Config: demo=%s coins=%s tf=%s poll=%ds",\n'
    '                demo_mode, str(symbols), timeframe, poll_interval)'
)
MAIN_CFG_NEW = (
    '    logger.info("Config: demo=%s coins=%s tf=%s poll=%ds",\n'
    '                demo_mode, str(symbols), timeframe, poll_interval)\n'
    '    write_bot_status("Config loaded: " + str(len(symbols)) + " coins, " + timeframe)'
)

# P1-C: after StrategyAdapter constructed (line ~209)
MAIN_STRAT_ANCHOR = (
    '    logger.info("Setting leverage and margin mode...")'
)
MAIN_STRAT_NEW = (
    '    write_bot_status("Strategy loaded: " + strat_cfg.get("plugin", "mock_strategy"))\n'
    '    logger.info("Setting leverage and margin mode...")'
)

# P1-D: after commission rate fetched (line ~215)
MAIN_COMM_ANCHOR = '    commission_rate = fetch_commission_rate(auth)'
MAIN_COMM_NEW = (
    '    commission_rate = fetch_commission_rate(auth)\n'
    '    write_bot_status("Connected to BingX API")'
)

# P1-E: after reconcile (line ~239)
MAIN_RECONCILE_ANCHOR = '    logger.info("Warming up market data...")'
MAIN_RECONCILE_NEW = (
    '    write_bot_status("Positions reconciled")\n'
    '    logger.info("Warming up market data...")'
)

# P1-F: warmup call with progress callback
MAIN_WARMUP_ANCHOR = '    feed.warmup()'
MAIN_WARMUP_NEW = (
    '    write_bot_status("Warming up " + str(len(symbols)) + " symbols...")\n'
    '    feed.warmup(\n'
    '        progress_callback=lambda i, n: write_bot_status(\n'
    '            "Warmup " + str(i) + "/" + str(n)))\n'
    '    write_bot_status("Warmup complete (" + str(len(symbols)) + " symbols)")'
)

# P1-G: after threads started (line ~269)
MAIN_THREADS_ANCHOR = '    logger.info("Threads started: MarketLoop + MonitorLoop + WSListener")'
MAIN_THREADS_NEW = (
    '    logger.info("Threads started: MarketLoop + MonitorLoop + WSListener")\n'
    '    write_bot_status("Bot running")'
)


def patch_main():
    """Apply all main.py changes."""
    print("\nP1: main.py -- write_bot_status helper + status calls")
    bak = backup(MAIN_PY)
    print("  Backup: " + str(bak))
    text = read(MAIN_PY)

    text = safe_replace(text, MAIN_HELPER_ANCHOR,    MAIN_HELPER_NEW,    "P1-helper")
    text = safe_replace(text, MAIN_CLEAR_ANCHOR,     MAIN_CLEAR_NEW,     "P1-A-clear")
    text = safe_replace(text, MAIN_CFG_ANCHOR,       MAIN_CFG_NEW,       "P1-B-config")
    text = safe_replace(text, MAIN_STRAT_ANCHOR,     MAIN_STRAT_NEW,     "P1-C-strategy")
    text = safe_replace(text, MAIN_COMM_ANCHOR,      MAIN_COMM_NEW,      "P1-D-connected")
    text = safe_replace(text, MAIN_RECONCILE_ANCHOR, MAIN_RECONCILE_NEW, "P1-E-reconcile")
    text = safe_replace(text, MAIN_WARMUP_ANCHOR,    MAIN_WARMUP_NEW,    "P1-F-warmup")
    text = safe_replace(text, MAIN_THREADS_ANCHOR,   MAIN_THREADS_NEW,   "P1-G-running")

    write(MAIN_PY, text)
    compile_check(MAIN_PY, "main.py")


# ---------------------------------------------------------------------------
# P2: data_fetcher.py -- progress_callback param in warmup()
# ---------------------------------------------------------------------------

FETCHER_OLD = '''\
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
                logger.warning("Warmup failed for %s", symbol)'''

FETCHER_NEW = '''\
    def warmup(self, progress_callback=None):
        """Initial fetch for all symbols at startup."""
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
                progress_callback(i + 1, total)'''


def patch_fetcher():
    """Add progress_callback to data_fetcher.py warmup()."""
    print("\nP2: data_fetcher.py -- warmup progress_callback")
    bak = backup(FETCHER_PY)
    print("  Backup: " + str(bak))
    text = read(FETCHER_PY)
    text = safe_replace(text, FETCHER_OLD, FETCHER_NEW, "P2-warmup")
    write(FETCHER_PY, text)
    compile_check(FETCHER_PY, "data_fetcher.py")


# ---------------------------------------------------------------------------
# P3: bingx-live-dashboard-v1-3.py -- Interval, Store, UI, 2 callbacks
# ---------------------------------------------------------------------------

# P3-A: add store-bot-status to layout store list
DASH_STORE_ANCHOR = (
    "    dcc.Store(id='store-unrealized', storage_type='memory'),"
)
DASH_STORE_NEW = (
    "    dcc.Store(id='store-unrealized', storage_type='memory'),\n"
    "    dcc.Store(id='store-bot-status', data=[]),\n"
    "    # 5s interval for bot status feed\n"
    "    dcc.Interval(id='status-interval', interval=5000, n_intervals=0),"
)

# P3-B: add status feed panel to make_operational_tab()
DASH_OPS_ANCHOR = (
    "        html.Div(id='pos-action-status',    # shows success/error from actions\n"
    "                 style={'marginTop': '8px', 'color': COLORS['green']}),\n"
    "    ])"
)
DASH_OPS_NEW = (
    "        html.Div(id='pos-action-status',    # shows success/error from actions\n"
    "                 style={'marginTop': '8px', 'color': COLORS['green']}),\n"
    "        # Bot status feed (Patch 7)\n"
    "        html.Div([\n"
    "            html.H4('Bot Status',\n"
    "                    style={'color': COLORS['muted'], 'fontSize': '13px',\n"
    "                           'marginTop': '20px', 'marginBottom': '6px'}),\n"
    "            html.Div(id='status-feed', className='status-feed-panel'),\n"
    "        ]),\n"
    "    ])"
)

# P3-C: add 2 new callbacks before the entry point block
DASH_CB_ANCHOR = (
    "# ---------------------------------------------------------------------------\n"
    "# Entry point\n"
    "# ---------------------------------------------------------------------------"
)
DASH_CB_NEW = '''\
# ---------------------------------------------------------------------------
# CB-S1: Load bot-status.json every 5s
# ---------------------------------------------------------------------------

@callback(
    Output('store-bot-status', 'data'),
    Input('status-interval', 'n_intervals'),
)
def load_bot_status(n_intervals):
    """Read bot-status.json and return messages list (newest first, max 20)."""
    try:
        status_path = BASE_DIR / "bot-status.json"
        if not status_path.exists():
            return []
        data = json.loads(status_path.read_text(encoding="utf-8"))
        msgs = data.get("messages", [])
        # Return newest first, capped at 20
        return list(reversed(msgs[-20:]))
    except Exception:
        return []


# ---------------------------------------------------------------------------
# CB-S2: Render bot status feed from store
# ---------------------------------------------------------------------------

@callback(
    Output('status-feed', 'children'),
    Input('store-bot-status', 'data'),
)
def render_status_feed(messages):
    """Render status messages as a styled list in the feed panel."""
    if not messages:
        return html.P("Bot offline", style={'color': COLORS['muted'],
                                            'margin': '0', 'fontFamily': 'monospace'})
    rows = []
    for entry in messages:
        ts_raw = entry.get("ts", "")
        msg = entry.get("msg", "")
        # Format timestamp as HH:MM:SS
        try:
            from datetime import datetime as _dt, timezone as _tz
            dt = _dt.fromisoformat(ts_raw)
            ts_str = dt.astimezone(_tz.utc).strftime("%H:%M:%S")
        except Exception:
            ts_str = ts_raw[:8] if ts_raw else "?"
        rows.append(
            html.P([
                html.Span(ts_str, className='status-ts'),
                msg,
            ], style={'margin': '1px 0'})
        )
    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------'''


def patch_dashboard():
    """Apply dashboard layout + callback changes."""
    print("\nP3: bingx-live-dashboard-v1-3.py -- Interval, Store, UI, callbacks")
    bak = backup(DASH_PY)
    print("  Backup: " + str(bak))
    text = read(DASH_PY)

    text = safe_replace(text, DASH_STORE_ANCHOR, DASH_STORE_NEW, "P3-A-store")
    text = safe_replace(text, DASH_OPS_ANCHOR,   DASH_OPS_NEW,   "P3-B-ops-tab")
    text = safe_replace(text, DASH_CB_ANCHOR,    DASH_CB_NEW,    "P3-C-callbacks")

    write(DASH_PY, text)
    compile_check(DASH_PY, "bingx-live-dashboard-v1-3.py")


# ---------------------------------------------------------------------------
# P4: assets/dashboard.css -- status feed panel styles
# ---------------------------------------------------------------------------

CSS_GUARD = "status-feed-panel"

CSS_FEED_BLOCK = """
/* === Patch 7: Bot status feed panel === */
.status-feed-panel {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 10px 14px;
    font-family: monospace;
    font-size: 12px;
    max-height: 180px;
    overflow-y: auto;
    color: #c9d1d9;
}
.status-feed-panel p {
    margin: 2px 0;
    line-height: 1.5;
}
.status-ts {
    color: #484f58;
    margin-right: 8px;
}
"""


def patch_css():
    """Append status feed CSS."""
    print("\nP4: assets/dashboard.css -- status feed styles")
    text = read(CSS_PATH)
    if CSS_GUARD in text:
        print("  SKIP: status-feed-panel already in CSS")
        return
    bak = backup(CSS_PATH)
    print("  Backup: " + str(bak))
    write(CSS_PATH, text + CSS_FEED_BLOCK)
    verify = read(CSS_PATH)
    if CSS_GUARD in verify:
        print("  PASS: P4-css-feed")
    else:
        ERRORS.append("P4-css-feed: guard not found after write")
        print("  FAIL: P4-css-feed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Run all patches and report results."""
    print("=" * 60)
    print("Patch 7: Bot status feed")
    print("=" * 60)

    patch_main()
    patch_fetcher()
    patch_dashboard()
    patch_css()

    print("\n" + "=" * 60)
    if ERRORS:
        print("RESULT: FAIL")
        for e in ERRORS:
            print("  ERROR: " + e)
        sys.exit(1)
    else:
        print("RESULT: PASS")
        print("")
        print("Next steps:")
        print("  1. Start bot (generates bot-status.json):")
        print('     python "' + str(BOT_ROOT / "main.py") + '"')
        print("  2. Start dashboard:")
        print('     python "' + str(DASH_PY) + '"')
        print("  3. Open Operational tab -- Bot Status panel shows startup messages")


if __name__ == "__main__":
    main()
