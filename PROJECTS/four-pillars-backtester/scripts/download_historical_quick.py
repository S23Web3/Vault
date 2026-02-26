"""
Quick-start historical data download.
Run this NOW while we plan the rest.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.fetcher import BybitFetcher

HISTORICAL_DIR = ROOT / "data" / "historical"
START_DATE = "2023-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

def download_coin(symbol, fetcher):
    """Download one coin, skip if exists."""
    output_file = HISTORICAL_DIR / f"{symbol}_1m.parquet"
    
    if output_file.exists():
        print(f"  SKIP {symbol} (exists)")
        return True
    
    try:
        print(f"  {symbol}...", end="", flush=True)
        
        # Fetch from Bybit
        df = fetcher.fetch(
            symbol=symbol,
            interval="1m",
            start_date=START_DATE,
            end_date=END_DATE
        )
        
        if df is None or len(df) == 0:
            print(" FAIL (no data)")
            return False
        
        # Verify volume exists
        if 'base_vol' not in df.columns:
            print(" FAIL (no volume)")
            return False
        
        # Add sanity checks
        df['valid_ohlc'] = (
            (df['high'] >= df['low']) & 
            (df['high'] >= df['open']) & 
            (df['high'] >= df['close'])
        )
        df['valid_volume'] = df['base_vol'] > 0
        
        # Save
        df.to_parquet(output_file, compression='snappy', index=False)
        
        size_mb = output_file.stat().st_size / (1024**2)
        invalid_pct = (~df['valid_ohlc']).sum() / len(df) * 100
        
        print(f" OK ({len(df):,} bars, {size_mb:.1f}MB, {invalid_pct:.2f}% invalid)")
        return True
        
    except Exception as e:
        print(f" ERROR: {e}")
        return False

def main():
    print("="*80)
    print(f"HISTORICAL DATA DOWNLOAD: {START_DATE} to {END_DATE}")
    print("="*80)
    
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    fetcher = BybitFetcher(cache_dir=str(ROOT / "data" / "cache"))
    
    # Get symbols from cache
    symbols = fetcher.list_cached()
    
    print(f"\nDownloading {len(symbols)} coins...")
    print(f"Estimated: 20-50 GB, 6-12 hours")
    print(f"Save to: {HISTORICAL_DIR}\n")
    
    start_time = time.time()
    success = 0
    
    for i, sym in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}]", end=" ")
        if download_coin(sym, fetcher):
            success += 1
        time.sleep(1)  # Rate limit
    
    elapsed = (time.time() - start_time) / 3600
    
    print("\n" + "="*80)
    print(f"COMPLETE: {success}/{len(symbols)} coins")
    print(f"Runtime: {elapsed:.2f} hours")
    print(f"Location: {HISTORICAL_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()
