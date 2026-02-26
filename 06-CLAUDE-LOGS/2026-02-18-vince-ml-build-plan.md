# VINCE ML Pipeline -- Revised Master Build Plan
**Date:** 2026-02-18
**Model:** Opus 4.6 (plan) + Sonnet 4.5 (execute)
**Status:** APPROVED -- ready to execute

---

## Context

The Sonnet-generated build instructions have **15 discrepancies** when cross-referenced against three authoritative sources:
1. **SPEC-C-VINCE-ML.md** -- the actual architecture spec
2. **BUILD-VINCE-ML.md** -- the actual build spec (P2+B2 XGBoost section)
3. **Book analyses** -- De Prado (AFML), Stefan/Jansen (ML4T), Van Tharp (R-multiples)

This plan fixes all discrepancies and categorizes the build into sections ordered by dependency.

---

## Discrepancy Table (Books + Specs vs Sonnet Build)

| # | Source | What Sonnet Build Says | What Source Says | Impact |
|---|--------|----------------------|-----------------|--------|
| 1 | SPEC-C | 70/10/20 pool split | **60/20/20** (Pool A/B/C) | Wrong split ratios |
| 2 | SPEC-C | XGBoost = production model | XGBoost = **AUDITOR only**, PyTorch = production | Wrong model role |
| 3 | SPEC-C | One global model | **One unified model** (PyTorch) with per-coin XGBoost auditors | Architecture mismatch |
| 4 | BUILD-VINCE-ML | Only PnL labeling (be_fees > 0.55) | **Two modes**: Exit (TP=1/SL=0) and PnL (win/loss) | Missing labeling mode |
| 5 | BUILD-VINCE-ML | No grade filtering | **Grade filtering D+R** with threshold sweep 0.3-0.7 | Missing key feature |
| 6 | BUILD-VINCE-ML | No walk-forward | **Walk-forward efficiency** (WFE) with ROBUST/MARGINAL/OVERFIT rating | Missing validation |
| 7 | De Prado Ch.3 | Simple win/loss labels | **Triple-barrier labeling** (dynamic SL/TP/time exit) | Inferior labeling |
| 8 | De Prado Ch.3 | No meta-labeling | **Meta-labeling**: ML decides size/skip on Four Pillars signals | Missing core technique |
| 9 | De Prado Ch.4 | No sample weights | **Sequential bootstrap + average uniqueness** for non-IID trades | Overfit risk |
| 10 | De Prado Ch.8 | SHAP after training only | **Feature importance BEFORE backtest** (ex-ante screening) | Wrong order |
| 11 | De Prado Ch.14 | No selection bias correction | **Deflated Sharpe ratio** for multi-model comparison | Overfit risk |
| 12 | Van Tharp | No R-multiple reporting | **R-multiples, SQN, expectunity** as validation metrics | Missing metrics |
| 13 | API | `classify_coins()` | `classify_coin_tiers()` | Wrong function |
| 14 | API | `tree_method='gpu_hist'` | `device='cuda'` + `tree_method='hist'` | Deprecated API |
| 15 | Data | Train on 14-row vince_features.csv | Per-trade features from backtester (thousands of rows per coin) | Wrong training data |

---

## Existing Infrastructure (DO NOT REWRITE)

All 9 ML modules exist and implement book-prescribed techniques:

