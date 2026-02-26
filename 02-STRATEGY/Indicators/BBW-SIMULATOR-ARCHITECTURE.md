# BBW Simulator Architecture
**Date:** 2026-02-14
**Project:** `four-pillars-backtester`
**Data Source:** 399 coins × 2 timeframes (1m, 5m) in `data/cache/`
**Related:** [[BBW-UML-DIAGRAMS]] | [[BBW-STATISTICS-RESEARCH]]

---

## GOAL

Answer: "Given the BBW state at any bar, what leverage, size, and target distance would have maximized risk-adjusted returns?"

BBW does NOT limit trades. BBW TUNES the LSG (Leverage, Size, Grid/Target).

---

## ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────┐
│                     BBW SIMULATOR PIPELINE                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PRE-STEP: COIN CLASSIFIER   research/coin_classifier.py         │
│  Input:  All 399 coin parquets                                   │
│  Output: coin_tiers.csv (KMeans clustering on vol features)      │
│                                                                  │
│  LAYER 1: CALCULATOR          signals/bbwp.py                    │
│  Input:  OHLCV DataFrame                                        │
│  Output: Per-bar BBWP value, spectrum, state, MA cross           │
│                                                                  │
│  LAYER 2: SEQUENCE TRACKER    signals/bbw_sequence.py            │
│  Input:  BBWP columns from Layer 1                               │
│  Output: Transitions, skip detection, direction, pattern ID      │
│                                                                  │
│  LAYER 3: FORWARD RETURN TAG  research/bbw_forward_returns.py    │
│  Input:  OHLCV only (Layer 1/2 NOT required)                    │
│  Output: Per-bar directional returns at 10/20 bars, ATR-norm     │
│                                                                  │
│  LAYER 4: SIMULATOR ENGINE    research/bbw_simulator.py          │
│  Input:  All columns from Layers 1-3                             │
│  Output: Statistical tables, optimal LSG mapping per BBW state   │
│                                                                  │
│  LAYER 4b: MONTE CARLO        research/bbw_monte_carlo.py        │
│  Input:  Trade results from Layer 4                              │
│  Output: Confidence intervals, overfit detection per state       │
│                                                                  │
│  LAYER 5: REPORT GENERATOR    research/bbw_report.py             │
│  Input:  Simulator + MC output                                   │
│  Output: CSV tables, summaries, per-tier breakdowns              │
│                                                                  │
│  LAYER 6: OLLAMA ANALYSIS     research/bbw_ollama_review.py      │
│  Input:  Report CSVs + MC results                                │
│  Output: NL summaries, anomaly flags, feature recommendations    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## LAYER 1: BBWP CALCULATOR — `signals/bbwp.py`

Port of Pine Script v2 logic to Python. Reusable by backtester and simulator.

### Function: `calculate_bbwp(df, params=None)`

**Input:** DataFrame with columns: `open, high, low, close, base_vol`

**Parameters (with defaults):**
```python
DEFAULT_PARAMS = {
    'basis_len': 13,          # BB period (scalping optimized)
    'basis_type': 'SMA',      # MA type for BB basis
    'lookback': 100,          # BBWP percentile lookback
    'bbwp_ma_len': 5,         # MA of BBWP for crossover detection
    'bbwp_ma_type': 'SMA',    # MA type
    'extreme_low': 10,        # Blue bar threshold
    'extreme_high': 90,       # Red bar threshold  
    'spectrum_low': 25,       # Blue spectrum threshold
    'spectrum_high': 75,      # Red spectrum threshold
    'ma_cross_timeout': 10,   # Bars before MA cross state auto-resets
}
```

**Output columns added to DataFrame:**
```
bbwp_value        : float (0-100)    — percentile rank
bbwp_ma           : float            — moving average of BBWP
bbwp_bbw_raw      : float            — raw BB width (for debugging)
bbwp_spectrum     : str              — 'blue'|'green'|'yellow'|'red'  (4 zones, no orange)
bbwp_state        : str              — 'BLUE_DOUBLE'|'BLUE'|'MA_CROSS_UP'|'MA_CROSS_DOWN'|'NORMAL'|'RED'|'RED_DOUBLE'
bbwp_points       : int (0-2)        — grade points for Four Pillars
bbwp_is_blue_bar  : bool             — extreme low background
bbwp_is_red_bar   : bool             — extreme high background
bbwp_ma_cross_up  : bool             — crossover event (single bar)
bbwp_ma_cross_down: bool             — crossunder event (single bar)
```

