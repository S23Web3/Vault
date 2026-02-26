"""
AVWAP trailing stop (v3.6 architecture).
SL = AVWAP ± max(stdev, ATR). Ratchets favorable only.
"""

import numpy as np


class AVWAPTrailExit:
    """
    Anchors AVWAP to entry bar.
    SL = AVWAP ± max(stdev, floor_atr_mult × ATR)
    Floor prevents stdev=0 on bar 1 from creating near-zero SL.
    """

    def __init__(self, floor_atr_mult: float = 1.0):
        self.floor_atr_mult = floor_atr_mult
        self.sum_pv = 0.0
        self.sum_v = 0.0
        self.prices = []
        self.current_sl = None

    def reset(self):
        self.sum_pv = 0.0
        self.sum_v = 0.0
        self.prices = []
        self.current_sl = None

    def compute_initial(self, direction: str, entry_price: float, atr: float,
                        hlc3: float, volume: float) -> dict:
        self.reset()
        self.sum_pv = hlc3 * volume
        self.sum_v = volume
        self.prices.append(hlc3)

        # Bar 1: stdev=0, use ATR floor
        sl_dist = self.floor_atr_mult * atr
        if direction == "LONG":
            self.current_sl = entry_price - sl_dist
        else:
            self.current_sl = entry_price + sl_dist

        return {"sl": self.current_sl, "tp": None, "be_raise": 0}

    def update_sl(self, direction: str, hlc3: float, volume: float, atr: float) -> float:
        """Update AVWAP and trailing SL. Returns new SL value."""
        self.sum_pv += hlc3 * volume
        self.sum_v += volume
        self.prices.append(hlc3)

        avwap = self.sum_pv / self.sum_v if self.sum_v > 0 else hlc3

        # Standard deviation of hlc3 values since anchor
        if len(self.prices) > 1:
            stdev = np.std(self.prices)
        else:
            stdev = 0.0

        sl_dist = max(stdev, self.floor_atr_mult * atr)

        if direction == "LONG":
            new_sl = avwap - sl_dist
            if new_sl > self.current_sl:
                self.current_sl = new_sl
        else:
            new_sl = avwap + sl_dist
            if new_sl < self.current_sl:
                self.current_sl = new_sl

        return self.current_sl
