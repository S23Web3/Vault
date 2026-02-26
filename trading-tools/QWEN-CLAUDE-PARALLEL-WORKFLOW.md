# Qwen + Claude Parallel Workflow

**Goal**: Work simultaneously - Qwen generates code, Claude integrates/tests
**Date**: 2026-02-09

---

## Task Division (From VINCE-IMPLEMENTATION-PLAN.md)

### ✅ QWEN TASKS (Code Generation)

**Qwen is best at**: Pure code generation, no file I/O

#### Phase 1: Core Infrastructure (Tonight - Overnight)
1. ✅ **base_strategy.py** - Abstract strategy interface
2. ✅ **position_manager.py** - MFE/MAE tracking
3. ✅ **exit_manager.py** - 4 risk methods (BE, BE+fees, BE+fees+trail, BE+trail)
4. ✅ **metrics.py** - SQN, Sharpe, LSG%, profit factor
5. ✅ **backtester.py** - Event-based backtest engine

**Status**: Running overnight via OLLAMA-OVERNIGHT-TASK.md

#### Phase 2: Strategy Components (Tomorrow)
6. **Four Pillars indicator calculations** (stochastics, EMAs, Cloud 3 filter)
7. **Signal generation logic** (A/B/C signal state machine)
8. **ATR-based SL/TP calculator**
9. **Cloud 3 directional bias filter**

#### Phase 3: Optimization Engine (Day 2-3)
10. **Parameter sweep** (grid search over ATR periods, MFE thresholds, SL locks)
11. **Bayesian optimization** wrapper (optuna integration)
12. **Walk-forward validation** splitter
13. **Multi-coin aggregator** (find "best practice" parameters)

#### Phase 4: ML Components (Day 4-5)
14. **XGBoost meta-labeling trainer** (skip/take classifier)
15. **Triple Barrier labeling** (TP/SL/time exit labels)
16. **Purged K-Fold CV** implementation
17. **SHAP value calculator** (per-trade feature importance)
18. **Feature engineering** (21 TA-Lib features)

#### Phase 5: Streamlit GUI (Day 6-7)
19. **Fuzzy coin selector** (fuzzywuzzy dropdown)
20. **Parameter input forms** (Streamlit widgets)
21. **Results dashboard tabs** (6 tabs: Summary, Trade List, Equity, LSG, SHAP, Heatmap)
22. **Chart generators** (Plotly equity curves, heatmaps)

#### Phase 6: Exchange Integration (Day 8-9)
23. **BingX data fetcher** (historical OHLCV API)
24. **WEEX data fetcher** (historical OHLCV API)
25. **WebSocket handlers** (live data streams)
26. **Order execution client** (BingX/WEEX trading API)

---

### ✅ CLAUDE TASKS (Integration, Testing, File Ops)

**Claude is best at**: File operations, testing, integration, planning

#### Phase 1: Integration & Testing (Tomorrow)
1. **Read Qwen's output** (5 Python files from overnight)
2. **Create file structure** (vince/ folders: strategies/, engine/, optimizer/, etc.)
3. **Write files** to correct locations
4. **Fix imports** and dependencies
5. **Run unit tests** (pytest on each module)
6. **Fix bugs** that Qwen missed
7. **Add logging** and error handling
8. **Create __init__.py** files for packages

#### Phase 2: Strategy Implementation (Day 2)
9. **Read v3.7.1 Pine Script** to understand logic
10. **Integrate** Qwen's Four Pillars components
11. **Test** on RIVERUSDT (5m, 3 months)
12. **Compare** with known results (+$55.9K expected)
13. **Fix discrepancies** (entry timing, exit logic, commission calc)

#### Phase 3: Data Pipeline (Day 3)
14. **Test** resample_timeframes.py on all coins
15. **Verify** 1m → 5m conversion accuracy
16. **Create data loader** that uses Qwen's code
17. **Test** on 9 coins (BTCUSDT, ETHUSDT, RIVER, KITE, PEPE, SAND, HYPE, SOL, BNB)

#### Phase 4: Optimization Integration (Day 4-5)
18. **Integrate** Qwen's parameter sweep
19. **Run** first optimization (RIVERUSDT, 5m)
20. **Validate** results match manual testing
21. **Test** multi-coin aggregation (top 20 coins)
22. **Generate** first optimization report

#### Phase 5: GUI Integration (Day 6-7)
23. **Integrate** Qwen's Streamlit components
24. **Test** coin selector, parameter inputs
25. **Wire up** backtester to GUI
26. **Test** report export (CSV, PNG, PDF)

#### Phase 6: ML Integration (Week 2)
27. **Train** first XGBoost model (RIVERUSDT)
28. **Test** skip/take predictions
29. **Generate** SHAP values
30. **Compare** Four Pillars alone vs + XGBoost filter

---

## Parallel Workflow Example (Day 1 - Tomorrow)

### Morning (8am-12pm)

