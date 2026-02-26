"""
Dashboard v3 -- VINCE Control Panel.
6-tab architecture: Single Coin | Discovery Sweep | Optimizer | Validation | Capital & Risk | Deploy

Based on dashboard_v2.py with:
  - st.tabs() restructure (replaces mode-based navigation)
  - Edge Quality panel (Tab 1)
  - Disk-persistent sweep (Tab 2)
  - Capital & Risk metrics (Tab 5)
  - Placeholder tabs (3, 4, 6)
  - CD-1 through CD-5 code debt fixes
  - S-1 date range, S-2 param presets, S-3 sweep stop
"""

import os
import sys
import json
import time
import hashlib
import logging
import logging.handlers
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from data.fetcher import BybitFetcher
from data.normalizer import OHLCVNormalizer
from signals.four_pillars_v383 import compute_signals_v383

# Try v385 first, fall back to v384
try:
    from engine.backtester_v385 import Backtester385 as Backtester
    _BT_VERSION = "v385"
except ImportError:
    from engine.backtester_v384 import Backtester384 as Backtester
    _BT_VERSION = "v384"

from gui.parameter_inputs import DEFAULT_PARAMS

# Logging
os.makedirs(os.path.join(_ROOT, "logs"), exist_ok=True)
_log_handler = logging.handlers.RotatingFileHandler(
    os.path.join(_ROOT, "logs", "dashboard.log"),
    maxBytes=5*1024*1024, backupCount=3,
)
_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger = logging.getLogger("dashboard_v3")
logger.addHandler(_log_handler)
logger.setLevel(logging.INFO)

st.set_page_config(page_title="VINCE Control Panel", layout="wide")

# --- Helper functions ---

def safe_dataframe(df):
    """Catch Arrow serialization errors by casting all to str."""
    try:
        st.dataframe(df, width=None)
    except Exception as e:
        logger.warning(f"Arrow error, falling back to str: {e}")
        st.dataframe(df.astype(str), width=None)


def safe_plotly_chart(fig, **kwargs):
    """Wrapper for st.plotly_chart with error handling."""
    try:
        st.plotly_chart(fig, use_container_width=True, **kwargs)
    except Exception as e:
        logger.warning(f"Plotly error: {e}")
        st.error(f"Chart error: {e}")


def params_hash(params):
    """MD5 hash of params dict for sweep file naming."""
    s = json.dumps(params, sort_keys=True, default=str)
    return hashlib.md5(s.encode()).hexdigest()[:8]


def load_presets():
    """Load param presets from data/presets/."""
    preset_dir = os.path.join(_ROOT, "data", "presets")
    os.makedirs(preset_dir, exist_ok=True)
    presets = {}
    for f in os.listdir(preset_dir):
        if f.endswith(".json"):
            name = f[:-5]
            with open(os.path.join(preset_dir, f), "r") as fh:
                presets[name] = json.load(fh)
    return presets


def save_preset(name, params):
    """Save param preset to data/presets/."""
    preset_dir = os.path.join(_ROOT, "data", "presets")
    os.makedirs(preset_dir, exist_ok=True)
    with open(os.path.join(preset_dir, f"{name}.json"), "w") as f:
        json.dump(params, f, indent=2)


def get_cached_symbols():
    """Return list of symbols with cached data."""
    cache_dir = os.path.join(_ROOT, "data", "cache")
    if not os.path.exists(cache_dir):
        return []
    symbols = set()
    for f in os.listdir(cache_dir):
        if f.endswith(".parquet"):
            parts = f.replace(".parquet", "").split("_")
            if len(parts) >= 2:
                symbols.add(parts[0])
    return sorted(symbols)


@st.cache_data(ttl=300)
def load_cached_data(symbol, timeframe):
    """Load cached OHLCV data for a symbol."""
    cache_dir = os.path.join(_ROOT, "data", "cache")
    path = os.path.join(cache_dir, f"{symbol}_{timeframe}.parquet")
    if not os.path.exists(path):
        path = os.path.join(cache_dir, f"{symbol}_1m.parquet")
        if not os.path.exists(path):
            return None
    return pd.read_parquet(path)


