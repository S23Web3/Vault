"""
Build script: dashboard_55_89_v2.py
Creates the 55/89 EMA Cross Scalp dashboard with portfolio mode, margin/leverage
controls, comparable date windows, and breakeven controls ported from v3.9.3.

Run: python scripts/build_dashboard_55_89_v2.py
"""
import sys
import py_compile
import ast
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
ERRORS = []
CREATED = []
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def write_and_validate(filepath, content):
    """Write content to filepath, run py_compile + ast.parse. Return True on success."""
    p = Path(filepath)
    if p.exists():
        print("SKIP (exists): " + str(p))
        ERRORS.append("EXISTS: " + str(p))
        return False
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        py_compile.compile(str(p), doraise=True)
        src = p.read_text(encoding="utf-8")
        ast.parse(src, filename=str(p))
        print("PASS: " + str(p))
        CREATED.append(str(p))
        return True
    except py_compile.PyCompileError as e:
        print("SYNTAX ERROR (py_compile): " + str(e))
        ERRORS.append("SYNTAX: " + str(p))
        return False
    except SyntaxError as e:
        print("SYNTAX ERROR (ast): " + str(e))
        ERRORS.append("AST: " + str(p))
        return False
    except Exception as e:
        print("WRITE ERROR: " + str(e))
        ERRORS.append("WRITE: " + str(p))
        return False


