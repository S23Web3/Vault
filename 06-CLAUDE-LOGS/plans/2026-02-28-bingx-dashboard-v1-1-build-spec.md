# Build Spec: BingX Live Dashboard v1-1
**Self-contained build document — no prior session context required**

---

## What This Is

A Plotly Dash web app that monitors and controls a live BingX futures trading bot.
It replaces `bingx-live-dashboard-v1.py` (which was Streamlit, read-only, and wrong).

**Tech:** Dash 4.0.0, dash-ag-grid, Plotly, port 8051
**Why Dash not Streamlit:** Streamlit reruns the full script on every widget click. This wipes mid-action form state (e.g., typing a new SL price). Dash uses a reactive callback graph — only the wired output updates. Per-row interactive buttons (Raise BE, Move SL) require Dash's pattern-matching callbacks (`MATCH` selector). Streamlit cannot do this.

---

## Output File

```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-1.py
C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\assets\dashboard.css
```

The `assets/` folder must be in the same directory as the dashboard file. Dash auto-serves it.

---

## Dependencies

```bash
pip install dash dash-ag-grid plotly pandas pyyaml requests python-dotenv
```

All already installed in the project venv except `dash` and `dash-ag-grid`.
`dash-ag-grid` version 33.3.3. `dash` version 4.0.0.

---

## Run Command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python bingx-live-dashboard-v1-1.py
# Opens at http://localhost:8051
```

**Production on VPS (jacky — 76.13.20.191):**
```bash
gunicorn -w 1 -b 0.0.0.0:8051 bingx_live_dashboard_v1_1:server
# Accessible from any browser at http://76.13.20.191:8051
# Add dash_auth.BasicAuth before VPS deployment (controls real money)
```
`server = app.server` must be defined at module level for gunicorn.

---

## Data Sources

### state.json — live bot state, updated by the running bot every loop
Path: `PROJECTS/bingx-connector/state.json`
```json
{
  "open_positions": {
    "ELSA-USDT_SHORT": {
      "symbol": "ELSA-USDT",
      "direction": "SHORT",
      "grade": "A",
      "entry_price": 0.084700,
      "sl_price": 0.085040,
      "tp_price": null,
      "quantity": 591.0,
      "notional_usd": 50.06,
      "entry_time": "2026-02-27T19:15:00+00:00",
      "order_id": "123456789",
      "atr_at_entry": 0.000170,
      "be_raised": true
    }
  },
  "daily_pnl": -2.45,
  "daily_trades": 3,
  "halt_flag": false,
  "session_start": "2026-02-28T08:00:00+00:00"
}
```

### trades.csv — append-only closed trade log
Path: `PROJECTS/bingx-connector/trades.csv`
Columns: `timestamp, symbol, direction, grade, entry_price, exit_price, exit_reason, pnl_net, quantity, notional_usd, entry_time, order_id`
- `exit_reason` values: `SL_HIT`, `TP_HIT`, `EXIT_UNKNOWN`, `SL_HIT_ASSUMED`
- `timestamp` = close time UTC ISO string
- `entry_time` = open time UTC ISO string

### config.yaml — bot configuration
Path: `PROJECTS/bingx-connector/config.yaml`
Relevant editable sections:
```yaml
connector:
  demo_mode: false           # bool — LIVE vs DEMO

four_pillars:
  sl_atr_mult: 2.0           # float — SL distance in ATR multiples
  tp_atr_mult: null          # float or null — null = no fixed TP
  require_stage2: true       # bool — Stage 2 stochastic filter
  rot_level: 80              # int — rotation level for Stage 2
  allow_a: true              # bool — allow Grade A entries
  allow_b: true              # bool — allow Grade B entries
  allow_c: false             # bool — allow Grade C entries

risk:
  max_positions: 8           # int
  max_daily_trades: 50       # int
  daily_loss_limit_usd: 15.0 # float
  min_atr_ratio: 0.003       # float — minimum ATR/price ratio
  cooldown_bars: 3           # int — bars between re-entries

position:
  margin_usd: 5.0            # float — margin per trade (*)
  leverage: 10               # int — leverage (*)
```
(*) margin_usd and leverage changes require bot restart to take effect.

### .env — API credentials
Path: `PROJECTS/bingx-connector/.env`
```
BINGX_API_KEY=...
BINGX_SECRET_KEY=...
```

---

## Architecture

Single-file Dash app. No multi-page routing (`use_pages=False`). Reason: no background enricher, no PostgreSQL, no ML models. All data loads in < 1s from local files.

```
app.layout
├── dcc.Interval (id='refresh-interval', 60s)
├── dcc.Store (id='store-state',   memory) — JSON string of state.json
├── dcc.Store (id='store-trades',  memory) — trades DataFrame as JSON orient=split
├── dcc.Store (id='store-config',  memory) — JSON string of config.yaml
├── html.Div  (id='status-bar')            — top bar, always visible
└── dcc.Tabs  (id='main-tabs')
    ├── Tab: Operational  (value='tab-ops')
    ├── Tab: History      (value='tab-hist')
    ├── Tab: Analytics    (value='tab-analytics')
    ├── Tab: Coin Summary (value='tab-coins')
    └── Tab: Bot Controls (value='tab-controls')
└── html.Div  (id='tab-content')           — rendered by tab-switch callback
```

**Single data load point:** `dcc.Interval` fires every 60s. One callback reads all three sources and writes all three stores. Every tab callback reads from stores — never from disk directly. This means files are read once per minute, not once per widget click.

**Store serialization rule:** DataFrames are stored as `.to_json(orient='split', date_format='iso')`. Never store a DataFrame object directly in dcc.Store — it is not JSON-serializable and will silently fail.

---

## Color Constants (module level)

```python
COLORS = {
    'bg':     '#0d1117',
    'panel':  '#161b22',
    'text':   '#c9d1d9',
    'muted':  '#8b949e',
    'green':  '#3fb950',
    'red':    '#f85149',
    'blue':   '#58a6ff',
    'orange': '#d29922',
    'grid':   '#21262d',
}
```

These are referenced everywhere. Never hardcode hex values inline.

---

## BingX API Client (module level)

The dashboard needs to call BingX to cancel/place orders (Raise BE, Move SL).
Import existing `BingXAuth` from `bingx_auth.py` in the same directory.

```python
import os
import time
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()
API_KEY    = os.getenv('BINGX_API_KEY', '')
SECRET_KEY = os.getenv('BINGX_SECRET_KEY', '')
BASE_URL   = 'https://open-api.bingx.com'  # live API, not VST
```

If `API_KEY` is empty, position action callbacks return an error message without crashing.

**Signing function** (replicated from bingx_auth.py pattern — do not import bot internals):
```python
def _sign(params: dict) -> dict:
    """Add timestamp and HMAC-SHA256 signature to params dict."""
    params['timestamp'] = int(time.time() * 1000)
    query = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params
```

**API helper:**
```python
def _bingx_request(method: str, path: str, params: dict) -> dict:
    """Send signed BingX API request. Returns response dict or {'error': msg}."""
    if not API_KEY or not SECRET_KEY:
        return {'error': 'No API keys configured'}
    try:
        signed = _sign(params)
        headers = {'X-BX-APIKEY': API_KEY}
        url = BASE_URL + path
        if method == 'GET':
            resp = requests.get(url, params=signed, headers=headers, timeout=8)
        elif method == 'DELETE':
            resp = requests.delete(url, params=signed, headers=headers, timeout=8)
        elif method == 'POST':
            resp = requests.post(url, params=signed, headers=headers, timeout=8)
        data = resp.json()
        if data.get('code', 0) != 0:
            return {'error': f"BingX error {data.get('code')}: {data.get('msg')}"}
        return data.get('data', {})
    except Exception as e:
        return {'error': str(e)}
```

---

## Complete Function Inventory

### Group A — Data Loaders (reused from v1, zero changes)

#### `load_state() -> dict`
**Docstring:** `Load state.json. Returns dict with safe defaults if file is missing.`
**Logic:**
- If `STATE_PATH` does not exist → return defaults dict
- Try `json.load(f)` → merge with defaults using `{**defaults, **data}`
- Except `json.JSONDecodeError, OSError` → return defaults
- Defaults: `{"open_positions": {}, "daily_pnl": 0.0, "daily_trades": 0, "halt_flag": False, "session_start": ""}`

#### `load_config() -> dict`
**Docstring:** `Load config.yaml. Returns empty dict if file missing or invalid.`
**Logic:**
- If `CONFIG_PATH` not exists → return `{}`
- Try `yaml.safe_load(f) or {}` → return
- Except `yaml.YAMLError, OSError` → return `{}`

#### `load_trades() -> pd.DataFrame`
**Docstring:** `Load trades.csv. Returns DataFrame sorted newest-first, or empty DataFrame.`
**Logic:**
- If `TRADES_PATH` not exists → return `pd.DataFrame()`
- `pd.read_csv(TRADES_PATH)` then:
  - `pd.to_datetime(df["timestamp"], utc=True, errors="coerce")`
  - `pd.to_datetime(df["entry_time"], utc=True, errors="coerce")`
  - `pd.to_numeric(df["pnl_net"], errors="coerce")`
  - `pd.to_numeric(df["entry_price"], errors="coerce")`
  - `pd.to_numeric(df["exit_price"], errors="coerce")`
  - sort by `timestamp` descending, reset index
- Except `Exception` → return empty DataFrame

#### `fetch_mark_price(symbol: str) -> float | None`
**Docstring:** `Fetch BingX mark price for one symbol via public REST endpoint. Returns float or None.`
**Logic:**
- GET `https://open-api.bingx.com/openApi/swap/v2/quote/price?symbol={symbol}` timeout=5
- `data = resp.json().get("data", {})`
- If dict: `val = float(data.get("price", 0))` → return if `val > 0` else None
- If list and non-empty: `val = float(data[0].get("price", 0))` → return if `val > 0` else None
- Except any Exception → return None

