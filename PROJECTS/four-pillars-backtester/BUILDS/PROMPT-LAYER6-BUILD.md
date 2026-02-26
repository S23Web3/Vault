# CLAUDE CODE PROMPT — Layer 6: Ollama Analysis

## CONTEXT

Project root: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
Layer 1 (`signals\bbwp.py`) — 61/61 PASS
Layer 2 (`signals\bbw_sequence.py`) — 68/68 PASS, 148/148 debug PASS
Layer 3 (`research\bbw_forward_returns.py`) — PASSING
Layer 4 (`research\bbw_simulator.py`) — BUILD PROMPT READY
Layer 4b (`research\bbw_monte_carlo.py`) — NOT BUILT
Layer 5 (`research\bbw_report.py`) — BUILD PROMPT READY

Layer 6 reads CSV files produced by Layer 5 from `reports/bbw/`.
Layer 6 is the INTERPRETATION LAYER — it uses local Ollama LLMs to reason about numerical results in trading context. The math is done. Layer 6 adds meaning.

## MANDATORY — READ FIRST

1. Read skill file: `skills\python\SKILL.md`
2. Read `BUILDS\PROMPT-LAYER5-BUILD.md` (Layer 5 spec — output CSV structure, MonteCarloResult interface, report_manifest.csv format)
3. Read architecture doc Layer 6 section: `02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md`

## STRATEGY — TOKEN CONSERVATION

Layer 6 is moderate complexity. Single Claude Code session expected.

**Execution steps:**
1. Read skill + L5 build prompt + architecture doc (3 reads)
1b. **PRE-CHECK:** Verify Layer 5 exists and imports clean:
    `python -c "from research.bbw_report import generate_reports, ReportSummary; print('L5 OK')"`
    If this fails, STOP. Layer 5 must be built and passing before Layer 6 can proceed.
1c. **PRE-CHECK:** Verify Ollama is running:
    `python -c "import requests; r = requests.get('http://localhost:11434/api/tags'); print('Ollama OK:', len(r.json().get('models',[])), 'models')"`
    If this fails, STOP. Ollama must be running locally.
2. Create `research\bbw_ollama_review.py` in one shot
3. `python -m py_compile research\bbw_ollama_review.py` — MUST pass
4. Create `tests\test_bbw_ollama_review.py` in one shot
5. `python -m py_compile tests\test_bbw_ollama_review.py` — MUST pass
6. Run: `python tests\test_bbw_ollama_review.py`
7. Create `scripts\debug_bbw_ollama_review.py` in one shot
8. `python -m py_compile scripts\debug_bbw_ollama_review.py` — MUST pass
9. Run: `python scripts\debug_bbw_ollama_review.py`
10. Create `scripts\sanity_check_bbw_ollama_review.py` in one shot
11. `python -m py_compile scripts\sanity_check_bbw_ollama_review.py` — MUST pass
12. Run: `python scripts\sanity_check_bbw_ollama_review.py`
13. Create `scripts\run_layer6_tests.py` in one shot
14. Run: `python scripts\run_layer6_tests.py`

Total: ~16-18 tool calls

## CRITICAL — STRING SAFETY

All docstrings use forward slashes for paths: `research/bbw_ollama_review.py`
All code paths use `pathlib.Path` with forward slashes or relative joins.
NEVER put Windows backslash paths in docstrings, strings, or f-strings.
After writing each .py file: `python -m py_compile <file>` — if SyntaxError, fix before proceeding.

---

## SPEC: `research\bbw_ollama_review.py`

### Architecture

```
bbw_ollama_review.py
├── run_ollama_analysis(report_dir, config=None) -> OllamaResult
│   ├── _discover_reports(report_dir)
│   ├── _validate_ollama_connection(config)
│   ├── _ollama_call(prompt, config, model, temperature) -> str
│   ├── _analyze_state_stats(discovered, config) -> str
│   ├── _analyze_features(discovered, config) -> str
│   ├── _investigate_anomalies(discovered, config) -> str
│   ├── _generate_executive_summary(analyses, discovered, config) -> str
│   ├── _write_outputs(analyses, output_dir)
│   └── returns OllamaResult (dataclass)
├── review_layer_code(filepath, spec_text, config=None) -> str
├── OllamaResult (dataclass)
└── OllamaConfig (dataclass)
```

### OllamaConfig dataclass:

