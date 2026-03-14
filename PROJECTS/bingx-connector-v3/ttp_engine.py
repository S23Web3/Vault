"""
Trailing Take Profit (TTP) exit engine.

Two-phase state machine: MONITORING -> ACTIVATED -> CLOSED.
Runs dual pessimistic/optimistic scenarios per candle.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TTPResult:
    """Result of evaluating one candle through the TTP engine."""

    closed_pessimistic: bool = False
    closed_optimistic: bool = False
    exit_pct_pessimistic: Optional[float] = None
    exit_pct_optimistic: Optional[float] = None
    trail_level_pct: Optional[float] = None
    extreme_pct: Optional[float] = None
    state: str = "MONITORING"


class TTPExit:
    """Trailing Take Profit exit engine -- evaluates one candle at a time."""

    def __init__(self, direction, entry_price, activation_pct=0.005,
                 trail_distance_pct=0.002):
        """Initialize TTP engine with direction, entry, activation, and trail distance."""
        self.direction = direction.upper()
        self.entry = float(entry_price)
        self.act = float(activation_pct)
        self.dist = float(trail_distance_pct)

        # State
        self.state = "MONITORING"
        self.extreme = None
        self.trail_level = None

        # Activation price (computed once)
        if self.direction == "LONG":
            self.activation_price = self.entry * (1.0 + self.act)
        else:
            self.activation_price = self.entry * (1.0 - self.act)

    def evaluate(self, candle_high, candle_low):
        """Evaluate one candle. Returns TTPResult."""
        h = float(candle_high)
        l = float(candle_low)

        # BUG 1 FIX: If already closed, return immediately with no mutation
        if self.state == "CLOSED":
            return TTPResult(state="CLOSED")

        if self.state == "MONITORING":
            activated = self._try_activate(h, l)
            if not activated:
                return TTPResult(state="MONITORING")
            # Activation candle: update extreme if candle extends past activation
            # but do NOT check trail stop (that starts next candle)
            self._update_extreme_on_activation(h, l)
            return TTPResult(
                state="ACTIVATED",
                trail_level_pct=self._trail_pct(),
                extreme_pct=self._extreme_pct(),
            )

        # --- ACTIVATED (non-activation candle): run dual scenario ---
        if self.direction == "LONG":
            result = self._evaluate_long(h, l)
        else:
            result = self._evaluate_short(h, l)
        return result

    def _try_activate(self, h, l):
        """Check if activation threshold is reached. Sets extreme and trail on activation."""
        if self.direction == "LONG":
            if h >= self.activation_price:
                self.state = "ACTIVATED"
                self.extreme = self.activation_price
                self.trail_level = self.extreme * (1.0 - self.dist)
                return True
        else:
            if l <= self.activation_price:
                self.state = "ACTIVATED"
                self.extreme = self.activation_price
                self.trail_level = self.extreme * (1.0 + self.dist)
                return True
        return False

    def _update_extreme_on_activation(self, h, l):
        """On activation candle, extend extreme past activation_price if candle overshoots."""
        if self.direction == "LONG":
            if h > self.extreme:
                self.extreme = h
                self.trail_level = self.extreme * (1.0 - self.dist)
        else:
            if l < self.extreme:
                self.extreme = l
                self.trail_level = self.extreme * (1.0 + self.dist)

    def _trail_pct(self):
        """Compute trail level as pct from entry."""
        if self.trail_level is None:
            return None
        if self.direction == "LONG":
            return (self.trail_level - self.entry) / self.entry
        return (self.entry - self.trail_level) / self.entry

    def _extreme_pct(self):
        """Compute extreme as pct from entry."""
        if self.extreme is None:
            return None
        if self.direction == "LONG":
            return (self.extreme - self.entry) / self.entry
        return (self.entry - self.extreme) / self.entry

    def _evaluate_long(self, h, l):
        """Evaluate long position: high extends, low reverses."""
        # Snapshot current state for pessimistic check
        pess_extreme = self.extreme
        pess_trail = self.trail_level

        # PESSIMISTIC: check reversal BEFORE updating extreme
        closed_pess = False
        exit_pct_pess = None
        if l <= pess_trail:
            closed_pess = True
            exit_pct_pess = (pess_trail - self.entry) / self.entry
        else:
            # Update extreme only if not closed
            if h > pess_extreme:
                pess_extreme = h
                pess_trail = pess_extreme * (1.0 - self.dist)

        # OPTIMISTIC: update extreme BEFORE checking reversal
        opt_extreme = self.extreme
        opt_trail = self.trail_level
        if h > opt_extreme:
            opt_extreme = h
            opt_trail = opt_extreme * (1.0 - self.dist)
        closed_opt = False
        exit_pct_opt = None
        if l <= opt_trail:
            closed_opt = True
            exit_pct_opt = (opt_trail - self.entry) / self.entry

        # Commit pessimistic state as conservative baseline
        if not closed_pess:
            self.extreme = pess_extreme
            self.trail_level = pess_trail
        else:
            # Keep state at pre-close values (no further updates)
            pass

        # Only pessimistic close drives state -- optimistic is informational only
        if closed_pess:
            self.state = "CLOSED"

        return TTPResult(
            closed_pessimistic=closed_pess,
            closed_optimistic=closed_opt,
            exit_pct_pessimistic=exit_pct_pess,
            exit_pct_optimistic=exit_pct_opt,
            trail_level_pct=(self.trail_level - self.entry) / self.entry if self.trail_level else None,
            extreme_pct=(self.extreme - self.entry) / self.entry if self.extreme else None,
            state=self.state,
        )

    def _evaluate_short(self, h, l):
        """Evaluate short position: low extends, high reverses."""
        # Snapshot current state for pessimistic check
        pess_extreme = self.extreme
        pess_trail = self.trail_level

        # PESSIMISTIC: check reversal BEFORE updating extreme
        closed_pess = False
        exit_pct_pess = None
        if h >= pess_trail:
            closed_pess = True
            exit_pct_pess = (self.entry - pess_trail) / self.entry
        else:
            if l < pess_extreme:
                pess_extreme = l
                pess_trail = pess_extreme * (1.0 + self.dist)

        # OPTIMISTIC: update extreme BEFORE checking reversal
        opt_extreme = self.extreme
        opt_trail = self.trail_level
        if l < opt_extreme:
            opt_extreme = l
            opt_trail = opt_extreme * (1.0 + self.dist)
        closed_opt = False
        exit_pct_opt = None
        if h >= opt_trail:
            closed_opt = True
            exit_pct_opt = (self.entry - opt_trail) / self.entry

        # Commit pessimistic state as conservative baseline
        if not closed_pess:
            self.extreme = pess_extreme
            self.trail_level = pess_trail

        # Only pessimistic close drives state -- optimistic is informational only
        if closed_pess:
            self.state = "CLOSED"

        return TTPResult(
            closed_pessimistic=closed_pess,
            closed_optimistic=closed_opt,
            exit_pct_pessimistic=exit_pct_pess,
            exit_pct_optimistic=exit_pct_opt,
            trail_level_pct=(self.entry - self.trail_level) / self.entry if self.trail_level else None,
            extreme_pct=(self.entry - self.extreme) / self.entry if self.extreme else None,
            state=self.state,
        )


def run_ttp_on_trade(candles_df, entry_price, direction,
                     activation_pct=0.005, trail_distance_pct=0.002):
    """Run TTP engine over a DataFrame of candles for one trade.

    Returns dict with exit_candle_idx, exit_pct_pess, exit_pct_opt,
    band_width_pct, and candle_results list.
    """
    engine = TTPExit(direction, entry_price, activation_pct, trail_distance_pct)
    results = []
    exit_idx = None

    # BUG 4 FIX: use enumerate + itertuples for positional index and speed
    for i, row in enumerate(candles_df[["high", "low"]].itertuples(index=False)):
        result = engine.evaluate(candle_high=row.high, candle_low=row.low)
        results.append(result)
        if exit_idx is None and (result.closed_pessimistic or result.closed_optimistic):
            exit_idx = i

    # Collect exit percentages
    exit_pct_pess = None
    exit_pct_opt = None
    if results:
        for r in results:
            if r.closed_pessimistic and exit_pct_pess is None:
                exit_pct_pess = r.exit_pct_pessimistic
            if r.closed_optimistic and exit_pct_opt is None:
                exit_pct_opt = r.exit_pct_optimistic

    # BUG 5 FIX: Only compute band_width when both scenarios have closed
    band_width_pct = None
    if exit_pct_pess is not None and exit_pct_opt is not None:
        band_width_pct = abs(exit_pct_opt - exit_pct_pess)

    return {
        "exit_candle_idx": exit_idx,
        "exit_pct_pessimistic": exit_pct_pess,
        "exit_pct_optimistic": exit_pct_opt,
        "band_width_pct": band_width_pct,
        "candle_results": results,
    }
