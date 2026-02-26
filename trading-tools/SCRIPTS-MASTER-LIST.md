# Trading Tools — Master Script List

**Location**: `trading-tools/`
**Purpose**: Centralized repository for all trading analysis, backtesting, ML, and live trading scripts
**Date**: 2026-02-09

---

## Status Legend
- ✅ **Complete** — Script exists and tested
- 🔄 **In Progress** — Partially built
- 📋 **Planned** — Not yet started
- ⏸️ **Paused** — Deferred for later

---

## 1. Data Management

### 1.1 Data Fetching
| Script | Status | Purpose | Exchange |
|--------|--------|---------|----------|
| `data/fetcher.py` | ✅ | Fetch historical OHLCV data | Bybit |
| `data/bingx_fetcher.py` | 📋 | Fetch historical data | BingX |
| `data/weex_fetcher.py` | 📋 | Fetch historical data | WEEX |
| `data/unified_fetcher.py` | 📋 | Multi-exchange wrapper | All |
| `scripts/fetch_data.py` | ✅ | CLI for data fetching | Bybit |

### 1.2 Data Processing
| Script | Status | Purpose |
|--------|--------|---------|
| `resample_timeframes.py` | ✅ | Convert 1m → 5m/15m/1h candles |
| `data/data_cleaner.py` | 📋 | Remove gaps, outliers, duplicates |
| `data/data_validator.py` | 📋 | Validate OHLCV integrity |
| `data/data_merger.py` | 📋 | Merge multi-exchange data |

### 1.3 Data Storage
| Script | Status | Purpose |
|--------|--------|---------|
| `data/cache_manager.py` | 📋 | Manage parquet cache |
| `data/database.py` | 📋 | PostgreSQL/TimescaleDB integration |
| `data/cloud_sync.py` | 📋 | S3/GCS backup |

---

## 2. Indicators & Signals

### 2.1 Four Pillars Indicators
| Script | Status | Purpose |
|--------|--------|---------|
| `signals/stochastic.py` | 🔄 | 4 stochastics (9-3, 14-3, 40-3, 60-10) |
| `signals/ripster_clouds.py` | 🔄 | EMA Clouds 2/3/4/5 |
| `signals/atr.py` | 🔄 | 14-period ATR |
| `signals/volume.py` | 🔄 | Volume analysis |

### 2.2 Four Pillars Signal Generation
| Script | Status | Purpose |
|--------|--------|---------|
| `signals/stage_machine.py` | 📋 | Stage 1/2 state machine |
| `signals/signal_generator.py` | 📋 | A/B/C signal logic |
| `signals/cloud3_filter.py` | 📋 | Directional filter (v3.8) |
| `signals/re_entry.py` | 📋 | Cloud 2 re-entry logic |

### 2.3 Additional Indicators (TA-Lib)
| Script | Status | Purpose |
|--------|--------|---------|
| `signals/talib_indicators.py` | 📋 | RSI, CCI, MFI, MACD, BBW, OBV, ADOSC |
| `signals/market_profile.py` | 📋 | Volume/Market Profile (for Vicky/Andy) |
| `signals/vwap.py` | 📋 | VWAP + anchored VWAP |

---

## 3. Strategy Implementations

### 3.1 Pine Script (TradingView)
| Script | Status | Purpose |
|--------|--------|---------|
| `pine/four_pillars_v3_7_1_strategy.pine` | ✅ | Current production version |
| `pine/four_pillars_v3_8_strategy.pine` | 📋 | Cloud 3 filter + ATR BE |
| `pine/four_pillars_v3_8.pine` | 📋 | Indicator only (no strategy calls) |

### 3.2 Python Strategy (for Vince)
| Script | Status | Purpose |
|--------|--------|---------|
| `strategies/four_pillars_v3_8.py` | 📋 | Main strategy class |
| `strategies/indicators.py` | 📋 | Shared indicator calculations |
| `strategies/signal_machine.py` | 📋 | Stage 1/2 logic |
| `strategies/position_manager.py` | 📋 | Position sizing, SL/TP |
| `strategies/be_raise.py` | 📋 | ATR-based BE logic |

