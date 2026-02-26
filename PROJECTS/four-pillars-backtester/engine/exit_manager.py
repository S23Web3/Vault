"""
Dynamic SL/TP management with 4 risk methods.

Methods:
  be_only:              Move SL to breakeven when MFE >= trigger
  be_plus_fees:         Move SL to entry + fees_atr when MFE >= trigger
  be_plus_fees_trail_tp: SL to entry + fees, TP trails
  be_trail_tp:          Both SL and TP trail from MFE peak
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExitConfig:
    """Configuration for the exit manager."""
    risk_method: str = "be_only"
    mfe_trigger: float = 1.0
    sl_lock: float = 0.0
    tp_trail_distance: float = 0.5
    fees_atr: float = 0.3

    def __post_init__(self):
        valid = ("be_only", "be_plus_fees", "be_plus_fees_trail_tp", "be_trail_tp")
        if self.risk_method not in valid:
            raise ValueError(f"risk_method must be one of {valid}, got {self.risk_method!r}")


class ExitManager:
    """
    Manages dynamic SL/TP adjustments based on position MFE.

    Usage:
        em = ExitManager(ExitConfig(risk_method="be_plus_fees", mfe_trigger=1.0))
        new_sl, new_tp = em.update_stops(
            direction="LONG", entry_price=100.0, current_atr=2.0,
            current_sl=98.0, current_tp=103.0, mfe_atr=1.2, peak_price=102.5
        )
    """

    def __init__(self, config: Optional[ExitConfig] = None):
        self.config = config or ExitConfig()
        self._activated = False

    def reset(self):
        """Reset activation state for a new position."""
        self._activated = False

    def update_stops(
        self,
        direction: str,
        entry_price: float,
        current_atr: float,
        current_sl: float,
        current_tp: float,
        mfe_atr: float,
        peak_price: float,
    ) -> tuple[float, float]:
        """
        Compute updated SL/TP based on risk method and current MFE.

        Args:
            direction: "LONG" or "SHORT".
            entry_price: Original entry price.
            current_atr: Current ATR value.
            current_sl: Current stop loss level.
            current_tp: Current take profit level.
            mfe_atr: Maximum Favorable Excursion in ATR units.
            peak_price: Best price reached so far.

        Returns:
            (new_sl, new_tp) -- never moves SL backwards (always improves).
        """
        cfg = self.config
        new_sl = current_sl
        new_tp = current_tp

        if mfe_atr < cfg.mfe_trigger:
            return new_sl, new_tp

        self._activated = True
        method = cfg.risk_method

        if method == "be_only":
            new_sl = self._be_sl(direction, entry_price, 0.0, current_atr)

        elif method == "be_plus_fees":
            new_sl = self._be_sl(direction, entry_price, cfg.fees_atr, current_atr)

        elif method == "be_plus_fees_trail_tp":
            new_sl = self._be_sl(direction, entry_price, cfg.fees_atr, current_atr)
            new_tp = self._trail_tp(direction, peak_price, cfg.tp_trail_distance, current_atr)

        elif method == "be_trail_tp":
            trail_sl = self._trail_sl(direction, peak_price, cfg.sl_lock, current_atr)
            new_sl = trail_sl
            new_tp = self._trail_tp(direction, peak_price, cfg.tp_trail_distance, current_atr)

        # Never move SL backwards
        if direction == "LONG":
            new_sl = max(new_sl, current_sl)
        else:
            new_sl = min(new_sl, current_sl)

        return new_sl, new_tp

    @staticmethod
    def _be_sl(direction: str, entry: float, offset_atr: float, atr: float) -> float:
        """SL at breakeven + offset."""
        offset = offset_atr * atr
        if direction == "LONG":
            return entry + offset
        return entry - offset

    @staticmethod
    def _trail_sl(direction: str, peak: float, lock_atr: float, atr: float) -> float:
        """Trailing SL locked behind peak price."""
        lock = lock_atr * atr
        if direction == "LONG":
            return peak - lock
        return peak + lock

    @staticmethod
    def _trail_tp(direction: str, peak: float, trail_dist_atr: float, atr: float) -> float:
        """Trailing TP ahead of peak price."""
        dist = trail_dist_atr * atr
        if direction == "LONG":
            return peak + dist
        return peak - dist


if __name__ == "__main__":
    em = ExitManager(ExitConfig(risk_method="be_plus_fees", mfe_trigger=1.0, fees_atr=0.3))
    sl, tp = em.update_stops("LONG", 100.0, 2.0, 98.0, 103.0, 1.2, 102.5)
    print(f"SL: {sl}, TP: {tp}")
