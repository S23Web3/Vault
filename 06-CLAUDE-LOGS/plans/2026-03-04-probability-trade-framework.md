# Probability-Based Trade Signal Detection: Markov + Black-Scholes
**Date:** 2026-03-04
**Status:** CONCEPT — theoretical framework, not yet implemented
**Applies to:** All trade types (1m scalps primary, trend-hold secondary)

---

## Core Idea

Replace hard-coded indicator thresholds with learned transition probabilities. Instead of "if delta < X AND stoch < 20 AND TDI crosses MA → trade", the system learns: "when the market is in combined state S, the probability of transitioning to a profitable entry state is P(S→entry)."

Black-Scholes probability math complements this by providing continuous probability estimates: "given the current delta and volatility, what is the probability of a crossover within N bars?" and "given entry, what is P(hit TP before SL)?"

---

## Why Markov Fits Trading State Machines

The strategy already operates as a state machine:
- FLAT → MONITORING → IN TRADE → TREND HOLD → EXIT (trend-hold type)
- WIDE → NARROWING → THRESHOLD → CROSSED → EXPANDING (1m delta scalp)

Both are sequences of discrete states with transitions. Markov formalizes this by learning transition probabilities from data instead of defining them manually.

---

## Observable State Variables

### EMA Delta Regime (5 states)
| State | Condition |
|-------|-----------|
| WIDE | Delta > upper_threshold (far from crossover) |
| NARROWING | Delta decreasing toward threshold |
| THRESHOLD | Delta within crossover approach zone |
| CROSSED | EMAs have crossed (delta sign flipped) |
| EXPANDING | Delta growing in new direction post-cross |

### Stochastic Zone (5 states)
| State | Condition |
|-------|-----------|
| NEUTRAL | All stochs mid-range (20-80) |
| ENTERING_OS | Fast stochs (9/14) crossing below 20 |
| IN_OS | Multiple stochs below 20 |
| ENTERING_OB | Fast stochs (9/14) crossing above 80 |
| IN_OB | Multiple stochs above 80 |

### TDI Position (3 states)
| State | Condition |
|-------|-----------|
| ABOVE_MA | TDI price line above its moving average |
| NEAR_MA | TDI price line within threshold of MA |
| BELOW_MA | TDI price line below its moving average |

### Combined State Space
- 5 x 5 x 3 = **75 possible combined states**
- Each bar maps to exactly one combined state
- Transition matrix: 75 x 75 = 5,625 entries

---

## Two Markov Approaches

### Approach 1: Observable Markov Chain (simpler)

States are directly observable from indicator values. Train by counting transitions in historical data.

**Training:**
1. Compute all three indicator state values for every bar in historical data
2. Count transitions: how many times did state (NARROWING, IN_OS, NEAR_MA) transition to (THRESHOLD, IN_OS, BELOW_MA)?
3. Normalize to get probabilities
4. Result: a 75x75 transition probability matrix

**Use:**
- At each bar, look up current combined state
- Check P(current_state → favorable_entry_state)
- If probability exceeds confidence threshold → signal fires

**Advantages:** Simple, interpretable, fast to compute
**Disadvantage:** Cannot detect hidden regimes (choppy vs trending market)

### Approach 2: Hidden Markov Model (more powerful)

The "true" market regime is HIDDEN. What we observe are the indicator states. HMM infers the hidden regime.

**Hidden states (latent — learned, not predefined):**
- Regime A: Trending (crossovers lead to follow-through)
- Regime B: Choppy (crossovers fail, mean-revert)
- Regime C: Transitioning (about to shift from choppy to trending or vice versa)

**Observations:** The 75 combined states from the observable indicators.

**Training:**
1. Use Baum-Welch algorithm (EM) on historical data
2. Algorithm learns:
   - Transition matrix between hidden states (3x3)
   - Emission matrix: P(observable_state | hidden_state) (3x75)
   - Initial state probabilities

**Use:**
- At each bar, use Viterbi algorithm or forward algorithm to infer current hidden state
- If hidden state = TRENDING and observable state = THRESHOLD + IN_OS + NEAR_MA → high confidence entry
- If hidden state = CHOPPY with same observables → skip or reduce size

**Advantages:** Detects regime, filters noise, adapts to market conditions
**Disadvantage:** More complex, requires careful validation to avoid overfitting

---

## Black-Scholes Probability Framework

Black-Scholes provides continuous probability estimates that complement Markov's discrete state transitions. Where Markov answers "what state is likely next?", BS answers "what is the probability of reaching a specific price level within a timeframe?"

### Application 1: Crossover Probability

Given current EMA delta and volatility, estimate P(crossover within N bars).

The EMA delta behaves like a mean-reverting spread. Using the BS framework:
- Delta = current distance between EMAs (e.g., EMA55 - EMA89)
- Sigma = volatility of the delta itself (computed from recent delta changes)
- Target = 0 (crossover = delta reaches zero)

