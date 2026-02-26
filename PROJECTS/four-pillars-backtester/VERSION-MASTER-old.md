# VERSION-MASTER.md
**Generated:** 2026-02-18 12:45:32
**Source:** scripts/build_docs_v1.py

---

## Component Versions

| Component | Version | File | Status |
|-----------|---------|------|--------|
| Backtester Engine | v3.8.4 | engine/backtester_v384.py | STABLE |
| State Machine | v3.8.3 | signals/state_machine_v383.py | STABLE |
| Signal Pipeline | v3.8.3 | signals/four_pillars_v383.py | STABLE |
| Commission Model | v1.0 | engine/commission.py | STABLE |
| Dashboard | v3.9.1 | scripts/dashboard_v391.py | STABLE |
| Capital Model | v2.0 | utils/capital_model_v2.py | STABLE |
| PDF Exporter | v2.0 | utils/pdf_exporter_v2.py | STABLE |
| Stochastics | v1.0 | signals/stochastics.py | STABLE |
| Clouds | v1.0 | signals/clouds.py | STABLE |
| BBWP | v1.0 | signals/bbwp.py | STABLE |
| BBW Sequence | v1.0 | signals/bbw_sequence.py | STABLE |
| BBW Simulator | v1.0 | research/bbw_simulator.py | STABLE |
| BBW Monte Carlo | v1.0 | research/bbw_monte_carlo.py | STABLE |
| BBW Report | v1.0 | research/bbw_report.py | STABLE |
| Coin Classifier | v1.0 | research/coin_classifier.py | STABLE |
| Feature Extractor | v1.0 | ml/features.py | BUGS (see below) |
| Feature Extractor v2 | v2.0 | ml/features_v2.py | BUGS (see below) |
| Feature Extractor v3 | v3.0 | ml/features_v3.py | PLANNED |
| XGBoost Trainer | v1.0 | ml/xgboost_trainer.py | BUGS (see below) |
| XGBoost Trainer v2 | v2.0 | ml/xgboost_trainer_v2.py | PLANNED |
| SHAP Analyzer | v1.0 | ml/shap_analyzer.py | BUGS (see below) |
| SHAP Analyzer v2 | v2.0 | ml/shap_analyzer_v2.py | PLANNED |
| Bet Sizing | v1.0 | ml/bet_sizing.py | BUGS (see below) |
| Bet Sizing v2 | v2.0 | ml/bet_sizing_v2.py | PLANNED |
| Purged CV | v1.0 | ml/purged_cv.py | BUILT |
| Walk Forward | v1.0 | ml/walk_forward.py | BUILT |
| Coin Features | v1.0 | ml/coin_features.py | BUILT |
| Training Pipeline | v1.0 | ml/training_pipeline.py | BUILT |
| Triple Barrier | v1.0 | ml/triple_barrier.py | BUILT (Phase 2) |
| Meta Label | v1.0 | ml/meta_label.py | BUILT (Phase 2) |
| Loser Analysis | v1.0 | ml/loser_analysis.py | BUILT |
| Vince Model (PyTorch) | v1.0 | ml/vince_model.py | BUILT (Phase 2) |
| Strategy Plugin Base | v1.0 | strategies/base.py | PLANNED |
| Four Pillars Plugin | v1.0 | strategies/four_pillars.py | PLANNED |
| Train Vince CLI | v1.0 | scripts/train_vince.py | PLANNED |

---

## Known Bugs (v1 modules)

### ml/features.py + ml/features_v2.py
- **dt_series.iloc[i]** on DatetimeIndex: AttributeError (DatetimeIndex has no .iloc)
- **np.isnan() on int-dtype**: TypeError when cloud3_bull/price_pos are int64
- **get_feature_columns()**: missing duration_bars from returned list

### ml/xgboost_trainer.py
- **use_label_encoder=False**: removed in XGBoost >= 1.6, causes TypeError
- **mask indexing**: y[mask.values] can silently misalign if y is a misaligned Series
- **No GPU params**: missing device='cuda' and tree_method='hist'

### ml/shap_analyzer.py
- **No empty array guard**: shap_values on empty X crashes downstream
- **Binary SHAP version**: old shap returns list of two arrays, not handled

### ml/bet_sizing.py
- **Silent zero-return**: avg_loss=0 guard returns zeros with no warning

---

## Planned Versions

### v3 Feature Extractor (ml/features_v3.py)
- Fixes all 3 bugs from v1/v2
- 26 features from v2 + duration_bars = 27 feature columns
- Uses pd.isna() instead of np.isnan() for int-safe NaN checks
- dt_series always wrapped in pd.Series for .iloc compatibility

### v2 XGBoost Trainer (ml/xgboost_trainer_v2.py)
- GPU mandatory: device='cuda', tree_method='hist'
- Removed use_label_encoder
- Safe mask indexing with np.asarray()

### v2 SHAP Analyzer (ml/shap_analyzer_v2.py)
- Empty array guard on compute()
- Binary shap list-vs-array normalization

### v2 Bet Sizing (ml/bet_sizing_v2.py)
- Logging on guard triggers instead of silent zeros

### Strategy Plugin System (strategies/)
- Abstract base: strategies/base.py
- First implementation: strategies/four_pillars.py
- Model isolation: models/{strategy_name}/ per strategy

### Train Vince CLI (scripts/train_vince.py)
- 12-step pipeline: load -> enrich -> signals -> backtest -> features -> label -> filter -> validate -> train -> SHAP -> bet_sizing -> save
- Per-coin XGBoost auditors
- GPU mandatory (fail fast)
- Walk-forward + purged CV validation modes

---

## Data Infrastructure

| Asset | File | Records |
|-------|------|---------|
| Coin Tiers | results/coin_tiers.csv | 399 coins, KMeans 3-5 clusters |
| Coin Pools | data/coin_pools.json | 60/20/20 split (A/B/C), seed=42 |
| OHLCV Cache | data/cache/ | 399 coins, 1m+5m parquets |
| Period 2023-2024 | data/periods/2023-2024/ | 166 coins |
| Period 2024-2025 | data/periods/2024-2025/ | 257 coins |
| CoinGecko | data/coingecko/ | Market cap, categories |
