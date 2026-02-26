"""
Capital Utilization & Conflict Analysis for v3.8.3 Multi-Coin.

Runs backtests on N coins, overlays position timelines, checks:
1. How much margin is used per bar across all coins combined
2. Whether combined positions ever exceed account capacity
3. Peak/avg capital deployed, idle capital, max coins possible
4. LSG% per coin and combined

Usage:
  python scripts/capital_analysis_v383.py
  python scripts/capital_analysis_v383.py --coins 10 --seed 42
  python scripts/capital_analysis_v383.py --account 10000 --sl-mult 2.5
"""

import argparse
import random
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v383 import Backtester383

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def list_5m_coins():
    return sorted([f.stem.replace("_5m", "") for f in CACHE_DIR.glob("*_5m.parquet")])


def load_5m(symbol):
    path = CACHE_DIR / f"{symbol}_5m.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    return df


def run_coin(symbol, df, params):
    """Run backtest, return (metrics, position_counts, datetime_index) or None."""
    try:
        df_sig = compute_signals_v383(df.copy(), params)
        bt = Backtester383(params)
        results = bt.run(df_sig)
        m = results["metrics"]
        m["symbol"] = symbol
        pos_counts = results["position_counts"]

        # Build datetime index
        if "datetime" in df_sig.columns:
            dt_index = pd.DatetimeIndex(df_sig["datetime"].values)
        elif df_sig.index.name == "datetime" or isinstance(df_sig.index, pd.DatetimeIndex):
            dt_index = df_sig.index
        else:
            dt_index = pd.RangeIndex(len(df_sig))

        return m, pos_counts, dt_index
    except Exception as e:
        print(f"  ERROR on {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="Capital utilization analysis v3.8.3")
    parser.add_argument("--coins", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--account", type=float, default=10000.0)
    parser.add_argument("--notional", type=float, default=5000.0)
    parser.add_argument("--leverage", type=float, default=20.0)
    parser.add_argument("--rebate", type=float, default=0.70)
    parser.add_argument("--sl-mult", type=float, default=2.5)
    parser.add_argument("--max-positions", type=int, default=4)
    args = parser.parse_args()

    random.seed(args.seed)
    margin_per_pos = args.notional / args.leverage

    params = {
        "notional": args.notional,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": args.rebate,
        "max_positions": args.max_positions,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": args.sl_mult,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "enable_adds": True,
        "enable_reentry": True,
        "b_open_fresh": True,
    }

    all_coins = list_5m_coins()
    selected = random.sample(all_coins, min(args.coins, len(all_coins)))
    print(f"Running v3.8.3 backtest on {len(selected)} coins (seed={args.seed}, sl_mult={args.sl_mult})")
    print(f"Account: ${args.account:,.0f} | Notional: ${args.notional:,.0f} | "
          f"Leverage: {args.leverage:.0f}x | Margin/pos: ${margin_per_pos:.0f}")
    print(f"Max positions per coin: {args.max_positions} | Rebate: {args.rebate*100:.0f}%\n")

    # Run all coins
    coin_results = {}
    coin_pos_series = {}

    for coin in selected:
        df = load_5m(coin)
        if df is None or len(df) < 200:
            print(f"  {coin}: SKIP")
            continue

        t0 = time.time()
        result = run_coin(coin, df, params)
        elapsed = time.time() - t0

        if result is None:
            continue

        m, pos_counts, dt_index = result
        coin_results[coin] = m

        # Create position count series with datetime index
        if isinstance(dt_index, pd.DatetimeIndex):
            pos_series = pd.Series(pos_counts, index=dt_index, name=coin)
        else:
            pos_series = pd.Series(pos_counts, name=coin)
        coin_pos_series[coin] = pos_series

        net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
        print(f"  {coin}: {m['total_trades']} trades, ${net_ar:,.2f} net, "
              f"avg_pos={m.get('avg_positions', 0):.1f}, "
              f"flat={m.get('pct_time_flat', 0):.0%}, "
              f"LSG={m.get('pct_losers_saw_green', 0):.0%} ({elapsed:.1f}s)")

    if not coin_results:
        print("No results to analyze.")
        sys.exit(1)

    # ── Combine position timelines ──────────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  CAPITAL UTILIZATION ANALYSIS: v3.8.3")
    print(f"  {len(coin_results)} coins | SL mult: {args.sl_mult} | "
          f"Account: ${args.account:,.0f}")
    print(f"{'=' * 78}")

    # Align all position series on common datetime index
    has_datetime = all(isinstance(s.index, pd.DatetimeIndex) for s in coin_pos_series.values())

    if has_datetime and coin_pos_series:
        all_index = coin_pos_series[list(coin_pos_series.keys())[0]].index
        for coin, series in coin_pos_series.items():
            all_index = all_index.union(series.index)

        combined_pos = pd.Series(0, index=all_index, dtype=int)
        for coin, series in coin_pos_series.items():
            aligned = series.reindex(all_index, fill_value=0)
            combined_pos += aligned

        combined_margin = combined_pos * margin_per_pos
    else:
        # Fallback: just sum the arrays (assumes same length/alignment)
        max_len = max(len(s) for s in coin_pos_series.values())
        combined_pos_arr = np.zeros(max_len, dtype=int)
        for series in coin_pos_series.values():
            combined_pos_arr[:len(series)] += series.values
        combined_pos = pd.Series(combined_pos_arr)
        combined_margin = combined_pos * margin_per_pos

    # ── Per-Coin Summary ────────────────────────────────────────────────
    print(f"\n  PER-COIN SUMMARY")
    print(f"  {'Symbol':<18} {'Trades':>7} {'WR':>5} {'LSG%':>5} {'Net(+reb)':>12} "
          f"{'$/Trade':>8} {'AvgPos':>7} {'Flat%':>6} {'AvgMgn':>8} {'PkMgn':>7} {'Scales':>7}")
    print(f"  {'-'*18} {'-'*7} {'-'*5} {'-'*5} {'-'*12} {'-'*8} {'-'*7} {'-'*6} {'-'*8} {'-'*7} {'-'*7}")

    total_trades = 0
    total_net = 0
    total_comm = 0
    total_rebate = 0
    total_scales = 0

    for coin, m in sorted(coin_results.items()):
        net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
        per_trade = net_ar / max(m["total_trades"], 1)
        avg_p = m.get("avg_positions", 0)
        flat = m.get("pct_time_flat", 0)
        avg_m = m.get("avg_margin_used", 0)
        pk_m = m.get("peak_margin_used", 0)
        lsg = m.get("pct_losers_saw_green", 0)
        sc = m.get("scale_out_count", 0)

        flag = "  " if net_ar >= 0 else "<<"
        print(f"  {coin:<18} {m['total_trades']:>7,} {m['win_rate']:>4.0%} {lsg:>4.0%} "
              f"${net_ar:>10,.2f} ${per_trade:>6.2f} {avg_p:>6.1f} {flat:>5.0%} "
              f"${avg_m:>6,.0f} ${pk_m:>5,.0f} {sc:>6} {flag}")

        total_trades += m["total_trades"]
        total_net += net_ar
        total_comm += m["total_commission"]
        total_rebate += m.get("total_rebate", 0)
        total_scales += sc

    print(f"  {'-'*18} {'-'*7} {'-'*5} {'-'*5} {'-'*12} {'-'*8} {'-'*7} {'-'*6} {'-'*8} {'-'*7} {'-'*7}")
    print(f"  {'TOTAL':<18} {total_trades:>7,} {'':>5} {'':>5} ${total_net:>10,.2f} "
          f"${total_net/max(total_trades,1):>6.2f} {'':>7} {'':>6} {'':>8} {'':>7} {total_scales:>6}")

    # ── Combined Capital Analysis ───────────────────────────────────────
    print(f"\n  COMBINED CAPITAL ANALYSIS ({len(coin_results)} coins simultaneous)")
    print(f"  {'-' * 60}")

    avg_combined_pos = combined_pos.mean()
    max_combined_pos = int(combined_pos.max())
    avg_combined_margin = float(combined_margin.mean())
    peak_combined_margin = float(combined_margin.max())
    pct_all_flat = float((combined_pos == 0).mean())

    print(f"  Avg combined positions:    {avg_combined_pos:.1f}")
    print(f"  Max combined positions:    {max_combined_pos}")
    print(f"  Avg combined margin:       ${avg_combined_margin:,.0f}")
    print(f"  Peak combined margin:      ${peak_combined_margin:,.0f}")
    print(f"  % time ALL flat:           {pct_all_flat:.1%}")
    print(f"  Avg idle capital:          ${args.account - avg_combined_margin:,.0f}")

    # ── Conflict Detection ──────────────────────────────────────────────
    print(f"\n  CONFLICT DETECTION")
    print(f"  {'-' * 60}")

    max_capacity = int(args.account / margin_per_pos)
    print(f"  Account capacity:          {max_capacity} positions (${args.account:,.0f} / ${margin_per_pos:.0f})")

    conflict_bars = combined_pos[combined_pos > max_capacity]
    if len(conflict_bars) > 0:
        print(f"  CONFLICTS FOUND:           {len(conflict_bars)} bars exceed capacity")
        print(f"  Conflict %:                {len(conflict_bars) / len(combined_pos):.2%}")
        print(f"  Max positions needed:      {max_combined_pos}")
        print(f"  Overshoot:                 {max_combined_pos - max_capacity} positions over limit")
        if has_datetime and isinstance(conflict_bars.index, pd.DatetimeIndex):
            print(f"  First conflict:            {conflict_bars.index[0]}")
            print(f"  Last conflict:             {conflict_bars.index[-1]}")
    else:
        print(f"  NO CONFLICTS. Peak {max_combined_pos} positions < {max_capacity} capacity.")
        headroom = max_capacity - max_combined_pos
        more_coins = int(headroom / args.max_positions) if args.max_positions > 0 else 0
        print(f"  Headroom:                  {headroom} positions spare at peak")
        print(f"  Could add:                 ~{more_coins} more coins (at {args.max_positions} max/coin)")

    # ── Position Distribution (combined) ────────────────────────────────
    print(f"\n  COMBINED POSITION DISTRIBUTION")
    print(f"  {'-' * 60}")
    for level in range(0, max_combined_pos + 1):
        pct = float((combined_pos == level).mean())
        bar = '#' * int(pct * 50)
        print(f"  {level:>3} positions: {pct:>6.1%}  {bar}")

    # ── Scaling Projection ──────────────────────────────────────────────
    print(f"\n  SCALING PROJECTION")
    print(f"  {'-' * 60}")

    avg_net_per_coin = total_net / len(coin_results)
    avg_margin_per_coin = avg_combined_margin / len(coin_results)

    for n_coins in [10, 20, 30, 40, 50]:
        proj_margin = avg_margin_per_coin * n_coins
        proj_net = avg_net_per_coin * n_coins
        proj_peak = (peak_combined_margin / len(coin_results)) * n_coins
        fits = "OK" if proj_peak <= args.account else f"NEED ${proj_peak:,.0f}"
        print(f"  {n_coins:>3} coins: ~${proj_net:>10,.0f} net | "
              f"avg margin ${proj_margin:>6,.0f} | peak ~${proj_peak:>6,.0f} | {fits}")

    # ── P&L Breakdown ───────────────────────────────────────────────────
    print(f"\n  P&L BREAKDOWN")
    print(f"  {'-' * 60}")
    gross_pnl = sum(m["gross_profit"] - m["gross_loss"] for m in coin_results.values())
    print(f"  Gross P&L (price only):    ${gross_pnl:,.2f}")
    print(f"  Total commission:          ${total_comm:,.2f}")
    print(f"  Total rebate ({args.rebate*100:.0f}%):        ${total_rebate:,.2f}")
    print(f"  Net commission:            ${total_comm - total_rebate:,.2f}")
    print(f"  Net P&L (after rebate):    ${total_net:,.2f}")
    print(f"  Per trade (after rebate):  ${total_net/max(total_trades,1):.2f}")
    print(f"  Total scale-outs:          {total_scales:,}")

    print(f"\n{'=' * 78}")


if __name__ == "__main__":
    main()
