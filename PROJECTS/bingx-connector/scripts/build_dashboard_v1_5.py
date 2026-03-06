"""
Build Phase 3: Dashboard v1.5

Reads bingx-live-dashboard-v1-4.py as base, applies all patches,
writes bingx-live-dashboard-v1-5.py. Does NOT modify v1-4.py.

Patches:
  P3-A: Fix _sign() -- add recvWindow before HMAC (BUG-4)
  P3-B: Remove reduceOnly from CB-6/CB-7/CB-16 (BUG-1b, 3 locations)
  P3-C: Analytics period quick-filter (session/today/7d/all) + session equity curve (BUG-2)
  P3-D: Coin summary syncs with analytics date range (BUG-5)
  P3-E: Status bar -- Exchange Connected indicator separate from Bot Online
  P3-F: TTP stats panel in Analytics tab (BUG-9 visibility)
  P3-G: Trade chart popup (CB-20) for History tab + Live Trades tab
  P3-H: Update docstring/title from v1-4 to v1-5

Run: python scripts/build_dashboard_v1_5.py
"""
import py_compile
import ast
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
SRC    = ROOT / "bingx-live-dashboard-v1-4.py"
DEST   = ROOT / "bingx-live-dashboard-v1-5.py"
ERRORS = []


def verify(path: Path, label: str) -> bool:
    """Syntax-check and AST-parse."""
    try:
        py_compile.compile(str(path), doraise=True)
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        print("  OK: " + label)
        return True
    except (py_compile.PyCompileError, SyntaxError) as e:
        print("  FAIL: " + label + " -- " + str(e))
        ERRORS.append(label)
        return False


def safe_replace(source: str, old: str, new: str, label: str) -> str:
    """Replace old with new exactly once; error if not found."""
    count = source.count(old)
    if count == 0:
        print("  MISSING ANCHOR: " + label)
        ERRORS.append("ANCHOR:" + label)
        return source
    if count > 1:
        print("  AMBIGUOUS (" + str(count) + "x): " + label)
        ERRORS.append("AMBIGUOUS:" + label)
        return source
    print("  PATCH: " + label)
    return source.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Load source
# ---------------------------------------------------------------------------
if not SRC.exists():
    print("ERROR: Source not found: " + str(SRC))
    sys.exit(1)
if DEST.exists():
    print("ERROR: " + DEST.name + " already exists. Delete it first or version it manually.")
    sys.exit(1)

src = SRC.read_text(encoding="utf-8")
print("Loaded: " + SRC.name + " (" + str(len(src)) + " chars)")

# ---------------------------------------------------------------------------
# P3-H: Update docstring + title
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    "BingX Live Dashboard v1-4\n\nPlotly Dash app",
    "BingX Live Dashboard v1-5\n\nPlotly Dash app",
    "P3-H: version string in docstring",
)
src = safe_replace(
    src,
    "title='BingX Live Dashboard v1-4'",
    "title='BingX Live Dashboard v1-5'",
    "P3-H: app title",
)
src = safe_replace(
    src,
    "python bingx-live-dashboard-v1-4.py",
    "python bingx-live-dashboard-v1-5.py",
    "P3-H: run command in docstring",
)

# ---------------------------------------------------------------------------
# P3-A: Fix _sign() -- add recvWindow before HMAC (BUG-4)
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """def _sign(params: dict) -> dict:
    \"\"\"Add timestamp and HMAC-SHA256 signature to params dict.\"\"\"
    params['timestamp'] = int(time.time() * 1000)
    query = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params""",
    """def _sign(params: dict) -> dict:
    \"\"\"Add timestamp, recvWindow, HMAC-SHA256 signature to params dict (BUG-4 fix).\"\"\"
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = '10000'
    query = '&'.join(k + '=' + str(v) for k, v in sorted(params.items()))
    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params""",
    "P3-A: add recvWindow to _sign()",
)

# ---------------------------------------------------------------------------
# P3-B: Remove reduceOnly from CB-6 (Raise BE) -- STOP_MARKET at entry
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': 'SELL' if direction == 'LONG' else 'BUY',
            'positionSide': position_side,
            'type': 'STOP_MARKET',
            'stopPrice': str(entry_price),
            'quantity': str(row.get('Qty', 0)),  # contract qty, NOT notional USD
            'reduceOnly': 'true',
            'workingType': 'MARK_PRICE',
        })
        if 'error' in place_result:
            return html.Span(f"Place failed: {place_result['error']}",
                             style={'color': COLORS['red']})

        # Step 5: Update state.json \u2014 be_raised=True, sl_price=entry""",
    """        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': 'SELL' if direction == 'LONG' else 'BUY',
            'positionSide': position_side,
            'type': 'STOP_MARKET',
            'stopPrice': str(entry_price),
            'quantity': str(row.get('Qty', 0)),  # contract qty, NOT notional USD
            'workingType': 'MARK_PRICE',
        })
        if 'error' in place_result:
            return html.Span(f"Place failed: {place_result['error']}",
                             style={'color': COLORS['red']})

        # Step 5: Update state.json \u2014 be_raised=True, sl_price=entry""",
    "P3-B1: remove reduceOnly from CB-6 Raise BE",
)

