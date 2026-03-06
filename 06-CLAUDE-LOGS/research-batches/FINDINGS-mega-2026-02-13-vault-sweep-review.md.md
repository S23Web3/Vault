# FINDINGS: 2026-02-13-vault-sweep-review.md

**Batch**: 4 of 22 (mega-file)
**Source**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-13-vault-sweep-review.md`
**File length**: 14,579 lines
**Read method**: 500-line chunks (token limit constraint)
**Completed**: 2026-03-05

---

## META

- **Review type**: Automated LLM code review
- **Model**: qwen2.5-coder:14b via Ollama
- **Date run**: 2026-02-13
- **Files reviewed**: 234
- **Issues found**: 168
- **Errors**: 0
- **Duration**: 16,972 seconds (282.9 minutes)
- **Scope**: All code files across the vault — Pine Script indicators, Python backtester engine, ML pipeline, data fetchers, optimizers, GUI/dashboard components, trading-tools library

---

## SUMMARY

Comprehensive automated review of 234 code files. The review model flagged 168 issues across the codebase. Most flagged issues (🔴) are minor robustness concerns (missing try/except, no retry logic) rather than logic-breaking bugs. A small number of genuine critical bugs were identified. Six large files (>50,000 chars) were skipped by the review model.

---

## CRITICAL BUGS (actionable, could cause wrong trades or system failure)

### 1. `data/db.py` line 38 — Hardcoded default password
- Default password hardcoded as `"admin"` in database connection
- **Risk**: Security — credentials exposed in source

### 2. `engine/backtester.py` line 130 — Double commission charge
- Commission may be charged twice on position close
- **Risk**: All backtest P&L results are understated by ~2x commission

### 3. `engine/exit_manager.py` line 114 — Wrong sign in BE stop loss
- `_be_sl` method: LONG SL set to `entry + offset` instead of `entry - offset`
- **Risk**: BE stop for LONG positions placed above entry price — trade closes immediately on raise

### 4. `engine/backtester_v382.py` — Re-entry state not reset after STOP_OUT
- After a STOP_OUT, re-entry flag is not cleared
- **Risk**: Re-entry signals fire incorrectly on subsequent bars

### 5. `staging/ml/live_pipeline.py` line 214 — ML confidence hardcoded to 0.5
- `confidence = 0.5` hardcoded — always bypasses the ML filter threshold check
- **Risk**: The live ML pipeline never actually filters signals; all signals pass regardless of model output

### 6. `signals/clouds.py` (backtester) — Off-by-one in EMA loop
- Loop start index off by one — first EMA values seeded incorrectly
- **Risk**: All cloud signal calculations have a one-bar shift error

### 7. `signals/four_pillars_v383.py` — ATR initialization off-by-one
- `atr[atr_len - 1]` seeded with mean of `tr[:atr_len]` instead of correct Wilder initialization
- **Risk**: ATR values wrong for first `atr_len` bars; SL distances incorrect at start of dataset

### 8. `strategies/signals.py` line 53 — Cooldown boundary error
- `if i - last_signal_bar < cooldown_bars:` should be `<=`
- **Risk**: Cooldown is one bar shorter than configured — more trades fire than intended

### 9. `trading-tools/exits/phased.py` line 27 — reset() doesn't reset current_sl
- `reset()` resets `phase` but not `current_sl`
- **Risk**: Reused PhasedExit objects carry stale SL from previous trade into new trade

### 10. `trading-tools/optimizer/grid_search.py` line 87 — Double compute_signals call
- `compute_signals()` called once before loop and again inside loop on same DataFrame
- **Risk**: Signal columns computed twice; second call may overwrite with different params

### 11. `trading-tools/scripts/fetch_data.py` line 60 — Wrong month calculation
- `timedelta(days=args.months * 30)` — 30 days per month assumption
- **Risk**: Fetched date range is wrong (up to 5 days short for 6-month fetch)

### 12. State machine stage_lookback boundary (multiple files)
- Files affected: `signals/state_machine_v382.py`, `signals/state_machine_v383.py`, `trading-tools/signals/state_machine.py`, `trading-tools/vince/strategies/signals.py`
- Bug: `bar_index - self.long_stage1_bar > self.stage_lookback` should be `>=`
- **Risk**: Stage stays active one bar too long after lookback expiry — extra signals fire

---

## LARGE FILES SKIPPED BY REVIEW MODEL

The following files exceeded the 50,000 character limit and were not reviewed:

| File | Size |
|------|------|
| `build_missing_files.py` | 1,571 lines |
| `build_ml_pipeline.py` | 1,501 lines |
| `build_staging.py` | 1,692 lines |
| `staging/dashboard.py` (not the same as trading-tools) | 1,498 lines |
| `dashboard_v2.py` | 1,533 lines |
| `master_build.py` | 1,455 lines |

These are build scripts and the main Streamlit dashboard. They were summarized at high level but not reviewed line-by-line.

---

## CLEAN FILES (🟢 — no critical issues found)

The following files passed review with no critical bugs:

**Pine Script:**
- `backup_2026-02-04_ripster_ema_clouds_v6.pine`
- `four_pillars_v3_8.pine`
- `Quad-Rotation-Stochastic-FAST-v1.3.pine`
- `Quad-Rotation-Stochastic-v4.pine`
- `ripster_ema_clouds_v6.pine` (02-STRATEGY)

**Python — engine/ML:**
- `commission.py`
- `metrics.py`
- `position_v382.py`
- `purged_cv.py`
- `shap_analyzer.py`
- `xgboost_trainer.py`
- `ml/__init__.py`
- `bayesian.py` (optimizer)
- `walk_forward.py` (optimizer)
- `signals/state_machine.py` (backtester)
- `signals/stochastics.py` (backtester)
- `strategies/base_strategy.py`
- `strategies/__init__.py`
- `strategies/indicators.py`

**Python — scripts:**
- `batch_sweep_v382.py`
- `check_cache_status.py`
- `compare_v382.py`
- `download_1year_gap.py`
- `fix_ml_features.py`
- `resample_timeframes.py`
- `sanity_check_cache.py`
- `sweep_all_coins.py`
- `sweep_sl_mult_v383.py`
- `sweep_v38.py`
- `test_download_FIXED.py`
- `test_download_periods.py`
- `test_download_simulation.py`
- `test_features_v2.py`
- `test_ml_pipeline.py`
- `test_period_loader.py`
- `test_sweep.py`
- `test_v382.py`
- `test_v383.py`
- `staging/run_backtest.py`
- `phase_diagram.py`

**trading-tools:**
- `trading-tools/data/fetcher.py`
- `trading-tools/engine/position.py`
- `trading-tools/engine/commission.py`
- `trading-tools/resample_timeframes.py`
- `trading-tools/run_ollama_sweep.py`
- `trading-tools/scripts/run_backtest.py`
- `trading-tools/signals/state_machine.py`
- `trading-tools/vince/__init__.py`
- `trading-tools/vince/base_strategy.py`
- `trading-tools/vince/engine/__init__.py`
- `trading-tools/vince/utils/__init__.py`
- `trading-tools/vince/utils/gpu_monitor.py`
- `trading-tools/vince/utils/ollama_helper.py`
- `trading-tools/tic_tac_toe_test_backup.py`
- `vault_sweep_4.py`

---

## RECURRING PATTERN ISSUES (not individually critical but systemic)

These appear in dozens of files and represent systemic weaknesses:

1. **Missing try/except around backtester.run()** — If run fails, script crashes silently
2. **No retry on API calls** — Bybit/exchange fetch calls have no retry logic in most scripts
3. **Missing CACHE_DIR.exists() check** — Many scripts glob cache without checking dir exists
4. **Bare except clauses** — `except Exception: pass` swallows errors
5. **`sys.path.insert` without validation** — Used in many scripts without checking path
6. **Print vs logging** — Widespread use of `print()` instead of `logging` with timestamps

---

## SECURITY ISSUES

| File | Issue |
|------|-------|
| `data/db.py` | Default password `"admin"` hardcoded |
| `vault_sweep_3.py` | `VAULT` path hardcoded with specific user path |
| `trading-tools/run_ollama_sweep.py` | API endpoints and paths hardcoded |
| `trading-tools/staging/ml/live_pipeline.py` | `sys.path.insert` without validation |

---

## PINE SCRIPT SPECIFIC ISSUES

- Division by zero in `highest - lowest == 0` in stoch_k functions (handled with default 50.0 — review flagged but this is intentional behavior)
- Stub functions returning hardcoded values in some indicator files
- `i_secret` webhook field potentially exposed in alerts — Pine Script limitation, not fixable

---

## FILE COVERAGE MAP

| Directory | Files Reviewed | 🔴 Critical | 🟢 Clean |
|-----------|---------------|-------------|---------|
| 02-STRATEGY (Pine) | ~15 | ~10 | ~5 |
| engine/ | ~12 | ~8 | ~4 |
| ml/ | ~6 | ~3 | ~3 |
| optimizer/ | ~8 | ~5 | ~3 |
| scripts/ | ~35 | ~20 | ~15 |
| signals/ | ~10 | ~7 | ~3 |
| staging/ | ~8 | ~5 | ~3 |
| strategies/ | ~6 | ~3 | ~3 |
| trading-tools/ | ~50 | ~35 | ~15 |
| vault root | ~4 | ~3 | ~1 |
| **Total** | **~234** | **~168** | **~66** |

---

## RECOMMENDED PRIORITY FIXES

In order of impact on live trading accuracy:

1. **IMMEDIATE**: `exit_manager.py` BE stop sign bug — trades currently stopped out at wrong price
2. **IMMEDIATE**: `staging/ml/live_pipeline.py` hardcoded confidence — ML filter is non-functional
3. **HIGH**: `engine/backtester.py` double commission — all historical backtest results invalid
4. **HIGH**: `engine/backtester_v382.py` re-entry state — extra trades firing after stop-outs
5. **HIGH**: State machine stage_lookback `>` vs `>=` — affects signal timing across all versions
6. **MEDIUM**: `signals/clouds.py` EMA off-by-one — cloud signals 1 bar late
7. **MEDIUM**: `strategies/signals.py` cooldown off-by-one — more trades than expected
8. **MEDIUM**: `exits/phased.py` reset() — stale SL on trade reuse
9. **LOW**: `fetch_data.py` month calculation — minor date range error
10. **LOW**: `db.py` hardcoded password — security debt

---

*Generated by research subagent. Read 14,579 lines across 30 chunks of 500 lines each.*
