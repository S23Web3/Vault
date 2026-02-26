# Project Audit — 2026-02-13

---

## What You're Building

A fully automated cryptocurrency scalping system called **Vince** that trades 24/7 without human intervention. The system uses a **Four Pillars** strategy (Ripster EMA Clouds, AVWAP, Quad Rotation Stochastics, BBWP) to generate signals, then filters them through ML (XGBoost now, PyTorch later) to skip bad trades. Revenue comes from two sources: direct P&L on winning trades, and **commission rebates** (70% of 0.08% taker fee) which are profitable even on flat equity if trade volume is high enough.

Three personas share the same engine: **Vince** (rebate farming on BingX/WEEX/Bybit), **Vicky** (copy trading for followers, needs 55%+ win rate), **Andy** (FTMO prop trading, 10%/month target with drawdown limits).

The end state is: TradingView sends webhook alerts → n8n validates momentum → exchange API executes trades → Vince monitors and adjusts → dashboard shows real-time status.

---

## Where You Stand

### LAYER 1: DATA — COMPLETE
- 399 coins cached in Parquet (1m), ~6.2 GB, 124.8M bars
- Bybit v5 API fetcher with rate limit handling and retry logic
- Universal CSV normalizer for 6 exchange formats (data/normalizer.py)
- Sanity check script validates cache integrity
- PostgreSQL (PG16, port 5433) with 5 tables for storing backtest results

### LAYER 2: STRATEGY (Python backtester) — COMPLETE, v3.8.4 CURRENT
- Full version chain: v3.7.1 → v3.8 → v3.8.2 (failed) → v3.8.3 → v3.8.4
- v3.8.4 = v3.8.3 + optional ATR-based take profit
- 4-stage stochastic state machine, A/B/C/D/ADD/RE/R signal grades
- ATR SL (2.5x optimal), AVWAP trailing, scale-out mechanism
- Best result: 3-coin optimal +$17,863 (RIVER TP=2.0, KITE/BERA no TP)
- Key insight: TP is coin-specific, not universal. Tight TP destroys value.
- 52 Python files, 8,600+ lines of code across engine/signals/strategies/scripts

### LAYER 3: DASHBOARD — COMPLETE, NOT FULLY TESTED
- Streamlit app (~1,450 lines), 4 modes: settings | single | sweep | sweep_detail
- Sweep: incremental (1 coin per rerun), CSV persistence, auto-resume
- Normalizer integrated for upload-and-backtest workflow
- Tests written (17 normalizer, 11 sweep) — **NOT YET RUN BY USER**
- ML tabs exist in staging but staging dashboard is STALE (pre-Feb 12 work)

### LAYER 4: ML (XGBoost) — BUILT, NOT WIRED
- All 9 ML modules exist: features, triple_barrier, purged_cv, meta_label, shap_analyzer, bet_sizing, walk_forward, loser_analysis, xgboost_trainer
- No orchestration script yet (`train_vince.py` spec exists in BUILD-VINCE-ML.md, not coded)
- No `models/` directory exists — no trained models saved
- `live_pipeline.py` in staging, not deployed to `ml/`
- The build spec (BUILD-VINCE-ML.md) is comprehensive and ready to execute

### LAYER 5: ML (PyTorch) — SPEC ONLY
- Full architecture designed in BUILD-VINCE-ML.md (B3 section)
- TradeTrajectoryNetwork: 3-branch LSTM + static features, 4 output heads
- PyTorch + CUDA installation still blocked on RTX 3060
- Zero code written

### LAYER 6: LIVE EXECUTION — NOT BUILT
- 24/7 executor framework (task_runner, watchdog, checkpoint) — spec exists, no code
- n8n workflows running on VPS "Jacky" but webhook returning 404
- Exchange API scripts not deployed to VPS
- TradingView → n8n → exchange pipeline not connected end-to-end

### LAYER 7: PINE SCRIPT (TradingView) — BUILT, NOT VALIDATED
- v3.8 indicator + strategy Pine Script files created
- No live validation against Python backtester (P5 in pending builds)
- Earlier versions (v3.5–v3.7.1) in repo, documented in version history

