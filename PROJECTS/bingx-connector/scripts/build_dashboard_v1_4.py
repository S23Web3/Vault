"""
build_dashboard_v1_4.py

Produces bingx-live-dashboard-v1-4.py from v1-3 source.

Patches applied (15 total):
  P1   - Docstring title: v1-3 -> v1-4
  P2   - Docstring tabs list: 5 tabs -> 6 tabs, renamed
  P3   - Docstring run command: filename update
  P3b  - Docstring gunicorn module name update
  P4   - Add import subprocess
  P5   - Add BOT_PID_PATH constant after LOG_DIR
  P6   - Add bot process helpers (_is_bot_running, _start_bot_process, _stop_bot_process)
  P7   - Rename make_operational_tab -> make_live_trades_tab, remove Bot Status section
  P8   - Add make_bot_terminal_tab() before make_history_tab()
  P9   - Rename make_bot_controls_tab -> make_strategy_params_tab
  P10  - App title: v1-3 -> v1-4
  P11  - Tab list: 5 -> 6 tabs, reordered, renamed
  P12  - Tab content divs: 5 -> 6, reordered, renamed function calls
  P13  - CB-2 clientside callback: 5 -> 6 tabs
  P14  - Add CB-T1 (start), CB-T2 (stop), CB-T3 (poll) before entry point

Run: python scripts/build_dashboard_v1_4.py
"""
import shutil
import sys
import py_compile
from datetime import datetime
from pathlib import Path

BOT_ROOT = Path(__file__).resolve().parent.parent
DASH_IN  = BOT_ROOT / "bingx-live-dashboard-v1-3.py"
DASH_OUT = BOT_ROOT / "bingx-live-dashboard-v1-4.py"

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


# ===========================================================================
# P1: Docstring title line
# ===========================================================================

P1_OLD = 'BingX Live Dashboard v1-3\n'
P1_NEW = 'BingX Live Dashboard v1-4\n'


# ===========================================================================
# P2: Docstring tabs list
# ===========================================================================

P2_OLD = '5 tabs: Operational | History | Analytics | Coin Summary | Bot Controls\n'
P2_NEW = '6 tabs: Live Trades | Bot Terminal | Strategy Parameters | History | Analytics | Coin Summary\n'


# ===========================================================================
# P3: Docstring run command filename
# ===========================================================================

P3_OLD = '    python bingx-live-dashboard-v1-3.py\n'
P3_NEW = '    python bingx-live-dashboard-v1-4.py\n'


# ===========================================================================
# P3b: Docstring gunicorn module name
# ===========================================================================

P3B_OLD = 'bingx_live_dashboard_v1_3:server'
P3B_NEW = 'bingx_live_dashboard_v1_4:server'


# ===========================================================================
# P4: Add import subprocess before import threading
# ===========================================================================

P4_OLD = 'import threading\n'
P4_NEW = 'import subprocess\nimport threading\n'


# ===========================================================================
# P5: Add BOT_PID_PATH constant after LOG_DIR
# ===========================================================================

P5_OLD = 'LOG_DIR = BASE_DIR / "logs"'
P5_NEW = 'LOG_DIR = BASE_DIR / "logs"\nBOT_PID_PATH = BASE_DIR / "bot.pid"'


# ===========================================================================
# P6: Bot process helpers (insert after LOG.info startup line)
# ===========================================================================

P6_OLD = 'LOG.info("Dashboard starting on port 8051")'

