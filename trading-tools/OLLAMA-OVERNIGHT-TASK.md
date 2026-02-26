# Ollama Overnight Task — Vince Backtester Core Components

**Date**: 2026-02-09
**Model**: DeepSeek Coder (recommended) or Qwen 2.5 Coder
**Estimated Time**: 4-6 hours (overnight)
**Deliverable**: 5 Python files ready for integration

---

## Task Overview

Generate the core backtesting engine components for the Vince ML platform. These are self-contained Python classes that don't require external context — just clean, production-ready code.

---

## Component 1: Base Strategy Interface

**File**: `strategies/base_strategy.py`

**Objective**: Create an abstract base class that all trading strategies must inherit from.

**Requirements**:
1. Use Python `abc` module for abstract methods
2. Type hints for all parameters and returns
3. Comprehensive docstrings (Google style)
4. Must be strategy-agnostic (works for any trading strategy)

**Methods to implement**:
```python
class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators needed for this strategy.

        Args:
            df: OHLCV dataframe with columns [timestamp, open, high, low, close, volume]

        Returns:
            df with additional indicator columns
        """
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate entry/exit signals based on indicators.

        Args:
            df: Dataframe with OHLCV + indicators

        Returns:
            df with additional signal columns:
                - enter_long: bool
                - enter_short: bool
                - exit_long: bool
                - exit_short: bool
        """
        pass

    @abstractmethod
    def get_sl_tp(self, entry_price: float, direction: str, atr: float) -> tuple[float, float]:
        """
        Calculate initial stop loss and take profit.

        Args:
            entry_price: Entry price
            direction: 'LONG' or 'SHORT'
            atr: Current ATR value

        Returns:
            (stop_loss_price, take_profit_price)
        """
        pass

    def get_name(self) -> str:
        """Return strategy name"""
        return self.__class__.__name__

    def get_config(self) -> dict:
        """Return strategy configuration"""
        return {}
```

**Additional requirements**:
- Add class-level docstring explaining how to subclass
- Add example usage in docstring
- Include all necessary imports at top

---

## Component 2: Position Manager

**File**: `engine/position_manager.py`

**Objective**: Track open positions with MFE/MAE (Max Favorable/Adverse Excursion).

**Requirements**:
1. Track entry price, size, direction
2. Calculate MFE/MAE in both $ and ATR terms
3. Track bars in trade
4. Calculate unrealized P&L
5. Handle both long and short positions

**Class structure**:
```python
class Position:
    """Represents an open trading position with MFE/MAE tracking"""

    def __init__(self,
                 entry_price: float,
                 size: float,
                 direction: str,  # 'LONG' or 'SHORT'
                 entry_atr: float,
                 stop_loss: float,
                 take_profit: float,
                 entry_time: pd.Timestamp):
        """Initialize position"""
        self.entry_price = entry_price
        self.size = size
        self.direction = direction
        self.entry_atr = entry_atr
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_time = entry_time

        # MFE/MAE tracking
        self.max_price = entry_price
        self.min_price = entry_price
        self.bars_in_trade = 0

    def update(self, bar: dict):
        """
        Update position with new bar data.

        Args:
            bar: Dict with keys [high, low, close, timestamp]
        """
        # Update max/min prices
        self.max_price = max(self.max_price, bar['high'])
        self.min_price = min(self.min_price, bar['low'])
        self.bars_in_trade += 1

    def get_mfe_atr(self) -> float:
        """Calculate Max Favorable Excursion in ATR terms"""
        if self.direction == 'LONG':
            return (self.max_price - self.entry_price) / self.entry_atr
        else:
            return (self.entry_price - self.min_price) / self.entry_atr

    def get_mae_atr(self) -> float:
        """Calculate Max Adverse Excursion in ATR terms"""
        if self.direction == 'LONG':
            return (self.entry_price - self.min_price) / self.entry_atr
        else:
            return (self.max_price - self.entry_price) / self.entry_atr

    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L"""
        if self.direction == 'LONG':
            return (current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - current_price) * self.size

    def check_exit(self, bar: dict) -> tuple[bool, str, float]:
        """
        Check if position should exit (SL/TP hit).

        Args:
            bar: Dict with keys [high, low, close]

        Returns:
            (should_exit, exit_reason, exit_price)
            exit_reason: 'SL', 'TP', or None
        """
        # Check stop loss
        if self.direction == 'LONG':
            if bar['low'] <= self.stop_loss:
                return (True, 'SL', self.stop_loss)
            if bar['high'] >= self.take_profit:
                return (True, 'TP', self.take_profit)
        else:
            if bar['high'] >= self.stop_loss:
                return (True, 'SL', self.stop_loss)
            if bar['low'] <= self.take_profit:
                return (True, 'TP', self.take_profit)

        return (False, None, None)

    def close(self, exit_price: float, exit_reason: str, exit_time: pd.Timestamp) -> dict:
        """
        Close position and return trade summary.

        Returns:
            dict with trade details
        """
        pnl = self.get_unrealized_pnl(exit_price)

        return {
            'entry_time': self.entry_time,
            'exit_time': exit_time,
            'entry_price': self.entry_price,
            'exit_price': exit_price,
            'direction': self.direction,
            'size': self.size,
            'pnl': pnl,
            'mfe_atr': self.get_mfe_atr(),
            'mae_atr': self.get_mae_atr(),
            'bars_in_trade': self.bars_in_trade,
            'exit_reason': exit_reason,
        }
```

