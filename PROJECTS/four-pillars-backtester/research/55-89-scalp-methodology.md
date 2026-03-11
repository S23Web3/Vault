# 55/89 EMA Cross Scalp — Research Methodology

**Date:** 2026-03-06
**Status:** DRAFT — awaiting user approval before any code is written
**Signal source:** User-stated, 3 elements only. No additions.

---

## The Signal (exactly as stated)

1. Stochastics aligned (directional momentum building as a group)
2. 55 EMA / 89 EMA cross on 1m
3. Move SL to BE after cross

---

## UML — Research Flow

```
1m Candle Arrives
    |
    v
+---------------------------+
| Compute Stoch 9 K + D     |
| (lightweight — always on) |
+---------------------------+
    |
    v
+---------------------------+
| Stoch 9 K/D Cross?        |
| K crossed above D (long)  |
| or below D (short)?       |
+---------------------------+
    |
    +----------+----------+
    |                     |
 No |                  Yes|
    v                     v
 [IDLE]           +---------------------------+
  (wait)          | MONITORING ACTIVATED       |
                  | t=0: stoch 9 fired         |
                  |                            |
                  | Now compute everything:    |
                  | - Stoch 14/40/60 K + D     |
                  | - Slope/accel (40, 60)     |
                  | - EMA(55), EMA(89), delta  |
                  | - BBWP + Spectrum MA       |
                  | - TDI price vs MA          |
                  +---------------------------+
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
     +-------------+ +-------------+ +-------------+
     | Stoch State | | BBW State   | | TDI State   |
     | 14: state   | | HEALTHY /   | | CONFIRMING /|
     | 40: state + | | EXTREME /   | | OPPOSING    |
     |   slope/acc | | QUIET       | |             |
     | 60: state + | |             | |             |
     |   slope/acc | |             | |             |
     +-------------+ +-------------+ +-------------+
              |               |               |
              +-------+-------+-------+-------+
                      |
                      v
            +---------------------+
            | Alignment Check     |
            | 14: MOVE/EXT?       |
            | 40,60: TURN+?       |
            | No contradiction?   |
            | Delta compressing?  |
            | TDI confirming?     |
            | BBW not QUIET?      |
            +---------------------+
                      |
               +------+------+
               |             |
            No |          Yes|
               v             v
     +--------------+  +--------------------+
     | Still        |  | ALIGNMENT ACTIVE   |
     | MONITORING   |  +--------------------+
     | (check if    |           |
     | stoch 9      |  +--------+--------+--------+
     | reversed)    |  |        |        |        |
     +--------------+  v        v        v        v
            |   +--------+ +------+ +-------+ +-----+
            |   | Markov | | OU   | | Joint | | MC  |
            |   | trans  | | diff | | empir | | sim |
            |   | matrix | | fit  | | dist  | |     |
            |   +--------+ +------+ +-------+ +-----+
            |        |        |        |        |
            |        +--------+--------+--------+
            |                          |
            v                          v
  +------------------+    +----------------------+
  | Stoch 9 reversed |    | Monte Carlo          |
  | K crossed back?  |    | 10,000+ paths from   |
  +------------------+    | t=0 (stoch 9 fired): |
            |             |                      |
         Yes|             | P(full alignment +   |
            v             |   EMA cross within   |
         [IDLE]           |   N bars before      |
         (pipeline        |   stoch 9 reverses)  |
          shuts down)     +----------------------+
                                     |
                                     v
                          +----------------------+
                          | Vince State Output   |
                          |                      |
                          | System state:        |
                          |   IDLE / MONITORING  |
                          |   / READY            |
                          |                      |
                          | Per bar (when not     |
                          | IDLE):               |
                          | - bars_since_alert   |
                          | - stoch states       |
                          | - alignment state    |
                          | - bbw_state          |
                          | - tdi_state          |
                          | - ema_delta_state    |
                          | - p_cross_5/10/20/50 |
                          | - p_aligned_at_cross |
                          +----------------------+
                                     |
                                     v
                          +----------------------+
                          | Validation           |
                          |                      |
                          | Train/test split     |
                          | Calibration plot     |
                          | Brier score          |
                          | MC prediction vs     |
                          | actual outcomes      |
                          +----------------------+
```

