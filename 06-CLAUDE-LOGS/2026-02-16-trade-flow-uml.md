# Four Pillars - UML Flow Diagrams
**Date:** 2026-02-16 15:50 GST  
**Purpose:** Visual system architecture for mobile review  
**Format:** Mermaid diagrams (render in Obsidian)

---

## Diagram 1: Trade Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> SignalDetection: Entry signal fires
    
    SignalDetection --> GradeEvaluation: Signal confirmed
    SignalDetection --> Idle: Signal rejected
    
    GradeEvaluation --> PositionEntry: Grade A/B/C approved
    GradeEvaluation --> Idle: Grade too weak
    
    PositionEntry --> InitialSL: Position opened
    
    InitialSL --> Monitoring: SL set at entry - (sl_mult × ATR)
    
    Monitoring --> StoppedOut: Price hits SL
    Monitoring --> BERaise: Price moves +be_raise × ATR
    Monitoring --> PartialExit: AVWAP checkpoint hit
    Monitoring --> FullExit: TP hit or manual close
    Monitoring --> AddSignal: ADD signal fires
    
    BERaise --> AVWAPTrailing: SL moved to breakeven
    
    AVWAPTrailing --> StoppedOut: Price hits trailing SL
    AVWAPTrailing --> PartialExit: AVWAP checkpoint hit
    AVWAPTrailing --> FullExit: TP hit or manual close
    AVWAPTrailing --> AddSignal: ADD signal fires
    
    AddSignal --> MultiSlot: New slot opened
    
    MultiSlot --> Monitoring: Each slot independent
    
    PartialExit --> AVWAPTrailing: Remainder continues
    
    StoppedOut --> ReEntryWindow: Check re-entry conditions
    FullExit --> Idle: All slots closed
    
    ReEntryWindow --> PositionEntry: RE signal within N bars
    ReEntryWindow --> Idle: Window expired
    
    note right of InitialSL
        LONG: entry - (sl_mult × ATR)
        SHORT: entry + (sl_mult × ATR)
        Typical sl_mult: 2.0
    end note
    
    note right of BERaise
        Trigger: Price moves +be_raise × ATR
        Action: Move SL to entry price
        Typical be_raise: 4
    end note
    
    note right of AVWAPTrailing
        Ratchets every bar:
        LONG: SL = max(current, AVWAP - band - floor)
        SHORT: SL = min(current, AVWAP + band + floor)
        Never reverses direction
    end note
    
    note right of AddSignal
        Conditions:
        - Existing position profitable
        - New entry signal fires
        - Max slots not reached (4)
        Clones parent AVWAP state
    end note
```

---

## Diagram 2: Entry Grade Decision Tree

```mermaid
graph TD
    Start[Entry Signal Detected] --> Stoch{Quad Stoch<br/>Aligned?}
    
    Stoch -->|Overbought/Oversold| Ripster{Cloud 3<br/>Position?}
    Stoch -->|Not aligned| C[Grade C<br/>Weak Entry]
    
    Ripster -->|Price ABOVE all 3 EMAs<br/>for LONG| AVWAP{AVWAP<br/>Alignment?}
    Ripster -->|Price BELOW all 3 EMAs<br/>for SHORT| AVWAP
    Ripster -->|Inside Cloud 3| B[Grade B<br/>Strong Entry]
    
    AVWAP -->|Price above AVWAP<br/>for LONG| BBW{BBW State<br/>Favorable?}
    AVWAP -->|Price below AVWAP<br/>for SHORT| BBW
    AVWAP -->|Misaligned| B
    
    BBW -->|BLUE/NORMAL<br/>Contraction| A[Grade A<br/>Strongest Entry]
    BBW -->|RED/Neutral| B
    BBW -->|Unfavorable| C
    
    A --> Execute{Execute?}
    B --> Execute
    C --> Execute
    
    Execute -->|Yes| LSG[Select LSG<br/>by BBW State]
    Execute -->|No| Reject[Reject Entry]
    
    LSG --> Open[Open Position]
    
    style A fill:#2d6a4f,stroke:#1b4332,color:#fff
    style B fill:#e9c46a,stroke:#f4a261,color:#000
    style C fill:#e76f51,stroke:#d62828,color:#fff
    
    note1[Cloud 3 Filter:<br/>34/50/72 EMA<br/>Must be clean trend]
    note2[Grade A = All 4 pillars aligned<br/>Grade B = 3/4 pillars<br/>Grade C = 2/4 pillars]
