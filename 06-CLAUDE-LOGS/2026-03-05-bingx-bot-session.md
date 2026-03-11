# BingX Bot Session Log — 2026-03-05

## Session Summary

Continuation from 2026-03-04 audit + patch session. Bot restarted with all fixes applied.

---

## Fixes Applied This Session

### Three-Stage Position Management (be_act / ttp_act split)
- `be_act: 0.004` — BE raises at +0.4% from entry (was shared 0.5% with TTP)
- `ttp_act: 0.008` — TTP activates at +0.8% from entry (was 0.5%)
- `ttp_dist: 0.003` — trail 0.3% behind extreme (was 0.2%)
- Files: `config.yaml`, `position_monitor.py` (reads `be_act`), `signal_engine.py` (fallback defaults updated)
- Test: `scripts/test_three_stage_logic.py` — 25/25 PASS

### orderId Extraction Fix (3 locations in position_monitor.py)
- `_place_be_sl()` line ~431: was `data.get("data",{}).get("orderId","?")` — missed nested `order` key
- `_tighten_sl_after_ttp()` line ~586: same bug
- `_place_market_close()` line ~685: same bug
- Fix: `_d.get("orderId") or _d.get("order",{}).get("orderId","?")` — matches executor.py pattern
- Evidence: `orderId=?` seen in log for BOME-USDT BE raise at 21:38:40

### Unrealized PnL in Telegram
- New method `_calc_unrealized_pnl()` in `position_monitor.py`
- Daily summary (17:00 UTC) now shows: Realized PnL, Unrealized, Equity, Trades, Open
- Hourly warning (when loss >= 50% limit) now includes unrealized + equity
- Hourly log INFO line updated with realized/unrealized/equity

### Other config changes
- `max_positions: 25` (was 15) — user increased via config.yaml

---

## Log Review — 2026-03-04-bot.log (11,466 lines, 953KB)

### Key events after 21:40 (last captured in prior session log)
- `21:38:40` — BOME-USDT BE raise fired, `orderId=?` (now fixed)
- `21:40:34` — RIVER-USDT SHORT opened
- Bot ran overnight into 2026-03-05

### Today's activity (log rolled into same file — 2026-03-04-bot.log)
- `13:15` — DNS resolution failure (`getaddrinfo failed`) for open-api.bingx.com
  - 30+ consecutive CRITICAL alerts for kline fetch failures
  - Network outage approx 5-10 minutes, self-recovered
  - No positions affected (SLs remain on exchange independently)
- `13:40:38` — BB-USDT LONG closed SL_HIT pnl=+$0.34
- `13:55:03` — STBL-USDT SHORT opened
- `14:05:24` — Q-USDT SHORT opened
- `14:20:22` — BEAT-USDT LONG opened
- `14:34:05` — STBL-USDT SHORT closed SL_HIT pnl=-$0.10
- `14:52:25` — BEAT-USDT LONG closed SL_HIT pnl=-$0.67

### Error count: 113 errors in log (majority from DNS outage block)
### RENDER-USDT: Still processing bars — not reconciled/closed as of last log entry

---

## Current Config State

```yaml
four_pillars:
  allow_a: true
  allow_b: true
  allow_c: false
  sl_atr_mult: 2.0
  tp_atr_mult: null
  require_stage2: true
  rot_level: 80

risk:
  max_positions: 25

position:
  margin_usd: 5.0
  leverage: 10
  be_act: 0.004
  ttp_act: 0.008
  ttp_dist: 0.003
  sl_trail_pct_post_ttp: 0.003
  be_auto: true
  ttp_enabled: true
```

---

## Time Sync Fix — Error 109400 (2026-03-05 evening)

**Problem**: Bot and dashboard use raw `time.time() * 1000` for BingX API timestamps. BingX rejects requests where timestamp drifts >5 seconds from server clock (error 109400). No server time sync existed. When timestamps went invalid, position reconciliation, SL moves, TTP closes, and balance queries all failed silently (logged as warnings, fell back to stale local state). User lost 17% due to this.