**What this UML represents:** the full research pipeline, gated by stoch 9. The system is IDLE until stoch 9 K/D cross fires — that is time-zero. Only then does the full indicator computation, state classification, alignment check, and Monte Carlo simulation run. If stoch 9 reverses before alignment completes, the pipeline shuts down and returns to IDLE. The output is a state vector Vince can read, with the core MC question: given stoch 9 just fired, what is P(full alignment + EMA cross before stoch 9 reverses)?

---

## 1. Stochastic Alignment — Markov Chain Model

### 1.1 What "Aligned" Means

Alignment is a probabilistic read of the 4 stochastics (9, 14, 40, 60) collectively showing directional intent. It is NOT:

- A binary all-4-crossed gate
- A count threshold ("at least N stochs crossed")
- A zone requirement ("must start from oversold/overbought")

It IS:

- Fast stochs (9, 14) already moving in the direction
- Slow stochs (40, 60) showing improving degree of change — they could be in the zone, at the zone edge, or already past it
- K/D crossover status is an observation within the read, not a prerequisite
- The EMA delta compression is part of this read, not a separate signal

### 1.2 Markov States

Each of the 4 stochastics is classified into one of 4 states at every 1m bar. These states are non-sequential — a stochastic can be in any state at any time, and can transition to any other state.

**For a LONG signal:**

| State | Label | Definition |
|-------|-------|------------|
| ZONE | In the zone | K < 20 |
| TURNING | Slope improving | K slope (first derivative) is positive, but acceleration may be zero or low |
| MOVING | Accelerating | K slope is positive AND acceleration (second derivative) > 0 |
| EXTENDED | Past midline | K > 50 with positive slope |

**For a SHORT signal:** mirror all conditions (K > 80 for ZONE, negative slopes, K < 50 for EXTENDED).

**Important**: TURNING does NOT require the stoch to be in or near the zone. A stoch at K=45 with improving slope is TURNING. The zone is just one possible starting point.

### 1.3 Additional Features Per State (not gating conditions)

At each bar, for each stochastic, also record:

- **K > D**: boolean. Whether K is above D (long) or below D (short). This is an observation, not a state gate.
- **K value**: the raw K value (0-100 scale)
- **K slope**: first derivative of K over N bars
- **K acceleration**: second derivative of K

These features enrich the Markov state but do not restrict transitions.

### 1.4 D Line Computation

D lines must be computed for all 4 stochastics with correct smoothing periods (from the position management study):

| Stochastic | K period | D smoothing | D = SMA(K, smooth) |
|------------|----------|-------------|---------------------|
| Stoch 9 | 9 | 3 | SMA(K_9, 3) |
| Stoch 14 | 14 | 3 | SMA(K_14, 3) |
| Stoch 40 | 40 | 4 | SMA(K_40, 4) |
| Stoch 60 | 60 | 10 | SMA(K_60, 10) |

Note: `stochastics_v2.py` currently only computes `stoch_60_d`. The notebook must compute D for all 4.

### 1.5 Transition Matrix

For each stochastic period (9, 14, 40, 60), estimate a 4x4 transition matrix from historical 1m data:

```
         ZONE   TURNING  MOVING  EXTENDED
ZONE     p00    p01      p02     p03
TURNING  p10    p11      p12     p13
MOVING   p20    p21      p22     p23
EXTENDED p30    p31      p32     p33
```

Each row sums to 1.0. Separate matrices per stoch because transition speeds differ (stoch 9 transitions much faster than stoch 60).

Estimation method: count observed transitions in historical data, normalize to probabilities. Minimum sample: 10,000 transitions per cell for statistical significance.

### 1.6 Joint State Distribution

