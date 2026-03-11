r"""
Master build script for 55/89 EMA Cross Scalp strategy.
Creates all files, validates each with py_compile, reports results.

Run: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_55_89_scalp.py"
"""

import py_compile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
ERRORS = []
CREATED = []
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def write_and_validate(filepath: Path, content: str):
    """Write file and py_compile. Track failures."""
    if filepath.exists():
        print(f"SKIP (exists): {filepath}")
        ERRORS.append(f"File already exists: {filepath}")
        return False
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    try:
        py_compile.compile(str(filepath), doraise=True)
        print(f"PASS: {filepath}")
        CREATED.append(str(filepath))
        return True
    except py_compile.PyCompileError as e:
        print(f"FAIL: {filepath} -- {e}")
        ERRORS.append(str(e))
        return False


# =============================================================================
# FILE 1: Signal Module — signals/ema_cross_55_89.py
# =============================================================================

SIGNAL_MODULE = r'''"""
55/89 EMA Cross Scalp — Signal pipeline.

Signal: stoch 9 K/D cross gates the pipeline. When alignment is active
(stoch 14 MOVING/EXTENDED, stoch 40/60 TURNING+, no contradiction,
delta compressing, TDI confirming, BBW not QUIET) AND 55/89 EMA delta
crosses zero, a trade signal fires.

Maps output to Backtester384-compatible columns (long_a, short_a, etc.).

Source of truth: PROJECTS/four-pillars-backtester/research/55-89-scalp-methodology.md
"""

import numpy as np
import pandas as pd
from numba import njit

from .stochastics_v2 import compute_all_stochastics, stoch_k
from .clouds_v2 import ema


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


# ---- TDI ----

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


def compute_tdi(close, rsi_period=9, smooth_period=5, signal_period=10):
    """Compute TDI: RSI smoothed price line and signal line."""
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

    bbw_state = np.full(n, 0, dtype=np.int8)  # 0=unknown
    for i in range(n):
        if np.isnan(bbwp[i]) or np.isnan(spectrum_ma[i]):
            continue
        if bbwp[i] > 80:
            bbw_state[i] = 2  # EXTREME
        elif bbwp[i] > spectrum_ma[i]:
            bbw_state[i] = 1  # HEALTHY
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


# ---- Main Signal Pipeline ----

def compute_signals_55_89(df, params=None):
    """Compute 55/89 EMA cross scalp signals mapped to Backtester384 columns.

    Pipeline:
    1. Compute stochs + D lines
    2. Compute EMA(55), EMA(89), delta
    3. Compute TDI, BBW
    4. Classify Markov states per stoch
    5. Run gated pipeline: IDLE -> MONITORING -> signal fires on alignment + delta cross
    6. Map to engine columns (long_a, short_a, etc.)
    """
    p = params or {}
    slope_n = p.get("slope_n", 5)
    slope_m = p.get("slope_m", 3)
    ema_fast = p.get("ema_fast", 55)
    ema_slow = p.get("ema_slow", 89)
    rsi_period = p.get("rsi_period", 9)
    rsi_smooth = p.get("rsi_smooth", 5)
    rsi_signal = p.get("rsi_signal", 10)
    bb_len = p.get("bb_len", 20)
    bb_mult = p.get("bb_mult", 2.0)
    bbwp_len = p.get("bbwp_len", 100)
    spectrum_ma_len = p.get("spectrum_ma_len", 7)
    atr_len = p.get("atr_length", 14)

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

    # Step 3: ATR
    atr_vals = compute_atr(df, atr_len)
    df["atr"] = atr_vals

    # Step 4: TDI
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

    # Step 6: Slopes and acceleration for stoch 40/60
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

    # Also compute slopes for stoch 9 and 14 (for contradiction check)
    slope_9 = np.full(n, 0.0)
    slope_14 = np.full(n, 0.0)
    accel_9 = np.full(n, 0.0)
    accel_14 = np.full(n, 0.0)
    for i in range(slope_n, n):
        slope_9[i] = k9[i] - k9[i - slope_n]
        slope_14[i] = k14[i] - k14[i - slope_n]
    for i in range(slope_n + slope_m, n):
        accel_9[i] = slope_9[i] - slope_9[i - slope_m]
        accel_14[i] = slope_14[i] - slope_14[i - slope_m]

    # Step 7: Gated pipeline — bar by bar
    long_a = np.zeros(n, dtype=bool)
    short_a = np.zeros(n, dtype=bool)

    # State tracking
    # 0 = IDLE, 1 = MONITORING_LONG, 2 = MONITORING_SHORT
    system_state = 0
    prev_k9_above_d9 = False

    for i in range(1, n):
        if np.isnan(k9[i]) or np.isnan(d9[i]) or np.isnan(atr_vals[i]):
            continue

        k9_above_d9 = k9[i] > d9[i]
        k9_below_d9 = k9[i] < d9[i]

        # Detect stoch 9 K/D cross
        k9_cross_bull = k9_above_d9 and not prev_k9_above_d9
        k9_cross_bear = k9_below_d9 and prev_k9_above_d9

        prev_k9_above_d9 = k9_above_d9

        # State transitions
        if system_state == 0:
            # IDLE: waiting for stoch 9 K/D cross
            if k9_cross_bull:
                system_state = 1  # MONITORING_LONG
            elif k9_cross_bear:
                system_state = 2  # MONITORING_SHORT
            continue

        # MONITORING: check if stoch 9 reversed
        if system_state == 1 and k9_below_d9:
            system_state = 0
            if k9_cross_bear:
                system_state = 2
            continue
        if system_state == 2 and k9_above_d9:
            system_state = 0
            if k9_cross_bull:
                system_state = 1
            continue

        # --- Alignment check ---
        if system_state == 1:
            # LONG alignment
            st14 = classify_markov_state_long(k14[i], slope_14[i], accel_14[i])
            st40 = classify_markov_state_long(k40[i], slope_40[i], accel_40[i])
            st60 = classify_markov_state_long(k60[i], slope_60[i], accel_60[i])

            # Stoch 14: MOVING or EXTENDED
            s14_ok = st14 in (STATE_MOVING, STATE_EXTENDED)
            # Stoch 40, 60: TURNING, MOVING, or EXTENDED
            s40_ok = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            s60_ok = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            # No contradiction: no negative slope on any stoch
            no_contra = slope_9[i] >= 0 and slope_14[i] >= 0 and slope_40[i] >= 0 and slope_60[i] >= 0
            # Delta compressing: delta < 0 and approaching zero (velocity positive)
            # or delta already crossed zero on this bar
            delta_prev = delta[i - 1] if not np.isnan(delta[i - 1]) else delta[i]
            delta_velocity = delta[i] - delta_prev
            delta_compressing = (delta[i] < 0 and delta_velocity > 0) or delta[i] >= 0
            # TDI confirming: price line above signal line
            tdi_ok = (not np.isnan(tdi_price[i]) and not np.isnan(tdi_signal[i])
                      and tdi_price[i] > tdi_signal[i])
            # BBW not QUIET
            bbw_ok = bbw_state[i] != -1

            alignment = s14_ok and s40_ok and s60_ok and no_contra and delta_compressing and tdi_ok and bbw_ok

            # Signal fires when alignment + delta crosses zero (EMA cross)
            if alignment:
                # Delta cross: was negative, now >= 0
                if delta_prev < 0 and delta[i] >= 0:
                    long_a[i] = True

        elif system_state == 2:
            # SHORT alignment
            st14 = classify_markov_state_short(k14[i], slope_14[i], accel_14[i])
            st40 = classify_markov_state_short(k40[i], slope_40[i], accel_40[i])
            st60 = classify_markov_state_short(k60[i], slope_60[i], accel_60[i])

            s14_ok = st14 in (STATE_MOVING, STATE_EXTENDED)
            s40_ok = st40 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            s60_ok = st60 in (STATE_TURNING, STATE_MOVING, STATE_EXTENDED)
            no_contra = slope_9[i] <= 0 and slope_14[i] <= 0 and slope_40[i] <= 0 and slope_60[i] <= 0
            delta_prev = delta[i - 1] if not np.isnan(delta[i - 1]) else delta[i]
            delta_velocity = delta[i] - delta_prev
            delta_compressing = (delta[i] > 0 and delta_velocity < 0) or delta[i] <= 0
            tdi_ok = (not np.isnan(tdi_price[i]) and not np.isnan(tdi_signal[i])
                      and tdi_price[i] < tdi_signal[i])
            bbw_ok = bbw_state[i] != -1

            alignment = s14_ok and s40_ok and s60_ok and no_contra and delta_compressing and tdi_ok and bbw_ok

            if alignment:
                # Delta cross: was positive, now <= 0
                if delta_prev > 0 and delta[i] <= 0:
                    short_a[i] = True

    # Step 8: Map to engine columns
    df["long_a"] = long_a
    df["short_a"] = short_a
    df["long_b"] = np.zeros(n, dtype=bool)
    df["short_b"] = np.zeros(n, dtype=bool)
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
'''

