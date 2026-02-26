# SPEC C: VINCE ML Architecture -- Unified Model + Training Infrastructure

**Version:** P2/P4 from pending builds
**Date:** 2026-02-13
**Depends on:** Spec B (backtester v385 produces the training data)
**Feeds:** Spec A Dashboard Tabs 3/4 become functional
**Output files:** `ml/vince_model.py`, `ml/coin_features.py`, `ml/training_pipeline.py`, `ml/xgboost_auditor.py`
**Test script:** `scripts/test_vince_ml.py`
**Review:** `DASHBOARD-V3-BUILD-SPEC-REVIEW.md`

---

## PURPOSE

Build VINCE's unified ML model that predicts trade outcomes using entry-state features, indicator lifecycle patterns, and coin characteristics. This is the intelligence layer that turns backtester data into actionable trade filters.

**Design principle:** One model, one framework, one truth. XGBoost serves as validation auditor, not production model.

---

## PART 1: COIN CHARACTERISTICS -- FEATURE ENGINEERING

**Problem:** The sweep shows WHICH coins performed well, but not WHY. VINCE needs to learn what characteristics predict a good trading coin so it can identify future candidates -- not just backtest historical winners.

**Principle:** VINCE must NEVER see backtest results during training. Characteristics are inputs. Results are labels. Training set and test set must be completely separate coin pools (no data leakage).

### Features to Compute Per Coin (from OHLCV data only):

| Feature | Calculation | Why It Matters |
|---------|-------------|----------------|
| avg_daily_volume | mean(daily quote volume) | Liquidity -- can we fill orders? |
| volume_stability | std(daily_vol) / mean(daily_vol) | Erratic volume = slippage risk |
| avg_spread_proxy | mean((high-low)/close) per bar | Tighter spread = better fills |
| volatility_regime | std(returns) annualized | Strategy needs volatility to profit |
| drift_noise_ratio | abs(close[-1] - close[0]) / std(close) | Net drift vs noise -- high = trending, low = ranging |
| mean_reversion_score | autocorrelation of returns at lag 1 | Negative = mean-reverting |
| volume_mcap_ratio | avg_volume / market_cap (if available) | High ratio = active trading interest |
| bar_count | total bars in dataset | Data sufficiency |
| gap_pct | (bars with volume=0) / total bars | Dead zones = illiquid |
| price_range | (max_price - min_price) / min_price | How much the coin moved overall |

**Implementation:** `ml/coin_features.py` -- takes OHLCV DataFrame, returns dict of 10 features. Cached per coin (computed once from raw data before backtest).

**Note:** `volume_mcap_ratio` requires external API for market cap. Flag as optional -- omit from v1, add when API available.

---

## PART 2: UNIFIED PYTORCH MODEL

**Why unified:**
- Two models can disagree -- needs arbitration layer -- more complexity, more failure points
- Separate models see partial data (XGBoost sees entry snapshot, LSTM sees sequences). A unified model sees the FULL picture: entry conditions + indicator evolution + trade lifecycle in a single forward pass.
- One training pipeline, one deployment path, one endpoint for n8n live integration.
- One set of gradients, one loss function, one optimization target.

### Architecture: VINCE Unified Model

```
INPUT LAYER
|-- Tabular branch: entry-state features (11 fields from Spec B) + lifecycle summary (14 fields)
|   -> Embedding layer for categoricals (grade, stoch9_direction, pnl_path)
|   -> Linear layers for numerics (stoch values, AVWAP dist, ATR, vol_ratio)
|   -> Output: 64-dim entry representation
|
|-- Sequence branch: per-bar indicator evolution (Layer 2 data)
|   -> Input: [bars x 15 features] per trade
|   -> LSTM or Transformer encoder
|   -> Output: 64-dim lifecycle representation
|
|-- Context branch: coin characteristics (10 fields from Part 1)
|   -> Linear layers
|   -> Output: 32-dim coin context
|
FUSION LAYER
|   -> Concatenate: [entry_repr | lifecycle_repr | coin_context] = 160-dim
|   -> Dense layers with dropout
|
OUTPUT LAYER
|   -> Primary: win probability (0-1)
|   -> Secondary: predicted P&L path (direct/green_then_red/red_then_green/choppy)
|   -> Tertiary: optimal exit bar estimate
```

### Training Data Sources:

| Source | Spec | Content |
|--------|------|---------|
| Per-trade parquet (Layer 1) | Spec B | Entry features + lifecycle summary + labels |
| Per-bar parquet (Layer 2) | This spec | Indicator sequences per trade |
| Coin characteristics | This spec | OHLCV-derived features per coin |
| Sweep CSV | Spec A | Coin-level performance labels |