Because all 4 stochastics are computed from the same close/high/low data, they are correlated by construction. The probability of a joint state (e.g., stoch 9 in MOVING, stoch 14 in MOVING, stoch 40 in TURNING, stoch 60 in ZONE) CANNOT be estimated as the product of individual state probabilities.

Instead: build an empirical joint distribution by counting how often each combination of (state_9, state_14, state_40, state_60) occurs in historical data. With 4 states per stochastic and 4 stochastics, this is a 4^4 = 256-cell distribution.

Some cells will be very rare or empty — that is expected and informative (e.g., stoch 9 in ZONE while stoch 60 in EXTENDED should be rare for the same direction).

### 1.7 Alignment Definition (for research validation)

Alignment is only evaluated after stoch 9 K/D cross has fired (section 5). Stoch 9 is the gate — it is not part of the alignment check. It already fired.

A bar is in "alignment" for long when (stoch 9 alert already active):

- Stoch 14: in MOVING or EXTENDED
- Stoch 40: in TURNING, MOVING, or EXTENDED (slope improving)
- Stoch 60: in TURNING, MOVING, or EXTENDED (slope improving)
- No stoch has a negative K slope (contradiction check)
- EMA delta (section 2) is compressing toward zero or has just crossed
- TDI on correct side of MA (section 4)
- BBW not QUIET (section 6)

This is the definition to test against historical EMA crosses. The research question: given stoch 9 has fired, when alignment is present, how often does a 55/89 EMA cross follow within N bars before stoch 9 reverses?

---

## 2. EMA Delta — Ornstein-Uhlenbeck Diffusion Model

### 2.1 The Delta

delta(t) = EMA(close, 55) - EMA(close, 89)

Both are exponential moving averages. When delta crosses zero, the 55 EMA has crossed the 89 EMA.

### 2.2 Ornstein-Uhlenbeck Model

Model the delta as a mean-reverting stochastic process:

```
dDelta = theta * (mu - Delta) * dt + sigma * dW
```

Where:

- theta = mean-reversion speed (how quickly delta reverts toward mu)
- mu = long-run mean of the delta process
- sigma = volatility of the delta process
- dW = Wiener process increment (random noise)

### 2.3 Parameter Estimation

From discrete 1m data, estimate via maximum likelihood:

- theta_hat = -log(rho) / dt, where rho = lag-1 autocorrelation of delta
- mu_hat = mean(delta)
- sigma_hat = std(delta_residuals) * sqrt(2 * theta / (1 - rho^2))

Where dt = 1 (one bar interval).

### 2.4 Hypothesis: Is the Delta Mean-Reverting?

This is NOT assumed — it must be tested. On trending coins, the delta can stay positive or negative for thousands of bars. If it is not mean-reverting, the OU model is wrong.

Tests to run per coin:

1. **Augmented Dickey-Fuller (ADF)**: null hypothesis = unit root (non-stationary). If p < 0.05, reject null, conclude stationary.
2. **KPSS test**: null hypothesis = stationary. If p < 0.05, reject null, conclude non-stationary.

Possible outcomes:

| ADF | KPSS | Conclusion |
|-----|------|------------|
| Reject (p < 0.05) | Fail to reject | Stationary — OU model is appropriate |
| Fail to reject | Reject (p < 0.05) | Non-stationary — OU model is NOT appropriate |
| Reject | Reject | Trend-stationary — consider detrending or regime-switching |
| Fail to reject | Fail to reject | Inconclusive — larger sample needed |

If delta is non-stationary on most coins: consider regime-switching OU (different theta/mu/sigma for trending vs ranging periods, classified by e.g. volatility regime). If that also fails, document the finding — OU may be the wrong model for this specific delta.

### 2.5 Probability Surface

The key output: given current delta value and current delta velocity (first difference of delta), what is P(delta crosses zero within N bars)?

This is computed from the OU model:

```
P(cross within N | delta_0, velocity_0) = P(min(delta_t for t in 1..N) <= 0 | delta_0)
```

