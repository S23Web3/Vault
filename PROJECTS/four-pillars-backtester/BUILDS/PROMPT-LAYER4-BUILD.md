# CLAUDE CODE PROMPT — Layer 4: Simulator Engine

## CONTEXT

Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
Layer 1 (`signals\bbwp.py`) — 61/61 PASS
Layer 2 (`signals\bbw_sequence.py`) — 68/68 PASS, 148/148 debug PASS
Layer 3 (`research\bbw_forward_returns.py`) — BUILDING NOW (do not touch)

Layer 4 consumes ALL output columns from Layers 1-3.
Layer 4 is the CORE VALUE — it answers: "For each BBW state, what LSG settings maximize expectancy?"

## MANDATORY — READ FIRST

1. Read skill file: `skills\python\SKILL.md`
2. Read `signals\bbwp.py` (Layer 1 output columns)
3. Read `signals\bbw_sequence.py` (Layer 2 output columns)
4. Read `BUILDS\PROMPT-LAYER3-BUILD.md` (Layer 3 output columns — file spec, do NOT run Layer 3)

## STRATEGY — TOKEN CONSERVATION

Layer 4 is complex. Split into 2 Claude Code sessions if needed.

**Session 1 (this prompt):**
1. Read skill + L1/L2/L3 specs (4 reads)
1b. **PRE-CHECK:** Verify Layer 3 exists and imports clean:
    `python -c "from research.bbw_forward_returns import tag_forward_returns; print('L3 OK')"`
    If this fails, STOP. Layer 3 must be built and passing before Layer 4 can proceed.
2. Create `research\bbw_simulator.py` in one shot
3. `python -m py_compile research\bbw_simulator.py` — MUST pass
4. Create `tests\test_bbw_simulator.py` in one shot
5. `python -m py_compile tests\test_bbw_simulator.py` — MUST pass
6. Run: `python tests\test_bbw_simulator.py`
7. Create `scripts\debug_bbw_simulator.py` in one shot
8. `python -m py_compile scripts\debug_bbw_simulator.py` — MUST pass
9. Run: `python scripts\debug_bbw_simulator.py`
10. Create `scripts\sanity_check_bbw_simulator.py` in one shot
11. `python -m py_compile scripts\sanity_check_bbw_simulator.py` — MUST pass
12. Run: `python scripts\sanity_check_bbw_simulator.py`
13. Create `scripts\run_layer4_tests.py` in one shot
14. Run: `python scripts\run_layer4_tests.py`

Total: ~18-22 tool calls

**If token cap hit after step 6:** Stop. Log progress. Session 2 picks up at step 7.

## CRITICAL — STRING SAFETY

All docstrings use forward slashes for paths: `research/bbw_simulator.py`
All code paths use `pathlib.Path` with forward slashes or relative joins.
NEVER put Windows backslash paths in docstrings, strings, or f-strings.
After writing each .py file: `python -m py_compile <file>` — if SyntaxError, fix before proceeding.

---

## SPEC: `research\bbw_simulator.py`

### Architecture

```
bbw_simulator.py
├── run_simulator(df, config=None) -> SimulatorResult
│   ├── _validate_input(df, config)
│   ├── _add_derived_columns(df, config)
│   ├── _assign_mfe_mae(df, direction, window)
│   ├── _compute_group_stats(df, group_col, windows, directions) -> pd.DataFrame
│   ├── _lsg_grid_search(df, config) -> pd.DataFrame
│   ├── _extract_top_combos(lsg_results, config, n_top=3) -> pd.DataFrame
│   ├── _scaling_simulation(df, scenarios, config, lsg_top) -> pd.DataFrame
│   └── returns SimulatorResult (dataclass)
└── SimulatorResult
    ├── group_stats: dict[str, pd.DataFrame]  # 7 analysis groups
    ├── lsg_results: pd.DataFrame              # full grid search results
    ├── lsg_top: pd.DataFrame                  # top 3 per state
    ├── scaling_results: pd.DataFrame          # scaling sequence results
    └── summary: dict                          # counts, runtime, metadata
```

### Input validation: `_validate_input(df, config)`

Required columns from Layer 1:
```python
L1_COLS = ['bbwp_value', 'bbwp_spectrum', 'bbwp_state', 'bbwp_is_blue_bar', 'bbwp_is_red_bar',
           'bbwp_ma_cross_up', 'bbwp_ma_cross_down']
```

Required columns from Layer 2:
```python
L2_COLS = ['bbw_seq_prev_color', 'bbw_seq_color_changed', 'bbw_seq_bars_in_color',
           'bbw_seq_bars_in_state', 'bbw_seq_direction', 'bbw_seq_skip_detected',
           'bbw_seq_pattern_id', 'bbw_seq_from_blue_bars', 'bbw_seq_from_red_bars']
```

