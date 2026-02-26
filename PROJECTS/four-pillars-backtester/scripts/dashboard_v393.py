r"""
Four Pillars v3.9.3 Backtest Dashboard -- Numba JIT + timing panel.
5-tab layout with ML integration.

v3.8.4 ENGINE (inherits from v3.8.3 signal pipeline):
  - ATR-based SL (sl_mult * ATR) and optional ATR-based TP (tp_mult * ATR)
  - Scale-out at AVWAP +2sigma checkpoints (replaces breakeven raise from v3.7)
  - D signal: continuation when 60-K stays pinned in extreme zone
  - AVWAP inheritance: ADD/RE slots clone parent AVWAP accumulator state
  - Multi-slot positions (up to max_positions concurrent slots)
  - Maker/taker commission model with daily rebate settlement at 17:00 UTC

SIGNAL PIPELINE (compute_signals_v383):
  compute_all_stochastics() -> 4 K values + D smooth
  compute_clouds()          -> Ripster EMA clouds 2-5 + price position + crosses
  FourPillarsStateMachine383 -> A/B/C/D entry signals + re-entry + add signals
  ATR (Wilder's RMA)        -> computed inline for SL/TP calculation

DATA FLOW:
  1. BybitFetcher.load_cached() -> 1m Parquet from data/cache/
  2. resample_5m() if 5m timeframe selected
  3. compute_signals_v383(df, signal_params) -> adds signal columns to df
  4. Backtester384(bt_params).run(df_sig) -> bar-by-bar multi-slot execution
  5. Returns: {trades_df, metrics, equity_curve, position_counts}
  6. Dashboard renders 5 tabs: Overview, Trade Analysis, MFE/MAE, ML, Validation

Run:  streamlit run scripts/dashboard.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester
"""
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.graph_objects as go

# --- Data layer: fetches and caches OHLCV from Bybit v5 API ---
from data.fetcher import BybitFetcher
from data.normalizer import OHLCVNormalizer, NormalizerError

# --- Signal pipeline: v3.8.3 stochastic state machine with D signal ---
# Inheritance chain: stochastics.py -> clouds.py -> state_machine_v383.py
# Output columns added to df:
#   long_a/b/c/d, short_a/b/c/d    -- entry signals by grade
#   reentry_long/short              -- cloud2 re-entry signals
#   add_long/short                  -- AVWAP-based add signals
#   cloud3_allows_long/short        -- directional filter (always on in v3.8+)
#   atr                             -- Wilder's RMA for SL/TP
#   stoch_9/14/40/60/60_d           -- stochastic K values + D smooth
from signals.four_pillars_v383_v2 import compute_signals_v383

# --- Backtest engine: v3.8.4 multi-slot with ATR TP + scale-out ---
# Inheritance chain: position_v384.py (PositionSlot384) + commission.py (CommissionModel)
#                    + avwap.py (AVWAPTracker)
# Per-bar execution order:
#   1. Commission settlement check (daily at 17:00 UTC)
#   2. Check exits on all slots (SL checked before TP -- pessimistic)
#   3. Update AVWAP accumulators + recalculate SL for remaining slots
#   4. Check scale-out opportunities (close at +2sigma)
#   5. Process pending limit orders (cancel expired / fill triggered)
#   6. Check stochastic entries (A > B > C > D > R priority)
#   7. Check AVWAP adds (limit orders inheriting parent AVWAP state)
#   8. Check AVWAP re-entry (limit orders inheriting exited slot's AVWAP state)
from engine.backtester_v384 import Backtester384
# --- Portfolio Enhancement v3: utils modules (2026-02-16) ---
# Phase 1: Reusable portfolio save/load
# Phase 2: Extended per-coin metrics + drill-down
# Phase 3: PDF export (requires: pip install reportlab)
# Phase 4: Unified capital model with trade rejection
from utils.portfolio_manager import (
    save_portfolio, load_portfolio, list_portfolios, delete_portfolio
)
from utils.coin_analysis import (
    compute_extended_metrics, compute_grade_distribution,
    compute_exit_distribution, compute_monthly_pnl,
    compute_loser_detail, compute_commission_breakdown,
    compute_daily_volume_stats
)
from utils.capital_model_v2 import (
    apply_capital_constraints, format_capital_summary, GRADE_PRIORITY
)
from utils.pdf_exporter_v2 import check_dependencies as check_pdf_deps, generate_portfolio_pdf
from utils.timing import TimingAccumulator, records_to_df


# --- Theme colors (dark mode) ---
COLORS = {
    "bg": "#0f1419", "card": "#1a1f26", "text": "#e7e9ea",
    "green": "#10b981", "red": "#ef4444", "blue": "#3b82f6",
    "orange": "#f59e0b", "purple": "#8b5cf6", "gray": "#6b7280",
}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
PARAM_LOG = PROJECT_ROOT / "data" / "output" / "param_log.jsonl"
SWEEP_PROGRESS = PROJECT_ROOT / "data" / "output" / "sweep_progress_v384.csv"

st.set_page_config(page_title="Four Pillars v3.8.4 Backtester", layout="wide")
st.markdown(f"""<style>
    .stApp {{ background-color: {COLORS['bg']}; }}
    h1, h2, h3 {{ color: {COLORS['text']}; }}
</style>""", unsafe_allow_html=True)

# ── Session state: mode navigation + result caching ────────────────────────
# mode: which view to render. Persists across reruns so back button works.
# *_data: cached backtest results so navigating back doesn't re-run.
if "mode" not in st.session_state:
    st.session_state["mode"] = "settings"
if "single_data" not in st.session_state:
    st.session_state["single_data"] = None
if "sweep_data" not in st.session_state:
    st.session_state["sweep_data"] = None
if "sweep_detail_symbol" not in st.session_state:
    st.session_state["sweep_detail_symbol"] = None
if "sweep_detail_data" not in st.session_state:
    st.session_state["sweep_detail_data"] = None
if "portfolio_data" not in st.session_state:
    st.session_state["portfolio_data"] = None
if "port_symbols_locked" not in st.session_state:
    st.session_state["port_symbols_locked"] = None
if "timing_records" not in st.session_state:
    st.session_state["timing_records"] = []


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data
def get_cached_symbols():
    """Return sorted list of symbols with cached data in data/cache/.
    Scans for *_1m.parquet (fetcher format) AND *_5m.parquet (normalizer uploads).
    Deduplicates so each symbol appears once regardless of intervals available."""
    symbols = set()
    for f in CACHE_DIR.glob("*.parquet"):
        stem = f.stem
        # Strip known interval suffixes to get symbol name
        for suffix in ["_1m", "_5m", "_15m", "_1h", "_4h", "_1d"]:
            if stem.endswith(suffix):
                symbols.add(stem[:-len(suffix)])
                break
    return sorted(symbols)


def resample_5m(df_1m):
    """Resample 1-minute OHLCV to 5-minute bars.

    Logic: standard OHLCV aggregation (open=first, high=max, low=min, close=last, vol=sum).
    Handles datetime as column or index. Returns df with datetime as column.
    Gracefully handles missing volume/timestamp columns (some data sources vary).
    """
    df = df_1m.copy()
    if 'datetime' not in df.columns:
        if df.index.name == 'datetime':
            df = df.reset_index()
    df = df.set_index('datetime')
    # Build aggregation dict dynamically -- only include columns that exist
    agg_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
    for col in ['base_vol', 'quote_vol', 'volume', 'turnover']:
        if col in df.columns:
            agg_dict[col] = 'sum'
    if 'timestamp' in df.columns:
        agg_dict['timestamp'] = 'first'
    ohlcv = df.resample('5min').agg(agg_dict).dropna(subset=['close'])
    return ohlcv.reset_index()


def load_data(symbol, timeframe):
    """Load cached data for a symbol at requested timeframe.

    Priority for 5m: try native {symbol}_5m.parquet first (normalizer uploads),
    then fall back to loading 1m and resampling. This avoids resampling when
    the user uploaded 5m data directly.
    Column normalization: renames volume->base_vol, turnover->quote_vol if needed,
    because backtester_v384 expects 'base_vol' for volume-weighted AVWAP calculations.
    """
    # Try native timeframe parquet first (e.g., BTCUSDT_5m.parquet)
    native_path = CACHE_DIR / f"{symbol}_{timeframe}.parquet"
    if native_path.exists():
        df = pd.read_parquet(native_path)
    else:
        # Fall back to 1m data via fetcher, then resample
        df = BybitFetcher(cache_dir=str(CACHE_DIR)).load_cached(symbol)
        if df is None:
            return None
    # Normalize column names for consistency with backtester
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    if timeframe == '5m' and not native_path.exists():
        df = resample_5m(df)
    return df


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def compute_sortino(net_pnls):
    """Compute Sortino ratio from per-trade net P&L array.

    Sortino = mean(returns) / downside_deviation.
    Downside deviation = sqrt(mean(min(returns, 0)^2)).
    Not included in Backtester384 metrics, so computed here from trades_df.
    Returns 0 if no downside trades or insufficient data.
    """
    if len(net_pnls) < 2:
        return 0.0
    mean_ret = np.mean(net_pnls)
    downside = net_pnls[net_pnls < 0]
    if len(downside) == 0:
        return 0.0
    dd = np.sqrt(np.mean(downside ** 2))
    return float(mean_ret / dd) if dd > 0 else 0.0