---

## 4. Backtesting Engine

### 4.1 Core Backtester
| Script | Status | Purpose |
|--------|--------|---------|
| `engine/backtester.py` | ✅ | Main backtesting engine |
| `engine/position.py` | ✅ | Position tracking |
| `engine/commission.py` | ✅ | Commission calculation |
| `engine/metrics.py` | ✅ | Performance metrics |

### 4.2 Backtesting Types
| Script | Status | Purpose |
|--------|--------|---------|
| `backtester/vectorized.py` | 📋 | Fast vectorized backtest |
| `backtester/event_based.py` | 📋 | Detailed event-by-event |
| `backtester/walk_forward.py` | 📋 | Walk-forward validation |

### 4.3 Exit Strategies
| Script | Status | Purpose |
|--------|--------|---------|
| `exits/static_atr.py` | ✅ | Fixed ATR SL/TP |
| `exits/avwap_trail.py` | ✅ | AVWAP trailing SL |
| `exits/cloud_trail.py` | ✅ | Cloud 3/4 trailing SL |
| `exits/phased.py` | ✅ | Phased exit (scale out) |
| `exits/atr_be_raise.py` | 📋 | ATR-based BE raise (v3.8) |
| `exits/mfe_mae_tracker.py` | 📋 | MFE/MAE tracking |

---

## 5. Optimization & Analysis

### 5.1 Parameter Optimization
| Script | Status | Purpose |
|--------|--------|---------|
| `optimizer/grid_search.py` | ✅ | Grid search optimizer |
| `optimizer/bayesian.py` | ✅ | Bayesian optimization |
| `optimizer/monte_carlo.py` | ✅ | Monte Carlo simulation |
| `optimizer/genetic.py` | 📋 | Genetic algorithm |
| `optimizer/parameter_sweep.py` | 📋 | Multi-parameter sweep |

### 5.2 ML-Based Optimization
| Script | Status | Purpose |
|--------|--------|---------|
| `optimizer/ml_regime.py` | ✅ | ML regime detection |
| `ml/xgboost_meta_labeling.py` | 📋 | Meta-labeling (skip/take/size) |
| `ml/pytorch_pattern.py` | 📋 | Pattern recognition NN |
| `ml/feature_engineering.py` | 📋 | Feature extraction |
| `ml/shap_analysis.py` | 📋 | SHAP feature importance |

### 5.3 Risk Analysis
| Script | Status | Purpose |
|--------|--------|---------|
| `analysis/risk_metrics.py` | 📋 | Sharpe, Sortino, Calmar, SQN |
| `analysis/drawdown.py` | 📋 | Max DD, consecutive losses |
| `analysis/r_multiples.py` | 📋 | R-multiple analysis (Van Tharp) |
| `analysis/mfe_mae.py` | 📋 | MFE/MAE analysis (Sweeney) |
| `analysis/loser_classification.py` | 📋 | Classify losers (A/B/C/D) |

---

## 6. Vince ML Pipeline

### 6.1 Data Preparation
| Script | Status | Purpose |
|--------|--------|---------|
| `vince/data_prep.py` | 📋 | Load 5m data, calculate indicators |
| `vince/feature_engineering.py` | 📋 | Create 21+ features |
| `vince/normalization.py` | 📋 | Z-score normalization |

### 6.2 Labeling
| Script | Status | Purpose |
|--------|--------|---------|
| `vince/triple_barrier.py` | 📋 | Triple Barrier labeling |
| `vince/mfe_mae_labels.py` | 📋 | Label by MFE/MAE |

### 6.3 Model Training
| Script | Status | Purpose |
|--------|--------|---------|
| `vince/xgboost_trainer.py` | 📋 | Train meta-labeling model |
| `vince/pytorch_trainer.py` | 📋 | Train neural network |
| `vince/purged_cv.py` | 📋 | Purged K-fold CV (De Prado) |

