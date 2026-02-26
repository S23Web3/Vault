"""
Streamlit parameter input form.
Returns a dict of all configurable parameters for backtesting.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


DEFAULT_PARAMS = {
    "timeframe": "5m",
    "notional": 10000.0,
    "margin": 500.0,
    "leverage": 20,
    "commission_rate": 0.0008,
    "rebate_pct": 0.70,
    "atr_period": 14,
    "sl_mult": 1.0,
    "tp_mult": 1.5,
    "cooldown": 3,
    "b_open_fresh": True,
    "be_raise_amount": 0.0,
    "risk_method": "be_only",
    "optimization_method": "bayesian",
    "n_trials": 200,
    "xgb_estimators": 200,
    "xgb_depth": 4,
    "ml_threshold": 0.5,
}


def parameter_inputs(defaults: dict = None) -> dict:
    """
    Streamlit form for all configuration options.

    Falls back to dict of defaults when not running in Streamlit.

    Args:
        defaults: Override default values.

    Returns:
        dict with all parameter values.
    """
    d = {**DEFAULT_PARAMS}
    if defaults:
        d.update(defaults)

    try:
        import streamlit as st

        st.sidebar.header("Strategy Parameters")
        d["timeframe"] = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h"], index=1)
        d["notional"] = st.sidebar.number_input("Notional ($)", value=d["notional"], step=1000.0)
        d["margin"] = st.sidebar.number_input("Margin ($)", value=d["margin"], step=100.0)
        d["leverage"] = st.sidebar.number_input("Leverage", value=d["leverage"], min_value=1, max_value=125)
        d["commission_rate"] = st.sidebar.number_input("Commission Rate", value=d["commission_rate"],
                                                        step=0.0001, format="%.4f")
        d["rebate_pct"] = st.sidebar.selectbox("Rebate %", [0.70, 0.50], index=0)

        st.sidebar.header("Entry / Exit")
        d["atr_period"] = st.sidebar.selectbox("ATR Period", [8, 13, 14, 21], index=2)
        d["sl_mult"] = st.sidebar.slider("SL (ATR mult)", 0.3, 4.0, d["sl_mult"], 0.1)
        d["tp_mult"] = st.sidebar.slider("TP (ATR mult)", 0.5, 6.0, d["tp_mult"], 0.1)
        d["cooldown"] = st.sidebar.slider("Cooldown (bars)", 0, 20, d["cooldown"])
        d["b_open_fresh"] = st.sidebar.checkbox("B Opens Fresh", value=d["b_open_fresh"])
        d["be_raise_amount"] = st.sidebar.number_input("BE Raise ($)", value=d["be_raise_amount"], step=1.0)
        d["risk_method"] = st.sidebar.selectbox("Risk Method",
                                                 ["be_only", "be_plus_fees", "be_plus_fees_trail_tp", "be_trail_tp"])

        st.sidebar.header("Optimization")
        d["optimization_method"] = st.sidebar.selectbox("Method", ["bayesian", "grid", "walk_forward"])
        d["n_trials"] = st.sidebar.number_input("Trials", value=d["n_trials"], step=50)

        st.sidebar.header("ML Meta-Label")
        d["xgb_estimators"] = st.sidebar.number_input("XGB Estimators", value=d["xgb_estimators"], step=50)
        d["xgb_depth"] = st.sidebar.slider("XGB Depth", 2, 10, d["xgb_depth"])
        d["ml_threshold"] = st.sidebar.slider("ML Threshold", 0.0, 1.0, d["ml_threshold"], 0.05)

    except (ImportError, RuntimeError):
        pass

    return d


if __name__ == "__main__":
    params = parameter_inputs()
    expected_keys = ["timeframe", "notional", "commission_rate", "atr_period",
                     "sl_mult", "tp_mult", "risk_method", "ml_threshold"]
    missing = [k for k in expected_keys if k not in params]
    if missing:
        print(f"FAIL -- missing keys: {missing}")
    else:
        print(f"PASS -- {len(params)} parameters returned")
