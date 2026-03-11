"""
Build script for dashboard_55_89_v3.py.
Writes scripts/dashboard_55_89_v3.py then validates with py_compile + ast.parse.
Run: python scripts/build_dashboard_55_89_v3.py
"""
import ast
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "dashboard_55_89_v3.py"

ERRORS = []


def check_file(path):
    """Run py_compile and ast.parse on path; print result; return True if clean."""
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        ERRORS.append(str(path))
        return False
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        print("  AST ERROR line " + str(e.lineno) + ": " + str(e.msg))
        ERRORS.append(str(path))
        return False
    print("  SYNTAX OK: " + str(path))
    return True


DASHBOARD_SOURCE = '''\
"""
55/89 EMA Cross Scalp Dashboard v3.

Changes from v2:
  1. Re-roll seed fix: seeds with time.time_ns() + counter on every click.
  2. Portfolio capital mode: Shared pool / Per-coin toggle.
  3. Missing metrics: Trading Volume and LSG% in single mode Row 3;
     Rebate and Volume columns in portfolio per-coin table.
  4. CPU/GPU engine toggle: GPU runs run_gpu_sweep() sl_mult x be_trigger grid
     in single mode, outputs two heatmaps + top-3 table.
  5. PDF export: reportlab + kaleido, metadata + metrics + equity curve PNG.

Run from backtester root:
  streamlit run scripts/dashboard_55_89_v3.py
"""

import io
import sys
import time
import random
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from signals.ema_cross_55_89 import compute_signals_55_89
from engine.backtester_v384 import Backtester384

try:
    from engine.cuda_sweep import CUDA_AVAILABLE, run_gpu_sweep, build_param_grid
except ImportError:
    CUDA_AVAILABLE = False
    run_gpu_sweep = None
    build_param_grid = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle,
        Paragraph, Spacer,
    )
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import plotly.io as pio
    # Kaleido availability is verified at use time via pio.to_image
    KALEIDO_AVAILABLE = True
except ImportError:
    KALEIDO_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COLORS = {
    "bg": "#0f1419", "card": "#1a1f26", "text": "#e7e9ea",
    "green": "#10b981", "red": "#ef4444", "blue": "#3b82f6",
    "orange": "#f59e0b", "purple": "#8b5cf6", "gray": "#6b7280",
    "teal": "#14b8a6",
}
COMMISSION_RATE = 0.0008


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_symbol_list():
    """Scan data/historical/ and data/cache/ for *_1m.parquet files."""
    symbols = set()
    for subdir in ["historical", "cache"]:
        d = ROOT / "data" / subdir
        if d.exists():
            for f in d.glob("*_1m.parquet"):
                sym = f.stem.replace("_1m", "")
                symbols.add(sym)
    return sorted(symbols)


def load_data(symbol):
    """Load 1m parquet for symbol; normalize column names for engine."""
    for subdir in ["historical", "cache"]:
        path = ROOT / "data" / subdir / (symbol + "_1m.parquet")
        if path.exists():
            df = pd.read_parquet(path)
            if "volume" in df.columns and "base_vol" not in df.columns:
                df = df.rename(columns={"volume": "base_vol"})
            if "turnover" in df.columns and "quote_vol" not in df.columns:
                df = df.rename(columns={"turnover": "quote_vol"})
            return df
    return None


def apply_date_filter(df, date_range):
    """Filter DataFrame to [start, end] inclusive; return filtered copy or original."""
    if date_range is None:
        return df
    start_date, end_date = date_range
    start_ts = pd.Timestamp(start_date, tz="UTC")
    end_ts = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    if "datetime" in df.columns:
        dt_col = pd.to_datetime(df["datetime"], utc=True)
        mask = (dt_col >= start_ts) & (dt_col < end_ts)
        return df[mask].reset_index(drop=True)
    elif isinstance(df.index, pd.DatetimeIndex):
        idx = df.index
        if idx.tzinfo is None:
            idx = idx.tz_localize("UTC")
        mask = (idx >= start_ts) & (idx < end_ts)
        return df[mask].reset_index(drop=True)
    return df


def resolve_date_range(preset, custom_start=None, custom_end=None, random_range=None):
    """Resolve period preset to (start_date, end_date) or None for All."""
    if preset == "All":
        return None
    if preset == "Custom":
        if custom_start and custom_end:
            return (custom_start, custom_end)
        return None
    if preset in ("Random Week", "Random Month"):
        return random_range
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    n = days_map.get(preset, 30)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=n)
    return (start, end)


def get_data_date_bounds(symbol):
    """Return (min_date, max_date) from coin parquet, or None if unavailable."""
    for subdir in ["historical", "cache"]:
        path = ROOT / "data" / subdir / (symbol + "_1m.parquet")
        if path.exists():
            try:
                df = pd.read_parquet(path, columns=["datetime"])
                dt = pd.to_datetime(df["datetime"], utc=True)
                return dt.min().date(), dt.max().date()
            except Exception:
                pass
    return None


def roll_random_range(symbol, window_days, seed=None):
    """Pick a random start date from the coin data; return (start, end) pair."""
    if seed is not None:
        random.seed(seed)
    bounds = get_data_date_bounds(symbol)
    if bounds is None:
        end = datetime.now(timezone.utc).date()
        return (end - timedelta(days=window_days), end)
    data_start, data_end = bounds
    latest_start = data_end - timedelta(days=window_days)
    if latest_start <= data_start:
        return (data_start, data_end)
    span = (latest_start - data_start).days
    offset = random.randint(0, span)
    start = data_start + timedelta(days=offset)
    end = start + timedelta(days=window_days)
    return (start, end)


def compute_params_hash(sig_params, bt_params, date_range, symbols):
    """Compute MD5 hash of all run params for cache invalidation."""
    key = json.dumps(
        {
            "sig": sig_params,
            "bt": {k: str(v) for k, v in bt_params.items()},
            "dr": str(date_range),
            "syms": sorted(symbols) if isinstance(symbols, list) else [symbols],
        },
        sort_keys=True,
    )
    return hashlib.md5(key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Backtest runners
# ---------------------------------------------------------------------------

def run_backtest_55_89(df, sig_params, bt_params):
    """Run compute_signals_55_89 then Backtester384; return (results, df_sig, timings)."""
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    t1 = time.perf_counter()
    bt = Backtester384(bt_params)
    results = bt.run(df_sig)
    t2 = time.perf_counter()
    return results, df_sig, (t1 - t0, t2 - t1)


def run_gpu_sweep_55_89(df, sig_params, notional, sl_range_max, be_range_max):
    """Compute signals on CPU then run GPU sweep; return (df_sweep, df_sig, timings)."""
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    t1 = time.perf_counter()
    sl_vals = np.arange(0.5, sl_range_max + 0.1, 0.5)
    be_vals = np.arange(0.0, be_range_max + 0.1, 0.5)
    param_grid = build_param_grid(
        sl_range=sl_vals,
        tp_range=[],
        be_vals=list(be_vals),
        cooldown_vals=[1],
        include_no_tp=True,
    )
    df_sweep = run_gpu_sweep(
        df_sig, param_grid,
        notional_val=float(notional),
        comm_rate=COMMISSION_RATE,
    )
    t2 = time.perf_counter()
    return df_sweep, df_sig, (t1 - t0, t2 - t1)


# ---------------------------------------------------------------------------
# Portfolio equity alignment
# ---------------------------------------------------------------------------

def align_portfolio_equity_55_89(coin_results, initial_equity, pool_mode=False, total_capital=None):
    """Build master datetime index, ffill-align per-coin equity, sum to portfolio.

    pool_mode: if True use total_capital as baseline; else initial_equity * n_coins.
    """
    master_dt = pd.DatetimeIndex([])
    for cr in coin_results:
        master_dt = master_dt.union(pd.DatetimeIndex(cr["datetime_index"]))
    master_dt = master_dt.sort_values()

    portfolio_eq = np.zeros(len(master_dt))
    per_coin_eq = {}
    for cr in coin_results:
        sym = cr["symbol"]
        dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        eq_series = pd.Series(cr["equity_curve"], index=dt_idx)
        fill_val = float(eq_series.iloc[0]) if len(eq_series) > 0 else float(initial_equity)
        eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(fill_val).values
        per_coin_eq[sym] = eq_aligned
        portfolio_eq += eq_aligned

    peaks = np.maximum.accumulate(portfolio_eq)
    safe_peaks = np.where(peaks > 0, peaks, 1.0)
    dd_arr = np.clip((portfolio_eq - peaks) / safe_peaks * 100.0, -100.0, 0.0)
    max_dd_pct = float(dd_arr.min())

    if pool_mode and total_capital is not None:
        baseline = float(total_capital)
    else:
        baseline = float(initial_equity) * len(coin_results)

    return {
        "master_dt": master_dt,
        "portfolio_eq": portfolio_eq,
        "per_coin_eq": per_coin_eq,
        "portfolio_dd_pct": round(max_dd_pct, 2),
        "baseline": baseline,
    }


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_dollar(val):
    """Format float as dollar string with sign."""
    if val >= 0:
        return "$" + "{:.2f}".format(val)
    return "-$" + "{:.2f}".format(abs(val))


def fmt_vol(val):
    """Format volume as compact dollar string."""
    if val >= 1_000_000:
        return "$" + "{:.1f}".format(val / 1_000_000) + "M"
    if val >= 1_000:
        return "$" + "{:.1f}".format(val / 1_000) + "k"
    return "$" + "{:.0f}".format(val)


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def _build_equity_fig(eq, x_axis):
    """Build equity curve Plotly figure for PDF embedding."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_axis, y=eq, mode="lines", name="Equity",
        line=dict(color="#3b82f6", width=1),
    ))
    fig.update_layout(
        template="plotly_dark", height=350,
        paper_bgcolor="#0f1419", plot_bgcolor="#1a1f26",
        margin=dict(l=40, r=20, t=30, b=30),
        xaxis_title="", yaxis_title="Equity ($)",
    )
    return fig


def _fig_to_png_bytes(fig):
    """Render Plotly figure to PNG bytes via kaleido; return None on failure."""
    if not KALEIDO_AVAILABLE:
        return None
    try:
        return pio.to_image(fig, format="png", width=1000, height=400)
    except Exception:
        return None


def generate_pdf_55_89(mode, cached, bt_params, date_range):
    """Generate PDF report bytes for single or portfolio mode results."""
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=36, bottomMargin=36,
    )
    story = []

    ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    dr_str = str(date_range) if date_range else "All"

    # --- Page 1: Metadata ---
    story.append(Paragraph("55/89 EMA Cross Scalp Backtest Report", h1))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Generated: " + ts_str, normal))
    story.append(Spacer(1, 6))

    if mode == "Single":
        sym = cached.get("symbol", "")
        story.append(Paragraph("Symbol: " + sym, normal))
        story.append(Paragraph("Date range: " + dr_str, normal))
        story.append(Spacer(1, 6))
        meta_rows = [
            ["Parameter", "Value"],
            ["Margin", "$" + "{:.0f}".format(bt_params.get("margin", 0))],
            ["Leverage", str(bt_params.get("leverage", 0)) + "x"],
            ["Notional", "$" + "{:,.0f}".format(bt_params.get("notional", 0))],
            ["SL mult", str(bt_params.get("sl_mult", 0)) + "x ATR"],
            ["BE trigger", str(bt_params.get("be_trigger_atr", 0)) + "x ATR"],
            ["Rebate %", "{:.0%}".format(bt_params.get("rebate_pct", 0))],
            ["Initial equity", "$" + "{:,.0f}".format(bt_params.get("initial_equity", 0))],
        ]
    else:
        coin_results = cached.get("coin_results", [])
        n_coins = len(coin_results)
        story.append(Paragraph("Mode: Portfolio (" + str(n_coins) + " coins)", normal))
        story.append(Paragraph("Date range: " + dr_str, normal))
        story.append(Spacer(1, 6))
        meta_rows = [
            ["Parameter", "Value"],
            ["Coins", str(n_coins)],
            ["Margin", "$" + "{:.0f}".format(bt_params.get("margin", 0))],
            ["Leverage", str(bt_params.get("leverage", 0)) + "x"],
            ["Notional", "$" + "{:,.0f}".format(bt_params.get("notional", 0))],
            ["SL mult", str(bt_params.get("sl_mult", 0)) + "x ATR"],
            ["Rebate %", "{:.0%}".format(bt_params.get("rebate_pct", 0))],
        ]

    meta_table = Table(meta_rows, colWidths=[160, 260])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.lightgrey]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # --- Page 2: Metrics ---
    story.append(Paragraph("Metrics", h2))
    story.append(Spacer(1, 8))

    if mode == "Single":
        m = cached.get("results", {}).get("metrics", {})
        metrics_rows = [
            ["Metric", "Value"],
            ["Total trades", str(m.get("total_trades", 0))],
            ["Win rate", "{:.1%}".format(m.get("win_rate", 0))],
            ["Net PnL", fmt_dollar(m.get("net_pnl", 0))],
            ["Profit factor", "{:.2f}".format(m.get("profit_factor", 0))],
            ["Sharpe", "{:.3f}".format(m.get("sharpe", 0))],
            ["Max DD", "{:.1f}%".format(m.get("max_drawdown_pct", 0))],
            ["Avg win", fmt_dollar(m.get("avg_win", 0))],
            ["Avg loss", fmt_dollar(m.get("avg_loss", 0))],
            ["Expectancy", fmt_dollar(m.get("expectancy", 0))],
            ["Commission", "$" + "{:.2f}".format(m.get("total_commission", 0))],
            ["Rebate $", "$" + "{:.2f}".format(m.get("total_rebate", 0))],
            ["Net w/Rebate", fmt_dollar(m.get("net_pnl_after_rebate", m.get("net_pnl", 0)))],
            ["BE raises", str(m.get("be_raised_count", 0))],
            ["LSG%", "{:.1f}%".format(m.get("pct_losers_saw_green", 0) * 100)],
            ["Volume $", fmt_vol(m.get("total_volume", 0))],
        ]
    else:
        coin_results = cached.get("coin_results", [])
        pf_data = cached.get("pf_data", {})
        portfolio_eq = pf_data.get("portfolio_eq", np.array([]))
        baseline = pf_data.get("baseline", 0.0)
        net_pnl_total = float(portfolio_eq[-1]) - baseline if len(portfolio_eq) > 0 else 0.0
        total_trades = sum(cr["metrics"].get("total_trades", 0) for cr in coin_results)
        metrics_rows = [
            ["Metric", "Value"],
            ["Coins", str(len(coin_results))],
            ["Total trades", str(total_trades)],
            ["Portfolio net PnL", fmt_dollar(net_pnl_total)],
            ["Max DD", "{:.1f}%".format(pf_data.get("portfolio_dd_pct", 0))],
        ]

    mt = Table(metrics_rows, colWidths=[200, 220])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), rl_colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.lightgrey]),
    ]))
    story.append(mt)
    story.append(Spacer(1, 18))

    # --- Page 3: Equity curve image ---
    story.append(Paragraph("Equity Curve", h2))
    story.append(Spacer(1, 8))

    if mode == "Single":
        eq = cached.get("results", {}).get("equity_curve", [])
        df_sig = cached.get("df_sig", pd.DataFrame())
        if "datetime" in df_sig.columns:
            x_axis = pd.to_datetime(df_sig["datetime"]).values
        else:
            x_axis = np.arange(len(eq))
        fig = _build_equity_fig(eq, x_axis)
        png_bytes = _fig_to_png_bytes(fig)
        if png_bytes:
            story.append(RLImage(io.BytesIO(png_bytes), width=480, height=192))
        else:
            story.append(Paragraph("Chart not available — install kaleido for chart images.", normal))
    else:
        pf_data = cached.get("pf_data", {})
        portfolio_eq = pf_data.get("portfolio_eq", np.array([]))
        master_dt = pf_data.get("master_dt", pd.DatetimeIndex([]))
        x_axis = master_dt.values if len(master_dt) > 0 else np.arange(len(portfolio_eq))
        fig = _build_equity_fig(portfolio_eq, x_axis)
        png_bytes = _fig_to_png_bytes(fig)
        if png_bytes:
            story.append(RLImage(io.BytesIO(png_bytes), width=480, height=192))
        else:
            story.append(Paragraph("Chart not available — install kaleido for chart images.", normal))

    # --- Page 4 (portfolio only): per-coin table ---
    if mode == "Portfolio":
        story.append(Spacer(1, 18))
        story.append(Paragraph("Per-Coin Summary", h2))
        story.append(Spacer(1, 8))
        coin_results = cached.get("coin_results", [])
        coin_rows = [["Symbol", "Trades", "WR%", "Net $", "Rebate $", "Volume $", "Sharpe", "DD%"]]
        for cr in sorted(coin_results, key=lambda x: x["metrics"].get("net_pnl", 0), reverse=True):
            m = cr["metrics"]
            coin_rows.append([
                cr["symbol"],
                str(m.get("total_trades", 0)),
                "{:.1f}".format(m.get("win_rate", 0) * 100),
                fmt_dollar(m.get("net_pnl", 0)),
                "$" + "{:.2f}".format(m.get("total_rebate", 0)),
                fmt_vol(m.get("total_volume", 0)),
                "{:.3f}".format(m.get("sharpe", 0)),
                "{:.1f}%".format(m.get("max_drawdown_pct", 0)),
            ])
        ct = Table(coin_rows)
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), rl_colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, rl_colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_colors.white, rl_colors.lightgrey]),
        ]))
        story.append(ct)

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def render_single_results(symbol, results, df_sig, timings, bt_params, date_range):
    """Render single-coin CPU backtest results: metrics, equity curve, trades table."""
    m = results["metrics"]
    eq = results["equity_curve"]
    trades_df = results.get("trades_df", pd.DataFrame())

    notional = bt_params["notional"]
    leverage = bt_params["leverage"]

    ts_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    dr_str = str(date_range) if date_range else "All"
    long_count = int(df_sig["long_a"].sum())
    short_count = int(df_sig["short_a"].sum())

    st.subheader(symbol + " -- Results")
    st.caption(
        "Date: " + dr_str
        + " | Bars: " + "{:,}".format(len(df_sig))
        + " | Signals: " + str(long_count) + "L / " + str(short_count) + "S"
        + " | Notional: $" + "{:,.0f}".format(notional)
        + " (" + str(int(leverage)) + "x)"
        + " | Signal: " + "{:.1f}s".format(timings[0])
        + " | Engine: " + "{:.1f}s".format(timings[1])
        + " | " + ts_str + " UTC"
    )

    total_trades = m.get("total_trades", 0)

    # Row 1: 6 cols
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Trades", total_trades)
    c2.metric("Win Rate", "{:.1%}".format(m.get("win_rate", 0)))
    c3.metric("Net PnL", fmt_dollar(m.get("net_pnl", 0)))
    c4.metric("Profit Factor", "{:.2f}".format(m.get("profit_factor", 0)))
    c5.metric("Sharpe", "{:.3f}".format(m.get("sharpe", 0)))
    c6.metric("Max DD", "{:.1f}%".format(m.get("max_drawdown_pct", 0)))

    # Row 2: 4 cols
    c7, c8, c9, c10 = st.columns(4)
    c7.metric("Avg Win", fmt_dollar(m.get("avg_win", 0)))
    c8.metric("Avg Loss", fmt_dollar(m.get("avg_loss", 0)))
    c9.metric("Expectancy", fmt_dollar(m.get("expectancy", 0)))
    c10.metric("Commission", "$" + "{:.2f}".format(m.get("total_commission", 0)))

    # Row 3: 5 cols (v3: added Volume $ and LSG%)
    c11, c12, c13, c14, c15 = st.columns(5)
    total_volume = m.get("total_volume", 0.0)
    total_rebate = m.get("total_rebate", 0.0)
    net_after_rebate = m.get("net_pnl_after_rebate", m.get("net_pnl", 0))
    be_raises = m.get("be_raised_count", 0)
    lsg_pct = m.get("pct_losers_saw_green", 0.0) * 100.0
    c11.metric("Volume $", fmt_vol(total_volume))
    c12.metric("Rebate $", "$" + "{:.2f}".format(total_rebate))
    c13.metric("Net w/Rebate", fmt_dollar(net_after_rebate))
    c14.metric("BE Raises", be_raises)
    c15.metric("LSG%", "{:.1f}%".format(lsg_pct))

    # Equity curve
    st.subheader("Equity Curve")
    fig_eq = go.Figure()
    if "datetime" in df_sig.columns:
        x_axis = pd.to_datetime(df_sig["datetime"]).values
    else:
        x_axis = np.arange(len(eq))
    fig_eq.add_trace(go.Scatter(
        x=x_axis, y=eq, mode="lines", name="Equity",
        line=dict(color=COLORS["blue"], width=1),
    ))
    fig_eq.update_layout(
        template="plotly_dark", height=350,
        paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
        margin=dict(l=40, r=20, t=30, b=30),
        xaxis_title="", yaxis_title="Equity ($)",
    )
    st.plotly_chart(fig_eq, use_container_width=True)

    # Trades table
    if total_trades > 0 and len(trades_df) > 0:
        st.subheader("Trades")
        display_cols = [c for c in [
            "direction", "entry_price", "exit_price", "pnl", "commission",
            "net_pnl", "mfe", "mae", "exit_reason", "saw_green",
        ] if c in trades_df.columns]
        st.dataframe(trades_df[display_cols], use_container_width=True, height=400)
    else:
        st.warning("No trades generated. Try different parameters or a different symbol.")


def render_gpu_results(symbol, df_sweep, df_sig, timings, date_range):
    """Render GPU sweep results: two heatmaps + top-3 table."""
    ts_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    dr_str = str(date_range) if date_range else "All"
    long_count = int(df_sig["long_a"].sum())
    short_count = int(df_sig["short_a"].sum())

    st.subheader(symbol + " -- GPU Sweep Results")
    st.caption(
        "Date: " + dr_str
        + " | Bars: " + "{:,}".format(len(df_sig))
        + " | Signals: " + str(long_count) + "L / " + str(short_count) + "S"
        + " | Signal: " + "{:.1f}s".format(timings[0])
        + " | Sweep: " + "{:.1f}s".format(timings[1])
        + " | Combos: " + "{:,}".format(len(df_sweep))
        + " | " + ts_str + " UTC"
    )

    sl_vals = sorted(df_sweep["sl_mult"].unique())
    be_vals = sorted(df_sweep["be_trigger_atr"].unique())

    def make_pivot(metric_col):
        """Pivot sweep results for heatmap; return 2d array (be_vals x sl_vals)."""
        pivot = np.full((len(be_vals), len(sl_vals)), np.nan)
        for _, row in df_sweep.iterrows():
            ri = be_vals.index(row["be_trigger_atr"])
            ci = sl_vals.index(row["sl_mult"])
            pivot[ri, ci] = row[metric_col]
        return pivot

    pnl_pivot = make_pivot("net_pnl")
    sharpe_pivot = make_pivot("sharpe")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Net PnL Heatmap")
        fig_pnl = go.Figure(go.Heatmap(
            x=sl_vals, y=be_vals, z=pnl_pivot,
            colorscale="RdYlGn", colorbar=dict(title="Net PnL $"),
            text=[[("$" + "{:.0f}".format(v)) if not np.isnan(v) else "" for v in row]
                  for row in pnl_pivot],
            texttemplate="%{text}",
        ))
        fig_pnl.update_layout(
            template="plotly_dark", height=400,
            paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
            xaxis_title="SL mult (ATR)", yaxis_title="BE trigger (ATR)",
            margin=dict(l=60, r=20, t=30, b=40),
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

    with col2:
        st.subheader("Sharpe Heatmap")
        fig_sharpe = go.Figure(go.Heatmap(
            x=sl_vals, y=be_vals, z=sharpe_pivot,
            colorscale="Viridis", colorbar=dict(title="Sharpe"),
            text=[[("{:.2f}".format(v)) if not np.isnan(v) else "" for v in row]
                  for row in sharpe_pivot],
            texttemplate="%{text}",
        ))
        fig_sharpe.update_layout(
            template="plotly_dark", height=400,
            paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
            xaxis_title="SL mult (ATR)", yaxis_title="BE trigger (ATR)",
            margin=dict(l=60, r=20, t=30, b=40),
        )
        st.plotly_chart(fig_sharpe, use_container_width=True)

    # Top-3 table
    st.subheader("Top 3 Combos by Net PnL")
    top3 = df_sweep.head(3)[["sl_mult", "be_trigger_atr", "total_trades", "win_rate",
                               "net_pnl", "sharpe", "max_dd_pct"]].copy()
    top3["win_rate"] = (top3["win_rate"] * 100).round(1)
    top3 = top3.rename(columns={
        "sl_mult": "SL mult",
        "be_trigger_atr": "BE trigger",
        "total_trades": "Trades",
        "win_rate": "WR%",
        "net_pnl": "Net PnL $",
        "sharpe": "Sharpe",
        "max_dd_pct": "Max DD%",
    })
    st.dataframe(top3, use_container_width=True)


def render_portfolio_results(coin_results, pf_data, initial_equity, date_range):
    """Render portfolio mode results: summary metrics, per-coin table, equity curve."""
    if not coin_results:
        st.warning("No coins returned trades. Try different parameters or a wider date range.")
        return

    n_coins = len(coin_results)
    portfolio_eq = pf_data["portfolio_eq"]
    per_coin_eq = pf_data["per_coin_eq"]
    master_dt = pf_data["master_dt"]
    max_dd_pct = pf_data["portfolio_dd_pct"]
    baseline = pf_data["baseline"]

    net_pnl_total = portfolio_eq[-1] - baseline if len(portfolio_eq) > 0 else 0.0
    total_trades = sum(cr["metrics"].get("total_trades", 0) for cr in coin_results)
    peak_eq = float(np.max(portfolio_eq)) if len(portfolio_eq) > 0 else baseline

    dr_str = str(date_range) if date_range else "All"
    st.caption(
        "Date window: " + dr_str
        + " | Coins with trades: " + str(n_coins)
        + " | All coins use same date filter"
    )

    # Portfolio summary
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Coins", n_coins)
    p2.metric("Net PnL", fmt_dollar(net_pnl_total))
    p3.metric("Max DD", "{:.1f}%".format(max_dd_pct))
    p4.metric("Peak Equity", "$" + "{:,.0f}".format(peak_eq))
    p5.metric("Total Trades", total_trades)

    # Per-coin summary table (v3: added Rebate $ and Volume $ columns)
    st.subheader("Per-Coin Results")
    rows = []
    for cr in coin_results:
        m = cr["metrics"]
        rows.append({
            "Symbol": cr["symbol"],
            "Trades": m.get("total_trades", 0),
            "WR%": round(m.get("win_rate", 0) * 100, 1),
            "Net $": round(m.get("net_pnl", 0), 2),
            "Rebate $": round(m.get("total_rebate", 0), 2),
            "Volume $": int(round(m.get("total_volume", 0), 0)),
            "Sharpe": round(m.get("sharpe", 0), 3),
            "PF": round(m.get("profit_factor", 0), 2),
            "DD%": round(m.get("max_drawdown_pct", 0), 1),
            "Expectancy": round(m.get("expectancy", 0), 2),
            "Commission": round(m.get("total_commission", 0), 2),
        })
    coin_df = pd.DataFrame(rows).sort_values("Net $", ascending=False).reset_index(drop=True)
    st.dataframe(coin_df, use_container_width=True, height=min(400, 35 * (n_coins + 2)))

    # Portfolio equity curve
    st.subheader("Portfolio Equity Curve")
    fig_pf = go.Figure()
    x_axis = master_dt.values if len(master_dt) > 0 else np.arange(len(portfolio_eq))

    for sym, eq_arr in per_coin_eq.items():
        fig_pf.add_trace(go.Scatter(
            x=x_axis, y=eq_arr, mode="lines", name=sym,
            line=dict(width=1), opacity=0.4,
            showlegend=True,
        ))

    fig_pf.add_trace(go.Scatter(
        x=x_axis, y=portfolio_eq, mode="lines", name="Portfolio",
        line=dict(color=COLORS["green"], width=2),
        showlegend=True,
    ))

    fig_pf.update_layout(
        template="plotly_dark", height=500,
        paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
        margin=dict(l=40, r=20, t=30, b=30),
        xaxis_title="", yaxis_title="Equity ($)",
        legend=dict(orientation="v", x=1.01, y=1),
    )
    st.plotly_chart(fig_pf, use_container_width=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Streamlit dashboard entry point for 55/89 EMA Cross Scalp v3."""
    st.set_page_config(page_title="55/89 EMA Cross Scalp v3", layout="wide")

    symbols = load_symbol_list()
    if not symbols:
        st.error("No parquet files found in data/historical/ or data/cache/")
        return

    # ---- Sidebar ----
    st.sidebar.title("55/89 Scalp v3")

    mode = st.sidebar.radio("Mode", ["Single", "Portfolio"], horizontal=True)

    st.sidebar.markdown("---")

    # Symbol / portfolio controls
    if mode == "Single":
        default_idx = symbols.index("BTCUSDT") if "BTCUSDT" in symbols else 0
        symbol = st.sidebar.selectbox("Symbol", symbols, index=default_idx)
    else:
        port_source = st.sidebar.radio("Coin Selection", ["Random N", "Custom"], horizontal=True)
        port_n = st.sidebar.slider("N coins", 2, 30, 10)
        if port_source == "Custom":
            port_custom = st.sidebar.multiselect("Select coins", symbols, default=symbols[:5])
        else:
            port_custom = []
        symbol = symbols[0]

    st.sidebar.markdown("---")

    # Portfolio capital mode (portfolio only)
    if mode == "Portfolio":
        st.sidebar.subheader("Capital Mode")
        cap_mode = st.sidebar.radio(
            "Capital mode",
            ["Shared pool", "Per-coin independent"],
            horizontal=True,
            index=0,
        )
    else:
        cap_mode = "Per-coin independent"

    # Signal parameters
    st.sidebar.subheader("Signal")
    slope_n = st.sidebar.slider("Slope window N", 2, 20, 5)
    slope_m = st.sidebar.slider("Accel window M", 2, 10, 3)

    st.sidebar.markdown("---")

    # Period
    st.sidebar.subheader("Period")
    date_preset = st.sidebar.radio(
        "Period",
        ["All", "7d", "30d", "90d", "Random Week", "Random Month", "Custom"],
        horizontal=False,
        index=0,
    )
    custom_start = None
    custom_end = None
    random_range = st.session_state.get("random_range", None)

    if date_preset == "Custom":
        custom_start = st.sidebar.date_input("From")
        custom_end = st.sidebar.date_input("To")

    elif date_preset in ("Random Week", "Random Month"):
        ref_sym = symbol if mode == "Single" else (symbols[0] if symbols else None)
        window = 7 if date_preset == "Random Week" else 30
        if random_range is None:
            seed = st.session_state.get("reroll_counter", 0) + int(time.time_ns() % 1_000_000)
            random_range = roll_random_range(ref_sym, window, seed=seed)
            st.session_state["random_range"] = random_range
        st.sidebar.caption(
            "Window: " + str(random_range[0]) + " to " + str(random_range[1])
        )
        if st.sidebar.button("Re-roll"):
            counter = st.session_state.get("reroll_counter", 0) + 1
            st.session_state["reroll_counter"] = counter
            seed = counter + int(time.time_ns() % 1_000_000)
            random_range = roll_random_range(ref_sym, window, seed=seed)
            st.session_state["random_range"] = random_range
            for k in ["result_single", "result_portfolio"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    else:
        if "random_range" in st.session_state:
            del st.session_state["random_range"]
        random_range = None

    date_range = resolve_date_range(date_preset, custom_start, custom_end, random_range)
    if date_range:
        st.sidebar.caption("Range: " + str(date_range[0]) + " to " + str(date_range[1]))

    st.sidebar.markdown("---")

    # Capital
    st.sidebar.subheader("Capital")
    cp1, cp2 = st.sidebar.columns(2)
    margin = cp1.number_input("Margin $", value=500.0, step=50.0, min_value=10.0)
    leverage = cp2.number_input("Leverage", value=20, step=1, min_value=1, max_value=125)
    notional = margin * leverage
    st.sidebar.caption("Notional: $" + "{:,.0f}".format(notional))

    if mode == "Portfolio" and cap_mode == "Shared pool":
        total_capital = st.sidebar.number_input(
            "Total portfolio capital ($)", value=10000.0, step=1000.0, min_value=100.0
        )
        # per_coin_equity computed after N is known
        initial_equity = total_capital  # placeholder; replaced below
        pool_mode = True
    else:
        initial_equity = st.sidebar.number_input(
            "Initial equity ($)", value=10000.0, step=1000.0, min_value=100.0
        )
        total_capital = initial_equity
        pool_mode = False

    st.sidebar.markdown("---")

    # Exits
    st.sidebar.subheader("Exits")
    sl_mult = st.sidebar.slider("SL multiplier (ATR x)", 0.5, 5.0, 2.5, 0.1)
    st.sidebar.caption("TP: disabled (strategy uses SL + BE only)")

    be1, be2 = st.sidebar.columns(2)
    be_trigger_atr = be1.slider("BE trigger (ATR x)", 0.0, 3.0, 1.0, 0.1)
    be_lock_atr = be2.slider("BE lock (ATR x)", 0.0, 2.0, 0.0, 0.1)
    if be_trigger_atr > 0:
        st.sidebar.caption(
            "BE: at " + "{:.1f}".format(be_trigger_atr) + "x ATR favorable "
            + "-> SL to entry +/- " + "{:.1f}".format(be_lock_atr) + "x ATR"
        )

    st.sidebar.markdown("---")

    # Commission
    st.sidebar.subheader("Commission")
    rebate_pct = st.sidebar.radio(
        "Rebate %", [0.70, 0.50, 0.0],
        format_func=lambda x: "{:.0%}".format(x),
        horizontal=True,
    )
    cost_side = notional * COMMISSION_RATE
    st.sidebar.caption(
        "Per side: $" + "{:.2f}".format(cost_side)
        + " | RT: $" + "{:.2f}".format(cost_side * 2)
        + " | Net RT: $" + "{:.2f}".format(cost_side * 2 * (1 - rebate_pct))
    )

    st.sidebar.markdown("---")

    # Engine toggle (Single mode only)
    engine_mode = "CPU"
    sl_range_max = 4.0
    be_range_max = 2.0
    if mode == "Single":
        st.sidebar.subheader("Engine")
        if CUDA_AVAILABLE:
            engine_mode = st.sidebar.radio("Engine", ["CPU", "GPU"], horizontal=True)
        else:
            st.sidebar.caption("GPU unavailable -- install numba with CUDA support")
        if engine_mode == "GPU":
            sl_range_max = st.sidebar.slider("SL range max (ATR)", 0.5, 4.0, 4.0, 0.5)
            be_range_max = st.sidebar.slider("BE range max (ATR)", 0.0, 2.0, 2.0, 0.5)
            st.sidebar.caption(
                "Grid: sl_mult 0.5-" + "{:.1f}".format(sl_range_max)
                + " step 0.5, be_trigger 0.0-" + "{:.1f}".format(be_range_max)
                + " step 0.5. TP disabled. Cooldown=1."
            )

    st.sidebar.markdown("---")

    # Action buttons
    if mode == "Single":
        run_btn = st.sidebar.button("Run Backtest", type="primary")
    else:
        run_btn = st.sidebar.button("Run Portfolio Backtest", type="primary")
    reset_btn = st.sidebar.button("Reset")

    if reset_btn:
        for key in ["result_single", "result_portfolio", "port_symbols_locked",
                    "last_params_hash_single", "last_params_hash_portfolio",
                    "random_range", "reroll_counter"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # ---- Param dicts ----
    sig_params = {"slope_n": slope_n, "slope_m": slope_m}
    bt_params = {
        "sl_mult": sl_mult,
        "tp_mult": None,
        "be_trigger_atr": be_trigger_atr,
        "be_lock_atr": be_lock_atr,
        "notional": notional,
        "margin": margin,
        "leverage": leverage,
        "commission_rate": COMMISSION_RATE,
        "maker_rate": 0.0002,
        "rebate_pct": rebate_pct,
        "initial_equity": initial_equity,
        "max_positions": 1,
        "cooldown": 1,
        "enable_adds": False,
        "enable_reentry": False,
        "b_open_fresh": False,
        "max_scaleouts": 0,
        "checkpoint_interval": 5,
        "sigma_floor_atr": 0.5,
    }

    # ---- Title ----
    st.title("55/89 EMA Cross Scalp v3")

    # ====================================================================
    # SINGLE MODE
    # ====================================================================
    if mode == "Single":
        current_hash = compute_params_hash(sig_params, bt_params, date_range, [symbol])

        if run_btn:
            st.session_state["last_params_hash_single"] = current_hash
            with st.spinner("Loading data..."):
                df = load_data(symbol)
                if df is None:
                    st.error("No data found for " + symbol)
                    st.stop()
                df = apply_date_filter(df, date_range)
                if len(df) < 200:
                    st.error("Too few bars after date filter (" + str(len(df)) + "). Widen the range.")
                    st.stop()

            if engine_mode == "GPU":
                if not CUDA_AVAILABLE:
                    st.warning("CUDA not available at runtime. Falling back to CPU.")
                    engine_mode = "CPU"

            if engine_mode == "GPU":
                with st.spinner("Computing signals + GPU sweep..."):
                    df_sweep, df_sig, timings = run_gpu_sweep_55_89(
                        df, sig_params, notional, sl_range_max, be_range_max
                    )
                st.session_state["result_single"] = {
                    "mode": "GPU",
                    "df_sweep": df_sweep,
                    "df_sig": df_sig,
                    "timings": timings,
                    "symbol": symbol,
                    "date_range": date_range,
                }
            else:
                with st.spinner("Computing signals + backtest..."):
                    results, df_sig, timings = run_backtest_55_89(df, sig_params, bt_params)
                st.session_state["result_single"] = {
                    "mode": "CPU",
                    "results": results,
                    "df_sig": df_sig,
                    "timings": timings,
                    "symbol": symbol,
                    "date_range": date_range,
                }

        if "result_single" in st.session_state:
            cached = st.session_state["result_single"]
            if current_hash != st.session_state.get("last_params_hash_single"):
                st.info("Settings changed. Click 'Run Backtest' to update results.")
            if cached.get("mode") == "GPU":
                render_gpu_results(
                    cached["symbol"],
                    cached["df_sweep"],
                    cached["df_sig"],
                    cached["timings"],
                    cached["date_range"],
                )
            else:
                render_single_results(
                    cached["symbol"],
                    cached["results"],
                    cached["df_sig"],
                    cached["timings"],
                    bt_params,
                    cached["date_range"],
                )
                # PDF export (CPU mode only — GPU has no equity curve)
                if REPORTLAB_AVAILABLE:
                    st.markdown("---")
                    if st.button("Export PDF"):
                        with st.spinner("Generating PDF..."):
                            pdf_bytes = generate_pdf_55_89(
                                "Single", cached, bt_params, cached["date_range"]
                            )
                        sym = cached["symbol"]
                        dr = cached["date_range"]
                        date_str = str(dr[0]) if dr else "all"
                        st.download_button(
                            "Download PDF",
                            data=pdf_bytes,
                            file_name="55_89_" + sym + "_" + date_str + ".pdf",
                            mime="application/pdf",
                        )
                else:
                    st.caption("PDF export unavailable -- install reportlab")
        elif not run_btn:
            st.info("Configure parameters in the sidebar, then click 'Run Backtest'.")

    # ====================================================================
    # PORTFOLIO MODE
    # ====================================================================
    else:
        if run_btn:
            # Resolve N for shared pool caption
            if port_source == "Random N":
                counter = st.session_state.get("reroll_counter", 0) + 1
                st.session_state["reroll_counter"] = counter
                seed = counter + int(time.time_ns() % 1_000_000)
                random.seed(seed)
                selected = random.sample(list(symbols), min(port_n, len(symbols)))
            else:
                selected = list(port_custom) if port_custom else symbols[:port_n]
            st.session_state["port_symbols_locked"] = selected

            # Per-coin equity for shared pool
            n_selected = max(len(selected), 1)
            if pool_mode:
                per_coin_equity = total_capital / n_selected
                if pool_mode:
                    st.sidebar.caption(
                        "Each coin gets $" + "{:,.0f}".format(per_coin_equity)
                        + " (total $" + "{:,.0f}".format(total_capital)
                        + " / " + str(n_selected) + " coins)"
                    )
            else:
                per_coin_equity = initial_equity
                st.sidebar.caption(
                    "Each coin runs with full $" + "{:,.0f}".format(per_coin_equity)
                    + " -- total implied capital: $" + "{:,.0f}".format(per_coin_equity * n_selected)
                )

            bt_params_pf = dict(bt_params)
            bt_params_pf["initial_equity"] = per_coin_equity

            current_hash = compute_params_hash(sig_params, bt_params_pf, date_range, selected)
            st.session_state["last_params_hash_portfolio"] = current_hash

            coin_results = []
            skipped = []
            progress = st.progress(0, text="Running portfolio...")
            for idx, sym in enumerate(selected):
                progress.progress((idx + 1) / len(selected), text="Running " + sym + "...")
                df = load_data(sym)
                if df is None:
                    skipped.append(sym + " (no data)")
                    continue
                df = apply_date_filter(df, date_range)
                if len(df) < 200:
                    skipped.append(sym + " (too few bars)")
                    continue
                try:
                    results, df_sig, _ = run_backtest_55_89(df, sig_params, bt_params_pf)
                except Exception as exc:
                    skipped.append(sym + " (error: " + str(exc) + ")")
                    continue
                if results["metrics"].get("total_trades", 0) == 0:
                    skipped.append(sym + " (0 trades)")
                    continue
                if "datetime" in df_sig.columns:
                    dt_idx = pd.DatetimeIndex(pd.to_datetime(df_sig["datetime"], utc=True))
                elif isinstance(df_sig.index, pd.DatetimeIndex):
                    dt_idx = df_sig.index
                    if dt_idx.tzinfo is None:
                        dt_idx = dt_idx.tz_localize("UTC")
                else:
                    dt_idx = pd.date_range("2020-01-01", periods=len(results["equity_curve"]), freq="1min")
                coin_results.append({
                    "symbol": sym,
                    "equity_curve": results["equity_curve"],
                    "datetime_index": dt_idx,
                    "metrics": results["metrics"],
                    "trades_df": results.get("trades_df", pd.DataFrame()),
                })
            progress.empty()

            if skipped:
                st.warning("Skipped " + str(len(skipped)) + " coins: " + ", ".join(skipped))

            if not coin_results:
                st.error("No coins produced trades. Try different params or a wider date range.")
                st.stop()

            pf_data = align_portfolio_equity_55_89(
                coin_results, per_coin_equity,
                pool_mode=pool_mode,
                total_capital=total_capital,
            )
            st.session_state["result_portfolio"] = {
                "coin_results": coin_results,
                "pf_data": pf_data,
                "date_range": date_range,
                "per_coin_equity": per_coin_equity,
                "pool_mode": pool_mode,
                "total_capital": total_capital,
            }

        if "result_portfolio" in st.session_state:
            cached_pf = st.session_state["result_portfolio"]
            locked = st.session_state.get("port_symbols_locked", [])
            if locked:
                current_hash = compute_params_hash(sig_params, bt_params, date_range, locked)
                if current_hash != st.session_state.get("last_params_hash_portfolio"):
                    st.info("Settings changed. Click 'Run Portfolio Backtest' to update results.")
            render_portfolio_results(
                cached_pf["coin_results"],
                cached_pf["pf_data"],
                cached_pf["per_coin_equity"],
                cached_pf["date_range"],
            )
            # PDF export
            if REPORTLAB_AVAILABLE:
                st.markdown("---")
                if st.button("Export PDF"):
                    with st.spinner("Generating PDF..."):
                        pdf_bytes = generate_pdf_55_89(
                            "Portfolio", cached_pf, bt_params, cached_pf["date_range"]
                        )
                    dr = cached_pf["date_range"]
                    date_str = str(dr[0]) if dr else "all"
                    st.download_button(
                        "Download PDF",
                        data=pdf_bytes,
                        file_name="55_89_portfolio_" + date_str + ".pdf",
                        mime="application/pdf",
                    )
            else:
                st.caption("PDF export unavailable -- install reportlab")
        elif not run_btn:
            st.info("Configure parameters in the sidebar, then click 'Run Portfolio Backtest'.")


if __name__ == "__main__":
    main()
'''


def main():
    """Write dashboard_55_89_v3.py and validate syntax."""
    if OUT.exists():
        print("ABORT: " + str(OUT) + " already exists. Remove it first.")
        sys.exit(1)

    print("Writing: " + str(OUT))
    OUT.write_text(DASHBOARD_SOURCE, encoding="utf-8")
    print("  Written: " + str(len(DASHBOARD_SOURCE)) + " chars")

    if not check_file(OUT):
        print("BUILD FAILED")
        sys.exit(1)

    print("")
    if ERRORS:
        print("BUILD FAILED -- errors in: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("BUILD SUCCESS")
        print("Run: streamlit run " + str(OUT))


if __name__ == "__main__":
    main()
