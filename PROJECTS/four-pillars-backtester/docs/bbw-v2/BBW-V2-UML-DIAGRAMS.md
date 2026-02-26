# BBW V2 - Complete UML Diagrams
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS.md`  
**Date:** 2026-02-17  
**Version:** 2.1

---

## 1. Component Architecture Diagram

```mermaid
graph TB
    %% Data Source
    CACHE[(Cached Data<br/>data/cache/*.parquet)]

    %% Data Pipeline Layers - COMPLETE
    subgraph DATA["Data Pipeline - Complete"]
        L1[Layer 1: BBWP Calculator<br/>signals/bbwp.py<br/>Input: OHLC<br/>Output: BBW states]
        L2[Layer 2: Sequence Tracker<br/>signals/bbw_sequence.py<br/>Input: BBW states<br/>Output: State transitions]
        L3[Layer 3: Forward Returns<br/>research/bbw_forward_returns.py<br/>Input: OHLC<br/>Output: 17 forward-looking metrics]
    end

    %% Backtester System - COMPLETE
    subgraph BACKTEST["Backtester System - Complete"]
        DASH[Dashboard v3.9.1<br/>scripts/dashboard_v391.py<br/>Orchestrates 400+ coin sweeps]
        BT[Backtester v3.8.5<br/>engine/backtester_v385.py<br/>Four Pillars Strategy<br/>93% success rate]
    end

    %% BBW Analysis - LAYERS 4-4b COMPLETE, LAYER 5 PENDING
    subgraph ANALYSIS["BBW Analysis V2"]
        L4[Layer 4: Results Analyzer<br/>research/bbw_analyzer_v2.py<br/>Groups by state×direction×LSG<br/>BE+fees success rates]
        L4b[Layer 4b: Monte Carlo<br/>research/bbw_monte_carlo_v2.py<br/>Bootstrap validation<br/>Verdicts: ROBUST/FRAGILE/etc]
        L5[Layer 5: VINCE Features<br/>research/bbw_report_v2.py<br/>⚡ PENDING BUILD<br/>Generates training CSVs]
    end

    %% VINCE ML - FUTURE
    subgraph ML["VINCE ML - Future"]
        VINCE_LOCAL[VINCE Local Training<br/>ml/vince_model.py<br/>XGBoost + PyTorch<br/>Learns optimal LSG]
        VINCE_CLOUD[VINCE Cloud Inference<br/>Real-time API<br/>Provides LSG predictions]
    end

    %% Data Flow
    CACHE --> L1
    CACHE --> BT
    L1 --> L2
    L2 --> L3
    
    DASH --> BT
    BT -->|Trade results| L4
    L2 -->|BBW states| L4
    L3 -.->|Forward metrics| L5
    
    L4 -->|Per-trade PnL| L4b
    L4b -->|Verdicts| L5
    L5 -->|Training CSVs| VINCE_LOCAL
    
    VINCE_LOCAL -.->|Trained models| VINCE_CLOUD
    VINCE_CLOUD -.->|Optimal LSG| BT

    %% Styling
    classDef complete fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef pending fill:#FFB6C1,stroke:#DC143C,stroke-width:3px
    classDef future fill:#DDA0DD,stroke:#9370DB,stroke-width:2px
    classDef data fill:#87CEEB,stroke:#4682B4,stroke-width:2px

    class CACHE data
    class L1,L2,L3,DASH,BT,L4,L4b complete
    class L5 pending
    class VINCE_LOCAL,VINCE_CLOUD future
```

---

## 2. Data Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant Cache as Cached Data
    participant L1 as Layer 1 BBWP
    participant L2 as Layer 2 Sequence
    participant L3 as Layer 3 Forward Returns
    participant BT as Backtester
    participant L4 as Layer 4 Analyzer
    participant L4b as Layer 4b Monte Carlo
    participant L5 as Layer 5 Features
    participant VINCE as VINCE ML

    Note over Cache,VINCE: Historical Analysis Pipeline
    
    Cache->>L1: OHLC bars
    L1->>L2: BBW states (7 types)
    L2->>L3: State sequences
    L3->>L3: Calculate 17 forward metrics
    
    Cache->>BT: OHLC bars
    BT->>BT: Execute Four Pillars strategy
    BT->>L4: Trade384 results
    L2->>L4: BBW states for enrichment
    
    L4->>L4: Group by state×direction×LSG
    L4->>L4b: Per-trade PnL lists
    L4b->>L4b: Bootstrap + permutation (1000 iter)
    L4b->>L5: Verdicts + confidence intervals
    
    L3-->>L5: Forward return metrics (optional)
    L4->>L5: Grouped performance
    L5->>L5: Generate VINCE features
    L5->>VINCE: Training CSVs

    Note over VINCE: Local Training Phase
    VINCE->>VINCE: Train XGBoost/PyTorch
    
    Note over VINCE: Cloud Deployment (Future)
    VINCE-->>BT: Real-time LSG predictions
```

---

## 3. Layer 3 Output Schema

```mermaid
classDiagram
    class ForwardReturnsDF {
        <<DataFrame>>
        +open: float
        +high: float
        +low: float
        +close: float
        +base_vol: float
        +fwd_atr: float
        +fwd_10_max_up_pct: float
        +fwd_10_max_down_pct: float
        +fwd_10_close_pct: float
        +fwd_10_max_up_atr: float
        +fwd_10_max_down_atr: float
        +fwd_10_max_range_atr: float
        +fwd_10_direction: str
        +fwd_10_proper_move: bool
        +fwd_20_max_up_pct: float
        +fwd_20_max_down_pct: float
        +fwd_20_close_pct: float
        +fwd_20_max_up_atr: float
        +fwd_20_max_down_atr: float
        +fwd_20_max_range_atr: float
        +fwd_20_direction: str
        +fwd_20_proper_move: bool
    }
    
    class Layer3 {
        +tag_forward_returns(df, windows, atr_period) DataFrame
        -_calculate_atr(df, period) Series
        -_forward_max(series, window) Series
        -_forward_min(series, window) Series
        -_forward_close(series, window) Series
    }
    
    Layer3 --> ForwardReturnsDF: produces
    
    note for ForwardReturnsDF "17 forward-looking metrics\nPredicts what happens\nin next 10/20 bars"
```

---

## 4. State Transition Diagram (BBW States)

```mermaid
stateDiagram-v2
    [*] --> NORMAL
    
    NORMAL --> BLUE: Compression detected
    BLUE --> BLUE_DOUBLE: Further compression
    BLUE_DOUBLE --> MA_CROSS_UP: Expansion begins (bullish)
    
    NORMAL --> RED: Expansion detected
    RED --> RED_DOUBLE: Further expansion
    RED_DOUBLE --> MA_CROSS_DOWN: Compression begins (bearish)
    
    MA_CROSS_UP --> NORMAL: Return to normal
    MA_CROSS_DOWN --> NORMAL: Return to normal
    
    BLUE --> NORMAL: False signal
    RED --> NORMAL: False signal
    
    note right of BLUE
        Low volatility
        Squeeze setup
    end note
    
    note right of RED
        High volatility
        Trending or reversal
    end note
```

---

## 5. Class Diagram - Layer 4/4b/5 Data Contracts

```mermaid
classDiagram
    class BBWAnalysisResultV2 {
        +results: DataFrame
        +best_combos: DataFrame
        +directional_bias: DataFrame
        +summary: dict
        +symbol: str
        +n_trades_analyzed: int
        +n_states: int
        +date_range: tuple
    }
    
    class MonteCarloResultV2 {
        +state_verdicts: DataFrame
        +confidence_intervals: DataFrame
        +overfit_flags: DataFrame
        +summary: dict
    }
    
    class BBWReportResultV2 {
        +directional_bias: DataFrame
        +be_fees_success: DataFrame
        +vince_features: DataFrame
        +lsg_sensitivity: DataFrame
        +state_summary: DataFrame
        +forward_metrics: DataFrame
        +summary: dict
        +output_dir: str
    }
    
    class Layer4 {
        +analyze_trades() BBWAnalysisResultV2
    }
    
    class Layer4b {
        +run_monte_carlo() MonteCarloResultV2
    }
    
    class Layer5 {
        +generate_vince_features() BBWReportResultV2
    }
    
    Layer4 --> BBWAnalysisResultV2: produces
    Layer4b --> MonteCarloResultV2: produces
    Layer5 --> BBWReportResultV2: produces
    
    Layer5 ..> BBWAnalysisResultV2: consumes
    Layer5 ..> MonteCarloResultV2: consumes
    Layer5 ..> ForwardReturnsDF: consumes (optional)
    
    note for BBWReportResultV2 "Includes forward_metrics\nfrom Layer 3 output"
```

---

## 6. Deployment Diagram - VINCE Local → Cloud

```mermaid
graph LR
    subgraph LOCAL["Local Development"]
        DATA[Historical Data<br/>400+ coins]
        TRAIN[Training Pipeline<br/>train_vince.py]
        MODEL[Trained Models<br/>models/*.json<br/>models/pytorch/*.pt]
    end
    
    subgraph CLOUD["Cloud Production"]
        API[VINCE API<br/>FastAPI/Flask]
        INFERENCE[Inference Engine<br/>Real-time predictions]
        MONITOR[Monitoring<br/>Grafana/Prometheus]
    end
    
    subgraph EXCHANGE["Live Trading"]
        WEBHOOK[n8n Webhook<br/>TradingView alerts]
        EXECUTOR[Trade Executor<br/>Bybit API]
    end
    
    DATA --> TRAIN
    TRAIN --> MODEL
    MODEL -.->|Deploy| API
    
    API --> INFERENCE
    INFERENCE --> MONITOR
    
    WEBHOOK --> API
    API --> EXECUTOR
    
    style LOCAL fill:#90EE90
    style CLOUD fill:#DDA0DD
    style EXCHANGE fill:#FFB6C1
```

---

## 7. Activity Diagram - 400-Coin Sweep

```mermaid
flowchart TD
    START([Start Sweep]) --> LOAD[Load coin list<br/>399 coins]
    LOAD --> LOOP{For each coin}
    
    LOOP -->|Next coin| L1[Layer 1: Calculate BBW]
    L1 --> L2[Layer 2: Track sequences]
    L2 --> L3[Layer 3: Forward returns]
    L3 --> BT[Run backtester<br/>Four Pillars]
    BT --> L4[Layer 4: Analyze results]
    L4 --> L4b[Layer 4b: Monte Carlo]
    L4b --> L5[Layer 5: Generate features]
    L5 --> SAVE[Save CSVs]
    
    SAVE --> CHECK{More coins?}
    CHECK -->|Yes| LOOP
    CHECK -->|No| AGGREGATE[Aggregate all CSVs]
    AGGREGATE --> TRAIN[Train VINCE models]
    TRAIN --> END([Sweep Complete])
    
    style L5 fill:#FFB6C1
    style TRAIN fill:#DDA0DD
```

---

## 8. Component Interaction Diagram

```mermaid
graph TB
    subgraph INPUT["Input Layer"]
        CACHE[(data/cache/<br/>*.parquet)]
    end
    
    subgraph SIGNALS["Signals Layer"]
        L1[bbwp.py]
        L2[bbw_sequence.py]
    end
    
    subgraph RESEARCH["Research Layer"]
        L3[bbw_forward_returns.py]
        L4[bbw_analyzer_v2.py]
        L4b[bbw_monte_carlo_v2.py]
        L5[bbw_report_v2.py]
    end
    
    subgraph ENGINE["Engine Layer"]
        BT[backtester_v385.py]
        COMM[commission.py]
        CAPITAL[capital_model_v2.py]
    end
    
    subgraph ML_LAYER["ML Layer"]
        FEATURES[features.py]
        XGBOOST[xgboost_trainer.py]
        PYTORCH[pytorch/model.py]
        VINCE[vince_model.py]
    end
    
    subgraph OUTPUT["Output Layer"]
        CSV[(Training CSVs)]
        MODELS[(Trained Models)]
    end
    
    CACHE --> L1
    CACHE --> BT
    L1 --> L2
    L2 --> L3
    L2 --> L4
    
    BT --> L4
    COMM --> BT
    CAPITAL --> BT
    
    L3 --> L5
    L4 --> L4b
    L4b --> L5
    
    L5 --> CSV
    CSV --> FEATURES
    FEATURES --> XGBOOST
    FEATURES --> PYTORCH
    XGBOOST --> VINCE
    PYTORCH --> VINCE
    
    VINCE --> MODELS
    MODELS -.-> BT
    
    style L5 fill:#FFB6C1
    style VINCE fill:#DDA0DD
```

---

## Key Corrections from V1 to V2

| Aspect | V1 (Wrong) | V2 (Correct) |
|--------|------------|--------------|
| **BBW Role** | Simulated trades | Analyzes real backtester results |
| **Direction Source** | BBW determined direction | Four Pillars strategy determines direction |
| **Layer Count** | Had Layer 6 | Only 5 layers (VINCE is separate) |
| **Metric** | Win rate | BE+fees rate |
| **Layer 3 Output** | Unclear | Feeds into Layer 5 as VINCE features |
| **VINCE Deployment** | Not specified | Local training → Cloud inference |

---

## Layer 3 Purpose (Clarified)

**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\research\bbw_forward_returns.py`

**What It Does:**
- Pure function, no dependencies on Layer 1/2
- Takes OHLC DataFrame as input
- Adds 17 forward-looking metrics (what happens in next 10/20 bars)
- Output: Same DataFrame + 17 new columns

**17 Columns Added:**
- `fwd_atr` (ATR for normalization)
- Per window (10, 20 bars):
  - `fwd_N_max_up_pct` - Max % upward move
  - `fwd_N_max_down_pct` - Max % downward move
  - `fwd_N_close_pct` - Close-to-close return
  - `fwd_N_max_up_atr` - Max upward move (ATR units)
  - `fwd_N_max_down_atr` - Max downward move (ATR units)
  - `fwd_N_max_range_atr` - Total range (ATR units)
  - `fwd_N_direction` - Direction label (UP/DOWN/NEUTRAL)
  - `fwd_N_proper_move` - Boolean (move > 3 ATR?)

**Integration:** Layer 3 → Layer 5 (forward metrics as VINCE features)

---

## VINCE Deployment Strategy

**Phase 1: Local Training**
- File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\ml\vince_model.py`
- Run on local machine with GPU
- Train XGBoost and PyTorch models
- Validate on held-out coins
- Save trained models

**Phase 2: Cloud Deployment**
- Deploy models to cloud API
- Real-time inference via FastAPI/Flask
- Monitoring with Grafana/Prometheus
- Auto-scaling based on request volume

**Phase 3: Live Integration**
- TradingView alerts → n8n webhook
- n8n queries VINCE cloud API
- VINCE returns optimal LSG
- Execute trade on Bybit with optimized parameters

---

## Status Summary

| Component | File | Status |
|-----------|------|--------|
| Layer 1 | signals/bbwp.py | ✅ Complete |
| Layer 2 | signals/bbw_sequence.py | ✅ Complete |
| Layer 3 | research/bbw_forward_returns.py | ✅ Complete |
| Dashboard | scripts/dashboard_v391.py | ✅ Complete |
| Backtester | engine/backtester_v385.py | ✅ Complete |
| Layer 4 | research/bbw_analyzer_v2.py | ✅ Complete |
| Layer 4b | research/bbw_monte_carlo_v2.py | ✅ Complete |
| Layer 5 | research/bbw_report_v2.py | ⚡ Pending |
| VINCE Local | ml/vince_model.py | 🔮 Future |
| VINCE Cloud | Cloud API | 🔮 Future |

---

**END OF UML DIAGRAMS**