DASHBOARD_CONTENT = r'''"""
55/89 EMA Cross Scalp Dashboard v2.

Features: margin/leverage controls, preset period filter, portfolio mode with
comparable date windows (all coins forced to same date range), breakeven sliders,
per-coin summary table, portfolio equity curve.

Run from backtester root:
  streamlit run scripts/dashboard_55_89_v2.py
"""

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
    """Load 1m parquet for symbol; normalize column names for engine compatibility."""
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
    """Filter DataFrame to [start, end] inclusive. Returns filtered copy or original."""
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


def resolve_date_range(preset, custom_start=None, custom_end=None):
    """Resolve period preset to (start_date, end_date) or None for All."""
    if preset == "All":
        return None
    if preset == "Custom":
        if custom_start and custom_end:
            return (custom_start, custom_end)
        return None
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    n = days_map.get(preset, 30)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=n)
    return (start, end)


def compute_params_hash(sig_params, bt_params, date_range, symbols):
    """Compute MD5 hash of all params for cache invalidation."""
    key = json.dumps(
        {"sig": sig_params, "bt": {k: str(v) for k, v in bt_params.items()},
         "dr": str(date_range), "syms": sorted(symbols) if isinstance(symbols, list) else [symbols]},
        sort_keys=True
    )
    return hashlib.md5(key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Backtest runner
# ---------------------------------------------------------------------------

def run_backtest_55_89(df, sig_params, bt_params):
    """Run compute_signals_55_89 then Backtester384. Returns (results, df_sig, timings)."""
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    t1 = time.perf_counter()
    bt = Backtester384(bt_params)
    results = bt.run(df_sig)
    t2 = time.perf_counter()
    return results, df_sig, (t1 - t0, t2 - t1)


# ---------------------------------------------------------------------------
# Portfolio equity alignment
# ---------------------------------------------------------------------------

def align_portfolio_equity_55_89(coin_results, initial_equity):
    """Build master datetime index, ffill-align per-coin equity curves, sum to portfolio."""
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

    return {
        "master_dt": master_dt,
        "portfolio_eq": portfolio_eq,
        "per_coin_eq": per_coin_eq,
        "portfolio_dd_pct": round(max_dd_pct, 2),
    }


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def fmt_dollar(val):
    """Format float as dollar string with sign."""
    if val >= 0:
        return "$" + "{:.2f}".format(val)
    return "-$" + "{:.2f}".format(abs(val))


def render_single_results(symbol, results, df_sig, timings, bt_params, date_range):
    """Render single-coin backtest results: metrics, equity curve, trades table."""
    m = results["metrics"]
    eq = results["equity_curve"]
    trades_df = results.get("trades_df", pd.DataFrame())

    notional = bt_params["notional"]
    margin = bt_params["margin"]
    leverage = bt_params["leverage"]
    rebate_pct = bt_params.get("rebate_pct", 0.70)

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

    # Row 3: 3 cols
    c11, c12, c13 = st.columns(3)
    total_rebate = m.get("total_rebate", 0.0)
    net_after_rebate = m.get("net_pnl_after_rebate", m.get("net_pnl", 0))
    be_raises = m.get("be_raised_count", 0)
    c11.metric("Rebate", "$" + "{:.2f}".format(total_rebate))
    c12.metric("Net w/Rebate", fmt_dollar(net_after_rebate))
    c13.metric("BE Raises", be_raises)

    # Equity curve
    st.subheader("Equity Curve")
    fig_eq = go.Figure()
    if "datetime" in df_sig.columns:
        x_axis = pd.to_datetime(df_sig["datetime"]).values
    else:
        x_axis = np.arange(len(eq))
    fig_eq.add_trace(go.Scatter(
        x=x_axis, y=eq, mode="lines", name="Equity",
        line=dict(color=COLORS["blue"], width=1)
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
            "net_pnl", "mfe", "mae", "exit_reason", "saw_green"
        ] if c in trades_df.columns]
        st.dataframe(trades_df[display_cols], use_container_width=True, height=400)
    else:
        st.warning("No trades generated. Try different parameters or a different symbol.")


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

    baseline = float(initial_equity) * n_coins
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

    # Per-coin summary table
    st.subheader("Per-Coin Results")
    rows = []
    for cr in coin_results:
        m = cr["metrics"]
        rows.append({
            "Symbol": cr["symbol"],
            "Trades": m.get("total_trades", 0),
            "WR%": round(m.get("win_rate", 0) * 100, 1),
            "Net $": round(m.get("net_pnl", 0), 2),
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

    # Thin per-coin lines
    for sym, eq_arr in per_coin_eq.items():
        fig_pf.add_trace(go.Scatter(
            x=x_axis, y=eq_arr, mode="lines", name=sym,
            line=dict(width=1), opacity=0.4,
            showlegend=True
        ))

    # Bold portfolio sum
    fig_pf.add_trace(go.Scatter(
        x=x_axis, y=portfolio_eq, mode="lines", name="Portfolio",
        line=dict(color=COLORS["green"], width=2),
        showlegend=True
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
    """Streamlit dashboard entry point for 55/89 EMA Cross Scalp."""
    st.set_page_config(page_title="55/89 EMA Cross Scalp v2", layout="wide")

    # ---- Symbol list ----
    symbols = load_symbol_list()
    if not symbols:
        st.error("No parquet files found in data/historical/ or data/cache/")
        return

    # ---- Sidebar ----
    st.sidebar.title("55/89 Scalp v2")

    # Mode
    mode = st.sidebar.radio("Mode", ["Single", "Portfolio"], horizontal=True)

    st.sidebar.markdown("---")

    # Symbol (single mode) or portfolio controls
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
        symbol = symbols[0]  # unused in portfolio mode

    st.sidebar.markdown("---")

    # Signal parameters
    st.sidebar.subheader("Signal")
    slope_n = st.sidebar.slider("Slope window N", 2, 20, 5)
    slope_m = st.sidebar.slider("Accel window M", 2, 10, 3)

    st.sidebar.markdown("---")

    # Period
    st.sidebar.subheader("Period")
    date_preset = st.sidebar.radio("Period", ["All", "7d", "30d", "90d", "Custom"],
                                   horizontal=True, index=0)
    custom_start = None
    custom_end = None
    if date_preset == "Custom":
        custom_start = st.sidebar.date_input("From")
        custom_end = st.sidebar.date_input("To")
    date_range = resolve_date_range(date_preset, custom_start, custom_end)
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
    initial_equity = st.sidebar.number_input("Initial equity ($)", value=10000.0,
                                              step=1000.0, min_value=100.0)

    st.sidebar.markdown("---")

    # Exits
    st.sidebar.subheader("Exits")
    sl_mult = st.sidebar.slider("SL multiplier (ATR x)", 0.5, 5.0, 2.5, 0.1)
    st.sidebar.caption("TP: disabled (strategy uses SL + BE only)")

    # Breakeven
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
        horizontal=True
    )
    cost_side = notional * COMMISSION_RATE
    st.sidebar.caption(
        "Per side: $" + "{:.2f}".format(cost_side)
        + " | RT: $" + "{:.2f}".format(cost_side * 2)
        + " | Net RT: $" + "{:.2f}".format(cost_side * 2 * (1 - rebate_pct))
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
                    "last_params_hash_single", "last_params_hash_portfolio"]:
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
    st.title("55/89 EMA Cross Scalp v2")

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

            with st.spinner("Computing signals + backtest..."):
                results, df_sig, timings = run_backtest_55_89(df, sig_params, bt_params)

            st.session_state["result_single"] = {
                "results": results, "df_sig": df_sig, "timings": timings,
                "symbol": symbol, "date_range": date_range,
            }

        if "result_single" in st.session_state:
            cached = st.session_state["result_single"]
            if current_hash != st.session_state.get("last_params_hash_single"):
                st.info("Settings changed. Click 'Run Backtest' to update results.")
            render_single_results(
                cached["symbol"],
                cached["results"],
                cached["df_sig"],
                cached["timings"],
                bt_params,
                cached["date_range"],
            )
        elif not run_btn:
            st.info("Configure parameters in the sidebar, then click 'Run Backtest'.")

    # ====================================================================
    # PORTFOLIO MODE
    # ====================================================================
    else:
        # Resolve which symbols to use
        if run_btn:
            if port_source == "Random N":
                selected = random.sample(list(symbols), min(port_n, len(symbols)))
            else:
                selected = list(port_custom) if port_custom else symbols[:port_n]
            st.session_state["port_symbols_locked"] = selected

            current_hash = compute_params_hash(sig_params, bt_params, date_range, selected)
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
                    results, df_sig, _ = run_backtest_55_89(df, sig_params, bt_params)
                except Exception as exc:
                    skipped.append(sym + " (error: " + str(exc) + ")")
                    continue
                if results["metrics"].get("total_trades", 0) == 0:
                    skipped.append(sym + " (0 trades)")
                    continue
                # Build datetime index for equity alignment
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

            pf_data = align_portfolio_equity_55_89(coin_results, initial_equity)
            st.session_state["result_portfolio"] = {
                "coin_results": coin_results,
                "pf_data": pf_data,
                "date_range": date_range,
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
                initial_equity,
                cached_pf["date_range"],
            )
        elif not run_btn:
            st.info("Configure parameters in the sidebar, then click 'Run Portfolio Backtest'.")


if __name__ == "__main__":
    main()
'''


if __name__ == "__main__":
    print("=" * 60)
    print("Building dashboard_55_89_v2.py")
    print(TIMESTAMP)
    print("=" * 60)

    if not ROOT.exists():
        print("ERROR: ROOT not found: " + str(ROOT))
        sys.exit(1)

    target = ROOT / "scripts" / "dashboard_55_89_v2.py"
    write_and_validate(target, DASHBOARD_CONTENT)

    print("=" * 60)
    if ERRORS:
        print("BUILD FAILED")
        for e in ERRORS:
            print("  " + e)
        sys.exit(1)
    else:
        print("BUILD SUCCESS")
        print("Files created: " + str(len(CREATED)))
        for f in CREATED:
            print("  " + f)
        print("")
        print("Run:")
        print('  cd "' + str(ROOT) + '"')
        print('  streamlit run scripts/dashboard_55_89_v2.py')
