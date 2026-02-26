# DASHBOARD V3 BUILD SPEC — VINCE Control Panel

**Version:** v3  
**Date:** 2026-02-13  
**Base:** `scripts/dashboard_v2.py` (1534 lines, Arrow + deprecation fixes)  
**Output:** `scripts/dashboard_v3.py`  
**Status:** REVIEW PENDING — do NOT build until Malik approves  

---

## PHILOSOPHY

The dashboard is VINCE's control panel. It is not a backtest viewer.

Every screen must answer a question VINCE needs to make a trading decision:
- **Can I trade this coin?** → Single Coin analysis
- **Which coins have edge?** → Discovery sweep
- **What params work best?** → Optimizer
- **Is the edge real?** → Validation
- **How much capital do I need?** → Portfolio risk
- **Go live?** → Deploy

If a metric doesn't help answer one of these questions, it doesn't belong on the dashboard.

---

## ARCHITECTURE

### Tab Structure (st.tabs — 6 tabs)

```
┌─────────────────────────────────────────────────────────┐
│ [Status Banner: sweep/backtest progress — always visible]│
├──────┬──────────┬──────────┬──────────┬────────┬────────┤
│ ⚙️   │ 🔍       │ 🎯       │ ✅        │ 💰     │ 🚀     │
│Single│Discovery │Optimizer │Validation│Capital │Deploy  │
│ Coin │  Sweep   │ (VINCE)  │  (WFE)   │ & Risk │        │
└──────┴──────────┴──────────┴──────────┴────────┴────────┘
```

Each tab feeds the next. Outputs from tab N are inputs to tab N+1.

### Global Sidebar (always visible, all tabs)

Current sidebar params stay — symbol, timeframe, stoch K values, Ripster EMAs, SL/TP/CD, commission, rebate, ML params. These are the "strategy config" shared across all tabs.

### Persistent Status Banner (above tabs)

Reads from disk (not session_state). Shows:
- Sweep status: `🔄 Sweep: AGIUSDT (24/400) — 6%` or `✅ Sweep complete: 400 coins`
- Backtest status: `⏳ Running: RIVERUSDT...`
- Idle: collapsed/hidden

---

## TAB 1: ⚙️ SINGLE COIN

**Question answered:** "Can I trade this coin with these params?"

### Existing (keep as-is from v2):
- Run Backtest button
- Equity curve
- Trade log
- 5 sub-tabs: Overview, Trade Analysis, MFE/MAE, ML Meta-Label, Validation
- Back to Settings button

### Add:
| Metric | Description | Location |
|--------|-------------|----------|
| Peak Capital | max(concurrent_positions × notional) at any point | Overview header |
| Capital Efficiency | net_pnl / peak_capital × 100 | Overview header |
| Max Single Win $ | largest winning trade | Overview header |
| Max Single Loss $ | largest losing trade | Overview header |
| Avg Winner $ | mean profit of winners | Overview header |
| Avg Loser $ | mean loss of losers | Overview header |
| Win/Loss Ratio | avg_winner / abs(avg_loser) | Overview header |
| Max Win Streak | consecutive winners | Trade Analysis |
| Max Loss Streak | consecutive losers | Trade Analysis |
| Expectancy Stability | std(rolling_expectancy) over 50-trade windows | Trade Analysis chart |
| LSG Flag | if LSG% > 90%, show ⚠️ "High reversion — losers frequently see green" | Overview, red text |

### Edge Quality Panel (new, inside Overview):
```
┌─ Edge Quality ──────────────────────────────────────┐
│ Expectancy: $20.27    Stability: ±$3.12 (σ)        │
│ Avg Win: $47.80       Avg Loss: -$28.90             │
│ W/L Ratio: 1.65       Best: +$312    Worst: -$89    │
│ Max Streak: 8W / 12L  LSG: 94.4% ⚠️                │
│ Capital Eff: 172%     Peak Capital: $30,000          │
└─────────────────────────────────────────────────────┘
```

---

## TAB 2: 🔍 DISCOVERY SWEEP

**Question answered:** "Which coins from my universe have edge?"

### Sweep Persistence (disk-based):
- Results file: `results/sweep_v3_{timeframe}_{params_hash}.csv`
- Write after EVERY coin (append mode)
- On tab load: read CSV → determine state (not started / in progress / complete)
- Resume: skip symbols already in CSV
- New Sweep: delete CSV, start fresh

### Sweep Controls:
- Source: All Cache | Custom List (.txt/.csv) | Upload Data
- Start / Resume / Stop buttons (disabled during execution, never hidden)
- Progress bar + current coin name + ETA

### Sweep CSV Columns:
```
symbol, trades, wr_pct, expectancy, net_pnl, profit_factor,
sharpe, sortino, calmar,
max_dd_pct, max_dd_amt, peak_capital,
capital_efficiency, max_single_win, max_single_loss,
avg_winner, avg_loser, wl_ratio,
max_win_streak, max_loss_streak,
lsg_pct, lsg_bars_avg, scale_outs,
tp_exits, sl_exits, be_exits,
volume, rebate, net_after_rebate,
grade, start_date, end_date, calendar_days,
status, timestamp
```

### Results Display (after sweep complete or partial):

**Summary Row:**
```
Coins: 400 | Profitable: 388 (97%) | Total Trades: 2,878,011
Total Net: $11.77M | Total Rebate: $X | Total Volume: $X
Peak Portfolio Capital: $X | Portfolio Sharpe: X | Portfolio Calmar: X
```

**Results Table — DEFAULT SORT: Calmar ratio (not net PnL)**

Rationale: Net PnL rewards coins with more data/trades. Calmar rewards risk-adjusted return. A coin with $5K net and 5% DD is better than $50K net and 44% DD.