---

## What's Blocking Progress

| Blocker | Impact | Fix |
|---------|--------|-----|
| ML not wired (no train_vince.py) | Can't filter D/R grade trades that drag -$3,323 | Build P2 from BUILD-VINCE-ML.md |
| Staging dashboard stale | ML tabs don't reflect current dashboard work | Only deploy live_pipeline.py, skip rest |
| PyTorch + CUDA not installed | GPU training deferred, can't build B3 | Install torch with CUDA for RTX 3060 |
| n8n webhook 404 | Live execution pipeline broken | Debug webhook URL + auth on Jacky |
| Tests not run | 84 tests written, 0 verified by user | Run test_normalizer.py + test_sweep.py |
| No trained models | ML modules exist but no saved .json models | Run train_vince.py after it's built |

---

## Pending Build Queue (Priority Order)

| # | Build | Effort | Depends On | Impact |
|---|-------|--------|------------|--------|
| P1 | Deploy live_pipeline.py only (skip stale staging) | 5 min | Nothing | Unblocks ML wiring |
| P2 | train_vince.py orchestrator + test | 2-3 hrs | P1 | Wires all 9 ML modules, filters D/R drag |
| P3 | Multi-coin portfolio optimization | 30 min | P2 results | Add PEPE/SAND/HYPE, find optimal portfolio |
| P4 | 400-coin ML sweep | 2-4 hrs runtime | P2 | Rank all coins by ML-filtered expectancy |
| P5 | TradingView validation (Pine vs Python) | 1 hr + manual TV export | Nothing | Verify strategy parity |
| P6 | 24/7 executor framework | 2-3 hrs | Nothing | Production runtime for live trading |
| P7 | Dashboard UI/UX research | Ongoing | Nothing | Workflow guidance, not just data display |
| B3 | PyTorch TradeTrajectoryNetwork | 4-6 hrs | PyTorch installed | Deep learning on trade sequences |
| B4 | Dashboard v2 (ML tab wiring + PyTorch tab) | 2-3 hrs | P2 + B3 | Visual ML analysis |

---

## Codebase Stats

| Category | Files | Key Files |
|----------|-------|-----------|
| engine/ | 9 | backtester_v384.py, position_v384.py, commission.py |
| signals/ | 7 | state_machine_v383.py, four_pillars_v383.py |
| ml/ | 10 | 9 modules + __init__ (no pytorch/ yet) |
| scripts/ | 46 | dashboard.py, run_backtest_v384.py, sweep_tp_v384.py |
| strategies/ | 6 | four_pillars_v3_8.py, cloud_filter.py |
| results/ | 9 | sweep + validation markdown reports |
| staging/ | 4 | STALE dashboard, live_pipeline.py |
| models/ | 0 | Directory doesn't exist yet |
| Pine Script | 2 | v3.8 indicator + strategy |
| Git tracked | 176 | 148 Python + 28 Pine Script |

---

## Timeline Assessment

**Weeks 1-2 (Feb 3-13, DONE):** Data infrastructure, strategy evolution (v3.7→v3.8.4), backtesting framework, dashboard, ML module library, documentation system.

**Week 3 target:** P1→P2→P3 (ML wiring + training + portfolio). This is the critical path — everything after depends on having trained models.

**Week 4 target:** P4 (400-coin sweep), P6 (executor), fix n8n webhook. This gets the system toward live operation.

**Month 2 target:** B3 (PyTorch), B4 (dashboard v2), live TradingView validation, deploy to VPS for 24/7 operation.

---

## Risk Assessment

1. **Overfitting risk**: v3.8.4 backtested on 3 months of data. Walk-forward validation (in ml/walk_forward.py) exists but hasn't been run on real trades yet.
2. **Commission assumption**: 70% rebate rate is exchange-specific and can change. System math depends on it.
3. **Execution gap**: Python backtester assumes instant fills. Live slippage on low-cap coins (RIVER, KITE) could erode edge.
4. **D/R grade drag**: -$3,323 across 3 coins. ML filter is the planned fix but unproven.
5. **Single timeframe**: All optimization on 5m. No multi-timeframe confirmation yet.
