"""
build_dashboard_v1_4_patch2.py

Fixes found after running v1-4:
  1. main.py: patch7 was applied twice -- duplicate write_bot_status function,
     duplicate BOT_ROOT/STATUS_PATH constants, duplicate clear-on-start block,
     and 5 duplicate call sites. All duplicates removed.
  2. dashboard.css: .status-feed-panel max-height 180px -> 360px
  3. bingx-live-dashboard-v1-4.py:
     - IndexError in _prepare_grouping: CB-T3 used
       prevent_initial_call='initial_duplicate', conflicting with CB-S1 on the
       same status-interval input. Fixed to prevent_initial_call=True.
     - Start Bot + Stop Bot replaced with single toggle button (bot-toggle-btn).
       Clicking toggles: starts if offline, stops if running. Writes
       "Bot stopped by dashboard" to bot-status.json on stop so Activity Log
       shows the event.
     - Header shows LIVE even when bot process is stopped. CB-3 now calls
       _is_bot_running() and shows OFFLINE when bot is not running.

Run: python scripts/build_dashboard_v1_4_patch2.py
"""
import py_compile
import sys
import shutil
from datetime import datetime
from pathlib import Path

BOT_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY  = BOT_ROOT / "main.py"
CSS_FILE = BOT_ROOT / "assets" / "dashboard.css"
DASH_V14 = BOT_ROOT / "bingx-live-dashboard-v1-4.py"

ERRORS = []


def safe_replace(text, old, new, label):
    """Replace old with new in text. Record error if old not found."""
    if old not in text:
        ERRORS.append(label + ": anchor not found")
        print("  FAIL: " + label)
        return text
    print("  PASS: " + label)
    return text.replace(old, new, 1)


def compile_check(path):
    """py_compile the patched file; record error on failure."""
    try:
        py_compile.compile(str(path), doraise=True)
        print("  SYNTAX OK: " + path.name)
    except py_compile.PyCompileError as e:
        ERRORS.append("syntax error in " + path.name + ": " + str(e))
        print("  SYNTAX FAIL: " + str(e))