Required columns from Layer 3 — **built dynamically from `config.windows`**:
```python
L3_FWD_SUFFIXES = ['max_up_pct', 'max_down_pct', 'max_up_atr', 'max_down_atr',
                   'close_pct', 'direction', 'max_range_atr', 'proper_move']
L3_OTHER = ['fwd_atr']

def _build_l3_cols(windows):
    cols = list(L3_OTHER)
    for w in windows:
        cols.extend([f'fwd_{w}_{suffix}' for suffix in L3_FWD_SUFFIXES])
    return cols

# Example: config.windows=[10,20] produces 17 required L3 columns
# Example: config.windows=[10] produces 9 required L3 columns (sanity check mode)
```

Also requires OHLCV: `['close']` (needed for PnL calculation).

Raises `ValueError` listing ALL missing columns if any absent.

### Config dataclass:

```python
@dataclass
class SimulatorConfig:
    # LSG Grid
    leverage_grid: list = field(default_factory=lambda: [5, 10, 15, 20])
    size_grid: list = field(default_factory=lambda: [0.25, 0.5, 0.75, 1.0])  # fraction of base_size
    target_atr_grid: list = field(default_factory=lambda: [1, 2, 3, 4, 5, 6])  # ATR multiples
    sl_atr_grid: list = field(default_factory=lambda: [1.0, 1.5, 2.0, 3.0])  # ATR multiples
    base_size: float = 250.0  # USD
    
    # Windows
    windows: list = field(default_factory=lambda: [10, 20])
    directions: list = field(default_factory=lambda: ['long', 'short'])
    
    # Scaling scenarios
    scaling_scenarios: list = field(default_factory=lambda: [
        # (entry_state, entry_size_frac, add_trigger_state, add_size_frac, max_bars_to_wait)
        ('NORMAL',      0.50, 'BLUE',        0.50, 10),
        ('NORMAL',      0.50, 'BLUE',        0.50, 20),
        ('NORMAL',      0.50, 'BLUE_DOUBLE', 0.50, 20),
        ('BLUE',        0.50, 'BLUE_DOUBLE', 0.50, 10),
        ('MA_CROSS_UP', 0.50, 'BLUE',        0.50, 10),
        ('NORMAL',      0.25, 'BLUE',        0.75, 15),
    ])
    
    # Thresholds
    min_sample_size: int = 30  # minimum bars in a group for stats to be meaningful
    scaling_use_threshold: float = 0.30  # triggered >= 30%
    scaling_edge_threshold: float = 0.20  # edge >= 20%
    
    # Analysis groups
    # NOTE: bins start at -1 (not 0) with right=True so that bin (-1, 5] captures values 1-5.
    # Layer 2 starts bars_in_state at 1 (never 0), but using -1 is defensive in case
    # any edge case or future change introduces 0.
    bars_in_state_bins: list = field(default_factory=lambda: [-1, 5, 10, 20, 50, 100, 999999])
    bars_in_state_labels: list = field(default_factory=lambda: ['1-5', '6-10', '11-20', '21-50', '51-100', '100+'])
```

### MFE/MAE Assignment: `_assign_mfe_mae(df, direction, window)`

This is where Layer 3's raw directional returns become trade-specific:

```python
def _assign_mfe_mae(df, direction, window):
    """
    LONG trade:  MFE = max_up_atr,   MAE = max_down_atr
    SHORT trade: MFE = max_down_atr,  MAE = max_up_atr
    
    Returns DataFrame with columns: mfe_atr, mae_atr, mfe_pct, mae_pct
    These are ALWAYS POSITIVE values:
    - mfe_atr: how far price moved IN YOUR FAVOR (ATR multiples)
    - mae_atr: how far price moved AGAINST YOU (ATR multiples)
    """
    prefix = f'fwd_{window}_'
    if direction == 'long':
        mfe_atr = df[f'{prefix}max_up_atr']
        mae_atr = df[f'{prefix}max_down_atr']
        mfe_pct = df[f'{prefix}max_up_pct']
        mae_pct = df[f'{prefix}max_down_pct'].abs()
    elif direction == 'short':
        mfe_atr = df[f'{prefix}max_down_atr']
        mae_atr = df[f'{prefix}max_up_atr']
        mfe_pct = df[f'{prefix}max_down_pct'].abs()
        mae_pct = df[f'{prefix}max_up_pct']
    return pd.DataFrame({'mfe_atr': mfe_atr, 'mae_atr': mae_atr,
                         'mfe_pct': mfe_pct, 'mae_pct': mae_pct}, index=df.index)
```

### Analysis Group Stats: `_compute_group_stats(df, group_col, windows, directions)`

For each unique value in `group_col`, for each window and direction.

**Source column mapping per iteration** (window=W, direction=D):
```python
# MFE/MAE come from _assign_mfe_mae(df, direction=D, window=W)
mfe_mae_df = _assign_mfe_mae(df, direction=D, window=W)

# These come from the CURRENT window's L3 columns:
close_pct_col    = f'fwd_{W}_close_pct'       # for mean/std/skew/kurtosis
direction_col    = f'fwd_{W}_direction'        # for directional_bias (values: 'up'/'down'/'flat')
range_atr_col    = f'fwd_{W}_max_range_atr'    # for mean_range_atr
proper_move_col  = f'fwd_{W}_proper_move'      # for proper_move_pct
```
Do NOT hardcode window=10 columns when iterating window=20.

