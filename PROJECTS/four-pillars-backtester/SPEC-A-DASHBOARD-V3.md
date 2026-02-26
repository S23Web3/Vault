# SPEC A: Dashboard v3 -- VINCE Control Panel

**Version:** v3
**Date:** 2026-02-13
**Base:** `scripts/dashboard_v2.py` (1534 lines)
**Output:** `scripts/dashboard_v3.py`
**Depends on:** Nothing (works with v384 backtester as-is)
**Review:** `DASHBOARD-V3-BUILD-SPEC-REVIEW.md`
**Related:** SPEC-B (Backtester v385), SPEC-C (VINCE ML)

---

## PHILOSOPHY

The dashboard is VINCE's control panel. It is not a backtest viewer.

Every screen must answer a question VINCE needs to make a trading decision:
- **Can I trade this coin?** -- Single Coin analysis
- **Which coins have edge?** -- Discovery sweep
- **What params work best?** -- Optimizer
- **Is the edge real?** -- Validation
- **How much capital do I need?** -- Portfolio risk
- **Go live?** -- Deploy

If a metric doesn't help answer one of these questions, it doesn't belong on the dashboard.

---

## ARCHITECTURE

### Tab Structure (st.tabs -- 6 tabs, TEXT ONLY, no emojis)

```
+------+----------+----------+----------+--------+--------+
|Single|Discovery |Optimizer |Validation|Capital |Deploy  |
| Coin |  Sweep   | (VINCE)  |  (WFE)   | & Risk |        |
+------+----------+----------+----------+--------+--------+
```

Each tab feeds the next. Outputs from tab N are inputs to tab N+1.

### Global Sidebar (always visible, all tabs)

Current sidebar params stay -- symbol, timeframe, stoch K values, Ripster EMAs, SL/TP/CD, commission, rebate, ML params. These are the "strategy config" shared across all tabs.

### Persistent Status Banner (above tabs)

Reads from disk (not session_state). Shows:
- Sweep in progress: `[Sweep: AGIUSDT 24/400 -- 6%]`
- Sweep complete: `[Sweep complete: 400 coins]`
- Backtest running: `[Running: RIVERUSDT...]`
- Idle: collapsed/hidden

---

## TAB 1: SINGLE COIN

**Question answered:** "Can I trade this coin with these params?"

### Existing (keep as-is from v2):
- Run Backtest button
- Equity curve
- Trade log
- 5 sub-tabs: Overview, Trade Analysis, MFE/MAE, ML Meta-Label, Validation
- Back to Settings button

### Add -- Edge Quality Panel (inside Overview sub-tab):

```
+-- Edge Quality -----------------------------------------+
| Expectancy: $20.27    Stability: +/-$3.12 (sigma)       |
| Avg Win: $47.80       Avg Loss: -$28.90                 |
| W/L Ratio: 1.65       Best: +$312    Worst: -$89        |
| Max Streak: 8W / 12L  LSG: 94.4% [HIGH REVERSION]      |
| Capital Eff: 172%     Peak Capital: $30,000              |
+----------------------------------------------------------+
```

Metrics read from backtester results dict using `.get()` with defaults:

| Metric | Key | Default | Location |
|--------|-----|---------|----------|
| Peak Capital | `peak_capital` | 0 | Overview header |
| Capital Efficiency | `capital_efficiency` | 0 | Overview header |
| Max Single Win $ | `max_single_win` | 0 | Overview header |
| Max Single Loss $ | `max_single_loss` | 0 | Overview header |
| Avg Winner $ | `avg_winner` | 0 | Overview header |
| Avg Loser $ | `avg_loser` | 0 | Overview header |
| Win/Loss Ratio | `wl_ratio` | 0 | Overview header |
| Max Win Streak | `max_win_streak` | 0 | Trade Analysis |
| Max Loss Streak | `max_loss_streak` | 0 | Trade Analysis |
| Expectancy Stability | computed | 0 | Trade Analysis chart |
| LSG Flag | `lsg_pct` | 0 | Overview, red text if > 90% |

**Graceful fallback:** All new metrics use `results.get("key", default)`. Dashboard v3 works with v384 backtester (shows 0 or N/A for missing metrics). When v385 lands, metrics auto-populate.

---

## TAB 2: DISCOVERY SWEEP

**Question answered:** "Which coins from my universe have edge?"

