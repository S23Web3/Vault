"""
AVWAP (Anchored Volume-Weighted Average Price) tracker.
Cumulative from entry bar. Computes center + sigma bands.
Matches v3.8.2 Pine Script compute_avwap_bands() exactly.
"""

import math


class AVWAPTracker:
    """Volume-weighted average price with standard deviation bands."""

    def __init__(self, sigma_floor_atr: float = 0.5):
        self.cum_pv = 0.0       # sum(hlc3 * volume)
        self.cum_v = 0.0        # sum(volume)
        self.cum_pv2 = 0.0      # sum(hlc3^2 * volume)
        self.sigma_floor_atr = sigma_floor_atr
        self.center = 0.0
        self.sigma = 0.0

    def update(self, hlc3: float, volume: float, atr: float):
        """Accumulate one bar, recompute center and sigma."""
        if volume <= 0:
            volume = 1e-10
        self.cum_pv += hlc3 * volume
        self.cum_v += volume
        self.cum_pv2 += hlc3 * hlc3 * volume

        self.center = self.cum_pv / self.cum_v
        variance = max((self.cum_pv2 / self.cum_v) - self.center ** 2, 0.0)
        sigma_raw = math.sqrt(variance)
        self.sigma = max(sigma_raw, self.sigma_floor_atr * atr)

    def bands(self) -> tuple:
        """Return (center, +1s, -1s, +2s, -2s)."""
        s = self.sigma
        c = self.center
        return c, c + s, c - s, c + 2 * s, c - 2 * s

    def clone(self):
        """Deep copy for AVWAP inheritance (ADD/RE slots copy parent's state)."""
        c = AVWAPTracker(self.sigma_floor_atr)
        c.cum_pv = self.cum_pv
        c.cum_v = self.cum_v
        c.cum_pv2 = self.cum_pv2
        c.center = self.center
        c.sigma = self.sigma
        return c

    def freeze(self) -> tuple:
        """Return (center, sigma) for re-entry state."""
        return self.center, self.sigma
