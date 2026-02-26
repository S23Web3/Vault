#!/usr/bin/env python3
"""
Timeframe Resampling Tool
Converts 1-minute candle data to any higher timeframe (5m, 15m, 1h, etc.)

Usage:
    # Test with 1 coin
    python resample_timeframes.py --symbol BTCUSDT --timeframe 5m --test

    # Process all coins
    python resample_timeframes.py --timeframe 5m --all

    # Process specific coins
    python resample_timeframes.py --timeframe 5m --symbols BTCUSDT ETHUSDT 1000PEPEUSDT
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import sys
from typing import Optional, List

# Fix Windows UTF-8 encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


class TimeframeResampler:
    """Resamples 1m OHLCV data to higher timeframes"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            raise FileNotFoundError(f"Cache directory not found: {self.cache_dir}")

        # Timeframe mapping (string → pandas resample rule)
        self.timeframe_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "1h": "1h",
            "2h": "2h",
            "4h": "4h",
            "1d": "1D",
        }

    def resample_ohlcv(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample 1m OHLCV data to target timeframe

        Args:
            df: DataFrame with columns [timestamp, open, high, low, close, base_vol, quote_vol, datetime]
            timeframe: Target timeframe (5m, 15m, 1h, etc.)

        Returns:
            Resampled DataFrame with same columns
        """
        if timeframe not in self.timeframe_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(self.timeframe_map.keys())}")

        # Ensure datetime is index and timezone-aware
        if "datetime" not in df.columns and "datetime" not in str(df.index.name):
            raise ValueError("DataFrame must have 'datetime' column or index")

        # Set datetime as index if not already
        if df.index.name != "datetime":
            df = df.set_index("datetime")

        # Convert to UTC timezone if not already
        if df.index.tz is None:
            df.index = pd.to_datetime(df.index, utc=True)
        elif df.index.tz != pd.Timestamp("2000-01-01", tz="UTC").tz:
            df.index = df.index.tz_convert("UTC")

        # Resample using proper OHLCV aggregation
        resample_rule = self.timeframe_map[timeframe]

        resampled = df.resample(resample_rule).agg(
            {
                "timestamp": "first",  # First timestamp in window
                "open": "first",  # First open in window
                "high": "max",  # Highest high in window
                "low": "min",  # Lowest low in window
                "close": "last",  # Last close in window
                "base_vol": "sum",  # Sum of base volume
                "quote_vol": "sum",  # Sum of quote volume
            }
        )

        # Drop incomplete candles (last row if volume is NaN)
        resampled = resampled.dropna()

        # Reset index to make datetime a column again
        resampled = resampled.reset_index()

        return resampled

    def resample_file(
        self, symbol: str, timeframe: str, output_dir: Optional[Path] = None, overwrite: bool = False
    ) -> Optional[Path]:
        """
        Resample a single coin's 1m data to target timeframe

        Args:
            symbol: Coin symbol (e.g., BTCUSDT)
            timeframe: Target timeframe (5m, 15m, etc.)
            output_dir: Output directory (default: cache_dir)
            overwrite: Overwrite existing file

        Returns:
            Path to resampled file, or None if skipped
        """
        # Input file path
        input_file = self.cache_dir / f"{symbol}_1m.parquet"
        if not input_file.exists():
            print(f"⚠️  {symbol}: Input file not found: {input_file}")
            return None

        # Output file path
        if output_dir is None:
            output_dir = self.cache_dir
        output_file = output_dir / f"{symbol}_{timeframe}.parquet"

        # Check if already exists
        if output_file.exists() and not overwrite:
            print(f"⏭️  {symbol}: Already exists (use --overwrite to replace): {output_file.name}")
            return output_file

        # Load 1m data
        try:
            df_1m = pd.read_parquet(input_file)
        except Exception as e:
            print(f"❌ {symbol}: Failed to load: {e}")
            return None

        # Resample
        try:
            df_resampled = self.resample_ohlcv(df_1m, timeframe)
        except Exception as e:
            print(f"❌ {symbol}: Failed to resample: {e}")
            return None

        # Save
        try:
            df_resampled.to_parquet(output_file, index=False)
        except Exception as e:
            print(f"❌ {symbol}: Failed to save: {e}")
            return None

        # Stats
        reduction = (1 - len(df_resampled) / len(df_1m)) * 100
        print(
            f"✅ {symbol}: {len(df_1m):,} → {len(df_resampled):,} candles ({reduction:.1f}% reduction) → {output_file.name}"
        )

        return output_file

    def resample_all(self, timeframe: str, output_dir: Optional[Path] = None, overwrite: bool = False) -> dict:
        """
        Resample all coins in cache directory

        Args:
            timeframe: Target timeframe (5m, 15m, etc.)
            output_dir: Output directory (default: cache_dir)
            overwrite: Overwrite existing files

        Returns:
            Dict with success/failed counts
        """
        # Find all 1m parquet files
        input_files = list(self.cache_dir.glob("*_1m.parquet"))
        symbols = [f.stem.replace("_1m", "") for f in input_files]

        print(f"\n📊 Found {len(symbols)} coins with 1m data")
        print(f"🎯 Target timeframe: {timeframe}")
        print(f"📁 Output directory: {output_dir or self.cache_dir}\n")

        results = {"success": [], "failed": [], "skipped": []}

        for symbol in symbols:
            result = self.resample_file(symbol, timeframe, output_dir, overwrite)
            if result:
                results["success"].append(symbol)
            else:
                results["failed"].append(symbol)

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Success: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"{'='*60}\n")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Resample 1m candle data to higher timeframes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with 1 coin
  python resample_timeframes.py --symbol BTCUSDT --timeframe 5m

  # Process all coins
  python resample_timeframes.py --timeframe 5m --all

  # Process specific coins
  python resample_timeframes.py --timeframe 5m --symbols BTCUSDT ETHUSDT 1000PEPEUSDT

  # Overwrite existing files
  python resample_timeframes.py --timeframe 5m --all --overwrite
        """,
    )

    parser.add_argument("--cache-dir", default="data/cache", help="Cache directory (default: data/cache)")
    parser.add_argument(
        "--timeframe",
        "-t",
        required=True,
        choices=["5m", "15m", "30m", "1h", "2h", "4h", "1d"],
        help="Target timeframe",
    )
    parser.add_argument("--symbol", "-s", help="Single symbol to process (e.g., BTCUSDT)")
    parser.add_argument("--symbols", nargs="+", help="Multiple symbols to process")
    parser.add_argument("--all", "-a", action="store_true", help="Process all coins")
    parser.add_argument("--output-dir", "-o", help="Output directory (default: same as cache-dir)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--test", action="store_true", help="Test mode (process single coin, show stats)")

    args = parser.parse_args()

    # Validate arguments
    if not any([args.symbol, args.symbols, args.all, args.test]):
        parser.error("Must specify --symbol, --symbols, --all, or --test")

    # Initialize resampler
    try:
        resampler = TimeframeResampler(cache_dir=args.cache_dir)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    # Test mode (process BTCUSDT)
    if args.test:
        print("🧪 TEST MODE: Processing BTCUSDT\n")
        result = resampler.resample_file("BTCUSDT", args.timeframe, output_dir, args.overwrite)

        if result:
            # Show sample data
            df = pd.read_parquet(result)
            print(f"\n📊 Sample of {args.timeframe} data:")
            print(df.head(10))
            print(f"\nShape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        sys.exit(0 if result else 1)

    # Single symbol
    if args.symbol:
        result = resampler.resample_file(args.symbol, args.timeframe, output_dir, args.overwrite)
        sys.exit(0 if result else 1)

    # Multiple symbols
    if args.symbols:
        results = {"success": [], "failed": []}
        for symbol in args.symbols:
            result = resampler.resample_file(symbol, args.timeframe, output_dir, args.overwrite)
            if result:
                results["success"].append(symbol)
            else:
                results["failed"].append(symbol)

        print(f"\n✅ Success: {len(results['success'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        sys.exit(0 if results["failed"] == 0 else 1)

    # All symbols
    if args.all:
        results = resampler.resample_all(args.timeframe, output_dir, args.overwrite)
        sys.exit(0 if len(results["failed"]) == 0 else 1)


if __name__ == "__main__":
    main()
