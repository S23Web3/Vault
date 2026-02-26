"""
Vince Screener Engine v1 -- pure logic, no Streamlit.
Sweeps cached coins, scores each against ATR ratio, PnL, volume, trade count.
Run standalone tests: python tests/test_screener_engine.py
From: C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester
"""
import logging
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

log = logging.getLogger(__name__)

MIN_BARS = 200  # minimum bars after lookback filter before running backtest

DEFAULT_THRESHOLDS = {
    "min_atr_ratio": 0.003,
    "min_net_pnl": 0.0,
    "min_avg_daily_vol_usd": 1_000_000.0,
    "min_trades": 3,
}

# Matches dashboard_v392.py sidebar defaults
DEFAULT_SIGNAL_PARAMS = {
    "atr_length": 14,
    "cross_level": 25,
    "zone_level": 30,
    "stage_lookback": 10,
    "allow_b_trades": True,
    "allow_c_trades": True,
    "b_open_fresh": True,
    "cloud2_reentry": True,
    "reentry_lookback": 10,
    "stoch_k1": 9,
    "stoch_k2": 14,
    "stoch_k3": 40,
    "stoch_k4": 60,
    "stoch_d_smooth": 10,
    "cloud2_fast": 5,
    "cloud2_slow": 12,
    "cloud3_fast": 34,
    "cloud3_slow": 50,
    "cloud4_fast": 72,
    "cloud4_slow": 89,
}

# Matches dashboard_v392.py sidebar defaults: margin=500, leverage=20, rebate=70%
DEFAULT_BT_PARAMS = {
    "sl_mult": 2.5,
    "tp_mult": 2.0,
    "cooldown": 3,
    "b_open_fresh": True,
    "notional": 10000.0,
    "commission_rate": 0.0008,
    "maker_rate": 0.0002,
    "rebate_pct": 0.70,
    "initial_equity": 10000.0,
    "max_positions": 4,
    "checkpoint_interval": 5,
    "max_scaleouts": 2,
    "sigma_floor_atr": 0.5,
    "enable_adds": True,
    "enable_reentry": True,
    "be_trigger_atr": 0.0,
    "be_lock_atr": 0.0,
}


def to_bingx_symbol(symbol: str) -> str:
    """Convert backtester symbol to BingX dash format. RIVERUSDT -> RIVER-USDT."""
    if symbol.endswith("USDT"):
        return symbol[:-4] + "-USDT"
    return symbol


