"""
Position slot for v3.9.1: 3-phase SL movement + Cloud 2 hard close.

Replaces the AVWAP-trail-as-SL approach from position_v384.
AVWAP is kept but only for ADD entry limits and scale-out triggers.

SL Phase System:
  Phase 0 (initial):
    LONG:  sl = entry - (2 x ATR),  tp = entry + (tp_mult x ATR)
    SHORT: sl = entry + (2 x ATR),  tp = entry - (tp_mult x ATR)

  Phase 1 (Cloud 2 cross in trade direction, fires once):
    LONG:  sl = candle_low - (1 x ATR)  [only if improves sl]
            tp = current_tp + (1 x ATR)
    SHORT: sl = candle_high + (1 x ATR) [only if improves sl]
            tp = current_tp - (1 x ATR)

  Phase 2 (Cloud 3 fresh cross in trade direction, fires once after Phase 1):
    LONG:  sl = sl + (1 x ATR)  [only if improves]
            tp = tp + (1 x ATR)
    SHORT: sl = sl - (1 x ATR)  [only if improves]
            tp = tp - (1 x ATR)

  Phase 3 (Cloud 3 AND Cloud 4 both in sync — continuous ATR trail):
    TP removed.
    LONG:  trail_extreme = max(trail_extreme, high); sl = trail_extreme - (1 x ATR)
    SHORT: trail_extreme = min(trail_extreme, low);  sl = trail_extreme + (1 x ATR)
    Guard: sl only moves in favorable direction.

Hard Close (highest priority — checked BEFORE SL/TP):
  LONG:  Cloud 2 crosses bearish (EMA5 < EMA12) -> exit immediately, reason=CLOUD2_CLOSE
  SHORT: Cloud 2 crosses bullish (EMA5 > EMA12) -> exit immediately, reason=CLOUD2_CLOSE

Breakeven (checked every bar before phase updates):
  When high (long) or low (short) crosses be_trigger_price, raise SL to be_lock_price.
  BE cooperates with phases: phases can continue moving SL after BE fires.

AVWAP role (corrected):
  - Scale-out trigger: at checkpoints, close 50% if price at +/-2sigma in trade direction
  - ADD entry limit: price must be at/past -2sigma (long) or +2sigma (short)
  - NOT used as SL trail
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .avwap import AVWAPTracker


@dataclass
class Trade391:
    """Completed trade record for v3.9.1."""
    direction:  str
    grade:      str
    entry_bar:  int
    exit_bar:   int
    entry_price: float
    exit_price:  float
    sl_price:    float
    tp_price:    Optional[float]
    pnl:         float
    commission:  float
    mfe:         float
    mae:         float
    exit_reason: str
    saw_green:   bool
    be_raised:   bool
    sl_phase:    int         # 0/1/2/3 -- which phase when closed
    entry_atr:   float
    scale_idx:   int = 0
    bbwp_state:  str = ""
    bbwp_value:  float = float("nan")
    bbwp_spectrum: str = ""


class PositionSlot391:
    """One position with 3-phase SL movement, Cloud 2 hard close, and AVWAP scale-outs."""

    def __init__(
        self,
        direction:          str,
        grade:              str,
        entry_bar:          int,
        entry_price:        float,
        atr:                float,
        hlc3:               float,
        volume:             float,
        sigma_floor_atr:    float = 0.5,
        sl_mult:            float = 2.0,
        tp_mult:            float = 4.0,
        be_trigger_atr:     float = 1.0,
        be_lock_atr:        float = 0.0,
        notional:           float = 5000.0,
        checkpoint_interval: int  = 5,
        max_scaleouts:      int   = 2,
        avwap_state:        Optional[AVWAPTracker] = None,
    ):
        """Initialise position with Phase 0 SL/TP and optional inherited AVWAP."""
        self.direction       = direction
        self.grade           = grade
        self.entry_bar       = entry_bar
        self.entry_price     = entry_price
        self.notional        = notional
        self.original_notional = notional
        self._entry_atr      = atr
        self.checkpoint_interval = checkpoint_interval
        self.max_scaleouts   = max_scaleouts
        self.scale_count     = 0
        self.entry_commission = 0.0

        # Phase tracking
        self.sl_phase         = 0
        self.phase1_done      = False
        self.phase2_done      = False
        self.phase3_ever_active = False
        self.trail_extreme    = None   # Phase 3 trailing high/low

        # BE raise
        self.be_raised        = False
        self.be_trigger_atr   = be_trigger_atr
        self.be_lock_atr      = be_lock_atr
        if be_trigger_atr > 0:
            if direction == "LONG":
                self._be_trigger_price = entry_price + atr * be_trigger_atr
                self._be_lock_sl       = entry_price + atr * be_lock_atr
            else:
                self._be_trigger_price = entry_price - atr * be_trigger_atr
                self._be_lock_sl       = entry_price - atr * be_lock_atr
        else:
            self._be_trigger_price = None
            self._be_lock_sl       = None

        # AVWAP (inherit from parent for ADD/RE, start fresh for A/B/C)
        if avwap_state is not None:
            self.avwap = avwap_state.clone()
        else:
            self.avwap = AVWAPTracker(sigma_floor_atr)
        self.avwap.update(hlc3, volume, atr)

        # Phase 0: Initial SL (ATR-based)
        if direction == "LONG":
            self.sl = entry_price - (atr * sl_mult)
        else:
            self.sl = entry_price + (atr * sl_mult)

        # TP (tp_mult=0 or None = no TP)
        if tp_mult and tp_mult > 0:
            if direction == "LONG":
                self.tp = entry_price + (atr * tp_mult)
            else:
                self.tp = entry_price - (atr * tp_mult)
        else:
            self.tp = None

        # MFE/MAE
        self.mfe       = 0.0
        self.mae       = 0.0
        self.saw_green = False

        # Cloud 2 hard close flag (set by engine, causes immediate exit)
        self._hard_close = False

    # ── Hard Close ────────────────────────────────────────────────────────────

    def check_cloud2_hard_close(self, cloud2_cross_bear: bool, cloud2_cross_bull: bool) -> bool:
        """
        Return True if Cloud 2 flipped against the trade direction this bar.

        LONG:  Cloud 2 crosses bearish (EMA5 below EMA12) -> hard close
        SHORT: Cloud 2 crosses bullish (EMA5 above EMA12) -> hard close
        """
        if self.direction == "LONG" and cloud2_cross_bear:
            return True
        if self.direction == "SHORT" and cloud2_cross_bull:
            return True
        return False

    # ── Normal Exit Check ─────────────────────────────────────────────────────

    def check_exit(self, high: float, low: float) -> Optional[str]:
        """Check SL or TP hit. SL checked first (pessimistic). Call BEFORE update_bar."""
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

    # ── Bar Update (phase advancement + BE + AVWAP + MFE/MAE) ────────────────

    def update_bar(
        self,
        bar_index:          int,
        high:               float,
        low:                float,
        close:              float,
        atr:                float,
        hlc3:               float,
        volume:             float,
        cloud2_cross_bull:  bool = False,
        cloud2_cross_bear:  bool = False,
        cloud3_cross_bull:  bool = False,
        cloud3_cross_bear:  bool = False,
        phase3_long:        bool = False,
        phase3_short:       bool = False,
    ) -> None:
        """
        Update AVWAP, SL phases, BE, MFE/MAE. Call AFTER check_exit and hard-close check.

        Phase advancement order:
          1. BE raise (fires fast on spikes)
          2. Phase 1 (Cloud 2 cross in trade direction, once)
          3. Phase 2 (Cloud 3 fresh cross after Phase 1, once)
          4. Phase 3 (Cloud 3 + Cloud 4 sync, continuous trail)
        """
        # AVWAP update (used for scale-outs and ADD limits, NOT for SL)
        self.avwap.update(hlc3, volume, atr)

        is_new_bar = bar_index > self.entry_bar

        # 1. Breakeven raise (fastest — checked before phase moves)
        if not self.be_raised and self._be_trigger_price is not None and is_new_bar:
            triggered = (
                (self.direction == "LONG"  and high >= self._be_trigger_price) or
                (self.direction == "SHORT" and low  <= self._be_trigger_price)
            )
            if triggered:
                self.be_raised = True
                if self.direction == "LONG" and self._be_lock_sl > self.sl:
                    self.sl = self._be_lock_sl
                elif self.direction == "SHORT" and self._be_lock_sl < self.sl:
                    self.sl = self._be_lock_sl

        # 2. Phase 1: Cloud 2 cross in trade direction (once, after entry bar)
        if not self.phase1_done and is_new_bar:
            if self.direction == "LONG" and cloud2_cross_bull:
                new_sl = low - atr              # candle low of cross bar minus 1 ATR
                if new_sl > self.sl:            # guard: only improve SL
                    self.sl = new_sl
                if self.tp is not None:
                    self.tp = self.tp + atr     # expand TP
                self.phase1_done = True
                self.sl_phase    = 1
            elif self.direction == "SHORT" and cloud2_cross_bear:
                new_sl = high + atr             # candle high plus 1 ATR
                if new_sl < self.sl:            # guard
                    self.sl = new_sl
                if self.tp is not None:
                    self.tp = self.tp - atr
                self.phase1_done = True
                self.sl_phase    = 1

        # 3. Phase 2: Cloud 3 fresh cross after Phase 1 (once)
        if self.phase1_done and not self.phase2_done and is_new_bar:
            if self.direction == "LONG" and cloud3_cross_bull:
                new_sl = self.sl + atr
                if new_sl > self.sl:            # guard (always true here, but explicit)
                    self.sl = new_sl
                if self.tp is not None:
                    self.tp = self.tp + atr
                self.phase2_done = True
                self.sl_phase    = 2
            elif self.direction == "SHORT" and cloud3_cross_bear:
                new_sl = self.sl - atr
                if new_sl < self.sl:
                    self.sl = new_sl
                if self.tp is not None:
                    self.tp = self.tp - atr
                self.phase2_done = True
                self.sl_phase    = 2

        # 4. Phase 3: Cloud 3 + Cloud 4 sync — continuous ATR trail
        phase3_trigger = (
            (self.direction == "LONG"  and phase3_long) or
            (self.direction == "SHORT" and phase3_short)
        )
        if phase3_trigger and not self.phase3_ever_active:
            # Activate Phase 3: remove TP, initialise trail
            self.tp              = None
            self.trail_extreme   = high if self.direction == "LONG" else low
            self.phase3_ever_active = True
            self.sl_phase        = 3

        if self.phase3_ever_active:
            if self.direction == "LONG":
                self.trail_extreme = max(self.trail_extreme, high)
                trail_sl = self.trail_extreme - atr
                if trail_sl > self.sl:
                    self.sl = trail_sl
            else:
                self.trail_extreme = min(self.trail_extreme, low)
                trail_sl = self.trail_extreme + atr
                if trail_sl < self.sl:
                    self.sl = trail_sl

        # MFE / MAE / saw_green
        if self.direction == "LONG":
            ub = (high - self.entry_price) / self.entry_price * self.original_notional
            uw = (low  - self.entry_price) / self.entry_price * self.original_notional
        else:
            ub = (self.entry_price - low)  / self.entry_price * self.original_notional
            uw = (self.entry_price - high) / self.entry_price * self.original_notional
        self.mfe = max(self.mfe, ub)
        self.mae = min(self.mae, uw)
        if ub > 0:
            self.saw_green = True

    # ── Scale-out ─────────────────────────────────────────────────────────────

    def check_scale_out(self, bar_index: int, close: float) -> bool:
        """Check if at a checkpoint and price hits AVWAP +/-2sigma in trade direction."""
        if self.scale_count >= self.max_scaleouts:
            return False
        bars_held = bar_index - self.entry_bar
        if bars_held < self.checkpoint_interval:
            return False
        if (bars_held % self.checkpoint_interval) != 0:
            return False
        c = self.avwap.center
        s = self.avwap.sigma
        if c is None or s is None:
            return False
        if self.direction == "LONG":
            return close >= c + 2 * s
        else:
            return close <= c - 2 * s

    def do_scale_out(
        self, bar_index: int, close: float, exit_commission: float
    ) -> Tuple["Trade391", bool]:
        """Execute scale-out; return (Trade391, is_fully_closed)."""
        self.scale_count += 1
        is_final = self.scale_count >= self.max_scaleouts
        close_notional = self.notional if is_final else self.notional / 2

        if self.direction == "LONG":
            pnl = (close - self.entry_price) / self.entry_price * close_notional
        else:
            pnl = (self.entry_price - close) / self.entry_price * close_notional

        self.notional -= close_notional

        trade = Trade391(
            direction    = self.direction,
            grade        = self.grade,
            entry_bar    = self.entry_bar,
            exit_bar     = bar_index,
            entry_price  = self.entry_price,
            exit_price   = close,
            sl_price     = self.sl,
            tp_price     = self.tp,
            pnl          = pnl,
            commission   = exit_commission,
            mfe          = self.mfe,
            mae          = self.mae,
            exit_reason  = "SCALE_" + str(self.scale_count),
            saw_green    = self.saw_green,
            be_raised    = self.be_raised,
            sl_phase     = self.sl_phase,
            entry_atr    = self._entry_atr,
            scale_idx    = self.scale_count,
        )
        return trade, is_final

    def close_at(
        self, price: float, bar_index: int, reason: str, commission: float
    ) -> "Trade391":
        """Close remaining position and return Trade391 record."""
        if self.direction == "LONG":
            pnl = (price - self.entry_price) / self.entry_price * self.notional
        else:
            pnl = (self.entry_price - price) / self.entry_price * self.notional

        return Trade391(
            direction    = self.direction,
            grade        = self.grade,
            entry_bar    = self.entry_bar,
            exit_bar     = bar_index,
            entry_price  = self.entry_price,
            exit_price   = price,
            sl_price     = self.sl,
            tp_price     = self.tp,
            pnl          = pnl,
            commission   = commission,
            mfe          = self.mfe,
            mae          = self.mae,
            exit_reason  = reason,
            saw_green    = self.saw_green,
            be_raised    = self.be_raised,
            sl_phase     = self.sl_phase,
            entry_atr    = self._entry_atr,
            scale_idx    = 0,
        )
