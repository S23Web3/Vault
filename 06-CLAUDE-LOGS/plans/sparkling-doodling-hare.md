# Plan: v384 Dashboard Preset + Yesterday's Log Review
Date: 2026-03-05

## Context

The live BingX bot runs `four_pillars_v384` with specific params that differ from the
backtester dashboard defaults. `require_stage2=True` and `rot_level=80` are not exposed
in the dashboard UI at all. The user wants to be able to launch the dashboard and have
it pre-configured to exactly match the live bot's signal logic — so backtest results
are comparable to live performance.

Additionally: check yesterday's log (2026-03-04-bot.log, 11,466 lines) for anything
missing from the session log, then create today's fresh session log entry.

---

## Part 1 — v384 Dashboard Preset

### What needs to happen

The backtester dashboard (`dashboard_v394.py`) reads all params from sidebar sliders at
runtime. Two live-bot params (`require_stage2`, `rot_level`) are completely absent from
the UI. The plan is to add a **"Load v384 Live Preset"** button to the dashboard sidebar
that sets all signal and backtest params to exactly match config.yaml.

### Files to modify

- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v394.py`

### Exact live bot params to encode as preset

| Param | Live value | Dashboard control |
|-------|-----------|-------------------|
| `cross_level` | 25 | Existing slider |
| `zone_level` | 30 | Existing slider |
| `atr_length` | 14 | Existing slider |
| `allow_b` | True | Existing checkbox |
| `allow_c` | False | Existing checkbox |
| `require_stage2` | True | NEW checkbox |
| `rot_level` | 80 | NEW slider (0-100) |
| `sl_mult` | 2.0 | Existing slider |
| `tp_mult` | None/disabled | Existing — set to 0 or unchecked |

### Implementation steps

1. **Add `require_stage2` checkbox** to signal logic section of sidebar
   - Label: "Require Stage 2"
   - Default: False (preserve existing behaviour)
   - Pass to `compute_signals()` as `require_stage2=...`

2. **Add `rot_level` slider** to signal logic section of sidebar
   - Range: 50-100, step 1, default 80
   - Pass to `compute_signals()` as `rot_level=...`

3. **Add "Load v384 Live Preset" button** at top of sidebar
   - On click: sets `st.session_state` keys for all signal + backtest params to live values
   - Causes sidebar controls to re-render with preset values
   - All existing sliders/checkboxes read from `st.session_state` so they update automatically

4. **Wire new params into `run_backtest()` call**
   - Wherever `sig_params` dict is assembled, add `require_stage2` and `rot_level`
   - `compute_signals()` already accepts both (confirmed: lines 60-61 of four_pillars.py)

5. **Build script**: `scripts/build_dashboard_v395.py`
   - Reads `dashboard_v394.py` as base
   - Applies patches via `safe_replace()`
   - Writes to `dashboard_v395.py`
   - Runs `py_compile` + `ast.parse` on output
   - Does NOT modify v394

### Coin list
Dashboard auto-discovers from `data/cache/*.parquet`. No change needed.
The 47 live coins must be cached before running the sweep — handled by existing data fetcher.

---

## Part 2 — Yesterday's Log Review + New Session Log

### Yesterday's log
File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\2026-03-04-bot.log`
953 KB, 11,466 lines

Scan for:
- ERROR/CRITICAL lines not captured in existing session log
- Position opens/closes after 21:40 (last known log entry)
- Whether orderId=? appeared on other BE raises (not just BOME)
- Whether RENDER-USDT was reconciled or closed

Append findings to:
`C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-04-bingx-dashboard-v1-4-patches.md`
(Edit tool only — append, never Write)

### Today's new log
Create: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-03-05-bingx-bot-session.md`

Contents:
- Fixes applied: be_act/ttp_act split, orderId fix x3, unrealized PnL in TG, max_positions=25
- Test: 25/25 PASS on three-stage logic test
- Config state: be_act=0.004, ttp_act=0.008, ttp_dist=0.003
- Pending: dashboard v1.5 be_act awareness, BE SL direction bug for SHORT

---

## Execution order

```
1. Scan yesterday's log -> append to 2026-03-04 session log
2. Create 2026-03-05 session log
3. Build dashboard_v395.py via build script
4. py_compile + ast.parse must pass
5. Run: streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v395.py"
```

## Files created / modified

| File | Action |
|------|--------|
| `PROJECTS/four-pillars-backtester/scripts/build_dashboard_v395.py` | CREATE |
| `PROJECTS/four-pillars-backtester/scripts/dashboard_v395.py` | CREATE (output of build) |
| `06-CLAUDE-LOGS/2026-03-04-bingx-dashboard-v1-4-patches.md` | APPEND (log review) |
| `06-CLAUDE-LOGS/2026-03-05-bingx-bot-session.md` | CREATE |

## Risk
Low. dashboard_v394.py untouched. v395 is new. Logs are append-only.

---
## SUPERSEDED CONTENT BELOW (previous session plan)

The live BingX bot has been running 12+ hours. Screenshots and log analysis reveal:
- TTP close orders failing (error 109400) causing infinite retry loops
- Close Market button broken (signature mismatch error 100001)
- Equity curve shows all historical sessions, not current session
- Coin summary date filter disconnected from analytics date filter
- EXIT_UNKNOWN exits not explained — TTP activating but failing to close
- No visibility into whether SL_HIT trades ever saw green (LSG gap)
- No per-trade TTP activation tracking in trades.csv
- Bot OFFLINE = position controls still needed but confusing UX
- Current v384 config ($5, 10x) underperforming vs backtester perspective → beta at $5 20x needed
- User wants: dynamic SL tightening after TTP activates (progressive trail), trade chart popup in v1.5, beta bot on a separate coin subset (user will specify coins)

---

## Confirmed Bugs (from code audit + logs)

| # | Bug | Root Cause | File | Location |
|---|-----|-----------|------|----------|
| BUG-1 | TTP/Close Market fails 109400 | `"reduceOnly": "true"` invalid in Hedge mode | position_monitor.py | `_place_market_close()` |
| BUG-1b | Same in dashboard | Same `reduceOnly` in 3 dashboard callbacks | bingx-live-dashboard-v1-4.py | CB-6, CB-7, CB-16 |
| BUG-4 | Close Market signature fails 100001 | `_sign()` missing `recvWindow` before HMAC | bingx-live-dashboard-v1-4.py | `_sign()` lines 191-197 |
| BUG-2 | Equity curve = drawdown shape | All sessions mixed, no session filter | bingx-live-dashboard-v1-4.py | `build_equity_figure()` + CB-9 |
| BUG-5 | Coin summary ignores analytics date | Separate radio filter, not wired to date range | bingx-live-dashboard-v1-4.py | CB-10 |
| BUG-5b | Coin detail doesn't reset on filter change | CB-15 doesn't listen to period filter | bingx-live-dashboard-v1-4.py | CB-15 |
| BUG-9 | TTP activation never recorded in trades.csv | `_append_trade()` doesn't write TTP fields | state_manager.py | `_append_trade()` lines 115-144 |

---

## Phase 1 — Diagnostic Scripts (read-only, no bot changes)

**Build script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_phase1_diagnostics.py`

Creates 4 scripts (all read-only):

### 1A — Error Audit
**Script:** `scripts\run_error_audit.py`
- Parses `logs\2026-03-03-bot.log` for ERROR/WARNING lines
- Categorizes: `TTP_CLOSE_FAIL` (109400), `AUTH_FAIL` (signature), `EXIT_DETECTION` (EXIT_UNKNOWN), `RECONCILE`, `WS_ERROR`, `OTHER`
- Counts occurrences, first/last timestamps per category
- Output: `logs\error_audit_2026-03-03.md` (markdown table)
- Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_error_audit.py"`

### 1B — Variable Web / Dependency Map
**Script:** `scripts\run_variable_web.py`
- Static AST analysis (no imports, pure file parsing)
- Traces data flow: config.yaml → signal_engine → executor → state.json → position_monitor → trades.csv → dashboard stores → callbacks
- Flags orphaned variables (written but never read) and dead-ends (read but never written)
- Output: `logs\variable_web.md` (Mermaid diagram + text audit)
- Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_variable_web.py"`

### 1C — TTP Audit
**Script:** `scripts\run_ttp_audit.py`
- Reads `trades.csv` — confirms `ttp_state` column is ABSENT (finding for BUG-9)
- Reads `state.json` — shows `ttp_state`, `ttp_trail_level`, `ttp_extreme`, `ttp_close_pending` for all open positions
- Parses bot log for TTP-related lines per position key, builds timeline
- Correlates EXIT_UNKNOWN count vs TTP fail count
- Output: `logs\ttp_audit_2026-03-03.md`
- Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_ttp_audit.py"`

### 1D — BingX Ticker Collector
**Script:** `scripts\run_ticker_collector.py`
- Calls public BingX API: `GET /openApi/swap/v2/quote/ticker` (no auth)
- Extracts: symbol, lastPrice, priceChangePercent (24h), quoteVolume, openInterest
- Filters to USDT-margined perpetuals only
- Sorts by volume descending
- Cross-references which of the 47 config.yaml coins rank in top/bottom half by liquidity
- Output: `logs\bingx_tickers_2026-03-04.csv` + console summary (top/bottom 20)
- Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_ticker_collector.py"`

**Phase 1 Risk: NONE** — all scripts are read-only. Ticker collector makes one unauthenticated GET.

---

## Phase 2 — Bot Core Fixes

**Build script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_phase2_bot_fixes.py`

**STOP BOT BEFORE RUNNING.** Patches two existing files in-place.

### P2-A: Fix BUG-1 — Remove `reduceOnly` from `_place_market_close()`
File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
- Anchor: `_place_market_close()` function signature
- Remove `"reduceOnly": "true"` from order_params dict
- `positionSide` already present — scopes the close correctly in Hedge mode
- Docstring updated to note Hedge-mode-only assumption

### P2-B: Add TTP + BE columns to `_append_trade()` (BUG-9)
File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\state_manager.py`
- Anchor: `_append_trade()` at lines 115-144
- New CSV header columns: `ttp_activated`, `ttp_extreme_pct`, `ttp_trail_pct`, `ttp_exit_reason`, `be_raised`, `saw_green`
- `ttp_activated`: True if `pos.ttp_state` in ("ACTIVATED", "CLOSED")
- `ttp_extreme_pct`: `(extreme - entry) / entry * 100` (sign-corrected per direction)
- `ttp_trail_pct`: same for trail level
- `ttp_exit_reason`: "TTP_CLOSE" if exit_reason == "TTP_EXIT", else blank
- `be_raised`: from pos.be_raised flag
- `saw_green`: always blank (populated by separate analysis script, not bot)
- Existing trades.csv rows unaffected (pandas read_csv handles variable column counts)

### P2-C: Dynamic SL Tightening after TTP activation (new behaviour)
File: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py`
- New method: `_tighten_sl_after_ttp(symbol, pos_data, mark_price)`
- Logic: once `ttp_state == "ACTIVATED"`, compute a progressive SL level:
  - Trail SL = current_extreme × (1 - sl_trail_pct) for LONG, current_extreme × (1 + sl_trail_pct) for SHORT
  - `sl_trail_pct` default: 0.3% (configurable in config.yaml under `four_pillars.sl_trail_pct_post_ttp`)
  - Only move SL upward (LONG) or downward (SHORT) — never widen
  - Cancel old SL order, place new STOP_MARKET at tightened level
  - Rate-limit: only update when new level is ≥ 0.1% better than current SL (avoid API spam)
- Called from `check()` loop after `_evaluate_ttp()` runs
- New config.yaml key added: `sl_trail_pct_post_ttp: 0.003` (0.3% default, null = disabled)

**Phase 2 Risk: MEDIUM**
- P2-A: Stop bot first. Removing `reduceOnly` correct for Hedge mode. Dangerous only on One-way accounts.
- P2-B: Additive only. Old rows get blank trailing columns — no data loss.
- P2-C: SL tightening is a live order operation. Rate-limit guard essential to avoid API hammering. Only activates after TTP is ACTIVATED (not before).

**Verification:**
1. `py_compile` passes on both modified files
2. Restart bot, watch log — next TTP close must NOT show 109400
3. New trade closes must have TTP columns in trades.csv
4. After TTP activates on a position, watch log for SL tightening events

---

## Phase 3 — Dashboard v1.5

**Build script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_5.py`

Reads `bingx-live-dashboard-v1-4.py` as base, applies patches via `safe_replace()`, writes to `bingx-live-dashboard-v1-5.py`. Does NOT modify v1-4.py.

### P3-A: Fix BUG-4 — `_sign()` add `recvWindow`
- Anchor: `_sign()` at lines 191-197
- Add `params['recvWindow'] = '10000'` before building query string
- Ensures signature matches BingX expectation

### P3-B: Fix BUG-1b — Remove `reduceOnly` from 3 dashboard callbacks
- CB-6 (`raise_breakeven` ~line 1512): remove `"reduceOnly": "true"` from STOP_MARKET params
- CB-7 (`move_sl` ~line 1607): same
- CB-16 (`close_market` ~line 1691): same

### P3-C: Fix BUG-2 — Analytics period quick-filter + session-aware equity curve
- Add `dcc.RadioItems(id='analytics-period-filter')` to Analytics tab with options: `session | today | 7d | all`
- CB-9 gets new Input: `analytics-period-filter`
- When `session`: filter df to trades since `session_start` (from state JSON)
- When `today`: filter to UTC today
- When `7d`: filter to last 7 days
- When `all`: no filter (current behaviour)
- Explicit date range always overrides the radio
- Unrealized extension fires for `session` and `all` views (not date-filtered views)

### P3-D: Fix BUG-5 — Coin Summary date sync
- CB-10 `update_coin_summary` gets new Inputs: `analytics-date-range.start_date`, `analytics-date-range.end_date`
- When analytics date range set → takes priority over coin-period-filter radio
- CB-15 `show_coin_detail` gets new Input: `coin-period-filter` → resets detail panel on filter change

### P3-E: Status bar — Exchange vs Bot mode
- CB-3 shows two separate indicators: `BOT: LIVE/OFFLINE` and `EXCHANGE: CONNECTED/ERROR`
- Bot OFFLINE + Exchange CONNECTED: position action buttons remain enabled (they go direct to API)
- Positions always shown from state.json (even bot offline) — fix confusing "OFFLINE = nothing works" UX

### P3-F: TTP Stats panel in Analytics tab
- New `html.Div(id='ttp-stats-section')` in Analytics tab below exit breakdown chart
- New CB-19 reads `store-trades`: if TTP columns present shows stats:
  - TTP Activated: N / X%
  - Closed via TTP trail: N / X%
  - SL hit while TTP ACTIVATED: N
  - Avg TTP extreme % when activated
- If TTP columns absent: shows "TTP tracking requires Phase 2 bot restart"

### P3-G: Trade Chart Popup (HIGH PRIORITY per user)
- History grid row click → modal overlay with multi-panel chart
- New CB-20: Input = `history-grid.selectedRows`, Output = `trade-chart-modal.children` + `trade-chart-modal.style`
- Data fetch: `GET /openApi/swap/v2/quote/klines` for the trade's symbol, timeframe=5m, from entry_time-20bars to exit_time+5bars
- Indicators computed in Python (no external library needed — inline):
  - Stochastic %K 9-3 and 14-3 (Raw K, smooth=1): using pandas rolling min/max
  - Ripster clouds: EMA pairs (5/12, 34/50, 72/89) via pandas ewm
  - BBW: Bollinger Band Width = (upper - lower) / middle
- Plotly make_subplots: 3 rows — candlestick, stochastic (dual lines), BBW bar
- Entry/exit marked as vertical lines + annotations
- Modal: `dbc.Modal` or inline `html.Div` with `position:fixed` overlay
- Close button dismisses modal

**Phase 3 Risk: MEDIUM**
- P3-A/B: Same as Phase 2 (auth + reduceOnly) — test manually after deploy
- P3-C/D/E: Low — UI-only changes
- P3-G: Medium — requires live BingX kline fetch per click; if kline fetch fails, show error in modal (don't crash)

**Verification:**
1. `py_compile` passes on v1-5.py
2. Launch v1-5.py: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py"`
3. Click Close Market on a position — must NOT show signature error or 109400
4. Analytics "session" filter shows only today's trades
5. Coin summary syncs with analytics date range
6. Click any closed trade in History tab — chart popup appears with candles + indicators

---

## Phase 4 — Beta Bot (v384, $5 margin, 20x leverage)

**Build script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_phase4_beta_bot.py`

### Beta Coin List (researched)

User provided 13 coins. Research found **2 overlaps** with live bot:
- **MUBARAK-USDT** and **SAHARA-USDT** are already in the live 47-coin list.

**Plan assumes: remove MUBARAK + SAHARA from beta** (11 safe coins remain). User can override.

Safe user coins (11): `ENSO-USDT, GRASS-USDT, POWER-USDT, VENICE-USDT, SIREN-USDT, FHE-USDT, BTR-USDT, OWC-USDT, WARD-USDT, WHITEWHALE-USDT, ESP-USDT`

Researched additions from live list (smaller/newer tier, no overlap):
`GIGGLE-USDT, PIPPIN-USDT, STBL-USDT, BREV-USDT, Q-USDT, BEAT-USDT, LYN-USDT, TRUTH-USDT, SKR-USDT`

**Beta coin list is still being finalized by user.** Phase 4 build script writes config_beta.yaml with the 11 confirmed safe coins as a placeholder. User adds remaining coins before starting the beta bot. Phase 1D (ticker collector) validates liquidity for all candidates.

### New files:
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config_beta.yaml`
  - Same strategy as config.yaml (four_pillars_v384)
  - `leverage: 20`, `margin_usd: 5` (notional = $100)
  - `coins:` — 11 safe user coins + researched additions confirmed by user
  - All data paths point to `beta/` subdirectory
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py`
  - Copy of main.py with `BASE_DIR / "beta"` path overrides
  - state.json → `beta/state.json`
  - trades.csv → `beta/trades.csv`
  - logs/ → `beta/logs/`
  - bot.pid → `beta/bot.pid`
  - bot-status.json → `beta/bot-status.json`
  - Prints clear WARNING at startup if any beta coin is already in live state.json

**Run command (when ready):** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py"`

**Phase 4 Risk: HIGH**
- 20x leverage = liquidation at ~5% adverse move
- Do NOT run both bots on overlapping coins simultaneously without double-entry guard
- Build script creates files only — user controls start time

---

## Previously Out of Scope — NOW INCLUDED

### BUG-10: Demo mode order verification (CRITICAL finding)
User reported **0 TTP/SL fills in the last demo run** — orders placed but never filled on BingX VST.

Root cause candidates to investigate in Phase 1 (diagnostic):
- VST endpoint differences: demo mode uses `https://open-api-vst.bingx.com` — some order types (STOP_MARKET, TRAILING_STOP_MARKET) may not be supported in VST
- `reduceOnly` error (BUG-1) may have silently blocked ALL close orders in demo too, not just TTP
- SL orders placed as STOP_MARKET with workingType=MARK_PRICE — VST may require CONTRACT_PRICE
- TTP `ttp_close_pending` path: the market close (BUG-1) blocks TTP exits, leaving positions open even after TTP signal

**Phase 1E — Demo Order Verification Script:**
Script: `scripts/run_demo_order_verify.py`
- Connects to BingX VST API using demo credentials from config.yaml
- Places a test MARKET order on a low-price coin (paper money)
- Then places a STOP_MARKET order with workingType=MARK_PRICE
- Then places a STOP_MARKET order with workingType=CONTRACT_PRICE
- Then places a TRAILING_STOP_MARKET order
- Queries each order status after 30s
- Reports: which order types are accepted and filled by BingX VST
- Output: `logs/demo_order_verify_2026-03-04.md`
- Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_demo_order_verify.py"`

This script directly answers: "is the SL/TTP being filled on BingX?" — if STOP_MARKET with MARK_PRICE is rejected by VST, that explains 0 fills.

### Trade Analysis Script (Phase 1F)
Script: `scripts/run_trade_analysis.py`
- Reads full `trades.csv` (231 trades)
- For each trade: fetches BingX order history (`/allOrders`) to get actual fill price, actual exit reason, actual commission paid
- Compares bot-recorded vs BingX-actual: flags any mismatches
- Fetches BingX klines for trade window → computes:
  - MFE (Maximum Favorable Excursion) = best unrealized % during trade
  - MAE (Maximum Adverse Excursion) = worst unrealized % during trade
  - saw_green = True if MFE > commission threshold (trade ever profitable net of fees)
- Outputs:
  - `logs/trade_analysis_2026-03-04.csv` — per-trade: symbol, direction, grade, entry, exit, exit_reason, pnl_net, mfe_pct, mae_pct, saw_green, be_raised, duration_bars
  - `logs/trade_analysis_2026-03-04.md` — summary stats: LSG%, avg MFE at SL, grade A vs B performance, exit reason breakdown, commission drag total
- Run: `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_trade_analysis.py"`

This is the "proper analysis of the trades that were taken."

### Trade chart for OPEN positions
P3-G scope expanded: chart popup available from BOTH History tab (closed trades) AND Live Trades tab (open positions). For open positions: chart shows candles from entry to now, with current mark price line.

---

## Execution Sequence

```
Phase 1  →  Run 4 diagnostic scripts (read results, confirm bugs)
Phase 2  →  STOP BOT → apply patches → py_compile → restart bot → verify no 109400
Phase 3  →  Build v1.5 dashboard → py_compile → launch → test Close Market + chart popup
Phase 4  →  USER provides beta coin list → build beta config → USER starts beta bot
```

---

## Files Modified / Created

| Phase | File | Action |
|-------|------|--------|
| 1 | `scripts/build_phase1_diagnostics.py` | CREATE |
| 1 | `scripts/run_error_audit.py` | CREATE |
| 1 | `scripts/run_variable_web.py` | CREATE |
| 1 | `scripts/run_ttp_audit.py` | CREATE |
| 1 | `scripts/run_ticker_collector.py` | CREATE |
| 2 | `scripts/build_phase2_bot_fixes.py` | CREATE |
| 2 | `position_monitor.py` | PATCH (reduceOnly + SL tighten) |
| 2 | `state_manager.py` | PATCH (TTP columns) |
| 2 | `config.yaml` | PATCH (add sl_trail_pct_post_ttp) |
| 3 | `scripts/build_dashboard_v1_5.py` | CREATE |
| 3 | `bingx-live-dashboard-v1-5.py` | CREATE (from v1-4 base) |
| 4 | `scripts/build_phase4_beta_bot.py` | CREATE |
| 4 | `config_beta.yaml` | CREATE |
| 4 | `main_beta.py` | CREATE |
| 4 | `beta/` directory | CREATE |
