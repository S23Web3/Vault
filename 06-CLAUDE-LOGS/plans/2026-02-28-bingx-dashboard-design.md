# Plan: BingX Live Trading Dashboard

**Date:** 2026-02-28
**Plan file:** dynamic-bubbling-cray.md

---

## Context

The BingX connector is live with real money ($5 margin, 10x leverage, up to 8 positions, 47 coins). The bot has no visual interface — the only way to check positions is reading state.json or bot logs. The user wants a proper dashboard that shows bot health at a glance and gives structured position management visibility. No charts required. No interactive trading controls (no order buttons). A clean, readable Dash page that auto-refreshes.

Previous session planned a dashboard but it was done without asking what the user actually wanted. This plan presents the structure first.

---

## Data Sources

| Source | What it provides |
|--------|-----------------|
| `state.json` | open_positions dict, daily_pnl, daily_trades, halt_flag, session_start |
| `trades.csv` | All closed trades: symbol, direction, grade, entry/exit price, exit_reason, pnl_net, notional_usd, timestamps |
| `config.yaml` | Limits: max_positions=8, max_daily_trades=50, daily_loss_limit_usd=15.0, margin_usd=5, leverage=10 |
| BingX mark price API (optional) | Current mark price per symbol → unrealized PnL per position |

**Per-position fields available from state.json:**
symbol, direction, grade, entry_price, sl_price, tp_price, quantity, notional_usd, entry_time, order_id, atr_at_entry, be_raised

---

## Dashboard Layout (Single Page, No Charts)

### Section 1 — Bot Status Banner
Full-width bar at the top showing:
- **Status badge**: LIVE / DEMO / HALTED (color: green/blue/red)
- **Session start**: e.g. "Running since 14:32 UTC (3h 22m)"
- **Last refreshed**: timestamp
- **Halt flag**: shown only when True (red alert)

### Section 2 — Summary Cards (4 cards in a row)

| Card | Value | Color logic |
|------|-------|-------------|
| Daily P&L | $-3.42 | red if negative, green if positive |
| Open Positions | 3 / 8 | orange if ≥6, red if =8 |
| Daily Trades | 12 / 50 | yellow if ≥40, red if =50 |
| Risk Used | 23% of $15.00 | yellow ≥50%, red ≥80% |

### Section 3 — Open Positions (Position Management)
AG Grid table, one row per open position. This is the main value section.

**Columns:**
| Column | Source | Notes |
|--------|--------|-------|
| Symbol | state.json | e.g. VIRTUAL-USDT |
| Dir | state.json | LONG / SHORT (colored) |
| Grade | state.json | A/B (styled) |
| Entry Price | state.json | |
| SL Price | state.json | |
| BE Raised | state.json | Yes / No badge |
| Entry Time | state.json | formatted "HH:MM UTC" |
| Duration | computed | now - entry_time |
| ATR at Entry | state.json | |
| Dist to SL % | computed | abs(entry_price - sl_price) / entry_price * 100 |
| Notional USD | state.json | |
| Unreal PnL | mark price API | optional; shown if API keys present |

Sort: newest first by entry_time.
Row color: LONG = faint green row, SHORT = faint red row.

### Section 4 — Today's Performance (Stats row)
3 stat blocks side by side:
- **Win Rate**: X% (W/L today)
- **Avg Win**: $X.XX | **Avg Loss**: $X.XX
- **Exit Breakdown**: SL_HIT: N | TP_HIT: N | EXIT_UNKNOWN: N | SL_HIT_ASSUMED: N

Filtered to today's date from trades.csv.

### Section 5 — Closed Trades Table
AG Grid with all trades from trades.csv.
**Columns:** Timestamp, Symbol, Dir, Grade, Entry Price, Exit Price, Exit Reason, PnL Net (colored), Notional
Default filter: today. User can clear to see all history.
Sorted: newest first.

---

## Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Framework | Plotly Dash | Per project skill requirement |
| Port | 8051 | 8050 reserved for Vince |
| Refresh | dcc.Interval, 60s | Matches bot's position_check_sec |
| State read | Direct JSON read (not StateManager) | Dashboard is read-only; no lock needed |
| Mark prices | Optional BingX REST call via bingx_auth.py | Only if .env keys present; graceful skip |
| AG Grid | dash_ag_grid | Matches Vince patterns |
| Config read | Direct YAML read | No imports needed |

---

## File to Create

**`C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\dashboard.py`**
- Single new file, ~280 lines
- No existing files modified
- Dependencies: dash, dash-ag-grid, plotly, pandas, pyyaml (all likely installed)
- Run command: `cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector" && python dashboard.py`

---

## Verification

1. Run `py_compile` on dashboard.py — must pass before delivery
2. Start dashboard: `python dashboard.py` — open http://localhost:8051
3. Confirm Section 2 cards show correct values from state.json
4. Confirm position table shows all open positions
5. Confirm trades table loads trades.csv rows
6. Wait 60s — confirm auto-refresh fires (Last refreshed timestamp updates)
7. If API keys available: confirm unrealized PnL column populates

---

## Notes / Open Questions

- Mark price fetch: does the user want this? It requires an outbound API call from the dashboard process (same keys the bot uses). Risk: rate limits if refresh is too fast. Could be toggled off.
- AG Grid column widths: will size to content by default — can be tuned.
- "Position management" without interactivity = read-only view. If user later wants actions (manual close, SL adjust), that is a separate build requiring careful API integration and confirmations.
