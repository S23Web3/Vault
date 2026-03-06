# BingX Full Audit + v1.5 Upgrade
**Date:** 2026-03-04
**Session type:** Multi-phase build (4 phases)
**Plan:** `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-04-bingx-v1-5-full-audit-upgrade.md`

---

## Context

Live bot running 12+ hours. User provided screenshots showing multiple issues:
- TTP close orders failing (error 109400) — infinite retry loops
- Close Market button broken (signature error 100001)
- Equity curve showing drawdown shape (all sessions mixed)
- Coin summary date filter disconnected from analytics tab
- EXIT_UNKNOWN exits not explained
- No TTP activation tracking in trades.csv
- Bot OFFLINE paradox — position controls needed but confusing UX
- $5/10x underperforming vs backtester perspective → beta at $5/20x

---

## Confirmed Bugs

| # | Bug | Root Cause | Fixed |
|---|-----|-----------|-------|
| BUG-1 | TTP/Close Market 109400 | `"reduceOnly": "true"` invalid in Hedge mode | Phase 2 (position_monitor.py) |
| BUG-1b | Dashboard same 109400 | Same in 3 callbacks | Phase 3 (v1.5 P3-B) |
| BUG-4 | Close Market 100001 signature | `_sign()` missing recvWindow before HMAC | Phase 3 (v1.5 P3-A) |
| BUG-2 | Equity curve = drawdown | All sessions mixed, no filter | Phase 3 (v1.5 P3-C) |
| BUG-5 | Coin summary ignores analytics date | Separate radio not wired to date range | Phase 3 (v1.5 P3-D) |
| BUG-9 | TTP not in trades.csv | `_append_trade()` missing TTP fields | Phase 2 (state_manager.py) |

---

## Phase 1 — Diagnostic Scripts (BUILT)

**Build script:** `scripts/build_phase1_diagnostics.py` — py_compile PASS

Scripts created (all read-only except demo_order_verify):
- `run_error_audit.py` — parses logs, categorizes TTP_CLOSE_FAIL/AUTH_FAIL/EXIT_DETECTION
- `run_variable_web.py` — static AST analysis of full data flow
- `run_ttp_audit.py` — correlates TTP state with log timeline
- `run_ticker_collector.py` — public BingX API for liquidity ranking
- `run_demo_order_verify.py` — tests STOP_MARKET/TRAILING/MARKET on BingX VST
- `run_trade_analysis.py` — MFE/MAE/saw_green per trade via kline fetch

**Status: BUILT. Run commands in plan file. Not yet executed (user to run).**

---

## Phase 2 — Bot Core Fixes (APPLIED)

**Build script:** `scripts/build_phase2_bot_fixes.py` — BUILD OK

Patches applied to live files:

| File | Change |
|------|--------|
| `position_monitor.py` | P2-A: removed `reduceOnly` from `_place_market_close()` |
| `position_monitor.py` | P2-C: added `_tighten_sl_after_ttp()` + `check_ttp_sl_tighten()` |
| `state_manager.py` | P2-B: added TTP+BE columns to `_append_trade()` (ttp_activated, ttp_extreme_pct, ttp_trail_pct, ttp_exit_reason, be_raised, saw_green) |
| `config.yaml` | P2-D: added `sl_trail_pct_post_ttp: 0.003` |
| `main.py` | P2-C wire: `monitor.check_ttp_sl_tighten()` added to monitor_loop |

**SL tightening logic:** After TTP ACTIVATED, trails SL toward `extreme * (1 - 0.003)` for LONG. Only moves in favourable direction. Rate-limited at 0.1% minimum improvement. Cancels old SL order, places new STOP_MARKET.

**Verification:** Stop bot first. Restart after patch. Next TTP close must NOT show 109400. New trade rows will have TTP columns.

---

## Phase 3 — Dashboard v1.5 (BUILT)

**Build script:** `scripts/build_dashboard_v1_5.py` — BUILD OK (all 17 patches)
**Output:** `bingx-live-dashboard-v1-5.py` — py_compile + ast.parse PASS
**Run:** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py"`

**Anchor fix note:** v1-4.py uses em-dash `\u2014` in `# Step 5: Update state.json — ...` comments. Build script anchors must use `\u2014` not `--`. Resolved after first run showed MISSING_ANCHOR for P3-B1/B2. Also: `"BingX Live Dashboard v1-4"` appears 2x (docstring + app.title), requiring separate anchors for P3-H.

