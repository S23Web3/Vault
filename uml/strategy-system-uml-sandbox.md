# Algorithmic Trading System - Architecture & Flow Diagrams
**Date:** 2026-02-16
**Purpose:** Generic system architecture reference (sandbox / shareable version)
**Format:** Mermaid diagrams (render in Obsidian)

---

## Diagram 1: Trade Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> SignalDetection: Entry signal fires

    SignalDetection --> GradeEvaluation: Signal confirmed
    SignalDetection --> Idle: Signal rejected

    GradeEvaluation --> PositionEntry: Signal grade approved
    GradeEvaluation --> Idle: Grade too weak

    PositionEntry --> InitialSL: Position opened

    InitialSL --> Monitoring: SL set at entry ± (risk_mult × volatility)

    Monitoring --> StoppedOut: Price hits SL
    Monitoring --> BERaise: Price moves +threshold × volatility
    Monitoring --> PartialExit: Trailing anchor checkpoint hit
    Monitoring --> FullExit: TP hit or manual close
    Monitoring --> AddSignal: Pyramid signal fires

    BERaise --> AnchorTrailing: SL moved to breakeven

    AnchorTrailing --> StoppedOut: Price hits trailing SL
    AnchorTrailing --> PartialExit: Anchor checkpoint hit
    AnchorTrailing --> FullExit: TP hit or manual close
    AnchorTrailing --> AddSignal: Pyramid signal fires

    AddSignal --> MultiSlot: New slot opened

    MultiSlot --> Monitoring: Each slot independent

    PartialExit --> AnchorTrailing: Remainder continues

    StoppedOut --> ReEntryWindow: Check re-entry conditions
    FullExit --> Idle: All slots closed

    ReEntryWindow --> PositionEntry: RE signal within N bars
    ReEntryWindow --> Idle: Window expired

    note right of InitialSL
        LONG: entry - (risk_mult × volatility)
        SHORT: entry + (risk_mult × volatility)
        Default risk_mult: configurable
    end note

    note right of BERaise
        Trigger: Price moves +threshold × volatility
        Action: Move SL to entry price
        Threshold: configurable
    end note

    note right of AnchorTrailing
        Ratchets every bar:
        LONG: SL = max(current, anchor - band - floor)
        SHORT: SL = min(current, anchor + band + floor)
        Never reverses direction
    end note

    note right of AddSignal
        Conditions:
        - Existing position active
        - New entry signal fires
        - Max slots not reached
        Inherits parent anchor state
    end note
```

---

## Diagram 2: Entry Grade Decision Tree

```mermaid
graph TD
    Start[Entry Signal Detected] --> Momentum{Momentum<br/>Indicator Aligned?}

    Momentum -->|Extreme zone reached| Trend{Trend Filter<br/>Position?}
    Momentum -->|Not aligned| C[Grade C<br/>Weak Entry]

    Trend -->|Price confirms trend direction| Anchor{Anchor<br/>Alignment?}
    Trend -->|Price against trend| C
    Trend -->|Price inside filter zone| B[Grade B<br/>Strong Entry]

    Anchor -->|Price supports direction| Volatility{Volatility State<br/>Favorable?}
    Anchor -->|Price against anchor| B
    Anchor -->|Anchor misaligned| B

    Volatility -->|Contraction state| A[Grade A<br/>Strongest Entry]
    Volatility -->|Neutral/Expansion| B
    Volatility -->|Unfavorable state| C

    A --> Execute{Execute?}
    B --> Execute
    C --> Execute

    Execute -->|Yes| LSG[Select Parameters<br/>by Volatility State]
    Execute -->|No| Reject[Reject Entry]

    LSG --> Open[Open Position]

    style A fill:#2d6a4f,stroke:#1b4332,color:#fff
    style B fill:#e9c46a,stroke:#f4a261,color:#000
    style C fill:#e76f51,stroke:#d62828,color:#fff

    note1[Trend Filter:<br/>Multi-EMA system<br/>Must be clean trend]
    note2[Grade A = All pillars aligned<br/>Grade B = 3/4 pillars<br/>Grade C = 2/4 pillars]