def run_backtest(symbol, timeframe, signal_params, bt_params, date_range=None):
    """Run a single backtest. Returns results dict."""
    df = load_cached_data(symbol, timeframe)
    if df is None:
        return None

    # Date range filter (S-1)
    if date_range and len(date_range) == 2:
        start_dt, end_dt = date_range
        if "datetime" in df.columns:
            mask = (pd.to_datetime(df["datetime"]) >= pd.Timestamp(start_dt)) & \
                   (pd.to_datetime(df["datetime"]) <= pd.Timestamp(end_dt))
            df = df[mask].reset_index(drop=True)
        elif isinstance(df.index, pd.DatetimeIndex):
            df = df[start_dt:end_dt].reset_index(drop=True)

    if len(df) < 100:
        return None

    # Resample if needed
    if timeframe != "1m" and "datetime" in df.columns:
        from data.normalizer import OHLCVNormalizer
        norm = OHLCVNormalizer()
        df = norm.resample_ohlcv(df, timeframe)

    df = compute_signals_v383(df, signal_params)
    bt = Backtester(params=bt_params)
    results = bt.run(df, bt_params)
    return results


def render_detail_view(results, symbol):
    """
    Render the 5-tab analysis view for a single backtest result.
    Used by both Tab 1 (Single Coin) and Tab 2 (Sweep drill-down).
    This is CD-1: extracted from duplicated code in v2.
    """
    if results is None:
        st.warning("No results to display.")
        return

    metrics = results.get("metrics", {})
    trades_df = results.get("trades_df", pd.DataFrame())
    equity = results.get("equity_curve", [])

    sub_tabs = st.tabs(["Overview", "Trade Analysis", "MFE/MAE", "ML Meta-Label", "Validation"])

    # --- Overview ---
    with sub_tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Net PnL", f"${metrics.get('net_pnl', 0):,.2f}")
        c2.metric("Trades", str(metrics.get('total_trades', 0)))
        c3.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")
        c4.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")

        # Edge Quality panel (new in v3)
        st.subheader("Edge Quality")
        eq1, eq2, eq3, eq4 = st.columns(4)
        eq1.metric("Avg Winner", f"${metrics.get('avg_winner', 0):,.2f}")
        eq2.metric("Avg Loser", f"${metrics.get('avg_loser', 0):,.2f}")
        eq3.metric("W/L Ratio", f"{metrics.get('wl_ratio', 0):.2f}")
        eq4.metric("Calmar", f"{metrics.get('calmar', 0):.2f}"
                   if metrics.get('calmar', 0) != float('inf') else "INF")

        eq5, eq6, eq7, eq8 = st.columns(4)
        eq5.metric("Max Win", f"${metrics.get('max_single_win', 0):,.2f}")
        eq6.metric("Max Loss", f"${metrics.get('max_single_loss', 0):,.2f}")
        eq7.metric("Win Streak", str(metrics.get('max_win_streak', 0)))
        eq8.metric("Loss Streak", str(metrics.get('max_loss_streak', 0)))

        lsg_pct = metrics.get("lsg_pct", 0)
        if lsg_pct > 90:
            st.warning(f"LSG: {lsg_pct:.1f}% [HIGH REVERSION]")
        elif lsg_pct > 0:
            st.info(f"LSG: {lsg_pct:.1f}%")

        # Equity curve
        if equity:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=equity, mode="lines", name="Equity"))
            fig.update_layout(title=f"{symbol} Equity Curve", height=400)
            safe_plotly_chart(fig)

    # --- Trade Analysis ---
    with sub_tabs[1]:
        if not trades_df.empty:
            st.subheader("Trade Log")
            display_cols = [c for c in trades_df.columns if c in [
                "direction", "grade", "entry_bar", "exit_bar",
                "entry_price", "exit_price", "pnl", "commission",
                "mfe", "mae", "exit_reason", "saw_green",
                "life_pnl_path", "lsg_category",
            ]]
            safe_dataframe(trades_df[display_cols] if display_cols else trades_df)

            # Grade distribution
            if "grade" in trades_df.columns:
                grade_counts = trades_df["grade"].value_counts()
                fig = px.bar(x=grade_counts.index, y=grade_counts.values,
                             title="Grade Distribution")
                safe_plotly_chart(fig)
        else:
            st.info("No trades.")

    # --- MFE/MAE ---
    with sub_tabs[2]:
        if not trades_df.empty and "mfe" in trades_df.columns:
            fig = px.scatter(trades_df, x="mae", y="mfe",
                             color="exit_reason" if "exit_reason" in trades_df.columns else None,
                             title="MFE vs MAE Scatter")
            safe_plotly_chart(fig)
        else:
            st.info("No MFE/MAE data.")

    # --- ML Meta-Label ---
    with sub_tabs[3]:
        try:
            from ml.meta_label import MetaLabelAnalyzer
            from ml.features_v2 import extract_trade_features, get_feature_columns
            st.info("ML Meta-Label analysis available. Run from Tab 1 with backtest results.")
        except ImportError:
            st.info("ML modules not available.")

    # --- Validation ---
    with sub_tabs[4]:
        try:
            from ml.walk_forward import summarize_walk_forward
            st.info("Walk-Forward validation available. Requires ML training first.")
        except ImportError:
            st.info("Validation modules not available.")