#### `fetch_all_mark_prices(symbols: list) -> dict`
**Docstring:** `Fetch mark prices for list of symbols in parallel. Returns {symbol: price} dict.`
**Logic:**
- Use `concurrent.futures.ThreadPoolExecutor(max_workers=8)`
- Submit `fetch_mark_price(sym)` for each symbol
- `as_completed(futures, timeout=8)` — collect results
- Return dict of non-None results
- On exception per future: skip that symbol silently

#### `fmt_duration(start_dt, end_dt=None) -> str`
**Docstring:** `Format duration between two datetimes as '2h 15m' or '45m'. Returns em-dash on error.`
**Logic:**
- If `end_dt` is None → `datetime.now(timezone.utc)`
- If `start_dt` is None or `pd.isna(start_dt)` → return `"—"`
- `total_sec = int((end_dt - start_dt).total_seconds())`
- If `total_sec < 0` → return `"—"`
- `h = total_sec // 3600`, `m = (total_sec % 3600) // 60`
- Return `f"{h}h {m}m"` if h > 0 else `f"{m}m"`
- Except Exception → return `"—"`

---

### Group B — Data Builders

#### `build_positions_df(state: dict, mark_prices: dict) -> pd.DataFrame`
**Docstring:** `Build display DataFrame for open positions. Adds unrealized PnL and distance-to-SL columns.`
**Logic:**
For each position in `state["open_positions"].values()`:
- Extract: `sym, direction, entry, qty, mark (from mark_prices), sl_raw, tp_raw`
- Compute `unreal_pnl`:
  - If mark and qty and entry → `sign = 1 if LONG else -1`, `unreal_pnl = round((mark - entry) * qty * sign, 4)`
  - Else None
- Compute `dist_to_sl_pct`:
  - If mark and sl_raw and sl_raw > 0 → `round(abs(mark - sl_raw) / mark * 100, 2)`
  - Else None
- Parse `entry_dt` from `pos["entry_time"]` ISO string, compute `duration` via `fmt_duration`
- `tp_display = round(float(tp_raw), 6) if tp_raw else "—"`
- Append row dict with keys: `Symbol, Dir, Grade, Entry, Stop Loss, Take Profit, BE Raised, Unreal PnL, Dist SL %, Duration, Notional, order_id`
  - `BE Raised` = `"Yes"` if `pos.get("be_raised")` else `"No"`
  - Include `order_id` as hidden column (needed for API calls)
- Return `pd.DataFrame(rows)` or empty DataFrame if no rows

#### `compute_metrics(df: pd.DataFrame) -> dict`
**Docstring:** `Compute summary performance metrics from closed trades DataFrame. Returns dict.`
**Logic:**
- Guard: if df empty or missing `pnl_net` column → return dict of zeros/defaults
- `total = len(df)`
- `wins = int((df["pnl_net"] > 0).sum())`
- `losses = total - wins`
- `win_rate = round(wins / total * 100, 1) if total > 0 else 0.0`
- `gross_wins = float(df[df.pnl_net > 0].pnl_net.sum())`
- `gross_losses = float(abs(df[df.pnl_net <= 0].pnl_net.sum()))`
- `profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else float('inf')`
- `avg_win = round(float(df[df.pnl_net > 0].pnl_net.mean()), 4) if wins > 0 else 0.0`
- `avg_loss = round(float(df[df.pnl_net <= 0].pnl_net.mean()), 4) if losses > 0 else 0.0`
- `expectancy = round((win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss), 4)`
- Max drawdown: `cum = df.sort_values("timestamp").pnl_net.cumsum()`, `max_dd = round(float((cum - cum.cummax()).min()), 4)`
- Return: `{"total": total, "win_rate": win_rate, "profit_factor": profit_factor, "avg_win": avg_win, "avg_loss": avg_loss, "expectancy": expectancy, "max_dd": max_dd, "gross_pnl": round(gross_wins - gross_losses, 4)}`

#### `build_coin_summary(df: pd.DataFrame) -> list`
**Docstring:** `Compute per-coin performance stats. Returns list of dicts for ag-grid rowData.`
**Logic:** (exact logic from v1, extracted to function)
For each `sym, grp` in `df.groupby("symbol")`:
- `total = len(grp)`, `wins = int((grp.pnl_net > 0).sum())`
- `wr = round(wins/total*100, 1) if total > 0 else 0.0`
- `net = round(float(grp.pnl_net.sum()), 4)`
- `avg = round(float(grp.pnl_net.mean()), 4)`
- `sl_pct = round((grp.exit_reason == "SL_HIT").sum() / total * 100, 1)`
- `tp_pct = round((grp.exit_reason == "TP_HIT").sum() / total * 100, 1)`
- `unk_pct = round(grp.exit_reason.isin(["EXIT_UNKNOWN", "SL_HIT_ASSUMED"]).sum() / total * 100, 1)`
- `best = round(float(grp.pnl_net.max()), 4)`, `worst = round(float(grp.pnl_net.min()), 4)`
- Append row with keys: `Symbol, Trades, WR %, Net PnL, Avg PnL, SL %, TP %, Unknown %, Best, Worst`
Return sorted by `Net PnL` descending as `list of dict` (`.to_dict('records')`)

---

### Group C — Chart Builders (all return `go.Figure`)

#### `build_equity_figure(df: pd.DataFrame) -> go.Figure`
**Docstring:** `Build cumulative net PnL equity curve as Plotly scatter figure.`
**Logic:**
- Sort df by timestamp ascending
- `cumulative = df["pnl_net"].cumsum()`
- `go.Scatter(x=df["timestamp"], y=cumulative, mode='lines', fill='tozeroy', line=dict(color=COLORS['green'], width=2), fillcolor='rgba(63,185,80,0.08)')`
- `fig.update_layout(title='Equity Curve', yaxis_title='Net PnL (USDT)', paper_bgcolor=COLORS['bg'], plot_bgcolor=COLORS['panel'], font=dict(color=COLORS['text']), margin=dict(l=40,r=20,t=40,b=40))`
- Guard: if df empty → return empty `go.Figure()` with same layout

#### `build_drawdown_figure(df: pd.DataFrame) -> go.Figure`
**Docstring:** `Build underwater equity drawdown curve as Plotly scatter figure.`
**Logic:**
- Sort by timestamp ascending
- `cum = df["pnl_net"].cumsum()`, `dd = cum - cum.cummax()`
- `go.Scatter(x=df["timestamp"], y=dd, mode='lines', fill='tozeroy', line=dict(color=COLORS['red'], width=1), fillcolor='rgba(248,81,73,0.12)')`
- Same layout settings as equity figure, title='Drawdown'

#### `build_exit_reason_figure(df: pd.DataFrame) -> go.Figure`
**Docstring:** `Build exit reason count bar chart.`
**Logic:**
- `counts = df["exit_reason"].value_counts()`
- Order: `['SL_HIT', 'TP_HIT', 'EXIT_UNKNOWN', 'SL_HIT_ASSUMED']` (only show what exists)
- Color per reason: SL_HIT=red, TP_HIT=green, EXIT_UNKNOWN=orange, SL_HIT_ASSUMED=orange
- `go.Bar(x=labels, y=values, marker_color=colors)`
- Title: 'Exit Breakdown'

#### `build_daily_pnl_figure(df: pd.DataFrame) -> go.Figure`
**Docstring:** `Build daily net PnL bar chart grouped by calendar day.`
**Logic:**
- `df["date"] = df["timestamp"].dt.date`
- `daily = df.groupby("date")["pnl_net"].sum().reset_index()`
- `colors = [COLORS['green'] if v >= 0 else COLORS['red'] for v in daily.pnl_net]`
- `go.Bar(x=daily.date, y=daily.pnl_net, marker_color=colors)`
- Title: 'Daily PnL'

---

### Group D — Layout Helpers

