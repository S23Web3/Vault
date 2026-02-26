"""
Simple event-driven backtester for Four Pillars v3.8.

Features:
- Bar-by-bar execution
- Entry on A/B/C signals
- Static SL/TP (1.0 ATR SL, 1.5 ATR TP)
- Commission: $8/side ($16 round trip)
- MFE/MAE tracking
- Trade-by-trade results
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Trade:
    """Single trade record."""
    entry_time: pd.Timestamp
    exit_time: Optional[pd.Timestamp] = None
    direction: str = 'FLAT'
    entry_price: float = 0.0
    exit_price: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0
    max_price: float = 0.0
    min_price: float = 0.0
    grade: str = ''
    pnl: float = 0.0
    commission: float = 16.0


class SimpleFourPillarsBacktester:
    """Event-driven backtester for Four Pillars strategy."""

    def __init__(self, initial_capital: float = 10000,
                 position_size: float = 10000,
                 sl_atr_mult: float = 1.0,
                 tp_atr_mult: float = 1.5,
                 commission_per_side: float = 8.0):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting capital ($10,000)
            position_size: Notional size per trade ($10,000)
            sl_atr_mult: SL distance in ATR (default 1.0)
            tp_atr_mult: TP distance in ATR (default 1.5)
            commission_per_side: Commission per side (default $8)
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.sl_atr_mult = sl_atr_mult
        self.tp_atr_mult = tp_atr_mult
        self.commission_per_side = commission_per_side

    def run(self, df: pd.DataFrame) -> Dict:
        """
        Run backtest on DataFrame with signals.

        Args:
            df: DataFrame with signals and indicators

        Returns:
            Dictionary with trades, metrics, and equity curve
        """
        trades: List[Trade] = []
        current_trade: Optional[Trade] = None
        equity = self.initial_capital

        for idx, row in df.iterrows():
            # Update MFE/MAE for open position
            if current_trade:
                current_trade.max_price = max(current_trade.max_price, row['high'])
                current_trade.min_price = min(current_trade.min_price, row['low'])

                # Check for SL/TP exit
                if current_trade.direction == 'LONG':
                    if row['low'] <= current_trade.sl_price:
                        # Stop loss hit
                        current_trade.exit_price = current_trade.sl_price
                        current_trade.exit_time = idx
                        current_trade.pnl = ((current_trade.exit_price - current_trade.entry_price) /
                                              current_trade.entry_price * self.position_size -
                                              current_trade.commission)
                        equity += current_trade.pnl
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif row['high'] >= current_trade.tp_price:
                        # Take profit hit
                        current_trade.exit_price = current_trade.tp_price
                        current_trade.exit_time = idx
                        current_trade.pnl = ((current_trade.exit_price - current_trade.entry_price) /
                                              current_trade.entry_price * self.position_size -
                                              current_trade.commission)
                        equity += current_trade.pnl
                        trades.append(current_trade)
                        current_trade = None
                        continue

                elif current_trade.direction == 'SHORT':
                    if row['high'] >= current_trade.sl_price:
                        current_trade.exit_price = current_trade.sl_price
                        current_trade.exit_time = idx
                        current_trade.pnl = ((current_trade.entry_price - current_trade.exit_price) /
                                              current_trade.entry_price * self.position_size -
                                              current_trade.commission)
                        equity += current_trade.pnl
                        trades.append(current_trade)
                        current_trade = None
                        continue
                    elif row['low'] <= current_trade.tp_price:
                        current_trade.exit_price = current_trade.tp_price
                        current_trade.exit_time = idx
                        current_trade.pnl = ((current_trade.entry_price - current_trade.exit_price) /
                                              current_trade.entry_price * self.position_size -
                                              current_trade.commission)
                        equity += current_trade.pnl
                        trades.append(current_trade)
                        current_trade = None
                        continue

            # Check for new entry signals (only if flat)
            if not current_trade:
                if row['enter_long_a']:
                    current_trade = Trade(
                        entry_time=idx,
                        direction='LONG',
                        entry_price=row['close'],
                        sl_price=row['close'] - (self.sl_atr_mult * row['atr']),
                        tp_price=row['close'] + (self.tp_atr_mult * row['atr']),
                        max_price=row['close'],
                        min_price=row['close'],
                        grade='A',
                        commission=self.commission_per_side * 2
                    )
                elif row['enter_short_a']:
                    current_trade = Trade(
                        entry_time=idx,
                        direction='SHORT',
                        entry_price=row['close'],
                        sl_price=row['close'] + (self.sl_atr_mult * row['atr']),
                        tp_price=row['close'] - (self.tp_atr_mult * row['atr']),
                        max_price=row['close'],
                        min_price=row['close'],
                        grade='A',
                        commission=self.commission_per_side * 2
                    )
                elif row['enter_long_bc']:
                    current_trade = Trade(
                        entry_time=idx,
                        direction='LONG',
                        entry_price=row['close'],
                        sl_price=row['close'] - (self.sl_atr_mult * row['atr']),
                        tp_price=row['close'] + (self.tp_atr_mult * row['atr']),
                        max_price=row['close'],
                        min_price=row['close'],
                        grade='BC',
                        commission=self.commission_per_side * 2
                    )
                elif row['enter_short_bc']:
                    current_trade = Trade(
                        entry_time=idx,
                        direction='SHORT',
                        entry_price=row['close'],
                        sl_price=row['close'] + (self.sl_atr_mult * row['atr']),
                        tp_price=row['close'] - (self.tp_atr_mult * row['atr']),
                        max_price=row['close'],
                        min_price=row['close'],
                        grade='BC',
                        commission=self.commission_per_side * 2
                    )

        metrics = self.calculate_metrics(trades)

        return {
            'trades': trades,
            'metrics': metrics,
            'final_equity': equity
        }

    def calculate_metrics(self, trades: List[Trade]) -> Dict:
        """Calculate performance metrics."""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_commission': 0,
                'net_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'sharpe': 0,
                'sqn': 0,
                'max_drawdown': 0,
                'max_dd_pct': 0
            }

        pnls = [t.pnl for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total_pnl = sum(pnls)
        total_commission = sum(t.commission for t in trades)
        net_pnl = total_pnl

        return {
            'total_trades': len(trades),
            'win_rate': len(wins) / len(trades) if trades else 0,
            'total_pnl': total_pnl,
            'total_commission': total_commission,
            'net_pnl': net_pnl,
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'sharpe': np.mean(pnls) / np.std(pnls) * np.sqrt(252) if np.std(pnls) > 0 else 0,
            'sqn': np.mean(pnls) / np.std(pnls) * np.sqrt(len(pnls)) if np.std(pnls) > 0 else 0,
            'max_drawdown': 0,  # TODO: calculate from equity curve
            'max_dd_pct': 0
        }