def log_params(symbol, timeframe, signal_params, bt_params, metrics):
    """Append run parameters and key metrics to JSONL log for tracking.

    Log location: data/output/param_log.jsonl
    v3.8.4 metrics logged: scale_out_count, tp_exits, sl_exits, total_rebate.
    v3.8.4 BE raise is ATR-based (cooperates with AVWAP trail, unlike v3.7 fixed-$ BE).
    bt_params may contain tp_mult=None which serializes to JSON null -- this is fine.
    """
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
            "profit_factor": float(metrics.get("profit_factor", 0)),
            "scale_out_count": metrics.get("scale_out_count", 0),
            "tp_exits": metrics.get("tp_exits", 0),
            "sl_exits": metrics.get("sl_exits", 0),
            "total_rebate": float(metrics.get("total_rebate", 0)),
        }
    }
    with open(PARAM_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def run_backtest(df, sig_params, run_params, accumulator=None):
    """Run full signal + backtest pipeline. Single entry point for all modes.

    Pipeline:
      df -> compute_signals_v383(sig_params) -> Backtester384(run_params).run()

    Returns: (results_dict, df_with_signals)
      results_dict keys:
        trades_df:       DataFrame with per-trade details (direction, grade, entry/exit
                         price, pnl, commission, net_pnl, mfe, mae, exit_reason,
                         saw_green, scale_idx, sl_price, tp_price)
        metrics:         dict with aggregate stats (total_trades, win_rate, expectancy,
                         net_pnl, profit_factor, sharpe, max_drawdown, max_drawdown_pct,
                         total_commission, scale_out_count, tp_exits, sl_exits, grades,
                         total_rebate, net_pnl_after_rebate, total_volume, total_sides,
                         avg_positions, max_positions_used, pct_time_flat, etc.)
        equity_curve:    numpy array of equity per bar
        position_counts: numpy array of active position count per bar
    """
    t0 = time.perf_counter()
    df_sig = compute_signals_v383(df.copy(), sig_params)
    t1 = time.perf_counter()
    bt = Backtester384(run_params)
    results = bt.run(df_sig)
    t2 = time.perf_counter()
    if accumulator is not None:
        accumulator.record("signals_ms", (t1 - t0) * 1000)
        accumulator.record("engine_ms", (t2 - t1) * 1000)
    return results, df_sig


def compute_params_hash(signal_params, bt_params, timeframe, date_range=None):
    """8-char MD5 hash of all params. Used to detect matching sweep progress.
    Same params + timeframe = same hash. Change any param = different hash."""
    payload = json.dumps({"s": signal_params, "b": bt_params, "tf": timeframe, "dr": str(date_range)}, sort_keys=True, default=str)
    return hashlib.md5(payload.encode()).hexdigest()[:8]


def apply_date_filter(df, date_range):
    """Filter DataFrame to date range. Returns original if too few bars after filter."""
    if date_range is None or len(date_range) != 2:
        return df
    start_dt, end_dt = date_range
    start_ts = pd.Timestamp(start_dt, tz="UTC")
    end_ts = pd.Timestamp(end_dt, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    if "datetime" in df.columns:
        dt_col = pd.to_datetime(df["datetime"], utc=True)
        mask = (dt_col >= start_ts) & (dt_col <= end_ts)
        df_filtered = df[mask].reset_index(drop=True)
    elif isinstance(df.index, pd.DatetimeIndex):
        df_filtered = df[start_ts:end_ts].reset_index(drop=True)
    else:
        return df
    if len(df_filtered) < 100:
        return df
    return df_filtered


def find_worst_drawdowns(equity_curve, datetimes=None, n_windows=3, min_window_bars=50):
    """Find top-N non-overlapping max drawdown windows from equity curve."""
    eq = np.array(equity_curve, dtype=float)
    n = len(eq)
    if n < min_window_bars:
        return []
    peaks = np.maximum.accumulate(eq)
    dd_pct = np.where(peaks > 0, (eq - peaks) / peaks * 100.0, 0.0)
    mask = np.ones(n, dtype=bool)
    windows = []
    for _ in range(n_windows):
        dd_masked = dd_pct.copy()
        dd_masked[~mask] = 0.0
        if dd_masked.min() >= 0:
            break
        trough_bar = int(np.argmin(dd_masked))
        peak_bar = trough_bar
        for b in range(trough_bar - 1, -1, -1):
            if eq[b] >= peaks[trough_bar]:
                peak_bar = b
                break
        if trough_bar - peak_bar < min_window_bars:
            peak_bar = max(0, trough_bar - min_window_bars)
        start_date, end_date = "", ""
        if datetimes is not None:
            try:
                start_date = str(datetimes[peak_bar])[:10]
                end_date = str(datetimes[trough_bar])[:10]
            except (IndexError, TypeError):
                pass
        windows.append({
            "start_bar": peak_bar, "end_bar": trough_bar,
            "start_date": start_date, "end_date": end_date,
            "dd_pct": round(float(dd_pct[trough_bar]), 2),
            "peak_equity": round(float(eq[peak_bar]), 2),
            "trough_equity": round(float(eq[trough_bar]), 2),
            "duration_bars": trough_bar - peak_bar,
        })
        buffer = max(10, (trough_bar - peak_bar) // 5)
        mask[max(0, peak_bar - buffer):min(n, trough_bar + buffer + 1)] = False
    return windows


def align_portfolio_equity(coin_results, margin_per_pos=500.0, max_positions=4):
    """Align multiple coin equity curves and compute portfolio metrics."""
    if not coin_results:
        return None
    master_dt = pd.DatetimeIndex([])
    for cr in coin_results:
        master_dt = master_dt.union(pd.DatetimeIndex(cr["datetime_index"]))
    master_dt = master_dt.sort_values()
    n_bars = len(master_dt)
    portfolio_eq = np.zeros(n_bars)
    total_positions = np.zeros(n_bars)
    per_coin_eq = {}
    for cr in coin_results:
        sym = cr["symbol"]
        dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        eq_series = pd.Series(cr["equity_curve"], index=dt_idx)
        _fill_val = float(eq_series.iloc[0]) if len(eq_series) > 0 else 10000.0
        eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(_fill_val).values
        per_coin_eq[sym] = eq_aligned
        portfolio_eq += eq_aligned
        pos_series = pd.Series(cr["position_counts"], index=dt_idx)
        pos_aligned = pos_series.reindex(master_dt, method="ffill").fillna(0).values
        total_positions += pos_aligned
    capital_allocated = total_positions * margin_per_pos
    peaks = np.maximum.accumulate(portfolio_eq)
    dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)
    dd_arr = np.clip(dd_arr, -100.0, 0.0)
    worst_bar = int(np.argmin(dd_arr))
    best_bar = int(np.argmax(portfolio_eq))
    def bar_info(bar_idx, label):
        """Build info dict for a specific bar (best/worst moment)."""
        dt_str = str(master_dt[bar_idx])[:19] if bar_idx < len(master_dt) else ""
        return {"label": label, "bar": bar_idx, "date": dt_str,
                "equity": round(float(portfolio_eq[bar_idx]), 2),
                "dd_pct": round(float(dd_arr[bar_idx]), 2),
                "positions": int(total_positions[bar_idx]),
                "capital": round(float(capital_allocated[bar_idx]), 2)}
    per_coin_lsg = {}
    for cr in coin_results:
        tdf = cr.get("trades_df")
        if tdf is not None and not tdf.empty:
            losers = tdf[tdf["net_pnl"] < 0]
            lsg = losers["saw_green"].sum() / len(losers) * 100.0 if len(losers) > 0 else 0.0
            per_coin_lsg[cr["symbol"]] = round(lsg, 1)
    return {"master_dt": master_dt, "portfolio_eq": portfolio_eq, "per_coin_eq": per_coin_eq,
            "total_positions": total_positions, "capital_allocated": capital_allocated,
            "best_moment": bar_info(best_bar, "Best"), "worst_moment": bar_info(worst_bar, "Worst"),
            "portfolio_dd_pct": round(float(dd_arr.min()), 2), "per_coin_lsg": per_coin_lsg}


def compute_avg_green_bars(trades_df, df_sig):
    """For losers where saw_green=True, compute avg bars they were profitable.
    Walks entry_bar -> exit_bar using df_sig close prices, counts bars where
    unrealized P&L > 0. Returns average count (float)."""
    losers = trades_df[(trades_df["net_pnl"] < 0) & (trades_df["saw_green"] == True)]
    if losers.empty:
        return 0.0
    close_vals = df_sig["close"].values if "close" in df_sig.columns else None
    if close_vals is None:
        return 0.0
    green_counts = []
    for _, t in losers.iterrows():
        eb = int(t["entry_bar"])
        xb = int(t["exit_bar"])
        ep = float(t["entry_price"])
        d = t["direction"]
        count = 0
        for bar in range(eb, min(xb + 1, len(close_vals))):
            if d == "LONG":
                unreal = close_vals[bar] - ep
            else:
                unreal = ep - close_vals[bar]
            if unreal > 0:
                count += 1
        green_counts.append(count)
    return float(np.mean(green_counts)) if green_counts else 0.0


# ============================================================================
# SIDEBAR -- All user-configurable parameters for signals and backtester
# ============================================================================

st.sidebar.title("Four Pillars v3.8.4")
cached = get_cached_symbols()
if not cached:
    st.error("No cached data.")
    st.stop()

# -- Data selection --
st.sidebar.subheader("Data")
symbol = st.sidebar.selectbox("Symbol", cached,
    index=cached.index("RIVERUSDT") if "RIVERUSDT" in cached else 0)
timeframe = st.sidebar.radio("Timeframe", ["1m", "5m"], index=1, horizontal=True)

# -- Date range filter (v3.1) --
st.sidebar.markdown("---")
st.sidebar.subheader("Date Range")
date_preset = st.sidebar.radio("Period", ["All", "7d", "30d", "90d", "1y", "Custom"],
    horizontal=True, index=0)
date_range = None
if date_preset == "Custom":
    dr_c1, dr_c2 = st.sidebar.columns(2)
    date_start = dr_c1.date_input("Start", datetime.now() - timedelta(days=90))
    date_end = dr_c2.date_input("End", datetime.now())
    date_range = (date_start, date_end)
elif date_preset != "All":
    _days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    _n_days = _days_map[date_preset]
    _de = datetime.now()
    _ds = _de - timedelta(days=_n_days)
    date_range = (_ds.date(), _de.date())
    _dr_label = _ds.strftime("%Y-%m-%d") + " to " + _de.strftime("%Y-%m-%d")
    st.sidebar.caption(_dr_label)
# -- Action buttons --
# Mode transitions via session_state. Buttons are True only on click frame,
# but mode persists across reruns so results stay visible.
st.sidebar.markdown("---")
run_single = st.sidebar.button("Run Backtest")
run_sweep = st.sidebar.button("Sweep ALL coins")
run_portfolio = st.sidebar.button("Portfolio Analysis")
batch_top = st.sidebar.slider("Top N", 5, 50, 20)
st.sidebar.markdown("---")
perf_debug = st.sidebar.checkbox("Performance Debug", value=False)

if run_single:
    st.session_state["mode"] = "single"
    st.session_state["single_data"] = None  # force fresh run with current params
if run_sweep:
    st.session_state["mode"] = "sweep"
if run_portfolio:
    st.session_state["mode"] = "portfolio"
    st.session_state["portfolio_data"] = None

# -- Stochastic K lengths (-> compute_signals_v383 -> compute_all_stochastics) --
# These control the 4-stochastic entry system (John Kurisko method).
# K1=9: entry trigger (Raw K, smooth=1). Crosses below cross_level -> zone entry.
# K2=14: confirmation. Reinforces K1 signal for B/C grade classification.
# K3=40: divergence detection. When K3 diverges from price -> stronger signal.
# K4=60: macro filter. 60-K entering extreme zone triggers entry window (v3.8.3 change).
# D smooth: SMA period applied to K4 only. D line used for 60-K zone detection.
st.sidebar.markdown("---")
st.sidebar.subheader("Stochastics (K lengths)")
sk1, sk2 = st.sidebar.columns(2)
stoch_k1 = sk1.number_input("K1 (entry)", value=9, min_value=3, max_value=100)
stoch_k2 = sk2.number_input("K2 (confirm)", value=14, min_value=3, max_value=100)
sk3, sk4 = st.sidebar.columns(2)
stoch_k3 = sk3.number_input("K3 (diverge)", value=40, min_value=3, max_value=200)
stoch_k4 = sk4.number_input("K4 (macro)", value=60, min_value=3, max_value=200)
stoch_d_smooth = st.sidebar.number_input("D smooth (SMA of K4)", value=10, min_value=1, max_value=50)

# -- Ripster EMA Clouds (-> compute_signals_v383 -> compute_clouds) --
# Cloud 2 (5/12): fast EMA cross. Price crosses above/below trigger re-entry signals.
# Cloud 3 (34/50): directional filter. ALWAYS ON in v3.8+. Long only when cloud3 bullish.
# Cloud 4 (72/89): trend confirmation. Used in staging/grade classification.
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

# -- Signal Logic (-> FourPillarsStateMachine383 via compute_signals_v383) --
# cross_level: stoch threshold for cross detection (default 25). K below this = oversold zone.
# zone_level: 60-K extreme zone threshold (default 30). v3.8.3 uses 60-K (not 9-K) for zone trigger.
# stage_lookback: bars to look back for staging confirmation (how many stochs confirmed).
# reentry_lookback: bars after exit to allow cloud2 re-entry signal.
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

# -- Exits (v3.8.4 ATR-based SL/TP) --
# SL = entry_price +/- ATR * sl_mult. Default 2.5 ATR (was 1.0 in v3.7).
#   After 5 bars, SL transitions from ATR-based to AVWAP center (tighter, data-driven).
# TP = entry_price +/- ATR * tp_mult. tp_mult=None disables TP (v3.8.3 behavior).
#   TP is checked AFTER SL each bar (pessimistic -- if both hit, SL wins).
#   Only re-entry on SL exit, NOT on TP exit.
# Cooldown = minimum bars between entries. Prevents churn (5 flips in 5 minutes).
st.sidebar.markdown("---")
st.sidebar.subheader("Exits")
cb1, cb2 = st.sidebar.columns(2)
sl_mult = cb1.slider("SL (ATR x)", 0.5, 5.0, 2.5, 0.1)
use_tp = st.sidebar.checkbox("Use TP", value=True)
if use_tp:
    # tp_mult is a float -- passed to Backtester384 which creates TP at entry +/- ATR*tp_mult
    tp_mult = cb2.slider("TP (ATR x)", 0.5, 6.0, 2.0, 0.1)
else:
    # tp_mult=None tells Backtester384 to skip TP -- identical to v3.8.3 behavior
    tp_mult = None
cooldown = st.sidebar.slider("Cooldown (bars)", 0, 20, 3)

# -- Breakeven raise (cooperates with AVWAP trail) --
# BE fires FAST on spikes (every bar), AVWAP trails the trend afterward.
# be_trigger_atr: price must move this many ATRs favorable to trigger BE raise.
# be_lock_atr: once triggered, SL moves to entry +/- this many ATRs (0 = breakeven).
# Set trigger=0 to disable. Both mechanisms cooperate -- BE locks spikes, AVWAP ratchets trend.
st.sidebar.markdown("---")
st.sidebar.subheader("Breakeven")
be1, be2 = st.sidebar.columns(2)
be_trigger_atr = be1.slider("BE trigger (ATR x)", 0.0, 3.0, 0.0, 0.1)
be_lock_atr = be2.slider("BE lock (ATR x)", 0.0, 2.0, 0.0, 0.1)
if be_trigger_atr > 0:
    st.sidebar.caption(f"When price moves {be_trigger_atr}x ATR favorable, SL -> entry +/- {be_lock_atr}x ATR")

# -- Scale-out (cooperates with BE raise) --
# checkpoint_interval: check for scale-out every N bars (default 5).
#   At each checkpoint, if close is at AVWAP +2sigma (favorable), close 50% of slot.
# max_scaleouts: max partial closes per slot (default 2 = close 50% then remaining 50%).
#   After scale-out, SL moves to AVWAP center (locks in profit without fixed $ BE).
# sigma_floor_atr: minimum AVWAP sigma as fraction of ATR (default 0.5).
#   Prevents micro-sigma SL when AVWAP std dev collapses (low-vol consolidation).
st.sidebar.markdown("---")
st.sidebar.subheader("Scale-Out")
so1, so2 = st.sidebar.columns(2)
checkpoint_interval = so1.slider("Checkpoint (bars)", 1, 20, 5)
max_scaleouts = so2.slider("Max scale-outs", 0, 5, 2)
sigma_floor_atr = st.sidebar.slider("Sigma floor (ATR x)", 0.1, 2.0, 0.5, 0.1)

# -- Position management (v3.8.4 multi-slot engine) --
# max_positions: concurrent slots (1-4). Each slot tracks its own AVWAP, SL, TP.
# enable_adds: AVWAP-based adds. When price hits -2sigma on existing slot, place limit
#   at -1sigma. Fill inherits parent's AVWAP accumulator (not fresh AVWAP).
# enable_reentry: after SL exit, clone AVWAP state and place limit order for re-entry.
#   Only triggers on SL exits (not TP). Re-entry window = reentry_window bars.
st.sidebar.markdown("---")
st.sidebar.subheader("Position")
cp1, cp2 = st.sidebar.columns(2)
margin = cp1.number_input("Margin $", value=500.0, step=50.0)
leverage = cp2.number_input("Leverage", value=20, step=1, min_value=1, max_value=125)
notional = margin * leverage
st.sidebar.caption(f"Notional: ${notional:,.0f}")
max_positions = st.sidebar.slider("Max positions", 1, 4, 4)
cp3, cp4 = st.sidebar.columns(2)
enable_adds = cp3.checkbox("AVWAP adds", value=True)
enable_reentry = cp4.checkbox("AVWAP re-entry", value=True)

# -- Commission model (rate-based, never hardcode dollar amounts) --
# commission_rate: taker rate per side on notional (0.0008 = 0.08%). Market/stop orders.
# maker_rate: maker rate per side (0.0002 = 0.02%). Limit orders (adds, re-entry fills).
# rebate_pct: % of daily commission returned at 17:00 UTC settlement.
#   70% account -> net RT cost = $4.80. 50% account -> net RT cost = $8.00.
# Cost calculation: cost_per_side = notional * rate. NEVER hardcode dollar amounts.
st.sidebar.markdown("---")
st.sidebar.subheader("Commission")
comm_pct = st.sidebar.number_input("Taker Rate %", value=0.08, step=0.01, format="%.2f")
commission_rate = comm_pct / 100.0
maker_pct = st.sidebar.number_input("Maker Rate %", value=0.02, step=0.01, format="%.2f")
maker_rate = maker_pct / 100.0
cost_side = notional * commission_rate
st.sidebar.caption(f"Per side: ${cost_side:,.2f} | RT: ${cost_side*2:,.2f}")

# -- Capital allocation mode --
# Moved to portfolio page. Default for non-portfolio modes:
total_portfolio_capital = None

rebate_pct = st.sidebar.radio("Rebate", [0.70, 0.50, 0.0],
    format_func=lambda x: f"{x:.0%}", horizontal=True)
st.sidebar.caption(f"Net RT: ${cost_side*2*(1-rebate_pct):,.2f}")

# -- ML parameters (for Tab 4 meta-label analysis) --
# These control the XGBoost binary classifier that filters trades.
# n_estimators: number of boosting rounds. Higher = more complex model.
# max_depth: tree depth. 4 is a good balance between expressiveness and overfitting.
# ml_threshold: probability cutoff for "take" vs "skip" decision.
st.sidebar.markdown("---")
st.sidebar.subheader("ML Meta-Label")
xgb_estimators = st.sidebar.number_input("XGB Estimators", value=200, step=50, min_value=50, max_value=1000)
xgb_depth = st.sidebar.slider("XGB Depth", 2, 10, 4)
ml_threshold = st.sidebar.slider("ML Threshold", 0.0, 1.0, 0.5, 0.05)



# ============================================================================
# PARAM DICTS -- Passed to signal pipeline and backtester
# ============================================================================

# signal_params -> compute_signals_v383()
# Flows through: compute_all_stochastics(df, params) -> compute_clouds(df, params)
#                -> FourPillarsStateMachine383(**params)
# Each function reads only the keys it needs; extra keys are ignored.
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

# bt_params -> Backtester384()
# Flows through: Backtester384.__init__(params) -> CommissionModel(**comm_params)
#                -> PositionSlot384(**slot_params) per entry
# tp_mult=None means no TP (v3.8.3 behavior). Float enables ATR-based TP.
# b_open_fresh appears in BOTH signal_params and bt_params because:
#   - Signal pipeline uses it to decide which B/C signals to fire
#   - Backtester uses it to gate B/C fresh entries in the execution loop
bt_params = {
    "sl_mult": sl_mult,
    "tp_mult": tp_mult,
    "cooldown": cooldown,
    "b_open_fresh": b_open_fresh,
    "notional": notional,
    "commission_rate": commission_rate,
    "maker_rate": maker_rate,
    "rebate_pct": rebate_pct,
    "initial_equity": 10000.0,
    "max_positions": max_positions,
    "checkpoint_interval": checkpoint_interval,
    "max_scaleouts": max_scaleouts,
    "sigma_floor_atr": sigma_floor_atr,
    "enable_adds": enable_adds,
    "enable_reentry": enable_reentry,
    "be_trigger_atr": be_trigger_atr,
    "be_lock_atr": be_lock_atr,
}


# ============================================================================
# MODE-BASED EXECUTION
# Replaces old if run_test / elif not run_batch / else branching.
# Each mode is mutually exclusive. Results cached in session_state.
# ============================================================================

mode = st.session_state["mode"]

# ── SETTINGS MODE ──────────────────────────────────────────────────────────
# Shows sidebar only. No computation. User configures params then clicks Run.
if mode == "settings":
    st.title("Four Pillars v3.8.4")
    st.info("Configure parameters in the sidebar, then click Run Backtest or Sweep ALL coins.")

# ── SINGLE MODE (5-tab detail for selected coin) ──────────────────────────
elif mode == "single":
    # Back button: clears cached results, returns to settings
    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.session_state["single_data"] = None
        st.rerun()
    st.title(f"4P v3.8.4 -- {symbol} {timeframe}")
    if date_range:
        st.caption(f"Date filter: {date_range[0]} to {date_range[1]}")

    # Run backtest only if no cached results (fresh run or back-then-rerun)
    if st.session_state["single_data"] is None:
        df = load_data(symbol, timeframe)
        if df is None:
            st.error(f"No data for {symbol}")
            st.stop()
        df = apply_date_filter(df, date_range)
        t0 = time.time()
        results, df_sig = run_backtest(df, signal_params, bt_params)
        m = results["metrics"]
        if m["total_trades"] == 0:
            st.warning("0 trades.")
            st.stop()
        trades_df = results["trades_df"]
        eq = results["equity_curve"]
        true_net = float(eq[-1] - 10000.0)
        exp = true_net / m["total_trades"]
        sortino = compute_sortino(trades_df["net_pnl"].values) if not trades_df.empty else 0.0
        avg_mfe = float(trades_df["mfe"].mean()) if not trades_df.empty and "mfe" in trades_df.columns else 0.0
        avg_green_bars = compute_avg_green_bars(trades_df, df_sig) if not trades_df.empty else 0.0
        # Cache TP comparison if TP enabled
        tp_comp = None
        if tp_mult is not None:
            no_tp_params = dict(bt_params, tp_mult=None)
            r_notp, _ = run_backtest(df, signal_params, no_tp_params)
            tp_comp = r_notp
        log_params(symbol, timeframe, signal_params, bt_params, m)
        st.session_state["single_data"] = {
            "results": results, "df_sig": df_sig, "metrics": m,
            "trades_df": trades_df, "eq": eq, "true_net": true_net,
            "exp": exp, "sortino": sortino, "avg_mfe": avg_mfe,
            "avg_green_bars": avg_green_bars, "tp_comp": tp_comp,
            "symbol": symbol, "df": df, "timeframe": timeframe, "elapsed": time.time() - t0,
        }

    # Load from cache
    _d = st.session_state["single_data"]
    results = _d["results"]
    df_sig = _d["df_sig"]
    m = _d["metrics"]
    trades_df = _d["trades_df"]
    eq = _d["eq"]
    true_net = _d["true_net"]
    exp = _d["exp"]
    sortino = _d["sortino"]
    avg_mfe = _d["avg_mfe"]
    avg_green_bars = _d.get("avg_green_bars", 0.0)

    # -- 5 TABS --
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Trade Analysis", "MFE/MAE & Losers", "ML Meta-Label", "Validation"
    ])

    # ── TAB 1: OVERVIEW ────────────────────────────────────────────────────
    # Key metrics in 3 rows, equity curve with peak overlay, grade breakdown,
    # exit reason aggregation, capital utilization stats, and optional TP comparison.
    with tab1:
        # Row 1: core performance metrics (same structure as v3.7 dashboard)
        r1 = st.columns(6)
        r1[0].metric("Trades", f"{m['total_trades']:,}")
        r1[1].metric("Win Rate", f"{m['win_rate']:.1%}")
        r1[2].metric("Exp $/tr", f"${exp:.2f}")
        r1[3].metric("Net P&L", f"${true_net:,.2f}", help="Profit after commissions and rebates")
        r1[4].metric("PF", f"{m['profit_factor']:.2f}")
        r1[5].metric("Max DD%", f"{m['max_drawdown_pct']:.1f}%", help="Largest peak-to-trough % drop")

        # Row 2: commission, exit management, and risk metrics
        # BE Raises and Scale-Outs cooperate: BE fires on spikes, scale-out trails trend
        r2 = st.columns(7)
        r2[0].metric("Comm $", f"${m['total_commission']:,.0f}")
        r2[1].metric("LSG", f"{m['pct_losers_saw_green']:.0%}", help="% of losers green before SL")
        r2[2].metric("BE Raises", f"{m.get('be_raised_count', 0):,}")
        r2[3].metric("Scale-Outs", f"{m.get('scale_out_count', 0):,}")
        r2[4].metric("Sharpe", f"{m['sharpe']:.3f}")
        r2[5].metric("Sortino", f"{sortino:.3f}")
        r2[6].metric("Avg MFE", f"${avg_mfe:.2f}")

        # Row 2b: LSG bars metric (avg bars losers were profitable before dying)
        if avg_green_bars > 0:
            st.caption(f"LSG Avg Green Bars: {avg_green_bars:.1f} (avg bars losers were profitable before SL)")

        # Row 3: v3.8.4 specific -- TP/SL exit counts, rebate totals, volume
        r3 = st.columns(6)
        tp_label = f"{tp_mult} ATR" if tp_mult else "off"
        r3[0].metric("TP Exits", f"{m.get('tp_exits', 0)} ({tp_label})")
        r3[1].metric("SL Exits", f"{m.get('sl_exits', 0)}")
        r3[2].metric("Rebate $", f"${m.get('total_rebate', 0):,.2f}")
        net_after_rebate = m.get("net_pnl_after_rebate", true_net)
        r3[3].metric("Net w/Rebate", f"${net_after_rebate:,.2f}")
        r3[4].metric("Volume $", f"${m.get('total_volume', 0):,.0f}")
        r3[5].metric("Sides", f"{m.get('total_sides', 0):,}")

        # Equity curve with peak overlay (drawdown = gap between lines)
        st.subheader("Equity Curve")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=df_sig["datetime"].values if "datetime" in df_sig.columns else None, y=eq, mode="lines", name="Equity",
                                     line=dict(color=COLORS["blue"], width=1.5)))
        fig_eq.add_trace(go.Scatter(x=df_sig["datetime"].values if "datetime" in df_sig.columns else None, y=np.maximum.accumulate(eq), mode="lines", name="Peak",
                                     line=dict(color=COLORS["gray"], width=0.8, dash="dot")))
        fig_eq.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                              plot_bgcolor=COLORS["card"], height=350,
                              margin=dict(l=40, r=20, t=20, b=30))
        st.plotly_chart(fig_eq, use_container_width=True)

        # Grade breakdown -- v3.8.4 includes D, ADD, RE in addition to A, B, C, R
        # Each grade has: count, win_rate, avg_pnl, total_pnl, tp_exits
        if m.get("grades"):
            st.subheader("Grades")
            gd = []
            for g in ["A", "B", "C", "D", "ADD", "RE", "R"]:
                if g in m["grades"]:
                    s = m["grades"][g]
                    gd.append({
                        "Grade": g, "Trades": s["count"],
                        "WR": round(s['win_rate'] * 100, 1),
                        "Avg": round(s['avg_pnl'], 2),
                        "Total": round(s['total_pnl'], 2),
                        "TP Exits": s.get("tp_exits", 0),
                    })
            st.dataframe(pd.DataFrame(gd).style.format({"WR": "{:.1f}%", "Avg": "${:.2f}", "Total": "${:.2f}"}), hide_index=True)

        # Exit reason aggregation -- groups by SL, TP, END, SCALE_OUT
        if not trades_df.empty:
            st.subheader("Exits")
            st.dataframe(trades_df.groupby("exit_reason").agg(
                N=("net_pnl", "count"), Avg=("net_pnl", "mean"), Sum=("net_pnl", "sum")
            ).round(2), use_container_width=True)

        # Capital utilization (v3.8.4 multi-slot tracking from position_counts array)
        st.subheader("Capital Utilization")
        cu = st.columns(5)
        cu[0].metric("Avg Positions", f"{m.get('avg_positions', 0):.1f}")
        cu[1].metric("Max Positions", f"{m.get('max_positions_used', 0)}")
        cu[2].metric("% Time Flat", f"{m.get('pct_time_flat', 0):.1%}")
        cu[3].metric("Avg Margin", f"${m.get('avg_margin_used', 0):,.0f}")
        cu[4].metric("Peak Margin", f"${m.get('peak_margin_used', 0):,.0f}")

        # ── Stress Test (v3.1) ──────────────────────────────────
        with st.expander("Stress Test (Worst Drawdowns)", expanded=False):
            n_stress = st.slider("Drawdown windows", 1, 5, 3, key="stress_n")
            dt_arr = df_sig["datetime"].values if "datetime" in df_sig.columns else None
            stress_windows = find_worst_drawdowns(eq, datetimes=dt_arr, n_windows=n_stress)
            if not stress_windows:
                st.info("No significant drawdowns detected.")
            else:
                st.dataframe(pd.DataFrame(stress_windows)[
                    ["start_date", "end_date", "dd_pct", "duration_bars", "peak_equity", "trough_equity"]
                ].round(2), use_container_width=True, hide_index=True)
                # Re-backtest on each window
                _df_raw = _d.get("df")
                if _df_raw is not None:
                    stress_rows = []
                    full_lsg = m.get("pct_losers_saw_green", 0) * 100
                    for wi, sw in enumerate(stress_windows):
                        _df_w = _df_raw.iloc[sw["start_bar"]:sw["end_bar"]+1].reset_index(drop=True)
                        if len(_df_w) < 50:
                            continue
                        try:
                            r_s, df_s = run_backtest(_df_w, signal_params, bt_params)
                            ms_s = r_s["metrics"]
                            eq_s = r_s["equity_curve"]
                            net_s = float(eq_s[-1] - 10000.0) if len(eq_s) > 0 else 0
                            lsg_s = ms_s.get("pct_losers_saw_green", 0) * 100
                            cap_s = ms_s.get("avg_margin_used", 0)
                            _wr_val = ms_s.get("win_rate", 0)
                            _wr_str = f"{_wr_val:.1%}" if ms_s["total_trades"] > 0 else "-"
                            stress_rows.append({
                                "Window": f"DD-{wi+1}",
                                "Dates": sw["start_date"] + " to " + sw["end_date"],
                                "DD%": round(sw["dd_pct"], 1),
                                "Trades": ms_s["total_trades"],
                                "WR": round(_wr_val * 100, 1) if ms_s["total_trades"] > 0 else 0,
                                "Net": round(net_s, 2),
                                "PF": round(ms_s["profit_factor"], 2),
                                "LSG%": round(lsg_s, 1),
                                "Avg Capital": round(cap_s, 0),
                            })
                        except Exception:
                            continue
                    if stress_rows:
                        st.subheader("Performance During Worst Drawdowns")
                        st.caption(f"Full-run LSG: {full_lsg:.1f}%")
                        st.dataframe(pd.DataFrame(stress_rows).style.format({"Net": "${:,.2f}", "Avg Capital": "${:,.0f}", "DD%": "{:.1f}%", "PF": "{:.2f}", "LSG%": "{:.1f}%", "WR": "{:.1f}%"}), hide_index=True)
                        # Best vs Worst capital moments
                        bc1, bc2 = st.columns(2)
                        best_idx = int(np.argmax(eq))
                        worst_idx = int(np.argmin(eq - np.maximum.accumulate(eq)))
                        best_dt = str(dt_arr[best_idx])[:10] if dt_arr is not None else ""
                        worst_dt = str(dt_arr[worst_idx])[:10] if dt_arr is not None else ""
                        best_pos = int(results["position_counts"][best_idx]) if "position_counts" in results else 0
                        worst_pos = int(results["position_counts"][worst_idx]) if "position_counts" in results else 0
                        bc1.metric("Best Equity", f"${float(eq[best_idx]):,.2f}", f"{best_dt} | {best_pos} pos")
                        bc2.metric("Worst DD Point", f"${float(eq[worst_idx]):,.2f}", f"{worst_dt} | {worst_pos} pos")

        # TP comparison: uses cached tp_comp from initial run (no re-computation)
        # Only shown when TP is enabled, so user can see the incremental impact
        tp_comp = _d.get("tp_comp")
        if tp_mult is not None and tp_comp is not None:
            st.subheader("TP Impact")
            r_notp = tp_comp
            m_notp = r_notp["metrics"]
            eq_notp = r_notp["equity_curve"]
            n_notp = float(eq_notp[-1] - 10000.0)

            st.dataframe(pd.DataFrame({
                "": ["Trades", "WR", "Net", "Exp", "DD%", "LSG", "Scale-Outs"],
                "No TP": [
                    m_notp["total_trades"], round(m_notp['win_rate'] * 100, 1), round(n_notp, 2),
                    round(n_notp/m_notp['total_trades'], 2) if m_notp["total_trades"] > 0 else "-",
                    round(m_notp['max_drawdown_pct'], 1), round(m_notp['pct_losers_saw_green'] * 100, 0),
                    m_notp.get("scale_out_count", 0),
                ],
                f"TP={tp_mult} ATR": [
                    m["total_trades"], round(m['win_rate'] * 100, 1), round(true_net, 2),
                    round(exp, 2), round(m['max_drawdown_pct'], 1),
                    round(m['pct_losers_saw_green'] * 100, 0), m.get("scale_out_count", 0),
                ],
            }), use_container_width=True, hide_index=True)

            # Overlay equity curves: red=no TP, green=with TP
            fig_tp = go.Figure()
            fig_tp.add_trace(go.Scatter(y=eq_notp, mode="lines", name="No TP",
                line=dict(color=COLORS["red"], width=1)))
            fig_tp.add_trace(go.Scatter(y=eq, mode="lines", name=f"TP={tp_mult}",
                line=dict(color=COLORS["green"], width=1)))
            fig_tp.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=30))
            st.plotly_chart(fig_tp, use_container_width=True)

    # ── TAB 2: TRADE ANALYSIS ──────────────────────────────────────────────
    # P&L distribution histogram, direction/grade breakdowns with bar charts,
    # trade duration histogram, and full scrollable trade log.
    with tab2:
        if not trades_df.empty:
            left, right = st.columns(2)
            with left:
                # P&L distribution -- histogram with zero line
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
                # Direction breakdown: LONG vs SHORT performance
                st.subheader("Direction Breakdown")
                dir_stats = trades_df.groupby("direction").agg(
                    Count=("net_pnl", "count"),
                    WinRate=("net_pnl", lambda x: (x > 0).mean()),
                    AvgPnL=("net_pnl", "mean"),
                    TotalPnL=("net_pnl", "sum"),
                ).round(3)
                st.dataframe(dir_stats)

                # Grade breakdown with colored bar chart
                # v3.8.4 grades: A (best), B, C, D (continuation), ADD, RE (AVWAP), R (re-entry)
                st.subheader("Grade Breakdown")
                grade_stats = trades_df.groupby("grade").agg(
                    Count=("net_pnl", "count"),
                    WinRate=("net_pnl", lambda x: (x > 0).mean()),
                    AvgPnL=("net_pnl", "mean"),
                    TotalPnL=("net_pnl", "sum"),
                ).round(3)
                # Color mapping for each grade
                grade_colors = {
                    "A": COLORS["green"], "B": COLORS["blue"], "C": COLORS["orange"],
                    "D": COLORS["purple"], "ADD": COLORS["gray"], "RE": COLORS["red"],
                    "R": COLORS["red"],
                }
                bar_colors = [grade_colors.get(g, COLORS["gray"]) for g in grade_stats.index]
                fig_grade = go.Figure(data=[
                    go.Bar(x=grade_stats.index, y=grade_stats["Count"], marker_color=bar_colors)
                ])
                fig_grade.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=250, margin=dict(l=40, r=20, t=20, b=40),
                    xaxis_title="Grade", yaxis_title="Trade Count")
                st.plotly_chart(fig_grade, use_container_width=True)

            # Duration histogram -- bars held from entry to exit
            if "entry_bar" in trades_df.columns and "exit_bar" in trades_df.columns:
                st.subheader("Trade Duration (bars)")
                durations = trades_df["exit_bar"] - trades_df["entry_bar"]
                fig_dur = go.Figure()
                fig_dur.add_trace(go.Histogram(x=durations, nbinsx=50,
                    marker_color=COLORS["purple"], opacity=0.7))
                fig_dur.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                    xaxis_title="Duration (bars)", yaxis_title="Count")
                st.plotly_chart(fig_dur, use_container_width=True)

            # Full trade log -- v3.8.4 columns
            # scale_idx replaces be_raised. sl_price/tp_price are new (ATR-based levels).
            st.subheader("Trades")
            log_cols = ["direction", "grade", "entry_price", "exit_price",
                "sl_price", "tp_price", "pnl", "commission", "net_pnl",
                "mfe", "mae", "exit_reason", "saw_green", "scale_idx"]
            available_cols = [c for c in log_cols if c in trades_df.columns]
            st.dataframe(trades_df[available_cols].round(4),
                use_container_width=True, height=400)

    # ── TAB 3: MFE/MAE & LOSERS ───────────────────────────────────────────
    # MFE/MAE scatter plot (green=winner, red=loser), Sweeney loser classification
    # (ml.loser_analysis), BE trigger optimization, End Trade Drawdown histogram.
    # These analyses work the same on v3.8.4 trades_df since mfe/mae columns exist.
    with tab3:
        if not trades_df.empty:
            # MFE/MAE scatter -- color by win/loss, hover shows grade + direction + P&L
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

            # Loser classification (Sweeney method from ml.loser_analysis)
            # Classes: W=winner, A=never saw green, B=saw green then lost,
            #          C=partial recovery, D=catastrophic (> 2x avg loss)
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
                        st.dataframe(summary.round(2), hide_index=True)

                with right3:
                    # BE trigger optimization -- simulates different BE trigger $ levels
                    # and shows net impact (losses saved vs winners killed)
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

                # ETD = MFE - final P&L. How much profit was given back before exit.
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
    # XGBoost meta-labeling pipeline:
    #   1. Extract market context features from df_sig at each trade's entry bar
    #   2. Label trades using triple barrier (TP=+1, SL=-1, other=0)
    #   3. Train XGBoost binary classifier (predict P(TP) for each trade)
    #   4. Show feature importance (built-in + SHAP)
    #   5. Compare filtered (ML threshold) vs unfiltered performance
    with tab4:
        if not trades_df.empty:
            try:
                from ml.features import extract_trade_features, get_feature_columns
                from ml.triple_barrier import label_trades, label_trades_by_pnl, get_label_distribution
                from ml.meta_label import MetaLabelAnalyzer
                from ml.bet_sizing import binary_sizing, get_sizing_summary

                # Feature extraction: pulls stoch values, cloud state, ATR, volume, etc.
                # from df_sig at each trade's entry_bar index
                st.subheader("Feature Extraction")
                feat_df = extract_trade_features(trades_df, df_sig)
                feature_cols = get_feature_columns()
                avail_cols = [c for c in feature_cols if c in feat_df.columns]
                st.text(f"Extracted {len(feat_df)} trades x {len(avail_cols)} features")

                # Triple barrier labels: classify each trade by exit type
                # +1 = TP hit (winner), -1 = SL hit (loser), 0 = other exit (END, scale-out)
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

                # XGBoost meta-label: binary classifier predicting P(profit after commission)
                # y_binary = 1 if net P&L > 0, 0 otherwise. Uses commission-aware labels.
                st.subheader("XGBoost Meta-Label")
                pnl_labels = label_trades_by_pnl(trades_df)
                y_binary = (pnl_labels == 1).astype(int)
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

                # Feature importance (XGBoost built-in gain-based)
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

                # SHAP global importance (requires pip install shap)
                # SHAP shows marginal contribution of each feature to predictions.
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

                # Bet sizing / filtering comparison
                # binary_sizing: if P(TP) >= ml_threshold -> take trade, else skip
                # Shows how many trades are filtered and the net P&L impact
                st.subheader("Filtered vs Unfiltered")
                proba = analyzer.predict_proba(X.values)
                sizes = binary_sizing(proba, threshold=ml_threshold)
                sizing_summary = get_sizing_summary(sizes)

                taken_mask = sizes > 0

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
                            round(all_net, 2),
                            round(trades_df['net_pnl'].mean(), 2),
                        ],
                        f"ML Filtered (>{ml_threshold:.0%})": [
                            len(taken_trades),
                            round(taken_net, 2),
                            round(taken_exp, 2),
                        ],
                    }), use_container_width=True, hide_index=True)

            except ImportError as e:
                st.warning(f"ML modules not available: {e}")
            except Exception as e:
                st.error(f"ML analysis error: {e}")

    # ── TAB 5: VALIDATION ─────────────────────────────────────────────────
    # Purged K-Fold CV: prevents look-ahead bias with embargo zone between folds.
    # Walk-Forward Efficiency: train on IS window, test on OOS window.
    #   WFE = OOS_accuracy / IS_accuracy. WFE >= 0.6 = ROBUST, < 0.3 = OVERFIT.
    #   Multiple sliding windows show consistency of ML filter performance.
    with tab5:
        if not trades_df.empty:
            try:
                from ml.purged_cv import purged_kfold_split, get_split_summary
                from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating, summarize_walk_forward
                from ml.features import extract_trade_features, get_feature_columns
                from ml.triple_barrier import label_trades_by_pnl
                from ml.meta_label import MetaLabelAnalyzer

                # Purged K-Fold CV: 5 folds with 10-bar embargo between train/test
                # Prevents leakage from correlated trades near fold boundaries
                st.subheader("Purged K-Fold CV")
                splits = purged_kfold_split(trades_df, n_splits=5, embargo_bars=10)
                split_summary = get_split_summary(splits, len(trades_df))
                st.dataframe(pd.DataFrame(split_summary).round(1), hide_index=True)

                # Walk-Forward Efficiency: anchored expanding or sliding windows
                # is_ratio=0.7 means 70% of window for training, 30% for testing
                st.subheader("Walk-Forward Efficiency")
                n_trades = len(trades_df)
                wf_windows = generate_windows(n_trades, is_ratio=0.7, min_trades_per_window=100, step_ratio=0.3)

                if len(wf_windows) > 0:
                    feat_df = extract_trade_features(trades_df, df_sig)
                    feature_cols = get_feature_columns()
                    avail_cols = [c for c in feature_cols if c in feat_df.columns]
                    pnl_labels = label_trades_by_pnl(trades_df)
                    y_binary = (pnl_labels == 1).astype(int)
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
                            # Purged CV within IS window for honest IS accuracy
                            is_trades = trades_df.iloc[is_start:is_end]
                            cv_accs = []
                            n_cv_splits = min(3, len(is_trades) // 10)
                            if n_cv_splits >= 2:
                                cv_splits = purged_kfold_split(is_trades, n_splits=n_cv_splits, embargo_bars=10)
                                for cv_train_idx, cv_test_idx in cv_splits:
                                    if len(cv_train_idx) < 10 or len(cv_test_idx) < 5:
                                        continue
                                    cv_model = MetaLabelAnalyzer(params={
                                        "n_estimators": xgb_estimators, "max_depth": xgb_depth,
                                    })
                                    cv_model.train(X_is[cv_train_idx], y_is[cv_train_idx])
                                    cv_proba = cv_model.predict_proba(X_is[cv_test_idx])
                                    cv_pred = (cv_proba >= 0.5).astype(int)
                                    cv_accs.append(float(np.mean(cv_pred == y_is[cv_test_idx])))
                                is_acc = float(np.mean(cv_accs)) if cv_accs else 0
                            else:
                                is_acc = 0

                            # Train final model on full IS, evaluate on OOS
                            model = MetaLabelAnalyzer(params={
                                "n_estimators": xgb_estimators, "max_depth": xgb_depth,
                            })
                            model.train(X_is, y_is)

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

                        # Bar chart: green if robust (>=0.6), orange if marginal, red if overfit (<0.3)
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
# SWEEP MODE -- Incremental execution with CSV persistence and auto-resume.
# Processes ONE coin per st.rerun() cycle. User can navigate away between coins.
# Progress saved to SWEEP_PROGRESS CSV after each coin. Auto-resumes from CSV.
# ============================================================================

elif mode == "sweep":
    # Back button
    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.rerun()

    st.title(f"Sweep -- {timeframe} (v3.8.4)")
    if date_range:
        st.caption(f"Date filter: {date_range[0]} to {date_range[1]}")
    tp_label = f"TP={tp_mult}" if tp_mult else "TP=off"
    st.caption(f"SL={sl_mult} {tp_label} CD={cooldown} "
               f"N=${notional:,.0f} Comm={comm_pct}% MaxPos={max_positions}")

    # ── Sweep source selector ──────────────────────────────────────────────
    sweep_source = st.radio("Sweep Source", ["All Cache", "Custom List", "Upload Data"],
                            horizontal=True, key="sweep_source_radio")

    # Determine which symbols to sweep based on source
    sweep_symbols = list(cached)  # default: all cache

    if sweep_source == "Custom List":
        list_file = st.file_uploader("Upload coin list (.txt, .csv, .json)",
                                     type=["txt", "csv", "json"], key="sweep_list_upload")
        if list_file is not None:
            raw = list_file.read().decode("utf-8-sig").strip()
            parsed_symbols = []
            if list_file.name.endswith(".json"):
                try:
                    parsed_symbols = [s.strip().upper() for s in json.loads(raw) if isinstance(s, str)]
                except json.JSONDecodeError:
                    st.error("Invalid JSON. Expected a list of strings.")
            elif list_file.name.endswith(".csv"):
                import csv as csv_mod
                reader = csv_mod.reader(raw.splitlines())
                rows = list(reader)
                if rows:
                    header = [h.strip().lower() for h in rows[0]]
                    sym_col = None
                    for i, h in enumerate(header):
                        if h in ("symbol", "pair", "coin", "ticker"):
                            sym_col = i
                            break
                    if sym_col is not None:
                        parsed_symbols = [r[sym_col].strip().upper() for r in rows[1:] if len(r) > sym_col]
                    else:
                        parsed_symbols = [r[0].strip().upper() for r in rows if r and not r[0].strip().lower() in ("symbol", "pair", "coin")]
            else:
                parsed_symbols = [line.strip().upper() for line in raw.splitlines() if line.strip()]

            if parsed_symbols:
                found = [s for s in parsed_symbols if s in cached]
                missing = [s for s in parsed_symbols if s not in cached]
                st.text(f"Found {len(found)}/{len(parsed_symbols)} symbols in cache.")
                if missing:
                    st.warning(f"Missing from cache: {', '.join(missing[:20])}")
                sweep_symbols = found
                st.session_state["sweep_custom_symbols"] = found  # persist across renders
            else:
                st.warning("No symbols parsed from uploaded file.")
                sweep_symbols = []
                st.session_state["sweep_custom_symbols"] = []
        else:
            _persisted = st.session_state.get("sweep_custom_symbols")
            if _persisted:
                sweep_symbols = _persisted
                st.info(f"Using {len(_persisted)} symbols from last upload. Re-upload to change.")
            else:
                st.info("Upload a .txt, .csv, or .json file with symbol names.")
                sweep_symbols = []

    elif sweep_source == "Upload Data":
        upload_file = st.file_uploader("Upload OHLCV CSV", type=["csv"], key="sweep_data_upload")
        if upload_file is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(upload_file.read())
                tmp_path = tmp.name

            normalizer = OHLCVNormalizer(cache_dir=str(CACHE_DIR))
            try:
                info = normalizer.detect_format(tmp_path)
                st.subheader("Detected Format")
                fc1, fc2, fc3, fc4 = st.columns(4)
                fc1.metric("Delimiter", repr(info["delimiter"]))
                fc2.metric("Interval", info["interval"] or "unknown")
                fc3.metric("Rows", f"{info['rows']:,}")
                fc4.metric("Timestamp", info["timestamp_format"] or "unknown")
                if info["date_range"]:
                    st.text(f"Date range: {info['date_range'][0]} to {info['date_range'][1]}")
                st.text(f"Column map: {info['column_map']}")
                if info["missing_fields"]:
                    st.warning(f"Missing fields: {info['missing_fields']}")
                if info["warnings"]:
                    for w in info["warnings"]:
                        st.warning(w)

                upload_symbol = st.text_input("Symbol name", value="", key="upload_symbol_input",
                                              placeholder="e.g. BTCUSDT").strip().upper()
                if st.button("Convert & Add to Sweep", key="convert_btn"):
                    if not upload_symbol:
                        st.error("Symbol name required.")
                    else:
                        try:
                            normalizer.normalize(tmp_path, upload_symbol)
                            st.success(f"Saved {upload_symbol} to cache.")
                            st.cache_data.clear()
                            sweep_symbols = [upload_symbol]
                        except NormalizerError as e:
                            st.error(f"Conversion failed: {e}")
                else:
                    sweep_symbols = []
            except NormalizerError as e:
                st.error(f"Format detection failed: {e}")
                sweep_symbols = []
        else:
            st.info("Upload a CSV file with OHLCV data.")
            sweep_symbols = []

    params_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)

    # Load existing progress from CSV (survives tab closes, reruns, crashes)
    completed_results = []
    completed_symbols = set()
    if SWEEP_PROGRESS.exists():
        try:
            prev_df = pd.read_csv(SWEEP_PROGRESS)
            if "params_hash" in prev_df.columns:
                matching = prev_df[prev_df["params_hash"] == params_hash]
                if not matching.empty:
                    completed_results = matching.drop(columns=["params_hash"]).to_dict("records")
                    completed_symbols = set(matching["Symbol"].tolist())
        except Exception:
            pass  # corrupt CSV, start fresh

    # Combine with any in-memory results from this session
    if st.session_state["sweep_data"] is not None:
        for r in st.session_state["sweep_data"]:
            if r["Symbol"] not in completed_symbols:
                completed_results.append(r)
                completed_symbols.add(r["Symbol"])

    remaining = [s for s in sweep_symbols if s not in completed_symbols]
    total = len(sweep_symbols)
    done = total - len(remaining)

    # Show progress
    if total == 0:
        st.info("No symbols selected for sweep. Choose a source above.")
        st.stop()
    progress_pct = done / max(total, 1)
    st.progress(progress_pct)

    if remaining:
        st.text(f"[{done+1}/{total}] Processing {remaining[0]}...")

        # Process NEXT ONE coin only (incremental -- non-blocking)
        sym = remaining[0]
        try:
            df = load_data(sym, timeframe)
            if df is not None and len(df) >= 200:
                df = apply_date_filter(df, date_range)
                result, df_sig_sweep = run_backtest(df, signal_params, bt_params)
                ms = result["metrics"]
                if ms["total_trades"] > 0:
                    eq_s = result["equity_curve"]
                    net_s = float(eq_s[-1] - 10000.0)
                    # Date range for this coin
                    dt_col = df_sig_sweep["datetime"] if "datetime" in df_sig_sweep.columns else df["datetime"] if "datetime" in df.columns else None
                    start_date = dt_col.iloc[0].strftime("%Y-%m-%d") if dt_col is not None else ""
                    end_date = dt_col.iloc[-1].strftime("%Y-%m-%d") if dt_col is not None else ""
                    # Compute LSG bars for sweep
                    lsg_bars = compute_avg_green_bars(result["trades_df"], df_sig_sweep) if not result["trades_df"].empty else 0.0
                    row = {
                        "Symbol": sym, "Trades": ms["total_trades"],
                        "WR%": round(ms["win_rate"]*100, 1), "Net": round(net_s, 2),
                        "Exp": round(net_s/ms["total_trades"], 2),
                        "LSG%": round(ms["pct_losers_saw_green"]*100, 1),
                        "LSG_Bars": round(lsg_bars, 1),
                        "ScaleOut": ms.get("scale_out_count", 0),
                        "TP_Exits": ms.get("tp_exits", 0),
                        "SL_Exits": ms.get("sl_exits", 0),
                        "DD%": round(ms["max_drawdown_pct"], 1),
                        "Sharpe": round(ms["sharpe"], 3),
                        "PF": round(ms["profit_factor"], 2),
                        "Rebate$": round(ms.get("total_rebate", 0), 2),
                        "Start": start_date,
                        "End": end_date,
                    }
                    completed_results.append(row)
                    completed_symbols.add(sym)
                    log_params(sym, timeframe, signal_params, bt_params, ms)

                    # Persist to CSV immediately (survives crashes)
                    row_csv = dict(row, params_hash=params_hash)
                    write_header = not SWEEP_PROGRESS.exists() or SWEEP_PROGRESS.stat().st_size == 0
                    pd.DataFrame([row_csv]).to_csv(
                        SWEEP_PROGRESS, mode="a", header=write_header, index=False)
        except Exception:
            pass

        # Store in session for display continuity
        st.session_state["sweep_data"] = completed_results

        # Display current results so far
        if completed_results:
            rdf = pd.DataFrame(completed_results).sort_values("Exp", ascending=False)
            st.dataframe(rdf, hide_index=True)

        # Rerun to process next coin (gives Streamlit a chance to handle button clicks)
        st.rerun()

    else:
        # Sweep complete
        st.text(f"Done. {len(completed_results)} coins.")
        st.session_state["sweep_data"] = completed_results

    # Display final results
    if completed_results:
        rdf = pd.DataFrame(completed_results).sort_values("Exp", ascending=False)
        prof = rdf[rdf["Net"] > 0]
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Coins", len(rdf))
        s2.metric("Profitable", f"{len(prof)} ({len(prof)/len(rdf)*100:.0f}%)" if len(rdf) > 0 else "0")
        s3.metric("Trades", f"{int(rdf['Trades'].sum()):,}")
        s4.metric("Net", f"${rdf['Net'].sum():,.2f}")
        s5.metric("Avg Exp", f"${rdf['Exp'].mean():.2f}")

        st.subheader(f"Top {batch_top}")
        st.dataframe(rdf.head(batch_top), hide_index=True)
        st.subheader("All")
        st.dataframe(rdf, hide_index=True, height=600)
        st.download_button("CSV", rdf.to_csv(index=False), "sweep_v384.csv", "text/csv")

        # Drill-down: select a coin from results to view 5-tab detail
        st.markdown("---")
        st.subheader("Drill Down")
        coin_options = rdf["Symbol"].tolist()
        selected_coin = st.selectbox("Select coin for detail view", coin_options, key="sweep_drill_select")
        if st.button("View Detail"):
            st.session_state["sweep_detail_symbol"] = selected_coin
            st.session_state["sweep_detail_data"] = None
            st.session_state["mode"] = "sweep_detail"
            st.rerun()

