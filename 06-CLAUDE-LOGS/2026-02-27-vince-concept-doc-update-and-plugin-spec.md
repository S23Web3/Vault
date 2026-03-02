# Vince Concept Doc Update + Plugin Interface Spec
**Date:** 2026-02-27
**Continuation of:** 2026-02-27-vince-ml-yt-findings.md

---

## What Was Done

### Task 1 — VINCE-V2-CONCEPT-v2.md (10 edits)

Applied all ML findings from the 202-video YT channel analysis to the concept doc.
Status unchanged: NOT YET APPROVED FOR BUILD. User still researching.

| Edit | What changed |
|------|-------------|
| 1 | Changelog items 15-18: Panel 2 priority, RL component, random sampling, expanded RL action space |
| 2 | Mode 2 Auto-Discovery: XGBoost feature importance pre-step, k-means clustering pre-step, 80/20 held-out partition, random dataset sampling, reflexivity caution |
| 3 | Mode 3 Settings Optimizer: walk-forward rolling window methodology, random dataset sampling per Optuna trial |
| 4 | New section "RL Exit Policy Optimizer": action space {HOLD/EXIT/RAISE_SL/SET_BE}, state vector, training methodology, intra-candle classification, dashboard integration, enricher expansion |
| 5 | Process Flow mermaid: RL EXIT POLICY node added (Enricher -> RL -> Storage -> Dashboard) |
| 6 | Stage 4 Dashboard mermaid: Panel 2 marked ★ PRIORITY, Panel 4 intra-candle events, Panel 6 feat importance, RL results feed Panel 2 |
| 7 | Constraints: survivorship bias bullet + reflexivity bullet |
| 8 | Open Questions: item 7 for RL scoping session |
| 9 | What Already Exists: strategies/base_v2.py replaces base.py reference |
| 10 | Date header updated to reflect 2026-02-27 additions |

### Task 2 — Plugin Interface Spec (P1.7)

Two deliverables created:

**VINCE-PLUGIN-INTERFACE-SPEC-v1.md** — 7-section formal spec:
- Section 1: Purpose
- Section 2: Full StrategyPlugin ABC with type signatures
- Section 3: Method contracts (3a-3e) — input/output guarantees, error contracts, performance requirements
- Section 4: OHLCV DataFrame contract
- Section 5: Enricher contract (naming convention, snapshot columns, OHLC tuples)
- Section 6: Compliance checklist (18 items)
- Section 7: FourPillarsPlugin compliance mapping — key issue identified: bar index alignment (Trade384 stores offsets, not absolute positional indices)

**strategies/base_v2.py** — Python StrategyPlugin ABC stub:
- All 5 abstract methods + 1 property
- Full docstrings
- py_compile: PASS
- base.py kept as archive (rejected v1 XGBoost classifier)

### Task 3 — Coherence Review

Word-for-word cross-check of all three documents. 5 issues found and fixed:

| # | Issue | Fix |
|---|-------|-----|
| 1 | Wrong filename: `four_pillars_v383.py` | Corrected to `four_pillars_v383_v2.py` |
| 2 | `strategies/four_pillars.py` listed as existing | Annotated "(to be created — primary build task)" |
| 3 | `symbol` (required column) hidden behind `...` in trade_schema example | Added `symbol` before optional `grade` |
| 4 | RL state vector hardcoded k1-k4 — contradicts strategy-agnostic design | Added preamble: indicator features come from `plugin.compute_signals()` dynamically |
| 5 | `list[str]` vs `list` type hint inconsistency | Aligned all to `list` |

---

## Files Created / Modified

| File | Action |
|------|--------|
| `PROJECTS/four-pillars-backtester/docs/VINCE-V2-CONCEPT-v2.md` | 10 edits + 5 coherence fixes |
| `PROJECTS/four-pillars-backtester/docs/VINCE-PLUGIN-INTERFACE-SPEC-v1.md` | Created (new) |
| `PROJECTS/four-pillars-backtester/strategies/base_v2.py` | Created (new), py_compile PASS |
| `memory/TOPIC-vince-v2.md` | Status + new file references updated |
| `06-CLAUDE-LOGS/plans/2026-02-27-vince-concept-doc-update-and-plugin-spec.md` | Plan copy (vault) |

---

## Status

- Concept doc: updated, NOT YET APPROVED FOR BUILD
- Plugin spec: complete, formally documented
- Python stub: complete, py_compile pass
- Next: user approves concept doc when research is complete, then FourPillarsPlugin wrapper build begins
