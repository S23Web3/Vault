"""
Enhanced Per-Coin Analysis -- Extended metrics and drill-down data.
Computes 10 additional metrics beyond the base 7.

v3 fixes (2026-02-16):
  - Sortino annualization uses bar_count (not trade count)
  - compute_monthly_pnl maps entry_bar through datetime_index
  - compute_commission_breakdown: rebate removed (not in Trade384)
  - Added be_raised to loser detail when available

v3.9 additions (2026-02-16):
  - compute_daily_volume_stats: avg/max/min daily trade count and volume
"""
import numpy as np
import pandas as pd


def compute_extended_metrics(trades_df, bar_count=None):
    """Compute 10 extended metrics from a trades DataFrame. Returns dict."""
    if trades_df is None or trades_df.empty:
        return {
            "avg_trade": 0.0, "best_trade": 0.0, "worst_trade": 0.0,
            "sl_pct": 0.0, "tp_pct": 0.0, "scale_pct": 0.0,
            "avg_mfe": 0.0, "avg_mae": 0.0,
            "max_consec_loss": 0, "sortino": 0.0,
        }
    net_col = "net_pnl" if "net_pnl" in trades_df.columns else "pnl"
    pnls = trades_df[net_col].values.astype(float)
    n = len(pnls)

    # Avg / Best / Worst trade
    avg_trade = float(pnls.mean()) if n > 0 else 0.0
    best_trade = float(pnls.max()) if n > 0 else 0.0
    worst_trade = float(pnls.min()) if n > 0 else 0.0

    # Exit reason breakdown
    if "exit_reason" in trades_df.columns:
        reasons = trades_df["exit_reason"].str.upper()
        sl_count = int((reasons == "SL").sum())
        tp_count = int((reasons == "TP").sum())
        scale_count = int(reasons.str.startswith("SCALE").sum())
    else:
        sl_count = tp_count = scale_count = 0
    sl_pct = round(sl_count / n * 100, 1) if n > 0 else 0.0
    tp_pct = round(tp_count / n * 100, 1) if n > 0 else 0.0
    scale_pct = round(scale_count / n * 100, 1) if n > 0 else 0.0

    # MFE / MAE averages
    avg_mfe = float(trades_df["mfe"].mean()) if "mfe" in trades_df.columns and n > 0 else 0.0
    avg_mae = float(trades_df["mae"].mean()) if "mae" in trades_df.columns and n > 0 else 0.0

    # Max consecutive losses
    max_consec = 0
    current = 0
    for p in pnls:
        if p < 0:
            current += 1
            max_consec = max(max_consec, current)
        else:
            current = 0

    # Sortino ratio (annualized for 5m bars, ~105,120 bars/year)
    # FIX BUG6: use bar_count (equity curve length) not trade count
    ann_factor = 105120  # 5m bars per year
    if bar_count is not None and bar_count > 0:
        ann_factor = min(bar_count, 105120)
    downside = pnls[pnls < 0]
    if len(downside) > 1 and pnls.std() > 0:
        downside_std = float(np.std(downside, ddof=1))
        sortino = float(pnls.mean() / downside_std * np.sqrt(ann_factor)) if downside_std > 0 else 0.0
    else:
        sortino = 0.0

    return {
        "avg_trade": round(avg_trade, 2),
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "sl_pct": sl_pct,
        "tp_pct": tp_pct,
        "scale_pct": scale_pct,
        "avg_mfe": round(avg_mfe, 4),
        "avg_mae": round(avg_mae, 4),
        "max_consec_loss": max_consec,
        "sortino": round(sortino, 3),
    }


def compute_grade_distribution(trades_df):
    """Compute grade distribution from trades. Returns dict of grade -> count."""
    if trades_df is None or trades_df.empty or "grade" not in trades_df.columns:
        return {}
    return dict(trades_df["grade"].value_counts().sort_index())


def compute_exit_distribution(trades_df):
    """Compute exit reason distribution. Returns dict of reason -> count."""
    if trades_df is None or trades_df.empty or "exit_reason" not in trades_df.columns:
        return {}
    return dict(trades_df["exit_reason"].value_counts())


