# Build Journal — 2026-02-09

## Book Analysis Complete — 9 Books Scored

| Book | Author | Rating | Key Takeaway |
|------|--------|--------|-------------|
| Maximum Adverse Excursion | Sweeney | 9/10 | MFE/MAE framework — gold standard for exit optimization |
| Advances in Financial ML | De Prado | 9/10 | Triple Barrier, Meta-Labeling, Purged CV, Feature Importance > Backtesting |
| ML for Algorithmic Trading | Jansen | 8/10 | SHAP values, XGBoost/LightGBM, purged CV, intraday boosting, Alpha Factor Library |
| Trade Your Way to Financial Freedom | Van Tharp | 7/10 | R-multiples, SQN, expectunity, position sizing = 90% of variance |
| AI in Finance | Hilpisch | 5/10 | ATR×leverage SL/TSL/TP backtesting, RNN 65% OOS, debunks normality |
| Reinforcement Learning for Finance | Hilpisch | 4/10 | DQL trading env, min_performance gate = FTMO drawdown |
| Python for Algo Trading | Hilpisch | 3/10 | Kelly Criterion, max drawdown calc. Rest platform-specific |
| Listed Volatility & Variance Derivatives | Hilpisch | 1/10 | Pricing variance swaps — zero relevance |
| Derivatives Analytics with Python | Hilpisch | 1/10 | Options pricing (FFT, Monte Carlo) — zero relevance |

---

## VINCE Upgrade Plan — What the Books Teach Us

### What VINCE Already Has (Sweeney 9/10)
The MFE/MAE framework is already the backbone:
- Per-trade MFE/MAE/ETD/MinFE tracking
- Loser classification (A/B/C/D by MFE depth)
- BE trigger optimization (net impact curve)
- 8 standard diagnostic charts
- R-multiple normalization
- Draw zone separation (commission casualties)

### What Books Add to VINCE

#### 1. ATR × Leverage Risk Gate (from Hilpisch "AI in Finance" Ch 11)
**Problem**: Our SL/TP is set in ATR multiples, but we don't gate entries based on ATR regime.
**Insight**: When ATR × leverage > threshold (e.g., 25% of equity), noise exceeds SL distance → stop-outs are random, not signal failures.
**VINCE action**: Add `atr_regime` feature to trade data. XGBoost can learn: "trades entered when ATR is >X% of price have Y% lower win rate." This becomes a kill switch — don't trade when ATR regime is unfavorable.

#### 2. min_performance Drawdown Gate (from Hilpisch "RL for Finance" Ch 6)
**Problem**: VINCE optimizes parameters but doesn't enforce drawdown limits during optimization.
**Insight**: The DQL agent's `min_performance` parameter kills episodes when equity drops below threshold. Maps directly to:
- FTMO: 3% daily / 10% total = hard kill
- Crypto: voluntary drawdown limit to protect capital
**VINCE action**: Add drawdown constraint to Optuna objective function:
```python
def objective(trial):
    # ... run backtest with trial params ...
    if max_drawdown > 0.10:  # 10% max drawdown
        return float('-inf')  # Kill this trial
    return sharpe_ratio
```
This ensures VINCE never recommends parameters that blow through drawdown limits.

#### 3. Non-Normal Return Awareness (from Hilpisch "AI in Finance" Ch 4)
**Problem**: Kelly Criterion and Sharpe ratio assume normal returns. Our returns are non-normal (leverage + SL/TP = guaranteed non-normal payoffs).
**Insight**: Ch 4 proves financial returns are NOT normally distributed. Ch 11 proves leverage + SL/TP orders make this WORSE — highly asymmetric, nonlinear payoffs.
**VINCE action**:
- Use Sortino ratio (downside-only risk) instead of Sharpe as primary objective
- Use modified Kelly (half-Kelly or fractional) for position sizing
- Monte Carlo validation: shuffle trade ORDER, not just bootstrap — captures serial correlation

#### 4. Data Augmentation for Small Samples (from Hilpisch "RL for Finance" Ch 4)
**Problem**: Walk-forward on 3 months gives thin OOS windows (1 month = ~1300 trades on 5m).
**Insight**: Noisy data + Monte Carlo simulation generates synthetic training data that preserves statistical properties while expanding the dataset.
**VINCE action**: For Optuna walk-forward, generate synthetic IS data by:
- Adding Gaussian noise to candles (preserves structure, expands sample)
- Monte Carlo shuffling of trade sequences for robustness testing
- Bootstrap confidence intervals on OOS equity curves

