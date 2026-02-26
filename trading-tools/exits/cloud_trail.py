"""
Cloud 3 trailing stop (v3.5.1 architecture).
Trail activates when ema50 crosses ema72 (Cloud 3/4 alignment).
SL follows Cloud 3 ± 1 ATR, ratchets favorable only.
"""

import numpy as np


class CloudTrailExit:
    """
    Initial SL = entry ± (initial_sl_mult × ATR)
    Once Cloud 3/4 aligns: SL trails Cloud 3 boundary ± trail_atr_mult × ATR
    SL only ratchets in favorable direction.
    """

    def __init__(self, initial_sl_mult: float = 2.0, trail_atr_mult: float = 1.0):
        self.initial_sl_mult = initial_sl_mult
        self.trail_atr_mult = trail_atr_mult
        self.activated = False
        self.current_sl = None

    def reset(self):
        self.activated = False
        self.current_sl = None

    def compute_initial(self, direction: str, entry_price: float, atr: float) -> dict:
        self.reset()
        if direction == "LONG":
            self.current_sl = entry_price - self.initial_sl_mult * atr
        else:
            self.current_sl = entry_price + self.initial_sl_mult * atr
        return {"sl": self.current_sl, "tp": None, "be_raise": 0}

    def update_sl(self, direction: str, cloud3_top: float, cloud3_bottom: float,
                  ema50: float, ema72: float, atr: float) -> float:
        """Update trailing SL. Returns new SL value."""
        # Check activation: Cloud 3/4 alignment
        if not self.activated:
            if direction == "LONG" and ema50 > ema72:
                self.activated = True
            elif direction == "SHORT" and ema50 < ema72:
                self.activated = True

        if not self.activated:
            return self.current_sl

        # Trail
        if direction == "LONG":
            trail_sl = cloud3_bottom - self.trail_atr_mult * atr
            if trail_sl > self.current_sl:
                self.current_sl = trail_sl
        else:
            trail_sl = cloud3_top + self.trail_atr_mult * atr
            if trail_sl < self.current_sl:
                self.current_sl = trail_sl

        return self.current_sl
