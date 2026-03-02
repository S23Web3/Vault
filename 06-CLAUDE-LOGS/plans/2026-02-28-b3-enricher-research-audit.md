# B3 Enricher — Research Audit & Scope Plan
**Date:** 2026-02-28
**Status:** RESEARCH / AUDIT — not yet scoped for build

---

## Context

The user referenced `BUILD-VINCE-B3-ENRICHER.md` which does not yet exist. B3 is the third
block of the Vince v2 build sequence. Its job: take a trade CSV produced by any
`StrategyPlugin.run_backtest()` call, load the OHLCV + indicator data for each traded symbol,
look up indicator state at three critical bars per trade (entry, MFE, exit), and attach those
values as snapshot columns. `diskcache` is used so `compute_signals()` runs once per symbol,
not once per trade.

This plan is a full audit: what needs to exist, what's already built, what's broken or missing,
what open questions block the build, and what improvements are visible.

---

## Skills Required

| Skill | Reason |
|-------|--------|
| `four-pillars` | Enricher wraps the Four Pillars signal pipeline |
| Python (MANDATORY per MEMORY.md) | Writing `enricher.py`, FourPillarsPlugin, tests |
| No Dash skill needed | B3 is a pure backend module — no UI |

---

## What Already Exists (Confirmed by Code Read)

| Component | File | Status |
|-----------|------|--------|
| StrategyPlugin ABC | `strategies/base_v2.py` | DONE — stub only, no implementation |
| Plugin interface spec | `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` | DONE — full contract |
| Concept doc v2 | `docs/VINCE-V2-CONCEPT-v2.md` | DONE — approved for build |
| Signal pipeline (non-Numba) | `signals/four_pillars.py` | EXISTS — wrong signature for plugin |
| Signal pipeline (Numba) | `signals/four_pillars_v383_v2.py` | EXISTS — wrong signature for plugin |
| Trade record | `engine/position_v384.py::Trade384` | EXISTS — missing `mfe_bar` field |
| Backtester | `engine/backtester_v384.py` | EXISTS — needs run_backtest() wrapper |
| OHLCV parquet cache | `data/cache/*.parquet` | EXISTS — 400+ coins, 1m + 5m |
| FourPillarsPlugin (BingX) | `PROJECTS/bingx-connector/plugins/four_pillars_v384.py` | EXISTS — different interface, reference only |
| diskcache | nowhere | NOT INSTALLED |
| `vince/` directory | nowhere | NOT CREATED |
| `enricher.py` | nowhere | NOT CREATED |
| `strategies/four_pillars_plugin.py` | nowhere | NOT CREATED |

---

## Scope of Work — Files to Build

### 1. Modify `engine/position_v384.py`
**Add `mfe_bar: int` to `Trade384` dataclass** (see Bottleneck 1 below).
Track which bar MFE occurred in `PositionSlot384.update_bar()`.
Propagate to `close_at()` and `do_scale_out()`.

### 2. `strategies/four_pillars_plugin.py` — FourPillarsPlugin wrapper
Implements `StrategyPlugin` ABC from `strategies/base_v2.py`.

| Method | What it does |
|--------|-------------|
| `compute_signals(ohlcv_df)` | Renames OHLCV cols to pipeline convention, calls existing `compute_signals()`, renames output cols to spec convention (`stoch_9` → `k1_9`, etc.) |
| `parameter_space()` | Returns dict extracted from `engine/backtester_v384.py::DEFAULT_PARAMS` |
| `trade_schema()` | Maps `Trade384` dataclass fields to schema dict, including new `mfe_bar` |
| `run_backtest(params, start, end, symbols)` | Wraps `Backtester384.run()`, filters date range, applies bar index offset to produce absolute RangeIndex positions |
| `strategy_document` | Returns `Path` to the strategy markdown (decision needed — see Q5) |

### 3. `vince/__init__.py` and `vince/enricher.py` — Core Enricher

```
vince/
  __init__.py
  enricher.py        ← B3 target
  cache_config.py    ← diskcache setup
```

`Enricher` class responsibilities:
- Accepts a `StrategyPlugin` instance and a trade CSV path
- For each unique (symbol, params_hash) pair:
  - Check `diskcache.FanoutCache` for pre-computed indicator DataFrame
  - On cache miss: load parquet, call `plugin.compute_signals()`, store in cache
