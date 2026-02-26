"""
Position tracking with MFE/MAE, breakeven raise, and AVWAP trailing stop.
"""

from dataclasses import dataclass
from typing import Optional
import math


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
    Manages an open position with SL/TP tracking, MFE/MAE, breakeven raise,
    and optional AVWAP trailing stop with selectable stdev bands.
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
        be_raise_amount: float = 0.0,
        be_trigger_atr: float = 0.0,
        be_lock_atr: float = 0.0,
        avwap_enabled: bool = False,
        avwap_band: int = 1,            # 1, 2, or 3 stdev
        avwap_floor_atr: float = 1.0,   # floor = N * ATR when stdev is tiny
    ):
        self.direction = direction
        self.grade = grade
        self.entry_bar = entry_bar
        self.entry_price = entry_price
        self.notional = notional
        self.atr = atr
        self.be_raised = False

        # BE mode
        self.be_trigger_atr = be_trigger_atr
        self.be_lock_atr = be_lock_atr
        self.be_raise_amount = be_raise_amount

        # AVWAP trailing stop
        self.avwap_enabled = avwap_enabled
        self.avwap_band = avwap_band
        self.avwap_floor_atr = avwap_floor_atr
        self._cum_pv = 0.0
        self._cum_v = 0.0
        self._cum_pv2 = 0.0   # for stdev: sum(price^2 * volume)
        self._bar_count = 0
        self.avwap_value = entry_price  # current AVWAP level
        self.avwap_stdev = 0.0

        # Set initial SL/TP (static ATR-based)
        if direction == "LONG":
            self.sl = entry_price - (sl_mult * atr)
            self.tp = (entry_price + (tp_mult * atr)) if use_tp else None
        else:
            self.sl = entry_price + (sl_mult * atr)
            self.tp = (entry_price - (tp_mult * atr)) if use_tp else None

        # MFE/MAE tracking
        self.mfe = 0.0
        self.mae = 0.0
        self.saw_green = False

    def _update_avwap(self, hlc3: float, volume: float):
        """Accumulate AVWAP and stdev from entry anchor."""
        if volume <= 0:
            volume = 1e-10  # avoid division by zero
        self._cum_pv += hlc3 * volume
        self._cum_v += volume
        self._cum_pv2 += (hlc3 ** 2) * volume
        self._bar_count += 1

        self.avwap_value = self._cum_pv / self._cum_v

        # Volume-weighted stdev: sqrt(sum(p^2*v)/sum(v) - avwap^2)
        variance = (self._cum_pv2 / self._cum_v) - (self.avwap_value ** 2)
        self.avwap_stdev = math.sqrt(max(variance, 0.0))

    def _avwap_sl(self) -> float:
        """Compute AVWAP-based SL at selected band. Ratchets favorable only."""
        band_dist = self.avwap_stdev * self.avwap_band
        floor_dist = self.avwap_floor_atr * self.atr
        sl_dist = max(band_dist, floor_dist)

        if self.direction == "LONG":
            return self.avwap_value - sl_dist
        else:
            return self.avwap_value + sl_dist

    def update(self, high: float, low: float, close: float,
               hlc3: float = 0.0, volume: float = 0.0) -> Optional[str]:
        """
        Update position with new bar data.
        Returns exit reason ("SL" or "TP") or None if still open.
        hlc3 and volume only needed when avwap_enabled=True.
        """
        # Update AVWAP if enabled
        if self.avwap_enabled and volume > 0:
            self._update_avwap(hlc3, volume)
            new_avwap_sl = self._avwap_sl()
            # Ratchet favorable only
            if self.direction == "LONG":
                if new_avwap_sl > self.sl:
                    self.sl = new_avwap_sl
            else:
                if new_avwap_sl < self.sl:
                    self.sl = new_avwap_sl

        if self.direction == "LONG":
            if low <= self.sl:
                return "SL"
            if self.tp is not None and high >= self.tp:
                return "TP"

            unrealized_best = (high - self.entry_price) / self.entry_price * self.notional
            unrealized_worst = (low - self.entry_price) / self.entry_price * self.notional
            self.mfe = max(self.mfe, unrealized_best)
            self.mae = min(self.mae, unrealized_worst)

            if unrealized_best > 0:
                self.saw_green = True

            # Breakeven raise (works with or without AVWAP)
            if not self.be_raised:
                if self.be_trigger_atr > 0:
                    trigger_dist = self.be_trigger_atr * self.atr
                    if high >= self.entry_price + trigger_dist:
                        lock_dist = self.be_lock_atr * self.atr
                        new_sl = self.entry_price + lock_dist
                        if new_sl > self.sl:
                            self.sl = new_sl
                            self.be_raised = True
                elif self.be_raise_amount > 0:
                    if unrealized_best >= self.be_raise_amount:
                        new_sl = self.entry_price + (self.be_raise_amount / self.notional * self.entry_price)
                        if new_sl > self.sl:
                            self.sl = new_sl
                            self.be_raised = True

        else:  # SHORT
            if high >= self.sl:
                return "SL"
            if self.tp is not None and low <= self.tp:
                return "TP"

            unrealized_best = (self.entry_price - low) / self.entry_price * self.notional
            unrealized_worst = (self.entry_price - high) / self.entry_price * self.notional
            self.mfe = max(self.mfe, unrealized_best)
            self.mae = min(self.mae, unrealized_worst)

            if unrealized_best > 0:
                self.saw_green = True

            if not self.be_raised:
                if self.be_trigger_atr > 0:
                    trigger_dist = self.be_trigger_atr * self.atr
                    if low <= self.entry_price - trigger_dist:
                        lock_dist = self.be_lock_atr * self.atr
                        new_sl = self.entry_price - lock_dist
                        if new_sl < self.sl:
                            self.sl = new_sl
                            self.be_raised = True
                elif self.be_raise_amount > 0:
                    if unrealized_best >= self.be_raise_amount:
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
