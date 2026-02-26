# CLAUDE CODE PROMPT — Layer 5: Report Generator

## CONTEXT

Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
Layer 1 (`signals\bbwp.py`) — 61/61 PASS
Layer 2 (`signals\bbw_sequence.py`) — 68/68 PASS, 148/148 debug PASS
Layer 3 (`research\bbw_forward_returns.py`) — PASSING
Layer 4 (`research\bbw_simulator.py`) — MUST BE PASSING before executing this prompt

Layer 5 consumes SimulatorResult from Layer 4 and (optionally) Monte Carlo results from Layer 4b.
Layer 5 is the OUTPUT LAYER — it transforms raw data structures into organized, human/machine-readable CSVs in `reports/bbw/`.

## MANDATORY — READ FIRST

1. Read skill file: `skills\python\SKILL.md`
2. Read `research\bbw_simulator.py` (Layer 4 — SimulatorResult dataclass, group_stats columns, lsg_results columns, scaling_results columns)
3. Read `BUILDS\PROMPT-LAYER4-BUILD.md` (Layer 4 spec — exact column definitions for all output DataFrames)

## STRATEGY — TOKEN CONSERVATION

Layer 5 is moderate complexity. Single Claude Code session expected.

**Execution steps:**
1. Read skill + L4 source + L4 build prompt (3 reads)
1b. **PRE-CHECK:** Verify Layer 4 exists and imports clean:
    `python -c "from research.bbw_simulator import run_simulator, SimulatorResult, SimulatorConfig; print('L4 OK')"`
    If this fails, STOP. Layer 4 must be built and passing before Layer 5 can proceed.
2. Create `research\bbw_report.py` in one shot
3. `python -m py_compile research\bbw_report.py` — MUST pass
4. Create `tests\test_bbw_report.py` in one shot
5. `python -m py_compile tests\test_bbw_report.py` — MUST pass
6. Run: `python tests\test_bbw_report.py`
7. Create `scripts\debug_bbw_report.py` in one shot
8. `python -m py_compile scripts\debug_bbw_report.py` — MUST pass
9. Run: `python scripts\debug_bbw_report.py`
10. Create `scripts\sanity_check_bbw_report.py` in one shot
11. `python -m py_compile scripts\sanity_check_bbw_report.py` — MUST pass
12. Run: `python scripts\sanity_check_bbw_report.py`
13. Create `scripts\run_layer5_tests.py` in one shot
14. Run: `python scripts\run_layer5_tests.py`

Total: ~16-18 tool calls

## CRITICAL — STRING SAFETY

All docstrings use forward slashes for paths: `research/bbw_report.py`
All code paths use `pathlib.Path` with forward slashes or relative joins.
NEVER put Windows backslash paths in docstrings, strings, or f-strings.
After writing each .py file: `python -m py_compile <file>` — if SyntaxError, fix before proceeding.

---

## SPEC: `research\bbw_report.py`

### Architecture

```
bbw_report.py
├── generate_reports(sim_result, mc_result=None, coin_tier=None, config=None, output_dir=None) -> ReportSummary
│   ├── _ensure_output_dirs(output_dir, mc_result, coin_tier)
│   ├── _write_aggregate_reports(group_stats, output_dir, config)
│   ├── _write_lsg_reports(lsg_top, lsg_results, output_dir, config)
│   ├── _write_scaling_report(scaling_results, output_dir, config)
│   ├── _write_monte_carlo_reports(mc_result, output_dir, config)     # skipped if mc_result is None
│   ├── _write_per_tier_report(lsg_top, coin_tier, output_dir, config) # skipped if coin_tier is None
│   ├── _write_summary_report(sim_result, mc_result, files_written, output_dir, config)
│   └── returns ReportSummary (dataclass)
├── ReportSummary (dataclass)
├── MonteCarloResult (dataclass — interface definition for Layer 4b)
└── ReportConfig (dataclass)
```

### ReportConfig dataclass:

```python
@dataclass
class ReportConfig:
    output_dir: Path = field(default_factory=lambda: Path('reports/bbw'))
    float_precision: int = 4           # decimal places in CSVs
    include_empty_groups: bool = False  # skip groups with 0 rows
    min_sample_flag: int = 30          # flag rows below this sample size
```

**NOTE:** `top_n_per_state` was removed. Top-N filtering is Layer 4's responsibility
(`_extract_top_combos(n_top=3)`). Layer 5 writes whatever lsg_top contains.

### MonteCarloResult interface (Layer 4b will implement this):

```python
@dataclass
class MonteCarloResult:
    """Interface definition for Layer 4b Monte Carlo output.
    
    Layer 5 consumes this. Layer 4b produces it.
    If Layer 4b is not built/run, mc_result=None and MC reports are skipped.
    """
    summary_by_state: pd.DataFrame
    # Expected columns:
    #   bbwp_state, window, direction, leverage, size_frac, target_atr, sl_atr,
    #   real_pnl, mc_mean_pnl, mc_std_pnl, mc_p5_pnl, mc_p95_pnl,
    #   real_sharpe, mc_mean_sharpe, mc_p95_sharpe,
    #   real_max_dd, mc_mean_max_dd, mc_p95_max_dd,
    #   n_sims, n_trades, mc_pass (bool)
    
    confidence_intervals: pd.DataFrame
    # Expected columns:
    #   bbwp_state, window, direction, metric (pnl/sharpe/max_dd),
    #   ci_lower_95, ci_upper_95, ci_lower_99, ci_upper_99,
    #   real_value, percentile_rank
    
    equity_distribution: pd.DataFrame
    # Expected columns:
    #   bbwp_state, window, direction, sim_id,
    #   final_pnl, max_drawdown, sharpe, n_trades
    
    overfit_flags: pd.DataFrame
    # Expected columns:
    #   bbwp_state, window, direction,
    #   real_pnl, mc_p95_pnl, is_overfit (bool),
    #   real_sharpe, mc_p95_sharpe, sharpe_overfit (bool),
    #   n_trades, verdict (str: 'ROBUST'|'SUSPECT'|'OVERFIT'),
    #   reason (str)
```

