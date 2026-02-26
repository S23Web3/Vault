# BBW Simulator — UML Diagrams
**Date:** 2026-02-14
**Project:** `four-pillars-backtester`
**Related:** [[BBW-STATISTICS-RESEARCH]] | [[BBW-SIMULATOR-ARCHITECTURE]]

---

## 1. Class Diagram — Static Structure

```mermaid
classDiagram
    direction TB
    
    class BBWPCalculator {
        -DEFAULT_PARAMS: dict
        -basis_len: int
        -lookback: int
        -bbwp_ma_len: int
        -extreme_low: float
        -extreme_high: float
        -spectrum_low: float
        -spectrum_high: float
        +calculate_bbwp(df, params) DataFrame
        -_calc_bb_width(close, period) Series
        -_calc_percentile_rank(bbw, lookback) Series
        -_spectrum_color(bbwp_value) str
        -_detect_state(row) str
        -_assign_points(state) int
    }
    
    class BBWSequenceTracker {
        -COLOR_ORDER: dict
        +track_bbw_sequence(df) DataFrame
        -_sequence_direction(prev, curr) str
        -_is_skip(prev, curr) bool
        -_build_pattern_id(colors, n) str
        -_count_bars_since(series, target) Series
    }
    
    class ForwardReturnTagger {
        -windows: list~int~
        -proper_move_atr: float
        +tag_forward_returns(df, windows) DataFrame
        -_rolling_max_up(close, high, window) Series
        -_rolling_max_down(close, low, window) Series
        -_normalize_by_atr(values, atr) Series
    }
    
    class CoinClassifier {
        -n_clusters: int
        -scaler: StandardScaler
        -kmeans: KMeans
        +classify_coin_tiers(coin_stats_df) DataFrame
        -_compute_coin_features(df) dict
        -_find_optimal_k(features) int
        -_assign_tier_labels(df) DataFrame
    }
    
    class BBWSimulator {
        -LEVERAGE_GRID: list~int~
        -SIZE_GRID: list~float~
        -TARGET_GRID: list~int~
        -SL_GRID: list~float~
        -WINDOWS: list~int~
        -DIRECTIONS: list~str~
        -SCALE_SCENARIOS: list~tuple~
        +run_simulation(df, coin_meta) dict
        -_grid_search_lsg(state_bars, direction) DataFrame
        -_simulate_scaling(df, scenario) dict
        -_calc_trade_metrics(entries, params) dict
        -_compute_state_statistics(df) dict
        -_compute_transition_matrix(df) DataFrame
    }
    
    class MonteCarloValidator {
        -n_simulations: int
        -confidence_level: float
        -shuffle_method: str
        +validate_lsg(trades, optimal_params) dict
        -_shuffle_trades(trades) list
        -_bootstrap_equity_curves(trades, n) list
        -_compute_confidence_intervals(curves) dict
        -_detect_overfitting(real_vs_shuffled) bool
    }
    
    class BBWReportGenerator {
        -output_dir: Path
        +generate_report(all_results) None
        -_aggregate_stats(results) DataFrame
        -_optimal_lsg_table(results) DataFrame
        -_scaling_results(results) DataFrame
        -_per_tier_breakdown(results, tiers) dict
        -_param_sensitivity(results) DataFrame
        -_monte_carlo_summary(mc_results) DataFrame
    }
    
    class VINCEFeatureExtractor {
        -bbw_feature_list: list~str~
        +extract_bbw_features(df) DataFrame
        -_compute_derivatives(bbwp_series) DataFrame
        -_compute_rolling_stats(bbwp_series) DataFrame
        -_compute_markov_features(state_series) Series
        -_compute_mutual_info(features, target) Series
    }
    
    BBWPCalculator --> BBWSequenceTracker : feeds bbwp columns
    BBWSequenceTracker --> ForwardReturnTagger : feeds sequence columns
    ForwardReturnTagger --> BBWSimulator : feeds forward returns
    CoinClassifier --> BBWSimulator : feeds coin_meta
    BBWSimulator --> MonteCarloValidator : feeds trade results per state
    MonteCarloValidator --> BBWReportGenerator : feeds confidence intervals
    BBWSimulator --> BBWReportGenerator : feeds simulation results
    BBWSimulator --> VINCEFeatureExtractor : feeds enriched DataFrame
    BBWPCalculator ..> VINCEFeatureExtractor : reused in live pipeline
    BBWSequenceTracker ..> VINCEFeatureExtractor : reused in live pipeline
```

---

## 2. Sequence Diagram — Per-Coin Processing Pipeline

