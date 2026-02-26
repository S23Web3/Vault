# QWEN FAST GENERATION — Core Vince Files Only (1-2 Hours)

**Goal**: Generate 5 essential files for immediate testing
**Estimated Time**: 30-90 minutes (not 6-12 hours)

---

## INSTRUCTIONS

Generate these 5 files in sequence. Each file should be complete and production-ready.

After each file, output: **"✓ [filename] COMPLETE"** then immediately start the next file.

---

## File 1: strategies/indicators.py (~200 lines)

```python
"""
Four Pillars indicator calculations.

Implements:
- Raw K Stochastics (9-3, 14-3, 40-3, 60-10)
- Ripster EMA Clouds (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89)
- ATR calculation
- Cloud 3 directional filter (price position vs Cloud 3)

All calculations match Pine Script v3.8 exactly.
"""

import pandas as pd
import numpy as np
from typing import Tuple

def stoch_k(df: pd.DataFrame, period: int, source_high: str = 'high',
            source_low: str = 'low', source_close: str = 'close') -> pd.Series:
    """
    Calculate Raw K Stochastic (K smoothing = 1, no D line).

    Args:
        df: DataFrame with OHLC data
        period: K period (e.g., 9, 14, 40, 60)
        source_high: Column name for high prices
        source_low: Column name for low prices
        source_close: Column name for close prices

    Returns:
        Series with stochastic K values (0-100)

    Example:
        >>> stoch_9_3 = stoch_k(df, period=9)
        >>> stoch_14_3 = stoch_k(df, period=14)
    """
    # [GENERATE IMPLEMENTATION]
    # Use rolling min/max, handle division by zero (return 50.0)
    pass


def calculate_ripster_clouds(df: pd.DataFrame,
                              ema5: int = 5, ema12: int = 12,
                              ema34: int = 34, ema50: int = 50,
                              ema72: int = 72, ema89: int = 89) -> pd.DataFrame:
    """
    Calculate Ripster EMA clouds and price position.

    Adds columns:
    - ema5, ema12, cloud2_bull, cloud2_top, cloud2_bottom
    - ema34, ema50, cloud3_bull, cloud3_top, cloud3_bottom
    - ema72, ema89, cloud4_bull
    - price_pos: -1 (below Cloud 3), 0 (inside), 1 (above)
    - cloud3_allows_long: True if price_pos >= 0
    - cloud3_allows_short: True if price_pos <= 0

    Args:
        df: DataFrame with 'close' column (modified in-place)
        ema5-ema89: EMA periods

    Returns:
        Modified DataFrame with new columns
    """
    # [GENERATE IMPLEMENTATION]
    # Calculate all EMAs using pandas .ewm()
    # Determine cloud tops/bottoms (max/min)
    # Calculate price_pos
    pass


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range.

    Args:
        df: DataFrame with 'high', 'low', 'close'
        period: ATR period (default 14)

    Returns:
        Series with ATR values
    """
    # [GENERATE IMPLEMENTATION]
    # TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
    # ATR = EMA(TR, period)
    pass


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all Four Pillars indicators in one call.

    Adds columns for stochastics, EMAs, clouds, ATR, and directional filters.

    Args:
        df: DataFrame with OHLC data

    Returns:
        Modified DataFrame with all indicator columns

    Example:
        >>> df = pd.read_parquet('RIVERUSDT_5m.parquet')
        >>> df = calculate_all_indicators(df)
        >>> print(df.columns)  # Now has stoch_9_3, ema34, cloud3_bull, atr, etc.
    """
    # [GENERATE IMPLEMENTATION]
    # Call all functions above
    # Return df with all columns added
    pass


# ✓ indicators.py COMPLETE
```

---

## File 2: strategies/signals.py (~250 lines)

