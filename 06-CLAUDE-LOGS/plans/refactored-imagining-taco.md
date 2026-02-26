# Dashboard Portfolio Enhancement Plan
## Reusable Portfolios + PDF Export + Per-Coin Analysis + Unified Capital Model

**Date:** 2026-02-16
**Project:** Four Pillars Trading System v3.8.4
**Scope:** Dashboard portfolio mode enhancements (4 features)

---

## Context

User identified 4 critical gaps in the current portfolio analysis dashboard:

1. **No reusable portfolio selections** — Random N coin selections cannot be saved/reloaded
2. **No PDF export** — Cannot present portfolio results professionally
3. **Insufficient per-coin analysis** — Only 7 metrics shown, no drill-down capability
4. **Misleading capital model** — Current model: each coin gets independent $10k pool (money sits idle). Need unified portfolio capital pool with utilization tracking.

Current architecture (from `scripts/dashboard.py`):
- Portfolio aggregation: `align_portfolio_equity()` function (line 327-373)
- Per-coin backtest: Sequential runs via `Backtester384` engine
- Capital model: Position count × margin per position (currently $500 default)
- Exports: Sweep CSV only (no portfolio export)
- Coin selection: Top N, Lowest N, Random N, Custom multiselect (not saved)

**Critical architectural constraint discovered:**
The backtester is NOT a unified portfolio engine. It's a **single-coin bottoms-up aggregator**:
- Each coin runs independently with full capital allocation
- Portfolio results = sum of aligned equity curves
- No cross-coin capital sharing or correlation-based position sizing
- Capital utilization = sum of concurrent positions × margin per position

This design choice impacts Feature 4 (unified capital model) implementation complexity.

---

## Current Implementation Analysis

### Capital Model (Current State)

**How it works now:**
```python
# dashboard.py line 349
capital_allocated = total_positions * margin_per_pos
```

- `margin_per_pos` = $500 (default, configurable)
- `total_positions` = sum of active positions across ALL coins at time T
- Each position (any coin) consumes exactly $500 margin

**Example with 3 coins:**
```
Time T=100:
  RIVER: 2 active positions
  KITE:  1 active position
  HYPE:  0 active positions

  Total positions = 3
  Capital allocated = 3 × $500 = $1,500
```

**What this means:**
- NOT "$10k per coin independent pools"
- It's a **unified position counter** already
- Capital utilization is tracked (line 1822: `capital_allocated.max()`)

**User's concern:**
"Money sits idle" — This is TRUE if:
- User allocates $10k total to portfolio
- Max concurrent positions = 6 (3 coins × 2 avg)
- Max capital used = 6 × $500 = $3,000
- Idle capital = $10k - $3k = $7k (70% unused)

**Root cause:** The engine doesn't have a "total portfolio capital" input. It just reports how much capital was used, but doesn't constrain entries based on available capital.

---

### Per-Coin Analysis (Current State)

**Metrics shown (line 1843-1857):**
1. Symbol
2. Trades (count)
3. WR% (win rate)
4. Net (P&L dollars)
5. LSG% (loser saw green %)
6. DD% (max drawdown %)
7. Sharpe
8. PF (profit factor)

**What's missing:**
- Individual equity curves per coin (only shown as thin aggregate lines)
- Trade-by-trade log per coin
- Entry/exit reason breakdown (SL vs TP vs scale-out %)
- Grade distribution (A/B/C/D/ADD/RE/R counts)
- MFE/MAE statistics
- Loser classification (which losers saw green, by how much)
- Commission vs rebate breakdown
- Risk metrics (Sortino, Calmar, max consecutive losses)

---

### Portfolio Selection (Current State)

**How selections work:**
- **Top N / Lowest N:** Deterministic from `SWEEP_PROGRESS.csv` (saved)
- **Random N:** Uses `random.sample()` — NOT SAVED, changes each run
- **Custom:** `st.multiselect()` — NOT SAVED, resets on page refresh

**No persistence mechanism:**
- No "Save Portfolio Template" button
- No "Load Previous Portfolio" option
- No portfolio naming/tagging
- No portfolio comparison feature

---

### Export Functionality (Current State)

**Sweep mode only:**
- CSV download: `sweep_v384.csv` (line 1564)
- Contains: All sweep results with metrics

**Portfolio mode: NO EXPORTS**
- No CSV button
- No PDF generation capability
- Results only viewable in Streamlit UI
- No equity curve image export
- No correlation matrix export

---

## Design Solutions

### Feature 1: Reusable Portfolio Selections

