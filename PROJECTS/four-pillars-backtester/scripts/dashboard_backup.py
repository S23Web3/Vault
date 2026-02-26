r"""
Four Pillars Backtest Dashboard -- Streamlit GUI
ALL parameters adjustable from sidebar. Backtest runs on change.
ML learns from your parameter adjustments via param_log.jsonl.

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
    """Log every parameter adjustment + result for ML training."""
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

    # Quick equity chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=eq, mode="lines", line=dict(color=COLORS["blue"], width=1.5)))
    fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["card"], height=250, margin=dict(l=30, r=10, t=10, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # First/last 5 trades
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
# SINGLE BACKTEST (full view)
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

    # Log for ML
    log_params(symbol, timeframe, signal_params, bt_params, m)

    # Metrics row 1
    r1 = st.columns(6)
    r1[0].metric("Trades", f"{m['total_trades']:,}")
    r1[1].metric("Win Rate", f"{m['win_rate']:.1%}")
    r1[2].metric("Exp $/tr", f"${exp:.2f}")
    r1[3].metric("Net P&L", f"${true_net:,.2f}")
    r1[4].metric("PF", f"{m['profit_factor']:.2f}")
    r1[5].metric("Max DD%", f"{m['max_drawdown_pct']:.1f}%")

    # Metrics row 2
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

    # MFE/MAE + P&L histogram
    left, right = st.columns(2)
    with left:
        st.subheader("MFE / MAE")
        if not trades_df.empty:
            cols = [COLORS["green"] if p > 0 else COLORS["red"] for p in trades_df["net_pnl"]]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trades_df["mae"], y=trades_df["mfe"], mode="markers",
                marker=dict(color=cols, size=5, opacity=0.6),
                text=trades_df.apply(lambda r: f"{r['grade']} {r['direction']} ${r['net_pnl']:.2f}", axis=1),
                hovertemplate="%{text}<br>MAE: $%{x:.2f}<br>MFE: $%{y:.2f}<extra></extra>"))
            fig.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=400,
                xaxis_title="MAE ($)", yaxis_title="MFE ($)",
                margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("P&L Distribution")
        if not trades_df.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Histogram(x=trades_df["net_pnl"], nbinsx=50,
                marker_color=COLORS["blue"], opacity=0.7))
            fig2.add_vline(x=0, line_dash="dash", line_color=COLORS["gray"])
            fig2.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=400,
                xaxis_title="Net P&L ($)", yaxis_title="Count",
                margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig2, use_container_width=True)

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

    # BE comparison (only when not AVWAP)
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

    # AVWAP vs no-AVWAP comparison
    if avwap_enabled:
        st.subheader("AVWAP Impact")
        bt_no_avwap = Backtester(dict(bt_params, avwap_enabled=False))
        r_na = bt_no_avwap.run(df_sig)
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

    # Trade log
    st.subheader("Trades")
    if not trades_df.empty:
        st.dataframe(trades_df[["direction", "grade", "entry_price", "exit_price",
            "pnl", "commission", "net_pnl", "mfe", "mae", "exit_reason",
            "saw_green", "be_raised"]].round(4),
            use_container_width=True, height=400)

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
        except Exception as e:
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
