# Algorithmic Trading System — System Flow
**Version:** 2026-03-05 | **Print:** A4 Landscape, 100% zoom

---

## Page 1 — Built Components (Backtester)

```mermaid
flowchart LR

    A1[(Price Cache\nN instruments\n✅ 2026-01-20)] --> A3
    A2[(Metadata\nMarket cap\n✅ 2026-01-25)] --> A3
    A3[Period Loader\nConcat + resample\n✅ 2026-01-20]

    A3 --> B1 & B2 & B3 & B4

    B1[Momentum\nOscillator\n✅ 2026-01-28]
    B2[Trend Filter\nEMA Clouds\n✅ 2026-01-28]
    B3[Anchor VWAP\nVol-weighted\n✅ 2026-01-28]
    B4[Vol State L1\nPercentile 0-100\n7 states\n✅ 2026-02-14]
    B4 --> B5[Vol Sequencer L2\nTransitions\n✅ 2026-02-14]
    B5 --> B6[Fwd Returns L3\nReturn by state\n✅ 2026-02-14]

    B1 & B2 & B3 & B4 --> SM

    SM["State Machine\nQuad / Rotation signals\nC signal REMOVED\n✅ v386 2026-02-28"]
    SM --> BT[Backtester v385\nMulti-slot\n✅ 2026-02-05]
    BT --> PM[Position Mgr\nSL → BE → AVWAP Trail\n✅ 2026-02-05]
    BT --> EM[Exit Mgr\n⚠️ Likely dead code\nconfirm before B3]
    PM & EM --> CM[Commission\nTaker + Rebate\n✅ 2026-02-05]
    BT --> DASH[Dashboard v3.9.4\nSingle · Sweep · PDF\nCUDA GPU Sweep\n✅ 2026-03-03]

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

## Page 1b — BingX Live Bot (Separate System)

```mermaid
flowchart LR

    CFG[config.yaml\n47 coins, 10x\n$50 margin\n✅ LIVE]
    SIG_ENG[Signal Engine\nfour_pillars_v386\nQuad + Rotation\n✅ 2026-02-28]
    BOT[main.py\nv384 patched\n✅ 2026-03-04]
    MON[Position Monitor\nSL · BE · TTP Trail\nreduceOnly FIXED\n✅ 2026-03-04]
    TTP[TTP Engine\nActivation + Trail\nHybrid arch\n✅ 2026-03-03]
    STATE[State Manager\nstate.json + trades.csv\nTTP columns added\n✅ 2026-03-04]
    DASH_BX[Dashboard v1.5\nClose Market FIXED\nSession equity curve\nTTP stats panel\n✅ 2026-03-04]
    BINGX[(BingX Exchange\nPerp futures\nHedge mode)]
    TG[Telegram\nAlerts\n✅ 2026-02-27]

    CFG --> BOT
    SIG_ENG --> BOT
    BOT --> MON
    MON --> TTP
    TTP --> MON
    MON --> STATE
    STATE --> DASH_BX
    BOT --> BINGX
    MON --> BINGX
    MON --> TG

    BETA[Beta Bot\nmain_beta.py\n44 coins, 20x, $5\n⏳ NOT STARTED\nOverlap cleanup needed]

    style CFG fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style SIG_ENG fill:#2d4a27,color:#fff,stroke:#1a3a18
    style BOT fill:#2d6a4f,color:#fff,stroke:#1b4332
    style MON fill:#2d6a4f,color:#fff,stroke:#1b4332
    style TTP fill:#2d6a4f,color:#fff,stroke:#1b4332
    style STATE fill:#2d6a4f,color:#fff,stroke:#1b4332
    style DASH_BX fill:#1a5a5a,color:#fff,stroke:#0d4a4a
    style BINGX fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style TG fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style BETA fill:#6b5a00,color:#fff,stroke:#504400
```

---

## Page 2a — Analysis + ML Training

```mermaid
flowchart LR
    BT2[Backtester v385\noutput\n✅ 2026-02-05]
    BT2 --> VA4[Results\nAnalyzer L4\n✅ 2026-02-15]
    VA4 --> VA4b[Monte Carlo\nL4b · CI\n✅ 2026-02-15]
    VA4b --> VA5[Feature Gen\nL5 · CSV\n⚡ 2026-02-20]
    VA5 --> SPLIT[Data Split\n53/10/20%\n⏳ Pending Phase 0]
    SPLIT --> M1[Feature\nSelect\n⏳ Pending B1]
    M1 --> M2[Feature\nEng\n⏳ Pending B1]
    M2 --> M3[Param\nOptimizer\n⏳ Pending B1]

    style BT2  fill:#5a3a1a,color:#fff,stroke:#3a2010
    style VA4  fill:#3a2d5a,color:#fff,stroke:#2a1d4a
    style VA4b fill:#3a2d5a,color:#fff,stroke:#2a1d4a
    style VA5  fill:#c44a00,color:#fff,stroke:#a03800
    style SPLIT fill:#6b5a00,color:#fff,stroke:#504400
    style M1   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style M2   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style M3   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
