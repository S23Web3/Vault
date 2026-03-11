"""
55/89 EMA Cross Scalp Dashboard — standalone Streamlit app.

Runs the 55/89 signal pipeline through Backtester384 with configurable params.
Does NOT modify dashboard_v394.py.

Run from backtester root:
  streamlit run scripts/dashboard_v394_55_89.py

Full path:
  streamlit run scripts/dashboard_v394_55_89.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from signals.ema_cross_55_89 import compute_signals_55_89
from engine.backtester_v384 import Backtester384


# ---- Theme ----
COLORS = {
    "bg": "#0f1419", "card": "#1a1f26", "text": "#e7e9ea",
    "green": "#10b981", "red": "#ef4444", "blue": "#3b82f6",
    "orange": "#f59e0b", "purple": "#8b5cf6", "gray": "#6b7280",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_symbol_list():
    """Scan data dirs for available 1m parquets."""
    symbols = set()
    for subdir in ["historical", "cache"]:
        d = PROJECT_ROOT / "data" / subdir
        if d.exists():
            for f in d.glob("*_1m.parquet"):
                sym = f.stem.replace("_1m", "")
                symbols.add(sym)
    return sorted(symbols)


def load_data(symbol):
    """Load 1m parquet for symbol."""
    for subdir in ["historical", "cache"]:
        path = PROJECT_ROOT / "data" / subdir / f"{symbol}_1m.parquet"
        if path.exists():
            return pd.read_parquet(path)
    return None


def run_backtest(df, sig_params, bt_params):
    """Run signal pipeline + backtest engine."""
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    t1 = time.perf_counter()
    bt = Backtester384(bt_params)
    results = bt.run(df_sig)
    t2 = time.perf_counter()
    return results, df_sig, (t1 - t0, t2 - t1)


def main():
    """Streamlit dashboard entry point."""
    st.set_page_config(page_title="55/89 EMA Cross Scalp", layout="wide")
    st.title("55/89 EMA Cross Scalp Backtest")

    # ---- Sidebar ----
    st.sidebar.header("Symbol")
    symbols = load_symbol_list()
    if not symbols:
        st.error("No parquet files found in data/historical/ or data/cache/")
        return

    symbol = st.sidebar.selectbox("Symbol", symbols, index=symbols.index("BTCUSDT") if "BTCUSDT" in symbols else 0)

    st.sidebar.header("Signal Parameters")
    slope_n = st.sidebar.slider("Slope window N", 2, 20, 5)
    slope_m = st.sidebar.slider("Accel window M", 2, 10, 3)

    st.sidebar.header("Backtest Parameters")
    sl_mult = st.sidebar.slider("SL multiplier (ATR)", 0.5, 5.0, 2.5, 0.1)
    notional = st.sidebar.number_input("Notional ($)", 1000, 50000, 5000, 1000)
    initial_equity = st.sidebar.number_input("Initial equity ($)", 1000, 100000, 10000, 1000)

    st.sidebar.header("Date Filter")
    use_date = st.sidebar.checkbox("Filter by date range")
    date_range = None
    if use_date:
        start_date = st.sidebar.date_input("Start date")
        end_date = st.sidebar.date_input("End date")
        date_range = (start_date, end_date)

    if st.sidebar.button("Run Backtest", type="primary"):
        with st.spinner("Loading data..."):
            df = load_data(symbol)
            if df is None:
                st.error(f"No data for {symbol}")
                return

            if date_range:
                start_ts = pd.Timestamp(date_range[0], tz="UTC")
                end_ts = pd.Timestamp(date_range[1], tz="UTC") + pd.Timedelta(days=1)
                if "datetime" in df.columns:
                    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
                    df = df[(df["datetime"] >= start_ts) & (df["datetime"] < end_ts)].reset_index(drop=True)

            st.info(f"Running on {len(df):,} bars...")

        sig_params = {"slope_n": slope_n, "slope_m": slope_m}
        bt_params = {
            "sl_mult": sl_mult,
            "tp_mult": None,
            "be_trigger_atr": 0.0,
            "be_lock_atr": 0.0,
            "notional": notional,
            "max_positions": 1,
            "cooldown": 1,
            "enable_adds": False,
            "enable_reentry": False,
            "commission_rate": 0.0008,
            "initial_equity": initial_equity,
        }

        with st.spinner("Computing signals + backtest..."):
            results, df_sig, timings = run_backtest(df, sig_params, bt_params)

        m = results["metrics"]
        trades_df = results.get("trades_df", pd.DataFrame())

        # ---- Metrics row ----
        st.subheader(f"{symbol} -- Results")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Trades", m.get("total_trades", 0))
        c2.metric("Win Rate", f"{m.get('win_rate', 0):.1%}")
        c3.metric("Net PnL", f"${m.get('net_pnl', 0):.2f}")
        c4.metric("Profit Factor", f"{m.get('profit_factor', 0):.2f}")
        c5.metric("Sharpe", f"{m.get('sharpe', 0):.3f}")
        c6.metric("Max DD", f"{m.get('max_drawdown_pct', 0):.1f}%")

        c7, c8, c9, c10 = st.columns(4)
        c7.metric("Avg Win", f"${m.get('avg_win', 0):.2f}")
        c8.metric("Avg Loss", f"${m.get('avg_loss', 0):.2f}")
        c9.metric("Expectancy", f"${m.get('expectancy', 0):.2f}")
        c10.metric("Commission", f"${m.get('total_commission', 0):.2f}")

        ts_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
        st.caption(f"Signal: {timings[0]:.1f}s | Engine: {timings[1]:.1f}s | {ts_str} UTC")

        # ---- Signal counts ----
        long_count = int(df_sig["long_a"].sum())
        short_count = int(df_sig["short_a"].sum())
        st.write(f"Signal counts: {long_count} long, {short_count} short")

        # ---- Equity curve ----
        st.subheader("Equity Curve")
        eq = results["equity_curve"]
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(y=eq, mode="lines", name="Equity",
                                     line=dict(color=COLORS["blue"], width=1)))
        fig_eq.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
            margin=dict(l=40, r=20, t=30, b=30),
        )
        st.plotly_chart(fig_eq, use_container_width=True)

        # ---- Trades table ----
        if len(trades_df) > 0:
            st.subheader("Trades")
            st.dataframe(trades_df, use_container_width=True, height=400)
        else:
            st.warning("No trades generated. Try different parameters or a different symbol.")


if __name__ == "__main__":
    main()
