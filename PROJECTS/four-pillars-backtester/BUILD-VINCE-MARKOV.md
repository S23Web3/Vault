# BUILD-VINCE-MARKOV.md
# Markov Chain — Indicator State Transition Engine

**Build ID:** VINCE-MARKOV
**Status:** READY TO SCOPE — added 2026-03-12
**Depends on:** B3 (Enricher) — needs indicator snapshot columns at every bar
**Used by:** B4 (Panel 2 — PnL Reversal), B5 (Query Engine)
**File:** `vince/markov.py`

---

## What It Does in Plain English

After a trade is entered, the stochastics move through states — rising, falling, overbought, reversing. Markov asks: given the stochastic is in state X right now, what is the probability it moves to state Y within the next N bars?

This answers exit timing directly. If stoch_60 is at 65 and rising, what is the probability it reaches 80 (full extension) before reversing below 50? If that probability is 70%, hold. If it is 30%, the trade has likely run its course — exit.

Vince builds this probability map from your actual OHLCV history (not the trade CSV). It is then applied to each trade's post-entry bar sequence to produce a "continuation probability" at each bar — a number from 0 to 1 representing the likelihood the move continues.

---

## State Space Definition

States are defined per indicator. Each indicator is discretised into 4 states:

| State | stoch value | label |
|-------|-------------|-------|
| 0 | 0–25 | OVERSOLD |
| 1 | 25–50 | LOWER_MID |
| 2 | 50–75 | UPPER_MID |
| 3 | 75–100 | OVERBOUGHT |

Primary indicator for exit timing: **stoch_60** (macro stochastic — the slowest, most reliable).
Secondary: **stoch_40** (confirms macro direction).
Optional: stoch_9 (fast — noisy, used for entry quality only, not exit timing).

Each combination of (stoch_60_state, stoch_40_state) = one composite state. 4×4 = 16 composite states total.

---

## Transition Matrix

Built from OHLCV history (not trade CSV). For each bar pair (t, t+1):
- Record state at t → state at t+1
- Accumulate counts into a 16×16 matrix
- Normalise each row to sum to 1.0 → probability of transitioning from state S to state S' in one bar

Matrix is coin-specific. Transition probabilities differ between BTCUSDT (smooth trends) and low-cap altcoins (erratic state jumps).

**Cache:** Transition matrices are cached per (symbol, timeframe, date_range). Rebuilding is cheap (one pass over OHLCV), but caching avoids repeat work. Use the existing `vince/cache_config.py` FanoutCache.

---

## What Vince Computes Per Trade

For each trade, after entry bar:
1. Walk forward bar by bar through the OHLCV data
2. At each bar, look up current composite state
3. Compute N-step forward probability: probability of reaching a "bullish extension" state (state 3 for LONG, state 0 for SHORT) within the next N bars
4. Compute "reversal risk": probability of crossing the midline (state transition from ≥2 to ≤1 for LONG) within N bars
5. Store as two columns per bar: `continuation_prob_Nbar`, `reversal_risk_Nbar`

N defaults: 3, 5, 10 bars (15min, 25min, 50min at 5m timeframe).

---

## N-Step Probability Calculation

Given transition matrix M (16×16), the N-step transition matrix is M^N (matrix power).
`scipy.linalg.matrix_power(M, N)` — one call, fast.

For a trade currently in composite state S:
- Row S of M^N gives the probability distribution over all 16 states after N bars
- Sum probabilities of all "target" states (e.g. state 3 for LONG extension)
- That sum = `continuation_prob_Nbar`

---

## Outputs Added to EnrichedTradeSet

The enricher (B3) calls `markov.attach_transition_probs(trade_row, ohlcv_df, matrix)` for each trade.

New columns added to enriched trade DataFrame:

