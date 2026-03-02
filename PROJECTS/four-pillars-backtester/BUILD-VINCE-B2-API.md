# B2 — API Layer + Dataclasses Build Spec

**Build ID:** VINCE-B2
**Status:** READY TO BUILD (after B1 passes compliance)
**Date:** 2026-02-28
**Source research:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-28-b2-api-types-research.md`

---

## What B2 Is

B2 creates the shared dataclasses and API layer that sits between the Dash pages
and the analysis engine. Pages NEVER call the enricher or plugin directly — all
access goes through vince/api.py. B2 is pure Python, no Dash callbacks.

---

## Skills to Load Before Building

- `/python` — MANDATORY per MEMORY.md for any .py file
- `/dash` — MANDATORY per CLAUDE.md for any file in vince/ directory

---

## Files

| # | File | Lines (est.) | Action |
|---|------|-------------|--------|
| 1 | `vince/__init__.py` | 1 | Create (empty package marker) |
| 2 | `vince/types.py` | ~120 | Create — all dataclasses |
| 3 | `vince/api.py` | ~100 | Create — API functions (stubs raise NotImplementedError) |
| 4 | `tests/test_b2_api.py` | ~40 | Create — smoke tests |

---

## Design Verdicts (locked by research session 2026-02-28)

### Verdict 1: Plugin as per-call argument
Every api.py function takes `plugin: StrategyPlugin` as an argument.
NOT a module-level global. Reason: thread-safe for Optuna parallelism,
testable, agent-callable (concept doc requires same API for GUI + future agent).

### Verdict 2: EnrichedTradeSet as DataFrame (NOT dataclass list)
`EnrichedTradeSet.trades` is a `pd.DataFrame`, not a list of `EnrichedTrade` objects.
400 coins x 1000 trades x 50 indicator cols = 400,000 rows.
DataFrame: vectorised groupby/filter/percentile — sub-second.
Dataclass list: list comprehensions + numpy conversion — minutes for permutation tests.

### Verdict 3: ConstellationFilter = typed base + column_filters dict
Universal fields (direction, outcome, min_mfe_atr, saw_green) are typed dataclass fields.
Plugin-specific indicator fields go in `column_filters: dict[str, Any]`.
Column names from `plugin.compute_signals()` output are the contract.
This makes ConstellationFilter plugin-agnostic and JSON-serializable for dcc.Store.

### Verdict 4: SessionRecord = named research session
Fields: session_id (uuid4 hex), name (str, user-editable), created_at (ISO 8601 UTC),
updated_at (ISO 8601 UTC), plugin_name (str), symbols (list[str]),
date_range (tuple[str, str]), notes (str), last_filter (dict | None).
NOT a per-enricher-run log. A named session groups multiple queries.

---

## Corrected run_enricher Signature

Concept doc had `run_enricher(symbols, params)` — params is undefined, plugin missing.
Correct:
```python
def run_enricher(
    trade_csv: Path,
    symbols: list,
    start: str,
    end: str,
    plugin: StrategyPlugin,
) -> EnrichedTradeSet:
```

---

## Types (vince/types.py)

All `@dataclass`. Stdlib + pandas only. No Dash imports.

```
IndicatorSnapshot
  k1: float, k2: float, k3: float, k4: float
  cloud_bull: bool
  bbw: float
  bar_idx: int

OHLCRow
  open: float, high: float, low: float, close: float

EnrichedTradeSet
  trades: pd.DataFrame        # all trades with snapshot cols attached
  session_id: str
  plugin_name: str
  symbols: list[str]
  date_range: tuple[str, str]
  enriched_at: str            # ISO 8601 UTC timestamp

MetricRow
  label: str
  matched: float
  complement: float
  delta: float

ConstellationFilter
  direction: str | None       # "LONG", "SHORT", None
  outcome: str | None         # "WIN", "LOSS", None
  min_mfe_atr: float | None
  saw_green: bool | None
  column_filters: dict        # {"k1_9_at_entry": (20, 40), "cloud3_bull_at_entry": True}

ConstellationResult
  matched_count: int
  complement_count: int
  metrics: list[MetricRow]
  permutation_p_value: float

SessionRecord
  session_id: str
  name: str
  created_at: str
  updated_at: str
  plugin_name: str
  symbols: list[str]
  date_range: tuple[str, str]
  notes: str
  last_filter: dict | None
```

---

## API Layer (vince/api.py)

Pure functions. No Dash imports. No global state.

```python
def run_enricher(trade_csv, symbols, start, end, plugin) -> EnrichedTradeSet:
    raise NotImplementedError("Implemented in B3")

def query_constellation(trade_set, f: ConstellationFilter) -> ConstellationResult:
    raise NotImplementedError("Implemented in B5")

def compute_mfe_histogram(trade_set, bins=None) -> pd.DataFrame:
    raise NotImplementedError("Implemented in B4")

def compute_tp_sweep(trade_set, tp_range=(0.5, 5.0), steps=19) -> pd.DataFrame:
    raise NotImplementedError("Implemented in B4")

def get_session_record(session_id: str) -> SessionRecord:
    raise NotImplementedError

def save_session_record(record: SessionRecord) -> None:
    raise NotImplementedError
```

---

## Imports Required

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import pandas as pd
from strategies.base_v2 import StrategyPlugin
```

---

## Verification

```bash
python -c "import py_compile; py_compile.compile('vince/__init__.py', doraise=True); print('OK')"
python -c "import py_compile; py_compile.compile('vince/types.py', doraise=True); print('OK')"
python -c "import py_compile; py_compile.compile('vince/api.py', doraise=True); print('OK')"
python tests/test_b2_api.py
```

Test cases:
1. All dataclasses instantiate without error
2. `ConstellationFilter()` with no args — no TypeError
3. `EnrichedTradeSet.trades` field accepts a pd.DataFrame
4. All api.py functions raise NotImplementedError (stubs)
5. py_compile passes all 3 files

---

## What B2 Does NOT Include

- No enricher logic (B3)
- No Optuna calls (B9)
- No Dash callbacks or layout (B6)
- No PostgreSQL writes
- No filled implementations — api.py is stubs only until B3-B5 are built
