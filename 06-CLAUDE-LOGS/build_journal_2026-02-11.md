# Build Journal — 2026-02-10 to 2026-02-11

## Scope of Work (What Was Requested)

User requested: Build all missing files in the Four Pillars ML backtester pipeline so the codebase is complete, tested, and error-free for a fresh start.

Three phases of work:
1. Build 11 missing infrastructure files (strategies/, engine/, optimizer/, ml/, gui/)
2. Comprehensive inventory of entire codebase to find remaining gaps
3. Build 4 remaining items into staging/ folder for safe deployment

---

## Phase 1: 11 Missing Files (build_missing_files.py)

**Build script**: `scripts/build_missing_files.py` (1570 lines)
**Result**: 10 written (1 skipped — base_strategy.py already existed), 19/19 tests passed

Files created:
1. `strategies/base_strategy.py` — SKIPPED (already existed from Qwen build)
2. `engine/exit_manager.py` — ExitManager with ExitConfig, 4 risk methods (be_only, be_plus_fees, be_plus_fees_trail_tp, be_trail_tp)
3. `strategies/indicators.py` — Wraps stochastics + clouds + ATR + volume into calculate_all_indicators()
4. `strategies/signals.py` — generate_all_signals() with cooldown, adds signal_type/direction columns
5. `strategies/cloud_filter.py` — apply_cloud3_filter() blocks signals violating Cloud 3 direction
6. `strategies/four_pillars_v3_8.py` — FourPillarsV38(BaseStrategy) with get_name()="FourPillarsV38"
7. `optimizer/walk_forward.py` — Time-based walk_forward_split() + walk_forward_validate()
8. `optimizer/aggregator.py` — aggregate_results() with weighted median for numeric, mode for categorical
9. `ml/xgboost_trainer.py` — train_xgboost() wrapper, predict_skip_take()
10. `gui/coin_selector.py` — fuzzy_match() using SequenceMatcher, get_available_coins()
11. `gui/parameter_inputs.py` — DEFAULT_PARAMS dict + parameter_inputs() Streamlit form

### Bugs Fixed During Phase 1
- **optimizer/walk_forward.py**: Test used 5000 bars (17 days) but needed 2+ months. Fixed: 100,000 bars, train_months=2, test_months=1
- **Streamlit ScriptRunContext spam**: parameter_inputs() calling st.sidebar flooded terminal. Fixed: suppress logging, test uses DEFAULT_PARAMS directly

---

## Phase 2: Comprehensive Inventory

**Total files found**: 62 Python files (52 with actual code)
**All existing modules**: Import-tested and verified working

Gaps identified:
1. Dashboard missing ML tabs (only single-view, no MFE/MAE/SHAP/WFE tabs)
2. Dashboard test script missing
3. WEEXFetcher import bug in run_backtest.py line 13
4. ml/live_pipeline.py not built

---

## Phase 3: 4 Staging Files (build_staging.py)

**Build script**: `scripts/build_staging.py` (1692 lines)
**Status**: Written, NOT YET RUN by user

Files to create:
1. `staging/dashboard.py` — 5-tab ML dashboard:
   - Tab 1: Overview (metrics, equity curve, grade breakdown, BE impact)
   - Tab 2: Trade Analysis (P&L distribution, direction/grade, duration)
   - Tab 3: MFE/MAE & Losers (scatter, Sweeney A/B/C/D, BE optimization, ETD)
   - Tab 4: ML Meta-Label (features, triple-barrier, XGBoost, SHAP, bet sizing)
   - Tab 5: Validation (Purged CV, walk-forward efficiency)

2. `staging/test_dashboard_ml.py` — Tests all 5 tabs with real RIVERUSDT data, no Streamlit needed

3. `staging/run_backtest.py` — Fixed: WEEXFetcher -> BybitFetcher import

4. `staging/ml/live_pipeline.py` — LivePipeline: rolling buffer -> indicators -> state machine -> features -> ML filter -> FilteredSignal output

---

## Complete File Inventory (as of 2026-02-11)

### data/ (3 files)
- `__init__.py`, `db.py` (67L), `fetcher.py` (247L)

### engine/ (5 files)
- `__init__.py`, `backtester.py` (380L), `commission.py` (89L), `exit_manager.py` (142L), `metrics.py` (258L), `position.py` (196L)

### exits/ (5 files)
- `__init__.py`, `static_atr.py` (83L), `cloud_trail.py` (108L), `avwap_trail.py` (94L), `phased.py` (118L)