**Column groups (toggleable):**
- Core: Symbol, Trades, WR%, Net, Exp, Grade
- Risk: DD%, DD$, Peak Capital, Cap Eff, Calmar, Sharpe, Sortino
- Quality: LSG%, LSG Bars, Max Win, Max Loss, Avg W/L Ratio, Streaks
- Exits: TP, SL, BE, ScaleOut
- Time: Start, End, Days, Volume, Rebate$

**Filters:**
- Min trades: [slider, default 100]
- Min Calmar: [slider, default 0.5]
- Max DD%: [slider, default 30]
- Grade: [multi-select A/B/C/D/R]
- LSG% max: [slider, default 95 — flag high-reversion coins]

**Charts:**
- Top/Bottom 20 by Calmar (horizontal bar)
- Scatter: Net PnL vs Max DD% (bubble size = trades)
- Grade distribution pie

**Export:**
- CSV download (full results)
- "Send to Optimizer" button → passes filtered coin list to Tab 3

---

## TAB 3: 🎯 OPTIMIZER (VINCE)

**Question answered:** "What are the optimal params per coin?"

**Input:** Filtered coin list from Tab 2 (or manual selection)

**Function:** Grid search across param ranges per coin. Uses existing `optimizer/grid_search.py`.

**Sweep params:**
- Cooldown: [1, 2, 3, 5]
- SL multiplier: [2.0, 2.5, 3.0, 3.5]
- TP multiplier: [2.0, 2.5, 3.0]
- BE raise: [2, 3, 4, 5]
- (Future: stoch K values, EMA lengths)

**Output per coin:**
- Best param combo (by Calmar)
- Heatmap: param sensitivity (how much does changing one param shift results?)
- Overfitting risk flag: if best combo is an outlier vs neighbors

**Persistence:** `results/optimizer_{timeframe}_{hash}.json`
- Per-coin optimal params stored as JSON
- Resume support (skip coins already optimized)

**"Send to Validation" button** → passes optimized configs to Tab 4

**Note:** This tab is a future build. For v3, show placeholder with description of what it will do. Wire it up when VINCE ML orchestration is ready (P2 from build journal).

---

## TAB 4: ✅ VALIDATION (WFE)

**Question answered:** "Is the edge real or overfit?"

**Input:** Optimized param configs from Tab 3

**Methods:**
- Walk-Forward Efficiency (WFE): train on 70%, test on 30%, compare
- Monte Carlo: randomize entry order 1000x, measure P&L distribution
- Out-of-sample: if coin has >6 months data, hold out last month

**Output per coin:**
- WFE score (>0.30 = usable, >0.50 = strong)
- Monte Carlo: P5/P50/P95 net PnL
- Confidence grade: HIGH / MEDIUM / LOW / REJECT

**"Send to Portfolio" button** → passes validated coins to Tab 5

**Note:** Future build. Placeholder for v3. Depends on Tab 3 being functional.

---

## TAB 5: 💰 CAPITAL & RISK

**Question answered:** "How much money do I need and what's my risk?"

**Input:** Validated coin list with per-coin configs

### Portfolio Metrics:
| Metric | Calculation |
|--------|------------|
| Total Coins | count of validated coins |
| Max Concurrent Positions | max(sum of open positions across all coins at any timestamp) |
| Peak Capital Required | max_concurrent × notional ($10,000) |
| Total Net PnL | sum across all coins |
| Portfolio Sharpe | portfolio-level, not avg of individual |
| Portfolio Max DD | correlated drawdown across all coins (not sum of individual DDs) |
| Portfolio Calmar | total_net / portfolio_max_dd |
| Capital Efficiency | total_net / peak_capital |
| Break-Even Month | at current avg daily PnL, when does cumulative PnL exceed peak capital? |

### Risk Scenarios:
- **Base case:** validated params, historical data
- **Worst case:** all coins hit max DD simultaneously
- **Conservative:** only HIGH confidence coins, 50% position size

### Charts:
- Portfolio equity curve (all coins combined)
- Capital utilization over time (how much capital deployed per day)
- Correlation matrix (which coins move together — diversification check)

### Investor View:
- Clean summary: capital required, expected return, max risk, timeframe
- Exportable as PDF or presentation-ready table

**Note:** Future build. For v3, calculate and display portfolio-level metrics from sweep CSV. Full portfolio simulation is a later phase.

---

## TAB 6: 🚀 DEPLOY

**Question answered:** "Ready for live?"

**Input:** Final validated, risk-checked coin list with configs

**Output:**
- Per-coin JSON config for n8n webhooks
- Exchange API setup checklist
- Position size calculator (given account balance)
- Paper trade mode toggle
- Export all configs as ZIP

**Note:** Future build. Placeholder for v3.

---

## WHAT TO BUILD IN V3 (SCOPE)

### BUILD NOW (v3 release):
1. Tab structure with st.tabs() — all 6 tabs visible
2. Tab 1 (Single Coin): add missing metrics (peak capital, cap eff, max win/loss, avg W/L, streaks, LSG flag, edge quality panel)
3. Tab 2 (Discovery): full rebuild with disk persistence, resume, new CSV columns, filters, default sort by Calmar, charts, export
4. Tab 5 (Capital): basic portfolio metrics calculated from sweep CSV (no full simulation yet)
5. Persistent status banner
6. Button visibility fixes (always visible, disabled during execution)
7. State namespace isolation per tab

### PLACEHOLDER (show description, not functional):
- Tab 3 (Optimizer) — depends on VINCE ML orchestration
- Tab 4 (Validation) — depends on Tab 3
- Tab 6 (Deploy) — depends on Tab 4

### NOT IN SCOPE:
- Backtest engine changes (backtester_v384.py untouched)
- ML module changes
- Signal engine changes
- Data fetching changes

---

## NEW METRICS — BACKTESTER ADDITIONS

The backtester needs to return these additional metrics in its results dict. This is the ONLY engine change required.

