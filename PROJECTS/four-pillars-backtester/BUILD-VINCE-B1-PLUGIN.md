# B1 — FourPillarsPlugin Build Spec

**Status:** READY TO BUILD
**Date:** 2026-02-28
**Author:** Research + audit session (see `06-CLAUDE-LOGS/plans/2026-02-28-vince-b1-plugin-scope-audit.md`)

---

## What B1 Is

B1 creates a v2-compliant `FourPillarsPlugin` in `strategies/four_pillars.py`.

This is the **concrete implementation** of the `StrategyPlugin` ABC defined in `strategies/base_v2.py`.
It wraps the existing Four Pillars backtester and signal pipeline behind the Vince plugin interface.
Every subsequent Vince component (Enricher, Optimizer, Validator, LLM layer) depends on this file.
Nothing else in Vince can run until B1 is complete.

---

## Skills to Load Before Building

```
/four-pillars        # signal logic, grade system, stochastic parameters
/four-pillars-project  # file versioning, which engine/signal versions are current
```

Dash skill: NOT needed. B1 is pure Python. Mandatory from B6 onward.

---

## File Handling — NEVER OVERWRITE

`strategies/four_pillars.py` already exists (v1, wrong base class, missing 4 required methods).

**Before any rewrite:**
1. Copy existing to `strategies/four_pillars_v1_archive.py`
2. Then write the new v2 implementation to `strategies/four_pillars.py`

---

## What the Existing File Does Wrong (Audit)

| Issue | Detail |
|-------|--------|
| Wrong base class | `from strategies.base import StrategyPlugin` — v1 ABC, not v2 |
| Missing 4 required methods | No `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document` |
| Wrong signal call point | Calls `FourPillarsStateMachine383` directly — should call `compute_signals_v383()` from `signals/four_pillars_v383_v2.py` |
| Wrong `compute_signals` signature | Takes `params=None` arg — v2 ABC takes only `ohlcv_df` (params go in constructor) |
| Split enrichment | Separate `enrich_ohlcv()` — v2 merges ATR + stochastics + clouds + state machine into one `compute_signals()` call |
| Legacy v1 methods | `extract_features()`, `get_feature_names()`, `label_trades()` — v1 classifier methods, drop them |

---

## Engine Version: v385 (NOT v384)

`run_backtest()` must instantiate `Backtester385` from `engine/backtester_v385.py`.

v385 inherits v384 and adds a post-processing pass that attaches entry-state snapshots, lifecycle
metrics, P&L path classification, and LSG category to each trade. This pre-enriched data reduces
work for B3 (Enricher). v385 returns the same dict structure as v384 — use `result["trades_df"]`
to get the enriched DataFrame.

```python
from engine.backtester_v385 import Backtester385
```

---

## Signal Pipeline: `signals/four_pillars_v383_v2.py`

Use `compute_signals_v383()` as the single call point for all indicator computation.
It runs Numba-accelerated stochastics, clouds, ATR, and the v383 state machine.

```python
from signals.four_pillars_v383_v2 import compute_signals_v383
```

Function signature: `compute_signals_v383(df: pd.DataFrame, params: dict = None) -> pd.DataFrame`

The v2 plugin ABC requires `compute_signals(self, ohlcv_df)` with NO params arg.
Store signal params at construction time and pass them internally:

```python
def compute_signals(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    return compute_signals_v383(ohlcv_df.copy(), self._signal_params)
```

---

## Constructor

```python
def __init__(self, signal_params: dict = None, bt_params: dict = None):
    self._signal_params = {**self.DEFAULT_SIGNAL_PARAMS, **(signal_params or {})}
    self._bt_params = {**self.DEFAULT_BT_PARAMS, **(bt_params or {})}
```

`DEFAULT_SIGNAL_PARAMS` = indicator configuration (stoch periods, cloud periods, ATR length)
`DEFAULT_BT_PARAMS` = backtester configuration (sl_mult, tp_mult, commission, etc.)

Keep them separate — `parameter_space()` exposes only the BT params as sweepable.
Signal params are fixed per plugin instance (changing them changes what the strategy IS).

---

## Method Specifications

### 1. `compute_signals(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame`

```python
def compute_signals(self, ohlcv_df: pd.DataFrame) -> pd.DataFrame:
    """Attach all Four Pillars indicator columns to OHLCV data."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(ohlcv_df.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {missing}")
    if len(ohlcv_df) < 61:  # stoch_60 lookback
        raise ValueError(f"Need >= 61 rows, got {len(ohlcv_df)}")
    return compute_signals_v383(ohlcv_df.copy(), self._signal_params)
```

