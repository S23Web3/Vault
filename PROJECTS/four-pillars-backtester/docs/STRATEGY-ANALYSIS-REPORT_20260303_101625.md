# Strategy Analysis Report
**Generated:** 2026-03-03 10:16 UTC

**Purpose:** Full audit of signal logic, version history, exit mechanics, live bot config, and BBW state. For discussion in Claude Web — do not use this to correct code, use it to understand what is actually happening.
---
## CRITICAL FINDINGS — Read This First
### Finding 1: Live bot is NOT running v386
> The bot plugin (bingx-connector/plugins/four_pillars_v384.py line 21) imports:
>     from signals.four_pillars import compute_signals
> This is the ORIGINAL signals/four_pillars.py — not v386.
> v386 was written but never connected to the bot.
> The bot and the backtester are running different default configurations.

### Finding 2: Trailing stop mechanism is completely different
> Backtester (position_v384.py): AVWAP-based trailing.
>   After checkpoint_interval=5 bars, SL transitions from fixed ATR-SL
>   to AVWAP center, ratcheting continuously with each bar.
> 
> Live bot (config.yaml):
>   trailing_activation_atr_mult: 2.0  (activate when price +/- 2x ATR from entry)
>   trailing_rate: 0.02                 (2% callback from peak)
> 
> These are NOT equivalent. AVWAP trailing is adaptive to volume-weighted price.
> BingX native trailing is a fixed percentage callback. They will produce
> different exit prices on the same trade.

### Finding 3: Breakeven raise is in the backtester but NOT in the live bot
> Backtester: be_trigger_atr and be_lock_atr parameters exist in position_v384.py.
> Live bot config.yaml: no be_trigger_atr or be_lock_atr keys anywhere.
> Bot uses only: fixed ATR SL + BingX native trailing (no BE raise step).
> Backtester includes: fixed ATR SL → optional BE raise → AVWAP trailing.

### Finding 4: rot_level=80 is nearly meaningless as a filter
> require_stage2=True means: stoch_40 AND stoch_60 must have rotated through
> rot_level during Stage 1 before Grade A fires.
> 
> For LONGS with rot_level=80:
>   Condition: stoch_40 > (100 - 80) = 20  at any point during Stage 1.
>   stoch_40 above 20 is almost always true in any market.
>   This filter barely filters anything.
> 
> For SHORTS with rot_level=80:
>   Condition: stoch_40 < 80  at any point during Stage 1.
>   Again, almost always true.
> 
> If the intent was 'stoch_40 must have been in bullish/bearish territory
> before the pullback setup', rot_level=50 would require stoch_40 > 50 for longs.
> That is a meaningful quality filter. rot_level=80 is not.

### Finding 5: BBW is completely orphaned
> signals/bbwp.py exists and computes 10 BBW columns including bbwp_value,
> bbwp_spectrum, bbwp_state.
> It is NOT imported by signals/four_pillars.py (v1).
> It is NOT imported by signals/four_pillars_v386.py.
> It is NOT imported by the bot plugin.
> Vince cannot see BBW state at trade entry because it is never computed
> alongside the signal data. The Enricher will have no BBW columns to snapshot.

### Finding 6: signals/four_pillars.py (v1) vs v386 — different defaults
> v1 (what the bot runs):    allow_c=True,  require_stage2=False, rot_level=None
> v386 (backtester target):  allow_c=False, require_stage2=True,  rot_level=80
> 
> Bot overrides from config.yaml: require_stage2=True, rot_level=80, allow_c=False.
> So bot is effectively aligned with v386 via config — but running older ATR/stoch code.
> Key question: does signals/four_pillars.py have the same state machine logic as v386?

---
## Parameter Comparison Table
| Parameter | state_machine.py default | signals/four_pillars.py (v1) | signals/four_pillars_v386.py | Live bot config.yaml | Notes |
|---|---|---|---|---|---|
| cross_level | 25 | 25 | 25 | not set (uses code default) | stoch_9 entry level |
| zone_level | 30 | 30 | 30 | not set | stoch_14/40/60 zone |
| stage_lookback | 10 | 10 | 10 | not set | bars to wait in Stage 1 |
| allow_b_trades | True | True | True | allow_b: true |  |
| allow_c_trades | True | True | False | allow_c: false | v386 disabled C trades |
| require_stage2 | False | False | True | require_stage2: true | DIVERGENCE: v1 default=False |
| rot_level | 80 | None | 80 | rot_level: 80 | see Finding 4 |
| cloud3_window | 5 | None | 5 | not set | bars near Cloud3 required |
| use_ripster | False | False | False | not set | ripster disabled everywhere |
| use_60d | False | False | False | not set | stoch_60 D-line filter off |
| sl_atr_mult | N/A | N/A | N/A | sl_atr_mult: 2.0 | backtester default: 2.0 |
| tp_atr_mult | N/A | N/A | N/A | tp_atr_mult: null | no fixed TP in either |
| be_trigger_atr | N/A | N/A | N/A | NOT PRESENT | BE raise not in bot |
| trailing (method) | N/A | N/A | N/A | BingX native 2% | backtester uses AVWAP |
| BBW | absent | absent | absent | absent | orphaned — not wired anywhere |

---
## Source: signals/state_machine.py — The Actual Entry Conditions
> This is the core logic. Both the v1 and v386 pipelines use THIS file.
> If you want to understand what Grade A/B/C actually requires, read this.

