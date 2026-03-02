# B2 Research Audit — API Layer + Dataclasses
**Date:** 2026-02-28
**Scope:** Research audit of `vince/types.py` + `vince/api.py` — NOT a build plan yet

---

## Context

B2 is the second block in the Vince v2 build sequence. It creates:
- `PROJECTS/four-pillars-backtester/vince/types.py` — all dataclasses
- `PROJECTS/four-pillars-backtester/vince/api.py` — clean Python API functions (no Dash imports)

The `vince/` directory does not exist yet in the backtester. B1 (FourPillarsPlugin in `strategies/four_pillars.py`) is also not built. B2 depends on B1 for full implementation.

---

## Skills Required

| Skill | Why |
|-------|-----|
| **Python skill** (`/python`) | MANDATORY hard rule — any .py file triggers it |
| **Dash skill** (`/dash`) | MANDATORY hard rule — triggers on "any file in vince/ directory" |

Note: `vince/types.py` and `vince/api.py` contain zero Dash imports, but the hard rule in MEMORY.md triggers on directory membership. Load both before writing any code.

---

## What Exists (Reuse)

| File | Relevant content |
|------|-----------------|
| `strategies/base_v2.py` | `StrategyPlugin` ABC — the plugin interface B2 api.py calls |
| `engine/position_v384.py` | `Trade384` dataclass — maps to required trade CSV columns |
| `engine/backtester_v384.py` | `Backtester384.run()` — what `run_backtest()` will wrap |
| `signals/four_pillars.py` | `compute_signals(df, params)` — what the enricher calls |
| `engine/commission.py` | `CommissionModel` — commission math used in scoring |
| `data/db.py` | PostgreSQL connection — used by `save_session()` |

### What does NOT exist yet
- `vince/` directory (entire folder)
- `vince/__init__.py`
- `vince/types.py`
- `vince/api.py`
- `vince/enricher.py`
- `vince/query_engine.py`
- B1: `strategies/four_pillars.py` (the FourPillarsPlugin)

---

## Scope of B2 — Precise Boundary

B2 should deliver:
1. `vince/__init__.py` — empty, makes it a package
2. `vince/types.py` — all dataclasses (imports: stdlib + pandas only)
3. `vince/api.py` — function signatures + stub bodies (`raise NotImplementedError`)

B2 does NOT implement enricher logic, query logic, or optimizer logic — those are later build blocks. The stubs let B6 (Dashboard) import `vince.api` without errors.

---

## API Functions Defined in Concept Doc

```python
# vince/api.py — functions listed in VINCE-V2-CONCEPT-v2.md
def run_enricher(symbols: list, params: dict) -> EnrichedTradeSet: ...
def query_constellation(filters: ConstellationFilter) -> MetricTable: ...
def get_coin_scorecard(symbol: str) -> CoinScorecardResult: ...
def get_panel2_data(symbol: str, timeframe: str) -> PnLReversalResult: ...
def run_optimizer(config: OptimizerConfig) -> OptimizerResult: ...
def save_session(session: SessionRecord) -> None: ...
def get_session_history() -> list: ...
```

---

## Bottlenecks Identified

### B1: Missing plugin parameter in api.py
The concept doc lists `run_enricher(symbols, params)` but the enricher needs to call `plugin.compute_signals()`. There is no `plugin` argument in the signature. Every API function that touches enriched data needs to know which plugin is active.

**Two options:**
- A: Pass `plugin: StrategyPlugin` on every API call
- B: Module-level `active_plugin` — `api.set_active_plugin(plugin)` called once at app startup

Option B matches the Dash app pattern (plugin selected at startup, stored in `dcc.Store`). But it creates hidden global state. Option A is explicit but verbose.

**This must be decided before api.py can be written.**

### B2: EnrichedTrade — dataclass vs DataFrame
The concept doc shows `EnrichedTrade` as a dataclass, but indicator columns are plugin-specific and dynamic. Storing 400 coins × ~1000 trades × ~50 indicator columns as individual Python dataclass instances is slow.

**Three options:**
- A: `EnrichedTrade` dataclass with `snapshots: dict` for dynamic columns
- B: `EnrichedTradeSet` is a single pandas DataFrame with fixed base columns + dynamic indicator columns
- C: `EnrichedTrade` is a namedtuple/TypedDict per row, `EnrichedTradeSet` wraps a DataFrame

Option B (DataFrame-centric) is fastest for the query and analysis operations. Option A is the most "typed" but slowest at scale.

**This must be decided before types.py can be written.**

### B3: ConstellationFilter — plugin-agnostic design
The constellation query filter needs to work for ANY plugin. But the query dimensions are plugin-specific (k1_range, grade, cloud_state etc.). If `ConstellationFilter` has hardcoded Four Pillars fields, it breaks the plugin abstraction.