**Spectrum color mapping (4-tier, matching Pine v2 gradient inflection points):**
```python
def _spectrum_color(bbwp_value):
    """
    Matches Pine v2 f_spectrumColor gradient zones at 25/50/75.
    4 colors (orange removed — Pine has no discrete orange zone).
    Returns None for NaN input (warmup bars).
    """
    if np.isnan(bbwp_value): return None
    if bbwp_value <= 25:     return 'blue'
    elif bbwp_value <= 50:   return 'green'
    elif bbwp_value <= 75:   return 'yellow'
    else:                    return 'red'
```

### Calculation Logic:
```python
# 1. BB basis
basis = SMA(close, basis_len)

# 2. BB width
stdev = rolling_std(close, basis_len)
bbw = (2 * stdev) / basis

# 3. BBWP (percentile rank)
bbwp = rolling_percentrank(bbw, lookback)

# 4. BBWP MA
bbwp_ma = SMA(bbwp, bbwp_ma_len)

# 5. State detection (priority order, same as Pine v2)
```

---

## LAYER 2: SEQUENCE TRACKER — `signals/bbw_sequence.py`

### Function: `track_bbw_sequence(df)`

**Output columns added:**
```
bbw_seq_prev_color     : str    — previous bar's spectrum color
bbw_seq_color_changed  : bool   — color transition this bar
bbw_seq_bars_in_color  : int    — consecutive bars at current spectrum color
bbw_seq_bars_in_state  : int    — consecutive bars in current BBWP state
bbw_seq_direction      : str    — 'expanding'|'contracting'|'flat'
bbw_seq_skip_detected  : bool   — color skipped a step
bbw_seq_pattern_id     : str    — current sequence pattern (e.g., 'BG' = blue→green)
bbw_seq_from_blue_bars : int    — bars since last blue state
bbw_seq_from_red_bars  : int    — bars since last red state
```

### Sequence Direction Logic:
```python
COLOR_ORDER = {'blue': 0, 'green': 1, 'yellow': 2, 'red': 3}  # 4 colors, orange removed

def _sequence_direction(prev_color, curr_color):
    if prev_color == curr_color: return 'flat'
    return 'expanding' if COLOR_ORDER[curr_color] > COLOR_ORDER[prev_color] else 'contracting'

def _is_skip(prev_color, curr_color):
    return abs(COLOR_ORDER[curr_color] - COLOR_ORDER[prev_color]) > 1
```

### Pattern ID Encoding:
```
'BGY'  = blue → green → yellow  (normal expansion)
'GYR'  = green → yellow → red   (normal expansion)
'RYG'  = red → yellow → green   (normal contraction)
'BYR'  = blue → yellow → red    (skipped green) ← SKIP
'RG'   = red → green             (skipped yellow) ← SKIP
```

---

## LAYER 3: FORWARD RETURN TAGGER — `research/bbw_forward_returns.py`

### Function: `tag_forward_returns(df, windows=[10, 20])`

**Windows:** 10 bars (50min on 5m) and 20 bars (1h40 on 5m).

**Output columns per window:**
```
fwd_10_max_up_pct    : float  — max upside in %
fwd_10_max_down_pct  : float  — max downside in %
fwd_10_max_up_atr    : float  — max upside in ATR multiples
fwd_10_max_down_atr  : float  — max downside in ATR multiples
fwd_10_close_pct     : float  — close[bar+10] vs close[bar], %
fwd_10_direction     : str    — 'up' or 'down'
fwd_10_max_range_atr : float  — full range in ATR multiples
fwd_10_proper_move   : bool   — True if max_range_atr >= 3.0
```

