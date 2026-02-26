# Optimization & Walk-Forward Methodology

## Optuna Integration

### Built-in Visualizations (v4.7.0+)
| Function | Shows | Use Case |
|----------|-------|----------|
| plot_optimization_history | Objective per trial + best trend | Is optimization converging? |
| plot_parallel_coordinate | Multi-dim parameter relationships | Which param combos cluster around good results? |
| plot_contour | 2D surface for 2 params | Find optimal regions for param pairs |
| plot_param_importances | Bar chart (fANOVA method) | Which params matter most? |
| plot_slice | Individual param vs objective | Each param's independent effect |
| plot_pareto_front | Multi-objective tradeoff | When optimizing multiple objectives |

### Optuna Dashboard (Web UI)
- `pip install optuna-dashboard`
- `optuna-dashboard sqlite:///study.db`
- Real-time optimization monitoring
- LLM integration for natural language trial filtering

### Strategy Optimization Search Space (Four Pillars)
```python
def objective(trial):
    sl_mult = trial.suggest_float("sl_mult", 0.3, 3.0, step=0.1)
    tp_mult = trial.suggest_float("tp_mult", 0.5, 5.0, step=0.1)
    cooldown = trial.suggest_int("cooldown", 0, 20)
    be_trigger = trial.suggest_float("be_trigger_atr", 0.0, 2.0, step=0.1)
    be_lock = trial.suggest_float("be_lock_atr", 0.0, 1.0, step=0.05)
    # Return: Sharpe or net_pnl or composite
```

## Walk-Forward Analysis

### Core Process
1. Divide data into rolling windows
2. Optimize on in-sample (IS) window
3. Test optimized params on out-of-sample (OOS) window
4. Roll forward, repeat
5. Concatenate all OOS results into one equity curve

### Window Sizing
- Common ratio: 70% IS / 30% OOS per segment
- Minimum: IS window must contain 100+ trades
- For 3-month data: 2-month IS, 1-month OOS, roll by 1 month = 2 windows
- For 6-month data: 4-month IS, 2-month OOS, roll by 2 months = 2 windows

### Walk Forward Efficiency (WFE)
```
WFE = (Annualized OOS Return) / (Annualized IS Return)
```
- WFE > 60%: robust strategy
- WFE 30-60%: marginal, needs more data
- WFE < 30%: overfit, don't deploy

### Anchored vs Rolling Windows
| Approach | IS Window | Best For |
|----------|-----------|----------|
| Rolling | Fixed size, slides forward | Short-term strategies, respects regime changes |
| Anchored | Grows with each step | Longer timeframe, cumulative learning |

### Overfitting Prevention
1. Walk-forward analysis itself
2. Monte Carlo on OOS equity (shuffle trade order, bootstrap CI)
3. Parameter stability check (do optimal params change wildly between windows?)
4. Fewer free parameters (each one increases overfitting risk exponentially)
5. Regularize objective (optimize Sharpe, not raw profit)
6. Minimum 30 trades per OOS window, ideally 100+
7. Never touch OOS data for any parameter tuning

### Multi-Objective Optimization
For trading, often want to optimize multiple objectives:
- Maximize: net P&L, Sharpe ratio
- Minimize: max drawdown, commission total
- Optuna supports Pareto front for multi-objective

## XGBoost for Feature Importance

### Use Case: "What predicts a losing trade?"
```python
features = ['entry_stoch_9', 'entry_stoch_14', 'entry_stoch_40', 'entry_stoch_60',
            'entry_cloud3_bull', 'entry_price_pos', 'entry_atr',
            'grade_encoded', 'direction_encoded']
target = 'is_winner'  # binary classification

model = xgb.XGBClassifier(tree_method='gpu_hist', device='cuda')
model.fit(X_train, y_train)
importance = model.feature_importances_
```
This tells you: "stoch_40 > 70 at entry is the #1 predictor of a loser"

### Use Case: "What predicts an almost-winner loser?"
Same approach but target = 'loser_class' (multiclass: A/B/C/D)
Answers: "What do almost-winner losers have in common that clean losers don't?"

## GPU Acceleration (RTX 3060 12GB)
- PyTorch: tensor operations, future neural net models
- XGBoost: `tree_method='gpu_hist'` for GPU-accelerated training
- Optuna + XGBoost: each trial trains an XGBoost model on GPU
- Expected: 500 Optuna trials across 339 coins = hours, not days

## Recommended Books
1. John Sweeney, "Maximum Adverse Excursion" (1997) — MFE/MAE methodology
2. Stefan Jansen, "Machine Learning for Algorithmic Trading" (2020) — End-to-end ML + backtesting
3. Kevin Davey, "Building Winning Algorithmic Trading Systems" — Walk-forward focused
4. Marcos Lopez de Prado, "Advances in Financial Machine Learning" (2018) — Anti-overfitting
5. Van Tharp, "Trade Your Way to Financial Freedom" — R-multiples, SQN, position sizing
