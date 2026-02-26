"""
FIXED TEST - Shows correct 1 year gap (Feb 2025 to cache start).
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("data/cache")
ONE_YEAR_AGO = "2025-02-11"  # FIXED: Was 2024 (2 years ago), now 2025 (1 year ago)
RATE_LIMIT = 1.0  # seconds per API call

def simulate_download_for_coin(symbol):
    cache_file = CACHE_DIR / f"{symbol}_1m.parquet"
    
    if not cache_file.exists():
        return f"SKIP: No cache"
    
    df = pd.read_parquet(cache_file)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    
    earliest = df['datetime'].min()
    latest = df['datetime'].max()
    
    download_start = datetime.strptime(ONE_YEAR_AGO, "%Y-%m-%d").replace(tzinfo=earliest.tzinfo)
    download_end = earliest - timedelta(minutes=1)
    
    if earliest <= download_start:
        return f"✅ Complete: has {earliest.strftime('%Y-%m-%d')}"
    
    gap_days = (download_end - download_start).days
    gap_bars = gap_days * 1440
    
    size_mb = cache_file.stat().st_size / (1024**2)
    est_mb = (gap_bars / len(df)) * size_mb
    
    return {
        'symbol': symbol,
        'earliest': earliest.strftime('%Y-%m-%d'),
        'latest': latest.strftime('%Y-%m-%d'),
        'gap_days': gap_days,
        'gap_bars': gap_bars,
        'est_mb': est_mb
    }

def main():
    print("="*80)
    print("FIXED TEST - Correct 1 year calculation (Feb 2025, not Feb 2024)")
    print("="*80)
    
    samples = ['RIVERUSDT', 'BTCUSDT', 'ETHUSDT', 'SKRUSDT', 'ACUUSDT',
               'CYSUSDT', 'PIPPINUSDT', 'BREVUSDT', 'FHEUSDT', 'POWERUSDT']
    
    results = []
    
    print("\nChecking sample coins...\n")
    
    for sym in samples:
        r = simulate_download_for_coin(sym)
        
        if isinstance(r, str):
            print(f"{sym:15} {r}")
        else:
            results.append(r)
            print(f"{sym:15} Earliest: {r['earliest']}, Gap: {r['gap_days']:3} days = {r['gap_bars']:,} bars (~{r['est_mb']:.1f}MB)")
    
    if results:
        avg_days = sum(r['gap_days'] for r in results) / len(results)
        avg_mb = sum(r['est_mb'] for r in results) / len(results)
        total_mb_all = avg_mb * 399
        
        print(f"\n{'='*80}")
        print(f"Sample: {len(results)}/{len(samples)} need download")
        print(f"Avg gap: {avg_days:.0f} days (~{avg_days/30:.1f} months)")
        print(f"Avg size: {avg_mb:.1f}MB per coin")
        print(f"\n--- EXTRAPOLATED TO ALL 399 COINS ---")
        print(f"Total size: ~{total_mb_all:.0f}MB ({total_mb_all/1024:.1f}GB)")
        print(f"API calls: ~{avg_days * len(results)}") 
        print(f"Time: ~{399 * RATE_LIMIT / 60:.0f} minutes")
        print(f"{'='*80}")
        print("\nIf numbers look correct, run:")
        print("  python scripts\\download_1year_gap_FIXED.py")

if __name__ == "__main__":
    main()
