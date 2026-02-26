r"""
Master Build Script -- Sequential execution with error handling.

Runs all build/test steps one by one. Stops on first failure.
No-overwrite: will NOT overwrite existing files unless --force flag.
All output visible in terminal. Nothing runs in the background.

Steps:
  Pre. Dependencies -- checks Python packages, offers pip install -r requirements.txt
  1. Smoke test     -- writes+runs a hello.py to verify Python works
  2. Smoke test 2   -- writes+runs a tic-tac-toe script to verify complex output
  3. Fix features   -- patches ml/features.py column names (idempotent)
  4. Test ML        -- runs test_ml_pipeline.py (8/8 must pass)
  5. Dashboard      -- upgrades scripts/dashboard.py with 5-tab ML layout

Requires: Python 3.10+ (tested on 3.13), requirements.txt in project root

Run:  python scripts/master_build.py
From: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester

Flags:
  --force     Overwrite existing files (default: skip if exists)
  --dry-run   Show what would happen without writing files
  --skip-to N Skip to step N (1-5)
  --auto      Unattended mode: skip confirmation prompts, auto-resume from build log
"""

import sys
import subprocess
import time
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
ML_DIR = ROOT / "ml"
OUTPUT_DIR = ROOT / "data" / "output" / "ml"

# Track results
RESULTS = []


def banner(step, total, title):
    print(f"\n{'=' * 70}")
    print(f"  STEP {step}/{total}: {title}")
    print(f"{'=' * 70}")


def pass_step(step, msg):
    RESULTS.append(("PASS", step, msg))
    print(f"\n  >> PASS: {msg}")


def fail_step(step, msg):
    RESULTS.append(("FAIL", step, msg))
    print(f"\n  >> FAIL: {msg}")


def skip_step(step, msg):
    RESULTS.append(("SKIP", step, msg))
    print(f"\n  >> SKIP: {msg}")


def safe_write(filepath: Path, content: str, force: bool, dry_run: bool) -> bool:
    """Write file with no-overwrite protection. Returns True if written."""
    if filepath.exists() and not force:
        print(f"  File exists: {filepath.name}")
        print(f"  Use --force to overwrite. Skipping write.")
        return False
    if dry_run:
        print(f"  [DRY RUN] Would write: {filepath.name} ({len(content):,} bytes)")
        return False
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    print(f"  WROTE: {filepath.name} ({len(content):,} bytes)")
    return True


# Required packages: (import_name, pip_name, required_for)
DEPENDENCIES = [
    ("numpy", "numpy", "core"),
    ("pandas", "pandas", "core"),
    ("pyarrow", "pyarrow", "parquet files"),
    ("requests", "requests", "data fetching"),
    ("xgboost", "xgboost", "ML meta-label"),
    ("shap", "shap", "SHAP explanations"),
    ("streamlit", "streamlit", "dashboard"),
    ("plotly", "plotly", "dashboard charts"),
    ("psycopg2", "psycopg2-binary", "PostgreSQL"),
    ("dotenv", "python-dotenv", "env config"),
]


def check_dependencies():
    """Check all required Python packages. Returns (installed, missing) lists."""
    installed = []
    missing = []
    for import_name, pip_name, purpose in DEPENDENCIES:
        try:
            __import__(import_name)
            installed.append((import_name, pip_name, purpose))
        except ImportError:
            missing.append((import_name, pip_name, purpose))
    return installed, missing


def install_from_requirements():
    """Run pip install -r requirements.txt. Returns True if successful."""
    req_file = ROOT / "requirements.txt"
    if not req_file.exists():
        print(f"  ERROR: requirements.txt not found at {req_file}")
        return False
    print(f"\n  Installing from requirements.txt...")
    print(f"  Command: {sys.executable} -m pip install -r requirements.txt")
    print(f"  {'-' * 60}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            cwd=str(ROOT),
            timeout=600,
        )
        print(f"  {'-' * 60}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  {'-' * 60}")
        print(f"  TIMEOUT after 600s")
        return False
    except Exception as e:
        print(f"  {'-' * 60}")
        print(f"  ERROR: {e}")
        return False


def run_script(script_path: Path, description: str) -> int:
    """Run a Python script with full output visible. Returns exit code."""
    print(f"  Running: python {script_path.name}")
    print(f"  {'-' * 60}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(ROOT),
            timeout=300,
        )
        print(f"  {'-' * 60}")
        print(f"  Exit code: {result.returncode}")
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"  {'-' * 60}")
        print(f"  TIMEOUT after 300s")
        return -1
    except Exception as e:
        print(f"  {'-' * 60}")
        print(f"  ERROR: {e}")
        return -1