- For each trade row:
  - Look up `entry_bar`, `mfe_bar`, `exit_bar` in indicator DataFrame
  - Attach `{col}_at_entry`, `{col}_at_mfe`, `{col}_at_exit` columns
  - Attach `entry_ohlc`, `mfe_ohlc`, `exit_ohlc` (format TBD — see Q4)
- Returns enriched DataFrame

### 4. `tests/test_enricher.py` and `tests/test_four_pillars_plugin.py`
- Plugin compliance checklist (from spec Section 6)
- Enricher round-trip: synthetic OHLCV → backtest → enrich → verify column presence
- Cache hit/miss behaviour
- Thread-safety smoke test (2 concurrent enrich calls, same symbol)

---

## CRITICAL BLOCKERS — APIs and Missing Pieces

### BLOCKER 1: `mfe_bar` not in Trade384 (Highest Priority)
**File:** `engine/position_v384.py`

`Trade384` stores `mfe` (dollar float) and `mae` (dollar float) but NOT `mfe_bar` (which
bar the MFE occurred on). The Enricher needs `mfe_bar` to attach `_at_mfe` snapshot columns.

Without this, `k1_9_at_mfe`, `cloud3_bull_at_mfe`, `entry_ohlc` etc. are all impossible.

**Fix required:** Add `mfe_bar: int` to `Trade384`, track it in `update_bar()`.

```python
# In Trade384 dataclass — add:
mfe_bar: int  # bar index where MFE was achieved

# In PositionSlot384.__init__:
self.mfe_bar: int = entry_bar

# In update_bar() after MFE update:
if ub > self.mfe:
    self.mfe = ub
    self.mfe_bar = bar_index   # ← track it here
```

**Impact:** Breaking change to Trade384 schema. Any code that creates Trade384 instances must
add `mfe_bar=` argument. Affects `close_at()` and `do_scale_out()`.

---

### BLOCKER 2: `compute_signals()` signature mismatch
**File:** `signals/four_pillars.py`

Current signature: `compute_signals(df, params=None)` — takes 2 args.
Plugin interface requires: `compute_signals(self, ohlcv_df)` — params baked into instance.

The FourPillarsPlugin must store params in `__init__` and pass them internally.

Also: current pipeline expects columns `base_vol`, `quote_vol` (and uses `timestamp` as a
data column not the index). The OHLCV contract requires `volume` (float64) and RangeIndex.

**Fix required:** FourPillarsPlugin.compute_signals() must:
1. Rename `volume` → `base_vol` before calling `compute_signals()`
2. Ensure index is RangeIndex (not DatetimeIndex)
3. Pass `self._params` as the params arg

---

### BLOCKER 3: Indicator column naming convention mismatch
**Files:** `signals/four_pillars.py`, `signals/stochastics.py`

Current output column names:
```
stoch_9, stoch_14, stoch_40, stoch_60, stoch_60_d,
cloud3_bull, price_pos, price_cross_above_cloud2, price_cross_below_cloud2, atr
```

Spec (Section 5) requires:
```
k1_9, k2_14, k3_40, k4_60,  cloud2_bull, cloud3_bull, bbw, atr
```

**Decision needed (Q2):** Rename in the plugin wrapper (safest — no signal pipeline breakage)
or update `signals/stochastics.py` and `signals/clouds.py` directly (cleaner long-term but
risks breaking the existing backtester and BingX connector).

**Also:** `bbw` (Bollinger Band Width) is listed in the spec's example columns but is NOT
computed by `compute_signals()` currently. It exists in `signals/bbw.py` separately. Decision
needed: include BBW in the enriched snapshot or exclude it from B3?

---

### BLOCKER 4: `diskcache` not installed
**Impact:** Cannot build Enricher at all until installed.

```
pip install diskcache
```

**Design decision (Q3):** `diskcache.Cache` vs `diskcache.FanoutCache`

| Option | Pros | Cons |
|--------|------|------|
| `Cache` | Simple API, single directory | Not optimal for concurrent writes (Optuna parallelism) |
| `FanoutCache` | Sharded = better concurrency | Slightly more complex setup |

**Recommendation:** `FanoutCache` with 8 shards — Optuna parallelism makes concurrent
cache writes likely. Cache directory: `data/vince_cache/` (separate from `data/cache/`).

**Cache key design:**
```python
import hashlib, json
params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
key = f"{symbol}_{timeframe}_{params_hash}"
```

Cache stores: pre-computed indicator DataFrame as pickled object or parquet bytes.

---