| Column | Description |
|--------|-------------|
| `state_at_entry` | Composite state (0–15) at entry bar |
| `state_at_mfe` | Composite state at MFE bar |
| `state_at_exit` | Composite state at exit bar |
| `continuation_prob_3bar` | Prob of bullish extension within 3 bars, at entry |
| `continuation_prob_5bar` | Prob of bullish extension within 5 bars, at entry |
| `continuation_prob_10bar` | Prob of bullish extension within 10 bars, at entry |
| `reversal_risk_3bar` | Prob of crossing midline within 3 bars, at entry |
| `reversal_risk_5bar` | Prob of crossing midline within 5 bars, at entry |
| `avg_continuation_prob` | Mean continuation_prob_5bar across all bars from entry to exit |

---

## What Panel 2 (B4) Gets From Markov

Panel 2 gets a new chart: **State Transition Heatmap**.

X-axis: composite state at entry bar (0–15, labelled as "stoch60_state / stoch40_state")
Y-axis: win rate / avg net PnL
Color: continuation probability (5-bar)

Reading: "When trades entered in composite state 10 (stoch_60 UPPER_MID, stoch_40 OVERBOUGHT), continuation_prob_5bar was 0.71 and win rate was 68%. When they entered in state 6 (both LOWER_MID), continuation_prob_5bar was 0.38 and win rate was 31%."

This produces the "enter here, not there" decision for the strategy.

Second chart: **Post-Entry Probability Decay Curve**.
For a selected trade or average of all trades in a filter:
- X-axis: bars after entry (0 to max trade duration)
- Y-axis: continuation_prob_5bar at each bar
- Shows exactly when the probability flips — that is the optimal exit bar on average.

---

## What B5 (Query Engine) Gets From Markov

Two new filter fields added to `ConstellationFilter`:

```python
min_continuation_prob: Optional[float] = None   # e.g. 0.6 — only trades where prob >= 0.6 at entry
max_reversal_risk: Optional[float] = None        # e.g. 0.3 — only trades where reversal risk <= 0.3
```

Two new metrics added to `compute_metrics()`:

```python
"avg_continuation_prob_at_entry": float   # mean continuation_prob_5bar across matched set
"avg_reversal_risk_at_entry": float       # mean reversal_risk_5bar across matched set
```

This lets you ask: "show me all Grade A LONG trades where continuation_prob_5bar > 0.60 at entry — did those outperform trades where it was below 0.60?"

---

## File Structure

```
vince/
  markov.py          ← NEW — transition matrix builder + probability computer
  enricher.py        ← MODIFIED — calls markov.attach_transition_probs() per trade
  pages/
    pnl_reversal.py  ← MODIFIED — adds heatmap + decay curve functions
vince/types.py       ← MODIFIED — adds Markov filter fields to ConstellationFilter
```

---

## Module API (`vince/markov.py`)

```python
def build_transition_matrix(
    ohlcv_df: pd.DataFrame,
    stoch_60_col: str = "stoch_60",
    stoch_40_col: str = "stoch_40",
) -> np.ndarray:
    """Build 16x16 transition matrix from OHLCV indicator history.
    Returns normalised matrix where M[i][j] = P(state j | state i).
    Rows with zero counts default to uniform distribution (1/16)."""

def n_step_matrix(M: np.ndarray, n: int) -> np.ndarray:
    """Compute M^n using scipy.linalg.matrix_power."""

def composite_state(stoch_60_val: float, stoch_40_val: float) -> int:
    """Map (stoch_60, stoch_40) to composite state index 0–15.
    state = stoch_60_bucket * 4 + stoch_40_bucket
    bucket = 0 if val<25, 1 if val<50, 2 if val<75, 3 otherwise."""

def continuation_prob(
    M: np.ndarray,
    current_state: int,
    direction: str,   # "LONG" or "SHORT"
    n: int,
) -> float:
    """P(reaching extension state within n bars) for LONG or SHORT.
    LONG extension states: composite states where stoch_60_bucket == 3
    SHORT extension states: composite states where stoch_60_bucket == 0"""

def reversal_risk(
    M: np.ndarray,
    current_state: int,
    direction: str,
    n: int,
) -> float:
    """P(crossing midline within n bars).
    LONG reversal: transition from stoch_60_bucket >= 2 to stoch_60_bucket <= 1
    SHORT reversal: transition from stoch_60_bucket <= 1 to stoch_60_bucket >= 2"""

def attach_transition_probs(
    trade_row: pd.Series,
    enriched_ohlcv: pd.DataFrame,
    matrix_3: np.ndarray,
    matrix_5: np.ndarray,
    matrix_10: np.ndarray,
) -> dict:
    """For one trade, compute all Markov columns.
    Returns dict of new column values to merge into the trade DataFrame row."""
```

