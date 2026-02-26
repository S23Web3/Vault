# BBW Layer 5 Build Prompt — AUDIT REPORT
**Date:** 2026-02-14
**Auditor:** claude.ai desktop
**Target:** `BUILDS\PROMPT-LAYER5-BUILD.md`
**Result:** 15 issues found — 3 HIGH, 7 MEDIUM, 5 LOW

---

## HIGH SEVERITY (will cause runtime errors or wrong output)

### H1: Architecture diagram signatures don't match function specs
**Location:** Architecture section at top of L5 prompt
**Problem:** Every function in the architecture diagram is missing `config` parameter. Claude Code may use the architecture as the ground truth and omit `config` from actual implementations.

| Function | Architecture shows | Spec defines |
|----------|-------------------|-------------|
| `generate_reports` | `(sim_result, mc_result, coin_tier, output_dir)` | `(sim_result, mc_result, coin_tier, config, output_dir)` |
| `_ensure_output_dirs` | `(output_dir)` | `(output_dir, mc_result, coin_tier)` |
| `_write_aggregate_reports` | `(group_stats, output_dir)` | `(group_stats, output_dir, config)` |
| `_write_lsg_reports` | `(lsg_top, lsg_results, output_dir)` | `(lsg_top, lsg_results, output_dir, config)` |
| `_write_scaling_report` | `(scaling_results, output_dir)` | `(scaling_results, output_dir, config)` |
| `_write_monte_carlo_reports` | `(mc_result, output_dir)` | `(mc_result, output_dir, config)` |
| `_write_per_tier_report` | `(lsg_top, coin_tier, output_dir)` | `(lsg_top, coin_tier, output_dir, config)` |
| `_write_summary_report` | `(sim_result, mc_result, output_dir)` | `(sim_result, mc_result, files_written, output_dir, config)` |

**Fix:** Update architecture diagram to match all function signatures exactly.

### H2: `_summarize_group` crashes on all-NaN expectancy_usd
**Location:** `_write_lsg_reports` → `_summarize_group` inner function
**Problem:**
```python
best_idx = g['expectancy_usd'].idxmax()
```
If ALL values in a group's `expectancy_usd` column are NaN, `idxmax()` raises `ValueError: attempt to get argmax of an empty sequence`. This can happen when a state has too few bars for meaningful stats.

**Fix:** Add guard:
```python
if g['expectancy_usd'].isna().all():
    return pd.Series({...all NaN defaults...})
best_idx = g['expectancy_usd'].idxmax()
```

### H3: Mock `n_triggered` can exceed `n_entry_bars`
**Location:** `make_mock_sim_result` → scaling_results section
**Problem:**
```python
'n_entry_bars': np.random.randint(100, 5000),
'n_triggered': int(np.random.randint(100, 5000) * triggered_pct),
```
These are INDEPENDENT random calls. `n_triggered` could be 4500 × 0.6 = 2700 while `n_entry_bars` is 150. Invalid data that would not surface bugs in the `triggered_pct = n_triggered / n_entry_bars` calculation.

**Fix:**
```python
n_entry = np.random.randint(100, 5000)
...
'n_entry_bars': n_entry,
'n_triggered': int(n_entry * triggered_pct),
```

---

## MEDIUM SEVERITY (logic issues, misleading, or will cause FutureWarnings)

### M1: `_write_summary_report` has dead variable `mc_status`
**Location:** End of `_write_summary_report`
**Problem:**
```python
mc_status = 'included' if mc_result is not None else 'not_available'
```
Computed but never written to any file or returned. Dead code that suggests incomplete implementation.

**Fix:** Either remove it, or add it to `report_manifest.csv` as a metadata row, or include it in `simulation_metadata.csv`.

### M2: Report manifest doesn't list itself or simulation_metadata.csv
**Location:** `generate_reports` → summary step
**Problem:** `_write_summary_report` writes `report_manifest.csv` based on `files_written` dict collected BEFORE the summary step runs. So `report_manifest.csv` and `simulation_metadata.csv` are NOT listed in the manifest CSV on disk.

`ReportSummary.files_written` IS complete (via `all_files.update(summary)`), so Python callers get the full list. But Layer 6 reading from disk sees an incomplete manifest.

**Fix:** Write manifest last, accept self-reference paradox with a note:
```python
# Manifest cannot list itself. Layer 6 should add 2 to manifest row count.
# Listed files: all files EXCEPT report_manifest.csv and simulation_metadata.csv
```
Or restructure: collect all filenames first, then write manifest, then write metadata.

### M3: Manifest subdir detection is fragile (prefix-matching)
**Location:** `_write_summary_report` → subdir classification
**Problem:**
```python
if filename.startswith('mc_'):
    subdir = 'monte_carlo'
elif filename.startswith('tier_'):
    subdir = 'per_tier'
```
If `coin_tier='mc_something'`, the per-tier file `mc_something_optimal_lsg.csv` gets classified as `monte_carlo`. Unlikely but fragile.

**Fix:** Use a dict `{filename: subdir}` populated as files are written, instead of reverse-engineering subdir from filename. Change `_write_*` functions to return `{(subdir, filename): n_rows}` or pass subdir with each entry.