```

---

## Diagram 3: Stop Loss Lifecycle Flow

```mermaid
graph LR
    Entry[Position Entry] --> Initial[Initial SL]

    Initial --> |"Price moves<br/>+threshold × volatility"| BETrigger{BE Raise<br/>Triggered?}

    BETrigger -->|Yes| BE[Move SL to<br/>Entry Price]
    BETrigger -->|No| Monitor1[Monitor Price]

    Monitor1 --> |Price hits SL| Close1[Close Position]
    Monitor1 --> BETrigger

    BE --> Anchor[Anchor Trailing<br/>Activated]

    Anchor --> Recalc[Recalculate SL<br/>Every Bar]

    Recalc --> |"LONG:<br/>max(current_SL, anchor - band - floor)"| Update1[Update SL Up]
    Recalc --> |"SHORT:<br/>min(current_SL, anchor + band + floor)"| Update2[Update SL Down]

    Update1 --> Monitor2[Monitor Price]
    Update2 --> Monitor2

    Monitor2 --> |Price hits trailing SL| Close2[Close Position]
    Monitor2 --> Recalc

    style Initial fill:#e76f51,stroke:#d62828,color:#fff
    style BE fill:#e9c46a,stroke:#f4a261,color:#000
    style Anchor fill:#2d6a4f,stroke:#1b4332,color:#fff

    note1["Phase 1: Initial SL<br/>entry ± (risk_mult × volatility)<br/>Fixed distance"]
    note2["Phase 2: BE Raise<br/>Trigger: +threshold × volatility profit<br/>Action: Move to breakeven"]
    note3["Phase 3: Anchor Trail<br/>Dynamic ratcheting<br/>Never reverses"]
```

---

## Diagram 4: SL Movement Over Time

```mermaid
graph TD
    subgraph Phase 1: Initial SL
        P1[Entry: price<br/>Volatility measure: V<br/>risk_mult: configurable<br/>SL: entry - risk_mult × V]
    end

    subgraph Phase 2: BE Raise
        P2[Price reaches trigger level<br/>threshold × volatility<br/>SL moves to entry price]
    end

    subgraph Phase 3: Anchor Trailing
        P3A[Bar 1: Anchor value<br/>SL: max current, anchor-band-floor]
        P3B[Bar 2: Anchor rises<br/>SL: ratchets up with anchor]
        P3C[Bar 3: Anchor dips<br/>SL: stays at previous high<br/>Never reverses]
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

## Diagram 5: Pyramid (ADD) Signal Flow

```mermaid
sequenceDiagram
    participant Market
    participant Indicator as Momentum Indicator
    participant SM as State Machine
    participant PM as Position Manager
    participant Slot1 as Slot 1 (Original)
    participant Slot2 as Slot 2 (Pyramid)

    Market->>Indicator: Price movement
    Indicator->>SM: Entry signal fires
    SM->>PM: Grade A signal
    PM->>Slot1: Open position<br/>Entry at market, SL set

    Note over Slot1: Position active, monitoring

    Market->>Indicator: Pullback detected
    Indicator->>SM: Pyramid signal (lower grade ok)
    SM->>PM: ADD signal (original still active)

    PM->>Slot1: Confirm position active
    Slot1-->>PM: Active

    PM->>Slot2: Open pyramid slot<br/>Entry at pullback, SL set

    Note over Slot2: Inherits parent<br/>anchor state

    PM->>Slot1: Continue managing
    PM->>Slot2: Independent SL/TP

    Market->>Slot1: Price hits SL
    Slot1->>PM: Close Slot 1

    Note over Slot2: Slot 2 unaffected<br/>continues running

    Market->>Slot2: Price resumes trend
    Slot2->>PM: TP hit
    PM->>Slot2: Close Slot 2
```

---

## Diagram 6: System Flow — Page 1 (Built Components)

**Print:** A4 Landscape, 100% zoom

```mermaid
flowchart LR

    A1[(Price Cache\nN instruments\n✅ 2026-01-20)] --> A3
    A2[(Metadata\nMarket cap\n✅ 2026-01-25)] --> A3
    A3[Period Loader\nConcat + resample\n✅ 2026-01-20]

    A3 --> B1 & B2 & B3 & B4

    B1[Momentum\nIndicator\n✅ 2026-01-28]
    B2[Trend Filter\nEMA Clouds\n✅ 2026-01-28]
    B3[Anchor\nVol-weighted\n✅ 2026-01-28]
    B4[Vol State L1\nPercentile 0-100\n7 states\n✅ 2026-02-14]
    B4 --> B5[Vol Sequencer L2\nTransitions\n✅ 2026-02-14]
    B5 --> B6[Fwd Returns L3\nReturn by state\n✅ 2026-02-14]

    B1 & B2 & B3 & B4 --> SM

    SM[State Machine\nA B C D grades\n✅ 2026-01-30]
    SM --> BT[Backtester\nMulti-slot\n✅ 2026-02-05]
    BT --> PM[Position Mgr\nSL → BE → Trail\n✅ 2026-02-05]
    BT --> EM[Exit Mgr\nSL · TP · Scale\n⚠️ bug pending]
    PM & EM --> CM[Commission\nTaker + Rebate\n✅ 2026-02-05]
    BT --> DASH[Dashboard\nSingle · Sweep\nPortfolio · PDF\n✅ 2026-02-16]

    style A1 fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style A2 fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style A3 fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style B1 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B2 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B3 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B4 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B5 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B6 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style SM fill:#5a3a1a,color:#fff,stroke:#3a2010
    style BT fill:#5a3a1a,color:#fff,stroke:#3a2010
    style PM fill:#5a3a1a,color:#fff,stroke:#3a2010
    style EM fill:#8a2a0a,color:#fff,stroke:#6a1a00
    style CM fill:#5a3a1a,color:#fff,stroke:#3a2010
    style DASH fill:#1a5a5a,color:#fff,stroke:#0d4a4a
```