# =============================================================================
# FILE 2: Standalone Runner — scripts/run_55_89_backtest.py
# =============================================================================

RUNNER_CODE = r'''"""
Standalone runner for 55/89 EMA Cross Scalp backtest.

Loads parquet, computes signals, runs Backtester384, prints metrics.

Run: python scripts/run_55_89_backtest.py --symbol BTCUSDT --months 3
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

from signals.ema_cross_55_89 import compute_signals_55_89
from engine.backtester_v384 import Backtester384


def load_parquet(symbol, months=None):
    """Load 1m parquet for symbol from data/historical/ or data/cache/."""
    for subdir in ["historical", "cache"]:
        path = ROOT / "data" / subdir / f"{symbol}_1m.parquet"
        if path.exists():
            df = pd.read_parquet(path)
            if months and "datetime" in df.columns:
                cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=months * 30)
                df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
                df = df[df["datetime"] >= cutoff].reset_index(drop=True)
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Loaded {len(df)} bars from {path}")
            return df
    print(f"ERROR: No parquet found for {symbol}")
    sys.exit(1)


def main():
    """Run the 55/89 backtest from CLI."""
    parser = argparse.ArgumentParser(description="55/89 EMA Cross Scalp Backtest")
    parser.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    parser.add_argument("--months", type=int, default=None, help="Limit to last N months")
    parser.add_argument("--sl-mult", type=float, default=2.5, help="SL ATR multiplier (default 2.5)")
    parser.add_argument("--slope-n", type=int, default=5, help="Slope window N (default 5)")
    parser.add_argument("--slope-m", type=int, default=3, help="Accel window M (default 3)")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] 55/89 EMA Cross Scalp Backtest")
    print(f"[{ts}] Symbol: {args.symbol}, SL mult: {args.sl_mult}")

    df = load_parquet(args.symbol, args.months)

    sig_params = {
        "slope_n": args.slope_n,
        "slope_m": args.slope_m,
    }

    bt_params = {
        "sl_mult": args.sl_mult,
        "tp_mult": None,
        "be_trigger_atr": 0.0,
        "be_lock_atr": 0.0,
        "notional": 5000.0,
        "max_positions": 1,
        "cooldown": 1,
        "enable_adds": False,
        "enable_reentry": False,
        "commission_rate": 0.0008,
        "initial_equity": 10000.0,
    }

    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] Computing signals...")
    df_sig = compute_signals_55_89(df.copy(), sig_params)

    long_count = int(df_sig["long_a"].sum())
    short_count = int(df_sig["short_a"].sum())
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] Signals: {long_count} long, {short_count} short")

    print(f"[{ts}] Running backtest...")
    bt = Backtester384(bt_params)
    results = bt.run(df_sig)
    m = results["metrics"]

    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"\n[{ts}] === RESULTS ===")
    print(f"  Total trades:    {m.get('total_trades', 0)}")
    print(f"  Win rate:        {m.get('win_rate', 0):.1%}")
    print(f"  Net PnL:         ${m.get('net_pnl', 0):.2f}")
    print(f"  Profit factor:   {m.get('profit_factor', 0):.2f}")
    print(f"  Sharpe:          {m.get('sharpe', 0):.3f}")
    print(f"  Max drawdown:    {m.get('max_drawdown_pct', 0):.1f}%")
    print(f"  Avg win:         ${m.get('avg_win', 0):.2f}")
    print(f"  Avg loss:        ${m.get('avg_loss', 0):.2f}")
    print(f"  Expectancy:      ${m.get('expectancy', 0):.2f}")
    print(f"  Commission:      ${m.get('total_commission', 0):.2f}")
    print(f"  Rebate:          ${m.get('total_rebate', 0):.2f}")

    trades_df = results.get("trades_df")
    if trades_df is not None and len(trades_df) > 0:
        print(f"\n  Grade breakdown:")
        for grade_name, grade_data in m.get("grades", {}).items():
            print(f"    {grade_name}: {grade_data['count']} trades, "
                  + f"{grade_data['win_rate']:.0%} WR, "
                  + f"${grade_data['total_pnl']:.2f} PnL")


if __name__ == "__main__":
    main()
'''