### Input validation: `_validate_sim_result(sim_result)`

```python
def _validate_sim_result(sim_result):
    """Validate SimulatorResult has expected structure.
    
    Checks:
    - sim_result is a SimulatorResult instance (or duck-type check for testing)
    - group_stats is dict with string keys, DataFrame values
    - lsg_results is DataFrame with required columns
    - lsg_top is DataFrame with required columns
    - scaling_results is DataFrame with required columns
    - summary is dict
    
    Raises ValueError with specific missing field if invalid.
    """
    # Duck-type check (allows test mocks):
    required_attrs = ['group_stats', 'lsg_results', 'lsg_top', 'scaling_results', 'summary']
    missing = [a for a in required_attrs if not hasattr(sim_result, a)]
    if missing:
        raise ValueError(f"SimulatorResult missing attributes: {missing}")
    
    # group_stats validation
    if not isinstance(sim_result.group_stats, dict):
        raise ValueError("group_stats must be a dict")
    for key, df in sim_result.group_stats.items():
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"group_stats['{key}'] must be a DataFrame, got {type(df)}")
    
    # summary validation
    if not isinstance(sim_result.summary, dict):
        raise ValueError(f"summary must be a dict, got {type(sim_result.summary)}")
    
    # DataFrame validations
    LSG_REQUIRED = ['bbwp_state', 'window', 'direction', 'leverage', 'size_frac',
                    'target_atr', 'sl_atr', 'expectancy_usd', 'n_trades']
    LSG_TOP_REQUIRED = LSG_REQUIRED  # same columns
    SCALING_REQUIRED = ['entry_state', 'add_trigger_state', 'triggered_pct', 
                        'edge_pct', 'verdict']
    
    for name, df, req_cols in [
        ('lsg_results', sim_result.lsg_results, LSG_REQUIRED),
        ('lsg_top', sim_result.lsg_top, LSG_TOP_REQUIRED),
        ('scaling_results', sim_result.scaling_results, SCALING_REQUIRED),
    ]:
        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"{name} must be a DataFrame")
        missing_cols = [c for c in req_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"{name} missing columns: {missing_cols}")
```

### Validate MC result (only if provided):

```python
def _validate_mc_result(mc_result):
    """Validate MonteCarloResult if not None."""
    if mc_result is None:
        return
    required_attrs = ['summary_by_state', 'confidence_intervals', 
                      'equity_distribution', 'overfit_flags']
    missing = [a for a in required_attrs if not hasattr(mc_result, a)]
    if missing:
        raise ValueError(f"MonteCarloResult missing attributes: {missing}")
    for attr in required_attrs:
        val = getattr(mc_result, attr)
        if not isinstance(val, pd.DataFrame):
            raise ValueError(f"MonteCarloResult.{attr} must be a DataFrame")
```

---

### Directory structure creation: `_ensure_output_dirs(output_dir)`

```python
def _ensure_output_dirs(output_dir, mc_result=None, coin_tier=None):
    """Create report directory tree. Only create subdirs that will be populated.
    
    Always created:
        reports/bbw/aggregate/
        reports/bbw/scaling/
        reports/bbw/optimal/
    
    Conditional:
        reports/bbw/monte_carlo/    — only if mc_result is not None
        reports/bbw/per_tier/       — only if coin_tier is not None
    """
    base = Path(output_dir)
    always_dirs = ['aggregate', 'scaling', 'optimal']
    for d in always_dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    if mc_result is not None:
        (base / 'monte_carlo').mkdir(parents=True, exist_ok=True)
    if coin_tier is not None:
        (base / 'per_tier').mkdir(parents=True, exist_ok=True)
```

---

### Aggregate reports: `_write_aggregate_reports(group_stats, output_dir, config)`

Maps L4 analysis groups to CSV filenames:

```python
GROUP_TO_FILE = {
    'A_state':       'bbw_state_stats.csv',
    'B_spectrum':    'spectrum_color_stats.csv',
    'C_direction':   'sequence_direction_stats.csv',
    'D_pattern':     'sequence_pattern_stats.csv',
    'E_skip':        'skip_detection_stats.csv',
    'F_duration':    'duration_cross_stats.csv',
    'G_ma_spectrum': 'ma_cross_stats.csv',
}
```

For each group:
1. Get DataFrame from `group_stats[group_key]`
2. If DataFrame is empty and `config.include_empty_groups` is False → skip
3. Sort by `window`, `direction`, `edge_score` descending (NaN last)
4. Add `low_sample` bool column: True where `n_bars < config.min_sample_flag`
5. Round float columns to `config.float_precision` decimals
6. Write to `output_dir / 'aggregate' / filename`

