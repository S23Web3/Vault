# Plan: BingX Trade Analyzer v2

## Context

Bot has been running ~1 day (2026-03-04 17:52 to 2026-03-05 13:24+). 49 trades at $50 notional. Existing `run_trade_analysis.py` works but:
- Markdown tables have no column padding (hard to read)
- Terminal output is only 6 lines (too sparse)
- Missing analysis dimensions (symbol leaderboard, direction split, hold times, equity curve, TTP/BE effectiveness)
- Date filter hardcoded to `2026-03-04`

## What We Build

One build script: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_trade_analyzer_v2.py`

Creates: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_trade_analysis_v2.py`

## Analyzer v2 Spec

### Input

- Reads `trades.csv` (all columns including TTP/BE fields)
- Fetches 5m klines from BingX API for MFE/MAE/saw_green (same as v1)
- Config from `config.yaml` (demo_mode for API base URL)
- Credentials from `.env` (BINGX_API_KEY, BINGX_SECRET_KEY)

### CLI Flags

- `--from YYYY-MM-DD` — start date filter (default: 2026-03-04)
- `--to YYYY-MM-DD` — end date filter (default: today)
- `--days N` — shortcut: last N days (overrides --from)
- `--no-api` — skip kline fetches, local-only mode (uses existing TTP fields from CSV)

### Output (3 formats)

1. **Terminal** — fixed-width padded tables using f-string formatting
2. **Markdown** — `logs/trade_analysis_v2_YYYY-MM-DD.md` with padded markdown tables
3. **CSV** — `logs/trade_analysis_v2_YYYY-MM-DD.csv` with enriched per-trade data

### Analysis Sections (all three outputs)

1. **Summary Stats**
   - Total trades, wins, losses, win rate %
   - Net PnL, gross profit, gross loss, profit factor
   - Avg PnL per trade, avg winner, avg loser
   - Best trade, worst trade
   - LSG count + % (losers that saw green)

2. **Equity Curve** (terminal: ASCII mini-chart of cumulative PnL; markdown: data table)

3. **Symbol Leaderboard**
   - Symbol | Trades | Wins | WR% | Net PnL | Avg PnL
   - Sorted by net PnL descending

4. **Direction Breakdown**
   - LONG vs SHORT: trades, WR%, net PnL, avg MFE, avg MAE

5. **Grade Breakdown**
   - A vs B vs C: trades, WR%, net PnL, avg MFE, LSG%

6. **Exit Reason Breakdown**
   - SL_HIT, TTP_EXIT, EXIT_UNKNOWN, etc: count, % of total, avg PnL per exit type

7. **Hold Time Analysis**
   - Avg hold (minutes), shortest, longest
   - Winners avg hold vs losers avg hold

8. **TTP Performance** (if TTP trades exist)
   - TTP trades count, avg extreme %, avg trail %
   - TTP net PnL vs non-TTP net PnL

9. **BE Raise Effectiveness** (if BE trades exist)
   - BE raised trades: count, WR%, net PnL
   - Non-BE trades: count, WR%, net PnL

10. **Per-Trade Detail Table**
    - Properly spaced columns: Symbol | Dir | Grade | Entry | Exit | Reason | PnL | MFE% | MAE% | SawGreen | Hold(min) | BE | TTP

### Table Formatting

Terminal + Markdown: all columns padded to fixed widths using f-strings:

```text
Symbol        Dir    Grade  Entry       Exit        Reason        PnL       MFE%    MAE%   Green  Hold  BE   TTP
BOME-USDT     LONG   B      0.0004273   0.0004296   SL_HIT        +$0.21    0.96    0.66   Yes    16m   Yes  No
RIVER-USDT    SHORT  B      16.9070     17.3460     SL_HIT        -$1.31    0.00    0.00   No     24m   No   No
```

### Reused Code

- `sign_and_build()` from existing `run_trade_analysis.py` line 37 — BingX API signing
- `fetch_klines()` from existing `run_trade_analysis.py` line 68 — kline fetching
- `compute_mfe_mae()` from existing `run_trade_analysis.py` line 89 — MFE/MAE calculation
- `to_ms()` from existing `run_trade_analysis.py` line 115 — timestamp parsing
- Commission rate: 0.0008 (0.08% taker per side)

---

## Build Audit — Known Hazards

### CRITICAL: CSV Schema Mismatch

- **Header** (line 1): 12 columns — `timestamp,symbol,direction,grade,entry_price,exit_price,exit_reason,pnl_net,quantity,notional_usd,entry_time,order_id`
- **Rows 2-231** (old trades): 12 values — match header
- **Rows 232+** (newer trades): 18 values — 6 extra fields appended WITHOUT header update
- Extra fields (positional): `ttp_activated, ttp_extreme_pct, ttp_trail_pct, ttp_exit_reason, be_raised, saw_green`
- **Fix**: Use pandas `read_csv()`. Detect column count from first data row vs header. If mismatch, manually assign extended column names. OR: read with `names=FULL_18_COLUMNS, header=0` and let pandas handle the ragged rows.
- **Safest approach**: `pd.read_csv(path, names=FULL_COLUMNS, header=0, on_bad_lines='warn')` with all 18 column names defined. Rows with only 12 values get NaN for the last 6 columns.