```

---

## Diagram 3: Stop Loss Lifecycle Flow

```mermaid
graph LR
    Entry[Position Entry] --> Initial[Initial SL]
    
    Initial --> |"Price moves<br/>+be_raise × ATR"| BETrigger{BE Raise<br/>Triggered?}
    
    BETrigger -->|Yes| BE[Move SL to<br/>Entry Price]
    BETrigger -->|No| Monitor1[Monitor Price]
    
    Monitor1 --> |Price hits SL| Close1[Close Position]
    Monitor1 --> BETrigger
    
    BE --> AVWAP[AVWAP Trailing<br/>Activated]
    
    AVWAP --> Recalc[Recalculate SL<br/>Every Bar]
    
    Recalc --> |"LONG:<br/>max(current_SL, AVWAP - band - floor)"| Update1[Update SL Up]
    Recalc --> |"SHORT:<br/>min(current_SL, AVWAP + band + floor)"| Update2[Update SL Down]
    
    Update1 --> Monitor2[Monitor Price]
    Update2 --> Monitor2
    
    Monitor2 --> |Price hits trailing SL| Close2[Close Position]
    Monitor2 --> Recalc
    
    style Initial fill:#e76f51,stroke:#d62828,color:#fff
    style BE fill:#e9c46a,stroke:#f4a261,color:#000
    style AVWAP fill:#2d6a4f,stroke:#1b4332,color:#fff
    
    note1["Phase 1: Initial SL<br/>entry ± (sl_mult × ATR)<br/>Fixed distance"]
    note2["Phase 2: BE Raise<br/>Trigger: +be_raise × ATR profit<br/>Action: Move to breakeven"]
    note3["Phase 3: AVWAP Trail<br/>Dynamic ratcheting<br/>Never reverses"]
```

---

## Diagram 4: SL Movement Over Time (v3.9 Planned)

```mermaid
graph TD
    subgraph Phase 1: Initial SL
        P1[Entry: $100.00<br/>ATR: $2.50<br/>sl_mult: 2.0<br/>SL: $95.00]
    end
    
    subgraph Phase 2: BE Raise
        P2[Price reaches $110.00<br/>be_raise × ATR<br/>SL moves to $100.00]
    end
    
    subgraph Phase 3: AVWAP Trailing
        P3A[Bar 1: AVWAP $105.00<br/>SL: max$100, $105-2-1 = $102.00]
        P3B[Bar 2: AVWAP $108.00<br/>SL: max$102, $108-2-1 = $105.00]
        P3C[Bar 3: AVWAP $107.00<br/>SL: max$105, $107-2-1 = $104.00<br/>SL stays $105.00]
    end
    
    P1 --> P2
    P2 --> P3A
    P3A --> P3B
    P3B --> P3C
    
    style P1 fill:#e76f51,stroke:#d62828,color:#fff
    style P2 fill:#e9c46a,stroke:#f4a261,color:#000
    style P3A fill:#2d6a4f,stroke:#1b4332,color:#fff
    style P3B fill:#2d6a4f,stroke:#1b4332,color:#fff
    style P3C fill:#2d6a4f,stroke:#1b4332,color:#fff
```

---

## Diagram 5: ADD Signal Flow

```mermaid
sequenceDiagram
    participant Market
    participant Stoch as Quad Stoch
    participant SM as State Machine
    participant PM as Position Manager
    participant Slot1 as Slot 1 (Original)
    participant Slot2 as Slot 2 (ADD)
    
    Market->>Stoch: Price movement
    Stoch->>SM: Entry signal fires
    SM->>PM: Grade A signal
    PM->>Slot1: Open position<br/>Entry: $100, SL: $95
    
    Note over Slot1: Position now profitable<br/>Price at $108
    
    Market->>Stoch: Another entry signal
    Stoch->>SM: Entry signal (can be Grade B)
    SM->>PM: ADD signal (original still active)
    
    PM->>Slot1: Check if profitable
    Slot1-->>PM: Yes, price > entry
    
    PM->>Slot2: Open ADD slot<br/>Entry: $108, SL: $103
    
    Note over Slot2: Clones Slot 1<br/>AVWAP state
    
    PM->>Slot1: Continue managing
    PM->>Slot2: Independent SL/TP
    
    Market->>Slot1: Price drops to $95
    Slot1->>PM: SL hit, close Slot 1
    
    Note over Slot2: Slot 2 unaffected<br/>continues running
    
    Market->>Slot2: Price continues up
    Slot2->>PM: TP hit at $115
    PM->>Slot2: Close Slot 2
