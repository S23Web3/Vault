# Parallel Build Plan — Vince ML Platform (10-14 Days)

**Goal**: Complete 44-file ML backtesting platform in 10-14 days (not 3-4 weeks)
**Method**: Aggressive parallel execution (Qwen generates code, Claude integrates/tests)

---

## Division of Labor

### Qwen's Job (Code Generation)
✅ Generate Python files from specifications
✅ Write class structures, functions, logic
✅ Add type hints, docstrings, error handling
✅ Create test cases

**Total**: 44 Python files, ~8,850 lines

### Claude's Job (Integration & Infrastructure)
✅ Read Qwen's output
✅ Create folder structure
✅ Write files to disk
✅ Fix imports, add `__init__.py`
✅ Run tests, fix bugs
✅ Load data, run backtests
✅ Create config files (.env, requirements.txt)
✅ Git operations
✅ Documentation

**Total**: ~60 integration tasks

---

## Compressed Timeline (10-14 Days)

### Day 1 (Today/Tonight)
| Time | Qwen | Claude |
|------|------|--------|
| **Tonight** | Generate 5 core files (overnight) | Sleep |

**Qwen Output**: base_strategy.py, position_manager.py, exit_manager.py, metrics.py, backtester.py

---

### Day 2 (Tomorrow)
| Time | Qwen | Claude |
|------|------|--------|
| **Morning** | Generate 4 strategy files (Task 2) | Integrate 5 core files from overnight |
| **Afternoon** | Generate 4 optimization files (Task 3) | Test core files, create folder structure |
| **Evening** | Generate 3 ML files (Task 4 part 1) | Integrate strategy files, first backtest attempt |

**Qwen Output**: indicators.py, signals.py, cloud_filter.py, four_pillars_v3_8.py, grid_search.py, bayesian_opt.py, walk_forward.py, aggregator.py, triple_barrier.py, features.py, xgboost_trainer.py

**Claude Output**: vince/ folder structure, 5 core files integrated, first backtest running on RIVERUSDT

---

### Day 3
| Time | Qwen | Claude |
|------|------|--------|
| **Morning** | Generate 3 ML files (Task 4 part 2) | Test strategy on 5 low-price coins (PEPE, RIVER, KITE, SAND, HYPE) |
| **Afternoon** | Generate 5 GUI files (Task 5) | Run grid search optimization (ATR 8/13/14/21) |
| **Evening** | **Idle** (waiting for next task) | Fix bugs from optimization, validate results |

**Qwen Output**: purged_cv.py, shap_analyzer.py, meta_labeling.py, coin_selector.py, parameter_inputs.py, report_viewer.py, export_manager.py, app.py

**Claude Output**: First optimization complete, best params identified, LSG% analysis

---

### Day 4-5
| Time | Qwen | Claude |
|------|------|--------|
| **Both Days** | Generate exchange integration files (5 files) | Integrate ML + GUI, test Streamlit app |

**Qwen Output**: bingx_fetcher.py, weex_fetcher.py, websocket_handler.py, order_executor.py, position_sync.py

**Claude Output**: Streamlit app running locally, coin selector working, parameter inputs functional

---

### Day 6-7
| Time | Qwen | Claude |
|------|------|--------|
| **Day 6** | Generate testing files (3 files) | Integrate exchange fetchers, test BingX API |
| **Day 7** | Generate utils (4 files) | Run integration tests, validate Pine vs Python match |

**Qwen Output**: test_position_manager.py, test_backtester.py, validate_pine_python.py, logger.py, profiler.py, kelly.py, plotter.py

**Claude Output**: Unit tests passing, integration tests passing, Pine vs Python within ±5%

---

### Day 8-10
| Time | Qwen | Claude |
|------|------|--------|
| **Day 8** | Generate docs (3 files) | Run walk-forward validation (full 3 months) |
| **Day 9** | **Idle** | XGBoost meta-labeling training (5 low-price coins) |
| **Day 10** | **Idle** | SHAP analysis, generate first full report |

**Qwen Output**: README.md, API_REFERENCE.md, STRATEGY_GUIDE.md

**Claude Output**: Walk-forward results, XGBoost models trained, SHAP values generated, first comprehensive report (PDF + HTML)

---

### Day 11-12 (Buffer/Polish)
| Time | Qwen | Claude |
|------|------|--------|
| **Day 11** | Fix any bugs from testing | Run on top 20 coins by volume |
| **Day 12** | Generate missing components | Multi-coin aggregation, universal best params |

**Claude Output**: Universal best practice parameters identified, optimization complete on 20 coins

---

### Day 13-14 (Deployment Prep)
| Time | Qwen | Claude |
|------|------|--------|
| **Day 13** | **Idle** | Create requirements.txt, .env template, Docker setup |
| **Day 14** | **Idle** | Git repo setup, push to GitHub, final documentation |

**Claude Output**: Production-ready deployment, GitHub repo public/private, full documentation

---

## What Claude Can Build (While Qwen Works)