```python
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
        require_stage2: bool = False,
        rot_level: int = 80,
        cloud3_window: int = 5,
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
        self.require_stage2 = require_stage2
        self.rot_level = rot_level
        self.cloud3_window = cloud3_window

        # Persistent state — long setup
        self.long_stage = 0
        self.long_stage1_bar = None
        self.long_14_seen = False
        self.long_40_seen = False
        self.long_60_seen = False
        self.long_40_rot = False   # Stoch40 crossed above (100-rot_level) during Stage 1
        self.long_60_rot = False   # Stoch60 crossed above (100-rot_level) during Stage 1
        self.long_cloud3_bars_since = 999  # bars since price was last at/above Cloud 3

        # Persistent state — short setup
        self.short_stage = 0
        self.short_stage1_bar = None
        self.short_14_seen = False
        self.short_40_seen = False
        self.short_60_seen = False
        self.short_40_rot = False  # Stoch40 crossed below rot_level during Stage 1
        self.short_60_rot = False  # Stoch60 crossed below rot_level during Stage 1
        self.short_cloud3_bars_since = 999  # bars since price was last at/below Cloud 3

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

        # Cloud 3 directional filter (v3.8: ALWAYS ON)
        # price_pos >= 0 means price is above or inside Cloud 3
        cloud3_ok_long = price_pos >= 0
        cloud3_ok_short = price_pos <= 0
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
                self.long_40_rot = stoch_40 > (100 - self.rot_level)
                self.long_60_rot = stoch_60 > (100 - self.rot_level)
                self.long_cloud3_bars_since = 0 if price_pos >= 0 else 999

        elif self.long_stage == 1:
            if bar_index - self.long_stage1_bar > self.stage_lookback:
                self.long_stage = 0
            elif stoch_9 >= cross_low:
                others = (1 if self.long_14_seen else 0) + (1 if self.long_40_seen else 0) + (1 if self.long_60_seen else 0)
                stage2_ok_long = (not self.require_stage2) or (
                    self.long_40_rot and self.long_60_rot
                    and self.long_cloud3_bars_since <= self.cloud3_window
                )
                if others == 3 and cloud3_ok_long and d_ok_long and stage2_ok_long:
                    long_signal = True
                elif others >= 2 and self.allow_b and cloud3_ok_long and d_ok_long:
                    # Don't fire Grade B if Grade A was blocked by Stage 2
                    if not (self.require_stage2 and others == 3 and not stage2_ok_long):
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
                if stoch_40 > (100 - self.rot_level):
                    self.long_40_rot = True
                if stoch_60 > (100 - self.rot_level):
                    self.long_60_rot = True
                if price_pos >= 0:
                    self.long_cloud3_bars_since = 0
                else:
                    self.long_cloud3_bars_since = min(self.long_cloud3_bars_since + 1, 999)

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
                self.short_40_rot = stoch_40 < self.rot_level
                self.short_60_rot = stoch_60 < self.rot_level
                self.short_cloud3_bars_since = 0 if price_pos <= 0 else 999

        elif self.short_stage == 1:
            if bar_index - self.short_stage1_bar > self.stage_lookback:
                self.short_stage = 0
            elif stoch_9 <= cross_high:
                others = (1 if self.short_14_seen else 0) + (1 if self.short_40_seen else 0) + (1 if self.short_60_seen else 0)
                stage2_ok_short = (not self.require_stage2) or (
                    self.short_40_rot and self.short_60_rot
                    and self.short_cloud3_bars_since <= self.cloud3_window
                )
                if others == 3 and cloud3_ok_short and d_ok_short and stage2_ok_short:
                    short_signal = True
                elif others >= 2 and self.allow_b and cloud3_ok_short and d_ok_short:
                    # Don't fire Grade B if Grade A was blocked by Stage 2
                    if not (self.require_stage2 and others == 3 and not stage2_ok_short):
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
                if stoch_40 < self.rot_level:
                    self.short_40_rot = True
                if stoch_60 < self.rot_level:
                    self.short_60_rot = True
                if price_pos <= 0:
                    self.short_cloud3_bars_since = 0
                else:
                    self.short_cloud3_bars_since = min(self.short_cloud3_bars_since + 1, 999)

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
```
---
## Source: signals/four_pillars_v386.py — Current Backtester Pipeline
> This is what the backtester is configured to use.
> Uses the same state_machine.py above but passes v386 defaults.

```python
"""
Four Pillars v3.8.6 signal pipeline.

Changes from v3.8.4:
- require_stage2 default: True (was False)
  Grade A only fires when Stoch40+60 rotated during Stage 1
  AND price was at/near Cloud3 within cloud3_window bars.
  Removes low-conviction setups. Reduces ~93/day to ~40/day on 47-coin set.
- allow_c_trades default: False (was True)
  C-grade disabled -- insufficient edge vs rebate cost.

State machine (state_machine.py) unchanged -- all Stage 2 logic already present.
Economic model: volume -> rebates. Quality filter keeps account from bleeding.

Run (from backtester root):
  python -c "import py_compile; py_compile.compile('signals/four_pillars_v386.py', doraise=True); print('OK')"
"""

import numpy as np
import pandas as pd

from .stochastics import compute_all_stochastics
from .clouds import compute_clouds
from .state_machine import FourPillarsStateMachine, SignalResult


def compute_signals(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Run the full Four Pillars v3.8.6 signal pipeline on OHLCV data.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol]
        params: Strategy parameters. Defaults reflect v3.8.6 live config.

    Returns:
        DataFrame with all indicator and signal columns added.
    """
    if params is None:
        params = {}

    df = compute_all_stochastics(df, params)
    df = compute_clouds(df, params)

    # ATR (manual, matching Pine Script ta.atr(14))
    atr_len = params.get("atr_length", 14)
    tr = np.maximum(
        df["high"].values - df["low"].values,
        np.maximum(
            np.abs(df["high"].values - np.roll(df["close"].values, 1)),
            np.abs(df["low"].values - np.roll(df["close"].values, 1))
        )
    )
    tr[0] = df["high"].iloc[0] - df["low"].iloc[0]
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    df["atr"] = atr

    # v3.8.6 defaults: require_stage2=True, allow_c=False
    sm = FourPillarsStateMachine(
        cross_level=params.get("cross_level", 25),
        zone_level=params.get("zone_level", 30),
        stage_lookback=params.get("stage_lookback", 10),
        allow_b=params.get("allow_b_trades", True),
        allow_c=params.get("allow_c_trades", False),        # v386: False (was True)
        b_open_fresh=params.get("b_open_fresh", True),
        cloud2_reentry=params.get("cloud2_reentry", True),
        reentry_lookback=params.get("reentry_lookback", 10),
        use_ripster=params.get("use_ripster", False),
        use_60d=params.get("use_60d", False),
        require_stage2=params.get("require_stage2", True),  # v386: True (was False)
        rot_level=params.get("rot_level", 80),
        cloud3_window=params.get("cloud3_window", 5),
    )

    n = len(df)
    signals = {
        "long_a":       np.zeros(n, dtype=bool),
        "long_b":       np.zeros(n, dtype=bool),
        "long_c":       np.zeros(n, dtype=bool),
        "short_a":      np.zeros(n, dtype=bool),
        "short_b":      np.zeros(n, dtype=bool),
        "short_c":      np.zeros(n, dtype=bool),
        "reentry_long":  np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
    }

    stoch_9    = df["stoch_9"].values
    stoch_14   = df["stoch_14"].values
    stoch_40   = df["stoch_40"].values
    stoch_60   = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    cloud3_bull = df["cloud3_bull"].values
    price_pos   = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue

        result = sm.process_bar(
            bar_index=i,
            stoch_9=stoch_9[i],
            stoch_14=stoch_14[i],
            stoch_40=stoch_40[i],
            stoch_60=stoch_60[i],
            stoch_60_d=stoch_60_d[i],
            cloud3_bull=bool(cloud3_bull[i]),
            price_pos=int(price_pos[i]),
            price_cross_above_cloud2=bool(cross_above[i]),
            price_cross_below_cloud2=bool(cross_below[i]),
        )

        signals["long_a"][i]       = result.long_a
        signals["long_b"][i]       = result.long_b
        signals["long_c"][i]       = result.long_c
        signals["short_a"][i]      = result.short_a
        signals["short_b"][i]      = result.short_b
        signals["short_c"][i]      = result.short_c
        signals["reentry_long"][i]  = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short

    for col, arr in signals.items():
        df[col] = arr

    return df
```
---
## Source: signals/four_pillars.py — What the Live Bot Actually Runs
> This is the ORIGINAL pipeline imported by the bot plugin.
> Compare carefully with v386 above — same state_machine, different defaults.

