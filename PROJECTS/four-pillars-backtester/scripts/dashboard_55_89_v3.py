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
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from signals.ema_cross_55_89_v2 import compute_signals_55_89
from engine.backtester_55_89 import Backtester5589

try:
    from engine.backtester_5589_jit import Backtester5589Fast as _FastEngine
    _JIT_AVAILABLE = True
except ImportError:
    _FastEngine = None
    _JIT_AVAILABLE = False

def _make_engine(bt_params):
    """Return JIT engine if available, else pure-Python fallback."""
    if _JIT_AVAILABLE:
        return _FastEngine(bt_params)
    return Backtester5589(bt_params)

try:
    from engine.cuda_sweep_5589 import CUDA_AVAILABLE, run_gpu_sweep_5589, build_param_grid_5589
except ImportError:
    CUDA_AVAILABLE = False
    run_gpu_sweep_5589 = None
    build_param_grid_5589 = None

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
# Styled metric cards
# ---------------------------------------------------------------------------

_CARD_CSS_INJECTED = False

def inject_card_css():
    """Inject custom CSS for metric cards once per session."""
    global _CARD_CSS_INJECTED
    if _CARD_CSS_INJECTED:
        return
    css = (
        "<style>"
        ".metric-card {"
        "  background: #1a1f26;"
        "  border: 1px solid #2a3040;"
        "  border-radius: 8px;"
        "  padding: 12px 16px;"
        "  text-align: center;"
        "}"
        ".metric-card .label {"
        "  font-size: 0.75rem;"
        "  color: #8b95a5;"
        "  text-transform: uppercase;"
        "  letter-spacing: 0.5px;"
        "  margin-bottom: 4px;"
        "}"
        ".metric-card .value {"
        "  font-size: 1.4rem;"
        "  font-weight: 700;"
        "  line-height: 1.2;"
        "}"
        ".metric-card .value.green { color: #10b981; }"
        ".metric-card .value.red { color: #ef4444; }"
        ".metric-card .value.blue { color: #3b82f6; }"
        ".metric-card .value.orange { color: #f59e0b; }"
        ".metric-card .value.purple { color: #8b5cf6; }"
        ".metric-card .value.teal { color: #14b8a6; }"
        ".metric-card .value.text { color: #e7e9ea; }"
        ".section-label {"
        "  font-size: 0.65rem;"
        "  color: #5a6270;"
        "  text-transform: uppercase;"
        "  letter-spacing: 1px;"
        "  margin: 16px 0 6px 0;"
        "  padding-bottom: 4px;"
        "  border-bottom: 1px solid #1e2530;"
        "}"
        "</style>"
    )
    st.markdown(css, unsafe_allow_html=True)
    _CARD_CSS_INJECTED = True


def metric_card(label, value, color="text"):
    """Return HTML for a single styled metric card."""
    return (
        '<div class="metric-card">'
        '<div class="label">' + str(label) + '</div>'
        '<div class="value ' + color + '">' + str(value) + '</div>'
        '</div>'
    )


def render_section_label(text):
    """Render a subtle section header above a row of metric cards."""
    st.markdown(
        '<div class="section-label">' + text + '</div>',
        unsafe_allow_html=True,
    )