```python
@dataclass
class OllamaConfig:
    base_url: str = 'http://localhost:11434'
    
    # Model selection per task
    code_review_model: str = 'qwen2.5-coder:32b'
    fast_analysis_model: str = 'qwen3:8b'
    deep_analysis_model: str = 'qwen3-coder:30b'
    
    # Generation params
    code_review_temp: float = 0.3
    analysis_temp: float = 0.3
    deep_temp: float = 0.2
    summary_temp: float = 0.1
    
    # Timeouts and retries
    request_timeout: int = 120          # seconds per API call
    max_retries: int = 2                # retry on timeout/connection error
    retry_delay: float = 5.0            # seconds between retries
    
    # Input limits
    max_csv_chars: int = 50000          # truncate CSV input beyond this
    max_code_chars: int = 30000         # truncate code input beyond this
    
    # Output
    output_dir: Path = field(default_factory=lambda: Path('reports/bbw/ollama'))
    
    # Feature: skip individual analysis steps
    skip_state_analysis: bool = False
    skip_feature_analysis: bool = False
    skip_anomaly_investigation: bool = False
    skip_executive_summary: bool = False
```

### OllamaResult dataclass:

```python
@dataclass
class OllamaResult:
    state_analysis: Optional[str]          # markdown text or None if skipped/failed
    feature_recommendations: Optional[str]
    anomaly_flags: Optional[str]
    executive_summary: Optional[str]
    
    files_written: dict                    # {filename: filepath}
    models_used: dict                      # {task: model_name}
    errors: list                           # non-fatal error messages
    runtime_sec: float
    
    # Per-step timing
    timings: dict                          # {step_name: seconds}
```

---

### Ollama API wrapper: `_ollama_call(prompt, config, model, temperature)`

```python
def _ollama_call(prompt, config, model, temperature):
    """Send prompt to local Ollama and return response text.
    
    Handles:
    - Connection errors (Ollama not running)
    - Timeout (model too slow)
    - Retries with exponential backoff
    - Empty/malformed responses
    
    Returns response text string.
    Raises OllamaConnectionError if all retries fail.
    """
    import requests
    
    for attempt in range(config.max_retries + 1):
        try:
            response = requests.post(
                f'{config.base_url}/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'temperature': temperature,
                    'stream': False,
                },
                timeout=config.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            text = data.get('response', '')
            if not text.strip():
                raise ValueError("Empty response from Ollama")
            return text.strip()
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < config.max_retries:
                time.sleep(config.retry_delay * (attempt + 1))
                continue
            raise OllamaConnectionError(f"Ollama unreachable after {config.max_retries + 1} attempts: {e}")
        except requests.HTTPError as e:
            # Model not found, server error, etc.
            raise OllamaConnectionError(f"Ollama HTTP error: {e}")


class OllamaConnectionError(Exception):
    """Raised when Ollama API is unreachable or returns errors."""
    pass
```

---

### Report discovery: `_discover_reports(report_dir)`

```python
def _discover_reports(report_dir):
    """Read report_manifest.csv to discover available L5 outputs.
    
    Returns dict of {filename: full_path} for all existing CSV files.
    Falls back to directory scan if manifest is missing.
    
    NOTE: manifest doesn't list itself or simulation_metadata.csv.
    Add those manually if they exist on disk.
    """
    base = Path(report_dir)
    manifest_path = base / 'report_manifest.csv'
    
    discovered = {}
    
    if manifest_path.exists():
        manifest = pd.read_csv(manifest_path)
        for _, row in manifest.iterrows():
            # Handle root-level files (subdir == 'root')
            if row['subdir'] == 'root':
                filepath = base / row['filename']
            else:
                filepath = base / row['subdir'] / row['filename']
            if filepath.exists():
                discovered[row['filename']] = filepath
        # Add manifest and metadata (not in manifest itself)
        for extra in ['report_manifest.csv', 'simulation_metadata.csv']:
            p = base / extra
            if p.exists():
                discovered[extra] = p
    else:
        # Fallback: scan directory tree for CSVs
        for csv_path in base.rglob('*.csv'):
            discovered[csv_path.name] = csv_path
    
    return discovered
```

---

### Connection validation: `_validate_ollama_connection(config)`