```mermaid
sequenceDiagram
    participant CLI as run_bbw_simulator.py
    participant CC as CoinClassifier
    participant L1 as BBWPCalculator
    participant L2 as BBWSequenceTracker
    participant L3 as ForwardReturnTagger
    participant L4 as BBWSimulator
    participant MC as MonteCarloValidator
    participant L5 as BBWReportGenerator
    participant FS as FileSystem

    CLI->>FS: Load all 399 coin parquets
    FS-->>CLI: List of DataFrames

    CLI->>CC: classify_coin_tiers(all_coin_stats)
    CC->>CC: compute 5 features per coin
    CC->>CC: StandardScaler + KMeans
    CC-->>CLI: coin_tiers.csv

    loop For each coin in selected set
        CLI->>FS: Load OHLCV parquet
        FS-->>CLI: df

        CLI->>L1: calculate_bbwp(df, params)
        L1-->>CLI: df + 10 bbwp_ columns

        CLI->>L2: track_bbw_sequence(df)
        L2-->>CLI: df + 8 bbw_seq_ columns

        CLI->>L3: tag_forward_returns(df, [10, 20])
        L3-->>CLI: df + 16 fwd_ columns

        CLI->>L4: run_simulation(df, coin_meta)
        L4->>L4: Group A-G stats
        L4->>L4: LSG grid search (10,752 combos)
        L4->>L4: Scaling sequences (6 scenarios)
        L4-->>CLI: results dict

        CLI->>MC: validate_lsg(trades, optimal_params)
        MC->>MC: 1000x trade shuffle
        MC->>MC: Bootstrap equity curves
        MC->>MC: Confidence intervals
        MC-->>CLI: mc_results dict

        CLI->>CLI: Append to all_results[]
    end

    CLI->>L5: generate_report(all_results)
    L5->>FS: Write CSVs + MC report
    L5-->>CLI: Report complete
```

---

## 3. Activity Diagram — Simulator Decision Logic

```mermaid
flowchart TD
    START([Enriched DataFrame]) --> GROUPBY[Group bars by bbwp_state]

    GROUPBY --> STATS[Distribution stats per state]

    STATS --> KSTEST{KS test vs NORMAL}
    KSTEST -->|p < 0.05| USEFUL[Discriminative state]
    KSTEST -->|p >= 0.05| FLAG[Low-value state]

    USEFUL --> GRID[LSG Grid Search]
    FLAG --> GRID

    GRID --> PARAMS[7 states × 2 dir × 4 SL ×\n4 lev × 4 size × 6 tgt × 2 win\n= 10,752 combos]

    PARAMS --> RACE{TP or SL first?}
    RACE -->|TP| WIN[+ P&L]
    RACE -->|SL| LOSS[- P&L]
    RACE -->|Neither| HOLD[Close Δ P&L]

    WIN --> METRICS[win_rate, expectancy,\nprofit_factor, max_dd]
    LOSS --> METRICS
    HOLD --> METRICS

    METRICS --> RANK[Top 5 by expectancy]
    RANK --> MC_VAL[Monte Carlo Validation]

    MC_VAL --> SHUFFLE[1000x trade order shuffle]
    SHUFFLE --> BOOTSTRAP[Bootstrap equity curves]
    BOOTSTRAP --> CI[95% confidence intervals]
    CI --> OVERFIT{Real > 95th pctl\nof shuffled?}
    OVERFIT -->|Yes| ROBUST[LSG params are robust]
    OVERFIT -->|No| SUSPECT[Possible overfit — flag]

    ROBUST --> SCALING[Scaling Sequence Sim]
    SUSPECT --> SCALING

    SCALING --> TRIGGER{Add trigger found\nin window?}
    TRIGGER -->|Yes| TWO_LEG[Two-leg P&L]
    TRIGGER -->|No| PARTIAL[Partial P&L]
    TWO_LEG --> VERDICT{triggered >= 30%\nAND edge >= 20%?}
    PARTIAL --> VERDICT
    VERDICT -->|Yes| USE[USE]
    VERDICT -->|No trigger| SKIP[SKIP]
    VERDICT -->|Edge but rare| MARGINAL[MARGINAL]

    USE --> OUTPUT([Final output])
    SKIP --> OUTPUT
    MARGINAL --> OUTPUT
```

---

## 4. Component Diagram — System Architecture