```python
"""
Orchestrator: compute indicators → run state machine → output signal DataFrame.
"""

import numpy as np
import pandas as pd

from .stochastics import compute_all_stochastics
from .clouds import compute_clouds
from .state_machine import FourPillarsStateMachine, SignalResult


def compute_signals(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Run the full Four Pillars signal pipeline on OHLCV data.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol]
        params: Strategy parameters (defaults to v3.7.1 settings)

    Returns:
        DataFrame with all indicator and signal columns added.
    """
    if params is None:
        params = {}

    # Compute indicators (pass params through for adjustable K lengths / EMA lengths)
    df = compute_all_stochastics(df, params)
    df = compute_clouds(df, params)

    # ATR (manual, matching Pine Script ta.atr(14))
    atr_len = params.get("atr_length", 14)
    tr = np.maximum(
        df["high"].values - df["low"].values,
        np.maximum(
            np.abs(df["high"].values - np.roll(df["close"].values, 1)),
            np.abs(df["low"].values - np.roll(df["close"].values, 1))
        )
    )
    tr[0] = df["high"].iloc[0] - df["low"].iloc[0]  # First bar: just H-L
    # RMA (Wilder's smoothing) for ATR
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    df["atr"] = atr

    # Initialize state machine
    sm = FourPillarsStateMachine(
        cross_level=params.get("cross_level", 25),
        zone_level=params.get("zone_level", 30),
        stage_lookback=params.get("stage_lookback", 10),
        allow_b=params.get("allow_b_trades", True),
        allow_c=params.get("allow_c_trades", True),
        b_open_fresh=params.get("b_open_fresh", True),
        cloud2_reentry=params.get("cloud2_reentry", True),
        reentry_lookback=params.get("reentry_lookback", 10),
        use_ripster=params.get("use_ripster", False),
        use_60d=params.get("use_60d", False),
        require_stage2=params.get("require_stage2", False),
        rot_level=params.get("rot_level", 80),
        cloud3_window=params.get("cloud3_window", 5),
    )

    # Run bar-by-bar
    n = len(df)
    signals = {
        "long_a": np.zeros(n, dtype=bool),
        "long_b": np.zeros(n, dtype=bool),
        "long_c": np.zeros(n, dtype=bool),
        "short_a": np.zeros(n, dtype=bool),
        "short_b": np.zeros(n, dtype=bool),
        "short_c": np.zeros(n, dtype=bool),
        "reentry_long": np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
    }

    stoch_9 = df["stoch_9"].values
    stoch_14 = df["stoch_14"].values
    stoch_40 = df["stoch_40"].values
    stoch_60 = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    cloud3_bull = df["cloud3_bull"].values
    price_pos = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        # Skip bars where indicators aren't ready
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue

        result = sm.process_bar(
            bar_index=i,
            stoch_9=stoch_9[i],
            stoch_14=stoch_14[i],
            stoch_40=stoch_40[i],
            stoch_60=stoch_60[i],
            stoch_60_d=stoch_60_d[i],
            cloud3_bull=bool(cloud3_bull[i]),
            price_pos=int(price_pos[i]),
            price_cross_above_cloud2=bool(cross_above[i]),
            price_cross_below_cloud2=bool(cross_below[i]),
        )

        signals["long_a"][i] = result.long_a
        signals["long_b"][i] = result.long_b
        signals["long_c"][i] = result.long_c
        signals["short_a"][i] = result.short_a
        signals["short_b"][i] = result.short_b
        signals["short_c"][i] = result.short_c
        signals["reentry_long"][i] = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short

    for col, arr in signals.items():
        df[col] = arr

    return df
```
---
## Source: engine/position_v384.py — Backtester Exit Logic (AVWAP+BE)
> This is the exit mechanism the backtester uses.
> Key: AVWAP trailing after checkpoint_interval bars, optional BE raise.
> The bot does NOT use this — it uses BingX native trailing instead.

