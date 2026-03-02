# Plan: bingx-live-dashboard-v1.py

**Date:** 2026-02-28

---

## What the user wants

3 tabs. Read-only monitoring. No buttons, no order actions.

---

## Tab 1 — Positions (open positions)

Source: `state.json` + BingX mark price API

Columns:
| Column | Source | Notes |
|--------|--------|-------|
| Symbol | state.json | |
| Direction | state.json | LONG / SHORT |
| Grade | state.json | A / B |
| Entry Price | state.json | |
| Stop Loss | state.json | sl_price |
| Take Profit | state.json | tp_price or "—" |
| BE Raised | state.json | be_raised → Yes / No |
| Unrealized PnL | mark price API | (mark - entry) * qty * sign |
| Duration | computed | now - entry_time |

Row color: green tint = LONG, red tint = SHORT.
Sorted newest first.

---

## Tab 2 — History (closed trades)

Source: `trades.csv`

Columns:
| Column | Source |
|--------|--------|
| Date/Time | timestamp |
| Symbol | symbol |
| Direction | direction |
| Grade | grade |
| Entry Price | entry_price |
| Exit Price | exit_price |
| Exit Reason | exit_reason |
| Net PnL | pnl_net (green / red) |
| Duration | timestamp - entry_time |

Sorted newest first. Default filter: today. Clearable to show all history.

Note: SL/TP prices are NOT in trades.csv — only exit_reason shows what triggered the close.

---

## Tab 3 — Coin Summary

Source: `trades.csv` grouped by symbol

Columns (computed from closed trades only):
| Column | How |
|--------|-----|
| Symbol | group key |
| Trades | count |
| Wins | pnl_net > 0 |
| Losses | pnl_net <= 0 |
| Win Rate % | wins / trades |
| Net PnL | sum(pnl_net) |
| Avg PnL | mean(pnl_net) |
| SL Hit % | count(exit_reason == SL_HIT) / trades |
| TP Hit % | count(exit_reason == TP_HIT) / trades |
| Unknown % | count(exit_reason == EXIT_UNKNOWN) / trades |
| Best Trade | max(pnl_net) |
| Worst Trade | min(pnl_net) |

Note: True LSG% (Losers Saw Green) requires MFE tick data which the bot does not persist.
The exit breakdown (SL%/TP%/Unknown%) is the equivalent view available from trades.csv.
Sorted by Net PnL descending.

---

## Technology: Streamlit

**Reason:** This is a read-only monitoring dashboard with 3 tabs, file-based data, and simple tables.
Dash would add 150+ lines of callback boilerplate for no benefit here.

| Streamlit | Dash |
|-----------|------|
| `st.tabs()` — built-in | dcc.Tabs + callbacks |
| `st.dataframe()` — built-in | dash_ag_grid setup |
| `time.sleep(60); st.rerun()` — 2 lines | dcc.Interval + callback wiring |
| ~150 lines total | ~300 lines total |

Streamlit is the right tool for a monitoring dashboard.

---

## File

**Name:** `bingx-live-dashboard-v1.py`
**Location:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1.py`
**Run:** `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1.py"`

No existing files modified.

---

## Data files read (read-only)

- `state.json` — open positions
- `trades.csv` — closed trade history
- `config.yaml` — limits (max_positions, daily_loss_limit_usd)
- `.env` — API key + secret for mark price fetch
- BingX public endpoint: `GET /openApi/swap/v2/quote/price?symbol=X-USDT`

---

## Verification

1. `py_compile` on the file — must pass
2. `streamlit run bingx-live-dashboard-v1.py` — opens in browser
3. Tab 1: positions table shows all entries from state.json with correct unrealized PnL sign
4. Tab 2: history table loads trades.csv, PnL colored correctly
5. Tab 3: coin summary totals match manual sum of trades.csv
6. Wait 60s — page auto-refreshes (Last updated timestamp changes)