**Two options:**
- A: `ConstellationFilter` has `column_filters: dict[str, Any]` — keys are column names from `compute_signals()` output
- B: `ConstellationFilter` has `base_filters` (direction, outcome — universal) + `plugin_filters: dict`

Option A is simpler and fully generic. The column names act as the contract.

### B4: Bar index alignment (CRITICAL — flagged in spec)
`VINCE-PLUGIN-INTERFACE-SPEC-v1.md` Section 7 explicitly calls this out:

> "Trade384 currently stores entry/exit as bar offsets within a single symbol's run, not as positional indices into the global OHLCV parquet. The wrapper must translate these to absolute positional indices."

The current `Backtester384.run(df)` takes an already-filtered DataFrame for a single symbol. The `entry_bar` field in `Trade384` is a position into THAT DataFrame, not into the full parquet. If the Enricher loads the full parquet and tries to look up `entry_bar=5`, it gets the wrong bar.

This is a B1 problem (FourPillarsPlugin must solve it), but B2's `run_enricher()` must document this requirement clearly.

### B5: `run_enricher` signature is incomplete
`run_enricher(symbols: list, params: dict)` — params for what? The enricher doesn't run the backtest itself; it consumes the trade CSV that `plugin.run_backtest()` already produced. The full call needs:

```python
def run_enricher(
    trade_csv: Path,       # output from plugin.run_backtest()
    symbols: list,         # to load parquet data
    start: str,
    end: str,
    plugin: StrategyPlugin,
) -> EnrichedTradeSet
```

The concept doc signature is a stub that needs fleshing out.

### B6: MFE bar definition ambiguity
For PnL Reversal Analysis, the Enricher walks bars from entry to exit to find the MFE bar. For LONG: MFE = bar with highest `high`. If there are multiple bars with equal max high, which is chosen? First occurrence or last? This affects exit_ohlc capture for intra-candle classification in Panel 4.

Must be specified before enricher.py is built (not B2, but B2's `EnrichedTrade` dataclass must include the right fields).

### B7: SessionRecord — what is a "session"?
The concept doc says `save_session(session: SessionRecord)`. But when does a session start/end? Options:
- A: One session = one enricher run (one call to run_enricher)
- B: One session = a user's research sitting (multiple queries, saved as a named session)
- C: One session = one Mode 2/3 sweep result

This determines what fields `SessionRecord` needs. The concept doc says Panel 7 shows "all sessions, annotatable, filters restorable" — implying sessions save filter state for restoration.

---

## Questions Requiring User Decisions (Block the Build)

1. **Active plugin — module-level global or per-call argument?**
   (Affects every api.py function signature)

2. **EnrichedTradeSet — dataclass list or DataFrame?**
   (Affects types.py design and every downstream analysis function)

3. **ConstellationFilter — typed fields or `column_filters: dict`?**
   (Affects types.py + query_engine.py interface)

4. **What does a SessionRecord contain?**
   What does "filters restorable" mean — does it store the full ConstellationFilter, result, metadata?

5. **run_enricher signature** — confirm the corrected signature above or define differently?

---

## Improvements vs Concept Doc

| Area | Current concept | Improvement |
|------|----------------|-------------|
| `run_enricher` signature | `(symbols, params)` — incomplete | `(trade_csv, symbols, start, end, plugin)` — explicit, no hidden state |
| `EnrichedTradeSet` | implied list of dataclasses | DataFrame + metadata dataclass — 50-100x faster for 400-coin analysis |
| `ConstellationFilter` | implied hardcoded fields | `column_filters: dict[str, Any]` — plugin-agnostic |
| `SessionRecord` | undefined fields | Needs: uuid, timestamp, plugin_name, symbols, date_range, filters, result_summary |
| `MetricTable` | implied fields | Should carry provenance: session_id, symbols, date_range, plugin, computation_timestamp |
| `get_panel2_data` signature | `(symbol, timeframe)` | timeframe param is unused by Vince (indicator-only, no price charts) — should be removed or clarified |
| api.py plugin awareness | not addressed | Two patterns available — choose one before build |

---

## Files to Create in B2

```
four-pillars-backtester/
  vince/
    __init__.py          (new — empty package marker)
    types.py             (new — all dataclasses, stdlib+pandas only)
    api.py               (new — function stubs, imports types.py + strategies/base_v2.py)
```

---

## Verification After B2

- `py_compile` on all 3 files (hard rule)
- `from vince.types import EnrichedTrade, MetricTable, ConstellationFilter, SessionRecord` — no import errors
- `from vince.api import run_enricher, query_constellation` — no import errors
- `from vince.api import get_coin_scorecard` — no import errors
- All api.py functions raise `NotImplementedError` (confirmed stubs, not silent pass)
- No Dash, no engine imports in types.py (isolation guaranteed)