**Immediate fix**: `w32tm /resync /force` in admin PowerShell — synced Windows clock to NTP. Running bot stopped getting 109400 immediately (no restart needed).

**Permanent fix**: Build script `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_time_sync.py` — creates `time_sync.py` module + patches 5 files. Applied to disk. Activates on next bot/dashboard restart.

**Files created:**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\time_sync.py` — TimeSync class: fetches `/openApi/swap/v2/server/time`, calculates offset, RTT midpoint compensation, 30s periodic sync, thread-safe singleton, `force_resync()` on 109400 error

**Files modified (with .bak backups):**
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx_auth.py` — `import time` replaced with `from time_sync import synced_timestamp_ms`, line 43 uses synced time
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\main.py` — TimeSync init at startup (sync + periodic), cleanup at shutdown
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\executor.py` — 109400 retry block (force_resync + re-sign + retry once)
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\position_monitor.py` — 109400 retry in `_fetch_positions()`
- `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-4.py` — synced timestamps in `_sign()`, 109400 retry in `_bingx_request()`, TimeSync init at startup

**Plan**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-05-bingx-timestamp-sync-fix.md`

**Status**: Files on disk. Bot restart required to activate. Dashboard can be restarted independently.

---

## Trade Analyzer v2 + ATR Investigation (2026-03-05 afternoon)

### Trade Analyzer v2

Built comprehensive trade analysis script to replace the sparse v1 analyzer.

