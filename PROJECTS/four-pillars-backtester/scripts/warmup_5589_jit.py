"""
One-shot JIT warmup for Backtester5589Fast.

Compiles _run_5589_core and caches the binary to disk.
Subsequent runs (including dashboard) load the cache in <1s.

Run once from the .venv312 environment:
  python scripts/warmup_5589_jit.py
"""

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def make_mini_df(n: int = 500) -> pd.DataFrame:
    """Generate minimal synthetic signal DataFrame for JIT warmup."""
    rng   = np.random.default_rng(42)
    close = 50000.0 + np.cumsum(rng.normal(0, 10.0, n))
    close = np.clip(close, 10000.0, 100000.0)
    high  = close * rng.uniform(1.000, 1.003, n)
    low   = close * rng.uniform(0.997, 1.000, n)
    vol   = rng.uniform(1.0, 100.0, n)
    atr   = close * 0.002
    stoch = rng.uniform(10.0, 90.0, n)
    ema89 = close * 0.998
    ema55 = close * 0.999

    df = pd.DataFrame({
        "datetime":  pd.date_range("2025-01-01", periods=n, freq="1min", tz="UTC"),
        "open":      close * rng.uniform(0.999, 1.001, n),
        "high":      high,
        "low":       low,
        "close":     close,
        "volume":    vol,
        "atr":       atr,
        "stoch_9_d": stoch,
        "ema_89":    ema89,
        "ema_55":    ema55,
    })

    # Inject a few signals
    long_a  = np.zeros(n, dtype=bool)
    short_a = np.zeros(n, dtype=bool)
    for i in [50, 150, 250, 350, 450]:
        if i < n:
            long_a[i]  = True
    for i in [100, 200, 300, 400]:
        if i < n:
            short_a[i] = True

    df["long_a"]  = long_a
    df["short_a"] = short_a
    return df


def main() -> None:
    """Run warmup: compile JIT, verify output matches Backtester5589, report timing."""
    print("=== warmup_5589_jit.py ===")
    print("Root: " + str(ROOT))

    print("")
    print("Importing Backtester5589Fast...")
    from engine.backtester_5589_jit import Backtester5589Fast
    print("  Import OK")

    print("")
    print("Importing Backtester5589 (reference)...")
    from engine.backtester_55_89 import Backtester5589
    print("  Import OK")

    df = make_mini_df(500)
    print("")
    print("Synthetic data: " + str(len(df)) + " bars")
    print("Signals: " + str(int(df['long_a'].sum())) + " long, " + str(int(df['short_a'].sum())) + " short")

    params = {
        "sl_mult": 2.5, "avwap_sigma": 2.0, "avwap_warmup": 5,
        "tp_atr_offset": 0.5, "ratchet_threshold": 2,
        "notional": 5000.0, "initial_equity": 10000.0,
        "commission_rate": 0.0008, "maker_rate": 0.0002, "rebate_pct": 0.70,
    }

    # Reference run
    t0 = time.perf_counter()
    ref = Backtester5589(params).run(df)
    t_ref = time.perf_counter() - t0
    ref_trades = ref["metrics"]["total_trades"]
    ref_pnl    = ref["metrics"]["net_pnl"]
    print("")
    print("Reference (Python): " + str(ref_trades) + " trades, PnL $" + "{:.2f}".format(ref_pnl)
          + " in {:.3f}s".format(t_ref))

    # JIT first run (triggers compilation)
    print("")
    print("JIT first run (compiling _run_5589_core)...")
    t0 = time.perf_counter()
    fast = Backtester5589Fast(params).run(df)
    t_jit1 = time.perf_counter() - t0
    jit_trades = fast["metrics"]["total_trades"]
    jit_pnl    = fast["metrics"]["net_pnl"]
    print("JIT first run:  " + str(jit_trades) + " trades, PnL $" + "{:.2f}".format(jit_pnl)
          + " in {:.3f}s".format(t_jit1) + " (includes compile time)")

    # JIT second run (cached)
    t0 = time.perf_counter()
    fast2 = Backtester5589Fast(params).run(df)
    t_jit2 = time.perf_counter() - t0
    print("JIT cached run: " + str(fast2["metrics"]["total_trades"]) + " trades"
          + " in {:.3f}s".format(t_jit2))

    # Agreement check
    print("")
    if ref_trades == jit_trades:
        print("[PASS] Trade count matches: " + str(ref_trades))
    else:
        print("[WARN] Trade count mismatch: ref=" + str(ref_trades) + " jit=" + str(jit_trades))

    pnl_diff = abs(ref_pnl - jit_pnl)
    if pnl_diff < 0.01:
        print("[PASS] Net PnL agrees within $0.01 (diff=$" + "{:.6f}".format(pnl_diff) + ")")
    else:
        print("[WARN] PnL diff $" + "{:.4f}".format(pnl_diff)
              + " (ref=$" + "{:.2f}".format(ref_pnl) + " jit=$" + "{:.2f}".format(jit_pnl) + ")")

    print("")
    print("Compile time cached to numba __pycache__.")
    print("Dashboard will load the cache on next import.")
    print("")
    print("=== DONE ===")
    print("Activate venv and run dashboard:")
    print("  streamlit run \"" + str(ROOT / "scripts" / "dashboard_55_89_v3.py") + "\"")


if __name__ == "__main__":
    main()
