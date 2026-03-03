"""
Four Pillars v3.9.0 State Machine — Aligned to Pine v3.8.2 source of truth.

KEY CHANGES FROM state_machine.py (v386):
- Grade C removed from state machine entirely.
  In Pine, C was "2/4 stochs + Cloud 3". That is NOT what Grade C means in trading.
  Grade C = continuation/pyramid entry when already in a same-direction position.
  The ENGINE (backtester_v390.py) assigns grade "C" when A/B fires while in position.
  The state machine only produces A and B.
- require_stage2 removed. Not present in Pine v3.8.2 source.
- rot_level removed. Not present in Pine v3.8.2 source.
- cloud3_window removed. Not present in Pine v3.8.2 source.
- Grade A: 4/4 stochs, bypasses Cloud 3 filter (highest conviction reversal).
  Matches Pine comment: "A trade (4/4) -- bypasses Cloud 3 filter (highest conviction reversal)"
- Grade B: 3/4 stochs, Cloud 3 gated.
  Matches Pine comment: "B trade (3/4) -- requires Cloud 3 alignment"
- Re-entry (R): Cloud 2 cross after recent signal. Handled externally, passed in via signal columns.

Source of truth: four_pillars_v3_8_2_strategy.pine Section 8 (lines ~165-230)
"""

from dataclasses import dataclass, field


@dataclass
class SignalResult:
    """Output from one bar of the state machine."""
    long_a: bool = False
    long_b: bool = False
    short_a: bool = False
    short_b: bool = False
    reentry_long: bool = False
    reentry_short: bool = False

    @property
    def any_long(self) -> bool:
        return self.long_a or self.long_b or self.reentry_long

    @property
    def any_short(self) -> bool:
        return self.short_a or self.short_b or self.reentry_short

    @property
    def any_signal(self) -> bool:
        return self.any_long or self.any_short


