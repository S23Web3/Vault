# Dashboard v3 Capital Usage Metrics + Aesthetic Layout

**Date:** 2026-03-10
**Context:** User wants capital usage metrics (avg capital used, recommended wallet size, daily volume perspective) added to the 55/89 dashboard v3. Current layout uses plain `st.metric()` in 4 rows. User wants aesthetically appealing layout.

---

## What Changes

Modify `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_55_89_v3.py`

### 1. Add styled HTML metric cards (CSS injection)

Replace plain `st.metric()` calls with styled HTML cards using `st.markdown()` with custom CSS. Cards will have:

- Dark card background (#1a1f26) with subtle border
- Color-coded values (green for positive, red for negative, blue for neutral)
- Compact label above, large value below
- Grouped into logical sections with section headers

### 2. Reorganize metrics into 4 logical groups

**Group A: Performance** (Row 1 -- 6 cols)

- Trades, Win Rate, Net PnL, Profit Factor, Sharpe, Max DD

**Group B: Trade Economics** (Row 2 -- 4 cols)

- Avg Win, Avg Loss, Expectancy, Commission

**Group C: Volume & Rebates** (Row 3 -- 5 cols)

- Volume $, Daily Volume, Rebate $, Net w/Rebate, LSG%

**Group D: Capital Usage** (Row 4 -- NEW -- 5 cols)

- Avg Capital Used, Peak Capital Used, % Time Flat, Capital Efficiency (ROI), Recommended Wallet

### 3. New metrics computed from existing engine data

The engine already returns these (no engine changes needed):

- `avg_margin_used` -- average margin deployed across all bars
- `peak_margin_used` -- max margin deployed at any point
- `pct_time_flat` -- % of bars with no position open
- `avg_positions` -- avg concurrent positions

New derived metrics:

- **Daily Volume** = total_volume / trading_days (trading_days from date_range or bar count / 1440)
- **Capital Efficiency** = net_pnl / avg_margin_used (ROI on deployed capital)
- **Recommended Wallet** = peak_margin_used * 1.5 (safety buffer for drawdown + margin)

### 4. Apply to both single-coin and portfolio views

Both `render_single_results()` (line 543+) and `render_portfolio_results()` (line 703+) get the same treatment:

- Same card styling
- Same 4-group layout
- Portfolio aggregates capital metrics across coins

---

## Key Files

| File | Action |
|------|--------|
| `scripts/dashboard_55_89_v3.py` | MODIFY -- add CSS, replace metrics rows, add capital group |
| `engine/backtester_55_89.py` | READ ONLY -- already has avg_margin_used, peak_margin_used, pct_time_flat |

---

## Implementation Steps

### Step 1: Add CSS helper function + metric card renderer

- `inject_card_css()` -- one-time CSS injection via `st.markdown(unsafe_allow_html=True)`
- `metric_card(label, value, color="text")` -- returns HTML string for a styled card

### Step 2: Add `compute_capital_metrics()` helper

- Takes metrics dict + date_range, returns dict with daily_volume, capital_efficiency, recommended_wallet

### Step 3: Update `render_single_results()` (lines 557-584)

- Replace `st.metric()` calls with `st.markdown(metric_card(...), unsafe_allow_html=True)` in `st.columns()` blocks
- Add Row 4: Capital Usage group with new metrics
- Add "Daily Volume" to Row 3 (replace or add alongside Volume $)

### Step 4: Update `render_portfolio_results()` (lines 762-790)

- Same card treatment as single mode
- Aggregate avg_margin_used and peak_margin_used across coins (sum for portfolio)
- Add Row 4: Capital Usage group

### Step 5: py_compile validation

---

## Verification

1. `py_compile` passes on modified dashboard_55_89_v3.py
2. User runs `streamlit run scripts/dashboard_55_89_v3.py`
3. Check: styled cards render in dark theme, colors correct
4. Check: Capital Usage row shows avg/peak margin, efficiency, recommended wallet
5. Check: Daily Volume metric shows sensible $/day figure
6. Check: Portfolio mode aggregates capital metrics correctly
