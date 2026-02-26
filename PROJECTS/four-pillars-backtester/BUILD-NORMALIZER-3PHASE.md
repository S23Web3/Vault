Project: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester

READ FIRST: data/fetcher.py, scripts/run_backtest_v384.py (load_cached function), 
signals/four_pillars_v383.py (first 30 lines — see what columns it needs)

THREE builds. Sequential.

=== BUILD 1: DATA NORMALIZER — data/normalizer.py ===

Create a universal OHLCV normalizer that accepts any exchange CSV and converts 
to our internal parquet format.

Internal schema (target):
  timestamp: int64 (epoch milliseconds)
  open: float64
  high: float64  
  low: float64
  close: float64
  base_vol: float64
  quote_vol: float64
  datetime: datetime64[ns, UTC]

The normalizer should:

1. AUTO-DETECT delimiter (comma, tab, semicolon, pipe)
   - Try csv.Sniffer on first 5 lines

2. AUTO-DETECT column mapping using fuzzy matching:
   Known column name variants per field:
   - timestamp: ["timestamp", "ts", "time", "date", "datetime", "open_time", 
                  "Open time", "startTime", "candle_time", "t"]
   - open: ["open", "o", "Open", "open_price", "first"]
   - high: ["high", "h", "High", "high_price", "max"]
   - low: ["low", "l", "Low", "low_price", "min"]
   - close: ["close", "c", "Close", "close_price", "last"]
   - base_vol: ["volume", "vol", "Volume", "base_vol", "base_volume", 
                 "baseVolume", "amount"]
   - quote_vol: ["turnover", "quote_vol", "quote_volume", "quoteVolume", 
                  "Quote asset volume", "volCcy", "quote_asset_volume"]
   
   If quote_vol is missing, set to NaN (it's not critical for signals).
   If volume/base_vol is missing → error, can't proceed.

3. AUTO-DETECT timestamp format:
   - If numeric > 1e12: epoch milliseconds
   - If numeric > 1e9 and < 1e12: epoch seconds → multiply by 1000
   - If string: try pd.to_datetime() with multiple formats
     ["ISO8601", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M"]

4. VALIDATE after conversion:
   - No duplicate timestamps
   - OHLC sanity: high >= open, high >= close, low <= open, low <= close
   - Sorted ascending by timestamp
   - Report: total rows, date range, detected interval (1m/5m/15m/1h/etc)
   - Auto-detect interval from median diff between consecutive timestamps

5. SAVE as parquet:
   - Output: data/cache/{SYMBOL}_{interval}.parquet
   - If interval is 1m, also resample and save 5m version
   - Write .meta file matching fetcher format: "{start_ms},{end_ms}"

Class API:
```python
class OHLCVNormalizer:
    def __init__(self, cache_dir="data/cache"):
        ...
    
    def detect_format(self, file_path: str) -> dict:
        """Analyze file and return detected format info without converting."""
        # Returns: {delimiter, column_map, timestamp_format, interval, rows, date_range}
    
    def normalize(self, file_path: str, symbol: str, 
                  column_map: dict = None,  # override auto-detect
                  timestamp_format: str = None  # override auto-detect
                  ) -> pd.DataFrame:
        """Convert any OHLCV CSV to internal format. Save to parquet. Return df."""
    
    def normalize_batch(self, folder_path: str, symbol_from_filename: bool = True) -> dict:
        """Normalize all CSV files in a folder. 
        If symbol_from_filename=True, extract symbol from filename 
        (e.g., 'BTCUSDT_1m.csv' → 'BTCUSDT')."""
```

=== BUILD 2: COIN LIST SUPPORT FOR SWEEP ===

Currently the sweep reads all parquet files from data/cache/.
Add two new input modes to the dashboard sweep tab:

A) TEXT/CSV COIN LIST UPLOAD:
   - Streamlit file_uploader accepting .txt, .csv, .json
   - .txt: one symbol per line (BTCUSDT\nETHUSDT\n...)
   - .csv: first column = symbol names, OR column header "symbol"/"Symbol"/"pair"
   - .json: list of strings ["BTCUSDT", "ETHUSDT", ...]
   - After parsing, validate each symbol has data in cache
   - Show: "Found 45/50 symbols in cache. Missing: [X, Y, Z]"

B) CSV DATA UPLOAD (raw OHLCV):
   - File uploader accepting .csv
   - Run OHLCVNormalizer.detect_format() → show detected format to user
   - Show preview: detected columns, interval, date range, sample rows
   - User confirms or overrides column mapping
   - On confirm: normalize → save to cache as parquet → add to sweep list
   - Support single file (one coin) or ZIP of multiple CSVs

Dashboard UI for sweep tab:
Sweep Mode: [All Cache] [Custom List] [Upload Data]
[All Cache] → current behavior, scan data/cache/*.parquet
[Custom List] → file uploader for .txt/.csv/.json coin list
[Upload Data] → file uploader for raw OHLCV CSV(s)
→ shows format detection results
→ symbol name input (if single file)
→ convert button → runs normalizer → adds to sweep

=== BUILD 3: UPLOADED CSV → PARQUET CONVERSION UTILITY ===

Add a standalone script: scripts/convert_csv.py

Usage:
  python scripts/convert_csv.py --input data.csv --symbol BTCUSDT
  python scripts/convert_csv.py --input ./exports/ --batch
  python scripts/convert_csv.py --input data.csv --symbol BTCUSDT --preview

Features:
  --preview: show detected format without converting
  --batch: process all CSVs in folder
  --columns: manual column map override as JSON string
    e.g. --columns '{"time":"timestamp","o":"open","h":"high","l":"low","c":"close","v":"base_vol"}'
  --interval: force interval instead of auto-detect (1m, 5m, 15m, 1h, 4h, 1d)
  --resample: also create resampled versions (e.g., --resample 5m,15m,1h)

After conversion, print summary:
  Symbol: BTCUSDT
  Source: data.csv (Binance format detected)
  Rows: 525,600 → 525,600 (0 duplicates removed)
  Period: 2024-01-01 → 2024-12-31 (365 days)
  Interval: 1m (detected)
  Saved: data/cache/BTCUSDT_1m.parquet (42.1 MB)
  Saved: data/cache/BTCUSDT_5m.parquet (8.4 MB)

START by reading data/fetcher.py to understand the existing parquet save format
and .meta file convention. The normalizer output MUST match exactly so 
load_cached() works without changes.
