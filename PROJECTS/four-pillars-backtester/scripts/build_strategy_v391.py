"""
Build script for Four Pillars v3.9.1 strategy.
Creates 4 files: clouds_v391.py, four_pillars_v391.py, position_v391.py, backtester_v391.py
Run: python scripts/build_strategy_v391.py
"""
import sys
import py_compile
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIGNALS_DIR = ROOT / "signals"
ENGINE_DIR  = ROOT / "engine"

ERRORS = []


def verify(path: Path) -> bool:
    """Syntax-check and AST-parse a .py file; return True if clean."""
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        return False
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
    except SyntaxError as e:
        print("  AST ERROR in " + str(path) + " line " + str(e.lineno) + ": " + str(e.msg))
        return False
    print("  OK: " + str(path))
    return True


def write_file(path: Path, content: str) -> bool:
    """Write content to path if it does not exist; return True on success."""
    if path.exists():
        print("  SKIP (already exists): " + str(path))
        return False
    path.write_text(content, encoding="utf-8")
    print("  WROTE: " + str(path))
    return True


# ─── File 1: signals/clouds_v391.py ──────────────────────────────────────────

CLOUDS_V391 = '''\
"""
Ripster EMA Cloud calculations v391.

Extends clouds.py with EMA cross-detection columns required by the
3-phase SL movement system and Cloud 2 hard-close exit logic.

New columns vs clouds.py:
  cloud2_cross_bull  - True on the bar EMA5 crosses above EMA12 (one bar only)
  cloud2_cross_bear  - True on the bar EMA5 crosses below EMA12
  cloud3_cross_bull  - True on the bar EMA34 crosses above EMA50
  cloud3_cross_bear  - True on the bar EMA34 crosses below EMA50
  cloud4_bull        - EMA72 > EMA89 (already in clouds.py, kept for clarity)
  phase3_active_long - cloud3_bull AND cloud4_bull (Phase 3 trail trigger for longs)
  phase3_active_short- cloud3_bear AND cloud4_bear (Phase 3 trail trigger for shorts)
"""

import numpy as np
import pandas as pd


def ema(series: np.ndarray, length: int) -> np.ndarray:
    """Exponential Moving Average matching Pine Script ta.ema()."""
    result = np.full(len(series), np.nan)
    if len(series) < length:
        return result
    result[length - 1] = np.mean(series[:length])
    mult = 2.0 / (length + 1)
    for i in range(length, len(series)):
        result[i] = series[i] * mult + result[i - 1] * (1 - mult)
    return result


def compute_clouds_v391(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Compute Ripster EMA Clouds with full cross-detection for v391.

    Returns df with all original cloud columns plus:
      cloud2_cross_bull, cloud2_cross_bear,
      cloud3_cross_bull, cloud3_cross_bear,
      phase3_active_long, phase3_active_short
    """
    p = params or {}
    c2_fast = p.get("cloud2_fast", 5)
    c2_slow = p.get("cloud2_slow", 12)
    c3_fast = p.get("cloud3_fast", 34)
    c3_slow = p.get("cloud3_slow", 50)
    c4_fast = p.get("cloud4_fast", 72)
    c4_slow = p.get("cloud4_slow", 89)

    close = df["close"].values
    df = df.copy()

    # Cloud 2 (EMA 5/12)
    ema5  = ema(close, c2_fast)
    ema12 = ema(close, c2_slow)
    df["ema5"]         = ema5
    df["ema12"]        = ema12
    df["cloud2_bull"]  = ema5 > ema12
    df["cloud2_bear"]  = ema5 < ema12
    df["cloud2_top"]   = np.maximum(ema5, ema12)
    df["cloud2_bottom"]= np.minimum(ema5, ema12)

    # Cloud 3 (EMA 34/50)
    ema34 = ema(close, c3_fast)
    ema50 = ema(close, c3_slow)
    df["ema34"]        = ema34
    df["ema50"]        = ema50
    df["cloud3_bull"]  = ema34 > ema50
    df["cloud3_bear"]  = ema34 < ema50
    df["cloud3_top"]   = np.maximum(ema34, ema50)
    df["cloud3_bottom"]= np.minimum(ema34, ema50)

    # Cloud 4 (EMA 72/89)
    ema72 = ema(close, c4_fast)
    ema89 = ema(close, c4_slow)
    df["ema72"]        = ema72
    df["ema89"]        = ema89
    df["cloud4_bull"]  = ema72 > ema89
    df["cloud4_bear"]  = ema72 < ema89

    # Price position relative to Cloud 3
    df["price_pos"] = np.where(
        close > df["cloud3_top"].values,  1,
        np.where(close < df["cloud3_bottom"].values, -1, 0)
    )
    df["cloud3_allows_long"]  = df["price_pos"] >= 0
    df["cloud3_allows_short"] = df["price_pos"] <= 0

    # Price cross over Cloud 2 (for re-entry signals — unchanged from v390)
    df["price_cross_above_cloud2"] = (close > df["cloud2_top"].values) & (
        np.roll(close, 1) <= np.roll(df["cloud2_top"].values, 1)
    )
    df["price_cross_below_cloud2"] = (close < df["cloud2_bottom"].values) & (
        np.roll(close, 1) >= np.roll(df["cloud2_bottom"].values, 1)
    )
    df.iloc[0, df.columns.get_loc("price_cross_above_cloud2")] = False
    df.iloc[0, df.columns.get_loc("price_cross_below_cloud2")] = False

    # EMA cross-detection: True only on the bar the cross occurs
    c2_bull = df["cloud2_bull"].values.astype(bool)
    c3_bull = df["cloud3_bull"].values.astype(bool)
    c4_bull = df["cloud4_bull"].values.astype(bool)

    c2_bull_prev = np.roll(c2_bull, 1)
    c3_bull_prev = np.roll(c3_bull, 1)

    # cloud2_cross_bull: EMA5 crosses above EMA12
    cloud2_cross_bull  = c2_bull & ~c2_bull_prev
    cloud2_cross_bear  = ~c2_bull & c2_bull_prev
    # cloud3_cross_bull: EMA34 crosses above EMA50
    cloud3_cross_bull  = c3_bull & ~c3_bull_prev
    cloud3_cross_bear  = ~c3_bull & c3_bull_prev

    # Fix bar 0 (roll wraps last bar onto first)
    cloud2_cross_bull[0] = False
    cloud2_cross_bear[0] = False
    cloud3_cross_bull[0] = False
    cloud3_cross_bear[0] = False

    df["cloud2_cross_bull"]   = cloud2_cross_bull
    df["cloud2_cross_bear"]   = cloud2_cross_bear
    df["cloud3_cross_bull"]   = cloud3_cross_bull
    df["cloud3_cross_bear"]   = cloud3_cross_bear

    # Phase 3 activation: Cloud 3 AND Cloud 4 both aligned
    df["phase3_active_long"]  = c3_bull & c4_bull
    df["phase3_active_short"] = ~c3_bull & ~c4_bull

    return df
'''