**Add to `engine/backtester_v384.py` metrics output:**

```python
# Capital metrics
"peak_capital": max concurrent open positions × notional at any bar
"capital_efficiency": net_pnl / peak_capital * 100

# Trade quality
"max_single_win": max(trade_pnls where pnl > 0)
"max_single_loss": min(trade_pnls where pnl < 0)
"avg_winner": mean(trade_pnls where pnl > 0)
"avg_loser": mean(trade_pnls where pnl < 0)
"wl_ratio": avg_winner / abs(avg_loser)
"max_win_streak": longest consecutive wins
"max_loss_streak": longest consecutive losses

# Risk
"sortino": sortino_ratio (downside deviation only)
"calmar": net_pnl / abs(max_drawdown_amount) if max_dd != 0 else 0

# Breakeven exits (already tracked? verify)
"be_exits": count of trades closed at breakeven
```

**Where to add:** After existing metrics calculation block. These are all derivable from the existing `self.trades` list — no new data collection needed.

---

## IMPLEMENTATION SEQUENCE

```
Step 1:  Read dashboard_v2.py fully
Step 2:  Read backtester_v384.py metrics section
Step 3:  Backup dashboard_v2.py → dashboard_v2_backup.py
Step 4:  Add new metrics to backtester_v384.py (small, isolated change)
Step 5:  Create dashboard_v3.py from v2 base
Step 6:  Restructure into st.tabs() — 6 tabs
Step 7:  Isolate session_state namespaces (single_*, sweep_*, explorer_*)
Step 8:  Tab 1: add Edge Quality panel + new metrics display
Step 9:  Tab 2: rebuild sweep with disk persistence, new columns, filters, charts
Step 10: Tab 5: basic portfolio metrics from sweep CSV
Step 11: Tabs 3/4/6: placeholder pages with descriptions
Step 12: Add persistent status banner above tabs
Step 13: Fix button visibility (always visible, disabled during execution)
Step 14: Test single coin RIVERUSDT → verify new metrics display
Step 15: Test sweep start → switch tab → switch back → verify resume
Step 16: Test sweep complete → verify filters, sort by Calmar, charts
Step 17: Test export CSV → verify all columns present
```

---

## CLAUDE CODE PROMPT