#### `build_metric_card(label: str, value: str, color: str = None) -> html.Div`
**Docstring:** `Build a single metric display card div.`
**Returns:**
```python
html.Div([
    html.Div(label, style={'fontSize': '11px', 'color': COLORS['muted']}),
    html.Div(value, style={'fontSize': '22px', 'fontWeight': 'bold',
                           'color': color or COLORS['text']}),
], style={'padding': '16px', 'background': COLORS['panel'],
          'borderRadius': '8px', 'minWidth': '120px', 'flex': '1'})
```

#### `make_operational_tab() -> html.Div`
**Docstring:** `Build layout for Operational tab — positions grid + action panel.`
**Returns:**
```
html.Div([
    html.H3("Open Positions"),
    dcc.Loading(id='positions-loading', type='circle', children=[
        dag.AgGrid(id='positions-grid', columnDefs=POSITION_COLUMNS,
                   rowData=[], dashGridOptions={
                       'rowSelection': 'single',
                       'overlayNoRowsTemplate': 'No open positions',
                       'rowClassRules': {
                           'row-long':  {'function': 'params.data.Dir === "LONG"'},
                           'row-short': {'function': 'params.data.Dir === "SHORT"'},
                       }
                   },
                   defaultColDef={'sortable': True, 'resizable': True},
                   className='ag-theme-alpine-dark',
                   style={'height': '300px'}),
    ]),
    html.Div(id='selected-pos-info'),  # shows selected row info
    html.Div(id='pos-action-status',   # shows success/error from actions
             style={'marginTop': '8px', 'color': COLORS['green']}),
])
```

**Selected position action panel** (rendered by callback into `selected-pos-info`):
When a row is selected, show:
```
"Selected: {SYMBOL} {DIRECTION}  |  Entry: {entry}  |  SL: {sl}"
[Raise to Breakeven]   [Move SL to: ____] [Submit]
```
If `be_raised == "Yes"` → disable Raise to Breakeven button (already raised).

#### `make_history_tab() -> html.Div`
**Docstring:** `Build layout for History tab — filterable closed trades grid.`
**Returns:**
```
html.Div([
    html.Div([  # filter row
        dcc.Checklist(id='hist-today-filter', options=[{'label': 'Today only', 'value': 'today'}],
                      value=['today'], inline=True),
        dcc.Dropdown(id='hist-dir-filter', options=['LONG','SHORT'], placeholder='Direction',
                     clearable=True, style={'width':'120px'}),
        dcc.Dropdown(id='hist-grade-filter', options=['A','B','C'], placeholder='Grade',
                     clearable=True, style={'width':'100px'}),
        dcc.Dropdown(id='hist-exit-filter',
                     options=['SL_HIT','TP_HIT','EXIT_UNKNOWN','SL_HIT_ASSUMED'],
                     placeholder='Exit Reason', clearable=True, style={'width':'160px'}),
    ], style={'display':'flex', 'gap':'12px', 'alignItems':'center', 'marginBottom':'12px'}),
    dag.AgGrid(id='history-grid', columnDefs=HISTORY_COLUMNS, rowData=[],
               defaultColDef={'sortable': True, 'filter': True, 'resizable': True},
               dashGridOptions={'pagination': True, 'paginationPageSize': 50},
               className='ag-theme-alpine-dark', style={'height': '500px'}),
    html.Div(id='history-summary', style={'color': COLORS['muted'], 'marginTop': '8px'}),
])
```

#### `make_analytics_tab() -> html.Div`
**Docstring:** `Build layout for Analytics tab — metrics, charts, grade comparison.`
**Returns:**
```
html.Div([
    html.Div(id='analytics-metric-cards',
             style={'display':'flex', 'gap':'12px', 'flexWrap':'wrap', 'marginBottom':'16px'}),
    html.Div([
        dcc.Graph(id='equity-chart', style={'flex':'1'}),
        dcc.Graph(id='drawdown-chart', style={'flex':'1'}),
    ], style={'display':'flex', 'gap':'12px', 'marginBottom':'16px'}),
    html.Div([
        dcc.Graph(id='exit-reason-chart', style={'flex':'1'}),
        dcc.Graph(id='daily-pnl-chart', style={'flex':'1'}),
    ], style={'display':'flex', 'gap':'12px', 'marginBottom':'16px'}),
    html.H4("Grade A vs Grade B"),
    html.Div(id='grade-comparison-table'),
])
```

#### `make_coin_summary_tab() -> html.Div`
**Docstring:** `Build layout for Coin Summary tab — per-coin stats grid.`
**Returns:**
```
html.Div([
    dcc.RadioItems(id='coin-period-filter',
                   options=[
                       {'label': 'All time', 'value': 'all'},
                       {'label': 'Last 7 days', 'value': '7d'},
                       {'label': 'This week', 'value': 'week'},
                   ],
                   value='all', inline=True, style={'marginBottom': '12px'}),
    dag.AgGrid(id='coin-summary-grid', columnDefs=COIN_COLUMNS, rowData=[],
               defaultColDef={'sortable': True, 'resizable': True},
               dashGridOptions={'pagination': True, 'paginationPageSize': 50},
               className='ag-theme-alpine-dark', style={'height': '600px'}),
    html.Div(id='coin-summary-caption', style={'color': COLORS['muted'], 'marginTop': '8px'}),
])
```

#### `make_bot_controls_tab() -> html.Div`
**Docstring:** `Build layout for Bot Controls tab — config editor and bot restart.`

Layout structure (see full spec in Bot Controls Callbacks section below).

---

## AG-Grid Column Definitions

### POSITION_COLUMNS
```python
POSITION_COLUMNS = [
    {'field': 'Symbol',     'pinned': 'left', 'width': 120},
    {'field': 'Dir',        'width': 70,
     'cellStyle': {'function': '(p) => ({color: p.value==="LONG" ? "#3fb950" : "#f85149", fontWeight:"bold"})'}},
    {'field': 'Grade',      'width': 70},
    {'field': 'Entry',      'width': 110, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(6)'}},
    {'field': 'Stop Loss',  'width': 110, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(6)'}},
    {'field': 'Take Profit','width': 110},
    {'field': 'BE Raised',  'width': 90,
     'cellStyle': {'function': '(p) => ({color: p.value==="Yes" ? "#3fb950" : "#8b949e"})'}},
    {'field': 'Unreal PnL', 'width': 110, 'type': 'numericColumn',
     'cellStyle': {'function': '(p) => p.value == null ? {} : ({color: p.value >= 0 ? "#3fb950" : "#f85149", fontWeight:"bold"})'},
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(4) : "—"'}},
    {'field': 'Dist SL %',  'width': 90, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(2)+"%" : "—"'}},
    {'field': 'Duration',   'width': 90},
    {'field': 'Notional',   'width': 90, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(2)'}},
    {'field': 'order_id',   'hide': True},  # hidden, used by action callbacks
]
```

### HISTORY_COLUMNS
```python
HISTORY_COLUMNS = [
    {'field': 'Date',        'width': 120, 'pinned': 'left'},
    {'field': 'Symbol',      'width': 110},
    {'field': 'Dir',         'width': 70},
    {'field': 'Grade',       'width': 70,  'filter': True},
    {'field': 'Entry',       'width': 100, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(6)'}},
    {'field': 'Exit',        'width': 100, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(6) : "—"'}},
    {'field': 'Exit Reason', 'width': 130, 'filter': True,
     'cellStyle': {'function': '''(p) => ({
         color: p.value==="TP_HIT" ? "#3fb950" :
                p.value==="SL_HIT" ? "#f85149" : "#d29922"
     })'''}},
    {'field': 'Net PnL',     'width': 100, 'type': 'numericColumn',
     'cellStyle': {'function': '(p) => ({color: p.value >= 0 ? "#3fb950" : "#f85149", fontWeight:"bold"})'},
     'valueFormatter': {'function': 'params.value.toFixed(4)'}},
    {'field': 'Duration',    'width': 90},
    {'field': 'Notional',    'width': 90,  'type': 'numericColumn'},
]
```

### COIN_COLUMNS
```python
COIN_COLUMNS = [
    {'field': 'Symbol',    'pinned': 'left', 'width': 120},
    {'field': 'Trades',    'width': 80,  'type': 'numericColumn'},
    {'field': 'WR %',      'width': 80,  'type': 'numericColumn'},
    {'field': 'Net PnL',   'width': 100, 'type': 'numericColumn',
     'cellStyle': {'function': '(p) => ({color: p.value >= 0 ? "#3fb950" : "#f85149", fontWeight:"bold"})'},
     'valueFormatter': {'function': 'params.value.toFixed(4)'}},
    {'field': 'Avg PnL',   'width': 90,  'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(4)'}},
    {'field': 'SL %',      'width': 70,  'type': 'numericColumn'},
    {'field': 'TP %',      'width': 70,  'type': 'numericColumn'},
    {'field': 'Unknown %', 'width': 90,  'type': 'numericColumn'},
    {'field': 'Best',      'width': 90,  'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(4)'}},
    {'field': 'Worst',     'width': 90,  'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(4)'}},
]
```

---

## Complete Callback Inventory

