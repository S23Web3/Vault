"""
Performance metrics: win rate, expectancy, Sharpe, Sortino, MFE/MAE analysis.
"""

import numpy as np
import pandas as pd
from typing import Optional


def compute_metrics(trades: list, equity_curve: Optional[np.ndarray] = None) -> dict:
    """
    Compute comprehensive metrics from a list of Trade objects.

    Returns dict with all key performance stats.
    """
    if not trades:
        return {"total_trades": 0}

    pnls = np.array([t.pnl for t in trades])
    net_pnls = np.array([t.pnl - t.commission for t in trades])
    commissions = np.array([t.commission for t in trades])

    winners = net_pnls[net_pnls > 0]
    losers = net_pnls[net_pnls <= 0]

    total = len(trades)
    win_count = len(winners)
    loss_count = len(losers)
    win_rate = win_count / total if total > 0 else 0

    avg_win = np.mean(winners) if len(winners) > 0 else 0
    avg_loss = np.mean(losers) if len(losers) > 0 else 0
    expectancy = np.mean(net_pnls)

    gross_profit = np.sum(winners) if len(winners) > 0 else 0
    gross_loss = np.abs(np.sum(losers)) if len(losers) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # MFE/MAE
    mfes = np.array([t.mfe for t in trades])
    maes = np.array([t.mae for t in trades])
    saw_green = sum(1 for t in trades if t.saw_green)
    saw_green_losers = sum(1 for t in trades if t.saw_green and t.pnl - t.commission <= 0)
    total_losers = sum(1 for t in trades if t.pnl - t.commission <= 0)
    pct_losers_saw_green = saw_green_losers / total_losers if total_losers > 0 else 0

    # Breakeven raise stats
    be_raised_count = sum(1 for t in trades if t.be_raised)

    # Grade breakdown
    grades = {}
    for grade in ["A", "B", "C", "D", "ADD", "RE", "R"]:
        grade_trades = [t for t in trades if t.grade == grade]
        if grade_trades:
            grade_pnls = [t.pnl - t.commission for t in grade_trades]
            grades[grade] = {
                "count": len(grade_trades),
                "win_rate": sum(1 for p in grade_pnls if p > 0) / len(grade_trades),
                "avg_pnl": np.mean(grade_pnls),
                "total_pnl": np.sum(grade_pnls),
            }

    # Sharpe / Sortino (annualized from per-trade)
    if len(net_pnls) > 1:
        sharpe = np.mean(net_pnls) / np.std(net_pnls) if np.std(net_pnls) > 0 else 0
        downside = net_pnls[net_pnls < 0]
        downside_std = np.std(downside) if len(downside) > 1 else 1
        sortino = np.mean(net_pnls) / downside_std if downside_std > 0 else 0
    else:
        sharpe = 0
        sortino = 0

    # Max drawdown from equity curve
    max_dd = 0
    max_dd_pct = 0
    if equity_curve is not None and len(equity_curve) > 0:
        peak = np.maximum.accumulate(equity_curve)
        drawdown = peak - equity_curve
        max_dd = np.max(drawdown)
        max_dd_pct = np.max(drawdown / peak) * 100 if np.max(peak) > 0 else 0

    return {
        "total_trades": total,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": profit_factor,
        "net_pnl": np.sum(net_pnls),
        "total_commission": np.sum(commissions),
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd_pct,
        "avg_mfe": np.mean(mfes),
        "avg_mae": np.mean(maes),
        "pct_losers_saw_green": pct_losers_saw_green,
        "saw_green_losers": saw_green_losers,
        "total_losers": total_losers,
        "be_raised_count": be_raised_count,
        "grades": grades,
    }


def trades_to_dataframe(trades: list) -> pd.DataFrame:
    """Convert list of Trade objects to a DataFrame."""
    if not trades:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            "direction": t.direction,
            "grade": t.grade,
            "entry_bar": t.entry_bar,
            "exit_bar": t.exit_bar,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "sl_price": t.sl_price,
            "tp_price": t.tp_price,
            "pnl": t.pnl,
            "commission": t.commission,
            "net_pnl": t.pnl - t.commission,
            "mfe": t.mfe,
            "mae": t.mae,
            "exit_reason": t.exit_reason,
            "saw_green": t.saw_green,
            "be_raised": t.be_raised,
        }
        for t in trades
    ])
