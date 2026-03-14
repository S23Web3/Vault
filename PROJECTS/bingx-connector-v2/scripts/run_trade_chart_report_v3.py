#!/usr/bin/env python3
"""
Trade Chart Report v3 - TDI module swap (Wilder RSI 13, correct fast/slow).
Paginated one-trade-per-page, AVWAP SD bands, toggle overlays,
structured @anchor notes, entry/exit markers, corrected TDI indicator.

Run: python scripts/run_trade_chart_report_v3.py --date 2026-03-11
"""
import argparse
import csv
import hashlib
import hmac as hmac_lib
import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone, date
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yaml
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
TRADES_CSV = ROOT / "trades_all.csv"
CONFIG_PATH = ROOT / "config.yaml"
LOG_DIR = ROOT / "logs"
KLINE_PATH = "/openApi/swap/v2/quote/klines"

FULL_COLUMNS = [
    "timestamp", "symbol", "direction", "grade", "entry_price", "exit_price",
    "exit_reason", "pnl_net", "quantity", "notional_usd", "entry_time", "order_id",
    "ttp_activated", "ttp_extreme_pct", "ttp_trail_pct", "ttp_exit_reason",
    "be_raised", "saw_green", "atr_at_entry", "sl_price",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TDI Module Import (Wilder RSI 13, zones, divergence)
# ---------------------------------------------------------------------------

_BACKTESTER = ROOT.parent / "four-pillars-backtester"
if str(_BACKTESTER) not in sys.path:
    sys.path.insert(0, str(_BACKTESTER))
from signals.tdi import compute_tdi


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def safe_float(val, default=0.0):
    """Parse a value to float, returning default on failure."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_bool(val):
    """Parse a value to bool."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return False
    return str(val).strip().lower() == "true"


def to_ms(ts_str):
    """Parse ISO timestamp string to milliseconds epoch."""
    if not ts_str or (isinstance(ts_str, float) and pd.isna(ts_str)):
        return 0
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return 0


def hold_minutes(entry_ts, exit_ts):
    """Compute hold time in minutes between two ISO timestamps."""
    entry_ms = to_ms(entry_ts)
    exit_ms = to_ms(exit_ts)
    if entry_ms == 0 or exit_ms == 0:
        return 0.0
    return max((exit_ms - entry_ms) / 60000.0, 0.0)


# ---------------------------------------------------------------------------
# BingX API
# ---------------------------------------------------------------------------


def sign_and_build(base, path, params, api_key, secret):
    """Build signed URL and return (url, headers)."""
    params["timestamp"] = str(int(time.time() * 1000))
    params["recvWindow"] = "10000"
    sorted_params = sorted(params.items())
    qs = "&".join(k + "=" + str(v) for k, v in sorted_params)
    sig = hmac_lib.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = base + path + "?" + qs + "&signature=" + sig
    return url, {"X-BX-APIKEY": api_key}


def fetch_klines(symbol, start_ms, end_ms, base, api_key, secret):
    """Fetch 5m klines for symbol in [start_ms, end_ms]."""
    params = {
        "symbol": symbol,
        "interval": "5m",
        "startTime": str(start_ms),
        "endTime": str(end_ms),
        "limit": "500",
    }
    url, headers = sign_and_build(base, KLINE_PATH, params, api_key, secret)
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        if data.get("code", -1) != 0:
            return []
        return data.get("data", [])
    except Exception as e:
        log.warning("Kline fetch failed %s: %s", symbol, e)
        return []


# ---------------------------------------------------------------------------
# Indicators
# ---------------------------------------------------------------------------


def stoch_k(close, high, low, k_len):
    """Raw K stochastic -- no SMA smoothing."""
    n = len(close)
    result = np.full(n, np.nan)
    for i in range(k_len - 1, n):
        wl = low[i - k_len + 1: i + 1]
        wh = high[i - k_len + 1: i + 1]
        lowest = np.min(wl)
        highest = np.max(wh)
        if highest - lowest == 0:
            result[i] = 50.0
        else:
            result[i] = 100.0 * (close[i] - lowest) / (highest - lowest)
    return result


def find_ema_cross_before(df, entry_idx):
    """Find last EMA 55/89 cross before entry_idx. Return cross bar index."""
    ema55 = df["ema55"].values
    ema89 = df["ema89"].values
    diff = ema55 - ema89
    for i in range(entry_idx - 1, 0, -1):
        if not (np.isnan(diff[i]) or np.isnan(diff[i - 1])):
            if (diff[i] >= 0 and diff[i - 1] < 0) or (diff[i] <= 0 and diff[i - 1] > 0):
                return i
    return 0


def compute_indicators(df, entry_idx):
    """Compute all chart indicators on kline DataFrame."""
    c = df["close"].values.astype(float)
    h = df["high"].values.astype(float)
    lo = df["low"].values.astype(float)
    v = df["volume"].values.astype(float)

    # EMA 55 and EMA 89 (must be before AVWAP for cross detection)
    df["ema55"] = df["close"].astype(float).ewm(span=55, adjust=False).mean()
    df["ema89"] = df["close"].astype(float).ewm(span=89, adjust=False).mean()

    # Find AVWAP anchor: last EMA 55/89 cross before entry
    anchor_idx = find_ema_cross_before(df, entry_idx)

    # AVWAP anchored at EMA cross point + SD bands
    tp = (h + lo + c) / 3.0
    avwap = np.full(len(df), np.nan)
    avwap_1sd_upper = np.full(len(df), np.nan)
    avwap_1sd_lower = np.full(len(df), np.nan)
    avwap_2sd_upper = np.full(len(df), np.nan)
    avwap_2sd_lower = np.full(len(df), np.nan)

    if 0 <= anchor_idx < len(df):
        cum_tpv = 0.0
        cum_v = 0.0
        cum_sq_dev = 0.0
        count = 0
        for i in range(anchor_idx, len(df)):
            cum_tpv += tp[i] * v[i]
            cum_v += v[i]
            if cum_v > 0:
                vwap_val = cum_tpv / cum_v
                avwap[i] = vwap_val
                count += 1
                cum_sq_dev += (tp[i] - vwap_val) ** 2
                if count > 1:
                    sd = np.sqrt(cum_sq_dev / count)
                    avwap_1sd_upper[i] = vwap_val + sd
                    avwap_1sd_lower[i] = vwap_val - sd
                    avwap_2sd_upper[i] = vwap_val + 2.0 * sd
                    avwap_2sd_lower[i] = vwap_val - 2.0 * sd

    df["avwap"] = avwap
    df["avwap_1sd_upper"] = avwap_1sd_upper
    df["avwap_1sd_lower"] = avwap_1sd_lower
    df["avwap_2sd_upper"] = avwap_2sd_upper
    df["avwap_2sd_lower"] = avwap_2sd_lower

    # AVWAP Hi -- anchored at highest high bar in window + SD bands
    hi_anchor = int(np.argmax(h))
    avwap_hi = np.full(len(df), np.nan)
    avwap_hi_1sd_u = np.full(len(df), np.nan)
    avwap_hi_1sd_l = np.full(len(df), np.nan)
    avwap_hi_2sd_u = np.full(len(df), np.nan)
    avwap_hi_2sd_l = np.full(len(df), np.nan)
    if 0 <= hi_anchor < len(df):
        cum_tpv_h = 0.0
        cum_v_h = 0.0
        cum_sq_h = 0.0
        cnt_h = 0
        for i in range(hi_anchor, len(df)):
            cum_tpv_h += tp[i] * v[i]
            cum_v_h += v[i]
            if cum_v_h > 0:
                vw = cum_tpv_h / cum_v_h
                avwap_hi[i] = vw
                cnt_h += 1
                cum_sq_h += (tp[i] - vw) ** 2
                if cnt_h > 1:
                    sd_h = np.sqrt(cum_sq_h / cnt_h)
                    avwap_hi_1sd_u[i] = vw + sd_h
                    avwap_hi_1sd_l[i] = vw - sd_h
                    avwap_hi_2sd_u[i] = vw + 2.0 * sd_h
                    avwap_hi_2sd_l[i] = vw - 2.0 * sd_h
    df["avwap_hi"] = avwap_hi
    df["avwap_hi_1sd_u"] = avwap_hi_1sd_u
    df["avwap_hi_1sd_l"] = avwap_hi_1sd_l
    df["avwap_hi_2sd_u"] = avwap_hi_2sd_u
    df["avwap_hi_2sd_l"] = avwap_hi_2sd_l

    # AVWAP Lo -- anchored at lowest low bar in window + SD bands
    lo_anchor = int(np.argmin(lo))
    avwap_lo = np.full(len(df), np.nan)
    avwap_lo_1sd_u = np.full(len(df), np.nan)
    avwap_lo_1sd_l = np.full(len(df), np.nan)
    avwap_lo_2sd_u = np.full(len(df), np.nan)
    avwap_lo_2sd_l = np.full(len(df), np.nan)
    if 0 <= lo_anchor < len(df):
        cum_tpv_l = 0.0
        cum_v_l = 0.0
        cum_sq_l = 0.0
        cnt_l = 0
        for i in range(lo_anchor, len(df)):
            cum_tpv_l += tp[i] * v[i]
            cum_v_l += v[i]
            if cum_v_l > 0:
                vw = cum_tpv_l / cum_v_l
                avwap_lo[i] = vw
                cnt_l += 1
                cum_sq_l += (tp[i] - vw) ** 2
                if cnt_l > 1:
                    sd_l = np.sqrt(cum_sq_l / cnt_l)
                    avwap_lo_1sd_u[i] = vw + sd_l
                    avwap_lo_1sd_l[i] = vw - sd_l
                    avwap_lo_2sd_u[i] = vw + 2.0 * sd_l
                    avwap_lo_2sd_l[i] = vw - 2.0 * sd_l
    df["avwap_lo"] = avwap_lo
    df["avwap_lo_1sd_u"] = avwap_lo_1sd_u
    df["avwap_lo_1sd_l"] = avwap_lo_1sd_l
    df["avwap_lo_2sd_u"] = avwap_lo_2sd_u
    df["avwap_lo_2sd_l"] = avwap_lo_2sd_l

    # Stochastics
    df["stoch_9"] = stoch_k(c, h, lo, 9)
    df["stoch_14"] = stoch_k(c, h, lo, 14)
    s40 = stoch_k(c, h, lo, 40)
    df["stoch_40"] = s40
    df["stoch_40_d"] = pd.Series(s40).rolling(4, min_periods=1).mean().values
    s60 = stoch_k(c, h, lo, 60)
    df["stoch_60"] = s60
    df["stoch_60_d"] = pd.Series(s60).rolling(10, min_periods=1).mean().values

    # TDI -- Traders Dynamic Index (Wilder RSI 13, proper fast/slow, zones, divergence)
    try:
        tdi_df = compute_tdi(df, {"tdi_preset": "cw_trades"})
        df["tdi_rsi"] = tdi_df["tdi_rsi"]
        df["tdi_upper"] = tdi_df["tdi_bb_upper"]
        df["tdi_lower"] = tdi_df["tdi_bb_lower"]
        df["tdi_mid"] = tdi_df["tdi_bb_mid"]
        df["tdi_fast"] = tdi_df["tdi_fast_ma"]
        df["tdi_slow"] = tdi_df["tdi_signal"]
        df["tdi_zone"] = tdi_df["tdi_zone"]
        df["tdi_cloud_bull"] = tdi_df["tdi_cloud_bull"]
        df["tdi_long"] = tdi_df["tdi_long"]
        df["tdi_short"] = tdi_df["tdi_short"]
        df["tdi_bull_div"] = tdi_df["tdi_bull_div"]
        df["tdi_bear_div"] = tdi_df["tdi_bear_div"]
    except Exception as e:
        log.warning("TDI compute failed: %s", e)

    return df


# ---------------------------------------------------------------------------
# Four Pillars Signal Detection
# ---------------------------------------------------------------------------


def detect_signals(df, cfg):
    """Run Four Pillars signal detection. Returns True if signals added."""
    try:
        _BACKTESTER = ROOT.parent / "four-pillars-backtester"
        if str(_BACKTESTER) not in sys.path:
            sys.path.insert(0, str(_BACKTESTER))
        from signals.four_pillars import compute_signals

        fp = cfg.get("four_pillars", {})
        params = {
            "cross_level": fp.get("cross_level", 25),
            "zone_level": fp.get("zone_level", 30),
            "allow_b_trades": fp.get("allow_b", True),
            "allow_c_trades": fp.get("allow_c", False),
            "require_stage2": fp.get("require_stage2", True),
            "rot_level": fp.get("rot_level", 80),
            "atr_length": fp.get("atr_length", 14),
        }

        sig_df = df.copy()
        if "time" in sig_df.columns and "timestamp" not in sig_df.columns:
            sig_df = sig_df.rename(columns={"time": "timestamp"})
        if "volume" in sig_df.columns and "base_vol" not in sig_df.columns:
            sig_df = sig_df.rename(columns={"volume": "base_vol"})
        if "quote_vol" not in sig_df.columns:
            sig_df["quote_vol"] = 0.0

        sig_df = compute_signals(sig_df, params)

        for col in ["long_a", "long_b", "short_a", "short_b"]:
            if col in sig_df.columns:
                df[col] = sig_df[col].values

        return True
    except Exception as e:
        log.warning("Signal detection failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Trade Loading
# ---------------------------------------------------------------------------


def load_and_filter_trades(target_date, from_time, symbol_filter):
    """Load trades.csv and filter by date/time/symbol."""
    if not TRADES_CSV.exists():
        log.error("trades.csv not found: %s", TRADES_CSV)
        sys.exit(1)

    rows = []
    with open(TRADES_CSV, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        _header = next(reader)
        for line in reader:
            while len(line) < len(FULL_COLUMNS):
                line.append("")
            rows.append(dict(zip(FULL_COLUMNS, line[:len(FULL_COLUMNS)])))

    trades = []
    for row in rows:
        entry_time = row.get("entry_time", "")
        if not entry_time:
            continue
        if target_date and not entry_time.startswith(target_date):
            continue
        if from_time:
            try:
                et_dt = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
                et_hm = et_dt.strftime("%H:%M")
                if et_hm < from_time:
                    continue
            except Exception:
                continue
        if symbol_filter and row.get("symbol", "") != symbol_filter:
            continue
        trades.append(row)

    log.info("Filtered to %d trades", len(trades))
    return trades


# ---------------------------------------------------------------------------
# Chart Building
# ---------------------------------------------------------------------------


def build_trade_chart(trade, kline_df, trade_num, has_signals):
    """Build Plotly figure with 6 subplots: price, stoch 9, stoch 14, TDI, stoch 40, stoch 60."""
    fig = make_subplots(
        rows=6, cols=1, shared_xaxes=True,
        vertical_spacing=0.015,
        row_heights=[0.30, 0.12, 0.12, 0.16, 0.15, 0.15],
        subplot_titles=["", "Stoch 9", "Stoch 14", "TDI 13", "Stoch 40", "Stoch 60"],
    )

    times = kline_df["time_str"].tolist()
    direction = trade.get("direction", "LONG")
    entry_price = safe_float(trade.get("entry_price"))
    exit_price = safe_float(trade.get("exit_price"))
    symbol = trade.get("symbol", "")
    grade = trade.get("grade", "")
    pnl_net = safe_float(trade.get("pnl_net"))
    exit_reason = trade.get("exit_reason", "")
    is_long = direction == "LONG"
    entry_color = "#00ff7f" if is_long else "#ff4444"

    # --- Panel 1: Candlestick + Overlays ---
    fig.add_trace(go.Candlestick(
        x=times, open=kline_df["open"], high=kline_df["high"],
        low=kline_df["low"], close=kline_df["close"],
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        name="OHLC", showlegend=False,
    ), row=1, col=1)

    # Invisible clickable overlay for measure/pin tools (close price at every bar)
    fig.add_trace(go.Scatter(
        x=times, y=kline_df["close"], mode="markers",
        marker=dict(size=12, color="rgba(0,0,0,0)"),
        name="_overlay", showlegend=False,
        hovertemplate="%{x}<br>%{y:.6f}<extra></extra>",
    ), row=1, col=1)

    # EMA 55/89
    fig.add_trace(go.Scatter(
        x=times, y=kline_df["ema55"], mode="lines",
        line=dict(color="#FF8C00", width=1), name="EMA 55",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=kline_df["ema89"], mode="lines",
        line=dict(color="#1E90FF", width=1), name="EMA 89",
    ), row=1, col=1)

    # AVWAP + SD bands
    avwap_valid = kline_df[kline_df["avwap"].notna()]
    if len(avwap_valid) > 0:
        avt = avwap_valid["time_str"].tolist()
        fig.add_trace(go.Scatter(
            x=avt, y=avwap_valid["avwap"],
            mode="lines", line=dict(color="#FFFFFF", width=1, dash="dash"),
            name="AVWAP",
        ), row=1, col=1)

        # 1 SD bands
        sd1_valid = avwap_valid[avwap_valid["avwap_1sd_upper"].notna()]
        if len(sd1_valid) > 0:
            sd1t = sd1_valid["time_str"].tolist()
            fig.add_trace(go.Scatter(
                x=sd1t, y=sd1_valid["avwap_1sd_upper"],
                mode="lines", line=dict(color="rgba(173,216,230,0.5)", width=0.8, dash="dot"),
                name="AVWAP +1SD", showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=sd1t, y=sd1_valid["avwap_1sd_lower"],
                mode="lines", line=dict(color="rgba(173,216,230,0.5)", width=0.8, dash="dot"),
                name="AVWAP -1SD", showlegend=False,
            ), row=1, col=1)

        # 2 SD bands
        sd2_valid = avwap_valid[avwap_valid["avwap_2sd_upper"].notna()]
        if len(sd2_valid) > 0:
            sd2t = sd2_valid["time_str"].tolist()
            fig.add_trace(go.Scatter(
                x=sd2t, y=sd2_valid["avwap_2sd_upper"],
                mode="lines", line=dict(color="rgba(173,216,230,0.3)", width=0.6, dash="dot"),
                name="AVWAP +2SD", showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=sd2t, y=sd2_valid["avwap_2sd_lower"],
                mode="lines", line=dict(color="rgba(173,216,230,0.3)", width=0.6, dash="dot"),
                name="AVWAP -2SD", showlegend=False,
            ), row=1, col=1)

    # AVWAP Hi (from highest high bar) -- yellow-green dashed + SD bands
    avwap_hi_valid = kline_df[kline_df["avwap_hi"].notna()]
    if len(avwap_hi_valid) > 0:
        fig.add_trace(go.Scatter(
            x=avwap_hi_valid["time_str"].tolist(), y=avwap_hi_valid["avwap_hi"],
            mode="lines", line=dict(color="#ADFF2F", width=1, dash="dash"),
            name="AVWAP Hi",
        ), row=1, col=1)
        hi_sd1 = avwap_hi_valid[avwap_hi_valid["avwap_hi_1sd_u"].notna()]
        if len(hi_sd1) > 0:
            hi_sd1t = hi_sd1["time_str"].tolist()
            fig.add_trace(go.Scatter(
                x=hi_sd1t, y=hi_sd1["avwap_hi_1sd_u"],
                mode="lines", line=dict(color="rgba(173,255,47,0.4)", width=0.8, dash="dot"),
                name="AVWAP Hi +1SD", showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=hi_sd1t, y=hi_sd1["avwap_hi_1sd_l"],
                mode="lines", line=dict(color="rgba(173,255,47,0.4)", width=0.8, dash="dot"),
                name="AVWAP Hi -1SD", showlegend=False,
            ), row=1, col=1)
        hi_sd2 = avwap_hi_valid[avwap_hi_valid["avwap_hi_2sd_u"].notna()]
        if len(hi_sd2) > 0:
            hi_sd2t = hi_sd2["time_str"].tolist()
            fig.add_trace(go.Scatter(
                x=hi_sd2t, y=hi_sd2["avwap_hi_2sd_u"],
                mode="lines", line=dict(color="rgba(173,255,47,0.25)", width=0.6, dash="dot"),
                name="AVWAP Hi +2SD", showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=hi_sd2t, y=hi_sd2["avwap_hi_2sd_l"],
                mode="lines", line=dict(color="rgba(173,255,47,0.25)", width=0.6, dash="dot"),
                name="AVWAP Hi -2SD", showlegend=False,
            ), row=1, col=1)

    # AVWAP Lo (from lowest low bar) -- coral dashed + SD bands
    avwap_lo_valid = kline_df[kline_df["avwap_lo"].notna()]
    if len(avwap_lo_valid) > 0:
        fig.add_trace(go.Scatter(
            x=avwap_lo_valid["time_str"].tolist(), y=avwap_lo_valid["avwap_lo"],
            mode="lines", line=dict(color="#FF7F50", width=1, dash="dash"),
            name="AVWAP Lo",
        ), row=1, col=1)
        lo_sd1 = avwap_lo_valid[avwap_lo_valid["avwap_lo_1sd_u"].notna()]
        if len(lo_sd1) > 0:
            lo_sd1t = lo_sd1["time_str"].tolist()
            fig.add_trace(go.Scatter(
                x=lo_sd1t, y=lo_sd1["avwap_lo_1sd_u"],
                mode="lines", line=dict(color="rgba(255,127,80,0.4)", width=0.8, dash="dot"),
                name="AVWAP Lo +1SD", showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=lo_sd1t, y=lo_sd1["avwap_lo_1sd_l"],
                mode="lines", line=dict(color="rgba(255,127,80,0.4)", width=0.8, dash="dot"),
                name="AVWAP Lo -1SD", showlegend=False,
            ), row=1, col=1)
        lo_sd2 = avwap_lo_valid[avwap_lo_valid["avwap_lo_2sd_u"].notna()]
        if len(lo_sd2) > 0:
            lo_sd2t = lo_sd2["time_str"].tolist()
            fig.add_trace(go.Scatter(
                x=lo_sd2t, y=lo_sd2["avwap_lo_2sd_u"],
                mode="lines", line=dict(color="rgba(255,127,80,0.25)", width=0.6, dash="dot"),
                name="AVWAP Lo +2SD", showlegend=False,
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=lo_sd2t, y=lo_sd2["avwap_lo_2sd_l"],
                mode="lines", line=dict(color="rgba(255,127,80,0.25)", width=0.6, dash="dot"),
                name="AVWAP Lo -2SD", showlegend=False,
            ), row=1, col=1)

    # Entry/exit arrow markers (Change 4)
    entry_bar_time = trade.get("_entry_bar_time")
    exit_bar_time = trade.get("_exit_bar_time")
    entry_idx_local = trade.get("_entry_idx")
    exit_idx_local = trade.get("_exit_idx")

    if entry_bar_time is not None and entry_idx_local is not None:
        # Offset arrow away from candle by ~0.3% of price range so it doesn't overlap wick
        price_range = float(kline_df["high"].max() - kline_df["low"].min())
        offset = price_range * 0.015
        if is_long:
            marker_y = float(kline_df.iloc[entry_idx_local]["low"]) - offset
            marker_sym = "triangle-up"
            marker_clr = "#00ff7f"
        else:
            marker_y = float(kline_df.iloc[entry_idx_local]["high"]) + offset
            marker_sym = "triangle-down"
            marker_clr = "#ff4444"
        entry_label = "LONG ENTRY" if is_long else "SHORT ENTRY"
        text_pos = "bottom center" if is_long else "top center"
        fig.add_trace(go.Scatter(
            x=[entry_bar_time], y=[marker_y], mode="markers+text",
            marker=dict(symbol=marker_sym, size=16, color=marker_clr, line=dict(width=1, color="#FFFFFF")),
            text=[entry_label], textposition=text_pos,
            textfont=dict(size=9, color=marker_clr),
            name="Entry", showlegend=False,
        ), row=1, col=1)

    if exit_bar_time is not None and exit_idx_local is not None:
        exit_offset_y = float(kline_df.iloc[exit_idx_local]["low"]) - offset if is_long else float(kline_df.iloc[exit_idx_local]["high"]) + offset
        fig.add_trace(go.Scatter(
            x=[exit_bar_time], y=[exit_offset_y], mode="markers+text",
            marker=dict(symbol="x", size=14, color="#AAAAAA", line=dict(width=2, color="#AAAAAA")),
            text=["EXIT"], textposition="bottom center" if is_long else "top center",
            textfont=dict(size=9, color="#AAAAAA"),
            name="Exit", showlegend=False,
        ), row=1, col=1)

    # Entry/exit vertical lines (6 rows)
    for r in range(1, 7):
        yref_str = "y domain" if r == 1 else ("y" + str(r) + " domain")
        if entry_bar_time:
            fig.add_shape(
                type="line", x0=entry_bar_time, x1=entry_bar_time,
                y0=0, y1=1, yref=yref_str,
                line=dict(color=entry_color, dash="dash", width=1),
                row=r, col=1,
            )
        if exit_bar_time:
            fig.add_shape(
                type="line", x0=exit_bar_time, x1=exit_bar_time,
                y0=0, y1=1, yref=yref_str,
                line=dict(color="#AAAAAA", dash="dot", width=1),
                row=r, col=1,
            )

    # Entry/exit price horizontals
    fig.add_hline(
        y=entry_price, line_dash="dot", line_color=entry_color,
        line_width=1, opacity=0.6, row=1, col=1,
    )
    fig.add_hline(
        y=exit_price, line_dash="dot", line_color="#AAAAAA",
        line_width=1, opacity=0.6, row=1, col=1,
    )

    # Four Pillars signal vertical lines
    if has_signals:
        signal_defs = [
            ("long_a", "green", "solid", 2, 0.9, "A^"),
            ("long_b", "green", "dash", 1.5, 0.7, "B^"),
            ("short_a", "red", "solid", 2, 0.9, "Av"),
            ("short_b", "red", "dash", 1.5, 0.7, "Bv"),
        ]
        for col, color, dash, width, opacity, label in signal_defs:
            if col not in kline_df.columns:
                continue
            sig_mask = kline_df[col].fillna(False).astype(bool)
            sig_bars = kline_df[sig_mask]
            for _, sbar in sig_bars.iterrows():
                st = sbar["time_str"]
                fig.add_shape(
                    type="line", x0=st, x1=st, y0=0, y1=1,
                    yref="y domain",
                    line=dict(color=color, dash=dash, width=width),
                    opacity=opacity, row=1, col=1,
                )
                fig.add_annotation(
                    x=st, y=1.0, yref="y domain",
                    text=label, showarrow=False,
                    font=dict(size=9, color=color),
                    yanchor="bottom", row=1, col=1,
                )
                # Signal lines on stoch/TDI panels (rows 2-6)
                for sr in range(2, 7):
                    fig.add_shape(
                        type="line", x0=st, x1=st, y0=0, y1=1,
                        yref="y" + str(sr) + " domain",
                        line=dict(color=color, dash=dash, width=width),
                        opacity=0.3, row=sr, col=1,
                    )

    # Annotation box
    hold_min = hold_minutes(trade.get("entry_time"), trade.get("timestamp"))
    be_raised = safe_bool(trade.get("be_raised"))
    ttp_act = safe_bool(trade.get("ttp_activated"))
    n_la = int(kline_df["long_a"].sum()) if has_signals and "long_a" in kline_df.columns else 0
    n_lb = int(kline_df["long_b"].sum()) if has_signals and "long_b" in kline_df.columns else 0
    n_sa = int(kline_df["short_a"].sum()) if has_signals and "short_a" in kline_df.columns else 0
    n_sb = int(kline_df["short_b"].sum()) if has_signals and "short_b" in kline_df.columns else 0

    annot_parts = [
        "5m | " + symbol + " | " + direction + " | " + grade,
        "Entry: " + str(entry_price) + " -> Exit: " + str(exit_price),
        "PnL: $" + str(round(pnl_net, 4)) + " | Reason: " + exit_reason,
        "Hold: " + str(int(hold_min)) + "m | BE: " + str(be_raised) + " | TTP: " + str(ttp_act),
        "Signals: " + str(n_la) + "A^ " + str(n_lb) + "B^ " + str(n_sa) + "Av " + str(n_sb) + "Bv in window",
    ]
    annot_text = "<br>".join(annot_parts)

    fig.add_annotation(
        x=0.01, y=0.99, xref="x domain", yref="y domain",
        text=annot_text, showarrow=False,
        font=dict(family="Courier New, monospace", size=10, color="#c9d1d9"),
        align="left", bgcolor="rgba(22, 27, 34, 0.85)",
        bordercolor="rgba(0,0,0,0)", borderwidth=0,
        row=1, col=1,
    )

    # --- Panel 2: Stoch 9 (zone levels: 25/75) ---
    if "stoch_9" in kline_df.columns:
        s9 = kline_df["stoch_9"].values.astype(float)
        # Overbought zone fill (>75): green
        s9_upper_base = np.full(len(s9), 75.0)
        s9_upper_clip = np.where(s9 > 75, s9, 75.0)
        fig.add_trace(go.Scatter(
            x=times, y=s9_upper_base, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s9_upper_clip, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(0,255,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=2, col=1)
        # Oversold zone fill (<25): red
        s9_lower_clip = np.where(s9 < 25, s9, 25.0)
        s9_lower_base = np.full(len(s9), 25.0)
        fig.add_trace(go.Scatter(
            x=times, y=s9_lower_clip, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s9_lower_base, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(255,0,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["stoch_9"], mode="lines",
            line=dict(color="#00BFFF", width=1), name="K9",
        ), row=2, col=1)
    fig.add_hline(y=75, line_dash="dash", line_color="red", line_width=0.5, opacity=0.4, row=2, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color="green", line_width=0.5, opacity=0.4, row=2, col=1)

    # --- Panel 3: Stoch 14 (zone levels: 25/75) ---
    if "stoch_14" in kline_df.columns:
        s14 = kline_df["stoch_14"].values.astype(float)
        s14_upper_base = np.full(len(s14), 75.0)
        s14_upper_clip = np.where(s14 > 75, s14, 75.0)
        fig.add_trace(go.Scatter(
            x=times, y=s14_upper_base, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s14_upper_clip, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(0,255,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=3, col=1)
        s14_lower_clip = np.where(s14 < 25, s14, 25.0)
        s14_lower_base = np.full(len(s14), 25.0)
        fig.add_trace(go.Scatter(
            x=times, y=s14_lower_clip, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s14_lower_base, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(255,0,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["stoch_14"], mode="lines",
            line=dict(color="#DA70D6", width=1), name="K14",
        ), row=3, col=1)
    fig.add_hline(y=75, line_dash="dash", line_color="red", line_width=0.5, opacity=0.4, row=3, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color="green", line_width=0.5, opacity=0.4, row=3, col=1)

    # --- Panel 4: TDI 13 ---
    if "tdi_rsi" in kline_df.columns:
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["tdi_upper"], mode="lines",
            line=dict(color="#12bcc9", width=1.5, dash="solid"), name="TDI VB Hi",
            opacity=0.6, showlegend=False,
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["tdi_lower"], mode="lines",
            line=dict(color="#12bcc9", width=1.5, dash="solid"), name="TDI VB Lo",
            opacity=0.6, showlegend=False,
            fill="tonexty", fillcolor="rgba(18,188,201,0.18)",
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["tdi_mid"], mode="lines",
            line=dict(color="#FF8C00", width=1.5), name="TDI MBL",
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["tdi_fast"], mode="lines",
            line=dict(color="#00FF00", width=2), name="TDI Fast",
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["tdi_slow"], mode="lines",
            line=dict(color="#FF0000", width=1.5), name="TDI Slow",
        ), row=4, col=1)
    # TDI horizontal levels
    fig.add_hline(y=70, line_dash="dot", line_color="green", line_width=0.5, opacity=0.4, row=4, col=1)
    fig.add_hline(y=50, line_dash="dot", line_color="orange", line_width=0.5, opacity=0.4, row=4, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="red", line_width=0.5, opacity=0.4, row=4, col=1)

    # --- Panel 5: Stoch 40 (zone levels: 30/70) ---
    if "stoch_40" in kline_df.columns:
        s40 = kline_df["stoch_40"].values.astype(float)
        s40_ub = np.full(len(s40), 70.0)
        s40_uc = np.where(s40 > 70, s40, 70.0)
        fig.add_trace(go.Scatter(
            x=times, y=s40_ub, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=5, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s40_uc, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(0,255,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=5, col=1)
        s40_lc = np.where(s40 < 30, s40, 30.0)
        s40_lb = np.full(len(s40), 30.0)
        fig.add_trace(go.Scatter(
            x=times, y=s40_lc, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=5, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s40_lb, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(255,0,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=5, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["stoch_40"], mode="lines",
            line=dict(color="#FFD700", width=1.5), name="K40",
        ), row=5, col=1)
    if "stoch_40_d" in kline_df.columns:
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["stoch_40_d"], mode="lines",
            line=dict(color="#FFD700", width=1, dash="dot"), name="D40",
        ), row=5, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.5, opacity=0.4, row=5, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.5, opacity=0.4, row=5, col=1)

    # --- Panel 6: Stoch 60 (zone levels: 30/70) ---
    if "stoch_60" in kline_df.columns:
        s60 = kline_df["stoch_60"].values.astype(float)
        s60_ub = np.full(len(s60), 70.0)
        s60_uc = np.where(s60 > 70, s60, 70.0)
        fig.add_trace(go.Scatter(
            x=times, y=s60_ub, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=6, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s60_uc, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(0,255,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=6, col=1)
        s60_lc = np.where(s60 < 30, s60, 30.0)
        s60_lb = np.full(len(s60), 30.0)
        fig.add_trace(go.Scatter(
            x=times, y=s60_lc, mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ), row=6, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=s60_lb, mode="lines",
            line=dict(width=0), fill="tonexty", fillcolor="rgba(255,0,0,0.15)",
            showlegend=False, hoverinfo="skip",
        ), row=6, col=1)
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["stoch_60"], mode="lines",
            line=dict(color="#FF6347", width=2), name="K60",
        ), row=6, col=1)
    if "stoch_60_d" in kline_df.columns:
        fig.add_trace(go.Scatter(
            x=times, y=kline_df["stoch_60_d"], mode="lines",
            line=dict(color="#FF6347", width=1.5, dash="dot"), name="D60",
        ), row=6, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.5, opacity=0.4, row=6, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.5, opacity=0.4, row=6, col=1)

    # Layout -- Change 5: 5m timeframe in title
    entry_time_str = trade.get("entry_time", "")[:19]
    title_text = (
        "#" + str(trade_num) + " 5m | " + symbol
        + " | " + direction + " | " + grade
        + " | " + entry_time_str
        + " | PnL: $" + str(round(pnl_net, 4))
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="Courier New, monospace", size=11),
        height=1400,
        margin=dict(l=60, r=20, t=40, b=20),
        title=dict(text=title_text, font=dict(size=12)),
        showlegend=False,
        xaxis_rangeslider_visible=False,
    )
    # Stoch panels 0-100, TDI panel 0-100
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    fig.update_yaxes(range=[0, 100], row=4, col=1)
    fig.update_yaxes(range=[0, 100], row=5, col=1)
    fig.update_yaxes(range=[0, 100], row=6, col=1)

    # Crosshair spike lines on all axes
    spike_opts = dict(
        showspikes=True, spikemode="across", spikesnap="cursor",
        spikethickness=1, spikedash="dot", spikecolor="#58a6ff",
    )
    fig.update_xaxes(**spike_opts)
    fig.update_yaxes(showspikes=True, spikemode="across", spikesnap="cursor",
                     spikethickness=1, spikedash="dot", spikecolor="#58a6ff")
    # Hover: closest trace only, compact label, semi-transparent
    fig.update_layout(
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="rgba(13,17,23,0.75)",
            bordercolor="rgba(88,166,255,0.4)",
            font=dict(family="Courier New", size=10, color="#c9d1d9"),
            namelength=20,
        ),
    )

    # Style subplot titles
    for ann in fig.layout.annotations:
        ann.font = dict(size=10, color="#8b949e")

    return fig


# ---------------------------------------------------------------------------
# HTML Assembly
# ---------------------------------------------------------------------------


def build_html_report(trades_info, charts_html, target_date, from_time):
    """Assemble the full HTML report with pagination and notes panel."""
    total = len(trades_info)
    wins = sum(1 for t in trades_info if t["pnl"] > 0)
    wr = round(wins / total * 100, 1) if total > 0 else 0.0
    net_pnl = round(sum(t["pnl"] for t in trades_info), 4)
    first_t = min(t["entry_time"] for t in trades_info) if trades_info else ""
    last_t = max(t["entry_time"] for t in trades_info) if trades_info else ""

    p = []
    p.append("<!DOCTYPE html>")
    p.append('<html lang="en">')
    p.append("<head>")
    p.append('<meta charset="utf-8">')
    p.append("<title>Trade Chart Report v2 " + target_date + "</title>")
    p.append('<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>')
    p.append("<style>")
    p.append(CSS_BLOCK)
    p.append("</style>")
    p.append("</head>")
    p.append("<body>")

    # Summary bar
    summary_text = (
        "Date: " + target_date
        + " | Trades: " + str(total)
        + " | WR: " + str(wr) + "%"
        + " | Net PnL: $" + str(net_pnl)
        + " | " + first_t[:16] + " &rarr; " + last_t[:16]
    )
    p.append('<div id="summary-bar">')
    p.append('<span>' + summary_text + '</span>')
    p.append('<span id="nav-controls">')
    p.append('<button onclick="prevTrade()" title="Previous (Left Arrow)">&larr;</button>')
    p.append('<span id="page-indicator">1/' + str(total) + '</span>')
    p.append('<button onclick="nextTrade()" title="Next (Right Arrow)">&rarr;</button>')
    p.append('<button id="measure-btn" onclick="toggleMeasure()" title="Click two points to measure price delta">Measure</button>')
    p.append('<button id="pin-btn" onclick="togglePinMode()" title="Click chart to drop a numbered pin (auto-inserts into notes)">Pin</button>')
    p.append('<span id="measure-label" style="display:none;color:#58a6ff;margin-left:8px;font-weight:bold"></span>')
    p.append('</span>')
    p.append("</div>")

    # Left sidebar - trades list
    p.append('<div id="sidebar">')
    p.append('<div class="sidebar-header">-- TRADES --</div>')
    for i, info in enumerate(trades_info, 1):
        clr = "#00ff7f" if info["pnl"] > 0 else "#ef5350"
        dir_short = "L" if info["direction"] == "LONG" else "S"
        link_text = "#" + str(i) + " " + info["symbol"] + " " + dir_short + " $" + str(round(info["pnl"], 4))
        p.append('<a href="javascript:void(0)" onclick="goToTrade(' + str(i) + ')" '
                 + 'id="sidebar-link-' + str(i) + '" '
                 + 'style="color:' + clr + '">' + link_text + "</a>")
    # Legend at bottom of sidebar
    p.append('<div class="sidebar-legend">')
    p.append('<div class="sidebar-header" style="margin-top:16px">-- LEGEND --</div>')
    # (color, css_classes, label) -- classes: "" solid, "dashed", "dotted", "thick"
    legend_items = [
        ("#FF8C00", "", "EMA 55"),
        ("#1E90FF", "", "EMA 89"),
        ("#FFFFFF", "dashed", "AVWAP"),
        ("rgba(173,216,230,0.7)", "dotted", "AVWAP SD bands"),
        ("#ADFF2F", "dashed", "AVWAP Hi"),
        ("rgba(173,255,47,0.6)", "dotted", "AVWAP Hi SD"),
        ("#FF7F50", "dashed", "AVWAP Lo"),
        ("rgba(255,127,80,0.6)", "dotted", "AVWAP Lo SD"),
        ("#00BFFF", "", "K9"),
        ("#DA70D6", "", "K14"),
        ("#FFD700", "", "K40"),
        ("#FFD700", "dotted", "D40"),
        ("#FF6347", "thick", "K60"),
        ("#FF6347", "dotted", "D60"),
        ("#00FF00", "thick", "TDI Fast"),
        ("#FF0000", "", "TDI Slow"),
        ("#FF8C00", "", "TDI MBL"),
        ("#12bcc9", "", "TDI VB"),
        ("#00ff7f", "", "Entry (L)"),
        ("#ff4444", "", "Entry (S)"),
        ("#AAAAAA", "", "Exit"),
    ]
    for color, cls, label in legend_items:
        swatch_cls = "legend-swatch" + (" " + cls if cls else "")
        p.append('<div class="legend-item"><span class="' + swatch_cls + '" style="color:' + color + '"></span>' + label + '</div>')
    p.append('</div>')
    p.append("</div>")

    # Right sidebar - notes panel (Change 6, 7, 8, 10)
    p.append('<div id="notes-panel">')
    p.append('<div class="notes-header">-- NOTES --</div>')

    # Toggle buttons (Change 8)
    p.append('<div class="toggle-section">')
    p.append('<div class="toggle-label">Overlays:</div>')
    p.append('<label><input type="checkbox" id="tog-avwap" checked onchange="toggleOverlay(\'avwap\')"> AVWAP + Bands</label>')
    p.append('<label><input type="checkbox" id="tog-avwaphi" checked onchange="toggleOverlay(\'avwaphi\')"> AVWAP Hi + Bands</label>')
    p.append('<label><input type="checkbox" id="tog-avwaplo" checked onchange="toggleOverlay(\'avwaplo\')"> AVWAP Lo + Bands</label>')
    p.append('<label><input type="checkbox" id="tog-ema" checked onchange="toggleOverlay(\'ema\')"> EMA 55/89</label>')
    p.append('<label><input type="checkbox" id="tog-ripster" checked onchange="toggleOverlay(\'ripster\')"> Ripster</label>')
    p.append('<label><input type="checkbox" id="tog-markers" checked onchange="toggleOverlay(\'markers\')"> Entry/Exit</label>')
    p.append('<label><input type="checkbox" id="tog-stoch9" checked onchange="toggleOverlay(\'stoch9\')"> Stoch 9</label>')
    p.append('<label><input type="checkbox" id="tog-stoch14" checked onchange="toggleOverlay(\'stoch14\')"> Stoch 14</label>')
    p.append('<label><input type="checkbox" id="tog-tdi" checked onchange="toggleOverlay(\'tdi\')"> TDI 13</label>')
    p.append('<label><input type="checkbox" id="tog-stoch40" checked onchange="toggleOverlay(\'stoch40\')"> Stoch 40</label>')
    p.append('<label><input type="checkbox" id="tog-stoch60" checked onchange="toggleOverlay(\'stoch60\')"> Stoch 60</label>')
    p.append('</div>')

    # Export + clear pins buttons
    p.append('<div style="display:flex;gap:4px;margin-bottom:12px">')
    p.append('<button id="export-btn" onclick="exportAllNotes()" style="flex:1">Save All Notes (.md)</button>')
    p.append('<button id="clear-pins-btn" onclick="clearPins()" style="flex:0 0 auto;background:#484f58;color:#fff;border:none;padding:6px 10px;border-radius:4px;cursor:pointer;font-family:\'Courier New\',monospace;font-size:11px">Clear Pins</button>')
    p.append('</div>')

    # Notes textarea + preview (Change 7)
    p.append('<div class="note-box">')
    p.append('<label>Trade Notes:</label>')
    p.append('<textarea id="notes-textarea" rows="12" '
             + 'placeholder="Add notes... use @stoch9 @ema55 @avwap etc." '
             + 'oninput="onNoteInput()"></textarea>')
    p.append('<div class="note-footer">')
    p.append('<span class="char-count" id="char-count">0 chars</span>')
    p.append('<span id="save-status" style="font-size:10px;margin-left:6px"></span>')
    p.append('<button onclick="saveCurrentNote()">Save Note</button>')
    p.append('</div>')
    p.append('<div id="note-preview" class="note-preview"></div>')
    p.append('</div>')

    p.append("</div>")

    # Main content - trade pages
    p.append('<div id="main">')
    for i, (info, chart_html) in enumerate(zip(trades_info, charts_html), 1):
        display = "block" if i == 1 else "none"
        p.append('<div id="trade-page-' + str(i) + '" class="trade-page" style="display:' + display + '">')
        entry_t = info["entry_time"][:19]
        exit_t = info["exit_time"][:19]
        header = (
            "#" + str(i) + " " + info["symbol"]
            + " | " + info["direction"]
            + " | " + info["grade"]
            + " | " + entry_t + " &rarr; " + exit_t
            + " | " + info["exit_reason"]
        )
        p.append('<div class="trade-header">' + header + "</div>")
        p.append('<div class="chart-container">')
        p.append(chart_html)
        p.append('</div>')
        p.append("</div>")
    p.append("</div>")

    # Footer
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    p.append('<div id="footer">Generated: ' + now_str + " UTC | " + str(total) + " trades | run_trade_chart_report_v2.py</div>")

    # Build trades_info JSON for JS
    trades_json_parts = []
    for i, info in enumerate(trades_info, 1):
        trades_json_parts.append(
            '{"num":' + str(i)
            + ',"symbol":"' + info["symbol"]
            + '","direction":"' + info["direction"]
            + '","pnl":' + str(round(info["pnl"], 4))
            + '}'
        )
    trades_json = "[" + ",".join(trades_json_parts) + "]"

    # JavaScript
    p.append("<script>")
    p.append(build_js_block(target_date, total, trades_json))
    p.append("</script>")

    p.append("</body>")
    p.append("</html>")

    return "\n".join(p)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CSS_BLOCK = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0d1117; color: #c9d1d9;
  font-family: "Courier New", monospace; font-size: 12px;
}
#summary-bar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: #161b22; padding: 8px 16px; font-size: 12px;
  border-bottom: 1px solid #30363d;
  display: flex; justify-content: space-between; align-items: center;
}
#nav-controls button {
  background: #238636; color: #fff; border: none;
  padding: 4px 12px; margin: 0 4px; border-radius: 4px;
  cursor: pointer; font-family: "Courier New", monospace; font-size: 13px;
}
#nav-controls button:hover { background: #2ea043; }
#page-indicator { margin: 0 8px; color: #58a6ff; }
#pin-btn {
  background: #6e40c9; color: #fff; border: none;
  padding: 4px 12px; margin: 0 4px; border-radius: 4px;
  cursor: pointer; font-family: "Courier New", monospace; font-size: 13px;
}
#pin-btn:hover { background: #8957e5; }
#sidebar {
  position: fixed; left: 0; top: 36px; bottom: 0; width: 220px;
  overflow-y: auto; background: #0d1117;
  border-right: 1px solid #30363d; padding: 8px;
}
#sidebar .sidebar-header {
  color: #58a6ff; font-weight: bold; margin-bottom: 8px; text-align: center;
}
#sidebar a {
  display: block; padding: 3px 4px; text-decoration: none;
  font-size: 11px; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; border-radius: 3px;
}
#sidebar a:hover { background: #161b22; }
#sidebar a.active { background: #21262d; border-left: 3px solid #58a6ff; padding-left: 6px; }
.sidebar-legend { border-top: 1px solid #30363d; padding-top: 4px; }
.legend-item {
  font-size: 10px; padding: 1px 4px; color: #8b949e;
  display: flex; align-items: center; gap: 6px;
}
.legend-swatch {
  display: inline-block; width: 18px; height: 0; flex-shrink: 0;
  border-top: 2px solid currentColor;
}
.legend-swatch.dashed { border-top-style: dashed; }
.legend-swatch.dotted { border-top-style: dotted; }
.legend-swatch.thick { border-top-width: 3px; }
#notes-panel {
  position: fixed; right: 0; top: 36px; bottom: 0; width: 280px;
  overflow-y: auto; background: #0d1117;
  border-left: 1px solid #30363d; padding: 8px;
}
.notes-header {
  color: #58a6ff; font-weight: bold; margin-bottom: 8px; text-align: center;
}
.toggle-section {
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid #21262d;
}
.toggle-label { color: #8b949e; margin-bottom: 4px; }
.toggle-section label {
  display: block; padding: 2px 0; cursor: pointer; font-size: 11px;
  color: #c9d1d9;
}
.toggle-section input[type="checkbox"] { margin-right: 6px; }
#export-btn {
  background: #1f6feb; color: #fff; border: none;
  padding: 6px 12px; border-radius: 4px; cursor: pointer;
  font-family: "Courier New", monospace; font-size: 11px;
}
#export-btn:hover { background: #388bfd; }
.note-box { margin-top: 4px; }
.note-box label { color: #8b949e; display: block; margin-bottom: 4px; }
.note-box textarea {
  width: 100%; background: #161b22; border: 1px solid #30363d;
  color: #c9d1d9; font-family: "Courier New", monospace; font-size: 11px;
  padding: 8px; border-radius: 4px; resize: vertical;
}
.note-footer {
  display: flex; justify-content: space-between;
  align-items: center; margin-top: 4px;
}
.char-count { color: #484f58; font-size: 10px; }
.note-footer button {
  background: #238636; color: #fff; border: none;
  padding: 4px 12px; border-radius: 4px; cursor: pointer;
  font-size: 11px; font-family: "Courier New", monospace;
}
.note-footer button:hover { background: #2ea043; }
.note-preview {
  margin-top: 8px; padding: 8px; background: #161b22;
  border: 1px solid #21262d; border-radius: 4px;
  font-size: 11px; line-height: 1.5; min-height: 40px;
  white-space: pre-wrap; word-wrap: break-word;
}
#main {
  margin-left: 230px; margin-right: 290px;
  padding: 50px 16px 16px 16px;
}
.trade-page { background: #0d1117; }
.trade-header {
  color: #58a6ff; font-size: 13px; margin-bottom: 8px;
  padding-bottom: 4px; border-bottom: 1px solid #21262d;
}
.chart-container { width: 100%; }
.no-chart {
  color: #484f58; text-align: center; padding: 100px 0; font-size: 14px;
}
#footer {
  text-align: center; color: #484f58; font-size: 10px;
  padding: 16px; margin-left: 230px; margin-right: 290px;
  border-top: 1px solid #21262d;
}
"""


# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------


def build_js_block(target_date, total, trades_json):
    """Build the JavaScript block for pagination, notes, toggles, export."""
    return """
var REPORT_DATE = '""" + target_date + """';
var TOTAL = """ + str(total) + """;
var TRADES = """ + trades_json + """;
var currentPage = 1;

// --- Anchor color map ---
var ANCHOR_COLORS = {
  "stoch9": "#00BFFF", "stoch14": "#DA70D6",
  "stoch40": "#FFD700", "stoch60": "#FF6347",
  "tdi": "#00FF00", "tdislow": "#FF0000", "tdimid": "#FF8C00",
  "ema55": "#FF8C00", "ema89": "#1E90FF",
  "avwap": "#FFFFFF", "avwaphi": "#ADFF2F", "avwaplo": "#FF7F50",
  "entry": "#00ff7f",
  "exit": "#AAAAAA", "trend": "#FFFF00", "grade": "#00BFFF"
};

// --- Overlay trace name groups ---
var OVERLAY_TRACES = {
  "avwap": ["AVWAP", "AVWAP +1SD", "AVWAP -1SD", "AVWAP +2SD", "AVWAP -2SD"],
  "avwaphi": ["AVWAP Hi", "AVWAP Hi +1SD", "AVWAP Hi -1SD", "AVWAP Hi +2SD", "AVWAP Hi -2SD"],
  "avwaplo": ["AVWAP Lo", "AVWAP Lo +1SD", "AVWAP Lo -1SD", "AVWAP Lo +2SD", "AVWAP Lo -2SD"],
  "ema": ["EMA 55", "EMA 89"],
  "ripster": ["Ripster"],
  "markers": ["Entry", "Exit"],
  "stoch9": ["K9"],
  "stoch14": ["K14"],
  "tdi": ["TDI VB Hi", "TDI VB Lo", "TDI MBL", "TDI Fast", "TDI Slow"],
  "stoch40": ["K40", "D40"],
  "stoch60": ["K60", "D60"]
};

// --- Pagination ---
function goToTrade(n) {
  if (n < 1 || n > TOTAL) return;
  // save current note before switching
  saveCurrentNote();
  // hide current
  var cur = document.getElementById("trade-page-" + currentPage);
  if (cur) cur.style.display = "none";
  var curLink = document.getElementById("sidebar-link-" + currentPage);
  if (curLink) curLink.classList.remove("active");
  // show new
  currentPage = n;
  var next = document.getElementById("trade-page-" + n);
  if (next) next.style.display = "block";
  var nextLink = document.getElementById("sidebar-link-" + n);
  if (nextLink) nextLink.classList.add("active");
  document.getElementById("page-indicator").textContent = n + "/" + TOTAL;
  // load note for this trade
  loadCurrentNote();
  // load toggle states
  loadToggleStates();
  // resize plotly chart (hidden div fix) + init measure tool
  measureState.active = false;
  measureState.startY = null;
  var mbtn = document.getElementById("measure-btn");
  if (mbtn) { mbtn.style.background = "#238636"; mbtn.textContent = "Measure"; }
  document.getElementById("measure-label").style.display = "none";
  pinState.active = false;
  pinState.count = 0;
  var pbtn = document.getElementById("pin-btn");
  if (pbtn) { pbtn.style.background = "#6e40c9"; pbtn.textContent = "Pin"; }
  setTimeout(function() {
    var chartDiv = next ? next.querySelector(".js-plotly-plot") : null;
    if (chartDiv) {
      Plotly.Plots.resize(chartDiv);
      initMeasureTool(chartDiv);
      initPinTool(chartDiv);
      loadPins(chartDiv);
    }
  }, 50);
}
function nextTrade() { goToTrade(currentPage + 1); }
function prevTrade() { goToTrade(currentPage - 1); }

// Keyboard navigation
document.addEventListener("keydown", function(e) {
  if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
  if (e.key === "ArrowLeft") prevTrade();
  if (e.key === "ArrowRight") nextTrade();
});

// --- Notes (localStorage + server auto-save) ---
var SERVER_NOTES = {};  // loaded from server on init
var _saveTimer = null;
function noteKey(n) { return "bingx_note_" + REPORT_DATE + "_" + n; }

function saveCurrentNote() {
  var ta = document.getElementById("notes-textarea");
  var text = ta.value;
  localStorage.setItem(noteKey(currentPage), text);
  // Save to server (disk)
  saveNoteToServer(currentPage, text);
}

function saveNoteToServer(tradeNum, text) {
  fetch("/api/save-note", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({trade: tradeNum, note: text})
  }).then(function(r) {
    var el = document.getElementById("save-status");
    if (el) {
      el.textContent = r.ok ? "saved" : "err";
      el.style.color = r.ok ? "#238636" : "#da3633";
      setTimeout(function() { el.textContent = ""; }, 1500);
    }
  }).catch(function() {});
}

function debouncedAutoSave() {
  if (_saveTimer) clearTimeout(_saveTimer);
  _saveTimer = setTimeout(function() { saveCurrentNote(); }, 500);
}

function loadCurrentNote() {
  var ta = document.getElementById("notes-textarea");
  // Server notes take priority, then localStorage
  var serverNote = SERVER_NOTES[String(currentPage)];
  var localNote = localStorage.getItem(noteKey(currentPage));
  ta.value = serverNote || localNote || "";
  updatePreview();
  updateCharCount();
}

function loadAllNotesFromServer() {
  fetch("/api/load-notes").then(function(r) {
    return r.json();
  }).then(function(data) {
    SERVER_NOTES = data || {};
    // Sync to localStorage
    for (var k in SERVER_NOTES) {
      localStorage.setItem(noteKey(parseInt(k, 10)), SERVER_NOTES[k]);
    }
    loadCurrentNote();
  }).catch(function() {
    // Server not available, fall back to localStorage only
    loadCurrentNote();
  });
}

function updateCharCount() {
  var ta = document.getElementById("notes-textarea");
  document.getElementById("char-count").textContent = ta.value.length + " chars";
}
function onNoteInput() {
  updateCharCount();
  updatePreview();
  debouncedAutoSave();
}

// --- @Anchor preview ---
function updatePreview() {
  var ta = document.getElementById("notes-textarea");
  var text = ta.value;
  // escape HTML
  var safe = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  // highlight @anchors
  var pattern = /@(stoch9|stoch14|stoch40|stoch60|tdi|tdislow|tdimid|ema55|ema89|avwaphi|avwaplo|avwap|entry|exit|trend|grade)/g;
  var highlighted = safe.replace(pattern, function(match, anchor) {
    var color = ANCHOR_COLORS[anchor] || "#c9d1d9";
    return '<span style="color:' + color + ';font-weight:bold">' + match + '</span>';
  });
  document.getElementById("note-preview").innerHTML = highlighted;
}

// --- Toggle overlays ---
function toggleKey(n, overlay) { return "bingx_toggle_" + REPORT_DATE + "_" + n + "_" + overlay; }

function toggleOverlay(overlay) {
  var cb = document.getElementById("tog-" + overlay);
  var visible = cb.checked;
  localStorage.setItem(toggleKey(currentPage, overlay), visible ? "1" : "0");
  applyToggle(overlay, visible);
}

function applyToggle(overlay, visible) {
  var page = document.getElementById("trade-page-" + currentPage);
  if (!page) return;
  var chartDiv = page.querySelector(".js-plotly-plot");
  if (!chartDiv || !chartDiv.data) return;
  var traceNames = OVERLAY_TRACES[overlay] || [];
  for (var i = 0; i < chartDiv.data.length; i++) {
    var name = chartDiv.data[i].name || "";
    if (traceNames.indexOf(name) !== -1) {
      Plotly.restyle(chartDiv, {"visible": visible}, [i]);
    }
  }
}

function loadToggleStates() {
  var overlays = ["avwap", "avwaphi", "avwaplo", "ema", "ripster", "markers", "stoch9", "stoch14", "tdi", "stoch40", "stoch60"];
  for (var j = 0; j < overlays.length; j++) {
    var ov = overlays[j];
    var saved = localStorage.getItem(toggleKey(currentPage, ov));
    var cb = document.getElementById("tog-" + ov);
    if (saved !== null) {
      cb.checked = saved === "1";
    } else {
      cb.checked = true;
    }
    applyToggle(ov, cb.checked);
  }
}

// --- Export all notes ---
function exportAllNotes() {
  saveCurrentNote();
  var lines = ["# Trade Notes -- " + REPORT_DATE, ""];
  for (var i = 0; i < TRADES.length; i++) {
    var t = TRADES[i];
    var note = localStorage.getItem(noteKey(t.num)) || "";
    lines.push("## Trade #" + t.num + " -- " + t.symbol + " | " + t.direction + " | $" + t.pnl);
    lines.push("");
    lines.push(note || "(no notes)");
    lines.push("");
  }
  var content = lines.join("\\n");
  var blob = new Blob([content], {type: "text/markdown"});
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = "trade_notes_" + REPORT_DATE + ".md";
  a.click();
  URL.revokeObjectURL(url);
}

// --- Price measurement tool ---
var measureState = { active: false, startY: null, startX: null, shapes: [] };

function initMeasureTool(chartDiv) {
  if (!chartDiv) return;
  chartDiv.on("plotly_click", function(data) {
    if (!measureState.active) return;
    var pt = data.points[0];
    if (!pt) return;
    // Only accept clicks on price panel (yaxis "y")
    var ya = pt.data.yaxis || "y";
    if (ya !== "y") return;
    var price = pt.y;
    var timeStr = pt.x;
    if (measureState.startY === null) {
      // First click: mark point A
      measureState.startY = price;
      measureState.startX = timeStr;
      clearMeasureShapes(chartDiv);
      // Draw horizontal line at A
      var layout = chartDiv.layout;
      var shapes = layout.shapes ? layout.shapes.slice() : [];
      shapes.push({
        type: "line", x0: 0, x1: 1, xref: "x domain", y0: price, y1: price, yref: "y",
        line: {color: "#58a6ff", width: 1, dash: "dash"}, name: "_measure"
      });
      Plotly.relayout(chartDiv, {shapes: shapes});
      showMeasureLabel("A: " + price.toFixed(6) + "  (click B)");
    } else {
      // Second click: mark point B, show delta
      var delta = price - measureState.startY;
      var pct = ((delta / measureState.startY) * 100).toFixed(3);
      var sign = delta >= 0 ? "+" : "";
      var midY = (price + measureState.startY) / 2;
      // Draw line at B + vertical connector + result annotation
      var layout = chartDiv.layout;
      var shapes = layout.shapes ? layout.shapes.slice() : [];
      shapes.push({
        type: "line", x0: 0, x1: 1, xref: "x domain", y0: price, y1: price, yref: "y",
        line: {color: "#58a6ff", width: 1, dash: "dash"}, name: "_measure"
      });
      // Vertical connector between A and B at the clicked x
      shapes.push({
        type: "line", x0: timeStr, x1: timeStr, y0: measureState.startY, y1: price,
        xref: "x", yref: "y",
        line: {color: "#58a6ff", width: 1.5, dash: "dot"}, name: "_measure"
      });
      Plotly.relayout(chartDiv, {shapes: shapes});
      // Add result annotation at midpoint
      var annotations = layout.annotations ? layout.annotations.slice() : [];
      var resultText = sign + delta.toFixed(6) + " (" + sign + pct + "%)";
      annotations.push({
        x: timeStr, y: midY, xref: "x", yref: "y",
        text: resultText, showarrow: false,
        font: {size: 11, color: "#58a6ff", family: "Courier New"},
        bgcolor: "rgba(13,17,23,0.9)", bordercolor: "#58a6ff", borderwidth: 1, borderpad: 4,
        name: "_measure"
      });
      Plotly.relayout(chartDiv, {annotations: annotations});
      showMeasureLabel(resultText);
      measureState.startY = null;
      measureState.startX = null;
    }
  });
}

function clearMeasureShapes(chartDiv) {
  if (!chartDiv || !chartDiv.layout) return;
  // Remove shapes tagged as measure
  var shapes = (chartDiv.layout.shapes || []).filter(function(s) { return s.name !== "_measure"; });
  var annotations = (chartDiv.layout.annotations || []).filter(function(a) { return a.name !== "_measure"; });
  Plotly.relayout(chartDiv, {shapes: shapes, annotations: annotations});
}

function showMeasureLabel(text) {
  var el = document.getElementById("measure-label");
  el.textContent = text;
  el.style.display = "inline";
}

function toggleMeasure() {
  // Turn off pin if on
  if (pinState.active) togglePinMode();
  measureState.active = !measureState.active;
  measureState.startY = null;
  measureState.startX = null;
  var btn = document.getElementById("measure-btn");
  btn.style.background = measureState.active ? "#da3633" : "#238636";
  btn.textContent = measureState.active ? "Measure: ON" : "Measure";
  if (!measureState.active) {
    // Clear measure visuals from current chart
    var page = document.getElementById("trade-page-" + currentPage);
    if (page) {
      var cd = page.querySelector(".js-plotly-plot");
      if (cd) clearMeasureShapes(cd);
    }
    document.getElementById("measure-label").style.display = "none";
  }
}

// --- Pin tool ---
var pinState = { active: false, count: 0 };
var PIN_COLORS = ["#e6db74", "#66d9ef", "#f92672", "#a6e22e", "#fd971f", "#ae81ff", "#56b6c2", "#c678dd"];

function pinKey(n) { return "bingx_pins_" + REPORT_DATE + "_" + n; }

function togglePinMode() {
  // Turn off measure if on
  if (measureState.active) toggleMeasure();
  pinState.active = !pinState.active;
  var btn = document.getElementById("pin-btn");
  btn.style.background = pinState.active ? "#da3633" : "#6e40c9";
  btn.textContent = pinState.active ? "Pin: ON" : "Pin";
}

function getTraceValuesAtX(chartDiv, xVal) {
  // Look up all named trace values at x coordinate
  var readings = {};
  var NAMED = ["EMA 55","EMA 89","AVWAP","AVWAP Hi","AVWAP Lo",
               "K9","K14","K40","D40","K60","D60",
               "TDI Fast","TDI Slow","TDI MBL","TDI VB Hi","TDI VB Lo"];
  for (var i = 0; i < chartDiv.data.length; i++) {
    var tr = chartDiv.data[i];
    var nm = tr.name || "";
    if (NAMED.indexOf(nm) === -1) continue;
    if (!tr.x || !tr.y) continue;
    // Find matching x index
    for (var j = 0; j < tr.x.length; j++) {
      if (tr.x[j] === xVal) {
        var v = tr.y[j];
        if (v !== null && v !== undefined && !isNaN(v)) {
          readings[nm] = v;
        }
        break;
      }
    }
  }
  return readings;
}

function initPinTool(chartDiv) {
  if (!chartDiv) return;
  chartDiv.on("plotly_click", function(data) {
    if (!pinState.active) return;
    var pt = data.points[0];
    if (!pt) return;
    pinState.count++;
    var pinNum = pinState.count;
    var pinColor = PIN_COLORS[(pinNum - 1) % PIN_COLORS.length];
    var yVal = pt.y;
    var xVal = pt.x;
    // Determine which panel was clicked
    var yaxis = pt.data.yaxis || "y";
    var panelNames = {"y": "Price", "y2": "Stoch9", "y3": "Stoch14", "y4": "TDI", "y5": "Stoch40", "y6": "Stoch60"};
    var panelName = panelNames[yaxis] || "Price";
    // Add annotation on chart
    var annot = {
      x: xVal, y: yVal, xref: pt.data.xaxis || "x", yref: yaxis,
      text: "P" + pinNum, showarrow: true, arrowhead: 2, arrowsize: 1, arrowwidth: 1.5,
      arrowcolor: pinColor, font: {size: 10, color: pinColor, family: "Courier New"},
      bgcolor: "rgba(13,17,23,0.85)", bordercolor: pinColor, borderwidth: 1, borderpad: 2
    };
    var layout = chartDiv.layout;
    var annotations = layout.annotations ? layout.annotations.slice() : [];
    annotations.push(annot);
    Plotly.relayout(chartDiv, {annotations: annotations});
    // Collect ALL indicator values at this x coordinate
    var readings = getTraceValuesAtX(chartDiv, xVal);
    // Build pin reference with full readings
    var lines = [];
    lines.push("[P" + pinNum + " " + panelName + " " + xVal + "]");
    // Group readings by panel
    var priceKeys = ["EMA 55","EMA 89","AVWAP","AVWAP Hi","AVWAP Lo"];
    var stochKeys = ["K9","K14","K40","D40","K60","D60"];
    var tdiKeys = ["TDI Fast","TDI Slow","TDI MBL","TDI VB Hi","TDI VB Lo"];
    var pParts = [];
    for (var k = 0; k < priceKeys.length; k++) {
      if (readings[priceKeys[k]] !== undefined) pParts.push(priceKeys[k] + ":" + readings[priceKeys[k]].toFixed(6));
    }
    if (pParts.length) lines.push("  " + pParts.join(" | "));
    var sParts = [];
    for (var k = 0; k < stochKeys.length; k++) {
      if (readings[stochKeys[k]] !== undefined) sParts.push(stochKeys[k] + ":" + readings[stochKeys[k]].toFixed(1));
    }
    if (sParts.length) lines.push("  " + sParts.join(" | "));
    var tParts = [];
    for (var k = 0; k < tdiKeys.length; k++) {
      if (readings[tdiKeys[k]] !== undefined) tParts.push(tdiKeys[k] + ":" + readings[tdiKeys[k]].toFixed(1));
    }
    if (tParts.length) lines.push("  " + tParts.join(" | "));
    var pinRef = lines.join("\\n");
    // Insert into notes textarea
    var ta = document.getElementById("notes-textarea");
    var cursorPos = ta.selectionStart || ta.value.length;
    var before = ta.value.substring(0, cursorPos);
    var after = ta.value.substring(cursorPos);
    var sep = (before.length > 0 && before[before.length - 1] !== "\\n") ? "\\n" : "";
    ta.value = before + sep + pinRef + "\\n" + after;
    updatePreview();
    updateCharCount();
    // Save pin data to localStorage
    savePins(chartDiv);
  });
}

function savePins(chartDiv) {
  if (!chartDiv || !chartDiv.layout) return;
  var annotations = chartDiv.layout.annotations || [];
  var pins = [];
  for (var i = 0; i < annotations.length; i++) {
    var a = annotations[i];
    if (a.text && a.text.match && a.text.match(/^P\\d+$/)) {
      pins.push({x: a.x, y: a.y, xref: a.xref, yref: a.yref, text: a.text,
                 arrowcolor: a.arrowcolor, font_color: a.font ? a.font.color : "#e6db74",
                 bordercolor: a.bordercolor});
    }
  }
  localStorage.setItem(pinKey(currentPage), JSON.stringify(pins));
}

function loadPins(chartDiv) {
  if (!chartDiv) return;
  var saved = localStorage.getItem(pinKey(currentPage));
  if (!saved) { pinState.count = 0; return; }
  var pins;
  try { pins = JSON.parse(saved); } catch(e) { pinState.count = 0; return; }
  if (!pins || !pins.length) { pinState.count = 0; return; }
  var layout = chartDiv.layout;
  var annotations = layout.annotations ? layout.annotations.slice() : [];
  var maxPin = 0;
  for (var i = 0; i < pins.length; i++) {
    var p = pins[i];
    var num = parseInt(p.text.replace("P", ""), 10);
    if (num > maxPin) maxPin = num;
    annotations.push({
      x: p.x, y: p.y, xref: p.xref, yref: p.yref,
      text: p.text, showarrow: true, arrowhead: 2, arrowsize: 1, arrowwidth: 1.5,
      arrowcolor: p.arrowcolor || p.bordercolor, font: {size: 10, color: p.font_color || p.arrowcolor, family: "Courier New"},
      bgcolor: "rgba(13,17,23,0.85)", bordercolor: p.bordercolor || p.arrowcolor, borderwidth: 1, borderpad: 2
    });
  }
  pinState.count = maxPin;
  Plotly.relayout(chartDiv, {annotations: annotations});
}

function clearPins() {
  var page = document.getElementById("trade-page-" + currentPage);
  if (!page) return;
  var chartDiv = page.querySelector(".js-plotly-plot");
  if (!chartDiv || !chartDiv.layout) return;
  var annotations = chartDiv.layout.annotations || [];
  var kept = [];
  for (var i = 0; i < annotations.length; i++) {
    var a = annotations[i];
    if (!(a.text && a.text.match && a.text.match(/^P\\d+$/))) {
      kept.push(a);
    }
  }
  Plotly.relayout(chartDiv, {annotations: kept});
  localStorage.removeItem(pinKey(currentPage));
  pinState.count = 0;
}

// --- Init on load ---
window.addEventListener("load", function() {
  // highlight first sidebar link
  var firstLink = document.getElementById("sidebar-link-1");
  if (firstLink) firstLink.classList.add("active");
  // load notes from server (falls back to localStorage)
  loadAllNotesFromServer();
  // load toggle states for first trade
  loadToggleStates();
  // init measure + pin tools on first chart
  var page1 = document.getElementById("trade-page-1");
  if (page1) {
    var cd = page1.querySelector(".js-plotly-plot");
    if (cd) { initMeasureTool(cd); initPinTool(cd); loadPins(cd); }
  }
});
"""


# ---------------------------------------------------------------------------
# Notes Server
# ---------------------------------------------------------------------------

NOTES_PORT = 9234


def make_notes_handler(notes_file, serve_dir):
    """Create HTTP handler class that serves files and handles note save/load API."""

    class NotesHandler(SimpleHTTPRequestHandler):
        """HTTP handler for serving report + note persistence API."""

        def __init__(self, *args, **kwargs):
            """Init with serve directory."""
            super().__init__(*args, directory=str(serve_dir), **kwargs)

        def log_message(self, fmt, *args):
            """Suppress default access logs."""
            pass

        def do_OPTIONS(self):
            """Handle CORS preflight."""
            self.send_response(200)
            self._cors_headers()
            self.end_headers()

        def do_GET(self):
            """Handle GET -- serve files or load notes."""
            if self.path == "/api/load-notes":
                self._load_notes()
            else:
                super().do_GET()

        def do_POST(self):
            """Handle POST -- save note."""
            if self.path == "/api/save-note":
                self._save_note()
            else:
                self.send_response(404)
                self.end_headers()

        def _cors_headers(self):
            """Add CORS headers."""
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _load_notes(self):
            """Return all saved notes as JSON."""
            data = {}
            if Path(notes_file).exists():
                try:
                    data = json.loads(Path(notes_file).read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        def _save_note(self):
            """Save a single trade note to disk."""
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                trade_num = str(body.get("trade", ""))
                note_text = body.get("note", "")
                # Load existing
                data = {}
                if Path(notes_file).exists():
                    try:
                        data = json.loads(Path(notes_file).read_text(encoding="utf-8"))
                    except Exception:
                        data = {}
                data[trade_num] = note_text
                Path(notes_file).write_text(json.dumps(data, indent=2), encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._cors_headers()
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(500)
                self._cors_headers()
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))

    return NotesHandler


def start_notes_server(notes_file, serve_dir, port=NOTES_PORT):
    """Start the notes HTTP server in a daemon thread. Returns the server."""
    handler_cls = make_notes_handler(notes_file, serve_dir)
    server = HTTPServer(("127.0.0.1", port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Run the trade chart report generator v2."""
    parser = argparse.ArgumentParser(description="Trade Chart Report v2")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"),
                        help="Filter trades from this date (YYYY-MM-DD, default: today)")
    parser.add_argument("--from-time", default=None,
                        help="Filter start time within date (HH:MM)")
    parser.add_argument("--symbol", default=None,
                        help="Filter to one symbol only")
    parser.add_argument("--no-api", action="store_true",
                        help="Skip live kline fetch; use CSV data only")
    args = parser.parse_args()

    target_date = args.date
    from_time = args.from_time
    symbol_filter = args.symbol
    no_api = args.no_api

    # Load config
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    demo_mode = cfg.get("connector", {}).get("demo_mode", False)
    base_url = "https://open-api-vst.bingx.com" if demo_mode else "https://open-api.bingx.com"

    # Load credentials
    api_key = ""
    secret_key = ""
    if not no_api:
        if load_dotenv is not None:
            load_dotenv(ROOT / ".env")
        api_key = os.getenv("BINGX_API_KEY", "")
        secret_key = os.getenv("BINGX_SECRET_KEY", "")
        if not api_key or not secret_key:
            log.warning("Missing API credentials -- falling back to --no-api mode")
            no_api = True

    # Load and filter trades
    trades = load_and_filter_trades(target_date, from_time, symbol_filter)
    if not trades:
        print("No trades found for " + target_date)
        sys.exit(0)

    log.info("Processing %d trades for %s", len(trades), target_date)

    # Process each trade
    trades_info = []
    charts_html = []

    for idx, trade in enumerate(trades, 1):
        symbol = trade.get("symbol", "")
        entry_time = trade.get("entry_time", "")
        exit_time = trade.get("timestamp", "")
        pnl = safe_float(trade.get("pnl_net"))

        info = {
            "symbol": symbol,
            "direction": trade.get("direction", ""),
            "grade": trade.get("grade", ""),
            "entry_time": entry_time,
            "exit_time": exit_time,
            "exit_reason": trade.get("exit_reason", ""),
            "pnl": pnl,
        }
        trades_info.append(info)

        if no_api:
            charts_html.append('<div class="no-chart">No chart data available (--no-api mode)</div>')
            continue

        # Fetch klines -- 120 bars pre-entry for stoch 40/60 history (Change 3)
        entry_ms = to_ms(entry_time)
        exit_ms = to_ms(exit_time)
        if entry_ms == 0:
            charts_html.append('<div class="no-chart">Invalid entry time</div>')
            continue

        candle_ms = 5 * 60 * 1000
        start_ms = entry_ms - (120 * candle_ms)
        end_ms = exit_ms + (20 * candle_ms) if exit_ms > 0 else entry_ms + (140 * candle_ms)

        log.info("[%d/%d] Fetching klines for %s ...", idx, len(trades), symbol)
        klines = fetch_klines(symbol, start_ms, end_ms, base_url, api_key, secret_key)
        time.sleep(0.3)

        if not klines:
            charts_html.append('<div class="no-chart">No kline data returned for ' + symbol + "</div>")
            continue

        # Build DataFrame from klines
        kline_df = pd.DataFrame(klines)
        for col in ["open", "high", "low", "close", "volume"]:
            if col in kline_df.columns:
                kline_df[col] = kline_df[col].astype(float)
        kline_df["time"] = kline_df["time"].astype(int)
        kline_df = kline_df.sort_values("time").reset_index(drop=True)
        kline_df["time_dt"] = pd.to_datetime(kline_df["time"], unit="ms", utc=True)
        kline_df["time_str"] = kline_df["time_dt"].dt.strftime("%Y-%m-%d %H:%M")

        # Find entry/exit bar indices
        diffs_entry = np.abs(kline_df["time"].values - entry_ms)
        entry_idx = int(np.argmin(diffs_entry))
        diffs_exit = np.abs(kline_df["time"].values - exit_ms) if exit_ms > 0 else diffs_entry
        exit_idx = int(np.argmin(diffs_exit))

        trade["_entry_bar_time"] = kline_df.iloc[entry_idx]["time_str"]
        trade["_exit_bar_time"] = kline_df.iloc[exit_idx]["time_str"]
        trade["_entry_idx"] = entry_idx
        trade["_exit_idx"] = exit_idx

        # Compute indicators (includes AVWAP anchored at EMA cross)
        kline_df = compute_indicators(kline_df, entry_idx)

        # Detect Four Pillars signals
        has_signals = detect_signals(kline_df, cfg)

        # Build chart
        fig = build_trade_chart(trade, kline_df, idx, has_signals)
        chart_html = pio.to_html(fig, full_html=False, include_plotlyjs=False)
        charts_html.append(chart_html)

        log.info("[%d/%d] %s chart built (%d bars)", idx, len(trades), symbol, len(kline_df))

    # Build HTML report
    html_content = build_html_report(trades_info, charts_html, target_date, from_time or "00:00")

    # Write output
    LOG_DIR.mkdir(exist_ok=True)
    out_path = LOG_DIR / ("trade_chart_report_" + target_date + ".html")
    out_path.write_text(html_content, encoding="utf-8")
    log.info("Report written: %s", out_path)

    # Notes file on disk (JSON)
    notes_file = str(LOG_DIR / ("trade_notes_" + target_date + ".json"))
    log.info("Notes file: %s", notes_file)

    # Start local server for auto-saving notes
    report_filename = out_path.name
    server = start_notes_server(notes_file, str(LOG_DIR), NOTES_PORT)
    serve_url = "http://127.0.0.1:" + str(NOTES_PORT) + "/" + report_filename
    log.info("Serving at %s", serve_url)

    # Open in Brave browser
    brave_paths = [
        Path(os.environ.get("PROGRAMFILES", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe",
    ]
    brave_exe = None
    for bp in brave_paths:
        if bp.exists():
            brave_exe = str(bp)
            break
    if brave_exe:
        log.info("Opening report in Brave...")
        subprocess.Popen([brave_exe, serve_url])
    else:
        log.warning("Brave not found -- open manually: %s", serve_url)

    print("Done. Notes auto-save to: " + notes_file)
    print("Server running at " + serve_url + " -- Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