---

## Diagram 6b: System Flow — Page 2a (Analysis + ML Training)

```mermaid
flowchart LR
    BT2[Backtester\noutput\n✅ 2026-02-05]
    BT2 --> VA4[Results\nAnalyzer L4\n✅ 2026-02-15]
    VA4 --> VA4b[Monte Carlo\nL4b · CI\n✅ 2026-02-15]
    VA4b --> VA5[Feature Gen\nL5 · CSV\n⚡ 2026-02-20]
    VA5 --> SPLIT[Data Split\n53/10/20%\n⏳ 2026-02-20]
    SPLIT --> M1[Feature\nSelect\n⏳ 2026-02-24]
    M1 --> M2[Feature\nEng\n⏳ 2026-02-24]
    M2 --> M3[Param\nOptimizer\n⚡ 2026-02-28]

    style BT2  fill:#5a3a1a,color:#fff,stroke:#3a2010
    style VA4  fill:#3a2d5a,color:#fff,stroke:#2a1d4a
    style VA4b fill:#3a2d5a,color:#fff,stroke:#2a1d4a
    style VA5  fill:#c44a00,color:#fff,stroke:#a03800
    style SPLIT fill:#6b5a00,color:#fff,stroke:#504400
    style M1   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style M2   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style M3   fill:#c44a00,color:#fff,stroke:#a03800
```

## Diagram 6c: System Flow — Page 2b (Validation + Live)

```mermaid
flowchart LR
    M3[Param\nOptimizer\n⚡ 2026-02-28]
    M3 --> M4[Trade\nFilter\n⏳ 2026-03-03]
    M4 --> M5[Position\nSizer\n⏳ 2026-03-03]
    M5 --> VAL[Validation\n10% held-out\n⏳ 2026-03-07]
    VAL --> TEST[Final Test\nFROZEN\n⏳ 2026-03-10]
    TEST --> INF[Inference\nSub-50ms\n⏳ 2026-03-14]
    INF --> WH[Webhook\n⏳ 2026-03-14]
    WH --> EXC[Exchange\nAPI\n⏳ 2026-03-17]
    EXC --> RET[Retrain\nDaily\n⏳ 2026-03-17]
    RET -->|loop| INF
    M3 -.->|live model| INF

    style M3   fill:#c44a00,color:#fff,stroke:#a03800
    style M4   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style M5   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style VAL  fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style TEST fill:#7a0a0a,color:#fff,stroke:#5a0000
    style INF  fill:#1a3a7a,color:#fff,stroke:#0d2a5a
    style WH   fill:#1a3a7a,color:#fff,stroke:#0d2a5a
    style EXC  fill:#1a3a7a,color:#fff,stroke:#0d2a5a
    style RET  fill:#1a5a27,color:#fff,stroke:#0d4a18
```

| ✅ Built | ⚡ Bottleneck | ⚠️ Bug pending | ⏳ Pending |
|---------|-------------|--------------|---------|

**Critical path:** Feature Gen ⚡ → Data Split → Param Optimizer ⚡ → Validation → Final Test → Live

---

## Diagram 7: Critical Path Timeline

```mermaid
gantt
    title Algorithmic Trading System - Critical Path
    dateFormat YYYY-MM-DD
    section Analysis Pipeline
    Volatility Layer completion      :active, va5, 2026-02-16, 4d
    Data split generation            :split, after va5, 1d

    section Data Preparation
    Restore exit logic               :data1, after va5, 2d
    Full instrument sweep            :data2, after data1, 1d
    Feature CSV exports              :data3, after split, 1d

    section ML Agent
    Parameter optimizer build        :ml1, after data3, 5d
    Model training                   :ml2, after ml1, 2d
    Cross-validation                 :ml3, after ml2, 2d
    Held-out validation              :ml4, after ml3, 2d

    section Testing
    Hyperparameter tuning            :test1, after ml4, 3d
    Final test evaluation            :milestone, test2, after test1, 1d

    section Production
    Webhook integration              :prod1, after test2, 3d
    Adaptive exit logic              :prod2, after test2, 2d
    Live deployment                  :milestone, prod3, after prod1, 1d
    Daily retraining schedule        :prod4, after prod3, 2d
```