```

---

## Diagram 6: System Architecture (Component Diagram)

```mermaid
graph TB
    subgraph Data Layer
        Cache[(Bybit Cache<br/>399 coins<br/>6.2GB)]
        CG[(CoinGecko<br/>394 coins<br/>5 datasets)]
        Period[(Period Loaders<br/>2023-2025)]
    end
    
    subgraph Signal Pipeline
        BBW1[Layer 1: BBWP<br/>10 columns]
        BBW2[Layer 2: Sequence<br/>9 columns]
        BBW3[Layer 3: Forward Returns<br/>17 columns]
        Stoch[Quad Rotation<br/>Stochastic]
        Ripster[Ripster EMA<br/>Clouds 2-5]
        AVWAP[Anchored VWAP<br/>±3σ bands]
    end
    
    subgraph State Machine
        SM[Four Pillars<br/>State Machine v383]
        Grading[Entry Grading<br/>A/B/C/D]
    end
    
    subgraph Backtester
        BT[Backtester v385<br/>Multi-slot]
        Exit[Exit Manager<br/>SL/TP lifecycle]
        Pos[Position Manager<br/>4 concurrent slots]
    end
    
    subgraph BBW Analysis
        BBW4[Layer 4: Analyzer<br/>Real trade results]
        BBW4b[Layer 4b: Monte Carlo<br/>Bootstrap CI]
        BBW5[Layer 5: VINCE Features<br/>CSV exports]
    end
    
    subgraph VINCE ML
        Module1[Module 1: RFE]
        Module2[Module 2: Features]
        Module3[Module 3: LSG Optimizer]
        Module4[Module 4: Meta-Label]
        Module5[Module 5: Bet Sizing]
    end
    
    subgraph Dashboard
        UI[Streamlit UI<br/>5 tabs]
        Viz[Plotly Charts]
    end
    
    subgraph Live Trading
        N8N[n8n Webhook]
        TV[TradingView Alerts]
        Exec[Exchange API<br/>BingX/WEEX/Bybit]
    end
    
    Cache --> BBW1
    Cache --> Stoch
    Cache --> Ripster
    Cache --> AVWAP
    CG --> Module2
    Period --> BBW1
    
    BBW1 --> BBW2
    BBW2 --> BBW3
    BBW1 --> SM
    Stoch --> SM
    Ripster --> SM
    AVWAP --> SM
    
    SM --> Grading
    Grading --> BT
    BT --> Exit
    BT --> Pos
    Exit --> BT
    Pos --> BT
    
    BT --> BBW4
    BBW4 --> BBW4b
    BBW4b --> BBW5
    
    BBW5 --> Module2
    Module2 --> Module1
    Module1 --> Module3
    Module3 --> Module4
    Module4 --> Module5
    
    BT --> UI
    BBW4 --> UI
    UI --> Viz
    
    Module3 --> N8N
    TV --> N8N
    N8N --> Exec
    
    style BBW5 fill:#ff6b35,stroke:#d62828,color:#fff
    style Module3 fill:#ff6b35,stroke:#d62828,color:#fff
    style N8N fill:#6c757d,stroke:#495057,color:#fff
```

---

## Diagram 7: Critical Path Timeline

```mermaid
gantt
    title Four Pillars - Critical Path (Feb-Mar 2026)
    dateFormat YYYY-MM-DD
    section BBW Pipeline
    Layer 5 completion           :active, bbw5, 2026-02-16, 4d
    splits.json generation        :bbw6, after bbw5, 1d
    
    section Data Prep
    Restore BE raise              :data1, after bbw5, 2d
    400-coin sweep                :data2, after data1, 1d
    Layer 5 CSV exports           :data3, after bbw6, 1d
    
    section VINCE ML
    Module 3 build (LSG Opt)      :vince1, after data3, 5d
    XGBoost training              :vince2, after vince1, 2d
    5-fold cross-validation       :vince3, after vince2, 2d
    Validation (40 coins)         :vince4, after vince3, 2d
    
    section Testing
    Hyperparameter tuning         :test1, after vince4, 3d
    Test set evaluation (79 coins):milestone, test2, after test1, 1d
    
    section Production
    n8n webhook integration       :prod1, after test2, 3d
    Cloud 4 trailing exits        :prod2, after test2, 2d
    Live deployment               :milestone, prod3, after prod1, 1d
    Daily retraining schedule     :prod4, after prod3, 2d