| Module | Book Source | Technique | Status |
|--------|-----------|-----------|--------|
| `ml/triple_barrier.py` | De Prado Ch.3 | Dynamic SL/TP/time labeling | BUILT, not wired |
| `ml/meta_label.py` | De Prado Ch.3 | ML confidence on top of white-box signals | BUILT, not wired |
| `ml/purged_cv.py` | De Prado Ch.7 | Purged K-fold + embargo | BUILT, has bugs |
| `ml/features.py` | Jansen Ch.6 | Per-trade feature extraction (13 cols) | BUILT, has bugs |
| `ml/features_v2.py` | Jansen Ch.6 | Extended features (26 cols) | BUILT, no bug fixes |
| `ml/xgboost_trainer.py` | Jansen Ch.14 | XGBoost binary classifier | BUILT, no GPU |
| `ml/shap_analyzer.py` | Jansen Ch.8 | SHAP feature attribution | BUILT, fragile |
| `ml/bet_sizing.py` | De Prado Ch.10 | Kelly/linear/binary sizing | BUILT, edge case |
| `ml/walk_forward.py` | De Prado Ch.12 | Walk-forward validation | BUILT, not wired |
| `ml/loser_analysis.py` | Van Tharp | Trade outcome patterns | BUILT, not wired |
| `ml/coin_features.py` | SPEC-C Part 1 | 10 OHLCV-derived features per coin | BUILT, clean |
| `ml/training_pipeline.py` | SPEC-C | Pool assignment + training loop | BUILT, 60/20/20 |

Also exists:
| Module | Purpose |
|--------|---------|
| `signals/state_machine_v383.py` | Four Pillars signal generation |
| `engine/backtester_v384.py` | Trade execution |
| `engine/commission.py` | Commission model (0.08% taker / 0.02% maker) |
| `ml/vince_model.py` | PyTorch 3-branch model (149 lines, Phase 2) |
| `research/coin_classifier.py` | KMeans tier assignment |

---

## SECTION 0: Strategy Plugin Architecture (NEW -- user decision)
**Build script:** Part of `scripts/build_train_vince_v1.py`
**Output:** `strategies/base.py`, `strategies/four_pillars.py`, `strategies/__init__.py`
**Blockers:** None
**Duration:** ~15 min (part of Section D build)

### Why:
MEMORY.md says "strategy-agnostic ML agent, Four Pillars is the FIRST strategy loaded."
But all ml/ modules hardcode Four Pillars features (stoch_9, cloud3_bull, grade_enc).
User chose: plugin system where Four Pillars is the first implementation.

### Interface (`strategies/base.py`):
```python
class StrategyPlugin:
    """Base class for all strategy plugins."""
    name: str                          # e.g. "four_pillars"

    def enrich_ohlcv(self, df) -> df:
        """Compute indicator columns (ATR, stochastics, clouds, etc.)"""
        raise NotImplementedError

    def compute_signals(self, df) -> df:
        """Add signal columns (entries, reentries, adds)."""
        raise NotImplementedError

    def get_backtester_params(self) -> dict:
        """Return backtester config (sl_mult, tp_mult, commission, etc.)."""
        raise NotImplementedError

    def extract_features(self, trades_df, ohlcv_df) -> DataFrame:
        """Extract per-trade features for ML training."""
        raise NotImplementedError

    def get_feature_names(self) -> list:
        """Return ordered list of feature column names."""
        raise NotImplementedError

    def label_trades(self, trades_df, mode='exit') -> Series:
        """Generate binary labels. Modes: 'exit' (TP=1/SL=0) or 'pnl' (win/loss)."""
        raise NotImplementedError
```

### Implementation (`strategies/four_pillars.py`):
- `enrich_ohlcv()` -- computes ATR(14), 4 stochastic K values, EMA34/50, Cloud 3 state, price_pos, base_vol
- `compute_signals()` -- wraps `FourPillarsStateMachine383`
- `get_backtester_params()` -- returns default params (sl_mult=1.0, tp_mult=2.0, commission_rate=0.0008, etc.)
- `extract_features()` -- wraps `features_v3.py::extract_trade_features()`
- `get_feature_names()` -- returns the corrected 13-column list (or 26 from v2)
- `label_trades()` -- Exit mode (TP=1/SL=0) and PnL mode (net_pnl > 0)

