# Dashboard Design Document
## Four Pillars Trading System v3.8.4

**Living Document** -- Updated per major version.
**Last Updated:** 2026-02-16
**File:** `DASHBOARD-DESIGN.md` (project root)

---

## 1. Executive Summary

Streamlit-based backtesting dashboard for the Four Pillars trading strategy.
4 operational modes: Settings, Single, Sweep, Portfolio.

**Main file:** `scripts/dashboard.py` (1,897 lines)
**Run command:** `streamlit run scripts/dashboard.py`
**From directory:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester`

---

## 2. Version History

### v3.5.1
- Cloud 3 trail SL -- bled out (abandoned)

### v3.6
- AVWAP SL -- bled out (abandoned)
- Pine: `02-STRATEGY/Indicators/four_pillars_v3_6.pine`

### v3.7 (Rebate Farming Architecture)
- Goal: ~3000 trades/month, flat equity, rebate = profit
- Tight SL/TP: 1.0 ATR SL, 1.5 ATR TP (no trailing)
- B/C open fresh, B/C can flip, free flips
- Cloud 2 re-entry broadened, single order ID, pyramiding=1

### v3.7.1 (Commission Fix)
- cash_per_order=8 replaces commission.percent
- Removed strategy.close_all() from all flips
- strategy.cancel() before flips, 3-bar cooldown
- Dashboard Comm$ row added
- **BUG FOUND:** Phantom Trade Bug -- close_all + entry = double commission
- Pine: `02-STRATEGY/Indicators/four_pillars_v3_7_1_strategy.pine`

### v3.8 (2026-02-10)
- Cloud 3 directional filter (always on)
- ATR-based breakeven raise
- Rate-based commission model (0.0008 taker)
- MFE/MAE tracking added
- Files: `state_machine.py`, `clouds.py`
- Result: RIVER 5m: 1,278 trades, +$18,952 net

### v3.8.3 (2026-02-11)
- Entry logic overhaul: zone trigger from 9-K to 60-K
- A/B/C grading corrected, D signal added (continuation)
- SL overhaul: ATR * sl_mult (default 2.0)
- Scale-out: every 5 bars at +2sigma, close 50%, max 2
- AVWAP inheritance: ADD/RE clone parent accumulator
- Best SL: 2.5 ATR (9/10 coins profitable)
- LSG: 85-92% across all coins
- **Issue:** D+R grades drag P&L: D -$3.59/tr, R -$3.00/tr
- Files: `state_machine_v383.py`, `four_pillars_v383.py`, `position_v383.py`, `backtester_v383.py`

### v3.8.4 (2026-02-11) -- CURRENT
- Optional ATR-based TP on v3.8.3
- SL checked first (pessimistic)
- Only re-entry on SL, not TP
- TP results (coin-specific, NOT universal):
  - RIVER: TP=2.0 beats no-TP (+$7,911 vs +$6,261)
  - KITE: No TP best (+$5,069)
  - BERA: No TP best (+$4,883)
- Optimal 3-coin net: +$17,863
- Capital analysis: DD $6,138, peak margin $1,500, headroom $2,362 on $10K
- Files: `position_v384.py`, `backtester_v384.py`

---

## 3. Architecture Overview

### Module Dependencies

```
dashboard.py
  |-- data.fetcher.BybitFetcher        (OHLCV from Bybit v5 API)
  |-- data.normalizer.OHLCVNormalizer  (CSV-to-parquet, 6 formats)
  |-- signals.four_pillars_v383        (compute_signals_v383)
  |      |-- signals.stochastics       (4-K stochastic)
  |      |-- signals.clouds            (Ripster EMA clouds)
  |      |-- signals.state_machine_v383 (A/B/C/D state machine)
  |-- engine.backtester_v384           (Backtester384 multi-slot engine)
  |      |-- engine.position_v384      (PositionSlot384)
  |      |-- engine.avwap              (AVWAP center + sigma bands)
  |      |-- engine.commission         (rate-based + daily rebate)
  |-- utils.portfolio_manager          (NEW: save/load portfolio templates)
  |-- utils.coin_analysis              (NEW: extended per-coin metrics)
  |-- utils.pdf_exporter               (NEW: PDF report generation)
  |-- utils.capital_model              (NEW: unified capital constraints)