```python
OUTPUT_COLS = [
    'group_value',         # the category value
    'window',              # 10 or 20
    'direction',           # 'long' or 'short'
    'n_bars',              # sample count
    'mean_mfe_atr',        # mean Maximum Favorable Excursion
    'median_mfe_atr',
    'p90_mfe_atr',
    'mean_mae_atr',        # mean Maximum Adverse Excursion
    'median_mae_atr',
    'p90_mae_atr',
    'mfe_mae_ratio',       # mean_mfe / mean_mae — edge indicator
    'mean_range_atr',      # mean total range
    'proper_move_pct',     # % of bars with proper_move=True
    'directional_bias',    # % of bars where market naturally moved in the trade direction
                           # MAPPING: direction='long' → count fwd_N_direction=='up'
                           #          direction='short' → count fwd_N_direction=='down'
                           # Do NOT compare fwd_N_direction == direction directly
                           # (L3 uses 'up'/'down'/'flat', not 'long'/'short')
    'mean_close_pct',      # mean close-to-close %
    'std_close_pct',       # std of close-to-close %
    'skew_close_pct',      # skewness — positive = fat right tail (good for longs)
    'kurtosis_close_pct',  # kurtosis — high = fat tails
    'edge_score',          # (mean_mfe - mean_mae) / std(close_pct) — risk-adjusted edge
]

# EDGE CASE HANDLING for group stats:
# - mfe_mae_ratio: if mean_mae == 0 → np.inf (no adverse excursion = perfect)
# - edge_score: if std_close_pct == 0 → NaN (flat price = no info)
# - Groups with n_bars < config.min_sample_size: still computed but flagged
#   in the output. Filtering happens in _extract_top_combos, not here.
```

### 7 Analysis Groups:

```python
ANALYSIS_GROUPS = {
    'A_state':       'bbwp_state',
    'B_spectrum':    'bbwp_spectrum',
    'C_direction':   'bbw_seq_direction',
    'D_pattern':     'bbw_seq_pattern_id',
    'E_skip':        'bbw_seq_skip_detected',
    'F_duration':    'duration_bin',          # derived: pd.cut(bbw_seq_bars_in_state, bins)
    'G_ma_spectrum': 'ma_spectrum_combo',     # derived: f"{ma_cross_state}_{spectrum}"
}
```

Group F requires creating a binned column first:
```python
df['duration_bin'] = pd.cut(df['bbw_seq_bars_in_state'], bins=config.bars_in_state_bins,
                            labels=config.bars_in_state_labels, right=True)
```

Group G requires creating a combo column:
```python
# MA cross state: 'cross_up' if bbwp_ma_cross_up, 'cross_down' if bbwp_ma_cross_down, 'no_cross' otherwise
# Combined: e.g., 'cross_up_blue', 'no_cross_yellow'
df['ma_spectrum_combo'] = df.apply(
    lambda r: f"{'cross_up' if r['bbwp_ma_cross_up'] else 'cross_down' if r['bbwp_ma_cross_down'] else 'no_cross'}_{r['bbwp_spectrum']}"
    if pd.notna(r['bbwp_spectrum']) else None, axis=1)
```

**IMPORTANT:** Do NOT use `.apply()` row-wise for the combo column in production code.

**CAUTION:** `np.char.add` on object arrays can convert None to string 'None',
producing garbage like 'no_cross_None'. Use pandas string ops on a pre-filtered mask:

```python
# Step 1: determine MA cross state (vectorized)
conditions = [df['bbwp_ma_cross_up'] == True, df['bbwp_ma_cross_down'] == True]
choices = ['cross_up', 'cross_down']
ma_state = pd.Series(np.select(conditions, choices, default='no_cross'), index=df.index)

# Step 2: build combo only where spectrum is valid (not None/NaN)
spectrum_valid = df['bbwp_spectrum'].notna()
combo = pd.Series(None, index=df.index, dtype=object)
combo[spectrum_valid] = ma_state[spectrum_valid] + '_' + df.loc[spectrum_valid, 'bbwp_spectrum']
df['ma_spectrum_combo'] = combo
# Result: 'cross_up_blue', 'no_cross_yellow', None (for NaN spectrum bars)
```

### Derived Column Builder: `_add_derived_columns(df, config)`

Creates the two derived columns needed by Groups F and G. Called once on `df_valid`
before group stats or grid search runs.

```python
def _add_derived_columns(df, config):
    """Add duration_bin and ma_spectrum_combo columns in-place.
    
    Modifies df directly (already a copy in the main flow).
    """
    # Group F: duration bins
    df['duration_bin'] = pd.cut(
        df['bbw_seq_bars_in_state'],
        bins=config.bars_in_state_bins,
        labels=config.bars_in_state_labels,
        right=True
    )
    
    # Group G: MA cross + spectrum combo
    conditions = [df['bbwp_ma_cross_up'] == True, df['bbwp_ma_cross_down'] == True]
    choices = ['cross_up', 'cross_down']
    ma_state = pd.Series(np.select(conditions, choices, default='no_cross'), index=df.index)
    spectrum_valid = df['bbwp_spectrum'].notna()
    combo = pd.Series(None, index=df.index, dtype=object)
    combo[spectrum_valid] = ma_state[spectrum_valid] + '_' + df.loc[spectrum_valid, 'bbwp_spectrum']
    df['ma_spectrum_combo'] = combo
```