```python
"""
Four Pillars A/B/C signal generation (state machine).

Implements:
- Stage 1 → Stage 2 state machine for A signals (4/4 stochs)
- B signals (3/4 stochs)
- C signals (2/4 stochs + Cloud 3)
- Cooldown gate (min bars between entries)
- Cloud 3 directional filter

Matches Pine Script v3.8 logic exactly.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class FourPillarsSignals:
    """
    Generate A/B/C entry signals using multi-stochastic state machine.
    """

    def __init__(self, cross_level: int = 25, zone_level: int = 30,
                 stage_lookback: int = 10, cooldown_bars: int = 3,
                 allow_b_trades: bool = True, allow_c_trades: bool = True):
        """
        Initialize signal generator.

        Args:
            cross_level: 9-3 stoch cross level (default 25)
            zone_level: Other stochs zone level (default 30)
            stage_lookback: Max bars in Stage 1 before expiry (default 10)
            cooldown_bars: Min bars between entries (default 3)
            allow_b_trades: Enable B signals (default True)
            allow_c_trades: Enable C signals (default True)
        """
        # [GENERATE IMPLEMENTATION]
        pass


    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate A/B/C signals for entire DataFrame.

        Requires columns: stoch_9_3, stoch_14_3, stoch_40_3, stoch_60_10,
                          cloud3_allows_long, cloud3_allows_short, price_pos

        Adds columns:
        - long_signal, long_signal_b, long_signal_c
        - short_signal, short_signal_b, short_signal_c
        - enter_long_a, enter_short_a (cooldown-gated A signals)
        - enter_long_bc, enter_short_bc (cooldown-gated B/C signals)

        Args:
            df: DataFrame with indicators already calculated

        Returns:
            Modified DataFrame with signal columns
        """
        # [GENERATE IMPLEMENTATION]
        # Use vectorized operations where possible
        # Fallback to row-by-row for state machine if needed
        pass


# ✓ signals.py COMPLETE
```

---

## File 3: engine/backtester.py (~300 lines)

```python
"""
Simple event-driven backtester for Four Pillars v3.8.

Features:
- Bar-by-bar execution
- Entry on A/B/C signals
- Static SL/TP (1.0 ATR SL, 1.5 ATR TP)
- Commission: $8/side ($16 round trip)
- MFE/MAE tracking
- Trade-by-trade results

Does NOT include (for speed):
- Breakeven raise (add later)
- Trailing TP (add later)
- Rebate calculation (add later)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Trade:
    """Single trade record."""
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp] = None
    direction: str = 'FLAT'  # 'LONG' or 'SHORT'
    entry_price: float = 0.0
    exit_price: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0
    max_price: float = 0.0  # MFE tracking
    min_price: float = 0.0  # MAE tracking
    grade: str = ''  # 'A', 'B', or 'C'
    pnl: float = 0.0
    commission: float = 16.0  # $8 per side


class SimpleFourPillarsBacktester:
    """
    Event-driven backtester for Four Pillars strategy.
    """

    def __init__(self, initial_capital: float = 10000,
                 position_size: float = 10000,
                 sl_atr_mult: float = 1.0,
                 tp_atr_mult: float = 1.5,
                 commission_per_side: float = 8.0):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting capital ($10,000)
            position_size: Notional size per trade ($10,000 = $500 margin × 20x)
            sl_atr_mult: SL distance in ATR (default 1.0)
            tp_atr_mult: TP distance in ATR (default 1.5)
            commission_per_side: Commission per side (default $8)
        """
        # [GENERATE IMPLEMENTATION]
        pass


    def run(self, df: pd.DataFrame) -> Dict:
        """
        Run backtest on DataFrame with signals.

        Requires columns: enter_long_a, enter_long_bc, enter_short_a, enter_short_bc, atr

        Args:
            df: DataFrame with signals and indicators

        Returns:
            Dictionary with:
            - trades: List[Trade] (all trades)
            - metrics: Dict (win_rate, total_pnl, sharpe, sqn, etc.)
            - equity_curve: pd.Series (cumulative P&L)
        """
        # [GENERATE IMPLEMENTATION]
        # Loop through each bar
        # Check for entry signals
        # Update MFE/MAE for open position
        # Check for SL/TP exit
        # Record completed trades
        pass


    def calculate_metrics(self, trades: List[Trade]) -> Dict:
        """
        Calculate performance metrics from trade list.

        Returns:
            Dict with win_rate, avg_win, avg_loss, total_pnl, sharpe, sqn, max_dd, etc.
        """
        # [GENERATE IMPLEMENTATION]
        pass


# ✓ backtester.py COMPLETE
```

