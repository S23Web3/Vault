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