# ========================================================================
# STEP 1: Hello World smoke test
# ========================================================================
HELLO_PY = '''\
"""Smoke test: verify Python runs scripts correctly."""
import sys
print("Hello from master_build smoke test")
print(f"Python: {sys.version}")
print(f"CWD: {__import__('os').getcwd()}")
print("STATUS: OK")
sys.exit(0)
'''


# ========================================================================
# STEP 2: Tic-Tac-Toe smoke test (complex output)
# ========================================================================
TICTACTOE_PY = '''\
"""Smoke test 2: verify complex output rendering."""
import sys

def print_board(board):
    for i in range(3):
        row = " | ".join(board[i*3:(i+1)*3])
        print(f"  {row}")
        if i < 2:
            print("  ---------")

def check_winner(board, player):
    wins = [
        [0,1,2], [3,4,5], [6,7,8],
        [0,3,6], [1,4,7], [2,5,8],
        [0,4,8], [2,4,6],
    ]
    for w in wins:
        if all(board[i] == player for i in w):
            return True
    return False

# Play a deterministic game
board = [" "] * 9
moves_x = [4, 0, 8, 2]  # X moves (center, corners)
moves_o = [1, 3, 5]      # O moves (edges)

print("Tic-Tac-Toe Smoke Test")
print("======================")

for turn in range(7):
    if turn % 2 == 0:
        pos = moves_x[turn // 2]
        board[pos] = "X"
    else:
        pos = moves_o[turn // 2]
        board[pos] = "O"

    print(f"\\nTurn {turn + 1}: {'X' if turn % 2 == 0 else 'O'} -> position {pos}")
    print_board(board)

    if check_winner(board, "X"):
        print("\\nX wins!")
        break
    if check_winner(board, "O"):
        print("\\nO wins!")
        break

print("\\nSTATUS: OK")
sys.exit(0)
'''


