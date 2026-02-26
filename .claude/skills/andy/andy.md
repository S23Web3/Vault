# Andy — FTMO Prop Trading Project

## Mission
$1,000 from crypto directionals → $200K FTMO challenge → 10%/month → fund vince.ai African academies.

- **vince.ai**: Mini AI academies in African cities — teach people to work with AI, excel their lives
- Finance teachers + hardware (used computers via Prague 8 + Sharjah connects)
- Website: rallypointtoken.com
- **First milestone**: ~$17K in 2 months (1 month to pass challenge + 1 month to first payout) → launch first academy

## The Pipeline

| Step | Action | Cost/Outcome |
|------|--------|-------------|
| 1. Seed | Win $1,000 from crypto directional trades | $1,000 cash |
| 2. Challenge | Buy FTMO $200K 1-step challenge | $999 fee |
| 3. Pass | Hit 10% ($20K) profit target | Funded account |
| 4. Trade | Make 10%/month on $200K | $20K/month simulated |
| 5. Get paid | 80% profit split + fee refund | **$16K/month + $999 back** |
| 6. Scale | After 4 months → 90% split + 25% account growth | $18K+/month, growing |
| 7. Deploy | Fund vince.ai academies | Change lives |

## FTMO $200K Account — Exact Rules

### 1-Step Challenge (Preferred)
| Rule | Value |
|------|-------|
| Challenge Fee | $999 (refunded with first payout) |
| Account Size | $200,000 simulated |
| Profit Target | 10% = $20,000 |
| Max Daily Loss | 3% = $6,000 |
| Max Total Loss | 10% = $20,000 |
| Min Trading Days | None (1-step) |
| Time Limit | Unlimited |
| Best Day Rule | No single day > 50% of total profit |
| Profit Split | 80% (→ 90% with scaling) |
| Platform | **cTrader** (preferred over MT4/MT5) |

### 2-Step Challenge (Backup)
| Rule | Value |
|------|-------|
| Challenge Fee | $1,080 one-time (covers both phases, refunded with first payout) |
| Phase 1 Target | 10% = $20,000 |
| Phase 2 Target | 5% = $10,000 |
| Max Daily Loss | 5% = $10,000 |
| Max Total Loss | 10% = $20,000 |
| Min Trading Days | 4 per phase |
| Time Limit | Unlimited |

### Real Timeline & Income Projection (10%/month)
| Month | Phase | What Happens |
|-------|-------|-------------|
| 1 | Challenge | Pass: hit $20K profit target on $200K |
| 2 | First payout | $16,000 (80%) + $999 fee refund = **$17,000 cash** |
| 3 | Second payout | $16,000 |
| 4 | Third payout | $16,000 (cumulative: **$65,000**) |
| 5+ | Scaling kicks in | 90% split + 25% account growth → $18K+/month |
| 9+ | Account at $250K+ | $22,500/month |

### Scaling Plan (after 4 months + 10% net + 2 payouts)
- Account grows 25% every 4 months
- Profit split upgrades to 90%
- $200K → $250K → $312K → ... → **$2,000,000 cap**
- At $2M cap with 90% and 10%/month: **$180,000/month**

## Key Differences from WEEX/Bybit Crypto
| Factor | WEEX/Bybit (Rebate Farming) | FTMO (Andy) |
|--------|---------------------------|-------------|
| Capital | Own $500 × 20x leverage | Their $200K |
| Commission | 0.06% taker ($12 RT on $10K) | Spread-based (forex) or low commission |
| Risk | Lose your own money | Lose the account → re-challenge ($999) |
| Drawdown rules | None | **3% daily / 10% total — HARD LIMITS** |
| Profit model | Flat equity + rebates | Must WIN trades |
| Trade frequency | ~3000/month | ~100-200/month |
| Instruments | Crypto perpetuals | Forex, indices, commodities, crypto |
| Hours | 24/7 | Market hours (forex ~5 days/week) |
| Platform | TradingView | **cTrader** |
| Best Day Rule | N/A | No day > 50% of total profit |

## Strategy Adaptation for FTMO

### What Changes
1. **Win rate matters** — no rebates to subsidize losses. Every trade must pay for itself
2. **Drawdown management is #1 priority** — 3% daily / 10% total = instant account death
3. **Fewer, higher-quality trades** — not 3000/month, maybe 100-200/month
4. **Position sizing** — 1-2% risk per trade max (Kelly-constrained for FTMO rules)
5. **Instrument selection** — forex/indices may have better signal characteristics
6. **Session filters** — London/NY overlap, avoid Asian session for EUR/USD
7. **No rapid flipping** — every flip costs real P&L
8. **Best Day Rule awareness** — can't spike one day, need consistent daily returns

