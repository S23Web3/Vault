# RESEARCH SYNTHESIS — Four Pillars Trading System

Generated: 2026-03-06
Source: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\RESEARCH-FINDINGS.md` (21 research batches, 140+ session logs, ~8600 lines)

---

## 1. What is the project goal?

Build a complete algorithmic trading system around the **Four Pillars** strategy — from Pine Script indicators on TradingView, through a Python backtester for multi-coin parameter optimization, to a live trading bot on BingX, supported by an ML research engine (Vince) and comprehensive dashboards.

The strategy combines four signal components:
- **Ripster EMA Clouds** (Cloud 2: 5/12, Cloud 3: 34/50, Cloud 4: 72/89, Cloud 5: 180/200)
- **AVWAP** (Anchored VWAP, Brian Shannon methodology)
- **Quad Rotation Stochastics** (Kurisko Raw K: 9-3 entry, 14-3 confirm, 40-3 divergence, 60-10 macro)
- **BBWP** (Bollinger Band Width Percentile — volatility filter)

Signal grading: **A** = Quad (4/4 stochs aligned), **B** = Rotation (3/4 stochs), **C** = ADD (engine label for position additions, not a standalone signal type).

The end-state vision: backtest across 399 crypto coins, identify optimal parameters per coin, deploy live via BingX with automated entries/exits, and use ML to surface trade-quality patterns that humans miss.

---

## 2. Current state of each major component

### Four Pillars Backtester

- **Current version**: v3.8.4 (stable production). Codebase: 142,935 lines across the project.
- **Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`
- **Capabilities**: Multi-coin batch backtesting, 399 coins supported, CSV data pipeline, PostgreSQL storage (vince database, port 5433), commission modeling (0.08%/side taker on notional).
- **Dashboard versions**: v3.9.0 through v3.9.4 were Streamlit-based dashboards built on top of v3.8.4 engine. v3.9.4 added CUDA GPU sweep (Numba @cuda.jit on RTX 3060) for parameter optimization. These are dashboard/UI layers — the core engine remains v3.8.4.
- **Data**: 5-minute OHLCV CSVs for 399 coins stored locally. 1-minute data also available but backtests confirmed 5m > 1m for all low-price coins.
- **Key findings from backtests**: LSG (Losing-but-Scored-Good) rate 85-92% — most losers were profitable at some point, making TP/ML filtering the key lever. Tight TP (< 2.0 ATR) destroys value on most coins. Always backtest, never trust MFE alone.

### BingX Live Bot

