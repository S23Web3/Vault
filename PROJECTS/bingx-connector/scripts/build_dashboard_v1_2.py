"""
build_dashboard_v1_2.py

Build script for BingX Live Dashboard v1-2.
Reads v1-1, applies 8 fixes (dark CSS, date pickers, tab visibility, timing,
professional analytics, chart cleanup), writes v1-2 + updated CSS + updated tests.

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python scripts/build_dashboard_v1_2.py

Then test:
    python scripts/test_dashboard.py

Then run:
    python bingx-live-dashboard-v1-2.py
"""

import os
import py_compile
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector")
V1_1 = BASE / "bingx-live-dashboard-v1-1.py"
V1_2 = BASE / "bingx-live-dashboard-v1-2.py"
CSS_PATH = BASE / "assets" / "dashboard.css"
TEST_PATH = BASE / "scripts" / "test_dashboard.py"

ERRORS = []
WRITES = []


def report(label, ok, detail=""):
    """Report pass/fail for a build step."""
    status = "OK" if ok else "FAIL"
    msg = "  {:<6} {}".format(status, label)
    if not ok and detail:
        msg += " -- " + detail
    print(msg)
    if not ok:
        ERRORS.append(label)


def backup_if_exists(path):
    """Create timestamped backup if file exists."""
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.parent / "{}.{}.bak".format(path.stem, ts)
        shutil.copy2(path, bak)
        print("  Backup: {}".format(bak))


