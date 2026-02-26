"""
Debug pool balance calculation -- traces every entry/exit event and pool state.
Runs the same 2-coin portfolio as the dashboard to find where pool_pnl diverges
from per-coin net sum.

Run: python scripts/debug_pool_balance.py
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

# Load engine
from engine.backtester_v384 import Backtester384
from engine.signals import compute_signals
from data.bybit_fetcher import BybitFetcher
from utils.capital_model import apply_capital_constraints, _map_bar_to_master, _grade_sort_key

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print("=" * 70)
print(f"Pool Balance Debug -- {TIMESTAMP}")
print("=" * 70)

# Settings matching dashboard defaults
SYMBOLS = ["NOTUSDT", "SUSDT"]
MARGIN = 500.0
LEVERAGE = 20
NOTIONAL = MARGIN * LEVERAGE  # 10000
TOTAL_CAPITAL = 10000.0
COMMISSION_RATE = 0.0008
MAKER_RATE = 0.0002
REBATE_PCT = 0.70
TIMEFRAME = "5"

signal_params = {
    "stoch_k": 9, "stoch_d": 3, "stoch_smooth": 1,
    "stoch_k2": 14, "stoch_d2": 3, "stoch_smooth2": 1,
    "stoch_k3": 40, "stoch_d3": 3, "stoch_smooth3": 1,
    "stoch_k4": 60, "stoch_d4": 10, "stoch_smooth4": 1,
    "ema_fast": 12, "ema_slow": 26,
    "cloud2_fast": 5, "cloud2_slow": 12,
    "cloud3_fast": 34, "cloud3_slow": 50,
    "cloud4_fast": 72, "cloud4_slow": 89,
    "cloud5_fast": 180, "cloud5_slow": 200,
    "avwap_lookback": 50,
    "b_open_fresh": True,
}

bt_params = {
    "sl_mult": 3.0,
    "tp_mult": None,
    "cooldown": 3,
    "b_open_fresh": True,
    "notional": NOTIONAL,
    "commission_rate": COMMISSION_RATE,
    "maker_rate": MAKER_RATE,
    "rebate_pct": REBATE_PCT,
    "initial_equity": 10000.0,
    "max_positions": 4,
    "checkpoint_interval": 5,
    "max_scaleouts": 2,
    "sigma_floor_atr": 0.5,
    "enable_adds": True,
    "enable_reentry": True,
    "be_trigger_atr": 1.5,
    "be_lock_atr": 0.3,
}


def load_data(symbol, tf):
    """Load cached parquet data for a symbol."""
    cache_dir = ROOT / "data" / "cache"
    pattern = f"{symbol}_{tf}m_*.parquet"
    files = sorted(cache_dir.glob(pattern))
    if not files:
        print(f"  No cache for {symbol}")
        return None
    dfs = [pd.read_parquet(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").drop_duplicates("datetime").reset_index(drop=True)
    return df


def run_backtest(df, sig_params, run_params):
    """Run signals + backtester."""
    df_sig = compute_signals(df, sig_params)
    bt = Backtester384(run_params)
    results = bt.run(df_sig)
    return results, df_sig


def align_portfolio_equity(coin_results, margin_per_pos=500.0, max_positions=4):
    """Align per-coin equity curves to a common datetime index."""
    all_dt = set()
    for cr in coin_results:
        dt_idx = pd.DatetimeIndex(cr["datetime_index"])
        all_dt.update(dt_idx.tolist())
    master_dt = pd.DatetimeIndex(sorted(all_dt))
    n_bars = len(master_dt)

    per_coin_eq = {}
    total_positions = np.zeros(n_bars)
    for cr in coin_results:
        sym = cr["symbol"]
        coin_dt = pd.DatetimeIndex(cr["datetime_index"])
        eq = np.array(cr["equity_curve"], dtype=float)
        eq_series = pd.Series(eq, index=coin_dt)
        eq_aligned = eq_series.reindex(master_dt, method="ffill").fillna(10000.0).values
        per_coin_eq[sym] = eq_aligned

        pos = np.array(cr["position_counts"], dtype=float)
        pos_series = pd.Series(pos, index=coin_dt)
        pos_aligned = pos_series.reindex(master_dt, method="ffill").fillna(0).values
        total_positions += pos_aligned

    portfolio_eq = np.zeros(n_bars)
    for eq_arr in per_coin_eq.values():
        portfolio_eq += eq_arr
    capital_allocated = total_positions * margin_per_pos

    peaks = np.maximum.accumulate(portfolio_eq)
    dd_arr = np.where(peaks > 0, (portfolio_eq - peaks) / peaks * 100.0, 0.0)
    dd_arr = np.clip(dd_arr, -100.0, 0.0)

    best_bar = int(np.argmax(portfolio_eq))
    worst_bar = int(np.argmin(dd_arr))

    def _bar_info(bar_idx, label):
        """Build info dict for a bar."""
        dt_str = str(master_dt[bar_idx])[:19]
        return {
            "label": label, "bar": bar_idx, "date": dt_str,
            "equity": round(float(portfolio_eq[bar_idx]), 2),
            "dd_pct": round(float(dd_arr[bar_idx]), 2),
            "positions": int(total_positions[bar_idx]),
            "capital": round(float(capital_allocated[bar_idx]), 2),
        }

    return {
        "master_dt": master_dt,
        "per_coin_eq": per_coin_eq,
        "portfolio_eq": portfolio_eq,
        "total_positions": total_positions,
        "capital_allocated": capital_allocated,
        "portfolio_dd_pct": round(float(dd_arr.min()), 2),
        "best_moment": _bar_info(best_bar, "Best"),
        "worst_moment": _bar_info(worst_bar, "Worst"),
    }


# ============================================================
# RUN BACKTESTS
# ============================================================
print("\n--- Running backtests ---")
coin_results = []
for sym in SYMBOLS:
    df = load_data(sym, TIMEFRAME)
    if df is None:
        continue
    print(f"  {sym}: {len(df)} bars loaded")
    r, ds = run_backtest(df, signal_params, bt_params)
    m = r["metrics"]
    print(f"  {sym}: {m['total_trades']} trades, net_pnl=${m['net_pnl']:+,.2f}")
    dt_idx = ds["datetime"] if "datetime" in ds.columns else pd.RangeIndex(len(r["equity_curve"]))
    coin_results.append({
        "symbol": sym,
        "equity_curve": r["equity_curve"],
        "datetime_index": dt_idx,
        "position_counts": r["position_counts"],
        "trades_df": r["trades_df"],
        "metrics": r["metrics"],
    })

if not coin_results:
    print("No coin results!")
    sys.exit(1)

# Align
pf = align_portfolio_equity(coin_results, margin_per_pos=MARGIN, max_positions=4)
print(f"\n--- Portfolio aligned: {len(pf['master_dt'])} bars ---")
print(f"  portfolio_eq[0]  = {pf['portfolio_eq'][0]:,.2f}")
print(f"  portfolio_eq[-1] = {pf['portfolio_eq'][-1]:,.2f}")
print(f"  engine baseline  = {10000.0 * len(coin_results):,.2f}")
print(f"  engine net P&L   = {pf['portfolio_eq'][-1] - 10000.0 * len(coin_results):+,.2f}")

# ============================================================
# MANUAL POOL TRACE (mirror capital_model.py logic exactly)
# ============================================================
print("\n--- Pool Balance Trace ---")
master_dt = pf["master_dt"]
n_bars = len(master_dt)

# Collect events
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
        entry_bar_master = _map_bar_to_master(entry_bar_local, coin_dt_idx, master_dt)
        exit_bar_master = _map_bar_to_master(exit_bar_local, coin_dt_idx, master_dt)
        grade = str(row.get("grade", "D"))
        pnl = float(row.get("net_pnl", row.get("pnl", 0)))
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

events.sort(key=lambda e: (e["bar"], -e["strength"]))
print(f"  Total events: {len(events)}")

# Process with full trace
pool_balance = float(TOTAL_CAPITAL)
active_positions = []
rejected = []
accepted = []
sum_entry_deductions = 0.0
sum_exit_returns = 0.0
sum_accepted_pnl = 0.0

for i, evt in enumerate(events):
    bar = evt["bar"]
    if bar >= n_bars:
        continue

    # Close expired
    still_active = []
    for ap_exit_bar, ap_pnl, ap_ref in active_positions:
        if ap_exit_bar <= bar:
            returned = MARGIN + ap_pnl
            pool_balance += returned
            sum_exit_returns += returned
        else:
            still_active.append((ap_exit_bar, ap_pnl, ap_ref))
    active_positions = still_active

    margin_in_use = len(active_positions) * MARGIN
    available = pool_balance - margin_in_use

    if available >= MARGIN:
        pool_balance -= MARGIN
        sum_entry_deductions += MARGIN
        active_positions.append((evt["exit_bar"], evt["pnl"], evt))
        accepted.append(evt)
        sum_accepted_pnl += evt["pnl"]
    else:
        rejected.append(evt)

# Final settlement
final_settlement = 0.0
for ap_exit_bar, ap_pnl, ap_ref in active_positions:
    returned = MARGIN + ap_pnl
    pool_balance += returned
    sum_exit_returns += returned
    final_settlement += returned
final_pool = pool_balance

print(f"\n--- Pool Trace Results ---")
print(f"  Total events:        {len(events)}")
print(f"  Accepted:            {len(accepted)}")
print(f"  Rejected:            {len(rejected)}")
print(f"  Sum entry deductions: ${sum_entry_deductions:,.2f}")
print(f"  Sum exit returns:     ${sum_exit_returns:,.2f}")
print(f"  Sum accepted PnL:     ${sum_accepted_pnl:+,.2f}")
print(f"  Final settlement:     ${final_settlement:,.2f}")
print(f"  Final pool:           ${final_pool:,.2f}")
print(f"  Pool P&L:             ${final_pool - TOTAL_CAPITAL:+,.2f}")
print(f"  Expected P&L:         ${sum_accepted_pnl:+,.2f}")
print(f"  DELTA:                ${final_pool - TOTAL_CAPITAL - sum_accepted_pnl:+,.2f}")

# Verify: per-coin accepted net_pnl
print(f"\n--- Per-Coin Accepted PnL ---")
for sym in SYMBOLS:
    sym_pnls = [e["pnl"] for e in accepted if e["coin"] == sym]
    print(f"  {sym}: {len(sym_pnls)} trades, sum=${sum(sym_pnls):+,.2f}")

sym_pnls_rej = [e["pnl"] for e in rejected]
print(f"  REJECTED: {len(rejected)} trades, sum=${sum(sym_pnls_rej):+,.2f}")

# Cross-check with capital_model.apply_capital_constraints
print(f"\n--- apply_capital_constraints() ---")
cap_result = apply_capital_constraints(coin_results, pf, TOTAL_CAPITAL, MARGIN, notional=NOTIONAL)
eff = cap_result["capital_efficiency"]
print(f"  pool_pnl:        ${eff['pool_pnl']:+,.2f}")
print(f"  final_pool:      ${eff['final_pool']:,.2f}")
print(f"  rejected_count:  {eff['trades_rejected']}")
print(f"  missed_pnl:      ${eff['missed_pnl']:+,.2f}")

# Per-coin adjusted equity
adj_cr = cap_result["adjusted_coin_results"]
adj_pf = cap_result["adjusted_pf"]
for cr in adj_cr:
    eq = cr["equity_curve"]
    eq_last = float(eq[-1]) if hasattr(eq, '__len__') else float(eq)
    net = eq_last - 10000.0
    m = cr["metrics"]
    print(f"  {cr['symbol']}: eq[-1]=${eq_last:,.2f}, net=${net:+,.2f}, trades={m['total_trades']}, m.net_pnl=${m['net_pnl']:+,.2f}")

port_eq = adj_pf["portfolio_eq"]
print(f"\n  adjusted portfolio_eq[-1] = ${port_eq[-1]:,.2f}")
print(f"  adjusted net (eq-baseline) = ${port_eq[-1] - 10000.0*len(coin_results):+,.2f}")

# Check available margin double-deduction issue
print(f"\n--- Double Deduction Check ---")
print(f"  In the event loop, 'available = pool_balance - margin_in_use'")
print(f"  But pool_balance ALREADY has margin deducted for active positions!")
print(f"  This means available is computed as pool_balance - margin_in_use")
print(f"  where pool_balance = deposit - sum(active_margins) + sum(closed returns)")
print(f"  and margin_in_use = len(active) * margin")
print(f"  So effective available = deposit - 2*sum(active_margins) + sum(closed returns)")
print(f"  This is a DOUBLE DEDUCTION -- the final pool is correct but")
print(f"  more trades get rejected than necessary.")

# Show first 10 rejections
if rejected:
    print(f"\n--- First 10 Rejections ---")
    for r in rejected[:10]:
        print(f"  bar={r['bar']}, {r['coin']}, pnl=${r['pnl']:+.2f}, grade={r['grade']}")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
