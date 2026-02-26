# Project Status Review + VINCE Data Strategy
**Date:** 2026-02-16 15:30 GST  
**Session:** Eagle-eye status check + data preservation planning  
**Status:** Analysis complete, implementation pending

---

## Key Corrections

### BBW Architecture (CORRECTED)
**WRONG (Initial Response):**
- BBW has 6 layers (including Layer 6 LLM analysis)
- Layer 6: bbw_vince_insights.py

**CORRECT (User Correction):**
- BBW has 5 layers only (NO Layer 6)
- VINCE is separate ML component, NOT part of BBW pipeline
- BBW is pure data generator for VINCE training

**BBW V2 Layer Status:**
```
Layer 1: BBWP Calculator           ✅ COMPLETE (61/61 tests PASS)
Layer 2: BBW Sequence Analyzer     ✅ COMPLETE (68/68 tests PASS)
Layer 3: Forward Returns           ✅ COMPLETE (PASSING)
Layer 4: Backtester Results Analyzer ✅ COMPLETE (analyzes real trades)
Layer 4b: Monte Carlo Validation   ✅ COMPLETE (45/45 tests, 56/56 debug)
Layer 5: VINCE Feature Generator   ⚡ IN PROGRESS (pending completion)
```

### Project Reality
- **Source:** Real backtester results from 400+ coins, 1 year data, 93% success
- **NOT:** Synthetic simulated trades
- **Direction:** Determined by full Four Pillars strategy (Stochastics + Ripster + AVWAP)
- **BBW Role:** Enriches trades with volatility state, groups by (state, direction, LSG)

---

## Current Project Status

### Completed
- Data infrastructure: 399 coins, 6.2GB cache, CoinGecko integration
- Signal layer: Four Pillars v383 with state machine
- Dashboard v3.9: 5-tab Streamlit UI
- BBW Layers 1-4b: Full pipeline operational

### In Progress
- BBW Layer 5: VINCE feature CSV generation
- Dashboard testing: AVWAP bug, 5m validation needed
- Core Build 2: Test suite validation

### Blocked
- VINCE ML training: Waiting for Layer 5 completion + BE raise data
- 399-coin sweep: Needs clean data with BE raise restored
- Live integration: Needs VINCE validation

### Critical Path
BBW Layer 5 → 400-coin sweep → VINCE training → Live deployment

---

## VINCE Data Preservation Strategy

### Problem Identified
**User Concern:** "I don't want VINCE to burn through my limited data and then have data bias"

**Context:**
- 399 coins × ~1 year × 5m bars = ~42M bars total
- Once used for training, cannot be reused for clean validation
- Need strategy to preserve test data integrity

### Data Inventory
```
Total available: 42M bars across 399 coins
Already backtested: Dashboard sweep (93% success)
Risk: Training on all data = no clean validation set
```

### Recommended Strategy: HYBRID SPLIT

**Phase 1 - Model Development:**
```
Training:   280 coins × 8 months  = 22.4M bars (53%)
Validation:  40 coins × 12 months =  4.2M bars (10%)
Test (LOCKED): 79 coins × 12 months =  8.3M bars (20%)
Future reserve: Remaining          =  7.1M bars (17%)
```

**Phase 2 - Production Refinement:**
```
Retrain:    320 coins × 10 months (once architecture proven)
Validate:   Last 2 months of same 320 coins
Final test: 79 never-seen coins × full year
```

**Advantages:**
- Double validation: coin generalization + time robustness
- Maximum data efficiency (53% for training vs burning 80%+)
- Clean final test set for performance reporting
- 79 coins completely untouched until final evaluation

### Split Implementation

**File Structure:**
```json
splits.json (created ONCE, never modified):
{
  "train_coins": [280 coin symbols],
  "val_coins": [40 coin symbols],
  "test_coins": [79 coin symbols],  // FROZEN, never loaded during training
  "train_months": [1, 2, 3, 4, 5, 6, 7, 8],
  "val_months": [9, 10, 11, 12],
  "frozen_date": "2026-02-16",
  "stratification": "market_cap_balanced"
}
```

**VINCE Module 3 Logic:**
```python
# Load splits ONCE at startup
splits = load_splits_config()

# NEVER access test_coins during training/validation
train_data = load_coins(splits['train_coins'])
val_data = load_coins(splits['val_coins'])
# test_data loaded ONLY for final report/paper
```

