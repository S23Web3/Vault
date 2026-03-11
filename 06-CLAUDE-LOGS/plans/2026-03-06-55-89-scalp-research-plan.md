# Plan: 55/89 EMA Cross Scalp — Research Phase (v2)

**Date:** 2026-03-06
**Status:** PENDING APPROVAL
**Revision:** v2 — corrected after discrepancy audit

---

## Context

The user has a 1m scalp signal with 3 confirmed elements:

1. Stochastics aligned (directional momentum building as a group — probabilistic, not a binary gate)
2. 55 EMA / 89 EMA cross on 1m (BOTH are EMAs — confirmed)
3. Move SL to BE after cross

"Aligned" means: fast stochs (9, 14) already moving; slow stochs (40, 60) showing improving degree of change — could be in the zone, at the zone edge, or already past it. The K/D crossover on slow stochs is an observation within this read, not a prerequisite. The EMA delta compression is part of how alignment is read, not a separate signal.

The user wants literal Markov chain and OU diffusion models built — confirmed.

The user wants this run "as if live" — candle-by-candle replay, no lookahead.

---

## Discrepancies Found in v1 Plan (corrected in v2)

1. **89 was labelled SMA — it is EMA.** Both 55 and 89 are EMAs. Delta = EMA(55) - EMA(89). OU dynamics differ from EMA-vs-SMA.
2. **Markov states forced a zone-first path (S0 in zone -> S1 climbing -> S2 crossed -> S3 extended).** User said 40/60 "could already be moving and at the zone or moved." States must allow any starting position, not require passage through zone.
3. **"At least 2 stochs in S1 or higher" was my wording.** User described a specific fast/slow relationship (9/14 leading, 40/60 catching up), not a count threshold. The Markov model must capture which stochs are in which state, not just how many.
4. **K/D cross was placed as state S2 (prerequisite for S3).** User described K/D cross as an observation — "is a crossover happening" — not a gated progression. States should not require K/D cross as a mandatory step.
5. **EMA delta was separated from stochastic alignment.** User described them as interwoven — the delta compression is part of reading alignment, not a standalone condition.
6. **Plan said "no new indicator code needed" — wrong.** `stochastics_v2.py` only computes `stoch_60_d`. Research needs D lines for all 4 stochs with correct smoothing (9->3, 14->3, 40->4, 60->10 per position management study).
7. **"Move SL to BE after cross" is ambiguous.** Which cross? Likely the 55/89 EMA cross (the trigger), but could be a K/D cross on a stoch. Flagged — user to confirm.
8. **No initial SL — functional gap, not just "out of scope."** A live replay needs an initial SL to simulate trade survival. Without it, you can't determine if a trade lives to reach BE. Flagged — user must define before backtest phase.
9. **No exit rule — same gap.** Once at BE, what closes the trade? Without an exit, no trade P&L can be computed. Flagged.
10. **OU mean-reversion assumption may not hold.** EMA(55) - EMA(89) on trending 1m crypto data can stay one-directional for thousands of bars. mu ~ 0 is a hypothesis, not a fact. Research must test this explicitly and consider regime-switching if it fails.
11. **Independence assumption for compound probability is almost certainly wrong.** All 4 stochs use the same close/high/low — they are correlated by construction. Plan must use joint empirical distributions or copulas, not product of marginals.
12. **Markov/B-S are literal builds** — confirmed by user. Not conceptual framing.

---

## What Is In Scope

- Research methodology document (define math, states, and models on paper)
- Jupyter notebook (explore data, fit models, validate assumptions)
- Extend `stochastics_v2.py` to compute D lines for all 4 stochs (required for research)

## What Is Out Of Scope (not stated by user)

- TP rule
- Initial SL rule
- HTF filter
- BBW/TDI entry conditions
- Nothing else is added

## Flagged for User — Must Answer Before Backtest Phase

These are NOT invented conditions. They are functional gaps that prevent simulating trades:

- **Initial SL**: what value? (needed to determine if trade survives to BE)
- **Exit rule**: what closes a trade after SL moves to BE?
- **"After cross confirms"**: which cross triggers the BE move — the 55/89 EMA cross?

---

## Phase 1: Methodology Document