For OU with known parameters, this is the first-passage-time distribution. No closed-form exists, but it can be estimated:

- Monte Carlo simulation: generate 10,000 OU paths from (delta_0, velocity_0), count what fraction cross zero within N bars
- Numerical PDE: solve the Fokker-Planck equation with absorbing boundary at delta=0

The notebook should produce a heatmap: x-axis = current delta, y-axis = current velocity, color = P(cross within N bars). Separate heatmaps for N = 5, 10, 20, 50 bars.

### 2.6 Integration With Stochastic Alignment

The delta compression is part of how alignment is read, not a separate signal. The research must produce a conditional probability:

**P(EMA cross within N bars | alignment state active AND delta compressing)**

This is the joint probability that combines both models. Compute by:

1. Identify bars where stochastic alignment state is active (section 1.7)
2. For those bars, record the delta value and velocity
3. From the OU model, compute P(cross within N) at those delta/velocity values
4. Compare against actual cross outcomes (did a cross actually happen within N bars?)

This produces the calibration: does the OU prediction match reality when alignment is present?

---

## 3. Slope / Degree of Change

### 3.1 Definition

"Improving slope" on stoch 40 and 60:

- **First derivative (slope)**: slope_N(i) = K(i) - K(i - N)
- **Second derivative (acceleration)**: accel(i) = slope_N(i) - slope_N(i - M)

"Improving" for long = acceleration > 0. The degree of change is increasing, regardless of whether the stoch is in the zone, at the zone edge, or past it.

"Improving" for short = acceleration < 0. The degree of change is decreasing (K falling faster).

### 3.2 Parameters to Determine

- **N** (slope window): how many bars for the first derivative? Too small = noisy, too large = lagging. Candidate values: 3, 5, 8, 13 bars.
- **M** (acceleration window): how many bars for the second derivative? Same trade-off. Candidate values: 3, 5, 8 bars.

The notebook will test each combination and measure discriminative power: for each (N, M) pair, how well does "acceleration > 0" predict that a stoch will continue moving in that direction for the next K bars?

### 3.3 Relationship to Markov States

The slope and acceleration values are what determine which Markov state a stochastic is in:

- ZONE: K value check only (< 20 or > 80)
- TURNING: slope > 0 (for long), acceleration may be any value
- MOVING: slope > 0 AND acceleration > 0
- EXTENDED: K > 50 AND slope > 0

So (N, M) directly affect how bars are classified into states, which affects the transition matrix and the joint distribution. The notebook must show sensitivity: how do different (N, M) values change the state classifications and downstream probabilities?

---

## 4. TDI — Directional Confirmation

### 4.1 Source

From position management study (confirmed user rules). User confirmed TDI applies to the 55/89 scalp, not just trend-holds.

Settings: RSI period=9, RSI price smoothing=5, Signal line=10, Bollinger band period=34.

### 4.2 Rule

TDI price line must be on the correct side of its moving average:
- LONG: TDI above MA
- SHORT: TDI below MA

This is a binary check at the time of alignment. If TDI is on the wrong side, alignment is present but unconfirmed — the directional momentum in stochs/delta is not backed by the RSI-based momentum read.

### 4.3 TDI State

Two states:

| State | Condition | Meaning |
|-------|-----------|---------|
| CONFIRMING | TDI on correct side of MA | Momentum agrees with alignment direction |
| OPPOSING | TDI on wrong side of MA | Momentum disagrees — alignment may be noise |

### 4.4 Integration

TDI state becomes another feature in the Vince state vector and another dimension on the joint distribution. The alignment definition (section 1.7) is evaluated only after stoch 9 has fired (section 5):

A bar is in "alignment" for long when (stoch 9 alert already active):
- Stoch 14: in MOVING or EXTENDED
- Stoch 40, 60: in TURNING, MOVING, or EXTENDED (slope improving)
- No stoch has negative K slope (contradiction check)
- EMA delta compressing toward zero or just crossed
- TDI on correct side of MA (CONFIRMING)
- BBW not QUIET