```python
def _validate_ollama_connection(config):
    """Check Ollama is running and required models are available.
    
    Returns dict of {task: model_name} for available models.
    Raises OllamaConnectionError if Ollama is not reachable.
    Logs warning (does not raise) if a model is not pulled.
    """
    import requests
    
    try:
        response = requests.get(f'{config.base_url}/api/tags', timeout=10)
        response.raise_for_status()
    except (requests.ConnectionError, requests.Timeout) as e:
        raise OllamaConnectionError(f"Ollama not running at {config.base_url}: {e}")
    
    available = {m['name'] for m in response.json().get('models', [])}
    
    required = {
        'code_review': config.code_review_model,
        'fast_analysis': config.fast_analysis_model,
        'deep_analysis': config.deep_analysis_model,
    }
    
    warnings = []
    models_available = {}
    for task, model in required.items():
        # Check both exact match and base name (e.g., 'qwen3:8b' matches 'qwen3:8b')
        if model in available:
            models_available[task] = model
        else:
            warnings.append(f"Model '{model}' not found for {task}. Available: {sorted(available)}")
            # Try fallback: use fast_analysis_model for everything
            if config.fast_analysis_model in available:
                models_available[task] = config.fast_analysis_model
            else:
                warnings.append(f"No fallback model available for {task}")
    
    return models_available, warnings
```

---

### Analysis step 1: State analysis

```python
def _analyze_state_stats(discovered, config):
    """Interpret BBW state statistics in trading context.
    
    Reads: bbw_state_stats.csv (required), mc_summary_by_state.csv (optional)
    Model: fast_analysis_model (qwen3:8b)
    
    Returns markdown string.
    """
    state_file = discovered.get('bbw_state_stats.csv')
    if state_file is None:
        return None  # cannot run without state stats
    
    state_data = _read_csv_truncated(state_file, config.max_csv_chars)
    
    mc_data = ''
    mc_file = discovered.get('mc_summary_by_state.csv')
    if mc_file is not None:
        mc_data = _read_csv_truncated(mc_file, config.max_csv_chars)
    
    prompt = f"""You are analyzing BBW Simulator results for a crypto scalping system.
Context: 399 coins, 5m timeframe, $250 position × up to 20x leverage.
BBW = Bollinger Band Width Percentile. States: BLUE_DOUBLE, BLUE, MA_CROSS_UP, NORMAL, MA_CROSS_DOWN, RED, RED_DOUBLE.
BBW does NOT limit trades. BBW TUNES the LSG (Leverage, Size, Grid/Target distance).

STATE STATISTICS:
{state_data}

{'MONTE CARLO RESULTS:' + chr(10) + mc_data if mc_data else 'Monte Carlo results not available.'}

Provide:
1. Which BBW states have statistically significant edges? Look at edge_score, mfe_mae_ratio, directional_bias.
2. For states with data: are the optimal LSG parameters robust or potentially overfit?
3. Which states should be traded aggressively (high leverage, full size) vs cautiously (reduced)?
4. Any surprising findings or contradictions?
5. Specific recommendations for the BBW_LSG_MAP config — which direction per state, relative sizing.
6. Flag any rows where low_sample=True and explain impact on confidence.

Be direct. No disclaimers. This is for a professional trader.
Output as Obsidian markdown with ## headers."""

    return _ollama_call(prompt, config, config.fast_analysis_model, config.analysis_temp)
```

---

### Analysis step 2: Feature recommendations

