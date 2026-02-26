"""
Vince Screener v1 -- Streamlit app.
Sweeps cached coins, scores them, exports eligible list to bingx-connector.
Run: streamlit run scripts/screener_v1.py
From: C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester
"""
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd

from utils.screener_engine import (
    screen_coin,
    to_bingx_symbol,
    DEFAULT_SIGNAL_PARAMS,
    DEFAULT_BT_PARAMS,
    DEFAULT_THRESHOLDS,
)

log = logging.getLogger(__name__)

CACHE_DIR = ROOT / "data" / "cache"
CONNECTOR_DIR = ROOT.parent / "bingx-connector"
ACTIVE_COINS_PATH = CONNECTOR_DIR / "active_coins.json"

st.set_page_config(page_title="Vince Screener v1", layout="wide")
st.title("Vince Screener v1")
st.caption("Sweeps cached coins against ATR ratio, 30d PnL, volume, trade count.")

# --- Session state initialisation ---
_STATE_DEFAULTS = {
    "screener_results": None,       # JSON string of results DataFrame
    "screener_running": False,      # True while screener loop is active
    "screener_progress": 0,         # index of next coin to screen
    "screener_partial": [],         # accumulated row dicts
    "screener_symbols": [],         # symbol list for current run
    "screener_lookback": 30,        # lookback days locked at run start
    "screener_thresholds": DEFAULT_THRESHOLDS,  # thresholds locked at run start
}
for _k, _v in _STATE_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# --- Sidebar ---
st.sidebar.header("Screener Parameters")
lookback_days = st.sidebar.slider("Lookback (days)", 14, 90, 30)
min_atr = st.sidebar.number_input("Min ATR ratio", value=0.003, step=0.001, format="%.4f")
min_vol = st.sidebar.number_input(
    "Min daily vol (USD)", value=1_000_000.0, step=100_000.0, format="%.0f"
)
min_pnl = st.sidebar.number_input("Min net PnL ($)", value=0.0, step=10.0)
min_trades = st.sidebar.number_input("Min trades", value=3, step=1, min_value=1)

thresholds = {
    "min_atr_ratio": float(min_atr),
    "min_net_pnl": float(min_pnl),
    "min_avg_daily_vol_usd": float(min_vol),
    "min_trades": int(min_trades),
}

st.sidebar.header("Coin Source")
coin_source = st.sidebar.radio("Source", ["All Cache (399 coins)", "Custom list"])

custom_text = ""
if coin_source == "Custom list":
    custom_text = st.sidebar.text_area(
        "Symbols (one per line, backtester format)",
        value="RIVERUSDT\nKITEUSDT\nBERAUSDT",
        height=150,
    )


@st.cache_data
def get_all_symbols() -> list:
    """Return all symbols with a _1m.parquet file in data/cache/."""
    return sorted(
        f.stem[:-3]  # strip _1m suffix
        for f in CACHE_DIR.glob("*_1m.parquet")
    )


if coin_source == "All Cache (399 coins)":
    all_symbols = get_all_symbols()
else:
    all_symbols = [s.strip() for s in custom_text.splitlines() if s.strip()]

st.sidebar.caption("Coins to screen: " + str(len(all_symbols)))

run_btn = st.sidebar.button("Run Screener", type="primary", use_container_width=True)
clear_btn = st.sidebar.button("Clear Results", use_container_width=True)

if clear_btn:
    for k, v in _STATE_DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()

if run_btn:
    st.session_state["screener_running"] = True
    st.session_state["screener_progress"] = 0
    st.session_state["screener_partial"] = []
    st.session_state["screener_symbols"] = all_symbols
    st.session_state["screener_results"] = None
    # Lock params at run start so mid-run sidebar changes don't corrupt results
    st.session_state["screener_lookback"] = lookback_days
    st.session_state["screener_thresholds"] = dict(thresholds)
    st.rerun()


