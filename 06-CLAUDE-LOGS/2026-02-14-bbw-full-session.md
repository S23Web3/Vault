# 2026-02-14 — BBW Simulator: Diagrams Fix, Monte Carlo, Ollama, Layer 1 Prompt + Build Complete
**Session:** claude.ai desktop
**Previous:** https://claude.ai/chat/ff97f27c-5294-44da-b0ee-0f6cf5d4a061

---

## Summary

Session covered 5 areas: UML diagram fixes, Monte Carlo addition, Ollama integration, Claude Code prompt for Layer 1, and confirmation that Layer 1 build is complete.

---

## Work Done

### 1. UML Diagram Fixes (BBW-UML-DIAGRAMS.md rewritten)
- State diagram: replaced tiny stateDiagram-v2 with flowchart LR — readable boxes with full LSG params per state
- Added color-coded zones (blue/neutral/red) and transition legend table
- VINCE feature legend: categorized table (Direct 4, Derived 7, Sequence 5, Markov 1 = 17 total)
- Added MonteCarloValidator class to class diagram
- Updated sequence diagram and component diagram with MC + Ollama layers

### 2. Monte Carlo Validation Added (Layer 4b)
- File: `research/bbw_monte_carlo.py`
- 1000x trade order shuffle per BBW state
- 95% confidence intervals on PnL, max DD, Sharpe
- Overfit detection: real PnL must beat 95th percentile of shuffled
- 4 output CSVs: mc_summary_by_state, mc_confidence_intervals, mc_equity_distribution, mc_overfit_flags
- Runtime: ~23 min for 399 coins
- Full implementation code added to BBW-STATISTICS-RESEARCH.md

### 3. Ollama Integration (Layer 6)
- Confirmed: numpy does math, Ollama reasons about results
- 6 integration points with model assignments:
  1. Code review per layer — `qwen2.5-coder:32b`
  2. State analysis from CSVs — `qwen3:8b`
  3. Feature recommendations from MI scores — `qwen3:8b`
  4. Anomaly investigation of MC flags — `qwen3-coder:30b`
  5. Executive summary with BBW_LSG_MAP — `qwen3-coder:30b`
  6. Build log generation — `qwen3:8b`
- Ollama runtime: ~3 min total
- Full API integration code in architecture doc

### 4. Architecture Doc Written
- `BBW-SIMULATOR-ARCHITECTURE.md` — comprehensive 6-layer spec
- All layers with inputs/outputs/functions
- CLI flags including --no-ollama, --no-monte-carlo, --mc-sims
- Runtime: ~35 min total (8 compute + 23 MC + 3 Ollama + 1 overhead)
- File structure, dependencies, decisions locked

### 5. Claude Code Prompt for Layer 1
- `CLAUDE-CODE-PROMPT-LAYER1.md` — 12KB self-contained build prompt
- Mandatory reads: skill file, Pine source, architecture, research doc
- 5 tricky parts flagged (MA cross persistence, percentrank matching, NaN, basis=0, points mapping)
- Build order: tests first → implementation → sanity on RIVERUSDT → Ollama review → log
- Review checklist: Pine fidelity (7), code quality (8), performance (4), downstream compat (4)

### 6. Investopedia Article Review
- URL: investopedia.com/articles/technical/04/030304.asp (BB squeeze basics)
- Verdict: NO VALUE — covers basic squeeze theory already exceeded by our architecture
- BBWP percentile rank > raw BBW, 7-state machine > binary squeeze/not, other 3 pillars solve direction problem
- Only tangential concept: %B (price position within bands) — potential future VINCE feature, not needed now

### 7. Layer 1 Build — COMPLETE
- `signals/bbwp.py` built and tested in Claude Code
- Status: confirmed complete by user

---

## Files Written/Updated

| File | Location | Action |
|------|----------|--------|
| BBW-UML-DIAGRAMS.md | 02-STRATEGY/Indicators/ | Rewritten — 6 diagrams with legends, MC class |
| BBW-STATISTICS-RESEARCH.md | 02-STRATEGY/Indicators/ | Updated — Monte Carlo section, build sequence |
| BBW-SIMULATOR-ARCHITECTURE.md | 02-STRATEGY/Indicators/ | NEW — full 6-layer architecture + Ollama |
| CLAUDE-CODE-PROMPT-LAYER1.md | 02-STRATEGY/Indicators/ | NEW — Claude Code build prompt |
| 2026-02-14-bbw-uml-research.md | 06-CLAUDE-LOGS/ | Updated |
| 2026-02-14-bbw-layer1-prompt.md | 06-CLAUDE-LOGS/ | Written mid-session |
| 2026-02-14-bbw-full-session.md | 06-CLAUDE-LOGS/ | THIS FILE |

---

## Decisions

| Decision | Choice |
|----------|--------|
| Ollama in simulator | Yes — Layer 6, post-computation reasoning |
| Models | qwen3:8b (fast), qwen2.5-coder:32b (review), qwen3-coder:30b (deep) |
| Monte Carlo | Yes — Layer 4b, 1000 sims, 95% CI |
| Total pipeline runtime | ~35 min for 399 coins |
| Investopedia article | No value — already exceeded |
| Layer 1 | COMPLETE |

---

## Issues This Session
- Context compaction triggered without warning — caused wasteful token-burning search outside vault
- Multiple unnecessary filesystem searches outside Obsidian vault
- Rule violated: should warn before exceeding context, allow new chat

---

## Pipeline Status

| Layer | File | Status |
|-------|------|--------|
| 0 | research/__init__.py | NOT STARTED |
| 1 | signals/bbwp.py | ✅ COMPLETE |
| 2 | signals/bbw_sequence.py | NEXT — needs Claude Code prompt |
| 3 | research/coin_classifier.py | NOT STARTED |
| 4 | research/bbw_forward_returns.py | NOT STARTED |
| 5 | research/bbw_simulator.py | NOT STARTED |
| 5b | research/bbw_monte_carlo.py | NOT STARTED |
| 6 | research/bbw_report.py | NOT STARTED |
| 6b | research/bbw_ollama_review.py | NOT STARTED |
| 7 | scripts/run_bbw_simulator.py | NOT STARTED |

## Next Steps
1. New chat — write CLAUDE-CODE-PROMPT-LAYER2.md for signals/bbw_sequence.py
2. Get Layer 1 test results / Ollama review findings if not already logged
3. Build Layer 2 in Claude Code
