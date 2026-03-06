r"""
Build script: creates scripts/fetch_bingx_ohlcv.py
Fetches ALL BingX perpetual futures 1m OHLCV data (1 year back).
Saves to data/cache/ in the same parquet format the dashboard reads.

Run:  python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_fetch_bingx.py"
Then: python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_bingx_ohlcv.py" --dry-run
      python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\fetch_bingx_ohlcv.py"
"""

import py_compile
from pathlib import Path

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
OUT = ROOT / "scripts" / "fetch_bingx_ohlcv.py"

CODE = r'''"""
Fetch ALL BingX perpetual futures OHLCV 1m data, 1 year back.

Discovers symbols via /openApi/swap/v2/quote/contracts.
Fetches 1m klines via /openApi/swap/v3/quote/klines (1440 per request).
Saves to data/cache/{SYMBOL}_1m.parquet + .meta (uniform format).
Also resamples and saves {SYMBOL}_5m.parquet + .meta.

Schema matches Bybit parquets exactly:
    timestamp   int64       epoch ms
    open        float64
    high        float64
    low         float64
    close       float64
    base_vol    float64
    quote_vol   float64
    datetime    datetime64[ns, UTC]

Usage:
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py"
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py" --dry-run
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py" --symbol BTC-USDT
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py" --max-coins 10
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py" --months 6
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py" --skip-existing
    python "C:\\Users\\User\\Documents\\Obsidian Vault\\PROJECTS\\four-pillars-backtester\\scripts\\fetch_bingx_ohlcv.py" --output-dir data/bingx
"""

import argparse
import datetime
import logging
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

# ── constants ──────────────────────────────────────────────────────────────

BASE_URL = "https://open-api.bingx.com"
CONTRACTS_PATH = "/openApi/swap/v2/quote/contracts"
KLINES_PATH = "/openApi/swap/v3/quote/klines"
MAX_CANDLES = 1440
ONE_MINUTE_MS = 60_000
DEFAULT_MONTHS = 12
MAX_RETRIES = 5
RATE_LIMIT_SLEEP = 0.35  # seconds between requests (conservative)

ROOT = Path(r"C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester")
DEFAULT_CACHE = ROOT / "data" / "bingx"
LOG_DIR = ROOT / "logs"


def setup_logging():
    """Configure dual logging: file + console with timestamps."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    log_file = LOG_DIR / f"{today}-bingx-fetch.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


def bingx_to_parquet_symbol(bingx_sym):
    """Convert BingX symbol (BTC-USDT) to parquet filename format (BTCUSDT)."""
    return bingx_sym.replace("-", "")


def fetch_all_perp_symbols(session):
    """Discover all USDT perpetual futures symbols from BingX."""
    url = BASE_URL + CONTRACTS_PATH
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code", 0) != 0:
        raise RuntimeError(f"Contracts API error: {data}")

    contracts = data.get("data", [])
    symbols = []
    for c in contracts:
        sym = c.get("symbol", "")
        # Only USDT perpetuals
        if sym.endswith("-USDT"):
            symbols.append(sym)

    symbols.sort()
    return symbols


def fetch_klines_page(session, symbol, interval, start_ms, end_ms):
    """Fetch one page of klines from BingX. Returns list of candle dicts or None."""
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": str(int(start_ms)),
        "endTime": str(int(end_ms)),
        "limit": str(MAX_CANDLES),
    }

    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    url = BASE_URL + KLINES_PATH + "?" + query

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code", 0) != 0:
                code = data.get("code")
                msg = data.get("msg", "")
                # Rate limit or server error — retry
                if code in (429, -1003, -1015, 100400, 100429):
                    wait = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logging.warning(
                        "Rate limit %s (code=%s), retry in %.1fs",
                        symbol, code, wait
                    )
                    time.sleep(wait)
                    continue
                logging.error("Klines API error %s: code=%s msg=%s", symbol, code, msg)
                return None

            raw = data.get("data", [])
            if not raw:
                return []
            return raw

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_err = e
            wait = (2 ** attempt) + random.uniform(0.5, 1.5)
            logging.warning(
                "Klines %s attempt %d/%d: %s, retry in %.1fs",
                symbol, attempt + 1, MAX_RETRIES, type(e).__name__, wait
            )
            time.sleep(wait)

        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, "status_code", 0)
            if status in (429, 500, 502, 503, 504):
                wait = (2 ** attempt) + random.uniform(2, 5)
                logging.warning("HTTP %s %s, retry in %.1fs", status, symbol, wait)
                time.sleep(wait)
                continue
            logging.error("HTTP %s for %s: %s", status, symbol, e)
            return None

        except (ValueError, KeyError) as e:
            logging.error("Parse error %s: %s", symbol, e)
            return None

    logging.error("Klines failed after %d retries: %s (%s)", MAX_RETRIES, symbol, last_err)
    return None


def parse_klines(raw):
    """Parse BingX kline response (objects or arrays) into DataFrame."""
    if not raw:
        return pd.DataFrame()

    if isinstance(raw[0], dict):
        df = pd.DataFrame(raw)
        col_map = {}
        for col in df.columns:
            lc = col.lower()
            if lc in ("open", "high", "low", "close", "volume", "time"):
                col_map[col] = lc
        df = df.rename(columns=col_map)
    elif isinstance(raw[0], list):
        # BingX array order: [time, open, close, high, low, volume, ...]
        ncols = len(raw[0])
        base_cols = ["time", "open", "close", "high", "low", "volume"]
        extra = ["extra_" + str(i) for i in range(max(0, ncols - 6))]
        df = pd.DataFrame(raw, columns=base_cols + extra)
    else:
        return pd.DataFrame()

    # Convert numerics
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "time" in df.columns:
        df["time"] = pd.to_numeric(df["time"], errors="coerce").astype("int64")

    # Keep only needed columns
    keep = [c for c in ["time", "open", "high", "low", "close", "volume"] if c in df.columns]
    df = df[keep].copy()
    df = df.sort_values("time").reset_index(drop=True)
    return df


def fetch_symbol_full(session, symbol, start_ms, end_ms, coin_bar=None, coin_base=0.0):
    """Fetch all 1m candles for a symbol between start_ms and end_ms."""
    all_candles = []
    cursor = start_ms
    had_error = False
    empty_streak = 0
    total_range_ms = end_ms - start_ms
    total_candles = 0
    prev_outer_n = coin_base

    pbar = tqdm(
        total=100,
        desc=f"  {symbol}",
        unit="%",
        bar_format="{l_bar}{bar}| {n:.0f}% [{elapsed}<{remaining}, {postfix}]",
        leave=False,
    )
    pbar.set_postfix_str("0 candles")

    def _update_outer(pct_inner):
        """Advance the outer coin_bar fractionally based on inner progress."""
        nonlocal prev_outer_n
        if coin_bar is None:
            return
        new_n = coin_base + (pct_inner / 100.0)
        delta = new_n - prev_outer_n
        if delta > 0:
            coin_bar.update(delta)
            prev_outer_n = new_n

    while cursor < end_ms:
        page_end = min(cursor + MAX_CANDLES * ONE_MINUTE_MS, end_ms)
        raw = fetch_klines_page(session, symbol, "1m", cursor, page_end)

        if raw is None:
            logging.error("Hard error fetching %s, aborting symbol", symbol)
            had_error = True
            break

        if not raw:
            empty_streak += 1
            if empty_streak >= 3:
                jump = min(MAX_CANDLES * ONE_MINUTE_MS * 10, end_ms - cursor)
                cursor += jump
            else:
                cursor = page_end
            pct = min(100, ((cursor - start_ms) / total_range_ms) * 100)
            pbar.n = pct
            date_str = pd.Timestamp(cursor, unit="ms", tz="UTC").strftime("%Y-%m-%d")
            pbar.set_postfix_str(f"{total_candles:,} candles, scanning {date_str}")
            pbar.refresh()
            _update_outer(pct)
            continue

        df = parse_klines(raw)
        if df.empty:
            empty_streak += 1
            cursor = page_end
            pct = min(100, ((cursor - start_ms) / total_range_ms) * 100)
            pbar.n = pct
            pbar.refresh()
            _update_outer(pct)
            continue

        empty_streak = 0
        all_candles.append(df)
        max_ts = int(df["time"].max())
        total_candles += len(df)

        cursor = max_ts + ONE_MINUTE_MS
        pct = min(100, ((cursor - start_ms) / total_range_ms) * 100)
        pbar.n = pct
        pbar.set_postfix_str(f"{total_candles:,} candles")
        pbar.refresh()
        _update_outer(pct)

        time.sleep(RATE_LIMIT_SLEEP)

    pbar.n = 100
    pbar.refresh()
    pbar.close()
    _update_outer(100)

    if not all_candles:
        return pd.DataFrame()

    combined = pd.concat(all_candles, ignore_index=True)
    combined = combined.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    if had_error:
        logging.warning("PARTIAL data for %s: %d candles saved before error", symbol, len(combined))
    return combined


def to_parquet_format(df):
    """Convert fetched BingX data to standard parquet schema."""
    out = pd.DataFrame()
    out["timestamp"] = df["time"].astype("int64")
    out["open"] = df["open"].astype("float64")
    out["high"] = df["high"].astype("float64")
    out["low"] = df["low"].astype("float64")
    out["close"] = df["close"].astype("float64")
    out["base_vol"] = df["volume"].astype("float64")
    out["quote_vol"] = np.nan  # BingX does not provide turnover
    out["datetime"] = pd.to_datetime(out["timestamp"], unit="ms", utc=True)
    return out


def resample_5m(df_1m):
    """Resample 1m parquet-format DataFrame to 5m."""
    if df_1m.empty:
        return pd.DataFrame()

    df = df_1m.copy()
    df = df.set_index("datetime")

    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "base_vol": "sum",
        "quote_vol": "sum",
        "timestamp": "first",
    }

    resampled = df.resample("5min").agg(agg).dropna(subset=["close"])
    resampled["quote_vol"] = np.nan  # preserve NaN (BingX has no turnover)
    resampled = resampled.reset_index()

    # Reorder columns to match schema
    resampled = resampled[["timestamp", "open", "high", "low", "close",
                           "base_vol", "quote_vol", "datetime"]]
    return resampled


def save_parquet(df, filepath, meta_path):
    """Save DataFrame as parquet + meta file."""
    df.to_parquet(filepath, index=False, engine="pyarrow")
    start_ms = int(df["timestamp"].min())
    end_ms = int(df["timestamp"].max())
    meta_path.write_text(f"{start_ms},{end_ms}")


def main():
    """Entry point for BingX OHLCV fetcher."""
    parser = argparse.ArgumentParser(
        description="Fetch BingX perpetual futures 1m OHLCV data"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="List symbols only, do not fetch data")
    parser.add_argument("--symbol", type=str, default=None,
                        help="Fetch a single symbol (e.g. BTC-USDT)")
    parser.add_argument("--max-coins", type=int, default=0,
                        help="Max coins to fetch (0 = all)")
    parser.add_argument("--months", type=int, default=DEFAULT_MONTHS,
                        help="How many months back to fetch (default 12)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip coins that already have a parquet file")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: data/cache)")
    parser.add_argument("--resume-from", type=str, default=None,
                        help="Resume from this symbol (alphabetical, skip earlier)")
    args = parser.parse_args()

    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("BingX OHLCV Fetcher started")
    logger.info("Months back: %d", args.months)

    cache_dir = Path(args.output_dir) if args.output_dir else DEFAULT_CACHE
    cache_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", cache_dir)

    session = requests.Session()
    session.headers.update({"User-Agent": "four-pillars-fetcher/1.0"})

    # ── discover symbols ──────────────────────────────────────────────────
    if args.symbol:
        symbols = [args.symbol]
        logger.info("Single symbol mode: %s", args.symbol)
    else:
        logger.info("Discovering all BingX USDT perp symbols...")
        symbols = fetch_all_perp_symbols(session)
        logger.info("Found %d USDT perpetual symbols", len(symbols))

    if args.resume_from:
        before = len(symbols)
        symbols = [s for s in symbols if s >= args.resume_from]
        logger.info("Resuming from %s: %d -> %d symbols", args.resume_from, before, len(symbols))

    if args.max_coins > 0:
        symbols = symbols[:args.max_coins]
        logger.info("Limited to %d symbols", len(symbols))

    if args.dry_run:
        logger.info("DRY RUN — listing %d symbols:", len(symbols))
        for i, s in enumerate(symbols):
            parq_name = bingx_to_parquet_symbol(s) + "_1m.parquet"
            exists = (cache_dir / parq_name).exists()
            tag = " [EXISTS]" if exists else ""
            logger.info("  %3d. %s -> %s%s", i + 1, s, parq_name, tag)
        existing_count = sum(1 for s in symbols if (cache_dir / (bingx_to_parquet_symbol(s) + "_1m.parquet")).exists())
        logger.info("Total: %d symbols, %d already cached", len(symbols), existing_count)
        return

    # ── time range ────────────────────────────────────────────────────────
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (args.months * 30 * 24 * 60 * 60 * 1000)
    logger.info(
        "Time range: %s to %s",
        pd.Timestamp(start_ms, unit="ms", tz="UTC").strftime("%Y-%m-%d"),
        pd.Timestamp(now_ms, unit="ms", tz="UTC").strftime("%Y-%m-%d"),
    )

    # ── fetch loop ────────────────────────────────────────────────────────
    total = len(symbols)
    success = 0
    skipped = 0
    failed = 0
    errors = []
    t0 = time.time()

    coin_bar = tqdm(
        total=total,
        desc="Coins",
        unit="coin",
        bar_format="{l_bar}{bar}| {n:.1f}/{total_fmt} [{elapsed}<{remaining}, {postfix}]",
    )

    try:
        for idx, sym in enumerate(symbols):
            parq_sym = bingx_to_parquet_symbol(sym)
            parq_1m = cache_dir / f"{parq_sym}_1m.parquet"
            meta_1m = cache_dir / f"{parq_sym}_1m.meta"
            parq_5m = cache_dir / f"{parq_sym}_5m.parquet"
            meta_5m = cache_dir / f"{parq_sym}_5m.meta"

            coin_bar.set_description(f"Coins ({sym})")
            coin_bar.set_postfix_str(f"ok={success} fail={failed} skip={skipped}")
            coin_base = float(idx)

            if args.skip_existing and parq_1m.exists():
                skipped += 1
                coin_bar.n = float(idx + 1)
                coin_bar.refresh()
                continue

            t_sym = time.time()
            df_raw = fetch_symbol_full(session, sym, start_ms, now_ms,
                                       coin_bar=coin_bar, coin_base=coin_base)

            if df_raw.empty:
                failed += 1
                errors.append(sym)
                logging.warning("%s: no data returned", sym)
                coin_bar.n = float(idx + 1)
                coin_bar.refresh()
                continue

            # Convert to parquet format
            df_1m = to_parquet_format(df_raw)
            df_1m = df_1m.dropna(subset=["close"])

            if df_1m.empty:
                failed += 1
                errors.append(sym)
                logging.warning("%s: all rows NaN after conversion", sym)
                coin_bar.n = float(idx + 1)
                coin_bar.refresh()
                continue

            # Save 1m
            save_parquet(df_1m, parq_1m, meta_1m)

            # Resample and save 5m
            df_5m = resample_5m(df_1m)
            if not df_5m.empty:
                save_parquet(df_5m, parq_5m, meta_5m)

            elapsed_sym = time.time() - t_sym
            date_range = (
                pd.Timestamp(int(df_1m["timestamp"].min()), unit="ms", tz="UTC").strftime("%Y-%m-%d")
                + " to "
                + pd.Timestamp(int(df_1m["timestamp"].max()), unit="ms", tz="UTC").strftime("%Y-%m-%d")
            )
            logging.info(
                "%s: %d 1m, %d 5m, %s (%.1fs)",
                sym, len(df_1m), len(df_5m), date_range, elapsed_sym,
            )
            success += 1
            coin_bar.n = float(idx + 1)
            coin_bar.refresh()

    except KeyboardInterrupt:
        coin_bar.close()
        logger.info("")
        logger.info("INTERRUPTED by user (Ctrl+C)")
        logger.info("Resume with: --skip-existing --resume-from %s", sym)

    coin_bar.close()

    # ── summary ───────────────────────────────────────────────────────────
    elapsed = time.time() - t0
    logger.info("=" * 60)
    logger.info("DONE in %.0f seconds (%.1f minutes)", elapsed, elapsed / 60)
    logger.info("Success: %d | Skipped: %d | Failed: %d | Total: %d", success, skipped, failed, total)
    if errors:
        logger.info("Failed symbols: " + ", ".join(errors))


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
print(f'  python "{OUT}" --symbol BTC-USDT')
print(f'  python "{OUT}" --max-coins 5')
print(f'  python "{OUT}"')
print(f'  python "{OUT}" --skip-existing --resume-from ETH-USDT')
