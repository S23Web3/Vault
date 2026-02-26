# Vince ML — Strategy Exposure Audit
**Date**: 2026-02-17
**Trigger**: User asked whether the Vince ML build exposes the Four Pillars strategy and is safe to share publicly.

---

## Audit Scope

Two codebase agents scanned:
- `signals/` — all indicator and state machine files
- `ml/` — all ML infrastructure files
- `scripts/build_staging.py` — staging build script

---

## Findings

### signals/ — PROPRIETARY (NOT SAFE TO SHARE)

| File | Contents |
|------|----------|
| `state_machine.py` | A/B/C/R grade entry logic, exact criteria per grade, long/short setup stages |
| `stochastics.py` | Kurisko Raw K settings: K1=9, K2=14, K3=40, K4=60, d_smooth=10 |
| `clouds.py` | Ripster EMA cloud parameters: Cloud2=5/12, Cloud3=34/50, Cloud4=72/89 |
| `four_pillars.py` | Full signal pipeline orchestrator |
| `four_pillars_v382.py` | v3.8.2 variant |
| `four_pillars_v383.py` | v3.8.3 variant |
| `state_machine_v382.py` | v3.8.2 A-bypass variant |
| `state_machine_v383.py` | v3.8.3 variant |
| `bbwp.py` | BBW Percentile indicator (Layer 1) |
| `bbw_sequence.py` | BBW sequence detection (Layer 2) |

**All 10 files expose complete strategy logic. Anyone with these files could fully replicate Four Pillars.**

---

### ml/ — GENERIC (SAFE TO SHARE)

| File | Contents |
|------|----------|
| `features.py` | Strategy-agnostic feature extraction from trade data + OHLCV |
| `features_v2.py` | Extended features (26 total), fully generic |
| `coin_features.py` | Market microstructure features (coin characteristics) |
| `triple_barrier.py` | Triple barrier labeling (De Prado Ch 3) |
| `meta_label.py` | Meta-labeling with XGBoost (De Prado Ch 3.6) |
| `shap_analyzer.py` | SHAP explainability framework |
| `purged_cv.py` | Purged cross-validation (De Prado) |
| `bet_sizing.py` | Kelly criterion + position sizing |
| `walk_forward.py` | Walk-forward analysis framework |
| `loser_analysis.py` | Trade loss analysis |
| `xgboost_trainer.py` | Generic XGBoost training wrapper |
| `vince_model.py` | PyTorch multi-task model (tabular + LSTM + context branches) |
| `training_pipeline.py` | Generic training orchestration |
| `xgboost_auditor.py` | Model audit framework |

**All 14 files are strategy-agnostic. They consume trade records and features but have zero hardcoded strategy logic. Could plug into any strategy.**

---

### Other Files — NOT SAFE

| File | Reason |
|------|--------|
| `scripts/build_staging.py` | Embeds exact stochastic settings, cloud parameters, A/B/C grade logic, rebate rates |
| `scripts/dashboard_v391.py` | Parameter UI reveals all indicator settings to anyone who reads the code |
| `scripts/dashboard.py` | Same — production dashboard with all parameters |

---

## Verdict

| Directory / File | Safe to Share? |
|-----------------|----------------|
| `ml/` (all 14 files) | YES — pure ML infrastructure |
| `signals/` (all 10 files) | NO — complete strategy exposure |
| `scripts/build_staging.py` | NO — embeds all parameters |
| `scripts/dashboard*.py` | NO — reveals parameter defaults |

---

## Recommendations

1. GitHub public repo: Only `ml/` is safe to open-source as-is.
2. If open-sourcing the backtester framework: replace `signals/` with a strategy interface/stub.
3. Strip all numeric defaults from dashboard before sharing.
4. Treat `signals/` and all dashboard files as confidential.
