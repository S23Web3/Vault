# BBW Simulator — Statistics Research & VINCE Features
**Date:** 2026-02-14
**Project:** `four-pillars-backtester`
**Related:** [[BBW-UML-DIAGRAMS]] | [[BBW-SIMULATOR-ARCHITECTURE]]

---

## SCOPE DECISION: Ripster/AVWAP at Entry

**Answer: No. That's rabbitholing.**

The BBW simulator is a **single-pillar research engine**. Its job is to answer one question: *"Given BBW state X, what LSG parameters maximize risk-adjusted returns?"*

Recording Ripster or AVWAP values at entry would:
- Cross into **multi-pillar combinatorial space** (BBW × Ripster × AVWAP × Stoch = 4-way cross-tab)
- Blow up the parameter grid from 10,752 → 150,000+ combinations per coin
- Duplicate work that belongs to the **ML layer** (VINCE)

**Where Ripster/AVWAP integration actually belongs:**
1. `signals/bbwp.py` outputs BBW features per bar
2. `signals/ripster.py` outputs Ripster features per bar (already exists)
3. `signals/avwap.py` outputs AVWAP features per bar (already exists)
4. `ml/features.py` **combines all pillar features into one feature matrix**
5. XGBoost/PyTorch learns cross-pillar interactions automatically

The BBW simulator produces the **BBW→LSG lookup table**. VINCE learns **when multiple pillars align** to override or confirm that table. These are two separate jobs.

---

## NUMPY / SCIPY STATISTICS — VINCE Feature Engineering

### What the BBW Simulator Produces (Per Bar, Per Coin)

These columns become ML features. Organized by statistical category:

### A. Direct BBW Features (Layer 1-2 output → VINCE input)

| Feature | Type | Numpy/Pandas Method | VINCE Use |
|---------|------|---------------------|-----------|
| `bbwp_value` | float 0-100 | `pd.Series.rolling(100).rank(pct=True) * 100` | Primary continuous feature |
| `bbwp_ma` | float | `pd.Series.rolling(5).mean()` | Trend of volatility |
| `bbwp_bbw_raw` | float | `(2 * rolling_std) / rolling_mean` | Raw input before percentile |
| `bbwp_state` | categorical | Priority-based if/elif chain | One-hot encoded for ML |
| `bbwp_spectrum` | ordinal | Threshold mapping function | Ordinal encoded (0-4) |
| `bbwp_points` | int 0-2 | Conditional assignment | Direct numeric feature |
| `bbwp_ma_cross_up` | bool | `(bbwp > bbwp_ma) & (bbwp.shift(1) <= bbwp_ma.shift(1))` | Binary event flag |
| `bbwp_ma_cross_down` | bool | Inverse of above | Binary event flag |

### B. Derived Statistical Features (Computed in feature engineering step)

| Feature | Formula | Library | VINCE Use |
|---------|---------|---------|-----------|
| `bbwp_roc` | `bbwp_value.diff(1)` | pandas | Rate of change — how fast volatility is shifting |
| `bbwp_roc_5` | `bbwp_value.diff(5)` | pandas | 5-bar momentum of BBWP |
| `bbwp_acceleration` | `bbwp_roc.diff(1)` | pandas | 2nd derivative — acceleration of vol change |
| `bbwp_ma_distance` | `bbwp_value - bbwp_ma` | numpy | Distance from MA — divergence signal |
| `bbwp_zscore` | `(bbwp - rolling_mean) / rolling_std` | numpy | Z-score within lookback — extreme detection |
| `bbwp_skew_20` | `bbwp_value.rolling(20).skew()` | pandas/scipy | Asymmetry of recent BBWP distribution |
| `bbwp_kurt_20` | `bbwp_value.rolling(20).kurt()` | pandas/scipy | Tail thickness — are we seeing extremes? |
| `bbwp_entropy` | Custom (see below) | scipy | Information content of recent states |

### C. Sequence Features (Layer 2 → VINCE)