# --- Incremental screener loop (one coin per st.rerun) ---
if st.session_state["screener_running"]:
    symbols = st.session_state["screener_symbols"]
    idx = st.session_state["screener_progress"]
    total = len(symbols)
    active_lookback = st.session_state["screener_lookback"]
    active_thresholds = st.session_state["screener_thresholds"]

    progress_bar = st.progress(idx / max(total, 1))
    status_text = st.empty()

    if idx < total:
        sym = symbols[idx]
        status_text.text("Screening " + str(idx + 1) + "/" + str(total) + ": " + sym)
        row = screen_coin(
            sym, CACHE_DIR, active_lookback,
            DEFAULT_SIGNAL_PARAMS, DEFAULT_BT_PARAMS, active_thresholds,
        )
        st.session_state["screener_partial"].append(row)
        st.session_state["screener_progress"] = idx + 1
        progress_bar.progress((idx + 1) / total)
        if idx + 1 < total:
            st.rerun()
        else:
            # All coins done
            st.session_state["screener_running"] = False
            df_result = pd.DataFrame(st.session_state["screener_partial"])
            df_result = df_result.sort_values("score", ascending=False).reset_index(drop=True)
            st.session_state["screener_results"] = df_result.to_json(orient="records")
            status_text.text("Screener complete.")
            st.rerun()


# --- Results display ---
if st.session_state["screener_results"] is not None:
    df = pd.read_json(st.session_state["screener_results"], orient="records")
    eligible_df = df[df["eligible"] == True]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total screened", len(df))
    col2.metric("Eligible", len(eligible_df))
    col3.metric("Ineligible", len(df) - len(eligible_df))

    st.subheader("Results")
    display_cols = [
        "symbol", "atr_ratio", "net_pnl_30d", "avg_daily_vol_usd",
        "trade_count", "score", "pass_atr", "pass_pnl", "pass_vol",
        "pass_trades", "eligible",
    ]
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()

    df_display["avg_daily_vol_usd"] = df_display["avg_daily_vol_usd"].apply(
        lambda v: ("$" + "{:.1f}".format(v / 1_000_000) + "M") if pd.notna(v) else "N/A"
    )
    df_display["net_pnl_30d"] = df_display["net_pnl_30d"].apply(
        lambda v: ("$" + "{:,.0f}".format(v)) if pd.notna(v) else "N/A"
    )
    df_display["atr_ratio"] = df_display["atr_ratio"].apply(
        lambda v: "{:.4f}".format(v) if pd.notna(v) else "N/A"
    )

    def _highlight_eligible(row):
        """Highlight eligible rows green, ineligible rows dark red."""
        color = "#1a3a1a" if row.get("eligible") is True else "#2a1a1a"
        return ["background-color: " + color] * len(row)

    styled = df_display.style.apply(_highlight_eligible, axis=1)
    st.dataframe(styled, use_container_width=True, height=500)

    # --- Export section ---
    st.subheader("Export")
    ex1, ex2 = st.columns(2)

    with ex1:
        if st.button("Export to active_coins.json", type="primary"):
            if len(eligible_df) == 0:
                st.warning("No eligible coins to export.")
            else:
                bingx_symbols = [to_bingx_symbol(s) for s in eligible_df["symbol"].tolist()]
                try:
                    CONNECTOR_DIR.mkdir(parents=True, exist_ok=True)
                    ACTIVE_COINS_PATH.write_text(
                        json.dumps(bingx_symbols, indent=2),
                        encoding="utf-8",
                    )
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                    st.success(
                        "Exported " + str(len(bingx_symbols)) + " coins at " + ts
                        + "\n" + str(ACTIVE_COINS_PATH)
                    )
                    st.code(json.dumps(bingx_symbols, indent=2))
                except Exception as e:
                    st.error("Export failed: " + str(e))

    with ex2:
        if len(eligible_df) > 0:
            bingx_list = [to_bingx_symbol(s) for s in eligible_df["symbol"].tolist()]
            coin_text = "\n".join(bingx_list)
            st.text_area("Eligible coins (BingX format)", value=coin_text, height=200)
            st.caption("Copy above for manual config.yaml paste.")
        else:
            st.info("No eligible coins.")

elif not st.session_state["screener_running"]:
    st.info("Configure parameters in the sidebar and click Run Screener.")
