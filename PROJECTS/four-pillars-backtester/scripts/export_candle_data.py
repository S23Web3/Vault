"""
Candle Data Export Tool
=======================
Exports parquet OHLCV data to a chosen destination for sharing.
Supports selective export by data source, symbol filter, and output format.

Usage:
    python export_candle_data.py
    python export_candle_data.py --dest D:\export --source bingx --format parquet
    python export_candle_data.py --dest \\NAS\share\candles --symbols BTC,ETH,SOL
    python export_candle_data.py --list   # just show what's available
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ── Data source registry ────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

SOURCES = {
    "cache":      {"path": DATA_ROOT / "cache",               "desc": "Latest candle cache (1m + 5m)"},
    "historical": {"path": DATA_ROOT / "historical",          "desc": "Historical archive"},
    "bingx":      {"path": DATA_ROOT / "bingx",               "desc": "BingX exchange data (1m + 5m)"},
    "csv":        {"path": DATA_ROOT / "csv",                  "desc": "CSV format candles"},
    "periods_23": {"path": DATA_ROOT / "periods" / "2023-2024","desc": "Period data 2023-2024"},
    "periods_24": {"path": DATA_ROOT / "periods" / "2024-2025","desc": "Period data 2024-2025"},
    "coingecko":  {"path": DATA_ROOT / "coingecko",            "desc": "CoinGecko metadata"},
    "trading_tools": {
        "path": PROJECT_ROOT.parent.parent / "trading-tools" / "data" / "cache",
        "desc": "Trading-tools candle cache",
    },
}


def fmt_size(nbytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} PB"


def scan_source(path: Path) -> dict:
    """Scan a source directory and return stats."""
    if not path.exists():
        return {"exists": False, "files": 0, "size": 0, "symbols": set(), "extensions": {}}

    files = list(path.rglob("*"))
    data_files = [f for f in files if f.is_file() and f.suffix in (".parquet", ".csv", ".json", ".meta")]
    total_size = sum(f.stat().st_size for f in data_files)

    symbols = set()
    extensions = {}
    for f in data_files:
        ext = f.suffix
        extensions[ext] = extensions.get(ext, 0) + 1
        # extract symbol from SYMBOLUSDT_1m.parquet pattern
        name = f.stem
        if "_" in name:
            symbols.add(name.rsplit("_", 1)[0])

    return {
        "exists": True,
        "files": len(data_files),
        "size": total_size,
        "symbols": symbols,
        "extensions": extensions,
    }


def list_sources():
    """Print a summary of all available data sources."""
    print("\n  CANDLE DATA INVENTORY")
    print("  " + "=" * 70)

    total_size = 0
    total_files = 0

    for key, info in SOURCES.items():
        stats = scan_source(info["path"])
        if not stats["exists"]:
            status = "NOT FOUND"
            size_str = "-"
            file_str = "-"
            sym_str = "-"
        else:
            status = "OK"
            size_str = fmt_size(stats["size"])
            file_str = str(stats["files"])
            sym_str = str(len(stats["symbols"]))
            total_size += stats["size"]
            total_files += stats["files"]

        exts = ", ".join(f"{e}({c})" for e, c in stats.get("extensions", {}).items()) if stats["exists"] else ""
        print(f"\n  [{key}]  {info['desc']}")
        print(f"    Path:    {info['path']}")
        print(f"    Status:  {status}  |  Files: {file_str}  |  Size: {size_str}  |  Symbols: {sym_str}")
        if exts:
            print(f"    Types:   {exts}")

    print(f"\n  TOTAL: {total_files} files, {fmt_size(total_size)}")
    print()


def filter_files(source_path: Path, symbols: list[str] | None, fmt: str) -> list[Path]:
    """Get list of files to export, filtered by symbol and format."""
    if fmt == "parquet":
        pattern = "*.parquet"
    elif fmt == "csv":
        pattern = "*.csv"
    else:
        pattern = "*"

    files = sorted(source_path.rglob(pattern))
    # always include .meta and .json companion files
    companions = sorted(source_path.rglob("*.meta")) + sorted(source_path.rglob("*.json"))
    all_files = list(set(files + companions))

    if not symbols:
        return sorted(all_files)

    # filter to matching symbols
    symbols_upper = [s.upper().strip() for s in symbols]
    filtered = []
    for f in all_files:
        name = f.stem.upper()
        matched = False
        for sym in symbols_upper:
            # match BTCUSDT from BTC, or exact match
            if name.startswith(sym + "USDT") or name.startswith(sym + "_") or name == sym:
                matched = True
                break
        if matched:
            filtered.append(f)
        # always include metadata files that don't match symbol pattern
        elif f.suffix == ".json" and "_" not in f.stem:
            filtered.append(f)

    return sorted(filtered)


def convert_parquet_to_csv(src: Path, dst: Path):
    """Convert a parquet file to CSV."""
    if not HAS_PANDAS:
        print(f"    SKIP (pandas not installed): {src.name}")
        return False
    try:
        df = pd.read_parquet(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dst, index=False)
        return True
    except Exception as e:
        print(f"    ERROR converting {src.name}: {e}")
        return False


def export_data(sources: list[str], dest: Path, symbols: list[str] | None,
                out_format: str, convert: bool, dry_run: bool):
    """Copy candle data to destination."""
    dest.mkdir(parents=True, exist_ok=True)

    total_copied = 0
    total_bytes = 0
    total_skipped = 0
    start_time = time.time()

    for src_key in sources:
        if src_key not in SOURCES:
            print(f"  Unknown source: {src_key} — skipping")
            continue

        src_info = SOURCES[src_key]
        src_path = src_info["path"]

        if not src_path.exists():
            print(f"  [{src_key}] path not found, skipping: {src_path}")
            continue

        files = filter_files(src_path, symbols, out_format)
        if not files:
            print(f"  [{src_key}] no matching files")
            continue

        dest_dir = dest / src_key
        src_size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"\n  [{src_key}] {len(files)} files ({fmt_size(src_size)}) -> {dest_dir}")

        for f in files:
            rel = f.relative_to(src_path)
            target = dest_dir / rel

            # handle parquet -> csv conversion
            if convert and f.suffix == ".parquet" and out_format == "csv":
                target = target.with_suffix(".csv")
                if dry_run:
                    print(f"    CONVERT {rel} -> {target.name}")
                    total_copied += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if convert_parquet_to_csv(f, target):
                    total_copied += 1
                    total_bytes += target.stat().st_size
                continue

            if dry_run:
                print(f"    COPY {rel}")
                total_copied += 1
                continue

            target.parent.mkdir(parents=True, exist_ok=True)

            # skip if destination exists and same size
            if target.exists() and target.stat().st_size == f.stat().st_size:
                total_skipped += 1
                continue

            shutil.copy2(f, target)
            total_copied += 1
            total_bytes += f.stat().st_size

            # progress every 50 files
            if total_copied % 50 == 0:
                print(f"    ... {total_copied} files copied ({fmt_size(total_bytes)})")

    elapsed = time.time() - start_time
    print(f"\n  {'DRY RUN ' if dry_run else ''}DONE: {total_copied} files copied, "
          f"{total_skipped} skipped (already exist), "
          f"{fmt_size(total_bytes)} in {elapsed:.1f}s")

    # write a manifest
    if not dry_run and total_copied > 0:
        manifest = {
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sources": sources,
            "symbols_filter": symbols,
            "format": out_format,
            "files_copied": total_copied,
            "files_skipped": total_skipped,
            "total_bytes": total_bytes,
            "schema": {
                "columns": ["timestamp", "open", "high", "low", "close", "base_vol", "quote_vol", "datetime"],
                "timestamp_unit": "milliseconds (epoch)",
                "datetime_tz": "UTC",
                "volume_note": "base_vol = coin qty, quote_vol = USDT notional",
            },
            "reading_example": (
                "import pandas as pd\n"
                "df = pd.read_parquet('BTCUSDT_1m.parquet')\n"
                "print(df.head())"
            ),
        }
        manifest_path = dest / "MANIFEST.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"  Manifest written to {manifest_path}")


def interactive_mode():
    """Walk the user through export options."""
    print("\n  CANDLE DATA EXPORT TOOL")
    print("  " + "=" * 40)

    # show sources
    list_sources()

    # pick sources
    available = [k for k, v in SOURCES.items() if v["path"].exists()]
    print(f"  Available sources: {', '.join(available)}")
    print(f"  Recommended for sharing: bingx, cache, coingecko")
    src_input = input("\n  Which sources to export? (comma-separated, or 'all'): ").strip()

    if src_input.lower() == "all":
        sources = available
    else:
        sources = [s.strip() for s in src_input.split(",") if s.strip() in available]
        if not sources:
            print("  No valid sources selected.")
            return

    # pick destination
    dest_input = input("  Destination path (e.g. D:\\export, /mnt/usb/candles): ").strip()
    if not dest_input:
        print("  No destination given.")
        return
    dest = Path(dest_input)

    # symbol filter
    sym_input = input("  Filter symbols? (e.g. BTC,ETH,SOL or Enter for all): ").strip()
    symbols = [s.strip() for s in sym_input.split(",") if s.strip()] if sym_input else None

    # format
    fmt_input = input("  Output format? [parquet/csv/both] (default: parquet): ").strip().lower()
    if fmt_input not in ("parquet", "csv", "both"):
        fmt_input = "parquet"

    # dry run first
    print("\n  --- DRY RUN (nothing copied yet) ---")
    out_fmt = "parquet" if fmt_input != "csv" else "csv"
    convert = fmt_input == "csv"
    export_data(sources, dest, symbols, out_fmt, convert, dry_run=True)

    confirm = input("\n  Proceed with copy? [y/N]: ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return

    export_data(sources, dest, symbols, out_fmt, convert, dry_run=False)

    # if both formats requested, do csv conversion pass
    if fmt_input == "both":
        print("\n  --- Converting parquet -> CSV copies ---")
        export_data(sources, dest / "csv_copies", symbols, "csv", convert=True, dry_run=False)

    print(f"\n  Export complete! Share the folder: {dest}")
    print("  Your mate can read files with:")
    print("    import pandas as pd")
    print("    df = pd.read_parquet('BTCUSDT_1m.parquet')")
    print()


def main():
    parser = argparse.ArgumentParser(description="Export candle data for sharing")
    parser.add_argument("--list", action="store_true", help="List available data sources and exit")
    parser.add_argument("--dest", type=str, help="Destination directory path")
    parser.add_argument("--source", type=str, help="Comma-separated source keys (e.g. bingx,cache)")
    parser.add_argument("--symbols", type=str, help="Comma-separated symbol filter (e.g. BTC,ETH,SOL)")
    parser.add_argument("--format", type=str, choices=["parquet", "csv", "both"], default="parquet",
                        help="Output format (default: parquet)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be copied without copying")
    args = parser.parse_args()

    if args.list:
        list_sources()
        return

    # no args = interactive mode
    if not args.dest:
        interactive_mode()
        return

    # CLI mode
    dest = Path(args.dest)
    available = [k for k, v in SOURCES.items() if v["path"].exists()]

    if args.source:
        sources = [s.strip() for s in args.source.split(",")]
    else:
        sources = available

    symbols = [s.strip() for s in args.symbols.split(",")] if args.symbols else None
    convert = args.format == "csv"

    export_data(sources, dest, symbols, args.format, convert, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