**NOTE:** These are raw directional components, NOT MFE/MAE. Layer 4 assigns direction:
- LONG: MFE = max_up_atr, MAE = max_down_atr
- SHORT: MFE = max_down_atr, MAE = max_up_atr

**"Proper move" threshold:** 3 ATR (matches DOGE 3.32 R:R trade).

---

## LAYER 4: SIMULATOR ENGINE — `research/bbw_simulator.py`

### Analysis Groups:

| Group | Grouping | Purpose |
|-------|----------|---------|
| A | By bbwp_state | Core: which states produce best opportunities |
| B | By bbwp_spectrum | Finer granularity than state |
| C | By bbw_seq_direction | Expanding vs contracting vs flat |
| D | By bbw_seq_pattern_id | Which color sequences predict moves |
| E | By bbw_seq_skip_detected | Does skipping a color predict anything |
| F | By bars_in_state (binned) | Does duration in blue predict bigger moves |
| G | By MA cross + spectrum combo | What happens after MA cross at different levels |

### LSG Grid Search:

```python
LEVERAGE_GRID  = [5, 10, 15, 20]
SIZE_GRID      = [0.25, 0.5, 0.75, 1.0]    # fraction of $250
TARGET_GRID    = [1, 2, 3, 4, 5, 6]         # ATR multiples
SL_GRID        = [1.0, 1.5, 2.0, 3.0]       # ATR multiples
WINDOWS        = [10, 20]
DIRECTIONS     = ['long', 'short']
```

**Total: 7 states × 2 dir × 4 SL × 4 lev × 4 size × 6 tgt × 2 win = 10,752 combos**

Vectorized with numpy. No Python loops over bars.

### Scaling Sequence Simulation:

```python
SCALE_SCENARIOS = [
    # (entry_state, entry_size, add_trigger_state, add_size, max_bars_to_wait)
    ('NORMAL',     0.50, 'BLUE',        0.50, 10),
    ('NORMAL',     0.50, 'BLUE',        0.50, 20),
    ('NORMAL',     0.50, 'BLUE_DOUBLE', 0.50, 20),
    ('BLUE',       0.50, 'BLUE_DOUBLE', 0.50, 10),
    ('MA_CROSS_UP',0.50, 'BLUE',        0.50, 10),
    ('NORMAL',     0.25, 'BLUE',        0.75, 15),
]
```

Verdicts: `USE` (triggered >= 30% AND edge >= 20%), `MARGINAL`, `SKIP` (triggered < 15%).

---

## LAYER 4b: MONTE CARLO VALIDATION — `research/bbw_monte_carlo.py`

See [[BBW-STATISTICS-RESEARCH]] for full implementation.

Per BBW state's top LSG combo:
- 1000x trade order shuffle → rebuild equity curve each time
- 95% confidence intervals on PnL, max DD, Sharpe
- Overfit detection: real PnL must beat 95th percentile of shuffled
- Output: `reports/bbw/monte_carlo/` with per-state verdicts

---

## LAYER 5: REPORT GENERATOR — `research/bbw_report.py`

### Report Contents:

```
reports/bbw/
├── aggregate/
│   ├── bbw_state_stats.csv
│   ├── spectrum_color_stats.csv
│   ├── sequence_direction_stats.csv
│   ├── sequence_pattern_stats.csv
│   ├── skip_detection_stats.csv
│   ├── duration_cross_stats.csv
│   └── ma_cross_stats.csv
├── scaling/
│   └── scaling_sequences.csv
├── per_tier/
│   ├── tier_0_optimal_lsg.csv
│   ├── tier_1_optimal_lsg.csv
│   ├── tier_2_optimal_lsg.csv
│   └── tier_3_optimal_lsg.csv
├── sensitivity/
│   └── param_sensitivity.csv
├── monte_carlo/
│   ├── mc_summary_by_state.csv
│   ├── mc_confidence_intervals.csv
│   ├── mc_equity_distribution.csv
│   └── mc_overfit_flags.csv
└── ollama/
    ├── state_analysis.md
    ├── anomaly_flags.md
    ├── feature_recommendations.md
    └── executive_summary.md
```