All use `from dash import callback` (Dash 4.0 pattern). `@app.callback` is legacy.
All have `prevent_initial_call=True` unless explicitly noted otherwise.
All have one-line docstrings.

---

### CB-1: Data Loader
```python
@callback(
    Output('store-state',  'data'),
    Output('store-trades', 'data'),
    Output('store-config', 'data'),
    Input('refresh-interval', 'n_intervals'),
)
def load_all_data(n_intervals):
    """Load state.json, trades.csv, config.yaml into stores on each interval tick."""
```
**Logic:**
- Call `load_state()` → `json.dumps(result)`
- Call `load_trades()` → `.to_json(orient='split', date_format='iso')`
- Call `load_config()` → `json.dumps(result)`
- Return all three
- `prevent_initial_call=False` — MUST fire on load to populate stores before tabs render

---

### CB-2: Tab Content Renderer
```python
@callback(
    Output('tab-content', 'children'),
    Input('main-tabs', 'value'),
    prevent_initial_call=False,
)
def render_tab(tab_value):
    """Return layout for the selected tab."""
```
**Logic:**
- `if tab_value == 'tab-ops':      return make_operational_tab()`
- `if tab_value == 'tab-hist':     return make_history_tab()`
- `if tab_value == 'tab-analytics':return make_analytics_tab()`
- `if tab_value == 'tab-coins':    return make_coin_summary_tab()`
- `if tab_value == 'tab-controls': return make_bot_controls_tab()`
- `return html.Div("Unknown tab")`

---

### CB-3: Status Bar
```python
@callback(
    Output('status-bar', 'children'),
    Input('store-state',  'data'),
    Input('store-config', 'data'),
)
def update_status_bar(state_json, config_json):
    """Render top status bar with bot mode, daily PnL, positions, risk usage."""
```
**Logic:**
- Parse: `state = json.loads(state_json)`, `cfg = json.loads(config_json)`
- `halt_flag = state.get("halt_flag", False)`
- `demo_mode = cfg.get("connector", {}).get("demo_mode", True)`
- `daily_pnl = float(state.get("daily_pnl", 0.0))`
- `open_count = len(state.get("open_positions", {}))`
- `daily_trades = int(state.get("daily_trades", 0))`
- `max_positions = cfg.get("risk", {}).get("max_positions", 8)`
- `max_daily_trades = cfg.get("risk", {}).get("max_daily_trades", 50)`
- `daily_loss_limit = cfg.get("risk", {}).get("daily_loss_limit_usd", 15.0)`
- `risk_pct = round(abs(daily_pnl) / daily_loss_limit * 100, 1) if daily_loss_limit > 0 else 0.0`
- Status: `"HALTED"` (red) if halt_flag, `"DEMO"` (blue) if demo_mode, `"LIVE"` (green) otherwise
- PnL color: green if >= 0 else red
- Return `html.Div([...cards...], style={'display':'flex', 'gap':'12px', 'padding':'12px', 'background':COLORS['panel'], 'borderBottom':f'1px solid {COLORS["grid"]}'})`
- Cards: Status | Daily PnL | Positions (n/max) | Daily Trades (n/max) | Risk Used (n%) | Last refresh time

---

### CB-4: Positions Grid
```python
@callback(
    Output('positions-grid', 'rowData'),
    Input('store-state', 'data'),
    prevent_initial_call=True,
)
def update_positions_grid(state_json):
    """Load open positions with live mark prices into ag-grid."""
```
**Logic:**
- `state = json.loads(state_json)`
- `positions = state.get("open_positions", {})`
- If empty → return `[]`
- `symbols = [p["symbol"] for p in positions.values()]`
- `mark_prices = fetch_all_mark_prices(symbols)` (parallel, 8 workers)
- `pos_df = build_positions_df(state, mark_prices)`
- If empty → return `[]`
- Return `pos_df.to_dict('records')`

---

### CB-5: Selected Position Info
```python
@callback(
    Output('selected-pos-info', 'children'),
    Input('positions-grid', 'selectedRows'),
    prevent_initial_call=True,
)
def show_selected_position(selected_rows):
    """Render action panel for the selected position row."""
```
**Logic:**
- If not selected_rows → return `html.Div("Select a position to manage it.", style={'color': COLORS['muted']})`
- `row = selected_rows[0]`
- `be_already_raised = row.get("BE Raised") == "Yes"`
- Return `html.Div([` with:
  - Info line: `f"{row['Symbol']} {row['Dir']}  |  Entry: {row['Entry']}  |  SL: {row['Stop Loss']}"`
  - `html.Button("Raise to Breakeven", id="raise-be-btn", n_clicks=0, disabled=be_already_raised)`
  - `dcc.Input(id="new-sl-input", type="number", placeholder="New SL price", debounce=True)`
  - `html.Button("Move SL", id="move-sl-btn", n_clicks=0)`
  - Hidden `html.Div(id="selected-symbol", children=row["Symbol"], style={"display":"none"})`

---

### CB-6: Raise to Breakeven
```python
@callback(
    Output('pos-action-status', 'children'),
    Input('raise-be-btn', 'n_clicks'),
    State('positions-grid', 'selectedRows'),
    State('store-state', 'data'),
    prevent_initial_call=True,
)
def raise_breakeven(n_clicks, selected_rows, state_json):
    """Cancel SL order and place new STOP_MARKET at entry price for selected position."""
```
**Logic:**
- If not n_clicks or not selected_rows → `raise PreventUpdate`
- `row = selected_rows[0]`
- `symbol = row["Symbol"]`, `direction = row["Dir"]`, `entry_price = row["Entry"]`
- `position_side = "LONG" if direction == "LONG" else "SHORT"`
- Step 1: GET open orders for symbol
  ```
  data = _bingx_request('GET', '/openApi/swap/v2/trade/openOrders',
                         {'symbol': symbol})
  ```
  If error → return `f"Error fetching orders: {data['error']}"`
- Step 2: Find SL order (type STOP_MARKET, reduceOnly=True or side opposite to direction)
  - Orders in `data.get("orders", [])`
  - SL order: `type == "STOP_MARKET"` and `reduceOnly == True`
  - If no SL order found → return `"No SL order found for {symbol}"`
- Step 3: Cancel SL order
  ```
  cancel_result = _bingx_request('DELETE', '/openApi/swap/v2/trade/order',
                                  {'symbol': symbol, 'orderId': sl_order["orderId"]})
  ```
  If error → return `f"Cancel failed: {cancel_result['error']}"`
- Step 4: Place new STOP_MARKET at entry_price
  ```
  place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
      'symbol': symbol,
      'side': 'SELL' if direction == 'LONG' else 'BUY',
      'positionSide': position_side,
      'type': 'STOP_MARKET',
      'stopPrice': str(entry_price),
      'quantity': str(row.get('quantity', 0)),
      'reduceOnly': 'true',
      'workingType': 'MARK_PRICE',
  })
  ```
  If error → return `f"Place failed: {place_result['error']}"`
- Step 5: Update state.json — write `be_raised=True` and `sl_price=entry_price` for this position
  - Read state.json, find position key matching symbol+direction, update, atomic write
  - Use tmp file + `os.replace()` pattern
- Return `f"BE raised for {symbol} — SL moved to {entry_price}"`

---

### CB-7: Move SL
```python
@callback(
    Output('pos-action-status', 'children'),
    Input('move-sl-btn', 'n_clicks'),
    State('positions-grid', 'selectedRows'),
    State('new-sl-input', 'value'),
    prevent_initial_call=True,
)
def move_sl(n_clicks, selected_rows, new_sl_price):
    """Cancel existing SL and place new STOP_MARKET at user-specified price."""
```
**Logic:**
- Guard: not n_clicks or not selected_rows or new_sl_price is None → `raise PreventUpdate`
- `row = selected_rows[0]`
- `symbol = row["Symbol"]`, `direction = row["Dir"]`
- `new_sl = float(new_sl_price)`
- Validate direction: if LONG and new_sl >= row["Entry"] → return `"Invalid: LONG SL must be below entry price"`
- Validate direction: if SHORT and new_sl <= row["Entry"] → return `"Invalid: SHORT SL must be above entry price"`
- Same cancel + place flow as CB-6, but `stopPrice = str(new_sl)` instead of entry_price
- Update state.json: `sl_price = new_sl` for this position
- Return `f"SL moved to {new_sl} for {symbol}"`

**Note:** CB-6 and CB-7 both write to `Output('pos-action-status', 'children')`. This is allowed in Dash only if they are in DIFFERENT callbacks with different Inputs. They are — CB-6 triggers on `raise-be-btn`, CB-7 on `move-sl-btn`.

---

