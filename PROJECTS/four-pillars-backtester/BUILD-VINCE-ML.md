# VINCE ML Training Pipeline
**Build Specification for Four Pillars Backtester**
**Version:** 2.0
**Date:** 2026-02-17

**ARCHIVED** — This build spec covers the v1 classifier pipeline (XGBoost + PyTorch). The v2 concept (`docs/VINCE-V2-CONCEPT-v2.md`) replaces this approach. Do not build from this spec.

---

## Table of Contents

1. [Execution Overview](#execution-overview)
2. [P1: Deploy Staging](#p1-deploy-staging)
3. [P2+B2: XGBoost Training Pipeline](#p2b2-xgboost-training-pipeline)
4. [P4: 400-Coin ML Sweep](#p4-400-coin-ml-sweep)
5. [B3: PyTorch Trade Trajectory Network](#b3-pytorch-trade-trajectory-network)
6. [B4: Dashboard Integration](#b4-dashboard-integration)
7. [Directory Structure](#directory-structure)
8. [Run Sequence](#run-sequence)

---

## Execution Overview

### Build Order

| Phase | Component | Description |
|-------|-----------|-------------|
| **P1** | Deploy Staging | Move staging files to production (terminal only) |
| **P2+B2** | VINCE XGBoost | Complete training pipeline with grade filtering |
| **P4** | 400-Coin Sweep | Train models across all cached coins |
| **B3** | PyTorch TTN | Deep learning trajectory network |
| **B4** | Dashboard v2 | Integration of trained models into UI |

### Permissions Summary

- **WRITE:** New files in `scripts/`, `ml/pytorch/`, `models/`
- **READ:** Existing `ml/*.py`, `signals/`, `engine/`, `data/cache/`
- **VERSIONED EDIT:** `scripts/dashboard.py` → `scripts/dashboard_v2.py`
- **NO BASH:** User executes all commands from terminal

---

<div style="page-break-after: always;"></div>

## P1: Deploy Staging

**Purpose:** Move completed staging files into production directories  
**Execution:** User runs from PowerShell terminal  
**Duration:** <1 minute

### Commands

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Deploy files
Copy-Item staging\run_backtest.py scripts\run_backtest.py -Force
Copy-Item staging\test_dashboard_ml.py scripts\test_dashboard_ml.py -Force

# Create ml directory if needed
if (-not (Test-Path ml)) { New-Item -ItemType Directory -Path ml }
Copy-Item staging\ml\live_pipeline.py ml\live_pipeline.py -Force

# Verify imports
python -c "from ml.live_pipeline import LivePipeline; print('live_pipeline OK')"
python -c "from ml.xgboost_trainer import train_xgboost; print('xgboost_trainer OK')"
```

### Success Criteria

- [ ] Files copied without errors
- [ ] Import verification passes
- [ ] No staging/ directory references in production code

---

<div style="page-break-after: always;"></div>

## P2+B2: XGBoost Training Pipeline

### Required Reading

Before building, review these existing modules:

| Module | Purpose |
|--------|---------|
| `ml/features.py` | Feature extraction functions |
| `ml/triple_barrier.py` | Trade labeling logic |
| `ml/xgboost_trainer.py` | Core XGBoost wrapper |
| `ml/meta_label.py` | Alternative XGB interface |
| `ml/shap_analyzer.py` | Feature importance |
| `ml/purged_cv.py` | Cross-validation |
| `ml/walk_forward.py` | Walk-forward validation |
| `ml/bet_sizing.py` | Position sizing strategies |
| `ml/loser_analysis.py` | MFE/MAE analysis |

### NEW FILE: `scripts/train_vince.py`

Orchestrator connecting all ML modules into end-to-end pipeline.

#### Command-Line Interface

```bash
# Basic usage
python scripts/train_vince.py --symbol RIVERUSDT

# Walk-forward validation
python scripts/train_vince.py --symbol RIVERUSDT --walk-forward

# Grade filtering analysis
python scripts/train_vince.py --symbol RIVERUSDT --grade-filter D,R

# PnL-based labeling
python scripts/train_vince.py --symbol RIVERUSDT --label-mode pnl --draw-zone 0.5

# Sweep top 20 coins
python scripts/train_vince.py --symbol ALL --top 20
```

---

<div style="page-break-after: always;"></div>

### Pipeline Steps (Sequential)

#### 1. Load Data
- Use `load_cached()` pattern from `run_backtest_v384.py`
- Validate: minimum 1000 bars, no NaN in OHLC

#### 2. Generate Signals
- Import `compute_signals_v383()` (or v384)
- Run on OHLCV dataframe
- Output: `df_sig` with indicator columns

#### 3. Run Backtest
- Initialize `Backtester384(df_sig, params)`
- Parameters from CLI args:
  - `--sl-mult` (default 2.5)
  - `--tp-mult` (default None)
  - `--notional` (default 5000)
  - `--leverage` (default 20)
  - `--commission` (default 0.0008)
  - `--max-positions` (default 4)

#### 4. Extract Features
- Call `features.extract_trade_features(trades_df, df_sig)`
- Returns 14-column feature matrix
- Validate: no all-NaN columns, minimum 50 valid rows

#### 5. Label Trades
Two modes controlled by `--label-mode`:

**Exit Mode (default):**
```python
labels = triple_barrier.label_trades(trades_df)
# Mapping: TP(+1) → 1, SL(-1) → 0, other(0) → 0
```

**PnL Mode:**
```python
labels = triple_barrier.label_trades_by_pnl(trades_df, draw_zone)
# Mapping: win(+1) → 1, loss(-1) → 0, draw(0) → excluded
```

---

<div style="page-break-after: always;"></div>

#### 6. Grade Analysis (D+R Filtering)

When `--grade-filter` provided (e.g., "D,R"):

**Split Strategy:**
1. Separate trades into filtered grades vs remaining
2. Train two models independently
3. Compare performance metrics

**Output Analysis:**
- "Skipping all D trades saves $X, loses Y trades"
- "Skipping D trades where P(win) < 0.4 saves $X"
- Threshold sweep: 0.3, 0.4, 0.5, 0.6, 0.7

**Metrics Per Threshold:**
- Trades skipped
- P&L saved
- P&L lost
- Net impact

#### 7. Validation Strategy

**Walk-Forward Mode** (`--walk-forward` flag):
- Use `walk_forward.generate_windows()`
- Train on in-sample, predict on out-of-sample
- Calculate Walk Forward Efficiency (WFE)
- Rating: ROBUST / MARGINAL / OVERFIT

**Default Mode** (Purged Cross-Validation):
- 5-fold purged CV
- Print per-fold accuracy
- Report average ± standard deviation

#### 8. Train Final Model
```python
model = xgboost_trainer.train_xgboost(
    X, y, feature_names, test_size=0.3
)
```

**Output Metrics:**
- Accuracy, Precision, Recall, F1
- Positive prediction rate
- Feature importance (top 10)

---

<div style="page-break-after: always;"></div>

#### 9. SHAP Analysis
- Generate SHAP values for feature explanations
- Output top 10 features with directionality:
  - Positive = "take trade"
  - Negative = "skip trade"

#### 10. Bet Sizing Simulation

Test multiple threshold strategies:

| Threshold | Trades Taken | Trades Skipped | Simulated P&L |
|-----------|--------------|----------------|---------------|
| 0.4 | 1500 | 400 | $8,200 |
| 0.5 | 1200 | 700 | $8,500 |
| 0.6 | 900 | 1000 | $7,800 |
| 0.7 | 600 | 1300 | $6,400 |

Include Kelly sizing calculation using `avg_win/avg_loss` from trades.

#### 11. Save Model + Report

**Model File:** `models/{symbol}_xgb_{timestamp}.json`

**Report File:** `models/{symbol}_report_{timestamp}.json`

**Report Contents:**
```json
{
  "symbol": "RIVERUSDT",
  "timeframe": "5m",
  "params": {"sl_mult": 2.5, "notional": 5000, ...},
  "n_trades": 1901,
  "n_features": 14,
  "label_mode": "exit",
  "label_distribution": {"take": 820, "skip": 1081},
  "cv_metrics": {"fold_1_acc": 0.89, ...},
  "wfe_metrics": {"wfe": 0.68, "rating": "ROBUST"},
  "test_metrics": {"accuracy": 0.914, ...},
  "feature_importance": [...],
  "shap_values": [...],
  "grade_analysis": {...},
  "bet_sizing_sim": {...}
}
```

---

<div style="page-break-after: always;"></div>

#### 12. Summary Output

One-line summary format:
```
RIVERUSDT: 1901 trades, XGB acc=91.4%, WFE=0.68 ROBUST,
top features: [stoch_60, duration_bars, atr_pct],
D-grade skip@0.5: saves $2,100 (skips 340 trades)
```

### Complete CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--symbol` | **REQUIRED** | Symbol name or "ALL" |
| `--timeframe` | "5m" | Bar timeframe |
| `--sl-mult` | 2.5 | Stop-loss ATR multiplier |
| `--tp-mult` | None | Take-profit ATR multiplier |
| `--notional` | 5000 | Position size |
| `--leverage` | 20 | Leverage multiplier |
| `--commission` | 0.0008 | Commission rate |
| `--max-positions` | 4 | Concurrent positions |
| `--label-mode` | "exit" | "exit" or "pnl" |
| `--draw-zone` | 0.0 | Draw zone for pnl mode |
| `--grade-filter` | None | Comma-separated grades |
| `--walk-forward` | False | Use WF validation |
| `--top` | None | Limit coins (ALL mode) |
| `--output-dir` | "models/" | Output directory |
| `--verbose` | False | Print detailed logs |

---

<div style="page-break-after: always;"></div>

### NEW FILE: `scripts/test_train_vince.py`

Test suite validating training pipeline without full backtest.

**Test Coverage:**

1. Import all ML modules
2. Load cached coin (RIVERUSDT)
3. Generate signals
4. Run backtest (first 5000 bars for speed)
5. Extract features (validate shape)
6. Label trades (both modes)
7. Train XGBoost on subset
8. SHAP analysis
9. Save/load model roundtrip
10. Grade filter analysis
11. Bet sizing simulation

**Success Criteria:** All 11 tests pass in <2 minutes

---

<div style="page-break-after: always;"></div>

## P4: 400-Coin ML Sweep

**Purpose:** Train per-coin XGBoost models across all cached data  
**Execution:** Single command with `--symbol ALL`  
**Duration:** ~6-8 hours (400 coins)

### Command

```powershell
python scripts/train_vince.py --symbol ALL --grade-filter D,R --verbose
```

### ALL Mode Logic

```
1. Scan data/cache/ for all *_5m.parquet files
2. Sort by file size descending (proxy for trade count)
3. If --top N specified: take first N symbols
4. For each symbol:
   - Run full pipeline (steps 1-12)
   - Catch errors per-coin, continue to next
   - Collect summary row
5. After all coins:
   - Print summary table
   - Save models/sweep_summary_{timestamp}.csv
   - Print: "Sweep complete: X/Y coins trained, Z errors"
```

### Output Files

- `models/{symbol}_xgb_{timestamp}.json` (one per coin)
- `models/{symbol}_report_{timestamp}.json` (one per coin)
- `models/sweep_summary_{timestamp}.csv` (aggregate results)

### Summary Table Format

| Symbol | Trades | Accuracy | WFE | Top Feature | D-Skip Savings |
|--------|--------|----------|-----|-------------|----------------|
| RIVERUSDT | 1901 | 91.4% | 0.68 | stoch_60 | $2,100 |
| CELOUSDT | 2340 | 88.2% | 0.55 | duration_bars | $1,850 |
| ... | ... | ... | ... | ... | ... |

---

<div style="page-break-after: always;"></div>

## B3: PyTorch Trade Trajectory Network

### Prerequisites

**Verify PyTorch Installation:**
```powershell
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

Expected output:
```
PyTorch 2.x.x, CUDA: True
Device: NVIDIA GeForce RTX 3060
```

### Architecture Overview

Three-branch neural network with multi-task learning:

1. **Branch 1:** Pre-Entry Context (50 bars before trade)
2. **Branch 2:** Trade Trajectory (up to 200 bars during trade)
3. **Branch 3:** Static Features (14 engineered features)

**Fusion Layer:** Combines all branches → 4 output heads

**Output Heads:**
- Exit Quality (binary classification)
- Remaining Favorable Excursion (regression)
- Market Regime (3-class classification)
- Optimal Stop-Loss (regression)

---

<div style="page-break-after: always;"></div>

### NEW DIRECTORY: `ml/pytorch/`

Seven files implementing complete PyTorch pipeline.

#### 1. `ml/pytorch/__init__.py`
Empty initialization file.

#### 2. `ml/pytorch/config.py`

Hyperparameters and paths:

```python
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Sequence lengths
SEQ_LEN_PRE = 50      # bars before entry
SEQ_LEN_TRADE = 200   # max bars during trade

# Features
OHLCV_FEATURES = 8    # OHLC, volume, ATR, stoch, cloud
TRADE_FEATURES = 10   # OHLCV + unrealized_pnl + bars_held
STATIC_FEATURES = 14  # from features.py

# Model architecture
HIDDEN_DIM = 128
FUSION_DIM = 160      # 64 + 64 + 32
DROPOUT = 0.3

# Training
BATCH_SIZE = 512
LR = 0.001
EPOCHS = 100
EARLY_STOP_PATIENCE = 10

# Paths
MODEL_DIR = "models/pytorch/"
LOG_DIR = "logs/pytorch/"
CHECKPOINT_EVERY = 10  # epochs
```

---

<div style="page-break-after: always;"></div>

#### 3. `ml/pytorch/feature_eng.py`

Sequence feature construction from OHLCV and signals.

**Key Functions:**

**`extract_pre_entry_sequence(ohlcv_df, entry_bar, seq_len=50)`**
- Extract 50 bars ending at entry
- Columns: open, high, low, close, volume, ATR, stoch_9, cloud3_bull
- Normalization: per-sequence z-score on prices
- Volume: log1p transform
- Left-pad with zeros if insufficient history
- Returns: tensor (50, 8), mask tensor (50,)

**`extract_trade_sequence(ohlcv_df, trade_row, max_len=200)`**
- Extract bars from entry to exit
- Additional features: unrealized_pnl, bars_held
- Truncate if >200 bars, right-pad if shorter
- Returns: tensor (200, 10), mask (200,), actual_length

**`extract_static_features(trade_row, ohlcv_df)`**
- Uses existing `features.extract_trade_features()`
- Returns: tensor (14,)

**`build_labels(trade_row)`**

Returns dictionary:
```python
{
  "exit_quality": 1 if exit_reason=="TP" else 0,
  "rfe": (mfe - max(net_pnl, 0)) / sl_distance,
  "regime": 0=trending, 1=ranging, 2=volatile,
  "optimal_sl": mae / atr_at_entry
}
```

---

<div style="page-break-after: always;"></div>

#### 4. `ml/pytorch/dataset.py`

**TradeDataset** (torch.utils.data.Dataset)

Handles data loading and batching for PyTorch training.

**Key Features:**
- Time-based split (70% train, 30% validation)
- Pre-computes all sequences and labels
- Handles variable-length sequences with padding/masks

**`__getitem__(self, idx)` returns:**
```python
{
  "pre_entry_seq": (50, 8),
  "pre_entry_mask": (50,),
  "trade_seq": (200, 10),
  "trade_mask": (200,),
  "trade_actual_len": int,
  "static_features": (14,),
  "labels": {exit_quality, rfe, regime, optimal_sl}
}
```

**TradeDatasetBuilder**

Helper class for dataset construction:

**`build_from_backtest(symbol, timeframe, params, config)`**
- Load → signals → backtest → dataset
- Single-coin pipeline

**`build_multi_coin(symbols, timeframe, params, config)`**
- Concatenate multiple coins
- Maintain time order within each coin

---

<div style="page-break-after: always;"></div>

#### 5. `ml/pytorch/model.py`

**TradeTrajectoryNetwork** (nn.Module)

Three-branch architecture with multi-task heads.

**Architecture Summary:**

```
Branch 1: Pre-Entry LSTM
  Input: (batch, 50, 8)
  LSTM: 2 layers, hidden_dim=128, bidirectional=False
  Output: (batch, 64)

Branch 2: Trade LSTM
  Input: (batch, 200, 10)
  LSTM: 2 layers, hidden_dim=128, bidirectional=False
  Output: (batch, 64)

Branch 3: Static MLP
  Input: (batch, 14)
  MLP: 14 → 64 → 32 (ReLU, Dropout)
  Output: (batch, 32)

Fusion Layer
  Input: concat(64, 64, 32) = (batch, 160)
  MLP: 160 → 128 → 64 (ReLU, Dropout)
  Output: (batch, 64)

Output Heads
  exit_quality: Linear(64, 1) + Sigmoid
  rfe: Linear(64, 1)
  regime: Linear(64, 3) + Softmax
  optimal_sl: Linear(64, 1)
```

---

<div style="page-break-after: always;"></div>

#### 6. `ml/pytorch/trainer.py`

**VinceTrainer**

Handles training loop, validation, and checkpointing.

**Multi-Task Loss Function:**

```python
loss_weights = {
  "exit_quality": 1.0,   # Binary Cross-Entropy
  "rfe": 0.5,            # Mean Squared Error
  "regime": 0.3,         # Cross-Entropy
  "optimal_sl": 0.3      # Mean Squared Error
}

total_loss = sum(weight * task_loss 
                 for weight, task_loss in zip(weights, losses))
```

**Key Methods:**

- `train_epoch(train_loader)` - Training pass
- `validate_epoch(val_loader)` - Validation pass with metrics
- `fit(train_dataset, val_dataset, epochs)` - Full training loop
- `save_checkpoint(path, epoch, val_loss)` - Save model state
- `load_checkpoint(path)` - Restore model state

**Features:**
- Early stopping (patience=10 epochs)
- Learning rate scheduling (ReduceLROnPlateau)
- Per-head metric tracking
- Training history JSON export

---

<div style="page-break-after: always;"></div>

#### 7. `ml/pytorch/inference.py`

**VinceInference**

Production inference for trained models.

**Key Methods:**

**`predict_single(pre_entry_seq, trade_seq, static_features)`**
- Single trade prediction
- Returns probabilities/values for all 4 heads

**`predict_batch(dataset)`**
- Batch prediction for analysis
- Returns DataFrame aligned to trades

**`mc_dropout_predict(..., n_samples=50)`**
- Monte Carlo Dropout for uncertainty estimation
- Run forward pass 50 times with dropout enabled
- Returns: mean predictions + standard deviation
- High std = model uncertainty

**`compare_vs_xgboost(xgb_model_path, dataset)`**
- Load XGBoost model
- Predict on same trades
- Compare metrics
- Identify disagreements (ensemble candidates)

#### 8. `ml/pytorch/evaluate.py`

Model evaluation and visualization.

**`evaluate_model(model, val_dataset, device)`**

Per-head metrics:
- Exit quality: accuracy, precision, recall, F1, AUC-ROC
- RFE: MAE, RMSE, R-squared
- Regime: confusion matrix, per-class accuracy
- Optimal SL: MAE vs actual SL

**`plot_training_curves(history_path, output_path)`**
- Loss curves (train/val)
- Per-head loss curves
- Learning rate schedule

**`compare_coins(model, symbols, config)`**
- Cross-coin performance analysis
- Gradient attribution for feature importance

---

<div style="page-break-after: always;"></div>

### NEW FILE: `scripts/train_vince_pytorch.py`

PyTorch training orchestrator.

**Usage Examples:**

```bash
# Train single coin
python scripts/train_vince_pytorch.py --symbol RIVERUSDT

# Custom hyperparameters
python scripts/train_vince_pytorch.py --symbol RIVERUSDT \
  --epochs 100 --batch-size 512 --lr 0.001

# Compare with XGBoost
python scripts/train_vince_pytorch.py --symbol RIVERUSDT --compare-xgb

# Resume from checkpoint
python scripts/train_vince_pytorch.py --resume models/pytorch/checkpoint_epoch50.pt

# Multi-coin sweep
python scripts/train_vince_pytorch.py --symbol ALL --top 20
```

**CLI Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `--symbol` | **REQUIRED** | Symbol or "ALL" |
| `--timeframe` | "5m" | Bar timeframe |
| `--epochs` | 100 | Training epochs |
| `--batch-size` | 512 | Batch size |
| `--lr` | 0.001 | Learning rate |
| `--device` | "auto" | cuda/cpu |
| `--checkpoint` | "models/pytorch/" | Checkpoint directory |
| `--compare-xgb` | False | XGBoost comparison |
| `--resume` | None | Resume from checkpoint |
| `--top` | None | Limit coins (ALL mode) |
| `--verbose` | False | Detailed logging |

---

<div style="page-break-after: always;"></div>

**Pipeline Steps:**

1. Load data (same as XGBoost pipeline)
2. Build TradeDataset with feature engineering
3. Time-based train/val split (70/30)
4. Initialize model from config
5. Train using VinceTrainer
6. Evaluate with per-head metrics
7. Save model + report to `models/pytorch/`
8. Optional: Compare with XGBoost
9. Print summary

**Output Files:**
- `models/pytorch/{symbol}_checkpoint_{timestamp}.pt`
- `models/pytorch/{symbol}_report_{timestamp}.json`

### NEW FILE: `scripts/test_pytorch_pipeline.py`

Test suite for PyTorch pipeline.

**Test Coverage:**

1. Verify CUDA detection
2. Import all `ml/pytorch/` modules
3. Feature extraction with dummy data
4. Dataset construction and `__getitem__`
5. Model forward pass
6. Training step (loss decreases)
7. Save/load roundtrip
8. Config validation

**Success Criteria:** All 8 tests pass in <30 seconds

---

<div style="page-break-after: always;"></div>

## B4: Dashboard Integration

### VERSIONED EDIT: `scripts/dashboard_v2.py`

Copy of existing dashboard with two major additions.

#### Tab 4 Changes: Wire Trained XGBoost

**Current State:** Trains model in-session (ephemeral)

**New Features:**

**Model Loading:**
```
[Load Model] button → file picker (models/*.json)
OR
[Train New] → in-session training (existing behavior)
```

**When Model Loaded:**

1. **Metadata Display:**
   - Symbol, training date
   - Accuracy, WFE rating
   - Feature count

2. **Prediction Distribution:**
   - Probability histogram
   - Interactive threshold slider (0.3 to 0.8)

3. **Performance Comparison Table:**

| Metric | All Trades | Filtered (>thresh) | Skipped (<thresh) |
|--------|------------|-------------------|-------------------|
| Trades | 1901 | 1200 | 701 |
| Net P&L | $6,261 | $8,100 | -$1,839 |
| Win Rate | 43% | 58% | 18% |
| Avg $/trade | $3.29 | $6.75 | -$2.62 |

4. **Grade Breakdown:**
   - Distribution of skipped trades by grade
   - "Skipped: 420 D-grade, 180 R-grade, 101 other"

5. **SHAP Waterfall Plot:**
   - Top 10 features
   - Force plot for feature contributions

---

<div style="page-break-after: always;"></div>

#### NEW Tab 6: PyTorch Analysis

Complete deep learning analysis interface.

**Model Loading:**
```
[Load Model] button → file picker (models/pytorch/*.pt)
```

**When Model Loaded:**

**Metadata Section:**
- Architecture details
- Training epochs, validation loss
- Device (CUDA/CPU)

**6a. Exit Quality Prediction**

- Probability distribution histogram
- Calibration curve (predicted vs actual)
- Threshold analysis table

**6b. Remaining Favorable Excursion**

- Scatter plot: predicted vs actual RFE
- R-squared metric
- Highlight: trades with RFE > 1.0R

**6c. Regime Classification**

Per-regime performance breakdown:

| Regime | Trades | Win Rate | Net P&L | Avg $/trade |
|--------|--------|----------|---------|-------------|
| Trending | 600 | 52% | $5,000 | $8.33 |
| Ranging | 800 | 38% | $1,000 | $1.25 |
| Volatile | 500 | 40% | $200 | $0.40 |

**6d. Optimal SL Analysis**

- Scatter: predicted vs actual SL (ATR units)
- Distribution: too wide / right / too tight
- Simulated P&L with optimal SL

---

<div style="page-break-after: always;"></div>

**6e. XGBoost vs PyTorch Comparison**

When both models available:

- Side-by-side metrics table
- Disagreement analysis
- Ensemble performance (averaged predictions)

**6f. Uncertainty (MC Dropout)**

- Prediction uncertainty distribution
- High-uncertainty trades visualization
- Filter: "skip trades where uncertainty > threshold"

---

<div style="page-break-after: always;"></div>

## Directory Structure

Final file structure after all builds complete:

```
four-pillars-backtester/
├── models/                             ← NEW
│   ├── .gitkeep
│   ├── {symbol}_xgb_{ts}.json         ← XGBoost models
│   ├── {symbol}_report_{ts}.json      ← Training reports
│   ├── sweep_summary_{ts}.csv         ← Sweep results
│   └── pytorch/                        ← NEW
│       ├── checkpoint_{symbol}_{ts}.pt
│       └── {symbol}_report_{ts}.json
│
├── ml/
│   ├── features.py                     (existing)
│   ├── triple_barrier.py               (existing)
│   ├── xgboost_trainer.py              (existing)
│   ├── meta_label.py                   (existing)
│   ├── shap_analyzer.py                (existing)
│   ├── purged_cv.py                    (existing)
│   ├── walk_forward.py                 (existing)
│   ├── bet_sizing.py                   (existing)
│   ├── loser_analysis.py               (existing)
│   └── pytorch/                        ← NEW
│       ├── __init__.py
│       ├── config.py
│       ├── feature_eng.py
│       ├── dataset.py
│       ├── model.py
│       ├── trainer.py
│       ├── inference.py
│       └── evaluate.py
│
└── scripts/
    ├── train_vince.py                  ← NEW
    ├── test_train_vince.py             ← NEW
    ├── train_vince_pytorch.py          ← NEW
    ├── test_pytorch_pipeline.py        ← NEW
    ├── dashboard_v2.py                 ← NEW
    └── (all existing scripts unchanged)
```

---

<div style="page-break-after: always;"></div>

## Run Sequence

Complete execution order for user terminal.

### Phase 1: Deploy Staging

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

# Deploy files
Copy-Item staging\run_backtest.py scripts\run_backtest.py -Force
Copy-Item staging\ml\live_pipeline.py ml\live_pipeline.py -Force
```

### Phase 2: XGBoost Pipeline

```powershell
# Test pipeline
python scripts/test_train_vince.py

# Train single coin with validation
python scripts/train_vince.py --symbol RIVERUSDT \
  --grade-filter D,R --walk-forward --verbose

# 400-coin sweep
python scripts/train_vince.py --symbol ALL --grade-filter D,R
```

### Phase 3: PyTorch Pipeline

```powershell
# Test pipeline
python scripts/test_pytorch_pipeline.py

# Train with XGBoost comparison
python scripts/train_vince_pytorch.py --symbol RIVERUSDT \
  --compare-xgb --verbose
```

### Phase 4: Launch Dashboard

```powershell
streamlit run scripts/dashboard_v2.py
```

---

## Appendix: Success Criteria

### P1 Success
- [ ] Files deployed without errors
- [ ] Imports verified successfully

### P2+B2 Success
- [ ] All tests pass in `test_train_vince.py`
- [ ] Single coin training completes without errors
- [ ] Model and report files saved
- [ ] SHAP analysis generates successfully

### P4 Success
- [ ] Sweep completes for all coins
- [ ] Summary CSV generated
- [ ] <5% error rate across coins

### B3 Success
- [ ] All tests pass in `test_pytorch_pipeline.py`
- [ ] Training converges (validation loss decreases)
- [ ] Checkpoint files saved
- [ ] Per-head metrics reasonable

### B4 Success
- [ ] Dashboard launches without errors
- [ ] Tab 4 loads XGBoost models
- [ ] Tab 6 loads PyTorch models
- [ ] All visualizations render correctly

---

**END OF BUILD SPECIFICATION**