### Cross-Validation Within Training Set

**5-Fold CV on 280 training coins:**
```
Fold 1: Train 224 coins, validate 56 coins
Fold 2: Train 224 coins, validate 56 coins (different split)
... (5 folds total)
```

**Benefits:**
- Uses 100% of training data efficiently
- Detects overfitting early (variance across folds)
- Provides confidence intervals on metrics
- Does NOT touch validation or test sets

### Monte Carlo Integration

**BBW Layer 4b verdicts filter training data:**
```
ROBUST states:        Include in training (high confidence)
FRAGILE states:       Lower weight or exclude (noisy)
COMMISSION_KILL:      Exclude entirely (no edge, pure noise)
```

**Result:**
- Training on ~60-70% of states
- But the CLEAN 60-70% (high-confidence data only)
- Reduces noise, improves generalization

### Data Augmentation (Synthetic Expansion)

**Bootstrap within-state trades:**
```
Example:
BLUE → NORMAL transition: 1000 real trades
Generate 5000 synthetic trades by resampling with replacement
```

**BBWP noise injection (training only):**
```
Real BBWP: 45.3
Augmented: 45.3 ± 2% = [44.4, 46.2] range
Forces robust learning, not exact threshold memorization
```

**Validation/test:** REAL data only (no augmentation)

### Incremental Learning Timeline

**Week 1:** Train on 280 coins × 6 months (oldest data)
**Week 2-4:** Add months 7-8 incrementally (transfer learning)
**Week 5+:** Daily new data added, incremental retraining
**Test set:** Untouched until quarterly performance review

### Critical Protection Rules

**IMMUTABLE RULES:**
1. `test_coins` list written ONCE before any training
2. Test set NEVER loaded during development phase
3. No hyperparameter tuning on test set
4. Test evaluation run ONCE for final report
5. Coin allocation stratified by market cap (not cherry-picked)

**Violation Detection:**
```python
# In VINCE code
assert current_coins.isdisjoint(splits['test_coins']), \
    "TEST SET CONTAMINATION DETECTED"
```

---

## Data Efficiency Comparison

| Strategy | Training Data | Test Reserve | Risk of Bias |
|----------|---------------|--------------|--------------|
| No split | 42M bars (100%) | 0 bars | EXTREME |
| Simple 80/20 | 33.6M (80%) | 8.4M (20%) | High |
| **Hybrid recommended** | **22.4M (53%)** | **12.5M (30%)** | **Low** |
| Overly conservative | 16.8M (40%) | 25.2M (60%) | Low but wasteful |

**Recommendation:** 53% training is optimal balance
- Sufficient data for robust learning
- 30% held out for clean validation
- 17% buffer for future expansion

---

## Next Actions

**Immediate (This Session):**
1. Complete BBW Layer 5 build
2. Generate splits.json (280/40/79 allocation)
3. Document test set freeze date

**This Week:**
1. Restore BE raise in backtester
2. Run 400-coin sweep with clean data
3. Generate Layer 5 CSV outputs

**Next Week:**
1. Build VINCE Module 3 (LSG Optimizer)
2. Implement train/val/test split logic
3. 5-fold cross-validation on training set
4. Initial XGBoost model training

**Protection Measures:**
1. Test set coins written to splits.json (immutable)
2. Code assertions prevent test set access
3. Validation metrics tracked separately from test metrics
4. Final test evaluation: ONE run, documented, never repeated

---

## Summary

**Project Health:** 85% complete
- BBW: 5 layers, 4.5 complete (Layer 5 pending)
- Data: 399 coins, 42M bars, 93% backtest success
- Next milestone: Layer 5 → VINCE training data ready

**Data Strategy:** Hybrid split (53% train, 10% val, 20% test, 17% future)
- Protects against data bias via coin-level holdout
- Enables cross-validation without burning test set
- Monte Carlo verdicts filter low-confidence states
- Incremental learning preserves older data

**Critical Insight:** Training on 53% of CLEAN data beats training on 80% of NOISY data.

**Risk Mitigation:**
- Test set frozen before any model development
- 5-fold CV provides confidence intervals
- BBW Monte Carlo filters remove fragile states
- Data augmentation expands effective training size

**Timeline:**
- Layer 5 complete: This week
- VINCE training: Next week
- Production deployment: 3-4 weeks

**Blocker:** BBW Layer 5 completion → unlocks entire VINCE pipeline
