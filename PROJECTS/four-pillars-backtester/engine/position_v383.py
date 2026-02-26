"""
Position slot for v3.8.3: ATR initial SL, AVWAP trailing, scale-out mechanism.

SL logic:
  A/B/C/D entries: ATR-based SL (entry_price +/- ATR * sl_mult). Fixed for first N bars.
  ADD/RE entries: AVWAP 2sigma SL (inherited from parent slot). Fixed for first N bars.
  After checkpoint_interval bars: SL moves to AVWAP center, continuously ratcheted.

Scale-out:
  At each checkpoint (every checkpoint_interval bars), if close hits AVWAP +/- 2sigma
  in the trade's direction, close half (or all if final). SL snaps to AVWAP center.
  Max 2 scale-outs (50% + 50% = fully closed).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .avwap import AVWAPTracker


@dataclass
class Trade383:
    """Completed trade record for v3.8.3."""
    direction: str
    grade: str
    entry_bar: int
    exit_bar: int
    entry_price: float
    exit_price: float
    sl_price: float
    tp_price: Optional[float]
    pnl: float
    commission: float
    mfe: float
    mae: float
    exit_reason: str
    saw_green: bool
    be_raised: bool
    exit_stage: int
    entry_atr: float
    scale_idx: int = 0


class PositionSlot383:
    """One position with ATR/AVWAP SL and scale-out mechanism."""

    def __init__(
        self,
        direction: str,
        grade: str,
        entry_bar: int,
        entry_price: float,
        atr: float,
        hlc3: float,
        volume: float,
        sigma_floor_atr: float = 0.5,
        sl_mult: float = 2.0,
        notional: float = 5000.0,
        checkpoint_interval: int = 5,
        max_scaleouts: int = 2,
        avwap_state: AVWAPTracker = None,
    ):
        self.direction = direction
        self.grade = grade
        self.entry_bar = entry_bar
        self.entry_price = entry_price
        self.notional = notional
        self.original_notional = notional
        self._entry_atr = atr
        self.checkpoint_interval = checkpoint_interval
        self.max_scaleouts = max_scaleouts
        self.scale_count = 0
        self.entry_commission = 0.0

        # AVWAP: inherit from parent (ADD/RE) or start fresh (A/B/C/D)
        if avwap_state is not None:
            self.avwap = avwap_state.clone()
        else:
            self.avwap = AVWAPTracker(sigma_floor_atr)
        self.avwap.update(hlc3, volume, atr)

        # SL initialization
        self.sl_phase = "initial"  # "initial" -> "avwap" after checkpoint_interval bars
        if grade in ("A", "B", "C", "D"):
            # ATR-based SL
            if direction == "LONG":
                self.sl = entry_price - (atr * sl_mult)
            else:
                self.sl = entry_price + (atr * sl_mult)
        else:
            # ADD/RE: AVWAP 2sigma SL
            c, s = self.avwap.center, self.avwap.sigma
            if direction == "LONG":
                self.sl = c - 2 * s
            else:
                self.sl = c + 2 * s

        # MFE/MAE
        self.mfe = 0.0
        self.mae = 0.0
        self.saw_green = False

    def check_exit(self, high: float, low: float) -> Optional[str]:
        """Check if SL hit. Called BEFORE update_bar."""
        if self.direction == "LONG" and low <= self.sl:
            return "SL"
        if self.direction == "SHORT" and high >= self.sl:
            return "SL"
        return None

    def update_bar(
        self,
        bar_index: int,
        high: float,
        low: float,
        close: float,
        atr: float,
        hlc3: float,
        volume: float,
    ):
        """Update AVWAP, SL, MFE/MAE. Called AFTER check_exit."""

        # Accumulate AVWAP
        self.avwap.update(hlc3, volume, atr)

        bars_held = bar_index - self.entry_bar

        # Phase transition: after checkpoint_interval bars, SL tracks AVWAP center
        if bars_held >= self.checkpoint_interval and self.sl_phase == "initial":
            self.sl_phase = "avwap"
            target_sl = self.avwap.center
            if self.direction == "LONG" and target_sl > self.sl:
                self.sl = target_sl
            elif self.direction == "SHORT" and target_sl < self.sl:
                self.sl = target_sl

        # Continuously track AVWAP center (ratcheted) after phase transition
        if self.sl_phase == "avwap":
            target_sl = self.avwap.center
            if self.direction == "LONG" and target_sl > self.sl:
                self.sl = target_sl
            elif self.direction == "SHORT" and target_sl < self.sl:
                self.sl = target_sl

        # MFE/MAE
        if self.direction == "LONG":
            ub = (high - self.entry_price) / self.entry_price * self.original_notional
            uw = (low - self.entry_price) / self.entry_price * self.original_notional
        else:
            ub = (self.entry_price - low) / self.entry_price * self.original_notional
            uw = (self.entry_price - high) / self.entry_price * self.original_notional
        self.mfe = max(self.mfe, ub)
        self.mae = min(self.mae, uw)
        if ub > 0:
            self.saw_green = True

    def check_scale_out(self, bar_index: int, close: float) -> bool:
        """Check if at a checkpoint and close hits +/-2sigma in trade direction."""
        if self.scale_count >= self.max_scaleouts:
            return False
        bars_held = bar_index - self.entry_bar
        if bars_held < self.checkpoint_interval:
            return False
        if (bars_held % self.checkpoint_interval) != 0:
            return False

        c = self.avwap.center
        s = self.avwap.sigma
        if self.direction == "LONG":
            return close >= c + 2 * s
        else:
            return close <= c - 2 * s

    def do_scale_out(self, bar_index: int, close: float, exit_commission: float) -> Tuple[Trade383, bool]:
        """Execute scale-out. Returns (Trade383, is_fully_closed)."""
        self.scale_count += 1
        is_final = (self.scale_count >= self.max_scaleouts)

        if is_final:
            close_notional = self.notional
        else:
            close_notional = self.notional / 2

        if self.direction == "LONG":
            pnl = (close - self.entry_price) / self.entry_price * close_notional
        else:
            pnl = (self.entry_price - close) / self.entry_price * close_notional

        self.notional -= close_notional

        # SL snaps to AVWAP center after scale-out
        target_sl = self.avwap.center
        if self.direction == "LONG" and target_sl > self.sl:
            self.sl = target_sl
        elif self.direction == "SHORT" and target_sl < self.sl:
            self.sl = target_sl

        trade = Trade383(
            direction=self.direction,
            grade=self.grade,
            entry_bar=self.entry_bar,
            exit_bar=bar_index,
            entry_price=self.entry_price,
            exit_price=close,
            sl_price=self.sl,
            tp_price=None,
            pnl=pnl,
            commission=exit_commission,
            mfe=self.mfe,
            mae=self.mae,
            exit_reason=f"SCALE_{self.scale_count}",
            saw_green=self.saw_green,
            be_raised=False,
            exit_stage=0,
            entry_atr=self._entry_atr,
            scale_idx=self.scale_count,
        )
        return trade, is_final

    def close_at(self, price: float, bar_index: int, reason: str, commission: float) -> Trade383:
        """Close remaining position and return Trade383 record."""
        if self.direction == "LONG":
            pnl = (price - self.entry_price) / self.entry_price * self.notional
        else:
            pnl = (self.entry_price - price) / self.entry_price * self.notional

        return Trade383(
            direction=self.direction,
            grade=self.grade,
            entry_bar=self.entry_bar,
            exit_bar=bar_index,
            entry_price=self.entry_price,
            exit_price=price,
            sl_price=self.sl,
            tp_price=None,
            pnl=pnl,
            commission=commission,
            mfe=self.mfe,
            mae=self.mae,
            exit_reason=reason,
            saw_green=self.saw_green,
            be_raised=False,
            exit_stage=0,
            entry_atr=self._entry_atr,
            scale_idx=0,
        )