# ── SWEEP DETAIL MODE (5-tab for coin selected from sweep results) ─────────
elif mode == "sweep_detail":
    detail_sym = st.session_state.get("sweep_detail_symbol", "")
    if st.button("Back to Sweep"):
        st.session_state["mode"] = "sweep"
        st.session_state["sweep_detail_data"] = None
        st.rerun()

    st.title(f"4P v3.8.4 -- {detail_sym} {timeframe}")

    if st.session_state["sweep_detail_data"] is None:
        df = load_data(detail_sym, timeframe)
        if df is None:
            st.error(f"No data for {detail_sym}")
            st.stop()
        df = apply_date_filter(df, date_range)
        results, df_sig = run_backtest(df, signal_params, bt_params)
        m = results["metrics"]
        if m["total_trades"] == 0:
            st.warning("0 trades.")
            st.stop()
        trades_df = results["trades_df"]
        eq = results["equity_curve"]
        true_net = float(eq[-1] - 10000.0)
        exp = true_net / m["total_trades"]
        sortino = compute_sortino(trades_df["net_pnl"].values) if not trades_df.empty else 0.0
        avg_mfe = float(trades_df["mfe"].mean()) if not trades_df.empty and "mfe" in trades_df.columns else 0.0
        avg_green_bars = compute_avg_green_bars(trades_df, df_sig) if not trades_df.empty else 0.0
        tp_comp = None
        if tp_mult is not None:
            no_tp_params = dict(bt_params, tp_mult=None)
            r_notp, _ = run_backtest(df, signal_params, no_tp_params)
            tp_comp = r_notp
        st.session_state["sweep_detail_data"] = {
            "results": results, "df_sig": df_sig, "metrics": m,
            "trades_df": trades_df, "eq": eq, "true_net": true_net,
            "exp": exp, "sortino": sortino, "avg_mfe": avg_mfe,
            "avg_green_bars": avg_green_bars, "tp_comp": tp_comp,
            "symbol": detail_sym, "df": df, "timeframe": timeframe,
        }

    # Reuse the exact same 5-tab rendering as single mode
    # Load from sweep_detail cache and set the same local vars
    _d = st.session_state["sweep_detail_data"]
    results = _d["results"]
    df_sig = _d["df_sig"]
    m = _d["metrics"]
    trades_df = _d["trades_df"]
    eq = _d["eq"]
    true_net = _d["true_net"]
    exp = _d["exp"]
    sortino = _d["sortino"]
    avg_mfe = _d["avg_mfe"]
    avg_green_bars = _d.get("avg_green_bars", 0.0)

    # NOTE: The 5-tab rendering code below is duplicated from single mode.
    # In a future refactor, extract into a render_5tabs() function.
    # For now, the same tabs render here using the same variable names.

    if not trades_df.empty:
        _sortino = sortino
        _avg_mfe = avg_mfe
    else:
        _sortino = 0.0
        _avg_mfe = 0.0

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Trade Analysis", "MFE/MAE & Losers", "ML Meta-Label", "Validation"
    ])

    with tab1:
        r1 = st.columns(6)
        r1[0].metric("Trades", f"{m['total_trades']:,}")
        r1[1].metric("Win Rate", f"{m['win_rate']:.1%}")
        r1[2].metric("Exp $/tr", f"${exp:.2f}")
        r1[3].metric("Net P&L", f"${true_net:,.2f}", help="Profit after commissions and rebates")
        r1[4].metric("PF", f"{m['profit_factor']:.2f}")
        r1[5].metric("Max DD%", f"{m['max_drawdown_pct']:.1f}%", help="Largest peak-to-trough % drop")

        r2 = st.columns(7)
        r2[0].metric("Comm $", f"${m['total_commission']:,.0f}")
        r2[1].metric("LSG", f"{m['pct_losers_saw_green']:.0%}", help="% of losers green before SL")
        r2[2].metric("BE Raises", f"{m.get('be_raised_count', 0):,}")
        r2[3].metric("Scale-Outs", f"{m.get('scale_out_count', 0):,}")
        r2[4].metric("Sharpe", f"{m['sharpe']:.3f}")
        r2[5].metric("Sortino", f"{_sortino:.3f}")
        r2[6].metric("Avg MFE", f"${_avg_mfe:.2f}")

        if avg_green_bars > 0:
            st.caption(f"LSG Avg Green Bars: {avg_green_bars:.1f}")

        r3 = st.columns(6)
        tp_label = f"{tp_mult} ATR" if tp_mult else "off"
        r3[0].metric("TP Exits", f"{m.get('tp_exits', 0)} ({tp_label})")
        r3[1].metric("SL Exits", f"{m.get('sl_exits', 0)}")
        r3[2].metric("Rebate $", f"${m.get('total_rebate', 0):,.2f}")
        net_after_rebate = m.get("net_pnl_after_rebate", true_net)
        r3[3].metric("Net w/Rebate", f"${net_after_rebate:,.2f}")
        r3[4].metric("Volume $", f"${m.get('total_volume', 0):,.0f}")
        r3[5].metric("Sides", f"{m.get('total_sides', 0):,}")

        st.subheader("Equity Curve")
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(x=df_sig["datetime"].values if "datetime" in df_sig.columns else None, y=eq, mode="lines", name="Equity",
                                     line=dict(color=COLORS["blue"], width=1.5)))
        fig_eq.add_trace(go.Scatter(x=df_sig["datetime"].values if "datetime" in df_sig.columns else None, y=np.maximum.accumulate(eq), mode="lines", name="Peak",
                                     line=dict(color=COLORS["gray"], width=0.8, dash="dot")))
        fig_eq.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                              plot_bgcolor=COLORS["card"], height=350,
                              margin=dict(l=40, r=20, t=20, b=30))
        st.plotly_chart(fig_eq, use_container_width=True)

    with tab2:
        if not trades_df.empty:
            st.subheader("P&L Distribution")
            fig_pnl = go.Figure()
            fig_pnl.add_trace(go.Histogram(x=trades_df["net_pnl"], nbinsx=50,
                marker_color=COLORS["blue"], opacity=0.7))
            fig_pnl.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=400, margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig_pnl, use_container_width=True)

            st.subheader("Trades")
            log_cols = ["direction", "grade", "entry_price", "exit_price",
                "sl_price", "tp_price", "pnl", "commission", "net_pnl",
                "mfe", "mae", "exit_reason", "saw_green", "scale_idx"]
            available_cols = [c for c in log_cols if c in trades_df.columns]
            st.dataframe(trades_df[available_cols].round(4),
                use_container_width=True, height=400)

    with tab3:
        if not trades_df.empty:
            st.subheader("MFE / MAE Scatter")
            cols_mfe = [COLORS["green"] if p > 0 else COLORS["red"] for p in trades_df["net_pnl"]]
            fig_mfe = go.Figure()
            fig_mfe.add_trace(go.Scatter(x=trades_df["mae"], y=trades_df["mfe"], mode="markers",
                marker=dict(color=cols_mfe, size=5, opacity=0.6)))
            fig_mfe.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=400, margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig_mfe, use_container_width=True)

    with tab4:
        st.info("ML Meta-Label analysis available in single-coin mode.")

    with tab5:
        st.info("Validation analysis available in single-coin mode.")