**Solution: Portfolio Templates with JSON Persistence**

**Storage format:**
```json
{
  "name": "Low Cap Momentum",
  "created": "2026-02-16T14:32:00",
  "coins": ["RIVERUSDT", "KITEUSDT", "HYPEUSDT"],
  "selection_method": "custom",
  "params_hash": "a3f9c2...",
  "notes": "Top 3 performers from Feb 14 sweep"
}
```

**File location:**
```
C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\portfolios\
  ├─ low_cap_momentum.json
  ├─ high_sharpe_basket.json
  └─ random_20_20260216.json  (auto-saved random selections)
```

**UI Changes (dashboard.py):**
1. **Save Portfolio button** (after coin selection, before backtest)
   - Input: Portfolio name (text input)
   - Action: Save to JSON with timestamp
   - Auto-save Random N selections with date suffix

2. **Load Portfolio dropdown** (above coin selection)
   - Lists all `.json` files in `portfolios/` directory
   - On select: Load coins, display metadata (created date, notes)
   - Button: "Rerun This Portfolio"

3. **Portfolio Manager section** (new sidebar tab)
   - List all saved portfolios
   - Actions: Rename, Delete, Duplicate, Add Notes
   - Compare: Select 2 portfolios → side-by-side metrics

**Implementation files:**
- New module: `utils/portfolio_manager.py` (save/load/list/delete functions)
- Dashboard changes: Lines 1737-1800 (portfolio selection section)

---

### Feature 2: PDF Export

**Solution: Multi-Page PDF Report with Charts**

**Library:** `reportlab` (programmatic generation) + `matplotlib` for chart embedding

**Report structure:**
```
Page 1: Executive Summary
  - Portfolio name, date range, total coins
  - Net P&L, Win Rate, Sharpe, Max DD
  - Best/Worst coin performers (top 3 each)
  - Capital utilization summary (peak, average, % idle)

Page 2: Portfolio Performance
  - Equity curve chart (PNG embedded)
  - Capital allocation over time chart
  - Drawdown curve

Page 3: Per-Coin Summary Table
  - All 7 current metrics + new metrics (see Feature 3)
  - Sortable by Net P&L

Page 4+: Per-Coin Detail Pages (1 page per coin)
  - Equity curve
  - Trade breakdown (SL/TP/Scale-out counts)
  - Grade distribution bar chart
  - MFE/MAE box plots
  - Top 5 best/worst trades table

Page N: Correlation Matrix
  - Equity change correlation heatmap
  - Diversification score

Page N+1: Risk Analysis
  - VaR (Value at Risk) estimates
  - Tail risk metrics
  - Consecutive loss statistics
```

**Export button placement:**
- Portfolio results section (line 1860, after equity curve display)
- Button: "Export Portfolio Report as PDF"
- Filename: `portfolio_report_{name}_{date}.pdf`
- Save location: `results/pdf_reports/`

**Implementation files:**
- New module: `utils/pdf_exporter.py` (report generation logic)
- Dependencies: `reportlab`, `matplotlib`, `PIL` (for chart embedding)
- Dashboard changes: Line ~1900 (add export button after charts)

---

### Feature 3: Enhanced Per-Coin Analysis

**Solution: Drill-Down Modal + Expanded Metrics Table**

**Expanded metrics table (add 10 columns):**
| New Column | Calculation | Purpose |
|------------|-------------|---------|
| Avg Trade | Net / Trades | Expectancy per trade |
| Best Trade | Max single trade P&L | Outlier detection |
| Worst Trade | Min single trade P&L | Risk assessment |
| SL% | SL exits / Total trades | Stop-out frequency |
| TP% | TP exits / Total trades | Target hit frequency |
| Scale% | Scale exits / Total trades | Partial exit frequency |
| Avg MFE | Mean(MFE) across trades | Profit potential |
| Avg MAE | Mean(MAE) across trades | Risk exposure |
| Max Consec Loss | Longest loss streak | Psychological risk |
| Sortino | Downside deviation Sharpe | Risk-adjusted return |

