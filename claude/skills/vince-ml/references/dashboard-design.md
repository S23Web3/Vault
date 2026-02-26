# Dashboard Design Standard

## Industry Consensus Layout (5 Tabs)

### Tab 1: Overview
- **KPI Cards** (top row, large): Net P&L, Total Trades, Win Rate, Profit Factor, Max DD, Sharpe
- **Equity Curve** (large, prominent) with drawdown overlay
- **Monthly/Daily Returns** heatmap or bar chart
- **Commission Summary** (critical for rebate farming)
- Coin leaderboard table (sortable by any metric)

### Tab 2: Trade Analysis
- Full trade table (sortable, filterable by coin/grade/direction/exit reason)
- P&L histogram (distribution of trade outcomes)
- Win/Loss by direction (Long vs Short breakdown)
- Win/Loss by grade (A/B/C/R)
- Win/Loss by exit reason (SL/TP/FLIP)
- Consecutive win/loss streak tracking
- Trade duration histogram

### Tab 3: MFE/MAE & LSG
- MAE vs P&L scatter (green=winners, red=losers)
- MFE vs P&L scatter (filtered to losers = LSG analysis)
- MFE histogram for losers (depth distribution)
- ETD distribution histogram
- Loser classification pie/bar (A/B/C/D categories)
- BE Trigger Optimization Surface: heatmap of trigger level vs net P&L impact
- Time-to-MFE histogram for losers

### Tab 4: Risk
- Rolling Sharpe/Sortino (30-trade window)
- Monte Carlo equity bands (95% CI)
- Drawdown periods table (top 10 worst, with duration)
- Max consecutive losses
- Value at Risk (VaR) / CVaR

### Tab 5: Optimization
- Optuna `plot_param_importances` (which params matter?)
- Optuna `plot_contour` (2D surface for top param pairs)
- Optuna `plot_parallel_coordinate` (multi-dimensional view)
- Best parameter table with metrics
- Walk-forward OOS equity curve
- WFE (Walk Forward Efficiency) per window

## Sidebar (Global Filters)
- Coin selector (multi-select)
- Direction filter (All / Long / Short)
- Grade filter (A / B / C / R)
- Date range
- BE raise level slider
- Commission rate input

## Streamlit Implementation Pattern
```python
st.set_page_config(page_title="VINCE", layout="wide")
# Dark theme CSS
# Sidebar filters
# st.tabs() for main navigation
# st.metric() for KPI cards with delta
# st.dataframe() for sortable trade tables
# st.plotly_chart() for interactive Plotly charts
# @st.cache_data for data loading
```

## Design Principles
- Progressive disclosure: summary first, details on demand
- Dark theme (match TradingView aesthetic)
- Max 2 levels of tabs (primary + sub-tabs like All/Long/Short)
- Interactive: filters affect all views
- KPI cards physically large at top
- Green/red color coding consistent throughout

## Comparable Platforms
- Freqtrade: Full backtest + hyperopt, Streamlit-compatible
- QuantConnect: 300K+ community, open-source LEAN engine
- 3Commas: SaaS, DCA/Grid bots, community strategy sharing
- NautilusTrader: Rust core, ultra-fast, professional-grade
- Backtrader: Python event-driven, aging but solid
- QuantStats: 50+ metrics library, HTML tearsheet generation
- VectorBT: Fast vectorized backtesting, Plotly integration