### Hardware:
- RTX 3060 12GB
- PyTorch 2.10.0+cu130
- CUDA available

---

## PART 3: PHASED BUILD

### Phase 1: Tabular Only (entry features + lifecycle summary)

Train on entry-state (14 fields) + lifecycle summary (15 fields) from Layer 1 parquet. No sequence data. Validates data pipeline and feature signal.

- **Input:** 25 features per trade (11 entry-state + 14 lifecycle, tabular branch only, no sequence branch)
- **Label:** win/loss binary, P&L path classification
- **Training time:** Minutes on RTX 3060
- **Purpose:** Baseline accuracy. If entry features alone can predict at >55% accuracy, the signal is real.

### Phase 2: Add Sequences (LSTM/Transformer branch)

Add per-bar indicator evolution data. LSTM branch consumes variable-length sequences.

- **Input:** 25 tabular features + [bars x 15] sequence per trade
- **Requires:** Layer 2 per-bar parquet data (Part 5)
- **Training time:** Hours on RTX 3060
- **Purpose:** Learn indicator evolution patterns that tabular summary misses. Should beat Phase 1 accuracy.

### Phase 3: Live Integration

Model runs on live trades via n8n webhook.
- Entry features scored at signal time (reject low-probability trades)
- Sequence branch updates per bar while trade is open
- Adaptive exit signal based on lifecycle pattern recognition

---

## PART 4: XGBOOST VALIDATION AUDITOR

**Role:** Validation/auditor model. Trains on the same data, same features, independently. NOT a production model -- it never makes live decisions.

**Purpose:**
1. **Cross-validate feature importance:** If PyTorch (via Captum) and XGBoost (via SHAP) agree on which features matter, confidence is high
2. **Flag disagreements:** If PyTorch says "AVWAP distance is #1" but XGBoost says "irrelevant", something is wrong -- investigate before deploying either
3. **Baseline comparison:** XGBoost accuracy on tabular features sets the floor. PyTorch with sequences should beat it. If it doesn't, the sequence data isn't adding value.
4. **Runs overnight** alongside PyTorch training. Training speed difference is irrelevant.

**Implementation:** `ml/xgboost_auditor.py` -- uses existing `ml/xgboost_trainer.py` infrastructure. Trains on same train/val split. Outputs SHAP waterfall plots.

### Interpretability Stack:

| Tool | Model | Output |
|------|-------|--------|
| Captum | PyTorch | Feature attribution per prediction |
| Attention weights | Transformer (if used) | Which bars mattered most in sequence |
| SHAP waterfall | XGBoost | Feature importance rankings |

**Agreement metric:** % of top-10 features that appear in both models' top-10 lists. If agreement < 70%, flag for manual review before any deployment.

### Dashboard Tab 3 (when functional):
- Side-by-side comparison panel showing both models' feature rankings
- Agreement score displayed prominently
- Drill-down into disagreements

---

## PART 5: PER-BAR LAYER 2 STORAGE (on-demand)

**Path:** `results/bars_{symbol}_{timeframe}.parquet`
**Schema:** One row per bar per open trade (only bars where a position is open)

**Columns (15 per bar):**
```
trade_id, bar_index, timestamp, unrealized_pnl,
mfe_so_far, mae_so_far,
stoch9, stoch14, stoch40, stoch60, stoch60_d,
ripster_cloud_width, ripster_expanding,
avwap_distance, atr, vol_ratio
```

**DEFERRED:** `bbwp` column added after Python BBWP port (raises to 16 columns).

**Size estimate:**
- avg 15 bars/trade x 7K trades/coin x 400 coins x 15 columns = ~630M rows
- At ~90 bytes/row compressed parquet = ~54GB total
- Per-coin files: ~135MB each

**Generation:** Only on demand via `--save-bars` flag. NOT generated during normal sweep or backtest runs. This is for Phase 2 LSTM training only.

**Mitigation for size:**
- Per-coin files (not one giant file)
- Compressed parquet (snappy or zstd)
- Only generate for training pool coins (60% of 400 = 240 coins = ~36GB)
- Can delete after training (model is the artifact, not the data)

---

## PART 6: VINCE BLIND TRAINING PROTOCOL

**Critical design decision:** VINCE trains on a random subset of coins. The holdout set is NEVER seen during training. This prevents memorization of coin-specific patterns.

### Pool Split:

| Pool | % | Coins | Purpose |
|------|---|-------|---------|
| A: Training | 60% | ~240 | VINCE sees characteristics + results |
| B: Validation | 20% | ~80 | VINCE predicts, then checks |
| C: Holdout | 20% | ~80 | Never touched until final evaluation |