### What Carries Over
1. **Stochastic confluence** — multi-TF stoch alignment works on any instrument
2. **EMA Cloud structure** — trend identification is universal
3. **ATR-based SL/TP** — volatility-normalized stops work everywhere
4. **MFE/MAE analysis** — Sweeney framework applies to any market
5. **BE raise logic** — even MORE critical with FTMO drawdown rules
6. **Python backtester** — adapt data source, same analysis framework
7. **Loser classification** — A/B/C/D framework for optimizing exits

## Technical Infrastructure
- **Charting**: TradingView (Pine Script signals)
- **Execution**: cTrader (better than MT4/MT5 — modern API, better fills, cAlgo for automation)
- **Backtester**: Python (adapt four-pillars-backtester for forex/index data)
- **Automation path**: TradingView alerts → webhook → cTrader API / cAlgo bot
- **Data sources**: TradingView (charting), Dukascopy/TrueFX (tick data for backtesting)

## Execution Plan

| Workstream | Status | Description |
|------------|--------|-------------|
| ANDY-1 | Pending | Backtest Four Pillars on forex pairs (EUR/USD, GBP/USD, USD/JPY) |
| ANDY-2 | Pending | Backtest on indices (US30, NAS100, SPX500) |
| ANDY-3 | Pending | Position sizing (Kelly constrained by FTMO 3% daily / 10% total) |
| ANDY-4 | Pending | Session filters (London, NY, overlap windows) |
| ANDY-5 | Pending | Best Day Rule compliance |
| ANDY-6 | Pending | Spread/commission impact analysis (forex vs crypto) |
| ANDY-7 | Pending | cTrader API / cAlgo integration |
| ANDY-8 | Pending | Options flow macro filter (VIX/skew for indices, IV for forex) |
| ANDY-9 | Pending | FTMO free trial test run |

## Book Insights for FTMO

| Book | Rating | What Andy Inherits |
|------|--------|--------------------|
| Sweeney "MAE" | 9/10 | MFE/MAE framework, loser classification, BE trigger optimization — even more critical with 10% drawdown limit |
| De Prado "Advances in Financial ML" | 9/10 | Meta-Labeling (skip bad signals), Purged CV (no leakage), Bet Sizing (probability → position size), Triple Barrier (time exit for session trading) |
| Hilpisch "AI in Finance" | 5/10 | ATR regime gate, Sortino over Sharpe (downside risk = FTMO drawdown) |
| Hilpisch "RL for Finance" | 4/10 | min_performance gate = FTMO 3% daily / 10% total drawdown kill switch |
| Jansen "ML for Algo Trading" | 8/10 | SHAP values (per-trade failure explanation), Kelly for multi-asset sizing, intraday boosting strategy, Alpha Factor Library |
| Van Tharp "Trade Your Way" | 7/10 | Position sizing = 90% of variance (FTMO's #1 constraint), SQN metric, percent-risk model (1-2% per trade) |

### De Prado Concepts — FTMO-Critical
1. **Meta-Labeling**: Four Pillars generates signal → XGBoost decides act/skip. For FTMO, skipping marginal signals is survival. A 55% skip accuracy on bad trades could mean the difference between passing and failing the challenge.
2. **Bet Sizing**: Map XGBoost confidence → position size (0.5% to 2% risk). High confidence = full size, marginal = half size. Respects 3% daily drawdown.
3. **Triple Barrier**: Time barrier = session close. If a forex trade hasn't hit SL or TP by session end, close it. Prevents overnight gap risk on funded accounts.
4. **Purged K-Fold CV**: When backtesting forex with overlapping windows, purge training samples that leak into test set. Prevents overfitting.
5. **Sharpe = f(precision, frequency)**: For Andy, p (win rate) matters more than n (trade count) — opposite of rebate farming. At 150 trades/month, need ~55% win rate for Sharpe > 2.

## Related Projects
- [four-pillars-project](..\four-pillars-project\) — crypto rebate farming (shares strategy DNA)
- [four-pillars](..\four-pillars\) — core signal logic
- [pinescript](..\pinescript\) — Pine Script v6
- [vince-ml](..\vince-ml\) — MFE/MAE optimization framework
