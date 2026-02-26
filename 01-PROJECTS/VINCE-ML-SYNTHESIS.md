# Vince ML Synthesis — Book Insights for Four Pillars v3.8+

**Date**: 2026-02-09
**Purpose**: ML framework for Vince (crypto + rebates) based on 11 books analyzed
**Focus**: XGBoost meta-labeling, feature engineering, backtesting framework, position sizing

---

## Core ML Framework (De Prado "Advances in Financial ML")

### 1. Meta-Labeling (Ch 3)
**Problem**: Four Pillars generates A/B/C signals, but not all are good trades.
**Solution**: Primary model (Four Pillars) predicts direction. Secondary model (XGBoost) predicts size (0 = skip, 0.5 = half size, 1.0 = full size).

**Benefits**:
- Focuses ML on "bet sizing" problem, not direction prediction
- Reduces false positives (bad A/B/C signals)
- Improves Sharpe ratio by skipping marginal trades

**Implementation**:
```python
# Primary model (Four Pillars indicator)
primary_signal = four_pillars_signal()  # Returns 1 (long), -1 (short), or 0 (no signal)

# Secondary model (XGBoost)
if primary_signal != 0:
    features = extract_features(bar)  # Stoch K values, EMA distances, ATR%, volume ratio
    size_prediction = xgboost_model.predict(features)  # Returns 0.0 to 1.0

    if size_prediction < 0.3:
        # Skip trade (low confidence)
        pass
    elif size_prediction < 0.7:
        # Half size (medium confidence)
        position_size = base_size * 0.5
    else:
        # Full size (high confidence)
        position_size = base_size * 1.0
```

**Training data labels**:
- Label = 1 if trade hit TP
- Label = 0 if trade hit SL
- Label = (profit / TP_target) if closed manually (0.0 to 1.0)

### 2. Triple Barrier Method (Ch 3)
**Purpose**: Dynamic exit labeling for ML training.

**Three barriers**:
1. **Upper barrier (TP)**: +1.5 ATR from entry (profit target)
2. **Lower barrier (SL)**: -1.0 ATR from entry (stop loss)
3. **Vertical barrier (Time)**: Max bars in trade (e.g., 100 bars on 5m = 8.3 hours)

**Label assignment**:
- If price hits upper barrier first → Label = 1 (winner)
- If price hits lower barrier first → Label = 0 (loser)
- If time barrier hit first → Label = (profit / TP_target) capped at [0, 1]

