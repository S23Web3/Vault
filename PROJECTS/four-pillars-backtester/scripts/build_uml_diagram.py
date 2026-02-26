"""
Build script: generates Mermaid UML diagrams for Four Pillars v3.9.1.
Output: results/uml/four-pillars-architecture.md (Obsidian-readable).
Run: python scripts/build_uml_diagram.py
"""
import os
import sys
import py_compile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results" / "uml"


def build_class_diagram():
    """Return Mermaid class diagram string."""
    return """```mermaid
classDiagram
    direction TB

    %% ===== DATA LAYER =====
    class BybitFetcher {
        +fetch_klines(symbol, interval, start, end) DataFrame
        +load_cached(symbol, interval) DataFrame
        -_paginate_backward(symbol, interval, end_ms)
        -cache_dir : Path
    }

    class OHLCVNormalizer {
        +normalize(df, exchange) DataFrame
        +detect_format(df) str
        -EXCHANGE_FORMATS : dict
    }

    class ParquetCache {
        <<data store>>
        +path : data/cache/
        +format : SYMBOL_TFm.parquet
        +columns : datetime, open, high, low, close, volume
        +size : ~6.2 GB / 399 coins
    }

    %% ===== SIGNAL LAYER =====
    class compute_signals_v383 {
        <<function>>
        +compute_signals_v383(df, params) DataFrame
        -calls compute_all_stochastics()
        -calls compute_clouds()
        -calls FourPillarsStateMachine383
    }

    class FourPillarsStateMachine383 {
        +process_bar(bar_data) dict
        -state : str
        -direction : str
        -Output: long_a/b/c/d, short_a/b/c/d
        -Output: add_long/short, reentry_long/short
    }

    class Stochastics {
        <<module: signals/stochastics>>
        +compute_all_stochastics(df, params) DataFrame
        -stoch_9_3 : entry
        -stoch_14_3 : confirm
        -stoch_40_3 : divergence
        -stoch_60_10 : macro
    }

    class Clouds {
        <<module: signals/clouds>>
        +compute_clouds(df, params) DataFrame
        -cloud2 : 5/12 EMA
        -cloud3 : 34/50 EMA
        -cloud4 : 72/89 EMA
        -cloud5 : 180/200 EMA
    }

    %% ===== ENGINE LAYER =====
    class Backtester384 {
        +run(df) dict
        -_open_slot(slots, idx, ...) void
        -_find_empty(slots) int
        -_compute_metrics(trades, eq) dict
        -_trades_to_df(trades) DataFrame
        -slots : PositionSlot384[max_positions]
        -comm : CommissionModel
        -initial_equity : float = 10000
        -max_positions : int = 4
        -notional : float
        -sl_mult : float = 2.0
        -tp_mult : float?
        -max_scaleouts : int = 2
    }

    class PositionSlot384 {
        +check_exit(high, low) str?
        +update_bar(bar, high, low, close, atr, hlc3, vol) void
        +check_scale_out(bar, close) bool
        +do_scale_out(bar, close, comm) tuple
        +close_at(price, bar, reason, comm) Trade384
        -direction : str
        -grade : str
        -entry_bar : int
        -entry_price : float
        -notional : float
        -sl : float
        -tp : float?
        -avwap : AVWAPTracker
        -mfe : float
        -mae : float
        -saw_green : bool
        -be_raised : bool
        -scale_count : int
    }

    class Trade384 {
        <<dataclass>>
        +direction : str
        +grade : str
        +entry_bar : int
        +exit_bar : int
        +entry_price : float
        +exit_price : float
        +sl_price : float
        +tp_price : float?
        +pnl : float
        +commission : float
        +mfe : float
        +mae : float
        +exit_reason : str
        +saw_green : bool
        +be_raised : bool
        +scale_idx : int = 0
        +entry_atr : float
    }

    class CommissionModel {
        +charge(maker=False) float
        +charge_custom(notional, maker=False) float
        +check_settlement(bar_dt) float
        +net_commission : float
        -commission_rate : float = 0.0008
        -maker_rate : float = 0.0002
        -rebate_pct : float = 0.70
        -settlement_hour : int = 17
        -total_commission : float
        -total_rebate : float
        -total_volume : float
        -daily_commission : float
    }

    class AVWAPTracker {
        +update(hlc3, volume) void
        +value : float
        -cum_pv : float
        -cum_vol : float
    }

    %% ===== PORTFOLIO LAYER =====
    class align_portfolio_equity {
        <<function in dashboard>>
        +align_portfolio_equity(coin_results, margin, max_pos) dict
        -Output: master_dt, portfolio_eq, per_coin_eq
        -Output: capital_allocated, portfolio_dd_pct
        -Output: best_moment, worst_moment
    }

    class CapitalModelV2 {
        <<module: utils/capital_model_v2>>
        +apply_capital_constraints(coin_results, pf, capital, margin, ...) dict
        +format_capital_summary(efficiency) list
        -_group_trades_into_positions(coin_results, master_dt) list
        -_rebuild_metrics_from_df(tdf, eq, metrics, notional) dict
        -_map_bar_to_master(bar, coin_dt, master_dt) int
        -_grade_sort_key(grade) int
        -GRADE_PRIORITY : dict
    }

    class PoolSimulation {
        <<internal to CapitalModelV2>>
        -balance : float
        -margin_used : float
        -active : list
        -daily_comm_accumulated : float
        -settlement at 17:00 UTC
        +accept_position() void
        +reject_position() void
        +settle_rebate() void
    }

    %% ===== ANALYSIS LAYER =====
    class CoinAnalysis {
        <<module: utils/coin_analysis>>
        +compute_extended_metrics(tdf, bar_count) dict
        +compute_grade_distribution(tdf) dict
        +compute_exit_distribution(tdf) dict
        +compute_monthly_pnl(tdf, dt_idx) DataFrame
        +compute_loser_detail(tdf) DataFrame
        +compute_commission_breakdown(tdf) dict
        +compute_daily_volume_stats(tdf, dt_idx, notional) dict
    }

    %% ===== OUTPUT LAYER =====
    class DashboardV391 {
        <<Streamlit app: scripts/dashboard_v391.py>>
        +Settings Tab : sidebar config
        +Single Coin Tab : one backtest
        +Sweep Tab : multi-param grid
        +Sweep Detail Tab : drill into sweep
        +Portfolio Tab : multi-coin analysis
        -Mode 1: Per-Coin Independent (N x $10k)
        -Mode 2: Shared Pool ($X deposit)
    }

    class PDFExporterV2 {
        <<module: utils/pdf_exporter_v2>>
        +check_dependencies() tuple
        +generate_portfolio_pdf(pf, coins, name, capital, cap_result) str
        -_fig_to_image(fig, width, dpi) Image
        -_make_equity_chart(dt, eq, per_coin, title) Figure
        -_make_capital_chart(dt, allocated, total) Figure
        -_make_coin_equity_chart(dt, eq, symbol) Figure
    }

    class PortfolioManager {
        <<module: utils/portfolio_manager>>
        +save_portfolio(name, coins, method, notes, hash) str
        +load_portfolio(filename) dict
        +list_portfolios() list
        +delete_portfolio(filename) bool
        +rename_portfolio(old, new_name) str
        -PORTFOLIO_DIR : Path
    }

    class CSVExport {
        <<PATCH 14 in dashboard>>
        +columns: symbol, entry_datetime, exit_datetime
        +columns: direction, grade, entry/exit_price
        +columns: pnl, commission, net_pnl
        +columns: mfe, mae, exit_reason, saw_green
    }

    %% ===== RELATIONSHIPS =====
    BybitFetcher --> ParquetCache : writes/reads
    OHLCVNormalizer --> ParquetCache : normalizes into
    ParquetCache --> DashboardV391 : loads from

    DashboardV391 --> compute_signals_v383 : calls
    compute_signals_v383 --> Stochastics : uses
    compute_signals_v383 --> Clouds : uses
    compute_signals_v383 --> FourPillarsStateMachine383 : uses

    DashboardV391 --> Backtester384 : runs backtest
    Backtester384 --> CommissionModel : owns
    Backtester384 --> PositionSlot384 : manages 1..4
    PositionSlot384 --> AVWAPTracker : tracks
    PositionSlot384 --> Trade384 : produces
    Backtester384 --> Trade384 : collects

    DashboardV391 --> align_portfolio_equity : aggregates
    DashboardV391 --> CapitalModelV2 : constrains (Mode 2)
    CapitalModelV2 --> PoolSimulation : runs internally
    CapitalModelV2 --> Trade384 : groups by position

    DashboardV391 --> CoinAnalysis : extended metrics
    DashboardV391 --> PDFExporterV2 : exports PDF
    DashboardV391 --> CSVExport : exports CSV
    DashboardV391 --> PortfolioManager : save/load portfolios

    CommissionModel ..> PoolSimulation : rebate settlement mirrors
```"""


