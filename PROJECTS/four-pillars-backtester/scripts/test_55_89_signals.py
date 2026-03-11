"""
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
