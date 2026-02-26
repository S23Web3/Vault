# BBW Layer 5 Build Prompt + Audit — 2026-02-14
**Session:** claude.ai desktop
**Outcome:** Layer 5 build prompt created, audited (15 issues found), all fixes applied

---

## WHAT WAS DONE

1. Read `06-CLAUDE-LOGS\2026-02-14-bbw-layer4-audit-and-sync.md` — full context on pipeline status, all layer column specs, build order
2. Read `02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md` — Layer 5 scope, output directory tree, L4b Monte Carlo interface, Layer 6 Ollama integration points
3. Read `BUILDS\PROMPT-LAYER4-BUILD.md` — full SimulatorResult dataclass spec, all output column definitions for group_stats (19 cols), lsg_results (18 cols), scaling_results (12 cols), config dataclass
4. Built `BUILDS\PROMPT-LAYER5-BUILD.md` — complete Claude Code build prompt for Layer 5

## LAYER 5 DESIGN SUMMARY

**File:** `research/bbw_report.py`
**Purpose:** Format Layer 4 (and optionally L4b) data structures into organized CSVs

### Input contract:
- `SimulatorResult` (REQUIRED) — from L4 `run_simulator()`
- `MonteCarloResult` (OPTIONAL) — from L4b, None if not built
- `coin_tier` (OPTIONAL) — string like 'tier_0', None if classifier not built

### Output structure:
```
reports/bbw/
├── aggregate/              ← 7 CSVs from L4 group_stats (A-G)
│   ├── bbw_state_stats.csv
│   ├── spectrum_color_stats.csv
│   ├── sequence_direction_stats.csv
│   ├── sequence_pattern_stats.csv
│   ├── skip_detection_stats.csv
│   ├── duration_cross_stats.csv
│   └── ma_cross_stats.csv
├── optimal/                ← LSG grid results
│   ├── optimal_lsg_by_state.csv   (top N per state with rank column)
│   └── lsg_grid_summary.csv       (compressed grid: 1 row per state×window×dir)
├── scaling/
│   └── scaling_sequences.csv       (sorted: USE → MARGINAL → SKIP)
├── monte_carlo/            ← only if mc_result provided
│   ├── mc_summary_by_state.csv
│   ├── mc_confidence_intervals.csv
│   ├── mc_equity_distribution.csv
│   └── mc_overfit_flags.csv
├── per_tier/               ← only if coin_tier provided
│   └── {tier}_optimal_lsg.csv
├── report_manifest.csv     ← machine-readable file list
└── simulation_metadata.csv ← sim_result.summary as key-value
```

### Key design decisions:
1. Optional dependencies — mc_result and coin_tier gracefully skipped when None
2. No data transformation — Layer 5 formats only, does NOT recompute statistics
3. Duck-typed validation — test mocks work without importing Layer 4
4. low_sample flag added (n_bars < 30) but NOT filtered — Layer 6 decides trust
5. sensitivity/ deferred to CLI runner (requires param sweep infrastructure)
6. MonteCarloResult interface defined for Layer 4b to implement

### Files to be created by Claude Code:
- `research\bbw_report.py` — main module
- `tests\test_bbw_report.py` — 20 tests, 60+ assertions
- `scripts\debug_bbw_report.py` — 40+ validation checks
- `scripts\sanity_check_bbw_report.py` — mock + real data modes
- `scripts\run_layer5_tests.py` — orchestrator

### Deviation from architecture doc:
- `optimal/` subdir instead of dumping lsg_top at root
- `sensitivity/` deferred (not L5's job — CLI param sweep)
- `per_tier/` conditional on coin_classifier being built
- Added `report_manifest.csv` and `simulation_metadata.csv` for Layer 6 discovery

## PIPELINE STATUS (updated)

| Layer | File | Status | Tests |
|-------|------|--------|-------|
| PRE-STEP | `research/coin_classifier.py` | NOT BUILT | — |
| Layer 1 | `signals/bbwp.py` | ✅ COMPLETE | 61/61 PASS |
| Layer 2 | `signals/bbw_sequence.py` | ✅ COMPLETE | 68/68 PASS |
| Layer 3 | `research/bbw_forward_returns.py` | ✅ COMPLETE | PASSING |
| Layer 4 | `research/bbw_simulator.py` | BUILD PROMPT READY | — |
| Layer 4b | `research/bbw_monte_carlo.py` | NOT BUILT | — |
| Layer 5 | `research/bbw_report.py` | BUILD PROMPT READY | — |
| Layer 6 | `research/bbw_ollama_review.py` | NOT BUILT | — |

## BUILD ORDER

```
NEXT:    Layer 4  → execute BUILDS\PROMPT-LAYER4-BUILD.md in Claude Code
THEN:    Layer 4b → needs build prompt (Monte Carlo)
THEN:    Layer 5  → execute BUILDS\PROMPT-LAYER5-BUILD.md in Claude Code
THEN:    Layer 6  → needs build prompt (Ollama)
```

## AUDIT RESULTS

15 issues found across 3 severity levels. All fixed in PROMPT-LAYER5-BUILD.md.
Full audit log: `06-CLAUDE-LOGS\2026-02-14-bbw-layer5-audit.md`

| ID | Severity | Summary | Status |
|----|----------|---------|--------|
| H1 | HIGH | Architecture diagram signatures missing `config` param | ✅ FIXED |
| H2 | HIGH | `_summarize_group` crashes on all-NaN expectancy_usd | ✅ FIXED |
| H3 | HIGH | Mock n_triggered can exceed n_entry_bars (independent randoms) | ✅ FIXED |
| M1 | MEDIUM | Dead `mc_status` variable in `_write_summary_report` | ✅ FIXED (now written to metadata) |
| M2 | MEDIUM | Report manifest doesn't list itself | ✅ FIXED (documented, metadata written first) |
| M3 | MEDIUM | Manifest subdir detection fragile (prefix-matching) | ✅ FIXED (explicit SUBDIR_MAP) |
| M4 | MEDIUM | `groupby.apply()` FutureWarning in pandas ≥2.1 | ✅ FIXED (include_groups=False) |
| M5 | MEDIUM | `ReportConfig.top_n_per_state` unused | ✅ FIXED (removed, documented) |
| M6 | MEDIUM | Test count mismatch: header says 12, list has 20 | ✅ FIXED |
| M7 | MEDIUM | `_validate_sim_result` doesn't check summary is dict | ✅ FIXED |
| L1 | LOW | Mock E_skip bools converted to strings | Documented |
| L2 | LOW | No `__all__` export list | ✅ FIXED |
| L3 | LOW | sim_result validation asymmetry not documented | ✅ FIXED (comment added) |
| L4 | LOW | ascending list construction brittle | ✅ FIXED (explicit list comp) |
| L5 | LOW | L5 doesn't re-validate all 18 L4 columns | Non-issue (documented) |

## NOTES

- Layer 5 can be executed as soon as Layer 4 passes all tests
- MC section will produce 0 files until Layer 4b is built — this is by design
- Per-tier section will produce 0 files until coin_classifier is built — also by design
- Layer 5 test suite is fully self-contained (mock objects, no L4 import required)
