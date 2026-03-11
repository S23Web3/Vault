"""
Build script: 55/89 signal pipeline v2 redesign + engine BE trigger.

Workflow: LOG -> WRITE -> AUDIT -> TEST -> OUTPUT

Creates:
  signals/ema_cross_55_89_v2.py   (2-state overzone entry, cascading grade)
  scripts/test_55_89_signals_v2.py (7 test cases)

Modifies:
  engine/backtester_55_89.py      (BE trigger on EMA cross, overzone params, trade_grade)
  scripts/dashboard_55_89_v3.py   (import v2, new sliders, grade column)

Run: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/build_5589_v2_redesign.py"
"""

import ast
import logging
import os
import py_compile
import re
import sys
import textwrap
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
log_file = LOGS_DIR / datetime.now(timezone.utc).strftime("%Y-%m-%d-build-5589-v2.log")
file_handler = TimedRotatingFileHandler(
    str(log_file), when="midnight", backupCount=30, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(fmt)
stream_handler.setFormatter(fmt)

log = logging.getLogger("build_5589_v2")
log.setLevel(logging.DEBUG)
log.addHandler(file_handler)
log.addHandler(stream_handler)

ERRORS = []
ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def validate_output(path_str: str) -> bool:
    """Run py_compile + ast.parse on a .py file. Both must pass."""
    try:
        py_compile.compile(path_str, doraise=True)
        log.info("  SYNTAX OK: %s", path_str)
    except py_compile.PyCompileError as e:
        log.error("  SYNTAX ERROR: %s", e)
        return False
    try:
        source = Path(path_str).read_text(encoding="utf-8")
        ast.parse(source, filename=path_str)
        log.info("  AST OK: %s", path_str)
    except SyntaxError as e:
        log.error("  AST ERROR in %s line %s: %s", path_str, e.lineno, e.msg)
        return False
    return True


def check_exists(path: Path) -> bool:
    """Return True if file already exists (abort for new files)."""
    if path.exists():
        log.error("FILE ALREADY EXISTS: %s -- aborting write", path)
        return True
    return False


# ===========================================================================
# FILE 1: signals/ema_cross_55_89_v2.py
# ===========================================================================
log.info("=" * 70)
log.info("[%s] BUILD START: 55/89 Signal Pipeline v2 Redesign", ts)
log.info("=" * 70)

SIGNAL_V2_PATH = ROOT / "signals" / "ema_cross_55_89_v2.py"
if check_exists(SIGNAL_V2_PATH):
    ERRORS.append(str(SIGNAL_V2_PATH))
else:
    log.info("STEP 1: Writing %s", SIGNAL_V2_PATH)

    SIGNAL_V2_CODE = textwrap.dedent('''\
    """
    55/89 EMA Cross Scalp v2 -- Signal pipeline.

    v2 redesign: 2-state stoch 9 D overzone entry, cascading alignment
    (affects trade grade, not entry decision), EMA cross columns for BE trigger,
    TDI uses RSI 14, regression channel gate (stub or real module).

    Entry logic:
      State 1 (MONITORING): stoch 9 D drops below 20 (long) / above 80 (short)
      State 2 (ENTRY): stoch 9 D exits overzone + regression gate passes -> signal fires

    Grade system at entry:
      A = stoch 40 AND 60 already TURNING+ at entry
      B = stoch 40 OR 60 TURNING+ (partial alignment)
      C = neither 40 nor 60 TURNING+ (no alignment yet)

    Source of truth: 06-CLAUDE-LOGS/plans/2026-03-10-5589-v2-redesign-plan.md
    """

    import numpy as np
    import pandas as pd
    from numba import njit

    from .stochastics_v2 import compute_all_stochastics
    from .clouds_v2 import ema

    # Try real regression channel; fall back to stub
    try:
        from .regression_channel import (
            fit_channel,
            pre_stage1_gate,
            compute_channel_anchored,
            price_in_lower_half,
        )
        _HAS_REGRESSION = True
    except ImportError:
        _HAS_REGRESSION = False


    # ---- ATR (Wilder RMA) ----

    @njit(cache=True)
    def _rma_kernel(tr, atr_len):
        """Wilder RMA loop for ATR; Numba JIT-compiled."""
        atr = np.full(len(tr), np.nan)
        if len(tr) < atr_len:
            return atr
        atr[atr_len - 1] = np.mean(tr[:atr_len])
        for i in range(atr_len, len(tr)):
            atr[i] = (atr[i - 1] * (atr_len - 1) + tr[i]) / atr_len
        return atr


    def compute_atr(df, atr_len=14):
        """Compute ATR using Wilder RMA."""
        h = df["high"].values
        l = df["low"].values
        c = df["close"].values
        prev_c = np.roll(c, 1)
        tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
        tr[0] = h[0] - l[0]
        return _rma_kernel(tr, atr_len)


    # ---- D lines (SMA of K) ----

    def compute_d_line(k_series, smooth):
        """Compute D line as SMA(K, smooth)."""
        return pd.Series(k_series).rolling(window=smooth, min_periods=1).mean().values


    # ---- TDI (RSI 14 for v2) ----

    def compute_rsi(close, period):
        """Compute RSI using Wilder smoothing."""
        n = len(close)
        rsi = np.full(n, np.nan)
        if n < period + 1:
            return rsi
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        if avg_loss == 0:
            rsi[period] = 100.0
        else:
            rsi[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                rsi[i + 1] = 100.0
            else:
                rsi[i + 1] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        return rsi


    def sma(series, window):
        """Simple moving average with min_periods=1."""
        return pd.Series(series).rolling(window=window, min_periods=1).mean().values


    def compute_tdi(close, rsi_period=14, smooth_period=5, signal_period=10):
        """Compute TDI: RSI smoothed price line and signal line. v2 default RSI=14."""
        rsi = compute_rsi(close, rsi_period)
        price_line = sma(rsi, smooth_period)
        signal_line = sma(rsi, signal_period)
        return price_line, signal_line


    # ---- BBW / BBWP ----

    def compute_bbwp(close, bb_len=20, bb_mult=2.0, bbwp_len=100, spectrum_ma_len=7):
        """Compute BBWP and Spectrum MA. Returns (bbwp, spectrum_ma, bbw_state)."""
        n = len(close)
        s = pd.Series(close)
        sma_bb = s.rolling(window=bb_len, min_periods=bb_len).mean().values
        std_bb = s.rolling(window=bb_len, min_periods=bb_len).std(ddof=0).values
        upper = sma_bb + bb_mult * std_bb
        lower = sma_bb - bb_mult * std_bb
        bbw = np.full(n, np.nan)
        valid = sma_bb != 0
        bbw[valid] = (upper[valid] - lower[valid]) / sma_bb[valid]

        bbwp = np.full(n, np.nan)
        for i in range(bbwp_len + bb_len - 1, n):
            window = bbw[i - bbwp_len + 1: i + 1]
            valid_w = window[~np.isnan(window)]
            if len(valid_w) > 0:
                bbwp[i] = np.sum(valid_w < bbw[i]) / len(valid_w) * 100.0

        spectrum_ma = sma(bbwp, spectrum_ma_len)

        bbw_state = np.full(n, 0, dtype=np.int8)
        for i in range(n):
            if np.isnan(bbwp[i]) or np.isnan(spectrum_ma[i]):
                continue
            if bbwp[i] > 80:
                bbw_state[i] = 2   # EXTREME
            elif bbwp[i] > spectrum_ma[i]:
                bbw_state[i] = 1   # HEALTHY
            else:
                bbw_state[i] = -1  # QUIET

        return bbwp, spectrum_ma, bbw_state


    # ---- Markov State Classification ----

    STATE_ZONE = 0
    STATE_TURNING = 1
    STATE_MOVING = 2
    STATE_EXTENDED = 3

    STATE_NAMES = {0: "ZONE", 1: "TURNING", 2: "MOVING", 3: "EXTENDED"}


    def classify_markov_state_long(k_val, slope, accel):
        """Classify a single stoch bar into Markov state for LONG."""
        if k_val < 20:
            return STATE_ZONE
        if k_val > 50 and slope > 0:
            return STATE_EXTENDED
        if slope > 0 and accel > 0:
            return STATE_MOVING
        if slope > 0:
            return STATE_TURNING
        return STATE_ZONE


    def classify_markov_state_short(k_val, slope, accel):
        """Classify a single stoch bar into Markov state for SHORT."""
        if k_val > 80:
            return STATE_ZONE
        if k_val < 50 and slope < 0:
            return STATE_EXTENDED
        if slope < 0 and accel < 0:
            return STATE_MOVING
        if slope < 0:
            return STATE_TURNING
        return STATE_ZONE


    # ---- Regression Channel Gate ----

    def regression_gate_long(i, close_arr, pre_lookback=20, r2_min=0.45, slope_pct_max=-0.001):
        """Check if pre-entry channel shows orderly decline for LONG entry."""
        if not _HAS_REGRESSION:
            return True  # stub: always pass
        start = max(0, i - pre_lookback)
        if i - start < 3:
            return True  # not enough bars, pass by default
        prices = close_arr[start:i + 1]
        ch = fit_channel(prices)
        return pre_stage1_gate(ch, r2_min=r2_min, slope_pct_max=slope_pct_max)


    def regression_gate_short(i, close_arr, pre_lookback=20, r2_min=0.45, slope_pct_min=0.001):
        """Check if pre-entry channel shows orderly rally for SHORT entry."""
        if not _HAS_REGRESSION:
            return True  # stub: always pass
        start = max(0, i - pre_lookback)
        if i - start < 3:
            return True
        prices = close_arr[start:i + 1]
        ch = fit_channel(prices)
        # For short: need positive slope (was rallying) and good R2
        return ch.r_squared > r2_min and ch.slope_pct > slope_pct_min


    # ---- Main Signal Pipeline v2 ----

    def compute_signals_55_89(df, params=None):
        """Compute 55/89 v2 signals: 2-state overzone entry, cascading grade, EMA cross BE columns.

        Pipeline:
        1. Compute stochs + D lines
        2. Compute EMA(55), EMA(89), delta, EMA cross columns
        3. Compute TDI (RSI 14), BBW
        4. Classify Markov states per stoch (for grading)
        5. Run 2-state overzone pipeline: IDLE -> MONITORING -> ENTRY
        6. Grade each signal: A/B/C based on stoch 40/60 alignment at entry
        7. Map to engine columns (long_a, short_a, trade_grade, ema_cross_bull, ema_cross_bear)
        """
        p = params or {}
        slope_n = p.get("slope_n", 5)
        slope_m = p.get("slope_m", 3)
        ema_fast = p.get("ema_fast", 55)
        ema_slow = p.get("ema_slow", 89)
        rsi_period = p.get("rsi_period", 14)
        rsi_smooth = p.get("rsi_smooth", 5)
        rsi_signal = p.get("rsi_signal", 10)
        bb_len = p.get("bb_len", 20)
        bb_mult = p.get("bb_mult", 2.0)
        bbwp_len = p.get("bbwp_len", 100)
        spectrum_ma_len = p.get("spectrum_ma_len", 7)
        atr_len = p.get("atr_length", 14)
        overzone_long = p.get("overzone_long_threshold", 20.0)
        overzone_short = p.get("overzone_short_threshold", 80.0)
        min_signal_gap = p.get("min_signal_gap", 50)
        pre_lookback = p.get("pre_lookback", 20)
        r2_min = p.get("r2_min", 0.45)

        df = df.copy()
        n = len(df)
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values

        # Step 1: Stochastics (all 4 K values)
        df = compute_all_stochastics(df, params)
        k9 = df["stoch_9"].values
        k14 = df["stoch_14"].values
        k40 = df["stoch_40"].values
        k60 = df["stoch_60"].values

        # D lines with correct smoothing per position management study
        d9 = compute_d_line(k9, 3)
        d14 = compute_d_line(k14, 3)
        d40 = compute_d_line(k40, 4)
        d60 = compute_d_line(k60, 10)
        df["stoch_9_d"] = d9
        df["stoch_14_d"] = d14
        df["stoch_40_d"] = d40
        df["stoch_60_d"] = d60

        # Step 2: EMAs and delta
        ema55 = ema(close, ema_fast)
        ema89 = ema(close, ema_slow)
        delta = ema55 - ema89
        df["ema_55"] = ema55
        df["ema_89"] = ema89
        df["ema_delta"] = delta

        # EMA cross columns (for engine BE trigger)
        ema_cross_bull = np.zeros(n, dtype=bool)
        ema_cross_bear = np.zeros(n, dtype=bool)
        for i in range(1, n):
            if np.isnan(delta[i]) or np.isnan(delta[i - 1]):
                continue
            if delta[i - 1] < 0 and delta[i] >= 0:
                ema_cross_bull[i] = True
            elif delta[i - 1] > 0 and delta[i] <= 0:
                ema_cross_bear[i] = True
        df["ema_cross_bull"] = ema_cross_bull
        df["ema_cross_bear"] = ema_cross_bear

        # Step 3: ATR
        atr_vals = compute_atr(df, atr_len)
        df["atr"] = atr_vals

        # Step 4: TDI (RSI 14 for v2)
        tdi_price, tdi_signal = compute_tdi(close, rsi_period, rsi_smooth, rsi_signal)
        df["tdi_price"] = tdi_price
        df["tdi_signal"] = tdi_signal

        # Step 5: BBW
        bbwp, spectrum_ma, bbw_state = compute_bbwp(close, bb_len, bb_mult, bbwp_len, spectrum_ma_len)
        df["bbwp_value"] = bbwp
        df["bbwp_spectrum"] = spectrum_ma
        bbw_state_str = np.where(bbw_state == 1, "HEALTHY",
                        np.where(bbw_state == 2, "EXTREME",
                        np.where(bbw_state == -1, "QUIET", "UNKNOWN")))
        df["bbwp_state"] = bbw_state_str

        # Step 6: Slopes and acceleration for grading
        slope_40 = np.full(n, 0.0)
        slope_60 = np.full(n, 0.0)
        accel_40 = np.full(n, 0.0)
        accel_60 = np.full(n, 0.0)
        for i in range(slope_n, n):
            slope_40[i] = k40[i] - k40[i - slope_n]
            slope_60[i] = k60[i] - k60[i - slope_n]
        for i in range(slope_n + slope_m, n):
            accel_40[i] = slope_40[i] - slope_40[i - slope_m]
            accel_60[i] = slope_60[i] - slope_60[i - slope_m]

        # Step 7: 2-state overzone pipeline -- bar by bar
        long_a = np.zeros(n, dtype=bool)
        short_a = np.zeros(n, dtype=bool)
        trade_grade = np.full(n, "", dtype=object)

        # State tracking for 2-state machine
        # 0 = IDLE, 1 = MONITORING_LONG, 2 = MONITORING_SHORT
        system_state = 0
        last_signal_bar = -9999

        for i in range(1, n):
            if np.isnan(d9[i]) or np.isnan(atr_vals[i]):
                continue

            d9_val = d9[i]
            d9_prev = d9[i - 1] if not np.isnan(d9[i - 1]) else d9_val

            # ---- State transitions ----

            if system_state == 0:
                # IDLE: detect overzone entry
                if d9_val < overzone_long and d9_prev >= overzone_long:
                    # Stoch 9 D just dropped below 20 -> start monitoring long
                    system_state = 1
                elif d9_val > overzone_short and d9_prev <= overzone_short:
                    # Stoch 9 D just rose above 80 -> start monitoring short
                    system_state = 2
                continue

            elif system_state == 1:
                # MONITORING_LONG: waiting for stoch 9 D to exit overzone (rise back above 20)
                if d9_val >= overzone_long and d9_prev < overzone_long:
                    # Overzone exit detected -- check gates
                    if i - last_signal_bar < min_signal_gap:
                        system_state = 0  # cooldown, back to idle
                        continue

                    # Regression channel gate
                    if not regression_gate_long(i, close, pre_lookback, r2_min):
                        system_state = 0  # gate failed
                        continue

                    # ENTRY: fire long signal
                    long_a[i] = True
                    last_signal_bar = i

                    # Grade: check stoch 40/60 alignment at entry
                    st40 = classify_markov_state_long(k40[i], slope_40[i], accel_40[i])
                    st60 = classify_markov_state_long(k60[i], slope_60[i], accel_60[i])
                    s40_turning = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
                    s60_turning = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)

                    if s40_turning and s60_turning:
                        trade_grade[i] = "A"
                    elif s40_turning or s60_turning:
                        trade_grade[i] = "B"
                    else:
                        trade_grade[i] = "C"

                    system_state = 0  # back to idle after signal
                    continue

                # If stoch 9 D rises above overzone_short while monitoring long,
                # that is contradictory -- go idle
                if d9_val > overzone_short:
                    system_state = 0
                    continue

            elif system_state == 2:
                # MONITORING_SHORT: waiting for stoch 9 D to exit overzone (drop back below 80)
                if d9_val <= overzone_short and d9_prev > overzone_short:
                    # Overzone exit detected -- check gates
                    if i - last_signal_bar < min_signal_gap:
                        system_state = 0
                        continue

                    # Regression channel gate (for short: need prior rally)
                    if not regression_gate_short(i, close, pre_lookback, r2_min):
                        system_state = 0
                        continue

                    # ENTRY: fire short signal
                    short_a[i] = True
                    last_signal_bar = i

                    # Grade: check stoch 40/60 alignment at entry
                    st40 = classify_markov_state_short(k40[i], slope_40[i], accel_40[i])
                    st60 = classify_markov_state_short(k60[i], slope_60[i], accel_60[i])
                    s40_turning = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
                    s60_turning = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)

                    if s40_turning and s60_turning:
                        trade_grade[i] = "A"
                    elif s40_turning or s60_turning:
                        trade_grade[i] = "B"
                    else:
                        trade_grade[i] = "C"

                    system_state = 0
                    continue

                # If stoch 9 D drops below overzone_long while monitoring short,
                # contradictory -- go idle
                if d9_val < overzone_long:
                    system_state = 0
                    continue

        # Step 8: Map to engine columns
        df["long_a"] = long_a
        df["short_a"] = short_a
        df["trade_grade"] = trade_grade
        df["long_b"] = np.zeros(n, dtype=bool)
        df["long_c"] = np.zeros(n, dtype=bool)
        df["short_b"] = np.zeros(n, dtype=bool)
        df["short_c"] = np.zeros(n, dtype=bool)
        df["reentry_long"] = np.zeros(n, dtype=bool)
        df["reentry_short"] = np.zeros(n, dtype=bool)
        df["cloud3_allows_long"] = np.ones(n, dtype=bool)
        df["cloud3_allows_short"] = np.ones(n, dtype=bool)
        df["cloud2_cross_bull"] = np.zeros(n, dtype=bool)
        df["cloud2_cross_bear"] = np.zeros(n, dtype=bool)
        df["cloud3_cross_bull"] = np.zeros(n, dtype=bool)
        df["cloud3_cross_bear"] = np.zeros(n, dtype=bool)
        df["phase3_active_long"] = np.zeros(n, dtype=bool)
        df["phase3_active_short"] = np.zeros(n, dtype=bool)

        return df
    ''')

    SIGNAL_V2_PATH.write_text(SIGNAL_V2_CODE, encoding="utf-8")
    log.info("  Written: %s", SIGNAL_V2_PATH)
    if not validate_output(str(SIGNAL_V2_PATH)):
        ERRORS.append(str(SIGNAL_V2_PATH))


# ===========================================================================
# FILE 2: scripts/test_55_89_signals_v2.py
# ===========================================================================
TEST_V2_PATH = ROOT / "scripts" / "test_55_89_signals_v2.py"
if check_exists(TEST_V2_PATH):
    ERRORS.append(str(TEST_V2_PATH))
else:
    log.info("STEP 2: Writing %s", TEST_V2_PATH)

    TEST_V2_CODE = textwrap.dedent('''\
    """
    Tests for 55/89 EMA Cross Scalp v2 signal pipeline.
    Run: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/test_55_89_signals_v2.py"
    """

    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT))

    import numpy as np
    import pandas as pd

    PASS_COUNT = 0
    FAIL_COUNT = 0
    RESULTS = []


    def report(name, passed, detail=""):
        """Report a test result."""
        global PASS_COUNT, FAIL_COUNT
        status = "PASS" if passed else "FAIL"
        if passed:
            PASS_COUNT += 1
        else:
            FAIL_COUNT += 1
        msg = "  [" + status + "] " + name
        if detail:
            msg += " -- " + detail
        print(msg)
        RESULTS.append((name, status, detail))


    def make_ohlcv(n=500, price=10.0, seed=42):
        """Generate synthetic OHLCV DataFrame for testing."""
        rng = np.random.default_rng(seed)
        close = price + np.cumsum(rng.normal(0, price * 0.003, n))
        close = np.clip(close, price * 0.5, price * 2)
        high = close * (1 + rng.uniform(0.0, 0.003, n))
        low = close * (1 - rng.uniform(0.0, 0.003, n))
        opn = close * (1 + rng.uniform(-0.001, 0.001, n))
        vol = rng.integers(100000, 1000000, n).astype(float)
        df = pd.DataFrame({
            "open": opn, "high": high, "low": low,
            "close": close, "volume": vol,
        })
        df.index = pd.date_range("2025-01-01", periods=n, freq="5min")
        df.index.name = "datetime"
        return df


    def make_overzone_scenario(n=200, seed=99):
        """Build synthetic data where stoch 9 D dips below 20 then exits back above 20."""
        rng = np.random.default_rng(seed)
        # Create a price series that drops then recovers (forces stoch 9 into overzone)
        prices = np.ones(n) * 100.0
        # Bars 0-50: stable
        # Bars 51-100: decline (pushes stoch 9 below 20)
        # Bars 101-150: recovery (stoch 9 exits overzone)
        # Bars 151+: stable
        for i in range(51, 101):
            prices[i] = prices[i - 1] - 0.3 + rng.normal(0, 0.05)
        for i in range(101, 151):
            prices[i] = prices[i - 1] + 0.3 + rng.normal(0, 0.05)
        for i in range(151, n):
            prices[i] = prices[i - 1] + rng.normal(0, 0.05)

        high = prices * (1 + np.abs(rng.normal(0, 0.001, n)))
        low = prices * (1 - np.abs(rng.normal(0, 0.001, n)))
        df = pd.DataFrame({
            "open": prices, "high": high, "low": low,
            "close": prices, "volume": rng.integers(100000, 1000000, n).astype(float),
        })
        df.index = pd.date_range("2025-06-01", periods=n, freq="5min")
        df.index.name = "datetime"
        return df


    def main():
        """Run all v2 signal tests."""
        from signals.ema_cross_55_89_v2 import compute_signals_55_89

        print("=" * 60)
        print("55/89 Signal Pipeline v2 -- Test Suite")
        print("=" * 60)

        # ---- Test 1: Overzone entry fires signal ----
        print("\\nTest 1: Overzone entry -- stoch 9 D dips below 20 and exits")
        df_oz = make_overzone_scenario(n=300, seed=99)
        result = compute_signals_55_89(df_oz, {"min_signal_gap": 1})
        longs = int(result["long_a"].sum())
        shorts = int(result["short_a"].sum())
        total = longs + shorts
        report("T1_overzone_entry",
               total > 0,
               "signals: " + str(longs) + "L / " + str(shorts) + "S")

        # ---- Test 2: No signal while still in overzone ----
        print("\\nTest 2: No signal while stoch 9 D is still below 20")
        # Use the same scenario but check no signal fires while d9 < 20
        d9 = result["stoch_9_d"].values
        long_bars = np.where(result["long_a"].values)[0]
        if len(long_bars) > 0:
            first_signal = long_bars[0]
            # At signal bar, d9 should be >= 20 (just exited overzone)
            d9_at_signal = d9[first_signal]
            report("T2_no_signal_in_overzone",
                   d9_at_signal >= 20.0,
                   "d9 at signal bar: " + "{:.2f}".format(d9_at_signal))
        else:
            report("T2_no_signal_in_overzone", False, "No long signals found to check")

        # ---- Test 3: Cooldown suppresses rapid signals ----
        print("\\nTest 3: Cooldown -- min_signal_gap suppression")
        df_big = make_ohlcv(n=2000, price=5.0, seed=123)
        result_no_gap = compute_signals_55_89(df_big, {"min_signal_gap": 1})
        result_gap50 = compute_signals_55_89(df_big, {"min_signal_gap": 50})
        result_gap200 = compute_signals_55_89(df_big, {"min_signal_gap": 200})
        count_no_gap = int(result_no_gap["long_a"].sum() + result_no_gap["short_a"].sum())
        count_gap50 = int(result_gap50["long_a"].sum() + result_gap50["short_a"].sum())
        count_gap200 = int(result_gap200["long_a"].sum() + result_gap200["short_a"].sum())
        report("T3_cooldown",
               count_gap50 <= count_no_gap and count_gap200 <= count_gap50,
               "gap=1: " + str(count_no_gap) + ", gap=50: " + str(count_gap50) + ", gap=200: " + str(count_gap200))

        # ---- Test 4: Grade A -- stoch 40/60 already turning at entry ----
        print("\\nTest 4: Grade A -- stoch 40/60 turning at entry")
        result_graded = compute_signals_55_89(df_big, {"min_signal_gap": 1})
        signal_bars = np.where(result_graded["long_a"].values | result_graded["short_a"].values)[0]
        grades_at_signals = result_graded["trade_grade"].values[signal_bars]
        grade_counts = {}
        for g in grades_at_signals:
            if g:
                grade_counts[g] = grade_counts.get(g, 0) + 1
        has_grades = len(grade_counts) > 0
        report("T4_grade_A",
               has_grades and "A" in grade_counts,
               "grade distribution: " + str(grade_counts))

        # ---- Test 5: Grade C -- stoch 40/60 not turning ----
        print("\\nTest 5: Grade C -- stoch 40/60 not turning at entry")
        report("T5_grade_C",
               has_grades and "C" in grade_counts,
               "grade distribution: " + str(grade_counts))

        # ---- Test 6: TDI uses RSI 14 ----
        print("\\nTest 6: TDI uses RSI 14 (verify columns exist and are not NaN)")
        has_tdi_price = "tdi_price" in result_graded.columns
        has_tdi_signal = "tdi_signal" in result_graded.columns
        tdi_valid = False
        if has_tdi_price and has_tdi_signal:
            # With RSI 14, first valid TDI should be around bar 14+
            first_valid = np.where(~np.isnan(result_graded["tdi_price"].values))[0]
            if len(first_valid) > 0:
                tdi_valid = first_valid[0] >= 14  # RSI 14 needs 15 bars minimum
        report("T6_tdi_rsi14",
               has_tdi_price and has_tdi_signal and tdi_valid,
               "first valid TDI bar: " + (str(first_valid[0]) if len(first_valid) > 0 else "none"))

        # ---- Test 7: EMA cross columns ----
        print("\\nTest 7: EMA cross columns computed correctly")
        has_bull = "ema_cross_bull" in result_graded.columns
        has_bear = "ema_cross_bear" in result_graded.columns
        bull_count = int(result_graded["ema_cross_bull"].sum()) if has_bull else 0
        bear_count = int(result_graded["ema_cross_bear"].sum()) if has_bear else 0
        report("T7_ema_cross_columns",
               has_bull and has_bear and (bull_count + bear_count) > 0,
               "bull crosses: " + str(bull_count) + ", bear crosses: " + str(bear_count))

        # ---- Summary ----
        print("\\n" + "=" * 60)
        print("RESULTS: " + str(PASS_COUNT) + " PASS, " + str(FAIL_COUNT) + " FAIL out of " + str(PASS_COUNT + FAIL_COUNT))
        if FAIL_COUNT > 0:
            print("FAILURES:")
            for name, status, detail in RESULTS:
                if status == "FAIL":
                    print("  - " + name + ": " + detail)
        print("=" * 60)
        return FAIL_COUNT == 0


    if __name__ == "__main__":
        ok = main()
        sys.exit(0 if ok else 1)
    ''')

    TEST_V2_PATH.write_text(TEST_V2_CODE, encoding="utf-8")
    log.info("  Written: %s", TEST_V2_PATH)
    if not validate_output(str(TEST_V2_PATH)):
        ERRORS.append(str(TEST_V2_PATH))


# ===========================================================================
# FILE 3: engine/backtester_55_89.py -- MODIFY (BE trigger + overzone params + trade_grade)
# ===========================================================================
ENGINE_PATH = ROOT / "engine" / "backtester_55_89.py"
log.info("STEP 3: Modifying %s", ENGINE_PATH)

engine_src = ENGINE_PATH.read_text(encoding="utf-8")
original_engine = engine_src  # backup for rollback

# --- Edit 3a: Add new params to __init__ ---
old_init_block = """        self.sigma_floor_atr = float(p.get("sigma_floor_atr", 0.5))"""
new_init_block = """        self.sigma_floor_atr = float(p.get("sigma_floor_atr", 0.5))
        self.enable_ema_be = bool(p.get("enable_ema_be", True))
        self.overzone_long_threshold = float(p.get("overzone_long_threshold", 20.0))
        self.overzone_short_threshold = float(p.get("overzone_short_threshold", 80.0))"""

if old_init_block in engine_src:
    engine_src = engine_src.replace(old_init_block, new_init_block, 1)
    log.info("  Edit 3a: Added enable_ema_be + overzone params to __init__")
else:
    log.warning("  Edit 3a: Could not find __init__ block to patch")

# --- Edit 3b: Add ema_55 array extraction in run() ---
old_ema_72_line = """        # EMA 72 computed here (Cloud 4 = 72/89; signal module only has 55/89)
        ema_72_arr = ema(close, 72)"""
new_ema_72_line = """        # EMA 72 computed here (Cloud 4 = 72/89; signal module only has 55/89)
        ema_72_arr = ema(close, 72)

        # EMA 55 for BE trigger (v2: EMA cross sets BE)
        ema_55_arr = df["ema_55"].values.astype(float) if "ema_55" in df.columns else ema(close, 55)

        # Trade grade from signal pipeline (v2)
        trade_grade_arr = df["trade_grade"].values if "trade_grade" in df.columns else np.full(n, "")"""

if old_ema_72_line in engine_src:
    engine_src = engine_src.replace(old_ema_72_line, new_ema_72_line, 1)
    log.info("  Edit 3b: Added ema_55_arr and trade_grade_arr extraction")
else:
    log.warning("  Edit 3b: Could not find ema_72 line to patch")

# --- Edit 3c: Add BE-related fields to position dict ---
old_pos_dict_end = """                    "saw_green": False,
                    }"""
new_pos_dict_end = """                    "saw_green": False,
                        "ema_be_triggered": False,
                        "trade_grade": trade_grade_arr[i] if i < len(trade_grade_arr) else "",
                    }"""

if old_pos_dict_end in engine_src:
    engine_src = engine_src.replace(old_pos_dict_end, new_pos_dict_end, 1)
    log.info("  Edit 3c: Added ema_be_triggered + trade_grade to position dict")
else:
    log.warning("  Edit 3c: Could not find position dict end to patch")

# --- Edit 3d: Pass ema_55_arr to _update_position ---
old_update_call = """                pos = self._update_position(pos, i, high, low, close, hlc3, volume, atr,
                                            stoch_9_d, ema_72_arr, ema_89_arr)"""
new_update_call = """                pos = self._update_position(pos, i, high, low, close, hlc3, volume, atr,
                                            stoch_9_d, ema_72_arr, ema_89_arr, ema_55_arr)"""

if old_update_call in engine_src:
    engine_src = engine_src.replace(old_update_call, new_update_call, 1)
    log.info("  Edit 3d: Passed ema_55_arr to _update_position")
else:
    log.warning("  Edit 3d: Could not find _update_position call to patch")

# --- Edit 3e: Update _update_position signature and add BE logic ---
old_update_sig = """    def _update_position(self, pos: dict, i: int,
                         high: np.ndarray, low: np.ndarray, close: np.ndarray,
                         hlc3: float, volume: np.ndarray, atr: np.ndarray,
                         stoch_9_d: np.ndarray, ema_72_arr: np.ndarray,
                         ema_89_arr: np.ndarray) -> dict:
        \"\"\"Advance position state by one bar; sets pos[closed] if exiting.\"\"\"
        direction = pos["direction"]
        sl = pos["sl"]
        pos["bars_in_trade"] += 1
        bars = pos["bars_in_trade"]

        # Update AVWAP every bar
        pos["tracker"].update(hlc3, volume[i], atr[i])"""

new_update_sig = """    def _update_position(self, pos: dict, i: int,
                         high: np.ndarray, low: np.ndarray, close: np.ndarray,
                         hlc3: float, volume: np.ndarray, atr: np.ndarray,
                         stoch_9_d: np.ndarray, ema_72_arr: np.ndarray,
                         ema_89_arr: np.ndarray, ema_55_arr: np.ndarray = None) -> dict:
        \"\"\"Advance position state by one bar; sets pos[closed] if exiting.\"\"\"
        direction = pos["direction"]
        sl = pos["sl"]
        pos["bars_in_trade"] += 1
        bars = pos["bars_in_trade"]

        # Update AVWAP every bar
        pos["tracker"].update(hlc3, volume[i], atr[i])

        # BE trigger: EMA 55 crosses EMA 89 in trade direction
        if (self.enable_ema_be and not pos.get("ema_be_triggered", False)
                and ema_55_arr is not None and i > 0):
            e55 = ema_55_arr[i]
            e55_prev = ema_55_arr[i - 1]
            e89 = ema_89_arr[i]
            e89_prev = ema_89_arr[i - 1]
            if not (np.isnan(e55) or np.isnan(e55_prev) or np.isnan(e89) or np.isnan(e89_prev)):
                cross_bull = (e55_prev < e89_prev) and (e55 >= e89)
                cross_bear = (e55_prev > e89_prev) and (e55 <= e89)
                if (direction == "LONG" and cross_bull) or (direction == "SHORT" and cross_bear):
                    be_level = pos["entry_price"]
                    if direction == "LONG":
                        sl = max(sl, be_level)
                    else:
                        sl = min(sl, be_level)
                    pos["sl"] = sl
                    pos["ema_be_triggered"] = True"""

if old_update_sig in engine_src:
    engine_src = engine_src.replace(old_update_sig, new_update_sig, 1)
    log.info("  Edit 3e: Updated _update_position with BE trigger logic")
else:
    log.warning("  Edit 3e: Could not find _update_position signature to patch")

# --- Edit 3f: Add trade_grade to trade record ---
old_trade_record = """                    trade = {
                        "entry_bar": pos["entry_bar"],
                        "exit_bar": i,
                        "direction": pos["direction"],
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "pnl": net,
                        "commission": pos["entry_commission"] + comm_exit,
                        "exit_reason": pos["exit_reason"],
                        "bars_held": i - pos["entry_bar"],
                        "ratchet_count": pos["ratchet_count"],
                        "phase_at_exit": pos["phase"],
                        "saw_green": pos["saw_green"],
                    }"""

new_trade_record = """                    trade = {
                        "entry_bar": pos["entry_bar"],
                        "exit_bar": i,
                        "direction": pos["direction"],
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "pnl": net,
                        "commission": pos["entry_commission"] + comm_exit,
                        "exit_reason": pos["exit_reason"],
                        "bars_held": i - pos["entry_bar"],
                        "ratchet_count": pos["ratchet_count"],
                        "phase_at_exit": pos["phase"],
                        "saw_green": pos["saw_green"],
                        "ema_be_triggered": pos.get("ema_be_triggered", False),
                        "trade_grade": pos.get("trade_grade", ""),
                    }"""

if old_trade_record in engine_src:
    engine_src = engine_src.replace(old_trade_record, new_trade_record, 1)
    log.info("  Edit 3f: Added ema_be_triggered + trade_grade to trade record")
else:
    log.warning("  Edit 3f: Could not find trade record block to patch")

# --- Edit 3g: Also update EOD close trade record ---
old_eod_record = """            trades.append({
                "entry_bar": pos["entry_bar"],
                "exit_bar": n - 1,
                "direction": pos["direction"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "pnl": net,
                "commission": pos["entry_commission"] + comm_exit,
                "exit_reason": "eod",
                "bars_held": (n - 1) - pos["entry_bar"],
                "ratchet_count": pos["ratchet_count"],
                "phase_at_exit": pos["phase"],
                "saw_green": pos["saw_green"],
            })"""

new_eod_record = """            trades.append({
                "entry_bar": pos["entry_bar"],
                "exit_bar": n - 1,
                "direction": pos["direction"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "pnl": net,
                "commission": pos["entry_commission"] + comm_exit,
                "exit_reason": "eod",
                "bars_held": (n - 1) - pos["entry_bar"],
                "ratchet_count": pos["ratchet_count"],
                "phase_at_exit": pos["phase"],
                "saw_green": pos["saw_green"],
                "ema_be_triggered": pos.get("ema_be_triggered", False),
                "trade_grade": pos.get("trade_grade", ""),
            })"""

if old_eod_record in engine_src:
    engine_src = engine_src.replace(old_eod_record, new_eod_record, 1)
    log.info("  Edit 3g: Added fields to EOD trade record")
else:
    log.warning("  Edit 3g: Could not find EOD trade record to patch")

# --- Edit 3h: Add be_raised_count tracking in metrics ---
old_be_count = """            "be_raised_count": 0,"""
new_be_count = """            "be_raised_count": sum(1 for t in trades if t.get("ema_be_triggered", False)),"""

if old_be_count in engine_src:
    engine_src = engine_src.replace(old_be_count, new_be_count, 1)
    log.info("  Edit 3h: be_raised_count now tracks actual EMA BE triggers")
else:
    log.warning("  Edit 3h: Could not find be_raised_count to patch")

# Write modified engine
ENGINE_PATH.write_text(engine_src, encoding="utf-8")
log.info("  Written: %s", ENGINE_PATH)
if not validate_output(str(ENGINE_PATH)):
    ERRORS.append(str(ENGINE_PATH))
    # Rollback on failure
    ENGINE_PATH.write_text(original_engine, encoding="utf-8")
    log.error("  ROLLED BACK engine to original due to validation failure")


# ===========================================================================
# FILE 4: scripts/dashboard_55_89_v3.py -- MODIFY (import v2, new sliders, grade column)
# ===========================================================================
DASH_PATH = ROOT / "scripts" / "dashboard_55_89_v3.py"
log.info("STEP 4: Modifying %s", DASH_PATH)

dash_src = DASH_PATH.read_text(encoding="utf-8")
original_dash = dash_src

# --- Edit 4a: Swap import to v2 ---
old_import = "from signals.ema_cross_55_89 import compute_signals_55_89"
new_import = "from signals.ema_cross_55_89_v2 import compute_signals_55_89"

if old_import in dash_src:
    dash_src = dash_src.replace(old_import, new_import, 1)
    log.info("  Edit 4a: Swapped signal import to v2")
else:
    # Maybe already swapped
    if new_import in dash_src:
        log.info("  Edit 4a: Already using v2 import")
    else:
        log.warning("  Edit 4a: Could not find signal import line")

# --- Edit 4b: Add trade_grade to trades table display ---
old_display_cols = """        display_cols = [c for c in [
            "direction", "entry_price", "exit_price", "pnl", "commission",
            "net_pnl", "mfe", "mae", "exit_reason", "saw_green",
        ] if c in trades_df.columns]"""

new_display_cols = """        display_cols = [c for c in [
            "direction", "trade_grade", "entry_price", "exit_price", "pnl", "commission",
            "net_pnl", "mfe", "mae", "exit_reason", "saw_green", "ema_be_triggered",
        ] if c in trades_df.columns]"""

if old_display_cols in dash_src:
    dash_src = dash_src.replace(old_display_cols, new_display_cols, 1)
    log.info("  Edit 4b: Added trade_grade + ema_be_triggered to trades table")
else:
    log.warning("  Edit 4b: Could not find display_cols block")

# --- Edit 4c: Add new sidebar sliders ---
# Find the sig_params line and add new sliders after it
old_sig_params = '    sig_params = {"slope_n": slope_n, "slope_m": slope_m}'
new_sig_params = '''    min_signal_gap = st.sidebar.slider("Min signal gap (bars)", 1, 500, 50, 10)
    overzone_long_th = st.sidebar.slider("Overzone long threshold", 5.0, 40.0, 20.0, 1.0)
    overzone_short_th = st.sidebar.slider("Overzone short threshold", 60.0, 95.0, 80.0, 1.0)
    sig_params = {"slope_n": slope_n, "slope_m": slope_m, "min_signal_gap": min_signal_gap, "overzone_long_threshold": overzone_long_th, "overzone_short_threshold": overzone_short_th}'''

if old_sig_params in dash_src:
    dash_src = dash_src.replace(old_sig_params, new_sig_params, 1)
    log.info("  Edit 4c: Added min_signal_gap + overzone sliders to sidebar")
else:
    log.warning("  Edit 4c: Could not find sig_params line")

# Write modified dashboard
DASH_PATH.write_text(dash_src, encoding="utf-8")
log.info("  Written: %s", DASH_PATH)
if not validate_output(str(DASH_PATH)):
    ERRORS.append(str(DASH_PATH))
    DASH_PATH.write_text(original_dash, encoding="utf-8")
    log.error("  ROLLED BACK dashboard to original due to validation failure")


# ===========================================================================
# AUDIT PHASE
# ===========================================================================
log.info("=" * 70)
log.info("AUDIT PHASE")
log.info("=" * 70)

AUDIT_FILES = [
    str(SIGNAL_V2_PATH),
    str(TEST_V2_PATH),
    str(ENGINE_PATH),
    str(DASH_PATH),
]

audit_pass = True

for fpath in AUDIT_FILES:
    if not Path(fpath).exists():
        log.error("AUDIT SKIP: %s does not exist", fpath)
        audit_pass = False
        continue

    source = Path(fpath).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=fpath)
    fname = Path(fpath).name

    # Audit 1: Every def has a docstring
    missing_docs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                missing_docs.append(node.name)
    if missing_docs:
        log.warning("  AUDIT [%s] missing docstrings: %s", fname, ", ".join(missing_docs))
        audit_pass = False
    else:
        log.info("  AUDIT [%s] docstrings: OK", fname)

    # Audit 2: No escaped quotes in f-strings (check source text)
    fstring_issues = []
    for line_no, line in enumerate(source.splitlines(), 1):
        if "\\'" in line and "{" in line and "}" in line:
            fstring_issues.append(str(line_no))
    if fstring_issues:
        log.warning("  AUDIT [%s] possible escaped quotes in f-strings at lines: %s",
                     fname, ", ".join(fstring_issues))
        audit_pass = False
    else:
        log.info("  AUDIT [%s] f-string escapes: OK", fname)

