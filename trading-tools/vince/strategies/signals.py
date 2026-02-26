"""
Four Pillars A/B/C signal generation (state machine).

Implements:
- Stage 1 → Stage 2 state machine for A signals (4/4 stochs)
- B signals (3/4 stochs)
- C signals (2/4 stochs + Cloud 3)
- Cooldown gate (min bars between entries)
- Cloud 3 directional filter

Matches Pine Script v3.8 logic exactly.
"""

import pandas as pd
import numpy as np
from typing import Dict


class FourPillarsSignals:
    """
    Generate A/B/C entry signals using multi-stochastic state machine.
    """

    def __init__(self, cross_level: int = 25, zone_level: int = 30,
                 stage_lookback: int = 10, cooldown_bars: int = 3,
                 allow_b_trades: bool = True, allow_c_trades: bool = True):
        """
        Initialize signal generator.

        Args:
            cross_level: 9-3 stoch cross level (default 25)
            zone_level: Other stochs zone level (default 30)
            stage_lookback: Max bars in Stage 1 before expiry (default 10)
            cooldown_bars: Min bars between entries (default 3)
            allow_b_trades: Enable B signals (default True)
            allow_c_trades: Enable C signals (default True)
        """
        self.cross_level = cross_level
        self.zone_level = zone_level
        self.stage_lookback = stage_lookback
        self.cooldown_bars = cooldown_bars
        self.allow_b_trades = allow_b_trades
        self.allow_c_trades = allow_c_trades

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate A/B/C signals for entire DataFrame.

        Requires columns: stoch_9_3, stoch_14_3, stoch_40_3, stoch_60_10,
                          cloud3_allows_long, cloud3_allows_short, price_pos

        Adds columns:
        - long_signal, long_signal_b, long_signal_c
        - short_signal, short_signal_b, short_signal_c
        - enter_long_a, enter_short_a (cooldown-gated A signals)
        - enter_long_bc, enter_short_bc (cooldown-gated B/C signals)

        Args:
            df: DataFrame with indicators already calculated

        Returns:
            Modified DataFrame with signal columns
        """
        # Initialize signal columns
        df['long_signal'] = False
        df['long_signal_b'] = False
        df['long_signal_c'] = False
        df['short_signal'] = False
        df['short_signal_b'] = False
        df['short_signal_c'] = False

        # State machine variables (row-by-row processing required)
        long_stage = 0
        long_stage1_bar = -999
        long_14_seen = False
        long_40_seen = False
        long_60_seen = False

        short_stage = 0
        short_stage1_bar = -999
        short_14_seen = False
        short_40_seen = False
        short_60_seen = False

        last_entry_bar = -999

        cross_low = self.cross_level
        cross_high = 100 - self.cross_level
        zone_low = self.zone_level
        zone_high = 100 - self.zone_level

        # Row-by-row state machine
        for idx in range(len(df)):
            row = df.iloc[idx]

            # === LONG SIGNALS ===
            if long_stage == 0:
                if row['stoch_9_3'] < cross_low:
                    long_stage = 1
                    long_stage1_bar = idx
                    long_14_seen = row['stoch_14_3'] < zone_low
                    long_40_seen = row['stoch_40_3'] < zone_low
                    long_60_seen = row['stoch_60_10'] < cross_low

            elif long_stage == 1:
                if idx - long_stage1_bar > self.stage_lookback:
                    long_stage = 0
                elif row['stoch_9_3'] >= cross_low:
                    # Stage 2: Exit oversold
                    long_others = int(long_14_seen) + int(long_40_seen) + int(long_60_seen)

                    if long_others == 3 and row['cloud3_allows_long']:
                        df.at[df.index[idx], 'long_signal'] = True
                    elif long_others >= 2 and self.allow_b_trades and row['cloud3_allows_long']:
                        df.at[df.index[idx], 'long_signal_b'] = True
                    elif long_14_seen and self.allow_c_trades and row['price_pos'] == 1:
                        df.at[df.index[idx], 'long_signal_c'] = True

                    long_stage = 0
                else:
                    # Still in Stage 1 - track other stochs
                    if row['stoch_14_3'] < zone_low:
                        long_14_seen = True
                    if row['stoch_40_3'] < zone_low:
                        long_40_seen = True
                    if row['stoch_60_10'] < cross_low:
                        long_60_seen = True

            # === SHORT SIGNALS ===
            if short_stage == 0:
                if row['stoch_9_3'] > cross_high:
                    short_stage = 1
                    short_stage1_bar = idx
                    short_14_seen = row['stoch_14_3'] > zone_high
                    short_40_seen = row['stoch_40_3'] > zone_high
                    short_60_seen = row['stoch_60_10'] > cross_high

            elif short_stage == 1:
                if idx - short_stage1_bar > self.stage_lookback:
                    short_stage = 0
                elif row['stoch_9_3'] <= cross_high:
                    short_others = int(short_14_seen) + int(short_40_seen) + int(short_60_seen)

                    if short_others == 3 and row['cloud3_allows_short']:
                        df.at[df.index[idx], 'short_signal'] = True
                    elif short_others >= 2 and self.allow_b_trades and row['cloud3_allows_short']:
                        df.at[df.index[idx], 'short_signal_b'] = True
                    elif short_14_seen and self.allow_c_trades and row['price_pos'] == -1:
                        df.at[df.index[idx], 'short_signal_c'] = True

                    short_stage = 0
                else:
                    if row['stoch_14_3'] > zone_high:
                        short_14_seen = True
                    if row['stoch_40_3'] > zone_high:
                        short_40_seen = True
                    if row['stoch_60_10'] > cross_high:
                        short_60_seen = True

        # Cooldown-gated entry signals
        df['enter_long_a'] = False
        df['enter_short_a'] = False
        df['enter_long_bc'] = False
        df['enter_short_bc'] = False

        last_entry_bar = -999
        for idx in range(len(df)):
            cooldown_ok = (idx - last_entry_bar) >= self.cooldown_bars

            if df.iloc[idx]['long_signal'] and cooldown_ok:
                df.at[df.index[idx], 'enter_long_a'] = True
                last_entry_bar = idx
            elif df.iloc[idx]['short_signal'] and cooldown_ok:
                df.at[df.index[idx], 'enter_short_a'] = True
                last_entry_bar = idx
            elif (df.iloc[idx]['long_signal_b'] or df.iloc[idx]['long_signal_c']) and cooldown_ok:
                df.at[df.index[idx], 'enter_long_bc'] = True
                last_entry_bar = idx
            elif (df.iloc[idx]['short_signal_b'] or df.iloc[idx]['short_signal_c']) and cooldown_ok:
                df.at[df.index[idx], 'enter_short_bc'] = True
                last_entry_bar = idx

        return df
