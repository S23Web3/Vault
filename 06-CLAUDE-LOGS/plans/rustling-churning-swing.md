# Vince Parameter Optimizer — Build Plan
**Date:** 2026-02-18 | **Model:** Opus 4.6

---

## Context

The previous build (2026-02-18 session) was mislabeled as "Vince" but built Vicky's tool — an XGBoost trade classifier that SKIPS trades. That is the opposite of what Vince does. Vince is a rebate farmer. More trades = more rebate income. Vince finds the BEST PARAMETER COMBINATIONS for the Four Pillars strategy, not which trades to avoid.

**What went wrong:** Trade filtering (meta-labeling, bet sizing, skip/take) was built. The user gets 70% rebates ($4.80/RT net on 70% accounts). Skipping trades directly destroys rebate income.

**What this build does:** Bayesian parameter optimization (Optuna) that wraps the existing `compute_signals_v383()` + `Backtester384.run()` pipeline. Finds optimal stochastic, cloud, SL/TP, BE, and position management settings per coin. Objective function includes rebate income. Trade count is NOT reduced — if anything, better parameters may INCREASE trade count.

---

## Scope

### BUILD (this session)
- `scripts/build_optimize_vince.py` — build script (creates all files below)
- `ml/parameter_optimizer.py` — Optuna sweep engine (~400 lines)
- `scripts/optimize_vince.py` — CLI entry point (~350 lines)
- `tests/test_parameter_optimizer.py` — test suite (~200 lines)

