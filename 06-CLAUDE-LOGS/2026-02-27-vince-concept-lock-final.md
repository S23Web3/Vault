# Session Log: Vince v2 Concept Lock + Build Plan Alignment
**Date:** 2026-02-27
**Session type:** Concept finalization + plan alignment
**Continues from:** 2026-02-27-vince-concept-doc-update-and-plugin-spec.md

---

## What Was Done

### 1. Concept Lock
Added two missing sections to `PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md`:

**GUI — Dash Application section:**
- Framework: Plotly Dash (replaces Streamlit dashboard_v392.py entirely)
- Run command: `python vince/app.py`
- Layout: sidebar nav + persistent context bar + main content area
- 8 core panels defined with "what it answers" framing
- Future panels: RL Exit Policy, LLM Interpretation (separate scoping sessions required)

**Architecture — Module Boundaries section:**
- Three-layer model: GUI layer → API layer → Engine/Analysis layer
- Separation rule: panel files import only from `vince.api` and `vince.types`
- API function signatures defined (7 functions)
- Types dataclasses defined (9 dataclasses)
- Full file layout diagram

Status changed to: **CONCEPT v2 — APPROVED FOR BUILD (2026-02-27)**

---

### 2. Build Plan Created
`C:\Users\User\.claude\plans\async-watching-balloon.md` (+ vault copy at `06-CLAUDE-LOGS/plans/2026-02-27-vince-b1-b10-build-plan.md`)

**10 build phases:**
| Phase | Output |
|-------|--------|
| B1 | `strategies/four_pillars.py` — FourPillarsPlugin |
| B2 | `vince/api.py`, `vince/types.py` |
| B3 | `vince/enricher.py` |
| B4 | `vince/pages/pnl_reversal.py` (data module) |
| B5 | `vince/query_engine.py` |
| B6 | `vince/app.py`, `vince/layout.py` (Dash shell) |
| B7 | Pages 1, 3, 4, 5 (Coin Scorecard, Constellation, Exit State, Trade Browser) |
| B8 | `vince/discovery.py` (Mode 2) |
| B9 | `vince/optimizer.py` (Mode 3) |
| B10 | Pages 6, 7, 8 (Optimizer, Validation, History) |

---

### 3. Dash Skill Created (separate agent)
`C:\Users\User\.claude\skills\dash\SKILL.md` — 1,040 lines. Two-part (architecture + technical reference). Covers Dash 4.0.0, pattern-matching callbacks, dcc.Store, background callbacks, ag-grid, ML serving, PostgreSQL, production config. CLAUDE.md updated with DASH SKILL MANDATORY rule.

---

### 4. Plan Alignment (4 issues resolved)

| Issue | Fix | Files Changed |
|-------|-----|---------------|
| `vince/panels/` vs Dash native `pages/` convention | Renamed to `vince/pages/` throughout | Concept doc (3 places), build plan (2 places), SKILL.md |
| B4 before B6 — ordering confusion | B4 description clarified: "pure Python data module (no Dash imports)" | Build plan |
| `four_pillars_plugin.py` vs `four_pillars.py` | Use `four_pillars.py` — matches locked concept doc | Build plan (B1 table + file structure) |
| No enriched trades storage strategy | Added diskcache pattern to B3: session_id in dcc.Store, enriched trades on disk by key | Build plan |

---

## Decisions Made

- **Vince = the app.** Dashboard serves Vince — not added to Streamlit, replaces it entirely.
- **Dash framework** (Plotly Dash 4.0.0). Pattern-matching callbacks required for constellation builder.
- **Agent is future.** API skeleton built now. No agent build phases in B1-B10.
- **`vince/pages/`** — Dash native convention with `dash.register_page()` and `use_pages=True`.
- **Enriched trades**: diskcache for dev (same cache as `DiskcacheLongCallbackManager`). PostgreSQL for prod if needed.
- **B3/B4/B5 are data-only modules** — no Dash imports. B6 wires them into the app.

---

## Current State

| Document | Status |
|----------|--------|
| `VINCE-V2-CONCEPT-v2.md` | APPROVED FOR BUILD. GUI + Architecture sections added. `pages/` convention. |
| `VINCE-PLUGIN-INTERFACE-SPEC-v1.md` | Coherence reviewed. 5 fixes applied. |
| `strategies/base_v2.py` | StrategyPlugin ABC. py_compile pass. |
| Build plan `async-watching-balloon.md` | All 4 alignment issues fixed. |
| Vault copy `plans/2026-02-27-vince-b1-b10-build-plan.md` | Created. |
| `C:\Users\User\.claude\skills\dash\SKILL.md` | Created by agent. `pages/` trigger updated. |

---

## Next Step

**B1: FourPillarsPlugin** — `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\four_pillars.py`

- Implements `StrategyPlugin` ABC from `strategies/base_v2.py`
- Wraps `engine/backtester_v384.py` (run_backtest)
- Calls `signals/four_pillars_v383_v2.py` (compute_signals_v383) for compute_signals()
- Uses `engine/commission.py` for commission model
- Pure Python, no Dash imports
- BACKLOG: P0.5 READY
