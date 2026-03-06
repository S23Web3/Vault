r"""
Build script: creates scripts/daily_bingx_update.py

Incremental updater for BingX perpetual futures 1m OHLCV data.
Reads .meta files to find last cached timestamp, fetches only the gap to now.
Discovers new coins not yet in cache and fetches full history for them.

Run:  python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/build_daily_bingx_updater.py"
Then: python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py" --dry-run
      python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py"
"""

import py_compile
from pathlib import Path

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
OUT = ROOT / "scripts" / "daily_bingx_update.py"

CODE = r'''"""
Daily incremental updater for BingX perpetual futures 1m OHLCV data.

Reads .meta files in data/bingx/ to find the last cached timestamp per coin.
Fetches only the gap (cached_end -> now) and appends to existing parquets.
Also discovers new coins not yet cached and fetches full history for them.

Imports fetch functions from fetch_bingx_ohlcv.py (no code duplication).

Usage:
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py" --dry-run
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py"
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py" --skip-new
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py" --skip-resample
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py" --max-new 20
    python "C:/Users/User/Documents/Obsidian Vault/PROJECTS/four-pillars-backtester/scripts/daily_bingx_update.py" --months 6
"""

import argparse
import datetime
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# ── path setup ────────────────────────────────────────────────────────────

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
sys.path.insert(0, str(ROOT / "scripts"))

from fetch_bingx_ohlcv import (
    fetch_all_perp_symbols,
    fetch_klines_page,
    parse_klines,
    to_parquet_format,
    resample_5m,
    save_parquet,
    bingx_to_parquet_symbol,
    MAX_CANDLES,
    ONE_MINUTE_MS,
    RATE_LIMIT_SLEEP,
)

# ── constants ─────────────────────────────────────────────────────────────

BINGX_DIR = ROOT / "data" / "bingx"
LOG_DIR = ROOT / "logs"
DEFAULT_MONTHS = 12


def setup_logging():
    """Configure dual logging: file + console with timestamps."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    log_file = LOG_DIR / f"{today}-bingx-daily-update.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on re-runs
    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger


def read_meta(meta_path):
    """Read a .meta file and return (start_ms, end_ms) or None."""
    if not meta_path.exists():
        return None
    try:
        text = meta_path.read_text().strip()
        parts = text.split(",")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return None


def fetch_gap(session, symbol, start_ms, end_ms):
    """Fetch candles for a time range (no progress bar, used for small gaps)."""
    all_candles = []
    cursor = start_ms

    while cursor < end_ms:
        page_end = min(cursor + MAX_CANDLES * ONE_MINUTE_MS, end_ms)
        raw = fetch_klines_page(session, symbol, "1m", cursor, page_end)

        if raw is None:
            logging.error("Hard error fetching gap for %s", symbol)
            break

        if not raw:
            cursor = page_end
            continue

        df = parse_klines(raw)
        if df.empty:
            cursor = page_end
            continue

        all_candles.append(df)
        max_ts = int(df["time"].max())
        cursor = max_ts + ONE_MINUTE_MS
        time.sleep(RATE_LIMIT_SLEEP)

    if not all_candles:
        return pd.DataFrame()

    combined = pd.concat(all_candles, ignore_index=True)
    combined = combined.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    return combined


def incremental_update(session, symbol, cache_dir, now_ms, months_back):
    """Update one symbol incrementally. Returns (status, candles_added)."""
    parq_sym = bingx_to_parquet_symbol(symbol)
    parq_1m = cache_dir / f"{parq_sym}_1m.parquet"
    meta_1m = cache_dir / f"{parq_sym}_1m.meta"
    parq_5m = cache_dir / f"{parq_sym}_5m.parquet"
    meta_5m = cache_dir / f"{parq_sym}_5m.meta"

    meta = read_meta(meta_1m)

    if meta is not None:
        cached_start, cached_end = meta
        gap_ms = now_ms - cached_end
        gap_hours = gap_ms / (3600 * 1000)

        if gap_hours < 2:
            # Less than 2 hours behind — consider current
            return "current", 0

        # Fetch only the gap
        logging.info("%s: gap = %.1f hours, fetching...", symbol, gap_hours)
        df_gap_raw = fetch_gap(session, symbol, cached_end + ONE_MINUTE_MS, now_ms)

        if df_gap_raw.empty:
            logging.warning("%s: no new data in gap", symbol)
            return "no_data", 0

        df_gap = to_parquet_format(df_gap_raw)
        df_gap = df_gap.dropna(subset=["close"])

        if df_gap.empty:
            return "no_data", 0

        # Load existing, merge, deduplicate
        df_existing = pd.read_parquet(parq_1m)
        df_merged = pd.concat([df_existing, df_gap], ignore_index=True)
        df_merged = df_merged.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

        candles_added = len(df_merged) - len(df_existing)
        save_parquet(df_merged, parq_1m, meta_1m)

        # Resample full merged data to 5m
        df_5m = resample_5m(df_merged)
        if not df_5m.empty:
            save_parquet(df_5m, parq_5m, meta_5m)

        return "updated", candles_added

    else:
        # New coin — no existing data, full fetch
        start_ms = now_ms - (months_back * 30 * 24 * 60 * 60 * 1000)
        logging.info("%s: NEW coin, fetching %d months back...", symbol, months_back)
        df_raw = fetch_gap(session, symbol, start_ms, now_ms)

        if df_raw.empty:
            return "empty", 0

        df_1m = to_parquet_format(df_raw)
        df_1m = df_1m.dropna(subset=["close"])

        if df_1m.empty:
            return "empty", 0

        save_parquet(df_1m, parq_1m, meta_1m)

        df_5m = resample_5m(df_1m)
        if not df_5m.empty:
            save_parquet(df_5m, parq_5m, meta_5m)

        return "new", len(df_1m)


def main():
    """Entry point for BingX daily updater."""
    parser = argparse.ArgumentParser(
        description="Incremental updater for BingX perpetual futures 1m OHLCV data"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview gaps and new coins without fetching")
    parser.add_argument("--skip-new", action="store_true",
                        help="Only update existing cached coins, skip new discoveries")
    parser.add_argument("--skip-resample", action="store_true",
                        help="Skip 5m resampling (1m only)")
    parser.add_argument("--max-new", type=int, default=0,
                        help="Max new coins to add per run (0 = all)")
    parser.add_argument("--months", type=int, default=DEFAULT_MONTHS,
                        help="Lookback months for new coins (default 12)")
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("BingX Daily Updater started")

    BINGX_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Data directory: %s", BINGX_DIR)

    session = requests.Session()
    session.headers.update({"User-Agent": "four-pillars-fetcher/1.0"})

    # ── discover symbols ──────────────────────────────────────────────────
    logger.info("Discovering BingX USDT perp symbols...")
    all_symbols = fetch_all_perp_symbols(session)
    logger.info("Found %d USDT perpetual symbols on BingX", len(all_symbols))

    # ── classify: existing vs new ─────────────────────────────────────────
    existing = []
    new_coins = []
    for sym in all_symbols:
        parq_sym = bingx_to_parquet_symbol(sym)
        meta_path = BINGX_DIR / f"{parq_sym}_1m.meta"
        if meta_path.exists():
            existing.append(sym)
        else:
            new_coins.append(sym)

    logger.info("Existing cached: %d | New (not cached): %d", len(existing), len(new_coins))

    now_ms = int(time.time() * 1000)

    # ── dry run ───────────────────────────────────────────────────────────
    if args.dry_run:
        logger.info("DRY RUN — no data will be fetched")
        logger.info("")
        logger.info("--- EXISTING COINS (gaps) ---")
        total_gap_hours = 0
        for sym in existing:
            parq_sym = bingx_to_parquet_symbol(sym)
            meta = read_meta(BINGX_DIR / f"{parq_sym}_1m.meta")
            if meta:
                gap_h = (now_ms - meta[1]) / (3600 * 1000)
                total_gap_hours += gap_h
                if gap_h >= 2:
                    logger.info("  %s: %.1f hours behind", sym, gap_h)
                else:
                    logger.info("  %s: current (%.1f hours)", sym, gap_h)
        logger.info("Total gap: %.1f hours across %d coins", total_gap_hours, len(existing))
        logger.info("")
        logger.info("--- NEW COINS ---")
        for i, sym in enumerate(new_coins):
            logger.info("  %3d. %s (would fetch %d months)", i + 1, sym, args.months)
        if args.skip_new:
            logger.info("  (--skip-new: these would be skipped)")
        if args.max_new > 0:
            logger.info("  (--max-new %d: only first %d would be fetched)", args.max_new, args.max_new)
        return

    # ── update existing coins ─────────────────────────────────────────────
    t0 = time.time()
    updated = 0
    current = 0
    no_data = 0
    failed_list = []

    logger.info("")
    logger.info("--- UPDATING %d EXISTING COINS ---", len(existing))
    for idx, sym in enumerate(existing):
        try:
            status, added = incremental_update(session, sym, BINGX_DIR, now_ms, args.months)
            if status == "current":
                current += 1
            elif status == "updated":
                updated += 1
                logger.info("[%d/%d] %s: +%d candles", idx + 1, len(existing), sym, added)
            elif status == "no_data":
                no_data += 1
            else:
                failed_list.append(sym)
        except Exception as e:
            logging.error("[%d/%d] %s: %s", idx + 1, len(existing), sym, e)
            failed_list.append(sym)

    logger.info("Existing coins: %d updated, %d current, %d no_data, %d failed",
                updated, current, no_data, len(failed_list))

    # ── fetch new coins ───────────────────────────────────────────────────
    new_added = 0
    new_failed = []

    if not args.skip_new and new_coins:
        fetch_new = new_coins
        if args.max_new > 0:
            fetch_new = new_coins[:args.max_new]

        logger.info("")
        logger.info("--- FETCHING %d NEW COINS ---", len(fetch_new))
        for idx, sym in enumerate(fetch_new):
            try:
                status, added = incremental_update(session, sym, BINGX_DIR, now_ms, args.months)
                if status == "new":
                    new_added += 1
                    logger.info("[%d/%d] %s: %d candles (new)", idx + 1, len(fetch_new), sym, added)
                elif status == "empty":
                    logger.warning("[%d/%d] %s: no data available", idx + 1, len(fetch_new), sym)
                    new_failed.append(sym)
                else:
                    new_failed.append(sym)
            except Exception as e:
                logging.error("[%d/%d] %s: %s", idx + 1, len(fetch_new), sym, e)
                new_failed.append(sym)

    # ── summary ───────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    logger.info("")
    logger.info("=" * 60)
    logger.info("DONE in %.0f seconds (%.1f minutes)", elapsed, elapsed / 60)
    logger.info("Existing: %d updated, %d current, %d no_data, %d failed",
                updated, current, no_data, len(failed_list))
    if new_coins and not args.skip_new:
        logger.info("New coins: %d added, %d failed", new_added, len(new_failed))
    if failed_list:
        logger.info("Failed (existing): " + ", ".join(failed_list))
    if new_failed:
        logger.info("Failed (new): " + ", ".join(new_failed))

    # Disk usage
    total_files = list(BINGX_DIR.glob("*.parquet"))
    total_size_mb = sum(f.stat().st_size for f in total_files) / (1024 * 1024)
    logger.info("BingX cache: %d parquet files, %.1f MB", len(total_files), total_size_mb)


if __name__ == "__main__":
    main()
'''

# ── write file ────────────────────────────────────────────────────────────
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(CODE.lstrip(), encoding="utf-8")
print(f"WROTE: {OUT}")

# ── py_compile ────────────────────────────────────────────────────────────
py_compile.compile(str(OUT), doraise=True)
print(f"py_compile PASS: {OUT}")
print()
print("Run commands:")
print(f'  python "{OUT}" --dry-run')
print(f'  python "{OUT}"')
print(f'  python "{OUT}" --skip-new')
print(f'  python "{OUT}" --max-new 20')
