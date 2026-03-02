# MASTER BUILD — Vince Documentation Sync
# Agent-executable instruction set. No code. Documentation only.
# Date: 2026-02-28

---

## CONTEXT (read before doing anything)

The Vince v2 research dashboard project has had 5 research sessions today (2026-02-28).
Each session produced audit logs and plans but the documentation system is out of sync.
This build creates missing build docs, adds build status to UML files, and updates all
index/status/memory files to reflect the true current state.

**What exists — confirmed by vault sweep:**
- `BUILD-VINCE-B1-PLUGIN.md` — 469 lines, READY TO BUILD (exists, do not touch)
- `BUILD-VINCE-ML.md` — ARCHIVED (exists, do not touch)
- `docs/VINCE-V2-CONCEPT-v2.md` — 749 lines, APPROVED, locked for content changes
- `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — 440 lines, APPROVED
- `strategies/base_v2.py` — StrategyPlugin ABC, complete
- `vince/` directory — DOES NOT EXIST (zero code written)
- B2 research log: `06-CLAUDE-LOGS/2026-02-28-b2-api-types-research.md`
- B3 research plan: `06-CLAUDE-LOGS/plans/2026-02-28-b3-enricher-research-audit.md`
- B4 research log: `06-CLAUDE-LOGS/2026-02-28-vince-b4-scope-audit.md`
- B1 scope audit: `06-CLAUDE-LOGS/2026-02-28-vince-b1-scope-audit.md`

**Root path:** `C:\Users\User\Documents\Obsidian Vault`
**Backtester path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester`

---

## HARD RULES (from MEMORY.md — must follow)

- NEVER OVERWRITE FILES — check if file exists first. If yes, abort that step and report it.
- JOURNALS: EDIT ONLY, NEVER WRITE — use Edit tool (append) on existing files like INDEX.md, TOPIC files, PRODUCT-BACKLOG.md. NEVER use Write tool on existing files.
- FULL PATHS EVERYWHERE — every file reference must be the full Windows path.
- No code — this build is documentation only.
- MANDATORY timestamps — every log entry must include a timestamp.
- After every Write/Edit, read back the relevant section to verify it landed correctly.

---

## STEP 1 — Check which build docs already exist

Before creating any file, run Glob for:
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B*.md`

If BUILD-VINCE-B2-API.md, BUILD-VINCE-B3-ENRICHER.md, BUILD-VINCE-B4-PNL-REVERSAL.md,
BUILD-VINCE-B5-QUERY-ENGINE.md, or BUILD-VINCE-B6-DASH-SHELL.md already exist — STOP
and report. Do not overwrite.

---

## STEP 2 — Create BUILD-VINCE-B2-API.md

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B2-API.md`

**Write this exact content:**

```
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
def run_enricher(
    trade_csv: Path,
    symbols: list,
    start: str,
    end: str,
    plugin: StrategyPlugin,
) -> EnrichedTradeSet:

---

## Types (vince/types.py)

All @dataclass. Stdlib + pandas only. No Dash imports.

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

---

## API Layer (vince/api.py)

Pure functions. No Dash imports. No global state.

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

---

## What B2 Does NOT Include

- No enricher logic (B3)
- No Optuna calls (B9)
- No Dash callbacks or layout (B6)
- No PostgreSQL writes
- No filled implementations — api.py is stubs only until B3-B5 are built
```

---

## STEP 3 — Create BUILD-VINCE-B3-ENRICHER.md

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B3-ENRICHER.md`

See full spec in the created file. Key: BLOCKED on 8 user decisions. Q1 (mfe_bar) is critical.

---

## STEP 4 — Create BUILD-VINCE-B4-PNL-REVERSAL.md

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B4-PNL-REVERSAL.md`

See full spec in the created file. BLOCKED on B1->B2->B3.

---

## STEP 5 — Create BUILD-VINCE-B5-QUERY-ENGINE.md

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B5-QUERY-ENGINE.md`

See full spec in the created file. BLOCKED on B1->B2->B3.

---

## STEP 6 — Create BUILD-VINCE-B6-DASH-SHELL.md

**Path:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B6-DASH-SHELL.md`

See full spec in the created file. BLOCKED on B1->B5.

---

## STEP 7 — Update docs/VINCE-V2-CONCEPT-v2.md (prepend status section)

Prepend Build Status table. Content locked, no changes to existing sections.

---

## STEP 8 — Update docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md (prepend status section)

Prepend Implementation Status table. Content locked, no changes to existing sections.

---

## STEP 9 — Update INDEX.md (append missing rows)

**File:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md`

Add 4 rows to Vince/ML/Screener By Topic section. Add B3 plan to Subdirectories section.

---

## STEP 10 — Update PRODUCT-BACKLOG.md

**File:** `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md`

Update P0.5 notes. Add P1.8 (B2), P1.9 (B3), P2.5 (B4), P2.6 (B5), P2.7 (B6).

---

## STEP 11 — Update TOPIC-vince-v2.md

**File:** `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-vince-v2.md`

Append B1-B4 Research Sessions section with all session logs, build specs, critical open issue, status summary.

---

## STEP 12 — Write vault copy of this plan

**Path:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-vince-doc-sync.md`

This file. Then append row to INDEX.md Plans section.

---

## EXECUTION STATUS (2026-02-28)

All 12 steps completed by Claude Code agent. Results:

**Files created (5):**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B2-API.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B3-ENRICHER.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B4-PNL-REVERSAL.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B5-QUERY-ENGINE.md`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\BUILD-VINCE-B6-DASH-SHELL.md`

**Files updated (6):**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md` — Build Status table prepended
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — Implementation Status table prepended
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\INDEX.md` — Vince topic rows + plans entry added
- `C:\Users\User\Documents\Obsidian Vault\PRODUCT-BACKLOG.md` — P0.5 updated, B2-B6 entries added
- `C:\Users\User\.claude\projects\c--Users-User-Documents-Obsidian-Vault\memory\TOPIC-vince-v2.md` — B1-B4 section appended
- `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-vince-doc-sync.md` — this file

**Files skipped (1):**
- `BUILD-VINCE-B1-PLUGIN.md` — already existed (469 lines), not overwritten per hard rules

---

## VERIFICATION CHECKLIST

After all steps complete, verify:

1. Glob `PROJECTS/four-pillars-backtester/BUILD-VINCE-B*.md` — should show 6 files (B1 through B6)
2. Read first 10 lines of `docs/VINCE-V2-CONCEPT-v2.md` — should start with `## Build Status`
3. Read first 10 lines of `docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` — should start with `## Implementation Status`
4. Read last 20 lines of `06-CLAUDE-LOGS/INDEX.md` — should include the 4 new 2026-02-28 rows
5. Read last 30 lines of `memory/TOPIC-vince-v2.md` — should include the new section
6. Confirm `PRODUCT-BACKLOG.md` contains B2-B6 entries

Report: files created, files updated, any skipped (already existed), any errors.
