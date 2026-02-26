"""
Unified Capital Model v2 -- Post-processing filter for portfolio capital constraints.
Two modes: Per-Coin Independent vs Unified Portfolio Pool.

v2 changes (2026-02-17):
  - Position grouping: trades grouped by (coin, entry_bar) to collapse scale-outs
  - Exchange-model pool: separate balance (realized) and margin_used (locked)
  - No double margin deduction
  - Rebased portfolio equity starts at total_capital, not N*10k
  - Pool balance history tracked per bar for capital chart overlay
  - Best/worst moments recomputed from rebased equity
  - DD% computed on rebased equity (correct relative to deposit)
  - fillna uses actual starting equity, not hardcoded 10000

v1 fixes (2026-02-16):
  - Dynamic pool balance (margin returned + PnL on trade close)
  - Bar indices mapped through datetime_index to master_dt
  - MFE removed from signal strength (look-ahead bias)
  - Equity curves rebuilt after rejecting trades
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
    pos = master_dt.searchsorted(target_dt, side="left")
    if pos >= len(master_dt):
        pos = len(master_dt) - 1
    return int(pos)


def _group_trades_into_positions(coin_results, master_dt):
    """Group Trade384 records into positions by (coin, entry_bar). Returns list of position dicts."""
    positions = {}

    for cr in coin_results:
        sym = cr["symbol"]
        tdf = cr.get("trades_df")
        coin_dt_idx = cr["datetime_index"]
        if tdf is None or tdf.empty:
            continue

        # Group by entry_bar -- all trades from same position share entry_bar
        for entry_bar_local, group in tdf.groupby("entry_bar"):
            entry_bar_local = int(entry_bar_local)
            entry_bar_master = _map_bar_to_master(entry_bar_local, coin_dt_idx, master_dt)

            # exit_bar = last piece to close (max across scale-outs + final close)
            exit_bars_local = group["exit_bar"].astype(int).values
            exit_bar_local_max = int(exit_bars_local.max())
            exit_bar_master = _map_bar_to_master(exit_bar_local_max, coin_dt_idx, master_dt)

            # Aggregate P&L and commission across all records in this position
            net_col = "net_pnl" if "net_pnl" in group.columns else "pnl"
            total_net_pnl = float(group[net_col].sum())
            total_commission = float(group["commission"].sum()) if "commission" in group.columns else 0.0

            # Grade from first record (all records in a position share grade)
            grade = str(group.iloc[0].get("grade", "D"))
            strength = -_grade_sort_key(grade) * 100

            key = (sym, entry_bar_master)
            positions[key] = {
                "coin": sym,
                "entry_bar": entry_bar_master,
                "exit_bar": exit_bar_master,
                "net_pnl": total_net_pnl,
                "commission": total_commission,
                "grade": grade,
                "strength": strength,
                "n_records": len(group),
                "trade_indices": list(group.index),
            }

    # Convert to sorted list (dict discarded after this)
    events = sorted(positions.values(), key=lambda p: (p["entry_bar"], -p["strength"]))
    return events


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

    if len(pnls) > 1 and np.std(pnls) > 0:
        sharpe = float(np.mean(pnls) / np.std(pnls))
        downside = pnls[pnls < 0]
        ds_std = float(np.std(downside)) if len(downside) > 1 else 1.0
        sortino = float(np.mean(pnls) / ds_std) if ds_std > 0 else 0
    else:
        sharpe = 0
        sortino = 0

    max_dd_pct = 0
    if eq_curve is not None and len(eq_curve) > 0:
        peak = np.maximum.accumulate(eq_curve)
        dd_pct_arr = np.where(peak > 0, (peak - eq_curve) / peak * 100, 0)
        max_dd_pct = float(np.max(dd_pct_arr))

    total_losers = loss_count
    saw_green_losers = 0
    if "saw_green" in tdf.columns:
        loser_mask = pnls <= 0
        sg_col = tdf["saw_green"].values
        saw_green_losers = int(np.sum(sg_col[loser_mask]))
    pct_lsg = saw_green_losers / total_losers if total_losers > 0 else 0

    accepted_comm = float(np.sum(commissions))
    orig_comm = orig_metrics.get("total_commission", 0)
    if orig_comm > 0:
        comm_ratio = accepted_comm / orig_comm
    else:
        comm_ratio = 1.0
    total_rebate = orig_metrics.get("total_rebate", 0) * comm_ratio
    # Scale volume/sides from original engine values (accounts for scale-outs
    # which use partial notionals via charge_custom)
    total_volume = orig_metrics.get("total_volume", 0) * comm_ratio
    orig_sides = orig_metrics.get("total_sides", 0)
    total_sides = int(round(orig_sides * comm_ratio)) if orig_sides > 0 else total * 2

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


def apply_capital_constraints(coin_results, pf_data, total_capital, margin_per_pos, notional=None, rebate_pct=0.70, settlement_hour=17):
    """
    Post-process portfolio results to enforce unified capital constraints.

    Uses position grouping to collapse scale-out Trade384 records into single
    position events. Uses exchange-model accounting with separate balance
    (realized cash) and margin_used (locked capital) to avoid double deduction.
    Daily rebate settlement at settlement_hour UTC replenishes pool balance.

    Returns dict with adjusted results, rejection log, and rebased equity.
    """
    if notional is None:
        notional = margin_per_pos * 10
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
                "final_pool": 0,
                "pool_pnl": 0,
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

    # Step 1: Group trades into positions (dict, then sorted list)
    events = _group_trades_into_positions(coin_results, master_dt)

    # Step 2: Exchange-model pool simulation with daily rebate settlement
    # balance = realized cash (changes on trade close + rebate settlement)
    # margin_used = locked capital (changes on open/close)
    # available = balance - margin_used (no double deduction)
    balance = float(total_capital)
    margin_used = 0.0
    active = []  # list of (exit_bar, net_pnl, position_dict)
    rejected = []
    accepted = []

    # Daily rebate settlement tracking
    daily_comm_accumulated = 0.0
    last_settlement_day = None
    total_rebate_settled = 0.0
    prev_bar = -1

    for pos in events:
        bar = pos["entry_bar"]
        if bar >= n_bars:
            continue

        # Check for daily rebate settlement at settlement_hour UTC
        if bar > prev_bar and bar < n_bars:
            bar_dt_ts = master_dt[bar]
            current_day = bar_dt_ts.date()
            current_hour = bar_dt_ts.hour
            if last_settlement_day is None:
                last_settlement_day = current_day
            if current_day > last_settlement_day and current_hour >= settlement_hour:
                if daily_comm_accumulated > 0:
                    rebate_amount = daily_comm_accumulated * rebate_pct
                    balance += rebate_amount
                    total_rebate_settled += rebate_amount
                    daily_comm_accumulated = 0.0
                last_settlement_day = current_day
        prev_bar = bar

        # Close expired positions: release margin, settle P&L to balance
        still_active = []
        for a_exit, a_pnl, a_pos in active:
            if a_exit <= bar:
                balance += a_pnl
                margin_used -= margin_per_pos
            else:
                still_active.append((a_exit, a_pnl, a_pos))
        active = still_active

        # Check available capital (exchange model: no double deduction)
        available = balance - margin_used

        if available >= margin_per_pos:
            # Accept: lock margin, track commission for daily rebate
            margin_used += margin_per_pos
            active.append((pos["exit_bar"], pos["net_pnl"], pos))
            accepted.append(pos)
            daily_comm_accumulated += pos["commission"]
        else:
            # Reject position
            rejected.append({
                "bar": bar,
                "coin": pos["coin"],
                "trade_indices": pos["trade_indices"],
                "grade": pos["grade"],
                "reason": "Insufficient capital",
                "balance": round(balance, 2),
                "margin_used": round(margin_used, 2),
                "available": round(available, 2),
                "needed": round(margin_per_pos, 2),
                "missed_pnl": round(pos["net_pnl"], 2),
                "n_records": pos["n_records"],
            })

    # Final rebate settlement for remaining daily commission
    if daily_comm_accumulated > 0:
        rebate_amount = daily_comm_accumulated * rebate_pct
        balance += rebate_amount
        total_rebate_settled += rebate_amount

    # Build pool balance history (per-bar step function with daily rebate)
    pool_balance_history = np.full(n_bars, float(total_capital))
    _bal = float(total_capital)
    _mu = 0.0
    _hist_active = []
    _hist_daily_comm = 0.0
    _hist_last_settle_day = None

    # Build lookup: which bars have entry/exit events
    _entry_at_bar = {}
    for pos in accepted:
        b = pos["entry_bar"]
        if b not in _entry_at_bar:
            _entry_at_bar[b] = []
        _entry_at_bar[b].append(pos)

    for bar_i in range(n_bars):
        # Daily rebate settlement check
        bar_dt_ts = master_dt[bar_i]
        _curr_day = bar_dt_ts.date()
        _curr_hour = bar_dt_ts.hour
        if _hist_last_settle_day is None:
            _hist_last_settle_day = _curr_day
        if _curr_day > _hist_last_settle_day and _curr_hour >= settlement_hour:
            if _hist_daily_comm > 0:
                _bal += _hist_daily_comm * rebate_pct
                _hist_daily_comm = 0.0
            _hist_last_settle_day = _curr_day

        # Close positions that exit at or before this bar
        _still = []
        for _ax, _ap, _apos in _hist_active:
            if _ax <= bar_i:
                _bal += _ap
                _mu -= margin_per_pos
            else:
                _still.append((_ax, _ap, _apos))
        _hist_active = _still

        # Open positions that enter at this bar
        if bar_i in _entry_at_bar:
            for epos in _entry_at_bar[bar_i]:
                _mu += margin_per_pos
                _hist_active.append((epos["exit_bar"], epos["net_pnl"], epos))
                _hist_daily_comm += epos.get("commission", 0)

        pool_balance_history[bar_i] = _bal

    # Final rebate settlement for history
    if _hist_daily_comm > 0 and n_bars > 0:
        pool_balance_history[-1] += _hist_daily_comm * rebate_pct

    # Build rejection set per coin: {sym: set of trade_indices}
    # Each rejected position has trade_indices = list of DataFrame row indices
    reject_by_coin = {}
    for r in rejected:
        coin = r["coin"]
        if coin not in reject_by_coin:
            reject_by_coin[coin] = set()
        for tidx in r["trade_indices"]:
            reject_by_coin[coin].add(tidx)

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

        # Use actual starting equity, not hardcoded 10000
        _start_eq = float(eq_orig[0]) if len(eq_orig) > 0 else 10000.0

        if rejected_idxs and tdf is not None and not tdf.empty:
            eq_adjusted = eq_orig.copy()
            for ridx in rejected_idxs:
                if ridx in tdf.index:
                    row = tdf.loc[ridx]
                    exit_bar_local = int(row.get("exit_bar", len(coin_dt_idx) - 1))
                    net = float(row.get("net_pnl", row.get("pnl", 0)))
                    if exit_bar_local < len(eq_adjusted):
                        eq_adjusted[exit_bar_local:] -= net
            eq_series = pd.Series(eq_adjusted, index=coin_dt_idx)
            eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(_start_eq).values
        else:
            eq_series = pd.Series(eq_orig, index=coin_dt_idx)
            eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(_start_eq).values

        adjusted_per_coin_eq[sym] = eq_aligned

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

        adj_cr = dict(cr)
        adj_cr["equity_curve"] = eq_aligned if rejected_idxs else cr["equity_curve"]
        if rejected_idxs and tdf is not None and not tdf.empty:
            adj_tdf = tdf.drop(index=[i for i in rejected_idxs if i in tdf.index])
            adj_cr["trades_df"] = adj_tdf.reset_index(drop=True)
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

    # Settle remaining active positions into final balance
    for a_exit, a_pnl, a_pos in active:
        balance += a_pnl
        margin_used -= margin_per_pos

    # Rebate was already settled daily into balance during the simulation loop.
    # total_rebate_settled tracks the cumulative amount credited.
    final_pool = balance

    # Two rebased curves for different purposes
    engine_baseline = 10000.0 * len(coin_results)

    # 1. Pool balance = actual realized capital (step-function, no unrealized P&L)
    #    Used for: Net P&L, DD%, best/worst -- reflects real risk
    rebased_portfolio_eq = pool_balance_history.copy()

    # 2. Adjusted equity rebased = smoother visual for equity chart
    rebased_chart_eq = adjusted_portfolio_eq - engine_baseline + total_capital

    # Compute DD% on pool balance (actual realized capital risk)
    peaks = np.maximum.accumulate(rebased_portfolio_eq)
    dd_arr = np.where(peaks > 0, (rebased_portfolio_eq - peaks) / peaks * 100.0, 0.0)
    dd_arr = np.clip(dd_arr, -100.0, 0.0)

    # Recompute best/worst moments from rebased equity
    best_bar = int(np.argmax(rebased_portfolio_eq))
    worst_bar = int(np.argmin(dd_arr))

    def _bar_info(bar_idx, label):
        """Build info dict for a bar on the rebased equity curve."""
        dt_str = str(master_dt[bar_idx])[:19] if bar_idx < len(master_dt) else ""
        return {
            "label": label,
            "bar": bar_idx,
            "date": dt_str,
            "equity": round(float(rebased_portfolio_eq[bar_idx]), 2),
            "dd_pct": round(float(dd_arr[bar_idx]), 2),
            "positions": int(adjusted_total_positions[bar_idx]),
            "capital": round(float(adjusted_capital_allocated[bar_idx]), 2),
        }

    # Capital efficiency
    peak_used = float(adjusted_capital_allocated.max())
    avg_used = float(adjusted_capital_allocated.mean())
    idle_pct = (1.0 - avg_used / total_capital) * 100 if total_capital > 0 else 0.0
    total_events = len(events)
    rejected_count = len(rejected)
    rejection_pct = (rejected_count / total_events * 100) if total_events > 0 else 0.0
    missed_pnl = sum(r["missed_pnl"] for r in rejected)

    # Build adjusted pf_data
    adjusted_pf = dict(pf_data)
    adjusted_pf["portfolio_eq"] = adjusted_portfolio_eq
    adjusted_pf["rebased_portfolio_eq"] = rebased_portfolio_eq
    adjusted_pf["rebased_chart_eq"] = rebased_chart_eq
    adjusted_pf["pool_balance_history"] = pool_balance_history
    adjusted_pf["per_coin_eq"] = adjusted_per_coin_eq
    adjusted_pf["total_positions"] = adjusted_total_positions
    adjusted_pf["capital_allocated"] = adjusted_capital_allocated
    adjusted_pf["portfolio_dd_pct"] = round(float(dd_arr.min()), 2)
    adjusted_pf["best_moment"] = _bar_info(best_bar, "Best")
    adjusted_pf["worst_moment"] = _bar_info(worst_bar, "Worst")

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
        "Starting Capital:    $" + f"{efficiency['total_capital']:,.0f}",
        "Final Pool Balance:  $" + f"{efficiency.get('final_pool', efficiency['total_capital']):,.0f}",
        "Pool P&L:            $" + f"{efficiency.get('pool_pnl', 0):+,.2f}",
        "Peak Margin Used:    $" + f"{efficiency['peak_used']:,.0f}" + " (" + f"{efficiency['peak_pct']:.1f}%)",
        "Avg Margin Used:     $" + f"{efficiency['avg_used']:,.0f}" + " (" + f"{efficiency['avg_pct']:.1f}%)",
        "Avg Idle Capital:    " + f"{efficiency['idle_pct']:.1f}%",
        "Trades Rejected:     " + str(efficiency['trades_rejected']) + " (" + f"{efficiency['rejection_pct']:.1f}%)",
        "Missed P&L:          $" + f"{efficiency['missed_pnl']:,.2f}",
    ]
    return lines