| Time | Qwen | Claude |
|------|------|--------|
| 8:00 | **Idle** (overnight task complete) | Read Qwen's 5 files from overnight |
| 8:30 | Generate Four Pillars indicators | Create vince/ folder structure |
| 9:00 | Generate signal state machine | Write Qwen's files to disk |
| 9:30 | Generate ATR SL/TP calculator | Fix imports, add __init__.py |
| 10:00 | Generate Cloud 3 filter | Run pytest on position_manager |
| 10:30 | **Idle** (waiting for next task) | Fix bugs in exit_manager |
| 11:00 | Generate parameter sweep | Test backtester on dummy data |
| 11:30 | Generate Bayesian optimizer | Integrate Four Pillars strategy |

### Afternoon (12pm-6pm)

| Time | Qwen | Claude |
|------|------|--------|
| 12:00 | **Idle** | Load RIVERUSDT 5m data |
| 12:30 | Generate walk-forward splitter | Run first backtest (Four Pillars v3.8 Python) |
| 1:00 | Generate multi-coin aggregator | Compare with Pine Script results |
| 1:30 | **Idle** | Fix entry/exit timing bugs |
| 2:00 | Generate XGBoost trainer | Re-run backtest, validate $55.9K result |
| 2:30 | Generate Triple Barrier labeler | Test on 5 low-price coins (PEPE, RIVER, KITE, SAND, HYPE) |
| 3:00 | **Idle** | Aggregate results, check LSG% |
| 3:30 | Generate feature engineering | Run parameter sweep (ATR 8, 13, 14, 21) |
| 4:00 | **Idle** | Analyze sweep results |
| 5:00 | Generate SHAP calculator | Generate first optimization report |

**Total Qwen Tasks**: 12 (8am-4pm)
**Total Claude Tasks**: 15 (8am-5pm)

**Overlap**: ~70% (working simultaneously most of the day)

---

## How to Execute Parallel Workflow

### Setup (One Time)

1. **Start Ollama API** (leave running):
```bash
ollama serve
```

2. **Open 2 terminals**:
   - **Terminal 1**: Ollama interactive (for asking Qwen)
   - **Terminal 2**: Python/testing (for Claude's work)

### Workflow Loop

**Claude (me)**:
1. Identifies next task for Qwen
2. Writes prompt to QWEN-TASKS.md
3. You paste prompt to Ollama Terminal 1
4. While Qwen works, Claude does file ops (Terminal 2)
5. You paste Qwen's output back to Claude
6. Claude integrates, tests, fixes bugs
7. Repeat

---

## Task Queue Management

### File: `QWEN-TASK-QUEUE.md`

```markdown
## Pending Tasks for Qwen

### Priority 1 (Do Now)
- [ ] Four Pillars indicator calculations (stochs, EMAs, ATR, Cloud 3)
- [ ] Signal generation state machine (A/B/C logic)

### Priority 2 (Do Next)
- [ ] Parameter sweep (grid search)
- [ ] Bayesian optimizer wrapper

### Priority 3 (Later)
- [ ] XGBoost trainer
- [ ] Streamlit GUI components

### Completed
- [x] base_strategy.py (overnight)
- [x] position_manager.py (overnight)
- [x] exit_manager.py (overnight)
- [x] metrics.py (overnight)
- [x] backtester.py (overnight)
```

---

## Communication Protocol

### Qwen → Claude (You paste)
```
# Example
Claude, Qwen generated this code for Four Pillars indicators:

[paste Qwen's code]

Can you integrate it into vince/strategies/four_pillars_v3_8.py?
```

### Claude → Qwen (I write)
```
User, ask Qwen to generate this:

"Write a Python function to calculate 4 stochastic oscillators with these settings:
- 9-3 (K=9, smooth=1, D=3)
- 14-3 (K=14, smooth=1, D=3)
- 40-3 (K=40, smooth=1, D=3)
- 60-10 (K=60, smooth=1, D=10)

Use ta-lib. Return DataFrame with columns: stoch_9_k, stoch_14_k, stoch_40_k, stoch_60_k, stoch_60_d"
```

---

## Efficiency Metrics

**Without Parallel Workflow**:
- Claude alone: ~20 hours to build full Vince platform
- Limited by file ops, testing, integration

**With Parallel Workflow**:
- Qwen generates code: ~8 hours total (12 tasks × 40 min avg)
- Claude integrates/tests: ~12 hours total (15 tasks × 48 min avg)
- **Overlap**: ~70% working simultaneously
- **Total time**: ~14 hours (vs 20 hours) = **30% faster**
- **Claude API calls saved**: ~40% (Qwen does code generation)

---

## Next Steps

1. **Wait for Qwen download** to complete (currently 66%)
2. **Paste OLLAMA-OVERNIGHT-TASK.md** to Qwen
3. **Tomorrow morning**: You paste Qwen's 5 files to me
4. **I integrate/test** while you start Qwen on next tasks
5. **Repeat** until all 145 scripts built

---

## Success Criteria

- ✅ Qwen generates 80+ scripts over 2 weeks
- ✅ Claude integrates all scripts, fixes bugs, runs tests
- ✅ Total time: ~14 days (vs 30 days with Claude alone)
- ✅ Rate limit usage: ~50% less (Qwen handles code gen)
- ✅ Quality: Same (Claude reviews + tests all Qwen code)

**Target**: Fully functional Vince ML platform in 2 weeks with parallel workflow.