def build_component_diagram():
    """Return Mermaid component diagram string."""
    return """```mermaid
flowchart TB
    subgraph DATA["DATA LAYER"]
        direction LR
        BYBIT["Bybit v5 API<br/><i>Public, no auth</i>"]
        FETCH["data/fetcher.py<br/><b>BybitFetcher</b>"]
        NORM["data/normalizer.py<br/><b>OHLCVNormalizer</b>"]
        CACHE[("data/cache/<br/>399 coins<br/>1m Parquet<br/>~6.2 GB")]
        UPLOAD["User CSV Upload"]

        BYBIT -->|klines| FETCH
        FETCH -->|write| CACHE
        UPLOAD -->|normalize| NORM
        NORM -->|write| CACHE
    end

    subgraph SIGNALS["SIGNAL LAYER"]
        direction LR
        SIG["signals/four_pillars_v383.py<br/><b>compute_signals_v383()</b>"]
        STOCH["signals/stochastics.py<br/>9-3, 14-3, 40-3, 60-10"]
        CLOUD["signals/clouds.py<br/>Ripster 5/12, 34/50, 72/89, 180/200"]
        SM["signals/state_machine_v383.py<br/><b>FourPillarsStateMachine383</b>"]

        SIG --> STOCH
        SIG --> CLOUD
        SIG --> SM
    end

    subgraph ENGINE["ENGINE LAYER"]
        direction LR
        BT["engine/backtester_v384.py<br/><b>Backtester384</b>"]
        POS["engine/position_v384.py<br/><b>PositionSlot384</b><br/><b>Trade384</b>"]
        COMM["engine/commission.py<br/><b>CommissionModel</b><br/>Taker 0.08% / Maker 0.02%<br/>Rebate 70% daily 5pm UTC"]
        AVWAP["engine/avwap.py<br/><b>AVWAPTracker</b>"]

        BT --> POS
        BT --> COMM
        POS --> AVWAP
    end

    subgraph PORTFOLIO["PORTFOLIO LAYER"]
        direction LR
        ALIGN["align_portfolio_equity()<br/><i>in dashboard</i>"]
        CAP["utils/capital_model_v2.py<br/><b>apply_capital_constraints()</b><br/>Exchange-model pool<br/>Position grouping<br/>Daily rebate settlement"]
        PM["utils/portfolio_manager.py<br/>JSON save/load/list/delete"]
    end

    subgraph ANALYSIS["ANALYSIS LAYER"]
        direction LR
        COIN["utils/coin_analysis.py<br/>Extended metrics<br/>Grade/exit distributions<br/>Monthly P&L<br/>Daily volume stats"]
    end

    subgraph OUTPUT["OUTPUT LAYER"]
        direction LR
        DASH["scripts/dashboard_v391.py<br/><b>Streamlit Dashboard v3.9.1</b><br/>5 tabs: Settings | Single | Sweep<br/>Sweep Detail | Portfolio"]
        PDF["utils/pdf_exporter_v2.py<br/>Multi-page PDF<br/>matplotlib + reportlab"]
        CSV["Combined Trades CSV<br/>symbol + datetime mapping"]
    end

    CACHE -->|load 5m OHLCV| DASH
    DASH -->|DataFrame| SIG
    SIG -->|signals + atr| BT
    BT -->|Trade384[], equity, metrics| DASH
    DASH -->|coin_results[]| ALIGN
    ALIGN -->|pf_data| CAP
    CAP -->|adjusted results| DASH
    DASH --> COIN
    DASH --> PDF
    DASH --> CSV
    DASH --> PM

    style DATA fill:#1a1a2e,stroke:#4488ff,color:#fff
    style SIGNALS fill:#16213e,stroke:#00ff88,color:#fff
    style ENGINE fill:#1a1a2e,stroke:#ff4444,color:#fff
    style PORTFOLIO fill:#16213e,stroke:#ffaa00,color:#fff
    style ANALYSIS fill:#1a1a2e,stroke:#aa88ff,color:#fff
    style OUTPUT fill:#16213e,stroke:#00ff88,color:#fff
```"""


