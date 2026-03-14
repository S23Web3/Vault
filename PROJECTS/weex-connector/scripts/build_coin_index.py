"""
Build WEEX coin index: cross-reference WEEX perps against BingX and Bybit data.
Run: python scripts/build_coin_index.py
"""
import sys
import logging
import traceback
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup — dual handler (file + console)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_log_file = LOGS_DIR / ("build_coin_index_" + datetime.now(timezone.utc).strftime("%Y-%m-%d") + ".log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(str(_log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WEEX_EXCHANGE_INFO_URL = "https://api-contract.weex.com/capi/v3/market/exchangeInfo"
BINGX_DATA_DIR = (
    PROJECT_ROOT.parent
    / "four-pillars-backtester"
    / "data"
    / "bingx"
)
BYBIT_DATA_DIR = (
    PROJECT_ROOT.parent
    / "four-pillars-backtester"
    / "data"
    / "cache"
)
OUTPUT_CSV = PROJECT_ROOT / "docs" / "WEEX-COIN-INDEX.csv"
CSV_COLUMNS = [
    "symbol",
    "on_weex",
    "on_bingx",
    "on_bybit",
    "data_source",
    "quantityPrecision",
    "pricePrecision",
    "minOrderSize",
    "maxLeverage",
    "takerFeeRate",
]


# ---------------------------------------------------------------------------
# Fetch helpers
# ---------------------------------------------------------------------------

def fetch_weex_contracts() -> list[dict]:
    """Fetch all USDT-margined perpetual contracts from WEEX exchangeInfo endpoint."""
    log.info("Fetching WEEX contract list from %s", WEEX_EXCHANGE_INFO_URL)
    try:
        req = urllib.request.Request(
            WEEX_EXCHANGE_INFO_URL,
            headers={"User-Agent": "weex-coin-index/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        data = json.loads(raw)
    except Exception as exc:
        log.error("Failed to fetch WEEX exchangeInfo: %s", exc)
        log.debug(traceback.format_exc())
        return []

    # Response is a raw object (no wrapper) per WEEX GET endpoint convention
    # Structure: { "symbols": [...], "timezone": "...", "serverTime": ... }
    symbols_raw = data.get("symbols", [])
    if not symbols_raw:
        log.warning("No symbols in WEEX exchangeInfo response. Keys: %s", list(data.keys()))
        return []

    contracts = []
    for sym in symbols_raw:
        # Only USDT-margined perps (forwardContractFlag: true)
        if not sym.get("forwardContractFlag", False):
            continue
        contracts.append({
            "symbol": sym.get("symbol", ""),
            "quantityPrecision": sym.get("quantityPrecision", ""),
            "pricePrecision": sym.get("pricePrecision", ""),
            "minOrderSize": sym.get("minQty", sym.get("minOrderSize", "")),
            "maxLeverage": sym.get("maxLeverage", ""),
            "takerFeeRate": sym.get("takerFeeRate", ""),
        })

    log.info("WEEX: found %d USDT-margined perp contracts", len(contracts))
    return contracts


def load_local_symbols(data_dir: Path, label: str) -> set[str]:
    """
    Extract unique base symbols from parquet filenames in a data directory.

    Filename pattern: BTCUSDT_1m.parquet or BTCUSDT_5m.parquet
    Symbol extracted: strip trailing _Xm.parquet suffix, uppercase.
    """
    if not data_dir.exists():
        log.warning("%s data dir not found: %s", label, data_dir)
        return set()

    parquet_files = list(data_dir.glob("*.parquet"))
    log.info("%s: found %d parquet files in %s", label, len(parquet_files), data_dir)

    symbols: set[str] = set()
    for f in parquet_files:
        name = f.stem  # e.g. BTCUSDT_1m
        # Strip timeframe suffix: _1m, _5m, _15m, _1h, etc.
        parts = name.rsplit("_", 1)
        if len(parts) == 2:
            base = parts[0].upper()
        else:
            base = name.upper()
        symbols.add(base)

    log.info("%s: %d unique symbols extracted", label, len(symbols))
    return symbols


# ---------------------------------------------------------------------------
# Cross-reference
# ---------------------------------------------------------------------------

def build_index(
    weex_contracts: list[dict],
    bingx_symbols: set[str],
    bybit_symbols: set[str],
) -> list[dict]:
    """Cross-reference WEEX contracts with BingX and Bybit symbol sets; return row list."""
    rows = []
    for c in weex_contracts:
        sym = c["symbol"].upper()
        on_bingx = sym in bingx_symbols
        on_bybit = sym in bybit_symbols

        if on_bybit:
            data_source = "bybit"
        elif on_bingx:
            data_source = "bingx"
        else:
            data_source = "none"

        rows.append({
            "symbol": sym,
            "on_weex": True,
            "on_bingx": on_bingx,
            "on_bybit": on_bybit,
            "data_source": data_source,
            "quantityPrecision": c["quantityPrecision"],
            "pricePrecision": c["pricePrecision"],
            "minOrderSize": c["minOrderSize"],
            "maxLeverage": c["maxLeverage"],
            "takerFeeRate": c["takerFeeRate"],
        })

    # Sort: bybit-sourced first, then bingx-only, then none; alpha within each
    priority = {"bybit": 0, "bingx": 1, "none": 2}
    rows.sort(key=lambda r: (priority.get(r["data_source"], 3), r["symbol"]))
    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_csv(rows: list[dict], out_path: Path) -> None:
    """Write cross-reference rows to CSV at out_path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        log.warning("Output CSV already exists — overwriting: %s", out_path)
    with open(str(out_path), "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    log.info("CSV written: %s  (%d rows)", out_path, len(rows))


def print_summary(rows: list[dict]) -> None:
    """Print summary counts to console and log."""
    total_weex = len(rows)
    on_bybit = sum(1 for r in rows if r["on_bybit"])
    on_bingx = sum(1 for r in rows if r["on_bingx"])
    on_bingx_only = sum(1 for r in rows if r["on_bingx"] and not r["on_bybit"])
    weex_only = sum(1 for r in rows if r["data_source"] == "none")
    both = sum(1 for r in rows if r["on_bingx"] and r["on_bybit"])

    log.info("=" * 60)
    log.info("WEEX COIN INDEX SUMMARY")
    log.info("=" * 60)
    log.info("Total WEEX perp contracts  : %d", total_weex)
    log.info("Overlap with Bybit data    : %d", on_bybit)
    log.info("Overlap with BingX data    : %d", on_bingx)
    log.info("  - BingX AND Bybit        : %d", both)
    log.info("  - BingX only (no Bybit)  : %d", on_bingx_only)
    log.info("WEEX-only (no local data)  : %d", weex_only)
    log.info("=" * 60)
    log.info("Data source breakdown:")
    log.info("  bybit  (preferred)       : %d", on_bybit)
    log.info("  bingx  (fallback)        : %d", on_bingx_only)
    log.info("  none   (no local data)   : %d", weex_only)
    log.info("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Fetch WEEX contracts, cross-ref with local data, write CSV, print summary."""
    log.info("=== build_coin_index.py START ===")
    log.info("WEEX URL      : %s", WEEX_EXCHANGE_INFO_URL)
    log.info("BingX data dir: %s", BINGX_DATA_DIR)
    log.info("Bybit data dir: %s", BYBIT_DATA_DIR)
    log.info("Output CSV    : %s", OUTPUT_CSV)

    weex_contracts = fetch_weex_contracts()
    if not weex_contracts:
        log.error("No WEEX contracts fetched — aborting.")
        sys.exit(1)

    bingx_symbols = load_local_symbols(BINGX_DATA_DIR, "BingX")
    bybit_symbols = load_local_symbols(BYBIT_DATA_DIR, "Bybit")

    rows = build_index(weex_contracts, bingx_symbols, bybit_symbols)
    write_csv(rows, OUTPUT_CSV)
    print_summary(rows)

    log.info("=== build_coin_index.py DONE ===")


if __name__ == "__main__":
    main()