```python
"""
Position slot for v3.8.4: ATR SL + optional ATR TP, AVWAP trailing, scale-out.

v3.8.4 adds: tp_mult parameter for ATR-based take profit.
Everything else identical to v3.8.3.

SL logic (unchanged from v3.8.3):
  A/B/C/D entries: ATR-based SL (entry_price +/- ATR * sl_mult). Fixed for first N bars.
  ADD/RE entries: AVWAP 2sigma SL (inherited from parent slot). Fixed for first N bars.
  After checkpoint_interval bars: SL moves to AVWAP center, continuously ratcheted.

BE raise (cooperates with AVWAP):
  be_trigger_atr=X: when unrealized P&L exceeds X*ATR, raise SL to entry +/- be_lock_atr*ATR.
  Fires FAST on spikes (checked every bar, no checkpoint wait).
  Checked BEFORE AVWAP ratchet in update_bar() -- both cooperate:
    BE locks in on spikes, AVWAP continues trailing the trend afterward.
  be_trigger_atr=0: disabled (default).

TP logic (NEW in v3.8.4):
  tp_mult=None: no TP (same as v3.8.3 behavior)
  tp_mult=X: TP at entry_price +/- ATR * X. Closes full position.
  SL checked first (pessimistic) when both could trigger on same bar.

Scale-out (unchanged):
  At each checkpoint, if close hits AVWAP +/- 2sigma, close half.
  Max 2 scale-outs. TP takes priority over scale-out if both trigger.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from .avwap import AVWAPTracker


@dataclass
class Trade384:
    """Completed trade record for v3.8.4."""
    direction: str
    grade: str
    entry_bar: int
    exit_bar: int
    entry_price: float
    exit_price: float
    sl_price: float
    tp_price: Optional[float]
    pnl: float
    commission: float
    mfe: float
    mae: float
    exit_reason: str
    saw_green: bool
    be_raised: bool
    exit_stage: int
    entry_atr: float
    scale_idx: int = 0


class PositionSlot384:
    """One position with ATR/AVWAP SL, optional ATR TP, and scale-out."""

    def __init__(
        self,
        direction: str,
        grade: str,
        entry_bar: int,
        entry_price: float,
        atr: float,
        hlc3: float,
        volume: float,
        sigma_floor_atr: float = 0.5,
        sl_mult: float = 2.0,
        tp_mult: float = None,
        be_trigger_atr: float = 0.0,
        be_lock_atr: float = 0.0,
        notional: float = 5000.0,
        checkpoint_interval: int = 5,
        max_scaleouts: int = 2,
        avwap_state: AVWAPTracker = None,
    ):
        self.direction = direction
        self.grade = grade
        self.entry_bar = entry_bar
        self.entry_price = entry_price
        self.notional = notional
        self.original_notional = notional
        self._entry_atr = atr
        self.checkpoint_interval = checkpoint_interval
        self.max_scaleouts = max_scaleouts
        self.scale_count = 0
        self.entry_commission = 0.0

        # BE raise: fires fast on spikes, before AVWAP ratchet
        self.be_raised = False
        self.be_trigger_atr = be_trigger_atr
        self.be_lock_atr = be_lock_atr
        if be_trigger_atr > 0:
            if direction == "LONG":
                self._be_trigger_price = entry_price + atr * be_trigger_atr
                self._be_lock_sl = entry_price + atr * be_lock_atr
            else:
                self._be_trigger_price = entry_price - atr * be_trigger_atr
                self._be_lock_sl = entry_price - atr * be_lock_atr
        else:
            self._be_trigger_price = None
            self._be_lock_sl = None

        # AVWAP: inherit from parent (ADD/RE) or start fresh (A/B/C/D)
        if avwap_state is not None:
            self.avwap = avwap_state.clone()
        else:
            self.avwap = AVWAPTracker(sigma_floor_atr)
        self.avwap.update(hlc3, volume, atr)

        # SL initialization
        self.sl_phase = "initial"
        if grade in ("A", "B", "C", "D"):
            if direction == "LONG":
                self.sl = entry_price - (atr * sl_mult)
            else:
                self.sl = entry_price + (atr * sl_mult)
        else:
            c, s = self.avwap.center, self.avwap.sigma
            if direction == "LONG":
                self.sl = c - 2 * s
            else:
                self.sl = c + 2 * s

        # TP initialization (None = no TP, same as v3.8.3)
        self.tp = None
        if tp_mult is not None:
            if direction == "LONG":
                self.tp = entry_price + (atr * tp_mult)
            else:
                self.tp = entry_price - (atr * tp_mult)

        # MFE/MAE
        self.mfe = 0.0
        self.mae = 0.0
        self.saw_green = False

    def check_exit(self, high: float, low: float) -> Optional[str]:
        """Check if SL or TP hit. SL first (pessimistic). Called BEFORE update_bar."""
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

    def update_bar(
        self,
        bar_index: int,
        high: float,
        low: float,
        close: float,
        atr: float,
        hlc3: float,
        volume: float,
    ):
        """Update AVWAP, SL, MFE/MAE. Called AFTER check_exit."""
        self.avwap.update(hlc3, volume, atr)
        bars_held = bar_index - self.entry_bar

        # BE raise: check BEFORE AVWAP ratchet. Fires fast on spikes.
        if not self.be_raised and self._be_trigger_price is not None:
            triggered = (self.direction == "LONG" and high >= self._be_trigger_price) or \
                        (self.direction == "SHORT" and low <= self._be_trigger_price)
            if triggered:
                self.be_raised = True
                if self.direction == "LONG" and self._be_lock_sl > self.sl:
                    self.sl = self._be_lock_sl
                elif self.direction == "SHORT" and self._be_lock_sl < self.sl:
                    self.sl = self._be_lock_sl

        if bars_held >= self.checkpoint_interval and self.sl_phase == "initial":
            self.sl_phase = "avwap"
            target_sl = self.avwap.center
            if self.direction == "LONG" and target_sl > self.sl:
                self.sl = target_sl
            elif self.direction == "SHORT" and target_sl < self.sl:
                self.sl = target_sl

        if self.sl_phase == "avwap":
            target_sl = self.avwap.center
            if self.direction == "LONG" and target_sl > self.sl:
                self.sl = target_sl
            elif self.direction == "SHORT" and target_sl < self.sl:
                self.sl = target_sl

        # MFE/MAE
        if self.direction == "LONG":
            ub = (high - self.entry_price) / self.entry_price * self.original_notional
            uw = (low - self.entry_price) / self.entry_price * self.original_notional
        else:
            ub = (self.entry_price - low) / self.entry_price * self.original_notional
            uw = (self.entry_price - high) / self.entry_price * self.original_notional
        self.mfe = max(self.mfe, ub)
        self.mae = min(self.mae, uw)
        if ub > 0:
            self.saw_green = True

    def check_scale_out(self, bar_index: int, close: float) -> bool:
        """Check if at a checkpoint and close hits +/-2sigma in trade direction."""
        if self.scale_count >= self.max_scaleouts:
            return False
        bars_held = bar_index - self.entry_bar
        if bars_held < self.checkpoint_interval:
            return False
        if (bars_held % self.checkpoint_interval) != 0:
            return False

        c = self.avwap.center
        s = self.avwap.sigma
        if self.direction == "LONG":
            return close >= c + 2 * s
        else:
            return close <= c - 2 * s

    def do_scale_out(self, bar_index: int, close: float, exit_commission: float) -> Tuple[Trade384, bool]:
        """Execute scale-out. Returns (Trade384, is_fully_closed)."""
        self.scale_count += 1
        is_final = (self.scale_count >= self.max_scaleouts)

        if is_final:
            close_notional = self.notional
        else:
            close_notional = self.notional / 2

        if self.direction == "LONG":
            pnl = (close - self.entry_price) / self.entry_price * close_notional
        else:
            pnl = (self.entry_price - close) / self.entry_price * close_notional

        self.notional -= close_notional

        target_sl = self.avwap.center
        if self.direction == "LONG" and target_sl > self.sl:
            self.sl = target_sl
        elif self.direction == "SHORT" and target_sl < self.sl:
            self.sl = target_sl

        trade = Trade384(
            direction=self.direction,
            grade=self.grade,
            entry_bar=self.entry_bar,
            exit_bar=bar_index,
            entry_price=self.entry_price,
            exit_price=close,
            sl_price=self.sl,
            tp_price=self.tp,
            pnl=pnl,
            commission=exit_commission,
            mfe=self.mfe,
            mae=self.mae,
            exit_reason=f"SCALE_{self.scale_count}",
            saw_green=self.saw_green,
            be_raised=self.be_raised,
            exit_stage=0,
            entry_atr=self._entry_atr,
            scale_idx=self.scale_count,
        )
        return trade, is_final

    def close_at(self, price: float, bar_index: int, reason: str, commission: float) -> Trade384:
        """Close remaining position and return Trade384 record."""
        if self.direction == "LONG":
            pnl = (price - self.entry_price) / self.entry_price * self.notional
        else:
            pnl = (self.entry_price - price) / self.entry_price * self.notional

        return Trade384(
            direction=self.direction,
            grade=self.grade,
            entry_bar=self.entry_bar,
            exit_bar=bar_index,
            entry_price=self.entry_price,
            exit_price=price,
            sl_price=self.sl,
            tp_price=self.tp,
            pnl=pnl,
            commission=commission,
            mfe=self.mfe,
            mae=self.mae,
            exit_reason=reason,
            saw_green=self.saw_green,
            be_raised=self.be_raised,
            exit_stage=0,
            entry_atr=self._entry_atr,
            scale_idx=0,
        )
```
---
## Source: engine/exit_manager.py — Dynamic SL/TP Methods
> ExitManager with 4 risk methods: be_only, be_plus_fees, be_plus_fees_trail_tp, be_trail_tp.
> Status: EXISTS but check whether backtester_v384 actually calls it.
> position_v384.py has its own inline BE+AVWAP logic — ExitManager may be unused.