# --- Sidebar ---

def render_sidebar():
    """Render sidebar with strategy params. Returns (signal_params, bt_params, date_range)."""
    st.sidebar.title("VINCE Control Panel")
    st.sidebar.caption(f"Backtester: {_BT_VERSION}")

    # S-2: Param presets
    presets = load_presets()
    preset_names = ["(Custom)"] + list(presets.keys())
    selected_preset = st.sidebar.selectbox("Preset", preset_names)

    defaults = DEFAULT_PARAMS.copy()
    if selected_preset != "(Custom)" and selected_preset in presets:
        defaults.update(presets[selected_preset])

    # Save preset
    with st.sidebar.expander("Save/Delete Preset"):
        new_name = st.text_input("Preset name")
        if st.button("Save Current") and new_name:
            save_preset(new_name, defaults)
            st.success(f"Saved: {new_name}")
            st.rerun()

    st.sidebar.divider()

    # Symbol & timeframe
    symbols = get_cached_symbols()
    symbol = st.sidebar.selectbox("Symbol", symbols if symbols else ["RIVERUSDT"])
    timeframe = st.sidebar.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "30m", "1h"], index=2)

    # S-1: Date range filter
    date_range = None
    use_date_filter = st.sidebar.checkbox("Date Range Filter")
    if use_date_filter:
        d1 = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=90))
        d2 = st.sidebar.date_input("End Date", datetime.now())
        date_range = (d1, d2)

    st.sidebar.divider()

    # Stochastic params
    st.sidebar.subheader("Stochastics")
    k9 = st.sidebar.number_input("K9 Period", value=defaults.get("stoch_k9", 9), min_value=1)
    k14 = st.sidebar.number_input("K14 Period", value=defaults.get("stoch_k14", 14), min_value=1)
    k40 = st.sidebar.number_input("K40 Period", value=defaults.get("stoch_k40", 40), min_value=1)
    k60 = st.sidebar.number_input("K60 Period", value=defaults.get("stoch_k60", 60), min_value=1)

    st.sidebar.divider()

    # Strategy params
    st.sidebar.subheader("Strategy")
    sl_mult = st.sidebar.slider("SL Multiplier (ATR)", 0.5, 5.0, defaults.get("sl_mult", 2.5), 0.1)
    tp_mult = st.sidebar.slider("TP Multiplier (ATR)", 0.0, 5.0, defaults.get("tp_mult", 2.0), 0.1)
    cooldown = st.sidebar.slider("Cooldown (bars)", 0, 20, defaults.get("cooldown", 3))
    margin = st.sidebar.number_input("Margin ($)", value=defaults.get("margin", 500.0))
    leverage = st.sidebar.number_input("Leverage", value=defaults.get("leverage", 20))
    commission_rate = st.sidebar.number_input("Commission Rate", value=defaults.get("commission_rate", 0.0008), format="%.4f")
    rebate_pct = st.sidebar.slider("Rebate %", 0, 100, defaults.get("rebate_pct", 70))

    signal_params = {
        "stoch_k9": k9, "stoch_k14": k14, "stoch_k40": k40, "stoch_k60": k60,
    }
    bt_params = {
        "symbol": symbol, "timeframe": timeframe,
        "sl_mult": sl_mult, "tp_mult": tp_mult, "cooldown": cooldown,
        "margin": margin, "leverage": leverage,
        "commission_rate": commission_rate, "rebate_pct": rebate_pct,
    }

    return symbol, timeframe, signal_params, bt_params, date_range