def compute_monthly_pnl(trades_df, datetime_index=None):
    """Compute monthly P&L by mapping entry_bar to datetime via datetime_index."""
    if trades_df is None or trades_df.empty:
        return pd.DataFrame(columns=["month", "pnl"])
    net_col = "net_pnl" if "net_pnl" in trades_df.columns else "pnl"
    # FIX BUG5: entry_dt doesnt exist in real trades_df, map entry_bar instead
    if datetime_index is not None and "entry_bar" in trades_df.columns:
        df = trades_df.copy()
        dt_idx = pd.DatetimeIndex(datetime_index)
        max_bar = len(dt_idx) - 1
        bars = df["entry_bar"].clip(0, max_bar).astype(int)
        df["_entry_dt"] = dt_idx[bars]
        df["_month"] = df["_entry_dt"].dt.to_period("M").astype(str)
        monthly = df.groupby("_month")[net_col].sum().reset_index()
        monthly.columns = ["month", "pnl"]
        return monthly
    return pd.DataFrame(columns=["month", "pnl"])


def compute_loser_detail(trades_df):
    """Extract loser trades that saw green with detail. Returns DataFrame."""
    if trades_df is None or trades_df.empty:
        return pd.DataFrame()
    net_col = "net_pnl" if "net_pnl" in trades_df.columns else "pnl"
    losers = trades_df[trades_df[net_col] < 0].copy()
    if losers.empty or "saw_green" not in losers.columns:
        return pd.DataFrame()
    green_losers = losers[losers["saw_green"] == True].copy()
    if green_losers.empty:
        return pd.DataFrame()
    cols = ["direction", "grade", "entry_price", "exit_price", net_col, "mfe", "mae", "exit_reason"]
    available = [c for c in cols if c in green_losers.columns]
    return green_losers[available].round(4)


def compute_commission_breakdown(trades_df):
    """Compute commission breakdown. Returns dict."""
    # FIX BUG4: rebate column does not exist in Trade384/trades_df.
    # Rebates are settled daily at 17:00 UTC by the commission model,
    # not tracked per-trade. Only report gross commission here.
    if trades_df is None or trades_df.empty:
        return {"total_commission": 0.0, "net_commission": 0.0}
    comm = float(trades_df["commission"].sum()) if "commission" in trades_df.columns else 0.0
    return {
        "total_commission": round(comm, 2),
        "net_commission": round(comm, 2),
    }


def compute_daily_volume_stats(trades_df, datetime_index=None, notional=5000.0):
    """Compute daily trade count and volume stats. Returns dict with avg/max/min per day."""
    empty = {
        "avg_trades_per_day": 0.0,
        "max_trades_day": 0,
        "min_trades_day": 0,
        "max_trades_date": "",
        "min_trades_date": "",
        "avg_volume_per_day": 0.0,
        "max_volume_day": 0.0,
        "min_volume_day": 0.0,
        "max_volume_date": "",
        "min_volume_date": "",
        "total_trading_days": 0,
    }
    if trades_df is None or trades_df.empty:
        return empty
    if datetime_index is None or "entry_bar" not in trades_df.columns:
        return empty

    dt_idx = pd.DatetimeIndex(datetime_index)
    max_bar = len(dt_idx) - 1
    df = trades_df.copy()
    bars = df["entry_bar"].clip(0, max_bar).astype(int)
    df["_entry_dt"] = dt_idx[bars]
    df["_date"] = df["_entry_dt"].dt.date

    # Each trade = 2 sides (entry + exit) * notional
    daily_trades = df.groupby("_date").size()
    daily_volume = daily_trades * notional * 2

    total_days = len(daily_trades)
    if total_days == 0:
        return empty

    avg_trades = float(daily_trades.mean())
    max_trades = int(daily_trades.max())
    min_trades = int(daily_trades.min())
    max_t_date = str(daily_trades.idxmax())
    min_t_date = str(daily_trades.idxmin())

    avg_vol = float(daily_volume.mean())
    max_vol = float(daily_volume.max())
    min_vol = float(daily_volume.min())
    max_v_date = str(daily_volume.idxmax())
    min_v_date = str(daily_volume.idxmin())

    return {
        "avg_trades_per_day": round(avg_trades, 1),
        "max_trades_day": max_trades,
        "min_trades_day": min_trades,
        "max_trades_date": max_t_date,
        "min_trades_date": min_t_date,
        "avg_volume_per_day": round(avg_vol, 2),
        "max_volume_day": round(max_vol, 2),
        "min_volume_day": round(min_vol, 2),
        "max_volume_date": max_v_date,
        "min_volume_date": min_v_date,
        "total_trading_days": total_days,
    }
