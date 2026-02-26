"""
CLI utility for converting OHLCV CSV files to internal parquet format.
Wraps data.normalizer.OHLCVNormalizer.

Usage:
  python scripts/convert_csv.py --input data.csv --symbol BTCUSDT
  python scripts/convert_csv.py --input ./exports/ --batch
  python scripts/convert_csv.py --input data.csv --symbol BTCUSDT --preview
  python scripts/convert_csv.py --input data.csv --symbol BTCUSDT --resample 5m,15m,1h
  python scripts/convert_csv.py --input data.csv --symbol BTCUSDT \
      --columns '{"time":"timestamp","o":"open","h":"high","l":"low","c":"close","v":"base_vol"}'
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.normalizer import OHLCVNormalizer, NormalizerError


def main():
    parser = argparse.ArgumentParser(
        description="Convert OHLCV CSV files to internal parquet format"
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to CSV file or folder (with --batch)"
    )
    parser.add_argument(
        "--symbol", default=None,
        help="Symbol name (e.g., BTCUSDT). Required for single file, ignored with --batch"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Show detected format without converting"
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Process all CSV files in folder"
    )
    parser.add_argument(
        "--columns", default=None,
        help='Manual column map as JSON: \'{"time":"timestamp","o":"open",...}\''
    )
    parser.add_argument(
        "--interval", default=None,
        help="Force interval instead of auto-detect (1m, 5m, 15m, 1h, 4h, 1d)"
    )
    parser.add_argument(
        "--resample", default=None,
        help="Create additional resampled versions (e.g., 5m,15m,1h)"
    )
    parser.add_argument(
        "--cache-dir", default="data/cache",
        help="Output directory for parquet files (default: data/cache)"
    )
    args = parser.parse_args()

    normalizer = OHLCVNormalizer(cache_dir=args.cache_dir)
    input_path = Path(args.input)

    # Parse column override if provided
    column_map = None
    if args.columns:
        try:
            raw_map = json.loads(args.columns)
            # raw_map: {"source_col": "target_field"} -> invert to {"target_field": "source_col"}
            column_map = {v: k for k, v in raw_map.items()}
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid --columns JSON: {e}")
            sys.exit(1)

    # -- Preview mode --
    if args.preview:
        if not input_path.exists():
            print(f"ERROR: File not found: {input_path}")
            sys.exit(1)
        if input_path.is_dir():
            csv_files = sorted(input_path.glob("*.csv"))
            if not csv_files:
                print(f"No CSV files in {input_path}")
                sys.exit(1)
            for f in csv_files:
                print(f"\n--- {f.name} ---")
                info = normalizer.detect_format(str(f))
                _print_format_info(info)
        else:
            info = normalizer.detect_format(str(input_path))
            _print_format_info(info)
        return

    # -- Batch mode --
    if args.batch:
        if not input_path.is_dir():
            print(f"ERROR: --batch requires a directory. Got: {input_path}")
            sys.exit(1)
        results = normalizer.normalize_batch(str(input_path))

        # Resample if requested
        if args.resample and results:
            intervals = [i.strip() for i in args.resample.split(",")]
            _do_resample(normalizer, results, intervals)
        return

    # -- Single file mode --
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)
    if not args.symbol:
        print("ERROR: --symbol required for single file conversion")
        sys.exit(1)

    try:
        df = normalizer.normalize(
            str(input_path),
            args.symbol,
            column_map=column_map,
            timestamp_format=None,
        )

        # Resample if requested
        if args.resample:
            intervals = [i.strip() for i in args.resample.split(",")]
            _do_resample(normalizer, {args.symbol.upper(): df}, intervals)

    except NormalizerError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def _print_format_info(info: dict):
    """Print format detection results."""
    print(f"  Delimiter:  {info['delimiter']!r}")
    print(f"  Columns:    {info['column_map']}")
    print(f"  Timestamp:  {info['timestamp_format']}")
    print(f"  Interval:   {info['interval']}")
    print(f"  Rows:       {info['rows']:,}")
    if info["date_range"]:
        print(f"  Date range: {info['date_range'][0]} to {info['date_range'][1]}")
    if info["missing_fields"]:
        print(f"  MISSING:    {info['missing_fields']}")
    if info["warnings"]:
        for w in info["warnings"]:
            print(f"  WARNING:    {w}")


def _do_resample(normalizer: OHLCVNormalizer, results: dict, intervals: list):
    """Create resampled versions for each symbol in results."""
    for symbol, df in results.items():
        for interval in intervals:
            try:
                df_r = normalizer.resample_ohlcv(df, interval)
                p = normalizer.cache_dir / f"{symbol}_{interval}.parquet"
                m = normalizer.cache_dir / f"{symbol}_{interval}.meta"
                df_r.to_parquet(p, engine="pyarrow", index=False)
                s = int(df_r["timestamp"].iloc[0])
                e = int(df_r["timestamp"].iloc[-1])
                m.write_text(f"{s},{e}")
                print(f"  Resampled:  {p} ({p.stat().st_size/1024/1024:.1f} MB)")
            except Exception as ex:
                print(f"  Resample {interval} failed for {symbol}: {ex}")


if __name__ == "__main__":
    main()