```python
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
```
---
## Source: bingx-connector/plugins/four_pillars_v384.py — Live Bot Plugin
> This is what the bot executes on every 5m candle close.
> Line 21: imports from signals.four_pillars (v1 — NOT v386).
> Exit is handled by BingX exchange via SL order + native trailing stop order.
> No AVWAP, no BE raise — those are backtester-only features.

```python
"""
Four Pillars v3.8.4 strategy plugin for BingX connector.
Runs the same compute_signals() used by the dashboard on live OHLCV bars.
A/B/C entry signals with fixed ATR-based SL and optional TP.
Loaded by StrategyAdapter when config.yaml: strategy.plugin = "four_pillars_v384"
"""
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Add backtester root — same signal code the dashboard uses
_BACKTESTER = (
    Path(__file__).resolve().parent.parent.parent / "four-pillars-backtester"
)
if str(_BACKTESTER) not in sys.path:
    sys.path.insert(0, str(_BACKTESTER))

from signals.four_pillars import compute_signals
from plugins.mock_strategy import Signal

logger = logging.getLogger(__name__)


class FourPillarsV384:
    """Four Pillars strategy plugin — A/B/C entries, fixed ATR SL/TP."""

    def __init__(self, config=None):
        """Read four_pillars sub-block from config; set sl/tp multipliers."""
        cfg = (config or {}).get("four_pillars", {})
        self.allow_a = cfg.get("allow_a", True)
        self.allow_b = cfg.get("allow_b", True)
        self.allow_c = cfg.get("allow_c", False)
        self.sl_mult = float(cfg.get("sl_atr_mult", 2.0))
        tp_raw = cfg.get("tp_atr_mult", None)
        self.tp_mult = float(tp_raw) if tp_raw is not None else None
        self._params = {
            "atr_length":     cfg.get("atr_length", 14),
            "cross_level":    cfg.get("cross_level", 25),
            "zone_level":     cfg.get("zone_level", 30),
            "allow_b_trades": self.allow_b,
            "allow_c_trades": self.allow_c,
            "require_stage2": cfg.get("require_stage2", False),
            "rot_level":      cfg.get("rot_level", 80),
        }
        logger.info(
            "FourPillarsV384: allow_a=%s allow_b=%s allow_c=%s "
            "sl=%.1f tp=%s stage2=%s rot=%d backtester=%s",
            self.allow_a, self.allow_b, self.allow_c,
            self.sl_mult, str(self.tp_mult),
            cfg.get("require_stage2", False), cfg.get("rot_level", 80),
            str(_BACKTESTER),
        )

    def get_signal(self, ohlcv_df: pd.DataFrame) -> Optional[Signal]:
        """Run compute_signals on live bars; return Signal from last closed bar or None."""
        if ohlcv_df is None or len(ohlcv_df) < 2:
            return None
        try:
            df = ohlcv_df.copy()
            # Normalize: MarketDataFeed uses 'time' and 'volume'
            # compute_signals expects 'timestamp' and 'base_vol'
            df = df.rename(columns={"time": "timestamp", "volume": "base_vol"})
            if "quote_vol" not in df.columns:
                df["quote_vol"] = 0.0
            df = compute_signals(df, self._params)
        except Exception as e:
            logger.error("compute_signals failed: %s", e)
            return None

        # Last CLOSED bar is iloc[-2] — last row is the current open bar
        row = df.iloc[-2]
        atr = row.get("atr", float("nan"))
        if pd.isna(atr) or atr <= 0:
            return None

        entry = float(row["close"])
        bar_ts = int(row.get("timestamp", 0))

        # Priority: A > B > C, LONG before SHORT on same bar
        checks = []
        if self.allow_a:
            checks.append(("LONG", "A", "long_a"))
        if self.allow_b:
            checks.append(("LONG", "B", "long_b"))
        if self.allow_c:
            checks.append(("LONG", "C", "long_c"))
        if self.allow_a:
            checks.append(("SHORT", "A", "short_a"))
        if self.allow_b:
            checks.append(("SHORT", "B", "short_b"))
        if self.allow_c:
            checks.append(("SHORT", "C", "short_c"))

        for direction, grade, col in checks:
            if bool(row.get(col, False)):
                sig = self._make_signal(direction, grade, entry, atr, bar_ts)
                logger.info(
                    "Signal: %s-%s entry=%.6f sl=%.6f tp=%s atr=%.6f",
                    direction, grade, entry,
                    sig.sl_price,
                    "%.6f" % sig.tp_price if sig.tp_price else "None",
                    atr,
                )
                return sig
        return None

    def _make_signal(
        self, direction: str, grade: str,
        entry: float, atr: float, bar_ts: int
    ) -> Signal:
        """Construct Signal with ATR-based SL and optional fixed TP."""
        if direction == "LONG":
            sl = entry - self.sl_mult * atr
            tp = (entry + self.tp_mult * atr) if self.tp_mult is not None else None
        else:
            sl = entry + self.sl_mult * atr
            tp = (entry - self.tp_mult * atr) if self.tp_mult is not None else None
        return Signal(
            direction=direction,
            grade=grade,
            entry_price=entry,
            sl_price=sl,
            tp_price=tp,
            atr=atr,
            bar_ts=bar_ts,
        )

    def get_name(self) -> str:
        """Return human-readable plugin name."""
        return "FourPillarsV384"

    def get_version(self) -> str:
        """Return strategy version string."""
        return "3.8.4"

    def warmup_bars(self) -> int:
        """Return minimum bars needed before first valid signal."""
        return 200

    def get_allowed_grades(self) -> list:
        """Return list of grade strings this plugin may emit."""
        grades = []
        if self.allow_a:
            grades.append("A")
        if self.allow_b:
            grades.append("B")
        if self.allow_c:
            grades.append("C")
        return grades
```
---
## Source: bingx-connector/config.yaml — Live Bot Configuration
> These are the actual values running on the live bot right now.
> Note: require_stage2=true and rot_level=80 are set here, which overrides
> the v1 default of require_stage2=False.