def write_file(path, content, label):
    """Write file content and record it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    WRITES.append(str(path))
    report("wrote {}".format(label), path.exists())


def find_line(lines, text, start=0):
    """Find first line index containing text, starting from start."""
    for i in range(start, len(lines)):
        if text in lines[i]:
            return i
    return None


def find_section_start(lines, header_text, start=0):
    """Find the '# ---' line index that starts a section containing header_text."""
    idx = find_line(lines, header_text, start)
    if idx is None:
        return None
    # Back up to the preceding '# ---' separator line
    if idx > 0 and lines[idx - 1].strip().startswith("# ---"):
        return idx - 1
    return idx


# ===================================================================
# NEW CONTENT: compute_metrics (ANALYTICS-1)
# ===================================================================

NEW_COMPUTE_METRICS = '''\
def compute_metrics(df: pd.DataFrame) -> dict:
    """Compute professional trading metrics from closed trades DataFrame."""
    empty = {
        "total": 0, "win_rate": 0.0, "profit_factor": 0.0,
        "avg_win": 0.0, "avg_loss": 0.0, "expectancy": 0.0,
        "max_dd": 0.0, "max_dd_pct": 0.0, "gross_pnl": 0.0,
        "net_pnl": 0.0, "sharpe": 0.0,
        "sl_hit_pct": 0.0, "tp_hit_pct": 0.0,
        "avg_win_loss_ratio": 0.0,
        "be_hit_count": "N/A", "be_hit_pct": "N/A",
        "lsg_pct": "N/A",
    }
    if df.empty or "pnl_net" not in df.columns:
        return empty

    total = len(df)
    wins = int((df["pnl_net"] > 0).sum())
    losses = total - wins
    win_rate = round(wins / total * 100, 1) if total > 0 else 0.0
    gross_wins = float(df[df.pnl_net > 0].pnl_net.sum())
    gross_losses = float(abs(df[df.pnl_net <= 0].pnl_net.sum()))
    profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else float('inf')
    avg_win = round(float(df[df.pnl_net > 0].pnl_net.mean()), 4) if wins > 0 else 0.0
    avg_loss = round(float(df[df.pnl_net <= 0].pnl_net.mean()), 4) if losses > 0 else 0.0
    expectancy = round((win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss), 4)
    net_pnl = round(gross_wins - gross_losses, 4)

    # Avg Win/Loss ratio
    avg_win_loss_ratio = round(avg_win / abs(avg_loss), 2) if avg_loss != 0 else float('inf')

    # Max drawdown $ and %
    cum = df.sort_values("timestamp").pnl_net.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    max_dd = round(float(dd.min()), 4) if len(cum) > 0 else 0.0
    max_dd_pct = 0.0
    if len(cum) > 0:
        dd_idx = dd.idxmin()
        peak_at_dd = peak.loc[dd_idx]
        if peak_at_dd > 0:
            max_dd_pct = round(float(dd.loc[dd_idx] / peak_at_dd * 100), 2)

    # Sharpe ratio (annualized from daily PnL)
    sharpe = 0.0
    if "timestamp" in df.columns:
        df_copy = df.copy()
        df_copy["date"] = df_copy["timestamp"].dt.date
        daily_pnl = df_copy.groupby("date")["pnl_net"].sum()
        if len(daily_pnl) >= 2:
            mean_daily = float(daily_pnl.mean())
            std_daily = float(daily_pnl.std())
            if std_daily > 0:
                sharpe = round(mean_daily / std_daily * math.sqrt(365), 2)

    # Exit reason percentages
    sl_hit_pct = 0.0
    tp_hit_pct = 0.0
    if "exit_reason" in df.columns and total > 0:
        sl_hit_pct = round((df.exit_reason == "SL_HIT").sum() / total * 100, 1)
        tp_hit_pct = round((df.exit_reason == "TP_HIT").sum() / total * 100, 1)

    # BE Hit and LSG -- placeholder until bot tracks these columns
    be_hit_count = "N/A"
    be_hit_pct = "N/A"
    lsg_pct = "N/A"
    if "be_raised" in df.columns:
        be_count = int(df["be_raised"].sum())
        be_hit_count = be_count
        be_hit_pct = round(be_count / total * 100, 1) if total > 0 else 0.0
    if "saw_green" in df.columns:
        losing = df[df.pnl_net <= 0]
        if len(losing) > 0:
            lsg_pct = round(losing["saw_green"].sum() / len(losing) * 100, 1)

    return {
        "total": total,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_win_loss_ratio": avg_win_loss_ratio,
        "expectancy": expectancy,
        "max_dd": max_dd,
        "max_dd_pct": max_dd_pct,
        "net_pnl": net_pnl,
        "gross_pnl": net_pnl,
        "sharpe": sharpe,
        "sl_hit_pct": sl_hit_pct,
        "tp_hit_pct": tp_hit_pct,
        "be_hit_count": be_hit_count,
        "be_hit_pct": be_hit_pct,
        "lsg_pct": lsg_pct,
    }'''


# ===================================================================
# NEW CONTENT: make_history_tab (FIX-3)
# ===================================================================

NEW_MAKE_HISTORY_TAB = '''\
def make_history_tab() -> html.Div:
    """Build layout for History tab -- filterable closed trades grid."""
    return html.Div([
        html.Div([
            dcc.DatePickerRange(
                id='hist-date-range',
                display_format='YYYY-MM-DD',
                start_date_placeholder_text='Start date',
                end_date_placeholder_text='End date',
                style={'marginRight': '12px'},
            ),
            dcc.Dropdown(id='hist-dir-filter', options=['LONG', 'SHORT'],
                         placeholder='Direction', clearable=True, style={'width': '120px'}),
            dcc.Dropdown(id='hist-grade-filter', options=['A', 'B', 'C'],
                         placeholder='Grade', clearable=True, style={'width': '100px'}),
            dcc.Dropdown(id='hist-exit-filter',
                         options=['SL_HIT', 'TP_HIT', 'EXIT_UNKNOWN', 'SL_HIT_ASSUMED'],
                         placeholder='Exit Reason', clearable=True, style={'width': '160px'}),
        ], style={'display': 'flex', 'gap': '12px', 'alignItems': 'center',
                  'marginBottom': '12px'}),
        dag.AgGrid(id='history-grid', columnDefs=HISTORY_COLUMNS, rowData=[],
                   defaultColDef={'sortable': True, 'filter': True, 'resizable': True},
                   dashGridOptions={'pagination': True, 'paginationPageSize': 50},
                   className='ag-theme-alpine-dark', style={'height': '500px'}),
        html.Div(id='history-summary', style={'color': COLORS['muted'], 'marginTop': '8px'}),
    ])'''


# ===================================================================
# NEW CONTENT: make_analytics_tab (FIX-3 + ANALYTICS-3)
# ===================================================================

NEW_MAKE_ANALYTICS_TAB = '''\
def make_analytics_tab() -> html.Div:
    """Build layout for Analytics tab -- metrics, charts, grade comparison."""
    return html.Div([
        html.Div([
            html.Label("Date Range:", style={'color': COLORS['muted'], 'marginRight': '8px'}),
            dcc.DatePickerRange(
                id='analytics-date-range',
                display_format='YYYY-MM-DD',
                start_date_placeholder_text='Start date',
                end_date_placeholder_text='End date',
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
        html.Div(id='analytics-metric-cards',
                 style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap',
                        'marginBottom': '16px'}),
        html.Div([
            dcc.Graph(id='equity-chart', style={'flex': '1'},
                      config={'displayModeBar': False}),
            dcc.Graph(id='drawdown-chart', style={'flex': '1'},
                      config={'displayModeBar': False}),
        ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '16px'}),
        html.Div([
            dcc.Graph(id='exit-reason-chart', style={'flex': '1'},
                      config={'displayModeBar': False}),
            dcc.Graph(id='daily-pnl-chart', style={'flex': '1'},
                      config={'displayModeBar': False}),
        ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '16px'}),
        html.H4("Grade A vs Grade B"),
        html.Div(id='grade-comparison-table'),
    ])'''


# ===================================================================
# NEW CONTENT: App init + layout (FIX-4)
# ===================================================================

NEW_APP_LAYOUT = '''\
# ---------------------------------------------------------------------------
# Dash App
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,  # Still needed -- CB-5 creates action buttons dynamically
    title='BingX Live Dashboard v1-2',
)
server = app.server  # Expose Flask server for gunicorn

app.layout = html.Div([
    # 60s auto-refresh interval
    dcc.Interval(id='refresh-interval', interval=60_000, n_intervals=0),

    # Data stores -- JSON strings, refreshed by CB-1
    dcc.Store(id='store-state',  storage_type='memory'),
    dcc.Store(id='store-trades', storage_type='memory'),
    dcc.Store(id='store-config', storage_type='memory'),

    # Status bar -- always visible
    html.Div(id='status-bar'),

    # Tab navigation
    dcc.Tabs(id='main-tabs', value='tab-ops', children=[
        dcc.Tab(label='Operational',  value='tab-ops'),
        dcc.Tab(label='History',      value='tab-hist'),
        dcc.Tab(label='Analytics',    value='tab-analytics'),
        dcc.Tab(label='Coin Summary', value='tab-coins'),
        dcc.Tab(label='Bot Controls', value='tab-controls'),
    ]),

    # ALL tab content rendered at startup -- visibility toggled by clientside callback
    html.Div(id='tab-content-ops',       children=make_operational_tab(),
             style={'padding': '16px', 'display': 'block'}),
    html.Div(id='tab-content-hist',      children=make_history_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-analytics', children=make_analytics_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-coins',     children=make_coin_summary_tab(),
             style={'padding': '16px', 'display': 'none'}),
    html.Div(id='tab-content-controls',  children=make_bot_controls_tab(),
             style={'padding': '16px', 'display': 'none'}),
], style={'background': COLORS['bg'], 'minHeight': '100vh'})'''


# ===================================================================
# NEW CONTENT: CB-1 with timing (FIX-5) + CB-2 clientside (FIX-4)
# ===================================================================

NEW_CB1_AND_CB2 = '''\
# ---------------------------------------------------------------------------
# CB-1: Data Loader -- fires on each interval tick AND on page load
# ---------------------------------------------------------------------------

@callback(
    Output('store-state',  'data'),
    Output('store-trades', 'data'),
    Output('store-config', 'data'),
    Input('refresh-interval', 'n_intervals'),
    prevent_initial_call=False,  # MUST fire on load to populate stores before tabs render
)
def load_all_data(n_intervals):
    """Load state.json, trades.csv, config.yaml into stores on each interval tick."""
    try:
        t0 = time.time()
        state_data = json.dumps(load_state())
        t_state = time.time()

        trades_df = load_trades()
        trades_data = trades_df.to_json(orient='split', date_format='iso') if not trades_df.empty else ""
        t_trades = time.time()

        config_data = json.dumps(load_config())
        t_config = time.time()

        LOG.debug("Data loaded: %d positions, %d trades | timing: state=%.3fs trades=%.3fs config=%.3fs total=%.3fs",
                  len(json.loads(state_data).get("open_positions", {})),
                  len(trades_df),
                  t_state - t0, t_trades - t_state, t_config - t_trades, t_config - t0)
        return state_data, trades_data, config_data
    except Exception as e:
        LOG.error("Data load error: %s", e, exc_info=True)
        return no_update, no_update, no_update  # Skip update -- nothing changed


# ---------------------------------------------------------------------------
# CB-2 (REPLACED): Clientside Tab Visibility Toggle
# ---------------------------------------------------------------------------

app.clientside_callback(
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


# ===================================================================
# NEW CONTENT: CB-8 History Grid (FIX-3)
# ===================================================================

NEW_CB8 = '''\
# ---------------------------------------------------------------------------
# CB-8: History Grid
# ---------------------------------------------------------------------------

@callback(
    Output('history-grid', 'rowData'),
    Output('history-summary', 'children'),
    Input('hist-date-range', 'start_date'),
    Input('hist-date-range', 'end_date'),
    Input('hist-dir-filter', 'value'),
    Input('hist-grade-filter', 'value'),
    Input('hist-exit-filter', 'value'),
    Input('store-trades', 'data'),
    prevent_initial_call=True,  # Do not fire on page load -- stores not yet populated
)
def update_history_grid(start_date, end_date, dir_filter, grade_filter, exit_filter, trades_json):
    """Filter and render closed trades into history ag-grid."""
    try:
        if not trades_json:
            return [], "No trade data"

        df = pd.read_json(trades_json, orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")

        # Apply date range filter
        if start_date:
            start_dt = pd.to_datetime(start_date, utc=True)
            df = df[df["timestamp"] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)
            df = df[df["timestamp"] < end_dt]

        if dir_filter:
            df = df[df.direction == dir_filter]
        if grade_filter:
            df = df[df.grade == grade_filter]
        if exit_filter:
            df = df[df.exit_reason == exit_filter]

        if df.empty:
            return [], "No trades match filters"

        # Add display columns
        df["Date"] = df["timestamp"].dt.strftime("%m-%d %H:%M")
        df["Duration"] = df.apply(
            lambda r: fmt_duration(r["entry_time"], r["timestamp"]), axis=1)
        df["Notional"] = pd.to_numeric(df.get("notional_usd", pd.Series(dtype=float)),
                                       errors='coerce')

        # Rename for display
        df = df.rename(columns={
            "symbol": "Symbol", "direction": "Dir", "grade": "Grade",
            "entry_price": "Entry", "exit_price": "Exit",
            "exit_reason": "Exit Reason", "pnl_net": "Net PnL",
        })

        display_cols = ["Date", "Symbol", "Dir", "Grade", "Entry", "Exit",
                        "Exit Reason", "Net PnL", "Duration", "Notional"]
        # Only include columns that exist
        display_cols = [c for c in display_cols if c in df.columns]

        total_pnl = round(float(df["Net PnL"].sum()), 4)
        pnl_color = COLORS['green'] if total_pnl >= 0 else COLORS['red']
        summary = html.Span(
            "{} trades | Total PnL: {:+.4f}".format(len(df), total_pnl),
            style={'color': pnl_color}
        )

        return df[display_cols].to_dict('records'), summary
    except Exception as e:
        LOG.error("Error in history grid: %s", e, exc_info=True)
        return [], html.Span("Error: " + str(e), style={'color': COLORS['red']})'''


# ===================================================================
# NEW CONTENT: CB-9 Analytics (FIX-3 + ANALYTICS-1)
# ===================================================================

NEW_CB9 = '''\
# ---------------------------------------------------------------------------
# CB-9: Analytics Update
# ---------------------------------------------------------------------------

@callback(
    Output('analytics-metric-cards', 'children'),
    Output('equity-chart',           'figure'),
    Output('drawdown-chart',         'figure'),
    Output('exit-reason-chart',      'figure'),
    Output('daily-pnl-chart',        'figure'),
    Output('grade-comparison-table', 'children'),
    Input('analytics-date-range',    'start_date'),
    Input('analytics-date-range',    'end_date'),
    Input('store-trades',            'data'),
    prevent_initial_call=True,  # Do not fire on page load -- stores not yet populated
)
def update_analytics(start_date, end_date, trades_json):
    """Compute all analytics from trades store and render all analytics tab components."""
    try:
        empty_fig = _empty_figure()
        empty_cards = html.Div("No trade data loaded.", style={'color': COLORS['muted']})
        empty_table = html.Div("No grade data.", style={'color': COLORS['muted']})

        if not trades_json:
            return empty_cards, empty_fig, empty_fig, empty_fig, empty_fig, empty_table

        df = pd.read_json(trades_json, orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

        # Apply date range filter
        if start_date:
            start_dt = pd.to_datetime(start_date, utc=True)
            df = df[df["timestamp"] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)
            df = df[df["timestamp"] < end_dt]

        if df.empty:
            return empty_cards, empty_fig, empty_fig, empty_fig, empty_fig, empty_table

        metrics = compute_metrics(df)

        # Build metric cards -- ANALYTICS-1 professional layout
        pf_str = "{:.2f}".format(metrics['profit_factor']) if metrics['profit_factor'] != float('inf') else "INF"
        wlr_str = "{:.2f}".format(metrics['avg_win_loss_ratio']) if metrics['avg_win_loss_ratio'] != float('inf') else "INF"
        be_str = str(metrics['be_hit_count']) if metrics['be_hit_count'] != "N/A" else "N/A"
        be_pct_str = "{:.1f}%".format(metrics['be_hit_pct']) if metrics['be_hit_pct'] != "N/A" else "N/A"
        lsg_str = "{:.1f}%".format(metrics['lsg_pct']) if metrics['lsg_pct'] != "N/A" else "N/A"

        cards = html.Div([
            build_metric_card("Total Trades", str(metrics["total"])),
            build_metric_card("Net PnL", "${:+.4f}".format(metrics['net_pnl']),
                              COLORS['green'] if metrics['net_pnl'] >= 0 else COLORS['red']),
            build_metric_card("Win Rate", "{:.1f}%".format(metrics['win_rate']),
                              COLORS['green'] if metrics['win_rate'] >= 50 else COLORS['red']),
            build_metric_card("Profit Factor", pf_str,
                              COLORS['green'] if metrics['profit_factor'] >= 1 else COLORS['red']),
            build_metric_card("Sharpe", str(metrics['sharpe']),
                              COLORS['green'] if metrics['sharpe'] > 0 else COLORS['red']),
            build_metric_card("Max DD $", "${:.4f}".format(metrics['max_dd']), COLORS['red']),
            build_metric_card("Max DD %", "{:.2f}%".format(metrics['max_dd_pct']), COLORS['red']),
            build_metric_card("Expectancy", "${:+.4f}".format(metrics['expectancy']),
                              COLORS['green'] if metrics['expectancy'] >= 0 else COLORS['red']),
            build_metric_card("W/L Ratio", wlr_str,
                              COLORS['green'] if metrics['avg_win_loss_ratio'] >= 1 else COLORS['red']),
            build_metric_card("SL Hit %", "{:.1f}%".format(metrics['sl_hit_pct']), COLORS['red']),
            build_metric_card("TP Hit %", "{:.1f}%".format(metrics['tp_hit_pct']), COLORS['green']),
            build_metric_card("BE Hits", be_str, COLORS['muted']),
            build_metric_card("LSG %", lsg_str, COLORS['muted']),
        ], style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'})

        # Build charts
        equity_fig = build_equity_figure(df)
        dd_fig = build_drawdown_figure(df)
        exit_fig = build_exit_reason_figure(df)
        daily_fig = build_daily_pnl_figure(df)

        # Grade comparison table
        grade_rows = []
        if "grade" in df.columns:
            for grade, grp in df.groupby("grade"):
                gm = compute_metrics(grp)
                grade_rows.append({
                    "Grade": grade,
                    "Trades": gm["total"],
                    "Win Rate %": gm["win_rate"],
                    "Net PnL": gm["gross_pnl"],
                    "Profit Factor": gm["profit_factor"] if gm["profit_factor"] != float('inf') else 999,
                    "Expectancy": gm["expectancy"],
                    "Sharpe": gm["sharpe"],
                })

        if grade_rows:
            grade_cols = [{'field': k} for k in grade_rows[0].keys()]
            grade_table = dag.AgGrid(
                columnDefs=grade_cols, rowData=grade_rows,
                defaultColDef={'sortable': True},
                className='ag-theme-alpine-dark',
                style={'height': '150px'},
            )
        else:
            grade_table = empty_table

        return cards, equity_fig, dd_fig, exit_fig, daily_fig, grade_table
    except Exception as e:
        LOG.error("Error in analytics: %s", e, exc_info=True)
        empty_fig = _empty_figure()
        return (html.Div("Error: " + str(e), style={'color': COLORS['red']}),
                empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("Error: " + str(e), style={'color': COLORS['red']}))'''


# ===================================================================
# CSS CONTENT (FIX-1 + FIX-2)
# ===================================================================

CSS_CONTENT = """\
/* === Base === */
body {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Consolas', 'Monaco', monospace;
    margin: 0;
}