| Feature | Type | Method | VINCE Use |
|---------|------|--------|-----------|
| `bbw_seq_bars_in_state` | int | Counter reset on state change | Duration feature — how long in current state |
| `bbw_seq_bars_in_color` | int | Counter reset on color change | Duration at spectrum level |
| `bbw_seq_direction` | categorical | Color order comparison | Expanding/contracting/flat |
| `bbw_seq_skip_detected` | bool | `abs(color_rank_diff) > 1` | Anomaly flag — skipped color step |
| `bbw_seq_pattern_id` | categorical | Last 3 color transitions encoded | Categorical feature, target-encoded for ML |
| `bbw_seq_from_blue_bars` | int | Bars since last blue | Recency of low-vol state |
| `bbw_seq_from_red_bars` | int | Bars since last red | Recency of high-vol state |

### D. Advanced Statistics for Report Layer (scipy.stats)

These are computed per BBW state across all bars in the simulation:

```python
from scipy.stats import skew, kurtosis, entropy, ks_2samp
import numpy as np

# Per BBW state, compute distribution statistics of forward returns
for state in states:
    state_returns = df[df['bbwp_state'] == state]['fwd_10_close_pct']
    
    stats_dict = {
        'mean':     np.mean(state_returns),
        'median':   np.median(state_returns),
        'std':      np.std(state_returns),
        'skew':     skew(state_returns, nan_policy='omit'),
        'kurtosis': kurtosis(state_returns, fisher=True, nan_policy='omit'),
        'iqr':      np.percentile(state_returns, 75) - np.percentile(state_returns, 25),
        'p5':       np.percentile(state_returns, 5),   # tail risk
        'p95':      np.percentile(state_returns, 95),   # upside potential
        'sharpe':   np.mean(state_returns) / np.std(state_returns) if np.std(state_returns) > 0 else 0,
        'sortino':  np.mean(state_returns) / np.std(state_returns[state_returns < 0]) if len(state_returns[state_returns < 0]) > 0 else 0,
    }
    
    # KS test: is this state's return distribution different from NORMAL state?
    normal_returns = df[df['bbwp_state'] == 'NORMAL']['fwd_10_close_pct']
    ks_stat, ks_pvalue = ks_2samp(state_returns, normal_returns)
    stats_dict['ks_stat'] = ks_stat
    stats_dict['ks_pvalue'] = ks_pvalue  # < 0.05 means statistically different
```

### E. Transition Probability Matrix (Markov Chain)

```python
# State transition probabilities — feeds into VINCE as context features
from collections import Counter

states_sequence = df['bbwp_state'].values
transitions = Counter(zip(states_sequence[:-1], states_sequence[1:]))
all_states = df['bbwp_state'].unique()

# Build transition matrix
trans_matrix = pd.DataFrame(0.0, index=all_states, columns=all_states)
for (from_s, to_s), count in transitions.items():
    trans_matrix.loc[from_s, to_s] = count

# Normalize rows to probabilities
trans_matrix = trans_matrix.div(trans_matrix.sum(axis=1), axis=0)

# VINCE feature: probability of transitioning to BLUE from current state
df['prob_to_blue'] = df['bbwp_state'].map(
    trans_matrix['BLUE'].to_dict()
)
```

### F. Mutual Information (Feature Selection for VINCE)

```python
from sklearn.feature_selection import mutual_info_classif

# How much information does each BBW feature carry about forward direction?
bbw_features = df[['bbwp_value', 'bbwp_roc', 'bbwp_ma_distance', 
                     'bbw_seq_bars_in_state', 'bbwp_skew_20', 'bbwp_kurt_20']].dropna()
target = df.loc[bbw_features.index, 'fwd_10_direction'].map({'up': 1, 'down': 0})

mi_scores = mutual_info_classif(bbw_features, target, random_state=42)
# Rank features by information content → prune low-value ones from VINCE
```

### G. Complete VINCE Feature Vector from BBW