### M4: `groupby.apply()` FutureWarning in pandas ≥ 2.1
**Location:** `_write_lsg_reports` → grid summary
**Problem:**
```python
summary = (lsg_results
           .groupby(['bbwp_state', 'window', 'direction'])
           .apply(_summarize_group)
           .reset_index())
```
In pandas 2.1+, `.apply()` on GroupBy that returns Series emits `FutureWarning` about including group keys. May also produce unexpected column duplication.

**Fix:** Add `include_groups=False` parameter:
```python
.apply(_summarize_group, include_groups=False)
```
Or check pandas version and handle both cases.

### M5: `ReportConfig.top_n_per_state` is unused
**Location:** `ReportConfig` dataclass
**Problem:** `top_n_per_state: int = 3` is defined but never referenced in any L5 function. The actual top-N filtering happens in L4's `_extract_top_combos(n_top=3)`. Having it in ReportConfig implies L5 controls this, which is misleading.

**Fix:** Either remove it from ReportConfig (top-N is L4's responsibility), or use it in `_write_lsg_reports` to filter lsg_top to config.top_n_per_state per group.

### M6: Test count mismatch in header
**Location:** Test spec header
**Problem:** Header says "12 tests, 60+ assertions" but test list contains 20 numbered tests.

**Fix:** Update header to "20 tests, 80+ assertions".

### M7: `_validate_sim_result` doesn't check `summary` is dict
**Location:** `_validate_sim_result` function
**Problem:** The function checks all DataFrame attributes but doesn't validate `summary` is a dict. If `summary` is None or a DataFrame, `_write_summary_report` will crash at `sim_result.summary.items()`.

**Fix:** Add:
```python
if not isinstance(sim_result.summary, dict):
    raise ValueError(f"summary must be a dict, got {type(sim_result.summary)}")
```

---

## LOW SEVERITY (minor, cosmetic, or defensive)

### L1: Mock E_skip group values converted to strings unnecessarily
**Location:** `make_mock_sim_result` → group_stats E_skip
**Problem:**
```python
'group_value': val if not isinstance(val, bool) else str(val),
```
Converts `True`/`False` to `'True'`/`'False'` strings. Real L4 output stores bools. Tests won't catch bool-handling edge cases in CSV writing (e.g., pandas writes `True`/`False` for bool, `True`/`False` for string — same in CSV, but different in-memory types).

**Fix:** Keep bools as-is. Or note the conversion is intentional for CSV round-tripping.

### L2: No `__all__` export list defined
**Location:** Module-level spec
**Problem:** Consistent with previous layers, should define exports.

**Fix:** Add to spec:
```python
__all__ = ['generate_reports', 'ReportSummary', 'ReportConfig', 'MonteCarloResult']
```

### L3: `_validate_sim_result` raises on validation failure — inconsistent with MC
**Location:** `generate_reports` main flow
**Problem:** `_validate_sim_result` is called outside try/except (crashes entire function), while `_validate_mc_result` is caught (graceful skip). This asymmetry is intentional (sim_result is required) but not documented.

**Fix:** Add comment in the spec:
```python
# Intentionally NOT in try/except — invalid sim_result is fatal, not recoverable
_validate_sim_result(sim_result)
```

### L4: `ascending` list construction in `_write_aggregate_reports` is correct but brittle
**Location:** Sort logic
**Problem:**
```python
ascending = [True] * (len(sort_cols) - 1) + [False] if 'edge_score' in sort_cols else [True] * len(sort_cols)
```
Python ternary precedence makes this correct, but it's hard to read and assumes edge_score is always last in sort_cols.

**Fix:** Make explicit:
```python
ascending = []
for col in sort_cols:
    ascending.append(False if col == 'edge_score' else True)
```

### L5: Missing `bbwp_ma` from L5 validation LSG_REQUIRED (not a bug — just noted)
**Location:** LSG_REQUIRED columns list
**Observation:** L5 only validates the columns it actually uses for writing (bbwp_state, window, direction, leverage, size_frac, target_atr, sl_atr, expectancy_usd, n_trades). It doesn't validate ALL 18 L4 output columns. This is fine — L5 is a formatter, not a re-validator of L4 logic. Non-issue, just documenting the design choice.

---

## SUMMARY

| Severity | Count | Action |
|----------|-------|--------|
| HIGH | 3 | Must fix before Claude Code execution |
| MEDIUM | 7 | Should fix for robustness |
| LOW | 5 | Fix if convenient, document if not |
| **Total** | **15** | — |

## CROSS-REFERENCE VALIDATION (PASSED)

| Check | Result |
|-------|--------|
| L4 group_stats column `n_bars` → L5 uses `n_bars` | ✅ Match |
| L4 lsg_results column `n_trades` → L5 uses `n_trades` | ✅ Match |
| L4 lsg_results column `expectancy_usd` → L5 sorts/ranks by `expectancy_usd` | ✅ Match |
| L4 scaling `entry_state, add_trigger_state, triggered_pct, edge_pct, verdict` → L5 SCALING_REQUIRED | ✅ Match |
| L4 SimulatorResult has 5 attrs → L5 validates 5 attrs | ✅ Match |
| L4 ANALYSIS_GROUPS has 7 keys → L5 GROUP_TO_FILE has 7 entries | ✅ Match |
| L4 group keys A_state through G_ma_spectrum → L5 GROUP_TO_FILE keys match | ✅ Match |
| MonteCarloResult interface columns → mock MC data has matching columns | ✅ Match |
| Architecture doc directory tree → L5 output tree matches (with documented deviations) | ✅ Match |