```python
def _write_aggregate_reports(group_stats, output_dir, config):
    """Write 7 aggregate CSV files from L4 group_stats.
    
    Returns dict of {filename: n_rows} for summary.
    """
    written = {}
    agg_dir = Path(output_dir) / 'aggregate'
    
    for group_key, filename in GROUP_TO_FILE.items():
        if group_key not in group_stats:
            continue
        df = group_stats[group_key].copy()
        if df.empty and not config.include_empty_groups:
            continue
        
        # Flag low sample size
        if 'n_bars' in df.columns:
            df['low_sample'] = df['n_bars'] < config.min_sample_flag
        
        # Sort: window asc, direction asc, edge_score desc
        sort_cols = []
        if 'window' in df.columns:
            sort_cols.append('window')
        if 'direction' in df.columns:
            sort_cols.append('direction')
        if 'edge_score' in df.columns:
            sort_cols.append('edge_score')
        
        if sort_cols:
            ascending = [False if col == 'edge_score' else True for col in sort_cols]
            df = df.sort_values(sort_cols, ascending=ascending, na_position='last')
        
        # Round floats
        float_cols = df.select_dtypes(include=['float64', 'float32']).columns
        df[float_cols] = df[float_cols].round(config.float_precision)
        
        filepath = agg_dir / filename
        df.to_csv(filepath, index=False)
        written[filename] = len(df)
    
    return written
```

---

### LSG optimal reports: `_write_lsg_reports(lsg_top, lsg_results, output_dir, config)`

Two files:

1. **`optimal/optimal_lsg_by_state.csv`** — the lsg_top DataFrame (top N per state × window × direction)
   - Sort by: bbwp_state, window, direction, expectancy_usd desc
   - Add rank column (1-N within each state×window×direction group)
   - Add `low_sample` flag
   - Round floats

2. **`optimal/lsg_grid_summary.csv`** — aggregated view of the full grid search
   - NOT the full lsg_results (could be 10K+ rows)
   - Instead: per state × window × direction, report:
     - n_combos_tested
     - best_expectancy_usd
     - worst_expectancy_usd
     - median_expectancy_usd
     - best_combo (string: "lev=20_sz=1.0_tgt=4_sl=2.0")
     - best_win_rate
     - best_profit_factor
     - best_sharpe_approx
   - This is a compressed summary that fits on screen

```python
def _write_lsg_reports(lsg_top, lsg_results, output_dir, config):
    """Write optimal LSG CSV and grid summary.
    
    Returns dict of {filename: n_rows}.
    """
    written = {}
    opt_dir = Path(output_dir) / 'optimal'
    
    # 1. Optimal LSG by state
    df_top = lsg_top.copy()
    if not df_top.empty:
        # Add within-group rank
        df_top['rank'] = df_top.groupby(['bbwp_state', 'window', 'direction'])['expectancy_usd'].rank(ascending=False, method='dense').astype(int)
        df_top['low_sample'] = df_top['n_trades'] < config.min_sample_flag
        df_top = df_top.sort_values(['bbwp_state', 'window', 'direction', 'rank'])
        
        float_cols = df_top.select_dtypes(include=['float64', 'float32']).columns
        df_top[float_cols] = df_top[float_cols].round(config.float_precision)
        
        filepath = opt_dir / 'optimal_lsg_by_state.csv'
        df_top.to_csv(filepath, index=False)
        written['optimal_lsg_by_state.csv'] = len(df_top)
    
    # 2. Grid summary (compressed from full lsg_results)
    if not lsg_results.empty:
        def _summarize_group(g):
            # Guard: if all expectancy_usd are NaN, return NaN defaults
            valid_exp = g['expectancy_usd'].dropna()
            if valid_exp.empty:
                return pd.Series({
                    'n_combos_tested': len(g),
                    'best_expectancy_usd': np.nan,
                    'worst_expectancy_usd': np.nan,
                    'median_expectancy_usd': np.nan,
                    'best_combo': 'N/A',
                    'best_win_rate': np.nan,
                    'best_profit_factor': np.nan,
                    'best_sharpe_approx': np.nan,
                    'n_trades': 0,
                })
            best_idx = g['expectancy_usd'].idxmax()
            best_row = g.loc[best_idx]
            return pd.Series({
                'n_combos_tested': len(g),
                'best_expectancy_usd': g['expectancy_usd'].max(),
                'worst_expectancy_usd': g['expectancy_usd'].min(),
                'median_expectancy_usd': g['expectancy_usd'].median(),
                'best_combo': f"lev={best_row['leverage']}_sz={best_row['size_frac']}_tgt={best_row['target_atr']}_sl={best_row['sl_atr']}",
                'best_win_rate': best_row.get('win_rate', np.nan),
                'best_profit_factor': best_row.get('profit_factor', np.nan),
                'best_sharpe_approx': best_row.get('sharpe_approx', np.nan),
                'n_trades': best_row.get('n_trades', 0),
            })
        
        summary = (lsg_results
                   .groupby(['bbwp_state', 'window', 'direction'])
                   .apply(_summarize_group, include_groups=False)
                   .reset_index())
        
        summary['low_sample'] = summary['n_trades'] < config.min_sample_flag
        float_cols = summary.select_dtypes(include=['float64', 'float32']).columns
        summary[float_cols] = summary[float_cols].round(config.float_precision)
        
        filepath = opt_dir / 'lsg_grid_summary.csv'
        summary.to_csv(filepath, index=False)
        written['lsg_grid_summary.csv'] = len(summary)
    
    return written
```

---

### Scaling report: `_write_scaling_report(scaling_results, output_dir, config)`

Single file: `scaling/scaling_sequences.csv`