# --- Main tab rendering ---

def render_tab1_single(symbol, timeframe, signal_params, bt_params, date_range):
    """Tab 1: Single Coin analysis."""
    run_btn = st.button("Run Backtest", disabled=st.session_state.get("single_running", False))

    if run_btn:
        st.session_state["single_running"] = True
        with st.spinner(f"Running {symbol} {timeframe}..."):
            results = run_backtest(symbol, timeframe, signal_params, bt_params, date_range)
            st.session_state["single_results"] = results
            st.session_state["single_symbol"] = symbol
        st.session_state["single_running"] = False

    results = st.session_state.get("single_results")
    sym = st.session_state.get("single_symbol", symbol)
    if results:
        render_detail_view(results, sym)
    else:
        st.info("Click 'Run Backtest' to analyze a coin.")


def render_tab2_sweep(symbol, timeframe, signal_params, bt_params, date_range):
    """Tab 2: Discovery Sweep with disk persistence."""
    ph = params_hash({**signal_params, **bt_params, "tf": timeframe})
    csv_path = os.path.join(_ROOT, "results", f"sweep_v3_{timeframe}_{ph}.csv")

    # Load existing sweep state
    existing_df = None
    completed_symbols = set()
    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path)
        completed_symbols = set(existing_df["symbol"].tolist())

    # Source selection
    source = st.radio("Source", ["All Cache", "Custom List", "Upload Data"], horizontal=True)
    if source == "All Cache":
        sweep_symbols = get_cached_symbols()
    elif source == "Custom List":
        custom_text = st.text_area("Symbols (one per line)")
        sweep_symbols = [s.strip() for s in custom_text.split("\n") if s.strip()]
    else:
        # CD-5: Upload flow preserved
        uploaded = st.file_uploader("Upload CSV/OHLCV file")
        if uploaded:
            try:
                norm = OHLCVNormalizer()
                content = uploaded.read().decode("utf-8")
                import io
                raw_df = pd.read_csv(io.StringIO(content))
                detected = norm.detect_format(raw_df)
                st.write(f"Detected format: {detected}")
                sym_input = st.text_input("Symbol for this data")
                if st.button("Convert & Add to Cache") and sym_input:
                    normalized = norm.normalize(raw_df)
                    cache_path = os.path.join(_ROOT, "data", "cache", f"{sym_input}_1m.parquet")
                    normalized.to_parquet(cache_path)
                    st.success(f"Saved to cache: {sym_input}")
            except Exception as e:
                st.error(f"Upload error: {e}")
        sweep_symbols = get_cached_symbols()

    remaining = [s for s in sweep_symbols if s not in completed_symbols]
    total = len(sweep_symbols)
    done = len(completed_symbols)

    st.write(f"Total: {total} | Done: {done} | Remaining: {len(remaining)}")

    # Sweep controls (always visible, disable during run)
    col1, col2, col3 = st.columns(3)
    is_running = st.session_state.get("sweep_running", False)
    start_btn = col1.button("Start Sweep", disabled=is_running or len(remaining) == 0)
    resume_btn = col2.button("Resume", disabled=is_running or len(remaining) == 0)
    stop_btn = col3.button("Stop Sweep")  # S-3

    if stop_btn:
        st.session_state["sweep_stop"] = True

    if start_btn:
        # New sweep -- delete old CSV
        if os.path.exists(csv_path):
            os.remove(csv_path)
        completed_symbols = set()
        remaining = sweep_symbols[:]
        st.session_state["sweep_stop"] = False
        st.session_state["sweep_running"] = True

    if resume_btn:
        st.session_state["sweep_stop"] = False
        st.session_state["sweep_running"] = True

    if st.session_state.get("sweep_running", False) and remaining:
        sym = remaining[0]
        progress = st.progress((done) / max(total, 1))
        st.write(f"[Sweep: {sym} {done+1}/{total}]")

        try:
            results = run_backtest(sym, timeframe, signal_params, bt_params, date_range)
            if results:
                m = results.get("metrics", {})
                row = {
                    "symbol": sym,
                    "start_date": "", "end_date": "", "calendar_days": 0,
                    "trades": m.get("total_trades", 0),
                    "wr_pct": m.get("win_rate", 0),
                    "expectancy": m.get("expectancy", 0),
                    "net_pnl": m.get("net_pnl", 0),
                    "profit_factor": m.get("profit_factor", 0),
                    "grade": m.get("dominant_grade", ""),
                    "sharpe": m.get("sharpe", 0),
                    "sortino": m.get("sortino", 0),
                    "calmar": m.get("calmar", 0),
                    "max_dd_pct": m.get("max_dd_pct", 0),
                    "max_dd_amt": m.get("max_drawdown", 0),
                    "peak_capital": m.get("peak_capital", 0),
                    "capital_efficiency": m.get("capital_efficiency", 0),
                    "max_single_win": m.get("max_single_win", 0),
                    "max_single_loss": m.get("max_single_loss", 0),
                    "avg_winner": m.get("avg_winner", 0),
                    "avg_loser": m.get("avg_loser", 0),
                    "wl_ratio": m.get("wl_ratio", 0),
                    "max_win_streak": m.get("max_win_streak", 0),
                    "max_loss_streak": m.get("max_loss_streak", 0),
                    "lsg_pct": m.get("lsg_pct", 0),
                    "lsg_bars_avg": m.get("lsg_bars_avg", 0),
                    "tp_exits": m.get("tp_exits", 0),
                    "sl_exits": m.get("sl_exits", 0),
                    "be_exits": m.get("be_exits", 0),
                    "scale_outs": m.get("scale_outs", 0),
                    "volume": m.get("total_volume", 0),
                    "rebate": m.get("total_rebate", 0),
                    "net_after_rebate": m.get("net_pnl", 0) + m.get("total_rebate", 0),
                    "status": "ok",
                    "timestamp": datetime.now().isoformat(),
                }
                row_df = pd.DataFrame([row])
                if os.path.exists(csv_path):
                    row_df.to_csv(csv_path, mode="a", header=False, index=False)
                else:
                    row_df.to_csv(csv_path, index=False)
            else:
                # CD-2: Log errors instead of silent pass
                err_row = pd.DataFrame([{"symbol": sym, "status": "error: no data",
                                         "timestamp": datetime.now().isoformat()}])
                if os.path.exists(csv_path):
                    err_row.to_csv(csv_path, mode="a", header=False, index=False)
                else:
                    err_row.to_csv(csv_path, index=False)
                logger.warning(f"Sweep: {sym} returned no results")

        except Exception as e:
            # CD-2: Error tracking
            logger.error(f"Sweep error {sym}: {e}", exc_info=True)
            err_row = pd.DataFrame([{"symbol": sym, "status": f"error: {e}",
                                     "timestamp": datetime.now().isoformat()}])
            if os.path.exists(csv_path):
                err_row.to_csv(csv_path, mode="a", header=False, index=False)
            else:
                err_row.to_csv(csv_path, index=False)

        # Check stop
        if st.session_state.get("sweep_stop", False):
            st.session_state["sweep_running"] = False
            st.info("Sweep stopped. Use Resume to continue.")
        else:
            st.rerun()
    else:
        st.session_state["sweep_running"] = False

    # Display results
    if os.path.exists(csv_path):
        sweep_df = pd.read_csv(csv_path)
        ok_df = sweep_df[sweep_df.get("status", pd.Series(["ok"]*len(sweep_df))) == "ok"]
        err_count = len(sweep_df) - len(ok_df)

        if not ok_df.empty:
            # Summary row
            st.subheader("Sweep Results")
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Coins", str(len(ok_df)))
            profitable = ok_df[ok_df.get("net_pnl", pd.Series([0])) > 0] if "net_pnl" in ok_df.columns else ok_df
            s2.metric("Profitable", f"{len(profitable)} ({len(profitable)/max(len(ok_df),1)*100:.0f}%)")
            s3.metric("Total Trades", f"{int(ok_df['trades'].sum()):,}" if "trades" in ok_df.columns else "0")
            s4.metric("Total Net", f"${ok_df['net_pnl'].sum():,.2f}" if "net_pnl" in ok_df.columns else "$0")

            if err_count > 0:
                st.warning(f"{err_count} coins failed. Check logs/dashboard.log")

            # Filters
            st.subheader("Filters")
            fc1, fc2, fc3 = st.columns(3)
            min_trades = fc1.slider("Min Trades", 0, 500, 100)
            max_dd = fc2.slider("Max DD%", 0, 100, 30)
            min_calmar = fc3.slider("Min Calmar", 0.0, 10.0, 0.5)

            filtered = ok_df.copy()
            if "trades" in filtered.columns:
                filtered = filtered[filtered["trades"] >= min_trades]
            if "max_dd_pct" in filtered.columns:
                filtered = filtered[filtered["max_dd_pct"].abs() <= max_dd]
            if "calmar" in filtered.columns:
                filtered = filtered[filtered["calmar"] >= min_calmar]

            # Sort by Calmar (not net PnL)
            if "calmar" in filtered.columns:
                filtered = filtered.sort_values("calmar", ascending=False)

            safe_dataframe(filtered)

            # Charts
            if "calmar" in filtered.columns and len(filtered) > 0:
                top20 = filtered.head(20)
                fig = px.bar(top20, x="calmar", y="symbol", orientation="h",
                             title="Top 20 by Calmar Ratio")
                safe_plotly_chart(fig)

            if "net_pnl" in filtered.columns and "max_dd_pct" in filtered.columns:
                fig = px.scatter(filtered, x="max_dd_pct", y="net_pnl",
                                 size="trades" if "trades" in filtered.columns else None,
                                 hover_name="symbol", title="Net PnL vs Max DD%")
                safe_plotly_chart(fig)

            # Export
            csv_export = filtered.to_csv(index=False)
            st.download_button("Download CSV", csv_export, "sweep_results.csv")

            # Drill-down
            st.subheader("Drill-Down")
            if "symbol" in filtered.columns:
                drill_sym = st.selectbox("Select coin for detail", filtered["symbol"].tolist())
                if st.button("Show Detail"):
                    with st.spinner(f"Running {drill_sym}..."):
                        detail_results = run_backtest(drill_sym, timeframe, signal_params, bt_params, date_range)
                    if detail_results:
                        render_detail_view(detail_results, drill_sym)