Patches:
- **P3-A:** `_sign()` adds `params['recvWindow'] = '10000'` before HMAC → fixes 100001
- **P3-B:** `reduceOnly` removed from CB-6 (Raise BE), CB-7 (Move SL), CB-16 (Close Market)
- **P3-C:** `dcc.RadioItems(id='analytics-period-filter')` with session/today/7d/all options. CB-9 filters equity curve to session_start from state JSON when session selected.
- **P3-D:** CB-10 `update_coin_summary` gets `analytics-date-range` start/end inputs (priority over radio). CB-15 `show_coin_detail` gets `coin-period-filter` input (resets on filter change).
- **P3-E:** Status bar shows `BOT: LIVE/OFFLINE` + `EXCHANGE: CONNECTED/NO DATA` as two separate metric cards.
- **P3-F:** CB-19 `update_ttp_stats` — checks for `ttp_activated` column. Shows stats if present; "requires Phase 2 restart" if absent.
- **P3-G:** Trade chart popup — `_fetch_klines_for_chart()`, `_build_trade_chart()` (3-row subplot: candles+EMAs, dual stochastic K, BBW bars), CB-20 fires on `history-grid.selectedRows` and `positions-grid.selectedRows`. Modal with fixed overlay + close button.
- **P3-H:** Version strings updated (docstring, app.title, run command).

---

## Phase 4 — Beta Bot (BUILT)

**Build script:** `scripts/build_phase4_beta_bot.py` — BUILD OK
**Output:**
- `config_beta.yaml` — 44 coins, 20x leverage, $5 margin, data under `beta/`
- `main_beta.py` — main.py adapted for beta (config_beta.yaml + beta/ paths)
- `beta/` + `beta/logs/` — created empty

**Beta coin list (44 coins):**
11 user-specified safe coins: ENSO, GRASS, POWER, VENICE, SIREN, FHE, BTR, OWC, WARD, WHITEWHALE, ESP
33 additional from screenshots (no live overlap, no ETH/BTC): INJ, JTO, JUP, LINK, LTC, METAX, MUS, MYX, NEAR, ONDO, PENGU, POPCAT, PUMP, QNT, 1000SHIB, SOL, SUI, UNI, XRP, ZEC, ZEN, APE, ASTER, AXS, BANK, BERAU, BNB, BONK, DASH, DOT, FARTCOIN, HMSTR, IMX

**Excluded (overlap with live 47):** MUBARAK, SAHARA, PIPPIN, RIVER, SUSHI, APT, DYDX, RENDER, MEME, 1000PEPE

**Overlap guard:** main_beta.py checks live state.json for open positions on beta coins at startup. 15s warning + abort opportunity if overlap found.

**Before starting:** Run `run_ticker_collector.py` to verify all 44 coins are liquid on BingX perpetuals.
**Run:** `python "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main_beta.py"`

---

## Files Created/Modified

| File | Action |
|------|--------|
| `scripts/build_phase1_diagnostics.py` | CREATED |
| `scripts/run_error_audit.py` | CREATED (by phase1 build) |
| `scripts/run_variable_web.py` | CREATED (by phase1 build) |
| `scripts/run_ttp_audit.py` | CREATED (by phase1 build) |
| `scripts/run_ticker_collector.py` | CREATED (by phase1 build) |
| `scripts/run_demo_order_verify.py` | CREATED (by phase1 build) |
| `scripts/run_trade_analysis.py` | CREATED (by phase1 build) |
| `scripts/build_phase2_bot_fixes.py` | CREATED |
| `position_monitor.py` | PATCHED (reduceOnly + SL tighten) |
| `state_manager.py` | PATCHED (TTP columns) |
| `config.yaml` | PATCHED (sl_trail_pct_post_ttp) |
| `main.py` | PATCHED (check_ttp_sl_tighten wired in) |
| `scripts/build_dashboard_v1_5.py` | CREATED |
| `bingx-live-dashboard-v1-5.py` | CREATED (from v1-4 base) |
| `scripts/build_phase4_beta_bot.py` | CREATED |
| `config_beta.yaml` | CREATED |
| `main_beta.py` | CREATED |
| `beta/` | CREATED |
| `scripts/run_phase1_all.py` | CREATED (phase 1 runner, subprocess-based) |
| `scripts/run_trade_analysis.py` | PATCHED (klines dict format fix: `bar["high"]`/`bar["low"]`/`k["time"]`) |

