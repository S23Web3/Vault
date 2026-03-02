"""
CLI entry point for fetching historical candle data from Bybit.
Run from terminal: python scripts/fetch_data.py --coins 5 --months 3

This is a standalone script meant to be run overnight from the terminal.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from data.fetcher import BybitFetcher


def load_config() -> dict:
    config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Fetch Bybit historical candle data")
    parser.add_argument("--coins", type=int, default=None,
                        help="Number of coins to fetch (default: all in config)")
    parser.add_argument("--months", type=int, default=3,
                        help="Months of history to fetch (default: 3)")
    parser.add_argument("--hours", type=int, default=None,
                        help="Hours of history (overrides --months for testing)")
    parser.add_argument("--symbols", nargs="+", default=None,
                        help="Specific symbols to fetch (overrides config)")
    parser.add_argument("--all", action="store_true",
                        help="Fetch all symbols found in cache (ignores config list)")
    parser.add_argument("--force", action="store_true",
                        help="Force re-fetch even if cached")
    parser.add_argument("--rate", type=float, default=0.1,
                        help="Seconds between API requests (default: 0.1)")
    args = parser.parse_args()

    config = load_config()

    # Cache dir
    cache_dir = Path(__file__).resolve().parent.parent / config.get("data", {}).get("cache_dir", "data/cache")

    # Determine symbols
    if args.symbols:
        symbols = args.symbols
    elif args.all:
        symbols = sorted(f.stem.replace("_1m", "") for f in cache_dir.glob("*_1m.parquet"))
        if not symbols:
            print("ERROR: --all specified but no cached parquets found in", cache_dir)
            sys.exit(1)
    else:
        symbols = config.get("coins", ["BTCUSDT"])

    if args.coins is not None:
        symbols = symbols[:args.coins]

    # Determine time range
    end_time = datetime.now(timezone.utc)
    if args.hours is not None:
        start_time = end_time - timedelta(hours=args.hours)
        range_desc = f"last {args.hours} hours"
    else:
        start_time = end_time - timedelta(days=args.months * 30)
        range_desc = f"last {args.months} months"

    print("=" * 60)
    print("Four Pillars — Bybit Data Fetcher")
    print("=" * 60)
    print(f"Symbols:    {len(symbols)} coins")
    print(f"Range:      {range_desc}")
    print(f"Start:      {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"End:        {end_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Cache:      {cache_dir}")
    print(f"Rate limit: {args.rate}s between requests")
    print(f"Force:      {args.force}")
    print("=" * 60)
    print()

    fetcher = BybitFetcher(cache_dir=str(cache_dir), rate_limit=args.rate)
    results = fetcher.fetch_multiple(symbols, start_time, end_time, force=args.force)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_candles = sum(len(df) for df in results.values())
    total_size = sum(
        (cache_dir / f"{s}_1m.parquet").stat().st_size
        for s in results.keys()
        if (cache_dir / f"{s}_1m.parquet").exists()
    )
    print(f"Symbols fetched: {len(results)}/{len(symbols)}")
    print(f"Total candles:   {total_candles:,}")
    print(f"Total size:      {total_size / 1024 / 1024:.1f} MB")

    failed = set(symbols) - set(results.keys())
    if failed:
        print(f"Failed:          {', '.join(failed)}")


if __name__ == "__main__":
    main()