# ========================================================================
# STEP 5: Dashboard upgrade content
# ========================================================================
DASHBOARD_ML_PY = '''r"""
Four Pillars Backtest Dashboard -- Streamlit GUI (ML Edition)
ALL parameters adjustable from sidebar. Backtest runs on change.
ML learns from your parameter adjustments via param_log.jsonl.
5-Tab layout: Overview | Trade Analysis | MFE/MAE & Losers | ML Meta-Label | Validation

Run: streamlit run scripts/dashboard.py
From: C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester
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
        f.write(json.dumps(entry) + '\\n')


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
st.sidebar.subheader("ML Analysis")
xgb_estimators = st.sidebar.number_input("XGB Estimators", value=200, min_value=50, max_value=1000, step=50)
xgb_depth = st.sidebar.number_input("XGB Depth", value=4, min_value=2, max_value=10)
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

xgb_params = {
    "n_estimators": xgb_estimators, "max_depth": xgb_depth,
    "learning_rate": 0.05, "subsample": 0.8,
    "colsample_bytree": 0.8, "verbosity": 0,
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
# SINGLE BACKTEST (full 5-tab view)
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

    # KPI row (always visible above tabs)
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

    # ====================================================================
    # 5-TAB LAYOUT
    # ====================================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Trade Analysis", "MFE/MAE & Losers",
        "ML Meta-Label", "Validation"
    ])

    # ================================================================
    # TAB 1: OVERVIEW
    # ================================================================
    with tab1:
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

    # ================================================================
    # TAB 2: TRADE ANALYSIS
    # ================================================================
    with tab2:
        if not trades_df.empty:
            # P&L histogram + direction split
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
                    N=("net_pnl", "count"),
                    WR=("net_pnl", lambda x: (x > 0).mean()),
                    Avg=("net_pnl", "mean"),
                    Total=("net_pnl", "sum"),
                ).round(2)
                dir_stats["WR"] = dir_stats["WR"].apply(lambda x: f"{x:.1%}")
                st.dataframe(dir_stats, use_container_width=True)

                # Grade bar chart
                if "grade" in trades_df.columns:
                    grade_counts = trades_df["grade"].value_counts().sort_index()
                    fig_grade = go.Figure()
                    fig_grade.add_trace(go.Bar(
                        x=grade_counts.index, y=grade_counts.values,
                        marker_color=[COLORS["green"], COLORS["blue"], COLORS["orange"], COLORS["gray"]][:len(grade_counts)],
                    ))
                    fig_grade.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=300,
                        xaxis_title="Grade", yaxis_title="Count",
                        margin=dict(l=40, r=20, t=20, b=40))
                    st.plotly_chart(fig_grade, use_container_width=True)

            # Duration histogram
            if "entry_bar" in trades_df.columns and "exit_bar" in trades_df.columns:
                st.subheader("Trade Duration (bars)")
                durations = trades_df["exit_bar"] - trades_df["entry_bar"]
                fig_dur = go.Figure()
                fig_dur.add_trace(go.Histogram(x=durations, nbinsx=40,
                    marker_color=COLORS["purple"], opacity=0.7))
                fig_dur.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=300,
                    xaxis_title="Bars", yaxis_title="Count",
                    margin=dict(l=40, r=20, t=20, b=40))
                st.plotly_chart(fig_dur, use_container_width=True)

            # Trade log
            st.subheader("Trade Log")
            st.dataframe(trades_df[["direction", "grade", "entry_price", "exit_price",
                "pnl", "commission", "net_pnl", "mfe", "mae", "exit_reason",
                "saw_green", "be_raised"]].round(4),
                use_container_width=True, height=400)

    # ================================================================
    # TAB 3: MFE/MAE & LOSERS
    # ================================================================
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

            # Loser analysis
            try:
                from ml.loser_analysis import classify_losers, get_class_summary, optimize_be_trigger, compute_etd

                classified = classify_losers(trades_df)
                class_summary = get_class_summary(classified)

                left3, right3 = st.columns(2)
                with left3:
                    st.subheader("Loser Classes (Sweeney)")
                    if not class_summary.empty:
                        class_colors = {"W": COLORS["green"], "A": COLORS["blue"],
                                        "B": COLORS["orange"], "C": COLORS["purple"], "D": COLORS["red"]}
                        fig_cls = go.Figure()
                        fig_cls.add_trace(go.Bar(
                            x=class_summary["class"], y=class_summary["count"],
                            marker_color=[class_colors.get(c, COLORS["gray"]) for c in class_summary["class"]],
                            text=class_summary["pct"].apply(lambda x: f"{x:.1f}%"),
                            textposition="auto",
                        ))
                        fig_cls.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                            plot_bgcolor=COLORS["card"], height=350,
                            xaxis_title="Class", yaxis_title="Trades",
                            margin=dict(l=40, r=20, t=20, b=40))
                        st.plotly_chart(fig_cls, use_container_width=True)
                        st.dataframe(class_summary.round(2), use_container_width=True, hide_index=True)

                with right3:
                    st.subheader("ETD Distribution")
                    etd_df = compute_etd(trades_df)
                    fig_etd = go.Figure()
                    fig_etd.add_trace(go.Histogram(x=etd_df["etd"], nbinsx=40,
                        marker_color=COLORS["orange"], opacity=0.7))
                    fig_etd.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=350,
                        xaxis_title="ETD ($)", yaxis_title="Count",
                        margin=dict(l=40, r=20, t=20, b=40))
                    st.plotly_chart(fig_etd, use_container_width=True)
                    st.caption(f"Avg ETD: ${etd_df['etd'].mean():.2f} | "
                               f"Avg ETD Ratio: {etd_df['etd_ratio'].mean():.2f}")

                # BE optimization
                st.subheader("BE Trigger Optimization (Sweeney)")
                be_opt = optimize_be_trigger(trades_df)
                if not be_opt.empty:
                    best_row = be_opt.loc[be_opt["net_impact"].idxmax()]
                    fig_be = go.Figure()
                    fig_be.add_trace(go.Scatter(x=be_opt["trigger"], y=be_opt["net_impact"],
                        mode="lines", name="Net Impact", line=dict(color=COLORS["green"], width=2)))
                    fig_be.add_trace(go.Scatter(x=be_opt["trigger"], y=be_opt["saved_value"],
                        mode="lines", name="Losers Saved $", line=dict(color=COLORS["blue"], width=1, dash="dot")))
                    fig_be.add_trace(go.Scatter(x=be_opt["trigger"], y=-be_opt["killed_value"],
                        mode="lines", name="Winners Killed $", line=dict(color=COLORS["red"], width=1, dash="dot")))
                    fig_be.add_vline(x=best_row["trigger"], line_dash="dash", line_color=COLORS["orange"])
                    fig_be.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=350,
                        xaxis_title="BE Trigger ($)", yaxis_title="$ Impact",
                        margin=dict(l=40, r=20, t=20, b=40))
                    st.plotly_chart(fig_be, use_container_width=True)
                    st.caption(f"Optimal trigger: ${best_row['trigger']:.2f} | "
                               f"Net impact: ${best_row['net_impact']:.2f} | "
                               f"Saves {int(best_row['losers_saved'])} losers, "
                               f"kills {int(best_row['winners_killed'])} winners")

            except ImportError as e:
                st.warning(f"ml.loser_analysis not available: {e}")
            except Exception as e:
                st.error(f"Loser analysis error: {e}")

    # ================================================================
    # TAB 4: ML META-LABEL
    # ================================================================
    with tab4:
        if trades_df.empty or m["total_trades"] < 30:
            st.warning("Need 30+ trades for ML analysis.")
        else:
            try:
                from ml.features import extract_trade_features, get_feature_columns
                from ml.triple_barrier import label_trades, get_label_distribution
                from ml.meta_label import MetaLabelAnalyzer
                from ml.bet_sizing import binary_sizing, get_sizing_summary

                # Feature extraction
                with st.spinner("Extracting features..."):
                    feats = extract_trade_features(trades_df, df_sig)
                    feat_cols = get_feature_columns()
                    available_cols = [c for c in feat_cols if c in feats.columns]
                    X = feats[available_cols].copy()

                # Labels
                labels = label_trades(trades_df)
                dist = get_label_distribution(labels)
                binary_y = (labels == 1).astype(int)

                left4, right4 = st.columns(2)
                with left4:
                    st.subheader("Label Distribution")
                    fig_lab = go.Figure()
                    fig_lab.add_trace(go.Bar(
                        x=["TP (+1)", "SL (-1)", "Other (0)"],
                        y=[dist["tp_count"], dist["sl_count"], dist["other_count"]],
                        marker_color=[COLORS["green"], COLORS["red"], COLORS["gray"]],
                    ))
                    fig_lab.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=300,
                        margin=dict(l=40, r=20, t=20, b=40))
                    st.plotly_chart(fig_lab, use_container_width=True)

                with right4:
                    st.subheader("Features")
                    st.text(f"Trades: {len(feats)}")
                    st.text(f"Features: {len(available_cols)}")
                    st.text(f"Columns: {', '.join(available_cols)}")

                # Train XGBoost
                with st.spinner("Training XGBoost..."):
                    analyzer = MetaLabelAnalyzer(xgb_params)
                    train_result = analyzer.train(X, binary_y, feature_names=available_cols)

                st.subheader("XGBoost Meta-Label")
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Train Accuracy", f"{train_result['train_accuracy']:.3f}")
                mc2.metric("Samples", f"{train_result['train_samples']}")
                mc3.metric("Positive Rate", f"{train_result['positive_rate']:.3f}")
                mc4.metric("Dropped NaN", f"{train_result['dropped_nan']}")

                # Feature importance
                imp = analyzer.get_feature_importance()
                st.subheader("Feature Importance")
                fig_imp = go.Figure()
                fig_imp.add_trace(go.Bar(
                    x=imp["importance"], y=imp["feature"], orientation="h",
                    marker_color=COLORS["blue"],
                ))
                fig_imp.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                    plot_bgcolor=COLORS["card"], height=max(300, len(imp) * 25),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=120, r=20, t=20, b=40))
                st.plotly_chart(fig_imp, use_container_width=True)

                # SHAP (optional)
                try:
                    from ml.shap_analyzer import ShapAnalyzer
                    with st.spinner("Computing SHAP values..."):
                        shap_a = ShapAnalyzer(analyzer.model, feature_names=available_cols)
                        shap_vals = shap_a.compute(X)
                        glob_imp = shap_a.get_global_importance()

                    st.subheader("SHAP Global Importance")
                    fig_shap = go.Figure()
                    fig_shap.add_trace(go.Bar(
                        x=glob_imp["mean_abs_shap"], y=glob_imp["feature"], orientation="h",
                        marker_color=COLORS["purple"],
                    ))
                    fig_shap.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                        plot_bgcolor=COLORS["card"], height=max(300, len(glob_imp) * 25),
                        yaxis=dict(autorange="reversed"),
                        margin=dict(l=120, r=20, t=20, b=40))
                    st.plotly_chart(fig_shap, use_container_width=True)
                except ImportError:
                    st.info("Install shap for SHAP explanations: pip install shap")

                # Bet sizing / filtering
                st.subheader("ML Filter Results")
                probs = analyzer.predict_proba(X)
                sizes = binary_sizing(probs, threshold=ml_threshold)
                sizing = get_sizing_summary(sizes)

                fc1, fc2, fc3, fc4 = st.columns(4)
                fc1.metric("Total Signals", f"{sizing['total_signals']}")
                fc2.metric("Taken", f"{sizing['taken']}")
                fc3.metric("Skipped", f"{sizing['skipped']}")
                fc4.metric("Skip Rate", f"{sizing['skip_rate']:.1%}")

                # Filtered vs unfiltered comparison
                mask = sizes > 0
                if mask.sum() > 0:
                    ft = trades_df.iloc[:len(mask)][mask]
                    filt_net = (ft["pnl"] - ft["commission"]).sum()
                    filt_exp = (ft["pnl"] - ft["commission"]).mean()
                    st.dataframe(pd.DataFrame({
                        "": ["Trades", "Net P&L", "Exp $/tr"],
                        "Unfiltered": [m["total_trades"], f"${true_net:,.2f}", f"${exp:.2f}"],
                        f"ML Filtered (t={ml_threshold})": [
                            int(mask.sum()), f"${filt_net:,.2f}", f"${filt_exp:.2f}"],
                    }), use_container_width=True, hide_index=True)

            except ImportError as e:
                st.warning(f"ML modules not available: {e}")
                st.info("Run: python scripts/build_ml_pipeline.py")
            except Exception as e:
                st.error(f"ML analysis error: {e}")

    # ================================================================
    # TAB 5: VALIDATION
    # ================================================================
    with tab5:
        if trades_df.empty or m["total_trades"] < 50:
            st.warning("Need 50+ trades for validation.")
        else:
            try:
                from ml.purged_cv import purged_kfold_split, get_split_summary
                from ml.walk_forward import generate_windows, summarize_walk_forward
                from ml.meta_label import MetaLabelAnalyzer as WF_Analyzer
                from ml.features import extract_trade_features, get_feature_columns
                from ml.triple_barrier import label_trades as wf_label_trades

                # Re-extract features for validation (standalone from Tab 4)
                with st.spinner("Preparing validation data..."):
                    v_feats = extract_trade_features(trades_df, df_sig)
                    v_feat_cols = get_feature_columns()
                    v_available = [c for c in v_feat_cols if c in v_feats.columns]
                    v_X = v_feats[v_available].copy()
                    v_labels = wf_label_trades(trades_df)
                    v_binary_y = (v_labels == 1).astype(int)

                # Purged CV
                st.subheader("Purged K-Fold CV (De Prado Ch 7)")
                n_splits = min(5, len(trades_df) // 20)
                if n_splits >= 2:
                    splits = purged_kfold_split(trades_df, n_splits=n_splits, embargo_bars=10)
                    split_summary = get_split_summary(splits, len(trades_df))
                    st.dataframe(pd.DataFrame(split_summary).round(1),
                                 use_container_width=True, hide_index=True)

                    # Train per fold, show accuracy
                    fold_results = []
                    for fold_idx, (train_idx, test_idx) in enumerate(splits):
                        try:
                            train_X = v_X.iloc[train_idx]
                            train_y = v_binary_y[train_idx]
                            test_X = v_X.iloc[test_idx]
                            test_y = v_binary_y[test_idx]
                            if len(train_X) < 20 or len(test_X) < 5:
                                continue
                            fold_model = WF_Analyzer(xgb_params)
                            fold_model.train(train_X, train_y, feature_names=v_available)
                            preds = fold_model.model.predict(test_X.values)
                            acc = float(np.mean(preds == test_y))
                            fold_results.append({
                                "Fold": fold_idx + 1,
                                "Train": len(train_idx),
                                "Test": len(test_idx),
                                "Test Accuracy": f"{acc:.3f}",
                            })
                        except Exception:
                            continue

                    if fold_results:
                        st.dataframe(pd.DataFrame(fold_results),
                                     use_container_width=True, hide_index=True)
                else:
                    st.info(f"Need 40+ trades for purged CV (have {len(trades_df)})")

                # Walk-Forward
                st.subheader("Walk-Forward Validation")
                if len(v_X) >= 200:
                    windows = generate_windows(len(v_X), is_ratio=0.7, min_trades_per_window=50)
                    wf_results = []
                    for w_idx, w in enumerate(windows[:10]):
                        try:
                            is_X = v_X.iloc[w["is_start"]:w["is_end"]]
                            is_y = v_binary_y[w["is_start"]:w["is_end"]]
                            oos_X = v_X.iloc[w["oos_start"]:w["oos_end"]]
                            oos_y = v_binary_y[w["oos_start"]:w["oos_end"]]
                            if len(is_X) < 20 or len(oos_X) < 5:
                                continue
                            wf_model = WF_Analyzer(xgb_params)
                            wf_model.train(is_X, is_y, feature_names=v_available)
                            is_acc = float(np.mean(wf_model.model.predict(is_X.values) == is_y))
                            oos_acc = float(np.mean(wf_model.model.predict(oos_X.values) == oos_y))
                            wf_results.append({
                                "is_metric": is_acc,
                                "oos_metric": oos_acc,
                            })
                        except Exception:
                            continue

                    if wf_results:
                        wf_summary = summarize_walk_forward(wf_results)

                        vc1, vc2, vc3, vc4 = st.columns(4)
                        vc1.metric("Windows", f"{wf_summary['n_windows']}")
                        vc2.metric("Avg WFE", f"{wf_summary['avg_wfe']:.3f}")
                        vc3.metric("Min WFE", f"{wf_summary['min_wfe']:.3f}")
                        vc4.metric("Rating", wf_summary["rating"])

                        # WFE per window bar chart
                        fig_wfe = go.Figure()
                        wfe_colors = []
                        for w in wf_summary["wfes"]:
                            if w >= 0.6:
                                wfe_colors.append(COLORS["green"])
                            elif w >= 0.3:
                                wfe_colors.append(COLORS["orange"])
                            else:
                                wfe_colors.append(COLORS["red"])
                        fig_wfe.add_trace(go.Bar(
                            x=list(range(1, len(wf_summary["wfes"]) + 1)),
                            y=wf_summary["wfes"],
                            marker_color=wfe_colors,
                        ))
                        fig_wfe.add_hline(y=0.6, line_dash="dash", line_color=COLORS["green"],
                                          annotation_text="ROBUST")
                        fig_wfe.add_hline(y=0.3, line_dash="dash", line_color=COLORS["orange"],
                                          annotation_text="MARGINAL")
                        fig_wfe.update_layout(template="plotly_dark", paper_bgcolor=COLORS["bg"],
                            plot_bgcolor=COLORS["card"], height=350,
                            xaxis_title="Window", yaxis_title="WFE",
                            margin=dict(l=40, r=20, t=20, b=40))
                        st.plotly_chart(fig_wfe, use_container_width=True)

                        # IS vs OOS table
                        wf_table = []
                        for i, wr in enumerate(wf_results):
                            from ml.walk_forward import compute_wfe, get_wfe_rating
                            w = compute_wfe(wr["is_metric"], wr["oos_metric"])
                            wf_table.append({
                                "Window": i + 1,
                                "IS Acc": f"{wr['is_metric']:.3f}",
                                "OOS Acc": f"{wr['oos_metric']:.3f}",
                                "WFE": f"{w:.3f}",
                                "Rating": get_wfe_rating(w),
                            })
                        st.dataframe(pd.DataFrame(wf_table),
                                     use_container_width=True, hide_index=True)
                    else:
                        st.info("Walk-forward training failed for all windows.")
                else:
                    st.info(f"Need 200+ trades for walk-forward (have {len(v_X)})")

            except ImportError as e:
                st.warning(f"Validation modules not available: {e}")
                st.info("Run: python scripts/build_ml_pipeline.py")
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
'''