### NOT building
- No trade filtering, meta-labeling, or bet sizing
- No strategy plugin (not needed — call signal/backtester directly)
- No Vicky separation (separate scope)
- No PyTorch models
- No dashboard integration (that's a future scope)

### Dependency
- `pip install optuna` (required, user must install before running)

---

## Architecture

```
Raw OHLCV parquet
       |
       v
 Optuna TPE Sampler (300 trials per coin)
       |--- sample signal_params (stoch, cloud, cross_level, zone_level, etc.)
       |--- sample bt_params (sl_mult, tp_mult, be, positions, etc.)
       |
       v
 compute_signals_v383(df.copy(), signal_params)   [signals/four_pillars_v383.py]
       |--- compute_all_stochastics(df, params)    [signals/stochastics.py]
       |--- compute_clouds(df, params)             [signals/clouds.py]
       |--- ATR (RMA, atr_length param)
       |--- FourPillarsStateMachine383 (state machine with params)
       |
       v
 Backtester384(bt_params).run(df_sig)             [engine/backtester_v384.py]
       |
       v
 metrics["net_pnl_after_rebate"]  -->  Optuna maximizes
       |
       v
 After all trials:
   - Best params JSON
   - All trials CSV
   - Parameter importance (fANOVA + SHAP)
   - Grade analysis (A/B/C/D at optimal params)
   - Walk-forward validation (optional)
```

No strategy plugin needed. Same call pattern as `dashboard_v391.py:run_backtest()`.

---

## Parameter Search Space (26 swept parameters)

### Signal Parameters (16)

| Param | Type | Default | Range | Constraint |
|-------|------|---------|-------|------------|
| stoch_k1 | int | 9 | 5-15 | k1 < k2 |
| stoch_k2 | int | 14 | max(k1+1,10)-20 | k2 < k3 |
| stoch_k3 | int | 40 | max(k2+1,30)-55 | k3 < k4 |
| stoch_k4 | int | 60 | max(k3+1,45)-75 | — |
| stoch_d_smooth | int | 10 | 3-20 | — |
| cloud2_fast | int | 5 | 3-10 | fast < slow |
| cloud2_slow | int | 12 | max(c2f+1,8)-20 | — |
| cloud3_fast | int | 34 | 20-55 | fast < slow |
| cloud3_slow | int | 50 | max(c3f+1,35)-75 | — |
| cloud4_fast | int | 72 | 50-100 | fast < slow |
| cloud4_slow | int | 89 | max(c4f+1,70)-120 | — |
| cross_level | int | 25 | 15-40 | — |
| zone_level | int | 30 | max(cross,20)-45 | >= cross_level |
| allow_b_trades | bool | True | T/F | — |
| allow_c_trades | bool | True | T/F | — |
| use_60d | bool | False | T/F | — |

### Backtester Parameters (10)

| Param | Type | Default | Range | Constraint |
|-------|------|---------|-------|------------|
| sl_mult | float | 2.0 | 0.5-5.0 (step 0.1) | — |
| tp_mult | None/float | None | None,1.0,1.5,2.0,2.5,3.0,4.0 | categorical |
| be_trigger_atr | float | 0.0 | 0.0-3.0 (step 0.1) | — |
| be_lock_atr | float | 0.0 | 0.0-trigger (step 0.1) | <= trigger |
| max_positions | int | 4 | 1-4 | — |
| cooldown | int | 3 | 0-10 | — |
| checkpoint_interval | int | 5 | 3-15 | — |
| max_scaleouts | int | 2 | 0-3 | — |
| enable_adds | bool | True | T/F | — |
| enable_reentry | bool | True | T/F | — |

### Fixed (NOT swept)
commission_rate=0.0008, maker_rate=0.0002, rebate_pct=0.70, notional=5000, initial_equity=10000, atr_length=14, sigma_floor_atr=0.5, b_open_fresh=True, cancel_bars=3, reentry_window=5, max_avwap_age=50, settlement_hour_utc=17

All constraints enforced at sampling time via conditional ranges (Optuna idiomatic approach, no wasted trials).

---

## Objective Functions

User selects via `--objective` flag:

| Name | Formula | When to use |
|------|---------|-------------|
| `net_pnl_after_rebate` (default) | gross_pnl - commission*(1-0.70) | Rebate farming (Vince's primary) |
| `sharpe` | Sharpe ratio from backtester | Risk-adjusted |
| `risk_adjusted` | net_pnl_after_rebate / (1 + abs(max_dd_pct)) | PnL with DD penalty |

Pruning: trials with < 10 trades are pruned (not counted).

---

## CLI Flags

```
python optimize_vince.py
  --symbol RIVERUSDT        Single coin (or ALL for sweep)
  --tier 1                  Per-tier mode (0-3)
  --top 20                  Limit ALL to top N coins
  --timeframe 5m            1m or 5m (default: 5m)
  --n-trials 300            Optuna trials per coin
  --timeout 600             Max seconds per optimization
  --objective net_pnl_after_rebate
  --walk-forward            Enable walk-forward validation
  --wf-splits 5             Walk-forward folds
  --wf-trials 100           Trials per WF fold
  --output-dir results/vince
  --resume                  Resume from SQLite study
  --rebate-pct 0.70         Override rebate percentage
  --notional 5000           Override notional
  --verbose                 Debug logging
```

---

## Walk-Forward Validation

Expanding window approach (simulates real workflow: optimize on all history, trade next period):

```
Fold 1:  |===IS===|=OOS=|
Fold 2:  |====IS====|=OOS=|
Fold 3:  |======IS======|=OOS=|
Fold 4:  |========IS========|=OOS=|
```

For each fold: run Optuna on IS data, evaluate best params on OOS data.
WFE = mean(OOS_metric / IS_metric). Rating: ROBUST (>0.6), MARGINAL (0.3-0.6), OVERFIT (<0.3).

Reuses `compute_wfe()` and `get_wfe_rating()` from existing `ml/walk_forward.py`.

---

## Parameter Importance Analysis

Two methods run after optimization completes:

1. **Optuna fANOVA** (built-in) — functional ANOVA on trial results, gives magnitude of each parameter's impact
2. **XGBoost surrogate + SHAP** (optional) — trains XGBRegressor on (params -> objective), SHAP gives directional insight (does increasing sl_mult help or hurt?)

Output tells user: "sl_mult matters most (importance=0.34), followed by tp_mult (0.29)..."

---

## Output Per Coin

| File | Content |
|------|---------|
| `{SYMBOL}_optimal.json` | Best params + full metrics + grade breakdown + rebate projection |
| `{SYMBOL}_trials.csv` | All 300 trials (every param + objective + trades + WR + DD) |
| `{SYMBOL}_study.db` | Optuna SQLite (for --resume) |
| `{SYMBOL}_importance.json` | fANOVA + SHAP parameter importance |
| `{SYMBOL}_walk_forward.json` | WFE results per fold (if --walk-forward) |
| `sweep_summary.csv` | All coins' best results (sweep modes only) |

---

## Timing Estimates

| Mode | Time |
|------|------|
| Single coin, 300 trials | ~15 min |
| Single coin + walk-forward (5 folds x 100 trials) | ~45 min |
| Top 20 coins, 300 trials each | ~5 hours |
| All 399 per-tier (5 tiers x 300 trials) | ~1.5 hours |

Each trial: ~3 sec (1.5s signals + 1.5s backtester on 105K 5m bars).

---

## Files Reused (NOT modified)

| File | What optimizer uses from it |
|------|----------------------------|
| `signals/four_pillars_v383.py` | `compute_signals_v383(df, params)` |
| `signals/stochastics.py` | Called internally by above |
| `signals/clouds.py` | Called internally by above |
| `engine/backtester_v384.py` | `Backtester384(params).run(df)` |
| `engine/commission.py` | Used by Backtester384 internally |
| `ml/walk_forward.py` | `compute_wfe()`, `get_wfe_rating()` |
| `research/coin_classifier.py` | Tier classification for --tier mode |
| `data/coin_pools.json` | Pool A/B/C assignment (holdout protection) |

---

## Verification

1. Run build: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\build_optimize_vince.py"`
2. Run tests: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\tests\test_parameter_optimizer.py"`
3. Quick smoke test (10 trials): `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\optimize_vince.py" --symbol RIVERUSDT --n-trials 10 --verbose`
4. Full optimization: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\optimize_vince.py" --symbol RIVERUSDT --n-trials 300 --verbose`
5. Walk-forward: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\optimize_vince.py" --symbol RIVERUSDT --walk-forward --wf-splits 3 --wf-trials 50 --verbose`
6. Compare optimal vs default params on dashboard
