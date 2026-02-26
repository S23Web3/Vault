"""
Position slot for v3.8.2: AVWAP-anchored 3-stage trailing SL.
Each slot tracks one independent position with its own AVWAP.

Stage 1: SL at AVWAP +/- 2sigma (wide, dynamic)
Stage 2: SL at AVWAP +/- (ATR * mult) (tighter, fixed duration)
Stage 3: SL at Cloud3 boundary +/- (ATR * mult) (trailing forever)
"""

from dataclasses import dataclass
from typing import Optional

from .avwap import AVWAPTracker


@dataclass
class Trade382:
    """Completed trade record for v3.8.2."""
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


class PositionSlot:
    """One position with AVWAP-based 3-stage trailing SL."""

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
        sl_atr_mult: float = 1.0,
        stage1to2_trigger: str = "opposite_2sigma",
        stage2_bars: int = 5,
        notional: float = 5000.0,
        be_levels: list = None,
    ):
        self.direction = direction
        self.grade = grade
        self.entry_bar = entry_bar
        self.entry_price = entry_price
        self.notional = notional
        self.sl_atr_mult = sl_atr_mult
        self.stage1to2_trigger = stage1to2_trigger
        self.stage2_bars = stage2_bars

        # Stage machine
        self.stage = 1
        self.stage_bar = entry_bar

        # AVWAP (seed with entry bar)
        self.avwap = AVWAPTracker(sigma_floor_atr)
        self.avwap.update(hlc3, volume, atr)

        # Initial SL at AVWAP +/- 2sigma (Stage 1)
        c, s = self.avwap.center, self.avwap.sigma
        if direction == "LONG":
            self.sl = c - 2 * s
        else:
            self.sl = c + 2 * s

        # MFE/MAE
        self.mfe = 0.0
        self.mae = 0.0
        self.saw_green = False

        # BE raise (multi-level)
        self._entry_atr = atr
        self.be_levels = be_levels or []
        self.be_active = [False] * len(self.be_levels)
        self.be_triggered = False
        self.entry_commission = 0.0

    def check_exit(self, high: float, low: float) -> Optional[str]:
        """Check if SL hit using current bar's high/low. Returns 'SL' or None.
        Called BEFORE update_bar (uses SL from previous bar)."""
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
        cloud3_top: float,
        cloud3_bottom: float,
    ):
        """Update AVWAP, stage transitions, SL, and MFE/MAE.
        Called AFTER check_exit (sets SL for next bar)."""

        # Step A: Accumulate AVWAP
        self.avwap.update(hlc3, volume, atr)
        c = self.avwap.center
        s = self.avwap.sigma
        p2 = c + 2 * s
        m2 = c - 2 * s

        # Step B: Stage transitions
        bars_in_stage = bar_index - self.stage_bar

        if self.stage == 1:
            transition = False
            if self.stage1to2_trigger == "opposite_2sigma":
                if self.direction == "LONG" and high >= p2:
                    transition = True
                elif self.direction == "SHORT" and low <= m2:
                    transition = True
            elif self.stage1to2_trigger == "bars_5" and bars_in_stage >= 5:
                transition = True
            elif self.stage1to2_trigger == "bars_10" and bars_in_stage >= 10:
                transition = True

            if transition:
                self.stage = 2
                self.stage_bar = bar_index
                bars_in_stage = 0

        if self.stage == 2 and bars_in_stage >= self.stage2_bars:
            self.stage = 3
            self.stage_bar = bar_index

        # Step C: Compute target SL
        if self.stage == 1:
            target_sl = m2 if self.direction == "LONG" else p2
        elif self.stage == 2:
            if self.direction == "LONG":
                target_sl = c - (self.sl_atr_mult * atr)
            else:
                target_sl = c + (self.sl_atr_mult * atr)
        else:  # stage 3
            if self.direction == "LONG":
                target_sl = cloud3_bottom - (self.sl_atr_mult * atr)
            else:
                target_sl = cloud3_top + (self.sl_atr_mult * atr)

        # Step D: Ratchet (SL only moves in favorable direction)
        if self.direction == "LONG" and target_sl > self.sl:
            self.sl = target_sl
        elif self.direction == "SHORT" and target_sl < self.sl:
            self.sl = target_sl

        # Step D2: Multi-level BE raise
        if self.be_levels:
            for lv_idx, (trigger_mult, lock_mult) in enumerate(self.be_levels):
                if self.be_active[lv_idx]:
                    continue
                if self.direction == "LONG":
                    if high - self.entry_price >= trigger_mult * self._entry_atr:
                        be_sl = self.entry_price + lock_mult * self._entry_atr
                        if be_sl > self.sl:
                            self.sl = be_sl
                        self.be_active[lv_idx] = True
                        self.be_triggered = True
                else:
                    if self.entry_price - low >= trigger_mult * self._entry_atr:
                        be_sl = self.entry_price - lock_mult * self._entry_atr
                        if be_sl < self.sl:
                            self.sl = be_sl
                        self.be_active[lv_idx] = True
                        self.be_triggered = True

        # Step E: MFE/MAE
        if self.direction == "LONG":
            ub = (high - self.entry_price) / self.entry_price * self.notional
            uw = (low - self.entry_price) / self.entry_price * self.notional
        else:
            ub = (self.entry_price - low) / self.entry_price * self.notional
            uw = (self.entry_price - high) / self.entry_price * self.notional
        self.mfe = max(self.mfe, ub)
        self.mae = min(self.mae, uw)
        if ub > 0:
            self.saw_green = True

    def close_at(self, price: float, bar_index: int, reason: str, commission: float) -> Trade382:
        """Close position and return Trade382 record."""
        if self.direction == "LONG":
            pnl = (price - self.entry_price) / self.entry_price * self.notional
        else:
            pnl = (self.entry_price - price) / self.entry_price * self.notional

        return Trade382(
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
            be_raised=self.be_triggered,
            exit_stage=self.stage,
            entry_atr=self._entry_atr,
        )