Final feature list that Layer 4 produces and VINCE consumes:

```python
VINCE_BBW_FEATURES = [
    # Direct (Layer 1)
    'bbwp_value',           # continuous 0-100
    'bbwp_points',          # ordinal 0-2
    'bbwp_is_blue_bar',     # binary
    'bbwp_is_red_bar',      # binary
    
    # Derived (feature engineering)
    'bbwp_roc',             # 1-bar rate of change
    'bbwp_roc_5',           # 5-bar momentum
    'bbwp_acceleration',    # 2nd derivative
    'bbwp_ma_distance',     # distance from BBWP MA
    'bbwp_zscore',          # rolling z-score
    'bbwp_skew_20',         # 20-bar rolling skewness
    'bbwp_kurt_20',         # 20-bar rolling kurtosis
    
    # Sequence (Layer 2)
    'bbw_seq_bars_in_state',  # duration in current state
    'bbw_seq_direction_enc',  # ordinal: contracting=0, flat=1, expanding=2
    'bbw_seq_skip_detected',  # binary anomaly
    'bbw_seq_from_blue_bars', # recency of low-vol
    'bbw_seq_from_red_bars',  # recency of high-vol
    
    # Markov
    'prob_to_blue',           # transition probability to blue
    
    # Interaction (computed at ML layer, not simulator)
    # 'bbwp_x_ripster_trend',  ← THIS is where cross-pillar features go
    # 'bbwp_x_avwap_distance', ← NOT in the BBW simulator
]
```

**Total: 17 BBW features for VINCE.** Cross-pillar interactions are computed in `ml/features.py`, NOT in the BBW simulator.

---

## MONTE CARLO VALIDATION — Layer 4b

**File:** `research/bbw_monte_carlo.py`

Matches approach from `v3.8-MONTE-CARLO-FINDINGS.md` but applied per BBW state.

### Purpose
The LSG grid search finds the "best" parameters per state. Monte Carlo answers: **"Is that edge real or is it an artifact of trade ordering?"**

### Method

```python
import numpy as np

def validate_lsg_params(trades_df, n_simulations=1000, confidence=0.95):
    """
    Monte Carlo validation for optimal LSG parameters.
    
    Args:
        trades_df: DataFrame with columns [pnl, state, direction, lsg_params]
        n_simulations: number of shuffle iterations
        confidence: confidence level for intervals
    
    Returns:
        dict with real_metrics, shuffled_distribution, confidence_intervals, is_robust
    """
    real_pnl = trades_df['pnl'].values
    real_equity = np.cumsum(real_pnl)
    real_metrics = {
        'total_pnl': real_equity[-1],
        'max_dd': _max_drawdown(real_equity),
        'sharpe': np.mean(real_pnl) / np.std(real_pnl) if np.std(real_pnl) > 0 else 0,
        'profit_factor': abs(real_pnl[real_pnl > 0].sum() / real_pnl[real_pnl < 0].sum()) if real_pnl[real_pnl < 0].sum() != 0 else np.inf,
    }
    
    # Shuffle trade order N times, rebuild equity curve each time
    shuffled_totals = np.zeros(n_simulations)
    shuffled_dds = np.zeros(n_simulations)
    shuffled_sharpes = np.zeros(n_simulations)
    
    for i in range(n_simulations):
        shuffled = np.random.permutation(real_pnl)
        equity = np.cumsum(shuffled)
        shuffled_totals[i] = equity[-1]
        shuffled_dds[i] = _max_drawdown(equity)
        shuffled_sharpes[i] = np.mean(shuffled) / np.std(shuffled) if np.std(shuffled) > 0 else 0
    
    # Confidence intervals
    lo = (1 - confidence) / 2 * 100
    hi = (1 + confidence) / 2 * 100
    
    ci = {
        'pnl_lo': np.percentile(shuffled_totals, lo),
        'pnl_hi': np.percentile(shuffled_totals, hi),
        'pnl_median': np.median(shuffled_totals),
        'dd_95th': np.percentile(shuffled_dds, 95),  # worst-case DD
        'sharpe_lo': np.percentile(shuffled_sharpes, lo),
        'sharpe_hi': np.percentile(shuffled_sharpes, hi),
    }
    
    # Robustness check: real result should beat 95th percentile of random
    pnl_percentile = (shuffled_totals < real_metrics['total_pnl']).mean() * 100
    
    return {
        'real_metrics': real_metrics,
        'confidence_intervals': ci,
        'pnl_percentile': pnl_percentile,  # where real falls in shuffled distribution
        'is_robust': pnl_percentile >= 95,  # real beats 95% of random orderings
        'n_simulations': n_simulations,
    }

def _max_drawdown(equity_curve):
    """Max drawdown from equity curve array."""
    peak = np.maximum.accumulate(equity_curve)
    dd = equity_curve - peak
    return dd.min()
```