---

## LAYER 6: OLLAMA ANALYSIS — `research/bbw_ollama_review.py`

Local LLM analysis of simulation results. Runs AFTER Layers 1-5 produce the CSVs.

### Why Ollama (not numpy)

The math is done. Layers 1-5 produce numbers. Layer 6 needs **reasoning about those numbers** in trading context — exactly what an LLM does well.

| Task | What numpy does | What Ollama adds |
|------|----------------|-----------------|
| State stats | Calculates mean, std, skew | Explains "BLUE has positive skew = squeeze breakouts tend to overshoot to the upside" |
| Monte Carlo | Produces confidence intervals | Flags "RED_DOUBLE params passed MC but sample size is only 31K — thin data" |
| Overfit detection | Binary pass/fail | Contextualizes "MA_CROSS_UP failed MC — edge likely from 2 outlier coins, not systematic" |
| Feature importance | Mutual information scores | Recommends "bbwp_acceleration has near-zero MI — consider dropping from VINCE to reduce noise" |
| Scaling verdicts | triggered_pct and edge_pct | Synthesizes "NORMAL→BLUE(10bar) at 34% trigger rate gives +29% edge. At your 160 trades/day on AXS, that's ~54 scale-ins/day — operationally viable" |
| Cross-tier comparison | Per-tier CSVs | Identifies "tier_3 coins (RIVER-like) show 2x expectancy in BLUE vs tier_0 (BTC-like) — BBW is more useful on volatile coins" |

### Model Selection

```python
OLLAMA_CONFIG = {
    'code_review': {
        'model': 'qwen2.5-coder:32b',     # Reviews generated Python code
        'use_when': 'After each Layer is built, before tests',
        'prompt_type': 'code_audit',
    },
    'results_analysis': {
        'model': 'qwen3:8b',               # Fast, good reasoning
        'use_when': 'After Layer 5 produces CSVs',
        'prompt_type': 'trading_analysis',
    },
    'deep_analysis': {
        'model': 'qwen3-coder:30b',        # Complex multi-file analysis
        'use_when': 'Final executive summary, anomaly investigation',
        'prompt_type': 'research_synthesis',
    },
}
```

### Integration Points

