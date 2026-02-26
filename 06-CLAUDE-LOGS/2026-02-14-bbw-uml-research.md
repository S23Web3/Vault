# BBW Simulator — Session Log
**Date:** 2026-02-14
**Sessions:** 2 (architecture + UML/research)

---

## SESSION 1: BBW Engine Build & Squeeze Opportunity Identification

**Chat:** https://claude.ai/chat/ff97f27c-5294-44da-b0ee-0f6cf5d4a061
**Time:** 2026-02-14 (morning)

### What Was Done

1. **Reviewed existing vault files:**
   - `02-STRATEGY/Indicators/bbwp_v2.pine`
   - `02-STRATEGY/Indicators/BBWP-v2-BUILD-SPEC.md`
   - `02-STRATEGY/bbwp-01-definitions.png`
   - `02-STRATEGY/Indicators/bbwp_caretaker_v6.pine`

2. **Core concept established:** BBW does NOT limit trades. BBW TUNES the LSG (Leverage, Size, Grid/Target).

3. **Full architecture document produced:** `bbw-simulator-architecture.md`
   - 5-layer pipeline: Calculator → Sequence → Forward Returns → Simulator → Report
   - Pre-step: KMeans coin classification
   - LSG grid search: 10,752 parameter combinations per state
   - Scaling sequence simulation: 6 enter-partial + add-on-improvement scenarios
   - Runtime estimate: ~8 minutes for 399 coins on 5m data
   - Parameter sensitivity analysis included

4. **BBWP percentile rank implementation options researched:**
   - Option A: `pd.Series.rolling(100).rank(pct=True)` — recommended for production
   - Option B: `scipy.stats.percentileofscore` — recommended for validation
   - Option C: Pure numpy rolling — fastest but more code

### Decisions Made
- Stop loss: test 1, 1.5, 2, 3 ATR
- Forward windows: 10 bars + 20 bars on 5m
- Proper move threshold: 3 ATR
- Coin grouping: data-driven KMeans clustering
- TDI: out of scope
- Other vol indicators: reference only, not integrated

### Files Produced
- `bbw-simulator-architecture.md` (downloaded, needs vault copy to 02-STRATEGY/Indicators/)

### Pending at End of Session
- UML diagrams not yet built
- Numpy/statistics research not completed
- Build not started (waiting for UML approval)

---

## SESSION 2: UML Diagrams & VINCE Feature Research

**Time:** 2026-02-14 (afternoon)

### What Was Done

1. **Scope question answered: Ripster/AVWAP at entry?**
   - **Answer: No — that's rabbitholing**
   - BBW simulator is single-pillar research
   - Ripster/AVWAP integration belongs at ML layer (VINCE)
   - `ml/features.py` combines all pillar features
   - XGBoost/PyTorch learns cross-pillar interactions automatically

2. **Numpy/Scipy statistics research completed:**
   - 17 BBW features identified for VINCE input
   - Distribution statistics per state: mean, std, skew, kurtosis, IQR, p5, p95, Sharpe, Sortino
   - KS test for state discrimination (is BLUE statistically different from NORMAL?)
   - Markov transition probability matrix
   - Mutual information scoring for feature selection
   - Rolling derivatives: ROC, acceleration, z-score
   - Rolling shape stats: skewness(20), kurtosis(20)

3. **6 UML diagrams produced (Mermaid format, Obsidian-native):**
   - Class Diagram — static structure of all 7 classes
   - Sequence Diagram — per-coin processing pipeline
   - Activity Diagram — simulator decision logic with LSG grid + scaling
   - Component Diagram — system architecture showing research vs live pipeline
   - State Diagram — BBWP state machine with transitions and LSG notes
   - Data Flow Diagram — feature engineering pipeline from raw OHLCV → VINCE vector

4. **Build sequence defined:**
   - 10 steps, estimated 5 hours Claude Code work
   - Test-first approach per python-trading-development-skill.md
   - scikit-learn confirmed installed

### Revisions
- State diagram: replaced stateDiagram-v2 with flowchart for larger readable boxes, added full LSG params per state
- VINCE feature legend: added table + note explaining 17 features across 4 categories
- Monte Carlo: added Layer 4b (`research/bbw_monte_carlo.py`) — 1000x trade shuffle, confidence intervals, overfit detection. Matches v3.8 MC approach. Adds ~23 min to runtime.
- Ollama: confirmed NOT needed — BBW simulator is pure numpy/pandas. Ollama relevant for VINCE NL reasoning, not statistical engine.
- Split combined file into separate UML and Research docs

### Files Written to Vault
- `02-STRATEGY/Indicators/BBW-UML-DIAGRAMS.md` — 6 Mermaid diagrams with legends
- `02-STRATEGY/Indicators/BBW-STATISTICS-RESEARCH.md` — scope, features, Monte Carlo, build sequence
- `06-CLAUDE-LOGS/2026-02-14-bbw-uml-research.md` — This log

### Next Steps
1. Review all 4 docs in Obsidian — diagrams render natively
2. Approve architecture → start build in Claude Code
3. Build sequence: Layer 1 first, test against Pine Script output

### Additional Revisions (same session)
- Ollama Layer 6 added to architecture: 6 integration points using qwen3:8b (fast), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep analysis)
- Math stays in numpy. Reasoning about math goes to Ollama.
- Architecture doc written: `BBW-SIMULATOR-ARCHITECTURE.md`
- Total runtime now ~35 min (8 compute + 23 MC + 3 Ollama + overhead)

### Final Vault Files
- `02-STRATEGY/Indicators/BBW-UML-DIAGRAMS.md` — 6 diagrams with legends
- `02-STRATEGY/Indicators/BBW-STATISTICS-RESEARCH.md` — features, MC, build sequence
- `02-STRATEGY/Indicators/BBW-SIMULATOR-ARCHITECTURE.md` — full architecture + Ollama Layer 6
- `06-CLAUDE-LOGS/2026-02-14-bbw-uml-research.md` — this log