# ---------------------------------------------------------------------------
# P3-B: Remove reduceOnly from CB-7 (Move SL)
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': 'SELL' if direction == 'LONG' else 'BUY',
            'positionSide': position_side,
            'type': 'STOP_MARKET',
            'stopPrice': str(new_sl),
            'quantity': str(row.get('Qty', 0)),  # contract qty, NOT notional USD
            'reduceOnly': 'true',
            'workingType': 'MARK_PRICE',
        })
        if 'error' in place_result:
            return html.Span(f"Place failed: {place_result['error']}",
                             style={'color': COLORS['red']})

        # Step 5: Update state.json \u2014 sl_price = new_sl""",
    """        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': 'SELL' if direction == 'LONG' else 'BUY',
            'positionSide': position_side,
            'type': 'STOP_MARKET',
            'stopPrice': str(new_sl),
            'quantity': str(row.get('Qty', 0)),  # contract qty, NOT notional USD
            'workingType': 'MARK_PRICE',
        })
        if 'error' in place_result:
            return html.Span(f"Place failed: {place_result['error']}",
                             style={'color': COLORS['red']})

        # Step 5: Update state.json \u2014 sl_price = new_sl""",
    "P3-B2: remove reduceOnly from CB-7 Move SL",
)

# ---------------------------------------------------------------------------
# P3-B: Remove reduceOnly from CB-16 (Close Market)
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """        # Step 3: Place MARKET close order (reduceOnly)
        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': close_side,
            'positionSide': position_side,
            'type': 'MARKET',
            'quantity': str(qty),
            'reduceOnly': 'true',
        })""",
    """        # Step 3: Place MARKET close order (positionSide scopes it -- no reduceOnly in Hedge mode)
        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
            'symbol': symbol,
            'side': close_side,
            'positionSide': position_side,
            'type': 'MARKET',
            'quantity': str(qty),
        })""",
    "P3-B3: remove reduceOnly from CB-16 Close Market",
)

# ---------------------------------------------------------------------------
# P3-C: Analytics tab -- add period quick-filter radio + session equity (BUG-2)
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """def make_analytics_tab() -> html.Div:
    \"\"\"Build layout for Analytics tab -- metrics, charts, grade comparison.\"\"\"
    return html.Div([
        html.Div([
            html.Label("Date Range:", style={'color': COLORS['muted'], 'marginRight': '8px'}),
            dcc.DatePickerRange(
                id='analytics-date-range',
                display_format='YYYY-MM-DD',
                start_date_placeholder_text='Start date',
                end_date_placeholder_text='End date',
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px', 'maxWidth': '500px'}),
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
        html.Div(id='grade-comparison-table', style={'maxWidth': '800px'}),
    ])""",
    """def make_analytics_tab() -> html.Div:
    \"\"\"Build layout for Analytics tab -- metrics, charts, grade comparison.\"\"\"
    return html.Div([
        # Period quick-filter + date range picker
        html.Div([
            dcc.RadioItems(
                id='analytics-period-filter',
                options=[
                    {'label': ' Session', 'value': 'session'},
                    {'label': ' Today',   'value': 'today'},
                    {'label': ' 7 Days',  'value': '7d'},
                    {'label': ' All',     'value': 'all'},
                ],
                value='session',
                inline=True,
                inputStyle={'marginRight': '4px'},
                labelStyle={'marginRight': '18px', 'color': COLORS['text'], 'cursor': 'pointer'},
            ),
            html.Span("|", style={'color': COLORS['grid'], 'margin': '0 12px'}),
            html.Label("Custom:", style={'color': COLORS['muted'], 'marginRight': '8px'}),
            dcc.DatePickerRange(
                id='analytics-date-range',
                display_format='YYYY-MM-DD',
                start_date_placeholder_text='Start date',
                end_date_placeholder_text='End date',
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px',
                  'flexWrap': 'wrap', 'gap': '8px'}),
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
        html.Div(id='grade-comparison-table', style={'maxWidth': '800px'}),
        html.Hr(style={'borderColor': COLORS['grid'], 'margin': '20px 0'}),
        html.H4("TTP Performance"),
        html.Div(id='ttp-stats-section'),
    ])""",
    "P3-C: analytics tab layout with period filter + TTP stats section",
)