### 6.4 Analysis & Reporting
| Script | Status | Purpose |
|--------|--------|---------|
| `vince/walk_forward.py` | 📋 | Walk-forward validation |
| `vince/parameter_sweep.py` | 📋 | Grid search optimal params |
| `vince/risk_methods.py` | 📋 | Compare 4 BE strategies |
| `vince/generate_report.py` | 📋 | Comprehensive results |
| `vince/shap_explainer.py` | 📋 | SHAP values + plots |

### 6.5 Utilities
| Script | Status | Purpose |
|--------|--------|---------|
| `vince/utils.py` | 📋 | Shared utilities |
| `vince/config.yaml` | 📋 | Hyperparameters |
| `vince/requirements.txt` | 📋 | Dependencies |

---

## 7. Live Trading Bot

### 7.1 Exchange Connections
| Script | Status | Purpose |
|--------|--------|---------|
| `live/bingx_client.py` | 📋 | BingX REST + WebSocket |
| `live/weex_client.py` | 📋 | WEEX REST + WebSocket |
| `live/bybit_client.py` | ⏸️ | Bybit REST + WebSocket (paused) |
| `live/unified_client.py` | 📋 | Multi-exchange wrapper |

### 7.2 Real-Time Data
| Script | Status | Purpose |
|--------|--------|---------|
| `live/websocket_handler.py` | 📋 | WebSocket connection manager |
| `live/kline_aggregator.py` | 📋 | Aggregate 1m → 5m in real-time |
| `live/order_book.py` | 📋 | Order book tracking |

### 7.3 Trading Engine
| Script | Status | Purpose |
|--------|--------|---------|
| `live/trading_bot.py` | 📋 | Main bot orchestrator |
| `live/signal_detector.py` | 📋 | Real-time signal detection |
| `live/order_manager.py` | 📋 | Order placement/cancellation |
| `live/position_tracker.py` | 📋 | Track open positions |
| `live/risk_manager.py` | 📋 | Real-time risk checks |

### 7.4 Execution & Safety
| Script | Status | Purpose |
|--------|--------|---------|
| `live/order_execution.py` | 📋 | Smart order routing |
| `live/slippage_model.py` | 📋 | Model slippage |
| `live/circuit_breaker.py` | 📋 | Emergency stop |
| `live/heartbeat.py` | 📋 | Connection monitoring |

### 7.5 Paper Trading
| Script | Status | Purpose |
|--------|--------|---------|
| `live/paper_trading.py` | 📋 | Simulated trading |
| `live/mock_exchange.py` | 📋 | Mock exchange for testing |

---

## 8. Dashboard & Monitoring

### 8.1 Backtesting Dashboard
| Script | Status | Purpose |
|--------|--------|---------|
| `scripts/dashboard.py` | ✅ | Backtest results viewer |
| `dashboard/streamlit_app.py` | 📋 | Streamlit dashboard |
| `dashboard/plotly_charts.py` | 📋 | Interactive charts |

### 8.2 Live Trading Dashboard
| Script | Status | Purpose |
|--------|--------|---------|
| `dashboard/live_monitor.py` | 📋 | Real-time position monitor |
| `dashboard/pnl_tracker.py` | 📋 | P&L tracking |
| `dashboard/alerts.py` | 📋 | Discord/Telegram alerts |

### 8.3 Reporting
| Script | Status | Purpose |
|--------|--------|---------|
| `reports/daily_summary.py` | 📋 | Daily performance report |
| `reports/weekly_report.py` | 📋 | Weekly analysis |
| `reports/monthly_report.py` | 📋 | Monthly breakdown |
| `reports/trade_journal.py` | 📋 | Trade log with screenshots |

---

## 9. Testing & Validation

### 9.1 Unit Tests
| Script | Status | Purpose |
|--------|--------|---------|
| `tests/test_indicators.py` | 📋 | Test indicator calculations |
| `tests/test_signals.py` | 📋 | Test signal generation |
| `tests/test_backtester.py` | 📋 | Test backtesting engine |
| `tests/test_position.py` | 📋 | Test position manager |

