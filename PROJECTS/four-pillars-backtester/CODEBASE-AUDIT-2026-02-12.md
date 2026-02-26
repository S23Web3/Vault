# Four Pillars Codebase Audit — Feb 12, 2026

## VERSION CHAIN (Chronological)

### v3.7.1 (Original)
- `engine/position.py` + `engine/backtester.py`
- `signals/four_pillars.py` + `signals/state_machine.py`
- Single position, BE raise + AVWAP trail, static ATR SL/TP
- **notional = $10,000**, sl_mult=1.0, tp_mult=1.5
- Result: 20,283 trades, +$97K, 17% WR

### v3.8.2 (3-Stage SL)
- `engine/position_v382.py` + `engine/backtester_v382.py`
- `signals/four_pillars_v382.py` + `signals/state_machine_v382.py`
- 4-slot pyramiding, 3-stage AVWAP→ATR→Cloud3 trail
- Multi-level BE raise (trigger_mult, lock_mult pairs)
- **notional = $5,000** per slot, Cloud3 directional filter
- Result: 621 trades, -$9.7K (execution order bug + Cloud3 filter killed volume)

### v3.8.3 (Simplified SL)
- `engine/position_v383.py` + `engine/backtester_v383.py`
- `signals/four_pillars_v383.py` + `signals/state_machine_v383.py`
- Dropped 3-stage SL → ATR initial then AVWAP center trail
- Added scale-out mechanism (50% at checkpoints hitting ±2σ)
- Added D signal (continuation while 60-K pinned)
- Removed explicit BE raise — AVWAP center ratchet IS the BE mechanism
- **notional = $5,000**, sl_mult=2.0

### v3.8.4 (Current — adds TP)
- `engine/position_v384.py` + `engine/backtester_v384.py`
- Signals: reuses `signals/four_pillars_v383.py` (no signal changes)
- State machine: reuses `signals/state_machine_v383.py`
- Added optional `tp_mult` parameter (ATR-based TP)
- Everything else identical to v3.8.3
- **notional = $5,000**, sl_mult default 2.0 (CLI default 2.5)

---

## FILE STATUS MAP

### ENGINE (core logic)

| File | Version | Status | Used by |
|------|---------|--------|---------|
| `avwap.py` | Shared | ✅ ACTIVE | All v3.8.x |
| `commission.py` | Shared | ✅ ACTIVE | All versions |
| `metrics.py` | v3.7.1 only | ⚠️ LEGACY | backtester.py only |
| `exit_manager.py` | Unknown | ❓ CHECK | Nothing imports it |
| `position.py` | v3.7.1 | ⚠️ LEGACY | backtester.py |
| `position_v382.py` | v3.8.2 | ⚠️ SUPERSEDED | backtester_v382.py |
| `position_v383.py` | v3.8.3 | ⚠️ SUPERSEDED | backtester_v383.py |
| `position_v384.py` | v3.8.4 | ✅ CURRENT | backtester_v384.py |
| `backtester.py` | v3.7.1 | ⚠️ LEGACY | dashboard.py, run_backtest.py |
| `backtester_v382.py` | v3.8.2 | ⚠️ SUPERSEDED | run_backtest_v382.py |
| `backtester_v383.py` | v3.8.3 | ⚠️ SUPERSEDED | run_backtest_v383.py |
| `backtester_v384.py` | v3.8.4 | ✅ CURRENT | run_backtest_v384.py, sweep_tp_v384.py |

### SIGNALS (entry detection)

| File | Version | Status | Used by |
|------|---------|--------|---------|
| `stochastics.py` | Shared | ✅ ACTIVE | All signal pipelines |
| `clouds.py` | Shared | ✅ ACTIVE | All signal pipelines |
| `four_pillars.py` | v3.7.1 | ⚠️ LEGACY | backtester.py chain |
| `four_pillars_v382.py` | v3.8.2 | ⚠️ SUPERSEDED | backtester_v382.py chain |
| `four_pillars_v383.py` | v3.8.3/4 | ✅ CURRENT | backtester_v383/384 chain |
| `state_machine.py` | v3.7.1 | ⚠️ LEGACY | four_pillars.py |
| `state_machine_v382.py` | v3.8.2 | ⚠️ SUPERSEDED | four_pillars_v382.py |
| `state_machine_v383.py` | v3.8.3/4 | ✅ CURRENT | four_pillars_v383.py |