def _filter_lookback(df: pd.DataFrame, lookback_days: int) -> pd.DataFrame:
    """Filter DataFrame to last N calendar days from UTC now."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    cutoff_ts = pd.Timestamp(cutoff)
    if "datetime" in df.columns:
        dt_col = pd.to_datetime(df["datetime"], utc=True)
        mask = dt_col >= cutoff_ts
        return df[mask].reset_index(drop=True)
    if isinstance(df.index, pd.DatetimeIndex):
        idx = df.index.tz_localize("UTC") if df.index.tz is None else df.index
        return df[idx >= cutoff_ts].reset_index(drop=True)
    log.warning("No datetime column or DatetimeIndex found -- returning full DataFrame")
    return df


def screen_coin(
    symbol: str,
    cache_dir: Path,
    lookback_days: int,
    signal_params: dict,
    bt_params: dict,
    thresholds: dict,
) -> dict:
    """Screen one coin. Returns metric dict with eligible flag and pass/fail per criterion."""
    # Late imports so callers can set sys.path before importing backtester modules
    from signals.four_pillars_v383_v2 import compute_signals_v383
    from engine.backtester_v384 import Backtester384

    result = {
        "symbol": symbol,
        "atr_ratio": float("nan"),
        "net_pnl_30d": float("nan"),
        "avg_daily_vol_usd": float("nan"),
        "trade_count": 0,
        "pass_atr": False,
        "pass_pnl": False,
        "pass_vol": False,
        "pass_trades": False,
        "score": 0.0,
        "eligible": False,
        "error": None,
    }

    try:
        parquet_path = cache_dir / (symbol + "_1m.parquet")
        if not parquet_path.exists():
            result["error"] = "no_cache"
            log.warning("SKIP %s: parquet not found at %s", symbol, parquet_path)
            return result

        df = pd.read_parquet(parquet_path)

        # Normalise column names -- matches dashboard_v392 load_data behaviour
        if "volume" in df.columns and "base_vol" not in df.columns:
            df = df.rename(columns={"volume": "base_vol"})
        if "turnover" in df.columns and "quote_vol" not in df.columns:
            df = df.rename(columns={"turnover": "quote_vol"})

        df = _filter_lookback(df, lookback_days)

        if len(df) < MIN_BARS:
            result["error"] = "too_few_bars:" + str(len(df))
            log.warning("SKIP %s: %d bars after filter (need %d)", symbol, len(df), MIN_BARS)
            return result

        # Volume metric: avg daily USD volume (quote_vol per 1m bar * 1440 bars/day)
        if "quote_vol" in df.columns:
            avg_daily_vol = float(df["quote_vol"].mean()) * 1440
        else:
            avg_daily_vol = 0.0
            log.warning("%s: no quote_vol column -- volume set to 0", symbol)
        result["avg_daily_vol_usd"] = avg_daily_vol

        # Signal pipeline (same as dashboard run_backtest)
        df_sig = compute_signals_v383(df.copy(), signal_params)

        # ATR ratio: mean(atr) / mean(close) -- commission viability proxy
        if "atr" in df_sig.columns and "close" in df_sig.columns:
            valid = df_sig[["atr", "close"]].dropna()
            if len(valid) > 0:
                atr_ratio = float(valid["atr"].mean() / valid["close"].mean())
            else:
                atr_ratio = 0.0
        else:
            atr_ratio = 0.0
            log.warning("%s: atr or close column missing after signals", symbol)
        result["atr_ratio"] = atr_ratio

        # Backtest (same as dashboard run_backtest)
        bt_results = Backtester384(bt_params).run(df_sig)
        metrics = bt_results["metrics"]
        net_pnl = float(metrics.get("net_pnl", 0.0))
        trade_count = int(metrics.get("total_trades", 0))
        result["net_pnl_30d"] = net_pnl
        result["trade_count"] = trade_count

        # Pass/fail per criterion
        min_atr = thresholds.get("min_atr_ratio", DEFAULT_THRESHOLDS["min_atr_ratio"])
        min_pnl = thresholds.get("min_net_pnl", DEFAULT_THRESHOLDS["min_net_pnl"])
        min_vol = thresholds.get("min_avg_daily_vol_usd", DEFAULT_THRESHOLDS["min_avg_daily_vol_usd"])
        min_tr = thresholds.get("min_trades", DEFAULT_THRESHOLDS["min_trades"])

        result["pass_atr"] = bool(atr_ratio > min_atr)
        result["pass_pnl"] = bool(net_pnl > min_pnl)
        result["pass_vol"] = bool(avg_daily_vol > min_vol)
        result["pass_trades"] = bool(trade_count >= min_tr)
        result["eligible"] = all([
            result["pass_atr"],
            result["pass_pnl"],
            result["pass_vol"],
            result["pass_trades"],
        ])

        # Score: 0-4 criteria passed + normalised PnL tiebreak (0.0-0.1)
        criteria_score = sum([
            result["pass_atr"],
            result["pass_pnl"],
            result["pass_vol"],
            result["pass_trades"],
        ])
        result["score"] = float(criteria_score) + min(max(net_pnl, 0.0), 1000.0) / 10000.0

        log.info(
            "%s  atr=%.4f  pnl=$%.0f  vol=$%.0fM  trades=%d  eligible=%s",
            symbol, atr_ratio, net_pnl, avg_daily_vol / 1_000_000,
            trade_count, result["eligible"],
        )

    except Exception as e:
        result["error"] = str(e)
        log.error("FAIL %s: %s", symbol, e)
        log.debug(traceback.format_exc())

    return result


def run_screener(
    symbols: list,
    cache_dir: Path,
    lookback_days: int = 30,
    signal_params: dict = None,
    bt_params: dict = None,
    thresholds: dict = None,
) -> pd.DataFrame:
    """Screen all symbols. Return DataFrame ranked by score descending."""
    sig_p = signal_params if signal_params is not None else DEFAULT_SIGNAL_PARAMS
    bt_p = bt_params if bt_params is not None else DEFAULT_BT_PARAMS
    th_p = thresholds if thresholds is not None else DEFAULT_THRESHOLDS

    rows = []
    for i, sym in enumerate(symbols, 1):
        log.info("[%d/%d] %s", i, len(symbols), sym)
        rows.append(screen_coin(sym, cache_dir, lookback_days, sig_p, bt_p, th_p))

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df.sort_values("score", ascending=False).reset_index(drop=True)
