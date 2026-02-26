# BBW V2 Layer 4b Build Journal
**Build Date:** 2026-02-16
**File:** `research/bbw_monte_carlo_v2.py`
**Status:** BUILD STARTED

---

## Session Metadata

**Start Time:** 2026-02-16 (continuing from Layer 4)
**Build Phase:** Layer 4b - Monte Carlo Validation V2
**Expected Duration:** 3-4 hours
**Test Target:** 30+ unit tests, 100+ assertions

---

## Architecture Overview

**Layer 4b V2 vs V1 Differences:**

| Aspect | V1 (bbw_monte_carlo.py) | V2 (THIS BUILD) |
|--------|-------------------------|-----------------|
| Input | OHLC + simulated trades | BBWAnalysisResultV2 (real backtester results) |
| Trade source | Simulator generates trades | Analyzer provides existing trades |
| per_trade_pnl | Calculated from simulation | Extracted from backtester results |
| Validation | Simulated edge robustness | Real backtester edge robustness |
| Direction | BBW decides direction | Four Pillars strategy decides |

**Key Point:** V2 validates REAL backtester results, V1 validated SIMULATED results.

---

## Build Plan Overview

### Phase 1: Input Validation (20 min)
- [ ] `validate_monte_carlo_input()` function
- [ ] Check BBWAnalysisResultV2 structure
- [ ] Verify per_trade_pnl arrays exist
- [ ] 5 unit tests

### Phase 2: Bootstrap Testing (45 min)
- [ ] `run_bootstrap_pnl()` function
- [ ] Resample with replacement
- [ ] Calculate confidence intervals for PnL metrics
- [ ] 8 unit tests

### Phase 3: Permutation Testing (45 min)
- [ ] `run_permutation_dd()` function
- [ ] Shuffle trade sequence (path-dependent)
- [ ] Calculate drawdown/MCL percentiles
- [ ] 8 unit tests

### Phase 4: Verdict Classification (30 min)
- [ ] `classify_verdict()` function
- [ ] ROBUST/FRAGILE/COMMISSION_KILL/INSUFFICIENT logic
- [ ] Threshold checks
- [ ] 6 unit tests

### Phase 5: Main Pipeline (30 min)
- [ ] `run_monte_carlo_v2()` orchestrator
- [ ] MonteCarloResultV2 dataclass
- [ ] Assemble all results
- [ ] 5 integration tests

### Phase 6: Debug Script (60 min)
- [ ] `scripts/debug_bbw_monte_carlo_v2.py`
- [ ] Visual confidence interval plots (ASCII)
- [ ] Verdict distribution
- [ ] Hand-computed checks

### Phase 7: Sanity Check (30 min)
- [ ] Run on Layer 4 output
- [ ] Validate verdicts make sense
- [ ] Export results

---

## Input Contract

**BBWAnalysisResultV2 (from Layer 4):**
```python
@dataclass
class BBWAnalysisResultV2:
    results: pd.DataFrame           # All (state, direction, LSG) groups
    best_combos: pd.DataFrame       # Top LSG per (state, direction)
    directional_bias: pd.DataFrame  # LONG vs SHORT comparison
    summary: dict                   # Metadata
    symbol: str
    n_trades_analyzed: int
    n_states: int
    date_range: Tuple[datetime, datetime]
    runtime_seconds: float
```

**Key column needed:** `per_trade_pnl` (list of floats) in best_combos DataFrame

---

## Output Contract

**MonteCarloResultV2:**
```python
@dataclass
class MonteCarloResultV2:
    state_verdicts: pd.DataFrame
        # Columns: bbw_state, direction, n_trades, mean_pnl,
        #          ci_lower, ci_upper, verdict, verdict_reason

    confidence_intervals: pd.DataFrame
        # Columns: bbw_state, direction, metric (pnl/sharpe/sortino),
        #          real_value, ci_lower, ci_upper, pctl_rank

    overfit_flags: pd.DataFrame
        # Columns: bbw_state, direction, sample_size_flag,
        #          commission_kill_flag, dd_fragile_flag, verdict

    summary: dict
        # Keys: n_states_tested, n_robust, n_fragile,
        #       n_commission_kill, runtime_seconds
```

---

## Core Logic Definitions

### Bootstrap PnL (with replacement)

```python
def run_bootstrap_pnl(per_trade_pnl: list, n_sims: int = 1000):
    """Bootstrap resample PnL to get confidence intervals.

    Logic:
    1. For each simulation:
       - Resample n trades WITH replacement
       - Calculate mean PnL
    2. Sort simulated means
    3. Extract 5th and 95th percentiles (90% CI)
    4. Return (ci_lower, ci_upper, bootstrap_means)
    """
    n_trades = len(per_trade_pnl)
    pnl_array = np.array(per_trade_pnl)
    bootstrap_means = []

    for _ in range(n_sims):
        # Resample with replacement
        sample = np.random.choice(pnl_array, size=n_trades, replace=True)
        bootstrap_means.append(sample.mean())

    bootstrap_means = np.array(bootstrap_means)
    ci_lower = np.percentile(bootstrap_means, 5)
    ci_upper = np.percentile(bootstrap_means, 95)

    return ci_lower, ci_upper, bootstrap_means
```

### Permutation DD (without replacement, path-dependent)

