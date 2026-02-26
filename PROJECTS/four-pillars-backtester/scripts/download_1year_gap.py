"""
Download 1 YEAR of historical data (Feb 2024 to earliest cached).
ONLY downloads the MISSING gap.
Does NOT re-download existing data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.fetcher import BybitFetcher

HISTORICAL_DIR = ROOT / "data" / "historical"
CACHE_DIR = ROOT / "data" / "cache"
ONE_YEAR_AGO = "2024-02-11"  # 1 year from today
RATE_LIMIT = 1.0  # seconds between API calls

def download_missing_gap(symbol, fetcher):
    """Download ONLY the missing gap (1 year ago to earliest cached)."""
    
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    
    if not cache_file.exists():
        print(f"  {symbol}: No cache, skipping")
        return False
    
    # Load cache to check date range
    df = pd.read_parquet(cache_file)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    earliest_cached = df['datetime'].min()
    latest_cached = df['datetime'].max()
    
    # Calculate download range
    download_start = datetime.strptime(ONE_YEAR_AGO, "%Y-%m-%d").replace(tzinfo=earliest_cached.tzinfo)
    download_end = earliest_cached - timedelta(minutes=1)
    
    # Check if we need anything
    if earliest_cached <= download_start:
        print(f"  {symbol}: Already complete (has {earliest_cached.strftime('%Y-%m-%d')})")
        return True
    
    # Calculate gap size
    gap_days = (download_end - download_start).days
    gap_bars = gap_days * 1440  # 1440 minutes per day
    
    print(f"  {symbol}: Gap {gap_days} days ({download_start.strftime('%Y-%m-%d')} to {download_end.strftime('%Y-%m-%d')})...", end="", flush=True)
    
    try:
        # Fetch ONLY the missing data
        gap_df = fetcher.fetch_symbol(
            symbol=symbol,
            start_time=download_start,
            end_time=download_end,
            force=True
        )
        
        if gap_df is None or len(gap_df) == 0:
            print(" No data available")
            return False
        
        # Combine: gap + existing
        combined_df = pd.concat([gap_df, df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        # Save
        combined_df.to_parquet(cache_file, engine='pyarrow', index=False)
        
        # Copy to historical
        hist_file = HISTORICAL_DIR / f"{symbol}_1m.parquet"
        combined_df.to_parquet(hist_file, compression='snappy', index=False)
        
        new_bars = len(gap_df)
        total_bars = len(combined_df)
        size_mb = hist_file.stat().st_size / (1024**2)
        
        print(f" +{new_bars:,} bars, total {total_bars:,}, {size_mb:.1f}MB")
        return True
        
    except Exception as e:
        print(f" ERROR: {e}")
        return False

def main():
    print("="*80)
    print(f"DOWNLOAD 1 YEAR HISTORICAL GAP: {ONE_YEAR_AGO} to your earliest cached data")
    print("="*80)
    print("This will NOT touch your existing recent months")
    print("Only fills missing gap backwards from what you already have")
    print("="*80)
    
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    fetcher = BybitFetcher(cache_dir=str(CACHE_DIR), rate_limit=RATE_LIMIT)
    cached_symbols = sorted(fetcher.list_cached())
    
    print(f"\n{len(cached_symbols)} coins to check...")
    print(f"Rate limit: {RATE_LIMIT}s per request")
    print(f"Estimated time: {len(cached_symbols) * RATE_LIMIT / 60:.1f} minutes\n")
    
    # First, check one coin to show example
    if cached_symbols:
        test_file = CACHE_DIR / f"{cached_symbols[0]}_1m.parquet"
        test_df = pd.read_parquet(test_file)
        test_df['datetime'] = pd.to_datetime(test_df['timestamp'], unit='ms', utc=True)
        
        print("EXAMPLE (first coin):")
        print(f"  Symbol: {cached_symbols[0]}")
        print(f"  Current earliest: {test_df['datetime'].min()}")
        print(f"  Download will start from: {ONE_YEAR_AGO}")
        print(f"  Gap: ~{(test_df['datetime'].min() - datetime.strptime(ONE_YEAR_AGO, '%Y-%m-%d').replace(tzinfo=test_df['datetime'].min().tzinfo)).days} days\n")
    
    response = input("Proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    start_time = time.time()
    success = 0
    
    for i, symbol in enumerate(cached_symbols, 1):
        print(f"[{i}/{len(cached_symbols)}]", end=" ")
        
        if download_missing_gap(symbol, fetcher):
            success += 1
        
        time.sleep(RATE_LIMIT)
    
    elapsed = (time.time() - start_time) / 60
    
    print("\n" + "="*80)
    print(f"COMPLETE: {success}/{len(cached_symbols)} coins")
    print(f"Runtime: {elapsed:.1f} minutes")
    print(f"Data saved to: {HISTORICAL_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()