def render_tab3_placeholder():
    """Tab 3: Optimizer placeholder."""
    st.subheader("Optimizer (VINCE)")
    st.info("Coming soon. This tab will provide per-coin parameter optimization "
            "using grid search across SL, TP, cooldown, and BE parameters. "
            "Requires filtered coin list from Discovery Sweep (Tab 2).")
    st.write("Planned features:")
    st.write("- Grid search across param ranges per coin")
    st.write("- Best param combo by Calmar ratio")
    st.write("- Heatmap: parameter sensitivity")
    st.write("- Overfitting risk flag")


def render_tab4_placeholder():
    """Tab 4: Validation placeholder."""
    st.subheader("Validation (WFE)")
    st.info("Coming soon. This tab will validate whether the discovered edge is real "
            "or overfit, using Walk-Forward Efficiency and Monte Carlo analysis.")
    st.write("Planned features:")
    st.write("- Walk-Forward Efficiency: train 70%, test 30%")
    st.write("- Monte Carlo: randomize entry order 1000x")
    st.write("- Out-of-sample holdout test")
    st.write("- Confidence grade: HIGH / MEDIUM / LOW / REJECT")


def render_tab5_capital(timeframe, bt_params):
    """Tab 5: Capital & Risk from sweep CSV."""
    st.subheader("Capital & Risk")

    # Find most recent sweep CSV
    results_dir = os.path.join(_ROOT, "results")
    csvs = [f for f in os.listdir(results_dir) if f.startswith("sweep_v3_") and f.endswith(".csv")]
    if not csvs:
        st.info("No sweep results found. Run a Discovery Sweep first (Tab 2).")
        return

    selected_csv = st.selectbox("Sweep file", csvs)
    sweep_df = pd.read_csv(os.path.join(results_dir, selected_csv))
    ok_df = sweep_df[sweep_df.get("status", pd.Series(["ok"]*len(sweep_df))) == "ok"]

    if ok_df.empty:
        st.warning("No successful sweep results in this file.")
        return

    # Portfolio metrics
    st.subheader("Portfolio Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Coins", str(len(ok_df)))
    m2.metric("Total Trades", f"{int(ok_df.get('trades', pd.Series([0])).sum()):,}")
    total_net = ok_df.get("net_pnl", pd.Series([0])).sum()
    m3.metric("Total Net PnL", f"${total_net:,.2f}")
    total_rebate = ok_df.get("rebate", pd.Series([0])).sum()
    m4.metric("Total Rebate", f"${total_rebate:,.2f}")

    m5, m6, m7, m8 = st.columns(4)
    pk = ok_df.get("peak_capital", pd.Series([0])).sum()
    m5.metric("Sum Peak Capital", f"${pk:,.2f}")
    m6.metric("Portfolio Cap Eff", f"{total_net/pk*100:.1f}%" if pk > 0 else "N/A")
    avg_cal = ok_df.get("calmar", pd.Series([0])).mean()
    m7.metric("Avg Calmar", f"{avg_cal:.2f}")
    worst_cal = ok_df.get("calmar", pd.Series([0])).min()
    m8.metric("Worst Calmar", f"{worst_cal:.2f}")

    # Risk scenarios
    st.subheader("Risk Scenarios")
    max_dd_sum = ok_df.get("max_dd_amt", pd.Series([0])).abs().sum()
    st.write(f"Worst case (all coins hit max DD simultaneously): ${max_dd_sum:,.2f}")

    # Charts
    if "calmar" in ok_df.columns:
        fig = px.histogram(ok_df, x="calmar", nbins=20, title="Calmar Distribution")
        safe_plotly_chart(fig)

    if "peak_capital" in ok_df.columns:
        fig = px.bar(ok_df.sort_values("peak_capital", ascending=False).head(20),
                     x="symbol", y="peak_capital", title="Top 20 Capital Utilization")
        safe_plotly_chart(fig)