**Output:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\55-89-scalp-methodology.md`

### 1A. Stochastic Alignment — Markov Chain

**States per stochastic** — non-sequential, any entry point:

- ZONE: K < 20 (for long) or K > 80 (for short)
- TURNING: K slope improving (first derivative turning positive for long)
- MOVING: K actively rising/falling with improving acceleration (second derivative > 0)
- EXTENDED: K past midline (> 50 for long), strong momentum

These are NOT sequential gates — a stoch can be observed in any state at any time. The Markov chain models transitions between these states, not a required progression.

**Transition matrix**: estimate P(state_i -> state_j) for each of the 4 stochs from historical 1m data. Separate matrices per stoch period (9, 14, 40, 60) because transition speeds differ.

**Alignment definition**: a joint state observation:

- Fast stochs (9, 14): in MOVING or EXTENDED
- Slow stochs (40, 60): in TURNING, MOVING, or EXTENDED (slope improving)
- No stoch actively contradicting (K slope worsening against direction)
- EMA delta compressing toward cross (integrated, not separate)

**Joint distribution**: because all stochs share the same price data, independence is invalid. Use empirical joint state counts from historical data to estimate P(alignment state | all 4 stoch states). No product-of-marginals.

**K/D cross observation**: for each stoch, record whether K > D (or K < D for short) as an additional binary feature on the state, not a gated prerequisite.

**D line smoothing** — must match position management study:

- Stoch 9: D = SMA(K, 3)
- Stoch 14: D = SMA(K, 3)
- Stoch 40: D = SMA(K, 4)
- Stoch 60: D = SMA(K, 10)

### 1B. EMA Delta — Ornstein-Uhlenbeck Diffusion

The signal: delta = EMA(close, 55) - EMA(close, 89). Both EMAs.

**Model**: Ornstein-Uhlenbeck process:

- dDelta = theta * (mu - Delta) * dt + sigma * dW

**Key hypothesis to test**: is the delta actually mean-reverting? On trending coins it may not be. Research must:

1. Fit theta, mu, sigma on multiple coins
2. Test stationarity of the delta series (ADF test, KPSS test)
3. If non-stationary: consider regime-switching OU (different parameters for trending vs ranging periods)
4. If persistently non-stationary: OU may be the wrong model — document this finding

**Output**: P(cross within N bars | current delta, current delta velocity) — this is the probability surface the notebook must produce.

**Integration with alignment**: the delta compression is part of the alignment read, not a separate trigger. The notebook must show: when stochs are in alignment state AND delta is compressing, what is P(cross)?

### 1C. Slope / Degree of Change

"Improving slope" on stoch 40 and 60:

- First derivative: slope_N = K[i] - K[i-N]
- Second derivative (acceleration): accel = slope_N[i] - slope_N[i-M]
- "Improving" for long = acceleration > 0 (degree is increasing, regardless of whether slope is already positive)

N and M are parameters — determine from data. Research: what N values produce the most discriminative signal?

Note: "improving" does NOT require the stoch to be in the zone. It requires the rate of change to be increasing.

---

## Phase 2: Jupyter Notebook

**Output:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\notebooks\55-89-scalp-research.ipynb`

Cells:

1. Load 3-5 liquid 1m parquets from `data/historical/`
2. Compute all 4 stochs + D lines (extend `compute_all_stochastics()` or compute D inline)
3. Compute EMA(55) and EMA(89) using existing `ema()` from `signals/clouds_v2.py`
4. Compute delta = EMA55 - EMA89
5. Classify each bar into Markov states for all 4 stochs
6. Build empirical joint state distribution (not product of marginals)
7. Estimate Markov transition matrices per stoch period
8. Stationarity tests on delta series (ADF, KPSS) — per coin
9. Fit OU parameters (theta, mu, sigma) — per coin, flag non-stationary cases
10. Probability surface: P(cross within N bars) as function of (delta, delta_velocity)
11. Combined view: when alignment state is active AND delta compressing, overlay actual cross events
12. Sensitivity analysis on slope window parameter N

---

## Existing Code to Reuse

| What                       | File                       | Function                     |
|----------------------------|----------------------------|------------------------------|
| Raw K stochastic (all 4)   | `signals/stochastics_v2.py` | `compute_all_stochastics()` |
| EMA (JIT, matches Pine)    | `signals/clouds_v2.py`     | `ema()`                      |
| 1m parquet data            | `data/historical/*.parquet` | pandas read_parquet          |

## New Code Required

| What                        | Why                                                                                                                                       |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| D lines for stochs 9, 14, 40 | `stochastics_v2.py` only has `stoch_60_d`. Need D = SMA(K, smooth) for all 4, with correct smoothing per position management study. |

---

## Files to Create

| File                                  | Phase                             |
|---------------------------------------|-----------------------------------|
| `research/55-89-scalp-methodology.md` | 1 — math definitions, no code    |
| `notebooks/55-89-scalp-research.ipynb` | 2 — after methodology approved   |

---

## Verification

- Methodology doc: user reads and approves state definitions + model choices before code
- Notebook: all cells run top to bottom, no errors
- Stationarity tests produce p-values (not assumed)
- OU fit produces finite theta/sigma with confidence intervals
- Markov matrix rows sum to 1.0
- Joint distribution is empirical, not product of marginals
- Probability surface renders as heatmap with cross events overlaid