### Sweep Persistence (disk-based):
- Results file: `results/sweep_v3_{timeframe}_{params_hash}.csv`
- Write after EVERY coin (append mode)
- On tab load: read CSV -- determine state (not started / in progress / complete)
- Resume: skip symbols already in CSV
- New Sweep: delete CSV, start fresh

### Sweep Controls:
- Source: All Cache | Custom List (.txt/.csv) | Upload Data
- Start / Resume / Stop buttons (always visible, disabled during execution, never hidden)
- Progress bar + current coin name + ETA

### Sweep CSV Columns (~30 columns, user-facing only):

```
# Identity
symbol, start_date, end_date, calendar_days,

# Performance
trades, wr_pct, expectancy, net_pnl, profit_factor, grade,

# Risk-adjusted
sharpe, sortino, calmar,

# Drawdown
max_dd_pct, max_dd_amt, peak_capital, capital_efficiency,

# Trade quality
max_single_win, max_single_loss, avg_winner, avg_loser, wl_ratio,
max_win_streak, max_loss_streak,

# LSG
lsg_pct, lsg_bars_avg,

# Exits
tp_exits, sl_exits, be_exits, scale_outs,

# Volume & rebate
volume, rebate, net_after_rebate,

# Meta
status, timestamp
```

Total: ~33 columns. Coin characteristics, entry-state comparisons, and LSG categorization are NOT in this CSV -- they belong to SPEC-B/C outputs.

### Results Display (after sweep complete or partial):

**Summary Row:**
```
Coins: 400 | Profitable: 388 (97%) | Total Trades: 2,878,011
Total Net: $11.77M | Total Rebate: $X | Total Volume: $X
```

**Results Table -- DEFAULT SORT: Calmar ratio (not net PnL)**

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
- LSG% max: [slider, default 95]

**Charts:**
- Top/Bottom 20 by Calmar (horizontal bar)
- Scatter: Net PnL vs Max DD% (bubble size = trades)
- Grade distribution pie

**Export:**
- CSV download (full results)
- "Send to Optimizer" button -- passes filtered coin list to Tab 3

---

## TAB 3: OPTIMIZER (VINCE) -- PLACEHOLDER

**Question answered:** "What are the optimal params per coin?"

**Input:** Filtered coin list from Tab 2 (or manual selection)

**When built (uses existing `optimizer/grid_search.py` -- needs coin list from Tab 2):**
- Grid search across param ranges per coin
- Cooldown: [1, 2, 3, 5]
- SL multiplier: [2.0, 2.5, 3.0, 3.5]
- TP multiplier: [2.0, 2.5, 3.0]
- BE raise: [2, 3, 4, 5]
- Best param combo by Calmar
- Heatmap: param sensitivity
- Overfitting risk flag

**v3 display:** Placeholder page with description of what it will do, "Coming Soon" message, and note that it needs optimized configs from Tab 2 sweep.

---

## TAB 4: VALIDATION (WFE) -- PLACEHOLDER

**Question answered:** "Is the edge real or overfit?"

**When built (depends on Tab 3):**
- Walk-Forward Efficiency (WFE): train 70%, test 30%
- Monte Carlo: randomize entry order 1000x
- Out-of-sample: hold out last month if >6 months data
- Confidence grade: HIGH / MEDIUM / LOW / REJECT

**v3 display:** Placeholder page with description.

---

## TAB 5: CAPITAL & RISK

**Question answered:** "How much money do I need and what's my risk?"

**Input:** Completed sweep CSV from Tab 2.

### Portfolio Metrics (calculated from sweep CSV):
| Metric | Calculation |
|--------|------------|
| Total Coins | count of coins passing filters |
| Total Trades | sum of trades across all coins |
| Total Net PnL | sum across all coins |
| Sum of Peak Capitals | worst-case concurrent capital |
| Portfolio Capital Efficiency | total_net / sum_peak_capitals |
| Average Calmar | mean(calmar) across coins |
| Worst Calmar | min(calmar) |
| Total Rebate | sum(rebate) |

### Risk Scenarios:
- **Base case:** validated params, historical data
- **Worst case:** all coins hit max DD simultaneously
- **Conservative:** only top-10 Calmar coins, 50% position size

### Charts:
- Capital utilization across coins (bar chart)
- Calmar distribution (histogram)