```yaml
connector:
  poll_interval_sec: 45    # was 30, bumped for 53 coins (~25s to poll all)
  position_check_sec: 60
  timeframe: "5m"
  ohlcv_buffer_bars: 201
  demo_mode: false

coins:
  # 47 coins: 14 high-Exp originals + 33 low-DD additions from v384 sweep
  # Removed: 1000TOSHI, XCN, MON, DODO, ES, 1000000MOG (not on BingX perps 2026-02-25)
  # All filtered: Trades >= 400, PF >= 1.03, DD <= 30%, Exp > 0
  # Verify against BingX before starting: python scripts/verify_coins.py
  # --- Original high-Exp picks ---
  - "SKR-USDT"
  - "TRUTH-USDT"
  - "RIVER-USDT"
  - "STBL-USDT"
  - "ZKP-USDT"
  - "LYN-USDT"
  - "BEAT-USDT"
  - "GIGGLE-USDT"
  - "PIPPIN-USDT"
  - "FOLKS-USDT"
  - "NAORIS-USDT"
  - "Q-USDT"
  - "ELSA-USDT"
  - "UB-USDT"
  # --- Low-DD additions (sorted by DD% ascending) ---
  - "THETA-USDT"       # DD: 0.8% | PF: 1.17 | Exp: 1.24
  - "SAHARA-USDT"      # DD: 0.9% | PF: 1.32 | Exp: 1.74
  - "TIA-USDT"         # DD: 0.9% | PF: 1.11 | Exp: 1.09
  - "APT-USDT"         # DD: 1.0% | PF: 1.17 | Exp: 1.29
  - "AIXBT-USDT"       # DD: 1.1% | PF: 1.05 | Exp: 0.93
  - "GALA-USDT"        # DD: 1.1% | PF: 1.04 | Exp: 0.84
  - "LDO-USDT"         # DD: 1.1% | PF: 1.07 | Exp: 0.96
  - "SUSHI-USDT"       # DD: 1.1% | PF: 1.16 | Exp: 1.20
  - "VET-USDT"         # DD: 1.1% | PF: 1.08 | Exp: 0.96
  - "WAL-USDT"         # DD: 1.1% | PF: 1.04 | Exp: 0.84
  - "WIF-USDT"         # DD: 1.1% | PF: 1.11 | Exp: 1.09
  - "WOO-USDT"         # DD: 1.1% | PF: 1.11 | Exp: 1.04

  - "ATOM-USDT"        # DD: 1.2% | PF: 1.12 | Exp: 1.06
  - "BOME-USDT"        # DD: 1.2% | PF: 1.17 | Exp: 1.39
  - "DYDX-USDT"        # DD: 1.3% | PF: 1.08 | Exp: 0.98
  - "VIRTUAL-USDT"     # DD: 1.3% | PF: 1.09 | Exp: 1.10
  - "BREV-USDT"        # DD: 1.4% | PF: 1.11 | Exp: 1.24
  - "CYBER-USDT"       # DD: 1.4% | PF: 1.24 | Exp: 1.61
  - "EIGEN-USDT"       # DD: 1.4% | PF: 1.11 | Exp: 1.11
  - "MUBARAK-USDT"     # DD: 1.4% | PF: 1.15 | Exp: 1.25
  - "1000PEPE-USDT"    # DD: 1.5% | PF: 1.08 | Exp: 0.99
  - "DEEP-USDT"        # DD: 1.5% | PF: 1.09 | Exp: 1.08
  - "ETHFI-USDT"       # DD: 1.5% | PF: 1.05 | Exp: 0.92
  - "RENDER-USDT"      # DD: 1.5% | PF: 1.21 | Exp: 1.52
  - "BB-USDT"          # DD: 1.6% | PF: 1.03 | Exp: 0.83
  - "F-USDT"           # DD: 1.6% | PF: 1.13 | Exp: 1.30
  - "GUN-USDT"         # DD: 1.6% | PF: 1.20 | Exp: 1.64
  - "KAITO-USDT"       # DD: 1.6% | PF: 1.11 | Exp: 1.13
  - "MEME-USDT"        # DD: 1.6% | PF: 1.14 | Exp: 1.20
  - "PENDLE-USDT"      # DD: 1.7% | PF: 1.03 | Exp: 0.86
  - "SCRT-USDT"        # DD: 1.7% | PF: 1.20 | Exp: 1.68
  - "SQD-USDT"         # DD: 1.7% | PF: 1.07 | Exp: 0.93
  - "STX-USDT"         # DD: 1.8% | PF: 1.12 | Exp: 1.12

strategy:
  plugin: "four_pillars_v384"

four_pillars:
  allow_a: true
  allow_b: true
  allow_c: false
  sl_atr_mult: 2.0
  tp_atr_mult: null      # no fixed TP — SL at 2x ATR, let winners run
  require_stage2: true   # Stoch40+60 must rotate before Grade A fires
  rot_level: 80

risk:
  max_positions: 8        # $110 account, 8 * $5 margin = $40 max margin used
  max_daily_trades: 50
  daily_loss_limit_usd: 15.0   # ~14% of $110 account
  min_atr_ratio: 0.003
  cooldown_bars: 3        # bars to wait before re-entering same symbol+direction
  bar_duration_sec: 300   # 5m = 300s

position:
  margin_usd: 5.0
  leverage: 10
  margin_mode: "ISOLATED"
  sl_working_type: "MARK_PRICE"
  tp_working_type: "MARK_PRICE"
  trailing_activation_atr_mult: 2.0   # activate trail when price reaches entry +/- 2xATR
  trailing_rate: 0.02                  # 2% callback from peak once activation hit

notification:
  daily_summary_utc_hour: 17
```
---
## Source: signals/bbwp.py — BBW Signal (Orphaned)
> This file computes 10 BBW/BBWP columns from close price.
> Output includes: bbwp_value (percentile rank of BB width),
> bbwp_spectrum (LOW/NORMAL/HIGH/EXTREME), bbwp_state (BLUE/RED/etc).
> NOT connected to any signal pipeline or backtester.
> For Vince to see BBW context at trade entry, this must be called inside
> compute_signals() before the state machine runs.