---

## File 4: test_riverusdt.py (~100 lines)

```python
"""
Quick test: Run backtest on RIVERUSDT 5m data.

This is a standalone test script that loads data, calculates indicators,
generates signals, runs backtest, and prints results.

Usage:
    cd trading-tools
    python test_riverusdt.py
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from vince.strategies.indicators import calculate_all_indicators
from vince.strategies.signals import FourPillarsSignals
from vince.engine.backtester import SimpleFourPillarsBacktester


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

    print(f"[1/4] Loading data: {data_path}")
    df = pd.read_parquet(data_path)
    print(f"      Loaded {len(df)} candles ({df.index[0]} to {df.index[-1]})")
    print()

    # Calculate indicators
    print(f"[2/4] Calculating indicators...")
    df = calculate_all_indicators(df)
    print(f"      Added columns: {list(df.columns[-10:])}")  # Show last 10 columns
    print()

    # Generate signals
    print(f"[3/4] Generating A/B/C signals...")
    signal_gen = FourPillarsSignals(cooldown_bars=3)
    df = signal_gen.generate_signals(df)

    long_signals = df['enter_long_a'].sum() + df['enter_long_bc'].sum()
    short_signals = df['enter_short_a'].sum() + df['enter_short_bc'].sum()
    print(f"      Long signals: {long_signals}, Short signals: {short_signals}")
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
    print(f"Total Trades:    {metrics['total_trades']}")
    print(f"Win Rate:        {metrics['win_rate']:.2%}")
    print(f"Total P&L:       ${metrics['total_pnl']:,.2f}")
    print(f"Total Commission: ${metrics['total_commission']:,.2f}")
    print(f"Net P&L:         ${metrics['net_pnl']:,.2f}")
    print(f"Avg Win:         ${metrics['avg_win']:,.2f}")
    print(f"Avg Loss:        ${metrics['avg_loss']:,.2f}")
    print(f"Sharpe Ratio:    {metrics['sharpe']:.2f}")
    print(f"SQN:             {metrics['sqn']:.2f}")
    print(f"Max Drawdown:    ${metrics['max_drawdown']:,.2f} ({metrics['max_dd_pct']:.2%})")
    print()

    # Show first 5 trades
    print("First 5 trades:")
    for i, trade in enumerate(results['trades'][:5]):
        print(f"  {i+1}. {trade.direction:5s} @ ${trade.entry_price:.4f} → ${trade.exit_price:.4f} = ${trade.pnl:+.2f} ({trade.grade})")

    print()
    print("[OK] Test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ✓ test_riverusdt.py COMPLETE
```

---

## File 5: vince/__init__.py (~10 lines)

```python
"""
Vince ML Trading Platform — Core Package.

Subpackages:
- strategies: Four Pillars indicators and signals
- engine: Backtester and position management
"""

__version__ = "1.0.0-alpha"


# ✓ __init__.py COMPLETE
```

---

## COMPLETION

After generating all 5 files, output:

```
="*60
[OK] GENERATION COMPLETE
="*60

Files created:
1. vince/strategies/indicators.py (stochastics, EMAs, clouds, ATR)
2. vince/strategies/signals.py (A/B/C state machine)
3. vince/engine/backtester.py (simple event-driven backtester)
4. test_riverusdt.py (standalone test script)
5. vince/__init__.py (package init)

Next steps:
  cd trading-tools
  python test_riverusdt.py

Expected runtime: <10 seconds
Expected output: ~100-300 trades, $XXX profit, X% win rate
```

**START GENERATING NOW.**