Show as clean metric cards using st.metric().

**Note:** Full portfolio simulation (correlated equity curves, concurrent position tracking) is a later phase. v3 uses aggregate stats from sweep CSV.

---

## TAB 6: DEPLOY -- PLACEHOLDER

**Question answered:** "Ready for live?"

**When built:**
- Per-coin JSON config for n8n webhooks
- Exchange API setup checklist
- Position size calculator
- Paper trade mode toggle
- Export all configs as ZIP

**v3 display:** Placeholder page with description.

---

## CODE DEBT FIXES (MANDATORY in v3)

### CD-1: Extract render_detail_view() -- CRITICAL

v2 lines 1443-1533 duplicate the 5-tab rendering from single mode (lines 623-1147). ~90 lines of copy-paste in sweep_detail vs ~524 lines in single mode. Extract into `render_detail_view(results, symbol)` called from both:
- Tab 1 single coin results
- Tab 2 sweep drill-down (click a row -- see full analysis)

### CD-2: Sweep Error Tracking

v2 line 1342 has `except Exception: pass`. Fix:
- `error_count` counter displayed in sweep progress UI
- Failed symbols logged to `logs/dashboard.log` with traceback
- `status` column in sweep CSV: `"ok"` or `"error: {reason}"`
- Summary shows "X coins failed" with expandable error list

### CD-3: Enable ML Tabs in Sweep Detail

v2 lines 1529-1533 gate ML tabs with `st.info("available in single-coin mode")`. Once render_detail_view() is extracted, remove the gate. All 5 analysis tabs available in sweep drill-down.

### CD-4: Use safe_plotly_chart() Consistently

v2 defines wrapper at line 69-75 but never calls it. Replace ALL `st.plotly_chart()` calls with `safe_plotly_chart()`. Or remove the wrapper if not needed.

### CD-5: Preserve Normalizer/Upload Flow

v2 lines 1181-1262 (~80 lines) handle Upload Data: detect_format preview, symbol input, convert button. Must migrate intact to Tab 2 sweep source options.

---

## ADDITIONAL FEATURES (SHOULD -- include in v3)

### S-1: Date Range Filter

Two `st.sidebar.date_input()` widgets. Filter cached data before passing to backtest. 5 lines of code, high user value -- test "last 30 days" vs "last 6 months" without modifying cache.

### S-2: Param Presets (Save/Load)

"Save Preset" -- `data/presets/{name}.json`. "Load Preset" dropdown. Ship 3 defaults:
- "Rebate Farm" (tight SL/TP, max cooldown, volume priority)
- "Conservative" (wide SL, no scale-out)
- "Aggressive" (tight SL, TP=2.0, fast BE)

### S-3: Sweep Stop Button

```python
if st.button("Stop Sweep"):
    st.session_state["sweep_stop"] = True
# In loop:
if st.session_state.get("sweep_stop"):
    break  # remaining coins stay for resume
```

---

## WHAT TO BUILD IN V3 (SCOPE SUMMARY)

### BUILD NOW:
1. Tab structure with st.tabs() -- all 6 tabs visible, TEXT labels only
2. Tab 1 (Single Coin): Edge Quality panel reading metrics via `.get()` with defaults
3. Tab 2 (Discovery): full rebuild -- disk persistence, resume, ~33 col CSV, filters, Calmar sort, charts, export
4. Tab 5 (Capital): basic portfolio metrics from sweep CSV
5. Persistent status banner reading from disk
6. Button visibility fixes (always visible, disabled during execution)
7. State namespace isolation per tab (single_*, sweep_*, portfolio_*)
8. Code debt fixes CD-1 through CD-5
9. S-1 date range filter, S-2 param presets, S-3 sweep stop button

### PLACEHOLDER (show description, not functional):
- Tab 3 (Optimizer) -- depends on VINCE ML orchestration
- Tab 4 (Validation) -- depends on Tab 3
- Tab 6 (Deploy) -- depends on Tab 4

### NOT IN SCOPE (moved to Spec B/C):
- Backtester engine changes (stays at v384)
- Entry-state logging
- Trade lifecycle logging
- LSG categorization
- Coin characteristics
- ML architecture
- Per-trade/per-bar parquet storage

---

## IMPLEMENTATION SEQUENCE

