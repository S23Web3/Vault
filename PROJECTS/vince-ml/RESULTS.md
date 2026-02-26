# Vince ML Analysis Results

**Analysis Date**: [DATE]
**Timeframe**: 5m
**Date Range**: [START] to [END]
**Coins Analyzed**: [N] coins
**Total Trades**: [N] trades

---

## Executive Summary

[Brief 2-3 sentence summary of key findings]

**Key Findings**:
- Best performing coin: [COIN] (+$X, Y% win rate, Z SQN)
- Worst performing coin: [COIN] (-$X, Y% win rate, Z SQN)
- Optimal BE trigger: [X]× ATR (universal best practice)
- Optimal BE lock: [Y]× ATR (covers commission + buffer)
- Most important feature: [FEATURE] (SHAP value: [X])

---

## 1. Aggregate Performance

### Overall Metrics (All Coins Combined)

| Metric | Value |
|--------|-------|
| **Total Trades** | [N] |
| **Win Rate** | [X]% |
| **Total Profit** | $[X] |
| **Avg R per Trade** | [X]R |
| **Expectancy** | $[X]/trade |
| **Sharpe Ratio** | [X] |
| **SQN** | [X] |
| **Max Drawdown** | [X]% |
| **Total Commission** | $[X] |
| **Net Commission** (after rebates) | $[X] |

### Trade Grade Breakdown

| Grade | Count | Win Rate | Avg R | Total Profit |
|-------|-------|----------|-------|--------------|
| **A** (4/4 stochs) | [N] | [X]% | [Y]R | $[Z] |
| **B** (3/4 stochs) | [N] | [X]% | [Y]R | $[Z] |
| **C** (2/4 + Cloud 3) | [N] | [X]% | [Y]R | $[Z] |
| **R** (Cloud 2 re-entry) | [N] | [X]% | [Y]R | $[Z] |

**Insight**: [Which grade performed best? Should we filter any grades?]

---

## 2. Per-Coin Results

### Top 10 Performers (by SQN × Profit)

| Rank | Coin | Trades | Win Rate | Total Profit | SQN | Sharpe | Optimal BE |
|------|------|--------|----------|--------------|-----|--------|------------|
| 1 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 2 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 3 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 4 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 5 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 6 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 7 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 8 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 9 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |
| 10 | [COIN] | [N] | [X]% | $[Y] | [Z] | [A] | [B]×ATR |

**Common Traits**: [What do top performers have in common? Low price? High volume? Low ATR/price ratio?]

---

### Bottom 10 Performers (by SQN × Profit)

| Rank | Coin | Trades | Win Rate | Total Profit | SQN | Sharpe | Issue |
|------|------|--------|----------|--------------|-----|--------|-------|
| 1 | [COIN] | [N] | [X]% | -$[Y] | [Z] | [A] | [ISSUE] |
| 2 | [COIN] | [N] | [X]% | -$[Y] | [Z] | [A] | [ISSUE] |
| 3 | [COIN] | [N] | [X]% | -$[Y] | [Z] | [A] | [ISSUE] |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Common Issues**: [High commission/win ratio? Low volatility? Choppy market?]

---

## 3. Parameter Optimization Results

### Universal Best Parameters (All Coins)

| Parameter | Optimal Value | Range Tested | Notes |
|-----------|---------------|--------------|-------|
| **ATR Period** | [X] | 8-21 | [Insight] |
| **SL ATR Mult** | [X] | 0.8-1.5 | [Insight] |
| **TP ATR Mult** | [X] | 1.2-2.5 | [Insight] |
| **BE Trigger** | [X]×ATR | 0.3-0.7 | [Insight] |
| **BE Lock** | [X]×ATR | 0.2-0.5 | [Insight] |
| **Cooldown** | [X] bars | 0-10 | [Insight] |

**Insight**: [Do all coins agree on these values? Or is per-coin optimization needed?]

---

### Per-Coin Optimal Parameters (Top 5)

#### RIVERUSDT
```yaml
atr_period: [X]
sl_atr: [X]
tp_atr: [X]
be_trigger: [X]
be_lock: [X]
```
**Performance**: [N] trades, [X]% win rate, $[Y] profit, [Z] SQN

#### KITEUSDT
```yaml
atr_period: [X]
sl_atr: [X]
tp_atr: [X]
be_trigger: [X]
be_lock: [X]
```
**Performance**: [N] trades, [X]% win rate, $[Y] profit, [Z] SQN