### Model Isolation (prevents cross-strategy contamination):
```
models/
  four_pillars/     -- all Four Pillars models (zero state from other strategies)
  vicky/            -- all Vicky models (fresh, no Four Pillars bias)
  andy/             -- all Andy models (fresh)
```
- `train_vince.py --strategy four_pillars` writes to `models/four_pillars/` ONLY
- New strategy = new empty directory, zero inherited weights
- SHARED (safely): coin_pools.json, raw OHLCV, validation tools (purged_cv, bet_sizing)
- NEVER SHARED: model weights, features, SHAP values, labels

### Future strategies (not built now, just documented):
- `strategies/vicky.py` -- copy trading (different signals, same backtester)
- `strategies/andy.py` -- FTMO rules (different risk params)

---

## SECTION A: Foundation Documentation
**Build script:** `scripts/build_docs_v1.py`
**Output:** `VERSION-MASTER.md`, `docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md`
**Blockers:** None
**Duration:** ~10 min

1. VERSION-MASTER.md -- single source of truth for all component versions, known bugs, planned versions, file locations
2. VINCE-ML-UML-DIAGRAMS.md -- 4 Mermaid diagrams:
   - Training pipeline (12-step sequence from BUILD-VINCE-ML.md)
   - Live inference flow (3-branch fusion from SPEC-C)
   - Component architecture (all 12 existing modules)
   - Data split protection (Pool A/B/C immutability)

---

## SECTION B: Data Infrastructure
**Build script:** `scripts/build_data_infra_v1.py`
**Output:** `results/coin_tiers.csv`, `data/coin_pools.json`
**Blockers:** None
**Duration:** ~5-15 min

1. `classify_coin_tiers()` (correct function name) on 399 coins in data/cache/
2. **60/20/20 split** (per SPEC-C and training_pipeline.py), NOT 70/10/20
   - Pool A: ~240 coins (training)
   - Pool B: ~80 coins (validation)
   - Pool C: ~79 coins (holdout, NEVER touched during development)
   - Stratified by tier (proportional representation)
   - Seed=42, frozen_date stamped
3. Validation: no duplicates, all 399 assigned, JSON round-trip

---

## SECTION C: ML Module Bug Fixes
**Build script:** Part of `scripts/build_train_vince_v1.py`
**Output:** 4 versioned fixed modules
**Blockers:** None
**Duration:** ~10 min

| New File | Fixes | Source Bugs |
|----------|-------|-------------|
| `ml/xgboost_trainer_v2.py` | GPU `device='cuda'`, mask indexing, remove `use_label_encoder` | xgboost_trainer.py lines 50, 67 |
| `ml/features_v3.py` | `get_feature_columns()` mismatch, `dt_series.iloc`, NaN guards, inherits v2's 26 features | features.py lines 94, 113, 157 |
| `ml/shap_analyzer_v2.py` | Empty array guard, binary-only assertion | shap_analyzer.py line 65 |
| `ml/bet_sizing_v2.py` | Kelly `avg_loss=0` guard, negative edge logging | bet_sizing.py line 86 |

---

## SECTION D: XGBoost Training Pipeline (Core Build)
**Build script:** `scripts/build_train_vince_v1.py`
**Output:** `scripts/train_vince.py`
**Blockers:** Section B (needs coin_pools.json), Section C (needs fixed modules)
**Duration to build:** ~20 min. Training run: 2-4 hours on GPU (user-initiated)

### Architecture per BUILD-VINCE-ML.md P2+B2:
- **Per-coin models** (one XGBoost auditor per coin)
- `--symbol RIVERUSDT` trains single coin
- `--symbol ALL` sweeps all 5m parquets