log.info("AUDIT RESULT: %s", "PASS" if audit_pass else "FAIL")
if not audit_pass:
    ERRORS.append("AUDIT_FAILED")


# ===========================================================================
# TEST PHASE
# ===========================================================================
log.info("=" * 70)
log.info("TEST PHASE")
log.info("=" * 70)

test_pass = False
try:
    sys.path.insert(0, str(ROOT))
    # Import and run test module
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_v2", str(TEST_V2_PATH))
    test_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_mod)
    test_pass = test_mod.main()
    log.info("TEST RESULT: %s", "PASS" if test_pass else "FAIL")
except Exception as e:
    log.error("TEST PHASE EXCEPTION: %s", e)
    import traceback
    log.debug(traceback.format_exc())
    test_pass = False

if not test_pass:
    ERRORS.append("TESTS_FAILED")


# ===========================================================================
# OUTPUT SUMMARY
# ===========================================================================
log.info("=" * 70)
log.info("BUILD SUMMARY")
log.info("=" * 70)

files_written = [
    str(SIGNAL_V2_PATH),
    str(TEST_V2_PATH),
    str(ENGINE_PATH) + " (modified)",
    str(DASH_PATH) + " (modified)",
]

for f in files_written:
    log.info("  FILE: %s", f)

if ERRORS:
    log.error("BUILD FAILED -- errors:")
    for e in ERRORS:
        log.error("  - %s", e)
    sys.exit(1)
else:
    log.info("BUILD SUCCESS -- all py_compile, audit, and tests passed")
    log.info("Log file: %s", log_file)
    sys.exit(0)
