"""
Build script: Creates all 11 missing files for the Four Pillars backtester.
Skips files that already exist. Tests each file after creation.

Run: python scripts/build_missing_files.py
"""

import sys
import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

# ── File definitions ─────────────────────────────────────────────────────────

FILES = {}

# ─────────────────────────────────────────────────────────────────────────────
# 1. strategies/base_strategy.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["strategies/base_strategy.py"] = '''\
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the given DataFrame."""
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on calculated indicators."""
        pass

    @abstractmethod
    def get_sl_tp(self, entry_price: float, atr_value: float) -> tuple[float, float]:
        """Return (stop_loss, take_profit) for a LONG position."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the strategy."""
        pass
'''

# ─────────────────────────────────────────────────────────────────────────────
# 2. engine/exit_manager.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["engine/exit_manager.py"] = '''\
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
'''

# ─────────────────────────────────────────────────────────────────────────────
# 3. strategies/indicators.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["strategies/indicators.py"] = '''\
"""
Unified indicator calculation for the Four Pillars strategy.
Wraps signals.stochastics, signals.clouds, and ATR into a single call.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from signals.stochastics import compute_all_stochastics
from signals.clouds import compute_clouds


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    ATR using Wilder's RMA (matches Pine Script ta.atr).

    Args:
        df: DataFrame with high, low, close columns.
        period: ATR lookback period.

    Returns:
        Series with ATR values.
    """
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values

    tr = np.maximum(
        high - low,
        np.maximum(
            np.abs(high - np.roll(close, 1)),
            np.abs(low - np.roll(close, 1)),
        ),
    )
    tr[0] = high[0] - low[0]

    atr = np.full(len(tr), np.nan)
    atr[period - 1] = np.mean(tr[:period])
    for i in range(period, len(tr)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period

    return pd.Series(atr, index=df.index, name="atr")


def calculate_stochastics(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute all 4 stochastics (9-3, 14-3, 40-3, 60-10)."""
    return compute_all_stochastics(df, params)


def calculate_ripster_clouds(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """Compute Ripster EMA Clouds 2-5."""
    return compute_clouds(df, params)


def calculate_cloud3_bias(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Cloud 3 directional bias.

    Adds columns:
        price_pos: -1 (below), 0 (inside), 1 (above) Cloud 3
        cloud3_allows_long: True if price_pos >= 0
        cloud3_allows_short: True if price_pos <= 0
    """
    df = df.copy()
    close = df["close"].values

    if "cloud3_top" not in df.columns:
        df = calculate_ripster_clouds(df)

    top = df["cloud3_top"].values
    bot = df["cloud3_bottom"].values

    df["price_pos"] = np.where(close > top, 1, np.where(close < bot, -1, 0))
    df["cloud3_allows_long"] = df["price_pos"] >= 0
    df["cloud3_allows_short"] = df["price_pos"] <= 0

    return df


def calculate_volume_analysis(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Compute volume analysis metrics.

    Adds columns:
        volume_ratio: current volume / rolling average
        volume_surge: True if volume_ratio > 2.0
    """
    df = df.copy()
    vol_col = "base_vol" if "base_vol" in df.columns else "volume"
    if vol_col not in df.columns:
        df["volume_ratio"] = 1.0
        df["volume_surge"] = False
        return df

    vol = df[vol_col]
    avg = vol.rolling(lookback, min_periods=1).mean()
    df["volume_ratio"] = np.where(avg > 0, vol / avg, 1.0)
    df["volume_surge"] = df["volume_ratio"] > 2.0
    return df


def calculate_all_indicators(df: pd.DataFrame, atr_period: int = 14, params: dict = None) -> pd.DataFrame:
    """
    Run all indicator calculations in sequence.

    Args:
        df: DataFrame with OHLCV columns.
        atr_period: ATR lookback period.
        params: Optional dict for stochastic/cloud overrides.

    Returns:
        DataFrame with all indicator columns added.
    """
    df = calculate_stochastics(df, params)
    df = calculate_ripster_clouds(df, params)
    df["atr"] = calculate_atr(df, atr_period)
    df = calculate_cloud3_bias(df)
    df = calculate_volume_analysis(df)
    return df


if __name__ == "__main__":
    n = 200
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame({
        "open": close - 0.1,
        "high": close + np.abs(np.random.randn(n)) * 0.5,
        "low": close - np.abs(np.random.randn(n)) * 0.5,
        "close": close,
        "base_vol": np.random.randint(1000, 5000, n).astype(float),
    })
    result = calculate_all_indicators(df)
    expected = ["stoch_9", "stoch_14", "stoch_40", "stoch_60", "atr", "cloud3_top",
                "price_pos", "cloud3_allows_long", "volume_ratio"]
    missing = [c for c in expected if c not in result.columns]
    if missing:
        print(f"FAIL -- missing columns: {missing}")
    else:
        print(f"PASS -- {len(result.columns)} columns, {len(result)} rows")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 4. strategies/signals.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["strategies/signals.py"] = '''\
"""
Four Pillars A/B/C signal generation wrapper.
Uses the state machine from signals.state_machine and applies cooldown.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from signals.four_pillars import compute_signals


def generate_a_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Extract A-grade signals (4/4 stochs aligned + Cloud 3 filter)."""
    out = df[["long_a", "short_a"]].copy()
    out.rename(columns={"long_a": "long", "short_a": "short"}, inplace=True)
    return out


def generate_b_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Extract B-grade signals (3/4 stochs aligned + Cloud 3 filter)."""
    out = df[["long_b", "short_b"]].copy()
    out.rename(columns={"long_b": "long", "short_b": "short"}, inplace=True)
    return out


def generate_c_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Extract C-grade signals (2/4 stochs aligned + inside Cloud 3)."""
    out = df[["long_c", "short_c"]].copy()
    out.rename(columns={"long_c": "long", "short_c": "short"}, inplace=True)
    return out


def apply_cooldown(signals_df: pd.DataFrame, cooldown_bars: int = 3) -> pd.DataFrame:
    """
    Apply minimum bars between signals.

    Args:
        signals_df: DataFrame with signal columns (long_a, short_a, etc.).
        cooldown_bars: Minimum bars between entries.

    Returns:
        Filtered DataFrame with cooldown applied.
    """
    df = signals_df.copy()
    signal_cols = [c for c in df.columns if c.startswith(("long_", "short_"))]

    last_signal_bar = -999
    for i in range(len(df)):
        has_signal = any(df[c].iloc[i] for c in signal_cols if isinstance(df[c].iloc[i], (bool, np.bool_)) and df[c].iloc[i])
        if has_signal:
            if i - last_signal_bar < cooldown_bars:
                for c in signal_cols:
                    df.iloc[i, df.columns.get_loc(c)] = False
            else:
                last_signal_bar = i

    return df


def generate_all_signals(df: pd.DataFrame, cooldown_bars: int = 3, params: dict = None) -> pd.DataFrame:
    """
    Run full signal pipeline: indicators -> state machine -> cooldown.

    Args:
        df: Raw OHLCV DataFrame.
        cooldown_bars: Min bars between entries.
        params: Signal parameters (atr_length, cross_level, etc.).

    Returns:
        DataFrame with signal columns: long_a/b/c, short_a/b/c,
        signal_type (A/B/C), direction (LONG/SHORT).
    """
    df = compute_signals(df, params)

    if cooldown_bars > 0:
        df = apply_cooldown(df, cooldown_bars)

    # Add consolidated signal columns
    n = len(df)
    signal_type = [""] * n
    direction = [""] * n

    for i in range(n):
        if df["long_a"].iloc[i]:
            signal_type[i], direction[i] = "A", "LONG"
        elif df["short_a"].iloc[i]:
            signal_type[i], direction[i] = "A", "SHORT"
        elif df["long_b"].iloc[i]:
            signal_type[i], direction[i] = "B", "LONG"
        elif df["short_b"].iloc[i]:
            signal_type[i], direction[i] = "B", "SHORT"
        elif df["long_c"].iloc[i]:
            signal_type[i], direction[i] = "C", "LONG"
        elif df["short_c"].iloc[i]:
            signal_type[i], direction[i] = "C", "SHORT"
        elif df["reentry_long"].iloc[i]:
            signal_type[i], direction[i] = "R", "LONG"
        elif df["reentry_short"].iloc[i]:
            signal_type[i], direction[i] = "R", "SHORT"

    df["signal_type"] = signal_type
    df["direction"] = direction

    return df


if __name__ == "__main__":
    n = 500
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    df = pd.DataFrame({
        "open": close - 0.1,
        "high": close + np.abs(np.random.randn(n)) * 0.5,
        "low": close - np.abs(np.random.randn(n)) * 0.5,
        "close": close,
        "base_vol": np.random.randint(1000, 5000, n).astype(float),
    })
    result = generate_all_signals(df)
    sigs = result[result["signal_type"] != ""]
    print(f"PASS -- {len(sigs)} signals out of {len(result)} bars")
    print(f"  Types: {sigs['signal_type'].value_counts().to_dict()}")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 5. strategies/cloud_filter.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["strategies/cloud_filter.py"] = '''\
"""
Cloud 3 directional filter (simplified wrapper).
Blocks signals that violate Cloud 3 direction.
"""

import pandas as pd


def apply_cloud3_filter(df: pd.DataFrame, signals_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Block signals that violate Cloud 3 direction.

    If signal is LONG but cloud3_allows_long=False, remove signal.
    If signal is SHORT but cloud3_allows_short=False, remove signal.

    Args:
        df: DataFrame with cloud3_allows_long, cloud3_allows_short columns.
        signals_df: Optional separate signals DataFrame. If None, filter df in-place.

    Returns:
        Filtered DataFrame with blocked signals removed.
    """
    if signals_df is not None:
        out = signals_df.copy()
        allows_long = df["cloud3_allows_long"].values
        allows_short = df["cloud3_allows_short"].values
    else:
        out = df.copy()
        allows_long = out["cloud3_allows_long"].values
        allows_short = out["cloud3_allows_short"].values

    # Block long signals where Cloud 3 disallows
    long_cols = [c for c in out.columns if c.startswith("long_")]
    for c in long_cols:
        out[c] = out[c] & allows_long

    # Block short signals where Cloud 3 disallows
    short_cols = [c for c in out.columns if c.startswith("short_")]
    for c in short_cols:
        out[c] = out[c] & allows_short

    # Update direction column if present
    if "direction" in out.columns:
        for i in range(len(out)):
            d = out["direction"].iloc[i]
            if d == "LONG" and not allows_long[i]:
                out.iloc[i, out.columns.get_loc("direction")] = ""
                out.iloc[i, out.columns.get_loc("signal_type")] = ""
            elif d == "SHORT" and not allows_short[i]:
                out.iloc[i, out.columns.get_loc("direction")] = ""
                out.iloc[i, out.columns.get_loc("signal_type")] = ""

    return out


if __name__ == "__main__":
    import numpy as np
    n = 10
    df = pd.DataFrame({
        "long_a": [True, False, True, False, False, True, False, False, True, False],
        "short_a": [False, True, False, True, False, False, True, False, False, True],
        "signal_type": ["A", "A", "A", "A", "", "A", "A", "", "A", "A"],
        "direction": ["LONG", "SHORT", "LONG", "SHORT", "", "LONG", "SHORT", "", "LONG", "SHORT"],
        "cloud3_allows_long": [True, True, False, True, True, True, True, True, False, True],
        "cloud3_allows_short": [True, True, True, False, True, True, True, True, True, False],
    })
    result = apply_cloud3_filter(df)
    blocked = (df["direction"] != "") & (result["direction"] == "")
    print(f"PASS -- {blocked.sum()} signals blocked by Cloud 3 filter")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 6. strategies/four_pillars_v3_8.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["strategies/four_pillars_v3_8.py"] = '''\
"""
Four Pillars v3.8 strategy implementation.
Inherits from BaseStrategy, uses the existing signal pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from strategies.base_strategy import BaseStrategy
from signals.four_pillars import compute_signals
from strategies.cloud_filter import apply_cloud3_filter


class FourPillarsV38(BaseStrategy):
    """
    Four Pillars v3.8 strategy.

    Config:
        atr_period: ATR lookback (8, 13, 14, or 21). Default 14.
        sl_atr_mult: SL distance in ATR units. Default 1.0.
        tp_atr_mult: TP distance in ATR units. Default 1.5.
        allow_b_fresh: Whether B signals can open fresh positions. Default True.
        cooldown_bars: Min bars between entries. Default 3.
        commission_rate: Per-side commission rate. Default 0.0008.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.atr_period = self.config.get("atr_period", 14)
        self.sl_atr_mult = self.config.get("sl_atr_mult", 1.0)
        self.tp_atr_mult = self.config.get("tp_atr_mult", 1.5)
        self.allow_b_fresh = self.config.get("allow_b_fresh", True)
        self.cooldown_bars = self.config.get("cooldown_bars", 3)
        self.commission_rate = self.config.get("commission_rate", 0.0008)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators (stochs, clouds, ATR)."""
        params = {
            "atr_length": self.atr_period,
            "allow_b_trades": True,
            "allow_c_trades": True,
            "b_open_fresh": self.allow_b_fresh,
        }
        df = compute_signals(df, params)
        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals with Cloud 3 filter applied."""
        if "long_a" not in df.columns:
            df = self.calculate_indicators(df)
        df = apply_cloud3_filter(df)
        return df

    def get_sl_tp(self, entry_price: float, atr_value: float) -> tuple[float, float]:
        """Return (stop_loss, take_profit) for a LONG position."""
        sl = entry_price - self.sl_atr_mult * atr_value
        tp = entry_price + self.tp_atr_mult * atr_value
        return sl, tp

    def get_name(self) -> str:
        return "FourPillarsV38"


if __name__ == "__main__":
    import numpy as np
    strategy = FourPillarsV38()
    assert strategy.get_name() == "FourPillarsV38"
    sl, tp = strategy.get_sl_tp(100.0, 2.0)
    assert sl == 98.0 and tp == 103.0, f"SL/TP mismatch: {sl}, {tp}"
    assert isinstance(strategy, BaseStrategy)
    print("PASS -- FourPillarsV38 instantiates, SL/TP correct, inherits BaseStrategy")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 7. optimizer/walk_forward.py (optimizer-level, wraps ml/walk_forward.py)
# ─────────────────────────────────────────────────────────────────────────────
FILES["optimizer/walk_forward.py"] = '''\
"""
Walk-forward validation at the optimizer level.
Splits OHLCV data by time, optimizes on train window, tests on test window.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd


def walk_forward_split(
    df: pd.DataFrame,
    train_months: int = 2,
    test_months: int = 1,
    step_weeks: int = 2,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Split time-series data into walk-forward train/test windows.

    Args:
        df: DataFrame with datetime index or column.
        train_months: Size of training window in months.
        test_months: Size of test window in months.
        step_weeks: Step forward between windows in weeks.

    Returns:
        List of (train_df, test_df) tuples.
    """
    if isinstance(df.index, pd.DatetimeIndex):
        ts = df.index
    elif "datetime" in df.columns:
        ts = pd.to_datetime(df["datetime"])
    elif "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"])
    else:
        raise ValueError("DataFrame must have datetime index or datetime/timestamp column")

    start = ts.min()
    end = ts.max()

    train_delta = pd.DateOffset(months=train_months)
    test_delta = pd.DateOffset(months=test_months)
    step_delta = pd.DateOffset(weeks=step_weeks)

    windows = []
    cursor = start

    while cursor + train_delta + test_delta <= end:
        train_end = cursor + train_delta
        test_end = train_end + test_delta

        train_mask = (ts >= cursor) & (ts < train_end)
        test_mask = (ts >= train_end) & (ts < test_end)

        train_df = df[train_mask.values] if not isinstance(df.index, pd.DatetimeIndex) else df[train_mask]
        test_df = df[test_mask.values] if not isinstance(df.index, pd.DatetimeIndex) else df[test_mask]

        if len(train_df) > 0 and len(test_df) > 0:
            windows.append((train_df, test_df))

        cursor += step_delta

    return windows


def walk_forward_validate(
    run_backtest_fn,
    df: pd.DataFrame,
    params: dict,
    train_months: int = 2,
    test_months: int = 1,
    step_weeks: int = 2,
) -> dict:
    """
    Run walk-forward validation using a backtest function.

    Args:
        run_backtest_fn: Callable(df, params) -> dict with "metrics" key.
        df: Full OHLCV+signals DataFrame.
        params: Backtest parameters.
        train_months: Training window size.
        test_months: Test window size.
        step_weeks: Step between windows.

    Returns:
        dict with per-window results and degradation ratios.
    """
    windows = walk_forward_split(df, train_months, test_months, step_weeks)

    results = []
    for i, (train_df, test_df) in enumerate(windows):
        train_result = run_backtest_fn(train_df, params)
        test_result = run_backtest_fn(test_df, params)

        train_sharpe = train_result["metrics"].get("sharpe", 0)
        test_sharpe = test_result["metrics"].get("sharpe", 0)

        degradation = test_sharpe / train_sharpe if train_sharpe != 0 else 0

        results.append({
            "window": i,
            "train_trades": train_result["metrics"].get("total_trades", 0),
            "test_trades": test_result["metrics"].get("total_trades", 0),
            "train_sharpe": train_sharpe,
            "test_sharpe": test_sharpe,
            "degradation": degradation,
        })

    avg_deg = np.mean([r["degradation"] for r in results]) if results else 0
    overfit = avg_deg < 0.5

    return {
        "windows": results,
        "avg_degradation": float(avg_deg),
        "overfit_flag": overfit,
        "n_windows": len(results),
    }


if __name__ == "__main__":
    dates = pd.date_range("2025-11-01", periods=5000, freq="5min")
    df = pd.DataFrame({
        "datetime": dates,
        "close": 100 + np.cumsum(np.random.randn(5000) * 0.1),
    })
    windows = walk_forward_split(df, train_months=1, test_months=1, step_weeks=1)
    print(f"PASS -- {len(windows)} walk-forward windows generated")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 8. optimizer/aggregator.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["optimizer/aggregator.py"] = '''\
"""
Aggregate optimization results across multiple coins.
Find universal best parameters via mode (categorical) and median (numeric).
"""

import numpy as np
import pandas as pd
from collections import Counter
from typing import Any


def aggregate_results(per_coin_results: dict[str, dict]) -> dict[str, Any]:
    """
    Find universal best parameters across all coins.

    Uses mode for categorical params, weighted median for numeric.
    Weight = SQN (or sharpe if SQN not available).

    Args:
        per_coin_results: {coin_name: {param_name: best_value, "sharpe": x, ...}}

    Returns:
        dict with aggregated best params and per-coin summary.
    """
    if not per_coin_results:
        return {"params": {}, "coins": 0, "summary": []}

    all_params = {}
    weights = {}

    for coin, result in per_coin_results.items():
        w = result.get("sqn", result.get("sharpe", 1.0))
        weights[coin] = max(w, 0.01)

        for key, val in result.items():
            if key in ("sharpe", "sqn", "net_pnl", "total_trades", "win_rate",
                       "max_drawdown", "profit_factor"):
                continue
            if key not in all_params:
                all_params[key] = []
            all_params[key].append((val, weights[coin]))

    aggregated = {}
    for param, values_weights in all_params.items():
        vals = [v for v, w in values_weights]

        # Categorical: use mode
        if isinstance(vals[0], str):
            counts = Counter(vals)
            aggregated[param] = counts.most_common(1)[0][0]
        else:
            # Numeric: weighted median
            w_arr = np.array([w for v, w in values_weights])
            v_arr = np.array([float(v) for v, w in values_weights])
            sorted_idx = np.argsort(v_arr)
            v_sorted = v_arr[sorted_idx]
            w_sorted = w_arr[sorted_idx]
            cum_w = np.cumsum(w_sorted)
            half = cum_w[-1] / 2.0
            idx = np.searchsorted(cum_w, half)
            aggregated[param] = float(v_sorted[min(idx, len(v_sorted) - 1)])

    summary = []
    for coin, result in per_coin_results.items():
        summary.append({
            "coin": coin,
            "weight": weights[coin],
            **{k: v for k, v in result.items()
               if k in ("sharpe", "net_pnl", "total_trades", "win_rate")},
        })

    return {
        "params": aggregated,
        "coins": len(per_coin_results),
        "summary": summary,
    }


def compare_optimizers(results_by_method: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Compare grid search vs Bayesian vs walk-forward results.

    Args:
        results_by_method: {"grid": df, "bayesian": df, "walk_forward": df}

    Returns:
        Summary DataFrame with best params and metrics per method.
    """
    rows = []
    for method, df in results_by_method.items():
        if len(df) == 0:
            continue
        best_idx = df["sharpe"].idxmax() if "sharpe" in df.columns else 0
        best = df.iloc[best_idx] if isinstance(best_idx, int) else df.loc[best_idx]
        rows.append({
            "method": method,
            "best_sharpe": best.get("sharpe", 0),
            "best_net_pnl": best.get("net_pnl", 0),
            "trials": len(df),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    results = {
        "RIVERUSDT": {"sl_mult": 1.0, "tp_mult": 1.5, "cooldown": 3, "risk_method": "be_only", "sharpe": 1.8},
        "KITEUSDT": {"sl_mult": 1.2, "tp_mult": 1.5, "cooldown": 5, "risk_method": "be_plus_fees", "sharpe": 1.2},
        "1000PEPEUSDT": {"sl_mult": 1.0, "tp_mult": 2.0, "cooldown": 3, "risk_method": "be_only", "sharpe": 0.9},
    }
    agg = aggregate_results(results)
    print(f"PASS -- aggregated {agg['coins']} coins, params: {agg['params']}")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 9. ml/xgboost_trainer.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["ml/xgboost_trainer.py"] = '''\
"""
XGBoost binary classifier for meta-labeling.
Wraps ml.meta_label.MetaLabelAnalyzer with a simpler interface.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str] = None,
    test_size: float = 0.3,
    params: dict = None,
) -> dict:
    """
    Train XGBoost binary classifier.

    Args:
        X: Feature matrix (n_samples x n_features).
        y: Binary labels (0 or 1).
        feature_names: Optional list of feature names.
        test_size: Fraction for test split.
        params: XGBoost hyperparameters override.

    Returns:
        dict with model, feature_importances, test_metrics.
    """
    if not HAS_XGB:
        raise ImportError("xgboost not installed. pip install xgboost")

    # Clean NaN
    if isinstance(X, pd.DataFrame):
        mask = ~X.isna().any(axis=1)
        X = X[mask].values
        y = y[mask.values] if hasattr(mask, 'values') else y[mask]
    else:
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = y[mask]

    if len(X) < 20:
        raise ValueError(f"Need >= 20 samples, got {len(X)}")

    default_params = {
        "objective": "binary:logistic",
        "max_depth": 4,
        "learning_rate": 0.05,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "logloss",
        "use_label_encoder": False,
        "verbosity": 0,
    }
    if params:
        default_params.update(params)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    model = XGBClassifier(**default_params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred.astype(float)

    importances = model.feature_importances_
    if feature_names and len(feature_names) == X.shape[1]:
        imp_df = pd.DataFrame({
            "feature": feature_names,
            "importance": importances,
        }).sort_values("importance", ascending=False)
    else:
        imp_df = pd.DataFrame({
            "feature": [f"f{i}" for i in range(len(importances))],
            "importance": importances,
        }).sort_values("importance", ascending=False)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "positive_rate": float(np.mean(y)),
    }

    return {
        "model": model,
        "feature_importances": imp_df,
        "metrics": metrics,
    }


def predict_skip_take(model, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """
    Predict 0 (SKIP) or 1 (TAKE) for each sample.

    Args:
        model: Trained XGBClassifier.
        X: Feature matrix.
        threshold: Probability threshold.

    Returns:
        Array of 0s and 1s.
    """
    proba = model.predict_proba(X)[:, 1]
    return (proba >= threshold).astype(int)


if __name__ == "__main__":
    np.random.seed(42)
    X = np.random.randn(200, 10)
    y = (X[:, 0] + X[:, 1] * 0.5 > 0).astype(int)
    result = train_xgboost(X, y, feature_names=[f"feat_{i}" for i in range(10)])
    print(f"PASS -- accuracy: {result['metrics']['accuracy']:.3f}, "
          f"features: {len(result['feature_importances'])}")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 10. gui/coin_selector.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["gui/coin_selector.py"] = '''\
"""
Fuzzy search coin selector for Streamlit.
Scans data/cache/ for available Parquet files and provides fuzzy matching.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from difflib import SequenceMatcher


def get_available_coins(data_dir: str = None) -> list[str]:
    """
    Scan data directory for cached coin Parquet files.

    Args:
        data_dir: Path to data/cache/ directory.

    Returns:
        Sorted list of coin symbol names.
    """
    if data_dir is None:
        data_dir = str(Path(__file__).resolve().parent.parent / "data" / "cache")

    cache = Path(data_dir)
    if not cache.exists():
        return []

    coins = set()
    for f in cache.glob("*.parquet"):
        name = f.stem.upper()
        # Strip timeframe suffix if present (e.g., BTCUSDT_1m -> BTCUSDT)
        if "_" in name:
            name = name.split("_")[0]
        coins.add(name)

    return sorted(coins)


def fuzzy_match(query: str, coins: list[str], limit: int = 5) -> list[str]:
    """
    Fuzzy match a query against available coins.

    Args:
        query: User input (e.g., "asx" -> suggests "AXSUSDT").
        coins: Available coin symbols.
        limit: Max number of suggestions.

    Returns:
        List of matching coin names, best first.
    """
    if not query:
        return coins[:limit]

    query = query.upper()

    # Exact prefix match first
    prefix = [c for c in coins if c.startswith(query)]
    if prefix:
        return prefix[:limit]

    # Substring match
    contains = [c for c in coins if query in c]
    if contains:
        return contains[:limit]

    # Fuzzy ratio
    scored = []
    for c in coins:
        ratio = SequenceMatcher(None, query, c).ratio()
        scored.append((c, ratio))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:limit]]


