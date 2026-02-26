"""
CLI entry point for v3.8.4 backtest.
ATR SL + optional ATR TP, scale-out, D signal, AVWAP inheritance.

Usage:
  python scripts/run_backtest_v384.py --symbol RIVERUSDT
  python scripts/run_backtest_v384.py --symbol RIVERUSDT --tp-mult 2.0
  python scripts/run_backtest_v384.py --symbol KITEUSDT --sl-mult 2.0 --tp-mult 1.5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v384 import Backtester384


CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def load_cached(symbol: str, timeframe: str = "5m") -> pd.DataFrame:
    path = CACHE_DIR / f"{symbol}_{timeframe}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    return df


def print_results(symbol: str, m: dict, timeframe: str = "5m", tp_mult=None):
    tp_label = f"{tp_mult} ATR" if tp_mult else "none"
    print(f"\n{'=' * 55}")
    print(f"  v3.8.4 BACKTEST: {symbol} ({timeframe})")
    print(f"{'=' * 55}")
    print(f"  Total trades:     {m['total_trades']}")
    print(f"  Win rate:         {m['win_rate']:.1%}")
    print(f"  Expectancy:       ${m['expectancy']:.2f}/trade")
    print(f"  Net P&L:          ${m['net_pnl']:.2f}")
    print(f"  Profit factor:    {m['profit_factor']:.2f}")
    print(f"  Sharpe:           {m['sharpe']:.2f}")
    print(f"  Max drawdown:     ${m['max_drawdown']:.2f} ({m['max_drawdown_pct']:.1f}%)")
    print(f"  Total commission: ${m['total_commission']:.2f}")
    print(f"  Total rebate:     ${m.get('total_rebate', 0):.2f}")
    net_ar = m.get("net_pnl_after_rebate", m["net_pnl"] + m.get("total_rebate", 0))
    per_trade_ar = net_ar / max(m["total_trades"], 1)
    print(f"  NET (w/rebate):   ${net_ar:.2f} (${per_trade_ar:.2f}/trade)")
    print(f"  Scale-outs:       {m.get('scale_out_count', 0)}")
    tp_ex = m.get("tp_exits", 0)
    sl_ex = m.get("sl_exits", 0)
    print(f"  TP exits:         {tp_ex}  (TP={tp_label})")
    print(f"  SL exits:         {sl_ex}")
    vol = m.get("total_volume", 0)
    sides = m.get("total_sides", 0)
    print(f"  Trading volume:   ${vol:,.0f} ({sides:,} sides)")
    print(f"  Losers saw green: {m['pct_losers_saw_green']:.0%} ({m['saw_green_losers']}/{m['total_losers']})")

    if m.get("grades"):
        print(f"\n  Grade breakdown:")
        for grade, stats in m["grades"].items():
            tp_g = stats.get("tp_exits", 0)
            tp_str = f", TP={tp_g}" if tp_g > 0 else ""
            print(f"    {grade}: {stats['count']} trades, "
                  f"{stats['win_rate']:.0%} WR, ${stats['avg_pnl']:.2f}/trade{tp_str}")

    # Capital utilization
    avg_pos = m.get("avg_positions", 0)
    max_pos = m.get("max_positions_used", 0)
    pct_flat = m.get("pct_time_flat", 0)
    avg_margin = m.get("avg_margin_used", 0)
    peak_margin = m.get("peak_margin_used", 0)
    margin_per = peak_margin / max(max_pos, 1)

    print(f"\n  Capital utilization:")
    print(f"    Avg positions:    {avg_pos:.1f} / {max_pos} max")
    print(f"    % time flat:      {pct_flat:.1%}")
    print(f"    Margin/position:  ${margin_per:,.0f}")
    print(f"    Avg margin used:  ${avg_margin:,.0f}")
    print(f"    Peak margin used: ${peak_margin:,.0f}")


def main():
    parser = argparse.ArgumentParser(description="Run Four Pillars v3.8.4 backtest")
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--timeframe", type=str, default="5m", choices=["1m", "5m"])
    parser.add_argument("--rebate", type=float, default=0.70)
    parser.add_argument("--notional", type=float, default=5000.0)
    parser.add_argument("--cooldown", type=int, default=3)
    parser.add_argument("--max-positions", type=int, default=4)
    parser.add_argument("--sl-mult", type=float, default=2.5)
    parser.add_argument("--tp-mult", type=float, default=None)
    parser.add_argument("--checkpoint", type=int, default=5)
    parser.add_argument("--max-scaleouts", type=int, default=2)
    parser.add_argument("--sigma-floor", type=float, default=0.5)
    parser.add_argument("--no-adds", action="store_true")
    parser.add_argument("--no-reentry", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    params = {
        "commission_rate": 0.0008,
        "maker_rate": 0.0002,
        "rebate_pct": args.rebate,
        "notional": args.notional,
        "cooldown": args.cooldown,
        "max_positions": args.max_positions,
        "sl_mult": args.sl_mult,
        "tp_mult": args.tp_mult,
        "checkpoint_interval": args.checkpoint,
        "max_scaleouts": args.max_scaleouts,
        "sigma_floor_atr": args.sigma_floor,
        "enable_adds": not args.no_adds,
        "enable_reentry": not args.no_reentry,
        "b_open_fresh": True,
    }

    df = load_cached(args.symbol, args.timeframe)
    if df is None:
        print(f"No {args.timeframe} cached data for {args.symbol}")
        sys.exit(1)

    print(f"Loaded {len(df)} candles for {args.symbol} ({args.timeframe})")

    df = compute_signals_v383(df, params)
    print("Signals computed (v3.8.4)")

    bt = Backtester384(params)
    results = bt.run(df)

    print_results(args.symbol, results["metrics"], args.timeframe, args.tp_mult)

    if args.output:
        results["trades_df"].to_csv(args.output, index=False)
        print(f"\nTrade log saved to {args.output}")


if __name__ == "__main__":
    main()
