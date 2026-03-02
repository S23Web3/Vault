# B2 Research Audit — API Layer + Dataclasses (vince/types.py + vince/api.py)
**Date:** 2026-02-28
**Type:** Research audit — no code built
**Plan files:** `06-CLAUDE-LOGS/plans/2026-02-28-b2-api-types-research-audit.md`

---

## What Was Done

Full research audit of B2 before build begins. Goal: identify all design decisions, bottlenecks, and open questions so B2 can be written without guessing.

Files audited:
- `PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md` (concept doc, approved)
- `PROJECTS/four-pillars-backtester/docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` (plugin spec)
- `PROJECTS/four-pillars-backtester/strategies/base_v2.py` (StrategyPlugin ABC)
- `PROJECTS/four-pillars-backtester/engine/position_v384.py` (Trade384 dataclass)
- `PROJECTS/four-pillars-backtester/engine/backtester_v384.py` (Backtester384)
- `PROJECTS/four-pillars-backtester/signals/four_pillars.py` (compute_signals)

---

## Key Finding: vince/ Directory Does Not Exist

Neither `vince/` nor any of B2's target files exist. B1 (FourPillarsPlugin) is also unbuilt. B2 depends on B1 for full implementation — B2 delivers stubs only.

---

## Skills Required (Both Mandatory)

- `/python` — hard rule for any .py file
- `/dash` — hard rule triggers on "any file in vince/ directory" per MEMORY.md

---

## 7 Bottlenecks Identified

| # | Issue | Blocks |
|---|-------|--------|
| B1 | Missing `plugin` param in api.py concept doc signatures | All api.py function signatures |
| B2 | EnrichedTrade: dataclass vs DataFrame | types.py |
| B3 | ConstellationFilter: typed fields vs generic dict | types.py |
| B4 | Bar index alignment (flagged in spec Section 7) | enricher.py (B3 build) |
| B5 | run_enricher signature incomplete in concept doc | api.py |
| B6 | MFE bar: first vs last equal max high | EnrichedTrade fields |
| B7 | SessionRecord scope undefined | types.py |

---

## Design Verdicts (Researched, Not Just Listed)

### 1. Active plugin — per-call argument (VERDICT)
Concept doc signature `run_enricher(symbols, params)` has no plugin arg. Must add.
- Per-call: thread-safe (Optuna parallelism), testable, agent-callable (concept doc requires "same API for GUI and future agent")
- Module-level global: breaks thread safety, hard to test, violates agent-callable requirement
- **Verdict: per-call `plugin: StrategyPlugin` on every function**

### 2. EnrichedTradeSet — DataFrame-centric (VERDICT)
400 coins × 1000 trades × 50 indicator cols = 400,000 rows.
- DataFrame: vectorized groupby/filter/percentile — sub-second. Panel 2 (highest priority) is 3-4 pandas calls.
- Dataclass list: list comprehensions + numpy conversion per query — minutes for Mode 2 permutation tests.
- **Verdict: `EnrichedTradeSet.trades: pd.DataFrame` + metadata fields. No `EnrichedTrade` row dataclass.**

### 3. ConstellationFilter — typed base + column_filters dict (VERDICT)
Plugin-specific indicator fields (k1_9, grade, cloud3_bull) are dynamic — cannot hardcode them.
- Universal fields (direction, outcome, min_mfe_atr, saw_green) are typed — always present from trade_schema()
- Indicator-specific fields go in `column_filters: dict[str, Any]` — column names from compute_signals() are the contract
- **Verdict: typed base + `column_filters: dict`. JSON-serializable for dcc.Store.**

### 4. SessionRecord — named research session (VERDICT)
Concept doc Panel 7: "annotatable, filters restorable."
- Named session: user names it (auto-default "YYYY-MM-DD HH:MM"), multiple queries belong to one session, filter state restorable
- Per-enricher-run: Panel 7 becomes a raw log, "annotatable" doesn't fit
- **Verdict: named research session. Fields: session_id (uuid4), name, created_at (UTC timestamp — mandatory), updated_at, plugin_name, symbols, date_range, notes, last_filter (dict)**

---

## Corrected run_enricher Signature

Concept doc had `run_enricher(symbols, params)` — params is undefined and plugin is missing.

Correct signature:
```python
def run_enricher(
    trade_csv: Path,
    symbols: list,
    start: str,
    end: str,
    plugin: StrategyPlugin,
) -> EnrichedTradeSet
```

---

## Improvements vs Concept Doc

| Area | Concept doc | Corrected |
|------|------------|-----------|
| run_enricher signature | `(symbols, params)` — incomplete | `(trade_csv, symbols, start, end, plugin)` |
| EnrichedTradeSet | implied dataclass list | DataFrame + metadata — 50-100x faster |
| ConstellationFilter | implied hardcoded fields | typed base + `column_filters: dict` |
| SessionRecord | undefined | uuid, timestamps, plugin_name, symbols, date_range, notes, last_filter |
| MetricTable | implied fields | add provenance: session_id, symbols, date_range, plugin, computation_timestamp |
| get_panel2_data | `(symbol, timeframe)` | timeframe unused — remove or clarify |

---

## B2 Scope (3 Files)

```
four-pillars-backtester/vince/__init__.py   (new — empty)
four-pillars-backtester/vince/types.py      (new — dataclasses, stdlib+pandas only)
four-pillars-backtester/vince/api.py        (new — stubs raise NotImplementedError)
```

---

## Next Steps

1. B1 must be built first (FourPillarsPlugin) — bar index alignment must be solved there
2. B2 can then be built: `vince/__init__.py`, `vince/types.py`, `vince/api.py` (stubs)
3. Load both `/python` and `/dash` skills before writing any code
4. After B2: B3 (enricher.py) — separate scoping session planned