def build_sequence_diagram():
    """Return Mermaid sequence diagram for portfolio flow."""
    return """```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant D as Dashboard v3.9.1
    participant C as ParquetCache
    participant S as SignalPipeline
    participant E as Backtester384
    participant CM as CommissionModel
    participant A as align_portfolio_equity
    participant K as CapitalModelV2
    participant AN as CoinAnalysis
    participant PDF as PDFExporterV2
    participant CSV as CSVExport

    U->>D: Select coins + params + mode
    Note over D: Mode 1: Per-Coin Independent<br/>Mode 2: Shared Pool

    loop For each coin in portfolio
        D->>C: load_data(symbol, "5m")
        C-->>D: DataFrame (OHLCV)
        D->>S: compute_signals_v383(df, sig_params)
        S-->>D: df + signal columns + ATR
        D->>E: Backtester384(run_params).run(df_sig)

        Note over E,CM: Per-bar loop (8640 bars / 30 days)
        activate E
        E->>CM: check_settlement(bar_dt)
        Note over CM: 5pm UTC: rebate = daily_comm * 70%
        CM-->>E: rebate amount (credited to equity)
        E->>E: Check SL/TP exits (maker 0.02%)
        E->>E: Update AVWAP + trailing SL
        E->>E: Check scale-outs (maker 0.02%)
        E->>E: Process pending limit orders
        E->>E: Check A/B/C/D entries (taker 0.08%)
        E->>E: Check ADD/RE entries (maker 0.02%)
        deactivate E

        E-->>D: {trades_df, equity_curve, metrics, position_counts}
    end

    D->>A: align_portfolio_equity(coin_results)
    A-->>D: pf_data {master_dt, portfolio_eq, per_coin_eq, capital_allocated}

    alt Mode 2: Shared Pool
        D->>K: apply_capital_constraints(coin_results, pf, $10k, $500)
        activate K
        Note over K: 1. Group trades by (coin, entry_bar)<br/>2. Sort positions by entry_bar<br/>3. Exchange-model pool simulation
        K->>K: Process position events
        Note over K: For each position:<br/>- Settle daily rebate at 5pm UTC<br/>- Close expired positions<br/>- available = balance - margin_used<br/>- Accept if available >= $500<br/>- Reject if insufficient
        K->>K: Rebuild equity curves (rejected removed)
        K->>K: Compute pool_balance_history (per-bar)
        K->>K: Rebase: rebased_portfolio_eq, rebased_chart_eq
        K-->>D: {adjusted_pf, adjusted_coin_results, capital_efficiency}
        deactivate K
    end

    D->>AN: compute_extended_metrics(trades_df)
    D->>AN: compute_daily_volume_stats(trades_df)
    AN-->>D: metrics + volume/rebate stats

    D->>D: Render Streamlit UI (Plotly charts, tables)

    opt User clicks "Export PDF"
        D->>PDF: generate_portfolio_pdf(pf, coins, capital_result)
        PDF-->>D: PDF file path
    end

    opt User clicks "Export CSV"
        D->>CSV: Generate combined trades DataFrame
        Note over CSV: Map bar indices to datetimes<br/>Add symbol column
        CSV-->>D: Download button with CSV data
    end
```"""


