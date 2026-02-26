# Vince V2 ML Spec Review — Research & Fixes
**Date:** 2026-02-24
**Files reviewed:**
- `docs/VINCE-V2-CONCEPT.md` (v1, superseded)
- `docs/VINCE-V2-CONCEPT-v2.md` (v2, corrected)
- `SPEC-C-VINCE-ML.md`
- `.claude/skills/vince-ml/SKILL.md` + all references
- Full project tree scan (ml/, scripts/, docs/, staging/)

**Objective:** Thorough research and identification of whether the ML spec is on the right track.

---

## Taxonomy — What the Spec Actually Is

The Vince architecture blends three distinct paradigms:

| Component | Category | ML? |
|-----------|----------|-----|
| Mode 1 / Mode 2 (constellation query) | Exploratory data analysis + frequency counting | No |
| Mode 3 (Optuna sweep) | Bayesian hyperparameter optimization | ML-adjacent |
| SPEC-C (XGBoost + PyTorch) | Predictive classification model | Yes |

---

## What Was Already Right (no changes needed)

1. **"Always show N" constraint** — prevents the entire class of errors where small-sample patterns are surfaced as signal
2. **Complement always alongside the pattern** — proper A/B reasoning
3. **Trade count floor in optimizer** — protects rebate model during parameter sweep
4. **Two-sided Monte Carlo** — trade shuffle (order dependency) + candle bootstrap (regime dependence)
5. **ETD tracking** — most diagnostic exit metric; absent from most retail tools
6. **Strategy-agnostic plugin architecture** — correct separation of concerns
7. **XGBoost as adversarial auditor** — feature importance consensus between structurally different models
8. **Coin pool split 60/20/20 with holdout** — De Prado methodology, correct for coin-level learning

---

## Self-Evaluation of Recommendations

Before applying fixes, each recommendation was evaluated for accuracy:

| # | Recommendation | Verdict | Reasoning |
|---|---------------|---------|-----------|
| 1 | Mode 2 needs permutation test | **DEFINITIVE FIX** | Multiple comparisons without correction guarantees spurious patterns. Infrastructure exists. |
| 2 | Mode 3 fitness function unspecified | **DEFINITIVE FIX** | Calmar with rebate and trade count floor satisfies all three stated constraints. No weighting required. |
| 3 | SPEC-C vs VINCE-V2 classifier conflict | **USER DECISION** | Tab 3 "entry filter recommendations" contradicts "NOT a classifier." |
| 4 | 55% accuracy gate wrong metric | **OVERSTATED** | It's a training sanity check, not a deployment threshold. Non-filtering system. Acceptable. |
| 5 | LSTM for 15-bar sequences suboptimal | **OVERSTATED** | SPEC-C already says "LSTM or Transformer." Not locked in. Non-issue. |
| 6 | K4 bucket boundaries intuited | **DEFINITIVE FIX** | Decision tree derivation is a concrete pre-build step. |

Items 4 and 5 were dropped — no changes applied.

---

## Changes Applied

### 1. `docs/VINCE-V2-CONCEPT-v2.md` — Mode 2 Permutation Gate

**Before:** "Controls: effect size threshold (user-set), minimum N threshold (user-set)"

**After:** Added significance gate requiring permutation baseline — shuffle trade outcome labels, run same sweep, record empirical null distribution of deltas. Only surface patterns where real delta exceeds 95th percentile of permuted distribution. Uses existing Monte Carlo trade shuffle infrastructure. User-set thresholds layer on top, not instead.

**Why:** With 15+ binary/trinary constellation dimensions, millions of combinations are searched. Without correction, top-N patterns will include false discoveries. The permutation test provides a data-driven significance threshold that adapts to the actual search space. De Prado addresses this as "Deflation of the Sharpe Ratio."

### 2. `docs/VINCE-V2-CONCEPT-v2.md` — Mode 3 Fitness Function

**Before:** "Fitness function defined at build time. Constraints: (1) trade count must not decrease below baseline, (2) rebate must be factored, (3) win rate alone is not valid."

**After:** Defined explicitly — Calmar ratio with rebate:
```
if trade_count < baseline_trade_count * 0.95:
    return -inf  # hard rejection

net_pnl_with_rebate = gross_pnl - commissions + rebate_income
score = net_pnl_with_rebate / max_drawdown_dollars
```

**Why:** Calmar penalises drawdown naturally without requiring tuned composite weights. Rebate in the numerator satisfies constraint (2). Trade count floor is a hard rejection before scoring begins, not a soft penalty. Win rate is absent from the formula, satisfying constraint (3). No ambiguity at build time.

### 3. `docs/VINCE-V2-CONCEPT-v2.md` — K4 Regime Bucket Derivation

**Before:** "These are hypotheses. Vince tests them. The data decides." (vague)

**After:** Added concrete 5-step pre-build procedure:
1. Plot win rate vs continuous macro signal value (rolling mean)
2. Fit supervised decision tree (macro_signal → outcome) to 3–4 splits
3. Use empirical split points as bucket boundaries
4. Replace intuited values (25/45/55/75) with data-derived ones
5. Document derivation date and dataset used

**Why:** Intuited boundaries are a fine starting hypothesis, but the spec lacked a method to validate or replace them. A decision tree on K4 with 20K+ trades per coin will find natural regime boundaries in seconds. The boundaries will differ per coin universe and time window, so the derivation must be documented and stored.

### 4. `SPEC-C-VINCE-ML.md` — Tab 3 Relabelled

**Before:** "Entry filter recommendations ('reject trades where stoch9 > 70 AND ripster_expanding = False')"

**After:** "Research findings panel: surfaces indicator conditions statistically associated with losing trades. Informational only — no trade is rejected by Vince. Trade count is never reduced by this output. TAKE/SKIP decisions are Vicky's domain — separate build."

**Why:** User chose "Informational only" to resolve the Vince/Vicky conflict. Vince surfaces findings. The user reads them and decides. Trade count is never reduced.

---

## Overall Assessment

The spec is on the right track. The statistical reasoning and architectural decisions are sound. The main gaps were:
- No formal correction for the multiple hypothesis testing problem in Mode 2 (fixed)
- No explicit fitness function for Mode 3 optimizer (fixed)
- Architectural contradiction between SPEC-C and VINCE-V2 on trade filtering (resolved)
- Regime bucket boundaries specified without a derivation method (fixed)

No structural redesign needed. No paradigm changes needed. Four targeted fixes applied.