---

### LSG Grid Search: `_lsg_grid_search(df, config)`

Internally groups by `df['bbwp_state']`. For each BBW state × direction × window, simulate every combo of (leverage, size, target_atr, sl_atr).

**Outer loop structure** (pseudo-code):
```python
for window in config.windows:
    for direction in config.directions:
        mfe_mae = _assign_mfe_mae(df, direction, window)
        close_pct = df[f'fwd_{window}_close_pct']   # MUST match current window
        atr_i = df['fwd_atr']
        close_i = df['close']
        for state in df['bbwp_state'].unique():
            mask = df['bbwp_state'] == state
            # run _vectorized_pnl on masked subset with all combos
```
CRITICAL: `close_pct` must come from the CURRENT window being evaluated.
Using `fwd_10_close_pct` for window=20 analysis would corrupt AMBIGUOUS/TIMEOUT PnL.

**Vectorized PnL calculation per combo:**

```python
def _vectorized_pnl(mfe_atr, mae_atr, close_pct, atr_i, close_i, direction,
                    target_atr, sl_atr, leverage, size_frac, base_size):
    """
    For each bar, determine if target or stop was hit first (approximation).
    
    Logic:
    - If mfe_atr >= target_atr AND mae_atr < sl_atr: WIN (target hit, stop never hit)
    - If mae_atr >= sl_atr AND mfe_atr < target_atr: LOSS (stop hit, target never hit)
    - If mfe_atr >= target_atr AND mae_atr >= sl_atr: AMBIGUOUS — use close_pct direction
    - If mfe_atr < target_atr AND mae_atr < sl_atr: TIMEOUT — use close_pct for PnL
    
    NOTE: This is a simplification. In real trading, the ORDER of hitting TP vs SL
    matters (which happened first within the bar). For 5m bars this is acceptable.
    The Monte Carlo layer (4b) will validate robustness.
    
    PnL calculation (all values are PER-BAR at the entry bar):
    - atr_i   = df['fwd_atr']   (ATR at this entry bar — from Layer 3)
    - close_i = df['close']      (close at this entry bar — entry price)
    - notional = size_frac * base_size * leverage  (e.g., 1.0 * $250 * 20 = $5000)
    
    - WIN:       +(target_atr * atr_i / close_i) * notional
    - LOSS:      -(sl_atr * atr_i / close_i) * notional
    - AMBIGUOUS: close_pct / 100 * notional  (for longs; negate close_pct for shorts)
                 We don't know TP/SL hit order, so use actual close outcome.
                 Classification: 'win' if pnl > 0 else 'loss'
    - TIMEOUT:   close_pct / 100 * notional  (for longs; negate close_pct for shorts)
    
    CRITICAL: atr_i and close_i MUST come from df['fwd_atr'] and df['close']
    per-bar. Do NOT use group-level averages. Each bar's PnL uses its own
    ATR and close price at the moment of hypothetical entry.
    
    Returns: ndarray of PnL in USD, shape (n_bars,) or (n_bars, n_combos)
    """
```

**CRITICAL: Do NOT loop over combos with Python for-loops.** Use numpy broadcasting:

```python
# Shape: (n_bars,) for mfe_atr, mae_atr
# Shape: (n_combos,) for target_atr, sl_atr, leverage, size_frac
# Broadcast to (n_bars, n_combos) using np.newaxis

# Build combo grid
from itertools import product
combos = list(product(config.leverage_grid, config.size_grid,
                       config.target_atr_grid, config.sl_atr_grid))
combos_arr = np.array(combos)  # shape (n_combos, 4)
lev = combos_arr[:, 0]   # (n_combos,)
sz = combos_arr[:, 1]
tgt = combos_arr[:, 2]
sl = combos_arr[:, 3]

# Broadcast: (n_bars, 1) vs (1, n_combos) -> (n_bars, n_combos)
mfe_2d = mfe_atr.values[:, np.newaxis]  # (n_bars, 1)
mae_2d = mae_atr.values[:, np.newaxis]
tgt_2d = tgt[np.newaxis, :]             # (1, n_combos)
sl_2d = sl[np.newaxis, :]

hit_tp = mfe_2d >= tgt_2d               # (n_bars, n_combos) bool
hit_sl = mae_2d >= sl_2d

# Outcome matrix
win = hit_tp & ~hit_sl
loss = hit_sl & ~hit_tp
ambiguous = hit_tp & hit_sl
timeout = ~hit_tp & ~hit_sl

# PnL matrix (n_bars, n_combos)
atr_2d = atr_i.values[:, np.newaxis]          # (n_bars, 1)
close_2d = close_i.values[:, np.newaxis]      # (n_bars, 1)
notional_2d = (sz * base_size * lev)[np.newaxis, :]  # (1, n_combos)

pnl = np.zeros_like(mfe_2d)                   # (n_bars, n_combos)
pnl[win]  = (tgt_2d * atr_2d / close_2d * notional_2d)[win]
pnl[loss] = -(sl_2d * atr_2d / close_2d * notional_2d)[loss]

# AMBIGUOUS + TIMEOUT: use close_pct (per-bar, broadcast across combos)
# For longs: pnl = close_pct / 100 * notional
# For shorts: pnl = -close_pct / 100 * notional
# CRITICAL: close_pct MUST be re-derived per window iteration.
# This line is INSIDE the `for window in config.windows:` loop.
# close_pct = df[f'fwd_{window}_close_pct'] — set at loop top, NOT reused across windows.
close_pct_2d = close_pct.values[:, np.newaxis]  # (n_bars, 1)
dir_sign = 1.0 if direction == 'long' else -1.0
pnl[ambiguous | timeout] = (dir_sign * close_pct_2d / 100 * notional_2d)[ambiguous | timeout]
```

