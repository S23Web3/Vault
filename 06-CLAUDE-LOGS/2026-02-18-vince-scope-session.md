# Vince ML v2 Scoping Session Log
**Date:** 2026-02-18
**Model:** Opus 4.6
**Status:** SCOPE IN PROGRESS (not finalized)

---

## Session Timeline

### Phase 1: Identifying the Problem
- User asked what the last build was. Two builds identified: Dashboard v3.9.2 (Numba) and Vince ML Train Pipeline.
- User explained Vince ML v1 FAILED: "fundamentally wrong." Built a critic (TAKE/SKIP trade filter) when user needs an assistant (parameter optimizer).
- Key quote: "never less trades just better win rates or stop losses. Total Volume $1,492,840,000"

### Phase 2: Correcting Approach
- Launched 3 explore agents to research logs, build scripts, ML modules.
- Found v1 was Vicky's architecture (copy trading, trade filtering) mislabeled as Vince.
- User corrected me multiple times: "SCOPE, not build. Not plan. SCOPE."
- User said I wasted 36K tokens by jumping ahead.

### Phase 3: Mapping Relationship Questions
- Mapped 83 relationship questions across 12 categories.
- User corrected S1: stochastics are a UNIT, not separate variables.
- User corrected: individual levels don't matter (20 vs 25 doesn't matter). Patterns matter (divergence, pullback, channel).
- Dynamic properties added: slope, speed, crossing events, duration in state.

### Phase 4: Constellation Concept
- Each indicator has STATIC (snapshot) and DYNAMIC (behavior) properties.
- AVWAP: not Shannon structural anchoring. Entry-anchored intentionally.
- User corrected persona mixing: "that is for vicky not for vince."
- User: "price action is for amateurs" -- reads INDICATORS, not price.
- User: "you can not read it, you need to read all parameters" -- complete numerical state.

### Phase 5: Trade Data Analysis
- User provided two 10-coin portfolio CSV exports.
- Run 1: 77,995 trades, 86.0% LSG. Run 2: 89,633 trades, 85.6% LSG.
- User: "its not a coincidence" -- LSG is systemic across any random coin set.

### Phase 6: Late Entry Example
- User: "late entry meaning 9,3 is under 60 for long and above 40 for short"
- I INCORRECTLY restated as "K1 past 60" -- inverting the direction entirely.
- User: "wtf, i said under 60 for long and you make is past 60?"
- CORRECT: K1 UNDER 60 for long = K1 < 60, hasn't reached 60 yet (still moving up from oversold).

### Phase 7: Dashboard Audit Request
- User: "i want a full audit on the code of the dashboard. is this really through?"
- Full audit completed across 9 files. Result: engine is mechanically correct with 1 known bug (scale-out commission double-count in CSV, equity unaffected).

---

## Critical Errors Made This Session

1. **Inverted "under 60" to "past 60"** -- changed the signal direction entirely.
2. **Jumped to plan/build before finishing scope** -- user had to correct multiple times.
3. **Mixed up personas** -- described Vicky's job as Vince's.
4. **Used "price action" phrase** -- user corrected: reads indicators, not price.
5. **Used summaries instead of exact values** -- user requires ALL parameters.
6. **Framed problem as "fear of adjustment"** -- user's actual point: can't manually review thousands of trades.

## Prevention Rules

1. NEVER paraphrase directional statements. Quote exact words.
2. SCOPE before plan. PLAN before build. Get approval at each step.
3. When in doubt, STOP and ask. Do not guess directions or meanings.
4. Stochastics = UNIT. Never analyze independently.
5. Complete numerical state only. No summaries.

---

## Key Decisions Made

1. Vince ML v1 (XGBoost classifier) = REJECTED. Wrong architecture.
2. Vince ML v2 = trade research engine (PyTorch, GPU, relationship analysis).
3. Strategy-agnostic base. Four Pillars first plugin.
4. Never reduce trade count. Volume preserved.
5. No prioritization of relationships -- data shows what's there.
6. RE-ENTRY logic fix deferred until after Vince scope.
7. Dashboard v3.9.2 (Numba) -- build script ready, not yet run.

---

## Pending for Next Session

1. **Continue Vince ML v2 scoping** -- user was still providing examples.
2. **Architecture breakdown** -- modules, interfaces, data contracts.
3. **New UML diagrams** -- reflecting research engine, not classifier.
4. **Fix scale-out commission bug** -- user decides priority.
5. **Run dashboard v3.9.2 build** -- verify Numba, check parity.

---

## Files Written This Session

| File | Purpose |
|------|---------|
| Plan file (functional-orbiting-rabbit.md) | Handoff document with scope + audit + rules |
| 06-CLAUDE-LOGS/2026-02-18-dashboard-audit.md | Full dashboard code audit results |
| 06-CLAUDE-LOGS/2026-02-18-vince-scope-session.md | This session log |
