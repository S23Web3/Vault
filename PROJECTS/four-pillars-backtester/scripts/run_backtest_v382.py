"""
CLI entry point for v3.8.2 backtest.
Uses AVWAP 3-stage trailing SL, multi-position slots, no TP.
Loads 5m cached data by default (optimal timeframe per testing).

Usage:
  python scripts/run_backtest_v382.py --symbol RIVERUSDT
  python scripts/run_backtest_v382.py --symbol BERAUSDT --timeframe 1m
  python scripts/run_backtest_v382.py --symbol KITEUSDT --rebate 0.70
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signals.four_pillars_v382 import compute_signals_v382
from engine.backtester_v382 import Backtester382


CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"


def load_cached(symbol: str, timeframe: str = "5m") -> pd.DataFrame:
    """Load cached Parquet data for a symbol + timeframe."""
    path = CACHE_DIR / f"{symbol}_{timeframe}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    # Ensure column naming consistency
    if "volume" in df.columns and "base_vol" not in df.columns:
        df = df.rename(columns={"volume": "base_vol"})
    if "turnover" in df.columns and "quote_vol" not in df.columns:
        df = df.rename(columns={"turnover": "quote_vol"})
    return df


def list_cached(timeframe: str = "5m") -> list:
    """List all cached symbols for a timeframe."""
    suffix = f"_{timeframe}.parquet"
    return sorted([f.stem.replace(suffix.replace(".parquet", ""), "")
                    for f in CACHE_DIR.glob(f"*{suffix}")])


def run_single(symbol: str, timeframe: str = "5m", params: dict = None) -> dict:
    """Run v3.8.2 backtest on one symbol. Returns results dict or None."""
    df = load_cached(symbol, timeframe)
    if df is None:
        return None

    df = compute_signals_v382(df, params or {})
    bt = Backtester382(params)
    return bt.run(df)


def print_results(symbol: str, m: dict, timeframe: str = "5m"):
    """Print formatted backtest results."""
    print(f"\n{'=' * 55}")
    print(f"  v3.8.2 BACKTEST: {symbol} ({timeframe})")
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
    print(f"  Losers saw green: {m['pct_losers_saw_green']:.0%} ({m['saw_green_losers']}/{m['total_losers']})")

    if m.get("grades"):
        print(f"\n  Grade breakdown:")
        for grade, stats in m["grades"].items():
            print(f"    {grade}: {stats['count']} trades, "
                  f"{stats['win_rate']:.0%} WR, ${stats['avg_pnl']:.2f}/trade")


def main():
    parser = argparse.ArgumentParser(description="Run Four Pillars v3.8.2 backtest")
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--timeframe", type=str, default="5m", choices=["1m", "5m"])
    parser.add_argument("--rebate", type=float, default=0.50)
    parser.add_argument("--notional", type=float, default=5000.0)
    parser.add_argument("--cooldown", type=int, default=3)
    parser.add_argument("--max-positions", type=int, default=4)
    parser.add_argument("--sigma-floor", type=float, default=0.5)
    parser.add_argument("--sl-atr-mult", type=float, default=1.0)
    parser.add_argument("--stage2-bars", type=int, default=5)
    parser.add_argument("--stage1to2", type=str, default="opposite_2sigma",
                        choices=["opposite_2sigma", "bars_5", "bars_10"])
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
        "sigma_floor_atr": args.sigma_floor,
        "sl_atr_mult": args.sl_atr_mult,
        "stage2_bars": args.stage2_bars,
        "stage1to2_trigger": args.stage1to2,
        "enable_adds": not args.no_adds,
        "enable_reentry": not args.no_reentry,
        "b_open_fresh": True,
    }

    df = load_cached(args.symbol, args.timeframe)
    if df is None:
        print(f"No {args.timeframe} cached data for {args.symbol}")
        sys.exit(1)

    print(f"Loaded {len(df)} candles for {args.symbol} ({args.timeframe})")

    df = compute_signals_v382(df, params)
    print("Signals computed (v3.8.2)")

    bt = Backtester382(params)
    results = bt.run(df)

    print_results(args.symbol, results["metrics"], args.timeframe)

    if args.output:
        results["trades_df"].to_csv(args.output, index=False)
        print(f"\nTrade log saved to {args.output}")


if __name__ == "__main__":
    main()