```python
import requests
import json

def ollama_analyze(prompt, model='qwen3:8b', temperature=0.3):
    """Send analysis prompt to local Ollama instance."""
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': model,
            'prompt': prompt,
            'temperature': temperature,
            'stream': False,
        }
    )
    return response.json()['response']

# --- INTEGRATION POINT 1: Code Review ---
# After each Layer .py file is built
def review_layer_code(filepath, spec_text):
    """qwen2.5-coder:32b reviews code against spec."""
    code = open(filepath).read()
    prompt = f"""Review this Python code against its specification.
Flag: logic errors, off-by-one, missing edge cases, vectorization opportunities.

SPEC:
{spec_text}

CODE:
{code}

Output: bullet list of issues found, or "PASS" if clean."""
    return ollama_analyze(prompt, model='qwen2.5-coder:32b')

# --- INTEGRATION POINT 2: State Analysis ---
# After Layer 5 produces aggregate CSVs
def analyze_state_stats(state_stats_csv, mc_summary_csv):
    """qwen3:8b interprets statistical results in trading context."""
    state_data = open(state_stats_csv).read()
    mc_data = open(mc_summary_csv).read()
    prompt = f"""You are analyzing BBW Simulator results for a crypto scalping system.
Context: 399 coins, 5m timeframe, $250 position × up to 20x leverage.

STATE STATISTICS:
{state_data}

MONTE CARLO RESULTS:
{mc_data}

Provide:
1. Which BBW states have statistically significant edges (KS p < 0.05)?
2. Are the optimal LSG parameters robust (MC pass) or overfit?
3. Which states should be traded aggressively vs cautiously?
4. Any surprising findings or contradictions in the data?
5. Specific recommendations for the BBW_LSG_MAP config.

Be direct. No disclaimers. This is for a professional trader."""
    return ollama_analyze(prompt, model='qwen3:8b')

# --- INTEGRATION POINT 3: Feature Recommendations ---
# After mutual information scoring
def analyze_features(mi_scores_csv):
    """qwen3:8b recommends feature pruning for VINCE."""
    mi_data = open(mi_scores_csv).read()
    prompt = f"""These are mutual information scores for BBW features predicting forward price direction.

{mi_data}

Which features should be:
- KEPT (high MI, trading-relevant)
- DROPPED (near-zero MI, adds noise)
- COMBINED (correlated features that should be merged)
- ENGINEERED (new derived features suggested by the patterns)

Consider: 17 features total, target is binary up/down, XGBoost model."""
    return ollama_analyze(prompt, model='qwen3:8b')

# --- INTEGRATION POINT 4: Anomaly Detection ---
# After Monte Carlo flags potential overfits
def investigate_anomalies(overfit_flags_csv, per_tier_dir):
    """qwen3-coder:30b investigates flagged anomalies across tiers."""
    flags = open(overfit_flags_csv).read()
    tier_data = {}
    for f in Path(per_tier_dir).glob('*.csv'):
        tier_data[f.stem] = open(f).read()
    
    prompt = f"""Monte Carlo flagged these BBW states as potentially overfit:
{flags}

Per-tier breakdowns:
{json.dumps(tier_data, indent=2)}

Investigate:
1. Is the overfit driven by specific coin tiers?
2. Are there outlier coins inflating the results?
3. Should the flagged LSG params be adjusted or discarded?
4. What would a conservative alternative look like?"""
    return ollama_analyze(prompt, model='qwen3-coder:30b', temperature=0.2)

# --- INTEGRATION POINT 5: Executive Summary ---
# Final output combining all analyses
def generate_executive_summary(all_analysis_results):
    """qwen3-coder:30b produces final actionable summary."""
    prompt = f"""Synthesize all BBW Simulator findings into an executive summary.

{json.dumps(all_analysis_results, indent=2)}

Structure:
1. HEADLINE: One sentence — is BBW useful as an LSG tuner?
2. BEST STATES: Top 3 BBW states by risk-adjusted expectancy
3. LSG MAP: Final recommended BBW_LSG_MAP config (Python dict)
4. SCALING: Which scaling sequences to implement
5. WARNINGS: States/params that failed MC or have thin data
6. VINCE FEATURES: Final 17→N feature list after pruning
7. NEXT STEPS: What to build/test next

Output as Obsidian markdown."""
    return ollama_analyze(prompt, model='qwen3-coder:30b', temperature=0.1)

# --- INTEGRATION POINT 6: Build Log ---
# After each build step completes
def generate_build_log(step_name, test_results, duration):
    """qwen3:8b writes structured build log entry."""
    prompt = f"""Write a concise build log entry for Obsidian.

Step: {step_name}
Test results: {test_results}
Duration: {duration}

Format: timestamp, what was built, test pass/fail, issues found, next step.
Keep it under 10 lines."""
    return ollama_analyze(prompt, model='qwen3:8b', temperature=0.1)
```

### Ollama Pipeline Sequence

```
Layer 5 produces CSVs
        │
        ▼
┌─ POINT 2: State Analysis (qwen3:8b) ──────────────┐
│  Reads: state_stats.csv + mc_summary.csv           │
│  Writes: reports/bbw/ollama/state_analysis.md       │
└────────────────────────────────────────────────────┘
        │
        ▼
┌─ POINT 3: Feature Recommendations (qwen3:8b) ─────┐
│  Reads: mi_scores.csv                              │
│  Writes: reports/bbw/ollama/feature_recommendations.md │
└────────────────────────────────────────────────────┘
        │
        ▼
┌─ POINT 4: Anomaly Investigation (qwen3-coder:30b) ┐
│  Reads: mc_overfit_flags.csv + per_tier/*.csv      │
│  Writes: reports/bbw/ollama/anomaly_flags.md        │
└────────────────────────────────────────────────────┘
        │
        ▼
┌─ POINT 5: Executive Summary (qwen3-coder:30b) ────┐
│  Reads: all previous Ollama outputs                │
│  Writes: reports/bbw/ollama/executive_summary.md    │
└────────────────────────────────────────────────────┘
```

