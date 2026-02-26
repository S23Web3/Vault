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

# ❌ FATAL — Even in docstrings
"""
File: C:\Users\User\Documents\Obsidian Vault\PROJECTS\file.py
"""

# ✅ CORRECT — Use raw strings for paths
path = r"C:\Users\User\Documents\project"

# ✅ CORRECT — Use pathlib (preferred)
path = Path("C:/Users/User/Documents/project")
path = Path(__file__).resolve().parent.parent

# ✅ CORRECT — Forward slashes in docstrings
"""
File: C:/Users/User/Documents/project/file.py
Run: python scripts/my_script.py
"""
```

### Rules for All Generated Python Files

1. **NEVER put Windows backslash paths in docstrings** — use forward slashes
2. **NEVER put Windows backslash paths in string literals** — use `r''` or `Path()`
3. **NEVER put Windows backslash paths in f-strings** — use `Path` objects
4. **ALL path construction MUST use `pathlib.Path`**
5. **Run-instructions in docstrings** — use forward slashes

---

## Pre-Execution Validation

### Always Syntax-Check Before Running

Every build prompt should include this validation step:
```
After writing each .py file:
1. Run: python -m py_compile <file.py>
2. If SyntaxError → fix immediately, do not proceed
3. Only run the script after syntax check passes
```

---

## Windows Environment Rules

**Desktop = Windows 11, VPS = Ubuntu 24**

```python
# ✅ CORRECT - Works on both
from pathlib import Path
cache_dir = Path("data/cache")
file_path = cache_dir / "RIVERUSDT_1m.parquet"

# ❌ WRONG - Breaks on Windows
file_path = "data/cache/RIVERUSDT_1m.parquet"
```

---

## Filename Etiquette & Location

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Module | `snake_case.py` | `capital_model.py` |
| Class | `PascalCase` | `CapitalModel` |
| Function/var | `snake_case` | `compute_pnl()` |
| Constant | `SCREAMING_SNAKE` | `COMMISSION_RATE = 0.0008` |
| Test file | `test_<module>.py` | `test_capital_model.py` |
| Build script | `build_<feature>.py` | `build_dashboard_v391.py` |
| Sanity check | `sanity_check_<module>.py` | `sanity_check_bbwp.py` |
| Debug script | `debug_<module>.py` | `debug_bbw_sequence.py` |

### Project Directory Structure

```
four-pillars-backtester/
├── scripts/          # build_*.py, sanity_check_*.py, debug_*.py, run_*.py
├── tests/            # test_*.py  (one per module)
├── utils/            # shared helpers (capital_model.py, pdf_exporter.py)
├── signals/          # indicator logic (bbwp.py, bbw_sequence.py)
├── research/         # exploratory modules (bbw_simulator.py)
├── data/             # normalizer.py, cache/ (parquet files)
└── results/          # CSV/PNG outputs from sanity checks
```

### Versioning Rule (MANDATORY)

```python
# BEFORE writing any file — check existence first
from pathlib import Path

def safe_write_path(base_path: Path) -> Path:
    """Return versioned path if base already exists."""
    if not base_path.exists():
        return base_path
    stem, suffix = base_path.stem, base_path.suffix
    n = 2
    while True:
        candidate = base_path.parent / f"{stem}_v{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1

# Usage
out = safe_write_path(Path("scripts/dashboard.py"))
# → scripts/dashboard_v2.py if dashboard.py already exists
```

---

## Debugging

### Use `logging`, Never `print`

```python
import logging

# Module-level setup (top of every module)
log = logging.getLogger(__name__)

# In scripts that are entry points
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Usage
log.debug("bar=%d price=%.6f", i, price)   # verbose, suppressed in prod
log.info("Backtest complete: %d trades", n)
log.warning("No data for %s, skipping", symbol)
log.error("Failed to load cache: %s", e)
```

### Structured Exception Handling

```python
import traceback

# CORRECT — always log full traceback
try:
    result = run_backtest(symbol)
except Exception as e:
    log.error("Backtest failed for %s: %s", symbol, e)
    log.debug(traceback.format_exc())   # full stack in debug mode
    raise  # re-raise unless you have a recovery path

# WRONG — swallowing errors silently
try:
    result = run_backtest(symbol)
except Exception:
    pass