```python
def _analyze_features(discovered, config):
    """Recommend feature pruning for VINCE ML model.
    
    Reads: All aggregate CSVs to build a feature importance picture.
    Model: fast_analysis_model (qwen3:8b)
    
    Returns markdown string.
    
    NOTE: True mutual information scoring is out of scope for the simulator pipeline.
    Layer 6 uses the group_stats edge_scores across different grouping variables
    as a proxy for feature importance. Groups with consistently high edge_scores
    suggest the grouping variable (= feature) is predictive.
    """
    # Collect edge_score summaries from all aggregate CSVs
    feature_data_parts = []
    aggregate_files = [
        ('bbwp_state (L1)', 'bbw_state_stats.csv'),
        ('spectrum_color (L1)', 'spectrum_color_stats.csv'),
        ('seq_direction (L2)', 'sequence_direction_stats.csv'),
        ('seq_pattern (L2)', 'sequence_pattern_stats.csv'),
        ('skip_detected (L2)', 'skip_detection_stats.csv'),
        ('duration_bin (L2)', 'duration_cross_stats.csv'),
        ('ma_spectrum_combo (L1+L2)', 'ma_cross_stats.csv'),
    ]
    
    for label, filename in aggregate_files:
        filepath = discovered.get(filename)
        if filepath is not None:
            try:
                df = pd.read_csv(filepath)
                # Summarize: mean edge_score, std edge_score, best group value
                if 'edge_score' in df.columns and not df['edge_score'].isna().all():
                    best_idx = df['edge_score'].idxmax()
                    feature_data_parts.append(
                        f"Feature: {label}\n"
                        f"  Mean edge_score: {df['edge_score'].mean():.4f}\n"
                        f"  Std edge_score: {df['edge_score'].std():.4f}\n"
                        f"  Best group: {df.loc[best_idx, 'group_value']} (edge={df.loc[best_idx, 'edge_score']:.4f})\n"
                        f"  N groups: {df['group_value'].nunique()}\n"
                    )
            except Exception:
                continue
    
    if not feature_data_parts:
        return None
    
    feature_data = '\n'.join(feature_data_parts)
    
    prompt = f"""These are edge_score summaries for BBW features used in a crypto scalping system.
Edge score = (mean_MFE - mean_MAE) / std(close_pct). Higher = more predictive of favorable moves.

{feature_data}

The target ML model (VINCE) uses XGBoost for trade direction prediction.
Current feature set: 17 BBW-derived features from Layers 1-2.

Recommend:
- KEEP: features with high/consistent edge scores (trading-relevant)
- DROP: features with near-zero or inconsistent edge scores (adds noise)
- COMBINE: correlated features that should be merged into one
- ENGINEER: new derived features suggested by the patterns

Consider which grouping variables show the most separation between their categories.
Output as Obsidian markdown with ## headers."""

    return _ollama_call(prompt, config, config.fast_analysis_model, config.analysis_temp)
```

---

### Analysis step 3: Anomaly investigation

```python
def _investigate_anomalies(discovered, config):
    """Investigate Monte Carlo overfit flags and cross-tier anomalies.
    
    Reads: mc_overfit_flags.csv (required), per_tier/*.csv (optional)
    Model: deep_analysis_model (qwen3-coder:30b)
    
    Returns markdown string. Returns None if no MC data available.
    """
    overfit_file = discovered.get('mc_overfit_flags.csv')
    if overfit_file is None:
        return None  # cannot investigate without MC flags
    
    flags_data = _read_csv_truncated(overfit_file, config.max_csv_chars)
    
    # Collect per-tier data if available
    tier_parts = []
    for filename, filepath in discovered.items():
        if filename.endswith('_optimal_lsg.csv') and 'tier_' in filename:
            try:
                tier_data = _read_csv_truncated(filepath, config.max_csv_chars // 4)
                tier_parts.append(f"--- {filename} ---\n{tier_data}")
            except Exception:
                continue
    
    tier_section = '\n'.join(tier_parts) if tier_parts else 'Per-tier data not available.'
    
    prompt = f"""Monte Carlo flagged these BBW states as potentially overfit:

OVERFIT FLAGS:
{flags_data}

PER-TIER BREAKDOWNS:
{tier_section}

Investigate:
1. Is the overfit driven by specific coin tiers (volatile vs calm)?
2. Are there outlier coins inflating the results?
3. Should the flagged LSG params be adjusted or discarded entirely?
4. What would a conservative alternative look like for each flagged state?
5. For ROBUST states: confirm the edge is likely real and tradeable.

Be specific about which states to trust and which to downgrade.
Output as Obsidian markdown with ## headers."""

    return _ollama_call(prompt, config, config.deep_analysis_model, config.deep_temp)
```

---

### Analysis step 4: Executive summary