/* === AG Grid row highlighting === */
.row-long  { background-color: rgba(63, 185, 80,  0.05) !important; }
.row-short { background-color: rgba(248, 81, 73, 0.05) !important; }

/* === Warning banner === */
.warning-banner {
    background-color: rgba(248, 81, 73, 0.10);
    border: 1px solid #f85149;
    padding: 12px 16px;
    border-radius: 4px;
    color: #c9d1d9;
}

/* === Dash tab styling === */
.dash-tabs { background-color: #0d1117; }
.dash-tab  { background-color: #161b22 !important; color: #8b949e !important;
             border: 1px solid #21262d !important; }
.dash-tab--selected { background-color: #0d1117 !important; color: #c9d1d9 !important;
                      border-bottom: 2px solid #58a6ff !important; }

/* === Loading spinner dark background === */
._dash-loading { background-color: rgba(13, 17, 23, 0.8); }

/* === FIX-1: Dark theme for form inputs === */
input[type="number"],
input[type="text"],
input[type="search"],
textarea {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 4px;
    padding: 6px 8px;
}

input[type="number"]:focus,
input[type="text"]:focus {
    border-color: #58a6ff !important;
    outline: none;
}

/* Dash radio items + checklists */
.dash-radio label,
.dash-checklist label {
    color: #c9d1d9 !important;
}

/* Dash Dropdown (React-Select internals) */
.Select-control {
    background-color: #161b22 !important;
    border-color: #30363d !important;
}
.Select-value-label,
.Select-placeholder,
.Select-input > input {
    color: #c9d1d9 !important;
}
.Select-menu-outer {
    background-color: #161b22 !important;
    border-color: #30363d !important;
}
.Select-option {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
}
.Select-option.is-focused {
    background-color: #21262d !important;
}
.Select-arrow {
    border-color: #c9d1d9 transparent transparent !important;
}

/* DatePickerRange dark theme */
.DateRangePickerInput,
.DateInput_input {
    background-color: #161b22 !important;
    color: #c9d1d9 !important;
    border-color: #30363d !important;
}
.CalendarDay__default {
    background: #161b22; color: #c9d1d9; border: 1px solid #21262d;
}
.CalendarDay__selected {
    background: #58a6ff; color: #0d1117;
}
.DayPickerNavigation_button__default {
    background: #21262d; border: 1px solid #30363d;
}
.CalendarMonth_caption { color: #c9d1d9; }

/* === FIX-2: AG Grid dark backgrounds === */
.ag-root-wrapper {
    background-color: #0d1117 !important;
}
.ag-overlay-no-rows-wrapper {
    background-color: #0d1117 !important;
    color: #8b949e !important;
}
.ag-header {
    background-color: #161b22 !important;
}
"""


# ===================================================================
# TEST CONTENT (updated for v1-2)
# ===================================================================

TEST_CONTENT = '''\
"""
test_dashboard.py

Audit and unit-test script for bingx-live-dashboard-v1-2.py.
Tests: py_compile, data loaders (mock), builders, validators, layout structure.
Run: python scripts/test_dashboard.py
"""

import sys
import json
import os
import tempfile
import py_compile
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

ERRORS = []
BASE = Path(__file__).parent.parent  # PROJECTS/bingx-connector/


def check(label, cond, detail=""):
    """Record pass or fail for a test assertion."""
    if cond:
        print("  PASS  {}".format(label))
    else:
        msg = "  FAIL  {}".format(label) + (" -- {}".format(detail) if detail else "")
        print(msg)
        ERRORS.append(label)


# -----------------------------------------------------------------------
# 1. py_compile -- both files
# -----------------------------------------------------------------------
print("\\n[1] py_compile")

for fname in ["bingx-live-dashboard-v1-2.py", "assets/dashboard.css"]:
    path = BASE / fname
    check("file exists: {}".format(fname), path.exists(), "not found at {}".format(path))

try:
    py_compile.compile(str(BASE / "bingx-live-dashboard-v1-2.py"), doraise=True)
    check("py_compile bingx-live-dashboard-v1-2.py", True)
except py_compile.PyCompileError as e:
    check("py_compile bingx-live-dashboard-v1-2.py", False, str(e))

try:
    py_compile.compile(str(Path(__file__)), doraise=True)
    check("py_compile test_dashboard.py", True)
except py_compile.PyCompileError as e:
    check("py_compile test_dashboard.py", False, str(e))


# -----------------------------------------------------------------------
# 2. Import dashboard module (no Dash server starts -- just import)
# -----------------------------------------------------------------------
print("\\n[2] Import dashboard module")
sys.path.insert(0, str(BASE))
try:
    # Hyphenated filename requires importlib
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "bingx_live_dashboard_v1_2",
        str(BASE / "bingx-live-dashboard-v1-2.py"),
    )
    dash_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(dash_mod)
    check("import dashboard module", True)
except Exception as e:
    check("import dashboard module", False, str(e))
    print("Cannot continue without import. Aborting.")
    sys.exit(1)


# -----------------------------------------------------------------------
# 3. Data loaders -- mock files
# -----------------------------------------------------------------------
print("\\n[3] Data loaders with mock files")

# 3a. load_state -- missing file
original_state_path = dash_mod.STATE_PATH
dash_mod.STATE_PATH = BASE / "nonexistent_state.json"
result = dash_mod.load_state()
check("load_state missing file returns defaults", isinstance(result, dict))
check("load_state has open_positions key", "open_positions" in result)
check("load_state has halt_flag key", "halt_flag" in result)
dash_mod.STATE_PATH = original_state_path

# 3b. load_state -- valid file
tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
json.dump({
    "open_positions": {"X_LONG": {"symbol": "X", "direction": "LONG",
                                   "entry_price": 1.0, "sl_price": 0.9,
                                   "tp_price": None, "quantity": 10,
                                   "notional_usd": 50, "grade": "A",
                                   "entry_time": "2026-02-28T10:00:00+00:00",
                                   "order_id": "123", "atr_at_entry": 0.05,
                                   "be_raised": False}},
    "daily_pnl": -1.5,
    "daily_trades": 2,
    "halt_flag": False,
    "session_start": "2026-02-28T08:00:00+00:00",
}, tmp)
tmp.close()
dash_mod.STATE_PATH = Path(tmp.name)
result = dash_mod.load_state()
check("load_state valid file parsed", result["daily_pnl"] == -1.5)
check("load_state open_positions populated", len(result["open_positions"]) == 1)
dash_mod.STATE_PATH = original_state_path
os.unlink(tmp.name)

# 3c. load_config -- missing file
original_config_path = dash_mod.CONFIG_PATH
dash_mod.CONFIG_PATH = BASE / "nonexistent_config.yaml"
result = dash_mod.load_config()
check("load_config missing file returns empty dict", result == {})
dash_mod.CONFIG_PATH = original_config_path

# 3d. load_trades -- missing file
original_trades_path = dash_mod.TRADES_PATH
dash_mod.TRADES_PATH = BASE / "nonexistent_trades.csv"
result = dash_mod.load_trades()
check("load_trades missing file returns empty DataFrame", result.empty)
dash_mod.TRADES_PATH = original_trades_path

# 3e. load_trades -- valid file
tmp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
tmp_csv.write(
    "timestamp,symbol,direction,grade,entry_price,exit_price,exit_reason,"
    "pnl_net,quantity,notional_usd,entry_time,order_id\\n"
    "2026-02-28T10:00:00+00:00,SKR-USDT,LONG,A,0.5,0.55,TP_HIT,"
    "0.025,100,50,2026-02-28T09:00:00+00:00,111\\n"
    "2026-02-28T11:00:00+00:00,SKR-USDT,SHORT,B,0.55,0.58,SL_HIT,"
    "-0.015,100,50,2026-02-28T10:30:00+00:00,222\\n"
)
tmp_csv.close()
dash_mod.TRADES_PATH = Path(tmp_csv.name)
result = dash_mod.load_trades()
check("load_trades valid file has 2 rows", len(result) == 2)
check("load_trades sorted newest first",
      result.iloc[0]["symbol"] == "SKR-USDT")
check("load_trades pnl_net is numeric",
      pd.api.types.is_numeric_dtype(result["pnl_net"]))


# -----------------------------------------------------------------------
# 4. Builder functions
# -----------------------------------------------------------------------
print("\\n[4] Builder functions")

# 4a. fmt_duration
check("fmt_duration returns em-dash for None start",
      dash_mod.fmt_duration(None) == "\\u2014")
now = datetime.now(timezone.utc)
start = now - timedelta(hours=2, minutes=15)
result = dash_mod.fmt_duration(start, now)
check("fmt_duration 2h 15m formatted correctly", result == "2h 15m")
start = now - timedelta(minutes=45)
result = dash_mod.fmt_duration(start, now)
check("fmt_duration 45m formatted correctly", result == "45m")

# 4b. build_positions_df
mock_state = {
    "open_positions": {
        "SKR-USDT_LONG": {
            "symbol": "SKR-USDT", "direction": "LONG",
            "entry_price": 0.5, "sl_price": 0.46,
            "tp_price": None, "quantity": 100,
            "notional_usd": 50.0, "grade": "A",
            "entry_time": "2026-02-28T10:00:00+00:00",
            "order_id": "111", "atr_at_entry": 0.02,
            "be_raised": False
        }
    }
}
mock_prices = {"SKR-USDT": 0.52}
df = dash_mod.build_positions_df(mock_state, mock_prices)
check("build_positions_df returns DataFrame", isinstance(df, pd.DataFrame))
check("build_positions_df has 1 row", len(df) == 1)
check("build_positions_df has Unreal PnL column", "Unreal PnL" in df.columns)
check("build_positions_df computes positive PnL for LONG gain",
      df.iloc[0]["Unreal PnL"] > 0)
check("build_positions_df has Dist SL % column", "Dist SL %" in df.columns)
check("build_positions_df Dist SL % is float",
      isinstance(df.iloc[0]["Dist SL %"], float))
check("build_positions_df BE Raised is No",
      df.iloc[0]["BE Raised"] == "No")

# 4c. compute_metrics
df_trades = dash_mod.load_trades()  # uses the CSV set above
metrics = dash_mod.compute_metrics(df_trades)
check("compute_metrics returns dict", isinstance(metrics, dict))
check("compute_metrics win_rate key exists", "win_rate" in metrics)
check("compute_metrics total = 2", metrics["total"] == 2)
check("compute_metrics win_rate 50%", metrics["win_rate"] == 50.0)
# v1-2 new metric keys
check("compute_metrics has sharpe key", "sharpe" in metrics)
check("compute_metrics has max_dd_pct key", "max_dd_pct" in metrics)
check("compute_metrics has net_pnl key", "net_pnl" in metrics)
check("compute_metrics has sl_hit_pct key", "sl_hit_pct" in metrics)
check("compute_metrics has tp_hit_pct key", "tp_hit_pct" in metrics)
check("compute_metrics has avg_win_loss_ratio key", "avg_win_loss_ratio" in metrics)
check("compute_metrics has be_hit_count key", "be_hit_count" in metrics)
check("compute_metrics has lsg_pct key", "lsg_pct" in metrics)
check("compute_metrics be_hit_count is N/A (no column)", metrics["be_hit_count"] == "N/A")
check("compute_metrics lsg_pct is N/A (no column)", metrics["lsg_pct"] == "N/A")
check("compute_metrics sl_hit_pct correct", metrics["sl_hit_pct"] == 50.0)
check("compute_metrics tp_hit_pct correct", metrics["tp_hit_pct"] == 50.0)
check("compute_metrics net_pnl correct", metrics["net_pnl"] == round(0.025 - 0.015, 4))
check("compute_metrics gross_pnl alias equals net_pnl", metrics["gross_pnl"] == metrics["net_pnl"])

# 4d. build_coin_summary
records = dash_mod.build_coin_summary(df_trades)
check("build_coin_summary returns list", isinstance(records, list))
check("build_coin_summary 1 coin (SKR-USDT)", len(records) == 1)
check("build_coin_summary WR % present", "WR %" in records[0])
check("build_coin_summary Net PnL correct",
      records[0]["Net PnL"] == round(0.025 - 0.015, 4))


# -----------------------------------------------------------------------
# 5. validate_config_updates
# -----------------------------------------------------------------------
print("\\n[5] validate_config_updates")

valid_updates = {
    "sl_atr_mult": 2.0, "tp_atr_mult": None, "require_stage2": True,
    "rot_level": 80, "allow_a": True, "allow_b": True,
    "max_positions": 8, "max_daily_trades": 50,
    "daily_loss_limit_usd": 15.0, "min_atr_ratio": 0.003,
    "cooldown_bars": 3, "margin_usd": 5.0, "leverage": 10,
}
ok, err = dash_mod.validate_config_updates(valid_updates)
check("validate_config_updates valid inputs pass", ok, err)

bad = dict(valid_updates)
bad["leverage"] = 0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates leverage=0 fails", not ok)

bad = dict(valid_updates)
bad["sl_atr_mult"] = -1.0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates negative sl_atr_mult fails", not ok)

bad = dict(valid_updates)
bad["daily_loss_limit_usd"] = -5.0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates negative loss limit fails", not ok)


# -----------------------------------------------------------------------
# 6. Chart builders -- smoke test (returns go.Figure without crash)
# -----------------------------------------------------------------------
print("\\n[6] Chart builders smoke test")

import plotly.graph_objects as go

fig = dash_mod.build_equity_figure(df_trades)
check("build_equity_figure returns Figure", isinstance(fig, go.Figure))

fig = dash_mod.build_drawdown_figure(df_trades)
check("build_drawdown_figure returns Figure", isinstance(fig, go.Figure))

fig = dash_mod.build_exit_reason_figure(df_trades)
check("build_exit_reason_figure returns Figure", isinstance(fig, go.Figure))

fig = dash_mod.build_daily_pnl_figure(df_trades)
check("build_daily_pnl_figure returns Figure", isinstance(fig, go.Figure))

# Empty DataFrame should not crash
fig = dash_mod.build_equity_figure(pd.DataFrame())
check("build_equity_figure empty df returns Figure", isinstance(fig, go.Figure))


# -----------------------------------------------------------------------
# 7. Layout structure (FIX-4 -- all tabs rendered at startup)
# -----------------------------------------------------------------------
print("\\n[7] Layout structure (FIX-4)")

layout = dash_mod.app.layout


def find_ids(component, found=None):
    """Recursively collect component IDs from layout tree."""
    if found is None:
        found = set()
    if hasattr(component, 'id') and component.id:
        found.add(component.id)
    if hasattr(component, 'children'):
        children = component.children
        if isinstance(children, list):
            for child in children:
                find_ids(child, found)
        elif children is not None:
            find_ids(children, found)
    return found


all_ids = find_ids(layout)
check("layout has tab-content-ops", "tab-content-ops" in all_ids)
check("layout has tab-content-hist", "tab-content-hist" in all_ids)
check("layout has tab-content-analytics", "tab-content-analytics" in all_ids)
check("layout has tab-content-coins", "tab-content-coins" in all_ids)
check("layout has tab-content-controls", "tab-content-controls" in all_ids)
check("layout has positions-grid (always present)", "positions-grid" in all_ids)
check("layout has analytics-date-range", "analytics-date-range" in all_ids)
check("layout has hist-date-range", "hist-date-range" in all_ids)
check("layout does NOT have old tab-content div", "tab-content" not in all_ids)


# -----------------------------------------------------------------------
# Cleanup and report
# -----------------------------------------------------------------------
dash_mod.TRADES_PATH = original_trades_path
os.unlink(tmp_csv.name)

print("\\n" + "=" * 60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print("{} test(s) failed.".format(len(ERRORS)))
    sys.exit(1)
else:
    print("All tests passed.")
    sys.exit(0)
'''


# ===================================================================
# BUILD LOGIC
# ===================================================================

def main():
    """Execute the full build: read v1-1, apply changes, write v1-2 + CSS + test."""
    print("Building BingX Dashboard v1-2...")
    print("=" * 60)

    # --- Pre-checks ---
    if not V1_1.exists():
        print("ERROR: v1-1 not found at {}".format(V1_1))
        sys.exit(1)
    if V1_2.exists():
        print("ERROR: {} already exists. Delete it manually to rebuild.".format(V1_2))
        sys.exit(1)

    # --- Step 1: Read v1-1 ---
    print("\n[Step 1] Read v1-1")
    src = V1_1.read_text(encoding="utf-8")
    report("Read v1-1", True, "{} chars".format(len(src)))

    # --- Step 2: Text replacements (version, import, chart labels) ---
    print("\n[Step 2] Text replacements")

    # Version bump
    count = src.count("BingX Live Dashboard v1-1")
    src = src.replace("BingX Live Dashboard v1-1", "BingX Live Dashboard v1-2")
    report("version bump in text", count > 0, "found {} occurrences".format(count))

    src = src.replace("bingx-live-dashboard-v1-1.py", "bingx-live-dashboard-v1-2.py")
    src = src.replace("bingx_live_dashboard_v1_1:server", "bingx_live_dashboard_v1_2:server")
    report("filename references updated", True)

    # Add import math
    old_import = "import hashlib\n"
    new_import = "import hashlib\nimport math\n"
    if old_import in src:
        src = src.replace(old_import, new_import, 1)
        report("added import math", True)
    else:
        report("added import math", False, "could not find 'import hashlib'")

    # Chart axis labels (ANALYTICS-3)
    chart_replacements = [
        (
            "fig.update_layout(title='Equity Curve', yaxis_title='Net PnL (USDT)', **CHART_LAYOUT)",
            "fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Net PnL (USDT)', **CHART_LAYOUT)",
            "equity chart xaxis_title",
        ),
        (
            "fig.update_layout(title='Drawdown', yaxis_title='Drawdown (USDT)', **CHART_LAYOUT)",
            "fig.update_layout(title='Drawdown', xaxis_title='Date', yaxis_title='Drawdown (USDT)', **CHART_LAYOUT)",
            "drawdown chart xaxis_title",
        ),
        (
            "fig.update_layout(title='Exit Breakdown', **CHART_LAYOUT)",
            "fig.update_layout(title='Exit Breakdown', xaxis_title='Exit Reason', yaxis_title='Count', **CHART_LAYOUT)",
            "exit breakdown axis titles",
        ),
        (
            "fig.update_layout(title='Daily PnL', **CHART_LAYOUT)",
            "fig.update_layout(title='Daily PnL', xaxis_title='Date', yaxis_title='PnL (USDT)', **CHART_LAYOUT)",
            "daily pnl axis titles",
        ),
    ]
    for old, new, label in chart_replacements:
        if old in src:
            src = src.replace(old, new, 1)
            report(label, True)
        else:
            report(label, False, "old string not found")

    # --- Step 3: Line-based section replacements (bottom to top) ---
    print("\n[Step 3] Section replacements (bottom to top)")
    lines = src.split("\n")

    # --- CB-9 ---
    cb9_start = find_section_start(lines, "CB-9: Analytics")
    cb10_start = find_section_start(lines, "CB-10: Coin Summary")
    if cb9_start is not None and cb10_start is not None:
        lines = lines[:cb9_start] + NEW_CB9.split("\n") + ["", ""] + lines[cb10_start:]
        report("replaced CB-9 (analytics + date range)", True)
    else:
        report("replaced CB-9", False, "section boundaries not found")

    # --- CB-8 ---
    cb8_start = find_section_start(lines, "CB-8: History")
    cb9_start = find_section_start(lines, "CB-9: Analytics")  # re-find after CB-9 replacement
    if cb8_start is not None and cb9_start is not None:
        lines = lines[:cb8_start] + NEW_CB8.split("\n") + ["", ""] + lines[cb9_start:]
        report("replaced CB-8 (history + date range)", True)
    else:
        report("replaced CB-8", False, "section boundaries not found")

    # --- CB-1 + CB-2 (replace both sections with new CB-1 + clientside) ---
    cb1_start = find_section_start(lines, "CB-1: Data Loader")
    cb3_start = find_section_start(lines, "CB-3: Status Bar")
    if cb1_start is not None and cb3_start is not None:
        lines = lines[:cb1_start] + NEW_CB1_AND_CB2.split("\n") + ["", ""] + lines[cb3_start:]
        report("replaced CB-1 (timing) + CB-2 (clientside)", True)
    else:
        report("replaced CB-1 + CB-2", False, "section boundaries not found")

    # --- App layout ---
    layout_start = find_section_start(lines, "# Dash App")
    layout_end = find_line(lines, "# ====")  # The "# ===" line before CALLBACKS
    if layout_start is not None and layout_end is not None:
        lines = lines[:layout_start] + NEW_APP_LAYOUT.split("\n") + ["", ""] + lines[layout_end:]
        report("replaced app layout (all tabs visible)", True)
    else:
        report("replaced app layout", False, "section boundaries not found")

    # --- make_analytics_tab ---
    at_start = find_line(lines, "def make_analytics_tab(")
    at_end = find_line(lines, "def make_coin_summary_tab(")
    if at_start is not None and at_end is not None:
        lines = lines[:at_start] + NEW_MAKE_ANALYTICS_TAB.split("\n") + ["", ""] + lines[at_end:]
        report("replaced make_analytics_tab (date picker + displayModeBar)", True)
    else:
        report("replaced make_analytics_tab", False, "function boundaries not found")

    # --- make_history_tab ---
    ht_start = find_line(lines, "def make_history_tab(")
    ht_end = find_line(lines, "def make_analytics_tab(")
    if ht_start is not None and ht_end is not None:
        lines = lines[:ht_start] + NEW_MAKE_HISTORY_TAB.split("\n") + ["", ""] + lines[ht_end:]
        report("replaced make_history_tab (date range picker)", True)
    else:
        report("replaced make_history_tab", False, "function boundaries not found")

    # --- compute_metrics ---
    cm_start = find_line(lines, "def compute_metrics(")
    cm_end = find_line(lines, "def build_coin_summary(")
    if cm_start is not None and cm_end is not None:
        lines = lines[:cm_start] + NEW_COMPUTE_METRICS.split("\n") + ["", ""] + lines[cm_end:]
        report("replaced compute_metrics (professional metrics)", True)
    else:
        report("replaced compute_metrics", False, "function boundaries not found")

    # Rejoin
    v1_2_content = "\n".join(lines)

    # --- Step 4: Write files ---
    print("\n[Step 4] Write files")

    # Dashboard v1-2
    write_file(V1_2, v1_2_content, "bingx-live-dashboard-v1-2.py")

    # CSS (backup old)
    backup_if_exists(CSS_PATH)
    write_file(CSS_PATH, CSS_CONTENT, "assets/dashboard.css")

    # Test (backup old)
    backup_if_exists(TEST_PATH)
    write_file(TEST_PATH, TEST_CONTENT, "scripts/test_dashboard.py")

    # --- Step 5: py_compile ---
    print("\n[Step 5] py_compile")

    for path, label in [(V1_2, "dashboard v1-2"), (TEST_PATH, "test_dashboard")]:
        try:
            py_compile.compile(str(path), doraise=True)
            report("py_compile {}".format(label), True)
        except py_compile.PyCompileError as e:
            report("py_compile {}".format(label), False, str(e))

    # --- Step 6: Summary ---
    print("\n" + "=" * 60)
    print("Files written:")
    for w in WRITES:
        print("  {}".format(w))

    if ERRORS:
        print("\nERRORS:")
        for e in ERRORS:
            print("  {}".format(e))
        print("\n{} error(s). Review and fix before running.".format(len(ERRORS)))
        sys.exit(1)
    else:
        print("\nBuild complete. No errors.")
        print("\nNext steps:")
        print('  1. python scripts/test_dashboard.py')
        print('  2. python bingx-live-dashboard-v1-2.py')
        sys.exit(0)


if __name__ == "__main__":
    main()