**max_drawdown_usd vectorized computation:**
```python
# After computing pnl_2d (n_bars, n_combos), compute max drawdown per combo:
cumsum_2d = np.cumsum(pnl_2d, axis=0)                    # (n_bars, n_combos)
running_max_2d = np.maximum.accumulate(cumsum_2d, axis=0) # (n_bars, n_combos)
dd_2d = running_max_2d - cumsum_2d                        # (n_bars, n_combos)
max_dd_per_combo = np.max(dd_2d, axis=0)                  # (n_combos,)
# This is fully vectorized — no Python loops needed.
# The per-bar cumsum array is temporary and NOT stored in output.
```

**Memory consideration:** For 100K bars × 384 combos (4×4×6×4), the 2D arrays are ~38M float64 = ~305 MB. Manageable. For 399 coins combined (~50M bars), must process PER STATE to reduce working set.

**Grid search aggregation per state:**
```python
OUTPUT_LSG_COLS = [
    'bbwp_state',
    'window',
    'direction',
    'leverage',
    'size_frac',
    'target_atr',
    'sl_atr',
    'n_trades',           # bars in this state
    'win_rate',           # % wins
    'avg_win_usd',        # mean PnL of wins
    'avg_loss_usd',       # mean PnL of losses (negative)
    'expectancy_usd',     # mean PnL across all trades in this state
    'total_pnl_usd',     # sum of all PnL
    'profit_factor',      # sum(wins) / abs(sum(losses)); inf if no losses; 0.0 if no wins; NaN if both 0
    'max_consecutive_loss',  # longest losing streak (numpy diff on win/loss bool sequence)
    'sharpe_approx',      # mean(pnl) / std(pnl) — simplified; NaN if std==0
    'max_drawdown_usd',   # max peak-to-trough on cumsum(per-bar PnL) for this combo
                          # NOTE: requires computing cumsum inline during aggregation,
                          # but the per-bar array is NOT stored — only the scalar DD is kept.
    'calmar_approx',      # total_pnl / abs(max_drawdown); NaN if max_dd==0
]
```

**Top combos extraction:**
```python
def _extract_top_combos(lsg_results, config, n_top=3):
    """Per state × window × direction: top N by expectancy_usd, filtered by min_sample_size.
    
    NOTE: config is passed explicitly (not captured from closure) for testability.
    """
    filtered = lsg_results[lsg_results['n_trades'] >= config.min_sample_size]
    top = (filtered.groupby(['bbwp_state', 'window', 'direction'])
           .apply(lambda g: g.nlargest(n_top, 'expectancy_usd'))
           .reset_index(drop=True))
    return top
```

### Scaling Simulation: `_scaling_simulation(df, scenarios, config, lsg_top)`

Receives `lsg_top` (output of `_extract_top_combos`) so it can look up the best
LSG combo per entry_state for the base PnL comparison. This avoids a circular
dependency — the grid search runs first, then scaling uses its results.

For each scenario `(entry_state, entry_size, add_trigger_state, add_size, max_bars_to_wait)`:

1. Find all bars where `bbwp_state == entry_state`
2. Look up best LSG combo for entry_state from `lsg_top` (top-1 by expectancy, window=10, direction='long')
3. For each entry bar, look forward up to `max_bars_to_wait` bars
4. If `bbwp_state == add_trigger_state` within window: TRIGGERED
5. Compare PnL of:
   - Base: entry at `entry_size` only, using best LSG from lsg_top for entry_state
   - Scaled: entry at `entry_size`, add `add_size` at trigger bar, same LSG params
6. Edge = (mean_scaled_pnl - mean_base_pnl) / abs(mean_base_pnl) * 100
   Guard: if abs(mean_base_pnl) < 1e-10, edge_pct = NaN (avoid div-by-zero)
7. If entry_state not found in lsg_top (too few samples), skip that scenario with verdict='SKIP'

**NOTE:** This section CAN use a Python loop over entry bars because the forward look is stateful. But batch it: pre-filter entry bars, vectorize the forward state lookup where possible.

