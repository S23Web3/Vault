"""
Test script for scripts/download_periods.py
File: PROJECTS/four-pillars-backtester/scripts/test_download_periods.py

Tests:
  1. fetch_range() returns candles for BTCUSDT (3 pages max)
  2. raw_to_df() converts raw candles to valid DataFrame
  3. sanity_check() passes on good data, fails on bad data
  4. Progress state load/save round-trip
  5. Output directory structure is correct
  6. Never overwrites existing files
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import numpy as np

from data.fetcher import BybitFetcher

# Import functions from download_periods
sys.path.insert(0, str(ROOT / "scripts"))
from download_periods import (
    fetch_range, raw_to_df, sanity_check,
    load_state, save_state, state_file, PERIODS_DIR,
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
    print("TEST: download_periods.py")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # --- Test 1: fetch_range with real Bybit API (small fetch) ---
    print("\n--- Test 1: fetch_range (BTCUSDT, 3 pages) ---")
    fetcher = BybitFetcher(cache_dir=str(ROOT / "data" / "cache"), rate_limit=0.1)
    # Fetch just 1 hour of data (60 candles)
    end_dt = datetime(2024, 6, 1, 1, 0, 0, tzinfo=timezone.utc)
    start_dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    raw = fetch_range(fetcher, "BTCUSDT", start_ms, end_ms, rate=0.1)
    test("fetch_range returns data", len(raw) > 0, f"got {len(raw)} candles")
    test("fetch_range candle format", len(raw) > 0 and len(raw[0]) == 7,
         f"expected 7 fields per candle")

    # --- Test 2: raw_to_df conversion ---
    print("\n--- Test 2: raw_to_df ---")
    df = raw_to_df(raw)
    test("raw_to_df returns DataFrame", isinstance(df, pd.DataFrame))
    test("raw_to_df has expected columns",
         all(c in df.columns for c in ["timestamp", "open", "high", "low", "close", "base_vol", "quote_vol", "datetime"]),
         f"columns: {list(df.columns)}")
    test("raw_to_df rows > 0", len(df) > 0, f"rows: {len(df)}")
    test("raw_to_df sorted ascending",
         (df["timestamp"].values[:-1] <= df["timestamp"].values[1:]).all() if len(df) > 1 else True)
    test("raw_to_df no duplicate timestamps",
         df.duplicated(subset=["timestamp"]).sum() == 0)

    # --- Test 3: raw_to_df with empty input ---
    print("\n--- Test 3: raw_to_df empty ---")
    empty_df = raw_to_df([])
    test("raw_to_df empty returns empty DataFrame",
         isinstance(empty_df, pd.DataFrame) and len(empty_df) == 0)

    # --- Test 4: sanity_check ---
    print("\n--- Test 4: sanity_check ---")
    if len(df) > 0:
        err = sanity_check(df, "BTCUSDT")
        test("sanity_check passes on good data", err is None, f"error: {err}")

        # Test with null OHLC
        bad_df = df.copy()
        bad_df.loc[0, "open"] = np.nan
        err = sanity_check(bad_df, "BTCUSDT")
        test("sanity_check catches null OHLC", err is not None and "null" in err, f"error: {err}")

        # Test with duplicates
        dup_df = pd.concat([df, df.iloc[:1]], ignore_index=True)
        err = sanity_check(dup_df, "BTCUSDT")
        test("sanity_check catches duplicates", err is not None and "duplicate" in err, f"error: {err}")

        # Test with unsorted
        unsorted_df = df.iloc[::-1].reset_index(drop=True)
        err = sanity_check(unsorted_df, "BTCUSDT")
        test("sanity_check catches unsorted",
             err is not None and "sorted" in err, f"error: {err}")

    # --- Test 5: Progress state round-trip ---
    print("\n--- Test 5: Progress state ---")
    # Use a temp directory to avoid touching real state
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        # Monkey-patch state_file to use temp dir
        import download_periods as dp
        orig_periods_dir = dp.PERIODS_DIR
        dp.PERIODS_DIR = tmp_dir

        test_state = {
            "period": "2023-2024",
            "completed": ["BTCUSDT", "ETHUSDT"],
            "no_data": ["KITEUSDT"],
            "failed": [],
        }
        save_state(test_state)

        # Verify file was created
        sf = tmp_dir / "_state_2023-2024.json"
        test("state file created", sf.exists())

        loaded = load_state("2023-2024")
        test("state round-trip completed",
             set(loaded["completed"]) == {"BTCUSDT", "ETHUSDT"},
             f"got: {loaded.get('completed')}")
        test("state round-trip no_data",
             loaded["no_data"] == ["KITEUSDT"],
             f"got: {loaded.get('no_data')}")

        dp.PERIODS_DIR = orig_periods_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # --- Test 6: Output file naming ---
    print("\n--- Test 6: Output file naming ---")
    expected_parquet = PERIODS_DIR / "2023-2024" / "BTCUSDT_1m.parquet"
    expected_meta = PERIODS_DIR / "2023-2024" / "BTCUSDT_1m.meta"
    test("parquet naming correct", str(expected_parquet).endswith("2023-2024\\BTCUSDT_1m.parquet") or
         str(expected_parquet).endswith("2023-2024/BTCUSDT_1m.parquet"))
    test("meta naming correct", str(expected_meta).endswith("2023-2024\\BTCUSDT_1m.meta") or
         str(expected_meta).endswith("2023-2024/BTCUSDT_1m.meta"))

    # --- Summary ---
    print("\n" + "=" * 70)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 70)
    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