```

### Debug Script Pattern

Every non-trivial module gets a `scripts/debug_<module>.py`:

```python
"""
Debug script for <module>.
Run: python scripts/debug_<module>.py
"""
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def main():
    """Run targeted debug cases and print results."""
    log.info("=== Debug: <module> ===")
    # Load minimal real or synthetic data
    # Run the function under test
    # Print/assert expected vs actual
    log.info("=== Done ===")

if __name__ == "__main__":
    main()
```

### Log Level Discipline

| Level | When to use |
|-------|-------------|
| `DEBUG` | Per-bar/per-trade detail, internal state |
| `INFO` | Phase transitions, totals, completion messages |
| `WARNING` | Skipped symbols, missing data, fallbacks |
| `ERROR` | Caught exceptions, file failures |
| `CRITICAL` | Unrecoverable state, abort conditions |

---

## Testing (Enhanced)

### Programmatic py_compile in Build Scripts

Every build script MUST call `py_compile` immediately after writing each file:

```python
import py_compile, sys

def verify(path: str) -> bool:
    """Syntax-check a .py file; return True if clean."""
    try:
        py_compile.compile(path, doraise=True)
        print("  SYNTAX OK: " + path)
        return True
    except py_compile.PyCompileError as e:
        print("  SYNTAX ERROR: " + str(e))
        return False

# In build script, after every Write call:
ERRORS = []
if not verify(str(output_path)):
    ERRORS.append(str(output_path))

# At end of build script:
if ERRORS:
    print("BUILD FAILED — syntax errors in: " + ", ".join(ERRORS))
    sys.exit(1)
else:
    print("BUILD OK — all files compile clean")
```

### Test File Structure

```python
"""
Tests for <module>.
Run: python tests/test_<module>.py
"""
import unittest
from pathlib import Path