def backup(path):
    """Create timestamped backup of path before patching."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path.with_suffix("." + ts + ".bak" + path.suffix)
    shutil.copy2(path, bak)
    print("  Backup: " + str(bak))


# ---------------------------------------------------------------------------
# main.py patches
# ---------------------------------------------------------------------------

# P1: Remove second (duplicate) write_bot_status function block.
# The first os.replace in the first function is followed by 3 blank lines
# then the duplicate block comment, constants, and function definition.
# The second os.replace ends the duplicate function, followed by 2 blank lines
# then def main(). We collapse all of that to just 2 blank lines + def main().

P1_OLD = '''    os.replace(tmp, STATUS_PATH)



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


def main():'''

P1_NEW = '''    os.replace(tmp, STATUS_PATH)


def main():'''

# P2: Remove duplicate clear-on-start block inside main().
P2_OLD = '''    # Clear status file from previous run
    import json as _json_init
    STATUS_PATH.write_text(
        _json_init.dumps({"bot_start": datetime.now(timezone.utc).isoformat(),
                          "messages": []}, indent=2),
        encoding="utf-8")
    # Clear status file from previous run
    import json as _json_init
    STATUS_PATH.write_text(
        _json_init.dumps({"bot_start": datetime.now(timezone.utc).isoformat(),
                          "messages": []}, indent=2),
        encoding="utf-8")
    utc4'''

P2_NEW = '''    # Clear status file from previous run
    import json as _json_init
    STATUS_PATH.write_text(
        _json_init.dumps({"bot_start": datetime.now(timezone.utc).isoformat(),
                          "messages": []}, indent=2),
        encoding="utf-8")
    utc4'''

# P3a-P3e: Remove duplicate call sites (each pair is two identical consecutive lines).

P3a_OLD = ('    write_bot_status("Config loaded: " + str(len(symbols)) + " coins, " + timeframe)\n'
           '    write_bot_status("Config loaded: " + str(len(symbols)) + " coins, " + timeframe)')
P3a_NEW = ('    write_bot_status("Config loaded: " + str(len(symbols)) + " coins, " + timeframe)')

P3b_OLD = ('    write_bot_status("Strategy loaded: " + strat_cfg.get("plugin", "mock_strategy"))\n'
           '    write_bot_status("Strategy loaded: " + strat_cfg.get("plugin", "mock_strategy"))')
P3b_NEW = ('    write_bot_status("Strategy loaded: " + strat_cfg.get("plugin", "mock_strategy"))')

P3c_OLD = ('    write_bot_status("Connected to BingX API")\n'
           '    write_bot_status("Connected to BingX API")')
P3c_NEW = ('    write_bot_status("Connected to BingX API")')

P3d_OLD = ('    write_bot_status("Positions reconciled")\n'
           '    write_bot_status("Positions reconciled")')
P3d_NEW = ('    write_bot_status("Positions reconciled")')

P3e_OLD = ('    write_bot_status("Bot running")\n'
           '    write_bot_status("Bot running")')
P3e_NEW = ('    write_bot_status("Bot running")')


# ---------------------------------------------------------------------------
# dashboard.css patches
# ---------------------------------------------------------------------------

P4_OLD = '    font-size: 12px;\n    max-height: 180px;\n    overflow-y: auto;'
P4_NEW = '    font-size: 12px;\n    max-height: 360px;\n    overflow-y: auto;'


# ---------------------------------------------------------------------------
# bingx-live-dashboard-v1-4.py patches
# ---------------------------------------------------------------------------

# P5: Replace two-button layout (Start Bot + Stop Bot) with single toggle button.
P5_OLD = '''        html.Div([
            html.Button(
                "Start Bot", id='start-bot-btn', n_clicks=0,
                style={
                    'marginRight': '8px',
                    'background': COLORS['green'],
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 20px',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                },
            ),
            html.Button(
                "Stop Bot", id='stop-bot-btn', n_clicks=0,
                style={
                    'marginRight': '16px',
                    'background': COLORS['red'],
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 20px',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                },
            ),
            html.Div(
                id='bot-run-status',
                children="Checking...",
                style={
                    'display': 'inline-block',
                    'padding': '6px 12px',
                    'background': COLORS['panel'],
                    'borderRadius': '4px',
                    'fontFamily': 'monospace',
                    'fontSize': '13px',
                    'color': COLORS['muted'],
                },
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),'''

P5_NEW = '''        html.Div([
            html.Button(
                "Start Bot", id='bot-toggle-btn', n_clicks=0,
                style={
                    'marginRight': '16px',
                    'background': COLORS['green'],
                    'color': 'white',
                    'border': 'none',
                    'padding': '8px 20px',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                },
            ),
            html.Div(
                id='bot-run-status',
                children="Checking...",
                style={
                    'display': 'inline-block',
                    'padding': '6px 12px',
                    'background': COLORS['panel'],
                    'borderRadius': '4px',
                    'fontFamily': 'monospace',
                    'fontSize': '13px',
                    'color': COLORS['muted'],
                },
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),'''

# P6: Replace CB-T1 (start_bot_cb) + CB-T2 (stop_bot_cb) with single toggle_bot_cb.
# Also defines _BTN_START_STYLE and _BTN_STOP_STYLE at module scope for reuse by CB-T3.
P6_OLD = '''# ---------------------------------------------------------------------------
# CB-T1: Start Bot button
# ---------------------------------------------------------------------------

@callback(
    Output('bot-run-status', 'children', allow_duplicate=True),
    Output('start-bot-btn', 'disabled', allow_duplicate=True),
    Output('stop-bot-btn', 'disabled', allow_duplicate=True),
    Input('start-bot-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def start_bot_cb(n_clicks):
    """Launch bot process in a new console window."""
    if _is_bot_running():
        return "Bot already running", True, False
    try:
        pid = _start_bot_process()
        return "Bot started (PID " + str(pid) + ")", True, False
    except Exception as e:
        LOG.error("Start bot failed: %s", e)
        return "Error: " + str(e), False, True


# ---------------------------------------------------------------------------
# CB-T2: Stop Bot button
# ---------------------------------------------------------------------------

@callback(
    Output('bot-run-status', 'children', allow_duplicate=True),
    Output('start-bot-btn', 'disabled', allow_duplicate=True),
    Output('stop-bot-btn', 'disabled', allow_duplicate=True),
    Input('stop-bot-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def stop_bot_cb(n_clicks):
    """Stop the running bot process."""
    if not _is_bot_running():
        return "Bot is not running", False, True
    ok = _stop_bot_process()
    if ok:
        return "Bot stopped", False, True
    return "Stop failed", False, False'''

P6_NEW = '''# ---------------------------------------------------------------------------
# CB-T1: Toggle bot start/stop
# ---------------------------------------------------------------------------

_BTN_START_STYLE = {
    'marginRight': '16px', 'background': COLORS['green'], 'color': 'white',
    'border': 'none', 'padding': '8px 20px', 'borderRadius': '4px',
    'cursor': 'pointer', 'fontWeight': 'bold',
}
_BTN_STOP_STYLE = {
    'marginRight': '16px', 'background': COLORS['red'], 'color': 'white',
    'border': 'none', 'padding': '8px 20px', 'borderRadius': '4px',
    'cursor': 'pointer', 'fontWeight': 'bold',
}


@callback(
    Output('bot-run-status', 'children', allow_duplicate=True),
    Output('bot-toggle-btn', 'children', allow_duplicate=True),
    Output('bot-toggle-btn', 'style', allow_duplicate=True),
    Input('bot-toggle-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def toggle_bot_cb(n_clicks):
    """Toggle bot: stop if running, start if offline."""
    if _is_bot_running():
        ok = _stop_bot_process()
        if ok:
            try:
                import json as _j
                from datetime import datetime as _dt, timezone as _tz
                sp = BASE_DIR / "bot-status.json"
                d = {}
                if sp.exists():
                    d = _j.loads(sp.read_text(encoding="utf-8"))
                d.setdefault("messages", [])
                d["messages"].append({"ts": _dt.now(_tz.utc).isoformat(),
                                      "msg": "Bot stopped by dashboard"})
                tmp = sp.with_suffix(".tmp")
                tmp.write_text(_j.dumps(d, indent=2), encoding="utf-8")
                os.replace(tmp, sp)
            except Exception:
                pass
            return "Bot stopped", "Start Bot", _BTN_START_STYLE
        return "Stop failed", "Stop Bot", _BTN_STOP_STYLE
    else:
        try:
            pid = _start_bot_process()
            return "Bot started (PID " + str(pid) + ")", "Stop Bot", _BTN_STOP_STYLE
        except Exception as e:
            LOG.error("Start bot failed: %s", e)
            return "Error: " + str(e), "Start Bot", _BTN_START_STYLE'''

# P7: Replace CB-T3 -- fix prevent_initial_call and update outputs to use bot-toggle-btn.
P7_OLD = '''@callback(
    Output('bot-run-status', 'children', allow_duplicate=True),
    Output('start-bot-btn', 'disabled', allow_duplicate=True),
    Output('stop-bot-btn', 'disabled', allow_duplicate=True),
    Input('status-interval', 'n_intervals'),
    prevent_initial_call='initial_duplicate',
)
def poll_bot_running(n_intervals):
    """Check bot process status on each 5s tick; update button state."""
    running = _is_bot_running()
    if running:
        return "RUNNING", True, False
    return "Offline", False, True'''

P7_NEW = '''@callback(
    Output('bot-run-status', 'children', allow_duplicate=True),
    Output('bot-toggle-btn', 'children', allow_duplicate=True),
    Output('bot-toggle-btn', 'style', allow_duplicate=True),
    Input('status-interval', 'n_intervals'),
    prevent_initial_call=True,
)
def poll_bot_running(n_intervals):
    """Check bot process status on each 5s tick; update toggle button state."""
    running = _is_bot_running()
    if running:
        return "RUNNING", "Stop Bot", _BTN_STOP_STYLE
    return "Offline", "Start Bot", _BTN_START_STYLE'''

# P8: Add status-interval as CB-3 input so header refreshes on every 5s tick.
P8_OLD = '''@callback(
    Output('status-bar', 'children'),
    Input('store-state',  'data'),
    Input('store-config', 'data'),
    Input('store-unrealized', 'data'),
)
def update_status_bar(state_json, config_json, unrealized_json):
    """Render top status bar with bot mode, daily PnL, positions, risk usage."""'''

P8_NEW = '''@callback(
    Output('status-bar', 'children'),
    Input('store-state',  'data'),
    Input('store-config', 'data'),
    Input('store-unrealized', 'data'),
    Input('status-interval', 'n_intervals'),
)
def update_status_bar(state_json, config_json, unrealized_json, _n_intervals):
    """Render top status bar with bot mode, daily PnL, positions, risk usage."""'''

# P9: In CB-3 status label logic, add OFFLINE check for stopped bot.
P9_OLD = '''        # Determine status label and color
        if halt_flag:
            status_label, status_color = "HALTED", COLORS['red']
        elif demo_mode:
            status_label, status_color = "DEMO", COLORS['blue']
        else:
            status_label, status_color = "LIVE", COLORS['green']'''

P9_NEW = '''        # Determine status label and color
        if halt_flag:
            status_label, status_color = "HALTED", COLORS['red']
        elif not _is_bot_running():
            status_label, status_color = "OFFLINE", COLORS['muted']
        elif demo_mode:
            status_label, status_color = "DEMO", COLORS['blue']
        else:
            status_label, status_color = "LIVE", COLORS['green']'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Apply all patches to main.py, dashboard.css, and v1-4 dashboard."""
    print("=" * 60)
    print("Patch 2: v1-4 dedup + toggle button + OFFLINE status")
    print("=" * 60)

    # --- main.py ---
    print()
    print("--- main.py ---")
    if not MAIN_PY.exists():
        print("FAIL: main.py not found: " + str(MAIN_PY))
        sys.exit(1)
    backup(MAIN_PY)
    text = MAIN_PY.read_text(encoding="utf-8")
    print("Read: " + str(MAIN_PY) + " (" + str(len(text)) + " chars)")
    print()
    print("Applying patches...")
    text = safe_replace(text, P1_OLD, P1_NEW, "P1-remove-dup-write_bot_status-block")
    text = safe_replace(text, P2_OLD, P2_NEW, "P2-remove-dup-clear-on-start")
    text = safe_replace(text, P3a_OLD, P3a_NEW, "P3a-remove-dup-config-loaded")
    text = safe_replace(text, P3b_OLD, P3b_NEW, "P3b-remove-dup-strategy-loaded")
    text = safe_replace(text, P3c_OLD, P3c_NEW, "P3c-remove-dup-connected")
    text = safe_replace(text, P3d_OLD, P3d_NEW, "P3d-remove-dup-positions-reconciled")
    text = safe_replace(text, P3e_OLD, P3e_NEW, "P3e-remove-dup-bot-running")
    print()
    MAIN_PY.write_text(text, encoding="utf-8")
    print("Wrote: " + str(MAIN_PY))
    compile_check(MAIN_PY)

    # --- dashboard.css ---
    print()
    print("--- dashboard.css ---")
    if not CSS_FILE.exists():
        print("FAIL: dashboard.css not found: " + str(CSS_FILE))
        sys.exit(1)
    backup(CSS_FILE)
    css = CSS_FILE.read_text(encoding="utf-8")
    print("Read: " + str(CSS_FILE) + " (" + str(len(css)) + " chars)")
    print()
    print("Applying patches...")
    css = safe_replace(css, P4_OLD, P4_NEW, "P4-status-feed-panel-max-height-360")
    print()
    CSS_FILE.write_text(css, encoding="utf-8")
    print("Wrote: " + str(CSS_FILE))

    # --- bingx-live-dashboard-v1-4.py ---
    print()
    print("--- bingx-live-dashboard-v1-4.py ---")
    if not DASH_V14.exists():
        print("FAIL: v1-4 not found: " + str(DASH_V14))
        sys.exit(1)
    backup(DASH_V14)
    text = DASH_V14.read_text(encoding="utf-8")
    print("Read: " + str(DASH_V14) + " (" + str(len(text)) + " chars)")
    print()
    print("Applying patches...")
    text = safe_replace(text, P5_OLD, P5_NEW, "P5-toggle-button-layout")
    text = safe_replace(text, P6_OLD, P6_NEW, "P6-CB-T1-T2-to-toggle_bot_cb")
    text = safe_replace(text, P7_OLD, P7_NEW, "P7-CB-T3-fix-prevent-initial-call")
    text = safe_replace(text, P8_OLD, P8_NEW, "P8-CB-3-add-status-interval-input")
    text = safe_replace(text, P9_OLD, P9_NEW, "P9-CB-3-add-OFFLINE-check")
    print()
    DASH_V14.write_text(text, encoding="utf-8")
    print("Wrote: " + str(DASH_V14))
    compile_check(DASH_V14)

    # --- Result ---
    print()
    print("=" * 60)
    if ERRORS:
        print("RESULT: FAIL")
        for e in ERRORS:
            print("  ERROR: " + e)
        sys.exit(1)
    else:
        print("RESULT: PASS")
        print()
        print("Next steps:")
        print('  1. Restart bot:       python "' + str(MAIN_PY) + '"')
        print('  2. Restart dashboard: python "' + str(DASH_V14) + '"')
        print()
        print("What changed:")
        print("  main.py     -- duplicate write_bot_status removed; all 5 call sites deduped")
        print("  dashboard.css -- status feed max-height 180->360px")
        print("  v1-4 dashboard:")
        print("    - IndexError fixed (CB-T3 prevent_initial_call)")
        print("    - Toggle button replaces Start Bot + Stop Bot")
        print("    - Header shows OFFLINE when bot process is stopped")
        print("    - Stop Bot writes 'Bot stopped by dashboard' to Activity Log")


if __name__ == "__main__":
    main()