### BLOCKER 5: Bar index offset — run_backtest() alignment
**File:** `engine/backtester_v384.py`

The current backtester runs on a date-filtered slice of the parquet. If the parquet has 50,000
bars and the date range starts at bar 10,000, the backtester's `entry_bar=0` maps to absolute
parquet index 10,000.

The Enricher uses `entry_bar` and `exit_bar` as absolute positional indices into the full
OHLCV DataFrame returned by `compute_signals()`. If the FourPillarsPlugin's `run_backtest()`
wrapper does not add the slice offset, every bar lookup will be wrong.

**Fix required:** FourPillarsPlugin.run_backtest() must:
1. Identify the parquet slice start (first bar on or after `start` date)
2. Add that offset to all `entry_bar`, `mfe_bar`, `exit_bar` values in the output CSV

---

### BLOCKER 6: OHLC tuple storage format undefined
**Spec says:** Attach `entry_ohlc`, `mfe_ohlc`, `exit_ohlc` as tuples `(open, high, low, close)`.

Tuples don't round-trip through CSV cleanly. Three options:

| Format | Pros | Cons |
|--------|------|------|
| JSON string: `"[1.1, 1.2, 1.0, 1.15]"` | One column, reversible | Requires parse on read |
| 4 separate columns: `entry_open`, `entry_high`, etc. | Native float, no parse | 12 extra columns |
| Pipe-delimited string: `"1.1\|1.2\|1.0\|1.15"` | Compact | Non-standard |

**Recommendation:** 4 separate columns. Dashboard queries will need individual OHLC values
anyway (e.g., Panel 4 Exit State Analysis checks if SL hit at intrabar high/low).

---

## Open Questions (Blocking or Design)

**Q1: mfe_bar tracking — can we modify position_v384.py?**
Adding `mfe_bar: int` to Trade384 is a breaking change. The backtester v3.8.4 is live in the
BingX connector (via `bingx-connector/plugins/four_pillars_v384.py`). Should we:
- (A) Modify position_v384.py directly and update all call sites
- (B) Create position_v385.py with the addition (cleaner version separation)
- (C) Have the Enricher find the MFE bar in a second pass over OHLCV (slower, avoids Trade384 change)

**Q2: Column renaming — plugin wrapper or signal pipeline?**
- (A) Rename in FourPillarsPlugin wrapper only (`stoch_9` → `k1_9` in output)
- (B) Rename in `signals/stochastics.py` + `signals/clouds.py` globally

Option A is safer (no backtester breakage). Option B is cleaner long-term.

**Q3: diskcache variant — Cache or FanoutCache?**
Recommendation is FanoutCache (see Blocker 4). Confirm?

**Q4: OHLC storage — tuple or 4 separate columns?**
Recommendation is 4 separate columns (see Blocker 6). Confirm?

**Q5: strategy_document — which file?**
The spec says `strategy_document` must be a `.md` file with entry rules, exit rules, indicator
list. Candidates:
- `docs/VINCE-V2-CONCEPT-v2.md` (concept, not strategy rules)
- `SPEC-C-VINCE-ML.md` (marked superseded)
- A new file: `docs/FOUR-PILLARS-STRATEGY-v384.md` (clean strategy document)

Recommendation: create `docs/FOUR-PILLARS-STRATEGY-v384.md` as a concise strategy doc.

**Q6: BBW in enriched snapshots?**
Bollinger Band Width is in the spec's indicator examples but not in the current signal pipeline.
- (A) Include BBW: adds it to `compute_signals()` for the plugin (modifies pipeline)
- (B) Exclude BBW from B3: add it later in B4/B5 when Panel analysis needs it

**Q7: Which signal pipeline version does the plugin use?**
- `signals/four_pillars.py` — standard Python, v3.8.4 compatible state machine
- `signals/four_pillars_v383_v2.py` — Numba JIT-compiled, faster but v3.8.3 state machine

For the Enricher, performance matters (400 symbols × compute_signals = significant work).
Recommendation: use Numba version but update it to v3.8.4 state machine, or use standard
version for correctness first, optimize later.

**Q8: Cache invalidation strategy**
When does the diskcache become stale?
- Parquet data is refreshed by the fetcher — do indicator caches need to be busted?
- Params change between backtests — cache key includes params_hash, so this is auto-handled
- Recommendation: add a parquet `mtime` check to the cache key

---

## Improvements Identified