### 4.5 TDI Computation

1. RSI = RSI(close, 9)
2. TDI price line = SMA(RSI, 5)
3. TDI signal line = SMA(RSI, 10)
4. State = CONFIRMING if TDI price > TDI signal (long) or TDI price < TDI signal (short)

---

## 5. Stoch 9 K/D Cross — The Monitoring Trigger

### 5.1 Source

From position management study (confirmed user rules). User confirmed this applies to the 55/89 scalp.

"Stoch 9 is the alert — it moves first. But you do NOT enter until the other stochastics follow."

### 5.2 Role: Gate That Activates the Pipeline

Stoch 9 K/D cross is NOT one of four equal stoch observations. It is the event that turns the entire pipeline on. Nothing else runs until this fires.

**System states:**

| State | Trigger | What happens |
|-------|---------|-------------|
| IDLE | Default | Only computing stoch 9 K and D. Nothing else runs. Waiting for K/D cross. |
| MONITORING | Stoch 9 K/D cross fires | Full pipeline activates: compute all indicators, classify states, check alignment, run OU/Markov/MC. |
| READY | Alignment + delta compressing + TDI confirming + BBW not QUIET | All conditions met. MC probabilities above threshold. Signal is live. |
| INACTIVE | Stoch 9 reverses (K crosses back below D for long) | Pipeline shuts down. Back to IDLE. |

The pipeline does not passively classify every bar. Stoch 9 K/D cross is the gate. Before it fires, the system is idle. After it fires, monitoring begins.

### 5.3 Impact on Markov Model

Stoch 9 is the conditioning event, not a peer in the joint distribution. The Markov model should track:
- Time since stoch 9 last crossed K/D (bars since alert)
- Whether stoch 9 is still in the post-cross direction

All transition probabilities are conditional on the alert having fired:
- P(stoch 14 transitions to MOVING | stoch 9 crossed K/D N bars ago)
- P(stoch 40 slope improving | stoch 9 alert active for N bars)
- P(stoch 60 turning | stoch 9 alert active for N bars)

This means the Markov chain does not model stoch 9 as one of four equal participants. Stoch 9's cross is time-zero. Everything else is measured relative to it.

### 5.4 Impact on MC Simulation

