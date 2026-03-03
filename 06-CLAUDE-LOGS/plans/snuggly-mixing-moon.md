# B1 Plan: FourPillarsPlugin (strategies/four_pillars.py)

## Context

The previous session built `signals/four_pillars_v386.py` (the updated signal pipeline) and
`docs/FOUR-PILLARS-STRATEGY-v386.md` (strategy document). B1 is the next prerequisite: wrap
the Four Pillars backtester behind the Vince v2 `StrategyPlugin` ABC so the Enricher, Optimizer,
and Dash shell can all call it through a standard interface.

The existing `strategies/four_pillars.py` is a v1 class that inherits from the wrong base and
is missing 4 of 5 required methods. It must be archived, then replaced.

---

## Files Involved

| Path | Action |
|------|--------|
| `PROJECTS/four-pillars-backtester/strategies/four_pillars.py` | Archive → rewrite |
| `PROJECTS/four-pillars-backtester/strategies/four_pillars_v1_archive.py` | Create (copy of current v1) |
| `PROJECTS/four-pillars-backtester/scripts/build_b1_plugin.py` | Create (build script) |

**Read-only references (do not modify):**
- `strategies/base_v2.py` — `StrategyPlugin` ABC
- `signals/four_pillars_v386.py` — `compute_signals()` standalone function
- `engine/backtester_v385.py` — `Backtester385` class
- `docs/FOUR-PILLARS-STRATEGY-v386.md` — strategy document for `strategy_document` property

---

## Build Script: `scripts/build_b1_plugin.py`

Single script. Creates all files, validates, reports. User runs it from terminal.

**Steps inside the script:**

### Step 1 — Archive v1
- Read `strategies/four_pillars.py`
- Write contents to `strategies/four_pillars_v1_archive.py` (fail if archive already exists)
- py_compile archive → PASS required

### Step 2 — Write new `strategies/four_pillars.py`
Full `FourPillarsPlugin(StrategyPlugin)` class. See Implementation Notes below.
- py_compile → PASS required

### Step 3 — Smoke tests (4 tests, all inline)
1. **Syntax check** — `import py_compile` already done, counts as test 1
2. **Interface check** — instantiate `FourPillarsPlugin()`, assert it's a `StrategyPlugin` instance,
   assert `parameter_space()` returns a dict, assert `trade_schema()` returns a dict with all 6 required keys
3. **compute_signals check** — build a 100-row synthetic OHLCV DataFrame, call `plugin.compute_signals(df)`,
   assert result has `stoch_9`, `long_a`, `short_a` columns, assert no rows dropped
4. **strategy_document check** — call `plugin.strategy_document`, assert it's a Path, assert `.exists()`

Script prints `ALL TESTS PASSED` or lists failures. No pytest dependency.

---

## Implementation Notes: FourPillarsPlugin

### Imports (critical — name conflict resolution)
```python
from signals.four_pillars_v386 import compute_signals as _compute_signals_fn
```
The class method is named `compute_signals(self, ohlcv_df)` — must alias the module-level function
to avoid shadowing.

### Constructor
```python
DEFAULT_SIGNAL_PARAMS = {
    "cross_level": 25, "zone_level": 30, "stage_lookback": 10,
    "allow_b_trades": True, "allow_c_trades": False, "b_open_fresh": True,
    "cloud2_reentry": True, "reentry_lookback": 10, "use_ripster": True,
    "use_60d": True, "require_stage2": True, "rot_level": 50,
    "cloud3_window": 5, "atr_length": 14,
}
DEFAULT_BT_PARAMS = {
    "sl_mult": 1.5, "tp_mult": 2.5, "be_trigger_atr": 1.0,
    "be_lock_atr": 0.3, "margin": 10.0, "leverage": 10,
    "commission_rate": 0.0008,
}
def __init__(self, signal_params=None, bt_params=None):
    self._signal_params = {**self.DEFAULT_SIGNAL_PARAMS, **(signal_params or {})}
    self._bt_params = {**self.DEFAULT_BT_PARAMS, **(bt_params or {})}
```