def compute_capital_metrics(metrics, n_bars, date_range=None, margin_per_pos=500.0):
    """Derive capital usage metrics from engine output.

    Uses avg_positions and max_positions_used (counts) times margin_per_pos
    to compute actual capital deployed. This avoids depending on the engine's
    avg_margin_used/peak_margin_used which may use notional instead of margin.
    """
    total_vol = metrics.get("total_volume", 0.0)
    avg_positions = metrics.get("avg_positions", 0.0)
    max_positions = metrics.get("max_positions_used", 0)
    pct_flat = metrics.get("pct_time_flat", 0.0)
    net_pnl = metrics.get("net_pnl", 0.0)

    avg_margin = avg_positions * margin_per_pos
    peak_margin = max_positions * margin_per_pos

    # Trading days: from date range or bar count (1440 bars = 1 day on 1m)
    if date_range and len(date_range) == 2:
        d0 = date_range[0]
        d1 = date_range[1]
        if hasattr(d0, "date"):
            d0 = d0.date()
        if hasattr(d1, "date"):
            d1 = d1.date()
        trading_days = max(1, (d1 - d0).days)
    else:
        trading_days = max(1, n_bars / 1440)

    daily_vol = total_vol / trading_days
    cap_efficiency = (net_pnl / avg_margin) * 100.0 if avg_margin > 0 else 0.0
    recommended_wallet = peak_margin * 1.5

    return {
        "daily_volume": daily_vol,
        "avg_margin_used": avg_margin,
        "peak_margin_used": peak_margin,
        "pct_time_flat": pct_flat,
        "capital_efficiency": cap_efficiency,
        "recommended_wallet": recommended_wallet,
        "trading_days": trading_days,
    }


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
                df["base_vol"] = df["volume"]  # keep "volume" for engine AVWAP
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
    """Run compute_signals_55_89 then Backtester5589; return (results, df_sig, timings)."""
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    t1 = time.perf_counter()
    bt = _make_engine(bt_params)
    results = bt.run(df_sig)
    t2 = time.perf_counter()
    return results, df_sig, (t1 - t0, t2 - t1)


