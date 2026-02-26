"""
Four Pillars entry signal state machine -- v3.8.3.

Zone trigger: Stoch 60-K enters oversold/overbought (< 25 / > 75).
While zone active, track faster stochs: 9 (< 30), 14 (< 30), 40 (< 25).
Signal fires when 9-K crosses back out of oversold/overbought.

A (4/4): 9 + 14 + 40 all flagged. Bypasses Cloud 3.
B (3/4): 9 + 14 flagged. Requires Cloud 3.
C (2/4): 9 flagged only. Requires price firmly above/below Cloud 3.
D (continuation): 60-K stays pinned, 9-K cycles again. No Cloud 3.
"""

from dataclasses import dataclass


@dataclass
class SignalResult:
    """Output from one bar of the state machine."""
    long_a: bool = False
    long_b: bool = False
    long_c: bool = False
    long_d: bool = False
    short_a: bool = False
    short_b: bool = False
    short_c: bool = False
    short_d: bool = False
    reentry_long: bool = False
    reentry_short: bool = False
    add_long: bool = False
    add_short: bool = False

    @property
    def any_long(self) -> bool:
        return self.long_a or self.long_b or self.long_c or self.long_d

    @property
    def any_short(self) -> bool:
        return self.short_a or self.short_b or self.short_c or self.short_d