#### 5. Feature Engineering for Direction Prediction (from Hilpisch "AI in Finance" Ch 8)
**Problem**: VINCE currently classifies losers AFTER the fact. Could it PREDICT losers BEFORE entry?
**Insight**: RNN with features (return, SMA delta, momentum, min/max, volatility) achieves 65% OOS direction accuracy on EUR/USD.
**VINCE action**: Add pre-entry features to XGBoost classifier:
```python
pre_entry_features = [
    'stoch_9_value',           # Raw K at entry
    'stoch_14_value',          # Confirmation stoch
    'stoch_40_value',          # Divergence stoch
    'stoch_60_value',          # Macro stoch
    'cloud3_distance',         # Price distance from Cloud 3
    'cloud2_slope',            # Cloud 2 momentum (rising/falling)
    'atr_percentile',          # ATR relative to recent history
    'volume_ratio',            # Volume vs 20-bar average
    'recent_signal_count',     # Signal density (flipping frequency)
    'time_since_last_loss',    # Bars since last losing trade
    'consecutive_losses',      # Current losing streak
]
target = 'is_winner'  # Binary: did this trade win?
```
Even 55% prediction accuracy saves money: skip the bottom 10% of predicted losers.

#### 6. Options Flow as Regime Filter (from Glassnode article)
**Problem**: Four Pillars trades blind to macro sentiment.
**Insight**: IV spikes, negative VRP, and put skew steepening all precede major drawdowns. The Feb 2026 BTC dump from $98K→$72K coincided with VRP flipping to -5.
**VINCE action**: If Glassnode/Deribit API data is available:
- Add `btc_iv_rank` (current IV vs 30-day range) as a feature
- Add `put_call_skew` as a feature
- XGBoost can learn: "trades entered when IV_rank > 80 lose at 2x the normal rate"
- For Andy: VIX serves the same purpose for index trades

---

## Priority Order for VINCE Upgrades

| Priority | Upgrade | Effort | Impact | Blocked By |
|----------|---------|--------|--------|------------|
| 1 | Drawdown constraint in Optuna objective | Low | High | Nothing — can add now |
| 2 | Pre-entry XGBoost features (stoch values, ATR percentile) | Medium | High | Needs enriched trade data |
| 3 | ATR regime gate | Low | Medium | Nothing — simple threshold |
| 4 | Sortino instead of Sharpe as primary objective | Low | Medium | Nothing |
| 5 | Data augmentation (noise + Monte Carlo) | Medium | Medium | Nothing |
| 6 | Options flow regime filter | High | High | Glassnode/Deribit API integration |

### What's NOT Worth Doing (from book analysis)
- **RNN for price prediction**: Hilpisch admits it's just "today's price shifted by one bar." Waste of GPU.
- **DQL trading agent**: Binary actions, no position sizing, no TCs. Our backtester is already better.
- **Options pricing models**: FFT, Black-Scholes, Monte Carlo for derivatives — irrelevant to directional trading.
- **Variance swap replication**: Institutional product, not applicable.

---

## Andy Project Created

Separate project skill for FTMO prop trading ($200K, cTrader):
- **File**: `.claude/skills/andy/andy.md`
- **Execution plan**: ANDY-1 through ANDY-9
- Shares strategy DNA with Four Pillars but separate project with own rules

---

## Tools Installed
- `pymupdf4llm` — PDF-to-markdown extractor (better than pypdf for tables/formatting)
- Full book analysis toolchain: `ebooklib` + `beautifulsoup4` + `pypdf` + `pymupdf4llm`

---

## Status at End of Day

### Completed Today
- 3 books analyzed (Derivatives Analytics 1/10, AI in Finance 5/10, RL for Finance 4/10 — recap)
- De Prado "Advances in Financial ML" analyzed — **9/10** (Triple Barrier, Meta-Labeling, Purged CV, Feature Importance)
- Andy project skill created and separated from Four Pillars
- All project skills updated (four-pillars-project, vince-ml, andy)
- VINCE upgrade plan synthesized from all 7 books
- Options flow macro filter added to both project roadmaps (WS4G, ANDY-8)
- pymupdf4llm installed for future PDF analysis
- **PyTorch CUDA installed**: `torch-2.10.0+cu130` verified on RTX 3060 12GB (CUDA 13.0, cuDNN 9.12.0)
- **Data refetch complete**: 99 coins re-fetched, 0 failures. Cache now 399 files / 1.74 GB. RIVER + SAND restored.

### Ready to Start
- Full 399-coin backtest on 5m (data + backtester + GPU all ready)
- WS4 ML optimizer (PyTorch installed, Optuna + XGBoost ready)
- WS4B MFE/MAE depth analysis
- De Prado concepts to implement: Meta-Labeling, Purged CV, Triple Barrier comparison