### signals/ (5 files)
- `__init__.py`, `stochastics.py` (152L), `clouds.py` (96L), `four_pillars.py` (142L), `state_machine.py` (287L)

### strategies/ (6 files)
- `__init__.py`, `base_strategy.py` (30L), `four_pillars_v3_8.py` (89L), `cloud_filter.py` (52L), `indicators.py` (68L), `signals.py` (94L)

### ml/ (9 files)
- `__init__.py`, `features.py` (234L), `triple_barrier.py` (105L), `purged_cv.py` (118L), `meta_label.py` (167L), `shap_analyzer.py` (156L), `bet_sizing.py` (129L), `walk_forward.py` (138L), `loser_analysis.py` (156L), `xgboost_trainer.py` (84L)

### optimizer/ (6 files)
- `__init__.py`, `grid_search.py` (147L), `bayesian.py` (189L), `monte_carlo.py` (143L), `aggregator.py` (89L), `ml_regime.py` (163L), `walk_forward.py` (94L)

### gui/ (3 files)
- `__init__.py`, `coin_selector.py` (68L), `parameter_inputs.py` (184L)

### scripts/ (17 files)
- `run_backtest.py` (187L), `dashboard.py` (412L), `dashboard_backup.py`, `fetch_data.py` (156L), `fetch_sub_1b.py` (198L), `sweep_low_price.py` (94L), `sweep_v38.py` (145L), `sweep_all_coins.py` (198L), `sweep_all_coins_ml.py` (243L), `run_ml_analysis.py` (267L), `test_build.py` (92L), `test_ml_pipeline.py` (201L), `master_build.py` (312L), `build_ml_pipeline.py` (487L), `fix_ml_features.py` (156L), `build_missing_files.py` (324L), `build_staging.py` (289L)

### Pine Script (2 files)
- `02-STRATEGY/Indicators/four_pillars_v3_8.pine` (467L) — indicator only
- `02-STRATEGY/Indicators/four_pillars_v3_8_strategy.pine` (601L) — full strategy

### Data Assets
- **30+ coins cached** in data/cache/ (1m + 5m Parquet)
- **Sweep results**: data/sweep_v38_results.csv (60 rows, 5 coins x 12 BE configs)
- **PostgreSQL**: vince database, 5 tables, PG16 port 5433

---

## Pending User Actions

1. Run: `cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester" && python scripts/build_staging.py`
2. Validate: `python staging/test_dashboard_ml.py`
3. Preview: `streamlit run staging/dashboard.py`
4. Deploy:
   - `copy staging\dashboard.py scripts\dashboard.py`
   - `copy staging\run_backtest.py scripts\run_backtest.py`
   - `copy staging\test_dashboard_ml.py scripts\test_dashboard_ml.py`
   - `copy staging\ml\live_pipeline.py ml\live_pipeline.py`

---

