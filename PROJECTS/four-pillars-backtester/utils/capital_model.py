"""
Unified Capital Model -- Post-processing filter for portfolio capital constraints.
Two modes: Per-Coin Independent vs Unified Portfolio Pool.

v3 fixes (2026-02-16):
  - Bar indices mapped through datetime_index to master_dt (cross-coin safe)
  - MFE removed from signal strength (was look-ahead bias)
  - Equity curves rebuilt after rejecting trades (not decorative)
  - Capital efficiency computed from accepted trades only
"""
import numpy as np
import pandas as pd
from datetime import datetime


# Grade priority: A is strongest signal, R is weakest
GRADE_PRIORITY = {"A": 0, "B": 1, "C": 2, "D": 3, "ADD": 4, "RE": 5, "R": 6}


def _grade_sort_key(grade_str):
    """Return numeric priority for a trade grade (lower = higher priority)."""
    return GRADE_PRIORITY.get(str(grade_str).upper(), 99)


def _map_bar_to_master(bar_idx, coin_dt_index, master_dt):
    """Map a per-coin bar index to the corresponding master_dt index."""
    coin_dt = pd.DatetimeIndex(coin_dt_index)
    if bar_idx < 0 or bar_idx >= len(coin_dt):
        bar_idx = max(0, min(bar_idx, len(coin_dt) - 1))
    target_dt = coin_dt[bar_idx]
    # Find nearest position in master_dt
    pos = master_dt.searchsorted(target_dt, side="left")
    if pos >= len(master_dt):
        pos = len(master_dt) - 1
    return int(pos)


def _rebuild_metrics_from_df(tdf, eq_curve, orig_metrics, notional):
    """Rebuild key metrics dict fields from a filtered trades DataFrame."""
    if tdf is None or tdf.empty:
        m = dict(orig_metrics)
        m["total_trades"] = 0
        m["win_count"] = 0
        m["loss_count"] = 0
        m["win_rate"] = 0
        m["net_pnl"] = 0
        m["total_commission"] = 0
        m["total_volume"] = 0
        m["total_sides"] = 0
        m["total_rebate"] = 0
        m["net_pnl_after_rebate"] = 0
        m["sharpe"] = 0
        m["sortino"] = 0
        m["profit_factor"] = 0
        m["max_drawdown_pct"] = 0
        m["pct_losers_saw_green"] = 0
        return m

    net_col = "net_pnl" if "net_pnl" in tdf.columns else "pnl"
    pnls = tdf[net_col].values.astype(float)
    commissions = tdf["commission"].values.astype(float) if "commission" in tdf.columns else np.zeros(len(tdf))

    total = len(tdf)
    winners = pnls[pnls > 0]
    losers = pnls[pnls <= 0]
    win_count = len(winners)
    loss_count = len(losers)
    win_rate = win_count / total if total > 0 else 0

    gross_profit = float(np.sum(winners)) if len(winners) > 0 else 0
    gross_loss = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Sharpe / Sortino
    if len(pnls) > 1 and np.std(pnls) > 0:
        sharpe = float(np.mean(pnls) / np.std(pnls))
        downside = pnls[pnls < 0]
        ds_std = float(np.std(downside)) if len(downside) > 1 else 1.0
        sortino = float(np.mean(pnls) / ds_std) if ds_std > 0 else 0
    else:
        sharpe = 0
        sortino = 0

    # Max drawdown from equity curve
    max_dd_pct = 0
    if eq_curve is not None and len(eq_curve) > 0:
        peak = np.maximum.accumulate(eq_curve)
        dd_pct_arr = np.where(peak > 0, (peak - eq_curve) / peak * 100, 0)
        max_dd_pct = float(np.max(dd_pct_arr))

    # LSG
    total_losers = loss_count
    saw_green_losers = 0
    if "saw_green" in tdf.columns:
        loser_mask = pnls <= 0
        sg_col = tdf["saw_green"].values
        saw_green_losers = int(np.sum(sg_col[loser_mask]))
    pct_lsg = saw_green_losers / total_losers if total_losers > 0 else 0

    # Volume/rebate: scale proportionally from original
    accepted_comm = float(np.sum(commissions))
    orig_comm = orig_metrics.get("total_commission", 0)
    if orig_comm > 0:
        comm_ratio = accepted_comm / orig_comm
    else:
        comm_ratio = 1.0
    total_rebate = orig_metrics.get("total_rebate", 0) * comm_ratio
    total_volume = total * notional * 2  # each trade = 2 sides
    total_sides = total * 2

    m = dict(orig_metrics)
    m["total_trades"] = total
    m["win_count"] = win_count
    m["loss_count"] = loss_count
    m["win_rate"] = win_rate
    m["net_pnl"] = float(np.sum(pnls))
    m["total_commission"] = accepted_comm
    m["total_volume"] = total_volume
    m["total_sides"] = total_sides
    m["total_rebate"] = total_rebate
    m["net_pnl_after_rebate"] = float(np.sum(pnls)) + total_rebate
    m["sharpe"] = sharpe
    m["sortino"] = sortino
    m["profit_factor"] = profit_factor
    m["max_drawdown_pct"] = max_dd_pct
    m["pct_losers_saw_green"] = pct_lsg
    m["gross_profit"] = gross_profit
    m["gross_loss"] = gross_loss
    return m


