#!/usr/bin/env python3
"""
Trade Chart Report Generator - Interactive HTML with Plotly charts.
Reads trades.csv, fetches 5m klines from BingX API, computes indicators,
runs Four Pillars signal detection, and generates a single-file HTML report.
"""
import argparse
import csv
import hashlib
import hmac as hmac_lib
import logging
import os
import sys
import time
from datetime import datetime, timezone, date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
TRADES_CSV = ROOT / "trades_all.csv"
CONFIG_PATH = ROOT / "config.yaml"
LOG_DIR = ROOT / "logs"
KLINE_PATH = "/openApi/swap/v2/quote/klines"

FULL_COLUMNS = [
    "timestamp", "symbol", "direction", "grade", "entry_price", "exit_price",
    "exit_reason", "pnl_net", "quantity", "notional_usd", "entry_time", "order_id",
    "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct", "ttp_exit_reason",
    "be_raised", "saw_green", "atr_at_entry", "sl_price",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def safe_float(val, default=0.0):
    """Parse a value to float, returning default on failure."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_bool(val):
    """Parse a value to bool."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return False
    return str(val).strip().lower() == "true"


def to_ms(ts_str):
    """Parse ISO timestamp string to milliseconds epoch."""
    if not ts_str or (isinstance(ts_str, float) and pd.isna(ts_str)):
        return 0
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def hold_minutes(entry_ts, exit_ts):
    """Compute hold time in minutes between two ISO timestamps."""
    entry_ms = to_ms(entry_ts)
    exit_ms = to_ms(exit_ts)
    if entry_ms == 0 or exit_ms == 0:
        return 0.0
    return max((exit_ms - entry_ms) / 60000.0, 0.0)


# ---------------------------------------------------------------------------
# BingX API (exact copy from run_trade_analysis_v2.py)
# ---------------------------------------------------------------------------


def sign_and_build(base, path, params, api_key, secret):
    """Build signed URL and return (url, headers)."""
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    sig = hmac_lib.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = base + path + "?" + qs + "&signature=" + sig
    return url, {"X-BX-APIKEY": api_key}


def fetch_klines(symbol, start_ms, end_ms, base, api_key, secret):
    """Fetch 5m klines for symbol in [start_ms, end_ms]."""
    params = {
        "symbol": symbol,
        "interval": "5m",
        "startTime": str(start_ms),
        "endTime": str(end_ms),
        "limit": "500",
    }
    url, headers = sign_and_build(base, KLINE_PATH, params, api_key, secret)
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        if data.get("code", -1) != 0:
            return []
        return data.get("data", [])
    except Exception as e:
        log.warning("Kline fetch failed %s: %s", symbol, e)
        return []


# ---------------------------------------------------------------------------
# Indicators (pure pandas/numpy, no TA-Lib)
# ---------------------------------------------------------------------------


def stoch_k(close, high, low, k_len):
    """Raw K stochastic -- no SMA smoothing. Pure numpy loop.
    Exact copy of signals/stochastics.py stoch_k().
    """
    n = len(close)
    result = np.full(n, np.nan)
    for i in range(k_len - 1, n):
        wl = low[i - k_len + 1: i + 1]
        wh = high[i - k_len + 1: i + 1]
        lowest = np.min(wl)
        highest = np.max(wh)
        if highest - lowest == 0:
            result[i] = 50.0
        else:
            result[i] = 100.0 * (close[i] - lowest) / (highest - lowest)
    return result


def compute_indicators(df, entry_idx):
    """Compute all chart indicators on kline DataFrame."""
    c = df["close"].values.astype(float)
    h = df["high"].values.astype(float)
    lo = df["low"].values.astype(float)
    v = df["volume"].values.astype(float)

    # EMA 55 and EMA 89
    df["ema55"] = df["close"].astype(float).ewm(span=55, adjust=False).mean()
    df["ema89"] = df["close"].astype(float).ewm(span=89, adjust=False).mean()

    # AVWAP anchored at entry candle
    tp = (h + lo + c) / 3.0
    avwap = np.full(len(df), np.nan)
    if 0 <= entry_idx < len(df):
        cum_tpv = 0.0
        cum_v = 0.0
        for i in range(entry_idx, len(df)):
            cum_tpv += tp[i] * v[i]
            cum_v += v[i]
            avwap[i] = cum_tpv / cum_v if cum_v > 0 else np.nan
    df["avwap"] = avwap

    # Stochastic 9 -- raw K only
    df["stoch_9"] = stoch_k(c, h, lo, 9)
    # Stochastic 14 -- raw K only
    df["stoch_14"] = stoch_k(c, h, lo, 14)
    # Stochastic 40 -- raw K + D (d_smooth=4)
    s40 = stoch_k(c, h, lo, 40)
    df["stoch_40"] = s40
    df["stoch_40_d"] = pd.Series(s40).rolling(4, min_periods=1).mean().values
    # Stochastic 60 -- raw K + D (d_smooth=10)
    s60 = stoch_k(c, h, lo, 60)
    df["stoch_60"] = s60
    df["stoch_60_d"] = pd.Series(s60).rolling(10, min_periods=1).mean().values

    return df


# ---------------------------------------------------------------------------
# Four Pillars Signal Detection
# ---------------------------------------------------------------------------


def detect_signals(df, cfg):
    """Run Four Pillars signal detection. Returns True if signals added."""
    try:
        _BACKTESTER = ROOT.parent / "four-pillars-backtester"
        if str(_BACKTESTER) not in sys.path:
            sys.path.insert(0, str(_BACKTESTER))
        from signals.four_pillars import compute_signals

        fp = cfg.get("four_pillars", {})
        params = {
            "cross_level": fp.get("cross_level", 25),
            "zone_level": fp.get("zone_level", 30),
            "allow_b_trades": fp.get("allow_b", True),
            "allow_c_trades": fp.get("allow_c", False),
            "require_stage2": fp.get("require_stage2", True),
            "rot_level": fp.get("rot_level", 80),
            "atr_length": fp.get("atr_length", 14),
        }

        sig_df = df.copy()
        if "time" in sig_df.columns and "timestamp" not in sig_df.columns:
            sig_df = sig_df.rename(columns={"time": "timestamp"})
        if "volume" in sig_df.columns and "base_vol" not in sig_df.columns:
            sig_df = sig_df.rename(columns={"volume": "base_vol"})
        if "quote_vol" not in sig_df.columns:
            sig_df["quote_vol"] = 0.0

        sig_df = compute_signals(sig_df, params)

        for col in ["long_a", "long_b", "short_a", "short_b"]:
            if col in sig_df.columns:
                df[col] = sig_df[col].values

        return True
    except Exception as e:
        log.warning("Signal detection failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Trade Loading
# ---------------------------------------------------------------------------


def load_and_filter_trades(target_date, from_time, symbol_filter):
    """Load trades.csv and filter by date/time/symbol."""
    if not TRADES_CSV.exists():
        log.error("trades.csv not found: %s", TRADES_CSV)
        sys.exit(1)

    rows = []
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        _header = next(reader)
        for line in reader:
            while len(line) < len(FULL_COLUMNS):
                line.append("")
            rows.append(dict(zip(FULL_COLUMNS, line[:len(FULL_COLUMNS)])))

    trades = []
    for row in rows:
        entry_time = row.get("entry_time", "")
        if not entry_time:
            continue
        if target_date and not entry_time.startswith(target_date):
            continue
        if from_time:
            try:
                et_dt = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
                et_hm = et_dt.strftime("%H:%M")
                if et_hm < from_time:
                    continue
            except Exception:
                continue
        if symbol_filter and row.get("symbol", "") != symbol_filter:
            continue
        trades.append(row)

    log.info("Filtered to %d trades", len(trades))
    return trades


# ---------------------------------------------------------------------------
# Chart Building
# ---------------------------------------------------------------------------


def build_trade_chart(trade, kline_df, trade_num, has_signals):
    """Build Plotly figure with 3 subplots for one trade."""
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.50, 0.30, 0.20],
    )

    times = kline_df["time_str"].tolist()
    direction = trade.get("direction", "LONG")
    entry_price = safe_float(trade.get("entry_price"))
    exit_price = safe_float(trade.get("exit_price"))
    symbol = trade.get("symbol", "")
    grade = trade.get("grade", "")
    pnl_net = safe_float(trade.get("pnl_net"))
    exit_reason = trade.get("exit_reason", "")
    is_long = direction == "LONG"
    entry_color = "#00ff7f" if is_long else "#ff4444"

    # --- Panel 1: Candlestick + Overlays ---
    fig.add_trace(go.Candlestick(
        x=times, open=kline_df["open"], high=kline_df["high"],
        low=kline_df["low"], close=kline_df["close"],
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        name="OHLC", showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=kline_df["ema55"], mode="lines",
        line=dict(color="#FF8C00", width=1), name="EMA 55",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=kline_df["ema89"], mode="lines",
        line=dict(color="#1E90FF", width=1), name="EMA 89",
    ), row=1, col=1)

    avwap_valid = kline_df[kline_df["avwap"].notna()]
    if len(avwap_valid) > 0:
        fig.add_trace(go.Scatter(
            x=avwap_valid["time_str"].tolist(), y=avwap_valid["avwap"],
            mode="lines", line=dict(color="#FFFFFF", width=1, dash="dash"),
            name="AVWAP",
        ), row=1, col=1)

    # Entry/exit vertical lines (all panels)
    entry_bar_time = trade.get("_entry_bar_time")
    exit_bar_time = trade.get("_exit_bar_time")

    for r in range(1, 4):
        yref_str = "y domain" if r == 1 else ("y" + str(r) + " domain")
        if entry_bar_time:
            fig.add_shape(
                type="line", x0=entry_bar_time, x1=entry_bar_time,
                y0=0, y1=1, yref=yref_str,
                line=dict(color=entry_color, dash="dash", width=1),
                row=r, col=1,
            )
        if exit_bar_time:
            fig.add_shape(
                type="line", x0=exit_bar_time, x1=exit_bar_time,
                y0=0, y1=1, yref=yref_str,
                line=dict(color="#AAAAAA", dash="dot", width=1),
                row=r, col=1,
            )

    # Entry/exit price horizontals
    fig.add_hline(
        y=entry_price, line_dash="dot", line_color=entry_color,
        line_width=1, opacity=0.6, row=1, col=1,
    )
    fig.add_hline(
        y=exit_price, line_dash="dot", line_color="#AAAAAA",
        line_width=1, opacity=0.6, row=1, col=1,
    )

    # Four Pillars signal vertical lines
    if has_signals:
        signal_defs = [
            ("long_a", "green", "solid", 2, 0.9, "A\u2191"),
            ("long_b", "green", "dash", 1.5, 0.7, "B\u2191"),
            ("short_a", "red", "solid", 2, 0.9, "A\u2193"),
            ("short_b", "red", "dash", 1.5, 0.7, "B\u2193"),
        ]
        for col, color, dash, width, opacity, label in signal_defs:
            if col not in kline_df.columns:
                continue
            sig_mask = kline_df[col].fillna(False).astype(bool)
            sig_bars = kline_df[sig_mask]
            for _, sbar in sig_bars.iterrows():
                st = sbar["time_str"]
                fig.add_shape(
                    type="line", x0=st, x1=st, y0=0, y1=1,
                    yref="y domain",
                    line=dict(color=color, dash=dash, width=width),
                    opacity=opacity, row=1, col=1,
                )
                fig.add_annotation(
                    x=st, y=1.0, yref="y domain",
                    text=label, showarrow=False,
                    font=dict(size=9, color=color),
                    yanchor="bottom", row=1, col=1,
                )
                fig.add_shape(
                    type="line", x0=st, x1=st, y0=0, y1=1,
                    yref="y2 domain",
                    line=dict(color=color, dash=dash, width=width),
                    opacity=0.4, row=2, col=1,
                )

    # Annotation box
    hold_min = hold_minutes(trade.get("entry_time"), trade.get("timestamp"))
    be_raised = safe_bool(trade.get("be_raised"))
    ttp_act = safe_bool(trade.get("ttp_activated"))
    n_la = int(kline_df["long_a"].sum()) if has_signals and "long_a" in kline_df.columns else 0
    n_lb = int(kline_df["long_b"].sum()) if has_signals and "long_b" in kline_df.columns else 0
    n_sa = int(kline_df["short_a"].sum()) if has_signals and "short_a" in kline_df.columns else 0
    n_sb = int(kline_df["short_b"].sum()) if has_signals and "short_b" in kline_df.columns else 0

    annot_parts = [
        symbol + " | " + direction + " | " + grade,
        "Entry: " + str(entry_price) + " -> Exit: " + str(exit_price),
        "PnL: $" + str(round(pnl_net, 4)) + " | Reason: " + exit_reason,
        "Hold: " + str(int(hold_min)) + "m | BE: " + str(be_raised) + " | TTP: " + str(ttp_act),
        "Signals: " + str(n_la) + "A\u2191 " + str(n_lb) + "B\u2191 " + str(n_sa) + "A\u2193 " + str(n_sb) + "B\u2193 in window",
    ]
    annot_text = "<br>".join(annot_parts)

    fig.add_annotation(
        x=0.01, y=0.99, xref="x domain", yref="y domain",
        text=annot_text, showarrow=False,
        font=dict(family="Courier New, monospace", size=10, color="#c9d1d9"),
        align="left", bgcolor="rgba(22, 27, 34, 0.85)",
        bordercolor="rgba(0,0,0,0)", borderwidth=0,
        row=1, col=1,
    )

    # --- Panel 2: Stochastics ---
    stoch_traces = [
        ("stoch_9", "#00BFFF", 1, "solid", "K9"),
        ("stoch_14", "#DA70D6", 1, "solid", "K14"),
        ("stoch_40", "#FFD700", 1.5, "solid", "K40"),
        ("stoch_40_d", "#FFD700", 1, "dot", "D40"),
        ("stoch_60", "#FF6347", 2, "solid", "K60"),
        ("stoch_60_d", "#FF6347", 1.5, "dot", "D60"),
    ]
    for col, color, width, dash, name in stoch_traces:
        if col in kline_df.columns:
            fig.add_trace(go.Scatter(
                x=times, y=kline_df[col], mode="lines",
                line=dict(color=color, width=width, dash=dash),
                name=name,
            ), row=2, col=1)

    fig.add_hline(y=80, line_dash="dash", line_color="red", line_width=0.5, opacity=0.4, row=2, col=1)
    fig.add_hline(y=20, line_dash="dash", line_color="green", line_width=0.5, opacity=0.4, row=2, col=1)
    fig.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.08, line_width=0, row=2, col=1)
    fig.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.08, line_width=0, row=2, col=1)

    # --- Panel 3: Volume ---
    vol_colors = [
        "#26a69a" if float(c) >= float(o) else "#ef5350"
        for c, o in zip(kline_df["close"], kline_df["open"])
    ]
    fig.add_trace(go.Bar(
        x=times, y=kline_df["volume"], marker_color=vol_colors,
        name="Volume", showlegend=False,
    ), row=3, col=1)

    # Layout
    entry_time_str = trade.get("entry_time", "")[:19]
    title_text = "#" + str(trade_num) + " " + symbol + " | " + direction + " | " + entry_time_str + " | PnL: $" + str(round(pnl_net, 4))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="Courier New, monospace", size=11),
        height=900,
        margin=dict(l=60, r=20, t=40, b=20),
        title=dict(text=title_text, font=dict(size=12)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
    )
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    return fig