```python
def _generate_executive_summary(analyses, discovered, config):
    """Synthesize all findings into actionable executive summary.
    
    Reads: All previous Ollama outputs + scaling_sequences.csv
    Model: deep_analysis_model (qwen3-coder:30b)
    
    Returns markdown string.
    """
    # Collect all previous analyses
    analysis_parts = []
    for name, text in analyses.items():
        if text is not None:
            analysis_parts.append(f"=== {name} ===\n{text[:config.max_csv_chars // 3]}")
    
    # Add scaling data
    scaling_file = discovered.get('scaling_sequences.csv')
    scaling_section = ''
    if scaling_file is not None:
        scaling_section = f"\nSCALING RESULTS:\n{_read_csv_truncated(scaling_file, config.max_csv_chars // 4)}"
    
    # Add grid summary
    grid_file = discovered.get('lsg_grid_summary.csv')
    grid_section = ''
    if grid_file is not None:
        grid_section = f"\nGRID SUMMARY:\n{_read_csv_truncated(grid_file, config.max_csv_chars // 4)}"
    
    all_text = '\n\n'.join(analysis_parts)
    
    prompt = f"""Synthesize all BBW Simulator findings into an executive summary.
Context: Crypto scalping, 399 coins, 5m timeframe, $250 base position, up to 20x leverage.

PREVIOUS ANALYSES:
{all_text}

{scaling_section}

{grid_section}

Structure your output EXACTLY as:

## HEADLINE
One sentence — is BBW useful as an LSG tuner?

## BEST STATES
Top 3 BBW states by risk-adjusted expectancy. For each: best direction, recommended leverage range, confidence level.

## LSG MAP
Final recommended BBW_LSG_MAP config as a Python dict:
```python
BBW_LSG_MAP = {{
    'STATE': {{'best_dir': 'long|short|neutral', 'leverage': N, 'size_frac': N, 'target_atr': N, 'sl_atr': N}},
    ...
}}
```
Values must come from actual simulation data, not placeholders.

## SCALING
Which scaling sequences to implement (USE verdict only). Operational viability assessment.

## WARNINGS
States/params that failed MC or have thin data. What to avoid.

## VINCE FEATURES
Final feature list after pruning: which of the 17 BBW features to keep for XGBoost.

## NEXT STEPS
Top 3 things to build/test next.

Output as Obsidian markdown. Be decisive, not hedging."""

    return _ollama_call(prompt, config, config.deep_analysis_model, config.summary_temp)
```

---

### Code review (standalone utility):

```python
def review_layer_code(filepath, spec_text, config=None):
    """Review a Python file against its specification using qwen2.5-coder:32b.
    
    This is a standalone utility called AFTER each layer is built,
    not part of the main run_ollama_analysis pipeline.
    
    Parameters
    ----------
    filepath : str or Path
        Path to the .py file to review.
    spec_text : str
        The specification text to check against.
    config : OllamaConfig, optional
    
    Returns
    -------
    str : Review output (bullet list of issues or "PASS")
    """
    if config is None:
        config = OllamaConfig()
    
    code = Path(filepath).read_text(encoding='utf-8')
    if len(code) > config.max_code_chars:
        code = code[:config.max_code_chars] + '\n# ... TRUNCATED ...'
    
    prompt = f"""Review this Python code against its specification.
Flag: logic errors, off-by-one bugs, missing edge cases, vectorization opportunities,
variable name mismatches, incorrect column references, missing NaN handling.

SPEC:
{spec_text[:config.max_csv_chars]}

CODE:
{code}

Output: numbered list of issues found with severity (HIGH/MEDIUM/LOW),
or "PASS — no issues found" if clean.
Do NOT suggest style improvements. Focus on correctness only."""

    return _ollama_call(prompt, config, config.code_review_model, config.code_review_temp)
```

---

### Helper: truncated CSV reader

```python
def _read_csv_truncated(filepath, max_chars):
    """Read CSV file as text, truncate if too large.
    
    Returns string content, truncated with a note if exceeds max_chars.
    """
    text = Path(filepath).read_text(encoding='utf-8')
    if len(text) > max_chars:
        text = text[:max_chars] + f'\n... TRUNCATED (original: {len(text)} chars) ...'
    return text
```

---

### Output writer: `_write_outputs(analyses, output_dir)`

```python
def _write_outputs(analyses, output_dir):
    """Write Ollama analysis results as markdown files.
    
    analyses: dict of {step_name: markdown_text}
    
    File mapping:
        state_analysis       → reports/bbw/ollama/state_analysis.md
        feature_recommendations → reports/bbw/ollama/feature_recommendations.md
        anomaly_flags        → reports/bbw/ollama/anomaly_flags.md
        executive_summary    → reports/bbw/ollama/executive_summary.md
    
    Skips None values (step was skipped or failed).
    Returns dict of {filename: filepath} for files actually written.
    """
    STEP_TO_FILE = {
        'state_analysis': 'state_analysis.md',
        'feature_recommendations': 'feature_recommendations.md',
        'anomaly_flags': 'anomaly_flags.md',
        'executive_summary': 'executive_summary.md',
    }
    
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    written = {}
    for step_name, filename in STEP_TO_FILE.items():
        text = analyses.get(step_name)
        if text is None:
            continue
        
        filepath = out_dir / filename
        # Add metadata header
        header = f"<!-- Generated by bbw_ollama_review.py at {pd.Timestamp.now().isoformat()} -->\n\n"
        filepath.write_text(header + text, encoding='utf-8')
        written[filename] = str(filepath)
    
    return written
```

