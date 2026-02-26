# VINCE Architecture Flow

```mermaid
graph TB
    Start([Market Data]) --> Fetch[data/fetcher.py]
    
    Fetch --> DB[(PostgreSQL)]
    DB --> OHLCV[Raw OHLCV<br/>399 coins]
    
    OHLCV --> Stoch[signals/stochastics.py]
    OHLCV --> Clouds[signals/clouds.py]
    Stoch --> StateMachine[signals/state_machine.py]
    Clouds --> StateMachine
    StateMachine --> Signals[A/B/C Signals]
    
    Signals --> Backtester[engine/backtester.py]
    Backtester --> Position[engine/position.py]
    Position --> Commission[engine/commission.py]
    Commission --> TradeDB[(Trade Results)]
    
    TradeDB --> Features[ml/features.py]
    Features --> XGBoost[ml/meta_label.py]
    XGBoost --> SHAP[ml/shap_analyzer.py]
    SHAP --> Loser[ml/loser_analysis.py]
    Loser --> VINCE{VINCE Brain}
    
    VINCE --> Skip[Skip Trade]
    VINCE --> Take[Take Trade]
    VINCE --> Cloud4[Cloud 4 Trail]
    VINCE --> StaticSL[Static SL]
    
    VINCE --> Dashboard[scripts/dashboard.py]
    Dashboard --> Tab1[Tab 1: Overview]
    Dashboard --> Tab2[Tab 2: Trades]
    Dashboard --> Tab3[Tab 3: MFE/MAE]
    Dashboard --> Tab4[Tab 4: ML]
    Dashboard --> Tab5[Tab 5: Validation]
    
    Tab4 -.Retrain.-> XGBoost
    Cloud4 -.Perf Data.-> Features
    
    classDef dataLayer fill:#1f77b4,stroke:#333,color:#fff
    classDef signalLayer fill:#ff7f0e,stroke:#333,color:#fff
    classDef engineLayer fill:#2ca02c,stroke:#333,color:#fff
    classDef mlLayer fill:#d62728,stroke:#333,color:#fff
    classDef decisionLayer fill:#9467bd,stroke:#333,color:#fff
    classDef dashLayer fill:#ffe66d,stroke:#333,color:#000
    
    class Fetch,DB,OHLCV dataLayer
    class Stoch,Clouds,StateMachine,Signals signalLayer
    class Backtester,Position,Commission,TradeDB engineLayer
    class Features,XGBoost,SHAP,Loser mlLayer
    class VINCE,Skip,Take,Cloud4,StaticSL decisionLayer
    class Dashboard,Tab1,Tab2,Tab3,Tab4,Tab5 dashLayer
```

---

## Daily VINCE Training Schedule

```mermaid
gantt
    title VINCE Automated Learning Cycle
    dateFormat HH:mm
    axisFormat %H:%M
    
    section Data Collection
    Fetch new data (last 24h)    :fetch, 17:00, 5m
    
    section Processing
    Incremental backtest          :backtest, after fetch, 10m
    Extract features              :features, after backtest, 3m
    
    section ML Training
    XGBoost retrain (GPU)         :xgboost, after features, 2m
    Update SHAP values            :shap, after xgboost, 1m
    
    section Validation
    Save checkpoint               :save, after shap, 1m
    Update dashboard metrics      :dash, after save, 1m
    
    section Ready
    VINCE ready for next day      :milestone, after dash, 0m
```

---

## File Structure

```
four-pillars-backtester/
├── data/
│   ├── fetcher.py          # Bybit + WEEX API
│   ├── db.py               # PostgreSQL connection
│   └── cache/              # 399 coins, 1.74 GB
│
├── signals/
│   ├── stochastics.py      # 9/14/40/60 K values
│   ├── clouds.py           # Ripster 2/3/4
│   ├── state_machine.py    # A/B/C grading
│   └── four_pillars.py     # Orchestrator
│
├── engine/
│   ├── backtester.py       # Bar-by-bar loop
│   ├── position.py         # MFE/MAE tracking
│   ├── commission.py       # 0.08% + rebate
│   └── exit_manager.py     # BE strategies
│
├── ml/
│   ├── features.py         # 14 features
│   ├── meta_label.py       # XGBoost (GPU)
│   ├── shap_analyzer.py    # Explainability
│   └── loser_analysis.py   # Sweeney A/B/C/D
│
├── scripts/
│   ├── dashboard.py        # Streamlit 5-tab
│   ├── vince_daily_train.py # Automated training
│   └── visualize_flow.py   # This generates diagrams
│
└── staging/
    └── dashboard.py        # 5-tab ML version (deploy this)
```

---

## VINCE Learning Loop

```mermaid
flowchart LR
    A[New Trade] --> B{VINCE Predict}
    B -->|Skip| C[No Entry]
    B -->|Take| D[Enter Trade]
    
    D --> E[Monitor Position]
    E --> F{Exit Decision}
    F -->|Cloud 4| G[Trail Cloud 4]
    F -->|Static SL| H[Fixed SL]
    
    G --> I[Trade Complete]
    H --> I
    C --> I
    
    I --> J[Store Results]
    J --> K[Extract Features]
    K --> L[Retrain XGBoost]
    L --> B
    
    style B fill:#9467bd,stroke:#333,color:#fff
    style L fill:#d62728,stroke:#333,color:#fff
```

---

## How to Use

### View in Obsidian
Open this file in Obsidian - Mermaid diagrams render automatically.

### Generate Interactive Version
```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"
python scripts\visualize_flow.py
```
Opens browser with clickable Sankey diagram at `data/output/vince_flow.html`

### Deploy Dashboard
```powershell
# Copy staging files to production
Copy-Item staging\dashboard.py scripts\dashboard.py -Force
streamlit run scripts\dashboard.py
```
