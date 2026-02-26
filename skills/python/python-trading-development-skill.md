# Python Coding Skill - Malik's Trading System

**Use this skill whenever writing Python code for trading system, backtesting, data processing, or automation.**

---

## CRITICAL RULE: Test-First Development

**NEVER write production code without testing first.**

### Testing Workflow (MANDATORY)

```
1. Write TEST version with mock/simulated data
2. Run test, verify logic is correct
3. User reviews test output
4. ONLY THEN write production version
5. Production inherits tested logic
```

**Example:**
```python
# ❌ WRONG - Direct production code
def download_data(symbols):
    for sym in symbols:
        fetcher.fetch(sym)  # Untested, could have bugs

# ✅ CORRECT - Test first
def test_download_simulation(symbols):
    """Test without API calls."""
    for sym in symbols:
        print(f"Would download {sym} from {start} to {end}")
    # User verifies output BEFORE real download
```

---

## Windows Environment Rules

**Desktop = Windows 11, VPS = Ubuntu 24**

### Path Handling
```python
# ✅ CORRECT - Works on both
from pathlib import Path
cache_dir = Path("data/cache")
file_path = cache_dir / "RIVERUSDT_1m.parquet"

# ❌ WRONG - Breaks on Windows
file_path = "data/cache/RIVERUSDT_1m.parquet"  # Forward slashes
```

### File Operations
```python
# ✅ Use Python libraries (pandas, pathlib, shutil)
import pandas as pd
from pathlib import Path
import shutil

# Read
df = pd.read_parquet(Path("data/cache/file.parquet"))

# Write
df.to_parquet(Path("data/output/result.parquet"))

# Copy
shutil.copy(src_path, dst_path)

# ❌ NEVER use bash commands on Windows desktop
os.system("cp file1 file2")  # Breaks on Windows
```

---

## Code Structure Rules

### 1. Explain Before/After Commands

```python
# ✅ CORRECT
"""
Download historical data incrementally.
ONLY fetches new data since last cached timestamp.
Avoids re-downloading existing months.
Rate limited: 1 second between API calls.
"""
def update_incremental():
    # Implementation
    pass

# ❌ WRONG - No explanation
def update():
    pass
```

### 2. Descriptive Variable Names

```python
# ✅ CORRECT
gap_days = (download_end - download_start).days
estimated_mb = (gap_bars / cached_bars) * cached_size_mb

# ❌ WRONG - Cryptic
d = (e - s).days
mb = (g / c) * s
```

### 3. Input Validation

```python
# ✅ CORRECT
def download_gap(symbol, start_date, end_date):
    if not cache_exists(symbol):
        print(f"SKIP {symbol}: No cache")
        return False
    
    if end_date <= start_date:
        print(f"ERROR: Invalid date range")
        return False
    
    # Proceed with download
```

---

## Error Handling

### Graceful Degradation

```python
# ✅ CORRECT - Continue on individual failures
for symbol in symbols:
    try:
        result = process(symbol)
    except Exception as e:
        print(f"ERROR {symbol}: {e}")
        continue  # Process remaining symbols

# ❌ WRONG - One failure kills everything
for symbol in symbols:
    result = process(symbol)  # Crashes on first error
```

### Informative Error Messages

```python
# ✅ CORRECT
except ValueError as e:
    print(f"ERROR parsing timestamp for {symbol}: {e}")
    print(f"  File: {cache_file}")
    print(f"  Expected format: YYYY-MM-DD")

# ❌ WRONG
except:
    print("Error")
```

---

## API Rate Limiting

### Always Include Rate Limits

```python
# ✅ CORRECT
RATE_LIMIT = 1.0  # seconds between requests

for symbol in symbols:
    fetch_data(symbol)
    time.sleep(RATE_LIMIT)  # Prevent API throttling

# ❌ WRONG - No rate limiting
for symbol in symbols:
    fetch_data(symbol)  # Will hit rate limits
```