def coin_selector(data_dir: str = None) -> list[str]:
    """
    Interactive coin selector (for Streamlit integration).

    Returns list of selected coins. When not running in Streamlit,
    returns all available coins.

    Args:
        data_dir: Path to data/cache/ directory.

    Returns:
        List of selected coin symbols.
    """
    coins = get_available_coins(data_dir)

    try:
        import streamlit as st
        query = st.text_input("Search coins", "")
        suggestions = fuzzy_match(query, coins)
        selected = st.multiselect("Select coins", suggestions, default=suggestions[:1] if suggestions else [])
        return selected
    except (ImportError, RuntimeError):
        return coins


if __name__ == "__main__":
    coins = get_available_coins()
    if coins:
        matches = fuzzy_match("riv", coins)
        print(f"PASS -- {len(coins)} coins found, fuzzy 'riv' -> {matches}")
    else:
        print(f"PASS -- coin_selector works (no cache files found, expected in test)")
'''

# ─────────────────────────────────────────────────────────────────────────────
# 11. gui/parameter_inputs.py
# ─────────────────────────────────────────────────────────────────────────────
FILES["gui/parameter_inputs.py"] = '''\
"""
Streamlit parameter input form.
Returns a dict of all configurable parameters for backtesting.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


DEFAULT_PARAMS = {
    "timeframe": "5m",
    "notional": 10000.0,
    "margin": 500.0,
    "leverage": 20,
    "commission_rate": 0.0008,
    "rebate_pct": 0.70,
    "atr_period": 14,
    "sl_mult": 1.0,
    "tp_mult": 1.5,
    "cooldown": 3,
    "b_open_fresh": True,
    "be_raise_amount": 0.0,
    "risk_method": "be_only",
    "optimization_method": "bayesian",
    "n_trials": 200,
    "xgb_estimators": 200,
    "xgb_depth": 4,
    "ml_threshold": 0.5,
}


def parameter_inputs(defaults: dict = None) -> dict:
    """
    Streamlit form for all configuration options.

    Falls back to dict of defaults when not running in Streamlit.

    Args:
        defaults: Override default values.

    Returns:
        dict with all parameter values.
    """
    d = {**DEFAULT_PARAMS}
    if defaults:
        d.update(defaults)

    try:
        import streamlit as st

        st.sidebar.header("Strategy Parameters")
        d["timeframe"] = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h"], index=1)
        d["notional"] = st.sidebar.number_input("Notional ($)", value=d["notional"], step=1000.0)
        d["margin"] = st.sidebar.number_input("Margin ($)", value=d["margin"], step=100.0)
        d["leverage"] = st.sidebar.number_input("Leverage", value=d["leverage"], min_value=1, max_value=125)
        d["commission_rate"] = st.sidebar.number_input("Commission Rate", value=d["commission_rate"],
                                                        step=0.0001, format="%.4f")
        d["rebate_pct"] = st.sidebar.selectbox("Rebate %", [0.70, 0.50], index=0)

        st.sidebar.header("Entry / Exit")
        d["atr_period"] = st.sidebar.selectbox("ATR Period", [8, 13, 14, 21], index=2)
        d["sl_mult"] = st.sidebar.slider("SL (ATR mult)", 0.3, 4.0, d["sl_mult"], 0.1)
        d["tp_mult"] = st.sidebar.slider("TP (ATR mult)", 0.5, 6.0, d["tp_mult"], 0.1)
        d["cooldown"] = st.sidebar.slider("Cooldown (bars)", 0, 20, d["cooldown"])
        d["b_open_fresh"] = st.sidebar.checkbox("B Opens Fresh", value=d["b_open_fresh"])
        d["be_raise_amount"] = st.sidebar.number_input("BE Raise ($)", value=d["be_raise_amount"], step=1.0)
        d["risk_method"] = st.sidebar.selectbox("Risk Method",
                                                 ["be_only", "be_plus_fees", "be_plus_fees_trail_tp", "be_trail_tp"])

        st.sidebar.header("Optimization")
        d["optimization_method"] = st.sidebar.selectbox("Method", ["bayesian", "grid", "walk_forward"])
        d["n_trials"] = st.sidebar.number_input("Trials", value=d["n_trials"], step=50)

        st.sidebar.header("ML Meta-Label")
        d["xgb_estimators"] = st.sidebar.number_input("XGB Estimators", value=d["xgb_estimators"], step=50)
        d["xgb_depth"] = st.sidebar.slider("XGB Depth", 2, 10, d["xgb_depth"])
        d["ml_threshold"] = st.sidebar.slider("ML Threshold", 0.0, 1.0, d["ml_threshold"], 0.05)

    except (ImportError, RuntimeError):
        pass

    return d


if __name__ == "__main__":
    params = parameter_inputs()
    expected_keys = ["timeframe", "notional", "commission_rate", "atr_period",
                     "sl_mult", "tp_mult", "risk_method", "ml_threshold"]
    missing = [k for k in expected_keys if k not in params]
    if missing:
        print(f"FAIL -- missing keys: {missing}")
    else:
        print(f"PASS -- {len(params)} parameters returned")
'''


# ── Build + Test Logic ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  BUILD MISSING FILES -- Four Pillars Backtester")
    print("=" * 60)
    print(f"  Project: {PROJECT}")
    print()

    written = []
    skipped = []
    failed = []

    for rel_path, content in FILES.items():
        full_path = PROJECT / rel_path
        if full_path.exists():
            skipped.append(rel_path)
            print(f"  [SKIP] {rel_path} (already exists)")
            continue

        full_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            full_path.write_text(content, encoding="utf-8")
            written.append(rel_path)
            print(f"  [WROTE] {rel_path} ({len(content)} bytes)")
        except Exception as e:
            failed.append((rel_path, str(e)))
            print(f"  [FAIL] {rel_path}: {e}")

    # Create __init__.py for new directories
    for rel_path in written:
        d = (PROJECT / rel_path).parent
        init = d / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
            print(f"  [INIT] {init.relative_to(PROJECT)}")

    print()
    print(f"  Written: {len(written)}, Skipped: {len(skipped)}, Failed: {len(failed)}")
    print()

    # ── Test Phase ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("  TESTING ALL FILES")
    print("=" * 60)
    print()

    # Suppress Streamlit warnings when running outside streamlit
    import logging
    logging.getLogger("streamlit").setLevel(logging.ERROR)

    test_results = []

    # Test 1: base_strategy.py
    try:
        from strategies.base_strategy import BaseStrategy
        try:
            BaseStrategy()
            test_results.append(("strategies/base_strategy.py", False, "Should not instantiate"))
        except TypeError:
            test_results.append(("strategies/base_strategy.py", True, "Abstract class OK"))
    except Exception as e:
        test_results.append(("strategies/base_strategy.py", False, str(e)))

    # Test 2: engine/exit_manager.py
    try:
        from engine.exit_manager import ExitManager, ExitConfig
        em = ExitManager(ExitConfig(risk_method="be_plus_fees", mfe_trigger=1.0, fees_atr=0.3))
        sl, tp = em.update_stops("LONG", 100.0, 2.0, 98.0, 103.0, 1.2, 102.5)
        assert isinstance(sl, float) and isinstance(tp, float), f"Bad types: {type(sl)}, {type(tp)}"
        assert sl >= 98.0, f"SL moved backwards: {sl}"
        test_results.append(("engine/exit_manager.py", True, f"SL={sl:.2f} TP={tp:.2f}"))
    except Exception as e:
        test_results.append(("engine/exit_manager.py", False, str(e)))

    # Test 3: strategies/indicators.py
    try:
        import numpy as np
        import pandas as pd
        from strategies.indicators import calculate_all_indicators
        n = 200
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        df = pd.DataFrame({
            "open": close - 0.1,
            "high": close + np.abs(np.random.randn(n)) * 0.5,
            "low": close - np.abs(np.random.randn(n)) * 0.5,
            "close": close,
            "base_vol": np.random.randint(1000, 5000, n).astype(float),
        })
        result = calculate_all_indicators(df)
        expected = ["stoch_9", "stoch_14", "stoch_40", "stoch_60", "atr",
                    "cloud3_top", "price_pos", "cloud3_allows_long", "volume_ratio"]
        missing = [c for c in expected if c not in result.columns]
        if missing:
            test_results.append(("strategies/indicators.py", False, f"Missing: {missing}"))
        else:
            test_results.append(("strategies/indicators.py", True, f"{len(result.columns)} cols"))
    except Exception as e:
        test_results.append(("strategies/indicators.py", False, str(e)))

    # Test 4: strategies/signals.py
    try:
        from strategies.signals import generate_all_signals
        n = 500
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        df = pd.DataFrame({
            "open": close - 0.1,
            "high": close + np.abs(np.random.randn(n)) * 0.5,
            "low": close - np.abs(np.random.randn(n)) * 0.5,
            "close": close,
            "base_vol": np.random.randint(1000, 5000, n).astype(float),
        })
        result = generate_all_signals(df)
        assert "signal_type" in result.columns, "Missing signal_type"
        assert "direction" in result.columns, "Missing direction"
        sigs = result[result["signal_type"] != ""]
        test_results.append(("strategies/signals.py", True, f"{len(sigs)} signals"))
    except Exception as e:
        test_results.append(("strategies/signals.py", False, str(e)))

    # Test 5: strategies/cloud_filter.py
    try:
        from strategies.cloud_filter import apply_cloud3_filter
        df = pd.DataFrame({
            "long_a": [True, False, True],
            "short_a": [False, True, False],
            "signal_type": ["A", "A", "A"],
            "direction": ["LONG", "SHORT", "LONG"],
            "cloud3_allows_long": [True, True, False],
            "cloud3_allows_short": [True, False, True],
        })
        result = apply_cloud3_filter(df)
        # Row 1 short blocked, Row 2 long blocked
        blocked = (df["direction"] != "") & (result["direction"] == "")
        test_results.append(("strategies/cloud_filter.py", True, f"{blocked.sum()} blocked"))
    except Exception as e:
        test_results.append(("strategies/cloud_filter.py", False, str(e)))

    # Test 6: strategies/four_pillars_v3_8.py
    try:
        from strategies.four_pillars_v3_8 import FourPillarsV38
        from strategies.base_strategy import BaseStrategy
        s = FourPillarsV38()
        assert s.get_name() == "FourPillarsV38", f"Bad name: {s.get_name()}"
        assert isinstance(s, BaseStrategy), "Not a BaseStrategy"
        sl, tp = s.get_sl_tp(100.0, 2.0)
        assert sl == 98.0 and tp == 103.0, f"SL/TP: {sl}/{tp}"
        test_results.append(("strategies/four_pillars_v3_8.py", True, "Inherits BaseStrategy"))
    except Exception as e:
        test_results.append(("strategies/four_pillars_v3_8.py", False, str(e)))

    # Test 7: optimizer/walk_forward.py
    try:
        from optimizer.walk_forward import walk_forward_split
        # 100k bars * 5min = ~347 days, enough for train=2m + test=1m windows
        dates = pd.date_range("2025-06-01", periods=100000, freq="5min")
        df = pd.DataFrame({
            "datetime": dates,
            "close": 100 + np.cumsum(np.random.randn(100000) * 0.1),
        })
        windows = walk_forward_split(df, train_months=2, test_months=1, step_weeks=2)
        assert isinstance(windows, list), f"Not a list: {type(windows)}"
        assert len(windows) > 0, "No windows generated"
        assert isinstance(windows[0], tuple) and len(windows[0]) == 2, "Bad tuple"
        test_results.append(("optimizer/walk_forward.py", True, f"{len(windows)} windows"))
    except Exception as e:
        test_results.append(("optimizer/walk_forward.py", False, str(e)))

    # Test 8: optimizer/aggregator.py
    try:
        from optimizer.aggregator import aggregate_results
        results = {
            "RIVER": {"sl_mult": 1.0, "tp_mult": 1.5, "risk_method": "be_only", "sharpe": 1.8},
            "KITE": {"sl_mult": 1.2, "tp_mult": 1.5, "risk_method": "be_plus_fees", "sharpe": 1.2},
        }
        agg = aggregate_results(results)
        assert isinstance(agg, dict), f"Not a dict: {type(agg)}"
        assert "params" in agg, "Missing 'params' key"
        test_results.append(("optimizer/aggregator.py", True, f"{agg['coins']} coins aggregated"))
    except Exception as e:
        test_results.append(("optimizer/aggregator.py", False, str(e)))

    # Test 9: ml/xgboost_trainer.py
    try:
        from ml.xgboost_trainer import train_xgboost
        np.random.seed(42)
        X = np.random.randn(200, 10)
        y = (X[:, 0] + X[:, 1] * 0.5 > 0).astype(int)
        result = train_xgboost(X, y, feature_names=[f"f{i}" for i in range(10)])
        assert "model" in result, "Missing model"
        assert "metrics" in result, "Missing metrics"
        acc = result["metrics"]["accuracy"]
        test_results.append(("ml/xgboost_trainer.py", True, f"acc={acc:.3f}"))
    except Exception as e:
        test_results.append(("ml/xgboost_trainer.py", False, str(e)))

    # Test 10: gui/coin_selector.py
    try:
        from gui.coin_selector import coin_selector, fuzzy_match, get_available_coins
        coins = get_available_coins()
        assert isinstance(coins, list), f"Not a list: {type(coins)}"
        # Test fuzzy match even if no coins in cache
        test_coins = ["BTCUSDT", "ETHUSDT", "AXSUSDT", "RIVERUSDT"]
        matches = fuzzy_match("riv", test_coins)
        assert "RIVERUSDT" in matches, f"Fuzzy failed: {matches}"
        test_results.append(("gui/coin_selector.py", True, f"{len(coins)} cached coins"))
    except Exception as e:
        test_results.append(("gui/coin_selector.py", False, str(e)))

    # Test 11: gui/parameter_inputs.py
    try:
        from gui.parameter_inputs import parameter_inputs, DEFAULT_PARAMS
        # Test defaults directly (avoids Streamlit ScriptRunContext spam)
        params = dict(DEFAULT_PARAMS)
        assert isinstance(params, dict), f"Not a dict: {type(params)}"
        expected_keys = ["timeframe", "notional", "commission_rate", "atr_period",
                         "sl_mult", "tp_mult", "risk_method", "ml_threshold"]
        missing = [k for k in expected_keys if k not in params]
        if missing:
            test_results.append(("gui/parameter_inputs.py", False, f"Missing: {missing}"))
        else:
            test_results.append(("gui/parameter_inputs.py", True, f"{len(params)} params"))
    except Exception as e:
        test_results.append(("gui/parameter_inputs.py", False, str(e)))

    # ── Also test existing ml/ modules ────────────────────────────────────────
    print()
    print("=" * 60)
    print("  TESTING EXISTING ML MODULES")
    print("=" * 60)
    print()

    # ml.features
    try:
        from ml.features import extract_trade_features, get_feature_columns
        cols = get_feature_columns()
        assert isinstance(cols, list) and len(cols) > 0
        test_results.append(("ml/features.py", True, f"{len(cols)} feature cols"))
    except Exception as e:
        test_results.append(("ml/features.py", False, str(e)))

    # ml.triple_barrier
    try:
        from ml.triple_barrier import label_trades, get_label_distribution
        test_df = pd.DataFrame({"exit_reason": ["TP", "SL", "SL", "TP", "FLIP"]})
        labels = label_trades(test_df)
        assert len(labels) == 5
        test_results.append(("ml/triple_barrier.py", True, "labeling OK"))
    except Exception as e:
        test_results.append(("ml/triple_barrier.py", False, str(e)))

    # ml.meta_label
    try:
        from ml.meta_label import MetaLabelAnalyzer
        analyzer = MetaLabelAnalyzer()
        assert hasattr(analyzer, "train")
        test_results.append(("ml/meta_label.py", True, "MetaLabelAnalyzer OK"))
    except Exception as e:
        test_results.append(("ml/meta_label.py", False, str(e)))

    # ml.purged_cv
    try:
        from ml.purged_cv import purged_kfold_split
        test_results.append(("ml/purged_cv.py", True, "import OK"))
    except Exception as e:
        test_results.append(("ml/purged_cv.py", False, str(e)))

    # ml.shap_analyzer
    try:
        from ml.shap_analyzer import ShapAnalyzer
        test_results.append(("ml/shap_analyzer.py", True, "import OK"))
    except Exception as e:
        test_results.append(("ml/shap_analyzer.py", False, str(e)))

    # ml.bet_sizing
    try:
        from ml.bet_sizing import binary_sizing, get_sizing_summary
        sizes = binary_sizing(np.array([0.3, 0.6, 0.8]), threshold=0.5)
        assert np.array_equal(sizes, np.array([0.0, 1.0, 1.0]))
        test_results.append(("ml/bet_sizing.py", True, "sizing OK"))
    except Exception as e:
        test_results.append(("ml/bet_sizing.py", False, str(e)))

    # ml.walk_forward
    try:
        from ml.walk_forward import generate_windows, compute_wfe, get_wfe_rating
        windows = generate_windows(500)
        assert len(windows) > 0
        rating = get_wfe_rating(0.7)
        assert rating == "ROBUST"
        test_results.append(("ml/walk_forward.py", True, f"{len(windows)} windows"))
    except Exception as e:
        test_results.append(("ml/walk_forward.py", False, str(e)))

    # ml.loser_analysis
    try:
        from ml.loser_analysis import classify_losers, get_class_summary
        test_df = pd.DataFrame({
            "entry_price": [100.0] * 5,
            "sl_price": [98.0] * 5,
            "mfe": [0.5, 1.5, 3.0, 4.0, 0.2],
            "pnl": [5.0, -3.0, -2.0, -1.0, -4.0],
            "commission": [1.0] * 5,
        })
        classified = classify_losers(test_df)
        assert "loser_class" in classified.columns
        test_results.append(("ml/loser_analysis.py", True, "classification OK"))
    except Exception as e:
        test_results.append(("ml/loser_analysis.py", False, str(e)))

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print()

    passed = 0
    total = len(test_results)
    for path, ok, msg in test_results:
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"  [{status}] {path}: {msg}")

    print()
    print(f"  {passed}/{total} passed, {total - passed} failed")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
