"""
BingX Live Dashboard v1

3 tabs: Positions | History | Coin Summary
Data sources: state.json, trades.csv, config.yaml
Mark prices: BingX public REST endpoint (no auth required)

Run:
    streamlit run "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\bingx-connector\\bingx-live-dashboard-v1.py"

Dependencies:
    pip install streamlit pandas pyyaml requests
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
STATE_PATH = BASE_DIR / "state.json"
TRADES_PATH = BASE_DIR / "trades.csv"
CONFIG_PATH = BASE_DIR / "config.yaml"

BINGX_PRICE_URL = "https://open-api.bingx.com/openApi/swap/v2/quote/price"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_state():
    """Load state.json. Returns dict with safe defaults if file is missing."""
    defaults = {
        "open_positions": {},
        "daily_pnl": 0.0,
        "daily_trades": 0,
        "halt_flag": False,
        "session_start": "",
    }
    if not STATE_PATH.exists():
        return defaults
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**defaults, **data}
    except (json.JSONDecodeError, OSError):
        return defaults


def load_config():
    """Load config.yaml. Returns dict or empty dict if file is missing."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError):
        return {}


def load_trades():
    """Load trades.csv. Returns DataFrame sorted newest first, or empty DataFrame."""
    if not TRADES_PATH.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(TRADES_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["entry_time"] = pd.to_datetime(df["entry_time"], utc=True, errors="coerce")
        df["pnl_net"] = pd.to_numeric(df["pnl_net"], errors="coerce")
        df["entry_price"] = pd.to_numeric(df["entry_price"], errors="coerce")
        df["exit_price"] = pd.to_numeric(df["exit_price"], errors="coerce")
        return df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Mark price fetch
# ---------------------------------------------------------------------------


def fetch_mark_price(symbol):
    """Fetch BingX mark price for one symbol. Returns float or None."""
    try:
        resp = requests.get(BINGX_PRICE_URL, params={"symbol": symbol}, timeout=5)
        data = resp.json().get("data", {})
        if isinstance(data, dict):
            val = float(data.get("price", 0))
            return val if val > 0 else None
        if isinstance(data, list) and data:
            val = float(data[0].get("price", 0))
            return val if val > 0 else None
    except Exception:
        pass
    return None


def fetch_all_mark_prices(symbols):
    """Fetch mark prices for a list of symbols. Returns dict symbol -> float."""
    prices = {}
    for sym in symbols:
        p = fetch_mark_price(sym)
        if p is not None:
            prices[sym] = p
    return prices


# ---------------------------------------------------------------------------
# Duration helper
# ---------------------------------------------------------------------------


def fmt_duration(start_dt, end_dt=None):
    """Format duration between two datetimes as '2h 15m' or '45m'."""
    if end_dt is None:
        end_dt = datetime.now(timezone.utc)
    if start_dt is None or pd.isna(start_dt):
        return "—"
    try:
        total_sec = int((end_dt - start_dt).total_seconds())
        if total_sec < 0:
            return "—"
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        return f"{h}h {m}m" if h > 0 else f"{m}m"
    except Exception:
        return "—"


# ---------------------------------------------------------------------------
# Build positions DataFrame
# ---------------------------------------------------------------------------


def build_positions_df(state, mark_prices):
    """Build display DataFrame for open positions from state dict and mark prices."""
    rows = []
    now = datetime.now(timezone.utc)
    for pos in state.get("open_positions", {}).values():
        sym = pos.get("symbol", "")
        direction = pos.get("direction", "")
        entry = pos.get("entry_price") or 0.0
        qty = pos.get("quantity") or 0.0
        mark = mark_prices.get(sym)

        if mark and qty and entry:
            sign = 1 if direction == "LONG" else -1
            unreal_pnl = round((mark - entry) * qty * sign, 4)
        else:
            unreal_pnl = None

        try:
            entry_dt_str = pos.get("entry_time", "")
            entry_dt = datetime.fromisoformat(entry_dt_str.replace("Z", "+00:00"))
        except Exception:
            entry_dt = None

        tp_raw = pos.get("tp_price")
        tp_display = round(float(tp_raw), 6) if tp_raw else "—"
        sl_raw = pos.get("sl_price") or 0.0

        rows.append({
            "Symbol": sym,
            "Dir": direction,
            "Grade": pos.get("grade", ""),
            "Entry": round(float(entry), 6),
            "Stop Loss": round(float(sl_raw), 6),
            "Take Profit": tp_display,
            "BE Raised": "Yes" if pos.get("be_raised") else "No",
            "Unreal PnL": unreal_pnl,
            "Duration": fmt_duration(entry_dt, now),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------


def color_pnl_col(val):
    """Return green/red CSS for PnL values."""
    try:
        v = float(val)
        if v > 0:
            return "color: #22c55e; font-weight: bold"
        if v < 0:
            return "color: #ef4444; font-weight: bold"
    except (TypeError, ValueError):
        pass
    return ""


def style_positions(df):
    """Apply direction-based row background and PnL coloring to positions df."""

    def row_bg(row):
        """Return background color list based on trade direction."""
        if row.get("Dir") == "LONG":
            bg = "background-color: rgba(34,197,94,0.08)"
        elif row.get("Dir") == "SHORT":
            bg = "background-color: rgba(239,68,68,0.08)"
        else:
            bg = ""
        return [bg] * len(row)

    styled = df.style.apply(row_bg, axis=1)
    if "Unreal PnL" in df.columns:
        styled = styled.map(color_pnl_col, subset=["Unreal PnL"])
    return styled


def style_history(df):
    """Apply PnL coloring to history dataframe."""
    if "Net PnL" in df.columns:
        return df.style.map(color_pnl_col, subset=["Net PnL"])
    return df.style


def style_summary(df):
    """Apply PnL coloring to coin summary dataframe."""
    if "Net PnL" in df.columns:
        return df.style.map(color_pnl_col, subset=["Net PnL"])
    return df.style


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

st.set_page_config(page_title="BingX Live v1", layout="wide")

# --- Header ---
col_title, col_refresh = st.columns([8, 1])
with col_title:
    st.title("BingX Live Dashboard v1")
with col_refresh:
    st.write("")
    if st.button("Refresh"):
        st.cache_data.clear()
        st.rerun()

# --- Load data ---
state = load_state()
cfg = load_config()
trades_df = load_trades()

# --- Config limits ---
risk_cfg = cfg.get("risk", {})
max_positions = risk_cfg.get("max_positions", 8)
max_daily_trades = risk_cfg.get("max_daily_trades", 50)
daily_loss_limit = risk_cfg.get("daily_loss_limit_usd", 15.0)

# --- Status bar ---
demo_mode = cfg.get("connector", {}).get("demo_mode", True)
halt_flag = state.get("halt_flag", False)
daily_pnl = float(state.get("daily_pnl", 0.0))
daily_trades_count = int(state.get("daily_trades", 0))
open_count = len(state.get("open_positions", {}))

if halt_flag:
    status_label = "HALTED"
    status_color = "red"
elif demo_mode:
    status_label = "DEMO"
    status_color = "blue"
else:
    status_label = "LIVE"
    status_color = "green"

risk_pct = (abs(daily_pnl) / daily_loss_limit * 100) if daily_loss_limit > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Status", status_label)
with c2:
    st.metric("Daily PnL", f"${daily_pnl:.2f}", delta=f"{daily_pnl:+.2f}")
with c3:
    st.metric("Open Positions", f"{open_count} / {max_positions}")
with c4:
    st.metric("Daily Trades", f"{daily_trades_count} / {max_daily_trades}")
with c5:
    st.metric("Risk Used", f"{risk_pct:.0f}% of ${daily_loss_limit:.0f}")

st.caption(
    "Last loaded: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    + "  |  Click Refresh to update data."
)
st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_pos, tab_hist, tab_summary = st.tabs(["Positions", "History", "Coin Summary"])

# ---------------------------------------------------------------------------
# Tab 1 — Positions
# ---------------------------------------------------------------------------

with tab_pos:
    st.subheader("Open Positions (" + str(open_count) + ")")

    positions = state.get("open_positions", {})
    if not positions:
        st.info("No open positions.")
    else:
        symbols = [p.get("symbol", "") for p in positions.values() if p.get("symbol")]

        with st.spinner("Fetching mark prices..."):
            mark_prices = fetch_all_mark_prices(symbols)

        pos_df = build_positions_df(state, mark_prices)

        if pos_df.empty:
            st.info("No position data to display.")
        else:
            st.dataframe(
                style_positions(pos_df),
                use_container_width=True,
                hide_index=True,
            )

        if mark_prices:
            st.caption("Mark prices fetched: " + str(len(mark_prices)) + " symbols")
        else:
            st.warning("Could not fetch mark prices. Unrealized PnL unavailable.")

# ---------------------------------------------------------------------------
# Tab 2 — History
# ---------------------------------------------------------------------------

with tab_hist:
    st.subheader("Closed Trades")

    if trades_df.empty:
        st.info("No closed trades in trades.csv.")
    else:
        today_only = st.checkbox("Today only", value=True, key="hist_today")

        df = trades_df.copy()
        if today_only:
            today_date = datetime.now(timezone.utc).date()
            df = df[df["timestamp"].dt.date == today_date].copy()

        if df.empty:
            st.info("No trades for today. Uncheck 'Today only' to see full history.")
        else:
            df["Duration"] = df.apply(
                lambda row: fmt_duration(row["entry_time"], row["timestamp"]), axis=1
            )
            df["Date/Time"] = df["timestamp"].dt.strftime("%m-%d %H:%M")

            display_df = df[[
                "Date/Time", "symbol", "direction", "grade",
                "entry_price", "exit_price", "exit_reason", "pnl_net", "Duration",
            ]].rename(columns={
                "symbol": "Symbol",
                "direction": "Dir",
                "grade": "Grade",
                "entry_price": "Entry",
                "exit_price": "Exit",
                "exit_reason": "Exit Reason",
                "pnl_net": "Net PnL",
            })

            st.dataframe(
                style_history(display_df),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(str(len(display_df)) + " trades shown")

# ---------------------------------------------------------------------------
# Tab 3 — Coin Summary
# ---------------------------------------------------------------------------

with tab_summary:
    st.subheader("Coin Summary")

    if trades_df.empty:
        st.info("No trade data available.")
    else:
        rows = []
        for sym, grp in trades_df.groupby("symbol"):
            total = len(grp)
            wins = int((grp["pnl_net"] > 0).sum())
            losses = int((grp["pnl_net"] <= 0).sum())
            wr = round(wins / total * 100, 1) if total > 0 else 0.0
            net = round(float(grp["pnl_net"].sum()), 4)
            avg = round(float(grp["pnl_net"].mean()), 4)
            sl_pct = round(
                (grp["exit_reason"] == "SL_HIT").sum() / total * 100, 1
            )
            tp_pct = round(
                (grp["exit_reason"] == "TP_HIT").sum() / total * 100, 1
            )
            unk_pct = round(
                grp["exit_reason"].isin(["EXIT_UNKNOWN", "SL_HIT_ASSUMED"]).sum()
                / total * 100,
                1,
            )
            best = round(float(grp["pnl_net"].max()), 4)
            worst = round(float(grp["pnl_net"].min()), 4)

            rows.append({
                "Symbol": sym,
                "Trades": total,
                "Wins": wins,
                "Losses": losses,
                "WR %": wr,
                "Net PnL": net,
                "Avg PnL": avg,
                "SL %": sl_pct,
                "TP %": tp_pct,
                "Unknown %": unk_pct,
                "Best": best,
                "Worst": worst,
            })

        summary_df = (
            pd.DataFrame(rows)
            .sort_values("Net PnL", ascending=False)
            .reset_index(drop=True)
        )

        st.dataframe(
            style_summary(summary_df),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(str(len(summary_df)) + " coins in history")