### Estimate Time Upfront

```python
# ✅ CORRECT
total_requests = len(symbols) * avg_pages_per_symbol
estimated_minutes = (total_requests * RATE_LIMIT) / 60
print(f"Estimated time: {estimated_minutes:.0f} minutes")

response = input("Proceed? (yes/no): ")
```

---

## Data Validation

### Always Verify Data Integrity

```python
# ✅ CORRECT
df['sanity_ohlc'] = (
    (df['high'] >= df['low']) &
    (df['high'] >= df['open']) &
    (df['high'] >= df['close'])
)

invalid_pct = (~df['sanity_ohlc']).sum() / len(df) * 100
print(f"Invalid bars: {invalid_pct:.2f}%")

# ❌ WRONG - Trust data blindly
df.to_parquet(output_file)  # No validation
```

### Check Expected Columns

```python
# ✅ CORRECT
required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'base_vol']
missing = [c for c in required_cols if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

# ❌ WRONG - Assume columns exist
df['base_vol'].sum()  # KeyError if missing
```

---

## Incremental Processing

### Save Checkpoints

```python
# ✅ CORRECT - Save progress every N iterations
CHECKPOINT_FREQ = 10

for i, symbol in enumerate(symbols):
    result = process(symbol)
    results.append(result)
    
    if (i + 1) % CHECKPOINT_FREQ == 0:
        save_checkpoint(results)
        print(f"Checkpoint: {i+1}/{len(symbols)}")

# ❌ WRONG - No checkpoints, lose all progress on crash
for symbol in symbols:
    result = process(symbol)
    results.append(result)
# Save only at end
```

---

## Debugging Helpers

### Progress Indicators

```python
# ✅ CORRECT
for i, symbol in enumerate(symbols, 1):
    print(f"[{i}/{len(symbols)}] {symbol}...", end="", flush=True)
    result = process(symbol)
    print(f" OK ({result.bars:,} bars)")

# ❌ WRONG - Silent processing
for symbol in symbols:
    result = process(symbol)
```

### Verbose Logging Option

```python
# ✅ CORRECT
def process(symbol, verbose=False):
    if verbose:
        print(f"  Loading cache: {cache_file}")
        print(f"  Date range: {start} to {end}")
    
    # Processing
```

---

## Performance Considerations

### Use Parquet (Not CSV)

```python
# ✅ CORRECT - Fast, compressed
df.to_parquet(file, compression='snappy', index=False)
df = pd.read_parquet(file)

# ❌ WRONG - Slow, large files
df.to_csv(file, index=False)  # 10x slower, 5x larger
```

### Batch Operations

```python
# ✅ CORRECT - Vectorized pandas
df['pnl'] = (df['exit_price'] - df['entry_price']) / df['entry_price'] * 10000

# ❌ WRONG - Row-by-row loops
for i, row in df.iterrows():
    df.at[i, 'pnl'] = (row['exit_price'] - row['entry_price']) / row['entry_price'] * 10000
```

---

## Trading System Specific

### Commission Calculation

```python
# ✅ CORRECT - Percentage-based
commission = notional * commission_rate  # 0.0008 = 0.08%
rebate = commission * rebate_pct  # 0.70 = 70%
net_commission = commission - rebate

# ❌ WRONG - Hardcoded dollar amounts
commission = 8.00  # Breaks with different position sizes
```

### Timestamp Handling

```python
# ✅ CORRECT - UTC timezone aware
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

# ❌ WRONG - Naive timestamps
df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')  # No timezone
```

---

## Testing Patterns

### Mock Data Generation

```python
def create_mock_data():
    """Generate realistic test data."""
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='1min')
    
    df = pd.DataFrame({
        'datetime': dates,
        'open': 1.0,
        'high': 1.01,
        'low': 0.99,
        'close': 1.0,
        'base_vol': 1000.0,
        'timestamp': [int(d.timestamp() * 1000) for d in dates]
    })
    
    return df
```

