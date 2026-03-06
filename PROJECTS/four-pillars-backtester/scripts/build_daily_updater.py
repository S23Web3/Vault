"""
Build script: Creates daily_update.py — daily Bybit data updater.
Discovers all active USDT perps, incrementally fetches new candles, resamples to 5m.

Run:  python scripts/build_daily_updater.py
Then: python scripts/daily_update.py --dry-run
"""

import sys
import ast
import py_compile
from pathlib import Path
from datetime import datetime

ERRORS = []
ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TARGET = SCRIPTS / "daily_update.py"


def verify(path: Path, label: str) -> bool:
    """Validate Python file with py_compile and ast.parse."""
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as e:
        ERRORS.append(f"[{label}] py_compile FAILED: {e}")
        return False
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source)
    except SyntaxError as e:
        ERRORS.append(f"[{label}] ast.parse FAILED: {e}")
        return False
    print(f"  [{label}] py_compile + ast.parse OK")
    return True


# ─── Build daily_update.py ──────────────────────────────────────────────────

DAILY_UPDATE_SOURCE = r'''"""
Daily Bybit Data Updater.
Discovers all active USDT linear perpetuals, incrementally fetches new 1m candles,
and resamples to 5m. Designed to run daily from terminal or Task Scheduler.

Usage:
    python scripts/daily_update.py                    # Full run
    python scripts/daily_update.py --dry-run          # Preview without fetching
    python scripts/daily_update.py --skip-new         # Only update existing cached coins
    python scripts/daily_update.py --skip-resample    # Skip 5m resampling
    python scripts/daily_update.py --max-new 50       # Limit new coin additions
    python scripts/daily_update.py --months 6         # Lookback for new coins (default 12)
"""

import sys
import time
import logging
import argparse
import requests
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ─── Paths ──────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
LOG_DIR = PROJECT_ROOT / "logs"

sys.path.insert(0, str(PROJECT_ROOT))

# ─── Logging (dual handler: file + console, with timestamps) ────────────────

def setup_logging() -> logging.Logger:
    """Configure dual-handler logger: timestamped file + console output."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}-daily-update.log"

    logger = logging.getLogger("daily_update")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    fh = logging.FileHandler(str(log_file), encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ─── Bybit API helpers ──────────────────────────────────────────────────────

BYBIT_BASE = "https://api.bybit.com"
RATE_LIMIT = 0.12
MAX_CANDLES = 1000
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BASE_WAIT = 10


def discover_symbols(session: requests.Session, log: logging.Logger) -> list[str]:
    """Query Bybit v5 instruments-info for all active USDT linear perpetual symbols."""
    url = f"{BYBIT_BASE}/v5/market/instruments-info"
    params = {"category": "linear", "limit": "1000"}
    try:
        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            log.error("Bybit API error: %s", data.get("retMsg", "unknown"))
            return []
        instruments = data["result"]["list"]
        symbols = sorted(
            i["symbol"] for i in instruments
            if i["symbol"].endswith("USDT") and i["status"] == "Trading"
        )
        log.info("Discovered %d active USDT perpetuals on Bybit", len(symbols))
        return symbols
    except requests.exceptions.RequestException as e:
        log.error("Failed to discover symbols: %s", e)
        return []


def fetch_page(session: requests.Session, symbol: str,
               start_ms: int, end_ms: int) -> tuple[list, bool]:
    """Fetch one page of 1m candles from Bybit. Returns (candles, rate_limited)."""
    url = f"{BYBIT_BASE}/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": "1",
        "start": str(start_ms),
        "end": str(end_ms),
        "limit": str(MAX_CANDLES),
    }
    try:
        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            msg = data.get("retMsg", "")
            if "Too many visits" in msg:
                return [], True
            return [], False
        candles = data.get("result", {}).get("list", [])
        return (candles if candles else []), False
    except requests.exceptions.RequestException:
        return [], False


def fetch_candles_range(session: requests.Session, symbol: str,
                        start_ms: int, end_ms: int,
                        log: logging.Logger) -> list:
    """Fetch all 1m candles for a symbol between start_ms and end_ms. Returns raw candle list."""
    cursor = end_ms
    all_candles = []
    page = 0

    while cursor > start_ms:
        page += 1
        candles = []
        rate_limited = False

        for attempt in range(MAX_RETRIES):
            candles, rate_limited = fetch_page(session, symbol, start_ms, cursor)
            if not rate_limited:
                break
            wait = RETRY_BASE_WAIT * (2 ** attempt)
            log.warning("  %s: rate limited, waiting %ds (attempt %d/%d)",
                        symbol, wait, attempt + 1, MAX_RETRIES)
            time.sleep(wait)

        if rate_limited and not candles:
            log.warning("  %s: rate limit not cleared after %d retries", symbol, MAX_RETRIES)
            break

        if not candles:
            break

        all_candles.extend(candles)

        oldest_ts = min(int(c[0]) for c in candles)
        next_cursor = oldest_ts - 1
        if next_cursor >= cursor:
            break
        cursor = next_cursor

        if len(candles) < MAX_CANDLES:
            break

        time.sleep(RATE_LIMIT)

        if page % 50 == 0:
            pct = min(100, (end_ms - cursor) / max(1, end_ms - start_ms) * 100)
            log.info("  %s: %d candles fetched (%.0f%%)", symbol, len(all_candles), pct)

    return all_candles


COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]


def candles_to_df(raw_candles: list, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Convert raw Bybit candle list to cleaned DataFrame."""
    df = pd.DataFrame(raw_candles, columns=COLUMNS)
    df["timestamp"] = pd.to_numeric(df["timestamp"])
    for col in ["open", "high", "low", "close", "volume", "turnover"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.rename(columns={"volume": "base_vol", "turnover": "quote_vol"})
    df = df[(df["timestamp"] >= start_ms) & (df["timestamp"] <= end_ms)]
    df = df.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


# ─── Incremental fetch logic ────────────────────────────────────────────────

def read_meta(symbol: str) -> tuple[int, int] | None:
    """Read cached .meta file. Returns (start_ms, end_ms) or None."""
    meta_file = CACHE_DIR / f"{symbol}_1m.meta"
    if not meta_file.exists():
        return None
    try:
        parts = meta_file.read_text().strip().split(",")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except (ValueError, OSError):
        pass
    return None


def write_meta(symbol: str, start_ms: int, end_ms: int) -> None:
    """Write .meta file for a symbol."""
    meta_file = CACHE_DIR / f"{symbol}_1m.meta"
    meta_file.write_text(f"{start_ms},{end_ms}")


def incremental_fetch(session: requests.Session, symbol: str,
                      default_start: datetime, end_time: datetime,
                      log: logging.Logger, dry_run: bool = False) -> str:
    """
    Incrementally fetch new candles for a symbol.
    Returns status string: 'updated', 'new', 'current', 'failed', 'dry_run'.
    """
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    end_ms = int(end_time.timestamp() * 1000)
    meta = read_meta(symbol)

    if meta is not None:
        cached_start_ms, cached_end_ms = meta
        if cached_end_ms >= end_ms:
            return "current"

        gap_start_ms = cached_end_ms
        gap_start_dt = datetime.fromtimestamp(cached_end_ms / 1000, tz=timezone.utc)

        if dry_run:
            gap_hours = (end_ms - gap_start_ms) / 3_600_000
            log.info("  %s: would fetch %.1f hours of gap (%s to now)",
                     symbol, gap_hours, gap_start_dt.strftime("%Y-%m-%d %H:%M"))
            return "dry_run"

        log.info("  %s: incremental from %s", symbol, gap_start_dt.strftime("%Y-%m-%d %H:%M"))
        raw = fetch_candles_range(session, symbol, gap_start_ms, end_ms, log)

        if not raw:
            write_meta(symbol, cached_start_ms, end_ms)
            log.info("  %s: no new candles in gap (market may be closed)", symbol)
            return "current"

        df_gap = candles_to_df(raw, gap_start_ms, end_ms)
        df_existing = pd.read_parquet(cache_file)
        df_merged = pd.concat([df_existing, df_gap], ignore_index=True)
        df_merged = df_merged.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

        new_start_ms = min(cached_start_ms, int(df_merged["timestamp"].min()))
        df_merged.to_parquet(cache_file, engine="pyarrow", index=False)
        write_meta(symbol, new_start_ms, end_ms)

        added = len(df_merged) - len(df_existing)
        log.info("  %s: +%d candles, %d total", symbol, max(added, 0), len(df_merged))
        return "updated"

    else:
        start_ms = int(default_start.timestamp() * 1000)

        if dry_run:
            months = (end_time - default_start).days / 30
            log.info("  %s: NEW coin, would fetch %.1f months of data", symbol, months)
            return "dry_run"

        log.info("  %s: NEW coin, full fetch from %s",
                 symbol, default_start.strftime("%Y-%m-%d"))
        raw = fetch_candles_range(session, symbol, start_ms, end_ms, log)

        if not raw:
            log.warning("  %s: no data returned", symbol)
            return "failed"

        df = candles_to_df(raw, start_ms, end_ms)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_file, engine="pyarrow", index=False)
        write_meta(symbol, start_ms, end_ms)

        log.info("  %s: %d candles saved", symbol, len(df))
        return "new"


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    """Entry point for daily Bybit data updater."""
    parser = argparse.ArgumentParser(description="Daily Bybit data updater — incremental fetch + resample")
    parser.add_argument("--months", type=int, default=12,
                        help="Lookback months for NEW coins (default: 12)")
    parser.add_argument("--skip-new", action="store_true",
                        help="Only update existing cached coins, skip newly discovered ones")
    parser.add_argument("--skip-resample", action="store_true",
                        help="Skip 5m resampling step")
    parser.add_argument("--max-new", type=int, default=None,
                        help="Max number of new coins to add per run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be fetched without fetching")
    args = parser.parse_args()

    log = setup_logging()
    log.info("=" * 70)
    log.info("Four Pillars -- Daily Bybit Data Updater")
    log.info("=" * 70)

    session = requests.Session()

    # Step 1: Discover all active USDT perps
    all_symbols = discover_symbols(session, log)
    if not all_symbols:
        log.error("Discovery failed. Exiting.")
        sys.exit(1)

    # Compare against cache
    cached_symbols = set(
        f.stem.replace("_1m", "")
        for f in CACHE_DIR.glob("*_1m.parquet")
    )
    existing = [s for s in all_symbols if s in cached_symbols]
    new_coins = [s for s in all_symbols if s not in cached_symbols]
    delisted = cached_symbols - set(all_symbols)

    log.info("Active on Bybit:   %d", len(all_symbols))
    log.info("Already cached:    %d", len(existing))
    log.info("New coins:         %d", len(new_coins))
    if delisted:
        log.info("Delisted (cached): %d", len(delisted))

    # Build work list
    work_list = list(existing)
    if not args.skip_new:
        if args.max_new is not None:
            new_coins = new_coins[:args.max_new]
            log.info("Capped new coins to %d", args.max_new)
        work_list.extend(new_coins)
    else:
        log.info("--skip-new: skipping %d new coins", len(new_coins))

    log.info("Total to process:  %d", len(work_list))
    log.info("")

    # Step 2: Incremental fetch
    end_time = datetime.now(timezone.utc)
    default_start = end_time - timedelta(days=args.months * 30)

    counts = {"updated": 0, "new": 0, "current": 0, "failed": 0, "dry_run": 0}
    updated_symbols = []
    total = len(work_list)

    for i, symbol in enumerate(work_list, 1):
        pct = i / total * 100
        log.info("[%d/%d] (%.1f%%) %s", i, total, pct, symbol)

        status = incremental_fetch(session, symbol, default_start, end_time, log, dry_run=args.dry_run)
        counts[status] += 1

        if status in ("updated", "new"):
            updated_symbols.append(symbol)

        time.sleep(0.5)

    # Step 3: Resample to 5m
    if not args.skip_resample and not args.dry_run and updated_symbols:
        log.info("")
        log.info("=" * 70)
        log.info("RESAMPLING %d symbols to 5m", len(updated_symbols))
        log.info("=" * 70)

        from resample_timeframes import TimeframeResampler
        resampler = TimeframeResampler(cache_dir=str(CACHE_DIR))

        resample_ok = 0
        resample_fail = 0
        for sym in updated_symbols:
            result = resampler.resample_file(sym, "5m", overwrite=True)
            if result:
                resample_ok += 1
            else:
                resample_fail += 1

        log.info("Resample done: %d OK, %d failed", resample_ok, resample_fail)

    # Step 4: Summary
    log.info("")
    log.info("=" * 70)
    log.info("SUMMARY")
    log.info("=" * 70)
    log.info("Updated (incremental): %d", counts["updated"])
    log.info("New coins fetched:     %d", counts["new"])
    log.info("Already current:       %d", counts["current"])
    log.info("Failed:                %d", counts["failed"])
    if args.dry_run:
        log.info("Dry-run previewed:     %d", counts["dry_run"])

    # Disk usage
    try:
        parquets_1m = list(CACHE_DIR.glob("*_1m.parquet"))
        parquets_5m = list(CACHE_DIR.glob("*_5m.parquet"))
        size_1m = sum(f.stat().st_size for f in parquets_1m)
        size_5m = sum(f.stat().st_size for f in parquets_5m)
        log.info("")
        log.info("Cache: %d coins (1m: %.1f MB, 5m: %.1f MB)",
                 len(parquets_1m), size_1m / 1024 / 1024, size_5m / 1024 / 1024)
    except OSError:
        pass

    log.info("Finished: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    try:
        import pandas
        import pyarrow
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install: pip install pandas pyarrow requests")
        sys.exit(1)
    main()
'''

# ─── Write and verify ───────────────────────────────────────────────────────

def main():
    """Build daily_update.py and validate with py_compile + ast.parse."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Building daily_update.py...")
    print(f"  Target: {TARGET}")

    if TARGET.exists():
        print(f"  WARNING: {TARGET} already exists, writing versioned copy")
        from datetime import date
        versioned = SCRIPTS / f"daily_update_{date.today().isoformat()}.py"
        versioned.write_text(DAILY_UPDATE_SOURCE.lstrip(), encoding="utf-8")
        print(f"  Wrote: {versioned}")
        verify(versioned, "daily_update (versioned)")
    else:
        TARGET.write_text(DAILY_UPDATE_SOURCE.lstrip(), encoding="utf-8")
        print(f"  Wrote: {TARGET}")
        verify(TARGET, "daily_update")

    print()
    if ERRORS:
        print("=" * 60)
        print("ERRORS:")
        for e in ERRORS:
            print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
    else:
        print("=" * 60)
        print("BUILD SUCCESS")
        print("=" * 60)
        print()
        print("Run commands:")
        print(f'  cd "{ROOT}"')
        print("  python scripts/daily_update.py --dry-run")
        print("  python scripts/daily_update.py")


if __name__ == "__main__":
    main()
