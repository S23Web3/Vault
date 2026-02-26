# BBW V2 - UML Diagrams (PDF Optimized)
**File:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS-PDF.md`  
**Date:** 2026-02-17  
**Version:** 2.3 - Optimized for PDF Export with Orientation Control

---

<style>
/* Center alignment for all diagrams */
.diagram-container {
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    margin: 2em 0;
}

/* Landscape orientation for specific pages */
@page {
    size: A4 portrait;
    margin: 1cm;
}

@page :nth(2) {
    size: A4 landscape;
}

@page :nth(6) {
    size: A4 landscape;
}

/* Center text and diagrams */
.centered {
    text-align: center;
    margin-left: auto;
    margin-right: auto;
}

h2, h3 {
    text-align: center;
}
</style>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Diagram 1: System Overview

### BBW V2 Complete Architecture

<div class="diagram-container">

```mermaid
graph TB
    CACHE[(Cached OHLC<br/>data/cache/*.parquet)]
    
    L1[Layer 1: BBWP<br/>signals/bbwp.py]
    L2[Layer 2: Sequence<br/>signals/bbw_sequence.py]
    L3[Layer 3: Forward Returns<br/>research/bbw_forward_returns.py]
    
    BT[Backtester v3.8.5<br/>engine/backtester_v385.py]
    
    L4[Layer 4: Analyzer<br/>research/bbw_analyzer_v2.py]
    L4b[Layer 4b: Monte Carlo<br/>research/bbw_monte_carlo_v2.py]
    L5[Layer 5: Features<br/>research/bbw_report_v2.py]
    
    VINCE[VINCE ML<br/>ml/vince_model.py]
    
    CACHE --> L1 --> L2 --> L3
    CACHE --> BT
    BT --> L4
    L2 --> L4
    L3 -.-> L5
    L4 --> L4b --> L5 --> VINCE
    VINCE -.-> BT
    
    classDef complete fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef pending fill:#FFB6C1,stroke:#DC143C,stroke-width:2px
    classDef future fill:#DDA0DD,stroke:#9370DB,stroke-width:2px
    
    class L1,L2,L3,BT,L4,L4b complete
    class L5 pending
    class VINCE future
```

</div>

**Legend:**
- 🟢 Green = Complete
- 🔴 Pink = Pending Build
- 🟣 Purple = Future

</div>

---

<div style="page-break-after: always;"></div>

<!-- LANDSCAPE PAGE -->
<div class="centered" style="width: 100%; height: 100%;">

## Diagram 2: Data Flow Sequence (Landscape)

### Historical Analysis Pipeline

<div class="diagram-container">

```mermaid
sequenceDiagram
    participant Cache as Cached Data
    participant L1 as Layer 1<br/>BBWP
    participant L2 as Layer 2<br/>Sequence
    participant L3 as Layer 3<br/>Forward Returns
    participant BT as Backtester<br/>v3.8.5
    participant L4 as Layer 4<br/>Analyzer
    participant L4b as Layer 4b<br/>Monte Carlo
    participant L5 as Layer 5<br/>Features
    participant VINCE as VINCE<br/>ML
    
    Note over Cache,VINCE: Historical Analysis Pipeline
    
    Cache->>L1: OHLC bars
    L1->>L2: BBW states (7 types)
    L2->>L3: State sequences
    L3->>L3: Calculate 17 forward metrics
    
    Cache->>BT: OHLC bars
    BT->>BT: Execute Four Pillars
    BT->>L4: Trade384 results
    L2->>L4: BBW states
    
    L4->>L4: Group by state×direction×LSG
    L4->>L4b: Per-trade PnL lists
    L4b->>L4b: Bootstrap 1000 iterations
    L4b->>L5: Verdicts + CI
    
    L3-->>L5: Forward metrics
    L4->>L5: Performance data
    L5->>VINCE: Training CSVs
    
    Note over VINCE: Local training phase
```

</div>

**Flow:** Cache → Layers 1-3 → Backtester → Layers 4-5 → VINCE

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Diagram 3: BBW State Transitions

### 7 Volatility States

<div class="diagram-container">

```mermaid
stateDiagram-v2
    [*] --> NORMAL
    
    NORMAL --> BLUE: Compression
    BLUE --> BLUE_DOUBLE: More compression
    BLUE_DOUBLE --> MA_CROSS_UP: Breakout up
    
    NORMAL --> RED: Expansion
    RED --> RED_DOUBLE: More expansion
    RED_DOUBLE --> MA_CROSS_DOWN: Breakdown
    
    MA_CROSS_UP --> NORMAL
    MA_CROSS_DOWN --> NORMAL
    BLUE --> NORMAL
    RED --> NORMAL
```

</div>

**States:**
- BLUE = Low volatility (squeeze)
- RED = High volatility (trending)
- DOUBLE = Extreme levels
- MA_CROSS = Direction confirmed

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Diagram 4: Layer 3 Output

### Forward Returns Schema (17 Columns)

<div class="diagram-container">

```mermaid
classDiagram
    class ForwardReturnsDF {
        +fwd_atr float
        +fwd_10_max_up_pct float
        +fwd_10_max_down_pct float
        +fwd_10_close_pct float
        +fwd_10_max_up_atr float
        +fwd_10_max_down_atr float
        +fwd_10_max_range_atr float
        +fwd_10_direction str
        +fwd_10_proper_move bool
        +fwd_20_* Same 8 metrics
    }
```

</div>

**Purpose:** Predicts what happens in next 10/20 bars

**Integration:** Feeds into Layer 5 as VINCE training features

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Diagram 5: Data Contracts

### Layer 4, 4b, 5 Outputs

<div class="diagram-container">

```mermaid
classDiagram
    class Layer4Output {
        +best_combos DataFrame
        +directional_bias DataFrame
        +summary dict
    }
    
    class Layer4bOutput {
        +state_verdicts DataFrame
        +confidence_intervals DataFrame
        +overfit_flags DataFrame
    }
    
    class Layer5Output {
        +vince_features DataFrame
        +directional_bias DataFrame
        +be_fees_success DataFrame
        +forward_metrics DataFrame
        +lsg_sensitivity DataFrame
    }
    
    Layer5Output ..> Layer4Output
    Layer5Output ..> Layer4bOutput
    Layer5Output ..> ForwardReturnsDF
```

</div>

**Layer 5** consumes outputs from **Layer 4**, **Layer 4b**, and **Layer 3**

</div>

---

<div style="page-break-after: always;"></div>

<!-- LANDSCAPE PAGE -->
<div class="centered" style="width: 100%; height: 100%;">

## Diagram 6: VINCE Deployment (Landscape)

### Local Training → Cloud Inference

<div class="diagram-container">

```mermaid
graph LR
    subgraph LOCAL[Local Desktop - RTX 3060]
        DATA[Historical Data<br/>400 coins<br/>1 year OHLCV]
        TRAIN[Training Pipeline<br/>XGBoost + PyTorch<br/>GPU Accelerated]
        MODEL[Saved Models<br/>models/*.json<br/>models/pytorch/*.pt]
    end
    
    subgraph CLOUD[Cloud API Server]
        API[FastAPI<br/>REST Endpoints<br/>/predict_lsg]
        INFERENCE[Inference Engine<br/>Real-time<br/>Predictions]
        MONITOR[Monitoring<br/>Grafana<br/>Prometheus]
    end
    
    subgraph LIVE[Live Trading System]
        TV[TradingView<br/>Alerts]
        WEBHOOK[n8n Webhook<br/>Alert Processor]
        EXEC[Bybit API<br/>Trade Execution]
    end
    
    DATA --> TRAIN --> MODEL
    MODEL -.->|Deploy| API
    API --> INFERENCE
    INFERENCE --> MONITOR
    
    TV --> WEBHOOK
    WEBHOOK -->|Query LSG| API
    API -->|Optimal LSG| WEBHOOK
    WEBHOOK --> EXEC
    
    style LOCAL fill:#90EE90
    style CLOUD fill:#DDA0DD
    style LIVE fill:#FFB6C1
```

</div>

**Phase 1:** Train locally (RTX 3060)  
**Phase 2:** Deploy to cloud  
**Phase 3:** Live trading integration

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Diagram 7: 400-Coin Sweep

### Training Data Generation Pipeline

<div class="diagram-container">

```mermaid
flowchart TD
    START([Start Sweep]) --> LOAD[Load 399 coins]
    LOAD --> LOOP{For each coin}
    
    LOOP --> L1[Layer 1<br/>BBWP]
    L1 --> L2[Layer 2<br/>Sequence]
    L2 --> L3[Layer 3<br/>Forward Returns]
    L3 --> BT[Backtest<br/>Four Pillars]
    BT --> L4[Layer 4<br/>Analyzer]
    L4 --> L4b[Layer 4b<br/>Monte Carlo]
    L4b --> L5[Layer 5<br/>Features]
    
    L5 --> MORE{More coins?}
    MORE -->|Yes| LOOP
    MORE -->|No| AGG[Aggregate<br/>All CSVs]
    AGG --> TRAIN[Train VINCE<br/>Models]
    TRAIN --> END([Sweep Complete])
    
    style L5 fill:#FFB6C1
    style TRAIN fill:#DDA0DD
```

</div>

**Duration:** ~6-8 hours for 400 coins

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Diagram 8: File Structure

### Component Organization

<div class="diagram-container">

```mermaid
graph TB
    subgraph DATA[Data Layer]
        CACHE[(cache/*.parquet)]
    end
    
    subgraph SIGNALS[Signals Layer]
        L1[bbwp.py]
        L2[bbw_sequence.py]
    end
    
    subgraph RESEARCH[Research Layer]
        L3[bbw_forward_returns.py]
        L4[bbw_analyzer_v2.py]
        L4b[bbw_monte_carlo_v2.py]
        L5[bbw_report_v2.py]
    end
    
    subgraph ENGINE[Engine Layer]
        BT[backtester_v385.py]
    end
    
    subgraph ML[Machine Learning]
        VINCE[vince_model.py]
    end
    
    CACHE --> L1 --> L2
    CACHE --> BT
    L2 --> L3 --> L5
    L2 --> L4
    BT --> L4 --> L4b --> L5
    L5 --> VINCE
```

</div>

**Root:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\`

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

## Summary Tables

### Component Status

| Layer | File | Status | Purpose |
|:-----:|:-----|:------:|:--------|
| L1 | signals/bbwp.py | ✅ Complete | Calculate BBW states |
| L2 | signals/bbw_sequence.py | ✅ Complete | Track state transitions |
| L3 | research/bbw_forward_returns.py | ✅ Complete | Forward-looking metrics |
| - | engine/backtester_v385.py | ✅ Complete | Execute Four Pillars |
| L4 | research/bbw_analyzer_v2.py | ✅ Complete | Analyze trade results |
| L4b | research/bbw_monte_carlo_v2.py | ✅ Complete | Validate robustness |
| L5 | research/bbw_report_v2.py | ⚡ Pending | Generate VINCE features |
| - | ml/vince_model.py | 🔮 Future | ML optimization |

</div>

---

<div style="page-break-after: always;"></div>

<div class="centered">

### Layer 3 Output Columns

| Column | Type | Description |
|:-------|:----:|:------------|
| fwd_atr | float | ATR normalization factor |
| fwd_10_max_up_pct | float | Max % up in 10 bars |
| fwd_10_max_down_pct | float | Max % down in 10 bars |
| fwd_10_close_pct | float | Close return in 10 bars |
| fwd_10_max_up_atr | float | Max up in ATR units |
| fwd_10_max_down_atr | float | Max down in ATR units |
| fwd_10_max_range_atr | float | Total range in ATR |
| fwd_10_direction | str | UP/DOWN/NEUTRAL |
| fwd_10_proper_move | bool | Move > 3 ATR? |
| fwd_20_* | - | Same 8 metrics for 20 bars |

---

### VINCE Deployment Phases

| Phase | Location | Purpose | Status |
|:-----:|:---------|:--------|:------:|
| 1 | Local Desktop | Train models on historical data | 🔮 Future |
| 2 | Cloud API | Real-time inference service | 🔮 Future |
| 3 | Live Trading | n8n webhook integration | 🔮 Future |

---

### V1 vs V2 Corrections

| Aspect | V1 (Wrong) | V2 (Correct) |
|:-------|:-----------|:-------------|
| BBW Role | Simulated trades | Analyzes backtester results |
| Direction | BBW decides | Four Pillars decides |
| Layers | 6 layers | 5 layers (VINCE separate) |
| Metric | Win rate | BE+fees rate |
| Layer 3 | Unclear | Forward metrics → Layer 5 |
| VINCE | Not specified | Local → Cloud deployment |

</div>

---

**END OF PDF-OPTIMIZED DIAGRAMS**

**Export Instructions:**
1. Open in Obsidian
2. Export to PDF
3. **Diagram 2 and 6 automatically landscape**
4. Other pages portrait with centered content
