# B1 Plugin Build — Research, Scope & Audit

**Date:** 2026-02-28
**File referenced by user:** `PROJECTS/four-pillars-backtester/BUILD-VINCE-B1-PLUGIN.md`
**Status of that file:** DOES NOT EXIST. Researched from actual build documentation below.

---

## Context

B1 is the first build step in the Vince v2 trade research engine (approved 2026-02-27).
B1 creates a v2-compliant `FourPillarsPlugin` that wraps the existing Four Pillars backtester,
making it accessible to all Vince analysis components (Enricher, Optimizer, Validator, LLM layer).
Without B1, nothing in Vince can run — it is the foundation.

---

## Source Documents

| Doc | Path |
|-----|------|
| Build plan (B1-B10) | `C:\Users\User\.claude\plans\async-watching-balloon.md` |
| Vault copy | `06-CLAUDE-LOGS\plans\2026-02-27-vince-b1-b10-build-plan.md` |
| Plugin interface spec | `PROJECTS/four-pillars-backtester/docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` |
| Concept doc (approved) | `PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md` |
| ABC to implement | `PROJECTS/four-pillars-backtester/strategies/base_v2.py` |

---

## Skills Required

| Skill | Why Needed | When |
|-------|-----------|------|
| **four-pillars** | Signal logic, grade system (A/B/C/D/ADD/RE), stochastic periods, parameter semantics | Load before writing any B1 code |
| **four-pillars-project** | Cross-file versioning (which v383, v384 files are current), overall build context | Load at session start |
| **dash** | NOT needed for B1. B1 is pure Python. Mandatory from B6 (vince/app.py) onward. | Skip for B1 |

No pinescript, no n8n, no claude-developer-platform needed for B1.

---

## Critical Discovery: File Already Exists (v1)

`strategies/four_pillars.py` already exists with a v1 partial implementation.
**It is NOT v2-compliant.** It must be rewritten, not created from scratch.

### What the existing file does wrong

| Issue | Detail |
|-------|--------|
| Wrong base class | `from strategies.base import StrategyPlugin` — imports v1 ABC, not v2 |
| Missing 4 required methods | No `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document` |
| Wrong signal version | Uses `signals/state_machine_v383.py` directly — build plan says use `signals/four_pillars_v383_v2.py` |
| Wrong `compute_signals` signature | Takes `params=None` — v2 ABC takes only `ohlcv_df` (params baked into constructor) |
| Split enrichment | Separate `enrich_ohlcv()` method — v2 merges this into `compute_signals()` |
| Legacy v1 methods present | `extract_features()`, `get_feature_names()`, `label_trades()` — v1 classifier methods, incompatible with v2 |

### NEVER OVERWRITE FILES rule applies

Existing `strategies/four_pillars.py` must be archived before rewriting.
Create versioned backup: `strategies/four_pillars_v1_archive.py` first.

---

## Scope of Work — B1 Only

**One target file:** `strategies/four_pillars.py` (rewrite)

### 5 methods to implement (ABC contract from `base_v2.py`)

#### 1. `compute_signals(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame`
- Merge current `enrich_ohlcv()` + `compute_signals()` into one method
- No `params` argument — bake DEFAULT_PARAMS into `__init__` (constructor params override)
- Call chain: `compute_all_stochastics()` → `compute_clouds()` → ATR → state machine
- Use `signals/four_pillars_v383_v2.py::compute_signals_v383()` as the orchestrator (build plan mandate)
- All original columns preserved, indicator columns appended, no NaN beyond lookback

#### 2. `parameter_space(self) -> dict`
- Extract sweepable params from `DEFAULT_BT_PARAMS`
- Confirmed sweepable (with sensible bounds):
  - `sl_mult`: float, low=0.5, high=5.0
  - `tp_mult`: float, low=0.5, high=5.0
  - `be_trigger_atr`: float, low=0.0, high=3.0
  - `be_lock_atr`: float, low=0.0, high=1.0
  - `cross_level`: int, low=15, high=50
  - `allow_b_trades`: bool
  - `allow_c_trades`: bool
- Fixed/non-sweepable params stay in constructor only (commission_rate, notional, etc.)

#### 3. `trade_schema(self) -> dict`
- Map `Trade384` dataclass fields to schema dict
- Required 6 (per spec): `entry_bar`, `exit_bar`, `pnl`, `commission`, `direction`, `symbol`
- Optional extras (Four Pillars specific): `grade`, `entry_price`, `exit_price`, `sl_price`, `tp_price`, `mfe`, `mae`, `exit_reason`, `saw_green`, `be_raised`, `exit_stage`, `entry_atr`, `scale_idx`
- `symbol` is added by `run_backtest()` wrapper (not in Trade384 — Trade384 is per-symbol)

