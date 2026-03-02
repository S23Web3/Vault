"""
BingX Live Dashboard v1-3

Plotly Dash app — monitors and controls a live BingX futures trading bot.
5 tabs: Operational | History | Analytics | Coin Summary | Bot Controls
Data sources: state.json, trades.csv, config.yaml
Position actions: Raise Breakeven, Move SL (via BingX REST API)

Run:
    cd "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector"
    python bingx-live-dashboard-v1-3.py
    # Opens at http://localhost:8051

Production:
    gunicorn -w 1 -b 0.0.0.0:8051 bingx_live_dashboard_v1_3:server

Dependencies:
    pip install dash dash-ag-grid plotly pandas pyyaml requests python-dotenv
"""

import hashlib
import math
import threading
import webbrowser
import hmac
import io
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import dash
import dash_ag_grid as dag
import pandas as pd
import plotly.graph_objects as go
import requests
import yaml
from dash import Input, Output, State, callback, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
STATE_PATH = BASE_DIR / "state.json"
TRADES_PATH = BASE_DIR / "trades.csv"
CONFIG_PATH = BASE_DIR / "config.yaml"
LOG_DIR = BASE_DIR / "logs"

BINGX_PRICE_URL = "https://open-api.bingx.com/openApi/swap/v2/quote/price"

# ---------------------------------------------------------------------------
# Color constants — referenced everywhere, never hardcode hex inline
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Tab styling constants -- inline styles bypass CSS class name issues
# ---------------------------------------------------------------------------

TAB_STYLE = {
    'backgroundColor': '#161b22', 'color': '#8b949e',
    'border': '1px solid #21262d', 'borderBottom': 'none',
    'padding': '10px 20px', 'cursor': 'pointer',
}

TAB_SELECTED_STYLE = {
    'backgroundColor': '#0d1117', 'color': '#58a6ff',
    'border': '1px solid #21262d', 'borderBottom': '2px solid #58a6ff',
    'padding': '10px 20px', 'fontWeight': 'bold',
}

# ---------------------------------------------------------------------------
# API keys
# ---------------------------------------------------------------------------

load_dotenv()
API_KEY = os.getenv('BINGX_API_KEY', '')
SECRET_KEY = os.getenv('BINGX_SECRET_KEY', '')
BASE_URL = 'https://open-api.bingx.com'  # live API, not VST

# ---------------------------------------------------------------------------
# Logging — dual handler (file + console), TimedRotatingFileHandler
# ---------------------------------------------------------------------------


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
LOG.info("Dashboard starting on port 8051")

# ---------------------------------------------------------------------------
# BingX API signing + request helper
# ---------------------------------------------------------------------------


def _sign(params: dict) -> dict:
    """Add timestamp and HMAC-SHA256 signature to params dict."""
    params['timestamp'] = int(time.time() * 1000)
    query = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params


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
        else:
            return {'error': f'Unsupported method: {method}'}
        data = resp.json()
        if data.get('code', 0) != 0:
            return {'error': f"BingX error {data.get('code')}: {data.get('msg')}"}
        return data.get('data', {})
    except Exception as e:
        return {'error': str(e)}


# ---------------------------------------------------------------------------
# Group A — Data Loaders
# ---------------------------------------------------------------------------


def load_state() -> dict:
    """Load state.json. Returns dict with safe defaults if file is missing."""
    defaults = {
        "open_positions": {},
        "daily_pnl": 0.0,
        "daily_trades": 0,
        "halt_flag": False,
        "session_start": "",
    }
    if not STATE_PATH.exists():
        return defaults
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge with defaults so missing keys never cause KeyError downstream
        return {**defaults, **data}
    except (json.JSONDecodeError, OSError):
        return defaults