**Additional requirements**:
- Add validation (e.g., size > 0, direction in ['LONG', 'SHORT'])
- Add `__repr__` method for debugging
- Handle edge cases (e.g., slippage on SL/TP)

---

## Component 3: Exit Manager (4 Risk Methods)

**File**: `engine/exit_manager.py`

**Objective**: Implement 4 risk management methods with dynamic SL adjustment based on MFE.

**Requirements**:
1. Support 4 risk methods:
   - `be_only`: Move SL to breakeven (0 ATR)
   - `be_plus_fees`: Move SL to entry + X ATR (cover fees)
   - `be_plus_fees_trail_tp`: SL to entry + fees, TP trails from max_price
   - `be_trail_tp`: SL to BE, TP trails
2. Dynamic SL movement based on MFE thresholds
3. Configurable parameters (mfe_trigger, sl_lock, tp_trail_distance)

**Class structure**:
```python
class ExitManager:
    """Manages dynamic stop loss and take profit adjustments"""

    def __init__(self,
                 risk_method: str,
                 mfe_trigger: float = 1.0,      # MFE threshold in ATR
                 sl_lock: float = 0.3,          # SL lock position in ATR from entry
                 tp_trail_distance: float = 0.5): # TP distance from max_price in ATR
        """
        Initialize exit manager.

        Args:
            risk_method: One of ['be_only', 'be_plus_fees', 'be_plus_fees_trail_tp', 'be_trail_tp']
            mfe_trigger: MFE threshold to activate SL movement (in ATR)
            sl_lock: Where to lock SL (in ATR from entry)
            tp_trail_distance: Trailing TP distance from max_price (in ATR)
        """
        self.risk_method = risk_method
        self.mfe_trigger = mfe_trigger
        self.sl_lock = sl_lock
        self.tp_trail_distance = tp_trail_distance

        # Validation
        valid_methods = ['be_only', 'be_plus_fees', 'be_plus_fees_trail_tp', 'be_trail_tp']
        if risk_method not in valid_methods:
            raise ValueError(f"risk_method must be one of {valid_methods}")

    def update_stops(self, position: Position, current_atr: float) -> tuple[float, float]:
        """
        Update stop loss and take profit based on risk method.

        Args:
            position: Current position object
            current_atr: Current ATR value

        Returns:
            (new_stop_loss, new_take_profit)
        """
        # Check if MFE exceeds trigger threshold
        mfe_atr = position.get_mfe_atr()

        if mfe_atr < self.mfe_trigger:
            # Not enough profit yet, keep original stops
            return (position.stop_loss, position.take_profit)

        # Calculate new stops based on risk method
        if self.risk_method == 'be_only':
            new_sl = self._be_only(position)
            new_tp = position.take_profit  # TP unchanged

        elif self.risk_method == 'be_plus_fees':
            new_sl = self._be_plus_fees(position, current_atr)
            new_tp = position.take_profit  # TP unchanged

        elif self.risk_method == 'be_plus_fees_trail_tp':
            new_sl = self._be_plus_fees(position, current_atr)
            new_tp = self._trailing_tp(position, current_atr)

        elif self.risk_method == 'be_trail_tp':
            new_sl = self._be_only(position)
            new_tp = self._trailing_tp(position, current_atr)

        # Ensure new SL is better than old SL (never move backwards)
        if position.direction == 'LONG':
            new_sl = max(new_sl, position.stop_loss)
        else:
            new_sl = min(new_sl, position.stop_loss)

        return (new_sl, new_tp)

    def _be_only(self, position: Position) -> float:
        """Move SL to breakeven (entry price)"""
        return position.entry_price

    def _be_plus_fees(self, position: Position, atr: float) -> float:
        """Move SL to entry + X ATR (to cover fees)"""
        if position.direction == 'LONG':
            return position.entry_price + (self.sl_lock * atr)
        else:
            return position.entry_price - (self.sl_lock * atr)

    def _trailing_tp(self, position: Position, atr: float) -> float:
        """Trail TP from max_price"""
        if position.direction == 'LONG':
            return position.max_price - (self.tp_trail_distance * atr)
        else:
            return position.min_price + (self.tp_trail_distance * atr)
```