```python
OUTPUT_SCALING_COLS = [
    'entry_state',
    'add_trigger_state',
    'entry_size_frac',
    'add_size_frac',
    'max_bars_to_wait',
    'n_entry_bars',         # total entry opportunities
    'n_triggered',          # how many found the add_trigger within window
    'triggered_pct',        # n_triggered / n_entry_bars
    'mean_base_pnl',        # PnL without scaling
    'mean_scaled_pnl',      # PnL with scaling
    'edge_pct',             # (scaled - base) / base * 100
    'verdict',              # 'USE', 'MARGINAL', or 'SKIP'
]
```

Verdict logic:
```python
if triggered_pct >= config.scaling_use_threshold and edge_pct >= config.scaling_edge_threshold * 100:
    verdict = 'USE'
elif triggered_pct < 0.15:
    verdict = 'SKIP'
else:
    verdict = 'MARGINAL'
```

### SimulatorResult dataclass:

```python
@dataclass
class SimulatorResult:
    group_stats: dict       # {'A_state': DataFrame, 'B_spectrum': DataFrame, ...}
    lsg_results: pd.DataFrame  # full grid search results
    lsg_top: pd.DataFrame      # top 3 per state
    scaling_results: pd.DataFrame
    summary: dict              # {'n_bars_total', 'n_bars_valid', 'n_states', 'runtime_sec', ...}
```

### Main entry point:

```python
def run_simulator(df, config=None):
    """
    Run full BBW simulator on a DataFrame with L1+L2+L3 columns.
    
    Parameters
    ----------
    df : pd.DataFrame
        Must contain all L1, L2, L3 output columns plus OHLCV.
    config : SimulatorConfig, optional
        Override default grid/threshold parameters.
    
    Returns
    -------
    SimulatorResult
        Contains all analysis group stats, LSG grid results, scaling results.
    """
    if config is None:
        config = SimulatorConfig()
    
    _validate_input(df, config)
    
    # Drop rows where L3 forward columns are NaN (last N bars + ATR warmup)
    # CRITICAL: must check ALL configured windows, not just window=10.
    # Window=20 has NaN for last 20 bars; window=10 only last 10. If we only
    # check fwd_10, bars at positions n-20 through n-11 leak NaN into window=20 stats.
    valid_mask = df['fwd_atr'].notna()
    for w in config.windows:
        valid_mask = valid_mask & df[f'fwd_{w}_max_up_atr'].notna()
    df_valid = df[valid_mask].copy()
    
    # Create derived columns for Groups F and G
    _add_derived_columns(df_valid, config)
    
    # Run 7 analysis groups
    group_stats = {}
    for group_name, group_col in ANALYSIS_GROUPS.items():
        group_stats[group_name] = _compute_group_stats(df_valid, group_col,
                                                        config.windows, config.directions)
    
    # LSG grid search per state
    lsg_results = _lsg_grid_search(df_valid, config)
    lsg_top = _extract_top_combos(lsg_results, config, n_top=3)
    
    # Scaling simulation (requires lsg_top for base PnL comparison)
    scaling_results = _scaling_simulation(df_valid, config.scaling_scenarios, config, lsg_top)
    
    return SimulatorResult(
        group_stats=group_stats,
        lsg_results=lsg_results,
        lsg_top=lsg_top,
        scaling_results=scaling_results,
        summary={...}
    )
```

### Performance requirements:
- Single coin (RIVERUSDT 5m, ~200K bars): < 30 seconds
- Group stats: vectorized groupby, no bar loops
- LSG grid: numpy broadcasting, no Python loops over combos or bars
- Scaling: Python loop over entry bars is acceptable (typically <50K entries per state)

---

## SPEC: `tests\test_bbw_simulator.py`

15 tests, 80+ assertions. Use synthetic data that mimics L1+L2+L3 output.

### Helper:

```python
def make_simulator_df(n=500, seed=42):
    """
    Generate synthetic DataFrame with all L1+L2+L3 columns.
    Uses realistic distributions for each column.
    """
    np.random.seed(seed)
    
    # OHLCV
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n)) * 1.0
    low = close - np.abs(np.random.randn(n)) * 1.0
    
    # L1 columns
    states = np.random.choice(
        ['BLUE_DOUBLE', 'BLUE', 'MA_CROSS_UP', 'NORMAL', 'MA_CROSS_DOWN', 'RED', 'RED_DOUBLE'],
        size=n, p=[0.05, 0.15, 0.05, 0.40, 0.05, 0.20, 0.10])
    spectrums = np.random.choice(['blue', 'green', 'yellow', 'red'], size=n, p=[0.15, 0.30, 0.35, 0.20])
    
    # L2 columns
    directions = np.random.choice(['expanding', 'contracting', 'flat'], size=n, p=[0.30, 0.30, 0.40])
    patterns = np.random.choice(['BG', 'GY', 'YR', 'RY', 'YG', 'GB', 'BGY', 'GYR', 'RYG'], size=n)
    
    # L3 columns — forward returns
    atr = np.full(n, 2.0)  # constant ATR for predictable math
    fwd_up_atr = np.abs(np.random.randn(n)) * 2.0
    fwd_down_atr = np.abs(np.random.randn(n)) * 2.0
    fwd_close_pct = np.random.randn(n) * 1.5
    
    df = pd.DataFrame({
        'open': close, 'high': high, 'low': low, 'close': close,
        'base_vol': np.random.rand(n) * 10000,
        # L1
        'bbwp_value': np.random.rand(n) * 100,
        'bbwp_spectrum': spectrums,
        'bbwp_state': states,
        'bbwp_is_blue_bar': np.random.rand(n) < 0.10,
        'bbwp_is_red_bar': np.random.rand(n) < 0.10,
        'bbwp_ma_cross_up': np.random.rand(n) < 0.03,
        'bbwp_ma_cross_down': np.random.rand(n) < 0.03,
        # L2
        'bbw_seq_prev_color': np.roll(spectrums, 1),
        'bbw_seq_color_changed': np.random.rand(n) < 0.15,
        'bbw_seq_bars_in_color': np.random.randint(1, 50, n),
        'bbw_seq_bars_in_state': np.random.randint(1, 50, n),
        'bbw_seq_direction': directions,
        'bbw_seq_skip_detected': np.random.rand(n) < 0.05,
        'bbw_seq_pattern_id': patterns,
        'bbw_seq_from_blue_bars': np.random.randint(0, 200, n).astype(float),
        'bbw_seq_from_red_bars': np.random.randint(0, 200, n).astype(float),
        # L3
        'fwd_atr': atr,
        'fwd_10_max_up_pct': fwd_up_atr * atr / close * 100,
        'fwd_10_max_down_pct': -(fwd_down_atr * atr / close * 100),
        'fwd_10_max_up_atr': fwd_up_atr,
        'fwd_10_max_down_atr': fwd_down_atr,
        'fwd_10_close_pct': fwd_close_pct,
        'fwd_10_direction': np.where(fwd_close_pct > 0, 'up', 'down'),
        'fwd_10_max_range_atr': fwd_up_atr + fwd_down_atr,
        'fwd_10_proper_move': (fwd_up_atr + fwd_down_atr) >= 3.0,
        'fwd_20_max_up_pct': fwd_up_atr * 1.3 * atr / close * 100,
        'fwd_20_max_down_pct': -(fwd_down_atr * 1.3 * atr / close * 100),
        'fwd_20_max_up_atr': fwd_up_atr * 1.3,
        'fwd_20_max_down_atr': fwd_down_atr * 1.3,
        'fwd_20_close_pct': fwd_close_pct * 1.2,
        'fwd_20_direction': np.where(fwd_close_pct * 1.2 > 0, 'up', 'down'),
        'fwd_20_max_range_atr': (fwd_up_atr + fwd_down_atr) * 1.3,
        'fwd_20_proper_move': ((fwd_up_atr + fwd_down_atr) * 1.3) >= 3.0,
    })
    return df
```

### Tests:

1. **Input validation** — missing columns raises ValueError with list of missing
2. **MFE/MAE assignment long** — verify mfe=max_up, mae=max_down for direction='long'
3. **MFE/MAE assignment short** — verify mfe=max_down, mae=max_up for direction='short'
4. **Group A (state) stats** — 7 states present, correct columns, n_bars sum = total valid bars
5. **Group F (duration) stats** — bins created correctly, all bars accounted for
6. **Group G (MA+spectrum) stats** — combo strings formatted correctly
7. **All 7 groups run** — group_stats dict has 7 keys, each value is a DataFrame
8. **Min sample size filter** — groups with < min_sample_size bars excluded from lsg_top
9. **LSG grid dimensions** — total rows in lsg_results = len(lev) × len(sz) × len(tgt) × len(sl) × n_states × len(windows) × len(directions)
10. **LSG PnL signs** — wins have positive PnL, losses have negative PnL
11. **LSG win rate bounds** — 0 <= win_rate <= 1 for all combos
12. **LSG top extraction** — max 3 per state × window × direction
13. **Scaling triggered pct** — 0 <= triggered_pct <= 1
14. **Scaling verdict logic** — verify USE/MARGINAL/SKIP thresholds
15. **SimulatorResult structure** — all fields present, correct types

### Known value test (test 10):

Create a 10-bar df where:
- All bars: bbwp_state = 'BLUE', fwd_10_max_up_atr = 4.0, fwd_10_max_down_atr = 1.0
- For LSG combo (leverage=20, size=1.0, target=3, sl=2):
  - MFE=4.0 >= target=3: hit TP
  - MAE=1.0 < SL=2: never hit SL
  - Result: WIN for all 10 bars
  - Win rate = 1.0
- For LSG combo (leverage=20, size=1.0, target=5, sl=0.5):
  - MFE=4.0 < target=5: miss TP
  - MAE=1.0 >= SL=0.5: hit SL
  - Result: LOSS for all 10 bars
  - Win rate = 0.0

---

## SPEC: `scripts\debug_bbw_simulator.py`