def run_gpu_sweep_55_89(df, sig_params, notional, sl_range_max, sigma_range_max):
    """Compute signals on CPU then run 5589 GPU sweep; return (df_sweep, df_sig, timings).

    Uses engine/cuda_sweep_5589.py: sl_mult x avwap_sigma grid, 4-phase AVWAP SL.
    Computes ema_72 here (not in signal module) for Cloud4 TP calculation.
    """
    from signals.clouds_v2 import ema as _ema
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    # EMA 72 needed for Cloud4 TP (signal module only has EMA 55/89)
    df_sig = df_sig.copy()
    df_sig["ema_72"] = _ema(df_sig["close"].values, 72)
    t1 = time.perf_counter()
    sl_vals = np.arange(0.5, sl_range_max + 0.1, 0.5)
    sigma_vals = np.arange(1.0, sigma_range_max + 0.1, 0.5)
    param_grid = build_param_grid_5589(
        sl_range=sl_vals,
        sigma_range=sigma_vals,
    )
    df_sweep = run_gpu_sweep_5589(
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
            ["AVWAP sigma", "{:.1f}".format(bt_params.get("avwap_sigma", 2.0))],
            ["AVWAP warmup", str(bt_params.get("avwap_warmup", 5)) + " bars"],
            ["TP ATR offset", "{:.1f}".format(bt_params.get("tp_atr_offset", 0.5)) + "x ATR"],
            ["Ratchet threshold", str(bt_params.get("ratchet_threshold", 2))],
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
    inject_card_css()

    # --- Group A: Performance ---
    render_section_label("Performance")
    net_pnl_val = m.get("net_pnl", 0)
    pnl_color = "green" if net_pnl_val >= 0 else "red"
    wr_val = m.get("win_rate", 0)
    wr_color = "green" if wr_val >= 0.4 else ("orange" if wr_val >= 0.3 else "red")
    pf_val = m.get("profit_factor", 0)
    pf_color = "green" if pf_val >= 1.0 else "red"
    sharpe_val = m.get("sharpe", 0)
    sharpe_color = "green" if sharpe_val > 0 else "red"
    dd_val = m.get("max_drawdown_pct", 0)
    dd_color = "green" if abs(dd_val) < 10 else ("orange" if abs(dd_val) < 25 else "red")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(metric_card("Trades", total_trades, "blue"), unsafe_allow_html=True)
    c2.markdown(metric_card("Win Rate", "{:.1%}".format(wr_val), wr_color), unsafe_allow_html=True)
    c3.markdown(metric_card("Net PnL", fmt_dollar(net_pnl_val), pnl_color), unsafe_allow_html=True)
    c4.markdown(metric_card("Profit Factor", "{:.2f}".format(pf_val), pf_color), unsafe_allow_html=True)
    c5.markdown(metric_card("Sharpe", "{:.3f}".format(sharpe_val), sharpe_color), unsafe_allow_html=True)
    c6.markdown(metric_card("Max DD", "{:.1f}%".format(dd_val), dd_color), unsafe_allow_html=True)

    # --- Group B: Trade Economics ---
    render_section_label("Trade Economics")
    avg_win_val = m.get("avg_win", 0)
    avg_loss_val = m.get("avg_loss", 0)
    exp_val = m.get("expectancy", 0)
    exp_color = "green" if exp_val > 0 else "red"

    c7, c8, c9, c10 = st.columns(4)
    c7.markdown(metric_card("Avg Win", fmt_dollar(avg_win_val), "green"), unsafe_allow_html=True)
    c8.markdown(metric_card("Avg Loss", fmt_dollar(avg_loss_val), "red"), unsafe_allow_html=True)
    c9.markdown(metric_card("Expectancy", fmt_dollar(exp_val), exp_color), unsafe_allow_html=True)
    c10.markdown(metric_card("Commission", "$" + "{:.2f}".format(m.get("total_commission", 0)), "orange"), unsafe_allow_html=True)

    # --- Group C: Volume & Rebates ---
    render_section_label("Volume & Rebates")
    total_volume = m.get("total_volume", 0.0)
    total_rebate = m.get("total_rebate", 0.0)
    net_after_rebate = m.get("net_pnl_after_rebate", m.get("net_pnl", 0))
    nar_color = "green" if net_after_rebate >= 0 else "red"
    lsg_pct = m.get("pct_losers_saw_green", 0.0) * 100.0
    margin_val = float(bt_params.get("margin", bt_params.get("notional", 10000) / bt_params.get("leverage", 20)))
    cap_m = compute_capital_metrics(m, len(df_sig), date_range, margin_per_pos=margin_val)

    c11, c12, c13, c14, c15 = st.columns(5)
    c11.markdown(metric_card("Volume $", fmt_vol(total_volume), "text"), unsafe_allow_html=True)
    c12.markdown(metric_card("Daily Volume", fmt_vol(cap_m["daily_volume"]), "blue"), unsafe_allow_html=True)
    c13.markdown(metric_card("Rebate $", "$" + "{:.2f}".format(total_rebate), "teal"), unsafe_allow_html=True)
    c14.markdown(metric_card("Net w/Rebate", fmt_dollar(net_after_rebate), nar_color), unsafe_allow_html=True)
    c15.markdown(metric_card("LSG%", "{:.1f}%".format(lsg_pct), "orange"), unsafe_allow_html=True)

    # --- Group D: Capital Usage ---
    render_section_label("Capital Usage")
    eff_color = "green" if cap_m["capital_efficiency"] > 0 else "red"
    flat_color = "text" if cap_m["pct_time_flat"] < 0.5 else "orange"

    c16, c17, c18, c19, c20 = st.columns(5)
    c16.markdown(metric_card("Avg Capital", fmt_dollar(cap_m["avg_margin_used"]), "blue"), unsafe_allow_html=True)
    c17.markdown(metric_card("Peak Capital", fmt_dollar(cap_m["peak_margin_used"]), "purple"), unsafe_allow_html=True)
    c18.markdown(metric_card("% Time Flat", "{:.1f}%".format(cap_m["pct_time_flat"] * 100.0), flat_color), unsafe_allow_html=True)
    c19.markdown(metric_card("Capital ROI", "{:.2f}%".format(cap_m["capital_efficiency"]), eff_color), unsafe_allow_html=True)
    c20.markdown(metric_card("Rec. Wallet", fmt_dollar(cap_m["recommended_wallet"]), "teal"), unsafe_allow_html=True)

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
            "direction", "trade_grade", "entry_price", "exit_price", "pnl", "commission",
            "net_pnl", "mfe", "mae", "exit_reason", "saw_green", "ema_be_triggered",
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
    sigma_vals = sorted(df_sweep["avwap_sigma"].unique())

    def make_pivot(metric_col):
        """Pivot sweep results for heatmap; return 2d array (sigma_vals x sl_vals)."""
        pivot = np.full((len(sigma_vals), len(sl_vals)), np.nan)
        for _, row in df_sweep.iterrows():
            ri = sigma_vals.index(row["avwap_sigma"])
            ci = sl_vals.index(row["sl_mult"])
            pivot[ri, ci] = row[metric_col]
        return pivot

    pnl_pivot = make_pivot("net_pnl")
    sharpe_pivot = make_pivot("sharpe")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Net PnL Heatmap")
        fig_pnl = go.Figure(go.Heatmap(
            x=sl_vals, y=sigma_vals, z=pnl_pivot,
            colorscale="RdYlGn", colorbar=dict(title="Net PnL $"),
            text=[[("$" + "{:.0f}".format(v)) if not np.isnan(v) else "" for v in row]
                  for row in pnl_pivot],
            texttemplate="%{text}",
        ))
        fig_pnl.update_layout(
            template="plotly_dark", height=400,
            paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
            xaxis_title="SL mult (ATR)", yaxis_title="AVWAP sigma",
            margin=dict(l=60, r=20, t=30, b=40),
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

    with col2:
        st.subheader("Sharpe Heatmap")
        fig_sharpe = go.Figure(go.Heatmap(
            x=sl_vals, y=sigma_vals, z=sharpe_pivot,
            colorscale="Viridis", colorbar=dict(title="Sharpe"),
            text=[[("{:.2f}".format(v)) if not np.isnan(v) else "" for v in row]
                  for row in sharpe_pivot],
            texttemplate="%{text}",
        ))
        fig_sharpe.update_layout(
            template="plotly_dark", height=400,
            paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
            xaxis_title="SL mult (ATR)", yaxis_title="AVWAP sigma",
            margin=dict(l=60, r=20, t=30, b=40),
        )
        st.plotly_chart(fig_sharpe, use_container_width=True)

    # Top-3 table
    st.subheader("Top 3 Combos by Net PnL")
    top3 = df_sweep.head(3)[["sl_mult", "avwap_sigma", "total_trades", "win_rate",
                               "net_pnl", "sharpe", "max_dd_pct"]].copy()
    top3["win_rate"] = (top3["win_rate"] * 100).round(1)
    top3 = top3.rename(columns={
        "sl_mult": "SL mult",
        "avwap_sigma": "AVWAP sigma",
        "total_trades": "Trades",
        "win_rate": "WR%",
        "net_pnl": "Net PnL $",
        "sharpe": "Sharpe",
        "max_dd_pct": "Max DD%",
    })
    st.dataframe(top3, use_container_width=True)


def render_portfolio_results(coin_results, pf_data, initial_equity, date_range, margin_per_pos=500.0):
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

    # Portfolio summary -- aggregate metrics across all coins (uniform with single mode)
    total_vol = sum(cr["metrics"].get("total_volume", 0.0) for cr in coin_results)
    total_rebate_pf = sum(cr["metrics"].get("total_rebate", 0.0) for cr in coin_results)
    total_commission_pf = sum(cr["metrics"].get("total_commission", 0.0) for cr in coin_results)
    total_be_raises = sum(cr["metrics"].get("be_raised_count", 0) for cr in coin_results)

    # Aggregate win/loss stats
    all_wins = []
    all_losses = []
    for cr in coin_results:
        m = cr["metrics"]
        wc = m.get("win_count", 0)
        lc = m.get("loss_count", 0)
        if wc > 0 and m.get("avg_win", 0) != 0:
            all_wins.extend([m["avg_win"]] * wc)
        if lc > 0 and m.get("avg_loss", 0) != 0:
            all_losses.extend([m["avg_loss"]] * lc)
    pf_win_rate = len(all_wins) / total_trades if total_trades > 0 else 0.0
    pf_avg_win = float(np.mean(all_wins)) if all_wins else 0.0
    pf_avg_loss = float(np.mean(all_losses)) if all_losses else 0.0
    pf_expectancy = (pf_win_rate * pf_avg_win + (1 - pf_win_rate) * pf_avg_loss) if total_trades > 0 else 0.0
    pf_gross_profit = sum(cr["metrics"].get("gross_profit", 0.0) for cr in coin_results)
    pf_gross_loss = sum(cr["metrics"].get("gross_loss", 0.0) for cr in coin_results)
    pf_profit_factor = pf_gross_profit / pf_gross_loss if pf_gross_loss > 0 else 0.0
    net_after_rebate_pf = net_pnl_total + total_rebate_pf

    # Aggregate LSG
    total_lsg_losers = sum(cr["metrics"].get("saw_green_losers", 0) for cr in coin_results)
    total_losers = sum(cr["metrics"].get("total_losers", 0) for cr in coin_results)
    pf_lsg_pct = (total_lsg_losers / total_losers * 100.0) if total_losers > 0 else 0.0

    # Weighted sharpe (by trade count)
    sharpe_num = sum(cr["metrics"].get("sharpe", 0) * cr["metrics"].get("total_trades", 0) for cr in coin_results)
    pf_sharpe = sharpe_num / total_trades if total_trades > 0 else 0.0

    inject_card_css()

    # Aggregate capital metrics across coins (use position counts * margin)
    pf_avg_positions = sum(cr["metrics"].get("avg_positions", 0.0) for cr in coin_results)
    pf_max_positions = sum(cr["metrics"].get("max_positions_used", 0) for cr in coin_results)
    pf_pct_flat = float(np.mean([cr["metrics"].get("pct_time_flat", 0.0) for cr in coin_results]))
    pf_capital_m = {
        "total_volume": total_vol,
        "avg_positions": pf_avg_positions,
        "max_positions_used": pf_max_positions,
        "pct_time_flat": pf_pct_flat,
        "net_pnl": net_pnl_total,
    }
    n_bars_pf = len(master_dt) if len(master_dt) > 0 else 1440
    cap_m = compute_capital_metrics(pf_capital_m, n_bars_pf, date_range, margin_per_pos=margin_per_pos)

    # --- Group A: Performance ---
    render_section_label("Performance")
    pnl_color = "green" if net_pnl_total >= 0 else "red"
    wr_color = "green" if pf_win_rate >= 0.4 else ("orange" if pf_win_rate >= 0.3 else "red")
    pf_color = "green" if pf_profit_factor >= 1.0 else "red"
    sh_color = "green" if pf_sharpe > 0 else "red"
    dd_color = "green" if abs(max_dd_pct) < 10 else ("orange" if abs(max_dd_pct) < 25 else "red")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(metric_card("Trades", total_trades, "blue"), unsafe_allow_html=True)
    c2.markdown(metric_card("Win Rate", "{:.1%}".format(pf_win_rate), wr_color), unsafe_allow_html=True)
    c3.markdown(metric_card("Net PnL", fmt_dollar(net_pnl_total), pnl_color), unsafe_allow_html=True)
    c4.markdown(metric_card("Profit Factor", "{:.2f}".format(pf_profit_factor), pf_color), unsafe_allow_html=True)
    c5.markdown(metric_card("Sharpe", "{:.3f}".format(pf_sharpe), sh_color), unsafe_allow_html=True)
    c6.markdown(metric_card("Max DD", "{:.1f}%".format(max_dd_pct), dd_color), unsafe_allow_html=True)

    # --- Group B: Trade Economics ---
    render_section_label("Trade Economics")
    exp_color = "green" if pf_expectancy > 0 else "red"

    c7, c8, c9, c10 = st.columns(4)
    c7.markdown(metric_card("Avg Win", fmt_dollar(pf_avg_win), "green"), unsafe_allow_html=True)
    c8.markdown(metric_card("Avg Loss", fmt_dollar(pf_avg_loss), "red"), unsafe_allow_html=True)
    c9.markdown(metric_card("Expectancy", fmt_dollar(pf_expectancy), exp_color), unsafe_allow_html=True)
    c10.markdown(metric_card("Commission", "$" + "{:.2f}".format(total_commission_pf), "orange"), unsafe_allow_html=True)

    # --- Group C: Volume & Rebates ---
    render_section_label("Volume & Rebates")
    nar_color = "green" if net_after_rebate_pf >= 0 else "red"

    c11, c12, c13, c14, c15 = st.columns(5)
    c11.markdown(metric_card("Volume $", fmt_vol(total_vol), "text"), unsafe_allow_html=True)
    c12.markdown(metric_card("Daily Volume", fmt_vol(cap_m["daily_volume"]), "blue"), unsafe_allow_html=True)
    c13.markdown(metric_card("Rebate $", "$" + "{:.2f}".format(total_rebate_pf), "teal"), unsafe_allow_html=True)
    c14.markdown(metric_card("Net w/Rebate", fmt_dollar(net_after_rebate_pf), nar_color), unsafe_allow_html=True)
    c15.markdown(metric_card("LSG%", "{:.1f}%".format(pf_lsg_pct), "orange"), unsafe_allow_html=True)

    # --- Group D: Capital Usage ---
    render_section_label("Capital Usage")
    eff_color = "green" if cap_m["capital_efficiency"] > 0 else "red"
    flat_color = "text" if cap_m["pct_time_flat"] < 0.5 else "orange"

    c16, c17, c18, c19, c20 = st.columns(5)
    c16.markdown(metric_card("Avg Capital", fmt_dollar(cap_m["avg_margin_used"]), "blue"), unsafe_allow_html=True)
    c17.markdown(metric_card("Peak Capital", fmt_dollar(cap_m["peak_margin_used"]), "purple"), unsafe_allow_html=True)
    c18.markdown(metric_card("% Time Flat", "{:.1f}%".format(cap_m["pct_time_flat"] * 100.0), flat_color), unsafe_allow_html=True)
    c19.markdown(metric_card("Capital ROI", "{:.2f}%".format(cap_m["capital_efficiency"]), eff_color), unsafe_allow_html=True)
    c20.markdown(metric_card("Rec. Wallet", fmt_dollar(cap_m["recommended_wallet"]), "teal"), unsafe_allow_html=True)

    # --- Row 5: Portfolio-specific ---
    render_section_label("Portfolio")
    p1, p2, p3 = st.columns(3)
    p1.markdown(metric_card("Coins", n_coins, "blue"), unsafe_allow_html=True)
    p2.markdown(metric_card("Peak Equity", "$" + "{:,.0f}".format(peak_eq), "green"), unsafe_allow_html=True)
    p3.markdown(metric_card("Total Rebate", "$" + "{:.2f}".format(total_rebate_pf), "teal"), unsafe_allow_html=True)

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
        port_n = st.sidebar.slider("N coins", 2, 50, 10)
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
    sl_mult = st.sidebar.slider("SL multiplier (ATR x)", 0.5, 8.0, 4.0, 0.1)
    avwap_sigma = st.sidebar.slider("AVWAP sigma", 1.0, 3.0, 2.0, 0.1)
    avwap_warmup = st.sidebar.slider("AVWAP warmup (bars)", 3, 50, 20, 1)
    tp_atr_offset = st.sidebar.slider("TP ATR offset", 0.0, 2.0, 0.5, 0.1)
    ratchet_threshold = st.sidebar.slider("Ratchet threshold", 1, 4, 2, 1)
    st.sidebar.caption(
        "Phase 1: ATR SL (bars 0-" + str(avwap_warmup - 1) + ") | "
        + "Phase 2: AVWAP " + "{:.1f}".format(avwap_sigma) + "sig | "
        + "Phase 4 TP after " + str(ratchet_threshold) + " ratchets"
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
            be_range_max = st.sidebar.slider("AVWAP sigma range max", 1.0, 4.0, 3.0, 0.5)
            st.sidebar.caption(
                "GPU sweep (5589 engine). Grid: sl_mult 0.5-" + "{:.1f}".format(sl_range_max)
                + " x avwap_sigma 1.0-" + "{:.1f}".format(be_range_max)
                + ", step 0.5. 4-phase AVWAP SL."
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
    min_signal_gap = st.sidebar.slider("Min signal gap (bars)", 1, 500, 50, 10)
    overzone_long_th = st.sidebar.slider("Overzone long threshold", 5.0, 40.0, 20.0, 1.0)
    overzone_short_th = st.sidebar.slider("Overzone short threshold", 60.0, 95.0, 80.0, 1.0)
    sig_params = {"slope_n": slope_n, "slope_m": slope_m, "min_signal_gap": min_signal_gap, "overzone_long_threshold": overzone_long_th, "overzone_short_threshold": overzone_short_th}
    bt_params = {
        "sl_mult": sl_mult,
        "avwap_sigma": avwap_sigma,
        "avwap_warmup": avwap_warmup,
        "tp_atr_offset": tp_atr_offset,
        "ratchet_threshold": ratchet_threshold,
        "notional": notional,
        "margin": margin,
        "leverage": leverage,
        "commission_rate": COMMISSION_RATE,
        "maker_rate": 0.0002,
        "rebate_pct": rebate_pct,
        "initial_equity": initial_equity,
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
            n_sel = len(selected)

            def _run_coin(sym):
                """Load, filter, and backtest one coin; return (sym, result_dict, skip_reason)."""
                df = load_data(sym)
                if df is None:
                    return sym, None, "no data"
                df = apply_date_filter(df, date_range)
                if len(df) < 200:
                    return sym, None, "too few bars"
                try:
                    results, df_sig, _ = run_backtest_55_89(df, sig_params, bt_params_pf)
                except Exception as exc:
                    return sym, None, "error: " + str(exc)[:80]
                if results["metrics"].get("total_trades", 0) == 0:
                    return sym, None, "0 trades"
                if "datetime" in df_sig.columns:
                    dt_idx = pd.DatetimeIndex(pd.to_datetime(df_sig["datetime"], utc=True))
                elif isinstance(df_sig.index, pd.DatetimeIndex):
                    dt_idx = df_sig.index
                    if dt_idx.tzinfo is None:
                        dt_idx = dt_idx.tz_localize("UTC")
                else:
                    dt_idx = pd.date_range("2020-01-01", periods=len(results["equity_curve"]), freq="1min")
                return sym, {
                    "symbol": sym,
                    "equity_curve": results["equity_curve"],
                    "datetime_index": dt_idx,
                    "metrics": results["metrics"],
                    "trades_df": results.get("trades_df", pd.DataFrame()),
                }, None

            workers = min(8, n_sel)
            progress = st.progress(0, text="Running portfolio (" + str(n_sel) + " coins, "
                                   + str(workers) + " threads)...")
            done = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(_run_coin, sym): sym for sym in selected}
                for future in as_completed(futures):
                    sym, result, reason = future.result()
                    done += 1
                    progress.progress(done / n_sel,
                                      text=sym + " done (" + str(done) + "/" + str(n_sel) + ")")
                    if result is None:
                        skipped.append(sym + " (" + reason + ")")
                    else:
                        coin_results.append(result)
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
                margin_per_pos=float(bt_params.get("margin", bt_params.get("notional", 10000) / bt_params.get("leverage", 20))),
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