### compute_signals(self, ohlcv_df)
- Validate required columns `{open, high, low, close, volume}` — raise `ValueError` with missing names
- Validate `len(ohlcv_df) >= 61` — raise `ValueError` with actual count
- Call `_compute_signals_fn(ohlcv_df.copy(), self._signal_params)` and return

### parameter_space(self)
Returns 7 sweepable params (signal + BT params mixed — both are valid Optuna sweep targets):
```python
{
    "sl_mult":        {"type": "float", "low": 0.5,  "high": 3.0},
    "tp_mult":        {"type": "float", "low": 1.0,  "high": 5.0},
    "be_trigger_atr": {"type": "float", "low": 0.5,  "high": 2.0},
    "be_lock_atr":    {"type": "float", "low": 0.1,  "high": 1.0},
    "cross_level":    {"type": "int",   "low": 15,   "high": 40},
    "allow_b_trades": {"type": "bool"},
    "allow_c_trades": {"type": "bool"},
}
```

### trade_schema(self)
6 required keys + ~13 optional (grade, entry_stoch* snapshots, life_mfe, life_mae,
life_duration_bars, life_pnl_path, lsg_category). All values are description strings.

### run_backtest(self, params, start, end, symbols)
Key design decisions:
- **Param routing**: pass ALL `params` to both signal pipeline AND Backtester385 — each uses
  what it knows via `.get()` with defaults, ignoring unknown keys. No explicit split needed.
- **Merged config**: `bt_cfg = {**self._bt_params, **params}` (params override defaults)
- **Signal config**: `sig_cfg = {**self._signal_params, **params}` (same override pattern)
- **Data path**: read from `config.yaml` → `data.cache_dir`, fallback to `data/cache/` relative
  to project root. Symbol parquet = `{cache_dir}/{symbol}_1m.parquet`
- **Date filter**: if parquet has a `timestamp` column, filter `[start, end]` inclusive after
  converting to UTC datetime
- **Min rows guard**: skip symbol if `len(df) < 61` after filtering (not an error — just no trades)
- **Backtester call**: `Backtester385(params={**bt_cfg, "symbol": symbol}).run(df)`
- **Output**: concat all symbols' `trades_df`, add `symbol` column, write to
  `results/trades_b1_{timestamp}.csv`, return `Path`
- **Empty result**: if no trades across all symbols, write empty CSV with schema columns, still
  return valid Path

### strategy_document property
```python
doc = Path(__file__).parent.parent / "docs" / "FOUR-PILLARS-STRATEGY-v386.md"
if not doc.exists():
    raise FileNotFoundError("Strategy document not found: " + str(doc))
return doc
```

---

## What B1 Does NOT Include

Per build spec — out of scope, do not add:
- No Dash / Plotly code
- No PostgreSQL writes
- No Optuna calls
- No Enricher logic
- No RL / LLM layer
- No pytest dependency (smoke tests are inline)

---

## Run Command (user executes)

```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts/build_b1_plugin.py
```

Expected output:
```
[ARCHIVE] strategies/four_pillars_v1_archive.py — py_compile PASS
[WRITE]   strategies/four_pillars.py — py_compile PASS
[TEST 1]  Syntax check — PASS
[TEST 2]  Interface check — PASS
[TEST 3]  compute_signals check — PASS
[TEST 4]  strategy_document check — PASS
ALL TESTS PASSED
```

---

## Post-Build Memory Updates

After successful build, update (Edit tool only, no Write):
- `06-CLAUDE-LOGS/2026-03-02-b1-four-pillars-plugin.md` — session log
- `06-CLAUDE-LOGS/INDEX.md` — add row
- `PRODUCT-BACKLOG.md` — B1 DONE, B2 READY
- `memory/TOPIC-vince-v2.md` — B1 status
- `LIVE-SYSTEM-STATUS.md` — if applicable
- `06-CLAUDE-LOGS/plans/2026-03-02-b1-four-pillars-plugin.md` — vault plan copy
