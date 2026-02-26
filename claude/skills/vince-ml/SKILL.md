# VINCE — ML Strategy Optimizer Skill

## Trigger Terms
"vince", "machine learning", "ML optimizer", "MFE", "MAE", "ETD", "loser analysis", "LSG depth", "walk-forward", "parameter optimization", "optuna", "xgboost", "backtest dashboard", "trade classification", "BE optimization", "breakeven optimization", "exit efficiency", "R-multiple", "system quality"

## Purpose
Knowledge base for the VINCE AI strategy optimizer — the machine learning layer on top of the Four Pillars backtester. Covers MFE/MAE professional analysis, dashboard design, parameter optimization, walk-forward methodology, and trade classification.

## Architecture
- **Runtime**: Local Python on RTX 3060 12GB (CUDA 13.1, PyTorch 2.10+cu130)
- **Optimizer**: Optuna (Bayesian) + XGBoost (feature importance) + PyTorch (GPU)
- **Dashboard**: Streamlit on localhost:8501
- **Data**: 370+ coins, 3-month 1m candles in Parquet, resampled to 5m for backtesting
- **Backtester**: Custom engine matching v3.7.1 Pine Script logic

## References
- [MFE/MAE Professional Framework](references/mfe-mae-framework.md)
- [Dashboard Design Standard](references/dashboard-design.md)
- [Optimization & Walk-Forward](references/optimization.md)
- [Algo Community Landscape](references/algo-community.md)

## Key Principles
1. **Data first, architecture later** — Run analysis, see results, then ask questions
2. **Questions, not answers** — Surface insights that prompt the trader to investigate
3. **MFE depth over binary LSG** — "How green?" not just "saw green?"
4. **Walk-forward or don't trust it** — Every Optuna result must be validated OOS
5. **R-multiples for comparison** — Normalize everything to risk units
6. **ETD is the missing metric** — End Trade Drawdown reveals systematic profit giveback
7. **BE trigger is a tradeoff curve** — Losers saved vs winners killed, find the peak
