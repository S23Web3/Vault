# Plan: Enrich Dash Skill with Trading Dashboard Knowledge

**Date:** 2026-02-28
**Scope:** Add trading-dashboard-specific knowledge sections to the Dash skill file.
**User intent:** "not in detail, in knowledge" — high-level conceptual coverage, short illustrative snippets only. No bloated code blocks.

---

## File to modify

`C:\Users\User\.claude\skills\dash\SKILL.md`

---

## What the skill currently covers (1,064 lines)

- Part 1: Architecture, callback graph, multi-page structure, Vince store hierarchy
- Part 2: Components, callbacks, pattern-matching, dcc.Store, background callbacks,
  Plotly figures (histogram, line, bar, heatmap), ag-grid, ML serving, PostgreSQL,
  gunicorn, performance, checklists, known bugs

## What's missing for trading dashboard knowledge

The skill has zero knowledge of:
1. Candlestick / OHLCV chart (`go.Candlestick`) — the #1 trading chart type
2. Real-time / live data patterns (`dcc.Interval`, background thread → Store)
3. Common trading dashboard panel taxonomy (what panels a trading UI typically has)
4. Equity curve and drawdown visualization patterns
5. Multi-chart synchronization (`relayoutData` linked zoom/crosshair)
6. Conditional cell coloring in ag-grid (green/red P&L, status badges)
7. Timezone-aware trading data handling in Plotly
8. Order book / depth chart visualization
9. Rolling metrics display (Sharpe, win rate % over time)
10. Alert/status indicator patterns (blinking, color-coded state pills)

---

## New section to add: PART 3 — TRADING DASHBOARD KNOWLEDGE

Add after the existing Part 2 (after line ~1054, before Version History).

### Subsections (knowledge-dense, concise — no large code walls):

#### 1. Candlestick Charts (go.Candlestick)
- `go.Candlestick` — OHLC input, standard trading chart
- Adding volume bars as secondary y-axis (`go.Bar`, `secondary_y=True`)
- Overlaying indicator traces (EMAs, BBands) as `go.Scatter` on same figure
- Rangeslider: disable for live charts (`xaxis_rangeslider_visible=False`)
- Key layout: `xaxis_type='category'` to skip market gaps (weekends/holidays)

#### 2. Trading Dashboard Panel Taxonomy
- The common panels in a production trading dashboard and what they contain:
  - Live price feed panel (candlestick + current price ticker)
  - Open positions panel (ag-grid with real-time P&L)
  - Equity curve panel (go.Scatter, cumulative PnL line)
  - Drawdown panel (go.Scatter area chart, negative shading)
  - Trade log panel (ag-grid, filterable, conditional color row)
  - Risk metrics scorecard (win rate, Sharpe, max DD, expectancy)
  - Signal/alert feed (timestamped log with color-coded severity)
  - Multi-timeframe charts (1m, 5m, 1h synchronized)

#### 3. Real-time Data Patterns
- `dcc.Interval` + callback polling store: the simplest live update pattern
- Background thread pushing to a shared `queue.Queue` + store: for WebSocket feeds
- WebSocket (e.g. BingX) → Python thread → `cache.set(live_key, data)` → `dcc.Interval` reads cache
- Rate: 1000ms for live P&L, 5000ms for equity curve refresh, 30000ms for scorecard
- Key trap: `dcc.Interval` fires on all connected clients — use `State` to gate updates

#### 4. Equity Curve & Drawdown Charts
- Equity curve: `go.Scatter(mode='lines')`, cumulative sum of net PnL over time
- Drawdown: `go.Scatter(fill='tonexty', fillcolor=RED_TRANSPARENT)` below zero
- Rolling win rate: `go.Scatter` with a 20-trade rolling mean
- Sharpe/Sortino display: `html.Div` scorecard cards, not charts (single numbers)

#### 5. Multi-Chart Synchronization (relayoutData)
- Linked zoom: callback reads `relayoutData` from one chart, applies `xaxis.range` to others
- `relayoutData` fires on every zoom/pan — use `State` on sibling charts to avoid loops
- Crosshair sync: clientside callback + `hoverData` for zero-latency cross-panel cursor

#### 6. Conditional Formatting in ag-grid
- Cell style functions (JS): color P&L cells green/red based on value
- Row class rules: highlight open positions, flag alerts
- Status badge pattern: `cellRenderer` for pill-shaped outcome labels (WIN/LOSS/BE)

#### 7. Timezone-Aware Data in Plotly
- Always store timestamps as UTC in the database
- Convert to local/exchange time only in the figure factory, not in callbacks
- Plotly's `xaxis_tickformat` and `xaxis_tickformatstops` for readable datetime axes
- Trap: mixing tz-aware and tz-naive Timestamps in pandas → silent NaT or crash

#### 8. Order Book / Depth Chart (optional, knowledge only)
- Horizontal bar chart: bids left (green), asks right (red), price center
- Update via `dcc.Interval` at ~500ms — use `extendData` not full figure replace for performance
- `go.Figure.update_traces` with `extendData` pattern is faster than rebuilding the figure

---

## Update metadata

- Bump Version History: v1.1 — 2026-02-28
- Update description frontmatter to include trading dashboard keywords:
  `candlestick, equity curve, drawdown, real-time, dcc.Interval, live data, order book`

---

## Vault copy

Also write identical copy to:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-02-28-dash-skill-trading-dashboard-enrichment.md`

---

## Verification

- Read the updated SKILL.md and confirm all 8 subsections are present
- Confirm version history updated to v1.1
- Confirm frontmatter description includes new keywords
- Confirm no existing sections were modified or deleted