```python
def _write_scaling_report(scaling_results, output_dir, config):
    """Write scaling simulation results.
    
    Returns dict of {filename: n_rows}.
    """
    written = {}
    scale_dir = Path(output_dir) / 'scaling'
    
    if scaling_results.empty:
        return written
    
    df = scaling_results.copy()
    
    # Sort: verdict priority (USE first, then MARGINAL, then SKIP), then edge_pct desc
    verdict_order = {'USE': 0, 'MARGINAL': 1, 'SKIP': 2}
    df['_verdict_sort'] = df['verdict'].map(verdict_order).fillna(3)
    df = df.sort_values(['_verdict_sort', 'edge_pct'], ascending=[True, False], na_position='last')
    df = df.drop(columns=['_verdict_sort'])
    
    float_cols = df.select_dtypes(include=['float64', 'float32']).columns
    df[float_cols] = df[float_cols].round(config.float_precision)
    
    filepath = scale_dir / 'scaling_sequences.csv'
    df.to_csv(filepath, index=False)
    written['scaling_sequences.csv'] = len(df)
    
    return written
```

---

### Monte Carlo reports: `_write_monte_carlo_reports(mc_result, output_dir, config)`

Four files. Only called if mc_result is not None.

```python
MC_FILE_MAP = {
    'summary_by_state':       'mc_summary_by_state.csv',
    'confidence_intervals':   'mc_confidence_intervals.csv',
    'equity_distribution':    'mc_equity_distribution.csv',
    'overfit_flags':          'mc_overfit_flags.csv',
}

def _write_monte_carlo_reports(mc_result, output_dir, config):
    """Write Monte Carlo validation CSVs.
    
    Returns dict of {filename: n_rows}.
    Skips entirely if mc_result is None.
    """
    if mc_result is None:
        return {}
    
    written = {}
    mc_dir = Path(output_dir) / 'monte_carlo'
    
    for attr_name, filename in MC_FILE_MAP.items():
        df = getattr(mc_result, attr_name, None)
        if df is None or not isinstance(df, pd.DataFrame):
            continue
        if df.empty and not config.include_empty_groups:
            continue
        
        df = df.copy()
        float_cols = df.select_dtypes(include=['float64', 'float32']).columns
        df[float_cols] = df[float_cols].round(config.float_precision)
        
        filepath = mc_dir / filename
        df.to_csv(filepath, index=False)
        written[filename] = len(df)
    
    return written
```

---

### Per-tier report: `_write_per_tier_report(lsg_top, coin_tier, output_dir, config)`

Single file per tier. Only called if coin_tier is not None.

```python
def _write_per_tier_report(lsg_top, coin_tier, output_dir, config):
    """Write tier-specific optimal LSG report.
    
    coin_tier is a string like 'tier_0', 'tier_1', etc.
    This function is called once per tier by the CLI runner.
    
    Returns dict of {filename: n_rows}.
    """
    if coin_tier is None:
        return {}
    
    written = {}
    tier_dir = Path(output_dir) / 'per_tier'
    
    df = lsg_top.copy()
    if df.empty:
        return written
    
    # Add tier label
    df['coin_tier'] = coin_tier
    
    # Sort and round
    df = df.sort_values(['bbwp_state', 'window', 'direction', 'expectancy_usd'], ascending=[True, True, True, False])
    float_cols = df.select_dtypes(include=['float64', 'float32']).columns
    df[float_cols] = df[float_cols].round(config.float_precision)
    
    filename = f'{coin_tier}_optimal_lsg.csv'
    filepath = tier_dir / filename
    df.to_csv(filepath, index=False)
    written[filename] = len(df)
    
    return written
```

---

### Summary report: `_write_summary_report(sim_result, mc_result, output_dir, config)`

Single file: `reports/bbw/report_summary.csv` — a metadata file describing what was generated.

```python
def _write_summary_report(sim_result, mc_result, files_written, output_dir, config):
    """Write a manifest/summary of all generated report files.
    
    Columns: filename, subdir, n_rows, generated_at
    Also includes sim_result.summary metadata as a separate CSV.
    
    Returns dict of {filename: n_rows}.
    """
    written = {}
    base = Path(output_dir)
    
    # 1. Simulation metadata (write first so manifest can reference it)
    if hasattr(sim_result, 'summary') and isinstance(sim_result.summary, dict):
        mc_status = 'included' if mc_result is not None else 'not_available'
        meta_rows = [{'key': k, 'value': str(v)} for k, v in sim_result.summary.items()]
        meta_rows.append({'key': 'mc_status', 'value': mc_status})
        meta_df = pd.DataFrame(meta_rows)
        filepath = base / 'simulation_metadata.csv'
        meta_df.to_csv(filepath, index=False)
        written['simulation_metadata.csv'] = len(meta_df)
    
    # 2. File manifest — uses a SUBDIR_MAP for reliable classification
    # NOTE: manifest cannot list itself. Layer 6 should expect manifest + metadata
    # as 2 additional files beyond what the manifest lists.
    SUBDIR_MAP = {
        'bbw_state_stats.csv': 'aggregate',
        'spectrum_color_stats.csv': 'aggregate',
        'sequence_direction_stats.csv': 'aggregate',
        'sequence_pattern_stats.csv': 'aggregate',
        'skip_detection_stats.csv': 'aggregate',
        'duration_cross_stats.csv': 'aggregate',
        'ma_cross_stats.csv': 'aggregate',
        'optimal_lsg_by_state.csv': 'optimal',
        'lsg_grid_summary.csv': 'optimal',
        'scaling_sequences.csv': 'scaling',
        'mc_summary_by_state.csv': 'monte_carlo',
        'mc_confidence_intervals.csv': 'monte_carlo',
        'mc_equity_distribution.csv': 'monte_carlo',
        'mc_overfit_flags.csv': 'monte_carlo',
        'simulation_metadata.csv': 'root',
    }
    # per_tier files are dynamic: {coin_tier}_optimal_lsg.csv
    
    manifest_rows = []
    for filename, n_rows in files_written.items():
        subdir = SUBDIR_MAP.get(filename)
        if subdir is None:
            # Per-tier files end with _optimal_lsg.csv
            subdir = 'per_tier' if filename.endswith('_optimal_lsg.csv') else 'unknown'
        manifest_rows.append({
            'filename': filename,
            'subdir': subdir,
            'n_rows': n_rows,
            'generated_at': pd.Timestamp.now().isoformat(),
        })
    
    manifest_df = pd.DataFrame(manifest_rows)
    filepath = base / 'report_manifest.csv'
    manifest_df.to_csv(filepath, index=False)
    written['report_manifest.csv'] = len(manifest_df)
    
    return written
```