**Formula (simplified):**
```
d = delta / (sigma * sqrt(N))
P(cross within N bars) = 2 * Phi(-|d|)
```
Where Phi is the standard normal CDF.

**Use:** When Markov says "we're in NARROWING state", BS quantifies HOW likely the cross is within 5, 10, 20 bars. This turns a binary state into a probability curve.

### Application 2: SL/TP Expected Value

Given entry price, SL distance, and TP distance, compute P(hit TP before SL).

This is the classic first-passage-time problem:
- Entry at price P
- TP at P + T (long) or P - T (short)
- SL at P - S (long) or P + S (short)
- Sigma = ATR-derived volatility
- Mu = drift (estimated from recent price trend)

**Formula:**
```
With drift mu and volatility sigma:
P(hit TP first) = [1 - exp(-2*mu*S/sigma^2)] / [exp(2*mu*T/sigma^2) - exp(-2*mu*S/sigma^2)]

With zero drift (simplified):
P(hit TP first) = S / (S + T)
```

**Use:** Before entering, compute whether the R:R is actually favorable given current volatility. A 2:1 R:R with zero drift = 33% win rate — break even. The drift term from trend detection (Markov hidden state = TRENDING) shifts this favorably.

### Application 3: Time-to-Target

Estimate expected time to reach Ripster Cloud milestone levels.

- Current price P
- Cloud 2 level at C2, Cloud 3 at C3, Cloud 4 at C4
- Sigma from ATR
- Drift from trend strength

**Use:** After gate opens (stoch 60 confirms trend), estimate how long the trade needs to reach each cloud level. Informs whether to use tight trail (target close) or wide trail (target far, needs patience).

### Application 4: The BBWP-to-BS Bridge

This is the key insight connecting the existing BBW module to probability math.

**BBWP percentile = where sigma sits in its historical distribution.**

- BBWP at 10th percentile → sigma is LOW relative to history → small moves expected
- BBWP at 90th percentile → sigma is HIGH → large moves expected
- BBWP spectrum color encodes this: blue/dark blue = low sigma, red = high sigma

**The bridge:**
1. BBWP percentile → map to current sigma regime
2. Current sigma → feed into BS formulas above
3. BS output → P(crossover), P(TP before SL), expected time-to-target

**This potentially answers BBW-1 computationally.** Instead of manually defining "what BBWP threshold means healthy vs extreme", the BS probability output naturally separates them:
- Low BBWP → low sigma → low P(crossover) → don't trade (the move won't come)
- Mid BBWP → moderate sigma → favorable P(crossover) → trade zone
- High BBWP → high sigma → high P(crossover) BUT also high P(SL hit) → tighten management

The thresholds emerge from the math rather than being manually defined.

---

## Three-Layer Probability Architecture

| Layer | Method | Answers | Speed |
|-------|--------|---------|-------|
| 1. Hard thresholds | Current system (delta < X, stoch < 20) | Binary yes/no | Instant |
| 2. Markov | Transition probabilities from historical state sequences | "What state comes next?" | O(1) lookup |
| 3. Black-Scholes | Continuous probability from volatility math | "What's the probability of reaching target?" | O(1) formula |

**Combined signal:**
- Layer 1 provides the initial filter (discard obviously wrong setups)
- Layer 2 provides regime context (is this a trending or choppy market?)
- Layer 3 provides precise probability (is this specific trade worth taking?)

All three must agree for highest confidence. Layer 1 alone = current system. Adding Layer 2 = regime-aware. Adding Layer 3 = probability-calibrated.

---

## Implementation Architecture

### Data Requirements
- 1m OHLCV data (already have 399 coins in cache)
- Need: EMA55, EMA89, Stoch 9/14/40/60, TDI (RSI9 smoothed, signal line, BB34)
- All computable from existing OHLCV data — no new data needed

### Compute: State Encoding
```
For each bar:
  1. Compute EMA55, EMA89 → delta = EMA55 - EMA89
  2. Classify delta_regime from delta value and delta change
  3. Compute stoch K values → classify stoch_zone
  4. Compute TDI price line and MA → classify tdi_position
  5. Combined state = (delta_regime, stoch_zone, tdi_position) → integer 0-74
```

### Compute: Transition Matrix (Observable Markov)
```
For each coin's historical data:
  Count transitions[state_t][state_t+1] += 1
  Normalize each row to sum to 1

Optional: pool across all coins for a "universal" matrix
Optional: per-coin matrices for coin-specific behavior
```

### Compute: HMM (if using Approach 2)
```
Library: hmmlearn (Python, scikit-learn compatible)
  from hmmlearn import hmm
  model = hmm.CategoricalHMM(n_components=3)  # 3 hidden states
  model.fit(observation_sequences)
```

### Compute: Black-Scholes Probabilities
```
Library: scipy.stats (norm.cdf for Phi)
  from scipy.stats import norm
  import numpy as np

  # Crossover probability
  delta = ema55 - ema89
  sigma_delta = np.std(delta_changes[-20:])  # recent delta volatility
  d = delta / (sigma_delta * np.sqrt(N))
  p_cross = 2 * norm.cdf(-abs(d))

  # TP/SL probability (with drift)
  mu = np.mean(returns[-20:])  # recent drift
  sigma = atr / price  # normalized volatility
  # First passage time formula
```

