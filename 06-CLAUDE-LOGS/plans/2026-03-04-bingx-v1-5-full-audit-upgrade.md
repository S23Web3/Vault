# BingX Connector — Full Audit + v1.5 Upgrade Plan
Date: 2026-03-04

## Context

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
- Cross-references beta coin list — flags any that are low-liquidity
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
- New config.yaml key: `sl_trail_pct_post_ttp: 0.003` (0.3% default, null = disabled)

**Phase 2 Risk: MEDIUM**
- P2-A: Stop bot first. Removing `reduceOnly` correct for Hedge mode.
- P2-B: Additive only — no data loss.
- P2-C: SL tightening is live order operation. Rate-limit guard prevents API spam. Only fires after TTP ACTIVATED.

**Verification:**
1. `py_compile` passes on both modified files
2. Restart bot — next TTP close must NOT show 109400
3. New trade closes have TTP columns in trades.csv
4. Watch log for SL tightening events after TTP activates

---

## Phase 3 — Dashboard v1.5

**Build script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_dashboard_v1_5.py`

Reads `bingx-live-dashboard-v1-4.py` as base, writes to `bingx-live-dashboard-v1-5.py`. Does NOT modify v1-4.py.

### P3-A: Fix BUG-4 — `_sign()` add `recvWindow`
- Add `params['recvWindow'] = '10000'` before building HMAC query string

### P3-B: Fix BUG-1b — Remove `reduceOnly` from CB-6, CB-7, CB-16
- 3 locations, all have `positionSide` already present

### P3-C: Fix BUG-2 — Analytics period quick-filter + session equity curve
- Add `dcc.RadioItems(id='analytics-period-filter')`: `session | today | 7d | all`
- CB-9 new Input: `analytics-period-filter`
- `session`: filter to `session_start` from state JSON
- `today`: UTC today; `7d`: last 7 days; `all`: no filter
- Explicit date range always overrides radio
- Unrealized extension fires for `session` and `all` views

### P3-D: Fix BUG-5 — Coin Summary date sync
- CB-10 gets Inputs: `analytics-date-range.start_date`, `analytics-date-range.end_date`
- Analytics date range takes priority over coin-period-filter radio when set
- CB-15 gets Input: `coin-period-filter` → resets detail panel on filter change

### P3-E: Status bar — Exchange vs Bot mode
- `BOT: LIVE/OFFLINE` + `EXCHANGE: CONNECTED/ERROR` as separate indicators
- Position action buttons remain enabled when bot OFFLINE + exchange CONNECTED

### P3-F: TTP Stats panel in Analytics tab
- New CB-19: if TTP columns present in trades.csv → show TTP Activated %, Closed via TTP %, SL hit while ACTIVATED, avg extreme %
- If columns absent: "TTP tracking requires Phase 2 bot restart"

### P3-G: Trade Chart Popup (HIGH PRIORITY)
- History grid row click → modal overlay
- New CB-20: fetches BingX klines for symbol around trade window (entry_time-20bars to exit_time+5bars)
- Indicators computed inline (no external library):
  - Stochastic %K 9-3 and 14-3 (Raw K, smooth=1): pandas rolling min/max
  - Ripster cloud EMAs: 5/12, 34/50, 72/89 via pandas ewm
  - BBW: (BB_upper - BB_lower) / BB_middle
- Plotly make_subplots (3 rows): candlestick, dual stochastic lines, BBW bar
- Entry/exit marked as vertical lines + annotations
- Modal: `html.Div` with `position:fixed` overlay + close button
- On kline fetch failure: show error message in modal, do not crash

**Phase 3 Risk: MEDIUM**
- P3-A/B: Test Close Market manually after deploy
- P3-G: Live kline fetch per click — guard against API failure

**Verification:**
1. `py_compile` on v1-5.py
2. Launch v1-5 — Close Market must work (no signature or 109400 errors)
3. Analytics "session" filter shows only current session trades
4. Coin summary syncs with analytics date range
5. Click closed trade in History → chart popup with candles + indicators appears

---

## Phase 4 — Beta Bot (v384, $5 margin, 20x leverage)

**USER ACTION REQUIRED:** Confirm the beta coin list is final before build runs.

**Beta coin list (user-provided + research needed):**

User-specified (13 coins):
`ENSO-USDT, GRASS-USDT, POWER-USDT, VENICE-USDT, MUBARAK-USDT, SAHARA-USDT, SIREN-USDT, FHE-USDT, BTR-USDT, OWC-USDT, WARD-USDT, WHITEWHALE-USDT, ESP-USDT`

Remaining slots: Research needed from the live bot's 47-coin list to find coins NOT already in live config that are suitable (liquid, low-price tier, available on BingX perpetuals). Ticker collector output (Phase 1D) will inform this selection.

**Build script:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_phase4_beta_bot.py`

### New files:
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\config_beta.yaml`
  - `leverage: 20`, `margin_usd: 5` (notional = $100)
  - `coins:` — user-confirmed beta list
  - Strategy: four_pillars_v384, same params as live
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py`
  - All data paths prefixed with `beta/`: state.json, trades.csv, logs/, bot.pid, bot-status.json
  - Startup WARNING if any beta coin found in live state.json open positions

**Run command (when ready):** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py"`

**Phase 4 Risk: HIGH**
- 20x leverage = ~5% adverse move to liquidation
- Do NOT run on coins overlapping with live bot without double-entry guard
- Build script creates files only — user starts bot

---

## Out of Scope

- LSG `saw_green` backfill for existing 231 trades (separate analysis script post-Phase 1)
- BUG-8 BE verification (analysable from new `be_raised` + `exit_reason` columns)
- Trade chart for open positions (history grid only in v1.5)
- Full double-entry guard (user providing separate coin list instead)

---

## Execution Sequence

```
Phase 1  →  Run 4 diagnostic scripts (read results, confirm bugs)
Phase 2  →  STOP BOT → patches → py_compile → restart → verify no 109400
Phase 3  →  Build v1.5 → py_compile → launch → test Close Market + chart popup
Phase 4  →  USER confirms beta coin list → build → USER starts beta bot
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
| 2 | `config.yaml` | PATCH (add sl_trail_pct_post_ttp key) |
| 3 | `scripts/build_dashboard_v1_5.py` | CREATE |
| 3 | `bingx-live-dashboard-v1-5.py` | CREATE (from v1-4 base) |
| 4 | `scripts/build_phase4_beta_bot.py` | CREATE |
| 4 | `config_beta.yaml` | CREATE |
| 4 | `main_beta.py` | CREATE |
| 4 | `beta/` directory | CREATE |