- **Location**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\`
- **Status**: LIVE on real account ($110 margin). Running on VPS Jacky (76.13.20.191).
- **Version**: v1.5 (as of 2026-03-05).
- **Architecture**: HMAC-SHA256 authentication, hedge mode perpetual futures, WebSocket listener for real-time data, REST API for order management.
- **Features built**: TTP engine (Trailing Take Profit), breakeven raise logic, position sizing from config, multi-coin support, time-sync fix (server timestamp delta), dashboard (Plotly Dash).
- **Bugs fixed during live deployment**:
  - `reduceOnly` parameter error on close orders (Feb 26-27)
  - Timestamp sync drift causing 401 auth failures (fixed with server time delta)
  - Breakeven price calculation error (was using entry instead of accounting for commission)
  - Buffer stuck at 200/201 — trim logic was cutting buffer back to 200 after every fetch, signals could never fire (cost 2+ hours to diagnose)
  - Position side mismatch in hedge mode
- **Config**: Coins, margin, leverage all configurable. Commission: 0.08% taker, 70% rebate account = $4.80/RT net.
- **Dashboard**: BingX dashboard built on Plotly Dash, shows positions, PnL, trade history. Separate from backtester dashboard.

### Vince ML Pipeline (B1-B6)

- **Concept**: Vince v2 is a **Trade Research Engine** (NOT a classifier). It surfaces patterns in trade data that humans can then use to refine strategy rules.
- **Status**: Concept APPROVED 2026-02-27. B2 (API layer) built. B1 (Phase 0 strategy alignment) BLOCKED. B3-B6 blocked on B1.
- **Build phases defined**:
  - **B1**: Phase 0 — Strategy alignment, feature engineering, data pipeline from backtester to ML
  - **B2**: API layer — FastAPI endpoints for serving model predictions (BUILT)
  - **B3**: Feature enrichment — Technical indicator features beyond raw OHLCV
  - **B4**: Model training pipeline — PyTorch on CUDA (RTX 3060, 12GB VRAM)
  - **B5**: Evaluation framework — Walk-forward validation, out-of-sample testing
  - **B6**: Dashboard integration — Plotly Dash 4.0 multi-page app, 8-panel research UI
  - **B7-B10**: Defined but distant (optimizer, constellation builder, production serving, monitoring)
- **B1 blocker**: Phase 0 requires deciding exactly which features to extract and how to align backtester output with ML input. This is a strategy decision, not a code decision — needs user input on what trade attributes matter most.
- **Tech stack decided**: Plotly Dash 4.0 (NOT Streamlit), PyTorch (NOT sklearn for production), PostgreSQL for storage, Ollama (qwen3:8b) for local LLM features.
- **Screener v1**: WEEX screener scoped as part of Vince ecosystem. Separate from main ML pipeline.

### Pine Script Indicators

- **Versions built**: v3.4 through v3.8, all Pine Script v6 on TradingView.
- **v3.4**: Initial Four Pillars indicator with Ripster Clouds + AVWAP + basic stochastics.
- **v3.5**: Added quad stochastic rotation. **Regression found**: stochastic smoothing was accidentally changed from Raw K (smooth=1) to smoothed, which altered signal behavior. Fixed in later version.
- **v3.6**: Commission-aware strategy with `strategy.commission.cash_per_order` (value=8). Fixed the `commission.percent` ambiguity with leverage.
- **v3.7**: **Commission bug discovered** — was double-counting or miscalculating commission in certain flip scenarios. `strategy.close_all()` causes phantom double-commission trades. Rule established: never use `strategy.close_all()` for flips.
- **v3.8**: Stable indicator version with all fixes applied. Used as reference for Python backtester parity checks.
- **Key lesson**: Pine Script and Python backtester must produce identical signals for the same data. Any divergence means one has a bug. Pine v3.5 stochastic regression was caught by comparing Pine vs Python outputs.

### Infrastructure

- **VPS Jacky**: 76.13.20.191. Runs BingX bot. VST (Visual Studio Tunnel) blocked — cannot use for remote dev.
- **GitHub**: S23Web3/ni9htw4lker (identity: S23Web3, malik@shortcut23.com). Also S23Web3/Vault for the Obsidian vault.
- **PostgreSQL**: PG16, port 5433, user=postgres, pw=admin. Database: vince. Tables: backtest_runs, backtest_trades, equity_snapshots, live_trades, commission_settlements.
- **Ollama**: Local LLM server at port 11434. Model: qwen3:8b (4.9GB, fits entirely in 12GB VRAM on RTX 3060).
- **Hardware**: NVIDIA RTX 3060 12GB VRAM, 32GB RAM, AMD Ryzen 7 5800X. CUDA-capable for Numba GPU sweeps and PyTorch training.
- **Python environment**: Local Windows 11 Pro. Bash shell available (Git Bash). Dependencies managed per-project.

---

## 3. What is the primary blocker right now?

**Vince B1 (Phase 0 — Strategy Alignment)** is the critical-path blocker for the ML pipeline. Everything from B3 through B10 depends on B1 defining the feature set and data alignment. B2 (API layer) was built ahead of B1 as infrastructure prep, but the ML pipeline cannot produce meaningful results until B1 is resolved.

For the BingX bot, the primary blocker is **signal quality verification** — the bot is live but needs more runtime data to confirm that the Python-generated signals match expected behavior on live markets. The buffer-stuck-at-200 bug demonstrated that subtle data pipeline issues can silently prevent signals from ever firing.

For the backtester, there is no blocker — v3.8.4 is stable and functional. The CUDA GPU sweep (v3.9.4) works but is a dashboard/optimization layer, not a core engine change.

---

## 4. What decisions are locked?

| Decision | Status | Date Locked | Context |
|----------|--------|-------------|---------|
| Commission rate: 0.08% (0.0008) taker per side on notional | LOCKED | 2026-02 | Derived from exchange fee schedule. Never hardcode dollar amounts. |
| Commission Pine Script: `strategy.commission.cash_per_order` value=8 | LOCKED | 2026-02 | `commission.percent` is ambiguous with leverage. Cash per order is unambiguous. |
| Never use `strategy.close_all()` for flips | LOCKED | 2026-02 | Causes phantom double-commission trades. |
| Stochastic settings (Kurisko Raw K): 9-3, 14-3, 40-3, 60-10, all smooth=1 | LOCKED | 2026-01 | John Kurisko methodology. Raw K (smooth=1) is non-negotiable. |
| Ripster Cloud numbering: C2=5/12, C3=34/50, C4=72/89, C5=180/200 | LOCKED | 2026-01 | Standard Ripster EMA Cloud settings. |
| 5m timeframe > 1m for all low-price coins | LOCKED | 2026-02 | Backtested across all 399 coins. Every low-price coin profitable on 5m, most negative on 1m. |
| Tight TP (< 2.0 ATR) destroys value | LOCKED | 2026-02 | Backtested. Always backtest TP levels, never trust MFE alone. |
| Vince v2 = Trade Research Engine, NOT classifier | LOCKED | 2026-02-27 | Concept approved by user. Surfaces patterns, does not make binary predictions. |
| Vince UI = Plotly Dash 4.0 (NOT Streamlit) | LOCKED | 2026-02 | Streamlit dashboard versions (v3.9.x) were transitional. Production UI is Dash. |
| Signal grading: A=Quad(4/4), B=Rotation(3/4), C=ADD(engine label) | LOCKED | 2026-02 | C is not a signal type — it's a position addition label. |
| PostgreSQL port 5433, database=vince | LOCKED | 2026-02 | PG16 installation uses non-default port. |
| BingX hedge mode for perpetual futures | LOCKED | 2026-02 | Required for simultaneous long/short capability. |
| Rebate: 70% account=$4.80/RT net, 50% account=$8.00/RT net | LOCKED | 2026-02 | Settle daily 5pm UTC. |
| Python backtester stable at v3.8.4 | LOCKED | 2026-02 | v3.9.x versions are dashboard layers on top of v3.8.4 engine. |
| Logging standard: dated files, dual handler, TimedRotatingFileHandler | LOCKED | 2026-02 | Non-negotiable for all projects. If it's not logged, it didn't happen. |

---

## 5. What decisions are still open?

| Decision | Status | Context |
|----------|--------|---------|
| Vince B1 feature set — which trade attributes to extract | OPEN | Needs user input. Strategy decision, not code decision. Determines entire ML pipeline direction. |
| Walk-forward validation window sizes for ML | OPEN | Part of B5 evaluation framework. Depends on B1 feature decisions. |
| Which coins to run live on BingX beyond initial test set | OPEN | Bot is live but coin selection for scaling up not finalized. |
| TTP (Trailing Take Profit) optimal parameters per coin | OPEN | TTP engine built in bot, but optimal trailing distances need more live data. |
| Whether to use Ollama/qwen3:8b for feature extraction or just for analysis | OPEN | Model available locally, but its role in the ML pipeline not yet defined. |
| CUDA GPU sweep — production use vs experimental | OPEN | v3.9.4 built it, works on RTX 3060, but unclear if it's the standard optimization path or one-off. |
| VPS scaling — single Jacky instance vs multi-VPS | OPEN | Currently single VPS. Scaling plan not defined. |
| BBW Simulator integration with live trading signals | OPEN | Pipeline complete (layers 1-5), but whether/how it feeds into live bot decisions not decided. |
| Screener architecture — standalone vs Vince-integrated | OPEN | WEEX screener scoped but implementation path relative to Vince not locked. |
| Position sizing model for live trading | OPEN | Bot uses config-based sizing. Dynamic sizing based on signal grade/volatility not yet designed. |

---

## 6. What has been confirmed working?

### Four Pillars Backtester
- v3.8.4 engine: runs full backtests across 399 coins on 5m data
- CSV data pipeline: loads, validates, and processes 5m OHLCV data
- Commission modeling: 0.08%/side on notional, correctly calculated
- PostgreSQL integration: backtest_runs, backtest_trades, equity_snapshots all populate correctly
- Batch mode: can run all 399 coins sequentially
- Signal generation: A/B grading produces expected entries matching Pine Script v3.8

### BingX Bot
- HMAC-SHA256 authentication with server time delta sync
- Order placement (market orders, limit orders) in hedge mode
- Position opening and closing with correct side handling
- TTP engine (trailing take profit) — logic implemented and running
- Breakeven raise — triggers correctly after threshold
- WebSocket connection for real-time data feed
- Dashboard (Plotly Dash) showing positions and PnL
- Runs stable on VPS Jacky for multi-day periods
- Logging with timestamps, dated log files, dual handler

### BBW Simulator Pipeline
- Layer 1: BBWP calculation from raw Bollinger Band Width
- Layer 2: Sequence detection (consecutive bars above/below thresholds)
- Layer 3: Forward return calculation after sequence events
- Layer 4: Simulator engine combining BBWP sequences with returns
- Layer 5: Monte Carlo simulation for confidence intervals
- V2 corrections applied (specific calculation fixes)
- Declared COMPLETE 2026-02-17

### Pine Script
- v3.8 indicator: Ripster Clouds + AVWAP + Quad Stochastics + BBWP overlay
- Commission via `cash_per_order` method (unambiguous with leverage)
- Signal parity with Python backtester confirmed at v3.8 level

### Infrastructure
- PostgreSQL PG16 on port 5433: stable, all tables created and populated
- Ollama qwen3:8b: loads fully into GPU VRAM, responds at port 11434
- GitHub repos: S23Web3/ni9htw4lker and S23Web3/Vault both active
- RTX 3060 CUDA: Numba GPU kernels execute correctly for parameter sweeps

---

## 7. What has been built but is unverified or untested?

### Four Pillars Backtester
- **v3.9.4 CUDA GPU sweep**: Built and runs, but not validated against CPU results for numerical parity. Unknown if GPU sweep produces identical optimal parameters to CPU brute force.
- **Streamlit dashboard versions (v3.9.0-v3.9.3)**: Built as UI layers, but superseded by Dash plans. Unclear if any are still runnable or if dependencies drifted.

### BingX Bot
- **Multi-coin simultaneous live trading**: Bot supports multiple coins in config, but most live testing has been single-coin or limited sets. Concurrent position management across many coins not stress-tested.
- **Rebate settlement tracking**: Commission settlements table exists in PostgreSQL, but automated reconciliation of daily 5pm UTC rebate deposits not verified against actual exchange settlements.
- **Error recovery after VPS restart**: Bot restarts and reconnects, but whether it correctly detects and resumes open positions after unexpected crash/restart not formally tested.

### Vince ML Pipeline
- **B2 API layer (FastAPI)**: Built but has no upstream data (B1 not done) and no downstream consumer. Endpoints exist but serve no trained model.

### BBW Simulator
- **Layer 6 (Report generation)**: Referenced in pipeline design but completion status ambiguous — layers 1-5 confirmed complete, layer 6 (report/visualization) may be partial.
- **Integration with backtester**: BBW pipeline runs standalone. Whether its output correctly feeds back into backtester signal filtering not tested end-to-end.

### Pine Script
- **v3.6 and v3.7 intermediate versions**: Built and iterated on, but with known bugs (commission issues in v3.7, smoothing regression in v3.5). These versions exist in TradingView but should not be used — only v3.8 is validated.

---

## 8. What has been planned but never executed?

### Four Pillars Backtester
- **Dynamic position sizing based on signal grade**: Discussed (A trades get more margin than B trades) but never implemented. Current system uses fixed sizing.
- **Walk-forward optimization**: Mentioned as necessary for preventing overfitting but no implementation exists.
- **Multi-timeframe backtesting**: 5m is the standard, 1m was tested and rejected, but 15m/1h timeframes never backtested.

### BingX Bot
- **Automated coin rotation**: Concept of dynamically switching which coins the bot trades based on backtester rankings — discussed but no implementation.
- **Risk management circuit breaker**: Auto-stop trading after N consecutive losses or X% daily drawdown — mentioned but not built.
- **Multi-exchange support**: BingX is the only exchange. No work toward Bybit, OKX, or other exchange connectors.

### Vince ML Pipeline
- **B3 (Feature enrichment)**: Defined in build plan, depends on B1, never started.
- **B4 (Model training pipeline)**: PyTorch on CUDA, defined but never started.
- **B5 (Evaluation framework)**: Walk-forward validation, defined but never started.
- **B6 (Dashboard integration)**: 8-panel Dash UI, extensively scoped and designed (panel taxonomy defined, page structure planned), but no code written.
- **B7-B10**: Optimizer, constellation builder, production serving, monitoring — defined at concept level only.
- **Phase 0 strategy alignment (B1)**: The most critical planned-but-unexecuted item. Everything downstream depends on it.

### Pine Script
- **v3.9+ indicator versions**: No Pine Script development beyond v3.8. All development effort shifted to Python backtester and bot.
- **Alert-to-bot webhook pipeline**: TradingView alerts triggering BingX bot via n8n webhook — discussed conceptually but never built. Bot uses its own signal generation instead of Pine Script alerts.

### Infrastructure
- **Multi-VPS deployment**: Only VPS Jacky exists. No scaling or redundancy plan executed.
- **Automated backup/restore**: PostgreSQL backups not automated. No disaster recovery tested.
- **CI/CD pipeline**: No automated testing, deployment, or integration pipeline. All deployments are manual.
- **n8n workflow automation**: n8n mentioned for TradingView-to-bot webhooks but no workflows built or deployed.
- **Monitoring/alerting**: No system health monitoring beyond manual log review. No PagerDuty, no Slack alerts, no automated health checks.

---

## Summary

The Four Pillars system has a **working backtester** (v3.8.4), a **live bot** (BingX v1.5 on real money), and a **complete volatility pipeline** (BBW layers 1-5). Pine Script indicators are stable at v3.8. Infrastructure (PostgreSQL, Ollama, CUDA, VPS) is operational.

The critical gap is the **ML pipeline** — Vince B1 (strategy alignment / feature engineering) remains unstarted, blocking all downstream ML work (B3-B10). B2 (API layer) was built proactively but serves nothing until B1 defines what data flows through it.

Secondary gaps: no automated risk management in the live bot, no walk-forward validation in the backtester, no CI/CD or monitoring infrastructure.

The system is in a state where **manual trading with backtester-informed parameters works**, but the vision of **ML-enhanced automated trading with dynamic optimization** requires completing the Vince pipeline starting with the B1 blocker.