Output columns appended (all from `compute_signals_v383`):
`stoch_9`, `stoch_14`, `stoch_40`, `stoch_60`, `stoch_60_d`,
`ema5`, `ema12`, `ema34`, `ema50`, `ema72`, `ema89`,
`cloud2_bull`, `cloud3_bull`, `cloud3_allows_long`, `cloud3_allows_short`, `price_pos`,
`price_cross_above_cloud2`, `price_cross_below_cloud2`, `atr`,
`long_a`, `long_b`, `long_c`, `long_d`,
`short_a`, `short_b`, `short_c`, `short_d`,
`reentry_long`, `reentry_short`, `add_long`, `add_short`

---

### 2. `parameter_space(self) -> dict`

Returns sweepable BT parameters for Optuna (Mode 3). Signal params are NOT sweepable here.

```python
def parameter_space(self) -> dict:
    """Return sweepable backtester parameters with bounds."""
    return {
        "sl_mult":        {"type": "float", "low": 0.5,  "high": 5.0},
        "tp_mult":        {"type": "float", "low": 0.5,  "high": 5.0},
        "be_trigger_atr": {"type": "float", "low": 0.0,  "high": 3.0},
        "be_lock_atr":    {"type": "float", "low": 0.0,  "high": 1.0},
        "cross_level":    {"type": "int",   "low": 15,   "high": 50},
        "allow_b_trades": {"type": "bool"},
        "allow_c_trades": {"type": "bool"},
    }
```

Fixed/non-sweepable (stay in constructor only): `commission_rate`, `notional`, `rebate_pct`,
`settlement_hour_utc`, `initial_equity`, `max_positions`, `cooldown`, `checkpoint_interval`.

---

### 3. `trade_schema(self) -> dict`

Declares all columns the trade CSV will contain. Reflects v385 enriched output.

**6 required columns** (spec-mandated):

| Column | Type | Source |
|--------|------|--------|
| `entry_bar` | int | Trade384.entry_bar — 0-based index into the date-filtered OHLCV slice |
| `exit_bar` | int | Trade384.exit_bar — 0-based index into the date-filtered OHLCV slice |
| `pnl` | float | Trade384.pnl — gross PnL in USD before commission |
| `commission` | float | Trade384.commission — total round-trip commission in USD |
| `direction` | str | Trade384.direction — "LONG" or "SHORT" (exact strings) |
| `symbol` | str | Added by run_backtest() wrapper — ticker e.g. "BTCUSDT" |

**Optional columns (Four Pillars + v385 specific):**

| Column | Source |
|--------|--------|
| `grade` | Trade384.grade — "A", "B", "C", "D", "ADD", "RE" |
| `entry_price` | Trade384.entry_price |
| `exit_price` | Trade384.exit_price |
| `sl_price` | Trade384.sl_price |
| `tp_price` | Trade384.tp_price (None if no TP) |
| `mfe` | Trade384.mfe — maximum favorable excursion in USD |
| `mae` | Trade384.mae — maximum adverse excursion in USD |
| `exit_reason` | Trade384.exit_reason — "SL", "TP", "SCALEOUT", "EOD" |
| `saw_green` | Trade384.saw_green — bool, losing trade that reached positive PnL |
| `be_raised` | Trade384.be_raised — bool |
| `exit_stage` | Trade384.exit_stage — int |
| `entry_atr` | Trade384.entry_atr |
| `scale_idx` | Trade384.scale_idx |
| `entry_stoch9_value` | v385 entry snapshot |
| `entry_stoch9_direction` | v385 — "rising", "falling", "flat" |
| `entry_stoch14_value` | v385 entry snapshot |
| `entry_stoch40_value` | v385 entry snapshot |
| `entry_stoch60_value` | v385 entry snapshot |
| `entry_stoch60_d` | v385 entry snapshot |
| `entry_ripster_cloud` | v385 — "cloud3_{distance:.2f}" |
| `entry_ripster_expanding` | v385 — bool |
| `entry_vol_ratio` | v385 — volume vs 20-bar mean |
| `life_pnl_path` | v385 — P&L path classification |
| `lsg_category` | v385 — LSG category string |

---

### 4. `run_backtest(self, params: dict, start: str, end: str, symbols: list) -> Path`

