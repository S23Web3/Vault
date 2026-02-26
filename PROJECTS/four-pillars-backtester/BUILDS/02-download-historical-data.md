# Task: Download Complete 2023-Now Dataset

## Goal
Download ALL historical data for 399 coins from 2023-01-01 to present.
- Timeframe: 1m
- Include: OHLCV (volume MUST be present)
- Format: Parquet (compressed)
- Sanity check: Add validation column
- Test: Mock data first, then real download

## Constraints
- NO data overwrite (check existing files first)
- Estimate size: ~20-50 GB total
- Runtime: ~6-12 hours for all coins
- Save to: `data/historical/` directory

## Files to Create
- `scripts/download_historical_data.py` (main script)
- `scripts/test_download_mock.py` (test with mock data)

## Implementation

### Step 1: Check if volume exists in current cache

```python
# scripts/check_volume_exists.py
from pathlib import Path
import pandas as pd

cache_dir = Path("data/cache")
sample_files = list(cache_dir.glob("*.parquet"))[:5]

for f in sample_files:
    df = pd.read_parquet(f)
    has_volume = 'base_vol' in df.columns or 'volume' in df.columns
    print(f"{f.name}: Volume={'✅' if has_volume else '❌'}")
    if has_volume:
        print(f"  Columns: {df.columns.tolist()}")
        break
```

### Step 2: Download script (with sanity checks)

```python
# scripts/download_historical_data.py
"""
Download complete historical dataset (2023-now).
Includes volume, sanity checks, no overwrites.
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
START_DATE = "2023-01-01"
END_DATE = datetime.now().strftime("%Y-%m-%d")

def estimate_download_size():
    """Estimate total download size."""
    # 1m candles = 525,600 bars/year
    # 2 years = ~1,051,200 bars/coin
    # 399 coins × 1M bars × 50 bytes/bar = ~20 GB
    bars_per_coin = 1_051_200
    bytes_per_bar = 50
    total_bytes = 399 * bars_per_coin * bytes_per_bar
    return total_bytes / (1024**3)  # GB

def add_sanity_check_column(df):
    """Add validation column to detect data issues."""
    df = df.copy()
    
    # Sanity checks
    df['sanity_ohlc_valid'] = (
        (df['open'] > 0) & 
        (df['high'] >= df['low']) & 
        (df['high'] >= df['open']) & 
        (df['high'] >= df['close']) &
        (df['low'] <= df['open']) &
        (df['low'] <= df['close'])
    )
    
    df['sanity_volume_valid'] = df['base_vol'] > 0
    
    df['sanity_all_valid'] = (
        df['sanity_ohlc_valid'] & 
        df['sanity_volume_valid']
    )
    
    return df

def download_coin(symbol, fetcher, start_date, end_date):
    """Download historical data for one coin."""
    output_file = HISTORICAL_DIR / f"{symbol}_1m_{start_date}_{end_date}.parquet"
    
    # Skip if already exists
    if output_file.exists():
        print(f"  SKIP {symbol} (already downloaded)")
        return True
    
    try:
        print(f"  Downloading {symbol}...", end="", flush=True)
        
        # Download (Bybit API)
        df = fetcher.fetch(
            symbol=symbol,
            interval="1m",
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or len(df) == 0:
            print(f" FAIL (no data)")
            return False
        
        # Add sanity checks
        df = add_sanity_check_column(df)
        
        # Verify volume exists
        if 'base_vol' not in df.columns:
            print(f" FAIL (no volume column)")
            return False
        
        # Sanity check stats
        invalid_count = (~df['sanity_all_valid']).sum()
        invalid_pct = invalid_count / len(df) * 100
        
        # Save to parquet
        df.to_parquet(output_file, compression='snappy', index=False)
        
        file_size_mb = output_file.stat().st_size / (1024**2)
        print(f" OK ({len(df):,} bars, {file_size_mb:.1f} MB, {invalid_pct:.2f}% invalid)")
        
        return True
        
    except Exception as e:
        print(f" ERROR: {e}")
        return False

def main():
    print("="*80)
    print(f"HISTORICAL DATA DOWNLOAD: {START_DATE} to {END_DATE}")
    print("="*80)
    
    # Create output directory
    HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Estimate size
    est_size_gb = estimate_download_size()
    print(f"\nEstimated download size: ~{est_size_gb:.1f} GB")
    print(f"Estimated runtime: ~6-12 hours (depends on API rate limits)")
    
    response = input("\nProceed with download? (yes/no): ")
    if response.lower() != 'yes':
        print("Download cancelled.")
        return
    
    # Initialize fetcher
    fetcher = BybitFetcher()
    
    # Get all symbols
    symbols = fetcher.list_available_symbols()
    print(f"\nDownloading {len(symbols)} coins...")
    
    # Download each coin
    start_time = time.time()
    success_count = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}]", end=" ")
        
        if download_coin(symbol, fetcher, START_DATE, END_DATE):
            success_count += 1
        
        # Rate limit: 1 request per second
        time.sleep(1)
    
    # Summary
    elapsed = time.time() - start_time
    print("\n" + "="*80)
    print(f"Download complete: {success_count}/{len(symbols)} coins")
    print(f"Runtime: {elapsed/3600:.2f} hours")
    print(f"Output: {HISTORICAL_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()
```