# ─── File 2: signals/four_pillars_v391.py ────────────────────────────────────

FOUR_PILLARS_V391 = '''\
"""
Four Pillars v3.9.1 signal pipeline.

Changes from four_pillars_v390.py:
- Uses compute_clouds_v391() which adds EMA cross-detection columns:
    cloud2_cross_bull, cloud2_cross_bear
    cloud3_cross_bull, cloud3_cross_bear
    phase3_active_long, phase3_active_short
  These columns are consumed by backtester_v391 for the 3-phase SL
  movement system and Cloud 2 hard-close exit logic.
- State machine unchanged (state_machine_v390 reused as-is).
- Stochastic ADD signal arrays computed here for backtester_v391:
    add_long_signal, add_short_signal
  True on the bar stoch9 exits overbought/oversold while 40/60 confirm.
"""

import numpy as np
import pandas as pd

from .stochastics import compute_all_stochastics
from .clouds_v391 import compute_clouds_v391
from .bbwp import calculate_bbwp
from .state_machine_v390 import FourPillarsStateMachine390


def compute_signals_v391(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Run the full Four Pillars v3.9.1 signal pipeline on OHLCV data.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol]
        params: Strategy parameters. See defaults below.

    Returns:
        DataFrame with all indicator and signal columns added.
        Key new columns vs v390:
          cloud2_cross_bull, cloud2_cross_bear  - EMA 5/12 cross bars
          cloud3_cross_bull, cloud3_cross_bear  - EMA 34/50 cross bars
          phase3_active_long, phase3_active_short - Phase 3 activation
          add_long_signal, add_short_signal     - Stoch-based ADD triggers
    """
    if params is None:
        params = {}

    # Step 1: stochastic indicators
    df = compute_all_stochastics(df, params)

    # Step 2: Ripster EMA clouds v391 (includes Cloud 4 + cross-detection)
    df = compute_clouds_v391(df, params)

    # Step 3: BBW volatility context (non-fatal)
    try:
        df = calculate_bbwp(df, params)
    except Exception as e:
        import warnings
        warnings.warn("BBW calculation failed, skipping: " + str(e), stacklevel=2)

    # Step 4: ATR — Wilder RMA matching Pine ta.atr(14)
    atr_len = params.get("atr_length", 14)
    tr = np.maximum(
        df["high"].values - df["low"].values,
        np.maximum(
            np.abs(df["high"].values - np.roll(df["close"].values, 1)),
            np.abs(df["low"].values  - np.roll(df["close"].values, 1))
        )
    )
    tr[0] = df["high"].iloc[0] - df["low"].iloc[0]
    atr = np.full(len(tr), np.nan)
    atr[atr_len - 1] = np.mean(tr[:atr_len])
    for i in range(atr_len, len(tr)):
        atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
    df["atr"] = atr

    # Step 5: Bar-by-bar state machine — A and B signals (unchanged from v390)
    sm = FourPillarsStateMachine390(
        cross_level      = params.get("cross_level",      25),
        zone_level       = params.get("zone_level",       30),
        stage_lookback   = params.get("stage_lookback",   10),
        allow_b          = params.get("allow_b_trades",   True),
        b_open_fresh     = params.get("b_open_fresh",     True),
        cloud2_reentry   = params.get("cloud2_reentry",   True),
        reentry_lookback = params.get("reentry_lookback", 10),
        use_ripster      = params.get("use_ripster",      False),
        use_60d          = params.get("use_60d",          False),
    )

    n = len(df)
    signals = {
        "long_a":        np.zeros(n, dtype=bool),
        "long_b":        np.zeros(n, dtype=bool),
        "long_c":        np.zeros(n, dtype=bool),  # zero — engine labels C
        "short_a":       np.zeros(n, dtype=bool),
        "short_b":       np.zeros(n, dtype=bool),
        "short_c":       np.zeros(n, dtype=bool),  # zero
        "reentry_long":  np.zeros(n, dtype=bool),
        "reentry_short": np.zeros(n, dtype=bool),
    }

    stoch_9    = df["stoch_9"].values
    stoch_14   = df["stoch_14"].values
    stoch_40   = df["stoch_40"].values
    stoch_60   = df["stoch_60"].values
    stoch_60_d = df["stoch_60_d"].values
    price_pos  = df["price_pos"].values
    cross_above = df["price_cross_above_cloud2"].values
    cross_below = df["price_cross_below_cloud2"].values

    for i in range(n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_60[i]) or np.isnan(atr[i]):
            continue
        result = sm.process_bar(
            bar_index                = i,
            stoch_9                  = stoch_9[i],
            stoch_14                 = stoch_14[i],
            stoch_40                 = stoch_40[i],
            stoch_60                 = stoch_60[i],
            stoch_60_d               = stoch_60_d[i],
            price_pos                = int(price_pos[i]),
            price_cross_above_cloud2 = bool(cross_above[i]),
            price_cross_below_cloud2 = bool(cross_below[i]),
        )
        signals["long_a"][i]        = result.long_a
        signals["long_b"][i]        = result.long_b
        signals["short_a"][i]       = result.short_a
        signals["short_b"][i]       = result.short_b
        signals["reentry_long"][i]  = result.reentry_long
        signals["reentry_short"][i] = result.reentry_short

    for col, arr in signals.items():
        df[col] = arr

    # Step 6: Stochastic ADD signal detection
    # LONG ADD: stoch9 was > add_ob (overbought) and now crosses back below it,
    #   while stoch40 >= add_bull_min AND stoch60 >= add_bull_min
    # SHORT ADD: stoch9 was < add_os (oversold) and now crosses back above it,
    #   while stoch40 <= add_bear_max AND stoch60 <= add_bear_max
    add_ob       = params.get("add_ob",       70)    # overbought level for stoch9
    add_os       = params.get("add_os",       30)    # oversold level for stoch9
    add_bull_min = params.get("add_bull_min", 48)    # stoch40/60 must be >= this for long add
    add_bear_max = params.get("add_bear_max", 52)    # stoch40/60 must be <= this for short add

    add_long  = np.zeros(n, dtype=bool)
    add_short = np.zeros(n, dtype=bool)

    for i in range(1, n):
        if np.isnan(stoch_9[i]) or np.isnan(stoch_40[i]) or np.isnan(stoch_60[i]):
            continue
        # Long ADD: stoch9 was above add_ob, now exits (crosses below add_ob)
        if stoch_9[i - 1] >= add_ob and stoch_9[i] < add_ob:
            if stoch_40[i] >= add_bull_min and stoch_60[i] >= add_bull_min:
                add_long[i] = True
        # Short ADD: stoch9 was below add_os, now exits (crosses above add_os)
        if stoch_9[i - 1] <= add_os and stoch_9[i] > add_os:
            if stoch_40[i] <= add_bear_max and stoch_60[i] <= add_bear_max:
                add_short[i] = True

    df["add_long_signal"]  = add_long
    df["add_short_signal"] = add_short

    return df
'''

