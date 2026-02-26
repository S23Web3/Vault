graph TB
    subgraph "DATA LAYERS (Unchanged)"
        L1[Layer 1: BBWP Calculator<br/>signals/bbwp.py<br/>Input: OHLC<br/>Output: BBWP percentile]
        L2[Layer 2: BBW Sequence<br/>signals/bbw_sequence.py<br/>Input: BBWP values<br/>Output: State sequence]
        L3[Layer 3: Forward Returns<br/>research/bbw_forward_returns.py<br/>Input: States + prices<br/>Output: Forward return analysis]
    end

    subgraph "BACKTESTER (Existing)"
        BT[Backtester v385<br/>engine/backtester_v385.py<br/>Four Pillars Strategy<br/>Stochastics + Ripster + AVWAP + BBW<br/>Output: Trade results]
        DASH[Dashboard v3<br/>scripts/dashboard_v3.py<br/>Executes sweeps<br/>400+ coins, year of data<br/>93% success rate]
    end

    subgraph "BBW ANALYSIS LAYERS (V2 Rebuild)"
        L4[Layer 4: BBW Analyzer V2<br/>research/bbw_analyzer_v2.py<br/>BACKTESTER RESULTS ANALYSIS<br/>Enrich trades with BBW state<br/>Group by state × direction × LSG<br/>Calculate BE+fees rates]
        L4b[Layer 4b: Monte Carlo V2<br/>research/bbw_monte_carlo_v2.py<br/>DIRECTIONAL VALIDATION<br/>Bootstrap + Permutation per state × direction<br/>Verdict: ROBUST/FRAGILE/COMMISSION_KILL]
        L5[Layer 5: Reporting V2<br/>research/bbw_report_v2.py<br/>VINCE FEATURE GENERATION<br/>Directional bias aggregation<br/>BE+fees success tables<br/>LSG effectiveness reports]
    end

    subgraph "VINCE ML (Separate Component - Future)"
        VINCE[VINCE Engine<br/>ml/vince_model.py<br/>Learns optimal LSG from:<br/>BBW + Ripster + AVWAP + Stochastics<br/>Real-time LSG optimization]
    end

    L1 --> L2
    L2 --> L3
    
    DASH -->|Executes| BT
    BT -->|Trade results<br/>direction already set| L4
    L2 -->|BBW states<br/>for enrichment| L4

    L4 -->|Per-trade PnL<br/>state × direction × LSG| L4b
    L4b -->|Verdicts<br/>Confidence intervals<br/>Overfit flags| L5
    L5 -->|VINCE features<br/>Directional bias<br/>BE+fees metrics| VINCE

    VINCE -->|Optimal LSG<br/>per market regime| BT

    classDef unchanged fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef rebuild fill:#FFB6C1,stroke:#DC143C,stroke-width:3px
    classDef existing fill:#F0E68C,stroke:#DAA520,stroke-width:2px
    classDef future fill:#DDA0DD,stroke:#9370DB,stroke-width:2px

    class L1,L2,L3 unchanged
    class L4,L4b,L5 rebuild
    class BT,DASH existing
    class VINCE future

    style L4 fill:#FFB6C1,stroke:#DC143C,stroke-width:4px,color:#000
    style L4b fill:#FFB6C1,stroke:#DC143C,stroke-width:4px,color:#000
    style L5 fill:#FFB6C1,stroke:#DC143C,stroke-width:4px,color:#000

    %% Annotations
    note1[V1: Simulated trades<br/>V2: Analyzes backtester results]
    note2[V1: Win rate metric<br/>V2: BE+fees rate metric]
    note3[V1: BBW determines direction<br/>V2: Direction from Four Pillars strategy]
    note4[NO LAYER 6<br/>VINCE is separate ML component]

    L4 -.-> note1
    L4 -.-> note2
    BT -.-> note3
    L5 -.-> note4