---

## Diagram 8: Commission & Rebate Flow

```mermaid
graph LR
    Entry[Entry Order<br/>Size × Leverage × Capital] --> EntryFee[Entry Fee<br/>Notional × rate]

    Exit[Exit Order<br/>Same Notional] --> ExitFee[Exit Fee<br/>Notional × rate]

    EntryFee --> RT[Round-Trip<br/>Commission]
    ExitFee --> RT

    RT --> Net[Net PnL<br/>Gross - RT]

    Entry --> Volume[Daily Volume<br/>Sum all trades]
    Exit --> Volume

    Volume --> Rebate[Rebate Calculation<br/>Volume × rebate_rate]

    Rebate --> Settlement[Settlement<br/>Daily cutoff]

    Settlement --> Credit[Credit to Account]

    style RT fill:#e76f51,stroke:#d62828,color:#fff
    style Rebate fill:#2d6a4f,stroke:#1b4332,color:#fff

    note1["Round-trip cost:<br/>notional × rate × 2 sides"]
    note2["Daily rebate:<br/>volume × rebate_rate<br/>Settled at daily cutoff"]
```

---

## Diagram 9: Data Split Strategy

```mermaid
graph TD
    subgraph Total Dataset
        Total[N instruments × M months<br/>Total bars available]
    end

    Total --> Train[Training Set<br/>~53% instruments<br/>8 months of data]
    Total --> Val[Validation Set<br/>~10% instruments<br/>Full date range]
    Total --> Test[Test Set FROZEN<br/>~20% instruments<br/>Full date range]
    Total --> Future[Future Reserve<br/>~17% buffer]

    Train --> CV[K-Fold Cross-Validation]

    CV --> Fold1[Fold 1: train subset / val subset]
    CV --> Fold2[Fold 2: different split]
    CV --> Fold3[Fold 3: different split]
    CV --> Fold4[Fold 4: different split]
    CV --> Fold5[Fold 5: different split]

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
    PM->>S1: Open Slot 1<br/>Entry at market, SL set

    Note over S1: Active, monitoring

    Market->>SM: Pyramid signal
    SM->>PM: Check capacity
    PM->>PM: Slots: 1/N used
    PM->>S2: Open Slot 2<br/>Entry at pullback, SL set

    Note over S1,S2: Both active,<br/>independent SL/TP

    Market->>S1: Price hits SL
    S1->>PM: Close Slot 1
    PM->>S1: Position closed

    Note over S1: Closed (stopped out)
    Note over S2: Still active

    Market->>SM: Re-entry signal<br/>(within lookback window)
    SM->>PM: Open re-entry
    PM->>S3: Open Slot 3<br/>Entry on re-entry, SL set

    Note over S2,S3: Both active

    Market->>SM: Another pyramid signal
    SM->>PM: Check capacity
    PM->>PM: Slots: 2/N used
    PM->>S4: Open Slot 4<br/>Entry at next pullback

    Note over S2,S3,S4: 3 active slots<br/>Max: N total

    Market->>S2: TP hit
    S2->>PM: Close Slot 2

    Market->>S3: Trailing anchor exits
    S3->>PM: Close Slot 3

    Market->>S4: Still running

    Note over S4: Only Slot 4 active<br/>Can open more slots
```

---

## Appendix: Terminology Mapping

| Sandbox Term | System-Specific Term |
|---|---|
| Momentum Indicator | Quad Rotation Stochastic (9/14/40/60 Raw K) |
| Trend Filter | Ripster EMA Cloud 3 (EMA 34/50) |
| Anchor Indicator | Anchored VWAP (AVWAP) |
| Volatility State | BBWP State (7 states) |
| Volatility Layer | BBW Pipeline (5 layers) |
| Parameter Optimizer | LSG Optimizer (Leverage/Size/Grid) |
| ML Agent | VINCE |
| Trade Filter | Meta-Labeling module |
| Position Sizer | Kelly Criterion bet sizing |
| Anchor Trailing | AVWAP Ratchet SL |
| Grade A/B/C/D | Four Pillars signal grades |
| risk_mult | sl_mult (ATR multiplier) |
| volatility measure | ATR14 |
| threshold | be_trigger_atr |
| Daily cutoff | 17:00 UTC rebate settlement |

---

**END OF DIAGRAMS**

Sandbox version -- all proprietary terminology replaced with generic equivalents.
Terminology mapping in appendix for internal reference.
