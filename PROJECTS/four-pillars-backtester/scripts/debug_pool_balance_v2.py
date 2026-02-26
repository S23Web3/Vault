"""
Pool Balance Tracer v2 -- traces every position event through the exchange-model pool.

Mirrors capital_model_v2.py logic EXACTLY to find where 3-coin portfolios break.
Outputs two CSVs:
  results/pool_trace_3coin.csv  -- every open/close/reject event with pool state
  results/all_trades_3coin.csv  -- combined trades from all coins with symbol + timestamps

Run: python scripts/debug_pool_balance_v2.py
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from engine.backtester_v384 import Backtester384
from signals.four_pillars_v383 import compute_signals_v383

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print("=" * 70)
print("Pool Balance Tracer v2 -- " + TS)
print("=" * 70)

# ============================================================
# SETTINGS (match dashboard defaults)
# ============================================================
SYMBOLS = ["CELOUSDT", "ZBCNUSDT", "GNOUSDT"]
LAST_N_DAYS = 30  # Set to None for full history
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

GRADE_PRIORITY = {"A": 0, "B": 1, "C": 2, "D": 3, "ADD": 4, "RE": 5, "R": 6}


def grade_sort_key(grade_str):
    """Return numeric priority for a trade grade (lower = higher priority)."""
    return GRADE_PRIORITY.get(str(grade_str).upper(), 99)


def load_data(symbol, tf):
    """Load cached parquet data for a symbol."""
    cache_dir = ROOT / "data" / "cache"
    # Try single file first, then chunked pattern
    single = cache_dir / (symbol + "_" + tf + "m.parquet")
    if single.exists():
        df = pd.read_parquet(single)
    else:
        pattern = symbol + "_" + tf + "m_*.parquet"
        files = sorted(cache_dir.glob(pattern))
        if not files:
            print("  No cache for " + symbol)
            return None
        dfs = [pd.read_parquet(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").drop_duplicates("datetime").reset_index(drop=True)
        if LAST_N_DAYS is not None:
            cutoff = df["datetime"].max() - pd.Timedelta(days=LAST_N_DAYS)
            df = df[df["datetime"] >= cutoff].reset_index(drop=True)
    return df


def run_backtest(df, sig_params, run_params):
    """Run signals + backtester, return results."""
    df_sig = compute_signals_v383(df.copy(), sig_params)
    bt = Backtester384(run_params)
    results = bt.run(df_sig)
    return results, df_sig


def map_bar_to_master(bar_idx, coin_dt_index, master_dt):
    """Map a per-coin bar index to the corresponding master_dt index."""
    coin_dt = pd.DatetimeIndex(coin_dt_index)
    if bar_idx < 0 or bar_idx >= len(coin_dt):
        bar_idx = max(0, min(bar_idx, len(coin_dt) - 1))
    target_dt = coin_dt[bar_idx]
    pos = master_dt.searchsorted(target_dt, side="left")
    if pos >= len(master_dt):
        pos = len(master_dt) - 1
    return int(pos)


# ============================================================
# RUN BACKTESTS
# ============================================================
print("\n--- Running backtests ---")
coin_results = []
for sym in SYMBOLS:
    df = load_data(sym, TIMEFRAME)
    if df is None:
        continue
    print("  " + sym + ": " + str(len(df)) + " bars loaded")
    r, ds = run_backtest(df, signal_params, bt_params)
    m = r["metrics"]
    dt_idx = ds["datetime"] if "datetime" in ds.columns else pd.RangeIndex(len(r["equity_curve"]))
    net_pnl = m["net_pnl"]
    rebate = m.get("total_rebate", 0)
    net_after = m.get("net_pnl_after_rebate", net_pnl)
    eq_last = float(r["equity_curve"][-1])
    print("  " + sym + ": " + str(m["total_trades"]) + " trades"
          + ", net_pnl=$" + "{:+,.2f}".format(net_pnl)
          + ", rebate=$" + "{:,.2f}".format(rebate)
          + ", net_after=$" + "{:+,.2f}".format(net_after)
          + ", eq[-1]=$" + "{:,.2f}".format(eq_last)
          + ", eq_net=$" + "{:+,.2f}".format(eq_last - 10000.0))
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

# ============================================================
# BUILD MASTER DATETIME INDEX
# ============================================================
all_dt = set()
for cr in coin_results:
    dt_idx = pd.DatetimeIndex(cr["datetime_index"])
    all_dt.update(dt_idx.tolist())
master_dt = pd.DatetimeIndex(sorted(all_dt))
n_bars = len(master_dt)
print("\nMaster dt: " + str(n_bars) + " bars")

# ============================================================
# COMBINED TRADES CSV (all coins, with symbol + timestamps)
# ============================================================
print("\n--- Building combined trades CSV ---")
all_trades_rows = []
for cr in coin_results:
    sym = cr["symbol"]
    tdf = cr.get("trades_df")
    coin_dt_idx = cr["datetime_index"]
    if tdf is None or tdf.empty:
        continue
    for _, row in tdf.iterrows():
        entry_bar = int(row.get("entry_bar", 0))
        exit_bar = int(row.get("exit_bar", len(coin_dt_idx) - 1))
        # Get timestamps from coin datetime index
        coin_dt = pd.DatetimeIndex(coin_dt_idx)
        entry_dt = str(coin_dt[min(entry_bar, len(coin_dt) - 1)])[:19] if entry_bar < len(coin_dt) else ""
        exit_dt = str(coin_dt[min(exit_bar, len(coin_dt) - 1)])[:19] if exit_bar < len(coin_dt) else ""
        all_trades_rows.append({
            "symbol": sym,
            "direction": row.get("direction", ""),
            "grade": row.get("grade", ""),
            "entry_bar": entry_bar,
            "exit_bar": exit_bar,
            "entry_time": entry_dt,
            "exit_time": exit_dt,
            "entry_price": row.get("entry_price", 0),
            "exit_price": row.get("exit_price", 0),
            "pnl": row.get("pnl", 0),
            "commission": row.get("commission", 0),
            "net_pnl": row.get("net_pnl", row.get("pnl", 0)),
            "exit_reason": row.get("exit_reason", ""),
            "scale_idx": row.get("scale_idx", 0),
            "saw_green": row.get("saw_green", False),
            "mfe": row.get("mfe", 0),
            "mae": row.get("mae", 0),
        })

all_trades_df = pd.DataFrame(all_trades_rows)
results_dir = ROOT / "results"
results_dir.mkdir(parents=True, exist_ok=True)
trades_csv_path = results_dir / "all_trades_3coin.csv"
all_trades_df.to_csv(trades_csv_path, index=False)
print("  Saved " + str(len(all_trades_df)) + " trades to " + str(trades_csv_path))

# ============================================================
# GROUP TRADES INTO POSITIONS (mirrors capital_model_v2 exactly)
# ============================================================
print("\n--- Grouping trades into positions ---")
positions = {}
for cr in coin_results:
    sym = cr["symbol"]
    tdf = cr.get("trades_df")
    coin_dt_idx = cr["datetime_index"]
    if tdf is None or tdf.empty:
        continue
    for entry_bar_local, group in tdf.groupby("entry_bar"):
        entry_bar_local = int(entry_bar_local)
        entry_bar_master = map_bar_to_master(entry_bar_local, coin_dt_idx, master_dt)
        exit_bars_local = group["exit_bar"].astype(int).values
        exit_bar_local_max = int(exit_bars_local.max())
        exit_bar_master = map_bar_to_master(exit_bar_local_max, coin_dt_idx, master_dt)
        net_col = "net_pnl" if "net_pnl" in group.columns else "pnl"
        total_net_pnl = float(group[net_col].sum())
        total_commission = float(group["commission"].sum()) if "commission" in group.columns else 0.0
        grade = str(group.iloc[0].get("grade", "D"))
        strength = -grade_sort_key(grade) * 100
        n_records = len(group)
        key = (sym, entry_bar_master)
        positions[key] = {
            "coin": sym,
            "entry_bar": entry_bar_master,
            "exit_bar": exit_bar_master,
            "net_pnl": total_net_pnl,
            "commission": total_commission,
            "grade": grade,
            "strength": strength,
            "n_records": n_records,
            "trade_indices": list(group.index),
        }

events = sorted(positions.values(), key=lambda p: (p["entry_bar"], -p["strength"]))
total_positions_count = len(events)

# Count records per position to show scale-out collapsing
multi_record = sum(1 for p in events if p["n_records"] > 1)
total_records = sum(p["n_records"] for p in events)
print("  Total trade records: " + str(total_records))
print("  Grouped into positions: " + str(total_positions_count))
print("  Multi-record positions (scale-outs): " + str(multi_record))
print("  Per coin:")
for sym in SYMBOLS:
    sym_pos = [p for p in events if p["coin"] == sym]
    sym_net = sum(p["net_pnl"] for p in sym_pos)
    print("    " + sym + ": " + str(len(sym_pos)) + " positions, net=$" + "{:+,.2f}".format(sym_net))

# ============================================================
# EXCHANGE-MODEL POOL SIMULATION WITH DAILY REBATE SETTLEMENT
# ============================================================
print("\n--- Exchange-Model Pool Trace (with daily rebate) ---")
print("  Starting capital: $" + "{:,.0f}".format(TOTAL_CAPITAL))
print("  Margin per position: $" + "{:,.0f}".format(MARGIN))
print("  Rebate pct: " + "{:.0f}%".format(REBATE_PCT * 100))

SETTLEMENT_HOUR = 17  # 5pm UTC

balance = float(TOTAL_CAPITAL)
margin_used = 0.0
active = []  # list of (exit_bar, net_pnl, position_dict)
accepted = []
rejected = []
trace_rows = []  # for CSV output

# Daily rebate tracking
daily_comm_accumulated = 0.0  # commission accumulated since last settlement
last_settlement_day = None
total_rebate_settled = 0.0
rebate_events = []  # log of each settlement

max_concurrent = 0
max_margin_used = 0.0
min_available = float(TOTAL_CAPITAL)
prev_bar = -1

for idx, pos in enumerate(events):
    bar = pos["entry_bar"]
    if bar >= n_bars:
        continue

    # Check for rebate settlement at 5pm UTC boundary
    # Process all bars between prev_bar and current bar
    if bar > prev_bar and bar < n_bars:
        bar_dt_ts = master_dt[bar]
        current_day = bar_dt_ts.date()
        current_hour = bar_dt_ts.hour
        if last_settlement_day is None:
            last_settlement_day = current_day
        if current_day > last_settlement_day and current_hour >= SETTLEMENT_HOUR:
            if daily_comm_accumulated > 0:
                rebate_amount = daily_comm_accumulated * REBATE_PCT
                balance += rebate_amount
                total_rebate_settled += rebate_amount
                rebate_events.append({
                    "bar": bar,
                    "date": str(current_day),
                    "daily_comm": round(daily_comm_accumulated, 2),
                    "rebate": round(rebate_amount, 2),
                    "balance_after": round(balance, 2),
                })
                daily_comm_accumulated = 0.0
            last_settlement_day = current_day
    prev_bar = bar

    # Close expired positions
    closed_this_step = 0
    closed_pnl = 0.0
    still_active = []
    for a_exit, a_pnl, a_pos in active:
        if a_exit <= bar:
            balance += a_pnl
            margin_used -= MARGIN
            closed_this_step += 1
            closed_pnl += a_pnl
        else:
            still_active.append((a_exit, a_pnl, a_pos))
    active = still_active

    available = balance - margin_used
    decision = ""
    reason = ""

    if available >= MARGIN:
        margin_used += MARGIN
        active.append((pos["exit_bar"], pos["net_pnl"], pos))
        accepted.append(pos)
        decision = "ACCEPT"
        # Track commission for daily rebate (accepted trades only)
        daily_comm_accumulated += pos["commission"]
        concurrent = len(active)
        if concurrent > max_concurrent:
            max_concurrent = concurrent
        if margin_used > max_margin_used:
            max_margin_used = margin_used
    else:
        rejected.append(pos)
        decision = "REJECT"
        reason = "avail=$" + "{:,.2f}".format(available) + " < margin=$" + "{:,.0f}".format(MARGIN)

    if available < min_available:
        min_available = available

    # Get timestamp for this bar
    bar_dt = str(master_dt[bar])[:19] if bar < n_bars else ""

    trace_rows.append({
        "event_idx": idx,
        "bar": bar,
        "datetime": bar_dt,
        "coin": pos["coin"],
        "grade": pos["grade"],
        "n_records": pos["n_records"],
        "net_pnl": round(pos["net_pnl"], 2),
        "commission": round(pos["commission"], 2),
        "decision": decision,
        "balance": round(balance, 2),
        "margin_used": round(margin_used, 2),
        "available": round(available, 2),
        "active_count": len(active),
        "closed_this_step": closed_this_step,
        "closed_pnl": round(closed_pnl, 2),
        "exit_bar": pos["exit_bar"],
        "rebate_settled_so_far": round(total_rebate_settled, 2),
        "reason": reason,
    })

# Final rebate settlement for any remaining daily commission
if daily_comm_accumulated > 0:
    rebate_amount = daily_comm_accumulated * REBATE_PCT
    balance += rebate_amount
    total_rebate_settled += rebate_amount
    rebate_events.append({
        "bar": n_bars - 1,
        "date": "FINAL",
        "daily_comm": round(daily_comm_accumulated, 2),
        "rebate": round(rebate_amount, 2),
        "balance_after": round(balance, 2),
    })

# Settle remaining active
remaining_pnl = 0.0
for a_exit, a_pnl, a_pos in active:
    balance += a_pnl
    margin_used -= MARGIN
    remaining_pnl += a_pnl
final_pool = balance

# Accepted commission total (for comparison)
accepted_comm = sum(p["commission"] for p in accepted)

# ============================================================
# SAVE POOL TRACE CSV
# ============================================================
trace_df = pd.DataFrame(trace_rows)
trace_csv_path = results_dir / "pool_trace_3coin.csv"
trace_df.to_csv(trace_csv_path, index=False)
print("  Saved " + str(len(trace_df)) + " events to " + str(trace_csv_path))

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("POOL TRACE SUMMARY")
print("=" * 70)
print("  Total positions:     " + str(total_positions_count))
print("  Accepted:            " + str(len(accepted)))
print("  Rejected:            " + str(len(rejected))
      + " (" + "{:.1f}".format(len(rejected)/total_positions_count*100 if total_positions_count > 0 else 0) + "%)")
print("  Max concurrent:      " + str(max_concurrent))
print("  Max margin used:     $" + "{:,.0f}".format(max_margin_used))
print("  Min available:       $" + "{:,.2f}".format(min_available))
print("")
print("  Starting balance:    $" + "{:,.2f}".format(TOTAL_CAPITAL))
print("  Final pool:          $" + "{:,.2f}".format(final_pool))
print("  Pool P&L:            $" + "{:+,.2f}".format(final_pool - TOTAL_CAPITAL))
print("  Total rebate settled:$" + "{:,.2f}".format(total_rebate_settled))
print("  Rebate settlements:  " + str(len(rebate_events)))
print("  Accepted commission: $" + "{:,.2f}".format(accepted_comm))
print("  Remaining settled:   $" + "{:+,.2f}".format(remaining_pnl))

# Show rebate settlement log
if rebate_events:
    print("\n--- Rebate Settlements ---")
    for re in rebate_events:
        print("  " + re["date"]
              + " | daily_comm=$" + "{:,.2f}".format(re["daily_comm"])
              + " | rebate=$" + "{:,.2f}".format(re["rebate"])
              + " | balance=$" + "{:,.2f}".format(re["balance_after"]))

# Per-coin breakdown
print("\n--- Per-Coin Breakdown ---")
for sym in SYMBOLS:
    acc_sym = [p for p in accepted if p["coin"] == sym]
    rej_sym = [p for p in rejected if p["coin"] == sym]
    acc_pnl = sum(p["net_pnl"] for p in acc_sym)
    rej_pnl = sum(p["net_pnl"] for p in rej_sym)
    cr = next((c for c in coin_results if c["symbol"] == sym), None)
    eng_net = cr["metrics"]["net_pnl"] if cr else 0
    eng_rebate = cr["metrics"].get("total_rebate", 0) if cr else 0
    eng_after = cr["metrics"].get("net_pnl_after_rebate", eng_net) if cr else 0
    eq_last = float(cr["equity_curve"][-1]) if cr else 10000.0
    print("  " + sym + ":")
    print("    Engine: " + str(cr["metrics"]["total_trades"]) + " trades"
          + ", net=$" + "{:+,.2f}".format(eng_net)
          + ", rebate=$" + "{:,.2f}".format(eng_rebate)
          + ", net_after=$" + "{:+,.2f}".format(eng_after)
          + ", eq[-1]=$" + "{:,.2f}".format(eq_last))
    print("    Pool:   " + str(len(acc_sym)) + " accepted"
          + ", " + str(len(rej_sym)) + " rejected"
          + ", acc_pnl=$" + "{:+,.2f}".format(acc_pnl)
          + ", rej_pnl=$" + "{:+,.2f}".format(rej_pnl))

# Show first 20 rejections
if rejected:
    print("\n--- First 20 Rejections ---")
    rej_count = 0
    for r in rejected[:20]:
        bar_dt = str(master_dt[r["entry_bar"]])[:19] if r["entry_bar"] < n_bars else ""
        print("  #" + str(rej_count) + " bar=" + str(r["entry_bar"])
              + " " + bar_dt
              + " " + r["coin"]
              + " " + r["grade"]
              + " pnl=$" + "{:+,.2f}".format(r["net_pnl"])
              + " recs=" + str(r["n_records"]))
        rej_count += 1

# Show concurrent position timeline at rejection points
if rejected:
    print("\n--- Active positions at first 5 rejection points ---")
    for r in rejected[:5]:
        bar = r["entry_bar"]
        bar_dt = str(master_dt[bar])[:19] if bar < n_bars else ""
        # Reconstruct what was active at this bar
        active_at_bar = []
        for p in accepted:
            if p["entry_bar"] <= bar and p["exit_bar"] > bar:
                active_at_bar.append(p)
        coins_active = {}
        for p in active_at_bar:
            c = p["coin"]
            if c not in coins_active:
                coins_active[c] = 0
            coins_active[c] += 1
        coin_str = ", ".join(c + ":" + str(n) for c, n in sorted(coins_active.items()))
        print("  bar=" + str(bar) + " " + bar_dt
              + " | rejected=" + r["coin"] + " " + r["grade"]
              + " | active=" + str(len(active_at_bar))
              + " (" + coin_str + ")"
              + " | margin=$" + "{:,.0f}".format(len(active_at_bar) * MARGIN))

# Sanity: verify balance math
print("\n--- Balance Sanity Check ---")
sum_acc_pnl = sum(p["net_pnl"] for p in accepted)
expected_pool = TOTAL_CAPITAL + sum_acc_pnl + total_rebate_settled
print("  sum(accepted net_pnl)  = $" + "{:+,.2f}".format(sum_acc_pnl))
print("  total_rebate_settled   = $" + "{:,.2f}".format(total_rebate_settled))
print("  CAPITAL + pnl + rebate = $" + "{:,.2f}".format(expected_pool))
print("  final_pool             = $" + "{:,.2f}".format(final_pool))
print("  delta (should be 0)    = $" + "{:+,.6f}".format(final_pool - expected_pool))

# Cross check: engine per-coin net sum
engine_net_sum = sum(cr["metrics"]["net_pnl"] for cr in coin_results)
engine_rebate_sum = sum(cr["metrics"].get("total_rebate", 0) for cr in coin_results)
engine_after_sum = sum(cr["metrics"].get("net_pnl_after_rebate", cr["metrics"]["net_pnl"]) for cr in coin_results)
eq_sum = sum(float(cr["equity_curve"][-1]) - 10000.0 for cr in coin_results)
print("\n  Engine total net_pnl:        $" + "{:+,.2f}".format(engine_net_sum))
print("  Engine total rebate:         $" + "{:,.2f}".format(engine_rebate_sum))
print("  Engine total after rebate:   $" + "{:+,.2f}".format(engine_after_sum))
print("  Engine eq sum (eq[-1]-10k):  $" + "{:+,.2f}".format(eq_sum))
print("  Pool accepted net_pnl:       $" + "{:+,.2f}".format(sum_acc_pnl))
print("  Difference (engine - pool):  $" + "{:+,.2f}".format(engine_net_sum - sum_acc_pnl))
if rejected:
    rej_pnl_total = sum(p["net_pnl"] for p in rejected)
    print("  Rejected total net_pnl:      $" + "{:+,.2f}".format(rej_pnl_total))
    print("  engine_net = pool_acc + rej?  $" + "{:+,.6f}".format(engine_net_sum - sum_acc_pnl - rej_pnl_total))

print("\n" + "=" * 70)
print("TRACE COMPLETE -- check results/ folder for CSVs")
print("=" * 70)