---

### Main entry point:

```python
def run_ollama_analysis(report_dir, config=None):
    """
    Run full Ollama analysis on Layer 5 report CSVs.
    
    Parameters
    ----------
    report_dir : str or Path
        Path to reports/bbw/ directory containing L5 output CSVs.
    config : OllamaConfig, optional
        Override model selection, timeouts, skip flags.
    
    Returns
    -------
    OllamaResult
        Contains all analysis texts, files written, timing, errors.
    """
    import time
    start = time.time()
    
    if config is None:
        config = OllamaConfig()
    
    errors = []
    timings = {}
    
    # 1. Validate Ollama connection
    try:
        models_available, model_warnings = _validate_ollama_connection(config)
        errors.extend(model_warnings)
    except OllamaConnectionError as e:
        # Fatal — cannot proceed without Ollama
        return OllamaResult(
            state_analysis=None, feature_recommendations=None,
            anomaly_flags=None, executive_summary=None,
            files_written={}, models_used={},
            errors=[str(e)], runtime_sec=round(time.time() - start, 3),
            timings={},
        )
    
    # 2. Discover available reports
    discovered = _discover_reports(report_dir)
    if not discovered:
        return OllamaResult(
            state_analysis=None, feature_recommendations=None,
            anomaly_flags=None, executive_summary=None,
            files_written={}, models_used=models_available,
            errors=['No report CSVs found in ' + str(report_dir)],
            runtime_sec=round(time.time() - start, 3),
            timings={},
        )
    
    # 3. Run analysis steps
    analyses = {}
    
    # Step 1: State analysis
    if not config.skip_state_analysis:
        step_start = time.time()
        try:
            analyses['state_analysis'] = _analyze_state_stats(discovered, config)
        except Exception as e:
            errors.append(f"State analysis failed: {e}")
            analyses['state_analysis'] = None
        timings['state_analysis'] = round(time.time() - step_start, 3)
    
    # Step 2: Feature recommendations
    if not config.skip_feature_analysis:
        step_start = time.time()
        try:
            analyses['feature_recommendations'] = _analyze_features(discovered, config)
        except Exception as e:
            errors.append(f"Feature analysis failed: {e}")
            analyses['feature_recommendations'] = None
        timings['feature_recommendations'] = round(time.time() - step_start, 3)
    
    # Step 3: Anomaly investigation
    if not config.skip_anomaly_investigation:
        step_start = time.time()
        try:
            analyses['anomaly_flags'] = _investigate_anomalies(discovered, config)
        except Exception as e:
            errors.append(f"Anomaly investigation failed: {e}")
            analyses['anomaly_flags'] = None
        timings['anomaly_investigation'] = round(time.time() - step_start, 3)
    
    # Step 4: Executive summary (depends on all previous)
    if not config.skip_executive_summary:
        step_start = time.time()
        try:
            analyses['executive_summary'] = _generate_executive_summary(analyses, discovered, config)
        except Exception as e:
            errors.append(f"Executive summary failed: {e}")
            analyses['executive_summary'] = None
        timings['executive_summary'] = round(time.time() - step_start, 3)
    
    # 4. Write outputs
    files_written = _write_outputs(analyses, config.output_dir)
    
    elapsed = time.time() - start
    
    return OllamaResult(
        state_analysis=analyses.get('state_analysis'),
        feature_recommendations=analyses.get('feature_recommendations'),
        anomaly_flags=analyses.get('anomaly_flags'),
        executive_summary=analyses.get('executive_summary'),
        files_written=files_written,
        models_used=models_available,
        errors=errors,
        runtime_sec=round(elapsed, 3),
        timings=timings,
    )
```

---

## SPEC: `tests\test_bbw_ollama_review.py`

20 tests, 60+ assertions. Mock Ollama API responses — do NOT call real Ollama in tests.

### Test strategy: Mock the Ollama API

```python
from unittest.mock import patch, MagicMock

def mock_ollama_response(text="Mock analysis output"):
    """Create a mock requests.Response for Ollama API."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'response': text}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp
```

