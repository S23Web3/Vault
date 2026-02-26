# BBW Layer 6 Build Prompt — AUDIT REPORT
**Date:** 2026-02-14
**Auditor:** claude.ai desktop
**Target:** `BUILDS\PROMPT-LAYER6-BUILD.md`
**Result:** 8 issues found — 1 HIGH, 4 MEDIUM, 3 LOW

---

## HIGH SEVERITY

### H1: Architecture diagram function signatures don't match spec
**Location:** Architecture section
**Problem:** Same pattern as L5 H1. Diagram shows:
- `_ollama_call(prompt, model, temperature)` but spec defines `_ollama_call(prompt, config, model, temperature)`
- `_analyze_state_stats(state_csv, mc_csv, config)` but spec defines `_analyze_state_stats(discovered, config)`
- `_analyze_features(mi_csv, config)` but spec defines `_analyze_features(discovered, config)`
- `_investigate_anomalies(overfit_csv, tier_dir, config)` but spec defines `_investigate_anomalies(discovered, config)`
- `_generate_executive_summary(all_analyses, config)` but spec defines `_generate_executive_summary(analyses, discovered, config)`

**Fix:** Update architecture diagram to match actual function signatures.

---

## MEDIUM SEVERITY

### M1: `_discover_reports` manifest lookup uses `subdir/filename` but `simulation_metadata.csv` is at root
**Location:** `_discover_reports` → manifest iteration
**Problem:**
```python
filepath = base / row['subdir'] / row['filename']
```
L5's SUBDIR_MAP maps `simulation_metadata.csv` → `'root'`. So this constructs `base / 'root' / 'simulation_metadata.csv'` which doesn't exist. The file is at `base / 'simulation_metadata.csv'`.

**Fix:** Handle `subdir == 'root'`:
```python
if row['subdir'] == 'root':
    filepath = base / row['filename']
else:
    filepath = base / row['subdir'] / row['filename']
```

### M2: `_validate_ollama_connection` doesn't return fallback for missing models
**Location:** Model availability check
**Problem:** If `config.fast_analysis_model` is also missing from available models, the fallback `models_available[task] = config.fast_analysis_model` still adds a non-existent model. Later `_ollama_call` will get HTTP 404.

**Fix:** Only assign fallback if the fallback model exists:
```python
if config.fast_analysis_model in available:
    models_available[task] = config.fast_analysis_model
else:
    # No usable model for this task
    warnings.append(f"No fallback available for {task}")
```

### M3: Test count mismatch
**Location:** Test spec header
**Problem:** Header says "15 tests, 50+ assertions" but test list has 20 tests.

**Fix:** Update to "20 tests, 60+ assertions".

### M4: `_ollama_call` catches `ValueError` (empty response) inside retry loop but doesn't retry
**Location:** `_ollama_call` function
**Problem:** `ValueError("Empty response from Ollama")` is raised but not caught by the `except (requests.ConnectionError, requests.Timeout)` handler. It propagates immediately without retrying. Empty responses could be transient (model loading).

**Fix:** Either add ValueError to the retry exceptions, or document this is intentional (empty response = model issue, not network issue).

---

## LOW SEVERITY

### L1: `_analyze_features` reads CSV as DataFrame just to extract edge_score stats — could use `_read_csv_truncated` for consistency
**Observation:** Other analysis functions pass raw CSV text to the LLM. `_analyze_features` uniquely parses CSVs as DataFrames to compute summary stats before prompting. This is fine (it's pre-processing, not transformation), but breaks the "no data transformation" design decision slightly. Intentional trade-off — documented.

### L2: `review_layer_code` uses `config.max_csv_chars` for spec truncation (naming inconsistency)
**Location:** `spec_text[:config.max_csv_chars]`
**Problem:** Uses `max_csv_chars` to truncate spec text, but spec text isn't CSV. Minor naming confusion.

**Fix:** Could add `max_spec_chars` to OllamaConfig, or just document the reuse.

### L3: No `__all__` note in test file spec
**Observation:** Minor. Tests don't need `__all__` but noting for consistency with L5 audit.

---

## CROSS-REFERENCE VALIDATION (PASSED)

| Check | Result |
|-------|--------|
| L5 `report_manifest.csv` format → L6 `_discover_reports` reads it | ✅ Match (with M1 fix) |
| L5 `bbw_state_stats.csv` filename → L6 references same name | ✅ Match |
| L5 `mc_overfit_flags.csv` filename → L6 references same name | ✅ Match |
| L5 `mc_summary_by_state.csv` filename → L6 references same name | ✅ Match |
| L5 `scaling_sequences.csv` filename → L6 references same name | ✅ Match |
| L5 `lsg_grid_summary.csv` filename → L6 references same name | ✅ Match |
| L5 `simulation_metadata.csv` at root → L6 discovery handles root (with M1 fix) | ✅ Match |
| L5 per_tier `{tier}_optimal_lsg.csv` pattern → L6 `endswith('_optimal_lsg.csv')` | ✅ Match |
| L5 output dir `reports/bbw/` → L6 reads from same | ✅ Match |
| L6 output dir `reports/bbw/ollama/` → no conflict with L5 dirs | ✅ Match |