### Step 3: Test with mock data

```python
# scripts/test_download_mock.py
"""Test download script with mock data."""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def create_mock_data():
    """Create mock 1m OHLCV data for testing."""
    dates = pd.date_range(
        start="2023-01-01",
        end="2023-01-02",
        freq="1min"
    )
    
    df = pd.DataFrame({
        'datetime': dates,
        'open': 1.0,
        'high': 1.01,
        'low': 0.99,
        'close': 1.0,
        'base_vol': 1000.0,
        'quote_vol': 1000.0,
        'timestamp': [int(d.timestamp() * 1000) for d in dates]
    })
    
    return df

def test_sanity_checks():
    """Test sanity check function."""
    from scripts.download_historical_data import add_sanity_check_column
    
    # Create mock data with some invalid rows
    df = create_mock_data()
    
    # Add invalid rows
    df.loc[10, 'high'] = 0.98  # High < Low (invalid)
    df.loc[20, 'base_vol'] = -100  # Negative volume (invalid)
    
    # Add sanity checks
    df = add_sanity_check_column(df)
    
    # Verify
    assert df['sanity_all_valid'].sum() == len(df) - 2, "Should detect 2 invalid rows"
    print("✅ Sanity check test passed")

def test_parquet_save():
    """Test parquet save/load."""
    from scripts.download_historical_data import add_sanity_check_column
    
    df = create_mock_data()
    df = add_sanity_check_column(df)
    
    # Save
    test_file = Path("data/historical/test_mock.parquet")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(test_file, compression='snappy', index=False)
    
    # Load
    df_loaded = pd.read_parquet(test_file)
    
    # Verify
    assert len(df_loaded) == len(df), "Row count mismatch"
    assert 'sanity_all_valid' in df_loaded.columns, "Sanity column missing"
    
    # Cleanup
    test_file.unlink()
    
    print("✅ Parquet save/load test passed")

if __name__ == "__main__":
    print("Testing mock data download...")
    test_sanity_checks()
    test_parquet_save()
    print("\n✅ All tests passed. Ready for real download.")
```

## Test Commands

**Step 1: Check current volume:**
```bash
python scripts\check_volume_exists.py
```

**Step 2: Test with mock data:**
```bash
python scripts\test_download_mock.py
```

**Step 3: Run real download:**
```bash
python scripts\download_historical_data.py
```

## Expected Timeline

| Phase | Duration |
|-------|----------|
| Mock test | 5 seconds |
| Volume check | 10 seconds |
| Real download (399 coins) | 6-12 hours |

## Verification

After download:
- Check `data/historical/*.parquet` files exist
- Verify sanity columns present
- Check total disk usage (~20-50 GB)
- Sample 5 random files, verify OHLCV + volume complete

## Permissions Setup

After download, run:
```bash
# Grant Claude Code access
icacls "data\historical" /grant Claude:(OI)(CI)F /T
```