def render_tab6_placeholder():
    """Tab 6: Deploy placeholder."""
    st.subheader("Deploy")
    st.info("Coming soon. This tab will generate per-coin JSON configs for n8n "
            "webhooks and manage the transition from backtest to live trading.")
    st.write("Planned features:")
    st.write("- Per-coin JSON config for n8n webhooks")
    st.write("- Exchange API setup checklist")
    st.write("- Position size calculator")
    st.write("- Paper trade mode toggle")
    st.write("- Export all configs as ZIP")


# === MAIN ===

def main():
    symbol, timeframe, signal_params, bt_params, date_range = render_sidebar()

    # Persistent status banner
    results_dir = os.path.join(_ROOT, "results")
    csvs = [f for f in os.listdir(results_dir) if f.startswith("sweep_v3_") and f.endswith(".csv")]
    if st.session_state.get("sweep_running", False):
        st.info("[Sweep in progress...]")
    elif csvs:
        latest = max(csvs, key=lambda f: os.path.getmtime(os.path.join(results_dir, f)))
        n = len(pd.read_csv(os.path.join(results_dir, latest)))
        st.caption(f"[Last sweep: {latest} -- {n} coins]")

    # 6 tabs, TEXT labels only, zero emojis
    tabs = st.tabs(["Single Coin", "Discovery Sweep", "Optimizer", "Validation", "Capital & Risk", "Deploy"])

    with tabs[0]:
        render_tab1_single(symbol, timeframe, signal_params, bt_params, date_range)

    with tabs[1]:
        render_tab2_sweep(symbol, timeframe, signal_params, bt_params, date_range)

    with tabs[2]:
        render_tab3_placeholder()

    with tabs[3]:
        render_tab4_placeholder()

    with tabs[4]:
        render_tab5_capital(timeframe, bt_params)

    with tabs[5]:
        render_tab6_placeholder()


if __name__ == "__main__":
    main()