---

## Dependencies

```
scipy  — already likely installed (linalg.matrix_power)
numpy  — already installed
```

Verify scipy at build time: `python -c "from scipy.linalg import matrix_power; print('scipy OK')`
If missing: `pip install scipy --break-system-packages`

---

## Limitations (document in code)

1. **Stationarity assumption:** The transition matrix is built from historical data and assumes the market is roughly stationary. In trending markets or regime changes, transition probabilities shift. This is a known limitation — Vince uses it as a directional signal, not a hard rule.

2. **Sparse states:** Some composite states (e.g. stoch_60=OVERBOUGHT + stoch_40=OVERSOLD) rarely occur. Rows with fewer than 10 observations default to uniform distribution. The enricher logs which states were sparse for review.

3. **Coin-specific matrices:** One matrix per coin. Do not share matrices across coins. Low-cap altcoins have fundamentally different transition dynamics than BTC.

4. **Timeframe fixed at 5m:** Transition matrix built on 5m OHLCV data. If timeframe changes, matrices must be rebuilt.

---

## Build Order Impact

Markov is a new module that slots between B3 and B4:

```
B1  strategies/four_pillars.py          (existing spec)
B2  vince/api.py + vince/types.py       (existing, add 2 filter fields)
B3  vince/enricher.py                   (existing spec + calls markov)
MARKOV  vince/markov.py                 ← NEW — build after B3, before B4
B4  vince/pages/pnl_reversal.py        (existing spec + heatmap + decay curve)
B5  vince/query_engine.py              (existing spec + 2 markov metrics)
B6  vince/app.py + layout.py           (Dash shell)
```

Markov must be built before B4 and B5 — both depend on the transition probability columns.

---

## Verification Tests

```bash
python -c "import py_compile; py_compile.compile('vince/markov.py', doraise=True); print('SYNTAX OK')"

python -c "
import numpy as np
import pandas as pd
from vince.markov import build_transition_matrix, composite_state, continuation_prob, reversal_risk, n_step_matrix

# 1. composite_state mapping
assert composite_state(10.0, 60.0) == 0*4 + 2  # stoch60=OVERSOLD(0), stoch40=UPPER_MID(2)
assert composite_state(80.0, 80.0) == 3*4 + 3  # both OVERBOUGHT
print('STATE MAPPING: PASS')

# 2. build_transition_matrix on synthetic data
n = 500
dummy = pd.DataFrame({
    'stoch_60': np.random.rand(n) * 100,
    'stoch_40': np.random.rand(n) * 100,
})
M = build_transition_matrix(dummy)
assert M.shape == (16, 16), f'expected (16,16) got {M.shape}'
assert np.allclose(M.sum(axis=1), 1.0, atol=1e-6), 'rows must sum to 1'
print('TRANSITION MATRIX: PASS')

# 3. n_step_matrix
M5 = n_step_matrix(M, 5)
assert M5.shape == (16, 16)
assert np.allclose(M5.sum(axis=1), 1.0, atol=1e-5)
print('N-STEP MATRIX: PASS')

# 4. continuation_prob returns float in [0, 1]
p = continuation_prob(M, current_state=6, direction='LONG', n=5)
assert 0.0 <= p <= 1.0, f'prob out of range: {p}'
print('CONTINUATION PROB: PASS')

# 5. reversal_risk returns float in [0, 1]
r = reversal_risk(M, current_state=10, direction='LONG', n=5)
assert 0.0 <= r <= 1.0, f'risk out of range: {r}'
print('REVERSAL RISK: PASS')

print('ALL MARKOV TESTS: PASS')
"
```