## Decisions Made
- Staging folder approach chosen over direct overwrite (user's choice)
- All 4 items built (user chose "All 4 items")
- build_staging.py includes syntax checks + smoke tests (100 bars through live_pipeline)
- WEEXFetcher bug fixed (-> BybitFetcher) in staging copy only, production run_backtest.py still has old import

---

## Phase 4: v3.8.3 Full Python Port (2026-02-11)

**What was built**: Complete v3.8.3 Python backtester — 4-stage state machine, A/B/C/D/ADD/RE/R signals, ATR SL (configurable multiplier), AVWAP trailing after checkpoint, scale-out mechanism, Cloud 3 directional filter.

### v3.8.3 Files Created (8 source + 3 results)
- `signals/state_machine_v383.py` — 4-stage stochastic state machine (60-K zone trigger, cross detection, confirmation tracking)
- `signals/four_pillars_v383.py` — compute_signals_v383(): stochastics + clouds + ATR + state machine + Cloud 3 filter + Cloud 2 re-entry
- `engine/position_v383.py` — PositionSlot383 + Trade383: ATR/AVWAP SL, MFE/MAE, scale-out (half position at checkpoint)
- `engine/backtester_v383.py` — Backtester383: 4-slot engine, execution order (exits -> update -> scale -> pending -> entries -> adds -> re-entry)
- `scripts/run_backtest_v383.py` — CLI with NET (w/rebate), volume tracking, grade breakdown
- `scripts/sweep_sl_mult_v383.py` — Sweeps SL 1.0-3.0 ATR across 10 coins
- `scripts/test_v383.py` — Import + smoke test
- `scripts/mfe_analysis_v383.py` — MFE/MAE analysis per grade, LSG buckets
- `scripts/capital_analysis_v383.py` — Multi-coin capital overlap analysis
- `scripts/validation_v371_vs_v383.py` — Side-by-side v3.7.1 vs v3.8.3 with stoch 9,3 and AVWAP context

### v3.8.3 Key Results
- `results/sweep_v383_sl_mult.md` — SL=2.5 ATR best (9/10 coins profitable)
- `results/mfe_analysis_v383.md` — LSG 85-92%, D+R grades drag P&L
- `results/validation_v371_vs_v383_RIVERUSDT.md` — v3.8.3 +$6,261 vs v3.7.1 -$2,948

### Modifications to Shared Files
- `engine/commission.py` — Added volume tracking: total_volume, total_sides, charge() and charge_custom() accumulate notional per side

---

## Phase 5: v3.8.4 TP + Capital Analysis (2026-02-11)

**What was built**: v3.8.4 adds optional ATR-based take profit on top of v3.8.3. TP sweep showed only TP=2.0 ATR beats the no-TP baseline. Capital analysis for multi-coin $10K account.

### v3.8.4 Files Created (5 source + 1 result)
- `engine/position_v384.py` (261L) — PositionSlot384 + Trade384: identical to v3.8.3 + tp_mult parameter. TP = entry +/- ATR * tp_mult. SL checked first (pessimistic) when both could trigger.
- `engine/backtester_v384.py` (566L) — Backtester384: imports position_v384, handles TP exit (exit_price = slot.tp), only re-entry on SL not TP. Metrics include tp_exits, sl_exits (total + per-grade). Capital utilization metrics: avg_positions, max_positions_used, pct_time_flat, avg_margin_used, peak_margin_used.
- `scripts/run_backtest_v384.py` (145L) — CLI with --tp-mult (default None = no TP), --sl-mult (default 2.5). Output includes TP/SL exits, volume, grade breakdown with per-grade TP counts, capital utilization section.
- `scripts/sweep_tp_v384.py` (192L) — Sweeps TP: None, 0.50, 0.75, 1.00, 1.25, 1.50, 2.00 ATR. Summary table, grade breakdown per TP level, delta vs baseline.
- `scripts/capital_analysis_v384.py` (286L) — Multi-coin (default: RIVER, KITE, BERA). Overlays equity curves on common DatetimeIndex. Combined drawdown from overlapping curves (not sum of individual DDs). Capital requirement = peak margin + combined DD. Position distribution histogram.

### v3.8.4 Key Results
- `results/sweep_v384_tp_RIVERUSDT.md`:
  - No TP (baseline): +$6,261 ($3.29/tr)
  - TP=0.50: -$5,095 (catastrophic, caps winners)
  - TP=2.00: +$7,911 ($3.77/tr) — ONLY level beating baseline
  - MFE analysis was WRONG about tight TP. Capping winners destroys more value than saving LSG trades.
- Capital analysis (3 coins, TP=2.0): Combined DD $6,138 (actual, vs $8,509 sum). Peak margin $1,500. Total needed $7,638 < $10K. Headroom $2,362. Total net +$13,872 (138.7% return on $10K).

### v3.8.4 TP Sweep — All 3 Coins (2026-02-11)

TP=2.0 ATR is NOT universal. Only helps RIVER:

| Coin | No TP (net) | TP=2.0 (net) | Delta | Optimal |
|------|-------------|--------------|-------|---------|
| RIVER | +$6,261 ($3.29/tr) | +$7,911 ($3.77/tr) | +$1,651 | TP=2.0 |
| KITE | +$5,069 ($2.79/tr) | +$3,552 ($1.72/tr) | -$1,518 | No TP |
| BERA | +$4,883 ($2.67/tr) | +$2,410 ($1.14/tr) | -$2,473 | No TP |

KITE and BERA: ALL TP levels worse than no TP. Every delta negative.
Combined 3-coin optimal (per-coin TP): $7,911 + $5,069 + $4,883 = +$17,863
Combined 3-coin uniform TP=2.0: $7,911 + $3,552 + $2,410 = +$13,872
Difference: +$3,991 from per-coin optimization.

Result files:
- `results/sweep_v384_tp_RIVERUSDT.md`
- `results/sweep_v384_tp_KITEUSDT.md`
- `results/sweep_v384_tp_BERAUSDT.md`

### Sanity Check (2026-02-11)
- All 6 v3.8.4 source files + 2 shared dependencies reviewed line by line
- **No bugs found**
- Execution order correct in backtester (exits -> update -> scale-out -> pending -> entries -> adds -> re-entry)
- SL checked before TP (pessimistic) in position slot
- Commission volume/sides tracking correct for partials (scale-outs)
- Capital utilization metrics computed from valid bars (excludes ATR warmup)
- Combined drawdown correctly computed from overlapping equity curves
- Design note: capital_analysis defaults TP=2.0 (best from sweep), run_backtest defaults None (explicit opt-in)

---

## Updated File Inventory (as of 2026-02-11 evening)

### engine/ (9 files)
- `__init__.py`, `avwap.py` (53L), `backtester.py` (380L), `backtester_v383.py`, `backtester_v384.py` (566L), `commission.py` (113L), `exit_manager.py` (142L), `metrics.py` (258L), `position.py` (196L), `position_v383.py`, `position_v384.py` (261L)

### signals/ (7 files)
- `__init__.py`, `stochastics.py` (152L), `clouds.py` (96L), `four_pillars.py` (142L), `four_pillars_v383.py`, `state_machine.py` (287L), `state_machine_v383.py`

### scripts/ (27 files)
- All 17 from Phase 1-3 inventory, plus:
- `run_backtest_v383.py`, `sweep_sl_mult_v383.py`, `test_v383.py`, `mfe_analysis_v383.py`, `capital_analysis_v383.py`, `validation_v371_vs_v383.py`
- `run_backtest_v384.py` (145L), `sweep_tp_v384.py` (192L), `capital_analysis_v384.py` (286L)

### results/ (4 files)
- `sweep_v383_sl_mult.md`, `mfe_analysis_v383.md`, `validation_v371_vs_v383_RIVERUSDT.md`, `sweep_v384_tp_RIVERUSDT.md`

---

## Remaining Steps

1. **Run TP sweep on KITE and BERA**: `python scripts/sweep_tp_v384.py --symbol KITEUSDT` and `--symbol BERAUSDT` to confirm TP=2.0 is optimal across all 3 coins
2. **Deploy staging files**: User still hasn't run `python scripts/build_staging.py` from Phase 3
3. **ML meta-label on D+R grades**: D and R are the biggest drag. XGBoost filter could skip bad D/R trades. Infrastructure exists in ml/ modules.
4. **Live testing on TradingView**: Compare Pine Script v3.8 indicator results with Python backtest
5. **Multi-coin sweep**: Run capital_analysis_v384.py with more coins (e.g., add PEPE, SAND, HYPE) to find optimal portfolio
6. **BE raise optimization**: ATR-based BE raise (Hilpisch formula) could convert more LSG losers to winners. LSG is 85-92% — significant opportunity.

---

## Phase 6: Dashboard Overhaul + Data Normalizer (2026-02-12)

See `BUILD-JOURNAL-2026-02-12.md` in Obsidian Vault root for full details.

### New Files
- `data/normalizer.py` (~370L) -- Universal OHLCV CSV-to-parquet normalizer
- `scripts/convert_csv.py` (~150L) -- CLI wrapper for normalizer
- `scripts/test_normalizer.py` (~450L) -- 17 normalizer tests
- `scripts/test_sweep.py` (~300L) -- 11 sweep/dashboard tests

### Edited Files
- `scripts/dashboard.py` (~1450L, was 1129L) -- Mode navigation, sweep persistence, coin list/upload, LSG bars

### Dashboard Architecture
- Mode machine: settings | single | sweep | sweep_detail
- Sweep: incremental (1 coin/rerun), CSV persistence, auto-resume, params_hash
- Sweep source radio: All Cache | Custom List | Upload Data
- Multi-interval: get_cached_symbols() scans all intervals, load_data() tries native parquet first

### BUILD-NORMALIZER-3PHASE.md -- ALL 3 BUILDS COMPLETE
- BUILD 1: `data/normalizer.py` -- auto-detect delimiter, columns, timestamps, validate, save parquet
- BUILD 2: Dashboard sweep coin list + data upload (radio selector, file uploaders, normalizer integration)
- BUILD 3: `scripts/convert_csv.py` -- CLI with --preview, --batch, --columns, --resample