```
Project: C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester

READ FIRST (mandatory):
- scripts/dashboard_v2.py (full file — this is the base)
- engine/backtester_v384.py (metrics section — understand what exists)
- DASHBOARD-V3-BUILD-SPEC.md (this file — the complete spec)

BACKUP:
- Copy dashboard_v2.py → dashboard_v2_backup.py

OUTPUT FILES:
- scripts/dashboard_v3.py (new file, do NOT overwrite v2)
- engine/backtester_v384.py (add new metrics only, do NOT change trade logic)

=== BACKTESTER METRICS ADDITION ===

In engine/backtester_v384.py, find the metrics calculation block (where
net_pnl, win_rate, profit_factor etc are computed). Add these metrics
using the existing self.trades list:

peak_capital: track max concurrent open positions × notional across all bars
capital_efficiency: net_pnl / peak_capital * 100
max_single_win: max profit from single trade
max_single_loss: max loss from single trade (negative number)
avg_winner: mean of winning trade PnLs
avg_loser: mean of losing trade PnLs
wl_ratio: avg_winner / abs(avg_loser)
max_win_streak: longest consecutive winning trades
max_loss_streak: longest consecutive losing trades
sortino: annualized sortino ratio using daily returns
calmar: net_pnl / abs(max_drawdown_amount)
be_exits: count of trades that closed at breakeven price

Do NOT change any entry logic, exit logic, or signal processing.
Metrics only.

=== DASHBOARD V3 ===

Create scripts/dashboard_v3.py based on dashboard_v2.py with these changes:

1. TABS: Replace single-view with st.tabs():
   Tab 1: "⚙️ Single Coin" — existing single-coin view + Edge Quality panel
   Tab 2: "🔍 Discovery" — rebuilt sweep with disk persistence
   Tab 3: "🎯 Optimizer" — placeholder (description only, not functional)
   Tab 4: "✅ Validation" — placeholder (description only, not functional)
   Tab 5: "💰 Capital & Risk" — basic portfolio metrics from sweep CSV
   Tab 6: "🚀 Deploy" — placeholder (description only, not functional)

2. TAB 1 — EDGE QUALITY PANEL:
   Add a panel in the Overview sub-tab showing:
   Peak Capital, Capital Efficiency, Max Win, Max Loss, Avg Winner,
   Avg Loser, W/L Ratio, Max Win Streak, Max Loss Streak,
   Expectancy Stability (std of rolling 50-trade expectancy),
   LSG flag (⚠️ if LSG% > 90%)
   Use st.columns() for clean layout.
   Read new metrics from backtester results dict.

3. TAB 2 — DISCOVERY SWEEP (full rebuild):
   a) Sweep source: All Cache | Custom List | Upload Data (keep existing)
   b) Persistence: write to results/sweep_v3_{tf}_{hash}.csv after EVERY coin
   c) Resume: on tab load, read CSV, skip completed symbols
   d) Buttons: Start/Resume/Stop — always visible, disabled during execution
   e) Progress: st.progress_bar + current coin + ETA
   f) CSV columns: symbol, trades, wr_pct, expectancy, net_pnl, profit_factor,
      sharpe, sortino, calmar, max_dd_pct, max_dd_amt, peak_capital,
      capital_efficiency, max_single_win, max_single_loss, avg_winner,
      avg_loser, wl_ratio, max_win_streak, max_loss_streak, lsg_pct,
      lsg_bars_avg, scale_outs, tp_exits, sl_exits, be_exits, volume,
      rebate, net_after_rebate, grade, start_date, end_date, calendar_days,
      status, timestamp
   g) Default sort: Calmar ratio descending (not net PnL)
   h) Filters: min trades, min Calmar, max DD%, grade multi-select, max LSG%
   i) Charts: Top/Bottom 20 by Calmar (bar), Net vs DD% scatter, grade pie
   j) Export CSV button

4. TAB 5 — CAPITAL & RISK (basic):
   Read completed sweep CSV. Calculate and display:
   - Total coins, total trades, total net PnL
   - Sum of peak capitals (worst case concurrent)
   - Portfolio capital efficiency
   - Average and worst Calmar across coins
   - Estimated capital required at different risk levels
   Show as clean metric cards using st.metric().

5. TABS 3/4/6 — PLACEHOLDERS:
   Each shows: tab title, description of what it will do, "Coming Soon"
   message, and what inputs it needs from the previous tab.

6. STATUS BANNER:
   At TOP of page (before tabs), read sweep CSV from disk:
   - If CSV exists and rows < total coins: show progress
   - If CSV complete: show summary
   - If no CSV: hidden
   Uses st.container() — survives tab switches because it reads disk.

7. STATE ISOLATION:
   - st.session_state.single_* for Tab 1
   - st.session_state.sweep_* for Tab 2
   - st.session_state.portfolio_* for Tab 5
   No shared mutable state between tabs.

8. FIXES CARRIED FROM V2:
   - Keep all Arrow serialization fixes (safe_dataframe)
   - Keep width='stretch' (not use_container_width)
   - Keep logging to logs/dashboard.log

=== CODE DEBT FIXES (mandatory) ===

CD-1: Extract render_detail_view(results, symbol) function.
  v2 has ~400 lines duplicated between single-coin view and sweep detail.
  Extract into one function. Call from Tab 1 results AND Tab 2 drill-down.

CD-2: Sweep error tracking.
  Replace `except Exception: pass` with:
  - error_count counter in progress UI
  - Failed symbols logged to logs/dashboard.log with traceback
  - status column in sweep CSV: "ok" or "error: {reason}"
  - Summary shows "X coins failed" with st.expander for error list

CD-3: Enable ALL 5 analysis tabs in sweep drill-down.
  Remove the st.info() gate on ML tabs. render_detail_view() handles this.

CD-4: Use safe_plotly_chart() for ALL plotly calls, or remove the wrapper.

CD-5: Preserve normalizer/upload flow (~80 lines from v2) in Tab 2 sweep source.

=== COIN CHARACTERISTICS (compute from OHLCV before backtest) ===

Add to backtester or as pre-processing step. For each coin, compute from raw data:
- avg_daily_volume: mean(daily quote volume)
- volume_stability: std(daily_vol) / mean(daily_vol)
- avg_spread_proxy: mean((high-low)/close)
- volatility_regime: std(returns) annualized
- trend_strength: abs(close[-1] - close[0]) / std(close)
- mean_reversion_score: autocorrelation of returns at lag 1
- gap_pct: (bars with volume=0) / total bars
- price_range: (max_price - min_price) / min_price

Add these as columns to sweep CSV output.
In Tab 2, show as expandable "Coin Profile" per row.

=== LSG CATEGORIZATION ===

For every losing trade where saw_green=True, categorize:
- Cat A (fast reversal): time_in_green < 3 bars
- Cat B (slow bleed): time_in_green > 10 bars
- Cat C (near-TP miss): MFE > 80% of TP target
- Cat D (BE failure): MFE > BE threshold but BE not raised

Add to backtester metrics:
  lsg_cat_a_pct, lsg_cat_b_pct, lsg_cat_c_pct, lsg_cat_d_pct,
  avg_loser_mfe, avg_loser_green_bars

Display in Tab 1 Edge Quality panel as breakdown under LSG%.
Add to sweep CSV columns.

=== ENTRY-STATE LOGGING (VINCE training data) ===

For EVERY trade (not just losers), log indicator state at entry bar:
  entry_stoch9_value, entry_stoch9_direction,
  entry_stoch14_value, entry_stoch40_value,
  entry_stoch60_value, entry_stoch60_d,
  entry_ripster_cloud (which pair), entry_ripster_expanding (bool),
  entry_bbwp_value, entry_bbwp_spectrum,
  entry_avwap_distance (% from AVWAP),
  entry_atr, entry_vol_ratio (vol / SMA20),
  entry_grade

Storage: Save per-trade parquet files:
  results/trades_{symbol}_{timeframe}.parquet
  One row per trade. All existing trade fields + entry state fields.
  This is VINCE's raw training dataset.

Dashboard Tab 1: Add LSG Comparison Panel showing avg entry-state
values for winners vs LSG losers side-by-side:
  Avg Stoch9, AVWAP dist, Vol Ratio, Ripster expanding%, BBWP value
  Split into two columns: "Winners" | "LSG Losers"

Sweep CSV: Add per-coin aggregates:
  avg_winner_entry_stoch9, avg_lsg_entry_stoch9,
  avg_winner_avwap_dist, avg_lsg_avwap_dist,
  winner_ripster_expanding_pct, lsg_ripster_expanding_pct

=== TRADE LIFECYCLE LOGGING ===

For EVERY trade, while position is open, track indicator behavior
and compute summary stats at close. Store in per-trade parquet
(Layer 1 — results/trades_{symbol}_{tf}.parquet), NOT every bar.

Lifecycle summary fields per trade:
  life_bars, life_stoch9_min, life_stoch9_max, life_stoch9_trend (slope),
  life_stoch9_crossed_signal (bool), life_ripster_flip (bool),
  life_ripster_width_change (%), life_bbwp_delta,
  life_avwap_max_dist, life_avwap_end_dist,
  life_vol_avg, life_vol_trend (slope),
  life_mfe_bar (bar# of MFE), life_mae_bar (bar# of MAE),
  life_pnl_path ("direct" / "green_then_red" / "red_then_green" / "choppy")

PnL path classification logic:
  - "direct": never crossed entry price after moving in trade direction
  - "green_then_red": went green (>0 unrealized), then closed at loss
  - "red_then_green": went red first, then recovered to profit
  - "choppy": crossed entry price 3+ times

Dashboard Tab 1: Show P&L path distribution + lifecycle comparison
(avg bars to MFE winners vs losers, ripster flip rate, stoch9 cross rate).

Optional Layer 2 (on-demand only, flag --save-bars):
  results/bars_{symbol}_{tf}.parquet — one row per bar per open trade.
  17 columns per bar. Only generate when VINCE needs sequence data.
  NOT generated during normal sweep or backtest runs.

=== ADDITIONAL FEATURES ===

S-1: Date range filter — two st.sidebar.date_input() widgets.
  Filter df before passing to backtest. "Last 30 days" vs "all data".

S-2: Param presets — Save/Load JSON to data/presets/.
  Ship 3 defaults: "Rebate Farm", "Conservative", "Aggressive".
  Sidebar dropdown + "Save Current" button.

S-3: Sweep stop button — sets session_state flag, loop breaks,
  remaining coins stay for resume via CSV.

=== CONSTRAINTS ===
- Create NEW file dashboard_v3.py — do NOT overwrite v2
- Do NOT change entry/exit/signal logic in backtester
- Keep ALL existing sidebar parameters exactly as they are
- Keep existing st.cache_data decorators
- Ensure results/ and data/presets/ directories created if missing
- All buttons always visible (disabled during execution, never hidden)
- LSG categories computed from existing MFE/trade data — no new data collection
- Coin characteristics computed once per coin, cached
```

