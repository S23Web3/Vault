"""
CLI entry point for running a backtest on cached data.
Usage: python scripts/run_backtest.py --symbol BTCUSDT --months 3
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from data.fetcher import BybitFetcher
from signals.four_pillars import compute_signals
from engine.backtester import Backtester
from engine.metrics import trades_to_dataframe


def load_config() -> dict:
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Run Four Pillars backtest")
    parser.add_argument("--symbol", type=str, required=True, help="Symbol to backtest (e.g. BTCUSDT)")
    parser.add_argument("--be-raise", type=float, default=0.0, help="Breakeven raise amount in $ (0=disabled)")
    parser.add_argument("--rebate", type=float, default=0.70, help="Commission rebate % (0.70 or 0.50)")
    parser.add_argument("--sl", type=float, default=None, help="SL ATR multiplier (default: from config)")
    parser.add_argument("--tp", type=float, default=None, help="TP ATR multiplier (default: from config)")
    parser.add_argument("--cooldown", type=int, default=None, help="Min bars between entries")
    parser.add_argument("--output", type=str, default=None, help="Save trade log CSV to this path")
    parser.add_argument("--save-db", action="store_true", help="Save results to PostgreSQL vince database")
    args = parser.parse_args()

    config = load_config()
    strategy = config.get("strategy", {})
    commission = config.get("commission", {})

    # Load cached data
    fetcher = BybitFetcher(cache_dir=str(Path(__file__).resolve().parent.parent / "data" / "cache"))
    df = fetcher.load_cached(args.symbol)
    if df is None:
        print(f"No cached data for {args.symbol}. Run fetch_data.py first.")
        sys.exit(1)

    print(f"Loaded {len(df)} candles for {args.symbol}")

    # Compute signals
    signal_params = {
        "atr_length": strategy.get("atr_length", 14),
        "cross_level": strategy.get("cross_level", 25),
        "zone_level": strategy.get("zone_level", 30),
        "stage_lookback": strategy.get("stage_lookback", 10),
        "allow_b_trades": strategy.get("allow_b_trades", True),
        "allow_c_trades": strategy.get("allow_c_trades", True),
        "b_open_fresh": strategy.get("b_open_fresh", True),
        "cloud2_reentry": strategy.get("cloud2_reentry", True),
        "reentry_lookback": strategy.get("reentry_lookback", 10),
    }
    df = compute_signals(df, signal_params)
    print(f"Signals computed")

    # Run backtest
    bt_params = {
        "sl_mult": args.sl or strategy.get("sl_mult", 1.0),
        "tp_mult": args.tp or strategy.get("tp_mult", 1.5),
        "cooldown": args.cooldown if args.cooldown is not None else strategy.get("cooldown", 3),
        "b_open_fresh": strategy.get("b_open_fresh", True),
        "be_raise_amount": args.be_raise,
        "commission_rate": commission.get("commission_rate", 0.0008),
        "rebate_pct": args.rebate,
        "settlement_hour_utc": commission.get("settlement_hour_utc", 17),
    }
    bt = Backtester(bt_params)
    results = bt.run(df)

    # Print results
    m = results["metrics"]
    print("\n" + "=" * 50)
    print(f"BACKTEST RESULTS -- {args.symbol}")
    print("=" * 50)
    print(f"Total trades:     {m['total_trades']}")
    print(f"Win rate:         {m['win_rate']:.1%}")
    print(f"Expectancy:       ${m['expectancy']:.2f}/trade")
    print(f"Net P&L:          ${m['net_pnl']:.2f}")
    print(f"Profit factor:    {m['profit_factor']:.2f}")
    print(f"Sharpe:           {m['sharpe']:.2f}")
    print(f"Max drawdown:     ${m['max_drawdown']:.2f} ({m['max_drawdown_pct']:.1f}%)")
    print(f"Total commission: ${m['total_commission']:.2f}")
    print(f"Losers saw green: {m['pct_losers_saw_green']:.0%} ({m['saw_green_losers']}/{m['total_losers']})")
    print(f"BE raises:        {m['be_raised_count']}")

    if m.get("grades"):
        print(f"\nGrade breakdown:")
        for grade, stats in m["grades"].items():
            print(f"  {grade}: {stats['count']} trades, {stats['win_rate']:.0%} WR, ${stats['avg_pnl']:.2f}/trade")

    # Save trade log
    if args.output:
        results["trades_df"].to_csv(args.output, index=False)
        print(f"\nTrade log saved to {args.output}")

    # Save to PostgreSQL
    if args.save_db:
        from data.db import save_backtest_run
        run_id = save_backtest_run(
            symbol=args.symbol,
            timeframe="1m",
            params=bt_params,
            metrics=m,
            trades=results["trades"],
            equity_curve=results["equity_curve"],
        )
        print(f"\nSaved to database: run_id={run_id}")


if __name__ == "__main__":
    main()