### CB-8: History Grid
```python
@callback(
    Output('history-grid', 'rowData'),
    Output('history-summary', 'children'),
    Input('hist-today-filter', 'value'),
    Input('hist-dir-filter', 'value'),
    Input('hist-grade-filter', 'value'),
    Input('hist-exit-filter', 'value'),
    State('store-trades', 'data'),
    prevent_initial_call=True,
)
def update_history_grid(today_filter, dir_filter, grade_filter, exit_filter, trades_json):
    """Filter and render closed trades into history ag-grid."""
```
**Logic:**
- If not trades_json → return `[], "No trade data"`
- `df = pd.read_json(trades_json, orient='split')`
- `df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")`
- `df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")`
- Apply filters:
  - `if 'today' in (today_filter or []):` → filter to today UTC date
  - `if dir_filter:` → `df = df[df.direction == dir_filter]`
  - `if grade_filter:` → `df = df[df.grade == grade_filter]`
  - `if exit_filter:` → `df = df[df.exit_reason == exit_filter]`
- If df empty → return `[], "No trades match filters"`
- Add display columns:
  - `df["Date"] = df["timestamp"].dt.strftime("%m-%d %H:%M")`
  - `df["Duration"] = df.apply(lambda r: fmt_duration(r["entry_time"], r["timestamp"]), axis=1)`
  - `df["Notional"] = pd.to_numeric(df["notional_usd"], errors='coerce')`
- Rename: `symbol→Symbol, direction→Dir, grade→Grade, entry_price→Entry, exit_price→Exit, exit_reason→Exit Reason, pnl_net→Net PnL`
- `total_pnl = round(float(df["Net PnL"].sum()), 4)`
- `pnl_color = COLORS['green'] if total_pnl >= 0 else COLORS['red']`
- Summary: `html.Span(f"{len(df)} trades | Total PnL: {total_pnl:+.4f}", style={'color': pnl_color})`
- Return `df[display_cols].to_dict('records'), summary`

---

### CB-9: Analytics Update
```python
@callback(
    Output('analytics-metric-cards', 'children'),
    Output('equity-chart',           'figure'),
    Output('drawdown-chart',         'figure'),
    Output('exit-reason-chart',      'figure'),
    Output('daily-pnl-chart',        'figure'),
    Output('grade-comparison-table', 'children'),
    Input('store-trades', 'data'),
    prevent_initial_call=True,
)
def update_analytics(trades_json):
    """Compute all analytics from trades store and render all analytics tab components."""
```
**Logic:**
- If not trades_json → return 6x placeholder/empty components
- `df = pd.read_json(trades_json, orient='split')`
- Parse timestamps
- `metrics = compute_metrics(df)`
- Metric cards row: `[build_metric_card(...) for ...]` using metrics dict
  - Cards: Win Rate, Profit Factor, Expectancy, Avg Win, Avg Loss, Max DD, Total Trades
  - PnL-related cards: green color if positive, red if negative
- `equity_fig = build_equity_figure(df)`
- `dd_fig = build_drawdown_figure(df)`
- `exit_fig = build_exit_reason_figure(df)`
- `daily_fig = build_daily_pnl_figure(df)`
- Grade comparison: `group = df.groupby("grade")` → compute WR/PnL/PF/Expectancy per grade → return `dag.AgGrid` with grade stats
- Return all 6 outputs

---

### CB-10: Coin Summary
```python
@callback(
    Output('coin-summary-grid',    'rowData'),
    Output('coin-summary-caption', 'children'),
    Input('coin-period-filter',    'value'),
    State('store-trades',          'data'),
    prevent_initial_call=True,
)
def update_coin_summary(period_filter, trades_json):
    """Filter trades by period and render per-coin summary grid."""
```
**Logic:**
- If not trades_json → return `[], ""`
- `df = pd.read_json(trades_json, orient='split')`
- Parse `df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")`
- Apply period filter:
  - `'7d'` → `df = df[df.timestamp >= pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)]`
  - `'week'` → filter to current ISO week
  - `'all'` → no filter
- `records = build_coin_summary(df)`
- Caption: `f"{len(records)} coins in history"`
- Return `records, caption`

---

### CB-11: Load Config Into Controls
```python
@callback(
    Output('ctrl-sl-atr-mult',        'value'),
    Output('ctrl-tp-atr-mult',        'value'),
    Output('ctrl-require-stage2',     'value'),
    Output('ctrl-rot-level',          'value'),
    Output('ctrl-allow-a',            'value'),
    Output('ctrl-allow-b',            'value'),
    Output('ctrl-max-positions',      'value'),
    Output('ctrl-max-daily-trades',   'value'),
    Output('ctrl-daily-loss-limit',   'value'),
    Output('ctrl-min-atr-ratio',      'value'),
    Output('ctrl-cooldown-bars',      'value'),
    Output('ctrl-margin-usd',         'value'),
    Output('ctrl-leverage',           'value'),
    Input('store-config', 'data'),
    prevent_initial_call=True,
)
def load_config_into_controls(config_json):
    """Populate Bot Controls form fields from current config.yaml values."""
```
**Logic:**
- `cfg = json.loads(config_json)`
- `fp = cfg.get("four_pillars", {})`
- `risk = cfg.get("risk", {})`
- `pos = cfg.get("position", {})`
- Return each value from config with sensible defaults if key missing

---

### CB-12: Save Config
```python
@callback(
    Output('save-config-status', 'children'),
    Input('save-config-btn', 'n_clicks'),
    State('ctrl-sl-atr-mult',        'value'),
    State('ctrl-tp-atr-mult',        'value'),
    State('ctrl-require-stage2',     'value'),
    State('ctrl-rot-level',          'value'),
    State('ctrl-allow-a',            'value'),
    State('ctrl-allow-b',            'value'),
    State('ctrl-max-positions',      'value'),
    State('ctrl-max-daily-trades',   'value'),
    State('ctrl-daily-loss-limit',   'value'),
    State('ctrl-min-atr-ratio',      'value'),
    State('ctrl-cooldown-bars',      'value'),
    State('ctrl-margin-usd',         'value'),
    State('ctrl-leverage',           'value'),
    prevent_initial_call=True,
)
def save_config(n_clicks, sl_mult, tp_mult, req_s2, rot_lvl,
                allow_a, allow_b, max_pos, max_trades,
                loss_limit, min_atr, cooldown, margin, leverage):
    """Validate inputs and write updated values to config.yaml atomically."""
```
**Logic:**
- Call `validate_config_updates(updates)` — see below. If invalid → return error message
- `cfg = load_config()` — read current (preserves coins list and other untouched keys)
- Build `updates` dict from form values:
  - `cfg["four_pillars"]["sl_atr_mult"] = float(sl_mult)`
  - `cfg["four_pillars"]["tp_atr_mult"] = float(tp_mult) if tp_mult else None`
  - `cfg["four_pillars"]["require_stage2"] = (req_s2 == "true")`
  - `cfg["four_pillars"]["rot_level"] = int(rot_lvl)`
  - `cfg["four_pillars"]["allow_a"] = (allow_a == "true")`
  - `cfg["four_pillars"]["allow_b"] = (allow_b == "true")`
  - `cfg["risk"]["max_positions"] = int(max_pos)`
  - `cfg["risk"]["max_daily_trades"] = int(max_trades)`
  - `cfg["risk"]["daily_loss_limit_usd"] = float(loss_limit)`
  - `cfg["risk"]["min_atr_ratio"] = float(min_atr)`
  - `cfg["risk"]["cooldown_bars"] = int(cooldown)`
  - `cfg["position"]["margin_usd"] = float(margin)`
  - `cfg["position"]["leverage"] = int(leverage)`
- Atomic write: `tmp = CONFIG_PATH.with_suffix('.yaml.tmp')` → `yaml.dump(cfg, f)` → `os.replace(tmp, CONFIG_PATH)`
- Build diff message: compare original vs new for each key
- Restart-required notice: if margin_usd or leverage changed → append "Restart bot to apply: margin_usd, leverage"
- Return diff message

#### `validate_config_updates(updates: dict) -> tuple[bool, str]`
**Docstring:** `Validate config form values before writing. Returns (is_valid, error_message).`
**Rules:**
- `sl_atr_mult` must be float > 0 and <= 10
- `tp_atr_mult` if not null must be float > 0
- `rot_level` must be int 50–95
- `max_positions` must be int 1–50
- `max_daily_trades` must be int 1–200
- `daily_loss_limit_usd` must be float > 0
- `min_atr_ratio` must be float 0.0001–0.05
- `cooldown_bars` must be int 0–20
- `margin_usd` must be float > 0
- `leverage` must be int 1–125
- Return `(False, "Error: {field} {reason}")` on first failure
- Return `(True, "")` if all valid

---

### CB-13: Halt Bot
```python
@callback(
    Output('halt-status', 'children'),
    Input('halt-bot-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def halt_bot(n_clicks):
    """Write halt_flag=True to state.json. Bot checks this on next loop (max 60s delay)."""
```
**Logic:**
- Read `state.json` → parse → set `halt_flag = True` → atomic write (tmp + os.replace)
- Return `html.Span("Bot halted — will stop accepting new trades on next loop.", style={'color': COLORS['red']})`

---