```
Step 1:  Read dashboard_v2.py fully
Step 2:  Backup dashboard_v2.py -- dashboard_v2_backup.py
Step 3:  Create dashboard_v3.py from v2 base
Step 4:  Restructure into st.tabs() -- 6 tabs, TEXT labels
Step 5:  Isolate session_state namespaces (single_*, sweep_*, portfolio_*)
Step 6:  Tab 1: add Edge Quality panel with .get() fallbacks
Step 7:  Tab 2: rebuild sweep with disk persistence, new columns, filters, charts
Step 8:  Tab 5: basic portfolio metrics from sweep CSV
Step 9:  Tabs 3/4/6: placeholder pages with descriptions
Step 10: Add persistent status banner above tabs
Step 11: Fix button visibility (always visible, disabled during execution)
Step 12: Code debt: extract render_detail_view()
Step 13: Code debt: sweep error tracking
Step 14: Code debt: enable ML tabs in sweep detail
Step 15: Code debt: use safe_plotly_chart() consistently
Step 16: Code debt: preserve normalizer/upload flow
Step 17: S-1 date range filter
Step 18: S-2 param presets
Step 19: S-3 sweep stop button
Step 20: Test single coin RIVERUSDT -- verify Edge Quality panel
Step 21: Test sweep start -- switch tab -- switch back -- verify resume
Step 22: Test sweep complete -- verify filters, Calmar sort, charts
Step 23: Test export CSV -- verify all ~33 columns present
```

---

## VERIFICATION CHECKLIST

- [ ] dashboard_v3.py created (v2 untouched)
- [ ] 6 tabs visible on load, TEXT labels only, zero emojis
- [ ] Tab 1: Edge Quality panel shows metrics (0/N/A if v384 backtester)
- [ ] Tab 1: LSG flag shows [HIGH REVERSION] text when LSG% > 90%
- [ ] Tab 2: Start sweep -- progress bar updates -- switch tab -- switch back -- resume works
- [ ] Tab 2: Completed sweep sorted by Calmar (not net PnL)
- [ ] Tab 2: Filters work (min trades, max DD%, grade)
- [ ] Tab 2: Export CSV has all ~33 columns
- [ ] Tab 5: Shows portfolio-level metrics from sweep CSV
- [ ] Tabs 3/4/6: Show placeholder descriptions
- [ ] Status banner shows sweep progress from any tab
- [ ] No Streamlit deprecation warnings
- [ ] No Arrow serialization errors
- [ ] Buttons never disappear, only disable
- [ ] render_detail_view() extracted, no code duplication
- [ ] Sweep errors logged, not silenced
- [ ] safe_plotly_chart() used for all plotly calls
- [ ] Normalizer/upload flow preserved in Tab 2
- [ ] Date range filter works in sidebar
- [ ] Param presets save/load works
- [ ] Sweep stop button breaks loop, resume picks up

---

## CONSTRAINTS

- Create NEW file dashboard_v3.py -- do NOT overwrite v2
- Do NOT change backtester_v384.py (that is Spec B scope)
- Keep ALL existing sidebar parameters exactly as they are
- Keep existing st.cache_data decorators
- Ensure results/ and data/presets/ directories created if missing
- All buttons always visible (disabled during execution, never hidden)
- Zero emojis anywhere -- tab names, status banners, comments, output

---

## DEPENDENCIES

| Dependency | Status | Needed For |
|-----------|--------|-----------|
| dashboard_v2.py | EXISTS | Base for v3 |
| backtester_v384.py | EXISTS | Runs backtests (unchanged) |
| results/ directory | Create if missing | Sweep CSV storage |
| data/presets/ directory | Create if missing | Param presets |
| Spec B (v385 metrics) | NOT YET BUILT | Edge Quality panel auto-populates when available |
| Spec C (VINCE ML) | NOT YET BUILT | Tabs 3/4 become functional when available |

---

## RISKS

| Risk | Mitigation |
|------|-----------|
| New metrics not available from v384 | `.get("key", 0)` with defaults everywhere |
| Calmar = 0 for coins with no drawdown | if max_dd == 0, display "INF" |
| Sweep CSV grows large | 400 rows x 33 columns = ~150KB, negligible |
| Sidebar too long with 6 tabs | Sidebar is global, stays fixed -- tabs only change main area |
| Streamlit reruns kill sweep | Disk persistence -- CSV is truth, not session_state |