P6_NEW = '''LOG.info("Dashboard starting on port 8051")


# ---------------------------------------------------------------------------
# Bot process helpers (v1-4)
# ---------------------------------------------------------------------------

def _is_bot_running() -> bool:
    """Check if bot process is alive via PID file + tasklist."""
    if not BOT_PID_PATH.exists():
        return False
    try:
        pid = int(BOT_PID_PATH.read_text(encoding="utf-8").strip())
        result = subprocess.run(
            ["tasklist", "/FI", "PID eq " + str(pid), "/NH"],
            capture_output=True, text=True, timeout=5,
        )
        return str(pid) in result.stdout
    except Exception:
        return False


def _start_bot_process() -> int:
    """Launch main.py in a new console window. Returns PID."""
    proc = subprocess.Popen(
        ["python", str(BASE_DIR / "main.py")],
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    BOT_PID_PATH.write_text(str(proc.pid), encoding="utf-8")
    LOG.info("Bot started: PID %d", proc.pid)
    return proc.pid


def _stop_bot_process() -> bool:
    """Kill bot by PID from pid file. Returns True on success."""
    if not BOT_PID_PATH.exists():
        return False
    try:
        pid = int(BOT_PID_PATH.read_text(encoding="utf-8").strip())
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], timeout=10)
        BOT_PID_PATH.unlink(missing_ok=True)
        LOG.info("Bot stopped: PID %d", pid)
        return True
    except Exception as e:
        LOG.error("Stop bot failed: %s", e)
        return False'''


# ===========================================================================
# P7: Rename make_operational_tab -> make_live_trades_tab
#     Remove Bot Status section (status-feed moves to Bot Terminal tab)
# ===========================================================================

P7_OLD = '''def make_operational_tab() -> html.Div:
    """Build layout for Operational tab -- positions grid + action panel."""
    return html.Div([
        html.H3("Open Positions"),
        dcc.Loading(id='positions-loading', type='circle', children=[
            dag.AgGrid(
                id='positions-grid',
                columnDefs=POSITION_COLUMNS,
                rowData=[],
                dashGridOptions={
                    'rowSelection': 'single',
                    'overlayNoRowsTemplate': 'No open positions',
                    'rowClassRules': {
                        'row-long':  {'function': 'params.data.Dir === "LONG"'},
                        'row-short': {'function': 'params.data.Dir === "SHORT"'},
                    }
                },
                defaultColDef={'sortable': True, 'resizable': True},
                className='ag-theme-alpine-dark',
                style={'height': '300px'},
            ),
        ]),
        html.Div(id='selected-pos-info'),   # shows selected row info + action buttons
        html.Div(id='pos-action-status',    # shows success/error from actions
                 style={'marginTop': '8px', 'color': COLORS['green']}),
        # Bot status feed (Patch 7)
        html.Div([
            html.H4('Bot Status',
                    style={'color': COLORS['muted'], 'fontSize': '13px',
                           'marginTop': '20px', 'marginBottom': '6px'}),
            html.Div(id='status-feed', className='status-feed-panel'),
        ]),
    ])'''

P7_NEW = '''def make_live_trades_tab() -> html.Div:
    """Build layout for Live Trades tab -- positions grid + action panel."""
    return html.Div([
        html.H3("Open Positions"),
        dcc.Loading(id='positions-loading', type='circle', children=[
            dag.AgGrid(
                id='positions-grid',
                columnDefs=POSITION_COLUMNS,
                rowData=[],
                dashGridOptions={
                    'rowSelection': 'single',
                    'overlayNoRowsTemplate': 'No open positions',
                    'rowClassRules': {
                        'row-long':  {'function': 'params.data.Dir === "LONG"'},
                        'row-short': {'function': 'params.data.Dir === "SHORT"'},
                    }
                },
                defaultColDef={'sortable': True, 'resizable': True},
                className='ag-theme-alpine-dark',
                style={'height': '300px'},
            ),
        ]),
        html.Div(id='selected-pos-info'),   # shows selected row info + action buttons
        html.Div(id='pos-action-status',    # shows success/error from actions
                 style={'marginTop': '8px', 'color': COLORS['green']}),
    ])'''


# ===========================================================================
# P8: Add make_bot_terminal_tab() before make_history_tab()
# ===========================================================================

P8_OLD = 'def make_history_tab() -> html.Div:'

P8_NEW = '''def make_bot_terminal_tab() -> html.Div:
    """Build layout for Bot Terminal tab -- start/stop bot + lifecycle messages."""
    return html.Div([
        html.H3("Bot Terminal"),
        html.P(
            "Launch and monitor the trading bot. Activity updates every 5 seconds.",
            style={'color': COLORS['muted'], 'marginBottom': '16px'},
        ),
        html.Div([
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
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
        html.H4(
            "Activity Log",
            style={'color': COLORS['muted'], 'fontSize': '13px', 'marginBottom': '6px'},
        ),
        html.Div(id='status-feed', className='status-feed-panel'),
    ])


def make_history_tab() -> html.Div:'''