### What Gets Validated

For each BBW state's top LSG combo:

| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| PnL percentile | Real PnL > 95th pctl of shuffled | Flag as overfit |
| Max DD | Real DD < 95th pctl worst-case DD | Flag as fragile |
| Sharpe robustness | Real Sharpe within top 10% | Reduce confidence in params |
| Sample size | n_trades >= 100 per state | Insufficient data warning |

### Output

```
reports/bbw/monte_carlo/
├── mc_summary_by_state.csv       — per-state robustness verdicts
├── mc_confidence_intervals.csv   — CI for PnL, DD, Sharpe per state
├── mc_equity_distribution.csv    — percentile bands for equity curves
└── mc_overfit_flags.csv          — states where params may be overfit
```

### Runtime Addition
- Per state: 1000 shuffles × ~0.5ms each = ~0.5s
- 7 states × 0.5s = ~3.5s per coin
- 399 coins × 3.5s = ~23 minutes total
- Combined with existing 8 min → **~31 minutes total runtime**

---

## BUILD SEQUENCE (Ordered)

| Step | File | Depends On | Est. Time |
|------|------|------------|-----------|
| 0 | `research/__init__.py` | — | 1 min |
| 1 | `signals/bbwp.py` | OHLCV data | 45 min |
| 2 | `signals/bbw_sequence.py` | Step 1 | 30 min |
| 3 | `research/coin_classifier.py` | All parquets | 20 min |
| 4 | `research/bbw_forward_returns.py` | Steps 1-2 | 30 min |
| 5 | `research/bbw_simulator.py` | Steps 1-4 | 90 min |
| 5b | `research/bbw_monte_carlo.py` | Step 5 | 30 min |
| 6 | `research/bbw_report.py` | Steps 5-5b | 45 min |
| 7 | `scripts/run_bbw_simulator.py` | Steps 0-6 | 20 min |
| 8 | Test on single coin (RIVERUSDT) | Steps 0-7 | 15 min |
| 9 | Full run (399 coins) | Step 8 passing | ~31 min runtime |

**Total build estimate: ~5 hours of Claude Code work**

### Test-First Approach (per python-trading-development-skill.md)

Each step gets a corresponding test file:
```
tests/
├── test_bbwp.py               ← Validate against Pine Script output
├── test_bbw_sequence.py        ← Known transition patterns
├── test_forward_returns.py     ← Manual calculation verification
├── test_coin_classifier.py     ← Cluster count stability
├── test_bbw_simulator.py       ← Single-state grid output shape
└── test_bbw_report.py          ← Output file existence + schema
```

---

## DEPENDENCIES SUMMARY

| Package | Already Installed | Used By |
|---------|-------------------|---------|
| pandas | ✅ | All layers |
| numpy | ✅ | All layers |
| pathlib | ✅ | File handling |
| scipy.stats | ✅ | skew, kurtosis, KS test, percentileofscore |
| scikit-learn | ✅ | KMeans, silhouette, mutual_info |