---

## Phase 1 Run Results (2026-03-04 18:02–18:21)

All 6 scripts passed via `run_phase1_all.py`.

### 1A — Error Audit
- 15,399 total error/warning lines
- **7,650 TTP_CLOSE_FAIL** — the reduceOnly 109400 bug caused ~50% of all log entries to be errors
- 29 API_TIMEOUT, 3 WS_ERROR, 7,716 OTHER

### 1D — Ticker Collector
- 597 USDT perpetuals found
- Additional live-bot overlaps discovered in beta candidate list: LYN, GIGGLE, BEAT, TRUTH, STBL, BREV, Q, SKR — all flagged `[OVERLAP-LIVE]`
- MUS-USDT not found on BingX (not available)
- config_beta.yaml needs these removed before starting beta bot

### 1E — Demo Order Verify
- All 5 order types placed with code=0
- Status=UNKNOWN after 5s — VST fill confirmation unreliable (known BingX VST behavior)

### 1F — Trade Analysis (230 trades)
- **Win rate: 8.3%** (expected 35-45% — catastrophically low)
- **Net PnL: -$825.24**
- **LSG%: 75.8%** — 3 in 4 losers were profitable at some point (0.937% avg MFE)
- **EXIT_UNKNOWN: 100 trades (43%)** — TTP activating, failing to close (109400 bug), positions closed via unknown mechanism
- **Grade A worse than Grade B**: A=3.3% WR / -$523 (61 trades), B=10.1% WR / -$302 (169 trades)
- Grade A LSG: 88.1% — A signals reach green almost universally but fail to hold

### Key Findings
1. The 109400 reduceOnly bug (now fixed) caused 43% of all exits to be unrecorded — this is the primary performance killer
2. LSG 75.8% + Avg MFE 0.937% → a TP at 0.5-0.7% would have captured most winners — backtester sweep warranted
3. Grade A signal quality needs investigation — possibly firing late (stage 2 too strict) or stoch confirming tops

---

## Phase 2 Status — ALREADY APPLIED

Build script ran but showed MISSING ANCHOR for P2-A and P2-B. Verified both patches were already applied in a prior session:
- `position_monitor.py`: `_place_market_close` docstring confirms no reduceOnly
- `state_manager.py`: `_append_trade` already has all TTP columns (ttp_activated, ttp_extreme_pct, saw_green, etc.)
- P2-C (SL tighten), P2-D (config key), main.py wiring: all SKIP (already applied)

**Bot is patched and ready to restart.**

## Audit Fixes — APPLIED (2026-03-04)

**Build script:** `scripts/build_audit_fixes.py` — BUILD OK (all 5 patches)

| Bug | File | Fix |
|-----|------|-----|
| C1 | position_monitor.py | Removed duplicate `_tighten_sl_after_ttp` (82 lines) + duplicate `check_ttp_sl_tighten` (13 lines) |
| H3 | signal_engine.py | `entry` captured before `if engine is None:` — fixes NameError on Set TTP dashboard action |
| H4 | state_manager.py | `reconcile()` now calls `_append_trade` for phantom closes with EXIT_UNKNOWN_RECONCILE + $0 PnL |
| M4 | main.py | Replaced both `input()` blocking calls — headless/VPS safe |
| M5 | state_manager.py | `reset_daily()` refreshes `session_start` — dashboard v1.5 session equity filter correct |

Not fixed (design discussion needed): H1 (BE/TTP coupling), H2 (exit price from state not fill), M1 (CSV header race), M2 (API rate limit batching), M3 (SL cancel-before-place race).

## Next Steps

- **IMMEDIATE**: Restart bot (`python main.py`) — all patches applied
- **Dashboard**: Launch v1.5 (`python bingx-live-dashboard-v1-5.py`) — test Close Market + session equity curve
- **Beta bot**: Remove confirmed overlaps from config_beta.yaml (LYN, GIGGLE, BEAT, TRUTH, STBL, BREV, Q, SKR, MUS) → start `python main_beta.py`
- **Future**: Backtester TP sweep at 0.5-1.0x ATR range (LSG data supports tight TP hypothesis)