```

## Page 2b — Validation + Live

```mermaid
flowchart LR
    M3[Param\nOptimizer\n⏳ Pending B1]
    M3 --> M4[Trade\nFilter\n⏳ Pending B3]
    M4 --> M5[Position\nSizer\n⏳ Pending B3]
    M5 --> VAL[Validation\n10% held-out\n⏳ Pending B3]
    VAL --> TEST[Final Test\nFROZEN\n⏳ Pending VAL]
    TEST --> INF[Inference\nSub-50ms\n⏳ Pending TEST]
    INF --> WH[Webhook\n⏳ Pending INF]
    WH --> EXC[Exchange\nAPI\n⏳ Pending WH]
    EXC --> RET[Retrain\nDaily\n⏳ Pending EXC]
    RET -->|loop| INF
    M3 -.->|live model| INF

    style M3   fill:#5a1a3a,color:#fff,stroke:#3a0a2a
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

## Page 3 — Vince ML Build Chain

```mermaid
flowchart TD

    P0["Phase 0: Strategy Alignment\n6 open questions\n⚠️ BLOCKER — answers needed"]

    B1["B1: FourPillarsPlugin\nstrategies/four_pillars.py\nWraps v386 signals + Backtester385\n⏳ Blocked on Phase 0"]
    B2["B2: vince/ API + Types\nvince/types.py · api.py · audit.py\n8 dataclasses · 8 API stubs\n✅ DONE 2026-03-02"]
    B3["B3: Enricher\nvince/enricher.py\nSnapshot indicators at entry/MFE/exit\n⏳ Blocked on B1"]
    B4["B4: PnL Reversal Panel\nvince/pages/pnl_reversal.py\nLSG · MFE histogram · TP sweep\n⏳ Blocked on B3"]
    B5["B5: Query Engine\nvince/query_engine.py\nConstellation filter · permutation test\n⏳ Blocked on B3"]
    B6["B6: Dash Shell\nvince/app.py + layout.py\n8-panel multi-page app\n⏳ Blocked on B1-B5"]

    P0 --> B1
    B2 --> B3
    B1 --> B3
    B3 --> B4
    B3 --> B5
    B4 & B5 --> B6

    style P0 fill:#8a2a0a,color:#fff,stroke:#6a1a00
    style B1 fill:#6b5a00,color:#fff,stroke:#504400
    style B2 fill:#2d6a4f,color:#fff,stroke:#1b4332
    style B3 fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style B4 fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style B5 fill:#5a1a3a,color:#fff,stroke:#3a0a2a
    style B6 fill:#1a3a7a,color:#fff,stroke:#0d2a5a
```

---

## Page 4 — Signal Architecture (Post-Rename)

```mermaid
flowchart TD

    OHLCV[OHLCV DataFrame] --> IND

    subgraph IND [Indicator Layer]
        K1[k_9 Raw K\n9-period stoch]
        K2[k_14 Raw K\n14-period stoch]
        K3[k_40 Raw K\n40-period stoch]
        K4[k_60 Raw K\n60-period stoch]
        CLOUD[EMA Cloud 3\ncloud3_allows_long/short]
        ATR[ATR 14]
        AVWAP[Anchored VWAP]
    end

    IND --> SM

    subgraph SM [State Machine v386]
        QUAD["QUAD signal\n4/4 stochs aligned\nCloud 3 bypassed\n= old Grade A"]
        ROT["ROTATION signal\n3/4 stochs aligned\nCloud 3 gated\n= old Grade B"]
        NOTE["❌ C signal REMOVED\n2/4 stochs was wrong by design\nNot a state machine signal"]
    end

    SM --> ENG

    subgraph ENG [Engine Layer — ADD logic]
        FRESH[Fresh entry → QUAD or ROTATION]
        ADD["ADD label applied when:\n• Quad or Rotation fires\n• Same-direction position open\n• Capacity + cooldown met\n= old Grade C (now engine label)"]
    end

    ENG --> POS[Position opened\nwith grade label]

    style QUAD fill:#2d6a4f,color:#fff,stroke:#1b4332
    style ROT fill:#e9c46a,color:#000,stroke:#f4a261
    style NOTE fill:#8a2a0a,color:#fff,stroke:#6a1a00
    style ADD fill:#1a3a7a,color:#fff,stroke:#0d2a5a
    style FRESH fill:#2d4a27,color:#fff,stroke:#1a3a18
```

---

| ✅ Built + Live | ⚡ Bottleneck | ⚠️ Bug / confirm needed | ⏳ Pending | 🔴 Blocked |
|---|---|---|---|---|

**Critical path (Vince):** Phase 0 answers → B1 → B3 → B4/B5 → B6
**Critical path (Bot):** Start beta bot (remove overlaps) → TP sweep at 0.5-0.7x ATR → v385 signal upgrade decision

---

## Change Log

| Date | Change |
|---|---|
| 2026-02-16 | Initial creation |
| 2026-03-05 | Signal rename: A→Quad, B→Rotation, C→ADD (engine label). C signal removed from state machine. BingX bot live system added (Page 1b). Vince build chain added (Page 3). Signal architecture post-rename added (Page 4). Dashboard updated to v3.9.4 CUDA. ExitManager flagged as likely dead code. Phase 0 blocker surfaced on Vince chain. |
