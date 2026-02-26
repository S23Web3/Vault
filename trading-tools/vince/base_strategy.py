from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    
    This class defines the interface that all trading strategies must implement.
    It provides a standardized way to calculate indicators, generate signals,
    and determine stop-loss and take-profit levels.
    
    Attributes:
        None
        
    Methods:
        calculate_indicators(df): Calculate technical indicators for the strategy
        generate_signals(df): Generate trading signals based on indicators
        get_sl_tp(entry_price, direction, atr): Calculate stop-loss and take-profit levels
    """
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with additional indicator columns
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on indicators.
        
        Args:
            df: DataFrame with OHLCV and indicator data
            
        Returns:
            DataFrame with signal columns
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass
    
    @abstractmethod
    def get_sl_tp(self, entry_price: float, direction: str, atr: float) -> Tuple[float, float]:
        """
        Calculate stop-loss and take-profit levels.
        
        Args:
            entry_price: Price at which position was entered
            direction: Trading direction ('LONG' or 'SHORT')
            atr: Average True Range value
            
        Returns:
            Tuple of (stop_loss, take_profit) prices
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        pass

class ExampleStrategy(BaseStrategy):
    """
    Example concrete implementation of BaseStrategy.
    
    This demonstrates how to implement the abstract methods.
    """
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Example implementation of indicator calculation.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        # Simple example: add 20-period SMA
        df['sma20'] = df['close'].rolling(window=20).mean()
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Example implementation of signal generation.
        
        Args:
            df: DataFrame with OHLCV and indicator data
            
        Returns:
            DataFrame with signal columns
        """
        # Simple example: buy when price crosses above SMA
        df['signal'] = 0
        df.loc[df['close'] > df['sma20'], 'signal'] = 1
        df.loc[df['close'] < df['sma20'], 'signal'] = -1
        return df
    
    def get_sl_tp(self, entry_price: float, direction: str, atr: float) -> Tuple[float, float]:
        """
        Example implementation of SL/TP calculation.
        
        Args:
            entry_price: Price at which position was entered
            direction: Trading direction ('LONG' or 'SHORT')
            atr: Average True Range value
            
        Returns:
            Tuple of (stop_loss, take_profit) prices
        """
        sl_distance = atr * 1.5
        tp_distance = atr * 2.0
        
        if direction == 'LONG':
            sl = entry_price - sl_distance
            tp = entry_price + tp_distance
        else:  # SHORT
            sl = entry_price + sl_distance
            tp = entry_price - tp_distance
            
        return sl, tp

if __name__ == "__main__":
    # Example usage
    print("BaseStrategy example implementation:")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'open': np.random.uniform(100, 200, 100),
        'high': np.random.uniform(100, 200, 100),
        'low': np.random.uniform(100, 200, 100),
        'close': np.random.uniform(100, 200, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    }, index=dates)
    
    # Test the example strategy
    strategy = ExampleStrategy()
    df_with_indicators = strategy.calculate_indicators(df)
    df_with_signals = strategy.generate_signals(df_with_indicators)
    
    print("Sample data with indicators and signals:")
    print(df_with_signals.tail())
    
    # Test SL/TP calculation
    sl, tp = strategy.get_sl_tp(150.0, 'LONG', 2.0)
    print(f"SL/TP for LONG at 150.0 with ATR=2.0: SL={sl:.2f}, TP={tp:.2f}")