### CB-14: Resume Bot
```python
@callback(
    Output('halt-status', 'children'),
    Input('resume-bot-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def resume_bot(n_clicks):
    """Write halt_flag=False to state.json."""
```
**Logic:**
- Read state.json → set `halt_flag = False` → atomic write
- Return `html.Span("Bot resumed.", style={'color': COLORS['green']})`

---

## Bot Controls Tab Layout Detail

```python
def make_bot_controls_tab():
    """Build layout for Bot Controls tab — config editor and halt/resume."""
    return html.Div([
        # Warning banner
        html.Div([
            html.Strong("LIVE BOT CONTROL"),
            html.Span(" — Changes to Strategy and Risk take effect on the next bot loop. "
                      "Parameters marked (*) require bot restart."),
        ], className='warning-banner', style={'marginBottom': '16px'}),

        # Strategy section
        html.H4("Strategy Parameters"),
        html.Div([
            html.Label("SL ATR Mult"),
            dcc.Input(id='ctrl-sl-atr-mult', type='number', step=0.1, min=0.1, max=10),
            html.Label("TP ATR Mult (null = trailing)"),
            dcc.Input(id='ctrl-tp-atr-mult', type='number', step=0.5, min=0, max=20,
                      placeholder='null'),
            html.Label("Require Stage 2"),
            dcc.RadioItems(id='ctrl-require-stage2',
                           options=[{'label':'Yes','value':'true'},
                                    {'label':'No', 'value':'false'}], inline=True),
            html.Label("Rotation Level"),
            dcc.Input(id='ctrl-rot-level', type='number', min=50, max=95, step=1),
            html.Label("Allow Grade A"),
            dcc.RadioItems(id='ctrl-allow-a',
                           options=[{'label':'Yes','value':'true'},
                                    {'label':'No', 'value':'false'}], inline=True),
            html.Label("Allow Grade B"),
            dcc.RadioItems(id='ctrl-allow-b',
                           options=[{'label':'Yes','value':'true'},
                                    {'label':'No', 'value':'false'}], inline=True),
        ], style={'display':'grid', 'gridTemplateColumns':'200px 1fr', 'gap':'8px',
                  'alignItems':'center', 'maxWidth':'500px', 'marginBottom':'16px'}),

        # Risk section
        html.H4("Risk Limits"),
        html.Div([
            html.Label("Max Positions"),
            dcc.Input(id='ctrl-max-positions', type='number', min=1, max=50, step=1),
            html.Label("Max Daily Trades"),
            dcc.Input(id='ctrl-max-daily-trades', type='number', min=1, max=200, step=1),
            html.Label("Daily Loss Limit ($)"),
            dcc.Input(id='ctrl-daily-loss-limit', type='number', min=1, step=0.5),
            html.Label("Min ATR Ratio"),
            dcc.Input(id='ctrl-min-atr-ratio', type='number', step=0.0005, min=0.0001),
            html.Label("Cooldown Bars"),
            dcc.Input(id='ctrl-cooldown-bars', type='number', min=0, max=20, step=1),
        ], style={'display':'grid', 'gridTemplateColumns':'200px 1fr', 'gap':'8px',
                  'alignItems':'center', 'maxWidth':'500px', 'marginBottom':'16px'}),

        # Position sizing — restart required
        html.H4("Position Sizing (*restart required)"),
        html.Div([
            html.Label("Margin per Trade ($)"),
            dcc.Input(id='ctrl-margin-usd', type='number', min=1, step=1),
            html.Label("Leverage"),
            dcc.Input(id='ctrl-leverage', type='number', min=1, max=125, step=1),
        ], style={'display':'grid', 'gridTemplateColumns':'200px 1fr', 'gap':'8px',
                  'alignItems':'center', 'maxWidth':'500px', 'marginBottom':'16px'}),

        html.Div([
            html.Button("Save Config", id='save-config-btn', n_clicks=0,
                        style={'marginRight':'8px', 'background': COLORS['blue'],
                               'color':'white', 'border':'none', 'padding':'8px 16px',
                               'borderRadius':'4px', 'cursor':'pointer'}),
            html.Button("Discard",     id='discard-config-btn', n_clicks=0,
                        style={'background': COLORS['grid'], 'color': COLORS['text'],
                               'border':'none', 'padding':'8px 16px',
                               'borderRadius':'4px', 'cursor':'pointer'}),
        ], style={'marginBottom': '12px'}),
        html.Div(id='save-config-status', style={'marginBottom': '24px'}),

        html.Hr(style={'borderColor': COLORS['grid']}),

        # Bot halt/resume
        html.H4("Bot Control"),
        html.P("Halt stops the bot from opening new trades. Open positions are not affected.",
               style={'color': COLORS['muted']}),
        html.Div([
            html.Button("Halt Bot",   id='halt-bot-btn',   n_clicks=0,
                        style={'marginRight':'8px', 'background': COLORS['red'],
                               'color':'white', 'border':'none', 'padding':'8px 16px',
                               'borderRadius':'4px', 'cursor':'pointer'}),
            html.Button("Resume Bot", id='resume-bot-btn', n_clicks=0,
                        style={'background': COLORS['green'], 'color':'white',
                               'border':'none', 'padding':'8px 16px',
                               'borderRadius':'4px', 'cursor':'pointer'}),
        ], style={'marginBottom': '8px'}),
        html.Div(id='halt-status'),
    ])
```

---

## assets/dashboard.css

Full content of the CSS file at `PROJECTS/bingx-connector/assets/dashboard.css`:

```css
body {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Consolas', 'Monaco', monospace;
    margin: 0;
}

.row-long  { background-color: rgba(63, 185, 80,  0.05) !important; }
.row-short { background-color: rgba(248, 81, 73, 0.05) !important; }

.warning-banner {
    background-color: rgba(248, 81, 73, 0.10);
    border: 1px solid #f85149;
    padding: 12px 16px;
    border-radius: 4px;
    color: #c9d1d9;
}

/* Dash core tab styling */
.dash-tabs { background-color: #0d1117; }
.dash-tab  { background-color: #161b22 !important; color: #8b949e !important;
             border: 1px solid #21262d !important; }
.dash-tab--selected { background-color: #0d1117 !important; color: #c9d1d9 !important;
                      border-bottom: 2px solid #58a6ff !important; }

/* Loading spinner dark background */
._dash-loading { background-color: rgba(13, 17, 23, 0.8); }
```

---

## App Entry Point

```python
if __name__ == '__main__':
    app.run(debug=False, port=8051, host='127.0.0.1')
```

`debug=False` in the main guard. If debug=True is used during development, change it manually — never leave it as default True.

`server = app.server` must be at module level (line immediately after `app = dash.Dash(...)`).

---

## py_compile Validation

```bash
python -c "import py_compile; py_compile.compile('bingx-live-dashboard-v1-1.py', doraise=True)"
```

Must pass before running.

---

## Verification Checklist

Run these after the build is complete:

1. `py_compile` passes — no syntax errors
2. `python bingx-live-dashboard-v1-1.py` starts without error, prints `Dash is running on http://127.0.0.1:8051/`
3. Open `http://localhost:8051` — page loads, status bar visible
4. **Operational tab:** grid loads (or shows "No open positions" overlay), no JS errors in browser console
5. **History tab:** filter row visible, grid renders (may be empty if no trades), "Today only" checked by default
6. **Analytics tab:** all 4 charts render (empty figure if no data), metric cards show zeros not errors
7. **Coin Summary tab:** grid renders, period radio buttons work
8. **Bot Controls tab:** form fields show current config values on load
9. **Save Config:** change sl_atr_mult to 2.2, click Save → verify config.yaml updated, diff shown
10. **Halt Bot:** click Halt → verify `state.json` `halt_flag: true` → click Resume → verify `false`
11. **Auto-refresh:** wait 65s — verify status bar "Last refresh" timestamp updates without page reload
12. **Position action (if positions open):** select a row → action panel appears → Raise BE button visible

---

## What Is NOT in This Build

- Signal Monitor tab (Type 8) — log file tailing — deferred P2
- Coins list editor — deferred (complex YAML list, separate feature)
- BasicAuth login — add before deploying to VPS port 8051
- nginx reverse proxy config — separate ops task
- `demo_mode` toggle — omitted intentionally (too dangerous to toggle without confirmation flow)

---

## Logging Specification

MEMORY.md rule: every script MUST persist errors and output.
Dashboard log file: `logs/YYYY-MM-DD-dashboard.log`

```python
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

LOG_DIR = BASE_DIR / "logs"

def setup_logging() -> logging.Logger:
    """Configure dual-handler logger (file + console) for the dashboard."""
    LOG_DIR.mkdir(exist_ok=True)
    log_path = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}-dashboard.log"

    logger = logging.getLogger("bingx_dashboard")
    logger.setLevel(logging.DEBUG)

    # File handler — rotates at midnight, keeps 30 days
    fh = TimedRotatingFileHandler(
        log_path, when="midnight", backupCount=30, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s UTC | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    ))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

LOG = setup_logging()
```

Call `setup_logging()` at module level immediately after constants. Assign result to `LOG`.