def build_data_model_diagram():
    """Return Mermaid ER diagram for key data structures."""
    return """```mermaid
erDiagram
    OHLCV_BAR {
        datetime datetime PK
        float open
        float high
        float low
        float close
        float volume
    }

    SIGNAL_BAR {
        int bar_index PK
        bool long_a
        bool long_b
        bool long_c
        bool long_d
        bool short_a
        bool short_b
        bool short_c
        bool short_d
        bool add_long
        bool add_short
        bool reentry_long
        bool reentry_short
        float atr
        float stoch_9
        float stoch_14
        float stoch_40
        float stoch_60
    }

    TRADE384 {
        int entry_bar PK
        int exit_bar
        string direction
        string grade
        float entry_price
        float exit_price
        float sl_price
        float tp_price
        float pnl
        float commission
        float net_pnl
        float mfe
        float mae
        string exit_reason
        bool saw_green
        bool be_raised
        int scale_idx
        float entry_atr
    }

    POSITION_EVENT {
        string coin PK
        int entry_bar PK
        int exit_bar
        float net_pnl
        float commission
        string grade
        int strength
        int n_records
    }

    COIN_RESULT {
        string symbol PK
        list trades
        DataFrame trades_df
        ndarray equity_curve
        ndarray position_counts
        list datetime_index
        dict metrics
    }

    PORTFOLIO_DATA {
        DatetimeIndex master_dt
        ndarray portfolio_eq
        dict per_coin_eq
        ndarray total_positions
        ndarray capital_allocated
        float portfolio_dd_pct
        dict best_moment
        dict worst_moment
    }

    CAPITAL_EFFICIENCY {
        float total_capital
        float final_pool
        float pool_pnl
        float peak_used
        float peak_pct
        float avg_used
        float idle_pct
        int trades_rejected
        float rejection_pct
        float missed_pnl
    }

    METRICS {
        int total_trades
        float win_rate
        float net_pnl
        float total_commission
        float total_rebate
        float net_pnl_after_rebate
        float sharpe
        float profit_factor
        float max_drawdown_pct
        float total_volume
        int total_sides
        float pct_losers_saw_green
        dict grades
    }

    OHLCV_BAR ||--|| SIGNAL_BAR : "compute_signals_v383"
    SIGNAL_BAR ||--|{ TRADE384 : "Backtester384.run()"
    TRADE384 }|--|| POSITION_EVENT : "group by (coin, entry_bar)"
    TRADE384 }|--|| COIN_RESULT : "collected into"
    COIN_RESULT }|--|| PORTFOLIO_DATA : "align_portfolio_equity"
    COIN_RESULT ||--|| METRICS : "contains"
    PORTFOLIO_DATA ||--|| CAPITAL_EFFICIENCY : "apply_capital_constraints"
```"""