### Rules:
1. Pool assignment is RANDOM, seeded for reproducibility
2. Pool C coins are NEVER used in training or validation
3. If a coin is added to the universe later, it goes to Pool C first
4. Pool assignment stored in `data/coin_pools.json`
5. Dashboard Tab 3 shows pool membership (so user knows which coins are blind)

### Training Flow:
1. Compute coin characteristics for ALL coins (no leakage -- OHLCV only)
2. Run v385 backtester on ALL coins (generates per-trade parquet)
3. Train unified model on Pool A trades only
4. Validate on Pool B trades
5. Final evaluation on Pool C trades (once, at the end)
6. If Pool C accuracy < Pool B accuracy by >5%, model is overfit -- retrain

### What VINCE Learns:
"Coins with `volatility_regime > X` and `volume_stability < Y` tend to have `Calmar > Z`"
"Trades entered with `stoch9 < 30` and `ripster_expanding = True` win 68% vs 42% otherwise"

### Output:
VINCE can score NEW coins (not in the 400) on likelihood of edge, using only OHLCV characteristics before any backtest runs.

---

## DASHBOARD INTEGRATION (Tabs 3/4)

### Tab 3 (Optimizer/VINCE) -- when functional:
- Feature importance rankings (Captum + SHAP side-by-side)
- Agreement score between PyTorch and XGBoost
- Per-trade prediction browser (sort by confidence, filter by outcome)
- Research findings panel: surfaces indicator conditions that are statistically associated
  with losing trades (e.g. "stoch9 > 70 AND ripster_expanding = False appeared in 34% of
  losers vs 12% of winners"). Informational only — no trade is rejected by Vince. The user
  reads the finding and decides what to do with it. Trade count is never reduced by this
  output. (TAKE/SKIP decisions are Vicky's domain — separate build.)

### Tab 4 (Validation) -- when functional:
- Pool B validation accuracy
- Pool C holdout results (revealed once)
- Walk-Forward Efficiency score
- Monte Carlo distribution of outcomes
- Confidence grade: HIGH / MEDIUM / LOW / REJECT

---

## FILES TO CREATE

| File | Purpose |
|------|---------|
| `ml/coin_features.py` | Compute 10 OHLCV-derived characteristics per coin |
| `ml/vince_model.py` | Unified PyTorch model (tabular + sequence + context) |
| `ml/training_pipeline.py` | Orchestrates data loading, pool split, training, validation |
| `ml/xgboost_auditor.py` | XGBoost validation model + SHAP comparison |
| `data/coin_pools.json` | Pool assignment (A/B/C per coin, seeded random) |
| `scripts/test_vince_ml.py` | End-to-end test of training pipeline |

---

## VERIFICATION CHECKLIST

- [ ] Coin characteristics computed for all cached coins
- [ ] Per-trade parquet files readable by training pipeline
- [ ] Pool split is deterministic (same seed = same split)
- [ ] Pool C coins never appear in training data
- [ ] Phase 1 model trains and produces predictions
- [ ] XGBoost auditor trains on same data
- [ ] Feature importance agreement metric computed
- [ ] SHAP waterfall plots generated
- [ ] Captum attributions generated
- [ ] Phase 1 accuracy > 55% (signal exists)
- [ ] Phase 2 accuracy > Phase 1 (sequences add value)
- [ ] Pool C accuracy within 5% of Pool B (no overfit)

---

## RISKS

| Risk | Mitigation |
|------|-----------|
| 60GB Layer 2 data | On-demand only, per-coin files, delete after training |
| Training time | Phase 1: minutes. Phase 2: hours. Overnight batch. |
| Overfit to training coins | Pool C holdout, 5% accuracy gap threshold |
| PyTorch/XGBoost disagree | Flag for manual review, don't deploy until resolved |
| Sequence branch adds no value | Phase 1 baseline comparison. If sequences don't beat it, skip. |
| CUDA OOM on 12GB | Batch size tuning, gradient accumulation, mixed precision |
| Market cap API needed for volume_mcap_ratio | Flag as optional, omit from v1 |

---

## DEPENDENCY CHAIN

```
Spec A (Dashboard v3) -- standalone, ships now
    |
    v
Spec B (Backtester v385) -- produces per-trade parquet with entry-state + lifecycle
    |
    v
THIS SPEC (VINCE ML) -- consumes parquet, trains model, feeds Dashboard Tabs 3/4
```

Spec A and B can ship independently. This spec requires Spec B's per-trade parquet output as training data.