### Improvement 1: Numba ATR in standard pipeline
`signals/four_pillars.py` has a pure-Python ATR loop (slow on 400 coins).
`signals/four_pillars_v383_v2.py` has `@njit(cache=True)` version.
The ATR kernel should be shared, not duplicated. Consolidate.

### Improvement 2: `compute_signals` return should expose raw stoch values, not just booleans
Currently the state machine outputs boolean signals (`long_a`, `short_b`, etc.). The enricher
needs raw indicator values at bars (`k1_9=42.3`, `cloud3_bull=True`, `atr=0.0023`).
The raw values ARE computed inside `compute_all_stochastics()` and `compute_clouds()` and stored
on the DataFrame — they just flow through. The FourPillarsPlugin rename layer maps them.
No structural change needed — just confirm the intermediate columns survive.

### Improvement 3: `trade_schema()` should include `mfe_bar` and `mae` metadata
The spec lists `mfe_atr` and `mae_atr` as optional columns. Trade384 has `mfe` and `mae`
in dollar terms. The plugin's `trade_schema()` should expose:
- `mfe_bar`: "int — bar index of maximum favorable excursion"
- `mfe_atr`: "float — MFE expressed in ATR units (mfe / entry_atr)"
- `mae_atr`: "float — MAE expressed in ATR units"

These enable Panel 2 (PnL Reversal Analysis) to show how far trades went before reversing.

### Improvement 4: FanoutCache size cap
Without a size limit, the diskcache can fill disk (400 coins × 5m + 1m = ~800 indicator DFs).
Add `size_limit=2 * 1024 ** 3` (2 GB cap) to FanoutCache init.

### Improvement 5: Enricher should be a context manager
```python
with Enricher(plugin=plugin, cache_dir="data/vince_cache") as enricher:
    df = enricher.enrich(trade_csv_path)
```
Ensures diskcache is closed cleanly (avoids file handle leaks on Windows).

### Improvement 6: Compliance test as a standalone CLI
The plugin compliance checklist (spec Section 6) should be runnable as:
```
python -m vince.compliance_check strategies.four_pillars_plugin.FourPillarsPlugin
```
This makes it easy to validate any future plugin without manual testing.

---

## Implementation Order (if approved)

1. Modify `engine/position_v384.py` — add `mfe_bar` (or create v385)
2. Write `strategies/four_pillars_plugin.py` — FourPillarsPlugin with all 5 methods
3. Write `tests/test_four_pillars_plugin.py` — compliance checklist
4. Install `diskcache`, write `vince/cache_config.py`
5. Write `vince/enricher.py` — Enricher class
6. Write `tests/test_enricher.py` — round-trip test

---

## Verification

```
# 1. Plugin compliance
python tests/test_four_pillars_plugin.py

# 2. Enricher round-trip (small dataset)
python tests/test_enricher.py --symbol BTCUSDT --start 2024-01-01 --end 2024-01-31

# 3. Check enriched CSV has all snapshot columns
python -c "
import pandas as pd
df = pd.read_csv('results/enriched_test.csv')
required = ['k1_9_at_entry', 'cloud3_bull_at_entry', 'atr_at_entry',
            'k1_9_at_mfe', 'cloud3_bull_at_mfe',
            'k1_9_at_exit', 'entry_open', 'entry_high', 'entry_low', 'entry_close']
missing = [c for c in required if c not in df.columns]
print('MISSING:', missing or 'NONE')
"

# 4. py_compile all new files (mandatory)
python -c "import py_compile; [py_compile.compile(f, doraise=True) for f in [
    'strategies/four_pillars_plugin.py',
    'vince/__init__.py',
    'vince/enricher.py',
    'vince/cache_config.py'
]]"
```

---

## Critical Paths Summary

```
OHLCV parquet
    └─ plugin.compute_signals(ohlcv_df)
           └─ diskcache (symbol + params_hash key)
                  └─ enricher.enrich(trade_csv, plugin)
                         ├─ for each trade: iloc[entry_bar] → _at_entry cols
                         ├─ for each trade: iloc[mfe_bar]   → _at_mfe cols   ← BLOCKED on Q1
                         └─ for each trade: iloc[exit_bar]  → _at_exit cols
                                └─ enriched_trades.csv (input to all 8 dashboard panels)
```

**The MFE bar question (Q1) is the single most important decision before the build starts.**
Everything else can be worked around. Without `mfe_bar`, the `_at_mfe` columns cannot exist
and Panel 4 (Exit State Analysis) and Panel 2 (PnL Reversal) lose their most valuable data.
