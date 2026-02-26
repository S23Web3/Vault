"""
Test script for scripts/download_periods_v2.py
File: PROJECTS/four-pillars-backtester/scripts/test_download_periods_v2.py

Tests:
  1. CoinGecko listing date loading from parquet
  2. filter_coins_for_period() correctly filters by date
  3. fetch_range() returns candles for BTCUSDT (small fetch)
  4. raw_to_df() converts raw candles to valid DataFrame
  5. sanity_check() passes on good data, fails on bad data
  6. Progress state load/save round-trip
  7. --all flag processes both periods list
  8. Coins without CG data are kept (not filtered out)
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd
import numpy as np

from data.fetcher import BybitFetcher

from download_periods_v2 import (
    fetch_range, raw_to_df, sanity_check,
    load_state, save_state, state_file,
    load_coingecko_listing_dates, filter_coins_for_period,
    PERIODS_DIR, PERIODS, ALL_PERIODS,
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
    print("TEST: download_periods_v2.py")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # --- Test 1: CoinGecko listing date loading ---
    print("\n--- Test 1: CoinGecko listing date loading ---")
    cg_dates = load_coingecko_listing_dates()
    test("cg_dates returns dict", isinstance(cg_dates, dict))
    if cg_dates:
        test("cg_dates has entries", len(cg_dates) > 0, f"count: {len(cg_dates)}")
        # Check a few known coins
        if "BTCUSDT" in cg_dates:
            test("BTC has early date", cg_dates["BTCUSDT"] < "2024-01-01",
                 f"BTC earliest: {cg_dates['BTCUSDT']}")
        if "ETHUSDT" in cg_dates:
            test("ETH has early date", cg_dates["ETHUSDT"] < "2024-01-01",
                 f"ETH earliest: {cg_dates['ETHUSDT']}")
        # Show date distribution
        before_2024 = sum(1 for d in cg_dates.values() if d < "2024-01-01")
        before_2025 = sum(1 for d in cg_dates.values() if d < "2025-01-01")
        print(f"  Distribution: {before_2024} coins before 2024, "
              f"{before_2025} coins before 2025, "
              f"{len(cg_dates)} total")
    else:
        print("  WARNING: No CoinGecko data found. Filtering tests will use mock data.")

    # --- Test 2: filter_coins_for_period ---
    print("\n--- Test 2: filter_coins_for_period ---")

    # Mock CG dates for predictable testing
    mock_cg = {
        "BTCUSDT": "2013-04-28",    # existed before 2023
        "ETHUSDT": "2015-08-07",    # existed before 2023
        "SOLUSDT": "2020-04-10",    # existed before 2023
        "JUPUSDT": "2024-01-31",    # listed Jan 2024 (after 2023-2024 period)
        "WIFUSDT": "2024-03-05",    # listed Mar 2024 (after 2023-2024 period)
        "RIVERUSDT": "2024-06-15",  # listed Jun 2024 (after 2023-2024 period)
        "KITEUSDT": "2024-11-02",   # listed Nov 2024 (after 2023-2024 period)
        "NEWCOIN2025": "2025-01-15", # listed Jan 2025 (after both periods)
    }
    all_syms = sorted(mock_cg.keys())

    # 2023-2024: only BTC, ETH, SOL should be eligible
    elig_23, skip_23 = filter_coins_for_period(all_syms, "2023-2024", mock_cg)
    test("2023-2024 eligible count", len(elig_23) == 3,
         f"expected 3, got {len(elig_23)}: {elig_23}")
    test("2023-2024 skipped count", skip_23 == 5,
         f"expected 5, got {skip_23}")
    test("2023-2024 has BTC", "BTCUSDT" in elig_23)
    test("2023-2024 has ETH", "ETHUSDT" in elig_23)
    test("2023-2024 has SOL", "SOLUSDT" in elig_23)
    test("2023-2024 excludes JUP", "JUPUSDT" not in elig_23)
    test("2023-2024 excludes RIVER", "RIVERUSDT" not in elig_23)

    # 2024-2025: BTC, ETH, SOL, JUP, WIF, RIVER, KITE should be eligible
    elig_24, skip_24 = filter_coins_for_period(all_syms, "2024-2025", mock_cg)
    test("2024-2025 eligible count", len(elig_24) == 7,
         f"expected 7, got {len(elig_24)}: {elig_24}")
    test("2024-2025 skipped count", skip_24 == 1,
         f"expected 1, got {skip_24}")
    test("2024-2025 has JUP", "JUPUSDT" in elig_24)
    test("2024-2025 has RIVER", "RIVERUSDT" in elig_24)
    test("2024-2025 excludes NEWCOIN2025", "NEWCOIN2025" not in elig_24)

    # Empty CG dates = no filtering (all pass through)
    elig_empty, skip_empty = filter_coins_for_period(all_syms, "2023-2024", {})
    test("empty CG dates keeps all", len(elig_empty) == len(all_syms),
         f"expected {len(all_syms)}, got {len(elig_empty)}")
    test("empty CG dates zero skipped", skip_empty == 0)

    # --- Test 3: Coin not in CG is kept (conservative) ---
    print("\n--- Test 3: Unknown coins kept ---")
    partial_cg = {"BTCUSDT": "2013-04-28"}
    syms_with_unknown = ["BTCUSDT", "UNKNOWNCOIN"]
    elig_unk, skip_unk = filter_coins_for_period(syms_with_unknown, "2023-2024", partial_cg)
    test("unknown coin kept", "UNKNOWNCOIN" in elig_unk,
         f"eligible: {elig_unk}")
    test("unknown coin not skipped", skip_unk == 0)

    # --- Test 4: fetch_range with real Bybit API (small fetch) ---
    print("\n--- Test 4: fetch_range (BTCUSDT, 1 hour) ---")
    fetcher = BybitFetcher(cache_dir=str(ROOT / "data" / "cache"), rate_limit=0.1)
    end_dt = datetime(2024, 6, 1, 1, 0, 0, tzinfo=timezone.utc)
    start_dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    raw = fetch_range(fetcher, "BTCUSDT", start_ms, end_ms, rate=0.1)
    test("fetch_range returns data", len(raw) > 0, f"got {len(raw)} candles")
    test("fetch_range candle format", len(raw) > 0 and len(raw[0]) == 7,
         f"expected 7 fields per candle")

    # --- Test 5: raw_to_df conversion ---
    print("\n--- Test 5: raw_to_df ---")
    df = raw_to_df(raw)
    test("raw_to_df returns DataFrame", isinstance(df, pd.DataFrame))
    test("raw_to_df has expected columns",
         all(c in df.columns for c in ["timestamp", "open", "high", "low", "close",
                                        "base_vol", "quote_vol", "datetime"]),
         f"columns: {list(df.columns)}")
    test("raw_to_df rows > 0", len(df) > 0, f"rows: {len(df)}")
    test("raw_to_df sorted ascending",
         (df["timestamp"].values[:-1] <= df["timestamp"].values[1:]).all() if len(df) > 1 else True)
    test("raw_to_df no duplicate timestamps",
         df.duplicated(subset=["timestamp"]).sum() == 0)

    # Empty input
    empty_df = raw_to_df([])
    test("raw_to_df empty returns empty DataFrame",
         isinstance(empty_df, pd.DataFrame) and len(empty_df) == 0)

    # --- Test 6: sanity_check ---
    print("\n--- Test 6: sanity_check ---")
    if len(df) > 0:
        err = sanity_check(df, "BTCUSDT")
        test("sanity_check passes on good data", err is None, f"error: {err}")

        bad_df = df.copy()
        bad_df.loc[0, "open"] = np.nan
        err = sanity_check(bad_df, "BTCUSDT")
        test("sanity_check catches null OHLC", err is not None and "null" in err)

        dup_df = pd.concat([df, df.iloc[:1]], ignore_index=True)
        err = sanity_check(dup_df, "BTCUSDT")
        test("sanity_check catches duplicates", err is not None and "duplicate" in err)

        unsorted_df = df.iloc[::-1].reset_index(drop=True)
        err = sanity_check(unsorted_df, "BTCUSDT")
        test("sanity_check catches unsorted", err is not None and "sorted" in err)

    # --- Test 7: Progress state round-trip ---
    print("\n--- Test 7: Progress state round-trip ---")
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        import download_periods_v2 as dp2
        orig_periods_dir = dp2.PERIODS_DIR
        dp2.PERIODS_DIR = tmp_dir

        test_state = {
            "period": "2023-2024",
            "completed": ["BTCUSDT", "ETHUSDT"],
            "no_data": ["KITEUSDT"],
            "failed": [],
        }
        save_state(test_state)

        sf = tmp_dir / "_state_2023-2024.json"
        test("state file created", sf.exists())

        loaded = load_state("2023-2024")
        test("state round-trip completed",
             set(loaded["completed"]) == {"BTCUSDT", "ETHUSDT"},
             f"got: {loaded.get('completed')}")
        test("state round-trip no_data",
             loaded["no_data"] == ["KITEUSDT"],
             f"got: {loaded.get('no_data')}")

        dp2.PERIODS_DIR = orig_periods_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # --- Test 8: ALL_PERIODS constant ---
    print("\n--- Test 8: ALL_PERIODS constant ---")
    test("ALL_PERIODS has 2 entries", len(ALL_PERIODS) == 2,
         f"got {len(ALL_PERIODS)}")
    test("ALL_PERIODS order correct",
         ALL_PERIODS == ["2023-2024", "2024-2025"],
         f"got {ALL_PERIODS}")
    test("PERIODS dict has both", all(p in PERIODS for p in ALL_PERIODS))

    # --- Test 9: Real CG date distribution (if data available) ---
    if cg_dates:
        print("\n--- Test 9: Real CG distribution ---")
        all_cached = sorted(cg_dates.keys())
        real_elig_23, real_skip_23 = filter_coins_for_period(all_cached, "2023-2024", cg_dates)
        real_elig_24, real_skip_24 = filter_coins_for_period(all_cached, "2024-2025", cg_dates)
        print(f"  2023-2024: {len(real_elig_23)} eligible, {real_skip_23} skipped")
        print(f"  2024-2025: {len(real_elig_24)} eligible, {real_skip_24} skipped")
        test("2023-2024 has fewer coins than 2024-2025",
             len(real_elig_23) <= len(real_elig_24),
             f"2023: {len(real_elig_23)}, 2024: {len(real_elig_24)}")
        test("total equals cached count",
             len(real_elig_23) + real_skip_23 == len(all_cached),
             f"{len(real_elig_23)} + {real_skip_23} != {len(all_cached)}")

    # --- Summary ---
    print("\n" + "=" * 70)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 70)
    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