def load_config() -> dict:
    """Load config.yaml. Returns empty dict if file missing or invalid."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError):
        return {}


def load_trades() -> pd.DataFrame:
    """Load trades.csv. Returns DataFrame sorted newest-first, or empty DataFrame."""
    if not TRADES_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(TRADES_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
        df["pnl_net"] = pd.to_numeric(df["pnl_net"], errors="coerce")
        df["entry_price"] = pd.to_numeric(df["entry_price"], errors="coerce")
        df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


def fetch_mark_price(symbol: str):
    """Fetch BingX mark price for one symbol via public REST endpoint. Returns float or None."""
    try:
        resp = requests.get(BINGX_PRICE_URL, params={"symbol": symbol}, timeout=5)
        data = resp.json().get("data", {})
        if isinstance(data, dict):
            val = float(data.get("price", 0))
            return val if val > 0 else None
        if isinstance(data, list) and data:
            val = float(data[0].get("price", 0))
            return val if val > 0 else None
    except Exception:
        pass
    return None


def fetch_all_mark_prices(symbols: list) -> dict:
    """Fetch mark prices for list of symbols in parallel. Returns {symbol: price} dict."""
    prices = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_mark_price, sym): sym for sym in symbols}
        for future in as_completed(futures, timeout=8):
            sym = futures[future]
            try:
                p = future.result()
                if p is not None:
                    prices[sym] = p
            except Exception:
                # Skip symbols that fail silently
                pass
    return prices


def fetch_account_balance() -> dict:
    """Fetch real account balance from BingX API (v3). Returns dict with balance, equity, unrealized."""
    default = {"balance": 0.0, "equity": 0.0, "unrealized": 0.0, "available_margin": 0.0, "used_margin": 0.0}
    if not API_KEY or not SECRET_KEY:
        return default
    try:
        data = _bingx_request('GET', '/openApi/swap/v3/user/balance', {})
        if 'error' in data:
            LOG.warning("Balance API error: %s", data['error'])
            return default
        accounts = data if isinstance(data, list) else [data]
        for acc in accounts:
            if acc.get('asset', '') == 'USDT':
                return {
                    "balance": float(acc.get('balance', 0)),
                    "equity": float(acc.get('equity', 0)),
                    "unrealized": float(acc.get('unrealizedProfit', 0)),
                    "available_margin": float(acc.get('availableMargin', 0)),
                    "used_margin": float(acc.get('usedMargin', 0)),
                }
        return default
    except Exception as e:
        LOG.warning("Balance fetch failed: %s", e)
        return default


def reconcile_positions(state: dict) -> dict:
    """Validate state.json positions against BingX API. Removes phantoms, writes cleaned state."""
    positions = state.get("open_positions", {})
    if not positions or not API_KEY or not SECRET_KEY:
        return state  # No positions or no API keys -- skip reconciliation
    try:
        data = _bingx_request('GET', '/openApi/swap/v2/user/positions', {})
        if 'error' in data:
            LOG.warning("Reconcile API error: %s -- using local state", data['error'])
            return state
        # Build set of live position keys from exchange
        live_positions = data if isinstance(data, list) else []
        live_keys = set()
        for pos in live_positions:
            amt = float(pos.get('positionAmt', 0))
            if amt == 0:
                continue
            sym = pos.get('symbol', '')
            side = pos.get('positionSide', '')
            if side in ('LONG', 'SHORT'):
                direction = side
            else:
                direction = 'LONG' if amt > 0 else 'SHORT'
            live_keys.add(sym + '_' + direction)
        # Remove phantom positions
        state_keys = set(positions.keys())
        phantoms = state_keys - live_keys
        if phantoms:
            for key in phantoms:
                LOG.warning("Reconcile: removing phantom position %s", key)
                state["open_positions"].pop(key, None)
            # Atomic write cleaned state
            _write_state(state)
            LOG.info("Reconcile: removed %d phantom positions", len(phantoms))
        else:
            LOG.debug("Reconcile: state matches exchange (%d positions)", len(state_keys))
    except Exception as e:
        LOG.warning("Reconcile failed: %s -- using local state", e)
    return state


def fmt_duration(start_dt, end_dt=None) -> str:
    """Format duration between two datetimes as '2h 15m' or '45m'. Returns em-dash on error."""
    if end_dt is None:
        end_dt = datetime.now(timezone.utc)
    if start_dt is None or pd.isna(start_dt):
        return "\u2014"
    try:
        total_sec = int((end_dt - start_dt).total_seconds())
        if total_sec < 0:
            return "\u2014"
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        return f"{h}h {m}m" if h > 0 else f"{m}m"
    except Exception:
        return "\u2014"


# ---------------------------------------------------------------------------
# Group B — Data Builders
# ---------------------------------------------------------------------------


def build_positions_df(state: dict, mark_prices: dict) -> pd.DataFrame:
    """Build display DataFrame for open positions. Adds unrealized PnL and distance-to-SL columns."""
    rows = []
    now = datetime.now(timezone.utc)
    for pos in state.get("open_positions", {}).values():
        sym = pos.get("symbol", "")
        direction = pos.get("direction", "")
        entry = pos.get("entry_price") or 0.0
        qty = pos.get("quantity") or 0.0
        mark = mark_prices.get(sym)
        sl_raw = pos.get("sl_price") or 0.0
        tp_raw = pos.get("tp_price")

        # Compute unrealized PnL from mark vs entry
        if mark and qty and entry:
            sign = 1 if direction == "LONG" else -1
            unreal_pnl = round((mark - entry) * qty * sign, 4)
        else:
            unreal_pnl = None

        # Compute distance to SL as percentage
        if mark and sl_raw and sl_raw > 0:
            dist_to_sl_pct = round(abs(mark - sl_raw) / mark * 100, 2)
        else:
            dist_to_sl_pct = None

        # Parse entry time for duration calculation
        try:
            entry_dt_str = pos.get("entry_time", "")
            entry_dt = datetime.fromisoformat(entry_dt_str.replace("Z", "+00:00"))
        except Exception:
            entry_dt = None

        tp_display = round(float(tp_raw), 6) if tp_raw else "\u2014"

        rows.append({
            "Symbol": sym,
            "Dir": direction,
            "Grade": pos.get("grade", ""),
            "Entry": round(float(entry), 6),
            "Stop Loss": round(float(sl_raw), 6),
            "Take Profit": tp_display,
            "BE Raised": "Yes" if pos.get("be_raised") else "No",
            "Unreal PnL": unreal_pnl,
            "Dist SL %": dist_to_sl_pct,
            "Duration": fmt_duration(entry_dt, now),
            "Qty": float(qty),  # raw contract quantity for API order placement
            "Notional": round(float(pos.get("notional_usd", 0)), 2),
            "order_id": pos.get("order_id", ""),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


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

    # Max drawdown $ and % (P7 fix: cap at -100%, skip when peak < $1)
    cum = df.sort_values("timestamp").pnl_net.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    max_dd = round(float(dd.min()), 4) if len(cum) > 0 else 0.0
    max_dd_pct = 0.0
    if len(cum) > 0 and float(dd.min()) < 0:
        dd_idx = dd.idxmin()
        peak_at_dd = float(peak.loc[dd_idx])
        if peak_at_dd >= 1.0:
            max_dd_pct = round(float(dd.loc[dd_idx] / peak_at_dd * 100), 2)
            max_dd_pct = max(max_dd_pct, -100.0)  # Cap at -100%

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
    }


def build_coin_summary(df: pd.DataFrame) -> list:
    """Compute per-coin performance stats. Returns list of dicts for ag-grid rowData."""
    if df.empty or "pnl_net" not in df.columns:
        return []
    rows = []
    for sym, grp in df.groupby("symbol"):
        total = len(grp)
        wins = int((grp.pnl_net > 0).sum())
        wr = round(wins / total * 100, 1) if total > 0 else 0.0
        net = round(float(grp.pnl_net.sum()), 4)
        avg = round(float(grp.pnl_net.mean()), 4)
        sl_pct = round((grp.exit_reason == "SL_HIT").sum() / total * 100, 1)
        tp_pct = round((grp.exit_reason == "TP_HIT").sum() / total * 100, 1)
        unk_pct = round(
            grp.exit_reason.isin(["EXIT_UNKNOWN", "SL_HIT_ASSUMED"]).sum() / total * 100, 1
        )
        best = round(float(grp.pnl_net.max()), 4)
        worst = round(float(grp.pnl_net.min()), 4)

        rows.append({
            "Symbol": sym, "Trades": total, "WR %": wr,
            "Net PnL": net, "Avg PnL": avg,
            "SL %": sl_pct, "TP %": tp_pct, "Unknown %": unk_pct,
            "Best": best, "Worst": worst,
        })

    # Sort by Net PnL descending and return as list of dicts
    summary_df = pd.DataFrame(rows).sort_values("Net PnL", ascending=False)
    return summary_df.to_dict('records')


# ---------------------------------------------------------------------------
# Group C — Chart Builders (all return go.Figure)
# ---------------------------------------------------------------------------

CHART_LAYOUT = dict(
    paper_bgcolor=COLORS['bg'],
    plot_bgcolor=COLORS['panel'],
    font=dict(color=COLORS['text']),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor=COLORS['grid']),
    yaxis=dict(gridcolor=COLORS['grid']),
)


def _empty_figure(title: str = "") -> go.Figure:
    """Return an empty figure with dark theme layout."""
    fig = go.Figure()
    fig.update_layout(title=title, **CHART_LAYOUT)
    return fig


def build_equity_figure(df: pd.DataFrame) -> go.Figure:
    """Build cumulative net PnL equity curve as Plotly scatter figure."""
    if df.empty or "pnl_net" not in df.columns:
        return _empty_figure("Equity Curve")
    df_sorted = df.sort_values("timestamp")
    cumulative = df_sorted["pnl_net"].cumsum()
    fig = go.Figure(go.Scatter(
        x=df_sorted["timestamp"], y=cumulative,
        mode='lines', fill='tozeroy',
        line=dict(color=COLORS['green'], width=2),
        fillcolor='rgba(63,185,80,0.08)',
    ))
    fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Net PnL (USDT)', **CHART_LAYOUT)
    return fig


def build_drawdown_figure(df: pd.DataFrame) -> go.Figure:
    """Build underwater equity drawdown curve as Plotly scatter figure."""
    if df.empty or "pnl_net" not in df.columns:
        return _empty_figure("Drawdown")
    df_sorted = df.sort_values("timestamp")
    cum = df_sorted["pnl_net"].cumsum()
    dd = cum - cum.cummax()
    fig = go.Figure(go.Scatter(
        x=df_sorted["timestamp"], y=dd,
        mode='lines', fill='tozeroy',
        line=dict(color=COLORS['red'], width=1),
        fillcolor='rgba(248,81,73,0.12)',
    ))
    fig.update_layout(title='Drawdown', xaxis_title='Date', yaxis_title='Drawdown (USDT)', **CHART_LAYOUT)
    return fig


def build_exit_reason_figure(df: pd.DataFrame) -> go.Figure:
    """Build exit reason count bar chart."""
    if df.empty or "exit_reason" not in df.columns:
        return _empty_figure("Exit Breakdown")
    reason_order = ['SL_HIT', 'TP_HIT', 'EXIT_UNKNOWN', 'SL_HIT_ASSUMED']
    color_map = {
        'SL_HIT': COLORS['red'], 'TP_HIT': COLORS['green'],
        'EXIT_UNKNOWN': COLORS['orange'], 'SL_HIT_ASSUMED': COLORS['orange'],
    }
    counts = df["exit_reason"].value_counts()
    labels = [r for r in reason_order if r in counts.index]
    values = [counts[r] for r in labels]
    colors = [color_map.get(r, COLORS['muted']) for r in labels]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colors))
    fig.update_layout(title='Exit Breakdown', xaxis_title='Exit Reason', yaxis_title='Count', **CHART_LAYOUT)
    return fig


def build_daily_pnl_figure(df: pd.DataFrame) -> go.Figure:
    """Build daily net PnL bar chart grouped by calendar day."""
    if df.empty or "pnl_net" not in df.columns:
        return _empty_figure("Daily PnL")
    df_copy = df.copy()
    df_copy["date"] = df_copy["timestamp"].dt.date
    daily = df_copy.groupby("date")["pnl_net"].sum().reset_index()
    colors = [COLORS['green'] if v >= 0 else COLORS['red'] for v in daily.pnl_net]
    fig = go.Figure(go.Bar(x=daily.date, y=daily.pnl_net, marker_color=colors))
    fig.update_layout(title='Daily PnL', xaxis_title='Date', yaxis_title='PnL (USDT)', **CHART_LAYOUT)
    return fig


# ---------------------------------------------------------------------------
# Group D — Layout Helpers
# ---------------------------------------------------------------------------


def build_metric_card(label: str, value: str, color: str = None) -> html.Div:
    """Build a single metric display card div."""
    return html.Div([
        html.Div(label, style={'fontSize': '11px', 'color': COLORS['muted']}),
        html.Div(value, style={'fontSize': '22px', 'fontWeight': 'bold',
                               'color': color or COLORS['text']}),
    ], style={'padding': '16px', 'background': COLORS['panel'],
              'borderRadius': '8px', 'minWidth': '120px', 'flex': '1'})


# ---------------------------------------------------------------------------
# AG-Grid Column Definitions
# ---------------------------------------------------------------------------

POSITION_COLUMNS = [
    {'field': 'Symbol',     'pinned': 'left', 'width': 120},
    {'field': 'Dir',        'width': 70,
     'cellStyle': {'function': "(p) => ({color: p.value==='LONG' ? '#3fb950' : '#f85149', fontWeight:'bold'})"}},
    {'field': 'Grade',      'width': 70},
    {'field': 'Entry',      'width': 110, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(6)'}},
    {'field': 'Stop Loss',  'width': 110, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(6)'}},
    {'field': 'Take Profit', 'width': 110},
    {'field': 'BE Raised',  'width': 90,
     'cellStyle': {'function': "(p) => ({color: p.value==='Yes' ? '#3fb950' : '#8b949e'})"}},
    {'field': 'Unreal PnL', 'width': 110, 'type': 'numericColumn',
     'cellStyle': {'function': "(p) => p.value == null ? {} : ({color: p.value >= 0 ? '#3fb950' : '#f85149', fontWeight:'bold'})"},
     'valueFormatter': {'function': "params.value != null ? params.value.toFixed(4) : '\u2014'"}},
    {'field': 'Dist SL %',  'width': 90, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(2)+"%" : "\u2014"'}},
    {'field': 'Duration',   'width': 90},
    {'field': 'Notional',   'width': 90, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(2)'}},
    {'field': 'Qty',        'hide': True},  # hidden, raw contract quantity for API orders
    {'field': 'order_id',   'hide': True},  # hidden, used by action callbacks
]

HISTORY_COLUMNS = [
    {'field': 'Date',        'width': 120, 'pinned': 'left'},
    {'field': 'Symbol',      'width': 110},
    {'field': 'Dir',         'width': 70},
    {'field': 'Grade',       'width': 70, 'filter': True},
    {'field': 'Entry',       'width': 100, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value.toFixed(6)'}},
    {'field': 'Exit',        'width': 100, 'type': 'numericColumn',
     'valueFormatter': {'function': 'params.value != null ? params.value.toFixed(6) : "\u2014"'}},
    {'field': 'Exit Reason', 'width': 130, 'filter': True,
     'cellStyle': {'function': """(p) => ({
         color: p.value==='TP_HIT' ? '#3fb950' :
                p.value==='SL_HIT' ? '#f85149' : '#d29922'
     })"""}},
    {'field': 'Net PnL',     'width': 100, 'type': 'numericColumn',
     'cellStyle': {'function': "(p) => ({color: p.value >= 0 ? '#3fb950' : '#f85149', fontWeight:'bold'})"},
     'valueFormatter': {'function': 'params.value.toFixed(4)'}},
    {'field': 'Duration',    'width': 90},
    {'field': 'Notional',    'width': 90, 'type': 'numericColumn'},
]

COIN_COLUMNS = [
    {'field': 'Symbol',    'pinned': 'left', 'width': 120},
    {'field': 'Trades',    'width': 80,  'type': 'numericColumn'},
    {'field': 'WR %',      'width': 80,  'type': 'numericColumn'},
    {'field': 'Net PnL',   'width': 100, 'type': 'numericColumn',
     'cellStyle': {'function': "(p) => ({color: p.value >= 0 ? '#3fb950' : '#f85149', fontWeight:'bold'})"},
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

# ---------------------------------------------------------------------------
# Tab layout builders
# ---------------------------------------------------------------------------


def make_operational_tab() -> html.Div:
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
    ])


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
    ])


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
    ])


def make_coin_summary_tab() -> html.Div:
    """Build layout for Coin Summary tab -- per-coin stats grid."""
    return html.Div([
        dcc.RadioItems(
            id='coin-period-filter',
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
        html.Div(id='coin-summary-caption',
                 style={'color': COLORS['muted'], 'marginTop': '8px'}),
    ])


def make_bot_controls_tab() -> html.Div:
    """Build layout for Bot Controls tab -- config editor and halt/resume."""
    return html.Div([
        # Warning banner
        html.Div([
            html.Strong("LIVE BOT CONTROL"),
            html.Span(" \u2014 Changes to Strategy and Risk take effect on the next bot loop. "
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
                           options=[{'label': 'Yes', 'value': 'true'},
                                    {'label': 'No', 'value': 'false'}], inline=True),
            html.Label("Rotation Level"),
            dcc.Input(id='ctrl-rot-level', type='number', min=50, max=95, step=1),
            html.Label("Allow Grade A"),
            dcc.RadioItems(id='ctrl-allow-a',
                           options=[{'label': 'Yes', 'value': 'true'},
                                    {'label': 'No', 'value': 'false'}], inline=True),
            html.Label("Allow Grade B"),
            dcc.RadioItems(id='ctrl-allow-b',
                           options=[{'label': 'Yes', 'value': 'true'},
                                    {'label': 'No', 'value': 'false'}], inline=True),
        ], style={'display': 'grid', 'gridTemplateColumns': '200px 1fr', 'gap': '8px',
                  'alignItems': 'center', 'maxWidth': '500px', 'marginBottom': '16px'}),

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
        ], style={'display': 'grid', 'gridTemplateColumns': '200px 1fr', 'gap': '8px',
                  'alignItems': 'center', 'maxWidth': '500px', 'marginBottom': '16px'}),

        # Position sizing — restart required
        html.H4("Position Sizing (*restart required)"),
        html.Div([
            html.Label("Margin per Trade ($)"),
            dcc.Input(id='ctrl-margin-usd', type='number', min=1, step=1),
            html.Label("Leverage"),
            dcc.Input(id='ctrl-leverage', type='number', min=1, max=125, step=1),
        ], style={'display': 'grid', 'gridTemplateColumns': '200px 1fr', 'gap': '8px',
                  'alignItems': 'center', 'maxWidth': '500px', 'marginBottom': '16px'}),

        html.Div([
            html.Button("Save Config", id='save-config-btn', n_clicks=0,
                         style={'marginRight': '8px', 'background': COLORS['blue'],
                                'color': 'white', 'border': 'none', 'padding': '8px 16px',
                                'borderRadius': '4px', 'cursor': 'pointer'}),
            html.Button("Discard", id='discard-config-btn', n_clicks=0,
                         style={'background': COLORS['grid'], 'color': COLORS['text'],
                                'border': 'none', 'padding': '8px 16px',
                                'borderRadius': '4px', 'cursor': 'pointer'}),
        ], style={'marginBottom': '12px'}),
        html.Div(id='save-config-status', style={'marginBottom': '24px'}),

        html.Hr(style={'borderColor': COLORS['grid']}),

        # Bot halt/resume
        html.H4("Bot Control"),
        html.P("Halt stops the bot from opening new trades. Open positions are not affected.",
               style={'color': COLORS['muted']}),
        html.Div([
            html.Button("Halt Bot", id='halt-bot-btn', n_clicks=0,
                         style={'marginRight': '8px', 'background': COLORS['red'],
                                'color': 'white', 'border': 'none', 'padding': '8px 16px',
                                'borderRadius': '4px', 'cursor': 'pointer'}),
            html.Button("Resume Bot", id='resume-bot-btn', n_clicks=0,
                         style={'background': COLORS['green'], 'color': 'white',
                                'border': 'none', 'padding': '8px 16px',
                                'borderRadius': '4px', 'cursor': 'pointer'}),
        ], style={'marginBottom': '8px'}),
        html.Div(id='halt-status'),
    ])


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------


def validate_config_updates(updates: dict):
    """Validate config form values before writing. Returns (is_valid, error_message)."""
    sl = updates.get("sl_atr_mult")
    if sl is None or float(sl) <= 0 or float(sl) > 10:
        return (False, "Error: sl_atr_mult must be > 0 and <= 10")

    tp = updates.get("tp_atr_mult")
    if tp is not None and float(tp) <= 0:
        return (False, "Error: tp_atr_mult must be > 0 if set")

    rot = updates.get("rot_level")
    if rot is None or int(rot) < 50 or int(rot) > 95:
        return (False, "Error: rot_level must be 50-95")

    mp = updates.get("max_positions")
    if mp is None or int(mp) < 1 or int(mp) > 50:
        return (False, "Error: max_positions must be 1-50")

    mt = updates.get("max_daily_trades")
    if mt is None or int(mt) < 1 or int(mt) > 200:
        return (False, "Error: max_daily_trades must be 1-200")

    dll = updates.get("daily_loss_limit_usd")
    if dll is None or float(dll) <= 0:
        return (False, "Error: daily_loss_limit_usd must be > 0")

    mar = updates.get("min_atr_ratio")
    if mar is None or float(mar) < 0.0001 or float(mar) > 0.05:
        return (False, "Error: min_atr_ratio must be 0.0001-0.05")

    cb = updates.get("cooldown_bars")
    if cb is None or int(cb) < 0 or int(cb) > 20:
        return (False, "Error: cooldown_bars must be 0-20")

    mu = updates.get("margin_usd")
    if mu is None or float(mu) <= 0:
        return (False, "Error: margin_usd must be > 0")

    lev = updates.get("leverage")
    if lev is None or int(lev) < 1 or int(lev) > 125:
        return (False, "Error: leverage must be 1-125")

    return (True, "")


# ---------------------------------------------------------------------------
# State write helper — atomic write via tmp + os.replace
# ---------------------------------------------------------------------------


def _write_state(state: dict) -> None:
    """Atomic write state.json — prevents partial reads by bot."""
    tmp = STATE_PATH.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


# ---------------------------------------------------------------------------
# Dash App
# ---------------------------------------------------------------------------

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,  # Still needed -- CB-5 creates action buttons dynamically
    title='BingX Live Dashboard v1-3',
)
server = app.server  # Expose Flask server for gunicorn

app.layout = html.Div([
    # 60s auto-refresh interval
    dcc.Interval(id='refresh-interval', interval=60_000, n_intervals=0),

    # Data stores -- JSON strings, refreshed by CB-1
    dcc.Store(id='store-state',  storage_type='memory'),
    dcc.Store(id='store-trades', storage_type='memory'),
    dcc.Store(id='store-config', storage_type='memory'),
    dcc.Store(id='store-unrealized', storage_type='memory'),

    # Status bar -- always visible
    html.Div(id='status-bar'),

    # Tab navigation
    dcc.Tabs(id='main-tabs', value='tab-ops',
             parent_style={'backgroundColor': '#0d1117'},
             style={'borderBottom': '1px solid #21262d'},
             children=[
        dcc.Tab(label='Operational',  value='tab-ops', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='History',      value='tab-hist', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Analytics',    value='tab-analytics', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Coin Summary', value='tab-coins', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        dcc.Tab(label='Bot Controls', value='tab-controls', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
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
], style={'background': COLORS['bg'], 'minHeight': '100vh'})


# ===========================================================================
# CALLBACKS
# ===========================================================================

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
)


# ---------------------------------------------------------------------------
# CB-3: Status Bar
# ---------------------------------------------------------------------------

@callback(
    Output('status-bar', 'children'),
    Input('store-state',  'data'),
    Input('store-config', 'data'),
    Input('store-unrealized', 'data'),
)
def update_status_bar(state_json, config_json, unrealized_json):
    """Render top status bar with bot mode, daily PnL, positions, risk usage."""
    try:
        if not state_json or not config_json:
            return html.Div("Loading...", style={'padding': '12px'})

        state = json.loads(state_json)
        cfg = json.loads(config_json)

        halt_flag = state.get("halt_flag", False)
        demo_mode = cfg.get("connector", {}).get("demo_mode", True)
        daily_pnl = float(state.get("daily_pnl", 0.0))
        # Parse balance data from BingX API (via store-unrealized)
        bal_data = json.loads(unrealized_json) if unrealized_json else {}
        if isinstance(bal_data, dict):
            api_balance = float(bal_data.get("balance", 0.0))
            api_equity = float(bal_data.get("equity", 0.0))
            unrealized_pnl = float(bal_data.get("unrealized", 0.0))
        else:
            # Legacy format (plain float) -- backwards compat
            api_balance = 0.0
            api_equity = 0.0
            unrealized_pnl = float(bal_data) if bal_data else 0.0
        unreal_color = COLORS['green'] if unrealized_pnl >= 0 else COLORS['red']
        open_count = len(state.get("open_positions", {}))
        daily_trades = int(state.get("daily_trades", 0))
        max_positions = cfg.get("risk", {}).get("max_positions", 8)
        max_daily_trades = cfg.get("risk", {}).get("max_daily_trades", 50)
        daily_loss_limit = cfg.get("risk", {}).get("daily_loss_limit_usd", 15.0)
        risk_pct = round(abs(daily_pnl) / daily_loss_limit * 100, 1) if daily_loss_limit > 0 else 0.0

        # Determine status label and color
        if halt_flag:
            status_label, status_color = "HALTED", COLORS['red']
        elif demo_mode:
            status_label, status_color = "DEMO", COLORS['blue']
        else:
            status_label, status_color = "LIVE", COLORS['green']

        pnl_color = COLORS['green'] if daily_pnl >= 0 else COLORS['red']
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        # Use real API balance if available, fall back to state.json
        if api_balance > 0:
            balance_color = COLORS['green'] if api_balance >= 100 else COLORS['red']
            equity_color = COLORS['green'] if api_equity >= 100 else COLORS['red']
        else:
            api_balance = daily_pnl
            api_equity = daily_pnl + unrealized_pnl
            balance_color = COLORS['green'] if api_balance >= 0 else COLORS['red']
            equity_color = COLORS['green'] if api_equity >= 0 else COLORS['red']

        return html.Div([
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
                  'borderBottom': f"1px solid {COLORS['grid']}"})
    except Exception as e:
        LOG.error("Error in status bar: %s", e, exc_info=True)
        return html.Div(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-4: Positions Grid
# ---------------------------------------------------------------------------

@callback(
    Output('positions-grid', 'rowData'),
    Output('store-unrealized', 'data'),
    Input('store-state', 'data'),
    prevent_initial_call=True,  # Do not fire on page load — stores not yet populated
)
def update_positions_grid(state_json):
    """Load open positions with live mark prices into ag-grid. Outputs unrealized PnL to store."""
    try:
        if not state_json:
            return [], json.dumps(fetch_account_balance())
        state = json.loads(state_json)
        # Reconcile against BingX API -- removes phantom positions
        state = reconcile_positions(state)
        positions = state.get("open_positions", {})
        if not positions:
            return [], json.dumps(fetch_account_balance())
        symbols = [p["symbol"] for p in positions.values() if p.get("symbol")]
        mark_prices = fetch_all_mark_prices(symbols)
        LOG.debug("Mark prices fetched: %d/%d symbols", len(mark_prices), len(symbols))
        pos_df = build_positions_df(state, mark_prices)
        if pos_df.empty:
            return [], json.dumps(0.0)
        # Fetch real balance from BingX API
        bal = fetch_account_balance()
        return pos_df.to_dict('records'), json.dumps(bal)
    except Exception as e:
        LOG.error("Error loading positions: %s", e, exc_info=True)
        return [], json.dumps({"balance": 0.0, "equity": 0.0, "unrealized": 0.0})


# ---------------------------------------------------------------------------
# CB-5: Selected Position Info
# ---------------------------------------------------------------------------

@callback(
    Output('selected-pos-info', 'children'),
    Input('positions-grid', 'selectedRows'),
    prevent_initial_call=True,  # Do not fire on page load
)
def show_selected_position(selected_rows):
    """Render action panel for the selected position row."""
    try:
        if not selected_rows:
            return html.Div("Select a position to manage it.",
                            style={'color': COLORS['muted'], 'marginTop': '8px'})
        row = selected_rows[0]
        be_already_raised = row.get("BE Raised") == "Yes"
        return html.Div([
            html.Div(
                f"{row['Symbol']} {row['Dir']}  |  Entry: {row['Entry']}  |  SL: {row['Stop Loss']}",
                style={'fontWeight': 'bold', 'marginBottom': '8px'}
            ),
            html.Div([
                html.Button("Raise to Breakeven", id="raise-be-btn", n_clicks=0,
                            disabled=be_already_raised,
                            style={'marginRight': '12px', 'background': COLORS['blue'],
                                   'color': 'white', 'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer',
                                   'opacity': '0.4' if be_already_raised else '1'}),
                dcc.Input(id="new-sl-input", type="number", placeholder="New SL price",
                          debounce=True,
                          style={'marginRight': '8px', 'width': '140px'}),
                html.Button("Move SL", id="move-sl-btn", n_clicks=0,
                            style={'background': COLORS['orange'], 'color': 'white',
                                   'border': 'none', 'padding': '6px 12px',
                                   'borderRadius': '4px', 'cursor': 'pointer'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            # Hidden div to store selected symbol for API calls
            html.Div(id="selected-symbol", children=row["Symbol"],
                     style={"display": "none"}),
        ], style={'marginTop': '12px', 'padding': '12px',
                  'background': COLORS['panel'], 'borderRadius': '8px'})
    except Exception as e:
        LOG.error("Error in selected position: %s", e, exc_info=True)
        return html.Div(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-6: Raise to Breakeven
# ---------------------------------------------------------------------------

@callback(
    Output('pos-action-status', 'children', allow_duplicate=True),
    Input('raise-be-btn', 'n_clicks'),
    State('positions-grid', 'selectedRows'),
    State('store-state', 'data'),
    prevent_initial_call=True,  # Do not fire on page load
)
def raise_breakeven(n_clicks, selected_rows, state_json):
    """Cancel SL order and place new STOP_MARKET at entry price for selected position."""
    symbol = "unknown"
    try:
        if not n_clicks or not selected_rows:
            raise PreventUpdate  # Guard — button not yet clicked
        row = selected_rows[0]
        symbol = row["Symbol"]
        direction = row["Dir"]
        entry_price = row["Entry"]
        position_side = "LONG" if direction == "LONG" else "SHORT"

        # Validate: SL at entry requires mark to be on the profitable side
        # LONG SL at entry: mark must be above entry (stop triggers on downward move)
        # SHORT SL at entry: mark must be below entry (stop triggers on upward move)
        mark = fetch_mark_price(symbol)
        if mark is not None:
            if direction == "LONG" and mark <= entry_price:
                return html.Span(
                    f"Cannot raise BE: mark ({mark}) is not above entry ({entry_price})",
                    style={'color': COLORS['red']})
            if direction == "SHORT" and mark >= entry_price:
                return html.Span(
                    f"Cannot raise BE: mark ({mark}) is not below entry ({entry_price})",
                    style={'color': COLORS['red']})

        LOG.info("Raise BE: %s %s", symbol, direction)

        # Step 1: GET open orders for symbol
        data = _bingx_request('GET', '/openApi/swap/v2/trade/openOrders',
                              {'symbol': symbol})
        if 'error' in data:
            return html.Span(f"Error fetching orders: {data['error']}",
                             style={'color': COLORS['red']})

        # Step 2: Find SL order (STOP_MARKET, reduceOnly)
        orders = data.get("orders", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        sl_order = None
        for order in orders:
            if order.get("type") == "STOP_MARKET":
                sl_order = order
                break
        if not sl_order:
            return html.Span(f"No SL order found for {symbol}",
                             style={'color': COLORS['orange']})

        # Step 3: Cancel SL order
        cancel_result = _bingx_request('DELETE', '/openApi/swap/v2/trade/order',
                                        {'symbol': symbol, 'orderId': sl_order["orderId"]})
        if 'error' in cancel_result:
            return html.Span(f"Cancel failed: {cancel_result['error']}",
                             style={'color': COLORS['red']})

        # Step 4: Place new STOP_MARKET at entry price
        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
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

        # Step 5: Update state.json — be_raised=True, sl_price=entry
        try:
            state = json.loads(state_json) if state_json else load_state()
            pos_key = f"{symbol}_{direction}"
            if pos_key in state.get("open_positions", {}):
                state["open_positions"][pos_key]["be_raised"] = True
                state["open_positions"][pos_key]["sl_price"] = entry_price
                _write_state(state)  # Atomic write — prevents partial reads by bot
        except Exception as state_err:
            LOG.error("State write failed after BE raise: %s", state_err, exc_info=True)

        LOG.info("Raise BE success: %s", symbol)
        return html.Span(f"BE raised for {symbol} \u2014 SL moved to {entry_price}",
                         style={'color': COLORS['green']})
    except PreventUpdate:
        raise  # Re-raise PreventUpdate before outer except
    except Exception as e:
        LOG.error("Raise BE failed for %s: %s", symbol, e, exc_info=True)
        return html.Span(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-7: Move SL
# ---------------------------------------------------------------------------

@callback(
    Output('pos-action-status', 'children', allow_duplicate=True),
    Input('move-sl-btn', 'n_clicks'),
    State('positions-grid', 'selectedRows'),
    State('new-sl-input', 'value'),
    State('store-state', 'data'),
    prevent_initial_call=True,  # Do not fire on page load
)
def move_sl(n_clicks, selected_rows, new_sl_price, state_json):
    """Cancel existing SL and place new STOP_MARKET at user-specified price."""
    symbol = "unknown"
    try:
        if not n_clicks or not selected_rows or new_sl_price is None:
            raise PreventUpdate  # Guard — button not yet clicked or no price entered
        row = selected_rows[0]
        symbol = row["Symbol"]
        direction = row["Dir"]
        new_sl = float(new_sl_price)
        position_side = "LONG" if direction == "LONG" else "SHORT"

        # Validate SL direction
        if direction == "LONG" and new_sl >= row["Entry"]:
            return html.Span("Invalid: LONG SL must be below entry price",
                             style={'color': COLORS['red']})
        if direction == "SHORT" and new_sl <= row["Entry"]:
            return html.Span("Invalid: SHORT SL must be above entry price",
                             style={'color': COLORS['red']})

        LOG.info("Move SL: %s new_sl=%s", symbol, new_sl)

        # Step 1: GET open orders for symbol
        data = _bingx_request('GET', '/openApi/swap/v2/trade/openOrders',
                              {'symbol': symbol})
        if 'error' in data:
            return html.Span(f"Error fetching orders: {data['error']}",
                             style={'color': COLORS['red']})

        # Step 2: Find SL order
        orders = data.get("orders", []) if isinstance(data, dict) else data if isinstance(data, list) else []
        sl_order = None
        for order in orders:
            if order.get("type") == "STOP_MARKET":
                sl_order = order
                break
        if not sl_order:
            return html.Span(f"No SL order found for {symbol}",
                             style={'color': COLORS['orange']})

        # Step 3: Cancel SL order
        cancel_result = _bingx_request('DELETE', '/openApi/swap/v2/trade/order',
                                        {'symbol': symbol, 'orderId': sl_order["orderId"]})
        if 'error' in cancel_result:
            return html.Span(f"Cancel failed: {cancel_result['error']}",
                             style={'color': COLORS['red']})

        # Step 4: Place new STOP_MARKET at user price
        place_result = _bingx_request('POST', '/openApi/swap/v2/trade/order', {
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

        # Step 5: Update state.json — sl_price = new_sl
        try:
            state = json.loads(state_json) if state_json else load_state()
            pos_key = f"{symbol}_{direction}"
            if pos_key in state.get("open_positions", {}):
                state["open_positions"][pos_key]["sl_price"] = new_sl
                _write_state(state)  # Atomic write — prevents partial reads by bot
        except Exception as state_err:
            LOG.error("State write failed after SL move: %s", state_err, exc_info=True)

        LOG.info("Move SL success: %s", symbol)
        return html.Span(f"SL moved to {new_sl} for {symbol}",
                         style={'color': COLORS['green']})
    except PreventUpdate:
        raise  # Re-raise PreventUpdate before outer except
    except Exception as e:
        LOG.error("Move SL failed for %s: %s", symbol, e, exc_info=True)
        return html.Span(f"Error: {e}", style={'color': COLORS['red']})


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

        df = pd.read_json(io.StringIO(trades_json), orient='split')
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
        return [], html.Span("Error: " + str(e), style={'color': COLORS['red']})


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
    Input('store-unrealized',        'data'),
    prevent_initial_call=True,
)
def update_analytics(start_date, end_date, trades_json, unrealized_json):
    """Compute all analytics from trades store and render all analytics tab components."""
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
        # Extend equity curve with current unrealized PnL (all-time view only)
        if unrealized_json and not df.empty and not start_date and not end_date:
            try:
                bal_data = json.loads(unrealized_json)
                unreal_val = float(bal_data.get("unrealized", 0.0)) if isinstance(bal_data, dict) else float(bal_data)
                if unreal_val != 0.0:
                    df_sorted = df.sort_values("timestamp")
                    last_cum = float(df_sorted["pnl_net"].cumsum().iloc[-1])
                    equity_fig.add_trace(go.Scatter(
                        x=[df_sorted["timestamp"].iloc[-1], datetime.now(timezone.utc)],
                        y=[last_cum, last_cum + unreal_val],
                        mode='lines+markers',
                        line=dict(color=COLORS['blue'], width=2, dash='dash'),
                        marker=dict(size=6, color=COLORS['blue']),
                        name='+ Unrealized',
                        showlegend=True,
                    ))
            except Exception:
                pass
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
                html.Div("Error: " + str(e), style={'color': COLORS['red']}))


# ---------------------------------------------------------------------------
# CB-10: Coin Summary
# ---------------------------------------------------------------------------

@callback(
    Output('coin-summary-grid',    'rowData'),
    Output('coin-summary-caption', 'children'),
    Input('coin-period-filter',    'value'),
    Input('store-trades',          'data'),
    prevent_initial_call=True,
)
def update_coin_summary(period_filter, trades_json):
    """Filter trades by period and render per-coin summary grid."""
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
        # 'all' — no filter

        records = build_coin_summary(df)
        caption = f"{len(records)} coins in history"
        return records, caption
    except Exception as e:
        LOG.error("Error in coin summary: %s", e, exc_info=True)
        return [], html.Span(f"Error: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-11: Load Config Into Controls
# ---------------------------------------------------------------------------

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
    prevent_initial_call=True,  # Do not fire on page load — stores not yet populated
)
def load_config_into_controls(config_json):
    """Populate Bot Controls form fields from current config.yaml values."""
    try:
        if not config_json:
            raise PreventUpdate  # Guard — config not loaded yet
        cfg = json.loads(config_json)
        fp = cfg.get("four_pillars", {})
        risk = cfg.get("risk", {})
        pos = cfg.get("position", {})
        return (
            fp.get("sl_atr_mult", 2.0),
            fp.get("tp_atr_mult"),
            "true" if fp.get("require_stage2", True) else "false",
            fp.get("rot_level", 80),
            "true" if fp.get("allow_a", True) else "false",
            "true" if fp.get("allow_b", True) else "false",
            risk.get("max_positions", 8),
            risk.get("max_daily_trades", 50),
            risk.get("daily_loss_limit_usd", 15.0),
            risk.get("min_atr_ratio", 0.003),
            risk.get("cooldown_bars", 3),
            pos.get("margin_usd", 5.0),
            pos.get("leverage", 10),
        )
    except PreventUpdate:
        raise  # Re-raise PreventUpdate before outer except
    except Exception as e:
        LOG.error("Error loading config into controls: %s", e, exc_info=True)
        raise PreventUpdate


# ---------------------------------------------------------------------------
# CB-12: Save Config
# ---------------------------------------------------------------------------

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
    prevent_initial_call=True,  # Do not fire on page load
)
def save_config(n_clicks, sl_mult, tp_mult, req_s2, rot_lvl,
                allow_a, allow_b, max_pos, max_trades,
                loss_limit, min_atr, cooldown, margin, leverage):
    """Validate inputs and write updated values to config.yaml atomically."""
    try:
        if not n_clicks:
            raise PreventUpdate  # Guard — button not yet clicked

        # Build updates dict for validation
        updates = {
            "sl_atr_mult": sl_mult, "tp_atr_mult": tp_mult if tp_mult else None,
            "rot_level": rot_lvl, "max_positions": max_pos,
            "max_daily_trades": max_trades, "daily_loss_limit_usd": loss_limit,
            "min_atr_ratio": min_atr, "cooldown_bars": cooldown,
            "margin_usd": margin, "leverage": leverage,
        }

        ok, err = validate_config_updates(updates)
        if not ok:
            return html.Span(err, style={'color': COLORS['red']})

        # Read current config — preserves coins list and other untouched keys
        cfg = load_config()
        original_cfg = json.dumps(cfg)

        # Ensure sections exist
        cfg.setdefault("four_pillars", {})
        cfg.setdefault("risk", {})
        cfg.setdefault("position", {})

        # Apply form values
        cfg["four_pillars"]["sl_atr_mult"] = float(sl_mult)
        cfg["four_pillars"]["tp_atr_mult"] = float(tp_mult) if tp_mult else None
        cfg["four_pillars"]["require_stage2"] = (req_s2 == "true")
        cfg["four_pillars"]["rot_level"] = int(rot_lvl)
        cfg["four_pillars"]["allow_a"] = (allow_a == "true")
        cfg["four_pillars"]["allow_b"] = (allow_b == "true")
        cfg["risk"]["max_positions"] = int(max_pos)
        cfg["risk"]["max_daily_trades"] = int(max_trades)
        cfg["risk"]["daily_loss_limit_usd"] = float(loss_limit)
        cfg["risk"]["min_atr_ratio"] = float(min_atr)
        cfg["risk"]["cooldown_bars"] = int(cooldown)
        cfg["position"]["margin_usd"] = float(margin)
        cfg["position"]["leverage"] = int(leverage)

        # Atomic write — prevents partial reads by bot
        tmp = CONFIG_PATH.with_suffix('.yaml.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
        os.replace(tmp, CONFIG_PATH)

        # Build diff message
        old_cfg = json.loads(original_cfg)
        changes = []
        old_fp = old_cfg.get("four_pillars", {})
        old_risk = old_cfg.get("risk", {})
        old_pos = old_cfg.get("position", {})
        new_fp = cfg["four_pillars"]
        new_risk = cfg["risk"]
        new_pos = cfg["position"]

        for key in new_fp:
            if old_fp.get(key) != new_fp[key]:
                changes.append(f"{key}: {old_fp.get(key)} -> {new_fp[key]}")
        for key in new_risk:
            if old_risk.get(key) != new_risk[key]:
                changes.append(f"{key}: {old_risk.get(key)} -> {new_risk[key]}")

        restart_needed = []
        if old_pos.get("margin_usd") != new_pos["margin_usd"]:
            changes.append(f"margin_usd: {old_pos.get('margin_usd')} -> {new_pos['margin_usd']}")
            restart_needed.append("margin_usd")
        if old_pos.get("leverage") != new_pos["leverage"]:
            changes.append(f"leverage: {old_pos.get('leverage')} -> {new_pos['leverage']}")
            restart_needed.append("leverage")

        diff_msg = "Saved. "
        if changes:
            diff_msg += "Changed: " + "; ".join(changes)
        else:
            diff_msg += "No changes detected."
        if restart_needed:
            diff_msg += " | Restart bot to apply: " + ", ".join(restart_needed)

        LOG.info("Config saved: %s", diff_msg)
        return html.Span(diff_msg, style={'color': COLORS['green']})
    except PreventUpdate:
        raise  # Re-raise PreventUpdate before outer except
    except Exception as e:
        LOG.error("Config write failed: %s", e, exc_info=True)
        return html.Span(f"Write failed: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-13: Halt Bot
# ---------------------------------------------------------------------------

@callback(
    Output('halt-status', 'children', allow_duplicate=True),
    Input('halt-bot-btn', 'n_clicks'),
    prevent_initial_call=True,  # Do not fire on page load
)
def halt_bot(n_clicks):
    """Write halt_flag=True to state.json. Bot checks this on next loop (max 60s delay)."""
    try:
        if not n_clicks:
            raise PreventUpdate  # Guard — button not yet clicked
        state = load_state()
        state["halt_flag"] = True
        _write_state(state)  # Atomic write — prevents partial reads by bot
        LOG.info("Bot halt_flag set to True")
        return html.Span("Bot halted \u2014 will stop accepting new trades on next loop.",
                         style={'color': COLORS['red']})
    except PreventUpdate:
        raise  # Re-raise PreventUpdate before outer except
    except Exception as e:
        LOG.error("State write failed: %s", e, exc_info=True)
        return html.Span(f"Write failed: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# CB-14: Resume Bot
# ---------------------------------------------------------------------------

@callback(
    Output('halt-status', 'children', allow_duplicate=True),
    Input('resume-bot-btn', 'n_clicks'),
    prevent_initial_call=True,  # Do not fire on page load
)
def resume_bot(n_clicks):
    """Write halt_flag=False to state.json."""
    try:
        if not n_clicks:
            raise PreventUpdate  # Guard — button not yet clicked
        state = load_state()
        state["halt_flag"] = False
        _write_state(state)  # Atomic write — prevents partial reads by bot
        LOG.info("Bot halt_flag set to False")
        return html.Span("Bot resumed.", style={'color': COLORS['green']})
    except PreventUpdate:
        raise  # Re-raise PreventUpdate before outer except
    except Exception as e:
        LOG.error("State write failed: %s", e, exc_info=True)
        return html.Span(f"Write failed: {e}", style={'color': COLORS['red']})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    threading.Timer(1.5, webbrowser.open, args=["http://127.0.0.1:8051/"]).start()
    app.run(debug=False, port=8051, host='127.0.0.1')