```python
"""
Layer 1: BBWP Calculator — Port of bbwp_v2.pine to Python.

Pure function. No side effects, no print(), no file I/O.
Input: DataFrame with columns: open, high, low, close, base_vol
Output: Same DataFrame with 10 new bbwp_ columns added.

Pine Script source of truth: 02-STRATEGY/Indicators/bbwp_v2.pine (264 lines, Pine v6)
"""

import warnings

import numpy as np
import pandas as pd

# ─── Default Parameters (matching Pine v2 inputs) ────────────────────────────

DEFAULT_PARAMS = {
    'basis_len': 13,
    'basis_type': 'SMA',
    'lookback': 100,
    'bbwp_ma_len': 5,
    'bbwp_ma_type': 'SMA',
    'extreme_low': 10,
    'extreme_high': 90,
    'spectrum_low': 25,
    'spectrum_high': 75,
    'ma_cross_timeout': 10,
}

# ─── State-to-Points mapping (Pine v2 lines 149-169) ─────────────────────────

STATE_POINTS = {
    'BLUE_DOUBLE': 2,
    'BLUE': 1,
    'RED_DOUBLE': 1,
    'RED': 1,
    'MA_CROSS_UP': 1,
    'MA_CROSS_DOWN': 0,
    'NORMAL': 0,
}

# ─── Required input columns ──────────────────────────────────────────────────

REQUIRED_COLS = ['close']

# ─── Output columns (10 total) ───────────────────────────────────────────────

OUTPUT_COLS = [
    'bbwp_value', 'bbwp_ma', 'bbwp_bbw_raw', 'bbwp_spectrum',
    'bbwp_state', 'bbwp_points', 'bbwp_is_blue_bar', 'bbwp_is_red_bar',
    'bbwp_ma_cross_up', 'bbwp_ma_cross_down',
]


def _apply_ma(series: pd.Series, length: int, ma_type: str) -> pd.Series:
    """Apply moving average of specified type to a series."""
    if ma_type == 'EMA':
        return series.ewm(span=length, adjust=False).mean()
    elif ma_type == 'WMA':
        weights = np.arange(1, length + 1, dtype=float)
        return series.rolling(length).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    elif ma_type == 'RMA':
        return series.ewm(alpha=1.0 / length, adjust=False).mean()
    elif ma_type == 'HMA':
        half_len = max(int(length / 2), 1)
        sqrt_len = max(int(np.sqrt(length)), 1)
        wma_half = _apply_ma(series, half_len, 'WMA')
        wma_full = _apply_ma(series, length, 'WMA')
        diff = 2 * wma_half - wma_full
        return _apply_ma(diff, sqrt_len, 'WMA')
    elif ma_type == 'VWMA':
        # Fallback to SMA if no volume context available
        warnings.warn("VWMA requested but no volume data available, falling back to SMA", stacklevel=2)
        return series.rolling(length).mean()
    else:
        # SMA (default)
        return series.rolling(length).mean()


def _percentrank_pine(bbw: pd.Series, lookback: int) -> pd.Series:
    """Match Pine's ta.percentrank with NaN-tolerant window (min lookback//2 valid)."""
    values = bbw.values
    n = len(values)
    result = np.full(n, np.nan)
    min_valid = max(lookback // 2, 1)

    for i in range(lookback, n):
        if np.isnan(values[i]):
            continue
        # Previous lookback values (NOT including current bar)
        prev_window = values[i - lookback:i]
        valid_mask = ~np.isnan(prev_window)
        valid_count = valid_mask.sum()
        if valid_count < min_valid:
            continue
        current = values[i]
        count_below = np.sum(prev_window[valid_mask] < current)
        result[i] = (count_below / valid_count) * 100

    return pd.Series(result, index=bbw.index)


def _spectrum_color(bbwp_val: float):
    """Map BBWP value to 4-zone spectrum color (Pine gradient inflection at 25/50/75)."""
    if np.isnan(bbwp_val):
        return None
    if bbwp_val <= 25:
        return 'blue'
    elif bbwp_val <= 50:
        return 'green'
    elif bbwp_val <= 75:
        return 'yellow'
    else:
        return 'red'


def _detect_states(bbwp_values: np.ndarray, bbwp_ma_values: np.ndarray,
                   params: dict) -> tuple:
    """Detect BBWP states using stateful MA cross persistence.

    Must iterate bar-by-bar because MA cross state persists across bars
    (Pine v2 uses `var` variables). Returns arrays for state, points,
    cross_up events, cross_down events.

    Pine v2 reference: lines 100-169.
    """
    n = len(bbwp_values)
    states = np.empty(n, dtype=object)
    points = np.zeros(n, dtype=np.int64)
    cross_up_events = np.zeros(n, dtype=bool)
    cross_down_events = np.zeros(n, dtype=bool)

    extreme_low = params['extreme_low']
    extreme_high = params['extreme_high']
    spectrum_low = params['spectrum_low']
    spectrum_high = params['spectrum_high']
    ma_cross_timeout = params['ma_cross_timeout']

    # Persistent state variables (Pine `var`)
    show_ma_cross_up = False
    show_ma_cross_down = False
    ma_cross_bar = -1  # -1 means na (no active cross)

    for i in range(n):
        bbwp = bbwp_values[i]
        bbwp_ma = bbwp_ma_values[i]

        # Handle NaN bbwp — default to NORMAL, 0 points
        if np.isnan(bbwp):
            states[i] = 'NORMAL'
            points[i] = 0
            continue

        # MA may still be NaN during warmup gap (bars with valid bbwp but NaN MA)
        ma_is_nan = np.isnan(bbwp_ma)

        # Bar conditions (Pine lines 104-105)
        blu_bar = bbwp <= extreme_low   # <=, not <
        red_bar = bbwp >= extreme_high  # >=, not >

        # Spectrum conditions (Pine lines 108-109)
        blu_spectrum = bbwp < spectrum_low   # <, strict
        red_spectrum = bbwp > spectrum_high  # >, strict

        # MA cross conditions — only fire in normal range (Pine lines 112-114)
        in_normal_range = (not blu_spectrum) and (not red_spectrum)

        # Crossover/crossunder detection (compare current vs previous bar)
        ma_cross_up_event = False
        ma_cross_down_event = False
        if i > 0 and in_normal_range and not ma_is_nan:
            prev_bbwp = bbwp_values[i - 1]
            prev_ma = bbwp_ma_values[i - 1]
            if not (np.isnan(prev_bbwp) or np.isnan(prev_ma)):
                # Pine ta.crossover: current > MA AND previous <= MA
                if bbwp > bbwp_ma and prev_bbwp <= prev_ma:
                    ma_cross_up_event = True
                # Pine ta.crossunder: current < MA AND previous >= MA
                if bbwp < bbwp_ma and prev_bbwp >= prev_ma:
                    ma_cross_down_event = True

        cross_up_events[i] = ma_cross_up_event
        cross_down_events[i] = ma_cross_down_event

        # Check timeout (Pine line 123)
        ma_cross_timed_out = False
        if ma_cross_bar >= 0:
            if (i - ma_cross_bar) >= ma_cross_timeout:
                ma_cross_timed_out = True

        # Update persistent state (Pine lines 125-140)
        if ma_cross_up_event:
            show_ma_cross_up = True
            show_ma_cross_down = False
            ma_cross_bar = i
        elif ma_cross_down_event:
            show_ma_cross_down = True
            show_ma_cross_up = False
            ma_cross_bar = i
        elif blu_spectrum or red_spectrum or ma_cross_timed_out:
            show_ma_cross_up = False
            show_ma_cross_down = False
            ma_cross_bar = -1

        # State determination — priority order (Pine lines 149-169)
        if blu_bar and blu_spectrum:
            states[i] = 'BLUE_DOUBLE'
            points[i] = 2
        elif blu_spectrum:
            states[i] = 'BLUE'
            points[i] = 1
        elif red_bar and red_spectrum:
            states[i] = 'RED_DOUBLE'
            points[i] = 1
        elif red_spectrum:
            states[i] = 'RED'
            points[i] = 1
        elif show_ma_cross_up:
            states[i] = 'MA_CROSS_UP'
            points[i] = 1
        elif show_ma_cross_down:
            states[i] = 'MA_CROSS_DOWN'
            points[i] = 0
        else:
            states[i] = 'NORMAL'
            points[i] = 0

    return states, points, cross_up_events, cross_down_events


def calculate_bbwp(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Port of bbwp_v2.pine to Python.

    Input: DataFrame with columns: open, high, low, close, base_vol
    Output: Same DataFrame with 10 new bbwp_ columns added.

    This is a PURE FUNCTION -- no side effects, no file I/O.
    """
    # Merge user params with defaults
    p = {**DEFAULT_PARAMS}
    if params:
        p.update(params)

    # Validate required columns
    for col in REQUIRED_COLS:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Work on a copy to avoid mutating input
    result = df.copy()
    close = result['close'].astype(float)

    # ── Step 1: BB Width (Pine lines 89-91) ───────────────────────────────
    basis = _apply_ma(close, p['basis_len'], p['basis_type'])
    stdev = close.rolling(p['basis_len']).std(ddof=0)
    bbw = np.where(basis > 0, (2 * stdev) / basis, 0.0)
    bbw = pd.Series(bbw, index=close.index)
    # Propagate NaN from basis warmup
    bbw[basis.isna()] = np.nan

    result['bbwp_bbw_raw'] = bbw

    # ── Step 2: BBWP percentile rank (Pine line 94) ──────────────────────
    bbwp = _percentrank_pine(bbw, p['lookback'])
    result['bbwp_value'] = bbwp

    # ── Step 3: BBWP MA (Pine line 97) ───────────────────────────────────
    bbwp_ma = _apply_ma(bbwp, p['bbwp_ma_len'], p['bbwp_ma_type'])
    result['bbwp_ma'] = bbwp_ma

    # ── Step 4: Spectrum color (vectorized) ──────────────────────────────
    result['bbwp_spectrum'] = bbwp.apply(_spectrum_color)

    # ── Step 5: Bar conditions (vectorized, Pine lines 104-105) ──────────
    result['bbwp_is_blue_bar'] = bbwp <= p['extreme_low']
    result['bbwp_is_red_bar'] = bbwp >= p['extreme_high']
    # NaN comparisons already produce False — no explicit override needed

    # ── Step 6: State detection (loop — stateful) ────────────────────────
    bbwp_arr = bbwp.values.astype(float)
    bbwp_ma_arr = bbwp_ma.values.astype(float)

    states, pts, cross_up, cross_down = _detect_states(
        bbwp_arr, bbwp_ma_arr, p
    )

    result['bbwp_state'] = states
    result['bbwp_points'] = pts
    result['bbwp_ma_cross_up'] = cross_up
    result['bbwp_ma_cross_down'] = cross_down

    return result
```
---
## Version History — Docstrings Only
> What each version said it changed, in its own words.

