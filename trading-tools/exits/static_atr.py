"""
Static ATR exit strategy (v3.7.1 default).
Fixed SL/TP at entry, optional breakeven+$X raise.
"""


class StaticATRExit:
    """
    SL = entry ± (sl_mult × ATR)
    TP = entry ± (tp_mult × ATR)
    Optional: raise SL to breakeven+$X when unrealized profit >= $X
    """

    def __init__(self, sl_mult: float = 1.0, tp_mult: float = 1.5,
                 use_tp: bool = True, be_raise: float = 0.0):
        self.sl_mult = sl_mult
        self.tp_mult = tp_mult
        self.use_tp = use_tp
        self.be_raise = be_raise

    def compute_levels(self, direction: str, entry_price: float, atr: float) -> dict:
        if direction == "LONG":
            sl = entry_price - self.sl_mult * atr
            tp = (entry_price + self.tp_mult * atr) if self.use_tp else None
        else:
            sl = entry_price + self.sl_mult * atr
            tp = (entry_price - self.tp_mult * atr) if self.use_tp else None
        return {"sl": sl, "tp": tp, "be_raise": self.be_raise}
