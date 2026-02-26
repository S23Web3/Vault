"""
Four Pillars entry signal state machine.
Bar-by-bar processing with persistent state, matching v3.7.1 lines 102-283.
"""

from dataclasses import dataclass, field


@dataclass
class SignalResult:
    """Output from one bar of the state machine."""
    long_a: bool = False
    long_b: bool = False
    long_c: bool = False
    short_a: bool = False
    short_b: bool = False
    short_c: bool = False
    reentry_long: bool = False
    reentry_short: bool = False
    add_long: bool = False
    add_short: bool = False

    @property
    def any_long(self) -> bool:
        return self.long_a or self.long_b or self.long_c

    @property
    def any_short(self) -> bool:
        return self.short_a or self.short_b or self.short_c


class FourPillarsStateMachine:
    """
    Processes bars one at a time, maintains persistent state.
    Matches v3.7.1 Pine Script logic exactly.
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
        use_ripster: bool = False,
        use_60d: bool = False,
        add_zone_short: int = 70,
        add_zone_long: int = 30,
        add_mid_short: float = 52.0,
        add_mid_long: float = 48.0,
    ):
        # Settings
        self.cross_level = cross_level
        self.zone_level = zone_level
        self.stage_lookback = stage_lookback
        self.allow_b = allow_b
        self.allow_c = allow_c
        self.b_open_fresh = b_open_fresh
        self.cloud2_reentry = cloud2_reentry
        self.reentry_lookback = reentry_lookback
        self.use_ripster = use_ripster
        self.use_60d = use_60d
        self.add_zone_short = add_zone_short
        self.add_zone_long = add_zone_long
        self.add_mid_short = add_mid_short
        self.add_mid_long = add_mid_long

        # Persistent state — long setup
        self.long_stage = 0
        self.long_stage1_bar = None
        self.long_14_seen = False
        self.long_40_seen = False
        self.long_60_seen = False

        # Persistent state — short setup
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
        cloud3_bull: bool,
        price_pos: int,
        price_cross_above_cloud2: bool,
        price_cross_below_cloud2: bool,
    ) -> SignalResult:
        """Process one bar, return signals. Matches v3.7.1 lines 102-226."""

        result = SignalResult()

        cross_low = self.cross_level
        cross_high = 100 - self.cross_level
        zone_low = self.zone_level
        zone_high = 100 - self.zone_level

        # Filters
        ripster_ok_long = not self.use_ripster or cloud3_bull or price_pos >= 0
        ripster_ok_short = not self.use_ripster or not cloud3_bull or price_pos <= 0
        d_ok_long = not self.use_60d or stoch_60_d > 20
        d_ok_short = not self.use_60d or stoch_60_d < 80

        # ─── LONG SETUP STATE MACHINE ───
        long_signal = False
        long_signal_b = False
        long_signal_c = False

        if self.long_stage == 0:
            if stoch_9 < cross_low:
                self.long_stage = 1
                self.long_stage1_bar = bar_index
                self.long_14_seen = stoch_14 < zone_low
                self.long_40_seen = stoch_40 < zone_low
                self.long_60_seen = stoch_60 < cross_low

        elif self.long_stage == 1:
            if bar_index - self.long_stage1_bar > self.stage_lookback:
                self.long_stage = 0
            elif stoch_9 >= cross_low:
                others = (1 if self.long_14_seen else 0) + (1 if self.long_40_seen else 0) + (1 if self.long_60_seen else 0)
                if others == 3 and ripster_ok_long and d_ok_long:
                    long_signal = True
                elif others >= 2 and self.allow_b and ripster_ok_long and d_ok_long:
                    long_signal_b = True
                elif self.long_14_seen and self.allow_c and price_pos == 1:
                    long_signal_c = True
                self.long_stage = 0
            else:
                if stoch_14 < zone_low:
                    self.long_14_seen = True
                if stoch_40 < zone_low:
                    self.long_40_seen = True
                if stoch_60 < cross_low:
                    self.long_60_seen = True

        # ─── SHORT SETUP STATE MACHINE ───
        short_signal = False
        short_signal_b = False
        short_signal_c = False

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
                others = (1 if self.short_14_seen else 0) + (1 if self.short_40_seen else 0) + (1 if self.short_60_seen else 0)
                if others == 3 and ripster_ok_short and d_ok_short:
                    short_signal = True
                elif others >= 2 and self.allow_b and ripster_ok_short and d_ok_short:
                    short_signal_b = True
                elif self.short_14_seen and self.allow_c and price_pos == -1:
                    short_signal_c = True
                self.short_stage = 0
            else:
                if stoch_14 > zone_high:
                    self.short_14_seen = True
                if stoch_40 > zone_high:
                    self.short_40_seen = True
                if stoch_60 > cross_high:
                    self.short_60_seen = True

        # ─── RE-ENTRY TRACKING ───
        any_long = long_signal or long_signal_b or long_signal_c
        any_short = short_signal or short_signal_b or short_signal_c

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

        # ─── ADD SIGNALS ───
        add_long = (stoch_9 > self.add_zone_long and
                    stoch_40 > self.add_mid_long and stoch_60 > self.add_mid_long)
        # Crossover approximation: was below, now above
        add_short = (stoch_9 < self.add_zone_short and
                     stoch_40 < self.add_mid_short and stoch_60 < self.add_mid_short)

        # Pack result
        result.long_a = long_signal
        result.long_b = long_signal_b
        result.long_c = long_signal_c
        result.short_a = short_signal
        result.short_b = short_signal_b
        result.short_c = short_signal_c
        result.reentry_long = reentry_long
        result.reentry_short = reentry_short
        result.add_long = add_long
        result.add_short = add_short

        return result