**What gets logged:**

| Event | Level | Message format |
|---|---|---|
| App startup | INFO | `Dashboard starting on port 8051` |
| Data load (60s tick) | DEBUG | `Data loaded: {N} positions, {M} trades` |
| Mark price fetch | DEBUG | `Mark prices fetched: {N}/{total} symbols` |
| API call (Raise BE) | INFO | `Raise BE: {symbol} {direction}` |
| API call (Move SL) | INFO | `Move SL: {symbol} new_sl={price}` |
| API success | INFO | `{action} success: {symbol}` |
| API error | ERROR | `{action} failed: {error_msg}` |
| Save Config | INFO | `Config saved: {diff_summary}` |
| Config write error | ERROR | `Config write failed: {error_msg}` |
| Halt/Resume | INFO | `Bot halt_flag set to {value}` |
| state.json write error | ERROR | `State write failed: {error_msg}` |
| Any unhandled exception | ERROR | `Unhandled in {callback_name}: {traceback}` |

---

## Error Catching Rules — Every Callback

**Rule:** Every callback body is wrapped in `try/except Exception`. On exception:
1. Log with `LOG.error(f"Error in {cb_name}: {e}", exc_info=True)`
2. Return a visible error message to the UI — never let Dash show "Internal server error"
3. Never re-raise in a callback

**Standard error return pattern per output type:**

```python
# Output is a grid rowData list:
except Exception as e:
    LOG.error(f"Error loading positions: {e}", exc_info=True)
    return []

# Output is a figure:
except Exception as e:
    LOG.error(f"Error building equity chart: {e}", exc_info=True)
    return go.Figure().update_layout(
        paper_bgcolor=COLORS['bg'],
        annotations=[dict(text=f"Error: {e}", x=0.5, y=0.5,
                          showarrow=False, font=dict(color=COLORS['red']))]
    )

# Output is html children:
except Exception as e:
    LOG.error(f"Error in {cb_name}: {e}", exc_info=True)
    return html.Div(f"Error: {e}", style={'color': COLORS['red']})

# Output is dcc.Store data:
except Exception as e:
    LOG.error(f"Data load error: {e}", exc_info=True)
    return no_update
```

**API callback error pattern (CB-6, CB-7):**

```python
def raise_breakeven(n_clicks, selected_rows, state_json):
    """Cancel SL order and place new STOP_MARKET at entry price."""
    try:
        if not n_clicks or not selected_rows:
            raise PreventUpdate
        # ... main logic ...
        LOG.info(f"Raise BE success: {symbol}")
        return html.Span(f"BE raised for {symbol}", style={'color': COLORS['green']})
    except PreventUpdate:
        raise
    except Exception as e:
        LOG.error(f"Raise BE failed for {symbol}: {e}", exc_info=True)
        return html.Span(f"Error: {e}", style={'color': COLORS['red']})
```

Note: `PreventUpdate` must be re-raised — never catch it in the outer except.

**File write error pattern (save_config, halt_bot, resume_bot):**

```python
    except Exception as e:
        LOG.error(f"Config write failed: {e}", exc_info=True)
        return html.Span(f"Write failed: {e}", style={'color': COLORS['red']})
```

---

## Docstring and Comment Rules

**Rule from MEMORY.md:** Every `def` must have a one-line docstring. No exceptions.

**Format:**

```python
def load_state() -> dict:
    """Load state.json. Returns dict with safe defaults if file is missing."""
    # Merge with defaults so missing keys never cause KeyError downstream
    defaults = {...}
    ...
```

**Comment rules:**
- Every non-obvious line gets an inline comment
- Every guard clause (`if not x: return`) gets a comment explaining why
- Every API call gets a comment with the endpoint and purpose
- Every atomic write (tmp + os.replace) gets a comment: `# Atomic write — prevents partial reads by bot`
- Every `prevent_initial_call=True` in a callback gets a comment: `# Do not fire on page load — stores not yet populated`
- Every `no_update` return gets a comment: `# Skip update — nothing changed`
- Every `raise PreventUpdate` gets a comment: `# Guard — button not yet clicked`

---

## Test/Audit Script

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\test_dashboard.py`

This script tests every function in the dashboard without running the Dash server.
Run command:
```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/test_dashboard.py
```

Expected output: all PASS lines, then `All tests passed` or a list of FAIL lines.

**Full test script spec:**

```python
"""
test_dashboard.py

Audit and unit-test script for bingx-live-dashboard-v1-1.py.
Tests: py_compile, data loaders (mock), builders, validators.
Run: python scripts/test_dashboard.py
"""

import sys
import json
import os
import tempfile
import py_compile
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

ERRORS = []
BASE  = Path(__file__).parent.parent  # PROJECTS/bingx-connector/


def check(label: str, cond: bool, detail: str = "") -> None:
    """Record pass or fail for a test assertion."""
    if cond:
        print(f"  PASS  {label}")
    else:
        msg = f"  FAIL  {label}" + (f" — {detail}" if detail else "")
        print(msg)
        ERRORS.append(label)


# -----------------------------------------------------------------------
# 1. py_compile — both files
# -----------------------------------------------------------------------
print("\n[1] py_compile")

for fname in ["bingx-live-dashboard-v1-1.py", "assets/dashboard.css"]:
    path = BASE / fname
    check(f"file exists: {fname}", path.exists(), f"not found at {path}")

try:
    py_compile.compile(str(BASE / "bingx-live-dashboard-v1-1.py"), doraise=True)
    check("py_compile bingx-live-dashboard-v1-1.py", True)
except py_compile.PyCompileError as e:
    check("py_compile bingx-live-dashboard-v1-1.py", False, str(e))

try:
    py_compile.compile(str(Path(__file__)), doraise=True)
    check("py_compile test_dashboard.py", True)
except py_compile.PyCompileError as e:
    check("py_compile test_dashboard.py", False, str(e))


# -----------------------------------------------------------------------
# 2. Import dashboard module (no Dash server starts — just import)
# -----------------------------------------------------------------------
print("\n[2] Import dashboard module")
sys.path.insert(0, str(BASE))
try:
    import bingx_live_dashboard_v1_1 as dash_mod
    check("import dashboard module", True)
except Exception as e:
    check("import dashboard module", False, str(e))
    print("Cannot continue without import. Aborting.")
    sys.exit(1)


# -----------------------------------------------------------------------
# 3. Data loaders — mock files
# -----------------------------------------------------------------------
print("\n[3] Data loaders with mock files")

# 3a. load_state — missing file
original_state_path = dash_mod.STATE_PATH
dash_mod.STATE_PATH = BASE / "nonexistent_state.json"
result = dash_mod.load_state()
check("load_state missing file returns defaults", isinstance(result, dict))
check("load_state has open_positions key", "open_positions" in result)
check("load_state has halt_flag key", "halt_flag" in result)
dash_mod.STATE_PATH = original_state_path

# 3b. load_state — valid file
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

# 3c. load_config — missing file
original_config_path = dash_mod.CONFIG_PATH
dash_mod.CONFIG_PATH = BASE / "nonexistent_config.yaml"
result = dash_mod.load_config()
check("load_config missing file returns empty dict", result == {})
dash_mod.CONFIG_PATH = original_config_path

# 3d. load_trades — missing file
original_trades_path = dash_mod.TRADES_PATH
dash_mod.TRADES_PATH = BASE / "nonexistent_trades.csv"
result = dash_mod.load_trades()
check("load_trades missing file returns empty DataFrame", result.empty)
dash_mod.TRADES_PATH = original_trades_path

