# Build Journal -- 2026-02-10

## v3.8 Sweep Complete (5-coin, 12 BE configs)

60 backtests executed. All saved to PostgreSQL (run_id 2-61).

### Results: Fixed-$ BE vs ATR-based BE

| Coin | Best Fixed | Net P&L | Best ATR | Net P&L | Delta |
|------|-----------|---------|----------|---------|-------|
| 1000PEPEUSDT | BE$4 | +$1,068 | ATR0.3/0.1 | -$3,197 | -$4,265 |
| RIVERUSDT | BE$6 | +$19,545 | ATR0.3/0.1 | +$7,260 | -$12,285 |
| KITEUSDT | BE$4 | +$2,456 | ATR0.3/0.1 | -$1,825 | -$4,281 |
| HYPEUSDT | BE$4 | +$589 | ATR0.3/0.1 | -$3,367 | -$3,956 |
| SANDUSDT | BE$6 | +$1,845 | ATR0.3/0.1 | -$1,645 | -$3,490 |

**Verdict**: Fixed-$ BE wins on ALL coins. ATR-based BE loses money everywhere except RIVER.
ATR trigger distances too wide for low-price coins relative to fixed $ thresholds.

### v3.8 Cloud 3 Filter Impact

| Version | Total Net P&L | Total Trades | Avg Exp/trade |
|---------|--------------|--------------|---------------|
| v3.7.1 (no filter) | +$97,060 | 20,283 | +$4.79 |
| v3.8 (Cloud 3 filter) | +$25,500 | 6,731 | +$3.79 |

Cloud 3 filter blocks ~67% of trades. Per-trade quality drops from $4.79 to $3.79.
Filter is too aggressive for rebate farming where volume matters.

---

## ATR-based BE Raise Added to Backtester

Files modified:
- `engine/position.py` -- Added `be_trigger_atr` and `be_lock_atr` params
- `engine/backtester.py` -- Pass-through to Position constructor

Logic: When `be_trigger_atr > 0`, uses ATR-based trigger instead of fixed-dollar.
LONG: if high >= entry + (trigger * ATR), lock SL at entry + (lock * ATR).
SHORT: mirror.

---

## 399-Coin Full Sweep Built

Script: `scripts/sweep_all_coins.py`
- Auto-discovers all 399 cached coins
- 5m timeframe, v3.8 Cloud 3 filter, BE$2
- Saves to PostgreSQL + CSV + JSON + log
- Output: `data/output/sweep_all_coins/`
- Write permission check before start
- CLI: `--dry-run`, `--no-db`, `--top N`

Ollama prompt: `trading-tools/prompts/SWEEP-ALL-COINS-PROMPT.md`
Ollama can regenerate/review via: `python auto_generate_files.py prompts/SWEEP-ALL-COINS-PROMPT.md`

---

## MEMORY.md Hard Rules Established

Non-negotiable rules added to prevent token waste:
1. OUTPUT = BUILDS ONLY (write code + run command, stop)
2. NO FILLER (no humanizing)
3. NO BASH EXECUTION (user runs from terminal)
4. NEVER use emojis

Clarifications: DO read files to verify, DO run exploratory bash, DO explain/summarize briefly.

---

## Status at End of Session

### Completed
- v3.8 5-coin sweep (60 backtests, PostgreSQL run_id 2-61)
- ATR-based BE raise in position.py
- 399-coin sweep script built + evaluated
- Ollama prompt for sweep regeneration
- MEMORY.md hard rules
- Build journal

### Ready to Run
- `python scripts/sweep_all_coins.py` (399 coins, ~15-30 min)

### Next
- Priority 3: Run 399-coin sweep, analyze results
- Priority 4: Optuna on top 10 coins
- Priority 5: MFE/MAE depth analysis from PostgreSQL
- Priority 6: ML pipeline (ml/ directory)
