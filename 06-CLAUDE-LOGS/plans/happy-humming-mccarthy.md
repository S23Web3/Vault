# Corrective Plan: Vince Scope + Vicky Project Separation
**Date:** 2026-02-18 Session 3

---

## Part 1: Create Vicky Project Folder

**New folder:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\vicky\`

### Files to MOVE from four-pillars-backtester to vicky/

| Source (four-pillars-backtester/) | Destination (vicky/) | Reason |
|---|---|---|
| `scripts/train_vince.py` | `scripts/train_vicky.py` | Trade classifier = Vicky's tool |
| `scripts/build_train_vince_v1.py` | `scripts/build_train_vicky_v1.py` | Build script for above |
| `scripts/build_docs_v1.py` | `scripts/build_docs_v1.py` | Vicky pipeline docs |
| `models/four_pillars/RIVERUSDT_xgb_20260218_090251.json` | `models/RIVERUSDT_xgb_20260218_090251.json` | Trained classifier output |
| `models/four_pillars/RIVERUSDT_report_20260218_090251.json` | `models/RIVERUSDT_report_20260218_090251.json` | Training report |
| `ml/vince_model.py` | `ml/vicky_model.py` | PyTorch 3-branch (Phase 2) |
| `ml/meta_label.py` | `ml/meta_label.py` | Meta-labeling = Vicky |
| `ml/bet_sizing_v2.py` | `ml/bet_sizing_v2.py` | Bet sizing for filtered trades |
| `ml/triple_barrier.py` | `ml/triple_barrier.py` | Classifier labeling |
| `VERSION-MASTER.md` | `VERSION-MASTER.md` | Vicky pipeline version doc |
| `docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md` | `docs/VICKY-ML-UML-DIAGRAMS.md` | Pipeline UML |

### Files that STAY in four-pillars-backtester (shared infrastructure)

| File | Why shared |
|---|---|
| `strategies/base.py` | All personas use strategy plugins |
| `strategies/four_pillars.py` | Shared strategy implementation |
| `strategies/__init__.py` | Shared plugin loader |
| `engine/backtester_v384.py` | Both Vince optimizer and Vicky classifier run backtests |
| `engine/commission.py` | Shared |
| `signals/*` | Shared signal generation |
| `data/coin_pools.json` | Shared pool assignment (60/20/20) |
| `data/cache/*` | Shared OHLCV data |
| `results/coin_tiers.csv` | Shared tier classification |
| `ml/features_v3.py` | Shared feature extraction |
| `ml/xgboost_trainer_v2.py` | Shared XGBoost utility |
| `ml/shap_analyzer_v2.py` | Shared SHAP utility |
| `ml/purged_cv.py` | Shared validation |
| `ml/walk_forward.py` | Shared validation |
| `ml/coin_features.py` | Shared coin-level features |
| `ml/loser_analysis.py` | Shared analysis |
| `scripts/build_data_infra_v1.py` | Creates shared coin_pools.json + coin_tiers.csv |

### Vicky project structure after move

```
PROJECTS/vicky/
  scripts/
    train_vicky.py          (renamed from train_vince.py)
    build_train_vicky_v1.py (renamed from build_train_vince_v1.py)
    build_docs_v1.py
  ml/
    vicky_model.py          (renamed from vince_model.py)
    meta_label.py
    bet_sizing_v2.py
    triple_barrier.py
  models/
    RIVERUSDT_xgb_20260218_090251.json
    RIVERUSDT_report_20260218_090251.json
  docs/
    VICKY-ML-UML-DIAGRAMS.md
  VERSION-MASTER.md
```

Vicky scripts import from four-pillars-backtester via sys.path (same pattern already used in train_vince.py).

---

## Part 2: Vince Correct Scope -- Parameter Optimizer

### What Vince IS
A parameter sweep engine that finds optimal strategy settings. Wraps the existing backtester as the inner loop. Maximizes net PnL after commission + rebate.

### What Vince optimizes

| Parameter Group | Parameters | Current Defaults |
|---|---|---|
| **Stochastics** | k1_length, k2_length, k3_length, k4_length, d_smooth, cross_level, zone_level | 9, 14, 40, 60, 10, 25, 30 |
| **Clouds** | cloud2_fast/slow, cloud3_fast/slow, cloud4_fast/slow | 5/12, 34/50, 72/89 |
| **AVWAP** | anchor rules, period | (not yet parameterized) |
| **SL** | sl_mult (ATR multiplier) | 2.0 |
| **TP** | tp_mult (ATR multiplier or None) | None |
| **BE** | be_trigger_atr, be_lock_atr | 0.0, 0.0 |
| **Entry types** | allow_b, allow_c, b_open_fresh, use_60d | True, True, True, False |

### Objective function
```
net_pnl = gross_pnl - total_commission + total_rebate
```
Where rebate = rebate_pct * total_commission (settled daily 5pm UTC).

Vince trades a LOT. Higher trade count = more rebate income. The optimizer must account for this.

### Architecture

```
Parameter Grid/Bayesian
        |
        v
  strategy.enrich_ohlcv(df, params)   <-- params from sweep
        |
        v
  strategy.compute_signals(df, params) <-- params from sweep
        |
        v
  Backtester384.run(df, bt_params)     <-- sl/tp/be from sweep
        |
        v
  Collect: net_pnl, trade_count, win_rate, max_drawdown
        |
        v
  Rank by objective (net_pnl after rebate)
        |
        v
  Output: optimal_params.json per coin (or per tier)
```

### Sweep modes
1. **Grid search** -- exhaustive over defined parameter ranges (small space)
2. **Bayesian (Optuna)** -- for larger parameter spaces, prune bad combos early
3. **Per-coin** -- optimize each coin independently
4. **Per-tier** -- optimize one set per tier, apply to all coins in tier

### Output per coin
```json
{
  "symbol": "RIVERUSDT",
  "optimal_params": {
    "stoch_k1": 9, "stoch_k2": 14, ...
    "sl_mult": 2.0, "tp_mult": null,
    "allow_b": true, "allow_c": true
  },
  "metrics": {
    "net_pnl": 5432.10,
    "trade_count": 2408,
    "win_rate": 0.456,
    "max_drawdown": -1200.50,
    "rebate_earned": 890.40,
    "sharpe": 1.85
  },
  "search_space_size": 1200,
  "evaluated": 1200,
  "duration_sec": 45.2
}
```

### Vince project stays in four-pillars-backtester
Vince IS the backtester optimizer. His code lives in:
- `scripts/optimize_vince.py` -- CLI entry point
- `ml/parameter_optimizer.py` -- sweep engine (grid + Optuna)

No separate project folder needed. Vince optimizes the backtester itself.

---

## Part 3: MEMORY.md Updates

Add persona definitions (locked). Update last session. Correct "VINCE ML Build" section to say "VICKY ML Build (mislabeled as Vince)."

---

## Part 4: cloud3_allows_long/short

Pre-existing in `engine/backtester_v384.py` lines 240, 345, 378. Computed in `signals/clouds.py` lines 71-72. This build did not introduce it.

User enters below cloud 3 regularly. This is a potential backtester fix (separate scope, not this plan).

---

## Execution Steps

1. Create `PROJECTS/vicky/` folder structure
2. MOVE files (not copy -- delete originals after confirming move)
3. Update import paths in moved files (sys.path to four-pillars-backtester)
4. Rename references (vince -> vicky in docstrings/comments)
5. Update MEMORY.md with persona definitions + Vicky project path
6. Append session log to `06-CLAUDE-LOGS/2026-02-18-vince-ml-build.md`
7. Remove empty `models/four_pillars/` dir from backtester

No Python execution. All file moves + edits.

---

## Verification

- `ls PROJECTS/vicky/` shows correct structure
- `ls PROJECTS/four-pillars-backtester/models/four_pillars/` is empty or removed
- `train_vince.py` no longer exists in four-pillars-backtester/scripts/
- MEMORY.md has persona definitions
- Session log updated