```

---

## Diagram 8: Commission & Rebate Flow

```mermaid
graph LR
    Entry[Entry Order<br/>Size × Leverage × Base] --> EntryFee[Entry Fee<br/>Notional × 0.0008]
    
    Exit[Exit Order<br/>Same Notional] --> ExitFee[Exit Fee<br/>Notional × 0.0008]
    
    EntryFee --> RT[Round-Trip<br/>Commission]
    ExitFee --> RT
    
    RT --> Net[Net PnL<br/>Gross - RT]
    
    Entry --> Volume[Daily Volume<br/>Sum all trades]
    Exit --> Volume
    
    Volume --> Rebate[Rebate Calculation<br/>Volume × 0.0002]
    
    Rebate --> Settlement[Settlement<br/>17:00 UTC Daily]
    
    Settlement --> Credit[Credit to Account]
    
    style RT fill:#e76f51,stroke:#d62828,color:#fff
    style Rebate fill:#2d6a4f,stroke:#1b4332,color:#fff
    
    note1["Example:<br/>$250 base × 1.0 size × 20x = $5,000<br/>RT = $5,000 × 0.0008 × 2 = $8.00"]
    note2["Example:<br/>25 trades × $5,000 = $125,000<br/>Rebate = $125,000 × 0.0002 = $25"]
```

---

## Diagram 9: Data Split Strategy

```mermaid
graph TD
    subgraph Total Dataset
        Total[399 coins × 1 year<br/>~42M bars]
    end
    
    Total --> Train[Training Set<br/>280 coins × 8 months<br/>22.4M bars<br/>53%]
    Total --> Val[Validation Set<br/>40 coins × 12 months<br/>4.2M bars<br/>10%]
    Total --> Test[Test Set FROZEN<br/>79 coins × 12 months<br/>8.3M bars<br/>20%]
    Total --> Future[Future Reserve<br/>Remaining<br/>7.1M bars<br/>17%]
    
    Train --> CV[5-Fold Cross-Validation]
    
    CV --> Fold1[Fold 1: 224 train, 56 val]
    CV --> Fold2[Fold 2: 224 train, 56 val]
    CV --> Fold3[Fold 3: 224 train, 56 val]
    CV --> Fold4[Fold 4: 224 train, 56 val]
    CV --> Fold5[Fold 5: 224 train, 56 val]
    
    Fold1 --> Model[Model Training]
    Fold2 --> Model
    Fold3 --> Model
    Fold4 --> Model
    Fold5 --> Model
    
    Model --> ValTest[Validation Testing]
    Val --> ValTest
    
    ValTest --> Tune[Hyperparameter<br/>Tuning]
    
    Tune --> Final[Final Model]
    
    Final --> TestEval[Test Evaluation<br/>ONE RUN ONLY]
    Test --> TestEval
    
    style Train fill:#2d6a4f,stroke:#1b4332,color:#fff
    style Val fill:#e9c46a,stroke:#f4a261,color:#000
    style Test fill:#e76f51,stroke:#d62828,color:#fff
    style TestEval fill:#ff6b35,stroke:#d62828,color:#fff
```

---

## Diagram 10: Multi-Slot Position Management

```mermaid
sequenceDiagram
    participant Market
    participant SM as State Machine
    participant PM as Position Manager
    participant S1 as Slot 1
    participant S2 as Slot 2
    participant S3 as Slot 3
    participant S4 as Slot 4
    
    Market->>SM: Entry signal (Grade A)
    SM->>PM: Open position
    PM->>S1: Open Slot 1<br/>Entry: $100, SL: $95
    
    Note over S1: Active, monitoring
    
    Market->>SM: ADD signal
    SM->>PM: Check capacity
    PM->>PM: Slots: 1/4 used
    PM->>S2: Open Slot 2<br/>Entry: $108, SL: $103
    
    Note over S1,S2: Both active,<br/>independent SL/TP
    
    Market->>S1: Price drops to $95
    S1->>PM: SL hit, close Slot 1
    PM->>S1: Close position
    
    Note over S1: Closed (stopped out)
    Note over S2: Still active
    
    Market->>SM: RE-entry signal<br/>(within 10 bars)
    SM->>PM: Open RE-entry
    PM->>S3: Open Slot 3<br/>Entry: $97, SL: $92
    
    Note over S2,S3: Both active
    
    Market->>SM: Another ADD signal
    SM->>PM: Check capacity
    PM->>PM: Slots: 2/4 used
    PM->>S4: Open Slot 4<br/>Entry: $115, SL: $110
    
    Note over S2,S3,S4: 3 active slots<br/>Max: 4 total
    
    Market->>S2: TP hit at $120
    S2->>PM: Close Slot 2
    
    Market->>S3: AVWAP trail hits
    S3->>PM: Close Slot 3
    
    Market->>S4: Still running
    
    Note over S4: Only Slot 4 active<br/>Can open 3 more
```

---

**END OF DIAGRAMS**

All diagrams render in Obsidian with Mermaid plugin.  
Use for workflow visualization and handoff documentation.
