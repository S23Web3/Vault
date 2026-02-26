"""
Test script for data/period_loader.py
File: PROJECTS/four-pillars-backtester/scripts/test_period_loader.py

Tests:
  1. list_available_symbols() returns symbols from cache
  2. load_multi_period() loads existing cached data
  3. Deduplication works across overlapping periods
  4. get_symbol_coverage() returns period info
  5. Returns None for non-existent symbol
  6. Handles missing period directories gracefully
"""

import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

from data.period_loader import (
    load_multi_period, list_available_symbols, get_symbol_coverage,
    PERIOD_DIRS,
)

PASS = 0
FAIL = 0


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    ts = datetime.now().strftime("%H:%M:%S")
    if condition:
        PASS += 1
        print(f"[{ts}] PASS: {name}")
    else:
        FAIL += 1
        print(f"[{ts}] FAIL: {name} -- {detail}")


def main():
    global PASS, FAIL
    print("=" * 70)
    print("TEST: data/period_loader.py")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # --- Test 1: list_available_symbols ---
    print("\n--- Test 1: list_available_symbols ---")
    symbols = list_available_symbols()
    test("returns list", isinstance(symbols, list))
    test("non-empty (cache has data)", len(symbols) > 0,
         f"found {len(symbols)} symbols")
    test("sorted alphabetically",
         symbols == sorted(symbols) if symbols else True)

    if symbols:
        print(f"  First 5: {symbols[:5]}")
        print(f"  Total: {len(symbols)}")

    # --- Test 2: load_multi_period for known symbol ---
    print("\n--- Test 2: load_multi_period ---")
    # Use BTCUSDT as it should exist in cache
    test_symbol = "BTCUSDT"
    if test_symbol not in symbols and symbols:
        test_symbol = symbols[0]
        print(f"  BTCUSDT not found, using {test_symbol}")

    df = load_multi_period(test_symbol)
    test("returns DataFrame", isinstance(df, pd.DataFrame))

    if df is not None and len(df) > 0:
        test("has expected columns",
             all(c in df.columns for c in ["timestamp", "open", "high", "low", "close"]),
             f"columns: {list(df.columns)}")
        test("has datetime column", "datetime" in df.columns)
        test("has base_vol", "base_vol" in df.columns)
        test("rows > 0", len(df) > 0, f"rows: {len(df)}")

        # Sorted ascending
        ts = df["timestamp"].values
        test("sorted ascending", (ts[:-1] <= ts[1:]).all() if len(ts) > 1 else True)

        # No duplicates
        test("no duplicate timestamps", df.duplicated(subset=["timestamp"]).sum() == 0)

        # Date range
        start_dt = pd.to_datetime(df["timestamp"].min(), unit="ms", utc=True)
        end_dt = pd.to_datetime(df["timestamp"].max(), unit="ms", utc=True)
        print(f"  {test_symbol}: {len(df):,} bars, {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")

    # --- Test 3: get_symbol_coverage ---
    print("\n--- Test 3: get_symbol_coverage ---")
    coverage = get_symbol_coverage(test_symbol)
    test("returns list", isinstance(coverage, list))
    test("has at least 1 period (cache)", len(coverage) >= 1,
         f"periods: {len(coverage)}")

    for c in coverage:
        print(f"  Period: {c['period']}, bars: {c['bars']:,}, "
              f"range: {c['start']} to {c['end']}")
        test(f"  {c['period']} has bars > 0", c["bars"] > 0)

    # --- Test 4: Non-existent symbol ---
    print("\n--- Test 4: Non-existent symbol ---")
    df_none = load_multi_period("FAKECOIN_DOES_NOT_EXIST_USDT")
    test("non-existent returns None", df_none is None)

    empty_coverage = get_symbol_coverage("FAKECOIN_DOES_NOT_EXIST_USDT")
    test("non-existent coverage is empty", len(empty_coverage) == 0)

    # --- Test 5: Period directories ---
    print("\n--- Test 5: Period directory check ---")
    for pd_path in PERIOD_DIRS:
        exists = pd_path.exists()
        print(f"  {pd_path.name}: {'EXISTS' if exists else 'NOT YET'}")
    # At minimum, cache should exist
    test("cache dir exists", (ROOT / "data" / "cache").exists())

    # --- Test 6: 5m interval support ---
    print("\n--- Test 6: 5m interval ---")
    symbols_5m = list_available_symbols("5m")
    test("5m symbol list returns", isinstance(symbols_5m, list))
    if symbols_5m:
        df_5m = load_multi_period(symbols_5m[0], "5m")
        test("5m data loads", df_5m is not None and len(df_5m) > 0,
             f"rows: {len(df_5m) if df_5m is not None else 0}")

    # --- Summary ---
    print("\n" + "=" * 70)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 70)
    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
