# Task: Generate Full Coin Sweep Script (1m + 5m)

Generate a single Python script that backtests ALL cached cryptocurrency coins on BOTH 1-minute and 5-minute timeframes using the Four Pillars v3.8 trading strategy.

## Absolute Paths

- **Project root**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
- **Script location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\sweep_all_coins.py`
- **Data cache**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\`
- **Output directory**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\output\sweep_all_coins\`
- **Ollama prompt file (this file)**: `C:\Users\User\Documents\Obsidian Vault\trading-tools\prompts\SWEEP-ALL-COINS-PROMPT.md`
- **Ollama runner**: `C:\Users\User\Documents\Obsidian Vault\trading-tools\run_ollama_sweep.py`

## Run Commands

Direct run:
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/sweep_all_coins.py
python scripts/sweep_all_coins.py --dry-run --no-db --top 5
```

Ollama generate + test + listen:
```
cd "C:\Users\User\Documents\Obsidian Vault\trading-tools"
python run_ollama_sweep.py
python run_ollama_sweep.py --skip-generate
python run_ollama_sweep.py --no-listen
```

## Requirements

1. Auto-discover all cached coins from `data/cache/*.parquet` using `BybitFetcher.list_cached()`
2. Run BOTH 1m (raw cached data) and 5m (resampled) for each coin
3. Compute Four Pillars signals via `compute_signals()`
4. Run Backtester with these params:
   - sl_mult=1.0, tp_mult=1.5, cooldown=3
   - b_open_fresh=True, notional=10000.0
   - commission_rate=0.0008, rebate_pct=0.70
   - be_raise_amount=2.0
5. Save each result to PostgreSQL via `save_backtest_run()` with timeframe column
6. Output directory: `data/output/sweep_all_coins/` with write permission check
7. Output files: timestamped CSV, JSON summary, log file, plus `latest.csv` / `latest.json`
8. Per-timeframe rankings (top N by expectancy)
9. Head-to-head 1m vs 5m comparison table
10. Grand summary with total trades, net P&L, profitable %
11. CLI args: `--dry-run`, `--no-db`, `--top N`

## Imports Available

```python
from data.fetcher import BybitFetcher
from data.db import save_backtest_run
from signals.four_pillars import compute_signals
from engine.backtester import Backtester
```

## Output Location

All output goes to `data/output/sweep_all_coins/` relative to project root.
Script MUST verify write permission before starting (create dir, write test file, delete test file).
On PermissionError, print clear error message and exit.

## File Structure

Generate exactly one file:

### scripts/sweep_all_coins.py

Generate the complete script following all requirements above.