def build_commission_flow():
    """Return Mermaid diagram for commission and rebate flow."""
    return """```mermaid
flowchart LR
    subgraph ENTRY["POSITION ENTRY"]
        MO["Market Order<br/>(A/B/C/D/R grades)"]
        LO["Limit Order<br/>(ADD/RE fills)"]
    end

    subgraph FEES["COMMISSION CHARGED"]
        TAKER["TAKER FEE<br/>0.08% of notional<br/>$10,000 x 0.0008 = $8.00"]
        MAKER["MAKER FEE<br/>0.02% of notional<br/>$10,000 x 0.0002 = $2.00"]
    end

    subgraph EXIT["POSITION EXIT"]
        SL["Stop Loss<br/>(limit order)"]
        TP["Take Profit<br/>(limit order)"]
        SCALE["Scale-Out<br/>(limit order)"]
        END_C["END Close<br/>(last bar)"]
    end

    subgraph SETTLEMENT["DAILY SETTLEMENT (5pm UTC)"]
        GROSS["Gross Commission<br/>(accumulated daily)"]
        REBATE["Rebate Credit<br/>70% of gross"]
        POOL["Pool Balance<br/>(realized cash)"]
    end

    subgraph BLENDED["BLENDED RATE"]
        BLEND["Entry: 0.08% + Exit: 0.02%<br/>= 0.10% round-trip<br/>= 0.05% per side avg"]
    end

    MO -->|entry| TAKER
    LO -->|entry| MAKER
    SL -->|exit| MAKER
    TP -->|exit| MAKER
    SCALE -->|exit| MAKER
    END_C -->|exit| MAKER

    TAKER --> GROSS
    MAKER --> GROSS
    GROSS -->|daily 5pm UTC| REBATE
    REBATE -->|credit| POOL

    TAKER --> BLEND
    MAKER --> BLEND

    style ENTRY fill:#16213e,stroke:#4488ff,color:#fff
    style FEES fill:#1a1a2e,stroke:#ff4444,color:#fff
    style EXIT fill:#16213e,stroke:#00ff88,color:#fff
    style SETTLEMENT fill:#1a1a2e,stroke:#ffaa00,color:#fff
    style BLENDED fill:#16213e,stroke:#aa88ff,color:#fff
```"""


