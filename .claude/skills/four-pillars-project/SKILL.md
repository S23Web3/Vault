---
name: four-pillars-project
description: Master project skill for the Four Pillars Trading System. References all sub-skills. Use this when working on the overall project, switching between Pine Script and Python, or needing cross-cutting context. Triggers on terms like "four pillars project", "master plan", "backtester project", "WS1", "WS2", "WS3", "WS4", "WS5", "checkpoint".
---

# Four Pillars Project — Master Skill

## Sub-Skills

| Skill | Domain | When to Load |
|-------|--------|-------------|
| `pinescript` | Pine Script v6 language & patterns | Writing/editing .pine files |
| `four-pillars` | Strategy logic, commission math, version history | Strategy decisions, signal logic, lessons |
| `vince-ml` | ML optimizer, MFE/MAE analysis, dashboard design | ML work, trade analysis, optimization (WS4+) |

**Related project:** [`andy`](..\andy\andy.md) — FTMO prop trading ($200K, cTrader). Separate project, shares strategy DNA.

## Execution Plan

Full plan at: `C:\Users\User\.claude\plans\warm-waddling-wren.md`

### Crypto (WEEX/Bybit Rebate Farming)
| Workstream | Status | Description |
|------------|--------|-------------|
| WS1 | Done | Skill file optimization |
| WS2 | Pending | Progress review documents (07-BUILD-JOURNAL) |
| WS3A | Done | Data pipeline (Bybit v5 API → Parquet cache) |
| WS3B | Done | Signal engine (Four Pillars ported to Python) |
| WS3C | Done | Backtest engine (bar-by-bar, cash_per_order commission) |
| WS3D | Pending | Additional exit strategies |
| WS3E | Pending | Streamlit GUI |
| WS4 | In Progress | VINCE: ML optimizer (Optuna + XGBoost + PyTorch GPU) |
| WS4A | Done | Mass backtest — 5 low-price coins, 5m optimal (+$97K/3mo) |
| WS4B | Pending | MFE/MAE depth analysis + loser classification |
| WS4C | Pending | BE trigger optimization (net impact curve) |
| WS4D | Pending | Streamlit dashboard v2 (5-tab professional layout) |
| WS4E | Pending | Optuna parameter sweep + walk-forward validation |
| WS4F | Pending | XGBoost feature importance (predict losers) |
| WS4G | Pending | Options flow macro filter (IV, skew, VRP from Glassnode/Deribit) |
| WS5 | Pending | Stable v4 + Monte Carlo validation |

## Python Backtester Results (5m, 3 months)

| Coin | Net P&L | Trades | $/Trade | Optimal BE |
|------|---------|--------|---------|-----------|
| RIVERUSDT | +$55,900 | 4,006 | $13.95 | BE$4 |
| KITEUSDT | +$15,000 | 4,219 | $3.56 | BE$2 |
| 1000PEPEUSDT | +$10,400 | 4,108 | $2.53 | BE$2 |
| SANDUSDT | +$8,600 | 3,872 | $2.22 | BE$6 |
| HYPEUSDT | +$7,200 | 4,078 | $1.77 | BE$10 |
| **Total** | **+$97,060** | **20,283** | **$4.79** | — |

- 5m timeframe optimal for ALL coins (most negative on 1m)
- Commission: $6/side cash_per_order (0.06% on $10K notional)
- ATR/price ratio determines profitability — low-price coins win

## Book Analysis Log

| Book | Author | Rating | Key Takeaway |
|------|--------|--------|-------------|
| Maximum Adverse Excursion | Sweeney | 9/10 | MFE/MAE framework — the gold standard for exit optimization |
| Python for Algo Trading | Hilpisch | 3/10 | Kelly Criterion, max drawdown calc. Rest is platform-specific |
| Listed Volatility & Variance Derivatives | Hilpisch | 1/10 | About pricing variance swaps — zero relevance |
| Reinforcement Learning for Finance | Hilpisch | 4/10 | DQL trading env, min_performance gate = FTMO drawdown. No TCs |
| Derivatives Analytics with Python | Hilpisch | 1/10 | Options pricing (FFT, Monte Carlo, delta hedging) — zero relevance |
| AI in Finance | Hilpisch | 5/10 | Best Hilpisch — ATR×leverage SL/TSL/TP backtesting, RNN 65% OOS, debunks normality |
| Advances in Financial ML | De Prado | 9/10 | Triple Barrier, Meta-Labeling, Purged CV, Feature Importance > Backtesting, Bet Sizing |
| ML for Algorithmic Trading | Jansen | 8/10 | SHAP values, XGBoost/LightGBM comparison, purged CV, intraday boosting, Alpha Factor Library |
| Trade Your Way to Financial Freedom | Van Tharp | 7/10 | R-multiples, SQN, expectunity, "entries least important", position sizing = 90% of variance |

## Key Project Files

| File | Purpose |
|------|---------|
| `.claude/skills/pinescript/` | Pine Script v6 language skill |
| `.claude/skills/four-pillars/` | Strategy knowledge skill |
| `.claude/skills/four-pillars-project/` | This master skill |
| `.claude/skills/andy/` | FTMO prop trading (separate project) |
| `.claude/skills/vince-ml/` | ML optimizer, MFE/MAE, dashboard |
| `02-STRATEGY/Indicators/` | Pine Script strategy/indicator files |
| `02-STRATEGY/Indicators/FOUR-PILLARS-V3.8-PLAN.md` | v3.8 plan (ATR-based BE) |
| `PROJECTS/four-pillars-backtester/` | Python backtester |
| `PROJECTS/trading-dashboard/code/dashboard.py` | Streamlit GUI base |
| `07-BUILD-JOURNAL/` | Progress review documents |
| `07-TEMPLATES/` | Trade data CSVs, analysis notebooks |

## Git

- **Repo:** https://github.com/S23Web3/ni9htw4lker
- **Identity:** S23Web3