---

## VERIFICATION CHECKLIST

- [ ] dashboard_v3.py created (v2 untouched)
- [ ] backtester_v384.py has new metrics (trade logic untouched)
- [ ] 6 tabs visible on load
- [ ] Tab 1: Edge Quality panel shows all new metrics for RIVERUSDT
- [ ] Tab 1: LSG flag shows ⚠️ when LSG% > 90%
- [ ] Tab 2: Start sweep → progress bar updates → switch tab → switch back → resume works
- [ ] Tab 2: Completed sweep sorted by Calmar (not net PnL)
- [ ] Tab 2: Filters work (min trades, max DD%, grade)
- [ ] Tab 2: Export CSV has all columns including start_date, end_date, calmar, peak_capital
- [ ] Tab 5: Shows portfolio-level metrics from sweep CSV
- [ ] Tabs 3/4/6: Show placeholder descriptions
- [ ] Status banner shows sweep progress from any tab
- [ ] No Streamlit deprecation warnings
- [ ] No Arrow serialization errors
- [ ] Buttons never disappear, only disable

---

## DEPENDENCIES

| Dependency | Status | Needed For |
|-----------|--------|-----------|
| dashboard_v2.py | ✅ exists | Base for v3 |
| backtester_v384.py | ✅ exists | Add metrics |
| optimizer/grid_search.py | ✅ exists | Tab 3 (future) |
| ml/ modules (9 files) | ✅ exist | Tab 3/4 (future) |
| results/ directory | create if missing | Sweep CSV storage |

---

---

## CODE DEBT FIXES (from v1/v2 review — MANDATORY in v3)

Source: `DASHBOARD-V3-SUGGESTIONS.md`

### CD-1: Extract render_detail_view() — CRITICAL

v1 lines 1354-1499 duplicate the 5-tab rendering from single mode (lines 532-1111). ~400 lines of copy-paste. v3 MUST extract into `render_detail_view(results, symbol)` called from both:
- Tab 1 single coin results
- Tab 2 sweep drill-down (click a row → see full analysis)

This also enables ML tabs in sweep drill-down (currently gated, see CD-3).

### CD-2: Sweep Error Tracking

v1 line 1307 has `except Exception: pass` — failed coins silently vanish. Fix:
- `error_count` counter displayed in sweep progress UI
- Failed symbols logged to `logs/dashboard.log` with traceback
- `status` column in sweep CSV: `"ok"` or `"error: {reason}"`
- Summary shows "X coins failed" with expandable error list

### CD-3: Enable ML Tabs in Sweep Detail

v1 lines 1494-1498 gate ML tabs with `st.info("available in single-coin mode")`. Once render_detail_view() is extracted, remove the gate. All 5 analysis tabs available in sweep drill-down.

### CD-4: Use safe_plotly_chart() Consistently

v2 defines wrapper at line 69-75 but never calls it. v3: replace ALL `st.plotly_chart()` calls with `safe_plotly_chart()`. Or remove the wrapper if not needed.

### CD-5: Preserve Normalizer/Upload Flow

v1 lines 1181-1262 (~80 lines) handle Upload Data: detect_format preview, symbol input, convert button. Must migrate intact to Tab 2 sweep source options.

---

## COIN CHARACTERISTICS — FEATURE ENGINEERING FOR VINCE

**Problem:** The sweep shows WHICH coins performed well, but not WHY. VINCE needs to learn what characteristics predict a good trading coin so it can identify future candidates — not just backtest historical winners.

**Principle:** VINCE must NEVER see backtest results during training. Characteristics are inputs. Results are labels. Training set and test set must be completely separate coin pools (no data leakage).

### Characteristics to Compute Per Coin (from OHLCV data only):

| Feature | Calculation | Why It Matters |
|---------|-------------|----------------|
| avg_daily_volume | mean(daily quote volume) | Liquidity — can we fill orders? |
| volume_stability | std(daily_vol) / mean(daily_vol) | Erratic volume = slippage risk |
| avg_spread_proxy | mean((high-low)/close) per bar | Tighter spread = better fills |
| volatility_regime | std(returns) annualized | Strategy needs volatility to profit |
| trend_strength | abs(close[-1] - close[0]) / std(close) | Trending vs ranging |
| mean_reversion_score | autocorrelation of returns at lag 1 | Negative = mean-reverting |
| volume_mcap_ratio | avg_volume / market_cap (if available) | High ratio = active trading interest |
| bar_count | total bars in dataset | Data sufficiency |
| gap_pct | (bars with volume=0) / total bars | Dead zones = illiquid |
| price_range | (max_price - min_price) / min_price | How much the coin moved overall |

