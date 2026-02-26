"""
TEST VERSION - Simulates download without hitting API.
Shows what WOULD be downloaded, verifies logic.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("data/cache")
ONE_YEAR_AGO = "2024-02-11"

def simulate_download_for_coin(symbol):
    """Simulate what would be downloaded for one coin."""
    
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    
    if not cache_file.exists():
        return f"SKIP: No cache"
    
    # Load cache
    df = pd.read_parquet(cache_file)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    earliest_cached = df['datetime'].min()
    latest_cached = df['datetime'].max()
    total_cached_bars = len(df)
    
    # Calculate what we'd download
    download_start = datetime.strptime(ONE_YEAR_AGO, "%Y-%m-%d").replace(tzinfo=earliest_cached.tzinfo)
    download_end = earliest_cached - timedelta(minutes=1)
    
    # Check if gap exists
    if earliest_cached <= download_start:
        return f"✅ Complete: Has data from {earliest_cached.strftime('%Y-%m-%d')}"
    
    # Calculate gap
    gap_days = (download_end - download_start).days
    gap_hours = gap_days * 24
    gap_bars = gap_days * 1440  # 1m bars
    
    # Estimate size
    size_mb = cache_file.stat().st_size / (1024**2)
    bars_per_mb = total_cached_bars / size_mb if size_mb > 0 else 1000000
    estimated_new_mb = gap_bars / bars_per_mb
    
    return {
        'symbol': symbol,
        'current_earliest': earliest_cached.strftime('%Y-%m-%d %H:%M'),
        'current_latest': latest_cached.strftime('%Y-%m-%d %H:%M'),
        'current_bars': total_cached_bars,
        'gap_start': download_start.strftime('%Y-%m-%d'),
        'gap_end': download_end.strftime('%Y-%m-%d'),
        'gap_days': gap_days,
        'gap_bars': gap_bars,
        'estimated_mb': estimated_new_mb,
        'status': 'NEEDS_DOWNLOAD'
    }

def main():
    print("="*80)
    print("TEST RUN - SIMULATION ONLY (NO API CALLS)")
    print("="*80)
    
    # Check 10 sample coins
    sample_symbols = [
        'RIVERUSDT', 'BTCUSDT', 'ETHUSDT', 'SKRUSDT', 'ACUUSDT',
        'CYSUSDT', 'PIPPINUSDT', 'BREVUSDT', 'FHEUSDT', 'POWERUSDT'
    ]
    
    results = []
    total_gap_bars = 0
    total_estimated_mb = 0
    needs_download = 0
    complete = 0
    
    print("\nChecking sample coins...\n")
    
    for symbol in sample_symbols:
        result = simulate_download_for_coin(symbol)
        
        if isinstance(result, str):
            print(f"{symbol:15} {result}")
            if "Complete" in result:
                complete += 1
        else:
            results.append(result)
            needs_download += 1
            total_gap_bars += result['gap_bars']
            total_estimated_mb += result['estimated_mb']
            
            print(f"{symbol:15} Gap: {result['gap_days']:3} days ({result['gap_start']} to {result['gap_end']}) = {result['gap_bars']:,} bars (~{result['estimated_mb']:.1f}MB)")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Sample size: {len(sample_symbols)} coins")
    print(f"Complete: {complete}")
    print(f"Need download: {needs_download}")
    
    if needs_download > 0:
        avg_gap_days = total_gap_bars / (needs_download * 1440)
        avg_mb = total_estimated_mb / needs_download
        
        print(f"\nAverage gap: {avg_gap_days:.0f} days")
        print(f"Average size: {avg_mb:.1f}MB per coin")
        print(f"\n--- EXTRAPOLATED TO ALL 399 COINS ---")
        print(f"Total bars: ~{total_gap_bars * 399 / len(sample_symbols):,.0f}")
        print(f"Total size: ~{total_estimated_mb * 399 / len(sample_symbols):.1f}MB ({total_estimated_mb * 399 / len(sample_symbols) / 1024:.1f}GB)")
        print(f"API calls: ~{avg_gap_days * 399:.0f} requests")
        print(f"Time (1s/call): ~{avg_gap_days * 399 / 60:.0f} minutes")
    
    print("\n" + "="*80)
    print("This was a TEST RUN - no data downloaded")
    print("If numbers look correct, run the real script:")
    print("  python scripts\\download_1year_gap.py")
    print("="*80)

if __name__ == "__main__":
    main()