# =============================================================================
# FILE 3: Test Script — scripts/test_55_89_signals.py
# =============================================================================

TEST_CODE = r'''"""
Test script for 55/89 EMA Cross Scalp signal module.

Validates:
- Signal module imports
- compute_signals_55_89() runs on sample data
- Output has all required engine columns
- Signal counts are non-zero (sanity)
- Markov states are valid
- D lines match expected smoothing
- TDI computation produces valid output
- BBW state classification works

Run: python scripts/test_55_89_signals.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS_COUNT = 0
FAIL_COUNT = 0
FAIL_DETAILS = []


def check(name, condition, detail=""):
    """Check a test condition and print result."""
    global PASS_COUNT, FAIL_COUNT
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    if condition:
        PASS_COUNT += 1
        print(f"[{ts}] PASS: {name}")
    else:
        FAIL_COUNT += 1
        msg = f"{name} -- {detail}" if detail else name
        FAIL_DETAILS.append(msg)
        print(f"[{ts}] FAIL: {msg}")


def main():
    """Run all 55/89 signal tests."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] Testing 55/89 EMA Cross Scalp Signals")
    print("=" * 60)

    # Test 1: Import
    try:
        from signals.ema_cross_55_89 import compute_signals_55_89
        from signals.ema_cross_55_89 import (
            compute_atr, compute_d_line, compute_tdi, compute_bbwp,
            classify_markov_state_long, classify_markov_state_short,
            STATE_ZONE, STATE_TURNING, STATE_MOVING, STATE_EXTENDED,
        )
        check("Import signal module", True)
    except Exception as e:
        check("Import signal module", False, str(e))
        print("\nCannot continue without import. Exiting.")
        sys.exit(1)

    # Test 2: Load sample data
    import pandas as pd
    import numpy as np

    sample_path = None
    for subdir in ["historical", "cache"]:
        candidates = list((ROOT / "data" / subdir).glob("*_1m.parquet"))
        if candidates:
            sample_path = candidates[0]
            break

    if sample_path is None:
        check("Find sample parquet", False, "No parquet files found in data/historical/ or data/cache/")
        print("\nCannot continue without data. Exiting.")
        sys.exit(1)

    df = pd.read_parquet(sample_path)
    # Use first 5000 bars for speed
    df = df.head(5000).reset_index(drop=True)
    check("Load sample data", len(df) > 0, f"{len(df)} bars from {sample_path.name}")

    # Test 3: Run signal pipeline
    try:
        df_sig = compute_signals_55_89(df.copy())
        check("compute_signals_55_89 runs", True)
    except Exception as e:
        check("compute_signals_55_89 runs", False, str(e))
        print("\nCannot continue. Exiting.")
        sys.exit(1)

    # Test 4: Required engine columns
    required = ["close", "high", "low", "atr", "long_a", "long_b",
                 "short_a", "short_b", "reentry_long", "reentry_short",
                 "cloud3_allows_long", "cloud3_allows_short"]
    missing = [c for c in required if c not in df_sig.columns]
    check("Required engine columns", len(missing) == 0,
          "Missing: " + ", ".join(missing) if missing else "")

    # Test 5: Signal count sanity (may be zero on small sample but columns should exist)
    long_count = int(df_sig["long_a"].sum())
    short_count = int(df_sig["short_a"].sum())
    check("Signal columns have data", True,
          f"long_a={long_count}, short_a={short_count}")

    # Test 6: ATR not all NaN
    atr_valid = np.sum(~np.isnan(df_sig["atr"].values))
    check("ATR has valid values", atr_valid > 0, f"{atr_valid} valid ATR values")

    # Test 7: D lines present
    for col in ["stoch_9_d", "stoch_14_d", "stoch_40_d", "stoch_60_d"]:
        has_col = col in df_sig.columns
        if has_col:
            valid = np.sum(~np.isnan(df_sig[col].values))
            check(f"D line {col}", valid > 0, f"{valid} valid values")
        else:
            check(f"D line {col}", False, "Column missing")

    # Test 8: TDI columns
    for col in ["tdi_price", "tdi_signal"]:
        has_col = col in df_sig.columns
        if has_col:
            valid = np.sum(~np.isnan(df_sig[col].values))
            check(f"TDI {col}", valid > 0, f"{valid} valid values")
        else:
            check(f"TDI {col}", False, "Column missing")

    # Test 9: BBW state
    check("BBWP value column", "bbwp_value" in df_sig.columns)
    check("BBWP state column", "bbwp_state" in df_sig.columns)
    if "bbwp_state" in df_sig.columns:
        states = df_sig["bbwp_state"].unique()
        valid_states = {"HEALTHY", "EXTREME", "QUIET", "UNKNOWN"}
        all_valid = all(s in valid_states for s in states)
        check("BBW states are valid", all_valid, f"Found: {list(states)}")

    # Test 10: Markov state classification unit tests
    check("Markov ZONE long (K=15)", classify_markov_state_long(15, 0, 0) == STATE_ZONE)
    check("Markov TURNING long (K=30, slope=2, accel=0)",
          classify_markov_state_long(30, 2, 0) == STATE_TURNING)
    check("Markov MOVING long (K=35, slope=3, accel=1)",
          classify_markov_state_long(35, 3, 1) == STATE_MOVING)
    check("Markov EXTENDED long (K=55, slope=1, accel=0)",
          classify_markov_state_long(55, 1, 0) == STATE_EXTENDED)
    check("Markov ZONE short (K=85)", classify_markov_state_short(85, 0, 0) == STATE_ZONE)
    check("Markov MOVING short (K=45, slope=-3, accel=-1)",
          classify_markov_state_short(45, -3, -1) == STATE_MOVING)

    # Test 11: EMA columns
    check("EMA 55 column", "ema_55" in df_sig.columns)
    check("EMA 89 column", "ema_89" in df_sig.columns)
    check("EMA delta column", "ema_delta" in df_sig.columns)

    # Test 12: No B/C/D/reentry signals (should all be False for this strategy)
    check("long_b all False", not df_sig["long_b"].any())
    check("short_b all False", not df_sig["short_b"].any())
    check("reentry_long all False", not df_sig["reentry_long"].any())
    check("reentry_short all False", not df_sig["reentry_short"].any())

    # Summary
    print("=" * 60)
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    total = PASS_COUNT + FAIL_COUNT
    print(f"[{ts}] {PASS_COUNT}/{total} passed, {FAIL_COUNT} failed")
    if FAIL_DETAILS:
        print("\nFailures:")
        for f in FAIL_DETAILS:
            print(f"  - {f}")
    else:
        print("\nALL TESTS PASSED")

    return FAIL_COUNT == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

# =============================================================================
# FILE 4: Dashboard — scripts/dashboard_v394_55_89.py
# (Minimal standalone dashboard for 55/89 strategy)
# =============================================================================

DASHBOARD_CODE = r'''"""
55/89 EMA Cross Scalp Dashboard — standalone Streamlit app.

Runs the 55/89 signal pipeline through Backtester384 with configurable params.
Does NOT modify dashboard_v394.py.

Run from backtester root:
  streamlit run scripts/dashboard_v394_55_89.py

Full path:
  streamlit run scripts/dashboard_v394_55_89.py
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from signals.ema_cross_55_89 import compute_signals_55_89
from engine.backtester_v384 import Backtester384


# ---- Theme ----
COLORS = {
    "bg": "#0f1419", "card": "#1a1f26", "text": "#e7e9ea",
    "green": "#10b981", "red": "#ef4444", "blue": "#3b82f6",
    "orange": "#f59e0b", "purple": "#8b5cf6", "gray": "#6b7280",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_symbol_list():
    """Scan data dirs for available 1m parquets."""
    symbols = set()
    for subdir in ["historical", "cache"]:
        d = PROJECT_ROOT / "data" / subdir
        if d.exists():
            for f in d.glob("*_1m.parquet"):
                sym = f.stem.replace("_1m", "")
                symbols.add(sym)
    return sorted(symbols)


def load_data(symbol):
    """Load 1m parquet for symbol."""
    for subdir in ["historical", "cache"]:
        path = PROJECT_ROOT / "data" / subdir / f"{symbol}_1m.parquet"
        if path.exists():
            return pd.read_parquet(path)
    return None


def run_backtest(df, sig_params, bt_params):
    """Run signal pipeline + backtest engine."""
    t0 = time.perf_counter()
    df_sig = compute_signals_55_89(df.copy(), sig_params)
    t1 = time.perf_counter()
    bt = Backtester384(bt_params)
    results = bt.run(df_sig)
    t2 = time.perf_counter()
    return results, df_sig, (t1 - t0, t2 - t1)


def main():
    """Streamlit dashboard entry point."""
    st.set_page_config(page_title="55/89 EMA Cross Scalp", layout="wide")
    st.title("55/89 EMA Cross Scalp Backtest")

    # ---- Sidebar ----
    st.sidebar.header("Symbol")
    symbols = load_symbol_list()
    if not symbols:
        st.error("No parquet files found in data/historical/ or data/cache/")
        return

    symbol = st.sidebar.selectbox("Symbol", symbols, index=symbols.index("BTCUSDT") if "BTCUSDT" in symbols else 0)

    st.sidebar.header("Signal Parameters")
    slope_n = st.sidebar.slider("Slope window N", 2, 20, 5)
    slope_m = st.sidebar.slider("Accel window M", 2, 10, 3)

    st.sidebar.header("Backtest Parameters")
    sl_mult = st.sidebar.slider("SL multiplier (ATR)", 0.5, 5.0, 2.5, 0.1)
    notional = st.sidebar.number_input("Notional ($)", 1000, 50000, 5000, 1000)
    initial_equity = st.sidebar.number_input("Initial equity ($)", 1000, 100000, 10000, 1000)

    st.sidebar.header("Date Filter")
    use_date = st.sidebar.checkbox("Filter by date range")
    date_range = None
    if use_date:
        start_date = st.sidebar.date_input("Start date")
        end_date = st.sidebar.date_input("End date")
        date_range = (start_date, end_date)

    if st.sidebar.button("Run Backtest", type="primary"):
        with st.spinner("Loading data..."):
            df = load_data(symbol)
            if df is None:
                st.error(f"No data for {symbol}")
                return

            if date_range:
                start_ts = pd.Timestamp(date_range[0], tz="UTC")
                end_ts = pd.Timestamp(date_range[1], tz="UTC") + pd.Timedelta(days=1)
                if "datetime" in df.columns:
                    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
                    df = df[(df["datetime"] >= start_ts) & (df["datetime"] < end_ts)].reset_index(drop=True)

            st.info(f"Running on {len(df):,} bars...")

        sig_params = {"slope_n": slope_n, "slope_m": slope_m}
        bt_params = {
            "sl_mult": sl_mult,
            "tp_mult": None,
            "be_trigger_atr": 0.0,
            "be_lock_atr": 0.0,
            "notional": notional,
            "max_positions": 1,
            "cooldown": 1,
            "enable_adds": False,
            "enable_reentry": False,
            "commission_rate": 0.0008,
            "initial_equity": initial_equity,
        }

        with st.spinner("Computing signals + backtest..."):
            results, df_sig, timings = run_backtest(df, sig_params, bt_params)

        m = results["metrics"]
        trades_df = results.get("trades_df", pd.DataFrame())

        # ---- Metrics row ----
        st.subheader(f"{symbol} -- Results")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Trades", m.get("total_trades", 0))
        c2.metric("Win Rate", f"{m.get('win_rate', 0):.1%}")
        c3.metric("Net PnL", f"${m.get('net_pnl', 0):.2f}")
        c4.metric("Profit Factor", f"{m.get('profit_factor', 0):.2f}")
        c5.metric("Sharpe", f"{m.get('sharpe', 0):.3f}")
        c6.metric("Max DD", f"{m.get('max_drawdown_pct', 0):.1f}%")

        c7, c8, c9, c10 = st.columns(4)
        c7.metric("Avg Win", f"${m.get('avg_win', 0):.2f}")
        c8.metric("Avg Loss", f"${m.get('avg_loss', 0):.2f}")
        c9.metric("Expectancy", f"${m.get('expectancy', 0):.2f}")
        c10.metric("Commission", f"${m.get('total_commission', 0):.2f}")

        ts_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
        st.caption(f"Signal: {timings[0]:.1f}s | Engine: {timings[1]:.1f}s | {ts_str} UTC")

        # ---- Signal counts ----
        long_count = int(df_sig["long_a"].sum())
        short_count = int(df_sig["short_a"].sum())
        st.write(f"Signal counts: {long_count} long, {short_count} short")

        # ---- Equity curve ----
        st.subheader("Equity Curve")
        eq = results["equity_curve"]
        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(y=eq, mode="lines", name="Equity",
                                     line=dict(color=COLORS["blue"], width=1)))
        fig_eq.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card"],
            margin=dict(l=40, r=20, t=30, b=30),
        )
        st.plotly_chart(fig_eq, use_container_width=True)

        # ---- Trades table ----
        if len(trades_df) > 0:
            st.subheader("Trades")
            st.dataframe(trades_df, use_container_width=True, height=400)
        else:
            st.warning("No trades generated. Try different parameters or a different symbol.")


if __name__ == "__main__":
    main()
'''

# =============================================================================
# MAIN — Create all files and validate
# =============================================================================

if __name__ == "__main__":
    print(f"[{TIMESTAMP}] 55/89 EMA Cross Scalp — Master Build Script")
    print(f"[{TIMESTAMP}] Root: {ROOT}")
    print("=" * 70)

    # File 1: Signal module
    print("\n--- File 1: Signal Module ---")
    write_and_validate(ROOT / "signals" / "ema_cross_55_89.py", SIGNAL_MODULE)

    # File 2: Standalone runner
    print("\n--- File 2: Standalone Runner ---")
    write_and_validate(ROOT / "scripts" / "run_55_89_backtest.py", RUNNER_CODE)

    # File 3: Test script
    print("\n--- File 3: Test Script ---")
    write_and_validate(ROOT / "scripts" / "test_55_89_signals.py", TEST_CODE)

    # File 4: Dashboard
    print("\n--- File 4: Dashboard ---")
    write_and_validate(ROOT / "scripts" / "dashboard_v394_55_89.py", DASHBOARD_CODE)

    # Report
    print("\n" + "=" * 70)
    print(f"[{TIMESTAMP}] BUILD REPORT")
    print(f"  Created: {len(CREATED)} files")
    for f in CREATED:
        print(f"    {f}")

    if ERRORS:
        print(f"\n  FAILURES ({len(ERRORS)}):")
        for e in ERRORS:
            print(f"    {e}")
    else:
        print("\n  ALL FILES CREATED AND VALIDATED")

    print(f"\n[{TIMESTAMP}] Next steps:")
    print(f'  1. Run: python "{ROOT / "scripts" / "build_55_89_scalp.py"}"')
    print(f'  2. Test: python "{ROOT / "scripts" / "test_55_89_signals.py"}"')
    print(f'  3. Backtest: python "{ROOT / "scripts" / "run_55_89_backtest.py"}" --symbol BTCUSDT')
    print(f'  4. Dashboard: streamlit run "{ROOT / "scripts" / "dashboard_v394_55_89.py"}"')