def build_pool_state_diagram():
    """Return Mermaid state diagram for shared pool lifecycle."""
    return """```mermaid
stateDiagram-v2
    [*] --> PoolReady : deposit $10,000

    PoolReady --> CheckSignal : new bar arrives

    CheckSignal --> EvaluateCapital : signal detected (A/B/C/D)
    CheckSignal --> CheckSettlement : no signal

    CheckSettlement --> SettleRebate : 5pm UTC crossed
    CheckSettlement --> CheckExpired : not settlement time

    SettleRebate --> CheckExpired : balance += daily_comm * 70%

    CheckExpired --> ReleaseMargin : position exit_bar <= current_bar
    CheckExpired --> EvaluateCapital : no expired positions

    ReleaseMargin --> EvaluateCapital : balance += net_pnl, margin_used -= $500

    EvaluateCapital --> AcceptTrade : available >= $500
    EvaluateCapital --> RejectTrade : available < $500

    AcceptTrade --> PoolReady : margin_used += $500

    RejectTrade --> PoolReady : log rejection, missed P&L

    state AcceptTrade {
        [*] --> LockMargin
        LockMargin --> TrackCommission : taker 0.08% on entry
        TrackCommission --> MonitorPosition : position open
        MonitorPosition --> ExitPosition : SL/TP/Scale/END
        ExitPosition --> SettlePnL : maker 0.02% on exit
        SettlePnL --> [*] : balance += net_pnl
    }

    note right of PoolReady
        Pool State:
        balance (realized cash)
        margin_used (locked capital)
        available = balance - margin_used
    end note

    note right of SettleRebate
        Daily at 17:00 UTC
        rebate = daily_commission * 0.70
        Prevents pool drain
    end note
```"""


def main():
    """Generate Mermaid UML markdown file for Obsidian."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "four-pillars-architecture.md"

    content = f"""# Four Pillars Trading System -- Architecture (v3.9.1)

**Generated**: {ts}
**Dashboard**: `scripts/dashboard_v391.py` (2338 lines, 14 patches)
**Engine**: `engine/backtester_v384.py` (v3.8.4 with maker-exit fix)

---

## 1. System Component Diagram

Shows all modules and their dependencies. Main flow: Data -> Signals -> Engine -> Portfolio -> Capital Model -> Display/Export.

{build_component_diagram()}

---

## 2. Class Diagram

All classes, dataclasses, key methods, and relationships.

{build_class_diagram()}

---

## 3. Portfolio Backtest Sequence (Main Flow)

Step-by-step flow for a portfolio backtest in the v3.9.1 dashboard. Covers both Mode 1 (Per-Coin Independent) and Mode 2 (Shared Pool).

{build_sequence_diagram()}

---

## 4. Data Model (Entity-Relationship)