class FourPillarsStateMachine390:
    """
    Bar-by-bar state machine. Produces A and B signals only.

    Grade C is NOT produced here. The engine labels an entry as C when
    A or B fires while a same-direction position is already open.

    Matches Pine v3.8.2 Section 8 logic exactly:
    - Stage 0: waiting for stoch_9 to enter zone (< crossLow or > crossHigh)
    - Stage 1: stoch_9 in zone, track which others also enter zone
    - On stoch_9 exit from zone: count confirmations → A (4/4) or B (3/4)
    - Timeout: if stoch_9 stays in zone > stage_lookback bars → reset
    """

    def __init__(
        self,
        cross_level: int = 25,
        zone_level: int = 30,
        stage_lookback: int = 10,
        allow_b: bool = True,
        b_open_fresh: bool = True,
        cloud2_reentry: bool = True,
        reentry_lookback: int = 10,
        use_ripster: bool = False,
        use_60d: bool = False,
    ):
        self.cross_level = cross_level
        self.zone_level = zone_level
        self.stage_lookback = stage_lookback
        self.allow_b = allow_b
        self.b_open_fresh = b_open_fresh
        self.cloud2_reentry = cloud2_reentry
        self.reentry_lookback = reentry_lookback
        self.use_ripster = use_ripster
        self.use_60d = use_60d

        # Long state
        self.long_stage = 0
        self.long_stage1_bar = None
        self.long_14_seen = False
        self.long_40_seen = False
        self.long_60_seen = False

        # Short state
        self.short_stage = 0
        self.short_stage1_bar = None
        self.short_14_seen = False
        self.short_40_seen = False
        self.short_60_seen = False

        # Re-entry tracking
        self.bars_since_long = 999
        self.bars_since_short = 999

    def process_bar(
        self,
        bar_index: int,
        stoch_9: float,
        stoch_14: float,
        stoch_40: float,
        stoch_60: float,
        stoch_60_d: float,
        price_pos: int,                   # -1=below cloud3, 0=inside, 1=above
        price_cross_above_cloud2: bool,
        price_cross_below_cloud2: bool,
    ) -> SignalResult:
        """
        Process one bar. Returns SignalResult with A/B/reentry flags.

        price_pos maps to Pine's price_pos:
          close > cloud3_top  → 1
          close < cloud3_bottom → -1
          else → 0

        Cloud 3 gates:
          cloud3_allows_long  = price_pos >= 0  (above or inside cloud3)
          cloud3_allows_short = price_pos <= 0  (below or inside cloud3)

        Grade A bypasses Cloud 3 (4/4 = highest conviction, Pine comment explicit).
        Grade B requires Cloud 3 alignment (3/4).
        """
        result = SignalResult()

        cross_low  = self.cross_level
        cross_high = 100 - self.cross_level
        zone_low   = self.zone_level
        zone_high  = 100 - self.zone_level

        # Cloud 3 directional gates
        cloud3_ok_long  = price_pos >= 0
        cloud3_ok_short = price_pos <= 0

        # Optional 60-D filter
        d_ok_long  = (not self.use_60d) or (stoch_60_d > 20)
        d_ok_short = (not self.use_60d) or (stoch_60_d < 80)

        # ── LONG SETUP STATE MACHINE ──────────────────────────────────────────
        long_signal   = False
        long_signal_b = False

        if self.long_stage == 0:
            if stoch_9 < cross_low:
                self.long_stage = 1
                self.long_stage1_bar = bar_index
                # Snapshot which other stochs are already in zone at Stage 1 entry
                self.long_14_seen = stoch_14 < zone_low
                self.long_40_seen = stoch_40 < zone_low
                self.long_60_seen = stoch_60 < cross_low

        elif self.long_stage == 1:
            if bar_index - self.long_stage1_bar > self.stage_lookback:
                # Timeout — reset
                self.long_stage = 0
            elif stoch_9 >= cross_low:
                # stoch_9 exited zone — evaluate
                others = (
                    (1 if self.long_14_seen else 0)
                    + (1 if self.long_40_seen else 0)
                    + (1 if self.long_60_seen else 0)
                )
                if others == 3 and d_ok_long:
                    # Grade A: 4/4 stochs, NO Cloud 3 gate (Pine: bypasses filter)
                    long_signal = True
                elif others >= 2 and self.allow_b and cloud3_ok_long and d_ok_long:
                    # Grade B: 3/4 stochs, Cloud 3 gated
                    long_signal_b = True
                # Grade C deliberately omitted — engine labels continuation entries
                self.long_stage = 0
            else:
                # Still in Stage 1 — accumulate confirmations
                if stoch_14 < zone_low:
                    self.long_14_seen = True
                if stoch_40 < zone_low:
                    self.long_40_seen = True
                if stoch_60 < cross_low:
                    self.long_60_seen = True

        # ── SHORT SETUP STATE MACHINE ─────────────────────────────────────────
        short_signal   = False
        short_signal_b = False

        if self.short_stage == 0:
            if stoch_9 > cross_high:
                self.short_stage = 1
                self.short_stage1_bar = bar_index
                self.short_14_seen = stoch_14 > zone_high
                self.short_40_seen = stoch_40 > zone_high
                self.short_60_seen = stoch_60 > cross_high

        elif self.short_stage == 1:
            if bar_index - self.short_stage1_bar > self.stage_lookback:
                self.short_stage = 0
            elif stoch_9 <= cross_high:
                others = (
                    (1 if self.short_14_seen else 0)
                    + (1 if self.short_40_seen else 0)
                    + (1 if self.short_60_seen else 0)
                )
                if others == 3 and d_ok_short:
                    # Grade A: 4/4, no Cloud 3 gate
                    short_signal = True
                elif others >= 2 and self.allow_b and cloud3_ok_short and d_ok_short:
                    # Grade B: 3/4, Cloud 3 gated
                    short_signal_b = True
                self.short_stage = 0
            else:
                if stoch_14 > zone_high:
                    self.short_14_seen = True
                if stoch_40 > zone_high:
                    self.short_40_seen = True
                if stoch_60 > cross_high:
                    self.short_60_seen = True

        # ── RE-ENTRY TRACKING ─────────────────────────────────────────────────
        any_long  = long_signal or long_signal_b
        any_short = short_signal or short_signal_b

        if any_long:
            self.bars_since_long = 0
        else:
            self.bars_since_long = min(self.bars_since_long + 1, 999)

        if any_short:
            self.bars_since_short = 0
        else:
            self.bars_since_short = min(self.bars_since_short + 1, 999)

        recent_long  = 0 < self.bars_since_long  <= self.reentry_lookback
        recent_short = 0 < self.bars_since_short <= self.reentry_lookback

        reentry_long  = (
            self.cloud2_reentry
            and price_cross_above_cloud2
            and recent_long
            and not any_long
        )
        reentry_short = (
            self.cloud2_reentry
            and price_cross_below_cloud2
            and recent_short
            and not any_short
        )

        result.long_a       = long_signal
        result.long_b       = long_signal_b
        result.short_a      = short_signal
        result.short_b      = short_signal_b
        result.reentry_long  = reentry_long
        result.reentry_short = reentry_short

        return result