#### 1000PEPEUSDT
```yaml
atr_period: [X]
sl_atr: [X]
tp_atr: [X]
be_trigger: [X]
be_lock: [X]
```
**Performance**: [N] trades, [X]% win rate, $[Y] profit, [Z] SQN

[... repeat for other top coins ...]

---

## 4. Machine Learning Analysis

### XGBoost Meta-Labeling Results

**Model Performance**:
- Train Accuracy: [X]%
- Test Accuracy: [X]%
- Precision: [X]%
- Recall: [X]%
- F1 Score: [X]

**Insight**: [Can XGBoost predict trade outcomes better than random? If accuracy > 55%, meta-labeling adds value.]

---

### Feature Importance (SHAP Values)

| Rank | Feature | SHAP Value | Description |
|------|---------|------------|-------------|
| 1 | stoch_9_3 | [X] | Entry trigger stochastic |
| 2 | atr_pct | [X] | ATR as % of price (volatility) |
| 3 | ema_distance_34_50 | [X] | Cloud 3 width |
| 4 | rsi_14 | [X] | RSI momentum |
| 5 | volume_ratio | [X] | Current volume / avg volume |
| 6 | stoch_14_3 | [X] | Confirmation stochastic |
| 7 | cloud3_direction | [X] | Cloud 3 directional bias |
| 8 | bbw_pct | [X] | Bollinger Band width |
| 9 | macd_histogram | [X] | MACD momentum |
| 10 | stoch_40_3 | [X] | Divergence stochastic |

**Insight**: [Which features matter most? Are stochastics more important than EMAs? Does volume help?]

---

### SHAP Summary Plot

[Insert SHAP summary plot image here]

**Interpretation**: [What do SHAP values reveal? Red = positive contribution, blue = negative. High SHAP = important feature.]

---

## 5. MFE/MAE Analysis

### Loser Classification (Sweeney Framework)

| Class | Count | % of Losers | Avg MFE | Avg MAE | Recommendation |
|-------|-------|-------------|---------|---------|----------------|
| **A** (Small MFE, immediate loss) | [N] | [X]% | [Y]% | [Z]% | Bad entries — improve signal filter |
| **B** (Medium MFE, gave back) | [N] | [X]% | [Y]% | [Z]% | Raise BE earlier |
| **C** (Large MFE, gave back all) | [N] | [X]% | [Y]% | [Z]% | Add trailing TP or tighter BE |
| **D** (No MFE, straight to SL) | [N] | [X]% | [Y]% | [Z]% | Wrong direction — check Cloud 3 filter |

**LSG% (Losers Saw Green)**: [X]% of losers were profitable at some point