### Where This Goes:

**Tab 2 (Discovery):** Add "Coin Profile" expandable section per row showing these characteristics alongside backtest results. User can visually correlate "high volume coins tend to have better Calmar."

**Tab 3 (Optimizer / VINCE):** When VINCE trains:
1. Pool A (training): random 60% of coins — VINCE sees characteristics + results
2. Pool B (validation): random 20% — VINCE predicts, then checks
3. Pool C (holdout): remaining 20% — never touched until final evaluation
4. VINCE learns: "coins with volatility_regime > X and volume_stability < Y tend to have Calmar > Z"
5. Output: VINCE can score NEW coins (not in the 400) on likelihood of edge

**Sweep CSV addition (append these columns):**
```
avg_daily_volume, volume_stability, avg_spread_proxy,
volatility_regime, trend_strength, mean_reversion_score,
bar_count, gap_pct, price_range
```

(volume_mcap_ratio requires external API for market cap — flag as future/optional)

---

## LSG REDUCTION STRATEGY

**Problem:** LSG (Losers Saw Green) at 90-96% means almost every losing trade was profitable at some point before reversing to a loss. The rebate model absorbs this, but reducing LSG directly increases net PnL.

**Principle:** Do NOT reduce LSG by filtering out trades or reducing volume. The goal is MORE WINS from the SAME number of trades. Rebate revenue depends on volume.

### Root Causes of High LSG:

1. **BE raise too slow** — trade goes green, but BE isn't activated fast enough, price reverses
2. **No intermediate exit** — trade hits TP zone but no partial close, full reversal to SL
3. **Entry timing** — entering mid-move instead of at pullback, giving less room for the trade to work
4. **Exit rigidity** — fixed ATR-based SL/TP doesn't adapt to volatility changes during the trade

### What VINCE Should Analyze (Tab 3, when built):

For every LSG loser, compute:
- `max_favorable_excursion` — how far into profit did it go?
- `time_in_green` — how many bars was it profitable?
- `green_to_loss_speed` — how fast did it reverse? (bars from peak to SL)
- `be_raise_delay` — how many bars between entry and BE activation?
- `was_scale_out_possible` — did MFE exceed a partial-close threshold?

VINCE can then cluster LSG losers into fixable categories:
- **Category A: Fast reversals** (green < 3 bars) → entry timing problem → tighten entry conditions
- **Category B: Slow bleed** (green > 10 bars, gradual decline) → trail not tight enough → adaptive trail
- **Category C: Almost TP** (MFE > 80% of TP) → TP too wide → lower TP or add scale-out at 70% TP
- **Category D: BE should have saved it** (MFE > BE threshold but BE not raised) → BE logic bug or delay

### Dashboard Display (Tab 1, Edge Quality Panel):

Add LSG breakdown:
```
LSG: 94.4% ⚠️
  Category A (fast reversal): 31%
  Category B (slow bleed):    28%
  Category C (near-TP miss):  22%  
  Category D (BE failure):    19%
  Avg MFE of losers: $47.20
  Avg time in green: 8.3 bars
```

This turns LSG from a scary number into an actionable diagnosis.

### Entry-State Logging — THE LABELING LAYER

**Why:** LSG categories (A/B/C/D) explain HOW the trade died. But the real question is: what made some green trades WIN and others LOSE? The answer is in the indicator state at entry.

**Principle:** The backtester must log the Four Pillars indicator state at the moment of every entry. This is VINCE's training data. Without it, ML has nothing to learn from.

**Per-trade entry state to log:**

| Field | What | Why |
|-------|------|-----|
| entry_ripster_cloud | which cloud pair (2/3/4), price distance from cloud edge | was price deep in cloud or at edge? |
| entry_ripster_expanding | bool: cloud width increasing? | expanding = strong trend |
| entry_stoch9_value | K value 0-100 | already overbought at entry? |
| entry_stoch9_direction | rising/falling/flat | momentum direction |
| entry_stoch14_value | K value 0-100 | confirmation strength |
| entry_stoch40_value | K value 0-100 | divergence state |
| entry_stoch60_value | K value 0-100 | macro trend |
| entry_stoch60_d | D-smooth value | macro signal line |
| entry_bbwp_value | BBWP 0-100 | squeeze or expansion? |
| entry_bbwp_spectrum | blue/red/neutral | volatility regime |
| entry_avwap_distance | (price - avwap) / avwap × 100 | % away from anchor — overextended? |
| entry_atr | ATR value at entry bar | volatility context |
| entry_vol_ratio | volume / SMA(volume, 20) | above or below average volume |
| entry_grade | A/B/C/D/R | how many pillars aligned |