# ===========================================================================
# P9: Rename make_bot_controls_tab -> make_strategy_params_tab
# ===========================================================================

P9_OLD = '''def make_bot_controls_tab() -> html.Div:
    """Build layout for Bot Controls tab -- config editor and halt/resume."""'''

P9_NEW = '''def make_strategy_params_tab() -> html.Div:
    """Build layout for Strategy Parameters tab -- config editor and halt/resume."""'''


# ===========================================================================
# P10: App title
# ===========================================================================

P10_OLD = "title='BingX Live Dashboard v1-3',"
P10_NEW = "title='BingX Live Dashboard v1-4',"


# ===========================================================================
# P11: Tab list (5 -> 6 tabs, reordered, renamed labels)
# ===========================================================================

P11_OLD = '''    dcc.Tabs(id='main-tabs', value='tab-ops',
             parent_style={'backgroundColor': '#0d1117'},
             style={'borderBottom': '1px solid #21262d'},
             children=[
        dcc.Tab(label='Operational',  value='tab-ops', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='History',      value='tab-hist', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Analytics',    value='tab-analytics', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Coin Summary', value='tab-coins', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Bot Controls', value='tab-controls', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
    ]),'''

P11_NEW = '''    dcc.Tabs(id='main-tabs', value='tab-ops',
             parent_style={'backgroundColor': '#0d1117'},
             style={'borderBottom': '1px solid #21262d'},
             children=[
        dcc.Tab(label='Live Trades',         value='tab-ops',      style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Bot Terminal',        value='tab-terminal', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Strategy Parameters', value='tab-controls', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='History',             value='tab-hist',     style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Analytics',           value='tab-analytics',style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Coin Summary',        value='tab-coins',    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
    ]),'''


# ===========================================================================
# P12: Tab content divs (5 -> 6, reordered, renamed function calls)
# ===========================================================================

P12_OLD = '''    # ALL tab content rendered at startup -- visibility toggled by clientside callback
    html.Div(id='tab-content-ops',       children=make_operational_tab(),
             style={'padding': '16px', 'display': 'block'}),
    html.Div(id='tab-content-hist',      children=make_history_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-analytics', children=make_analytics_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-coins',     children=make_coin_summary_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-controls',  children=make_bot_controls_tab(),
             style={'padding': '16px', 'display': 'none'}),'''

P12_NEW = '''    # ALL tab content rendered at startup -- visibility toggled by clientside callback
    html.Div(id='tab-content-ops',       children=make_live_trades_tab(),
             style={'padding': '16px', 'display': 'block'}),
    html.Div(id='tab-content-terminal',  children=make_bot_terminal_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-controls',  children=make_strategy_params_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-hist',      children=make_history_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-analytics', children=make_analytics_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-coins',     children=make_coin_summary_tab(),
             style={'padding': '16px', 'display': 'none'}),'''


# ===========================================================================
# P13: CB-2 clientside callback (5 -> 6 tabs)
# ===========================================================================

P13_OLD = '''app.clientside_callback(
    """
    function(tab_value) {
        var tabs = ['tab-content-ops', 'tab-content-hist', 'tab-content-analytics',
                    'tab-content-coins', 'tab-content-controls'];
        var values = ['tab-ops', 'tab-hist', 'tab-analytics', 'tab-coins', 'tab-controls'];
        var styles = [];
        for (var i = 0; i < tabs.length; i++) {
            if (values[i] === tab_value) {
                styles.push({'padding': '16px', 'display': 'block'});
            } else {
                styles.push({'padding': '16px', 'display': 'none'});
            }
        }
        return styles;
    }
    """,
    [Output('tab-content-ops',       'style'),
     Output('tab-content-hist',      'style'),
     Output('tab-content-analytics', 'style'),
     Output('tab-content-coins',     'style'),
     Output('tab-content-controls',  'style')],
    Input('main-tabs', 'value'),
)'''