# P3-C: Update CB-9 to consume analytics-period-filter and session_start
src = safe_replace(
    src,
    """@callback(
    Output('analytics-metric-cards', 'children'),
    Output('equity-chart',           'figure'),
    Output('drawdown-chart',         'figure'),
    Output('exit-reason-chart',      'figure'),
    Output('daily-pnl-chart',        'figure'),
    Output('grade-comparison-table', 'children'),
    Input('analytics-date-range',    'start_date'),
    Input('analytics-date-range',    'end_date'),
    Input('store-trades',            'data'),
    Input('store-unrealized',        'data'),
    prevent_initial_call=True,
)
def update_analytics(start_date, end_date, trades_json, unrealized_json):
    \"\"\"Compute all analytics from trades store and render all analytics tab components.\"\"\"
    try:
        empty_fig = _empty_figure()
        empty_cards = html.Div("No trade data loaded.", style={'color': COLORS['muted']})
        empty_table = html.Div("No grade data.", style={'color': COLORS['muted']})

        if not trades_json:
            return empty_cards, empty_fig, empty_fig, empty_fig, empty_fig, empty_table

        df = pd.read_json(io.StringIO(trades_json), orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

        # Apply date range filter
        if start_date:
            start_dt = pd.to_datetime(start_date, utc=True)
            df = df[df["timestamp"] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)
            df = df[df["timestamp"] < end_dt]

        if df.empty:
            return empty_cards, empty_fig, empty_fig, empty_fig, empty_fig, empty_table""",
    """@callback(
    Output('analytics-metric-cards', 'children'),
    Output('equity-chart',           'figure'),
    Output('drawdown-chart',         'figure'),
    Output('exit-reason-chart',      'figure'),
    Output('daily-pnl-chart',        'figure'),
    Output('grade-comparison-table', 'children'),
    Input('analytics-date-range',    'start_date'),
    Input('analytics-date-range',    'end_date'),
    Input('analytics-period-filter', 'value'),
    Input('store-trades',            'data'),
    Input('store-unrealized',        'data'),
    State('store-state',             'data'),
    prevent_initial_call=True,
)
def update_analytics(start_date, end_date, period_filter, trades_json, unrealized_json, state_json):
    \"\"\"Compute all analytics from trades store and render all analytics tab components (v1-5).\"\"\"
    try:
        empty_fig = _empty_figure()
        empty_cards = html.Div("No trade data loaded.", style={'color': COLORS['muted']})
        empty_table = html.Div("No grade data.", style={'color': COLORS['muted']})

        if not trades_json:
            return empty_cards, empty_fig, empty_fig, empty_fig, empty_fig, empty_table

        df = pd.read_json(io.StringIO(trades_json), orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

        # Explicit date range always takes priority over radio filter
        if start_date or end_date:
            if start_date:
                start_dt = pd.to_datetime(start_date, utc=True)
                df = df[df["timestamp"] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)
                df = df[df["timestamp"] < end_dt]
        else:
            # Apply quick-filter radio
            now_utc = pd.Timestamp.now(tz='UTC')
            if period_filter == 'session':
                session_start = None
                try:
                    if state_json:
                        st = json.loads(state_json)
                        ss = st.get("session_start", "")
                        if ss:
                            session_start = pd.to_datetime(ss, utc=True)
                except Exception:
                    pass
                if session_start is not None:
                    df = df[df["timestamp"] >= session_start]
            elif period_filter == 'today':
                today_start = now_utc.normalize()
                df = df[df["timestamp"] >= today_start]
            elif period_filter == '7d':
                df = df[df["timestamp"] >= now_utc - pd.Timedelta(days=7)]
            # 'all' -- no filter

        if df.empty:
            return empty_cards, empty_fig, empty_fig, empty_fig, empty_fig, empty_table""",
    "P3-C: CB-9 add period_filter + session_start logic",
)

# ---------------------------------------------------------------------------
# P3-D: Coin Summary syncs with analytics date range (BUG-5)
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """@callback(
    Output('coin-summary-grid',    'rowData'),
    Output('coin-summary-caption', 'children'),
    Input('coin-period-filter',    'value'),
    Input('store-trades',          'data'),
    prevent_initial_call=True,
)
def update_coin_summary(period_filter, trades_json):
    \"\"\"Filter trades by period and render per-coin summary grid.\"\"\"
    try:
        if not trades_json:
            return [], ""
        df = pd.read_json(io.StringIO(trades_json), orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

        # Apply period filter
        if period_filter == '7d':
            cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)
            df = df[df.timestamp >= cutoff]
        elif period_filter == 'week':
            now = pd.Timestamp.now(tz='UTC')
            # Filter to current ISO week
            df = df[df.timestamp.dt.isocalendar().week == now.isocalendar().week]
            df = df[df.timestamp.dt.year == now.year]
        # 'all' \u2014 no filter

        records = build_coin_summary(df)
        caption = f"{len(records)} coins in history"
        return records, caption
    except Exception as e:
        LOG.error("Error in coin summary: %s", e, exc_info=True)
        return [], html.Span(f"Error: {e}", style={'color': COLORS['red']})""",
    """@callback(
    Output('coin-summary-grid',    'rowData'),
    Output('coin-summary-caption', 'children'),
    Input('coin-period-filter',    'value'),
    Input('analytics-date-range',  'start_date'),
    Input('analytics-date-range',  'end_date'),
    Input('store-trades',          'data'),
    prevent_initial_call=True,
)
def update_coin_summary(period_filter, start_date, end_date, trades_json):
    \"\"\"Filter trades by period and render per-coin summary grid (v1-5: syncs with analytics dates).\"\"\"
    try:
        if not trades_json:
            return [], ""
        df = pd.read_json(io.StringIO(trades_json), orient='split')
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

        # Analytics date range takes priority over coin radio filter
        if start_date or end_date:
            if start_date:
                df = df[df.timestamp >= pd.to_datetime(start_date, utc=True)]
            if end_date:
                df = df[df.timestamp < pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)]
        else:
            # Apply coin-period radio
            if period_filter == '7d':
                cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)
                df = df[df.timestamp >= cutoff]
            elif period_filter == 'week':
                now = pd.Timestamp.now(tz='UTC')
                df = df[df.timestamp.dt.isocalendar().week == now.isocalendar().week]
                df = df[df.timestamp.dt.year == now.year]
            # 'all' -- no filter

        records = build_coin_summary(df)
        caption = str(len(records)) + " coins in history"
        return records, caption
    except Exception as e:
        LOG.error("Error in coin summary: %s", e, exc_info=True)
        return [], html.Span("Error: " + str(e), style={'color': COLORS['red']})""",
    "P3-D: coin summary syncs with analytics date range",
)