```mermaid
flowchart LR
    subgraph DATA["Data Layer"]
        CACHE[(data/cache/\n399 coins × 2 TF)]
        TIERS[(coin_tiers.csv)]
    end

    subgraph SIGNALS["Signal Layer — Permanent"]
        BBWP[signals/bbwp.py\nLayer 1: Calculator]
        SEQ[signals/bbw_sequence.py\nLayer 2: Sequence]
    end

    subgraph RESEARCH["Research Layer — Run Once"]
        FWD[research/bbw_forward_returns.py\nLayer 3]
        SIM[research/bbw_simulator.py\nLayer 4]
        MCV[research/bbw_monte_carlo.py\nLayer 4b]
        RPT[research/bbw_report.py\nLayer 5]
        COIN[research/coin_classifier.py\nPre-step]
    end

    subgraph OUTPUT["Output Layer"]
        AGG[(reports/bbw/aggregate/)]
        SCALE[(reports/bbw/scaling/)]
        TIER_RPT[(reports/bbw/per_tier/)]
        SENS[(reports/bbw/sensitivity/)]
        MC_RPT[(reports/bbw/monte_carlo/)]
    end

    subgraph LIVE["Live Trading Pipeline"]
        FP[signals/four_pillars.py]
        ML[ml/features.py]
        VINCE[VINCE ML Agent]
    end

    CACHE --> BBWP
    CACHE --> COIN
    COIN --> TIERS
    TIERS --> SIM
    BBWP --> SEQ
    SEQ --> FWD
    FWD --> SIM
    SIM --> MCV
    MCV --> RPT
    SIM --> RPT
    RPT --> AGG
    RPT --> SCALE
    RPT --> TIER_RPT
    RPT --> SENS
    RPT --> MC_RPT

    BBWP -.->|reused| FP
    SEQ -.->|reused| FP
    AGG -.->|BBW_LSG_MAP config| FP
    FP --> ML
    ML --> VINCE

    style SIGNALS fill:#1a5276,color:#fff
    style RESEARCH fill:#7d3c98,color:#fff
    style LIVE fill:#1e8449,color:#fff
```

---

## 5. State Diagram — BBWP State Machine

> **Reading guide:** Each box is a BBWP state. Arrows show transitions with conditions. States on the left (blue) favor long setups with higher leverage. States on the right (red) favor short or caution with reduced size.

```mermaid
flowchart LR
    subgraph BLUE_ZONE["🔵 LOW VOLATILITY — Squeeze Building"]
        BD["**BLUE_DOUBLE**\n─────────────\nBBWP ≤ 10\nPoints: 2\nLev: 20x | Size: 100%\nTarget: 5 ATR | SL: 2 ATR\nDirection: LONG bias"]
        BL["**BLUE**\n─────────────\nBBWP 10-25\nPoints: 1\nLev: 20x | Size: 75%\nTarget: 4 ATR | SL: 1.5 ATR\nDirection: LONG bias"]
    end

    subgraph NEUTRAL_ZONE["⚪ TRANSITION ZONE"]
        MCU["**MA_CROSS_UP**\n─────────────\nBBWP crosses above MA\nPoints: 0\nLev: 15x | Size: 50%\nTarget: 3 ATR | SL: 2 ATR\nTimeout: 10 bars"]
        NR["**NORMAL**\n─────────────\nBBWP 25-75\nPoints: 0\nLev: 10x | Size: 50%\nTarget: 2 ATR | SL: 1.5 ATR\nDirection: Neutral"]
        MCD["**MA_CROSS_DOWN**\n─────────────\nBBWP crosses below MA\nPoints: 0\nLev: 10x | Size: 25%\nTarget: 2 ATR | SL: 1 ATR\nTimeout: 10 bars"]
    end

    subgraph RED_ZONE["🔴 HIGH VOLATILITY — Expansion Active"]
        RD["**RED**\n─────────────\nBBWP 75-90\nPoints: 0\nLev: 10x | Size: 25%\nTarget: 2 ATR | SL: 1 ATR\nDirection: SHORT bias"]
        RDD["**RED_DOUBLE**\n─────────────\nBBWP ≥ 90\nPoints: 0 (caution)\nLev: minimal or skip\nTarget: 1 ATR | SL: 1 ATR\nReversal watch"]
    end

    BD -->|"BBWP > 10"| BL
    BL -->|"BBWP ≤ 10"| BD
    BL -->|"BBWP ≥ 25"| NR
    BL -->|"crosses above MA"| MCU
    BD -->|"BBWP ≥ 25"| NR

    NR -->|"BBWP < 25"| BL
    NR -->|"BBWP > 75"| RD
    NR -->|"crosses above MA"| MCU
    NR -->|"crosses below MA"| MCD

    MCU -->|"BBWP < 25"| BL
    MCU -->|"timeout 10 bars"| NR
    MCD -->|"BBWP > 75"| RD
    MCD -->|"timeout 10 bars"| NR

    RD -->|"BBWP ≥ 90"| RDD
    RD -->|"BBWP ≤ 75"| NR
    RD -->|"crosses below MA"| MCD
    RDD -->|"BBWP < 90"| RD
    RDD -->|"BBWP ≤ 75"| NR

    style BLUE_ZONE fill:#1a3a5c,color:#fff
    style NEUTRAL_ZONE fill:#2c2c2c,color:#fff
    style RED_ZONE fill:#5c1a1a,color:#fff
```