**Drill-down modal (Streamlit expander per coin):**
```python
with st.expander(f"📊 {symbol} Detailed Analysis"):
    # Tab 1: Trades
    st.dataframe(trades_df)  # All trade details

    # Tab 2: Equity Curve
    fig = plot_coin_equity_curve(equity, datetime_index)
    st.pyplot(fig)

    # Tab 3: Trade Distribution
    - Grade breakdown (A/B/C/D/ADD/RE/R counts) as bar chart
    - Entry reason breakdown (stoch cross, cloud flip, etc.)
    - Exit reason breakdown (SL/TP/Scale/BE/End)

    # Tab 4: MFE/MAE Analysis
    - Scatter plot: MFE vs MAE per trade
    - Box plots: MFE and MAE distributions
    - Loser detail: Which losers saw green, by how much

    # Tab 5: Risk Metrics
    - Drawdown curve for this coin
    - Consecutive loss histogram
    - Commission vs Rebate breakdown
    - Monthly P&L distribution
```

**Implementation:**
- Dashboard changes: Lines 1843-1900 (table section)
- New helper functions in dashboard.py:
  - `render_coin_drilldown(coin_result, symbol)`
  - `plot_coin_equity_curve(equity, dt)`
  - `plot_mfe_mae_scatter(trades_df)`
  - `compute_extended_metrics(trades_df)`

---

### Feature 4: Unified Capital Model with Utilization Tracking

**Two-Mode Toggle Solution**

**Mode A: Per-Coin Independent (Current Behavior)**
- Each coin gets full `margin_per_pos` allocation
- No cross-coin capital constraints
- Good for: Single-coin optimization, max performance potential

**Mode B: Unified Portfolio Capital (New Feature)**
- User inputs: `total_portfolio_capital` (e.g., $10,000)
- Engine tracks: `capital_remaining` at each bar
- Entry constraint: Only open position if `capital_remaining >= margin_per_pos`
- Capital release: When position closes, capital returns to pool
- Risk check: Flag if strategy requires more capital than available

**UI Changes:**

```python
# Sidebar (line ~570)
capital_mode = st.radio(
    "Capital Allocation Mode",
    ["Per-Coin Independent", "Unified Portfolio Pool"]
)

if capital_mode == "Unified Portfolio Pool":
    total_portfolio_capital = st.number_input(
        "Total Portfolio Capital ($)",
        min_value=1000,
        max_value=100000,
        value=10000,
        step=1000
    )

    # Show estimated peak capital needed (from sweep data)
    st.info(f"⚠ Estimated peak capital needed: ${estimated_peak}")
    if estimated_peak > total_portfolio_capital:
        st.warning("Strategy may miss trades due to insufficient capital")
```

**Implementation approaches:**

**Approach 1: Post-Processing Filter (Recommended)**
- Run backtests normally (per-coin independent)
- Post-process aligned results to filter out trades that would exceed capital
- **Pro:** No engine changes, dashboard-only logic
- **Con:** Not truly realistic (entry order matters, first-come-first-serve bias)

**Approach 2: Pre-Sort Entry Priority (More Realistic)**
- Sort potential entries by signal strength (grade A > B > C, stoch value, etc.)
- Allocate capital to highest-priority entries first
- **Pro:** More realistic capital allocation
- **Con:** Requires access to signal strengths at each bar

**Approach 3: True Portfolio Engine (Most Complex)**
- Refactor `Backtester384` to accept multi-coin input
- Track global capital pool inside engine
- **Pro:** Fully accurate simulation
- **Con:** Major architectural change (weeks of work)

**Recommended: Approach 1 (Post-Processing Filter)**
Rationale:
- Fast to implement (dashboard-only changes)
- User can toggle between modes to see impact
- "Close enough" for capital planning (conservative estimate)
- Avoids multi-week engine refactor

**Output changes:**
1. **Capital Utilization Chart** (enhance existing, line 1879)
   - Add horizontal line: `total_portfolio_capital` (if unified mode)
   - Color zones: Green (<80% used), Yellow (80-95%), Red (>95%)
   - Show: Rejected trade count due to capital constraints

2. **New Metrics Section: "Capital Efficiency"**
   ```
   Total Capital:        $10,000
   Peak Capital Used:    $7,200 (72%)
   Avg Capital Used:     $4,500 (45%)
   Idle Capital (avg):   $5,500 (55%)
   Trades Rejected:      14 (8% of total signals)
   ```

3. **Risk Alert:**
   - If `peak_required > total_capital * 0.95`: Show warning
   - Suggest: "Consider increasing capital to $X or reducing position size"

**Implementation files:**
- Dashboard changes: Lines 327-373 (`align_portfolio_equity` function)
- New function: `apply_capital_constraints(aligned_results, total_capital, margin_per_pos)`
- Dashboard UI: Lines 570 (sidebar), 1820-1840 (capital metrics section)

---

## Implementation Plan

### Phase 1: Reusable Portfolios (Simplest, High Impact)
**Estimated: 1 build script, ~200 lines**