# ---------------------------------------------------------------------------
# HTML Assembly
# ---------------------------------------------------------------------------


def build_html_report(trades_info, charts_html, target_date, from_time):
    """Assemble the full HTML report."""
    total = len(trades_info)
    wins = sum(1 for t in trades_info if t["pnl"] > 0)
    wr = round(wins / total * 100, 1) if total > 0 else 0.0
    net_pnl = round(sum(t["pnl"] for t in trades_info), 4)
    first_t = min(t["entry_time"] for t in trades_info) if trades_info else ""
    last_t = max(t["entry_time"] for t in trades_info) if trades_info else ""

    p = []
    p.append("<!DOCTYPE html>")
    p.append('<html lang="en">')
    p.append("<head>")
    p.append('<meta charset="utf-8">')
    p.append("<title>Trade Chart Report " + target_date + "</title>")
    p.append('<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>')
    p.append("<style>")
    p.append("* { box-sizing: border-box; margin: 0; padding: 0; }")
    p.append('body { background: #0d1117; color: #c9d1d9; font-family: "Courier New", monospace; font-size: 12px; }')
    p.append("#summary-bar { position: fixed; top: 0; left: 0; right: 0; z-index: 1000; background: #161b22; padding: 8px 16px; font-size: 12px; border-bottom: 1px solid #30363d; }")
    p.append("#sidebar { position: fixed; left: 0; top: 36px; bottom: 0; width: 220px; overflow-y: auto; background: #0d1117; border-right: 1px solid #30363d; padding: 8px; }")
    p.append("#sidebar .sidebar-header { color: #58a6ff; font-weight: bold; margin-bottom: 8px; text-align: center; }")
    p.append("#sidebar a { display: block; padding: 3px 4px; text-decoration: none; font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }")
    p.append("#sidebar a:hover { background: #161b22; border-radius: 3px; }")
    p.append("#main { margin-left: 230px; padding: 50px 16px 16px 16px; }")
    p.append(".trade-section { margin-bottom: 24px; border: 1px solid #30363d; border-radius: 6px; padding: 12px; background: #0d1117; }")
    p.append(".trade-header { color: #58a6ff; font-size: 13px; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #21262d; }")
    p.append(".note-box { margin-top: 8px; }")
    p.append(".note-box label { color: #8b949e; display: block; margin-bottom: 4px; }")
    p.append(".note-box textarea { width: 100%; background: #161b22; border: 1px solid #30363d; color: #c9d1d9; font-family: 'Courier New', monospace; font-size: 11px; padding: 8px; border-radius: 4px; resize: vertical; }")
    p.append(".note-box .note-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }")
    p.append(".note-box .char-count { color: #484f58; font-size: 10px; }")
    p.append(".note-box button { background: #238636; color: #fff; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-family: 'Courier New', monospace; }")
    p.append(".note-box button:hover { background: #2ea043; }")
    p.append(".no-chart { color: #484f58; text-align: center; padding: 100px 0; font-size: 14px; }")
    p.append("#footer { text-align: center; color: #484f58; font-size: 10px; padding: 16px; margin-left: 230px; border-top: 1px solid #21262d; }")
    p.append("</style>")
    p.append("</head>")
    p.append("<body>")

    # Summary bar
    summary_text = (
        "Date: " + target_date
        + " | Trades: " + str(total)
        + " | WR: " + str(wr) + "%"
        + " | Net PnL: $" + str(net_pnl)
        + " | " + first_t[:16] + " &rarr; " + last_t[:16]
    )
    p.append('<div id="summary-bar">' + summary_text + "</div>")

    # Sidebar
    p.append('<div id="sidebar">')
    p.append('<div class="sidebar-header">&mdash;&mdash; TRADES &mdash;&mdash;</div>')
    for i, info in enumerate(trades_info, 1):
        clr = "#00ff7f" if info["pnl"] > 0 else "#ef5350"
        dir_short = "L" if info["direction"] == "LONG" else "S"
        link_text = "#" + str(i) + " " + info["symbol"] + " " + dir_short + " $" + str(round(info["pnl"], 4))
        p.append('<a href="#trade-' + str(i) + '" style="color:' + clr + '">' + link_text + "</a>")
    p.append("</div>")

    # Main content
    p.append('<div id="main">')
    for i, (info, chart_html) in enumerate(zip(trades_info, charts_html), 1):
        p.append('<section id="trade-' + str(i) + '" class="trade-section">')
        entry_t = info["entry_time"][:19]
        exit_t = info["exit_time"][:19]
        header = (
            "#" + str(i) + " " + info["symbol"]
            + " | " + info["direction"]
            + " | " + info["grade"]
            + " | " + entry_t + " &rarr; " + exit_t
            + " | " + info["exit_reason"]
        )
        p.append('<div class="trade-header">' + header + "</div>")
        p.append(chart_html)
        # Note box
        p.append('<div class="note-box">')
        p.append("<label>Trade Notes:</label>")
        p.append('<textarea id="note-' + str(i) + '" rows="4" placeholder="Add your notes about this trade..." onkeyup="updateCount(' + str(i) + ')"></textarea>')
        p.append('<div class="note-footer">')
        p.append('<span class="char-count" id="count-' + str(i) + '">0 chars</span>')
        p.append('<button id="btn-' + str(i) + '" onclick="saveNote(' + str(i) + ')">Save Note</button>')
        p.append("</div>")
        p.append("</div>")
        p.append("</section>")
    p.append("</div>")

    # Footer
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p.append('<div id="footer">Generated: ' + now_str + " | " + str(total) + " trades | run_trade_chart_report.py | bingx-connector-v2</div>")

    # JavaScript for localStorage notes
    p.append("<script>")
    p.append('var REPORT_DATE = "' + target_date + '";')
    p.append("function saveNote(n) {")
    p.append('  var ta = document.getElementById("note-" + n);')
    p.append('  var key = "bingx_note_" + REPORT_DATE + "_" + n;')
    p.append("  localStorage.setItem(key, ta.value);")
    p.append('  var btn = document.getElementById("btn-" + n);')
    p.append('  btn.textContent = "Saved \\u2713";')
    p.append('  setTimeout(function() { btn.textContent = "Save Note"; }, 1500);')
    p.append("}")
    p.append("function updateCount(n) {")
    p.append('  var ta = document.getElementById("note-" + n);')
    p.append('  var span = document.getElementById("count-" + n);')
    p.append('  span.textContent = ta.value.length + " chars";')
    p.append("}")
    p.append('window.addEventListener("load", function() {')
    p.append('  var areas = document.querySelectorAll("textarea[id^=note-]");')
    p.append("  areas.forEach(function(ta) {")
    p.append('    var n = ta.id.replace("note-", "");')
    p.append('    var key = "bingx_note_" + REPORT_DATE + "_" + n;')
    p.append("    var saved = localStorage.getItem(key);")
    p.append("    if (saved) ta.value = saved;")
    p.append("    updateCount(parseInt(n));")
    p.append("  });")
    p.append("});")
    p.append("</script>")

    p.append("</body>")
    p.append("</html>")

    return "\n".join(p)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Run the trade chart report generator."""
    parser = argparse.ArgumentParser(description="Trade Chart Report Generator")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"),
                        help="Filter trades from this date (YYYY-MM-DD, default: today)")
    parser.add_argument("--from-time", default=None,
                        help="Filter start time within date (HH:MM, default: 00:00)")
    parser.add_argument("--symbol", default=None,
                        help="Filter to one symbol only")
    parser.add_argument("--no-api", action="store_true",
                        help="Skip live kline fetch; use CSV data only")
    args = parser.parse_args()

    target_date = args.date
    from_time = args.from_time
    symbol_filter = args.symbol
    no_api = args.no_api

    # Load config
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    demo_mode = cfg.get("connector", {}).get("demo_mode", False)
    base_url = "https://open-api-vst.bingx.com" if demo_mode else "https://open-api.bingx.com"

    # Load credentials
    api_key = ""
    secret_key = ""
    if not no_api:
        if load_dotenv is not None:
            load_dotenv(ROOT / ".env")
        api_key = os.getenv("BINGX_API_KEY", "")
        secret_key = os.getenv("BINGX_SECRET_KEY", "")
        if not api_key or not secret_key:
            log.warning("Missing API credentials -- falling back to --no-api mode")
            no_api = True

    # Load and filter trades
    trades = load_and_filter_trades(target_date, from_time, symbol_filter)
    if not trades:
        print("No trades found for " + target_date)
        sys.exit(0)

    log.info("Processing %d trades for %s", len(trades), target_date)

    # Process each trade
    trades_info = []
    charts_html = []

    for idx, trade in enumerate(trades, 1):
        symbol = trade.get("symbol", "")
        entry_time = trade.get("entry_time", "")
        exit_time = trade.get("timestamp", "")
        pnl = safe_float(trade.get("pnl_net"))

        info = {
            "symbol": symbol,
            "direction": trade.get("direction", ""),
            "grade": trade.get("grade", ""),
            "entry_time": entry_time,
            "exit_time": exit_time,
            "exit_reason": trade.get("exit_reason", ""),
            "pnl": pnl,
        }
        trades_info.append(info)

        if no_api:
            charts_html.append('<div class="no-chart">No chart data available (--no-api mode)</div>')
            continue

        # Fetch klines
        entry_ms = to_ms(entry_time)
        exit_ms = to_ms(exit_time)
        if entry_ms == 0:
            charts_html.append('<div class="no-chart">Invalid entry time</div>')
            continue

        candle_ms = 5 * 60 * 1000  # 5 minutes
        start_ms = entry_ms - (60 * candle_ms)
        end_ms = exit_ms + (20 * candle_ms) if exit_ms > 0 else entry_ms + (80 * candle_ms)

        log.info("[%d/%d] Fetching klines for %s ...", idx, len(trades), symbol)
        klines = fetch_klines(symbol, start_ms, end_ms, base_url, api_key, secret_key)
        time.sleep(0.3)

        if not klines:
            charts_html.append('<div class="no-chart">No kline data returned for ' + symbol + "</div>")
            continue

        # Build DataFrame from klines
        kline_df = pd.DataFrame(klines)
        for col in ["open", "high", "low", "close", "volume"]:
            if col in kline_df.columns:
                kline_df[col] = kline_df[col].astype(float)
        kline_df["time"] = kline_df["time"].astype(int)
        kline_df = kline_df.sort_values("time").reset_index(drop=True)
        kline_df["time_dt"] = pd.to_datetime(kline_df["time"], unit="ms", utc=True)
        kline_df["time_str"] = kline_df["time_dt"].dt.strftime("%Y-%m-%d %H:%M")

        # Find entry/exit bar indices
        diffs_entry = np.abs(kline_df["time"].values - entry_ms)
        entry_idx = int(np.argmin(diffs_entry))
        diffs_exit = np.abs(kline_df["time"].values - exit_ms) if exit_ms > 0 else diffs_entry
        exit_idx = int(np.argmin(diffs_exit))

        trade["_entry_bar_time"] = kline_df.iloc[entry_idx]["time_str"]
        trade["_exit_bar_time"] = kline_df.iloc[exit_idx]["time_str"]

        # Compute indicators
        kline_df = compute_indicators(kline_df, entry_idx)

        # Detect Four Pillars signals
        has_signals = detect_signals(kline_df, cfg)

        # Build chart
        fig = build_trade_chart(trade, kline_df, idx, has_signals)
        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs=False)
        charts_html.append(chart_html)

        log.info("[%d/%d] %s chart built (%d bars)", idx, len(trades), symbol, len(kline_df))

    # Build HTML report
    html_content = build_html_report(trades_info, charts_html, target_date, from_time or "00:00")

    # Write output
    LOG_DIR.mkdir(exist_ok=True)
    out_path = LOG_DIR / ("trade_chart_report_" + target_date + ".html")
    out_path.write_text(html_content, encoding="utf-8")
    log.info("Report written: %s", out_path)
    print("Done. Report: " + str(out_path))


if __name__ == "__main__":
    main()
