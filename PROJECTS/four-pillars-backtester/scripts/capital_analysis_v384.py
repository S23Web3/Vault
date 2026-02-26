"""
Capital usage analysis for v3.8.4 multi-coin.
Runs backtests, overlays equity curves and position timelines.

Usage:
  python scripts/capital_analysis_v384.py
  python scripts/capital_analysis_v384.py --coins RIVERUSDT KITEUSDT BERAUSDT
"""

import argparse
import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v384 import Backtester384

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


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
    try:
        df_sig = compute_signals_v383(df.copy(), params)
        bt = Backtester384(params)
        results = bt.run(df_sig)
        m = results["metrics"]
        m["symbol"] = symbol

        if "datetime" in df_sig.columns:
            dt_index = pd.DatetimeIndex(df_sig["datetime"].values)
        elif isinstance(df_sig.index, pd.DatetimeIndex):
            dt_index = df_sig.index
        else:
            dt_index = pd.RangeIndex(len(df_sig))

        return m, results["position_counts"], results["equity_curve"], dt_index
    except Exception as e:
        print(f"  ERROR on {symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="Capital analysis v3.8.4")
    parser.add_argument("--coins", nargs="+", default=["RIVERUSDT", "KITEUSDT", "BERAUSDT"])
    parser.add_argument("--account", type=float, default=10000.0)
    parser.add_argument("--notional", type=float, default=5000.0)
    parser.add_argument("--leverage", type=float, default=20.0)
    parser.add_argument("--rebate", type=float, default=0.70)
    parser.add_argument("--sl-mult", type=float, default=2.5)
    parser.add_argument("--tp-mult", type=float, default=2.0)
    args = parser.parse_args()

    margin_per_pos = args.notional / args.leverage

    params = {
        "notional": args.notional,
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": args.rebate,
        "max_positions": 4,
        "cooldown": 3,
        "sigma_floor_atr": 0.5,
        "sl_mult": args.sl_mult,
        "tp_mult": args.tp_mult if args.tp_mult > 0 else None,
        "checkpoint_interval": 5,
        "max_scaleouts": 2,
        "enable_adds": True,
        "enable_reentry": True,
        "b_open_fresh": True,
    }

    tp_label = f"{args.tp_mult} ATR" if args.tp_mult > 0 else "none"
    print(f"v3.8.4 Capital Analysis: {len(args.coins)} coins")
    print(f"Account: ${args.account:,.0f} | Notional: ${args.notional:,.0f} | "
          f"Leverage: {args.leverage:.0f}x | Margin/pos: ${margin_per_pos:.0f}")
    print(f"SL: {args.sl_mult} ATR | TP: {tp_label} | Rebate: {args.rebate*100:.0f}%\n")

    coin_data = {}

    for symbol in args.coins:
        df = load_5m(symbol)
        if df is None or len(df) < 200:
            print(f"  {symbol}: SKIP (no data)")
            continue

        t0 = time.time()
        result = run_coin(symbol, df, params)
        elapsed = time.time() - t0

        if result is None:
            continue

        m, pos_counts, eq_curve, dt_index = result
        coin_data[symbol] = {
            "metrics": m,
            "pos_counts": pos_counts,
            "equity_curve": eq_curve,
            "dt_index": dt_index,
        }

        net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
        print(f"  {symbol}: {m['total_trades']} trades, ${net_ar:,.2f} net, "
              f"DD=${m['max_drawdown']:,.0f}, TP={m.get('tp_exits',0)}, "
              f"SL={m.get('sl_exits',0)} ({elapsed:.1f}s)")

    if not coin_data:
        print("No results.")
        sys.exit(1)

    # ── Align timelines ─────────────────────────────────────────
    has_datetime = all(isinstance(d["dt_index"], pd.DatetimeIndex) for d in coin_data.values())

    if has_datetime:
        # Build common datetime index
        all_idx = list(coin_data.values())[0]["dt_index"]
        for d in coin_data.values():
            all_idx = all_idx.union(d["dt_index"])

        combined_pos = pd.Series(0, index=all_idx, dtype=int)
        combined_pnl = pd.Series(0.0, index=all_idx, dtype=float)

        for symbol, d in coin_data.items():
            pos_s = pd.Series(d["pos_counts"], index=d["dt_index"])
            aligned_pos = pos_s.reindex(all_idx, fill_value=0)
            combined_pos += aligned_pos

            # Equity change from initial (P&L per bar)
            eq_s = pd.Series(d["equity_curve"], index=d["dt_index"])
            aligned_eq = eq_s.reindex(all_idx, method="ffill")
            initial_eq = d["equity_curve"][0]
            pnl_s = aligned_eq - initial_eq
            combined_pnl += pnl_s
    else:
        max_len = max(len(d["pos_counts"]) for d in coin_data.values())
        combined_pos_arr = np.zeros(max_len, dtype=int)
        combined_pnl_arr = np.zeros(max_len, dtype=float)
        for d in coin_data.values():
            pc = d["pos_counts"]
            combined_pos_arr[:len(pc)] += pc
            eq = d["equity_curve"]
            combined_pnl_arr[:len(eq)] += (eq - eq[0])
        combined_pos = pd.Series(combined_pos_arr)
        combined_pnl = pd.Series(combined_pnl_arr)

    # Combined equity curve (starting from account balance)
    combined_equity = args.account + combined_pnl
    combined_margin = combined_pos * margin_per_pos

    # Combined max drawdown
    peak = combined_equity.cummax()
    drawdown = peak - combined_equity
    combined_max_dd = float(drawdown.max())
    combined_max_dd_pct = float((drawdown / peak).max() * 100) if peak.max() > 0 else 0

    # ── Output ──────────────────────────────────────────────────
    print(f"\n{'=' * 78}")
    print(f"  CAPITAL ANALYSIS: v3.8.4 ({len(coin_data)} coins)")
    print(f"  Account: ${args.account:,.0f} | SL: {args.sl_mult} ATR | TP: {tp_label}")
    print(f"{'=' * 78}")

    # Per-coin summary
    print(f"\n  PER-COIN SUMMARY")
    print(f"  {'Symbol':<14} {'Trades':>7} {'WR':>5} {'Net(+reb)':>12} {'$/Tr':>7} "
          f"{'MaxDD':>8} {'DD%':>6} {'TP':>5} {'SL':>5} {'Volume':>12}")
    print(f"  {'-'*14} {'-'*7} {'-'*5} {'-'*12} {'-'*7} "
          f"{'-'*8} {'-'*6} {'-'*5} {'-'*5} {'-'*12}")

    total_trades = 0
    total_net = 0
    total_volume = 0

    for symbol, d in sorted(coin_data.items()):
        m = d["metrics"]
        net_ar = m.get("net_pnl_after_rebate", m["net_pnl"])
        pt = net_ar / max(m["total_trades"], 1)
        dd = m["max_drawdown"]
        dd_pct = m["max_drawdown_pct"]
        tp_ex = m.get("tp_exits", 0)
        sl_ex = m.get("sl_exits", 0)
        vol = m.get("total_volume", 0)
        print(f"  {symbol:<14} {m['total_trades']:>7,} {m['win_rate']:>4.0%} "
              f"${net_ar:>10,.2f} ${pt:>5.2f} "
              f"${dd:>6,.0f} {dd_pct:>5.1f}% "
              f"{tp_ex:>5} {sl_ex:>5} ${vol:>10,.0f}")
        total_trades += m["total_trades"]
        total_net += net_ar
        total_volume += vol

    print(f"  {'-'*14} {'-'*7} {'-'*5} {'-'*12} {'-'*7} "
          f"{'-'*8} {'-'*6} {'-'*5} {'-'*5} {'-'*12}")
    total_pt = total_net / max(total_trades, 1)
    print(f"  {'TOTAL':<14} {total_trades:>7,} {'':>5} "
          f"${total_net:>10,.2f} ${total_pt:>5.2f} "
          f"{'':>8} {'':>6} {'':>5} {'':>5} ${total_volume:>10,.0f}")

    # Combined capital
    print(f"\n  COMBINED CAPITAL ({len(coin_data)} coins simultaneous)")
    print(f"  {'-' * 60}")

    avg_pos = float(combined_pos.mean())
    max_pos = int(combined_pos.max())
    avg_margin = float(combined_margin.mean())
    peak_margin = float(combined_margin.max())
    pct_flat = float((combined_pos == 0).mean())
    idle_avg = args.account - avg_margin

    print(f"  Avg combined positions:    {avg_pos:.1f}")
    print(f"  Max combined positions:    {max_pos}")
    print(f"  Avg margin in use:         ${avg_margin:,.0f}")
    print(f"  Peak margin in use:        ${peak_margin:,.0f}")
    print(f"  % time ALL flat:           {pct_flat:.1%}")
    print(f"  Avg idle capital:          ${idle_avg:,.0f}")

    # Combined drawdown (THE KEY NUMBER)
    print(f"\n  COMBINED DRAWDOWN (overlapping equity curves)")
    print(f"  {'-' * 60}")

    # Individual DDs (for comparison)
    for symbol, d in sorted(coin_data.items()):
        m = d["metrics"]
        print(f"  {symbol:<14} DD: ${m['max_drawdown']:>6,.0f} ({m['max_drawdown_pct']:.1f}%)")

    print(f"  {'Sum of DDs':<14} DD: ${sum(d['metrics']['max_drawdown'] for d in coin_data.values()):>6,.0f} (worst case, no overlap)")
    print(f"  {'COMBINED':<14} DD: ${combined_max_dd:>6,.0f} ({combined_max_dd_pct:.1f}%) << ACTUAL")

    # Capital requirement
    print(f"\n  CAPITAL REQUIREMENT")
    print(f"  {'-' * 60}")
    print(f"  Peak margin needed:        ${peak_margin:,.0f}")
    print(f"  Combined max DD:           ${combined_max_dd:,.0f}")
    print(f"  Total needed (margin+DD):  ${peak_margin + combined_max_dd:,.0f}")
    print(f"  Account size:              ${args.account:,.0f}")

    headroom = args.account - (peak_margin + combined_max_dd)
    if headroom >= 0:
        print(f"  Headroom:                  ${headroom:,.0f} SAFE")
        extra_coins = int(headroom / (peak_margin / len(coin_data) + combined_max_dd / len(coin_data)))
        print(f"  Could add:                 ~{extra_coins} more coins")
    else:
        print(f"  SHORTFALL:                 ${-headroom:,.0f} NEED MORE CAPITAL")
        needed = peak_margin + combined_max_dd
        print(f"  Minimum account:           ${needed:,.0f}")

    # Final equity
    final_equity = float(combined_equity.iloc[-1])
    print(f"\n  FINAL RESULT")
    print(f"  {'-' * 60}")
    print(f"  Starting equity:           ${args.account:,.0f}")
    print(f"  Final equity:              ${final_equity:,.2f}")
    print(f"  Total net P&L:             ${total_net:,.2f}")
    print(f"  Return on account:         {total_net/args.account:.1%}")
    print(f"  Total trades:              {total_trades:,}")
    print(f"  Total volume:              ${total_volume:,.0f}")

    # Position distribution
    print(f"\n  COMBINED POSITION DISTRIBUTION")
    print(f"  {'-' * 60}")
    for level in range(0, max_pos + 1):
        pct = float((combined_pos == level).mean())
        bar = '#' * int(pct * 50)
        print(f"  {level:>3} positions: {pct:>6.1%}  {bar}")

    print(f"\n{'=' * 78}")


if __name__ == "__main__":
    main()