### Section 1: MFE/MAE assignment validation
- 10-bar synthetic data, known fwd values
- Verify long MFE = max_up, short MFE = max_down (exact values)

### Section 2: PnL calculation validation
- 5-bar data, single LSG combo, hand-compute expected PnL per bar
- Verify: win/loss classification, PnL amount, aggregate stats

### Section 3: Grid search validation
- Small grid (2 leverages × 2 sizes × 2 targets × 2 SLs = 16 combos)
- 50-bar data with known MFE/MAE pattern
- Verify combo count matches, best combo is the one we expect

### Section 4: Group stats validation
- 20-bar data with 2 states (10 bars each), different MFE distributions
- Verify per-state means match hand calculation

### Section 5: Scaling simulation validation
- 30-bar data with known state sequence: NORMAL(10) → BLUE(5) → NORMAL(15)
- Scenario: enter at NORMAL, add at BLUE, max_wait=12
- Entries at bars 0-9 (NORMAL): bars 0-9 should find BLUE at bar 10 (within 12 bars) → TRIGGERED
- Entry at bar 25 (NORMAL): no BLUE within 12 bars → NOT TRIGGERED
- Verify triggered count, triggered_pct

### Section 6: Cross-validate on RIVERUSDT 5m
- Run L1 → L2 → L3 → L4 (with small grid for speed)
- IMPORTANT: L3 `windows` param must be ⊇ L4 `config.windows`. Use same windows list for both.
- Print: top combo per state, group A stats summary
- Verify BLUE states have different characteristics than RED states

### Target: 50+ checks

---

## SPEC: `scripts\sanity_check_bbw_simulator.py`

Load RIVERUSDT 5m → L1 → L2 → L3 → L4 (reduced grid for speed).

**Reduced config for sanity check:**
```python
sanity_config = SimulatorConfig(
    leverage_grid=[10, 20],
    size_grid=[0.5, 1.0],
    target_atr_grid=[2, 4],
    sl_atr_grid=[1.5, 2.0],
    windows=[10],           # single window
    directions=['long'],     # single direction
)
```
Total combos: 7 × 1 × 1 × 2 × 2 × 2 × 2 = 112 (fast)

**Print:**
- Per group: name, n_categories, top category by edge_score
- LSG: total combos tested, best combo per state
- Scaling: per scenario verdict
- Runtime breakdown: group_stats_sec, lsg_sec, scaling_sec, total_sec
- Memory: peak RSS

**Save:** `results\bbw_simulator_sanity.csv` (lsg_top only, small file)

---

## SPEC: `scripts\run_layer4_tests.py`

Same pattern as `scripts\run_layer3_tests.py`:

```python
SCRIPTS_TO_RUN = [
    ("Layer 4 Tests", ROOT / "tests" / "test_bbw_simulator.py"),
    ("Layer 4 Debug Validator", ROOT / "scripts" / "debug_bbw_simulator.py"),
    ("Layer 4 Sanity Check", ROOT / "scripts" / "sanity_check_bbw_simulator.py"),
]
```

Log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-bbw-layer4-results.md`

---

## DESIGN DECISIONS (intentional, do NOT change)

1. **TP/SL ambiguity resolution** — When both hit within the window, use close_pct as actual PnL (not TP/SL magnitude). This is conservative since we don't know hit order. Monte Carlo (Layer 4b) validates whether this matters.
2. **No per-bar PnL STORAGE** — Layer 4 computes per-bar PnL arrays inline during grid aggregation (needed for max_drawdown, max_consecutive_loss, Sharpe), but does NOT store them in the output. Only scalar aggregates are kept. Equity curve visualization belongs in Layer 4b (Monte Carlo).
3. **No transaction costs** — deferred. Can be added as `config.fee_pct` later. Current analysis finds raw edge first.
4. **States from L1 only** — the 7 bbwp_state values. Not spectrum colors. States are the decision variable for LSG mapping.
5. **Scaling uses best LSG from grid for base PnL** — not a fixed combo. This ensures scaling is compared against the optimal non-scaled baseline.
6. **max_consecutive_loss** — computed per combo using numpy diff on win/loss sequence. Important for risk sizing.

## IMPORTS NEEDED

```python
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from itertools import product
from scipy.stats import skew, kurtosis
from pathlib import Path
from typing import Optional
import time
```

No new dependencies. All already installed in the project venv.

## DO NOT

- Do not rewrite `signals\bbwp.py`, `signals\bbw_sequence.py`, or `research\bbw_forward_returns.py`
- Do not use Python for-loops over DataFrame rows for group stats or LSG grid
- Do not print full DataFrames or full grid results to terminal
- Do not run on all 399 coins (single coin only: RIVERUSDT)
- Do not exceed 32K output tokens — if approaching limit, stop and log progress
- Do not apply edits interactively — write complete files in one shot each
- Do not put Windows backslash paths in any string literal, docstring, or f-string
- ALL paths in code: use `Path(__file__).resolve().parent.parent` or `Path("forward/slash")`
- After writing EVERY .py file: `python -m py_compile <file>` MUST pass before running