# 3e. load_trades — valid file
tmp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w")
tmp_csv.write(
    "timestamp,symbol,direction,grade,entry_price,exit_price,exit_reason,"
    "pnl_net,quantity,notional_usd,entry_time,order_id\n"
    "2026-02-28T10:00:00+00:00,SKR-USDT,LONG,A,0.5,0.55,TP_HIT,"
    "0.025,100,50,2026-02-28T09:00:00+00:00,111\n"
    "2026-02-28T11:00:00+00:00,SKR-USDT,SHORT,B,0.55,0.58,SL_HIT,"
    "-0.015,100,50,2026-02-28T10:30:00+00:00,222\n"
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
print("\n[4] Builder functions")

# 4a. fmt_duration
check("fmt_duration returns em-dash for None start",
      dash_mod.fmt_duration(None) == "—")
from datetime import timedelta
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
print("\n[5] validate_config_updates")

valid_updates = {
    "sl_atr_mult": 2.0, "tp_atr_mult": None, "require_stage2": True,
    "rot_level": 80, "allow_a": True, "allow_b": True,
    "max_positions": 8, "max_daily_trades": 50,
    "daily_loss_limit_usd": 15.0, "min_atr_ratio": 0.003,
    "cooldown_bars": 3, "margin_usd": 5.0, "leverage": 10,
}
ok, err = dash_mod.validate_config_updates(valid_updates)
check("validate_config_updates valid inputs pass", ok, err)

bad = dict(valid_updates); bad["leverage"] = 0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates leverage=0 fails", not ok)

bad = dict(valid_updates); bad["sl_atr_mult"] = -1.0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates negative sl_atr_mult fails", not ok)

bad = dict(valid_updates); bad["daily_loss_limit_usd"] = -5.0
ok, err = dash_mod.validate_config_updates(bad)
check("validate_config_updates negative loss limit fails", not ok)


# -----------------------------------------------------------------------
# 6. Chart builders — smoke test (returns go.Figure without crash)
# -----------------------------------------------------------------------
print("\n[6] Chart builders smoke test")

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
# Cleanup and report
# -----------------------------------------------------------------------
os.unlink(tmp_csv.name)

print("\n" + "="*60)
if ERRORS:
    print("FAILURES: " + ", ".join(ERRORS))
    print(f"{len(ERRORS)} test(s) failed.")
    sys.exit(1)
else:
    print("All tests passed.")
    sys.exit(0)
```

**py_compile of test script itself:**

```bash
python -c "import py_compile; py_compile.compile('scripts/test_dashboard.py', doraise=True)"
```

---

## Complete Execution Flow (Life Run-Through)

Trace every step from `python bingx-live-dashboard-v1-1.py` to a user action.

### Step 1 — Module load (before server starts)

```
python bingx-live-dashboard-v1-1.py
```

Python executes module-level code in order:
1. Imports (`dash, dcc, html, dag, go, pandas, requests, yaml, logging, ...`)
2. Path constants (`BASE_DIR, STATE_PATH, TRADES_PATH, CONFIG_PATH`)
3. Color constants (`COLORS = {...}`)
4. API keys loaded (`load_dotenv()`, `API_KEY = os.getenv(...)`)
5. `LOG = setup_logging()` — log dir created, handlers attached
6. `LOG.info("Dashboard starting on port 8051")`
7. `app = dash.Dash(__name__, suppress_callback_exceptions=True, title='...')`
8. `server = app.server` — Flask server exposed for gunicorn
9. `app.layout = html.Div([...])` — layout tree built (stores + interval + status bar + tabs + content div). No data loaded yet.
10. All `@callback` decorators execute — Dash registers the callback graph
11. `app.run(debug=False, port=8051, host='127.0.0.1')` — server starts

### Step 2 — Browser opens `http://localhost:8051`

1. Browser HTTP GET → Dash serves the HTML shell
2. JavaScript loads → Dash initializes client
3. `dcc.Interval` mounts with `n_intervals=0`
4. **CB-1 fires immediately** (`prevent_initial_call=False`):
   - `load_state()` → reads `state.json`
   - `load_trades()` → reads `trades.csv`, serializes to JSON
   - `load_config()` → reads `config.yaml`
   - All three written to `dcc.Store` components
   - `LOG.debug("Data loaded: 5 positions, 31 trades")`
5. **CB-3 fires** (triggered by store-state and store-config now populated):
   - Parses state, computes status metrics
   - Renders status bar: `LIVE | -$2.45 | 5/8 | 3/50 | 16% risk`
6. **CB-2 fires** (tab value default = 'tab-ops'):
   - Returns `make_operational_tab()` layout into `tab-content`
7. **CB-4 fires** (triggered by store-state now populated):
   - Reads positions from store
   - Calls `fetch_all_mark_prices(5 symbols)` — parallel HTTP, ~1s
   - `LOG.debug("Mark prices fetched: 5/5 symbols")`
   - Calls `build_positions_df(state, mark_prices)`
   - Returns `rowData` to `positions-grid`
   - Grid renders with 5 rows

### Step 3 — User switches to History tab

1. User clicks "History" tab
2. `main-tabs value` changes to `'tab-hist'`
3. **CB-2 fires** → returns `make_history_tab()` layout → renders filter row + empty grid
4. **CB-8 fires** (triggered by filter components rendering with default values):
   - `today_filter = ['today']`, all other filters = None
   - Reads `store-trades`
   - Applies today filter
   - Returns `rowData` to `history-grid`
   - Renders N trades for today
5. User unchecks "Today only" → `hist-today-filter` value changes → **CB-8 fires again** → returns all trades

### Step 4 — User selects a position row (back on Operational tab)

1. User clicks "Operational" tab → CB-2 → renders operational layout
2. User clicks a row in positions grid
3. `positions-grid selectedRows` changes
4. **CB-5 fires**:
   - `row = selected_rows[0]`
   - Checks `be_raised` — if False, Raise BE button enabled; if True, disabled
   - Returns action panel div below grid
5. User sees: `"ELSA-USDT SHORT  |  Entry: 0.084700  |  SL: 0.084700  [Raise to Breakeven (disabled — already raised)]  [Move SL to: ___] [Submit]"`

### Step 5 — User enters new SL price and clicks Move SL

1. User types `0.0850` in `new-sl-input`
2. User clicks "Move SL" button
3. `move-sl-btn n_clicks` increments
4. **CB-7 fires**:
   - `selected_rows` from State → `row = {Symbol: ELSA-USDT, Dir: SHORT, Entry: 0.084700, ...}`
   - `new_sl = 0.0850`
   - Validation: SHORT, new_sl > entry → `0.0850 > 0.084700` → VALID
   - `LOG.info("Move SL: ELSA-USDT SHORT new_sl=0.085")`
   - Step 1: GET open orders for ELSA-USDT → finds STOP_MARKET order id=987654
   - Step 2: DELETE order 987654
   - Step 3: POST new STOP_MARKET at 0.0850
   - Step 4: Read state.json → find ELSA-USDT_SHORT → update `sl_price=0.085` → atomic write
   - `LOG.info("Move SL success: ELSA-USDT")`
   - Returns `html.Span("SL moved to 0.085 for ELSA-USDT", style={'color': COLORS['green']})`
5. Green success message appears below grid
6. Next 60s interval tick → CB-1 fires → refreshes state.json → CB-4 fires → grid refreshes → SL column shows new value

### Step 6 — Auto-refresh at T+60s

1. `dcc.Interval n_intervals` increments to 1
2. **CB-1 fires**:
   - Reads state.json, trades.csv, config.yaml again
   - Updates all three stores
3. **CB-3 fires** (stores changed) → status bar re-renders with fresh data
4. **CB-4 fires** (store-state changed) → positions grid re-fetches mark prices → re-renders
5. No other callbacks fire (tab content, history grid, etc. are not wired to stores directly — only to their own tab-specific inputs)
6. Result: status bar + positions grid updated silently, user sees no page reload

### Step 7 — User changes sl_atr_mult in Bot Controls

1. User clicks "Bot Controls" tab
2. **CB-2** renders controls layout
3. **CB-11 fires** (triggered by store-config):
   - Reads config values → populates form inputs
   - `ctrl-sl-atr-mult` shows `2.0`
4. User clears field, types `2.2`
5. User clicks "Save Config"
6. **CB-12 fires**:
   - All State inputs collected
   - `validate_config_updates(updates)` → passes
   - `load_config()` → current config dict
   - Sets `cfg["four_pillars"]["sl_atr_mult"] = 2.2`
   - Write to `config.yaml.tmp` → `os.replace(tmp, config.yaml)`
   - `LOG.info("Config saved: sl_atr_mult 2.0 → 2.2")`
   - Returns: `"Saved. Changed: sl_atr_mult 2.0 → 2.2"`
7. Next bot loop (up to 45s): bot reads updated config on next restart OR if it hot-reads config

---

## Final File Checklist (new chat must verify)

Before starting build, confirm these files exist at correct paths:

```
PROJECTS/bingx-connector/
├── bingx-live-dashboard-v1-1.py   ← CREATE (this build)
├── assets/
│   └── dashboard.css              ← CREATE (this build)
├── scripts/
│   └── test_dashboard.py          ← CREATE (this build)
├── bingx-live-dashboard-v1.py     ← EXISTS (old Streamlit, do not touch)
├── state.json                     ← EXISTS (live bot writes this)
├── trades.csv                     ← EXISTS (live bot writes this)
├── config.yaml                    ← EXISTS (bot reads this)
├── bingx_auth.py                  ← EXISTS (for API signing)
├── .env                           ← EXISTS (BINGX_API_KEY, BINGX_SECRET_KEY)
└── logs/                          ← CREATED at runtime by dashboard
```

**Cross-check before calling build done:**
- [ ] `py_compile bingx-live-dashboard-v1-1.py` passes
- [ ] `py_compile scripts/test_dashboard.py` passes
- [ ] `python scripts/test_dashboard.py` → "All tests passed"
- [ ] `python bingx-live-dashboard-v1-1.py` starts on 8051 without error
- [ ] `logs/YYYY-MM-DD-dashboard.log` created on startup
- [ ] All 14 callbacks have `prevent_initial_call` set correctly
- [ ] All 14 callbacks have try/except wrapping the body
- [ ] All functions have one-line docstrings
- [ ] No `st.` references anywhere in the file
- [ ] No `import streamlit` anywhere in the file