**Insight**: [If LSG% is high (>60%), BE raise is the #1 optimization lever. If low (<40%), focus on signal quality.]

---

### MFE/MAE Distribution

[Insert MFE vs MAE scatter plot here]

**Interpretation**: [Are losers clustered near a certain MAE%? Do winners reach consistent MFE%?]

---

## 6. Walk-Forward Validation

### OOS Performance (Out-of-Sample)

| Window | Train Period | Test Period | Train Sharpe | Test Sharpe | Train SQN | Test SQN |
|--------|--------------|-------------|--------------|-------------|-----------|----------|
| 1 | [DATES] | [DATES] | [X] | [Y] | [A] | [B] |
| 2 | [DATES] | [DATES] | [X] | [Y] | [A] | [B] |
| 3 | [DATES] | [DATES] | [X] | [Y] | [A] | [B] |
| 4 | [DATES] | [DATES] | [X] | [Y] | [A] | [B] |
| 5 | [DATES] | [DATES] | [X] | [Y] | [A] | [B] |
| 6 | [DATES] | [DATES] | [X] | [Y] | [A] | [B] |

**Average**:
- Train Sharpe: [X], Test Sharpe: [Y] (degradation: [Z]%)
- Train SQN: [X], Test SQN: [Y] (degradation: [Z]%)

**Insight**: [Is OOS performance consistent? If test metrics degrade >30%, parameters are overfit.]

---

## 7. Risk Method Comparison

Tested 4 BE strategies:

| Method | Win Rate | Avg R | Total Profit | SQN | Sharpe | LSG% |
|--------|----------|-------|--------------|-----|--------|------|
| **1. BE at 0 ATR** (pure breakeven) | [X]% | [Y]R | $[Z] | [A] | [B] | [C]% |
| **2. BE + fees** (0.3 ATR lock) | [X]% | [Y]R | $[Z] | [A] | [B] | [C]% |
| **3. BE + fees + trail TP** | [X]% | [Y]R | $[Z] | [A] | [B] | [C]% |
| **4. BE + trail TP** (no fee buffer) | [X]% | [Y]R | $[Z] | [A] | [B] | [C]% |

**Winner**: [METHOD] — [REASON]

**Insight**: [Does trailing TP help? Does locking at BE+fees vs pure BE make a difference?]

---

## 8. Commission Analysis

### Commission Impact

| Metric | Value |
|--------|-------|
| **Gross Profit** (before commission) | $[X] |
| **Total Commission** | $[X] |
| **Net Profit** (after commission) | $[X] |
| **Commission as % of Gross** | [X]% |
| **Commission per Trade** | $[X] |
| **Rebate** (70% account) | $[X] |
| **Net Commission** (after rebate) | $[X] |

**Vince (rebate farming)**: Commission net cost = $[X], rebate revenue = $[Y], net = $[Z]

**Vicky (no rebates)**: Commission net cost = $[X], copy trading revenue (12%) = $[Y], net = $[Z]

**Insight**: [Is rebate farming still profitable? For Vicky (no rebates), is 55%+ win rate achievable?]

---

## 9. Comparison with v3.7.1

### Performance Deltas

| Metric | v3.7.1 | v3.8 | Change |
|--------|--------|------|--------|
| **Total Trades** | [N] | [N] | [±X]% |
| **Win Rate** | [X]% | [Y]% | [±Z]% |
| **Total Profit** | $[X] | $[Y] | [±Z]% |
| **SQN** | [X] | [Y] | [±Z]% |
| **Sharpe** | [X] | [Y] | [±Z]% |
| **Max DD** | [X]% | [Y]% | [±Z]% |

**Insight**: [Did Cloud 3 filter improve win rate? Did ATR-based BE improve SQN? Trade-offs?]

---

## 10. Visualizations

### Equity Curve (All Coins Combined)

[Insert interactive Plotly equity curve here]

**Key Events**: [Mark major drawdowns, equity peaks, etc.]

---

### Drawdown Plot

[Insert drawdown plot here]

**Max Drawdown**: [X]% on [DATE]

---

### Parameter Heatmap (BE Trigger vs BE Lock)

[Insert 2D heatmap: x=be_trigger, y=be_lock, color=SQN]

**Insight**: [What's the optimal BE trigger/lock combo? Is there a plateau?]

---

## 11. Recommendations

### Immediate Actions
1. **Update v3.8 defaults** to optimal parameters:
   ```pine
   i_beTrigger = [X]
   i_beLock = [X]
   i_slMult = [X]
   i_tpMult = [X]
   ```

2. **Filter out underperforming coins**: [LIST] showed negative SQN — avoid or adjust parameters.

3. **Implement XGBoost meta-labeling**: Test accuracy [X]% → can skip [Y]% of losing trades.

---

### v3.9 Features to Build
1. **Trailing TP**: If risk method #3 outperformed, implement TP trail from max_price.
2. **Cloud 2 exit**: If MFE/MAE shows losers give back gains late, add hard close on Cloud 2 flip.
3. **Stepped BE raise**: Multiple BE levels (0.5 ATR → 0.3 lock, 1.0 ATR → 0.8 lock, etc.)

---

### Long-Term Research
1. **Multi-timeframe**: Does 5m + 15m confluence improve win rate?
2. **Session filters**: For Andy (FTMO), block Asian session?
3. **Ensemble models**: XGBoost + LSTM voting → better accuracy?

---

## 12. Conclusions

[Summarize key findings in 3-5 bullet points]

**Next Steps**:
1. Update Pine Script v3.8 with optimal parameters
2. Deploy to live testing (paper trading first)
3. Run Vince analysis quarterly to adapt to changing market conditions

---

**Generated by**: Vince ML Platform v1.0
**Report Date**: [DATE]
**Contact**: [YOUR NAME]

---

## Appendix: Full Data Files

- **Per-coin results CSV**: `results/per_coin_results.csv`
- **All trades CSV**: `results/all_trades.csv`
- **Optimal parameters YAML**: `results/optimal_parameters.yaml`
- **XGBoost model**: `results/xgboost_model.pkl`
- **SHAP values**: `results/shap_values.pkl`
- **Equity curve HTML**: `results/equity_curve.html`
