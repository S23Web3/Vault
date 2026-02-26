"""
FIXED: Download 1 YEAR gap (Feb 2025 to earliest cached).
Bug fix: Changed 2024-02-11 to 2025-02-11 (correct 1 year ago).
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
ONE_YEAR_AGO = "2025-02-11"  # FIXED: Was 2024-02-11 (2 years), now correct 1 year
RATE_LIMIT = 0.05  # 20 req/s (Bybit allows 120 req/s = 600 per 5s per IP)

def download_missing_gap(symbol, fetcher):
    """Download ONLY the missing gap (1 year ago to earliest cached)."""
    
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    
    if not cache_file.exists():
        print(f"  {symbol}: No cache, skipping")
        return False
    
    df = pd.read_parquet(cache_file)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    earliest_cached = df['datetime'].min()
    
    download_start = datetime.strptime(ONE_YEAR_AGO, "%Y-%m-%d").replace(tzinfo=earliest_cached.tzinfo)
    download_end = earliest_cached - timedelta(minutes=1)
    
    # Check if already complete
    if earliest_cached <= download_start:
        print(f"  {symbol}: Complete (has {earliest_cached.strftime('%Y-%m-%d')})")
        return True
    
    gap_days = (download_end - download_start).days
    
    print(f"  {symbol}: Gap {gap_days} days ({download_start.strftime('%Y-%m-%d')} to {download_end.strftime('%Y-%m-%d')})...", end="", flush=True)
    
    try:
        gap_df = fetcher.fetch_symbol(
            symbol=symbol,
            start_time=download_start,
            end_time=download_end,
            force=True
        )
        
        if gap_df is None or len(gap_df) == 0:
            print(" No data")
            return False
        
        combined_df = pd.concat([gap_df, df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        combined_df.to_parquet(cache_file, engine='pyarrow', index=False)
        
        hist_file = HISTORICAL_DIR / f"{symbol}_1m.parquet"
        combined_df.to_parquet(hist_file, compression='snappy', index=False)
        
        print(f" +{len(gap_df):,} bars")
        return True
        
    except Exception as e:
        print(f" ERROR: {e}")
        return False

def main():
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    fetcher = BybitFetcher(cache_dir=str(CACHE_DIR), rate_limit=RATE_LIMIT)

    retry_mode = "--retry" in sys.argv
    retry_file = CACHE_DIR / "_retry_symbols.txt"

    if retry_mode:
        if not retry_file.exists():
            print("No _retry_symbols.txt found. Run sanity_check_cache.py first.")
            return
        symbols = [s.strip() for s in retry_file.read_text().splitlines() if s.strip()]
        print("="*80)
        print(f"RETRY MODE: {len(symbols)} partial symbols from sanity check")
        print("="*80)
    else:
        symbols = sorted(fetcher.list_cached())
        print("="*80)
        print(f"DOWNLOAD 1 YEAR GAP: {ONE_YEAR_AGO} to earliest cached")
        print(f"ALL {len(symbols)} symbols")
        print("="*80)

    print(f"\n{len(symbols)} coins, {RATE_LIMIT}s/page, 1s between symbols\n")

    response = input("Proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return

    t0 = time.time()
    success = 0

    for i, sym in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}]", end=" ")
        if download_missing_gap(sym, fetcher):
            success += 1
        time.sleep(1.0)  # 1s pause between symbols

    print(f"\n{'='*80}\nDone: {success}/{len(symbols)}, {(time.time()-t0)/60:.0f} min\n{'='*80}")

if __name__ == "__main__":
    main()