class FourPillarsStateMachine383:
    """
    v3.8.3 state machine.

    Stages:
      0: Idle. 60-K enters extreme -> stage 1.
      1: A/B/C tracking. 9-K cross back -> fire A/B/C. If 60-K still in zone -> stage 2.
      2: D-ready. Waiting for 9-K to re-enter zone. If 60-K leaves -> stage 0.
      3: D-tracking. 9-K in zone, waiting for cross back -> D fires. Loop to stage 2 if 60-K stays.
    """

    def __init__(
        self,
        cross_level: int = 25,
        zone_level: int = 30,
        stage_lookback: int = 10,
        allow_b: bool = True,
        allow_c: bool = True,
        b_open_fresh: bool = True,
        cloud2_reentry: bool = True,
        reentry_lookback: int = 10,
        use_60d: bool = False,
        add_zone_short: int = 70,
        add_zone_long: int = 30,
        add_mid_short: float = 52.0,
        add_mid_long: float = 48.0,
    ):
        self.cross_level = cross_level
        self.zone_level = zone_level
        self.stage_lookback = stage_lookback
        self.allow_b = allow_b
        self.allow_c = allow_c
        self.b_open_fresh = b_open_fresh
        self.cloud2_reentry = cloud2_reentry
        self.reentry_lookback = reentry_lookback
        self.use_60d = use_60d
        self.add_zone_short = add_zone_short
        self.add_zone_long = add_zone_long
        self.add_mid_short = add_mid_short
        self.add_mid_long = add_mid_long

        # Long setup state
        self.long_stage = 0
        self.long_stage_bar = None
        self.long_9_entered = False
        self.long_9_seen = False
        self.long_14_seen = False
        self.long_40_seen = False

        # Short setup state
        self.short_stage = 0
        self.short_stage_bar = None
        self.short_9_entered = False
        self.short_9_seen = False
        self.short_14_seen = False
        self.short_40_seen = False

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
        cloud3_bull: bool,
        price_pos: int,
        price_cross_above_cloud2: bool,
        price_cross_below_cloud2: bool,
    ) -> SignalResult:
        """Process one bar, return signals."""

        result = SignalResult()

        cross_low = self.cross_level
        cross_high = 100 - self.cross_level
        zone_low = self.zone_level
        zone_high = 100 - self.zone_level

        # Cloud 3 directional filter
        cloud3_ok_long = price_pos >= 0
        cloud3_ok_short = price_pos <= 0
        d_ok_long = not self.use_60d or stoch_60_d > 20
        d_ok_short = not self.use_60d or stoch_60_d < 80

        # --- LONG STATE MACHINE ---
        long_signal = False
        long_signal_b = False
        long_signal_c = False
        long_signal_d = False

        if self.long_stage == 0:
            # Stage 0: Idle. Wait for 60-K to enter oversold.
            if stoch_60 < cross_low:
                self.long_stage = 1
                self.long_stage_bar = bar_index
                self.long_9_entered = stoch_9 < cross_low
                self.long_9_seen = stoch_9 < zone_low
                self.long_14_seen = stoch_14 < zone_low
                self.long_40_seen = stoch_40 < cross_low

        elif self.long_stage == 1:
            # Stage 1: A/B/C tracking. Wait for 9-K to cross back.
            if bar_index - self.long_stage_bar > self.stage_lookback:
                # Timeout — check if 60-K still in zone for D transition
                if stoch_60 < cross_low:
                    self.long_stage = 2
                    self.long_stage_bar = bar_index
                else:
                    self.long_stage = 0
            elif self.long_9_entered and stoch_9 >= cross_low:
                # 9-K crossed back above 25 — check flags
                if self.long_9_seen and self.long_14_seen and self.long_40_seen and d_ok_long:
                    long_signal = True      # A: 4/4
                elif self.long_9_seen and self.long_14_seen and self.allow_b and cloud3_ok_long and d_ok_long:
                    long_signal_b = True    # B: 3/4
                elif self.long_9_seen and self.allow_c and price_pos == 1:
                    long_signal_c = True    # C: 2/4

                # After signal (or no signal): check if 60-K still in zone for D
                if stoch_60 < cross_low:
                    self.long_stage = 2
                    self.long_stage_bar = bar_index
                else:
                    self.long_stage = 0
            else:
                # Still tracking flags
                if stoch_9 < cross_low:
                    self.long_9_entered = True
                if stoch_9 < zone_low:
                    self.long_9_seen = True
                if stoch_14 < zone_low:
                    self.long_14_seen = True
                if stoch_40 < cross_low:
                    self.long_40_seen = True

        elif self.long_stage == 2:
            # Stage 2: D-ready. 60-K still in zone. Wait for 9-K to re-enter oversold.
            if stoch_60 >= cross_low:
                self.long_stage = 0  # 60-K left zone
            elif bar_index - self.long_stage_bar > self.stage_lookback:
                if stoch_60 < cross_low:
                    self.long_stage_bar = bar_index  # reset lookback, 60-K still pinned
                else:
                    self.long_stage = 0
            elif stoch_9 < cross_low:
                # 9-K re-entered oversold — start D tracking
                self.long_stage = 3
                self.long_stage_bar = bar_index
                self.long_9_entered = True

        elif self.long_stage == 3:
            # Stage 3: D-tracking. Wait for 9-K to cross back.
            if stoch_60 >= cross_low:
                self.long_stage = 0  # 60-K left zone
            elif bar_index - self.long_stage_bar > self.stage_lookback:
                if stoch_60 < cross_low:
                    self.long_stage = 2
                    self.long_stage_bar = bar_index
                else:
                    self.long_stage = 0
            elif self.long_9_entered and stoch_9 >= cross_low:
                # 9-K crossed back — D fires
                long_signal_d = True
                if stoch_60 < cross_low:
                    self.long_stage = 2  # loop — can fire more D's
                    self.long_stage_bar = bar_index
                else:
                    self.long_stage = 0
            else:
                if stoch_9 < cross_low:
                    self.long_9_entered = True

        # --- SHORT STATE MACHINE ---
        short_signal = False
        short_signal_b = False
        short_signal_c = False
        short_signal_d = False

        if self.short_stage == 0:
            if stoch_60 > cross_high:
                self.short_stage = 1
                self.short_stage_bar = bar_index
                self.short_9_entered = stoch_9 > cross_high
                self.short_9_seen = stoch_9 > zone_high
                self.short_14_seen = stoch_14 > zone_high
                self.short_40_seen = stoch_40 > cross_high

        elif self.short_stage == 1:
            if bar_index - self.short_stage_bar > self.stage_lookback:
                if stoch_60 > cross_high:
                    self.short_stage = 2
                    self.short_stage_bar = bar_index
                else:
                    self.short_stage = 0
            elif self.short_9_entered and stoch_9 <= cross_high:
                if self.short_9_seen and self.short_14_seen and self.short_40_seen and d_ok_short:
                    short_signal = True
                elif self.short_9_seen and self.short_14_seen and self.allow_b and cloud3_ok_short and d_ok_short:
                    short_signal_b = True
                elif self.short_9_seen and self.allow_c and price_pos == -1:
                    short_signal_c = True

                if stoch_60 > cross_high:
                    self.short_stage = 2
                    self.short_stage_bar = bar_index
                else:
                    self.short_stage = 0
            else:
                if stoch_9 > cross_high:
                    self.short_9_entered = True
                if stoch_9 > zone_high:
                    self.short_9_seen = True
                if stoch_14 > zone_high:
                    self.short_14_seen = True
                if stoch_40 > cross_high:
                    self.short_40_seen = True

        elif self.short_stage == 2:
            if stoch_60 <= cross_high:
                self.short_stage = 0
            elif bar_index - self.short_stage_bar > self.stage_lookback:
                if stoch_60 > cross_high:
                    self.short_stage_bar = bar_index
                else:
                    self.short_stage = 0
            elif stoch_9 > cross_high:
                self.short_stage = 3
                self.short_stage_bar = bar_index
                self.short_9_entered = True

        elif self.short_stage == 3:
            if stoch_60 <= cross_high:
                self.short_stage = 0
            elif bar_index - self.short_stage_bar > self.stage_lookback:
                if stoch_60 > cross_high:
                    self.short_stage = 2
                    self.short_stage_bar = bar_index
                else:
                    self.short_stage = 0
            elif self.short_9_entered and stoch_9 <= cross_high:
                short_signal_d = True
                if stoch_60 > cross_high:
                    self.short_stage = 2
                    self.short_stage_bar = bar_index
                else:
                    self.short_stage = 0
            else:
                if stoch_9 > cross_high:
                    self.short_9_entered = True

        # --- RE-ENTRY TRACKING ---
        any_long = long_signal or long_signal_b or long_signal_c or long_signal_d
        any_short = short_signal or short_signal_b or short_signal_c or short_signal_d

        if any_long:
            self.bars_since_long = 0
        else:
            self.bars_since_long += 1

        if any_short:
            self.bars_since_short = 0
        else:
            self.bars_since_short += 1

        recent_long = 0 < self.bars_since_long <= self.reentry_lookback
        recent_short = 0 < self.bars_since_short <= self.reentry_lookback

        reentry_long = (self.cloud2_reentry and price_cross_above_cloud2 and
                        recent_long and not any_long)
        reentry_short = (self.cloud2_reentry and price_cross_below_cloud2 and
                         recent_short and not any_short)

        # --- ADD SIGNALS ---
        add_long = (stoch_9 > self.add_zone_long and
                    stoch_40 > self.add_mid_long and stoch_60 > self.add_mid_long)
        add_short = (stoch_9 < self.add_zone_short and
                     stoch_40 < self.add_mid_short and stoch_60 < self.add_mid_short)

        # Pack result
        result.long_a = long_signal
        result.long_b = long_signal_b
        result.long_c = long_signal_c
        result.long_d = long_signal_d
        result.short_a = short_signal
        result.short_b = short_signal_b
        result.short_c = short_signal_c
        result.short_d = short_signal_d
        result.reentry_long = reentry_long
        result.reentry_short = reentry_short
        result.add_long = add_long
        result.add_short = add_short

        return result
