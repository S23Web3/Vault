"""
Position tracking with MFE/MAE and breakeven raise.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Trade:
    """Completed trade record."""
    direction: str          # "LONG" or "SHORT"
    grade: str              # "A", "B", "C", "R"
    entry_bar: int
    exit_bar: int
    entry_price: float
    exit_price: float
    sl_price: float
    tp_price: Optional[float]
    pnl: float              # Gross P&L (before commission)
    commission: float        # Total commission (entry + exit)
    mfe: float              # Max favorable excursion ($ on notional)
    mae: float              # Max adverse excursion ($ on notional)
    exit_reason: str         # "SL", "TP", "FLIP", "SIGNAL"
    saw_green: bool          # Did unrealized PnL ever go positive?
    be_raised: bool          # Was breakeven raise triggered?


class Position:
    """
    Manages an open position with SL/TP tracking, MFE/MAE, and breakeven raise.
    """

    def __init__(
        self,
        direction: str,
        grade: str,
        entry_bar: int,
        entry_price: float,
        atr: float,
        sl_mult: float = 1.0,
        tp_mult: float = 1.5,
        use_tp: bool = True,
        notional: float = 10000.0,
        be_raise_amount: float = 0.0,  # $0 = disabled
    ):
        self.direction = direction
        self.grade = grade
        self.entry_bar = entry_bar
        self.entry_price = entry_price
        self.notional = notional
        self.be_raise_amount = be_raise_amount
        self.be_raised = False

        # Set SL/TP
        if direction == "LONG":
            self.sl = entry_price - (sl_mult * atr)
            self.tp = (entry_price + (tp_mult * atr)) if use_tp else None
        else:
            self.sl = entry_price + (sl_mult * atr)
            self.tp = (entry_price - (tp_mult * atr)) if use_tp else None

        # MFE/MAE tracking
        self.mfe = 0.0  # Best unrealized $ profit
        self.mae = 0.0  # Worst unrealized $ loss
        self.saw_green = False

    def update(self, high: float, low: float, close: float) -> Optional[str]:
        """
        Update position with new bar data.
        Returns exit reason ("SL" or "TP") or None if still open.
        Checks SL/TP against high/low (intrabar), not just close.
        """
        if self.direction == "LONG":
            # Check SL hit (low touches SL)
            if low <= self.sl:
                return "SL"
            # Check TP hit (high touches TP)
            if self.tp is not None and high >= self.tp:
                return "TP"

            # Update MFE/MAE
            unrealized_best = (high - self.entry_price) / self.entry_price * self.notional
            unrealized_worst = (low - self.entry_price) / self.entry_price * self.notional
            self.mfe = max(self.mfe, unrealized_best)
            self.mae = min(self.mae, unrealized_worst)

            if unrealized_best > 0:
                self.saw_green = True

            # Breakeven raise
            if (self.be_raise_amount > 0 and not self.be_raised and
                    unrealized_best >= self.be_raise_amount):
                new_sl = self.entry_price + (self.be_raise_amount / self.notional * self.entry_price)
                if new_sl > self.sl:
                    self.sl = new_sl
                    self.be_raised = True

        else:  # SHORT
            # Check SL hit (high touches SL)
            if high >= self.sl:
                return "SL"
            # Check TP hit (low touches TP)
            if self.tp is not None and low <= self.tp:
                return "TP"

            # Update MFE/MAE
            unrealized_best = (self.entry_price - low) / self.entry_price * self.notional
            unrealized_worst = (self.entry_price - high) / self.entry_price * self.notional
            self.mfe = max(self.mfe, unrealized_best)
            self.mae = min(self.mae, unrealized_worst)

            if unrealized_best > 0:
                self.saw_green = True

            # Breakeven raise
            if (self.be_raise_amount > 0 and not self.be_raised and
                    unrealized_best >= self.be_raise_amount):
                new_sl = self.entry_price - (self.be_raise_amount / self.notional * self.entry_price)
                if new_sl < self.sl:
                    self.sl = new_sl
                    self.be_raised = True

        return None

    def close_at(self, price: float, bar_index: int, reason: str, commission: float) -> Trade:
        """Close position and return Trade record."""
        if self.direction == "LONG":
            pnl = (price - self.entry_price) / self.entry_price * self.notional
        else:
            pnl = (self.entry_price - price) / self.entry_price * self.notional

        return Trade(
            direction=self.direction,
            grade=self.grade,
            entry_bar=self.entry_bar,
            exit_bar=bar_index,
            entry_price=self.entry_price,
            exit_price=price,
            sl_price=self.sl,
            tp_price=self.tp,
            pnl=pnl,
            commission=commission,
            mfe=self.mfe,
            mae=self.mae,
            exit_reason=reason,
            saw_green=self.saw_green,
            be_raised=self.be_raised,
        )
