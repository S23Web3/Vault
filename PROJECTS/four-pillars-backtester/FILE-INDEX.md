# File Index -- Four Pillars Backtester
## Token-Optimized Quick Reference

**Updated:** 2026-02-16 | **Root:** `PROJECTS/four-pillars-backtester/`

---

## ACTIVE CODE (what you actually modify)

### Dashboard
| File | Lines | Purpose |
|------|-------|---------|
| `scripts/dashboard.py` | 1897 | Main Streamlit app, all 4 modes |

### Engine (v3.8.4)
| File | Lines | Purpose |
|------|-------|---------|
| `engine/backtester_v384.py` | 580 | Multi-slot bar-by-bar execution |
| `engine/position_v384.py` | 295 | PositionSlot384 with scale-out |
| `engine/avwap.py` | 52 | AVWAP center + sigma bands |
| `engine/commission.py` | 106 | Rate-based + daily 17:00 UTC rebate |

### Signals (v3.8.3 pipeline)
| File | Lines | Purpose |
|------|-------|---------|
| `signals/four_pillars_v383.py` | 111 | compute_signals_v383() entry point |
| `signals/state_machine_v383.py` | 339 | A/B/C/D + ADD/RE state machine |
| `signals/stochastics.py` | 63 | 4-K stochastic (9/14/40/60) |
| `signals/clouds.py` | 85 | Ripster EMA clouds 2-5 |

### Data
| File | Lines | Purpose |
|------|-------|---------|
| `data/fetcher.py` | 252 | BybitFetcher, v5 API, public |
| `data/normalizer.py` | 542 | Universal CSV-to-parquet, 6 formats |
| `data/db.py` | 219 | PostgreSQL interface (PG16, port 5433) |

### Utils (Portfolio Enhancement v3 -- 9 bugs fixed from v2 audit)
| File | Lines | Purpose |
|------|-------|---------|
| `utils/portfolio_manager.py` | ~100 | Save/load/list/delete portfolio JSON |
| `utils/coin_analysis.py` | ~150 | Extended metrics (Sortino uses bar_count, monthly PnL via dt_index) |
| `utils/pdf_exporter.py` | ~300 | Multi-page PDF with charts |
| `utils/capital_model.py` | ~250 | Unified capital (rebuilds equity, maps bars cross-coin, no MFE bias) |

### BBW Simulator Pipeline
| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `signals/bbwp.py` | 295 | Layer 1: BBWP calculator | DONE |
| `signals/bbw_sequence.py` | 168 | Layer 2: Sequence tracker | DONE |
| `research/bbw_forward_returns.py` | 121 | Layer 3: Forward returns | DONE |
| `research/bbw_simulator.py` | 586 | Layer 4: Grid search engine | DONE |
| `research/bbw_monte_carlo.py` | 514 | Layer 4b: Monte Carlo | DONE |
| `research/bbw_report.py` | 341 | Layer 5: CSV reports | DONE |

### ML Pipeline (Vince)
| File | Lines | Purpose |
|------|-------|---------|
| `ml/features_v2.py` | 334 | Feature extraction |
| `ml/xgboost_trainer.py` | 134 | XGBoost training |
| `ml/meta_label.py` | 147 | Secondary labeling |
| `ml/shap_analyzer.py` | 117 | SHAP interpretation |
| `ml/bet_sizing.py` | 121 | Position sizing |

---

## TESTS & DEBUG

| File | Tests | Purpose |
|------|-------|---------|
| `tests/test_bbwp.py` | 67 | BBW Layer 1 |
| `tests/test_bbw_sequence.py` | 68 | BBW Layer 2 |
| `tests/test_forward_returns.py` | 102 | BBW Layer 3 |
| `tests/test_bbw_simulator.py` | 55 | BBW Layer 4 |
| `tests/test_bbw_monte_carlo.py` | 45 | BBW Layer 4b |
| `tests/test_bbw_report.py` | 58 | BBW Layer 5 |
| `tests/test_portfolio_enhancements.py` | ~65 | Portfolio utils v3 (realistic trades_df columns) |
| `scripts/debug_portfolio_enhancements.py` | ~50 | Portfolio v3 bug fix verification |
| `scripts/build_dashboard_portfolio_v3.py` | ~1500 | Master build (creates all utils + tests) |

---

## KEY PATHS (copy-paste ready)

```
# Project root
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester

# Dashboard
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard.py

# Cache (399 coins, parquet)
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\cache\

# Sweep progress
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\data\output\sweep_progress_v384.csv

# Portfolio templates
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\portfolios\

# PDF reports output
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\results\pdf_reports\

# Design docs
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-DESIGN.md
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\BBW-SIMULATOR-ARCHITECTURE.md
C:\Users\User\Documents\Obsidian Vault\02-STRATEGY\Indicators\ATR-SL-MOVEMENT-BUILD-GUIDANCE.md
```

---

## LEGACY (do NOT modify)

| Dir | Contents |
|-----|----------|
| `engine/backtester.py` | v3.0 original (237L) |
| `engine/backtester_v382.py` | v3.8.2 (410L) |
| `engine/backtester_v383.py` | v3.8.3 (579L) |
| `engine/backtester_v385.py` | v3.8.5 staging candidate (379L) |
| `signals/state_machine.py` | v3.0 original (225L) |
| `signals/state_machine_v382.py` | v3.8.2 (240L) |
| `staging/` | v3.8.5 staging area (not deployed) |

---

## DIRECTORY MAP

```
four-pillars-backtester/
  |-- DASHBOARD-DESIGN.md      <-- living design doc
  |-- FILE-INDEX.md             <-- this file
  |-- config.yaml, .env, requirements.txt
  |
  |-- engine/                   <-- backtester core (v384 active)
  |-- signals/                  <-- signal pipeline (v383 + BBW L1-L2)
  |-- research/                 <-- BBW L3-L5 + Monte Carlo
  |-- data/                     <-- fetcher, normalizer, cache
  |     |-- cache/              <-- 399 coins parquet
  |     |-- output/             <-- sweep CSV, param logs
  |-- ml/                       <-- Vince ML pipeline (9 modules)
  |-- optimizer/                <-- grid search, bayesian, walk-forward
  |-- utils/                    <-- NEW: portfolio mgr, analysis, PDF, capital
  |-- portfolios/               <-- NEW: saved portfolio JSON templates
  |-- tests/                    <-- all test suites
  |-- scripts/                  <-- dashboard, build scripts, debug, sanity
  |-- results/                  <-- CSV results, PDF reports, BBW reports
  |-- staging/                  <-- v3.8.5 candidate (not deployed)
  |-- indicators/               <-- Pine Script source files
```

---

## IMPORT PATTERNS

```python
# From dashboard.py (or any script in scripts/):
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.fetcher import BybitFetcher
from data.normalizer import OHLCVNormalizer, NormalizerError
from signals.four_pillars_v383 import compute_signals_v383
from engine.backtester_v384 import Backtester384
from utils.portfolio_manager import save_portfolio, load_portfolio, list_portfolios
from utils.coin_analysis import compute_extended_metrics
from utils.pdf_exporter import generate_portfolio_pdf, check_dependencies
from utils.capital_model import apply_capital_constraints, format_capital_summary
```