# ─── File 3: engine/position_v391.py ─────────────────────────────────────────

POSITION_V391 = '''\
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
'''

# ─── File 4: engine/backtester_v391.py ───────────────────────────────────────

BACKTESTER_V391 = '''\
"""
Four Pillars v3.9.1 backtest engine.

Key changes from backtester_v390.py:
- Uses PositionSlot391 (3-phase SL movement, Cloud 2 hard close).
- Hard close (CLOUD2_CLOSE) checked BEFORE SL/TP every bar.
- Cloud cross columns passed per-bar to update_bar().
- ADD signals are stochastic-based (from add_long_signal / add_short_signal
  columns in df), not AVWAP-price-based. AVWAP -2sigma is entry limit only.
- Trade record is Trade391 (includes sl_phase at close, bbwp fields).
- Signal pipeline: four_pillars_v391.compute_signals_v391()
"""

import numpy as np
import pandas as pd
from datetime import timezone
from typing import Optional

from .position_v391 import PositionSlot391, Trade391
from .commission import CommissionModel
from .avwap import AVWAPTracker


class Backtester391:
    """
    v3.9.1 multi-slot backtester with 3-phase SL and Cloud 2 hard close.

    Grade C = continuation/pyramid into existing same-direction position.
    Grade A/B = fresh entries (or first pyramid).
    ADD = stochastic-based add-on within trend (separate from A/B/C).
    """

    def __init__(self, params: dict = None):
        """Initialise backtester with strategy parameters."""
        p = params or {}

        self.sigma_floor_atr     = p.get("sigma_floor_atr",      0.5)
        self.sl_mult             = p.get("sl_mult",               2.0)
        self.tp_mult             = p.get("tp_mult",               4.0)  # default 4x ATR TP
        self.be_trigger_atr      = p.get("be_trigger_atr",        1.0)
        self.be_lock_atr         = p.get("be_lock_atr",           0.0)

        self.checkpoint_interval = p.get("checkpoint_interval",   5)
        self.max_scaleouts       = p.get("max_scaleouts",         2)

        self.max_positions  = p.get("max_positions",  4)
        self.cooldown       = p.get("cooldown",       3)
        self.b_open_fresh   = p.get("b_open_fresh",   True)
        self.allow_c_trades = p.get("allow_c_trades", True)
        self.notional       = p.get("notional",       5000.0)

        self.enable_adds      = p.get("enable_adds",      True)
        self.enable_reentry   = p.get("enable_reentry",   True)
        self.cancel_bars      = p.get("cancel_bars",      3)
        self.reentry_window   = p.get("reentry_window",   5)
        self.max_avwap_age    = p.get("max_avwap_age",    50)

        self.comm = CommissionModel(
            commission_rate     = p.get("commission_rate",     0.0008),
            maker_rate          = p.get("maker_rate",          0.0002),
            notional            = self.notional,
            rebate_pct          = p.get("rebate_pct",          0.70),
            settlement_hour_utc = p.get("settlement_hour_utc", 17),
        )

        self.initial_equity = p.get("initial_equity", 10000.0)

    # ─────────────────────────────────────────────────────────────────────────

    def run(self, df: pd.DataFrame) -> dict:
        """Run backtest on signal-enriched DataFrame. Returns results dict."""
        n     = len(df)
        close = df["close"].values
        high  = df["high"].values
        low   = df["low"].values
        atr   = df["atr"].values
        hlc3  = (high + low + close) / 3.0
        vol   = df["base_vol"].values if "base_vol" in df.columns else np.ones(n)

        # Stochastic signal arrays
        long_a        = df["long_a"].values
        long_b        = df["long_b"].values
        short_a       = df["short_a"].values
        short_b       = df["short_b"].values
        reentry_long  = df["reentry_long"].values
        reentry_short = df["reentry_short"].values
        add_long      = df["add_long_signal"].values  if "add_long_signal"  in df.columns else np.zeros(n, dtype=bool)
        add_short     = df["add_short_signal"].values if "add_short_signal" in df.columns else np.zeros(n, dtype=bool)

        # Cloud gate arrays
        cloud3_ok_long  = df["cloud3_allows_long"].values
        cloud3_ok_short = df["cloud3_allows_short"].values

        # Phase trigger arrays (new in v391)
        c2_cross_bull   = df["cloud2_cross_bull"].values   if "cloud2_cross_bull"   in df.columns else np.zeros(n, dtype=bool)
        c2_cross_bear   = df["cloud2_cross_bear"].values   if "cloud2_cross_bear"   in df.columns else np.zeros(n, dtype=bool)
        c3_cross_bull   = df["cloud3_cross_bull"].values   if "cloud3_cross_bull"   in df.columns else np.zeros(n, dtype=bool)
        c3_cross_bear   = df["cloud3_cross_bear"].values   if "cloud3_cross_bear"   in df.columns else np.zeros(n, dtype=bool)
        ph3_long        = df["phase3_active_long"].values  if "phase3_active_long"  in df.columns else np.zeros(n, dtype=bool)
        ph3_short       = df["phase3_active_short"].values if "phase3_active_short" in df.columns else np.zeros(n, dtype=bool)

        # BBW context (optional)
        bbwp_state_arr    = df["bbwp_state"].values    if "bbwp_state"    in df.columns else np.full(n, "")
        bbwp_value_arr    = df["bbwp_value"].values    if "bbwp_value"    in df.columns else np.full(n, float("nan"))
        bbwp_spectrum_arr = df["bbwp_spectrum"].values if "bbwp_spectrum" in df.columns else np.full(n, "")

        # Datetime for commission settlement
        if "datetime" in df.columns:
            datetimes = df["datetime"].values
            has_dt = True
        elif isinstance(df.index, pd.DatetimeIndex):
            datetimes = df.index.values
            has_dt = True
        else:
            datetimes = None
            has_dt = False

        slots: list[Optional[PositionSlot391]] = [None] * 4
        last_entry_bar: Optional[int] = None
        trades: list[Trade391] = []
        equity = self.initial_equity
        equity_curve    = np.full(n, equity)
        position_counts = np.zeros(n, dtype=int)

        # Pending limit order state
        pend_bar:   Optional[int]          = None
        pend_dir:   int                    = 0
        pend_limit: Optional[float]        = None
        pend_grade: str                    = ""
        pend_avwap: Optional[AVWAPTracker] = None

        # Re-entry AVWAP state
        re_bar:     Optional[int]          = None
        re_dir:     int                    = 0
        re_tracker: Optional[AVWAPTracker] = None

        for i in range(n):
            if np.isnan(atr[i]):
                equity_curve[i] = equity
                continue

            # Commission settlement
            if has_dt and datetimes is not None:
                bar_dt = pd.Timestamp(datetimes[i]).to_pydatetime()
                if bar_dt.tzinfo is None:
                    bar_dt = bar_dt.replace(tzinfo=timezone.utc)
                equity += self.comm.check_settlement(bar_dt)

            # ── Step 1: Cloud 2 hard close (highest priority) ──────────────────
            for s in range(4):
                if slots[s] is None:
                    continue
                if slots[s].check_cloud2_hard_close(bool(c2_cross_bear[i]), bool(c2_cross_bull[i])):
                    comm_exit = self.comm.charge_custom(slots[s].notional, maker=True)
                    trade = slots[s].close_at(
                        close[i], i, "CLOUD2_CLOSE",
                        comm_exit + slots[s].entry_commission,
                    )
                    trade.bbwp_state   = str(bbwp_state_arr[slots[s].entry_bar])
                    trade.bbwp_value   = float(bbwp_value_arr[slots[s].entry_bar])
                    trade.bbwp_spectrum = str(bbwp_spectrum_arr[slots[s].entry_bar])
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if self.enable_reentry:
                        re_bar     = i
                        re_dir     = 1 if slots[s].direction == "LONG" else -1
                        re_tracker = slots[s].avwap.clone()
                    slots[s] = None

            # ── Step 2: Normal SL/TP exits ─────────────────────────────────────
            for s in range(4):
                if slots[s] is None:
                    continue
                reason = slots[s].check_exit(high[i], low[i])
                if reason:
                    exit_price = slots[s].tp if reason == "TP" else slots[s].sl
                    comm_exit  = self.comm.charge_custom(slots[s].notional, maker=True)
                    trade = slots[s].close_at(
                        exit_price, i, reason,
                        comm_exit + slots[s].entry_commission,
                    )
                    trade.bbwp_state    = str(bbwp_state_arr[slots[s].entry_bar])
                    trade.bbwp_value    = float(bbwp_value_arr[slots[s].entry_bar])
                    trade.bbwp_spectrum = str(bbwp_spectrum_arr[slots[s].entry_bar])
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if self.enable_reentry and reason == "SL":
                        re_bar     = i
                        re_dir     = 1 if slots[s].direction == "LONG" else -1
                        re_tracker = slots[s].avwap.clone()
                    slots[s] = None

            # ── Step 3: Update bars (phase advancement + AVWAP + BE + MFE/MAE) ─
            for s in range(4):
                if slots[s] is not None:
                    slots[s].update_bar(
                        i, high[i], low[i], close[i], atr[i], hlc3[i], vol[i],
                        cloud2_cross_bull = bool(c2_cross_bull[i]),
                        cloud2_cross_bear = bool(c2_cross_bear[i]),
                        cloud3_cross_bull = bool(c3_cross_bull[i]),
                        cloud3_cross_bear = bool(c3_cross_bear[i]),
                        phase3_long       = bool(ph3_long[i]),
                        phase3_short      = bool(ph3_short[i]),
                    )

            # ── Step 4: Scale-outs ─────────────────────────────────────────────
            for s in range(4):
                if slots[s] is None:
                    continue
                if slots[s].check_scale_out(i, close[i]):
                    is_final        = (slots[s].scale_count + 1 >= slots[s].max_scaleouts)
                    scale_notional  = slots[s].notional if is_final else slots[s].notional / 2
                    comm_exit       = self.comm.charge_custom(scale_notional, maker=True)
                    entry_share     = slots[s].entry_commission * scale_notional / slots[s].original_notional
                    trade, is_final = slots[s].do_scale_out(i, close[i], comm_exit + entry_share)
                    trade.bbwp_state    = str(bbwp_state_arr[slots[s].entry_bar])
                    trade.bbwp_value    = float(bbwp_value_arr[slots[s].entry_bar])
                    trade.bbwp_spectrum = str(bbwp_spectrum_arr[slots[s].entry_bar])
                    trades.append(trade)
                    equity += trade.pnl - comm_exit
                    if is_final:
                        slots[s] = None

            # ── Step 5: Pending limit fills ────────────────────────────────────
            if pend_dir != 0 and pend_bar is not None:
                if i - pend_bar >= self.cancel_bars:
                    pend_bar = pend_dir = 0
                    pend_limit = pend_grade = pend_avwap = None
                else:
                    filled = (
                        (pend_dir ==  1 and low[i]  <= pend_limit) or
                        (pend_dir == -1 and high[i] >= pend_limit)
                    )
                    if filled:
                        empty = self._find_empty(slots)
                        if empty >= 0:
                            comm_entry = self.comm.charge(maker=True)
                            equity    -= comm_entry
                            direction  = "LONG" if pend_dir == 1 else "SHORT"
                            slots[empty] = PositionSlot391(
                                direction           = direction,
                                grade               = pend_grade,
                                entry_bar           = i,
                                entry_price         = pend_limit,
                                atr                 = atr[i],
                                hlc3                = hlc3[i],
                                volume              = vol[i],
                                sigma_floor_atr     = self.sigma_floor_atr,
                                sl_mult             = self.sl_mult,
                                tp_mult             = self.tp_mult,
                                be_trigger_atr      = self.be_trigger_atr,
                                be_lock_atr         = self.be_lock_atr,
                                notional            = self.notional,
                                checkpoint_interval = self.checkpoint_interval,
                                max_scaleouts       = self.max_scaleouts,
                                avwap_state         = pend_avwap,
                            )
                            slots[empty].entry_commission = comm_entry
                            last_entry_bar = i
                        pend_bar = pend_dir = 0
                        pend_limit = pend_grade = pend_avwap = None

            # ── Step 6: Stochastic entries ─────────────────────────────────────
            active_count = sum(1 for s in slots if s is not None)
            cooldown_ok  = last_entry_bar is None or (i - last_entry_bar >= self.cooldown)
            can_enter    = active_count < self.max_positions and cooldown_ok

            has_longs  = any(s is not None and s.direction == "LONG"  for s in slots)
            has_shorts = any(s is not None and s.direction == "SHORT" for s in slots)

            can_long_a  = not has_shorts and can_enter
            can_short_a = not has_longs  and can_enter
            can_long_b  = not has_shorts and can_enter and bool(cloud3_ok_long[i])
            can_short_b = not has_longs  and can_enter and bool(cloud3_ok_short[i])

            did_enter = False

            # Grade A long
            if long_a[i] and can_long_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    grade = "C" if has_longs and self.allow_c_trades else "A"
                    if grade == "A" or (grade == "C" and self.allow_c_trades):
                        self._open_slot(slots, empty, "LONG", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # Grade A short
            if short_a[i] and can_short_a and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    grade = "C" if has_shorts and self.allow_c_trades else "A"
                    if grade == "A" or (grade == "C" and self.allow_c_trades):
                        self._open_slot(slots, empty, "SHORT", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # Grade B long
            if long_b[i] and can_long_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    fresh_ok = not has_longs or self.b_open_fresh
                    grade    = "C" if has_longs else "B"
                    if (grade == "B" and fresh_ok) or (grade == "C" and self.allow_c_trades):
                        self._open_slot(slots, empty, "LONG", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # Grade B short
            if short_b[i] and can_short_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    fresh_ok = not has_shorts or self.b_open_fresh
                    grade    = "C" if has_shorts else "B"
                    if (grade == "B" and fresh_ok) or (grade == "C" and self.allow_c_trades):
                        self._open_slot(slots, empty, "SHORT", grade, i,
                                        close[i], atr[i], hlc3[i], vol[i])
                        equity -= slots[empty].entry_commission
                        last_entry_bar = i
                        did_enter = True

            # Re-entry (state-machine cloud2 reentry signal)
            if reentry_long[i] and can_long_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    self._open_slot(slots, empty, "LONG", "R", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    equity -= slots[empty].entry_commission
                    last_entry_bar = i
                    did_enter = True

            if reentry_short[i] and can_short_b and not did_enter:
                empty = self._find_empty(slots)
                if empty >= 0:
                    self._open_slot(slots, empty, "SHORT", "R", i,
                                    close[i], atr[i], hlc3[i], vol[i])
                    equity -= slots[empty].entry_commission
                    last_entry_bar = i
                    did_enter = True

            # ── Step 7: Stochastic ADD signals ────────────────────────────────
            # ADD fires only when a position exists in the same direction.
            # Entry limit: AVWAP -2sigma (long) or +2sigma (short).
            # Uses pending limit order, same cancel logic as AVWAP ADDs.
            if self.enable_adds and pend_dir == 0 and not did_enter and cooldown_ok:
                for s in range(4):
                    if slots[s] is None or pend_dir != 0:
                        continue
                    sv = slots[s].avwap.center
                    ss = slots[s].avwap.sigma
                    if sv is None or ss is None:
                        continue
                    age = i - slots[s].entry_bar
                    if age > self.max_avwap_age:
                        continue

                    # Stoch-based ADD: signal fires, slot in correct direction
                    if add_long[i] and slots[s].direction == "LONG" and bool(cloud3_ok_long[i]):
                        pend_bar   = i
                        pend_dir   = 1
                        pend_limit = sv - ss        # AVWAP -1sigma limit
                        pend_grade = "ADD"
                        pend_avwap = slots[s].avwap.clone()
                        break
                    if add_short[i] and slots[s].direction == "SHORT" and bool(cloud3_ok_short[i]):
                        pend_bar   = i
                        pend_dir   = -1
                        pend_limit = sv + ss        # AVWAP +1sigma limit
                        pend_grade = "ADD"
                        pend_avwap = slots[s].avwap.clone()
                        break

            # ── Step 8: AVWAP re-entry ─────────────────────────────────────────
            re_dir_ok = (
                (re_dir ==  1 and not has_shorts) or
                (re_dir == -1 and not has_longs)  or
                re_dir == 0
            )
            if self.enable_reentry and re_dir != 0 and re_dir_ok and \
               pend_dir == 0 and not did_enter:
                if re_bar is not None and i - re_bar > self.reentry_window:
                    re_bar = re_dir = 0
                    re_tracker = None
                elif re_tracker is not None and active_count < self.max_positions and cooldown_ok:
                    c_re  = re_tracker.center
                    s_re  = re_tracker.sigma
                    if c_re is not None and s_re is not None:
                        re_m2 = c_re - 2.0 * s_re
                        re_p2 = c_re + 2.0 * s_re
                        re_m1 = c_re - s_re
                        re_p1 = c_re + s_re
                        if re_dir == 1 and low[i] <= re_m2 and bool(cloud3_ok_long[i]):
                            pend_bar   = i
                            pend_dir   = 1
                            pend_limit = re_m1
                            pend_grade = "RE"
                            pend_avwap = re_tracker.clone()
                            re_dir     = 0
                        elif re_dir == -1 and high[i] >= re_p2 and bool(cloud3_ok_short[i]):
                            pend_bar   = i
                            pend_dir   = -1
                            pend_limit = re_p1
                            pend_grade = "RE"
                            pend_avwap = re_tracker.clone()
                            re_dir     = 0

            # ── Equity curve ───────────────────────────────────────────────────
            position_counts[i] = sum(1 for s in slots if s is not None)
            unrealized = 0.0
            for s in range(4):
                if slots[s] is not None:
                    if slots[s].direction == "LONG":
                        unrealized += (close[i] - slots[s].entry_price) / slots[s].entry_price * slots[s].notional
                    else:
                        unrealized += (slots[s].entry_price - close[i]) / slots[s].entry_price * slots[s].notional
            equity_curve[i] = equity + unrealized

        # Close remaining open positions at last bar
        for s in range(4):
            if slots[s] is not None:
                comm_exit = self.comm.charge_custom(slots[s].notional, maker=True)
                trade = slots[s].close_at(
                    close[-1], n - 1, "END",
                    comm_exit + slots[s].entry_commission,
                )
                trade.bbwp_state    = ""
                trade.bbwp_value    = float("nan")
                trade.bbwp_spectrum = ""
                trades.append(trade)
                equity += trade.pnl - comm_exit
        equity_curve[-1] = equity

        metrics = self._compute_metrics(trades, equity_curve)
        metrics["final_equity"]         = equity
        metrics["equity_curve"]         = equity_curve
        metrics["total_rebate"]         = self.comm.total_rebate
        metrics["net_pnl_after_rebate"] = metrics["net_pnl"] + self.comm.total_rebate
        metrics["total_volume"]         = self.comm.total_volume
        metrics["total_sides"]          = self.comm.total_sides

        margin_per_pos = self.notional / 20.0
        valid_counts   = position_counts[~np.isnan(atr)]
        if len(valid_counts) > 0:
            metrics["avg_positions"]      = float(np.mean(valid_counts))
            metrics["max_positions_used"] = int(np.max(valid_counts))
            metrics["pct_time_flat"]      = float(np.sum(valid_counts == 0) / len(valid_counts))
            metrics["avg_margin_used"]    = float(np.mean(valid_counts) * margin_per_pos)
            metrics["peak_margin_used"]   = float(np.max(valid_counts) * margin_per_pos)
        else:
            metrics.update({
                "avg_positions": 0, "max_positions_used": 0,
                "pct_time_flat": 1.0, "avg_margin_used": 0, "peak_margin_used": 0,
            })

        return {
            "trades":          trades,
            "trades_df":       self._trades_to_df(trades),
            "metrics":         metrics,
            "equity_curve":    equity_curve,
            "position_counts": position_counts,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _find_empty(self, slots: list) -> int:
        """Return index of first empty slot, or -1 if all full."""
        for i in range(4):
            if slots[i] is None:
                return i
        return -1

    def _open_slot(
        self, slots: list, idx: int, direction: str, grade: str,
        bar_idx: int, entry_price: float, atr_val: float, hlc3_val: float, volume_val: float,
    ) -> None:
        """Open a new position slot and charge entry commission."""
        comm = self.comm.charge()
        slots[idx] = PositionSlot391(
            direction           = direction,
            grade               = grade,
            entry_bar           = bar_idx,
            entry_price         = entry_price,
            atr                 = atr_val,
            hlc3                = hlc3_val,
            volume              = volume_val,
            sigma_floor_atr     = self.sigma_floor_atr,
            sl_mult             = self.sl_mult,
            tp_mult             = self.tp_mult,
            be_trigger_atr      = self.be_trigger_atr,
            be_lock_atr         = self.be_lock_atr,
            notional            = self.notional,
            checkpoint_interval = self.checkpoint_interval,
            max_scaleouts       = self.max_scaleouts,
            avwap_state         = None,
        )
        slots[idx].entry_commission = comm

    def _compute_metrics(self, trades: list, equity_curve: np.ndarray) -> dict:
        """Compute summary metrics from completed trades."""
        if not trades:
            return {"total_trades": 0, "net_pnl": 0.0}

        pnls     = np.array([t.pnl for t in trades])
        net_pnls = np.array([t.pnl - t.commission for t in trades])
        comms    = np.array([t.commission for t in trades])
        winners  = net_pnls[net_pnls > 0]
        losers   = net_pnls[net_pnls <= 0]

        total    = len(trades)
        win_rate = len(winners) / total if total > 0 else 0.0
        gp       = float(np.sum(winners)) if len(winners) > 0 else 0.0
        gl       = float(np.abs(np.sum(losers))) if len(losers) > 0 else 0.0
        pf       = gp / gl if gl > 0 else float("inf")

        saw_green_losers = sum(1 for t in trades if t.saw_green and t.pnl - t.commission <= 0)
        total_losers     = sum(1 for t in trades if t.pnl - t.commission <= 0)

        grades = {}
        for grade in ["A", "B", "C", "R", "ADD", "RE"]:
            gt = [t for t in trades if t.grade == grade]
            if gt:
                gp2 = [t.pnl - t.commission for t in gt]
                grades[grade] = {
                    "count":     len(gt),
                    "win_rate":  sum(1 for p in gp2 if p > 0) / len(gt),
                    "avg_pnl":   float(np.mean(gp2)),
                    "total_pnl": float(np.sum(gp2)),
                }

        # Phase breakdown
        phase_stats = {}
        for ph in [0, 1, 2, 3]:
            pt = [t for t in trades if t.sl_phase == ph]
            if pt:
                pp = [t.pnl - t.commission for t in pt]
                phase_stats[ph] = {
                    "count":     len(pt),
                    "win_rate":  sum(1 for p in pp if p > 0) / len(pt),
                    "avg_pnl":   float(np.mean(pp)),
                    "total_pnl": float(np.sum(pp)),
                }

        # Exit reason breakdown
        exit_reasons = {}
        for t in trades:
            exit_reasons[t.exit_reason] = exit_reasons.get(t.exit_reason, 0) + 1

        # BBW breakdown
        bbwp_groups = {}
        for state in ["BLUE_DOUBLE", "BLUE", "NORMAL", "RED", "RED_DOUBLE", "MA_CROSS_UP", "MA_CROSS_DOWN"]:
            st = [t for t in trades if t.bbwp_state == state]
            if st:
                sp = [t.pnl - t.commission for t in st]
                bbwp_groups[state] = {
                    "count":    len(st),
                    "win_rate": sum(1 for p in sp if p > 0) / len(st),
                    "avg_pnl":  float(np.mean(sp)),
                }

        sharpe = 0.0
        if len(net_pnls) > 1 and np.std(net_pnls) > 0:
            sharpe = float(np.mean(net_pnls) / np.std(net_pnls))

        max_dd = max_dd_pct = 0.0
        if equity_curve is not None and len(equity_curve) > 0:
            peak       = np.maximum.accumulate(equity_curve)
            drawdown   = peak - equity_curve
            max_dd     = float(np.max(drawdown))
            max_dd_pct = float(np.max(drawdown / peak) * 100) if np.max(peak) > 0 else 0.0

        return {
            "total_trades":         total,
            "win_count":            len(winners),
            "loss_count":           len(losers),
            "win_rate":             win_rate,
            "avg_win":              float(np.mean(winners)) if len(winners) > 0 else 0.0,
            "avg_loss":             float(np.mean(losers))  if len(losers)  > 0 else 0.0,
            "expectancy":           float(np.mean(net_pnls)),
            "gross_profit":         gp,
            "gross_loss":           gl,
            "profit_factor":        pf,
            "net_pnl":              float(np.sum(net_pnls)),
            "total_commission":     float(np.sum(comms)),
            "sharpe":               sharpe,
            "max_drawdown":         max_dd,
            "max_drawdown_pct":     max_dd_pct,
            "pct_losers_saw_green": saw_green_losers / total_losers if total_losers > 0 else 0.0,
            "saw_green_losers":     saw_green_losers,
            "total_losers":         total_losers,
            "be_raised_count":      sum(1 for t in trades if t.be_raised),
            "cloud2_close_count":   exit_reasons.get("CLOUD2_CLOSE", 0),
            "tp_exits":             sum(1 for t in trades if t.exit_reason == "TP"),
            "sl_exits":             sum(1 for t in trades if t.exit_reason == "SL"),
            "grades":               grades,
            "phase_stats":          phase_stats,
            "exit_reasons":         exit_reasons,
            "bbwp_groups":          bbwp_groups,
        }

    def _trades_to_df(self, trades: list) -> pd.DataFrame:
        """Convert trade list to DataFrame."""
        if not trades:
            return pd.DataFrame()
        return pd.DataFrame([
            {
                "direction":    t.direction,
                "grade":        t.grade,
                "entry_bar":    t.entry_bar,
                "exit_bar":     t.exit_bar,
                "entry_price":  t.entry_price,
                "exit_price":   t.exit_price,
                "sl_price":     t.sl_price,
                "tp_price":     t.tp_price,
                "sl_phase":     t.sl_phase,
                "pnl":          t.pnl,
                "commission":   t.commission,
                "net_pnl":      t.pnl - t.commission,
                "mfe":          t.mfe,
                "mae":          t.mae,
                "exit_reason":  t.exit_reason,
                "saw_green":    t.saw_green,
                "be_raised":    t.be_raised,
                "scale_idx":    t.scale_idx,
                "bbwp_state":   t.bbwp_state,
                "bbwp_value":   t.bbwp_value,
                "bbwp_spectrum":t.bbwp_spectrum,
            }
            for t in trades
        ])
'''

# ─── Main: write all files ────────────────────────────────────────────────────

def main():
    """Write all v391 files and syntax-check each one."""
    print("=== build_strategy_v391.py ===")
    print("ROOT: " + str(ROOT))

    files = [
        (SIGNALS_DIR / "clouds_v391.py",       CLOUDS_V391),
        (SIGNALS_DIR / "four_pillars_v391.py",  FOUR_PILLARS_V391),
        (ENGINE_DIR  / "position_v391.py",      POSITION_V391),
        (ENGINE_DIR  / "backtester_v391.py",    BACKTESTER_V391),
    ]

    for path, content in files:
        print("\n--- " + path.name + " ---")
        if not write_file(path, content):
            continue
        if not verify(path):
            ERRORS.append(str(path))

    print("\n=== RESULTS ===")
    if ERRORS:
        print("BUILD FAILED -- syntax errors in: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print("BUILD OK -- all 4 files compile clean")
        print("Run command:")
        print('  python scripts/test_v391.py')


if __name__ == "__main__":
    main()