---

### ReportSummary dataclass:

```python
@dataclass
class ReportSummary:
    output_dir: str                 # base output directory
    files_written: dict             # {filename: n_rows}
    total_files: int                # count of files written
    total_rows: int                 # sum of all rows across files
    mc_included: bool               # whether MC results were included
    tier_included: bool             # whether per-tier results were included
    errors: list                    # list of error strings (non-fatal)
    runtime_sec: float              # wall clock time
```

---

### Main entry point:

```python
def generate_reports(sim_result, mc_result=None, coin_tier=None, 
                     config=None, output_dir=None):
    """
    Generate all BBW report CSVs from simulation results.
    
    Parameters
    ----------
    sim_result : SimulatorResult
        Required. Output from research.bbw_simulator.run_simulator().
    mc_result : MonteCarloResult, optional
        Output from research.bbw_monte_carlo. If None, MC reports skipped.
    coin_tier : str, optional
        Tier label like 'tier_0'. If None, per-tier report skipped.
    config : ReportConfig, optional
        Override report formatting options.
    output_dir : Path or str, optional
        Override output directory. Default: config.output_dir
    
    Returns
    -------
    ReportSummary
        Manifest of all files written, with row counts and timing.
    """
    import time
    start = time.time()
    
    if config is None:
        config = ReportConfig()
    if output_dir is not None:
        config.output_dir = Path(output_dir)
    
    errors = []
    
    # Validate inputs
    # Intentionally NOT in try/except — invalid sim_result is fatal, not recoverable.
    # MC validation IS caught below because mc_result is optional.
    _validate_sim_result(sim_result)
    if mc_result is not None:
        try:
            _validate_mc_result(mc_result)
        except ValueError as e:
            errors.append(f"MC validation failed, skipping MC reports: {e}")
            mc_result = None
    
    # Create directory structure
    _ensure_output_dirs(config.output_dir, mc_result, coin_tier)
    
    # Generate reports — collect all files_written
    all_files = {}
    
    # Aggregate (always)
    try:
        agg = _write_aggregate_reports(sim_result.group_stats, config.output_dir, config)
        all_files.update(agg)
    except Exception as e:
        errors.append(f"Aggregate reports failed: {e}")
    
    # LSG optimal (always)
    try:
        lsg = _write_lsg_reports(sim_result.lsg_top, sim_result.lsg_results, config.output_dir, config)
        all_files.update(lsg)
    except Exception as e:
        errors.append(f"LSG reports failed: {e}")
    
    # Scaling (always)
    try:
        scale = _write_scaling_report(sim_result.scaling_results, config.output_dir, config)
        all_files.update(scale)
    except Exception as e:
        errors.append(f"Scaling report failed: {e}")
    
    # Monte Carlo (conditional)
    try:
        mc = _write_monte_carlo_reports(mc_result, config.output_dir, config)
        all_files.update(mc)
    except Exception as e:
        errors.append(f"MC reports failed: {e}")
    
    # Per-tier (conditional)
    try:
        tier = _write_per_tier_report(sim_result.lsg_top, coin_tier, config.output_dir, config)
        all_files.update(tier)
    except Exception as e:
        errors.append(f"Per-tier report failed: {e}")
    
    # Summary/manifest (always, runs last)
    try:
        summary = _write_summary_report(sim_result, mc_result, all_files, config.output_dir, config)
        all_files.update(summary)
    except Exception as e:
        errors.append(f"Summary report failed: {e}")
    
    elapsed = time.time() - start
    
    return ReportSummary(
        output_dir=str(config.output_dir),
        files_written=all_files,
        total_files=len(all_files),
        total_rows=sum(all_files.values()),
        mc_included=mc_result is not None,
        tier_included=coin_tier is not None,
        errors=errors,
        runtime_sec=round(elapsed, 3),
    )
```

---

## SPEC: `tests\test_bbw_report.py`

20 tests, 80+ assertions. Use synthetic SimulatorResult (mock the dataclass).

### Test helper — mock SimulatorResult:

```python
def make_mock_sim_result(n_states=3, n_combos_per_state=5, n_scenarios=3, seed=42):
    """
    Create a minimal SimulatorResult with synthetic data.
    
    Does NOT require Layer 4 import — builds the dataclass manually
    so tests are independent of L4 implementation.
    """
    np.random.seed(seed)
    
    states = ['BLUE', 'NORMAL', 'RED'][:n_states]
    windows = [10, 20]
    directions = ['long', 'short']
    
    # group_stats: 7 groups, each a DataFrame with standard columns
    group_stats = {}
    group_cols = {
        'A_state': states,
        'B_spectrum': ['blue', 'green', 'yellow', 'red'],
        'C_direction': ['expanding', 'contracting', 'flat'],
        'D_pattern': ['BG', 'GY', 'YR'],
        'E_skip': [True, False],
        'F_duration': ['1-5', '6-10', '11-20'],
        'G_ma_spectrum': ['no_cross_blue', 'cross_up_green', 'no_cross_yellow'],
    }
    
    for group_key, values in group_cols.items():
        rows = []
        for val in values:
            for w in windows:
                for d in directions:
                    rows.append({
                        'group_value': val if not isinstance(val, bool) else str(val),
                        'window': w,
                        'direction': d,
                        'n_bars': np.random.randint(50, 5000),
                        'mean_mfe_atr': np.random.uniform(0.5, 4.0),
                        'median_mfe_atr': np.random.uniform(0.3, 3.5),
                        'p90_mfe_atr': np.random.uniform(2.0, 8.0),
                        'mean_mae_atr': np.random.uniform(0.3, 2.5),
                        'median_mae_atr': np.random.uniform(0.2, 2.0),
                        'p90_mae_atr': np.random.uniform(1.0, 5.0),
                        'mfe_mae_ratio': np.random.uniform(0.5, 3.0),
                        'mean_range_atr': np.random.uniform(1.0, 6.0),
                        'proper_move_pct': np.random.uniform(0.1, 0.8),
                        'directional_bias': np.random.uniform(0.3, 0.7),
                        'mean_close_pct': np.random.uniform(-1.0, 1.0),
                        'std_close_pct': np.random.uniform(0.5, 3.0),
                        'skew_close_pct': np.random.uniform(-1.0, 1.0),
                        'kurtosis_close_pct': np.random.uniform(2.0, 6.0),
                        'edge_score': np.random.uniform(-1.0, 2.0),
                    })
        group_stats[group_key] = pd.DataFrame(rows)
    
    # lsg_results: full grid
    lsg_rows = []
    for state in states:
        for w in windows:
            for d in directions:
                for i in range(n_combos_per_state):
                    lsg_rows.append({
                        'bbwp_state': state,
                        'window': w,
                        'direction': d,
                        'leverage': np.random.choice([5, 10, 15, 20]),
                        'size_frac': np.random.choice([0.25, 0.5, 0.75, 1.0]),
                        'target_atr': np.random.choice([1, 2, 3, 4, 5, 6]),
                        'sl_atr': np.random.choice([1.0, 1.5, 2.0, 3.0]),
                        'n_trades': np.random.randint(30, 5000),
                        'win_rate': np.random.uniform(0.3, 0.7),
                        'avg_win_usd': np.random.uniform(5, 50),
                        'avg_loss_usd': -np.random.uniform(5, 30),
                        'expectancy_usd': np.random.uniform(-10, 20),
                        'total_pnl_usd': np.random.uniform(-5000, 50000),
                        'profit_factor': np.random.uniform(0.5, 3.0),
                        'max_consecutive_loss': np.random.randint(1, 15),
                        'sharpe_approx': np.random.uniform(-0.5, 2.0),
                        'max_drawdown_usd': np.random.uniform(100, 5000),
                        'calmar_approx': np.random.uniform(0.1, 5.0),
                    })
    lsg_results = pd.DataFrame(lsg_rows)
    
    # lsg_top: top 3 per group (simulate _extract_top_combos output)
    lsg_top = (lsg_results
               .groupby(['bbwp_state', 'window', 'direction'])
               .apply(lambda g: g.nlargest(3, 'expectancy_usd'))
               .reset_index(drop=True))
    
    # scaling_results
    scale_rows = []
    for i in range(n_scenarios):
        triggered_pct = np.random.uniform(0.1, 0.6)
        edge_pct = np.random.uniform(-10, 40)
        if triggered_pct >= 0.30 and edge_pct >= 20:
            verdict = 'USE'
        elif triggered_pct < 0.15:
            verdict = 'SKIP'
        else:
            verdict = 'MARGINAL'
        n_entry = np.random.randint(100, 5000)
        scale_rows.append({
            'entry_state': np.random.choice(states),
            'add_trigger_state': np.random.choice(states),
            'entry_size_frac': 0.5,
            'add_size_frac': 0.5,
            'max_bars_to_wait': np.random.choice([10, 15, 20]),
            'n_entry_bars': n_entry,
            'n_triggered': int(n_entry * triggered_pct),
            'triggered_pct': triggered_pct,
            'mean_base_pnl': np.random.uniform(-5, 15),
            'mean_scaled_pnl': np.random.uniform(-5, 20),
            'edge_pct': edge_pct,
            'verdict': verdict,
        })
    scaling_results = pd.DataFrame(scale_rows)
    
    # summary dict
    summary = {
        'n_bars_total': 200000,
        'n_bars_valid': 199000,
        'n_states': n_states,
        'runtime_sec': 12.5,
        'coin': 'RIVERUSDT',
        'timeframe': '5m',
    }
    
    # Build a simple namespace object (avoids importing SimulatorResult)
    class MockSimResult:
        pass
    result = MockSimResult()
    result.group_stats = group_stats
    result.lsg_results = lsg_results
    result.lsg_top = lsg_top
    result.scaling_results = scaling_results
    result.summary = summary
    
    return result


def make_mock_mc_result(n_states=3, seed=42):
    """Create minimal MonteCarloResult mock."""
    np.random.seed(seed)
    states = ['BLUE', 'NORMAL', 'RED'][:n_states]
    
    # summary_by_state
    summary_rows = []
    for state in states:
        for w in [10, 20]:
            for d in ['long', 'short']:
                real_pnl = np.random.uniform(-1000, 5000)
                mc_mean = np.random.uniform(-500, 3000)
                mc_std = np.random.uniform(500, 2000)
                summary_rows.append({
                    'bbwp_state': state, 'window': w, 'direction': d,
                    'leverage': 20, 'size_frac': 1.0, 'target_atr': 4, 'sl_atr': 2.0,
                    'real_pnl': real_pnl, 'mc_mean_pnl': mc_mean, 'mc_std_pnl': mc_std,
                    'mc_p5_pnl': mc_mean - 1.65 * mc_std, 'mc_p95_pnl': mc_mean + 1.65 * mc_std,
                    'real_sharpe': np.random.uniform(-0.5, 2.0),
                    'mc_mean_sharpe': np.random.uniform(0, 1.0),
                    'mc_p95_sharpe': np.random.uniform(0.5, 1.5),
                    'real_max_dd': np.random.uniform(500, 3000),
                    'mc_mean_max_dd': np.random.uniform(500, 2500),
                    'mc_p95_max_dd': np.random.uniform(1000, 4000),
                    'n_sims': 1000, 'n_trades': np.random.randint(50, 5000),
                    'mc_pass': np.random.choice([True, False]),
                })
    
    # confidence_intervals
    ci_rows = []
    for state in states:
        for w in [10, 20]:
            for d in ['long', 'short']:
                for metric in ['pnl', 'sharpe', 'max_dd']:
                    real = np.random.uniform(-500, 5000)
                    ci_rows.append({
                        'bbwp_state': state, 'window': w, 'direction': d,
                        'metric': metric,
                        'ci_lower_95': real - np.random.uniform(500, 2000),
                        'ci_upper_95': real + np.random.uniform(500, 2000),
                        'ci_lower_99': real - np.random.uniform(1000, 3000),
                        'ci_upper_99': real + np.random.uniform(1000, 3000),
                        'real_value': real,
                        'percentile_rank': np.random.uniform(0, 1),
                    })
    
    # equity_distribution (keep small for tests)
    eq_rows = []
    for state in states[:1]:  # just 1 state for test size
        for sim_id in range(10):
            eq_rows.append({
                'bbwp_state': state, 'window': 10, 'direction': 'long',
                'sim_id': sim_id,
                'final_pnl': np.random.uniform(-2000, 10000),
                'max_drawdown': np.random.uniform(500, 3000),
                'sharpe': np.random.uniform(-0.5, 2.0),
                'n_trades': 500,
            })
    
    # overfit_flags
    of_rows = []
    for state in states:
        for w in [10, 20]:
            for d in ['long', 'short']:
                real_pnl = np.random.uniform(-1000, 5000)
                mc_p95 = np.random.uniform(0, 4000)
                is_overfit = real_pnl < mc_p95
                real_sharpe = np.random.uniform(-0.5, 2.0)
                mc_p95_sharpe = np.random.uniform(0.5, 1.5)
                sharpe_overfit = real_sharpe < mc_p95_sharpe
                if is_overfit and sharpe_overfit:
                    verdict = 'OVERFIT'
                elif is_overfit or sharpe_overfit:
                    verdict = 'SUSPECT'
                else:
                    verdict = 'ROBUST'
                of_rows.append({
                    'bbwp_state': state, 'window': w, 'direction': d,
                    'real_pnl': real_pnl, 'mc_p95_pnl': mc_p95, 'is_overfit': is_overfit,
                    'real_sharpe': real_sharpe, 'mc_p95_sharpe': mc_p95_sharpe,
                    'sharpe_overfit': sharpe_overfit,
                    'n_trades': np.random.randint(50, 5000),
                    'verdict': verdict,
                    'reason': f"{'PnL below MC p95' if is_overfit else ''}{' + ' if is_overfit and sharpe_overfit else ''}{'Sharpe below MC p95' if sharpe_overfit else ''}".strip(' + ') or 'Passed all checks',
                })
    
    class MockMCResult:
        pass
    mc = MockMCResult()
    mc.summary_by_state = pd.DataFrame(summary_rows)
    mc.confidence_intervals = pd.DataFrame(ci_rows)
    mc.equity_distribution = pd.DataFrame(eq_rows)
    mc.overfit_flags = pd.DataFrame(of_rows)
    
    return mc
```

