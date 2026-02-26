"""
Build script: Section A -- Foundation Documentation.
Creates VERSION-MASTER.md and docs/vince-ml/VINCE-ML-UML-DIAGRAMS.md.

Run: python scripts/build_docs_v1.py
"""

import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ERRORS = []


def safe_write(path: Path, content: str) -> bool:
    """Write file if it does not already exist; return True on success."""
    if path.exists():
        print("  SKIP (exists): " + str(path))
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("  WROTE: " + str(path))
    return True


def build_version_master() -> str:
    """Return VERSION-MASTER.md content."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""\
# VERSION-MASTER.md
**Generated:** {ts}
**Source:** scripts/build_docs_v1.py

---

## Component Versions

| Component | Version | File | Status |
|-----------|---------|------|--------|
| Backtester Engine | v3.8.4 | engine/backtester_v384.py | STABLE |
| State Machine | v3.8.3 | signals/state_machine_v383.py | STABLE |
| Signal Pipeline | v3.8.3 | signals/four_pillars_v383.py | STABLE |
| Commission Model | v1.0 | engine/commission.py | STABLE |
| Dashboard | v3.9.1 | scripts/dashboard_v391.py | STABLE |
| Capital Model | v2.0 | utils/capital_model_v2.py | STABLE |
| PDF Exporter | v2.0 | utils/pdf_exporter_v2.py | STABLE |
| Stochastics | v1.0 | signals/stochastics.py | STABLE |
| Clouds | v1.0 | signals/clouds.py | STABLE |
| BBWP | v1.0 | signals/bbwp.py | STABLE |
| BBW Sequence | v1.0 | signals/bbw_sequence.py | STABLE |
| BBW Simulator | v1.0 | research/bbw_simulator.py | STABLE |
| BBW Monte Carlo | v1.0 | research/bbw_monte_carlo.py | STABLE |
| BBW Report | v1.0 | research/bbw_report.py | STABLE |
| Coin Classifier | v1.0 | research/coin_classifier.py | STABLE |
| Feature Extractor | v1.0 | ml/features.py | BUGS (see below) |
| Feature Extractor v2 | v2.0 | ml/features_v2.py | BUGS (see below) |
| Feature Extractor v3 | v3.0 | ml/features_v3.py | PLANNED |
| XGBoost Trainer | v1.0 | ml/xgboost_trainer.py | BUGS (see below) |
| XGBoost Trainer v2 | v2.0 | ml/xgboost_trainer_v2.py | PLANNED |
| SHAP Analyzer | v1.0 | ml/shap_analyzer.py | BUGS (see below) |
| SHAP Analyzer v2 | v2.0 | ml/shap_analyzer_v2.py | PLANNED |
| Bet Sizing | v1.0 | ml/bet_sizing.py | BUGS (see below) |
| Bet Sizing v2 | v2.0 | ml/bet_sizing_v2.py | PLANNED |
| Purged CV | v1.0 | ml/purged_cv.py | BUILT |
| Walk Forward | v1.0 | ml/walk_forward.py | BUILT |
| Coin Features | v1.0 | ml/coin_features.py | BUILT |
| Training Pipeline | v1.0 | ml/training_pipeline.py | BUILT |
| Triple Barrier | v1.0 | ml/triple_barrier.py | BUILT (Phase 2) |
| Meta Label | v1.0 | ml/meta_label.py | BUILT (Phase 2) |
| Loser Analysis | v1.0 | ml/loser_analysis.py | BUILT |
| Vince Model (PyTorch) | v1.0 | ml/vince_model.py | BUILT (Phase 2) |
| Strategy Plugin Base | v1.0 | strategies/base.py | PLANNED |
| Four Pillars Plugin | v1.0 | strategies/four_pillars.py | PLANNED |
| Train Vince CLI | v1.0 | scripts/train_vince.py | PLANNED |

---

## Known Bugs (v1 modules)

### ml/features.py + ml/features_v2.py
- **dt_series.iloc[i]** on DatetimeIndex: AttributeError (DatetimeIndex has no .iloc)
- **np.isnan() on int-dtype**: TypeError when cloud3_bull/price_pos are int64
- **get_feature_columns()**: missing duration_bars from returned list

### ml/xgboost_trainer.py
- **use_label_encoder=False**: removed in XGBoost >= 1.6, causes TypeError
- **mask indexing**: y[mask.values] can silently misalign if y is a misaligned Series
- **No GPU params**: missing device='cuda' and tree_method='hist'

### ml/shap_analyzer.py
- **No empty array guard**: shap_values on empty X crashes downstream
- **Binary SHAP version**: old shap returns list of two arrays, not handled

### ml/bet_sizing.py
- **Silent zero-return**: avg_loss=0 guard returns zeros with no warning

---

## Planned Versions

### v3 Feature Extractor (ml/features_v3.py)
- Fixes all 3 bugs from v1/v2
- 26 features from v2 + duration_bars = 27 feature columns
- Uses pd.isna() instead of np.isnan() for int-safe NaN checks
- dt_series always wrapped in pd.Series for .iloc compatibility

### v2 XGBoost Trainer (ml/xgboost_trainer_v2.py)
- GPU mandatory: device='cuda', tree_method='hist'
- Removed use_label_encoder
- Safe mask indexing with np.asarray()

### v2 SHAP Analyzer (ml/shap_analyzer_v2.py)
- Empty array guard on compute()
- Binary shap list-vs-array normalization

### v2 Bet Sizing (ml/bet_sizing_v2.py)
- Logging on guard triggers instead of silent zeros

### Strategy Plugin System (strategies/)
- Abstract base: strategies/base.py
- First implementation: strategies/four_pillars.py
- Model isolation: models/{{strategy_name}}/ per strategy

### Train Vince CLI (scripts/train_vince.py)
- 12-step pipeline: load -> enrich -> signals -> backtest -> features -> label -> filter -> validate -> train -> SHAP -> bet_sizing -> save
- Per-coin XGBoost auditors
- GPU mandatory (fail fast)
- Walk-forward + purged CV validation modes

---

## Data Infrastructure

| Asset | File | Records |
|-------|------|---------|
| Coin Tiers | results/coin_tiers.csv | 399 coins, KMeans 3-5 clusters |
| Coin Pools | data/coin_pools.json | 60/20/20 split (A/B/C), seed=42 |
| OHLCV Cache | data/cache/ | 399 coins, 1m+5m parquets |
| Period 2023-2024 | data/periods/2023-2024/ | 166 coins |
| Period 2024-2025 | data/periods/2024-2025/ | 257 coins |
| CoinGecko | data/coingecko/ | Market cap, categories |
"""


