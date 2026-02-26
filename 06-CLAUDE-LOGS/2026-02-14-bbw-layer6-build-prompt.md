# BBW Layer 6 Build Prompt + Audit — 2026-02-14
**Session:** claude.ai desktop
**Outcome:** Layer 6 build prompt created with placeholders, audited (8 issues), all critical fixes applied

---

## WHAT WAS DONE

### 1. Created Layer 6 Build Prompt
- File: `BUILDS\PROMPT-LAYER6-BUILD.md`
- Full spec for `research\bbw_ollama_review.py` — Ollama LLM interpretation layer
- 4 analysis steps: state stats, feature recommendations, anomaly investigation, executive summary
- Standalone `review_layer_code()` utility for post-build code review
- OllamaConfig with model selection, skip flags, truncation limits
- OllamaResult dataclass with per-step timing
- 20 tests (all mock Ollama — no real LLM calls in test suite)
- Debug script with 7 sections (35+ checks), includes live Ollama test if available
- Sanity check with mock + live modes

### 2. Audited Layer 6 Build Prompt
- 8 issues found: 1 HIGH, 4 MEDIUM, 3 LOW
- All actionable fixes applied to PROMPT-LAYER6-BUILD.md
- Full audit log: `06-CLAUDE-LOGS\2026-02-14-bbw-layer6-audit.md`

---

## AUDIT RESULTS

| ID | Severity | Summary | Status |
|----|----------|---------|--------|
| H1 | HIGH | Architecture diagram signatures don't match spec | ✅ FIXED |
| M1 | MEDIUM | `_discover_reports` breaks on `subdir='root'` files | ✅ FIXED |
| M2 | MEDIUM | `_validate_ollama_connection` fallback can assign missing model | ✅ FIXED |
| M3 | MEDIUM | Test count mismatch: header says 15, list has 20 | ✅ FIXED |
| M4 | MEDIUM | `_ollama_call` empty response not retried | Documented (intentional) |
| L1 | LOW | `_analyze_features` parses CSV (slight design deviation) | Documented |
| L2 | LOW | `max_csv_chars` reused for spec truncation | Documented |
| L3 | LOW | No `__all__` note in test spec | Non-issue |

---

## KEY DESIGN DECISIONS

1. **All tests mock Ollama** — test suite runs without any LLM. Real calls only in debug/sanity.
2. **Graceful degradation** — Ollama down → OllamaResult with errors, no crash.
3. **No data transformation** — L6 passes CSV text to LLM prompts. Does not recompute stats.
4. **Prompts hardcoded** — in source code, not external files. Self-contained module.
5. **Executive summary depends on prior steps** — receives text from steps 1-3 as context.
6. **Code review standalone** — `review_layer_code()` separate from main pipeline.
7. **Skip flags** — individual steps skippable via OllamaConfig for fast iteration.

---

## L6 OUTPUT STRUCTURE

```
reports/bbw/ollama/
├── state_analysis.md           (BBW state edge interpretation)
├── feature_recommendations.md  (VINCE ML feature pruning)
├── anomaly_flags.md            (MC overfit investigation)
└── executive_summary.md        (BBW_LSG_MAP config + action items)
```

---

## L6 → LIVE SYSTEM HANDOFF

```
executive_summary.md contains:
├── BBW_LSG_MAP python dict     → signals/four_pillars.py (state machine sizing)
├── Feature pruning list        → ml/features.py (VINCE XGBoost input selection)
└── Scaling recommendations     → signals/four_pillars.py (position scaling logic)
```

This is the TERMINAL layer. No L7 or L8.

---

## FULL PIPELINE STATUS

```
Layer 1:  signals/bbwp.py              — ✅ COMPLETE (61/61 PASS)
Layer 2:  signals/bbw_sequence.py      — ✅ COMPLETE (68/68 PASS)
Layer 3:  research/bbw_forward_returns — ✅ COMPLETE (PASSING)
Layer 4:  research/bbw_simulator.py    — 📋 BUILD PROMPT READY (audited)
Layer 4b: research/bbw_monte_carlo.py  — ❌ NEEDS BUILD PROMPT
Layer 5:  research/bbw_report.py       — 📋 BUILD PROMPT READY (audited)
Layer 6:  research/bbw_ollama_review.py— 📋 BUILD PROMPT READY (audited)
```

## BUILD ORDER (execution sequence)

```
NEXT:    Layer 4  → execute BUILDS\PROMPT-LAYER4-BUILD.md in Claude Code
THEN:    Layer 4b → create build prompt (Monte Carlo validation)
THEN:    Layer 5  → execute BUILDS\PROMPT-LAYER5-BUILD.md in Claude Code
THEN:    Layer 6  → execute BUILDS\PROMPT-LAYER6-BUILD.md in Claude Code
```

---

## FILES CREATED/MODIFIED THIS SESSION

| File | Action |
|------|--------|
| `BUILDS\PROMPT-LAYER6-BUILD.md` | NEW — full build prompt |
| `BUILDS\PROMPT-LAYER5-BUILD.md` | MODIFIED — 15 audit fixes applied |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-audit.md` | NEW — L5 audit report |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer6-audit.md` | NEW — L6 audit report |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-build-prompt.md` | MODIFIED — added audit table |
| `06-CLAUDE-LOGS\2026-02-14-bbw-layer6-build-prompt.md` | NEW — this file |