**Additional requirements**:
- Add comprehensive docstrings for each method
- Add validation for parameters (e.g., mfe_trigger > 0)
- Add logging for SL/TP updates
- Handle edge cases (e.g., TP trailing below entry)

---

## Component 4: Metrics Calculator

**File**: `engine/metrics.py`

**Objective**: Calculate trading performance metrics (SQN, Sharpe, LSG%, R-multiples).

**Requirements**:
1. All metrics must use vectorized operations (pandas/numpy)
2. Handle edge cases (e.g., zero trades, zero variance)
3. Return NaN for invalid metrics (not 0)

**Functions to implement**:
```python
def calculate_sqn(returns: pd.Series) -> float:
    """
    Calculate System Quality Number (Van Tharp).

    SQN = (mean(R) * sqrt(n)) / std(R)

    Where R = return in R-multiples (return / initial_risk)

    Args:
        returns: Series of trade returns (in $)

    Returns:
        SQN score

    Interpretation:
        < 1.6: Poor
        1.6-1.9: Below average
        2.0-2.4: Average
        2.5-2.9: Good
        3.0-5.0: Excellent
        > 5.0: Superstar
    """
    pass

def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe Ratio.

    Sharpe = (mean(returns) - rf) / std(returns)

    Args:
        returns: Series of trade returns
        risk_free_rate: Annual risk-free rate (default 0 for crypto)

    Returns:
        Sharpe ratio (annualized if returns are daily)
    """
    pass

def calculate_sortino(returns: pd.Series, target_return: float = 0.0) -> float:
    """
    Calculate Sortino Ratio (downside deviation only).

    Sortino = (mean(returns) - target) / downside_std(returns)

    Args:
        returns: Series of trade returns
        target_return: Target return (default 0)

    Returns:
        Sortino ratio
    """
    pass

def calculate_lsg_percent(trades_df: pd.DataFrame) -> float:
    """
    Calculate LSG% (Loser Saw Green).

    LSG% = % of losing trades that had MFE > 0 at some point

    This metric shows how many losers were profitable before reversing.
    High LSG% suggests exits are the problem, not entries.

    Args:
        trades_df: Dataframe with columns [pnl, mfe_atr]

    Returns:
        LSG percentage (0-100)
    """
    pass

def calculate_max_drawdown(equity_curve: pd.Series) -> tuple[float, int]:
    """
    Calculate maximum drawdown and duration.

    Args:
        equity_curve: Series of cumulative equity

    Returns:
        (max_drawdown_pct, max_drawdown_duration_bars)
    """
    pass

def calculate_win_rate(trades_df: pd.DataFrame) -> float:
    """
    Calculate win rate (% of profitable trades).

    Args:
        trades_df: Dataframe with column [pnl]

    Returns:
        Win rate percentage (0-100)
    """
    pass

def calculate_profit_factor(trades_df: pd.DataFrame) -> float:
    """
    Calculate profit factor (gross profit / gross loss).

    Args:
        trades_df: Dataframe with column [pnl]

    Returns:
        Profit factor (>1 = profitable)
    """
    pass

def calculate_r_multiples(trades_df: pd.DataFrame, initial_risk_col: str = 'initial_risk') -> pd.Series:
    """
    Calculate R-multiples for each trade.

    R = actual_pnl / initial_risk

    Args:
        trades_df: Dataframe with columns [pnl, initial_risk]
        initial_risk_col: Column name for initial risk

    Returns:
        Series of R-multiples
    """
    pass

def generate_metrics_report(trades_df: pd.DataFrame) -> dict:
    """
    Generate comprehensive metrics report.

    Args:
        trades_df: Dataframe with columns [pnl, mfe_atr, mae_atr, entry_price, exit_price]

    Returns:
        dict with all metrics
    """
    return {
        'total_trades': len(trades_df),
        'win_rate': calculate_win_rate(trades_df),
        'profit_factor': calculate_profit_factor(trades_df),
        'total_pnl': trades_df['pnl'].sum(),
        'avg_pnl': trades_df['pnl'].mean(),
        'max_drawdown': calculate_max_drawdown(trades_df['pnl'].cumsum()),
        'sharpe': calculate_sharpe(trades_df['pnl']),
        'sortino': calculate_sortino(trades_df['pnl']),
        'sqn': calculate_sqn(trades_df['pnl']),
        'lsg_percent': calculate_lsg_percent(trades_df),
        'avg_mfe_atr': trades_df['mfe_atr'].mean(),
        'avg_mae_atr': trades_df['mae_atr'].mean(),
    }
```