```
Input:
  params  — keys from parameter_space(). All keys present, no extra keys.
  start   — "YYYY-MM-DD" inclusive
  end     — "YYYY-MM-DD" inclusive
  symbols — list of ticker strings, e.g. ["BTCUSDT", "ETHUSDT"]

Returns:
  Path to trade CSV in results/. File exists and is readable.
  CSV contains all columns from trade_schema().

Raises:
  ValueError  — start >= end, or invalid date format
  FileNotFoundError — parquet missing for any symbol
  RuntimeError — any internal backtester failure
```

**Implementation pattern:**

```python
def run_backtest(self, params, start, end, symbols):
    # 1. Validate dates
    from datetime import date
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    if s >= e:
        raise ValueError(f"start {start} must be before end {end}")

    # 2. Merge params into bt config
    bt_cfg = {**self._bt_params, **params}

    # 3. Per-symbol loop
    all_rows = []
    for sym in symbols:
        pq = CACHE_DIR / f"{sym}_5m.parquet"
        if not pq.exists():
            raise FileNotFoundError(f"Parquet not found: {pq}")

        df = pd.read_parquet(pq)
        df = _filter_date_range(df, start, end)   # see note below
        df = self.compute_signals(df)

        bt = Backtester385(bt_cfg)
        result = bt.run(df)
        trades_df = result["trades_df"]
        if len(trades_df) > 0:
            trades_df = trades_df.copy()
            trades_df["symbol"] = sym
            all_rows.append(trades_df)

    # 4. Write CSV
    from datetime import datetime
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = RESULTS_DIR / f"vince_{ts}.csv"
    RESULTS_DIR.mkdir(exist_ok=True)
    combined = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    combined.to_csv(out, index=False)
    return out
```

**Thread-safety:** `Backtester385` is instantiated fresh per call. No shared mutable state. Safe for Optuna parallel trials.

**Date filter — `_filter_date_range(df, start, end)`:**

Parquets use a `timestamp` column (Unix ms int) or a DatetimeIndex. Check both:

```python
def _filter_date_range(df, start, end):
    if "timestamp" in df.columns:
        s = pd.Timestamp(start, tz="UTC")
        e = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
        mask = (pd.to_datetime(df["timestamp"], unit="ms", utc=True) >= s) & \
               (pd.to_datetime(df["timestamp"], unit="ms", utc=True) < e)
        return df[mask].reset_index(drop=True)
    elif isinstance(df.index, pd.DatetimeIndex):
        s = pd.Timestamp(start, tz="UTC")
        e = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
        return df[(df.index >= s) & (df.index < e)].reset_index(drop=True)
    else:
        raise RuntimeError("Parquet has no recognizable timestamp column or DatetimeIndex")
```

**Bar index alignment note:** `entry_bar` / `exit_bar` are 0-based indices into the date-filtered slice
that was passed to `Backtester385.run()`. The B3 Enricher must use the SAME filtered slice when
calling `compute_signals()` for enrichment. B1 does not solve this — it is B3's responsibility.

---

### 5. `strategy_document` (property) -> Path

```python
@property
def strategy_document(self) -> Path:
    """Path to Four Pillars strategy markdown document."""
    doc = _ROOT / "docs" / "FOUR-PILLARS-STRATEGY-UML.md"
    if not doc.exists():
        raise FileNotFoundError(f"Strategy document not found: {doc}")
    return doc
```

`docs/FOUR-PILLARS-STRATEGY-UML.md` — confirmed to exist. Used by Panel 8 LLM Interpretive Layer.

---

## Constants

```python
_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = _ROOT / "data" / "cache"
RESULTS_DIR = _ROOT / "results"

DEFAULT_SIGNAL_PARAMS = {
    "atr_length": 14,
    "stoch_k1": 9,   "stoch_k2": 14, "stoch_k3": 40, "stoch_k4": 60,
    "stoch_d_smooth": 10,
    "cloud2_fast": 5,  "cloud2_slow": 12,
    "cloud3_fast": 34, "cloud3_slow": 50,
    "cloud4_fast": 72, "cloud4_slow": 89,
    "cross_level": 25, "zone_level": 30, "stage_lookback": 10,
    "allow_b_trades": True, "allow_c_trades": True,
    "b_open_fresh": True, "cloud2_reentry": True,
    "reentry_lookback": 10, "use_60d": False,
}

DEFAULT_BT_PARAMS = {
    "sl_mult": 2.0, "tp_mult": None,
    "be_trigger_atr": 0.0, "be_lock_atr": 0.0,
    "sigma_floor_atr": 0.5, "checkpoint_interval": 5,
    "max_scaleouts": 2, "max_positions": 4, "cooldown": 3,
    "notional": 5000.0, "commission_rate": 0.0008,
    "maker_rate": 0.0002, "rebate_pct": 0.70,
    "settlement_hour_utc": 17, "initial_equity": 10000.0,
    "enable_adds": True, "enable_reentry": True,
    "cancel_bars": 3, "reentry_window": 5, "max_avwap_age": 50,
}
```