### Simulation vs Production

```python
# TEST version
def simulate_download(symbols):
    """DRY RUN - No API calls."""
    for sym in symbols:
        gap_size = calculate_gap(sym)
        print(f"{sym}: Would download {gap_size} bars")
    return results

# PRODUCTION version (inherits tested logic)
def download_real(symbols):
    """LIVE - Makes API calls."""
    for sym in symbols:
        gap_size = calculate_gap(sym)  # Same logic as test
        data = fetcher.fetch(sym, gap_size)  # Only difference
        save(data)
```

---

## String & Encoding Safety (Windows)

### CRITICAL: Unicode Escape Prevention

Windows backslash paths inside Python strings cause `SyntaxError: (unicode error) 'unicodeescape' codec`. This happens because `\U`, `\N`, `\t`, `\n`, `\r`, `\b`, `\f`, `\a` are Python escape sequences.

**Dangerous sequences in Windows paths:**
- `\Users` → `\U` = 32-bit Unicode escape (expects 8 hex digits)
- `\new` → `\n` = newline
- `\temp` → `\t` = tab
- `\backup` → `\b` = backspace
- `\readme` → `\r` = carriage return

```python
# ❌ FATAL — Causes SyntaxError at parse time
path = "C:\Users\User\Documents\project"
# \U triggers: unicodeescape codec can't decode

# ❌ FATAL — Even in docstrings and comments inside triple-quoted strings
"""
File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\file.py
"""
# \U inside docstring = same SyntaxError

# ❌ FATAL — f-strings with backslash paths
print(f"Loading from C:\Users\User\Documents")

# ✅ CORRECT — Use raw strings for paths
path = r"C:\Users\User\Documents\project"

# ✅ CORRECT — Use pathlib (preferred)
path = Path("C:/Users/User/Documents/project")
path = Path(__file__).resolve().parent.parent  # relative, cross-platform

# ✅ CORRECT — Forward slashes work in Python on Windows
path = "C:/Users/User/Documents/project"

# ✅ CORRECT — In docstrings, use forward slashes or relative paths
"""
File: C:/Users/User/Documents/project/file.py
Run: python scripts/my_script.py
"""

# ✅ CORRECT — Escaped backslashes (verbose but safe)
path = "C:\\Users\\User\\Documents"
```

### Rules for All Generated Python Files