### 12-Step Pipeline (matching BUILD-VINCE-ML.md, using strategy plugin):
1. **Load strategy** -- `load_strategy(args.strategy)` (default: "four_pillars")
2. **Load OHLCV** -- `data/cache/{symbol}_5m.parquet`
3. **Enrich OHLCV** -- `strategy.enrich_ohlcv(df)` (ATR, stochastics, clouds)
4. **Generate signals** -- `strategy.compute_signals(df)` (entry/reentry/add columns)
5. **Run backtest** -- `Backtester384(strategy.get_backtester_params()).run(df)`
6. **Extract features** -- `strategy.extract_features(trades_df, df)` + `coin_features.py` (10 cols prepended)
7. **Label trades** -- `strategy.label_trades(trades_df, mode=args.label_mode)`:
   - Exit Mode (default): TP hit = 1, SL hit = 0, other = 0
   - PnL Mode (`--label-mode pnl`): net_pnl > 0 = 1, else 0
8. **Grade filtering** -- `--grade-filter D,R` with threshold sweep (0.3, 0.4, 0.5, 0.6, 0.7)
9. **Validation** -- TWO MODES per BUILD-VINCE-ML.md:
   - Default: 5-fold purged CV (purged_cv.py)
   - Walk-forward (`--walk-forward`): walk_forward.py with WFE score + ROBUST/MARGINAL/OVERFIT
10. **Train XGBoost** -- `xgboost_trainer_v2.py::train_xgboost()` (GPU-accelerated)
11. **SHAP analysis** -- `shap_analyzer_v2.py` (feature attribution)
12. **Bet sizing simulation** -- `bet_sizing_v2.py` (Kelly at multiple thresholds)
13. **Save** -- `models/{strategy}/{symbol}_xgb_{timestamp}.json` + `models/{strategy}/{symbol}_report_{timestamp}.json`

### CLI (matching BUILD-VINCE-ML.md):
```
python scripts/train_vince.py --symbol RIVERUSDT
python scripts/train_vince.py --symbol RIVERUSDT --walk-forward
python scripts/train_vince.py --symbol RIVERUSDT --grade-filter D,R
python scripts/train_vince.py --symbol RIVERUSDT --label-mode pnl
python scripts/train_vince.py --symbol ALL --top 20
```

### Report JSON per coin:
- symbol, timeframe, params, n_trades, n_features
- label_mode, label_distribution
- cv_metrics (accuracy, precision, recall, F1, AUC per fold)
- wfe_metrics (if --walk-forward: WFE score, rating)
- test_metrics (final holdout)
- feature_importance (sorted)
- shap_values (top 10 features)
- grade_analysis (filtered vs full model, net impact per threshold)
- bet_sizing_sim (binary/linear/Kelly results)

---

## SECTION E: Book-Prescribed Enhancements (Phase 2 -- Future Session)
**Purpose:** Integrate advanced techniques from De Prado and Van Tharp that the Sonnet build completely missed.
**These are NOT built this session** but documented for the next build.

### E1: Triple-Barrier Labeling (De Prado Ch.3)
- Wire existing `ml/triple_barrier.py` into train_vince.py as `--label-mode triple`
- Dynamic barriers: TP = N*ATR, SL = -M*ATR, time limit = K bars
- More information-rich labels than simple win/loss

### E2: Meta-Labeling (De Prado Ch.3)
- Wire existing `ml/meta_label.py` as secondary model layer
- Primary model = Four Pillars state machine (white-box signals)
- Secondary model = XGBoost decides TAKE/SKIP with confidence 0-1
- This IS the Vince architecture from SPEC-C

### E3: Sample Weights (De Prado Ch.4)
- Overlapping trades create non-IID samples
- Sequential bootstrap + average uniqueness weighting
- Prevents XGBoost from overfitting to redundant time periods

### E4: Feature Importance Pre-Screening (De Prado Ch.8)
- Run MDI/MDA BEFORE backtest optimization
- Filter to top-K features with stable importance across folds
- Reduces overfitting surface

### E5: Deflated Sharpe (De Prado Ch.14)
- Correct for selection bias when comparing 399 coin models
- Report deflated Sharpe alongside raw Sharpe in sweep_summary.csv

### E6: R-Multiples + SQN (Van Tharp)
- Compute R-multiple distribution per coin model
- SQN = mean(R) / std(R) * sqrt(n_trades)
- Expectunity = expectancy * opportunity (trades/year)
- Add to report JSON