# ── PORTFOLIO MODE (v3.1) ─────────────────────────────────────────────────
elif mode == "portfolio":
    if st.button("Back to Settings"):
        st.session_state["mode"] = "settings"
        st.session_state["portfolio_data"] = None
        st.session_state["port_symbols_locked"] = None
        st.rerun()

    st.title("Portfolio Analysis (v3.9.1)")
    if date_range:
        st.caption(f"Date filter: {date_range[0]} to {date_range[1]}")

    # Coin selection
    port_source = st.radio("Coin Selection", ["Top N", "Lowest N", "Random N", "Custom"],
        horizontal=True, key="port_source")
    port_n = st.slider("N coins", 2, 50, 10, key="port_n")

    # Load sweep results for Top/Lowest N
    sweep_csv_results = []
    if SWEEP_PROGRESS.exists():
        try:
            _sdf = pd.read_csv(SWEEP_PROGRESS)
            if not _sdf.empty and "Exp" in _sdf.columns:
                sweep_csv_results = _sdf.sort_values("Exp", ascending=False)["Symbol"].tolist()
        except Exception:
            pass

    # Check if we have a locked selection from a previous run
    _locked = st.session_state.get("port_symbols_locked")

    if port_source == "Custom":
        _default = _locked if _locked is not None else cached[:min(5, len(cached))]
        _default = [s for s in _default if s in cached]
        port_symbols = st.multiselect("Select coins", cached, default=_default)
    elif _locked is not None:
        # Reuse locked selection on reruns (prevents Random re-roll)
        port_symbols = _locked
    elif port_source == "Top N":
        if sweep_csv_results:
            port_symbols = sweep_csv_results[:port_n]
        else:
            st.warning("No sweep results found. Run a sweep first or choose another selection.")
            port_symbols = []
    elif port_source == "Lowest N":
        if sweep_csv_results:
            port_symbols = sweep_csv_results[-port_n:]
        else:
            st.warning("No sweep results found. Run a sweep first.")
            port_symbols = []
    elif port_source == "Random N":
        port_symbols = random.sample(list(cached), min(port_n, len(cached)))
    else:
        port_symbols = []

    if port_symbols:
        _syms_str = ", ".join(port_symbols[:5]) + (", ..." if len(port_symbols) > 5 else "")
        st.caption(f"Portfolio: {len(port_symbols)} coins -- {_syms_str}")


    # -- Portfolio Save/Load (Phase 1) --
    st.markdown("---")
    _pf_col1, _pf_col2 = st.columns(2)
    with _pf_col1:
        _saved_list = list_portfolios()
        if _saved_list:
            _pf_names = ["(none)"] + [p["name"] + " (" + str(p["coin_count"]) + " coins)" for p in _saved_list]
            _pf_choice = st.selectbox("Load Saved Portfolio", _pf_names, key="pf_load")
            if _pf_choice != "(none)":
                _pf_idx = _pf_names.index(_pf_choice) - 1
                _pf_file = _saved_list[_pf_idx]["file"]
                _pf_data = load_portfolio(_pf_file)
                if _pf_data is not None:
                    port_symbols = [s for s in _pf_data["coins"] if s in cached]
                    _missing = [s for s in _pf_data["coins"] if s not in cached]
                    if _missing:
                        st.warning("Missing from cache: " + ", ".join(_missing[:5]))
                    st.caption("Loaded: " + _pf_data.get("notes", ""))
        else:
            st.caption("No saved portfolios yet")

    with _pf_col2:
        _save_name = st.text_input("Save current selection as", key="pf_save_name")
        _save_notes = st.text_input("Notes (optional)", key="pf_save_notes")
        if st.button("Save Portfolio", key="pf_save_btn"):
            if _save_name and port_symbols:
                _method = port_source.lower().replace(" ", "_")
                _saved_path = save_portfolio(
                    _save_name, port_symbols,
                    selection_method=_method, notes=_save_notes
                )
                st.success("Saved: " + _save_name + " (" + str(len(port_symbols)) + " coins)")
            elif not _save_name:
                st.warning("Enter a portfolio name first")
            else:
                st.warning("Select coins first")

    # -- Delete saved portfolio --
    if _saved_list:
        with st.expander("Manage Saved Portfolios"):
            for _sp in _saved_list:
                _dc1, _dc2, _dc3 = st.columns([3, 1, 1])
                _dc1.text(_sp["name"] + " | " + str(_sp["coin_count"]) + " coins | " + _sp.get("notes", ""))
                _dc2.text(_sp.get("created", "")[:10])
                if _dc3.button("Delete", key="del_" + _sp["file"]):
                    delete_portfolio(_sp["file"])
                    st.rerun()
    st.markdown("---")

    # Capital configuration (on portfolio page, not sidebar)
    st.subheader("Capital")
    _cap_mode = st.radio("Mode", ["Per-Coin Independent", "Shared Pool"],
        horizontal=True, key="port_cap_mode",
        help="Per-Coin: each coin runs with full margin, no limit. Shared Pool: single deposit, trades draw from pool.")
    if _cap_mode == "Shared Pool":
        _cap_c1, _cap_c2 = st.columns(2)
        total_portfolio_capital = _cap_c1.number_input(
            "Total Capital ($)", min_value=1000, max_value=500000,
            value=10000, step=1000, key="port_total_cap"
        )
        _max_pos = int(total_portfolio_capital / margin) if margin > 0 else 0
        _cap_c2.metric("Max Concurrent Positions", _max_pos,
            help=f"${total_portfolio_capital:,.0f} / ${margin:,.0f} margin per trade")
    else:
        total_portfolio_capital = None
    st.markdown("---")

    _col_run, _col_reset = st.columns([3, 1])
    with _col_run:
        run_port = st.button("Run Portfolio Backtest", disabled=len(port_symbols) == 0)
    with _col_reset:
        if st.button("Reset Selection", key="port_reset"):
            st.session_state["port_symbols_locked"] = None
            st.session_state["portfolio_data"] = None
            st.rerun()

    if run_port and port_symbols:
        st.session_state["port_symbols_locked"] = port_symbols
        with st.spinner("Running portfolio backtest..."):
            coin_results = []
            _timing_acc = TimingAccumulator()
            progress = st.progress(0)
            status = st.empty()
            for ci, sym in enumerate(port_symbols):
                status.text(f"[{ci+1}/{len(port_symbols)}] {sym}...")
                progress.progress((ci + 1) / len(port_symbols))
                try:
                    _timing_acc.set_symbol(sym)
                    _t0 = time.perf_counter()
                    _df = load_data(sym, timeframe)
                    _timing_acc.record("load_ms", (time.perf_counter() - _t0) * 1000)
                    if _df is None or len(_df) < 200:
                        continue
                    _df = apply_date_filter(_df, date_range)
                    if len(_df) < 200:
                        continue
                    _timing_acc.record("bars", len(_df))
                    _r, _ds = run_backtest(_df, signal_params, bt_params, accumulator=_timing_acc)
                    if _r["metrics"]["total_trades"] == 0:
                        continue
                    dt_idx = _ds["datetime"] if "datetime" in _ds.columns else pd.RangeIndex(len(_r["equity_curve"]))
                    coin_results.append({
                        "symbol": sym,
                        "equity_curve": _r["equity_curve"],
                        "datetime_index": dt_idx,
                        "position_counts": _r["position_counts"],
                        "trades_df": _r["trades_df"],
                        "metrics": _r["metrics"],
                    })
                except Exception:
                    continue
            status.text(f"Done: {len(coin_results)}/{len(port_symbols)} coins with trades")
            st.session_state["timing_records"] = _timing_acc.records[:]

            if coin_results:
                pf = align_portfolio_equity(coin_results, margin_per_pos=margin, max_positions=max_positions)
                # Apply unified capital constraints if enabled (Phase 4)
                _cap_result = None
                if total_portfolio_capital is not None and total_portfolio_capital > 0:
                    _cap_result = apply_capital_constraints(
                        coin_results, pf, total_portfolio_capital, margin,
                        notional=notional, rebate_pct=rebate_pct
                    )
                    pf = _cap_result["adjusted_pf"]
                    coin_results = _cap_result["adjusted_coin_results"]
                _port_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)
                st.session_state["portfolio_data"] = {
                    "pf": pf, "coin_results": coin_results,
                    "capital_result": _cap_result,
                    "total_capital": total_portfolio_capital,
                    "params_hash": _port_hash,
                    "margin": margin,
                    "notional": notional,
                }

    _pd = st.session_state.get("portfolio_data")
    if _pd is not None:
        _current_hash = compute_params_hash(signal_params, bt_params, timeframe, date_range)
        _stored_hash = _pd.get("params_hash")
        _cap_changed = (total_portfolio_capital != _pd.get("total_capital"))
        _margin_changed = (margin != _pd.get("margin", margin))
        if _stored_hash and (_current_hash != _stored_hash or _cap_changed or _margin_changed):
            # BUG FIX v3.9.3: Clear stale portfolio data when settings change
            # Prevents displaying equity curves from previous date ranges
            st.session_state["portfolio_data"] = None
            _pd = None  # Update local var to trigger natural skip below
            st.info("Settings changed. Click **Run Portfolio Backtest** to generate new results.")

        if _pd is not None:  # Only proceed if cache is still valid
            pf = _pd["pf"]
            coin_results = _pd["coin_results"]
            # Use stored margin/notional from the run, not live sidebar values
            margin = _pd.get("margin", margin)
            notional = _pd.get("notional", notional)
            _eq_per_coin = 10000.0  # engine always runs at $10k/coin
            _engine_baseline = _eq_per_coin * len(coin_results)
            _total_cap_used = _pd.get("total_capital")
            if _total_cap_used is not None and _total_cap_used > 0:
                _baseline = float(_total_cap_used)
            else:
                _baseline = _engine_baseline

            # Summary metrics
            st.subheader("Portfolio Summary")
            if _total_cap_used is not None and _total_cap_used > 0:
                st.caption(f"Shared Pool: ${_baseline:,.0f} deposit | {len(coin_results)} coins | ${margin:,.0f}/trade")
            else:
                st.caption(f"Per-Coin Independent: {len(coin_results)} coins x ${_eq_per_coin:,.0f} each")
            pm1, pm2, pm3, pm4, pm5 = st.columns(5)
            # Net P&L: Mode 2 uses rebased equity, Mode 1 uses engine baseline
            if _total_cap_used is not None and _total_cap_used > 0:
                # Shared Pool: rebased_eq starts at total_capital
                _rebased = pf.get("rebased_portfolio_eq")
                if _rebased is not None:
                    port_net = float(_rebased[-1] - _total_cap_used)
                else:
                    _cap_data = _pd.get("capital_result")
                    if _cap_data is not None:
                        port_net = float(_cap_data["capital_efficiency"].get("pool_pnl", 0))
                    else:
                        port_net = float(pf["portfolio_eq"][-1] - _engine_baseline)
            else:
                port_net = float(pf["portfolio_eq"][-1] - _engine_baseline)
            pm1.metric("Coins", len(coin_results))
            pm2.metric("Net P&L", f"${port_net:,.2f}", help="Profit after commissions and rebates")
            _dd_pct = pf["portfolio_dd_pct"]
            pm3.metric("Max DD%", f"{_dd_pct:.1f}%", help="Largest peak-to-trough % drop")
            _peak_margin = float(pf["capital_allocated"].max())
            if _total_cap_used is not None and _total_cap_used > 0:
                _peak_pos = int(_peak_margin / margin) if margin > 0 else 0
                pm4.metric("Peak Margin", f"${_peak_margin:,.0f}",
                    f"{_peak_pos} positions",
                    help=f"Peak margin locked in trades. Pool: ${_total_cap_used:,.0f}")
            else:
                pm4.metric("Peak Capital", f"${_peak_margin:,.0f}", help="Max margin across all coins at once")
            _cap_data_for_trades = _pd.get("capital_result")
            _total_trades_sum = sum(cr["metrics"]["total_trades"] for cr in coin_results)
            if _cap_data_for_trades is not None:
                _rejected_trades = _cap_data_for_trades["rejected_count"]
                pm5.metric("Trades", f"{_total_trades_sum}",
                    f"{_rejected_trades} rejected",
                    help="Accepted trades (rejected = insufficient capital)")
            else:
                pm5.metric("Total Trades", _total_trades_sum, help="All trades across all coins")

            # Best vs Worst capital moments
            st.subheader("Peak Profit vs Worst Drawdown", help="Historical best/worst net P&L moments")
            bw1, bw2 = st.columns(2)
            best = pf["best_moment"]
            worst = pf["worst_moment"]
            _best_net = best["equity"] - _baseline
            _best_info = str(best["date"])[:10] + " | " + str(best["positions"]) + " pos | $" + f"{best['capital']:,.0f}" + " capital"
            bw1.metric("Peak Net Profit", f"${_best_net:+,.2f}", _best_info,
                help="Best net P&L at any point (equity - baseline).")
            _worst_dd = worst["dd_pct"]
            _worst_net = worst["equity"] - _baseline
            _worst_info = str(worst["date"])[:10] + " | " + str(worst["positions"]) + " pos | $" + f"{worst['capital']:,.0f}" + " capital"
            bw2.metric("Worst Drawdown", f"{_worst_dd:.1f}% (${_worst_net:+,.0f})", _worst_info,
                help="Largest peak-to-trough drop. Dollar amount = net P&L at that moment.")

            # LSG before/after
            # Extended per-coin metrics table (v3.9 -- 21 columns with volume/rebate)
            st.subheader("Per-Coin Performance", help="Extended metrics with drill-down per coin")
            ext_rows = []
            for cr in coin_results:
                ms_c = cr["metrics"]
                tdf = cr.get("trades_df")
                _dt_idx_c = cr.get("datetime_index")
                _bc = len(cr["equity_curve"]) if cr.get("equity_curve") is not None else None
                ext_m = compute_extended_metrics(tdf, bar_count=_bc)
                _dvs = compute_daily_volume_stats(tdf, datetime_index=_dt_idx_c, notional=notional)
                _net = round(float(cr["equity_curve"][-1] - _eq_per_coin), 2)
                _lsg = round(ms_c.get("pct_losers_saw_green", 0) * 100, 1)
                ext_rows.append({
                    "Symbol": cr["symbol"],
                    "Trades": ms_c["total_trades"],
                    "WR%": round(ms_c["win_rate"] * 100, 1),
                    "Net": _net,
                    "Volume$": round(ms_c.get("total_volume", 0), 0),
                    "Rebate$": round(ms_c.get("total_rebate", 0), 2),
                    "Reb/P%": round(ms_c.get("total_rebate", 0) / _net * 100, 1) if _net != 0 else 0.0,
                    "Tr/Day": _dvs["avg_trades_per_day"],
                    "MaxTr/D": _dvs["max_trades_day"],
                    "LSG%": _lsg,
                    "DD%": max(round(ms_c["max_drawdown_pct"], 1), -100.0),
                    "Sharpe": round(ms_c["sharpe"], 3),
                    "PF": round(ms_c["profit_factor"], 2),
                    "Avg$": ext_m["avg_trade"],
                    "Best$": ext_m["best_trade"],
                    "Worst$": ext_m["worst_trade"],
                    "SL%": ext_m["sl_pct"],
                    "TP%": ext_m["tp_pct"],
                    "MFE": round(ext_m["avg_mfe"], 4),
                    "MAE": round(ext_m["avg_mae"], 4),
                    "MaxLoss": ext_m["max_consec_loss"],
                    "Sortino": ext_m["sortino"],
                })
            ext_df = pd.DataFrame(ext_rows).sort_values("Net", ascending=False)
            st.dataframe(ext_df, hide_index=True, use_container_width=True)

            # Per-coin drill-down expanders (Phase 2)
            st.subheader("Per-Coin Drill-Down")
            _sorted_cr = sorted(coin_results,
                                key=lambda c: float(c["equity_curve"][-1] - _eq_per_coin),
                                reverse=True)
            for cr in _sorted_cr:
                _sym = cr["symbol"]
                _net_val = round(float(cr["equity_curve"][-1] - _eq_per_coin), 2)
                _label = _sym + " -- $" + f"{_net_val:,.2f}"
                with st.expander(_label):
                    _tdf = cr.get("trades_df")
                    _dt_idx = cr.get("datetime_index")
                    _dd_t1, _dd_t2, _dd_t3, _dd_t4 = st.tabs(
                        ["Trades", "Grade/Exit", "Monthly P&L", "Losers"]
                    )
                    with _dd_t1:
                        if _tdf is not None and not _tdf.empty:
                            _show_cols = ["direction", "grade", "entry_price", "exit_price",
                                          "pnl", "commission", "net_pnl", "mfe", "mae",
                                          "exit_reason", "saw_green"]
                            _avail = [c for c in _show_cols if c in _tdf.columns]
                            st.dataframe(_tdf[_avail].round(4), use_container_width=True, height=300)
                        else:
                            st.caption("No trades")
                    with _dd_t2:
                        _gc1, _gc2 = st.columns(2)
                        with _gc1:
                            st.caption("Grade Distribution")
                            _gd = compute_grade_distribution(_tdf)
                            if _gd:
                                _gd_df = pd.DataFrame(
                                    [{"Grade": k, "Count": v} for k, v in sorted(_gd.items())]
                                )
                                st.dataframe(_gd_df, hide_index=True)
                        with _gc2:
                            st.caption("Exit Reason Distribution")
                            _ed = compute_exit_distribution(_tdf)
                            if _ed:
                                _ed_df = pd.DataFrame(
                                    [{"Reason": k, "Count": v} for k, v in _ed.items()]
                                )
                                st.dataframe(_ed_df, hide_index=True)
                        _comm = compute_commission_breakdown(_tdf)
                        st.caption("Total Commission: $" + f"{_comm['total_commission']:,.2f}")
                    with _dd_t3:
                        _mpnl = compute_monthly_pnl(_tdf, datetime_index=_dt_idx)
                        if not _mpnl.empty:
                            st.dataframe(_mpnl.round(2), hide_index=True)
                        else:
                            st.caption("No monthly data available")
                    with _dd_t4:
                        _ld = compute_loser_detail(_tdf)
                        if not _ld.empty:
                            st.caption("Losers that saw green before SL:")
                            st.dataframe(_ld.round(4), use_container_width=True, height=250)
                        else:
                            st.caption("No losers with saw_green=True")


            # Portfolio equity curve (downsample to max 2000 points per trace)
            st.subheader("Portfolio Equity Curve")
            _n_pts = len(pf["master_dt"])
            _step = max(1, _n_pts // 2000)
            _dt_ds = pf["master_dt"][::_step]
            fig_port = go.Figure()
            # Per-coin thin lines
            for sym, eq_arr in pf["per_coin_eq"].items():
                # In Shared Pool mode, show P&L contribution (relative to starting equity)
                if _total_cap_used is not None and _total_cap_used > 0:
                    _display_eq = eq_arr - _eq_per_coin  # P&L only
                else:
                    _display_eq = eq_arr
                fig_port.add_trace(go.Scatter(
                    x=_dt_ds, y=_display_eq[::_step], mode="lines",
                    name=sym, line=dict(width=1), opacity=0.4))
            # Portfolio bold line -- use rebased chart equity in Shared Pool mode
            _chart_eq = pf.get("rebased_chart_eq", pf["portfolio_eq"]) if (_total_cap_used is not None and _total_cap_used > 0) else pf["portfolio_eq"]
            fig_port.add_trace(go.Scatter(
                x=_dt_ds, y=_chart_eq[::_step], mode="lines",
                name="PORTFOLIO", line=dict(width=3, color=COLORS["green"])))
            fig_port.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=500, margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig_port, use_container_width=True)

            # Capital utilization over time
            st.subheader("Capital Utilization Over Time")
            fig_cap = go.Figure()
            fig_cap.add_trace(go.Scatter(
                x=_dt_ds, y=pf["capital_allocated"][::_step], mode="lines",
                fill="tozeroy", name="Capital Allocated",
                line=dict(color=COLORS["blue"])))
            fig_cap.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                plot_bgcolor=COLORS["card"], height=300, margin=dict(l=40, r=20, t=20, b=40),
                yaxis_title="$ Capital")
            # Add capital limit line if unified mode is active
            _cap_res = st.session_state.get("portfolio_data", {}).get("capital_result")
            _tot_cap = st.session_state.get("portfolio_data", {}).get("total_capital")
            if _tot_cap is not None and _tot_cap > 0:
                fig_cap.add_trace(go.Scatter(
                    x=_dt_ds,
                    y=[_tot_cap] * len(_dt_ds),
                    mode="lines",
                    name="Capital Limit",
                    line=dict(width=2, color=COLORS["red"], dash="dash")
                ))
            # Add pool balance trace if available (Shared Pool mode)
            _pool_hist = pf.get("pool_balance_history")
            if _pool_hist is not None and _total_cap_used is not None:
                fig_cap.add_trace(go.Scatter(
                    x=_dt_ds, y=_pool_hist[::_step], mode="lines",
                    name="Pool Balance", line=dict(width=2, color=COLORS["green"])))
            st.plotly_chart(fig_cap, use_container_width=True)

            # Correlation matrix
            if len(pf["per_coin_eq"]) >= 2:
                st.subheader("Equity Change Correlation")
                changes = {}
                for sym, eq_arr in pf["per_coin_eq"].items():
                    changes[sym] = np.diff(eq_arr)
                corr_df = pd.DataFrame(changes).corr()
                st.dataframe(corr_df.round(3).style.background_gradient(cmap="RdYlGn_r", vmin=-1, vmax=1),
                    use_container_width=True)
            # -- Volume & Rebate Summary (v3.9) --
            st.markdown("---")
            st.subheader("Trading Volume & Rebates")
            if _total_cap_used is not None and _total_cap_used > 0:
                st.caption("Metrics based on accepted trades only (rejected trades excluded)")
            _total_vol = sum(cr["metrics"].get("total_volume", 0) for cr in coin_results)
            _total_reb = sum(cr["metrics"].get("total_rebate", 0) for cr in coin_results)
            _total_comm = sum(cr["metrics"].get("total_commission", 0) for cr in coin_results)
            _total_sides = sum(cr["metrics"].get("total_sides", 0) for cr in coin_results)
            _net_after_reb = sum(cr["metrics"].get("net_pnl_after_rebate", 0) for cr in coin_results)
            _v1, _v2, _v3 = st.columns(3)
            _v1.metric("Total Volume", f"${_total_vol:,.0f}")
            _v2.metric("Total Rebate", f"${_total_reb:,.2f}")
            _v3.metric("Net Commission", f"${_total_comm - _total_reb:,.2f}")
            _v4, _v5, _v6 = st.columns(3)
            _v4.metric("Total Sides", f"{_total_sides:,}")
            _v5.metric("Gross Commission", f"${_total_comm:,.2f}")
            _v6.metric("True Net P&L", f"${_net_after_reb:,.2f}")
            # Daily volume stats -- portfolio-level (all coins merged by date)
            _all_daily_trades = []
            for cr in coin_results:
                tdf = cr.get("trades_df")
                _dt_idx_c = cr.get("datetime_index")
                if tdf is None or tdf.empty or _dt_idx_c is None:
                    continue
                if "entry_bar" not in tdf.columns:
                    continue
                _di = pd.DatetimeIndex(_dt_idx_c)
                _max_bar = len(_di) - 1
                _bars = tdf["entry_bar"].clip(0, _max_bar).astype(int)
                _dates = _di[_bars].date
                for d in _dates:
                    _all_daily_trades.append(d)
            if _all_daily_trades:
                _daily_series = pd.Series(_all_daily_trades)
                _daily_counts = _daily_series.value_counts().sort_index()
                _daily_vol = _daily_counts * notional * 2
                _d1, _d2, _d3 = st.columns(3)
                _d1.metric("Avg Trades/Day", f"{_daily_counts.mean():.1f}")
                _d2.metric("Peak Trades/Day", f"{_daily_counts.max()}")
                _d3.metric("Lowest Trades/Day", f"{_daily_counts.min()}")
                _d4, _d5, _d6 = st.columns(3)
                _d4.metric("Avg Volume/Day", f"${_daily_vol.mean():,.0f}")
                _d5.metric("Peak Volume/Day", f"${_daily_vol.max():,.0f}")
                _d6.metric("Lowest Volume/Day", f"${_daily_vol.min():,.0f}")

            # -- Capital Efficiency Display (Phase 4) --
            _cap_data = _pd.get("capital_result")
            _total_cap = _pd.get("total_capital")
            if _cap_data is not None and _total_cap is not None:
                st.markdown("---")
                st.subheader("Shared Pool Capital Model")
                _eff = _cap_data["capital_efficiency"]
                _pool_pnl = _eff.get("pool_pnl", 0)
                _final_pool = _eff.get("final_pool", _eff["total_capital"])
                _ce1, _ce2, _ce3, _ce4 = st.columns(4)
                _ce1.metric("Starting Capital", f"${_eff['total_capital']:,.0f}")
                _ce2.metric("Final Pool", f"${_final_pool:,.0f}",
                            f"${_pool_pnl:+,.0f}")
                _ce3.metric("Peak Margin Used",
                            f"${_eff['peak_used']:,.0f} ({_eff['peak_pct']:.1f}%)")
                _ce4.metric("Avg Idle",
                            f"{_eff['idle_pct']:.1f}%")

                _rej1, _rej2 = st.columns(2)
                _rej1.metric("Trades Rejected",
                             f"{_eff['trades_rejected']} ({_eff['rejection_pct']:.1f}%)")
                _rej2.metric("Missed P&L",
                             f"${_eff['missed_pnl']:,.2f}")

                # Rejection log
                if _cap_data["rejection_log"]:
                    with st.expander("Rejected Trades (" + str(_cap_data["rejected_count"]) + ")"):
                        _rej_df = pd.DataFrame(_cap_data["rejection_log"])
                        st.dataframe(_rej_df, use_container_width=True, height=300)

                if _eff["peak_pct"] > 95:
                    st.warning(
                        "Peak capital usage exceeded 95%. "
                        "Consider increasing total capital to $"
                        + f"{int(_eff['peak_used'] * 1.2):,}"
                        + " or reducing position size."
                    )

            # -- Combined Trades CSV Export --
            st.markdown("---")
            st.subheader("Export All Trades")
            if st.button("Generate Combined Trades CSV", key="csv_export_btn"):
                _all_rows = []
                for cr in coin_results:
                    _tdf = cr.get("trades_df")
                    _dt_idx = cr.get("datetime_index")
                    if _tdf is None or _tdf.empty:
                        continue
                    _sym = cr["symbol"]
                    _di = pd.DatetimeIndex(_dt_idx) if _dt_idx is not None else None
                    for _, _row in _tdf.iterrows():
                        _r = _row.to_dict()
                        _r["symbol"] = _sym
                        if _di is not None:
                            _eb = int(_r.get("entry_bar", 0))
                            _xb = int(_r.get("exit_bar", 0))
                            _eb = max(0, min(_eb, len(_di) - 1))
                            _xb = max(0, min(_xb, len(_di) - 1))
                            _r["entry_datetime"] = str(_di[_eb])
                            _r["exit_datetime"] = str(_di[_xb])
                        _all_rows.append(_r)
                if _all_rows:
                    _combined = pd.DataFrame(_all_rows)
                    _col_order = ["symbol", "entry_datetime", "exit_datetime", "direction",
                                  "grade", "entry_price", "exit_price", "pnl", "commission",
                                  "net_pnl", "mfe", "mae", "exit_reason", "saw_green",
                                  "scale_idx", "entry_bar", "exit_bar"]
                    _col_order = [c for c in _col_order if c in _combined.columns]
                    _remaining = [c for c in _combined.columns if c not in _col_order]
                    _combined = _combined[_col_order + _remaining]
                    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    _fname = f"portfolio_trades_{_ts}.csv"
                    st.download_button(
                        "Download All Trades CSV",
                        data=_combined.to_csv(index=False),
                        file_name=_fname,
                        mime="text/csv",
                        key="csv_all_trades_dl"
                    )
                    st.success(str(len(_combined)) + " trades ready for download")
                else:
                    st.warning("No trades to export")

            # -- PDF Export (Phase 3) --
            st.markdown("---")
            _pdf_ok, _pdf_msg = check_pdf_deps()
            if _pdf_ok:
                _pdf_name = st.text_input("PDF Report Name", value="Portfolio", key="pdf_name")
                if st.button("Export Portfolio Report as PDF", key="pdf_export_btn"):
                    with st.spinner("Generating PDF report..."):
                        try:
                            _pdf_path = generate_portfolio_pdf(
                                pf, coin_results,
                                portfolio_name=_pdf_name,
                                total_capital=_total_cap,
                                capital_result=_cap_data
                            )
                            st.success("PDF saved: " + _pdf_path)
                            # Offer download
                            with open(_pdf_path, "rb") as _pf_file:
                                st.download_button(
                                    "Download PDF",
                                    data=_pf_file.read(),
                                    file_name=Path(_pdf_path).name,
                                    mime="application/pdf",
                                    key="pdf_download"
                                )
                        except Exception as _pdf_err:
                            st.error("PDF generation failed: " + str(_pdf_err))
            else:
                st.caption("PDF export unavailable: " + _pdf_msg)


            # -- Performance Debug Panel (v3.9.2) --
            if perf_debug:
                _trecs = st.session_state.get("timing_records", [])
                if _trecs:
                    st.markdown("---")
                    st.subheader("Performance Debug")
                    _tdf = records_to_df(_trecs)
                    if not _tdf.empty:
                        st.dataframe(_tdf, use_container_width=True)
                        for _tc in [c for c in _tdf.columns if c.endswith("_ms")]:
                            _mean = str(round(_tdf[_tc].mean(), 1))
                            _max = str(round(_tdf[_tc].max(), 1))
                            st.caption(_tc + ": mean=" + _mean + "ms  max=" + _max + "ms")
                else:
                    st.info("Run a portfolio backtest with Performance Debug enabled to see timing data.")