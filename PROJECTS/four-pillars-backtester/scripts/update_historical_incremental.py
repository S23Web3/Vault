"""
INCREMENTAL historical data update.
ONLY downloads NEW data (from last cached timestamp to now).
Does NOT re-download existing data.
Respects rate limits (1 request per second default).
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
RATE_LIMIT = 1.0  # seconds between requests

def get_last_timestamp(cache_file):
    """Get the last timestamp from existing cache."""
    if not cache_file.exists():
        return None
    
    df = pd.read_parquet(cache_file)
    if len(df) == 0:
        return None
    
    # Return last timestamp as datetime
    return pd.to_datetime(df['timestamp'].max(), unit='ms', utc=True)

def update_coin_incremental(symbol, fetcher):
    """Update one coin - ONLY fetch new data since last cached timestamp."""
    
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    
    # Check last timestamp
    last_ts = get_last_timestamp(cache_file)
    
    if last_ts is None:
        print(f"  {symbol}: No cache, skipping (use initial fetch script)")
        return False
    
    # Calculate date range for NEW data only
    start_time = last_ts + timedelta(minutes=1)  # Start 1 minute after last cached
    end_time = datetime.now(tz=last_ts.tzinfo)
    
    # Calculate how much new data
    hours_to_fetch = (end_time - start_time).total_seconds() / 3600
    
    if hours_to_fetch < 0.1:  # Less than 6 minutes
        print(f"  {symbol}: Up to date (last: {last_ts.strftime('%Y-%m-%d %H:%M')})")
        return True
    
    print(f"  {symbol}: Fetching {hours_to_fetch:.1f}h new data...", end="", flush=True)
    
    try:
        # Fetch ONLY new data
        new_df = fetcher.fetch_symbol(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            force=True  # Don't use cache, we're updating it
        )
        
        if new_df is None or len(new_df) == 0:
            print(" No new data")
            return True
        
        # Load existing cache
        existing_df = pd.read_parquet(cache_file)
        
        # Append new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Remove duplicates (just in case)
        combined_df = combined_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        # Save back to cache
        combined_df.to_parquet(cache_file, engine='pyarrow', index=False)
        
        # Update historical copy too
        hist_file = HISTORICAL_DIR / f"{symbol}_1m.parquet"
        combined_df.to_parquet(hist_file, compression='snappy', index=False)
        
        new_bars = len(new_df)
        total_bars = len(combined_df)
        
        print(f" OK (+{new_bars} bars, total: {total_bars:,})")
        return True
        
    except Exception as e:
        print(f" ERROR: {e}")
        return False

def main():
    print("="*80)
    print("INCREMENTAL DATA UPDATE (NEW DATA ONLY)")
    print("="*80)
    
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    fetcher = BybitFetcher(cache_dir=str(CACHE_DIR), rate_limit=RATE_LIMIT)
    
    # Get all cached symbols
    cached = sorted(fetcher.list_cached())
    
    print(f"\nUpdating {len(cached)} coins...")
    print(f"Rate limit: {RATE_LIMIT}s between requests")
    print(f"Estimated time: {len(cached) * RATE_LIMIT / 60:.1f} minutes\n")
    
    start_time = time.time()
    updated = 0
    
    for i, symbol in enumerate(cached, 1):
        print(f"[{i}/{len(cached)}]", end=" ")
        
        if update_coin_incremental(symbol, fetcher):
            updated += 1
        
        # Rate limit
        time.sleep(RATE_LIMIT)
    
    elapsed = (time.time() - start_time) / 60
    
    print("\n" + "="*80)
    print(f"COMPLETE: {updated}/{len(cached)} coins updated")
    print(f"Runtime: {elapsed:.1f} minutes")
    print("="*80)

if __name__ == "__main__":
    main()