Files to create:
- `utils/portfolio_manager.py` (save/load/list/delete)
- `portfolios/` directory (JSON storage)

Files to modify:
- `scripts/dashboard.py` lines 1737-1800 (add save/load UI)

Tests:
- Save portfolio → reload → verify coin list matches
- Auto-save random selections
- Delete portfolio → verify file removed

---

### Phase 2: Enhanced Per-Coin Analysis (Medium, Foundation for PDF)
**Estimated: 1 build script, ~300 lines**

Files to modify:
- `scripts/dashboard.py` lines 1843-1900 (expand table, add drill-down)

New functions:
- `compute_extended_metrics(trades_df)` → dict with 10 new metrics
- `render_coin_drilldown(coin_result, symbol)` → Streamlit expander with tabs
- `plot_coin_equity_curve(equity, dt)` → matplotlib figure
- `plot_mfe_mae_scatter(trades_df)` → matplotlib figure

Tests:
- Run portfolio backtest → verify 17 columns in table
- Open drill-down → verify all 5 tabs render
- Check edge case: coin with 0 trades

---

### Phase 3: PDF Export (Complex, Depends on Phase 2)
**Estimated: 1 build script, ~400 lines**

Files to create:
- `utils/pdf_exporter.py` (report generation logic)

Dependencies to install:
- `reportlab` (PDF generation)
- Already have: `matplotlib` (chart generation)

Files to modify:
- `scripts/dashboard.py` line ~1900 (add export button)

Functions needed:
- `generate_portfolio_pdf(portfolio_data, output_path)`
- `embed_matplotlib_chart(fig, pdf_canvas)`
- `render_summary_page(pdf, metrics)`
- `render_coin_detail_page(pdf, coin_result)`

Tests:
- Generate PDF → open in reader → verify all pages render
- Check: Charts embedded correctly
- Check: Multi-coin portfolio (10 coins) → correct page count

---

### Phase 4: Unified Capital Model (Most Complex, Optional)
**Estimated: 1 build script, ~350 lines**

Files to modify:
- `scripts/dashboard.py` lines 327-373 (`align_portfolio_equity`)
- `scripts/dashboard.py` lines 570 (sidebar toggle)
- `scripts/dashboard.py` lines 1820-1840 (capital metrics)

New function:
- `apply_capital_constraints(aligned_results, total_capital, margin_per_pos, mode)`

Tests:
- Run with $5k capital → verify some trades rejected
- Run with $50k capital → verify all trades allowed
- Compare: Independent vs Unified mode → verify P&L difference
- Check: Capital release on exit → verify capital_used decreases

---

## Verification Plan

### End-to-End Test Scenario

**Setup:**
1. Load 5 coins: RIVER, KITE, HYPE, SAND, 1000PEPE
2. Run portfolio backtest (both capital modes)
3. Save portfolio as "Test Portfolio"
4. Export PDF report

**Verify:**
- [ ] Portfolio saved to `portfolios/test_portfolio.json`
- [ ] Reload portfolio → same 5 coins loaded
- [ ] Table shows 17 columns (7 original + 10 new)
- [ ] Drill-down expander works for each coin
- [ ] PDF generated at `results/pdf_reports/portfolio_report_test_portfolio_20260216.pdf`
- [ ] PDF contains: summary + 5 coin detail pages + correlation page
- [ ] Unified capital mode: Shows rejected trade count > 0 (if constrained)
- [ ] Unified capital mode: Chart shows capital limit line
- [ ] Independent mode: No trade rejections

---

## Files to Create/Modify

### New Files (3)
1. `utils/portfolio_manager.py` (~150 lines)
2. `utils/pdf_exporter.py` (~400 lines)
3. `portfolios/` directory (JSON storage)

### Modified Files (1)
1. `scripts/dashboard.py` (~500 lines of changes across 4 sections)
   - Lines 570: Capital mode toggle
   - Lines 327-373: Capital constraints logic
   - Lines 1737-1800: Portfolio save/load UI
   - Lines 1843-1900: Enhanced table + drill-down
   - Line ~1900: PDF export button

### Dependencies to Install
```bash
pip install reportlab
```
(matplotlib, pandas, numpy already installed)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PDF generation fails on large portfolios | Medium | Medium | Paginate per-coin details, limit to 20 coins |
| Capital constraint logic breaks equity alignment | Medium | High | Unit tests on synthetic data, compare with independent mode |
| Portfolio JSON corruption | Low | Low | Validate JSON schema on load, backup on save |
| Drill-down modal slows dashboard | Medium | Low | Lazy-load charts (only render on expander open) |
| User confusion: two capital modes | Medium | Medium | Clear tooltips, default to Independent mode |