### Tests:

1. **Input validation — valid SimulatorResult** — no error raised
2. **Input validation — missing attribute** — ValueError with specific field name
3. **Input validation — missing lsg_results columns** — ValueError listing columns
4. **MC validation — None accepted** — no error, MC reports skipped
5. **MC validation — invalid MC result** — error caught, MC skipped, error logged
6. **Aggregate reports — 7 files created** — check file existence and n_rows > 0
7. **Aggregate reports — low_sample flag** — rows with n_bars < 30 flagged True
8. **Aggregate reports — float precision** — max 4 decimal places in CSV values
9. **LSG reports — optimal file has rank column** — ranks 1-3 per group
10. **LSG reports — grid summary compression** — fewer rows than full lsg_results
11. **Scaling report — verdict sort order** — USE first, SKIP last
12. **MC reports — 4 files created when mc_result provided** — check existence
13. **MC reports — 0 files when mc_result is None** — no monte_carlo dir or files
14. **Per-tier report — tier label in output** — coin_tier column present
15. **Per-tier report — skipped when coin_tier is None** — no per_tier dir
16. **Summary manifest — lists all files** — manifest n_rows == total files written
17. **Full pipeline — generate_reports returns ReportSummary** — all fields populated
18. **Full pipeline — errors list empty on clean run** — no errors
19. **ReportSummary fields** — output_dir, total_files, total_rows, mc_included correct
20. **Output directory cleanup** — files written to correct subdirectories