### 9.2 Integration Tests
| Script | Status | Purpose |
|--------|--------|---------|
| `tests/test_pine_vs_python.py` | 📋 | Verify Pine = Python |
| `tests/test_exchange_clients.py` | 📋 | Test exchange APIs |
| `tests/test_live_bot.py` | 📋 | Test live bot logic |

### 9.3 Validation Scripts
| Script | Status | Purpose |
|--------|--------|---------|
| `validation/verify_cloud3_filter.py` | 📋 | Verify Cloud 3 filter works |
| `validation/verify_be_raise.py` | 📋 | Verify ATR-based BE |
| `validation/compare_versions.py` | 📋 | Compare v3.7.1 vs v3.8 |

---

## 10. Utilities & Helpers

### 10.1 Configuration
| Script | Status | Purpose |
|--------|--------|---------|
| `config.yaml` | ✅ | Main config file |
| `config/exchange_config.yaml` | 📋 | Exchange API keys |
| `config/strategy_config.yaml` | 📋 | Strategy parameters |
| `config/ml_config.yaml` | 📋 | ML hyperparameters |

### 10.2 Logging & Debugging
| Script | Status | Purpose |
|--------|--------|---------|
| `utils/logger.py` | 📋 | Structured logging |
| `utils/profiler.py` | 📋 | Performance profiling |
| `utils/debugger.py` | 📋 | Debug helpers |

### 10.3 Math & Stats
| Script | Status | Purpose |
|--------|--------|---------|
| `utils/statistics.py` | 📋 | Statistical functions |
| `utils/kelly_criterion.py` | 📋 | Kelly position sizing |
| `utils/expectunity.py` | 📋 | Expectancy calculation |

### 10.4 Visualization
| Script | Status | Purpose |
|--------|--------|---------|
| `utils/chart_plotter.py` | 📋 | OHLCV charts |
| `utils/equity_curve.py` | 📋 | Equity curve plotter |
| `utils/drawdown_plot.py` | 📋 | Drawdown visualization |
| `utils/heatmap.py` | 📋 | Parameter heatmaps |

---

## 11. Documentation

### 11.1 Setup & Installation
| File | Status | Purpose |
|------|--------|---------|
| `README.md` | 📋 | Project overview |
| `SETUP-GUIDE.md` | ✅ | Installation instructions |
| `requirements.txt` | ✅ | Python dependencies |
| `requirements-frozen.txt` | ✅ | Frozen versions |

### 11.2 Usage Guides
| File | Status | Purpose |
|------|--------|---------|
| `docs/QUICKSTART.md` | 📋 | Quick start guide |
| `docs/BACKTESTING.md` | 📋 | Backtesting tutorial |
| `docs/LIVE-TRADING.md` | 📋 | Live trading guide |
| `docs/ML-PIPELINE.md` | 📋 | Vince ML guide |

### 11.3 Strategy Documentation
| File | Status | Purpose |
|------|--------|---------|
| `docs/FOUR-PILLARS-V3.8.md` | 📋 | v3.8 strategy spec |
| `docs/CLOUD3-FILTER.md` | 📋 | Directional filter logic |
| `docs/ATR-BE-RAISE.md` | 📋 | ATR-based BE logic |
| `docs/SIGNAL-GENERATION.md` | 📋 | A/B/C signal rules |

### 11.4 API Documentation
| File | Status | Purpose |
|------|--------|---------|
| `docs/API-BINGX.md` | 📋 | BingX API reference |
| `docs/API-WEEX.md` | 📋 | WEEX API reference |
| `docs/API-BYBIT.md` | ⏸️ | Bybit API reference |

---

## 12. Deployment

### 12.1 Docker
| File | Status | Purpose |
|------|--------|---------|
| `Dockerfile` | 📋 | Main container |
| `docker-compose.yml` | 📋 | Multi-service setup |
| `.dockerignore` | 📋 | Ignore patterns |