### Signal Generation
```
At each bar:
  current_state = encode(delta, stoch, tdi)

  # Layer 1: Hard threshold filter
  if not passes_basic_filter(delta, stoch, tdi): SKIP

  # Layer 2: Markov regime
  p_entry = transition_matrix[current_state][ENTRY_STATES].sum()
  hidden_state = hmm_model.predict(recent_observations)

  # Layer 3: BS probability
  p_cross = bs_crossover_probability(delta, sigma_delta, N=10)
  p_tp = bs_tp_probability(sl_distance, tp_distance, sigma, mu)

  # Combined decision
  if hidden_state == TRENDING and p_entry > markov_threshold and p_cross > bs_threshold:
    SIGNAL (confidence = p_entry * p_tp)
```

---

## What Vince Optimizes

### Observable Markov
| Parameter | Description |
|-----------|-------------|
| confidence_threshold | Minimum P(→entry) to fire signal |
| state_discretization | How to bin continuous values into discrete states |
| lookback for transitions | How many bars of history to build the matrix from |
| per-coin vs universal | Coin-specific matrices vs pooled across all coins |

### HMM
| Parameter | Description |
|-----------|-------------|
| n_hidden_states | Number of latent regimes (start with 3) |
| confidence_threshold | Minimum probability to fire |
| retraining_window | How often to retrain (daily? weekly? rolling?) |
| observation_encoding | How to discretize continuous indicators into states |

### Black-Scholes
| Parameter | Description |
|-----------|-------------|
| sigma_lookback | How many bars of recent data to estimate volatility (20? 50?) |
| drift_lookback | How many bars to estimate trend drift |
| bs_threshold | Minimum P(crossover) to consider setup valid |
| tp_sl_ratio_threshold | Minimum P(TP before SL) to take the trade |

---

## Application to Both Trade Types

### 1m Delta Scalp (Primary)
- High bar count = rich transition data
- All conditions quantifiable = clean state encoding
- Short hold time = fast feedback for validation
- Full automation target = probability framework fits perfectly
- BS crossover probability directly answers "is this delta narrowing likely to produce a cross?"

### Trend-Hold (5m)
- The Stoch 60 gate is already a state transition
- BBW health states (HEALTHY → EXTREME → EXIT) are Markov-compatible
- TDI 2-candle rule = a 2-step transition check
- Could use HMM to detect "is this a real trend-hold or will the gate fail?"
- BS time-to-target estimates how long to reach cloud milestones
- BS SL/TP probability validates whether the R:R is actually favorable

### Potential for Unified Model
- Same probability framework, different state definitions per trade type
- Train separate models for 1m and 5m
- The hidden regime detection could be SHARED — "is the market trending on this coin right now?" applies to both types
- BBWP-to-BS bridge works across both timeframes

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Overfitting to historical transitions | Walk-forward validation, per-coin vs universal comparison |
| State space too large (75 states sparse) | Reduce states (merge similar ones), or use continuous HMM |
| Non-stationary markets | Rolling retraining window, regime-aware model |
| Computational cost | Observable Markov is O(1) lookup — fast. HMM forward pass is O(N*K^2) per bar — still fast for K=3. BS is O(1) per formula. |
| Complexity without benefit | Benchmark against hard-threshold baseline. If probability framework doesn't beat simple rules, don't use it. |
| BS assumptions violated | BS assumes log-normal returns and constant volatility. Crypto violates both. Mitigation: use BS as approximation, not gospel. Rolling sigma partially handles non-constant volatility. Fat tails mean BS underestimates extreme moves — conservative for SL/TP estimation (actual P(SL hit) slightly higher than BS predicts). |
| Over-engineering | Start with Layer 1 + Layer 2 only. Add Layer 3 (BS) only if Layer 2 alone doesn't beat baseline. |

---

## Existing Tools in the System

- **hmmlearn**: Standard Python HMM library (pip install hmmlearn)
- **scipy.stats**: Normal CDF for BS calculations (already in most environments)
- **NumPy**: Transition matrix computation, sigma estimation
- **RTX 3060**: Not needed for Markov/BS (CPU-bound, matrix operations). Could use CUDA sweep engine to sweep threshold parameters across coins.
- **BBW 5-layer module**: Already computes regime-like features — could feed into state encoding AND provide sigma for BS
- **CUDA sweep engine**: Could sweep confidence_threshold parameter across coins

---

## What This Document Is NOT

- This is NOT a build spec — no code to be written yet
- This is NOT validated — needs backtesting to prove value over simple thresholds
- The state definitions are proposals, not confirmed rules
- Must prove probability framework adds value vs hard thresholds before building into strategy
- BS formulas are simplified — real implementation may need adjustments for crypto-specific behavior
