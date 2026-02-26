# Algorithmic Trading System — System Flow
**Version:** 2026-02-16 | **Print:** A4 Landscape, 100% zoom

---

## Page 1 — Built Components

```mermaid
flowchart LR

    A1[(Price Cache\nN instruments\n✅ 2026-01-20)] --> A3
    A2[(Metadata\nMarket cap\n✅ 2026-01-25)] --> A3
    A3[Period Loader\nConcat + resample\n✅ 2026-01-20]

    A3 --> B1 & B2 & B3 & B4

    B1[Momentum\nOscillator\n✅ 2026-01-28]
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

## Page 2a — Analysis + ML Training

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

## Page 2b — Validation + Live

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

---

| ✅ Built | ⚡ Bottleneck | ⚠️ Bug pending | ⏳ Pending |
|---------|-------------|--------------|---------|

**Critical path:** L5 Feature Gen ⚡ → Data Split → Param Optimizer ⚡ → Validation → Final Test → Live