### 12.2 CI/CD
| File | Status | Purpose |
|------|--------|---------|
| `.github/workflows/test.yml` | 📋 | GitHub Actions tests |
| `.github/workflows/deploy.yml` | 📋 | Auto-deployment |

### 12.3 Production Scripts
| Script | Status | Purpose |
|--------|--------|---------|
| `deploy/start_bot.sh` | 📋 | Start live bot |
| `deploy/stop_bot.sh` | 📋 | Stop live bot |
| `deploy/backup.sh` | 📋 | Backup data/logs |
| `deploy/monitor.sh` | 📋 | Health check |

---

## Summary Statistics

| Category | Total Scripts | Complete | In Progress | Planned | Paused |
|----------|---------------|----------|-------------|---------|--------|
| Data Management | 12 | 2 | 0 | 9 | 1 |
| Indicators & Signals | 13 | 0 | 4 | 9 | 0 |
| Strategy Implementations | 8 | 1 | 0 | 7 | 0 |
| Backtesting Engine | 11 | 4 | 0 | 7 | 0 |
| Optimization & Analysis | 16 | 4 | 0 | 12 | 0 |
| Vince ML Pipeline | 15 | 0 | 0 | 15 | 0 |
| Live Trading Bot | 16 | 0 | 0 | 15 | 1 |
| Dashboard & Monitoring | 11 | 1 | 0 | 10 | 0 |
| Testing & Validation | 9 | 0 | 0 | 9 | 0 |
| Utilities & Helpers | 14 | 0 | 0 | 14 | 0 |
| Documentation | 13 | 3 | 0 | 10 | 0 |
| Deployment | 7 | 0 | 0 | 7 | 0 |
| **TOTAL** | **145** | **15** | **4** | **124** | **2** |

---

## Priority Order for v3.8 Stable Version

### Phase 1: Pine Script v3.8 (This Week)
1. ✅ Copy v3.7.1 → v3.8
2. 📋 Add Cloud 3 directional filter
3. 📋 Add ATR-based BE raise
4. 📋 Update commission to $8/side
5. 📋 Add MFE/MAE tracking
6. 📋 Test on UNIUSDT (2m chart)

### Phase 2: Python v3.8 (Next Week)
1. 📋 `strategies/four_pillars_v3_8.py` — Main strategy
2. 📋 `strategies/indicators.py` — Indicator calculations
3. 📋 `strategies/signal_machine.py` — Stage 1/2 logic
4. 📋 `backtester/vectorized.py` — Fast backtesting
5. 📋 `validation/verify_pine_vs_python.py` — Verify match

### Phase 3: Exchange Integration (Week 3)
1. 📋 `data/bingx_fetcher.py` — BingX historical data
2. 📋 `data/weex_fetcher.py` — WEEX historical data
3. 📋 `live/bingx_client.py` — BingX WebSocket
4. 📋 `live/weex_client.py` — WEEX WebSocket
5. 📋 `live/paper_trading.py` — Paper trading mode

### Phase 4: Vince ML Analysis (Week 4)
1. 📋 Convert all 1m → 5m (100+ coins)
2. 📋 Run Vince ML pipeline (7 scripts)
3. 📋 Generate comprehensive report
4. 📋 Optimize parameters per coin
5. 📋 Update v3.8 with optimal params

### Phase 5: Live Trading (Week 5+)
1. 📋 `live/trading_bot.py` — Main bot
2. 📋 `live/order_manager.py` — Order execution
3. 📋 `dashboard/live_monitor.py` — Real-time dashboard
4. 📋 Paper trade for 1 week (verify)
5. 📋 Go live with small size ($100-500)

---

## Notes

- **Bybit**: Paused until client funds account
- **BingX + WEEX**: Primary exchanges for data + live trading
- **Focus**: Get stable v3.8 first, then ML analysis
- **Testing**: Sample coins + simulated live trading before real money
- **Location**: All scripts in `trading-tools/` folder
- **Journal**: Points to this file for tracking progress

---

**Last Updated**: 2026-02-09 16:27 UTC
**Next Review**: After Phase 1 completion