---

## Open Questions for User

Before finalizing implementation, need clarification on:

1. **Capital Mode Default:**
   - Should "Unified Portfolio Pool" be the default, or keep "Per-Coin Independent" as default?
   - Reasoning: Independent mode matches current behavior (backward compatible)

2. **Entry Priority in Unified Mode:**
   - How should we prioritize trades when capital is limited?
   - Options:
     - A) Grade-based: A > B > C > D
     - B) Signal strength: Higher stoch_k value first
     - C) First-come-first-serve: Bar entry order
   - Recommendation: **Grade-based** (aligns with strategy philosophy)

3. **PDF Detail Level:**
   - Should every coin get a full detail page, or only top/bottom N?
   - Concern: 20-coin portfolio = 25+ page PDF
   - Recommendation: **Full detail for all**, with option to "Export Summary Only" (5 pages max)

4. **Rejected Trades Visibility:**
   - In unified capital mode, should we show which specific trades were rejected?
   - Options:
     - A) Just count (simpler)
     - B) Highlight in drill-down trade table with reason (more informative)
   - Recommendation: **Option B** (add "Status" column: "Executed" | "Rejected: Insufficient Capital")

5. **Portfolio Comparison Feature:**
   - Should we build a side-by-side comparison of 2 saved portfolios?
   - Use case: Compare "Low Cap" vs "High Sharpe" baskets
   - Recommendation: **Defer to Phase 5** (nice-to-have, not critical)

---

## Additional Request: Core Design Document

**Scope:** Dashboard-focused design document
**Version tracking:** Granular (v3.0 → v3.8.4 from existing version-history.md)
**Location:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\DASHBOARD-DESIGN.md`
**Structure:** Hybrid (current architecture + roadmap section for 4 planned features)

**Document outline:**
1. **Executive Summary** — Dashboard purpose, modes (settings/single/sweep/portfolio)
2. **Version History** — Granular changelog from v3.0 → v3.8.4 (sourced from `09-ARCHIVE/four-pillars-version-history.md`)
3. **Architecture Overview** — File structure, module dependencies, Streamlit app flow
4. **Functionality Reference:**
   - Settings Mode: Parameter configuration
   - Single Mode: One-coin backtest with drill-down
   - Sweep Mode: Multi-coin sequential sweep with CSV persistence
   - Portfolio Mode: Aggregated results, equity alignment, correlation analysis
5. **File Locations** — All dashboard-related files with line number references
6. **Capital Model** — Current per-position allocation vs planned unified pool
7. **Data Flow** — OHLCV → Signals → Backtester → Dashboard → UI rendering
8. **Export Capabilities** — Current (CSV) + planned (PDF)
9. **Future Enhancements (Roadmap)** — 4-phase plan summary with links to detailed implementation plan

**Build approach:**
- Extract version history from `09-ARCHIVE/four-pillars-version-history.md`
- Document current dashboard.py architecture (1897 lines)
- Map all function locations with line numbers
- Include capital model diagrams
- Reference this enhancement plan in roadmap section

This will be built as a separate deliverable AFTER the 4-feature enhancement plan is approved.

---

## Summary

**Two deliverables:**

### Deliverable 1: Dashboard Enhancements (This Plan)
**4 features, 4 phases, ~1250 lines of new code:**

| Feature | Complexity | Lines | Priority |
|---------|------------|-------|----------|
| Reusable Portfolios | Low | ~200 | HIGH (foundation) |
| Enhanced Per-Coin Analysis | Medium | ~300 | HIGH (for PDF) |
| PDF Export | High | ~400 | MEDIUM (presentation) |
| Unified Capital Model | High | ~350 | MEDIUM (optional realism) |

**Recommended order:** 1 → 2 → 3 → 4 (build foundational features first)

**Critical path:** Phases 1-2 enable Phase 3. Phase 4 is independent and optional.

**User decision needed:** Answer 5 open questions above before starting Phase 4.

### Deliverable 2: Dashboard Core Design Document
**After enhancement implementation, create:**
- `DASHBOARD-DESIGN.md` (~400 lines)
- Granular version history (v3.0 → v3.8.4+)
- Full functionality reference with file locations
- Architecture diagrams for capital model and data flow
- Roadmap section summarizing completed enhancements

This document will serve as the living reference for all future dashboard work.
