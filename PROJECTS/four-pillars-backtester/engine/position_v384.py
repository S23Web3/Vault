"""
Position slot for v3.8.4: ATR SL + optional ATR TP, AVWAP trailing, scale-out.

v3.8.4 adds: tp_mult parameter for ATR-based take profit.
Everything else identical to v3.8.3.

SL logic (unchanged from v3.8.3):
  A/B/C/D entries: ATR-based SL (entry_price +/- ATR * sl_mult). Fixed for first N bars.
  ADD/RE entries: AVWAP 2sigma SL (inherited from parent slot). Fixed for first N bars.
  After checkpoint_interval bars: SL moves to AVWAP center, continuously ratcheted.

BE raise (cooperates with AVWAP):
  be_trigger_atr=X: when unrealized P&L exceeds X*ATR, raise SL to entry +/- be_lock_atr*ATR.
  Fires FAST on spikes (checked every bar, no checkpoint wait).
  Checked BEFORE AVWAP ratchet in update_bar() -- both cooperate:
    BE locks in on spikes, AVWAP continues trailing the trend afterward.
  be_trigger_atr=0: disabled (default).

TP logic (NEW in v3.8.4):
  tp_mult=None: no TP (same as v3.8.3 behavior)
  tp_mult=X: TP at entry_price +/- ATR * X. Closes full position.
  SL checked first (pessimistic) when both could trigger on same bar.

Scale-out (unchanged):
  At each checkpoint, if close hits AVWAP +/- 2sigma, close half.
  Max 2 scale-outs. TP takes priority over scale-out if both trigger.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .avwap import AVWAPTracker


@dataclass
class Trade384:
    """Completed trade record for v3.8.4."""
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


class PositionSlot384:
    """One position with ATR/AVWAP SL, optional ATR TP, and scale-out."""

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
        tp_mult: float = None,
        be_trigger_atr: float = 0.0,
        be_lock_atr: float = 0.0,
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

        # BE raise: fires fast on spikes, before AVWAP ratchet
        self.be_raised = False
        self.be_trigger_atr = be_trigger_atr
        self.be_lock_atr = be_lock_atr
        if be_trigger_atr > 0:
            if direction == "LONG":
                self._be_trigger_price = entry_price + atr * be_trigger_atr
                self._be_lock_sl = entry_price + atr * be_lock_atr
            else:
                self._be_trigger_price = entry_price - atr * be_trigger_atr
                self._be_lock_sl = entry_price - atr * be_lock_atr
        else:
            self._be_trigger_price = None
            self._be_lock_sl = None

        # AVWAP: inherit from parent (ADD/RE) or start fresh (A/B/C/D)
        if avwap_state is not None:
            self.avwap = avwap_state.clone()
        else:
            self.avwap = AVWAPTracker(sigma_floor_atr)
        self.avwap.update(hlc3, volume, atr)

        # SL initialization
        self.sl_phase = "initial"
        if grade in ("A", "B", "C", "D"):
            if direction == "LONG":
                self.sl = entry_price - (atr * sl_mult)
            else:
                self.sl = entry_price + (atr * sl_mult)
        else:
            c, s = self.avwap.center, self.avwap.sigma
            if direction == "LONG":
                self.sl = c - 2 * s
            else:
                self.sl = c + 2 * s

        # TP initialization (None = no TP, same as v3.8.3)
        self.tp = None
        if tp_mult is not None:
            if direction == "LONG":
                self.tp = entry_price + (atr * tp_mult)
            else:
                self.tp = entry_price - (atr * tp_mult)

        # MFE/MAE
        self.mfe = 0.0
        self.mae = 0.0
        self.saw_green = False

    def check_exit(self, high: float, low: float) -> Optional[str]:
        """Check if SL or TP hit. SL first (pessimistic). Called BEFORE update_bar."""
        if self.direction == "LONG":
            if low <= self.sl:
                return "SL"
            if self.tp is not None and high >= self.tp:
                return "TP"
        else:
            if high >= self.sl:
                return "SL"
            if self.tp is not None and low <= self.tp:
                return "TP"
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
        self.avwap.update(hlc3, volume, atr)
        bars_held = bar_index - self.entry_bar

        # BE raise: check BEFORE AVWAP ratchet. Fires fast on spikes.
        if not self.be_raised and self._be_trigger_price is not None:
            triggered = (self.direction == "LONG" and high >= self._be_trigger_price) or \
                        (self.direction == "SHORT" and low <= self._be_trigger_price)
            if triggered:
                self.be_raised = True
                if self.direction == "LONG" and self._be_lock_sl > self.sl:
                    self.sl = self._be_lock_sl
                elif self.direction == "SHORT" and self._be_lock_sl < self.sl:
                    self.sl = self._be_lock_sl

        if bars_held >= self.checkpoint_interval and self.sl_phase == "initial":
            self.sl_phase = "avwap"
            target_sl = self.avwap.center
            if self.direction == "LONG" and target_sl > self.sl:
                self.sl = target_sl
            elif self.direction == "SHORT" and target_sl < self.sl:
                self.sl = target_sl

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

    def do_scale_out(self, bar_index: int, close: float, exit_commission: float) -> Tuple[Trade384, bool]:
        """Execute scale-out. Returns (Trade384, is_fully_closed)."""
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

        target_sl = self.avwap.center
        if self.direction == "LONG" and target_sl > self.sl:
            self.sl = target_sl
        elif self.direction == "SHORT" and target_sl < self.sl:
            self.sl = target_sl

        trade = Trade384(
            direction=self.direction,
            grade=self.grade,
            entry_bar=self.entry_bar,
            exit_bar=bar_index,
            entry_price=self.entry_price,
            exit_price=close,
            sl_price=self.sl,
            tp_price=self.tp,
            pnl=pnl,
            commission=exit_commission,
            mfe=self.mfe,
            mae=self.mae,
            exit_reason=f"SCALE_{self.scale_count}",
            saw_green=self.saw_green,
            be_raised=self.be_raised,
            exit_stage=0,
            entry_atr=self._entry_atr,
            scale_idx=self.scale_count,
        )
        return trade, is_final

    def close_at(self, price: float, bar_index: int, reason: str, commission: float) -> Trade384:
        """Close remaining position and return Trade384 record."""
        if self.direction == "LONG":
            pnl = (price - self.entry_price) / self.entry_price * self.notional
        else:
            pnl = (self.entry_price - price) / self.entry_price * self.notional

        return Trade384(
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
            exit_stage=0,
            entry_atr=self._entry_atr,
            scale_idx=0,
        )