1. **NEVER put Windows backslash paths in docstrings** — use forward slashes
2. **NEVER put Windows backslash paths in string literals** — use `r''` or `Path()`
3. **NEVER put Windows backslash paths in comments** (they're safe in comments but establish bad habits — use forward slashes)
4. **NEVER put Windows backslash paths in f-strings** — use `Path` objects
5. **ALL path construction MUST use `pathlib.Path`** — it handles separators automatically
6. **Run-instructions in docstrings** — use forward slashes: `Run: python scripts/file.py`

### Pre-Commit String Safety Check

Before writing any `.py` file, scan for these patterns:
```python
import re

DANGEROUS_PATTERNS = [
    r'"[^"]*\\[UNtnrbfa][^\\]',   # \U, \N, \t etc. in double-quoted strings
    r"'[^']*\\[UNtnrbfa][^\\]",    # Same in single-quoted strings
    r'"""[\s\S]*?\\[UNtnrbfa]',    # Inside triple-quoted docstrings
]
# If any match → STOP, fix before writing file
```

---

## Pre-Execution Validation

### Always Syntax-Check Before Running

```python
# ✅ CORRECT — Validate syntax before execution
import py_compile
import sys

try:
    py_compile.compile('scripts/my_script.py', doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
```

### Claude Code Build Prompt Pattern

Every build prompt should include this validation step:
```
After writing each .py file:
1. Run: python -m py_compile <file.py>
2. If SyntaxError → fix immediately, do not proceed
3. Only run the script after syntax check passes
```

### AST Parse Validation (Stricter)

```python
import ast

def validate_python_file(filepath):
    """Parse file and catch encoding/syntax errors before execution."""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    try:
        ast.parse(source)
        print(f"VALID: {filepath}")
        return True
    except SyntaxError as e:
        print(f"INVALID: {filepath}")
        print(f"  Line {e.lineno}: {e.msg}")
        print(f"  {e.text}")
        return False
```

---

## Common Bugs to Avoid

### Off-by-One Errors

```python
# ✅ CORRECT
download_end = earliest_cached - timedelta(minutes=1)  # Don't overlap

# ❌ WRONG
download_end = earliest_cached  # Duplicate last bar
```

### Date Calculation Errors

```python
# ✅ CORRECT - Check your math
today = datetime(2026, 2, 11)
one_year_ago = datetime(2025, 2, 11)  # 2026 - 1 = 2025

# ❌ WRONG - Seen in real bug
one_year_ago = datetime(2024, 2, 11)  # 2026 - 2 = 2024 ❌
```

### Type Mismatches

```python
# ✅ CORRECT - Ensure timezone aware
download_start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=earliest.tzinfo)

# ❌ WRONG - Naive vs aware comparison
download_start = datetime.strptime(date_str, "%Y-%m-%d")  # Crashes if earliest has tz
```

---

## Code Review Checklist

Before submitting code, verify:

- [ ] **Test version created and run first**
- [ ] User reviewed test output
- [ ] Windows paths (pathlib) used
- [ ] **NO backslash paths in docstrings, strings, or f-strings**
- [ ] **`python -m py_compile` passes on every new .py file**
- [ ] **No `\U`, `\N`, `\t`, `\n`, `\r`, `\b` sequences in string literals**
- [ ] Rate limiting implemented
- [ ] Progress indicators shown
- [ ] Error handling for each failure mode
- [ ] Checkpoints save progress
- [ ] Data validation checks included
- [ ] Comments explain WHY, not just WHAT
- [ ] Estimated runtime shown upfront
- [ ] No hardcoded values (use constants)

---

## Example: Complete Script Template

```python
"""
Script purpose: One-line description
What it does: Detailed explanation
Dependencies: pandas, pathlib, etc.
Runtime: Estimated time
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import time

# Constants
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CACHE_DIR = ROOT / "data" / "cache"
OUTPUT_DIR = ROOT / "data" / "output"
RATE_LIMIT = 1.0  # seconds
CHECKPOINT_FREQ = 10  # save every N items

def validate_input(arg):
    """Validate input before processing."""
    if not arg:
        raise ValueError("Argument required")
    return True

def process_item(item, verbose=False):
    """Process one item with error handling."""
    try:
        if verbose:
            print(f"  Processing {item}...")
        
        # Main logic here
        result = do_work(item)
        
        return result
        
    except Exception as e:
        print(f"ERROR {item}: {e}")
        return None

def main():
    print("="*80)
    print("SCRIPT NAME - Brief Description")
    print("="*80)
    
    # Setup
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    items = load_items()
    print(f"\n{len(items)} items to process")
    print(f"Estimated time: {len(items) * RATE_LIMIT / 60:.0f} minutes\n")
    
    # Confirmation
    response = input("Proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return
    
    # Process with checkpoints
    results = []
    start_time = time.time()
    
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}]", end=" ")
        
        result = process_item(item)
        if result:
            results.append(result)
        
        # Checkpoint
        if i % CHECKPOINT_FREQ == 0:
            save_checkpoint(results)
        
        # Rate limit
        time.sleep(RATE_LIMIT)
    
    # Final save
    save_results(results)
    
    elapsed = (time.time() - start_time) / 60
    print(f"\n{'='*80}")
    print(f"Complete: {len(results)}/{len(items)} items")
    print(f"Runtime: {elapsed:.1f} minutes")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
```

---

## Remember

**"If it's not tested, it's broken."**

Always create test version → verify → then production.

Never skip testing to save time. The bug you catch in testing saves hours of debugging production failures.