def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos, notional=None):
    """
    Post-process portfolio results to enforce unified capital constraints.
    Filters out trades that would exceed total_capital.
    Rebuilds equity curves, trades_df, and metrics from accepted trades only.
    Returns dict with adjusted results and rejection log.
    """
    if notional is None:
        notional = margin_per_pos * 10  # fallback: assume 10x leverage
    if total_capital is None or total_capital <= 0:
        return {
            "adjusted_pf": pf_data,
            "adjusted_coin_results": coin_results,
            "capital_used": pf_data["capital_allocated"],
            "rejected_count": 0,
            "rejection_log": [],
            "missed_pnl": 0.0,
            "capital_efficiency": {
                "total_capital": 0,
                "peak_used": float(pf_data["capital_allocated"].max()),
                "peak_pct": 0.0,
                "avg_used": float(pf_data["capital_allocated"].mean()),
                "avg_pct": 0.0,
                "idle_pct": 0.0,
                "trades_rejected": 0,
                "rejection_pct": 0.0,
                "missed_pnl": 0.0,
            },
        }

    master_dt = pf_data["master_dt"]
    n_bars = len(master_dt)

    # Collect all trade entry/exit events with MAPPED timestamps
    # FIX BUG2: map per-coin bar indices to master_dt positions
    events = []
    for cr in coin_results:
        sym = cr["symbol"]
        tdf = cr.get("trades_df")
        coin_dt_idx = cr["datetime_index"]
        if tdf is None or tdf.empty:
            continue
        for row_idx, row in tdf.iterrows():
            entry_bar_local = int(row.get("entry_bar", 0))
            exit_bar_local = int(row.get("exit_bar", len(coin_dt_idx) - 1))
            # Map to master_dt positions
            entry_bar_master = _map_bar_to_master(entry_bar_local, coin_dt_idx, master_dt)
            exit_bar_master = _map_bar_to_master(exit_bar_local, coin_dt_idx, master_dt)
            grade = str(row.get("grade", "D"))
            pnl = float(row.get("net_pnl", row.get("pnl", 0)))
            # FIX BUG3: signal strength uses grade only (no MFE -- look-ahead bias)
            strength = -_grade_sort_key(grade) * 100
            events.append({
                "type": "ENTRY",
                "bar": entry_bar_master,
                "exit_bar": exit_bar_master,
                "coin": sym,
                "trade_idx": row_idx,
                "grade": grade,
                "strength": strength,
                "pnl": pnl,
                "commission": float(row.get("commission", 0)),
            })

    # Sort entries by bar, then by signal strength (highest first)
    events.sort(key=lambda e: (e["bar"], -e["strength"]))

    # Process: dynamic pool balance model
    # Pool starts at total_capital. Each entry locks margin_per_pos.
    # When trade closes, margin returns to pool + net_pnl.
    # Available = pool_balance - margin_in_use
    pool_balance = float(total_capital)
    active_positions = []  # list of (exit_bar_master, pnl, event_ref)
    rejected = []
    accepted = []

    for evt in events:
        bar = evt["bar"]
        if bar >= n_bars:
            continue

        # Close expired positions: return margin + P&L to pool
        still_active = []
        for ap_exit_bar, ap_pnl, ap_ref in active_positions:
            if ap_exit_bar <= bar:
                pool_balance += margin_per_pos + ap_pnl
            else:
                still_active.append((ap_exit_bar, ap_pnl, ap_ref))
        active_positions = still_active

        margin_in_use = len(active_positions) * margin_per_pos
        available = pool_balance - margin_in_use

        if available >= margin_per_pos:
            # Accept: deduct margin from pool (P&L settles on close)
            pool_balance -= margin_per_pos
            active_positions.append((evt["exit_bar"], evt["pnl"], evt))
            accepted.append(evt)
        else:
            # Reject trade
            rejected.append({
                "bar": bar,
                "coin": evt["coin"],
                "trade_idx": evt["trade_idx"],
                "grade": evt["grade"],
                "reason": "Insufficient capital",
                "pool_balance": round(pool_balance, 2),
                "margin_in_use": round(margin_in_use, 2),
                "available": round(available, 2),
                "needed": round(margin_per_pos, 2),
                "missed_pnl": round(evt["pnl"], 2),
            })

    # FIX BUG1: Rebuild equity curves and capital allocation from ACCEPTED trades only
    # Build rejection set per coin: {sym: set of trade_idx}
    reject_by_coin = {}
    for r in rejected:
        coin = r["coin"]
        if coin not in reject_by_coin:
            reject_by_coin[coin] = set()
        reject_by_coin[coin].add(r["trade_idx"])

    # Rebuild per-coin equity curves excluding rejected trades
    adjusted_coin_results = []
    adjusted_per_coin_eq = {}
    adjusted_total_positions = np.zeros(n_bars)

    for cr in coin_results:
        sym = cr["symbol"]
        coin_dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        eq_orig = np.array(cr["equity_curve"], dtype=float)
        tdf = cr.get("trades_df")
        rejected_idxs = reject_by_coin.get(sym, set())

        if rejected_idxs and tdf is not None and not tdf.empty:
            # Subtract rejected trade P&L from equity curve
            eq_adjusted = eq_orig.copy()
            for ridx in rejected_idxs:
                if ridx in tdf.index:
                    row = tdf.loc[ridx]
                    exit_bar_local = int(row.get("exit_bar", len(coin_dt_idx) - 1))
                    net = float(row.get("net_pnl", row.get("pnl", 0)))
                    # Remove this trade's contribution from exit_bar onward
                    if exit_bar_local < len(eq_adjusted):
                        eq_adjusted[exit_bar_local:] -= net
            # Align adjusted equity to master_dt
            eq_series = pd.Series(eq_adjusted, index=coin_dt_idx)
            eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values
        else:
            # No rejections for this coin -- use original aligned equity
            eq_series = pd.Series(eq_orig, index=coin_dt_idx)
            eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values

        adjusted_per_coin_eq[sym] = eq_aligned

        # Rebuild position counts excluding rejected trades
        pos_orig = np.array(cr["position_counts"], dtype=float)
        if rejected_idxs and tdf is not None:
            pos_adj = pos_orig.copy()
            for ridx in rejected_idxs:
                if ridx in tdf.index:
                    row = tdf.loc[ridx]
                    eb = int(row.get("entry_bar", 0))
                    xb = int(row.get("exit_bar", len(coin_dt_idx) - 1))
                    eb = max(0, min(eb, len(pos_adj) - 1))
                    xb = max(0, min(xb, len(pos_adj) - 1))
                    pos_adj[eb:xb + 1] = np.maximum(pos_adj[eb:xb + 1] - 1, 0)
            pos_series = pd.Series(pos_adj, index=coin_dt_idx)
        else:
            pos_series = pd.Series(pos_orig, index=coin_dt_idx)
        pos_aligned = pos_series.reindex(master_dt, method="ffill").fillna(0).values
        adjusted_total_positions += pos_aligned

        # Build adjusted coin result with filtered trades_df and rebuilt metrics
        adj_cr = dict(cr)
        adj_cr["equity_curve"] = eq_aligned if rejected_idxs else cr["equity_curve"]
        if rejected_idxs and tdf is not None and not tdf.empty:
            # Filter trades_df to accepted-only
            adj_tdf = tdf.drop(index=[i for i in rejected_idxs if i in tdf.index])
            adj_cr["trades_df"] = adj_tdf.reset_index(drop=True)
            # Rebuild metrics from accepted trades
            adj_cr["metrics"] = _rebuild_metrics_from_df(
                adj_cr["trades_df"], adj_cr["equity_curve"],
                cr["metrics"], notional
            )
        adjusted_coin_results.append(adj_cr)

    # Rebuild portfolio equity and capital from adjusted values
    adjusted_portfolio_eq = np.zeros(n_bars)
    for eq_arr in adjusted_per_coin_eq.values():
        adjusted_portfolio_eq += eq_arr
    adjusted_capital_allocated = adjusted_total_positions * margin_per_pos

    # Settle any remaining active positions into pool balance
    for ap_exit_bar, ap_pnl, ap_ref in active_positions:
        pool_balance += margin_per_pos + ap_pnl
    final_pool = pool_balance

    # Compute capital efficiency from ADJUSTED values
    peak_used = float(adjusted_capital_allocated.max())
    avg_used = float(adjusted_capital_allocated.mean())
    idle_pct = (1.0 - avg_used / total_capital) * 100 if total_capital > 0 else 0.0
    total_signals = len(events)
    rejected_count = len(rejected)
    rejection_pct = (rejected_count / total_signals * 100) if total_signals > 0 else 0.0
    missed_pnl = sum(r["missed_pnl"] for r in rejected)

    # Build adjusted pf_data
    peaks = np.maximum.accumulate(adjusted_portfolio_eq)
    dd_arr = np.where(peaks > 0, (adjusted_portfolio_eq - peaks) / peaks * 100.0, 0.0)
    dd_arr = np.clip(dd_arr, -100.0, 0.0)

    adjusted_pf = dict(pf_data)
    adjusted_pf["portfolio_eq"] = adjusted_portfolio_eq
    adjusted_pf["per_coin_eq"] = adjusted_per_coin_eq
    adjusted_pf["total_positions"] = adjusted_total_positions
    adjusted_pf["capital_allocated"] = adjusted_capital_allocated
    adjusted_pf["portfolio_dd_pct"] = round(float(dd_arr.min()), 2)

    return {
        "adjusted_pf": adjusted_pf,
        "adjusted_coin_results": adjusted_coin_results,
        "capital_used": adjusted_capital_allocated,
        "rejected_count": rejected_count,
        "rejection_log": rejected,
        "missed_pnl": round(missed_pnl, 2),
        "reject_by_coin": reject_by_coin,
        "capital_efficiency": {
            "total_capital": total_capital,
            "final_pool": round(final_pool, 2),
            "pool_pnl": round(final_pool - total_capital, 2),
            "peak_used": round(peak_used, 2),
            "peak_pct": round(peak_used / total_capital * 100, 1) if total_capital > 0 else 0,
            "avg_used": round(avg_used, 2),
            "avg_pct": round(avg_used / total_capital * 100, 1) if total_capital > 0 else 0,
            "idle_pct": round(idle_pct, 1),
            "trades_rejected": rejected_count,
            "rejection_pct": round(rejection_pct, 1),
            "missed_pnl": round(missed_pnl, 2),
        },
    }


def format_capital_summary(efficiency):
    """Format capital efficiency dict as display-ready lines. Returns list of strings."""
    lines = [
        f"Starting Capital:    ${efficiency['total_capital']:,.0f}",
        f"Final Pool Balance:  ${efficiency.get('final_pool', efficiency['total_capital']):,.0f}",
        f"Pool P&L:            ${efficiency.get('pool_pnl', 0):+,.2f}",
        f"Peak Margin Used:    ${efficiency['peak_used']:,.0f} ({efficiency['peak_pct']:.1f}%)",
        f"Avg Margin Used:     ${efficiency['avg_used']:,.0f} ({efficiency['avg_pct']:.1f}%)",
        f"Avg Idle Capital:    {efficiency['idle_pct']:.1f}%",
        f"Trades Rejected:     {efficiency['trades_rejected']} ({efficiency['rejection_pct']:.1f}%)",
        f"Missed P&L:          ${efficiency['missed_pnl']:,.2f}",
    ]
    return lines
