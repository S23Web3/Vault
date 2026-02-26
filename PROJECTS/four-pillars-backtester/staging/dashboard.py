r"""
Four Pillars Backtest Dashboard -- Streamlit GUI
5-tab layout with ML integration.

Run: streamlit run scripts/dashboard.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from data.fetcher import BybitFetcher
from signals.four_pillars import compute_signals
from engine.backtester import Backtester

COLORS = {
    "bg": "#0f1419", "card": "#1a1f26", "text": "#e7e9ea",
    "green": "#10b981", "red": "#ef4444", "blue": "#3b82f6",
    "orange": "#f59e0b", "purple": "#8b5cf6", "gray": "#6b7280",
}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
PARAM_LOG = PROJECT_ROOT / "data" / "output" / "param_log.jsonl"

st.set_page_config(page_title="Four Pillars Backtester", layout="wide")
st.markdown(f"""<style>
    .stApp {{ background-color: {COLORS['bg']}; }}
    h1, h2, h3 {{ color: {COLORS['text']}; }}
</style>""", unsafe_allow_html=True)


@st.cache_data
def get_cached_symbols():
    return sorted(BybitFetcher(cache_dir=str(CACHE_DIR)).list_cached())


def resample_5m(df_1m):
    df = df_1m.copy()
    if 'datetime' not in df.columns:
        if df.index.name == 'datetime':
            df = df.reset_index()
    df = df.set_index('datetime')
    ohlcv = df.resample('5min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
        'base_vol': 'sum', 'quote_vol': 'sum', 'timestamp': 'first'
    }).dropna()
    return ohlcv.reset_index()


def load_data(symbol, timeframe):
    df = BybitFetcher(cache_dir=str(CACHE_DIR)).load_cached(symbol)
    if df is None:
        return None
    if timeframe == '5m':
        df = resample_5m(df)
    return df


def log_params(symbol, timeframe, signal_params, bt_params, metrics):
    PARAM_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol, "timeframe": timeframe,
        "signal": signal_params, "backtest": bt_params,
        "result": {
            "trades": metrics.get("total_trades", 0),
            "win_rate": metrics.get("win_rate", 0),
            "net_pnl": float(metrics.get("net_pnl", 0)),
            "expectancy": float(metrics.get("expectancy", 0)),
            "sharpe": float(metrics.get("sharpe", 0)),
            "max_dd_pct": float(metrics.get("max_drawdown_pct", 0)),
            "pct_lsg": float(metrics.get("pct_losers_saw_green", 0)),
            "be_raised": metrics.get("be_raised_count", 0),
            "profit_factor": float(metrics.get("profit_factor", 0)),
        }
    }
    with open(PARAM_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("Four Pillars v3.8")
cached = get_cached_symbols()
if not cached:
    st.error("No cached data.")
    st.stop()

# -- Data --
st.sidebar.subheader("Data")
symbol = st.sidebar.selectbox("Symbol", cached,
    index=cached.index("RIVERUSDT") if "RIVERUSDT" in cached else 0)
timeframe = st.sidebar.radio("Timeframe", ["1m", "5m"], index=1, horizontal=True)

# -- Stochastics --
st.sidebar.markdown("---")
st.sidebar.subheader("Stochastics (K lengths)")
sk1, sk2 = st.sidebar.columns(2)
stoch_k1 = sk1.number_input("K1 (entry)", value=9, min_value=3, max_value=100)
stoch_k2 = sk2.number_input("K2 (confirm)", value=14, min_value=3, max_value=100)
sk3, sk4 = st.sidebar.columns(2)
stoch_k3 = sk3.number_input("K3 (diverge)", value=40, min_value=3, max_value=200)
stoch_k4 = sk4.number_input("K4 (macro)", value=60, min_value=3, max_value=200)
stoch_d_smooth = st.sidebar.number_input("D smooth (SMA of K4)", value=10, min_value=1, max_value=50)

# -- Ripster Clouds --
st.sidebar.markdown("---")
st.sidebar.subheader("Ripster Clouds (EMA lengths)")
cc1, cc2 = st.sidebar.columns(2)
cloud2_fast = cc1.number_input("Cloud2 fast", value=5, min_value=2, max_value=50)
cloud2_slow = cc2.number_input("Cloud2 slow", value=12, min_value=2, max_value=100)
cc3, cc4 = st.sidebar.columns(2)
cloud3_fast = cc3.number_input("Cloud3 fast", value=34, min_value=5, max_value=200)
cloud3_slow = cc4.number_input("Cloud3 slow", value=50, min_value=5, max_value=200)
cc5, cc6 = st.sidebar.columns(2)
cloud4_fast = cc5.number_input("Cloud4 fast", value=72, min_value=10, max_value=300)
cloud4_slow = cc6.number_input("Cloud4 slow", value=89, min_value=10, max_value=300)

# -- Signal Logic --
st.sidebar.markdown("---")
st.sidebar.subheader("Signal Logic")
c1, c2 = st.sidebar.columns(2)
cross_level = c1.number_input("Cross Level", value=25, min_value=5, max_value=50, step=5)
zone_level = c2.number_input("Zone Level", value=30, min_value=5, max_value=50, step=5)
c3, c4 = st.sidebar.columns(2)
stage_lookback = c3.number_input("Stage LB", value=10, min_value=1, max_value=50)
reentry_lookback = c4.number_input("Re-entry LB", value=10, min_value=1, max_value=50)
atr_length = st.sidebar.number_input("ATR Length", value=14, min_value=5, max_value=50)
c5, c6 = st.sidebar.columns(2)
allow_b = c5.checkbox("B trades", value=True)
allow_c = c6.checkbox("C trades", value=True)
c7, c8 = st.sidebar.columns(2)
b_open_fresh = c7.checkbox("B/C fresh", value=True)
cloud2_reentry = c8.checkbox("Cloud2 re-entry", value=True)

# -- Exits --
st.sidebar.markdown("---")
st.sidebar.subheader("Exits")
cb1, cb2 = st.sidebar.columns(2)
sl_mult = cb1.slider("SL (ATR x)", 0.3, 4.0, 1.0, 0.1)
tp_mult = cb2.slider("TP (ATR x)", 0.3, 6.0, 1.5, 0.1)
use_tp = st.sidebar.checkbox("Use TP", value=True)
cooldown = st.sidebar.slider("Cooldown (bars)", 0, 20, 3)

# -- AVWAP Trailing Stop --
st.sidebar.markdown("---")
st.sidebar.subheader("AVWAP Trail")
avwap_enabled = st.sidebar.checkbox("Enable AVWAP trail", value=False)
avwap_band = 1
avwap_floor_atr = 1.0
if avwap_enabled:
    avwap_band = st.sidebar.radio("Stdev band for SL", [1, 2, 3],
        format_func=lambda x: f"+/- {x} sigma", horizontal=True)
    avwap_floor_atr = st.sidebar.slider("Floor (ATR x)", 0.3, 3.0, 1.0, 0.1)
    st.sidebar.caption("AVWAP anchors at entry. SL = AVWAP +/- N*stdev. Ratchets favorable only.")

# -- Breakeven --
st.sidebar.markdown("---")
st.sidebar.subheader("Breakeven")
be_raise_amount = 0.0
be_trigger_atr = 0.0
be_lock_atr = 0.0
if avwap_enabled:
    st.sidebar.caption("BE disabled -- AVWAP trail handles SL movement")
    be_mode = "Off"
else:
    be_mode = st.sidebar.radio("BE Mode", ["Fixed $", "ATR-based", "Off"], horizontal=True)
    if be_mode == "Fixed $":
        be_raise_amount = st.sidebar.slider("BE $ trigger", 0, 50, 2, 1)
    elif be_mode == "ATR-based":
        cbe1, cbe2 = st.sidebar.columns(2)
        be_trigger_atr = cbe1.slider("Trigger ATR x", 0.1, 2.0, 0.5, 0.1)
        be_lock_atr = cbe2.slider("Lock ATR x", 0.0, 1.5, 0.3, 0.1)

# -- Position --
st.sidebar.markdown("---")
st.sidebar.subheader("Position")
cp1, cp2 = st.sidebar.columns(2)
margin = cp1.number_input("Margin $", value=500.0, step=50.0)
leverage = cp2.number_input("Leverage", value=20, step=1, min_value=1, max_value=125)
notional = margin * leverage
st.sidebar.caption(f"Notional: ${notional:,.0f}")

# -- Commission --
st.sidebar.markdown("---")
st.sidebar.subheader("Commission")
comm_pct = st.sidebar.number_input("Rate %", value=0.08, step=0.01, format="%.2f")
commission_rate = comm_pct / 100.0
cost_side = notional * commission_rate
st.sidebar.caption(f"Per side: ${cost_side:,.2f} | RT: ${cost_side*2:,.2f}")
rebate_pct = st.sidebar.radio("Rebate", [0.70, 0.50, 0.0],
    format_func=lambda x: f"{x:.0%}", horizontal=True)
st.sidebar.caption(f"Net RT: ${cost_side*2*(1-rebate_pct):,.2f}")

# -- ML Parameters --
st.sidebar.markdown("---")
st.sidebar.subheader("ML Meta-Label")
xgb_estimators = st.sidebar.number_input("XGB Estimators", value=200, step=50, min_value=50, max_value=1000)
xgb_depth = st.sidebar.slider("XGB Depth", 2, 10, 4)
ml_threshold = st.sidebar.slider("ML Threshold", 0.0, 1.0, 0.5, 0.05)

# -- Actions --
st.sidebar.markdown("---")
run_test = st.sidebar.button("Test Run (1 coin)")
run_batch = st.sidebar.button("Sweep ALL coins")
batch_top = st.sidebar.slider("Top N", 5, 50, 20)

# ============================================================================
# PARAM DICTS
# ============================================================================

signal_params = {
    "atr_length": atr_length, "cross_level": cross_level,
    "zone_level": zone_level, "stage_lookback": stage_lookback,
    "allow_b_trades": allow_b, "allow_c_trades": allow_c,
    "b_open_fresh": b_open_fresh, "cloud2_reentry": cloud2_reentry,
    "reentry_lookback": reentry_lookback,
    "stoch_k1": stoch_k1, "stoch_k2": stoch_k2,
    "stoch_k3": stoch_k3, "stoch_k4": stoch_k4,
    "stoch_d_smooth": stoch_d_smooth,
    "cloud2_fast": cloud2_fast, "cloud2_slow": cloud2_slow,
    "cloud3_fast": cloud3_fast, "cloud3_slow": cloud3_slow,
    "cloud4_fast": cloud4_fast, "cloud4_slow": cloud4_slow,
}

bt_params = {
    "sl_mult": sl_mult, "tp_mult": tp_mult, "use_tp": use_tp,
    "cooldown": cooldown, "b_open_fresh": b_open_fresh,
    "notional": notional, "commission_rate": commission_rate,
    "rebate_pct": rebate_pct, "initial_equity": 10000.0,
    "be_raise_amount": float(be_raise_amount),
    "be_trigger_atr": be_trigger_atr, "be_lock_atr": be_lock_atr,
    "avwap_enabled": avwap_enabled, "avwap_band": avwap_band,
    "avwap_floor_atr": avwap_floor_atr,
}

# ============================================================================
# TEST RUN (1 coin, quick output check)
# ============================================================================

if run_test:
    st.title(f"TEST -- {symbol} {timeframe}")
    t0 = time.time()
    df = load_data(symbol, timeframe)
    if df is None:
        st.error(f"No data for {symbol}")
        st.stop()

    st.text(f"Loaded {len(df):,} bars")
    df_sig = compute_signals(df.copy(), signal_params)
    st.text(f"Signals computed")
    bt = Backtester(bt_params)
    results = bt.run(df_sig)
    m = results["metrics"]
    elapsed = time.time() - t0

    if m["total_trades"] == 0:
        st.warning("0 trades.")
        st.stop()

    eq = results["equity_curve"]
    true_net = eq[-1] - 10000.0
    exp = true_net / m["total_trades"]

    st.success(f"Done in {elapsed:.1f}s")
    st.text(
        f"Trades: {m['total_trades']}  |  WR: {m['win_rate']:.1%}  |  "
        f"Exp: ${exp:.2f}  |  Net: ${true_net:,.2f}  |  "
        f"PF: {m['profit_factor']:.2f}  |  DD: {m['max_drawdown_pct']:.1f}%  |  "
        f"LSG: {m['pct_losers_saw_green']:.0%}  |  BE: {m['be_raised_count']}"
    )
    if avwap_enabled:
        st.text(f"AVWAP: band={avwap_band}sigma  floor={avwap_floor_atr}xATR")

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=eq, mode="lines", line=dict(color=COLORS["blue"], width=1.5)))
    fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["card"], height=250, margin=dict(l=30, r=10, t=10, b=20))
    st.plotly_chart(fig, use_container_width=True)

    tdf = results["trades_df"]
    if not tdf.empty:
        show_cols = ["direction", "grade", "entry_price", "exit_price", "net_pnl",
                     "mfe", "mae", "exit_reason", "be_raised"]
        st.text("First 5 trades:")
        st.dataframe(tdf[show_cols].head(5).round(4), use_container_width=True, hide_index=True)
        st.text("Last 5 trades:")
        st.dataframe(tdf[show_cols].tail(5).round(4), use_container_width=True, hide_index=True)

    log_params(symbol, timeframe, signal_params, bt_params, m)

# ============================================================================
# SINGLE BACKTEST (5-tab view)
# ============================================================================

elif not run_batch:
    st.title(f"4P -- {symbol} {timeframe}")

    df = load_data(symbol, timeframe)
    if df is None:
        st.error(f"No data for {symbol}")
        st.stop()

    df_sig = compute_signals(df.copy(), signal_params)
    bt = Backtester(bt_params)
    results = bt.run(df_sig)
    m = results["metrics"]
    trades_df = results["trades_df"]
    eq = results["equity_curve"]

    if m["total_trades"] == 0:
        st.warning("0 trades.")
        st.stop()

    true_net = eq[-1] - 10000.0
    exp = true_net / m["total_trades"]
    log_params(symbol, timeframe, signal_params, bt_params, m)

    # ── 5 TABS ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Trade Analysis", "MFE/MAE & Losers", "ML Meta-Label", "Validation"
    ])

    # ── TAB 1: OVERVIEW ────────────────────────────────────────────────────
    with tab1:
        r1 = st.columns(6)
        r1[0].metric("Trades", f"{m['total_trades']:,}")
        r1[1].metric("Win Rate", f"{m['win_rate']:.1%}")
        r1[2].metric("Exp $/tr", f"${exp:.2f}")
        r1[3].metric("Net P&L", f"${true_net:,.2f}")
        r1[4].metric("PF", f"{m['profit_factor']:.2f}")
        r1[5].metric("Max DD%", f"{m['max_drawdown_pct']:.1f}%")

        r2 = st.columns(6)
        r2[0].metric("Comm $", f"${m['total_commission']:,.0f}")
        r2[1].metric("LSG", f"{m['pct_losers_saw_green']:.0%}")
        r2[2].metric("BE Raises", f"{m['be_raised_count']:,}")
        r2[3].metric("Sharpe", f"{m['sharpe']:.3f}")
        r2[4].metric("Sortino", f"{m['sortino']:.3f}")
        r2[5].metric("Avg MFE", f"${m['avg_mfe']:.2f}")

        if avwap_enabled:
            st.caption(f"AVWAP trail ON: {avwap_band}-sigma band, floor {avwap_floor_atr}x ATR")

        # Equity curve
        st.subheader("Equity Curve")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(y=eq, mode="lines", name="Equity",
                                     line=dict(color=COLORS["blue"], width=1.5)))
        fig_eq.add_trace(go.Scatter(y=np.maximum.accumulate(eq), mode="lines", name="Peak",
                                     line=dict(color=COLORS["gray"], width=0.8, dash="dot")))
        fig_eq.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                              plot_bgcolor=COLORS["card"], height=350,
                              margin=dict(l=40, r=20, t=20, b=30))
        st.plotly_chart(fig_eq, use_container_width=True)

        # Grade breakdown
        if m.get("grades"):
            st.subheader("Grades")
            gd = []
            for g in ["A", "B", "C", "R"]:
                if g in m["grades"]:
                    s = m["grades"][g]
                    gd.append({"Grade": g, "Trades": s["count"], "WR": f"{s['win_rate']:.1%}",
                                "Avg": f"${s['avg_pnl']:.2f}", "Total": f"${s['total_pnl']:.2f}"})
            st.dataframe(pd.DataFrame(gd), use_container_width=True, hide_index=True)

        # Exit reasons
        if not trades_df.empty:
            st.subheader("Exits")
            st.dataframe(trades_df.groupby("exit_reason").agg(
                N=("net_pnl", "count"), Avg=("net_pnl", "mean"), Sum=("net_pnl", "sum")
            ).round(2), use_container_width=True)

        # BE comparison
        if not avwap_enabled and be_mode != "Off":
            st.subheader("BE Impact")
            bt2 = Backtester(dict(bt_params, be_raise_amount=0.0, be_trigger_atr=0.0, be_lock_atr=0.0))
            r2b = bt2.run(df_sig)
            m2 = r2b["metrics"]
            eq2 = r2b["equity_curve"]
            n2 = eq2[-1] - 10000.0
            st.dataframe(pd.DataFrame({
                "": ["Trades", "WR", "Net", "Exp", "DD%", "LSG", "BE_n"],
                "No BE": [m2["total_trades"], f"{m2['win_rate']:.1%}", f"${n2:,.2f}",
                    f"${n2/m2['total_trades']:.2f}" if m2["total_trades"] > 0 else "-",
                    f"{m2['max_drawdown_pct']:.1f}%", f"{m2['pct_losers_saw_green']:.0%}", 0],
                "With BE": [m["total_trades"], f"{m['win_rate']:.1%}", f"${true_net:,.2f}",
                    f"${exp:.2f}", f"{m['max_drawdown_pct']:.1f}%",
                    f"{m['pct_losers_saw_green']:.0%}", m["be_raised_count"]],
            }), use_container_width=True, hide_index=True)

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(y=eq2, mode="lines", name="No BE", line=dict(color=COLORS["red"], width=1)))
            fig3.add_trace(go.Scatter(y=eq, mode="lines", name="With BE", line=dict(color=COLORS["green"], width=1)))
            fig3.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=30))
            st.plotly_chart(fig3, use_container_width=True)

        # AVWAP comparison
        if avwap_enabled:
            st.subheader("AVWAP Impact")
            bt_na = Backtester(dict(bt_params, avwap_enabled=False))
            r_na = bt_na.run(df_sig)
            m_na = r_na["metrics"]
            eq_na = r_na["equity_curve"]
            n_na = eq_na[-1] - 10000.0
            st.dataframe(pd.DataFrame({
                "": ["Trades", "WR", "Net", "Exp", "DD%", "LSG"],
                "No AVWAP": [m_na["total_trades"], f"{m_na['win_rate']:.1%}", f"${n_na:,.2f}",
                    f"${n_na/m_na['total_trades']:.2f}" if m_na["total_trades"] > 0 else "-",
                    f"{m_na['max_drawdown_pct']:.1f}%", f"{m_na['pct_losers_saw_green']:.0%}"],
                f"AVWAP {avwap_band}s": [m["total_trades"], f"{m['win_rate']:.1%}", f"${true_net:,.2f}",
                    f"${exp:.2f}", f"{m['max_drawdown_pct']:.1f}%",
                    f"{m['pct_losers_saw_green']:.0%}"],
            }), use_container_width=True, hide_index=True)

            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(y=eq_na, mode="lines", name="No AVWAP", line=dict(color=COLORS["red"], width=1)))
            fig4.add_trace(go.Scatter(y=eq, mode="lines", name=f"AVWAP {avwap_band}s", line=dict(color=COLORS["green"], width=1)))
            fig4.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=30))
            st.plotly_chart(fig4, use_container_width=True)

    # ── TAB 2: TRADE ANALYSIS ──────────────────────────────────────────────
    with tab2:
        if not trades_df.empty:
            left, right = st.columns(2)
            with left:
                st.subheader("P&L Distribution")
                fig_pnl = go.Figure()
                fig_pnl.add_trace(go.Histogram(x=trades_df["net_pnl"], nbinsx=50,
                    marker_color=COLORS["blue"], opacity=0.7))
                fig_pnl.add_vline(x=0, line_dash="dash", line_color=COLORS["gray"])
                fig_pnl.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=400,
                    xaxis_title="Net P&L ($)", yaxis_title="Count",
                    margin=dict(l=40, r=20, t=20, b=40))
                st.plotly_chart(fig_pnl, use_container_width=True)

            with right:
                st.subheader("Direction Breakdown")
                dir_stats = trades_df.groupby("direction").agg(
                    Count=("net_pnl", "count"),
                    WinRate=("net_pnl", lambda x: (x > 0).mean()),
                    AvgPnL=("net_pnl", "mean"),
                    TotalPnL=("net_pnl", "sum"),
                ).round(3)
                st.dataframe(dir_stats, use_container_width=True)

                st.subheader("Grade Breakdown")
                grade_stats = trades_df.groupby("grade").agg(
                    Count=("net_pnl", "count"),
                    WinRate=("net_pnl", lambda x: (x > 0).mean()),
                    AvgPnL=("net_pnl", "mean"),
                    TotalPnL=("net_pnl", "sum"),
                ).round(3)
                fig_grade = go.Figure(data=[
                    go.Bar(x=grade_stats.index, y=grade_stats["Count"],
                           marker_color=[COLORS["green"], COLORS["blue"], COLORS["orange"], COLORS["purple"]][:len(grade_stats)])
                ])
                fig_grade.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=250, margin=dict(l=40, r=20, t=20, b=40),
                    xaxis_title="Grade", yaxis_title="Trade Count")
                st.plotly_chart(fig_grade, use_container_width=True)

            # Duration histogram
            if "entry_bar" in trades_df.columns and "exit_bar" in trades_df.columns:
                st.subheader("Trade Duration (bars)")
                durations = trades_df["exit_bar"] - trades_df["entry_bar"]
                fig_dur = go.Figure()
                fig_dur.add_trace(go.Histogram(x=durations, nbinsx=50, marker_color=COLORS["purple"], opacity=0.7))
                fig_dur.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                    xaxis_title="Duration (bars)", yaxis_title="Count")
                st.plotly_chart(fig_dur, use_container_width=True)

            # Full trade log
            st.subheader("Trades")
            st.dataframe(trades_df[["direction", "grade", "entry_price", "exit_price",
                "pnl", "commission", "net_pnl", "mfe", "mae", "exit_reason",
                "saw_green", "be_raised"]].round(4),
                use_container_width=True, height=400)

    # ── TAB 3: MFE/MAE & LOSERS ───────────────────────────────────────────
    with tab3:
        if not trades_df.empty:
            # MFE/MAE scatter
            st.subheader("MFE / MAE Scatter")
            cols_mfe = [COLORS["green"] if p > 0 else COLORS["red"] for p in trades_df["net_pnl"]]
            fig_mfe = go.Figure()
            fig_mfe.add_trace(go.Scatter(x=trades_df["mae"], y=trades_df["mfe"], mode="markers",
                marker=dict(color=cols_mfe, size=5, opacity=0.6),
                text=trades_df.apply(lambda r: f"{r['grade']} {r['direction']} ${r['net_pnl']:.2f}", axis=1),
                hovertemplate="%{text}<br>MAE: $%{x:.2f}<br>MFE: $%{y:.2f}<extra></extra>"))
            fig_mfe.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=400,
                xaxis_title="MAE ($)", yaxis_title="MFE ($)",
                margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig_mfe, use_container_width=True)

            # Loser classification
            try:
                from ml.loser_analysis import classify_losers, get_class_summary, optimize_be_trigger, compute_etd

                classified = classify_losers(trades_df)
                summary = get_class_summary(classified)

                left3, right3 = st.columns(2)
                with left3:
                    st.subheader("Loser Classes (Sweeney)")
                    if not summary.empty:
                        class_colors = {"W": COLORS["green"], "A": COLORS["red"],
                                        "B": COLORS["orange"], "C": COLORS["purple"], "D": COLORS["gray"]}
                        fig_class = go.Figure(data=[go.Bar(
                            x=summary["class"], y=summary["count"],
                            marker_color=[class_colors.get(c, COLORS["gray"]) for c in summary["class"]],
                            text=summary.apply(lambda r: f"{r['pct']:.1f}%", axis=1),
                            textposition="auto",
                        )])
                        fig_class.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                            plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                            xaxis_title="Class", yaxis_title="Count")
                        st.plotly_chart(fig_class, use_container_width=True)
                        st.dataframe(summary.round(2), use_container_width=True, hide_index=True)

                with right3:
                    st.subheader("BE Trigger Optimization")
                    be_opt = optimize_be_trigger(trades_df)
                    if not be_opt.empty:
                        fig_be = go.Figure()
                        fig_be.add_trace(go.Scatter(x=be_opt["trigger"], y=be_opt["net_impact"],
                            mode="lines+markers", name="Net Impact",
                            line=dict(color=COLORS["blue"], width=2)))
                        fig_be.add_trace(go.Scatter(x=be_opt["trigger"], y=be_opt["saved_value"],
                            mode="lines", name="Losses Saved",
                            line=dict(color=COLORS["green"], width=1, dash="dot")))
                        fig_be.add_trace(go.Scatter(x=be_opt["trigger"], y=-be_opt["killed_value"],
                            mode="lines", name="Winners Killed (neg)",
                            line=dict(color=COLORS["red"], width=1, dash="dot")))
                        fig_be.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                            plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                            xaxis_title="BE Trigger ($)", yaxis_title="Impact ($)")
                        st.plotly_chart(fig_be, use_container_width=True)

                # ETD histogram
                st.subheader("End Trade Drawdown (ETD)")
                etd_df = compute_etd(trades_df)
                fig_etd = go.Figure()
                fig_etd.add_trace(go.Histogram(x=etd_df["etd"], nbinsx=50,
                    marker_color=COLORS["orange"], opacity=0.7))
                fig_etd.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                    xaxis_title="ETD ($)", yaxis_title="Count")
                st.plotly_chart(fig_etd, use_container_width=True)

            except ImportError as e:
                st.warning(f"ML loser analysis not available: {e}")
            except Exception as e:
                st.error(f"Loser analysis error: {e}")

    # ── TAB 4: ML META-LABEL ──────────────────────────────────────────────
    with tab4:
        if not trades_df.empty:
            try:
                from ml.features import extract_trade_features, get_feature_columns
                from ml.triple_barrier import label_trades, get_label_distribution
                from ml.meta_label import MetaLabelAnalyzer
                from ml.bet_sizing import binary_sizing, get_sizing_summary

                st.subheader("Feature Extraction")
                feat_df = extract_trade_features(trades_df, df_sig)
                feature_cols = get_feature_columns()
                avail_cols = [c for c in feature_cols if c in feat_df.columns]
                st.text(f"Extracted {len(feat_df)} trades x {len(avail_cols)} features")

                # Labels
                st.subheader("Triple Barrier Labels")
                labels = label_trades(trades_df)
                dist = get_label_distribution(labels)
                lc1, lc2, lc3 = st.columns(3)
                lc1.metric("TP (+1)", f"{dist['tp_count']} ({dist['tp_pct']:.1f}%)")
                lc2.metric("SL (-1)", f"{dist['sl_count']} ({dist['sl_pct']:.1f}%)")
                lc3.metric("Other (0)", f"{dist['other_count']} ({dist['other_pct']:.1f}%)")

                fig_labels = go.Figure(data=[go.Bar(
                    x=["TP (+1)", "SL (-1)", "Other (0)"],
                    y=[dist["tp_count"], dist["sl_count"], dist["other_count"]],
                    marker_color=[COLORS["green"], COLORS["red"], COLORS["gray"]],
                )])
                fig_labels.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=250, margin=dict(l=40, r=20, t=20, b=40))
                st.plotly_chart(fig_labels, use_container_width=True)

                # Train XGBoost
                st.subheader("XGBoost Meta-Label")
                y_binary = (labels == 1).astype(int)
                X = feat_df[avail_cols]

                analyzer = MetaLabelAnalyzer(params={
                    "n_estimators": xgb_estimators,
                    "max_depth": xgb_depth,
                })
                train_result = analyzer.train(X.values, y_binary, feature_names=avail_cols)

                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Train Samples", train_result["train_samples"])
                mc2.metric("Accuracy", f"{train_result['train_accuracy']:.1%}")
                mc3.metric("Pos Rate", f"{train_result['positive_rate']:.1%}")
                mc4.metric("NaN Dropped", train_result["dropped_nan"])

                # Feature importance
                importance = analyzer.get_feature_importance()
                if not importance.empty:
                    st.subheader("Feature Importance (XGBoost)")
                    top_n = min(15, len(importance))
                    top = importance.head(top_n)
                    fig_imp = go.Figure(data=[go.Bar(
                        x=top["importance"].values[::-1],
                        y=top["feature"].values[::-1],
                        orientation="h",
                        marker_color=COLORS["blue"],
                    )])
                    fig_imp.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=400, margin=dict(l=120, r=20, t=20, b=40))
                    st.plotly_chart(fig_imp, use_container_width=True)

                # SHAP
                try:
                    from ml.shap_analyzer import ShapAnalyzer
                    st.subheader("SHAP Global Importance")
                    shap_an = ShapAnalyzer(analyzer.model, feature_names=avail_cols)
                    shap_vals = shap_an.compute(X)
                    shap_imp = shap_an.get_global_importance()

                    top_shap = shap_imp.head(top_n)
                    fig_shap = go.Figure(data=[go.Bar(
                        x=top_shap["mean_abs_shap"].values[::-1],
                        y=top_shap["feature"].values[::-1],
                        orientation="h",
                        marker_color=COLORS["purple"],
                    )])
                    fig_shap.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=400, margin=dict(l=120, r=20, t=20, b=40),
                        xaxis_title="Mean |SHAP|")
                    st.plotly_chart(fig_shap, use_container_width=True)
                except ImportError:
                    st.info("SHAP not installed. Run: pip install shap")
                except Exception as e:
                    st.warning(f"SHAP error: {e}")

                # Bet sizing comparison
                st.subheader("Filtered vs Unfiltered")
                proba = analyzer.predict_proba(X.values)
                sizes = binary_sizing(proba, threshold=ml_threshold)
                sizing_summary = get_sizing_summary(sizes)

                # Compare
                taken_mask = sizes > 0
                skipped_mask = ~taken_mask

                bs1, bs2, bs3 = st.columns(3)
                bs1.metric("Taken", f"{sizing_summary['taken']}")
                bs2.metric("Skipped", f"{sizing_summary['skipped']}")
                bs3.metric("Skip Rate", f"{sizing_summary['skip_rate']:.1%}")

                if taken_mask.any():
                    taken_trades = trades_df.iloc[:len(sizes)][taken_mask]
                    all_net = trades_df["net_pnl"].sum()
                    taken_net = taken_trades["net_pnl"].sum()
                    taken_exp = taken_trades["net_pnl"].mean() if len(taken_trades) > 0 else 0

                    st.dataframe(pd.DataFrame({
                        "": ["Trades", "Net P&L", "Avg P&L"],
                        "All (unfiltered)": [
                            len(trades_df),
                            f"${all_net:,.2f}",
                            f"${trades_df['net_pnl'].mean():.2f}",
                        ],
                        f"ML Filtered (>{ml_threshold:.0%})": [
                            len(taken_trades),
                            f"${taken_net:,.2f}",
                            f"${taken_exp:.2f}",
                        ],
                    }), use_container_width=True, hide_index=True)

            except ImportError as e:
                st.warning(f"ML modules not available: {e}")
            except Exception as e:
                st.error(f"ML analysis error: {e}")

    # ── TAB 5: VALIDATION ─────────────────────────────────────────────────
    with tab5:
        if not trades_df.empty:
            try:
                from ml.purged_cv import purged_kfold_split, get_split_summary
                from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward
                from ml.features import extract_trade_features, get_feature_columns
                from ml.triple_barrier import label_trades
                from ml.meta_label import MetaLabelAnalyzer

                # Purged CV
                st.subheader("Purged K-Fold CV")
                splits = purged_kfold_split(trades_df, n_splits=5, embargo_bars=10)
                split_summary = get_split_summary(splits, len(trades_df))
                st.dataframe(pd.DataFrame(split_summary).round(1), use_container_width=True, hide_index=True)

                # Walk-Forward
                st.subheader("Walk-Forward Efficiency")
                n_trades = len(trades_df)
                wf_windows = generate_windows(n_trades, is_ratio=0.7, min_trades_per_window=100, step_ratio=0.3)

                if len(wf_windows) > 0:
                    feat_df = extract_trade_features(trades_df, df_sig)
                    feature_cols = get_feature_columns()
                    avail_cols = [c for c in feature_cols if c in feat_df.columns]
                    labels = label_trades(trades_df)
                    y_binary = (labels == 1).astype(int)
                    X = feat_df[avail_cols].values

                    window_results = []
                    for w in wf_windows:
                        is_start, is_end = w["is_start"], w["is_end"]
                        oos_start, oos_end = w["oos_start"], w["oos_end"]

                        X_is = X[is_start:is_end]
                        y_is = y_binary[is_start:is_end]
                        X_oos = X[oos_start:oos_end]
                        y_oos = y_binary[oos_start:oos_end]

                        if len(X_is) < 20 or len(X_oos) < 10:
                            continue

                        try:
                            model = MetaLabelAnalyzer(params={
                                "n_estimators": xgb_estimators, "max_depth": xgb_depth,
                            })
                            model.train(X_is, y_is)
                            is_acc = model.train_result.get("train_accuracy", 0) if hasattr(model, "train_result") else 0

                            proba_oos = model.predict_proba(X_oos)
                            oos_pred = (proba_oos >= 0.5).astype(int)
                            oos_acc = float(np.mean(oos_pred == y_oos))

                            wfe = compute_wfe(is_acc, oos_acc) if is_acc > 0 else 0

                            window_results.append({
                                "is_metric": is_acc,
                                "oos_metric": oos_acc,
                            })
                        except Exception:
                            continue

                    if window_results:
                        wf_summary = summarize_walk_forward(window_results)

                        wfc1, wfc2, wfc3, wfc4 = st.columns(4)
                        wfc1.metric("Windows", wf_summary["n_windows"])
                        wfc2.metric("Avg WFE", f"{wf_summary['avg_wfe']:.2f}")
                        wfc3.metric("Min WFE", f"{wf_summary['min_wfe']:.2f}")
                        wfc4.metric("Rating", wf_summary["rating"])

                        wfes = wf_summary["wfes"]
                        fig_wfe = go.Figure(data=[go.Bar(
                            x=[f"W{i+1}" for i in range(len(wfes))],
                            y=wfes,
                            marker_color=[COLORS["green"] if w >= 0.6 else COLORS["orange"] if w >= 0.3 else COLORS["red"] for w in wfes],
                        )])
                        fig_wfe.add_hline(y=0.6, line_dash="dash", line_color=COLORS["green"], annotation_text="ROBUST")
                        fig_wfe.add_hline(y=0.3, line_dash="dash", line_color=COLORS["red"], annotation_text="OVERFIT")
                        fig_wfe.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                            plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                            xaxis_title="Window", yaxis_title="WFE")
                        st.plotly_chart(fig_wfe, use_container_width=True)
                    else:
                        st.info("Not enough trades per window for walk-forward analysis.")
                else:
                    st.info(f"Need more trades for walk-forward ({n_trades} available, need 143+ per window).")

            except ImportError as e:
                st.warning(f"ML modules not available: {e}")
            except Exception as e:
                st.error(f"Validation error: {e}")

# ============================================================================
# BATCH SWEEP
# ============================================================================

else:
    st.title(f"Sweep ALL -- {timeframe}")
    avwap_label = f" AVWAP={avwap_band}s" if avwap_enabled else ""
    st.caption(f"SL={sl_mult} TP={tp_mult} CD={cooldown} BE={be_mode}{avwap_label} "
               f"N=${notional:,.0f} Comm={comm_pct}%")

    progress = st.progress(0)
    status = st.empty()
    all_results = []

    for idx, sym in enumerate(cached):
        progress.progress((idx + 1) / len(cached))
        status.text(f"[{idx+1}/{len(cached)}] {sym}...")
        try:
            df = load_data(sym, timeframe)
            if df is None or len(df) < 200:
                continue
            df_sig = compute_signals(df.copy(), signal_params)
            bt = Backtester(bt_params.copy())
            result = bt.run(df_sig)
            m = result["metrics"]
            if m["total_trades"] == 0:
                continue
            eq = result["equity_curve"]
            net = eq[-1] - 10000.0
            all_results.append({
                "Symbol": sym, "Trades": m["total_trades"],
                "WR%": round(m["win_rate"]*100, 1), "Net": round(net, 2),
                "Exp": round(net/m["total_trades"], 2),
                "LSG%": round(m["pct_losers_saw_green"]*100, 1),
                "BE_n": m["be_raised_count"], "DD%": round(m["max_drawdown_pct"], 1),
                "Sharpe": round(m["sharpe"], 3), "PF": round(m["profit_factor"], 2),
            })
            log_params(sym, timeframe, signal_params, bt_params, m)
        except Exception:
            pass

    progress.progress(1.0)
    status.text(f"Done. {len(all_results)} coins.")

    if all_results:
        rdf = pd.DataFrame(all_results).sort_values("Exp", ascending=False)
        prof = rdf[rdf["Net"] > 0]
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Coins", len(rdf))
        s2.metric("Profitable", f"{len(prof)} ({len(prof)/len(rdf)*100:.0f}%)")
        s3.metric("Trades", f"{int(rdf['Trades'].sum()):,}")
        s4.metric("Net", f"${rdf['Net'].sum():,.2f}")
        s5.metric("Avg Exp", f"${rdf['Exp'].mean():.2f}")

        st.subheader(f"Top {batch_top}")
        st.dataframe(rdf.head(batch_top), use_container_width=True, hide_index=True)
        st.subheader("All")
        st.dataframe(rdf, use_container_width=True, hide_index=True, height=600)
        st.download_button("CSV", rdf.to_csv(index=False), "sweep.csv", "text/csv")
