# Plan: Lock Vince v2 Concept + Define Build Roadmap

**Date:** 2026-02-27
**Goal:** Get the Vince v2 concept doc approved for build, then produce the formal build plan.

---

## Context

Vince v2 concept doc (`PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md`) has been in scoping since 2026-02-18. The analysis engine design is solid (plugin interface, enricher, 3 modes, 8 panels, RL exit policy, random sampling).

User requirements:

- **Proper GUI** — Advanced Dash/Streamlit, not throwaway buttons. Good UX for daily use.
- **Agent-ready skeleton** — Clean API layer so an AI agent can plug in later. Agent itself is a future iteration.
- **Core focus** — Analysis engine + GUI first. Agent + RL + LLM = later phases.

---

## What Needs to Happen (in order)

### 1. Add GUI section to concept doc

The concept doc describes 8 panels but not HOW they're built. Add:

- **Framework decision:** Dash vs Streamlit (recommendation: Dash -- no re-run-on-every-click, proper callbacks, CSS control)
- **Layout:** Sidebar navigation for 8 panels, persistent filter bar, main content area
- **Key UX:** Filter changes trigger scoped callbacks (not full page reload). Real-time metric deltas.

### 2. Add architecture skeleton to concept doc

The concept doc doesn't define the internal module boundaries. Add:

- **API layer** (`vince/api.py`) — Clean Python functions that BOTH the GUI and a future agent call. This is the skeleton that makes agent integration trivial later.
  - `query_constellation(filters) -> MetricTable`
  - `run_enricher(symbols, params) -> EnrichedTradeSet`
  - `get_panel2_data(symbol) -> PnLReversalResult`
- **Separation rule:** GUI never calls analysis engine directly. GUI calls API. API calls engine. Future agent calls the same API.

### 3. Lock the concept

Change status to `APPROVED FOR BUILD`. Design freezes. Code begins.

### 4. Build (proposed order)

| Phase | What | Produces |
| ----- | ---- | -------- |
| **B1** | FourPillarsPlugin | Concrete plugin wrapping existing backtester |
| **B2** | API layer + types | `vince/api.py`, `vince/types.py` — the skeleton |
| **B3** | Enricher | Attach indicator snapshots to every trade |
| **B4** | Panel 2 (PnL Reversal) | Highest priority analysis — exit optimization |
| **B5** | Constellation Query Engine | Ask "when X was Y, what happened?" |
| **B6** | Dash GUI (Panels 1-4) | Working interactive dashboard |
| **B7** | Mode 2 Auto-Discovery | Sweep constellations, surface patterns |
| **B8** | Mode 3 Settings Optimizer | Optuna parameter sweep |
| **B9** | Dash GUI (Panels 5-7) | Optimizer + validator + session history panels |
| _future_ | Agent, RL, LLM | Plugs into the API layer built in B2 |

Each phase = one build session with tests.

---

## Decisions Needed From You

1. **Dash or Streamlit?** (Recommendation: Dash)
2. **Is the concept doc analysis engine design correct?** (Plugin, enricher, 3 modes, 8 panels)
3. **Is this build order right, or do you want to rearrange?**

Once you confirm, I add the GUI + skeleton sections to the concept doc, lock it, and B1 starts.