### HIGH: F-String Escape Trap (Build Script Rule)

- Per MEMORY.md: NEVER use escaped quotes in f-strings inside build scripts
- All `join()` calls inside the generated source must use string concatenation, not f-string braces
- Example WRONG: `f"SYMBOLS: {', '.join(symbols)}"`
- Example RIGHT: `"SYMBOLS: " + ", ".join(symbols)`

### HIGH: Division by Zero Guards

- Zero trades after date filter: skip all analysis, print "No trades found"
- All wins (zero losses): LSG% = 0, avg loser = 0, profit factor = inf -> cap at 999.9
- All losses (zero wins): avg winner = 0, profit factor = 0
- Empty grade/symbol groups: skip row in breakdown table

### MEDIUM: API Failure Handling

- kline fetch returns empty list for delisted/renamed symbols — MFE/MAE = 0.0, saw_green = False
- API timeout (15s) — log warning, continue to next trade
- Rate limit: 0.3s sleep between calls (same as v1, ~200 req/min is within BingX limit)
- `--no-api` flag skips all API calls, uses ttp_extreme_pct from CSV as MFE proxy

### MEDIUM: Float/String Parsing

- `pnl_net`, `entry_price`, `exit_price` may be empty string in corrupted rows — wrap in try/except, default to 0.0
- `ttp_extreme_pct` may be empty string or NaN — treat as 0.0
- `be_raised` is string "True"/"False" or empty — parse with `str(x).lower() == "true"`

### MEDIUM: Hold Time Edge Cases

- `entry_time` missing on some old trades — fall back to `timestamp - 1hr`
- Hold time < 0 (clock skew) — clamp to 0

### LOW: Timestamp Format

- All timestamps are ISO 8601 with timezone offset (+00:00 or Z) — use `datetime.fromisoformat()` with Z replacement

---

## Testing Plan

### Test 1: py_compile (mandatory, in build script)

```python
py_compile.compile(output_path, doraise=True)
```

Build script calls this immediately after writing the file. Build fails if syntax error.

### Test 2: Dry Run — `--no-api` mode

```bash
python scripts/run_trade_analysis_v2.py --no-api --days 1
```

- Verifies CSV parsing, date filtering, all analysis sections, table formatting
- No API dependency — runs in <1 second
- Check: all 10 sections print, no crashes, no division-by-zero errors
- Check: column alignment visually correct in terminal

### Test 3: Small API Run — `--days 1`

```bash
python scripts/run_trade_analysis_v2.py --days 1
```

- Tests API integration with minimal trades (~20-30 for one day)
- Check: MFE/MAE values populated (not all zeros)
- Check: saw_green flag matches expectation (MFE > 0.16% threshold)
- Check: CSV output has all 13+ columns

### Test 4: Full Run — all trades since 2026-03-04

```bash
python scripts/run_trade_analysis_v2.py
```

- ~49 trades, ~2 minutes with 0.3s rate limit
- Check: markdown report in `logs/trade_analysis_v2_2026-03-05.md`
- Check: CSV in `logs/trade_analysis_v2_2026-03-05.csv`
- Check: all analysis sections populated

### Test 5: Edge Case — Empty Date Range

```bash
python scripts/run_trade_analysis_v2.py --from 2099-01-01
```

- Should print "No trades found in date range" and exit cleanly
- No crashes, no empty tables

### Test 6: Output Validation Checklist

- [ ] Terminal tables aligned (check Symbol column, PnL column, MFE column)
- [ ] Markdown tables render correctly in Obsidian
- [ ] CSV opens correctly in Excel/pandas (correct column count per row)
- [ ] Summary stats match manual spot-check (count a few trades by hand)
- [ ] Equity curve cumulative PnL = sum of individual PnL values
- [ ] Hold times in minutes make sense (not negative, not >24h for most)

### Debugging Aids Built Into Script

1. **`--verbose` flag**: Print each trade as it's processed (symbol, API status, MFE/MAE)
2. **Error counter**: Track and report parse errors, API failures at end of run
3. **Progress indicator**: `[15/49] Processing RIVER-USDT...` on terminal
4. **Timestamped logging**: All log lines include timestamp per MEMORY.md rule
5. **API response logging**: On failure, log HTTP status code + response body (first 200 chars)

---

## Files

### New Files (created by build script)

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_trade_analyzer_v2.py` (build script)
- Output: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_trade_analysis_v2.py` (analyzer)

### No Files Modified

### Run Commands

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector"
python scripts/build_trade_analyzer_v2.py
python scripts/run_trade_analysis_v2.py --no-api          # Test 2: dry run
python scripts/run_trade_analysis_v2.py --days 1           # Test 3: small API
python scripts/run_trade_analysis_v2.py                    # Test 4: full run
python scripts/run_trade_analysis_v2.py --from 2099-01-01  # Test 5: empty range
```