Monte Carlo paths start from the moment stoch 9 fires. Each path simulates:
- How long until stoch 14 follows (or doesn't)
- Whether stoch 40/60 slope improves within the window
- Whether delta compresses to cross within the window
- Whether stoch 9 reverses before the above completes (cancellation)

The key MC output becomes: **given stoch 9 just fired, what is P(full alignment + EMA cross within N bars before stoch 9 reverses)?**

---

## 6. BBW Volatility Regime — State Filter

### 4.1 Source

From position management study (confirmed user rules, not invented):
- BBWP settings: SMA 7, length 100, Spectrum mode
- "BBW spectrum line must cross from below MA to above MA" = volatility confirming the move
- "Without this cross, the stochastic movement could be noise"

BBW answers a different question than Markov or OU. Markov: are the stochs aligned? OU: is the delta likely to cross? BBW: is the volatility regime confirming this move is real, or is it noise?

### 4.2 BBW States

Three discrete states from the position management study:

| State | Condition | Meaning |
|-------|-----------|---------|
| HEALTHY | Spectrum ABOVE MA | Volatility supports the move |
| EXTREME | Spectrum RED (high percentile) | Max volatility — move is overextended |
| QUIET | Spectrum BELOW MA or DARK BLUE | Low volatility — move is likely noise |

For the 55/89 scalp research: BBW HEALTHY at the time of alignment is a confirmation that the stochastic alignment + delta compression is happening in a real volatility environment. BBW QUIET during alignment = higher chance of false positive (alignment exists but the move fizzles).

### 4.3 BBW as Markov Context

BBW state becomes an additional dimension on the joint distribution:

- Without BBW: P(cross | stoch alignment state, delta)
- With BBW: P(cross | stoch alignment state, delta, BBW state)

This extends the joint space. Instead of 256 cells (4^4 stoch states), it becomes 256 x 3 = 768 cells. Some cells will be sparse — that is expected and informative (e.g., alignment active + delta compressing + BBW QUIET should be rare if the signal is real).

### 4.4 BBW Computation

BBWP = Bollinger Band Width Percentile:
1. Compute Bollinger Bands (20, 2.0) on close
2. BBW = (upper - lower) / middle
3. BBWP = percentile rank of current BBW over last 100 bars
4. Spectrum MA = SMA(BBWP, 7)
5. State = HEALTHY if BBWP > Spectrum MA, QUIET if below, EXTREME if BBWP > threshold (to determine from data)

Existing code: `research/bbw_analyzer_v2.py` already computes BBW states. Reuse the state classification logic.

---

## 5. Monte Carlo — Full Joint Simulation

### 5.1 Purpose

Sections 1-4 build individual models (Markov, OU, slope, BBW). Monte Carlo simulates the full joint system forward in time to produce the single output: P(EMA cross | current system state).

### 5.2 What Is Simulated

At each MC step, generate a synthetic 1m bar path:
1. **Stoch paths**: use the Markov transition matrices to simulate state sequences for all 4 stochs simultaneously (respecting joint distribution, not independently)
2. **Delta path**: use the fitted OU process to simulate delta forward from current (delta, velocity)
3. **BBW path**: use observed BBW state transitions to simulate volatility regime forward

For each simulation run (10,000+ paths):
- Start from the current observed system state (all 4 stoch states + delta + BBW)
- Simulate N bars forward
- Record whether delta crosses zero (EMA cross occurs)
- Record whether stoch alignment persists, degrades, or contradicts

### 5.3 Why Not Just OU Alone?

OU in isolation estimates P(cross | delta). But the user's signal requires alignment to be present when the cross happens. MC captures the reality that:
- Stoch alignment may collapse before the delta reaches zero (fast stochs reverse while delta is still compressing)
- BBW may shift to QUIET, meaning the delta compression is happening in a low-volatility regime where it doesn't lead to a real cross
- The joint dynamics matter: stochs and delta are both derived from the same price, so their paths are correlated

MC simulation with correlated paths captures these interactions. Independent simulation of each component would miss them.

### 5.4 Correlation Structure

All components (stochs, delta, BBW) are derived from the same close/high/low data. The MC simulation must preserve this correlation. Two approaches:

**Approach A — Empirical resampling**: instead of generating synthetic paths from fitted models, resample actual historical bar sequences that start from similar system states. This automatically preserves all correlations.

**Approach B — Copula-based**: fit marginal models independently (Markov for stochs, OU for delta), then use a copula to re-introduce correlation structure estimated from historical data.

Approach A is simpler and makes fewer assumptions. Start with A. Use B only if A produces insufficient variety in starting states.

### 5.5 Output

For each starting system state, MC produces:
- P(cross within 5 bars)
- P(cross within 10 bars)
- P(cross within 20 bars)
- P(cross within 50 bars)
- P(alignment still active when cross occurs)
- P(BBW HEALTHY when cross occurs)

These are the numbers Vince reads (section 6).

### 5.6 Validation

Compare MC-predicted probabilities against actual outcomes in held-out data:
- Split historical data into train (fit models) and test (validate predictions)
- For each alignment event in test set, compare MC P(cross) against whether a cross actually occurred
- Calibration plot: predicted probability vs observed frequency (should be a 45-degree line if well-calibrated)
- Brier score as single summary metric

Existing code: `research/bbw_monte_carlo_v2.py` has bootstrap/permutation testing infrastructure. The MC simulation is a new module but the validation pattern (confidence intervals, verdicts) can follow the same structure.

---

## 6. Vince State Output — What Vince Reads

### 6.1 Purpose

Vince needs discrete, machine-readable state labels at every 1m bar. Not raw numbers — states.

### 6.2 State Vector Per Bar

At each 1m bar, the research pipeline produces a state vector:

```
{
    "timestamp": "2026-03-06T14:05:00Z",
    "system_state": "MONITORING",   // IDLE / MONITORING / READY
    "bars_since_alert": 7,          // bars since stoch 9 K/D cross fired
    "stoch_9_kd": true,             // K > D (the gate — must be true when not IDLE)
    "stoch_14_state": "EXTENDED",
    "stoch_14_kd": true,
    "stoch_40_state": "TURNING",
    "stoch_40_kd": false,
    "stoch_60_state": "ZONE",
    "stoch_60_kd": false,
    "alignment": "ACTIVE",          // ACTIVE / INACTIVE / CONTRADICTED
    "tdi_state": "CONFIRMING",      // CONFIRMING / OPPOSING
    "ema_delta": -0.00023,          // raw delta value
    "ema_delta_velocity": 0.00004,  // delta first difference
    "ema_delta_state": "COMPRESSING",  // COMPRESSING / EXPANDING / CROSSED
    "bbw_state": "HEALTHY",         // HEALTHY / EXTREME / QUIET
    "p_cross_5": 0.12,             // MC probability of cross within 5 bars
    "p_cross_10": 0.31,
    "p_cross_20": 0.58,
    "p_cross_50": 0.84,
    "p_aligned_at_cross": 0.71     // P(alignment still active when cross occurs)
}
```

When system_state is IDLE, only `timestamp`, `system_state`, and `stoch_9_kd` are populated. All other fields are null — the pipeline is not running.

### 6.3 Derived States for Vince Decision-Making

From the state vector, three system-level states:

| State | Trigger | Condition | Meaning |
|-------|---------|-----------|---------|
| IDLE | Default / stoch 9 reversal | Stoch 9 K/D not crossed | Pipeline off. Only watching stoch 9. |
| MONITORING | Stoch 9 K/D cross fires | Full pipeline running, alignment building | Setup developing. All indicators computed. |
| READY | Alignment completes | alignment=ACTIVE, tdi=CONFIRMING, bbw not QUIET, p_cross_10 > threshold, p_aligned_at_cross > threshold | High probability the cross fires soon with alignment intact. |

Transitions:
- IDLE -> MONITORING: stoch 9 K/D cross
- MONITORING -> READY: all alignment conditions met + MC probabilities above threshold
- MONITORING -> IDLE: stoch 9 reverses (K crosses back)
- READY -> IDLE: stoch 9 reverses or alignment breaks

The thresholds for READY are determined by the research: what p_cross and p_aligned values historically led to actual EMA crosses? This comes from the MC validation (section 7.6).

---

## 7. Open Questions (must answer before backtest phase)

These are functional gaps that prevent simulating actual trades. They are not invented conditions — they are structural requirements of a trade simulation.

| # | Question | Why it matters |
|---|----------|----------------|
| 1 | **Initial SL value** — what determines the initial stop loss? | A live replay needs to know when a trade is stopped out before reaching BE. Without SL, trade survival cannot be computed. |
| 2 | **Exit rule** — once SL is at BE, what closes the trade? | Without an exit, trades run forever. No P&L can be computed. Options: opposite signal, time limit, trailing, opposite EMA cross. |
| 3 | **"After cross confirms"** — which cross triggers the BE move? | Likely the 55/89 EMA cross (the entry trigger). But could mean a K/D cross on a stoch. Ambiguity must be resolved. |

These will be asked when the backtest phase begins. The research phase (this document + notebook) does not need these answers — it is measuring probabilities, not simulating trades.

---

## 8. What This Document Does NOT Cover

- No TP rule (not stated by user)
- No HTF filter (not stated)
- No coin selection criteria (not stated)
- No position sizing (not stated)
- Nothing beyond the stated elements + confirmed indicators (TDI, BBW) + Markov/OU/slope/MC research framework