**Storage:** NOT in the sweep CSV (that's per-coin summary). Two storage layers:

**Layer 1: Per-trade summary** — `results/trades_{symbol}_{timeframe}.parquet`
- One row per trade
- Columns: all existing trade fields + entry state fields + trade lifecycle summary fields (below)
- This is VINCE's primary training dataset

**Layer 2: Per-bar trade journal** — `results/bars_{symbol}_{timeframe}.parquet`
- One row per bar per open trade (only bars where a position is open)
- Compact format: trade_id, bar_index, timestamp, unrealized_pnl, mfe_so_far, mae_so_far, stoch9, stoch14, stoch40, stoch60, stoch60_d, ripster_cloud_width, ripster_expanding, bbwp, avwap_distance, atr, vol_ratio
- This is VINCE's deep analysis dataset — for sequence modeling, pattern detection during trade lifecycle
- Size estimate: avg 15 bars/trade × 7K trades/coin × 400 coins × 17 columns = ~630M rows. At ~100 bytes/row compressed parquet = ~60GB total. Per-coin files ~150MB.
- **Mitigation:** Only generate on demand (sweep flag `--save-bars`), not by default. Or: store only summary stats per trade (see lifecycle summary below).

**Trade Lifecycle Summary (stored in Layer 1, one row per trade):**

Instead of storing every bar (expensive), compute summary stats of indicator behavior during the trade:

| Field | What | Why |
|-------|------|-----|
| life_bars | total bars trade was open | trade duration |
| life_stoch9_min | lowest stoch9 during trade | did momentum bottom out? |
| life_stoch9_max | highest stoch9 during trade | did it get overbought? |
| life_stoch9_trend | slope (linear regression of stoch9 over trade life) | rising/falling/flat momentum |
| life_stoch9_crossed_signal | bool: did K cross D during trade? | signal change mid-trade |
| life_ripster_flip | bool: did cloud color flip during trade? | trend reversal |
| life_ripster_width_change | (cloud_width_exit - cloud_width_entry) / cloud_width_entry | expanding or contracting |
| life_bbwp_delta | bbwp_exit - bbwp_entry | volatility regime shift |
| life_avwap_max_dist | max distance from AVWAP during trade | how far did it extend? |
| life_avwap_end_dist | AVWAP distance at exit bar | where did it close relative to anchor? |
| life_vol_avg | mean(vol_ratio) during trade | sustained volume or fade? |
| life_vol_trend | slope of volume ratio over trade life | increasing or decreasing interest |
| life_mfe_bar | bar number where MFE occurred | early peak (bad) vs late peak (good) |
| life_mae_bar | bar number where MAE occurred | when was max pain? |
| life_pnl_path | "direct" / "green_then_red" / "red_then_green" / "choppy" | P&L trajectory shape |

This gives VINCE 15 lifecycle features per trade without storing every bar. Combined with the 14 entry-state fields = 29 indicator features per trade. Across 2.8M trades, this is VINCE's complete training dataset.

**Dashboard display: P&L path classification**
```
Trade Lifecycle Patterns:
  Direct winners (entry → steady profit → TP):    34%
  Green-then-red (LSG — saw profit, reversed):      41%
  Red-then-green (held through DD, recovered):       12%
  Choppy (multiple crosses of entry price):          13%

  Avg bars to MFE: 8.2 (winners) vs 4.1 (losers)
  Ripster flipped during trade: 11% (winners) vs 38% (losers)
  Stoch9 crossed signal during trade: 23% (winners) vs 67% (losers)
```

**Dashboard display (Tab 1, new sub-section):**

LSG Comparison Panel — split LSG trades into winners vs losers:
```
                        Winners (went green → stayed)    LSG Losers (went green → reversed)
Avg Stoch 9 at entry:   34.2                             67.8
Avg AVWAP distance:     0.3%                             1.2%
Avg Vol Ratio:          1.8x                             0.9x
Ripster expanding:      78%                              41%
BBWP < 50 (squeeze):    82%                              53%
```

This instantly shows: winners entered with lower stoch (room to run), closer to AVWAP (not overextended), higher volume (conviction), expanding clouds (trend strength), and during squeeze (about to expand).

**VINCE's job (Tab 3, future):** Take this per-trade data across 400 coins and find the decision boundary. Which combination of entry states predicts winner vs LSG loser? Output = entry filter that rejects trades likely to become LSG losers WITHOUT reducing overall trade count (because better entries replace filtered ones).

**Critical design decision:** VINCE trains on a random 60% of coins. The other 40% is blind holdout. VINCE never sees their results. This prevents VINCE from memorizing coin-specific patterns.

### ML Architecture — Unified PyTorch Model

**Decision:** One model, one framework, one truth. No XGBoost + PyTorch split.

**Why unified:**
- Two models can disagree → needs arbitration layer → more complexity, more failure points
- Separate models see partial data (XGBoost sees entry snapshot, LSTM sees sequences). A unified model sees the FULL picture: entry conditions + indicator evolution + trade lifecycle in a single forward pass.
- One training pipeline, one deployment path, one endpoint for n8n live integration.
- One set of gradients, one loss function, one optimization target.

**Architecture: VINCE Unified Model (PyTorch)**

```
INPUT LAYER
├── Tabular branch: entry-state features (14 fields)
│   → Embedding layer for categoricals (grade, bbwp_spectrum)
│   → Linear layers for numerics (stoch values, AVWAP dist, ATR, vol_ratio)
│   → Output: 64-dim entry representation
│
├── Sequence branch: per-bar indicator evolution (Layer 2 data)
│   → Input: [bars × 17 features] per trade
│   → LSTM or Transformer encoder
│   → Output: 64-dim lifecycle representation
│
├── Context branch: coin characteristics (10 fields)
│   → Linear layers
│   → Output: 32-dim coin context
│
FUSION LAYER
│   → Concatenate: [entry_repr | lifecycle_repr | coin_context] = 160-dim
│   → Dense layers with dropout
│
OUTPUT LAYER
│   → Primary: win probability (0-1)
│   → Secondary: predicted P&L path (direct/green_then_red/red_then_green/choppy)
│   → Tertiary: optimal exit bar estimate
```

**Training data:**
- Per-trade parquet (Layer 1): entry features + lifecycle summary → tabular branch + labels
- Per-bar parquet (Layer 2, on-demand): indicator sequences → sequence branch
- Sweep CSV coin characteristics → context branch

**Hardware:** RTX 3060 12GB, PyTorch 2.10.0+cu130, CUDA available.

**Phased build:**
1. Phase 1 (tabular only): Train on entry features + lifecycle summary. No sequences. Validates data pipeline and feature signal. Fast to train (minutes).
2. Phase 2 (+ sequences): Add LSTM branch consuming per-bar data. Learns indicator evolution patterns. Slower to train but captures what XGBoost never could.
3. Phase 3 (+ live): Model runs on live trades via n8n webhook. Entry features scored at signal time. Sequence branch updates per bar while trade is open. Adaptive exit signal.

**XGBoost role:** Validation/auditor model. Trains on the same data, same features, independently. NOT a production model — it never makes live decisions.

Purpose:
- Cross-validate feature importance: if PyTorch (via Captum) and XGBoost (via SHAP) agree on which features matter, confidence is high
- Flag disagreements: if PyTorch says "AVWAP distance is #1" but XGBoost says "irrelevant", something is wrong — investigate before deploying either
- Baseline comparison: XGBoost accuracy on tabular features sets the floor. PyTorch with sequences should beat it. If it doesn't, the sequence data isn't adding value.
- Runs overnight alongside PyTorch training. Training speed difference is irrelevant.

**Interpretability stack:**
- PyTorch: Captum for feature attribution + attention weights (if Transformer)
- XGBoost: SHAP waterfall plots — native, fast, visual
- Dashboard Tab 3 (future): side-by-side comparison panel showing both models' feature rankings
- Agreement score: % of top-10 features that appear in both models' top-10
- If agreement < 70%, flag for manual review before any deployment

### Sweep Table Addition:

Add to sweep CSV (per-coin aggregates, not per-trade):
```
lsg_cat_a_pct, lsg_cat_b_pct, lsg_cat_c_pct, lsg_cat_d_pct,
avg_loser_mfe, avg_loser_green_bars,
avg_winner_entry_stoch9, avg_lsg_entry_stoch9,
avg_winner_avwap_dist, avg_lsg_avwap_dist,
winner_ripster_expanding_pct, lsg_ripster_expanding_pct
```

These aggregated comparisons give a quick read on entry quality differences between winners and LSG losers at the coin level. Full per-trade detail is in the parquet files.

---

## ADDITIONAL FEATURES (from suggestions review)

### SHOULD (include in v3 build):

**S-1: Date Range Filter**
Two `st.sidebar.date_input()` widgets. Filter cached data before passing to backtest. 5 lines of code, high user value — test "last 30 days" vs "last 6 months" without modifying cache.

**S-2: Param Presets (Save/Load)**
"Save Preset" → `data/presets/{name}.json`. "Load Preset" dropdown. Ship 3 defaults:
- "Rebate Farm" (tight SL/TP, max cooldown, volume priority)
- "Conservative" (wide SL, no scale-out)
- "Aggressive" (tight SL, TP=2.0, fast BE)

**S-3: Sweep Stop Button**
```python
if st.button("Stop Sweep"):
    st.session_state["sweep_stop"] = True
# In loop:
if st.session_state.get("sweep_stop"):
    break  # remaining coins stay for resume
```

### NICE (v4 candidates, not in v3 build):

- Sweep A/B comparison (load two CSVs, show delta per coin)
- Top N equity curve overlay (multi-trace plotly)
- Commission sensitivity row ("if rebate drops to 50%: Net = $X")
- Timeframe per tab (independent TF selection for single vs sweep)

---

## UPDATED SWEEP CSV COLUMNS (final)

```
# Identity
symbol, start_date, end_date, calendar_days, bar_count,

# Performance
trades, wr_pct, expectancy, net_pnl, profit_factor, grade,

# Risk-adjusted
sharpe, sortino, calmar,

# Drawdown
max_dd_pct, max_dd_amt, peak_capital, capital_efficiency,

# Trade quality
max_single_win, max_single_loss, avg_winner, avg_loser, wl_ratio,
max_win_streak, max_loss_streak,

# LSG analysis
lsg_pct, lsg_bars_avg, lsg_cat_a_pct, lsg_cat_b_pct, 
lsg_cat_c_pct, lsg_cat_d_pct, avg_loser_mfe, avg_loser_green_bars,

# Entry-state comparison (winners vs LSG losers, per-coin aggregates)
avg_winner_entry_stoch9, avg_lsg_entry_stoch9,
avg_winner_avwap_dist, avg_lsg_avwap_dist,
winner_ripster_expanding_pct, lsg_ripster_expanding_pct,

# Exits
tp_exits, sl_exits, be_exits, scale_outs,

# Volume & rebate
volume, rebate, net_after_rebate,

# Coin characteristics (for VINCE feature engineering)
avg_daily_volume, volume_stability, avg_spread_proxy,
volatility_regime, trend_strength, mean_reversion_score, gap_pct, price_range,

# Meta
status, timestamp
```

Total: ~51 columns. Still <250KB for 400 coins.

---

## RISKS

| Risk | Mitigation |
|------|-----------|
| Backtester metric changes break existing tests | Only ADD new keys to dict, never modify existing |
| Calmar = 0 for coins with no drawdown | Handle: if max_dd == 0, calmar = float('inf'), display "∞" |
| Sweep CSV grows large | 400 rows × 51 columns = ~250KB, negligible |
| Sidebar too long with 6 tabs | Sidebar is global, stays fixed — tabs only change main area |
| Streamlit reruns kill sweep | Disk persistence — CSV is truth, not session_state |
| LSG categorization adds compute time | Categories computed from existing MFE data — minimal overhead |
| Coin characteristics require extra calculation | Computed once from OHLCV before backtest — cached per coin |
| Volume/mcap ratio needs external API | Flagged as optional — omit from v3, add when API available |
| Per-trade parquet files large (2.8M trades) | Write per-coin files, not one giant file. ~400 files × ~7K trades avg = manageable |
| Entry-state logging slows backtester | Indicator values already computed — just snapshot at entry bar, minimal overhead |