All tests use `tmp_path` (pytest) or `tempfile.mkdtemp()` for output directories.

---

## SPEC: `scripts\debug_bbw_report.py`

### Section 1: Mock data generation validation
- Create mock SimulatorResult, verify all fields present
- Create mock MonteCarloResult, verify all fields present
- Print shapes and dtypes for each DataFrame

### Section 2: Aggregate report content validation
- Generate reports with mock data to temp dir
- Read back each aggregate CSV
- Verify: column names match expected, no empty files, low_sample flag present
- Print: first 3 rows of each CSV

### Section 3: LSG report content validation
- Verify optimal_lsg_by_state.csv has rank column with values 1-3
- Verify lsg_grid_summary.csv has fewer rows than full lsg_results
- Verify best_combo string format: "lev=X_sz=Y_tgt=Z_sl=W"
- Print: top combo per state from optimal file

### Section 4: Scaling report content validation
- Verify verdict sort order: USE before MARGINAL before SKIP
- Verify float precision in CSV
- Print: all rows

### Section 5: MC reports conditional generation
- Run with mc_result=None → verify no monte_carlo dir
- Run with mock mc_result → verify 4 files created
- Read back each MC CSV, verify columns match interface spec
- Print: overfit flags summary

### Section 6: Full pipeline with RIVERUSDT (if L4 is available)
- Try importing run_simulator
- If available: load RIVERUSDT 5m → L1 → L2 → L3 → L4 → L5
- Use reduced config (small grid) for speed
- Print: ReportSummary, list all files with sizes
- If L4 not available: print "L4 not ready, using mock data only"

### Target: 40+ checks

---

## SPEC: `scripts\sanity_check_bbw_report.py`

Two modes:

**Mode 1: Mock data (always runs)**
- Generate reports from mock SimulatorResult + mock MonteCarloResult
- Verify all expected files exist
- Verify total file count matches expected
- Print report summary

**Mode 2: Real data (only if L4 passes import check)**
- Load RIVERUSDT 5m → L1 → L2 → L3 → L4 (reduced config) → L5
- Generate reports to `reports/bbw/` (real output dir)
- Print: file list with sizes, ReportSummary
- Verify no errors in ReportSummary.errors

**Print:**
- Files generated (name, size, rows)
- Any errors encountered
- Runtime

---

## SPEC: `scripts\run_layer5_tests.py`

Same pattern as previous layers:

```python
SCRIPTS_TO_RUN = [
    ("Layer 5 Tests", ROOT / "tests" / "test_bbw_report.py"),
    ("Layer 5 Debug Validator", ROOT / "scripts" / "debug_bbw_report.py"),
    ("Layer 5 Sanity Check", ROOT / "scripts" / "sanity_check_bbw_report.py"),
]
```

Log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-bbw-layer5-results.md`

---

## DESIGN DECISIONS (intentional, do NOT change)

1. **Optional dependencies** — mc_result and coin_tier are optional. Layer 5 writes whatever it can with available inputs. Missing sections are skipped gracefully with logged errors.
2. **No data transformation** — Layer 5 does NOT recompute statistics. It formats and writes what Layer 4 already computed. The only "new" computation is the grid_summary compression and the manifest.
3. **Duck-typed validation** — Uses hasattr checks, not isinstance(SimulatorResult). This allows test mocks without importing Layer 4.
4. **Float precision** — All floats rounded to 4 decimal places in CSVs. Configurable via ReportConfig.
5. **low_sample flag** — Added to aggregate and optimal CSVs. Not filtered out — human/LLM reviewers (Layer 6) decide what to trust.
6. **Subdir naming** — Changed from architecture doc: `optimal/` instead of generic storage. `per_tier/` kept as-is. `sensitivity/` deferred (requires param sweep infrastructure not built yet).
7. **File manifest** — `report_manifest.csv` at root of output dir lists all generated files. Machine-readable for Layer 6 to discover what's available.
8. **No sensitivity reports yet** — `sensitivity/param_sensitivity.csv` requires running the simulator with different BBWP params (basis_len, lookback, etc). This is a CLI feature, not a Layer 5 responsibility. Deferred to CLI runner.

## IMPORTS NEEDED

```python
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import time

__all__ = ['generate_reports', 'ReportSummary', 'ReportConfig', 'MonteCarloResult']
```

No new dependencies.

## DO NOT

- Do not rewrite any previous layer files
- Do not recompute statistics that Layer 4 already computed
- Do not require Layer 4 import in tests (use mock objects)
- Do not write to `reports/bbw/ollama/` — that belongs to Layer 6
- Do not write to `reports/bbw/sensitivity/` — deferred to CLI
- Do not print full DataFrames to terminal
- Do not exceed 32K output tokens
- Do not apply edits interactively — write complete files in one shot each
- Do not put Windows backslash paths in any string literal, docstring, or f-string
- ALL paths in code: use `Path(__file__).resolve().parent.parent` or `Path("forward/slash")`
- After writing EVERY .py file: `python -m py_compile <file>` MUST pass before running