### v3.8.2
```
"""
Signal pipeline for v3.8.2. Uses FourPillarsStateMachine382 (A-signal fix).
Everything else identical to signals/four_pillars.py.
"""
```
### v3.8.3
```
"""
Signal pipeline for v3.8.3. Uses FourPillarsStateMachine383.
Adds D signal (continuation while 60-K pinned).
"""
```
### v3.8.3-v2 (Numba)
```
"""
Signal pipeline for v3.8.3 — v2: uses Numba-compiled stochastics/clouds/ATR.
Imports stochastics_v2 and clouds_v2; extracts _rma_kernel via @njit.
"""
```
### v3.8.6 / v386
```
"""
Four Pillars v3.8.6 signal pipeline.

Changes from v3.8.4:
- require_stage2 default: True (was False)
  Grade A only fires when Stoch40+60 rotated during Stage 1
  AND price was at/near Cloud3 within cloud3_window bars.
  Removes low-conviction setups. Reduces ~93/day to ~40/day on 47-coin set.
- allow_c_trades default: False (was True)
  C-grade disabled -- insufficient edge vs rebate cost.

State machine (state_machine.py) unchanged -- all Stage 2 logic already present.
Economic model: volume -> rebates. Quality filter keeps account from bleeding.

Run (from backtester root):
  python -c "import py_compile; py_compile.compile('signals/four_pillars_v386.py', doraise=True); print('OK')"
"""
```
---
## Questions for Claude Web Discussion
- 1. The state machine uses rot_level=80, which means stoch_40 > 20 for longs. Is this a meaningful filter at all? What would rot_level need to be to enforce 'stoch_40 was in bullish territory before the oversold setup'?

- 2. The backtester uses AVWAP trailing (SL moves to AVWAP center after N bars). The live bot uses BingX native trailing (2% callback from peak at 2x ATR activation). How much divergence should we expect in exit prices? Which is more aligned with the strategy intent?

- 3. v386 was written but the bot still imports v1. The bot overrides require_stage2 and rot_level via config, so signal logic is approximately the same. But are there any code-level differences between signals/four_pillars.py and v386 that matter?

- 4. BBW (Bollinger Band Width Percentile) is computed in bbwp.py but never wired in. If we wire it into compute_signals(), what would Vince actually see? Is BBWP the right context variable for understanding why trades win or lose?

- 5. ExitManager exists with 4 risk methods but position_v384.py has its own inline BE+AVWAP logic. Is ExitManager actually called anywhere, or is it dead code?

- 6. Grade C fires when: stoch_14 was seen in zone AND price_pos == +1 (LONG) or -1 (SHORT). With allow_c_trades=False, Grade C is disabled. Was the original C-grade intent different from this implementation?

---
*End of report. Generated by scripts/build_strategy_analysis.py*
