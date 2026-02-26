# VINCE ML Pipeline -- UML Diagrams
**Generated:** 2026-02-18 12:48:28
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
        DECISION{TAKE / SKIP}
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
        SPLIT{classify_coin_tiers + stratified split}
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