```

### Streamlit App Flow

```
st.session_state["mode"]:
  "settings" -> Parameter configuration sidebar
                 |-> "single"     (single coin backtest)
                 |-> "sweep"      (multi-coin sequential sweep)
                 |-> "portfolio"  (aggregated multi-coin analysis)

  "single"   -> 5-tab results: Overview, Trade Log, MFE/MAE, ML, Validation
  "sweep"    -> Incremental sweep with CSV persistence -> sweep_detail
  "portfolio"-> Coin selection -> Run -> Summary + Charts + Correlation
```

### Session State Keys

| Key | Type | Purpose |
|-----|------|---------|
| `mode` | str | Current view: settings/single/sweep/sweep_detail/portfolio |
| `single_data` | dict/None | Cached single-coin backtest results |
| `sweep_data` | list/None | Cached sweep results (list of dicts) |
| `sweep_detail_symbol` | str/None | Currently viewed sweep detail coin |
| `sweep_detail_data` | dict/None | Cached sweep detail results |
| `portfolio_data` | dict/None | Cached portfolio results: {"pf": ..., "coin_results": ...} |

---

## 4. Functionality Reference

### Settings Mode (Lines 450-660)

**Sidebar parameters:**
- Signal: stoch periods (9/14/40/60), K smooth, D smooth
- Clouds: Cloud 2-5 fast/slow EMA periods
- Position: Margin ($), Leverage, Max positions, AVWAP adds/re-entry
- Commission: Taker rate (0.08%), Maker rate (0.02%), Rebate tier
- ML: n_estimators, max_depth, threshold (Tab 4 meta-label)
- Filters: Date range, timeframe (1m/5m)
- TP/SL: sl_mult, tp_mult (0=disabled), checkpoint_interval

**Mode selection buttons:**
- Line 449: "Run Single" -> sets mode="single"
- Line 452: "Run Sweep" -> sets mode="sweep"
- Line 454: "Run Portfolio" -> sets mode="portfolio"

### Single Mode (Lines 660-1722)

**5-tab layout:**
1. **Overview** (Tab 1): Equity curve, metrics summary, drawdown windows
2. **Trade Analysis** (Tab 2): Full trade log dataframe
3. **MFE/MAE** (Tab 3): Scatter plot of MFE vs MAE
4. **ML** (Tab 4): XGBoost meta-label analysis (placeholder in sweep detail)
5. **Validation** (Tab 5): Signal validation (placeholder in sweep detail)

**Key functions called:**
- `load_data(symbol, timeframe)` -> Line 150
- `apply_date_filter(df, date_range)` -> Line 264
- `run_backtest(df, signal_params, bt_params)` -> Line 232

### Sweep Mode (Lines 1343-1680)

**Features:**
- Incremental: processes one coin at a time
- CSV persistence: saves to `data/output/sweep_progress_v384.csv`
- Auto-resume: keyed by `params_hash` (hash of all parameters)
- Crash-safe: appends to CSV after each coin
- Click-through: select coin from results -> sweep_detail mode

**Sweep results CSV columns:**
Symbol, Trades, WR%, Net, Exp, LSG%, ScaleOut, TP_Exits, SL_Exits, DD%, Sharpe, PF, Rebate$

### Portfolio Mode (Lines 1725-1898)

**Coin selection (Lines 1736-1766):**
- Top N: From sweep results sorted by Exp (deterministic)
- Lowest N: Bottom of sweep results
- Random N: `random.sample(cached, N)` (NOT saved)
- Custom: `st.multiselect()` from all cached coins

**Backtest loop (Lines 1774-1807):**
1. For each coin: load_data -> apply_date_filter -> run_backtest
2. Collect: equity_curve, position_counts, trades_df, metrics
3. Call `align_portfolio_equity()` -> aggregate results
4. Store in `st.session_state["portfolio_data"]`

**Results display (Lines 1810-1898):**
1. Summary metrics: Coins, Net P&L, Max DD%, Peak Capital, Total Trades
2. Best vs Worst moments: Equity/DD with timestamp and capital at that bar
3. LSG% per-coin table: Symbol, Trades, WR%, Net, LSG%, DD%, Sharpe, PF
4. Portfolio equity curve: Thin per-coin lines + bold portfolio line
5. Capital utilization: Fill chart of capital allocated over time
6. Correlation matrix: Equity change correlation heatmap

---

## 5. Key Functions & Line Numbers

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `load_data(symbol, timeframe)` | dashboard.py | 150 | Load OHLCV from cache, resample if 5m |
| `run_backtest(df, signal_params, bt_params)` | dashboard.py | 232 | Signal + backtest pipeline |
| `apply_date_filter(df, date_range)` | dashboard.py | 264 | Filter DataFrame by date |
| `find_drawdown_windows(eq, n_windows)` | dashboard.py | 290 | Top-N drawdown window extraction |
| `align_portfolio_equity(coin_results, ...)` | dashboard.py | 327 | Aggregate multi-coin equity curves |
| `compute_avg_green_bars(trades_df, df_sig)` | dashboard.py | 376 | Avg bars losers were profitable |
| `compute_signals_v383(df, params)` | signals/four_pillars_v383.py | - | Full signal pipeline |
| `Backtester384(params).run(df_sig)` | engine/backtester_v384.py | - | Multi-slot bar-by-bar execution |

---

## 6. File Locations

### Dashboard Core
- **Dashboard:** `scripts/dashboard.py` (1,897L)
- **Staging:** `staging/dashboard.py` (853L, v3.8.5 candidate)

### Engine
- **Active backtester:** `engine/backtester_v384.py` (580L)
- **Position tracking:** `engine/position_v384.py` (295L)
- **AVWAP:** `engine/avwap.py` (52L)
- **Commission:** `engine/commission.py` (106L)

### Signal Pipeline
- **Entry point:** `signals/four_pillars_v383.py` (111L)
- **State machine:** `signals/state_machine_v383.py` (339L)
- **Stochastics:** `signals/stochastics.py` (63L)
- **Clouds:** `signals/clouds.py` (85L)

### Data Layer
- **Fetcher:** `data/fetcher.py` (252L)
- **Normalizer:** `data/normalizer.py` (542L)
- **DB:** `data/db.py` (219L)
- **Cache dir:** `data/cache/` (399 coins, ~6.2 GB parquet)
- **Sweep CSV:** `data/output/sweep_progress_v384.csv`

### New Utils (Portfolio Enhancement v2)
- **Portfolio manager:** `utils/portfolio_manager.py`
- **Coin analysis:** `utils/coin_analysis.py`
- **PDF exporter:** `utils/pdf_exporter.py`
- **Capital model:** `utils/capital_model.py`
- **Portfolio storage:** `portfolios/*.json`

### BBW Simulator Pipeline
- **Layer 1:** `signals/bbwp.py` (295L) -- BBWP calculator
- **Layer 2:** `signals/bbw_sequence.py` (168L) -- sequence tracker
- **Layer 3:** `research/bbw_forward_returns.py` (121L) -- forward returns
- **Layer 4:** `research/bbw_simulator.py` (586L) -- simulator engine
- **Layer 4b:** `research/bbw_monte_carlo.py` (514L) -- Monte Carlo validation
- **Layer 5:** `research/bbw_report.py` (341L) -- report generation
- **Tests:** `tests/test_bbwp.py`, `test_bbw_sequence.py`, `test_forward_returns.py`, `test_bbw_simulator.py`

### Test Suites
- **Portfolio enhancements:** `tests/test_portfolio_enhancements.py`
- **Debug script:** `scripts/debug_portfolio_enhancements.py`

---

## 7. Capital Model

### Current (Per-Position Tracking)

```python
# dashboard.py line 349
capital_allocated = total_positions * margin_per_pos
```

- Each position (any coin) consumes margin_per_pos ($500 default)
- No total capital constraint -- tracks usage, doesn't limit entries
- Reports: Peak capital, capital at best/worst moments

### Planned (Unified Portfolio Pool)

Toggle: "Per-Coin Independent" vs "Unified Portfolio Pool"

When Unified:
- User inputs total_capital (e.g., $10,000)
- Post-processing filter rejects entries exceeding capital
- Priority: Signal-strength weighted KPI (grade + MFE bonus)
- Reports: Rejected trade count, missed P&L, idle capital %

Implementation: `utils/capital_model.py` -> `apply_capital_constraints()`

---

## 8. Data Flow

```
1. BybitFetcher.load_cached(symbol)
   -> Parquet from data/cache/ (1m bars)

2. resample_5m(df) if timeframe == "5m"
   -> OHLCV aggregation

3. compute_signals_v383(df, signal_params)
   -> Adds: stoch_k_9/14/40/60, cloud columns, state machine signals
   -> Adds: entry_signal, direction, grade (A/B/C/D/ADD/RE)
   -> Adds: ATR (Wilder's 14-bar RMA)

4. Backtester384(bt_params).run(df_sig)
   -> Bar-by-bar execution, multi-slot (up to 4 concurrent)
   -> Returns: equity_curve, position_counts, trades_df, metrics

5. Dashboard renders results
   -> Single: 5-tab layout with all metrics
   -> Sweep: Incremental CSV with progress bar
   -> Portfolio: align_portfolio_equity() -> charts + correlation
```

---

## 9. Export Capabilities

### Current
- **Sweep CSV:** `st.download_button` -> `sweep_v384.csv` (Line 1564)

### Planned
- **Portfolio PDF:** `utils/pdf_exporter.py` -> multi-page report
  - Executive summary, equity charts, per-coin detail pages
  - Capital utilization, correlation matrix
  - Button: "Export Portfolio Report as PDF"
  - Output: `results/pdf_reports/portfolio_report_{name}_{date}.pdf`

---

## 10. BBW Integration Points

BBW Layers 1-6 affect the dashboard in the following ways:

| Layer | Status | Dashboard Impact |
|-------|--------|------------------|
| L1-L2 | DONE | Signal columns available for display in trade log |
| L3 | DONE | Forward returns available for MFE/MAE analysis |
| L4 | DONE | Simulator results can feed portfolio optimization |
| L4b | DONE | Monte Carlo CI available for risk analysis tab |
| L5 | DONE | 11 CSVs generated for aggregate reporting |
| L6 | QUEUED | Ollama analysis results for strategy narrative |

**Future dashboard integration tasks:**
1. BBW tab in single mode: Display BBWP state, spectrum, sequence pattern
2. BBW-filtered portfolio: Only enter on specific BBWP states
3. L5 report viewer: Load and display bbw_report CSVs in dashboard
4. L4b confidence intervals: Show MC bands on equity curve

---

## 11. Future Enhancements (Roadmap)

### Phase 1: Reusable Portfolios -- BUILT
- `utils/portfolio_manager.py`: Save/load/list/delete JSON templates
- `portfolios/`: JSON storage directory
- Dashboard integration: Save/Load buttons in portfolio selection

### Phase 2: Enhanced Per-Coin Analysis -- BUILT
- `utils/coin_analysis.py`: 10 extended metrics + drill-down data
- Dashboard integration: Expanded table + Streamlit expanders per coin

### Phase 3: PDF Export -- BUILT
- `utils/pdf_exporter.py`: Multi-page PDF with charts
- Dependency: `pip install reportlab`
- Dashboard integration: Export button after portfolio results

### Phase 4: Unified Capital Model -- BUILT
- `utils/capital_model.py`: Post-processing capital constraints
- Dashboard integration: Toggle in sidebar, capital efficiency metrics
- Signal-strength weighted trade priority (grade + MFE)

### Phase 5 (Deferred): Portfolio Comparison
- Side-by-side comparison of 2 saved portfolios
- Waiting for BBW Layer 6 completion and full scope definition

---

## 12. Constants & Configuration

### Default Parameters
```
Margin: $500
Leverage: 20x
Notional: $10,000
Max Positions: 4
Taker Rate: 0.08% (0.0008)
Maker Rate: 0.02% (0.0002)
Rebate: 70%
SL Mult: 2.0 ATR
TP Mult: 0 (disabled)
Checkpoint Interval: 5 bars
```

### Stochastic Periods (Kurisko)
```
Entry:    9-3 (K=9, smooth=3)
Confirm:  14-3
Diverge:  40-3
Macro:    60-10
All Raw K (smooth=1)
```

### Ripster Cloud EMAs
```
Cloud 2: 5/12
Cloud 3: 34/50
Cloud 4: 72/89
Cloud 5: 180/200
```

---

## 13. Known Issues & Constraints

1. **Portfolio is aggregation, not simulation**: Each coin runs independently. No cross-coin capital sharing during backtest. Capital constraints are post-processed.
2. **Random N not saved**: Coin selections via "Random N" are lost on page refresh. Fix: Phase 1 auto-save.
3. **No PDF export**: Portfolio results only viewable in Streamlit. Fix: Phase 3.
4. **D+R grade drag**: D and R trades drag P&L by ~$3,300 on 3-coin portfolio. ML meta-label filter (Vince) is the intended fix.
5. **Tight TP destroys value**: TP < 2.0 ATR hurts most coins. Always backtest per coin.
6. **Commission ratio varies by price**: RIVER profitable (commission ~7% of TP), BTC fails (~46% of TP).