**Why important**:
- Prevents "look-ahead bias" (only using historical data up to exit point)
- Accounts for trades that neither hit TP nor SL (time exits)
- Aligns with real trading (you don't hold losers forever)

### 3. Purged K-Fold Cross-Validation (Ch 7)
**Problem**: Standard K-fold CV leaks information when time series data overlaps.
**Solution**: "Purge" training samples that overlap with test samples.

**Example**:
- Trade entry at bar 100, exit at bar 150 (50-bar duration)
- If test set starts at bar 120, remove bars 100-150 from training set
- Prevents model from "seeing the future"

**Implementation**:
```python
from sklearn.model_selection import TimeSeriesSplit

# Purged K-Fold with embargo
def purged_kfold(X, y, n_splits=5, pct_embargo=0.01):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    for train_idx, test_idx in tscv.split(X):
        # Purge: Remove training samples that overlap with test samples
        train_times = X.index[train_idx]
        test_times = X.index[test_idx]

        # Remove train samples within trade duration of first test sample
        min_test_time = test_times.min()
        purged_train_idx = train_idx[train_times < (min_test_time - trade_duration)]

        # Embargo: Remove training samples immediately before test set
        embargo_period = int(len(train_idx) * pct_embargo)
        purged_train_idx = purged_train_idx[:-embargo_period]

        yield purged_train_idx, test_idx
```

### 4. Feature Importance (Ch 8)
**Problem**: XGBoost's `feature_importances_` is biased toward high-cardinality features.
**Solution**: Use **Mean Decrease Impurity (MDI)** + **Mean Decrease Accuracy (MDA)** + **SHAP values** (from Jansen book).

**MDI** (built-in XGBoost):
- Measures how much each feature decreases Gini impurity across all trees
- Fast, but biased

**MDA** (permutation importance):
- Shuffle feature values, measure drop in accuracy
- Slower, but unbiased

**SHAP values** (Jansen book):
- Explains per-sample predictions
- Shows which features contributed to EACH trade's outcome
- Most interpretable

**Why important for Vince**:
- Identifies which Four Pillars components matter most (e.g., Stoch 9-3 vs 14-3 vs 40-3)
- Guides feature engineering (drop useless features, add new ones)
- Helps debug bad trades (SHAP shows why XGBoost skipped or took a trade)

### 5. Bet Sizing from Predicted Probability (Ch 10)
**Problem**: Binary classification (take/skip) ignores confidence level.
**Solution**: Use predicted probability to size position.

**Formula**:
```python
# XGBoost returns probability of class 1 (winner)
prob_win = xgboost_model.predict_proba(features)[0][1]

# Kelly Criterion (from Van Tharp + Hilpisch books)
# f = (p * b - q) / b
# where p = prob_win, q = 1 - p, b = win_size / loss_size
win_loss_ratio = 1.5  # TP = 1.5 ATR, SL = 1.0 ATR
kelly_fraction = (prob_win * win_loss_ratio - (1 - prob_win)) / win_loss_ratio

# Cap at max risk (1-2% of account)
position_size = max(0, min(kelly_fraction, 0.02)) * account_size
```

**Why important for Vince**:
- With rebates, even low-confidence trades (prob_win = 0.4) can be profitable
- Kelly fraction adjusts size based on edge
- Prevents over-betting on marginal signals

### 6. Sharpe Ratio Formula (Ch 15)
**Mathematical basis for rebate farming**:

$$
Sharpe = \frac{p \cdot \bar{R}_+ - (1-p) \cdot \bar{R}_-}{\sqrt{p \cdot \sigma_+^2 + (1-p) \cdot \sigma_-^2}} \cdot \sqrt{n}
$$

Where:
- $p$ = precision (win rate)
- $\bar{R}_+$ = average win size
- $\bar{R}_-$ = average loss size
- $\sigma_+$ = std dev of wins
- $\sigma_-$ = std dev of losses
- $n$ = trade frequency (trades per year)

**Key insight**: Sharpe scales with $\sqrt{n}$, so **high frequency compensates for low win rate**.

**Example**:
- Vince: p = 0.45 (45% win rate), n = 36,000 trades/year → Sharpe = 2.5
- Vicky: p = 0.55 (55% win rate), n = 12,000 trades/year → Sharpe = 2.0

---

## Feature Engineering (Jansen "ML for Algorithmic Trading")

### 1. Four Pillars Core Features (12 features)
- **Stochastic K values** (4): K9, K14, K40, K60
- **Stochastic D value** (1): D60 (SMA of K60, 10-period)
- **EMA Cloud distances** (4): Price distance to Cloud 2, 3, 4, 5 (in ATR units)
- **ATR%** (1): ATR / price × 100
- **Volume ratio** (1): Current volume / 20-period SMA of volume
- **Time of day** (1): Hour of day (0-23) — session filter proxy

### 2. Technical Indicators (TA-Lib Alpha Factor Library)
**From Jansen Ch 4, Table 4-2** (100+ indicators):

**Momentum** (add 5):
- RSI(14)
- CCI(20)
- Williams %R(14)
- MFI(14) — Money Flow Index (volume-weighted RSI)
- MACD(12, 26, 9) — 3 values: MACD line, signal line, histogram

**Volatility** (add 2):
- Bollinger Band Width: (upper - lower) / middle × 100
- Average True Range % (already have, but confirm calculation)

**Volume** (add 2):
- OBV (On-Balance Volume) — cumulative volume signed by direction
- ADOSC (Chaikin A/D Oscillator) — 3-10 period of A/D line

**Total features**: 12 (core) + 5 (momentum) + 2 (volatility) + 2 (volume) = **21 features**

### 3. Feature Preprocessing
**Gaussian Normalization** (from Hilpisch "AI in Finance"):
```python
# Z-score normalization
features_normalized = (features - features.mean()) / features.std()

# Rolling window (prevent look-ahead bias)
features_normalized = (features - features.rolling(100).mean()) / features.rolling(100).std()
```

**Why important**:
- Neural networks (if used) require normalized inputs
- XGBoost less sensitive, but still benefits
- Prevents features with large ranges (e.g., volume) from dominating

---

## MFE/MAE Analysis (Sweeney "Maximum Adverse Excursion")

### 1. Track Entry, Min, Max for Every Trade
```python
# From Hilpisch Ch 11
self.entry_price = price
self.min_price = price   # MAE (Maximum Adverse Excursion)
self.max_price = price   # MFE (Maximum Favorable Excursion)

# Update every bar while in trade
if in_position:
    self.min_price = min(self.min_price, current_price)
    self.max_price = max(self.max_price, current_price)
```

### 2. Classify Losers (A/B/C/D Framework from Sweeney)
- **Type A**: Never profitable (max < BE)
- **Type B**: Briefly profitable, quickly reversed (max > BE, duration < 5 bars)
- **Type C**: Held profit, gave it back (max > BE + fees, duration > 5 bars)
- **Type D**: Hit partial profit target, reversed (max > 0.5× TP)

### 3. Optimize BE Raise by Loser Type
**Current backtester results** (5m, 3 months):
- LSG (Loser Saw Green) = 68-84% across all coins
- Most losers were Type C (held profit, gave it back)

**v3.8 solution**: ATR-based BE raise
- Trigger: When profit > 0.5× ATR (replaces fixed $2/$4/$6)
- Lock: Move SL to entry + 0.3× ATR (covers fees)

---

## XGBoost Model Architecture (Jansen Ch 6)

### 1. Hyperparameters
```python
import xgboost as xgb

params = {
    'objective': 'binary:logistic',  # Or 'reg:squarederror' for continuous bet size
    'max_depth': 5,                  # Prevent overfitting
    'learning_rate': 0.01,           # Small steps
    'n_estimators': 1000,            # Many weak learners
    'subsample': 0.8,                # Row sampling (prevents overfitting)
    'colsample_bytree': 0.8,         # Feature sampling
    'gamma': 0.1,                    # Min loss reduction for split
    'reg_alpha': 0.1,                # L1 regularization
    'reg_lambda': 1.0,               # L2 regularization
    'scale_pos_weight': 1.0,         # Balance classes (if imbalanced)
    'random_state': 42
}

model = xgb.XGBClassifier(**params)
```

### 2. Training with Early Stopping
```python
# Split data: 70% train, 15% validation, 15% test
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, shuffle=False)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, shuffle=False)

# Train with early stopping
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=50,
    verbose=10
)

# Evaluate on test set
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Test accuracy: {accuracy:.2%}")
```

### 3. SHAP Values for Interpretability
```python
import shap

# Create explainer
explainer = shap.TreeExplainer(model)

# Explain all test predictions
shap_values = explainer.shap_values(X_test)

# Summary plot (global feature importance)
shap.summary_plot(shap_values, X_test)

# Force plot (per-sample explanation)
# Shows why XGBoost predicted skip (0) or take (1) for a specific trade
shap.force_plot(explainer.expected_value, shap_values[0], X_test.iloc[0])
```

**Why important**:
- Debugging: See which feature caused a bad prediction
- Feature engineering: Identify useless features to drop
- Validation: Confirm model uses Four Pillars logic (not spurious correlations)

---

## Position Sizing (Van Tharp "Trade Your Way to Financial Freedom")

### 1. R-Multiples
**Definition**: Trade outcome expressed in units of initial risk.

**Formula**:
```python
R = initial_risk = SL_distance * position_size
profit_loss = exit_price - entry_price
R_multiple = profit_loss / R
```

**Example**:
- Entry: $1.00, SL: $0.95, TP: $1.075
- R = $0.05 (5% stop)
- If hit TP: Profit = $0.075, R-multiple = 0.075 / 0.05 = **1.5R**
- If hit SL: Profit = -$0.05, R-multiple = -0.05 / 0.05 = **-1.0R**

**Why important**:
- Normalizes trade outcomes across different instruments (RIVER vs BTC)
- Allows position sizing based on volatility (tighter stop = larger size)

### 2. System Quality Number (SQN)
**Formula**:
$$
SQN = \frac{\bar{R} \times \sqrt{n}}{\sigma_R}
$$

Where:
- $\bar{R}$ = average R-multiple
- $n$ = number of trades
- $\sigma_R$ = std dev of R-multiples

**SQN Ratings** (Van Tharp):
- **1.6 - 2.0**: Below average (barely tradeable)
- **2.0 - 2.5**: Average
- **2.5 - 3.0**: Good
- **3.0 - 5.0**: Excellent
- **5.0 - 7.0**: Superb (holy grail)
- **> 7.0**: Too good to be true (probably overfitting)

**Why important for Vince**:
- SQN scales with $\sqrt{n}$, so high frequency helps
- Target: SQN > 2.5 (good system)
- With 36,000 trades/year, need $\bar{R} = 0.05$ and $\sigma_R = 0.5$ → SQN = 2.8

### 3. Expectunity
**Formula**:
$$
Expectunity = Expectancy \times Opportunity
$$

**Expectancy**:
$$
E = (P_w \times \bar{W}) - (P_l \times \bar{L})
$$

Where:
- $P_w$ = probability of win
- $\bar{W}$ = average win size
- $P_l$ = probability of loss
- $\bar{L}$ = average loss size

**Example (Vince)**:
- $P_w = 0.45$, $\bar{W} = 1.5R$
- $P_l = 0.55$, $\bar{L} = 1.0R$
- Expectancy = (0.45 × 1.5) - (0.55 × 1.0) = 0.675 - 0.55 = **0.125R per trade**
- Opportunity = 3000 trades/month
- Expectunity = 0.125 × 3000 = **375R per month**

**With rebates**:
- Rebate = $3.60 per RT (70% account) = 0.36R (if R = $10)
- Expectancy_total = 0.125 + 0.36 = **0.485R per trade**
- Expectunity_total = 0.485 × 3000 = **1,455R per month**

**Why important**:
- Explains why rebate farming works (high opportunity compensates for low/negative expectancy)
- For Vicky (no rebates), need positive expectancy (E > 0), so higher win rate or better exits

---

## Backtesting Framework (Hilpisch "AI in Finance" Ch 11 + De Prado Ch 7)

### 1. Vectorized vs Event-Based
**Vectorized** (fast, for initial testing):
- Apply indicators to entire DataFrame at once
- Generate signals, calculate P&L
- No order management, no slippage, no commissions
- Good for: Strategy screening, parameter optimization

**Event-Based** (slow, for final validation):
- Process bar-by-bar with order queue
- Track order IDs, fills, partial fills
- Model slippage, commissions, market impact
- Good for: Final validation, live trading simulation

**Vince approach**: Use vectorized for parameter sweep, event-based for final validation.

### 2. Walk-Forward Analysis (De Prado Ch 7)
**Purpose**: Prevent overfitting to single train/test split.

**Method**:
1. Split data into 10 windows (e.g., 3 months each)
2. For each window:
   - Train on window N-1
   - Test on window N
   - Record performance
3. Average performance across all windows

**Why important**:
- Single train/test split can be lucky/unlucky
- Walk-forward simulates "deploying model every 3 months"
- More realistic performance estimate

### 3. Commission Modeling
**Updated commission** (from user):
- **0.08%** = $8/side on $10K notional (20x leverage)
- **$16 round trip**

**Rebate** (Vince only):
- 70% account: $3.60 × 2 = $7.20 rebate per RT
- Net commission: $16 - $7.20 = **$8.80 net per RT**

**For backtester**:
```python
# TradingView strategy
strategy.commission.cash_per_order = 8  # $8/side, deterministic

# Python backtester
commission_per_trade = 16.0  # Round trip
rebate_per_trade = 7.20      # Vince only (70% account)
net_commission = commission_per_trade - rebate_per_trade  # $8.80
```

---

## Summary: ML Pipeline for Vince v3.8+

### Phase 1: Data Preparation
1. Load 3-month 1m/5m Bybit data for 9 coins (PROJECTS/four-pillars-backtester/data/cache/)
2. Resample to 5m (optimal timeframe)
3. Calculate Four Pillars indicators (Stoch K9/K14/K40/K60, EMA Clouds, ATR, volume)
4. Calculate TA-Lib features (RSI, CCI, Williams %R, MFI, MACD, BBW, OBV, ADOSC)
5. Normalize features (rolling z-score, 100-bar window)

### Phase 2: Label Generation (Triple Barrier)
1. For each Four Pillars signal (A/B/C):
   - Upper barrier: entry + 1.5 ATR
   - Lower barrier: entry - 1.0 ATR
   - Vertical barrier: 100 bars (8.3 hours on 5m)
2. Label = 1 if upper hit first, 0 if lower hit first, (profit / TP) if time hit first
3. Track MFE/MAE for every trade

### Phase 3: Train XGBoost Meta-Labeling Model
1. Split data: 70% train, 15% validation, 15% test (time-based, no shuffle)
2. Purged K-fold CV (5 folds, 1% embargo)
3. Train XGBoost with early stopping
4. Evaluate: Accuracy, precision, recall, F1, AUC-ROC
5. SHAP values: Global feature importance + per-sample explanations

### Phase 4: Backtest with Meta-Labeling
1. Generate Four Pillars signals (A/B/C)
2. For each signal, XGBoost predicts probability of win
3. Size position based on Kelly fraction (capped at 2% risk)
4. Track R-multiples, SQN, Expectunity
5. MFE/MAE analysis: Classify losers (A/B/C/D), optimize BE raise

### Phase 5: Walk-Forward Validation
1. Split 3 months into 6 windows (2 weeks each)
2. Train on window N-1, test on window N
3. Record: Sharpe, SQN, win rate, avg R, total profit, max DD
4. Average across all windows

### Phase 6: Risk Method Comparison (Vince)
Test 4 risk methods:
1. Move SL to breakeven (0 ATR)
2. BE + fees (0.3 ATR above entry)
3. BE + fees + trailing TP (trail TP from max_price)
4. BE + trailing TP (trail both SL and TP)

**Metric**: SQN × Total Profit (balances consistency and return)

---

## Expected Outcomes

### Vince (with rebates)
- **Win rate**: 45-50% (low is OK, rebates compensate)
- **Avg R**: +0.1R to +0.2R per trade (before rebates), +0.4R to +0.5R (after rebates)
- **SQN**: 2.5-3.0 (good system)
- **Total profit (3 months)**: $50K-$100K (across 20K-30K trades)
- **Best coins**: RIVER, KITE, PEPE (low price, high commission/TP ratio)

### Vicky (no rebates) — Future Phase
- **Win rate**: 55-60% (MUST be higher than Vince)
- **Avg R**: +0.2R to +0.3R per trade
- **SQN**: 2.0-2.5 (average to good)
- **Total profit (3 months)**: $30K-$50K (fewer trades due to meta-labeling skip)
- **Best coins**: Same as Vince, but more selective entries

---

## Books Referenced
1. **De Prado** "Advances in Financial ML" (9/10) — Meta-Labeling, Triple Barrier, Purged CV, Sharpe formula
2. **Jansen** "ML for Algorithmic Trading" (8/10) — SHAP values, Alpha Factor Library, feature engineering
3. **Van Tharp** "Trade Your Way to Financial Freedom" (7/10) — R-multiples, SQN, Expectunity
4. **Sweeney** "Maximum Adverse Excursion" (9/10) — MFE/MAE tracking, loser classification, BE optimization
5. **Hilpisch** "AI in Finance" (5/10) — ATR×leverage, backtesting framework

---

## Next Steps
1. Create scheduled approach plan for ML pipeline implementation
2. Build data preparation scripts
3. Build label generation script (Triple Barrier)
4. Build XGBoost training script
5. Build backtesting script with meta-labeling
6. Build walk-forward validation script
7. Build risk method comparison script
8. Run comprehensive analysis on all 9 coins