#### 4. `run_backtest(self, params, start, end, symbols) -> Path`
- Validate: `start < end`, ISO date format, non-empty symbols list
- For each symbol in `symbols`:
  - Load parquet from `data/cache/{symbol}_5m.parquet`
  - Raise `FileNotFoundError` if missing
  - Filter to `[start, end]` date range (on timestamp column)
  - Call `compute_signals()` to enrich the OHLCV slice
  - Instantiate `Backtester384(params)` and call `.run(enriched_df)`
  - Collect `result["trades"]` list of `Trade384` objects
  - Add `symbol` field to each trade
- Write all trades to `results/vince_{timestamp}.csv`
- Return `Path` to that CSV

**Thread-safety note:** Backtester384 is instantiated fresh per call — no shared mutable state. Thread-safe.

**Bar index note:** `entry_bar` / `exit_bar` in Trade384 are 0-based indices into the DATE-FILTERED DataFrame slice passed to `.run()`. The Enricher must use the same filtered slice when enriching. B1 only guarantees bar indices are correct for the slice it ran on — the Enricher slice alignment is an Enricher (B3) concern.

#### 5. `strategy_document` (property) -> Path
- Point to `docs/FOUR-PILLARS-STRATEGY-UML.md` (exists, is markdown)
- Raise `FileNotFoundError` if file is missing at access time

---

## Files B1 Reads / Wraps (do not modify)

| File | How B1 Uses It |
|------|---------------|
| `strategies/base_v2.py` | Imports `StrategyPlugin` ABC |
| `signals/four_pillars_v383_v2.py` | Calls `compute_signals_v383()` in `compute_signals()` |
| `engine/backtester_v384.py` | Instantiates `Backtester384`, calls `.run()` |
| `engine/position_v384.py` | `Trade384` dataclass — field list for `trade_schema()` |
| `engine/commission.py` | Instantiated inside Backtester384 (no direct import needed) |
| `docs/FOUR-PILLARS-STRATEGY-UML.md` | Returned by `strategy_document` property |

---

## Audit Findings

### Confirmed correct in build plan
- ABC in `base_v2.py` is py_compile-clean and complete
- `Backtester384.run()` returns `{"trades": [...], "trades_df": ..., "metrics": ..., "equity_curve": ...}`
- Trade384 has all needed fields including `entry_bar`, `exit_bar`, `pnl`, `commission`, `direction`, `grade`
- Strategy markdown doc exists at `docs/FOUR-PILLARS-STRATEGY-UML.md`
- `data/cache/` parquet loading pattern confirmed from `run_backtest_v384.py`

### Issues found (need decisions before build)

1. **Existing file conflict** — `strategies/four_pillars.py` exists (v1). NEVER OVERWRITE rule requires archiving first.

2. **Signal version mismatch** — existing file uses `FourPillarsStateMachine383` directly. Build plan mandates `signals/four_pillars_v383_v2.py::compute_signals_v383()` as the call point. These may produce different results. Confirm which is current.

3. **`backtester_v385.py` exists** — alongside v384. The build plan specifies v384. Confirm v384 is still the production engine (not v385).

4. **No `symbol` field in Trade384** — run_backtest() must add it manually when building the CSV. The trade_schema() must declare it even though it's not natively in Trade384.

5. **Date filtering mechanism** — parquets use a timestamp column. The filter `start <= ts <= end` requires knowing the column name. Confirmed from `run_backtest_v384.py`: parquets have a timestamp index or column. Need to confirm column name before writing filter logic.

---

## Verification (after build)

```bash
# Syntax check
python -c "import py_compile; py_compile.compile('strategies/four_pillars.py', doraise=True)"

# Interface smoke test
python -c "
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
ps = fp.parameter_space()
assert 'sl_mult' in ps
ts = fp.trade_schema()
assert 'entry_bar' in ts and 'symbol' in ts
doc = fp.strategy_document
assert doc.exists()
print('B1 interface: PASS')
"

# compute_signals smoke test (requires parquet)
python -c "
import pandas as pd, numpy as np
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
dummy = pd.DataFrame({'open': np.random.rand(300)*100, 'high': np.random.rand(300)*100+1,
    'low': np.random.rand(300)*100-1, 'close': np.random.rand(300)*100,
    'volume': np.random.rand(300)*1e6})
out = fp.compute_signals(dummy)
assert 'long_a' in out.columns
print('compute_signals: PASS')
"

# Full backtest smoke test (requires real parquet)
python -c "
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
params = {**fp.DEFAULT_BT_PARAMS, 'sl_mult': 2.0}
csv_path = fp.run_backtest(params, '2025-01-01', '2025-02-01', ['BTCUSDT'])
print('run_backtest CSV:', csv_path)
import pandas as pd
df = pd.read_csv(csv_path)
assert 'entry_bar' in df.columns and 'symbol' in df.columns
print('run_backtest: PASS')
"
```

---

## What B1 Does NOT Include

- No Dash code (B6+)
- No enricher logic (B3)
- No API layer (B2)
- No vince/ directory files
- No database writes
- No Optuna calls
- No RL components
- No LLM integration