### Helper: create mock report directory

```python
def create_mock_report_dir(tmp_path):
    """Create a reports/bbw/ directory with sample CSVs for testing.
    
    Uses mock data from L5 test helpers (same make_mock_sim_result pattern).
    Creates aggregate/, optimal/, scaling/, monte_carlo/ subdirs with CSVs.
    Also creates report_manifest.csv.
    """
    base = tmp_path / 'reports' / 'bbw'
    
    # aggregate/
    agg_dir = base / 'aggregate'
    agg_dir.mkdir(parents=True)
    # Write minimal CSV files with correct columns
    state_df = pd.DataFrame({
        'group_value': ['BLUE', 'NORMAL', 'RED'],
        'window': [10, 10, 10],
        'direction': ['long', 'long', 'long'],
        'n_bars': [5000, 50000, 3000],
        'mean_mfe_atr': [2.5, 1.2, 0.8],
        'mean_mae_atr': [0.8, 1.1, 1.5],
        'edge_score': [1.8, 0.1, -0.5],
        'low_sample': [False, False, False],
    })
    state_df.to_csv(agg_dir / 'bbw_state_stats.csv', index=False)
    # ... repeat for other aggregate CSVs (minimal columns OK for tests)
    
    # optimal/
    opt_dir = base / 'optimal'
    opt_dir.mkdir(parents=True)
    # ... create optimal_lsg_by_state.csv, lsg_grid_summary.csv
    
    # scaling/
    scale_dir = base / 'scaling'
    scale_dir.mkdir(parents=True)
    # ... create scaling_sequences.csv
    
    # monte_carlo/ (optional)
    mc_dir = base / 'monte_carlo'
    mc_dir.mkdir(parents=True)
    # ... create mc_overfit_flags.csv etc.
    
    # report_manifest.csv
    manifest = pd.DataFrame({
        'filename': ['bbw_state_stats.csv'],
        'subdir': ['aggregate'],
        'n_rows': [3],
        'generated_at': [pd.Timestamp.now().isoformat()],
    })
    manifest.to_csv(base / 'report_manifest.csv', index=False)
    
    return base
```

### Tests:

1. **OllamaConfig defaults** — verify all default values
2. **Connection validation — Ollama running** — mock successful /api/tags response
3. **Connection validation — Ollama down** — mock ConnectionError → OllamaConnectionError raised
4. **Connection validation — model missing** — mock response without required model → warning logged, fallback used
5. **Report discovery — with manifest** — discovers files listed in manifest
6. **Report discovery — without manifest** — fallback to directory scan
7. **Report discovery — empty directory** — returns empty dict
8. **Ollama call — success** — mock response returned correctly
9. **Ollama call — timeout with retry** — first call times out, second succeeds
10. **Ollama call — all retries fail** — OllamaConnectionError after max_retries
11. **Ollama call — empty response** — raises ValueError
12. **State analysis — runs with CSV data** — mock Ollama, verify prompt contains CSV content
13. **State analysis — skipped when no state_stats CSV** — returns None
14. **Executive summary — includes previous analyses** — verify prompt contains prior step outputs
15. **Output writer — creates markdown files** — verify files exist with metadata header
16. **Output writer — skips None analyses** — no file written for None
17. **Full pipeline — mock all steps** — OllamaResult has all fields populated
18. **Full pipeline — Ollama down → graceful failure** — errors list populated, no crash
19. **Skip flags — skip_state_analysis=True** — state_analysis is None, timing not recorded
20. **Code review — returns review text** — mock Ollama, verify prompt includes code and spec

All tests mock Ollama API. No real LLM calls in test suite.

---

## SPEC: `scripts\debug_bbw_ollama_review.py`

### Section 1: Config validation
- Create OllamaConfig with defaults, verify all fields
- Create OllamaConfig with overrides, verify overrides applied
- Print config summary

### Section 2: Report discovery validation
- Create mock report directory in temp folder
- Run _discover_reports, verify all CSVs found
- Test fallback mode (no manifest)
- Print discovered files

### Section 3: Ollama connection check (REAL — requires Ollama running)
- Attempt real connection to localhost:11434
- If Ollama running: list available models, verify at least 1 model present
- If Ollama NOT running: print "Ollama offline — skipping live tests"