# P3-D: Coin detail resets on period filter change
src = safe_replace(
    src,
    """@callback(
    Output('coin-detail-section', 'children'),
    Input('coin-summary-grid', 'selectedRows'),
    Input('store-trades', 'data'),
    prevent_initial_call=True,
)
def show_coin_detail(selected_rows, trades_json):""",
    """@callback(
    Output('coin-detail-section', 'children'),
    Input('coin-summary-grid', 'selectedRows'),
    Input('store-trades', 'data'),
    Input('coin-period-filter', 'value'),
    Input('analytics-date-range', 'start_date'),
    prevent_initial_call=True,
)
def show_coin_detail(selected_rows, trades_json, _period, _start):""",
    "P3-D: coin detail resets on filter change",
)

# ---------------------------------------------------------------------------
# P3-E: Status bar -- add Exchange Connected indicator
# ---------------------------------------------------------------------------
src = safe_replace(
    src,
    """        return html.Div([
            build_metric_card("Status", status_label, status_color),
            build_metric_card("Balance", "${:.2f}".format(api_balance), balance_color),
            build_metric_card("Equity", "${:.2f}".format(api_equity), equity_color),
            build_metric_card("Unrealized", "${:+.2f}".format(unrealized_pnl), unreal_color),
            build_metric_card("Positions", f"{open_count} / {max_positions}"),
            build_metric_card("Daily Trades", f"{daily_trades} / {max_daily_trades}"),
            build_metric_card("Risk Used", f"{risk_pct:.0f}%",
                              COLORS['red'] if risk_pct > 80 else COLORS['text']),
            build_metric_card("Last Refresh", now_str, COLORS['muted']),
        ], style={'display': 'flex', 'gap': '12px', 'padding': '12px',
                  'background': COLORS['panel'],
                  'borderBottom': f"1px solid {COLORS['grid']}"})""",
    """        # Exchange connected = API returned real balance data
        exch_connected = api_balance > 0
        exch_label = "CONNECTED" if exch_connected else "NO DATA"
        exch_color = COLORS['green'] if exch_connected else COLORS['muted']

        return html.Div([
            build_metric_card("BOT", status_label, status_color),
            build_metric_card("EXCHANGE", exch_label, exch_color),
            build_metric_card("Balance", "${:.2f}".format(api_balance), balance_color),
            build_metric_card("Equity", "${:.2f}".format(api_equity), equity_color),
            build_metric_card("Unrealized", "${:+.2f}".format(unrealized_pnl), unreal_color),
            build_metric_card("Positions", str(open_count) + " / " + str(max_positions)),
            build_metric_card("Daily Trades", str(daily_trades) + " / " + str(max_daily_trades)),
            build_metric_card("Risk Used", str(risk_pct) + "%",
                              COLORS['red'] if risk_pct > 80 else COLORS['text']),
            build_metric_card("Last Refresh", now_str, COLORS['muted']),
        ], style={'display': 'flex', 'gap': '12px', 'padding': '12px',
                  'background': COLORS['panel'],
                  'borderBottom': '1px solid ' + COLORS['grid']})""",
    "P3-E: status bar BOT/EXCHANGE dual indicators",
)