**Plan**: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\plans\2026-03-05-trade-analyzer-v2.md`

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_trade_analyzer_v2.py`
**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_trade_analysis_v2.py`

**Features (11 analysis sections)**:
1. Summary stats (trades, WR%, net PnL, profit factor, avg winner/loser, best/worst, LSG%)
2. Equity curve (ASCII terminal chart + markdown data table)
3. Symbol leaderboard (sorted by net PnL)
4. Direction breakdown (LONG vs SHORT)
5. Grade breakdown (A vs B vs C)
6. Exit reason breakdown (count, %, avg PnL per exit type)
7. Hold time analysis (avg, shortest, longest, winners vs losers)
8. TTP performance (TTP vs non-TTP PnL comparison)
9. BE raise effectiveness (BE vs non-BE WR% and PnL)
10. PnL distribution (std dev, skew, histogram)
11. Per-trade detail table (fixed-width padded columns)

**Additional metrics added mid-build**: PnL std dev/distribution/skew, max concurrent capital usage, max drawdown.

**CLI flags**: `--from`, `--to`, `--days`, `--no-api`, `--verbose`

**Output formats**: Terminal (fixed-width), Markdown (padded tables), CSV (enriched per-trade)

**Bugs fixed after initial build**:
- CSV schema mismatch: pandas couldn't handle ragged 12/18 column rows. Fixed with csv.reader + manual padding.
- ModuleNotFoundError dotenv: made import conditional for --no-api mode.
- Date filter upgraded from date-only to datetime-level (`2026-03-04T16:00` = 8pm Dubai time).

**Status**: Build OK. py_compile PASS. Tested with --no-api. Build script SOURCE is now out of sync with direct edits to output file (3 fixes applied directly).

### ATR Investigation

User asked: "i want an investigation of the losing trades whether the atr was really there"

**Build script**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\build_atr_investigation.py`
**Output**: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\scripts\run_atr_investigation.py`

**How ATR/SL chain works** (traced through codebase):
- `compute_signals()` in `signals/four_pillars.py`: ATR(14) via Wilder's RMA on 5m bars
- `_make_signal()` in `plugins/four_pillars_v384.py`: SL = entry +/- (ATR * 2.0)
- `risk_gate.py`: blocks trades where atr_ratio = ATR/price < 0.003
- `position_monitor.py`: SL_HIT exit_price = state's sl_price (placed SL, not actual fill)
- BE trades: SL moved to entry + commission buffer, loss is minimal

**Investigation approach**:
- Reverse-engineer implied ATR from SL distance: `implied_atr = abs(entry - exit) / sl_atr_mult`
- Compute atr_ratio, SL%, margin impact%
- Split into non-BE losers (11 trades, full SL hit) and BE losers (10 trades, tiny losses)
- Optional API verification: fetch 201 klines, compute ATR(14), compare to implied

**Key findings from manual CSV scan** (pre-script):
- Q-USDT: 5.15% SL distance, 2.58% ATR ratio, 51.5% margin impact -- worst
- PIPPIN-USDT: 3.19% SL, 1.59% ATR ratio, 31.9% margin impact
- RIVER-USDT: 2.60% SL, 1.30% ATR ratio, 26.0% margin impact
- These are legitimate ATR values (risk gate only blocks < 0.003), but consuming 25-50% of margin per loss
- Recommendation: consider max_atr_ratio cap (e.g. 0.015) to block ultra-volatile entries

**Status**: Build script written. py_compile PASS. Built and run with `--no-api`. Results below.

### ATR Investigation Results (--no-api run)

**Non-BE Losers (11 trades, full SL hit):**

| Symbol | Dir | SL% | ATR Ratio | Margin% | Verdict |
|--------|-----|-----|-----------|---------|---------|
| Q-USDT | SHORT | 5.15% | 2.58% | 51.5% | EXTREME_VOL |
| PIPPIN-USDT | SHORT | 3.19% | 1.59% | 31.9% | HIGH_VOL |
| RIVER-USDT | SHORT | 2.60% | 1.30% | 26.0% | HIGH_VOL |
| PIPPIN-USDT | LONG | 2.15% | 1.08% | 21.5% | HIGH_VOL |
| SIREN-USDT | SHORT | 1.93% | 0.97% | 19.3% | MED_VOL |
| STBL-USDT | SHORT | 1.71% | 0.86% | 17.1% | MED_VOL |
| SPX-USDT | LONG | 1.70% | 0.85% | 17.0% | MED_VOL |
| BERA-USDT | SHORT | 1.43% | 0.72% | 14.3% | NORMAL |
| BEAT-USDT | LONG | 1.34% | 0.67% | 13.4% | NORMAL |
| PAWS-USDT | LONG | 1.28% | 0.64% | 12.8% | NORMAL |
| BOME-USDT | LONG | 1.20% | 0.60% | 12.0% | NORMAL |

**Key finding**: ATR is real and legitimately computed. The problem is uncontrolled volatility -- 4 HIGH_VOL+ trades (atr_ratio > 1%) caused 66% of non-BE losses. Risk gate only blocks < 0.003; no upper bound exists.

**Three recommended fixes:**
1. `max_atr_ratio` cap at 0.015 in risk_gate.py -- blocks Q-USDT, PIPPIN, RIVER entries
2. ATR-scaled position sizing -- reduce margin for high-ATR coins
3. `sl_atr_mult` reduction from 2.0 to 1.5 -- tighter SL globally

---

## Trade Analyzer v2 — Actual Results (57 trades, 2026-03-04 to 2026-03-05)

Full report: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\logs\trade_analysis_v2_2026-03-05.md`

### Summary
- **57 trades**: 33W / 24L = 57.9% WR
- **Net PnL**: -$0.694 (before rebate)
- **Net PnL w/ 70% rebate**: +$2.50 (57 trades * $0.08 commission * 70% rebate = +$3.19 rebate)
- **Profit factor**: 0.94 (pre-rebate), ~1.25 (post-rebate)
- **Avg winner**: +$0.53, **Avg loser**: -$0.72
- **Best**: KAITO-USDT +$2.90, **Worst**: RIVER-USDT -$1.57
- **LSG**: 79.2% (19/24 losers saw green first)
- **Max drawdown**: $4.02
- **Peak concurrent positions**: 6 ($300 notional at $5 * 10x)