### Runtime for Ollama Layer

| Point | Model | Input size | Est. time |
|-------|-------|-----------|-----------|
| Code review (per layer) | qwen2.5-coder:32b | ~500 lines | ~30s per file |
| State analysis | qwen3:8b | ~2KB CSV | ~15s |
| Feature recommendations | qwen3:8b | ~1KB CSV | ~10s |
| Anomaly investigation | qwen3-coder:30b | ~10KB multi-file | ~45s |
| Executive summary | qwen3-coder:30b | ~5KB combined | ~30s |
| Build log (per step) | qwen3:8b | ~200 bytes | ~5s |

**Total Ollama time: ~3 minutes** (runs after the 31-minute compute pipeline)

---

## COIN CLASSIFIER — `research/coin_classifier.py`

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

def classify_coin_tiers(coin_stats_df, n_clusters=4):
    """
    Features per coin:
      - avg_atr_pct:     mean(ATR / close * 100)
      - avg_bbw_raw:     mean raw BB width
      - avg_daily_range: mean((high - low) / close * 100)
      - avg_base_vol:    mean daily volume in base currency
      - vol_of_vol:      std(ATR) / mean(ATR)
    
    KMeans with k=3,4,5 — pick best silhouette score.
    Labels sorted by avg_atr_pct: tier_0 (calmest) → tier_3 (wildest).
    """
```

---

## CONNECTION TO EXISTING SYSTEM

After simulator + Ollama produce optimal LSG mapping:

```python
# Generated by Layer 6 executive summary
BBW_LSG_MAP = {
    'BLUE_DOUBLE': {'best_dir': 'long', 'leverage': 20, 'size_frac': 1.0, 'target_atr': 5, 'sl_atr': 2.0},
    'BLUE':        {'best_dir': 'long', 'leverage': 20, 'size_frac': 0.75, 'target_atr': 4, 'sl_atr': 1.5},
    'MA_CROSS_UP': {'best_dir': 'long', 'leverage': 15, 'size_frac': 0.5, 'target_atr': 3, 'sl_atr': 2.0},
    'NORMAL':      {'best_dir': 'neutral', 'leverage': 10, 'size_frac': 0.5, 'target_atr': 2, 'sl_atr': 1.5},
    'MA_CROSS_DOWN':{'best_dir': 'short', 'leverage': 10, 'size_frac': 0.25, 'target_atr': 2, 'sl_atr': 1.0},
    'RED':         {'best_dir': 'short', 'leverage': 10, 'size_frac': 0.25, 'target_atr': 2, 'sl_atr': 1.0},
    'RED_DOUBLE':  {'best_dir': 'short', 'leverage': 5, 'size_frac': 0.25, 'target_atr': 1, 'sl_atr': 1.0},
}
# NOTE: Values above are placeholders — real values come from simulation data
```

Pipeline flow:
1. `signals/bbwp.py` → imported by `signals/four_pillars.py`
2. `bbwp_state` feeds state machine → reads `BBW_LSG_MAP` for sizing
3. Conflict handling: if pillars say LONG but BBW best_dir says SHORT → reduce size_frac
4. `ml/features.py` gets 17 BBW features + other pillar features → VINCE

---

## FILE STRUCTURE

```
four-pillars-backtester/
├── signals/
│   ├── bbwp.py                    ← Layer 1 (reusable)
│   └── bbw_sequence.py            ← Layer 2 (reusable)
├── research/
│   ├── __init__.py
│   ├── coin_classifier.py         ← Pre-step: KMeans
│   ├── bbw_forward_returns.py     ← Layer 3
│   ├── bbw_simulator.py           ← Layer 4
│   ├── bbw_monte_carlo.py         ← Layer 4b
│   ├── bbw_report.py              ← Layer 5
│   └── bbw_ollama_review.py       ← Layer 6
├── scripts/
│   └── run_bbw_simulator.py       ← CLI entry point
├── data/cache/                     ← existing 399 coins
├── reports/bbw/
│   ├── aggregate/
│   ├── scaling/
│   ├── per_tier/
│   ├── sensitivity/
│   ├── monte_carlo/
│   └── ollama/
└── tests/
    ├── test_bbwp.py
    ├── test_bbw_sequence.py
    ├── test_forward_returns.py
    ├── test_coin_classifier.py
    ├── test_bbw_simulator.py
    ├── test_bbw_monte_carlo.py
    └── test_bbw_report.py