# ---------------------------------------------------------------------------
# P3-F: TTP stats panel -- new CB-19 (appended after CB-10)
# ---------------------------------------------------------------------------
TTP_STATS_CB = """

# ---------------------------------------------------------------------------
# CB-19: TTP Stats Panel (v1-5)
# ---------------------------------------------------------------------------

@callback(
    Output('ttp-stats-section', 'children'),
    Input('store-trades', 'data'),
    Input('analytics-period-filter', 'value'),
    Input('analytics-date-range', 'start_date'),
    Input('analytics-date-range', 'end_date'),
    State('store-state', 'data'),
    prevent_initial_call=True,
)
def update_ttp_stats(trades_json, period_filter, start_date, end_date, state_json):
    \"\"\"Render TTP performance stats panel in Analytics tab (v1-5).\"\"\"
    try:
        if not trades_json:
            return html.Div("No trade data.", style={'color': COLORS['muted']})
        df = pd.read_json(io.StringIO(trades_json), orient='split')
        if 'ttp_activated' not in df.columns:
            return html.Div(
                "TTP tracking not yet active. Restart bot after Phase 2 fix to populate TTP columns.",
                style={'color': COLORS['muted'], 'fontStyle': 'italic'},
            )
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        # Apply same filter logic as analytics
        if start_date or end_date:
            if start_date:
                df = df[df["timestamp"] >= pd.to_datetime(start_date, utc=True)]
            if end_date:
                df = df[df["timestamp"] < pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)]
        else:
            now_utc = pd.Timestamp.now(tz='UTC')
            if period_filter == 'session':
                try:
                    if state_json:
                        st = json.loads(state_json)
                        ss = st.get("session_start", "")
                        if ss:
                            df = df[df["timestamp"] >= pd.to_datetime(ss, utc=True)]
                except Exception:
                    pass
            elif period_filter == 'today':
                df = df[df["timestamp"] >= now_utc.normalize()]
            elif period_filter == '7d':
                df = df[df["timestamp"] >= now_utc - pd.Timedelta(days=7)]

        if df.empty:
            return html.Div("No trades in selected period.", style={'color': COLORS['muted']})

        total = len(df)
        df['ttp_activated'] = df['ttp_activated'].astype(str).str.lower().isin(['true', '1'])
        activated = df['ttp_activated'].sum()
        act_pct = round(activated / total * 100, 1) if total else 0

        ttp_exits = 0
        if 'ttp_exit_reason' in df.columns:
            ttp_exits = (df['ttp_exit_reason'].astype(str) == 'TTP_CLOSE').sum()

        sl_while_activated = 0
        if 'exit_reason' in df.columns:
            sl_while_activated = len(df[
                df['ttp_activated'] & df['exit_reason'].isin(['SL_HIT', 'SL_HIT_ASSUMED'])
            ])

        avg_extreme = 0.0
        if 'ttp_extreme_pct' in df.columns:
            vals = pd.to_numeric(df.loc[df['ttp_activated'], 'ttp_extreme_pct'], errors='coerce').dropna()
            avg_extreme = round(vals.mean(), 3) if len(vals) else 0.0

        return html.Div([
            html.Div([
                build_metric_card("TTP Activated", str(activated) + " / " + str(act_pct) + "%",
                                  COLORS['blue']),
                build_metric_card("Closed via TTP", str(ttp_exits),
                                  COLORS['green'] if ttp_exits > 0 else COLORS['muted']),
                build_metric_card("SL Hit While TTP Active", str(sl_while_activated),
                                  COLORS['red'] if sl_while_activated > 0 else COLORS['muted']),
                build_metric_card("Avg TTP Extreme %", str(avg_extreme) + "%", COLORS['text']),
            ], style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'}),
        ])
    except Exception as e:
        LOG.error("TTP stats error: %s", e, exc_info=True)
        return html.Div("Error: " + str(e), style={'color': COLORS['red']})

"""

# Insert CB-19 after CB-10 (after update_coin_summary function ends)
src = safe_replace(
    src,
    """# ---------------------------------------------------------------------------
# CB-11: Load Config Into Controls
# ---------------------------------------------------------------------------""",
    TTP_STATS_CB + """# ---------------------------------------------------------------------------
# CB-11: Load Config Into Controls
# ---------------------------------------------------------------------------""",
    "P3-F: insert CB-19 TTP stats callback",
)

# ---------------------------------------------------------------------------
# P3-G: Trade chart popup -- layout addition + CB-20
# ---------------------------------------------------------------------------

# Add trade-chart-modal div to make_history_tab layout
src = safe_replace(
    src,
    """        html.Div(id='history-summary', style={'color': COLORS['muted'], 'marginTop': '8px'}),
    ])""",
    """        html.Div(id='history-summary', style={'color': COLORS['muted'], 'marginTop': '8px'}),
        # Trade chart popup modal (v1-5)
        html.Div(
            id='trade-chart-modal',
            children=[],
            style={'display': 'none'},
        ),
    ])""",
    "P3-G: add trade-chart-modal placeholder to history tab",
)

# Add chart popup click target to live trades tab
src = safe_replace(
    src,
    """        html.Div(id='selected-pos-info'),   # shows selected row info + action buttons
        html.Div(id='pos-action-status',    # shows success/error from actions
                 style={'marginTop': '8px', 'color': COLORS['green']}),
    ])""",
    """        html.Div(id='selected-pos-info'),   # shows selected row info + action buttons
        html.Div(id='pos-action-status',    # shows success/error from actions
                 style={'marginTop': '8px', 'color': COLORS['green']}),
        # Live trade chart popup modal (v1-5)
        html.Div(id='live-trade-chart-modal', children=[], style={'display': 'none'}),
    ])""",
    "P3-G: add live-trade-chart-modal to live trades tab",
)