---

## GPU Acceleration Strategy (RTX 3060, 12GB VRAM -- CUDA CONFIRMED)

CUDA is installed and working (user runs Ollama daily). XGBoost GPU is MANDATORY, not optional.

| Component | Method | Fallback |
|-----------|--------|----------|
| XGBoost training | `device='cuda'`, `tree_method='hist'` | **NONE -- fail fast if CUDA unavailable** |
| Data loading | pandas (sufficient for <200MB per coin) | N/A |
| KMeans | sklearn (399 coins = <5 sec) | N/A |
| SHAP | TreeExplainer (CPU, fast) | N/A |

### Realistic Time Estimates:
| Task | Estimate |
|------|----------|
| Backtester sweep (399 coins) | 10-30 min |
| Feature extraction | 2-5 min |
| XGBoost training (399 models) | 30-60 min |
| SHAP analysis (399 models) | 15-30 min |
| Walk-forward (5 folds x 399) | 1-2 hours |
| **Total full sweep** | **2-4 hours** |

---

## Stress Test: What Could Fail

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| State machine requires indicator columns not in OHLCV cache | HIGH | `enrich_ohlcv()` in strategy plugin computes ATR, stochastics, clouds from raw OHLCV |
| Some coins produce <20 trades (xgboost_trainer requires >=20) | MEDIUM | Skip coins with <20 trades, log warning, continue sweep |
| XGBoost CUDA not compiled | LOW (Ollama/CUDA active) | FAIL FAST -- no silent CPU fallback |
| purged_cv.py produces empty folds (small trade count) | MEDIUM | Reduce n_splits for coins with <100 trades |
| SHAP TreeExplainer crashes on edge cases | LOW | Wrap in try/except, log, skip SHAP for that coin |
| Grade filtering removes all trades | LOW | Check n_remaining > 20 before filtered model |
| Parquet files missing columns (older downloads) | MEDIUM | Validate required columns at load time, skip + log |

---

## Execution Order

### I write (while user is AFK):
```
1. Write scripts/build_docs_v1.py         [Section A]
2. py_compile check
3. Write scripts/build_data_infra_v1.py    [Section B]
4. py_compile check
5. Write scripts/build_train_vince_v1.py   [Sections 0+C+D]
6. py_compile + ast.parse check
7. Update MEMORY.md
8. Append session log to 06-CLAUDE-LOGS/
```

### User runs:
```powershell
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_docs_v1.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_data_infra_v1.py"
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_train_vince_v1.py"
# Single coin test:
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\train_vince.py" --symbol RIVERUSDT --timeframe 5m
# Full sweep (2-4 hours):
python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\train_vince.py" --symbol ALL --timeframe 5m
```

---

## Files Created This Session

### Build scripts (I write these directly):
- `scripts/build_docs_v1.py` -- Section A builder
- `scripts/build_data_infra_v1.py` -- Section B builder
- `scripts/build_train_vince_v1.py` -- Sections 0+C+D builder

### Generated by build scripts (user runs):
- `VERSION-MASTER.md` -- Section A
- `docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md` -- Section A
- `strategies/__init__.py` -- Section 0
- `strategies/base.py` -- Section 0 (StrategyPlugin interface)
- `strategies/four_pillars.py` -- Section 0 (first implementation)
- `ml/xgboost_trainer_v2.py` -- Section C
- `ml/features_v3.py` -- Section C
- `ml/shap_analyzer_v2.py` -- Section C
- `ml/bet_sizing_v2.py` -- Section C
- `scripts/train_vince.py` -- Section D

### Generated at runtime (user runs train_vince.py):
- `results/coin_tiers.csv` -- Section B
- `data/coin_pools.json` -- Section B
- `models/{strategy}/{symbol}_xgb_{ts}.json` -- Section D
- `models/{strategy}/{symbol}_report_{ts}.json` -- Section D
