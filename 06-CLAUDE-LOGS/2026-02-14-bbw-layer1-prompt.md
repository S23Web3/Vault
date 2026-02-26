# 2026-02-14 — BBW Simulator: Diagrams Fix, Monte Carlo, Ollama, Layer 1 Prompt
**Session:** claude.ai desktop
**Duration:** ~2 hours
**Previous:** https://claude.ai/chat/ff97f27c-5294-44da-b0ee-0f6cf5d4a061 (architecture + UML session)

---

## Work Done

### 1. UML Diagram Fixes
- State diagram: replaced tiny stateDiagram-v2 with flowchart LR — full LSG params per state, color-coded zones
- VINCE feature legend: added categorized table (Direct 4, Derived 7, Sequence 5, Markov 1 = 17 total)
- All 6 diagrams rewritten to `BBW-UML-DIAGRAMS.md`

### 2. Monte Carlo Added (Layer 4b)
- 1000x trade order shuffle per BBW state
- 95% confidence intervals on PnL, max DD, Sharpe
- Overfit detection: real PnL must beat 95th percentile of shuffled
- File: `research/bbw_monte_carlo.py`
- Runtime addition: ~23 min → total pipeline ~35 min for 399 coins
- Added to `BBW-STATISTICS-RESEARCH.md` with full implementation code

### 3. Ollama Integration (Layer 6)
- Confirmed: numpy does the math, Ollama reasons about the math
- 6 integration points:
  1. Code review per layer (`qwen2.5-coder:32b`)
  2. State analysis from CSVs (`qwen3:8b`)
  3. Feature recommendations from MI scores (`qwen3:8b`)
  4. Anomaly investigation of MC flags (`qwen3-coder:30b`)
  5. Executive summary with BBW_LSG_MAP (`qwen3-coder:30b`)
  6. Build log generation (`qwen3:8b`)
- Ollama runtime: ~3 min total
- File: `research/bbw_ollama_review.py`

### 4. Architecture Doc Written
- `BBW-SIMULATOR-ARCHITECTURE.md` — full 6-layer spec including Ollama
- All layers detailed with inputs/outputs/functions
- CLI flags documented
- Runtime estimates, dependencies, decisions locked

### 5. Claude Code Prompt for Layer 1
- `CLAUDE-CODE-PROMPT-LAYER1.md` — self-contained build prompt (12KB)
- Includes: context, mandatory reads, exact spec, 5 tricky parts, build order, review checklist, sanity perspective
- Build order: tests first → implementation → sanity on RIVERUSDT → Ollama review → log

---

## Files Written/Updated

| File | Location | Action |
|------|----------|--------|
| BBW-UML-DIAGRAMS.md | 02-STRATEGY/Indicators/ | Rewritten — larger state diagram, legends |
| BBW-STATISTICS-RESEARCH.md | 02-STRATEGY/Indicators/ | Updated — Monte Carlo section, build sequence |
| BBW-SIMULATOR-ARCHITECTURE.md | 02-STRATEGY/Indicators/ | NEW — full architecture + Ollama Layer 6 |
| CLAUDE-CODE-PROMPT-LAYER1.md | 02-STRATEGY/Indicators/ | NEW — Claude Code build prompt |
| 2026-02-14-bbw-uml-research.md | 06-CLAUDE-LOGS/ | Updated — revisions logged |
| 2026-02-14-bbw-layer1-prompt.md | 06-CLAUDE-LOGS/ | THIS FILE |

---

## Decisions Made

| Decision | Choice |
|----------|--------|
| Ollama in BBW simulator | Yes — Layer 6, reasoning about results (not math) |
| Models | qwen3:8b (fast), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep) |
| Monte Carlo | Yes — Layer 4b, 1000 sims, 95% CI |
| Total runtime | ~35 min (8 compute + 23 MC + 3 Ollama + 1 overhead) |

---

## Issues

- Context compaction triggered without warning — caused wasteful searching outside vault
- Token waste from searching C:\Users\User\Documents instead of staying in vault
- Compaction rule violated: should warn before exceeding context, allow new chat

---

## Next Steps

1. Open Claude Code in VS Code
2. Paste the 5-file read prompt
3. Claude Code builds tests/test_bbwp.py first, then signals/bbwp.py
4. After Layer 1 passes: new prompt for Layer 2
