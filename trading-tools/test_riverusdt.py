"""
Quick test: Run backtest on RIVERUSDT 5m data.

Usage:
    cd trading-tools
    python test_riverusdt.py
"""

import sys
from pathlib import Path

# Add vince to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pandas as pd
    from vince.strategies.indicators import calculate_all_indicators
    from vince.strategies.signals import FourPillarsSignals
    from vince.engine.backtester import SimpleFourPillarsBacktester
except ImportError as e:
    print(f"[ERROR] Missing dependencies: {e}")
    print("\nInstall required packages:")
    print("  pip install pandas numpy")
    sys.exit(1)


def main():
    """Run test backtest."""
    print("="*60)
    print("Four Pillars v3.8 — RIVERUSDT 5m Backtest")
    print("="*60)
    print()

    # Load data
    data_path = Path("../PROJECTS/four-pillars-backtester/data/cache/RIVERUSDT_5m.parquet")

    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        print("Run resample_timeframes.py first to generate 5m data")
        return 1

    print(f"[1/4] Loading data: {data_path.name}")
    df = pd.read_parquet(data_path)
    print(f"      Loaded {len(df)} candles")
    print(f"      Date range: {df.index[0]} to {df.index[-1]}")
    print()

    # Calculate indicators
    print(f"[2/4] Calculating indicators...")
    df = calculate_all_indicators(df)
    print(f"      Added: stoch_9_3, stoch_14_3, stoch_40_3, stoch_60_10")
    print(f"      Added: ema5-89, cloud tops/bottoms, price_pos, atr")
    print()

    # Generate signals
    print(f"[3/4] Generating A/B/C signals...")
    signal_gen = FourPillarsSignals(
        cross_level=25,
        zone_level=30,
        cooldown_bars=3,
        allow_b_trades=True,
        allow_c_trades=True
    )
    df = signal_gen.generate_signals(df)

    long_a = df['enter_long_a'].sum()
    long_bc = df['enter_long_bc'].sum()
    short_a = df['enter_short_a'].sum()
    short_bc = df['enter_short_bc'].sum()

    print(f"      Long A: {long_a}, Long B/C: {long_bc}")
    print(f"      Short A: {short_a}, Short B/C: {short_bc}")
    print(f"      Total signals: {long_a + long_bc + short_a + short_bc}")
    print()

    # Run backtest
    print(f"[4/4] Running backtest...")
    backtester = SimpleFourPillarsBacktester(
        initial_capital=10000,
        position_size=10000,
        sl_atr_mult=1.0,
        tp_atr_mult=1.5,
        commission_per_side=8.0
    )

    results = backtester.run(df)

    # Print results
    print()
    print("="*60)
    print("RESULTS")
    print("="*60)

    metrics = results['metrics']
    print(f"Total Trades:     {metrics['total_trades']}")
    print(f"Win Rate:         {metrics['win_rate']:.2%}")
    print(f"Total P&L:        ${metrics['total_pnl']:,.2f}")
    print(f"Total Commission: ${metrics['total_commission']:,.2f}")
    print(f"Net P&L:          ${metrics['net_pnl']:,.2f}")
    print(f"Avg Win:          ${metrics['avg_win']:,.2f}")
    print(f"Avg Loss:         ${metrics['avg_loss']:,.2f}")
    print(f"Sharpe Ratio:     {metrics['sharpe']:.2f}")
    print(f"SQN:              {metrics['sqn']:.2f}")
    print()

    if results['trades']:
        print("First 5 trades:")
        for i, trade in enumerate(results['trades'][:5]):
            pnl_sign = '+' if trade.pnl >= 0 else ''
            print(f"  {i+1}. {trade.direction:5s} @ ${trade.entry_price:.4f} → "
                  f"${trade.exit_price:.4f} = {pnl_sign}${trade.pnl:.2f} ({trade.grade})")

        print()
        print("Last 5 trades:")
        for i, trade in enumerate(results['trades'][-5:]):
            pnl_sign = '+' if trade.pnl >= 0 else ''
            print(f"  {i+1}. {trade.direction:5s} @ ${trade.entry_price:.4f} → "
                  f"${trade.exit_price:.4f} = {pnl_sign}${trade.pnl:.2f} ({trade.grade})")

    print()
    print("[OK] Test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
