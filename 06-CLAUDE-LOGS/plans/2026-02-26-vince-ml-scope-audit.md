# Vince ML — Status Audit & Scope

**Date:** 2026-02-26
**Purpose:** Where the project stands, what exists, what's decided, what's not.

---

## Context

The user asked to scope where Vince ML stands. There are THREE distinct things called "Vince" at different stages. This document untangles them and identifies the single blocker preventing forward progress.

---

## 1. Version Inventory

### A. Vince ML v1 — XGBoost/PyTorch Classifier (BUILT, STAGING, CONCEPTUALLY REJECTED)

- **Location:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\ml\`
- **Stats:** 19 files, 2,643 lines, 37/37 tests (2026-02-14)
- **What it does:** Predicts trade outcomes (win/loss probability), sizes positions, filters trades
- **Key modules:** `vince_model.py` (PyTorch 3-branch), `xgboost_trainer_v2.py`, `features_v3.py` (27 features), `training_pipeline.py` (pool A/B/C split), `triple_barrier.py`, `purged_cv.py`, `walk_forward.py`, `loser_analysis.py`, `shap_analyzer_v2.py`, `bet_sizing_v2.py`, `xgboost_auditor.py`, `coin_features.py`
- **Staging:** `scripts/build_staging.py` creates 4 files (dashboard, run_backtest, test_dashboard_ml, live_pipeline) — NEVER DEPLOYED
- **Backlog:** P1.2 "Deploy staging files" = READY (but should be re-evaluated)
- **STATUS: REJECTED CONCEPTUALLY.** User decided Vince is NOT a classifier. TAKE/SKIP = Vicky's job.

### B. Vince v2 — Trade Research Engine (CONCEPT WRITTEN, NOT APPROVED FOR BUILD)

- **Concept doc:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\VINCE-V2-CONCEPT-v2.md` (2026-02-23, 14 corrections from v1)
- **Spec review fixes (2026-02-24):** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-24-vince-v2-ml-spec-review.md`
- **Architecture:** Strategy-agnostic plugin + two-layer design
  - **Layer 1 (Quantitative):** Frequency counting, constellation queries, auto-discovery, optimizer. Always available. No LLM.
  - **Layer 2 (Interpretive):** Fine-tuned trading LLM via Ollama. Optional. SEPARATE SCOPING SESSION NEEDED.
- **Three modes:** (1) User Query, (2) Auto-Discovery w/ permutation gate, (3) Settings Optimizer w/ Calmar fitness
- **Plugin interface:** `compute_signals()`, `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document`
- **Backlog:** P1.7 "Plugin interface spec" = WAITING (blocked by concept approval)
- **STATUS: CONCEPT WRITTEN, NOT YET APPROVED FOR BUILD**

**NOTE:** `TOPIC-vince-v2.md` line 5 incorrectly says "APPROVED 2026-02-23." The concept doc header says "not yet approved for build." The 2026-02-24 todo log confirms not approved. This needs fixing.

### C. Existing Reusable Infrastructure (PRODUCTION)

Backtester v3.8.4, signal pipeline v383 (Numba JIT), BBW pipeline (Layers 1-5), dashboard v3.9.2, commission model, AVWAP tracker, data (399 coins, multiple periods), PostgreSQL schema — all production and available for v2.

### D. Existing Plugin Interface (PARTIAL, v1 CONTRACT)

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\base.py` — 6 abstract methods designed for v1 classification
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\strategies\four_pillars.py` — 215 lines, wraps signals + backtester
- **GAP:** The existing interface has `extract_features()`, `label_trades()`, `get_backtester_params()` (v1 classifier methods). v2 needs `parameter_space()`, `trade_schema()`, `run_backtest()`, `strategy_document` instead. Different contracts.

---

## 2. What's Reusable from v1 in v2

| v1 Module | v2 Use | Confidence |
|-----------|--------|------------|
| `features_v3.py` (27 features) | Enricher — indicator snapshots at entry/MFE/exit | HIGH (needs multi-bar adaptation) |
| `triple_barrier.py` | PnL Reversal Analysis labeling | HIGH |
| `purged_cv.py` | Permutation testing / validation | HIGH |
| `walk_forward.py` | Mode 3 optimizer training/test split | HIGH |
| `loser_analysis.py` | PnL Reversal Analysis (Panel 2) | HIGH |
| `coin_features.py` | Coin Scorecard (Panel 1) | MEDIUM |
| `strategies/four_pillars.py` (enrich_ohlcv, compute_signals impls) | Four Pillars plugin | HIGH (new contract, same internals) |

**NOT reusable:** `vince_model.py` (PyTorch), `training_pipeline.py`, `meta_label.py`, `bet_sizing*.py`, `xgboost_trainer*.py`, all staging files — these are v1 classifier-specific.

---

## 3. Decision Log

### Decided (firm)

| Decision | Date |
|----------|------|
| Vince is NOT a classifier (no TAKE/SKIP) | 2026-02-18 |
| Never reduce trade count (volume = rebate) | 2026-02-18 |
| Strategy-agnostic plugin architecture | 2026-02-20 |
| Two-layer architecture (quant + LLM) | 2026-02-20 |
| Three operating modes | 2026-02-19 |
| Tab 3 is informational only (not a filter) | 2026-02-24 |
| Trading LLM is separate build track | 2026-02-20 |
| Permutation significance gate for Mode 2 | 2026-02-24 (spec review) |
| Calmar fitness for Mode 3 | 2026-02-24 (spec review) |
| K4 buckets derived from data, not intuited | 2026-02-24 (spec review) |

### NOT Decided (open)

| Question | Blocked By |
|----------|------------|
| Concept v2 approved for build? | User action |
| 6-module architecture formally approved? | Concept approval |
| Mode 3 optimizer method (Optuna confirmed?) | User preference |
| Dashboard UX (what user clicks) | Concept approval |
| Monthly coin suitability — v1 or later? | User preference |
| Rolling regime detection — v1 or later? | User preference |
| Trading LLM fine-tuning scope | Separate session |

---

## 4. Document Conflicts to Fix

| Document | Problem | Action |
|----------|---------|--------|
| `TOPIC-vince-v2.md` line 5 | Says "APPROVED" — wrong | Fix to "WRITTEN 2026-02-23, NOT YET APPROVED FOR BUILD" |
| `SPEC-C-VINCE-ML.md` | Describes v1 classifier architecture, contradicts v2 | Mark header SUPERSEDED BY v2 concept |
| `BUILD-VINCE-ML.md` | 984-line build spec for v1 classifier pipeline | Mark ARCHIVED |
| `PRODUCT-BACKLOG.md` P1.2 | "Deploy staging files" = READY | Re-evaluate: staging files are v1 code |

---

## 5. Recommended Next Actions (ordered)

1. **Fix TOPIC file contradiction** — correct "APPROVED" to "NOT YET APPROVED FOR BUILD" in `TOPIC-vince-v2.md`
2. **User reads and approves concept v2** — `docs/VINCE-V2-CONCEPT-v2.md`. Single biggest blocker. Everything is downstream.
3. **Mark SPEC-C and BUILD-VINCE-ML as superseded/archived** — prevent future sessions from building v1
4. **Re-evaluate P1.2** — staging deployment of v1 classifier code serves no purpose under v2 direction
5. **Formal plugin interface spec (P1.7)** — first real build artifact for v2. Reconcile existing `strategies/base.py` with v2 contract.
6. **Scope trading LLM** — can run in parallel. DeepSeek-R1 response still needed (Qwen3 collected). Fine-tuning dataset, eval criteria TBD.
7. **Begin v2 build** — order: plugin interface -> Enricher -> Analyzer -> Dashboard skeleton -> Optimizer -> Validator -> LLM integration (last)

---

## Verification

- Read `docs/VINCE-V2-CONCEPT-v2.md` header to confirm "not yet approved" status
- Check `TOPIC-vince-v2.md` is corrected after Step 1
- Check `SPEC-C-VINCE-ML.md` and `BUILD-VINCE-ML.md` headers after Step 3
- Check `PRODUCT-BACKLOG.md` P1.2 status after Step 4