def build_uml_diagrams() -> str:
    """Return VINCE-ML-UML-DIAGRAMS.md content."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""\
# VINCE ML Pipeline -- UML Diagrams
**Generated:** {ts}
**Source:** scripts/build_docs_v1.py

---

## 1. Training Pipeline (12-step sequence)

```mermaid
sequenceDiagram
    participant User
    participant CLI as train_vince.py
    participant Strategy as StrategyPlugin
    participant BT as Backtester384
    participant FE as features_v3
    participant XGB as xgboost_trainer_v2
    participant SHAP as shap_analyzer_v2
    participant BS as bet_sizing_v2

    User->>CLI: --symbol RIVERUSDT --timeframe 5m
    CLI->>CLI: 1. GPU pre-flight check (CUDA mandatory)
    CLI->>Strategy: 2. load_strategy("four_pillars")
    CLI->>CLI: 3. Load OHLCV (data/cache/RIVERUSDT_5m.parquet)
    CLI->>Strategy: 4. enrich_ohlcv(df) -- ATR, stochastics, clouds
    CLI->>Strategy: 5. compute_signals(df) -- state machine
    CLI->>BT: 6. run(df) -- execute trades
    BT-->>CLI: trades_df, metrics, equity_curve
    CLI->>Strategy: 7. extract_features(trades_df, df)
    Strategy->>FE: extract_trade_features()
    FE-->>CLI: X (feature matrix)
    CLI->>Strategy: 8. label_trades(trades_df, mode)
    Strategy-->>CLI: y (binary labels)
    CLI->>CLI: 9. Grade filtering (optional --grade-filter D,R)
    CLI->>CLI: 10. Validation (purged CV or walk-forward)
    CLI->>XGB: 11. train_xgboost(X, y, device=cuda)
    XGB-->>CLI: model + metrics
    CLI->>SHAP: 12. compute(X) -- feature attribution
    SHAP-->>CLI: shap_values
    CLI->>BS: 13. kelly_sizing(proba, avg_win, avg_loss)
    BS-->>CLI: sizing simulation
    CLI->>CLI: 14. Save model + report JSON
    CLI-->>User: models/RIVERUSDT_xgb_YYYYMMDD.json
```

---

## 2. Live Inference Flow (Phase 2 -- 3-branch fusion)

```mermaid
flowchart LR
    subgraph Input
        OHLCV[Raw OHLCV Bar]
        SIGNAL[Four Pillars Signal]
    end

    subgraph VinceModel["Vince 3-Branch Model (PyTorch)"]
        B1[Branch 1: Trade Features<br/>13-26 numeric]
        B2[Branch 2: Grade + Direction<br/>Embedding lookup]
        B3[Branch 3: Coin Context<br/>10 OHLCV-derived features]
        FUSION[Fusion Layer<br/>Concat + Linear + Sigmoid]
    end

    subgraph Output
        PROB[Win Probability 0-1]
        SIZE[Bet Size via Kelly]
        DECISION{{TAKE / SKIP}}
    end

    OHLCV --> B1
    OHLCV --> B3
    SIGNAL --> B2
    B1 --> FUSION
    B2 --> FUSION
    B3 --> FUSION
    FUSION --> PROB
    PROB --> SIZE
    SIZE --> DECISION
```

---

## 3. Component Architecture

```mermaid
graph TB
    subgraph Strategies["Strategy Plugins"]
        BASE[strategies/base.py<br/>StrategyPlugin ABC]
        FP[strategies/four_pillars.py<br/>First implementation]
        BASE --> FP
    end

    subgraph Signals["Signal Generation"]
        STOCH[signals/stochastics.py<br/>4 Raw K values]
        CLOUD[signals/clouds.py<br/>Ripster EMAs + price_pos]
        SM[signals/state_machine_v383.py<br/>A/B/C/D + R + ADD]
        FPV[signals/four_pillars_v383.py<br/>Orchestrator]
        STOCH --> FPV
        CLOUD --> FPV
        SM --> FPV
    end

    subgraph Engine["Execution"]
        BT[engine/backtester_v384.py<br/>Multi-slot executor]
        COMM[engine/commission.py<br/>Taker 0.08% / Maker 0.02%]
        BT --> COMM
    end

    subgraph ML["ML Pipeline"]
        FEAT[ml/features_v3.py<br/>27 per-trade features]
        COIN[ml/coin_features.py<br/>10 OHLCV-derived]
        XGB[ml/xgboost_trainer_v2.py<br/>GPU-accelerated]
        SHAP_M[ml/shap_analyzer_v2.py<br/>Feature attribution]
        PCV[ml/purged_cv.py<br/>De Prado Ch.7]
        WF[ml/walk_forward.py<br/>WFE scoring]
        BET[ml/bet_sizing_v2.py<br/>Kelly / linear / binary]
    end

    subgraph Phase2["Phase 2 (Future)"]
        TB[ml/triple_barrier.py<br/>De Prado Ch.3]
        META[ml/meta_label.py<br/>Secondary classifier]
        VM[ml/vince_model.py<br/>PyTorch 3-branch]
    end

    FP --> FPV
    FP --> FEAT
    FPV --> BT
    BT --> FEAT
    FEAT --> XGB
    COIN --> XGB
    XGB --> SHAP_M
    XGB --> BET
    PCV --> XGB
    WF --> XGB
```

---

## 4. Data Split Protection (Pool Immutability)

```mermaid
flowchart TD
    subgraph Coins["399 Coins (data/cache/)"]
        ALL[All symbols]
    end

    subgraph Assignment["Pool Assignment (seed=42, frozen)"]
        SPLIT{{classify_coin_tiers + stratified split}}
    end

    subgraph Pools["Three Pools (IMMUTABLE after creation)"]
        PA["Pool A: ~240 coins (60%)<br/>TRAINING<br/>Used for: XGBoost fit, SHAP, feature selection"]
        PB["Pool B: ~80 coins (20%)<br/>VALIDATION<br/>Used for: hyperparameter tuning, WFE, early stopping"]
        PC["Pool C: ~79 coins (20%)<br/>HOLDOUT<br/>NEVER touched during development<br/>Final evaluation ONLY"]
    end

    subgraph Rules["Immutability Rules"]
        R1["Once coin_pools.json exists, NEVER regenerate"]
        R2["New coins added to Pool C only"]
        R3["Pool C results NOT used for model selection"]
        R4["frozen_date timestamp in JSON"]
    end

    ALL --> SPLIT
    SPLIT --> PA
    SPLIT --> PB
    SPLIT --> PC
    PA -.-> R1
    PB -.-> R1
    PC -.-> R2
    PC -.-> R3
```
"""


def main():
    """Build Section A documentation files."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] === Section A: Foundation Documentation ===")

    # 1. VERSION-MASTER.md
    vm_path = ROOT / "VERSION-MASTER.md"
    safe_write(vm_path, build_version_master())

    # 2. UML Diagrams
    uml_path = ROOT / "docs" / "vince-ml" / "VINCE-ML-UML-DIAGRAMS.md"
    safe_write(uml_path, build_uml_diagrams())

    # Summary
    ts2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ERRORS:
        print(f"[{ts2}] BUILD FAILED -- errors: " + ", ".join(ERRORS))
        sys.exit(1)
    else:
        print(f"[{ts2}] BUILD OK -- 2 documentation files created")
        print("  - " + str(vm_path))
        print("  - " + str(uml_path))


if __name__ == "__main__":
    main()
