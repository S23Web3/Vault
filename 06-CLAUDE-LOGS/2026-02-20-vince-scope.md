# Vince v2 — Scoping Session Log
**Date:** 2026-02-20
**Status:** Scoping in progress. Concept v2 rewrite pending. Trading LLM scoping needed as separate session.

---

## Session Summary

Continued scoping Vince v2 from 2026-02-19. Two topics: (1) full audit and correction of the concept doc v1 — 14 issues identified, (2) new architectural direction adding a two-layer design with a fine-tuned trading LLM.

---

## Hard Rule Added

MEMORY.md rule updated: "FULL PATHS EVERYWHERE" — extended from "in run commands only" to "in ANY output." Any file or directory reference in any output must use the full Windows path. No short names.

---

## Concept Doc Audit — 14 Issues

1. Strategy coupling: "indicator framework is fixed" — wrong. Plugin provides it, not Vince.
2. Fixed Constants section hardcodes K1/K2/K3/K4/Cloud EMAs — moves to plugin.
3. "What Vince Can Sweep" hardcodes TP/SL/cross_level/cloud3/BE — moves to plugin parameter_space().
4. Constellation Query Dimensions entire section hardcodes K1/K2/K3/K4/Cloud2/Cloud3/BBW/Grade A-R/entry type — all come from plugin at runtime via trade_schema() and signal definitions.
5. K4 Regime Buckets hardcodes K4 — generic equivalent: macro signal buckets defined per plugin.
6. Win rate as dominant metric throughout — bias. Replaced with full metric table (win rate, profit factor, avg net PnL, MFE, MAE, PnL reversal rate, MFE/MAE ratio, trade count).
7. "NOT autonomous" contradicted by Mode 3 (Optuna runs autonomously) — scoped correctly: optimizer runs computations autonomously, never applies setting changes without user action.
8. "Works on any CSV produced by the backtester" — coupling to one backtester. Fixed: any trade CSV with defined schema, schema defined by plugin.
9. Auto-discovery ranks by raw delta — no significance control. Fixed: effect size + user-set minimum N threshold.
10. "399 coins" and "data/cache/" hardcoded in diagrams — replaced with generic labels.
11. "Price action is for amateurs" — editorial comment in architectural document.
12. LSG terminology is Four Pillars specific — renamed to "PnL Reversal Analysis." LSG is an alias in the Four Pillars plugin.
13. "What Already Exists" listed strategy components as Vince core — separated into Vince core vs Four Pillars plugin.
14. dashboard_v391.py listed as Vince component — not applicable. Vince is a separate dashboard.

---

## Architecture Decisions — All Approved

### Plugin Interface
A strategy plugin provides two components:

**Computational:**
- compute_signals(ohlcv_df) → DataFrame
- parameter_space() → dict (sweepable params with bounds)
- trade_schema() → dict (columns in backtester trade CSV)
- run_backtest(params, start, end, symbols) → path

**Semantic:**
- strategy_document: Path — markdown file. If not in markdown, convert and check with user before accepting.

### Two-Layer Architecture
- Layer 1 (Quantitative): counts, compares, measures. Always available.
- Layer 2 (Interpretive): trading LLM via Ollama. Triggered after full sweep completes. User reads interpretation then interacts.

### Operating Modes
- Quantitative-only: no LLM required. Full analysis.
- Quantitative + Interpretive: LLM loaded. Full analysis plus strategy-grounded hypothesis layer.

### LLM Trigger Flow
1. Sweep/analysis runs and completes
2. LLM interprets the full results in context of strategy document
3. User reads interpretation
4. User interacts — follow-up questions, drill into specific patterns, request research directions

### Trading LLM
- Fine-tuned trading domain expert. Not a general model with prompts.
- Trained on: technical analysis, indicator mathematics, divergences, regression channels, market structure, backtesting concepts, strategy logic analysis.
- Does NOT need strategy-specific training — needs trading domain training. Reads any strategy document from first principles.
- Runs locally via Ollama. Candidate models: DeepSeek-R1 (reasoning chain visible), Qwen2.5.
- Chinese models require more explicit context — domain terminology defined in prompt, not assumed.
- Prompt engineering is iterative within the build (load trading context, test capability, design prompts from observed results).
- Shared asset: serves Vince, Vicky, Andy, and all future personas.
- SEPARATE build track from Vince. SEPARATE scoping session needed.

---

## Files Status

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT.md` — original concept doc. Has 14 known issues. Not corrected.
- Concept v2 rewrite: prepared but NOT written — session ended before write was executed.

---

## Trading LLM Research Material

Qwen3 was prompted directly by user with: "hello qwen, how do i train you to be very expert in trading analysis and strategy analysis and machine learning"

Full response saved to: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\TRADING-LLM-QWEN3-RESPONSE.md`

**Key observations:**
- Qwen3 demonstrates general ML + trading domain knowledge
- Response covers data collection, feature engineering, supervised/RL/unsupervised ML, backtesting, integration
- Gap: no mention of multi-stochastic systems, EMA clouds, BBW, or strategy-document-driven interpretation — confirms need for domain-specific fine-tuning
- Fine-tuning on financial texts + synthetic scenarios confirmed as viable approach by the model itself
- DeepSeek-R1 response should also be collected and compared before scoping the training dataset

To be worked on in a dedicated trading LLM scoping session.

---

## Session Update — 2026-02-23

**Concept v2 written:**
`C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md`

All 14 audit corrections applied. Two-layer architecture (Quantitative + Interpretive LLM) included. Plugin interface fully documented. Four Pillars examples clearly separated from Vince core.

**UML status clarified:** `docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md` exists (171 lines, generated 2026-02-18). No "TO BE CREATED" markers present.

**Status:** Concept v2 complete. Awaiting user approval before plugin interface formal scope.

---

## Pick-Up Instructions — Next Session

1. Read this log.
2. Write concept v2 to `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md` — all 14 corrections applied, two-layer LLM architecture included.
3. Scope the trading LLM (separate conversation — fine-tuning dataset, training, evaluation methodology).
4. After concept v2 is approved, scope the plugin interface formally.
