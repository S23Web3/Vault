# Plan: Add ML Analysis Tabs to Dashboard

## Context
The dashboard (`scripts/dashboard.py`, 526 lines) has full parameter controls and backtest visualization but no ML integration. The ml/ modules (features, triple_barrier, meta_label, shap_analyzer, bet_sizing, loser_analysis, walk_forward, purged_cv) are all built and tested (8/8 pass). The dashboard design reference specifies a 5-tab layout. Currently the dashboard has no tabs -- it's a single view with test/single/batch modes.

## What Changes
Add `st.tabs()` to the single-backtest view with 5 tabs matching the design reference. The ML analysis runs on the already-computed backtest result -- no extra backtest needed.

## File to Modify
- `scripts/dashboard.py` (the only file)

## Approach
Restructure the single-backtest section (lines 303-466) into 5 tabs using `st.tabs()`:

**Tab 1: Overview** (existing content, reorganized)
- KPI cards (already exist, lines 329-344)
- Equity curve with peak overlay (already exists, lines 350-359)
- Grade breakdown (already exists, lines 392-400)
- Exit reasons (already exists, lines 402-407)
- BE/AVWAP comparison (already exists, lines 409-457)

**Tab 2: Trade Analysis** (existing content, reorganized)
- Full trade table (already exists, lines 460-465)
- P&L histogram (already exists, lines 378-389)
- Direction breakdown, grade breakdown bar charts, duration histogram

**Tab 3: MFE/MAE & Losers** (NEW -- uses ml/)
- MFE/MAE scatter (already exists, lines 363-376)
- `ml.loser_analysis.classify_losers()` -> loser class bar chart (W/A/B/C/D)
- `ml.loser_analysis.get_class_summary()` -> summary table
- `ml.loser_analysis.optimize_be_trigger()` -> BE optimization line chart
- `ml.loser_analysis.compute_etd()` -> ETD histogram

**Tab 4: ML Meta-Label** (NEW -- uses ml/)
- `ml.features.extract_trade_features()` -> feature extraction
- `ml.triple_barrier.label_trades()` -> label distribution bar chart
- `ml.meta_label.MetaLabelAnalyzer` -> train XGBoost, show accuracy
- `ml.shap_analyzer.ShapAnalyzer` -> SHAP global importance bar chart
- `ml.bet_sizing.binary_sizing()` -> filtered vs unfiltered comparison table
- ML threshold slider inline controls what gets filtered

**Tab 5: Validation** (NEW -- uses ml/)
- `ml.purged_cv.purged_kfold_split()` -> fold summary table
- `ml.walk_forward.generate_windows()` + train per window -> WFE per window bar chart
- WFE rating (ROBUST/MARGINAL/OVERFIT)

## Sidebar Addition
Add under existing "Commission" section:
- ML section header
- XGBoost estimators (default 200)
- XGBoost depth (default 4)
- ML threshold slider (0.0-1.0, default 0.5)

## Key Reuse
- All ml/ imports already tested and working
- `trades_df` and `df_sig` from the existing backtest flow feed directly into ml/
- Plotly + dark theme patterns already established in existing charts
- `COLORS` dict already defined

## Implementation Order
1. Add ML sidebar params (3 inputs)
2. Wrap existing single-backtest content in `st.tabs()`
3. Move existing content into Tab 1 (Overview) and Tab 2 (Trade Analysis)
4. Build Tab 3 (MFE/MAE & Losers) with ml.loser_analysis
5. Build Tab 4 (ML Meta-Label) with ml.features, triple_barrier, meta_label, shap, bet_sizing
6. Build Tab 5 (Validation) with ml.purged_cv, walk_forward

## Delivery
Per MEMORY rules (SCRIPT IS THE BUILD), this will be delivered as a single Write to `scripts/dashboard.py` -- the existing file gets replaced with the upgraded version. No separate build script needed because this is a single-file edit, not multi-file generation.

A test script `scripts/test_dashboard_ml.py` will verify all 5 tabs' data flows work without Streamlit (import + call the ml/ functions with synthetic data).

## Verification
```
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"; streamlit run scripts/dashboard.py
```
- Select RIVERUSDT 5m
- Verify all 5 tabs render without errors
- Tab 3 should show MFE/MAE scatter, loser class bar chart, BE optimization, ETD histogram
- Tab 4 should show XGBoost accuracy, SHAP bar chart, filtered comparison
- Tab 5 should show WFE ratings per window
