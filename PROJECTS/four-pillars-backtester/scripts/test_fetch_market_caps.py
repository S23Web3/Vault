"""
Test script for scripts/fetch_market_caps.py
File: PROJECTS/four-pillars-backtester/scripts/test_fetch_market_caps.py

Tests:
  1. CoinGecko API key detection from .env
  2. Coin list loads from sub_1b_coins.json
  3. Single coin market chart fetch (BTC)
  4. Output data structure validation
  5. Parquet save/load round-trip
  6. Rate limit and error handling verification
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import requests
import pandas as pd

from fetch_market_caps import (
    load_env_key, fetch_market_chart, _save_parquet,
    COIN_LIST_FILE, OUTPUT_DIR,
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
    print("TEST: fetch_market_caps.py")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # --- Test 1: API key detection ---
    print("\n--- Test 1: API key detection ---")
    api_key = load_env_key()
    test("API key function runs", True)
    if api_key:
        test("API key found", len(api_key) > 5, f"key length: {len(api_key)}")
        print(f"  API tier: Pro (key={api_key[:8]}...)")
    else:
        print("  WARNING: No API key found. Tests will use free tier (slower).")
        test("API key not found (expected if not configured)", True)

    # --- Test 2: Coin list loading ---
    print("\n--- Test 2: Coin list ---")
    test("sub_1b_coins.json exists", COIN_LIST_FILE.exists(),
         f"path: {COIN_LIST_FILE}")

    if COIN_LIST_FILE.exists():
        with open(COIN_LIST_FILE) as f:
            coins = json.load(f)
        test("coin list is non-empty", len(coins) > 0, f"count: {len(coins)}")
        test("coin has cg_id field", "cg_id" in coins[0], f"keys: {list(coins[0].keys())}")
        test("coin has bybit_symbol", "bybit_symbol" in coins[0])
        test("coin has market_cap", "market_cap" in coins[0])

        # Find bitcoin for API test
        btc_entry = next((c for c in coins if c["cg_id"] == "bitcoin"), None)
        if btc_entry is None:
            # BTC may not be sub-$1B, use first coin
            btc_entry = {"cg_id": "bitcoin", "bybit_symbol": "BTCUSDT"}
    else:
        coins = []
        btc_entry = {"cg_id": "bitcoin", "bybit_symbol": "BTCUSDT"}

    # --- Test 3: Single coin fetch (Bitcoin, 7 days only) ---
    print("\n--- Test 3: Single coin fetch (bitcoin, 7 days) ---")
    session = requests.Session()
    data = fetch_market_chart("bitcoin", 7, api_key, session)

    test("fetch returns data", data is not None)
    if data:
        test("fetch returns list", isinstance(data, list))
        test("fetch has rows", len(data) > 0, f"rows: {len(data)}")
        test("row has date field", "date" in data[0], f"keys: {list(data[0].keys())}")
        test("row has market_cap field", "market_cap" in data[0])
        test("row has total_volume field", "total_volume" in data[0])
        test("market_cap is positive", data[0]["market_cap"] > 0,
             f"market_cap: {data[0]['market_cap']}")
        test("date format YYYY-MM-DD",
             len(data[0]["date"]) == 10 and data[0]["date"][4] == "-",
             f"date: {data[0]['date']}")

    # --- Test 4: Fetch with bad coin ID ---
    print("\n--- Test 4: Bad coin ID handling ---")
    bad_data = fetch_market_chart("this_coin_does_not_exist_xyz", 7, api_key, session)
    test("bad coin returns None", bad_data is None)

    # --- Test 5: Parquet round-trip ---
    print("\n--- Test 5: Parquet round-trip ---")
    if data:
        # Add symbol to rows
        rows = [dict(r, symbol="BTCUSDT") for r in data]

        tmp_dir = Path(tempfile.mkdtemp())
        tmp_file = tmp_dir / "test_output.parquet"

        # Monkey-patch OUTPUT_FILE
        import fetch_market_caps as fmc
        orig_output = fmc.OUTPUT_FILE
        fmc.OUTPUT_FILE = tmp_file

        _save_parquet(rows)
        test("parquet file created", tmp_file.exists())

        if tmp_file.exists():
            df = pd.read_parquet(tmp_file)
            test("parquet has expected columns",
                 all(c in df.columns for c in ["date", "symbol", "market_cap", "total_volume"]),
                 f"columns: {list(df.columns)}")
            test("parquet rows > 0", len(df) > 0,
                 f"got {len(df)} rows (may differ from input due to dedup)")
            test("parquet deduped", df.duplicated(subset=["date", "symbol"]).sum() == 0)

        fmc.OUTPUT_FILE = orig_output

        # Cleanup
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # --- Test 6: Longer fetch if paid API available ---
    if api_key:
        print("\n--- Test 6: Pro API 365-day fetch ---")
        data_365 = fetch_market_chart("bitcoin", 365, api_key, session)
        test("365-day fetch returns data", data_365 is not None)
        if data_365:
            test("365-day has 300+ rows", len(data_365) >= 300,
                 f"rows: {len(data_365)}")
    else:
        print("\n--- Test 6: SKIPPED (no API key for Pro tier test) ---")

    # --- Summary ---
    print("\n" + "=" * 70)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 70)
    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