# ========================================================================
# MAIN
# ========================================================================
def main():
    parser = argparse.ArgumentParser(description="Master build script -- sequential execution")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--skip-to", type=int, default=0, help="Skip to step N (1-5)")
    parser.add_argument("--auto", action="store_true", help="Unattended mode: no prompts, auto-resume")
    args = parser.parse_args()

    # Auto-resume: read build_log.txt to find last completed step
    if args.auto and args.skip_to == 0:
        log_path = SCRIPTS / "build_log.txt"
        if log_path.exists():
            log_content = log_path.read_text(encoding="utf-8")
            # Find highest step that PASSed in the LAST build entry
            last_build_start = log_content.rfind("BUILD v")
            if last_build_start >= 0:
                last_block = log_content[last_build_start:]
                import re
                passed_steps = re.findall(r"Step (\d+): \[PASS\]", last_block)
                if passed_steps:
                    last_passed = max(int(s) for s in passed_steps)
                    if last_passed >= 5:
                        print(f"  [AUTO-RESUME] All 5 steps already passed in previous build.")
                        print(f"  Nothing to do. Use --skip-to 1 --force to re-run everything.")
                        sys.exit(0)
                    args.skip_to = last_passed + 1
                    print(f"  [AUTO-RESUME] Build log found. Last passed: Step {last_passed}. Resuming at Step {args.skip_to}.")
                else:
                    # Last build had no passes -- check for failures
                    failed_steps = re.findall(r"Step (\d+): \[FAIL\]", last_block)
                    if failed_steps:
                        first_fail = min(int(s) for s in failed_steps)
                        args.skip_to = first_fail
                        print(f"  [AUTO-RESUME] Last build failed at Step {first_fail}. Retrying from Step {first_fail}.")
                    else:
                        args.skip_to = 1
            else:
                args.skip_to = 1
        else:
            args.skip_to = 1
    elif args.skip_to == 0:
        args.skip_to = 1

    total_steps = 5
    t_start = time.time()

    print("=" * 70)
    print("  MASTER BUILD SCRIPT -- Four Pillars ML Dashboard")
    print("=" * 70)
    print()
    print("  This script will run the following steps IN ORDER:")
    print("    Pre:    Check Python dependencies (offer to pip install if missing)")
    print("    Step 1: Smoke test -- write+run hello.py (verify Python works)")
    print("    Step 2: Smoke test -- write+run tic-tac-toe (verify complex output)")
    print("    Step 3: Fix ML features -- patch column names in ml/features.py")
    print("    Step 4: Test ML pipeline -- run test_ml_pipeline.py (8/8 must pass)")
    print("    Step 5: Upgrade dashboard -- replace dashboard.py with 5-tab ML version")
    print()
    print(f"  Project root:    {ROOT}")
    print(f"  Force overwrite: {args.force}")
    print(f"  Dry run:         {args.dry_run}")
    print(f"  Starting at:     Step {args.skip_to}")
    print()
    print("  SAFETY:")
    print("    - Existing files will NOT be overwritten (unless --force)")
    print("    - dashboard.py gets versioned backup (dashboard_v1.py, v2, ...) before upgrade")
    print("    - No files are deleted -- all temp/smoke files persist")
    print("    - Build log saved to scripts/build_log.txt with timestamps")
    print("    - Stops on first failure -- no partial builds")
    print("    - All output visible in terminal -- nothing hidden")
    print()

    if not args.dry_run and not args.auto:
        confirm = input("  Proceed? [y/N]: ").strip().lower()
        if confirm != "y":
            print("  Aborted by user.")
            sys.exit(0)
    elif args.auto:
        print("  [AUTO] Skipping confirmation -- unattended mode")

    # Permissions check (write a test file, leave it -- no deletions)
    print(f"\n  Checking write permissions...")
    for d in [SCRIPTS, ML_DIR, OUTPUT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        test_file = d / "__write_test__"
        try:
            test_file.write_text("write_ok")
        except PermissionError:
            print(f"  ERROR: No write permission to {d}")
            sys.exit(1)
    print(f"  All directories writable.")

    # Dependency check
    print(f"\n  Checking Python dependencies...")
    print(f"  Python: {sys.version}")
    installed, missing = check_dependencies()
    for imp, pip, purpose in installed:
        print(f"    {imp:>12} -- OK ({purpose})")
    if missing:
        print(f"\n  MISSING {len(missing)} package(s):")
        for imp, pip, purpose in missing:
            print(f"    {imp:>12} -- MISSING (pip install {pip}) [{purpose}]")
        print()
        if args.auto:
            do_install = "y"
            print("  [AUTO] Installing missing packages automatically")
        else:
            do_install = input("  Run 'pip install -r requirements.txt' now? [y/N]: ").strip().lower()
        if do_install == "y":
            success = install_from_requirements()
            if not success:
                print("  ERROR: pip install failed. Install manually and re-run:")
                print(f"  {sys.executable} -m pip install -r requirements.txt")
                sys.exit(1)
            # Re-check
            _, still_missing = check_dependencies()
            if still_missing:
                print(f"  ERROR: Still missing after install: {[m[1] for m in still_missing]}")
                sys.exit(1)
            print("  All packages installed successfully.")
        else:
            print("  Continuing without installing. Steps requiring missing packages may fail.")
    else:
        print(f"  All {len(installed)} packages present.")

    # ==================================================================
    # STEP 1: Hello World smoke test
    # ==================================================================
    if args.skip_to <= 1:
        banner(1, total_steps, "Smoke Test (hello.py)")
        hello_path = SCRIPTS / "_smoke_hello.py"
        written = safe_write(hello_path, HELLO_PY, args.force, args.dry_run)
        if not args.dry_run:
            if not hello_path.exists():
                fail_step(1, "hello.py not written and does not exist")
                print("\n  STOPPING: Step 1 failed.")
                _print_summary(t_start)
                sys.exit(1)
            code = run_script(hello_path, "Hello smoke test")
            if code != 0:
                fail_step(1, f"hello.py exited with code {code}")
                print("\n  STOPPING: Step 1 failed.")
                _print_summary(t_start)
                sys.exit(1)
            pass_step(1, "Python environment OK")
            print(f"  Smoke test persisted: {hello_path.name}")
        else:
            skip_step(1, "Dry run")

    # ==================================================================
    # STEP 2: Tic-Tac-Toe smoke test
    # ==================================================================
    if args.skip_to <= 2:
        banner(2, total_steps, "Smoke Test (tic-tac-toe)")
        ttt_path = SCRIPTS / "_smoke_tictactoe.py"
        written = safe_write(ttt_path, TICTACTOE_PY, args.force, args.dry_run)
        if not args.dry_run:
            if not ttt_path.exists():
                fail_step(2, "tictactoe.py not written and does not exist")
                print("\n  STOPPING: Step 2 failed.")
                _print_summary(t_start)
                sys.exit(1)
            code = run_script(ttt_path, "Tic-tac-toe smoke test")
            if code != 0:
                fail_step(2, f"tictactoe.py exited with code {code}")
                print("\n  STOPPING: Step 2 failed.")
                _print_summary(t_start)
                sys.exit(1)
            pass_step(2, "Complex output rendering OK")
            print(f"  Smoke test persisted: {ttt_path.name}")
        else:
            skip_step(2, "Dry run")

    # ==================================================================
    # STEP 3: Fix ML features column names
    # ==================================================================
    if args.skip_to <= 3:
        banner(3, total_steps, "Fix ML Features (column names)")
        fix_script = SCRIPTS / "fix_ml_features.py"
        if not fix_script.exists():
            skip_step(3, "fix_ml_features.py not found (already applied or not needed)")
        elif args.dry_run:
            skip_step(3, "Dry run")
        else:
            code = run_script(fix_script, "Fix column names in ml/features.py")
            if code != 0:
                fail_step(3, f"fix_ml_features.py exited with code {code}")
                print("\n  STOPPING: Step 3 failed.")
                _print_summary(t_start)
                sys.exit(1)
            pass_step(3, "ml/features.py column names fixed")

    # ==================================================================
    # STEP 4: Test ML pipeline
    # ==================================================================
    if args.skip_to <= 4:
        banner(4, total_steps, "Test ML Pipeline (8 modules)")
        test_script = SCRIPTS / "test_ml_pipeline.py"
        if not test_script.exists():
            fail_step(4, "test_ml_pipeline.py not found")
            print("\n  STOPPING: Step 4 failed.")
            _print_summary(t_start)
            sys.exit(1)
        elif args.dry_run:
            skip_step(4, "Dry run")
        else:
            code = run_script(test_script, "Test all 8 ML modules")
            if code != 0:
                fail_step(4, f"test_ml_pipeline.py exited with code {code}")
                print("\n  STOPPING: Step 4 failed. ML pipeline has errors.")
                _print_summary(t_start)
                sys.exit(1)
            pass_step(4, "All 8 ML modules pass")

    # ==================================================================
    # STEP 5: Upgrade dashboard with ML tabs
    # ==================================================================
    if args.skip_to <= 5:
        banner(5, total_steps, "Upgrade Dashboard (5-tab ML layout)")
        dashboard_path = SCRIPTS / "dashboard.py"

        if dashboard_path.exists():
            # Versioned backup: dashboard_v1.py, dashboard_v2.py, etc.
            import shutil
            v = 1
            while (SCRIPTS / f"dashboard_v{v}.py").exists():
                v += 1
            backup_path = SCRIPTS / f"dashboard_v{v}.py"
            shutil.copy2(dashboard_path, backup_path)
            print(f"  Backed up: dashboard.py -> dashboard_v{v}.py")

        written = safe_write(dashboard_path, DASHBOARD_ML_PY, force=True, dry_run=args.dry_run)
        if not args.dry_run:
            if written:
                pass_step(5, f"dashboard.py upgraded ({len(DASHBOARD_ML_PY):,} bytes)")
            else:
                fail_step(5, "dashboard.py not written")
                _print_summary(t_start)
                sys.exit(1)
        else:
            skip_step(5, "Dry run")

    _print_summary(t_start)


def _print_summary(t_start):
    from datetime import datetime
    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"  MASTER BUILD SUMMARY ({elapsed:.1f}s)")
    print(f"{'=' * 70}")
    for status, step, msg in RESULTS:
        print(f"  Step {step}: [{status}] {msg}")
    passed = sum(1 for s, _, _ in RESULTS if s == "PASS")
    failed = sum(1 for s, _, _ in RESULTS if s == "FAIL")
    skipped = sum(1 for s, _, _ in RESULTS if s == "SKIP")
    print(f"\n  Passed: {passed}  Failed: {failed}  Skipped: {skipped}")
    if failed == 0:
        print(f"\n  ALL STEPS PASSED")
        print(f"\n  Run the dashboard:")
        print(f'  cd "{ROOT}"; streamlit run scripts/dashboard.py')
    else:
        print(f"\n  ERRORS FOUND -- fix and re-run")
    print(f"{'=' * 70}")

    # Persist build log (append mode -- never overwrites)
    log_path = SCRIPTS / "build_log.txt"
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Determine build version from existing log entries
        build_v = 1
        if log_path.exists():
            existing = log_path.read_text(encoding="utf-8")
            build_v = existing.count("BUILD v") + 1
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 50}\n")
            f.write(f"BUILD v{build_v} -- {now}\n")
            f.write(f"Python: {sys.version.split()[0]}\n")
            f.write(f"Elapsed: {elapsed:.1f}s\n")
            for status, step, msg in RESULTS:
                f.write(f"  Step {step}: [{status}] {msg}\n")
            f.write(f"Result: {passed} passed, {failed} failed, {skipped} skipped\n")
        print(f"\n  Build log: {log_path.name} (BUILD v{build_v})")
    except Exception as e:
        print(f"\n  WARNING: Could not write build log: {e}")


if __name__ == "__main__":
    main()
