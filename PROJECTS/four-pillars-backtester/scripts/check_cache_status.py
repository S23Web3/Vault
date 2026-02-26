"""
CHECK: What data you actually have.
Shows exact date ranges for each coin.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path("data/cache")

print("="*80)
print("CHECKING YOUR CURRENT CACHE")
print("="*80)

# Check 5 sample coins
sample_coins = ['RIVERUSDT', 'BTCUSDT', 'ETHUSDT', 'SKRUSDT', 'ACUUSDT']

for symbol in sample_coins:
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    
    if not cache_file.exists():
        print(f"{symbol}: NOT CACHED")
        continue
    
    df = pd.read_parquet(cache_file)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    earliest = df['datetime'].min()
    latest = df['datetime'].max()
    total_bars = len(df)
    has_volume = 'base_vol' in df.columns
    
    print(f"\n{symbol}:")
    print(f"  Earliest: {earliest}")
    print(f"  Latest: {latest}")
    print(f"  Total bars: {total_bars:,}")
    print(f"  Has volume: {has_volume}")
    
    # Calculate gap from 1 year ago
    one_year_ago = datetime(2024, 2, 11, tzinfo=earliest.tzinfo)
    
    if earliest > one_year_ago:
        gap_days = (earliest - one_year_ago).days
        print(f"  MISSING: {gap_days} days from Feb 2024 to {earliest.strftime('%Y-%m-%d')}")
    else:
        print(f"  ✅ Has data from before Feb 2024")

print("\n" + "="*80)
print("Run this to see your actual cache status:")
print("python scripts\\check_cache_status.py")
print("="*80)