### SCRIPTS (runners)

| File | Version | Status | Notes |
|------|---------|--------|-------|
| `run_backtest.py` | v3.7.1 | ❌ BROKEN | Imports WEEXFetcher (deprecated) |
| `run_backtest_v382.py` | v3.8.2 | ⚠️ SUPERSEDED | Works but old version |
| `run_backtest_v383.py` | v3.8.3 | ⚠️ SUPERSEDED | Works but no TP |
| `run_backtest_v384.py` | v3.8.4 | ✅ CURRENT | Full featured, working |
| `dashboard.py` | v3.7.1 | ❌ OUTDATED | Imports old backtester.py |
| `sweep_tp_v384.py` | v3.8.4 | ✅ CURRENT | TP parameter sweep |
| `capital_analysis_v384.py` | v3.8.4 | ✅ CURRENT | Capital utilization analysis |
| `sweep_all_coins.py` | v3.7.1 | ⚠️ LEGACY | Uses old backtester |
| `sweep_all_coins_ml.py` | v3.7.1 | ⚠️ LEGACY | Uses old backtester |
| `sweep_v38.py` | v3.8.x | ❓ CHECK | May use old engine |
| `batch_sweep_v382.py` | v3.8.2 | ⚠️ SUPERSEDED | |
| `batch_sweep_v382_be.py` | v3.8.2 | ⚠️ SUPERSEDED | |
| `sweep_sl_mult_v383.py` | v3.8.3 | ⚠️ SUPERSEDED | |
| `analyze_v382_failure.py` | v3.8.2 | 📊 DIAGNOSTIC | One-time analysis |
| `lsg_diagnostic_v382.py` | v3.8.2 | 📊 DIAGNOSTIC | One-time analysis |
| `mfe_analysis_v383.py` | v3.8.3 | 📊 DIAGNOSTIC | One-time analysis |
| `compare_v382.py` | v3.8.2 | 📊 DIAGNOSTIC | One-time analysis |
| `validation_v371_vs_v383.py` | Comparison | 📊 DIAGNOSTIC | Cross-version comparison |
| `capital_analysis_v383.py` | v3.8.3 | ⚠️ SUPERSEDED | Use v384 version |
| `fetch_data.py` | Shared | ✅ ACTIVE | CLI fetcher |
| `fetch_sub_1b.py` | Shared | ✅ ACTIVE | Sub-1B mcap discovery |
| `download_1year_gap.py` | Shared | ⚠️ HAS BUG | _FIXED version exists |
| `download_1year_gap_FIXED.py` | Shared | ✅ CURRENT | Gap-fill downloader |
| `download_historical_quick.py` | Shared | ✅ ACTIVE | Quick download |
| `update_historical_incremental.py` | Shared | ✅ ACTIVE | Incremental updates |
| `check_cache_status.py` | Shared | ✅ ACTIVE | Cache health check |
| `sanity_check_cache.py` | Shared | ✅ ACTIVE | Data validation |
| `build_staging.py` | Staging | ❌ OBSOLETE | Targets old backtester |
| `test_ml_pipeline.py` | ML | ❓ CHECK | |
| `run_ml_analysis.py` | ML | ❓ CHECK | |
| `visualize_flow.py` | Docs | ✅ ACTIVE | VINCE flowchart |
| `resample_timeframes.py` | Data | ✅ ACTIVE | 1m→5m conversion |

### ML MODULES (VINCE)

| File | Purpose | Status |
|------|---------|--------|
| `ml/features.py` | Feature extraction at entry time | ✅ BUILT, never run on v384 |
| `ml/meta_label.py` | XGBoost meta-labeling (skip/take) | ✅ BUILT, never run on v384 |
| `ml/triple_barrier.py` | Label generation (win/loss/timeout) | ✅ BUILT, never run on v384 |
| `ml/xgboost_trainer.py` | XGBoost training wrapper | ✅ BUILT, never run on v384 |
| `ml/bet_sizing.py` | Kelly criterion position sizing | ✅ BUILT, never run |
| `ml/loser_analysis.py` | LSG (losers saw green) analysis | ✅ BUILT, used in diagnostics |
| `ml/purged_cv.py` | Purged K-fold cross validation | ✅ BUILT, never run |
| `ml/shap_analyzer.py` | SHAP feature importance | ✅ BUILT, never run |
| `ml/walk_forward.py` | Walk-forward validation | ✅ BUILT, never run |

