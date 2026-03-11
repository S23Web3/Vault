"""
Standalone runner for 55/89 EMA Cross Scalp backtest.

Loads parquet, computes signals, runs Backtester384, prints metrics.

Run: python scripts/run_55_89_backtest.py --symbol BTCUSDT --months 3
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

from signals.ema_cross_55_89 import compute_signals_55_89
from engine.backtester_v384 import Backtester384


def load_parquet(symbol, months=None):
    """Load 1m parquet for symbol from data/historical/ or data/cache/."""
    for subdir in ["historical", "cache"]:
        path = ROOT / "data" / subdir / f"{symbol}_1m.parquet"
        if path.exists():
            df = pd.read_parquet(path)
            if months and "datetime" in df.columns:
                cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=months * 30)
                df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
                df = df[df["datetime"] >= cutoff].reset_index(drop=True)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Loaded {len(df)} bars from {path}")
            return df
    print(f"ERROR: No parquet found for {symbol}")
    sys.exit(1)


def main():
    """Run the 55/89 backtest from CLI."""
    parser = argparse.ArgumentParser(description="55/89 EMA Cross Scalp Backtest")
    parser.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    parser.add_argument("--months", type=int, default=None, help="Limit to last N months")
    parser.add_argument("--sl-mult", type=float, default=2.5, help="SL ATR multiplier (default 2.5)")
    parser.add_argument("--slope-n", type=int, default=5, help="Slope window N (default 5)")
    parser.add_argument("--slope-m", type=int, default=3, help="Accel window M (default 3)")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] 55/89 EMA Cross Scalp Backtest")
    print(f"[{ts}] Symbol: {args.symbol}, SL mult: {args.sl_mult}")

    df = load_parquet(args.symbol, args.months)

    sig_params = {
        "slope_n": args.slope_n,
        "slope_m": args.slope_m,
    }

    bt_params = {
        "sl_mult": args.sl_mult,
        "tp_mult": None,
        "be_trigger_atr": 0.0,
        "be_lock_atr": 0.0,
        "notional": 5000.0,
        "max_positions": 1,
        "cooldown": 1,
        "enable_adds": False,
        "enable_reentry": False,
        "commission_rate": 0.0008,
        "initial_equity": 10000.0,
    }

    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] Computing signals...")
    df_sig = compute_signals_55_89(df.copy(), sig_params)

    long_count = int(df_sig["long_a"].sum())
    short_count = int(df_sig["short_a"].sum())
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] Signals: {long_count} long, {short_count} short")

    print(f"[{ts}] Running backtest...")
    bt = Backtester384(bt_params)
    results = bt.run(df_sig)
    m = results["metrics"]

    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"\n[{ts}] === RESULTS ===")
    print(f"  Total trades:    {m.get('total_trades', 0)}")
    print(f"  Win rate:        {m.get('win_rate', 0):.1%}")
    print(f"  Net PnL:         ${m.get('net_pnl', 0):.2f}")
    print(f"  Profit factor:   {m.get('profit_factor', 0):.2f}")
    print(f"  Sharpe:          {m.get('sharpe', 0):.3f}")
    print(f"  Max drawdown:    {m.get('max_drawdown_pct', 0):.1f}%")
    print(f"  Avg win:         ${m.get('avg_win', 0):.2f}")
    print(f"  Avg loss:        ${m.get('avg_loss', 0):.2f}")
    print(f"  Expectancy:      ${m.get('expectancy', 0):.2f}")
    print(f"  Commission:      ${m.get('total_commission', 0):.2f}")
    print(f"  Rebate:          ${m.get('total_rebate', 0):.2f}")

    trades_df = results.get("trades_df")
    if trades_df is not None and len(trades_df) > 0:
        print(f"\n  Grade breakdown:")
        for grade_name, grade_data in m.get("grades", {}).items():
            print(f"    {grade_name}: {grade_data['count']} trades, "
                  + f"{grade_data['win_rate']:.0%} WR, "
                  + f"${grade_data['total_pnl']:.2f} PnL")


if __name__ == "__main__":
    main()