```

---

## CLI ENTRY POINT — `scripts/run_bbw_simulator.py`

```
Usage:
  python scripts/run_bbw_simulator.py                          # all 399 coins, 5m
  python scripts/run_bbw_simulator.py --symbol RIVERUSDT       # single coin
  python scripts/run_bbw_simulator.py --tier tier_3            # one tier only
  python scripts/run_bbw_simulator.py --timeframe 1m           # 1m data
  python scripts/run_bbw_simulator.py --sensitivity            # param grid search
  python scripts/run_bbw_simulator.py --top 50                 # top 50 by volume
  python scripts/run_bbw_simulator.py --no-ollama              # skip LLM analysis
  python scripts/run_bbw_simulator.py --ollama-model qwen3:8b  # override model
  python scripts/run_bbw_simulator.py --no-monte-carlo         # skip MC validation
  python scripts/run_bbw_simulator.py --mc-sims 5000           # more MC iterations

Flags:
  --symbol SYMBOL         Run single coin only
  --tier TIER             Filter by volatility tier
  --timeframe TF          1m or 5m (default: 5m)
  --sensitivity           Run BBWP parameter grid search
  --top N                 Process top N coins by file size
  --windows 10,20         Forward return windows (default: 10,20)
  --proper-move-atr N     ATR threshold for "proper move" (default: 3.0)
  --sl-grid 1,1.5,2,3    SL distances to test
  --no-scaling            Skip scaling sequence simulation
  --no-monte-carlo        Skip Monte Carlo validation
  --mc-sims N             Monte Carlo iterations (default: 1000)
  --no-ollama             Skip Ollama analysis layer
  --ollama-model MODEL    Override Ollama model for analysis
  --output-dir PATH       Output directory (default: reports/bbw/)
  --verbose               Print progress per coin
```

---

## RUNTIME ESTIMATE

| Phase | Time |
|-------|------|
| Pre-step (coin classification) | ~30s |
| Layers 1-4 (399 coins × 5m) | ~8 min |
| Layer 4b (Monte Carlo, 1000 sims) | ~23 min |
| Layer 5 (report generation) | ~30s |
| Layer 6 (Ollama analysis) | ~3 min |
| **Total** | **~35 min** |

With parameter sensitivity (5 param combos): ~2.5 hours
With 1m data (5x more bars): ~3 hours

---

## DEPENDENCIES

| Package | Installed | Used By |
|---------|-----------|---------|
| pandas | ✅ | All layers |
| numpy | ✅ | All layers |
| pathlib | ✅ | File handling |
| scipy.stats | ✅ | skew, kurtosis, KS test |
| scikit-learn | ✅ | KMeans, silhouette, mutual_info |
| requests | ✅ | Ollama API calls |

---

## DECISIONS LOCKED

| Decision | Choice |
|----------|--------|
| Stop loss | Test multiple: 1, 1.5, 2, 3 ATR |
| Forward windows | 10 bars (50min) and 20 bars (1h40) on 5m |
| Scaling sequences | Yes — test enter-partial + add-on-improvement |
| Proper move threshold | 3 ATR |
| Coin grouping | Data-driven KMeans clustering |
| Monte Carlo | Yes — 1000 sims per state, 95% CI |
| Ollama integration | Yes — Layer 6 for analysis/interpretation |
| Ollama models | qwen3:8b (fast analysis), qwen2.5-coder:32b (code review), qwen3-coder:30b (deep analysis) |
| TDI | Out of scope |
| Ripster/AVWAP at entry | Out of scope — belongs in ml/features.py |

All design questions resolved. Ready for Claude Code build.