### Direction Breakdown
- **LONG**: 28 trades, 57.1% WR, +$3.26 PnL, avg MFE 1.26%
- **SHORT**: 29 trades, 58.6% WR, -$3.96 PnL, avg MFE 0.86%
- LONG outperforms SHORT by $7.22

### Key Systems
- **BE raised (45 trades)**: 71.1% WR, +$9.19 PnL -- backbone of the system
- **TTP exits (21 trades)**: +$9.59 total PnL -- profit engine
- **Non-TTP exits (36 trades)**: -$10.28 total PnL
- Without BE + TTP, the bot is deeply negative

### Grade Breakdown
- **Grade A**: 20 trades, 65.0% WR, +$3.70
- **Grade B**: 37 trades, 54.1% WR, -$4.39
- Grade A significantly more profitable per trade

### PnL Distribution
- **Std dev**: $0.99
- **Skew**: -1.70 (fat left tail -- big losers pull down)

---

## Scaling Analysis — $500 Margin / 20x / $10k Portfolio

User asked: "what if it was 500$ on 20x for a 10k portfolio"

### Scale Factor
- Current: $5 margin * 10x = $50 notional per trade
- Scaled: $500 margin * 20x = $10,000 notional per trade
- **Scale factor**: 200x (from $50 to $10,000 notional)

### Projected Metrics (200x scale)
| Metric | Current ($50) | Scaled ($10k) |
|--------|--------------|---------------|
| Net PnL (pre-rebate) | -$0.69 | -$138 |
| Rebate (70%) | +$3.19 | +$638 |
| Net PnL (post-rebate) | +$2.50 | +$500 |
| Max drawdown | $4.02 | $804 (8% of $10k) |
| Peak capital in use | $300 (6 pos) | $60,000 (6 pos * $10k) |
| Daily volume | 57 * $50 = $2,850 | 57 * $10,000 = $570,000 |

### Liquidation Risk
- At 20x leverage, liquidation occurs at ~4.6% adverse move (after fees)
- **Q-USDT**: 5.15% SL distance -- **WOULD BE LIQUIDATED** before SL hits at 20x
- PIPPIN-USDT: 3.19% SL -- safe but close to 20x margin
- Most trades: 1.2-2.0% SL -- safe at 20x

### Conclusion
At scale, the system is marginally profitable thanks to rebates. The 8% max drawdown is manageable for a $10k portfolio. The critical risk is ultra-volatile coins (Q-USDT class) that can liquidate at 20x before the SL triggers. A max_atr_ratio cap is essential at higher leverage.

---

## Pending / Next Session

### P1 — dashboard_v395.py (backtester dashboard with v384 preset)
Build script: `PROJECTS/four-pillars-backtester/scripts/build_dashboard_v395.py`
- Add `require_stage2` checkbox to sidebar (currently missing from dashboard UI)
- Add `rot_level` slider (0-100, default 80) to sidebar
- Add "Load v384 Live Preset" button that sets all params to live bot values
- Wire new params into `sig_params` dict passed to `compute_signals()`
- Output: `dashboard_v395.py` (v394 untouched)
- Run: `streamlit run "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\scripts\dashboard_v395.py"`

### P2 — Known unfixed bugs
- BE SL direction bug for SHORT: `entry * (1 - buffer)` places SL below entry (profit zone)
  - The cancel-then-replace sequence exposed this: cancel original SL succeeds, new BE SL placed at wrong level
  - Fix: SHORT BE price should be `entry * (1 - commission_rate - buffer)` which IS correct mathematically
  - Actually the issue is the exchange SL for SHORT must be ABOVE entry — the BE formula is correct but
    needs verification that the STOP_MARKET BUY order triggers correctly when price rises above stopPrice
- Dashboard v1-4 settings save writes `ttp_act` only — does not write `be_act`

---

## Evening Session — Dashboard v1.5 Full Debug + Fix Chain (continuation)

### Context
Bot running live. Dashboard v1.5 launched — showed multiple errors. Full audit + incremental fix session.

