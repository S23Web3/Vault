"""
WEEX API Probe - Tests candle endpoints for historical pagination support.
Run: python scripts/probe_weex_api.py

Tests 3 endpoint families with multiple pagination param combos.
Reports which endpoint + params return historical data vs latest-only.
No auth required (all public market data endpoints).
"""
import sys
import time
import logging
import traceback
from datetime import datetime, timezone, timedelta

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Target timestamps ---
# We want candles from ~30 days ago to prove historical pagination works.
# If an endpoint only returns "latest" data, the oldest timestamp will be
# within the last ~24h regardless of what we ask for.
NOW_MS = int(datetime.now(timezone.utc).timestamp() * 1000)
THIRTY_DAYS_AGO_MS = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp() * 1000)
SEVEN_DAYS_AGO_MS = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp() * 1000)
ONE_DAY_AGO_MS = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp() * 1000)

RATE_LIMIT = 0.5  # seconds between requests


def ts_to_str(ms: int) -> str:
    """Convert epoch ms to human-readable UTC string."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def extract_timestamps(data) -> tuple:
    """Extract first and last timestamps from API response data."""
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        last = data[-1]
        # Handle both list-of-lists and list-of-dicts
        if isinstance(first, list):
            return int(first[0]), int(last[0]), len(data)
        elif isinstance(first, dict):
            # Try common timestamp keys
            for key in ["time", "timestamp", "ts", "t", "openTime"]:
                if key in first:
                    return int(first[key]), int(last[key]), len(data)
        elif isinstance(first, str):
            # Some APIs return [["ts","o","h","l","c","v",...], ...]
            try:
                return int(first), int(last[0] if isinstance(last, list) else last), len(data)
            except (ValueError, TypeError):
                pass
    return None, None, 0


def probe_endpoint(name: str, url: str, base_params: dict, extra_params: dict) -> dict:
    """Hit one endpoint with params, return result summary."""
    params = {**base_params, **extra_params}
    result = {
        "name": name,
        "url": url,
        "params": extra_params,
        "status": None,
        "candles": 0,
        "first_ts": None,
        "last_ts": None,
        "historical": False,
        "error": None,
        "response_keys": None,
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        result["status"] = resp.status_code

        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        body = resp.json()

        # Try to find the candle data in various response structures
        data = None
        if isinstance(body, list):
            data = body
            result["response_keys"] = "raw_list"
        elif isinstance(body, dict):
            result["response_keys"] = list(body.keys())
            # Common wrapper patterns
            for path in [
                lambda b: b.get("data"),
                lambda b: b.get("data", {}).get("data") if isinstance(b.get("data"), dict) else None,
                lambda b: b.get("result"),
                lambda b: b.get("data", {}).get("candles") if isinstance(b.get("data"), dict) else None,
                lambda b: b.get("candles"),
            ]:
                candidate = path(body)
                if isinstance(candidate, list) and len(candidate) > 0:
                    data = candidate
                    break

        if data is None:
            result["error"] = "No candle data found in response"
            return result

        first_ts, last_ts, count = extract_timestamps(data)
        result["candles"] = count
        result["first_ts"] = first_ts
        result["last_ts"] = last_ts

        if first_ts and last_ts:
            # "Historical" = oldest candle is more than 2 days old
            two_days_ago = NOW_MS - (2 * 24 * 60 * 60 * 1000)
            oldest = min(first_ts, last_ts)
            result["historical"] = oldest < two_days_ago

    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection failed: {str(e)[:100]}"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:100]}"
        log.debug(traceback.format_exc())

    return result


def print_result(r: dict) -> None:
    """Print one probe result."""
    status = r["status"] or "N/A"
    candles = r["candles"]
    historical = "YES" if r["historical"] else "NO"
    error = r["error"] or ""

    first_str = ts_to_str(r["first_ts"]) if r["first_ts"] else "N/A"
    last_str = ts_to_str(r["last_ts"]) if r["last_ts"] else "N/A"

    log.info("  HTTP=%s  candles=%d  first=%s  last=%s  HISTORICAL=%s",
             status, candles, first_str, last_str, historical)
    if r["response_keys"]:
        log.info("  Response keys: %s", r["response_keys"])
    if error:
        log.warning("  Error: %s", error)
    if r["params"]:
        log.info("  Extra params: %s", r["params"])


def main() -> None:
    """Run all WEEX API probe tests."""
    log.info("=" * 70)
    log.info("WEEX API PROBE - Testing candle endpoints for pagination support")
    log.info("=" * 70)
    log.info("Target: candles from 30 days ago (%s)", ts_to_str(THIRTY_DAYS_AGO_MS))
    log.info("Now: %s", ts_to_str(NOW_MS))
    log.info("")

    results = []

    # ---------------------------------------------------------------
    # ENDPOINT 1: Contract candles (existing WEEXFetcher uses this)
    # ---------------------------------------------------------------
    log.info("-" * 60)
    log.info("ENDPOINT 1: Contract candles (api-contract.weex.com)")
    log.info("-" * 60)

    contract_url = "https://api-contract.weex.com/capi/v2/market/candles"
    contract_base = {"symbol": "cmt_btcusdt", "granularity": "1m", "limit": "1000"}

    tests_1 = [
        ("1a: baseline (no pagination)", {}),
        ("1b: startTime (30d ago)", {"startTime": str(THIRTY_DAYS_AGO_MS)}),
        ("1c: endTime (30d ago)", {"endTime": str(THIRTY_DAYS_AGO_MS)}),
        ("1d: startTime+endTime (30d window)", {"startTime": str(THIRTY_DAYS_AGO_MS), "endTime": str(SEVEN_DAYS_AGO_MS)}),
        ("1e: start (30d ago)", {"start": str(THIRTY_DAYS_AGO_MS)}),
        ("1f: end (30d ago)", {"end": str(THIRTY_DAYS_AGO_MS)}),
        ("1g: after (30d ago)", {"after": str(THIRTY_DAYS_AGO_MS)}),
        ("1h: before (30d ago)", {"before": str(THIRTY_DAYS_AGO_MS)}),
    ]

    for name, extra in tests_1:
        log.info("[%s]", name)
        r = probe_endpoint(name, contract_url, contract_base, extra)
        print_result(r)
        results.append(r)
        time.sleep(RATE_LIMIT)

    # ---------------------------------------------------------------
    # ENDPOINT 2: Spot candles (api-spot.weex.com)
    # ---------------------------------------------------------------
    log.info("")
    log.info("-" * 60)
    log.info("ENDPOINT 2: Spot candles (api-spot.weex.com)")
    log.info("-" * 60)

    spot_url = "https://api-spot.weex.com/api/v2/market/candles"
    spot_base = {"symbol": "BTCUSDT_SPBL", "granularity": "1min", "limit": "1000"}

    tests_2 = [
        ("2a: baseline (no pagination)", {}),
        ("2b: startTime (30d ago)", {"startTime": str(THIRTY_DAYS_AGO_MS)}),
        ("2c: endTime (30d ago)", {"endTime": str(THIRTY_DAYS_AGO_MS)}),
        ("2d: startTime+endTime (30d window)", {"startTime": str(THIRTY_DAYS_AGO_MS), "endTime": str(SEVEN_DAYS_AGO_MS)}),
        ("2e: after (30d ago)", {"after": str(THIRTY_DAYS_AGO_MS)}),
        ("2f: before (30d ago)", {"before": str(THIRTY_DAYS_AGO_MS)}),
    ]

    for name, extra in tests_2:
        log.info("[%s]", name)
        r = probe_endpoint(name, spot_url, spot_base, extra)
        print_result(r)
        results.append(r)
        time.sleep(RATE_LIMIT)

    # Also try with "period" instead of "granularity" (seen in screener scope doc)
    log.info("")
    log.info("[2g: period param instead of granularity]")
    spot_base_alt = {"symbol": "BTCUSDT_SPBL", "period": "1min", "limit": "1000"}
    r = probe_endpoint("2g: period param", spot_url, spot_base_alt,
                       {"startTime": str(THIRTY_DAYS_AGO_MS), "endTime": str(SEVEN_DAYS_AGO_MS)})
    print_result(r)
    results.append(r)
    time.sleep(RATE_LIMIT)

    # ---------------------------------------------------------------
    # ENDPOINT 3: v1 candles (api.weex.com — from build spec docs)
    # ---------------------------------------------------------------
    log.info("")
    log.info("-" * 60)
    log.info("ENDPOINT 3: v1 candles (api.weex.com)")
    log.info("-" * 60)

    v1_url = "https://api.weex.com/api/v1/market/candles"
    v1_base = {"symbol": "BTCUSDT", "type": "1min", "limit": "1000"}

    tests_3 = [
        ("3a: baseline", {}),
        ("3b: startAt (30d ago, seconds)", {"startAt": str(THIRTY_DAYS_AGO_MS // 1000)}),
        ("3c: endAt (30d ago, seconds)", {"endAt": str(THIRTY_DAYS_AGO_MS // 1000)}),
        ("3d: startAt+endAt (30d window, seconds)", {"startAt": str(THIRTY_DAYS_AGO_MS // 1000), "endAt": str(SEVEN_DAYS_AGO_MS // 1000)}),
    ]

    for name, extra in tests_3:
        log.info("[%s]", name)
        r = probe_endpoint(name, v1_url, v1_base, extra)
        print_result(r)
        results.append(r)
        time.sleep(RATE_LIMIT)

    # ---------------------------------------------------------------
    # ENDPOINT 4: Futures candles (api-futures.weex.com — Bitget pattern)
    # ---------------------------------------------------------------
    log.info("")
    log.info("-" * 60)
    log.info("ENDPOINT 4: Futures candles (api-futures.weex.com — Bitget pattern)")
    log.info("-" * 60)

    futures_url = "https://api-futures.weex.com/api/v2/mix/market/candles"
    futures_base = {"symbol": "BTCUSDT", "productType": "USDT-FUTURES", "granularity": "1m", "limit": "1000"}

    tests_4 = [
        ("4a: baseline", {}),
        ("4b: startTime+endTime (30d window)", {"startTime": str(THIRTY_DAYS_AGO_MS), "endTime": str(SEVEN_DAYS_AGO_MS)}),
    ]

    for name, extra in tests_4:
        log.info("[%s]", name)
        r = probe_endpoint(name, futures_url, futures_base, extra)
        print_result(r)
        results.append(r)
        time.sleep(RATE_LIMIT)

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    log.info("")
    log.info("=" * 70)
    log.info("SUMMARY")
    log.info("=" * 70)

    historical_hits = [r for r in results if r["historical"]]
    if historical_hits:
        log.info("PAGINATION CONFIRMED on %d endpoint(s):", len(historical_hits))
        for r in historical_hits:
            log.info("  [%s] %d candles, oldest=%s",
                     r["name"], r["candles"],
                     ts_to_str(min(r["first_ts"], r["last_ts"])) if r["first_ts"] and r["last_ts"] else "?")
    else:
        log.warning("NO endpoint returned historical data.")
        log.warning("Fallback options:")
        log.warning("  A) Start collecting from today, accumulate over time")
        log.warning("  B) Try Bitget API directly (may share data with WEEX)")
        log.warning("  C) Use Bybit data as proxy for backtesting")

    working = [r for r in results if r["candles"] > 0]
    failed = [r for r in results if r["candles"] == 0]
    log.info("")
    log.info("Total tests: %d  |  Returned data: %d  |  Failed/empty: %d  |  Historical: %d",
             len(results), len(working), len(failed), len(historical_hits))


if __name__ == "__main__":
    main()
