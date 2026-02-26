"""
Phased exit strategy (ATR-SL-MOVEMENT spec — not yet built in Pine Script).
SL progresses through Cloud 2 → Cloud 3 → Cloud 4 phases.
"""


class PhasedExit:
    """
    Phase 1: Entry → Cloud 2 alignment. SL = entry ± initial_mult × ATR
    Phase 2: Cloud 2 aligned. SL trails Cloud 2 boundary ± phase2_mult × ATR
    Phase 3: Cloud 3 aligned. SL trails Cloud 3 boundary ± phase3_mult × ATR
    Phase 4: Cloud 4 aligned. SL trails Cloud 4 boundary ± phase4_mult × ATR
    """

    def __init__(self, initial_mult: float = 1.5,
                 phase2_mult: float = 0.5, phase3_mult: float = 0.5,
                 phase4_mult: float = 0.5):
        self.initial_mult = initial_mult
        self.phase2_mult = phase2_mult
        self.phase3_mult = phase3_mult
        self.phase4_mult = phase4_mult
        self.phase = 1
        self.current_sl = None

    def reset(self):
        self.phase = 1
        self.current_sl = None

    def compute_initial(self, direction: str, entry_price: float, atr: float) -> dict:
        self.reset()
        if direction == "LONG":
            self.current_sl = entry_price - self.initial_mult * atr
        else:
            self.current_sl = entry_price + self.initial_mult * atr
        return {"sl": self.current_sl, "tp": None, "be_raise": 0}

    def update_sl(self, direction: str, cloud2_bull: bool, cloud3_bull: bool,
                  cloud4_bull: bool, cloud2_top: float, cloud2_bottom: float,
                  cloud3_top: float, cloud3_bottom: float,
                  ema72: float, ema89: float, atr: float) -> float:
        """Update phased SL. Returns new SL value."""

        # Phase progression
        if direction == "LONG":
            if self.phase == 1 and cloud2_bull:
                self.phase = 2
            if self.phase == 2 and cloud3_bull:
                self.phase = 3
            if self.phase == 3 and cloud4_bull:
                self.phase = 4

            if self.phase == 2:
                new_sl = cloud2_bottom - self.phase2_mult * atr
            elif self.phase == 3:
                new_sl = cloud3_bottom - self.phase3_mult * atr
            elif self.phase == 4:
                cloud4_bottom = min(ema72, ema89)
                new_sl = cloud4_bottom - self.phase4_mult * atr
            else:
                return self.current_sl

            # Ratchet only
            if new_sl > self.current_sl:
                self.current_sl = new_sl

        else:  # SHORT
            if self.phase == 1 and not cloud2_bull:
                self.phase = 2
            if self.phase == 2 and not cloud3_bull:
                self.phase = 3
            if self.phase == 3 and not cloud4_bull:
                self.phase = 4

            if self.phase == 2:
                new_sl = cloud2_top + self.phase2_mult * atr
            elif self.phase == 3:
                new_sl = cloud3_top + self.phase3_mult * atr
            elif self.phase == 4:
                cloud4_top = max(ema72, ema89)
                new_sl = cloud4_top + self.phase4_mult * atr
            else:
                return self.current_sl

            if new_sl < self.current_sl:
                self.current_sl = new_sl

        return self.current_sl