P13_NEW = '''app.clientside_callback(
    """
    function(tab_value) {
        var tabs = ['tab-content-ops', 'tab-content-terminal', 'tab-content-controls',
                    'tab-content-hist', 'tab-content-analytics', 'tab-content-coins'];
        var values = ['tab-ops', 'tab-terminal', 'tab-controls',
                      'tab-hist', 'tab-analytics', 'tab-coins'];
        var styles = [];
        for (var i = 0; i < tabs.length; i++) {
            if (values[i] === tab_value) {
                styles.push({'padding': '16px', 'display': 'block'});
            } else {
                styles.push({'padding': '16px', 'display': 'none'});
            }
        }
        return styles;
    }
    """,
    [Output('tab-content-ops',       'style'),
     Output('tab-content-terminal',  'style'),
     Output('tab-content-controls',  'style'),
     Output('tab-content-hist',      'style'),
     Output('tab-content-analytics', 'style'),
     Output('tab-content-coins',     'style')],
    Input('main-tabs', 'value'),
)'''


# ===========================================================================
# P14: CB-T1, CB-T2, CB-T3 (bot terminal callbacks) before entry point
# ===========================================================================

P14_OLD = '''# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------'''

P14_NEW = '''# ---------------------------------------------------------------------------
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
    return "Stop failed", False, False


# ---------------------------------------------------------------------------
# CB-T3: Poll bot running status every 5s
# ---------------------------------------------------------------------------

@callback(
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
    return "Offline", False, True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------'''


# ===========================================================================
# Main
# ===========================================================================

def main():
    """Apply all patches to v1-3 and write v1-4."""
    print("=" * 60)
    print("Build: BingX Live Dashboard v1-4")
    print("=" * 60)

    if not DASH_IN.exists():
        print("FAIL: source not found: " + str(DASH_IN))
        sys.exit(1)

    # Guard: back up existing v1-4 rather than silently overwriting
    if DASH_OUT.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = DASH_OUT.with_suffix("." + ts + ".bak.py")
        shutil.copy2(DASH_OUT, bak)
        print("  Backup existing v1-4: " + str(bak))

    text = read(DASH_IN)
    print("Read: " + str(DASH_IN) + " (" + str(len(text)) + " chars)")
    print()

    # Apply patches in dependency order
    print("Applying patches...")
    text = safe_replace(text, P1_OLD,   P1_NEW,   "P1-docstring-title")
    text = safe_replace(text, P2_OLD,   P2_NEW,   "P2-docstring-tabs")
    text = safe_replace(text, P3_OLD,   P3_NEW,   "P3-docstring-run")
    text = safe_replace(text, P3B_OLD,  P3B_NEW,  "P3b-docstring-gunicorn")
    text = safe_replace(text, P4_OLD,   P4_NEW,   "P4-import-subprocess")
    text = safe_replace(text, P5_OLD,   P5_NEW,   "P5-bot-pid-path")
    text = safe_replace(text, P6_OLD,   P6_NEW,   "P6-bot-helpers")
    text = safe_replace(text, P7_OLD,   P7_NEW,   "P7-live-trades-tab")
    text = safe_replace(text, P8_OLD,   P8_NEW,   "P8-bot-terminal-tab")
    text = safe_replace(text, P9_OLD,   P9_NEW,   "P9-strategy-params-tab")
    text = safe_replace(text, P10_OLD,  P10_NEW,  "P10-app-title")
    text = safe_replace(text, P11_OLD,  P11_NEW,  "P11-tab-list")
    text = safe_replace(text, P12_OLD,  P12_NEW,  "P12-tab-content-divs")
    text = safe_replace(text, P13_OLD,  P13_NEW,  "P13-clientside-cb")
    text = safe_replace(text, P14_OLD,  P14_NEW,  "P14-terminal-callbacks")

    print()
    write(DASH_OUT, text)
    print("Wrote: " + str(DASH_OUT) + " (" + str(len(text)) + " chars)")
    print()
    compile_check(DASH_OUT, "bingx-live-dashboard-v1-4.py")

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
        print("  1. Start dashboard:")
        print('     python "' + str(DASH_OUT) + '"')
        print("  2. Open Bot Terminal tab -> Start Bot")
        print("  3. Watch Activity Log for startup messages")


if __name__ == "__main__":
    main()