### State Transition Legend

| From → To | Condition | Meaning |
|-----------|-----------|---------|
| NORMAL → BLUE | BBWP drops below 25 | Volatility contracting, squeeze forming |
| BLUE → BLUE_DOUBLE | BBWP drops below 10 | Extreme squeeze, strongest entry signal |
| BLUE → MA_CROSS_UP | BBWP crosses above its MA | Volatility starting to expand from low |
| NORMAL → RED | BBWP rises above 75 | Volatility expanding, trend active |
| RED → RED_DOUBLE | BBWP rises above 90 | Extreme expansion, reversal watch |
| MA_CROSS_UP/DOWN → NORMAL | 10 bars timeout | Cross signal expired without follow-through |
| Any RED → NORMAL | BBWP drops below 75 | Expansion fading |
| Any BLUE → NORMAL | BBWP rises above 25 | Squeeze released |

---

## 6. Data Flow Diagram — Feature Engineering for VINCE

```mermaid
flowchart TB
    subgraph RAW["Raw OHLCV Input"]
        OHLCV["open | high | low | close | base_vol"]
    end

    subgraph L1["Layer 1: BBWP Calculator — signals/bbwp.py"]
        BB["BB basis = SMA(close, 13)\nBB width = 2×stdev / basis"]
        BBWP_CALC["BBWP = rolling_rank(BBW, 100) × 100\nBBWP_MA = SMA(BBWP, 5)"]
        STATE_DET["State detection: priority chain\nSpectrum color: 20/40/60/80 thresholds"]
    end

    subgraph L2["Layer 2: Sequence Tracker — signals/bbw_sequence.py"]
        SEQ_TRACK["Color transitions + direction\nSkip detection + pattern ID\nBars-in-state counters"]
    end

    subgraph DERIVED["Feature Engineering — computed per bar"]
        DERIV["ROC(1), ROC(5), acceleration\nMA distance, z-score\nrolling skew(20), kurtosis(20)\nMarkov transition probability"]
    end

    subgraph VINCE_VEC["VINCE Feature Vector — 17 features"]
        direction LR
        DIRECT["**Direct (4)**\nbbwp_value\nbbwp_points\nis_blue_bar\nis_red_bar"]
        CALC["**Derived (7)**\nroc, roc_5\nacceleration\nma_distance\nzscore\nskew_20\nkurt_20"]
        SEQ_F["**Sequence (5)**\nbars_in_state\ndirection_enc\nskip_detected\nfrom_blue_bars\nfrom_red_bars"]
        MARK["**Markov (1)**\nprob_to_blue"]
    end

    OHLCV --> L1
    L1 --> L2
    L1 --> DERIVED
    L2 --> DERIVED
    L1 --> VINCE_VEC
    L2 --> VINCE_VEC
    DERIVED --> VINCE_VEC

    style RAW fill:#333,color:#fff
    style L1 fill:#1a5276,color:#fff
    style L2 fill:#1a5276,color:#fff
    style DERIVED fill:#7d3c98,color:#fff
    style VINCE_VEC fill:#1e8449,color:#fff
```

### VINCE Feature Legend

| Category | Count | Features | Purpose |
|----------|-------|----------|---------|
| **Direct** | 4 | bbwp_value, bbwp_points, is_blue_bar, is_red_bar | Raw BBWP state at current bar |
| **Derived** | 7 | roc, roc_5, acceleration, ma_distance, zscore, skew_20, kurt_20 | Rate of change, momentum, extremes |
| **Sequence** | 5 | bars_in_state, direction_enc, skip_detected, from_blue_bars, from_red_bars | How BBW is evolving over time |
| **Markov** | 1 | prob_to_blue | Transition probability from current state |
| **Total** | **17** | | BBW-only features. Cross-pillar features (Ripster × BBW, AVWAP × BBW) computed in `ml/features.py` |

> **Note:** These 17 features are BBW's contribution to the VINCE feature matrix. Other pillars (Ripster, AVWAP, Quad Stoch) contribute their own features separately. Cross-pillar interaction features are computed at the ML layer, NOT in the BBW simulator.
