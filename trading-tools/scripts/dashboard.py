"""
Four Pillars Backtest Dashboard — Streamlit GUI
Run: streamlit run scripts/dashboard.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yaml

from data.fetcher import WEEXFetcher
from signals.four_pillars import compute_signals
from engine.backtester import Backtester

# ============================================================================
# CONFIG
# ============================================================================

COLORS = {
    "background": "#0f1419",
    "card_bg": "#1a1f26",
    "text": "#e7e9ea",
    "green": "#10b981",
    "red": "#ef4444",
    "accent": "#3b82f6",
    "orange": "#f59e0b",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"

st.set_page_config(page_title="Four Pillars Backtester", page_icon="4P", layout="wide")

st.markdown(f"""
<style>
    .stApp {{ background-color: {COLORS['background']}; }}
    h1, h2, h3 {{ color: {COLORS['text']}; }}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_config():
    with open(PROJECT_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


@st.cache_data
def get_cached_symbols():
    fetcher = WEEXFetcher(cache_dir=str(CACHE_DIR))
    return fetcher.list_cached()


@st.cache_data
def load_and_compute(symbol: str, params: dict):
    fetcher = WEEXFetcher(cache_dir=str(CACHE_DIR))
    df = fetcher.load_cached(symbol)
    if df is None:
        return None
    return compute_signals(df, params)


def run_backtest(df, bt_params):
    bt = Backtester(bt_params)
    return bt.run(df)


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("Four Pillars Backtester")

config = load_config()
cached = get_cached_symbols()

if not cached:
    st.error("No cached data. Run `python scripts/fetch_data.py` first.")
    st.stop()

symbol = st.sidebar.selectbox("Symbol", cached, index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("Strategy Parameters")

sl_mult = st.sidebar.slider("SL (ATR mult)", 0.3, 4.0, 1.0, 0.1)
tp_mult = st.sidebar.slider("TP (ATR mult)", 0.3, 6.0, 1.5, 0.1)
cooldown = st.sidebar.slider("Cooldown (bars)", 0, 20, 3)
be_raise = st.sidebar.slider("Breakeven Raise ($)", 0, 50, 0, 1)

st.sidebar.markdown("---")
st.sidebar.subheader("Commission")

rebate = st.sidebar.radio("Rebate", [0.70, 0.50, 0.0], format_func=lambda x: f"{x:.0%}")
cost_per_side = st.sidebar.number_input("Cost/side ($)", value=6.0, step=0.5)

st.sidebar.markdown("---")
compare_mode = st.sidebar.checkbox("Compare: no BE raise vs with BE raise")

# ============================================================================
# MAIN
# ============================================================================

st.title(f"4P Backtest — {symbol}")

signal_params = {
    "atr_length": config["strategy"]["atr_length"],
    "cross_level": config["strategy"]["cross_level"],
    "zone_level": config["strategy"]["zone_level"],
    "stage_lookback": config["strategy"]["stage_lookback"],
    "allow_b_trades": config["strategy"]["allow_b_trades"],
    "allow_c_trades": config["strategy"]["allow_c_trades"],
    "b_open_fresh": config["strategy"]["b_open_fresh"],
    "cloud2_reentry": config["strategy"]["cloud2_reentry"],
    "reentry_lookback": config["strategy"]["reentry_lookback"],
}

with st.spinner("Computing signals..."):
    df = load_and_compute(symbol, signal_params)

if df is None:
    st.error(f"No data for {symbol}")
    st.stop()

bt_params = {
    "sl_mult": sl_mult,
    "tp_mult": tp_mult,
    "cooldown": cooldown,
    "b_open_fresh": config["strategy"]["b_open_fresh"],
    "be_raise_amount": float(be_raise),
    "cost_per_side": cost_per_side,
    "rebate_pct": rebate,
    "settlement_hour_utc": 17,
}

with st.spinner("Running backtest..."):
    results = run_backtest(df, bt_params)

m = results["metrics"]

# ── Metrics cards ──
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Trades", m["total_trades"])
col2.metric("Win Rate", f"{m['win_rate']:.0%}")
col3.metric("Expectancy", f"${m['expectancy']:.2f}")
col4.metric("Net P&L", f"${m['net_pnl']:.2f}")
col5.metric("Profit Factor", f"{m['profit_factor']:.2f}")
col6.metric("Max DD", f"${m['max_drawdown']:.0f}")

col7, col8, col9, col10 = st.columns(4)
col7.metric("Commission", f"${m['total_commission']:.0f}")
col8.metric("Losers Saw Green", f"{m['pct_losers_saw_green']:.0%}")
col9.metric("BE Raises", m["be_raised_count"])
col10.metric("Sharpe", f"{m['sharpe']:.2f}")

# ── Equity curve ──
st.subheader("Equity Curve")
eq = results["equity_curve"]
fig_eq = go.Figure()
fig_eq.add_trace(go.Scatter(y=eq, mode="lines", name="Equity",
                             line=dict(color=COLORS["accent"], width=1.5)))
fig_eq.update_layout(
    template="plotly_dark",
    paper_bgcolor=COLORS["background"],
    plot_bgcolor=COLORS["card_bg"],
    height=350,
    margin=dict(l=40, r=20, t=20, b=30),
)
st.plotly_chart(fig_eq, use_container_width=True)

# ── Comparison mode ──
if compare_mode and be_raise > 0:
    st.subheader("Comparison: No BE Raise vs With BE Raise")
    bt_params_no_be = dict(bt_params, be_raise_amount=0.0)
    results_no_be = run_backtest(df, bt_params_no_be)
    m2 = results_no_be["metrics"]

    comp_df = pd.DataFrame({
        "Metric": ["Trades", "Win Rate", "Expectancy", "Net P&L", "Profit Factor",
                    "Max DD", "Losers Saw Green", "BE Raises"],
        f"No BE Raise": [m2["total_trades"], f"{m2['win_rate']:.0%}", f"${m2['expectancy']:.2f}",
                         f"${m2['net_pnl']:.2f}", f"{m2['profit_factor']:.2f}",
                         f"${m2['max_drawdown']:.0f}", f"{m2['pct_losers_saw_green']:.0%}", 0],
        f"BE +${be_raise}": [m["total_trades"], f"{m['win_rate']:.0%}", f"${m['expectancy']:.2f}",
                              f"${m['net_pnl']:.2f}", f"{m['profit_factor']:.2f}",
                              f"${m['max_drawdown']:.0f}", f"{m['pct_losers_saw_green']:.0%}",
                              m["be_raised_count"]],
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    fig_comp = go.Figure()
    fig_comp.add_trace(go.Scatter(y=results_no_be["equity_curve"], mode="lines",
                                   name="No BE Raise", line=dict(color=COLORS["red"], width=1)))
    fig_comp.add_trace(go.Scatter(y=eq, mode="lines",
                                   name=f"BE +${be_raise}", line=dict(color=COLORS["green"], width=1)))
    fig_comp.update_layout(template="plotly_dark", paper_bgcolor=COLORS["background"],
                            plot_bgcolor=COLORS["card_bg"], height=300,
                            margin=dict(l=40, r=20, t=20, b=30))
    st.plotly_chart(fig_comp, use_container_width=True)

# ── MFE/MAE scatter ──
st.subheader("MFE / MAE Scatter")
trades_df = results["trades_df"]
if not trades_df.empty:
    fig_mfe = go.Figure()
    colors = [COLORS["green"] if p > 0 else COLORS["red"] for p in trades_df["net_pnl"]]
    fig_mfe.add_trace(go.Scatter(
        x=trades_df["mae"], y=trades_df["mfe"], mode="markers",
        marker=dict(color=colors, size=5, opacity=0.6),
        text=trades_df.apply(lambda r: f"{r['grade']} {r['direction']} ${r['net_pnl']:.2f}", axis=1),
        hovertemplate="%{text}<br>MAE: $%{x:.2f}<br>MFE: $%{y:.2f}<extra></extra>",
    ))
    fig_mfe.update_layout(
        template="plotly_dark", paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["card_bg"], height=400,
        xaxis_title="MAE ($)", yaxis_title="MFE ($)",
        margin=dict(l=40, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_mfe, use_container_width=True)

# ── Grade breakdown ──
if m.get("grades"):
    st.subheader("Grade Breakdown")
    grade_data = []
    for grade, stats in m["grades"].items():
        grade_data.append({
            "Grade": grade,
            "Trades": stats["count"],
            "Win Rate": f"{stats['win_rate']:.0%}",
            "Avg P&L": f"${stats['avg_pnl']:.2f}",
            "Total P&L": f"${stats['total_pnl']:.2f}",
        })
    st.dataframe(pd.DataFrame(grade_data), use_container_width=True, hide_index=True)

# ── Trade log ──
st.subheader("Trade Log")
if not trades_df.empty:
    st.dataframe(
        trades_df[["direction", "grade", "entry_price", "exit_price", "pnl",
                    "commission", "net_pnl", "mfe", "mae", "exit_reason",
                    "saw_green", "be_raised"]].round(2),
        use_container_width=True, height=400,
    )
