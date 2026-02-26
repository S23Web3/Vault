# Three System Personas

## Vince (Four Pillars + ML + Rebates)
- **Commission**: 0.08% = $8/side on $10K notional (20x leverage)
- **Rebates**: Kept by user for community giveaways
- **Goal**: ~3000 trades/month across multiple coins, flat equity, rebates = profit
- **Timeframe**: 5m optimal (ALL 5 low-price coins profitable)
- **ML focus**: XGBoost meta-labeling, SHAP values, purged CV
- **Risk methods to test**:
  1. Move SL to breakeven
  2. BE + fees
  3. BE + fees + trailing TP
  4. BE + trailing TP
- **Data**: Full 3-month 1m/5m Bybit data for 9 coins (PROJECTS/four-pillars-backtester/)

## Vicky (Four Pillars - Rebates for Copy Traders)
- **Commission**: 0.08% = $8/side (NO rebates)
- **Revenue**: User earns 12% on copy trading side
- **Goal**: 55%+ win rate, positive expectancy per trade
- **Entry timeframe**: 5m (higher timeframe)
- **Validation timeframe**: Lower timeframe (1m?) to decide dump vs hold
- **Entry logic**: Lower timeframe analysis + higher timeframe confirmation
- **Scalp framework**: Also runs on Market Profile/Volume Profile scalp execution framework
- **Trade volume**: Can make 3000 trades/month across multiple coins
- **ML layer**: Meta-Labeling (XGBoost skip/act on marginal signals) - critical without rebates

## Andy (FTMO Forex/Commodities/Indexes)
- **Goal**: 10%/month on FTMO $200K funded account
- **Drawdown rules**: 3% daily ($6K) / 10% total ($20K)
- **Risk per trade**: 1-2% of account
- **Instruments**: Forex, commodities, indexes (NOT crypto)
- **Scalps**: 24/7 if standalone (includes Asian session)
- **Tools**: TradingView + cTrader + Python automation
- **Frameworks**: 5-block governance + scalp execution (Market Profile/Volume Profile)
- **Status**: Material gathering phase, work later (after Vince/Vicky)
- **Flowcharts**: `.claude/skills/andy/DIRECTIONAL-TRADING-FRAMEWORK.pdf` and `SCALP-EXECUTION-FRAMEWORK.pdf`

## Business Model (Copy Trading)
- **User earns**: 12% on copy trading side (Vicky's trades)
- **Rebates**: User keeps 100% of rebates (Vince's trades) for community giveaways
- **Vicky purpose**: Designed for copy traders who don't get rebates
- **Vince purpose**: User's own trading with rebate optimization