### Section 4: Prompt construction validation
- Create mock report dir with known CSV content
- Call _analyze_state_stats (mocked Ollama) → verify prompt contains expected CSV data
- Call _analyze_features (mocked Ollama) → verify prompt contains edge_score summaries
- Verify prompts stay under max_csv_chars limit
- Print prompt sizes

### Section 5: Output writing validation
- Write mock analyses to temp dir
- Verify 4 .md files created
- Verify metadata header present in each file
- Verify None analyses produce no file
- Print file sizes

### Section 6: End-to-end with mock Ollama
- Create full mock report dir
- Run run_ollama_analysis with mocked Ollama (patch requests.post)
- Verify OllamaResult fields
- Print: files written, timing, errors

### Section 7: End-to-end with REAL Ollama (only if running)
- If Ollama running AND L5 reports exist in `reports/bbw/`:
    - Run with fast_analysis_model only (skip deep analysis for speed)
    - Print: first 200 chars of each analysis
    - Print: timing per step
- If not available: print "Skipping live test"

### Target: 35+ checks

---

## SPEC: `scripts\sanity_check_bbw_ollama_review.py`

**Mode 1: Mock (always runs)**
- Create mock report dir → run_ollama_analysis with mocked Ollama
- Verify OllamaResult complete
- Verify all 4 .md files written
- Print summary

**Mode 2: Live (only if Ollama running + L5 reports exist)**
- Run on real `reports/bbw/` directory
- Use config with skip_anomaly_investigation=True (speed)
- Print: OllamaResult summary, file list, timing
- Verify no errors

---

## SPEC: `scripts\run_layer6_tests.py`

```python
SCRIPTS_TO_RUN = [
    ("Layer 6 Tests", ROOT / "tests" / "test_bbw_ollama_review.py"),
    ("Layer 6 Debug Validator", ROOT / "scripts" / "debug_bbw_ollama_review.py"),
    ("Layer 6 Sanity Check", ROOT / "scripts" / "sanity_check_bbw_ollama_review.py"),
]
```

Log: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-14-bbw-layer6-results.md`

---

## DESIGN DECISIONS (intentional, do NOT change)

1. **All Ollama calls are mocked in tests** — test suite must run without Ollama. Real LLM calls only in debug/sanity check scripts.
2. **Graceful degradation** — if Ollama is down, return OllamaResult with errors list. No crash. If specific models are missing, fall back to fast_analysis_model.
3. **No data transformation** — Layer 6 reads CSVs as text and passes them to LLM prompts. It does not parse or recompute any statistics. The LLM interprets the numbers.
4. **Feature analysis uses edge_score as MI proxy** — true mutual information scoring requires a separate computation pipeline (not built). Edge scores across grouping variables serve as a reasonable proxy.
5. **Executive summary depends on all prior steps** — it receives the text output of steps 1-3 as context. If a prior step failed, summary works with whatever is available.
6. **Code review is standalone** — `review_layer_code()` is not part of the main pipeline. It's called manually after each layer is built. Different model (coder) than analysis.
7. **Prompt engineering is hardcoded** — prompts are in the source code, not in external files. This keeps the module self-contained. If prompts need tuning, edit the source.
8. **Max input truncation** — CSVs and code are truncated to prevent context window overflow. Truncation adds a note so the LLM knows data is incomplete.
9. **Metadata headers in output** — every .md file gets a `<!-- Generated by ... -->` comment for traceability.
10. **Skip flags in config** — individual analysis steps can be skipped. Useful for fast iteration when only one step needs re-running.

## IMPORTS NEEDED

```python
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import time
import requests

__all__ = ['run_ollama_analysis', 'review_layer_code', 'OllamaResult', 'OllamaConfig', 'OllamaConnectionError']
```

No new dependencies (requests already installed).

## DO NOT

- Do not rewrite any previous layer files
- Do not call real Ollama in test suite (mock only)
- Do not parse LLM output as structured data — treat as raw markdown text
- Do not put Ollama prompts in external files — keep in source code
- Do not write to `reports/bbw/aggregate/` or any other L5 directory — only write to `reports/bbw/ollama/`
- Do not print full LLM responses to terminal in debug scripts (truncate to 200 chars)
- Do not exceed 32K output tokens
- Do not apply edits interactively — write complete files in one shot each
- Do not put Windows backslash paths in any string literal, docstring, or f-string
- ALL paths in code: use `Path(__file__).resolve().parent.parent` or `Path("forward/slash")`
- After writing EVERY .py file: `python -m py_compile <file>` MUST pass before running