---

## Imports Required

```python
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from strategies.base_v2 import StrategyPlugin
from signals.four_pillars_v383_v2 import compute_signals_v383
from engine.backtester_v385 import Backtester385
```

No direct import of `engine/position_v384.py` needed — `Backtester385.run()` returns `trades_df`
already as a DataFrame.

---

## Mandatory Checks Before Delivering

1. `py_compile` must pass — run immediately after writing
2. All 5 abstract methods implemented — no `NotImplementedError` raised
3. No imports from `strategies.base` (v1) — only `strategies.base_v2`
4. No import of old signal files (`four_pillars_v383.py`, `state_machine_v382.py`)
5. `parameter_space()` returns dict, not None — even if empty
6. `trade_schema()` includes `symbol` key
7. `strategy_document` raises `FileNotFoundError` if doc missing, not returns None

---

## Verification Tests

Run in `PROJECTS/four-pillars-backtester/` working directory.

```bash
# 1. Syntax check
python -c "import py_compile; py_compile.compile('strategies/four_pillars.py', doraise=True); print('SYNTAX OK')"

# 2. Interface smoke test (no parquet needed)
python -c "
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
ps = fp.parameter_space()
assert isinstance(ps, dict) and 'sl_mult' in ps, 'parameter_space fail'
ts = fp.trade_schema()
for col in ['entry_bar', 'exit_bar', 'pnl', 'commission', 'direction', 'symbol']:
    assert col in ts, f'trade_schema missing: {col}'
doc = fp.strategy_document
assert doc.exists(), f'strategy_document missing: {doc}'
print('INTERFACE: PASS')
"

# 3. compute_signals smoke test (synthetic data, no parquet needed)
python -c "
import pandas as pd, numpy as np
from strategies.four_pillars import FourPillarsPlugin
fp = FourPillarsPlugin()
n = 300
dummy = pd.DataFrame({
    'open':   np.random.rand(n) * 100 + 50,
    'high':   np.random.rand(n) * 5  + 103,
    'low':    np.random.rand(n) * 5  + 45,
    'close':  np.random.rand(n) * 100 + 50,
    'volume': np.random.rand(n) * 1e6,
})
out = fp.compute_signals(dummy)
required_sigs = ['long_a', 'short_a', 'stoch_9', 'stoch_60', 'atr', 'cloud3_bull']
for col in required_sigs:
    assert col in out.columns, f'compute_signals missing: {col}'
assert len(out) == n, 'compute_signals changed row count'
print('COMPUTE_SIGNALS: PASS')
"

# 4. run_backtest integration test (requires real parquet)
# Change BTCUSDT to any coin you have in data/cache/
python -c "
from strategies.four_pillars import FourPillarsPlugin
import pandas as pd
fp = FourPillarsPlugin()
params = dict(fp.DEFAULT_BT_PARAMS, sl_mult=2.0)
try:
    csv = fp.run_backtest(params, '2025-01-01', '2025-03-01', ['BTCUSDT'])
    df = pd.read_csv(csv)
    for col in ['entry_bar', 'exit_bar', 'pnl', 'commission', 'direction', 'symbol']:
        assert col in df.columns, f'CSV missing: {col}'
    print(f'RUN_BACKTEST: PASS — {len(df)} trades, CSV: {csv}')
except FileNotFoundError as e:
    print(f'PARQUET MISSING (expected if no data): {e}')
"
```

---

## What B1 Does NOT Include

- No Dash code — B6+
- No enricher snapshot logic — B3 (`vince/enricher.py`)
- No API layer — B2 (`vince/api.py`, `vince/types.py`)
- No vince/ directory files of any kind
- No PostgreSQL writes
- No Optuna sweep calls
- No RL components
- No LLM integration
- No test file — test commands above are inline smoke tests, not a test suite

---

## Build Order Context

```
B1  strategies/four_pillars.py         ← THIS SPEC
B2  vince/api.py + vince/types.py
B3  vince/enricher.py
B4  vince/pages/pnl_reversal.py        (PRIORITY)
B5  vince/query_engine.py
B6  vince/app.py + vince/layout.py     (Dash skill mandatory from here)
B7  Panels 1, 3, 4, 5
B8  vince/discovery.py
B9  vince/optimizer.py
B10 Panels 6, 7, 8
```