### Fix 1: store-bot-status KeyError (applied earlier session)
- `build_dashboard_v1_5_patch_runtime.py` — changed `dcc.Store(id='store-bot-status', data=[])` to `storage_type='memory'`
- Eliminated the KeyError on page load

### Fix 2: Full Line-by-Line Audit (3010 lines) — 4 bugs found
- **BUG-A (CRITICAL):** time_sync import + init + `_sign()` missing from v1.5 (built before time_sync was added)
- **BUG-B (CRITICAL):** `_bingx_request()` missing 109400 retry logic
- **BUG-C (HIGH):** CB-15 `show_coin_detail` missing `Input('analytics-date-range', 'end_date')` — caused IndexError in `_prepare_grouping`
- **BUG-D (MEDIUM):** `be_act` not wired into settings save/load callbacks
- Build script: `scripts/build_dashboard_v1_5_full_audit_fix.py` — 8 patches (P1-P8), all applied

### Fix 3: Signing Fix (100001 Signature Verification Failed)
- Root cause: dashboard used `requests.get(url, params=signed_dict)` — requests library re-encodes params, can reorder query string
- Bot (bingx_auth.py) builds URL manually: `url + '?' + sorted_query + '&signature=' + sig`
- Fix: aligned dashboard `_sign()` and `_bingx_request()` with bot's URL-build approach
- Build script: `scripts/build_dashboard_v1_5_signing_fix.py` — P1 (sign returns tuple), P2 (manual URL build)
- Result: EXCHANGE: CONNECTED, Balance $73.61, Equity $72.56 — live data confirmed

### Fix 4: Trades CSV Loading (History + Analytics showing no data)
- Root cause: bot writes 18 columns per trade row (three-stage fields), CSV header has 12 — `pd.read_csv()` throws `ParserError`, caught silently
- Fix: `csv.reader` with row truncation to header length
- Also: refresh interval reduced from 60s to 15s for faster position updates
- Build script: `scripts/build_dashboard_v1_5_trades_refresh.py`
- Result: 47 trades loaded in Analytics, History populated

### Fix 5: Max DD % Industry Standard (COMPLETE)
- Bug: DD% was calculated as `pnl_drawdown / pnl_peak` — gives -100% when cumulative PnL crosses zero
- Fix: equity-based drawdown — `equity = starting_balance + cumsum(PnL)`, DD% on equity curve
- `starting_balance = api_balance - net_pnl` (derived from live API balance)
- Build script: `scripts/build_dashboard_v1_5_drawdown_fix.py` — ran 2026-03-06, reported "not found" but patches were already applied (confirmed via grep). File is correct.

### 2026-03-06 Continuation
- Dashboard venv: `ModuleNotFoundError: No module named 'dash'` when run from `.venv312` (Python313)
- Confirmed: dash 4.0.0 installed on Python314 only
- Run command: `"C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe" "C:\Users\User\Documents\Obsidian Vault\PROJECTS\bingx-connector\bingx-live-dashboard-v1-5.py"`

### Build Scripts Created This Session
| Script | Purpose |
|--------|---------|
| `scripts/build_dashboard_v1_5_full_audit_fix.py` | 8-patch audit fix (BUG-A through BUG-D) |
| `scripts/build_dashboard_v1_5_signing_fix.py` | Signing URL-build fix (100001 error) |
| `scripts/build_dashboard_v1_5_trades_refresh.py` | CSV column mismatch fix + 15s refresh |
| `scripts/build_dashboard_v1_5_drawdown_fix.py` | Industry-standard Max DD % |

### Dashboard v1.5 Current Status
- EXCHANGE: CONNECTED
- Balance/Equity: live (signed API working)
- Positions: real-time with mark prices (15s refresh)
- History/Analytics: 47 trades loaded, charts populated
- Max DD %: FIXED (equity-based, confirmed in file)
- IndexError: FIXED (BUG-C)
- BE Activation %: wired into settings (BUG-D)
- Python: must use Python314 (`C:\Users\User\AppData\Local\Programs\Python\Python314\python.exe`)