### OPTIMIZER MODULES

| File | Purpose | Status |
|------|---------|--------|
| `optimizer/grid_search.py` | Parameter grid search | ✅ BUILT, needs PyTorch ❓ |
| `optimizer/bayesian.py` | Bayesian optimization | ✅ BUILT, needs PyTorch ❓ |
| `optimizer/ml_regime.py` | Regime detection model | ✅ BUILT, needs PyTorch |
| `optimizer/monte_carlo.py` | Monte Carlo validation | ✅ BUILT |
| `optimizer/walk_forward.py` | Walk-forward optimizer | ✅ BUILT |
| `optimizer/aggregator.py` | Results aggregation | ✅ BUILT |

### EXITS (standalone — legacy architecture)

| File | Purpose | Status |
|------|---------|--------|
| `exits/avwap_trail.py` | AVWAP trailing (v3.6 style) | ⚠️ LEGACY — replaced by avwap.py |
| `exits/cloud_trail.py` | Cloud3 trailing | ⚠️ LEGACY |
| `exits/phased.py` | Multi-phase exits | ⚠️ LEGACY |
| `exits/static_atr.py` | Static ATR SL/TP | ⚠️ LEGACY |

### OTHER

| File | Purpose | Status |
|------|---------|--------|
| `data/fetcher.py` | BybitFetcher (+ deprecated WEEXFetcher) | ✅ ACTIVE |
| `data/db.py` | PostgreSQL interface | ❓ Likely unused |
| `gui/coin_selector.py` | Dashboard coin picker | ⚠️ Tied to old dashboard |
| `gui/parameter_inputs.py` | Dashboard param inputs | ⚠️ Tied to old dashboard |
| `strategies/` | Alternate strategy architecture | ❓ Likely dead code |

---

## WHAT v3.8.4 ACTUALLY DOES

**Entry signals:** v3.8.3 state machine with A/B/C/D grades + re-entry
- A (4/4 stochastics): bypasses Cloud3 filter
- B (3/4): requires Cloud3 alignment
- C (2/4): requires price firmly in Cloud3 direction
- D (continuation): 60-K stays pinned, 9-K cycles again
- R (re-entry): after SL, limit order at AVWAP ±1σ

**Position management:** 4 slots, $5,000 each, 3-bar cooldown
- ADD: limit at AVWAP -1σ when price touches -2σ (inherits parent AVWAP)
- RE: same mechanic but after SL exit

**Exit system:**
- Initial SL: ATR × sl_mult (default 2.5 in CLI, 2.0 in code)
- After 5 bars: SL moves to AVWAP center, ratchets only tighter
- Optional TP: ATR × tp_mult (default None = no TP)
- Scale-out: every 5 bars, if price at AVWAP ±2σ, close 50% (max 2)
- SL checked FIRST (pessimistic) — execution order is correct

**NO explicit BE raise.** AVWAP center trail naturally passes entry price as trade moves favorably = implicit BE lock.

---

## GAPS IN v3.8.4

1. **No v3.8.4 dashboard** — dashboard.py imports old backtester.py
2. **No v3.8.4 multi-coin sweep** — sweep_all_coins.py uses old engine
3. **ML pipeline not wired to v3.8.4** — features/meta_label built for old Trade format
4. **No test_v384.py** — test files exist for v382/v383 only
5. **sl_mult mismatch** — code default 2.0, CLI default 2.5

---

## DEAD CODE (safe to archive)

**Engine:** position.py, position_v382.py, position_v383.py, backtester.py, backtester_v382.py, backtester_v383.py, exit_manager.py
**Signals:** four_pillars.py, four_pillars_v382.py, state_machine.py, state_machine_v382.py
**Scripts:** run_backtest.py, run_backtest_v382.py, run_backtest_v383.py, batch_sweep_v382*.py, sweep_sl_mult_v383.py, build_staging.py, test_v382.py, test_v383.py
**Exits:** entire exits/ directory
**Staging:** entire staging/ directory