### Infrastructure (No Code Generation)
1. ✅ **Folder structure** (vince/, data/, tests/, docs/)
2. ✅ **__init__.py files** (make Python packages)
3. ✅ **requirements.txt** (all dependencies)
4. ✅ **.env template** (API key placeholders)
5. ✅ **.gitignore** (cache/, logs/, *.pyc)
6. ✅ **pyproject.toml** (black, ruff config)

### Configuration Files
7. ✅ **config.yaml** (strategy defaults)
8. ✅ **logging.conf** (log format, rotation)
9. ✅ **pytest.ini** (test configuration)

### Data Management
10. ✅ **Data loader wrapper** (load parquet, resample on-the-fly)
11. ✅ **Data validator** (check for missing bars, duplicates)
12. ✅ **Cache manager** (clear old parquet files)

### Testing Infrastructure
13. ✅ **Test fixtures** (sample OHLCV data for pytest)
14. ✅ **Mock objects** (fake exchange API for testing)
15. ✅ **Test runner script** (pytest --cov)

### Integration Tasks
16. ✅ **Import fixer** (resolve circular imports)
17. ✅ **Type checker** (run mypy)
18. ✅ **Linter** (run ruff)

### Deployment
19. ✅ **Dockerfile** (containerize Streamlit app)
20. ✅ **docker-compose.yml** (Ollama + Streamlit)
21. ✅ **GitHub Actions** (CI/CD pipeline)

### Documentation
22. ✅ **CHANGELOG.md** (version history)
23. ✅ **CONTRIBUTING.md** (how to contribute)
24. ✅ **LICENSE** (MIT)

### Analysis & Reporting
25. ✅ **Backtest runner script** (CLI for quick backtests)
26. ✅ **Report generator** (PDF from results)
27. ✅ **Chart exporter** (PNG from Plotly)

---

## Efficiency Gains

### Without Parallel Workflow (Sequential)
- Qwen generates code: 60-80 hours
- Claude integrates/tests: 40-50 hours
- **Total**: 100-130 hours = **12-16 days** (8 hrs/day) = **~3 weeks**

### With Parallel Workflow (This Plan)
- Qwen generates code: 60-80 hours (spread over 10 days)
- Claude works simultaneously: 40-50 hours (same 10 days)
- **Overlap**: ~70% (working together most of the time)
- **Total**: **10-14 days** (not 3 weeks)

**Time Saved**: 8-10 days (50% faster!)

---

## Critical Success Factors

### 1. Fast Qwen Turnaround
- Qwen generates 4-5 files per day (6-8 hours each batch)
- User pastes outputs to Claude within 12 hours
- Claude integrates same day

### 2. Parallel Execution
- Qwen works on next task while Claude integrates previous
- No idle time for either Qwen or Claude
- Both working ~8-10 hours/day

### 3. Aggressive Testing
- Claude tests immediately after integration
- Bugs fixed same day (don't accumulate)
- No "testing phase" at end (continuous testing)

### 4. Simple Decision-Making
- User approves plan once (upfront)
- No back-and-forth on small decisions
- Trust Qwen's code + Claude's integration

---

## Daily Workflow Template

**Evening (User's Time)**:
1. Check Claude's progress from previous day
2. Paste latest Qwen output to Claude
3. Start next Qwen task (paste new prompt)
4. Let Qwen run overnight

**Morning (Claude's Time)**:
1. Integrate Qwen's overnight output
2. Test + fix bugs
3. Report status to user
4. Give user next Qwen prompt to paste

**Repeat for 10-14 days → Done!**

---

## Risk Mitigation

**Risk 1**: Qwen generates buggy code
- **Mitigation**: Claude tests immediately, fixes bugs same day
- **Impact**: Low (Claude is good at debugging)

**Risk 2**: Integration takes longer than expected
- **Mitigation**: Buffer days (11-14) for catch-up
- **Impact**: Medium (might stretch to 2 weeks instead of 10 days)

**Risk 3**: User unavailable to paste Qwen outputs
- **Mitigation**: Qwen can generate multiple files in one session (paste 2-3 prompts at once)
- **Impact**: Low (flexible scheduling)

**Risk 4**: GPU overheats or crashes overnight
- **Mitigation**: Qwen saves checkpoints, Claude can resume from partial output
- **Impact**: Low (lose max 1 night of work)

---

## Success Metrics

**By Day 5**: First backtest running on RIVERUSDT 5m
**By Day 7**: Optimization complete on 5 low-price coins
**By Day 10**: Full ML pipeline (XGBoost + SHAP) working
**By Day 14**: Production-ready platform deployed

**Final Deliverable**:
- ✅ 44 Python files (~8,850 lines)
- ✅ Streamlit GUI (6 tabs)
- ✅ Parameter optimization (grid, Bayesian, walk-forward)
- ✅ ML meta-labeling (XGBoost + SHAP)
- ✅ Exchange integration (BingX, WEEX)
- ✅ Full test suite (unit + integration)
- ✅ Complete documentation
- ✅ GitHub repo + CI/CD

**Time**: 10-14 days (not 3-4 weeks!)

---

**Start Tonight**: Qwen Task 1 (5 core files) already running overnight!