Key data structures and how they transform through the pipeline.

{build_data_model_diagram()}

---

## 5. Commission & Rebate Flow

How fees are charged, when rebates settle, and the blended rate calculation.

{build_commission_flow()}

---

## 6. Shared Pool State Machine

Lifecycle of the exchange-model pool simulation in Mode 2.

{build_pool_state_diagram()}

---

## File Inventory

| # | File | Lines | Layer | Role |
|---|------|-------|-------|------|
| 1 | `data/fetcher.py` | -- | Data | Bybit v5 API client, pagination, caching |
| 2 | `data/normalizer.py` | -- | Data | Universal OHLCV CSV-to-parquet (6 exchange formats) |
| 3 | `data/cache/` | 6.2 GB | Data | 399 coins, 1m Parquet files |
| 4 | `signals/stochastics.py` | -- | Signal | 4 stochastic periods (Kurisko Raw K) |
| 5 | `signals/clouds.py` | -- | Signal | Ripster EMA Clouds (5 cloud pairs) |
| 6 | `signals/state_machine_v383.py` | -- | Signal | A/B/C/D grading + ADD/RE signals |
| 7 | `signals/four_pillars_v383.py` | 111 | Signal | Signal pipeline orchestrator |
| 8 | `engine/backtester_v384.py` | ~581 | Engine | Core backtest engine, multi-slot positions |
| 9 | `engine/position_v384.py` | 296 | Engine | PositionSlot384 + Trade384 dataclass |
| 10 | `engine/commission.py` | 107 | Engine | Taker/maker rates, daily rebate settlement |
| 11 | `engine/avwap.py` | -- | Engine | Anchored VWAP tracker |
| 12 | `utils/capital_model_v2.py` | 537 | Portfolio | Exchange-model pool, position grouping, daily rebate |
| 13 | `utils/portfolio_manager.py` | 93 | Portfolio | JSON portfolio save/load/list/delete |
| 14 | `utils/coin_analysis.py` | 211 | Analysis | Extended metrics, grade/exit distributions, volume stats |
| 15 | `utils/pdf_exporter_v2.py` | 330 | Output | Multi-page PDF (matplotlib + reportlab) |
| 16 | `scripts/dashboard_v391.py` | 2338 | Output | Streamlit GUI (5 tabs, 2 portfolio modes) |
| 17 | `scripts/build_dashboard_v391.py` | 916 | Build | Build script: creates files 12, 15, 16 |

## Commission Reference

| Action | Order Type | Fee Rate | Example ($10k notional) |
|--------|-----------|----------|------------------------|
| Entry (A/B/C/D/R) | Market | 0.08% (taker) | $8.00 |
| Entry (ADD/RE) | Limit | 0.02% (maker) | $2.00 |
| Exit (SL/TP/Scale/END) | Limit | 0.02% (maker) | $2.00 |
| Round-trip (market entry) | -- | 0.10% total | $10.00 |
| Blended per-side | -- | 0.05% avg | $5.00 |
| Daily rebate | -- | 70% of gross | settled 5pm UTC |

## Portfolio Modes

| Feature | Mode 1: Per-Coin Independent | Mode 2: Shared Pool |
|---------|------------------------------|---------------------|
| Capital | N x $10,000 (engine default) | User deposit (e.g. $10,000) |
| Margin per trade | Implicit in engine | Explicit $500 from pool |
| Equity baseline | N x $10,000 | Deposit amount |
| Trade rejection | Never (unlimited capital) | When available < margin |
| Rebate settlement | Per-coin in engine | Daily in pool simulation |
| DD% reference | Engine baseline | Deposit (pool balance history) |
| Best metric | Rebased equity | Pool balance (realized cash) |
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("=" * 70)
    print("UML Diagram Builder -- " + ts)
    print("=" * 70)
    print("  Output: " + str(out_path))
    print("  Size:   " + str(len(content)) + " chars")
    print("  Open in Obsidian reading view to render Mermaid diagrams.")
    print("=" * 70)


if __name__ == "__main__":
    main()