class Test<Module>(unittest.TestCase):

    def setUp(self):
        """Set up synthetic data shared across tests."""
        # Build minimal mock DataFrame or state here
        pass

    def test_<case>_expected(self):
        """<case> should return <expected> when <condition>."""
        result = function_under_test(self.mock_data)
        self.assertEqual(result, expected, msg="<case>: got " + str(result))

    def test_<case>_edge(self):
        """<case> edge: empty input returns empty output."""
        result = function_under_test([])
        self.assertEqual(len(result), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
```

### Mock Data for Trading Tests

```python
import pandas as pd
import numpy as np

def make_ohlcv(n=100, price=0.01, seed=42) -> pd.DataFrame:
    """Generate synthetic OHLCV DataFrame for testing."""
    rng = np.random.default_rng(seed)
    close = price + np.cumsum(rng.normal(0, price * 0.01, n))
    close = np.clip(close, price * 0.5, price * 2)
    df = pd.DataFrame({
        "open":   close * rng.uniform(0.999, 1.001, n),
        "high":   close * rng.uniform(1.000, 1.005, n),
        "low":    close * rng.uniform(0.995, 1.000, n),
        "close":  close,
        "volume": rng.integers(1_000_000, 10_000_000, n).astype(float),
    })
    df.index = pd.date_range("2025-01-01", periods=n, freq="1min")
    df.index.name = "datetime"
    return df
```

### Assert Patterns

```python
# WRONG — bare assert, no context on failure
assert result == 42

# CORRECT — message tells you what failed and why
self.assertEqual(result, 42, msg="net_pnl: expected 42, got " + str(result))
self.assertAlmostEqual(commission, 0.80, places=2, msg="commission rounding")
self.assertGreater(len(trades), 0, msg="should have at least one trade")
self.assertIn("symbol", df.columns, msg="output DataFrame missing 'symbol' column")
```

---

## Syntax Error Prevention (Build Scripts)

### The F-String Join Trap

When a build script writes Python source as a triple-quoted string, escaped quotes inside f-string braces produce invalid output:

```python
# TRAP — produces {', '.join(X)} → invalid in output file
content = f"""
    print("FAILURES: {\\', \\'.join(ERRORS)}")
"""

# CORRECT — use concatenation, no quotes inside braces
content = """
    print("FAILURES: " + ", ".join(ERRORS))
"""
```

### Triple-Quoted String Escaping Rules

| Character | Inside triple-quoted build content | Risk |
|-----------|-----------------------------------|------|
| `\n \t \r` | Fine — they are literal escapes in the string | Low |
| `\'` inside `{...}` | FATAL — backslash-quote inside f-string expression | HIGH |
| `{variable}` | Only in f-strings — use `{{` / `}}` to escape literal braces | Medium |
| Backslash paths | Use forward slashes inside build content strings | High |

```python
# CORRECT build content template
content = """\
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ERRORS = []

def check():
    print("PASS: " + ", ".join(["a", "b"]))
"""
# Note: no f-string, no backslash paths, no escaped quotes
```

### Secondary Validator: ast.parse

Use `ast.parse()` to catch semantic errors that `py_compile` misses (e.g. invalid f-string expressions at the AST level):

```python
import ast

def deep_check(path: str) -> bool:
    """AST-parse a .py file to catch f-string and expression errors."""
    try:
        source = Path(path).read_text(encoding="utf-8")
        ast.parse(source, filename=path)
        print("  AST OK: " + path)
        return True
    except SyntaxError as e:
        print("  AST ERROR in " + path + " line " + str(e.lineno) + ": " + str(e.msg))
        return False
```

### Common Gotchas Table

| Gotcha | Symptom | Fix |
|--------|---------|-----|
| `\U` in path string | `SyntaxError: (unicode error)` | Use `Path()` or `r""` |
| `\'` in f-string braces | `SyntaxError: f-string expression` | Use string concatenation |
| `{{` forgotten in f-string | Wrong output, not a syntax error | Always use `{{` for literal `{` |
| Missing `encoding="utf-8"` in `open()` | `UnicodeDecodeError` on Windows | Always specify encoding |
| `df.set_index('datetime')` | Column disappears, KeyError later | Check `df.index.name` too |
| `import *` in modules | Name collision, untestable | Always explicit imports |

---

## Code Patterns

### Input Validation (System Boundaries Only)

```python
def process(symbol: str, start: str, end: str) -> bool:
    """Process symbol for date range; return False and log on invalid input."""
    if not Path(f"data/cache/{symbol}.parquet").exists():
        log.warning("SKIP %s: no cache", symbol)
        return False
    if end <= start:
        log.error("Invalid date range: %s to %s", start, end)
        return False
    return True
```

### Graceful Degradation

```python
# Continue on per-item failure; collect errors at end
errors = []
for symbol in symbols:
    try:
        process(symbol)
    except Exception as e:
        log.error("FAIL %s: %s", symbol, e)
        errors.append(symbol)
        continue
if errors:
    log.warning("Failed: " + ", ".join(errors))
```

### API Rate Limiting

```python
import time

RATE_LIMIT = 1.0  # seconds between requests

est_min = len(symbols) * RATE_LIMIT / 60
print(f"Estimated: {est_min:.0f} min. Proceed? (yes/no): ", end="")
if input().strip().lower() != "yes":
    sys.exit(0)

for symbol in symbols:
    fetch(symbol)
    time.sleep(RATE_LIMIT)
```

### Data Validation (OHLCV)

```python
def validate_ohlcv(df: pd.DataFrame) -> bool:
    """Check OHLCV sanity; log and return False on failure."""
    bad = ((df["high"] < df["low"]) | (df["high"] < df["close"])).sum()
    if bad > 0:
        log.warning("%d invalid bars", bad)
        return False
    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        log.error("Missing columns: " + ", ".join(missing))
        return False
    return True
```

### Incremental Processing (Checkpoints)

```python
CHECKPOINT_FREQ = 10

for i, symbol in enumerate(symbols, 1):
    result = process(symbol)
    results.append(result)
    if i % CHECKPOINT_FREQ == 0:
        pd.DataFrame(results).to_parquet(f"results/checkpoint_{i}.parquet")
        log.info("Checkpoint: %d/%d", i, len(symbols))
```

### Performance

```python
# Parquet > CSV (10x faster, 5x smaller)
df.to_parquet(path, compression="snappy", index=False)
df = pd.read_parquet(path)

# Vectorized > row loops
df["pnl"] = (df["exit_price"] - df["entry_price"]) / df["entry_price"]
# WRONG: for i, row in df.iterrows(): df.at[i, "pnl"] = ...
```

---

## Trading System Specifics

### Commission Calculation

```python
COMMISSION_RATE = 0.0008  # 0.08% taker

# CORRECT — rate-based, sweepable
commission = notional * COMMISSION_RATE
net_pnl = gross_pnl - commission

# WRONG — hardcoded, breaks with different sizes
commission = 8.00
```

### UTC Timestamps

```python
# CORRECT — timezone-aware
df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)

# WRONG — naive timestamps cause comparison errors with tz-aware
df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
```

---

## Common Bugs

| Bug | Symptom | Fix |
|-----|---------|-----|
| Off-by-one in gap fill | Duplicate last bar | `end = earliest - timedelta(minutes=1)` |
| Wrong year in date calc | Stale data fetched | 2026 - 1 = 2025 (not 2024) |
| Naive vs aware datetime | `TypeError: can't compare offset-naive and offset-aware` | `.replace(tzinfo=earliest.tzinfo)` |
| `df.set_index("datetime")` | KeyError on "datetime" column | Check `df.index.name` too |
| Bare `except:` | Swallows all errors silently | Always `except Exception as e:` |
| `import *` | Silent name collision | Always explicit imports |

---

## Complete Script Template

```python
"""
Script purpose: One-line description
Run: python scripts/<name>.py
"""
import sys
import time
import logging
import traceback
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CACHE_DIR  = ROOT / "data" / "cache"
OUTPUT_DIR = ROOT / "data" / "output"
RATE_LIMIT = 1.0
CHECKPOINT = 10


def process(item: str) -> dict | None:
    """Process one item; return result dict or None on failure."""
    try:
        return {"item": item, "status": "ok"}
    except Exception as e:
        log.error("FAIL %s: %s", item, e)
        log.debug(traceback.format_exc())
        return None


def main() -> None:
    """Entry point."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    items: list[str] = []  # replace with real list

    log.info("Items: %d  Est: %.0f min", len(items), len(items) * RATE_LIMIT / 60)
    if input("Proceed? (yes/no): ").strip().lower() != "yes":
        log.info("Cancelled")
        return

    results, errors = [], []
    for i, item in enumerate(items, 1):
        log.info("[%d/%d] %s", i, len(items), item)
        result = process(item)
        if result:
            results.append(result)
        else:
            errors.append(item)
        if i % CHECKPOINT == 0:
            pd.DataFrame(results).to_parquet(OUTPUT_DIR / f"ckpt_{i}.parquet")
        time.sleep(RATE_LIMIT)

    pd.DataFrame(results).to_parquet(OUTPUT_DIR / "results.parquet")
    log.info("Done: %d ok, %d failed", len(results), len(errors))
    if errors:
        log.warning("Failed: " + ", ".join(errors))


if __name__ == "__main__":
    main()
```

---

## Code Review Checklist

Before submitting code, verify:

**Filename & Location**
- [ ] File in correct directory (`scripts/`, `tests/`, `signals/`, etc.)
- [ ] Name follows convention (`snake_case.py`, `test_<module>.py`, `debug_<module>.py`)
- [ ] Checked file existence first — no silent overwrites
- [ ] Versioned copy created if file already exists (`_v2`, `_v3`)

**Syntax & Compilation**
- [ ] `py_compile.compile(path, doraise=True)` passes on every new `.py` file
- [ ] `ast.parse()` secondary check passes
- [ ] NO backslash paths in docstrings, strings, or f-strings
- [ ] NO `\U`, `\N`, `\t`, `\n`, `\r`, `\b` sequences in string literals
- [ ] NO escaped quotes inside f-string braces (`\'` trap)
- [ ] Literal braces in f-strings use `{{` / `}}`
- [ ] All `open()` calls include `encoding="utf-8"`

**Testing**
- [ ] Test version created and run first
- [ ] User reviewed test output
- [ ] Test file in `tests/test_<module>.py`
- [ ] Each test has a descriptive `msg=` in assertions
- [ ] Mock data is deterministic (fixed seed)
- [ ] Edge cases covered (empty input, single bar, max values)

**Debugging**
- [ ] `logging` used — no bare `print()` for diagnostic output
- [ ] Log level appropriate (`DEBUG` for per-bar, `INFO` for totals)
- [ ] Exception handlers log full traceback via `traceback.format_exc()`
- [ ] Debug script created at `scripts/debug_<module>.py`

**Code Quality**
- [ ] Windows paths use `pathlib.Path`
- [ ] Every `def` has a one-line docstring
- [ ] No hardcoded dollar amounts — derive from rate * notional
- [ ] Rate limiting implemented (API calls)
- [ ] Progress indicators shown (long loops)
- [ ] Error handling for each failure mode
- [ ] Data validation at system boundaries (API input, file load)
- [ ] No hardcoded values — use named constants

---

**"If it's not tested, it's broken."**