**Additional requirements**:
- Handle empty dataframes gracefully
- Return NaN for invalid metrics (e.g., SQN with 0 trades)
- Add type hints for all parameters
- Comprehensive docstrings with formulas

---

## Component 5: Simple Backtester

**File**: `engine/backtester.py`

**Objective**: Event-based backtesting engine that uses Position, ExitManager, and Metrics.

**Requirements**:
1. Bar-by-bar iteration (not vectorized)
2. Use Position and ExitManager classes
3. Track commission ($8/side)
4. Output trade list + metrics

**Class structure**:
```python
class Backtester:
    """Event-based backtesting engine"""

    def __init__(self,
                 strategy: BaseStrategy,
                 exit_manager: ExitManager,
                 commission_per_side: float = 8.0):
        """
        Initialize backtester.

        Args:
            strategy: Strategy instance (subclass of BaseStrategy)
            exit_manager: ExitManager instance
            commission_per_side: Commission in $ per side (default $8)
        """
        self.strategy = strategy
        self.exit_manager = exit_manager
        self.commission_per_side = commission_per_side

        self.position = None
        self.trades = []

    def run(self, df: pd.DataFrame) -> dict:
        """
        Run backtest on OHLCV data.

        Args:
            df: Dataframe with columns [timestamp, open, high, low, close, volume]

        Returns:
            dict with keys:
                - trades: list of trade dicts
                - metrics: dict of performance metrics
                - equity_curve: pd.Series of cumulative P&L
        """
        # Calculate indicators
        df = self.strategy.calculate_indicators(df)

        # Generate signals
        df = self.strategy.generate_signals(df)

        # Event loop
        for i in range(len(df)):
            bar = df.iloc[i].to_dict()

            # If in position, check for exit
            if self.position is not None:
                self._update_position(bar)
                should_exit, exit_reason, exit_price = self.position.check_exit(bar)

                if should_exit:
                    self._close_position(bar, exit_price, exit_reason)

            # If flat, check for entry
            else:
                if bar['enter_long']:
                    self._open_position(bar, 'LONG')
                elif bar['enter_short']:
                    self._open_position(bar, 'SHORT')

        # Close any open position at end
        if self.position is not None:
            self._close_position(df.iloc[-1].to_dict(), df.iloc[-1]['close'], 'END')

        # Calculate metrics
        trades_df = pd.DataFrame(self.trades)
        metrics = generate_metrics_report(trades_df)
        equity_curve = trades_df['pnl'].cumsum()

        return {
            'trades': self.trades,
            'metrics': metrics,
            'equity_curve': equity_curve,
        }

    def _open_position(self, bar: dict, direction: str):
        """Open new position"""
        entry_price = bar['close']
        atr = bar['atr']
        sl, tp = self.strategy.get_sl_tp(entry_price, direction, atr)

        self.position = Position(
            entry_price=entry_price,
            size=1.0,  # Fixed size for now
            direction=direction,
            entry_atr=atr,
            stop_loss=sl,
            take_profit=tp,
            entry_time=bar['timestamp']
        )

    def _update_position(self, bar: dict):
        """Update position with new bar"""
        self.position.update(bar)

        # Update stops via ExitManager
        new_sl, new_tp = self.exit_manager.update_stops(self.position, bar['atr'])
        self.position.stop_loss = new_sl
        self.position.take_profit = new_tp

    def _close_position(self, bar: dict, exit_price: float, exit_reason: str):
        """Close position and record trade"""
        trade = self.position.close(exit_price, exit_reason, bar['timestamp'])

        # Subtract commission (2 sides)
        trade['commission'] = 2 * self.commission_per_side
        trade['net_pnl'] = trade['pnl'] - trade['commission']

        self.trades.append(trade)
        self.position = None
```