# Append CB-20 before the final if __name__ block
CHART_CB = """

# ---------------------------------------------------------------------------
# CB-20: Trade Chart Popup (v1-5)
# Fires on history-grid row click -> fetches klines -> renders chart modal
# ---------------------------------------------------------------------------

def _fetch_klines_for_chart(symbol: str, start_ms: int, end_ms: int) -> list:
    \"\"\"Fetch 5m klines from BingX for the given symbol and time window.\"\"\"
    if not API_KEY or not SECRET_KEY:
        return []
    try:
        params = {
            'symbol': symbol,
            'interval': '5m',
            'startTime': str(start_ms),
            'endTime': str(end_ms),
            'limit': '300',
        }
        signed = _sign(params)
        headers = {'X-BX-APIKEY': API_KEY}
        url = BASE_URL + '/openApi/swap/v2/quote/klines'
        resp = requests.get(url, params=signed, headers=headers, timeout=15)
        data = resp.json()
        if data.get('code', -1) != 0:
            return []
        return data.get('data', [])
    except Exception as e:
        LOG.warning("Kline fetch failed %s: %s", symbol, e)
        return []


def _build_trade_chart(symbol: str, direction: str, entry_price: float,
                       exit_price: float, entry_ts: str, exit_ts: str,
                       entry_ms: int, exit_ms: int) -> go.Figure:
    \"\"\"Build multi-panel Plotly figure: candlestick + stochastic + BBW.\"\"\"
    import plotly.subplots as sp

    pad = 25 * 5 * 60 * 1000  # 25 bars padding
    klines = _fetch_klines_for_chart(symbol, max(0, entry_ms - pad), exit_ms + pad)

    if not klines:
        fig = go.Figure()
        fig.add_annotation(text="No kline data available", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font={'color': '#888', 'size': 14})
        fig.update_layout(paper_bgcolor='#0d1117', plot_bgcolor='#0d1117', height=300)
        return fig

    # Parse klines: [timestamp_ms, open, high, low, close, volume]
    ts_list, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    for k in klines:
        try:
            ts_list.append(pd.Timestamp(int(k[0]), unit='ms', tz='UTC'))
            opens.append(float(k[1]))
            highs.append(float(k[2]))
            lows.append(float(k[3]))
            closes.append(float(k[4]))
            volumes.append(float(k[5]) if len(k) > 5 else 0.0)
        except (IndexError, ValueError, TypeError):
            continue

    n = len(closes)
    if n < 14:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data (" + str(n) + " bars)",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font={'color': '#888', 'size': 14})
        fig.update_layout(paper_bgcolor='#0d1117', plot_bgcolor='#0d1117', height=300)
        return fig

    import numpy as np

    # Stochastic %K Raw (smooth=1): (close - lowest_low) / (highest_high - lowest_low) * 100
    def stoch_k(period: int) -> list:
        \"\"\"Compute raw stochastic K for given period.\"\"\"
        result = [None] * n
        for i in range(period - 1, n):
            lo = min(lows[i - period + 1: i + 1])
            hi = max(highs[i - period + 1: i + 1])
            denom = hi - lo
            result[i] = (closes[i] - lo) / denom * 100 if denom > 0 else 50.0
        return result

    def smooth_k(raw: list, period: int) -> list:
        \"\"\"SMA smoothing for stochastic D line.\"\"\"
        result = [None] * n
        for i in range(n):
            vals = [x for x in raw[max(0, i - period + 1): i + 1] if x is not None]
            if len(vals) == period:
                result[i] = sum(vals) / period
        return result

    k9_raw  = stoch_k(9)
    k9_d    = smooth_k(k9_raw, 3)
    k14_raw = stoch_k(14)
    k14_d   = smooth_k(k14_raw, 3)

    # Ripster clouds: EMA pairs (5/12, 34/50, 72/89)
    def ema(data: list, period: int) -> list:
        \"\"\"Compute EMA for given period.\"\"\"
        result = [None] * n
        mult = 2.0 / (period + 1)
        for i in range(n):
            if data[i] is None:
                continue
            if result[i - 1] is None and i == 0:
                result[i] = data[i]
            elif result[i - 1] is None:
                result[i] = data[i]
            else:
                result[i] = data[i] * mult + result[i - 1] * (1 - mult)
        return result

    ema5  = ema(closes, 5)
    ema12 = ema(closes, 12)
    ema34 = ema(closes, 34)
    ema50 = ema(closes, 50)

    # BBW: (BB_upper - BB_lower) / BB_middle
    def bbw(period: int = 20, mult: float = 2.0) -> list:
        \"\"\"Bollinger Band Width.\"\"\"
        result = [None] * n
        for i in range(period - 1, n):
            window = closes[i - period + 1: i + 1]
            mid = sum(window) / period
            std = (sum((x - mid) ** 2 for x in window) / period) ** 0.5
            result[i] = (2 * mult * std) / mid * 100 if mid > 0 else 0.0
        return result

    bbw_vals = bbw()

    # Build figure
    fig = sp.make_subplots(
        rows=3, cols=1,
        row_heights=[0.55, 0.25, 0.20],
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=[symbol + " 5m", "Stochastic", "BBW%"],
    )

    # Row 1: Candlestick
    fig.add_trace(go.Candlestick(
        x=ts_list, open=opens, high=highs, low=lows, close=closes,
        name="Price",
        increasing_line_color='#3fb950',
        decreasing_line_color='#f85149',
        showlegend=False,
    ), row=1, col=1)

    # Ripster EMA clouds
    valid = [i for i in range(n) if ema5[i] is not None and ema12[i] is not None]
    if valid:
        ts_v = [ts_list[i] for i in valid]
        e5v   = [ema5[i]  for i in valid]
        e12v  = [ema12[i] for i in valid]
        e34v  = [ema34[i] for i in valid if ema34[i] is not None]
        e50v  = [ema50[i] for i in valid if ema50[i] is not None]
        ts34  = [ts_list[i] for i in valid if ema34[i] is not None]

        fig.add_trace(go.Scatter(x=ts_v, y=e5v, line={'color': '#58a6ff', 'width': 1},
                                 name="EMA5", showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=ts_v, y=e12v, line={'color': '#388bfd', 'width': 1},
                                 fill='tonexty', fillcolor='rgba(56,139,253,0.12)',
                                 name="EMA12", showlegend=False), row=1, col=1)
        if e34v:
            fig.add_trace(go.Scatter(x=ts34, y=e34v, line={'color': '#f78166', 'width': 1},
                                     name="EMA34", showlegend=False), row=1, col=1)
        if e50v:
            fig.add_trace(go.Scatter(x=ts34, y=e50v, line={'color': '#ffa657', 'width': 1},
                                     fill='tonexty', fillcolor='rgba(255,166,87,0.10)',
                                     name="EMA50", showlegend=False), row=1, col=1)

    # Entry / Exit vertical lines
    try:
        entry_dt = pd.Timestamp(entry_ms, unit='ms', tz='UTC')
        exit_dt  = pd.Timestamp(exit_ms,  unit='ms', tz='UTC')
        for row_n in [1, 2, 3]:
            fig.add_vline(x=entry_dt, line_color='#3fb950', line_dash='dash',
                          line_width=1, row=row_n, col=1)
            fig.add_vline(x=exit_dt, line_color='#f85149', line_dash='dash',
                          line_width=1, row=row_n, col=1)
        fig.add_hline(y=entry_price, line_color='#3fb950', line_dash='dot',
                      line_width=1, row=1, col=1)
        if exit_price:
            fig.add_hline(y=exit_price, line_color='#f85149', line_dash='dot',
                          line_width=1, row=1, col=1)
    except Exception:
        pass

    # Row 2: Stochastic
    ts_k9  = [ts_list[i] for i in range(n) if k9_raw[i] is not None]
    v_k9   = [k9_raw[i]  for i in range(n) if k9_raw[i] is not None]
    ts_k9d = [ts_list[i] for i in range(n) if k9_d[i] is not None]
    v_k9d  = [k9_d[i]    for i in range(n) if k9_d[i] is not None]
    ts_k14 = [ts_list[i] for i in range(n) if k14_raw[i] is not None]
    v_k14  = [k14_raw[i] for i in range(n) if k14_raw[i] is not None]

    fig.add_trace(go.Scatter(x=ts_k9,  y=v_k9,  line={'color': '#58a6ff', 'width': 1},
                             name="%K(9)", showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=ts_k9d, y=v_k9d, line={'color': '#388bfd', 'width': 1},
                             name="%D(9)", showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=ts_k14, y=v_k14, line={'color': '#ffa657', 'width': 1, 'dash': 'dot'},
                             name="%K(14)", showlegend=False), row=2, col=1)
    fig.add_hline(y=80, line_color='#444', line_dash='dot', line_width=1, row=2, col=1)
    fig.add_hline(y=20, line_color='#444', line_dash='dot', line_width=1, row=2, col=1)

    # Row 3: BBW
    ts_bbw = [ts_list[i] for i in range(n) if bbw_vals[i] is not None]
    v_bbw  = [bbw_vals[i] for i in range(n) if bbw_vals[i] is not None]
    if ts_bbw:
        fig.add_trace(go.Bar(x=ts_bbw, y=v_bbw,
                             marker_color='#8b949e', name="BBW%",
                             showlegend=False), row=3, col=1)

    fig.update_layout(
        paper_bgcolor='#0d1117',
        plot_bgcolor='#161b22',
        font={'color': '#c9d1d9', 'size': 11},
        height=600,
        margin={'l': 50, 'r': 20, 't': 40, 'b': 20},
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 4):
        fig.update_xaxes(showgrid=True, gridcolor='#21262d', row=i, col=1)
        fig.update_yaxes(showgrid=True, gridcolor='#21262d', row=i, col=1)

    return fig


def _trade_chart_modal_content(row: dict) -> list:
    \"\"\"Build modal overlay children list from a selected history grid row.\"\"\"
    symbol      = row.get('Symbol', row.get('symbol', ''))
    direction   = row.get('Dir', row.get('direction', ''))
    entry_price = float(row.get('Entry', row.get('entry_price', 0)) or 0)
    exit_price  = float(row.get('Exit',  row.get('exit_price',  0)) or 0)
    entry_ts    = str(row.get('Entry Time', row.get('entry_time', '')))
    exit_ts     = str(row.get('Date', row.get('timestamp', '')))
    exit_reason = str(row.get('Exit Reason', row.get('exit_reason', '')))
    pnl_net     = float(row.get('Net PnL', row.get('pnl_net', 0)) or 0)

    def ts_to_ms(s: str) -> int:
        \"\"\"Parse ISO string to milliseconds epoch.\"\"\"
        try:
            dt = pd.Timestamp(s, tz='UTC') if '+' not in s and 'Z' not in s else pd.Timestamp(s)
            return int(dt.timestamp() * 1000)
        except Exception:
            return int(pd.Timestamp.now(tz='UTC').timestamp() * 1000)

    entry_ms = ts_to_ms(entry_ts)
    exit_ms  = ts_to_ms(exit_ts)
    if entry_ms >= exit_ms:
        exit_ms = entry_ms + 3600000  # fallback 1hr

    pnl_color = '#3fb950' if pnl_net >= 0 else '#f85149'
    fig = _build_trade_chart(symbol, direction, entry_price, exit_price,
                             entry_ts, exit_ts, entry_ms, exit_ms)

    return [
        # Backdrop
        html.Div(
            id='chart-modal-backdrop',
            style={
                'position': 'fixed', 'top': '0', 'left': '0',
                'width': '100%', 'height': '100%',
                'background': 'rgba(0,0,0,0.75)', 'zIndex': '1000',
                'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
            },
            children=[
                html.Div([
                    # Header
                    html.Div([
                        html.Span(symbol + "  " + direction,
                                  style={'fontWeight': 'bold', 'fontSize': '16px'}),
                        html.Span("  " + exit_reason,
                                  style={'color': '#888', 'marginLeft': '12px'}),
                        html.Span("  PnL: " + ("+" if pnl_net >= 0 else "") + str(round(pnl_net, 4)),
                                  style={'color': pnl_color, 'marginLeft': '12px'}),
                        html.Button("x  Close", id='close-chart-modal-btn',
                                    n_clicks=0,
                                    style={
                                        'float': 'right', 'background': '#21262d',
                                        'color': '#c9d1d9', 'border': '1px solid #444',
                                        'borderRadius': '4px', 'padding': '4px 12px',
                                        'cursor': 'pointer',
                                    }),
                    ], style={'marginBottom': '8px', 'overflow': 'hidden'}),
                    # Chart
                    dcc.Graph(figure=fig, config={'displayModeBar': False},
                              style={'width': '900px'}),
                ], style={
                    'background': '#0d1117', 'border': '1px solid #21262d',
                    'borderRadius': '8px', 'padding': '16px',
                    'maxWidth': '960px', 'width': '95vw',
                }),
            ],
        ),
    ]


@callback(
    Output('trade-chart-modal', 'children'),
    Output('trade-chart-modal', 'style'),
    Input('history-grid', 'selectedRows'),
    prevent_initial_call=True,
)
def open_trade_chart(selected_rows):
    \"\"\"Open trade chart modal when history grid row is clicked (v1-5).\"\"\"
    if not selected_rows:
        return [], {'display': 'none'}
    row = selected_rows[0]
    try:
        children = _trade_chart_modal_content(row)
        return children, {'display': 'block', 'position': 'relative', 'zIndex': '1000'}
    except Exception as e:
        LOG.error("Trade chart error: %s", e, exc_info=True)
        return [html.Span("Chart error: " + str(e), style={'color': '#f85149'})], {'display': 'block'}


@callback(
    Output('trade-chart-modal', 'children', allow_duplicate=True),
    Output('trade-chart-modal', 'style',    allow_duplicate=True),
    Input('close-chart-modal-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def close_trade_chart(n_clicks):
    \"\"\"Close trade chart modal (v1-5).\"\"\"
    return [], {'display': 'none'}

"""

src = safe_replace(
    src,
    """# ---------------------------------------------------------------------------
# CB-S1: Load bot-status.json every 5s
# ---------------------------------------------------------------------------""",
    CHART_CB + """# ---------------------------------------------------------------------------
# CB-S1: Load bot-status.json every 5s
# ---------------------------------------------------------------------------""",
    "P3-G: insert CB-20 trade chart popup callbacks",
)

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
DEST.write_text(src, encoding="utf-8")
print("")
print("Written: " + str(DEST))

verify(DEST, "bingx-live-dashboard-v1-5.py")

print("")
if ERRORS:
    print("BUILD FAILED: " + ", ".join(ERRORS))
    sys.exit(1)
else:
    print("BUILD OK -- Dashboard v1.5 ready")
    print("")
    print("Run:")
    print('  cd "' + str(ROOT) + '"')
    print("  python bingx-live-dashboard-v1-5.py")
    print("  # Opens at http://localhost:8051")