```python
def run_permutation_dd(per_trade_pnl: list, n_sims: int = 1000):
    """Permutation test for drawdown robustness.

    Logic:
    1. Calculate REAL max drawdown from original sequence
    2. For each simulation:
       - Shuffle trade sequence (permute)
       - Calculate max drawdown on shuffled sequence
    3. Compare real DD to permuted distribution
    4. If real DD > 95th percentile → fragile (path-dependent)
    """
    pnl_array = np.array(per_trade_pnl)

    # Real drawdown
    real_equity = np.cumsum(pnl_array)
    real_peak = np.maximum.accumulate(real_equity)
    real_dd = np.max(real_peak - real_equity)

    # Permutation distribution
    permuted_dds = []
    for _ in range(n_sims):
        shuffled = np.random.permutation(pnl_array)
        equity = np.cumsum(shuffled)
        peak = np.maximum.accumulate(equity)
        dd = np.max(peak - equity)
        permuted_dds.append(dd)

    permuted_dds = np.array(permuted_dds)
    p95 = np.percentile(permuted_dds, 95)

    # If real DD is much worse than typical permutation, it's fragile
    is_fragile = real_dd > p95

    return real_dd, p95, is_fragile
```

### Verdict Classification

```python
def classify_verdict(
    n_trades: int,
    mean_pnl: float,
    ci_lower: float,
    ci_upper: float,
    commission_per_trade: float,
    dd_fragile: bool,
    min_trades: int = 100,
    min_net_expectancy: float = 1.0
):
    """Classify edge robustness.

    Verdicts:
    - INSUFFICIENT: n_trades < min_trades
    - COMMISSION_KILL: ci_upper < 0 (even best case loses money)
    - FRAGILE: ci_lower < 0 OR dd_fragile (inconsistent edge)
    - ROBUST: ci_lower >= min_net_expectancy (consistent profitable edge)
    """
    if n_trades < min_trades:
        return "INSUFFICIENT", f"Only {n_trades} trades (need {min_trades})"

    if ci_upper < 0:
        return "COMMISSION_KILL", f"Even 95th percentile loses: {ci_upper:.2f}"

    if ci_lower < 0:
        return "FRAGILE", f"5th percentile negative: {ci_lower:.2f}"

    if dd_fragile:
        return "FRAGILE", "Drawdown fragile (path-dependent)"

    if ci_lower >= min_net_expectancy:
        return "ROBUST", f"Consistent edge: CI=[{ci_lower:.2f}, {ci_upper:.2f}]"

    return "FRAGILE", f"Weak edge: CI=[{ci_lower:.2f}, {ci_upper:.2f}]"
```

---

## Math Validations Tracker

### Validation 1: Bootstrap CI Coverage
**Status:** NOT TESTED
**Expected Result:**
```
Known PnL: [10, 10, 10, 10, 10] (all identical)
Bootstrap: All samples = 10
ci_lower = 10, ci_upper = 10 (no variance)

Known PnL: [5, 10, 15, 20, 25] (uniform)
mean = 15
Bootstrap 1000 sims → ci_lower ~= 7, ci_upper ~= 23 (roughly)
ASSERTION: Real mean in [ci_lower, ci_upper]
```

### Validation 2: Permutation DD Detection
**Status:** NOT TESTED
**Expected Result:**
```
Sequence: [+10, -20, +10, -20, +10] (oscillating)
Real DD = 20 (worst path: +10, -20, -20 = -30 from +10 peak)

Permutation: Shuffle breaks pattern
If pattern-dependent: real_dd > p95
If random: real_dd ~= median(permuted_dds)

ASSERTION: Fragile flag = True if pattern exists
```

### Validation 3: Verdict Logic
**Status:** NOT TESTED
**Expected Result:**
```
Case 1: n_trades = 50 → INSUFFICIENT
Case 2: ci_upper = -2.0 → COMMISSION_KILL
Case 3: ci_lower = -1.0, ci_upper = +5.0 → FRAGILE
Case 4: ci_lower = +2.0, ci_upper = +8.0 → ROBUST
```

---

## Build Log (Chronological)

### Entry 1: [TIMESTAMP] - Journal Created
**Phase:** Pre-Build
**Action:** Created build journal for Layer 4b V2
**Status:** Ready to start Monte Carlo validation build

**Next Steps:**
1. Create MonteCarloResultV2 dataclass
2. Write `validate_monte_carlo_input()` function
3. Write 5 input validation tests
4. Run tests and verify PASS

**Critical Rules Active:**
- Test-first development
- No Windows backslash paths
- py_compile before every run
- All functions need docstrings

---

## Files to Create

### Core Module
- [ ] `research/bbw_monte_carlo_v2.py` (~400-500 lines)
  - MonteCarloResultV2 dataclass
  - 5 core functions
  - Helper functions

### Test Suite
- [ ] `tests/test_bbw_monte_carlo_v2.py` (~400-500 lines)
  - 30+ unit tests
  - Mock data generators
  - Hand-computed validations

### Scripts
- [ ] `scripts/debug_bbw_monte_carlo_v2.py` (~300 lines)
  - Visual confidence interval display
  - Verdict distribution
  - Hand-checks

---

## Success Criteria

### Code Complete When:
- [ ] All 30+ unit tests PASS
- [ ] Bootstrap CI coverage validated
- [ ] Permutation DD detection validated
- [ ] Verdict classification logic validated
- [ ] Integration with Layer 4 output tested
- [ ] Debug script validates results
- [ ] Runtime < 30 seconds for typical dataset

### Ready for Layer 5 When:
- [ ] MonteCarloResultV2 output validated
- [ ] All verdicts make sense (manual review)
- [ ] state_verdicts DataFrame has required columns
- [ ] confidence_intervals DataFrame complete
- [ ] overfit_flags DataFrame complete
- [ ] Multi-state coverage (tests multiple BBW states)

---

**END OF JOURNAL HEADER - BUILD LOG ENTRIES BEGIN BELOW**

---