**Additional requirements**:
- Add position sizing logic (not just fixed size)
- Add slippage simulation
- Handle bars with no trades gracefully
- Add progress bar for long backtests (optional)

---

## Output Format

For each component, generate:

1. **Full Python file** with:
   - All imports at top
   - Comprehensive docstrings (Google style)
   - Type hints for all functions/methods
   - Input validation where appropriate
   - **Try/except blocks** for all operations that could fail
   - Example usage in docstring

2. **Simple test case** at bottom with error handling:
```python
if __name__ == "__main__":
    # Simple test with error handling
    try:
        print("Testing [ComponentName]...")
        # ... basic functionality test
        print("✓ All tests passed!")
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
```

## CRITICAL: Error Handling Requirements

**Every function must handle errors gracefully**:

```python
def method_name(self, param: type) -> return_type:
    """Docstring"""
    try:
        # Validate inputs
        if param is None:
            raise ValueError("param cannot be None")

        # Main logic
        result = do_something(param)

        # Validate output
        if result is None:
            raise RuntimeError("Operation returned None")

        return result

    except ValueError as e:
        # Input validation errors
        raise ValueError(f"Invalid input: {e}")
    except KeyError as e:
        # Missing dict keys
        raise KeyError(f"Missing required key: {e}")
    except ZeroDivisionError:
        # Math errors
        return float('nan')
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"Error in method_name: {e}")
        raise
```

**Why this matters**: The user won't be at their PC tonight. Code must not crash halfway through.

---

## Coding Standards

1. **PEP 8 compliant** (black formatter style)
2. **Type hints** everywhere
3. **Docstrings** for all classes/methods (Google style)
4. **No external dependencies** beyond:
   - pandas
   - numpy
   - typing
   - abc
5. **Error handling**: Raise descriptive exceptions
6. **Edge cases**: Handle empty inputs, zero values, NaN

---

## Example Output Structure

```python
#!/usr/bin/env python3
"""
Component Name - Brief description

This module implements [component description].

Example:
    >>> from engine.position_manager import Position
    >>> pos = Position(entry_price=100, size=1.0, direction='LONG', ...)
    >>> pos.update({'high': 105, 'low': 98, 'close': 102})
    >>> print(pos.get_mfe_atr())
    0.5
"""

from typing import Optional, Tuple, Dict
import pandas as pd
import numpy as np

class ComponentName:
    """Brief description"""

    def __init__(self, param1: int, param2: float):
        """
        Initialize component.

        Args:
            param1: Description
            param2: Description

        Raises:
            ValueError: If param1 < 0
        """
        if param1 < 0:
            raise ValueError("param1 must be >= 0")

        self.param1 = param1
        self.param2 = param2

    def method_name(self, arg: str) -> bool:
        """
        Brief description of what this method does.

        Args:
            arg: Description

        Returns:
            Description of return value

        Example:
            >>> obj = ComponentName(1, 2.0)
            >>> obj.method_name("test")
            True
        """
        # Implementation
        pass

if __name__ == "__main__":
    # Simple test
    print("Testing ComponentName...")
    obj = ComponentName(10, 5.0)
    result = obj.method_name("test")
    assert result == True, "Test failed!"
    print("✓ All tests passed!")
```

---

## Deliverables (5 Files)

1. `strategies/base_strategy.py` (~100 lines)
2. `engine/position_manager.py` (~150 lines)
3. `engine/exit_manager.py` (~120 lines)
4. `engine/metrics.py` (~200 lines)
5. `engine/backtester.py` (~150 lines)

**Total**: ~720 lines of production-ready Python code

---

## Instructions for User

1. **Choose model**: `ollama run deepseek-coder:33b`
2. **Paste this entire file** as the prompt
3. **Copy each output** to separate files
4. **Tomorrow morning**: Paste outputs to Claude for integration + testing

---

## Success Criteria

- [ ] All 5 files generated
- [ ] No syntax errors
- [ ] Type hints present
- [ ] Docstrings comprehensive
- [ ] Test cases included
- [ ] PEP 8 compliant
